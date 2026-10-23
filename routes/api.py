from flask import jsonify

from models import Product
from routes.common import register_route


def product_by_barcode(barcode):
    product = Product.query.filter_by(barcode=barcode).first()
    if not product:
        return jsonify({"found": False})
    return jsonify(
        {
            "found": True,
            "name": product.name,
            "brand": product.brand,
            "category": product.category,
            "manufacturer": product.manufacturer,
            "barcode": product.barcode,
        }
    )


def register(app):
    register_route(app, "/api/product/<barcode>", product_by_barcode)
