from flask import Blueprint, redirect, url_for


student_login = Blueprint(
    "student_login",
    __name__
)


# Old Student Login URL
# Redirect to the new central login

@student_login.route("/student-login")
def old_student_login():

    return redirect(
        url_for("auth.student_login")
    )


# Old Student Dashboard URL
# Redirect to the common role-based dashboard

@student_login.route("/student-dashboard")
def old_student_dashboard():

    return redirect(
        url_for("dashboard.dashboard")
    )


# Old Student Logout URL
# Redirect to the central logout

@student_login.route("/student-logout")
def old_student_logout():

    return redirect(
        url_for("auth.logout")
    )