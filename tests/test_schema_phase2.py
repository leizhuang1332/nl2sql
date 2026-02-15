import pytest
import os
import tempfile
import sqlite3
from src.schema.database_connector import DatabaseConnector
from src.schema.schema_doc_generator import SchemaDocGenerator


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
    conn.execute("INSERT INTO users (name, email, age) VALUES ('Alice', 'alice@example.com', 25)")
    conn.execute("INSERT INTO users (name, email, age) VALUES ('Bob', 'bob@example.com', 30)")
    conn.execute("INSERT INTO orders (user_id, amount) VALUES (1, 100.50)")
    conn.execute("INSERT INTO orders (user_id, amount) VALUES (1, 200.75)")
    conn.commit()
    conn.close()
    yield path
    os.unlink(path)


def test_schema_doc_generator_init(test_db):
    connector = DatabaseConnector(test_db)
    generator = SchemaDocGenerator(connector.db)
    assert generator.sample_rows == 3


def test_generate_table_doc(test_db):
    connector = DatabaseConnector(test_db)
    generator = SchemaDocGenerator(connector.db)
    doc = generator.generate_table_doc("users")
    
    assert doc["table_name"] == "users"
    assert "columns" in doc
    assert "sample_data" in doc
    assert "row_count" in doc
    assert doc["row_count"] == 2


def test_sample_data(test_db):
    connector = DatabaseConnector(test_db)
    generator = SchemaDocGenerator(connector.db)
    doc = generator.generate_table_doc("users")
    
    assert len(doc["sample_data"]) == 2
    assert doc["sample_data"][0]["name"] == "Alice"
    assert doc["sample_data"][1]["name"] == "Bob"


def test_generate_full_doc(test_db):
    connector = DatabaseConnector(test_db)
    generator = SchemaDocGenerator(connector.db)
    doc = generator.generate_full_doc()
    
    assert "# Database Schema" in doc
    assert "## users" in doc
    assert "## orders" in doc
    assert "### Columns" in doc
    assert "### Sample Data" in doc


def test_generate_json_doc(test_db):
    connector = DatabaseConnector(test_db)
    generator = SchemaDocGenerator(connector.db)
    doc = generator.generate_json_doc()
    
    assert "tables" in doc
    assert "metadata" in doc
    assert doc["metadata"]["total_tables"] == 2
    assert len(doc["tables"]) == 2


def test_custom_sample_rows(test_db):
    connector = DatabaseConnector(test_db)
    generator = SchemaDocGenerator(connector.db, sample_rows=1)
    doc = generator.generate_table_doc("users")
    
    assert len(doc["sample_data"]) == 1
