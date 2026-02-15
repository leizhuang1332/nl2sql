# 模块一：Schema 理解与表示模块 - 分阶段实现计划

本文档将模块一拆分为多个 Phase，按优先级顺序实现。

---

## Phase 1: 核心基础 (MVP)

**目标**: 实现 SQLite 数据库连接 + 基本 Schema 提取

### 任务清单

| 任务 | 文件 | 优先级 |
|------|------|--------|
| 实现 DatabaseConnector（仅 SQLite） | `database_connector.py` | P0 |
| 实现 SchemaExtractor 基本提取 | `schema_extractor.py` | P0 |
| 单元测试 | `tests/test_schema_phase1.py` | P1 |

### 核心代码

```python
# src/schema/database_connector.py
from langchain_community.utilities import SQLDatabase
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class DatabaseConnector:
    """数据库连接管理器 - MVP 仅支持 SQLite"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._db: Optional[SQLDatabase] = None
    
    @property
    def db(self) -> SQLDatabase:
        """延迟加载"""
        if self._db is None:
            self._db = SQLDatabase.from_uri(f"sqlite:///{self.db_path}")
        return self._db
    
    def get_usable_tables(self) -> List[str]:
        return self.db.get_usable_table_names()
    
    def test_connection(self) -> bool:
        try:
            self.db.run("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False
```

```python
# src/schema/schema_extractor.py
from typing import Dict, List, Any

class SchemaExtractor:
    """Schema 信息提取器"""
    
    def __init__(self, db: SQLDatabase):
        self.db = db
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """获取表结构"""
        ddl = self.db.get_table_info([table_name])
        return {
            "table_name": table_name,
            "ddl": ddl,
            "columns": self._extract_columns(ddl)
        }
    
    def _extract_columns(self, ddl: str) -> List[Dict]:
        """提取字段（简化版）"""
        # 实际可用 sqlparse
        import re
        pattern = r'(\w+)\s+(\w+(?:\(\d+\))?)'
        return [
            {"name": m.group(1), "type": m.group(2)}
            for m in re.finditer(pattern, ddl)
        ]
```

### 验收标准

- [ ] SQLite 数据库连接成功
- [ ] 能获取表名列表
- [ ] 能获取表结构（DDL + 字段）
- [ ] 单元测试通过

---

## Phase 2: 文档生成

**目标**: 生成 LLM 可读的 Schema 文档 + 采样数据

### 任务清单

| 任务 | 文件 | 优先级 |
|------|------|--------|
| 实现 SchemaDocGenerator | `schema_doc_generator.py` | P0 |
| 添加采样数据功能 | `schema_extractor.py` | P1 |
| 单元测试 | `tests/test_schema_phase2.py` | P1 |

### 核心代码

```python
# src/schema/schema_doc_generator.py
from typing import List, Dict

class SchemaDocGenerator:
    """Schema 文档生成器"""
    
    def __init__(self, schema_extractor):
        self.extractor = schema_extractor
    
    def generate_full_doc(self, table_names: List[str] = None) -> str:
        """生成完整文档"""
        if table_names is None:
            table_names = self.extractor.db.get_usable_table_names()
        
        docs = []
        for table in table_names:
            schema = self.extractor.get_table_schema(table)
            docs.append(self._format_table(schema))
        
        return "\n\n".join(docs)
    
    def _format_table(self, schema: Dict) -> str:
        lines = [f"## 表: {schema['table_name']}", ""]
        lines.append(f"结构:\n{schema['ddl']}")
        return "\n".join(lines)
```

### 验收标准

- [ ] 能生成完整 Schema 文档
- [ ] 支持指定表名列表
- [ ] 支持采样数据

---

## Phase 3: 语义增强

**目标**: 字段注释/业务含义注入，解决语义歧义

### 任务清单

| 任务 | 文件 | 优先级 |
|------|------|--------|
| 实现 SchemaEnhancer | `schema_enhancer.py` | P1 |
| 实现配置文件加载 | `schema_enhancer.py` | P1 |
| 单元测试 | `tests/test_schema_phase3.py` | P1 |

### 核心代码

```python
# src/schema/schema_enhancer.py
from typing import Dict

class SchemaEnhancer:
    """Schema 增强器 - 添加业务语义"""
    
    def __init__(self):
        self.field_descriptions: Dict[str, Dict[str, str]] = {}
    
    def add_field_description(self, table: str, field: str, description: str):
        """添加字段描述"""
        if table not in self.field_descriptions:
            self.field_descriptions[table] = {}
        self.field_descriptions[table][field] = description
    
    def enhance_schema(self, schema_doc: str, table_name: str) -> str:
        """注入字段描述"""
        if table_name not in self.field_descriptions:
            return schema_doc
        
        descriptions = self.field_descriptions[table_name]
        enhanced = schema_doc + "\n\n字段说明:\n"
        for field, desc in descriptions.items():
            enhanced += f"- {field}: {desc}\n"
        
        return enhanced
    
    def load_from_config(self, config: Dict):
        """从配置加载"""
        self.field_descriptions = config.get("field_mappings", {})
```

### 配置示例

```json
// config/field_descriptions.json
{
    "sales": {
        "amount": "销售收入金额（元）",
        "cost": "成本金额（元）",
        "profit": "利润金额（元）"
    },
    "orders": {
        "status": "订单状态: 0-待付款, 1-已付款, 2-已完成, 3-已取消",
        "create_time": "创建时间（时间戳）"
    }
}
```

### 验收标准

- [ ] 能添加字段描述
- [ ] 能从配置文件加载
- [ ] 增强后的 Schema 包含业务含义

---

## Phase 4: 关系提取

**目标**: 提取表之间的主键外键关系

### 任务清单

| 任务 | 文件 | 优先级 |
|------|------|--------|
| 实现 RelationshipExtractor | `relationship_extractor.py` | P2 |
| 支持手动配置关系 | `relationship_extractor.py` | P2 |
| 单元测试 | `tests/test_schema_phase4.py` | P2 |

### 核心代码

```python
# src/schema/relationship_extractor.py
from typing import Dict, List

class RelationshipExtractor:
    """关系提取器"""
    
    def __init__(self, schema_extractor):
        self.extractor = schema_extractor
        self.manual_relationships: Dict[str, List[Dict]] = {}
    
    def extract_relationships(self, table_names: List[str]) -> Dict[str, List[Dict]]:
        """提取关系"""
        relationships = {}
        for table in table_names:
            # 从 DDL 解析外键
            fk = self._extract_foreign_keys(table)
            # 合并手动配置
            manual = self.manual_relationships.get(table, [])
            relationships[table] = fk + manual
        return relationships
    
    def add_relationship(self, table: str, from_col: str, to_table: str, to_col: str):
        """手动添加关系"""
        if table not in self.manual_relationships:
            self.manual_relationships[table] = []
        self.manual_relationships[table].append({
            "from": from_col,
            "to_table": to_table,
            "to_col": to_col
        })
```

### 验收标准

- [ ] 能从 DDL 解析外键关系
- [ ] 支持手动配置关系
- [ ] 能生成关系图文档

---

## Phase 5: 多数据源支持

**目标**: 支持 MySQL/PostgreSQL/Oracle，扩展为工厂模式

### 任务清单

| 任务 | 文件 | 优先级 |
|------|------|--------|
| 扩展 DatabaseConnector | `database_connector.py` | P2 |
| 实现 DatabaseConnectorFactory | `database_factory.py` | P2 |
| 单元测试 | `tests/test_schema_phase5.py` | P2 |

### 核心代码

```python
# src/schema/database_factory.py
from enum import Enum

class DatabaseType(Enum):
    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    ORACLE = "oracle"

class DatabaseConnectorFactory:
    """数据库连接器工厂"""
    
    @staticmethod
    def create(db_type: str, **kwargs):
        db_type = DatabaseType(db_type.lower())
        
        if db_type == DatabaseType.SQLITE:
            from .database_connector import DatabaseConnector
            return DatabaseConnector(db_path=kwargs.get("database"))
        
        # 未来扩展
        raise NotImplementedError(f"暂不支持: {db_type.value}")
```

### 验收标准

- [ ] 支持 SQLite（已有）
- [ ] 预留 MySQL 扩展接口
- [ ] 预留 PostgreSQL 扩展接口

---

## 完整项目结构

```
src/schema/
├── __init__.py
├── database_connector.py      # Phase 1
├── database_factory.py         # Phase 5
├── schema_extractor.py         # Phase 1
├── schema_doc_generator.py     # Phase 2
├── schema_enhancer.py          # Phase 3
└── relationship_extractor.py   # Phase 4
```

---

## Phase 依赖关系

```
Phase 1 (基础)
    ↓
Phase 2 (文档)  ← Phase 1
    ↓
Phase 3 (语义)  ← Phase 2
    ↓
Phase 4 (关系)  ← Phase 1
    ↓
Phase 5 (扩展)  ← Phase 1
```

---

## 实现优先级总结

| Phase | 优先级 | MVP 必须 | 预计工作量 |
|-------|--------|----------|-----------|
| Phase 1 | P0 | ✅ | 1-2 天 |
| Phase 2 | P0 | ✅ | 0.5-1 天 |
| Phase 3 | P1 | 可选 | 0.5-1 天 |
| Phase 4 | P2 | 可选 | 1 天 |
| Phase 5 | P2 | 可选 | 1-2 天 |
