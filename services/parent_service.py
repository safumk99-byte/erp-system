from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from werkzeug.security import generate_password_hash

from database.db import get_connection


def list_parents():

    search = request.args.get(
        "search",
        ""
    ).strip()

    conn = get_connection()
    cur = conn.cursor()

    if search:

        cur.execute("""
            SELECT
                users.*
            FROM users
            JOIN roles
                ON users.role_id = roles.id
            WHERE
                users.institution_id = %s
                AND roles.name = 'parent'
                AND (
                    users.full_name ILIKE %s
                    OR users.username ILIKE %s
                    OR users.phone ILIKE %s
                )
            ORDER BY users.id DESC
        """, (
            session["institution_id"],
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        ))

    else:

        cur.execute("""
            SELECT
                users.*
            FROM users
            JOIN roles
                ON users.role_id = roles.id
            WHERE
                users.institution_id = %s
                AND roles.name = 'parent'
            ORDER BY users.id DESC
        """, (
            session["institution_id"],
        ))

    parents = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "parents/list.html",
        parents=parents,
        search=search
    )


def add_parent():

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":

        full_name = request.form["full_name"].strip()
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "parents/add.html"
            )

        cur.execute("""
            SELECT id
            FROM users
            WHERE username = %s
        """, (
            username,
        ))

        if cur.fetchone():

            flash(
                "Username already exists.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "parents/add.html"
            )

        hashed_password = generate_password_hash(
            password
        )

        cur.execute("""
            INSERT INTO users
            (
                institution_id,
                role_id,
                full_name,
                username,
                email,
                phone,
                password
            )
            VALUES
            (%s,5,%s,%s,%s,%s,%s)
        """, (
            session["institution_id"],
            full_name,
            username,
            email,
            phone,
            hashed_password
        ))

        conn.commit()

        cur.close()
        conn.close()

        flash(
            "Parent added successfully.",
            "success"
        )

        return redirect(
            url_for("parents.parent_list")
        )

    cur.close()
    conn.close()

    return render_template(
        "parents/add.html"
    )
    
def edit_parent(id):

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":

        full_name = request.form["full_name"].strip()
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()

        cur.execute("""
            SELECT id
            FROM users
            WHERE
                username = %s
                AND id != %s
        """, (
            username,
            id
        ))

        if cur.fetchone():

            flash(
                "Username already exists.",
                "error"
            )

            cur.close()
            conn.close()

            return redirect(
                url_for(
                    "parents.update_parent",
                    id=id
                )
            )

        cur.execute("""
            UPDATE users
            SET
                full_name=%s,
                username=%s,
                email=%s,
                phone=%s,
                updated_at=NOW()
            WHERE
                id=%s
                AND institution_id=%s
                AND role_id=5
        """, (
            full_name,
            username,
            email,
            phone,
            id,
            session["institution_id"]
        ))

        conn.commit()

        flash(
            "Parent updated successfully.",
            "success"
        )

        cur.close()
        conn.close()

        return redirect(
            url_for("parents.parent_list")
        )

    cur.execute("""
        SELECT *
        FROM users
        WHERE
            id=%s
            AND institution_id=%s
            AND role_id=5
    """, (
        id,
        session["institution_id"]
    ))

    parent = cur.fetchone()

    cur.close()
    conn.close()

    if not parent:

        flash(
            "Parent not found.",
            "error"
        )

        return redirect(
            url_for("parents.parent_list")
        )

    return render_template(
        "parents/edit.html",
        parent=parent
    )


def toggle_parent_status(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT is_active
        FROM users
        WHERE
            id=%s
            AND institution_id=%s
            AND role_id=5
    """, (
        id,
        session["institution_id"]
    ))

    parent = cur.fetchone()

    if not parent:

        cur.close()
        conn.close()

        flash(
            "Parent not found.",
            "error"
        )

        return redirect(
            url_for("parents.parent_list")
        )

    new_status = not parent["is_active"]

    cur.execute("""
        UPDATE users
        SET
            is_active=%s,
            updated_at=NOW()
        WHERE
            id=%s
            AND institution_id=%s
            AND role_id=5
    """, (
        new_status,
        id,
        session["institution_id"]
    ))

    conn.commit()

    cur.close()
    conn.close()

    flash(
        "Parent status updated successfully.",
        "success"
    )

    return redirect(
        url_for("parents.parent_list")
    )    