from flask import (
    render_template,
    session,
    request,
    redirect,
    url_for,
    flash
)
import os 
import uuid
from werkzeug.utils import secure_filename

from werkzeug.security import generate_password_hash

from database.db import get_connection


# =========================================================
# Helpers
# =========================================================

def get_institution_id():

    return session.get("institution_id")


def staff_list_redirect():

    return redirect(
        url_for("staff.staff_list")
    )


def portal_redirect():

    return redirect(
        url_for("portal.index")
    )


# =========================================================
# 1. List Staff
# =========================================================

def list_staff():

    institution_id = get_institution_id()

    if not institution_id:

        flash(
            "Institution information is missing.",
            "error"
        )

        return portal_redirect()

    search = request.args.get(
        "search",
        ""
    ).strip()

    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()

        if search:

            cur.execute("""
                SELECT
                    users.id,
                    users.institution_id,
                    users.full_name,
                    users.username,
                    users.email,
                    users.phone,
                    users.photo,
                    users.is_active,
                    users.created_at,
                    users.updated_at,
                    roles.name AS role_name

                FROM users

                JOIN roles
                    ON users.role_id = roles.id

                WHERE
                    users.institution_id = %s
                    AND roles.name = 'staff'
                    AND (
                        users.full_name ILIKE %s
                        OR users.username ILIKE %s
                        OR users.phone ILIKE %s
                    )

                ORDER BY
                    users.id DESC
            """, (
                institution_id,
                f"%{search}%",
                f"%{search}%",
                f"%{search}%"
            ))

        else:

            cur.execute("""
                SELECT
                    users.id,
                    users.institution_id,
                    users.full_name,
                    users.username,
                    users.email,
                    users.phone,
                    users.photo,
                    users.is_active,
                    users.created_at,
                    users.updated_at,
                    roles.name AS role_name

                FROM users

                JOIN roles
                    ON users.role_id = roles.id

                WHERE
                    users.institution_id = %s
                    AND roles.name = 'staff'

                ORDER BY
                    users.id DESC
            """, (
                institution_id,
            ))

        staff_members = cur.fetchall()

        return render_template(
            "staff/list.html",
            staff_members=staff_members,
            search=search
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "========== STAFF LIST ERROR =========="
        )

        print(
            repr(e)
        )

        raise

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()
            
def add_staff():

    institution_id = get_institution_id()

    if not institution_id:

        flash(
            "Institution information is missing.",
            "error"
        )

        return portal_redirect()

    conn = None
    cur = None

    try:

        if request.method == "GET":

            return render_template(
                "staff/add.html"
            )

        # -------------------------------------------------
        # Form values
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Photo
        # -------------------------------------------------

        photo = request.files.get(
            "photo"
        )

        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if not full_name:

            flash(
                "Full name is required.",
                "error"
            )

            return render_template(
                "staff/add.html"
            )

        if not username:

            flash(
                "Username is required.",
                "error"
            )

            return render_template(
                "staff/add.html"
            )

        if not password:

            flash(
                "Password is required.",
                "error"
            )

            return render_template(
                "staff/add.html"
            )

        if len(password) < 8:

            flash(
                "Password must be at least 8 characters.",
                "error"
            )

            return render_template(
                "staff/add.html"
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return render_template(
                "staff/add.html"
            )

        # -------------------------------------------------
        # Validate Photo
        # -------------------------------------------------

        photo_filename = None

        if photo and photo.filename:

            allowed_extensions = {
                "jpg",
                "jpeg",
                "png",
                "webp"
            }

            original_filename = secure_filename(
                photo.filename
            )

            extension = (
                original_filename
                .rsplit(".", 1)[-1]
                .lower()
            )

            if extension not in allowed_extensions:

                flash(
                    "Please upload a JPG, JPEG, PNG or WEBP image.",
                    "error"
                )

                return render_template(
                    "staff/add.html"
                )

            photo_filename = (
                f"staff_{uuid.uuid4().hex}.{extension}"
            )

        # -------------------------------------------------
        # Database
        # -------------------------------------------------

        conn = get_connection()
        cur = conn.cursor()

        # -------------------------------------------------
        # Username duplicate
        # -------------------------------------------------

        cur.execute("""
            SELECT
                id

            FROM users

            WHERE
                LOWER(username) = LOWER(%s)

            LIMIT 1
        """, (
            username,
        ))

        if cur.fetchone():

            flash(
                "Username already exists.",
                "error"
            )

            return render_template(
                "staff/add.html"
            )

        # -------------------------------------------------
        # Get staff role
        # -------------------------------------------------

        cur.execute("""
            SELECT
                id

            FROM roles

            WHERE
                name = 'staff'

            LIMIT 1
        """)

        role_data = cur.fetchone()

        if not role_data:

            conn.rollback()

            flash(
                "Staff role is not configured.",
                "error"
            )

            return render_template(
                "staff/add.html"
            )

        # -------------------------------------------------
        # Save Photo
        # -------------------------------------------------

        if photo_filename:

            upload_folder = os.path.join(
                "uploads",
                "staff"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            photo.save(
                os.path.join(
                    upload_folder,
                    photo_filename
                )
            )

        # -------------------------------------------------
        # Insert staff
        # -------------------------------------------------

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
                photo,
                is_active
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                TRUE
            )
        """, (
            institution_id,
            role_data["id"],
            full_name,
            username,
            email or None,
            phone or None,
            generate_password_hash(password),
            photo_filename
        ))

        conn.commit()

        flash(
            "Staff added successfully.",
            "success"
        )

        return staff_list_redirect()

    except Exception:

        if conn:
            conn.rollback()

        flash(
            "Unable to add staff member.",
            "error"
        )

        return render_template(
            "staff/add.html"
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()            


# =========================================================
# 3. Edit Staff
# =========================================================

def edit_staff(id):

    institution_id = get_institution_id()

    if not institution_id:

        flash(
            "Institution information is missing.",
            "error"
        )

        return portal_redirect()

    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()

        # -------------------------------------------------
        # Get staff
        # -------------------------------------------------

        cur.execute("""
            SELECT
                users.id,
                users.institution_id,
                users.full_name,
                users.username,
                users.email,
                users.phone,
                users.photo,
                users.is_active,
                roles.name AS role_name

            FROM users

            JOIN roles
                ON users.role_id = roles.id

            WHERE
                users.id = %s
                AND users.institution_id = %s
                AND roles.name = 'staff'

            LIMIT 1
        """, (
            id,
            institution_id
        ))

        staff = cur.fetchone()

        if not staff:

            flash(
                "Staff member not found.",
                "error"
            )

            return staff_list_redirect()

        # -------------------------------------------------
        # GET
        # -------------------------------------------------

        if request.method == "GET":

            return render_template(
                "staff/edit.html",
                staff=staff
            )

        # -------------------------------------------------
        # POST
        # -------------------------------------------------

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

        photo = request.files.get(
            "photo"
        )

        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if not full_name:

            flash(
                "Full name is required.",
                "error"
            )

            return render_template(
                "staff/edit.html",
                staff=staff
            )

        if not username:

            flash(
                "Username is required.",
                "error"
            )

            return render_template(
                "staff/edit.html",
                staff=staff
            )

        # -------------------------------------------------
        # Username duplicate
        # -------------------------------------------------

        cur.execute("""
            SELECT
                id

            FROM users

            WHERE
                LOWER(username) = LOWER(%s)
                AND id != %s

            LIMIT 1
        """, (
            username,
            id
        ))

        if cur.fetchone():

            flash(
                "Username already exists.",
                "error"
            )

            return render_template(
                "staff/edit.html",
                staff=staff
            )

        # -------------------------------------------------
        # Existing Photo
        # -------------------------------------------------

        current_photo = staff["photo"]

        new_photo = None

        # -------------------------------------------------
        # New Photo
        # -------------------------------------------------

        if photo and photo.filename:

            allowed_extensions = {
                "jpg",
                "jpeg",
                "png",
                "webp"
            }

            original_filename = secure_filename(
                photo.filename
            )

            extension = (
                original_filename
                .rsplit(".", 1)[-1]
                .lower()
            )

            if extension not in allowed_extensions:

                flash(
                    "Please upload a JPG, JPEG, PNG or WEBP image.",
                    "error"
                )

                return render_template(
                    "staff/edit.html",
                    staff=staff
                )

            new_photo = (
                f"staff_{uuid.uuid4().hex}.{extension}"
            )

            upload_folder = os.path.join(
                "uploads",
                "staff"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            photo.save(
                os.path.join(
                    upload_folder,
                    new_photo
                )
            )

        # -------------------------------------------------
        # Final Photo
        # -------------------------------------------------

        final_photo = (
            new_photo
            if new_photo
            else current_photo
        )

        # -------------------------------------------------
        # Update
        #
        # Role is intentionally NOT editable.
        # -------------------------------------------------

        cur.execute("""
            UPDATE users

            SET
                full_name = %s,
                username = %s,
                email = %s,
                phone = %s,
                photo = %s,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
        """, (
            full_name,
            username,
            email or None,
            phone or None,
            final_photo,
            id,
            institution_id
        ))

        if cur.rowcount != 1:

            conn.rollback()

            flash(
                "Staff member could not be updated.",
                "error"
            )

            return staff_list_redirect()

        conn.commit()

        # -------------------------------------------------
        # Delete Old Photo
        # -------------------------------------------------

        if new_photo and current_photo:

            old_photo_path = os.path.join(
                "uploads",
                "staff",
                current_photo
            )

            if os.path.exists(
                old_photo_path
            ):

                try:

                    os.remove(
                        old_photo_path
                    )

                except OSError:

                    pass

        flash(
            "Staff updated successfully.",
            "success"
        )

        return staff_list_redirect()

    except Exception:

        if conn:
            conn.rollback()

        flash(
            "Unable to update staff member.",
            "error"
        )

        return staff_list_redirect()

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()
            
            
            
# =========================================================
# 4. View Staff
# =========================================================

def view_staff(id):

    institution_id = get_institution_id()

    if not institution_id:

        flash(
            "Institution information is missing.",
            "error"
        )

        return portal_redirect()

    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()

        # -------------------------------------------------
        # Get Staff
        # -------------------------------------------------

        cur.execute("""
            SELECT
                users.id,
                users.full_name,
                users.username,
                users.email,
                users.phone,
                users.photo,
                users.is_active,
                roles.name AS role_name

            FROM users

            JOIN roles
                ON users.role_id = roles.id

            WHERE
                users.id = %s
                AND users.institution_id = %s
                AND roles.name = 'staff'

            LIMIT 1
        """, (
            id,
            institution_id
        ))

        staff = cur.fetchone()


        if not staff:

            flash(
                "Staff member not found.",
                "error"
            )

            return staff_list_redirect()


        # -------------------------------------------------
        # Get Assigned Classes
        # -------------------------------------------------

        cur.execute("""
            SELECT
                c.id,
                c.class_name

            FROM staff_classes sc

            JOIN classes c
                ON c.id = sc.class_id

            WHERE
                sc.staff_id = %s
                AND sc.institution_id = %s
                AND sc.is_active = TRUE

                AND c.institution_id = %s
                AND c.is_active = TRUE

            ORDER BY
                c.class_name
        """, (
            id,
            institution_id,
            institution_id
        ))

        classes = cur.fetchall()


        # -------------------------------------------------
        # Get Assigned Subjects
        # -------------------------------------------------

        cur.execute("""
            SELECT
                s.id,
                s.subject_name,
                c.class_name

            FROM staff_subjects ss

            JOIN subjects s
                ON s.id = ss.subject_id

            LEFT JOIN classes c
                ON c.id = s.class_id

            WHERE
                ss.staff_id = %s
                AND ss.institution_id = %s
                AND ss.is_active = TRUE

                AND s.institution_id = %s
                AND s.is_active = TRUE

            ORDER BY
                c.class_name,
                s.subject_name
        """, (
            id,
            institution_id,
            institution_id
        ))

        subjects = cur.fetchall()


        return render_template(
            "staff/view.html",

            staff=staff,

            classes=classes,

            subjects=subjects
        )


    except Exception:

        if conn:
            conn.rollback()

        flash(
            "Unable to load staff details.",
            "error"
        )

        return staff_list_redirect()


    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()            


# =========================================================
# 4. Toggle Staff Status
# POST only
# =========================================================

def toggle_staff_status(id):

    institution_id = get_institution_id()

    if not institution_id:

        flash(
            "Institution information is missing.",
            "error"
        )

        return portal_redirect()

    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()

        # -------------------------------------------------
        # Get staff
        # -------------------------------------------------

        cur.execute("""
            SELECT
                users.id,
                users.is_active

            FROM users

            JOIN roles
                ON users.role_id = roles.id

            WHERE
                users.id = %s
                AND users.institution_id = %s
                AND roles.name = 'staff'

            FOR UPDATE
        """, (
            id,
            institution_id
        ))

        staff = cur.fetchone()

        if not staff:

            flash(
                "Staff member not found.",
                "error"
            )

            return staff_list_redirect()

        new_status = not staff["is_active"]

        cur.execute("""
            UPDATE users

            SET
                is_active = %s,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
        """, (
            new_status,
            id,
            institution_id
        ))

        conn.commit()

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

        return staff_list_redirect()

    except Exception:

        if conn:
            conn.rollback()

        flash(
            "Unable to change staff status.",
            "error"
        )

        return staff_list_redirect()

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# 5. Assign Staff to Classes
# =========================================================

def assign_staff_classes(id):

    institution_id = session.get("institution_id")

    if not institution_id:

        flash(
            "Institution information is missing.",
            "error"
        )

        return portal_redirect()

    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()

        # -------------------------------------------------
        # Verify active staff
        # -------------------------------------------------

        cur.execute("""
            SELECT
                users.id,
                users.full_name

            FROM users

            JOIN roles
                ON users.role_id = roles.id

            WHERE
                users.id = %s
                AND users.institution_id = %s
                AND roles.name = 'staff'
                AND users.is_active = TRUE

            LIMIT 1
        """, (
            id,
            institution_id
        ))

        staff = cur.fetchone()

        if not staff:

            flash(
                "Active staff member not found.",
                "error"
            )

            return staff_list_redirect()

        # -------------------------------------------------
        # POST - Save assignments
        # -------------------------------------------------

        if request.method == "POST":

            selected_classes = request.form.getlist(
                "class_ids"
            )

            valid_class_ids = []

            for value in selected_classes:

                try:

                    class_id = int(value)

                    if class_id > 0:
                        valid_class_ids.append(class_id)

                except (TypeError, ValueError):

                    continue

            # Remove duplicate IDs

            valid_class_ids = list(
                set(valid_class_ids)
            )

            # -------------------------------------------------
            # Validate selected classes
            # -------------------------------------------------

            if valid_class_ids:

                cur.execute("""
                    SELECT
                        id

                    FROM classes

                    WHERE
                        institution_id = %s
                        AND is_active = TRUE
                        AND id = ANY(%s)
                """, (
                    institution_id,
                    valid_class_ids
                ))

                rows = cur.fetchall()

                allowed_class_ids = {
                    row["id"]
                    for row in rows
                }

                invalid_ids = (
                    set(valid_class_ids)
                    - allowed_class_ids
                )

                if invalid_ids:

                    conn.rollback()

                    flash(
                        "One or more selected classes are invalid or inactive.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "staff.assign_classes",
                            id=id
                        )
                    )

            # -------------------------------------------------
            # Remove old assignments
            # -------------------------------------------------

            cur.execute("""
                DELETE FROM staff_classes

                WHERE
                    staff_id = %s
                    AND institution_id = %s
            """, (
                id,
                institution_id
            ))

            # -------------------------------------------------
            # Insert new assignments
            # -------------------------------------------------

            for class_id in valid_class_ids:

                cur.execute("""
                    INSERT INTO staff_classes
                    (
                        institution_id,
                        staff_id,
                        class_id,
                        is_active
                    )

                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        TRUE
                    )

                    ON CONFLICT (staff_id, class_id)
                    DO UPDATE SET
                        institution_id = EXCLUDED.institution_id,
                        is_active = TRUE,
                        updated_at = NOW()
                """, (
                    institution_id,
                    id,
                    class_id
                ))

            conn.commit()

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

        # -------------------------------------------------
        # GET - Active classes
        # -------------------------------------------------

        cur.execute("""
            SELECT
                id,
                class_name

            FROM classes

            WHERE
                institution_id = %s
                AND is_active = TRUE

            ORDER BY
                class_name
        """, (
            institution_id,
        ))

        classes = cur.fetchall()

        # -------------------------------------------------
        # Get current assignments
        # -------------------------------------------------

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
            institution_id
        ))

        assigned_classes = cur.fetchall()

        assigned_class_ids = {
            row["class_id"]
            for row in assigned_classes
        }

        return render_template(
            "staff/assign_classes.html",
            staff=staff,
            classes=classes,
            assigned_class_ids=assigned_class_ids
        )

    except Exception:

        if conn:
            conn.rollback()

        flash(
            "Unable to update class assignments.",
            "error"
        )

        return redirect(
            url_for(
                "staff.assign_classes",
                id=id
            )
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# 6. Assign Staff to Subjects
# =========================================================

def assign_staff_subjects(id):

    institution_id = session.get("institution_id")

    if not institution_id:

        flash(
            "Institution information is missing.",
            "error"
        )

        return portal_redirect()

    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()

        # -------------------------------------------------
        # Verify active staff
        # -------------------------------------------------

        cur.execute("""
            SELECT
                users.id,
                users.full_name

            FROM users

            JOIN roles
                ON users.role_id = roles.id

            WHERE
                users.id = %s
                AND users.institution_id = %s
                AND roles.name = 'staff'
                AND users.is_active = TRUE

            LIMIT 1
        """, (
            id,
            institution_id
        ))

        staff = cur.fetchone()

        if not staff:

            flash(
                "Active staff member not found.",
                "error"
            )

            return staff_list_redirect()

        # -------------------------------------------------
        # POST - Save assignments
        # -------------------------------------------------

        if request.method == "POST":

            selected_subjects = request.form.getlist(
                "subject_ids"
            )

            valid_subject_ids = []

            for value in selected_subjects:

                try:

                    subject_id = int(value)

                    if subject_id > 0:
                        valid_subject_ids.append(subject_id)

                except (TypeError, ValueError):

                    continue

            # Remove duplicates

            valid_subject_ids = list(
                set(valid_subject_ids)
            )

            # -------------------------------------------------
            # Validate selected subjects
            # -------------------------------------------------

            if valid_subject_ids:

                cur.execute("""
                    SELECT
                        id

                    FROM subjects

                    WHERE
                        institution_id = %s
                        AND is_active = TRUE
                        AND id = ANY(%s)
                """, (
                    institution_id,
                    valid_subject_ids
                ))

                rows = cur.fetchall()

                allowed_subject_ids = {
                    row["id"]
                    for row in rows
                }

                invalid_ids = (
                    set(valid_subject_ids)
                    - allowed_subject_ids
                )

                if invalid_ids:

                    conn.rollback()

                    flash(
                        "One or more selected subjects are invalid or inactive.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "staff.assign_subjects",
                            id=id
                        )
                    )

            # -------------------------------------------------
            # Remove old assignments
            # -------------------------------------------------

            cur.execute("""
                DELETE FROM staff_subjects

                WHERE
                    staff_id = %s
                    AND institution_id = %s
            """, (
                id,
                institution_id
            ))

            # -------------------------------------------------
            # Insert new assignments
            # -------------------------------------------------

            for subject_id in valid_subject_ids:

                cur.execute("""
                    INSERT INTO staff_subjects
                    (
                        institution_id,
                        staff_id,
                        subject_id,
                        is_active
                    )

                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        TRUE
                    )

                    ON CONFLICT (staff_id, subject_id)
                    DO UPDATE SET
                        institution_id = EXCLUDED.institution_id,
                        is_active = TRUE,
                        updated_at = NOW()
                """, (
                    institution_id,
                    id,
                    subject_id
                ))

            conn.commit()

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

        # -------------------------------------------------
        # GET - Active subjects
        # -------------------------------------------------

        cur.execute("""
            SELECT
                s.id,
                s.subject_name,
                c.class_name

            FROM subjects s

            LEFT JOIN classes c
                ON s.class_id = c.id
                AND c.institution_id = s.institution_id

            WHERE
                s.institution_id = %s
                AND s.is_active = TRUE

            ORDER BY
                c.class_name,
                s.subject_name
        """, (
            institution_id,
        ))

        subjects = cur.fetchall()

        # -------------------------------------------------
        # Get current assignments
        # -------------------------------------------------

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
            institution_id
        ))

        assigned_subjects = cur.fetchall()

        assigned_subject_ids = {
            row["subject_id"]
            for row in assigned_subjects
        }

        return render_template(
            "staff/assign_subjects.html",
            staff=staff,
            subjects=subjects,
            assigned_subject_ids=assigned_subject_ids
        )

    except Exception:

        if conn:
            conn.rollback()

        flash(
            "Unable to update subject assignments.",
            "error"
        )

        return redirect(
            url_for(
                "staff.assign_subjects",
                id=id
            )
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()