from agents.result import EXPECTED_KEYS
from agents.sql_agent import run_sql_agent
from agents.retrieval_agent import run_retrieval_agent


def check_agent(name, function, question):
    result = function(question)
    keys = tuple(result.keys())

    print(f"\n{name}")
    print(f"Question: {question}")
    print(f"Top-level keys: {list(keys)}")
    print(f"Exact interface: {keys == EXPECTED_KEYS}")
    print(f"Success: {result['success']}")
    print(f"Sources: {result['sources']}")
    print(f"Metadata keys: {list(result['metadata'].keys())}")

    if keys != EXPECTED_KEYS:
        raise AssertionError(
            f"{name} returned incorrect top-level keys: {keys}"
        )

    if not result["success"]:
        raise RuntimeError(
            f"{name} failed. Review its metadata: {result['metadata']}"
        )


check_agent(
    "SQL agent",
    run_sql_agent,
    "How many active projects do we have?",
)

check_agent(
    "Retrieval agent",
    run_retrieval_agent,
    "What is our onboarding process?",
)

print("\nPASS: Both tools share the required interface.")