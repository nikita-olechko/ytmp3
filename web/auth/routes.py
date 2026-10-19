import hmac
import os
import time

from flask import Blueprint, redirect, render_template, request, session, url_for

auth_bp = Blueprint("auth", __name__)


def _password_matches(candidate: str) -> bool:
    return hmac.compare_digest(candidate.encode(), os.environ["APP_PASSWORD"].encode())


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if _password_matches(request.form.get("password", "")):
            session.permanent = True
            session["authed"] = True
            return redirect(url_for("convert.index"))
        time.sleep(1)
        error = "Wrong password"
    return render_template("login.html", error=error)


@auth_bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
