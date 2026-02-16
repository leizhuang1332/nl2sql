import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class AuditLogger:
    def __init__(
        self,
        log_file: str = "logs/audit.log",
        log_level: int = logging.INFO,
        max_file_size: int = 10 * 1024 * 1024,
        backup_count: int = 5
    ):
        self.log_file = log_file
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(log_level)
        self.logger.handlers.clear()

        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        )
        self.logger.addHandler(file_handler)

    def log_query(
        self,
        sql: str,
        user: str,
        result: str,
        validation_result: Optional[Any] = None,
        duration_ms: Optional[float] = None
    ):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "QUERY",
            "user": user,
            "sql": sql,
            "result": result,
            "validation": validation_result.message if validation_result else "N/A",
            "duration_ms": duration_ms
        }
        self.logger.info(f"QUERY: {log_entry}")

    def log_security_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        user: Optional[str] = None,
        severity: str = "WARNING"
    ):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "SECURITY",
            "event_type": event_type,
            "user": user,
            "severity": severity,
            "details": details
        }
        self.logger.warning(f"SECURITY: {log_entry}")

    def log_validation(
        self,
        sql: str,
        is_valid: bool,
        threat_level: str,
        message: str,
        user: Optional[str] = None
    ):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "VALIDATION",
            "user": user,
            "sql": sql,
            "is_valid": is_valid,
            "threat_level": threat_level,
            "message": message
        }
        if is_valid:
            self.logger.info(f"VALIDATION: {log_entry}")
        else:
            self.logger.warning(f"VALIDATION: {log_entry}")

    def log_error(
        self,
        error_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user: Optional[str] = None
    ):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "ERROR",
            "error_type": error_type,
            "message": message,
            "details": details or {},
            "user": user
        }
        self.logger.error(f"ERROR: {log_entry}")

    def log_connection(
        self,
        action: str,
        db_name: str,
        success: bool,
        user: Optional[str] = None
    ):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "CONNECTION",
            "action": action,
            "db_name": db_name,
            "success": success,
            "user": user
        }
        if success:
            self.logger.info(f"CONNECTION: {log_entry}")
        else:
            self.logger.warning(f"CONNECTION: {log_entry}")
