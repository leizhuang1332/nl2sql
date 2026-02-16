from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """应用配置"""
    
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o"
    
    # MiniMax
    minimax_api_key: str = "sk-cp-ZVNwPbRA4EmhTNwSKqE3t30NGw5537tXYpshPkdc39nqJVm4IS7k2OUvzIDujufT_jIGTCHu2adxkBDgx5nu-SS66bI7Kfr0dRLlbhP_QYgtq0USVUgx3KQ"
    minimax_model: str = "MiniMax-M2.5"
    
    # Database
    database_uri: str = "sqlite:///example.db"
    
    # Security
    read_only: bool = True
    allowed_tables: Optional[List[str]] = None
    max_retries: int = 3
    timeout: int = 30
    
    class Config:
        env_file = ".env"
