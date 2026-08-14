from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.subject_service import (
    list_subjects,
    add_subject,
    edit_subject,
    toggle_subject_status,
    view_all_subjects
)


subjects = Blueprint(
    "subjects",
    __name__
)


# =========================================================
# Subject Page
# =========================================================

@subjects.route("/subjects")
@login_required
@role_required("institution_admin", "staff")
def subject_list():

    return list_subjects()


# =========================================================
# View All Subjects
# =========================================================

@subjects.route("/subjects/view")
@login_required
@role_required("institution_admin", "staff")
def view_subjects():

    return view_all_subjects()


# =========================================================
# Add Subject
# =========================================================

@subjects.route(
    "/subjects/add",
    methods=["GET", "POST"]
)
@login_required
@role_required("institution_admin")
def create_subject():

    return add_subject()


# =========================================================
# Edit Subject
# =========================================================

@subjects.route(
    "/subjects/edit/<int:id>",
    methods=["GET", "POST"]
)
@login_required
@role_required("institution_admin")
def update_subject(id):

    return edit_subject(id)


# =========================================================
# Toggle Subject Status
# =========================================================

@subjects.route(
    "/subjects/toggle/<int:id>",
    methods=["POST"]
)
@login_required
@role_required("institution_admin")
def toggle_subject(id):

    return toggle_subject_status(id)