# 模块六：结果解释模块 - 分阶段实现计划

---

## Phase 1: 模块目标

将 SQL 查询结果翻译为自然语言回答：
- 结构化结果 → 人类可读的文字
- 关键数字提取与解读
- 对比分析（环比、同比）
- 多样化输出格式支持

---

## Phase 2: 核心功能设计

### 2.1 结果解释器主类

```python
# src/explanation/result_explainer.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import Dict, List, Any, Optional, Union
import json

class ResultExplainer:
    """结果解释器 - SQL 结果转自然语言"""
    
    def __init__(self, llm: Any, output_parser: Any = None):
        self.llm = llm
        self.output_parser = output_parser
    
    def explain(
        self,
        question: str,
        result: Any,
        format: str = "text"
    ) -> str:
        """
        解释查询结果
        """
        # 解析结果
        parsed_result = self._parse_result(result)
        
        # 根据格式选择解释策略
        if self._is_simple_result(parsed_result):
            return self._explain_simple(question, parsed_result)
        else:
            return self._explain_complex(question, parsed_result, format)
    
    def _parse_result(self, result: Any) -> Union[List[Dict], Dict, str]:
        """解析查询结果"""
        if isinstance(result, str):
            try:
                return json.loads(result)
            except:
                return self._parse_table_string(result)
        
        if isinstance(result, list):
            return result
        
        return [{"value": str(result)}]
    
    def _parse_table_string(self, table_str: str) -> List[Dict]:
        """解析表格字符串"""
        # 简化实现
        return [{"raw": table_str}]
    
    def _is_simple_result(self, result: Union[List, Dict]) -> bool:
        """判断是否为简单结果（单行单列）"""
        if isinstance(result, list):
            if len(result) == 1 and len(result[0]) == 1:
                return True
        return False
    
    def _explain_simple(
        self,
        question: str,
        result: List[Dict]
    ) -> str:
        """解释简单结果"""
        if not result:
            return "查询结果为空"
        
        # 提取值
        value = list(result[0].values())[0]
        
        # 构建解释
        # 分析问题类型
        if any(kw in question for kw in ["多少", "几个", "数量", "count"]):
            return f"结果是 {value} 个"
        
        if any(kw in question for kw in ["多少", "金额", "总额", "sum", "total"]):
            return f"总额是 {value}"
        
        if any(kw in question for kw in ["平均", "avg"]):
            return f"平均值是 {value}"
        
        return f"结果是 {value}"
    
    def _explain_complex(
        self,
        question: str,
        result: List[Dict],
        format: str = "text"
    ) -> str:
        """解释复杂结果（多行多列）"""
        prompt = self._build_explain_prompt(question, result, format)
        
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
        """构建解释 Prompt"""
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
        """降级解释（LLM 失败时）"""
        if not result:
            return "查询结果为空"
        
        lines = ["查询结果如下："]
        
        # 限制显示行数
        for i, row in enumerate(result[:10]):
            items = [f"{k}: {v}" for k, v in row.items()]
            lines.append(f"- {', '.join(items)}")
        
        if len(result) > 10:
            lines.append(f"... 共 {len(result)} 条")
        
        return "\n".join(lines)
```

### 2.2 数据分析师

```python
# src/explanation/data_analyst.py
from typing import Dict, List, Any, Optional
import statistics

class DataAnalyst:
    """数据分析师 - 统计分析功能"""
    
    def analyze(self, result: List[Dict]) -> Dict[str, Any]:
        """
        分析数据，返回统计信息
        """
        if not result:
            return {"error": "无数据"}
        
        # 提取数值列
        numeric_columns = self._extract_numeric_columns(result)
        
        analysis = {
            "row_count": len(result),
            "column_count": len(result[0]) if result else 0,
            "numeric_analysis": {}
        }
        
        # 分析数值列
        for col in numeric_columns:
            values = [row[col] for row in result if row.get(col) is not None]
            
            if values:
                try:
                    numeric_values = [float(v) for v in values]
                    
                    analysis["numeric_analysis"][col] = {
                        "sum": sum(numeric_values),
                        "avg": statistics.mean(numeric_values),
                        "min": min(numeric_values),
                        "max": max(numeric_values),
                        "count": len(numeric_values)
                    }
                except:
                    pass
        
        return analysis
    
    def _extract_numeric_columns(self, result: List[Dict]) -> List[str]:
        """提取数值列"""
        if not result:
            return []
        
        numeric_cols = []
        
        for col, value in result[0].items():
            if self._is_numeric(value):
                numeric_cols.append(col)
        
        return numeric_cols
    
    def _is_numeric(self, value: Any) -> bool:
        """判断是否为数值"""
        try:
            float(value)
            return True
        except:
            return False
    
    def calculate_trend(
        self,
        current: List[Dict],
        previous: List[Dict],
        metric_column: str
    ) -> Dict[str, Any]:
        """计算趋势（环比/同比）"""
        current_values = [row[metric_column] for row in current if metric_column in row]
        previous_values = [row[metric_column] for row in previous if metric_column in row]
        
        if not current_values or not previous_values:
            return {"error": "数据不足"}
        
        current_sum = sum(float(v) for v in current_values)
        previous_sum = sum(float(v) for v in previous_values)
        
        if previous_sum == 0:
            change = 0
        else:
            change = ((current_sum - previous_sum) / previous_sum) * 100
        
        return {
            "current": current_sum,
            "previous": previous_sum,
            "change": change,
            "trend": "up" if change > 0 else "down" if change < 0 else "flat"
        }
```

### 2.3 格式化器集合

```python
# src/explanation/formatters.py
from typing import Dict, List, Any
from datetime import datetime

class ResultFormatter:
    """结果格式化器"""
    
    @staticmethod
    def format_number(value: Any, format_type: str = "default") -> str:
        """格式化数字"""
        try:
            num = float(value)
            
            if format_type == "currency":
                return f"¥{num:,.2f}"
            
            if format_type == "percentage":
                return f"{num:.1f}%"
            
            if format_type == "compact":
                if abs(num) >= 10000:
                    return f"{num/10000:.1f}万"
                if abs(num) >= 1000:
                    return f"{num/1000:.1f}千"
            
            # 默认格式
            if isinstance(num, int) or num == int(num):
                return str(int(num))
            return f"{num:.2f}"
            
        except:
            return str(value)
    
    @staticmethod
    def format_table(
        result: List[Dict],
        max_rows: int = 10,
        max_width: int = 50
    ) -> str:
        """格式化表格输出"""
        if not result:
            return "无数据"
        
        # 获取列名
        headers = list(result[0].keys())
        
        # 计算列宽
        col_widths = {}
        for header in headers:
            col_widths[header] = min(
                max(len(str(header)), max_width),
                max(len(str(row.get(header, ""))) for row in result) + 2
            )
        
        lines = []
        
        # 表头
        header_line = " | ".join(
            str(h).ljust(col_widths[h]) for h in headers
        )
        lines.append(header_line)
        lines.append("-" * len(header_line))
        
        # 数据行
        for i, row in enumerate(result):
            if i >= max_rows:
                break
            
            line = " | ".join(
                str(row.get(h, "")).ljust(col_widths[h])[:max_width]
                for h in headers
            )
            lines.append(line)
        
        # 总数提示
        if len(result) > max_rows:
            lines.append(f"... 共 {len(result)} 条")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_json(result: List[Dict]) -> str:
        """格式化为 JSON"""
        import json
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    @staticmethod
    def format_markdown(result: List[Dict]) -> str:
        """格式化为 Markdown 表格"""
        if not result:
            return "无数据"
        
        headers = list(result[0].keys())
        
        lines = []
        
        # 表头
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        # 数据行
        for row in result:
            values = [str(row.get(h, "")) for h in headers]
            lines.append("| " + " | ".join(values) + " |")
        
        return "\n".join(lines)
```

---

## Phase 3: 高级功能

### 3.1 智能摘要生成

```python
# src/explanation/summarizer.py
from typing import Dict, List, Any

class ResultSummarizer:
    """结果摘要生成器"""
    
    def summarize(
        self,
        result: List[Dict],
        max_points: int = 5
    ) -> str:
        """
        生成摘要
        """
        if not result:
            return "查询结果为空"
        
        analysis = self._analyze_result(result)
        
        lines = []
        
        # 总数
        if "row_count" in analysis:
            lines.append(f"共 {analysis['row_count']} 条数据")
        
        # 关键指标
        if "numeric_analysis" in analysis:
            for col, stats in analysis["numeric_analysis"].items():
                lines.append(
                    f"{col}: 总计 {stats['sum']:.2f}, "
                    f"平均 {stats['avg']:.2f}, "
                    f"最大 {stats['max']:.2f}, 最小 {stats['min']:.2f}"
                )
        
        # Top 数据
        top_data = self._get_top_items(result, max_points)
        if top_data:
            lines.append("\n关键数据：")
            for i, item in enumerate(top_data, 1):
                lines.append(f"{i}. {item}")
        
        return "\n".join(lines)
    
    def _analyze_result(self, result: List[Dict]) -> Dict:
        """分析结果"""
        # 简化实现
        return {"row_count": len(result)}
    
    def _get_top_items(
        self,
        result: List[Dict],
        max_items: int
    ) -> List[str]:
        """获取关键数据"""
        # 简化实现
        return []
```

### 3.2 对比分析器

```python
# src/explanation/comparator.py
from typing import Dict, List, Any, Optional

class ComparisonAnalyzer:
    """对比分析器"""
    
    def compare(
        self,
        current: List[Dict],
        previous: List[Dict],
        question: str
    ) -> str:
        """
        对比分析
        """
        if not current or not previous:
            return "数据不足，无法对比"
        
        # 简化实现 - 计算基本统计
        current_stats = self._basic_stats(current)
        previous_stats = self._basic_stats(previous)
        
        lines = [
            f"当前数据：{current_stats}",
            f"上期数据：{previous_stats}"
        ]
        
        return "\n".join(lines)
    
    def _basic_stats(self, data: List[Dict]) -> str:
        """基本统计"""
        return f"{len(data)} 条"
```

---

## Phase 4: 项目结构

```
src/
├── explanation/
│   ├── __init__.py
│   ├── result_explainer.py     # 结果解释器主类
│   ├── data_analyst.py         # 数据分析师
│   ├── formatters.py           # 格式化器
│   ├── summarizer.py           # 摘要生成器
│   └── comparator.py           # 对比分析器
```

---

## Phase 5: 实现步骤

| 步骤 | 任务 | 优先级 |
|------|------|--------|
| 1 | 实现 ResultExplainer 基础解释 | P0 |
| 2 | 实现 ResultFormatter 格式化 | P0 |
| 3 | 实现 DataAnalyst 数据分析 | P1 |
| 4 | 实现 ResultSummarizer 摘要生成 | P1 |
| 5 | 实现 ComparisonAnalyzer 对比分析 | P2 |
| 6 | 添加多语言支持 | P2 |
| 7 | 集成测试与优化 | P1 |

---

## Phase 6: 解释 Prompt 模板

### 6.1 简洁回答模板

```python
CONCISE_EXPLAIN_PROMPT = """你是一个数据分析师。请简洁地回答用户问题。

用户问题: {question}

查询结果: {result}

要求：
1. 一句话回答
2. 包含关键数字
3. 使用中文

回答:"""
```

### 6.2 详细分析模板

```python
DETAILED_EXPLAIN_PROMPT = """你是一个数据分析专家。请详细分析以下查询结果。

用户问题: {question}

查询结果:
{result}

请分析：
1. 数据概况（总数、平均等）
2. 关键发现
3. 数据趋势
4. 异常值（如有）

分析:"""
```

### 6.3 对比分析模板

```python
COMPARISON_PROMPT = """你是一个数据分析专家。请对比分析以下两组数据。

当前数据:
{current}

上期数据:
{previous}

用户问题: {question}

请分析：
1. 变化幅度
2. 增长/下降趋势
3. 关键驱动因素

分析:"""
```

---

## Phase 7: 潜在挑战与解决方案

| 挑战 | 解决方案 |
|------|----------|
| 结果数据量大 | 限制展示行数 + 摘要先行 |
| LLM 幻觉 | 严格基于结果生成 + 验证 |
| 数值格式混乱 | 统一格式化 + 类型检测 |
| 响应延迟高 | 结果简单时使用规则解释 |
