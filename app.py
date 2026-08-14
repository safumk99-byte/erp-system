from flask import Flask, render_template
from config import SECRET_KEY
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
from services.notification_service import get_unread_count
from routes.reports import reports
from routes.parent import parent_bp

app = Flask(__name__)
app.secret_key = SECRET_KEY

@app.context_processor
def inject_notification_count():

    try:
        unread_notification_count = get_unread_count()
    except Exception:
        unread_notification_count = 0

    return {
        "unread_notification_count": unread_notification_count
    }

from services.report_context_service import get_report_context


@app.context_processor
def inject_report_context():

    return {
        "report_context": get_report_context()
    }
    
    
from services.notification_service import get_unread_count
    
@app.context_processor
def inject_notification_count():

    return {
        "unread_notification_count": get_unread_count()
    }    

app.register_blueprint(auth)
app.register_blueprint(dashboard_bp)
app.register_blueprint(institution)
app.register_blueprint(staff)
app.register_blueprint(portal)
app.register_blueprint(students)
app.register_blueprint(classes)
app.register_blueprint(subjects)
app.register_blueprint(parents)
app.register_blueprint(attendance)
app.register_blueprint(exams)
app.register_blueprint(reading)
app.register_blueprint(speaking)
app.register_blueprint(writing)
app.register_blueprint(publication)
app.register_blueprint(language)
app.register_blueprint(achievement)
app.register_blueprint(paper_presentation)
app.register_blueprint(staff_attendance)
app.register_blueprint(portion_completion)
app.register_blueprint(mentoring)
app.register_blueprint(student_leave)
app.register_blueprint(student_login)
app.register_blueprint(performance)
app.register_blueprint(academic_years)
app.register_blueprint(student_promotions)
app.register_blueprint(notifications)
app.register_blueprint(reports)
app.register_blueprint(parent_bp)

@app.route("/login")
def login():
    return render_template("login.html")


if __name__ == "__main__":
    
    app.run(debug=True)