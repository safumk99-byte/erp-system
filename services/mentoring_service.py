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


# =========================================================
# Mentoring Categories
# =========================================================

MENTORING_CATEGORIES = {
    "Behavioural",
    "Academic",
    "Personal Development"
}


# =========================================================
# 1. Mentoring Page
# =========================================================

def mentoring_page():

    student_id = request.args.get(
        "student_id",
        ""
    )

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    # =====================================================
    # Get Allowed Students
    # =====================================================

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

        cur.close()
        conn.close()

        return "Unauthorized", 403


    students = cur.fetchall()


    # =====================================================
    # Verify Selected Student
    # =====================================================

    if student_id:

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

            cur.close()
            conn.close()

            return "Unauthorized", 403


        valid_student = cur.fetchone()


        if not valid_student:

            cur.close()
            conn.close()

            flash(
                "You do not have access to this student.",
                "error"
            )

            return redirect(
                url_for(
                    "mentoring.mentoring_page_route"
                )
            )


    cur.close()
    conn.close()


    return render_template(
        "mentoring/form.html",

        students=students,

        student_id=student_id,

        note_date=str(date.today())
    )


# =========================================================
# 2. Save Mentoring Note
# =========================================================

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


    # =====================================================
    # Basic Validation
    # =====================================================

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


    if not note_date:

        flash(
            "Please select a note date.",
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

    role = session.get("role")


    # =====================================================
    # Verify Student Access
    # =====================================================

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

        cur.close()
        conn.close()

        return "Unauthorized", 403


    valid_student = cur.fetchone()


    if not valid_student:

        cur.close()
        conn.close()

        flash(
            "You do not have access to this student.",
            "error"
        )

        return redirect(
            url_for(
                "mentoring.mentoring_page_route"
            )
        )


    # =====================================================
    # Save Mentoring Note
    # =====================================================

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


# =========================================================
# 3. Mentoring List
# =========================================================

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

    role = session.get("role")


    # =====================================================
    # Get Allowed Students
    # =====================================================

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

        cur.close()
        conn.close()

        return "Unauthorized", 403


    students = cur.fetchall()


    # =====================================================
    # Verify Selected Student
    # =====================================================

    if student_id:

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

        valid_student = cur.fetchone()


        if not valid_student:

            cur.close()
            conn.close()

            flash(
                "You do not have access to this student.",
                "error"
            )

            return redirect(
                url_for(
                    "mentoring.mentoring_list_route"
                )
            )


    # =====================================================
    # Mentoring Records
    # =====================================================

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
            AND s.institution_id = %s
    """

    params = [
        session["institution_id"],
        session["institution_id"]
    ]


    # =====================================================
    # Staff Access Control
    # =====================================================

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


    # =====================================================
    # Student Filter
    # =====================================================

    if student_id:

        query += """
            AND mn.student_id = %s
        """

        params.append(student_id)


    # =====================================================
    # Category Filter
    # =====================================================

    if category:

        if category not in MENTORING_CATEGORIES:

            cur.close()
            conn.close()

            flash(
                "Invalid mentoring category.",
                "error"
            )

            return redirect(
                url_for(
                    "mentoring.mentoring_list_route"
                )
            )

        query += """
            AND mn.category = %s
        """

        params.append(category)


    # =====================================================
    # Order
    # =====================================================

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