import pytest
import os
import tempfile
import sqlite3
from src.schema.database_connector import DatabaseConnector
from src.schema.relationship_extractor import RelationshipExtractor


@pytest.fixture
def test_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        )
    """)
    conn.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            amount DECIMAL(10,2),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.execute("""
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER,
            product_id INTEGER,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    """)
    conn.execute("INSERT INTO users (name) VALUES ('Alice')")
    conn.execute("INSERT INTO orders (user_id, amount) VALUES (1, 100.00)")
    conn.commit()
    conn.close()
    yield path
    os.unlink(path)


def test_relationship_extractor_init(test_db):
    connector = DatabaseConnector(test_db)
    extractor = RelationshipExtractor(connector.db)
    assert extractor.db is not None


def test_extract_relationships(test_db):
    connector = DatabaseConnector(test_db)
    extractor = RelationshipExtractor(connector.db)
    relationships = extractor.extract_relationships()
    
    assert len(relationships) >= 2
    
    fk_found = False
    for rel in relationships:
        if rel["from_table"] == "orders" and rel["from_column"] == "user_id":
            fk_found = True
            assert rel["to_table"] == "users"
            assert rel["to_column"] == "id"
    
    assert fk_found is True


def test_get_table_relationships(test_db):
    connector = DatabaseConnector(test_db)
    extractor = RelationshipExtractor(connector.db)
    
    orders_relations = extractor.get_table_relationships("orders")
    
    assert "incoming" in orders_relations
    assert "outgoing" in orders_relations
    
    outgoing = orders_relations["outgoing"]
    assert any(r["to_table"] == "users" for r in outgoing)


def test_add_manual_relationship(test_db):
    connector = DatabaseConnector(test_db)
    extractor = RelationshipExtractor(connector.db)
    
    manual_rel = extractor.add_manual_relationship(
        from_table="users",
        from_column="id",
        to_table="orders",
        to_column="user_id",
        relationship_type="manual_foreign_key"
    )
    
    assert manual_rel["from_table"] == "users"
    assert manual_rel["to_table"] == "orders"
    assert manual_rel["relationship_type"] == "manual_foreign_key"
    assert manual_rel["manual"] is True


def test_merge_relationships(test_db):
    connector = DatabaseConnector(test_db)
    extractor = RelationshipExtractor(connector.db)
    
    auto_rels = [
        {
            "from_table": "orders",
            "from_column": "user_id",
            "to_table": "users",
            "to_column": "id",
            "relationship_type": "foreign_key"
        }
    ]
    
    manual_rels = [
        {
            "from_table": "users",
            "from_column": "id",
            "to_table": "orders",
            "to_column": "user_id",
            "relationship_type": "manual",
            "manual": True
        }
    ]
    
    merged = extractor.merge_relationships(auto_rels, manual_rels)
    
    assert len(merged) == 2


def test_no_foreign_keys(test_db):
    connector = DatabaseConnector(test_db)
    extractor = RelationshipExtractor(connector.db)
    
    relationships = extractor.extract_relationships(["users"])
    
    has_fk = any(r["relationship_type"] == "foreign_key" for r in relationships)
    assert has_fk is False
