from PIL import Image, ImageStat, UnidentifiedImageError


def analyze_image(image_path):
	try:
		with Image.open(image_path) as source:
			image = source.convert("RGB")
	except (OSError, UnidentifiedImageError) as error:
		raise ValueError("The uploaded file is not a valid image.") from error

	width, height = image.size
	grayscale = image.convert("L")
	contrast = ImageStat.Stat(grayscale).stddev[0]

	resolution_score = min(100, width * height / 10_000)
	contrast_score = min(100, contrast * 2)
	image_score = round(resolution_score * 0.7 + contrast_score * 0.3, 2)

	return {
		"image_score": image_score,
		"logo_score": 50,
		"packaging_score": 50,
	}
