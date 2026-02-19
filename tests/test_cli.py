"""Tests for CLI module."""
import subprocess
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from src.config import Settings
from src.main import run_cli, create_orchestrator


class TestCLI:
    """Test CLI functionality."""

    def test_cli_help(self):
        """Test CLI help output."""
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "--help"],
            capture_output=True,
            text=True,
            cwd="."
        )
        
        assert result.returncode == 0
        assert "NL2SQL" in result.stdout
        assert "cli" in result.stdout
        assert "api" in result.stdout

    def test_cli_tables_help(self):
        """Test CLI tables subcommand help."""
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "cli", "--help"],
            capture_output=True,
            text=True,
            cwd="."
        )
        
        assert result.returncode == 0
        assert "tables" in result.stdout

    def test_cli_tables_command(self):
        """Test CLI tables command."""
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "cli", "tables"],
            capture_output=True,
            text=True,
            cwd="."
        )
        
        assert result.returncode == 0
        assert "Available tables:" in result.stdout

    def test_cli_schema_command(self):
        """Test CLI schema command."""
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "cli", "schema", "products"],
            capture_output=True,
            text=True,
            cwd="."
        )
        
        assert result.returncode == 0
        assert "Schema for table" in result.stdout
        assert "products" in result.stdout

    def test_cli_query_without_llm(self):
        """Test CLI query command without LLM."""
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "cli", "query", "test"],
            capture_output=True,
            text=True,
            cwd="."
        )
        
        assert result.returncode == 1
        assert "LLM not available" in result.stderr or "LLM not available" in result.stdout

    def test_api_help(self):
        """Test API subcommand help."""
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "api", "--help"],
            capture_output=True,
            text=True,
            cwd="."
        )
        
        assert result.returncode == 0
        assert "--host" in result.stdout
        assert "--port" in result.stdout


class TestCreateOrchestrator:
    """Test create_orchestrator function."""

    def test_create_orchestrator_basic(self):
        """Test basic orchestrator creation."""
        settings = Settings(database_uri="sqlite:///example.db")
        orchestrator = create_orchestrator(settings)
        
        assert orchestrator is not None
        assert orchestrator.database_uri == "sqlite:///example.db"

    def test_create_orchestrator_singleton(self):
        """Test that orchestrator is a singleton."""
        settings = Settings(database_uri="sqlite:///example.db")
        
        orch1 = create_orchestrator(settings)
        orch2 = create_orchestrator(settings)
        
        assert orch1 is orch2
