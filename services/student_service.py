from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from database.db import get_connection


def list_students():

    search = request.args.get(
        "search",
        ""
    ).strip()

    conn = get_connection()
    cur = conn.cursor()

    if search:

        cur.execute("""
            SELECT
                students.*,
                classes.class_name
            FROM students
            JOIN classes
                ON students.class_id = classes.id
            WHERE
                students.institution_id = %s
                AND (
                    students.full_name ILIKE %s
                    OR students.admission_no ILIKE %s
                    OR students.parent_name ILIKE %s
                )
            ORDER BY students.id DESC
        """, (
            session["institution_id"],
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        ))

    else:

        cur.execute("""
            SELECT
                students.*,
                classes.class_name
            FROM students
            JOIN classes
                ON students.class_id = classes.id
            WHERE students.institution_id = %s
            ORDER BY students.id DESC
        """, (
            session["institution_id"],
        ))

    students = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "students/list.html",
        students=students,
        search=search
    )
    
def add_student():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            class_name
        FROM classes
        WHERE
            institution_id = %s
            AND is_active = TRUE
        ORDER BY class_name
    """, (
        session["institution_id"],
    ))

    classes = cur.fetchall()

    if request.method == "POST":

        full_name = request.form["full_name"].strip()
        gender = request.form["gender"]
        date_of_birth = request.form["date_of_birth"]
        class_id = request.form["class_id"]
        parent_name = request.form["parent_name"].strip()
        parent_phone = request.form["parent_phone"].strip()
        address = request.form["address"].strip()

        cur.execute("""
            SELECT admission_prefix
            FROM institutions
            WHERE id = %s
        """, (
            session["institution_id"],
        ))

        institution = cur.fetchone()

        prefix = institution["admission_prefix"]

        cur.execute("""
            SELECT admission_no
            FROM students
            WHERE institution_id = %s
            ORDER BY id DESC
            LIMIT 1
        """, (
            session["institution_id"],
        ))

        last_student = cur.fetchone()

        if last_student:

            number = int(
                last_student["admission_no"].split("-")[1]
            ) + 1

        else:

            number = 1

        admission_no = f"{prefix}-{number:04d}"

        cur.execute("""
            INSERT INTO students
            (
                institution_id,
                admission_no,
                full_name,
                gender,
                date_of_birth,
                class_id,
                parent_name,
                parent_phone,
                address
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            session["institution_id"],
            admission_no,
            full_name,
            gender,
            date_of_birth,
            class_id,
            parent_name,
            parent_phone,
            address
        ))

        conn.commit()

        flash(
            "Student added successfully.",
            "success"
        )

        cur.close()
        conn.close()

        return redirect(
            url_for("students.student_list")
        )

    cur.close()
    conn.close()

    return render_template(
        "students/add.html",
        classes=classes
    )
    
def edit_student(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            class_name
        FROM classes
        WHERE
            institution_id = %s
            AND is_active = TRUE
        ORDER BY class_name
    """, (
        session["institution_id"],
    ))

    classes = cur.fetchall()

    if request.method == "POST":

        full_name = request.form["full_name"].strip()
        gender = request.form["gender"]
        date_of_birth = request.form["date_of_birth"]
        class_id = request.form["class_id"]
        parent_name = request.form["parent_name"].strip()
        parent_phone = request.form["parent_phone"].strip()
        address = request.form["address"].strip()

        cur.execute("""
            UPDATE students
            SET
                full_name=%s,
                gender=%s,
                date_of_birth=%s,
                class_id=%s,
                parent_name=%s,
                parent_phone=%s,
                address=%s,
                updated_at=NOW()
            WHERE
                id=%s
                AND institution_id=%s
        """, (
            full_name,
            gender,
            date_of_birth,
            class_id,
            parent_name,
            parent_phone,
            address,
            id,
            session["institution_id"]
        ))

        conn.commit()

        flash(
            "Student updated successfully.",
            "success"
        )

        cur.close()
        conn.close()

        return redirect(
            url_for("students.student_list")
        )

    cur.execute("""
        SELECT *
        FROM students
        WHERE
            id=%s
            AND institution_id=%s
    """, (
        id,
        session["institution_id"]
    ))

    student = cur.fetchone()

    cur.close()
    conn.close()

    if not student:

        flash(
            "Student not found.",
            "error"
        )

        return redirect(
            url_for("students.student_list")
        )

    return render_template(
        "students/edit.html",
        student=student,
        classes=classes
    )
    
def toggle_student_status(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT is_active
        FROM students
        WHERE
            id=%s
            AND institution_id=%s
    """, (
        id,
        session["institution_id"]
    ))

    student = cur.fetchone()

    if not student:

        cur.close()
        conn.close()

        flash(
            "Student not found.",
            "error"
        )

        return redirect(
            url_for("students.student_list")
        )

    new_status = not student["is_active"]

    cur.execute("""
        UPDATE students
        SET
            is_active=%s,
            updated_at=NOW()
        WHERE
            id=%s
            AND institution_id=%s
    """, (
        new_status,
        id,
        session["institution_id"]
    ))

    conn.commit()

    cur.close()
    conn.close()

    flash(
        "Student status updated successfully.",
        "success"
    )

    return redirect(
        url_for("students.student_list")
    )            