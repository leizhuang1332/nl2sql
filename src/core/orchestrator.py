from typing import Optional, Dict, Any, List
import time
import logging

from langchain_community.utilities import SQLDatabase

from .types import (
    QueryResult,
    QueryStatus,
    MappingResult,
    SecurityResult,
    ExecutionResult,
)
from ..schema.database_connector import DatabaseConnector
from ..schema.schema_extractor import SchemaExtractor
from ..schema.schema_doc_generator import SchemaDocGenerator
from ..schema.schema_enhancer import SchemaEnhancer
from ..generation.sql_generator import SQLGenerator
from ..execution.query_executor import QueryExecutor
from ..semantic.semantic_mapper import SemanticMapper
from ..semantic.config_manager import SemanticConfigManager
from ..security.sql_validator import SQLSecurityValidator
from ..explanation.result_explainer import ResultExplainer


logger = logging.getLogger(__name__)


class NL2SQLOrchestrator:
    def __init__(
        self,
        llm: Any,
        database_uri: str,
        config: Optional[Dict[str, Any]] = None
    ):
        self.llm = llm
        self.database_uri = database_uri
        self.config = config or {}

        self._init_modules()

    def _init_modules(self):
        db_path = self.database_uri.replace("sqlite:///", "") if self.database_uri.startswith("sqlite:///") else self.database_uri
        
        self.db_connector = DatabaseConnector(db_path=db_path, db_type="sqlite")
        self.db = self.db_connector.db
        self.schema_extractor = SchemaExtractor(self.db)
        self.schema_doc_generator = SchemaDocGenerator(self.db)
        
        field_descriptions_path = self.config.get("field_descriptions_path")
        self.schema_enhancer = SchemaEnhancer(config_path=field_descriptions_path)

        self.sql_generator = SQLGenerator(
            llm=self.llm,
            prompt_template=None
        )

        self.query_executor = QueryExecutor(
            database=self.db,
            max_retries=self.config.get("max_retries", 3),
            llm=self.llm
        )

        self.semantic_mapper = SemanticMapper()
        semantic_config_path = self.config.get("semantic_mappings_path")
        if semantic_config_path:
            self.semantic_config = SemanticConfigManager(semantic_config_path)
            field_mappings = self.semantic_config.get_field_mappings()
            for term, fields in field_mappings.items():
                self.semantic_mapper.add_field_mapping(term, fields)
            time_mappings = self.semantic_config.get_time_mappings()
            for expr, sql_expr in time_mappings.items():
                self.semantic_mapper.add_time_mapping(expr, sql_expr)

        self.security_validator = SQLSecurityValidator(
            allowed_tables=self.config.get("allowed_tables"),
            allowed_columns=self.config.get("allowed_columns"),
            read_only=self.config.get("read_only", True)
        )

        self.result_explainer = ResultExplainer(llm=self.llm)

        logger.info("All modules initialized")

    def ask(self, question: str) -> QueryResult:
        start_time = time.time()

        result = QueryResult(
            status=QueryStatus.SUCCESS,
            question=question
        )

        try:
            mapping = self._semantic_mapping(question)
            result.mapping = mapping

            schema_doc = self._prepare_schema()

            sql = self._generate_sql(mapping.enhanced_question, schema_doc)
            result.sql = sql

            security_result = self._validate_security(sql)
            result.security = security_result

            if not security_result.is_valid:
                result.status = QueryStatus.SECURITY_REJECTED
                result.error_message = security_result.message
                result.metadata["execution_time"] = time.time() - start_time
                return result

            execution_result = self._execute_sql(sql)
            result.execution = execution_result

            if not execution_result.success:
                result.status = QueryStatus.EXECUTION_ERROR
                result.error_message = execution_result.error
                result.metadata["execution_time"] = time.time() - start_time
                return result

            explanation = self._explain_result(
                question,
                execution_result.result
            )
            result.explanation = explanation

            result.metadata["execution_time"] = time.time() - start_time

        except Exception as e:
            logger.error(f"Query processing failed: {e}", exc_info=True)
            result.status = QueryStatus.GENERATION_ERROR
            result.error_message = str(e)
            result.metadata["execution_time"] = time.time() - start_time

        return result

    def _semantic_mapping(self, question: str) -> MappingResult:
        enhanced_question, mapping_info = self.semantic_mapper.map(question)

        return MappingResult(
            enhanced_question=enhanced_question,
            field_mappings=mapping_info.get("field_mappings", []),
            time_mappings=mapping_info.get("time_mappings", []),
            sort_mappings=mapping_info.get("sort_mappings", [])
        )

    def _prepare_schema(self) -> str:
        tables = self.db.get_usable_table_names()

        if hasattr(self.schema_enhancer, 'enhance_tables'):
            self.schema_enhancer.enhance_tables(tables)

        schema_doc = self.schema_doc_generator.generate_full_doc(tables)

        return schema_doc

    def _generate_sql(self, enhanced_question: str, schema_doc: str) -> str:
        sql = self.sql_generator.generate(schema_doc, enhanced_question)
        return sql

    def _validate_security(self, sql: str) -> SecurityResult:
        validation = self.security_validator.validate(sql)

        return SecurityResult(
            is_valid=validation.is_valid,
            threat_level=validation.threat_level.value,
            message=validation.message,
            details=validation.details
        )

    def _execute_sql(self, sql: str) -> ExecutionResult:
        exec_result = self.query_executor.execute(sql)

        return ExecutionResult(
            success=exec_result["success"],
            result=exec_result.get("result"),
            error=exec_result.get("error", ""),
            attempts=exec_result.get("attempts", 1),
            execution_time=0.0
        )

    def _explain_result(self, question: str, result: Any) -> str:
        explanation = self.result_explainer.explain(question, result)
        return explanation

    def get_table_names(self) -> List[str]:
        return self.db.get_usable_table_names()

    def get_schema(self, table_name: str) -> Dict[str, Any]:
        return self.schema_extractor.get_table_schema(table_name)
