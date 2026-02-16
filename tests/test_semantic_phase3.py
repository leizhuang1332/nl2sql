import pytest
from src.semantic.context_aware_mapper import ContextAwareMapper
from src.semantic.semantic_mapper import SemanticMapper


def test_context_aware_mapper_init():
    mapper = ContextAwareMapper()
    assert mapper is not None
    assert mapper.field_contexts == {}


def test_context_aware_mapper_with_semantic_mapper():
    semantic_mapper = SemanticMapper()
    mapper = ContextAwareMapper(semantic_mapper=semantic_mapper)
    assert mapper.mapper is semantic_mapper


def test_add_context():
    mapper = ContextAwareMapper()
    mapper.add_context("sales.amount", ["销售额", "收入"], priority=1)
    assert "sales.amount" in mapper.field_contexts
    assert "销售额" in mapper.field_contexts["sales.amount"]["keywords"]


def test_add_context_multiple_keywords():
    mapper = ContextAwareMapper()
    mapper.add_context("sales.amount", ["销售额", "收入", "营业额"], priority=1)
    keywords = mapper.field_contexts["sales.amount"]["keywords"]
    assert len(keywords) == 3


def test_remove_context():
    mapper = ContextAwareMapper()
    mapper.add_context("sales.amount", ["销售额"], priority=1)
    mapper.remove_context("sales.amount")
    assert "sales.amount" not in mapper.field_contexts


def test_resolve_ambiguous_field_single_candidate():
    mapper = ContextAwareMapper()
    mapper.add_context("sales.amount", ["销售额"], priority=1)

    result = mapper.resolve_ambiguous_field("销售额", "查询月销售额")
    assert result == "sales.amount"


def test_resolve_ambiguous_field_multiple_candidates():
    mapper = ContextAwareMapper()
    mapper.add_context("sales.amount", ["销售额"], priority=1)
    mapper.add_context("orders.amount", ["订单金额"], priority=2)

    result = mapper.resolve_ambiguous_field("订单金额", "查询订单金额")
    assert result == "orders.amount"


def test_resolve_ambiguous_field_no_match():
    mapper = ContextAwareMapper()
    mapper.add_context("sales.amount", ["销售额"], priority=1)

    result = mapper.resolve_ambiguous_field("不存在的术语", "查询不存在的")
    assert result is None


def test_calculate_context_score():
    mapper = ContextAwareMapper()
    mapper.add_context("sales.amount", ["销售额", "收入"], priority=1)
    score = mapper._calculate_context_score("sales.amount", "查询销售额数据")
    assert score > 0


def test_calculate_context_score_no_field():
    mapper = ContextAwareMapper()
    score = mapper._calculate_context_score("不存在的字段", "查询")
    assert score == 0


def test_get_candidates():
    mapper = ContextAwareMapper()
    mapper.add_context("sales.amount", ["销售额", "收入"])
    mapper.add_context("orders.amount", ["订单金额"])

    candidates = mapper.get_candidates("销售额")
    assert "sales.amount" in candidates


def test_get_all_fields():
    mapper = ContextAwareMapper()
    mapper.add_context("sales.amount", ["销售额"])
    mapper.add_context("orders.amount", ["订单金额"])

    fields = mapper.get_all_fields()
    assert len(fields) == 2
    assert "sales.amount" in fields
    assert "orders.amount" in fields


def test_get_field_keywords():
    mapper = ContextAwareMapper()
    mapper.add_context("sales.amount", ["销售额", "收入"])

    keywords = mapper.get_field_keywords("sales.amount")
    assert "销售额" in keywords
    assert "收入" in keywords


def test_get_field_keywords_not_found():
    mapper = ContextAwareMapper()
    keywords = mapper.get_field_keywords("不存在的字段")
    assert keywords == []


def test_priority_impact():
    mapper = ContextAwareMapper()
    mapper.add_context("sales.amount", ["销售额"], priority=1)
    mapper.add_context("orders.amount", ["订单金额"], priority=5)

    result = mapper.resolve_ambiguous_field("订单金额", "订单金额查询")
    assert result == "orders.amount"
