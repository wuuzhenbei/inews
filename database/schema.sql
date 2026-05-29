-- 新闻主表
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    ai_summary TEXT,
    link TEXT UNIQUE,
    source TEXT NOT NULL,
    source_type TEXT,
    author TEXT,
    pub_time DATETIME,
    fetch_time DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- AI评分
    ai_score INTEGER,
    score_impact INTEGER,
    score_authority INTEGER,
    score_timeliness INTEGER,
    score_hotness INTEGER,
    score_interest INTEGER,
    score_novelty INTEGER,
    score_emergency INTEGER,
    score_credibility INTEGER,
    direction TEXT,

    -- 状态
    is_read BOOLEAN DEFAULT 0,
    is_blocked BOOLEAN DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_pub_time ON news(pub_time);
CREATE INDEX IF NOT EXISTS idx_fetch_time ON news(fetch_time);
CREATE INDEX IF NOT EXISTS idx_ai_score ON news(ai_score);
CREATE INDEX IF NOT EXISTS idx_source ON news(source);
CREATE INDEX IF NOT EXISTS idx_source_type ON news(source_type);
CREATE INDEX IF NOT EXISTS idx_direction ON news(direction);

-- 用户配置表
CREATE TABLE IF NOT EXISTS user_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
