from flask import (
    render_template, 
    request, 
    redirect, 
    url_for,
    flash 
    
)
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

        name = request.form["name"]
        code = request.form["code"]
        email = request.form["email"]
        phone = request.form["phone"]
        name = request.form["name"].strip()
        code = request.form["code"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()

        if not name:
            return "Institution Name is required"

        if not code:
            return "Institution Code is required"

        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute(
            "SELECT id FROM institutions WHERE code = %s",
            (code,)
        )

        existing = cur.fetchone()

        if existing:

            cur.close()
            conn.close()

            flash("Institution code already exists.", "error")
            return render_template("institutions/add.html")

        cur.execute("""
            INSERT INTO institutions
            (name, code, email, phone, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            name,
            code,
            email,
            phone,
            "Active"
        ))

        conn.commit()
        flash("Institution created successfully.", "success")



        cur.close()
        conn.close()

        return redirect(
            url_for("institution.institutions")
        )

    return render_template(
        "institutions/add.html"
    )
    
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
        