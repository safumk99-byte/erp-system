from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.attendance_service import (
    attendance_page,
    mark_attendance,
    get_student_popup
)

attendance = Blueprint(
    "attendance",
    __name__
)


@attendance.route("/attendance")
@login_required
@role_required("institution_admin", "staff")
def attendance_list():

    return attendance_page()


@attendance.route(
    "/attendance/mark",
    methods=["POST"]
)
@login_required
@role_required("institution_admin", "staff")
def save_attendance():

    return mark_attendance()


@attendance.route(
    "/attendance/student/<int:student_id>"
)
@login_required
@role_required("institution_admin", "staff")
def student_popup(student_id):

    return get_student_popup(
        student_id
    )