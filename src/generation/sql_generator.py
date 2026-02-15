from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class SQLGenerator:
    def __init__(
        self,
        llm: Any,
        prompt_template: Optional[ChatPromptTemplate] = None
    ):
        self.llm = llm
        self.prompt_template = prompt_template or self._get_default_template()
        self.output_parser = StrOutputParser()

    def generate(self, schema: str, question: str) -> str:
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
        sql = sql.strip()
        sql = sql.replace("```sql", "").replace("```", "")
        return sql.strip()
