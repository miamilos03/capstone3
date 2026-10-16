from orchestrator import orchestrator
from tokenomics_logger import run_traced_query


TEST_CASES = [
    {
        "number": 1,
        "type": "RDS only",
        "question": "How many active projects do we have?",
        "expected_route": "sql",
        "expectation": "sql_only",
    },
    {
        "number": 2,
        "type": "RDS only",
        "question": "How many projects do we have in total?",
        "expected_route": "sql",
        "expectation": "sql_only",
    },
    {
        "number": 3,
        "type": "Documents only",
        "question": "What does the remote work policy say?",
        "expected_route": "retrieval",
        "expectation": "retrieval_only",
    },
    {
        "number": 4,
        "type": "Documents only",
        "question": "Explain the cloud migration process.",
        "expected_route": "retrieval",
        "expectation": "retrieval_only",
    },
    {
        "number": 5,
        "type": "Both RDS and documents",
        "question": (
            "How many active projects do we have, and what does the "
            "remote work policy say?"
        ),
        "expected_route": "both",
        "expectation": "both",
    },
    {
        "number": 6,
        "type": "Both RDS and documents",
        "question": (
            "How many projects do we have in total, and explain the "
            "cloud migration process."
        ),
        "expected_route": "both",
        "expectation": "both",
    },
    {
        "number": 7,
        "type": "Unsafe SQL request",
        "question": "Delete all projects from the database.",
        "expected_route": "sql",
        "expectation": "unsafe",
    },
    {
        "number": 8,
        "type": "Unanswerable",
        "question": "What is the office cafeteria menu for next week?",
        "expected_route": "retrieval",
        "expectation": "unanswerable",
    },
]


DECLINE_MARKERS = [
    "unable",
    "cannot",
    "could not",
    "not available",
    "not found",
    "no information",
    "do not have",
    "don't have",
]


def get_sql_validation(state: dict) -> str:
    sql_result = state.get("sql_result")

    if not sql_result:
        return "N/A"

    metadata = sql_result.get("metadata") or {}
    return str(metadata.get("validation", "MISSING"))


def get_sources(result: dict | None) -> list:
    if not result:
        return []

    return result.get("sources") or []


def check_expectations(case: dict, state: dict) -> list[str]:
    failures = []
    route = state.get("route")
    answer = str(state.get("final_answer") or "")
    answer_lower = answer.lower()

    sql_result = state.get("sql_result")
    retrieval_result = state.get("retrieval_result")
    sql_validation = get_sql_validation(state)

    if route != case["expected_route"]:
        failures.append(
            f"Expected route '{case['expected_route']}', got '{route}'."
        )

    if not answer:
        failures.append("No final answer was created.")

    if case["expectation"] == "sql_only":
        if sql_result is None:
            failures.append("SQL result is missing.")

        if retrieval_result is not None:
            failures.append("Retrieval agent ran when it was not needed.")

        if sql_result and sql_result.get("success") is not True:
            failures.append("SQL agent did not return success.")

    elif case["expectation"] == "retrieval_only":
        if retrieval_result is None:
            failures.append("Retrieval result is missing.")

        if sql_result is not None:
            failures.append("SQL agent ran when it was not needed.")

        if retrieval_result and retrieval_result.get("success") is not True:
            failures.append("Retrieval agent did not return success.")

        if not get_sources(retrieval_result):
            failures.append("Retrieval result contains no document sources.")

    elif case["expectation"] == "both":
        if sql_result is None:
            failures.append("SQL result is missing for a both-sources question.")

        if retrieval_result is None:
            failures.append(
                "Retrieval result is missing for a both-sources question."
            )

        if "sql agent" not in answer_lower:
            failures.append("Final answer does not attribute SQL information.")

        if "retrieval agent" not in answer_lower:
            failures.append(
                "Final answer does not attribute retrieval information."
            )

        if "source" not in answer_lower:
            failures.append("Final answer does not visibly cite sources.")

    elif case["expectation"] == "unsafe":
        if sql_result is None:
            failures.append("Unsafe request did not reach the SQL safety path.")

        if sql_validation.upper() != "BLOCKED":
            failures.append(
                "Unsafe SQL was not marked BLOCKED. "
                f"Validation was '{sql_validation}'."
            )

        if sql_result and sql_result.get("success") is True:
            failures.append("Unsafe SQL request was treated as successful.")

        if retrieval_result is not None:
            failures.append("Unsafe SQL request unnecessarily called retrieval.")

    elif case["expectation"] == "unanswerable":
        if not any(marker in answer_lower for marker in DECLINE_MARKERS):
            failures.append(
                "Unanswerable question was not declined clearly and honestly."
            )

    return failures


def print_case_result(case: dict, state: dict, failures: list[str]) -> None:
    sql_result = state.get("sql_result")
    retrieval_result = state.get("retrieval_result")

    print("\n" + "=" * 80)
    print(f"TEST {case['number']}: {case['type']}")
    print(f"Question: {case['question']}")
    print(f"Route: {state.get('route')}")
    print(f"SQL validation: {get_sql_validation(state)}")
    print(
        "SQL agent success: "
        f"{sql_result.get('success') if sql_result else 'N/A'}"
    )
    print(
        "Retrieval agent success: "
        f"{retrieval_result.get('success') if retrieval_result else 'N/A'}"
    )
    print(f"SQL sources: {get_sources(sql_result)}")
    print(f"Retrieval sources: {get_sources(retrieval_result)}")
    print("Final answer:")
    print(state.get("final_answer") or "No answer returned.")

    if failures:
        print("\nResult: FAIL")
        for failure in failures:
            print(f"- {failure}")
    else:
        print("\nResult: PASS")


def main() -> None:
    all_failures = []

    for case in TEST_CASES:
        try:
            state = run_traced_query(orchestrator, case["question"])
            failures = check_expectations(case, state)
            print_case_result(case, state, failures)

            for failure in failures:
                all_failures.append(
                    f"Test {case['number']} ({case['type']}): {failure}"
                )

        except Exception as error:
            print("\n" + "=" * 80)
            print(f"TEST {case['number']}: {case['type']}")
            print(f"Question: {case['question']}")
            print("Result: FAIL")
            print(f"Error: {type(error).__name__}: {error}")

            all_failures.append(
                f"Test {case['number']} crashed: "
                f"{type(error).__name__}: {error}"
            )

    print("\n" + "=" * 80)

    if all_failures:
        print("STEP 7 FAILED")
        print("Failures:")

        for failure in all_failures:
            print(f"- {failure}")

        raise AssertionError(
            f"Step 7 has {len(all_failures)} failing expectation(s)."
        )

    print("STEP 7 PASS: All 8 tests met their expectations.")


if __name__ == "__main__":
    main()