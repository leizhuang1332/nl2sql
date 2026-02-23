# 计划：Generate SQL 展示中间过程 - 大模型思考过程展示

## 需求概述

在执行 "Generate SQL" 时展示中间过程，包括大模型的思考过程（Thinking）。当前系统已经支持流式返回 SQL 片段，但缺少模型推理过程的展示。

---

## 当前架构分析

### 数据流

```
用户问题 → SemanticMapper → SchemaDocGenerator → SQLGenerator → SecurityValidator → QueryExecutor → ResultExplainer
              ↓                   ↓                    ↓              ↓                 ↓              ↓
           mapping            schema             sql_generating   security        execution      explaining
```

### 关键技术栈

| 组件 | 技术 |
|------|------|
| 前端 | Next.js + Ant Design |
| 后端 | FastAPI + LangChain |
| LLM | MiniMax (Anthropic 兼容), OpenAI, Anthropic, Ollama |
| 流式传输 | Server-Sent Events (SSE) |

### 关键发现

1. **MiniMax API 原生支持 Thinking**：在 `test_minimax.py` 中发现 MiniMax API 返回 `type="thinking"` 块，包含模型的推理过程
2. **当前只返回 SQL 片段**：`sql_generator.py` 中的 `generate_stream` 只 yield SQL 文本，未包含思考过程
3. **流式架构已完备**：后端 `ask_stream` 方法已实现分阶段流式返回

---

## 可行性方案

### 方案一：MiniMax 原生 Thinking 块（推荐）

**思路**：利用 MiniMax API 原生的 `thinking` 块，直接获取模型推理过程。

**原理**：

```
MiniMax API 响应格式:
{
  "content": [
    {"type": "thinking", "thinking": "推理过程..."},
    {"type": "text", "text": "SQL 查询..."}
  ]
}
```

**实现步骤**：

1. **修改 LLM 初始化** (`llm_factory.py`)
   - 确保启用 `streaming=True` 参数
   - 配置 `thinking` 块透传

2. **修改 SQL 生成器** (`sql_generator.py`)
   - 创建 `generate_with_thinking` 方法
   - 解析 LLM 响应中的 `thinking` 和 `text` 块
   - 分别 yield thinking 和 SQL 片段

3. **修改编排器** (`orchestrator.py`)
   - 在 `ask_stream` 中新增 `thinking` 阶段
   - 透传 thinking 数据到前端

4. **修改前端** (`page.tsx` + 新建 `ThinkingDisplay.tsx`)
   - 新增思考过程展示组件
   - 实时渲染 thinking 文本

**优点**：
- ✅ 官方支持，无需额外 prompt 设计
- ✅ 推理过程准确、完整
- ✅ 性能开销最小

**缺点**：
- ❌ 仅支持 MiniMax 模型
- ❌ 需要确认 LangChain 是否透传 thinking 块

**预估工作量**：2-3 小时

---

### 方案二：Prompt 工程要求 Thinking 输出

**思路**：在 Prompt 中要求模型先输出思考过程，再输出 SQL，通过输出格式解析。

**原理**：

```python
# 修改 prompt 模板
PROMPT = """
基于以下数据库 Schema，将用户问题转换为 SQL 查询。

Schema:
{schema}

用户问题: {question}

请按以下格式输出：
1. 思考过程：用中文详细说明你如何分析这个问题，选择哪些表和字段
2. 最终 SQL：只返回 SQL 语句

思考过程：
"""

# 输出解析
# 1. "思考过程：" 之前的内容 → thinking
# 2. "最终 SQL：" 或 "SQL：" 之后的内容 → SQL
```

**实现步骤**：

1. **修改 Prompt 模板** (`sql_generator.py`)
   - 添加 thinking 输出指令
   - 设计清晰的输出格式

2. **修改生成方法**
   - 使用正则或结构化解析提取 thinking
   - 分别 yield thinking 和 SQL

3. **修改编排器** (`orchestrator.py`)
   - 新增 thinking 阶段流式返回

4. **前端展示**
   - 同方案一

**优点**：
- ✅ 兼容所有 LLM 提供商（OpenAI, Anthropic, MiniMax, Ollama）
- ✅ 实现统一，不依赖特定 API

**缺点**：
- ❌ Prompt 指令可能影响 SQL 质量
- ❌ 解析逻辑可能不稳定
- ❌ 额外 token 开销

**预估工作量**：3-4 小时

---

### 方案三：结构化输出 + Tool Use

**思路**：使用 LangChain 的 Tool/Structured Output 功能，让模型先输出推理，再生成 SQL。

**原理**：

```python
# 定义输出结构
class SQLGenerationOutput(BaseModel):
    thinking: str = Field(description="推理过程")
    sql: str = Field(description="生成的 SQL")

# 使用结构化输出
chain = prompt | llm.with_structured_output(SQLGenerationOutput)
result = chain.invoke({"schema": ..., "question": ...})
# result.thinking → 推理过程
# result.sql → SQL
```

**实现步骤**：

1. **定义 Pydantic 模型** (`generation/types.py`)
   ```python
   class SQLGenerationOutput(BaseModel):
       thinking: str
       sql: str
   ```

2. **修改 SQL 生成器**
   - 使用 `llm.with_structured_output()` 
   - 先获取 thinking，再生成 SQL（两阶段）

3. **流式处理改造**
   - 阶段1：流式返回 thinking
   - 阶段2：流式返回 SQL

4. **前后端适配**
   - 同方案一

**优点**：
- ✅ 输出格式完全可控
- ✅ 类型安全，易于解析
- ✅ 适合复杂场景

**缺点**：
- ❌ 结构化输出不支持流式 thinking（需分两次调用）
- ❌ 复杂度较高
- ❌ token 开销最大

**预估工作量**：4-6 小时

---

## 方案对比

| 维度 | 方案一 (原生) | 方案二 (Prompt) | 方案三 (结构化) |
|------|---------------|-----------------|-----------------|
| 兼容性 | 仅 MiniMax | 全 providers | 全 providers |
| 准确性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 实现复杂度 | 低 | 中 | 高 |
| 性能开销 | 最小 | 中 | 最大 |
| 维护成本 | 低 | 中 | 高 |
| 推荐指数 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

---

## 推荐方案

**方案一（MiniMax 原生 Thinking）+ 方案二（Prompt 回退）**

实施策略：
1. 首先尝试方案一，测试 MiniMax thinking 块是否被 LangChain 正确透传
2. 如果方案一不可行（LangChain 过滤了 thinking 块），使用方案二作为回退
3. 方案三作为最终备选

---

## 待确认问题

1. [ ] LangChain 是否透传 MiniMax 的 thinking 块？（需测试）
2. [ ] 前端展示 thinking 的 UI 设计要求？
3. [ ] 是否需要支持 OpenAI 的 reasoning_effort 参数？
4. [ ] thinking 内容是否需要持久化存储？

---

## 下一步行动

1. 测试 LangChain 对 MiniMax thinking 块的支持
2. 设计前端 UI 原型
3. 确认最终方案
4. 实施开发
