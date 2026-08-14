from datetime import date

from database.db import get_connection


# =========================================================
# Month Context
# =========================================================

def get_month_context():

    selected_month = None

    try:
        from flask import request

        selected_month = request.args.get(
            "month",
            ""
        ).strip()

    except Exception:
        selected_month = ""


    if selected_month:

        try:
            month_number = int(selected_month)

            if 1 <= month_number <= 12:

                month_date = date(
                    date.today().year,
                    month_number,
                    1
                )

                return {
                    "month_number": month_number,
                    "month_name": month_date.strftime("%B"),
                    "month_label": month_date.strftime("%B %Y"),
                    "is_selected": True
                }

        except (ValueError, TypeError):

            pass


    today = date.today()

    return {
        "month_number": today.month,
        "month_name": today.strftime("%B"),
        "month_label": today.strftime("%B %Y"),
        "is_selected": False
    }


# =========================================================
# Academic Year Context
# =========================================================

def get_academic_year_context():

    from flask import session

    institution_id = session.get(
        "institution_id"
    )

    if not institution_id:

        return None


    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT
                id,
                year_name,
                start_date,
                end_date,
                is_current

            FROM academic_years

            WHERE
                institution_id = %s
                AND is_active = TRUE
                AND is_current = TRUE

            LIMIT 1
        """, (
            institution_id,
        ))

        academic_year = cur.fetchone()

        return academic_year

    finally:

        cur.close()
        conn.close()


# =========================================================
# Course Context
# =========================================================

def get_course_context():

    from flask import request

    course = request.args.get(
        "course",
        ""
    ).strip()


    if not course:

        return None


    allowed_courses = {
        "kithab": "Kithab",
        "academic": "Academic",
        "language": "Language"
    }


    return allowed_courses.get(
        course.lower()
    )


# =========================================================
# Complete Report Context
# =========================================================

def get_report_context():

    academic_year = get_academic_year_context()

    return {
        "month_context": get_month_context(),

        "academic_year_context": academic_year,

        "course_context": get_course_context()
    }