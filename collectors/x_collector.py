import feedparser
import logging
from datetime import datetime, timedelta, timezone
from database.db import insert_news
from utils.text import safe_truncate
from collectors.utils import parse_feed_time, clean_html

logger = logging.getLogger(__name__)

# X关键人物监控清单 — 通过RSSHub /twitter/user/{screen_name} 获取
X_ACCOUNTS = [
    # 科技大佬
    {'name': '马斯克', 'screen_name': 'elonmusk', 'priority': 'S'},
    {'name': '奥特曼', 'screen_name': 'sama', 'priority': 'S'},
    {'name': '扎克伯格', 'screen_name': 'zuck', 'priority': 'S'},
    {'name': '贝佐斯', 'screen_name': 'JeffBezos', 'priority': 'A'},
    {'name': '比尔盖茨', 'screen_name': 'BillGates', 'priority': 'A'},
    {'name': '蒂姆库克', 'screen_name': 'tim_cook', 'priority': 'A'},
    {'name': '黄仁勋', 'screen_name': 'nvidia', 'priority': 'A'},
    {'name': '微软官方', 'screen_name': 'Microsoft', 'priority': 'A'},
    {'name': '谷歌CEO', 'screen_name': 'sundarpichai', 'priority': 'A'},

    # 政治人物
    {'name': '特朗普', 'screen_name': 'realDonaldTrump', 'priority': 'S'},
    {'name': '拜登', 'screen_name': 'POTUS', 'priority': 'A'},
    {'name': '莫迪', 'screen_name': 'narendramodi', 'priority': 'A'},
    {'name': '泽连斯基', 'screen_name': 'ZelenskyyUa', 'priority': 'A'},
    {'name': '欧盟主席', 'screen_name': 'vonderleyen', 'priority': 'B'},

    # 权威媒体
    {'name': 'BBC Breaking', 'screen_name': 'BBCBreaking', 'priority': 'S'},
    {'name': 'BBC World', 'screen_name': 'BBCWorld', 'priority': 'A'},
    {'name': 'CNN Breaking', 'screen_name': 'cnnbrk', 'priority': 'S'},
    {'name': 'CNN', 'screen_name': 'CNN', 'priority': 'A'},
    {'name': 'Reuters', 'screen_name': 'Reuters', 'priority': 'S'},
    {'name': 'AP通讯社', 'screen_name': 'AP', 'priority': 'S'},
    {'name': 'NY Times', 'screen_name': 'nytimes', 'priority': 'A'},
    {'name': 'Washington Post', 'screen_name': 'washingtonpost', 'priority': 'A'},
    {'name': 'Bloomberg', 'screen_name': 'Bloomberg', 'priority': 'S'},
    {'name': 'WSJ', 'screen_name': 'WSJ', 'priority': 'A'},
    {'name': 'FT金融时报', 'screen_name': 'FT', 'priority': 'A'},
    {'name': 'The Economist', 'screen_name': 'TheEconomist', 'priority': 'A'},
    {'name': 'CNBC', 'screen_name': 'CNBC', 'priority': 'A'},
    {'name': 'CNBC突发', 'screen_name': 'CNBCnow', 'priority': 'S'},
    {'name': 'Breaking News', 'screen_name': 'BreakingNews', 'priority': 'S'},
    {'name': 'Al Jazeera', 'screen_name': 'AJEnglish', 'priority': 'A'},

    # 财经博主/分析师
    {'name': 'Jim Cramer', 'screen_name': 'jimcramer', 'priority': 'A'},
    {'name': 'Peter Schiff', 'screen_name': 'PeterSchiff', 'priority': 'A'},
    {'name': 'Cathie Wood', 'screen_name': 'CathieDWood', 'priority': 'A'},
    {'name': 'Michael Saylor', 'screen_name': 'saylor', 'priority': 'A'},
    {'name': 'Vitalik Buterin', 'screen_name': 'VitalikButerin', 'priority': 'A'},
    {'name': 'CZ赵长鹏', 'screen_name': 'binance', 'priority': 'A'},
    {'name': 'Brian Armstrong', 'screen_name': 'brian_armstrong', 'priority': 'B'},
    {'name': 'Ray Dalio', 'screen_name': 'RayDalio', 'priority': 'A'},
    {'name': 'Nouriel Roubini', 'screen_name': 'Nouriel', 'priority': 'B'},

    # 科技媒体
    {'name': 'TechCrunch', 'screen_name': 'TechCrunch', 'priority': 'A'},
    {'name': 'The Verge', 'screen_name': 'verge', 'priority': 'A'},
    {'name': 'Wired', 'screen_name': 'WIRED', 'priority': 'B'},
    {'name': 'Ars Technica', 'screen_name': 'arstechnica', 'priority': 'B'},

    # AI领域
    {'name': 'OpenAI', 'screen_name': 'OpenAI', 'priority': 'A'},
    {'name': 'Google DeepMind', 'screen_name': 'GoogleDeepMind', 'priority': 'A'},
    {'name': 'Anthropic', 'screen_name': 'AnthropicAI', 'priority': 'A'},
    {'name': 'Hugging Face', 'screen_name': 'huggingface', 'priority': 'B'},
    {'name': 'Yann LeCun', 'screen_name': 'ylecun', 'priority': 'A'},
    {'name': 'Andrew Ng', 'screen_name': 'AndrewYNg', 'priority': 'A'},

    # 加密货币
    {'name': 'Bitcoin Magazine', 'screen_name': 'BitcoinMagazine', 'priority': 'A'},
    {'name': 'CoinDesk', 'screen_name': 'CoinDesk', 'priority': 'A'},
    {'name': 'Coinbase', 'screen_name': 'coinbase', 'priority': 'B'},

    # 对冲基金大佬
    {'name': 'Bill Ackman', 'screen_name': 'BillAckman', 'priority': 'S'},
    {'name': 'Mark Cuban', 'screen_name': 'mcuban', 'priority': 'A'},
    {'name': 'Michael Burry', 'screen_name': 'michaeljburry', 'priority': 'S'},

    # 宏观经济学家
    {'name': 'Mohamed El-Erian', 'screen_name': 'elerianm', 'priority': 'S'},
    {'name': 'Larry Summers', 'screen_name': 'LHSummers', 'priority': 'A'},
    {'name': 'Nassim Taleb', 'screen_name': 'nntaleb', 'priority': 'A'},

    # 华尔街顶流
    {'name': 'Zerohedge', 'screen_name': 'ZeroHedge', 'priority': 'S'},
    {'name': 'unusual_whales', 'screen_name': 'unusual_whales', 'priority': 'A'},

    # 美联储/央行
    {'name': '美联储官方', 'screen_name': 'federalreserve', 'priority': 'S'},
    {'name': '纽约联储', 'screen_name': 'newyorkfed', 'priority': 'A'},
    {'name': '欧央行', 'screen_name': 'ecb', 'priority': 'A'},
    {'name': '英格兰银行', 'screen_name': 'bankofengland', 'priority': 'A'},

    # 外交/国际
    {'name': '美国国务院', 'screen_name': 'StateDept', 'priority': 'S'},
    {'name': '联合国', 'screen_name': 'UN', 'priority': 'A'},
    {'name': 'NATO', 'screen_name': 'NATO', 'priority': 'A'},

    # 地缘/军事
    {'name': 'ISW战争研究所', 'screen_name': 'TheStudyofWar', 'priority': 'A'},
    {'name': '五角大楼', 'screen_name': 'DeptofDefense', 'priority': 'A'},

    # 法律/监管
    {'name': 'SEC', 'screen_name': 'SECGov', 'priority': 'A'},
    {'name': 'CFTC', 'screen_name': 'CFTC', 'priority': 'A'},
    {'name': 'DOJ司法部', 'screen_name': 'TheJusticeDept', 'priority': 'A'},
    {'name': 'FTC', 'screen_name': 'FTC', 'priority': 'A'},

    # AI领域补充
    {'name': 'Lisa Su AMD', 'screen_name': 'LisaSu', 'priority': 'A'},
    {'name': 'Dario Amodei', 'screen_name': 'DarioAmodei', 'priority': 'A'},
    {'name': 'Perplexity', 'screen_name': 'perplexity_ai', 'priority': 'A'},
]

# RSSHub实例列表（按优先级排序）
from collectors.rsshub_collector import get_working_rsshub


def _parse_twitter_time(entry):
    """解析RSSHub返回的Twitter时间"""
    pub_time = parse_feed_time(entry)
    if pub_time:
        return pub_time
    # 尝试从published_parsed解析
    pp = entry.get('published_parsed')
    if pp:
        try:
            dt = datetime(*pp[:6], tzinfo=timezone.utc)
            return dt.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
    return None


def fetch_x_tweets():
    """通过RSSHub获取X/Twitter关键人物的最新推文"""
    base = get_working_rsshub()
    if not base:
        logger.warning("无可用RSSHub实例，X采集跳过")
        return 0

    new_count = 0
    success_count = 0
    fail_count = 0

    for account in X_ACCOUNTS:
        try:
            url = f'{base}/twitter/user/{account["screen_name"]}'
            feed = feedparser.parse(url)

            if feed.bozo and not feed.entries:
                fail_count += 1
                logger.debug(f"X采集无数据 @{account['screen_name']}")
                continue

            success_count += 1
            for entry in feed.entries[:5]:
                title = entry.get('title', '').strip()
                if not title:
                    continue

                link = entry.get('link', '')
                if not link:
                    link = f"https://x.com/{account['screen_name']}"

                content = entry.get('summary', entry.get('description', ''))
                if content:
                    if '<' in content and '>' in content:
                        content = safe_truncate(clean_html(content))
                    else:
                        content = safe_truncate(content)

                pub_time = _parse_twitter_time(entry)

                _, is_new = insert_news(
                    title=title,
                    content=content,
                    link=link,
                    source=f"@{account['screen_name']} ({account['name']})",
                    source_type='x',
                    author=account['name'],
                    pub_time=pub_time
                )
                if is_new:
                    new_count += 1

        except Exception as e:
            fail_count += 1
            logger.error(f"X采集失败 @{account['screen_name']}: {e}")

    logger.info(f"X采集完成: 成功{success_count}源, 失败{fail_count}源, 新增{new_count}条")
    return new_count
