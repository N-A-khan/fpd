from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Seller(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150))
    phone = db.Column(db.String(50))
    verified = db.Column(db.Boolean, default=False)
    reports = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    brand = db.Column(db.String(100))
    category = db.Column(db.String(100))
    barcode = db.Column(db.String(2048), unique=True)
    manufacturer = db.Column(db.String(150))
    batch_format = db.Column(db.String(100))
    image = db.Column(db.String(300))
    seller_id = db.Column(db.Integer, db.ForeignKey("seller.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    seller = db.relationship("Seller", backref="products")


class Verification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    visitor_id = db.Column(db.String(32), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=True)
    image_path = db.Column(db.String(300))
    detected_barcode = db.Column(db.String(2048))
    detected_code_type = db.Column(db.String(20))
    extracted_text = db.Column(db.Text)
    image_score = db.Column(db.Float)
    logo_score = db.Column(db.Float)
    packaging_score = db.Column(db.Float)
    ocr_score = db.Column(db.Float)
    barcode_score = db.Column(db.Float)
    database_score = db.Column(db.Float)
    authenticity_score = db.Column(db.Float)
    result = db.Column(db.String(30))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref="verifications")
    product = db.relationship("Product", backref="verifications")


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    product_name = db.Column(db.String(150))
    brand = db.Column(db.String(100))
    seller_name = db.Column(db.String(150))
    reason = db.Column(db.Text)
    image = db.Column(db.String(300))
    status = db.Column(db.String(30), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref="reports")
