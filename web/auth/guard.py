from functools import wraps

from flask import jsonify, redirect, request, session, url_for

from web.auth.tokens import bearer_token, token_is_valid


def session_required(view):
    """Redirects pages, or returns 401 for API calls, when the browser session is not authenticated."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("authed"):
            return view(*args, **kwargs)
        if request.path.startswith("/api/"):
            return jsonify(error="Not logged in"), 401
        return redirect(url_for("auth.login"))
    return wrapped


def login_required(view):
    """Allows an authenticated browser session or a valid API bearer token."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        token = bearer_token(request.headers.get("Authorization"))
        if token is not None:
            if token_is_valid(token):
                return view(*args, **kwargs)
            return jsonify(error="Invalid or expired token"), 401
        return session_required(view)(*args, **kwargs)
    return wrapped
