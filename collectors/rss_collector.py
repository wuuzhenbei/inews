import feedparser
import warnings
import socket
from datetime import datetime
import time
import logging
from database.db import insert_news
from utils.text import safe_truncate
from collectors.utils import parse_feed_time, clean_html

warnings.filterwarnings('ignore', message='.*MarkupResemblesLocatorWarning.*')
logger = logging.getLogger(__name__)

# 设置全局socket超时，防止feedparser卡死
socket.setdefaulttimeout(15)

# 免费RSS源列表
RSS_SOURCES = [
    # 国内权威媒体
    {'name': '百度新闻·国内', 'url': 'https://news.baidu.com/n?cmd=1&class=civilnews&tn=rss', 'type': 'media'},
    {'name': '百度新闻·国际', 'url': 'https://news.baidu.com/n?cmd=1&class=internews&tn=rss', 'type': 'media'},
    {'name': '百度新闻·财经', 'url': 'https://news.baidu.com/n?cmd=1&class=finannews&tn=rss', 'type': 'media'},
    {'name': '百度新闻·科技', 'url': 'https://news.baidu.com/n?cmd=1&class=technnews&tn=rss', 'type': 'media'},

    # 国际权威媒体
    {'name': 'BBC News', 'url': 'https://feeds.bbci.co.uk/news/rss.xml', 'type': 'media'},
    {'name': 'BBC World', 'url': 'https://feeds.bbci.co.uk/news/world/rss.xml', 'type': 'media'},
    {'name': 'NYT Homepage', 'url': 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml', 'type': 'media'},
    {'name': 'Al Jazeera', 'url': 'https://www.aljazeera.com/xml/rss/all.xml', 'type': 'media'},
    {'name': 'The Guardian', 'url': 'https://www.theguardian.com/world/rss', 'type': 'media'},
    {'name': 'France24', 'url': 'https://www.france24.com/en/rss', 'type': 'media'},

    # 科技媒体
    {'name': '36氪', 'url': 'https://www.36kr.com/feed', 'type': 'tech'},
    {'name': '少数派', 'url': 'https://sspai.com/feed', 'type': 'tech'},
    {'name': 'TechCrunch', 'url': 'https://techcrunch.com/feed/', 'type': 'tech'},
    {'name': 'The Verge', 'url': 'https://www.theverge.com/rss/index.xml', 'type': 'tech'},
    {'name': 'Ars Technica', 'url': 'https://feeds.arstechnica.com/arstechnica/index', 'type': 'tech'},
    {'name': 'Wired', 'url': 'https://www.wired.com/feed/rss', 'type': 'tech'},
    {'name': 'Hacker News Best', 'url': 'https://hnrss.org/best', 'type': 'tech'},
    {'name': 'Engadget', 'url': 'https://www.engadget.com/rss.xml', 'type': 'tech'},

    # 财经
    {'name': 'Bloomberg', 'url': 'https://feeds.bloomberg.com/markets/news.rss', 'type': 'finance'},
    {'name': 'CoinDesk', 'url': 'https://www.coindesk.com/arc/outboundfeeds/rss/', 'type': 'crypto'},

    # 国内科技企业
    {'name': '小米社区', 'url': 'https://bbs.xiaomi.cn/feed', 'type': 'tech'},
    {'name': '小米博客', 'url': 'https://blog.mi.com/feed/', 'type': 'tech'},
    {'name': '华为新闻', 'url': 'https://www.huawei.com/cn/rss', 'type': 'tech'},
    {'name': '华为博客', 'url': 'https://blog.huawei.com/feed/', 'type': 'tech'},
    {'name': 'OPPO新闻', 'url': 'https://www.oppo.com/cn/news/feed/', 'type': 'tech'},
    {'name': 'vivo新闻', 'url': 'https://www.vivo.com/cn/news/feed', 'type': 'tech'},
    {'name': '联想新闻', 'url': 'https://news.lenovo.com/feed/', 'type': 'tech'},
    {'name': '比亚迪新闻', 'url': 'https://www.byd.com/cn/rss', 'type': 'tech'},
    {'name': '大疆新闻', 'url': 'https://www.dji.com/cn/newsroom/feed', 'type': 'tech'},
    {'name': '中兴通讯', 'url': 'https://www.zte.com.cn/cn/rss', 'type': 'tech'},
    {'name': '网易科技', 'url': 'https://tech.163.com/special/00094IHV/techimportant.xml', 'type': 'tech'},
    {'name': '新浪科技', 'url': 'https://rss.sina.com.cn/tech/rollnews.xml', 'type': 'tech'},
    {'name': '腾讯科技', 'url': 'https://www.qq.com/rss/tech.xml', 'type': 'tech'},
    {'name': '极客公园', 'url': 'https://www.geekpark.net/rss', 'type': 'tech'},
    {'name': '爱范儿', 'url': 'https://www.ifanr.com/feed', 'type': 'tech'},

    # 国际科技企业
    {'name': 'Apple Newsroom', 'url': 'https://www.apple.com/newsroom/rss-feed.rss', 'type': 'tech'},
    {'name': 'Google Blog', 'url': 'https://blog.google/rss/', 'type': 'tech'},
    {'name': 'Microsoft Blog', 'url': 'https://blogs.microsoft.com/feed/', 'type': 'tech'},
    {'name': 'Tesla Blog', 'url': 'https://www.tesla.com/blog/feed', 'type': 'tech'},
    {'name': 'Meta News', 'url': 'https://about.fb.com/news/feed/', 'type': 'tech'},
    {'name': 'NVIDIA Blog', 'url': 'https://blogs.nvidia.com/feed/', 'type': 'tech'},
    {'name': 'Samsung News', 'url': 'https://news.samsung.com/global/feed', 'type': 'tech'},
    {'name': 'Intel News', 'url': 'https://www.intel.com/content/www/us/en/newsroom/rss.html', 'type': 'tech'},
    {'name': 'AMD News', 'url': 'https://www.amd.com/en/blog.xml', 'type': 'tech'},
    {'name': 'Qualcomm News', 'url': 'https://www.qualcomm.com/news/rss', 'type': 'tech'},
    {'name': 'OpenAI Blog', 'url': 'https://openai.com/blog/rss.xml', 'type': 'tech'},
    {'name': 'GitHub Blog', 'url': 'https://github.blog/feed/', 'type': 'tech'},
    {'name': 'AWS Blog', 'url': 'https://aws.amazon.com/blogs/aws/feed/', 'type': 'tech'},
    {'name': 'Cloudflare Blog', 'url': 'https://blog.cloudflare.com/rss/', 'type': 'tech'},

    # AI公司
    {'name': 'Anthropic Blog', 'url': 'https://www.anthropic.com/rss.xml', 'type': 'tech'},
    {'name': 'DeepMind Blog', 'url': 'https://deepmind.google/blog/rss.xml', 'type': 'tech'},
    {'name': 'Hugging Face Blog', 'url': 'https://huggingface.co/blog/feed.xml', 'type': 'tech'},
    {'name': 'Mistral AI', 'url': 'https://mistral.ai/feed.xml', 'type': 'tech'},

    # 芯片/硬件
    {'name': 'TSMC', 'url': 'https://pr.tsmc.com/english/rss/news.xml', 'type': 'tech'},
    {'name': 'Arm Blog', 'url': 'https://community.arm.com/arm-community-blogs/b/blog.rss', 'type': 'tech'},

    # 云计算/SaaS
    {'name': 'Stripe Blog', 'url': 'https://stripe.com/blog/feed.rss', 'type': 'tech'},
    {'name': 'Vercel Blog', 'url': 'https://vercel.com/atom', 'type': 'tech'},
    {'name': 'Docker Blog', 'url': 'https://www.docker.com/blog/feed/', 'type': 'tech'},

    # 央行/监管
    {'name': '欧央行·新闻', 'url': 'https://www.ecb.europa.eu/rss/press.html', 'type': 'fed'},
    {'name': '美联储(RSSHub)', 'url': 'https://rsshub.app/federalreserve/press', 'type': 'fed'},
    {'name': '英格兰银行', 'url': 'https://www.bankofengland.co.uk/rss/news', 'type': 'fed'},

    # 外交/国际组织
    {'name': '联合国新闻', 'url': 'https://news.un.org/feed/subscribe/en/news/all/rss.xml', 'type': 'diplomatic'},
    {'name': '中国外交部(RSSHub)', 'url': 'https://rsshub.app/fmprc/fyrbt', 'type': 'diplomatic'},
    {'name': '美国国务院(RSSHub)', 'url': 'https://rsshub.app/state/briefing', 'type': 'diplomatic'},

    # 加密货币
    {'name': 'Decrypt', 'url': 'https://decrypt.co/feed', 'type': 'crypto'},
    {'name': 'Cointelegraph', 'url': 'https://cointelegraph.com/rss', 'type': 'crypto'},
    {'name': 'Bitcoin.com', 'url': 'https://news.bitcoin.com/feed/', 'type': 'crypto'},

    # 学术/科学
    {'name': 'Nature News', 'url': 'https://www.nature.com/nature.rss', 'type': 'science'},
    {'name': 'Science News', 'url': 'https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science', 'type': 'science'},
    {'name': 'MIT Technology Review', 'url': 'https://www.technologyreview.com/feed/', 'type': 'science'},
    {'name': 'arXiv AI', 'url': 'http://arxiv.org/rss/cs.AI', 'type': 'science'},
    {'name': 'arXiv ML', 'url': 'http://arxiv.org/rss/cs.LG', 'type': 'science'},
    {'name': 'Wired Science', 'url': 'https://www.wired.com/feed/category/science/latest/rss', 'type': 'science'},

    # 地缘政治/智库
    {'name': '外交事务', 'url': 'https://www.foreignaffairs.com/rss.xml', 'type': 'geopolitical'},
    {'name': 'RAND智库(RSSHub)', 'url': 'https://rsshub.app/rand/blog', 'type': 'geopolitical'},

    # 财经补充
    {'name': '华尔街见闻(RSSHub)', 'url': 'https://rsshub.app/wallstreetcn/news/global', 'type': 'finance'},
    {'name': '财新网(RSSHub)', 'url': 'https://rsshub.app/caixin/latest', 'type': 'finance'},
    {'name': '第一财经(RSSHub)', 'url': 'https://rsshub.app/yicai/brief', 'type': 'finance'},
]

def fetch_all_rss():
    """抓取所有RSS源，返回新增新闻数量"""
    new_count = 0
    for source in RSS_SOURCES:
        try:
            feed = feedparser.parse(source['url'])
            if feed.bozo and not feed.entries:
                logger.warning(f"RSS解析异常 {source['name']}: {feed.bozo_exception}")
                continue

            for entry in feed.entries[:20]:
                title = entry.get('title', '').strip()
                if not title:
                    continue
                link = entry.get('link', '')
                if not link:
                    continue

                content = entry.get('summary', entry.get('description', ''))
                # 清理HTML标签
                if content:
                    if '<' in content and '>' in content:
                        content = safe_truncate(clean_html(content))
                    else:
                        content = safe_truncate(content)

                pub_time = parse_feed_time(entry)
                author = entry.get('author', source['name'])

                _, is_new = insert_news(
                    title=title, content=content, link=link,
                    source=source['name'], source_type=source['type'],
                    author=author, pub_time=pub_time
                )
                if is_new:
                    new_count += 1

        except Exception as e:
            logger.error(f"抓取失败 {source['name']}: {e}")

    logger.info(f"RSS采集完成，新增 {new_count} 条")
    return new_count
