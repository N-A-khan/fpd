from flask import flash, redirect, render_template, request, url_for

from models import Product, Report, Seller, User, Verification, db
from routes.common import admin_required, register_route


@admin_required
def admin_dashboard():
    total = Verification.query.count()
    genuine = Verification.query.filter_by(result="Likely Original").count()
    fake = Verification.query.filter_by(result="Likely Fake").count()
    suspicious = Verification.query.filter_by(result="Suspicious").count()
    not_verified = Verification.query.filter_by(result="Not Verified").count()
    users = User.query.count()
    products = Product.query.count()
    reports = Report.query.filter_by(status="Pending").count()
    return render_template(
        "admin/dashboard.html",
        total=total,
        genuine=genuine,
        fake=fake,
        suspicious=suspicious,
        not_verified=not_verified,
        users=users,
        products=products,
        reports=reports,
    )


@admin_required
def admin_products():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("admin/products.html", products=products)


@admin_required
def add_product():
    sellers = Seller.query.all()
    if request.method == "POST":
        barcode = request.form.get("barcode", "").strip()
        existing = Product.query.filter_by(barcode=barcode).first()
        if existing:
            flash("Barcode already exists.", "danger")
            return redirect(url_for("add_product"))

        product = Product(
            name=request.form.get("name"),
            brand=request.form.get("brand"),
            category=request.form.get("category"),
            barcode=barcode,
            manufacturer=request.form.get("manufacturer"),
            batch_format=request.form.get("batch_format"),
            seller_id=request.form.get("seller_id") or None,
        )
        db.session.add(product)
        db.session.commit()
        flash("Product added successfully.", "success")
        return redirect(url_for("admin_products"))
    return render_template(
        "admin/add.product.html",
        sellers=sellers,
        barcode=request.args.get("barcode", ""),
    )


@admin_required
def edit_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("admin_products"))

    sellers = Seller.query.all()
    if request.method == "POST":
        product.name = request.form.get("name")
        product.brand = request.form.get("brand")
        product.category = request.form.get("category")
        product.barcode = request.form.get("barcode", "").strip()
        product.manufacturer = request.form.get("manufacturer")
        product.batch_format = request.form.get("batch_format")
        product.seller_id = request.form.get("seller_id") or None
        db.session.commit()
        flash("Product updated.", "success")
        return redirect(url_for("admin_products"))

    return render_template(
        "admin/edit_product.html", product=product, sellers=sellers
    )


@admin_required
def delete_product(product_id):
    product = db.session.get(Product, product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        flash("Product deleted.", "success")
    return redirect(url_for("admin_products"))


@admin_required
def sellers():
    seller_list = Seller.query.order_by(Seller.created_at.desc()).all()
    return render_template("admin/sellers.html", sellers=seller_list)


@admin_required
def add_seller():
    if request.method == "POST":
        seller = Seller(
            name=request.form.get("name"),
            email=request.form.get("email"),
            phone=request.form.get("phone"),
            verified=request.form.get("verified") == "on",
        )
        db.session.add(seller)
        db.session.commit()
        flash("Seller added.", "success")
        return redirect(url_for("sellers"))
    return render_template("admin/add_seller.html")


@admin_required
def toggle_seller(seller_id):
    seller = db.session.get(Seller, seller_id)
    if seller:
        seller.verified = not seller.verified
        db.session.commit()
    return redirect(url_for("sellers"))


@admin_required
def admin_reports():
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template("admin/reports.html", reports=reports)


@admin_required
def update_report(report_id, status):
    report = db.session.get(Report, report_id)
    if report:
        if status not in ["Pending", "Investigating", "Resolved", "Rejected"]:
            flash("Invalid report status.", "danger")
            return redirect(url_for("admin_reports"))
        report.status = status
        db.session.commit()
    return redirect(url_for("admin_reports"))


@admin_required
def analytics():
    records = Verification.query.all()
    total = len(records)
    genuine = sum(1 for record in records if record.result == "Likely Original")
    fake = sum(1 for record in records if record.result == "Likely Fake")
    suspicious = sum(1 for record in records if record.result == "Suspicious")
    not_verified = sum(1 for record in records if record.result == "Not Verified")

    if total:
        genuine_percent = round(genuine / total * 100, 2)
        fake_percent = round(fake / total * 100, 2)
        suspicious_percent = round(suspicious / total * 100, 2)
        scored_records = [
            record.authenticity_score
            for record in records
            if record.authenticity_score is not None
        ]
        average_score = (
            round(sum(scored_records) / len(scored_records), 2)
            if scored_records
            else 0
        )
    else:
        genuine_percent = 0
        fake_percent = 0
        suspicious_percent = 0
        average_score = 0

    not_verified_percent = round(not_verified / total * 100, 2) if total else 0

    categories = {}
    for verification in records:
        if verification.product:
            category = verification.product.category or "Unknown"
            if category not in categories:
                categories[category] = {"genuine": 0, "fake": 0, "suspicious": 0}
            if verification.result == "Likely Original":
                categories[category]["genuine"] += 1
            elif verification.result == "Likely Fake":
                categories[category]["fake"] += 1
            elif verification.result == "Suspicious":
                categories[category]["suspicious"] += 1

    return render_template(
        "admin/analytics.html",
        total=total,
        genuine=genuine,
        fake=fake,
        suspicious=suspicious,
        not_verified=not_verified,
        genuine_percent=genuine_percent,
        fake_percent=fake_percent,
        suspicious_percent=suspicious_percent,
        not_verified_percent=not_verified_percent,
        average_score=average_score,
        categories=categories,
    )


def register_routes(app):
    register_route(app, "/admin", admin_dashboard)
    register_route(app, "/admin/products", admin_products)
    register_route(app, "/admin/products/add", add_product, methods=("GET", "POST"))
    register_route(
        app,
        "/admin/products/edit/<int:product_id>",
        edit_product,
        methods=("GET", "POST"),
    )
    register_route(app, "/admin/products/delete/<int:product_id>", delete_product)
    register_route(app, "/admin/sellers", sellers)
    register_route(app, "/admin/sellers/add", add_seller, methods=("GET", "POST"))
    register_route(app, "/admin/sellers/toggle/<int:seller_id>", toggle_seller)
    register_route(app, "/admin/reports", admin_reports)
    register_route(app, "/admin/reports/<int:report_id>/<status>", update_report)
    register_route(app, "/admin/analytics", analytics)
