"""
orchestrator.py -- routes a question to the SQL agent, the retrieval agent,
or both, then synthesizes a single cited answer.
"""
from typing import Optional, TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

from agents.retrieval_agent import run_retrieval_agent
from agents.sql_agent import run_sql_agent
from bedrock_client import invoke_claude

load_dotenv()


class OrchestratorState(TypedDict):
    question: str
    route: Optional[str]
    sql_result: Optional[dict]
    retrieval_result: Optional[dict]
    final_answer: Optional[str]
    token_usage: Optional[dict]


SQL_KEYWORDS = [
    "how many",
    "count",
    "total",
    "average",
    "sum",
    "revenue",
    "how much",
    "list all",
    "which clients",
    "projects",
    "invoices",
    "consultants",
    "compare",
    "trend",
    "budget",
    "contract value",
    "status",
]

DOC_KEYWORDS = [
    "policy",
    "process",
    "procedure",
    "methodology",
    "what is",
    "explain",
    "describe",
    "guidelines",
    "approach",
    "onboarding",
]


def route_question(state: OrchestratorState) -> dict:
    question = state["question"].lower()

    is_sql = any(keyword in question for keyword in SQL_KEYWORDS)
    is_doc = any(keyword in question for keyword in DOC_KEYWORDS)

    if is_sql and is_doc:
        route = "both"
    elif is_sql:
        route = "sql"
    else:
        route = "retrieval"

    usage = dict(state.get("token_usage") or {})
    usage["classification"] = {
        "method": "keyword_rules",
        "input": 0,
        "output": 0,
    }

    print(f"[Router] route={route}")

    return {
        "route": route,
        "token_usage": usage,
    }


def choose_first_agent(state: OrchestratorState) -> str:
    if state["route"] == "sql":
        return "sql_agent"

    if state["route"] == "both":
        return "sql_agent"

    return "retrieval_agent"


def choose_after_sql(state: OrchestratorState) -> str:
    if state["route"] == "both":
        return "retrieval_agent"

    return "synthesiser"


def call_sql_agent(state: OrchestratorState) -> dict:
    print("[Orchestrator] Calling SQL agent")

    result = run_sql_agent(state["question"])
    usage = dict(state.get("token_usage") or {})
    usage["sql_agent"] = result.get("metadata", {}).get(
        "token_usage",
        {"input": 0, "output": 0},
    )

    return {
        "sql_result": result,
        "token_usage": usage,
    }


def call_retrieval_agent(state: OrchestratorState) -> dict:
    print("[Orchestrator] Calling retrieval agent")

    result = run_retrieval_agent(state["question"])
    usage = dict(state.get("token_usage") or {})
    usage["retrieval_agent"] = result.get("metadata", {}).get(
        "token_usage",
        {"input": 0, "output": 0},
    )

    return {
        "retrieval_result": result,
        "token_usage": usage,
    }


def build_synthesis_context(state: OrchestratorState) -> str:
    sections = []

    sql_result = state.get("sql_result")
    if sql_result is not None:
        sql_sources = "\n".join(
            f"- {source}" for source in sql_result.get("sources", [])
        )
        sections.append(
            "[SQL agent]\n"
            f"Success: {sql_result.get('success')}\n"
            f"Answer: {sql_result.get('answer')}\n"
            f"Source SQL:\n{sql_sources}"
        )

    retrieval_result = state.get("retrieval_result")
    if retrieval_result is not None:
        document_sources = "\n".join(
            f"- {source}" for source in retrieval_result.get("sources", [])
        )
        sections.append(
            "[Retrieval agent]\n"
            f"Success: {retrieval_result.get('success')}\n"
            f"Answer: {retrieval_result.get('answer')}\n"
            f"Document sources:\n{document_sources}"
        )

    return "\n\n".join(sections)


def synthesise(state: OrchestratorState) -> dict:
    context = build_synthesis_context(state)

    if not context:
        return {
            "final_answer": (
                "I was unable to find relevant information to answer "
                "this question."
            )
        }

    prompt = (
        "Answer the user's question using only the agent results below. "
        "Do not invent information. Clearly attribute each fact. "
        "Use the exact label '[SQL agent]' for database facts and include "
        "the SQL source. Use the exact label '[Retrieval agent]' for "
        "document facts and include the document source. "
        "When both results are available, use both sources in the answer. "
        "If an agent failed, state that honestly.\n\n"
        f"User question:\n{state['question']}\n\n"
        f"Agent results:\n{context}\n\n"
        "Final answer:"
    )

    result = invoke_claude(
    prompt,
    max_tokens=800,
    component="synthesis",
)

    usage = dict(state.get("token_usage") or {})
    usage["synthesis"] = {
        "input": result["input_tokens"],
        "output": result["output_tokens"],
    }

    return {
        "final_answer": result["text"],
        "token_usage": usage,
    }


def build_orchestrator():
    graph = StateGraph(OrchestratorState)

    graph.add_node("router", route_question)
    graph.add_node("sql_agent", call_sql_agent)
    graph.add_node("retrieval_agent", call_retrieval_agent)
    graph.add_node("synthesiser", synthesise)

    graph.set_entry_point("router")

    graph.add_conditional_edges(
        "router",
        choose_first_agent,
        {
            "sql_agent": "sql_agent",
            "retrieval_agent": "retrieval_agent",
        },
    )

    graph.add_conditional_edges(
        "sql_agent",
        choose_after_sql,
        {
            "retrieval_agent": "retrieval_agent",
            "synthesiser": "synthesiser",
        },
    )

    graph.add_edge("retrieval_agent", "synthesiser")
    graph.add_edge("synthesiser", END)

    return graph.compile()


orchestrator = build_orchestrator()


def run_orchestrator(question: str) -> OrchestratorState:
    initial_state: OrchestratorState = {
        "question": question,
        "route": None,
        "sql_result": None,
        "retrieval_result": None,
        "final_answer": None,
        "token_usage": {},
    }

    return orchestrator.invoke(initial_state)