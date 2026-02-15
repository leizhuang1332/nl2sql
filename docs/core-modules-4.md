# 模块四：语义映射模块 - 详细实现计划

## 4.1 模块目标

解决业务术语与技术字段之间的语义鸿沟：
- 建立业务词 ↔ 技术字段的映射
- 处理时间语义（"昨天"、"本月"等）
- 处理排序语义（"Top 5"、"前三"等）
- 支持向量化语义匹配

---

## 4.2 核心功能设计

### 4.2.1 语义映射器主类

```python
# src/semantic/semantic_mapper.py
from typing import Dict, List, Optional, Any, Tuple
import re
from datetime import datetime, timedelta

class SemanticMapper:
    """语义映射器 - 业务术语转技术字段"""
    
    def __init__(self):
        # 核心映射表：业务词 -> 技术字段/表达式
        self.field_mappings: Dict[str, List[str]] = {}
        
        # 时间表达式映射
        self.time_mappings: Dict[str, str] = {}
        
        # 排序表达映射
        self.sort_mappings: Dict[str, Dict] = {}
        
        # 初始化默认映射
        self._init_default_mappings()
    
    def _init_default_mappings(self):
        """初始化默认映射"""
        # 时间表达式
        self.time_mappings = {
            "今天": "DATE('now')",
            "昨天": "DATE('now', '-1 day')",
            "前天": "DATE('now', '-2 days')",
            "明天": "DATE('now', '+1 day')",
            "上周": "DATE('now', '-7 days')",
            "本周": "DATE('now', 'weekday 0', '-7 days')",
            "本月": "DATE('now', 'start of month')",
            "上月": "DATE('now', 'start of month', '-1 month')",
            "今年": "strftime('%Y', 'now')",
            "去年": "strftime('%Y', 'now', '-1 year')",
            "最近7天": "DATE('now', '-7 days')",
            "最近30天": "DATE('now', '-30 days')",
            "最近一年": "DATE('now', '-1 year')"
        }
        
        # 排序表达
        self.sort_mappings = {
            "top": {"keyword": "LIMIT", "order": "DESC"},
            "前三": {"keyword": "LIMIT", "order": "DESC", "count": 3},
            "前五": {"keyword": "LIMIT", "order": "DESC", "count": 5},
            "前10": {"keyword": "LIMIT", "order": "DESC", "count": 10},
            "最后": {"keyword": "LIMIT", "order": "ASC", "count": 1},
            "最早": {"keyword": "ORDER BY", "order": "ASC"}
        }
    
    def add_field_mapping(self, business_term: str, technical_fields: List[str]):
        """添加业务字段映射"""
        self.field_mappings[business_term] = technical_fields
    
    def add_time_mapping(self, expression: str, sql_expression: str):
        """添加时间表达式映射"""
        self.time_mappings[expression] = sql_expression
    
    def map(self, question: str) -> Tuple[str, Dict]:
        """
        执行语义映射
        返回：增强后的问题 + 映射信息
        """
        enhanced_question = question
        mapping_info = {
            "field_mappings": [],
            "time_mappings": [],
            "sort_mappings": []
        }
        
        # 1. 字段映射
        for biz_term, tech_fields in self.field_mappings.items():
            if biz_term in question:
                enhanced_question += f"\n[提示: '{biz_term}' 对应字段 {', '.join(tech_fields)}]"
                mapping_info["field_mappings"].append({
                    "term": biz_term,
                    "fields": tech_fields
                })
        
        # 2. 时间表达式映射
        for expr, sql_expr in self.time_mappings.items():
            if expr in question:
                enhanced_question += f"\n[提示: '{expr}' 应转换为 SQL 日期 {sql_expr}]"
                mapping_info["time_mappings"].append({
                    "expression": expr,
                    "sql": sql_expr
                })
        
        # 3. 排序映射
        for expr, config in self.sort_mappings.items():
            if expr in question:
                mapping_info["sort_mappings"].append({
                    "expression": expr,
                    "config": config
                })
        
        return enhanced_question, mapping_info
```

### 4.2.2 配置管理器

```python
# src/semantic/config_manager.py
import json
from pathlib import Path
from typing import Dict, List, Any

class SemanticConfigManager:
    """语义映射配置管理器"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, path: str):
        """从文件加载配置"""
        with open(path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    def save_config(self, path: str):
        """保存配置到文件"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def get_field_mappings(self) -> Dict[str, List[str]]:
        """获取字段映射配置"""
        return self.config.get("field_mappings", {})
    
    def get_time_mappings(self) -> Dict[str, str]:
        """获取时间映射配置"""
        return self.config.get("time_mappings", {})
    
    def add_field_mapping(self, term: str, fields: List[str]):
        """添加字段映射"""
        if "field_mappings" not in self.config:
            self.config["field_mappings"] = {}
        self.config["field_mappings"][term] = fields
```

### 4.2.3 配置文件格式

```json
// config/semantic_mappings.json
{
    "field_mappings": {
        "销售额": ["sales.amount", "orders.total_amount", "revenue.total"],
        "订单数": ["orders.count", "sales.order_count"],
        "客户数": ["customers.total", "customers.count"],
        "毛利率": ["products.profit_margin"],
        "库存量": ["inventory.quantity", "stock.amount"]
    },
    "time_mappings": {
        "今天": "DATE('now')",
        "昨天": "DATE('now', '-1 day')",
        "最近7天": "DATE('now', '-7 days')",
        "本月": "DATE('now', 'start of month')",
        "本季度": "DATE('now', 'start of quarter')",
        "今年": "strftime('%Y', 'now')"
    },
    "sort_mappings": {
        "top": {"type": "limit", "order": "DESC"},
        "前三": {"type": "limit", "count": 3, "order": "DESC"},
        "倒数第一": {"type": "limit", "count": 1, "order": "ASC"}
    },
    "aggregation_mappings": {
        "平均": "AVG",
        "总计": "SUM",
        "最大": "MAX",
        "最小": "MIN",
        "计数": "COUNT",
        "去重计数": "COUNT(DISTINCT"
    }
}
```

---

## 4.3 高级功能

### 4.3.1 向量语义匹配

```python
# src/semantic/vector_matcher.py
from typing import List, Tuple, Optional
import numpy as np

class VectorMatcher:
    """向量语义匹配器 - 用于模糊匹配业务术语"""
    
    def __init__(self, embeddings_model=None):
        self.embeddings_model = embeddings_model
        self.term_vectors: Dict[str, np.ndarray] = {}
        self.terms: List[str] = []
    
    def add_term(self, term: str, vector: np.ndarray):
        """添加术语及其向量"""
        self.terms.append(term)
        self.term_vectors[term] = vector
    
    def build_index(self, terms: List[str]):
        """从术语列表构建向量索引"""
        if not self.embeddings_model:
            return
        
        self.terms = terms
        vectors = self.embeddings_model.embed_documents(terms)
        for term, vector in zip(terms, vectors):
            self.term_vectors[term] = np.array(vector)
    
    def find_similar(
        self,
        query: str,
        threshold: float = 0.8,
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """
        查找相似的术语
        返回：(术语, 相似度) 列表
        """
        if not self.embeddings_model or not self.terms:
            return []
        
        # 计算查询向量
        query_vector = np.array(
            self.embeddings_model.embed_query(query)
        )
        
        similarities = []
        for term, term_vector in self.term_vectors.items():
            # 余弦相似度
            sim = self._cosine_similarity(query_vector, term_vector)
            if sim >= threshold:
                similarities.append((term, sim))
        
        # 排序返回 top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def _cosine_similarity(
        self,
        vec1: np.ndarray,
        vec2: np.ndarray
    ) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / (norm1 * norm2)
```

### 4.3.2 上下文感知映射

```python
# src/semantic/context_aware_mapper.py
from typing import Dict, List, Optional, Tuple

class ContextAwareMapper:
    """上下文感知映射器 - 根据问题上下文选择正确字段"""
    
    def __init__(self, semantic_mapper: SemanticMapper):
        self.mapper = semantic_mapper
        # 字段上下文关联
        self.field_contexts: Dict[str, Dict] = {}
    
    def add_context(
        self,
        field: str,
        context_keywords: List[str],
        priority: int = 1
    ):
        """
        添加字段的上下文关联
        例如：sales.amount 的上下文包括 "销售额"、"收入" 等
        """
        if field not in self.field_contexts:
            self.field_contexts[field] = {
                "keywords": [],
                "priority": priority
            }
        
        self.field_contexts[field]["keywords"].extend(context_keywords)
    
    def resolve_ambiguous_field(
        self,
        business_term: str,
        question_context: str
    ) -> Optional[str]:
        """
        消解歧义字段
        根据问题上下文确定具体使用哪个字段
        """
        # 找到所有可能映射的字段
        candidate_fields = []
        
        for field, context_info in self.field_contexts.items():
            keywords = context_info["keywords"]
            for keyword in keywords:
                if keyword in business_term:
                    candidate_fields.append((field, context_info["priority"]))
        
        if not candidate_fields:
            return None
        
        # 如果只有一个候选，直接返回
        if len(candidate_fields) == 1:
            return candidate_fields[0][0]
        
        # 根据上下文关键词匹配优先级
        best_field = None
        best_score = -1
        
        for field, priority in candidate_fields:
            # 计算上下文匹配分数
            score = self._calculate_context_score(
                field,
                question_context
            )
            
            if score > best_score:
                best_score = score
                best_field = field
        
        return best_field
    
    def _calculate_context_score(
        self,
        field: str,
        context: str
    ) -> float:
        """计算上下文匹配分数"""
        if field not in self.field_contexts:
            return 0
        
        keywords = self.field_contexts[field]["keywords"]
        score = 0
        
        for keyword in keywords:
            if keyword in context:
                score += 1
        
        # 考虑优先级
        score += self.field_contexts[field]["priority"]
        
        return score
```

---

## 4.4 项目结构

```
src/
├── semantic/
│   ├── __init__.py
│   ├── semantic_mapper.py      # 语义映射器主类
│   ├── config_manager.py       # 配置管理器
│   ├── vector_matcher.py       # 向量匹配器
│   ├── context_aware_mapper.py # 上下文感知映射
│   └── time_parser.py         # 时间表达式解析
```

---

## 4.5 实现步骤

| 步骤 | 任务 | 优先级 |
|------|------|--------|
| 1 | 实现 SemanticMapper 基础映射 | P0 |
| 2 | 实现时间表达式解析 | P0 |
| 3 | 实现配置加载/保存 | P1 |
| 4 | 实现 VectorMatcher 向量匹配 | P2 |
| 5 | 实现 ContextAwareMapper 上下文感知 | P2 |
| 6 | 编写配置文件模板 | P1 |
| 7 | 集成测试与优化 | P1 |

---

## 4.6 关键策略

### 4.6.1 语义增强 Prompt

```python
SEMANTIC_ENHANCE_PROMPT = """你是一个数据库语义专家。请分析用户问题中的业务术语，并补充语义信息。

用户问题: {question}

已知字段映射:
{field_mappings}

时间表达式映射:
{time_mappings}

请输出增强后的问题，包含必要的字段提示。"""

def build_enhance_prompt(
    question: str,
    field_mappings: Dict,
    time_mappings: Dict
) -> str:
    """构建语义增强 Prompt"""
    return SEMANTIC_ENHANCE_PROMPT.format(
        question=question,
        field_mappings=json.dumps(field_mappings, ensure_ascii=False),
        time_mappings=json.dumps(time_mappings, ensure_ascii=False)
    )
```

### 4.6.2 映射优先级

```
优先级从高到低：
1. 显式配置映射（用户手动添加）
2. 上下文感知匹配（根据问题上下文）
3. 向量相似度匹配（语义相似）
4. 规则匹配（正则表达式）
5. 默认/回退映射
```

---

## 4.7 潜在挑战与解决方案

| 挑战 | 解决方案 |
|------|----------|
| 字段歧义（"销售"对应多表） | 上下文感知 + 优先策略配置 |
| 新业务术语未收录 | 支持运行时动态添加映射 |
| 时间表达复杂（"上周末"） | 扩展时间映射库 + LLM 解析 |
| 向量匹配效果差 | 优化 embedding 模型选择 |
