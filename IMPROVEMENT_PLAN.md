# NewsAgg 项目整改方案

> 审查日期: 2026-05-29
> 最后更新: 2026-05-29
> 项目: NewsAgg — 实时新闻聚合 + AI 智能评分系统
> 技术栈: Python 3.10+ / Flask / SQLite / Vue 3 / Tailwind CSS

---

## 已完成项 (上次审查后的改进)

以下问题已在之前的迭代中修复:

- [x] `utils/ai_client.py` — 已创建线程安全的 OpenAI 单例（带 `threading.Lock`）
- [x] `collectors/utils.py` — 已提取公共时间解析 (`parse_feed_time`) 和 HTML 清理 (`clean_html`)
- [x] `utils/text.py` — 已提取 `safe_truncate` 函数
- [x] `tests/` — 已创建 `test_db.py` 和 `test_scorer.py` 基础测试
- [x] `requirements.txt` — 已移除 APScheduler、requests 升级到 >=2.32.0、添加 pytest
- [x] DOMPurify — 前端已引入并集成到 `formatSummary()`
- [x] `.env.example` — 需确认是否已创建

---

## 一、安全问题（P0 — 必须立即修复）

### 1.1 硬编码的 Twitter Bearer Token

**位置**: `collectors/x_collector.py:10`

```python
BEARER_TOKEN = 'AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=...'
```

**风险**: Token 已提交到 git 历史，即使后续移除仍可被恢复。

**修复**:
1. 将 token 移到 `.env`: `X_BEARER_TOKEN=xxx`
2. `config.py` 添加: `X_BEARER_TOKEN = os.getenv('X_BEARER_TOKEN', '')`
3. `x_collector.py` 改为: `from config import X_BEARER_TOKEN`
4. **强烈建议**: 在 X/Twitter 后台轮换此 token

---

### 1.2 API 端点无鉴权

**位置**: `app.py` — 所有 `/api/*` 端点

服务绑定 `0.0.0.0:5000`，无任何认证。任何人可触发采集、评分、修改配置。

**修复**（二选一）:

- **方案 A**: API Key 中间件
  ```python
  @app.before_request
  def check_api_key():
      if request.path.startswith('/api/'):
          key = request.headers.get('X-API-Key') or request.args.get('api_key')
          if key != os.getenv('API_ACCESS_KEY'):
              return jsonify({'error': 'unauthorized'}), 401
  ```

- **方案 B**: 限制本地访问 `WEB_HOST = '127.0.0.1'`

---

### 1.3 `/api/config` 无输入校验

**位置**: `app.py:309-316`

接受任意 key-value 直接写入数据库。

**修复**:
```python
ALLOWED_CONFIG_KEYS = {'interest_weights', 'blocked_keywords', 'ai_model',
                       'refresh_interval', 'collect_interval', 'breaking_threshold'}
```

---

### 1.4 前端 `loadNews` 的 limit=500 无上限保护

**位置**: `static/index.html:663`

```javascript
const p = new URLSearchParams({sort:sortType.value, source:filterSource.value, limit:'500'});
```

前端硬编码请求 500 条，后端 `/api/news` 未对 `limit` 设上限。恶意用户可改为 `limit=999999` 导致数据库压力。

**修复**: 后端添加上限:
```python
limit = min(int(request.args.get('limit', 200)), 500)
```

---

## 二、Bug 与逻辑错误（P0-P1）

### 2.1 `app.py` 的 `get_ai_client()` 未使用统一实现

**位置**: `app.py:28-34`

`utils/ai_client.py` 已有线程安全的单例实现，但 `app.py` 仍然维护自己的 `_ai_client` 全局变量，且**没有加锁**:

```python
# app.py — 不安全的实现，与 utils/ai_client.py 重复
_ai_client = None
def get_ai_client():
    global _ai_client
    if _ai_client is None:  # 无锁，多线程竞争
        from openai import OpenAI
        _ai_client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
    return _ai_client
```

**修复**: 删除 `app.py:28-34`，改为:
```python
from utils.ai_client import get_ai_client
```

---

### 2.2 `app.py:324` 裸 `except:` 吞掉所有异常

**位置**: `app.py:324`

```python
try:
    return jsonify(json.loads(raw))
except:
    pass
```

**修复**:
```python
except (json.JSONDecodeError, TypeError) as e:
    logger.warning(f"interest_weights 配置解析失败: {e}")
```

---

### 2.3 `app.py:132-135` 参数转换无异常处理

用户传入非数字 `days`/`limit`/`offset` → 500 错误。

**修复**:
```python
try:
    days = int(days) if days is not None else None
except (ValueError, TypeError):
    return jsonify({'error': 'invalid days'}), 400

try:
    limit = min(int(request.args.get('limit', 200)), 500)
    offset = max(int(request.args.get('offset', 0)), 0)
except (ValueError, TypeError):
    return jsonify({'error': 'invalid limit/offset'}), 400
```

---

### 2.4 `scheduler.py:14` — `_running` 在信号处理器中使用但初始化时序有问题

**位置**: `scheduler.py:14-21`

```python
_running = False                    # 第14行: 初始化为 False

def _signal_handler(sig, frame):
    global _running
    _running = False                # 第18行: 信号处理
    ...

signal.signal(signal.SIGINT, _signal_handler)   # 第21行: 注册信号
signal.signal(signal.SIGTERM, _signal_handler)
```

信号处理器在模块导入时就注册了，但 `_running` 是在 `start_scheduler()` 中才设为 `True`。如果在 `start_scheduler()` 之前收到 SIGINT，行为正确但日志会输出误导性信息。

**修复**: 将信号注册移到 `start_scheduler()` 内部:
```python
def start_scheduler():
    global _running
    if _running:
        return
    _running = True
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    ...
```

---

### 2.5 `scheduler.py:55` 日志信息与实际不符

```python
logger.info("调度器启动完成，共4个采集线程")
```

实际启动了 5 个线程（RSS、X、RSSHub、热搜、AI评分）。

**修复**: 改为 `f"调度器启动完成，共{len(tasks)}个线程"`

---

### 2.6 `app.py` 首次采集与调度器存在竞态

**位置**: `app.py:372-373`

```python
threading.Thread(target=_first_collect, daemon=True).start()  # 启动采集线程
start_scheduler()                                              # 启动调度器
```

首次采集线程和调度器几乎同时启动，调度器的 RSS 采集任务可能与首次采集并发执行同一批源，导致重复请求和潜在的数据库锁竞争。

**修复**: 让首次采集完成后调度器才开始:
```python
if __name__ == '__main__':
    init_db()
    _first_collect()  # 同步执行首次采集
    start_scheduler()
    app.run(...)
```

---

### 2.7 `database/db.py` 连接泄漏

**位置**: 所有函数 — 手动 `get_conn()` + `conn.close()`，异常时连接泄漏。

**修复**: 改为上下文管理器:
```python
from contextlib import contextmanager

@contextmanager
def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()
```

---

### 2.8 `collectors/x_collector.py:192` 时间解析格式可能失败

```python
dt = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y') + timedelta(hours=8)
```

X/Twitter API v2 返回 ISO 8601 格式 (`2024-01-15T10:30:00.000Z`)，而非 v1 的 `%a %b %d ...` 格式。如果 API 返回格式变化，此处会静默失败（被 `except (ValueError, TypeError): pass` 捕获）。

**修复**: 使用 `collectors/utils.py` 的 `parse_feed_time` 或直接用 `datetime.fromisoformat`。

---

### 2.9 `rss_collector.py:86-88` 多余的包装函数

```python
def parse_pub_time(entry):
    """从feed entry解析发布时间，转为北京时间(UTC+8)"""
    return parse_feed_time(entry)
```

直接调用 `parse_feed_time` 即可，无需包装。同理 `rsshub_collector.py` 也应直接调用。

---

### 2.10 `app.py` 的 `_first_collect` 只采集不评分

**位置**: `app.py:353-366`

首次采集完成后没有触发评分，用户首次打开页面会看到大量未评分的新闻。

**修复**:
```python
def _first_collect():
    try:
        ...
        fetch_all_rss()
        fetch_x_tweets()
        fetch_rsshub_feeds()
        fetch_all_hotlists()
        from processors.scorer import batch_score
        batch_score(limit=50)  # 首次采集后立即评分
        logger.info("首次采集+评分完成")
    except Exception as e:
        logger.error(f"首次采集异常: {e}")
```

---

## 三、数据库问题（P1-P2）

### 3.1 缺少 `fetch_time` 索引

**位置**: `database/schema.sql`

`fetch_time` 用于排序和日期筛选（`ORDER BY fetch_time DESC`、`date(fetch_time) = date('now')`），但没有索引。

**修复**:
```sql
CREATE INDEX IF NOT EXISTS idx_fetch_time ON news(fetch_time);
```

---

### 3.2 无数据清理策略

数据库只增不删，长期运行后 `news.db` 会无限增长。当前已 11.3MB。

**修复**: 添加定期清理函数:
```python
def cleanup_old_news(days=30):
    """清理超过N天的旧新闻"""
    with get_conn() as conn:
        cursor = conn.execute(
            "DELETE FROM news WHERE fetch_time < datetime('now', ?)",
            (f'-{days} days',)
        )
        conn.commit()
        return cursor.rowcount
```

在调度器中定期调用（如每天一次）。

---

### 3.3 `db.py:22` 裸 `except:`

```python
try:
    conn.execute("ALTER TABLE news ADD COLUMN ai_summary TEXT")
    conn.commit()
except:
    pass
```

**修复**: `except sqlite3.OperationalError: pass`

---

## 四、前端问题（P2）

### 4.1 背景图使用 picsum.photos 随机图片

**位置**: `static/index.html:108`

```html
<img src="https://picsum.photos/1920/1080" alt="" loading="eager">
```

- 每次刷新页面加载一张不同的随机图片（~200KB+），浪费带宽
- `picsum.photos` 服务不稳定，可能拖慢页面加载
- 图片内容不可控（可能加载不当内容）
- 与新闻聚合应用的专业形象不符

**修复**: 使用本地背景图或纯 CSS 渐变:
```html
<div style="background:linear-gradient(135deg,#0f1117,#1a1d2e)"></div>
```

---

### 4.2 `formatSummary` 中 `v-html` 的链接未过滤

**位置**: `static/index.html:649-658`

虽然已集成 DOMPurify，但默认配置允许 `<a>` 标签。AI 返回的 markdown 中如果包含 `[text](javascript:alert(1))` 形式的链接，DOMPurify 默认会阻止 `javascript:` 协议，但建议显式配置:

```javascript
return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['strong', 'br', 'div', 'span'],
    ALLOWED_ATTR: ['style']
});
```

---

### 4.3 SSE 流式解析健壮性不足

**位置**: `static/index.html:730-735`（`sendChat` 和 `sendRAGChat`）

```javascript
for(const line of decoder.decode(value).split('\n')) {
    if(line.startsWith('data: ')) {
        const d = line.slice(6);
        if(d === '[DONE]') continue;
        try { const j = JSON.parse(d); ... } catch {}
    }
}
```

问题:
1. `decoder.decode(value)` 可能在多字节字符边界处截断，导致 JSON 解析失败
2. `catch {}` 静默吞掉解析错误，调试困难
3. SSE 数据可能跨多个 chunk，当前实现无法处理跨 chunk 的消息

**修复**: 使用 TextDecoder 的 `stream: true` 选项，并累积 buffer:
```javascript
const decoder = new TextDecoder();
let buffer = '';
// ...
buffer += decoder.decode(value, {stream: true});
const lines = buffer.split('\n');
buffer = lines.pop();  // 保留未完成的行
for(const line of lines) { ... }
```

---

### 4.4 `sendChat` 和 `sendRAGChat` 大量重复代码

**位置**: `static/index.html:722-758`

两个函数逻辑几乎相同，仅 API endpoint 和目标变量不同。

**修复**: 提取公共函数:
```javascript
const streamChat = async (url, messages, userMsg, targetRef, loadingRef) => {
    // 通用 SSE 流式聊天逻辑
};
```

---

### 4.5 Google Fonts 加载可能阻塞渲染

**位置**: `static/index.html:17`

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
```

`@import` 在 CSS 中是渲染阻塞的。如果 Google Fonts CDN 慢或被墙（在中国大陆），页面会延迟渲染。

**修复**: 改为 `<link>` 标签并添加 `font-display: swap`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

或者直接移除 Inter 字体，使用系统字体栈:
```css
* { font-family: system-ui, -apple-system, 'Segoe UI', sans-serif; }
```

---

## 五、代码质量（P2-P3）

### 5.1 `collectors/rss_collector.py` — 多个 RSS 源使用 HTTP

**位置**: `rss_collector.py:16-25`

新华网、人民网、百度新闻等源全部使用 `http://` 而非 `https://`。在公网上传输 RSS 内容可能被中间人篡改。

**修复**: 逐一验证并升级为 `https://`（部分源可能不支持 HTTPS，需测试）。

---

### 5.2 `hotlist_collector.py` — 热搜链接可能不唯一

**位置**: `hotlist_collector.py:24`

```python
link = f'https://s.weibo.com/weibo?q=%23{title}%23'
```

如果同一话题多次上热搜，`link` 相同会导致 `INSERT` 因 `UNIQUE` 约束失败（被 `insert_news` 的去重逻辑处理，但语义上热搜排名变化应更新而非丢弃）。

---

### 5.3 测试隔离不足

**位置**: `tests/test_db.py`

```python
@pytest.fixture
def setup_db():
    init_db()
    yield
    # 测试后清理（可选）  ← 注释掉了
```

测试使用真实数据库文件 `data/news.db`，且不清理测试数据。测试之间会互相影响。

**修复**: 使用独立的测试数据库:
```python
@pytest.fixture
def setup_db(tmp_path):
    import database.db as db_module
    original_path = db_module.DB_PATH
    db_module.DB_PATH = str(tmp_path / 'test.db')
    init_db()
    yield
    db_module.DB_PATH = original_path
```

---

### 5.4 缺少 `test_api.py`

当前只有 `test_db.py` 和 `test_scorer.py`，没有 API 端点测试。

**建议**: 使用 Flask 的 test client 添加:
```python
def test_api_news(client):
    response = client.get('/api/news')
    assert response.status_code == 200
    assert isinstance(response.json, list)
```

---

### 5.5 CORS 未限制来源

**位置**: `app.py:25`

```python
CORS(app)  # 允许所有来源
```

**修复**: 如果仅本地使用:
```python
CORS(app, origins=['http://localhost:5000', 'http://127.0.0.1:5000'])
```

---

### 5.6 `.env.example` 缺少 `X_BEARER_TOKEN`

当前 `.env.example`（如已创建）需要包含所有环境变量，特别是 Twitter token。

---

## 六、执行计划

| 阶段 | 内容 | 优先级 | 预估工作量 |
|------|------|--------|-----------|
| **Phase 1** | 安全: 1.1 移除硬编码 token, 1.2 API 鉴权, 1.3 配置校验 | P0 | 1 小时 |
| **Phase 2** | Bug: 2.1 统一 AI 客户端, 2.3 参数校验, 2.6 竞态, 2.7 连接管理 | P0-P1 | 2 小时 |
| **Phase 3** | 数据库: 3.1 索引, 3.2 清理策略, 3.3 裸 except | P1-P2 | 1 小时 |
| **Phase 4** | 前端: 4.1 背景图, 4.3 SSE 健壮性, 4.4 代码去重, 4.5 字体 | P2 | 2 小时 |
| **Phase 5** | 代码质量: 5.1-5.6 | P2-P3 | 2 小时 |

---

## 七、当前优点

- **模块化结构清晰**: collectors / processors / database / utils 分层合理
- **SQL 参数化查询**: 全部使用 `?` 占位符，无 SQL 注入风险
- **`.gitignore` 正确配置**: `.env`、数据库、日志均已排除
- **WAL 模式**: SQLite 启用 WAL 提升并发读写性能
- **AI 降级策略**: AI 不用时自动降级到规则引擎评分
- **提交规范**: 遵循 conventional commits 格式
- **公共工具已提取**: `utils/ai_client.py`、`collectors/utils.py`、`utils/text.py`
- **基础测试已存在**: `test_db.py`、`test_scorer.py`

---

## 八、功能升级方案

以下是从产品功能角度出发的升级建议，按价值/难度分级。

---

### A. AI 能力增强（高价值）

#### A1. 事件聚类 — 同一事件的多源报道归组

**现状**: 每条新闻独立存在，用户看到大量重复报道（如"美联储加息"可能有 20 条不同来源的报道）。

**方案**: 利用 AI 对新闻标题做 embedding 或关键词提取，将报道同一事件的新闻聚合成"事件簇"。

```
数据库新增表:
  events (id, title, direction, first_seen, last_updated, news_count, top_score)
  event_news (event_id, news_id)

前端展示:
  - 事件卡片展开后显示所有相关报道
  - "3家媒体报道了此事" 标记
  - 按事件维度排序而非单条新闻
```

**价值**: 消除信息冗余，让用户快速了解"有哪些大事发生"而非"有哪些新闻"。

---

#### A2. 情感分析 — 新闻情绪维度

**现状**: 评分只考虑重要性，不考虑情绪倾向。

**方案**: 在 AI 评分时增加情感维度输出:

```python
# scorer.py 返回值增加字段
{
    "sentiment": "positive",      # positive / neutral / negative
    "sentiment_score": 0.7,       # -1.0 ~ 1.0
    "market_implication": "bullish"  # bullish / bearish / neutral (仅财经)
}
```

**前端**:
- 新闻卡片显示情绪图标（正面/中性/负面）
- 统计面板显示"今日情绪分布"饼图
- 筛选: "只看负面新闻" → 适合投资者快速扫描风险

---

#### A3. 命名实体识别 (NER) — 实体卡片

**现状**: 新闻中提到的人、公司、国家没有被结构化提取。

**方案**: AI 评分时同时输出实体列表:

```python
{
    "entities": [
        {"name": "美联储", "type": "ORG"},
        {"name": "鲍威尔", "type": "PERSON"},
        {"name": "美国", "type": "GPE"},
    ]
}
```

**前端**:
- 点击实体名 → 查看所有提到该实体的新闻
- 实体热度排行: "本周最多被提及: 特斯拉(28次), 苹果(22次)"
- 实体关系图: 哪些实体经常一起出现

---

#### A4. 多语言翻译 — 国际新闻中文摘要

**现状**: BBC、CNN、Reuters 等英文源的内容对中文用户阅读门槛高。

**方案**: 对英文内容的新闻，AI 总结时要求输出中文:

```python
# _build_summary_prompt 中增加判断
if is_english(title):
    prompt += "\n请用中文总结此英文新闻，核心术语保留英文原文。"
```

**价值**: 让不懂英文的用户也能快速了解国际新闻。

---

#### A5. 每日/每周新闻简报自动生成

**现状**: 用户只能逐条浏览，没有聚合视图。

**方案**: AI 根据当日高分新闻生成简报:

```python
@app.route('/api/digest')
def api_digest():
    """生成每日新闻简报"""
    top_news = get_news_list(sort='score', days=0, limit=20)
    prompt = f"""基于以下{len(top_news)}条新闻，生成一份简洁的每日新闻简报。
    格式：
    1. 今日头条（1-2条最重要的）
    2. 国内要闻（3-5条）
    3. 国际动态（3-5条）
    4. 科技财经（3-5条）
    每条一句话概括，附带评分。"""
    ...
```

**前端**: 顶部新增"今日简报"卡片，一键展开。

---

### B. 采集能力扩展（中高价值）

#### B1. 新增采集源

当前采集源覆盖面有限，建议补充:

| 类型 | 新增源 | 实现方式 |
|------|--------|---------|
| Reddit | r/worldnews, r/technology, r/wallstreetbets | RSS (`reddit.com/.rss`) |
| Telegram | 公开频道（如 breaking_news） | RSSHub `/telegram/channel/{name}` |
| YouTube | 科技/财经频道 | RSSHub `/youtube/channel/{id}` |
| 政府公告 | 国务院、证监会、央行 | RSS 或直接抓取 |
| 学术 | arXiv AI/CS 论文 | RSS (`arxiv.org/rss/cs.AI`) |
| 数据 | 经济指标（CPI、PMI等） | 定时抓取国家统计局 |

---

#### B2. 用户自定义 RSS 源

**现状**: RSS 源列表硬编码在 `rss_collector.py`，用户无法添加。

**方案**:
```python
# 数据库新增表
user_sources (id, name, url, source_type, enabled, created_at)

# API
POST /api/sources      — 添加自定义源
GET  /api/sources       — 列出所有源（含自定义）
DELETE /api/sources/:id — 删除
```

**前端**: 设置页新增"订阅源管理"标签页。

---

#### B3. OPML 导入/导出

**方案**: 支持标准 OPML 格式导入导出 RSS 订阅列表，方便从其他阅读器迁移。

```python
@app.route('/api/sources/import', methods=['POST'])
def import_opml():
    """解析OPML文件，批量添加RSS源"""

@app.route('/api/sources/export')
def export_opml():
    """导出当前所有RSS源为OPML格式"""
```

---

### C. 前端体验升级（中价值）

#### C1. 新闻详情页

**现状**: 点击新闻只能看 AI 总结弹窗或跳转原文。

**方案**: 内建详情页，包含:
- 完整新闻内容（而非截断的 2000 字）
- AI 深度分析（而非仅 2-3 句总结）
- 相关新闻列表（同一事件/同一来源/同一方向）
- 时间线: 该事件的演变过程
- 笔记区（本地存储，仅自己可见）

---

#### C2. 看板视图 — 多列布局

**现状**: 只有列表视图。

**方案**: 新增看板模式，按方向分列:

```
| 政治 | 经济 | 科技 | 军事 | 财经 |
|------|------|------|------|------|
| 新闻1| 新闻3| 新闻5| 新闻7| 新闻9|
| 新闻2| 新闻4| 新闻6| 新闻8| 新闻10|
```

类似 Trello 的多列布局，一屏掌握各领域动态。

---

#### C3. 数据可视化面板

**现状**: 只有底部一行统计数字。

**方案**: 新增统计面板:
- **评分分布柱状图**: S+/S/A/B/C/D/E 各多少条
- **来源分布饼图**: 媒体/X/热搜/科技/财经各占比
- **时间趋势折线图**: 过去 7 天每日新闻量和平均评分
- **热门关键词词云**: 当前高分新闻的关键词

实现: 用 Chart.js (CDN) 或 ECharts，无需构建工具。

---

#### C4. 键盘快捷键

**方案**:
```
j/k     — 上/下一条新闻
o/Enter — 打开新闻
s       — 打开AI总结
/       — 聚焦搜索框
Escape  — 关闭弹窗
1-5     — 切换筛选标签
```

实现: 全局 `keydown` 事件监听，不依赖任何库。

---

#### C5. 新闻收藏/稍后读

**方案**:
```sql
ALTER TABLE news ADD COLUMN is_bookmarked BOOLEAN DEFAULT 0;
```

```python
# API
POST /api/news/:id/bookmark   — 收藏/取消
GET  /api/news?bookmarked=1   — 获取收藏列表
```

**前端**: 新闻卡片增加收藏按钮（星标），筛选栏增加"收藏"选项。

---

#### C6. 分享功能

**方案**: 一键复制新闻摘要 + 原文链接到剪贴板:

```javascript
const shareNews = (news) => {
    const text = `📰 ${news.title}\n评分: ${news.ai_score}\n${news.ai_summary || ''}\n${news.link}`;
    navigator.clipboard.writeText(text);
    showToast('已复制到剪贴板');
};
```

可扩展: 生成新闻卡片图片（Canvas API），适合社交媒体分享。

---

### D. 部署与运维（中价值）

#### D1. Docker 化

**现状**: 只有 `start.bat`/`start.sh`，无容器化支持。

**方案**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

配套 `docker-compose.yml`:
```yaml
services:
  newsagg:
    build: .
    ports: ["5000:5000"]
    volumes: ["./data:/app/data", "./logs:/app/logs"]
    env_file: .env
    restart: unless-stopped
```

---

#### D2. 健康检查端点

```python
@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'db': check_db_connection(),
        'last_collect': get_last_collect_time(),
        'news_count': get_statistics()['total'],
    })
```

---

#### D3. 定时数据清理

```python
# scheduler.py 中添加每日清理任务
def daily_cleanup():
    deleted = cleanup_old_news(days=30)
    logger.info(f"清理了 {deleted} 条过期新闻")

# 每天凌晨3点执行
tasks.append((daily_cleanup, 86400, '每日数据清理'))
```

---

### E. 外部集成（低-中价值）

#### E1. RSS 输出 — 让其他阅读器订阅

**方案**: 将高分新闻以 RSS feed 形式输出:

```python
@app.route('/api/feed/rss')
def rss_feed():
    """输出高分新闻的RSS feed"""
    top = get_news_list(sort='score', limit=50)
    # 生成 RSS XML
```

用户可以用任何 RSS 阅读器订阅 `http://localhost:5000/api/feed/rss`。

---

#### E2. Webhook 通知

**方案**: 当出现 S+ 级别新闻时，发送 webhook:

```python
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')

def notify_breaking(news):
    if WEBHOOK_URL and news['ai_score'] >= 95:
        requests.post(WEBHOOK_URL, json={
            'text': f"🔴 S+级新闻: {news['title']}\n评分: {news['ai_score']}\n{news['link']}",
        })
```

可对接: Slack、飞书、钉钉、企业微信、Discord。

---

#### E3. Telegram Bot

**方案**: 推送高分新闻到 Telegram 频道/群组:

```python
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram(text):
    requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage', json={
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
        'parse_mode': 'HTML',
    })
```

---

### F. 评分系统升级（低-中价值）

#### F1. 用户反馈修正评分

**现状**: 评分完全由 AI + 规则决定，用户无法纠正。

**方案**:
```sql
ALTER TABLE news ADD COLUMN user_score_adj INTEGER DEFAULT 0;
-- 用户手动调整的分数偏移量
```

```python
POST /api/news/:id/score/adjust  — {"delta": +10} 或 {"delta": -15}
```

前端: 长按评分 badge 弹出调整滑块。用户的调整信号可用于微调规则引擎权重。

---

#### F2. 评分 A/B 测试

**现状**: 评分 prompt 和权重硬编码，无法对比效果。

**方案**: 支持多套评分策略并行运行:

```python
SCORE_STRATEGIES = {
    'v1': {'prompt': '...', 'weights': {...}},
    'v2': {'prompt': '...', 'weights': {...}},
}
```

对同一条新闻用不同策略评分，记录结果，后期对比哪个策略的用户点击率/阅读时长更高。

---

### G. 优先级排序总览

| 优先级 | 功能 | 理由 | 工作量 |
|--------|------|------|--------|
| **P0** | A5 每日简报 | 最高 ROI，AI 能力直接体现 | 2h |
| **P0** | C5 收藏/稍后读 | 用户刚需，实现简单 | 1h |
| **P1** | A1 事件聚类 | 核心差异化功能 | 8h |
| **P1** | A2 情感分析 | AI 评分时顺带输出 | 2h |
| **P1** | B2 自定义 RSS 源 | 用户个性化需求 | 3h |
| **P1** | D1 Docker 化 | 部署便利性 | 2h |
| **P2** | C3 数据可视化 | 信息密度提升 | 4h |
| **P2** | A3 命名实体 | 深度分析基础 | 3h |
| **P2** | C1 新闻详情页 | 用户体验提升 | 4h |
| **P2** | E1 RSS 输出 | 生态打通 | 2h |
| **P3** | A4 多语言翻译 | 面向中文用户的国际新闻 | 2h |
| **P3** | C2 看板视图 | 进阶用户需求 | 4h |
| **P3** | C4 键盘快捷键 | 效率用户需求 | 1h |
| **P3** | C6 分享功能 | 社交传播 | 1h |
| **P3** | E2 Webhook | 企业用户需求 | 1h |
| **P3** | E3 Telegram Bot | 推送通知 | 2h |
| **P3** | B3 OPML 导入导出 | 迁移便利 | 2h |
| **P3** | F1 用户反馈修正 | 评分系统迭代 | 2h |
| **P3** | F2 评分 A/B 测试 | 评分策略优化 | 3h |

---

## 九、信息源全面升级方案

> 详见独立文档: [SOURCE_UPGRADE_PLAN.md](SOURCE_UPGRADE_PLAN.md)
>
> 涵盖: Truth Social 实时监控、美联储一手信息、大使馆/外交渠道、国际财经大咖扩充（25+人）、科技公司一手消息（15+源）、学术/地缘/法律监管源、采集架构分层调度优化。
