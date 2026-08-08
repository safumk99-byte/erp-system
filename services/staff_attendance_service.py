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


ATTENDANCE_STATUSES = {
    "Present",
    "Absent",
    "Leave"
}


def get_staff(cur, attendance_date=None, period=None):
    """
    Get staff from the same users + roles structure
    used by Staff Management.
    """

    if attendance_date and period:

        cur.execute("""
            SELECT
                u.id,
                u.full_name,
                u.username,
                u.phone,
                r.name AS role,

                COALESCE(
                    sa.status,
                    'Present'
                ) AS status,

                sa.id AS attendance_id,
                sa.leave_reason,
                sa.leave_status,
                sa.remarks

            FROM users u

            JOIN roles r
                ON u.role_id = r.id

            LEFT JOIN staff_attendance sa
                ON sa.staff_id = u.id
                AND sa.attendance_date = %s
                AND sa.period = %s
                AND sa.institution_id = %s

            WHERE
                u.institution_id = %s
                AND r.name IN ('principal', 'staff')

            ORDER BY u.full_name
        """, (
            attendance_date,
            period,
            session["institution_id"],
            session["institution_id"]
        ))

    else:

        cur.execute("""
            SELECT
                u.id,
                u.full_name,
                u.username,
                u.phone,
                r.name AS role

            FROM users u

            JOIN roles r
                ON u.role_id = r.id

            WHERE
                u.institution_id = %s
                AND r.name IN ('principal', 'staff')

            ORDER BY u.full_name
        """, (
            session["institution_id"],
        ))

    return cur.fetchall()


def list_staff_attendance():

    attendance_date = request.args.get(
        "date",
        str(date.today())
    )

    conn = get_connection()
    cur = conn.cursor()

    # ---------------------------------
    # Get periods saved for this date
    # ---------------------------------

    cur.execute("""
        SELECT DISTINCT
            period

        FROM staff_attendance

        WHERE
            institution_id = %s
            AND attendance_date = %s

        ORDER BY period
    """, (
        session["institution_id"],
        attendance_date
    ))

    period_rows = cur.fetchall()

    periods = [
        row["period"]
        for row in period_rows
    ]


    # ---------------------------------
    # Get all staff
    # ---------------------------------

    cur.execute("""
        SELECT
            u.id,
            u.full_name,
            u.username,
            u.phone,
            r.name AS role

        FROM users u

        JOIN roles r
            ON u.role_id = r.id

        WHERE
            u.institution_id = %s
            AND r.name IN ('principal', 'staff')

        ORDER BY u.full_name
    """, (
        session["institution_id"],
    ))

    staff = cur.fetchall()


    # ---------------------------------
    # Get saved attendance
    # ---------------------------------

    attendance_map = {}

    cur.execute("""
        SELECT
            sa.staff_id,
            sa.period,
            sa.status,
            sa.leave_reason,
            sa.leave_status,
            sa.remarks

        FROM staff_attendance sa

        WHERE
            sa.institution_id = %s
            AND sa.attendance_date = %s

        ORDER BY
            sa.staff_id,
            sa.period
    """, (
        session["institution_id"],
        attendance_date
    ))

    attendance_rows = cur.fetchall()


    for row in attendance_rows:

        staff_id = row["staff_id"]
        period = row["period"]

        attendance_map[
            (staff_id, period)
        ] = row


    cur.close()
    conn.close()


    return render_template(
        "staff_attendance/list.html",

        staff=staff,

        periods=periods,

        attendance_map=attendance_map,

        attendance_date=attendance_date
    )
    
def mark_staff_attendance_page():

    attendance_date = request.args.get(
        "date",
        str(date.today())
    )

    period = request.args.get(
        "period",
        "1"
    )

    try:
        period = int(period)

        if period < 1:
            period = 1

    except (TypeError, ValueError):
        period = 1

    conn = get_connection()
    cur = conn.cursor()

    staff = get_staff(
        cur,
        attendance_date,
        period
    )

    cur.close()
    conn.close()

    return render_template(
        "staff_attendance/mark.html",
        staff=staff,
        attendance_date=attendance_date,
        period=period
    )    


def mark_staff_attendance():

    attendance_date = request.form.get(
        "attendance_date"
    )

    period = request.form.get(
        "period"
    )

    staff_ids = request.form.getlist(
        "staff_id"
    )

    if not attendance_date:

        flash(
            "Attendance date is required.",
            "error"
        )

        return redirect(
            url_for(
                "staff_attendance.staff_attendance_list"
            )
        )

    try:

        period = int(period)

        if period < 1:
            raise ValueError

    except (
        TypeError,
        ValueError
    ):

        flash(
            "Invalid period.",
            "error"
        )

        return redirect(
            url_for(
                "staff_attendance.staff_attendance_list",
                date=attendance_date
            )
        )

    conn = get_connection()
    cur = conn.cursor()

    for staff_id in staff_ids:

        status = request.form.get(
            f"status_{staff_id}",
            "Present"
        )

        leave_reason = request.form.get(
            f"leave_reason_{staff_id}",
            ""
        ).strip()

        remarks = request.form.get(
            f"remarks_{staff_id}",
            ""
        ).strip()

        if status not in ATTENDANCE_STATUSES:

            status = "Present"

        # Verify staff belongs to current institution

        cur.execute("""
            SELECT
                u.id

            FROM users u

            JOIN roles r
                ON u.role_id = r.id

            WHERE
                u.id = %s
                AND u.institution_id = %s
                AND r.name IN ('principal', 'staff')
        """, (
            staff_id,
            session["institution_id"]
        ))

        valid_staff = cur.fetchone()

        if not valid_staff:
            continue

        # Leave handling

        if status == "Leave":

            if leave_reason:

                leave_status = "Pending"

            else:

                leave_status = "Pending"

        else:

            leave_reason = None
            leave_status = "Not Required"

        # Insert or update the same
        # staff + date + period record.

        cur.execute("""
            INSERT INTO staff_attendance
            (
                institution_id,
                staff_id,
                attendance_date,
                period,
                status,
                leave_reason,
                leave_status,
                remarks
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
                %s
            )

            ON CONFLICT
            (
                staff_id,
                attendance_date,
                period
            )

            DO UPDATE SET

                status = EXCLUDED.status,

                leave_reason = EXCLUDED.leave_reason,

                leave_status = EXCLUDED.leave_status,

                remarks = EXCLUDED.remarks,

                updated_at = NOW()
        """, (
            session["institution_id"],
            staff_id,
            attendance_date,
            period,
            status,
            leave_reason,
            leave_status,
            remarks or None
        ))

    conn.commit()

    cur.close()
    conn.close()

    flash(
        "Staff attendance saved successfully.",
        "success"
    )

    return redirect(
        url_for(
            "staff_attendance.staff_attendance_list",
            date=attendance_date,
            period=period
        )
    )


def approve_staff_leave(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE staff_attendance

        SET
            leave_status = 'Approved',
            status = 'Leave',
            updated_at = NOW()

        WHERE
            id = %s
            AND institution_id = %s
            AND status = 'Leave'
            AND leave_status = 'Pending'
    """, (
        id,
        session["institution_id"]
    ))

    conn.commit()

    cur.close()
    conn.close()

    flash(
        "Staff leave approved.",
        "success"
    )

    return redirect(
        request.referrer
        or url_for(
            "staff_attendance.staff_attendance_list"
        )
    )


def reject_staff_leave(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE staff_attendance

        SET
            leave_status = 'Rejected',
            status = 'Absent',
            updated_at = NOW()

        WHERE
            id = %s
            AND institution_id = %s
            AND status = 'Leave'
            AND leave_status = 'Pending'
    """, (
        id,
        session["institution_id"]
    ))

    conn.commit()

    cur.close()
    conn.close()

    flash(
        "Staff leave rejected.",
        "success"
    )

    return redirect(
        request.referrer
        or url_for(
            "staff_attendance.staff_attendance_list"
        )
    )


def monthly_staff_attendance():

    year = request.args.get(
        "year"
    )

    month = request.args.get(
        "month"
    )

    today = date.today()

    try:

        year = int(
            year
            or today.year
        )

        month = int(
            month
            or today.month
        )

        if month < 1 or month > 12:
            raise ValueError

    except (
        TypeError,
        ValueError
    ):

        year = today.year
        month = today.month

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            u.id,
            u.full_name,
            u.username,
            r.name AS role,

            COUNT(sa.id)
                FILTER (
                    WHERE sa.status = 'Present'
                ) AS present_count,

            COUNT(sa.id)
                FILTER (
                    WHERE sa.status = 'Absent'
                ) AS absent_count,

            COUNT(sa.id)
                FILTER (
                    WHERE
                        sa.status = 'Leave'
                        AND sa.leave_status = 'Approved'
                ) AS approved_leave_count,

            COUNT(sa.id)
                FILTER (
                    WHERE
                        sa.status = 'Leave'
                        AND sa.leave_status = 'Pending'
                ) AS pending_leave_count

        FROM users u

        JOIN roles r
            ON u.role_id = r.id

        LEFT JOIN staff_attendance sa
            ON sa.staff_id = u.id

            AND sa.institution_id = %s

            AND EXTRACT(
                YEAR FROM sa.attendance_date
            ) = %s

            AND EXTRACT(
                MONTH FROM sa.attendance_date
            ) = %s

        WHERE
            u.institution_id = %s

            AND r.name IN (
                'principal',
                'staff'
            )

        GROUP BY
            u.id,
            u.full_name,
            u.username,
            r.name

        ORDER BY
            u.full_name
    """, (
        session["institution_id"],
        year,
        month,
        session["institution_id"]
    ))

    monthly_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "staff_attendance/monthly.html",
        monthly_data=monthly_data,
        year=year,
        month=month
    )
    
def staff_leave_requests():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            sa.id,
            sa.staff_id,
            sa.attendance_date,
            sa.period,
            sa.status,
            sa.leave_reason,
            sa.leave_status,
            sa.remarks,

            u.full_name,
            u.username,
            u.phone,

            r.name AS role

        FROM staff_attendance sa

        JOIN users u
            ON sa.staff_id = u.id

        JOIN roles r
            ON u.role_id = r.id

        WHERE
            sa.institution_id = %s
            AND sa.status = 'Leave'

        ORDER BY
            CASE
                WHEN sa.leave_status = 'Pending'
                THEN 1
                ELSE 2
            END,
            sa.attendance_date DESC,
            sa.period DESC,
            u.full_name
    """, (
        session["institution_id"],
    ))

    leave_requests = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "staff_attendance/leave_requests.html",
        leave_requests=leave_requests
    )    