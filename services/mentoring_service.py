from datetime import date

from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from database.db import get_connection


MENTORING_CATEGORIES = {
    "Behavioural",
    "Academic",
    "Personal Development"
}


def mentoring_page():

    student_id = request.args.get(
        "student_id",
        ""
    )

    conn = get_connection()
    cur = conn.cursor()

    # Active students

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

    cur.close()
    conn.close()

    return render_template(
        "mentoring/form.html",
        students=students,
        student_id=student_id,
        note_date=str(date.today())
    )


def save_mentoring_note():

    student_id = request.form.get(
        "student_id"
    )

    note_date = request.form.get(
        "note_date"
    )

    category = request.form.get(
        "category"
    )

    note = request.form.get(
        "note",
        ""
    ).strip()


    if not student_id:

        flash(
            "Please select a student.",
            "error"
        )

        return redirect(
            url_for(
                "mentoring.mentoring_page_route"
            )
        )


    if category not in MENTORING_CATEGORIES:

        flash(
            "Invalid mentoring category.",
            "error"
        )

        return redirect(
            url_for(
                "mentoring.mentoring_page_route",
                student_id=student_id
            )
        )


    if not note:

        flash(
            "Please enter a mentoring note.",
            "error"
        )

        return redirect(
            url_for(
                "mentoring.mentoring_page_route",
                student_id=student_id
            )
        )


    conn = get_connection()
    cur = conn.cursor()

    # Verify student belongs to current institution

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

    valid_student = cur.fetchone()


    if not valid_student:

        cur.close()
        conn.close()

        flash(
            "Invalid student.",
            "error"
        )

        return redirect(
            url_for(
                "mentoring.mentoring_page_route"
            )
        )


    # Save mentoring note

    cur.execute("""
        INSERT INTO mentoring_notes
        (
            institution_id,
            student_id,
            staff_id,
            note_date,
            category,
            note
        )

        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """, (
        session["institution_id"],
        student_id,
        session["user_id"],
        note_date,
        category,
        note
    ))


    conn.commit()

    cur.close()
    conn.close()


    flash(
        "Mentoring note saved successfully.",
        "success"
    )


    return redirect(
        url_for(
            "mentoring.mentoring_list_route",
            student_id=student_id
        )
    )
    
def mentoring_list():

    student_id = request.args.get(
        "student_id",
        ""
    )

    category = request.args.get(
        "category",
        ""
    )

    conn = get_connection()
    cur = conn.cursor()

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


    # Mentoring records

    query = """
        SELECT
            mn.id,
            mn.student_id,
            mn.note_date,
            mn.category,
            mn.note,
            mn.created_at,

            s.full_name AS student_name,
            s.admission_no,

            u.full_name AS staff_name

        FROM mentoring_notes mn

        JOIN students s
            ON mn.student_id = s.id

        JOIN users u
            ON mn.staff_id = u.id

        WHERE
            mn.institution_id = %s
    """

    params = [
        session["institution_id"]
    ]


    # Staff can see only their own notes.
    # Institution admin can see all notes.

    user_role = session.get("role")

    if user_role == "staff":

        query += """
            AND mn.staff_id = %s
        """

        params.append(
            session["user_id"]
        )


    if student_id:

        query += """
            AND mn.student_id = %s
        """

        params.append(student_id)


    if category:

        query += """
            AND mn.category = %s
        """

        params.append(category)


    query += """
        ORDER BY
            mn.note_date DESC,
            mn.id DESC
    """


    cur.execute(
        query,
        tuple(params)
    )

    notes = cur.fetchall()


    cur.close()
    conn.close()


    return render_template(
        "mentoring/list.html",

        notes=notes,

        students=students,

        student_id=student_id,

        category=category
    )    