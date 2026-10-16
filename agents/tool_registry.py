from collections.abc import Callable
from typing import Any

from agents.retrieval_agent import run_retrieval_agent
from agents.sql_agent import run_sql_agent


TOOL_REGISTRY: list[dict[str, Any]] = [
    {
        "name": "run_sql_agent",
        "description": (
            "Use for structured-data questions answered from the RDS database, "
            "including counts, lists, statuses, dates, budgets, contract values, "
            "clients, projects, consultants, and invoices. Do not use for "
            "onboarding procedures, policies, process descriptions, or other "
            "document-based questions. Do not use to modify data; this tool is "
            "read-only and executes only validated SELECT queries."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The user's structured-data question.",
                }
            },
            "required": ["question"],
        },
    },
    {
        "name": "run_retrieval_agent",
        "description": (
            "Use for questions answered from indexed documents, including "
            "onboarding procedures, policies, operating processes, guidelines, "
            "definitions, and other narrative content. Do not use for database "
            "counts, financial calculations, project statuses, or questions "
            "requiring current RDS records."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The user's document-based question.",
                }
            },
            "required": ["question"],
        },
    },
]


TOOL_FUNCTIONS: dict[str, Callable[[str], dict[str, Any]]] = {
    "run_sql_agent": run_sql_agent,
    "run_retrieval_agent": run_retrieval_agent,
}
