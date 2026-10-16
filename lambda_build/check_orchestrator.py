from pprint import pprint

from orchestrator import run_orchestrator


def show_state(label: str, question: str) -> dict:
    print("\n" + "=" * 70)
    print(label)
    print("Question:", question)

    state = run_orchestrator(question)

    print("\nPrinted state:")
    pprint(state)

    print("\nRoute:", state["route"])
    print("SQL result present:", state["sql_result"] is not None)
    print(
        "Retrieval result present:",
        state["retrieval_result"] is not None,
    )
    print("Final answer:")
    print(state["final_answer"])

    return state


sql_state = show_state(
    "SQL-ONLY TEST",
    "How many active projects do we have?",
)

assert sql_state["route"] == "sql"
assert sql_state["sql_result"] is not None
assert sql_state["retrieval_result"] is None


retrieval_state = show_state(
    "RETRIEVAL-ONLY TEST",
    "What is our onboarding process?",
)

assert retrieval_state["route"] == "retrieval"
assert retrieval_state["sql_result"] is None
assert retrieval_state["retrieval_result"] is not None


both_state = show_state(
    "BOTH-SOURCES TEST",
    "How many active projects do we have, and what is our onboarding process?",
)

assert both_state["route"] == "both"
assert both_state["sql_result"] is not None
assert both_state["retrieval_result"] is not None
assert both_state["final_answer"]

answer = both_state["final_answer"].lower()
assert "sql agent" in answer
assert "retrieval agent" in answer

print("\nPASS: Step 4 routing and synthesis checks passed.")