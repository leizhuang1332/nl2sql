# NL2SQL 编排层 (Orchestrator) 设计方案

## 1. 概述

### 1.1 目标
实现 `NL2SQLOrchestrator` 编排器，协调 6 大核心模块完成从自然语言到查询结果的完整流程。

### 1.2 模块依赖关系

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         NL2SQLOrchestrator                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│   Semantic    │          │    Schema     │          │   Security    │
│   Mapper      │◄────────►│   Manager     │─────────►│   Validator   │
│  (语义映射)    │          │  (Schema管理)  │          │   (安全验证)   │
└───────┬───────┘          └───────┬───────┘          └───────┬───────┘
        │                           │                           │
        │                           ▼                           │
        │                  ┌───────────────┐                    │
        │                  │   Generation   │                    │
        └─────────────────►│  SQL Generator │                    │
                           └───────┬───────┘                    │
                                   │                            │
                                   ▼                            │
                          ┌───────────────┐                    │
                          │    Execution   │◄───────────────────┘
                          │ Query Executor │
                          └───────┬───────┘
                                  │
                                  ▼
                          ┌───────────────┐
                          │   Explanation  │
                          │ Result Explainer│
                          └───────────────┘
```

### 1.3 调用流程

```
用户提问
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: Semantic Mapping (语义映射)                            │
│  - 字段映射、时间表达式解析、排序语义                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: Schema Preparation (Schema 准备)                      │
│  - 提取表结构、生成文档、添加采样数据                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: SQL Generation (SQL 生成)                              │
│  - 结合语义映射结果 + Schema 生成 SQL                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: Security Validation (安全验证)                         │
│  - 关键字检查、表/列白名单、只读检查                            │
│  - 验证失败则返回错误                                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 5: Execution (执行与修正)                                 │
│  - 执行 SQL、捕获错误、LLM 修正重试                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 6: Result Explanation (结果解释)                         │
│  - 分析结果数据、生成自然语言解释                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                       返回结果
```

---

## 2. 核心类设计

### 2.1 数据类型定义

```python
# src/core/types.py
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class QueryStatus(Enum):
    """查询状态枚举"""
    SUCCESS = "success"
    SEMANTIC_ERROR = "semantic_error"
    GENERATION_ERROR = "generation_error"
    SECURITY_REJECTED = "security_rejected"
    EXECUTION_ERROR = "execution_error"
    EXPLANATION_ERROR = "explanation_error"


@dataclass
class MappingResult:
    """语义映射结果"""
    enhanced_question: str
    field_mappings: List[Dict[str, Any]] = field(default_factory=list)
    time_mappings: List[Dict[str, Any]] = field(default_factory=list)
    sort_mappings: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class GenerationResult:
    """SQL 生成结果"""
    sql: str
    confidence: float = 1.0
    used_few_shots: List[str] = field(default_factory=list)


@dataclass
class SecurityResult:
    """安全验证结果"""
    is_valid: bool
    threat_level: str = "safe"
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    result: Any = None
    error: str = ""
    attempts: int = 1
    execution_time: float = 0.0


@dataclass
class QueryResult:
    """最终查询结果"""
    status: QueryStatus
    question: str
    mapping: Optional[MappingResult] = None
    sql: str = ""
    security: Optional[SecurityResult] = None
    execution: Optional[ExecutionResult] = None
    explanation: str = ""
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### 2.2 编排器主类

```python
# src/core/orchestrator.py
from typing import Optional, Dict, Any, List
import time
import logging

from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase

from .types import (
    QueryResult, 
    QueryStatus, 
    MappingResult, 
    SecurityResult,
    ExecutionResult
)
from ..schema.database_connector import DatabaseConnector
from ..schema.schema_extractor import SchemaExtractor
from ..schema.schema_doc_generator import SchemaDocGenerator
from ..schema.schema_enhancer import SchemaEnhancer
from ..generation.sql_generator import SQLGenerator
from ..generation.llm_factory import LLMFactory
from ..execution.query_executor import QueryExecutor
from ..semantic.semantic_mapper import SemanticMapper
from ..semantic.config_manager import SemanticConfigManager
from ..security.sql_validator import SQLSecurityValidator
from ..explanation.result_explainer import ResultExplainer


logger = logging.getLogger(__name__)


class NL2SQLOrchestrator:
    """
    NL2SQL 核心编排器
    
    协调所有模块完成从自然语言到查询结果的完整流程
    """
    
    def __init__(
        self,
        llm: Any,
        database_uri: str,
        config: Optional[Dict[str, Any]] = None
    ):
        self.llm = llm
        self.database_uri = database_uri
        self.config = config or {}
        
        # 初始化各模块
        self._init_modules()
    
    def _init_modules(self):
        """初始化所有模块"""
        # Schema 模块
        self.db_connector = DatabaseConnector(self.database_uri)
        self.db = self.db_connector.db
        self.schema_extractor = SchemaExtractor(self.db)
        self.schema_doc_generator = SchemaDocGenerator(self.db)
        self.schema_enhancer = SchemaEnhancer(
            self.db,
            self.config.get("field_descriptions", {})
        )
        
        # Generation 模块
        self.sql_generator = SQLGenerator(
            llm=self.llm,
            prompt_template=None  # 可自定义
        )
        
        # Execution 模块
        self.query_executor = QueryExecutor(
            database=self.db,
            max_retries=self.config.get("max_retries", 3),
            llm=self.llm  # 用于 SQL 修复
        )
        
        # Semantic 模块
        self.semantic_mapper = SemanticMapper()
        self.semantic_config = SemanticConfigManager(
            self.config.get("semantic_mappings_path")
        )
        # 加载语义配置
        if self.semantic_config.mappings:
            for term, fields in self.semantic_config.mappings.get("field_mappings", {}).items():
                self.semantic_mapper.add_field_mapping(term, fields)
            for expr, sql_expr in self.semantic_config.mappings.get("time_mappings", {}).items():
                self.semantic_mapper.add_time_mapping(expr, sql_expr)
        
        # Security 模块
        self.security_validator = SQLSecurityValidator(
            allowed_tables=self.config.get("allowed_tables"),
            allowed_columns=self.config.get("allowed_columns"),
            read_only=self.config.get("read_only", True)
        )
        
        # Explanation 模块
        self.result_explainer = ResultExplainer(llm=self.llm)
        
        logger.info("所有模块初始化完成")
    
    def ask(self, question: str) -> QueryResult:
        """
        处理用户提问
        
        Args:
            question: 用户问题
            
        Returns:
            QueryResult: 包含完整查询结果和解释
        """
        start_time = time.time()
        
        result = QueryResult(
            status=QueryStatus.SUCCESS,
            question=question
        )
        
        try:
            # Step 1: 语义映射
            mapping = self._semantic_mapping(question)
            result.mapping = mapping
            
            # Step 2: Schema 准备
            schema_doc = self._prepare_schema()
            
            # Step 3: SQL 生成
            sql = self._generate_sql(mapping.enhanced_question, schema_doc)
            result.sql = sql
            
            # Step 4: 安全验证
            security_result = self._validate_security(sql)
            result.security = security_result
            
            if not security_result.is_valid:
                result.status = QueryStatus.SECURITY_REJECTED
                result.error_message = security_result.message
                result.metadata["execution_time"] = time.time() - start_time
                return result
            
            # Step 5: 执行查询
            execution_result = self._execute_sql(sql)
            result.execution = execution_result
            
            if not execution_result.success:
                result.status = QueryStatus.EXECUTION_ERROR
                result.error_message = execution_result.error
                result.metadata["execution_time"] = time.time() - start_time
                return result
            
            # Step 6: 结果解释
            explanation = self._explain_result(
                question,
                execution_result.result
            )
            result.explanation = explanation
            
            result.metadata["execution_time"] = time.time() - start_time
            
        except Exception as e:
            logger.error(f"查询处理失败: {e}", exc_info=True)
            result.status = QueryStatus.GENERATION_ERROR
            result.error_message = str(e)
            result.metadata["execution_time"] = time.time() - start_time
        
        return result
    
    def _semantic_mapping(self, question: str) -> MappingResult:
        """Step 1: 语义映射"""
        enhanced_question, mapping_info = self.semantic_mapper.map(question)
        
        return MappingResult(
            enhanced_question=enhanced_question,
            field_mappings=mapping_info.get("field_mappings", []),
            time_mappings=mapping_info.get("time_mappings", []),
            sort_mappings=mapping_info.get("sort_mappings", [])
        )
    
    def _prepare_schema(self) -> str:
        """Step 2: 准备 Schema 文档"""
        # 获取所有表
        tables = self.db.get_usable_table_names()
        
        # 如果有字段增强配置，应用它
        if hasattr(self.schema_enhancer, 'enhance_tables'):
            self.schema_enhancer.enhance_tables(tables)
        
        # 生成 Schema 文档
        schema_doc = self.schema_doc_generator.generate_full_doc(tables)
        
        return schema_doc
    
    def _generate_sql(self, enhanced_question: str, schema_doc: str) -> str:
        """Step 3: 生成 SQL"""
        sql = self.sql_generator.generate(schema_doc, enhanced_question)
        return sql
    
    def _validate_security(self, sql: str) -> SecurityResult:
        """Step 4: 安全验证"""
        validation = self.security_validator.validate(sql)
        
        return SecurityResult(
            is_valid=validation.is_valid,
            threat_level=validation.threat_level.value,
            message=validation.message,
            details=validation.details
        )
    
    def _execute_sql(self, sql: str) -> ExecutionResult:
        """Step 5: 执行 SQL"""
        exec_result = self.query_executor.execute(sql)
        
        return ExecutionResult(
            success=exec_result["success"],
            result=exec_result.get("result"),
            error=exec_result.get("error", ""),
            attempts=exec_result.get("attempts", 1),
            execution_time=0.0  # 可扩展添加计时
        )
    
    def _explain_result(self, question: str, result: Any) -> str:
        """Step 6: 解释结果"""
        explanation = self.result_explainer.explain(question, result)
        return explanation
    
    def get_table_names(self) -> List[str]:
        """获取可用表列表"""
        return self.db.get_usable_table_names()
    
    def get_schema(self, table_name: str) -> Dict[str, Any]:
        """获取指定表的 Schema"""
        return self.schema_extractor.get_table_schema(table_name)
```

---

## 3. 使用示例

### 3.1 基础用法

```python
# src/main.py
from langchain_openai import ChatOpenAI
from src.core.orchestrator import NL2SQLOrchestrator
from src.config import Settings

# 初始化配置
settings = Settings(
    openai_api_key="your-api-key",
    database_uri="sqlite:///example.db"
)

# 初始化 LLM
llm = ChatOpenAI(model=settings.openai_model)

# 初始化编排器
orchestrator = NL2SQLOrchestrator(
    llm=llm,
    database_uri=settings.database_uri,
    config={
        "read_only": True,
        "max_retries": 3,
        "allowed_tables": ["users", "orders", "products"]
    }
)

# 处理问题
result = orchestrator.ask("上个月的销售额是多少?")

# 输出结果
print(f"状态: {result.status.value}")
print(f"SQL: {result.sql}")
print(f"解释: {result.explanation}")
```

### 3.2 批量处理

```python
# 批量处理多个问题
questions = [
    "有多少用户?",
    "本月订单数量",
    "销售额最高的产品"
]

for question in questions:
    result = orchestrator.ask(question)
    print(f"Q: {question}")
    print(f"A: {result.explanation}")
    print("---")
```

---

## 4. 集成测试方案

### 4.1 测试结构

```
tests/
├── conftest.py                 # pytest fixtures
├── test_orchestrator_unit.py   # 编排器单元测试
├── test_orchestrator_integration.py  # 集成测试
└── fixtures/
    ├── sample.db               # 测试用 SQLite 数据库
    └── questions.json          # 测试问题集
```

### 4.2 测试用例设计

#### 单元测试

```python
# tests/test_orchestrator_unit.py
import pytest
from unittest.mock import Mock, patch
from src.core.orchestrator import NL2SQLOrchestrator
from src.core.types import QueryStatus


@pytest.fixture
def mock_llm():
    llm = Mock()
    llm.invoke.return_value = Mock(content="SELECT * FROM users")
    return llm


@pytest.fixture
def orchestrator(mock_llm, tmp_path):
    """创建测试用编排器"""
    import sqlite3
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
    conn.close()
    
    return NL2SQLOrchestrator(
        llm=mock_llm,
        database_uri=f"sqlite:///{db_path}"
    )


def test_orchestrator_init(orchestrator):
    """测试编排器初始化"""
    assert orchestrator.db is not None
    assert orchestrator.sql_generator is not None
    assert orchestrator.query_executor is not None


def test_semantic_mapping(orchestrator):
    """测试语义映射"""
    result = orchestrator._semantic_mapping("今天有多少用户?")
    assert result.enhanced_question is not None
    assert "今天" in result.enhanced_question


def test_security_validation(orchestrator):
    """测试安全验证"""
    result = orchestrator._validate_security("SELECT * FROM users")
    assert result.is_valid is True
    
    # 测试危险 SQL
    result = orchestrator._validate_security("DROP TABLE users")
    assert result.is_valid is False
```

#### 集成测试

```python
# tests/test_orchestrator_integration.py
import pytest
import sqlite3
import tempfile
import os
from langchain_openai import ChatOpenAI
from src.core.orchestrator import NL2SQLOrchestrator


@pytest.fixture
def test_db():
    """创建测试数据库"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            amount DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        INSERT INTO users (name) VALUES ('Alice'), ('Bob');
        INSERT INTO orders (user_id, amount) VALUES 
            (1, 100.0), (1, 200.0), (2, 150.0);
    """)
    conn.close()
    
    yield path
    os.unlink(path)


@pytest.fixture
def real_orchestrator(test_db):
    """创建真实 LLM 的编排器（需要 API key）"""
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("需要 OPENAI_API_KEY")
    
    llm = ChatOpenAI(model="gpt-4o")
    return NL2SQLOrchestrator(
        llm=llm,
        database_uri=f"sqlite:///{test_db}",
        config={"read_only": True}
    )


def test_full_pipeline_simple(real_orchestrator):
    """测试完整流程 - 简单查询"""
    result = real_orchestrator.ask("有多少用户?")
    
    assert result.status == QueryStatus.SUCCESS
    assert result.sql
    assert result.explanation


def test_full_pipeline_with_join(real_orchestrator):
    """测试完整流程 - 关联查询"""
    result = real_orchestrator.ask("每个用户的订单总额是多少?")
    
    assert result.status == QueryStatus.SUCCESS
    assert "JOIN" in result.sql.upper() or "user_id" in result.sql.lower()
```

### 4.3 测试数据

```json
// tests/fixtures/questions.json
{
  "simple_queries": [
    {"question": "有多少用户?", "expected_tables": ["users"]},
    {"question": "本月订单数量", "expected_tables": ["orders"]}
  ],
  "complex_queries": [
    {"question": "销售额最高的前5个产品", "expected_keywords": ["ORDER BY", "LIMIT"]},
    {"question": "每个月的平均订单金额", "expected_keywords": ["GROUP BY", "AVG"]}
  ],
  "semantic_queries": [
    {"question": "今天的订单", "expected_time_conversion": true},
    {"question": "上周注册的用户的订单", "expected_join": true}
  ],
  "security_tests": [
    {"question": "删除所有用户", "should_reject": true},
    {"question": "显示所有表", "should_reject": false}
  ]
}
```

---

## 5. 后续工作

1. **实现 `src/core/types.py`** - 数据类型定义
2. **实现 `src/core/orchestrator.py`** - 编排器主类
3. **创建测试数据库和测试用例**
4. **运行集成测试验证流程**

---

## 6. 配置文件扩展

建议在 `config/settings.yaml` 中添加编排器相关配置：

```yaml
orchestrator:
  # 执行配置
  max_retries: 3
  timeout: 30
  execution_time_limit: 10
  
  # 安全配置
  read_only: true
  allowed_tables: []
  allowed_columns: {}
  
  # 语义配置
  semantic_mappings_path: config/semantic_mappings.json
  field_descriptions_path: config/field_descriptions.json
  
  # 解释配置
  default_explanation_format: text  # text | summary | comparison
  
  # 调试配置
  debug: false
  log_sql: true
  log_execution: true
```
