from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from database.db import get_connection


def list_classes():

    search = request.args.get(
        "search",
        ""
    ).strip()

    conn = get_connection()
    cur = conn.cursor()

    if search:

        cur.execute("""
            SELECT *
            FROM classes
            WHERE
                institution_id = %s
                AND class_name ILIKE %s
            ORDER BY id DESC
        """, (
            session["institution_id"],
            f"%{search}%"
        ))

    else:

        cur.execute("""
            SELECT *
            FROM classes
            WHERE institution_id = %s
            ORDER BY id DESC
        """, (
            session["institution_id"],
        ))

    classes = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "classes/list.html",
        classes=classes,
        search=search
    )
    
def add_class():

    if request.method == "POST":

        class_name = request.form["class_name"].strip()
        description = request.form["description"].strip()

        conn = get_connection()
        cur = conn.cursor()

        # Duplicate check
        cur.execute("""
            SELECT id
            FROM classes
            WHERE
                institution_id = %s
                AND LOWER(class_name) = LOWER(%s)
        """, (
            session["institution_id"],
            class_name
        ))

        if cur.fetchone():

            cur.close()
            conn.close()

            flash(
                "Class already exists.",
                "error"
            )

            return render_template(
                "classes/add.html"
            )

        cur.execute("""
            INSERT INTO classes
            (
                institution_id,
                class_name,
                description
            )
            VALUES
            (%s,%s,%s)
        """, (
            session["institution_id"],
            class_name,
            description
        ))

        conn.commit()

        cur.close()
        conn.close()

        flash(
            "Class added successfully.",
            "success"
        )

        return redirect(
            url_for("classes.class_list")
        )

    return render_template(
        "classes/add.html"
    )
    
def edit_class(id):

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":

        class_name = request.form["class_name"].strip()
        description = request.form["description"].strip()

        cur.execute("""
            SELECT id
            FROM classes
            WHERE
                institution_id = %s
                AND LOWER(class_name) = LOWER(%s)
                AND id != %s
        """, (
            session["institution_id"],
            class_name,
            id
        ))

        if cur.fetchone():

            flash(
                "Class already exists.",
                "error"
            )

            cur.close()
            conn.close()

            return redirect(
                url_for(
                    "classes.update_class",
                    id=id
                )
            )

        cur.execute("""
            UPDATE classes
            SET
                class_name = %s,
                description = %s,
                updated_at = NOW()
            WHERE
                id = %s
                AND institution_id = %s
        """, (
            class_name,
            description,
            id,
            session["institution_id"]
        ))

        conn.commit()

        flash(
            "Class updated successfully.",
            "success"
        )

        cur.close()
        conn.close()

        return redirect(
            url_for("classes.class_list")
        )

    cur.execute("""
        SELECT *
        FROM classes
        WHERE
            id = %s
            AND institution_id = %s
    """, (
        id,
        session["institution_id"]
    ))

    class_item = cur.fetchone()

    cur.close()
    conn.close()

    if not class_item:

        flash(
            "Class not found.",
            "error"
        )

        return redirect(
            url_for("classes.class_list")
        )

    return render_template(
        "classes/edit.html",
        class_item=class_item
    )
    
def toggle_class_status(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT is_active
        FROM classes
        WHERE
            id = %s
            AND institution_id = %s
    """, (
        id,
        session["institution_id"]
    ))

    class_item = cur.fetchone()

    if not class_item:

        cur.close()
        conn.close()

        flash(
            "Class not found.",
            "error"
        )

        return redirect(
            url_for("classes.class_list")
        )

    new_status = not class_item["is_active"]

    cur.execute("""
        UPDATE classes
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
            "Class activated successfully.",
            "success"
        )

    else:

        flash(
            "Class deactivated successfully.",
            "success"
        )

    return redirect(
        url_for("classes.class_list")
    )
    
# =========================================================
# View Students Of Class
# =========================================================

def view_class_students(id):

    conn = get_connection()
    cur = conn.cursor()

    # -----------------------------------------------------
    # Get Class
    # -----------------------------------------------------

    cur.execute("""
        SELECT
            id,
            class_name,
            description,
            is_active

        FROM classes

        WHERE
            id = %s
            AND institution_id = %s

        LIMIT 1
    """, (
        id,
        session["institution_id"]
    ))

    class_item = cur.fetchone()


    if not class_item:

        cur.close()
        conn.close()

        flash(
            "Class not found.",
            "error"
        )

        return redirect(
            url_for(
                "classes.class_list"
            )
        )


    # -----------------------------------------------------
    # Get Students
    # -----------------------------------------------------

    cur.execute("""
        SELECT
            id,
            admission_no,
            full_name,
            photo,
            is_active

        FROM students

        WHERE
            institution_id = %s
            AND class_id = %s

        ORDER BY
            full_name ASC
    """, (
        session["institution_id"],
        id
    ))

    students = cur.fetchall()


    cur.close()
    conn.close()


    return render_template(
        "classes/students.html",

        class_item=class_item,

        students=students
    )
    
    
# =========================================================
# View Students of a Class
# =========================================================

def class_students(class_id):

    conn = get_connection()
    cur = conn.cursor()

    # -----------------------------------------------------
    # Verify class belongs to current institution
    # -----------------------------------------------------

    cur.execute("""
        SELECT
            id,
            class_name,
            description,
            is_active
        FROM classes
        WHERE
            id = %s
            AND institution_id = %s
    """, (
        class_id,
        session["institution_id"]
    ))

    class_item = cur.fetchone()

    if not class_item:

        cur.close()
        conn.close()

        flash(
            "Class not found.",
            "error"
        )

        return redirect(
            url_for("classes.class_list")
        )

    # -----------------------------------------------------
    # Get students
    # -----------------------------------------------------

    cur.execute("""
        SELECT
            s.id,
            s.admission_no,
            s.full_name,
            s.gender,
            s.photo,
            s.is_active

        FROM students s

        WHERE
            s.class_id = %s
            AND s.institution_id = %s

        ORDER BY
            s.full_name ASC
    """, (
        class_id,
        session["institution_id"]
    ))

    students = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "classes/students.html",
        class_item=class_item,
        students=students
    )                    