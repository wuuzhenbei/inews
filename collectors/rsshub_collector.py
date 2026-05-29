import feedparser
import requests
from datetime import datetime
import logging
from database.db import insert_news
from config import RSSHUB_BASE
from utils.text import safe_truncate
from collectors.utils import parse_feed_time, clean_html

logger = logging.getLogger(__name__)

# 本地RSSHub实例的路由
RSSHUB_ROUTES = [
    # X/Twitter关键人物（通过RSSHub桥接）
    {'name': '马斯克', 'url': '/twitter/user/elonmusk', 'type': 'x', 'priority': 'S'},
    {'name': '特朗普', 'url': '/twitter/user/realDonaldTrump', 'type': 'x', 'priority': 'S'},
    {'name': '扎克伯格', 'url': '/twitter/user/zuck', 'type': 'x', 'priority': 'S'},
    {'name': '奥特曼', 'url': '/twitter/user/sama', 'type': 'x', 'priority': 'S'},
    {'name': '贝佐斯', 'url': '/twitter/user/JeffBezos', 'type': 'x', 'priority': 'A'},
    {'name': '比尔盖茨', 'url': '/twitter/user/BillGates', 'type': 'x', 'priority': 'A'},
    {'name': '蒂姆库克', 'url': '/twitter/user/tim_cook', 'type': 'x', 'priority': 'A'},
    {'name': 'CNBC突发', 'url': '/twitter/user/CNBCnow', 'type': 'x', 'priority': 'S'},
    {'name': 'Breaking News', 'url': '/twitter/user/BreakingNews', 'type': 'x', 'priority': 'S'},

    # 热搜/热榜
    {'name': '微博热搜', 'url': '/weibo/search/hot', 'type': 'hotlist'},
    {'name': '知乎热榜', 'url': '/zhihu/hotlist', 'type': 'hotlist'},
    {'name': 'B站热搜', 'url': '/bilibili/hot-search', 'type': 'hotlist'},
    {'name': '抖音热搜', 'url': '/douyin/trending', 'type': 'hotlist'},
    {'name': '百度热搜', 'url': '/baidu/top', 'type': 'hotlist'},

    # 科技/开发者
    {'name': 'Hacker News', 'url': '/hackernews', 'type': 'tech'},
    {'name': 'GitHub Trending', 'url': '/github/trending/daily/any', 'type': 'tech'},
    {'name': 'Product Hunt', 'url': '/producthunt/today', 'type': 'tech'},

    # 央视（通过RSSHub获取）
    {'name': '央视新闻', 'url': '/cctv', 'type': 'media'},

    # 央行/监管
    {'name': '美联储新闻', 'url': '/federalreserve/press', 'type': 'fed'},
    {'name': '美联储演讲', 'url': '/federalreserve/speeches', 'type': 'fed'},

    # 外交
    {'name': '中国外交部', 'url': '/fmprc/fyrbt', 'type': 'diplomatic'},
    {'name': '美国国务院', 'url': '/state/briefing', 'type': 'diplomatic'},

    # 财经
    {'name': '华尔街见闻·全球', 'url': '/wallstreetcn/news/global', 'type': 'finance'},
    {'name': '华尔街见闻·快讯', 'url': '/wallstreetcn/live/global', 'type': 'finance'},
    {'name': '财新网', 'url': '/caixin/latest', 'type': 'finance'},
    {'name': '第一财经', 'url': '/yicai/brief', 'type': 'finance'},

    # 地缘
    {'name': 'RAND智库', 'url': '/rand/blog', 'type': 'geopolitical'},
]

# 公共RSSHub实例（本地不可用时的备用）
PUBLIC_RSSHUB_INSTANCES = [
    'https://rsshub.app',
    'https://rsshub.rssforever.com',
    'https://rsshub.feedly.com',
]

def check_rsshub_available(base_url, timeout=5):
    """检查RSSHub实例是否可用"""
    try:
        r = requests.get(f'{base_url}/healthz', timeout=timeout)
        return r.status_code == 200
    except (requests.RequestException, ConnectionError, TimeoutError):
        return False

def get_working_rsshub():
    """获取可用的RSSHub实例地址"""
    if check_rsshub_available(RSSHUB_BASE):
        return RSSHUB_BASE
    for instance in PUBLIC_RSSHUB_INSTANCES:
        if check_rsshub_available(instance):
            logger.info(f"本地RSSHub不可用，使用公共实例: {instance}")
            return instance
    logger.warning("所有RSSHub实例均不可用")
    return None

def fetch_rsshub_feeds():
    """通过RSSHub获取内容"""
    base = get_working_rsshub()
    if not base:
        return 0

    new_count = 0
    for route in RSSHUB_ROUTES:
        try:
            url = f'{base}{route["url"]}'
            feed = feedparser.parse(url)

            if feed.bozo and not feed.entries:
                logger.debug(f"RSSHub路由无数据: {route['name']}")
                continue

            for entry in feed.entries[:15]:
                title = entry.get('title', '').strip()
                if not title:
                    continue
                link = entry.get('link', '')
                if not link:
                    link = url  # 某些热搜没有独立链接

                content = entry.get('summary', entry.get('description', ''))
                if content:
                    content = safe_truncate(clean_html(content))

                pub_time = parse_feed_time(entry)

                _, is_new = insert_news(
                    title=title, content=content, link=link,
                    source=route['name'], source_type=route['type'],
                    author=route['name'], pub_time=pub_time
                )
                if is_new:
                    new_count += 1

        except Exception as e:
            logger.error(f"RSSHub采集失败 {route['name']}: {e}")

    logger.info(f"RSSHub采集完成，新增 {new_count} 条")
    return new_count
