from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class QueryStatus(Enum):
    SUCCESS = "success"
    SEMANTIC_ERROR = "semantic_error"
    GENERATION_ERROR = "generation_error"
    SECURITY_REJECTED = "security_rejected"
    EXECUTION_ERROR = "execution_error"
    EXPLANATION_ERROR = "explanation_error"


@dataclass
class MappingResult:
    enhanced_question: str
    field_mappings: List[Dict[str, Any]] = field(default_factory=list)
    time_mappings: List[Dict[str, Any]] = field(default_factory=list)
    sort_mappings: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class GenerationResult:
    sql: str
    confidence: float = 1.0
    used_few_shots: List[str] = field(default_factory=list)


@dataclass
class SecurityResult:
    is_valid: bool
    threat_level: str = "safe"
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    success: bool
    result: Any = None
    error: str = ""
    attempts: int = 1
    execution_time: float = 0.0


@dataclass
class QueryResult:
    status: QueryStatus
    question: str
    mapping: Optional[MappingResult] = None
    sql: str = ""
    security: Optional[SecurityResult] = None
    execution: Optional[ExecutionResult] = None
    explanation: str = ""
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
