# NL2SQL 编排层 (Orchestrator) 设计方案

## 概述

实现 `NL2SQLOrchestrator` 编排器，协调 6 大核心模块完成从自然语言到查询结果的完整流程。

### 模块依赖关系

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

### 执行流程 (6步)

```
用户提问
    │
    ▼
Step 1: Semantic Mapping → 语义映射增强问题
Step 2: Schema Preparation → 生成LLM可读的Schema文档  
Step 3: SQL Generation → 结合语义+Schema生成SQL
Step 4: Security Validation → 安全验证 (失败则拒绝)
Step 5: Execution → 执行SQL + LLM修正重试
Step 6: Explanation → 解释查询结果
```

---

## Phase 1: 核心类型定义

### 目标
定义编排器所需的全部数据类型，包括查询状态、结果结构等。

### 实现文件
- `src/core/types.py`
- `src/core/__init__.py`

### 代码实现

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

### 单元测试

```python
# tests/test_core_types.py
import pytest
from src.core.types import (
    QueryStatus, 
    MappingResult, 
    SecurityResult, 
    ExecutionResult,
    QueryResult
)


def test_query_status_enum():
    """测试查询状态枚举"""
    assert QueryStatus.SUCCESS.value == "success"
    assert QueryStatus.SECURITY_REJECTED.value == "security_rejected"


def test_mapping_result():
    """测试语义映射结果"""
    result = MappingResult(
        enhanced_question="今天有多少用户?",
        field_mappings=[{"term": "用户", "fields": ["name"]}],
        time_mappings=[{"expression": "今天", "sql": "DATE('now')"}]
    )
    assert result.enhanced_question is not None
    assert len(result.field_mappings) == 1


def test_security_result():
    """测试安全验证结果"""
    result = SecurityResult(
        is_valid=True,
        threat_level="safe",
        message="验证通过"
    )
    assert result.is_valid is True


def test_execution_result():
    """测试执行结果"""
    result = ExecutionResult(
        success=True,
        result=[{"id": 1, "name": "Alice"}],
        attempts=1
    )
    assert result.success is True
    assert len(result.result) == 1


def test_query_result():
    """测试完整查询结果"""
    result = QueryResult(
        status=QueryStatus.SUCCESS,
        question="有多少用户?",
        sql="SELECT COUNT(*) FROM users",
        explanation="共有 100 个用户"
    )
    assert result.status == QueryStatus.SUCCESS
    assert result.sql
    assert result.explanation
```

### 验收标准
- [ ] 所有数据类型定义完整
- [ ] 单元测试覆盖所有类型
- [ ] 类型可被正确序列化/反序列化

---

## Phase 2: 编排器基础架构

### 目标
实现编排器主类框架，包括模块初始化和核心 `ask` 方法。

### 实现文件
- `src/core/orchestrator.py`

### 代码实现

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
    
    def get_table_names(self) -> List[str]:
        """获取可用表列表"""
        return self.db.get_usable_table_names()
    
    def get_schema(self, table_name: str) -> Dict[str, Any]:
        """获取指定表的 Schema"""
        return self.schema_extractor.get_table_schema(table_name)
```

### 单元测试

```python
# tests/test_orchestrator_phase2.py
import pytest
from unittest.mock import Mock, patch
from src.core.orchestrator import NL2SQLOrchestrator


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
    assert orchestrator.semantic_mapper is not None
    assert orchestrator.security_validator is not None
    assert orchestrator.result_explainer is not None


def test_get_table_names(orchestrator):
    """测试获取表名列表"""
    tables = orchestrator.get_table_names()
    assert "users" in tables


def test_get_schema(orchestrator):
    """测试获取表结构"""
    schema = orchestrator.get_schema("users")
    assert schema["table_name"] == "users"
    assert "columns" in schema
```

### 验收标准
- [ ] 编排器可正常初始化
- [ ] 所有6个模块正确注入
- [ ] `ask()` 方法骨架完成
- [ ] 单元测试通过

---

## Phase 3: 语义映射集成

### 目标
实现 `_semantic_mapping` 方法，将语义模块集成到编排流程。

### 代码实现

```python
# 在 orchestrator.py 中添加以下方法

def _semantic_mapping(self, question: str) -> MappingResult:
    """Step 1: 语义映射"""
    enhanced_question, mapping_info = self.semantic_mapper.map(question)
    
    return MappingResult(
        enhanced_question=enhanced_question,
        field_mappings=mapping_info.get("field_mappings", []),
        time_mappings=mapping_info.get("time_mappings", []),
        sort_mappings=mapping_info.get("sort_mappings", [])
    )
```

### 单元测试

```python
def test_semantic_mapping_basic(orchestrator):
    """测试基础语义映射"""
    result = orchestrator._semantic_mapping("有多少用户?")
    assert result.enhanced_question is not None
    assert result.question == "有多少用户?"


def test_semantic_mapping_time(orchestrator):
    """测试时间表达式映射"""
    result = orchestrator._semantic_mapping("今天的订单有多少?")
    assert "今天" in result.enhanced_question
    assert len(result.time_mappings) > 0


def test_semantic_mapping_field(orchestrator):
    """测试字段映射"""
    orchestrator.semantic_mapper.add_field_mapping("订单", ["orders"])
    result = orchestrator._semantic_mapping("订单数量是多少?")
    assert "订单" in result.enhanced_question
    assert len(result.field_mappings) > 0
```

### 验收标准
- [ ] 时间表达式正确转换
- [ ] 字段映射正确增强问题
- [ ] 映射结果包含完整信息

---

## Phase 4: Schema + SQL生成 + 安全验证集成

### 目标
实现 Schema 准备、SQL 生成和安全验证方法。

### 代码实现

```python
# 在 orchestrator.py 中添加以下方法

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
```

### 单元测试

```python
def test_prepare_schema(orchestrator):
    """测试 Schema 准备"""
    schema_doc = orchestrator._prepare_schema()
    assert "users" in schema_doc
    assert "id" in schema_doc.lower()


def test_generate_sql(orchestrator):
    """测试 SQL 生成"""
    schema_doc = "Table: users (id INTEGER, name TEXT)"
    sql = orchestrator._generate_sql("有多少用户?", schema_doc)
    assert sql.upper().startswith("SELECT")


def test_validate_security_safe(orchestrator):
    """测试安全验证 - 安全SQL"""
    result = orchestrator._validate_security("SELECT * FROM users")
    assert result.is_valid is True


def test_validate_security_dangerous(orchestrator):
    """测试安全验证 - 危险SQL"""
    result = orchestrator._validate_security("DROP TABLE users")
    assert result.is_valid is False
    assert result.threat_level == "critical"


def test_validate_security_readonly(orchestrator):
    """测试只读模式验证"""
    result = orchestrator._validate_security("INSERT INTO users VALUES (1)")
    assert result.is_valid is False
```

### 验收标准
- [ ] Schema 文档正确生成
- [ ] SQL 生成调用正常
- [ ] 安全验证正确拦截危险操作
- [ ] 单元测试通过

---

## Phase 5: 执行与结果解释集成

### 目标
实现 SQL 执行和结果解释方法，完成完整流程。

### 代码实现

```python
# 在 orchestrator.py 中添加以下方法

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
```

### 单元测试

```python
def test_execute_sql_success(orchestrator):
    """测试 SQL 执行成功"""
    # 先插入测试数据
    orchestrator.db_connector.db.run("INSERT INTO users (name) VALUES ('Alice')")
    
    result = orchestrator._execute_sql("SELECT * FROM users")
    assert result.success is True
    assert result.result is not None


def test_execute_sql_error(orchestrator):
    """测试 SQL 执行失败"""
    result = orchestrator._execute_sql("SELECT * FROM nonexistent_table")
    assert result.success is False
    assert result.error is not None


def test_explain_result(orchestrator):
    """测试结果解释"""
    result_data = [{"count": 100}]
    explanation = orchestrator._explain_result("有多少用户?", result_data)
    assert explanation is not None
    assert len(explanation) > 0
```

### 验收标准
- [ ] SQL 执行正确返回结果
- [ ] 执行错误正确捕获
- [ ] 结果解释正确生成
- [ ] 完整流程联调通过

---

## Phase 6: 集成测试

### 目标
创建完整的端到端集成测试。

### 测试结构

```
tests/
├── conftest.py                     # pytest fixtures
├── test_orchestrator_unit.py       # 编排器单元测试
└── test_orchestrator_integration.py # 集成测试
```

### 测试数据库 Fixture

```python
# tests/conftest.py
import pytest
import sqlite3
import tempfile
import os


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
            age INTEGER,
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
        
        -- 插入测试数据
        INSERT INTO users (name, age) VALUES 
            ('Alice', 25),
            ('Bob', 30),
            ('Charlie', 35);
            
        INSERT INTO orders (user_id, amount, status) VALUES 
            (1, 100.0, 'completed'),
            (1, 200.0, 'pending'),
            (2, 150.0, 'completed'),
            (2, 80.0, 'cancelled');
            
        INSERT INTO products (name, price, category) VALUES 
            ('iPhone', 5999.0, 'electronics'),
            ('MacBook', 9999.0, 'electronics'),
            ('T恤', 199.0, 'clothing');
    """)
    conn.close()
    
    yield path
    os.unlink(path)


@pytest.fixture
def mock_llm():
    """Mock LLM"""
    from unittest.mock import Mock
    llm = Mock()
    llm.invoke.return_value = Mock(content="SELECT COUNT(*) FROM users")
    return llm


@pytest.fixture
def orchestrator(mock_llm, test_db):
    """创建测试用编排器"""
    from src.core.orchestrator import NL2SQLOrchestrator
    return NL2SQLOrchestrator(
        llm=mock_llm,
        database_uri=f"sqlite:///{test_db}",
        config={"read_only": True}
    )
```

### 集成测试用例

```python
# tests/test_orchestrator_integration.py
import pytest
from src.core.types import QueryStatus


def test_e2e_simple_query(orchestrator):
    """端到端测试 - 简单查询"""
    result = orchestrator.ask("有多少用户?")
    
    assert result.status == QueryStatus.SUCCESS
    assert result.sql
    assert "SELECT" in result.sql.upper()
    assert result.explanation


def test_e2e_with_where(orchestrator):
    """端到端测试 - 带条件查询"""
    result = orchestrator.ask("订单金额大于100的有多少?")
    
    assert result.status == QueryStatus.SUCCESS
    assert result.sql
    assert "WHERE" in result.sql.upper() or ">" in result.sql


def test_e2e_with_join(orchestrator):
    """端到端测试 - 关联查询"""
    result = orchestrator.ask("每个用户的订单总额是多少?")
    
    assert result.status == QueryStatus.SUCCESS
    assert result.sql
    # 验证包含 JOIN 或子查询
    assert "JOIN" in result.sql.upper() or "user_id" in result.sql.lower()


def test_e2e_with_group_by(orchestrator):
    """端到端测试 - 分组查询"""
    result = orchestrator.ask("每个状态有多少订单?")
    
    assert result.status == QueryStatus.SUCCESS
    assert result.sql
    assert "GROUP BY" in result.sql.upper()


def test_e2e_security_rejection(orchestrator):
    """端到端测试 - 安全拒绝"""
    # 注入危险SQL的mock
    orchestrator.llm.invoke.return_value = Mock(content="DROP TABLE users")
    
    result = orchestrator.ask("删除用户表")
    
    assert result.status == QueryStatus.SECURITY_REJECTED
    assert result.security is not None
    assert result.security.is_valid is False


def test_e2e_execution_error(orchestrator):
    """端到端测试 - 执行错误"""
    # 模拟生成无效SQL
    orchestrator.llm.invoke.return_value = Mock(content="SELECT * FROM nonexistent")
    
    result = orchestrator.ask("查询不存在的表")
    
    # 可能触发执行错误或安全错误
    assert result.status in [QueryStatus.EXECUTION_ERROR, QueryStatus.SECURITY_REJECTED]
```

### 测试问题集

```json
// tests/fixtures/questions.json
{
  "simple_queries": [
    {"question": "有多少用户?", "expected_keywords": ["SELECT", "COUNT"]},
    {"question": "列出所有产品", "expected_keywords": ["SELECT", "products"]}
  ],
  "conditional_queries": [
    {"question": "年龄大于25的用户有哪些?", "expected_keywords": ["WHERE", ">", "25"]},
    {"question": "已完成的订单", "expected_keywords": ["WHERE", "status"]}
  ],
  "aggregate_queries": [
    {"question": "平均订单金额是多少?", "expected_keywords": ["AVG"]},
    {"question": "销售额最高的产品", "expected_keywords": ["ORDER BY", "DESC", "MAX"]}
  ],
  "join_queries": [
    {"question": "每个用户的订单数量", "expected_keywords": ["JOIN", "GROUP BY"]},
    {"question": "用户及其订单详情", "expected_keywords": ["JOIN"]}
  ],
  "time_queries": [
    {"question": "今天的订单", "expected_time_conversion": true},
    {"question": "上周的订单", "expected_time_conversion": true}
  ],
  "security_tests": [
    {"question": "删除所有数据", "should_reject": true, "danger_keyword": "DELETE"},
    {"question": "显示所有表", "should_reject": false}
  ]
}
```

### 验收标准
- [ ] 简单查询端到端通过
- [ ] 条件查询端到端通过
- [ ] 聚合查询端到端通过
- [ ] 关联查询端到端通过
- [ ] 安全拦截正常工作
- [ ] 执行错误正确处理

---

## 配置文件

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

---

## 使用示例

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
