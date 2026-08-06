from flask import Blueprint, session, redirect

dashboard = Blueprint("dashboard", __name__)


@dashboard.route("/dashboard")
def dashboard_home():

    if "user_id" not in session:
        return redirect("/login")

    return "Welcome to ERP Dashboard 🚀"