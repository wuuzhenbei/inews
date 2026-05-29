import pytest
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from processors.scorer import _rule_based_score, _extract_json

def test_rule_based_score_basic():
    """测试基本规则评分"""
    result = _rule_based_score(
        title="普通新闻标题",
        content="这是一条普通新闻的内容",
        source="测试来源"
    )
    assert 'total_score' in result
    assert 20 <= result['total_score'] <= 95
    assert 'direction' in result

def test_rule_based_score_breaking():
    """测试突发新闻评分"""
    result = _rule_based_score(
        title="突发：重大事件发生",
        content="紧急消息",
        source="BBC"
    )
    assert result['emergency'] >= 70
    assert result['total_score'] >= 50

def test_rule_based_score_finance():
    """测试财经新闻评分"""
    result = _rule_based_score(
        title="美联储宣布加息25个基点",
        content="利率上升影响股市",
        source="Bloomberg"
    )
    assert result['direction'] in ['财经', '经济']
    assert result['total_score'] >= 40

def test_extract_json():
    """测试JSON提取"""
    # 直接JSON
    result = _extract_json('{"total_score": 85}')
    assert result == {"total_score": 85}

    # 代码块中的JSON
    result = _extract_json('```json\n{"total_score": 90}\n```')
    assert result == {"total_score": 90}

    # 无效输入
    result = _extract_json('这不是JSON')
    assert result is None
