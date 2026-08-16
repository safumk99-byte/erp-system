from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from database.db import get_connection


# =========================================================
# Helpers
# =========================================================

def _get_institution_id():

    return session.get(
        "institution_id"
    )


# =========================================================
# Get Active Courses
# =========================================================

def _get_courses(cur, institution_id):

    cur.execute("""
        SELECT
            id,
            course_name,
            course_code

        FROM courses

        WHERE
            institution_id = %s
            AND is_active = TRUE

        ORDER BY
            course_name ASC
    """, (
        institution_id,
    ))

    return cur.fetchall()


# =========================================================
# Verify Course
# =========================================================

def _verify_course(
    cur,
    course_id,
    institution_id
):

    if not course_id:

        return True

    cur.execute("""
        SELECT
            id

        FROM courses

        WHERE
            id = %s
            AND institution_id = %s
            AND is_active = TRUE

        LIMIT 1
    """, (
        course_id,
        institution_id
    ))

    return bool(
        cur.fetchone()
    )


# =========================================================
# 1. List Classes
# =========================================================

def list_classes():

    search = request.args.get(
        "search",
        ""
    ).strip()

    institution_id = _get_institution_id()

    if not institution_id:

        return "Unauthorized", 403


    conn = get_connection()
    cur = conn.cursor()

    try:

        # -------------------------------------------------
        # Search
        # -------------------------------------------------

        if search:

            cur.execute("""
                SELECT
                    c.*,
                    co.course_name,
                    co.course_code

                FROM classes c

                LEFT JOIN courses co
                    ON co.id = c.course_id
                    AND co.institution_id = c.institution_id

                WHERE
                    c.institution_id = %s
                    AND c.class_name ILIKE %s

                ORDER BY
                    c.id DESC
            """, (
                institution_id,
                f"%{search}%"
            ))

        # -------------------------------------------------
        # All Classes
        # -------------------------------------------------

        else:

            cur.execute("""
                SELECT
                    c.*,
                    co.course_name,
                    co.course_code

                FROM classes c

                LEFT JOIN courses co
                    ON co.id = c.course_id
                    AND co.institution_id = c.institution_id

                WHERE
                    c.institution_id = %s

                ORDER BY
                    c.id DESC
            """, (
                institution_id,
            ))


        classes = cur.fetchall()


        return render_template(
            "classes/list.html",
            classes=classes,
            search=search
        )


    finally:

        cur.close()
        conn.close()


# =========================================================
# 2. Add Class
# =========================================================

def add_class():

    institution_id = _get_institution_id()

    if not institution_id:

        return "Unauthorized", 403


    conn = get_connection()
    cur = conn.cursor()

    try:

        # =================================================
        # POST
        # =================================================

        if request.method == "POST":

            class_name = request.form.get(
                "class_name",
                ""
            ).strip()

            description = request.form.get(
                "description",
                ""
            ).strip()

            course_id = request.form.get(
                "course_id",
                ""
            ).strip()


            # -------------------------------------------------
            # Validate Class Name
            # -------------------------------------------------

            if not class_name:

                flash(
                    "Class name is required.",
                    "error"
                )

                courses = _get_courses(
                    cur,
                    institution_id
                )

                return render_template(
                    "classes/add.html",
                    courses=courses
                )


            # -------------------------------------------------
            # Course ID
            # -------------------------------------------------

            if course_id:

                try:

                    course_id = int(
                        course_id
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    flash(
                        "Invalid course selected.",
                        "error"
                    )

                    courses = _get_courses(
                        cur,
                        institution_id
                    )

                    return render_template(
                        "classes/add.html",
                        courses=courses
                    )

            else:

                course_id = None


            # -------------------------------------------------
            # Verify Course
            # -------------------------------------------------

            if course_id is not None:

                if not _verify_course(
                    cur,
                    course_id,
                    institution_id
                ):

                    flash(
                        "Selected course is invalid or inactive.",
                        "error"
                    )

                    courses = _get_courses(
                        cur,
                        institution_id
                    )

                    return render_template(
                        "classes/add.html",
                        courses=courses
                    )


            # -------------------------------------------------
            # Duplicate Check
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    id

                FROM classes

                WHERE
                    institution_id = %s
                    AND LOWER(class_name) = LOWER(%s)

                LIMIT 1
            """, (
                institution_id,
                class_name
            ))

            if cur.fetchone():

                flash(
                    "Class already exists.",
                    "error"
                )

                courses = _get_courses(
                    cur,
                    institution_id
                )

                return render_template(
                    "classes/add.html",
                    courses=courses
                )


            # -------------------------------------------------
            # Insert
            # -------------------------------------------------

            cur.execute("""
                INSERT INTO classes
                (
                    institution_id,
                    course_id,
                    class_name,
                    description
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                institution_id,
                course_id,
                class_name,
                description
            ))


            conn.commit()


            flash(
                "Class added successfully.",
                "success"
            )


            return redirect(
                url_for(
                    "classes.class_list"
                )
            )


        # =================================================
        # GET
        # =================================================

        courses = _get_courses(
            cur,
            institution_id
        )


        return render_template(
            "classes/add.html",
            courses=courses
        )


    except Exception:

        conn.rollback()

        raise


    finally:

        cur.close()
        conn.close()


# =========================================================
# 3. Edit Class
# =========================================================

def edit_class(id):

    institution_id = _get_institution_id()

    if not institution_id:

        return "Unauthorized", 403


    conn = get_connection()
    cur = conn.cursor()

    try:

        # =================================================
        # Get Existing Class
        # =================================================

        cur.execute("""
            SELECT
                c.*,
                co.course_name,
                co.course_code

            FROM classes c

            LEFT JOIN courses co
                ON co.id = c.course_id
                AND co.institution_id = c.institution_id

            WHERE
                c.id = %s
                AND c.institution_id = %s

            LIMIT 1
        """, (
            id,
            institution_id
        ))

        class_item = cur.fetchone()


        if not class_item:

            flash(
                "Class not found.",
                "error"
            )

            return redirect(
                url_for(
                    "classes.class_list"
                )
            )


        # =================================================
        # POST
        # =================================================

        if request.method == "POST":

            class_name = request.form.get(
                "class_name",
                ""
            ).strip()

            description = request.form.get(
                "description",
                ""
            ).strip()

            course_id = request.form.get(
                "course_id",
                ""
            ).strip()


            # -------------------------------------------------
            # Validate Class Name
            # -------------------------------------------------

            if not class_name:

                flash(
                    "Class name is required.",
                    "error"
                )

                courses = _get_courses(
                    cur,
                    institution_id
                )

                return render_template(
                    "classes/edit.html",
                    class_item=class_item,
                    courses=courses
                )


            # -------------------------------------------------
            # Course ID
            # -------------------------------------------------

            if course_id:

                try:

                    course_id = int(
                        course_id
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    flash(
                        "Invalid course selected.",
                        "error"
                    )

                    courses = _get_courses(
                        cur,
                        institution_id
                    )

                    return render_template(
                        "classes/edit.html",
                        class_item=class_item,
                        courses=courses
                    )

            else:

                course_id = None


            # -------------------------------------------------
            # Verify Course
            # -------------------------------------------------

            if course_id is not None:

                if not _verify_course(
                    cur,
                    course_id,
                    institution_id
                ):

                    flash(
                        "Selected course is invalid or inactive.",
                        "error"
                    )

                    courses = _get_courses(
                        cur,
                        institution_id
                    )

                    return render_template(
                        "classes/edit.html",
                        class_item=class_item,
                        courses=courses
                    )


            # -------------------------------------------------
            # Duplicate Check
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    id

                FROM classes

                WHERE
                    institution_id = %s
                    AND LOWER(class_name) = LOWER(%s)
                    AND id != %s

                LIMIT 1
            """, (
                institution_id,
                class_name,
                id
            ))


            if cur.fetchone():

                flash(
                    "Class already exists.",
                    "error"
                )

                courses = _get_courses(
                    cur,
                    institution_id
                )

                return render_template(
                    "classes/edit.html",
                    class_item=class_item,
                    courses=courses
                )


            # -------------------------------------------------
            # Update
            # -------------------------------------------------

            cur.execute("""
                UPDATE classes

                SET
                    course_id = %s,
                    class_name = %s,
                    description = %s,
                    updated_at = NOW()

                WHERE
                    id = %s
                    AND institution_id = %s
            """, (
                course_id,
                class_name,
                description,
                id,
                institution_id
            ))


            conn.commit()


            flash(
                "Class updated successfully.",
                "success"
            )


            return redirect(
                url_for(
                    "classes.class_list"
                )
            )


        # =================================================
        # GET
        # =================================================

        courses = _get_courses(
            cur,
            institution_id
        )


        return render_template(
            "classes/edit.html",
            class_item=class_item,
            courses=courses
        )


    except Exception:

        conn.rollback()

        raise


    finally:

        cur.close()
        conn.close()


# =========================================================
# 4. Toggle Class Status
# =========================================================

def toggle_class_status(id):

    institution_id = _get_institution_id()

    if not institution_id:

        return "Unauthorized", 403


    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT
                is_active

            FROM classes

            WHERE
                id = %s
                AND institution_id = %s

            LIMIT 1
        """, (
            id,
            institution_id
        ))


        class_item = cur.fetchone()


        if not class_item:

            flash(
                "Class not found.",
                "error"
            )

            return redirect(
                url_for(
                    "classes.class_list"
                )
            )


        new_status = not class_item[
            "is_active"
        ]


        cur.execute("""
            UPDATE classes

            SET
                is_active = %s,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
        """, (
            new_status,
            id,
            institution_id
        ))


        conn.commit()


        if new_status:

            flash(
                "Class activated successfully.",
                "success"
            )

        else:

            flash(
                "Class deactivated successfully.",
                "success"
            )


        return redirect(
            url_for(
                "classes.class_list"
            )
        )


    except Exception:

        conn.rollback()

        raise


    finally:

        cur.close()
        conn.close()


# =========================================================
# 5. View Students Of Class
# =========================================================

def view_class_students(id):

    institution_id = _get_institution_id()

    if not institution_id:

        return "Unauthorized", 403


    conn = get_connection()
    cur = conn.cursor()

    try:

        # -------------------------------------------------
        # Get Class
        # -------------------------------------------------

        cur.execute("""
            SELECT
                c.id,
                c.class_name,
                c.description,
                c.is_active,
                c.course_id,
                co.course_name

            FROM classes c

            LEFT JOIN courses co
                ON co.id = c.course_id
                AND co.institution_id = c.institution_id

            WHERE
                c.id = %s
                AND c.institution_id = %s

            LIMIT 1
        """, (
            id,
            institution_id
        ))


        class_item = cur.fetchone()


        if not class_item:

            flash(
                "Class not found.",
                "error"
            )

            return redirect(
                url_for(
                    "classes.class_list"
                )
            )


        # -------------------------------------------------
        # Get Students
        # -------------------------------------------------

        cur.execute("""
            SELECT
                id,
                admission_no,
                full_name,
                photo,
                is_active

            FROM students

            WHERE
                institution_id = %s
                AND class_id = %s

            ORDER BY
                full_name ASC
        """, (
            institution_id,
            id
        ))


        students = cur.fetchall()


        return render_template(
            "classes/students.html",
            class_item=class_item,
            students=students
        )


    finally:

        cur.close()
        conn.close()


# =========================================================
# 6. View Students Of Class
# =========================================================

def class_students(class_id):

    institution_id = _get_institution_id()

    if not institution_id:

        return "Unauthorized", 403


    conn = get_connection()
    cur = conn.cursor()

    try:

        # -------------------------------------------------
        # Verify Class
        # -------------------------------------------------

        cur.execute("""
            SELECT
                c.id,
                c.class_name,
                c.description,
                c.is_active,
                c.course_id,
                co.course_name

            FROM classes c

            LEFT JOIN courses co
                ON co.id = c.course_id
                AND co.institution_id = c.institution_id

            WHERE
                c.id = %s
                AND c.institution_id = %s

            LIMIT 1
        """, (
            class_id,
            institution_id
        ))


        class_item = cur.fetchone()


        if not class_item:

            flash(
                "Class not found.",
                "error"
            )

            return redirect(
                url_for(
                    "classes.class_list"
                )
            )


        # -------------------------------------------------
        # Get Students
        # -------------------------------------------------

        cur.execute("""
            SELECT
                s.id,
                s.admission_no,
                s.full_name,
                s.gender,
                s.photo,
                s.is_active

            FROM students s

            WHERE
                s.class_id = %s
                AND s.institution_id = %s

            ORDER BY
                s.full_name ASC
        """, (
            class_id,
            institution_id
        ))


        students = cur.fetchall()


        return render_template(
            "classes/students.html",
            class_item=class_item,
            students=students
        )


    finally:

        cur.close()
        conn.close()