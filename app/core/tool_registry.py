from collections.abc import Callable
from typing import Any

from app.skills.comms import handle_comms
from app.skills.scheduling import handle_scheduling


TOOLS: dict[str, Callable[[dict[str, Any]], str]] = {
    "scheduling": handle_scheduling,
    "comms": handle_comms,
}


def select_tool(step_text: str) -> str | None:
    text = step_text.lower()
    if any(k in text for k in ["schedule", "meeting", "calendar", "book"]):
        return "scheduling"
    if any(k in text for k in ["slack", "message", "announce", "notify"]):
        return "comms"
    return None
