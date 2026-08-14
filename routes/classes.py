from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.class_service import (
    list_classes,
    add_class,
    edit_class,
    toggle_class_status,
    view_class_students,
    class_students
)

classes = Blueprint(
    "classes",
    __name__
)


@classes.route("/classes")
@login_required
@role_required("institution_admin", "staff")
def class_list():

    return list_classes()

@classes.route("/classes/add", methods=["GET", "POST"])
@login_required
@role_required("institution_admin", "staff")
def create_class():

    return add_class()

@classes.route("/classes/edit/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("institution_admin", "staff")
def update_class(id):

    return edit_class(id)


@classes.route("/classes/toggle/<int:id>")
@login_required
@role_required("institution_admin", "staff")
def toggle_class(id):

    return toggle_class_status(id)

# =========================================================
# View Students Of Class
# =========================================================

@classes.route(
    "/classes/<int:id>/students"
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def class_students(id):

    return view_class_students(id)

# =========================================================
# View Students of Class
# =========================================================

@classes.route(
    "/classes/<int:class_id>/students"
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def class_students_page(class_id):

    return class_students(class_id)