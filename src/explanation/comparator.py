import statistics
from typing import Any, Dict, List, Optional


class ComparisonAnalyzer:
    def compare(
        self,
        current: List[Dict],
        previous: List[Dict],
        question: str
    ) -> str:
        if not current or not previous:
            return "数据不足，无法对比"

        current_stats = self._basic_stats(current)
        previous_stats = self._basic_stats(previous)

        current_numeric = self._numeric_stats(current)
        previous_numeric = self._numeric_stats(previous)

        lines = []
        lines.append(f"当前数据：{current_stats}")
        lines.append(f"上期数据：{previous_stats}")

        if current_numeric and previous_numeric:
            for col in current_numeric:
                if col in previous_numeric:
                    curr = current_numeric[col]
                    prev = previous_numeric[col]

                    if prev != 0:
                        change = ((curr - prev) / prev) * 100
                        trend = "↑" if change > 0 else "↓" if change < 0 else "→"
                        lines.append(
                            f"{col}: {curr:.2f} vs {prev:.2f} ({trend} {abs(change):.1f}%)"
                        )

        return "\n".join(lines)

    def _basic_stats(self, data: List[Dict]) -> str:
        if not data:
            return "0 条"
        return f"{len(data)} 条"

    def _numeric_stats(self, data: List[Dict]) -> Dict[str, float]:
        if not data:
            return {}

        numeric_cols = []
        for col, value in data[0].items():
            if self._is_numeric(value):
                numeric_cols.append(col)

        result = {}
        for col in numeric_cols:
            values = [row[col] for row in data if row.get(col) is not None]
            if values:
                try:
                    numeric_values = [float(v) for v in values]
                    result[col] = sum(numeric_values)
                except (ValueError, TypeError):
                    pass

        return result

    def _is_numeric(self, value: Any) -> bool:
        if value is None:
            return False
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def get_comparison_dict(
        self,
        current: List[Dict],
        previous: List[Dict]
    ) -> Dict[str, Any]:
        if not current or not previous:
            return {"error": "数据不足"}

        current_count = len(current)
        previous_count = len(previous)

        current_numeric = self._numeric_stats(current)
        previous_numeric = self._numeric_stats(previous)

        comparisons = {}
        for col in current_numeric:
            if col in previous_numeric:
                curr = current_numeric[col]
                prev = previous_numeric[col]
                if prev != 0:
                    change = ((curr - prev) / prev) * 100
                    comparisons[col] = {
                        "current": curr,
                        "previous": prev,
                        "change_percent": change,
                        "trend": "up" if change > 0 else "down" if change < 0 else "flat"
                    }

        return {
            "current_count": current_count,
            "previous_count": previous_count,
            "count_change": ((current_count - previous_count) / previous_count * 100) if previous_count else 0,
            "numeric_comparisons": comparisons
        }
