from typing import Tuple, List


class SQLValidator:
    DANGEROUS_KEYWORDS = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']

    def __init__(self, custom_dangerous_keywords: List[str] = None):
        if custom_dangerous_keywords:
            self.DANGEROUS_KEYWORDS = self.DANGEROUS_KEYWORDS + custom_dangerous_keywords

    def validate(self, sql: str) -> Tuple[bool, str]:
        sql = sql.strip().upper()

        for keyword in self.DANGEROUS_KEYWORDS:
            if keyword in sql:
                return False, f"包含危险操作: {keyword}"

        if not sql.startswith('SELECT'):
            return False, "只支持 SELECT 查询"

        return True, "验证通过"

    def validate_with_fix(self, sql: str) -> Tuple[bool, str, str]:
        is_valid, message = self.validate(sql)
        if is_valid:
            return True, message, sql

        fixed_sql = sql
        for keyword in self.DANGEROUS_KEYWORDS:
            fixed_sql = fixed_sql.replace(keyword, "")

        is_valid_fixed, message_fixed = self.validate(fixed_sql)
        return is_valid_fixed, message_fixed, fixed_sql if is_valid_fixed else sql

    def is_select_only(self, sql: str) -> bool:
        return sql.strip().upper().startswith('SELECT')

    def contains_dangerous_keyword(self, sql: str) -> bool:
        sql_upper = sql.strip().upper()
        return any(keyword in sql_upper for keyword in self.DANGEROUS_KEYWORDS)
