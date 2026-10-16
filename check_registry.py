from agents.tool_registry import TOOL_FUNCTIONS, TOOL_REGISTRY


expected_names = {
    "run_sql_agent",
    "run_retrieval_agent",
}

registered_names = {
    tool["name"]
    for tool in TOOL_REGISTRY
}

if registered_names != expected_names:
    raise AssertionError(
        f"Incorrect tools registered: {registered_names}"
    )

for tool in TOOL_REGISTRY:
    description = tool["description"].lower()

    has_usage_instruction = "use for" in description
    has_boundary_instruction = (
        "do not use" in description or "not for" in description
    )

    if not has_usage_instruction or not has_boundary_instruction:
        raise AssertionError(
            f"Description is not specific enough: {tool['name']}"
        )

    if tool["name"] not in TOOL_FUNCTIONS:
        raise AssertionError(
            f"No callable mapped for: {tool['name']}"
        )

    print(f"\nTool: {tool['name']}")
    print(f"Description: {tool['description']}")
    print(f"Callable registered: {tool['name'] in TOOL_FUNCTIONS}")

print("\nPASS: Both tools have specific registry descriptions.")