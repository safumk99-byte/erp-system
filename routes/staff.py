from flask import Blueprint,send_from_directory
import os

from middleware.auth import login_required
from middleware.roles import role_required

from services.staff_service import (
    list_staff,
    add_staff,
    edit_staff,
    view_staff,
    toggle_staff_status,
    assign_staff_classes,
    assign_staff_subjects
)


staff = Blueprint(
    "staff",
    __name__
)


# =========================================================
# Staff List
# =========================================================

@staff.route("/staff")
@login_required
@role_required("institution_admin")
def staff_list():

    return list_staff()


# =========================================================
# Add Staff
# =========================================================

@staff.route(
    "/staff/add",
    methods=["GET", "POST"]
)
@login_required
@role_required("institution_admin")
def create_staff():

    return add_staff()


# =========================================================
# Edit Staff
# =========================================================

@staff.route(
    "/staff/edit/<int:id>",
    methods=["GET", "POST"]
)
@login_required
@role_required("institution_admin")
def update_staff(id):

    return edit_staff(id)


# =========================================================
# View Staff
# =========================================================

@staff.route(
    "/staff/view/<int:id>"
)
@login_required
@role_required("institution_admin")
def view_staff_page(id):

    return view_staff(id)

# =========================================================
# Toggle Staff Status
# POST only
# =========================================================

@staff.route(
    "/staff/toggle/<int:id>",
    methods=["POST"]
)
@login_required
@role_required("institution_admin")
def toggle_staff(id):

    return toggle_staff_status(id)


# =========================================================
# Assign Staff to Classes
# =========================================================

@staff.route(
    "/staff/<int:id>/assign-classes",
    methods=["GET", "POST"]
)
@login_required
@role_required("institution_admin")
def assign_classes(id):

    return assign_staff_classes(id)


# =========================================================
# Assign Staff to Subjects
# =========================================================

@staff.route(
    "/staff/<int:id>/assign-subjects",
    methods=["GET", "POST"]
)
@login_required
@role_required("institution_admin")
def assign_subjects(id):

    return assign_staff_subjects(id)

# =========================================================
# Staff Photo
# =========================================================

@staff.route(
    "/uploads/staff/<filename>"
)
@login_required
@role_required("institution_admin")
def staff_photo(filename):

    upload_folder = os.path.join(
        "uploads",
        "staff"
    )

    return send_from_directory(
        upload_folder,
        filename
    )