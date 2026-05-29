import requests
from datetime import datetime
import logging
import json
from database.db import insert_news

logger = logging.getLogger(__name__)

def fetch_weibo_hot():
    """直接抓取微博热搜（备用方案，不依赖RSSHub）"""
    try:
        url = 'https://weibo.com/ajax/side/hotSearch'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        new_count = 0
        # 使用日期作为去重的一部分，同一天同一话题不重复
        date_prefix = datetime.now().strftime('%Y%m%d')
        for item in data.get('data', {}).get('realtime', [])[:30]:
            title = item.get('word', '')
            if not title:
                continue
            # 使用日期+标题作为唯一链接
            link = f'https://s.weibo.com/weibo?q=%23{title}%23&date={date_prefix}'
            content = f"微博热搜排名{item.get('rank', '?')}，热度{item.get('num', '?')}"
            _, is_new = insert_news(
                title=f'[微博热搜] {title}',
                content=content, link=link,
                source='微博热搜', source_type='hotlist',
                pub_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            if is_new:
                new_count += 1
        logger.info(f"微博热搜采集完成，新增 {new_count} 条")
        return new_count
    except Exception as e:
        logger.error(f"微博热搜采集失败: {e}")
        return 0

def fetch_toutiao_hot():
    """抓取今日头条热榜"""
    try:
        url = 'https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        new_count = 0
        date_prefix = datetime.now().strftime('%Y%m%d')
        for item in data.get('data', [])[:30]:
            title = item.get('Title', '')
            if not title:
                continue
            link = item.get('Url', '')
            hot_value = item.get('HotValue', '')
            content = f"头条热榜，热度值: {hot_value}"
            # 如果没有独立链接，使用日期+标题
            if not link:
                link = f'https://www.toutiao.com/search/?keyword={title}&date={date_prefix}'
            _, is_new = insert_news(
                title=f'[头条热榜] {title}',
                content=content, link=link,
                source='今日头条', source_type='hotlist',
                pub_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            if is_new:
                new_count += 1
        logger.info(f"头条热榜采集完成，新增 {new_count} 条")
        return new_count
    except Exception as e:
        logger.error(f"头条热榜采集失败: {e}")
        return 0

def fetch_zhihu_hot():
    """抓取知乎热榜（直接API）"""
    try:
        url = 'https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=30'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        new_count = 0
        date_prefix = datetime.now().strftime('%Y%m%d')
        for item in data.get('data', [])[:30]:
            target = item.get('target', {})
            title = target.get('title', '')
            if not title:
                continue
            question_id = target.get('id', '')
            # 使用日期+问题ID作为唯一链接
            link = f"https://www.zhihu.com/question/{question_id}?date={date_prefix}"
            excerpt = target.get('excerpt', '')
            heat = item.get('detail_text', '')
            _, is_new = insert_news(
                title=f'[知乎热榜] {title}',
                content=f"{excerpt} | 热度: {heat}" if excerpt else f"热度: {heat}",
                link=link,
                source='知乎热榜', source_type='hotlist',
                pub_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            if is_new:
                new_count += 1
        logger.info(f"知乎热榜采集完成，新增 {new_count} 条")
        return new_count
    except Exception as e:
        logger.error(f"知乎热榜采集失败: {e}")
        return 0

def fetch_all_hotlists():
    """抓取所有热搜热榜"""
    total = 0
    total += fetch_weibo_hot()
    total += fetch_toutiao_hot()
    total += fetch_zhihu_hot()
    return total
