# 模块二：SQL 生成模块 - 详细实现计划

## 2.1 模块目标

将用户的自然语言问题转换为准确的 SQL 查询语句，核心包括：
- Prompt 工程设计
- LLM 调用封装
- 输出解析与验证
- Few-shot 示例管理

---

## 2.2 核心功能设计

### 2.2.1 SQL 生成器主类

```python
# src/generation/sql_generator.py
from langchain_core.prompts import ChatPromptTemplate, FewShotPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class SQLGenerator:
    """SQL 生成器 - 自然语言转 SQL"""
    
    def __init__(
        self,
        llm: Any,  # 可以是 ChatOpenAI 或其他 LLM
        prompt_template: Optional[str] = None
    ):
        self.llm = llm
        self.prompt_template = prompt_template or self._get_default_template()
        self.output_parser = StrOutputParser()
    
    def generate(self, schema: str, question: str) -> str:
        """
        生成 SQL 语句
        """
        prompt = self.prompt_template.format(
            schema=schema,
            question=question
        )
        
        try:
            result = self.llm.invoke(prompt)
            sql = self.output_parser.parse(result)
            return self._clean_sql(sql)
        except Exception as e:
            logger.error(f"SQL 生成失败: {e}")
            raise
    
    def _get_default_template(self) -> ChatPromptTemplate:
        """获取默认 Prompt 模板"""
        return ChatPromptTemplate.from_template("""
基于以下数据库 Schema，将用户问题转换为 SQL 查询。

Schema:
{schema}

用户问题: {question}

要求：
1. 只返回 SQL 语句，不要解释
2. 确保 SQL 语法正确
3. 使用合适的聚合函数和条件判断

SQL:
""")
    
    def _clean_sql(self, sql: str) -> str:
        """清理 SQL 输出，去除多余字符"""
        sql = sql.strip()
        # 移除可能的 markdown 代码块标记
        sql = sql.replace("```sql", "").replace("```", "")
        return sql.strip()
```

### 2.2.2 Few-shot Prompt 管理器

```python
# src/generation/few_shot_manager.py
from typing import List, Dict
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate

class FewShotManager:
    """Few-shot 示例管理器"""
    
    def __init__(self):
        self.examples: List[Dict[str, str]] = []
    
    def add_example(self, question: str, sql: str):
        """添加示例"""
        self.examples.append({"question": question, "sql": sql})
    
    def get_prompt_with_examples(
        self,
        schema: str,
        question: str,
        example_count: int = 3
    ) -> str:
        """
        生成包含 Few-shot 示例的 Prompt
        """
        # 选择最近的 example_count 个示例
        selected = self.examples[-example_count:]
        
        example_prompt = PromptTemplate(
            input_variables=["question", "sql"],
            template="问题: {question}\nSQL: {sql}"
        )
        
        few_shot_prompt = FewShotPromptTemplate(
            examples=selected,
            example_prompt=example_prompt,
            prefix="以下是一些示例：\n\n",
            suffix=f"\n\n基于以下数据库 Schema，将用户问题转换为 SQL。\n\nSchema:\n{schema}\n\n用户问题: {{question}}\n\nSQL:",
            input_variables=["question"]
        )
        
        return few_shot_prompt.format(question=question)
    
    def load_examples_from_file(self, filepath: str):
        """从文件加载示例"""
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.examples = data.get("examples", [])
    
    def save_examples_to_file(self, filepath: str):
        """保存示例到文件"""
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({"examples": self.examples}, f, ensure_ascii=False, indent=2)
```

### 2.2.3 Prompt 模板集合

```python
# src/generation/prompts.py

# 基础模板
BASIC_TEMPLATE = """基于以下数据库 Schema，将用户问题转换为 SQL 查询。

Schema:
{schema}

用户问题: {question}

只返回 SQL 代码，不要解释。"""

# 详细模板（带要求说明）
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

# 带上下文的模板
CONTEXT_TEMPLATE = """已知信息：
- 数据库 Schema: {schema}
- 之前对话: {context}

用户问题: {question}

请生成 SQL 查询："""

# 复杂查询模板
COMPLEX_TEMPLATE = """作为 SQL 专家，请处理以下复杂查询场景：

Schema:
{schema}

问题类型: {question_type}
具体问题: {question}

{additional_instructions}

SQL:"""
```

---

## 2.3 高级功能

### 2.3.1 多版本 LLM 支持

```python
# src/generation/llm_factory.py
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama

class LLMFactory:
    """LLM 工厂类"""
    
    @staticmethod
    def create_llm(provider: str, **kwargs) -> Any:
        """创建 LLM 实例"""
        providers = {
            "openai": lambda: ChatOpenAI(
                model=kwargs.get("model", "gpt-4"),
                temperature=kwargs.get("temperature", 0),
                api_key=kwargs.get("api_key")
            ),
            "anthropic": lambda: ChatAnthropic(
                model=kwargs.get("model", "claude-3-opus"),
                temperature=kwargs.get("temperature", 0),
                api_key=kwargs.get("api_key")
            ),
            "ollama": lambda: ChatOllama(
                model=kwargs.get("model", "llama2"),
                temperature=kwargs.get("temperature", 0)
            )
        }
        
        if provider not in providers:
            raise ValueError(f"不支持的 LLM 提供商: {provider}")
        
        return providers[provider]()
```

### 2.3.2 SQL 验证器

```python
# src/generation/sql_validator.py
import re
from typing import Tuple

class SQLValidator:
    """SQL 验证器"""
    
    def validate(self, sql: str) -> Tuple[bool, str]:
        """验证 SQL 是否合法"""
        sql = sql.strip().upper()
        
        # 检查是否包含危险操作
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
        for keyword in dangerous_keywords:
            if keyword in sql:
                return False, f"包含危险操作: {keyword}"
        
        # 检查是否 SELECT 语句
        if not sql.startswith('SELECT'):
            return False, "只支持 SELECT 查询"
        
        return True, "验证通过"
    
    def suggest_fixes(self, sql: str, error: str) -> str:
        """生成修复建议（可以调用 LLM）"""
        pass
```

---

## 2.4 项目结构

```
src/
├── generation/
│   ├── __init__.py
│   ├── sql_generator.py       # SQL 生成器主类
│   ├── few_shot_manager.py    # Few-shot 管理
│   ├── prompts.py              # Prompt 模板集合
│   ├── llm_factory.py         # LLM 工厂
│   └── sql_validator.py        # SQL 验证
```

---

## 2.5 实现步骤

| 步骤 | 任务 | 优先级 |
|------|------|--------|
| 1 | 实现 LLMFactory 支持多提供商 | P0 |
| 2 | 实现 SQLGenerator 基础功能 | P0 |
| 3 | 实现 FewShotManager 示例管理 | P1 |
| 4 | 添加多种 Prompt 模板 | P1 |
| 5 | 实现 SQLValidator 验证功能 | P1 |
| 6 | 添加示例数据收集功能 | P2 |
| 7 | 集成测试与优化 | P1 |

---

## 2.6 关键策略

### 2.6.1 提升准确率的技巧

1. **Schema 包含采样数据** - 帮助 LLM 理解字段含义
2. **Few-shot 示例** - 提供 2-5 个正确示例
3. **明确要求** - 在 Prompt 中说明具体要求
4. **输出格式约束** - "只返回 SQL，不要解释"

### 2.6.2 Prompt 工程最佳实践

```
结构：
1. 角色定义（你是 SQL 专家）
2. Schema 信息（表结构 + 采样数据）
3. 用户问题
4. 输出要求（格式、约束）
5. 示例（可选）

示例数量：2-5 个为宜
位置：相关示例在前，不相关在后
```

---

## 2.7 潜在挑战与解决方案

| 挑战 | 解决方案 |
|------|----------|
| LLM 生成错误 SQL | 添加执行验证+错误修正循环 |
| 输出格式不稳定 | 严格约束输出，用代码块标记 |
| 上下文窗口限制 | 精简 Schema 或按需加载 |
| 复杂查询理解困难 | Few-shot + 详细 Prompt |
