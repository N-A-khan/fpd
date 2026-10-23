from flask import render_template, session

from models import Verification
from routes.common import get_visitor_id, register_route


def index():
    user_id = session.get("user_id")
    owner = {"user_id": user_id} if user_id else {
        "visitor_id": get_visitor_id()
    }
    total = Verification.query.filter_by(**owner).count()
    genuine = Verification.query.filter_by(
        **owner, result="Likely Original"
    ).count()
    fake = Verification.query.filter_by(
        **owner, result="Likely Fake"
    ).count()
    suspicious = Verification.query.filter_by(
        **owner, result="Suspicious"
    ).count()
    not_verified = Verification.query.filter_by(
        **owner, result="Not Verified"
    ).count()
    return render_template(
        "index.html",
        total=total,
        genuine=genuine,
        fake=fake,
        suspicious=suspicious,
        not_verified=not_verified,
    )


def about():
    return render_template("about.html")


def register(app):
    register_route(app, "/", index)
    register_route(app, "/about", about)
