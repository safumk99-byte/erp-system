from flask import (
    render_template,
    session
)

from database.db import get_connection


# =========================================================
# Performance Matrix
# =========================================================

def performance_matrix():

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")
    institution_id = session.get("institution_id")

    # =====================================================
    # Allowed Students
    # =====================================================

    if role == "institution_admin":

        student_condition = """
            s.institution_id = %s
            AND s.is_active = TRUE
        """

        student_params = [
            institution_id
        ]

    elif role == "staff":

        student_condition = """
            s.institution_id = %s
            AND s.is_active = TRUE

            AND EXISTS (
                SELECT 1
                FROM staff_classes sc
                WHERE
                    sc.institution_id = %s
                    AND sc.staff_id = %s
                    AND sc.class_id = s.class_id
                    AND sc.is_active = TRUE
            )
        """

        student_params = [
            institution_id,
            institution_id,
            session.get("user_id")
        ]

    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    # =====================================================
    # Point-based module totals
    #
    # Only APPROVED records are counted.
    # =====================================================

    query = f"""

        WITH module_points AS (

            -- Reading
            SELECT
                student_id,
                SUM(
                    COALESCE(points, 0)
                ) AS points
            FROM reading_submissions
            WHERE
                institution_id = %s
                AND status = 'Approved'
            GROUP BY student_id


            UNION ALL


            -- Writing
            SELECT
                student_id,
                SUM(
                    COALESCE(points, 0)
                ) AS points
            FROM writing_submissions
            WHERE
                institution_id = %s
                AND status = 'Approved'
            GROUP BY student_id


            UNION ALL


            -- Speaking
            SELECT
                student_id,
                SUM(
                    COALESCE(points, 0)
                ) AS points
            FROM speaking_submissions
            WHERE
                institution_id = %s
                AND status = 'Approved'
            GROUP BY student_id


            UNION ALL


            -- Publications
            SELECT
                student_id,
                SUM(
                    COALESCE(points, 0)
                    +
                    COALESCE(bonus_points, 0)
                ) AS points
            FROM publications
            WHERE
                institution_id = %s
                AND status = 'Approved'
            GROUP BY student_id


            UNION ALL


            -- Language Skills
            SELECT
                student_id,
                SUM(
                    COALESCE(points, 0)
                    +
                    COALESCE(bonus_points, 0)
                ) AS points
            FROM language_skill_assessments
            WHERE
                institution_id = %s
                AND status = 'Approved'
            GROUP BY student_id


            UNION ALL


            -- Achievements
            SELECT
                student_id,
                SUM(
                    COALESCE(points, 0)
                    +
                    COALESCE(bonus_points, 0)
                ) AS points
            FROM achievements
            WHERE
                institution_id = %s
                AND status = 'Approved'
            GROUP BY student_id


            UNION ALL


            -- Paper Presentations
            SELECT
                student_id,
                SUM(
                    COALESCE(points, 0)
                ) AS points
            FROM paper_presentations
            WHERE
                institution_id = %s
                AND status = 'Approved'
            GROUP BY student_id
        ),


        consolidated_points AS (

            SELECT
                student_id,
                SUM(points) AS css_points

            FROM module_points

            GROUP BY student_id
        ),


        exam_data AS (

            SELECT
                em.student_id,

                SUM(
                    em.mark
                ) AS obtained_marks,

                SUM(
                    e.total_mark
                ) AS possible_marks

            FROM exam_marks em

            JOIN exams e
                ON e.id = em.exam_id

            WHERE
                e.institution_id = %s
                AND e.is_active = TRUE

            GROUP BY em.student_id
        ),


        attendance_data AS (

            SELECT
                a.student_id,

                COUNT(*) AS total_periods,

                COUNT(*) FILTER (
                    WHERE a.status IN (
                        'Present',
                        'Late'
                    )
                ) AS attended_periods

            FROM attendance a

            WHERE
                a.institution_id = %s

            GROUP BY a.student_id
        )


        SELECT

            s.id,
            s.admission_no,
            s.full_name,

            c.id AS class_id,
            c.class_name,


            -- CSS / Consolidated Points
            COALESCE(
                cp.css_points,
                0
            ) AS css_points,


            -- Exam
            COALESCE(
                ed.obtained_marks,
                0
            ) AS exam_obtained,

            COALESCE(
                ed.possible_marks,
                0
            ) AS exam_possible,


            -- Attendance
            COALESCE(
                ad.total_periods,
                0
            ) AS attendance_total,

            COALESCE(
                ad.attended_periods,
                0
            ) AS attendance_attended


        FROM students s


        LEFT JOIN classes c
            ON c.id = s.class_id


        LEFT JOIN consolidated_points cp
            ON cp.student_id = s.id


        LEFT JOIN exam_data ed
            ON ed.student_id = s.id


        LEFT JOIN attendance_data ad
            ON ad.student_id = s.id


        WHERE
            {student_condition}


        ORDER BY
            c.class_name,
            s.full_name

    """


    params = [

        # Reading
        institution_id,

        # Writing
        institution_id,

        # Speaking
        institution_id,

        # Publication
        institution_id,

        # Language
        institution_id,

        # Achievement
        institution_id,

        # Paper
        institution_id,

        # Exam
        institution_id,

        # Attendance
        institution_id,

        # Students
        *student_params
    ]


    cur.execute(
        query,
        tuple(params)
    )


    rows = cur.fetchall()


    # =====================================================
    # Calculate Display Values
    # =====================================================

    students = []


    for row in rows:

        css_points = float(
            row["css_points"] or 0
        )


        exam_obtained = float(
            row["exam_obtained"] or 0
        )

        exam_possible = float(
            row["exam_possible"] or 0
        )


        if exam_possible > 0:

            exam_percentage = round(
                (
                    exam_obtained
                    / exam_possible
                ) * 100,
                2
            )

        else:

            exam_percentage = None


        attendance_total = int(
            row["attendance_total"] or 0
        )

        attendance_attended = int(
            row["attendance_attended"] or 0
        )


        if attendance_total > 0:

            attendance_percentage = round(
                (
                    attendance_attended
                    / attendance_total
                ) * 100,
                2
            )

        else:

            attendance_percentage = None


        students.append({

            "id":
                row["id"],

            "admission_no":
                row["admission_no"],

            "full_name":
                row["full_name"],

            "class_id":
                row["class_id"],

            "class_name":
                row["class_name"]
                or "Unassigned",

            "css_points":
                round(css_points, 2),

            "exam_percentage":
                exam_percentage,

            "attendance_percentage":
                attendance_percentage
        })


    # =====================================================
    # Class-wise Performance Matrix
    # =====================================================

    class_map = {}


    for student in students:

        class_name = (
            student["class_name"]
        )


        if class_name not in class_map:

            class_map[class_name] = {

                "class_id":
                    student["class_id"],

                "class_name":
                    class_name,

                "students":
                    0,

                "total_css":
                    0,

                "total_exam":
                    0,

                "exam_count":
                    0,

                "total_attendance":
                    0,

                "attendance_count":
                    0
            }


        item = class_map[class_name]


        item["students"] += 1

        item["total_css"] += (
            student["css_points"]
        )


        if student["exam_percentage"] is not None:

            item["total_exam"] += (
                student["exam_percentage"]
            )

            item["exam_count"] += 1


        if student["attendance_percentage"] is not None:

            item["total_attendance"] += (
                student["attendance_percentage"]
            )

            item["attendance_count"] += 1


    class_summary = []


    for item in class_map.values():

        if item["exam_count"] > 0:

            average_exam = round(
                item["total_exam"]
                / item["exam_count"],
                2
            )

        else:

            average_exam = None


        if item["attendance_count"] > 0:

            average_attendance = round(
                item["total_attendance"]
                / item["attendance_count"],
                2
            )

        else:

            average_attendance = None


        class_summary.append({

        "class_id":
            item.get("class_id"),

        "class_name":
            item["class_name"],

        "students":
            item["students"],

        "total_css":
            round(
                item["total_css"],
                2
            ),

        "average_css":
            round(
                item["total_css"]
                / item["students"],
                2
            )
            if item["students"] > 0
            else 0,

        "average_exam":
            average_exam,

        "average_attendance":
            average_attendance
    })


    cur.close()
    conn.close()


    return render_template(
        "performance/matrix.html",
        students=students,
        class_summary=class_summary
    )
    
# =========================================================
# Class Performance
# =========================================================

def class_performance(class_id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")
    institution_id = session.get("institution_id")


    # =====================================================
    # Verify Class Access
    # =====================================================

    if role == "institution_admin":

        cur.execute("""
            SELECT
                id,
                class_name

            FROM classes

            WHERE
                id = %s
                AND institution_id = %s
                AND is_active = TRUE
        """, (
            class_id,
            institution_id
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
                c.id = %s
                AND c.institution_id = %s

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

                AND c.is_active = TRUE
        """, (
            class_id,
            institution_id,
            institution_id,
            session.get("user_id")
        ))

    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    class_row = cur.fetchone()


    if not class_row:

        cur.close()
        conn.close()

        return "Class not found", 404


    # =====================================================
    # Students + CSS
    # =====================================================

    cur.execute("""
        SELECT

            s.id,
            s.admission_no,
            s.full_name,

            COALESCE(
                (
                    SELECT SUM(points)

                    FROM (

                        SELECT
                            COALESCE(
                                SUM(points),
                                0
                            ) AS points

                        FROM reading_submissions

                        WHERE
                            student_id = s.id
                            AND institution_id = %s
                            AND status = 'Approved'


                        UNION ALL


                        SELECT
                            COALESCE(
                                SUM(points),
                                0
                            )

                        FROM writing_submissions

                        WHERE
                            student_id = s.id
                            AND institution_id = %s
                            AND status = 'Approved'


                        UNION ALL


                        SELECT
                            COALESCE(
                                SUM(points),
                                0
                            )

                        FROM speaking_submissions

                        WHERE
                            student_id = s.id
                            AND institution_id = %s
                            AND status = 'Approved'


                        UNION ALL


                        SELECT
                            COALESCE(
                                SUM(points + bonus_points),
                                0
                            )

                        FROM publications

                        WHERE
                            student_id = s.id
                            AND institution_id = %s
                            AND status = 'Approved'


                        UNION ALL


                        SELECT
                            COALESCE(
                                SUM(points + bonus_points),
                                0
                            )

                        FROM language_skill_assessments

                        WHERE
                            student_id = s.id
                            AND institution_id = %s
                            AND status = 'Approved'


                        UNION ALL


                        SELECT
                            COALESCE(
                                SUM(
                                    COALESCE(points, 0)
                                    +
                                    COALESCE(bonus_points, 0)
                                ),
                                0
                            )

                        FROM achievements

                        WHERE
                            student_id = s.id
                            AND institution_id = %s
                            AND status = 'Approved'


                        UNION ALL


                        SELECT
                            COALESCE(
                                SUM(points),
                                0
                            )

                        FROM paper_presentations

                        WHERE
                            student_id = s.id
                            AND institution_id = %s
                            AND status = 'Approved'

                    ) module_points

                ),
                0
            ) AS css_points,


            -- =========================================
            -- Exam Percentage
            -- =========================================

            (
                SELECT
                    CASE
                        WHEN SUM(e.total_mark) > 0
                        THEN
                            ROUND(
                                (
                                    SUM(em.mark)
                                    /
                                    SUM(e.total_mark)
                                ) * 100,
                                2
                            )
                        ELSE NULL
                    END

                FROM exam_marks em

                JOIN exams e
                    ON e.id = em.exam_id

                WHERE
                    em.student_id = s.id
                    AND e.institution_id = %s
                    AND e.is_active = TRUE
            ) AS exam_percentage,


            -- =========================================
            -- Attendance Percentage
            -- =========================================

            (
                SELECT
                    CASE
                        WHEN COUNT(*) > 0
                        THEN
                            ROUND(
                                (
                                    COUNT(*) FILTER (
                                        WHERE a.status IN (
                                            'Present',
                                            'Late'
                                        )
                                    )::numeric
                                    /
                                    COUNT(*)
                                ) * 100,
                                2
                            )
                        ELSE NULL
                    END

                FROM attendance a

                WHERE
                    a.student_id = s.id
                    AND a.institution_id = %s
            ) AS attendance_percentage


        FROM students s


        WHERE
            s.institution_id = %s
            AND s.class_id = %s
            AND s.is_active = TRUE


        ORDER BY
            s.full_name
    """, (

        institution_id,  # reading
        institution_id,  # writing
        institution_id,  # speaking
        institution_id,  # publication
        institution_id,  # language
        institution_id,  # achievement
        institution_id,  # paper

        institution_id,  # exam
        institution_id,  # attendance

        institution_id,  # student institution
        class_id
    ))


    students = cur.fetchall()


    # =====================================================
    # Class Statistics
    # =====================================================

    total_students = len(students)


    if total_students > 0:

        average_css = round(
            sum(
                float(
                    student["css_points"] or 0
                )
                for student in students
            )
            / total_students,
            2
        )

    else:

        average_css = 0


    exam_values = [
        float(student["exam_percentage"])
        for student in students
        if student["exam_percentage"] is not None
    ]


    attendance_values = [
        float(student["attendance_percentage"])
        for student in students
        if student["attendance_percentage"] is not None
    ]


    average_exam = (
        round(
            sum(exam_values)
            / len(exam_values),
            2
        )
        if exam_values
        else None
    )


    average_attendance = (
        round(
            sum(attendance_values)
            / len(attendance_values),
            2
        )
        if attendance_values
        else None
    )


    cur.close()
    conn.close()


    return render_template(
        "performance/class.html",

        class_data=class_row,

        students=students,

        total_students=total_students,

        average_css=average_css,

        average_exam=average_exam,

        average_attendance=average_attendance
    )    