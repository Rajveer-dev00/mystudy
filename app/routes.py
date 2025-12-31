from flask import Blueprint, render_template, request, redirect, url_for, session
from .db import get_db
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
import matplotlib.pyplot as plt
import os


main = Blueprint("main", __name__)

# ---------------- REGISTER ----------------
@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user (name, email, username, password) VALUES (%s,%s,%s,%s)",
            (name, email, username, password)
        )
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("main.login"))

    return render_template("register.html")


# ---------------- LOGIN ----------------
@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM user WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user"] = user["username"]
            return redirect(url_for("main.home"))

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@main.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("main.login"))


# ---------------- HOME / DASHBOARD ----------------
@main.route("/", methods=["GET", "POST"])
def home():
    if "user" not in session:
        return redirect(url_for("main.login"))

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        date = request.form["date"]
        subject = request.form["subject"]
        hours = request.form["hours"]

        cur.execute(
            "INSERT INTO study_log (date, subject, study_hours) VALUES (%s,%s,%s)",
            (date, subject, hours)
        )
        conn.commit()

    # ---- SELECT ----
    cur.execute("SELECT id, date, subject, study_hours FROM study_log ORDER BY date DESC")
    rows = cur.fetchall()

    # ---- PANDAS ANALYTICS ----
    total_hours = 0
    subject_summary = []

    if rows:
        df = pd.DataFrame(rows)
        total_hours = int(df["study_hours"].sum())

        subject_summary = (
            df.groupby("subject")["study_hours"]
            .sum()
            .reset_index()
            .to_dict(orient="records")
        )
        #-----matplotlib chart----------
        subjects=df.groupby("subject")["study_hours"].sum().index.tolist()
        hours_list=df.groupby("subject")["study_hours"].sum().values.tolist()
        
        os.makedirs("static",exist_ok=True)
        plt.figure(figsize=(6,4))
        plt.bar(subjects,hours_list)
        plt.xlabel("Subjects")
        plt.ylabel("Study.hours")
        plt.title("Subject-wise Study Hours")
        plt.tight_layout()
        plt.savefig("static/study_chart.png")
        plt.close()

    cur.close()
    conn.close()

    return render_template(
        "index.html",
        logs=rows,
        total_hours=total_hours,
        subject_summary=subject_summary
    )


# ---------------- DELETE ----------------
@main.route("/delete/<int:id>")
def delete_log(id):
    if "user" not in session:
        return redirect(url_for("main.login"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM study_log WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("main.home"))
