# NL2SQL

基于 LangChain 的自然语言转 SQL 查询项目。

## 项目简介

NL2SQL 是一个能够将自然语言转换为 SQL 查询的工具，支持：

- **多数据源**：SQLite、MySQL、PostgreSQL、Oracle
- **多 LLM 提供商**：MiniMax、OpenAI、Anthropic、Ollama
- **语义映射**：将业务术语映射到数据库字段
- **安全验证**：SQL 注入检测、权限控制、只读模式
- **结果解释**：将查询结果转换为自然语言

**项目架构**：[docs/technical-architecture.md](https://github.com/leizhuang1332/nl2sql/blob/master/docs/technical-architecture.md)

**6 大核心模块**：[docs/nl2sql-core-modules.md](https://github.com/leizhuang1332/nl2sql/blob/master/docs/nl2sql-core-modules.md)

**编排层设计**：[docs/orchestrator-design.md](https://github.com/leizhuang1332/nl2sql/blob/master/docs/orchestrator-design.md)

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 配置文件

创建 `.env` 文件配置 API 密钥：

```bash
MINIMAX_API_KEY=your_api_key_here
```

或使用 YAML 配置文件 `config/settings.yaml`。

### 使用 CLI

```bash
# 查看所有表
python -m src.main cli tables

# 查看表结构
python -m src.main cli schema products

# 执行查询
python -m src.main cli query "查询所有价格大于100的产品"
python -m src.main cli query "统计订单数量" --show-sql
```

### 使用 API

```bash
# 启动 API 服务
python -m src.main api --port 8000
```

## API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/tables` | 获取所有表 |
| GET | `/schema/{table_name}` | 获取表结构 |
| POST | `/query` | 执行查询 |

### API 示例

```bash
# 健康检查
curl http://localhost:8000/health

# 获取表列表
curl http://localhost:8000/tables

# 获取表结构
curl http://localhost:8000/schema/products

# 执行查询
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "查询所有产品"}'
```

## 项目结构

```
nl2sql/
├── src/
│   ├── config.py          # 配置管理
│   ├── main.py           # CLI & API 入口
│   ├── core/
│   │   ├── orchestrator.py  # 编排器
│   │   └── types.py         # 类型定义
│   ├── schema/            # Schema 模块
│   ├── generation/        # SQL 生成模块
│   ├── execution/        # 查询执行模块
│   ├── semantic/         # 语义映射模块
│   ├── security/         # 安全模块
│   └── explanation/     # 结果解释模块
├── config/               # 配置文件
│   ├── settings.yaml
│   ├── field_descriptions.json
│   ├── semantic_mappings.json
│   └── security_policy.json
├── tests/               # 测试文件
└── example.db          # 示例数据库
```

## 配置说明

### 环境变量

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `MINIMAX_API_KEY` | MiniMax API 密钥 | - |
| `OPENAI_API_KEY` | OpenAI API 密钥 | - |
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | - |

### YAML 配置 (config/settings.yaml)

```yaml
llm:
  provider: minimax      # openai / minimax / anthropic / ollama / custom
  model: MiniMax-M2.5
  api_key: ${MINIMAX_API_KEY}
  temperature: 0.7

database:
  uri: sqlite:///example.db

security:
  read_only: true
  max_retries: 3

api:
  host: 0.0.0.0
  port: 8000
```

## 运行测试

```bash
pytest tests/
```

## License

MIT
