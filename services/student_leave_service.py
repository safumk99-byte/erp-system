from datetime import date

from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from services.notification_service import (
    notify_student_and_parent
)

from database.db import get_connection


# =========================================================
# Helper: Get Current Student
# =========================================================

def _get_current_student(cur):

    institution_id = session.get(
        "institution_id"
    )

    user_id = session.get(
        "user_id"
    )

    role = session.get(
        "role"
    )


    if not institution_id or not user_id:

        return None


    # =====================================================
    # Student Login
    # =====================================================

    if role == "student":

        student_id = session.get(
            "student_id"
        )


        if not student_id:

            return None


        cur.execute("""
            SELECT
                id,
                institution_id,
                full_name,
                parent_user_id

            FROM students

            WHERE
                id = %s
                AND institution_id = %s
                AND is_active = TRUE

            LIMIT 1
        """, (
            student_id,
            institution_id
        ))


        return cur.fetchone()


    # =====================================================
    # Parent Login
    # =====================================================

    if role == "parent":

        cur.execute("""
            SELECT
                id,
                institution_id,
                full_name,
                parent_user_id

            FROM students

            WHERE
                parent_user_id = %s
                AND institution_id = %s
                AND is_active = TRUE

            ORDER BY
                id

            LIMIT 1
        """, (
            user_id,
            institution_id
        ))


        return cur.fetchone()


    return None


# =========================================================
# 1. Student Leave Page
# =========================================================

def student_leave_page():

    institution_id = session.get(
        "institution_id"
    )


    if not institution_id:

        return "Unauthorized", 403


    conn = get_connection()
    cur = conn.cursor()


    try:

        # -------------------------------------------------
        # Get Current Student
        # -------------------------------------------------

        student = _get_current_student(
            cur
        )


        if not student:

            flash(
                "Student not found.",
                "error"
            )

            return redirect(
                url_for(
                    "portal.index"
                )
            )


        # -------------------------------------------------
        # Student ID
        # -------------------------------------------------

        student_id = student[
            "id"
        ]


        # -------------------------------------------------
        # Get Leave Requests
        # -------------------------------------------------

        cur.execute("""
            SELECT
                id,
                leave_date,
                reason,
                status,
                review_remarks,
                created_at

            FROM student_leave_requests

            WHERE
                student_id = %s
                AND institution_id = %s

            ORDER BY
                leave_date DESC,
                id DESC
        """, (
            student_id,
            institution_id
        ))


        leave_requests = cur.fetchall()


        return render_template(
            "student_leave/form.html",
            leave_requests=leave_requests,
            today=str(
                date.today()
            )
        )


    finally:

        cur.close()
        conn.close()


# =========================================================
# 2. Submit Student Leave
# =========================================================

def submit_student_leave():

    institution_id = session.get(
        "institution_id"
    )


    if not institution_id:

        return "Unauthorized", 403


    leave_date = request.form.get(
        "leave_date"
    )


    reason = request.form.get(
        "reason",
        ""
    ).strip()


    # =====================================================
    # Validation
    # =====================================================

    if not leave_date:

        flash(
            "Please select a leave date.",
            "error"
        )

        return redirect(
            url_for(
                "student_leave.student_leave_page_route"
            )
        )


    if not reason:

        flash(
            "Please enter the reason for leave.",
            "error"
        )

        return redirect(
            url_for(
                "student_leave.student_leave_page_route"
            )
        )


    conn = get_connection()
    cur = conn.cursor()


    try:

        # =================================================
        # Get Current Student
        # =================================================

        student = _get_current_student(
            cur
        )


        if not student:

            flash(
                "Student not found.",
                "error"
            )

            return redirect(
                url_for(
                    "student_leave.student_leave_page_route"
                )
            )


        # =================================================
        # Student ID
        # =================================================

        student_id = student[
            "id"
        ]


        # =================================================
        # Duplicate Check
        # =================================================

        cur.execute("""
            SELECT
                id

            FROM student_leave_requests

            WHERE
                student_id = %s
                AND institution_id = %s
                AND leave_date = %s
                AND status IN (
                    'Pending',
                    'Approved'
                )

            LIMIT 1
        """, (
            student_id,
            institution_id,
            leave_date
        ))


        existing = cur.fetchone()


        if existing:

            flash(
                "A leave request already exists for this date.",
                "error"
            )

            return redirect(
                url_for(
                    "student_leave.student_leave_page_route"
                )
            )


        # =================================================
        # Insert Leave Request
        # =================================================

        cur.execute("""
            INSERT INTO student_leave_requests
            (
                institution_id,
                student_id,
                leave_date,
                reason,
                status
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                'Pending'
            )
        """, (
            institution_id,
            student_id,
            leave_date,
            reason
        ))


        conn.commit()


        flash(
            "Leave application submitted successfully.",
            "success"
        )


        return redirect(
            url_for(
                "student_leave.student_leave_page_route"
            )
        )


    except Exception:

        conn.rollback()


        flash(
            "Unable to submit leave request.",
            "error"
        )


        return redirect(
            url_for(
                "student_leave.student_leave_page_route"
            )
        )


    finally:

        cur.close()
        conn.close()


# =========================================================
# 3. Student Leave Requests
# =========================================================

def student_leave_requests():

    institution_id = session.get(
        "institution_id"
    )


    role = session.get(
        "role"
    )


    if not institution_id:

        return "Unauthorized", 403


    if role not in (
        "institution_admin",
        "staff"
    ):

        return "Unauthorized", 403


    conn = get_connection()
    cur = conn.cursor()


    try:

        # =================================================
        # Institution Admin
        # =================================================

        if role == "institution_admin":

            cur.execute("""
                SELECT
                    lr.id,
                    lr.leave_date,
                    lr.reason,
                    lr.status,
                    lr.created_at,

                    s.id AS student_id,
                    s.full_name AS student_name,
                    s.admission_no,

                    c.class_name

                FROM student_leave_requests lr

                JOIN students s
                    ON lr.student_id = s.id

                LEFT JOIN classes c
                    ON s.class_id = c.id

                WHERE
                    lr.institution_id = %s
                    AND s.institution_id = %s

                ORDER BY
                    CASE
                        WHEN lr.status = 'Pending'
                        THEN 1
                        ELSE 2
                    END,

                    lr.leave_date DESC,
                    lr.id DESC
            """, (
                institution_id,
                institution_id
            ))


        # =================================================
        # Staff
        # =================================================

        else:

            cur.execute("""
                SELECT DISTINCT
                    lr.id,
                    lr.leave_date,
                    lr.reason,
                    lr.status,
                    lr.created_at,

                    s.id AS student_id,
                    s.full_name AS student_name,
                    s.admission_no,

                    c.class_name

                FROM student_leave_requests lr

                JOIN students s
                    ON lr.student_id = s.id

                LEFT JOIN classes c
                    ON s.class_id = c.id

                JOIN staff_classes sc
                    ON sc.class_id = s.class_id

                WHERE
                    lr.institution_id = %s
                    AND s.institution_id = %s

                    AND sc.institution_id = %s
                    AND sc.staff_id = %s
                    AND sc.is_active = TRUE

                ORDER BY
                    CASE
                        WHEN lr.status = 'Pending'
                        THEN 1
                        ELSE 2
                    END,

                    lr.leave_date DESC,
                    lr.id DESC
            """, (
                institution_id,
                institution_id,
                institution_id,
                session.get(
                    "user_id"
                )
            ))


        requests = cur.fetchall()


        return render_template(
            "student_leave/requests.html",
            requests=requests
        )


    finally:

        cur.close()
        conn.close()


# =========================================================
# 4. Review Student Leave
# =========================================================

def review_student_leave():

    institution_id = session.get(
        "institution_id"
    )


    user_id = session.get(
        "user_id"
    )


    role = session.get(
        "role"
    )


    if not institution_id or not user_id:

        return "Unauthorized", 403


    if role not in (
        "institution_admin",
        "staff"
    ):

        return "Unauthorized", 403


    request_id = request.form.get(
        "request_id"
    )


    action = request.form.get(
        "action"
    )


    review_remarks = request.form.get(
        "review_remarks",
        ""
    ).strip()


    # =====================================================
    # Validate Request
    # =====================================================

    if not request_id:

        flash(
            "Invalid leave request.",
            "error"
        )

        return redirect(
            url_for(
                "student_leave.student_leave_requests_route"
            )
        )


    if action not in (
        "approve",
        "reject"
    ):

        flash(
            "Invalid action.",
            "error"
        )

        return redirect(
            url_for(
                "student_leave.student_leave_requests_route"
            )
        )


    conn = get_connection()
    cur = conn.cursor()


    try:

        # =================================================
        # Find Leave Request
        # =================================================

        if role == "institution_admin":

            cur.execute("""
                SELECT
                    lr.id,
                    lr.student_id,
                    lr.leave_date,
                    lr.status

                FROM student_leave_requests lr

                JOIN students s
                    ON lr.student_id = s.id

                WHERE
                    lr.id = %s
                    AND lr.institution_id = %s
                    AND s.institution_id = %s

                FOR UPDATE
            """, (
                request_id,
                institution_id,
                institution_id
            ))


        else:

            cur.execute("""
                SELECT
                    lr.id,
                    lr.student_id,
                    lr.leave_date,
                    lr.status

                FROM student_leave_requests lr

                JOIN students s
                    ON lr.student_id = s.id

                JOIN staff_classes sc
                    ON sc.class_id = s.class_id

                WHERE
                    lr.id = %s
                    AND lr.institution_id = %s
                    AND s.institution_id = %s

                    AND sc.institution_id = %s
                    AND sc.staff_id = %s
                    AND sc.is_active = TRUE

                FOR UPDATE
            """, (
                request_id,
                institution_id,
                institution_id,
                institution_id,
                user_id
            ))


        leave_request = cur.fetchone()


        if not leave_request:

            flash(
                "Leave request not found or you do not have permission.",
                "error"
            )

            return redirect(
                url_for(
                    "student_leave.student_leave_requests_route"
                )
            )


        # =================================================
        # Already Reviewed
        # =================================================

        if leave_request["status"] != "Pending":

            flash(
                "This leave request has already been reviewed.",
                "error"
            )

            return redirect(
                url_for(
                    "student_leave.student_leave_requests_route"
                )
            )


        # =================================================
        # Reject
        # =================================================

        if action == "reject":

            cur.execute("""
                UPDATE student_leave_requests

                SET
                    status = 'Rejected',
                    reviewed_by = %s,
                    reviewed_at = NOW(),
                    review_remarks = %s,
                    updated_at = NOW()

                WHERE
                    id = %s
                    AND institution_id = %s
            """, (
                user_id,
                review_remarks or None,
                request_id,
                institution_id
            ))


            # ---------------------------------------------
            # Notification
            # ---------------------------------------------

            notify_student_and_parent(
                student_id=leave_request[
                    "student_id"
                ],
                module_name="Leave Application",
                approved=False,
                remarks=review_remarks,
                institution_id=institution_id,
                cur=cur
            )


            # ---------------------------------------------
            # Commit
            # ---------------------------------------------

            conn.commit()


            flash(
                "Leave request rejected and notification sent.",
                "success"
            )


            return redirect(
                url_for(
                    "student_leave.student_leave_requests_route"
                )
            )


        # =================================================
        # Approve
        # =================================================

        cur.execute("""
            UPDATE student_leave_requests

            SET
                status = 'Approved',
                reviewed_by = %s,
                reviewed_at = NOW(),
                review_remarks = %s,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
        """, (
            user_id,
            review_remarks or None,
            request_id,
            institution_id
        ))


        # =================================================
        # Attendance
        # =================================================

        cur.execute("""
            SELECT
                id,
                period_number

            FROM attendance

            WHERE
                student_id = %s
                AND institution_id = %s
                AND attendance_date = %s

            ORDER BY
                period_number
        """, (
            leave_request[
                "student_id"
            ],
            institution_id,
            leave_request[
                "leave_date"
            ]
        ))


        attendance_rows = cur.fetchall()


        # =================================================
        # Existing Attendance Records
        # =================================================

        if attendance_rows:

            for attendance in attendance_rows:

                cur.execute("""
                    UPDATE attendance

                    SET
                        status = 'Leave',
                        marked_by = %s,
                        updated_at = NOW()

                    WHERE
                        id = %s
                        AND institution_id = %s
                """, (
                    user_id,
                    attendance["id"],
                    institution_id
                ))


        # =================================================
        # No Attendance Record
        # =================================================

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
                    'Leave',
                    %s,
                    %s
                )
            """, (
                institution_id,
                leave_request[
                    "student_id"
                ],
                leave_request[
                    "leave_date"
                ],
                user_id,
                1
            ))


        # =================================================
        # Notification
        # =================================================

        notify_student_and_parent(
            student_id=leave_request[
                "student_id"
            ],
            module_name="Leave Application",
            approved=True,
            remarks=review_remarks,
            institution_id=institution_id,
            cur=cur
        )


        # =================================================
        # Commit Everything Together
        # =================================================

        conn.commit()


        flash(
            "Leave approved, attendance updated, and notification sent.",
            "success"
        )


        return redirect(
            url_for(
                "student_leave.student_leave_requests_route"
            )
        )


    except Exception:

        conn.rollback()


        flash(
            "Unable to review leave request. No changes were saved.",
            "error"
        )


        return redirect(
            url_for(
                "student_leave.student_leave_requests_route"
            )
        )


    finally:

        cur.close()
        conn.close()