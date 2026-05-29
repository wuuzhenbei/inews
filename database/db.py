import sqlite3
import os
from contextlib import contextmanager
from config import DB_PATH
from utils.text import safe_truncate

@contextmanager
def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with get_conn() as conn:
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        # 迁移：添加ai_summary列
        try:
            conn.execute("ALTER TABLE news ADD COLUMN ai_summary TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass
        # 迁移：添加fetch_time索引
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_fetch_time ON news(fetch_time)")
            conn.commit()
        except sqlite3.OperationalError:
            pass
        # 迁移：添加收藏列
        try:
            conn.execute("ALTER TABLE news ADD COLUMN is_bookmarked BOOLEAN DEFAULT 0")
            conn.commit()
        except sqlite3.OperationalError:
            pass

def insert_news(title, content, link, source, source_type, author=None, pub_time=None):
    """插入一条新闻，返回 (id, is_new)。link去重。使用INSERT OR IGNORE避免竞态条件。"""
    with get_conn() as conn:
        # 先查是否已存在（快路径，避免不必要的INSERT）
        cursor = conn.execute("SELECT id FROM news WHERE link = ?", (link,))
        existing = cursor.fetchone()
        if existing:
            return existing['id'], False

        # INSERT OR IGNORE处理并发插入的竞态条件
        cursor = conn.execute("""
            INSERT OR IGNORE INTO news (title, content, link, source, source_type, author, pub_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title, safe_truncate(content), link, source, source_type, author, pub_time))
        conn.commit()
        if cursor.rowcount > 0:
            return cursor.lastrowid, True
        # 并发插入了相同link，重新查询返回已有记录
        cursor = conn.execute("SELECT id FROM news WHERE link = ?", (link,))
        existing = cursor.fetchone()
        return (existing['id'], False) if existing else (None, False)

def get_unscored_news(limit=50):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, content, source, direction FROM news WHERE ai_score IS NULL AND is_blocked = 0 ORDER BY fetch_time DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

def update_score(news_id, scores):
    with get_conn() as conn:
        conn.execute("""
            UPDATE news SET
                ai_score=?, score_impact=?, score_authority=?,
                score_timeliness=?, score_hotness=?, score_interest=?,
                score_novelty=?, score_emergency=?, score_credibility=?,
                direction=?, summary=?
            WHERE id=?
        """, (
            scores.get('total_score'), scores.get('impact'), scores.get('authority'),
            scores.get('timeliness'), scores.get('hotness'), scores.get('interest_match'),
            scores.get('novelty'), scores.get('emergency'), scores.get('credibility'),
            scores.get('direction'), scores.get('summary'), news_id
        ))
        conn.commit()

def get_news_list(sort='score', source_type=None, keyword=None, days=None, limit=200, offset=0, direction=None, author=None):
    with get_conn() as conn:
        query = "SELECT * FROM news WHERE is_blocked = 0"
        params = []

        # 屏蔽关键词过滤
        blocked_raw = get_config('blocked_keywords')
        if blocked_raw:
            try:
                import json as _json
                blocked = _json.loads(blocked_raw)
                if isinstance(blocked, list) and blocked:
                    for bk in blocked:
                        if bk and bk.strip():
                            query += " AND title NOT LIKE ? AND content NOT LIKE ?"
                            params.extend([f'%{bk.strip()}%', f'%{bk.strip()}%'])
            except (ValueError, TypeError):
                pass

        if source_type and source_type != 'all':
            query += " AND source_type = ?"
            params.append(source_type)

        if direction and direction != 'all':
            query += " AND direction = ?"
            params.append(direction)

        if author and author != 'all':
            query += " AND author = ?"
            params.append(author)

        if keyword:
            query += " AND (title LIKE ? OR content LIKE ?)"
            params.extend([f'%{keyword}%', f'%{keyword}%'])

        if days is not None:
            if days == 0:
                query += " AND date(COALESCE(pub_time, fetch_time)) = date('now', 'localtime')"
            else:
                query += " AND date(COALESCE(pub_time, fetch_time)) >= date('now', 'localtime', ?)"
                params.append(f'-{days} days')

        if sort == 'score':
            query += " ORDER BY ai_score DESC NULLS LAST, pub_time DESC"
        else:
            query += " ORDER BY pub_time DESC"

        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

def get_statistics():
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM news").fetchone()[0]
        scored = conn.execute("SELECT COUNT(*) FROM news WHERE ai_score IS NOT NULL").fetchone()[0]
        today_count = conn.execute("SELECT COUNT(*) FROM news WHERE date(fetch_time) = date('now', 'localtime')").fetchone()[0]
        last = conn.execute("SELECT MAX(fetch_time) FROM news").fetchone()[0]
        return {'total': total, 'scored': scored, 'today': today_count, 'last_update': last}

def mark_read(news_id):
    with get_conn() as conn:
        conn.execute("UPDATE news SET is_read = 1 WHERE id = ?", (news_id,))
        conn.commit()

def get_config(key=None):
    with get_conn() as conn:
        if key:
            row = conn.execute("SELECT value FROM user_config WHERE key = ?", (key,)).fetchone()
            return row['value'] if row else None
        rows = conn.execute("SELECT key, value FROM user_config").fetchall()
        return {r['key']: r['value'] for r in rows}

def save_config(key, value):
    with get_conn() as conn:
        conn.execute("INSERT OR REPLACE INTO user_config (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

def search_news(keyword, limit=50):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM news WHERE (title LIKE ? OR content LIKE ?) AND is_blocked = 0 ORDER BY ai_score DESC NULLS LAST LIMIT ?",
            (f'%{keyword}%', f'%{keyword}%', limit)
        ).fetchall()
        return [dict(r) for r in rows]

def save_ai_summary(news_id, summary_text):
    with get_conn() as conn:
        conn.execute("UPDATE news SET ai_summary = ? WHERE id = ?", (summary_text, news_id))
        conn.commit()

def get_ai_summary(news_id):
    with get_conn() as conn:
        row = conn.execute("SELECT ai_summary FROM news WHERE id = ?", (news_id,)).fetchone()
        return row['ai_summary'] if row else None

def get_unsummarized_news(limit=50):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, content, source_type, direction FROM news WHERE ai_summary IS NULL AND is_blocked = 0 ORDER BY ai_score DESC NULLS LAST LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

def get_all_news_context(limit=200):
    """获取新闻摘要用于RAG上下文"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, source, source_type, direction, ai_score, ai_summary, pub_time FROM news WHERE is_blocked = 0 ORDER BY ai_score DESC NULLS LAST LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

def get_news_by_keyword(keywords, limit=30):
    """根据关键词搜索相关新闻（用于RAG优化）"""
    with get_conn() as conn:
        conditions = ' OR '.join(['title LIKE ?' for _ in keywords])
        params = [f'%{k}%' for k in keywords]
        params.append(limit)
        rows = conn.execute(
            f"SELECT id, title, source, source_type, direction, ai_score, ai_summary, pub_time FROM news WHERE is_blocked = 0 AND ({conditions}) ORDER BY ai_score DESC NULLS LAST LIMIT ?",
            params
        ).fetchall()
        return [dict(r) for r in rows]

def cleanup_old_news(days=30):
    """清理超过N天的旧新闻（不删除收藏的），优先用pub_time"""
    with get_conn() as conn:
        cursor = conn.execute(
            "DELETE FROM news WHERE COALESCE(pub_time, fetch_time) < datetime('now', ?) AND is_bookmarked = 0",
            (f'-{days} days',)
        )
        conn.commit()
        return cursor.rowcount

def toggle_bookmark(news_id):
    """切换收藏状态，返回新状态"""
    with get_conn() as conn:
        row = conn.execute("SELECT is_bookmarked FROM news WHERE id = ?", (news_id,)).fetchone()
        if not row:
            return None
        new_val = 0 if row['is_bookmarked'] else 1
        conn.execute("UPDATE news SET is_bookmarked = ? WHERE id = ?", (new_val, news_id))
        conn.commit()
        return new_val

def get_bookmarked_news(limit=100):
    """获取收藏的新闻"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM news WHERE is_bookmarked = 1 ORDER BY pub_time DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
