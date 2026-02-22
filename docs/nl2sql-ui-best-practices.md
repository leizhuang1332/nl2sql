# NL2SQL 前端 UI 最佳实践 - 布局模式研究

基于对 GitHub 多个开源项目的研究，以下是 nl2sql 应用最常见的三种 UI 布局模式：

---

## 1. Split-Pane (分栏) 布局 — 最常用

**适用场景**: 专业 SQL 编辑器，用户需要编写和优化查询

**典型项目**:
- `latticexyz/mud` - Explorer 使用 SQLEditor + TablesViewer + 结果分栏
- `lightdash/lightdash` - SQL Runner 功能
- `edp963/davinci` - EditorContainer with SourceTable, SqlEditor, SqlPreview

**布局结构**:
```
┌────────────────┬────────────────────┬──────────────────┐
│  Schema Panel  │   SQL Editor       │  Results Panel   │
│   (25% min)   │     (flex)         │    (30% min)    │
│                │                    │                  │
│ - Table list  │ - Monaco/Code     │ - Data table    │
│ - Column types│ - Syntax highlight│ - Pagination    │
│ - Search      │ - Auto-complete   │ - Export        │
└────────────────┴────────────────────┴──────────────────┘
```

**关键技术栈**:
- `shadcn/ui` ResizablePanel
- `@monaco-editor/react` - SQL 编辑
- `@tanstack/react-table` / `ag-grid` - 结果表格

---

## 2. Chat-Based (聊天) 布局 — AI 原生交互

**适用场景**: 自然语言对话界面，面向非技术用户

**典型项目**:
- `Chat2DB` - 文本转 SQL 功能
- `linuxfoundation/insights` - Text-to-SQL agent
- `sourcebot-dev/sourcebot` - Chat thread

**布局结构**:
```
┌─────────────────────────────────────────────────────────┐
│  [对话历史 - 可滚动]                                     │
│                                                          │
│  User: "显示上周所有订单"                               │
│                                                          │
│  AI: "生成的 SQL:"                                     │
│  ┌─────────────────────────────────────────────────┐  │
│  │ SELECT * FROM orders                             │  │
│  │ WHERE created_at >= DATE_SUB(NOW(), INTERVAL    │  │
│  │ 7 DAY);                                          │  │
│  └─────────────────────────────────────────────────┘  │
│  [复制] [运行] [编辑]                                  │
│                                                          │
│  ┌─────────────────────────────────────────────────┐  │
│  │ Results Table (可展开)                           │  │
│  └─────────────────────────────────────────────────┘  │
│                                                          │
│  [输入: 提问...]                              [发送]   │
└─────────────────────────────────────────────────────────┘
```

**关键特性**:
- 消息对 (用户问题 → AI SQL 回复)
- 流式响应 + thinking 指示器
- 内联工具执行结果

---

## 3. Form Wizard (表单向导) 布局 — 引导式查询

**适用场景**: 面向非技术用户的分步查询构建

**典型流程**:
1. 选择数据库/表
2. 选择列
3. 添加过滤条件
4. 预览生成的 SQL
5. 执行

**关键组件**:
- Stepper/进度指示器
- 实时更新的 SQL 预览
- 每个查询组件的表单字段

---

## 4. Hybrid (混合) 布局 — 推荐方案

结合以上三种模式的优点：

```
┌────────────────────────────────────────────────────────────────┐
│  Header: Database Selector │ Query History Dropdown           │
├──────────────┬────────────────────────────────────────────────┤
│              │                                                │
│  Schema      │  [Natural Language Input]                      │
│  Explorer    │  "显示各区域销售总额"                         │
│              │                           [Generate SQL]       │
│  - Tables    │                                                │
│  - Columns   │  ┌────────────────────────────────────────┐  │
│  - Types     │  │ SELECT region, SUM(amount)               │  │
│              │  │ FROM sales                              │  │
│              │  │ GROUP BY region                         │  │
│              │  └────────────────────────────────────────┘  │
│              │  [Edit in Editor] [Run] [Copy]                │
│              │                                                │
│              │  ┌────────────────────────────────────────┐  │
│              │  │ Results Table                           │  │
│              │  │ ...                                     │  │
│              │  └────────────────────────────────────────┘  │
└──────────────┴────────────────────────────────────────────────┘
```

---

## 技术选型建议

| 模式 | 推荐库 |
|------|--------|
| 可调整面板 | `shadcn/ui` ResizablePanel, `react-resizable` |
| SQL 编辑器 | `@monaco-editor/react` |
| 结果表格 | `@tanstack/react-table`, `ag-grid-react` |
| Schema 树 | 自定义树组件, `react-json-view` |
| 聊天界面 | 流式响应组件, message-pair 组件 |

---

## 总结建议

对于新的 NL2SQL 项目：

1. **桌面专业用户** → 采用 Split-Pane 布局 (可调整的查询/结果视图)
2. **普通用户** → 采用 Chat-Based 布局 (对话式 AI 交互)
3. **最佳实践** → 采用 Hybrid 方案，结合：
   - 左侧 Schema 浏览器
   - 自然语言输入
   - SQL 预览
   - 结果表格展示
4. 使用 **可调整面板** (shadcn/ui pattern) 增加灵活性

---

## 参考项目

- [latticexyz/mud](https://github.com/latticexyz/mud)
- [lightdash/lightdash](https://github.com/lightdash/lightdash)
- [edp963/davinci](https://github.com/edp963/davinci)
- [Chat2DB/Chat2DB](https://github.com/Chat2DB/Chat2DB)
- [linuxfoundation/insights](https://github.com/linuxfoundation/insights)
- [sourcebot-dev/sourcebot](https://github.com/sourcebot-dev/sourcebot)
- [shadcn-ui/ui](https://github.com/shadcn-ui/ui)
