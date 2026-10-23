def explain_verification(verification):
    if verification.image_score is not None and verification.image_score >= 80:
        image_finding = {
            "kind": "positive",
            "title": "Image reference matched",
            "detail": (
                f"The uploaded image matches a reference image with "
                f"{verification.image_score:.0f}% similarity."
            ),
        }
    elif verification.image_score is not None:
        image_finding = {
            "kind": "warning",
            "title": "Image reference not matched",
            "detail": (
                f"The closest reference image match is "
                f"{verification.image_score:.0f}%; at least 80% is required to match."
            ),
        }
    else:
        image_finding = {
            "kind": "info",
            "title": "Image reference not checked",
            "detail": "This scan does not have an image reference comparison result.",
        }
    return [image_finding]