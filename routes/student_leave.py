from flask import Blueprint

from services.student_leave_service import (
    student_leave_page,
    submit_student_leave,
    student_leave_requests,
    review_student_leave
)

from middleware.auth import login_required
from middleware.roles import role_required


student_leave = Blueprint(
    "student_leave",
    __name__
)


# =========================================================
# Student Leave Page
# =========================================================

@student_leave.route("/student-leave")
@login_required
def student_leave_page_route():

    return student_leave_page()


# =========================================================
# Submit Leave
# =========================================================

@student_leave.route(
    "/student-leave/submit",
    methods=["POST"]
)
@login_required
def submit_student_leave_route():

    return submit_student_leave()


# =========================================================
# Leave Requests
# =========================================================

@student_leave.route(
    "/student-leave/requests"
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def student_leave_requests_route():

    return student_leave_requests()


# =========================================================
# Review Leave
# =========================================================

@student_leave.route(
    "/student-leave/review",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def review_student_leave_route():

    return review_student_leave()