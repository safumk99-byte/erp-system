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

def list_exams():

    search = request.args.get(
        "search",
        ""
    ).strip()

    conn = get_connection()
    cur = conn.cursor()

    if search:

        cur.execute("""
            SELECT
                e.*,
                c.class_name
            FROM exams e

            JOIN classes c
                ON e.class_id = c.id

            WHERE
                e.institution_id = %s
                AND e.exam_name ILIKE %s

            ORDER BY e.id DESC

        """, (
            session["institution_id"],
            f"%{search}%"
        ))

    else:

        cur.execute("""
            SELECT
                e.*,
                c.class_name
            FROM exams e

            JOIN classes c
                ON e.class_id = c.id

            WHERE
                e.institution_id = %s

            ORDER BY e.id DESC

        """, (
            session["institution_id"],
        ))

    exams = cur.fetchall()

    # Add subjects to every exam
    exam_list = []

    for exam in exams:

        cur.execute("""
            SELECT
                s.id,
                s.subject_name
            FROM exam_subjects es

            JOIN subjects s
                ON es.subject_id = s.id

            WHERE
                es.exam_id = %s

            ORDER BY s.subject_name

        """, (
            exam["id"],
        ))

        subjects = cur.fetchall()

        exam_data = dict(exam)

        exam_data["subjects"] = ", ".join(
            subject["subject_name"]
            for subject in subjects
        )

        exam_data["subject_ids"] = [
            {
                "id": subject["id"],
                "name": subject["subject_name"]
            }
            for subject in subjects
        ]

        exam_list.append(exam_data)

    cur.close()
    conn.close()

    return render_template(
        "exams/list.html",
        exams=exam_list,
        search=search
    )
    
def add_exam():

    conn = get_connection()
    cur = conn.cursor()

    # Classes

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

    # Subjects

    cur.execute("""

        SELECT

            id,
            subject_name

        FROM subjects

        WHERE

            institution_id=%s

            AND is_active=TRUE

        ORDER BY subject_name

    """, (

        session["institution_id"],

    ))

    subjects = cur.fetchall()

    if request.method == "POST":

        exam_name = request.form["exam_name"].strip()

        exam_type = request.form["exam_type"]

        class_id = request.form["class_id"]

        total_mark = request.form["total_mark"]

        exam_date = request.form["exam_date"]

        selected_subjects = request.form.getlist(
            "subjects"
        )

        if not selected_subjects:

            flash(
                "Select at least one subject.",
                "error"
            )

            return render_template(
                "exams/add.html",
                classes=classes,
                subjects=subjects
            )

        cur.execute("""

            INSERT INTO exams
            (

                institution_id,

                class_id,

                subject_id,

                exam_name,

                exam_type,

                exam_date,

                total_mark

            )

            VALUES
            (

                %s,

                %s,

                NULL,

                %s,

                %s,

                %s,

                %s

            )

            RETURNING id

        """, (

            session["institution_id"],

            class_id,

            exam_name,

            exam_type,

            exam_date,

            total_mark

        ))

        exam = cur.fetchone()

        exam_id = exam["id"]

        for subject_id in selected_subjects:

            cur.execute("""

                INSERT INTO exam_subjects
                (

                    exam_id,

                    subject_id

                )

                VALUES
                (

                    %s,

                    %s

                )

            """, (

                exam_id,

                subject_id

            ))

        conn.commit()

        cur.close()
        conn.close()

        flash(

            "Exam created successfully.",

            "success"

        )

        return redirect(

            url_for(
                "exams.exam_list"
            )

        )

    cur.close()
    conn.close()

    return render_template(

        "exams/add.html",

        classes=classes,

        subjects=subjects

    )
    
def edit_exam(id):

    conn = get_connection()
    cur = conn.cursor()

    # Classes
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

    # Subjects
    cur.execute("""
        SELECT
            id,
            subject_name
        FROM subjects
        WHERE
            institution_id=%s
            AND is_active=TRUE
        ORDER BY subject_name
    """, (
        session["institution_id"],
    ))

    subjects = cur.fetchall()

    if request.method == "POST":

        exam_name = request.form["exam_name"].strip()
        exam_type = request.form["exam_type"]
        class_id = request.form["class_id"]
        total_mark = request.form["total_mark"]
        exam_date = request.form["exam_date"]
        selected_subjects = request.form.getlist("subjects")

        cur.execute("""
            UPDATE exams
            SET
                class_id=%s,
                exam_name=%s,
                exam_type=%s,
                exam_date=%s,
                total_mark=%s,
                updated_at=NOW()
            WHERE
                id=%s
                AND institution_id=%s
        """, (
            class_id,
            exam_name,
            exam_type,
            exam_date,
            total_mark,
            id,
            session["institution_id"]
        ))

        # പഴയ subject links delete ചെയ്യുക
        cur.execute("""
            DELETE FROM exam_subjects
            WHERE exam_id=%s
        """, (
            id,
        ))

        # പുതിയ subject links save ചെയ്യുക
        for subject_id in selected_subjects:

            cur.execute("""
                INSERT INTO exam_subjects
                (
                    exam_id,
                    subject_id
                )
                VALUES
                (%s,%s)
            """, (
                id,
                subject_id
            ))

        conn.commit()

        flash(
            "Exam updated successfully.",
            "success"
        )

        cur.close()
        conn.close()

        return redirect(
            url_for("exams.exam_list")
        )

    # Exam Details
    cur.execute("""
        SELECT *
        FROM exams
        WHERE
            id=%s
            AND institution_id=%s
    """, (
        id,
        session["institution_id"]
    ))

    exam = cur.fetchone()

    # Selected Subjects
    cur.execute("""
        SELECT subject_id
        FROM exam_subjects
        WHERE exam_id=%s
    """, (
        id,
    ))

    selected_subjects = [
        row["subject_id"]
        for row in cur.fetchall()
    ]

    cur.close()
    conn.close()

    return render_template(
        "exams/edit.html",
        exam=exam,
        classes=classes,
        subjects=subjects,
        selected_subjects=selected_subjects
    )
    
def toggle_exam(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            is_active
        FROM exams
        WHERE
            id=%s
            AND institution_id=%s
    """, (
        id,
        session["institution_id"]
    ))

    exam = cur.fetchone()

    if not exam:

        cur.close()
        conn.close()

        flash(
            "Exam not found.",
            "error"
        )

        return redirect(
            url_for("exams.exam_list")
        )

    new_status = not exam["is_active"]

    cur.execute("""
        UPDATE exams
        SET
            is_active=%s,
            updated_at=NOW()
        WHERE
            id=%s
            AND institution_id=%s
    """, (
        new_status,
        id,
        session["institution_id"]
    ))

    conn.commit()

    cur.close()
    conn.close()

    flash(
        "Exam status updated successfully.",
        "success"
    )

    return redirect(
        url_for("exams.exam_list")
    )
    
def enter_marks(id, subject_id):

    conn = get_connection()
    cur = conn.cursor()

    # Exam + Subject details
    cur.execute("""
        SELECT
            e.id,
            e.exam_name,
            e.exam_type,
            e.exam_date,
            e.total_mark,
            e.class_id,

            c.class_name,

            s.id AS subject_id,
            s.subject_name

        FROM exams e

        JOIN classes c
            ON e.class_id = c.id

        JOIN exam_subjects es
            ON e.id = es.exam_id

        JOIN subjects s
            ON es.subject_id = s.id

        WHERE
            e.id = %s
            AND es.subject_id = %s
            AND e.institution_id = %s

        LIMIT 1
    """, (
        id,
        subject_id,
        session["institution_id"]
    ))

    exam = cur.fetchone()

    if not exam:

        cur.close()
        conn.close()

        flash(
            "Exam or subject not found.",
            "error"
        )

        return redirect(
            url_for("exams.exam_list")
        )

    # Students + Existing Marks
    cur.execute("""
        SELECT

            st.id,
            st.admission_no,
            st.full_name,

            em.mark,
            em.grade

        FROM students st

        LEFT JOIN exam_marks em
            ON st.id = em.student_id

            AND em.exam_id = %s

            AND em.subject_id = %s

        WHERE

            st.institution_id = %s

            AND st.class_id = %s

            AND st.is_active = TRUE

        ORDER BY st.full_name

    """, (
        id,
        subject_id,
        session["institution_id"],
        exam["class_id"]
    ))

    students = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "exams/marks.html",
        exam=exam,
        students=students
    )
    
def save_marks(id, subject_id):

    conn = get_connection()
    cur = conn.cursor()

    # Verify exam + subject
    cur.execute("""
        SELECT
            e.total_mark

        FROM exams e

        JOIN exam_subjects es
            ON e.id = es.exam_id

        WHERE
            e.id = %s
            AND es.subject_id = %s
            AND e.institution_id = %s

        LIMIT 1
    """, (
        id,
        subject_id,
        session["institution_id"]
    ))

    exam = cur.fetchone()

    if not exam:

        cur.close()
        conn.close()

        flash(
            "Exam or subject not found.",
            "error"
        )

        return redirect(
            url_for("exams.exam_list")
        )

    total_mark = float(exam["total_mark"])

    student_ids = request.form.getlist(
        "student_id"
    )

    for student_id in student_ids:

        mark_value = request.form.get(
            f"mark_{student_id}",
            ""
        ).strip()

        if mark_value == "":
            continue

        try:
            mark = float(mark_value)

        except ValueError:

            flash(
                "Invalid mark entered.",
                "error"
            )

            cur.close()
            conn.close()

            return redirect(
                url_for(
                    "exams.exam_marks",
                    id=id,
                    subject_id=subject_id
                )
            )

        if mark < 0 or mark > total_mark:

            flash(
                f"Mark must be between 0 and {total_mark}.",
                "error"
            )

            cur.close()
            conn.close()

            return redirect(
                url_for(
                    "exams.exam_marks",
                    id=id,
                    subject_id=subject_id
                )
            )

        percentage = (
            mark / total_mark
        ) * 100

        if percentage >= 90:
            grade = "A+"

        elif percentage >= 80:
            grade = "A"

        elif percentage >= 70:
            grade = "B+"

        elif percentage >= 60:
            grade = "B"

        elif percentage >= 50:
            grade = "C"

        else:
            grade = "D"

        # Check existing mark
        cur.execute("""
            SELECT id
            FROM exam_marks

            WHERE
                exam_id = %s
                AND subject_id = %s
                AND student_id = %s
        """, (
            id,
            subject_id,
            student_id
        ))

        existing = cur.fetchone()

        if existing:

            cur.execute("""
                UPDATE exam_marks

                SET
                    mark = %s,
                    grade = %s,
                    entered_by = %s,
                    updated_at = NOW()

                WHERE id = %s
            """, (
                mark,
                grade,
                session.get("user_id"),
                existing["id"]
            ))

        else:

            cur.execute("""
                INSERT INTO exam_marks
                (
                    exam_id,
                    subject_id,
                    student_id,
                    mark,
                    grade,
                    entered_by
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
                id,
                subject_id,
                student_id,
                mark,
                grade,
                session.get("user_id")
            ))

    conn.commit()

    cur.close()
    conn.close()

    flash(
        "Marks saved successfully.",
        "success"
    )

    return redirect(
        url_for(
            "exams.exam_marks",
            id=id,
            subject_id=subject_id
        )
    ) 
    
def get_class_subjects(class_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""

        SELECT

            id,
            subject_name

        FROM subjects

        WHERE

            institution_id=%s

            AND class_id=%s

            AND is_active=TRUE

        ORDER BY subject_name

    """, (

        session["institution_id"],

        class_id

    ))

    subjects = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(subjects)                   
    
        