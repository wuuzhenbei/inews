# NewsAgg 信息源全面升级方案

> 针对个人项目场景，重点优化信息采集的**广度、深度和时效性**。
> 最后更新: 2026-05-29

---

## 目录

1. [Trump Truth Social 实时监控](#1-trump-truth-social-实时监控)
2. [美联储 (Federal Reserve)](#2-美联储-federal-reserve)
3. [大使馆/外交机构](#3-大使馆外交机构)
4. [国际财经大咖](#4-国际财经大咖)
5. [科技公司一手消息](#5-科技公司一手消息)
6. [专业领域信息源](#6-专业领域信息源)
7. [采集架构优化](#7-采集架构优化)
8. [完整源清单汇总](#8-完整源清单汇总)
9. [快速实现路径](#9-快速实现路径)

---

## 1. Trump Truth Social 实时监控

Trump 主要活跃在 Truth Social 而非 X，必须单独采集。

### 方案 A — RSSHub（推荐）

RSSHub 提供 Truth Social 路由，需本地部署 RSSHub Docker 实例:

```python
# rsshub_collector.py 新增
{'name': 'Trump-TruthSocial', 'url': '/truthsocial/user/realDonaldTrump', 'type': 'truthsocial', 'priority': 'S'}
```

### 方案 B — 直接抓取

Truth Social 有公开 API（无需登录）:

```python
# collectors/truthsocial_collector.py
TRUTHSOCIAL_ACCOUNTS = [
    {'name': '特朗普', 'username': 'realDonaldTrump', 'priority': 'S'},
]

class TruthSocialScraper:
    def get_account_id(self, username):
        r = requests.get(f'https://truthsocial.com/api/v1/accounts/lookup?acct={username}')
        return r.json().get('id')

    def get_statuses(self, account_id, limit=20):
        r = requests.get(f'https://truthsocial.com/api/v1/accounts/{account_id}/statuses?limit={limit}')
        return r.json()
```

**需要新增**: `collectors/truthsocial_collector.py`，并在 `scheduler.py` 中添加调度。

### 可扩展的 Truth Social 账号

```python
TRUTHSOCIAL_ACCOUNTS = [
    {'name': '特朗普', 'username': 'realDonaldTrump', 'priority': 'S'},
    # 未来可扩展其他 Truth Social 用户
]
```

---

## 2. 美联储 (Federal Reserve)

美联储是全球金融风向标，必须覆盖其所有公开渠道。

### RSS 源（全部免费、官方）

```python
# rss_collector.py 新增 — 美联储专区
{'name': '美联储·全部新闻', 'url': 'https://www.federalreserve.gov/feeds/press_all.xml', 'type': 'fed'},
{'name': '美联储·演讲', 'url': 'https://www.federalreserve.gov/feeds/speeches.xml', 'type': 'fed'},
{'name': '美联储·FOMC纪要', 'url': 'https://www.federalreserve.gov/feeds/fomcminutes.xml', 'type': 'fed'},
{'name': '美联储·监管动态', 'url': 'https://www.federalreserve.gov/feeds/press_regulatory.xml', 'type': 'fed'},
{'name': '美联储·数据发布', 'url': 'https://www.federalreserve.gov/feeds/press_data.xml', 'type': 'fed'},
```

### X 账号

```python
# x_collector.py 新增
{'name': '美联储官方', 'screen_name': 'federalreserve', 'priority': 'S'},
{'name': '纽约联储', 'screen_name': 'newyorkfed', 'priority': 'A'},
{'name': '旧金山联储', 'screen_name': 'sffaborul', 'priority': 'B'},
```

### 其他国家央行

```python
{'name': '欧央行', 'screen_name': 'ecb', 'priority': 'A'},
{'name': '英格兰银行', 'screen_name': 'bankofengland', 'priority': 'A'},
{'name': '日本央行', 'screen_name': 'bank_of_japan', 'priority': 'A'},
{'name': '中国人民银行', 'screen_name': 'PBC', 'priority': 'A'},  # 注意：可能无X账号
```

### 其他央行 RSS

```python
{'name': '欧央行·新闻', 'url': 'https://www.ecb.europa.eu/rss/press.html', 'type': 'fed'},
{'name': '英格兰银行·新闻', 'url': 'https://www.bankofengland.co.uk/rss/news', 'type': 'fed'},
{'name': 'BIS国际清算银行', 'url': 'https://www.bis.org/doclist/pressrelease.rss', 'type': 'fed'},
```

---

## 3. 大使馆/外交机构

大使馆是获取外交政策第一手信息的重要渠道。

### RSS 源（通过 RSSHub）

```python
# rsshub_collector.py 新增 — 外交渠道
{'name': '美国国务院', 'url': '/state/briefing', 'type': 'diplomatic', 'priority': 'S'},
{'name': '中国外交部', 'url': '/fmprc/fyrbt', 'type': 'diplomatic', 'priority': 'S'},
```

### 直接 RSS

```python
{'name': '美国国务院·新闻', 'url': 'https://www.state.gov/feeds/all-stories/', 'type': 'diplomatic'},
{'name': '英国外交部', 'url': 'https://www.gov.uk/government/organisations/foreign-commonwealth-office.atom', 'type': 'diplomatic'},
{'name': '联合国新闻', 'url': 'https://news.un.org/feed/subscribe/en/news/all/rss.xml', 'type': 'diplomatic'},
{'name': 'NATO新闻', 'url': 'https://www.nato.int/rss/news.xml', 'type': 'diplomatic'},
```

### X 账号

```python
# x_collector.py 新增 — 外交/大使馆
{'name': '美国国务院', 'screen_name': 'StateDept', 'priority': 'S'},
{'name': '中国外交部发言人', 'screen_name': 'MFA_China', 'priority': 'A'},
{'name': '俄罗斯外交部', 'screen_name': 'maborul_russia', 'priority': 'A'},
{'name': '以色列总理', 'screen_name': 'IsraeliPM', 'priority': 'A'},
{'name': '伊朗外交部', 'screen_name': 'IRIMFA_EN', 'priority': 'B'},
{'name': '联合国', 'screen_name': 'UN', 'priority': 'A'},
{'name': 'NATO', 'screen_name': 'NATO', 'priority': 'A'},
{'name': '欧盟外交', 'screen_name': 'eu_eeas', 'priority': 'A'},
```

---

## 4. 国际财经大咖

当前 X 账号列表缺少很多关键人物。以下是分层扩充。

### Tier 1 — S级（全球顶级，必须监控）

```python
# 对冲基金大佬
{'name': 'Bill Ackman', 'screen_name': 'BillAckman', 'priority': 'S'},
{'name': 'Carl Icahn', 'screen_name': 'Carl_C_Icahn', 'priority': 'S'},
{'name': 'Mark Cuban', 'screen_name': 'mcuban', 'priority': 'A'},
{'name': 'Chamath Palihapitiya', 'screen_name': 'chamath', 'priority': 'A'},
{'name': 'Michael Burry', 'screen_name': 'michaeljburry', 'priority': 'S'},  # Big Short

# 宏观经济学家
{'name': 'Mohamed El-Erian', 'screen_name': 'elerianm', 'priority': 'S'},  # Allianz首席经济顾问
{'name': 'Larry Summers', 'screen_name': 'LHSummers', 'priority': 'A'},   # 前美财政部长
{'name': 'Paul Krugman', 'screen_name': 'paborul', 'priority': 'A'},      # 诺贝尔经济学奖
{'name': 'Nassim Taleb', 'screen_name': 'nntaleb', 'priority': 'A'},      # 黑天鹅作者

# 华尔街顶流
{'name': 'Game of Trades', 'screen_name': 'GameofTrades_', 'priority': 'A'},
{'name': 'Wall Street Silver', 'screen_name': 'WallStreetSilv', 'priority': 'A'},
{'name': 'Zerohedge', 'screen_name': 'ZeroHedge', 'priority': 'S'},       # 财经快讯极快
{'name': 'unusual_whales', 'screen_name': 'unusual_whales', 'priority': 'A'},  # 期权异动
{'name': 'Jesse Felder', 'screen_name': 'jessefelder', 'priority': 'A'},  # Felder Report
```

### Tier 2 — 加密/科技投资

```python
{'name': 'Arthur Hayes', 'screen_name': 'CryptoHayes', 'priority': 'A'},  # BitMEX创始人
{'name': 'Balaji', 'screen_name': 'balaborul', 'priority': 'A'},          # 前Coinbase CTO
{'name': 'Raoul Pal', 'screen_name': 'RaoulGMI', 'priority': 'A'},       # Real Vision创始人
{'name': 'Lyn Alden', 'screen_name': 'LynAldenContact', 'priority': 'A'}, # 宏观分析师
{'name': 'PlanB', 'screen_name': 'planaborni_', 'priority': 'A'},         # S2F模型作者
```

### 已有账号（参考，避免重复）

```
已有: RayDalio, PeterSchiff, CathieDWood, saylor, VitalikButerin, binance,
      brian_armstrong, Nouriel, jimcramer, planaborni_
```

---

## 5. 科技公司一手消息

当前 RSS 列表缺少很多重要科技公司的官方信息源。

### AI 公司（最重要）

```python
{'name': 'Anthropic Blog', 'url': 'https://www.anthropic.com/rss.xml', 'type': 'tech'},
{'name': 'DeepMind Blog', 'url': 'https://deepmind.google/blog/rss.xml', 'type': 'tech'},
{'name': 'Hugging Face Blog', 'url': 'https://huggingface.co/blog/feed.xml', 'type': 'tech'},
{'name': 'Stability AI', 'url': 'https://stability.ai/blog/rss.xml', 'type': 'tech'},
{'name': 'Mistral AI', 'url': 'https://mistral.ai/feed.xml', 'type': 'tech'},
{'name': 'Perplexity Blog', 'url': 'https://www.perplexity.ai/hub/feed', 'type': 'tech'},
{'name': 'Cohere Blog', 'url': 'https://txt.cohere.com/rss/', 'type': 'tech'},
```

### 芯片/硬件

```python
{'name': 'TSMC', 'url': 'https://pr.tsmc.com/english/rss/news.xml', 'type': 'tech'},
{'name': 'ASML', 'url': 'https://www.asml.com/en/rss', 'type': 'tech'},
{'name': 'Broadcom', 'url': 'https://www.broadcom.com/blog/rss', 'type': 'tech'},
{'name': 'Arm Blog', 'url': 'https://community.arm.com/arm-community-blogs/b/blog.rss', 'type': 'tech'},
```

### 云计算/SaaS

```python
{'name': 'Stripe Blog', 'url': 'https://stripe.com/blog/feed.rss', 'type': 'tech'},
{'name': 'Vercel Blog', 'url': 'https://vercel.com/atom', 'type': 'tech'},
{'name': 'Supabase Blog', 'url': 'https://supabase.com/blog/rss.xml', 'type': 'tech'},
{'name': 'Docker Blog', 'url': 'https://www.docker.com/blog/feed/', 'type': 'tech'},
{'name': 'MongoDB Blog', 'url': 'https://www.mongodb.com/developer/feeds/all/rss.xml', 'type': 'tech'},
```

### 新能源/汽车

```python
{'name': 'Rivian', 'url': 'https://rivian.com/newsroom/rss', 'type': 'tech'},
{'name': 'Lucid Motors', 'url': 'https://lucidmotors.com/newsroom/rss', 'type': 'tech'},
{'name': '蔚来汽车', 'url': 'https://www.nio.com/news/rss', 'type': 'tech'},
{'name': '理想汽车', 'url': 'https://www.lixiang.com/en/news.rss', 'type': 'tech'},
```

### 中国 AI 公司

```python
{'name': '百度AI', 'url': 'https://ai.baidu.com/rss', 'type': 'tech'},
{'name': '阿里云博客', 'url': 'https://developer.aliyun.com/article/rss', 'type': 'tech'},
{'name': '字节跳动技术博客', 'url': 'https://techblog.toutiao.com/feed', 'type': 'tech'},
{'name': '月之暗面(Kimi)', 'url': 'https://www.moonshot.cn/blog/rss', 'type': 'tech'},
{'name': '智谱AI', 'url': 'https://www.zhipuai.cn/blog/rss', 'type': 'tech'},
```

### 科技公司 X 账号补充

```python
{'name': 'Demis Hassabis', 'screen_name': 'demaborul', 'priority': 'A'},  # DeepMind CEO
{'name': 'Lisa Su (AMD)', 'screen_name': 'LisaSu', 'priority': 'A'},      # AMD CEO
{'name': 'Dario Amodei', 'screen_name': 'DarioAmodei', 'priority': 'A'},  # Anthropic CEO
{'name': 'Mistral AI', 'screen_name': 'MistralAI', 'priority': 'A'},
{'name': 'Perplexity', 'screen_name': 'perplexity_ai', 'priority': 'A'},  # AI搜索新势力
{'name': 'Jensen Huang', 'screen_name': 'nvidia', 'priority': 'A'},       # 已有
{'name': 'Tim Cook', 'screen_name': 'tim_cook', 'priority': 'A'},         # 已有
{'name': 'Satya Nadella', 'screen_name': 'sataborasu', 'priority': 'A'},  # 已有
{'name': 'Elon Musk', 'screen_name': 'elonmusk', 'priority': 'S'},        # 已有
{'name': 'Mark Zuckerberg', 'screen_name': 'zuck', 'priority': 'S'},      # 已有
{'name': 'Sam Altman', 'screen_name': 'sama', 'priority': 'S'},           # 已有
```

---

## 6. 专业领域信息源

### 加密货币（扩充）

```python
# RSS
{'name': 'The Block', 'url': 'https://www.theblock.co/rss.xml', 'type': 'crypto'},
{'name': 'Decrypt', 'url': 'https://decrypt.co/feed', 'type': 'crypto'},
{'name': 'Cointelegraph', 'url': 'https://cointelegraph.com/rss', 'type': 'crypto'},
{'name': 'Bitcoin Magazine', 'url': 'https://bitcoinmagazine.com/feed', 'type': 'crypto'},
{'name': 'DefiLlama', 'url': 'https://defillama.com/rss', 'type': 'crypto'},  # DeFi数据

# X
{'name': 'SEC', 'screen_name': 'SECGov', 'priority': 'A'},
{'name': 'CFTC', 'screen_name': 'CFTC', 'priority': 'A'},       # 美国商品期货委员会
{'name': 'Gary Gensler', 'screen_name': 'GaryGensler', 'priority': 'A'},
```

### 地缘政治/军事

```python
# X
{'name': 'ISW战争研究所', 'screen_name': 'TheStudyofWar', 'priority': 'A'},
{'name': 'OSINT开源情报', 'screen_name': 'sentdefender', 'priority': 'A'},
{'name': 'War Monitor', 'screen_name': 'warmonitor3', 'priority': 'A'},
{'name': 'Pentagon五角大楼', 'screen_name': 'DeptofDefense', 'priority': 'A'},
{'name': 'CIA', 'screen_name': 'CIA', 'priority': 'B'},
{'name': 'MI6英国军情六处', 'screen_name': 'MI6', 'priority': 'B'},

# RSS
{'name': 'ISW战争研究所', 'url': 'https://www.understandingwar.org/rss.xml', 'type': 'geopolitical'},
{'name': 'CSIS战略', 'url': 'https://www.csis.org/analysis/feed', 'type': 'geopolitical'},
{'name': 'RAND智库', 'url': 'https://www.rand.org/pubs/topics.rss', 'type': 'geopolitical'},
```

### 科学/学术

```python
# RSS
{'name': 'Nature News', 'url': 'https://www.nature.com/nature.rss', 'type': 'science'},
{'name': 'Science News', 'url': 'https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science', 'type': 'science'},
{'name': 'arXiv AI', 'url': 'http://arxiv.org/rss/cs.AI', 'type': 'science'},
{'name': 'arXiv ML', 'url': 'http://arxiv.org/rss/cs.LG', 'type': 'science'},
{'name': 'arXiv 量化金融', 'url': 'http://arxiv.org/rss/q-fin', 'type': 'science'},
{'name': 'MIT Technology Review', 'url': 'https://www.technologyreview.com/feed/', 'type': 'science'},
{'name': 'Wired Science', 'url': 'https://www.wired.com/feed/category/science/latest/rss', 'type': 'science'},
```

### 法律/监管

```python
# X
{'name': '美国最高法院', 'screen_name': 'Scotus', 'priority': 'A'},
{'name': 'DOJ美国司法部', 'screen_name': 'TheJusticeDept', 'priority': 'A'},
{'name': 'FTC联邦贸易委', 'screen_name': 'FTC', 'priority': 'A'},

# RSS
{'name': '美国司法部·新闻', 'url': 'https://www.justice.gov/feeds/opa-press.xml', 'type': 'diplomatic'},
{'name': 'SEC新闻', 'url': 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=&dateb=&owner=include&count=40&search_text=&action=getcompany.rss', 'type': 'finance'},
```

---

## 7. 采集架构优化

### 7.1 优先级分层调度

当前所有源的采集频率相同，应按重要性分层:

```python
# config.py 修改采集频率
FETCH_INTERVAL_TIER1 = 60      # S级源: 1分钟（Trump TruthSocial、Fed、Breaking News）
FETCH_INTERVAL_TIER2 = 300     # A级源: 5分钟（主流媒体、央行、科技大佬）
FETCH_INTERVAL_TIER3 = 900     # B级源: 15分钟（热榜、一般媒体）
FETCH_INTERVAL_TIER4 = 1800    # 普通源: 30分钟（科技博客、RSSHub）
```

每个源配置中标注 `tier` 字段，调度器根据 tier 选择不同间隔。

### 7.2 新增 `source_type` 分类

当前只有 `media/x/hotlist/tech/finance`，建议扩展:

```python
SOURCE_TYPES = {
    'media':        '权威媒体',
    'x':            'X/Twitter',
    'truthsocial':  'Truth Social',   # 新增
    'hotlist':      '热搜热榜',
    'tech':         '科技',
    'finance':      '财经',
    'fed':          '央行/监管',       # 新增
    'diplomatic':   '外交',            # 新增
    'science':      '学术/科学',       # 新增
    'crypto':       '加密货币',        # 新增
    'geopolitical': '地缘政治',        # 新增
}
```

前端筛选栏相应扩展。

### 7.3 X 采集改为分优先级调度

当前 X 采集一次性遍历所有账号，应按 priority 分组:

```python
def fetch_x_tweets(priority_filter=None):
    """按优先级分组采集"""
    accounts = X_ACCOUNTS
    if priority_filter:
        accounts = [a for a in accounts if a['priority'] == priority_filter]
    ...
```

- S 级账号: 每 2 分钟采集一次
- A 级账号: 每 5 分钟采集一次
- B 级账号: 每 15 分钟采集一次

### 7.4 RSSHub 实例优化

当前 RSSHub 配置仅 `localhost:1200`，建议:

1. **本地 Docker 部署**: `docker run -d -p 1200:1200 diygod/rsshub`
2. **备用公共实例**: 已有 `PUBLIC_RSSHUB_INSTANCES` 列表，可扩展
3. **自建缓存**: 对频繁访问的 RSSHub 路由做本地缓存，减少对上游的压力

---

## 8. 完整源清单汇总

以下是升级后的完整信息源覆盖:

| 类别 | 当前数量 | 升级后数量 | 关键新增 |
|------|---------|-----------|---------|
| RSS 媒体 | 19 | 25+ | 美联储5个、国务院、联合国、NATO |
| RSS 科技 | 26 | 45+ | Anthropic、DeepMind、Mistral、arXiv、Nature、Science |
| RSS 财经 | 2 | 8+ | The Block、Decrypt、Cointelegraph、BIS |
| X 账号 | 55 | 85+ | Bill Ackman、El-Erian、ZeroHedge、SEC、ISW |
| Truth Social | 0 | 1+ | Trump |
| 热搜热榜 | 5 | 5 | 不变 |
| 外交渠道 | 0 | 6+ | 美国务院、中国外交部、NATO、联合国 |
| 央行渠道 | 0 | 8+ | 美联储、欧央行、英格兰银行、BIS |
| 学术/科学 | 0 | 7+ | Nature、Science、arXiv AI/ML/Q-Fin |
| 地缘政治 | 0 | 5+ | ISW、CSIS、RAND、五角大楼 |
| 法律/监管 | 0 | 4+ | SEC、DOJ、FTC、CFTC |

---

## 9. 快速实现路径

### 第一步（30分钟）— 美联储 + Truth Social

1. 在 `rss_collector.py` 的 `RSS_SOURCES` 中追加 5 条美联储 RSS（type 改为 `fed`）
2. 在 `rsshub_collector.py` 的 `RSSHUB_ROUTES` 中追加 Truth Social 路由
3. 在 `config.py` 中新增 `FETCH_INTERVAL_TIER1 = 60`
4. 测试验证

### 第二步（30分钟）— 扩充 X 账号

1. 在 `x_collector.py` 的 `X_ACCOUNTS` 中追加上述所有新账号
2. 修改 `fetch_x_tweets()` 支持按 priority 分组采集
3. 在 `scheduler.py` 中为不同 priority 的 X 账号设置不同采集间隔

### 第三步（1小时）— 科技公司 + 学术源

1. 在 `rss_collector.py` 中追加 AI 公司、芯片公司、学术源 RSS
2. 在 `config.py` 中新增 `source_type` 分类映射
3. 前端筛选栏扩展新分类

### 第四步（1小时）— 外交 + 地缘 + 法律

1. 在 `rsshub_collector.py` 中追加外交渠道
2. 在 `rss_collector.py` 中追加直接 RSS（国务院、联合国、NATO、DOJ）
3. 在 `x_collector.py` 中追加地缘政治、法律监管账号
