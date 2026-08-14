from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required



from services.report_service import (
    central_report,
    central_report_pdf,
    central_report_excel
)


reports = Blueprint(
    "reports",
    __name__
)


# =========================================================
# Central Report
# =========================================================

@reports.route("/reports/central")
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def central_report_page():

    return central_report()

# =========================================================
# Central Report PDF
# =========================================================

@reports.route("/reports/central/pdf")
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def central_report_pdf_page():

    return central_report_pdf()

# =========================================================
# Central Report Excel
# =========================================================

@reports.route("/reports/central/excel")
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def central_report_excel_page():

    return central_report_excel()