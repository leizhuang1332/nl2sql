import pytest
import os
import tempfile
import sqlite3
from src.schema.database_connector import DatabaseConnector, DatabaseConnectorFactory


@pytest.fixture
def test_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100)
        )
    """)
    conn.commit()
    conn.close()
    yield path
    os.unlink(path)


def test_database_connector_sqlite(test_db):
    connector = DatabaseConnector(db_type="sqlite", db_path=test_db)
    assert connector.test_connection() is True
    tables = connector.get_usable_tables()
    assert "users" in tables


def test_database_connector_in_memory():
    connector = DatabaseConnector(db_type="sqlite")
    assert connector.db_type == "sqlite"


def test_database_connector_invalid_type():
    connector = DatabaseConnector(db_type="invalid")
    with pytest.raises(ValueError, match="不支持的数据库类型"):
        _ = connector.db


def test_factory_create_sqlite(test_db):
    connector = DatabaseConnectorFactory.create(db_type="sqlite", db_path=test_db)
    assert connector.db_type == "sqlite"
    assert connector.test_connection() is True


def test_factory_create_mysql():
    connector = DatabaseConnectorFactory.create_mysql(
        host="localhost",
        port=3306,
        user="root",
        password="password",
        database="testdb"
    )
    assert connector.db_type == "mysql"
    assert connector._connection_params["host"] == "localhost"
    assert connector._connection_params["port"] == 3306


def test_factory_create_postgresql():
    connector = DatabaseConnectorFactory.create_postgresql(
        host="localhost",
        port=5432,
        user="postgres",
        password="password",
        database="testdb"
    )
    assert connector.db_type == "postgresql"
    assert connector._connection_params["host"] == "localhost"
    assert connector._connection_params["port"] == 5432


def test_factory_create_oracle():
    connector = DatabaseConnectorFactory.create_oracle(
        host="localhost",
        port=1521,
        user="system",
        password="password",
        service_name="orcl"
    )
    assert connector.db_type == "oracle"
    assert connector._connection_params["service_name"] == "orcl"


def test_factory_create_with_kwargs():
    connector = DatabaseConnectorFactory.create(
        db_type="mysql",
        host="myhost",
        database="mydb"
    )
    assert connector.db_type == "mysql"
    assert connector._connection_params["host"] == "myhost"
    assert connector._connection_params["database"] == "mydb"


def test_sqlite_uri_build():
    connector = DatabaseConnector(db_type="sqlite", db_path="/path/to/db.db")
    uri = connector._build_uri()
    assert uri == "sqlite:////path/to/db.db"


def test_sqlite_memory_uri_build():
    connector = DatabaseConnector(db_type="sqlite")
    uri = connector._build_uri()
    assert uri == "sqlite:///:memory:"
