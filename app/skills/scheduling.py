from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field


class SchedulingInput(BaseModel):
    request: str = Field(min_length=1)


def handle_scheduling(payload: dict) -> str:
    data = SchedulingInput(**payload)
    now = datetime.now(timezone.utc)
    slot_1 = now + timedelta(days=1)
    slot_2 = now + timedelta(days=2)
    return (
        f"Scheduling analysis for: '{data.request}'. "
        f"Proposed slots: {slot_1.strftime('%Y-%m-%d %H:%M UTC')} or {slot_2.strftime('%Y-%m-%d %H:%M UTC')}."
    )
