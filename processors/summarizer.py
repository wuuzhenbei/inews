import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from database.db import get_unsummarized_news, save_ai_summary, get_ai_summary
from utils.ai_client import get_ai_client
from config import AI_MODEL

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = """请对以下新闻进行简要分析总结，包含:
1. 核心事件
2. 关键影响
3. 后续关注点

标题：{title}
内容：{content}

中文回答，简洁专业，200字以内。"""


def _summarize_one(news):
    """为单条新闻生成AI总结"""
    news_id = news['id']
    cached = get_ai_summary(news_id)
    if cached:
        return True

    title = news.get('title', '')
    content = (news.get('content', '') or '')[:800]
    if not title:
        return False

    prompt = SUMMARY_PROMPT.format(title=title, content=content)
    try:
        client = get_ai_client()
        resp = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的新闻分析师。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        summary = resp.choices[0].message.content
        save_ai_summary(news_id, summary)
        return True
    except Exception as e:
        logger.error(f"自动总结失败 news_id={news_id}: {e}")
        return False


def auto_batch_summarize(limit=10):
    """自动批量总结未总结的高分新闻（供调度器调用）"""
    news_list = get_unsummarized_news(limit=limit)
    if not news_list:
        logger.debug("没有需要自动总结的新闻")
        return 0

    success = 0
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(_summarize_one, n): n for n in news_list}
        for future in as_completed(futures):
            try:
                if future.result():
                    success += 1
            except Exception as e:
                logger.error(f"总结线程异常: {e}")

    if success > 0:
        logger.info(f"自动总结完成: {success}/{len(news_list)} 条")
    return success
