from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.student_service import (
    list_students,
    add_student,
    edit_student,
    toggle_student_status
)

students = Blueprint(
    "students",
    __name__
)


@students.route("/students")
@login_required
@role_required("institution_admin", "staff")
def student_list():

    return list_students()

@students.route("/students/add", methods=["GET", "POST"])
@login_required
@role_required("institution_admin", "staff")
def create_student():

    return add_student()

@students.route("/students/edit/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("institution_admin", "staff")
def update_student(id):

    return edit_student(id)


@students.route("/students/toggle/<int:id>")
@login_required
@role_required("institution_admin", "staff")
def toggle_student(id):

    return toggle_student_status(id)