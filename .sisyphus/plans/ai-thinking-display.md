# 计划: 真实展示AI思考过程

## TL;DR

> **快速总结**: 实现MiniMax M2.5模型的原生thinking流式输出，在UI中默认展示思考过程和处理阶段，每条stream流数据实时渲染

> **交付物**:
> - 修复sql_generator.py中的buffer未初始化bug
> - 新增MiniMax原生thinking流式支持（不使用Prompt模板强制）
> - 修改ThinkingDisplay组件默认展示（在输入框下方）
> - 处理阶段进度默认展示并实时渲染

> **预计工作量**: 中等
> **并行执行**: 部分可以并行（后端和前端可以分开改）

---

## 背景

### 原始需求
用户希望真实展示AI思考过程：
1. 先测试MiniMax API调用，获取thinking标签规范（包括stream流式响应的模型思考）
2. UI思考组件改成输入框下面，默认展示不隐藏
3. 处理阶段默认展示，stream流结果实时渲染

### 现有代码分析

**后端**:
- `test_minimax.py`: 测试文件，注释说明了thinking区块格式 `{"type": "thinking", "thinking": "推理内容"}`
- `llm_factory.py`: 使用`ChatAnthropic`兼容MiniMax API
- `sql_generator.py`: 
  - 使用Prompt模板强制LLM输出`<thinking>`和`<sql>`标签
  - **BUG**: `generate_with_thinking_stream`方法第102行`buffer`变量未初始化
- `orchestrator.py`: 调用`sql_generator.generate_with_thinking_stream`处理流式数据

**前端**:
- `api.ts`: 定义了`StreamChunk`接口，已有`thinking`和`chunk`字段
- `ThinkingDisplay.tsx`: 思考展示组件，但默认隐藏（当`!thinking && !loading`时返回null）
- `page.tsx`: 
  - 已处理thinking流式接收
  - Thinking组件在QueryInput之前渲染（不在输入框下方）
  - 处理阶段进度通过`streamStage`和`streamProgress`展示

---

## 工作目标

### 核心目标
1. 实现MiniMax M2.5原生thinking流式输出（不依赖Prompt模板）
2. 前端UI默认展示思考组件
3. 处理阶段实时渲染

### 具体交付物

#### 后端改动
- [ ] 1. 修复`sql_generator.py`中的buffer未初始化bug
- [ ] 2. 新增使用MiniMax原生thinking输出的流式方法
- [ ] 3. 确保API正确传递thinking数据到前端

#### 前端改动
- [ ] 4. 修改ThinkingDisplay组件：始终显示（移除默认隐藏逻辑）
- [ ] 5. 调整组件顺序：Thinking组件在QueryInput下方
- [ ] 6. 处理阶段进度条默认展示，不隐藏
- [ ] 7. 确保每条stream流数据实时渲染

---

## 验证策略

### 测试决策
- **测试框架**: pytest
- **自动化测试**: 单元测试
- **Agent QA**: 是（必须浏览器测试UI）

### QA策略
- **后端**: pytest运行测试，curl测试API响应
- **前端**: Playwright浏览器测试，验证UI展示

---

## 执行策略

### 第一阶段：后端改动

#### 任务1: 修复buffer未初始化bug
- **文件**: `src/generation/sql_generator.py`
- **修改**: 第102行添加`buffer = ""`

#### 任务2: 新增MiniMax原生thinking支持
- **分析**: 
  - 从test_minimax.py可知，MiniMax M2.5支持原生thinking区块
  - 流式响应时，chunk.delta.type为"thinking_delta"
  - 需要修改LLM调用方式，使用流式并正确解析thinking区块

- **修改方案**:
  1. 修改`llm_factory.py`：确保流式配置正确
  2. 新增或修改`sql_generator.py`中的方法：
     - 方案A: 使用LangChain的流式回调
     - 方案B: 直接调用Anthropic客户端获取原生thinking

### 第二阶段：前端改动

#### 任务3: ThinkingDisplay默认展示
- **文件**: `frontend/src/components/nl2sql/ThinkingDisplay.tsx`
- **修改**: 移除`if (!thinking && !loading) return null`逻辑

#### 任务4: 调整组件顺序
- **文件**: `frontend/src/app/page.tsx`
- **修改**: 将ThinkingDisplay移到QueryInput下方

#### 任务5: 处理阶段默认展示
- **文件**: `frontend/src/components/nl2sql/QueryInput.tsx`
- **检查**: 进度条组件是否默认显示

---

## 待测试验证命令

```bash
# 后端测试
pytest tests/ -v

# API测试
curl -X POST http://localhost:8000/query/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "查询所有产品"}'

# 前端测试
cd frontend && npm run build
npm run dev  # 浏览器测试
```

---

## 风险与限制

1. **API兼容性**: MiniMax API可能存在版本差异，需要测试
2. **流式性能**: 原生thinking流可能影响响应速度
3. **UI布局**: 思考组件放在输入框下方可能影响整体布局

---

## 成功标准

- [ ] MiniMax API原生thinking能正确流式返回
- [ ] 前端能实时展示思考内容
- [ ] ThinkingDisplay组件默认可见
- [ ] 处理阶段进度条默认可见
- [ ] 所有stream流数据实时渲染
- [ ] 无TypeScript编译错误
- [ ] 后端pytest测试通过
