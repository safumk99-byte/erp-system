from flask import Blueprint, render_template, session, redirect, url_for

institution_dashboard = Blueprint(
    "institution_dashboard",
    __name__
)


@institution_dashboard.route("/institution/dashboard")
def dashboard():

    if session.get("role") != "institution_admin":
        return redirect(url_for("auth.login"))

    return render_template(
        "institution/dashboard.html"
    )