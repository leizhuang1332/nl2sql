import pytest
import os
import tempfile
import sqlite3
from src.schema.database_connector import DatabaseConnector
from src.schema.schema_extractor import SchemaExtractor


@pytest.fixture
def test_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100),
            age INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            amount DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()
    yield path
    os.unlink(path)


def test_database_connector(test_db):
    connector = DatabaseConnector(test_db)
    assert connector.test_connection() is True
    tables = connector.get_usable_tables()
    assert "users" in tables
    assert "orders" in tables


def test_schema_extractor(test_db):
    connector = DatabaseConnector(test_db)
    extractor = SchemaExtractor(connector.db)
    schema = extractor.get_table_schema("users")
    assert schema["table_name"] == "users"
    assert "ddl" in schema
    assert "columns" in schema
    assert len(schema["columns"]) > 0


def test_column_extraction(test_db):
    connector = DatabaseConnector(test_db)
    extractor = SchemaExtractor(connector.db)
    schema = extractor.get_table_schema("users")
    column_names = [col["name"] for col in schema["columns"]]
    assert "id" in column_names
    assert "name" in column_names
    assert "email" in column_names
    assert "age" in column_names
