from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from database.db import get_connection


def list_writings():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            w.*,
            s.full_name,
            s.admission_no

        FROM writing_submissions w

        JOIN students s
            ON w.student_id = s.id

        WHERE
            w.institution_id = %s

        ORDER BY w.id DESC

    """, (
        session["institution_id"],
    ))

    writings = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "writing/list.html",
        writings=writings
    )


def add_writing():

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


def approve_writing(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            writing_type,
            pages

        FROM writing_submissions

        WHERE
            id = %s
            AND institution_id = %s

    """, (
        id,
        session["institution_id"]
    ))

    writing = cur.fetchone()

    if not writing:

        cur.close()
        conn.close()

        flash(
            "Writing submission not found.",
            "error"
        )

        return redirect(
            url_for(
                "writing.writing_list"
            )
        )

    writing_type = writing["writing_type"]
    pages = writing["pages"]

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
        "Writing submission approved.",
        "success"
    )

    return redirect(
        url_for(
            "writing.writing_list"
        )
    )


def reject_writing(id):

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
                "writing.writing_list"
            )
        )

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
        "Writing submission rejected.",
        "success"
    )

    return redirect(
        url_for(
            "writing.writing_list"
        )
    )
    
def edit_writing(id):

    conn = get_connection()
    cur = conn.cursor()

    # Get existing submission
    cur.execute("""
        SELECT *
        FROM writing_submissions

        WHERE
            id = %s
            AND institution_id = %s
            AND status = 'Pending'

    """, (
        id,
        session["institution_id"]
    ))

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

    cur.close()
    conn.close()

    return render_template(
        "writing/edit.html",
        writing=writing,
        students=students
    )    