from datetime import date

from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from database.db import get_connection


def student_leave_page():

    conn = get_connection()
    cur = conn.cursor()

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
        session["student_id"],
        session["institution_id"]
    ))

    leave_requests = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "student_leave/form.html",
        leave_requests=leave_requests,
        today=str(date.today())
    )


def submit_student_leave():

    leave_date = request.form.get(
        "leave_date"
    )

    reason = request.form.get(
        "reason",
        ""
    ).strip()


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


    # Verify student belongs to current institution

    cur.execute("""
        SELECT
            id

        FROM students

        WHERE
            id = %s
            AND institution_id = %s
            AND is_active = TRUE
    """, (
        session["student_id"],
        session["institution_id"]
    ))

    student = cur.fetchone()


    if not student:

        cur.close()
        conn.close()

        flash(
            "Student not found.",
            "error"
        )

        return redirect(
            url_for(
                "student_leave.student_leave_page_route"
            )
        )


    # Prevent duplicate pending/approved request

    cur.execute("""
        SELECT
            id

        FROM student_leave_requests

        WHERE
            student_id = %s
            AND institution_id = %s
            AND leave_date = %s
            AND status IN ('Pending', 'Approved')
    """, (
        session["student_id"],
        session["institution_id"],
        leave_date
    ))

    existing = cur.fetchone()


    if existing:

        cur.close()
        conn.close()

        flash(
            "A leave request already exists for this date.",
            "error"
        )

        return redirect(
            url_for(
                "student_leave.student_leave_page_route"
            )
        )


    # Create leave request

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
        session["institution_id"],
        session["student_id"],
        leave_date,
        reason
    ))


    conn.commit()

    cur.close()
    conn.close()


    flash(
        "Leave application submitted successfully.",
        "success"
    )


    return redirect(
        url_for(
            "student_leave.student_leave_page_route"
        )
    )
    
def student_leave_requests():

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")

    # ---------------------------------
    # Institution Admin
    # ---------------------------------

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
            session["institution_id"],
            session["institution_id"]
        ))

    # ---------------------------------
    # Staff
    # ---------------------------------

    elif role == "staff":

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
            session["institution_id"],
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    requests = cur.fetchall()

    cur.close()
    conn.close()


    return render_template(
        "student_leave/requests.html",
        requests=requests
    )
    
def review_student_leave():

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

    role = session.get("role")


    # ---------------------------------
    # Verify Leave Request Access
    # ---------------------------------

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
            session["institution_id"],
            session["institution_id"]
        ))

    elif role == "staff":

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
            session["institution_id"],
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    leave_request = cur.fetchone()


    if not leave_request:

        conn.rollback()
        cur.close()
        conn.close()

        flash(
            "Leave request not found or you do not have permission.",
            "error"
        )

        return redirect(
            url_for(
                "student_leave.student_leave_requests_route"
            )
        )


    # ---------------------------------
    # Already reviewed
    # ---------------------------------

    if leave_request["status"] != "Pending":

        conn.rollback()
        cur.close()
        conn.close()

        flash(
            "This leave request has already been reviewed.",
            "error"
        )

        return redirect(
            url_for(
                "student_leave.student_leave_requests_route"
            )
        )


    # ---------------------------------
    # REJECT
    # ---------------------------------

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
            session["user_id"],
            review_remarks or None,
            request_id,
            session["institution_id"]
        ))


        conn.commit()

        cur.close()
        conn.close()


        flash(
            "Leave request rejected.",
            "success"
        )


        return redirect(
            url_for(
                "student_leave.student_leave_requests_route"
            )
        )


    # ---------------------------------
    # APPROVE
    # ---------------------------------

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
        session["user_id"],
        review_remarks or None,
        request_id,
        session["institution_id"]
    ))


    # ---------------------------------
    # Attendance → Leave
    # ---------------------------------

    cur.execute("""
        SELECT
            id

        FROM attendance

        WHERE
            student_id = %s
            AND institution_id = %s
            AND attendance_date = %s

        FOR UPDATE
    """, (
        leave_request["student_id"],
        session["institution_id"],
        leave_request["leave_date"]
    ))

    attendance = cur.fetchone()


    if attendance:

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
            session["user_id"],
            attendance["id"],
            session["institution_id"]
        ))

    else:

        cur.execute("""
            INSERT INTO attendance
            (
                institution_id,
                student_id,
                attendance_date,
                status,
                marked_by
            )

            VALUES
            (
                %s,
                %s,
                %s,
                'Leave',
                %s
            )
        """, (
            session["institution_id"],
            leave_request["student_id"],
            leave_request["leave_date"],
            session["user_id"]
        ))


    conn.commit()

    cur.close()
    conn.close()


    flash(
        "Leave approved and attendance updated successfully.",
        "success"
    )


    return redirect(
        url_for(
            "student_leave.student_leave_requests_route"
        )
    )        