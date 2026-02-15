from typing import Literal, Optional, Any
from langchain_community.utilities import SQLDatabase
import logging

logger = logging.getLogger(__name__)

DB_TYPE = Literal["sqlite", "mysql", "postgresql", "oracle"]


class DatabaseConnector:
    def __init__(self, db_path: str = None, db_type: DB_TYPE = "sqlite", **kwargs):
        self.db_path = db_path
        self.db_type = db_type
        self._db: Optional[SQLDatabase] = None
        self._connection_params = kwargs

    @property
    def db(self) -> SQLDatabase:
        if self._db is None:
            uri = self._build_uri()
            self._db = SQLDatabase.from_uri(uri)
        return self._db

    def _build_uri(self) -> str:
        if self.db_type == "sqlite":
            if self.db_path:
                return f"sqlite:///{self.db_path}"
            return "sqlite:///:memory:"

        elif self.db_type == "mysql":
            host = self._connection_params.get("host", "localhost")
            port = self._connection_params.get("port", 3306)
            user = self._connection_params.get("user", "root")
            password = self._connection_params.get("password", "")
            database = self._connection_params.get("database", "")
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

        elif self.db_type == "postgresql":
            host = self._connection_params.get("host", "localhost")
            port = self._connection_params.get("port", 5432)
            user = self._connection_params.get("user", "postgres")
            password = self._connection_params.get("password", "")
            database = self._connection_params.get("database", "")
            return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"

        elif self.db_type == "oracle":
            host = self._connection_params.get("host", "localhost")
            port = self._connection_params.get("port", 1521)
            user = self._connection_params.get("user", "system")
            password = self._connection_params.get("password", "")
            service_name = self._connection_params.get("service_name", "orcl")
            return f"oracle+oracledb://{user}:{password}@{host}:{port}/?service_name={service_name}"

        else:
            raise ValueError(f"不支持的数据库类型: {self.db_type}")

    def get_usable_tables(self) -> list:
        return self.db.get_usable_table_names()

    def test_connection(self) -> bool:
        try:
            self.db.run("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False


class DatabaseConnectorFactory:
    @staticmethod
    def create(
        db_type: DB_TYPE,
        db_path: str = None,
        **kwargs: Any
    ) -> DatabaseConnector:
        return DatabaseConnector(db_path=db_path, db_type=db_type, **kwargs)

    @staticmethod
    def create_sqlite(db_path: str) -> DatabaseConnector:
        return DatabaseConnector(db_type="sqlite", db_path=db_path)

    @staticmethod
    def create_mysql(
        host: str = "localhost",
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: str = ""
    ) -> DatabaseConnector:
        return DatabaseConnector(
            db_type="mysql",
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )

    @staticmethod
    def create_postgresql(
        host: str = "localhost",
        port: int = 5432,
        user: str = "postgres",
        password: str = "",
        database: str = ""
    ) -> DatabaseConnector:
        return DatabaseConnector(
            db_type="postgresql",
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )

    @staticmethod
    def create_oracle(
        host: str = "localhost",
        port: int = 1521,
        user: str = "system",
        password: str = "",
        service_name: str = "orcl"
    ) -> DatabaseConnector:
        return DatabaseConnector(
            db_type="oracle",
            host=host,
            port=port,
            user=user,
            password=password,
            service_name=service_name
        )
