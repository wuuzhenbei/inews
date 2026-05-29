# iNews - 实时新闻聚合 & AI 智能评级

一个实时新闻聚合平台，自动从全球多个来源采集新闻，通过 AI 进行智能评分和分类，帮助用户快速获取高价值信息。

## 功能特性

- **多源新闻采集** - RSS、X/Twitter、热搜榜、RSSHub，覆盖国内外主流媒体
- **AI 智能评分** - 10 维度评分体系（影响力、权威性、时效性、热度等），支持 API + 规则双引擎
- **AI 新闻摘要** - 一键生成新闻摘要，支持批量处理
- **RAG 智能问答** - 基于新闻库的 AI 对话，支持深度追问和多视角分析
- **市场简报** - AI 生成每日市场简报
- **实时更新** - SSE 推送 + 轮询，新新闻实时通知
- **情报作战室 UI** - 星空蓝主题、毛玻璃卡片、环形评分、鼠标跟随光晕

## 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量（可选，不配置则使用规则评分）
export AI_API_KEY="your-api-key"
export AI_BASE_URL="https://api.siliconflow.cn/v1"
export AI_MODEL="MiMo-V2.5"

# 3. 启动
python app.py

# 4. 访问
# http://localhost:5000
```

或使用启动脚本：
```bash
# Windows
start.bat

# Linux/Mac
bash start.sh
```

## 配置项

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AI_API_KEY` | AI 模型 API Key | - |
| `AI_BASE_URL` | API 地址 | `https://api.siliconflow.cn/v1` |
| `AI_MODEL` | 模型名称 | `MiMo-V2.5` |
| `RSSHUB_BASE` | RSSHub 实例地址 | `http://localhost:1200` |
| `FETCH_INTERVAL_RSS` | RSS 采集间隔(秒) | `300` |
| `FETCH_INTERVAL_X` | X/Twitter 采集间隔(秒) | `600` |
| `FETCH_INTERVAL_HOTLIST` | 热搜采集间隔(秒) | `180` |

## 采集源

### RSS 源 (40+)
- **国内**: 新华网、央视新闻、人民日报、百度新闻、凤凰网、澎湃新闻
- **国际**: BBC、CNN、Reuters、NYT、Al Jazeera、The Guardian、France24
- **科技**: 36氪、TechCrunch、The Verge、Hacker News、Ars Technica
- **财经**: Bloomberg、CNBC、CoinDesk
- **学术/外交**: Nature、Science、NATO、UN

### X/Twitter 关键人物
- 科技: 马斯克、扎克伯格、Sam Altman、黄仁勋、Satya Nadella
- 政治: 特朗普、莫迪
- AI: OpenAI、Google DeepMind、Anthropic

### 热搜热榜
- 微博热搜、知乎热榜、头条热榜、B站热搜

## 项目结构

```
findnews/
├── app.py                    # Flask 主应用 + REST API
├── config.py                 # 配置管理
├── requirements.txt          # Python 依赖
├── collectors/               # 新闻采集器
│   ├── rss_collector.py      # RSS 源采集
│   ├── x_collector.py        # X/Twitter 采集 (via RSSHub)
│   ├── rsshub_collector.py   # RSSHub 通用采集
│   ├── hotlist_collector.py  # 热搜热榜采集
│   ├── scheduler.py          # 采集调度器
│   └── utils.py              # 时间解析、HTML清洗
├── processors/               # 数据处理器
│   ├── scorer.py             # AI 评分引擎 (规则+API双引擎)
│   └── summarizer.py         # AI 摘要生成器
├── database/                 # 数据库
│   ├── db.py                 # SQLite 操作 (WAL模式)
│   └── schema.sql            # 表结构
├── utils/                    # 工具模块
│   ├── ai_client.py          # OpenAI-compatible 客户端
│   └── text.py               # 文本工具
└── static/                   # 前端 (Vue 3 SPA)
    ├── index.html            # 主页面
    ├── css/style.css         # 样式 (毛玻璃+星空主题)
    ├── js/app.js             # Vue 3 应用逻辑
    └── js/*.js               # Vue/Tailwind/DOMPurify
```

## 评分体系

10 维度 AI 评分，总分 0-100：

| 维度 | 权重 | 说明 |
|------|------|------|
| 影响力 | 35% | 新闻事件的影响范围和深度 |
| 热度 | 15% | 当前关注度和传播度 |
| 权威性 | 12% | 来源可信度 |
| 兴趣匹配 | 12% | 与用户关注方向的匹配度 |
| 时效性 | 8% | 新闻新鲜度 |
| 突发性 | 8% | 是否突发事件 |
| 可信度 | 5% | 信息可信程度 |
| 新颖度 | 5% | 话题新颖程度 |

评分等级：S+ (90+) > S (80-89) > A (70-79) > B (50-69) > C (30-49) > D (15-29) > E (0-14)

## 技术栈

- **后端**: Python 3.10+ / Flask / SQLite (WAL)
- **前端**: Vue 3 / Tailwind CSS / DOMPurify
- **AI**: OpenAI-compatible API (小米 MiMo 推理模型)
- **采集**: feedparser / requests / BeautifulSoup
- **UI**: 毛玻璃效果 / 星空背景 / SVG 环形评分 / 鼠标跟随光晕

## 许可证

MIT
