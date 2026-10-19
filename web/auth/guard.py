from functools import wraps

from flask import jsonify, redirect, request, session, url_for


def login_required(view):
    """Redirects pages, or returns 401 for API calls, when the session is not authenticated."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("authed"):
            return view(*args, **kwargs)
        if request.path.startswith("/api/"):
            return jsonify(error="Not logged in"), 401
        return redirect(url_for("auth.login"))
    return wrapped
