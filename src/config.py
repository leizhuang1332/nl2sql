"""
Configuration module for NL2SQL.

Supports YAML configuration file loading with environment variable override.
Configuration priority (lowest to highest): YAML < .env < explicit kwargs
"""
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    NL2SQL Application Settings.
    
    Supports loading from YAML config file with environment variable override.
    Priority: yaml < .env < explicit kwargs
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ===================
    # LLM Configuration
    # ===================
    # LLM provider: openai / minimax / anthropic / ollama / custom
    llm_provider: str = Field(default="minimax", alias="llm_provider")
    # Model name
    llm_model: str = Field(default="MiniMax-M2.5", alias="llm_model")
    # API Key
    llm_api_key: str = Field(default="", alias="llm_api_key")
    # API Base URL (for custom provider or proxy)
    llm_base_url: str = Field(default="", alias="llm_base_url")
    # Temperature parameter
    llm_temperature: float = Field(default=0.7, alias="llm_temperature")
    # Max tokens
    llm_max_tokens: int = Field(default=2000, alias="llm_max_tokens")
    # Request timeout
    llm_timeout: int = Field(default=60, alias="llm_timeout")
    
    # MiniMax specific settings
    minimax_api_key: str = Field(default="", alias="minimax_api_key")
    minimax_model: str = Field(default="MiniMax-M2.5", alias="minimax_model")
    minimax_base_url: str = Field(default="https://api.minimaxi.com/anthropic", alias="minimax_base_url")
    
    # Anthropic specific settings
    anthropic_api_key: str = Field(default="", alias="anthropic_api_key")
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022", alias="anthropic_model")
    
    # Ollama specific settings
    ollama_base_url: str = Field(default="http://localhost:11434", alias="ollama_base_url")
    ollama_model: str = Field(default="llama2", alias="ollama_model")
    
    # ===================
    # Database Configuration
    # ===================
    database_uri: str = Field(default="sqlite:///example.db", alias="database_uri")
    database_pool_size: int = Field(default=5, alias="database_pool_size")
    database_max_overflow: int = Field(default=10, alias="database_max_overflow")
    database_pool_recycle: int = Field(default=3600, alias="database_pool_recycle")
    database_query_timeout: int = Field(default=30, alias="database_query_timeout")
    database_echo: bool = Field(default=False, alias="database_echo")
    
    # ===================
    # Security Configuration
    # ===================
    security_read_only: bool = Field(default=True, alias="security_read_only")
    security_max_retries: int = Field(default=3, alias="security_max_retries")
    security_timeout: int = Field(default=30, alias="security_timeout")
    security_allowed_tables: List[str] = Field(default_factory=list, alias="security_allowed_tables")
    security_forbidden_keywords: List[str] = Field(
        default_factory=lambda: ["DROP", "TRUNCATE", "ALTER", "CREATE"],
        alias="security_forbidden_keywords"
    )
    security_max_rows: int = Field(default=1000, alias="security_max_rows")
    
    # ===================
    # Paths Configuration
    # ===================
    path_field_descriptions: str = Field(
        default="config/field_descriptions.json",
        alias="path_field_descriptions"
    )
    path_semantic_mappings: str = Field(
        default="config/semantic_mappings.json",
        alias="path_semantic_mappings"
    )
    path_security_policy: str = Field(
        default="config/security_policy.json",
        alias="path_security_policy"
    )
    
    # ===================
    # API Configuration
    # ===================
    api_host: str = Field(default="0.0.0.0", alias="api_host")
    api_port: int = Field(default=8000, alias="api_port")
    api_cors_origins: List[str] = Field(
        default_factory=lambda: ["*"],
        alias="api_cors_origins"
    )
    api_reload: bool = Field(default=False, alias="api_reload")
    api_workers: int = Field(default=1, alias="api_workers")
    api_log_level: str = Field(default="info", alias="api_log_level")
    
    # ===================
    # Logging Configuration
    # ===================
    log_level: str = Field(default="INFO", alias="log_level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        alias="log_format"
    )
    log_file: str = Field(default="", alias="log_file")
    log_file_max_size: int = Field(default=10, alias="log_file_max_size")
    log_file_backup_count: int = Field(default=5, alias="log_file_backup_count")
    log_sql: bool = Field(default=False, alias="log_sql")
    
    # ===================
    # Execution Configuration
    # ===================
    execution_enabled: bool = Field(default=True, alias="execution_enabled")
    execution_retries: int = Field(default=3, alias="execution_retries")
    execution_retry_interval: int = Field(default=1, alias="execution_retry_interval")
    execution_timeout: int = Field(default=60, alias="execution_timeout")
    
    # ===================
    # Explanation Configuration
    # ===================
    explanation_enabled: bool = Field(default=True, alias="explanation_enabled")
    explanation_mode: str = Field(default="simple", alias="explanation_mode")
    explanation_format: str = Field(default="text", alias="explanation_format")
    explanation_language: str = Field(default="zh", alias="explanation_language")
    
    # ===================
    # Semantic Configuration
    # ===================
    semantic_enabled: bool = Field(default=True, alias="semantic_enabled")
    semantic_vector_matching_enabled: bool = Field(
        default=False,
        alias="semantic_vector_matching_enabled"
    )
    semantic_vector_provider: str = Field(
        default="openai",
        alias="semantic_vector_provider"
    )
    semantic_vector_model: str = Field(
        default="text-embedding-3-small",
        alias="semantic_vector_model"
    )
    semantic_similarity_threshold: float = Field(
        default=0.7,
        alias="semantic_similarity_threshold"
    )
    semantic_context_window: int = Field(
        default=3,
        alias="semantic_context_window"
    )

    @classmethod
    @lru_cache(maxsize=1)
    def get_yaml_settings(cls, yaml_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load settings from YAML configuration file.
        
        Supports environment variable references in format: ${VAR_NAME}
        
        Args:
            yaml_path: Path to YAML config file. If None, uses default path.
            
        Returns:
            Dictionary of settings loaded from YAML file.
        """
        if yaml_path is None:
            # Default to config/settings.yaml in project root
            project_root = cls._find_project_root()
            yaml_path = project_root / "config" / "settings.yaml"
        
        yaml_path = Path(yaml_path)
        
        if not yaml_path.exists():
            return {}
        
        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_content = f.read()
        
        # Process environment variable references
        yaml_content = cls._process_env_vars(yaml_content)
        
        # Parse YAML
        config_data = yaml.safe_load(yaml_content) or {}
        
        # Flatten nested config (e.g., llm.provider -> llm_provider)
        flat_config = cls._flatten_config(config_data)
        
        return flat_config
    
    @classmethod
    def _find_project_root(cls) -> Path:
        """Find project root directory."""
        # Start from this file's directory and go up
        current = Path(__file__).resolve().parent
        
        # Look for pyproject.toml or config/settings.yaml
        while current != current.parent:
            if (current / "pyproject.toml").exists() or (current / "config" / "settings.yaml").exists():
                return current
            current = current.parent
        
        # Fallback to current directory
        return Path.cwd()
    
    @staticmethod
    def _process_env_vars(content: str) -> str:
        """
        Process environment variable references in YAML content.
        
        Supports format: ${VAR_NAME} or ${VAR_NAME:-default_value}
        If env var is not set and no default provided, keeps the placeholder as-is.
        """
        # Pattern: ${VAR_NAME} or ${VAR_NAME:-default}
        pattern = r'\$\{([^}:]+)(?::-([^}]*))?\}'
        
        def replace_env_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else None
            
            # Try to get from environment
            if default_value is not None:
                # Has default, use it
                value = os.environ.get(var_name, default_value)
            else:
                # No default - check if env var exists
                if var_name in os.environ:
                    value = os.environ[var_name]
                else:
                    # Keep original placeholder if env var not set and no default
                    value = match.group(0)
            
            return str(value)
        
        return re.sub(pattern, replace_env_var, content)
    
    @classmethod
    def _flatten_config(cls, config: Dict[str, Any], parent_key: str = "") -> Dict[str, Any]:
        """
        Flatten nested YAML configuration.
        
        Example:
            {"llm": {"provider": "openai"}} -> {"llm_provider": "openai"}
        """
        items = {}
        
        for key, value in config.items():
            new_key = f"{parent_key}_{key}" if parent_key else key
            
            if isinstance(value, dict):
                items.update(cls._flatten_config(value, new_key))
            else:
                items[new_key] = value
        
        return items
    
    @classmethod
    def from_yaml(cls, yaml_path: Optional[str] = None, **kwargs) -> "Settings":
        """
        Create Settings instance from YAML config with override support.
        
        Priority: yaml < .env < kwargs
        
        Args:
            yaml_path: Path to YAML config file
            **kwargs: Explicit parameters override YAML and .env
            
        Returns:
            Settings instance
        """
        # Step 1: Load from YAML (lowest priority)
        yaml_settings = cls.get_yaml_settings(yaml_path)
        
        # Step 2: Create instance with YAML settings
        # Pydantic will automatically merge .env values (they override YAML)
        instance = cls(**yaml_settings)
        
        # Step 3: Apply explicit kwargs (highest priority)
        if kwargs:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
        
        return instance
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return self.model_dump()


# Convenience function for quick access
@lru_cache(maxsize=1)
def get_settings(**kwargs) -> Settings:
    """
    Get application settings with caching.
    
    Args:
        **kwargs: Override settings
        
    Returns:
        Settings instance
    """
    return Settings.from_yaml(**kwargs)
