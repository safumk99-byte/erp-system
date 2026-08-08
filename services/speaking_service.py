from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from database.db import get_connection


def list_speakings():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            sp.*,
            s.full_name,
            s.admission_no

        FROM speaking_submissions sp

        JOIN students s
            ON sp.student_id = s.id

        WHERE
            sp.institution_id = %s

        ORDER BY sp.id DESC

    """, (
        session["institution_id"],
    ))

    speakings = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "speaking/list.html",
        speakings=speakings
    )


def add_speaking():

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


def approve_speaking(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            duration_minutes

        FROM speaking_submissions

        WHERE
            id = %s
            AND institution_id = %s

    """, (
        id,
        session["institution_id"]
    ))

    speaking = cur.fetchone()

    if not speaking:

        cur.close()
        conn.close()

        flash(
            "Speaking submission not found.",
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


def reject_speaking(id):

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
    
def edit_speaking(id):

    conn = get_connection()
    cur = conn.cursor()

    # Get existing pending submission
    cur.execute("""
        SELECT *
        FROM speaking_submissions

        WHERE
            id = %s
            AND institution_id = %s
            AND status = 'Pending'

    """, (
        id,
        session["institution_id"]
    ))

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

    cur.close()
    conn.close()

    return render_template(
        "speaking/edit.html",
        speaking=speaking,
        students=students
    )    