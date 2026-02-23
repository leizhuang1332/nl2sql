# 计划：Generate SQL 展示中间过程 - 大模型思考过程展示

## 需求概述

在执行 "Generate SQL" 时展示中间过程，包括大模型的思考过程（Thinking）。当前系统已经支持流式返回 SQL 片段，但缺少模型推理过程的展示。

---

## 已选择方案：方案二（Prompt 工程要求 Thinking 输出）

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
2. 最终 SQL：只返回 SQL 语句，不要解释

思考过程：
"""

# 输出解析
# 1. "思考过程：" 之前的内容 → thinking
# 2. "最终 SQL：" 或 "SQL：" 之后的内容 → SQL
```

**选择理由**：
- ✅ 兼容所有 LLM 提供商（OpenAI, Anthropic, MiniMax, Ollama）
- ✅ 实现统一，不依赖特定 API
- ✅ 无需修改 LangChain 底层

---

## 详细实施计划

### 一、后端改动

#### 1.1 修改 SQL 生成器 (`src/generation/sql_generator.py`)

**任务 1：更新 Prompt 模板**

```python
def _get_default_template(self) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_template("""
基于以下数据库 Schema，将用户问题转换为 SQL 查询。

Schema:
{schema}

用户问题: {question}

请按以下格式输出：
1. 思考过程：用中文详细说明你如何分析这个问题，选择哪些表和字段，使用了哪些条件
2. 最终 SQL：只返回 SQL 语句，不要解释

思考过程：
""")
```

**任务 2：新增 `generate_with_thinking_stream` 方法**

```python
def generate_with_thinking_stream(self, schema: str, question: str) -> Generator[Dict[str, str], None, None]:
    """流式生成 SQL，包含思考过程
    
    Yields:
        {"type": "thinking", "content": "推理片段..."}
        {"type": "sql", "content": "SQL 片段..."}
        {"type": "done", "thinking": "完整思考", "sql": "完整SQL"}
    """
    # 收集完整内容
    thinking_buffer = ""
    sql_buffer = ""
    current_phase = "thinking"  # thinking -> sql
    
    for chunk in self._stream_raw(schema, question):
        # 解析 chunk，判断是 thinking 还是 sql
        # 使用正则或状态机解析
        if current_phase == "thinking":
            # 检测是否进入 SQL 阶段
            if contains_sql_start(chunk):
                current_phase = "sql"
                # yield 剩余 thinking
                yield {"type": "thinking", "content": thinking_buffer}
            else:
                thinking_buffer += chunk
                yield {"type": "thinking", "content": chunk}
        else:
            sql_buffer += chunk
            yield {"type": "sql", "content": chunk}
    
    # 完成时返回完整内容
    yield {
        "type": "done",
        "thinking": thinking_buffer,
        "sql": self._clean_sql(sql_buffer)
    }
```

**任务 3：实现解析逻辑**

```python
import re

def _parse_thinking_output(self, full_output: str) -> Dict[str, str]:
    """解析完整输出，分离 thinking 和 SQL"""
    
    # 尝试多种分隔符
    patterns = [
        r'最终\s*SQL[：:]\s*',
        r'SQL[：:]\s*',
        r'```sql\s*',
        r'\n\s*SQL\s*:\s*\n',
    ]
    
    thinking = ""
    sql = ""
    
    for pattern in patterns:
        match = re.search(pattern, full_output, re.IGNORECASE)
        if match:
            thinking = full_output[:match.start()]
            sql = full_output[match.end():]
            break
    
    # 清理
    thinking = thinking.replace("思考过程：", "").replace("思考过程:", "").strip()
    sql = self._clean_sql(sql)
    
    return {"thinking": thinking, "sql": sql}
```

#### 1.2 修改编排器 (`src/core/orchestrator.py`)

**任务 4：在 `ask_stream` 中新增 thinking 阶段**

在现有的流式处理中，在 `sql_generating` 之前新增 `thinking` 阶段：

```python
def ask_stream(self, question: str) -> Generator[Dict[str, Any], None, None]:
    # ... existing mapping and schema stages ...
    
    try:
        # Thinking 阶段
        for item in self.sql_generator.generate_with_thinking_stream(
            schema_doc, mapping.enhanced_question
        ):
            if item["type"] == "thinking":
                yield {
                    "stage": "thinking",
                    "status": "streaming",
                    "chunk": item["content"],
                    "timestamp": time.time() - start_time
                }
            elif item["type"] == "sql":
                yield {
                    "stage": "sql_generating",
                    "status": "streaming",
                    "chunk": item["content"],
                    "timestamp": time.time() - start_time
                }
            elif item["type"] == "done":
                thinking = item.get("thinking", "")
                sql = item.get("sql", "")
                
                yield {
                    "stage": "thinking_done",
                    "status": "success",
                    "data": {"thinking": thinking},
                    "timestamp": time.time() - start_time
                }
                
                yield {
                    "stage": "sql_generated",
                    "status": "success",
                    "data": {"sql": sql},
                    "timestamp": time.time() - start_time
                }
    except Exception as e:
        yield {"stage": "thinking", "status": "error", "error": str(e)}
        return
```

#### 1.3 修改 API 响应 (`src/main.py`)

**任务 5：确保 thinking 数据透传到前端**

在 `query_stream` 函数中，确保透传新增的 thinking 字段：

```python
@app.post("/query/stream")
async def query_stream(request: StreamQueryRequest, http_request: Request) -> StreamingResponse:
    async def event_generator():
        for chunk in orchestrator.ask_stream(request.question):
            data = {
                "stage": chunk.get("stage"),
                "status": chunk.get("status"),
                "timestamp": chunk.get("timestamp"),
            }
            
            # 透传所有数据
            if "data" in chunk:
                data["data"] = chunk["data"]
            if "chunk" in chunk:
                data["chunk"] = chunk["chunk"]
            if "error" in chunk:
                data["error"] = chunk["error"]
            
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
```

---

### 二、前端改动

#### 2.1 更新 API 类型定义 (`frontend/src/lib/api.ts`)

**任务 6：新增 Thinking 数据类型**

```typescript
export interface StreamChunk {
  stage?: string;
  status?: string;
  sql?: string;
  result?: unknown;
  error?: string;
  explanation?: string;
  thinking?: string;  // 新增
  data?: Record<string, unknown>;
}
```

#### 2.2 新增 ThinkingDisplay 组件 (`frontend/src/components/nl2sql/ThinkingDisplay.tsx`)

**任务 7：创建 Thinking 展示组件**

```typescript
// frontend/src/components/nl2sql/ThinkingDisplay.tsx
'use client';

import React, { useRef, useEffect } from 'react';
import { Card, Spin } from 'antd';
import { BulbOutlined, LoadingOutlined } from '@ant-design/icons';

interface ThinkingDisplayProps {
  thinking: string;
  loading?: boolean;
}

export const ThinkingDisplay: React.FC<ThinkingDisplayProps> = ({
  thinking,
  loading = false
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [thinking]);

  if (!thinking && !loading) {
    return null;
  }

  return (
    <Card
      className="bg-slate-800 border-slate-700 mb-4"
      title={
        <div className="flex items-center gap-2 text-slate-200">
          {loading ? (
            <LoadingOutlined className="text-yellow-400" />
          ) : (
            <BulbOutlined className="text-yellow-400" />
          )}
          <span className="font-medium">AI 思考过程</span>
        </div>
      }
      bodyStyle={{ padding: 0 }}
    >
      <div
        ref={containerRef}
        className="h-40 overflow-auto p-4 bg-slate-900 rounded-b-lg"
      >
        {thinking ? (
          <pre className="text-sm text-yellow-200 whitespace-pre-wrap font-mono leading-relaxed">
            {thinking}
          </pre>
        ) : (
          <div className="flex items-center justify-center h-full text-slate-500">
            <Spin indicator={<LoadingOutlined spin />} tip="思考中..." />
          </div>
        )}
      </div>
    </Card>
  );
};

export default ThinkingDisplay;
```

#### 2.3 修改主页面 (`frontend/src/app/page.tsx`)

**任务 8：集成 Thinking 展示**

```typescript
// 在 Home 组件中添加 state
const [thinking, setThinking] = useState('');

// 在 handleQuerySubmit 中处理 thinking 数据
const handleQuerySubmit = async (question: string) => {
  // ... existing setup ...
  
  await nl2sqlApi.queryStream(
    { question, include_sql: true },
    (chunk: StreamChunk) => {
      const data = chunk.data as Record<string, unknown> | undefined;
      
      // 处理 thinking 阶段
      if (chunk.stage === 'thinking' && chunk.status === 'streaming') {
        const thinkingChunk = chunk.chunk as string;
        setThinking(prev => prev + thinkingChunk);
      }
      
      // thinking 完成时
      if (chunk.stage === 'thinking_done' && data?.thinking) {
        setThinking(data.thinking as string);
      }
      
      // ... existing handlers ...
    },
    // ... callbacks ...
  );
};

// 在右侧面板中渲染 ThinkingDisplay
const rightPanel = (
  <div className="h-full flex flex-col p-4 gap-4 overflow-auto">
    <ThinkingDisplay 
      thinking={thinking} 
      loading={loading && !thinking} 
    />
    
    <QueryInput 
      onSubmit={handleQuerySubmit} 
      loading={loading}
      disabled={loading}
      streaming={streaming}
      streamStage={streamStage}
      streamProgress={streamProgress}
    />
    
    <SQLPreview 
      sql={sql}
      onRun={handleRunQuery}
      loading={loading}
    />
    
    <div className="flex-1">
      <ResultsTable 
        data={results}
        loading={loading}
      />
    </div>
  </div>
);
```

#### 2.4 优化展示效果（可选）

**任务 9：添加 Markdown 渲染支持**

如果 thinking 内容包含 Markdown 格式，添加渲染支持：

```bash
npm install react-markdown @types/react-markdown
```

```typescript
import ReactMarkdown from 'react-markdown';

<div className="text-sm text-yellow-200 whitespace-pre-wrap font-mono leading-relaxed">
  <ReactMarkdown>{thinking}</ReactMarkdown>
</div>
```

**任务 10：添加 Thinking 折叠功能**

```typescript
const [thinkingExpanded, setThinkingExpanded] = useState(true);

<Card
  className="bg-slate-800 border-slate-700 mb-4"
  extra={
    <Button 
      type="link" 
      onClick={() => setThinkingExpanded(!thinkingExpanded)}
      className="text-slate-400"
    >
      {thinkingExpanded ? '收起' : '展开'}
    </Button>
  }
>
  {thinkingExpanded && (
    <div className="h-40 overflow-auto ...">
      ...
    </div>
  )}
</Card>
```

---

## 实施步骤（任务清单）

### Wave 1: 后端核心

| 任务 | 描述 | 文件 | 预估时间 |
|------|------|------|----------|
| T1 | 更新 SQL Generator Prompt 模板 | `src/generation/sql_generator.py` | 0.5h |
| T2 | 实现 generate_with_thinking_stream 方法 | `src/generation/sql_generator.py` | 1.5h |
| T3 | 修改 Orchestrator ask_stream 新增 thinking 阶段 | `src/core/orchestrator.py` | 1h |
| T4 | 测试后端流式 API | - | 0.5h |

### Wave 2: 前端展示

| 任务 | 描述 | 文件 | 预估时间 |
| T5 | 更新 API 类型定义 | `frontend/src/lib/api.ts` | 0.25h |
| T6 | 创建 ThinkingDisplay 组件 | `frontend/src/components/nl2sql/ThinkingDisplay.tsx` | 1h |
| T7 | 集成到主页面 | `frontend/src/app/page.tsx` | 0.5h |
| T8 | 浏览器测试 | - | 0.5h |

### Wave 3: 优化（可选）

| 任务 | 描述 | 文件 | 预估时间 |
| T9 | 添加 Markdown 渲染 | `frontend/src/components/nl2sql/ThinkingDisplay.tsx` | 0.5h |
| T10 | 添加折叠功能 | `frontend/src/components/nl2sql/ThinkingDisplay.tsx` | 0.25h |

---

## UI 设计草图

```
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 💡 AI 思考过程                                       │  │
│  ├─────────────────────────────────────────────────────┤  │
│  │ 分析用户问题：查询所有价格大于100的产品               │  │
│  │                                                     │  │
│  │ 1. 确定查询目标：products 表中的产品信息            │  │
│  │ 2. 筛选条件：price > 100                           │  │
│  │ 3. 需要字段：name, price, category                  │  │
│  │                                                     │  │
│  │ 推理完成，开始生成 SQL...                           │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ [语义映射] [Schema准备] [SQL生成✓] [安全验证] ...  │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ SELECT name, price, category FROM products           │  │
│  │ WHERE price > 100;                                   │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 结果表格                                             │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 测试场景

### TDD 测试用例

1. **Thinking 流式输出**
   - 输入：`"查询所有价格大于100的产品"`
   - 期望：thinking 逐步输出，每个字符/片段实时显示

2. **Thinking 内容正确性**
   - 验证 thinking 包含对问题的分析
   - 验证 thinking 说明使用了哪些表和字段

3. **SQL 正确生成**
   - 验证 thinking 完成后，SQL 正确生成
   - 验证 SQL 语法正确

4. **多 LLM 提供商兼容性**
   - 测试 OpenAI
   - 测试 Anthropic
   - 测试 Ollama
   - 测试 MiniMax

5. **错误处理**
   - LLM 返回格式异常时的降级处理
   - 网络错误时的用户体验

---

## 风险与缓解

| 风险 | 级别 | 缓解措施 |
|------|------|----------|
| Prompt 影响 SQL 质量 | 中 | A/B 测试对比，灵活调整指令 |
| 解析逻辑不稳定 | 中 | 多正则回退，容错处理 |
| token 开销增加 | 低 | 可选功能，可关闭 |

---

## 成功标准

- [ ] 后端 API 正确返回 thinking 数据
- [ ] 前端实时展示 thinking 过程
- [ ] thinking 和 SQL 正确关联
- [ ] 兼容所有 LLM 提供商
- [ ] 浏览器测试通过
- [ ] lint 和 build 通过
