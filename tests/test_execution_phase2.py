import pytest
from src.execution.error_analyzer import ErrorAnalyzer, RetryConfig, RetryStrategy


def test_error_analyzer_init():
    analyzer = ErrorAnalyzer()
    assert analyzer is not None


def test_error_analyzer_syntax_error():
    analyzer = ErrorAnalyzer()
    error_type, suggestion = analyzer.analyze("syntax error near 'FROM'")
    assert error_type == "syntax"
    assert "语法错误" in suggestion["message"]


def test_error_analyzer_no_table():
    analyzer = ErrorAnalyzer()
    error_type, suggestion = analyzer.analyze("no such table: users")
    assert error_type == "no_table"
    assert "表不存在" in suggestion["message"]


def test_error_analyzer_no_column():
    analyzer = ErrorAnalyzer()
    error_type, suggestion = analyzer.analyze("no such column: user_name")
    assert error_type == "no_column"
    assert "列不存在" in suggestion["message"]


def test_error_analyzer_type_mismatch():
    analyzer = ErrorAnalyzer()
    error_type, suggestion = analyzer.analyze("cannot convert text to integer")
    assert error_type == "type_mismatch"
    assert "数据类型不匹配" in suggestion["message"]


def test_error_analyzer_constraint():
    analyzer = ErrorAnalyzer()
    error_type, suggestion = analyzer.analyze("UNIQUE constraint failed")
    assert error_type == "constraint"
    assert "约束冲突" in suggestion["message"]


def test_error_analyzer_unknown():
    analyzer = ErrorAnalyzer()
    error_type, suggestion = analyzer.analyze("some random error")
    assert error_type == "unknown"
    assert "未知错误类型" in suggestion["message"]


def test_error_analyzer_case_insensitive():
    analyzer = ErrorAnalyzer()
    error_type, suggestion = analyzer.analyze("SYNTAX ERROR near SELECT")
    assert error_type == "syntax"


def test_retry_config_init():
    config = RetryConfig()
    assert config.max_retries == 3
    assert config.strategy == RetryStrategy.EXPONENTIAL
    assert config.base_delay == 1.0
    assert config.max_delay == 10.0


def test_retry_config_custom():
    config = RetryConfig(max_retries=5, strategy=RetryStrategy.LINEAR, base_delay=2.0)
    assert config.max_retries == 5
    assert config.strategy == RetryStrategy.LINEAR
    assert config.base_delay == 2.0


def test_retry_config_immediate():
    config = RetryConfig(strategy=RetryStrategy.IMMEDIATE)
    assert config.get_delay(0) == 0
    assert config.get_delay(1) == 0
    assert config.get_delay(5) == 0


def test_retry_config_linear():
    config = RetryConfig(strategy=RetryStrategy.LINEAR, base_delay=1.0)
    assert config.get_delay(0) == 0
    assert config.get_delay(1) == 1.0
    assert config.get_delay(2) == 2.0
    assert config.get_delay(10) == 10.0


def test_retry_config_exponential():
    config = RetryConfig(strategy=RetryStrategy.EXPONENTIAL, base_delay=1.0)
    assert config.get_delay(0) == 1.0
    assert config.get_delay(1) == 2.0
    assert config.get_delay(2) == 4.0
    assert config.get_delay(3) == 8.0


def test_retry_config_max_delay():
    config = RetryConfig(strategy=RetryStrategy.EXPONENTIAL, base_delay=1.0, max_delay=5.0)
    assert config.get_delay(10) == 5.0


def test_retry_strategy_constants():
    assert RetryStrategy.IMMEDIATE == "immediate"
    assert RetryStrategy.LINEAR == "linear"
    assert RetryStrategy.EXPONENTIAL == "exponential"
