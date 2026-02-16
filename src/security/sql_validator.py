import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class ThreatLevel(Enum):
    """威胁等级枚举"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """验证结果数据类"""
    is_valid: bool
    threat_level: ThreatLevel
    message: str
    details: Dict = field(default_factory=dict)


class SQLSecurityValidator:
    """SQL 安全验证器"""
    
    DANGEROUS_KEYWORDS = [
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
        "CREATE", "TRUNCATE", "EXEC", "EXECUTE", "GRANT",
        "REVOKE", "--", ";--", "/*", "*/", "xp_", "sp_"
    ]
    
    SUSPICIOUS_PATTERNS = [
        r"union\s+select",
        r"or\s+['\"]?\d+\s*=\s*['\"]?\d+",
        r"or\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+",
        r"sleep\s*\(",
        r"benchmark\s*\(",
        r"load_file\s*\(",
        r"into\s+outfile",
    ]

    def __init__(
        self,
        allowed_tables: Optional[List[str]] = None,
        allowed_columns: Optional[Dict[str, List[str]]] = None,
        read_only: bool = True
    ):
        """
        初始化 SQL 安全验证器
        
        Args:
            allowed_tables: 允许访问的表列表
            allowed_columns: 允许访问的列字典 {table_name: [columns]}
            read_only: 是否只允许 SELECT 查询
        """
        self.allowed_tables = allowed_tables or []
        self.allowed_columns = allowed_columns or {}
        self.read_only = read_only

    def validate(self, sql: str) -> ValidationResult:
        """
        验证 SQL 安全性
        
        Args:
            sql: 要验证的 SQL 语句
            
        Returns:
            ValidationResult: 验证结果
        """
        if not sql or not sql.strip():
            return ValidationResult(
                is_valid=False,
                threat_level=ThreatLevel.CRITICAL,
                message="SQL 语句为空"
            )
        
        sql_upper = sql.upper()
        
        # 检查危险关键字
        result = self._check_dangerous_keywords(sql_upper)
        if not result.is_valid:
            return result
        
        # 检查可疑模式
        result = self._check_suspicious_patterns(sql)
        if not result.is_valid:
            return result
        
        # 检查表白名单
        result = self._check_table_whitelist(sql)
        if not result.is_valid:
            return result
        
        # 检查列白名单
        result = self._check_column_whitelist(sql)
        if not result.is_valid:
            return result
        
        # 检查只读模式
        if self.read_only:
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
        return ValidationResult(is_valid=True, threat_level=ThreatLevel.SAFE, message="")

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
        return ValidationResult(is_valid=True, threat_level=ThreatLevel.SAFE, message="")

    def _check_table_whitelist(self, sql: str) -> ValidationResult:
        """检查表白名单"""
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
        """检查列白名单"""
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
        """检查只读模式"""
        if not sql_upper.strip().startswith("SELECT"):
            return ValidationResult(
                is_valid=False,
                threat_level=ThreatLevel.HIGH,
                message="只允许 SELECT 查询"
            )
        return ValidationResult(is_valid=True, threat_level=ThreatLevel.SAFE, message="")

    def _extract_tables(self, sql: str) -> List[str]:
        """从 SQL 中提取表名"""
        tables = []
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
        """从 SQL 中提取列名"""
        columns = []
        pattern = r"SELECT\s+(.+?)\s+FROM"
        match = re.search(pattern, sql, re.IGNORECASE)
        if match:
            cols_str = match.group(1)
            if cols_str.strip() != "*":
                columns = [col.strip().split()[-1] for col in cols_str.split(",")]
        return columns

    def _get_allowed_columns_for_query(self, sql: str) -> List[str]:
        """获取查询允许的列"""
        tables = self._extract_tables(sql)
        allowed = []
        for table in tables:
            if table in self.allowed_columns:
                allowed.extend(self.allowed_columns[table])
        return allowed
