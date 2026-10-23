import os
from datetime import datetime

from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from models import Product, Report, Verification, db
from routes.common import allowed_file, get_visitor_id, register_route


def dashboard():
    user_id = session.get("user_id")
    owner = {"user_id": user_id} if user_id else {
        "visitor_id": get_visitor_id()
    }
    total = Verification.query.filter_by(**owner).count()
    genuine = Verification.query.filter_by(
        **owner, result="Likely Original"
    ).count()
    fake = Verification.query.filter_by(
        **owner, result="Likely Fake"
    ).count()
    suspicious = Verification.query.filter_by(
        **owner, result="Suspicious"
    ).count()
    not_verified = Verification.query.filter_by(
        **owner, result="Not Verified"
    ).count()
    recent = Verification.query.filter_by(**owner).order_by(
        Verification.created_at.desc()
    ).limit(5).all()
    return render_template(
        "user/dashboard.html",
        total=total,
        genuine=genuine,
        fake=fake,
        suspicious=suspicious,
        not_verified=not_verified,
        recent=recent,
    )


def scan():
    visitor_id = get_visitor_id()
    if request.method == "POST":
        from utils.ai_prediction import (
            predict_image_authenticity,
            verify_product_code,
        )
        from utils.barcode import (
            InvalidCodeImageError,
            BarcodeScannerUnavailableError,
            scan_code,
        )

        file = request.files.get("product_image")
        if not file or file.filename == "":
            flash("Please select a product image.", "danger")
            return redirect(url_for("scan"))
        if not allowed_file(file.filename):
            flash("Invalid image format.", "danger")
            return redirect(url_for("scan"))

        filename = secure_filename(file.filename)
        unique_name = datetime.utcnow().strftime("%Y%m%d%H%M%S") + "_" + filename
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, unique_name)
        file.save(filepath)

        try:
            code = scan_code(filepath)
        except (BarcodeScannerUnavailableError, InvalidCodeImageError) as error:
            os.remove(filepath)
            flash(str(error), "danger")
            return redirect(url_for("scan"))

        code_value = code["value"] if code else None
        code_type = code["type"] if code else None
        product = (
            Product.query.filter_by(barcode=code_value).first()
            if code_value
            else None
        )
        prediction = predict_image_authenticity(filepath)
        code_scores = verify_product_code(code_value, product)
        verification = Verification(
            user_id=session.get("user_id"),
            visitor_id=visitor_id,
            product_id=product.id if product else None,
            image_path="uploads/" + unique_name,
            detected_barcode=code_value,
            detected_code_type=code_type,
            image_score=prediction["image_score"],
            barcode_score=code_scores["code_score"] if code else None,
            database_score=code_scores["database_score"],
            authenticity_score=prediction["authenticity_score"],
            result=prediction["result"],
        )
        db.session.add(verification)
        db.session.commit()
        return redirect(url_for("result", verification_id=verification.id))
    return render_template("user/scan.html")


def result(verification_id):
    verification = db.session.get(Verification, verification_id)
    if not verification:
        flash("Verification not found.", "danger")
        return redirect(url_for("dashboard"))
    is_admin = session.get("role") == "admin"
    if verification.user_id is not None:
        owns_result = verification.user_id == session.get("user_id")
    else:
        owns_result = verification.visitor_id == get_visitor_id()
    if not owns_result and not is_admin:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("dashboard"))
    from utils.result import explain_verification

    return render_template(
        "user/result.html",
        verification=verification,
        findings=explain_verification(verification),
    )


def history():
    user_id = session.get("user_id")
    owner = {"user_id": user_id} if user_id else {
        "visitor_id": get_visitor_id()
    }
    records = Verification.query.filter_by(**owner).order_by(
        Verification.created_at.desc()
    ).all()
    return render_template("user/history.html", records=records)


def delete_history_record(verification_id):
    user_id = session.get("user_id")
    owner = {"user_id": user_id} if user_id else {
        "visitor_id": get_visitor_id()
    }
    verification = Verification.query.filter_by(
        id=verification_id, **owner
    ).first()
    if not verification:
        flash("History record not found.", "danger")
        return redirect(url_for("history"))

    image_path = verification.image_path
    db.session.delete(verification)
    db.session.commit()

    if image_path:
        normalized_path = image_path.replace("\\", "/")
        image_name = (
            normalized_path[len("uploads/"):]
            if normalized_path.startswith("uploads/")
            else ""
        )
        if (
            image_name
            and "/" not in image_name
        ):
            filepath = os.path.join(
                current_app.config["UPLOAD_FOLDER"], image_name
            )
            if os.path.isfile(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    current_app.logger.exception(
                        "Could not remove uploaded image %s", filepath
                    )
                    flash(
                        "History record deleted, but its uploaded image could not be removed.",
                        "warning",
                    )
                    return redirect(url_for("history"))

    flash("History record deleted.", "success")
    return redirect(url_for("history"))


def report():
    if request.method == "POST":
        report = Report(
            user_id=session.get("user_id"),
            product_name=request.form.get("product_name"),
            brand=request.form.get("brand"),
            seller_name=request.form.get("seller_name"),
            reason=request.form.get("reason"),
        )
        db.session.add(report)
        db.session.commit()
        flash("Fake product report submitted.", "success")
        return redirect(url_for("dashboard"))
    return render_template("user/report.html")


def register_routes(app):
    register_route(app, "/dashboard", dashboard)
    register_route(app, "/scan", scan, methods=("GET", "POST"))
    register_route(app, "/result/<int:verification_id>", result)
    register_route(app, "/history", history)
    register_route(
        app,
        "/history/delete/<int:verification_id>",
        delete_history_record,
        methods=("POST",),
    )
    register_route(app, "/report", report, methods=("GET", "POST"))
