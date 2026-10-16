"""
tokenomics_logger.py -- structured logging and full-chain tracing for the
orchestrator, kept separate from orchestrator.py itself, the same way
bedrock_client.py stays separate from every agent that calls it.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

TOKEN_LOG_FILE = Path(
    os.getenv("TOKENOMICS_LOG_FILE", "tokenomics.jsonl")
)


def log_token_usage(
    component: str,
    model_id: str,
    input_tokens: int,
    output_tokens: int,
) -> dict:
    input_price = float(os.environ["BEDROCK_INPUT_PRICE_PER_1M"])
    output_price = float(os.environ["BEDROCK_OUTPUT_PRICE_PER_1M"])

    cost_usd = (
        (input_tokens / 1_000_000) * input_price
        + (output_tokens / 1_000_000) * output_price
    )

    entry = {
        "call_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": component,
        "model_id": model_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cost_usd": round(cost_usd, 10),
    }

    TOKEN_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    with TOKEN_LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry) + "\n")

    print(
        f"[Tokenomics] {component} | "
        f"input={input_tokens} | "
        f"output={output_tokens} | "
        f"cost=${cost_usd:.8f}"
    )

    return entry

def log_decision(stage: str, question: str, details: dict):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "question": question,
        "details": details,
    }

    print(f"[LOG] {stage}: {json.dumps(details)}")

    with open("/tmp/agent_decisions.jsonl", "a", encoding="utf-8") as file:
        file.write(json.dumps(entry) + "\n")


def route_question_logged(state):
    from orchestrator import route_question

    result = route_question(state)

    log_decision(
        "routing",
        state["question"],
        {"route": result["route"]},
    )

    return result


def run_traced_query(orchestrator, question: str) -> dict:
    trace_id = str(uuid.uuid4())[:8]

    log_decision(
        "query_start",
        question,
        {"trace_id": trace_id},
    )

    result = orchestrator.invoke({
        "question": question,
        "route": None,
        "sql_result": None,
        "retrieval_result": None,
        "final_answer": None,
        "token_usage": None,
    })

    log_decision(
        "query_complete",
        question,
        {
            "trace_id": trace_id,
            "route": result["route"],
            "sql_validation": (
                result.get("sql_result", {})
                .get("metadata", {})
                .get("validation")
                if result.get("sql_result")
                else None
            ),
            "retrieval_chunk_count": (
                len(result.get("retrieval_result", {}).get("sources", []))
                if result.get("retrieval_result")
                else None
            ),
            "token_usage": result.get("token_usage"),
        },
    )

    return result