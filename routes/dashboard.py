from flask import Blueprint, session, redirect, render_template

from middleware.auth import login_required
from middleware.roles import role_required

dashboard = Blueprint("dashboard", __name__)


@dashboard.route("/dashboard")
@login_required
@role_required("super_admin")
def dashboard_home():

    return render_template("dashboard/index.html")