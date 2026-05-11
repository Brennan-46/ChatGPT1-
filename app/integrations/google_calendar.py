from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class CalendarSlot:
    start_at: datetime
    end_at: datetime


class GoogleCalendarClient:
    """
    Production placeholder for Google Calendar.
    Intentionally excludes delete APIs to enforce least-privilege defaults.
    """

    def find_available_slots(self, duration_minutes: int = 30, days_ahead: int = 5) -> list[CalendarSlot]:
        now = datetime.now(timezone.utc)
        slots = []
        for i in range(1, min(days_ahead, 3) + 1):
            start = (now + timedelta(days=i)).replace(hour=15, minute=0, second=0, microsecond=0)
            end = start + timedelta(minutes=duration_minutes)
            slots.append(CalendarSlot(start_at=start, end_at=end))
        return slots

    def create_event(self, title: str, start_at: datetime, end_at: datetime, attendees: list[str] | None = None) -> dict[str, str]:
        return {
            "status": "created_stub",
            "title": title,
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
            "attendees": ",".join(attendees or []),
        }
