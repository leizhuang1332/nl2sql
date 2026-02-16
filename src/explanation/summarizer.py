import statistics
from typing import Any, Dict, List, Optional


class ResultSummarizer:
    def __init__(self, data_analyst: Any = None):
        self.data_analyst = data_analyst

    def summarize(
        self,
        result: List[Dict],
        max_points: int = 5
    ) -> str:
        if not result:
            return "查询结果为空"

        analysis = self._analyze_result(result)

        lines = []

        if "row_count" in analysis:
            lines.append(f"共 {analysis['row_count']} 条数据")

        if "numeric_analysis" in analysis:
            for col, stats in analysis["numeric_analysis"].items():
                lines.append(
                    f"{col}: 总计 {stats.get('sum', 0):.2f}, "
                    f"平均 {stats.get('avg', 0):.2f}, "
                    f"最大 {stats.get('max', 0):.2f}, 最小 {stats.get('min', 0):.2f}"
                )

        top_data = self._get_top_items(result, max_points)
        if top_data:
            lines.append("\n关键数据：")
            for i, item in enumerate(top_data, 1):
                lines.append(f"{i}. {item}")

        return "\n".join(lines)

    def _analyze_result(self, result: List[Dict]) -> Dict:
        if not result:
            return {"row_count": 0}

        analysis = {"row_count": len(result)}

        numeric_columns = self._extract_numeric_columns(result)
        if numeric_columns:
            analysis["numeric_analysis"] = {}

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

    def _get_top_items(
        self,
        result: List[Dict],
        max_items: int
    ) -> List[str]:
        if not result:
            return []

        items = []
        for row in result:
            item_strs = [f"{k}: {v}" for k, v in row.items()]
            items.append(", ".join(item_strs))

        return items[:max_items]

    def get_summary_dict(
        self,
        result: List[Dict],
        max_items: int = 5
    ) -> Dict[str, Any]:
        if not result:
            return {"error": "无数据"}

        analysis = self._analyze_result(result)

        top_data = self._get_top_items(result, max_items)

        return {
            "row_count": analysis.get("row_count", 0),
            "numeric_analysis": analysis.get("numeric_analysis", {}),
            "top_items": top_data
        }
