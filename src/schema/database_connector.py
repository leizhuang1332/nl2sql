from langchain_community.utilities import SQLDatabase
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class DatabaseConnector:
    """数据库连接管理器 - MVP 仅支持 SQLite"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._db: Optional[SQLDatabase] = None
    
    @property
    def db(self) -> SQLDatabase:
        if self._db is None:
            self._db = SQLDatabase.from_uri(f"sqlite:///{self.db_path}")
        return self._db
    
    def get_usable_tables(self) -> List[str]:
        return self.db.get_usable_table_names()
    
    def test_connection(self) -> bool:
        try:
            self.db.run("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False
