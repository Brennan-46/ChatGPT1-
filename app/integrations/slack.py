import json

import httpx

from app.core.config import settings


class SlackIntegrationError(Exception):
    pass


class SlackClient:
    def __init__(self) -> None:
        self.token = settings.slack_bot_token

    def post_message(self, channel: str, text: str) -> dict:
        if not self.token:
            return {"status": "stub", "channel": channel, "text": text}
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        payload = {"channel": channel, "text": text}
        with httpx.Client(timeout=10.0) as client:
            response = client.post("https://slack.com/api/chat.postMessage", headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            body = response.json()
            if not body.get("ok", False):
                raise SlackIntegrationError(body.get("error", "unknown_error"))
            return body
