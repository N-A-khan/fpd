import os
import unittest
from tempfile import TemporaryDirectory

from app import create_app
from models import Verification, db


class VerificationHistoryRouteTests(unittest.TestCase):
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

    def create_visitor_verification(self, visitor_id, image_path=None):
        with self.app.app_context():
            verification = Verification(
                visitor_id=visitor_id,
                image_path=image_path,
                result="Not Verified",
            )
            db.session.add(verification)
            db.session.commit()
            return verification.id

    def test_owner_can_delete_history_record_and_uploaded_image(self):
        self.client.get("/history")
        with self.client.session_transaction() as browser_session:
            visitor_id = browser_session["visitor_id"]

        image_name = "uploaded-product.png"
        image_file = os.path.join(self.upload_folder.name, image_name)
        with open(image_file, "wb") as uploaded_image:
            uploaded_image.write(b"image")
        verification_id = self.create_visitor_verification(
            visitor_id, f"uploads/{image_name}"
        )

        response = self.client.post(
            f"/history/delete/{verification_id}",
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"History record deleted.", response.data)
        self.assertFalse(os.path.exists(image_file))
        with self.app.app_context():
            self.assertIsNone(db.session.get(Verification, verification_id))

    def test_visitor_cannot_delete_another_visitors_history(self):
        self.client.get("/history")
        with self.client.session_transaction() as browser_session:
            visitor_id = browser_session["visitor_id"]
        verification_id = self.create_visitor_verification("another-visitor")

        response = self.client.post(
            f"/history/delete/{verification_id}",
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"History record not found.", response.data)
        with self.app.app_context():
            self.assertIsNotNone(db.session.get(Verification, verification_id))

    def test_history_displays_delete_button(self):
        self.client.get("/history")
        with self.client.session_transaction() as browser_session:
            visitor_id = browser_session["visitor_id"]
        self.create_visitor_verification(visitor_id)

        response = self.client.get("/history")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Delete", response.data)


if __name__ == "__main__":
    unittest.main()
