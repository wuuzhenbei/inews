import os
import sys
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, jsonify, request, send_from_directory, Response, stream_with_context
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(__file__))

from database.db import (
    init_db, get_conn, get_news_list, get_statistics, mark_read,
    get_config, save_config, search_news, save_ai_summary, get_ai_summary,
    get_unsummarized_news, get_all_news_context, get_news_by_keyword, cleanup_old_news,
    toggle_bookmark, get_bookmarked_news
)
from collectors.scheduler import start_scheduler
from processors.scorer import batch_score
from config import WEB_HOST, WEB_PORT, DEFAULT_INTEREST_WEIGHTS, AI_API_KEY, AI_BASE_URL, AI_MODEL, AI_CHAT_MODEL, API_ACCESS_KEY
from utils.ai_client import get_ai_client

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
CORS(app, origins=['http://localhost:5000', 'http://127.0.0.1:5000', 'http://0.0.0.0:5000', 'http://10.3.182.211:5000'], supports_credentials=True)

# API鉴权中间件
@app.before_request
def check_api_key():
    if API_ACCESS_KEY and request.path.startswith('/api/'):
        key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if key != API_ACCESS_KEY:
            return jsonify({'error': 'unauthorized'}), 401

# 允许的配置key
ALLOWED_CONFIG_KEYS = {'interest_weights', 'blocked_keywords', 'ai_model',
                       'refresh_interval', 'collect_interval', 'breaking_threshold',
                       'breaking_types'}

executor = ThreadPoolExecutor(max_workers=8)

def _build_summary_prompt(title, content, source_type, direction):
    if source_type == 'finance' or direction == '财经' or any(k in title for k in ['股','债','基金','利率','GDP','通胀','CPI','Fed','央行','汇率','黄金','原油','Bitcoin','BTC','ETH','crypto']):
        return f"""请对以下财经新闻做专业分析总结，要求：
1. 用2-3句话概括核心事件
2. 对以下市场的影响分析：
   - 股票市场（A股/美股/港股相关板块）
   - 期货市场（商品期货/金融期货）
   - 黄金与贵金属
   - 加密货币（BTC/ETH等）
   - 外汇市场（人民币/美元/欧元等）
   - 债券市场
3. 投资建议方向（看多/看空/观望）

新闻标题：{title}
新闻内容：{content[:800]}

请用中文回答，简洁专业。"""
    elif source_type == 'tech' or direction == '科技':
        return f"""请对以下科技新闻做分析总结，要求：
1. 用2-3句话概括核心事件
2. 对行业的影响（AI/半导体/消费电子/云计算/新能源等）
3. 相关公司和产业链影响
4. 技术趋势判断

新闻标题：{title}
新闻内容：{content[:800]}

请用中文回答，简洁专业。"""
    elif source_type == 'x':
        return f"""请对以下社交媒体动态做分析总结，要求：
1. 用2-3句话概括核心信息
2. 发布者的身份和影响力说明
3. 可能的后续影响和关注点
4. 如果涉及财经，补充市场影响

新闻标题：{title}
新闻内容：{content[:800]}

请用中文回答，简洁专业。"""
    else:
        return f"""请对以下新闻做分析总结，要求：
1. 用2-3句话概括核心事件
2. 事件的背景和重要性
3. 可能的影响和后续发展
4. 关注要点

新闻标题：{title}
新闻内容：{content[:800]}

请用中文回答，简洁专业。"""

def _generate_single_summary(news, override_prompt=None, force=False):
    """为单条新闻生成AI总结（线程安全）。override_prompt可覆盖默认prompt，force=True跳过缓存。"""
    news_id = news['id']
    if not force:
        cached = get_ai_summary(news_id)
        if cached:
            return {'id': news_id, 'summary': cached, 'cached': True}

    title = news.get('title', '')
    content = news.get('content', '')
    source_type = news.get('source_type', 'media')
    direction = news.get('direction', '')
    prompt = override_prompt or _build_summary_prompt(title, content, source_type, direction)

    try:
        client = get_ai_client()
        resp = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的新闻分析师，擅长对各类新闻进行深度解读和影响分析。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        summary = resp.choices[0].message.content
        save_ai_summary(news_id, summary)
        return {'id': news_id, 'summary': summary, 'cached': False}
    except Exception as e:
        logger.error(f"AI总结失败 news_id={news_id}: {e}")
        return {'id': news_id, 'error': str(e)}

# ── 前端页面 ──
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# ── 新闻API ──
@app.route('/api/news')
def api_news():
    sort = request.args.get('sort', 'score')
    source = request.args.get('source', 'all')
    keyword = request.args.get('keyword', None)
    direction = request.args.get('direction', None)
    author = request.args.get('author', None)
    days = request.args.get('days', None)
    if days is not None:
        try:
            days = int(days)
        except (ValueError, TypeError):
            return jsonify({'error': 'invalid days parameter'}), 400
    try:
        limit = min(int(request.args.get('limit', 200)), 500)
        offset = max(int(request.args.get('offset', 0)), 0)
    except (ValueError, TypeError):
        return jsonify({'error': 'invalid limit/offset'}), 400
    news = get_news_list(sort=sort, source_type=source, keyword=keyword, days=days,
                         limit=limit, offset=offset, direction=direction, author=author)
    return jsonify(news)

@app.route('/api/news/<int:news_id>/read', methods=['POST'])
def api_mark_read(news_id):
    mark_read(news_id)
    return jsonify({'status': 'ok'})

@app.route('/api/news/<int:news_id>/bookmark', methods=['POST'])
def api_toggle_bookmark(news_id):
    result = toggle_bookmark(news_id)
    if result is None:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'status': 'ok', 'is_bookmarked': result})

@app.route('/api/bookmarks')
def api_bookmarks():
    news = get_bookmarked_news(limit=200)
    return jsonify(news)

@app.route('/api/search')
def api_search():
    keyword = request.args.get('q', '')
    if not keyword:
        return jsonify([])
    results = search_news(keyword)
    return jsonify(results)

@app.route('/api/authors')
def api_authors():
    """获取去重的作者/来源列表，可按source_type筛选"""
    source_type = request.args.get('source', None)
    with get_conn() as conn:
        if source_type and source_type != 'all':
            rows = conn.execute(
                "SELECT DISTINCT author FROM news WHERE author IS NOT NULL AND author != '' AND source_type = ? ORDER BY author",
                (source_type,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT DISTINCT author, source_type FROM news WHERE author IS NOT NULL AND author != '' ORDER BY source_type, author"
            ).fetchall()
    if source_type and source_type != 'all':
        return jsonify([r['author'] for r in rows])
    else:
        result = {}
        for r in rows:
            st = r['source_type'] or 'other'
            if st not in result:
                result[st] = []
            result[st].append(r['author'])
        return jsonify(result)

@app.route('/api/statistics')
def api_statistics():
    return jsonify(get_statistics())

# ── AI总结API（带缓存）──
@app.route('/api/news/<int:news_id>/summary')
def api_news_summary(news_id):
    focus = request.args.get('focus', '')
    regenerate = request.args.get('regenerate', '') == '1'

    # 非重新生成时检查缓存
    if not regenerate:
        cached = get_ai_summary(news_id)
        if cached:
            return jsonify({'summary': cached, 'type': 'cached', 'cached': True})

    with get_conn() as conn:
        row = conn.execute("SELECT * FROM news WHERE id = ?", (news_id,)).fetchone()
    if not row:
        return jsonify({'error': 'not found'}), 404

    news = dict(row)
    # 如果指定了focus，覆盖默认的source_type判断
    if focus:
        title = news.get('title', '')
        content = news.get('content', '')
        prompt = _build_summary_prompt(title, content, focus, focus)
    else:
        prompt = None
    result = _generate_single_summary(news, override_prompt=prompt, force=True)
    if 'error' in result:
        return jsonify({'error': result['error']}), 500
    return jsonify({'summary': result['summary'], 'type': news.get('source_type',''), 'cached': False})

# ── 批量总结API（并行）──
@app.route('/api/summary/batch', methods=['POST'])
def api_batch_summary():
    limit = request.json.get('limit', 10) if request.json else 10
    news_list = get_unsummarized_news(limit=limit)
    if not news_list:
        return jsonify({'processed': 0, 'success': 0, 'message': '没有需要总结的新闻'})

    results = []
    futures = {executor.submit(_generate_single_summary, n): n for n in news_list}
    for future in as_completed(futures, timeout=120):
        try:
            r = future.result(timeout=60)
            results.append(r)
        except Exception as e:
            results.append({'error': str(e)})

    success = sum(1 for r in results if 'summary' in r)
    return jsonify({'processed': len(results), 'success': success})

# ── 新闻聊天API（流式）──
@app.route('/api/news/<int:news_id>/chat', methods=['POST'])
def api_news_chat(news_id):
    data = request.json or {}
    user_msg = data.get('message', '')
    if not user_msg:
        return jsonify({'error': 'empty message'}), 400

    with get_conn() as conn:
        row = conn.execute("SELECT * FROM news WHERE id = ?", (news_id,)).fetchone()
    if not row:
        return jsonify({'error': 'not found'}), 404

    news = dict(row)
    ai_summary = get_ai_summary(news_id) or ''

    chat_model = AI_CHAT_MODEL or AI_MODEL

    system_prompt = f"""你是新闻分析师。用户正在阅读以下新闻，请基于内容回答问题。
标题：{news.get('title','')}
来源：{news.get('source','')} ({news.get('source_type','')})
内容：{(news.get('content','') or '')[:800]}
总结：{ai_summary}
简洁专业回答。"""

    def generate():
        try:
            client = get_ai_client()
            stream = client.chat.completions.create(
                model=chat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ],
                max_tokens=1000,
                temperature=0.5,
                stream=True
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield f"data: {json.dumps({'text': chunk.choices[0].delta.content}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return Response(stream_with_context(generate()), content_type='text/event-stream')

# ── RAG全局对话API（流式）──
@app.route('/api/chat', methods=['POST'])
def api_rag_chat():
    data = request.json or {}
    user_msg = data.get('message', '')
    if not user_msg:
        return jsonify({'error': 'empty message'}), 400

    # RAG优化：关键词匹配中英文，减少上下文量
    import re
    keywords = re.findall(r'[一-鿿]{2,}|[a-zA-Z]{3,}', user_msg)
    if keywords:
        news_context = get_news_by_keyword(keywords, limit=30)
        if not news_context:
            news_context = get_all_news_context(limit=50)
    else:
        news_context = get_all_news_context(limit=50)

    context_parts = []
    for n in news_context:
        score = n.get('ai_score', '')
        line = f"[{n['source_type']}] {n['title']}"
        if score:
            line += f"({score})"
        direction = n.get('direction', '')
        if direction:
            line += f"[{direction}]"
        summary = n.get('ai_summary', '')
        if summary:
            line += f" - {summary[:80]}"
        context_parts.append(line)

    context_text = '\n'.join(context_parts)

    chat_model = AI_CHAT_MODEL or AI_MODEL

    system_prompt = f"""你是新闻助手。基于以下{len(news_context)}条新闻回答问题。
新闻数据：
{context_text[:4000]}
要求：简洁专业，中文回答，可引用新闻标题。"""

    def generate():
        try:
            client = get_ai_client()
            stream = client.chat.completions.create(
                model=chat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ],
                max_tokens=800,
                temperature=0.5,
                stream=True
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield f"data: {json.dumps({'text': chunk.choices[0].delta.content}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return Response(stream_with_context(generate()), content_type='text/event-stream')

# ── 配置API ──
@app.route('/api/config', methods=['GET'])
def api_get_config():
    config = get_config()
    return jsonify(config)

@app.route('/api/config', methods=['POST'])
def api_save_config():
    data = request.json
    if not data:
        return jsonify({'error': 'no data'}), 400
    for key, value in data.items():
        if key not in ALLOWED_CONFIG_KEYS:
            continue  # 忽略非法key
        save_config(key, value if isinstance(value, str) else json.dumps(value, ensure_ascii=False))
    return jsonify({'status': 'saved'})

@app.route('/api/config/weights', methods=['GET'])
def api_get_weights():
    raw = get_config('interest_weights')
    if raw:
        try:
            return jsonify(json.loads(raw))
        except (json.JSONDecodeError, TypeError):
            pass
    return jsonify(DEFAULT_INTEREST_WEIGHTS)

@app.route('/api/config/weights', methods=['POST'])
def api_save_weights():
    data = request.json
    if not data or not isinstance(data, dict):
        return jsonify({'error': 'invalid request body'}), 400
    save_config('interest_weights', json.dumps(data, ensure_ascii=False))
    return jsonify({'status': 'saved'})

# ── AI深度分析API ──
@app.route('/api/news/<int:news_id>/risk')
def api_risk_assessment(news_id):
    """A10: 风险评估"""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM news WHERE id = ?", (news_id,)).fetchone()
    if not row:
        return jsonify({'error': 'not found'}), 404
    news = dict(row)
    prompt = f"""对此新闻进行风险评估，用JSON格式返回:
新闻标题：{news.get('title','')}
新闻内容：{(news.get('content','') or '')[:600]}

返回格式：
{{"market_risk":1-10,"geopolitical_risk":1-10,"tech_risk":1-10,"regulatory_risk":1-10,"social_risk":1-10,"overall":"低/中/高/极高","analysis":"简要分析"}}"""

    try:
        client = get_ai_client()
        resp = client.chat.completions.create(
            model=AI_CHAT_MODEL or AI_MODEL,
            messages=[
                {"role": "system", "content": "你是风险评估专家。只返回JSON，不要其他内容。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500, temperature=0.3
        )
        import re
        text = resp.choices[0].message.content
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return jsonify(json.loads(json_match.group()))
        return jsonify({'error': '解析失败', 'raw': text}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/news/<int:news_id>/impact')
def api_impact_prediction(news_id):
    """A4: 影响预测"""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM news WHERE id = ?", (news_id,)).fetchone()
    if not row:
        return jsonify({'error': 'not found'}), 404
    news = dict(row)
    prompt = f"""基于此新闻预测后续发展:
标题：{news.get('title','')}
内容：{(news.get('content','') or '')[:600]}

用JSON返回:
{{"next_24h":"24小时内可能进展","next_week":"一周内可能走向","market_impact":"市场影响","key_signals":"需关注的关键信号","historical_precedent":"历史先例"}}"""

    try:
        client = get_ai_client()
        resp = client.chat.completions.create(
            model=AI_CHAT_MODEL or AI_MODEL,
            messages=[
                {"role": "system", "content": "你是趋势预测专家。只返回JSON。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600, temperature=0.4
        )
        import re
        text = resp.choices[0].message.content
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return jsonify(json.loads(json_match.group()))
        return jsonify({'error': '解析失败', 'raw': text}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/news/<int:news_id>/perspectives')
def api_multi_perspective(news_id):
    """A1: 多视角分析"""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM news WHERE id = ?", (news_id,)).fetchone()
    if not row:
        return jsonify({'error': 'not found'}), 404
    news = dict(row)
    prompt = f"""从不同立场分析此新闻:
标题：{news.get('title','')}
内容：{(news.get('content','') or '')[:600]}

用JSON返回:
{{"wall_street":"投资者/金融角度","white_house":"美国政府/政策角度","beijing":"中国/外交角度","tech_circle":"技术/创新角度","public":"普通民众角度"}}"""

    try:
        client = get_ai_client()
        resp = client.chat.completions.create(
            model=AI_CHAT_MODEL or AI_MODEL,
            messages=[
                {"role": "system", "content": "你是多视角分析师。只返回JSON。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800, temperature=0.4
        )
        import re
        text = resp.choices[0].message.content
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return jsonify(json.loads(json_match.group()))
        return jsonify({'error': '解析失败', 'raw': text}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/brief', methods=['GET', 'POST'])
def api_daily_market_brief():
    """I1: 每日市场简报"""
    news_context = get_all_news_context(limit=80)
    finance_news = [n for n in news_context if n.get('source_type') in ('finance', 'fed', 'crypto') or '股' in n.get('title','') or '市场' in n.get('title','')]
    if not finance_news:
        finance_news = news_context[:30]

    context_parts = []
    for n in finance_news[:30]:
        line = f"- {n['title']}"
        summary = n.get('ai_summary', '')
        if summary:
            line += f" ({summary[:60]})"
        context_parts.append(line)

    prompt = f"""基于以下财经新闻，生成今日市场简报:
{chr(10).join(context_parts)}

格式：
1. 全球市场概览
2. 重大财经事件
3. 央行/监管动态
4. 行业板块表现
5. 明日关注
简洁专业，中文回答。"""

    # 支持流式和非流式两种模式
    use_stream = request.args.get('stream', '1') == '1'

    if use_stream:
        def generate():
            try:
                client = get_ai_client()
                stream = client.chat.completions.create(
                    model=AI_CHAT_MODEL or AI_MODEL,
                    messages=[
                        {"role": "system", "content": "你是专业财经分析师。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000, temperature=0.4, stream=True
                )
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield f"data: {json.dumps({'text': chunk.choices[0].delta.content}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

        return Response(stream_with_context(generate()), content_type='text/event-stream',
                        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
    else:
        try:
            client = get_ai_client()
            resp = client.chat.completions.create(
                model=AI_CHAT_MODEL or AI_MODEL,
                messages=[
                    {"role": "system", "content": "你是专业财经分析师。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000, temperature=0.4
            )
            text = resp.choices[0].message.content
            return jsonify({'text': text})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# ── 手动操作API ──
@app.route('/api/score/trigger', methods=['POST'])
def api_trigger_score():
    count = batch_score(limit=20)
    return jsonify({'scored': count})

@app.route('/api/collect/trigger', methods=['POST'])
def api_trigger_collect():
    from collectors.rss_collector import fetch_all_rss
    from collectors.x_collector import fetch_x_tweets
    from collectors.rsshub_collector import fetch_rsshub_feeds
    from collectors.hotlist_collector import fetch_all_hotlists
    total = 0
    total += fetch_all_rss()
    total += fetch_x_tweets()
    total += fetch_rsshub_feeds()
    total += fetch_all_hotlists()
    return jsonify({'new_articles': total})

def _first_collect():
    try:
        from collectors.rss_collector import fetch_all_rss
        from collectors.x_collector import fetch_x_tweets
        from collectors.rsshub_collector import fetch_rsshub_feeds
        from collectors.hotlist_collector import fetch_all_hotlists
        logger.info("开始首次数据采集...")
        fetch_all_rss()
        fetch_x_tweets()
        fetch_rsshub_feeds()
        fetch_all_hotlists()
        # 首次采集后立即评分
        batch_score(limit=30)
        logger.info("首次采集+评分完成")
    except Exception as e:
        logger.error(f"首次采集异常: {e}")

# ── 采集状态追踪 ──
_collector_status = {
    'last_rss': None, 'last_x': None, 'last_rsshub': None, 'last_hotlist': None,
    'rss_ok': None, 'x_ok': None, 'rsshub_ok': None, 'hotlist_ok': None,
    'started_at': None,
}

@app.route('/api/health')
def api_health():
    """采集健康状态面板"""
    stats = get_statistics()
    from collectors.rsshub_collector import get_working_rsshub, check_rsshub_available
    from config import RSSHUB_BASE
    rsshub_ok = check_rsshub_available(RSSHUB_BASE, timeout=3)

    # 获取各源的新闻数量分布
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT source_type, COUNT(*) as cnt FROM news GROUP BY source_type ORDER BY cnt DESC"
        ).fetchall()
        type_dist = {r['source_type']: r['cnt'] for r in rows}

        # 最近24小时各源采集情况
        rows2 = conn.execute(
            "SELECT source, MAX(fetch_time) as last_fetch, COUNT(*) as cnt "
            "FROM news WHERE fetch_time > datetime('now', '-1 day') "
            "GROUP BY source ORDER BY cnt DESC LIMIT 30"
        ).fetchall()
        source_activity = [{'source': r['source'], 'last_fetch': r['last_fetch'], 'count': r['cnt']} for r in rows2]

    return jsonify({
        'status': 'ok',
        'rsshub_available': rsshub_ok,
        'rsshub_url': RSSHUB_BASE,
        'statistics': stats,
        'source_distribution': type_dist,
        'recent_sources': source_activity,
    })

# ── 启动 ──
if __name__ == '__main__':
    init_db()
    logger.info("数据库初始化完成")
    # 异步执行首次采集，不阻塞Web服务启动
    threading.Thread(target=_first_collect, daemon=True, name='first-collect').start()
    start_scheduler()
    logger.info(f"Web服务启动: http://localhost:{WEB_PORT}")
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False, threaded=True)
