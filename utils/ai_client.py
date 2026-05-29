import threading
from config import AI_API_KEY, AI_BASE_URL

_client = None
_client_lock = threading.Lock()

def get_ai_client():
    """获取线程安全的OpenAI客户端单例"""
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                from openai import OpenAI
                _client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
    return _client
