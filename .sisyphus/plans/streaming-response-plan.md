# NL2SQL 流式响应功能开发工作计划

## 概述

为 NL2SQL 项目的 CLI 调用和 REST API 增加流式响应（Streaming）支持，使用户能够实时获取查询进度和中间结果，提升用户体验。

## 目标

1. CLI 命令支持 `--stream` 参数，实现实时流式输出
2. REST API 新增 `/query/stream` 端点，支持 Server-Sent Events (SSE) 流式响应
3. 修改底层模块（LLM Factory、SQL Generator、Result Explainer、Orchestrator）支持流式处理

---

## 一、现状分析

### 1.1 当前架构

| 组件 | 文件路径 | 框架/技术 |
|------|----------|-----------|
| CLI 入口 | `src/main.py` (run_cli 函数) | argparse |
| REST API | `src/main.py` (create_app 函数) | FastAPI |
| SQL 生成 | `src/generation/sql_generator.py` | LangChain |
| 结果解释 | `src/explanation/result_explainer.py` | LangChain |
| LLM 工厂 | `src/generation/llm_factory.py` | LangChain |
| 编排器 | `src/core/orchestrator.py` | 核心调度 |

### 1.2 当前调用流程

```
用户请求 (CLI/API)
    ↓
NL2SQLOrchestrator.ask()
    ↓
1. 语义映射 (SemanticMapper)
    ↓
2. Schema 准备 (SchemaManager)
    ↓
3. SQL 生成 (SQLGenerator) ← 使用 LLM.invoke()
    ↓
4. 安全验证 (SecurityValidator)
    ↓
5. SQL 执行 (QueryExecutor)
    ↓
6. 结果解释 (ResultExplainer) ← 使用 LLM.invoke()
    ↓
返回完整结果
```

### 1.3 流式处理目标流程

```
用户请求 (CLI/API)
    ↓
NL2SQLOrchestrator.ask_stream() [新增]
    ↓
1. 语义映射 → yield {"stage": "mapping", "data": ...}
    ↓
2. Schema 准备 → yield {"stage": "schema", "data": ...}
    ↓
3. SQL 生成 (流式) → yield {"stage": "sql", "chunk": "SELECT..."}
    ↓
4. 安全验证 → yield {"stage": "security", "data": ...}
    ↓
5. SQL 执行 → yield {"stage": "execution", "data": ...}
    ↓
6. 结果解释 (流式) → yield {"stage": "explanation", "chunk": "查询结果..."}
    ↓
完成 → yield {"stage": "done"}
```

---

## 二、需要修改的文件

### 2.1 文件修改清单

| 序号 | 文件路径 | 修改类型 | 描述 |
|------|----------|----------|------|
| 1 | `src/generation/llm_factory.py` | 修改 | 添加 stream 参数到 create_llm() |
| 2 | `src/generation/sql_generator.py` | 新增方法 | 添加 generate_stream() 方法 |
| 3 | `src/explanation/result_explainer.py` | 新增方法 | 添加 explain_stream() 方法 |
| 4 | `src/core/orchestrator.py` | 新增方法 | 添加 ask_stream() 方法 |
| 5 | `src/main.py` | 修改 | CLI 添加 --stream，API 添加 /query/stream |

---

## 三、详细任务分解

### 任务 1: 修改 LLM Factory 支持流式

**文件**: `src/generation/llm_factory.py`

**修改内容**:

```python
def create_llm(
    provider: Literal["minimax", "openai", "anthropic", "ollama", "custom"],
    model: str = None,
    api_key: str = None,
    base_url: str = None,
    temperature: float = 0,
    stream: bool = False,  # 新增参数
    **kwargs: Any
) -> Any:
    # MiniMax provider
    if provider == "minimax":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model or "MiniMax-M2.5",
            api_key=api_key,
            base_url=base_url or "https://api.minimaxi.com/anthropic",
            temperature=temperature if temperature > 0 else 1.0,
            streaming=stream,  # 新增
            **kwargs
        )
    
    # OpenAI provider
    elif provider == "openai":
        return ChatOpenAI(
            model=model or "gpt-4",
            api_key=api_key,
            temperature=temperature,
            streaming=stream,  # 新增
            **kwargs
        )
    
    # Anthropic provider
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model or "claude-3-opus-20240229",
            api_key=api_key,
            temperature=temperature,
            streaming=stream,  # 新增
            **kwargs
        )
    
    # Ollama provider
    elif provider == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=model or "llama2",
            temperature=temperature,
            **kwargs
        )
    
    # Custom provider
    elif provider == "custom":
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            streaming=stream,  # 新增
            **kwargs
        )
```

**注意事项**:
- `ChatOpenAI` 使用 `streaming=True` 参数
- `ChatAnthropic` 使用 `streaming=True` 参数
- 需要确认 LangChain 版本对流式的支持

---

### 任务 2: SQL Generator 添加流式方法

**文件**: `src/generation/sql_generator.py`

**新增方法**:

```python
from typing import Generator

class SQLGenerator:
    # ... 现有代码 ...
    
    def generate_stream(self, schema: str, question: str) -> Generator[str, None, None]:
        """流式生成 SQL
        
        Args:
            schema: 数据库 Schema 文档
            question: 用户问题
            
        Yields:
            SQL 片段（逐步返回）
        """
        try:
            chain = self.prompt_template | self.llm | self.output_parser
            
            # 使用 stream() 而非 invoke()
            for chunk in chain.stream({"schema": schema, "question": question}):
                yield chunk
                
        except Exception as e:
            logger.error(f"SQL 流式生成失败: {e}")
            yield f"[ERROR] {str(e)}"
```

**流式输出格式**:
- 每个 chunk 是一个字符串片段
- 最终需要组装成完整 SQL

---

### 任务 3: Result Explainer 添加流式方法

**文件**: `src/explanation/result_explainer.py`

**新增方法**:

```python
from typing import Generator, Any, Dict, List, Union

class ResultExplainer:
    # ... 现有代码 ...
    
    def explain_stream(
        self,
        question: str,
        result: Any,
        format: str = "text"
    ) -> Generator[str, None, None]:
        """流式解释查询结果
        
        Args:
            question: 用户问题
            result: 查询结果
            format: 输出格式 (text/summary/comparison)
            
        Yields:
            解释文本片段
        """
        parsed_result = self._parse_result(result)
        
        # 简单结果直接返回
        if self._is_simple_result(parsed_result):
            explanation = self._explain_simple(question, parsed_result)
            yield explanation
            return
        
        # 复杂结果使用 LLM 流式生成
        if self.llm is None:
            # 无 LLM 时使用 fallback
            fallback = self._fallback_explain(parsed_result)
            yield fallback
            return
        
        try:
            prompt = self._build_explain_prompt(question, parsed_result, format)
            
            # 流式调用 LLM
            for chunk in self.llm.stream(prompt):
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                yield content
                
        except Exception as e:
            logger.error(f"结果解释流式生成失败: {e}")
            yield self._fallback_explain(parsed_result)
```

---

### 任务 4: Orchestrator 添加流式处理方法

**文件**: `src/core/orchestrator.py`

**新增方法**:

```python
from typing import Generator, Dict, Any
import json

class NL2SQLOrchestrator:
    # ... 现有代码 ...
    
    def ask_stream(self, question: str) -> Generator[Dict[str, Any], None, None]:
        """流式处理问题
        
        Args:
            question: 用户问题
            
        Yields:
            包含不同阶段的流式数据块
        """
        start_time = time.time()
        
        # 阶段 1: 语义映射
        try:
            mapping = self._semantic_mapping(question)
            yield {
                "stage": "mapping",
                "status": "success",
                "data": {
                    "enhanced_question": mapping.enhanced_question,
                    "field_mappings": mapping.field_mappings,
                },
                "timestamp": time.time() - start_time
            }
        except Exception as e:
            yield {"stage": "mapping", "status": "error", "error": str(e)}
            return
        
        # 阶段 2: Schema 准备
        try:
            schema_doc = self._prepare_schema()
            yield {
                "stage": "schema",
                "status": "success",
                "data": {"schema": schema_doc[:500] + "..."},  # 截断显示
                "timestamp": time.time() - start_time
            }
        except Exception as e:
            yield {"stage": "schema", "status": "error", "error": str(e)}
            return
        
        # 阶段 3: SQL 生成 (流式)
        try:
            sql_chunks = []
            for chunk in self.sql_generator.generate_stream(schema_doc, mapping.enhanced_question):
                sql_chunks.append(chunk)
                yield {
                    "stage": "sql_generating",
                    "status": "streaming",
                    "chunk": chunk,
                    "timestamp": time.time() - start_time
                }
            
            sql = "".join(sql_chunks)
            sql = self.sql_generator._clean_sql(sql)  # 清理格式
            
            yield {
                "stage": "sql_generated",
                "status": "success",
                "data": {"sql": sql},
                "timestamp": time.time() - start_time
            }
        except Exception as e:
            yield {"stage": "sql_generating", "status": "error", "error": str(e)}
            return
        
        # 阶段 4: 安全验证
        try:
            security_result = self._validate_security(sql)
            yield {
                "stage": "security",
                "status": "success" if security_result.is_valid else "rejected",
                "data": {
                    "is_valid": security_result.is_valid,
                    "message": security_result.message,
                },
                "timestamp": time.time() - start_time
            }
            
            if not security_result.is_valid:
                yield {
                    "stage": "done",
                    "status": "security_rejected",
                    "error": security_result.message,
                    "timestamp": time.time() - start_time
                }
                return
        except Exception as e:
            yield {"stage": "security", "status": "error", "error": str(e)}
            return
        
        # 阶段 5: SQL 执行
        try:
            execution_result = self._execute_sql(sql)
            yield {
                "stage": "execution",
                "status": "success" if execution_result.success else "error",
                "data": {
                    "success": execution_result.success,
                    "result": execution_result.result,
                    "error": execution_result.error,
                },
                "timestamp": time.time() - start_time
            }
            
            if not execution_result.success:
                yield {
                    "stage": "done",
                    "status": "execution_error",
                    "error": execution_result.error,
                    "timestamp": time.time() - start_time
                }
                return
        except Exception as e:
            yield {"stage": "execution", "status": "error", "error": str(e)}
            return
        
        # 阶段 6: 结果解释 (流式)
        try:
            explanation_chunks = []
            for chunk in self.result_explainer.explain_stream(
                question, 
                execution_result.result
            ):
                explanation_chunks.append(chunk)
                yield {
                    "stage": "explaining",
                    "status": "streaming",
                    "chunk": chunk,
                    "timestamp": time.time() - start_time
                }
            
            explanation = "".join(explanation_chunks)
            
            yield {
                "stage": "explained",
                "status": "success",
                "data": {"explanation": explanation},
                "timestamp": time.time() - start_time
            }
        except Exception as e:
            yield {"stage": "explaining", "status": "error", "error": str(e)}
            # 继续完成，不中断
        
        # 完成
        yield {
            "stage": "done",
            "status": "success",
            "data": {
                "question": question,
                "sql": sql,
                "execution_result": execution_result.result,
                "explanation": explanation if 'explanation' in locals() else None,
            },
            "timestamp": time.time() - start_time
        }
```

---

### 任务 5: CLI 添加流式参数

**文件**: `src/main.py`

**修改 `main()` 函数**:

```python
# 在 query_parser 中添加 --stream 参数
query_parser.add_argument("question", type=str, help="自然语言问题")
query_parser.add_argument("--show-sql", action="store_true", help="显示生成的 SQL")
query_parser.add_argument("--stream", action="store_true", help="流式输出结果")  # 新增
query_parser.set_defaults(command="query")
```

**修改 `run_cli()` 函数**:

```python
def run_cli(args: argparse.Namespace, settings: Settings) -> None:
    """运行 CLI 模式"""
    orchestrator = create_orchestrator(settings)
    
    if args.command == "query":
        if orchestrator.llm is None:
            print("错误: LLM 不可用。请安装必要的依赖。")
            print("运行: pip install langchain-anthropic")
            sys.exit(1)
        
        # 判断是否使用流式输出
        if getattr(args, 'stream', False):
            # 流式输出模式
            print(f"\n问题: {args.question}")
            print("-" * 50)
            
            for chunk in orchestrator.ask_stream(args.question):
                stage = chunk.get("stage")
                status = chunk.get("status")
                
                if stage == "mapping" and status == "success":
                    print(f"[1/6] 语义映射: ✓")
                    
                elif stage == "schema" and status == "success":
                    print(f"[2/6] Schema 准备: ✓")
                    
                elif stage == "sql_generating" and status == "streaming":
                    print(f"[3/6] SQL 生成: {chunk.get('chunk')}", end="", flush=True)
                    
                elif stage == "sql_generated" and status == "success":
                    print(f"\n[3/6] SQL 生成完成: {chunk['data']['sql']}")
                    if args.show_sql:
                        print(f"SQL: {chunk['data']['sql']}")
                    
                elif stage == "security" and status == "success":
                    print(f"[4/6] 安全验证: ✓")
                    
                elif stage == "execution" and status == "success":
                    print(f"[5/6] SQL 执行: ✓")
                    if chunk['data'].get('result'):
                        print(f"结果: {chunk['data']['result']}")
                    
                elif stage == "explaining" and status == "streaming":
                    print(f"[6/6] 解释: {chunk.get('chunk')}", end="", flush=True)
                    
                elif stage == "explained" and status == "success":
                    print(f"\n[6/6] 解释完成")
                    
                elif stage == "done" and status == "success":
                    print("-" * 50)
                    print("完成!")
        else:
            # 现有同步模式
            result = orchestrator.ask(args.question)
            
            if result.status.value == "success":
                print(f"\n问题: {result.question}")
                if args.show_sql and result.sql:
                    print(f"\nSQL: {result.sql}")
                if result.execution and result.execution.result:
                    print(f"\n结果: {result.execution.result}")
                if result.explanation:
                    print(f"\n解释: {result.explanation}")
            else:
                print(f"错误: {result.status.value}")
                if result.error_message:
                    print(f"详情: {result.error_message}")
                sys.exit(1)
```

---

### 任务 6: REST API 添加流式端点

**文件**: `src/main.py`

**新增导入**:

```python
from fastapi.responses import StreamingResponse
import json
import asyncio
```

**新增请求模型**:

```python
class StreamQueryRequest(BaseModel):
    question: str
    include_sql: bool = False
```

**新增流式端点**:

```python
@app.post("/query/stream")
async def query_stream(
    request: StreamQueryRequest,
    http_request: Request
) -> StreamingResponse:
    """流式查询接口
    
    使用 Server-Sent Events (SSE) 进行流式输出
    
    返回格式:
    data: {"stage": "mapping", "status": "success", ...}
    data: {"stage": "sql_generating", "status": "streaming", "chunk": "..."}
    ...
    """
    async def event_generator():
        try:
            orchestrator = create_orchestrator(settings)
            
            for chunk in orchestrator.ask_stream(request.question):
                # 格式化输出
                data = {
                    "stage": chunk.get("stage"),
                    "status": chunk.get("status"),
                    "timestamp": chunk.get("timestamp"),
                }
                
                # 根据不同阶段添加数据
                if "data" in chunk:
                    data["data"] = chunk["data"]
                if "chunk" in chunk:
                    data["chunk"] = chunk["chunk"]
                if "error" in chunk:
                    data["error"] = chunk["error"]
                
                # SSE 格式: data: {json}\n\n
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                
                # 如果客户端断开，停止生成
                if await http_request.is_disconnected():
                    break
                    
        except Exception as e:
            logger.exception("流式查询失败")
            error_data = json.dumps({
                "stage": "error",
                "status": "error",
                "error": str(e)
            }, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        }
    )
```

---

## 四、API 端点设计

### 4.1 新增端点

| 方法 | 路径 | 描述 | 响应格式 |
|------|------|------|----------|
| POST | `/query/stream` | 流式执行查询 | text/event-stream (SSE) |

### 4.2 SSE 响应格式

```json
// 阶段: 语义映射
{"stage": "mapping", "status": "success", "data": {"enhanced_question": "..."}, "timestamp": 0.1}

// 阶段: Schema 准备  
{"stage": "schema", "status": "success", "data": {"schema": "..."}, "timestamp": 0.2}

// 阶段: SQL 生成中
{"stage": "sql_generating", "status": "streaming", "chunk": "SELECT ", "timestamp": 0.5}

// 阶段: SQL 生成完成
{"stage": "sql_generated", "status": "success", "data": {"sql": "SELECT * FROM..."}, "timestamp": 0.8}

// 阶段: 安全验证
{"stage": "security", "status": "success", "data": {"is_valid": true}, "timestamp": 0.9}

// 阶段: 执行
{"stage": "execution", "status": "success", "data": {"result": [...]}, "timestamp": 1.0}

// 阶段: 解释中
{"stage": "explaining", "status": "streaming", "chunk": "查询结果", "timestamp": 1.5}

// 阶段: 完成
{"stage": "done", "status": "success", "data": {...}, "timestamp": 2.0}
```

---

## 五、CLI 使用示例

### 5.1 同步模式（现有）

```bash
python -m src.main cli query "查询所有价格大于100的产品"
```

输出:
```
问题: 查询所有价格大于100的产品

SQL: SELECT * FROM products WHERE price > 100

结果: [(1, '产品A', 150), (2, '产品B', 200)]

解释: 查询返回了2个价格大于100的产品，分别是...
```

### 5.2 流式模式（新增）

```bash
python -m src.main cli query "查询所有价格大于100的产品" --stream
```

输出:
```
问题: 查询所有价格大于100的产品
--------------------------------------------------
[1/6] 语义映射: ✓
[2/6] Schema 准备: ✓
[3/6] SQL 生成: SELECT * FROM products WHERE price > 100
[3/6] SQL 生成完成: SELECT * FROM products WHERE price > 100
SQL: SELECT * FROM products WHERE price > 100
[4/6] 安全验证: ✓
[5/6] SQL 执行: ✓
结果: [(1, '产品A', 150), (2, '产品B', 200)]
[6/6] 解释: 查询返回了2个价格大于100的产品，分别是产品A和产品B
[6/6] 解释完成
--------------------------------------------------
完成!
```

---

## 六、API 调用示例

### 6.1 同步模式

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "查询所有产品", "include_sql": true}'
```

### 6.2 流式模式

```bash
curl -N -X POST http://localhost:8000/query/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "查询所有产品", "include_sql": true}'
```

输出:
```
data: {"stage": "mapping", "status": "success", ...}
data: {"stage": "schema", "status": "success", ...}
data: {"stage": "sql_generating", "status": "streaming", "chunk": "SELECT"}
data: {"stage": "sql_generating", "status": "streaming", "chunk": " *"}
...
data: {"stage": "done", "status": "success", ...}
```

---

## 七、测试计划

### 7.1 单元测试

| 测试项 | 测试内容 | 文件 |
|--------|----------|------|
| LLM Factory 流式参数 | 验证 stream 参数正确传递 | tests/test_llm_factory.py |
| SQL Generator 流式生成 | 验证流式输出正确 | tests/test_sql_generator.py |
| Result Explainer 流式解释 | 验证流式解释正确 | tests/test_result_explainer.py |
| Orchestrator 流式处理 | 验证各阶段正确 yield | tests/test_orchestrator.py |

### 7.2 集成测试

| 测试项 | 测试内容 | 文件 |
|--------|----------|------|
| CLI 流式输出 | 验证 --stream 参数工作 | tests/test_cli_stream.py |
| API 流式端点 | 验证 /query/stream 端点 | tests/test_api_stream.py |
| SSE 格式验证 | 验证响应格式正确 | tests/test_api_stream.py |

### 7.3 手动测试

1. CLI 同步模式
2. CLI 流式模式
3. API 同步端点
4. API 流式端点
5. 错误处理（LLM 不可用、SQL 执行失败等）

---

## 八、潜在问题与解决方案

### 8.1 LLM 不支持流式

**问题**: 部分 LLM 提供商或版本不支持流式 API

**解决方案**:
```python
# 在 create_llm 中检测
if stream:
    try:
        # 测试流式能力
        test_stream = llm.stream("test")
        next(test_stream)
    except Exception:
        logger.warning("LLM 不支持流式，回退到同步模式")
        stream = False
```

### 8.2 缓冲区问题

**问题**: Nginx/代理服务器可能缓冲 SSE 响应

**解决方案**:
```python
# 添加响应头
headers={
    "X-Accel-Buffering": "no",
    "Cache-Control": "no-cache",
}
```

### 8.3 客户端断开

**问题**: 客户端断开连接后，服务端应停止处理

**解决方案**:
```python
# FastAPI 中检查连接状态
if await http_request.is_disconnected():
    break
```

---

## 九、任务依赖关系

```
┌─────────────────┐
│  任务1: LLM Factory  │
│  (stream 参数)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  任务2: SQL Generator│
│  (generate_stream)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  任务3: Result Explainer │
│  (explain_stream)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  任务4: Orchestrator │
│  (ask_stream)       │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│ 任务5  │ │ 任务6 │
│  CLI  │ │  API  │
└───────┘ └───────┘
```

---

## 十、时间估算

| 任务 | 难度 | 预估时间 |
|------|------|----------|
| 任务1: LLM Factory | 低 | 30 分钟 |
| 任务2: SQL Generator | 低 | 1 小时 |
| 任务3: Result Explainer | 低 | 1 小时 |
| 任务4: Orchestrator | 中 | 2 小时 |
| 任务5: CLI | 低 | 1 小时 |
| 任务6: REST API | 中 | 2 小时 |
| 测试与调试 | 中 | 3 小时 |
| **总计** | - | **约 10.5 小时** |

---

## 十一、后续扩展

### 11.1 可选功能

1. **WebSocket 支持**: 除了 SSE，提供 WebSocket 流式接口
2. **进度百分比**: 估算各阶段进度百分比
3. **取消请求**: 支持客户端取消正在进行的请求
4. **多语言支持**: 流式输出支持多种语言

### 11.2 性能优化

1. **并发处理**: 某些阶段可以并行处理
2. **缓存优化**: 对 Schema 等不变内容缓存
3. **连接池**: LLM 连接池复用

---

## 附录: 修改文件清单

| 文件 | 操作 | 行数变化 |
|------|------|----------|
| `src/generation/llm_factory.py` | 修改 | +10 行 |
| `src/generation/sql_generator.py` | 新增方法 | +25 行 |
| `src/explanation/result_explainer.py` | 新增方法 | +40 行 |
| `src/core/orchestrator.py` | 新增方法 | +120 行 |
| `src/main.py` | 修改 | +80 行 |
| **总计** | - | **+275 行** |
