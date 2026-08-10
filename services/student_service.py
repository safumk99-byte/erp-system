import os
import uuid
from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from database.db import get_connection
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename


# =========================================================
# 1. List Students
# =========================================================

def list_students():

    search = request.args.get(
        "search",
        ""
    ).strip()

    class_id = request.args.get(
        "class_id",
        ""
    ).strip()

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")
    institution_id = session.get("institution_id")
    user_id = session.get("user_id")


    # =====================================================
    # Get Allowed Classes
    # =====================================================

    if role == "institution_admin":

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
            institution_id,
        ))


    elif role == "staff":

        cur.execute("""
            SELECT DISTINCT
                c.id,
                c.class_name

            FROM classes c

            JOIN staff_classes sc
                ON sc.class_id = c.id

            WHERE
                c.institution_id = %s
                AND c.is_active = TRUE

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

            ORDER BY c.class_name
        """, (
            institution_id,
            institution_id,
            user_id
        ))


    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    classes = cur.fetchall()


    # =====================================================
    # Validate Selected Class
    # =====================================================

    selected_class_id = None

    if class_id:

        try:

            selected_class_id = int(class_id)

        except (TypeError, ValueError):

            selected_class_id = None


    # =====================================================
    # Institution Admin → Students
    # =====================================================

    if role == "institution_admin":

        query = """
            SELECT
                students.*,
                classes.class_name

            FROM students

            JOIN classes
                ON students.class_id = classes.id

            WHERE
                students.institution_id = %s
        """

        params = [
            institution_id
        ]


        if selected_class_id is not None:

            query += """
                AND students.class_id = %s
            """

            params.append(
                selected_class_id
            )


        if search:

            query += """
                AND (
                    students.full_name ILIKE %s
                    OR students.admission_no ILIKE %s
                    OR students.parent_name ILIKE %s
                )
            """

            search_value = f"%{search}%"

            params.extend([
                search_value,
                search_value,
                search_value
            ])


        query += """
            ORDER BY students.id DESC
        """


        cur.execute(
            query,
            params
        )


    # =====================================================
    # Staff → Students
    # =====================================================

    elif role == "staff":

        query = """
            SELECT DISTINCT
                students.*,
                classes.class_name

            FROM students

            JOIN classes
                ON students.class_id = classes.id

            JOIN staff_classes
                ON staff_classes.class_id = students.class_id

            WHERE
                students.institution_id = %s

                AND staff_classes.institution_id = %s
                AND staff_classes.staff_id = %s
                AND staff_classes.is_active = TRUE
        """

        params = [
            institution_id,
            institution_id,
            user_id
        ]


        if selected_class_id is not None:

            query += """
                AND students.class_id = %s
            """

            params.append(
                selected_class_id
            )


        if search:

            query += """
                AND (
                    students.full_name ILIKE %s
                    OR students.admission_no ILIKE %s
                    OR students.parent_name ILIKE %s
                )
            """

            search_value = f"%{search}%"

            params.extend([
                search_value,
                search_value,
                search_value
            ])


        query += """
            ORDER BY students.id DESC
        """


        cur.execute(
            query,
            params
        )


    students = cur.fetchall()


    cur.close()
    conn.close()


    return render_template(
        "students/list.html",
        students=students,
        classes=classes,
        search=search,
        class_id=class_id
    )

# =========================================================
# 2. Add Student
# =========================================================

def add_student():

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")
    institution_id = session.get("institution_id")
    user_id = session.get("user_id")

    # =====================================================
    # Basic Session Validation
    # =====================================================

    if not institution_id:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    # =====================================================
    # Get Allowed Classes
    # =====================================================

    if role == "institution_admin":

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
            institution_id,
        ))


    elif role == "staff":

        cur.execute("""
            SELECT DISTINCT
                c.id,
                c.class_name

            FROM classes c

            JOIN staff_classes sc
                ON sc.class_id = c.id

            WHERE
                c.institution_id = %s
                AND c.is_active = TRUE

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

            ORDER BY c.class_name
        """, (
            institution_id,
            institution_id,
            user_id
        ))


    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    classes = cur.fetchall()


    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        gender = request.form.get(
            "gender"
        )

        date_of_birth = request.form.get(
            "date_of_birth"
        ) or None

        class_id = request.form.get(
            "class_id"
        )

        parent_name = request.form.get(
            "parent_name",
            ""
        ).strip()

        parent_phone = request.form.get(
            "parent_phone",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        student_password = request.form.get(
            "student_password",
            ""
        ).strip()


        # =================================================
        # Validate Full Name
        # =================================================

        if not full_name:

            flash(
                "Student name is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/add.html",
                classes=classes
            )


        if len(full_name) > 150:

            flash(
                "Student name is too long.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/add.html",
                classes=classes
            )


        # =================================================
        # Validate Gender
        # =================================================

        allowed_genders = {
            "Male",
            "Female",
            "Other"
        }

        if gender not in allowed_genders:

            flash(
                "Please select a valid gender.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/add.html",
                classes=classes
            )


        # =================================================
        # Validate Class
        # =================================================

        if not class_id:

            flash(
                "Please select a class.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/add.html",
                classes=classes
            )


        try:

            class_id = int(class_id)

        except (TypeError, ValueError):

            flash(
                "Invalid class selected.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/add.html",
                classes=classes
            )


        # =================================================
        # Verify Class Belongs To Institution
        # =================================================

        cur.execute("""
            SELECT
                id

            FROM classes

            WHERE
                id = %s
                AND institution_id = %s
                AND is_active = TRUE
        """, (
            class_id,
            institution_id
        ))

        selected_class = cur.fetchone()


        if not selected_class:

            flash(
                "Invalid class selected.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/add.html",
                classes=classes
            )


        # =================================================
        # Staff → Assigned Class Check
        # =================================================

        if role == "staff":

            cur.execute("""
                SELECT
                    id

                FROM staff_classes

                WHERE
                    institution_id = %s
                    AND staff_id = %s
                    AND class_id = %s
                    AND is_active = TRUE
            """, (
                institution_id,
                user_id,
                class_id
            ))

            assigned_class = cur.fetchone()


            if not assigned_class:

                flash(
                    "You cannot add a student to an unassigned class.",
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "students/add.html",
                    classes=classes
                )


        # =================================================
        # Validate Parent Name
        # =================================================

        if parent_name and len(parent_name) > 150:

            flash(
                "Parent name is too long.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/add.html",
                classes=classes
            )


        # =================================================
        # Validate Parent Phone
        # =================================================

        if parent_phone and len(parent_phone) > 30:

            flash(
                "Parent phone number is too long.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/add.html",
                classes=classes
            )


        # =================================================
        # Student Login Password
        # =================================================

        if not student_password:

            flash(
                "Student login password is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/add.html",
                classes=classes
            )


        if len(student_password) < 6:

            flash(
                "Student password must be at least 6 characters.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/add.html",
                classes=classes
            )


        # =================================================
        # Get Institution Admission Prefix
        # =================================================

        cur.execute("""
            SELECT
                admission_prefix

            FROM institutions

            WHERE
                id = %s
        """, (
            institution_id,
        ))

        institution = cur.fetchone()


        if not institution:

            flash(
                "Institution information not found.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/add.html",
                classes=classes
            )


        prefix = (
            institution["admission_prefix"]
            or ""
        ).strip()


        if not prefix:

            flash(
                "Admission number prefix is not configured for this institution.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/add.html",
                classes=classes
            )


        # =================================================
        # Generate Admission Number
        # =================================================

        cur.execute("""
            SELECT
                admission_no

            FROM students

            WHERE
                institution_id = %s

            ORDER BY id DESC

            LIMIT 1
        """, (
            institution_id,
        ))

        last_student = cur.fetchone()


        number = 1


        if last_student:

            last_admission_no = (
                last_student["admission_no"]
                or ""
            ).strip()


            try:

                last_number = int(
                    last_admission_no.rsplit(
                        "-",
                        1
                    )[1]
                )

                number = last_number + 1

            except (
                ValueError,
                IndexError
            ):

                flash(
                    "Unable to generate the next admission number. Please check the existing admission number format.",
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "students/add.html",
                    classes=classes
                )


        admission_no = (
            f"{prefix}-{number:04d}"
        )


        # =================================================
        # Check Admission Number
        # =================================================

        cur.execute("""
            SELECT
                id

            FROM students

            WHERE
                institution_id = %s
                AND admission_no = %s
        """, (
            institution_id,
            admission_no
        ))

        existing_student = cur.fetchone()


        if existing_student:

            flash(
                "Generated admission number already exists. Please try again.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/add.html",
                classes=classes
            )


        # =================================================
        # Check User Account
        # =================================================

        cur.execute("""
            SELECT
                id

            FROM users

            WHERE
                institution_id = %s
                AND username = %s
        """, (
            institution_id,
            admission_no
        ))

        existing_user = cur.fetchone()


        if existing_user:

            flash(
                "A login account already exists for this admission number.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/add.html",
                classes=classes
            )


        # =================================================
        # Create User + Student
        # =================================================

        try:

            hashed_password = generate_password_hash(
                student_password
            )


            # ---------------------------------------------
            # Create Student User Account
            # ---------------------------------------------

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

                VALUES
                (
                    %s,
                    6,
                    %s,
                    %s,
                    %s,
                    TRUE
                )

                RETURNING id
            """, (
                institution_id,
                full_name,
                admission_no,
                hashed_password
            ))


            user_row = cur.fetchone()


            if not user_row:

                raise RuntimeError(
                    "Student user account could not be created."
                )


            student_user_id = user_row["id"]


            # ---------------------------------------------
            # Create Student
            # ---------------------------------------------

            cur.execute("""
                INSERT INTO students
                (
                    institution_id,
                    admission_no,
                    full_name,
                    gender,
                    date_of_birth,
                    class_id,
                    parent_name,
                    parent_phone,
                    address,
                    user_id,
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
                    %s,
                    TRUE
                )
            """, (
                institution_id,
                admission_no,
                full_name,
                gender,
                date_of_birth,
                class_id,
                parent_name,
                parent_phone,
                address,
                student_user_id
            ))


            # ---------------------------------------------
            # Commit Both Together
            # ---------------------------------------------

            conn.commit()


        except Exception:

            conn.rollback()

            flash(
                "Unable to add student. No changes were saved.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/add.html",
                classes=classes
            )


        # =================================================
        # Success
        # =================================================

        cur.close()
        conn.close()


        flash(
            f"Student added successfully. Login ID: {admission_no}",
            "success"
        )


        return redirect(
            url_for(
                "students.student_list"
            )
        )


    # =====================================================
    # GET
    # =====================================================

    cur.close()
    conn.close()


    return render_template(
        "students/add.html",
        classes=classes
    )



# =========================================================
# 3. Edit Student
# =========================================================

def edit_student(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")
    institution_id = session.get("institution_id")
    user_id = session.get("user_id")

    # =====================================================
    # Basic Session Validation
    # =====================================================

    if not institution_id:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    # =====================================================
    # Get Allowed Classes
    # =====================================================

    if role == "institution_admin":

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
            institution_id,
        ))


    elif role == "staff":

        cur.execute("""
            SELECT DISTINCT
                c.id,
                c.class_name

            FROM classes c

            JOIN staff_classes sc
                ON sc.class_id = c.id

            WHERE
                c.institution_id = %s
                AND c.is_active = TRUE

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

            ORDER BY c.class_name
        """, (
            institution_id,
            institution_id,
            user_id
        ))


    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    classes = cur.fetchall()


    # =====================================================
    # Verify Student Access
    # =====================================================

    if role == "institution_admin":

        cur.execute("""
            SELECT
                *

            FROM students

            WHERE
                id = %s
                AND institution_id = %s
        """, (
            id,
            institution_id
        ))


    elif role == "staff":

        cur.execute("""
            SELECT DISTINCT
                students.*

            FROM students

            JOIN staff_classes
                ON staff_classes.class_id = students.class_id

            WHERE
                students.id = %s
                AND students.institution_id = %s
                AND students.is_active = TRUE

                AND staff_classes.institution_id = %s
                AND staff_classes.staff_id = %s
                AND staff_classes.is_active = TRUE
        """, (
            id,
            institution_id,
            institution_id,
            user_id
        ))


    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    student = cur.fetchone()


    # =====================================================
    # Student Not Found / No Permission
    # =====================================================

    if not student:

        cur.close()
        conn.close()

        flash(
            "You do not have permission to edit this student.",
            "error"
        )

        return redirect(
            url_for(
                "students.student_list"
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

        gender = request.form.get(
            "gender"
        )

        date_of_birth = request.form.get(
            "date_of_birth"
        ) or None

        class_id = request.form.get(
            "class_id"
        )

        parent_name = request.form.get(
            "parent_name",
            ""
        ).strip()

        parent_phone = request.form.get(
            "parent_phone",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()


        # =================================================
        # Validate Full Name
        # =================================================

        if not full_name:

            flash(
                "Student name is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        if len(full_name) > 150:

            flash(
                "Student name is too long.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        # =================================================
        # Validate Gender
        # =================================================

        allowed_genders = {
            "Male",
            "Female",
            "Other"
        }

        if gender not in allowed_genders:

            flash(
                "Please select a valid gender.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        # =================================================
        # Validate Date of Birth
        # =================================================

        if not date_of_birth:

            flash(
                "Date of birth is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        # =================================================
        # Validate Class
        # =================================================

        if not class_id:

            flash(
                "Please select a class.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        try:

            class_id = int(class_id)

        except (TypeError, ValueError):

            flash(
                "Invalid class selected.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        # =================================================
        # Verify Class Belongs To Institution
        # =================================================

        cur.execute("""
            SELECT
                id

            FROM classes

            WHERE
                id = %s
                AND institution_id = %s
                AND is_active = TRUE
        """, (
            class_id,
            institution_id
        ))

        selected_class = cur.fetchone()


        if not selected_class:

            flash(
                "Invalid class selected.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        # =================================================
        # Staff → Assigned Class Check
        # =================================================

        if role == "staff":

            cur.execute("""
                SELECT
                    id

                FROM staff_classes

                WHERE
                    institution_id = %s
                    AND staff_id = %s
                    AND class_id = %s
                    AND is_active = TRUE
            """, (
                institution_id,
                user_id,
                class_id
            ))

            assigned_class = cur.fetchone()


            if not assigned_class:

                flash(
                    "You cannot assign this student to an unassigned class.",
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "students/edit.html",
                    student=student,
                    classes=classes
                )


        # =================================================
        # Validate Parent Name
        # =================================================

        if not parent_name:

            flash(
                "Parent name is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        if len(parent_name) > 150:

            flash(
                "Parent name is too long.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        # =================================================
        # Validate Parent Phone
        # =================================================

        if not parent_phone:

            flash(
                "Parent phone number is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        if len(parent_phone) > 30:

            flash(
                "Parent phone number is too long.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        # =================================================
        # Update Student
        # =================================================

        try:

            cur.execute("""
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
            """, (
                full_name,
                gender,
                date_of_birth,
                class_id,
                parent_name,
                parent_phone,
                address,
                id,
                institution_id
            ))


            if cur.rowcount != 1:

                raise RuntimeError(
                    "Student update failed."
                )


            conn.commit()


        except Exception:

            conn.rollback()

            flash(
                "Unable to update student. No changes were saved.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "students/edit.html",
                student=student,
                classes=classes
            )


        # =================================================
        # Success
        # =================================================

        cur.close()
        conn.close()


        flash(
            "Student updated successfully.",
            "success"
        )


        return redirect(
            url_for(
                "students.student_list"
            )
        )


    # =====================================================
    # GET
    # =====================================================

    cur.close()
    conn.close()


    return render_template(
        "students/edit.html",
        student=student,
        classes=classes
    )


# =========================================================
# 4. Toggle Student Status
# =========================================================

def toggle_student_status(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")
    institution_id = session.get("institution_id")
    staff_user_id = session.get("user_id")


    # =====================================================
    # Basic Session Validation
    # =====================================================

    if not institution_id:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    # =====================================================
    # Verify Student Access
    # =====================================================

    if role == "institution_admin":

        cur.execute("""
            SELECT
                s.is_active,
                s.user_id

            FROM students s

            WHERE
                s.id = %s
                AND s.institution_id = %s
        """, (
            id,
            institution_id
        ))


    elif role == "staff":

        cur.execute("""
            SELECT DISTINCT
                s.is_active,
                s.user_id

            FROM students s

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                s.id = %s
                AND s.institution_id = %s

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE
        """, (
            id,
            institution_id,
            institution_id,
            staff_user_id
        ))


    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    student = cur.fetchone()


    # =====================================================
    # Student Not Found / No Permission
    # =====================================================

    if not student:

        cur.close()
        conn.close()

        flash(
            "You do not have permission to change this student's status.",
            "error"
        )

        return redirect(
            url_for(
                "students.student_list"
            )
        )


    # =====================================================
    # Calculate New Status
    # =====================================================

    new_status = not student["is_active"]

    student_user_id = student["user_id"]


    # =====================================================
    # Update Student + User Together
    # =====================================================

    try:

        # -----------------------------------------------
        # Update Student
        # -----------------------------------------------

        cur.execute("""
            UPDATE students

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


        if cur.rowcount != 1:

            raise RuntimeError(
                "Student status update failed."
            )


        # -----------------------------------------------
        # Update Student Login Account
        # -----------------------------------------------

        if student_user_id is not None:

            cur.execute("""
                UPDATE users

                SET
                    is_active = %s

                WHERE
                    id = %s
                    AND institution_id = %s
            """, (
                new_status,
                student_user_id,
                institution_id
            ))


            if cur.rowcount != 1:

                raise RuntimeError(
                    "Student login account status update failed."
                )


        # -----------------------------------------------
        # Commit Both Changes
        # -----------------------------------------------

        conn.commit()


    except Exception:

        conn.rollback()

        flash(
            "Unable to change student status. No changes were saved.",
            "error"
        )

        cur.close()
        conn.close()

        return redirect(
            url_for(
                "students.student_list"
            )
        )


    # =====================================================
    # Close Connection
    # =====================================================

    cur.close()
    conn.close()


    # =====================================================
    # Success Message
    # =====================================================

    if new_status:

        flash(
            "Student and student login account activated successfully.",
            "success"
        )

    else:

        flash(
            "Student and student login account deactivated successfully.",
            "success"
        )


    return redirect(
        url_for(
            "students.student_list"
        )
    )
    
# =========================================================
# 5. Student Profile
# =========================================================

def student_profile(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")
    institution_id = session.get("institution_id")
    user_id = session.get("user_id")

    # =====================================================
    # Basic Session Validation
    # =====================================================

    if not institution_id:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    # =====================================================
    # Institution Admin
    # =====================================================

    if role == "institution_admin":

        cur.execute("""
            SELECT
                s.id,
                s.institution_id,
                s.admission_no,
                s.full_name,
                s.gender,
                s.date_of_birth,
                s.parent_name,
                s.parent_phone,
                s.address,
                s.photo,
                s.is_active,
                s.created_at,
                s.updated_at,
                s.class_id,
                s.user_id,
                s.parent_user_id,

                c.class_name,

                u.is_active AS user_active

            FROM students s

            LEFT JOIN classes c
                ON c.id = s.class_id

            LEFT JOIN users u
                ON u.id = s.user_id

            WHERE
                s.id = %s
                AND s.institution_id = %s
        """, (
            id,
            institution_id
        ))


    # =====================================================
    # Staff
    # =====================================================

    elif role == "staff":

        cur.execute("""
            SELECT DISTINCT
                s.id,
                s.institution_id,
                s.admission_no,
                s.full_name,
                s.gender,
                s.date_of_birth,
                s.parent_name,
                s.parent_phone,
                s.address,
                s.photo,
                s.is_active,
                s.created_at,
                s.updated_at,
                s.class_id,
                s.user_id,
                s.parent_user_id,

                c.class_name,

                u.is_active AS user_active

            FROM students s

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            LEFT JOIN classes c
                ON c.id = s.class_id

            LEFT JOIN users u
                ON u.id = s.user_id

            WHERE
                s.id = %s
                AND s.institution_id = %s

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE
        """, (
            id,
            institution_id,
            institution_id,
            user_id
        ))


    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    student = cur.fetchone()


    # =====================================================
    # Student Not Found / No Access
    # =====================================================

    if not student:

        cur.close()
        conn.close()

        flash(
            "Student not found or you do not have permission to view this student.",
            "error"
        )

        return redirect(
            url_for(
                "students.student_list"
            )
        )


    # =====================================================
    # Close Database
    # =====================================================

    cur.close()
    conn.close()


    # =====================================================
    # Render Profile
    # =====================================================

    return render_template(
        "students/profile.html",
        student=student
    )    