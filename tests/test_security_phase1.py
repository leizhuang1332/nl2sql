import pytest
import json
import tempfile
import os
from src.security.sql_validator import SQLSecurityValidator, ThreatLevel, ValidationResult
from src.security.permission_manager import PermissionManager, PermissionLevel


class TestSQLSecurityValidator:
    def test_sql_validator_init(self):
        validator = SQLSecurityValidator()
        assert validator is not None
        assert validator.read_only is True

    def test_sql_validator_init_with_params(self):
        validator = SQLSecurityValidator(
            allowed_tables=["users", "orders"],
            allowed_columns={"users": ["id", "name"]},
            read_only=False
        )
        assert validator.allowed_tables == ["users", "orders"]
        assert validator.allowed_columns == {"users": ["id", "name"]}
        assert validator.read_only is False

    def test_sql_validator_safe_query(self):
        validator = SQLSecurityValidator()
        result = validator.validate("SELECT * FROM users")
        assert result.is_valid is True
        assert result.threat_level == ThreatLevel.SAFE

    def test_sql_validator_dangerous_keywords_drop(self):
        validator = SQLSecurityValidator()
        result = validator.validate("DROP TABLE users")
        assert result.is_valid is False
        assert result.threat_level == ThreatLevel.CRITICAL
        assert "DROP" in result.message

    def test_sql_validator_dangerous_keywords_delete(self):
        validator = SQLSecurityValidator()
        result = validator.validate("DELETE FROM users")
        assert result.is_valid is False
        assert result.threat_level == ThreatLevel.CRITICAL

    def test_sql_validator_dangerous_keywords_insert(self):
        validator = SQLSecurityValidator()
        result = validator.validate("INSERT INTO users VALUES (1, 'test')")
        assert result.is_valid is False
        assert result.threat_level == ThreatLevel.CRITICAL

    def test_sql_validator_dangerous_keywords_update(self):
        validator = SQLSecurityValidator()
        result = validator.validate("UPDATE users SET name = 'test'")
        assert result.is_valid is False
        assert result.threat_level == ThreatLevel.CRITICAL

    def test_sql_validator_suspicious_pattern_union(self):
        validator = SQLSecurityValidator()
        result = validator.validate("SELECT * FROM users UNION SELECT * FROM admins")
        assert result.is_valid is False
        assert result.threat_level == ThreatLevel.HIGH

    def test_sql_validator_suspicious_pattern_or_1_equals_1(self):
        validator = SQLSecurityValidator()
        result = validator.validate("SELECT * FROM users WHERE id = '1' OR '1'='1'")
        assert result.is_valid is False
        assert result.threat_level == ThreatLevel.HIGH

    def test_sql_validator_table_whitelist_allowed(self):
        validator = SQLSecurityValidator(allowed_tables=["users", "orders"])
        result = validator.validate("SELECT * FROM users")
        assert result.is_valid is True

    def test_sql_validator_table_whitelist_not_allowed(self):
        validator = SQLSecurityValidator(allowed_tables=["users", "orders"])
        result = validator.validate("SELECT * FROM admins")
        assert result.is_valid is False
        assert result.threat_level == ThreatLevel.HIGH

    def test_sql_validator_column_whitelist_allowed(self):
        validator = SQLSecurityValidator(
            allowed_columns={"users": ["id", "name", "email"]}
        )
        result = validator.validate("SELECT id, name FROM users")
        assert result.is_valid is True

    def test_sql_validator_column_whitelist_not_allowed(self):
        validator = SQLSecurityValidator(
            allowed_columns={"users": ["id", "name"]}
        )
        result = validator.validate("SELECT id, name, password FROM users")
        assert result.is_valid is False
        assert result.threat_level == ThreatLevel.MEDIUM

    def test_sql_validator_read_only_allows_select(self):
        validator = SQLSecurityValidator(read_only=True)
        result = validator.validate("SELECT * FROM users")
        assert result.is_valid is True

    def test_sql_validator_read_only_blocks_update(self):
        validator = SQLSecurityValidator(read_only=True)
        result = validator.validate("UPDATE users SET name = 'test'")
        assert result.is_valid is False
        assert result.threat_level == ThreatLevel.CRITICAL

    def test_sql_validator_read_only_disabled(self):
        validator = SQLSecurityValidator(read_only=False)
        result = validator.validate("SELECT * FROM users")
        assert result.is_valid is True


class TestPermissionManager:
    def test_permission_manager_init(self):
        manager = PermissionManager()
        assert manager is not None
        assert len(manager.table_permissions) == 0

    def test_permission_manager_set_permission_read(self):
        manager = PermissionManager()
        manager.set_table_permission("users", PermissionLevel.READ)
        assert manager.can_read_table("users") is True
        assert manager.can_write_table("users") is False
        assert manager.can_admin_table("users") is False

    def test_permission_manager_set_permission_write(self):
        manager = PermissionManager()
        manager.set_table_permission("users", PermissionLevel.WRITE)
        assert manager.can_read_table("users") is True
        assert manager.can_write_table("users") is True
        assert manager.can_admin_table("users") is False

    def test_permission_manager_set_permission_admin(self):
        manager = PermissionManager()
        manager.set_table_permission("users", PermissionLevel.ADMIN)
        assert manager.can_read_table("users") is True
        assert manager.can_write_table("users") is True
        assert manager.can_admin_table("users") is True

    def test_permission_manager_unconfigured_table(self):
        manager = PermissionManager()
        assert manager.can_read_table("users") is False

    def test_permission_manager_column_access(self):
        manager = PermissionManager()
        manager.set_table_permission("users", PermissionLevel.READ, ["id", "name"])
        assert manager.can_access_column("users", "id") is True
        assert manager.can_access_column("users", "name") is True
        assert manager.can_access_column("users", "password") is False

    def test_permission_manager_column_access_no_restriction(self):
        manager = PermissionManager()
        manager.set_table_permission("users", PermissionLevel.READ)
        assert manager.can_access_column("users", "id") is True
        assert manager.can_access_column("users", "password") is True

    def test_permission_manager_load_from_config(self):
        manager = PermissionManager()
        config = {
            "column_permissions": {
                "users": {"level": "READ", "columns": ["id", "name"]},
                "orders": {"level": "WRITE", "columns": None}
            }
        }
        manager.load_from_config(config)
        assert manager.can_read_table("users") is True
        assert manager.can_write_table("orders") is True
        assert manager.can_access_column("users", "id") is True

    def test_permission_manager_clear(self):
        manager = PermissionManager()
        manager.set_table_permission("users", PermissionLevel.READ)
        assert manager.can_read_table("users") is True
        manager.clear()
        assert manager.can_read_table("users") is False

    def test_permission_manager_get_all_tables(self):
        manager = PermissionManager()
        manager.set_table_permission("users", PermissionLevel.READ)
        manager.set_table_permission("orders", PermissionLevel.WRITE)
        tables = manager.get_all_tables()
        assert "users" in tables
        assert "orders" in tables

    def test_permission_manager_get_table_permission(self):
        manager = PermissionManager()
        manager.set_table_permission("users", PermissionLevel.READ, ["id", "name"])
        perm = manager.get_table_permission("users")
        assert perm is not None
        assert perm.table_name == "users"
        assert perm.permission_level == PermissionLevel.READ
