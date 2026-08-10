from datetime import date

from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
    jsonify
)

from database.db import get_connection


# =========================================================
# Allowed Attendance Statuses
# =========================================================

ALLOWED_STATUSES = {
    "Present",
    "Late",
    "Absent",
    "Leave"
}


# =========================================================
# Allowed Periods
# =========================================================

ALLOWED_PERIODS = {
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8
}


# =========================================================
# Verify Class Access
# =========================================================

def _class_is_allowed(cur, class_id):

    role = session.get("role")

    # -----------------------------------------------------
    # Institution Admin
    # -----------------------------------------------------

    if role == "institution_admin":

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
            session["institution_id"]
        ))

    # -----------------------------------------------------
    # Staff
    # -----------------------------------------------------

    elif role == "staff":

        cur.execute("""
            SELECT
                c.id

            FROM classes c

            JOIN staff_classes sc
                ON sc.class_id = c.id

            WHERE
                c.id = %s
                AND c.institution_id = %s

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

                AND c.is_active = TRUE
        """, (
            class_id,
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

    else:

        return False

    return cur.fetchone() is not None


# =========================================================
# Get Allowed Classes
# =========================================================

def _get_classes(cur):

    role = session.get("role")

    # -----------------------------------------------------
    # Institution Admin
    # -----------------------------------------------------

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
            session["institution_id"],
        ))

    # -----------------------------------------------------
    # Staff
    # -----------------------------------------------------

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

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

                AND c.is_active = TRUE

            ORDER BY c.class_name
        """, (
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

    else:

        return []

    return cur.fetchall()


# =========================================================
# Validate Period
# =========================================================

def _get_period_number(value):

    try:

        period_number = int(value)

    except (TypeError, ValueError):

        return None

    if period_number not in ALLOWED_PERIODS:

        return None

    return period_number


# =========================================================
# 1. Attendance Page
# =========================================================

def attendance_page():

    attendance_date = request.args.get(
        "date",
        str(date.today())
    )

    class_id = request.args.get(
        "class_id",
        ""
    )

    period_number = _get_period_number(
        request.args.get(
            "period_number",
            "1"
        )
    )

    if period_number is None:

        period_number = 1


    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    # =====================================================
    # Role Check
    # =====================================================

    if role not in (
        "institution_admin",
        "staff"
    ):

        cur.close()
        conn.close()

        return "Unauthorized", 403


    # =====================================================
    # Get Allowed Classes
    # =====================================================

    classes = _get_classes(cur)

    students = []


    # =====================================================
    # Selected Class
    # =====================================================

    if class_id:

        # -------------------------------------------------
        # Verify Class Access
        # -------------------------------------------------

        if not _class_is_allowed(
            cur,
            class_id
        ):

            cur.close()
            conn.close()

            flash(
                "You do not have access to this class.",
                "error"
            )

            return redirect(
                url_for(
                    "attendance.attendance_list"
                )
            )


        # -------------------------------------------------
        # Get Students + Attendance
        # -------------------------------------------------

        cur.execute("""
            SELECT
                s.id,
                s.admission_no,
                s.full_name,
                s.photo,
                s.parent_name,
                s.parent_phone,
                c.class_name,

                COALESCE(
                    a.status,
                    'Present'
                ) AS status

            FROM students s

            JOIN classes c
                ON s.class_id = c.id

            LEFT JOIN attendance a
                ON a.student_id = s.id
                AND a.institution_id = s.institution_id
                AND a.attendance_date = %s
                AND a.period_number = %s

            WHERE
                s.institution_id = %s
                AND s.class_id = %s
                AND s.is_active = TRUE

            ORDER BY
                s.full_name
        """, (
            attendance_date,
            period_number,
            session["institution_id"],
            class_id
        ))

        students = cur.fetchall()


    cur.close()
    conn.close()


    return render_template(
        "attendance/list.html",
        classes=classes,
        students=students,
        attendance_date=attendance_date,
        class_id=class_id,
        period_number=period_number
    )


# =========================================================
# 2. Mark Attendance
# =========================================================

# =========================================================
# 2. Mark Attendance
# =========================================================

def mark_attendance():

    attendance_date = request.form["attendance_date"]

    class_id = request.form["class_id"]

    period_number = request.form.get(
        "period_number",
        "1"
    )

    student_ids = request.form.getlist(
        "student_id"
    )

    # =========================================
    # Validate Period
    # =========================================

    try:

        period_number = int(
            period_number
        )

    except (TypeError, ValueError):

        flash(
            "Invalid period number.",
            "error"
        )

        return redirect(
            url_for(
                "attendance.attendance_list",
                date=attendance_date,
                class_id=class_id
            )
        )


    if period_number <= 0:

        flash(
            "Period number must be greater than zero.",
            "error"
        )

        return redirect(
            url_for(
                "attendance.attendance_list",
                date=attendance_date,
                class_id=class_id
            )
        )


    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    # =========================================
    # Verify Class Access
    # =========================================

    if role == "institution_admin":

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
            session["institution_id"]
        ))

    elif role == "staff":

        cur.execute("""
            SELECT
                c.id

            FROM classes c

            JOIN staff_classes sc
                ON sc.class_id = c.id

            WHERE
                c.id = %s
                AND c.institution_id = %s

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

                AND c.is_active = TRUE
        """, (
            class_id,
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    allowed_class = cur.fetchone()


    if not allowed_class:

        cur.close()
        conn.close()

        flash(
            "You do not have access to this class.",
            "error"
        )

        return redirect(
            url_for(
                "attendance.attendance_list"
            )
        )


    # =========================================
    # Verify Students + Save Attendance
    # =========================================

    for student_id in student_ids:

        # -------------------------------------
        # Verify Student
        # -------------------------------------

        cur.execute("""
            SELECT
                id

            FROM students

            WHERE
                id = %s
                AND institution_id = %s
                AND class_id = %s
                AND is_active = TRUE
        """, (
            student_id,
            session["institution_id"],
            class_id
        ))

        student = cur.fetchone()


        if not student:

            cur.close()
            conn.close()

            flash(
                "Invalid student access.",
                "error"
            )

            return redirect(
                url_for(
                    "attendance.attendance_list",
                    date=attendance_date,
                    class_id=class_id,
                    period_number=period_number
                )
            )


        # -------------------------------------
        # Get Status
        # -------------------------------------

        status = request.form.get(
            f"status_{student_id}",
            "Present"
        )


        allowed_statuses = {
            "Present",
            "Absent",
            "Leave",
            "Late"
        }


        if status not in allowed_statuses:

            cur.close()
            conn.close()

            flash(
                "Invalid attendance status.",
                "error"
            )

            return redirect(
                url_for(
                    "attendance.attendance_list",
                    date=attendance_date,
                    class_id=class_id,
                    period_number=period_number
                )
            )


        # -------------------------------------
        # Check Existing Attendance
        # -------------------------------------

        cur.execute("""
            SELECT
                id

            FROM attendance

            WHERE
                institution_id = %s
                AND student_id = %s
                AND attendance_date = %s
                AND period_number = %s
        """, (
            session["institution_id"],
            student_id,
            attendance_date,
            period_number
        ))


        row = cur.fetchone()


        # =====================================
        # Update Existing
        # =====================================

        if row:

            cur.execute("""
                UPDATE attendance

                SET
                    status = %s,
                    marked_by = %s,
                    updated_at = NOW()

                WHERE
                    id = %s
                    AND institution_id = %s
            """, (
                status,
                session["user_id"],
                row["id"],
                session["institution_id"]
            ))


        # =====================================
        # Insert New
        # =====================================

        else:

            cur.execute("""
                INSERT INTO attendance
                (
                    institution_id,
                    student_id,
                    attendance_date,
                    status,
                    marked_by,
                    period_number
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                session["institution_id"],
                student_id,
                attendance_date,
                status,
                session["user_id"],
                period_number
            ))


    # =========================================
    # Commit
    # =========================================

    conn.commit()

    cur.close()
    conn.close()


    flash(
        f"Attendance saved successfully for Period {period_number}.",
        "success"
    )


    return redirect(
        url_for(
            "attendance.attendance_list",
            date=attendance_date,
            class_id=class_id,
            period_number=period_number
        )
    )


# =========================================================
# 3. Get Student Popup
# =========================================================

def get_student_popup(student_id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    # =====================================================
    # Institution Admin
    # =====================================================

    if role == "institution_admin":

        cur.execute("""
            SELECT
                s.id,
                s.admission_no,
                s.full_name,
                s.photo,
                s.parent_name,
                s.parent_phone,
                c.class_name

            FROM students s

            JOIN classes c
                ON s.class_id = c.id

            WHERE
                s.id = %s
                AND s.institution_id = %s
                AND s.is_active = TRUE
        """, (
            student_id,
            session["institution_id"]
        ))


    # =====================================================
    # Staff
    # =====================================================

    elif role == "staff":

        cur.execute("""
            SELECT
                s.id,
                s.admission_no,
                s.full_name,
                s.photo,
                s.parent_name,
                s.parent_phone,
                c.class_name

            FROM students s

            JOIN classes c
                ON s.class_id = c.id

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                s.id = %s
                AND s.institution_id = %s
                AND s.is_active = TRUE

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE
        """, (
            student_id,
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))


    else:

        cur.close()
        conn.close()

        return jsonify({
            "success": False
        })


    student = cur.fetchone()

    cur.close()
    conn.close()


    if not student:

        return jsonify({
            "success": False
        })


    return jsonify({
        "success": True,
        "student": student
    })
    
# =========================================================
# 4. Monthly Attendance Summary
# =========================================================

def attendance_summary_data():

    month = request.args.get(
        "month",
        date.today().strftime("%Y-%m")
    )

    class_id = request.args.get(
        "class_id",
        ""
    )

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")

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
            session["institution_id"],
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

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

                AND c.is_active = TRUE

            ORDER BY c.class_name
        """, (
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    classes = cur.fetchall()

    students = []


    # =====================================================
    # Selected Class
    # =====================================================

    if class_id:

        if role == "institution_admin":

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
                session["institution_id"]
            ))

        elif role == "staff":

            cur.execute("""
                SELECT
                    c.id

                FROM classes c

                JOIN staff_classes sc
                    ON sc.class_id = c.id

                WHERE
                    c.id = %s
                    AND c.institution_id = %s

                    AND sc.institution_id = %s
                    AND sc.staff_id = %s
                    AND sc.is_active = TRUE

                    AND c.is_active = TRUE
            """, (
                class_id,
                session["institution_id"],
                session["institution_id"],
                session["user_id"]
            ))

        allowed_class = cur.fetchone()


        if not allowed_class:

            cur.close()
            conn.close()

            flash(
                "You do not have access to this class.",
                "error"
            )

            return redirect(
                url_for(
                    "attendance.attendance_summary"
                )
            )


        # =================================================
        # Monthly Student Attendance
        # =================================================

        cur.execute("""
            SELECT
                s.id,
                s.admission_no,
                s.full_name,

                COUNT(a.id) AS total_periods,

                COUNT(
                    CASE
                        WHEN a.status = 'Present'
                        THEN 1
                    END
                ) AS present_count,

                COUNT(
                    CASE
                        WHEN a.status = 'Late'
                        THEN 1
                    END
                ) AS late_count,

                COUNT(
                    CASE
                        WHEN a.status = 'Leave'
                        THEN 1
                    END
                ) AS leave_count,

                COUNT(
                    CASE
                        WHEN a.status = 'Absent'
                        THEN 1
                    END
                ) AS absent_count

            FROM students s

            LEFT JOIN attendance a
                ON a.student_id = s.id
                AND a.institution_id = s.institution_id

                AND TO_CHAR(
                    a.attendance_date,
                    'YYYY-MM'
                ) = %s

            WHERE
                s.institution_id = %s
                AND s.class_id = %s
                AND s.is_active = TRUE

            GROUP BY
                s.id,
                s.admission_no,
                s.full_name

            ORDER BY
                s.full_name
        """, (
            month,
            session["institution_id"],
            class_id
        ))

        students = cur.fetchall()


    # =====================================================
    # Calculate Attendance Percentage
    # =====================================================

    summary_students = []

    for student in students:

        total_periods = student[
            "total_periods"
        ] or 0

        present_count = student[
            "present_count"
        ] or 0

        late_count = student[
            "late_count"
        ] or 0

        leave_count = student[
            "leave_count"
        ] or 0

        absent_count = student[
            "absent_count"
        ] or 0


        # -----------------------------------------------
        # Attendance Percentage
        #
        # Late is treated as attended.
        # Leave is not counted as attended.
        # -----------------------------------------------

        attended_periods = (
            present_count
            + late_count
        )


        if total_periods > 0:

            attendance_percentage = round(
                (
                    attended_periods
                    / total_periods
                ) * 100,
                2
            )

        else:

            attendance_percentage = 0


        # -----------------------------------------------
        # Exam Eligibility
        # -----------------------------------------------

        if (
            total_periods > 0
            and attendance_percentage >= 60
        ):

            eligibility = "Eligible"

        else:

            eligibility = "Not Eligible"


        summary_students.append({
            "id": student["id"],
            "admission_no": student["admission_no"],
            "full_name": student["full_name"],
            "total_periods": total_periods,
            "present_count": present_count,
            "late_count": late_count,
            "leave_count": leave_count,
            "absent_count": absent_count,
            "attendance_percentage":
                attendance_percentage,
            "eligibility":
                eligibility
        })


    cur.close()
    conn.close()


    return render_template(
        "attendance/summary.html",
        classes=classes,
        students=summary_students,
        month=month,
        class_id=class_id
    )    