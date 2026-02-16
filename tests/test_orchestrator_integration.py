import pytest
import sqlite3
import tempfile
import os
from unittest.mock import Mock


@pytest.fixture
def test_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            age INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            amount DECIMAL(10,2),
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price DECIMAL(10,2),
            category TEXT
        );
        
        INSERT INTO users (name, age) VALUES 
            ('Alice', 25),
            ('Bob', 30),
            ('Charlie', 35);
            
        INSERT INTO orders (user_id, amount, status) VALUES 
            (1, 100.0, 'completed'),
            (1, 200.0, 'pending'),
            (2, 150.0, 'completed'),
            (2, 80.0, 'cancelled');
            
        INSERT INTO products (name, price, category) VALUES 
            ('iPhone', 5999.0, 'electronics'),
            ('MacBook', 9999.0, 'electronics'),
            ('T恤', 199.0, 'clothing');
    """)
    conn.close()

    yield path
    os.unlink(path)


@pytest.fixture
def mock_llm():
    llm = Mock()
    llm.invoke.return_value = "SELECT COUNT(*) FROM users"
    return llm


@pytest.fixture
def orchestrator(mock_llm, test_db):
    from src.core.orchestrator import NL2SQLOrchestrator
    return NL2SQLOrchestrator(
        llm=mock_llm,
        database_uri=f"sqlite:///{test_db}",
        config={"read_only": True}
    )


def test_e2e_simple_query(orchestrator):
    """端到端测试 - 简单查询"""
    result = orchestrator.ask("有多少用户?")

    assert result.status.value == "success"
    assert result.sql
    assert "SELECT" in result.sql.upper()
    assert result.explanation


def test_e2e_list_all_products(orchestrator):
    """端到端测试 - 列出所有产品"""
    orchestrator.llm.invoke.return_value = "SELECT * FROM products"
    result = orchestrator.ask("列出所有产品")

    assert result.status.value == "success"
    assert result.sql
    assert "products" in result.sql.lower()


def test_e2e_conditional_query(orchestrator):
    """端到端测试 - 带条件查询"""
    orchestrator.llm.invoke.return_value = "SELECT * FROM users WHERE age > 25"
    result = orchestrator.ask("年龄大于25的用户有哪些?")

    assert result.status.value == "success"
    assert result.sql
    assert "WHERE" in result.sql.upper() or ">" in result.sql


def test_e2e_completed_orders(orchestrator):
    """端到端测试 - 已完成的订单"""
    orchestrator.llm.invoke.return_value = "SELECT * FROM orders WHERE status = 'completed'"
    result = orchestrator.ask("已完成的订单有哪些?")

    assert result.status.value == "success"
    assert result.sql
    assert "status" in result.sql.lower()


def test_e2e_aggregate_count(orchestrator):
    """端到端测试 - 聚合查询 COUNT"""
    orchestrator.llm.invoke.return_value = "SELECT AVG(amount) FROM orders"
    result = orchestrator.ask("平均订单金额是多少?")

    assert result.status.value == "success"
    assert result.sql
    assert "AVG" in result.sql.upper() or "avg" in result.sql.lower()


def test_e2e_aggregate_sum(orchestrator):
    """端到端测试 - 聚合查询 SUM"""
    orchestrator.llm.invoke.return_value = "SELECT user_id, SUM(amount) FROM orders GROUP BY user_id"
    result = orchestrator.ask("每个用户的订单总额是多少?")

    assert result.status.value == "success"
    assert result.sql


def test_e2e_group_by(orchestrator):
    """端到端测试 - 分组查询"""
    orchestrator.llm.invoke.return_value = "SELECT status, COUNT(*) FROM orders GROUP BY status"
    result = orchestrator.ask("每个状态有多少订单?")

    assert result.status.value == "success"
    assert result.sql
    assert "GROUP BY" in result.sql.upper()


def test_e2e_join_query(orchestrator):
    """端到端测试 - 关联查询"""
    orchestrator.llm.invoke.return_value = "SELECT u.name, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id"
    result = orchestrator.ask("每个用户的订单数量")

    assert result.status.value == "success"
    assert result.sql


def test_e2e_security_rejection_dangerous_keyword(orchestrator):
    """端到端测试 - 安全拒绝 - 危险关键字"""
    orchestrator.llm.invoke.return_value = "DROP TABLE users"

    result = orchestrator.ask("删除用户表")

    assert result.status.value == "security_rejected"
    assert result.security is not None
    assert result.security.is_valid is False


def test_e2e_security_rejection_insert(orchestrator):
    """端到端测试 - 安全拒绝 - INSERT 操作"""
    orchestrator.llm.invoke.return_value = "INSERT INTO users VALUES (1, 'test', 20)"

    result = orchestrator.ask("插入一个用户")

    assert result.status.value == "security_rejected"
    assert result.security is not None
    assert result.security.is_valid is False


def test_e2e_security_rejection_update(orchestrator):
    """端到端测试 - 安全拒绝 - UPDATE 操作"""
    orchestrator.llm.invoke.return_value = "UPDATE users SET age = 100"

    result = orchestrator.ask("更新用户年龄")

    assert result.status.value == "security_rejected"
    assert result.security is not None
    assert result.security.is_valid is False


def test_e2e_time_expression(orchestrator):
    """端到端测试 - 时间表达式"""
    result = orchestrator.ask("今天的订单有多少?")

    assert result.status.value == "success"
    assert result.mapping is not None
    assert "今天" in result.mapping.enhanced_question


def test_e2e_sort_expression(orchestrator):
    """端到端测试 - 排序表达式"""
    result = orchestrator.ask("销售额最高的前5个产品")

    assert result.status.value == "success"
    assert result.sql


def test_e2e_result_explanation(orchestrator):
    """端到端测试 - 结果解释"""
    result = orchestrator.ask("有多少用户?")

    assert result.status.value == "success"
    assert result.explanation
    assert len(result.explanation) > 0


def test_e2e_metadata_tracking(orchestrator):
    """端到端测试 - 元数据追踪"""
    result = orchestrator.ask("有多少用户?")

    assert result.status.value == "success"
    assert "execution_time" in result.metadata


def test_e2e_full_pipeline_with_all_stages(orchestrator):
    """端到端测试 - 完整流水线包含所有阶段"""
    result = orchestrator.ask("有多少用户?")

    assert result.question == "有多少用户?"
    assert result.mapping is not None
    assert result.sql
    assert result.security is not None
    assert result.security.is_valid is True
    assert result.execution is not None
    assert result.execution.success is True
    assert result.explanation
