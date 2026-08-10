from flask import (
    Blueprint,
    render_template,
    session
)

from middleware.auth import login_required
from database.db import get_connection

dashboard_bp = Blueprint(
    "dashboard",
    __name__
)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():

    role = session.get("role")

    if role == "staff":

        return render_template(
            "dashboard/staff.html"
        )

    elif role == "student":

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                s.id,
                s.admission_no,
                s.full_name,
                c.class_name

            FROM students s

            LEFT JOIN classes c
                ON s.class_id = c.id

            WHERE
                s.id = %s
                AND s.institution_id = %s
                AND s.is_active = TRUE
        """, (
            session.get("student_id"),
            session.get("institution_id")
        ))

        student = cur.fetchone()


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
            session.get("student_id"),
            session.get("institution_id")
        ))

        attendance = cur.fetchone()

        cur.close()
        conn.close()


        return render_template(
            "dashboard/student.html",
            student=student,
            attendance=attendance
        )

    elif role == "parent":

        return render_template(
            "dashboard/parent.html"
        )

    elif role == "principal":

        return render_template(
            "dashboard/principal.html"
        )

    return render_template(
        "dashboard/index.html"
    )