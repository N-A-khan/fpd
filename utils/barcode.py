class BarcodeScannerUnavailableError(RuntimeError):
    pass


class InvalidCodeImageError(ValueError):
    pass


def scan_code(image_path):
    try:
        from pyzbar.pyzbar import decode
    except (ImportError, OSError) as error:
        raise BarcodeScannerUnavailableError(
            "The QR/barcode scanner is unavailable. Install the required ZBar runtime."
        ) from error

    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(image_path) as image:
            results = decode(image)
    except (OSError, UnidentifiedImageError) as error:
        raise InvalidCodeImageError(
            "The uploaded file is not a valid image."
        ) from error

    if not results:
        return None

    result = results[0]
    code_type = "QR Code" if result.type.upper() == "QRCODE" else "Barcode"
    return {
        "value": result.data.decode("utf-8", errors="replace").strip(),
        "type": code_type,
    }