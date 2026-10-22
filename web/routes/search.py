from flask import Blueprint, jsonify, request

from web.auth.guard import login_required
from web.search.youtube import SearchError, search

search_bp = Blueprint("search", __name__)


@search_bp.get("/api/search")
@login_required
def search_videos():
    try:
        results = search(request.args.get("q", ""), request.args.get("limit", 10, type=int))
    except SearchError as e:
        return jsonify(error=str(e)), 400
    return jsonify(results=results)
