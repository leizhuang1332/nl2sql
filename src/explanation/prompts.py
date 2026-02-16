CONCISE_EXPLAIN_PROMPT = """你是一个数据分析师。请简洁地回答用户问题。

用户问题: {question}

查询结果: {result}

要求：
1. 一句话回答
2. 包含关键数字
3. 使用中文

回答:"""

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

SUMMARY_PROMPT = """请总结以下查询结果的关键信息。

查询结果:
{result}

请提取：
1. 总数/总数
2. 关键指标
3. 最重要的 {max_points} 条数据

总结:"""

TREND_ANALYSIS_PROMPT = """请分析以下数据的时间趋势。

查询结果:
{result}

用户问题: {question}

请分析：
1. 整体趋势（上升/下降/平稳）
2. 峰值和谷值
3. 周期性特征（如有）

分析:"""

def get_concise_prompt(question: str, result: str) -> str:
    return CONCISE_EXPLAIN_PROMPT.format(question=question, result=result)

def get_detailed_prompt(question: str, result: str) -> str:
    return DETAILED_EXPLAIN_PROMPT.format(question=question, result=result)

def get_comparison_prompt(current: str, previous: str, question: str) -> str:
    return COMPARISON_PROMPT.format(current=current, previous=previous, question=question)

def get_summary_prompt(result: str, max_points: int = 5) -> str:
    return SUMMARY_PROMPT.format(result=result, max_points=max_points)

def get_trend_prompt(question: str, result: str) -> str:
    return TREND_ANALYSIS_PROMPT.format(question=question, result=result)
