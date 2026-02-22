from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import List, Dict, Optional, Any, Generator
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
        try:
            chain = self.prompt_template | self.llm | self.output_parser
            sql = chain.invoke({"schema": schema, "question": question})
            return self._clean_sql(sql)
        except Exception as e:
            logger.error(f"SQL 生成失败: {e}")
            raise

    def generate_stream(self, schema: str, question: str) -> Generator[str, None, None]:
        """流式生成 SQL
        
        Args:
            schema: 数据库 Schema 文档
            question: 用户问题
            
        Yields:
            SQL 片段（逐步返回）
        """
        try:
            chain = self.prompt_template | self.llm | self.output_parser
            
            # 使用 stream() 而非 invoke()
            for chunk in chain.stream({"schema": schema, "question": question}):
                yield chunk
                
        except Exception as e:
            logger.error(f"SQL 流式生成失败: {e}")
            yield f"[ERROR] {str(e)}"

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
