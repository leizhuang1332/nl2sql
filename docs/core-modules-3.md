# 模块三：查询执行与错误修正模块 - 详细实现计划

## 3.1 模块目标

实现 SQL 的安全执行与自动错误修复：
- 执行 SQL 查询并返回结果
- 捕获 SQL 执行错误
- 将错误反馈给 LLM 进行修复
- 支持多次重试直到成功或达到最大次数

---

## 3.2 核心功能设计

### 3.2.1 查询执行器主类

```python
# src/execution/query_executor.py
from typing import Dict, Any, Optional, List
from langchain_community.utilities import SQLDatabase
import logging
import re

logger = logging.getLogger(__name__)

class QueryExecutor:
    """SQL 查询执行器"""
    
    def __init__(
        self,
        database: SQLDatabase,
        max_retries: int = 3,
        llm: Optional[Any] = None
    ):
        self.database = database
        self.max_retries = max_retries
        self.llm = llm  # 用于错误修复的 LLM
        self.execution_history: List[Dict] = []
    
    def execute(self, sql: str) -> Dict[str, Any]:
        """
        执行 SQL 查询
        返回：成功/失败状态、结果/错误信息、执行的 SQL
        """
        for attempt in range(self.max_retries):
            try:
                # 执行查询
                result = self.database.run(sql)
                
                # 记录成功执行
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
                
                # 记录失败执行
                self._record_execution(sql, success=False, error=error_msg)
                
                # 如果还有重试次数，尝试修复
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
        """记录执行历史"""
        self.execution_history.append({
            "sql": sql,
            "success": success,
            "result": result,
            "error": error
        })
    
    def _fix_sql(self, sql: str, error: str) -> str:
        """
        使用 LLM 修复 SQL 错误
        """
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
            
            # 清理输出
            fixed_sql = self._clean_sql(fixed_sql)
            return fixed_sql
            
        except Exception as e:
            logger.error(f"SQL 修复失败: {e}")
            return sql  # 返回原始 SQL
    
    def _clean_sql(self, sql: str) -> str:
        """清理 SQL 输出"""
        sql = sql.strip()
        # 移除 markdown 代码块
        sql = sql.replace("```sql", "").replace("```", "")
        return sql.strip()
    
    def get_history(self) -> List[Dict]:
        """获取执行历史"""
        return self.execution_history
```

### 3.2.2 执行结果处理器

```python
# src/execution/result_handler.py
from typing import Any, Dict, List, Union
import json

class ResultHandler:
    """执行结果处理器"""
    
    def __init__(self):
        self.formatters = {
            "table": self._format_table,
            "json": self._format_json,
            "text": self._format_text,
            "markdown": self._format_markdown
        }
    
    def handle(
        self,
        result: Any,
        format_type: str = "table"
    ) -> Union[str, List[Dict]]:
        """
        处理查询结果
        """
        # 解析结果字符串
        parsed = self._parse_result(result)
        
        # 格式化输出
        formatter = self.formatters.get(format_type, self._format_table)
        return formatter(parsed)
    
    def _parse_result(self, result: Any) -> List[Dict]:
        """
        解析 SQL 返回的结果
        支持字符串格式和原始格式
        """
        if isinstance(result, str):
            # LangChain 返回的可能是字符串格式
            try:
                # 尝试解析为 JSON
                return json.loads(result)
            except:
                # 尝试解析为表格格式
                return self._parse_table_string(result)
        
        if isinstance(result, list):
            return result
        
        return [{"value": str(result)}]
    
    def _parse_table_string(self, table_str: str) -> List[Dict]:
        """
        解析表格字符串格式
        例如: "[('Alice', 25), ('Bob', 30)]"
        """
        # 实现表格字符串解析
        # 这里需要根据实际返回格式调整
        return []
    
    def _format_table(self, data: List[Dict]) -> str:
        """格式化为表格"""
        if not data:
            return "无结果"
        
        # 获取所有列名
        headers = list(data[0].keys()) if data else []
        
        # 构建表格
        lines = []
        
        # 表头
        lines.append(" | ".join(headers))
        lines.append(" | ".join(["---"] * len(headers)))
        
        # 数据行
        for row in data:
            values = [str(row.get(h, "")) for h in headers]
            lines.append(" | ".join(values))
        
        return "\n".join(lines)
    
    def _format_json(self, data: List[Dict]) -> str:
        """格式化为 JSON"""
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def _format_text(self, data: List[Dict]) -> str:
        """格式化为纯文本"""
        if not data:
            return "无结果"
        
        lines = []
        for row in data:
            for key, value in row.items():
                lines.append(f"{key}: {value}")
            lines.append("---")
        
        return "\n".join(lines)
    
    def _format_markdown(self, data: List[Dict]) -> str:
        """格式化为 Markdown"""
        md = "## 查询结果\n\n"
        md += self._format_table(data)
        return md
```

### 3.2.3 错误分析与分类

```python
# src/execution/error_analyzer.py
from typing import Tuple, Dict
import re

class ErrorAnalyzer:
    """SQL 错误分析器"""
    
    # 常见错误模式
    ERROR_PATTERNS = {
        "syntax": [
            r"syntax error",
            r"near .*",
            r"unexpected .*"
        ],
        "no_table": [
            r"no such table",
            r"table .* doesn't exist"
        ],
        "no_column": [
            r"no such column",
            r"column .* not found"
        ],
        "type_mismatch": [
            r"cannot convert",
            r"type mismatch"
        ],
        "constraint": [
            r"UNIQUE constraint",
            r"FOREIGN KEY constraint",
            r"NOT NULL constraint"
        ]
    }
    
    def analyze(self, error_msg: str) -> Tuple[str, Dict]:
        """
        分析错误类型并返回分类和建议
        """
        error_msg = error_msg.lower()
        
        for error_type, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, error_msg, re.IGNORECASE):
                    return error_type, self._get_suggestion(error_type)
        
        return "unknown", {"message": "未知错误类型", "fix_suggestion": "请检查 SQL 语法"}
    
    def _get_suggestion(self, error_type: str) -> Dict:
        """获取错误修复建议"""
        suggestions = {
            "syntax": {
                "message": "SQL 语法错误",
                "fix_suggestion": "检查关键字拼写、括号匹配、引号使用"
            },
            "no_table": {
                "message": "表不存在",
                "fix_suggestion": "确认表名是否正确，检查 Schema"
            },
            "no_column": {
                "message": "列不存在",
                "fix_suggestion": "确认字段名是否正确，注意大小写"
            },
            "type_mismatch": {
                "message": "数据类型不匹配",
                "fix_suggestion": "检查字段类型，确保类型转换正确"
            },
            "constraint": {
                "message": "约束冲突",
                "fix_suggestion": "检查数据是否违反约束条件"
            }
        }
        return suggestions.get(error_type, {})
```

---

## 3.3 高级功能

### 3.3.1 重试策略配置

```python
# src/execution/retry_strategy.py
from typing import Optional
from enum import Enum

class RetryStrategy(Enum):
    """重试策略"""
    IMMEDIATE = "immediate"      # 立即重试
    LINEAR = "linear"            # 线性等待
    EXPONENTIAL = "exponential"   # 指数退避

class RetryConfig:
    """重试配置"""
    
    def __init__(
        self,
        max_retries: int = 3,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        base_delay: float = 1.0,
        max_delay: float = 10.0
    ):
        self.max_retries = max_retries
        self.strategy = strategy
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def get_delay(self, attempt: int) -> float:
        """计算重试延迟"""
        if self.strategy == RetryStrategy.IMMEDIATE:
            return 0
        
        if self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * attempt
        else:  # EXPONENTIAL
            delay = self.base_delay * (2 ** attempt)
        
        return min(delay, self.max_delay)
```

### 3.3.2 慢查询检测

```python
# src/execution/query_monitor.py
import time
from typing import Dict, Optional

class QueryMonitor:
    """查询监控器"""
    
    def __init__(self, slow_query_threshold: float = 5.0):
        self.slow_query_threshold = slow_query_threshold
        self.query_stats: Dict[str, Dict] = {}
    
    def record_query(self, sql: str, duration: float, success: bool):
        """记录查询执行信息"""
        if sql not in self.query_stats:
            self.query_stats[sql] = {
                "count": 0,
                "total_duration": 0,
                "success_count": 0,
                "failure_count": 0
            }
        
        stats = self.query_stats[sql]
        stats["count"] += 1
        stats["total_duration"] += duration
        
        if success:
            stats["success_count"] += 1
        else:
            stats["failure_count"] += 1
        
        # 标记慢查询
        if duration > self.slow_query_threshold:
            stats["is_slow"] = True
            stats["slow_duration"] = duration
    
    def get_slow_queries(self) -> list:
        """获取慢查询列表"""
        return [
            sql for sql, stats in self.query_stats.items()
            if stats.get("is_slow")
        ]
```

---

## 3.4 项目结构

```
src/
├── execution/
│   ├── __init__.py
│   ├── query_executor.py       # 查询执行器
│   ├── result_handler.py       # 结果处理器
│   ├── error_analyzer.py       # 错误分析器
│   ├── retry_strategy.py       # 重试策略
│   └── query_monitor.py        # 查询监控
```

---

## 3.5 实现步骤

| 步骤 | 任务 | 优先级 |
|------|------|--------|
| 1 | 实现 QueryExecutor 基础执行 | P0 |
| 2 | 实现错误捕获与重试逻辑 | P0 |
| 3 | 实现 ResultHandler 结果处理 | P0 |
| 4 | 实现 ErrorAnalyzer 错误分析 | P1 |
| 5 | 实现 RetryConfig 重试配置 | P1 |
| 6 | 实现 QueryMonitor 监控 | P2 |
| 7 | 集成测试与优化 | P1 |

---

## 3.6 关键策略

### 3.6.1 错误修复 Prompt 模板

```python
ERROR_FIX_PROMPT = """你是一个 SQL 专家。请修复以下 SQL 语句的错误。

原始 SQL:
{sql}

错误信息:
{error}

数据库 Schema:
{schema}

要求：
1. 分析错误原因
2. 修复 SQL
3. 只返回修复后的 SQL，不要解释

修复后的 SQL:"""

def build_fix_prompt(sql: str, error: str, schema: str) -> str:
    """构建错误修复 Prompt"""
    return ERROR_FIX_PROMPT.format(sql=sql, error=error, schema=schema)
```

### 3.6.2 执行流程

```
执行 SQL (尝试 1)
    ↓ 成功
返回结果

    ↓ 失败
分析错误类型
    ↓
生成修复 Prompt
    ↓
调用 LLM 修复
    ↓
执行 SQL (尝试 2)
    ↓ 成功
返回结果

    ↓ 失败
重复直到达到最大次数
```

---

## 3.7 潜在挑战与解决方案

| 挑战 | 解决方案 |
|------|----------|
| LLM 修复失败 | 限制重试次数，返回原始错误 |
| 无限循环修复 | 设置最大重试次数（建议 3 次） |
| 错误分类不准 | 补充更多错误模式，定期更新 |
| 慢查询影响体验 | 添加超时机制和监控告警 |
