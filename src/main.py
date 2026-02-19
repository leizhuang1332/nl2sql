"""
NL2SQL Main Entry Point.

Provides CLI and FastAPI dual-mode entry.
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import Settings, get_settings
from .core.orchestrator import NL2SQLOrchestrator
from .generation.llm_factory import create_llm


logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    question: str
    include_schema: bool = False
    include_sql: bool = False


class QueryResponse(BaseModel):
    question: str
    result: Any
    sql: Optional[str] = None
    table_schema: Optional[Dict] = None
    status: str
    error: Optional[str] = None


_orchestrator_instance: Optional[NL2SQLOrchestrator] = None


def create_orchestrator(settings: Settings) -> NL2SQLOrchestrator:
    """Create NL2SQLOrchestrator instance from settings."""
    global _orchestrator_instance
    
    if _orchestrator_instance is not None:
        return _orchestrator_instance
    
    try:
        llm = create_llm(
            provider=settings.llm_provider,
            model=settings.llm_model,
            api_key=settings.llm_api_key or settings.minimax_api_key,
            base_url=settings.llm_base_url or settings.minimax_base_url,
            temperature=settings.llm_temperature,
        )
    except ImportError as e:
        logger.warning(f"Failed to create LLM (dependency missing): {e}")
        llm = None
    
    config = {
        "field_descriptions_path": settings.path_field_descriptions,
        "semantic_mappings_path": settings.path_semantic_mappings,
        "security_policy_path": settings.path_security_policy,
        "max_retries": settings.security_max_retries,
        "timeout": settings.security_timeout,
        "read_only": settings.security_read_only,
        "allowed_tables": settings.security_allowed_tables,
        "max_rows": settings.security_max_rows,
        "explanation_enabled": settings.explanation_enabled,
        "explanation_mode": settings.explanation_mode,
        "explanation_format": settings.explanation_format,
        "explanation_language": settings.explanation_language,
        "semantic_enabled": settings.semantic_enabled,
    }
    
    _orchestrator_instance = NL2SQLOrchestrator(
        llm=llm,
        database_uri=settings.database_uri,
        config=config
    )
    
    return _orchestrator_instance


def run_cli(args: argparse.Namespace, settings: Settings) -> None:
    """Run CLI mode."""
    orchestrator = create_orchestrator(settings)
    
    if args.command == "tables":
        tables = orchestrator.get_table_names()
        print("Available tables:")
        for table in tables:
            print(f"  - {table}")
        return
    
    if args.command == "schema":
        schema = orchestrator.get_schema(args.table)
        print(f"Schema for table '{args.table}':")
        print(schema)
        return
    
    if args.command == "query":
        if orchestrator.llm is None:
            print("Error: LLM not available. Please install required dependencies.")
            print("Run: pip install langchain-anthropic")
            sys.exit(1)
        
        result = orchestrator.ask(args.question)
        
        if result.status.value == "success":
            print(f"\nQuestion: {result.question}")
            if args.show_sql and result.sql:
                print(f"\nSQL: {result.sql}")
            if result.execution and result.execution.result:
                print(f"\nResult: {result.execution.result}")
            if result.explanation:
                print(f"\nExplanation: {result.explanation}")
        else:
            print(f"Error: {result.status.value}")
            if result.error_message:
                print(f"Details: {result.error_message}")
            sys.exit(1)
        return
    
    print(f"Unknown command: {args.command}")
    sys.exit(1)


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """Create FastAPI application."""
    if settings is None:
        settings = get_settings()
    
    app = FastAPI(
        title="NL2SQL API",
        description="Natural Language to SQL Query API",
        version="0.1.0"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health")
    async def health_check() -> Dict[str, str]:
        return {"status": "healthy", "service": "nl2sql"}
    
    @app.get("/tables")
    async def list_tables() -> Dict[str, List[str]]:
        orchestrator = create_orchestrator(settings)
        tables = orchestrator.get_table_names()
        return {"tables": tables}
    
    @app.get("/schema/{table_name}")
    async def get_table_schema(table_name: str) -> Dict[str, Any]:
        try:
            orchestrator = create_orchestrator(settings)
            schema = orchestrator.get_schema(table_name)
            
            if not schema:
                raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
            
            return {"table": table_name, "schema": schema}
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.exception("Failed to get schema")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/query", response_model=QueryResponse)
    async def query(request: QueryRequest, http_request: Request) -> QueryResponse:
        try:
            orchestrator = create_orchestrator(settings)
            
            result = orchestrator.ask(request.question)
            
            return QueryResponse(
                question=result.question,
                result=result.execution.result if result.execution else None,
                sql=result.sql if request.include_sql else None,
                table_schema=result.execution.schema if request.include_schema and result.execution else None,
                status=result.status.value,
                error=result.error_message
            )
        except Exception as e:
            logger.exception("Query execution failed")
            raise HTTPException(status_code=500, detail=str(e))
    
    return app


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="NL2SQL - Natural Language to SQL Query"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML config file"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    subparsers = parser.add_subparsers(dest="mode", help="Operating mode")
    
    cli_parser = subparsers.add_parser("cli", help="CLI mode")
    cli_subparsers = cli_parser.add_subparsers(dest="command", help="CLI command")
    
    tables_parser = cli_subparsers.add_parser("tables", help="List all tables")
    tables_parser.set_defaults(command="tables")
    
    schema_parser = cli_subparsers.add_parser("schema", help="Get table schema")
    schema_parser.add_argument("table", type=str, help="Table name")
    schema_parser.set_defaults(command="schema")
    
    query_parser = cli_subparsers.add_parser("query", help="Execute query")
    query_parser.add_argument("question", type=str, help="Natural language question")
    query_parser.add_argument("--show-sql", action="store_true", help="Show generated SQL")
    query_parser.set_defaults(command="query")
    
    api_parser = subparsers.add_parser("api", help="API mode")
    api_parser.add_argument("--host", type=str, default=None, help="API host")
    api_parser.add_argument("--port", type=int, default=None, help="API port")
    api_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    if args.mode is None:
        parser.print_help()
        sys.exit(1)
    
    settings = Settings.from_yaml(args.config) if args.config else Settings()
    
    if args.mode == "cli":
        if not hasattr(args, "command"):
            print("Error: CLI mode requires a command (tables, schema, or query)")
            sys.exit(1)
        run_cli(args, settings)
    
    elif args.mode == "api":
        import uvicorn
        
        app = create_app(settings)
        
        host = args.host or settings.api_host
        port = args.port or settings.api_port
        reload = args.reload or settings.api_reload
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            log_level=settings.api_log_level
        )


if __name__ == "__main__":
    main()
