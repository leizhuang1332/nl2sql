import pytest
from src.explanation import prompts


class TestPromptTemplates:
    def test_concise_explain_prompt(self):
        prompt = prompts.get_concise_prompt("有多少用户", "[{'count': 100}]")
        assert "有多少用户" in prompt
        assert "count" in prompt

    def test_detailed_explain_prompt(self):
        prompt = prompts.get_detailed_prompt("用户分析", "[{'name': 'John'}]")
        assert "用户分析" in prompt
        assert "John" in prompt

    def test_comparison_prompt(self):
        current = "[{'amount': 150}]"
        previous = "[{'amount': 100}]"
        prompt = prompts.get_comparison_prompt(current, previous, "增长了多少")
        assert "150" in prompt
        assert "100" in prompt
        assert "增长了多少" in prompt

    def test_summary_prompt(self):
        result = "[{'name': 'John'}]"
        prompt = prompts.get_summary_prompt(result, max_points=5)
        assert "John" in prompt
        assert "5" in prompt

    def test_trend_prompt(self):
        prompt = prompts.get_trend_prompt("趋势如何", "[{'date': '2024-01', 'value': 100}]")
        assert "趋势如何" in prompt
        assert "100" in prompt

    def test_concise_prompt_contains_requirements(self):
        prompt = prompts.CONCISE_EXPLAIN_PROMPT
        assert "一句话回答" in prompt
        assert "关键数字" in prompt

    def test_detailed_prompt_contains_requirements(self):
        prompt = prompts.DETAILED_EXPLAIN_PROMPT
        assert "数据概况" in prompt
        assert "关键发现" in prompt

    def test_comparison_prompt_contains_requirements(self):
        prompt = prompts.COMPARISON_PROMPT
        assert "变化幅度" in prompt
        assert "增长/下降趋势" in prompt

    def test_summary_prompt_contains_requirements(self):
        prompt = prompts.SUMMARY_PROMPT
        assert "总数" in prompt
        assert "关键指标" in prompt

    def test_trend_prompt_contains_requirements(self):
        prompt = prompts.TREND_ANALYSIS_PROMPT
        assert "整体趋势" in prompt
        assert "峰值和谷值" in prompt

    def test_prompt_format_variables(self):
        prompt = prompts.get_summary_prompt("test", 3)
        assert "max_points" not in prompt
        assert "3" in prompt
