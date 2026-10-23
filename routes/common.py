from functools import wraps
from uuid import uuid4

from flask import current_app, flash, redirect, session, url_for

from models import User, db


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


def get_visitor_id():
    visitor_id = session.get("visitor_id")
    if not visitor_id:
        visitor_id = uuid4().hex
        session["visitor_id"] = visitor_id
    return visitor_id


def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        user = db.session.get(User, session["user_id"])
        if not user or user.role != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("dashboard"))
        return function(*args, **kwargs)

    return wrapper


def register_route(app, rule, view, methods=("GET",)):
    app.add_url_rule(
        rule,
        endpoint=view.__name__,
        view_func=view,
        methods=list(methods),
    )
