from flask import (
    Blueprint,
    render_template
)

from middleware.auth import login_required

dashboard_bp = Blueprint(
    "dashboard",
    __name__
)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():

    return render_template(
        "dashboard/index.html"
    )