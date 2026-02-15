from langchain_community.utilities import SQLDatabase
from typing import Dict, List, Any
import re


class SchemaExtractor:
    """Schema 信息提取器"""
    
    def __init__(self, db: SQLDatabase):
        self.db = db
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        ddl = self.db.get_table_info([table_name])
        return {
            "table_name": table_name,
            "ddl": ddl,
            "columns": self._extract_columns(ddl)
        }
    
    def _extract_columns(self, ddl: str) -> List[Dict]:
        columns = []
        ddl_only = ddl.split("/*")[0]
        for line in ddl_only.split("\n"):
            line = line.strip().rstrip(",")
            if line and not line.startswith("CREATE TABLE") and not line.startswith("PRIMARY KEY") and not line.startswith(")"):
                match = re.match(r'(\w+)\s+(\w+(?:\([^)]+\))?)', line)
                if match:
                    columns.append({"name": match.group(1), "type": match.group(2).upper()})
        return columns
    
    def _extract_type(self, column_str: str) -> str:
        match = re.search(r'(INT|INTEGER|BIGINT|SMALLINT|TINYINT|FLOAT|DOUBLE|DECIMAL|NUMERIC|VARCHAR|CHAR|TEXT|BLOB|DATE|TIME|DATETIME|TIMESTAMP|BOOLEAN|BOOL)', column_str, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return "UNKNOWN"
