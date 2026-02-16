import statistics
from typing import Any, Dict, List, Optional


class DataAnalyst:
    def analyze(self, result: List[Dict]) -> Dict[str, Any]:
        if not result:
            return {"error": "无数据"}

        numeric_columns = self._extract_numeric_columns(result)

        analysis = {
            "row_count": len(result),
            "column_count": len(result[0]) if result else 0,
            "numeric_analysis": {}
        }

        for col in numeric_columns:
            values = [row[col] for row in result if row.get(col) is not None]

            if values:
                try:
                    numeric_values = [float(v) for v in values]

                    analysis["numeric_analysis"][col] = {
                        "sum": sum(numeric_values),
                        "avg": statistics.mean(numeric_values),
                        "min": min(numeric_values),
                        "max": max(numeric_values),
                        "count": len(numeric_values)
                    }
                except (ValueError, TypeError):
                    pass

        return analysis

    def _extract_numeric_columns(self, result: List[Dict]) -> List[str]:
        if not result:
            return []

        numeric_cols = []

        for col, value in result[0].items():
            if self._is_numeric(value):
                numeric_cols.append(col)

        return numeric_cols

    def _is_numeric(self, value: Any) -> bool:
        if value is None:
            return False
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def calculate_trend(
        self,
        current: List[Dict],
        previous: List[Dict],
        metric_column: str
    ) -> Dict[str, Any]:
        current_values = [row[metric_column] for row in current if metric_column in row and row[metric_column] is not None]
        previous_values = [row[metric_column] for row in previous if metric_column in row and row[metric_column] is not None]

        if not current_values or not previous_values:
            return {"error": "数据不足"}

        try:
            current_sum = sum(float(v) for v in current_values)
            previous_sum = sum(float(v) for v in previous_values)
        except (ValueError, TypeError):
            return {"error": "数据格式错误"}

        if previous_sum == 0:
            change = 0.0
        else:
            change = ((current_sum - previous_sum) / previous_sum) * 100

        return {
            "current": current_sum,
            "previous": previous_sum,
            "change": change,
            "trend": "up" if change > 0 else "down" if change < 0 else "flat"
        }

    def get_column_stats(self, result: List[Dict], column: str) -> Optional[Dict[str, Any]]:
        if not result:
            return None

        values = [row[column] for row in result if column in row and row[column] is not None]
        if not values:
            return None

        if self._is_numeric(values[0]):
            try:
                numeric_values = [float(v) for v in values]
                return {
                    "sum": sum(numeric_values),
                    "avg": statistics.mean(numeric_values),
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "count": len(numeric_values)
                }
            except (ValueError, TypeError):
                return None
        else:
            unique_values = list(set(values))
            return {
                "unique_count": len(unique_values),
                "sample_values": unique_values[:5]
            }
