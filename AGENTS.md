# Project Instructions

**技术架构参考**: [docs/technical-architecture.md](docs/technical-architecture.md) - LangChain 1.2.x 技术栈与 6 大核心模块设计


## MANDATORY: Agent Workflow

Every new agent session MUST follow this workflow:

### Step 1: Initialize Environment

```bash
./init.sh
```

This will:
- Install all dependencies
- Start the development server at http://localhost:3000

**DO NOT skip this step.** Ensure the server is running before proceeding.

### Step 2: Select Next feature

Read `feature_list.json` and select ONE feature to work on.

Selection criteria (in order of priority):
1. Choose a feature where `passes: false`
2. Consider dependencies - fundamental features should be done first
3. Pick the highest-priority incomplete feature

### Step 3: Implement the feature

- Read the feature description and steps carefully
- Implement the functionality to satisfy all steps
- Follow existing code patterns and conventions

### Step 4: Test Thoroughly

After implementation, verify ALL steps in the feature:

**强制测试要求（Testing Requirements - MANDATORY）：**

1. **大幅度页面修改**（新建页面、重写组件、修改核心交互）：
   - **必须在浏览器中测试！** 使用 MCP Playwright 工具
   - 验证页面能正确加载和渲染
   - 验证表单提交、按钮点击等交互功能
   - 截图确认 UI 正确显示

2. **小幅度代码修改**（修复 bug、调整样式、添加辅助函数）：
   - 可以使用单元测试或 lint/build 验证
   - 如有疑虑，仍建议浏览器测试

3. **所有修改必须通过**：
   - `npm run lint` 无错误
   - `npm run build` 构建成功
   - 浏览器/单元测试验证功能正常

**测试清单：**
- [ ] 代码没有 TypeScript 错误
- [ ] lint 通过
- [ ] build 成功
- [ ] 功能在浏览器中正常工作（对于 UI 相关修改）

### Step 5: Update Progress

Write your work to `progress.md`:

```
## [Date] - feature: [feature description]

### What was done:
- [specific changes made]

### Testing:
- [how it was tested]

### Notes:
- [any relevant notes for future agents]
```

### Step 6: Commit Changes (包含 feature_list.json 更新)

**IMPORTANT: 所有更改必须在同一个 commit 中提交，包括 feature_list.json 的更新！**

流程：
1. 更新 `feature_list.json`，将任务的 `passes` 从 `false` 改为 `true`
2. 更新 `progress.md` 记录工作内容
3. 一次性提交所有更改：

```bash
git add .
git commit -m "[feature description] - completed"
```

**规则:**
- 只有在所有步骤都验证通过后才标记 `passes: true`
- 永远不要删除或修改任务描述
- 永远不要从列表中移除任务
- **一个 feature 的所有内容（代码、progress.md、feature_list.json）必须在同一个 commit 中提交**

---

## ⚠️ 阻塞处理（Blocking Issues）

**如果任务无法完成测试或需要人工介入，必须遵循以下规则：**

### 需要停止任务并请求人工帮助的情况：

1. **缺少环境配置**：
   - .env.local 需要填写真实的 API 密钥
   - Supabase 项目需要创建和配置
   - 外部服务需要开通账号

2. **外部依赖不可用**：
   - 第三方 API 服务宕机
   - 需要人工授权的 OAuth 流程
   - 需要付费升级的服务

3. **测试无法进行**：
   - 登录/注册功能需要真实用户账号
   - 功能依赖外部系统尚未部署
   - 需要特定硬件环境

### 阻塞时的正确操作：

**DO NOT（禁止）：**
- ❌ 提交 git commit
- ❌ 将 feature_list.json 的 passes 设为 true
- ❌ 假装任务已完成

**DO（必须）：**
- ✅ 在 progress.md 中记录当前进度和阻塞原因
- ✅ 输出清晰的阻塞信息，说明需要人工做什么
- ✅ 停止任务，等待人工介入

### 阻塞信息格式：

```
🚫 任务阻塞 - 需要人工介入

**当前任务**: [任务名称]

**已完成的工作**:
- [已完成的代码/配置]

**阻塞原因**:
- [具体说明为什么无法继续]

**需要人工帮助**:
1. [具体的步骤 1]
2. [具体的步骤 2]
...

**解除阻塞后**:
- 运行 [命令] 继续任务
```

---

## Commands

```bash
# In project dir/
npm run dev      # Start dev server
npm run build    # Production build
npm run lint     # Run linter
```

## Coding Conventions

- TypeScript strict mode
- Functional components with hooks
- Tailwind CSS for styling
- Write tests for new features

---

## Key Rules

1. **One feature per session** - Focus on completing one feature well
2. **Test before marking complete** - All steps must pass
3. **Browser testing for UI changes** - Creating or significantly modifying a page must be tested in a browser
4. **Document in progress.md** - Help future agents understand your work
5. **One commit per feature** - All changes (code, progress.md, feature_list.json) must be committed in the same commit
6. **Never remove features** - Only flip `passes: false` to `true`
7. **Stop if blocked** - When blocked, do not submit. Output blocking information and stop.
