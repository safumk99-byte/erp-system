from flask import (
    render_template,
    session,
    request,
    redirect,
    url_for,
    flash
)

from werkzeug.security import generate_password_hash

from database.db import get_connection


def list_staff():

    search = request.args.get(
        "search",
        ""
    ).strip()

    conn = get_connection()
    cur = conn.cursor()

    if search:

        cur.execute("""
            SELECT
                users.*,
                roles.name AS role_name
            FROM users
            JOIN roles
                ON users.role_id = roles.id
            WHERE
                users.institution_id = %s
                AND roles.name IN ('principal', 'staff')
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
                users.*,
                roles.name AS role_name
            FROM users
            JOIN roles
                ON users.role_id = roles.id
            WHERE
                users.institution_id = %s
                AND roles.name IN ('principal', 'staff')
            ORDER BY users.id DESC
        """, (
            session["institution_id"],
        ))

    staff_members = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "staff/list.html",
        staff_members=staff_members,
        search=search
    )
    
def add_staff():

    if request.method == "POST":

        full_name = request.form["full_name"].strip()
        username = request.form["username"].strip().lower()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        role = request.form["role"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return render_template(
                "staff/add.html"
            )

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id
            FROM users
            WHERE username = %s
            """,
            (username,)
        )

        if cur.fetchone():

            cur.close()
            conn.close()

            flash(
                "Username already exists.",
                "error"
            )

            return render_template(
                "staff/add.html"
            )

        cur.execute(
            """
            SELECT id
            FROM roles
            WHERE name = %s
            """,
            (role,)
        )

        role_data = cur.fetchone()

        cur.execute(
            """
            INSERT INTO users
            (
                institution_id,
                role_id,
                full_name,
                username,
                email,
                phone,
                password,
                is_active
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                session["institution_id"],
                role_data["id"],
                full_name,
                username,
                email,
                phone,
                generate_password_hash(password),
                True
            )
        )

        conn.commit()

        cur.close()
        conn.close()

        flash(
            "Staff added successfully.",
            "success"
        )

        return redirect(
            url_for("staff.staff_list")
        )

    return render_template(
        "staff/add.html"
    )
    
def edit_staff(id):

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":

        full_name = request.form["full_name"].strip()
        username = request.form["username"].strip().lower()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        role = request.form["role"]

        # Username duplicate check
        cur.execute(
            """
            SELECT id
            FROM users
            WHERE username = %s
            AND id != %s
            """,
            (
                username,
                id
            )
        )

        if cur.fetchone():

            flash(
                "Username already exists.",
                "error"
            )

            cur.close()
            conn.close()

            return redirect(
                url_for(
                    "staff.update_staff",
                    id=id
                )
            )

        # Get role id
        cur.execute(
            """
            SELECT id
            FROM roles
            WHERE name = %s
            """,
            (role,)
        )

        role_data = cur.fetchone()

        # Update staff
        cur.execute(
            """
            UPDATE users
            SET
                full_name = %s,
                username = %s,
                email = %s,
                phone = %s,
                role_id = %s,
                updated_at = NOW()
            WHERE
                id = %s
                AND institution_id = %s
            """,
            (
                full_name,
                username,
                email,
                phone,
                role_data["id"],
                id,
                session["institution_id"]
            )
        )

        conn.commit()

        flash(
            "Staff updated successfully.",
            "success"
        )

        cur.close()
        conn.close()

        return redirect(
            url_for("staff.staff_list")
        )

    # GET Request
    cur.execute(
        """
        SELECT
            users.*,
            roles.name AS role_name
        FROM users
        JOIN roles
            ON users.role_id = roles.id
        WHERE
            users.id = %s
            AND users.institution_id = %s
        """,
        (
            id,
            session["institution_id"]
        )
    )

    staff = cur.fetchone()

    cur.close()
    conn.close()

    if not staff:

        flash(
            "Staff not found.",
            "error"
        )

        return redirect(
            url_for("staff.staff_list")
        )

    return render_template(
        "staff/edit.html",
        staff=staff
    )
    
def toggle_staff_status(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            is_active
        FROM users
        WHERE
            id = %s
            AND institution_id = %s
        """,
        (
            id,
            session["institution_id"]
        )
    )

    staff = cur.fetchone()

    if not staff:

        cur.close()
        conn.close()

        flash(
            "Staff not found.",
            "error"
        )

        return redirect(
            url_for("staff.staff_list")
        )

    new_status = not staff["is_active"]

    cur.execute(
        """
        UPDATE users
        SET
            is_active = %s,
            updated_at = NOW()
        WHERE
            id = %s
            AND institution_id = %s
        """,
        (
            new_status,
            id,
            session["institution_id"]
        )
    )

    conn.commit()

    cur.close()
    conn.close()

    if new_status:

        flash(
            "Staff activated successfully.",
            "success"
        )

    else:

        flash(
            "Staff deactivated successfully.",
            "success"
        )

    return redirect(
        url_for("staff.staff_list")
    )
    
# =========================================================
# Assign Staff to Classes
# =========================================================

def assign_staff_classes(id):

    conn = get_connection()
    cur = conn.cursor()

    # ---------------------------------
    # Verify staff belongs to institution
    # ---------------------------------

    cur.execute("""
        SELECT
            id,
            full_name
        FROM users
        WHERE
            id = %s
            AND institution_id = %s
            AND is_active = TRUE
    """, (
        id,
        session["institution_id"]
    ))

    staff = cur.fetchone()

    if not staff:

        cur.close()
        conn.close()

        flash(
            "Staff not found.",
            "error"
        )

        return redirect(
            url_for("staff.staff_list")
        )

    # ---------------------------------
    # Save assignments
    # ---------------------------------

    if request.method == "POST":

        selected_classes = request.form.getlist(
            "class_ids"
        )

        # Remove old assignments
        cur.execute("""
            DELETE FROM staff_classes
            WHERE
                staff_id = %s
                AND institution_id = %s
        """, (
            id,
            session["institution_id"]
        ))

        # Insert selected classes
        for class_id in selected_classes:

            cur.execute("""
                INSERT INTO staff_classes
                (
                    institution_id,
                    staff_id,
                    class_id,
                    is_active
                )
                VALUES
                (%s, %s, %s, TRUE)
                ON CONFLICT (staff_id, class_id)
                DO UPDATE SET
                    is_active = TRUE,
                    updated_at = NOW()
            """, (
                session["institution_id"],
                id,
                class_id
            ))

        conn.commit()

        cur.close()
        conn.close()

        flash(
            "Class assignments updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "staff.assign_classes",
                id=id
            )
        )

    # ---------------------------------
    # Get institution classes
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
    # Get assigned classes
    # ---------------------------------

    cur.execute("""
        SELECT
            class_id
        FROM staff_classes
        WHERE
            staff_id = %s
            AND institution_id = %s
            AND is_active = TRUE
    """, (
        id,
        session["institution_id"]
    ))

    assigned_classes = cur.fetchall()

    assigned_class_ids = {
        row["class_id"]
        for row in assigned_classes
    }

    cur.close()
    conn.close()

    return render_template(
        "staff/assign_classes.html",
        staff=staff,
        classes=classes,
        assigned_class_ids=assigned_class_ids
    )


# =========================================================
# Assign Staff to Subjects
# =========================================================

def assign_staff_subjects(id):

    conn = get_connection()
    cur = conn.cursor()

    # ---------------------------------
    # Verify staff belongs to institution
    # ---------------------------------

    cur.execute("""
        SELECT
            id,
            full_name
        FROM users
        WHERE
            id = %s
            AND institution_id = %s
            AND is_active = TRUE
    """, (
        id,
        session["institution_id"]
    ))

    staff = cur.fetchone()

    if not staff:

        cur.close()
        conn.close()

        flash(
            "Staff not found.",
            "error"
        )

        return redirect(
            url_for("staff.staff_list")
        )

    # ---------------------------------
    # Save assignments
    # ---------------------------------

    if request.method == "POST":

        selected_subjects = request.form.getlist(
            "subject_ids"
        )

        # Remove old assignments
        cur.execute("""
            DELETE FROM staff_subjects
            WHERE
                staff_id = %s
                AND institution_id = %s
        """, (
            id,
            session["institution_id"]
        ))

        # Insert selected subjects
        for subject_id in selected_subjects:

            cur.execute("""
                INSERT INTO staff_subjects
                (
                    institution_id,
                    staff_id,
                    subject_id,
                    is_active
                )
                VALUES
                (%s, %s, %s, TRUE)
                ON CONFLICT (staff_id, subject_id)
                DO UPDATE SET
                    is_active = TRUE,
                    updated_at = NOW()
            """, (
                session["institution_id"],
                id,
                subject_id
            ))

        conn.commit()

        cur.close()
        conn.close()

        flash(
            "Subject assignments updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "staff.assign_subjects",
                id=id
            )
        )

    # ---------------------------------
    # Get institution subjects
    # ---------------------------------

    cur.execute("""
        SELECT
            s.id,
            s.subject_name,
            c.class_name
        FROM subjects s
        LEFT JOIN classes c
            ON s.class_id = c.id
        WHERE
            s.institution_id = %s
            AND s.is_active = TRUE
        ORDER BY
            c.class_name,
            s.subject_name
    """, (
        session["institution_id"],
    ))

    subjects = cur.fetchall()

    # ---------------------------------
    # Get assigned subjects
    # ---------------------------------

    cur.execute("""
        SELECT
            subject_id
        FROM staff_subjects
        WHERE
            staff_id = %s
            AND institution_id = %s
            AND is_active = TRUE
    """, (
        id,
        session["institution_id"]
    ))

    assigned_subjects = cur.fetchall()

    assigned_subject_ids = {
        row["subject_id"]
        for row in assigned_subjects
    }

    cur.close()
    conn.close()

    return render_template(
        "staff/assign_subjects.html",
        staff=staff,
        subjects=subjects,
        assigned_subject_ids=assigned_subject_ids
    )                