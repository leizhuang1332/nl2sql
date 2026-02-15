# 模块二：SQL 生成模块 - Phase 实现计划

## Phase 0: 概述

### 模块目标

将用户的自然语言问题转换为准确的 SQL 查询语句，核心包括：
- Prompt 工程设计
- LLM 调用封装
- 输出解析与验证
- Few-shot 示例管理

### MVP 规范

**使用模型**: MiniMax M2.5

**LLM 兼容性设计**:
- 本模块设计为兼容任意符合 **OpenAI风格** 和 **Anthropic风格** 的 LLM
- MVP 仅支持 MiniMax M2.5

---

## Phase 1: LLM 工厂 + SQL 生成器

### 目标

实现 LLM 工厂 (支持 MiniMax M2.5) 和 SQL 生成器基础功能

### 文件

| 文件 | 描述 |
|------|------|
| `src/generation/llm_factory.py` | LLM 工厂类 |
| `src/generation/sql_generator.py` | SQL 生成器主类 |

### LLMFactory 实现

```python
# src/generation/llm_factory.py
from typing import Any, Literal
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

class LLMFactory:
    """LLM 工厂类 - 支持任意 OpenAI/Anthropic 风格 LLM"""
    
    PROVIDERS = Literal["minimax", "openai", "anthropic", "ollama", "custom"]
    
    @staticmethod
    def create_llm(
        provider: PROVIDER,
        model: str = None,
        api_key: str = None,
        base_url: str = None,
        temperature: float = 0,
        **kwargs
    ) -> Any:
        """创建 LLM 实例"""
        
        if provider == "minimax":
            # MVP 使用 MiniMax M2.5
            return ChatOpenAI(
                model=model or "MiniMax-M2.5",
                api_key=api_key,
                base_url=base_url or "https://api.minimax.chat/v1",
                temperature=temperature,
                **kwargs
            )
        
        elif provider == "openai":
            return ChatOpenAI(
                model=model or "gpt-4",
                api_key=api_key,
                temperature=temperature,
                **kwargs
            )
        
        elif provider == "anthropic":
            return ChatAnthropic(
                model=model or "claude-3-opus-20240229",
                api_key=api_key,
                temperature=temperature,
                **kwargs
            )
        
        elif provider == "ollama":
            from langchain_community.chat_models import ChatOllama
            return ChatOllama(
                model=model or "llama2",
                temperature=temperature,
                **kwargs
            )
        
        elif provider == "custom":
            # 兼容任意 OpenAI 风格的 API
            return ChatOpenAI(
                model=model,
                api_key=api_key,
                base_url=base_url,
                temperature=temperature,
                **kwargs
            )
        
        else:
            raise ValueError(f"不支持的 LLM 提供商: {provider}")
```

### SQLGenerator 实现

```python
# src/generation/sql_generator.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class SQLGenerator:
    """SQL 生成器 - 自然语言转 SQL"""
    
    def __init__(
        self,
        llm: Any,
        prompt_template: Optional[ChatPromptTemplate] = None
    ):
        self.llm = llm
        self.prompt_template = prompt_template or self._get_default_template()
        self.output_parser = StrOutputParser()
    
    def generate(self, schema: str, question: str) -> str:
        """生成 SQL 语句"""
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
        sql = sql.replace("```sql", "").replace("```", "")
        return sql.strip()
```

### 使用示例

```python
from src.generation.llm_factory import LLMFactory
from src.generation.sql_generator import SQLGenerator

# 创建 LLM 实例 (MVP: MiniMax M2.5)
llm = LLMFactory.create_llm(
    provider="minimax",
    model="MiniMax-M2.5",
    api_key="your-api-key",
    base_url="https://api.minimax.chat/v1",
    temperature=0
)

# 创建 SQL 生成器
generator = SQLGenerator(llm=llm)

# 生成 SQL
schema = "users(id, name, email)"
question = "查询所有用户"
sql = generator.generate(schema=schema, question=question)
```

### 测试

```python
# tests/test_generation_phase1.py
import pytest
from src.generation.llm_factory import LLMFactory
from src.generation.sql_generator import SQLGenerator
from unittest.mock import MagicMock

def test_llm_factory_create_minimax():
    llm = LLMFactory.create_llm(
        provider="minimax",
        model="MiniMax-M2.5",
        api_key="test-key"
    )
    assert llm.model_name == "MiniMax-M2.5"

def test_sql_generator_init():
    mock_llm = MagicMock()
    generator = SQLGenerator(llm=mock_llm)
    assert generator.llm == mock_llm

def test_sql_generator_clean_sql():
    mock_llm = MagicMock()
    generator = SQLGenerator(llm=mock_llm)
    
    # Test markdown code block removal
    assert generator._clean_sql("```sql\nSELECT * FROM users\n```") == "SELECT * FROM users"
    assert generator._clean_sql("SELECT * FROM users") == "SELECT * FROM users"
```

---

## Phase 2: Few-shot 管理 + Prompt 模板

### 目标

实现 Few-shot 示例管理和多种 Prompt 模板

### 文件

| 文件 | 描述 |
|------|------|
| `src/generation/few_shot_manager.py` | Few-shot 示例管理器 |
| `src/generation/prompts.py` | Prompt 模板集合 |

### FewShotManager 实现

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
        """生成包含 Few-shot 示例的 Prompt"""
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

### Prompts 实现

```python
# src/generation/prompts.py

# 基础模板
BASIC_TEMPLATE = """基于以下数据库 Schema，将用户问题转换为 SQL 查询。

Schema:
{schema}

用户问题: {question}

只返回 SQL 代码，不要解释。"""

# 详细模板
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

## Phase 3: SQL 验证器

### 目标

实现 SQL 验证功能，防止危险操作

### 文件

| 文件 | 描述 |
|------|------|
| `src/generation/sql_validator.py` | SQL 验证器 |

### SQLValidator 实现

```python
# src/generation/sql_validator.py
from typing import Tuple

class SQLValidator:
    """SQL 验证器"""
    
    DANGEROUS_KEYWORDS = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
    
    def validate(self, sql: str) -> Tuple[bool, str]:
        """验证 SQL 是否合法"""
        sql = sql.strip().upper()
        
        # 检查是否包含危险操作
        for keyword in self.DANGEROUS_KEYWORDS:
            if keyword in sql:
                return False, f"包含危险操作: {keyword}"
        
        # 检查是否 SELECT 语句
        if not sql.startswith('SELECT'):
            return False, "只支持 SELECT 查询"
        
        return True, "验证通过"
    
    def validate_with_fix(self, sql: str) -> Tuple[bool, str, str]:
        """验证并尝试修复"""
        is_valid, message = self.validate(sql)
        if is_valid:
            return True, message, sql
        
        # 简单修复：移除危险关键词
        fixed_sql = sql
        for keyword in self.DANGEROUS_KEYWORDS:
            fixed_sql = fixed_sql.replace(keyword, "")
        
        is_valid_fixed, message_fixed = self.validate(fixed_sql)
        return is_valid_fixed, message_fixed, fixed_sql if is_valid_fixed else sql
```

---

## Phase 4: 集成测试 (可选)

### 项目结构

```
src/
├── generation/
│   ├── __init__.py
│   ├── sql_generator.py       # Phase 1
│   ├── few_shot_manager.py    # Phase 2
│   ├── prompts.py              # Phase 2
│   ├── llm_factory.py         # Phase 1
│   └── sql_validator.py       # Phase 3
```

### 实现步骤

| Phase | 任务 | 优先级 |
|-------|------|--------|
| 1 | LLMFactory + SQLGenerator | P0 |
| 2 | FewShotManager + prompts | P1 |
| 3 | SQLValidator | P1 |
| 4 | 集成测试 | P2 |

---

## 关键策略

### 提升准确率的技巧

1. **Schema 包含采样数据** - 帮助 LLM 理解字段含义
2. **Few-shot 示例** - 提供 2-5 个正确示例
3. **明确要求** - 在 Prompt 中说明具体要求
4. **输出格式约束** - "只返回 SQL，不要解释"

### Prompt 工程最佳实践

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

## 潜在挑战与解决方案

| 挑战 | 解决方案 |
|------|----------|
| LLM 生成错误 SQL | 添加执行验证+错误修正循环 |
| 输出格式不稳定 | 严格约束输出，用代码块标记 |
| 上下文窗口限制 | 精简 Schema 或按需加载 |
| 复杂查询理解困难 | Few-shot + 详细 Prompt |
