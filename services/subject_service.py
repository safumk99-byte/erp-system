from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
    jsonify
)

from database.db import get_connection



# =========================================================
# Helpers
# =========================================================

def _institution_id():

    return session.get("institution_id")


def _redirect_to_list():

    return redirect(
        url_for("subjects.subject_list")
    )


def _portal_redirect():

    return redirect(
        url_for("portal.index")
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
# Get Classes Of Course
# =========================================================

def _get_course_classes(
    cur,
    institution_id,
    course_id,
    include_class_id=None
):

    if not course_id:

        return []


    if include_class_id:

        cur.execute("""
            SELECT
                id,
                class_name,
                course_id

            FROM classes

            WHERE
                institution_id = %s
                AND course_id = %s
                AND (
                    is_active = TRUE
                    OR id = %s
                )

            ORDER BY
                class_name ASC
        """, (
            institution_id,
            course_id,
            include_class_id
        ))

    else:

        cur.execute("""
            SELECT
                id,
                class_name,
                course_id

            FROM classes

            WHERE
                institution_id = %s
                AND course_id = %s
                AND is_active = TRUE

            ORDER BY
                class_name ASC
        """, (
            institution_id,
            course_id
        ))

    return cur.fetchall()


# =========================================================
# Validate Course
# =========================================================

def _valid_course(
    cur,
    institution_id,
    course_id
):

    if not course_id:

        return None


    try:

        course_id = int(course_id)

    except (
        ValueError,
        TypeError
    ):

        return None


    cur.execute("""
        SELECT
            id,
            course_name,
            course_code

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

    return cur.fetchone()


# =========================================================
# Validate Class Belongs To Course
# =========================================================

def _valid_class(
    cur,
    institution_id,
    class_id,
    course_id
):

    if not class_id or not course_id:

        return None


    try:

        class_id = int(class_id)
        course_id = int(course_id)

    except (
        ValueError,
        TypeError
    ):

        return None


    cur.execute("""
        SELECT
            id,
            class_name,
            course_id

        FROM classes

        WHERE
            id = %s
            AND institution_id = %s
            AND course_id = %s
            AND is_active = TRUE

        LIMIT 1
    """, (
        class_id,
        institution_id,
        course_id
    ))

    return cur.fetchone()


# =========================================================
# 1. List Subjects
# =========================================================

def list_subjects():

    institution_id = _institution_id()

    if not institution_id:

        flash(
            "Institution information is missing.",
            "error"
        )

        return _portal_redirect()


    search = request.args.get(
        "search",
        ""
    ).strip()


    conn = None
    cur = None


    try:

        conn = get_connection()
        cur = conn.cursor()


        query = """
            SELECT
                subjects.id,
                subjects.institution_id,
                subjects.class_id,
                subjects.subject_name,
                subjects.description,
                subjects.is_active,
                subjects.created_at,
                subjects.updated_at,

                classes.class_name,

                courses.id AS course_id,
                courses.course_name,
                courses.course_code

            FROM subjects

            JOIN classes
                ON subjects.class_id = classes.id
                AND classes.institution_id = subjects.institution_id

            LEFT JOIN courses
                ON classes.course_id = courses.id
                AND courses.institution_id = subjects.institution_id

            WHERE
                subjects.institution_id = %s
        """


        params = [
            institution_id
        ]


        if search:

            query += """
                AND (
                    subjects.subject_name ILIKE %s
                    OR classes.class_name ILIKE %s
                    OR courses.course_name ILIKE %s
                )
            """

            search_value = (
                f"%{search}%"
            )

            params.extend([
                search_value,
                search_value,
                search_value
            ])


        query += """
            ORDER BY
                courses.course_name,
                classes.class_name,
                subjects.subject_name
        """


        cur.execute(
            query,
            tuple(params)
        )


        subjects = cur.fetchall()


        return render_template(
            "subjects/list.html",
            subjects=subjects,
            search=search
        )


    except Exception:

        if conn:
            conn.rollback()

        flash(
            "Unable to load subjects.",
            "error"
        )

        return _redirect_to_list()


    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# 2. View All Subjects
# =========================================================

def view_all_subjects():

    institution_id = _institution_id()

    if not institution_id:

        flash(
            "Institution information is missing.",
            "error"
        )

        return _portal_redirect()


    search = request.args.get(
        "search",
        ""
    ).strip()


    conn = None
    cur = None


    try:

        conn = get_connection()
        cur = conn.cursor()


        query = """
            SELECT
                subjects.id,
                subjects.institution_id,
                subjects.class_id,
                subjects.subject_name,
                subjects.description,
                subjects.is_active,

                classes.class_name,

                courses.id AS course_id,
                courses.course_name,
                courses.course_code

            FROM subjects

            JOIN classes
                ON subjects.class_id = classes.id
                AND classes.institution_id = subjects.institution_id

            LEFT JOIN courses
                ON classes.course_id = courses.id
                AND courses.institution_id = subjects.institution_id

            WHERE
                subjects.institution_id = %s
        """


        params = [
            institution_id
        ]


        if search:

            query += """
                AND (
                    subjects.subject_name ILIKE %s
                    OR classes.class_name ILIKE %s
                    OR courses.course_name ILIKE %s
                )
            """

            search_value = (
                f"%{search}%"
            )

            params.extend([
                search_value,
                search_value,
                search_value
            ])


        query += """
            ORDER BY
                courses.course_name,
                classes.class_name,
                subjects.subject_name
        """


        cur.execute(
            query,
            tuple(params)
        )


        subjects = cur.fetchall()


        # -------------------------------------------------
        # Assigned Staff
        # -------------------------------------------------

        subject_ids = [
            subject["id"]
            for subject in subjects
        ]


        staff_by_subject = {}


        if subject_ids:

            cur.execute("""
                SELECT
                    ss.subject_id,
                    u.id AS staff_id,
                    u.full_name,
                    u.username

                FROM staff_subjects ss

                JOIN users u
                    ON ss.staff_id = u.id
                    AND u.institution_id = ss.institution_id

                WHERE
                    ss.institution_id = %s
                    AND ss.subject_id = ANY(%s)
                    AND ss.is_active = TRUE
                    AND u.is_active = TRUE

                ORDER BY
                    u.full_name
            """, (
                institution_id,
                subject_ids
            ))


            assigned_staff = cur.fetchall()


            for staff in assigned_staff:

                subject_id = (
                    staff["subject_id"]
                )


                if subject_id not in staff_by_subject:

                    staff_by_subject[
                        subject_id
                    ] = []


                staff_by_subject[
                    subject_id
                ].append(
                    staff
                )


        return render_template(
            "subjects/view.html",
            subjects=subjects,
            staff_by_subject=staff_by_subject,
            search=search
        )


    except Exception:

        if conn:
            conn.rollback()

        flash(
            "Unable to load subjects.",
            "error"
        )

        return _redirect_to_list()


    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# 3. Add Subject
# =========================================================

def add_subject():

    institution_id = _institution_id()


    if not institution_id:

        flash(
            "Institution information is missing.",
            "error"
        )

        return _portal_redirect()


    conn = None
    cur = None


    try:

        conn = get_connection()
        cur = conn.cursor()


        # -------------------------------------------------
        # Courses
        # -------------------------------------------------

        courses = _get_courses(
            cur,
            institution_id
        )


        # -------------------------------------------------
        # Selected Course
        # -------------------------------------------------

        selected_course_id = request.values.get(
            "course_id",
            ""
        ).strip()


        selected_class_id = request.values.get(
            "class_id",
            ""
        ).strip()


        # -------------------------------------------------
        # Classes
        # -------------------------------------------------

        classes = _get_course_classes(
            cur,
            institution_id,
            selected_course_id
        )


        # -------------------------------------------------
        # GET
        # -------------------------------------------------

        if request.method == "GET":

            return render_template(
                "subjects/add.html",

                courses=courses,

                classes=classes,

                selected_course_id=selected_course_id,

                selected_class_id=selected_class_id
            )


        # -------------------------------------------------
        # POST
        # -------------------------------------------------

        subject_name = request.form.get(
            "subject_name",
            ""
        ).strip()


        description = request.form.get(
            "description",
            ""
        ).strip()


        # -------------------------------------------------
        # Course Validation
        # -------------------------------------------------

        course = _valid_course(
            cur,
            institution_id,
            selected_course_id
        )


        if not course:

            flash(
                "Please select a valid course.",
                "error"
            )

            return render_template(
                "subjects/add.html",

                courses=courses,

                classes=classes,

                selected_course_id=selected_course_id,

                selected_class_id=selected_class_id
            )


        # -------------------------------------------------
        # Class Validation
        # -------------------------------------------------

        valid_class = _valid_class(
            cur,
            institution_id,
            selected_class_id,
            selected_course_id
        )


        if not valid_class:

            flash(
                "Please select a valid class for the selected course.",
                "error"
            )

            classes = _get_course_classes(
                cur,
                institution_id,
                selected_course_id
            )


            return render_template(
                "subjects/add.html",

                courses=courses,

                classes=classes,

                selected_course_id=selected_course_id,

                selected_class_id=selected_class_id
            )


        # -------------------------------------------------
        # Subject Validation
        # -------------------------------------------------

        if not subject_name:

            flash(
                "Subject name is required.",
                "error"
            )

            return render_template(
                "subjects/add.html",

                courses=courses,

                classes=classes,

                selected_course_id=selected_course_id,

                selected_class_id=selected_class_id
            )


        # -------------------------------------------------
        # Duplicate Check
        # -------------------------------------------------

        cur.execute("""
            SELECT
                id

            FROM subjects

            WHERE
                institution_id = %s
                AND class_id = %s
                AND LOWER(subject_name) = LOWER(%s)

            LIMIT 1
        """, (
            institution_id,
            selected_class_id,
            subject_name
        ))


        if cur.fetchone():

            flash(
                "Subject already exists for this class.",
                "error"
            )

            return render_template(
                "subjects/add.html",

                courses=courses,

                classes=classes,

                selected_course_id=selected_course_id,

                selected_class_id=selected_class_id
            )


        # -------------------------------------------------
        # Insert
        # -------------------------------------------------

        cur.execute("""
            INSERT INTO subjects
            (
                institution_id,
                class_id,
                subject_name,
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
            selected_class_id,
            subject_name,
            description
        ))


        conn.commit()


        flash(
            "Subject added successfully.",
            "success"
        )


        return _redirect_to_list()


    except Exception:

        if conn:
            conn.rollback()

        flash(
            "Unable to add subject.",
            "error"
        )


        return render_template(
            "subjects/add.html",

            courses=(
                courses
                if "courses" in locals()
                else []
            ),

            classes=(
                classes
                if "classes" in locals()
                else []
            ),

            selected_course_id=(
                selected_course_id
                if "selected_course_id" in locals()
                else ""
            ),

            selected_class_id=(
                selected_class_id
                if "selected_class_id" in locals()
                else ""
            )
        )


    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# 4. Edit Subject
# =========================================================

def edit_subject(id):

    institution_id = _institution_id()

    if not institution_id:

        flash(
            "Institution information is missing.",
            "error"
        )

        return _portal_redirect()


    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()


        # =================================================
        # Get Subject + Current Course
        # =================================================

        cur.execute("""
            SELECT
                s.id,
                s.institution_id,
                s.class_id,
                s.subject_name,
                s.description,
                s.is_active,
                s.created_at,
                s.updated_at,

                c.class_name,
                c.course_id,

                co.course_name,
                co.course_code

            FROM subjects s

            JOIN classes c
                ON s.class_id = c.id
                AND c.institution_id = s.institution_id

            LEFT JOIN courses co
                ON c.course_id = co.id
                AND co.institution_id = s.institution_id

            WHERE
                s.id = %s
                AND s.institution_id = %s

            LIMIT 1
        """, (
            id,
            institution_id
        ))

        subject = cur.fetchone()


        if not subject:

            flash(
                "Subject not found.",
                "error"
            )

            return _redirect_to_list()


        # =================================================
        # Current Course ID
        # =================================================

        selected_course_id = (
            subject["course_id"]
            if subject["course_id"]
            else ""
        )


        selected_class_id = (
            subject["class_id"]
            if subject["class_id"]
            else ""
        )


        # =================================================
        # Load Active Courses
        # =================================================

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

        courses = cur.fetchall()


        # =================================================
        # Load Classes Of Current Course
        # =================================================

        classes = []


        if selected_course_id:

            cur.execute("""
                SELECT
                    id,
                    class_name,
                    course_id

                FROM classes

                WHERE
                    institution_id = %s
                    AND course_id = %s
                    AND is_active = TRUE

                ORDER BY
                    class_name ASC
            """, (
                institution_id,
                selected_course_id
            ))

            classes = cur.fetchall()


        # =================================================
        # GET
        # =================================================

        if request.method == "GET":

            return render_template(
                "subjects/edit.html",

                subject=subject,

                courses=courses,

                classes=classes,

                selected_course_id=selected_course_id,

                selected_class_id=selected_class_id
            )


        # =================================================
        # POST
        # =================================================

        course_id = request.form.get(
            "course_id",
            ""
        ).strip()


        class_id = request.form.get(
            "class_id",
            ""
        ).strip()


        subject_name = request.form.get(
            "subject_name",
            ""
        ).strip()


        description = request.form.get(
            "description",
            ""
        ).strip()


        # =================================================
        # Validation
        # =================================================

        if not course_id:

            flash(
                "Please select a course.",
                "error"
            )

            return render_template(
                "subjects/edit.html",

                subject=subject,

                courses=courses,

                classes=classes,

                selected_course_id=course_id,

                selected_class_id=class_id
            )


        if not class_id:

            flash(
                "Please select a class.",
                "error"
            )

            return render_template(
                "subjects/edit.html",

                subject=subject,

                courses=courses,

                classes=classes,

                selected_course_id=course_id,

                selected_class_id=class_id
            )


        if not subject_name:

            flash(
                "Subject name is required.",
                "error"
            )

            return render_template(
                "subjects/edit.html",

                subject=subject,

                courses=courses,

                classes=classes,

                selected_course_id=course_id,

                selected_class_id=class_id
            )


        if len(subject_name) > 150:

            flash(
                "Subject name is too long.",
                "error"
            )

            return render_template(
                "subjects/edit.html",

                subject=subject,

                courses=courses,

                classes=classes,

                selected_course_id=course_id,

                selected_class_id=class_id
            )


        # =================================================
        # Verify Course
        # =================================================

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

        valid_course = cur.fetchone()


        if not valid_course:

            flash(
                "Selected course is invalid or inactive.",
                "error"
            )

            return render_template(
                "subjects/edit.html",

                subject=subject,

                courses=courses,

                classes=classes,

                selected_course_id=course_id,

                selected_class_id=class_id
            )


        # =================================================
        # Verify Class Belongs To Selected Course
        # =================================================

        cur.execute("""
            SELECT
                id,
                class_name,
                course_id

            FROM classes

            WHERE
                id = %s
                AND institution_id = %s
                AND course_id = %s
                AND is_active = TRUE

            LIMIT 1
        """, (
            class_id,
            institution_id,
            course_id
        ))

        valid_class = cur.fetchone()


        if not valid_class:

            flash(
                "Selected class does not belong to the selected course.",
                "error"
            )

            # Reload correct classes

            cur.execute("""
                SELECT
                    id,
                    class_name,
                    course_id

                FROM classes

                WHERE
                    institution_id = %s
                    AND course_id = %s
                    AND is_active = TRUE

                ORDER BY
                    class_name ASC
            """, (
                institution_id,
                course_id
            ))

            classes = cur.fetchall()


            return render_template(
                "subjects/edit.html",

                subject=subject,

                courses=courses,

                classes=classes,

                selected_course_id=course_id,

                selected_class_id=class_id
            )


        # =================================================
        # Duplicate Subject Check
        # =================================================

        cur.execute("""
            SELECT
                id

            FROM subjects

            WHERE
                institution_id = %s
                AND class_id = %s
                AND LOWER(subject_name) = LOWER(%s)
                AND id != %s

            LIMIT 1
        """, (
            institution_id,
            class_id,
            subject_name,
            id
        ))

        duplicate = cur.fetchone()


        if duplicate:

            flash(
                "Subject already exists for this class.",
                "error"
            )

            return render_template(
                "subjects/edit.html",

                subject=subject,

                courses=courses,

                classes=classes,

                selected_course_id=course_id,

                selected_class_id=class_id
            )


        # =================================================
        # Update Subject
        # =================================================

        cur.execute("""
            UPDATE subjects

            SET
                class_id = %s,
                subject_name = %s,
                description = %s,
                updated_at = CURRENT_TIMESTAMP

            WHERE
                id = %s
                AND institution_id = %s
        """, (
            class_id,
            subject_name,
            description or None,
            id,
            institution_id
        ))


        conn.commit()


        flash(
            "Subject updated successfully.",
            "success"
        )


        return _redirect_to_list()


    except Exception:

        if conn:
            conn.rollback()

        flash(
            "Unable to update subject.",
            "error"
        )

        return _redirect_to_list()


    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# 5. Toggle Subject Status
# =========================================================

def toggle_subject_status(id):

    institution_id = _institution_id()


    if not institution_id:

        flash(
            "Institution information is missing.",
            "error"
        )

        return _portal_redirect()


    conn = None
    cur = None


    try:

        conn = get_connection()
        cur = conn.cursor()


        cur.execute("""
            SELECT
                id,
                is_active

            FROM subjects

            WHERE
                id = %s
                AND institution_id = %s

            FOR UPDATE
        """, (
            id,
            institution_id
        ))


        subject = cur.fetchone()


        if not subject:

            flash(
                "Subject not found.",
                "error"
            )

            return _redirect_to_list()


        new_status = not subject["is_active"]


        cur.execute("""
            UPDATE subjects

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
                "Subject activated successfully.",
                "success"
            )

        else:

            flash(
                "Subject deactivated successfully.",
                "success"
            )


        return _redirect_to_list()


    except Exception:

        if conn:
            conn.rollback()

        flash(
            "Unable to change subject status.",
            "error"
        )

        return _redirect_to_list()


    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()
            
            
def get_course_classes_for_subject():

    institution_id = session.get("institution_id")

    if not institution_id:

        return jsonify({
            "classes": []
        }), 403


    course_id = request.args.get(
        "course_id",
        ""
    ).strip()


    if not course_id:

        return jsonify({
            "classes": []
        })


    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                class_name

            FROM classes

            WHERE
                institution_id = %s
                AND course_id = %s
                AND is_active = TRUE

            ORDER BY
                class_name ASC
        """, (
            institution_id,
            course_id
        ))

        classes = cur.fetchall()

        return jsonify({
            "classes": classes
        })

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()            