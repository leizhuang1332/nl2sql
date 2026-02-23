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

请按照以下格式输出：
<thinking>
在这里写出你的思考过程，包括：
1. 理解用户问题的意图
2. 确定需要查询哪些表和字段
3. 确定需要的聚合函数、筛选条件、排序等
4. 确认 SQL 逻辑的正确性
</thinking>
<sql>
在这里写出生成的 SQL 查询语句
</sql>
SQL:
""")
    def _clean_sql(self, sql: str) -> str:
        sql = sql.strip()
        # 如果包含 <sql> 标签，提取 SQL 内容
        if "<sql>" in sql and "</sql>" in sql:
            start = sql.find("<sql>") + len("<sql>")
            end = sql.find("</sql>")
            sql = sql[start:end]
        sql = sql.replace("```sql", "").replace("```", "")
        return sql.strip()
    def _extract_thinking(self, output: str) -> str:
        """从输出中提取 thinking 内容"""
        output = output.strip()
        if "<thinking>" in output and "</thinking>" in output:
            start = output.find("<thinking>") + len("<thinking>")
            end = output.find("</thinking>")
            return output[start:end].strip()
        
        return ""

    def generate_with_thinking_stream(self, schema: str, question: str) -> Generator[Dict[str, str], None, None]:
        """流式生成 thinking 和 SQL，分阶段返回
        
        Args:
            schema: 数据库 Schema 文档
            question: 用户问题
            
        Yields:
            Dict with keys: 'type' ('thinking' or 'sql'), 'content'
        """
        try:
            chain = self.prompt_template | self.llm | self.output_parser
            
            buffer = ""
            in_thinking = False
            in_sql = False
            thinking_content = ""
            
            for chunk in chain.stream({"schema": schema, "question": question}):
                buffer += chunk
                
                # 检测是否进入 thinking 阶段
                if "<thinking>" in buffer and not in_thinking:
                    # 清除 <thinking> 标签之前的内容
                    before_thinking = buffer.split("<thinking>", 1)[0]
                    if before_thinking.strip():
                        continue
                    in_thinking = True
                    buffer = buffer.split("<thinking>", 1)[1]
                
                # 处理 thinking 阶段
                if in_thinking and not in_sql:
                    if "</thinking>" in buffer:
                        # thinking 结束
                        thinking_part = buffer.split("</thinking>", 1)[0]
                        thinking_content += thinking_part
                        yield {"type": "thinking", "content": thinking_content}
                        
                        # 切换到 SQL 阶段
                        buffer = buffer.split("</thinking>", 1)[1]
                        in_thinking = False
                        in_sql = True
                    else:
                        # 继续累积 thinking 内容
                        thinking_content += chunk
                        yield {"type": "thinking", "content": thinking_content}
                
                # 处理 SQL 阶段
                if in_sql:
                    # 直接输出剩余内容（包含 <sql> 标签）
                    sql_content = buffer
                    if "<sql>" in sql_content:
                        sql_content = sql_content.split("<sql>", 1)[1]
                    if "</sql>" in sql_content:
                        sql_content = sql_content.split("</sql>", 1)[0]
                    
                    yield {"type": "sql", "content": sql_content.strip()}
                    
        except Exception as e:
            logger.error(f"Thinking + SQL 流式生成失败: {e}")
            yield {"type": "error", "content": str(e)}

    def _parse_thinking_output(self, output: str) -> str:
        """解析 thinking 输出，支持多种分隔符
        
        支持的格式:
        - <thinking>...</thinking>
        - ```thinking\n...\n```
        - ===THINKING===\n        ...
        ===END===
        
        Args:
            output: LLM 原始输出
            
        Returns:
            解析后的 thinking 内容
        """
        output = output.strip()
        
        # 格式 1: <thinking>...</thinking>
        if "<thinking>" in output and "</thinking>" in output:
            start = output.find("<thinking>") + len("<thinking>")
            end = output.find("</thinking>")
            return output[start:end].strip()
        
        # 格式 2: ```thinking...```
        if "```thinking" in output.lower():
            lines = output.split("\n")
            thinking_lines = []
            in_thinking_block = False
            for line in lines:
                if line.strip().lower().startswith("```thinking"):
                    in_thinking_block = True
                    continue
                if line.strip() == "```" and in_thinking_block:
                    break
                if in_thinking_block:
                    thinking_lines.append(line)
            if thinking_lines:
                return "\n".join(thinking_lines).strip()
        
        # 格式 3: ===THINKING=== ... ===END===
        if "===THINKING===" in output:
            start = output.find("===THINKING===") + len("===THINKING===")
            if "===END===" in output:
                end = output.find("===END===")
                return output[start:end].strip()
            return output[start:].strip()
        
        # 格式 4: 没有标签，返回空字符串
        return ""

    def _contains_sql_start(self, text: str) -> bool:
        """检测文本中是否包含 SQL 开始标记
        
        Args:
            text: 待检测文本
            
        Returns:
            True if SQL 开始标记被检测到
        """
        text_lower = text.lower().strip()
        
        # 检测各种 SQL 开始标记
        sql_starters = [
            "<sql>",
            "```sql",
            "sql:",
            "select ",
            "===",  # ===SQL=== 格式
        ]
        
        return any(text_lower.startswith(starter) or 
                   f"\n{starter}" in f"\n{text_lower}" or 
                   f" {starter}" in f" {text_lower}"
                   for starter in sql_starters)
