# NL2SQL Hybrid 前端项目创建计划

## TL;DR

> 基于 Hybrid 布局方案创建 NL2SQL 前端项目，使用 React + Next.js + TypeScript + Ant Design ProComponents + Tailwind CSS

> **交付物**: 完整的 Next.js 前端项目，包含 Hybrid 布局、Schema Explorer、Query Input、SQL Preview、Results Table
> 
> **预估工作量**: Medium
> **并行执行**: YES - 多组件可并行开发

---

## Context

### 原始需求
根据 `docs/nl2sql-ui-best-practices.md` 中的 4. Hybrid (混合) 布局方案创建前端项目：
- 技术栈: React + Next.js + TypeScript + Ant Design ProComponents + Tailwind CSS

### 设计系统
基于 ui-ux-pro-max 生成的设计系统：
- **风格**: Vibrant & Block-based (开发者工具风格)
- **配色**: 
  - Primary: #1E293B (深蓝灰)
  - Secondary: #334155
  - CTA: #22C55E (运行绿)
  - Background: #0F172A (深色背景)
  - Text: #F8FAFC
- **字体**: JetBrains Mono (标题) + IBM Plex Sans (正文)

### Hybrid 布局结构
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

## Work Objectives

### Core Objective
创建完整的 NL2SQL 前端项目，实现 Hybrid 布局方案

### Concrete Deliverables
- [ ] Next.js 项目初始化 (frontend 目录)
- [ ] Tailwind CSS 配置
- [ ] shadcn/ui 组件库
- [ ] Schema Explorer 组件 (左侧数据库结构树)
- [ ] QueryInput 组件 (自然语言输入)
- [ ] SQLPreview 组件 (SQL 预览 + 编辑/运行/复制)
- [ ] ResultsTable 组件 (结果表格展示)
- [ ] HybridLayout 主布局 (可调整面板)
- [ ] 主页面集成

### Definition of Done
- [ ] `npm run build` 成功
- [ ] `npm run lint` 无错误
- [ ] 页面在浏览器中正常渲染

### Must Have
- 响应式布局
- 深色主题 (基于设计系统)
- 组件间状态协调

### Must NOT Have
- 避免使用 emoji 作为图标
- 避免布局抖动

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (Next.js + shadcn/ui)
- **Automated tests**: None (UI 项目)
- **Framework**: Manual browser testing

### QA Policy
- 使用 Playwright 进行 UI 验证
- 验证页面加载、组件渲染、交互功能

---

## Execution Strategy

### 并行开发 Waves

**Wave 1 (基础架构):**
- [ ] 1. 配置 Ant Design ProComponents 主题
- [ ] 2. 创建全局样式和布局组件

**Wave 2 (核心组件):**
- [ ] 3. SchemaExplorer 组件
- [ ] 4. QueryInput 组件  
- [ ] 5. SQLPreview 组件
- [ ] 6. ResultsTable 组件

**Wave 3 (集成):**
- [ ] 7. HybridLayout 可调整布局
- [ ] 8. 主页面组装
- [ ] 9. API 集成 (连接后端)

**Wave 4 (验证):**
- [ ] 10. 构建验证
- [ ] 11. UI 测试

---

## TODOs

- [ ] 1. 配置 Ant Design ProComponents 主题
   
   **What to do**:
   - 在 `src/app/globals.css` 添加设计系统配色
   - 创建 `src/components/Providers.tsx` 配置 Ant Design ConfigProvider
   - 设置深色主题变量
   
   **References**:
   - `frontend/src/app/globals.css` - 全局样式
   - `https://ant.design/components/config-provider` - Ant Design 主题配置
   
   **Acceptance Criteria**:
   - [ ] ConfigProvider 正确配置深色主题
   - [ ] 全局样式使用设计系统配色

- [ ] 2. 创建全局样式和布局组件
   
   **What to do**:
   - 更新 Tailwind 配置添加自定义颜色
   - 创建基础布局组件 `src/components/nl2sql/MainLayout.tsx`
   - 实现 Header 组件 (数据库选择器 + 历史记录)
   
   **References**:
   - `docs/nl2sql-ui-best-practices.md` - 布局方案
   - `frontend/src/app/globals.css` - 样式配置
   
   **Acceptance Criteria**:
   - [ ] Header 显示数据库选择器
   - [ ] Header 显示历史记录下拉菜单

- [ ] 3. SchemaExplorer 组件
   
   **What to do**:
   - 创建 `src/components/nl2sql/SchemaExplorer.tsx`
   - 使用 Ant Design Tree 组件展示数据库表结构
   - 添加搜索过滤功能
   - 展示列名、类型、主键信息
   
   **References**:
   - `https://ant.design/components/tree` - Tree 组件文档
   
   **Acceptance Criteria**:
   - [ ] 树形展示所有表和列
   - [ ] 搜索框可过滤表/列
   - [ ] 显示列类型和主键标识

- [ ] 4. QueryInput 组件
   
   **What to do**:
   - 创建 `src/components/nl2sql/QueryInput.tsx`
   - 使用 Ant Design Input.TextArea 组件
   - 添加发送按钮
   - 支持流式输出显示
   
   **References**:
   - `https://ant.design/components/input` - Input 组件
   
   **Acceptance Criteria**:
   - [ ] 多行文本输入框
   - [ ] 发送按钮调用 API
   - [ ] 显示加载状态

- [ ] 5. SQLPreview 组件
   
   **What to do**:
   - 创建 `src/components/nl2sql/SQLPreview.tsx`
   - 使用 Ant Design Card 组件展示 SQL
   - 添加 "Edit in Editor"、"Run"、"Copy" 按钮
   - 使用 JetBrains Mono 字体
   
   **References**:
   - `https://ant.design/components/card` - Card 组件
   
   **Acceptance Criteria**:
   - [ ] SQL 代码高亮显示
   - [ ] 三个功能按钮可用
   - [ ] 复制功能正常

- [ ] 6. ResultsTable 组件
   
   **What to do**:
   - 创建 `src/components/nl2sql/ResultsTable.tsx`
   - 使用 Ant Design Table 组件
   - 支持分页
   - 空状态提示
   
   **References**:
   - `https://ant.design/components/table` - Table 组件
   
   **Acceptance Criteria**:
   - [ ] 表格正确展示查询结果
   - [ ] 支持分页
   - [ ] 空数据显示友好提示

- [ ] 7. HybridLayout 可调整布局
   
   **What to do**:
   - 创建 `src/components/nl2sql/HybridLayout.tsx`
   - 使用 shadcn/ui ResizablePanel 实现左右可调
   - 或使用 react-resizable 实现面板调整
   
   **References**:
   - `https://ui.shadcn.com/docs/components/resizable` - Resizable
   - `docs/nl2sql-ui-best-practices.md` - 布局方案
   
   **Acceptance Criteria**:
   - [ ] 左右面板可通过拖拽调整宽度
   - [ ] 最小宽度限制

- [ ] 8. 主页面组装
   
   **What to do**:
   - 更新 `src/app/page.tsx`
   - 组合所有组件
   - 添加状态管理 (query, sql, results)
   
   **Acceptance Criteria**:
   - [ ] 页面完整渲染 Hybrid 布局
   - [ ] 组件间状态正确传递

- [ ] 9. API 集成
   
   **What to do**:
   - 创建 API 客户端 `src/lib/api.ts`
   - 实现 `/query`, `/tables`, `/schema` 接口调用
   - 添加错误处理
   
   **References**:
   - `src/main.py` - 后端 API 定义
   
   **Acceptance Criteria**:
   - [ ] 成功调用后端 API
   - [ ] 错误状态正确处理

- [ ] 10. 构建验证
   
   **Acceptance Criteria**:
   - [ ] `npm run build` 成功
   - [ ] `npm run lint` 无错误

- [ ] 11. UI 测试
   
   **Acceptance Criteria**:
   - [ ] 页面在浏览器中正常加载
   - [ ] 各组件正常显示
   - [ ] 交互功能正常工作

---

## Final Verification Wave

- [ ] F1. **构建验证** - 运行 `npm run build` 和 `npm run lint`
- [ ] F2. **UI 验证** - 使用 Playwright 验证页面渲染

---

## Success Criteria

### 验证命令
```bash
cd frontend && npm run build  # 预期: 构建成功
cd frontend && npm run lint   # 预期: 无错误
```

---

## 技术栈清单

| 组件 | 库 |
|------|-----|
| 框架 | Next.js 14 (App Router) |
| 语言 | TypeScript |
| UI 库 | Ant Design 5.x + ProComponents |
| 样式 | Tailwind CSS |
| 布局 | shadcn/ui ResizablePanel |
| 图标 | @ant-design/icons |
