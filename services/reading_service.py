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
# Verify Student Access
# =========================================================

def _student_is_allowed(cur, student_id):

    role = session.get("role")

    # -----------------------------------------------------
    # Institution Admin
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Staff
    # -----------------------------------------------------

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
# Get Allowed Students
# =========================================================

def _get_students(cur):

    role = session.get("role")

    # -----------------------------------------------------
    # Institution Admin
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Staff
    # -----------------------------------------------------

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
# List Readings
# =========================================================

def list_readings():

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")

    query = """
        SELECT
            r.*,
            s.full_name,
            s.admission_no

        FROM reading_submissions r

        JOIN students s
            ON r.student_id = s.id

        WHERE
            r.institution_id = %s
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
        ORDER BY r.id DESC
    """


    cur.execute(
        query,
        tuple(params)
    )

    readings = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "reading/list.html",
        readings=readings
    )


# =========================================================
# Add Reading
# =========================================================

def add_reading():

    conn = get_connection()
    cur = conn.cursor()

    students = _get_students(cur)

    if request.method == "POST":

        student_id = request.form["student_id"]

        book_title = request.form[
            "book_title"
        ].strip()

        reading_type = request.form[
            "reading_type"
        ]

        pages = request.form["pages"]

        review = request.form[
            "review"
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
                "reading/add.html",
                students=students
            )


        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if not book_title:

            flash(
                "Book title is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "reading/add.html",
                students=students
            )


        if not review:

            flash(
                "Review is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "reading/add.html",
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
                "reading/add.html",
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
                "reading/add.html",
                students=students
            )


        # Points will be calculated
        # after approval.

        points = 0


        cur.execute("""
            INSERT INTO reading_submissions
            (
                institution_id,
                student_id,
                book_title,
                reading_type,
                pages,
                review,
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
            book_title,
            reading_type,
            pages,
            review,
            points
        ))


        conn.commit()

        cur.close()
        conn.close()


        flash(
            "Reading submission added successfully.",
            "success"
        )


        return redirect(
            url_for(
                "reading.reading_list"
            )
        )


    cur.close()
    conn.close()


    return render_template(
        "reading/add.html",
        students=students
    )


# =========================================================
# Approve Reading
# =========================================================

def approve_reading(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    # -----------------------------------------------------
    # Get Reading + Verify Student Access
    # -----------------------------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT
                r.reading_type,
                r.pages

            FROM reading_submissions r

            JOIN students s
                ON r.student_id = s.id

            WHERE
                r.id = %s
                AND r.institution_id = %s
                AND s.institution_id = %s
                AND r.status = 'Pending'
        """, (
            id,
            session["institution_id"],
            session["institution_id"]
        ))

    elif role == "staff":

        cur.execute("""
            SELECT
                r.reading_type,
                r.pages

            FROM reading_submissions r

            JOIN students s
                ON r.student_id = s.id

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                r.id = %s
                AND r.institution_id = %s
                AND s.institution_id = %s
                AND r.status = 'Pending'

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


    reading = cur.fetchone()


    if not reading:

        cur.close()
        conn.close()

        flash(
            "Reading submission not found or you do not have permission to approve it.",
            "error"
        )

        return redirect(
            url_for(
                "reading.reading_list"
            )
        )


    reading_type = reading["reading_type"]
    pages = reading["pages"]

    points = 0


    if reading_type == "Fiction":

        if pages >= 50:
            points = 3

    elif reading_type == "Non-Fiction":

        if pages >= 25:
            points = 5


    cur.execute("""
        UPDATE reading_submissions

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
        "Reading submission approved.",
        "success"
    )


    return redirect(
        url_for(
            "reading.reading_list"
        )
    )


# =========================================================
# Reject Reading
# =========================================================

def reject_reading(id):

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
                "reading.reading_list"
            )
        )


    # -----------------------------------------------------
    # Verify Reading Access
    # -----------------------------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT
                r.id

            FROM reading_submissions r

            JOIN students s
                ON r.student_id = s.id

            WHERE
                r.id = %s
                AND r.institution_id = %s
                AND s.institution_id = %s
                AND r.status = 'Pending'
        """, (
            id,
            session["institution_id"],
            session["institution_id"]
        ))

    elif role == "staff":

        cur.execute("""
            SELECT
                r.id

            FROM reading_submissions r

            JOIN students s
                ON r.student_id = s.id

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                r.id = %s
                AND r.institution_id = %s
                AND s.institution_id = %s
                AND r.status = 'Pending'

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


    reading = cur.fetchone()


    if not reading:

        cur.close()
        conn.close()

        flash(
            "Reading submission not found or you do not have permission to reject it.",
            "error"
        )

        return redirect(
            url_for(
                "reading.reading_list"
            )
        )


    cur.execute("""
        UPDATE reading_submissions

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
        "Reading submission rejected.",
        "success"
    )


    return redirect(
        url_for(
            "reading.reading_list"
        )
    )


# =========================================================
# Edit Reading
# =========================================================

def edit_reading(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    # -----------------------------------------------------
    # Get Existing Submission
    # -----------------------------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT
                r.*

            FROM reading_submissions r

            JOIN students s
                ON r.student_id = s.id

            WHERE
                r.id = %s
                AND r.institution_id = %s
                AND s.institution_id = %s
                AND r.status = 'Pending'

        """, (
            id,
            session["institution_id"],
            session["institution_id"]
        ))

    elif role == "staff":

        cur.execute("""
            SELECT
                r.*

            FROM reading_submissions r

            JOIN students s
                ON r.student_id = s.id

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                r.id = %s
                AND r.institution_id = %s
                AND s.institution_id = %s
                AND r.status = 'Pending'

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


    reading = cur.fetchone()


    if not reading:

        cur.close()
        conn.close()

        flash(
            "Reading submission not found or cannot be edited.",
            "error"
        )

        return redirect(
            url_for(
                "reading.reading_list"
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

        book_title = request.form[
            "book_title"
        ].strip()

        reading_type = request.form[
            "reading_type"
        ]

        pages = request.form["pages"]

        review = request.form[
            "review"
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
                "reading/edit.html",
                reading=reading,
                students=students
            )


        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if not book_title or not review:

            flash(
                "Book title and review are required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "reading/edit.html",
                reading=reading,
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
                "reading/edit.html",
                reading=reading,
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
                "reading/edit.html",
                reading=reading,
                students=students
            )


        # -------------------------------------------------
        # Update
        # -------------------------------------------------

        cur.execute("""
            UPDATE reading_submissions

            SET
                student_id = %s,
                book_title = %s,
                reading_type = %s,
                pages = %s,
                review = %s,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
                AND status = 'Pending'

        """, (
            student_id,
            book_title,
            reading_type,
            pages,
            review,
            id,
            session["institution_id"]
        ))
        
        conn.commit()

        cur.close()
        conn.close()


        flash(
            "Reading submission updated successfully.",
            "success"
        )


        return redirect(
            url_for(
                "reading.reading_list"
            )
        )


    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    cur.close()
    conn.close()


    return render_template(
        "reading/edit.html",
        reading=reading,
        students=students
    )