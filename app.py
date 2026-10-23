import os

from flask import Flask
from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash

from config import Config
from models import User, db
from routes import register_routes


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    register_routes(app)
    return app


app = create_app()


def initialize_database():
    os.makedirs(os.path.join(app.root_path, "database"), exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    with app.app_context():
        db.create_all()
        verification_columns = {
            column["name"]
            for column in inspect(db.engine).get_columns("verification")
        }
        if "visitor_id" not in verification_columns:
            db.session.execute(
                text("ALTER TABLE verification ADD COLUMN visitor_id VARCHAR(32)")
            )
            db.session.commit()
        if "detected_code_type" not in verification_columns:
            db.session.execute(
                text("ALTER TABLE verification ADD COLUMN detected_code_type VARCHAR(20)")
            )
            db.session.commit()

        admin = User.query.filter_by(email="admin@example.com").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@example.com",
                password=generate_password_hash("admin123"),
                role="admin",
            )
            db.session.add(admin)
            db.session.commit()


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)
