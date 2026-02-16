from typing import Optional, Tuple


class TimeParser:
    def __init__(self):
        self.patterns = {}

    def parse(self, expression: str) -> Optional[Tuple[str, str]]:
        expression = expression.strip()

        mappings = {
            "今天": ("DATE('now')", "DATE('now')"),
            "昨天": ("DATE('now', '-1 day')", "DATE('now', '-1 day')"),
            "前天": ("DATE('now', '-2 days')", "DATE('now', '-2 days')"),
            "明天": ("DATE('now', '+1 day')", "DATE('now', '+1 day')"),
            "最近7天": ("DATE('now', '-7 days')", "DATE('now')"),
            "最近30天": ("DATE('now', '-30 days')", "DATE('now')"),
            "本月": ("DATE('now', 'start of month')", "DATE('now')"),
            "上月": ("DATE('now', 'start of month', '-1 month')", "DATE('now', 'start of month', '-1 month')"),
        }

        return mappings.get(expression)

    def parse_range(self, expression: str) -> Optional[dict]:
        result = self.parse(expression)
        if result:
            return {"start": result[0], "end": result[1]}
        return None
