import pytest
import json
from src.explanation.result_explainer import ResultExplainer
from src.explanation.data_analyst import DataAnalyst
from src.explanation.formatters import ResultFormatter


class TestResultExplainer:
    def test_result_explainer_init(self):
        explainer = ResultExplainer()
        assert explainer is not None

    def test_result_explainer_with_llm(self):
        explainer = ResultExplainer(llm="mock_llm")
        assert explainer.llm == "mock_llm"

    def test_explain_list_result(self):
        explainer = ResultExplainer()
        result = [{"name": "John", "age": 30}]
        response = explainer.explain("查询用户", result)
        assert response is not None

    def test_explain_json_string(self):
        explainer = ResultExplainer()
        result = json.dumps([{"name": "John", "age": 30}])
        parsed = explainer._parse_result(result)
        assert isinstance(parsed, list)
        assert parsed[0]["name"] == "John"

    def test_explain_simple_result_count(self):
        explainer = ResultExplainer()
        result = [{"count": 100}]
        response = explainer.explain("有多少用户", result)
        assert "100" in response

    def test_explain_simple_result_sum(self):
        explainer = ResultExplainer()
        result = [{"total": 5000}]
        response = explainer.explain("总金额是多少", result)
        assert "5000" in response

    def test_explain_simple_result_avg(self):
        explainer = ResultExplainer()
        result = [{"avg": 85.5}]
        response = explainer.explain("平均分是多少", result)
        assert "85.5" in response

    def test_explain_complex_result(self):
        explainer = ResultExplainer()
        result = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25}
        ]
        response = explainer.explain("查询用户", result)
        assert response is not None

    def test_explain_empty_result(self):
        explainer = ResultExplainer()
        result = []
        response = explainer.explain("查询", result)
        assert "空" in response

    def test_fallback_explain(self):
        explainer = ResultExplainer()
        result = [{"name": "John", "age": 30}]
        response = explainer._fallback_explain(result)
        assert "John" in response
        assert "30" in response


class TestDataAnalyst:
    def test_data_analyst_init(self):
        analyst = DataAnalyst()
        assert analyst is not None

    def test_analyze_empty(self):
        analyst = DataAnalyst()
        result = analyst.analyze([])
        assert "error" in result

    def test_analyze_single_row(self):
        analyst = DataAnalyst()
        result = [{"name": "John", "age": 30}]
        analysis = analyst.analyze(result)
        assert analysis["row_count"] == 1
        assert analysis["column_count"] == 2

    def test_analyze_numeric_columns(self):
        analyst = DataAnalyst()
        result = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25}
        ]
        analysis = analyst.analyze(result)
        assert "numeric_analysis" in analysis
        assert "age" in analysis["numeric_analysis"]

    def test_analyze_numeric_stats(self):
        analyst = DataAnalyst()
        result = [
            {"value": 10},
            {"value": 20},
            {"value": 30}
        ]
        analysis = analyst.analyze(result)
        assert analysis["numeric_analysis"]["value"]["sum"] == 60
        assert analysis["numeric_analysis"]["value"]["avg"] == 20
        assert analysis["numeric_analysis"]["value"]["min"] == 10
        assert analysis["numeric_analysis"]["value"]["max"] == 30

    def test_calculate_trend(self):
        analyst = DataAnalyst()
        current = [{"amount": 100}, {"amount": 200}]
        previous = [{"amount": 80}, {"amount": 120}]
        trend = analyst.calculate_trend(current, previous, "amount")
        assert "current" in trend
        assert "previous" in trend
        assert "change" in trend
        assert "trend" in trend

    def test_calculate_trend_insufficient_data(self):
        analyst = DataAnalyst()
        current = [{"amount": 100}]
        previous = []
        trend = analyst.calculate_trend(current, previous, "amount")
        assert "error" in trend

    def test_get_column_stats_numeric(self):
        analyst = DataAnalyst()
        result = [{"value": 10}, {"value": 20}, {"value": 30}]
        stats = analyst.get_column_stats(result, "value")
        assert stats["sum"] == 60
        assert stats["avg"] == 20

    def test_get_column_stats_string(self):
        analyst = DataAnalyst()
        result = [{"name": "John"}, {"name": "Jane"}, {"name": "John"}]
        stats = analyst.get_column_stats(result, "name")
        assert stats["unique_count"] == 2


class TestResultFormatter:
    def test_result_formatter_init(self):
        formatter = ResultFormatter()
        assert formatter is not None

    def test_format_number_default(self):
        result = ResultFormatter.format_number(1234.56)
        assert result == "1234.56"

    def test_format_number_integer(self):
        result = ResultFormatter.format_number(100)
        assert result == "100"

    def test_format_number_currency(self):
        result = ResultFormatter.format_number(1234.5, "currency")
        assert "¥" in result

    def test_format_number_percentage(self):
        result = ResultFormatter.format_number(85.5, "percentage")
        assert "%" in result

    def test_format_number_compact(self):
        result = ResultFormatter.format_number(15000, "compact")
        assert "万" in result

    def test_format_table(self):
        result = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25}
        ]
        formatted = ResultFormatter.format_table(result)
        assert "John" in formatted
        assert "Jane" in formatted

    def test_format_table_empty(self):
        result = []
        formatted = ResultFormatter.format_table(result)
        assert "无数据" in formatted

    def test_format_json(self):
        result = [{"name": "John", "age": 30}]
        formatted = ResultFormatter.format_json(result)
        assert "John" in formatted

    def test_format_markdown(self):
        result = [{"name": "John", "age": 30}]
        formatted = ResultFormatter.format_markdown(result)
        assert "|" in formatted
        assert "---" in formatted

    def test_format_csv(self):
        result = [{"name": "John", "age": 30}]
        formatted = ResultFormatter.format_csv(result)
        assert "name,age" in formatted
        assert "John,30" in formatted

    def test_format_html(self):
        result = [{"name": "John", "age": 30}]
        formatted = ResultFormatter.format_html(result)
        assert "<table>" in formatted
        assert "<td>John</td>" in formatted

    def test_format_text(self):
        result = [{"name": "John", "age": 30}]
        formatted = ResultFormatter.format_text(result)
        assert "John" in formatted
        assert "age" in formatted
