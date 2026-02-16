from typing import Tuple, Dict
import re


class ErrorAnalyzer:
    ERROR_PATTERNS = {
        "syntax": [
            r"syntax error",
            r"near .*",
            r"unexpected .*"
        ],
        "no_table": [
            r"no such table",
            r"table .* doesn't exist"
        ],
        "no_column": [
            r"no such column",
            r"column .* not found"
        ],
        "type_mismatch": [
            r"cannot convert",
            r"type mismatch"
        ],
        "constraint": [
            r"UNIQUE constraint",
            r"FOREIGN KEY constraint",
            r"NOT NULL constraint"
        ]
    }

    def analyze(self, error_msg: str) -> Tuple[str, Dict]:
        error_msg_lower = error_msg.lower()

        for error_type, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, error_msg_lower, re.IGNORECASE):
                    return error_type, self._get_suggestion(error_type)

        return "unknown", {"message": "未知错误类型", "fix_suggestion": "请检查 SQL 语法"}

    def _get_suggestion(self, error_type: str) -> Dict:
        suggestions = {
            "syntax": {
                "message": "SQL 语法错误",
                "fix_suggestion": "检查关键字拼写、括号匹配、引号使用"
            },
            "no_table": {
                "message": "表不存在",
                "fix_suggestion": "确认表名是否正确，检查 Schema"
            },
            "no_column": {
                "message": "列不存在",
                "fix_suggestion": "确认字段名是否正确，注意大小写"
            },
            "type_mismatch": {
                "message": "数据类型不匹配",
                "fix_suggestion": "检查字段类型，确保类型转换正确"
            },
            "constraint": {
                "message": "约束冲突",
                "fix_suggestion": "检查数据是否违反约束条件"
            }
        }
        return suggestions.get(error_type, {})


class RetryStrategy:
    IMMEDIATE = "immediate"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"


class RetryConfig:
    def __init__(
        self,
        max_retries: int = 3,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        base_delay: float = 1.0,
        max_delay: float = 10.0
    ):
        self.max_retries = max_retries
        self.strategy = strategy
        self.base_delay = base_delay
        self.max_delay = max_delay

    def get_delay(self, attempt: int) -> float:
        if self.strategy == RetryStrategy.IMMEDIATE:
            return 0

        if self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * attempt
        else:
            delay = self.base_delay * (2 ** attempt)

        return min(delay, self.max_delay)
