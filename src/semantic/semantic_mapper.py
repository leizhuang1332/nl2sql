from typing import Dict, List, Tuple


class SemanticMapper:
    def __init__(self):
        self.field_mappings: Dict[str, List[str]] = {}
        self.time_mappings: Dict[str, str] = {}
        self.sort_mappings: Dict[str, Dict] = {}
        self._init_default_mappings()

    def _init_default_mappings(self):
        self.time_mappings = {
            "今天": "DATE('now')",
            "昨天": "DATE('now', '-1 day')",
            "前天": "DATE('now', '-2 days')",
            "明天": "DATE('now', '+1 day')",
            "上周": "DATE('now', '-7 days')",
            "本周": "DATE('now', 'weekday 0', '-7 days')",
            "本月": "DATE('now', 'start of month')",
            "上月": "DATE('now', 'start of month', '-1 month')",
            "今年": "strftime('%Y', 'now')",
            "去年": "strftime('%Y', 'now', '-1 year')",
            "最近7天": "DATE('now', '-7 days')",
            "最近30天": "DATE('now', '-30 days')",
            "最近一年": "DATE('now', '-1 year')"
        }

        self.sort_mappings = {
            "top": {"keyword": "LIMIT", "order": "DESC"},
            "前三": {"keyword": "LIMIT", "order": "DESC", "count": 3},
            "前五": {"keyword": "LIMIT", "order": "DESC", "count": 5},
            "前10": {"keyword": "LIMIT", "order": "DESC", "count": 10},
            "最后": {"keyword": "LIMIT", "order": "ASC", "count": 1},
            "最早": {"keyword": "ORDER BY", "order": "ASC"}
        }

    def add_field_mapping(self, business_term: str, technical_fields: List[str]):
        self.field_mappings[business_term] = technical_fields

    def add_time_mapping(self, expression: str, sql_expression: str):
        self.time_mappings[expression] = sql_expression

    def add_sort_mapping(self, expression: str, config: Dict):
        self.sort_mappings[expression] = config

    def map(self, question: str) -> Tuple[str, Dict]:
        enhanced_question = question
        mapping_info = {
            "field_mappings": [],
            "time_mappings": [],
            "sort_mappings": []
        }

        for biz_term, tech_fields in self.field_mappings.items():
            if biz_term in question:
                enhanced_question += f"\n[提示: '{biz_term}' 对应字段 {', '.join(tech_fields)}]"
                mapping_info["field_mappings"].append({
                    "term": biz_term,
                    "fields": tech_fields
                })

        for expr, sql_expr in self.time_mappings.items():
            if expr in question:
                enhanced_question += f"\n[提示: '{expr}' 应转换为 SQL 日期 {sql_expr}]"
                mapping_info["time_mappings"].append({
                    "expression": expr,
                    "sql": sql_expr
                })

        for expr, config in self.sort_mappings.items():
            if expr in question:
                mapping_info["sort_mappings"].append({
                    "expression": expr,
                    "config": config
                })

        return enhanced_question, mapping_info

    def get_field_mapping(self, business_term: str) -> List[str]:
        return self.field_mappings.get(business_term, [])

    def get_time_mapping(self, expression: str) -> str:
        return self.time_mappings.get(expression, "")
