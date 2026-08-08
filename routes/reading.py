from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.reading_service import (
    list_readings,
    add_reading,
    edit_reading,
    approve_reading,
    reject_reading
)


reading = Blueprint(
    "reading",
    __name__
)


@reading.route("/reading")
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def reading_list():

    return list_readings()


@reading.route(
    "/reading/add",
    methods=["GET", "POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def create_reading():

    return add_reading()


@reading.route(
    "/reading/<int:id>/approve",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def approve_reading_submission(id):

    return approve_reading(id)


@reading.route(
    "/reading/<int:id>/reject",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def reject_reading_submission(id):

    return reject_reading(id)

@reading.route(
    "/reading/<int:id>/edit",
    methods=["GET", "POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def edit_reading_submission(id):

    return edit_reading(id)