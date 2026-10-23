import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from PIL import Image

from utils.ai_prediction import REFERENCE_IMAGES, predict_image_authenticity, verify_product_code


class ProductCodeVerificationTests(unittest.TestCase):
    def test_registered_barcode_is_verified_using_code_only(self):
        product = SimpleNamespace(barcode="123456789")

        result = verify_product_code("123456789", product)

        self.assertEqual(result["result"], "Likely Original")
        self.assertEqual(result["code_score"], 100)
        self.assertEqual(result["authenticity_score"], 100)

    def test_registered_qr_value_is_verified_using_code_only(self):
        product = SimpleNamespace(barcode="https://example.test/product/123")

        result = verify_product_code(
            "https://example.test/product/123",
            product,
        )

        self.assertEqual(result["result"], "Likely Original")
        self.assertEqual(result["code_score"], 100)
        self.assertEqual(result["authenticity_score"], 100)

    def test_unregistered_qr_stays_unverified_with_zero_catalog_match(self):
        result = verify_product_code(
            "https://example.test/unregistered",
            None,
        )

        self.assertEqual(result["result"], "Not Verified")
        self.assertEqual(result["code_score"], 0)
        self.assertIsNone(result["authenticity_score"])

    def test_unknown_code_is_not_called_fake(self):
        result = verify_product_code("not-registered", None)

        self.assertEqual(result["result"], "Not Verified")
        self.assertEqual(result["code_score"], 0)
        self.assertIsNone(result["authenticity_score"])

    def test_empty_code_is_not_verified(self):
        result = verify_product_code(None, None)

        self.assertEqual(result["result"], "Not Verified")
        self.assertEqual(result["code_score"], 0)


class ProductImagePredictionTests(unittest.TestCase):
    def test_reference_images_match_from_a_different_path(self):
        for reference_path in REFERENCE_IMAGES:
            with self.subTest(image=reference_path.name):
                with TemporaryDirectory() as temporary_directory:
                    copied_path = Path(temporary_directory) / "renamed.png"
                    copied_path.write_bytes(reference_path.read_bytes())

                    prediction = predict_image_authenticity(copied_path)

                self.assertEqual(prediction["result"], "Likely Original")
                self.assertGreaterEqual(prediction["image_score"], 80)
                self.assertLessEqual(prediction["image_score"], 90)
                self.assertEqual(
                    prediction["authenticity_score"],
                    prediction["image_score"],
                )

    def test_resized_jpeg_copy_matches_reference(self):
        with TemporaryDirectory() as temporary_directory:
            image_path = Path(temporary_directory) / "resized-reference.jpg"
            with Image.open(REFERENCE_IMAGES[1]) as reference:
                reference.resize((144, 147)).convert("RGB").save(
                    image_path,
                    format="JPEG",
                    quality=85,
                )

            prediction = predict_image_authenticity(image_path)

        self.assertEqual(prediction["result"], "Likely Original")
        self.assertGreaterEqual(prediction["image_score"], 80)
        self.assertLessEqual(prediction["image_score"], 90)

    def test_unregistered_image_is_labeled_fake(self):
        with TemporaryDirectory() as temporary_directory:
            image_path = Path(temporary_directory) / "other.png"
            Image.new("RGB", (10, 10), "white").save(image_path)

            prediction = predict_image_authenticity(image_path)

        self.assertEqual(prediction["result"], "Likely Fake")
        self.assertLess(prediction["image_score"], 80)
        self.assertEqual(prediction["authenticity_score"], 0)


if __name__ == "__main__":
    unittest.main()
