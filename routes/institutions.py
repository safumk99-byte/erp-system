from flask import Blueprint

from middleware.auth import login_required
from services.institution_service import(
    list_institutions,
    add_institution,
    update_institution,
    deactivate_institution_service
)

institution = Blueprint("institution", __name__)


@institution.route("/institutions")
@login_required
def institutions():

    return list_institutions()

@institution.route("/institutions/add", methods=["GET", "POST"])
@login_required
def create_institution():

    return add_institution()

@institution.route("/institutions/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_institution(id):

    return update_institution(id)

@institution.route("/institutions/deactivate/<int:id>")
@login_required
def deactivate_institution(id):

    return deactivate_institution_service(id)