import threading
import signal
import logging
from collectors.rss_collector import fetch_all_rss
from collectors.rsshub_collector import fetch_rsshub_feeds
from collectors.hotlist_collector import fetch_all_hotlists
from collectors.x_collector import fetch_x_tweets
from processors.scorer import batch_score
from processors.summarizer import auto_batch_summarize
from database.db import cleanup_old_news, get_config
from config import FETCH_INTERVAL_MEDIA, FETCH_INTERVAL_X, FETCH_INTERVAL_HOTLIST

logger = logging.getLogger(__name__)

_running = False
_stop_event = threading.Event()

def _signal_handler(sig, frame):
    global _running
    _running = False
    _stop_event.set()
    logger.info("收到停止信号，正在关闭调度器...")

def _run_loop(func, interval, name):
    """循环执行采集任务，使用Event实现可中断sleep"""
    while _running:
        try:
            logger.info(f"开始执行: {name}")
            count = func()
            logger.info(f"完成: {name}，处理 {count} 条")
        except Exception as e:
            logger.error(f"任务异常 {name}: {e}")
        # 使用Event.wait替代time.sleep，可被停止信号立即中断
        _stop_event.wait(interval)

def _get_config_interval(key, default):
    """从用户配置获取间隔值"""
    val = get_config(key)
    if val:
        try:
            return int(val)
        except (ValueError, TypeError):
            pass
    return default

def start_scheduler():
    """启动后台采集和评分调度器"""
    global _running
    if _running:
        return
    _running = True
    _stop_event.clear()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    def _cleanup_task():
        deleted = cleanup_old_news(days=30)
        if deleted > 0:
            logger.info(f"清理了 {deleted} 条过期新闻")
        return deleted

    # RSSHub独立间隔（比X采集更慢，避免重复抓Twitter）
    rsshub_interval = max(FETCH_INTERVAL_X * 3, 360)  # 至少6分钟

    tasks = [
        (fetch_all_rss, FETCH_INTERVAL_MEDIA, 'RSS媒体采集'),
        (fetch_x_tweets, FETCH_INTERVAL_X, 'X关键人物采集'),
        (fetch_rsshub_feeds, rsshub_interval, 'RSSHub采集'),
        (fetch_all_hotlists, FETCH_INTERVAL_HOTLIST, '热搜热榜采集'),
        (batch_score, 120, 'AI批量评分'),
        (auto_batch_summarize, 600, 'AI自动总结'),
        (_cleanup_task, 86400, '数据清理'),
    ]

    for func, interval, name in tasks:
        t = threading.Thread(target=_run_loop, args=(func, interval, name), daemon=True, name=name)
        t.start()
        logger.info(f"已启动调度线程: {name} (间隔{interval}秒)")

    logger.info(f"调度器启动完成，共{len(tasks)}个线程")

def stop_scheduler():
    global _running
    _running = False
    _stop_event.set()
    logger.info("调度器已停止")
