import pytest
from src.explanation.formatters import ResultFormatter, I18N_MESSAGES


class TestI18N:
    def test_i18n_messages_zh(self):
        assert "zh" in I18N_MESSAGES
        assert I18N_MESSAGES["zh"]["no_data"] == "无数据"
        assert I18N_MESSAGES["zh"]["total_rows"] == "共 {count} 条"

    def test_i18n_messages_en(self):
        assert "en" in I18N_MESSAGES
        assert I18N_MESSAGES["en"]["no_data"] == "No data"
        assert I18N_MESSAGES["en"]["total_rows"] == "Total {count} rows"

    def test_formatter_init_default_locale(self):
        formatter = ResultFormatter()
        assert formatter.locale == "zh"

    def test_formatter_init_custom_locale(self):
        formatter = ResultFormatter(locale="en")
        assert formatter.locale == "en"

    def test_format_table_chinese(self):
        result = [{"name": "John", "age": 30}]
        formatted = ResultFormatter.format_table(result, locale="zh")
        assert "无数据" not in formatted
        assert "John" in formatted
        assert "30" in formatted

    def test_format_table_english(self):
        result = [{"name": "John", "age": 30}]
        formatted = ResultFormatter.format_table(result, locale="en")
        assert "No data" not in formatted
        assert "John" in formatted
        assert "30" in formatted

    def test_format_table_no_data_zh(self):
        result = []
        formatted = ResultFormatter.format_table(result, locale="zh")
        assert "无数据" in formatted

    def test_format_table_no_data_en(self):
        result = []
        formatted = ResultFormatter.format_table(result, locale="en")
        assert "No data" in formatted

    def test_format_markdown_chinese(self):
        result = [{"name": "John", "age": 30}]
        formatted = ResultFormatter.format_markdown(result, locale="zh")
        assert "John" in formatted
        assert "age" in formatted

    def test_format_markdown_english(self):
        result = [{"name": "John", "age": 30}]
        formatted = ResultFormatter.format_markdown(result, locale="en")
        assert "John" in formatted

    def test_format_html_chinese(self):
        result = [{"name": "John", "age": 30}]
        formatted = ResultFormatter.format_html(result, locale="zh")
        assert "<td>John</td>" in formatted

    def test_format_html_english(self):
        result = [{"name": "John", "age": 30}]
        formatted = ResultFormatter.format_html(result, locale="en")
        assert "<td>John</td>" in formatted

    def test_format_text_chinese(self):
        result = [{"name": "John", "age": 30}]
        formatted = ResultFormatter.format_text(result, locale="zh")
        assert "John" in formatted

    def test_format_text_english(self):
        result = [{"name": "John", "age": 30}]
        formatted = ResultFormatter.format_text(result, locale="en")
        assert "John" in formatted

    def test_format_text_no_data_zh(self):
        result = []
        formatted = ResultFormatter.format_text(result, locale="zh")
        assert "无数据" in formatted

    def test_format_text_no_data_en(self):
        result = []
        formatted = ResultFormatter.format_text(result, locale="en")
        assert "No data" in formatted
