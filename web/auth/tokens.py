import time

from flask import current_app
from itsdangerous import BadSignature, URLSafeSerializer

SALT = "api-token"
TTL_HOURS = (1, 24, 168)


def _serializer() -> URLSafeSerializer:
    return URLSafeSerializer(current_app.secret_key, salt=SALT)


def issue_token(hours: int) -> tuple[str, int]:
    """Returns a signed API token and its expiry (unix seconds)."""
    if hours not in TTL_HOURS:
        hours = 24
    expires_at = int(time.time()) + hours * 3600
    return _serializer().dumps({"exp": expires_at}), expires_at


def token_is_valid(token: str) -> bool:
    try:
        payload = _serializer().loads(token)
    except BadSignature:
        return False
    return isinstance(payload, dict) and payload.get("exp", 0) > time.time()


def bearer_token(auth_header: str | None) -> str | None:
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return None
