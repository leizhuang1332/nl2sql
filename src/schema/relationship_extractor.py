import json
import os
from typing import Dict, List, Any, Optional
from sqlalchemy import text
from langchain_community.utilities import SQLDatabase


class RelationshipExtractor:
    def __init__(self, db: SQLDatabase):
        self.db = db
    
    def extract_relationships(self, table_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        if table_names is None:
            table_names = self.db.get_usable_table_names()
        
        relationships = []
        
        for table_name in table_names:
            fk_relations = self._extract_foreign_keys(table_name)
            relationships.extend(fk_relations)
        
        return relationships
    
    def _extract_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        relationships = []
        
        try:
            query = f"PRAGMA foreign_key_list({table_name})"
            with self.db._engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()
            
            for row in rows:
                relationships.append({
                    "from_table": table_name,
                    "from_column": row[3],
                    "to_table": row[2],
                    "to_column": row[4],
                    "relationship_type": "foreign_key"
                })
        except Exception:
            pass
        
        return relationships
    
    def get_table_relationships(self, table_name: str) -> Dict[str, List[Dict[str, Any]]]:
        all_relations = self.extract_relationships([table_name])
        
        incoming = [r for r in all_relations if r["to_table"] == table_name]
        outgoing = [r for r in all_relations if r["from_table"] == table_name]
        
        return {
            "incoming": incoming,
            "outgoing": outgoing
        }
    
    def add_manual_relationship(
        self,
        from_table: str,
        from_column: str,
        to_table: str,
        to_column: str,
        relationship_type: str = "foreign_key"
    ) -> Dict[str, Any]:
        return {
            "from_table": from_table,
            "from_column": from_column,
            "to_table": to_table,
            "to_column": to_column,
            "relationship_type": relationship_type,
            "manual": True
        }
    
    def merge_relationships(
        self,
        auto_relationships: List[Dict[str, Any]],
        manual_relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        seen = set()
        merged = []
        
        for rel in auto_relationships + manual_relationships:
            key = (rel["from_table"], rel["from_column"], rel["to_table"], rel["to_column"])
            if key not in seen:
                seen.add(key)
                merged.append(rel)
        
        return merged
