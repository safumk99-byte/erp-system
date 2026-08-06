from flask import Blueprint, render_template, session, redirect, url_for

admin_dashboard = Blueprint("admin_dashboard", __name__)


@admin_dashboard.route("/admin/dashboard")
def dashboard():

    if session.get("role") != "super_admin":
        return redirect(url_for("auth.login"))

    return render_template("admin/dashboard.html")