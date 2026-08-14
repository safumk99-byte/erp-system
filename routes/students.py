from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required
from flask import Blueprint, send_from_directory
import os

from services.student_service import (
    list_students,
    add_student,
    edit_student,
    toggle_student_status,
    student_profile
)
from services.student_exam_service import(
    student_results,
    student_exams
)

from services.student_progress_service import(
    student_progress
)

students = Blueprint(
    "students",
    __name__
)


@students.route("/students")
@login_required
@role_required("institution_admin", "staff")
def student_list():

    return list_students()

@students.route("/students/add", methods=["GET", "POST"])
@login_required
@role_required("institution_admin", "staff")
def create_student():

    return add_student()

@students.route("/students/edit/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("institution_admin", "staff")
def update_student(id):

    return edit_student(id)


@students.route("/students/toggle/<int:id>")
@login_required
@role_required("institution_admin", "staff")
def toggle_student(id):

    return toggle_student_status(id)

# =========================================================
# Student Profile
# =========================================================

@students.route("/students/<int:id>")
@login_required
@role_required("institution_admin", "staff")
def view_student(id):

    return student_profile(id)

# =========================================================
# Student Photo
# =========================================================

@students.route(
    "/uploads/students/<filename>"
)
@login_required
@role_required(
    "institution_admin",
    "staff",
    "student",
    "parent"
)
def student_photo(filename):

    upload_folder = os.path.join(
        "uploads",
        "students"
    )

    return send_from_directory(
        upload_folder,
        filename
    )
    
# =========================================================
# Student Results
# =========================================================

@students.route("/student/results")
@login_required
@role_required("student")
def student_results_page():

    return student_results()

# =========================================================
# Student Exams
# =========================================================

@students.route("/student/exams")
@login_required
@role_required("student")
def student_exams_page():

    return student_exams()

# =========================================================
# Student Progress Hub
# =========================================================

@students.route("/student/progress")
@login_required
@role_required("student")
def student_progress_page():

    return student_progress()    