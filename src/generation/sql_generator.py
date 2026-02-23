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
        return ChatPromptTemplate.from_template("""你是一个 SQL 专家。请严格按照以下格式输出你的思考过程和 SQL 查询。
1. 首先输出 <thinking> 标签
2. 在 <thinking> 和 </thinking> 之间写下你的完整思考过程
3. 然后输出 <sql> 标签
4. 在 <sql> 和 </sql> 之间写下生成的 SQL 查询
示例格式：
<thinking>
我需要先理解用户的问题...经过分析，我认为应该查询 products 表...
</thinking>
<sql>
SELECT * FROM products;
</sql>
现在开始输出：
{schema}
用户问题: {question}
请严格按照上述格式输出：
<thinking>
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
            Dict with keys: 'type' ('thinking' or 'sql'), 'content'
        """
        try:
            chain = self.prompt_template | self.llm | self.output_parser
            in_thinking = False
            in_sql = False
            thinking_content = ""
            sql_content = ""
            buffer = ""
            
            for chunk in chain.stream({"schema": schema, "question": question}):
                buffer += chunk
                
                # 检查是否进入 thinking 阶段
                if not in_thinking and not in_sql:
                    if "<thinking>" in buffer:
                        in_thinking = True
                        # 提取 <thinking> 之后的内容
                        parts = buffer.split("<thinking>", 1)
                        buffer = parts[1] if len(parts) > 1 else ""
                
                # 处理 thinking 阶段
                if in_thinking and not in_sql:
                    if "</thinking>" in buffer:
                        # thinking 结束
                        parts = buffer.split("</thinking>", 1)
                        thinking_content += parts[0]
                        buffer = parts[1] if len(parts) > 1 else ""
                        in_thinking = False
                        in_sql = True
                        # 发送完整的 thinking
                        yield {"type": "thinking", "content": thinking_content}
                    else:
                        # 继续累加 thinking
                        thinking_content += chunk
                        yield {"type": "thinking", "content": thinking_content}
                
                # 处理 SQL 阶段
                if in_sql and buffer.strip():
                    sql_content += chunk
                    # 提取 <sql>...</sql> 之间的内容
                    if "<sql>" in buffer:
                        parts = buffer.split("<sql>", 1)
                        buffer = parts[1] if len(parts) > 1 else buffer
                    if "</sql>" in buffer:
                        parts = buffer.split("</sql>", 1)
                        sql_content = parts[0]
                        buffer = parts[1] if len(parts) > 1 else ""
                    yield {"type": "sql", "content": sql_content.strip()}
                    in_sql = False  # 完成 SQL 输出
                    
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

    def _get_native_thinking_template(self) -> ChatPromptTemplate:
        """获取不强制 thinking 标签的简化模板，让模型自由使用原生 thinking"""
        return ChatPromptTemplate.from_template("""你是一个 SQL 专家。请根据以下数据库结构和用户问题生成 SQL 查询。

数据库结构：
{schema}

用户问题：{question}

请直接输出 SQL 查询语句，不要包含任何解释或思考过程。""")

    def generate_with_native_thinking_stream(self, schema: str, question: str) -> Generator[Dict[str, str], None, None]:
        """使用简化模板的流式生成方法
        
        这个方法使用简化的 Prompt 模板，不强制要求模型输出 thinking 标签，
        让模型可以自由使用原生 thinking 能力。
        
        Args:
            schema: 数据库 Schema 文档
            question: 用户问题
            
        Yields:
            Dict with keys: 'type' ('thinking' or 'sql'), 'content'
        """
        try:
            # 使用简化模板，让模型自由决定是否使用 thinking
            simple_template = self._get_native_thinking_template()
            chain = simple_template | self.llm | self.output_parser
            
            in_thinking = True
            thinking_content = ""
            sql_content = ""
            buffer = ""
            has_sent_thinking = False
            
            for chunk in chain.stream({"schema": schema, "question": question}):
                buffer += chunk
                
                # 尝试检测是否进入 SQL 阶段
                if in_thinking:
                    # 检查是否包含 SQL 开始标记
                    if self._contains_sql_start(buffer):
                        # 提取 thinking 内容
                        thinking_content = buffer
                        for sql_starter in ["<sql>", "```sql", "SQL:", "select "]:
                            if sql_starter.lower() in buffer.lower():
                                parts = buffer.split(sql_starter, 1)
                                if len(parts) > 1:
                                    thinking_content = parts[0].strip()
                                    sql_content = parts[1].strip()
                                    break
                        in_thinking = False
                        
                        # 发送 thinking 内容
                        if thinking_content.strip():
                            yield {"type": "thinking", "content": thinking_content}
                            has_sent_thinking = True
                        
                        # 发送 SQL 内容
                        if sql_content.strip():
                            yield {"type": "sql", "content": self._clean_sql(sql_content)}
                    else:
                        # 还在 thinking 阶段，继续累积
                        if chunk:
                            yield {"type": "thinking", "content": buffer}
                            has_sent_thinking = True
                else:
                    # SQL 阶段
                    sql_content += chunk
                    yield {"type": "sql", "content": self._clean_sql(sql_content)}
            
            # 如果没有发送过 thinking，发送一个空 thinking 表示开始
            if not has_sent_thinking:
                yield {"type": "thinking", "content": ""}
                
        except Exception as e:
            logger.error(f"原生 Thinking 流式生成失败: {e}")
            yield {"type": "error", "content": str(e)}
