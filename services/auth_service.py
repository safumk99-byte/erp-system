from flask import request, session, redirect, render_template
from werkzeug.security import check_password_hash

from database.db import get_connection


def login_user():

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
            session["institution_id"] = user["institution_id"]
            session["role"] = user["role_name"]
            session["full_name"] = user["full_name"]

            return redirect("/dashboard")

        return "Invalid Login"

    return render_template("auth/login.html")

def logout_user():

    session.clear()

    return redirect("/login")