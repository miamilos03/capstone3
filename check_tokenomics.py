from collections import defaultdict
import json

from dotenv import load_dotenv

load_dotenv()

from orchestrator import orchestrator
from tokenomics_logger import TOKEN_LOG_FILE, run_traced_query


QUESTIONS = [
    "How many active projects do we have?",
    "How many invoices are currently unpaid?",
    "Which clients are in the database?",
    "How many consultants do we have?",
    "What does the remote work policy say?",
    "Explain the cloud migration process.",
    "What is our onboarding process?",
    "What guidelines are in the remote work policy?",
    "How many active projects are there, and what does the remote work policy say?",
    "Compare project budgets and explain the cloud migration approach.",
]


TOKEN_LOG_FILE.unlink(missing_ok=True)

for number, question in enumerate(QUESTIONS, start=1):
    result = run_traced_query(orchestrator, question)

    print(
        f"Query {number}/10 | "
        f"route={result['route']} | "
        f"answer_created={bool(result.get('final_answer'))}"
    )


records = []

with TOKEN_LOG_FILE.open(encoding="utf-8") as file:
    for line in file:
        if line.strip():
            records.append(json.loads(line))

if not records:
    raise RuntimeError("No tokenomics records were created.")


summary = defaultdict(
    lambda: {
        "calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
    }
)

for record in records:
    component = record["component"]
    item = summary[component]

    item["calls"] += 1
    item["input_tokens"] += record["input_tokens"]
    item["output_tokens"] += record["output_tokens"]
    item["cost_usd"] += record["cost_usd"]


required_components = {
    "sql_generation",
    "sql_result_interpretation",
    "retrieval_answer_generation",
    "synthesis",
}

missing_components = required_components - set(summary)

if missing_components:
    raise AssertionError(
        f"Missing token logs: {sorted(missing_components)}"
    )


total_cost = 0.0
tokens_by_component = {}

print("\n10-QUERY TOKENOMICS SUMMARY")
print(f"Queries run: {len(QUESTIONS)}")
print(f"Claude calls logged: {len(records)}")
print()
print(
    f"{'Component':32} {'Calls':>5} "
    f"{'Input':>10} {'Output':>10} {'Cost USD':>12}"
)
print("-" * 75)

for component, item in sorted(summary.items()):
    total_tokens = (
        item["input_tokens"] + item["output_tokens"]
    )

    total_cost += item["cost_usd"]
    tokens_by_component[component] = total_tokens

    print(
        f"{component:32} "
        f"{item['calls']:>5} "
        f"{item['input_tokens']:>10} "
        f"{item['output_tokens']:>10} "
        f"${item['cost_usd']:>11.8f}"
    )

largest_component = max(
    tokens_by_component,
    key=tokens_by_component.get,
)

print("-" * 75)
print(f"Total cost: ${total_cost:.8f}")
print(f"Most tokens: {largest_component}")
print("\nPASS: Token logging and 10-query summary completed.")