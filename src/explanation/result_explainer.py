import json
import logging
from typing import Any, Dict, List, Optional, Union, Generator

logger = logging.getLogger(__name__)


class ResultExplainer:
    def __init__(self, llm: Any = None, output_parser: Any = None):
        self.llm = llm
        self.output_parser = output_parser

    def explain(
        self,
        question: str,
        result: Any,
        format: str = "text"
    ) -> str:
        parsed_result = self._parse_result(result)

        if self._is_simple_result(parsed_result):
            return self._explain_simple(question, parsed_result)
        else:
            return self._explain_complex(question, parsed_result, format)

    def explain_stream(
        self,
        question: str,
        result: Any,
        format: str = "text"
    ) -> Generator[str, None, None]:
        parsed_result = self._parse_result(result)

        if self._is_simple_result(parsed_result):
            explanation = self._explain_simple(question, parsed_result)
            yield explanation
            return

        if self.llm is None:
            fallback = self._fallback_explain(parsed_result)
            yield fallback
            return

        try:
            prompt = self._build_explain_prompt(question, parsed_result, format)

            for chunk in self.llm.stream(prompt):
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                yield content

        except Exception as e:
            logger.error(f"结果解释流式生成失败: {e}")
            yield self._fallback_explain(parsed_result)

    def _parse_result(self, result: Any) -> Union[List[Dict], Dict, str]:
        if isinstance(result, str):
            try:
                return json.loads(result)
            except:
                return self._parse_table_string(result)

        if isinstance(result, list):
            return result

        if isinstance(result, dict):
            return [result]

        return [{"value": str(result)}]

    def _parse_table_string(self, table_str: str) -> List[Dict]:
        lines = [line.strip() for line in table_str.strip().split("\n") if line.strip()]
        if not lines:
            return [{"raw": table_str}]

        headers = [h.strip() for h in lines[0].split("|") if h.strip()]
        if not headers:
            return [{"raw": table_str}]

        data = []
        for line in lines[2:]:
            values = [v.strip() for v in line.split("|") if v.strip()]
            if len(values) == len(headers):
                data.append(dict(zip(headers, values)))

        return data if data else [{"raw": table_str}]

    def _is_simple_result(self, result: Union[List, Dict]) -> bool:
        if isinstance(result, list):
            if len(result) == 1 and len(result[0]) == 1:
                return True
        return False

    def _explain_simple(
        self,
        question: str,
        result: List[Dict]
    ) -> str:
        if not result:
            return "查询结果为空"

        value = list(result[0].values())[0]

        if any(kw in question for kw in ["多少", "几个", "数量", "count", "多少个"]):
            return f"结果是 {value} 个"

        if any(kw in question for kw in ["多少", "金额", "总额", "sum", "total", "多少钱"]):
            return f"总额是 {value}"

        if any(kw in question for kw in ["平均", "avg", "平均值"]):
            return f"平均值是 {value}"

        return f"结果是 {value}"

    def _explain_complex(
        self,
        question: str,
        result: List[Dict],
        format: str = "text"
    ) -> str:
        prompt = self._build_explain_prompt(question, result, format)

        if self.llm is None:
            return self._fallback_explain(result)

        try:
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            return self._fallback_explain(result)

    def _build_explain_prompt(
        self,
        question: str,
        result: List[Dict],
        format: str
    ) -> str:
        result_str = json.dumps(result, ensure_ascii=False, indent=2)

        templates = {
            "text": f"""基于以下查询结果，用简洁的自然语言回答用户问题。

用户问题: {question}

查询结果:
{result_str}

要求：
1. 直接回答问题
2. 突出关键数字
3. 如有多条数据，先总结再详细说明
4. 使用中文回答

回答:""",

            "summary": f"""总结以下查询结果的关键信息。

查询结果:
{result_str}

请提取：
1. 总数/总数
2. 关键指标
3. 最重要的 3 条数据

总结:""",

            "comparison": f"""对比分析以下查询结果。

查询结果:
{result_str}

用户问题: {question}

请分析：
1. 数据趋势
2. 关键变化点
3. 异常值

分析:"""
        }

        return templates.get(format, templates["text"])

    def _fallback_explain(self, result: List[Dict]) -> str:
        if not result:
            return "查询结果为空"

        lines = ["查询结果如下："]

        for i, row in enumerate(result[:10]):
            items = [f"{k}: {v}" for k, v in row.items()]
            lines.append(f"- {', '.join(items)}")

        if len(result) > 10:
            lines.append(f"... 共 {len(result)} 条")

        return "\n".join(lines)
