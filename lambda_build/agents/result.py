from typing import Any

EXPECTED_KEYS = ("success", "answer", "sources", "metadata")


def agent_result(
    success: bool,
    answer: str,
    sources: list[Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "success": bool(success),
        "answer": str(answer),
        "sources": sources,
        "metadata": metadata,
    }