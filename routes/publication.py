from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.publication_service import (
    list_publications,
    add_publication,
    edit_publication,
    approve_publication,
    reject_publication
)


publication = Blueprint(
    "publication",
    __name__
)


@publication.route("/publications")
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def publication_list():

    return list_publications()


@publication.route(
    "/publications/add",
    methods=["GET", "POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def create_publication():

    return add_publication()


@publication.route(
    "/publications/<int:id>/approve",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def approve_publication_submission(id):

    return approve_publication(id)


@publication.route(
    "/publications/<int:id>/reject",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def reject_publication_submission(id):

    return reject_publication(id)

@publication.route(
    "/publications/<int:id>/edit",
    methods=["GET", "POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def edit_publication_submission(id):

    return edit_publication(id)