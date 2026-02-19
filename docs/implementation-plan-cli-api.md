# NL2SQL CLI & API 实现计划

## 概述

实现 `src/main.py` 提供 CLI 和 FastAPI 双模式入口，完善配置系统支持 YAML 配置。

---

## 任务清单

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

---

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

---

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

---

### Task 4: 更新依赖

**目标**: 添加 FastAPI 相关依赖

**步骤**:
1. 在 `pyproject.toml` 添加:
   - `fastapi >= 0.100.0`
   - `uvicorn >= 0.20.0`
   - `pyyaml >= 6.0`
2. 运行 `pip install -r requirements.txt` 更新环境

**修改文件**: `pyproject.toml`, `requirements.txt`

---

### Task 5: 测试验证

**目标**: 验证功能正常工作

**步骤**:

#### 5.1 测试 CLI 模式

##### 5.1.1 基本查询测试
```bash
python -m src.main cli "查询所有用户"
```
预期: 成功执行，返回用户列表

##### 5.1.2 聚合查询测试
```bash
python -m src.main cli "统计订单数量"
```
预期: 成功执行，返回 COUNT 结果

##### 5.1.3 条件查询测试
```bash
python -m src.main cli "查询年龄大于25岁的用户"
```
预期: 成功执行，返回 WHERE 条件过滤结果

##### 5.1.4 连接查询测试
```bash
python -m src.main cli "查询每个用户的订单"
```
预期: 成功执行，返回 JOIN 查询结果

##### 5.1.5 错误查询测试
```bash
python -m src.main cli "删除所有数据"
```
预期: 安全拒绝，返回 security_rejected 状态

##### 5.1.6 帮助信息测试
```bash
python -m src.main --help
python -m src.main cli --help
```
预期: 显示帮助信息

#### 5.2 测试 API 模式

##### 5.2.1 启动服务
```bash
python -m src.main api --port 8000 &
```

##### 5.2.2 健康检查端点
```bash
curl http://localhost:8000/health
```
预期: `{"status":"healthy"}`

##### 5.2.3 列出表端点
```bash
curl http://localhost:8000/tables
```
预期: `{"tables":["users","orders","products"]}`

##### 5.2.4 获取表结构端点
```bash
curl http://localhost:8000/schema/users
```
预期: 返回 users 表的完整结构

##### 5.2.5 执行查询端点 - 成功案例
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "有多少用户?"}'
```
预期:
```json
{
  "question": "有多少用户?",
  "status": "success",
  "sql": "SELECT COUNT(*) FROM users",
  "explanation": "结果是 [4] 个用户",
  "error_message": null,
  "execution_time": 0.XXX,
  "metadata": {}
}
```

##### 5.2.6 执行查询端点 - 安全拒绝
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "删除所有用户"}'
```
预期:
```json
{
  "question": "删除所有用户",
  "status": "security_rejected",
  "sql": "DELETE FROM users",
  "explanation": null,
  "error_message": "安全验证失败: 危险操作",
  "execution_time": 0.XXX,
  "metadata": {}
}
```

##### 5.2.7 执行查询端点 - 错误处理
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": ""}'
```
预期: 返回 422 验证错误

##### 5.2.8 不返回解释测试
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question", "include_ex": "查询用户planation": false}'
```
预期: explanation 字段为 null

##### 5.2.9 并发请求测试
```bash
# 同时发送多个请求
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"question": "查询用户1"}' &
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"question": "查询用户2"}' &
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"question": "查询用户3"}' &
wait
```
预期: 所有请求成功返回，无竞态条件

##### 5.2.10 大数据量结果测试
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "列出所有订单和产品"}'
```
预期: 返回大量数据，响应正常

#### 5.3 测试配置加载

##### 5.3.1 默认配置加载
```bash
# 无任何配置文件
python -c "from src.config import Settings; s = Settings(); print(s.database_uri)"
```
预期: 使用默认值 `sqlite:///example.db`

##### 5.3.2 YAML 配置加载
```bash
# 存在 settings.yaml
python -c "from src.config import Settings; s = Settings(); print(s.llm_model)"
```
预期: 读取 yaml 中的值

##### 5.3.3 .env 覆盖 YAML
```bash
# .env 中设置 DATABASE_URI
python -c "from src.config import Settings; s = Settings(); print(s.database_uri)"
```
预期: .env 值优先于 yaml

##### 5.3.4 显式参数覆盖所有
```bash
python -c "from src.config import Settings; s = Settings(database_uri='sqlite:///test.db'); print(s.database_uri)"
```
预期: 显式参数优先级最高

#### 5.4 测试边界情况

##### 5.4.1 空问题查询
```bash
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"question": ""}'
```
预期: 422 验证错误

##### 5.4.2 极长问题查询
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "重复查询语..."}'  # 10000+ 字符
```
预期: 正常处理或返回适当错误

##### 5.4.3 SQL 注入尝试
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "查询用户; DROP TABLE users;"}'
```
预期: 安全验证拒绝

##### 5.4.4 不存在的表查询
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "查询不存在的表"}'
```
预期: 执行错误，返回 execution_error 状态

##### 5.4.5 获取不存在表的结构
```bash
curl http://localhost:8000/schema/nonexistent
```
预期: 404 错误

#### 5.5 运行现有测试
```bash
python -m pytest tests/ -v
```

确保无回归问题

---

## 新增测试用例文件

### 5.6 创建 tests/test_cli.py

```python
# tests/test_cli.py
import pytest
import subprocess
import sys

class TestCLI:
    """CLI 模式测试"""
    
    def test_cli_help(self):
        """测试 CLI 帮助信息"""
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "NL2SQL" in result.stdout
    
    def test_cli_subcommand_help(self):
        """测试子命令帮助"""
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "cli", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "question" in result.stdout
    
    def test_cli_query_success(self):
        """测试 CLI 成功查询"""
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "cli", "查询所有用户"],
            capture_output=True, text=True
        )
        assert "Status: success" in result.stdout
        assert "SELECT" in result.stdout
    
    def test_cli_query_security_rejection(self):
        """测试 CLI 安全拒绝"""
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "cli", "删除所有用户"],
            capture_output=True, text=True
        )
        assert "security_rejected" in result.stdout
```

### 5.7 创建 tests/test_api.py

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from src.main import create_app
from src.config import Settings

@pytest.fixture
def client():
    """创建测试客户端"""
    settings = Settings()
    app = create_app(settings)
    return TestClient(app)

class TestAPI:
    """API 模式测试"""
    
    def test_health_endpoint(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_tables_endpoint(self, client):
        """测试列出表端点"""
        response = client.get("/tables")
        assert response.status_code == 200
        assert "tables" in response.json()
    
    def test_schema_endpoint_success(self, client):
        """测试获取表结构 - 成功"""
        response = client.get("/schema/users")
        assert response.status_code == 200
        assert "schema" in response.json()
    
    def test_schema_endpoint_not_found(self, client):
        """测试获取表结构 - 不存在"""
        response = client.get("/schema/nonexistent")
        assert response.status_code == 404
    
    def test_query_endpoint_success(self, client):
        """测试执行查询 - 成功"""
        response = client.post("/query", json={"question": "有多少用户?"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "sql" in data
    
    def test_query_endpoint_security_rejection(self, client):
        """测试执行查询 - 安全拒绝"""
        response = client.post("/query", json={"question": "删除所有用户"})
        assert response.status_code == 200
        assert response.json()["status"] == "security_rejected"
    
    def test_query_endpoint_validation_error(self, client):
        """测试执行查询 - 验证错误"""
        response = client.post("/query", json={"question": ""})
        assert response.status_code == 422
    
    def test_query_without_explanation(self, client):
        """测试不返回解释"""
        response = client.post(
            "/query",
            json={"question": "查询用户", "include_explanation": False}
        )
        assert response.status_code == 200
        assert response.json()["explanation"] is None
```

### 5.8 创建 tests/test_config.py

```python
# tests/test_config.py
import pytest
import os
import tempfile
from src.config import Settings

class TestConfig:
    """配置加载测试"""
    
    def test_default_settings(self):
        """测试默认配置"""
        s = Settings()
        assert s.database_uri == "sqlite:///example.db"
        assert s.read_only is True
    
    def test_yaml_loading(self):
        """测试 YAML 配置加载"""
        # 需要存在 settings.yaml
        s = Settings()
        # 验证 YAML 配置被加载
        assert hasattr(s, 'llm_provider')
    
    def test_env_override_yaml(self, monkeypatch):
        """测试环境变量覆盖 YAML"""
        monkeypatch.setenv("DATABASE_URI", "sqlite:///env_test.db")
        s = Settings()
        assert s.database_uri == "sqlite:///env_test.db"
    
    def test_explicit_override_all(self):
        """测试显式参数覆盖所有"""
        s = Settings(database_uri="sqlite:///explicit.db")
        assert s.database_uri == "sqlite:///explicit.db"
```

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

1. Task 1: 创建 settings.yaml
2. Task 2: 更新 config.py
3. Task 3: 创建 main.py
4. Task 4: 更新依赖
5. Task 5: 测试验证

---

## 风险与注意事项

| 风险 | 缓解措施 |
|------|----------|
| API Key 安全 | 使用环境变量引用，不写入 yaml |
| 数据库路径 | 使用绝对路径或相对于项目根目录 |
| CORS | 默认允许所有，生产环境需配置 |
| 并发 | 全局单例 orchestrator，注意线程安全 |

---

## 验收标准

### CLI 模式
- [ ] `python -m src.main --help` 显示帮助信息
- [ ] `python -m src.main cli --help` 显示 CLI 子命令帮助
- [ ] `python -m src.main cli "查询用户"` 正常工作
- [ ] `python -m src.main cli "统计订单数量"` 聚合查询正常
- [ ] `python -m src.main cli "查询年龄大于25岁的用户"` 条件查询正常
- [ ] `python -m src.main cli "删除所有用户"` 安全拒绝正常

### API 模式
- [ ] `python -m src.main api --port 8000` 启动成功
- [ ] `GET /health` 返回 `{"status": "healthy"}`
- [ ] `GET /tables` 返回表列表
- [ ] `GET /schema/users` 返回表结构
- [ ] `GET /schema/nonexistent` 返回 404
- [ ] `POST /query` 成功查询返回正确结果
- [ ] `POST /query` 安全拒绝返回 security_rejected
- [ ] `POST /query` 空问题返回 422 验证错误
- [ ] `POST /query` 关闭 explanation 返回 null
- [ ] 并发请求正常工作

### 配置加载
- [ ] 默认配置正常加载
- [ ] YAML 配置正确读取
- [ ] .env 覆盖 YAML 配置
- [ ] 显式参数优先级最高

### 测试套件
- [ ] tests/test_cli.py CLI 测试通过
- [ ] tests/test_api.py API 测试通过
- [ ] tests/test_config.py 配置测试通过
- [ ] 现有测试全部通过（无回归）
