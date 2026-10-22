from flask import Blueprint, jsonify, request

from web.auth.guard import session_required
from web.auth.tokens import issue_token

tokens_bp = Blueprint("tokens", __name__)


@tokens_bp.post("/api/tokens")
@session_required
def create_token():
    body = request.get_json(silent=True) or {}
    token, expires_at = issue_token(int(body.get("hours", 24)))
    return jsonify(token=token, expires_at=expires_at)
