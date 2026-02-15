# 模块五：安全验证模块 - 详细实现计划

## 5.1 模块目标

确保 SQL 查询的安全性，防止：
- SQL 注入攻击
- 恶意数据操作（DROP、DELETE、UPDATE 等）
- 未授权的表/字段访问
- 敏感数据泄露

---

## 5.2 核心功能设计

### 5.2.1 SQL 安全验证器

```python
# src/security/sql_validator.py
import re
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class ThreatLevel(Enum):
    """威胁等级"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    threat_level: ThreatLevel
    message: str
    details: Dict = None

class SQLSecurityValidator:
    """SQL 安全验证器"""
    
    # 危险关键字
    DANGEROUS_KEYWORDS = [
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", 
        "CREATE", "TRUNCATE", "EXEC", "EXECUTE", "GRANT",
        "REVOKE", "--", ";--", "/*", "*/", "xp_", "sp_"
    ]
    
    # 可疑模式
    SUSPICIOUS_PATTERNS = [
        r"union\s+select",      # UNION 注入
        r"'\s+or\s+'1'\s*=\s*1",  # 永真条件
        r"sleep\s*\(",          # 时间盲注
        r"benchmark\s*\(",     # 性能注入
        r"load_file\s*\(",      # 文件读取
        r"into\s+outfile",      # 文件写入
    ]
    
    def __init__(
        self,
        allowed_tables: Optional[List[str]] = None,
        allowed_columns: Optional[Dict[str, List[str]]] = None
    ):
        self.allowed_tables = allowed_tables or []
        self.allowed_columns = allowed_columns or {}
    
    def validate(self, sql: str) -> ValidationResult:
        """
        全面验证 SQL 安全性
        """
        sql_upper = sql.upper()
        
        # 1. 检查危险关键字
        result = self._check_dangerous_keywords(sql_upper)
        if not result.is_valid:
            return result
        
        # 2. 检查可疑模式
        result = self._check_suspicious_patterns(sql)
        if not result.is_valid:
            return result
        
        # 3. 检查表名白名单
        result = self._check_table_whitelist(sql)
        if not result.is_valid:
            return result
        
        # 4. 检查列名白名单
        result = self._check_column_whitelist(sql)
        if not result.is_valid:
            return result
        
        # 5. 检查只读权限
        result = self._check_read_only(sql_upper)
        if not result.is_valid:
            return result
        
        return ValidationResult(
            is_valid=True,
            threat_level=ThreatLevel.SAFE,
            message="验证通过"
        )
    
    def _check_dangerous_keywords(self, sql_upper: str) -> ValidationResult:
        """检查危险关键字"""
        for keyword in self.DANGEROUS_KEYWORDS:
            if keyword in sql_upper:
                return ValidationResult(
                    is_valid=False,
                    threat_level=ThreatLevel.CRITICAL,
                    message=f"包含危险关键字: {keyword}",
                    details={"keyword": keyword}
                )
        return ValidationResult(
            is_valid=True,
            threat_level=ThreatLevel.SAFE,
            message=""
        )
    
    def _check_suspicious_patterns(self, sql: str) -> ValidationResult:
        """检查可疑模式"""
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                return ValidationResult(
                    is_valid=False,
                    threat_level=ThreatLevel.HIGH,
                    message=f"检测到可疑模式: {pattern}",
                    details={"pattern": pattern}
                )
        return ValidationResult(
            is_valid=True,
            threat_level=ThreatLevel.SAFE,
            message=""
        )
    
    def _check_table_whitelist(self, sql: str) -> ValidationResult:
        """检查表名白名单"""
        if not self.allowed_tables:
            return ValidationResult(
                is_valid=True,
                threat_level=ThreatLevel.SAFE,
                message=""
            )
        
        # 提取 SQL 中的表名（简化实现）
        tables = self._extract_tables(sql)
        
        for table in tables:
            if table not in self.allowed_tables:
                return ValidationResult(
                    is_valid=False,
                    threat_level=ThreatLevel.HIGH,
                    message=f"未授权的表: {table}",
                    details={"table": table}
                )
        
        return ValidationResult(
            is_valid=True,
            threat_level=ThreatLevel.SAFE,
            message=""
        )
    
    def _check_column_whitelist(self, sql: str) -> ValidationResult:
        """检查列名白名单"""
        if not self.allowed_columns:
            return ValidationResult(
                is_valid=True,
                threat_level=ThreatLevel.SAFE,
                message=""
            )
        
        # 提取 SQL 中的列名
        columns = self._extract_columns(sql)
        
        for column in columns:
            # 获取该表允许的列
            allowed = self._get_allowed_columns_for_query(sql)
            if allowed and column not in allowed:
                return ValidationResult(
                    is_valid=False,
                    threat_level=ThreatLevel.MEDIUM,
                    message=f"未授权的列: {column}",
                    details={"column": column}
                )
        
        return ValidationResult(
            is_valid=True,
            threat_level=ThreatLevel.SAFE,
            message=""
        )
    
    def _check_read_only(self, sql_upper: str) -> ValidationResult:
        """检查是否只读"""
        if not sql_upper.strip().startswith("SELECT"):
            return ValidationResult(
                is_valid=False,
                threat_level=ThreatLevel.HIGH,
                message="只允许 SELECT 查询"
            )
        return ValidationResult(
            is_valid=True,
            threat_level=ThreatLevel.SAFE,
            message=""
        )
    
    def _extract_tables(self, sql: str) -> List[str]:
        """提取 SQL 中的表名（简化实现）"""
        tables = []
        # 匹配 FROM 和 JOIN 后的表名
        patterns = [
            r"FROM\s+(\w+)",
            r"JOIN\s+(\w+)",
            r"INTO\s+(\w+)",
            r"UPDATE\s+(\w+)"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            tables.extend(matches)
        
        return list(set(tables))
    
    def _extract_columns(self, sql: str) -> List[str]:
        """提取 SQL 中的列名（简化实现）"""
        columns = []
        # 匹配 SELECT 后的列名
        pattern = r"SELECT\s+(.+?)\s+FROM"
        match = re.search(pattern, sql, re.IGNORECASE)
        
        if match:
            cols_str = match.group(1)
            if cols_str.strip() == "*":
                return []  # SELECT * 不检查具体列
            
            # 分割列名
            columns = [
                col.strip().split()[-1] 
                for col in cols_str.split(",")
            ]
        
        return columns
    
    def _get_allowed_columns_for_query(self, sql: str) -> List[str]:
        """根据查询确定允许的列"""
        tables = self._extract_tables(sql)
        
        allowed = []
        for table in tables:
            if table in self.allowed_columns:
                allowed.extend(self.allowed_columns[table])
        
        return allowed
```

### 5.2.2 查询权限管理器

```python
# src/security/permission_manager.py
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

class PermissionLevel(Enum):
    """权限等级"""
    NONE = 0
    READ = 1
    WRITE = 2
    ADMIN = 3

@dataclass
class TablePermission:
    """表权限"""
    table_name: str
    permission_level: PermissionLevel
    allowed_columns: Optional[Set[str]] = None

class PermissionManager:
    """权限管理器"""
    
    def __init__(self):
        self.table_permissions: Dict[str, TablePermission] = {}
    
    def set_table_permission(
        self,
        table_name: str,
        permission_level: PermissionLevel,
        allowed_columns: Optional[List[str]] = None
    ):
        """设置表权限"""
        self.table_permissions[table_name] = TablePermission(
            table_name=table_name,
            permission_level=permission_level,
            allowed_columns=set(allowed_columns) if allowed_columns else None
        )
    
    def can_read_table(self, table_name: str) -> bool:
        """检查是否可读"""
        perm = self.table_permissions.get(table_name)
        if not perm:
            return False
        return perm.permission_level >= PermissionLevel.READ
    
    def can_write_table(self, table_name: str) -> bool:
        """检查是否可写"""
        perm = self.table_permissions.get(table_name)
        if not perm:
            return False
        return perm.permission_level >= PermissionLevel.WRITE
    
    def can_access_column(self, table_name: str, column: str) -> bool:
        """检查是否可访问列"""
        perm = self.table_permissions.get(table_name)
        if not perm:
            return False
        
        if perm.allowed_columns is None:
            return True  # 没有列限制
        
        return column in perm.allowed_columns
    
    def load_from_config(self, config: Dict):
        """从配置加载权限"""
        for table, perms in config.items():
            level = PermissionLevel[perms.get("level", "READ")]
            columns = perms.get("columns")
            self.set_table_permission(table, level, columns)
```

### 5.2.3 敏感数据过滤器

```python
# src/security/sensitive_filter.py
from typing import List, Set, Dict
import re

class SensitiveDataFilter:
    """敏感数据过滤器"""
    
    # 默认敏感字段模式
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
        """判断是否为敏感列"""
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
        """过滤结果中的敏感数据"""
        sensitive_cols = [
            col for col in columns 
            if self.is_sensitive_column(col)
        ]
        
        if not sensitive_cols:
            return result
        
        # 过滤敏感列
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
        """遮蔽敏感值"""
        if not value:
            return ""
        
        value = str(value)
        if len(value) <= visible:
            return value
        
        return self.mask_char * (len(value) - visible) + value[-visible:]
    
    def add_sensitive_pattern(self, pattern: str):
        """添加敏感字段模式"""
        self.sensitive_fields.add(pattern.lower())
```

---

## 5.3 高级功能

### 5.3.1 SQL 注入检测器

```python
# src/security/injection_detector.py
import re
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class InjectionIndicator:
    """注入指标"""
    pattern: str
    severity: str
    description: str

class SQLInjectionDetector:
    """SQL 注入检测器"""
    
    # 注入检测模式
    INJECTION_PATTERNS = [
        # 注释注入
        (r"'(\s*(--|#|/\*))", "HIGH", "注释注入"),
        
        # UNION 注入
        (r"union\s+(all\s+)?select", "HIGH", "UNION 注入"),
        
        # 永真条件
        (r"or\s+['\"]?\d+\s*=\s*['\"]?\d+", "MEDIUM", "永真条件"),
        (r"or\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+", "MEDIUM", "永真条件"),
        
        # 布尔盲注
        (r"and\s+\d+\s*=\s*\d+", "MEDIUM", "布尔盲注"),
        
        # 时间盲注
        (r"waitfor\s+delay", "HIGH", "时间盲注"),
        (r"sleep\s*\(\s*\d+\s*\)", "HIGH", "时间盲注"),
        
        # 错误注入
        (r"extractvalue\(", "MEDIUM", "XML 注入"),
        (r"updatexml\(", "MEDIUM", "XML 注入"),
    ]
    
    def detect(self, sql: str) -> Tuple[bool, List[InjectionIndicator]]:
        """
        检测 SQL 注入
        返回：(是否安全, 指标列表)
        """
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

### 5.3.2 审计日志

```python
# src/security/audit_logger.py
import logging
from datetime import datetime
from typing import Dict, Any, Optional

class AuditLogger:
    """审计日志"""
    
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
        """记录查询日志"""
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
        """记录安全事件"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details
        }
        
        self.logger.warning(f"SECURITY: {log_entry}")
```

---

## 5.4 项目结构

```
src/
├── security/
│   ├── __init__.py
│   ├── sql_validator.py        # SQL 验证器
│   ├── permission_manager.py    # 权限管理
│   ├── sensitive_filter.py      # 敏感数据过滤
│   ├── injection_detector.py    # 注入检测
│   └── audit_logger.py          # 审计日志
```

---

## 5.5 实现步骤

| 步骤 | 任务 | 优先级 |
|------|------|--------|
| 1 | 实现 SQLSecurityValidator 基础验证 | P0 |
| 2 | 实现权限管理器 | P0 |
| 3 | 实现敏感数据过滤器 | P1 |
| 4 | 实现注入检测器 | P1 |
| 5 | 实现审计日志 | P1 |
| 6 | 配置安全策略 | P1 |
| 7 | 集成测试 | P0 |

---

## 5.6 安全策略配置

```python
# config/security_policy.py

# 安全策略配置示例
SECURITY_POLICY = {
    # 只读模式
    "read_only": True,
    
    # 允许的表
    "allowed_tables": [
        "orders",
        "products", 
        "customers",
        "sales"
    ],
    
    # 表级列权限
    "column_permissions": {
        "customers": {
            "level": "READ",
            "columns": ["id", "name", "email", "created_at"]
        },
        "orders": {
            "level": "READ", 
            "columns": None  # 所有列
        }
    },
    
    # 危险关键字
    "dangerous_keywords": [
        "DROP", "DELETE", "UPDATE", "INSERT"
    ],
    
    # 敏感字段
    "sensitive_fields": [
        "password", "credit_card", "ssn"
    ]
}
```

---

## 5.7 潜在挑战与解决方案

| 挑战 | 解决方案 |
|------|----------|
| 绕过检测的 SQL | 定期更新检测模式 + 行为分析 |
| 复杂查询验证困难 | 使用 SQL 解析器而非正则 |
| 性能与安全平衡 | 分层验证 + 缓存白名单 |
| 误拦截正常查询 | 支持配置例外规则 |
