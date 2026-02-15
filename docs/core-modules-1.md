# 模块一：Schema 理解与表示模块 - 详细实现计划

## 1.1 模块目标

让 LLM 能够"看懂"数据库结构，包括：
- 表结构（表名、字段名、字段类型、主键、外键）
- 字段注释/业务含义
- 数据样例（帮助理解数据分布和格式）
- 表之间的关系

---

## 1.2 核心功能设计

### 1.2.1 数据库连接管理（支持多数据源）

```python
# src/schema/database_connector.py
from langchain_community.utilities import SQLDatabase
from typing import Optional, List, Dict, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class DatabaseType(Enum):
    """支持的数据库类型"""
    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    ORACLE = "oracle"
    # 未来扩展
    ELASTICSEARCH = "elasticsearch"
    REDIS = "redis"

class DatabaseConnector:
    """
    数据库连接管理器
    
    支持多种数据库类型，MVP 仅实现 SQLite，保持可扩展性
    """
    
    # 数据库类型到 URI 前缀的映射
    URI_PREFIXES = {
        DatabaseType.SQLITE: "sqlite:///",
        DatabaseType.MYSQL: "mysql+pymysql://",
        DatabaseType.POSTGRESQL: "postgresql://",
        DatabaseType.ORACLE: "oracle://",
    }
    
    def __init__(
        self,
        db_type: Union[str, DatabaseType] = DatabaseType.SQLITE,
        host: str = "localhost",
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        uri: str = None  # 直接传入 URI
    ):
        """
        初始化数据库连接器
        
        Args:
            db_type: 数据库类型 (sqlite/mysql/postgresql/oracle)
            host: 主机地址
            port: 端口
            database: 数据库名
            user: 用户名
            password: 密码
            uri: 直接传入完整 URI（优先级最高）
        """
        # 确定数据库类型
        if isinstance(db_type, str):
            db_type = DatabaseType(db_type.lower())
        self.db_type = db_type
        
        # 构建 URI
        if uri:
            self.db_uri = uri
        else:
            self.db_uri = self._build_uri(
                db_type, host, port, database, user, password
            )
        
        self._db: Optional[SQLDatabase] = None
    
    def _build_uri(
        self,
        db_type: DatabaseType,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str
    ) -> str:
        """构建数据库 URI"""
        if db_type == DatabaseType.SQLITE:
            # SQLite: sqlite:///database.db
            return f"sqlite:///{database}"
        
        # 其他数据库
        prefix = self.URI_PREFIXES.get(db_type, "")
        port_str = f":{port}" if port else ""
        auth = f"{user}:{password}@" if user else ""
        
        return f"{prefix}{auth}{host}{port_str}/{database}"
    
    @property
    def db(self) -> SQLDatabase:
        """延迟加载数据库连接"""
        if self._db is None:
            self._db = SQLDatabase.from_uri(self.db_uri)
        return self._db
    
    def get_usable_tables(self) -> List[str]:
        """获取可用的表名列表"""
        return self.db.get_usable_table_names()
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            self.db.run("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    @staticmethod
    def from_config(config: Dict) -> "DatabaseConnector":
        """从配置字典创建连接器"""
        return DatabaseConnector(
            db_type=config.get("type", "sqlite"),
            host=config.get("host", "localhost"),
            port=config.get("port"),
            database=config.get("database"),
            user=config.get("user"),
            password=config.get("password"),
            uri=config.get("uri")
        )


# ============================================================================
# 扩展：未来支持更多数据源
# ============================================================================

class ElasticsearchConnector:
    """Elasticsearch 连接器（预留扩展）"""
    pass

class RedisConnector:
    """Redis 连接器（预留扩展）"""
    pass

class DatabaseConnectorFactory:
    """数据库连接器工厂"""
    
    @staticmethod
    def create(connector_type: str, **kwargs) -> DatabaseConnector:
        """创建数据库连接器"""
        connectors = {
            "sqlite": DatabaseConnector,
            "mysql": DatabaseConnector,
            "postgresql": DatabaseConnector,
            "oracle": DatabaseConnector,
            # 未来扩展
            # "elasticsearch": ElasticsearchConnector,
            # "redis": RedisConnector,
        }
        
        if connector_type not in connectors:
            raise ValueError(f"不支持的数据库类型: {connector_type}")
        
        return connectors[connector_type](**kwargs)
```

### 1.2.2 Schema 信息提取器

```python
# src/schema/schema_extractor.py
from typing import Dict, List, Any
import re

class SchemaExtractor:
    """Schema 信息提取器"""
    
    def __init__(self, database_connector: DatabaseConnector):
        self.db = database_connector.db
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        获取单个表的完整 Schema 信息
        返回：表结构、字段详情、采样数据
        """
        # 1. 获取 DDL（建表语句）
        ddl = self.db.get_table_info([table_name])
        
        # 2. 获取采样数据（用于理解数据分布）
        sample_data = self._get_sample_data(table_name)
        
        # 3. 提取字段详情
        columns = self._extract_columns(ddl)
        
        return {
            "table_name": table_name,
            "ddl": ddl,
            "columns": columns,
            "sample_data": sample_data
        }
    
    def _get_sample_data(self, table_name: str, limit: int = 3) -> List[Dict]:
        """获取表的前 N 条数据"""
        try:
            result = self.db.run(f"SELECT * FROM {table_name} LIMIT {limit}")
            # 解析结果为字典列表
            return self._parse_result(result)
        except Exception:
            return []
    
    def _extract_columns(self, ddl: str) -> List[Dict]:
        """从 DDL 中提取字段信息"""
        columns = []
        # 简单正则提取字段（实际可用 sqlparse 库）
        pattern = r'(\w+)\s+(\w+(?:\(\d+\))?)'
        for match in re.finditer(pattern, ddl):
            columns.append({
                "name": match.group(1),
                "type": match.group(2)
            })
        return columns
    
    def _parse_result(self, result: str) -> List[Dict]:
        """解析 SQL 查询结果"""
        # 实现结果解析逻辑
        pass
```

### 1.2.3 Schema 文档生成器

```python
# src/schema/schema_doc_generator.py
from typing import List, Dict
from .schema_extractor import SchemaExtractor

class SchemaDocGenerator:
    """Schema 文档生成器 - 生成 LLM 可读的 Schema 描述"""
    
    def __init__(self, schema_extractor: SchemaExtractor):
        self.extractor = schema_extractor
    
    def generate_full_schema_doc(self, table_names: List[str] = None) -> str:
        """
        生成完整的 Schema 文档
        可指定表名列表，不指定则获取所有表
        """
        if table_names is None:
            table_names = self.extractor.db.get_usable_table_names()
        
        schema_docs = []
        for table in table_names:
            schema_info = self.extractor.get_table_schema(table)
            doc = self._format_table_doc(schema_info)
            schema_docs.append(doc)
        
        return "\n\n".join(schema_docs)
    
    def _format_table_doc(self, schema_info: Dict) -> str:
        """格式化单个表的文档"""
        lines = [
            f"## 表: {schema_info['table_name']}",
            "",
            "### 结构:",
            f"{schema_info['ddl']}",
            "",
            "### 示例数据:"
        ]
        
        # 添加示例数据
        if schema_info['sample_data']:
            for row in schema_info['sample_data']:
                lines.append(f"- {row}")
        
        return "\n".join(lines)
    
    def generate_compact_schema(self, table_names: List[str] = None) -> str:
        """
        生成精简版 Schema（只包含表名和字段）
        适用于上下文窗口有限的情况
        """
        if table_names is None:
            table_names = self.extractor.db.get_usable_table_names()
        
        lines = ["## 数据库 Schema", ""]
        for table in table_names:
            schema_info = self.extractor.get_table_schema(table)
            lines.append(f"### {table}")
            for col in schema_info['columns']:
                lines.append(f"- {col['name']}: {col['type']}")
            lines.append("")
        
        return "\n".join(lines)
```

---

## 1.3 增强功能

### 1.3.1 字段注释/业务含义注入

**为什么需要这一步？**

| 问题场景 | 后果 |
|----------|------|
| 字段名 `amount` | LLM 不知道是"销售额"还是"退款金额" |
| 字段名 `status` | LLM 不知道 0/1 代表什么状态 |
| 日期字段 `create_time` | 不知道是时间戳还是日期字符串 |
| 多表关联 | 不知道 `order_id` 应该关联哪张表 |

**缺少这步会导致**：
1. **SQL 生成错误** - 选错字段（如问销售额选中 cost 字段）
2. **语义歧义** - 无法理解业务术语与技术字段的对应
3. **关联查询失败** - 多表 join 时无法正确关联

```python
# src/schema/schema_enhancer.py
from typing import Dict, Optional

class SchemaEnhancer:
    """Schema 增强器 - 添加业务语义"""
    
    def __init__(self):
        # 从配置文件或数据库加载字段映射
        self.field_descriptions: Dict[str, Dict[str, str]] = {}
    
    def add_field_description(self, table: str, field: str, description: str):
        """添加字段的业务含义描述"""
        if table not in self.field_descriptions:
            self.field_descriptions[table] = {}
        self.field_descriptions[table][field] = description
    
    def enhance_schema(self, schema_doc: str, table_name: str) -> str:
        """在 Schema 文档中注入字段描述"""
        if table_name not in self.field_descriptions:
            return schema_doc
        
        descriptions = self.field_descriptions[table_name]
        enhanced = schema_doc + "\n\n### 字段说明:\n"
        for field, desc in descriptions.items():
            enhanced += f"- {field}: {desc}\n"
        
        return enhanced
```

### 1.3.2 主键外键关系提取

```python
# src/schema/relationship_extractor.py
class RelationshipExtractor:
    """关系提取器 - 提取表之间的主外键关系"""
    
    def __init__(self, schema_extractor: SchemaExtractor):
        self.extractor = schema_extractor
    
    def extract_relationships(self, table_names: List[str]) -> Dict[str, List[Dict]]:
        """提取表之间的关系"""
        relationships = {}
        
        for table in table_names:
            schema_info = self.extractor.get_table_schema(table)
            # 分析 DDL 中的外键定义
            foreign_keys = self._extract_foreign_keys(schema_info['ddl'])
            if foreign_keys:
                relationships[table] = foreign_keys
        
        return relationships
    
    def _extract_foreign_keys(self, ddl: str) -> List[Dict]:
        """提取外键定义"""
        # 解析 FOREIGN KEY 语句
        pass
```

---

## 1.4 项目结构

```
src/
├── schema/
│   ├── __init__.py
│   ├── database_connector.py    # 数据库连接管理（支持多数据源）
│   ├── database_factory.py     # 数据库连接器工厂
│   ├── schema_extractor.py      # Schema 信息提取
│   ├── schema_doc_generator.py  # 文档生成
│   ├── schema_enhancer.py       # 业务语义增强
│   └── relationship_extractor.py # 关系提取
```

---

## 1.5 实现步骤

| 步骤 | 任务 | 优先级 |
|------|------|--------|
| 1 | 实现 DatabaseConnector 数据库连接（支持多类型） | P0 |
| 2 | 实现 DatabaseConnectorFactory 工厂模式 | P1 |
| 3 | 实现 SchemaExtractor 基本提取功能 | P0 |
| 4 | 实现 SchemaDocGenerator 文档生成 | P0 |
| 5 | 添加采样数据获取功能 | P1 |
| 6 | 实现 SchemaEnhancer 字段描述增强 | P1 |
| 7 | 实现 RelationshipExtractor 关系提取 | P2 |
| 8 | 添加单元测试 | P1 |

---

## 1.6 关键技术点

1. **LangChain SQLDatabase** - 官方提供的数据库工具类
2. **Factory 模式** - 支持多数据库类型扩展
3. **采样数据** - 帮助 LLM 理解数据格式和分布
4. **字段描述** - 解决技术字段与业务术语的映射（关键！）
5. **关系图谱** - 帮助 LLM 理解多表关联查询

---

## 1.7 数据库类型支持说明

| 数据库 | MVP 支持 | 扩展支持 | 说明 |
|--------|----------|----------|------|
| SQLite | ✅ P0 | - | MVP 首选 |
| MySQL | - | ✅ 预留 | 需安装 pymysql |
| PostgreSQL | - | ✅ 预留 | 需安装 psycopg2 |
| Oracle | - | ✅ 预留 | 需安装 cx_Oracle |
| Elasticsearch | - | ✅ 预留 | 未来扩展 |
| Redis | - | ✅ 预留 | 未来扩展 |

### 扩展新数据库类型的步骤

```python
# 1. 在 DatabaseType 枚举添加新类型
class DatabaseType(Enum):
    NEW_DB = "newdb"

# 2. 在 URI_PREFIXES 添加映射
URI_PREFIXES = {
    DatabaseType.NEW_DB: "newdb://",
}

# 3. 如需特殊处理，创建专门的 Connector 类
class NewDBConnector:
    pass
```

---

## 1.8 潜在挑战与解决方案

| 挑战 | 解决方案 |
|------|----------|
| 大规模数据库 Schema 过长 | 使用摘要/精简模式，或按需加载相关表 |
| 字段名无业务含义 | 提供配置文件或从注释中提取（必做！） |
| 外键关系不清晰 | 手动维护关系配置或从 DDL 解析 |
| 多数据库类型支持 | 使用 Factory 模式，预留扩展接口 |
| 非关系型数据库 | 针对 ES/Redis 设计专门的 Connector |
