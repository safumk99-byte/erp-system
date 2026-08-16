import os

from flask import Flask

from config import SECRET_KEY

from routes.admin_dashboard import admin_dashboard
from routes.auth import auth
from routes.dashboard import dashboard_bp
from routes.institutions import institution
from routes.staff import staff
from routes.portal import portal
from routes.students import students
from routes.classes import classes
from routes.subjects import subjects
from routes.parents import parents
from routes.attendance import attendance
from routes.exams import exams
from routes.reading import reading
from routes.speaking import speaking
from routes.writing import writing
from routes.publication import publication
from routes.language import language
from routes.achievement import achievement
from routes.paper_presentation import paper_presentation
from routes.staff_attendance import staff_attendance
from routes.portion_completion import portion_completion
from routes.mentoring import mentoring
from routes.student_leave import student_leave
from routes.student_login import student_login
from routes.performance import performance
from routes.academic_year import academic_years
from routes.student_promotions import student_promotions
from routes.notifications import notifications
from routes.reports import reports
from routes.parent import parent_bp
from routes.institution_dashboard import institution_dashboard
from routes.courses import courses
from routes.settings import settings

from services.notification_service import (
    get_unread_count
)

from services.report_context_service import (
    get_report_context
)


# =========================================================
# Flask Application
# =========================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = SECRET_KEY


# =========================================================
# Context Processors
# =========================================================

@app.context_processor
def inject_notification_count():

    try:

        unread_notification_count = (
            get_unread_count()
        )

    except Exception:

        unread_notification_count = 0

    return {
        "unread_notification_count":
            unread_notification_count
    }


@app.context_processor
def inject_report_context():

    try:

        report_context = (
            get_report_context()
        )

    except Exception:

        report_context = {
            "month_context": None,
            "academic_year_context": None,
            "course_context": None
        }

    return {
        "report_context": report_context
    }


# =========================================================
# Blueprint Registration
# =========================================================
app.register_blueprint(admin_dashboard)

# ---------------------------------------------------------
# Authentication / Portal
# ---------------------------------------------------------

app.register_blueprint(auth)
app.register_blueprint(portal)
app.register_blueprint(student_login)


# ---------------------------------------------------------
# Dashboards
# ---------------------------------------------------------

app.register_blueprint(dashboard_bp)
app.register_blueprint(institution_dashboard)


# ---------------------------------------------------------
# Institution Management
# ---------------------------------------------------------

app.register_blueprint(institution)
app.register_blueprint(courses)
app.register_blueprint(academic_years)
app.register_blueprint(student_promotions)
app.register_blueprint(settings)


# ---------------------------------------------------------
# Academic Structure
# ---------------------------------------------------------

app.register_blueprint(classes)
app.register_blueprint(subjects)
app.register_blueprint(exams)
app.register_blueprint(performance)


# ---------------------------------------------------------
# Student / Parent
# ---------------------------------------------------------

app.register_blueprint(students)
app.register_blueprint(parents)
app.register_blueprint(parent_bp)
app.register_blueprint(student_leave)


# ---------------------------------------------------------
# Staff
# ---------------------------------------------------------

app.register_blueprint(staff)
app.register_blueprint(staff_attendance)


# ---------------------------------------------------------
# Academic Assessment
# ---------------------------------------------------------

app.register_blueprint(attendance)
app.register_blueprint(reading)
app.register_blueprint(speaking)
app.register_blueprint(writing)
app.register_blueprint(publication)
app.register_blueprint(language)
app.register_blueprint(achievement)
app.register_blueprint(paper_presentation)
app.register_blueprint(portion_completion)
app.register_blueprint(mentoring)


# ---------------------------------------------------------
# System
# ---------------------------------------------------------

app.register_blueprint(notifications)
app.register_blueprint(reports)


# =========================================================
# Application Entry Point
# =========================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "5000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )