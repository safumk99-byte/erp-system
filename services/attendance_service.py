from datetime import date, datetime

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


ALLOWED_STATUSES = {
    "Present",
    "Late",
    "Absent",
    "Leave"
}

ALLOWED_PERIODS = set(range(1, 9))


# =========================================================
# Helpers
# =========================================================

def _get_period_number(value):

    try:
        period_number = int(value)
    except (TypeError, ValueError):
        return None

    if period_number not in ALLOWED_PERIODS:
        return None

    return period_number


def _valid_date(value):

    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except (TypeError, ValueError):
        return False


def _valid_month(value):

    try:
        datetime.strptime(value, "%Y-%m")
        return True
    except (TypeError, ValueError):
        return False


def _class_is_allowed(cur, class_id):

    role = session.get("role")
    institution_id = session.get("institution_id")
    user_id = session.get("user_id")

    if role == "institution_admin":

        cur.execute("""
            SELECT id
            FROM classes
            WHERE
                id = %s
                AND institution_id = %s
                AND is_active = TRUE
            LIMIT 1
        """, (
            class_id,
            institution_id
        ))

    elif role == "staff":

        cur.execute("""
            SELECT c.id
            FROM classes c
            JOIN staff_classes sc
                ON sc.class_id = c.id
                AND sc.institution_id = c.institution_id
            WHERE
                c.id = %s
                AND c.institution_id = %s
                AND c.is_active = TRUE
                AND sc.staff_id = %s
                AND sc.is_active = TRUE
            LIMIT 1
        """, (
            class_id,
            institution_id,
            user_id
        ))

    else:
        return False

    return cur.fetchone() is not None


def _get_classes(cur):

    role = session.get("role")
    institution_id = session.get("institution_id")
    user_id = session.get("user_id")

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
                AND sc.institution_id = c.institution_id
            WHERE
                c.institution_id = %s
                AND c.is_active = TRUE
                AND sc.staff_id = %s
                AND sc.is_active = TRUE
            ORDER BY c.class_name
        """, (
            institution_id,
            user_id
        ))

    else:
        return []

    return cur.fetchall()


def _attendance_redirect(
    attendance_date,
    class_id,
    period_number
):

    return redirect(
        url_for(
            "attendance.attendance_list",
            date=attendance_date,
            class_id=class_id,
            period_number=period_number
        )
    )


# =========================================================
# 1. Attendance Page
# =========================================================

def attendance_page():

    attendance_date = request.args.get(
        "date",
        str(date.today())
    ).strip()

    if not _valid_date(attendance_date):
        attendance_date = str(date.today())

    class_id = request.args.get(
        "class_id",
        ""
    ).strip()

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

    if role not in (
        "institution_admin",
        "staff"
    ):

        cur.close()
        conn.close()

        return "Unauthorized", 403

    classes = _get_classes(cur)
    students = []

    if class_id:

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
                AND c.institution_id = s.institution_id

            LEFT JOIN attendance a
                ON a.student_id = s.id
                AND a.institution_id = s.institution_id
                AND a.attendance_date = %s
                AND a.period_number = %s

            WHERE
                s.institution_id = %s
                AND s.class_id = %s
                AND s.is_active = TRUE

            ORDER BY s.full_name
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
# Attendance Notification
# =========================================================

def _create_attendance_notification(
    cur,
    student,
    status,
    attendance_date,
    period_number
):

    if status not in (
        "Absent",
        "Leave"
    ):
        return

    parent_user_id = student["parent_user_id"]

    if not parent_user_id:
        return

    if status == "Absent":

        message = (
            f'{student["full_name"]} was marked absent '
            f'on {attendance_date} '
            f'(Period {period_number}).'
        )

    else:

        message = (
            f'{student["full_name"]} was marked on leave '
            f'on {attendance_date} '
            f'(Period {period_number}).'
        )

    cur.execute("""
        INSERT INTO notifications
        (
            institution_id,
            user_id,
            notification_type,
            title,
            message
        )
        VALUES
        (%s, %s, %s, %s, %s)
    """, (
        student["institution_id"],
        parent_user_id,
        "attendance",
        "Attendance Alert",
        message
    ))


# =========================================================
# 2. Mark Attendance
# =========================================================

def mark_attendance():

    attendance_date = request.form.get(
        "attendance_date",
        ""
    ).strip()

    class_id = request.form.get(
        "class_id",
        ""
    ).strip()

    period_number = _get_period_number(
        request.form.get(
            "period_number",
            "1"
        )
    )

    student_ids = request.form.getlist(
        "student_id"
    )

    if not _valid_date(attendance_date):

        flash(
            "Invalid attendance date.",
            "error"
        )

        return redirect(
            url_for(
                "attendance.attendance_list"
            )
        )

    if period_number is None:

        flash(
            "Invalid period number.",
            "error"
        )

        return _attendance_redirect(
            attendance_date,
            class_id,
            1
        )

    if not class_id:

        flash(
            "Please select a class.",
            "error"
        )

        return redirect(
            url_for(
                "attendance.attendance_list",
                date=attendance_date
            )
        )

    if not student_ids:

        flash(
            "No students were submitted.",
            "error"
        )

        return _attendance_redirect(
            attendance_date,
            class_id,
            period_number
        )

    conn = get_connection()
    cur = conn.cursor()

    try:

        if not _class_is_allowed(
            cur,
            class_id
        ):

            flash(
                "You do not have access to this class.",
                "error"
            )

            conn.rollback()

            return redirect(
                url_for(
                    "attendance.attendance_list"
                )
            )

        for student_id in student_ids:

            cur.execute("""
                SELECT
                    id,
                    full_name,
                    institution_id,
                    parent_user_id

                FROM students

                WHERE
                    id = %s
                    AND institution_id = %s
                    AND class_id = %s
                    AND is_active = TRUE

                LIMIT 1
            """, (
                student_id,
                session["institution_id"],
                class_id
            ))

            student = cur.fetchone()

            if not student:

                raise ValueError(
                    "Invalid student access."
                )

            status = request.form.get(
                f"status_{student_id}",
                "Present"
            )

            if status not in ALLOWED_STATUSES:

                raise ValueError(
                    "Invalid attendance status."
                )

            cur.execute("""
                SELECT
                    id,
                    status

                FROM attendance

                WHERE
                    institution_id = %s
                    AND student_id = %s
                    AND attendance_date = %s
                    AND period_number = %s

                LIMIT 1
            """, (
                session["institution_id"],
                student_id,
                attendance_date,
                period_number
            ))

            existing = cur.fetchone()

            if existing:

                previous_status = existing["status"]

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
                    existing["id"],
                    session["institution_id"]
                ))

                if (
                    status in (
                        "Absent",
                        "Leave"
                    )
                    and status != previous_status
                ):

                    _create_attendance_notification(
                        cur,
                        student,
                        status,
                        attendance_date,
                        period_number
                    )

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
                    (%s, %s, %s, %s, %s, %s)
                """, (
                    session["institution_id"],
                    student_id,
                    attendance_date,
                    status,
                    session["user_id"],
                    period_number
                ))

                if status in (
                    "Absent",
                    "Leave"
                ):

                    _create_attendance_notification(
                        cur,
                        student,
                        status,
                        attendance_date,
                        period_number
                    )

        conn.commit()

    except ValueError as error:

        conn.rollback()

        flash(
            str(error),
            "error"
        )

        return _attendance_redirect(
            attendance_date,
            class_id,
            period_number
        )

    except Exception:

        conn.rollback()

        flash(
            "Unable to save attendance. No changes were saved.",
            "error"
        )

        return _attendance_redirect(
            attendance_date,
            class_id,
            period_number
        )

    finally:

        cur.close()
        conn.close()

    flash(
        f"Attendance saved successfully for Period {period_number}.",
        "success"
    )

    return _attendance_redirect(
        attendance_date,
        class_id,
        period_number
    )


# =========================================================
# 3. Student Popup
# =========================================================

def get_student_popup(student_id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")
    institution_id = session.get("institution_id")
    user_id = session.get("user_id")

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
                AND c.institution_id = s.institution_id

            WHERE
                s.id = %s
                AND s.institution_id = %s
                AND s.is_active = TRUE

            LIMIT 1
        """, (
            student_id,
            institution_id
        ))

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
                AND c.institution_id = s.institution_id

            JOIN staff_classes sc
                ON sc.class_id = s.class_id
                AND sc.institution_id = s.institution_id

            WHERE
                s.id = %s
                AND s.institution_id = %s
                AND s.is_active = TRUE
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

            LIMIT 1
        """, (
            student_id,
            institution_id,
            user_id
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

    # -----------------------------------------------------
    # Student Photo URL
    # -----------------------------------------------------

    photo_url = None

    if student["photo"]:

        photo_url = url_for(
            "students.student_photo",
            filename=student["photo"]
        )

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return jsonify({
        "success": True,

        "student": {
            "id": student["id"],
            "admission_no": student["admission_no"],
            "full_name": student["full_name"],
            "photo": photo_url,
            "parent_name": student["parent_name"],
            "parent_phone": student["parent_phone"],
            "class_name": student["class_name"]
        }
    })


# =========================================================
# 4. Monthly Attendance Summary
# =========================================================

def attendance_summary_data():

    # -----------------------------------------------------
    # Attendance Rule
    # 7 Late = 1 Absent
    # -----------------------------------------------------

    LATE_TO_ABSENT = 7

    month = request.args.get(
        "month",
        date.today().strftime("%Y-%m")
    ).strip()

    class_id = request.args.get(
        "class_id",
        ""
    ).strip()

    if not _valid_month(month):

        month = date.today().strftime("%Y-%m")

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")

    if role not in (
        "institution_admin",
        "staff"
    ):

        cur.close()
        conn.close()

        return "Unauthorized", 403

    # -----------------------------------------------------
    # Get allowed classes
    # -----------------------------------------------------

    classes = _get_classes(cur)

    students = []

    # -----------------------------------------------------
    # Selected Class
    # -----------------------------------------------------

    if class_id:

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
                    "attendance.attendance_summary_page"
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

    # -----------------------------------------------------
    # Calculate Summary
    # -----------------------------------------------------

    summary_students = []

    for student in students:

        total_periods = (
            student["total_periods"] or 0
        )

        present_count = (
            student["present_count"] or 0
        )

        late_count = (
            student["late_count"] or 0
        )

        leave_count = (
            student["leave_count"] or 0
        )

        absent_count = (
            student["absent_count"] or 0
        )

        # -------------------------------------------------
        # Convert Late to Absent
        #
        # Every 7 Late = 1 Absent
        # -------------------------------------------------

        converted_absent = (
            late_count // LATE_TO_ABSENT
        )

        remaining_late = (
            late_count % LATE_TO_ABSENT
        )

        # -------------------------------------------------
        # Effective counts
        # -------------------------------------------------

        effective_absent = (
            absent_count
            + converted_absent
        )

        # -------------------------------------------------
        # Attended periods
        #
        # Only Present counts as attended.
        # Converted Late periods become Absent.
        # Remaining Late stays Late.
        # -------------------------------------------------

        attended_periods = present_count

        # -------------------------------------------------
        # Effective total
        #
        # We keep the original number of attendance
        # records as the total number of periods.
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Eligibility
        # -------------------------------------------------

        eligibility = (
            "Eligible"
            if (
                total_periods > 0
                and attendance_percentage >= 60
            )
            else
            "Not Eligible"
        )

        # -------------------------------------------------
        # Summary
        # -------------------------------------------------

        summary_students.append({

            "id":
                student["id"],

            "admission_no":
                student["admission_no"],

            "full_name":
                student["full_name"],

            "total_periods":
                total_periods,

            "present_count":
                present_count,

            # Original Late count
            "late_count":
                late_count,

            # Late remaining after conversion
            "remaining_late":
                remaining_late,

            # Number of Late converted to Absent
            "converted_absent":
                converted_absent,

            # Actual Absent + converted Late
            "absent_count":
                effective_absent,

            "leave_count":
                leave_count,

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
    
# =========================================================
# 5. Today's 8 Period Attendance Progress
# =========================================================

def today_attendance_page():

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

        flash(
            "Institution information is missing.",
            "error"
        )

        return redirect(
            url_for("portal.index")
        )

    if role not in (
        "institution_admin",
        "staff"
    ):

        return "Unauthorized", 403

    today = date.today()

    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()

        # =================================================
        # Get accessible classes
        # =================================================

        classes = _get_classes(cur)

        # =================================================
        # Selected class
        # =================================================

        class_id = request.args.get(
            "class_id",
            ""
        ).strip()

        selected_class = None

        if class_id:

            try:

                class_id = int(class_id)

            except (TypeError, ValueError):

                class_id = ""

        # =================================================
        # Validate selected class
        # =================================================

        if class_id:

            if not _class_is_allowed(
                cur,
                class_id
            ):

                flash(
                    "You do not have access to this class.",
                    "error"
                )

                return redirect(
                    url_for(
                        "attendance.today_attendance"
                    )
                )

            cur.execute("""
                SELECT
                    id,
                    class_name

                FROM classes

                WHERE
                    id = %s
                    AND institution_id = %s

                LIMIT 1
            """, (
                class_id,
                institution_id
            ))

            selected_class = cur.fetchone()

        # =================================================
        # Period Data
        # =================================================

        periods = []

        for period_number in range(1, 9):

            period = {
                "period_number": period_number,
                "total_students": 0,
                "marked_students": 0,
                "present": 0,
                "late": 0,
                "leave": 0,
                "absent": 0,
                "status": "Not Started",
                "students": []
            }

            # -------------------------------------------------
            # Only load student attendance when class selected
            # -------------------------------------------------

            if class_id:

                cur.execute("""
                    SELECT
                        s.id,
                        s.admission_no,
                        s.full_name,
                        s.photo,

                        COALESCE(
                            a.status,
                            'Not Marked'
                        ) AS attendance_status

                    FROM students s

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
                    today,
                    period_number,
                    institution_id,
                    class_id
                ))

                students = cur.fetchall()

                period["total_students"] = len(
                    students
                )

                for student in students:

                    status = student[
                        "attendance_status"
                    ]

                    if status != "Not Marked":

                        period[
                            "marked_students"
                        ] += 1

                    if status == "Present":

                        period["present"] += 1

                    elif status == "Late":

                        period["late"] += 1

                    elif status == "Leave":

                        period["leave"] += 1

                    elif status == "Absent":

                        period["absent"] += 1

                    period["students"].append({
                        "id": student["id"],
                        "admission_no":
                            student["admission_no"],
                        "full_name":
                            student["full_name"],
                        "photo":
                            student["photo"],
                        "status":
                            status
                    })

                # -------------------------------------------------
                # Determine period status
                # -------------------------------------------------

                if period["total_students"] == 0:

                    period["status"] = "No Students"

                elif (
                    period["marked_students"]
                    == period["total_students"]
                ):

                    period["status"] = "Completed"

                elif period["marked_students"] > 0:

                    period["status"] = "Partial"

                else:

                    period["status"] = "Not Started"

            periods.append(
                period
            )

        # =================================================
        # Current Progress
        # =================================================

        completed_periods = sum(
            1
            for period in periods
            if period["status"] == "Completed"
        )

        partial_periods = sum(
            1
            for period in periods
            if period["status"] == "Partial"
        )

        started_periods = sum(
            1
            for period in periods
            if period["marked_students"] > 0
        )

        # =================================================
        # Find latest period with attendance
        # =================================================

        latest_period = None

        for period in periods:

            if period["marked_students"] > 0:

                latest_period = period[
                    "period_number"
                ]

        return render_template(
            "attendance/today.html",
            classes=classes,
            periods=periods,
            selected_class=selected_class,
            class_id=class_id,
            attendance_date=today,
            completed_periods=completed_periods,
            partial_periods=partial_periods,
            started_periods=started_periods,
            latest_period=latest_period
        )

    except Exception:

        if conn:
            conn.rollback()

        flash(
            "Unable to load today's attendance progress.",
            "error"
        )

        return redirect(
            url_for(
                "attendance.attendance_list"
            )
        )

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()   