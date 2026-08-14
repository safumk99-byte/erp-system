from flask import (
    render_template,
    request,
    session,
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

def _get_role_id(cur, role_name):

    cur.execute(
        """
        SELECT
            id

        FROM roles

        WHERE
            name = %s

        LIMIT 1
        """,
        (role_name,)
    )

    role = cur.fetchone()

    if not role:
        return None

    return role["id"]


def _redirect_to_student_list():

    return redirect(
        url_for("students.student_list")
    )


# =========================================================
# 1. List Students
# =========================================================

def list_students():

    institution_id = session.get("institution_id")

    if not institution_id:

        flash(
            "Institution information is missing.",
            "error"
        )

        return redirect(
            url_for("portal.index")
        )

    search = request.args.get(
        "search",
        ""
    ).strip()

    class_id = request.args.get(
        "class_id",
        ""
    ).strip()

    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()

        # -------------------------------------------------
        # Get active classes for filter
        # -------------------------------------------------

        cur.execute(
            """
            SELECT
                id,
                class_name

            FROM classes

            WHERE
                institution_id = %s
                AND is_active = TRUE

            ORDER BY
                class_name
            """,
            (
                institution_id,
            )
        )

        classes = cur.fetchall()

        # -------------------------------------------------
        # Check whether current user is staff
        # -------------------------------------------------

        is_staff = (
            session.get("role") == "staff"
        )

        # -------------------------------------------------
        # Build student query
        # -------------------------------------------------

        params = [
            institution_id
        ]

        where_conditions = [
            "students.institution_id = %s"
        ]

        if is_staff:

            where_conditions.append(
                """
                EXISTS (
                    SELECT 1
                    FROM staff_classes sc
                    WHERE
                        sc.staff_id = %s
                        AND sc.institution_id = %s
                        AND sc.class_id = students.class_id
                        AND sc.is_active = TRUE
                )
                """
            )

            params.extend([
                session.get("user_id"),
                institution_id
            ])

        if search:

            where_conditions.append(
                """
                (
                    students.full_name ILIKE %s
                    OR students.admission_no ILIKE %s
                )
                """
            )

            search_value = f"%{search}%"

            params.extend([
                search_value,
                search_value
            ])

        if class_id:

            try:

                class_id_int = int(class_id)

                where_conditions.append(
                    "students.class_id = %s"
                )

                params.append(
                    class_id_int
                )

            except (TypeError, ValueError):

                class_id = ""

        query = f"""
            SELECT
                students.*,
                classes.class_name

            FROM students

            LEFT JOIN classes
                ON students.class_id = classes.id
                AND classes.institution_id = students.institution_id

            WHERE
                {' AND '.join(where_conditions)}

            ORDER BY
                students.id DESC
        """

        cur.execute(
            query,
            tuple(params)
        )

        students = cur.fetchall()

        return render_template(
            "students/list.html",
            students=students,
            classes=classes,
            search=search,
            class_id=class_id
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# 2. Add Student
# =========================================================

def add_student():

    institution_id = session.get(
        "institution_id"
    )

    if not institution_id:

        flash(
            "Institution information is missing.",
            "error"
        )

        return redirect(
            url_for("portal.index")
        )

    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()

        # =================================================
        # Active Classes
        # =================================================

        cur.execute(
            """
            SELECT
                id,
                class_name

            FROM classes

            WHERE
                institution_id = %s
                AND is_active = TRUE

            ORDER BY
                class_name
            """,
            (
                institution_id,
            )
        )

        classes = cur.fetchall()


        # =================================================
        # POST
        # =================================================

        if request.method == "POST":

            full_name = request.form.get(
                "full_name",
                ""
            ).strip()

            gender = request.form.get(
                "gender",
                ""
            ).strip()

            date_of_birth = request.form.get(
                "date_of_birth",
                ""
            ).strip()

            class_id = request.form.get(
                "class_id",
                ""
            ).strip()

            parent_name = request.form.get(
                "parent_name",
                ""
            ).strip()

            parent_phone = request.form.get(
                "parent_phone",
                ""
            ).strip()

            parent_email = request.form.get(
                "parent_email",
                ""
            ).strip()

            parent_username = request.form.get(
                "parent_username",
                ""
            ).strip().lower()

            parent_password = request.form.get(
                "parent_password",
                ""
            )

            student_password = request.form.get(
                "student_password",
                ""
            )

            address = request.form.get(
                "address",
                ""
            ).strip()

            # =================================================
            # Photo
            # =================================================

            photo = request.files.get(
                "photo"
            )

            photo_filename = None


            # =================================================
            # Basic Validation
            # =================================================

            if not full_name:

                flash(
                    "Student name is required.",
                    "error"
                )

                return render_template(
                    "students/add.html",
                    classes=classes
                )


            if not gender:

                flash(
                    "Gender is required.",
                    "error"
                )

                return render_template(
                    "students/add.html",
                    classes=classes
                )


            if not date_of_birth:

                flash(
                    "Date of birth is required.",
                    "error"
                )

                return render_template(
                    "students/add.html",
                    classes=classes
                )


            if not class_id:

                flash(
                    "Class is required.",
                    "error"
                )

                return render_template(
                    "students/add.html",
                    classes=classes
                )


            try:

                class_id = int(class_id)

            except (
                TypeError,
                ValueError
            ):

                flash(
                    "Invalid class selected.",
                    "error"
                )

                return render_template(
                    "students/add.html",
                    classes=classes
                )


            if not parent_name:

                flash(
                    "Parent name is required.",
                    "error"
                )

                return render_template(
                    "students/add.html",
                    classes=classes
                )


            if not parent_phone:

                flash(
                    "Parent phone is required.",
                    "error"
                )

                return render_template(
                    "students/add.html",
                    classes=classes
                )


            if not parent_email:

                flash(
                    "Parent email is required.",
                    "error"
                )

                return render_template(
                    "students/add.html",
                    classes=classes
                )


            if not parent_username:

                flash(
                    "Parent username is required.",
                    "error"
                )

                return render_template(
                    "students/add.html",
                    classes=classes
                )


            if not parent_password:

                flash(
                    "Parent password is required.",
                    "error"
                )

                return render_template(
                    "students/add.html",
                    classes=classes
                )


            if not student_password:

                flash(
                    "Student password is required.",
                    "error"
                )

                return render_template(
                    "students/add.html",
                    classes=classes
                )


            # =================================================
            # Validate Photo
            # =================================================

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


                if "." not in original_filename:

                    flash(
                        "Invalid photo file.",
                        "error"
                    )

                    return render_template(
                        "students/add.html",
                        classes=classes
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
                        "students/add.html",
                        classes=classes
                    )


                photo_filename = (
                    f"student_{uuid.uuid4().hex}.{extension}"
                )


            # =================================================
            # Verify Class
            # =================================================

            cur.execute(
                """
                SELECT
                    id

                FROM classes

                WHERE
                    id = %s
                    AND institution_id = %s
                    AND is_active = TRUE

                LIMIT 1
                """,
                (
                    class_id,
                    institution_id
                )
            )

            selected_class = cur.fetchone()


            if not selected_class:

                flash(
                    "Selected class is invalid or inactive.",
                    "error"
                )

                return render_template(
                    "students/add.html",
                    classes=classes
                )


            # =================================================
            # Parent Username Check
            # =================================================

            cur.execute(
                """
                SELECT
                    id

                FROM users

                WHERE
                    LOWER(username) = LOWER(%s)

                LIMIT 1
                """,
                (
                    parent_username,
                )
            )

            if cur.fetchone():

                flash(
                    "Parent username already exists.",
                    "error"
                )

                return render_template(
                    "students/add.html",
                    classes=classes
                )


            # =================================================
            # Get Roles
            # =================================================

            parent_role_id = _get_role_id(
                cur,
                "parent"
            )

            student_role_id = _get_role_id(
                cur,
                "student"
            )


            if not parent_role_id:

                flash(
                    "Parent role is not configured.",
                    "error"
                )

                return render_template(
                    "students/add.html",
                    classes=classes
                )


            if not student_role_id:

                flash(
                    "Student role is not configured.",
                    "error"
                )

                return render_template(
                    "students/add.html",
                    classes=classes
                )


            # =================================================
            # Generate Admission Number
            # =================================================

            cur.execute(
                """
                SELECT
                    pg_advisory_xact_lock(
                        hashtext(%s)
                    )
                """,
                (
                    f"student-admission:{institution_id}",
                )
            )


            cur.execute(
                """
                SELECT
                    admission_no

                FROM students

                WHERE
                    institution_id = %s

                ORDER BY
                    id DESC

                LIMIT 1
                """,
                (
                    institution_id,
                )
            )


            last_student = cur.fetchone()


            if last_student:

                try:

                    last_number = int(
                        str(
                            last_student["admission_no"]
                        ).split("-")[-1]
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    last_number = 0

            else:

                last_number = 0


            admission_no = (
                f"STU-{last_number + 1:04d}"
            )


            # =================================================
            # Ensure Admission Number Is Unique
            # =================================================

            while True:

                cur.execute(
                    """
                    SELECT
                        id

                    FROM students

                    WHERE
                        institution_id = %s
                        AND admission_no = %s

                    LIMIT 1
                    """,
                    (
                        institution_id,
                        admission_no
                    )
                )


                if not cur.fetchone():

                    break


                last_number += 1

                admission_no = (
                    f"STU-{last_number:04d}"
                )


            # =================================================
            # Password Hashes
            # =================================================

            student_hashed_password = (
                generate_password_hash(
                    student_password
                )
            )

            parent_hashed_password = (
                generate_password_hash(
                    parent_password
                )
            )


            # =================================================
            # Create Student User
            # =================================================

            cur.execute(
                """
                INSERT INTO users
                (
                    institution_id,
                    role_id,
                    full_name,
                    username,
                    password,
                    is_active
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    TRUE
                )

                RETURNING id
                """,
                (
                    institution_id,
                    student_role_id,
                    full_name,
                    admission_no,
                    student_hashed_password
                )
            )


            student_user = cur.fetchone()


            if not student_user:

                raise RuntimeError(
                    "Student user could not be created."
                )


            student_user_id = (
                student_user["id"]
            )


            # =================================================
            # Create Parent User
            # =================================================

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
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    TRUE
                )

                RETURNING id
                """,
                (
                    institution_id,
                    parent_role_id,
                    parent_name,
                    parent_username,
                    parent_email,
                    parent_phone,
                    parent_hashed_password
                )
            )


            parent_user = cur.fetchone()


            if not parent_user:

                raise RuntimeError(
                    "Parent user could not be created."
                )


            parent_user_id = (
                parent_user["id"]
            )


            # =================================================
            # Create Student
            # =================================================

            cur.execute(
                """
                INSERT INTO students
                (
                    institution_id,
                    user_id,
                    class_id,
                    full_name,
                    admission_no,
                    gender,
                    date_of_birth,
                    address,
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
                    %s,
                    TRUE
                )

                RETURNING id
                """,
                (
                    institution_id,
                    student_user_id,
                    class_id,
                    full_name,
                    admission_no,
                    gender,
                    date_of_birth,
                    address or None,
                    photo_filename
                )
            )


            student = cur.fetchone()


            if not student:

                raise RuntimeError(
                    "Student record could not be created."
                )


            student_id = student["id"]


            # =================================================
            # Parent Relationship
            # =================================================

            cur.execute(
                """
                UPDATE students

                SET
                    parent_user_id = %s,
                    parent_name = %s,
                    parent_phone = %s,
                    updated_at = NOW()

                WHERE
                    id = %s
                    AND institution_id = %s
                """,
                (
                    parent_user_id,
                    parent_name,
                    parent_phone,
                    student_id,
                    institution_id
                )
            )


            # =================================================
            # Save Photo To Common Folder
            # =================================================

            if photo_filename:

                upload_folder = os.path.join(
                    "static",
                    "uploads"
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


            # =================================================
            # Commit
            # =================================================

            conn.commit()


            flash(
                f"Student added successfully. Admission No: {admission_no}",
                "success"
            )


            return redirect(
                url_for(
                    "students.student_list"
                )
            )


        # =================================================
        # GET
        # =================================================

        return render_template(
            "students/add.html",
            classes=classes
        )


    except Exception as e:

        if conn:
            conn.rollback()

        flash(
            "Unable to add student. Please check the details and try again.",
            "error"
        )

        return render_template(
            "students/add.html",
            classes=classes
        )


    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# 3. Edit Student
# =========================================================

def edit_student(id):

    institution_id = session.get(
        "institution_id"
    )

    if not institution_id:

        flash(
            "Institution information is missing.",
            "error"
        )

        return redirect(
            url_for("portal.index")
        )

    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()


        # =================================================
        # Active Classes
        # =================================================

        cur.execute(
            """
            SELECT
                id,
                class_name

            FROM classes

            WHERE
                institution_id = %s
                AND is_active = TRUE

            ORDER BY
                class_name
            """,
            (
                institution_id,
            )
        )

        classes = cur.fetchall()


        # =================================================
        # Get Student + Parent
        # =================================================

        cur.execute(
            """
            SELECT

                s.*,

                pu.full_name AS parent_user_name,
                pu.username AS parent_username,
                pu.email AS parent_email,
                pu.phone AS parent_user_phone

            FROM students s

            LEFT JOIN users pu
                ON pu.id = s.parent_user_id
                AND pu.institution_id = s.institution_id

            WHERE
                s.id = %s
                AND s.institution_id = %s

            LIMIT 1
            """,
            (
                id,
                institution_id
            )
        )

        student = cur.fetchone()


        if not student:

            flash(
                "Student not found.",
                "error"
            )

            return redirect(
                url_for(
                    "students.student_list"
                )
            )


        # =================================================
        # GET
        # =================================================

        if request.method == "GET":

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        # =================================================
        # Form Values
        # =================================================

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        gender = request.form.get(
            "gender",
            ""
        ).strip()

        date_of_birth = request.form.get(
            "date_of_birth",
            ""
        ).strip()

        class_id = request.form.get(
            "class_id",
            ""
        ).strip()

        parent_name = request.form.get(
            "parent_name",
            ""
        ).strip()

        parent_phone = request.form.get(
            "parent_phone",
            ""
        ).strip()

        parent_email = request.form.get(
            "parent_email",
            ""
        ).strip()

        parent_password = request.form.get(
            "parent_password",
            ""
        )

        address = request.form.get(
            "address",
            ""
        ).strip()


        # =================================================
        # Photo
        # =================================================

        photo = request.files.get(
            "photo"
        )

        photo_filename = None


        # =================================================
        # Validation
        # =================================================

        if not full_name:

            flash(
                "Student name is required.",
                "error"
            )

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        if not gender:

            flash(
                "Gender is required.",
                "error"
            )

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        if not date_of_birth:

            flash(
                "Date of birth is required.",
                "error"
            )

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        if not class_id:

            flash(
                "Class is required.",
                "error"
            )

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        try:

            class_id = int(class_id)

        except (
            TypeError,
            ValueError
        ):

            flash(
                "Invalid class selected.",
                "error"
            )

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        if not parent_name:

            flash(
                "Parent name is required.",
                "error"
            )

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        if not parent_phone:

            flash(
                "Parent phone is required.",
                "error"
            )

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        if not parent_email:

            flash(
                "Parent email is required.",
                "error"
            )

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        # =================================================
        # Validate Class
        # =================================================

        cur.execute(
            """
            SELECT
                id

            FROM classes

            WHERE
                id = %s
                AND institution_id = %s
                AND is_active = TRUE

            LIMIT 1
            """,
            (
                class_id,
                institution_id
            )
        )

        selected_class = cur.fetchone()


        if not selected_class:

            flash(
                "Selected class is invalid or inactive.",
                "error"
            )

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        # =================================================
        # Validate Photo
        # =================================================

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


            if "." not in original_filename:

                flash(
                    "Invalid photo file.",
                    "error"
                )

                return render_template(
                    "students/edit.html",
                    student=student,
                    classes=classes
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
                    "students/edit.html",
                    student=student,
                    classes=classes
                )


            photo_filename = (
                f"student_{uuid.uuid4().hex}.{extension}"
            )


        # =================================================
        # Update Student
        # =================================================

        if photo_filename:

            cur.execute(
                """
                UPDATE students

                SET
                    full_name = %s,
                    gender = %s,
                    date_of_birth = %s,
                    class_id = %s,
                    parent_name = %s,
                    parent_phone = %s,
                    address = %s,
                    photo = %s,
                    updated_at = NOW()

                WHERE
                    id = %s
                    AND institution_id = %s
                """,
                (
                    full_name,
                    gender,
                    date_of_birth,
                    class_id,
                    parent_name,
                    parent_phone,
                    address or None,
                    photo_filename,
                    id,
                    institution_id
                )
            )

        else:

            cur.execute(
                """
                UPDATE students

                SET
                    full_name = %s,
                    gender = %s,
                    date_of_birth = %s,
                    class_id = %s,
                    parent_name = %s,
                    parent_phone = %s,
                    address = %s,
                    updated_at = NOW()

                WHERE
                    id = %s
                    AND institution_id = %s
                """,
                (
                    full_name,
                    gender,
                    date_of_birth,
                    class_id,
                    parent_name,
                    parent_phone,
                    address or None,
                    id,
                    institution_id
                )
            )


        # =================================================
        # Update Parent User
        # =================================================

        if student["parent_user_id"]:

            if parent_password:

                if len(parent_password) < 6:

                    conn.rollback()

                    flash(
                        "Parent password must be at least 6 characters.",
                        "error"
                    )

                    return render_template(
                        "students/edit.html",
                        student=student,
                        classes=classes
                    )


                cur.execute(
                    """
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
                    """,
                    (
                        parent_name,
                        parent_email,
                        parent_phone,
                        generate_password_hash(
                            parent_password
                        ),
                        student["parent_user_id"],
                        institution_id
                    )
                )

            else:

                cur.execute(
                    """
                    UPDATE users

                    SET
                        full_name = %s,
                        email = %s,
                        phone = %s,
                        updated_at = NOW()

                    WHERE
                        id = %s
                        AND institution_id = %s
                    """,
                    (
                        parent_name,
                        parent_email,
                        parent_phone,
                        student["parent_user_id"],
                        institution_id
                    )
                )


        # =================================================
        # Save New Photo
        # =================================================

        if photo_filename:

            upload_folder = os.path.join(
                "static",
                "uploads"
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


        # =================================================
        # Commit
        # =================================================

        conn.commit()


        flash(
            "Student updated successfully.",
            "success"
        )


        return redirect(
            url_for(
                "students.view_student",
                id=id
            )
        )


    except Exception:

        if conn:
            conn.rollback()

        flash(
            "Unable to update student.",
            "error"
        )

        return redirect(
            url_for(
                "students.student_list"
            )
        )


    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# 4. Toggle Student Status
# =========================================================

def toggle_student_status(id):

    institution_id = session.get(
        "institution_id"
    )

    if not institution_id:

        flash(
            "Institution information is missing.",
            "error"
        )

        return redirect(
            url_for("portal.index")
        )

    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()

        # -------------------------------------------------
        # Get student
        # -------------------------------------------------

        cur.execute(
            """
            SELECT
                id,
                user_id,
                is_active

            FROM students

            WHERE
                id = %s
                AND institution_id = %s

            LIMIT 1
            """,
            (
                id,
                institution_id
            )
        )

        student = cur.fetchone()

        if not student:

            flash(
                "Student not found.",
                "error"
            )

            return _redirect_to_student_list()

        # -------------------------------------------------
        # Staff permission
        # -------------------------------------------------

        if session.get("role") == "staff":

            cur.execute(
                """
                SELECT
                    1

                FROM students s

                JOIN staff_classes sc
                    ON sc.class_id = s.class_id
                    AND sc.institution_id = s.institution_id

                WHERE
                    s.id = %s
                    AND s.institution_id = %s
                    AND sc.staff_id = %s
                    AND sc.is_active = TRUE

                LIMIT 1
                """,
                (
                    id,
                    institution_id,
                    session.get("user_id")
                )
            )

            if not cur.fetchone():

                flash(
                    "You don't have permission to change this student.",
                    "error"
                )

                return _redirect_to_student_list()

        new_status = not student["is_active"]

        # -------------------------------------------------
        # Update student
        # -------------------------------------------------

        cur.execute(
            """
            UPDATE students

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
                institution_id
            )
        )

        # -------------------------------------------------
        # Update student login account
        # -------------------------------------------------

        if student["user_id"]:

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
                    student["user_id"],
                    institution_id
                )
            )

        conn.commit()

        if new_status:

            flash(
                "Student activated successfully.",
                "success"
            )

        else:

            flash(
                "Student deactivated successfully.",
                "success"
            )

        return _redirect_to_student_list()

    except Exception:

        if conn:
            conn.rollback()

        flash(
            "Unable to update student status.",
            "error"
        )

        return _redirect_to_student_list()

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# 5. Student Profile
# =========================================================

def student_profile(id):

    institution_id = session.get(
        "institution_id"
    )

    if not institution_id:

        flash(
            "Institution information is missing.",
            "error"
        )

        return redirect(
            url_for("portal.index")
        )

    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()

        # -------------------------------------------------
        # Get student
        # -------------------------------------------------

        cur.execute(
            """
            SELECT
                students.*,
                classes.class_name

            FROM students

            LEFT JOIN classes
                ON students.class_id = classes.id
                AND classes.institution_id = students.institution_id

            WHERE
                students.id = %s
                AND students.institution_id = %s

            LIMIT 1
            """,
            (
                id,
                institution_id
            )
        )

        student = cur.fetchone()

        if not student:

            flash(
                "Student not found.",
                "error"
            )

            return _redirect_to_student_list()

        # -------------------------------------------------
        # Staff permission
        # -------------------------------------------------

        if session.get("role") == "staff":

            cur.execute(
                """
                SELECT
                    1

                FROM staff_classes

                WHERE
                    staff_id = %s
                    AND institution_id = %s
                    AND class_id = %s
                    AND is_active = TRUE

                LIMIT 1
                """,
                (
                    session.get("user_id"),
                    institution_id,
                    student["class_id"]
                )
            )

            if not cur.fetchone():

                flash(
                    "You don't have permission to view this student.",
                    "error"
                )

                return _redirect_to_student_list()

        # -------------------------------------------------
        # Student statistics
        # -------------------------------------------------

        cur.execute(
            """
            SELECT
                COUNT(*) AS total_days

            FROM attendance

            WHERE
                student_id = %s
                AND institution_id = %s
            """,
            (
                id,
                institution_id
            )
        )

        attendance_summary = cur.fetchone()

        # -------------------------------------------------
        # Attendance counts
        # -------------------------------------------------

        cur.execute(
            """
            SELECT
                COALESCE(
                    SUM(
                        CASE
                            WHEN status = 'present'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS present_count,

                COALESCE(
                    SUM(
                        CASE
                            WHEN status = 'absent'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS absent_count,

                COALESCE(
                    SUM(
                        CASE
                            WHEN status = 'leave'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS leave_count

            FROM attendance

            WHERE
                student_id = %s
                AND institution_id = %s
            """,
            (
                id,
                institution_id
            )
        )

        attendance_counts = cur.fetchone()

        # -------------------------------------------------
        # Return profile
        # -------------------------------------------------

        return render_template(
            "students/profile.html",
            student=student,
            attendance_summary=attendance_summary,
            attendance_counts=attendance_counts
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()