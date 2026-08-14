from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.student_promotion_service import (
    list_promotions,
    promote_student
)


student_promotions = Blueprint(
    "student_promotions",
    __name__
)


# =========================================================
# Promotion History
# =========================================================

@student_promotions.route("/student-promotions")
@login_required
@role_required("institution_admin")
def list_promotions_page():

    return list_promotions()


# =========================================================
# Promote Student
# =========================================================

@student_promotions.route(
    "/student-promotions/add",
    methods=["GET", "POST"]
)
@login_required
@role_required("institution_admin")
def create_promotion():

    return promote_student()