import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PIL import Image

from app import create_app
from models import Product, Verification, db
from utils.ai_prediction import REFERENCE_IMAGES


class ProductScanRouteTests(unittest.TestCase):
    def setUp(self):
        self.upload_folder = TemporaryDirectory()
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "UPLOAD_FOLDER": self.upload_folder.name,
        })
        with self.app.app_context():
            db.create_all()
            db.session.add(
                Product(
                    name="Acme Soap",
                    brand="Acme",
                    barcode="https://example.test/acme-soap",
                )
            )
            db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()
        self.upload_folder.cleanup()

    def scan_and_get_result(self, scanned_code, filename, image_bytes=None):
        image_file = BytesIO(image_bytes) if image_bytes else BytesIO()
        if image_bytes is None:
            Image.new("RGB", (20, 20), "white").save(image_file, format="PNG")
        image_file.seek(0)

        with patch("utils.barcode.scan_code", return_value=scanned_code):
            response = self.client.post(
                "/scan",
                data={"product_image": (image_file, filename)},
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            verification = Verification.query.order_by(Verification.id.desc()).first()
            result_url = f"/result/{verification.id}"

        result_response = self.client.get(result_url)
        self.assertEqual(result_response.status_code, 200)
        self.assertNotIn(b"Photo quality", result_response.data)
        self.assertNotIn(b"Package text match", result_response.data)
        return verification, result_response

    def test_qr_scan_checks_only_the_qr_code(self):
        verification, result_response = self.scan_and_get_result(
            {
                "value": "https://example.test/acme-soap",
                "type": "QR Code",
            },
            "qr-product.png",
        )

        self.assertEqual(verification.detected_code_type, "QR Code")
        self.assertEqual(verification.result, "Likely Fake")
        self.assertEqual(verification.barcode_score, 100)
        self.assertEqual(verification.authenticity_score, 0)
        self.assertLess(verification.image_score, 80)
        self.assertIsNone(verification.ocr_score)
        self.assertIn(b"Likely Fake", result_response.data)
        self.assertNotIn(b"catalog match", result_response.data)
        self.assertIn(b"Image check", result_response.data)

    def test_unregistered_qr_image_is_fake_with_zero_catalog_match(self):
        verification, result_response = self.scan_and_get_result(
            {
                "value": "https://example.test/unregistered",
                "type": "QR Code",
            },
            "unknown-qr.png",
        )

        self.assertEqual(verification.result, "Likely Fake")
        self.assertEqual(verification.authenticity_score, 0)
        self.assertIn(b"Likely Fake", result_response.data)
        self.assertIn(b"0%", result_response.data)

    def test_barcode_scan_checks_only_the_barcode(self):
        with self.app.app_context():
            db.session.add(
                Product(name="Acme Drink", barcode="5449000000996")
            )
            db.session.commit()

        verification, result_response = self.scan_and_get_result(
            {
                "value": "5449000000996",
                "type": "Barcode",
            },
            "barcode-product.png",
        )

        self.assertEqual(verification.detected_code_type, "Barcode")
        self.assertEqual(verification.result, "Likely Fake")
        self.assertEqual(verification.barcode_score, 100)
        self.assertEqual(verification.authenticity_score, 0)
        self.assertLess(verification.image_score, 80)
        self.assertNotIn(b"catalog match", result_response.data)

    def test_unmatched_image_without_catalog_code_is_fake(self):
        verification, result_response = self.scan_and_get_result(
            None,
            "product-without-code.png",
        )

        self.assertEqual(verification.result, "Likely Fake")
        self.assertEqual(verification.authenticity_score, 0)
        self.assertIn(b"Image reference not matched", result_response.data)

    def test_each_reference_image_is_detected_as_real_when_uploaded(self):
        for reference_path in REFERENCE_IMAGES:
            with self.subTest(image=reference_path.name):
                reference_bytes = Path(reference_path).read_bytes()
                verification, result_response = self.scan_and_get_result(
                    None,
                    f"renamed-{reference_path.name}",
                    image_bytes=reference_bytes,
                )

                self.assertEqual(verification.result, "Likely Original")
                self.assertGreaterEqual(verification.image_score, 80)
                self.assertLessEqual(verification.image_score, 90)
                self.assertEqual(
                    verification.authenticity_score,
                    verification.image_score,
                )
                self.assertIn(b"Likely Real", result_response.data)
                self.assertIn(b"Reference image recognized", result_response.data)
                self.assertIn(b"Image reference matched", result_response.data)
                self.assertIn(b"Image reference similarity", result_response.data)

    def test_unregistered_barcode_image_is_fake_with_zero_catalog_match(self):
        verification, result_response = self.scan_and_get_result(
            {
                "value": "4006381333931",
                "type": "Barcode",
            },
            "unregistered-barcode.png",
        )

        self.assertEqual(verification.result, "Likely Fake")
        self.assertEqual(verification.barcode_score, 0)
        self.assertEqual(verification.authenticity_score, 0)
        self.assertIn(b"0%", result_response.data)


if __name__ == "__main__":
    unittest.main()
