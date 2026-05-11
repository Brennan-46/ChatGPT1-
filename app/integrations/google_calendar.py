import json
import random
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError

from app.core.config import settings
from app.observability_logging import log_event

CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


class CalendarIntegrationError(Exception):
    pass


class CalendarAuthError(CalendarIntegrationError):
    pass


class CalendarRateLimitError(CalendarIntegrationError):
    pass


class CircuitOpenError(CalendarIntegrationError):
    pass


@dataclass
class CalendarSlot:
    start_at: datetime
    end_at: datetime


class GoogleCalendarClient:
    """OAuth user-flow calendar client without delete APIs (least-privilege default)."""

    _failure_count = 0
    _circuit_open_until = 0.0

    def _build_service(self) -> Resource | None:
        if not settings.google_calendar_credentials_json:
            return None
        try:
            credentials_info = json.loads(settings.google_calendar_credentials_json)
            credentials = Credentials.from_authorized_user_info(credentials_info, scopes=CALENDAR_SCOPES)
            svc = build("calendar", "v3", credentials=credentials, cache_discovery=False)
            log_event("calendar_service_initialized", calendar_id=settings.google_calendar_id)
            return svc
        except Exception as exc:
            raise CalendarAuthError(f"Failed to initialize Google Calendar credentials: {exc}") from exc

    def find_available_slots(self, duration_minutes: int = 30, days_ahead: int = 5) -> list[CalendarSlot]:
        service = self._build_service()
        if service is None:
            return self._fallback_slots(duration_minutes=duration_minutes, days_ahead=days_ahead)

        now = datetime.now(UTC)
        time_min = now.isoformat()
        time_max = (now + timedelta(days=days_ahead)).isoformat()
        body = {"timeMin": time_min, "timeMax": time_max, "items": [{"id": settings.google_calendar_id}]}

        busy = self._with_retry(lambda: service.freebusy().query(body=body).execute()).get("calendars", {}).get(settings.google_calendar_id, {}).get("busy", [])

        candidate = now.replace(hour=15, minute=0, second=0, microsecond=0)
        slots: list[CalendarSlot] = []
        for _ in range(max(days_ahead, 3)):
            candidate += timedelta(days=1)
            end = candidate + timedelta(minutes=duration_minutes)
            overlap = any(self._overlaps(candidate, end, b["start"], b["end"]) for b in busy)
            if not overlap:
                slots.append(CalendarSlot(start_at=candidate, end_at=end))
                if len(slots) >= 3:
                    break
        return slots

    def create_event(self, title: str, start_at: datetime, end_at: datetime, attendees: list[str] | None = None) -> dict[str, str]:
        service = self._build_service()
        if service is None:
            return {"status": "created_stub", "title": title, "start_at": start_at.isoformat(), "end_at": end_at.isoformat(), "attendees": ",".join(attendees or [])}

        payload = {
            "summary": title,
            "start": {"dateTime": start_at.isoformat()},
            "end": {"dateTime": end_at.isoformat()},
            "attendees": [{"email": x} for x in (attendees or [])],
        }
        created = self._with_retry(lambda: service.events().insert(calendarId=settings.google_calendar_id, body=payload).execute())
        return {
            "status": "created",
            "title": created.get("summary", title),
            "start_at": created.get("start", {}).get("dateTime", start_at.isoformat()),
            "end_at": created.get("end", {}).get("dateTime", end_at.isoformat()),
            "attendees": ",".join(attendees or []),
        }

    def _with_retry(self, fn, max_retries: int = 3):
        if time.time() < self._circuit_open_until:
            raise CircuitOpenError("Google Calendar circuit is temporarily open")
        for attempt in range(max_retries):
            try:
                result = fn()
                self._failure_count = 0
                return result
            except HttpError as exc:
                status = getattr(exc.resp, "status", None)
                if status in {401, 403}:
                    raise CalendarAuthError(f"Google Calendar auth error: HTTP {status}") from exc
                if status == 429:
                    if attempt < max_retries - 1:
                        time.sleep((2**attempt) + random.uniform(0, 0.25))
                        continue
                    self._failure_count += 1
                    self._trip_circuit_if_needed()
                    raise CalendarRateLimitError("Google Calendar rate limit exceeded") from exc
                self._failure_count += 1
                self._trip_circuit_if_needed()
                raise CalendarIntegrationError(f"Google Calendar API error: HTTP {status}") from exc
            except Exception as exc:
                self._failure_count += 1
                self._trip_circuit_if_needed()
                raise CalendarIntegrationError(f"Google Calendar request failed: {exc}") from exc
        self._failure_count += 1
        self._trip_circuit_if_needed()
        raise CalendarIntegrationError("Google Calendar retry policy exhausted")

    def _trip_circuit_if_needed(self) -> None:
        if self._failure_count >= 5:
            self._circuit_open_until = time.time() + 30

    @staticmethod
    def _fallback_slots(duration_minutes: int = 30, days_ahead: int = 5) -> list[CalendarSlot]:
        now = datetime.now(UTC)
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
