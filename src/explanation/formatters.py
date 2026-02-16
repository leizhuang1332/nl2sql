import json
from datetime import datetime
from typing import Any, Dict, List, Optional


I18N_MESSAGES = {
    "zh": {
        "no_data": "无数据",
        "total_rows": "共 {count} 条",
        "page_info": "第 {current} / {total} 页"
    },
    "en": {
        "no_data": "No data",
        "total_rows": "Total {count} rows",
        "page_info": "Page {current} / {total}"
    }
}


class ResultFormatter:
    def __init__(self, locale: str = "zh"):
        self.locale = locale
        self._messages = I18N_MESSAGES.get(locale, I18N_MESSAGES["zh"])

    def _t(self, key: str, **kwargs) -> str:
        template = self._messages.get(key, key)
        return template.format(**kwargs) if kwargs else template

    @staticmethod
    def format_number(value: Any, format_type: str = "default") -> str:
        try:
            num = float(value)

            if format_type == "currency":
                return f"¥{num:,.2f}"

            if format_type == "percentage":
                return f"{num:.1f}%"

            if format_type == "compact":
                if abs(num) >= 10000:
                    return f"{num/10000:.1f}万"
                if abs(num) >= 1000:
                    return f"{num/1000:.1f}千"

            if isinstance(num, int) or num == int(num):
                return str(int(num))
            return f"{num:.2f}"

        except (ValueError, TypeError):
            return str(value)

    @staticmethod
    def format_table(
        result: List[Dict],
        max_rows: int = 10,
        max_width: int = 50,
        locale: str = "zh"
    ) -> str:
        messages = I18N_MESSAGES.get(locale, I18N_MESSAGES["zh"])
        no_data = messages["no_data"]
        
        if not result:
            return no_data

        headers = list(result[0].keys())

        col_widths = {}
        for header in headers:
            max_content_width = max(len(str(header)), max(len(str(row.get(header, ""))) for row in result) + 2)
            col_widths[header] = min(max_content_width, max_width)

        lines = []

        header_line = " | ".join(
            str(h).ljust(col_widths[h]) for h in headers
        )
        lines.append(header_line)
        lines.append("-" * len(header_line))

        for i, row in enumerate(result):
            if i >= max_rows:
                break

            line = " | ".join(
                str(row.get(h, "")).ljust(col_widths[h])[:max_width]
                for h in headers
            )
            lines.append(line)

        if len(result) > max_rows:
            total_msg = messages.get("total_rows", "共 {count} 条")
            lines.append(f"... {total_msg.format(count=len(result))}")

        return "\n".join(lines)

    @staticmethod
    def format_json(result: List[Dict]) -> str:
        return json.dumps(result, ensure_ascii=False, indent=2)

    @staticmethod
    def format_markdown(
        result: List[Dict],
        locale: str = "zh"
    ) -> str:
        messages = I18N_MESSAGES.get(locale, I18N_MESSAGES["zh"])
        no_data = messages["no_data"]
        
        if not result:
            return no_data

        headers = list(result[0].keys())

        lines = []

        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        for row in result:
            values = [str(row.get(h, "")) for h in headers]
            lines.append("| " + " | ".join(values) + " |")

        return "\n".join(lines)

    @staticmethod
    def format_csv(result: List[Dict]) -> str:
        if not result:
            return ""

        headers = list(result[0].keys())
        lines = [",".join(headers)]

        for row in result:
            values = [str(row.get(h, "")) for h in headers]
            lines.append(",".join(values))

        return "\n".join(lines)

    @staticmethod
    def format_html(result: List[Dict], locale: str = "zh") -> str:
        messages = I18N_MESSAGES.get(locale, I18N_MESSAGES["zh"])
        no_data = messages["no_data"]
        
        if not result:
            return f"<table><tr><td>{no_data}</td></tr></table>"

        headers = list(result[0].keys())

        lines = ["<table>"]
        lines.append("<thead><tr>")
        for h in headers:
            lines.append(f"<th>{h}</th>")
        lines.append("</tr></thead>")

        lines.append("<tbody>")
        for row in result:
            lines.append("<tr>")
            for h in headers:
                lines.append(f"<td>{row.get(h, '')}</td>")
            lines.append("</tr>")
        lines.append("</tbody>")

        lines.append("</table>")
        return "\n".join(lines)

    @staticmethod
    def format_text(
        result: List[Dict],
        max_rows: int = 10,
        locale: str = "zh"
    ) -> str:
        messages = I18N_MESSAGES.get(locale, I18N_MESSAGES["zh"])
        no_data = messages["no_data"]
        
        if not result:
            return no_data

        lines = []
        for i, row in enumerate(result):
            if i >= max_rows:
                break
            items = [f"{k}: {v}" for k, v in row.items()]
            lines.append(", ".join(items))

        if len(result) > max_rows:
            total_msg = messages.get("total_rows", "共 {count} 条")
            lines.append(f"... {total_msg.format(count=len(result))}")

        return "\n".join(lines)
