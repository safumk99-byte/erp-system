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
# Get Allowed Students
# =========================================================

def _get_students(cur):

    role = session.get("role")

    if role == "institution_admin":

        cur.execute("""
            SELECT
                id,
                admission_no,
                full_name

            FROM students

            WHERE
                institution_id = %s
                AND is_active = TRUE

            ORDER BY full_name
        """, (
            session["institution_id"],
        ))

    elif role == "staff":

        cur.execute("""
            SELECT DISTINCT
                s.id,
                s.admission_no,
                s.full_name

            FROM students s

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                s.institution_id = %s
                AND s.is_active = TRUE

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

            ORDER BY s.full_name
        """, (
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

    else:

        return []

    return cur.fetchall()


# =========================================================
# Verify Student Access
# =========================================================

def _student_is_allowed(cur, student_id):

    role = session.get("role")

    if role == "institution_admin":

        cur.execute("""
            SELECT
                id

            FROM students

            WHERE
                id = %s
                AND institution_id = %s
                AND is_active = TRUE
        """, (
            student_id,
            session["institution_id"]
        ))

    elif role == "staff":

        cur.execute("""
            SELECT
                s.id

            FROM students s

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                s.id = %s
                AND s.institution_id = %s
                AND s.is_active = TRUE

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE
        """, (
            student_id,
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

    else:

        return False

    return cur.fetchone() is not None


# =========================================================
# List Speakings
# =========================================================

def list_speakings():

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")

    query = """
        SELECT
            sp.*,
            s.full_name,
            s.admission_no

        FROM speaking_submissions sp

        JOIN students s
            ON sp.student_id = s.id

        WHERE
            sp.institution_id = %s
            AND s.institution_id = %s
    """

    params = [
        session["institution_id"],
        session["institution_id"]
    ]


    # -----------------------------------------------------
    # Staff → Assigned Students Only
    # -----------------------------------------------------

    if role == "staff":

        query += """
            AND EXISTS (
                SELECT 1

                FROM staff_classes sc

                WHERE
                    sc.institution_id = %s
                    AND sc.staff_id = %s
                    AND sc.class_id = s.class_id
                    AND sc.is_active = TRUE
            )
        """

        params.extend([
            session["institution_id"],
            session["user_id"]
        ])


    query += """
        ORDER BY sp.id DESC
    """


    cur.execute(
        query,
        tuple(params)
    )

    speakings = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "speaking/list.html",
        speakings=speakings
    )


# =========================================================
# Add Speaking
# =========================================================

def add_speaking():

    conn = get_connection()
    cur = conn.cursor()

    students = _get_students(cur)


    if request.method == "POST":

        student_id = request.form["student_id"]

        title = request.form[
            "title"
        ].strip()

        presentation_date = request.form.get(
            "presentation_date"
        )

        duration_minutes = request.form[
            "duration_minutes"
        ]

        description = request.form.get(
            "description",
            ""
        ).strip()


        # -------------------------------------------------
        # Verify Student Access
        # -------------------------------------------------

        if not _student_is_allowed(
            cur,
            student_id
        ):

            flash(
                "You do not have access to this student.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "speaking/add.html",
                students=students
            )


        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if not title:

            flash(
                "Presentation title is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "speaking/add.html",
                students=students
            )


        try:

            duration_minutes = int(
                duration_minutes
            )

        except (TypeError, ValueError):

            flash(
                "Invalid duration.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "speaking/add.html",
                students=students
            )


        if duration_minutes <= 0:

            flash(
                "Duration must be greater than zero.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "speaking/add.html",
                students=students
            )


        # Points are calculated only
        # after approval.

        points = 0


        cur.execute("""
            INSERT INTO speaking_submissions
            (
                institution_id,
                student_id,
                title,
                presentation_date,
                duration_minutes,
                description,
                points,
                status
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                'Pending'
            )

        """, (
            session["institution_id"],
            student_id,
            title,
            presentation_date or None,
            duration_minutes,
            description,
            points
        ))


        conn.commit()

        cur.close()
        conn.close()


        flash(
            "Speaking submission added successfully.",
            "success"
        )


        return redirect(
            url_for(
                "speaking.speaking_list"
            )
        )


    cur.close()
    conn.close()


    return render_template(
        "speaking/add.html",
        students=students
    )


# =========================================================
# Approve Speaking
# =========================================================

def approve_speaking(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    # -----------------------------------------------------
    # Verify Speaking + Student Access
    # -----------------------------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT
                sp.duration_minutes

            FROM speaking_submissions sp

            JOIN students s
                ON sp.student_id = s.id

            WHERE
                sp.id = %s
                AND sp.institution_id = %s
                AND s.institution_id = %s
                AND sp.status = 'Pending'
        """, (
            id,
            session["institution_id"],
            session["institution_id"]
        ))

    elif role == "staff":

        cur.execute("""
            SELECT
                sp.duration_minutes

            FROM speaking_submissions sp

            JOIN students s
                ON sp.student_id = s.id

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                sp.id = %s
                AND sp.institution_id = %s
                AND s.institution_id = %s
                AND sp.status = 'Pending'

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE
        """, (
            id,
            session["institution_id"],
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    speaking = cur.fetchone()


    if not speaking:

        cur.close()
        conn.close()

        flash(
            "Speaking submission not found or you do not have permission to approve it.",
            "error"
        )

        return redirect(
            url_for(
                "speaking.speaking_list"
            )
        )


    duration_minutes = speaking[
        "duration_minutes"
    ]

    points = 0


    if duration_minutes >= 5:
        points = 5


    cur.execute("""
        UPDATE speaking_submissions

        SET
            status = 'Approved',
            points = %s,
            reviewed_by = %s,
            reviewed_at = NOW(),
            rejection_reason = NULL,
            updated_at = NOW()

        WHERE
            id = %s
            AND institution_id = %s
            AND status = 'Pending'

    """, (
        points,
        session.get("user_id"),
        id,
        session["institution_id"]
    ))


    conn.commit()

    cur.close()
    conn.close()


    flash(
        "Speaking submission approved.",
        "success"
    )


    return redirect(
        url_for(
            "speaking.speaking_list"
        )
    )


# =========================================================
# Reject Speaking
# =========================================================

def reject_speaking(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")

    reason = request.form.get(
        "rejection_reason",
        ""
    ).strip()


    if not reason:

        flash(
            "Rejection reason is required.",
            "error"
        )

        cur.close()
        conn.close()

        return redirect(
            url_for(
                "speaking.speaking_list"
            )
        )


    # -----------------------------------------------------
    # Verify Speaking + Student Access
    # -----------------------------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT
                sp.id

            FROM speaking_submissions sp

            JOIN students s
                ON sp.student_id = s.id

            WHERE
                sp.id = %s
                AND sp.institution_id = %s
                AND s.institution_id = %s
                AND sp.status = 'Pending'
        """, (
            id,
            session["institution_id"],
            session["institution_id"]
        ))

    elif role == "staff":

        cur.execute("""
            SELECT
                sp.id

            FROM speaking_submissions sp

            JOIN students s
                ON sp.student_id = s.id

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                sp.id = %s
                AND sp.institution_id = %s
                AND s.institution_id = %s
                AND sp.status = 'Pending'

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE
        """, (
            id,
            session["institution_id"],
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    speaking = cur.fetchone()


    if not speaking:

        cur.close()
        conn.close()

        flash(
            "Speaking submission not found or you do not have permission to reject it.",
            "error"
        )

        return redirect(
            url_for(
                "speaking.speaking_list"
            )
        )


    cur.execute("""
        UPDATE speaking_submissions

        SET
            status = 'Rejected',
            points = 0,
            reviewed_by = %s,
            reviewed_at = NOW(),
            rejection_reason = %s,
            updated_at = NOW()

        WHERE
            id = %s
            AND institution_id = %s
            AND status = 'Pending'

    """, (
        session.get("user_id"),
        reason,
        id,
        session["institution_id"]
    ))


    conn.commit()

    cur.close()
    conn.close()


    flash(
        "Speaking submission rejected.",
        "success"
    )


    return redirect(
        url_for(
            "speaking.speaking_list"
        )
    )


# =========================================================
# Edit Speaking
# =========================================================

def edit_speaking(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    # -----------------------------------------------------
    # Get Existing Pending Submission
    # -----------------------------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT
                sp.*

            FROM speaking_submissions sp

            JOIN students s
                ON sp.student_id = s.id

            WHERE
                sp.id = %s
                AND sp.institution_id = %s
                AND s.institution_id = %s
                AND sp.status = 'Pending'

        """, (
            id,
            session["institution_id"],
            session["institution_id"]
        ))

    elif role == "staff":

        cur.execute("""
            SELECT
                sp.*

            FROM speaking_submissions sp

            JOIN students s
                ON sp.student_id = s.id

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                sp.id = %s
                AND sp.institution_id = %s
                AND s.institution_id = %s
                AND sp.status = 'Pending'

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

        """, (
            id,
            session["institution_id"],
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    speaking = cur.fetchone()


    if not speaking:

        cur.close()
        conn.close()

        flash(
            "Speaking submission not found or cannot be edited.",
            "error"
        )

        return redirect(
            url_for(
                "speaking.speaking_list"
            )
        )


    # -----------------------------------------------------
    # Allowed Students
    # -----------------------------------------------------

    students = _get_students(cur)


    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        student_id = request.form["student_id"]

        title = request.form[
            "title"
        ].strip()

        presentation_date = request.form.get(
            "presentation_date"
        )

        duration_minutes = request.form[
            "duration_minutes"
        ]

        description = request.form.get(
            "description",
            ""
        ).strip()


        # -------------------------------------------------
        # Verify New Student Access
        # -------------------------------------------------

        if not _student_is_allowed(
            cur,
            student_id
        ):

            flash(
                "You do not have access to this student.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "speaking/edit.html",
                speaking=speaking,
                students=students
            )


        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if not title:

            flash(
                "Presentation title is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "speaking/edit.html",
                speaking=speaking,
                students=students
            )


        try:

            duration_minutes = int(
                duration_minutes
            )

        except (TypeError, ValueError):

            flash(
                "Invalid duration.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "speaking/edit.html",
                speaking=speaking,
                students=students
            )


        if duration_minutes <= 0:

            flash(
                "Duration must be greater than zero.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "speaking/edit.html",
                speaking=speaking,
                students=students
            )


        # -------------------------------------------------
        # Update
        # -------------------------------------------------

        cur.execute("""
            UPDATE speaking_submissions

            SET
                student_id = %s,
                title = %s,
                presentation_date = %s,
                duration_minutes = %s,
                description = %s,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
                AND status = 'Pending'

        """, (
            student_id,
            title,
            presentation_date or None,
            duration_minutes,
            description,
            id,
            session["institution_id"]
        ))


        conn.commit()

        cur.close()
        conn.close()


        flash(
            "Speaking submission updated successfully.",
            "success"
        )


        return redirect(
            url_for(
                "speaking.speaking_list"
            )
        )


    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    cur.close()
    conn.close()


    return render_template(
        "speaking/edit.html",
        speaking=speaking,
        students=students
    )