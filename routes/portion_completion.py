from flask import Blueprint

from services.portion_completion_service import (
    portion_completion_page,
    save_portion_completion,
    portion_completion_list
)

from middleware.auth import login_required
from middleware.roles import role_required


portion_completion = Blueprint(
    "portion_completion",
    __name__
)


# ---------------------------------
# Portion Completion Page
# ---------------------------------

@portion_completion.route(
    "/portion-completion"
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def portion_completion_page_route():

    return portion_completion_page()


# ---------------------------------
# Save Portion Completion
# ---------------------------------

@portion_completion.route(
    "/portion-completion/save",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def save_portion_completion_route():

    return save_portion_completion()


# ---------------------------------
# Portion Completion List
# ---------------------------------

@portion_completion.route(
    "/portion-completion/list"
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def portion_completion_list_route():

    return portion_completion_list()