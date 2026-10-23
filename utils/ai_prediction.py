from pathlib import Path

from PIL import Image, ImageChops, ImageOps, ImageStat


REFERENCE_IMAGES = (
    Path(__file__).resolve().parent.parent / "image" / "barcode.png",
    Path(__file__).resolve().parent.parent / "image" / "shampoo.png",
)
IMAGE_SIZE = (128, 128)
MATCH_THRESHOLD = 80
MAX_MATCH_SCORE = 90


def predict_image_authenticity(image_path):
    with Image.open(image_path) as uploaded_image:
        uploaded_image = ImageOps.fit(
            uploaded_image.convert("RGB"),
            IMAGE_SIZE,
            method=Image.Resampling.LANCZOS,
        )

    image_score = 0.0
    for reference_path in REFERENCE_IMAGES:
        with Image.open(reference_path) as reference_image:
            reference_image = ImageOps.fit(
                reference_image.convert("RGB"),
                IMAGE_SIZE,
                method=Image.Resampling.LANCZOS,
            )
        channel_differences = ImageStat.Stat(
            ImageChops.difference(uploaded_image, reference_image)
        ).mean
        similarity = max(
            0.0,
            100.0 - sum(channel_differences) / len(channel_differences) / 255 * 100,
        )
        image_score = max(
            image_score,
            round(similarity * MAX_MATCH_SCORE / 100, 2),
        )

    matches_reference = image_score >= MATCH_THRESHOLD
    result = "Likely Original" if matches_reference else "Likely Fake"

    return {
        "image_score": image_score,
        "authenticity_score": image_score if matches_reference else 0.0,
        "result": result,
    }


def verify_product_code(code, product):
    matched = bool(code and product and code == product.barcode)
    result = "Likely Original" if matched else "Not Verified"

    return {
        "code_score": 100 if matched else 0,
        "database_score": 100 if matched else 0,
        "authenticity_score": 100.0 if matched else None,
        "result": result,
    }