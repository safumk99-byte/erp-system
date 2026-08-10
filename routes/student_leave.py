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


@student_leave.route(
    "/student-leave"
)
@login_required
def student_leave_page_route():

    return student_leave_page()


@student_leave.route(
    "/student-leave/submit",
    methods=["POST"]
)
@login_required
def submit_student_leave_route():

    return submit_student_leave()

@student_leave.route(
    "/student-leave/requests"
)
@login_required
@role_required(
    "institution_admin",
    "principal",
    "staff"
)
def student_leave_requests_route():

    return student_leave_requests()


@student_leave.route(
    "/student-leave/review",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "principal",
    "staff"
)
def review_student_leave_route():

    return review_student_leave()