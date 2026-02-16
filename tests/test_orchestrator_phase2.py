import pytest
import sqlite3
import tempfile
import os
from unittest.mock import Mock, patch


@pytest.fixture
def mock_llm():
    llm = Mock()
    llm.invoke.return_value = Mock(content="SELECT * FROM users")
    return llm


@pytest.fixture
def test_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            age INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            amount DECIMAL(10,2)
        )
    """)
    conn.commit()
    conn.close()

    yield path
    os.unlink(path)


@pytest.fixture
def orchestrator(mock_llm, test_db):
    from src.core.orchestrator import NL2SQLOrchestrator
    return NL2SQLOrchestrator(
        llm=mock_llm,
        database_uri=f"sqlite:///{test_db}",
        config={"read_only": True}
    )


def test_orchestrator_init(orchestrator):
    assert orchestrator.db is not None
    assert orchestrator.sql_generator is not None
    assert orchestrator.query_executor is not None
    assert orchestrator.semantic_mapper is not None
    assert orchestrator.security_validator is not None
    assert orchestrator.result_explainer is not None
    assert orchestrator.schema_extractor is not None
    assert orchestrator.schema_doc_generator is not None


def test_get_table_names(orchestrator):
    tables = orchestrator.get_table_names()
    assert "users" in tables
    assert "orders" in tables


def test_get_schema(orchestrator):
    schema = orchestrator.get_schema("users")
    assert schema["table_name"] == "users"
    assert "columns" in schema


def test_semantic_mapping(orchestrator):
    result = orchestrator._semantic_mapping("有多少用户?")
    assert result.enhanced_question is not None
    assert "多少" in result.enhanced_question


def test_semantic_mapping_with_time(orchestrator):
    result = orchestrator._semantic_mapping("今天的订单有多少?")
    assert "今天" in result.enhanced_question


def test_prepare_schema(orchestrator):
    schema_doc = orchestrator._prepare_schema()
    assert "users" in schema_doc
    assert "orders" in schema_doc
    assert "id" in schema_doc.lower()


def test_generate_sql(orchestrator):
    schema_doc = "Table: users (id INTEGER, name TEXT)"
    sql = orchestrator._generate_sql("有多少用户?", schema_doc)
    assert sql.upper().startswith("SELECT")


def test_validate_security_safe(orchestrator):
    result = orchestrator._validate_security("SELECT * FROM users")
    assert result.is_valid is True


def test_validate_security_dangerous(orchestrator):
    result = orchestrator._validate_security("DROP TABLE users")
    assert result.is_valid is False
    assert result.threat_level == "critical"


def test_validate_security_insert(orchestrator):
    result = orchestrator._validate_security("INSERT INTO users VALUES (1)")
    assert result.is_valid is False


def test_execute_sql_success(orchestrator):
    from src.execution.query_executor import QueryExecutor
    orchestrator.db_connector.db.run("INSERT INTO users (name, age) VALUES ('Alice', 25)")

    result = orchestrator._execute_sql("SELECT * FROM users")
    assert result.success is True


def test_execute_sql_error(orchestrator):
    result = orchestrator._execute_sql("SELECT * FROM nonexistent_table")
    assert result.attempts > 1


def test_explain_result(orchestrator):
    result_data = [{"count": 100}]
    explanation = orchestrator._explain_result("有多少用户?", result_data)
    assert explanation is not None
    assert len(explanation) > 0


def test_ask_with_mock_llm(orchestrator):
    orchestrator.llm.invoke.return_value = "SELECT COUNT(*) FROM users"

    result = orchestrator.ask("有多少用户?")

    assert result.question == "有多少用户?"
    assert result.sql is not None
    assert "SELECT" in result.sql.upper()
