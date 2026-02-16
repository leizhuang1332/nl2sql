from typing import Any, Dict, List, Union
import json


class ResultHandler:
    def __init__(self):
        self.formatters = {
            "table": self._format_table,
            "json": self._format_json,
            "text": self._format_text,
            "markdown": self._format_markdown
        }

    def handle(
        self,
        result: Any,
        format_type: str = "table"
    ) -> Union[str, List[Dict]]:
        parsed = self._parse_result(result)

        formatter = self.formatters.get(format_type, self._format_table)
        return formatter(parsed)

    def _parse_result(self, result: Any) -> List[Dict]:
        if isinstance(result, str):
            try:
                return json.loads(result)
            except:
                return self._parse_table_string(result)

        if isinstance(result, list):
            return result

        return [{"value": str(result)}]

    def _parse_table_string(self, table_str: str) -> List[Dict]:
        return []

    def _format_table(self, data: List[Dict]) -> str:
        if not data:
            return "无结果"

        headers = list(data[0].keys()) if data else []

        lines = []
        lines.append(" | ".join(headers))
        lines.append(" | ".join(["---"] * len(headers)))

        for row in data:
            values = [str(row.get(h, "")) for h in headers]
            lines.append(" | ".join(values))

        return "\n".join(lines)

    def _format_json(self, data: List[Dict]) -> str:
        return json.dumps(data, ensure_ascii=False, indent=2)

    def _format_text(self, data: List[Dict]) -> str:
        if not data:
            return "无结果"

        lines = []
        for row in data:
            for key, value in row.items():
                lines.append(f"{key}: {value}")
            lines.append("---")

        return "\n".join(lines)

    def _format_markdown(self, data: List[Dict]) -> str:
        md = "## 查询结果\n\n"
        md += self._format_table(data)
        return md
