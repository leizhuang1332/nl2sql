BASIC_TEMPLATE = """基于以下数据库 Schema，将用户问题转换为 SQL 查询。

Schema:
{schema}

用户问题: {question}

只返回 SQL 代码，不要解释。"""

DETAILED_TEMPLATE = """你是一个 SQL 专家。请根据给定的数据库 Schema，将用户问题转换为 SQL 查询。

## 数据库 Schema
{schema}

## 用户问题
{question}

## 要求
1. 只返回 SQL 语句，不要其他解释
2. 确保 SQL 语法正确
3. 使用合适的聚合函数、WHERE 条件
4. 注意处理日期、数值格式化
5. 如果问题需要关联多表，使用 JOIN

## SQL"""

CONTEXT_TEMPLATE = """已知信息：
- 数据库 Schema: {schema}
- 之前对话: {context}

用户问题: {question}

请生成 SQL 查询："""

COMPLEX_TEMPLATE = """作为 SQL 专家，请处理以下复杂查询场景：

Schema:
{schema}

问题类型: {question_type}
具体问题: {question}

{additional_instructions}

SQL:"""
