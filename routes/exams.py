from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.exam_service import (
    list_exams,
    add_exam,
    edit_exam,
    toggle_exam,
    enter_marks,
    save_marks,
    get_class_subjects
)

exams = Blueprint(
    "exams",
    __name__
)


@exams.route("/exams")
@login_required
@role_required("institution_admin", "staff")
def exam_list():

    return list_exams()


@exams.route("/exams/add", methods=["GET", "POST"])
@login_required
@role_required("institution_admin", "staff")
def create_exam():

    return add_exam()


@exams.route("/exams/edit/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("institution_admin", "staff")
def update_exam(id):

    return edit_exam(id)


@exams.route("/exams/toggle/<int:id>")
@login_required
@role_required("institution_admin", "staff")
def toggle_exam_status(id):

    return toggle_exam(id)


@exams.route("/exams/<int:id>/marks")
@login_required
@role_required("institution_admin", "staff")
def exam_marks(id):

    return enter_marks(id)


@exams.route("/exams/<int:id>/marks", methods=["POST"])
@login_required
@role_required("institution_admin", "staff")
def save_exam_marks(id):

    return save_marks(id)

@exams.route(
    "/exams/class-subjects/<int:class_id>"
)
@login_required
@role_required("institution_admin", "staff")
def class_subjects(class_id):

    return get_class_subjects(class_id)