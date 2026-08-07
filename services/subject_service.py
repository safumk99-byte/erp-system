from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from database.db import get_connection


def list_subjects():

    search = request.args.get(
        "search",
        ""
    ).strip()

    conn = get_connection()
    cur = conn.cursor()

    if search:

        cur.execute("""
            SELECT
                subjects.*,
                classes.class_name
            FROM subjects
            JOIN classes
                ON subjects.class_id = classes.id
            WHERE
                subjects.institution_id = %s
                AND (
                    subjects.subject_name ILIKE %s
                    OR classes.class_name ILIKE %s
                )
            ORDER BY subjects.id DESC
        """, (
            session["institution_id"],
            f"%{search}%",
            f"%{search}%"
        ))

    else:

        cur.execute("""
            SELECT
                subjects.*,
                classes.class_name
            FROM subjects
            JOIN classes
                ON subjects.class_id = classes.id
            WHERE
                subjects.institution_id = %s
            ORDER BY subjects.id DESC
        """, (
            session["institution_id"],
        ))

    subjects = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "subjects/list.html",
        subjects=subjects,
        search=search
    )
    
def add_subject():

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

        class_id = request.form["class_id"]
        subject_name = request.form["subject_name"].strip()
        description = request.form["description"].strip()

        cur.execute("""
            SELECT id
            FROM subjects
            WHERE
                institution_id = %s
                AND class_id = %s
                AND LOWER(subject_name) = LOWER(%s)
        """, (
            session["institution_id"],
            class_id,
            subject_name
        ))

        if cur.fetchone():

            flash(
                "Subject already exists.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "subjects/add.html",
                classes=classes
            )

        cur.execute("""
            INSERT INTO subjects
            (
                institution_id,
                class_id,
                subject_name,
                description
            )
            VALUES
            (%s,%s,%s,%s)
        """, (
            session["institution_id"],
            class_id,
            subject_name,
            description
        ))

        conn.commit()

        cur.close()
        conn.close()

        flash(
            "Subject added successfully.",
            "success"
        )

        return redirect(
            url_for("subjects.subject_list")
        )

    cur.close()
    conn.close()

    return render_template(
        "subjects/add.html",
        classes=classes
    )
    
def edit_subject(id):

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

        class_id = request.form["class_id"]
        subject_name = request.form["subject_name"].strip()
        description = request.form["description"].strip()

        cur.execute("""
            SELECT id
            FROM subjects
            WHERE
                institution_id = %s
                AND class_id = %s
                AND LOWER(subject_name) = LOWER(%s)
                AND id != %s
        """, (
            session["institution_id"],
            class_id,
            subject_name,
            id
        ))

        if cur.fetchone():

            flash(
                "Subject already exists.",
                "error"
            )

            cur.close()
            conn.close()

            return redirect(
                url_for(
                    "subjects.update_subject",
                    id=id
                )
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
            session["institution_id"]
        ))

        conn.commit()

        flash(
            "Subject updated successfully.",
            "success"
        )

        cur.close()
        conn.close()

        return redirect(
            url_for("subjects.subject_list")
        )

    cur.execute("""
        SELECT *
        FROM subjects
        WHERE
            id = %s
            AND institution_id = %s
    """, (
        id,
        session["institution_id"]
    ))

    subject = cur.fetchone()

    cur.close()
    conn.close()

    if not subject:

        flash(
            "Subject not found.",
            "error"
        )

        return redirect(
            url_for("subjects.subject_list")
        )

    return render_template(
        "subjects/edit.html",
        subject=subject,
        classes=classes
    )
    
def toggle_subject_status(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT is_active
        FROM subjects
        WHERE
            id = %s
            AND institution_id = %s
    """, (
        id,
        session["institution_id"]
    ))

    subject = cur.fetchone()

    if not subject:

        cur.close()
        conn.close()

        flash(
            "Subject not found.",
            "error"
        )

        return redirect(
            url_for("subjects.subject_list")
        )

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
        session["institution_id"]
    ))

    conn.commit()

    cur.close()
    conn.close()

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

    return redirect(
        url_for("subjects.subject_list")
    )            