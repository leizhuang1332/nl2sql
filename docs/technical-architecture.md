# NL2SQL 智能问数项目 - 技术架构文档

## 1. 技术栈选型

### 1.1 核心框架 (LangChain 1.0+)

| 包名 | 版本 | 用途 |
|------|------|------|
| `langchain` | >=1.2.0 | 核心框架 |
| `langchain-core` | >=1.2.0 | 核心接口与原语 |
| `langchain-openai` | >=1.0.0 | OpenAI LLM 集成 |
| `langchain-community` | >=0.3.0 | 社区工具 (SQLDatabase) |
| `langgraph` | >=1.0.0 | Agent 运行时 |

### 1.2 数据库驱动

| 数据库 | 推荐驱动 | 版本 |
|--------|----------|------|
| SQLite | 内置 | - |
| PostgreSQL | `psycopg2-binary` 或 `asyncpg` | >=2.9.0 |
| MySQL | `pymysql` | >=1.1.0 |

### 1.3 辅助依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| `sqlalchemy` | >=2.0.0 | 数据库 ORM |
| `langsmith` | latest | 可观测性 (可选) |
| `pydantic` | >=2.0.0 | 数据验证 |

### 1.4 Python 版本要求

```
Python >= 3.10
```

---

## 2. 项目架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户请求层                                │
│                   (API / Web Interface)                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                      编排调度层                                  │
│                   (NL2SQL Orchestrator)                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  语义映射 → Schema组装 → SQL生成 → 安全验证 → 执行修正  │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼──────┐  ┌──────▼──────┐  ┌─────▼─────┐
│  语义映射模块 │  │Schema模块   │  │ SQL生成模块│
│  (semantic)  │  │ (schema)    │  │(generation)│
└───────────────┘  └─────────────┘  └───────────┘
        │                 │                 │
┌───────▼──────┐  ┌──────▼──────┐  ┌─────▼─────┐
│ 安全验证模块 │  │ 执行修正模块 │  │结果解释模块│
│  (security)  │  │ (execution)  │  │(explanation)
└───────────────┘  └─────────────┘  └───────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                       数据层                                      │
│                  (SQLDatabase + DB)                              │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 模块调用流程

```
用户提问
    │
    ▼
┌───────────────────────────────┐
│    SemanticMapper (语义映射)   │
│  - 字段映射                    │
│  - 时间表达式                  │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│   SchemaManager (Schema管理)   │
│  - 表结构获取                   │
│  - 采样数据                    │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│   SQLGenerator (SQL生成)       │
│  - Prompt 模板                 │
│  - Few-shot 示例               │
│  - LLM 调用                   │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│  SecurityValidator (安全验证)   │
│  - 关键字检查                  │
│  - 表/列白名单                │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│  QueryExecutor (执行与修正)    │
│  - SQL 执行                   │
│  - 错误捕获                   │
│  - LLM 修正重试               │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│  ResultExplainer (结果解释)    │
│  - 数据分析                   │
│  - 自然语言生成               │
└───────────────┬───────────────┘
                │
                ▼
           返回结果
```

---

## 3. 项目结构

```
nl2sql/
├── src/
│   ├── __init__.py
│   ├── main.py                 # 入口文件
│   ├── config.py               # 配置管理
│   │
│   ├── schema/                 # 模块1: Schema 理解
│   │   ├── __init__.py
│   │   ├── database_connector.py
│   │   ├── schema_extractor.py
│   │   ├── schema_doc_generator.py
│   │   └── schema_enhancer.py
│   │
│   ├── generation/             # 模块2: SQL 生成
│   │   ├── __init__.py
│   │   ├── sql_generator.py
│   │   ├── few_shot_manager.py
│   │   ├── prompts.py
│   │   ├── llm_factory.py
│   │   └── sql_validator.py
│   │
│   ├── execution/              # 模块3: 执行与修正
│   │   ├── __init__.py
│   │   ├── query_executor.py
│   │   ├── result_handler.py
│   │   ├── error_analyzer.py
│   │   ├── retry_strategy.py
│   │   └── query_monitor.py
│   │
│   ├── semantic/               # 模块4: 语义映射
│   │   ├── __init__.py
│   │   ├── semantic_mapper.py
│   │   ├── config_manager.py
│   │   ├── vector_matcher.py
│   │   └── time_parser.py
│   │
│   ├── security/               # 模块5: 安全验证
│   │   ├── __init__.py
│   │   ├── sql_validator.py
│   │   ├── permission_manager.py
│   │   ├── sensitive_filter.py
│   │   ├── injection_detector.py
│   │   └── audit_logger.py
│   │
│   ├── explanation/            # 模块6: 结果解释
│   │   ├── __init__.py
│   │   ├── result_explainer.py
│   │   ├── data_analyst.py
│   │   ├── formatters.py
│   │   └── summarizer.py
│   │
│   └── core/                   # 核心编排
│       ├── __init__.py
│       ├── orchestrator.py     # 主调度器
│       └── types.py            # 类型定义
│
├── config/
│   ├── settings.yaml           # 应用配置
│   ├── security_policy.json    # 安全策略
│   └── semantic_mappings.json  # 语义映射配置
│
├── tests/
│   ├── test_schema.py
│   ├── test_generation.py
│   ├── test_execution.py
│   ├── test_semantic.py
│   ├── test_security.py
│   └── test_explanation.py
│
├── docs/
│   ├── core-modules-1.md       # 各模块详细设计
│   ├── core-modules-2.md
│   ├── core-modules-3.md
│   ├── core-modules-4.md
│   ├── core-modules-5.md
│   └── core-modules-6.md
│
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 4. 核心类设计

### 4.1 NL2SQL 编排器

```python
# src/core/orchestrator.py
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI

class NL2SQLOrchestrator:
    """
    NL2SQL 核心编排器
    协调所有模块完成从自然语言到查询结果的完整流程
    """
    
    def __init__(
        self,
        llm: ChatOpenAI,
        db_uri: str,
        config: Dict[str, Any]
    ):
        self.llm = llm
        self.db_uri = db_uri
        self.config = config
        
        # 初始化各模块
        self._init_modules()
    
    def _init_modules(self):
        """初始化所有模块"""
        # TODO: 初始化各个模块实例
        pass
    
    def ask(self, question: str) -> Dict[str, Any]:
        """
        处理用户提问
        返回: { success, sql, result, explanation }
        """
        pass
```

### 4.2 配置管理

```python
# src/config.py
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    """应用配置"""
    
    # LLM 配置
    openai_api_key: str
    openai_model: str = "gpt-4o"
    
    # 数据库配置
    database_uri: str
    
    # 安全配置
    read_only: bool = True
    allowed_tables: Optional[List[str]] = None
    
    # 执行配置
    max_retries: int = 3
    timeout: int = 30
    
    class Config:
        env_file = ".env"
```

---

## 5. 安装与依赖

### 5.1 requirements.txt

```
# Core
langchain>=1.2.0
langchain-core>=1.2.0
langchain-openai>=1.0.0
langchain-community>=0.3.0
langgraph>=1.0.0

# Database
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0  # PostgreSQL (可选)
pymysql>=1.1.0         # MySQL (可选)

# Utilities
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0

# Optional
langsmith>=0.1.0  # 可观测性
```

### 5.2 安装命令

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key
```

---

## 6. 快速开始示例

```python
# src/main.py
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
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
    db_uri=settings.database_uri,
    config=settings.model_dump()
)

# 处理问题
result = orchestrator.ask("上个月的销售额是多少?")

print(result["explanation"])
```

---

## 7. 版本信息

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | >=3.10 | 最低要求 |
| LangChain | 1.2.x | 核心框架 |
| LangGraph | 1.0.x | Agent 运行时 |
| 项目 | 0.1.0 | 初始版本 |

---

## 8. 后续步骤

1. 初始化项目结构
2. 安装依赖
3. 实现核心编排器
4. 逐个实现 6 个模块
5. 编写单元测试
6. 集成测试
