from datetime import date

from flask import request, session

from database.db import get_connection


# =========================================================
# Month Context
# =========================================================

def get_month_context():

    selected_month = request.args.get(
        "month",
        ""
    ).strip()

    # -----------------------------------------------------
    # Selected Month
    # -----------------------------------------------------

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

        except (
            ValueError,
            TypeError
        ):

            pass

    # -----------------------------------------------------
    # Default Month
    # -----------------------------------------------------

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

    institution_id = session.get(
        "institution_id"
    )

    if not institution_id:

        return None

    selected_year_id = request.args.get(
        "academic_year",
        ""
    ).strip()

    conn = get_connection()
    cur = conn.cursor()

    try:

        # -------------------------------------------------
        # Selected Academic Year
        # -------------------------------------------------

        if selected_year_id:

            try:

                selected_year_id = int(
                    selected_year_id
                )

            except (
                ValueError,
                TypeError
            ):

                selected_year_id = None


            if selected_year_id:

                cur.execute("""
                    SELECT
                        id,
                        year_name,
                        start_date,
                        end_date,
                        is_current

                    FROM academic_years

                    WHERE
                        id = %s
                        AND institution_id = %s
                        AND is_active = TRUE

                    LIMIT 1
                """, (
                    selected_year_id,
                    institution_id
                ))

                academic_year = cur.fetchone()

                if academic_year:

                    return academic_year

        # -------------------------------------------------
        # Default → Current Academic Year
        # -------------------------------------------------

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

        return cur.fetchone()

    finally:

        cur.close()
        conn.close()


# =========================================================
# Course Context
# =========================================================

def get_course_context():

    institution_id = session.get(
        "institution_id"
    )

    if not institution_id:

        return None

    selected_course_id = request.args.get(
        "course",
        ""
    ).strip()

    if not selected_course_id:

        return None

    try:

        selected_course_id = int(
            selected_course_id
        )

    except (
        ValueError,
        TypeError
    ):

        return None

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT
                id,
                course_name,
                course_code,
                description,
                is_active

            FROM courses

            WHERE
                id = %s
                AND institution_id = %s
                AND is_active = TRUE

            LIMIT 1
        """, (
            selected_course_id,
            institution_id
        ))

        return cur.fetchone()

    finally:

        cur.close()
        conn.close()


# =========================================================
# Available Academic Years
# =========================================================

def get_available_academic_years():

    institution_id = session.get(
        "institution_id"
    )

    if not institution_id:

        return []

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

            ORDER BY
                start_date DESC NULLS LAST,
                id DESC
        """, (
            institution_id,
        ))

        return cur.fetchall()

    finally:

        cur.close()
        conn.close()


# =========================================================
# Available Courses
# =========================================================

def get_available_courses():

    institution_id = session.get(
        "institution_id"
    )

    if not institution_id:

        return []

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT
                id,
                course_name,
                course_code,
                description,
                is_active

            FROM courses

            WHERE
                institution_id = %s
                AND is_active = TRUE

            ORDER BY
                course_name ASC,
                id ASC
        """, (
            institution_id,
        ))

        return cur.fetchall()

    finally:

        cur.close()
        conn.close()


# =========================================================
# Complete Report Context
# =========================================================

def get_report_context():

    month = get_month_context()

    academic_year = get_academic_year_context()

    course = get_course_context()

    academic_years = get_available_academic_years()

    courses = get_available_courses()

    return {

        # -------------------------------------------------
        # Current selections
        # -------------------------------------------------

        "month_context": month,

        "academic_year_context":
            academic_year,

        "course_context":
            course,

        # -------------------------------------------------
        # Dropdown options
        # -------------------------------------------------

        "academic_years":
            academic_years,

        "courses":
            courses
    }