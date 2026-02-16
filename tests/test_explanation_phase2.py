import pytest
from src.explanation.summarizer import ResultSummarizer
from src.explanation.comparator import ComparisonAnalyzer


class TestResultSummarizer:
    def test_summarizer_init(self):
        summarizer = ResultSummarizer()
        assert summarizer is not None

    def test_summarize_empty(self):
        summarizer = ResultSummarizer()
        result = summarizer.summarize([])
        assert "空" in result

    def test_summarize_single_row(self):
        summarizer = ResultSummarizer()
        result = [{"name": "John", "age": 30}]
        summary = summarizer.summarize(result)
        assert "1" in summary or "条数据" in summary

    def test_summarize_multiple_rows(self):
        summarizer = ResultSummarizer()
        result = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25}
        ]
        summary = summarizer.summarize(result)
        assert "2" in summary or "条数据" in summary

    def test_summarize_with_numeric(self):
        summarizer = ResultSummarizer()
        result = [
            {"amount": 100},
            {"amount": 200},
            {"amount": 300}
        ]
        summary = summarizer.summarize(result)
        assert "600" in summary or "总计" in summary

    def test_summarize_max_points(self):
        summarizer = ResultSummarizer()
        result = [
            {"name": "A"},
            {"name": "B"},
            {"name": "C"},
            {"name": "D"},
            {"name": "E"}
        ]
        summary = summarizer.summarize(result, max_points=3)
        lines = summary.split("\n")
        key_data_lines = [l for l in lines if "关键数据" in l or (l.startswith("1.") or l.startswith("2.") or l.startswith("3."))]
        assert len(key_data_lines) <= 4

    def test_get_summary_dict(self):
        summarizer = ResultSummarizer()
        result = [{"name": "John", "amount": 100}]
        summary_dict = summarizer.get_summary_dict(result)
        assert "row_count" in summary_dict
        assert summary_dict["row_count"] == 1


class TestComparisonAnalyzer:
    def test_comparator_init(self):
        comparator = ComparisonAnalyzer()
        assert comparator is not None

    def test_compare_both_empty(self):
        comparator = ComparisonAnalyzer()
        result = comparator.compare([], [], "对比")
        assert "不足" in result

    def test_compare_current_empty(self):
        comparator = ComparisonAnalyzer()
        result = comparator.compare([], [{"amount": 100}], "对比")
        assert "不足" in result

    def test_compare_previous_empty(self):
        comparator = ComparisonAnalyzer()
        result = comparator.compare([{"amount": 100}], [], "对比")
        assert "不足" in result

    def test_compare_equal_data(self):
        comparator = ComparisonAnalyzer()
        current = [{"amount": 100}, {"amount": 200}]
        previous = [{"amount": 100}, {"amount": 200}]
        result = comparator.compare(current, previous, "对比")
        assert "当前数据" in result
        assert "上期数据" in result

    def test_compare_with_growth(self):
        comparator = ComparisonAnalyzer()
        current = [{"amount": 150}, {"amount": 150}]
        previous = [{"amount": 100}, {"amount": 100}]
        result = comparator.compare(current, previous, "对比")
        assert "↑" in result or "up" in result.lower()

    def test_compare_with_decline(self):
        comparator = ComparisonAnalyzer()
        current = [{"amount": 80}, {"amount": 80}]
        previous = [{"amount": 100}, {"amount": 100}]
        result = comparator.compare(current, previous, "对比")
        assert "↓" in result or "down" in result.lower()

    def test_get_comparison_dict(self):
        comparator = ComparisonAnalyzer()
        current = [{"amount": 150}, {"amount": 150}]
        previous = [{"amount": 100}, {"amount": 100}]
        comparison = comparator.get_comparison_dict(current, previous)
        assert "current_count" in comparison
        assert "previous_count" in comparison
        assert comparison["current_count"] == 2

    def test_get_comparison_dict_insufficient(self):
        comparator = ComparisonAnalyzer()
        comparison = comparator.get_comparison_dict([], [])
        assert "error" in comparison
