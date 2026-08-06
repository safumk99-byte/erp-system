from flask import Blueprint, render_template, request, redirect, session
from werkzeug.security import check_password_hash

from database.db import get_connection

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        institution_code = request.form["institution_code"].strip()
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                users.*,
                roles.name AS role_name
            FROM users
            JOIN institutions
                ON users.institution_id = institutions.id
            JOIN roles
                ON users.role_id = roles.id
            WHERE institutions.code = %s
            AND users.username = %s
            AND users.is_active = TRUE
        """, (institution_code, username))

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["role"] = user["role_name"]
            session["institution_id"] = user["institution_id"]

            return redirect("/dashboard")

        return "Invalid Login"

    return render_template("login.html")