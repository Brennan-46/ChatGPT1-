import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.config import settings

CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


@dataclass
class CalendarSlot:
    start_at: datetime
    end_at: datetime


class GoogleCalendarClient:
    """
    OAuth user-flow calendar client.
    Expects GOOGLE_CALENDAR_CREDENTIALS_JSON to contain authorized user JSON.
    Intentionally excludes delete APIs to enforce least-privilege defaults.
    """

    def _service(self):
        if not settings.google_calendar_credentials_json:
            return None
        credentials_info = json.loads(settings.google_calendar_credentials_json)
        credentials = Credentials.from_authorized_user_info(credentials_info, scopes=CALENDAR_SCOPES)
        return build("calendar", "v3", credentials=credentials, cache_discovery=False)

    def find_available_slots(self, duration_minutes: int = 30, days_ahead: int = 5) -> list[CalendarSlot]:
        service = self._service()
        if service is None:
            return self._fallback_slots(duration_minutes=duration_minutes, days_ahead=days_ahead)

        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        time_max = (now + timedelta(days=days_ahead)).isoformat()
        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": settings.google_calendar_id}],
        }
        busy = (
            service.freebusy()
            .query(body=body)
            .execute()
            .get("calendars", {})
            .get(settings.google_calendar_id, {})
            .get("busy", [])
        )

        # simple first-pass slot generation; can be upgraded with robust availability search
        candidate = now + timedelta(days=1)
        candidate = candidate.replace(hour=15, minute=0, second=0, microsecond=0)
        slots: list[CalendarSlot] = []
        for _ in range(3):
            end = candidate + timedelta(minutes=duration_minutes)
            overlap = any(self._overlaps(candidate, end, b["start"], b["end"]) for b in busy)
            if not overlap:
                slots.append(CalendarSlot(start_at=candidate, end_at=end))
            candidate += timedelta(days=1)
        return slots

    def create_event(self, title: str, start_at: datetime, end_at: datetime, attendees: list[str] | None = None) -> dict[str, str]:
        service = self._service()
        if service is None:
            return {
                "status": "created_stub",
                "title": title,
                "start_at": start_at.isoformat(),
                "end_at": end_at.isoformat(),
                "attendees": ",".join(attendees or []),
            }

        payload = {
            "summary": title,
            "start": {"dateTime": start_at.isoformat()},
            "end": {"dateTime": end_at.isoformat()},
            "attendees": [{"email": x} for x in (attendees or [])],
        }
        created = service.events().insert(calendarId=settings.google_calendar_id, body=payload).execute()
        return {
            "status": "created",
            "title": created.get("summary", title),
            "start_at": created.get("start", {}).get("dateTime", start_at.isoformat()),
            "end_at": created.get("end", {}).get("dateTime", end_at.isoformat()),
            "attendees": ",".join(attendees or []),
        }

    def _fallback_slots(self, duration_minutes: int = 30, days_ahead: int = 5) -> list[CalendarSlot]:
        now = datetime.now(timezone.utc)
        slots = []
        for i in range(1, min(days_ahead, 3) + 1):
            start = (now + timedelta(days=i)).replace(hour=15, minute=0, second=0, microsecond=0)
            end = start + timedelta(minutes=duration_minutes)
            slots.append(CalendarSlot(start_at=start, end_at=end))
        return slots

    @staticmethod
    def _overlaps(start: datetime, end: datetime, busy_start: str, busy_end: str) -> bool:
        b_start = datetime.fromisoformat(busy_start.replace("Z", "+00:00"))
        b_end = datetime.fromisoformat(busy_end.replace("Z", "+00:00"))
        return start < b_end and end > b_start
