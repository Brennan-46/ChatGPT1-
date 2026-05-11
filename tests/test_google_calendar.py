from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from googleapiclient.errors import HttpError

from app.integrations.google_calendar import (
    CalendarAuthError,
    CalendarIntegrationError,
    CalendarRateLimitError,
    GoogleCalendarClient,
)


class DummyReq:
    def __init__(self, payload):
        self._payload = payload

    def execute(self):
        return self._payload


class DummyFreeBusy:
    def __init__(self, payload):
        self.payload = payload

    def query(self, body):
        return DummyReq(self.payload)


class DummyEvents:
    def __init__(self, payload):
        self.payload = payload

    def insert(self, calendarId, body):
        return DummyReq(self.payload)


class DummyService:
    def __init__(self, freebusy_payload=None, event_payload=None):
        self._freebusy_payload = freebusy_payload or {"calendars": {"primary": {"busy": []}}}
        self._event_payload = event_payload or {"summary": "x", "start": {"dateTime": "s"}, "end": {"dateTime": "e"}}

    def freebusy(self):
        return DummyFreeBusy(self._freebusy_payload)

    def events(self):
        return DummyEvents(self._event_payload)


def test_find_available_slots_uses_fallback_without_credentials(monkeypatch):
    monkeypatch.setattr('app.integrations.google_calendar.settings.google_calendar_credentials_json', '')
    client = GoogleCalendarClient()
    slots = client.find_available_slots(30, 3)
    assert len(slots) >= 1


def test_find_available_slots_with_service(monkeypatch):
    payload = {"calendars": {"primary": {"busy": []}}}
    client = GoogleCalendarClient()
    monkeypatch.setattr(client, '_build_service', lambda: DummyService(freebusy_payload=payload))
    slots = client.find_available_slots(30, 3)
    assert len(slots) >= 1


def test_create_event_calls_insert(monkeypatch):
    event_payload = {
        "summary": "Business Agent Scheduled Meeting",
        "start": {"dateTime": "2026-01-01T15:00:00+00:00"},
        "end": {"dateTime": "2026-01-01T15:30:00+00:00"},
    }
    client = GoogleCalendarClient()
    monkeypatch.setattr(client, '_build_service', lambda: DummyService(event_payload=event_payload))
    result = client.create_event(
        title='Business Agent Scheduled Meeting',
        start_at=datetime.now(UTC),
        end_at=datetime.now(UTC) + timedelta(minutes=30),
        attendees=['a@example.com'],
    )
    assert result['status'] == 'created'


def test_retry_maps_401_to_auth_error():
    client = GoogleCalendarClient()
    response = SimpleNamespace(status=401, reason='Unauthorized')

    def bad_call():
        raise HttpError(response, b'{}')

    with pytest.raises(CalendarAuthError):
        client._with_retry(bad_call, max_retries=1)


def test_retry_maps_429_to_rate_limit_error():
    client = GoogleCalendarClient()
    response = SimpleNamespace(status=429, reason='Rate Limited')

    def bad_call():
        raise HttpError(response, b'{}')

    with pytest.raises(CalendarRateLimitError):
        client._with_retry(bad_call, max_retries=1)


def test_retry_maps_generic_exception_to_integration_error():
    client = GoogleCalendarClient()

    def bad_call():
        raise RuntimeError('boom')

    with pytest.raises(CalendarIntegrationError):
        client._with_retry(bad_call, max_retries=1)
