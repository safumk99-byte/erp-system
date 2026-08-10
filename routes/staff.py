from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.staff_service import (
    list_staff,
    add_staff,
    edit_staff,
    toggle_staff_status,
    assign_staff_classes,
    assign_staff_subjects
)

staff = Blueprint(
    "staff",
    __name__
)


@staff.route("/staff")
@login_required
@role_required("institution_admin")
def staff_list():

    return list_staff()


@staff.route("/staff/add", methods=["GET", "POST"])
@login_required
@role_required("institution_admin")
def create_staff():

    return add_staff()

@staff.route("/staff/edit/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("institution_admin")
def update_staff(id):

    return edit_staff(id)

@staff.route("/staff/toggle/<int:id>")
@login_required
@role_required("institution_admin")
def toggle_staff(id):

    return toggle_staff_status(id)

# -------------------------
# Staff Class Assignment
# -------------------------

@staff.route(
    "/staff/<int:id>/assign-classes",
    methods=["GET", "POST"]
)
@login_required
@role_required("institution_admin")
def assign_classes(id):

    return assign_staff_classes(id)


# -------------------------
# Staff Subject Assignment
# -------------------------

@staff.route(
    "/staff/<int:id>/assign-subjects",
    methods=["GET", "POST"]
)
@login_required
@role_required("institution_admin")
def assign_subjects(id):

    return assign_staff_subjects(id)