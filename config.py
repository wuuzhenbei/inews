import os
from dotenv import load_dotenv

load_dotenv()

# 数据库
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'news.db')

# AI API
AI_API_KEY = os.getenv('AI_API_KEY', '')
AI_BASE_URL = os.getenv('AI_BASE_URL', 'https://api.siliconflow.cn/v1')
AI_MODEL = os.getenv('AI_MODEL', 'Qwen/Qwen2.5-7B-Instruct')
AI_CHAT_MODEL = os.getenv('AI_CHAT_MODEL', '')  # 聊天专用模型，留空则用AI_MODEL

# 模型预设配置（仅用于前端展示，实际配置仍从环境变量读取）
MODEL_PRESETS = {
    'deepseek-chat': {
        'name': 'DeepSeek V3',
        'provider': 'DeepSeek',
        'base_url': 'https://api.deepseek.com/v1',
    },
    'deepseek-reasoner': {
        'name': 'DeepSeek R1',
        'provider': 'DeepSeek',
        'base_url': 'https://api.deepseek.com/v1',
    },
    'Qwen/Qwen2.5-72B-Instruct': {
        'name': 'Qwen2.5 72B',
        'provider': '通义千问',
        'base_url': 'https://api.siliconflow.cn/v1',
    },
    'mimo-v2.5': {
        'name': 'MiMo V2.5',
        'provider': '小米',
        'base_url': 'https://token-plan-cn.xiaomimimo.com/v1',
    },
    'moonshot-v1-8k': {
        'name': 'Moonshot V1',
        'provider': '月之暗面',
        'base_url': 'https://api.moonshot.cn/v1',
    },
    'glm-4-flash': {
        'name': 'GLM-4 Flash',
        'provider': '智谱',
        'base_url': 'https://open.bigmodel.cn/api/paas/v4',
    },
}

# X/Twitter
X_BEARER_TOKEN = os.getenv('X_BEARER_TOKEN', '')

# API访问密钥
API_ACCESS_KEY = os.getenv('API_ACCESS_KEY', '')

# RSSHub
RSSHUB_BASE = os.getenv('RSSHUB_BASE', 'http://localhost:1200')

# 采集频率（秒）
FETCH_INTERVAL_X = 120          # X关键人物: 2分钟
FETCH_INTERVAL_MEDIA = 600      # 权威媒体: 10分钟
FETCH_INTERVAL_HOTLIST = 180    # 热搜热榜: 3分钟
FETCH_INTERVAL_GENERAL = 1800   # 常规源: 30分钟

# 评分阈值
SCORE_THRESHOLD_TOP = 85        # AI精选阈值
DEDUP_SIMILARITY = 0.85         # 去重相似度阈值

# 前端
WEB_HOST = '0.0.0.0'
WEB_PORT = 5000

# 用户默认兴趣权重
DEFAULT_INTEREST_WEIGHTS = {
    '政治': 10,
    '经济': 15,
    '科技': 20,
    '军事': 5,
    '社会': 5,
    '文化': 5,
    '突发': 10,
    '财经': 15,
}

# 评分等级映射
SCORE_LEVELS = [
    (95, 'S+', '#dc2626', '历史级别重大事件'),
    (85, 'S',  '#f97316', '影响全球格局的重大事件'),
    (70, 'A',  '#eab308', '影响多国/多行业的重大新闻'),
    (50, 'B',  '#22c55e', '影响本国/本行业的重要新闻'),
    (30, 'C',  '#3b82f6', '区域性/垂直领域关注新闻'),
    (15, 'D',  '#6b7280', '一般性新闻'),
    (0,  'E',  '#374151', '低重要性信息'),
]
