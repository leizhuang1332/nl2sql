"""Tests for config module."""
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from src.config import Settings, get_settings


class TestSettings:
    """Test Settings class."""

    def test_default_values(self):
        """Test default settings values."""
        settings = Settings()
        
        assert settings.llm_provider == "minimax"
        assert settings.llm_model == "MiniMax-M2.5"
        assert settings.database_uri == "sqlite:///example.db"
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000
        assert settings.security_read_only is True

    def test_settings_from_kwargs(self):
        """Test settings with explicit kwargs."""
        settings = Settings(
            database_uri="sqlite:///test.db",
            api_port=9000,
            llm_provider="openai"
        )
        
        assert settings.database_uri == "sqlite:///test.db"
        assert settings.api_port == 9000
        assert settings.llm_provider == "openai"

    def test_yaml_loading(self):
        """Test YAML config loading."""
        settings = Settings.from_yaml()
        
        assert settings.llm_provider == "minimax"
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000

    def test_get_yaml_settings(self):
        """Test get_yaml_settings class method."""
        yaml_settings = Settings.get_yaml_settings()
        
        assert "llm_provider" in yaml_settings
        assert "database_uri" in yaml_settings
        assert "api_host" in yaml_settings

    def test_env_var_replacement(self):
        """Test environment variable replacement in YAML."""
        os.environ["TEST_API_KEY"] = "test-key-123"
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({
                "llm": {
                    "api_key": "${TEST_API_KEY}",
                    "provider": "test"
                }
            }, f)
            f.flush()
            
            settings = Settings.get_yaml_settings(f.name)
            
            os.unlink(f.name)
            
            assert settings["llm_api_key"] == "test-key-123"

    def test_env_var_with_default(self):
        """Test environment variable with default value."""
        os.environ.pop("NONEXISTENT_VAR", None)
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({
                "test": {
                    "value": "${NONEXISTENT_VAR:-default_value}"
                }
            }, f)
            f.flush()
            
            settings = Settings.get_yaml_settings(f.name)
            
            os.unlink(f.name)
            
            assert settings["test_value"] == "default_value"

    def test_to_dict(self):
        """Test to_dict method."""
        settings = Settings()
        result = settings.to_dict()
        
        assert isinstance(result, dict)
        assert "llm_provider" in result
        assert "database_uri" in result

    def test_nested_config_flattening(self):
        """Test nested YAML config flattening."""
        config = {
            "llm": {
                "provider": "openai",
                "model": "gpt-4"
            },
            "api": {
                "host": "localhost",
                "port": 8080
            }
        }
        
        flat = Settings._flatten_config(config)
        
        assert flat["llm_provider"] == "openai"
        assert flat["llm_model"] == "gpt-4"
        assert flat["api_host"] == "localhost"
        assert flat["api_port"] == 8080


class TestGetSettings:
    """Test get_settings convenience function."""

    def test_get_settings_cached(self):
        """Test that get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2

    def test_get_settings_with_override(self):
        """Test get_settings with kwargs override."""
        settings = get_settings(api_port=9999)
        
        assert settings.api_port == 9999
