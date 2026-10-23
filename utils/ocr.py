from PIL import Image, UnidentifiedImageError
import pytesseract


def extract_text(image_path):
	try:
		with Image.open(image_path) as image:
			return pytesseract.image_to_string(image).strip()
	except pytesseract.TesseractNotFoundError:
		return ""
	except (OSError, UnidentifiedImageError, pytesseract.TesseractError):
		return ""
