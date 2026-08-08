from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.staff_attendance_service import (
    list_staff_attendance,
    mark_staff_attendance_page,
    mark_staff_attendance,
    approve_staff_leave,
    reject_staff_leave,
    monthly_staff_attendance,
    staff_leave_requests
)


staff_attendance = Blueprint(
    "staff_attendance",
    __name__
)


@staff_attendance.route(
    "/staff-attendance"
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def staff_attendance_list():

    return list_staff_attendance()


@staff_attendance.route(
    "/staff-attendance/save",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def save_staff_attendance():

    return mark_staff_attendance()


@staff_attendance.route(
    "/staff-attendance/<int:id>/approve-leave",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def approve_staff_leave_submission(id):

    return approve_staff_leave(id)


@staff_attendance.route(
    "/staff-attendance/<int:id>/reject-leave",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def reject_staff_leave_submission(id):

    return reject_staff_leave(id)


@staff_attendance.route(
    "/staff-attendance/monthly"
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def staff_attendance_monthly():

    return monthly_staff_attendance()

@staff_attendance.route(
    "/staff-attendance/leave-requests"
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def staff_leave_requests_page():

    return staff_leave_requests()

@staff_attendance.route(
    "/staff-attendance/mark"
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def mark_staff_attendance_page_route():

    return mark_staff_attendance_page()