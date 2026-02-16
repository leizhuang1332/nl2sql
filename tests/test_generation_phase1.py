import pytest
from unittest.mock import MagicMock
from src.generation.llm_factory import LLMFactory, create_llm
from src.generation.sql_generator import SQLGenerator


def test_llm_factory_create_minimax():
    llm = create_llm(
        provider="minimax",
        model="MiniMax-M2.5",
        api_key="test-key"
    )
    assert llm.model_name == "MiniMax-M2.5"


def test_llm_factory_create_openai():
    llm = create_llm(
        provider="openai",
        model="gpt-4",
        api_key="test-key"
    )
    assert llm.model_name == "gpt-4"


def test_llm_factory_invalid_provider():
    with pytest.raises(ValueError, match="不支持的 LLM 提供商"):
        create_llm(provider="invalid_provider")


def test_sql_generator_init():
    mock_llm = MagicMock()
    generator = SQLGenerator(llm=mock_llm)
    assert generator.llm == mock_llm


def test_sql_generator_clean_sql():
    mock_llm = MagicMock()
    generator = SQLGenerator(llm=mock_llm)

    assert generator._clean_sql("```sql\nSELECT * FROM users\n```") == "SELECT * FROM users"
    assert generator._clean_sql("SELECT * FROM users") == "SELECT * FROM users"
    assert generator._clean_sql("  SELECT * FROM users  ") == "SELECT * FROM users"


def test_sql_generator_with_mock_llm():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = "SELECT * FROM users WHERE age > 18"
    mock_llm.return_value = "SELECT * FROM users WHERE age > 18"
    generator = SQLGenerator(llm=mock_llm)
    result = generator._clean_sql("SELECT * FROM users WHERE age > 18")
    assert result == "SELECT * FROM users WHERE age > 18"


def test_sql_generator_with_markdown():
    mock_llm = MagicMock()
    generator = SQLGenerator(llm=mock_llm)
    result = generator._clean_sql("```sql\nSELECT name FROM users\n```")
    assert result == "SELECT name FROM users"
