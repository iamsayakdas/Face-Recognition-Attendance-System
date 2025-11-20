from flask import Flask, render_template, redirect, url_for, request, flash, send_file
import pandas as pd
from datetime import datetime

import db   # <-- import database module
db.init_db()  # <-- IMPORTANT: create DB tables on Render startup

app = Flask(__name__)
app.secret_key = "YOUR_SECRET_KEY"

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"


def check_login(req):
    return req.cookies.get("logged") == "1"


@app.route("/")
def home():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        if u == ADMIN_USER and p == ADMIN_PASS:
            resp = redirect("/dashboard")
            resp.set_cookie("logged", "1")
            return resp
        else:
            flash("Invalid username or password")

    return render_template("login.html")


@app.route("/logout")
def logout():
    resp = redirect("/login")
    resp.set_cookie("logged", "", expires=0)
    return resp


@app.route("/dashboard")
def dashboard():
    if not check_login(request):
        return redirect("/login")

    all_att = db.get_attendance_joined()

    stats = {
        "students": len(db.get_all_students()),
        "records": len(all_att),
        "today": sum(1 for r in all_att if r[0] == datetime.now().strftime("%Y-%m-%d"))
    }

    return render_template("dashboard.html",
                           stats=stats,
                           recent=all_att[:10])


@app.route("/students")
def students():
    if not check_login(request):
        return redirect("/login")

    return render_template("students.html",
                           students=db.get_all_students())


@app.route("/attendance")
def attendance():
    if not check_login(request):
        return redirect("/login")

    return render_template("attendance.html",
                           attendance=db.get_attendance_joined())


@app.route("/export_excel")
def export_excel():
    rows = db.get_attendance_joined()

    df = pd.DataFrame(rows,
                      columns=["Date", "Time", "Roll", "Name", "Phone", "Email", "Status"])

    df.to_excel("attendance_web.xlsx", index=False)
    return send_file("attendance_web.xlsx", as_attachment=True)


# Render DOES NOT run app.run(), so this block is only local use
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
