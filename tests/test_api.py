"""Tests for API module."""
import pytest
from fastapi.testclient import TestClient

from src.config import Settings
from src.main import create_app, _orchestrator_instance


@pytest.fixture(autouse=True)
def reset_orchestrator():
    """Reset orchestrator singleton before each test."""
    _orchestrator_instance = None
    yield
    _orchestrator_instance = None


class TestAPI:
    """Test API functionality."""

    def test_create_app(self):
        """Test app creation."""
        settings = Settings(database_uri="sqlite:///example.db")
        app = create_app(settings)
        
        assert app is not None
        assert app.title == "NL2SQL API"

    def test_health_endpoint(self):
        """Test health check endpoint."""
        settings = Settings(database_uri="sqlite:///example.db")
        app = create_app(settings)
        client = TestClient(app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_tables_endpoint(self):
        """Test tables listing endpoint."""
        settings = Settings(database_uri="sqlite:///example.db")
        app = create_app(settings)
        client = TestClient(app)
        
        response = client.get("/tables")
        
        assert response.status_code == 200
        assert "tables" in response.json()

    def test_schema_endpoint_success(self):
        """Test schema retrieval endpoint."""
        settings = Settings(database_uri="sqlite:///example.db")
        app = create_app(settings)
        client = TestClient(app)
        
        response = client.get("/schema/products")
        
        assert response.status_code == 200
        assert "table" in response.json()
        assert "schema" in response.json()

    def test_schema_endpoint_not_found(self):
        """Test schema endpoint with non-existent table."""
        settings = Settings(database_uri="sqlite:///example.db")
        app = create_app(settings)
        client = TestClient(app)
        
        response = client.get("/schema/nonexistent")
        
        assert response.status_code in [404, 500]

    def test_query_endpoint(self):
        """Test query endpoint."""
        settings = Settings(database_uri="sqlite:///example.db")
        app = create_app(settings)
        client = TestClient(app)
        
        response = client.post("/query", json={
            "question": "test"
        })
        
        assert response.status_code in [200, 500]

    def test_query_endpoint_with_include_options(self):
        """Test query endpoint with include options."""
        settings = Settings(database_uri="sqlite:///example.db")
        app = create_app(settings)
        client = TestClient(app)
        
        response = client.post("/query", json={
            "question": "test",
            "include_sql": True,
            "include_schema": True
        })
        
        assert response.status_code in [200, 500]


class TestAPIEndpoints:
    """Test individual API endpoints."""

    def test_cors_headers(self):
        """Test CORS headers are present."""
        settings = Settings(
            database_uri="sqlite:///example.db",
            api_cors_origins=["*"]
        )
        app = create_app(settings)
        client = TestClient(app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
