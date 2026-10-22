import os

from flask import Flask

from web.auth.routes import auth_bp
from web.routes.convert import convert_bp
from web.routes.search import search_bp
from web.routes.tokens import tokens_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ["SECRET_KEY"]
    app.config.update(
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "1") == "1",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 30,
    )
    app.register_blueprint(auth_bp)
    app.register_blueprint(convert_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(tokens_bp)
    return app
