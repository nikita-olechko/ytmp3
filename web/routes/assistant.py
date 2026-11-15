from flask import Blueprint, jsonify, request

from web.assistant.client import AssistantError, conversation, enabled, send
from web.auth.guard import session_required

assistant_bp = Blueprint("assistant", __name__)


def _relay(call):
    if not enabled():
        return jsonify(error="The assistant is not configured"), 404
    try:
        return jsonify(call())
    except AssistantError as e:
        return jsonify(error=str(e)), 502


@assistant_bp.get("/api/assistant/conversation")
@session_required
def get_conversation():
    return _relay(conversation)


@assistant_bp.post("/api/assistant/message")
@session_required
def post_message():
    message = ((request.get_json(silent=True) or {}).get("message") or "").strip()
    if not message:
        return jsonify(error="Write a message"), 400
    return _relay(lambda: send(message))
