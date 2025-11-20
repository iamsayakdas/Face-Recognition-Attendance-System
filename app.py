from flask import (
    Flask, render_template, redirect, url_for,
    request, flash, send_file, make_response
)
import pandas as pd
from datetime import datetime, timedelta
import jwt
import secrets

import db

# Initialize DB (creates tables & default admin if needed)
db.init_db()

app = Flask(__name__)
app.secret_key = "CHANGE_THIS_SECRET_KEY_FOR_PRODUCTION"
JWT_SECRET = app.secret_key
JWT_ALGO = "HS256"


# ========== Helper functions ==========

def create_jwt_for_admin(admin_id):
    payload = {
        "admin_id": admin_id,
        "exp": datetime.utcnow() + timedelta(hours=6)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    # PyJWT returns str in v2+
    return token


def get_current_admin():
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

    admin = db.get_admin_by_id(data.get("admin_id"))
    return admin


def login_required():
    admin = get_current_admin()
    if not admin:
        return None
    return admin


@app.context_processor
def inject_current_admin():
    return {"current_admin": get_current_admin()}


# ========== Routes ==========

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        admin_row = db.get_admin_by_username(username)
        if admin_row and db.verify_admin_password(admin_row, password):
            token = create_jwt_for_admin(admin_row["id"])
            resp = make_response(redirect(url_for("dashboard")))
            resp.set_cookie(
                "access_token",
                token,
                httponly=True,
                samesite="Lax",
                max_age=6 * 60 * 60,
            )
            return resp
        else:
            flash("Invalid username or password")

    return render_template("login.html")


@app.route("/logout")
def logout():
    resp = make_response(redirect(url_for("login")))
    resp.set_cookie("access_token", "", expires=0)
    return resp


@app.route("/dashboard")
def dashboard():
    admin = login_required()
    if not admin:
        return redirect(url_for("login"))

    all_att = db.get_attendance_joined()

    stats = {
        "students": len(db.get_all_students()),
        "records": len(all_att),
        "today": sum(1 for r in all_att if r[0] == datetime.now().strftime("%Y-%m-%d")),
    }

    return render_template("dashboard.html", stats=stats, recent=all_att[:10])


@app.route("/students")
def students():
    admin = login_required()
    if not admin:
        return redirect(url_for("login"))

    return render_template("students.html", students=db.get_all_students())


@app.route("/attendance")
def attendance():
    admin = login_required()
    if not admin:
        return redirect(url_for("login"))

    return render_template("attendance.html", attendance=db.get_attendance_joined())


@app.route("/export_excel")
def export_excel():
    admin = login_required()
    if not admin:
        return redirect(url_for("login"))

    rows = db.get_attendance_joined()
    df = pd.DataFrame(
        rows,
        columns=[
            "Date",
            "Time",
            "Roll",
            "Name",
            "Phone",
            "Email",
            "Status",
        ],
    )
    df.to_excel("attendance_web.xlsx", index=False)
    return send_file("attendance_web.xlsx", as_attachment=True)


# ===== Admin management (multiple admin accounts) =====

@app.route("/admins")
def admins():
    admin = login_required()
    if not admin:
        return redirect(url_for("login"))

    admins_list = db.list_admins()
    return render_template("admins.html", admins=admins_list)


@app.route("/admins/new", methods=["GET", "POST"])
def admins_new():
    admin = login_required()
    if not admin:
        return redirect(url_for("login"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Username and password are required")
        else:
            db.create_admin(username, email, password)
            flash("New admin created")
            return redirect(url_for("admins"))

    return render_template("admin_new.html")


# ========== Forgot Password & Reset ==========

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        admin_row = db.get_admin_by_username(username)
        if not admin_row:
            flash("No admin found with that username")
        else:
            # Generate reset token
            token = secrets.token_urlsafe(32)
            expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()

            db.set_admin_reset_token(admin_row["id"], token, expires_at)

            reset_link = url_for("reset_password", token=token, _external=True)

            # In real app, send by email. For demo, show it on page
            flash("Password reset link (demo):")
            flash(reset_link)

    return render_template("forgot_password.html")


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    admin_row = db.get_admin_by_reset_token(token)
    if not admin_row:
        flash("Invalid or expired reset token")
        return redirect(url_for("login"))

    # Check expiry
    expires = admin_row["reset_token_expires_at"]
    if expires:
        try:
            exp_dt = datetime.fromisoformat(expires)
            if datetime.utcnow() > exp_dt:
                flash("Reset token has expired")
                return redirect(url_for("login"))
        except ValueError:
            flash("Invalid reset token data")
            return redirect(url_for("login"))

    if request.method == "POST":
        pwd = request.form.get("password", "").strip()
        confirm = request.form.get("confirm", "").strip()
        if not pwd or not confirm:
            flash("Both password fields are required")
        elif pwd != confirm:
            flash("Passwords do not match")
        else:
            db.set_admin_password(admin_row["id"], pwd)
            flash("Password reset successfully. Please log in.")
            return redirect(url_for("login"))

    return render_template("reset_password.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
