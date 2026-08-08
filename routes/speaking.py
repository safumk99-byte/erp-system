from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.speaking_service import (
    list_speakings,
    add_speaking,
    edit_speaking,
    approve_speaking,
    reject_speaking
)


speaking = Blueprint(
    "speaking",
    __name__
)


@speaking.route("/speaking")
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def speaking_list():

    return list_speakings()


@speaking.route(
    "/speaking/add",
    methods=["GET", "POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def create_speaking():

    return add_speaking()


@speaking.route(
    "/speaking/<int:id>/approve",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def approve_speaking_submission(id):

    return approve_speaking(id)


@speaking.route(
    "/speaking/<int:id>/reject",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def reject_speaking_submission(id):

    return reject_speaking(id)

@speaking.route(
    "/speaking/<int:id>/edit",
    methods=["GET", "POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def edit_speaking_submission(id):

    return edit_speaking(id)