import json
import re
import logging
import time
from config import AI_API_KEY, AI_BASE_URL, AI_MODEL
from database.db import get_unscored_news, update_score
from utils.ai_client import get_ai_client

logger = logging.getLogger(__name__)

def _extract_json(text):
    """从AI回复中提取JSON对象"""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass
    return None

# ── 尝试加载openai，失败则跳过API评分 ──
_api_available = False
_api_key_valid = None  # None=未测试, True=可用, False=不可用
try:
    from openai import OpenAI
    _api_available = True
except ImportError:
    logger.warning("openai库未安装，仅使用规则评分")

# ── 关键词权重库（用于规则评分）──
_KEYWORD_SCORES = {
    # 最高分关键词（全球重大影响）
    'war': 30, '战争': 30, '冲突': 22, 'nuclear': 28, '核武器': 28, '核': 22,
    'earthquake': 25, '地震': 25, 'tsunami': 25, '海啸': 25,
    'pandemic': 25, '疫情': 22, 'outbreak': 22,
    'assassination': 28, '刺杀': 28, 'coup': 25, '政变': 25,
    'invasion': 25, '入侵': 25, 'missile': 22, '导弹': 22,
    'kill': 18, '死': 15, '亡': 12, 'died': 15, 'death': 15,

    # 高分关键词
    'sanction': 18, '制裁': 18, 'tariff': 15, '关税': 15,
    'interest rate': 18, '利率': 18, 'inflation': 15, '通胀': 15,
    'fed': 15, '美联储': 18, '加息': 15, '降息': 15,
    'trump': 18, '特朗普': 20, 'biden': 15, '拜登': 18,
    'election': 15, '选举': 15, '总统': 15, 'president': 12,
    'summit': 12, '峰会': 12, '条约': 12, 'treaty': 12,

    # 中文新闻高频词（提升中文新闻评分）
    '重大': 15, '重要': 12, '紧急': 18, '突发': 20, '速报': 18,
    '首次': 10, '创历史新高': 15, '创新高': 12, '暴跌': 15, '暴涨': 15,
    '大涨': 12, '大跌': 12, '涨停': 10, '跌停': 10,
    '宣布': 8, '发布': 8, '公布': 8, '揭秘': 8,
    '中共': 12, '中央': 10, '国务院': 12, '两会': 12,
    '习近平': 15, '李强': 10, '中国': 6, '美国': 6, '俄罗斯': 8,
    '乌克兰': 12, '以色列': 12, '巴勒斯坦': 12, '加沙': 12,
    '朝鲜': 12, '韩国': 8, '日本': 8, '印度': 8,
    '中东': 10, '欧洲': 8, '亚太': 8,

    # 科技
    'ai': 10, '人工智能': 12, 'chatgpt': 12, 'gpt': 10, '大模型': 12,
    'spacex': 15, 'nasa': 12, '发射': 10, '火箭': 10, '卫星': 8,
    'apple': 10, '苹果': 10, 'google': 10, '谷歌': 10,
    'microsoft': 10, '微软': 10, 'tesla': 10, '特斯拉': 12,
    '芯片': 15, '半导体': 15, 'chip': 12, '光刻': 15,
    '华为': 12, '小米': 10, '比亚迪': 10, '腾讯': 8, '阿里': 8, '字节': 8,

    # 财经
    '股市': 10, 'a股': 12, '美股': 12, '港股': 10,
    '比特币': 12, '加密': 10, 'crypto': 10,
    '上市': 10, 'ipo': 10, '收购': 12, '并购': 12,
    '破产': 15, 'bankruptcy': 15, '暴雷': 15,
    'gdp': 10, '经济': 8, '增长': 8, '衰退': 12,

    # 灾害
    '洪水': 18, '台风': 18, '飓风': 18, '暴雨': 15,
    '火灾': 15, '爆炸': 18, 'accident': 12, '事故': 15,
    '坠机': 18, '空难': 20, '沉船': 15,

    # 社会热点
    '高考': 10, '考研': 8, '招聘': 6, '房价': 10,
    '医疗': 8, '反腐': 12, '落马': 15, '被查': 12,
    '失踪': 12, '遇害': 15, '绑架': 15,
}

_DIRECTION_KEYWORDS = {
    '政治': ['president', '总统', 'election', '选举', 'government', '政府', '政策', 'minister', '部长',
             'congress', '议会', 'trump', '特朗普', 'biden', '拜登', 'war', '战争', 'military', '军事',
             'diplomatic', '外交', 'sanction', '制裁', 'treaty', '条约', 'nato', '联合国', 'un', 'united nations'],
    '经济': ['economy', '经济', 'gdp', 'inflation', '通胀', 'interest rate', '利率', 'trade', '贸易',
             'tariff', '关税', 'import', '出口', 'export', '进口', 'market', '市场', 'recession', '衰退'],
    '科技': ['ai', '人工智能', 'tech', '科技', 'chip', '芯片', 'spacex', 'nasa', 'apple', 'google',
             'microsoft', 'openai', 'robot', '机器人', 'quantum', '量子', 'software', '软件', 'launch', '发布'],
    '军事': ['military', '军事', 'army', '军队', 'navy', '海军', 'air force', '空军', 'weapon', '武器',
             'missile', '导弹', 'nuclear', '核', 'troop', '部队', 'defense', '国防', 'invasion', '入侵'],
    '社会': ['society', '社会', 'education', '教育', 'health', '健康', 'environment', '环境',
             'protest', '抗议', 'crime', '犯罪', 'accident', '事故', 'earthquake', '地震', 'flood', '洪水'],
    '文化': ['culture', '文化', 'film', '电影', 'music', '音乐', 'sport', '体育', 'entertainment', '娱乐',
             'art', '艺术', 'fashion', '时尚', 'celebrity', '明星'],
    '突发': ['breaking', '突发', 'emergency', '紧急', 'urgent', '紧急', 'alert', '警报',
             'explosion', '爆炸', 'attack', '袭击', 'crash', '坠毁', 'disaster', '灾难'],
    '财经': ['stock', '股票', 'market', '市场', 'crypto', '加密', 'bitcoin', '比特币', 'ipo', '上市',
             'invest', '投资', 'fund', '基金', 'bank', '银行', 'finance', '金融', 'oil', '石油', 'gold', '黄金'],
}

# ── 来源权威性预设分数 ──
_SOURCE_AUTHORITY = {
    '新华网': 90, '央视新闻': 90, '人民日报': 88, 'BBC': 85, 'CNN': 82,
    'Reuters': 88, 'AP News': 85, 'NYT': 83, 'The Guardian': 80,
    'Al Jazeera': 78, 'France24': 76, 'Bloomberg': 85, 'CNBC': 80,
    '马斯克': 85, '特朗普': 82, '扎克伯格': 78, 'Breaking News': 88,
    '微博热搜': 65, '知乎热榜': 60, 'B站热搜': 55, '头条热榜': 60,
    'TechCrunch': 72, 'The Verge': 70, '36氪': 68, 'Hacker News': 70,
}


def _rule_based_score(title, content, source):
    """纯规则评分，不需要API"""
    text = f"{title} {content}".lower()
    title_lower = title.lower()

    # 1. 关键词影响力评分 - 标题权重更高
    impact = 20  # 基础分
    matched_keywords = []
    for kw, score in _KEYWORD_SCORES.items():
        kw_lower = kw.lower()
        if kw_lower in title_lower:
            impact += score * 1.8  # 标题中的关键词权重更高
            matched_keywords.append(kw)
        elif kw_lower in text:
            impact += score * 0.7
            matched_keywords.append(kw)
    impact = min(100, int(impact))

    # 2. 来源权威性
    authority = 55  # 提高默认值
    for src_name, score in _SOURCE_AUTHORITY.items():
        if src_name in source:
            authority = score
            break

    # 3. 时效性 - 有内容的新闻更新鲜
    timeliness = 75 if content and len(content) > 50 else 60

    # 4. 热度 - 关键词命中越多越热
    hotness = min(100, 25 + len(matched_keywords) * 12)

    # 5. 兴趣匹配 - 基于方向匹配度
    direction_scores = {}
    for dir_name, keywords in _DIRECTION_KEYWORDS.items():
        direction_scores[dir_name] = sum(1 for kw in keywords if kw.lower() in text)
    max_dir_count = max(direction_scores.values()) if direction_scores else 0
    interest_match = min(100, 35 + max_dir_count * 10)

    # 6. 新闻质量信号
    content_len = len(content or '')
    if content_len > 300:
        quality_bonus = 12
    elif content_len > 100:
        quality_bonus = 6
    else:
        quality_bonus = 0

    # 7. 突发程度
    emergency_keywords = ['breaking', '突发', 'urgent', '紧急', 'alert', '警报', 'just in', '刚刚', '速报']
    emergency = 25
    for kw in emergency_keywords:
        if kw in text:
            emergency = 85
            break

    # 8. 新闻类别基础分
    type_base = {
        'breaking': 70, '突发': 70,
        'media': 60, '权威': 60,
        'x': 65, '推特': 65,
        'hotlist': 50, '热搜': 50,
        'tech': 55, '科技': 55,
        'finance': 58, '财经': 58,
    }
    novelty = 50
    for kw, base in type_base.items():
        if kw in source.lower() or kw in source:
            novelty = base
            break

    # 9. 可信度
    credibility = int(authority * 0.7 + 18)

    # 10. 方向分类
    direction = max(direction_scores, key=direction_scores.get) if max_dir_count > 0 else '未分类'

    # 11. 综合评分
    total = int(
        impact * 0.35 +
        authority * 0.12 +
        timeliness * 0.08 +
        hotness * 0.15 +
        interest_match * 0.12 +
        novelty * 0.05 +
        emergency * 0.08 +
        credibility * 0.05
    )
    total = max(20, min(95, total + quality_bonus))

    # 12. 摘要（规则模式：取标题+方向标签）
    dir_label = direction if direction and direction != '未分类' else ''
    if dir_label:
        summary = f"[{dir_label}] {title[:45]}" if len(title) > 45 else f"[{dir_label}] {title}"
    else:
        summary = title[:50] if len(title) <= 50 else title[:47] + '...'

    return {
        'total_score': total,
        'impact': impact,
        'authority': authority,
        'timeliness': timeliness,
        'hotness': hotness,
        'interest_match': interest_match,
        'novelty': novelty,
        'emergency': emergency,
        'credibility': credibility,
        'direction': direction,
        'summary': summary,
    }


def _api_score(title, content, source):
    """API评分（需要有效API密钥）"""
    global _api_key_valid
    if not _api_available or not AI_API_KEY:
        return None
    if _api_key_valid is False:
        return None

    try:
        client = get_ai_client()
        prompt = f"""评分任务：对新闻打0-100分。直接输出JSON，不要解释。

95-100历史级 85-94全球重大 70-84行业重大 50-69重要 30-49区域 15-29一般 0-14低

JSON格式：{{"total_score":分数,"impact":影响力分,"authority":权威性分,"timeliness":时效分,"hotness":热度分,"interest_match":兴趣匹配分,"novelty":新颖分,"emergency":突发分,"credibility":可信度分,"direction":"政治/经济/科技/军事/社会/文化/突发/财经","summary":"摘要20字内"}}

新闻：{title[:150]}
来源：{source}"""

        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,  # 推理模型需要大量token用于思考
            temperature=0.2,
        )
        msg = response.choices[0].message
        # MiMo推理模型：优先用content，如果为空则用reasoning_content
        text = (msg.content or '').strip()
        if not text and hasattr(msg, 'reasoning_content') and msg.reasoning_content:
            text = msg.reasoning_content.strip()

        # 提取JSON
        result = _extract_json(text)
        if result:
            for key in ['total_score', 'impact', 'authority', 'timeliness', 'hotness',
                         'interest_match', 'novelty', 'emergency', 'credibility']:
                if key in result:
                    try:
                        result[key] = max(0, min(100, int(float(result[key]))))
                    except (ValueError, TypeError):
                        result[key] = 50
            return result
        else:
            logger.warning(f"API返回JSON提取失败: {text[:200]}")
    except Exception as e:
        err_str = str(e)
        if '401' in err_str or 'Invalid token' in err_str or 'Unauthorized' in err_str:
            _api_key_valid = False
            logger.warning("API密钥无效，后续将仅使用规则评分")
        else:
            logger.debug(f"API评分失败: {e}")
    return None


def _apply_interest_weights(scores):
    """根据用户配置的兴趣权重调整总分"""
    try:
        from database.db import get_config
        import json as _json
        weights_raw = get_config('interest_weights')
        if not weights_raw:
            return scores
        weights = _json.loads(weights_raw)
        if not isinstance(weights, dict):
            return scores

        direction = scores.get('direction', '')
        # 配置直接使用中文key，无需映射
        if direction and direction in weights:
            w = float(weights[direction])
            # 权重范围0.5-2.0，对总分做调整
            factor = 0.5 + (w / 100.0) * 1.5  # 0→0.5, 100→2.0
            adjusted = int(scores['total_score'] * factor)
            scores['total_score'] = max(20, min(95, adjusted))
    except Exception:
        pass
    return scores


def score_single_news(title, content, source):
    """评分入口：先尝试API，失败则用规则"""
    result = _api_score(title, content, source)
    if result:
        result = _apply_interest_weights(result)
        result['_method'] = 'api'
        return result

    result = _rule_based_score(title, content, source)
    result = _apply_interest_weights(result)
    result['_method'] = 'rule'
    return result


def batch_score(limit=30):
    """批量为未评分的新闻打分（并行）"""
    unscored = get_unscored_news(limit=limit)
    if not unscored:
        logger.info("没有待评分的新闻")
        return 0

    from concurrent.futures import ThreadPoolExecutor, as_completed

    scored_count = 0

    def _score_one(news):
        result = score_single_news(news['title'], news.get('content', ''), news.get('source', ''))
        if result:
            method = result.pop('_method', 'unknown')
            update_score(news['id'], result)
            return {'id': news['id'], 'score': result.get('total_score'), 'method': method, 'title': news['title'][:30]}
        return None

    # 规则评分用高并发，API评分用低并发
    has_api = _api_available and _api_key_valid is not False
    max_workers = 4 if has_api else 8

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_score_one, n): n for n in unscored}
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    scored_count += 1
                    if scored_count % 10 == 0:
                        logger.info(f"[{result['method']}] 已评分 {scored_count} 条 (最新: [{result['score']}分] {result['title']})")
            except Exception as e:
                logger.error(f"评分异常: {e}")

    logger.info(f"批量评分完成，成功 {scored_count}/{len(unscored)} 条")
    return scored_count
