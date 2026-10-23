import unittest
from tempfile import TemporaryDirectory

from app import create_app
from models import Verification, db


class HomeRouteTests(unittest.TestCase):
    def setUp(self):
        self.upload_folder = TemporaryDirectory()
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "UPLOAD_FOLDER": self.upload_folder.name,
        })
        with self.app.app_context():
            db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()
        self.upload_folder.cleanup()

    def test_home_counters_start_at_zero_for_new_visitor(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<h3>0</h3>", response.data)

    def test_home_counters_only_include_current_visitors_history(self):
        self.client.get("/")
        with self.client.session_transaction() as browser_session:
            visitor_id = browser_session["visitor_id"]

        with self.app.app_context():
            db.session.add_all([
                Verification(visitor_id=visitor_id, result="Likely Original"),
                Verification(visitor_id=visitor_id, result="Likely Fake"),
                Verification(visitor_id="another-visitor", result="Likely Original"),
            ])
            db.session.commit()

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<h3>2</h3>", response.data)
        self.assertIn(b"<h3>1</h3>", response.data)
        self.assertEqual(response.data.count(b"<h3>1</h3>"), 2)


if __name__ == "__main__":
    unittest.main()
