from datetime import datetime
from pydantic import BaseModel, Field

from app.integrations.google_calendar import GoogleCalendarClient


class SchedulingInput(BaseModel):
    request: str = Field(min_length=1)
    duration_minutes: int = Field(default=30, ge=15, le=180)


calendar_client = GoogleCalendarClient()


def handle_scheduling(payload: dict) -> str:
    data = SchedulingInput(**payload)
    request_lower = data.request.lower()

    slots = calendar_client.find_available_slots(duration_minutes=data.duration_minutes)
    if not slots:
        return "No slots found in the search window."

    if "book" in request_lower or "create" in request_lower:
        event = calendar_client.create_event(
            title="Business Agent Scheduled Meeting",
            start_at=slots[0].start_at,
            end_at=slots[0].end_at,
            attendees=[],
        )
        return f"Event {event['status']} for {event['start_at']} to {event['end_at']}."

    slot_text = ", ".join([f"{s.start_at.strftime('%Y-%m-%d %H:%M UTC')}" for s in slots])
    return f"Scheduling analysis for: '{data.request}'. Proposed slots: {slot_text}."
