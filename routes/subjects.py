from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.subject_service import (
    list_subjects,
    add_subject,
    edit_subject,
    toggle_subject_status
)

subjects = Blueprint(
    "subjects",
    __name__
)


@subjects.route("/subjects")
@login_required
@role_required("institution_admin", "staff")
def subject_list():

    return list_subjects()

@subjects.route("/subjects/add", methods=["GET", "POST"])
@login_required
@role_required("institution_admin", "staff")
def create_subject():

    return add_subject()


@subjects.route("/subjects/edit/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("institution_admin", "staff")
def update_subject(id):

    return edit_subject(id)


@subjects.route("/subjects/toggle/<int:id>")
@login_required
@role_required("institution_admin", "staff")
def toggle_subject(id):

    return toggle_subject_status(id)