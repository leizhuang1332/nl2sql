# 模块四：语义映射模块 - Phase 实现计划

## Phase 0: 概述

### 模块目标

解决业务术语与技术字段之间的语义鸿沟：
- 建立业务词 ↔ 技术字段的映射
- 处理时间语义（"昨天"、"本月"等）
- 处理排序语义（"Top 5"、"前三"等）
- 支持向量化语义匹配

---

## Phase 1: 核心映射功能

### 目标

实现 SemanticMapper 基础映射、时间表达式解析、配置加载/保存

### 文件

| 文件 | 描述 |
|------|------|
| `src/semantic/semantic_mapper.py` | 语义映射器主类 |
| `src/semantic/time_parser.py` | 时间表达式解析器 |
| `src/semantic/config_manager.py` | 配置管理器 |
| `config/semantic_mappings.json` | 配置文件模板 |

### SemanticMapper 实现

```python
# src/semantic/semantic_mapper.py
from typing import Dict, List, Optional, Tuple
import re

class SemanticMapper:
    def __init__(self):
        self.field_mappings: Dict[str, List[str]] = {}
        self.time_mappings: Dict[str, str] = {}
        self.sort_mappings: Dict[str, Dict] = {}
        self._init_default_mappings()

    def _init_default_mappings(self):
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
        
        self.sort_mappings = {
            "top": {"keyword": "LIMIT", "order": "DESC"},
            "前三": {"keyword": "LIMIT", "order": "DESC", "count": 3},
            "前五": {"keyword": "LIMIT", "order": "DESC", "count": 5},
            "前10": {"keyword": "LIMIT", "order": "DESC", "count": 10},
            "最后": {"keyword": "LIMIT", "order": "ASC", "count": 1},
            "最早": {"keyword": "ORDER BY", "order": "ASC"}
        }

    def add_field_mapping(self, business_term: str, technical_fields: List[str]):
        self.field_mappings[business_term] = technical_fields

    def add_time_mapping(self, expression: str, sql_expression: str):
        self.time_mappings[expression] = sql_expression

    def map(self, question: str) -> Tuple[str, Dict]:
        enhanced_question = question
        mapping_info = {
            "field_mappings": [],
            "time_mappings": [],
            "sort_mappings": []
        }
        
        for biz_term, tech_fields in self.field_mappings.items():
            if biz_term in question:
                enhanced_question += f"\n[提示: '{biz_term}' 对应字段 {', '.join(tech_fields)}]"
                mapping_info["field_mappings"].append({
                    "term": biz_term,
                    "fields": tech_fields
                })
        
        for expr, sql_expr in self.time_mappings.items():
            if expr in question:
                enhanced_question += f"\n[提示: '{expr}' 应转换为 SQL 日期 {sql_expr}]"
                mapping_info["time_mappings"].append({
                    "expression": expr,
                    "sql": sql_expr
                })
        
        for expr, config in self.sort_mappings.items():
            if expr in question:
                mapping_info["sort_mappings"].append({
                    "expression": expr,
                    "config": config
                })
        
        return enhanced_question, mapping_info
```

### TimeParser 实现

```python
# src/semantic/time_parser.py
from typing import Optional, Tuple
from datetime import datetime, timedelta
import re

class TimeParser:
    def __init__(self):
        self.patterns = {}

    def parse(self, expression: str) -> Optional[Tuple[str, str]]:
        """解析时间表达式，返回 (start_date, end_date)"""
        expression = expression.strip()
        
        if expression == "今天":
            return ("DATE('now')", "DATE('now')")
        elif expression == "昨天":
            return ("DATE('now', '-1 day')", "DATE('now', '-1 day')")
        elif expression == "最近7天":
            return ("DATE('now', '-7 days')", "DATE('now')")
        elif expression == "本月":
            return ("DATE('now', 'start of month')", "DATE('now')")
        
        return None
```

### ConfigManager 实现

```python
# src/semantic/config_manager.py
import json
from typing import Dict, List, Any

class SemanticConfigManager:
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}

    def load_config(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def save_config(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def get_field_mappings(self) -> Dict[str, List[str]]:
        return self.config.get("field_mappings", {})

    def get_time_mappings(self) -> Dict[str, str]:
        return self.config.get("time_mappings", {})
```

### 配置文件模板

```json
// config/semantic_mappings.json
{
    "field_mappings": {
        "销售额": ["sales.amount", "orders.total_amount", "revenue.total"],
        "订单数": ["orders.count", "sales.order_count"],
        "客户数": ["customers.total", "customers.count"]
    },
    "time_mappings": {
        "今天": "DATE('now')",
        "昨天": "DATE('now', '-1 day')",
        "本月": "DATE('now', 'start of month')"
    },
    "sort_mappings": {
        "top": {"type": "limit", "order": "DESC"},
        "前三": {"type": "limit", "count": 3, "order": "DESC"}
    }
}
```

### 测试

```python
# tests/test_semantic_phase1.py
import pytest
from src.semantic.semantic_mapper import SemanticMapper
from src.semantic.time_parser import TimeParser

def test_semantic_mapper_init():
    mapper = SemanticMapper()
    assert mapper is not None
    assert len(mapper.time_mappings) > 0

def test_add_field_mapping():
    mapper = SemanticMapper()
    mapper.add_field_mapping("销售额", ["sales.amount"])
    assert "销售额" in mapper.field_mappings

def test_map_question():
    mapper = SemanticMapper()
    mapper.add_field_mapping("销售额", ["sales.amount"])
    result, info = mapper.map("查询销售额")
    assert "销售额" in result

def test_time_parser():
    parser = TimeParser()
    result = parser.parse("今天")
    assert result is not None
```

---

## Phase 2: 向量语义匹配

### 目标

实现 VectorMatcher 向量语义匹配

### 文件

| 文件 | 描述 |
|------|------|
| `src/semantic/vector_matcher.py` | 向量语义匹配器 |

### VectorMatcher 实现

```python
# src/semantic/vector_matcher.py
from typing import List, Tuple, Optional, Dict
import numpy as np

class VectorMatcher:
    def __init__(self, embeddings_model=None):
        self.embeddings_model = embeddings_model
        self.term_vectors: Dict[str, np.ndarray] = {}
        self.terms: List[str] = []

    def build_index(self, terms: List[str]):
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
        if not self.embeddings_model or not self.terms:
            return []
        
        query_vector = np.array(
            self.embeddings_model.embed_query(query)
        )
        
        similarities = []
        for term, term_vector in self.term_vectors.items():
            sim = self._cosine_similarity(query_vector, term_vector)
            if sim >= threshold:
                similarities.append((term, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / (norm1 * norm2)
```

### 测试

```python
# tests/test_semantic_phase2.py
import pytest
import numpy as np
from unittest.mock import MagicMock
from src.semantic.vector_matcher import VectorMatcher

def test_vector_matcher_init():
    matcher = VectorMatcher()
    assert matcher is not None

def test_vector_matcher_without_model():
    matcher = VectorMatcher()
    result = matcher.find_similar("销售")
    assert result == []

def test_vector_matcher_with_mock():
    matcher = VectorMatcher()
    mock_model = MagicMock()
    mock_model.embed_documents.return_value = [[1, 0], [0, 1]]
    mock_model.embed_query.return_value = [1, 0]
    matcher.embeddings_model = mock_model
    
    matcher.build_index(["销售", "订单"])
    result = matcher.find_similar("销售", threshold=0.5)
    
    assert len(result) > 0

def test_cosine_similarity():
    matcher = VectorMatcher()
    vec1 = np.array([1, 0])
    vec2 = np.array([1, 0])
    sim = matcher._cosine_similarity(vec1, vec2)
    assert sim == 1.0
```

---

## Phase 3: 上下文感知映射

### 目标

实现 ContextAwareMapper 上下文感知字段消解

### 文件

| 文件 | 描述 |
|------|------|
| `src/semantic/context_aware_mapper.py` | 上下文感知映射器 |

### ContextAwareMapper 实现

```python
# src/semantic/context_aware_mapper.py
from typing import Dict, List, Optional, Tuple

class ContextAwareMapper:
    def __init__(self, semantic_mapper=None):
        self.mapper = semantic_mapper
        self.field_contexts: Dict[str, Dict] = {}

    def add_context(
        self,
        field: str,
        context_keywords: List[str],
        priority: int = 1
    ):
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
        candidate_fields = []
        
        for field, context_info in self.field_contexts.items():
            keywords = context_info["keywords"]
            for keyword in keywords:
                if keyword in business_term:
                    candidate_fields.append((field, context_info["priority"]))
        
        if not candidate_fields:
            return None
        
        if len(candidate_fields) == 1:
            return candidate_fields[0][0]
        
        best_field = None
        best_score = -1
        
        for field, priority in candidate_fields:
            score = self._calculate_context_score(field, question_context)
            
            if score > best_score:
                best_score = score
                best_field = field
        
        return best_field

    def _calculate_context_score(self, field: str, context: str) -> float:
        if field not in self.field_contexts:
            return 0
        
        keywords = self.field_contexts[field]["keywords"]
        score = 0
        
        for keyword in keywords:
            if keyword in context:
                score += 1
        
        score += self.field_contexts[field]["priority"]
        
        return score
```

### 测试

```python
# tests/test_semantic_phase3.py
import pytest
from src.semantic.context_aware_mapper import ContextAwareMapper
from src.semantic.semantic_mapper import SemanticMapper

def test_context_aware_mapper_init():
    mapper = ContextAwareMapper()
    assert mapper is not None

def test_add_context():
    mapper = ContextAwareMapper()
    mapper.add_context("sales.amount", ["销售额", "收入"], priority=1)
    assert "sales.amount" in mapper.field_contexts

def test_resolve_ambiguous_field():
    mapper = ContextAwareMapper()
    mapper.add_context("sales.amount", ["月销售额"], priority=1)
    mapper.add_context("orders.amount", ["订单金额"], priority=2)
    
    result = mapper.resolve_ambiguous_field("销售额", "查询月销售额")
    assert result in ["sales.amount", "orders.amount"]

def test_calculate_context_score():
    mapper = ContextAwareMapper()
    mapper.add_context("sales.amount", ["销售额", "收入"], priority=1)
    score = mapper._calculate_context_score("sales.amount", "查询销售额数据")
    assert score > 0
```

---

## 项目结构

```
src/
├── semantic/
│   ├── __init__.py
│   ├── semantic_mapper.py      # Phase 1
│   ├── time_parser.py          # Phase 1
│   ├── config_manager.py       # Phase 1
│   ├── vector_matcher.py       # Phase 2
│   └── context_aware_mapper.py # Phase 3
```

---

## 实现步骤

| Phase | 任务 | 优先级 |
|-------|------|--------|
| 1 | SemanticMapper + TimeParser + Config | P0 |
| 2 | VectorMatcher 向量匹配 | P1 |
| 3 | ContextAwareMapper 上下文感知 | P1 |

---

## 关键策略

### 映射优先级

```
优先级从高到低：
1. 显式配置映射（用户手动添加）
2. 上下文感知匹配（根据问题上下文）
3. 向量相似度匹配（语义相似）
4. 规则匹配（正则表达式）
5. 默认/回退映射
```
