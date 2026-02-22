# 前后端对接联调计划

## 一、当前状态分析

### 1.1 后端 API 现状

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/health` | GET | 健康检查 | ✅ 已实现 |
| `/tables` | GET | 获取所有表名 | ✅ 已实现 |
| `/schema/{table_name}` | GET | 获取表结构 | ✅ 已实现 |
| `/query` | POST | 执行查询 | ✅ 已实现 |
| `/query/stream` | POST | 流式查询 | ✅ 已实现 |

### 1.2 前端现状

| 组件 | 状态 | 问题 |
|------|------|------|
| `page.tsx` | ⚠️ Mock 数据 | 未调用 API |
| `SchemaExplorer.tsx` | ⚠️ Mock 数据 | 未调用 `/tables` |
| `QueryInput.tsx` | ⚠️ Mock 数据 | 未调用 `/query` |
| `SQLPreview.tsx` | ✅ 已实现 | 依赖父组件传递 |
| `ResultsTable.tsx` | ✅ 已实现 | 依赖父组件传递 |
| `api.ts` | ⚠️ 类型不匹配 | 需要修正 |

---

## 二、对接任务清单

### 2.1 任务 1: 修正 API 类型定义

**问题**: 前端 `api.ts` 的类型定义与后端响应不匹配

| 文件 | 问题 |
|------|------|
| `QueryResponse.results` | 后端返回 `result`，不是 `results` |
| `QueryResponse.sql` | 后端默认不返回，需设置 `include_sql: true` |
| `SchemaResponse` | 后端返回结构不同 |

**步骤**:
1. 修改 `frontend/src/lib/api.ts` 中的类型定义
2. 统一使用后端返回的字段名

---

### 2.2 任务 2: Schema Explorer 对接

**当前**: 使用 mock 数据
**目标**: 调用 `/tables` 和 `/schema/{table_name}`

**步骤**:
1. 在 `SchemaExplorer.tsx` 中添加 `useEffect` 加载数据
2. 调用 `nl2sqlApi.getTables()` 获取表列表
3. 遍历表名调用 `nl2sqlApi.getSchema(tableName)` 获取每个表的结构
4. 处理加载状态和错误状态
5. 考虑添加缓存机制避免重复请求

---

### 2.3 任务 3: 查询功能对接

**当前**: `page.tsx` 中 `handleQuerySubmit` 使用 mock
**目标**: 调用 `/query` API

**步骤**:
1. 修改 `page.tsx` 导入 `nl2sqlApi`
2. 在 `handleQuerySubmit` 中调用 `nl2sqlApi.query({ question })`
3. 处理响应:
   - 设置 `sql` 状态
   - 设置 `results` 状态
   - 添加错误处理
4. 配置 `include_sql: true` 获取 SQL 语句

---

### 2.4 任务 4: 流式响应支持 (可选)

**当前**: 使用同步请求
**目标**: 支持 `/query/stream` 实时显示进度

**步骤**:
1. 在 `api.ts` 添加流式请求方法
2. 修改 `QueryInput` 支持流式输出显示
3. 实现 SSE (Server-Sent Events) 消费逻辑
4. 分阶段显示处理进度 (语义映射 → SQL生成 → 执行 → 解释)

---

### 2.5 任务 5: 配置环境变量

**步骤**:
1. 创建 `frontend/.env.local` 文件
2. 配置 `NEXT_PUBLIC_API_URL=http://localhost:8000`
3. 验证前端能访问后端 API (CORS 已配置)

---

### 2.6 任务 6: 集成测试验证

**步骤**:
1. 启动后端: `python -m src.main api --port 8000`
2. 启动前端: `cd frontend && npm run dev`
3. 测试场景:
   - [ ] Schema Explorer 正确加载表结构
   - [ ] 输入自然语言查询，点击生成 SQL
   - [ ] SQL Preview 正确显示
   - [ ] Results Table 显示查询结果
   - [ ] 错误处理正常 (无效查询、网络错误)

---

## 三、文件修改清单

| 优先级 | 文件 | 修改内容 |
|--------|------|----------|
| P0 | `frontend/src/lib/api.ts` | 类型修正 + 添加流式方法 |
| P0 | `frontend/src/app/page.tsx` | 调用真实 API |
| P0 | `frontend/src/components/nl2sql/SchemaExplorer.tsx` | 加载真实 Schema |
| P1 | `frontend/.env.local` | 配置 API 地址 |
| P1 | `frontend/src/components/nl2sql/QueryInput.tsx` | 流式输出支持 |
| P2 | `frontend/src/components/nl2sql/SQLPreview.tsx` | 编辑后重新执行 |

---

## 四、验证标准

- [ ] `npm run lint` 通过
- [ ] `npm run build` 成功
- [ ] 浏览器中 Schema Explorer 显示真实表结构
- [ ] 输入查询后返回正确的 SQL 和结果
- [ ] 错误场景正常提示

---

## 五、技术细节

### 后端 API 响应格式

```json
// GET /tables
{ "tables": ["products", "orders", "users"] }

// GET /schema/products
{ "table": "products", "schema": "..." }

// POST /query
{
  "question": "查询所有产品",
  "result": [...],
  "sql": "SELECT * FROM products",
  "status": "success",
  "error": null
}
```

### 前端需要适配

1. **字段名映射**: `result` → `results`
2. **Schema 解析**: 后端返回字符串格式，前端需解析为对象树
3. **错误处理**: 后端可能返回非 200 状态码
