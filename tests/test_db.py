import pytest
import os
import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

@pytest.fixture
def setup_db(tmp_path):
    """使用临时数据库进行测试"""
    import database.db as db_module
    original_path = db_module.DB_PATH
    db_module.DB_PATH = str(tmp_path / 'test.db')
    db_module.init_db()
    yield
    db_module.DB_PATH = original_path

def test_insert_news(setup_db):
    """测试插入新闻"""
    from database.db import insert_news
    # 使用时间戳确保链接唯一
    unique_link = f"https://example.com/test_{int(time.time() * 1000)}"
    news_id, is_new = insert_news(
        title="测试新闻标题",
        content="测试新闻内容",
        link=unique_link,
        source="测试来源",
        source_type="media"
    )
    assert news_id > 0
    assert is_new == True

def test_insert_duplicate_news(setup_db):
    """测试插入重复新闻"""
    from database.db import insert_news
    # 第一次插入
    insert_news(
        title="测试新闻",
        content="内容",
        link="https://example.com/dup",
        source="来源",
        source_type="media"
    )
    # 第二次插入相同链接
    news_id, is_new = insert_news(
        title="测试新闻2",
        content="内容2",
        link="https://example.com/dup",
        source="来源",
        source_type="media"
    )
    assert is_new == False

def test_get_news_list(setup_db):
    """测试获取新闻列表"""
    from database.db import insert_news, get_news_list
    # 插入测试数据
    for i in range(3):
        insert_news(
            title=f"新闻{i}",
            content=f"内容{i}",
            link=f"https://example.com/list{i}",
            source="来源",
            source_type="media"
        )
    # 获取列表
    news = get_news_list(limit=10)
    assert len(news) > 0

def test_get_statistics(setup_db):
    """测试获取统计信息"""
    from database.db import get_statistics
    stats = get_statistics()
    assert 'total' in stats
    assert 'scored' in stats
    assert 'today' in stats

def test_cleanup_old_news(setup_db):
    """测试清理旧新闻"""
    from database.db import insert_news, cleanup_old_news, get_conn
    # 插入一条新闻
    insert_news(
        title="旧新闻",
        content="内容",
        link="https://example.com/old",
        source="来源",
        source_type="media"
    )
    # 手动修改fetch_time为30天前
    with get_conn() as conn:
        conn.execute("UPDATE news SET fetch_time = datetime('now', '-31 days') WHERE link = ?",
                     ("https://example.com/old",))
        conn.commit()
    # 清理
    deleted = cleanup_old_news(days=30)
    assert deleted >= 1
