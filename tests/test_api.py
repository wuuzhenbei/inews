import pytest
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

@pytest.fixture
def client(tmp_path):
    """创建测试客户端"""
    import database.db as db_module
    original_path = db_module.DB_PATH
    # 设置测试数据库路径
    test_db_path = str(tmp_path / 'test.db')
    db_module.DB_PATH = test_db_path
    db_module.init_db()

    # 重新导入app以使用新的数据库路径
    import importlib
    import app as app_module
    importlib.reload(app_module)

    app_module.app.config['TESTING'] = True
    with app_module.app.test_client() as client:
        yield client

    db_module.DB_PATH = original_path

def test_api_news(client):
    """测试获取新闻列表API"""
    response = client.get('/api/news')
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_api_news_with_params(client):
    """测试带参数的新闻列表API"""
    response = client.get('/api/news?sort=latest&limit=10')
    assert response.status_code == 200

def test_api_news_invalid_params(client):
    """测试无效参数"""
    response = client.get('/api/news?days=abc')
    assert response.status_code == 400

def test_api_statistics(client):
    """测试统计信息API"""
    response = client.get('/api/statistics')
    assert response.status_code == 200
    data = response.json
    assert 'total' in data
    assert 'scored' in data
    assert 'today' in data

def test_api_search(client):
    """测试搜索API"""
    response = client.get('/api/search?q=test')
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_api_search_empty(client):
    """测试空搜索"""
    response = client.get('/api/search')
    assert response.status_code == 200
    assert response.json == []

def test_api_config(client):
    """测试配置API"""
    # 获取配置
    response = client.get('/api/config')
    assert response.status_code == 200

def test_api_config_save(client):
    """测试保存配置"""
    response = client.post('/api/config', json={'theme': 'dark'})
    assert response.status_code == 200
    assert response.json['status'] == 'saved'

def test_api_config_invalid_key(client):
    """测试无效配置key"""
    response = client.post('/api/config', json={'evil_key': 'value'})
    assert response.status_code == 200
    # 验证evil_key没有被保存
    response = client.get('/api/config')
    assert 'evil_key' not in response.json

def test_api_news_not_found(client):
    """测试不存在的新闻"""
    response = client.get('/api/news/99999/summary')
    assert response.status_code == 404
