from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.parent_dashboard_service import (
    parent_dashboard,
    parent_child_progress
)


parent_bp = Blueprint(
    "parent",
    __name__
)


# =========================================================
# Child Progress
# =========================================================

@parent_bp.route(
    "/parent/student/<int:student_id>/progress"
)
@login_required
@role_required("parent")
def child_progress(student_id):

    return parent_child_progress(
        student_id
    )