# 模块五：安全验证模块 - Phase 实现计划

## Phase 0: 概述

### 模块目标

确保 SQL 查询的安全性，防止：
- SQL 注入攻击
- 恶意数据操作（DROP、DELETE、UPDATE 等）
- 未授权的表/字段访问
- 敏感数据泄露

---

## Phase 1: SQL 安全验证 + 权限管理

### 目标

实现 SQLSecurityValidator 和 PermissionManager

### 文件

| 文件 | 描述 |
|------|------|
| `src/security/sql_validator.py` | SQL 安全验证器 |
| `src/security/permission_manager.py` | 权限管理器 |
| `config/security_policy.json` | 安全策略配置 |

### SQLSecurityValidator 实现

```python
# src/security/sql_validator.py
import re
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class ThreatLevel(Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    is_valid: bool
    threat_level: ThreatLevel
    message: str
    details: Dict = None

class SQLSecurityValidator:
    DANGEROUS_KEYWORDS = [
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", 
        "CREATE", "TRUNCATE", "EXEC", "EXECUTE", "GRANT",
        "REVOKE", "--", ";--", "/*", "*/", "xp_", "sp_"
    ]
    
    SUSPICIOUS_PATTERNS = [
        r"union\s+select",
        r"'\s+or\s+'1'\s*=\s*1",
        r"sleep\s*\(",
        r"benchmark\s*\(",
        r"load_file\s*\(",
        r"into\s+outfile",
    ]

    def __init__(
        self,
        allowed_tables: Optional[List[str]] = None,
        allowed_columns: Optional[Dict[str, List[str]]] = None
    ):
        self.allowed_tables = allowed_tables or []
        self.allowed_columns = allowed_columns or {}

    def validate(self, sql: str) -> ValidationResult:
        sql_upper = sql.upper()
        
        result = self._check_dangerous_keywords(sql_upper)
        if not result.is_valid:
            return result
        
        result = self._check_suspicious_patterns(sql)
        if not result.is_valid:
            return result
        
        result = self._check_table_whitelist(sql)
        if not result.is_valid:
            return result
        
        result = self._check_column_whitelist(sql)
        if not result.is_valid:
            return result
        
        result = self._check_read_only(sql_upper)
        if not result.is_valid:
            return result
        
        return ValidationResult(
            is_valid=True,
            threat_level=ThreatLevel.SAFE,
            message="验证通过"
        )

    def _check_dangerous_keywords(self, sql_upper: str) -> ValidationResult:
        for keyword in self.DANGEROUS_KEYWORDS:
            if keyword in sql_upper:
                return ValidationResult(
                    is_valid=False,
                    threat_level=ThreatLevel.CRITICAL,
                    message=f"包含危险关键字: {keyword}",
                    details={"keyword": keyword}
                )
        return ValidationResult(is_valid=True, threat_level=ThreatLevel.SAFE, message="")

    def _check_suspicious_patterns(self, sql: str) -> ValidationResult:
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                return ValidationResult(
                    is_valid=False,
                    threat_level=ThreatLevel.HIGH,
                    message=f"检测到可疑模式: {pattern}",
                    details={"pattern": pattern}
                )
        return ValidationResult(is_valid=True, threat_level=ThreatLevel.SAFE, message="")

    def _check_table_whitelist(self, sql: str) -> ValidationResult:
        if not self.allowed_tables:
            return ValidationResult(is_valid=True, threat_level=ThreatLevel.SAFE, message="")
        
        tables = self._extract_tables(sql)
        for table in tables:
            if table not in self.allowed_tables:
                return ValidationResult(
                    is_valid=False,
                    threat_level=ThreatLevel.HIGH,
                    message=f"未授权的表: {table}",
                    details={"table": table}
                )
        return ValidationResult(is_valid=True, threat_level=ThreatLevel.SAFE, message="")

    def _check_column_whitelist(self, sql: str) -> ValidationResult:
        if not self.allowed_columns:
            return ValidationResult(is_valid=True, threat_level=ThreatLevel.SAFE, message="")
        
        columns = self._extract_columns(sql)
        allowed = self._get_allowed_columns_for_query(sql)
        
        for column in columns:
            if allowed and column not in allowed:
                return ValidationResult(
                    is_valid=False,
                    threat_level=ThreatLevel.MEDIUM,
                    message=f"未授权的列: {column}",
                    details={"column": column}
                )
        return ValidationResult(is_valid=True, threat_level=ThreatLevel.SAFE, message="")

    def _check_read_only(self, sql_upper: str) -> ValidationResult:
        if not sql_upper.strip().startswith("SELECT"):
            return ValidationResult(
                is_valid=False,
                threat_level=ThreatLevel.HIGH,
                message="只允许 SELECT 查询"
            )
        return ValidationResult(is_valid=True, threat_level=ThreatLevel.SAFE, message="")

    def _extract_tables(self, sql: str) -> List[str]:
        tables = []
        patterns = [r"FROM\s+(\w+)", r"JOIN\s+(\w+)", r"INTO\s+(\w+)", r"UPDATE\s+(\w+)"]
        for pattern in patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            tables.extend(matches)
        return list(set(tables))

    def _extract_columns(self, sql: str) -> List[str]:
        columns = []
        pattern = r"SELECT\s+(.+?)\s+FROM"
        match = re.search(pattern, sql, re.IGNORECASE)
        if match:
            cols_str = match.group(1)
            if cols_str.strip() != "*":
                columns = [col.strip().split()[-1] for col in cols_str.split(",")]
        return columns

    def _get_allowed_columns_for_query(self, sql: str) -> List[str]:
        tables = self._extract_tables(sql)
        allowed = []
        for table in tables:
            if table in self.allowed_columns:
                allowed.extend(self.allowed_columns[table])
        return allowed
```

### PermissionManager 实现

```python
# src/security/permission_manager.py
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

class PermissionLevel(Enum):
    NONE = 0
    READ = 1
    WRITE = 2
    ADMIN = 3

@dataclass
class TablePermission:
    table_name: str
    permission_level: PermissionLevel
    allowed_columns: Optional[Set[str]] = None

class PermissionManager:
    def __init__(self):
        self.table_permissions: Dict[str, TablePermission] = {}

    def set_table_permission(
        self,
        table_name: str,
        permission_level: PermissionLevel,
        allowed_columns: Optional[List[str]] = None
    ):
        self.table_permissions[table_name] = TablePermission(
            table_name=table_name,
            permission_level=permission_level,
            allowed_columns=set(allowed_columns) if allowed_columns else None
        )

    def can_read_table(self, table_name: str) -> bool:
        perm = self.table_permissions.get(table_name)
        if not perm:
            return False
        return perm.permission_level >= PermissionLevel.READ

    def can_write_table(self, table_name: str) -> bool:
        perm = self.table_permissions.get(table_name)
        if not perm:
            return False
        return perm.permission_level >= PermissionLevel.WRITE

    def can_access_column(self, table_name: str, column: str) -> bool:
        perm = self.table_permissions.get(table_name)
        if not perm:
            return False
        if perm.allowed_columns is None:
            return True
        return column in perm.allowed_columns

    def load_from_config(self, config: Dict):
        for table, perms in config.items():
            level = PermissionLevel[perms.get("level", "READ")]
            columns = perms.get("columns")
            self.set_table_permission(table, level, columns)
```

### 配置文件

```json
// config/security_policy.json
{
    "read_only": true,
    "allowed_tables": ["orders", "products", "customers", "sales"],
    "column_permissions": {
        "customers": {
            "level": "READ",
            "columns": ["id", "name", "email", "created_at"]
        },
        "orders": {
            "level": "READ",
            "columns": null
        }
    },
    "dangerous_keywords": ["DROP", "DELETE", "UPDATE", "INSERT"],
    "sensitive_fields": ["password", "credit_card", "ssn"]
}
```

### 测试

```python
# tests/test_security_phase1.py
import pytest
from src.security.sql_validator import SQLSecurityValidator, ThreatLevel, ValidationResult
from src.security.permission_manager import PermissionManager, PermissionLevel

def test_sql_validator_init():
    validator = SQLSecurityValidator()
    assert validator is not None

def test_sql_validator_safe_query():
    validator = SQLSecurityValidator()
    result = validator.validate("SELECT * FROM users")
    assert result.is_valid is True

def test_sql_validator_dangerous_keywords():
    validator = SQLSecurityValidator()
    result = validator.validate("DROP TABLE users")
    assert result.is_valid is False
    assert result.threat_level == ThreatLevel.CRITICAL

def test_permission_manager_init():
    manager = PermissionManager()
    assert manager is not None

def test_permission_manager_set_permission():
    manager = PermissionManager()
    manager.set_table_permission("users", PermissionLevel.READ)
    assert manager.can_read_table("users") is True

def test_permission_manager_load_from_config():
    manager = PermissionManager()
    config = {"users": {"level": "READ", "columns": ["id", "name"]}}
    manager.load_from_config(config)
    assert manager.can_read_table("users") is True
```

---

## Phase 2: 敏感数据过滤 + SQL 注入检测

### 目标

实现 SensitiveDataFilter 和 SQLInjectionDetector

### 文件

| 文件 | 描述 |
|------|------|
| `src/security/sensitive_filter.py` | 敏感数据过滤器 |
| `src/security/injection_detector.py` | SQL 注入检测器 |

### SensitiveDataFilter 实现

```python
# src/security/sensitive_filter.py
from typing import List, Set, Dict

class SensitiveDataFilter:
    DEFAULT_SENSITIVE_PATTERNS = [
        "password", "passwd", "pwd",
        "secret", "token", "api_key", "apikey",
        "credit_card", "card_number", "cvv",
        "ssn", "social_security",
        "phone", "mobile", "tel",
        "email", "address", "birth",
        "id_card", "身份证"
    ]

    def __init__(
        self,
        sensitive_fields: List[str] = None,
        mask_char: str = "*"
    ):
        self.sensitive_fields = set(
            sensitive_fields or self.DEFAULT_SENSITIVE_PATTERNS
        )
        self.mask_char = mask_char

    def is_sensitive_column(self, column_name: str) -> bool:
        column_lower = column_name.lower()
        return any(
            pattern in column_lower 
            for pattern in self.sensitive_fields
        )

    def filter_result(
        self,
        result: List[Dict],
        columns: List[str]
    ) -> List[Dict]:
        sensitive_cols = [
            col for col in columns 
            if self.is_sensitive_column(col)
        ]
        
        if not sensitive_cols:
            return result
        
        filtered = []
        for row in result:
            filtered_row = {}
            for key, value in row.items():
                if key in sensitive_cols:
                    filtered_row[key] = self._mask_value(value)
                else:
                    filtered_row[key] = value
            filtered.append(filtered_row)
        
        return filtered

    def _mask_value(self, value: str, visible: int = 0) -> str:
        if not value:
            return ""
        value = str(value)
        if len(value) <= visible:
            return value
        return self.mask_char * (len(value) - visible) + value[-visible:]

    def add_sensitive_pattern(self, pattern: str):
        self.sensitive_fields.add(pattern.lower())
```

### SQLInjectionDetector 实现

```python
# src/security/injection_detector.py
import re
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class InjectionIndicator:
    pattern: str
    severity: str
    description: str

class SQLInjectionDetector:
    INJECTION_PATTERNS = [
        (r"'(\s*(--|#|/\*))", "HIGH", "注释注入"),
        (r"union\s+(all\s+)?select", "HIGH", "UNION 注入"),
        (r"or\s+['\"]?\d+\s*=\s*['\"]?\d+", "MEDIUM", "永真条件"),
        (r"or\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+", "MEDIUM", "永真条件"),
        (r"and\s+\d+\s*=\s*\d+", "MEDIUM", "布尔盲注"),
        (r"waitfor\s+delay", "HIGH", "时间盲注"),
        (r"sleep\s*\(\s*\d+\s*\)", "HIGH", "时间盲注"),
        (r"extractvalue\(", "MEDIUM", "XML 注入"),
        (r"updatexml\(", "MEDIUM", "XML 注入"),
    ]

    def detect(self, sql: str) -> Tuple[bool, List[InjectionIndicator]]:
        indicators = []
        
        for pattern, severity, description in self.INJECTION_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                indicators.append(InjectionIndicator(
                    pattern=pattern,
                    severity=severity,
                    description=description
                ))
        
        return len(indicators) == 0, indicators
```

### 测试

```python
# tests/test_security_phase2.py
import pytest
from src.security.sensitive_filter import SensitiveDataFilter
from src.security.injection_detector import SQLInjectionDetector, InjectionIndicator

def test_sensitive_filter_init():
    filter = SensitiveDataFilter()
    assert filter is not None

def test_sensitive_filter_is_sensitive():
    filter = SensitiveDataFilter()
    assert filter.is_sensitive_column("password") is True
    assert filter.is_sensitive_column("name") is False

def test_sensitive_filter_mask_value():
    filter = SensitiveDataFilter()
    result = filter._mask_value("123456", visible=2)
    assert result == "****56"

def test_sensitive_filter_filter_result():
    filter = SensitiveDataFilter()
    result = [{"name": "John", "password": "secret"}]
    filtered = filter.filter_result(result, ["name", "password"])
    assert filtered[0]["password"] != "secret"

def test_injection_detector_init():
    detector = SQLInjectionDetector()
    assert detector is not None

def test_injection_detector_safe():
    detector = SQLInjectionDetector()
    is_safe, indicators = detector.detect("SELECT * FROM users")
    assert is_safe is True
    assert len(indicators) == 0

def test_injection_detector_union():
    detector = SQLInjectionDetector()
    is_safe, indicators = detector.detect("SELECT * FROM users UNION SELECT * FROM admins")
    assert is_safe is False
    assert len(indicators) > 0
```

---

## Phase 3: 审计日志

### 目标

实现 AuditLogger

### 文件

| 文件 | 描述 |
|------|------|
| `src/security/audit_logger.py` | 审计日志 |

### AuditLogger 实现

```python
# src/security/audit_logger.py
import logging
from datetime import datetime
from typing import Dict, Any, Optional

class AuditLogger:
    def __init__(self, log_file: str = "logs/audit.log"):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler(log_file)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s"
            )
        )
        self.logger.addHandler(handler)
    
    def log_query(
        self,
        sql: str,
        user: str,
        result: str,
        validation_result: Any = None
    ):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "sql": sql,
            "result": "success" if result else "failed",
            "validation": validation_result.message if validation_result else "N/A"
        }
        
        self.logger.info(f"QUERY: {log_entry}")
    
    def log_security_event(
        self,
        event_type: str,
        details: Dict[str, Any]
    ):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details
        }
        
        self.logger.warning(f"SECURITY: {log_entry}")
```

### 测试

```python
# tests/test_security_phase3.py
import pytest
import tempfile
import os
from src.security.audit_logger import AuditLogger

def test_audit_logger_init():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    logger = AuditLogger(log_file=path)
    assert logger is not None
    os.unlink(path)

def test_audit_logger_log_query():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    logger = AuditLogger(log_file=path)
    logger.log_query("SELECT * FROM users", "test_user", "success")
    os.unlink(path)

def test_audit_logger_log_security_event():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    logger = AuditLogger(log_file=path)
    logger.log_security_event("INTRUSION", {"ip": "192.168.1.1"})
    os.unlink(path)
```

---

## 项目结构

```
src/
├── security/
│   ├── __init__.py
│   ├── sql_validator.py        # Phase 1
│   ├── permission_manager.py   # Phase 1
│   ├── sensitive_filter.py    # Phase 2
│   ├── injection_detector.py  # Phase 2
│   └── audit_logger.py        # Phase 3
```

---

## 实现步骤

| Phase | 任务 | 优先级 |
|-------|------|--------|
| 1 | SQLSecurityValidator + PermissionManager | P0 |
| 2 | SensitiveDataFilter + InjectionDetector | P1 |
| 3 | AuditLogger | P1 |

---

## 安全策略配置

```json
{
    "read_only": true,
    "allowed_tables": ["orders", "products", "customers", "sales"],
    "column_permissions": {
        "customers": {
            "level": "READ",
            "columns": ["id", "name", "email", "created_at"]
        }
    },
    "dangerous_keywords": ["DROP", "DELETE", "UPDATE", "INSERT"],
    "sensitive_fields": ["password", "credit_card", "ssn"]
}
```
