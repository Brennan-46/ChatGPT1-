from pydantic import BaseModel, Field

from app.integrations.slack import SlackClient, SlackIntegrationError


class CommsInput(BaseModel):
    request: str = Field(min_length=1)
    channel: str = Field(default="#general")


slack_client = SlackClient()


def handle_comms(payload: dict) -> str:
    data = CommsInput(**payload)
    try:
        result = slack_client.post_message(channel=data.channel, text=data.request)
        return f"Slack message status: {result.get('status', 'sent')}"
    except SlackIntegrationError as exc:
        return f"Slack integration error: {exc}"
