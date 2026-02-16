import pytest
import os
import tempfile
from src.semantic.semantic_mapper import SemanticMapper
from src.semantic.time_parser import TimeParser
from src.semantic.config_manager import SemanticConfigManager


def test_semantic_mapper_init():
    mapper = SemanticMapper()
    assert mapper is not None
    assert len(mapper.time_mappings) > 0
    assert len(mapper.sort_mappings) > 0


def test_add_field_mapping():
    mapper = SemanticMapper()
    mapper.add_field_mapping("销售额", ["sales.amount"])
    assert "销售额" in mapper.field_mappings
    assert mapper.field_mappings["销售额"] == ["sales.amount"]


def test_add_time_mapping():
    mapper = SemanticMapper()
    mapper.add_time_mapping("今天", "DATE('now')")
    assert mapper.time_mappings["今天"] == "DATE('now')"


def test_add_sort_mapping():
    mapper = SemanticMapper()
    mapper.add_sort_mapping("top10", {"type": "limit", "count": 10, "order": "DESC"})
    assert "top10" in mapper.sort_mappings


def test_map_question():
    mapper = SemanticMapper()
    mapper.add_field_mapping("销售额", ["sales.amount"])
    result, info = mapper.map("查询销售额")
    assert "销售额" in result
    assert len(info["field_mappings"]) > 0


def test_map_question_with_time():
    mapper = SemanticMapper()
    result, info = mapper.map("查询今天的销售额")
    assert "今天" in result
    assert len(info["time_mappings"]) > 0


def test_map_question_with_sort():
    mapper = SemanticMapper()
    result, info = mapper.map("查询销售额前三")
    assert len(info["sort_mappings"]) > 0


def test_get_field_mapping():
    mapper = SemanticMapper()
    mapper.add_field_mapping("销售额", ["sales.amount"])
    fields = mapper.get_field_mapping("销售额")
    assert fields == ["sales.amount"]


def test_get_field_mapping_not_found():
    mapper = SemanticMapper()
    fields = mapper.get_field_mapping("不存在的术语")
    assert fields == []


def test_get_time_mapping():
    mapper = SemanticMapper()
    sql = mapper.get_time_mapping("今天")
    assert sql == "DATE('now')"


def test_get_time_mapping_not_found():
    mapper = SemanticMapper()
    sql = mapper.get_time_mapping("不存在的表达式")
    assert sql == ""


def test_time_parser_init():
    parser = TimeParser()
    assert parser is not None


def test_time_parser_parse():
    parser = TimeParser()
    result = parser.parse("今天")
    assert result is not None
    assert result == ("DATE('now')", "DATE('now')")


def test_time_parser_parse_yesterday():
    parser = TimeParser()
    result = parser.parse("昨天")
    assert result == ("DATE('now', '-1 day')", "DATE('now', '-1 day')")


def test_time_parser_parse_not_found():
    parser = TimeParser()
    result = parser.parse("不存在的表达式")
    assert result is None


def test_time_parser_parse_range():
    parser = TimeParser()
    result = parser.parse_range("今天")
    assert result is not None
    assert "start" in result
    assert "end" in result


def test_config_manager_init():
    manager = SemanticConfigManager()
    assert manager is not None
    assert manager.config == {}


def test_config_manager_add_field_mapping():
    manager = SemanticConfigManager()
    manager.add_field_mapping("销售额", ["sales.amount"])
    assert "销售额" in manager.config["field_mappings"]


def test_config_manager_add_time_mapping():
    manager = SemanticConfigManager()
    manager.add_time_mapping("今天", "DATE('now')")
    assert "今天" in manager.config["time_mappings"]


def test_config_manager_to_dict():
    manager = SemanticConfigManager()
    manager.add_field_mapping("销售额", ["sales.amount"])
    d = manager.to_dict()
    assert "field_mappings" in d


def test_config_manager_load_save():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)

    try:
        manager = SemanticConfigManager()
        manager.add_field_mapping("销售额", ["sales.amount"])
        manager.save_config(path)

        new_manager = SemanticConfigManager()
        new_manager.load_config(path)

        assert "销售额" in new_manager.config["field_mappings"]
    finally:
        os.unlink(path)
