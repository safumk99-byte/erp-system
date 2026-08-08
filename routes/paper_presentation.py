from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.paper_presentation_service import (
    list_paper_presentations,
    add_paper_presentation,
    edit_paper_presentation,
    approve_paper_presentation,
    reject_paper_presentation
)


paper_presentation = Blueprint(
    "paper_presentation",
    __name__
)


@paper_presentation.route("/paper-presentations")
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def paper_presentation_list():

    return list_paper_presentations()


@paper_presentation.route(
    "/paper-presentations/add",
    methods=["GET", "POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def create_paper_presentation():

    return add_paper_presentation()


@paper_presentation.route(
    "/paper-presentations/<int:id>/edit",
    methods=["GET", "POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def edit_paper_presentation_submission(id):

    return edit_paper_presentation(id)


@paper_presentation.route(
    "/paper-presentations/<int:id>/approve",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def approve_paper_presentation_submission(id):

    return approve_paper_presentation(id)


@paper_presentation.route(
    "/paper-presentations/<int:id>/reject",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def reject_paper_presentation_submission(id):

    return reject_paper_presentation(id)