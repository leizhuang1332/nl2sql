import pytest
from src.explanation.result_explainer import ResultExplainer
from src.explanation.data_analyst import DataAnalyst
from src.explanation.formatters import ResultFormatter
from src.explanation.summarizer import ResultSummarizer
from src.explanation.comparator import ComparisonAnalyzer
from src.explanation import prompts


class TestIntegration:
    def test_full_workflow(self):
        result = [
            {"name": "John", "amount": 100},
            {"name": "Jane", "amount": 200},
            {"name": "Bob", "amount": 150}
        ]
        
        explainer = ResultExplainer()
        analyst = DataAnalyst()
        formatter = ResultFormatter()
        
        explanation = explainer.explain("查询销售数据", result)
        assert explanation is not None
        
        analysis = analyst.analyze(result)
        assert analysis["row_count"] == 3
        assert "amount" in analysis["numeric_analysis"]
        
        formatted = formatter.format_table(result)
        assert "John" in formatted
        
        formatted_json = formatter.format_json(result)
        assert "John" in formatted_json
        
        formatted_md = formatter.format_markdown(result)
        assert "John" in formatted_md

    def test_explainer_with_analyst(self):
        result = [{"count": 100}]
        
        explainer = ResultExplainer()
        explanation = explainer.explain("有多少用户", result)
        
        assert "100" in explanation

    def test_analyst_with_summarizer(self):
        result = [
            {"name": "John", "score": 85},
            {"name": "Jane", "score": 92},
            {"name": "Bob", "score": 78}
        ]
        
        analyst = DataAnalyst()
        summarizer = ResultSummarizer()
        
        analysis = analyst.analyze(result)
        summary = summarizer.summarize(result)
        
        assert "3" in summary
        assert "score" in analysis["numeric_analysis"]

    def test_comparator_with_analyst(self):
        current = [{"amount": 150}, {"amount": 200}]
        previous = [{"amount": 100}, {"amount": 100}]
        
        analyst = DataAnalyst()
        comparator = ComparisonAnalyzer()
        
        trend = analyst.calculate_trend(current, previous, "amount")
        assert trend["trend"] == "up"
        
        comparison = comparator.compare(current, previous, "对比增长")
        assert "当前数据" in comparison

    def test_all_formatters(self):
        result = [
            {"name": "John", "age": 30, "city": "Beijing"},
            {"name": "Jane", "age": 25, "city": "Shanghai"}
        ]
        
        formatter = ResultFormatter()
        
        table = formatter.format_table(result)
        assert "John" in table
        
        json_str = formatter.format_json(result)
        assert "John" in json_str
        
        md = formatter.format_markdown(result)
        assert "John" in md
        
        csv = formatter.format_csv(result)
        assert "name,age,city" in csv
        
        html = formatter.format_html(result)
        assert "<td>John</td>" in html
        
        text = formatter.format_text(result)
        assert "John" in text

    def test_i18n_with_formatters(self):
        result = [{"name": "John"}]
        
        formatter_zh = ResultFormatter(locale="zh")
        formatter_en = ResultFormatter(locale="en")
        
        table_zh = formatter_zh.format_table(result)
        assert "John" in table_zh
        
        table_en = formatter_en.format_table(result)
        assert "John" in table_en

    def test_prompts_with_explainer(self):
        result = [{"name": "John", "amount": 100}]
        
        explainer = ResultExplainer()
        
        concise_prompt = prompts.get_concise_prompt("有多少", str(result))
        detailed_prompt = prompts.get_detailed_prompt("分析", str(result))
        
        assert "有多少" in concise_prompt
        assert "分析" in detailed_prompt
        
        response = explainer.explain("有多少", result)
        assert response is not None


class TestE2E:
    def test_complete_nl2sql_flow(self):
        query_result = [
            {"product": "iPhone", "sales": 1000, "revenue": 999000},
            {"product": "Android", "sales": 1500, "revenue": 750000},
            {"product": "Windows", "sales": 800, "revenue": 640000}
        ]
        
        explainer = ResultExplainer()
        analyst = DataAnalyst()
        summarizer = ResultSummarizer()
        comparator = ComparisonAnalyzer()
        formatter = ResultFormatter()
        
        nl_response = explainer.explain("销售情况如何", query_result)
        assert nl_response is not None
        
        analysis = analyst.analyze(query_result)
        assert analysis["row_count"] == 3
        
        summary = summarizer.summarize(query_result)
        assert "3" in summary
        
        table_output = formatter.format_table(query_result)
        assert "iPhone" in table_output
        
        json_output = formatter.format_json(query_result)
        assert "iPhone" in json_output

    def test_comparison_workflow(self):
        last_month = [
            {"product": "A", "sales": 100},
            {"product": "B", "sales": 200}
        ]
        
        this_month = [
            {"product": "A", "sales": 150},
            {"product": "B", "sales": 180}
        ]
        
        analyst = DataAnalyst()
        comparator = ComparisonAnalyzer()
        summarizer = ResultSummarizer()
        
        trend = analyst.calculate_trend(this_month, last_month, "sales")
        assert trend["trend"] == "up"
        
        comparison_text = comparator.compare(this_month, last_month, "销售对比")
        assert "当前数据" in comparison_text
        
        last_summary = summarizer.summarize(last_month)
        this_summary = summarizer.summarize(this_month)
        
        assert "2" in last_summary
        assert "2" in this_summary

    def test_empty_handling(self):
        explainer = ResultExplainer()
        analyst = DataAnalyst()
        summarizer = ResultSummarizer()
        comparator = ComparisonAnalyzer()
        formatter = ResultFormatter()
        
        empty_result = []
        
        explanation = explainer.explain("查询", empty_result)
        assert "空" in explanation
        
        analysis = analyst.analyze(empty_result)
        assert "error" in analysis
        
        summary = summarizer.summarize(empty_result)
        assert "空" in summary
        
        comparison = comparator.compare([], [], "对比")
        assert "不足" in comparison
        
        table = formatter.format_table(empty_result)
        assert "无数据" in table
