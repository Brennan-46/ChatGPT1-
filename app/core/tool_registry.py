from collections.abc import Callable
from typing import Any

from app.skills.scheduling import handle_scheduling


TOOLS: dict[str, Callable[[dict[str, Any]], str]] = {
    "scheduling": handle_scheduling,
}


def select_tool(step_text: str) -> str | None:
    text = step_text.lower()
    if any(k in text for k in ["schedule", "meeting", "calendar"]):
        return "scheduling"
    return None
