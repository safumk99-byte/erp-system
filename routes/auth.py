from flask import Blueprint, render_template

from services.auth_service import (
    login_user,
    logout_user
)

auth = Blueprint(
    "auth",
    __name__
)


# -------------------------
# Super Admin Login
# -------------------------
@auth.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    return login_user(
        login_type="admin"
    )


# -------------------------
# Institution Login
# -------------------------
@auth.route("/institution/login", methods=["GET", "POST"])
def institution_login():

    return login_user(
        login_type="institution_admin"
    )


# -------------------------
# Staff Login
# -------------------------
@auth.route("/staff/login", methods=["GET", "POST"])
def staff_login():

    return login_user(
        login_type="staff"
    )


# -------------------------
# Parent Login
# -------------------------
@auth.route("/parent/login", methods=["GET", "POST"])
def parent_login():

    return login_user(
        login_type="parent"
    )


# -------------------------
# Student Login
# -------------------------
@auth.route("/student/login", methods=["GET", "POST"])
def student_login():

    return login_user(
        login_type="student"
    )


# -------------------------
# Logout
# -------------------------
@auth.route("/logout")
def logout():

    return logout_user()