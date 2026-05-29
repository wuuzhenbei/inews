from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

CST = timezone(timedelta(hours=8))

def parse_pub_time(time_str, fallback=None):
    """解析时间字符串，返回北京时间字符串，支持多种格式"""
    if not time_str:
        return fallback or datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(time_str, datetime):
        return time_str.astimezone(CST).strftime('%Y-%m-%d %H:%M:%S')
    time_str = str(time_str).strip()
    # ISO 8601
    if 'T' in time_str:
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            return dt.astimezone(CST).strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            pass
    # 常见格式
    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S', '%a, %d %b %Y %H:%M:%S']:
        try:
            dt = datetime.strptime(time_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=CST)
            return dt.astimezone(CST).strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            pass
    return fallback or datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S')

def parse_feed_time(entry):
    """从feed entry解析发布时间，转为北京时间(UTC+8)"""
    for field in ['published_parsed', 'updated_parsed']:
        t = entry.get(field)
        if t:
            try:
                dt = datetime(*t[:6], tzinfo=timezone.utc).astimezone(CST)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError, OverflowError):
                pass
    # 回退：尝试解析时间字符串
    for field in ['published', 'updated', 'created']:
        t = entry.get(field)
        if t:
            try:
                dt = datetime.fromisoformat(str(t).replace('Z', '+00:00'))
                return dt.astimezone(CST).strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                pass
    return None

def clean_html(html_text):
    """去除HTML标签，返回纯文本"""
    if not html_text:
        return ''
    return BeautifulSoup(html_text, 'html.parser').get_text(separator=' ', strip=True)
