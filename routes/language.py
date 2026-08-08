from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.language_service import (
    list_language_skills,
    add_language_skill,
    edit_language_skill,
    approve_language_skill,
    reject_language_skill
)


language = Blueprint(
    "language",
    __name__
)


@language.route("/language")
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def language_list():

    return list_language_skills()


@language.route(
    "/language/add",
    methods=["GET", "POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def create_language():

    return add_language_skill()


@language.route(
    "/language/<int:id>/edit",
    methods=["GET", "POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def edit_language_submission(id):

    return edit_language_skill(id)


@language.route(
    "/language/<int:id>/approve",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def approve_language_submission(id):

    return approve_language_skill(id)


@language.route(
    "/language/<int:id>/reject",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def reject_language_submission(id):

    return reject_language_skill(id)