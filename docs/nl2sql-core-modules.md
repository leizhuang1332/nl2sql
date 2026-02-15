# NL2SQL 智能问数项目 - 6 大核心模块

基于 LangChain 1.0+ 开发的 NL2SQL（自然语言转 SQL）项目，核心需要实现以下 **6 个关键模块**：

---

## 1. Schema 理解与表示模块

**作用**：让 LLM "看懂" 数据库结构

```python
from langchain_community.utilities import SQLDatabase

db = SQLDatabase.from_uri("sqlite:///your_db.db")

# 核心：获取表结构 + 字段注释 + 采样数据
def get_core_schema(db):
    tables = db.get_usable_table_names()
    schema_docs = []
    for table in tables:
        ddl = db.get_table_info([table])  # 建表语句
        sample = db.run(f"SELECT * FROM {table} LIMIT 2")  # 采样数据帮助理解
        schema_docs.append(f"表 {table}:\n{ddl}\n示例数据:\n{sample}")
    return "\n\n".join(schema_docs)
```

**关键输出**：`表结构 + 字段类型 + 数据样例`

---

## 2. SQL 生成模块（Prompt + LLM）

**作用**：自然语言 → SQL

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

# 核心 Prompt：Schema + 问题 → SQL
prompt = ChatPromptTemplate.from_template("""
基于以下数据库 Schema，将用户问题转换为 SQL。

Schema:
{schema}

用户问题: {question}

只返回 SQL 代码，不要解释。
SQL:
""")

sql_chain = prompt | ChatOpenAI(temperature=0) | StrOutputParser()
```

**关键**：零样本（Zero-shot）或 Few-shot 示例提升准确率

---

## 3. 查询执行与错误修正模块

**作用**：执行 SQL，失败时自动修复

```python
def execute_with_fix(sql, db, max_retry=2):
    for i in range(max_retry):
        try:
            result = db.run(sql)
            return {"success": True, "result": result, "sql": sql}
        except Exception as e:
            if i == max_retry - 1:
                return {"success": False, "error": str(e)}
            # 错误反馈给 LLM 修正
            fix_prompt = f"SQL 执行错误: {e}\n请修正: {sql}"
            sql = llm.invoke(fix_prompt).content
```

**关键**：执行失败 → 捕获错误 → LLM 修正 → 重试

---

## 4. 语义映射模块（业务术语翻译）

**作用**：解决"销售额" ≠ `sales.amount` 的语义鸿沟

```python
# 核心：建立业务词 ↔ 技术字段的映射
SEMANTIC_MAP = {
    "销售额": ["sales.amount", "orders.total_price"],
    "最近一个月": "DATE('now', '-1 month')",
    "Top5": "ORDER BY xxx DESC LIMIT 5"
}

def translate_terms(question):
    # 简单替换或向量检索匹配
    enhanced = question
    for biz, tech in SEMANTIC_MAP.items():
        if biz in question:
            enhanced += f"\n[注意: {biz} 对应字段为 {tech}]"
    return enhanced
```

**关键**：没有这层，用户说"昨天的单量" LLM 不知道是哪张表的哪个字段

---

## 5. 安全验证模块

**作用**：防止 SQL 注入和误操作

```python
def validate_sql(sql, allowed_tables):
    # 核心检查点
    forbidden = ['DROP', 'DELETE', 'UPDATE', 'INSERT', '--']
    if any(kw in sql.upper() for kw in forbidden):
        return False, "包含危险操作"
    
    # 检查表名白名单
    used_tables = extract_tables(sql)  # 正则提取表名
    if not all(t in allowed_tables for t in used_tables):
        return False, "包含未授权表"
    
    return True, "通过"
```

**关键**：只读权限 + 关键字黑名单 + 表名白名单

---

## 6. 结果解释模块

**作用**：把 SQL 结果翻译成人话

```python
explain_prompt = """
查询结果: {result}
用户问题: {question}

用一句话回答用户的问题，并指出关键数字。
"""

explainer = ChatPromptTemplate.from_template(explain_prompt) | ChatOpenAI()
```

**关键**：用户问"销售额多少"，返回"本月销售额为 125 万，环比增长 15%" 而不是原始表格

---

## 最小可行架构（MVP）

```
用户提问 
    ↓
[语义映射] → 翻译业务术语
    ↓
[Schema + 问题] → 组装 Prompt
    ↓
[LLM] → 生成 SQL
    ↓
[安全验证] → 检查合法性
    ↓
[执行器] → 查数据库（失败则修正重试）
    ↓
[结果解释] → 生成自然语言答案
    ↓
返回给用户
```

---

## 总结

这 6 个模块构成了 NL2SQL 的完整闭环，缺一不可。其中 **语义映射** 和 **错误修正** 是生产环境中最影响准确率的关键模块。

- **语义映射**：解决业务术语与技术字段之间的语义鸿沟
- **错误修正**：通过 LLM 自动修复 SQL 执行错误，提升查询成功率
