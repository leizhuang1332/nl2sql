import pytest
from src.generation.sql_validator import SQLValidator


def test_sql_validator_init():
    validator = SQLValidator()
    assert validator is not None


def test_sql_validator_valid_select():
    validator = SQLValidator()
    is_valid, message = validator.validate("SELECT * FROM users")
    assert is_valid is True
    assert "通过" in message


def test_sql_validator_select_with_where():
    validator = SQLValidator()
    is_valid, message = validator.validate("SELECT name, age FROM users WHERE age > 18")
    assert is_valid is True


def test_sql_validator_select_with_join():
    validator = SQLValidator()
    is_valid, message = validator.validate(
        "SELECT users.name, orders.amount FROM users JOIN orders ON users.id = orders.user_id"
    )
    assert is_valid is True


def test_sql_validator_drop_rejected():
    validator = SQLValidator()
    is_valid, message = validator.validate("DROP TABLE users")
    assert is_valid is False
    assert "DROP" in message


def test_sql_validator_delete_rejected():
    validator = SQLValidator()
    is_valid, message = validator.validate("DELETE FROM users WHERE id = 1")
    assert is_valid is False
    assert "DELETE" in message


def test_sql_validator_update_rejected():
    validator = SQLValidator()
    is_valid, message = validator.validate("UPDATE users SET name = 'test'")
    assert is_valid is False
    assert "UPDATE" in message


def test_sql_validator_insert_rejected():
    validator = SQLValidator()
    is_valid, message = validator.validate("INSERT INTO users (name) VALUES ('test')")
    assert is_valid is False
    assert "INSERT" in message


def test_sql_validator_alter_rejected():
    validator = SQLValidator()
    is_valid, message = validator.validate("ALTER TABLE users ADD COLUMN new_col VARCHAR")
    assert is_valid is False
    assert "ALTER" in message


def test_sql_validator_create_rejected():
    validator = SQLValidator()
    is_valid, message = validator.validate("CREATE TABLE new_table (id INT)")
    assert is_valid is False
    assert "CREATE" in message


def test_sql_validator_truncate_rejected():
    validator = SQLValidator()
    is_valid, message = validator.validate("TRUNCATE TABLE users")
    assert is_valid is False
    assert "TRUNCATE" in message


def test_sql_validator_non_select_rejected():
    validator = SQLValidator()
    is_valid, message = validator.validate("SHOW TABLES")
    assert is_valid is False
    assert "SELECT" in message


def test_sql_validator_case_insensitive():
    validator = SQLValidator()
    is_valid, message = validator.validate("select * from users")
    assert is_valid is True


def test_sql_validator_with_whitespace():
    validator = SQLValidator()
    is_valid, message = validator.validate("  SELECT * FROM users  ")
    assert is_valid is True


def test_sql_validator_validate_with_fix():
    validator = SQLValidator()
    is_valid, message, fixed_sql = validator.validate_with_fix("SELECT * FROM users")
    assert is_valid is True
    assert fixed_sql == "SELECT * FROM users"


def test_sql_validator_validate_with_fix_removes_dangerous():
    validator = SQLValidator()
    is_valid, message, fixed_sql = validator.validate_with_fix("SELECT 1; DROP TABLE users")
    assert "SELECT" in fixed_sql


def test_sql_validator_is_select_only():
    validator = SQLValidator()
    assert validator.is_select_only("SELECT * FROM users") is True
    assert validator.is_select_only("select name from users") is True
    assert validator.is_select_only("DROP TABLE users") is False


def test_sql_validator_contains_dangerous_keyword():
    validator = SQLValidator()
    assert validator.contains_dangerous_keyword("SELECT * FROM users") is False
    assert validator.contains_dangerous_keyword("DROP TABLE users") is True
    assert validator.contains_dangerous_keyword("DELETE FROM users") is True


def test_sql_validator_custom_keywords():
    validator = SQLValidator(custom_dangerous_keywords=["EXEC", "EXECUTE"])
    is_valid, message = validator.validate("EXEC sp_executesql")
    assert is_valid is False
    assert "EXEC" in message
