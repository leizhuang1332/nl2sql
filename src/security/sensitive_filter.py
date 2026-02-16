from typing import List, Set, Dict, Any, Optional


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
        sensitive_fields: Optional[List[str]] = None,
        mask_char: str = "*",
        visible_chars: int = 0
    ):
        self.sensitive_fields: Set[str] = set(
            sensitive_fields or self.DEFAULT_SENSITIVE_PATTERNS
        )
        self.mask_char = mask_char
        self.visible_chars = visible_chars

    def is_sensitive_column(self, column_name: str) -> bool:
        column_lower = column_name.lower()
        return any(
            pattern in column_lower
            for pattern in self.sensitive_fields
        )

    def filter_result(
        self,
        result: List[Dict[str, Any]],
        columns: List[str]
    ) -> List[Dict[str, Any]]:
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

    def _mask_value(self, value: Any) -> str:
        if value is None:
            return ""
        str_value = str(value)
        visible = self.visible_chars
        if visible > 0:
            visible = min(visible, len(str_value))
            return self.mask_char * (len(str_value) - visible) + str_value[-visible:]
        return self.mask_char * len(str_value)

    def add_sensitive_pattern(self, pattern: str):
        self.sensitive_fields.add(pattern.lower())

    def remove_sensitive_pattern(self, pattern: str):
        self.sensitive_fields.discard(pattern.lower())

    def get_sensitive_patterns(self) -> Set[str]:
        return self.sensitive_fields.copy()

    def filter_columns(self, columns: List[str]) -> List[str]:
        return [col for col in columns if self.is_sensitive_column(col)]

    def filter_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        filtered = {}
        for key, value in row.items():
            if self.is_sensitive_column(key):
                filtered[key] = self._mask_value(value)
            else:
                filtered[key] = value
        return filtered
