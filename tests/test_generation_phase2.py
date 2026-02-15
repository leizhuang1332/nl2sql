import pytest
import json
import tempfile
import os
from src.generation.few_shot_manager import FewShotManager
from src.generation import prompts


def test_few_shot_manager_init():
    manager = FewShotManager()
    assert manager.get_example_count() == 0


def test_few_shot_manager_add_example():
    manager = FewShotManager()
    manager.add_example("查询所有用户", "SELECT * FROM users")
    assert manager.get_example_count() == 1


def test_few_shot_manager_get_prompt_with_examples():
    manager = FewShotManager()
    manager.add_example("查询所有用户", "SELECT * FROM users")
    manager.add_example("查询年龄大于18的用户", "SELECT * FROM users WHERE age > 18")

    prompt = manager.get_prompt_with_examples(
        schema="users(id, name, age)",
        question="查询年龄小于25的用户",
        example_count=2
    )

    assert "SELECT * FROM users" in prompt
    assert "SELECT * FROM users WHERE age > 18" in prompt
    assert "查询年龄小于25的用户" in prompt


def test_few_shot_manager_example_count_limit():
    manager = FewShotManager()
    for i in range(5):
        manager.add_example(f"问题{i}", f"SELECT {i}")

    prompt = manager.get_prompt_with_examples(
        schema="users(id)",
        question="测试",
        example_count=3
    )

    assert manager.get_example_count() == 5
    assert "SELECT 2" in prompt
    assert "SELECT 3" in prompt
    assert "SELECT 4" in prompt


def test_few_shot_manager_clear_examples():
    manager = FewShotManager()
    manager.add_example("查询所有用户", "SELECT * FROM users")
    manager.clear_examples()
    assert manager.get_example_count() == 0


def test_few_shot_manager_save_load_examples():
    manager = FewShotManager()
    manager.add_example("查询所有用户", "SELECT * FROM users")
    manager.add_example("查询年龄大于18的用户", "SELECT * FROM users WHERE age > 18")

    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)

    try:
        manager.save_examples_to_file(path)

        new_manager = FewShotManager()
        new_manager.load_examples_from_file(path)

        assert new_manager.get_example_count() == 2
        assert new_manager.examples[0]["question"] == "查询所有用户"
        assert new_manager.examples[1]["sql"] == "SELECT * FROM users WHERE age > 18"
    finally:
        os.unlink(path)


def test_prompts_basic_template():
    result = prompts.BASIC_TEMPLATE.format(
        schema="users(id, name)",
        question="查询所有用户"
    )
    assert "users(id, name)" in result
    assert "查询所有用户" in result


def test_prompts_detailed_template():
    result = prompts.DETAILED_TEMPLATE.format(
        schema="users(id, name, age)",
        question="查询年龄大于18的用户"
    )
    assert "SQL 专家" in result
    assert "users(id, name, age)" in result


def test_prompts_context_template():
    result = prompts.CONTEXT_TEMPLATE.format(
        schema="users(id, name)",
        context="之前查询过用户列表",
        question="查询年龄大于18的用户"
    )
    assert "之前对话" in result
    assert "之前查询过用户列表" in result


def test_prompts_complex_template():
    result = prompts.COMPLEX_TEMPLATE.format(
        schema="users(id, name, age)",
        question_type="聚合查询",
        question="统计每个年龄段的用户数量",
        additional_instructions="使用 GROUP BY"
    )
    assert "问题类型" in result
    assert "聚合查询" in result
    assert "使用 GROUP BY" in result
