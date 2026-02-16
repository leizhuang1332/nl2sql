"""
Usage example for NL2SQL project.
This file demonstrates how to use the NL2SQLOrchestrator to query databases using natural language.
"""
import os
import sqlite3
import tempfile
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 获取当前文件（test_usage.py）的目录
# tests_dir = os.path.dirname(os.path.abspath(__file__))
# # 获取项目根目录（tests目录的上一级）
# project_root = os.path.dirname(tests_dir)
# # 将项目根目录加入Python搜索路径
# sys.path.insert(0, project_root)

# Set API key (or use .env file)
# os.environ["OPENAI_API_KEY"] = "your-api-key-here"

from src.core.orchestrator import NL2SQLOrchestrator
from src.generation.llm_factory import LLMFactory


def create_sample_db():
    """Create a sample SQLite database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            age INTEGER,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            amount DECIMAL(10,2),
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price DECIMAL(10,2),
            category TEXT
        );
        
        INSERT INTO users (name, age, email) VALUES 
            ('Alice', 25, 'alice@example.com'),
            ('Bob', 30, 'bob@example.com'),
            ('Charlie', 35, 'charlie@example.com'),
            ('Diana', 28, 'diana@example.com');
            
        INSERT INTO orders (user_id, amount, status) VALUES 
            (1, 100.0, 'completed'),
            (1, 200.0, 'pending'),
            (2, 150.0, 'completed'),
            (2, 80.0, 'cancelled'),
            (3, 300.0, 'completed');
            
        INSERT INTO products (name, price, category) VALUES 
            ('iPhone 15', 5999.0, 'electronics'),
            ('MacBook Pro', 9999.0, 'electronics'),
            ('T恤', 199.0, 'clothing'),
            ('运动鞋', 499.0, 'clothing'),
            ('咖啡机', 1299.0, 'appliances');
    """)
    conn.close()
    
    return path


def main():
    # Create sample database
    db_path = create_sample_db()
    print(f"Created test database: {db_path}")
    
    try:
        # Create LLM (supports: openai, minimax, anthropic, ollama)
        # Example with OpenAI:
        llm = LLMFactory.create(
            provider="minimax",
            model="MiniMax-M2.5",
            api_key=os.environ["MINIMAX_API_KEY"],
            base_url=os.environ["MINIMAX_BASE_URL"],
            temperature=1
        )
        
        # Or use a mock LLM for testing without API key:
        # from unittest.mock import Mock
        # llm = Mock()
        # llm.invoke.return_value = "SELECT COUNT(*) FROM users"
        
        # Create orchestrator
        orchestrator = NL2SQLOrchestrator(
            llm=llm,
            database_uri=f"sqlite:///{db_path}",
            config={
                "read_only": True,  # Only allow SELECT queries
                "max_retries": 3,
            }
        )
        
        # List available tables
        print(f"\nAvailable tables: {orchestrator.get_table_names()}")
        
        # Example queries
        queries = [
            "查询所有用户的数量",
            "列出所有已完成订单",
            "查询最贵的产品",
            "计算每个用户的订单总金额",
            "查询有哪些产品分类",
        ]
        
        print("\n" + "="*60)
        print("Running queries...")
        print("="*60)
        
        for question in queries:
            print(f"\n问题: {question}")
            print("-" * 40)
            
            result = orchestrator.ask(question)
            
            print(f"状态: {result.status.value}")
            if result.sql:
                print(f"SQL: {result.sql}")
            if result.execution and result.execution.result:
                print(f"结果: {result.execution.result}")
            if result.explanation:
                print(f"解释: {result.explanation}")
            if result.error_message:
                print(f"错误: {result.error_message}")
            
            print()
    
    finally:
        # Cleanup
        os.unlink(db_path)
        print("Test database cleaned up.")


if __name__ == "__main__":
    main()
