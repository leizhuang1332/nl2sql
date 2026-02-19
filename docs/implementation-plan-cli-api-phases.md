# NL2SQL CLI & API 实现计划 (分阶段版本)

## 概述

实现 `src/main.py` 提供 CLI 和 FastAPI 双模式入口，完善配置系统支持 YAML 配置。

---

## Phase 1: 创建 YAML 配置文件

### Task 1: 创建 config/settings.yaml

**目标**: 创建 YAML 格式的配置文件

**步骤**:
1. 创建 `config/settings.yaml` 文件
2. 定义 LLM 配置（provider, model, api_key, temperature）
3. 定义 Database 配置（uri）
4. 定义 Security 配置（read_only, max_retries, timeout, allowed_tables）
5. 定义 Paths 配置（field_descriptions, semantic_mappings, security_policy）
6. 定义 API 配置（host, port, cors_origins）
7. 定义 Logging 配置（level, format）

**输出文件**: `config/settings.yaml`

**验收标准**:
- [ ] `config/settings.yaml` 文件存在
- [ ] 包含所有必要的配置节

---

## Phase 2: 更新配置系统

### Task 2: 更新 src/config.py

**目标**: 支持 YAML 配置加载，与 .env 兼容

**步骤**:
1. 添加 `pyyaml` 导入
2. 添加 `lru_cache` 装饰器
3. 创建 `get_yaml_settings()` 类方法
4. 实现配置合并逻辑（yaml < .env < explicit kwargs）
5. 更新字段命名（添加 llm_ 前缀）
6. 添加 API 相关配置字段

**修改文件**: `src/config.py`

**验收标准**:
- [ ] `Settings` 类可加载 YAML 配置
- [ ] `.env` 变量优先级高于 YAML
- [ ] 显式参数优先级最高

---

## Phase 3: 创建主入口

### Task 3: 创建 src/main.py

**目标**: 提供 CLI 和 FastAPI 双模式入口

**步骤**:

#### 3.1 创建应用工厂
1. 定义 `create_orchestrator(settings)` 函数
2. 使用现有 `create_llm()` 工厂创建 LLM
3. 构建 orchestrator 配置字典

#### 3.2 CLI 模式实现
1. 创建 `run_cli(args, settings)` 函数
2. 执行单次查询并格式化输出
3. 显示 SQL、结果、解释、执行时间

#### 3.3 FastAPI 模式实现
1. 创建 `create_app(settings)` 工厂函数
2. 定义 QueryRequest / QueryResponse 模型
3. 实现 `/query` 端点 - POST
4. 实现 `/tables` 端点 - GET
5. 实现 `/schema/{table_name}` 端点 - GET
6. 实现 `/health` 端点 - GET
7. 添加 startup 事件初始化 orchestrator
8. 配置 CORS

#### 3.4 入口点
1. 创建 `main()` 函数
2. 解析命令行参数（cli / api 子命令）
3. 配置日志
4. 根据模式启动对应服务

**输出文件**: `src/main.py`

**验收标准**:
- [ ] `python -m src.main --help` 正常显示
- [ ] CLI 模式可执行查询
- [ ] API 模式可启动服务

---

## Phase 4: 更新依赖

### Task 4: 更新依赖

**目标**: 添加 FastAPI 相关依赖

**步骤**:
1. 在 `pyproject.toml` 添加:
   - `fastapi >= 0.100.0`
   - `uvicorn >= 0.20.0`
   - `pyyaml >= 6.0`
2. 运行 `pip install -r requirements.txt` 更新环境

**修改文件**: `pyproject.toml`, `requirements.txt`

**验收标准**:
- [ ] 依赖安装成功
- [ ] 无导入错误

---

## 技术细节

### 配置加载优先级

```
config/settings.yaml  (默认配置)
        ↓
.env 变量          (覆盖 yaml)
        ↓
显式 kwargs       (最高优先级 - 用于测试)
```

### API 设计

| 端点 | 方法 | 请求体 | 响应 |
|------|------|--------|------|
| `/health` | GET | - | `{"status": "healthy"}` |
| `/tables` | GET | - | `{"tables": ["users", "orders"]}` |
| `/schema/{table}` | GET | - | `{"table": "...", "schema": {...}}` |
| `/query` | POST | `{"question": "..."}` | `QueryResponse` |

### QueryResponse 结构

```python
class QueryResponse(BaseModel):
    question: str
    status: str
    sql: Optional[str] = None
    explanation: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    metadata: dict = {}
```

---

## 预期输出文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `config/settings.yaml` | 新建 | YAML 配置文件 |
| `src/config.py` | 修改 | 添加 YAML 加载支持 |
| `src/main.py` | 新建 | CLI + API 入口 |
| `pyproject.toml` | 修改 | 添加依赖 |
| `requirements.txt` | 修改 | 添加依赖 |

---

## 执行顺序

1. Phase 1 (Task 1): 创建 settings.yaml
2. Phase 2 (Task 2): 更新 config.py
3. Phase 3 (Task 3): 创建 main.py
4. Phase 4 (Task 4): 更新依赖

---

## 风险与注意事项

| 风险 | 缓解措施 |
|------|----------|
| API Key 安全 | 使用环境变量引用，不写入 yaml |
| 数据库路径 | 使用绝对路径或相对于项目根目录 |
| CORS | 默认允许所有，生产环境需配置 |
| 并发 | 全局单例 orchestrator，注意线程安全 |
