from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.performance_service import (
    performance_matrix,
    class_performance
)


# =========================================================
# Performance Blueprint
# =========================================================

performance = Blueprint(
    "performance",
    __name__
)


# =========================================================
# Performance Matrix
# =========================================================

@performance.route(
    "/performance"
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def performance_page():

    return performance_matrix()


# =========================================================
# Class Performance
# =========================================================

@performance.route(
    "/performance/class/<int:class_id>"
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def class_performance_page(
    class_id
):

    return class_performance(
        class_id
    )