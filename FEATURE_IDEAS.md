# NewsAgg 功能创意大全

> 个人项目 + token 无限制 = 尽情发挥 AI 能力
> 最后更新: 2026-05-29
> 目标: 把这个新闻聚合器打造成个人的 **AI 驱动情报中心**

---

## 目录

- [A. AI 深度分析](#a-ai-深度分析)
- [B. 智能研究工具](#b-智能研究工具)
- [C. 数据分析与洞察](#c-数据分析与洞察)
- [D. 自动化与监控](#d-自动化与监控)
- [E. 可视化](#e-可视化)
- [F. 外部集成与导出](#f-外部集成与导出)
- [G. 个人效率工具](#g-个人效率工具)
- [H. 内容创作辅助](#h-内容创作辅助)
- [I. 金融/投资专用](#i-金融投资专用)
- [J. 学习与知识管理](#j-学习与知识管理)
- [K. 高级采集](#k-高级采集)
- [L. 实验性功能](#l-实验性功能)

---

## A. AI 深度分析

token 无限制 = 可以对每条新闻做尽可能深入的 AI 分析。

### A1. 多视角分析（同一事件不同立场）

对同一条新闻，AI 分别从不同立场分析:

```python
PERSPECTIVES = {
    '华尔街': '从投资者/金融角度分析',
    '白宫': '从美国政府/政策角度分析',
    '北京': '从中国政府/外交角度分析',
    '科技圈': '从技术/创新角度分析',
    '普通民众': '从普通人生活影响角度分析',
}
```

前端: 切换 tab 看不同视角的分析，一屏理解事件全貌。

### A2. AI 事实核查

AI 交叉验证新闻中的关键声明:

```python
def fact_check(news):
    prompt = f"""对以下新闻中的关键事实声明进行核查:
    1. 列出所有可验证的事实声明
    2. 对每条声明，指出可能的验证来源
    3. 标注哪些是已证实的、哪些是存疑的、哪些可能是误导
    4. 检查是否有逻辑矛盾或数据错误

    新闻: {news['title']}
    内容: {news['content']}"""
```

### A3. AI 偏见检测

分析新闻的叙事框架和潜在偏见:

```python
def detect_bias(news):
    prompt = f"""分析以下新闻的叙事偏见:
    1. 标题是否有煽动性/倾向性?
    2. 是否选择性呈现事实?
    3. 引用的消息源是否多元?
    4. 与同一事件的其他报道对比，这篇的立场是什么?
    5. 偏见评分: -1(极左) 到 +1(极右), 0=中立"""
```

### A4. AI 影响预测

基于新闻内容预测后续发展:

```python
def predict_impact(news):
    prompt = f"""基于历史经验和当前形势，预测此事件的后续发展:
    1. 未来24小时可能的进展
    2. 未来1周的可能走向
    3. 对相关市场/行业/地区的具体影响
    4. 需要关注的关键信号（什么情况下预期会改变）
    5. 历史上类似事件的先例和结果"""
```

### A5. AI 事件关联发现

自动发现新闻之间的隐藏关联:

```python
def find_connections(current_news, recent_news):
    prompt = f"""分析以下新闻之间的潜在关联:
    当前新闻: {current_news['title']}
    最近新闻: {[n['title'] for n in recent_news[:20]]}

    找出:
    1. 直接关联（同一事件的不同报道）
    2. 间接关联（因果关系、产业链关系）
    3. 模式识别（类似事件重复出现）
    4. 时间线关联（按时间顺序的事件链）"""
```

### A6. AI 竞争对手分析

针对科技/商业新闻，分析竞争格局:

```python
def competitive_analysis(news):
    prompt = f"""基于此新闻，分析相关公司的竞争格局:
    1. 各家公司的战略动向
    2. 市场份额变化趋势
    3. 技术路线对比
    4. 护城河分析
    5. 投资价值判断"""
```

### A7. AI 全文翻译（非摘要）

对英文新闻做完整中文翻译（token 密集型，但你有无限 token）:

```python
def full_translate(content):
    prompt = f"""将以下英文新闻翻译为中文，要求:
    1. 专业术语保留英文原文（如 FOMC、GDP）
    2. 人名/公司名使用通用中文译名
    3. 保持原文段落结构
    4. 翻译准确流畅

    {content[:3000]}"""
```

### A8. AI 生成新闻评注

AI 对新闻加上专业评注:

```python
def annotate_news(news):
    prompt = f"""对以下新闻添加专业评注:
    1. 在关键信息处标注 [评注: ...]
    2. 解释专业术语
    3. 补充背景知识
    4. 指出需要进一步关注的要点
    5. 标注信息来源的可信度

    {news['content']}"""
```

### A9. AI 辩论模拟

让 AI 模拟不同专家对此事件的辩论:

```python
def simulate_debate(news):
    prompt = f"""模拟以下角色对此新闻的辩论:
    - 沃伦·巴菲特（价值投资者视角）
    - 埃隆·马斯克（科技颠覆者视角）
    - 一位中国经济学家（中国立场）
    - 一位普通美国选民（民生视角）

    每人发言2-3轮，有交锋有反驳。"""
```

### A10. AI 风险评估

对新闻涉及的风险做结构化评估:

```python
def risk_assessment(news):
    prompt = f"""对此新闻进行风险评估:
    1. 市场风险: 对股市/债市/汇市的影响程度 (1-10)
    2. 地缘风险: 是否加剧国际紧张 (1-10)
    3. 技术风险: 对相关技术发展的影响 (1-10)
    4. 监管风险: 是否可能引发监管行动 (1-10)
    5. 社会风险: 对公众情绪/社会稳定的影响 (1-10)
    综合风险等级: 低/中/高/极高"""
```

---

## B. 智能研究工具

### B1. 话题深度研究（Research Mode）

用户输入一个话题，AI 自动从新闻库中挖掘所有相关信息:

```python
@app.route('/api/research', methods=['POST'])
def research_topic():
    topic = request.json.get('topic')
    # 1. 从数据库搜索相关新闻
    related = search_news(topic, limit=50)
    # 2. AI 生成研究报告
    prompt = f"""基于以下{len(related)}条关于"{topic}"的新闻，生成一份深度研究报告:
    1. 概述（100字）
    2. 时间线（按时间排列的关键事件）
    3. 各方立场（不同国家/公司/人物的态度）
    4. 数据分析（涉及的关键数字和趋势）
    5. 未来展望（可能的发展方向）
    6. 关键人物（谁在推动/影响此事）
    7. 投资启示（对投资者的建议）"""
```

### B2. 专家观点汇总

自动收集不同专家对同一话题的看法:

```python
def expert_roundup(topic):
    # 搜索所有提到该话题的 X 账号推文
    # 按账号分类汇总观点
    prompt = f"""汇总以下专家对"{topic}"的观点:
    {expert_tweets}

    输出格式:
    - 看多阵营: [专家名] 认为...
    - 看空阵营: [专家名] 认为...
    - 中立/观望: [专家名] 认为..."""
```

### B3. 政策追踪器

追踪特定政策/法规的进展:

```python
POLICY_TRACKERS = [
    '美国对华关税',
    '美联储利率决策',
    'AI监管立法',
    '加密货币监管',
    'TikTok禁令',
]

def track_policy(policy_name):
    # 搜索相关新闻，按时间线排列
    # AI 分析政策当前状态和下一步
```

### B4. 公司档案自动生成

自动为每个被提及的公司生成档案:

```python
def generate_company_profile(company_name):
    # 搜索所有提到该公司的新闻
    news = search_news(company_name, limit=100)
    prompt = f"""基于以下新闻，生成{company_name}的公司档案:
    1. 基本信息（行业、市值、创始人等）
    2. 近期重大事件时间线
    3. 竞争对手和市场地位
    4. 技术优势和风险
    5. 近期新闻情绪趋势
    6. 关键人物动态
    7. 投资者关注点"""
```

### B5. 人物档案自动生成

自动为每个被提及的人物生成档案:

```python
def generate_person_profile(person_name):
    news = search_news(person_name, limit=50)
    prompt = f"""基于以下新闻，生成{person_name}的人物档案:
    1. 身份背景
    2. 近期言论/行动汇总
    3. 立场分析（政治/经济/技术观点）
    4. 影响力评估
    5. 与其他人物的关系网络
    6. 未来动向预测"""
```

### B6. 国家/地区档案

自动汇总某个国家/地区的所有相关新闻:

```python
def generate_country_briefing(country):
    news = search_news(country, limit=100)
    prompt = f"""基于以下新闻，生成{country}的国家简报:
    1. 政治动态
    2. 经济指标和趋势
    3. 外交关系（与哪些国家有互动）
    4. 科技发展
    5. 社会事件
    6. 国际形象变化
    7. 投资环境评估"""
```

### B7. 历史对比分析

将当前事件与历史事件对比:

```python
def historical_comparison(news):
    prompt = f"""将以下新闻与历史事件对比:
    新闻: {news['title']}

    找出历史上3-5个类似事件:
    1. 事件名称和时间
    2. 背景相似之处
    3. 当时的处理方式
    4. 最终结果
    5. 对当前事件的启示"""
```

---

## C. 数据分析与洞察

### C1. 新闻热度追踪

追踪特定话题的热度变化:

```python
@app.route('/api/analytics/trend')
def topic_trend():
    keyword = request.args.get('q')
    # 按天统计包含该关键词的新闻数量
    # 返回时间序列数据供前端绘图
```

### C2. 信息源交叉分析

分析同一事件在不同信息源中的呈现差异:

```python
def cross_source_analysis(event_keyword):
    # 搜索所有来源的报道
    # AI 对比分析
    prompt = f"""对比以下不同来源对"{event_keyword}"的报道:
    {grouped_by_source}

    分析:
    1. 各来源的报道角度差异
    2. 标题措辞对比（中性/正面/负面）
    3. 关注重点差异
    4. 信息完整性对比
    5. 哪个来源的报道最全面/最客观"""
```

### C3. 实体关系图谱数据

提取新闻中的实体关系，生成图谱数据:

```python
@app.route('/api/analytics/entity-graph')
def entity_graph():
    # 从最近N天的新闻中提取实体和关系
    # 返回 {nodes: [...], edges: [...]} 供前端 D3.js 绘图
```

### C4. 评分分布分析

```python
@app.route('/api/analytics/score-distribution')
def score_distribution():
    # 返回各分数段的新闻数量
    # 按 source_type 分组
    # 按天分组（趋势）
```

### C5. 来源可靠性评分

基于历史数据评估每个信息源的可靠性:

```python
def source_reliability():
    # 统计每个来源的平均评分、新闻量、被引用频率
    # AI 分析哪些来源的信息最有价值
```

### C6. 信息熵分析

衡量每天新闻的信息多样性:

```python
def information_entropy():
    # 计算每天新闻的方向分布
    # 高熵 = 话题分散，低熵 = 集中在某几个话题
    # 可视化信息多样性趋势
```

### C7. 媒体议程对比

对比不同媒体的"议程设置"（哪些话题被重点报道）:

```python
def media_agenda_comparison():
    # 按来源分组，统计各来源最常报道的方向
    # 可视化: 每个来源的报道方向分布雷达图
```

### C8. 情绪时序分析

追踪特定话题的情绪变化:

```python
def sentiment_timeline(topic):
    # 按天统计关于该话题的新闻情绪
    # 绘制情绪曲线
    # 标注关键转折点
```

---

## D. 自动化与监控

### D1. 关键词/话题告警

当特定关键词出现在高分新闻中时，推送通知:

```python
# 数据库
alerts (id, keyword, min_score, enabled, created_at)

# 调度器中检查
def check_alerts():
    alerts = get_active_alerts()
    recent = get_recent_news(minutes=5)
    for alert in alerts:
        matches = [n for n in recent if alert['keyword'] in n['title'] and n['ai_score'] >= alert['min_score']]
        if matches:
            notify(alert, matches)
```

### D2. 定时简报推送

每天定时生成并推送简报:

```python
SCHEDULES = [
    {'name': '早报', 'time': '08:00', 'type': 'morning'},
    {'name': '午间快报', 'time': '12:30', 'type': 'noon'},
    {'name': '晚报', 'time': '18:00', 'type': 'evening'},
    {'name': '周报', 'time': 'sunday 20:00', 'type': 'weekly'},
]
```

### D3. 异常检测

自动检测新闻流量/评分的异常模式:

```python
def detect_anomaly():
    # 检测:
    # 1. 突然出现大量同一话题的新闻（可能是突发事件）
    # 2. 某个来源突然大量发稿（可能是重大事件）
    # 3. 评分分布突然变化（可能是AI模型漂移）
    # 4. 某个方向的新闻突然激增
```

### D4. 后续追踪

对重要新闻标记"后续跟进"，自动追踪后续报道:

```python
# 数据库
followups (id, news_id, keyword, status, last_checked)

# 调度器
def check_followups():
    followups = get_active_followups()
    for f in followups:
        new = search_news(f['keyword'], days=1)
        if new:
            notify_followup(f, new)
```

### D5. 自动存档

对 S+ 级新闻自动保存完整原文（防链接失效）:

```python
def archive_important(news):
    if news['ai_score'] >= 95:
        # 抓取完整网页
        html = requests.get(news['link']).text
        # 保存到 data/archives/{news_id}.html
        # 或调用 Wayback Machine API 存档
```

### D6. 跨平台监控

同一话题在 X、Truth Social、Reddit、新闻中的讨论对比:

```python
def cross_platform_monitor(topic):
    # 搜索 X 上的讨论
    # 搜索 Truth Social 上的讨论
    # 搜索新闻报道
    # 搜索 Reddit 讨论
    # AI 对比各平台的讨论热度和情绪
```

---

## E. 可视化

### E1. 世界地图可视化

在地图上标注新闻事件发生地点:

```python
@app.route('/api/analytics/geo')
def news_geo():
    # AI 从新闻中提取地理位置
    # 返回 {lat, lng, title, score} 数组
    # 前端用 Leaflet.js 渲染
```

### E2. 新闻时间线

按时间轴展示事件发展:

```python
@app.route('/api/timeline/<topic>')
def topic_timeline(topic):
    # 搜索该话题的所有新闻
    # 按时间排序
    # 返回时间线数据
    # 前端用 Timeline.js 渲染
```

### E3. 热力图/词云

```python
@app.route('/api/analytics/wordcloud')
def wordcloud():
    # 从高分新闻中提取高频词
    # 返回 {word, count, sentiment} 数组
    # 前端用词云库渲染
```

### E4. 评分趋势图

```python
@app.route('/api/analytics/score-trend')
def score_trend():
    # 按天统计平均评分、最高评分、评分分布
    # 返回时间序列数据
```

### E5. 来源关系网络

可视化哪些来源经常报道相同事件:

```python
@app.route('/api/analytics/source-network')
def source_network():
    # 分析哪些来源的新闻标题相似度高
    # 返回 {sources, connections} 数据
    # 前端用 D3.js force-directed graph 渲染
```

### E6. 主题河流图 (ThemeRiver)

展示各方向新闻量随时间的变化:

```python
@app.route('/api/analytics/theme-river')
def theme_river():
    # 按天+方向分组统计新闻量
    # 返回时间序列矩阵
    # 前端用 ECharts themeRiver 渲染
```

---

## F. 外部集成与导出

### F1. Obsidian/Notion 导出

将新闻以 Markdown 格式导出到笔记工具:

```python
def export_to_obsidian(news):
    md = f"""---
title: {news['title']}
source: {news['source']}
score: {news['ai_score']}
date: {news['pub_time']}
tags: [{news['direction']}]
---

# {news['title']}

{news['ai_summary']}

## 原文
{news['content']}

## AI分析
{news['ai_analysis']}

## 链接
- [原文]({news['link']})
"""
    # 保存到 Obsidian vault 目录
    # 或通过 Notion API 创建页面
```

### F2. 生成 Podcast 脚本

AI 生成可朗读的新闻播客脚本:

```python
@app.route('/api/podcast')
def generate_podcast():
    top = get_news_list(sort='score', days=0, limit=10)
    prompt = f"""基于以下新闻，生成一段5分钟的播客脚本:
    格式:
    [开场白] 大家好，这里是NewsAgg每日新闻播客...
    [头条] 今天我们首先关注... (2分钟)
    [快讯] 接下来快速浏览几条重要新闻... (2分钟)
    [结语] 以上就是今天的新闻要点... (1分钟)

    语气: 专业但不枯燥，适当加入分析和见解
    新闻: {[n['title'] + ': ' + (n['ai_summary'] or '') for n in top]}"""
```

### F3. 生成每日新闻图片卡片

用 Canvas API 生成可分享的新闻卡片图片:

```python
@app.route('/api/news/<int:id>/card')
def news_card_image(news_id):
    # 生成包含标题、评分、摘要的图片
    # 返回 PNG
```

### F4. RSS 输出（已列出但补充细节）

```python
@app.route('/api/feed/rss')
@app.route('/api/feed/rss/<direction>')
@app.route('/api/feed/rss/min-score/<int:score>')
def rss_feed(direction=None, min_score=None):
    # 支持按方向、最低评分过滤
    # 支持 ATOM 格式
```

### F5. Webhook 输出

```python
WEBHOOK_EVENTS = {
    'breaking_news': 'S+级新闻出现',
    'alert_match': '关键词告警触发',
    'daily_digest': '每日简报生成完成',
    'anomaly': '异常检测触发',
}
```

### F6. 邮件摘要

```python
def send_email_digest():
    # 使用 SMTP 发送每日简报邮件
    # HTML 格式，包含 top 10 新闻
```

### F7. 浏览器扩展

开发简单的 Chrome 扩展:
- 显示今日新闻摘要
- 当前页面相关新闻推荐
- 一键收藏到 NewsAgg

---

## G. 个人效率工具

### G1. 阅读队列

```python
# 数据库
reading_queue (id, news_id, priority, added_at, read_at)

# API
POST /api/queue/add     — 加入阅读队列
GET  /api/queue          — 获取队列（按优先级排序）
POST /api/queue/:id/read — 标记已读
```

### G2. 阅读统计

```python
@app.route('/api/stats/reading')
def reading_stats():
    # 今日阅读量
    # 本周阅读量
    # 各方向阅读分布
    # 平均阅读时长
    # 阅读习惯分析
```

### G3. 笔记/标注

```python
# 数据库
notes (id, news_id, content, highlight, created_at)

# API
POST /api/news/:id/notes   — 添加笔记
GET  /api/notes             — 获取所有笔记
```

### G4. 标签系统

```python
# 数据库
tags (id, name, color)
news_tags (news_id, tag_id)

# 用户可以给新闻打自定义标签
# 如: "需要跟进"、"已分享"、"投资相关"、"技术参考"
```

### G5. 搜索历史

```python
# 保存搜索历史，方便重复搜索
search_history (id, query, result_count, searched_at)
```

### G6. 键盘快捷键

```
j/k       — 上/下一条
o/Enter   — 打开
s         — AI总结
b         — 收藏
q         — 加入阅读队列
/         — 搜索
1-6       — 切换来源筛选
d         — 日期筛选
Escape    — 关闭弹窗
?         — 显示快捷键帮助
```

### G7. 主题切换

```python
# 深色主题（当前默认）
# 浅色主题
# 跟随系统
# 自定义主题色
```

---

## H. 内容创作辅助

### H1. AI 生成社交媒体帖子

```python
def generate_social_post(news, platform):
    prompts = {
        'twitter': f"将以下新闻压缩为一条280字以内的推文，要有吸引力: {news['title']}",
        'weibo': f"将以下新闻写成一条微博，带话题标签: {news['title']}",
        'linkedin': f"将以下新闻写成LinkedIn专业分析帖: {news['title']}",
    }
```

### H2. AI 生成新闻通讯 (Newsletter)

```python
@app.route('/api/newsletter')
def generate_newsletter():
    top = get_news_list(sort='score', days=1, limit=15)
    prompt = f"""基于以下新闻，生成一份专业的新闻通讯:

    # [日期] 每日新闻通讯

    ## 今日头条
    (最重要的1-2条，详细分析)

    ## 快讯
    (5-8条，每条2-3句话)

    ## 值得关注
    (3-5条，虽然评分不高但可能有长期影响)

    ## 数据说话
    (列出新闻中的关键数字)

    风格: 专业、简洁、有洞察力"""
```

### H3. AI 生成研究报告框架

```python
def generate_research_outline(topic):
    prompt = f"""基于"{topic}"相关的新闻，生成一份研究报告大纲:
    1. 摘要
    2. 背景与现状
    3. 关键参与者分析
    4. 数据与趋势
    5. 风险与机遇
    6. 前瞻与建议
    7. 参考资料（引用具体新闻）

    每个章节列出要点和需要引用的新闻。"""
```

### H4. AI 生成演讲稿/汇报材料

```python
def generate_presentation(topic, duration='5min'):
    prompt = f"""基于"{topic}"的新闻，生成一份{duration}的演讲稿:
    - 开场引入（用一个引人注目的新闻事实）
    - 核心观点（3个）
    - 支撑数据（引用具体新闻和数字）
    - 结论和行动建议"""
```

---

## I. 金融/投资专用

### I1. 每日市场简报

```python
@app.route('/api/market/daily-brief')
def daily_market_brief():
    # 收集今日财经新闻
    # AI 生成市场简报
    prompt = f"""生成今日市场简报:
    1. 全球市场概览（美股/欧股/亚太/加密）
    2. 重大财经事件
    3. 央行动态
    4. 行业板块表现
    5. 明日关注事项
    6. 投资者情绪指标"""
```

### I2. 个股/币种影响分析

```python
@app.route('/api/impact/<ticker>')
def ticker_impact(ticker):
    # 搜索所有提到该股票/币种的新闻
    # AI 分析综合影响
    prompt = f"""分析近期新闻对 {ticker} 的影响:
    1. 利好因素
    2. 利空因素
    3. 综合判断: 看多/看空/中性
    4. 关键催化剂
    5. 风险提示"""
```

### I3. 板块轮动分析

```python
def sector_rotation():
    # 分析近期各板块新闻量和情绪变化
    # AI 判断资金可能流向
```

### I4. 黑天鹅监控

```python
def black_swan_monitor():
    # 监控异常模式:
    # 1. 大量负面新闻集中在某个领域
    # 2. 多个不相关来源同时报道类似风险
    # 3. 突发的地缘政治事件
    # 4. 央行/监管的意外行动
```

### I5. 期权异动关联

```python
def options_flow_analysis():
    # 结合 unusual_whales 的期权异动数据
    # 与新闻事件关联分析
    prompt = f"""结合以下期权异动和新闻，分析可能的关联:
    期权异动: {options_data}
    相关新闻: {related_news}

    分析: 是否有人提前知道消息? 智慧钱在做什么?"""
```

### I6. 宏观经济仪表盘

```python
@app.route('/api/macro/dashboard')
def macro_dashboard():
    # 汇总宏观经济指标相关的新闻
    # CPI、GDP、就业、利率、汇率等
    # AI 生成宏观环境评估
```

---

## J. 学习与知识管理

### J1. 每日学习卡片

```python
@app.route('/api/flashcards')
def daily_flashcards():
    top = get_news_list(sort='score', days=1, limit=10)
    prompt = f"""基于以下新闻，生成10张学习卡片:
    格式:
    Q: [问题]
    A: [答案]

    内容:
    - 关键概念解释
    - 人物/公司背景
    - 历史背景
    - 专业术语"""
```

### J2. 新闻知识图谱

```python
@app.route('/api/knowledge/graph')
def knowledge_graph():
    # 从所有新闻中提取知识
    # 构建概念之间的关系
    # 供前端以交互式图谱展示
```

### J3. 每日测验

```python
@app.route('/api/quiz')
def daily_quiz():
    """基于今日新闻生成测验"""
    prompt = f"""基于以下新闻，生成5道选择题:
    每题4个选项，标注正确答案和解释。
    覆盖不同难度（简单/中等/困难）。"""
```

### J4. 术语词典自动扩展

```python
# 遇到新的专业术语时自动添加到词典
glossary (id, term, definition, first_seen_news_id, category)
```

### J5. 阅读理解训练

```python
def reading_comprehension(news):
    """AI 基于新闻内容生成阅读理解题"""
    # 适合英文新闻的阅读理解练习
```

---

## K. 高级采集

### K1. 网页全文抓取

对高分新闻自动抓取完整原文:

```python
def fetch_full_article(url):
    # 用 readability 或 trafilatura 提取正文
    # 去除广告、导航栏等噪音
    # 保存到数据库
```

### K2. Wayback Machine 集成

```python
def check_archive(url):
    """检查该URL是否已被存档"""
    r = requests.get(f'https://archive.org/wayback/available?url={url}')
    return r.json()
```

### K3. Google News 采集

```python
# 通过 RSSHub
{'name': 'Google News 中文', 'url': '/google/news/zh-CN', 'type': 'media'},
{'name': 'Google News 英文', 'url': '/google/news/en-US', 'type': 'media'},
{'name': 'Google News 科技', 'url': '/google/news/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB', 'type': 'tech'},
```

### K4. Reddit 采集

```python
# Reddit 子版块
{'name': 'r/worldnews', 'url': 'https://www.reddit.com/r/worldnews/.rss', 'type': 'media'},
{'name': 'r/technology', 'url': 'https://www.reddit.com/r/technology/.rss', 'type': 'tech'},
{'name': 'r/wallstreetbets', 'url': 'https://www.reddit.com/r/wallstreetbets/.rss', 'type': 'finance'},
{'name': 'r/cryptocurrency', 'url': 'https://www.reddit.com/r/cryptocurrency/.rss', 'type': 'crypto'},
{'name': 'r/artificial', 'url': 'https://www.reddit.com/r/artificial/.rss', 'type': 'tech'},
```

### K5. YouTube 频道 RSS

```python
# 通过 RSSHub
{'name': 'MKBHD', 'url': '/youtube/channel/UCBJycsmduvYEL83R_U4JriQ', 'type': 'tech'},
{'name': 'Linus Tech Tips', 'url': '/youtube/channel/UCXuqSBlHAE6Xw-yeJA0Tunw', 'type': 'tech'},
{'name': 'Bloomberg TV', 'url': '/youtube/channel/UCIALMKvObZNtJ68-rmLfsXA', 'type': 'finance'},
```

### K6. Newsletter 订阅采集

```python
# 采集知名 Newsletter 的内容
# 如: The Hustle, Morning Brew, Stratechery
# 通过 RSSHub 或邮件解析
```

### K7. SEC/EDGAR 文件监控

```python
# 监控上市公司的重要 SEC 文件
# 10-K, 10-Q, 8-K, S-1 等
# 通过 RSSHub 或 EDGAR API
```

### K8. 专利数据库监控

```python
# 监控特定公司/领域的专利申请
# USPTO, EPO, CNIPA
# 可通过 RSSHub 或直接 API
```

---

## L. 实验性功能

### L1. AI 新闻写作

AI 基于多个信息源合成一篇新文章:

```python
def ai_write_article(topic):
    sources = search_news(topic, limit=10)
    prompt = f"""基于以下多篇报道，撰写一篇综合分析文章:
    要求:
    - 综合多方信息，不偏不倚
    - 补充背景知识
    - 加入独立分析和见解
    - 1000-2000字

    参考来源:
    {[s['title'] + ' (' + s['source'] + ')' for s in sources]}"""
```

### L2. AI 新闻预测

```python
def predict_tomorrow_news():
    """基于当前趋势预测明天可能发生的事"""
    recent = get_news_list(sort='score', days=3, limit=50)
    prompt = f"""基于近3天的新闻趋势，预测明天可能发生的事情:
    1. 高概率事件（>70%）
    2. 中概率事件（30-70%）
    3. 低概率但需关注的事件（<30%）
    基于: {[n['title'] for n in recent]}"""
```

### L3. 反事实分析

```python
def counterfactual_analysis(news):
    """如果这件事没有发生，会怎样?"""
    prompt = f"""进行反事实分析:
    事件: {news['title']}
    如果这件事没有发生:
    1. 市场会怎样?
    2. 相关公司/人物会怎样?
    3. 历史走向会有什么不同?"""
```

### L4. AI 观点进化追踪

```python
def track_opinion_evolution(person, topic):
    """追踪某人对某话题观点的变化"""
    # 搜索该人关于该话题的所有历史发言
    # AI 分析观点是否/如何变化
```

### L5. 信息级联分析

```python
def information_cascade():
    """分析信息是如何从一个来源传播到另一个的"""
    # 追踪同一新闻在不同来源出现的时间顺序
    # 识别信息源头和传播路径
```

### L6. 假新闻检测器

```python
def fake_news_detector(news):
    prompt = f"""评估以下新闻的可信度:
    1. 消息源是否可靠?
    2. 是否有其他来源佐证?
    3. 数据是否合理?
    4. 语言是否有煽动性?
    5. 是否符合已知事实?
    可信度评分: 1-10"""
```

### L7. 新闻成瘾监控

```python
def news_consumption_report():
    """生成用户的新闻消费报告"""
    # 今日阅读量
    # 消耗的 AI token 量
    # 最常阅读的方向
    # 是否过度关注负面新闻
    # 建议: 是否需要减少新闻消费
```

---

## 功能优先级总览

按实现难度和价值排序:

### 立即可做（1-2小时/个）

| 功能 | 价值 | 难度 |
|------|------|------|
| A1 多视角分析 | 高 | 低 |
| A4 影响预测 | 高 | 低 |
| A7 全文翻译 | 中 | 低 |
| A10 风险评估 | 高 | 低 |
| G1 阅读队列 | 中 | 低 |
| G3 笔记/标注 | 中 | 低 |
| H2 生成Newsletter | 中 | 低 |
| I1 每日市场简报 | 高 | 低 |
| J1 学习卡片 | 中 | 低 |
| K3 Google News | 中 | 低 |
| K4 Reddit | 中 | 低 |

### 需要一定开发（2-4小时/个）

| 功能 | 价值 | 难度 |
|------|------|------|
| A2 事实核查 | 高 | 中 |
| A5 事件关联 | 高 | 中 |
| B1 话题深度研究 | 高 | 中 |
| C1 热度追踪 | 中 | 中 |
| D1 关键词告警 | 高 | 中 |
| D5 自动存档 | 中 | 中 |
| E1 世界地图 | 中 | 中 |
| E2 时间线 | 中 | 中 |
| F1 Obsidian导出 | 中 | 中 |
| I2 个股影响分析 | 高 | 中 |
| K1 全文抓取 | 中 | 中 |

### 大工程（4小时+）

| 功能 | 价值 | 难度 |
|------|------|------|
| A9 辩论模拟 | 高 | 中 |
| B2 专家观点汇总 | 高 | 中 |
| C3 实体关系图谱 | 中 | 高 |
| D3 异常检测 | 中 | 高 |
| E6 主题河流图 | 中 | 高 |
| F7 浏览器扩展 | 中 | 高 |
| J2 知识图谱 | 中 | 高 |
| L1 AI新闻写作 | 高 | 中 |
