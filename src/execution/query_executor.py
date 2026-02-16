from typing import Dict, Any, Optional, List
from langchain_community.utilities import SQLDatabase
import logging

logger = logging.getLogger(__name__)


class QueryExecutor:
    def __init__(
        self,
        database: SQLDatabase,
        max_retries: int = 3,
        llm: Optional[Any] = None
    ):
        self.database = database
        self.max_retries = max_retries
        self.llm = llm
        self.execution_history: List[Dict] = []

    def execute(self, sql: str) -> Dict[str, Any]:
        for attempt in range(self.max_retries):
            try:
                result = self.database.run(sql)

                self._record_execution(sql, success=True, result=result)

                return {
                    "success": True,
                    "result": result,
                    "sql": sql,
                    "attempts": attempt + 1
                }

            except Exception as e:
                error_msg = str(e)
                logger.warning(f"SQL 执行失败 (尝试 {attempt + 1}/{self.max_retries}): {error_msg}")

                self._record_execution(sql, success=False, error=error_msg)

                if attempt < self.max_retries - 1 and self.llm:
                    sql = self._fix_sql(sql, error_msg)
                    logger.info(f"修复后的 SQL: {sql}")
                else:
                    return {
                        "success": False,
                        "error": error_msg,
                        "sql": sql,
                        "attempts": attempt + 1
                    }

        return {
            "success": False,
            "error": "达到最大重试次数",
            "sql": sql,
            "attempts": self.max_retries
        }

    def _record_execution(
        self,
        sql: str,
        success: bool,
        result: Any = None,
        error: str = None
    ):
        self.execution_history.append({
            "sql": sql,
            "success": success,
            "result": result,
            "error": error
        })

    def _fix_sql(self, sql: str, error: str) -> str:
        if not self.llm:
            return sql

        fix_prompt = f"""SQL 执行失败，请修复以下 SQL 语句。

原始 SQL:
{sql}

错误信息:
{error}

请直接返回修复后的 SQL，不要解释。"""

        try:
            response = self.llm.invoke(fix_prompt)
            fixed_sql = response.content if hasattr(response, 'content') else str(response)

            fixed_sql = self._clean_sql(fixed_sql)
            return fixed_sql

        except Exception as e:
            logger.error(f"SQL 修复失败: {e}")
            return sql

    def _clean_sql(self, sql: str) -> str:
        sql = sql.strip()
        sql = sql.replace("```sql", "").replace("```", "")
        return sql.strip()

    def get_history(self) -> List[Dict]:
        return self.execution_history
