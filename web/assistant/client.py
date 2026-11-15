"""Talks to a Claude session through claude-connector's relay API."""
import json
import os
import urllib.error
import urllib.request
from urllib.parse import quote

CONNECTOR_URL = os.environ.get("CONNECTOR_URL", "").rstrip("/")
CONNECTOR_TOKEN = os.environ.get("CONNECTOR_TOKEN", "")
PROJECT = os.environ.get("ASSISTANT_PROJECT", "lidarr")
TIMEOUT_S = 60


class AssistantError(Exception):
    pass


def enabled() -> bool:
    return bool(CONNECTOR_URL and CONNECTOR_TOKEN)


def _request(method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"{CONNECTOR_URL}{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {CONNECTOR_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "ytmp3",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        try:
            message = json.load(e).get("message")
        except ValueError:
            message = None
        raise AssistantError(message or f"Connector responded {e.code}") from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise AssistantError("The connector is unreachable") from e


def send(message: str) -> dict:
    return _request("POST", "/api/relay/message", {"project": PROJECT, "message": message})


def conversation() -> dict:
    return _request("GET", f"/api/relay/conversation?project={quote(PROJECT)}")
