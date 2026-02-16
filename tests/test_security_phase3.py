import pytest
import tempfile
import os
import logging
from src.security.audit_logger import AuditLogger


class TestAuditLogger:
    def test_audit_logger_init(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        logger = AuditLogger(log_file=path)
        assert logger is not None
        os.unlink(path)

    def test_audit_logger_log_query(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        logger = AuditLogger(log_file=path)
        logger.log_query("SELECT * FROM users", "test_user", "success")
        with open(path, "r") as f:
            content = f.read()
        assert "QUERY" in content
        assert "SELECT * FROM users" in content
        assert "test_user" in content
        os.unlink(path)

    def test_audit_logger_log_query_with_duration(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        logger = AuditLogger(log_file=path)
        logger.log_query("SELECT * FROM users", "test_user", "success", duration_ms=50.5)
        with open(path, "r") as f:
            content = f.read()
        assert "50.5" in content
        os.unlink(path)

    def test_audit_logger_log_security_event(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        logger = AuditLogger(log_file=path)
        logger.log_security_event("INTRUSION", {"ip": "192.168.1.1"})
        with open(path, "r") as f:
            content = f.read()
        assert "SECURITY" in content
        assert "INTRUSION" in content
        assert "192.168.1.1" in content
        os.unlink(path)

    def test_audit_logger_log_security_event_with_user(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        logger = AuditLogger(log_file=path)
        logger.log_security_event("UNAUTHORIZED_ACCESS", {"table": "admins"}, user="hacker", severity="CRITICAL")
        with open(path, "r") as f:
            content = f.read()
        assert "CRITICAL" in content
        assert "hacker" in content
        os.unlink(path)

    def test_audit_logger_log_validation_valid(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        logger = AuditLogger(log_file=path)
        logger.log_validation("SELECT * FROM users", True, "SAFE", "验证通过", user="test_user")
        with open(path, "r") as f:
            content = f.read()
        assert "VALIDATION" in content
        assert "True" in content
        os.unlink(path)

    def test_audit_logger_log_validation_invalid(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        logger = AuditLogger(log_file=path)
        logger.log_validation("DROP TABLE users", False, "CRITICAL", "包含危险操作", user="test_user")
        with open(path, "r") as f:
            content = f.read()
        assert "VALIDATION" in content
        assert "False" in content
        assert "CRITICAL" in content
        os.unlink(path)

    def test_audit_logger_log_error(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        logger = AuditLogger(log_file=path)
        logger.log_error("CONNECTION_ERROR", "Failed to connect to database", {"host": "localhost"}, user="test_user")
        with open(path, "r") as f:
            content = f.read()
        assert "ERROR" in content
        assert "CONNECTION_ERROR" in content
        os.unlink(path)

    def test_audit_logger_log_connection_success(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        logger = AuditLogger(log_file=path)
        logger.log_connection("CONNECT", "test_db", True, user="test_user")
        with open(path, "r") as f:
            content = f.read()
        assert "CONNECTION" in content
        assert "True" in content
        os.unlink(path)

    def test_audit_logger_log_connection_failure(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        logger = AuditLogger(log_file=path)
        logger.log_connection("CONNECT", "test_db", False, user="test_user")
        with open(path, "r") as f:
            content = f.read()
        assert "CONNECTION" in content
        assert "False" in content
        os.unlink(path)

    def test_audit_logger_creates_log_directory(self):
        fd, temp_path = tempfile.mkstemp()
        os.close(fd)
        log_dir = os.path.join(os.path.dirname(temp_path), "subdir", "logs")
        log_file = os.path.join(log_dir, "audit.log")
        logger = AuditLogger(log_file=log_file)
        logger.log_query("SELECT 1", "user", "success")
        assert os.path.exists(log_file)
        os.unlink(log_file)
        os.rmdir(log_dir)
