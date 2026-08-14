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

        if search:

            cur.execute("""
                SELECT
                    subjects.id,
                    subjects.institution_id,
                    subjects.class_id,
                    subjects.subject_name,
                    subjects.description,
                    subjects.is_active,
                    subjects.created_at,
                    subjects.updated_at,
                    classes.class_name

                FROM subjects

                JOIN classes
                    ON subjects.class_id = classes.id
                    AND classes.institution_id = subjects.institution_id

                WHERE
                    subjects.institution_id = %s
                    AND (
                        subjects.subject_name ILIKE %s
                        OR classes.class_name ILIKE %s
                    )

                ORDER BY
                    subjects.id DESC
            """, (
                institution_id,
                f"%{search}%",
                f"%{search}%"
            ))

        else:

            cur.execute("""
                SELECT
                    subjects.id,
                    subjects.institution_id,
                    subjects.class_id,
                    subjects.subject_name,
                    subjects.description,
                    subjects.is_active,
                    subjects.created_at,
                    subjects.updated_at,
                    classes.class_name

                FROM subjects

                JOIN classes
                    ON subjects.class_id = classes.id
                    AND classes.institution_id = subjects.institution_id

                WHERE
                    subjects.institution_id = %s

                ORDER BY
                    subjects.id DESC
            """, (
                institution_id,
            ))

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

        # -------------------------------------------------
        # Get all subjects
        #
        # Each subject is returned once.
        # Assigned staff are loaded separately below.
        # -------------------------------------------------

        if search:

            cur.execute("""
                SELECT
                    subjects.id,
                    subjects.institution_id,
                    subjects.class_id,
                    subjects.subject_name,
                    subjects.description,
                    subjects.is_active,
                    classes.class_name

                FROM subjects

                JOIN classes
                    ON subjects.class_id = classes.id
                    AND classes.institution_id = subjects.institution_id

                WHERE
                    subjects.institution_id = %s
                    AND (
                        subjects.subject_name ILIKE %s
                        OR classes.class_name ILIKE %s
                    )

                ORDER BY
                    classes.class_name,
                    subjects.subject_name
            """, (
                institution_id,
                f"%{search}%",
                f"%{search}%"
            ))

        else:

            cur.execute("""
                SELECT
                    subjects.id,
                    subjects.institution_id,
                    subjects.class_id,
                    subjects.subject_name,
                    subjects.description,
                    subjects.is_active,
                    classes.class_name

                FROM subjects

                JOIN classes
                    ON subjects.class_id = classes.id
                    AND classes.institution_id = subjects.institution_id

                WHERE
                    subjects.institution_id = %s

                ORDER BY
                    classes.class_name,
                    subjects.subject_name
            """, (
                institution_id,
            ))

        subjects = cur.fetchall()

        # -------------------------------------------------
        # Get assigned staff for each subject
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

                subject_id = staff["subject_id"]

                if subject_id not in staff_by_subject:

                    staff_by_subject[subject_id] = []

                staff_by_subject[subject_id].append(
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
        # Load active classes
        # -------------------------------------------------

        cur.execute("""
            SELECT
                id,
                class_name

            FROM classes

            WHERE
                institution_id = %s
                AND is_active = TRUE

            ORDER BY
                class_name
        """, (
            institution_id,
        ))

        classes = cur.fetchall()

        # -------------------------------------------------
        # GET
        # -------------------------------------------------

        if request.method == "GET":

            return render_template(
                "subjects/add.html",
                classes=classes
            )

        # -------------------------------------------------
        # POST
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if not class_id:

            flash(
                "Please select a class.",
                "error"
            )

            return render_template(
                "subjects/add.html",
                classes=classes
            )

        if not subject_name:

            flash(
                "Subject name is required.",
                "error"
            )

            return render_template(
                "subjects/add.html",
                classes=classes
            )

        # -------------------------------------------------
        # Verify class
        # -------------------------------------------------

        cur.execute("""
            SELECT
                id

            FROM classes

            WHERE
                id = %s
                AND institution_id = %s
                AND is_active = TRUE

            LIMIT 1
        """, (
            class_id,
            institution_id
        ))

        valid_class = cur.fetchone()

        if not valid_class:

            flash(
                "Selected class is invalid or inactive.",
                "error"
            )

            return render_template(
                "subjects/add.html",
                classes=classes
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
            class_id,
            subject_name
        ))

        if cur.fetchone():

            flash(
                "Subject already exists for this class.",
                "error"
            )

            return render_template(
                "subjects/add.html",
                classes=classes
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
            class_id,
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
            classes=classes if "classes" in locals() else []
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

        cur.execute("""
            SELECT
                id,
                institution_id,
                class_id,
                subject_name,
                description,
                is_active,
                created_at,
                updated_at

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

        cur.execute("""
            SELECT
                id,
                class_name

            FROM classes

            WHERE
                institution_id = %s
                AND (
                    is_active = TRUE
                    OR id = %s
                )

            ORDER BY
                class_name
        """, (
            institution_id,
            subject["class_id"]
        ))

        classes = cur.fetchall()

        if request.method == "GET":

            return render_template(
                "subjects/edit.html",
                subject=subject,
                classes=classes
            )

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

        if not class_id:

            flash(
                "Please select a class.",
                "error"
            )

            return render_template(
                "subjects/edit.html",
                subject=subject,
                classes=classes
            )

        if not subject_name:

            flash(
                "Subject name is required.",
                "error"
            )

            return render_template(
                "subjects/edit.html",
                subject=subject,
                classes=classes
            )

        cur.execute("""
            SELECT
                id

            FROM classes

            WHERE
                id = %s
                AND institution_id = %s
                AND is_active = TRUE

            LIMIT 1
        """, (
            class_id,
            institution_id
        ))

        valid_class = cur.fetchone()

        if not valid_class:

            flash(
                "Selected class is invalid or inactive.",
                "error"
            )

            return render_template(
                "subjects/edit.html",
                subject=subject,
                classes=classes
            )

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

        if cur.fetchone():

            flash(
                "Subject already exists for this class.",
                "error"
            )

            return render_template(
                "subjects/edit.html",
                subject=subject,
                classes=classes
            )

        cur.execute("""
            UPDATE subjects

            SET
                class_id = %s,
                subject_name = %s,
                description = %s,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
        """, (
            class_id,
            subject_name,
            description,
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