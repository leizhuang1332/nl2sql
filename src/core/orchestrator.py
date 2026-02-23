from typing import Optional, Dict, Any, List, Generator
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

    def ask_stream(self, question: str) -> Generator[Dict[str, Any], None, None]:
        start_time = time.time()

        try:
            mapping = self._semantic_mapping(question)
            yield {
                "stage": "mapping",
                "status": "success",
                "data": {
                    "enhanced_question": mapping.enhanced_question,
                    "field_mappings": mapping.field_mappings,
                },
                "timestamp": time.time() - start_time
            }
        except Exception as e:
            yield {"stage": "mapping", "status": "error", "error": str(e)}
            return

        try:
            schema_doc = self._prepare_schema()
            yield {
                "stage": "schema",
                "status": "success",
                "data": {"schema": schema_doc[:500] + "..."},
                "timestamp": time.time() - start_time
            }
        except Exception as e:
            yield {"stage": "schema", "status": "error", "error": str(e)}
            return

        try:
            sql_chunks = []
            thinking_chunks = []
            
            # 使用 generate_with_thinking_stream 同时获取 thinking 和 SQL
            for item in self.sql_generator.generate_with_thinking_stream(schema_doc, mapping.enhanced_question):
                item_type = item.get("type")
                logger.info(f"[DEBUG] orchestrator received item: type={item_type}, content={repr(item.get('content', '')[:50])}...")
                if item_type == "thinking":
                    # 流式输出 thinking
                    thinking_content = item.get("content", "")
                    thinking_chunks.append(thinking_content)
                    yield {
                        "stage": "thinking",
                        "status": "streaming",
                        "chunk": thinking_content,
                        "timestamp": time.time() - start_time
                    }
                elif item_type == "sql":
                    # 流式输出 SQL
                    sql_chunks.append(item.get("content", ""))
                    yield {
                        "stage": "sql_generating",
                        "status": "streaming",
                        "chunk": item.get("content", ""),
                        "timestamp": time.time() - start_time
                    }
                elif item_type == "error":
                    yield {
                        "stage": "thinking",
                        "status": "error",
                        "error": item.get("content", "Unknown error"),
                        "timestamp": time.time() - start_time
                    }
                    return
            
            # 完成 thinking 阶段
            thinking = "".join(thinking_chunks)
            if thinking:
                yield {
                    "stage": "thinking_done",
                    "status": "success",
                    "data": {"thinking": thinking},
                    "timestamp": time.time() - start_time
                }
            
            sql = "".join(sql_chunks)
            sql = self.sql_generator._clean_sql(sql)

            yield {
                "stage": "sql_generated",
                "status": "success",
                "data": {"sql": sql},
                "timestamp": time.time() - start_time
            }
        except Exception as e:
            yield {"stage": "thinking", "status": "error", "error": str(e)}
            return

        try:
            security_result = self._validate_security(sql)
            yield {
                "stage": "security",
                "status": "success" if security_result.is_valid else "rejected",
                "data": {
                    "is_valid": security_result.is_valid,
                    "message": security_result.message,
                },
                "timestamp": time.time() - start_time
            }

            if not security_result.is_valid:
                yield {
                    "stage": "done",
                    "status": "security_rejected",
                    "error": security_result.message,
                    "timestamp": time.time() - start_time
                }
                return
        except Exception as e:
            yield {"stage": "security", "status": "error", "error": str(e)}
            return

        try:
            execution_result = self._execute_sql(sql)
            
            # Get column names for the query
            columns = self._get_column_names(sql)
            
            yield {
                "stage": "execution",
                "status": "success" if execution_result.success else "error",
                "data": {
                    "success": execution_result.success,
                    "result": execution_result.result,
                    "error": execution_result.error,
                    "columns": columns,
                },
                "timestamp": time.time() - start_time
            }

            if not execution_result.success:
                yield {
                    "stage": "done",
                    "status": "execution_error",
                    "error": execution_result.error,
                    "timestamp": time.time() - start_time
                }
                return
        except Exception as e:
            yield {"stage": "execution", "status": "error", "error": str(e)}
            return

        try:
            explanation_chunks = []
            for chunk in self.result_explainer.explain_stream(
                question,
                execution_result.result
            ):
                explanation_chunks.append(chunk)
                yield {
                    "stage": "explaining",
                    "status": "streaming",
                    "chunk": chunk,
                    "timestamp": time.time() - start_time
                }

            explanation = "".join(explanation_chunks)

            yield {
                "stage": "explained",
                "status": "success",
                "data": {"explanation": explanation},
                "timestamp": time.time() - start_time
            }
        except Exception as e:
            yield {"stage": "explaining", "status": "error", "error": str(e)}

        yield {
            "stage": "done",
            "status": "success",
            "data": {
                "question": question,
                "sql": sql,
                "execution_result": execution_result.result,
                "columns": columns,
                "explanation": explanation if 'explanation' in locals() else None,
            },
            "timestamp": time.time() - start_time
        }

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

    def _get_column_names(self, sql: str) -> List[str]:
        """Extract column names from SQL query result."""
        try:
            # Simple table name extraction from SELECT query
            # Handle: SELECT * FROM table, SELECT col1, col2 FROM table, etc.
            sql_lower = sql.lower()
            
            # Find table name after FROM keyword
            from_idx = sql_lower.find(" from ")
            if from_idx == -1:
                return []
            
            # Get the part after FROM
            after_from = sql[from_idx + 6:].strip()
            
            # Handle JOINs - get first table name
            join_idx = after_from.find(" join ")
            if join_idx > 0:
                table_part = after_from[:join_idx].strip()
            else:
                # Handle WHERE, ORDER BY, etc.
                for delimiter in [" where ", " order by ", " group by ", " limit ", " having "]:
                    delim_idx = table_part.lower().find(delimiter) if 'table_part' in locals() else after_from.lower().find(delimiter)
                    if delim_idx > 0:
                        table_part = after_from[:delim_idx].strip()
                        break
                else:
                    table_part = after_from.split()[0] if after_from else ""
            
            # Clean table name (remove aliases, quotes, and semicolons)
            table_name = table_part.split()[0].strip('"`[];')
            
            # Get column info from database
            if table_name:
                # Use SQLDatabase's get_table_info to get columns
                table_info = self.db.get_table_info([table_name])
                # Parse DDL to extract column names
                columns = self._parse_columns_from_ddl(table_info)
                return columns
            
            return []
        except Exception as e:
            logging.warning(f"Failed to get column names: {e}")
            return []

    def _parse_columns_from_ddl(self, ddl: str) -> List[str]:
        """Parse column names from DDL string."""
        import re
        columns = []
        
        # Find the CREATE TABLE section (before comments)
        # DDL format: CREATE TABLE ... ( columns ) /* comments */
        create_table_match = re.search(r'CREATE TABLE.*?\((.*?)\)', ddl, re.DOTALL | re.IGNORECASE)
        if not create_table_match:
            return columns
        
        columns_section = create_table_match.group(1)
        
        # Match column definitions: column_name DATA_TYPE
        # Pattern: identifier followed by type (at the start of a line)
        pattern = r'^\s*(\w+)\s+\w+'
        
        for line in columns_section.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Skip constraint definitions
            if line.lower().startswith(('primary key', 'foreign key', 'unique', 'check', 'constraint')):
                continue
            
            match = re.match(pattern, line)
            if match:
                col_name = match.group(1)
                columns.append(col_name)
        
        return columns

    def _explain_result(self, question: str, result: Any) -> str:
        explanation = self.result_explainer.explain(question, result)
        return explanation

    def get_table_names(self) -> List[str]:
        return self.db.get_usable_table_names()

    def get_schema(self, table_name: str) -> Dict[str, Any]:
        return self.schema_extractor.get_table_schema(table_name)
