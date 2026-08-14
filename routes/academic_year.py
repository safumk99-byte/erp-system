from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.academic_year_service import (
    list_academic_years,
    add_academic_year,
    edit_academic_year,
    toggle_academic_year_status,
    set_current_academic_year
)


academic_years = Blueprint(
    "academic_years",
    __name__
)


# =========================================================
# List Academic Years
# =========================================================

@academic_years.route("/academic-years")
@login_required
@role_required("institution_admin")
def list_academic_years_page():

    return list_academic_years()


# =========================================================
# Add Academic Year
# =========================================================

@academic_years.route(
    "/academic-years/add",
    methods=["GET", "POST"]
)
@login_required
@role_required("institution_admin")
def create_academic_year():

    return add_academic_year()


# =========================================================
# Edit Academic Year
# =========================================================

@academic_years.route(
    "/academic-years/edit/<int:id>",
    methods=["GET", "POST"]
)
@login_required
@role_required("institution_admin")
def update_academic_year(id):

    return edit_academic_year(id)


# =========================================================
# Toggle Academic Year Status
# IMPORTANT:
# This changes database state, therefore POST only.
# =========================================================

@academic_years.route(
    "/academic-years/toggle/<int:id>",
    methods=["POST"]
)
@login_required
@role_required("institution_admin")
def toggle_academic_year(id):

    return toggle_academic_year_status(id)


# =========================================================
# Set Current Academic Year
# IMPORTANT:
# This changes database state, therefore POST only.
# =========================================================

@academic_years.route(
    "/academic-years/current/<int:id>",
    methods=["POST"]
)
@login_required
@role_required("institution_admin")
def make_current_academic_year(id):

    return set_current_academic_year(id)