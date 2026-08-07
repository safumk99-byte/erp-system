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

def attendance_page():

    attendance_date = request.args.get(
        "date",
        str(date.today())
    )

    class_id = request.args.get(
        "class_id",
        ""
    )

    conn = get_connection()
    cur = conn.cursor()

    # Active Classes

    cur.execute("""

        SELECT
            id,
            class_name

        FROM classes

        WHERE

            institution_id=%s

            AND is_active=TRUE

        ORDER BY class_name

    """, (

        session["institution_id"],

    ))

    classes = cur.fetchall()

    students = []

    if class_id:

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

                ON s.class_id=c.id

            LEFT JOIN attendance a

                ON a.student_id=s.id

                AND a.attendance_date=%s

            WHERE

                s.institution_id=%s

                AND s.class_id=%s

                AND s.is_active=TRUE

            ORDER BY s.full_name

        """, (

            attendance_date,

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

        class_id=class_id

    )
    
def mark_attendance():

    attendance_date = request.form["attendance_date"]

    class_id = request.form["class_id"]

    student_ids = request.form.getlist(
        "student_id"
    )

    conn = get_connection()
    cur = conn.cursor()

    for student_id in student_ids:

        status = request.form.get(

            f"status_{student_id}",

            "Present"

        )

        cur.execute("""

            SELECT id

            FROM attendance

            WHERE

                student_id=%s

                AND attendance_date=%s

        """, (

            student_id,

            attendance_date

        ))

        row = cur.fetchone()

        if row:

            cur.execute("""

                UPDATE attendance

                SET

                    status=%s,

                    marked_by=%s,

                    updated_at=NOW()

                WHERE id=%s

            """, (

                status,

                session["user_id"],

                row["id"]

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

                    %s,

                    %s

                )

            """, (

                session["institution_id"],

                student_id,

                attendance_date,

                status,

                session["user_id"]

            ))

    conn.commit()

    cur.close()
    conn.close()

    flash(

        "Attendance saved successfully.",

        "success"

    )

    return redirect(

        url_for(

            "attendance.attendance_list",

            date=attendance_date,

            class_id=class_id

        )

    )
    
def get_student_popup(student_id):

    conn = get_connection()
    cur = conn.cursor()

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

            ON s.class_id=c.id

        WHERE

            s.id=%s

            AND s.institution_id=%s

    """, (

        student_id,

        session["institution_id"]

    ))

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