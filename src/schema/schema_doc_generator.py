from langchain_community.utilities import SQLDatabase
from typing import Dict, List, Any, Optional
from sqlalchemy import text
from .schema_extractor import SchemaExtractor


class SchemaDocGenerator:
    def __init__(self, db: SQLDatabase, sample_rows: int = 3):
        self.db = db
        self.extractor = SchemaExtractor(db)
        self.sample_rows = sample_rows
    
    def generate_table_doc(self, table_name: str) -> Dict[str, Any]:
        schema = self.extractor.get_table_schema(table_name)
        sample_data = self._get_sample_data(table_name)
        
        doc = {
            "table_name": table_name,
            "description": "",
            "columns": schema["columns"],
            "sample_data": sample_data,
            "row_count": self._get_row_count(table_name)
        }
        return doc
    
    def generate_full_doc(self, table_names: Optional[List[str]] = None) -> str:
        if table_names is None:
            table_names = self.db.get_usable_table_names()
        
        sections = ["# Database Schema\n"]
        
        for table_name in table_names:
            table_doc = self.generate_table_doc(table_name)
            sections.append(self._format_table_doc(table_doc))
            sections.append("")
        
        return "\n".join(sections)
    
    def generate_json_doc(self, table_names: Optional[List[str]] = None) -> Dict[str, Any]:
        if table_names is None:
            table_names = self.db.get_usable_table_names()
        
        return {
            "tables": [self.generate_table_doc(name) for name in table_names],
            "metadata": {
                "total_tables": len(table_names)
            }
        }
    
    def _get_sample_data(self, table_name: str) -> List[Dict[str, Any]]:
        try:
            with self.db._engine.connect() as conn:
                result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT {self.sample_rows}"))
                rows = result.fetchall()
                if not rows:
                    return []
                
                column_names = rows[0]._mapping.keys()
                
                return [dict(row._mapping) for row in rows]
        except Exception:
            return []
    
    def _get_row_count(self, table_name: str) -> int:
        try:
            with self.db._engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                return count or 0
        except Exception:
            return 0
    
    def _format_table_doc(self, table_doc: Dict[str, Any]) -> str:
        lines = []
        lines.append(f"## {table_doc['table_name']}")
        lines.append(f"- Rows: {table_doc['row_count']}")
        lines.append("")
        
        lines.append("### Columns")
        lines.append("| Column | Type |")
        lines.append("|--------|------|")
        for col in table_doc["columns"]:
            lines.append(f"| {col['name']} | {col['type']} |")
        
        if table_doc["sample_data"]:
            lines.append("")
            lines.append("### Sample Data")
            lines.append("")
            
            headers = list(table_doc["sample_data"][0].keys())
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
            
            for row in table_doc["sample_data"]:
                values = [str(row.get(h, "")) for h in headers]
                lines.append("| " + " | ".join(values) + " |")
        
        return "\n".join(lines)
