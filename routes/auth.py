from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from models import User, db
from routes.common import register_route


def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if (
            user
            and user.role == "admin"
            and check_password_hash(user.password, password)
        ):
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            return redirect(url_for("admin_dashboard"))
        flash("Invalid administrator email or password.", "danger")
    return render_template("auth/login.html")


def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("index"))


def register_routes(app):
    register_route(app, "/admin/login", login, methods=("GET", "POST"))
    register_route(app, "/logout", logout)
