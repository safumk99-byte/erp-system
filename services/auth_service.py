from flask import (
    request,
    session,
    redirect,
    render_template,
    flash,
    url_for
)
from werkzeug.security import check_password_hash

from database.db import get_connection


def login_user(login_type):

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        institution_code = request.form.get(
            "institution_code",
            ""
        ).strip()

        conn = get_connection()
        cur = conn.cursor()

        # -------------------------
        # Super Admin Login
        # -------------------------
        if login_type == "admin":

            cur.execute("""
                SELECT
                    users.*,
                    roles.name AS role_name
                FROM users
                JOIN roles
                    ON users.role_id = roles.id
                WHERE
                    users.username = %s
                    AND roles.name = 'super_admin'
                    AND users.is_active = TRUE
            """, (username,))

        # -------------------------
        # Institution / Staff /
        # Parent / Student Login
        # -------------------------
        else:

            cur.execute("""
                SELECT
                    users.*,
                    roles.name AS role_name
                FROM users
                JOIN institutions
                    ON users.institution_id = institutions.id
                JOIN roles
                    ON users.role_id = roles.id
                WHERE
                    institutions.code = %s
                    AND users.username = %s
                    AND roles.name = %s
                    AND users.is_active = TRUE
            """, (
                institution_code,
                username,
                login_type
            ))

        user = cur.fetchone()
        
        cur.close()
        conn.close()

        if not user:

            flash(
                "Invalid login credentials.",
                "error"
            )

            return render_template(
                "auth/login.html",
                login_type=login_type,
                title=f"{login_type.replace('_', ' ').title()} Login",
                heading=f"{login_type.replace('_', ' ').title()} Login",
                subtitle="Sign in to continue"
            )
            
       
        if not check_password_hash(
            user["password"],
            password
        ):

            flash(
                "Invalid login credentials.",
                "error"
            )

            return render_template(
                "auth/login.html",
                login_type=login_type,
                title=f"{login_type.replace('_', ' ').title()} Login",
                heading=f"{login_type.replace('_', ' ').title()} Login",
                subtitle="Sign in to continue"
            )

        session.clear()

        session["user_id"] = user["id"]
        session["institution_id"] = user["institution_id"]
        session["role"] = user["role_name"]
        session["role_id"] = user["role_id"]
        session["full_name"] = user["full_name"]


        # -------------------------
        # Student Dashboard
        # -------------------------

        if user["role_name"] == "student":

            # Get student record linked to this user

            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT
                    id,
                    full_name

                FROM students

                WHERE
                    user_id = %s
                    AND institution_id = %s
                    AND is_active = TRUE
            """, (
                user["id"],
                user["institution_id"]
            ))

            student = cur.fetchone()

            cur.close()
            conn.close()


            if not student:

                session.clear()

                flash(
                    "Student profile not found.",
                    "error"
                )

                return redirect(
                    url_for(
                        "auth.student_login"
                    )
                )


            session["student_id"] = student["id"]

            session["student_name"] = student["full_name"]


            return redirect(
                url_for(
                    "dashboard.dashboard"
                )
                    )


        # -------------------------
        # Other Users
        # -------------------------

        return redirect(
            url_for(
                "dashboard.dashboard"
            )
        )

    return render_template(
        "auth/login.html",
        login_type=login_type,
        title=f"{login_type.replace('_', ' ').title()} Login",
        heading=f"{login_type.replace('_', ' ').title()} Login",
        subtitle=login_type
    )


def logout_user():

    session.clear()

    flash(
        "Logged out successfully.",
        "success"
    )

    return redirect(
        url_for("portal.index")
    )