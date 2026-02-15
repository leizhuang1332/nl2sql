import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path


class SchemaEnhancer:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.field_descriptions: Dict[str, Dict[str, str]] = {}
        self.table_descriptions: Dict[str, str] = {}
        
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
    
    def _load_config(self, config_path: str) -> None:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.field_descriptions = config.get("fields", {})
            self.table_descriptions = config.get("tables", {})
        except Exception:
            self.field_descriptions = {}
            self.table_descriptions = {}
    
    def add_field_description(self, table_name: str, field_name: str, description: str) -> None:
        key = f"{table_name}.{field_name}"
        self.field_descriptions[key] = description
    
    def add_table_description(self, table_name: str, description: str) -> None:
        self.table_descriptions[table_name] = description
    
    def get_field_description(self, table_name: str, field_name: str) -> Optional[str]:
        key = f"{table_name}.{field_name}"
        return self.field_descriptions.get(key)
    
    def get_table_description(self, table_name: str) -> Optional[str]:
        return self.table_descriptions.get(table_name)
    
    def enhance_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        table_name = schema.get("table_name", "")
        
        enhanced = schema.copy()
        
        if table_name in self.table_descriptions:
            enhanced["description"] = self.table_descriptions[table_name]
        
        if "columns" in schema:
            enhanced["columns"] = []
            for col in schema["columns"]:
                enhanced_col = col.copy()
                desc = self.get_field_description(table_name, col.get("name", ""))
                if desc:
                    enhanced_col["description"] = desc
                enhanced["columns"].append(enhanced_col)
        
        return enhanced
    
    def enhance_full_schema(self, full_schema: Dict[str, Any]) -> Dict[str, Any]:
        enhanced = full_schema.copy()
        
        if "tables" in full_schema:
            enhanced["tables"] = [
                self.enhance_schema(table) 
                for table in full_schema["tables"]
            ]
        
        return enhanced
    
    def to_config_dict(self) -> Dict[str, Any]:
        return {
            "tables": self.table_descriptions,
            "fields": self.field_descriptions
        }
    
    def save_config(self, output_path: str) -> bool:
        try:
            config = self.to_config_dict()
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
