from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.parent_service import (
    list_parents,
    add_parent,
    edit_parent,
    toggle_parent_status
)

parents = Blueprint(
    "parents",
    __name__
)


@parents.route("/parents")
@login_required
@role_required("institution_admin", "staff")
def parent_list():

    return list_parents()


@parents.route("/parents/add", methods=["GET", "POST"])
@login_required
@role_required("institution_admin", "staff")
def create_parent():

    return add_parent()


@parents.route("/parents/edit/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("institution_admin", "staff")
def update_parent(id):

    return edit_parent(id)


@parents.route("/parents/toggle/<int:id>")
@login_required
@role_required("institution_admin", "staff")
def toggle_parent(id):

    return toggle_parent_status(id)