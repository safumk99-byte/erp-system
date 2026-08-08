from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from database.db import get_connection


def list_readings():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            r.*,
            s.full_name,
            s.admission_no

        FROM reading_submissions r

        JOIN students s
            ON r.student_id = s.id

        WHERE
            r.institution_id = %s

        ORDER BY r.id DESC

    """, (
        session["institution_id"],
    ))

    readings = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "reading/list.html",
        readings=readings
    )


def add_reading():

    conn = get_connection()
    cur = conn.cursor()

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

    students = cur.fetchall()

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


def approve_reading(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            reading_type,
            pages

        FROM reading_submissions

        WHERE
            id = %s
            AND institution_id = %s

    """, (
        id,
        session["institution_id"]
    ))

    reading = cur.fetchone()

    if not reading:

        cur.close()
        conn.close()

        flash(
            "Reading submission not found.",
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


def reject_reading(id):

    conn = get_connection()
    cur = conn.cursor()

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
    
def edit_reading(id):

    conn = get_connection()
    cur = conn.cursor()

    # Get existing submission
    cur.execute("""
        SELECT *
        FROM reading_submissions

        WHERE
            id = %s
            AND institution_id = %s
            AND status = 'Pending'

    """, (
        id,
        session["institution_id"]
    ))

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

    # Students
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

    students = cur.fetchall()

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

    cur.close()
    conn.close()

    return render_template(
        "reading/edit.html",
        reading=reading,
        students=students
    )    