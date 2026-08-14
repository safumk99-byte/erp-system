from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from database.db import get_connection

from services.notification_service import notify_student_and_parent


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
# List Writings
# =========================================================

def list_writings():

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")

    query = """
        SELECT
            w.*,
            s.full_name,
            s.admission_no

        FROM writing_submissions w

        JOIN students s
            ON w.student_id = s.id

        WHERE
            w.institution_id = %s
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
        ORDER BY w.id DESC
    """


    cur.execute(
        query,
        tuple(params)
    )

    writings = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "writing/list.html",
        writings=writings
    )


# =========================================================
# Add Writing
# =========================================================

def add_writing():

    conn = get_connection()
    cur = conn.cursor()

    students = _get_students(cur)


    if request.method == "POST":

        student_id = request.form["student_id"]

        title = request.form[
            "title"
        ].strip()

        writing_type = request.form[
            "writing_type"
        ]

        pages = request.form["pages"]

        content = request.form[
            "content"
        ].strip()


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
                "writing/add.html",
                students=students
            )


        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if not title:

            flash(
                "Title is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "writing/add.html",
                students=students
            )


        if not content:

            flash(
                "Writing content is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "writing/add.html",
                students=students
            )


        try:

            pages = int(pages)

        except (TypeError, ValueError):

            flash(
                "Invalid page count.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "writing/add.html",
                students=students
            )


        if pages <= 0:

            flash(
                "Pages must be greater than zero.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "writing/add.html",
                students=students
            )


        # Points are calculated
        # only after approval.

        points = 0


        cur.execute("""
            INSERT INTO writing_submissions
            (
                institution_id,
                student_id,
                title,
                writing_type,
                pages,
                content,
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
            writing_type,
            pages,
            content,
            points
        ))


        conn.commit()

        cur.close()
        conn.close()


        flash(
            "Writing submission added successfully.",
            "success"
        )


        return redirect(
            url_for(
                "writing.writing_list"
            )
        )


    cur.close()
    conn.close()


    return render_template(
        "writing/add.html",
        students=students
    )


# =========================================================
# Approve Writing
# =========================================================

def approve_writing(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")
    institution_id = session.get("institution_id")
    user_id = session.get("user_id")


    # -----------------------------------------------------
    # Verify Writing + Student Access
    # -----------------------------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT
                w.student_id,
                w.writing_type,
                w.pages

            FROM writing_submissions w

            JOIN students s
                ON w.student_id = s.id

            WHERE
                w.id = %s
                AND w.institution_id = %s
                AND s.institution_id = %s
                AND w.status = 'Pending'

            FOR UPDATE
        """, (
            id,
            institution_id,
            institution_id
        ))


    elif role == "staff":

        cur.execute("""
            SELECT
                w.student_id,
                w.writing_type,
                w.pages

            FROM writing_submissions w

            JOIN students s
                ON w.student_id = s.id

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                w.id = %s
                AND w.institution_id = %s
                AND s.institution_id = %s
                AND w.status = 'Pending'

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

            FOR UPDATE
        """, (
            id,
            institution_id,
            institution_id,
            institution_id,
            user_id
        ))


    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    writing = cur.fetchone()


    if not writing:

        cur.close()
        conn.close()

        flash(
            "Writing submission not found or you do not have permission to approve it.",
            "error"
        )

        return redirect(
            url_for(
                "writing.writing_list"
            )
        )


    student_id = writing["student_id"]
    writing_type = writing["writing_type"]
    pages = writing["pages"]


    # -----------------------------------------------------
    # Calculate Points
    # -----------------------------------------------------

    points = 0


    if writing_type == "Fiction":

        if pages >= 1:

            points = 3


    elif writing_type == "Non-Fiction":

        if pages >= 4:

            points = 5

            extra_pages = pages - 4

            points += (
                extra_pages // 2
            )


    # -----------------------------------------------------
    # Approve Writing
    # -----------------------------------------------------

    cur.execute("""
        UPDATE writing_submissions

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
        user_id,
        id,
        institution_id
    ))


    # -----------------------------------------------------
    # Notification
    # -----------------------------------------------------

    notify_student_and_parent(
        student_id=student_id,
        module_name="Writing Skill",
        approved=True,
        remarks=None,
        institution_id=institution_id,
        cur=cur
    )


    # -----------------------------------------------------
    # Commit
    # -----------------------------------------------------

    conn.commit()


    cur.close()
    conn.close()


    flash(
        "Writing submission approved and notification sent.",
        "success"
    )


    return redirect(
        url_for(
            "writing.writing_list"
        )
    )


# =========================================================
# Reject Writing
# =========================================================

def reject_writing(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")
    institution_id = session.get("institution_id")
    user_id = session.get("user_id")


    reason = request.form.get(
        "rejection_reason",
        ""
    ).strip()


    # -----------------------------------------------------
    # Validate Reason
    # -----------------------------------------------------

    if not reason:

        flash(
            "Rejection reason is required.",
            "error"
        )

        cur.close()
        conn.close()

        return redirect(
            url_for(
                "writing.writing_list"
            )
        )


    # -----------------------------------------------------
    # Verify Writing + Student Access
    # -----------------------------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT
                w.id,
                w.student_id

            FROM writing_submissions w

            JOIN students s
                ON w.student_id = s.id

            WHERE
                w.id = %s
                AND w.institution_id = %s
                AND s.institution_id = %s
                AND w.status = 'Pending'

            FOR UPDATE
        """, (
            id,
            institution_id,
            institution_id
        ))


    elif role == "staff":

        cur.execute("""
            SELECT
                w.id,
                w.student_id

            FROM writing_submissions w

            JOIN students s
                ON w.student_id = s.id

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                w.id = %s
                AND w.institution_id = %s
                AND s.institution_id = %s
                AND w.status = 'Pending'

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

            FOR UPDATE
        """, (
            id,
            institution_id,
            institution_id,
            institution_id,
            user_id
        ))


    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    writing = cur.fetchone()


    if not writing:

        cur.close()
        conn.close()

        flash(
            "Writing submission not found or you do not have permission to reject it.",
            "error"
        )

        return redirect(
            url_for(
                "writing.writing_list"
            )
        )


    student_id = writing["student_id"]


    # -----------------------------------------------------
    # Reject Writing
    # -----------------------------------------------------

    cur.execute("""
        UPDATE writing_submissions

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
        user_id,
        reason,
        id,
        institution_id
    ))


    # -----------------------------------------------------
    # Notification
    # -----------------------------------------------------

    notify_student_and_parent(
        student_id=student_id,
        module_name="Writing Skill",
        approved=False,
        remarks=reason,
        institution_id=institution_id,
        cur=cur
    )


    # -----------------------------------------------------
    # Commit
    # -----------------------------------------------------

    conn.commit()


    cur.close()
    conn.close()


    flash(
        "Writing submission rejected and notification sent.",
        "success"
    )


    return redirect(
        url_for(
            "writing.writing_list"
        )
    )


# =========================================================
# Edit Writing
# =========================================================

def edit_writing(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    # -----------------------------------------------------
    # Get Existing Submission
    # -----------------------------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT
                w.*

            FROM writing_submissions w

            JOIN students s
                ON w.student_id = s.id

            WHERE
                w.id = %s
                AND w.institution_id = %s
                AND s.institution_id = %s
                AND w.status = 'Pending'

        """, (
            id,
            session["institution_id"],
            session["institution_id"]
        ))

    elif role == "staff":

        cur.execute("""
            SELECT
                w.*

            FROM writing_submissions w

            JOIN students s
                ON w.student_id = s.id

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                w.id = %s
                AND w.institution_id = %s
                AND s.institution_id = %s
                AND w.status = 'Pending'

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


    writing = cur.fetchone()


    if not writing:

        cur.close()
        conn.close()

        flash(
            "Writing submission not found or cannot be edited.",
            "error"
        )

        return redirect(
            url_for(
                "writing.writing_list"
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

        writing_type = request.form[
            "writing_type"
        ]

        pages = request.form["pages"]

        content = request.form[
            "content"
        ].strip()


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
                "writing/edit.html",
                writing=writing,
                students=students
            )


        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if not title or not content:

            flash(
                "Title and writing content are required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "writing/edit.html",
                writing=writing,
                students=students
            )


        try:

            pages = int(pages)

        except (TypeError, ValueError):

            flash(
                "Invalid page count.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "writing/edit.html",
                writing=writing,
                students=students
            )


        if pages <= 0:

            flash(
                "Pages must be greater than zero.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "writing/edit.html",
                writing=writing,
                students=students
            )


        # -------------------------------------------------
        # Update
        # -------------------------------------------------

        cur.execute("""
            UPDATE writing_submissions

            SET
                student_id = %s,
                title = %s,
                writing_type = %s,
                pages = %s,
                content = %s,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
                AND status = 'Pending'

        """, (
            student_id,
            title,
            writing_type,
            pages,
            content,
            id,
            session["institution_id"]
        ))


        conn.commit()

        cur.close()
        conn.close()


        flash(
            "Writing submission updated successfully.",
            "success"
        )


        return redirect(
            url_for(
                "writing.writing_list"
            )
        )


    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    cur.close()
    conn.close()


    return render_template(
        "writing/edit.html",
        writing=writing,
        students=students
    )