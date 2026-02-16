import re
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class InjectionIndicator:
    pattern: str
    severity: str
    description: str


class SQLInjectionDetector:
    INJECTION_PATTERNS = [
        (r"'(\s*(--|#|/\*))", "HIGH", "注释注入"),
        (r"\s--(\s|$)", "HIGH", "注释注入"),
        (r"\s#(\s|$)", "HIGH", "注释注入"),
        (r"union\s+(all\s+)?select", "HIGH", "UNION 注入"),
        (r"or\s+['\"]?\d+\s*=\s*['\"]?\d+", "MEDIUM", "永真条件"),
        (r"or\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+", "MEDIUM", "永真条件"),
        (r"and\s+\d+\s*=\s*\d+", "MEDIUM", "布尔盲注"),
        (r"waitfor\s+delay", "HIGH", "时间盲注"),
        (r"sleep\s*\(\s*\d+\s*\)", "HIGH", "时间盲注"),
        (r"extractvalue\(", "MEDIUM", "XML 注入"),
        (r"updatexml\(", "MEDIUM", "XML 注入"),
    ]

    def __init__(self, custom_patterns: Optional[List[Tuple[str, str, str]]] = None):
        self.patterns = custom_patterns or self.INJECTION_PATTERNS

    def detect(self, sql: str) -> Tuple[bool, List[InjectionIndicator]]:
        indicators = []

        for pattern, severity, description in self.patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                indicators.append(InjectionIndicator(
                    pattern=pattern,
                    severity=severity,
                    description=description
                ))

        return len(indicators) == 0, indicators

    def is_safe(self, sql: str) -> bool:
        safe, _ = self.detect(sql)
        return safe

    def get_indicators(self, sql: str) -> List[InjectionIndicator]:
        _, indicators = self.detect(sql)
        return indicators

    def add_pattern(self, pattern: str, severity: str, description: str):
        self.patterns.append((pattern, severity, description))

    def remove_pattern(self, pattern: str):
        self.patterns = [p for p in self.patterns if p[0] != pattern]

    def get_high_severity_indicators(self, sql: str) -> List[InjectionIndicator]:
        _, indicators = self.detect(sql)
        return [ind for ind in indicators if ind.severity == "HIGH"]

    def has_high_severity(self, sql: str) -> bool:
        return len(self.get_high_severity_indicators(sql)) > 0
