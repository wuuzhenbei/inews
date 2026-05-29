def safe_truncate(text, max_chars=2000):
    """安全截断文本，避免在代理对中间截断"""
    if not text:
        return ''
    if len(text) <= max_chars:
        return text
    return text[:max_chars]
