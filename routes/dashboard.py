from flask import (
    Blueprint,
    render_template,
    session
)

from middleware.auth import login_required
from database.db import get_connection

from services.parent_dashboard_service import(
    parent_dashboard
)

dashboard_bp = Blueprint(
    "dashboard",
    __name__
)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():

    role = session.get("role")

    # =====================================================
    # STAFF
    # =====================================================

    if role == "staff":

        return render_template(
            "dashboard/staff.html"
        )


    # =====================================================
    # STUDENT DASHBOARD
    # =====================================================

    elif role == "student":

        conn = get_connection()
        cur = conn.cursor()

        student_id = session.get("student_id")
        institution_id = session.get("institution_id")


        # =================================================
        # 1. Student Information
        # =================================================

        cur.execute("""
            SELECT
                s.id,
                s.admission_no,
                s.full_name,
                s,photo,
                s.class_id,
                c.class_name

            FROM students s

            LEFT JOIN classes c
                ON s.class_id = c.id
                AND c.institution_id = s.institution_id

            WHERE
                s.id = %s
                AND s.institution_id = %s
                AND s.is_active = TRUE

            LIMIT 1
        """, (
            student_id,
            institution_id
        ))

        student = cur.fetchone()


        # -------------------------------------------------
        # Student not found
        # -------------------------------------------------

        if not student:

            cur.close()
            conn.close()

            return "Student not found.", 404


        # =================================================
        # 2. Attendance
        # =================================================

        cur.execute("""
            SELECT
                COUNT(*) AS total_days,

                COUNT(*) FILTER (
                    WHERE status = 'Present'
                ) AS present_days,

                COUNT(*) FILTER (
                    WHERE status = 'Absent'
                ) AS absent_days,

                COUNT(*) FILTER (
                    WHERE status = 'Leave'
                ) AS leave_days

            FROM attendance

            WHERE
                student_id = %s
                AND institution_id = %s
        """, (
            student_id,
            institution_id
        ))

        attendance = cur.fetchone()


        # -------------------------------------------------
        # Attendance Percentage
        #
        # Leave is not included in attendance percentage.
        # Percentage = Present / (Present + Absent)
        # -------------------------------------------------

        total_attendance_days = (
            (attendance["present_days"] or 0)
            +
            (attendance["absent_days"] or 0)
        )


        if total_attendance_days > 0:

            attendance_percentage = round(
                (
                    attendance["present_days"]
                    /
                    total_attendance_days
                ) * 100,
                2
            )

        else:

            attendance_percentage = 0


        attendance = dict(attendance)

        attendance[
            "attendance_percentage"
        ] = attendance_percentage


        # =================================================
        # 3. Upcoming Exams
        # =================================================

        cur.execute("""
            SELECT
                e.id,
                e.exam_name,
                e.exam_type,
                e.exam_date,
                e.total_mark,

                STRING_AGG(
                    s.subject_name,
                    ', '
                    ORDER BY s.subject_name
                ) AS subjects

            FROM exams e

            JOIN exam_subjects es
                ON es.exam_id = e.id

            JOIN subjects s
                ON s.id = es.subject_id

            WHERE
                e.institution_id = %s
                AND e.class_id = %s
                AND e.is_active = TRUE
                AND e.exam_date >= CURRENT_DATE

            GROUP BY
                e.id,
                e.exam_name,
                e.exam_type,
                e.exam_date,
                e.total_mark

            ORDER BY
                e.exam_date ASC,
                e.id ASC

            LIMIT 5
        """, (
            institution_id,
            student["class_id"]
        ))

        upcoming_exams = cur.fetchall()


        # =================================================
        # 4. Recent Results
        # =================================================

        cur.execute("""
            SELECT
                e.id AS exam_id,
                e.exam_name,
                e.exam_type,
                e.exam_date,

                s.subject_name,

                em.mark,
                em.grade,

                e.total_mark

            FROM exam_marks em

            JOIN exams e
                ON e.id = em.exam_id

            JOIN subjects s
                ON s.id = em.subject_id

            WHERE
                em.student_id = %s
                AND e.institution_id = %s
                AND e.class_id = %s
                AND e.is_active = TRUE
                AND em.subject_id IS NOT NULL

            ORDER BY
                e.exam_date DESC,
                em.id DESC

            LIMIT 6
        """, (
            student_id,
            institution_id,
            student["class_id"]
        ))

        recent_results = cur.fetchall()


        # =================================================
        # 5. Latest Exam Summary
        # =================================================

        cur.execute("""
            SELECT
                e.id AS exam_id,
                e.exam_name,
                e.exam_type,
                e.exam_date,

                COUNT(em.id) AS subjects_completed,

                COALESCE(
                    SUM(em.mark),
                    0
                ) AS total_obtained,

                COALESCE(
                    SUM(e.total_mark),
                    0
                ) AS total_possible

            FROM exam_marks em

            JOIN exams e
                ON e.id = em.exam_id

            WHERE
                em.student_id = %s
                AND e.institution_id = %s
                AND e.class_id = %s
                AND e.is_active = TRUE
                AND em.subject_id IS NOT NULL

            GROUP BY
                e.id,
                e.exam_name,
                e.exam_type,
                e.exam_date

            ORDER BY
                e.exam_date DESC,
                e.id DESC

            LIMIT 1
        """, (
            student_id,
            institution_id,
            student["class_id"]
        ))

        latest_result = cur.fetchone()


        # -------------------------------------------------
        # Calculate Latest Overall Percentage + Grade
        # -------------------------------------------------

        if latest_result:

            latest_result = dict(
                latest_result
            )

            total_obtained = float(
                latest_result["total_obtained"] or 0
            )

            total_possible = float(
                latest_result["total_possible"] or 0
            )


            if total_possible > 0:

                percentage = (
                    total_obtained
                    /
                    total_possible
                ) * 100

            else:

                percentage = 0


            percentage = round(
                percentage,
                2
            )


            if percentage >= 90:

                overall_grade = "A+"

            elif percentage >= 80:

                overall_grade = "A"

            elif percentage >= 70:

                overall_grade = "B+"

            elif percentage >= 60:

                overall_grade = "B"

            elif percentage >= 50:

                overall_grade = "C"

            else:

                overall_grade = "D"


            latest_result[
                "percentage"
            ] = percentage

            latest_result[
                "grade"
            ] = overall_grade


        # =================================================
        # Close Database
        # =================================================

        cur.close()
        conn.close()


        # =================================================
        # Render Student Dashboard
        # =================================================

        return render_template(
            "dashboard/student.html",

            student=student,

            attendance=attendance,

            upcoming_exams=upcoming_exams,

            recent_results=recent_results,

            latest_result=latest_result
        )


    # =====================================================
    # PARENT
    # =====================================================

    elif role == "parent":

        return parent_dashboard()


    # =====================================================
    # PRINCIPAL
    # =====================================================

    elif role == "principal":

        return render_template(
            "dashboard/principal.html"
        )


    # =====================================================
    # DEFAULT
    # =====================================================

    return render_template(
        "dashboard/index.html"
    )