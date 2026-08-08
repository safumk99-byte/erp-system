from flask import Blueprint

from services.mentoring_service import (
    mentoring_page,
    save_mentoring_note,
    mentoring_list
)

from middleware.auth import login_required
from middleware.roles import role_required


mentoring = Blueprint(
    "mentoring",
    __name__
)


@mentoring.route(
    "/mentoring"
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def mentoring_page_route():

    return mentoring_page()


@mentoring.route(
    "/mentoring/save",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def save_mentoring_note_route():

    return save_mentoring_note()

@mentoring.route(
    "/mentoring/list"
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def mentoring_list_route():

    return mentoring_list()