from flask import Blueprint, jsonify, request

from web.auth.guard import login_required
from web.converter.youtube import ConversionError, to_mp3
from web.library.store import LibraryError, enabled, save

library_bp = Blueprint("library", __name__)


@library_bp.post("/api/library")
@login_required
def add_to_library():
    if not enabled():
        return jsonify(error="Saving to the library is not configured"), 404
    body = request.get_json(silent=True) or {}
    try:
        result = to_mp3(body.get("url", "").strip(), str(body.get("quality", "192")), embed_metadata=True)
    except ConversionError as e:
        return jsonify(error=str(e)), 400
    try:
        name = save(result.path, result.label)
    except LibraryError as e:
        return jsonify(error=str(e)), 500
    finally:
        result.cleanup()
    return jsonify(saved=name)
