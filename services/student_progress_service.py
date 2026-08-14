from flask import (
    render_template,
    session
)

from database.db import get_connection


# =========================================================
# Student Progress Hub
# =========================================================

def student_progress():

    student_id = session.get("student_id")
    institution_id = session.get("institution_id")


    # -----------------------------------------------------
    # Basic session validation
    # -----------------------------------------------------

    if not student_id or not institution_id:

        return "Unauthorized", 401


    conn = get_connection()
    cur = conn.cursor()


    # =====================================================
    # 1. Student Information
    # =====================================================

    cur.execute("""
        SELECT
            s.id,
            s.admission_no,
            s.full_name,
            s.class_id,
            c.class_name

        FROM students s

        LEFT JOIN classes c
            ON c.id = s.class_id
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

    student = cur.fetchone()


    if not student:

        cur.close()
        conn.close()

        return "Student not found.", 404


    # =====================================================
    # 2. Skill / Achievement Summary
    #
    # Only APPROVED records count as completed progress.
    # =====================================================

    cur.execute("""
        WITH module_summary AS (

            -- ---------------------------------------------
            -- Reading
            -- ---------------------------------------------

            SELECT
                'Reading' AS module,

                COUNT(*) AS approved_count,

                COALESCE(
                    SUM(points),
                    0
                ) AS points

            FROM reading_submissions

            WHERE
                student_id = %s
                AND institution_id = %s
                AND status = 'Approved'


            UNION ALL


            -- ---------------------------------------------
            -- Writing
            -- ---------------------------------------------

            SELECT
                'Writing' AS module,

                COUNT(*) AS approved_count,

                COALESCE(
                    SUM(points),
                    0
                ) AS points

            FROM writing_submissions

            WHERE
                student_id = %s
                AND institution_id = %s
                AND status = 'Approved'


            UNION ALL


            -- ---------------------------------------------
            -- Speaking
            -- ---------------------------------------------

            SELECT
                'Speaking' AS module,

                COUNT(*) AS approved_count,

                COALESCE(
                    SUM(points),
                    0
                ) AS points

            FROM speaking_submissions

            WHERE
                student_id = %s
                AND institution_id = %s
                AND status = 'Approved'


            UNION ALL


            -- ---------------------------------------------
            -- Language Skills
            -- ---------------------------------------------

            SELECT
                'Language Skills' AS module,

                COUNT(*) AS approved_count,

                COALESCE(
                    SUM(
                        COALESCE(points, 0)
                        +
                        COALESCE(bonus_points, 0)
                    ),
                    0
                ) AS points

            FROM language_skill_assessments

            WHERE
                student_id = %s
                AND institution_id = %s
                AND status = 'Approved'


            UNION ALL


            -- ---------------------------------------------
            -- Achievements
            -- ---------------------------------------------

            SELECT
                'Achievements' AS module,

                COUNT(*) AS approved_count,

                COALESCE(
                    SUM(
                        COALESCE(points, 0)
                        +
                        COALESCE(bonus_points, 0)
                    ),
                    0
                ) AS points

            FROM achievements

            WHERE
                student_id = %s
                AND institution_id = %s
                AND status = 'Approved'


            UNION ALL


            -- ---------------------------------------------
            -- Publications
            -- ---------------------------------------------

            SELECT
                'Publications' AS module,

                COUNT(*) AS approved_count,

                COALESCE(
                    SUM(
                        COALESCE(points, 0)
                        +
                        COALESCE(bonus_points, 0)
                    ),
                    0
                ) AS points

            FROM publications

            WHERE
                student_id = %s
                AND institution_id = %s
                AND status = 'Approved'


            UNION ALL


            -- ---------------------------------------------
            -- Paper Presentations
            -- ---------------------------------------------

            SELECT
                'Paper Presentation' AS module,

                COUNT(*) AS approved_count,

                COALESCE(
                    SUM(points),
                    0
                ) AS points

            FROM paper_presentations

            WHERE
                student_id = %s
                AND institution_id = %s
                AND status = 'Approved'
        )


        SELECT
            module,
            approved_count,
            points

        FROM module_summary

        ORDER BY
            CASE module
                WHEN 'Reading' THEN 1
                WHEN 'Writing' THEN 2
                WHEN 'Speaking' THEN 3
                WHEN 'Language Skills' THEN 4
                WHEN 'Achievements' THEN 5
                WHEN 'Publications' THEN 6
                WHEN 'Paper Presentation' THEN 7
                ELSE 99
            END
    """, (
        # Reading
        student_id,
        institution_id,

        # Writing
        student_id,
        institution_id,

        # Speaking
        student_id,
        institution_id,

        # Language
        student_id,
        institution_id,

        # Achievements
        student_id,
        institution_id,

        # Publications
        student_id,
        institution_id,

        # Paper
        student_id,
        institution_id
    ))

    module_rows = cur.fetchall()


    # =====================================================
    # 3. Convert Module Summary To Dictionary
    # =====================================================

    module_summary = {}

    for row in module_rows:

        module_summary[
            row["module"]
        ] = {

            "count":
                int(
                    row["approved_count"] or 0
                ),

            "points":
                round(
                    float(
                        row["points"] or 0
                    ),
                    2
                )
        }


    # =====================================================
    # 4. Overall Skill Points
    # =====================================================

    total_progress_points = round(
        sum(
            item["points"]
            for item in module_summary.values()
        ),
        2
    )


    total_approved_activities = sum(
        item["count"]
        for item in module_summary.values()
    )


    # =====================================================
    # 5. Attendance Summary
    # =====================================================

    cur.execute("""
        SELECT

            COUNT(*) AS total_days,

            COUNT(*) FILTER (
                WHERE status = 'Present'
            ) AS present_days,

            COUNT(*) FILTER (
                WHERE status = 'Absent'
            ) AS absent_days,

            COUNT(*) FILTER (
                WHERE status = 'Leave'
            ) AS leave_days

        FROM attendance

        WHERE
            student_id = %s
            AND institution_id = %s
    """, (
        student_id,
        institution_id
    ))

    attendance = cur.fetchone()


    present_days = int(
        attendance["present_days"] or 0
    )

    absent_days = int(
        attendance["absent_days"] or 0
    )

    leave_days = int(
        attendance["leave_days"] or 0
    )

    total_attendance_days = (
        present_days
        +
        absent_days
    )


    if total_attendance_days > 0:

        attendance_percentage = round(
            (
                present_days
                /
                total_attendance_days
            ) * 100,
            2
        )

    else:

        attendance_percentage = 0


    attendance_summary = {

        "total_days":
            int(
                attendance["total_days"] or 0
            ),

        "present_days":
            present_days,

        "absent_days":
            absent_days,

        "leave_days":
            leave_days,

        "percentage":
            attendance_percentage
    }


    # =====================================================
    # 6. Exam Performance
    # =====================================================

    cur.execute("""
        SELECT

            COALESCE(
                SUM(em.mark),
                0
            ) AS obtained_marks,

            COALESCE(
                SUM(e.total_mark),
                0
            ) AS possible_marks

        FROM exam_marks em

        JOIN exams e
            ON e.id = em.exam_id

        WHERE
            em.student_id = %s
            AND e.institution_id = %s
            AND e.is_active = TRUE
            AND em.subject_id IS NOT NULL
    """, (
        student_id,
        institution_id
    ))

    exam_summary = cur.fetchone()


    exam_obtained = float(
        exam_summary["obtained_marks"] or 0
    )

    exam_possible = float(
        exam_summary["possible_marks"] or 0
    )


    if exam_possible > 0:

        exam_percentage = round(
            (
                exam_obtained
                /
                exam_possible
            ) * 100,
            2
        )

    else:

        exam_percentage = 0


    exam_performance = {

        "obtained":
            round(
                exam_obtained,
                2
            ),

        "possible":
            round(
                exam_possible,
                2
            ),

        "percentage":
            exam_percentage
    }


    # =====================================================
    # 7. Recent Achievements
    # =====================================================

    cur.execute("""
        SELECT
            id,
            achievement_type,
            event_name,
            position,
            title,
            issuing_organization,
            achievement_date,
            points,
            bonus_points,
            description

        FROM achievements

        WHERE
            student_id = %s
            AND institution_id = %s
            AND status = 'Approved'

        ORDER BY
            achievement_date DESC NULLS LAST,
            id DESC

        LIMIT 5
    """, (
        student_id,
        institution_id
    ))

    achievements = cur.fetchall()


    # =====================================================
    # 8. Recent Reading
    # =====================================================

    cur.execute("""
        SELECT
            id,
            book_title,
            reading_type,
            pages,
            review,
            points,
            created_at

        FROM reading_submissions

        WHERE
            student_id = %s
            AND institution_id = %s
            AND status = 'Approved'

        ORDER BY
            created_at DESC,
            id DESC

        LIMIT 5
    """, (
        student_id,
        institution_id
    ))

    reading_records = cur.fetchall()


    # =====================================================
    # 9. Recent Writing
    # =====================================================

    cur.execute("""
        SELECT
            id,
            title,
            writing_type,
            pages,
            points,
            created_at

        FROM writing_submissions

        WHERE
            student_id = %s
            AND institution_id = %s
            AND status = 'Approved'

        ORDER BY
            created_at DESC,
            id DESC

        LIMIT 5
    """, (
        student_id,
        institution_id
    ))

    writing_records = cur.fetchall()


    # =====================================================
    # 10. Recent Speaking
    # =====================================================

    cur.execute("""
        SELECT
            id,
            title,
            presentation_date,
            duration_minutes,
            description,
            points,
            created_at

        FROM speaking_submissions

        WHERE
            student_id = %s
            AND institution_id = %s
            AND status = 'Approved'

        ORDER BY
            presentation_date DESC NULLS LAST,
            id DESC

        LIMIT 5
    """, (
        student_id,
        institution_id
    ))

    speaking_records = cur.fetchall()


    # =====================================================
    # 11. Recent Language Skills
    # =====================================================

    cur.execute("""
        SELECT
            id,
            language_name,
            skill_type,
            category,
            title,
            duration_minutes,
            pages,
            points,
            bonus_points,
            created_at

        FROM language_skill_assessments

        WHERE
            student_id = %s
            AND institution_id = %s
            AND status = 'Approved'

        ORDER BY
            created_at DESC,
            id DESC

        LIMIT 5
    """, (
        student_id,
        institution_id
    ))

    language_records = cur.fetchall()


    # =====================================================
    # 12. Recent Publications
    # =====================================================

    cur.execute("""
        SELECT
            id,
            publication_type,
            title,
            category,
            pages,
            publication_date,
            points,
            bonus_points,
            created_at

        FROM publications

        WHERE
            student_id = %s
            AND institution_id = %s
            AND status = 'Approved'

        ORDER BY
            publication_date DESC NULLS LAST,
            id DESC

        LIMIT 5
    """, (
        student_id,
        institution_id
    ))

    publication_records = cur.fetchall()


    # =====================================================
    # 13. Recent Paper Presentations
    # =====================================================

    cur.execute("""
        SELECT
            id,
            topic,
            presentation_level,
            affiliated_institution,
            description,
            points,
            created_at

        FROM paper_presentations

        WHERE
            student_id = %s
            AND institution_id = %s
            AND status = 'Approved'

        ORDER BY
            created_at DESC,
            id DESC

        LIMIT 5
    """, (
        student_id,
        institution_id
    ))

    paper_records = cur.fetchall()


    # =====================================================
    # Close Database
    # =====================================================

    cur.close()
    conn.close()


    # =====================================================
    # Render
    # =====================================================

    return render_template(
        "student/progress.html",

        student=student,

        module_summary=module_summary,

        total_progress_points=total_progress_points,

        total_approved_activities=
            total_approved_activities,

        attendance=attendance_summary,

        exam_performance=
            exam_performance,

        achievements=achievements,

        reading_records=
            reading_records,

        writing_records=
            writing_records,

        speaking_records=
            speaking_records,

        language_records=
            language_records,

        publication_records=
            publication_records,

        paper_records=
            paper_records
    )