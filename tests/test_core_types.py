import pytest
from src.core.types import (
    QueryStatus,
    MappingResult,
    GenerationResult,
    SecurityResult,
    ExecutionResult,
    QueryResult,
)


def test_query_status_enum():
    assert QueryStatus.SUCCESS.value == "success"
    assert QueryStatus.SECURITY_REJECTED.value == "security_rejected"
    assert QueryStatus.EXECUTION_ERROR.value == "execution_error"


def test_mapping_result():
    result = MappingResult(
        enhanced_question="今天有多少用户?",
        field_mappings=[{"term": "用户", "fields": ["name"]}],
        time_mappings=[{"expression": "今天", "sql": "DATE('now')"}],
    )
    assert result.enhanced_question == "今天有多少用户?"
    assert len(result.field_mappings) == 1
    assert len(result.time_mappings) == 1


def test_mapping_result_defaults():
    result = MappingResult(enhanced_question="test")
    assert result.enhanced_question == "test"
    assert result.field_mappings == []
    assert result.time_mappings == []
    assert result.sort_mappings == []


def test_generation_result():
    result = GenerationResult(
        sql="SELECT COUNT(*) FROM users",
        confidence=0.95,
        used_few_shots=["example1", "example2"],
    )
    assert result.sql == "SELECT COUNT(*) FROM users"
    assert result.confidence == 0.95
    assert len(result.used_few_shots) == 2


def test_generation_result_defaults():
    result = GenerationResult(sql="SELECT 1")
    assert result.sql == "SELECT 1"
    assert result.confidence == 1.0
    assert result.used_few_shots == []


def test_security_result():
    result = SecurityResult(
        is_valid=True,
        threat_level="safe",
        message="验证通过",
        details={"check": "passed"},
    )
    assert result.is_valid is True
    assert result.threat_level == "safe"
    assert result.message == "验证通过"


def test_security_result_defaults():
    result = SecurityResult(is_valid=False, threat_level="critical")
    assert result.is_valid is False
    assert result.threat_level == "critical"
    assert result.message == ""
    assert result.details == {}


def test_execution_result():
    result = ExecutionResult(
        success=True,
        result=[{"id": 1, "name": "Alice"}],
        attempts=1,
        execution_time=0.5,
    )
    assert result.success is True
    assert len(result.result) == 1
    assert result.attempts == 1
    assert result.execution_time == 0.5


def test_execution_result_defaults():
    result = ExecutionResult(success=False, error="Table not found")
    assert result.success is False
    assert result.error == "Table not found"
    assert result.result is None
    assert result.attempts == 1
    assert result.execution_time == 0.0


def test_query_result():
    mapping = MappingResult(enhanced_question="test question")
    security = SecurityResult(is_valid=True)
    execution = ExecutionResult(success=True, result=[])

    result = QueryResult(
        status=QueryStatus.SUCCESS,
        question="有多少用户?",
        mapping=mapping,
        sql="SELECT COUNT(*) FROM users",
        security=security,
        execution=execution,
        explanation="共有 100 个用户",
    )

    assert result.status == QueryStatus.SUCCESS
    assert result.question == "有多少用户?"
    assert result.sql == "SELECT COUNT(*) FROM users"
    assert result.explanation == "共有 100 个用户"


def test_query_result_minimal():
    result = QueryResult(
        status=QueryStatus.SUCCESS,
        question="test?",
    )
    assert result.status == QueryStatus.SUCCESS
    assert result.question == "test?"
    assert result.mapping is None
    assert result.sql == ""
    assert result.security is None
    assert result.execution is None
    assert result.explanation == ""
    assert result.metadata == {}


def test_query_result_with_metadata():
    result = QueryResult(
        status=QueryStatus.EXECUTION_ERROR,
        question="test?",
        error_message="timeout",
        metadata={"execution_time": 30.5, "retry_count": 3},
    )
    assert result.status == QueryStatus.EXECUTION_ERROR
    assert result.error_message == "timeout"
    assert result.metadata["execution_time"] == 30.5
    assert result.metadata["retry_count"] == 3
