from flask import (
    render_template, 
    request, 
    redirect, 
    url_for,
    flash 
    
)

from werkzeug.security import generate_password_hash
from database.db import get_connection


def list_institutions():

    search = request.args.get("search", "").strip()

    conn = get_connection()
    cur = conn.cursor()

    if search:

        cur.execute("""
            SELECT *
            FROM institutions
            WHERE
                LOWER(name) LIKE LOWER(%s)
                OR LOWER(code) LIKE LOWER(%s)
            ORDER BY id DESC
        """, (
            f"%{search}%",
            f"%{search}%"
        ))

    else:

        cur.execute("""
            SELECT *
            FROM institutions
            ORDER BY id DESC
        """)

    institutions = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "institutions/list.html",
        institutions=institutions,
        search=search
    )
    



def add_institution():

    if request.method == "POST":

        name = request.form["name"].strip()
        code = request.form["code"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()

        admin_full_name = request.form["admin_full_name"].strip()
        admin_username = request.form["admin_username"].strip()
        admin_password = request.form["admin_password"]
        confirm_password = request.form["confirm_password"]

        if not name:
            flash("Institution name is required.", "error")
            return render_template("institutions/add.html")

        if not code:
            flash("Institution code is required.", "error")
            return render_template("institutions/add.html")

        if admin_password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("institutions/add.html")

        conn = get_connection()
        cur = conn.cursor()

        try:

            # Institution code duplicate check
            cur.execute(
                "SELECT id FROM institutions WHERE code = %s",
                (code,)
            )

            if cur.fetchone():
                flash("Institution code already exists.", "error")
                return render_template("institutions/add.html")

            # Username duplicate check
            cur.execute(
                "SELECT id FROM users WHERE username = %s",
                (admin_username,)
            )

            if cur.fetchone():
                flash("Username already exists.", "error")
                return render_template("institutions/add.html")

            # Get Institution Admin role
            cur.execute(
                "SELECT id FROM roles WHERE name = %s",
                ("institution_admin",)
            )

            role = cur.fetchone()

            if not role:
                flash("Institution Admin role not found.", "error")
                return render_template("institutions/add.html")

            role_id = role["id"]

            # Create Institution
            cur.execute("""
                INSERT INTO institutions
                (
                    name,
                    code,
                    email,
                    phone,
                    status
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                name,
                code,
                email,
                phone,
                "Active"
            ))

            institution_id = cur.fetchone()["id"]

            # Hash Password
            hashed_password = generate_password_hash(admin_password)

            # Create Institution Admin User
            cur.execute("""
                INSERT INTO users
                (
                    institution_id,
                    role_id,
                    full_name,
                    username,
                    password,
                    is_active
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                institution_id,
                role_id,
                admin_full_name,
                admin_username,
                hashed_password,
                True
            ))

            conn.commit()

            flash(
                "Institution and administrator created successfully.",
                "success"
            )

            return redirect(
                url_for("institution.institutions")
            )

        except Exception as e:

            conn.rollback()

            flash(
                f"Error: {str(e)}",
                "error"
            )

            return render_template("institutions/add.html")

        finally:

            cur.close()
            conn.close()

    return render_template("institutions/add.html")
    
def update_institution(id):

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":

        name = request.form["name"].strip()
        code = request.form["code"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()

        cur.execute("""
            UPDATE institutions
            SET
                name=%s,
                code=%s,
                email=%s,
                phone=%s,
                updated_at=NOW()
            WHERE id=%s
        """, (
            name,
            code,
            email,
            phone,
            id
        ))

        conn.commit()

        cur.close()
        conn.close()

        flash("Institution updated successfully.", "success")

        return redirect(url_for("institution.institutions"))

    cur.execute(
        "SELECT * FROM institutions WHERE id=%s",
        (id,)
    )

    institution = cur.fetchone()

    cur.close()
    conn.close()

    return render_template(
        "institutions/edit.html",
        institution=institution
    )  
    
def deactivate_institution_service(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT status FROM institutions WHERE id=%s",
        (id,)
    )

    institution = cur.fetchone()

    new_status = "Inactive"

    if institution["status"] == "Inactive":
        new_status = "Active"

    cur.execute("""
        UPDATE institutions
        SET
            status=%s,
            updated_at=NOW()
        WHERE id=%s
    """, (
        new_status,
        id
    ))

    conn.commit()

    cur.close()
    conn.close()

    flash(
        f"Institution {new_status.lower()} successfully.",
        "success"
    )

    return redirect(
        url_for("institution.institutions")
    )      
        