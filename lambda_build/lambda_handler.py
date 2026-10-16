"""
lambda_handler.py -- wraps the orchestrator in the format Lambda expects.
"""
import json

from orchestrator import build_orchestrator
from tokenomics_logger import run_traced_query


orchestrator = build_orchestrator()


def handler(event, context):
    try:
        raw_body = event.get("body", "{}") if isinstance(event, dict) else "{}"
        body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
        question = body.get("question", "").strip()

        if not question:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "question is required"}),
            }

        result = run_traced_query(orchestrator, question)

        sql_result = result.get("sql_result") or {}
        metadata = sql_result.get("metadata") or {}
        sql_validation = metadata.get("validation")

        response_body = {
            "answer": result.get("final_answer"),
            "route": result.get("route"),
            "sql_validation": sql_validation,
            "token_usage": result.get("token_usage") or {},
        }

        print(
            "ORCHESTRATOR_RESULT "
            + json.dumps(response_body, default=str)
        )

        return {
            "statusCode": 200,
            "body": json.dumps(response_body, default=str),
        }

    except Exception as error:
        print(
            "ORCHESTRATOR_ERROR "
            + json.dumps(
                {
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
            )
        )

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": "The orchestrator failed.",
                    "error_type": type(error).__name__,
                }
            ),
        }