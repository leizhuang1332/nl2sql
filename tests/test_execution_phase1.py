import pytest
import os
import tempfile
import sqlite3
from unittest.mock import MagicMock, patch
from src.execution.query_executor import QueryExecutor
from src.execution.result_handler import ResultHandler


@pytest.fixture
def test_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100),
            age INTEGER
        )
    """)
    conn.execute("INSERT INTO users (name, age) VALUES ('Alice', 25)")
    conn.execute("INSERT INTO users (name, age) VALUES ('Bob', 30)")
    conn.commit()
    conn.close()
    yield path
    os.unlink(path)


def test_query_executor_init(test_db):
    from langchain_community.utilities import SQLDatabase
    db = SQLDatabase.from_uri(f"sqlite:///{test_db}")
    executor = QueryExecutor(database=db)
    assert executor.max_retries == 3
    assert executor.execution_history == []


def test_query_executor_custom_max_retries(test_db):
    from langchain_community.utilities import SQLDatabase
    db = SQLDatabase.from_uri(f"sqlite:///{test_db}")
    executor = QueryExecutor(database=db, max_retries=5)
    assert executor.max_retries == 5


def test_query_executor_execute_success(test_db):
    from langchain_community.utilities import SQLDatabase
    db = SQLDatabase.from_uri(f"sqlite:///{test_db}")
    executor = QueryExecutor(database=db)
    result = executor.execute("SELECT * FROM users")
    assert result["success"] is True
    assert "Alice" in str(result["result"])
    assert result["attempts"] == 1


def test_query_executor_execute_failure(test_db):
    from langchain_community.utilities import SQLDatabase
    db = SQLDatabase.from_uri(f"sqlite:///{test_db}")
    executor = QueryExecutor(database=db, max_retries=2)
    result = executor.execute("SELECT * FROM nonexistent")
    assert result["success"] is False
    assert "no such table" in result["error"].lower()


def test_query_executor_record_execution(test_db):
    from langchain_community.utilities import SQLDatabase
    db = SQLDatabase.from_uri(f"sqlite:///{test_db}")
    executor = QueryExecutor(database=db)
    executor.execute("SELECT * FROM users")
    history = executor.get_history()
    assert len(history) == 1
    assert history[0]["success"] is True


def test_query_executor_clean_sql():
    from langchain_community.utilities import SQLDatabase
    db = MagicMock()
    executor = QueryExecutor(database=db)

    assert executor._clean_sql("```sql\nSELECT * FROM users\n```") == "SELECT * FROM users"
    assert executor._clean_sql("SELECT * FROM users") == "SELECT * FROM users"
    assert executor._clean_sql("  SELECT * FROM users  ") == "SELECT * FROM users"


def test_result_handler_init():
    handler = ResultHandler()
    assert "table" in handler.formatters
    assert "json" in handler.formatters
    assert "text" in handler.formatters
    assert "markdown" in handler.formatters


def test_result_handler_format_table():
    handler = ResultHandler()
    data = [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]
    result = handler.handle(data, format_type="table")
    assert "name" in result
    assert "age" in result
    assert "Alice" in result
    assert "Bob" in result


def test_result_handler_format_json():
    handler = ResultHandler()
    data = [{"name": "Alice", "age": 25}]
    result = handler.handle(data, format_type="json")
    assert "Alice" in result
    assert "25" in result


def test_result_handler_format_text():
    handler = ResultHandler()
    data = [{"name": "Alice", "age": 25}]
    result = handler.handle(data, format_type="text")
    assert "name: Alice" in result
    assert "age: 25" in result


def test_result_handler_format_markdown():
    handler = ResultHandler()
    data = [{"name": "Alice"}]
    result = handler.handle(data, format_type="markdown")
    assert "## 查询结果" in result
    assert "name" in result


def test_result_handler_parse_string_json():
    handler = ResultHandler()
    result = handler._parse_result('[{"name": "Alice"}]')
    assert result == [{"name": "Alice"}]


def test_result_handler_parse_string_invalid():
    handler = ResultHandler()
    result = handler._parse_result("invalid data")
    assert result == []


def test_result_handler_empty_result():
    handler = ResultHandler()
    result = handler.handle([], format_type="table")
    assert result == "无结果"
