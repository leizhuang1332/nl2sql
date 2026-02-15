import pytest
import os
import tempfile
import json
from src.schema.schema_enhancer import SchemaEnhancer


def test_schema_enhancer_init():
    enhancer = SchemaEnhancer()
    assert enhancer.field_descriptions == {}
    assert enhancer.table_descriptions == {}


def test_schema_enhancer_with_config():
    config = {
        "tables": {"users": "User table"},
        "fields": {"users.id": "User ID"}
    }
    
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    
    try:
        with open(path, 'w') as f:
            json.dump(config, f)
        
        enhancer = SchemaEnhancer(path)
        assert enhancer.table_descriptions["users"] == "User table"
        assert enhancer.field_descriptions["users.id"] == "User ID"
    finally:
        os.unlink(path)


def test_add_field_description():
    enhancer = SchemaEnhancer()
    enhancer.add_field_description("users", "id", "User ID")
    
    assert enhancer.get_field_description("users", "id") == "User ID"
    assert enhancer.get_field_description("users", "name") is None


def test_add_table_description():
    enhancer = SchemaEnhancer()
    enhancer.add_table_description("users", "User table")
    
    assert enhancer.get_table_description("users") == "User table"
    assert enhancer.get_table_description("orders") is None


def test_enhance_schema():
    enhancer = SchemaEnhancer()
    enhancer.add_field_description("users", "id", "User unique ID")
    enhancer.add_table_description("users", "User information")
    
    schema = {
        "table_name": "users",
        "description": "",
        "columns": [
            {"name": "id", "type": "INTEGER"},
            {"name": "name", "type": "VARCHAR"}
        ]
    }
    
    enhanced = enhancer.enhance_schema(schema)
    
    assert enhanced["description"] == "User information"
    assert enhanced["columns"][0]["description"] == "User unique ID"
    assert "description" not in enhanced["columns"][1]


def test_enhance_full_schema():
    enhancer = SchemaEnhancer()
    enhancer.add_table_description("users", "User table")
    enhancer.add_field_description("users", "id", "User ID")
    
    full_schema = {
        "tables": [
            {
                "table_name": "users",
                "description": "",
                "columns": [{"name": "id", "type": "INTEGER"}]
            }
        ]
    }
    
    enhanced = enhancer.enhance_full_schema(full_schema)
    
    assert enhanced["tables"][0]["description"] == "User table"
    assert enhanced["tables"][0]["columns"][0]["description"] == "User ID"


def test_to_config_dict():
    enhancer = SchemaEnhancer()
    enhancer.add_table_description("users", "User table")
    enhancer.add_field_description("users", "id", "User ID")
    
    config = enhancer.to_config_dict()
    
    assert config["tables"]["users"] == "User table"
    assert config["fields"]["users.id"] == "User ID"


def test_save_config():
    enhancer = SchemaEnhancer()
    enhancer.add_table_description("users", "User table")
    enhancer.add_field_description("users", "id", "User ID")
    
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    
    try:
        result = enhancer.save_config(path)
        assert result is True
        
        with open(path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded["tables"]["users"] == "User table"
        assert loaded["fields"]["users.id"] == "User ID"
    finally:
        os.unlink(path)
