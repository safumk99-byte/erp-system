from flask import (
    render_template,
    session
)

from database.db import get_connection


# =========================================================
# Student Results
# =========================================================

def student_results():

    student_id = session.get("student_id")
    institution_id = session.get("institution_id")

    conn = get_connection()
    cur = conn.cursor()


    # =====================================================
    # Student
    # =====================================================

    cur.execute("""
        SELECT
            st.id,
            st.admission_no,
            st.full_name,
            st.class_id,
            c.class_name

        FROM students st

        LEFT JOIN classes c
            ON c.id = st.class_id
            AND c.institution_id = st.institution_id

        WHERE
            st.id = %s
            AND st.institution_id = %s
            AND st.is_active = TRUE

        LIMIT 1
    """, (
        student_id,
        institution_id
    ))

    student = cur.fetchone()


    if not student:

        cur.close()
        conn.close()

        return "Student not found.", 404


    # =====================================================
    # Get Exams With Marks
    # =====================================================

    cur.execute("""
        SELECT
            e.id AS exam_id,
            e.exam_name,
            e.exam_type,
            e.exam_date,
            e.total_mark,

            s.id AS subject_id,
            s.subject_name,

            em.mark,
            em.grade,
            em.remark

        FROM exam_marks em

        JOIN exams e
            ON e.id = em.exam_id

        JOIN subjects s
            ON s.id = em.subject_id

        WHERE
            em.student_id = %s
            AND e.institution_id = %s
            AND e.class_id = %s
            AND e.is_active = TRUE
            AND em.subject_id IS NOT NULL

        ORDER BY
            e.exam_date DESC,
            e.id DESC,
            s.subject_name ASC
    """, (
        student_id,
        institution_id,
        student["class_id"]
    ))

    marks = cur.fetchall()


    # =====================================================
    # Group Results By Exam
    # =====================================================

    grouped_results = {}


    for row in marks:

        exam_id = row["exam_id"]


        if exam_id not in grouped_results:

            grouped_results[exam_id] = {

                "exam_id": exam_id,

                "exam_name":
                    row["exam_name"],

                "exam_type":
                    row["exam_type"],

                "exam_date":
                    row["exam_date"],

                "total_mark":
                    float(row["total_mark"]),

                "subjects": [],

                "total_obtained": 0,

                "total_possible": 0

            }


        result = grouped_results[exam_id]


        # -------------------------------------------------
        # Subject Result
        # -------------------------------------------------

        mark = float(
            row["mark"]
        )


        result["subjects"].append({

            "subject_id":
                row["subject_id"],

            "subject_name":
                row["subject_name"],

            "mark":
                mark,

            "grade":
                row["grade"],

            "remark":
                row["remark"]

        })


        # -------------------------------------------------
        # Totals
        # -------------------------------------------------

        result["total_obtained"] += mark

        result["total_possible"] += float(
            row["total_mark"]
        )


    # =====================================================
    # Calculate Percentage + Overall Grade
    # =====================================================

    results = []


    for result in grouped_results.values():

        total_obtained = result[
            "total_obtained"
        ]

        total_possible = result[
            "total_possible"
        ]


        if total_possible > 0:

            percentage = (
                total_obtained
                /
                total_possible
            ) * 100

        else:

            percentage = 0


        percentage = round(
            percentage,
            2
        )


        # -------------------------------------------------
        # Overall Grade
        # -------------------------------------------------

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


        result["total_obtained"] = round(
            total_obtained,
            2
        )

        result["total_possible"] = round(
            total_possible,
            2
        )

        result["percentage"] = percentage

        result["grade"] = overall_grade


        results.append(result)


    # =====================================================
    # Close
    # =====================================================

    cur.close()
    conn.close()


    # =====================================================
    # Render
    # =====================================================

    return render_template(
        "student/results.html",

        student=student,

        results=results
    )
    
# =========================================================
# Student Exams
# =========================================================

def student_exams():

    student_id = session.get("student_id")
    institution_id = session.get("institution_id")

    conn = get_connection()
    cur = conn.cursor()


    # =====================================================
    # Student
    # =====================================================

    cur.execute("""
        SELECT
            st.id,
            st.admission_no,
            st.full_name,
            st.class_id,
            c.class_name

        FROM students st

        LEFT JOIN classes c
            ON c.id = st.class_id
            AND c.institution_id = st.institution_id

        WHERE
            st.id = %s
            AND st.institution_id = %s
            AND st.is_active = TRUE

        LIMIT 1
    """, (
        student_id,
        institution_id
    ))

    student = cur.fetchone()


    if not student:

        cur.close()
        conn.close()

        return "Student not found.", 404


    # =====================================================
    # Exams
    # =====================================================

    cur.execute("""
        SELECT
            e.id,
            e.exam_name,
            e.exam_type,
            e.exam_date,
            e.total_mark,

            STRING_AGG(
                s.subject_name,
                ', '
                ORDER BY s.subject_name
            ) AS subjects

        FROM exams e

        JOIN exam_subjects es
            ON es.exam_id = e.id

        JOIN subjects s
            ON s.id = es.subject_id

        WHERE
            e.institution_id = %s
            AND e.class_id = %s
            AND e.is_active = TRUE

        GROUP BY
            e.id,
            e.exam_name,
            e.exam_type,
            e.exam_date,
            e.total_mark

        ORDER BY
            e.exam_date DESC,
            e.id DESC
    """, (
        institution_id,
        student["class_id"]
    ))

    exams = cur.fetchall()


    # =====================================================
    # Prepare Exam Status
    # =====================================================

    from datetime import date

    today = date.today()

    exam_list = []


    for exam in exams:

        exam_data = dict(exam)

        exam_date = exam_data["exam_date"]


        if exam_date > today:

            exam_data["status"] = "Upcoming"

        elif exam_date == today:

            exam_data["status"] = "Today"

        else:

            exam_data["status"] = "Completed"


        exam_list.append(
            exam_data
        )


    # =====================================================
    # Close
    # =====================================================

    cur.close()
    conn.close()


    # =====================================================
    # Render
    # =====================================================

    return render_template(
        "student/exams.html",

        student=student,

        exams=exam_list
    )    