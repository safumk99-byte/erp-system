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


# =========================================================
# Helper: Get Parent Role ID
# =========================================================

def _get_parent_role_id(cur):

    cur.execute("""
        SELECT id
        FROM roles
        WHERE name = 'parent'
        LIMIT 1
    """)

    role = cur.fetchone()

    if not role:
        return None

    return role["id"]


# =========================================================
# Parent Access Check
#
# Institution Admin:
#     Can access all parents.
#
# Staff:
#     Can access only parents connected to students
#     in classes assigned to that staff member.
# =========================================================

def _parent_access_allowed(
    cur,
    parent_id,
    institution_id,
    role,
    user_id
):

    # -----------------------------------------------------
    # Institution Admin
    # -----------------------------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT 1
            FROM users u
            JOIN roles r
                ON u.role_id = r.id
            WHERE
                u.id = %s
                AND u.institution_id = %s
                AND r.name = 'parent'
            LIMIT 1
        """, (
            parent_id,
            institution_id
        ))

        return cur.fetchone() is not None


    # -----------------------------------------------------
    # Staff
    # -----------------------------------------------------

    if role == "staff":

        cur.execute("""
            SELECT 1

            FROM users parent_user

            JOIN roles parent_role
                ON parent_user.role_id = parent_role.id

            JOIN students
                ON students.parent_user_id = parent_user.id
                AND students.institution_id = parent_user.institution_id
                AND students.is_active = TRUE

            JOIN staff_classes
                ON staff_classes.class_id = students.class_id
                AND staff_classes.institution_id = students.institution_id
                AND staff_classes.staff_id = %s
                AND staff_classes.is_active = TRUE

            WHERE
                parent_user.id = %s
                AND parent_user.institution_id = %s
                AND parent_role.name = 'parent'

            LIMIT 1
        """, (
            user_id,
            parent_id,
            institution_id
        ))

        return cur.fetchone() is not None


    return False


# =========================================================
# Parent List
# =========================================================

def list_parents():

    search = request.args.get(
        "search",
        ""
    ).strip()

    institution_id = session.get(
        "institution_id"
    )

    role = session.get(
        "role"
    )

    user_id = session.get(
        "user_id"
    )


    if not institution_id:

        return "Unauthorized", 403


    conn = get_connection()
    cur = conn.cursor()


    # =====================================================
    # Institution Admin
    # =====================================================

    if role == "institution_admin":

        if search:

            cur.execute("""
                SELECT
                    users.id,
                    users.full_name AS parent_name,
                    users.username,
                    users.email,
                    users.phone,
                    users.is_active,

                    students.id AS student_id,
                    students.full_name AS student_name,
                    students.admission_no,

                    classes.class_name

                FROM users

                JOIN roles
                    ON users.role_id = roles.id

                LEFT JOIN students
                    ON students.parent_user_id = users.id
                    AND students.institution_id = users.institution_id
                    AND students.is_active = TRUE

                LEFT JOIN classes
                    ON classes.id = students.class_id

                WHERE
                    users.institution_id = %s
                    AND roles.name = 'parent'

                    AND (
                        users.full_name ILIKE %s
                        OR users.username ILIKE %s
                        OR users.phone ILIKE %s
                        OR students.full_name ILIKE %s
                        OR students.admission_no ILIKE %s
                    )

                ORDER BY
                    users.id DESC
            """, (
                institution_id,
                f"%{search}%",
                f"%{search}%",
                f"%{search}%",
                f"%{search}%",
                f"%{search}%"
            ))

        else:

            cur.execute("""
                SELECT
                    users.id,
                    users.full_name AS parent_name,
                    users.username,
                    users.email,
                    users.phone,
                    users.is_active,

                    students.id AS student_id,
                    students.full_name AS student_name,
                    students.admission_no,

                    classes.class_name

                FROM users

                JOIN roles
                    ON users.role_id = roles.id

                LEFT JOIN students
                    ON students.parent_user_id = users.id
                    AND students.institution_id = users.institution_id
                    AND students.is_active = TRUE

                LEFT JOIN classes
                    ON classes.id = students.class_id

                WHERE
                    users.institution_id = %s
                    AND roles.name = 'parent'

                ORDER BY
                    users.id DESC
            """, (
                institution_id,
            ))


    # =====================================================
    # Staff
    #
    # Only parents connected to students in the staff's
    # assigned classes are visible.
    # =====================================================

    elif role == "staff":

        if search:

            cur.execute("""
                SELECT DISTINCT
                    users.id,
                    users.full_name AS parent_name,
                    users.username,
                    users.email,
                    users.phone,
                    users.is_active,

                    students.id AS student_id,
                    students.full_name AS student_name,
                    students.admission_no,

                    classes.class_name

                FROM users

                JOIN roles
                    ON users.role_id = roles.id

                JOIN students
                    ON students.parent_user_id = users.id
                    AND students.institution_id = users.institution_id
                    AND students.is_active = TRUE

                JOIN classes
                    ON classes.id = students.class_id

                JOIN staff_classes
                    ON staff_classes.class_id = students.class_id
                    AND staff_classes.institution_id = students.institution_id
                    AND staff_classes.staff_id = %s
                    AND staff_classes.is_active = TRUE

                WHERE
                    users.institution_id = %s
                    AND roles.name = 'parent'

                    AND (
                        users.full_name ILIKE %s
                        OR users.username ILIKE %s
                        OR users.phone ILIKE %s
                        OR students.full_name ILIKE %s
                        OR students.admission_no ILIKE %s
                    )

                ORDER BY
                    users.id DESC
            """, (
                user_id,
                institution_id,
                f"%{search}%",
                f"%{search}%",
                f"%{search}%",
                f"%{search}%",
                f"%{search}%"
            ))

        else:

            cur.execute("""
                SELECT DISTINCT
                    users.id,
                    users.full_name AS parent_name,
                    users.username,
                    users.email,
                    users.phone,
                    users.is_active,

                    students.id AS student_id,
                    students.full_name AS student_name,
                    students.admission_no,

                    classes.class_name

                FROM users

                JOIN roles
                    ON users.role_id = roles.id

                JOIN students
                    ON students.parent_user_id = users.id
                    AND students.institution_id = users.institution_id
                    AND students.is_active = TRUE

                JOIN classes
                    ON classes.id = students.class_id

                JOIN staff_classes
                    ON staff_classes.class_id = students.class_id
                    AND staff_classes.institution_id = students.institution_id
                    AND staff_classes.staff_id = %s
                    AND staff_classes.is_active = TRUE

                WHERE
                    users.institution_id = %s
                    AND roles.name = 'parent'

                ORDER BY
                    users.id DESC
            """, (
                user_id,
                institution_id
            ))


    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    parents = cur.fetchall()

    cur.close()
    conn.close()


    return render_template(
        "parents/list.html",
        parents=parents,
        search=search
    )


# =========================================================
# Add Parent
#
# Currently not exposed through blueprint, but kept
# compatible with the existing service structure.
# =========================================================

def add_parent():

    institution_id = session.get(
        "institution_id"
    )

    if not institution_id:

        return "Unauthorized", 403


    conn = get_connection()
    cur = conn.cursor()


    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip().lower()

        email = request.form.get(
            "email",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )


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


        # -----------------------------------------------------
        # Username duplicate
        # -----------------------------------------------------

        cur.execute("""
            SELECT id
            FROM users
            WHERE
                institution_id = %s
                AND username = %s
        """, (
            institution_id,
            username
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


        # -----------------------------------------------------
        # Parent role
        # -----------------------------------------------------

        parent_role_id = _get_parent_role_id(cur)

        if not parent_role_id:

            flash(
                "Parent role is not configured.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "parents/add.html"
            )


        # -----------------------------------------------------
        # Create parent
        # -----------------------------------------------------

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
                password,
                is_active
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,TRUE)
        """, (
            institution_id,
            parent_role_id,
            full_name,
            username,
            email or None,
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
            url_for(
                "parents.parent_list"
            )
        )


    cur.close()
    conn.close()


    return render_template(
        "parents/add.html"
    )


# =========================================================
# Edit Parent
# =========================================================

def edit_parent(id):

    institution_id = session.get(
        "institution_id"
    )

    role = session.get(
        "role"
    )

    user_id = session.get(
        "user_id"
    )


    if not institution_id:

        return "Unauthorized", 403


    conn = get_connection()
    cur = conn.cursor()


    # =====================================================
    # Parent Role
    # =====================================================

    parent_role_id = _get_parent_role_id(cur)

    if not parent_role_id:

        cur.close()
        conn.close()

        flash(
            "Parent role is not configured.",
            "error"
        )

        return redirect(
            url_for(
                "parents.parent_list"
            )
        )


    # =====================================================
    # Verify Access
    # =====================================================

    if not _parent_access_allowed(
        cur,
        id,
        institution_id,
        role,
        user_id
    ):

        cur.close()
        conn.close()

        flash(
            "You are not authorized to edit this parent.",
            "error"
        )

        return redirect(
            url_for(
                "parents.parent_list"
            )
        )


    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        new_password = request.form.get(
            "new_password",
            ""
        ).strip()


        # =================================================
        # Validate Parent Name
        # =================================================

        if not full_name:

            flash(
                "Parent name is required.",
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


        if len(full_name) > 150:

            flash(
                "Parent name is too long.",
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


        # =================================================
        # Validate Phone
        # =================================================

        if not phone:

            flash(
                "Parent phone number is required.",
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


        if len(phone) > 30:

            flash(
                "Parent phone number is too long.",
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


        # =================================================
        # Validate Email
        # =================================================

        if email and len(email) > 255:

            flash(
                "Parent email is too long.",
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


        # =================================================
        # Validate New Password
        #
        # Blank = Keep Existing Password
        # =================================================

        if new_password and len(new_password) < 6:

            flash(
                "New password must be at least 6 characters.",
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


        # =================================================
        # Update Parent
        # =================================================

        try:

            if new_password:

                hashed_password = (
                    generate_password_hash(
                        new_password
                    )
                )

                cur.execute("""
                    UPDATE users

                    SET
                        full_name = %s,
                        email = %s,
                        phone = %s,
                        password = %s,
                        updated_at = NOW()

                    WHERE
                        id = %s
                        AND institution_id = %s
                        AND role_id = %s
                """, (
                    full_name,
                    email or None,
                    phone,
                    hashed_password,
                    id,
                    institution_id,
                    parent_role_id
                ))

            else:

                cur.execute("""
                    UPDATE users

                    SET
                        full_name = %s,
                        email = %s,
                        phone = %s,
                        updated_at = NOW()

                    WHERE
                        id = %s
                        AND institution_id = %s
                        AND role_id = %s
                """, (
                    full_name,
                    email or None,
                    phone,
                    id,
                    institution_id,
                    parent_role_id
                ))


            if cur.rowcount != 1:

                raise RuntimeError(
                    "Parent update failed."
                )


            # =================================================
            # Synchronize Student Parent Details
            # =================================================

            cur.execute("""
                UPDATE students

                SET
                    parent_name = %s,
                    parent_phone = %s,
                    updated_at = NOW()

                WHERE
                    parent_user_id = %s
                    AND institution_id = %s
            """, (
                full_name,
                phone,
                id,
                institution_id
            ))


            conn.commit()


        except Exception:

            conn.rollback()

            flash(
                "Unable to update parent. No changes were saved.",
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


        cur.close()
        conn.close()


        flash(
            "Parent updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "parents.parent_list"
            )
        )


    # =====================================================
    # GET
    # =====================================================

    cur.execute("""
        SELECT
            users.id,
            users.full_name,
            users.username,
            users.email,
            users.phone,
            users.is_active,

            students.id AS student_id,
            students.full_name AS student_name,
            students.admission_no,

            classes.class_name

        FROM users

        JOIN roles
            ON users.role_id = roles.id

        LEFT JOIN students
            ON students.parent_user_id = users.id
            AND students.institution_id = users.institution_id
            AND students.is_active = TRUE

        LEFT JOIN classes
            ON classes.id = students.class_id

        WHERE
            users.id = %s
            AND users.institution_id = %s
            AND roles.name = 'parent'
    """, (
        id,
        institution_id
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
            url_for(
                "parents.parent_list"
            )
        )


    return render_template(
        "parents/edit.html",
        parent=parent
    )


# =========================================================
# Toggle Parent Status
# =========================================================

def toggle_parent_status(id):

    institution_id = session.get(
        "institution_id"
    )

    role = session.get(
        "role"
    )

    user_id = session.get(
        "user_id"
    )


    if not institution_id:

        return "Unauthorized", 403


    conn = get_connection()
    cur = conn.cursor()


    # =====================================================
    # Parent Role
    # =====================================================

    parent_role_id = _get_parent_role_id(cur)

    if not parent_role_id:

        cur.close()
        conn.close()

        flash(
            "Parent role is not configured.",
            "error"
        )

        return redirect(
            url_for(
                "parents.parent_list"
            )
        )


    # =====================================================
    # Verify Staff / Admin Access
    # =====================================================

    if not _parent_access_allowed(
        cur,
        id,
        institution_id,
        role,
        user_id
    ):

        cur.close()
        conn.close()

        flash(
            "You are not authorized to change this parent's status.",
            "error"
        )

        return redirect(
            url_for(
                "parents.parent_list"
            )
        )


    # =====================================================
    # Get Current Status
    # =====================================================

    cur.execute("""
        SELECT
            is_active
        FROM users
        WHERE
            id = %s
            AND institution_id = %s
            AND role_id = %s
    """, (
        id,
        institution_id,
        parent_role_id
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
            url_for(
                "parents.parent_list"
            )
        )


    new_status = not parent["is_active"]


    # =====================================================
    # Update Status
    # =====================================================

    cur.execute("""
        UPDATE users

        SET
            is_active = %s,
            updated_at = NOW()

        WHERE
            id = %s
            AND institution_id = %s
            AND role_id = %s
    """, (
        new_status,
        id,
        institution_id,
        parent_role_id
    ))


    conn.commit()


    cur.close()
    conn.close()


    if new_status:

        flash(
            "Parent activated successfully.",
            "success"
        )

    else:

        flash(
            "Parent deactivated successfully.",
            "success"
        )


    return redirect(
        url_for(
            "parents.parent_list"
        )
    )