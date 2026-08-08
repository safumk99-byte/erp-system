from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.writing_service import (
    list_writings,
    add_writing,
    edit_writing,
    approve_writing,
    reject_writing
)


writing = Blueprint(
    "writing",
    __name__
)


@writing.route("/writing")
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def writing_list():

    return list_writings()


@writing.route(
    "/writing/add",
    methods=["GET", "POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def create_writing():

    return add_writing()


@writing.route(
    "/writing/<int:id>/approve",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def approve_writing_submission(id):

    return approve_writing(id)


@writing.route(
    "/writing/<int:id>/reject",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def reject_writing_submission(id):

    return reject_writing(id)

@writing.route(
    "/writing/<int:id>/edit",
    methods=["GET", "POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def edit_writing_submission(id):

    return edit_writing(id)