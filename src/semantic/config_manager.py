import json
from typing import Dict, List, Any


class SemanticConfigManager:
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}

        if config_path:
            self.load_config(config_path)

    def load_config(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def save_config(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def get_field_mappings(self) -> Dict[str, List[str]]:
        return self.config.get("field_mappings", {})

    def get_time_mappings(self) -> Dict[str, str]:
        return self.config.get("time_mappings", {})

    def get_sort_mappings(self) -> Dict[str, Any]:
        return self.config.get("sort_mappings", {})

    def add_field_mapping(self, term: str, fields: List[str]):
        if "field_mappings" not in self.config:
            self.config["field_mappings"] = {}
        self.config["field_mappings"][term] = fields

    def add_time_mapping(self, expression: str, sql_expr: str):
        if "time_mappings" not in self.config:
            self.config["time_mappings"] = {}
        self.config["time_mappings"][expression] = sql_expr

    def to_dict(self) -> Dict[str, Any]:
        return self.config
