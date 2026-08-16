from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from database.db import get_connection


courses = Blueprint(
    "courses",
    __name__
)


# =========================================================
# Course List
# =========================================================

@courses.route("/courses")
def course_list():

    if session.get("role") != "institution_admin":
        return "Unauthorized", 403

    institution_id = session.get("institution_id")

    if not institution_id:
        return "Unauthorized", 403

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT
                id,
                course_name,
                course_code,
                description,
                is_active,
                created_at,
                updated_at

            FROM courses

            WHERE
                institution_id = %s

            ORDER BY
                is_active DESC,
                course_name ASC
        """, (
            institution_id,
        ))

        courses_list = cur.fetchall()

        return render_template(
            "courses/list.html",
            courses=courses_list
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# Add Course
# =========================================================

@courses.route(
    "/courses/add",
    methods=["GET", "POST"]
)
def add_course():

    if session.get("role") != "institution_admin":
        return "Unauthorized", 403

    institution_id = session.get("institution_id")

    if not institution_id:
        return "Unauthorized", 403

    if request.method == "POST":

        course_name = request.form.get(
            "course_name",
            ""
        ).strip()

        course_code = request.form.get(
            "course_code",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()


        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if not course_name:

            flash(
                "Course name is required.",
                "error"
            )

            return render_template(
                "courses/add.html"
            )


        if len(course_name) > 150:

            flash(
                "Course name is too long.",
                "error"
            )

            return render_template(
                "courses/add.html"
            )


        # -------------------------------------------------
        # Insert
        # -------------------------------------------------

        conn = get_connection()
        cur = conn.cursor()

        try:

            cur.execute("""
                SELECT
                    id

                FROM courses

                WHERE
                    institution_id = %s
                    AND LOWER(course_name) = LOWER(%s)
            """, (
                institution_id,
                course_name
            ))

            existing = cur.fetchone()

            if existing:

                flash(
                    "This course already exists.",
                    "error"
                )

                return render_template(
                    "courses/add.html"
                )


            cur.execute("""
                INSERT INTO courses
                (
                    institution_id,
                    course_name,
                    course_code,
                    description,
                    is_active
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    TRUE
                )
            """, (
                institution_id,
                course_name,
                course_code or None,
                description or None
            ))

            conn.commit()

            flash(
                "Course added successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "courses.course_list"
                )
            )

        except Exception:

            conn.rollback()
            raise

        finally:

            cur.close()
            conn.close()


    return render_template(
        "courses/add.html"
    )


# =========================================================
# Edit Course
# =========================================================

@courses.route(
    "/courses/edit/<int:id>",
    methods=["GET", "POST"]
)
def edit_course(id):

    if session.get("role") != "institution_admin":
        return "Unauthorized", 403

    institution_id = session.get("institution_id")

    if not institution_id:
        return "Unauthorized", 403

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
        """, (
            id,
            institution_id
        ))

        course = cur.fetchone()

        if not course:

            flash(
                "Course not found.",
                "error"
            )

            return redirect(
                url_for(
                    "courses.course_list"
                )
            )


        if request.method == "POST":

            course_name = request.form.get(
                "course_name",
                ""
            ).strip()

            course_code = request.form.get(
                "course_code",
                ""
            ).strip()

            description = request.form.get(
                "description",
                ""
            ).strip()


            if not course_name:

                flash(
                    "Course name is required.",
                    "error"
                )

                return render_template(
                    "courses/edit.html",
                    course=course
                )


            # ---------------------------------------------
            # Duplicate check
            # ---------------------------------------------

            cur.execute("""
                SELECT
                    id

                FROM courses

                WHERE
                    institution_id = %s
                    AND LOWER(course_name) = LOWER(%s)
                    AND id != %s
            """, (
                institution_id,
                course_name,
                id
            ))

            duplicate = cur.fetchone()

            if duplicate:

                flash(
                    "Another course with this name already exists.",
                    "error"
                )

                return render_template(
                    "courses/edit.html",
                    course=course
                )


            cur.execute("""
                UPDATE courses

                SET
                    course_name = %s,
                    course_code = %s,
                    description = %s,
                    updated_at = CURRENT_TIMESTAMP

                WHERE
                    id = %s
                    AND institution_id = %s
            """, (
                course_name,
                course_code or None,
                description or None,
                id,
                institution_id
            ))

            conn.commit()

            flash(
                "Course updated successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "courses.course_list"
                )
            )


        return render_template(
            "courses/edit.html",
            course=course
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# Toggle Course Status
# =========================================================

@courses.route(
    "/courses/toggle/<int:id>",
    methods=["POST"]
)
def toggle_course(id):

    if session.get("role") != "institution_admin":
        return "Unauthorized", 403

    institution_id = session.get(
        "institution_id"
    )

    if not institution_id:
        return "Unauthorized", 403

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            UPDATE courses

            SET
                is_active = NOT is_active,
                updated_at = CURRENT_TIMESTAMP

            WHERE
                id = %s
                AND institution_id = %s

            RETURNING
                course_name,
                is_active
        """, (
            id,
            institution_id
        ))

        course = cur.fetchone()

        if not course:

            conn.rollback()

            flash(
                "Course not found.",
                "error"
            )

            return redirect(
                url_for(
                    "courses.course_list"
                )
            )


        conn.commit()


        if course["is_active"]:

            flash(
                f"{course['course_name']} activated successfully.",
                "success"
            )

        else:

            flash(
                f"{course['course_name']} deactivated successfully.",
                "success"
            )


        return redirect(
            url_for(
                "courses.course_list"
            )
        )

    except Exception:

        conn.rollback()
        raise

    finally:

        cur.close()
        conn.close()