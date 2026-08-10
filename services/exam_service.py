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
# Helper Functions
# =========================================================

def _class_is_allowed(cur, class_id):

    role = session.get("role")

    if role == "institution_admin":

        cur.execute("""
            SELECT id
            FROM classes
            WHERE
                id = %s
                AND institution_id = %s
                AND is_active = TRUE
        """, (
            class_id,
            session["institution_id"]
        ))

        return cur.fetchone() is not None


    if role == "staff":

        cur.execute("""
            SELECT 1
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

            LIMIT 1
        """, (
            class_id,
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

        return cur.fetchone() is not None


    return False


def _subject_is_allowed(
    cur,
    subject_id,
    class_id
):

    role = session.get("role")

    if role == "institution_admin":

        cur.execute("""
            SELECT id
            FROM subjects

            WHERE
                id = %s
                AND class_id = %s
                AND institution_id = %s
                AND is_active = TRUE
        """, (
            subject_id,
            class_id,
            session["institution_id"]
        ))

        return cur.fetchone() is not None


    if role == "staff":

        cur.execute("""
            SELECT 1

            FROM subjects s

            JOIN staff_subjects ss
                ON ss.subject_id = s.id

            WHERE
                s.id = %s
                AND s.class_id = %s
                AND s.institution_id = %s

                AND ss.institution_id = %s
                AND ss.staff_id = %s
                AND ss.is_active = TRUE

                AND s.is_active = TRUE

            LIMIT 1
        """, (
            subject_id,
            class_id,
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

        return cur.fetchone() is not None


    return False


# =========================================================
# 1. List Exams
# =========================================================

def list_exams():

    search = request.args.get(
        "search",
        ""
    ).strip()

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    if role == "institution_admin":

        query = """
            SELECT
                e.*,
                c.class_name

            FROM exams e

            JOIN classes c
                ON e.class_id = c.id

            WHERE
                e.institution_id = %s
        """

        params = [
            session["institution_id"]
        ]


    elif role == "staff":

        query = """
            SELECT DISTINCT
                e.*,
                c.class_name

            FROM exams e

            JOIN classes c
                ON e.class_id = c.id

            JOIN staff_classes sc
                ON sc.class_id = e.class_id

            JOIN exam_subjects es
                ON es.exam_id = e.id

            JOIN staff_subjects ss
                ON ss.subject_id = es.subject_id

            WHERE
                e.institution_id = %s

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

                AND ss.institution_id = %s
                AND ss.staff_id = %s
                AND ss.is_active = TRUE
        """

        params = [
            session["institution_id"],
            session["institution_id"],
            session["user_id"],
            session["institution_id"],
            session["user_id"]
        ]


    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    if search:

        query += """
            AND e.exam_name ILIKE %s
        """

        params.append(
            f"%{search}%"
        )


    query += """
        ORDER BY e.id DESC
    """


    cur.execute(
        query,
        tuple(params)
    )

    exams = cur.fetchall()


    # -----------------------------------------------------
    # Subjects for each exam
    # -----------------------------------------------------

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


        exam_data = dict(
            exam
        )


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


        exam_list.append(
            exam_data
        )


    cur.close()
    conn.close()


    return render_template(
        "exams/list.html",

        exams=exam_list,

        search=search
    )


# =========================================================
# 2. Add Exam
# =========================================================

def add_exam():

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    # -----------------------------------------------------
    # Classes
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


    elif role == "staff":

        cur.execute("""
            SELECT
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


    # -----------------------------------------------------
    # Subjects
    # -----------------------------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT
                id,
                subject_name

            FROM subjects

            WHERE
                institution_id = %s
                AND is_active = TRUE

            ORDER BY subject_name
        """, (
            session["institution_id"],
        ))


    else:

        cur.execute("""
            SELECT DISTINCT
                s.id,
                s.subject_name

            FROM subjects s

            JOIN staff_subjects ss
                ON ss.subject_id = s.id

            WHERE
                s.institution_id = %s

                AND ss.institution_id = %s
                AND ss.staff_id = %s
                AND ss.is_active = TRUE

                AND s.is_active = TRUE

            ORDER BY s.subject_name
        """, (
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))


    subjects = cur.fetchall()


    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    if request.method == "GET":

        cur.close()
        conn.close()

        return render_template(
            "exams/add.html",
            classes=classes,
            subjects=subjects
        )


    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    exam_name = request.form[
        "exam_name"
    ].strip()

    exam_type = request.form[
        "exam_type"
    ]

    class_id = request.form[
        "class_id"
    ]

    total_mark = request.form[
        "total_mark"
    ]

    exam_date = request.form[
        "exam_date"
    ]

    selected_subjects = request.form.getlist(
        "subjects"
    )


    # -----------------------------------------------------
    # Class Access
    # -----------------------------------------------------

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
                "exams.create_exam"
            )
        )


    # -----------------------------------------------------
    # Subject Required
    # -----------------------------------------------------

    if not selected_subjects:

        cur.close()
        conn.close()

        flash(
            "Select at least one subject.",
            "error"
        )

        return redirect(
            url_for(
                "exams.create_exam"
            )
        )


    # -----------------------------------------------------
    # Verify Subjects
    # -----------------------------------------------------

    for subject_id in selected_subjects:

        if not _subject_is_allowed(
            cur,
            subject_id,
            class_id
        ):

            cur.close()
            conn.close()

            flash(
                "You do not have access to one or more selected subjects.",
                "error"
            )

            return redirect(
                url_for(
                    "exams.create_exam"
                )
            )


    # -----------------------------------------------------
    # Create Exam
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # Save Exam Subjects
    # -----------------------------------------------------

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
    
# =========================================================
# 3. Edit Exam
# =========================================================

def edit_exam(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    # -----------------------------------------------------
    # Get Exam
    # -----------------------------------------------------

    cur.execute("""
        SELECT *
        FROM exams

        WHERE
            id = %s
            AND institution_id = %s
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
            url_for(
                "exams.exam_list"
            )
        )


    # -----------------------------------------------------
    # Staff Access
    # -----------------------------------------------------

    if role == "staff":

        cur.execute("""
            SELECT 1

            FROM exams e

            JOIN staff_classes sc
                ON sc.class_id = e.class_id

            JOIN exam_subjects es
                ON es.exam_id = e.id

            JOIN staff_subjects ss
                ON ss.subject_id = es.subject_id

            WHERE
                e.id = %s

                AND e.institution_id = %s

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

                AND ss.institution_id = %s
                AND ss.staff_id = %s
                AND ss.is_active = TRUE

            LIMIT 1
        """, (
            id,

            session["institution_id"],

            session["institution_id"],
            session["user_id"],

            session["institution_id"],
            session["user_id"]
        ))

        if not cur.fetchone():

            cur.close()
            conn.close()

            flash(
                "You do not have access to this exam.",
                "error"
            )

            return redirect(
                url_for(
                    "exams.exam_list"
                )
            )


    # -----------------------------------------------------
    # Classes
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

    else:

        cur.execute("""
            SELECT
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

    classes = cur.fetchall()


    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        exam_name = request.form[
            "exam_name"
        ].strip()

        exam_type = request.form[
            "exam_type"
        ]

        class_id = request.form[
            "class_id"
        ]

        total_mark = request.form[
            "total_mark"
        ]

        exam_date = request.form[
            "exam_date"
        ]

        selected_subjects = request.form.getlist(
            "subjects"
        )


        # -------------------------------------------------
        # Verify Class
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
                    "exams.update_exam",
                    id=id
                )
            )


        # -------------------------------------------------
        # Subject Required
        # -------------------------------------------------

        if not selected_subjects:

            cur.close()
            conn.close()

            flash(
                "Select at least one subject.",
                "error"
            )

            return redirect(
                url_for(
                    "exams.update_exam",
                    id=id
                )
            )


        # -------------------------------------------------
        # Verify Subjects
        # -------------------------------------------------

        for subject_id in selected_subjects:

            if not _subject_is_allowed(
                cur,
                subject_id,
                class_id
            ):

                cur.close()
                conn.close()

                flash(
                    "You do not have access to one or more selected subjects.",
                    "error"
                )

                return redirect(
                    url_for(
                        "exams.update_exam",
                        id=id
                    )
                )


        # -------------------------------------------------
        # Update Exam
        # -------------------------------------------------

        cur.execute("""
            UPDATE exams

            SET
                class_id = %s,
                exam_name = %s,
                exam_type = %s,
                exam_date = %s,
                total_mark = %s,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
        """, (
            class_id,
            exam_name,
            exam_type,
            exam_date,
            total_mark,
            id,
            session["institution_id"]
        ))


        # -------------------------------------------------
        # Delete Old Subjects
        # -------------------------------------------------

        cur.execute("""
            DELETE FROM exam_subjects

            WHERE
                exam_id = %s
        """, (
            id,
        ))


        # -------------------------------------------------
        # Save New Subjects
        # -------------------------------------------------

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
                id,
                subject_id
            ))


        conn.commit()

        cur.close()
        conn.close()


        flash(
            "Exam updated successfully.",
            "success"
        )


        return redirect(
            url_for(
                "exams.exam_list"
            )
        )


    # -----------------------------------------------------
    # Selected Subjects
    # -----------------------------------------------------

    cur.execute("""
        SELECT
            subject_id

        FROM exam_subjects

        WHERE
            exam_id = %s
    """, (
        id,
    ))


    selected_subjects = [
        row["subject_id"]
        for row in cur.fetchall()
    ]


    # -----------------------------------------------------
    # Subjects
    # -----------------------------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT
                id,
                subject_name

            FROM subjects

            WHERE
                institution_id = %s
                AND is_active = TRUE

            ORDER BY subject_name
        """, (
            session["institution_id"],
        ))

    else:

        cur.execute("""
            SELECT DISTINCT
                s.id,
                s.subject_name

            FROM subjects s

            JOIN staff_subjects ss
                ON ss.subject_id = s.id

            WHERE
                s.institution_id = %s

                AND ss.institution_id = %s
                AND ss.staff_id = %s
                AND ss.is_active = TRUE

                AND s.is_active = TRUE

            ORDER BY s.subject_name
        """, (
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

    subjects = cur.fetchall()


    cur.close()
    conn.close()


    return render_template(
        "exams/edit.html",

        exam=exam,

        classes=classes,

        subjects=subjects,

        selected_subjects=selected_subjects
    )


# =========================================================
# 4. Toggle Exam Status
# =========================================================

def toggle_exam(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    # -----------------------------------------------------
    # Institution Admin
    # -----------------------------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT
                is_active

            FROM exams

            WHERE
                id = %s
                AND institution_id = %s
        """, (
            id,
            session["institution_id"]
        ))


    # -----------------------------------------------------
    # Staff
    # -----------------------------------------------------

    elif role == "staff":

        cur.execute("""
            SELECT DISTINCT
                e.is_active

            FROM exams e

            JOIN staff_classes sc
                ON sc.class_id = e.class_id

            JOIN exam_subjects es
                ON es.exam_id = e.id

            JOIN staff_subjects ss
                ON ss.subject_id = es.subject_id

            WHERE
                e.id = %s

                AND e.institution_id = %s

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

                AND ss.institution_id = %s
                AND ss.staff_id = %s
                AND ss.is_active = TRUE

            LIMIT 1
        """, (
            id,
            session["institution_id"],

            session["institution_id"],
            session["user_id"],

            session["institution_id"],
            session["user_id"]
        ))


    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    exam = cur.fetchone()


    if not exam:

        cur.close()
        conn.close()

        flash(
            "Exam not found or access denied.",
            "error"
        )

        return redirect(
            url_for(
                "exams.exam_list"
            )
        )


    new_status = not exam[
        "is_active"
    ]


    cur.execute("""
        UPDATE exams

        SET
            is_active = %s,
            updated_at = NOW()

        WHERE
            id = %s
            AND institution_id = %s
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
        url_for(
            "exams.exam_list"
        )
    )
    
# =========================================================
# 5. Enter Marks
# =========================================================

def enter_marks(id, subject_id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    # -----------------------------------------------------
    # Exam + Subject
    # -----------------------------------------------------

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
            url_for(
                "exams.exam_list"
            )
        )


    # -----------------------------------------------------
    # Staff Class Access
    # -----------------------------------------------------

    if role == "staff":

        if not _class_is_allowed(
            cur,
            exam["class_id"]
        ):

            cur.close()
            conn.close()

            flash(
                "You do not have access to this class.",
                "error"
            )

            return redirect(
                url_for(
                    "exams.exam_list"
                )
            )


        # -------------------------------------------------
        # Staff Subject Access
        # -------------------------------------------------

        if not _subject_is_allowed(
            cur,
            subject_id,
            exam["class_id"]
        ):

            cur.close()
            conn.close()

            flash(
                "You do not have access to this subject.",
                "error"
            )

            return redirect(
                url_for(
                    "exams.exam_list"
                )
            )


    # -----------------------------------------------------
    # Students + Existing Marks
    # -----------------------------------------------------

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


# =========================================================
# 6. Save Marks
# =========================================================

def save_marks(id, subject_id):

    conn = get_connection()
    cur = conn.cursor()


    # -----------------------------------------------------
    # Verify Exam + Subject
    # -----------------------------------------------------

    cur.execute("""
        SELECT
            e.total_mark,
            e.class_id

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
            url_for(
                "exams.exam_list"
            )
        )


    # -----------------------------------------------------
    # Staff Access
    # -----------------------------------------------------

    if session.get("role") == "staff":

        if not _class_is_allowed(
            cur,
            exam["class_id"]
        ):

            cur.close()
            conn.close()

            flash(
                "You do not have access to this class.",
                "error"
            )

            return redirect(
                url_for(
                    "exams.exam_list"
                )
            )


        if not _subject_is_allowed(
            cur,
            subject_id,
            exam["class_id"]
        ):

            cur.close()
            conn.close()

            flash(
                "You do not have access to this subject.",
                "error"
            )

            return redirect(
                url_for(
                    "exams.exam_list"
                )
            )


    total_mark = float(
        exam["total_mark"]
    )


    student_ids = request.form.getlist(
        "student_id"
    )


    # -----------------------------------------------------
    # Save Each Student Mark
    # -----------------------------------------------------

    for student_id in student_ids:


        # -------------------------------------------------
        # Verify Student
        # -------------------------------------------------

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
            exam["class_id"]
        ))

        valid_student = cur.fetchone()


        if not valid_student:

            cur.close()
            conn.close()

            flash(
                "Invalid student access.",
                "error"
            )

            return redirect(
                url_for(
                    "exams.exam_marks",
                    id=id,
                    subject_id=subject_id
                )
            )


        # -------------------------------------------------
        # Get Mark
        # -------------------------------------------------

        mark_value = request.form.get(
            f"mark_{student_id}",
            ""
        ).strip()


        if mark_value == "":
            continue


        try:

            mark = float(
                mark_value
            )

        except ValueError:

            cur.close()
            conn.close()

            flash(
                "Invalid mark entered.",
                "error"
            )

            return redirect(
                url_for(
                    "exams.exam_marks",
                    id=id,
                    subject_id=subject_id
                )
            )


        # -------------------------------------------------
        # Validate Mark
        # -------------------------------------------------

        if mark < 0 or mark > total_mark:

            cur.close()
            conn.close()

            flash(
                f"Mark must be between 0 and {total_mark}.",
                "error"
            )

            return redirect(
                url_for(
                    "exams.exam_marks",
                    id=id,
                    subject_id=subject_id
                )
            )


        # -------------------------------------------------
        # Calculate Percentage
        # -------------------------------------------------

        percentage = (
            mark / total_mark
        ) * 100


        # -------------------------------------------------
        # Grade
        # -------------------------------------------------

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


        # -------------------------------------------------
        # Check Existing Mark
        # -------------------------------------------------

        cur.execute("""
            SELECT
                id

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


        # -------------------------------------------------
        # Update Existing
        # -------------------------------------------------

        if existing:

            cur.execute("""
                UPDATE exam_marks

                SET
                    mark = %s,
                    grade = %s,
                    entered_by = %s,
                    updated_at = NOW()

                WHERE
                    id = %s
            """, (
                mark,
                grade,
                session.get("user_id"),
                existing["id"]
            ))


        # -------------------------------------------------
        # Insert New
        # -------------------------------------------------

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
    
# =========================================================
# 7. Get Class Subjects
# =========================================================

def get_class_subjects(class_id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    # -----------------------------------------------------
    # Verify Class Access
    # -----------------------------------------------------

    if not _class_is_allowed(
        cur,
        class_id
    ):

        cur.close()
        conn.close()

        return jsonify([])


    # -----------------------------------------------------
    # Institution Admin
    # -----------------------------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT
                id,
                subject_name

            FROM subjects

            WHERE
                institution_id = %s
                AND class_id = %s
                AND is_active = TRUE

            ORDER BY subject_name
        """, (
            session["institution_id"],
            class_id
        ))


    # -----------------------------------------------------
    # Staff
    # -----------------------------------------------------

    elif role == "staff":

        cur.execute("""
            SELECT DISTINCT
                s.id,
                s.subject_name

            FROM subjects s

            JOIN staff_subjects ss
                ON ss.subject_id = s.id

            WHERE
                s.institution_id = %s
                AND s.class_id = %s

                AND ss.institution_id = %s
                AND ss.staff_id = %s
                AND ss.is_active = TRUE

                AND s.is_active = TRUE

            ORDER BY s.subject_name
        """, (
            session["institution_id"],
            class_id,
            session["institution_id"],
            session["user_id"]
        ))


    else:

        cur.close()
        conn.close()

        return jsonify([])


    subjects = cur.fetchall()


    cur.close()
    conn.close()


    return jsonify(
        subjects
    )
    
# =========================================================
# 8. Exam Report
# =========================================================

def exam_report(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")

    # =====================================================
    # Get Exam
    # =====================================================

    cur.execute("""
        SELECT
            e.id,
            e.exam_name,
            e.exam_type,
            e.exam_date,
            e.total_mark,
            e.class_id,
            c.class_name

        FROM exams e

        JOIN classes c
            ON e.class_id = c.id

        WHERE
            e.id = %s
            AND e.institution_id = %s

        LIMIT 1
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
            url_for(
                "exams.exam_list"
            )
        )


    # =====================================================
    # Staff Class Access
    # =====================================================

    if role == "staff":

        if not _class_is_allowed(
            cur,
            exam["class_id"]
        ):

            cur.close()
            conn.close()

            flash(
                "You do not have access to this exam.",
                "error"
            )

            return redirect(
                url_for(
                    "exams.exam_list"
                )
            )


    # =====================================================
    # Get Exam Subjects
    # =====================================================

    cur.execute("""
        SELECT
            s.id,
            s.subject_name

        FROM exam_subjects es

        JOIN subjects s
            ON es.subject_id = s.id

        WHERE
            es.exam_id = %s

        ORDER BY
            s.subject_name
    """, (
        id,
    ))

    subjects = cur.fetchall()


    if not subjects:

        cur.close()
        conn.close()

        flash(
            "No subjects found for this exam.",
            "error"
        )

        return redirect(
            url_for(
                "exams.exam_list"
            )
        )


    # =====================================================
    # Staff Subject Access
    # =====================================================

    if role == "staff":

        allowed_subjects = []

        for subject in subjects:

            if _subject_is_allowed(
                cur,
                subject["id"],
                exam["class_id"]
            ):

                allowed_subjects.append(
                    subject
                )

        subjects = allowed_subjects


        if not subjects:

            cur.close()
            conn.close()

            flash(
                "You do not have access to the subjects in this exam.",
                "error"
            )

            return redirect(
                url_for(
                    "exams.exam_list"
                )
            )


    # =====================================================
    # Get Students
    # =====================================================

    cur.execute("""
        SELECT
            id,
            admission_no,
            full_name

        FROM students

        WHERE
            institution_id = %s
            AND class_id = %s
            AND is_active = TRUE

        ORDER BY
            full_name
    """, (
        session["institution_id"],
        exam["class_id"]
    ))

    students = cur.fetchall()


    # =====================================================
    # Get Marks
    # =====================================================

    subject_ids = [
        subject["id"]
        for subject in subjects
    ]


    cur.execute("""
        SELECT
            student_id,
            subject_id,
            mark,
            grade

        FROM exam_marks

        WHERE
            exam_id = %s
            AND subject_id = ANY(%s)
    """, (
        id,
        subject_ids
    ))

    marks = cur.fetchall()


    # =====================================================
    # Build Mark Lookup
    # =====================================================

    mark_lookup = {}

    for row in marks:

        mark_lookup[
            (
                row["student_id"],
                row["subject_id"]
            )
        ] = row


    # =====================================================
    # Build Report Rows
    # =====================================================

    report_rows = []


    for student in students:

        subject_results = []

        total_obtained = 0
        total_possible = 0


        for subject in subjects:

            result = mark_lookup.get(
                (
                    student["id"],
                    subject["id"]
                )
            )


            if result:

                mark = float(
                    result["mark"]
                )

                grade = result["grade"]

            else:

                mark = None
                grade = "-"


            subject_results.append({
                "subject_id": subject["id"],
                "subject_name": subject["subject_name"],
                "mark": mark,
                "grade": grade
            })


            if mark is not None:

                total_obtained += mark
                total_possible += float(
                    exam["total_mark"]
                )


        # =================================================
        # Overall Percentage
        # =================================================

        if total_possible > 0:

            percentage = (
                total_obtained
                / total_possible
            ) * 100

        else:

            percentage = 0


        # =================================================
        # Overall Grade
        # =================================================

        if percentage >= 90:

            overall_grade = "A+"

        elif percentage >= 80:

            overall_grade = "A"

        elif percentage >= 70:

            overall_grade = "B+"

        elif percentage >= 60:

            overall_grade = "B"

        elif percentage >= 50:

            overall_grade = "C"

        else:

            overall_grade = "D"


        report_rows.append({

            "student_id": student["id"],

            "admission_no":
                student["admission_no"],

            "full_name":
                student["full_name"],

            "subjects":
                subject_results,

            "total_obtained":
                total_obtained,

            "total_possible":
                total_possible,

            "percentage":
                round(
                    percentage,
                    2
                ),

            "grade":
                overall_grade
        })


    cur.close()
    conn.close()


    return render_template(
        "exams/report.html",
        exam=exam,
        subjects=subjects,
        report_rows=report_rows
    )                