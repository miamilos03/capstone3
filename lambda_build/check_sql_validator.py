from agents.sql_agent import validate_sql


TEST_CASES = [
    (
        "valid SELECT",
        "SELECT COUNT(*) FROM projects",
        True,
    ),
    (
        "destructive statement",
        "DELETE FROM projects",
        False,
    ),
    (
        "blocked word inside column name",
        "SELECT deleted_at FROM clients",
        True,
    ),
    (
        "stacked query with destructive keyword",
        "SELECT * FROM projects; DELETE FROM clients",
        False,
    ),
    (
        "stacked query with two SELECT statements",
        "SELECT * FROM projects; SELECT * FROM clients",
        False,
    ),
]


for name, query, expected_valid in TEST_CASES:
    result = validate_sql(query)
    actual_valid = result["valid"]
    passed = actual_valid == expected_valid

    print(f"{name}: {'PASS' if passed else 'FAIL'}")
    print(f"  Query: {query}")
    print(f"  Expected valid: {expected_valid}")
    print(f"  Actual valid: {actual_valid}")
    print(f"  Reason: {result['reason']}")

    if not passed:
        raise AssertionError(f"Failed test: {name}")


print("\nPASS: All five SQL validator tests passed.")