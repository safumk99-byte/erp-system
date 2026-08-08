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


def portion_completion_page():

    class_id = request.args.get(
        "class_id",
        ""
    )

    subject_id = request.args.get(
        "subject_id",
        ""
    )

    completion_date = request.args.get(
        "date",
        str(date.today())
    )

    conn = get_connection()
    cur = conn.cursor()

    # Active classes

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

    subjects = []

    # Subjects belonging to selected class

    if class_id:

        cur.execute("""
            SELECT
                id,
                subject_name

            FROM subjects

            WHERE
                institution_id = %s
                AND class_id = %s
                AND is_active = TRUE

            ORDER BY subject_name
        """, (
            session["institution_id"],
            class_id
        ))

        subjects = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "portion_completion/form.html",

        classes=classes,

        subjects=subjects,

        class_id=class_id,

        subject_id=subject_id,

        completion_date=completion_date
    )


def save_portion_completion():

    class_id = request.form.get(
        "class_id"
    )

    subject_id = request.form.get(
        "subject_id"
    )

    completion_date = request.form.get(
        "completion_date"
    )

    completed_portion = request.form.get(
        "completed_portion",
        ""
    ).strip()

    remarks = request.form.get(
        "remarks",
        ""
    ).strip()


    if not class_id:

        flash(
            "Please select a class.",
            "error"
        )

        return redirect(
            url_for(
                "portion_completion.portion_completion_list"
            )
        )


    if not subject_id:

        flash(
            "Please select a subject.",
            "error"
        )

        return redirect(
            url_for(
                "portion_completion.portion_completion_page"
            )
        )


    if not completed_portion:

        flash(
            "Please enter the completed portion.",
            "error"
        )

        return redirect(
            url_for(
                "portion_completion.portion_completion_page",
                class_id=class_id,
                subject_id=subject_id,
                date=completion_date
            )
        )


    conn = get_connection()
    cur = conn.cursor()


    # Verify class belongs to current institution

    cur.execute("""
        SELECT id

        FROM classes

        WHERE
            id = %s
            AND institution_id = %s
            AND is_active = TRUE
    """, (
        class_id,
        session["institution_id"]
    ))

    valid_class = cur.fetchone()


    if not valid_class:

        cur.close()
        conn.close()

        flash(
            "Invalid class.",
            "error"
        )

        return redirect(
            url_for(
                "portion_completion.portion_completion_page"
            )
        )


    # Verify subject belongs to selected class

    cur.execute("""
        SELECT id

        FROM subjects

        WHERE
            id = %s
            AND class_id = %s
            AND institution_id = %s
            AND is_active = TRUE
    """, (
        subject_id,
        class_id,
        session["institution_id"]
    ))

    valid_subject = cur.fetchone()


    if not valid_subject:

        cur.close()
        conn.close()

        flash(
            "Invalid subject.",
            "error"
        )

        return redirect(
            url_for(
                "portion_completion.portion_completion_page",
                class_id=class_id
            )
        )


    # Save

    cur.execute("""
        INSERT INTO portion_completion
        (
            institution_id,
            class_id,
            subject_id,
            staff_id,
            completion_date,
            completed_portion,
            remarks
        )

        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """, (
        session["institution_id"],
        class_id,
        subject_id,
        session["user_id"],
        completion_date,
        completed_portion,
        remarks or None
    ))


    conn.commit()

    cur.close()
    conn.close()


    flash(
        "Portion completed successfully.",
        "success"
    )


    return redirect(
        url_for(
            "portion_completion.portion_completion_list"
        )
    )
    
def portion_completion_list():

    class_id = request.args.get(
        "class_id",
        ""
    )

    subject_id = request.args.get(
        "subject_id",
        ""
    )

    conn = get_connection()
    cur = conn.cursor()

    # ---------------------------------
    # Classes
    # ---------------------------------

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


    # ---------------------------------
    # Subjects
    # ---------------------------------

    subjects = []

    if class_id:

        cur.execute("""
            SELECT
                id,
                subject_name

            FROM subjects

            WHERE
                institution_id = %s
                AND class_id = %s
                AND is_active = TRUE

            ORDER BY subject_name
        """, (
            session["institution_id"],
            class_id
        ))

        subjects = cur.fetchall()


    # ---------------------------------
    # Completed Portions
    # ---------------------------------

    query = """
        SELECT
            pc.id,
            pc.completion_date,
            pc.completed_portion,
            pc.remarks,

            c.class_name,

            s.subject_name,

            u.full_name AS staff_name

        FROM portion_completion pc

        JOIN classes c
            ON pc.class_id = c.id

        JOIN subjects s
            ON pc.subject_id = s.id

        JOIN users u
            ON pc.staff_id = u.id

        WHERE
            pc.institution_id = %s
    """

    params = [
        session["institution_id"]
    ]


    if class_id:

        query += """
            AND pc.class_id = %s
        """

        params.append(class_id)


    if subject_id:

        query += """
            AND pc.subject_id = %s
        """

        params.append(subject_id)


    query += """
        ORDER BY
            pc.completion_date DESC,
            c.class_name,
            s.subject_name,
            pc.id DESC
    """


    cur.execute(
        query,
        tuple(params)
    )

    completions = cur.fetchall()


    cur.close()
    conn.close()


    return render_template(
        "portion_completion/list.html",

        completions=completions,

        classes=classes,

        subjects=subjects,

        class_id=class_id,

        subject_id=subject_id
    )    