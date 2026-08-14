from flask import (
    render_template,
    session
)

from database.db import get_connection


# =========================================================
# Parent Dashboard
# =========================================================

def parent_dashboard():

    parent_user_id = session.get("user_id")
    institution_id = session.get("institution_id")


    # -----------------------------------------------------
    # Session Validation
    # -----------------------------------------------------

    if not parent_user_id or not institution_id:

        return "Unauthorized", 401


    conn = get_connection()
    cur = conn.cursor()


    # =====================================================
    # 1. Get Parent's Children
    # =====================================================

    cur.execute("""
        SELECT
            s.id,
            s.admission_no,
            s.full_name,
            s.photo,
            s.class_id,
            c.class_name

        FROM students s

        LEFT JOIN classes c
            ON c.id = s.class_id
            AND c.institution_id = s.institution_id

        WHERE
            s.parent_user_id = %s
            AND s.institution_id = %s
            AND s.is_active = TRUE

        ORDER BY
            s.full_name
    """, (
        parent_user_id,
        institution_id
    ))

    children = cur.fetchall()


    # =====================================================
    # No Children
    # =====================================================

    if not children:

        cur.close()
        conn.close()

        return render_template(
            "dashboard/parent.html",
            children=[]
        )


    # =====================================================
    # 2. Prepare Child Dashboard Data
    # =====================================================

    child_data = []


    for child in children:

        student_id = child["id"]


        # =================================================
        # Attendance
        # =================================================

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

        total_days = int(
            attendance["total_days"] or 0
        )


        # -------------------------------------------------
        # Attendance Percentage
        # -------------------------------------------------

        attendance_days = (
            present_days
            +
            absent_days
        )


        if attendance_days > 0:

            attendance_percentage = round(
                (
                    present_days
                    /
                    attendance_days
                ) * 100,
                2
            )

        else:

            attendance_percentage = 0


        attendance_data = {

            "total_days":
                total_days,

            "present_days":
                present_days,

            "absent_days":
                absent_days,

            "leave_days":
                leave_days,

            "percentage":
                attendance_percentage
        }


        # =================================================
        # Exam Performance
        # =================================================

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

        exam = cur.fetchone()


        obtained_marks = float(
            exam["obtained_marks"] or 0
        )

        possible_marks = float(
            exam["possible_marks"] or 0
        )


        if possible_marks > 0:

            exam_percentage = round(
                (
                    obtained_marks
                    /
                    possible_marks
                ) * 100,
                2
            )

        else:

            exam_percentage = 0


        exam_data = {

            "obtained":
                round(
                    obtained_marks,
                    2
                ),

            "possible":
                round(
                    possible_marks,
                    2
                ),

            "percentage":
                exam_percentage
        }


        # =================================================
        # Recent Achievements
        # =================================================

        cur.execute("""
            SELECT
                id,
                title,
                achievement_type,
                event_name,
                position,
                achievement_date,
                points,
                bonus_points

            FROM achievements

            WHERE
                student_id = %s
                AND institution_id = %s
                AND status = 'Approved'

            ORDER BY
                achievement_date DESC NULLS LAST,
                id DESC

            LIMIT 3
        """, (
            student_id,
            institution_id
        ))

        achievements = cur.fetchall()


        # =================================================
        # Recent Exams
        # =================================================

        cur.execute("""
            SELECT DISTINCT
                e.id,
                e.exam_name,
                e.exam_type,
                e.exam_date,
                e.total_mark

            FROM exams e

            JOIN exam_marks em
                ON em.exam_id = e.id

            WHERE
                em.student_id = %s
                AND e.institution_id = %s
                AND e.is_active = TRUE

            ORDER BY
                e.exam_date DESC,
                e.id DESC

            LIMIT 5
        """, (
            student_id,
            institution_id
        ))

        recent_exams = cur.fetchall()


        # =================================================
        # Child Data
        # =================================================

        child_data.append({

            "student":
                child,

            "attendance":
                attendance_data,

            "exam":
                exam_data,

            "achievements":
                achievements,

            "recent_exams":
                recent_exams
        })


    # =====================================================
    # Close Database
    # =====================================================

    cur.close()
    conn.close()


    # =====================================================
    # Render
    # =====================================================

    return render_template(
        "dashboard/parent.html",
        children=child_data
    )
    
# =========================================================
# Parent Child Progress
# =========================================================

def parent_child_progress(student_id):

    parent_user_id = session.get("user_id")
    institution_id = session.get("institution_id")

    if not parent_user_id or not institution_id:
        return "Unauthorized", 401

    conn = get_connection()
    cur = conn.cursor()

    # -----------------------------------------------------
    # Verify Parent -> Child Relationship
    # -----------------------------------------------------

    cur.execute("""
        SELECT
            s.id,
            s.admission_no,
            s.full_name,
            s.photo,
            c.class_name

        FROM students s

        LEFT JOIN classes c
            ON c.id = s.class_id
            AND c.institution_id = s.institution_id

        WHERE
            s.id = %s
            AND s.parent_user_id = %s
            AND s.institution_id = %s
            AND s.is_active = TRUE

        LIMIT 1
    """, (
        student_id,
        parent_user_id,
        institution_id
    ))

    student = cur.fetchone()

    if not student:

        cur.close()
        conn.close()

        return "Unauthorized", 403

    # =====================================================
    # Attendance
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

    present = int(attendance["present_days"] or 0)
    absent = int(attendance["absent_days"] or 0)
    leave = int(attendance["leave_days"] or 0)

    attendance_total = present + absent

    attendance_percentage = (
        round((present / attendance_total) * 100, 2)
        if attendance_total > 0
        else 0
    )

    attendance = {
        "total_days": int(
            attendance["total_days"] or 0
        ),
        "present_days": present,
        "absent_days": absent,
        "leave_days": leave,
        "percentage": attendance_percentage
    }

    # =====================================================
    # Module Summary
    # =====================================================

    cur.execute("""
        SELECT
            'Reading' AS module,
            COUNT(*) AS activity_count,
            COALESCE(SUM(points), 0) AS points
        FROM reading_submissions
        WHERE
            student_id = %s
            AND institution_id = %s
            AND status = 'Approved'

        UNION ALL

        SELECT
            'Writing',
            COUNT(*),
            COALESCE(SUM(points), 0)
        FROM writing_submissions
        WHERE
            student_id = %s
            AND institution_id = %s
            AND status = 'Approved'

        UNION ALL

        SELECT
            'Speaking',
            COUNT(*),
            COALESCE(SUM(points), 0)
        FROM speaking_submissions
        WHERE
            student_id = %s
            AND institution_id = %s
            AND status = 'Approved'

        UNION ALL

        SELECT
            'Language Skills',
            COUNT(*),
            COALESCE(
                SUM(
                    COALESCE(points, 0)
                    +
                    COALESCE(bonus_points, 0)
                ),
                0
            )
        FROM language_skill_assessments
        WHERE
            student_id = %s
            AND institution_id = %s
            AND status = 'Approved'

        UNION ALL

        SELECT
            'Achievements',
            COUNT(*),
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
            student_id = %s
            AND institution_id = %s
            AND status = 'Approved'

        UNION ALL

        SELECT
            'Publications',
            COUNT(*),
            COALESCE(
                SUM(
                    COALESCE(points, 0)
                    +
                    COALESCE(bonus_points, 0)
                ),
                0
            )
        FROM publications
        WHERE
            student_id = %s
            AND institution_id = %s
            AND status = 'Approved'

        UNION ALL

        SELECT
            'Paper Presentation',
            COUNT(*),
            COALESCE(SUM(points), 0)
        FROM paper_presentations
        WHERE
            student_id = %s
            AND institution_id = %s
            AND status = 'Approved'
    """, (
        student_id, institution_id,
        student_id, institution_id,
        student_id, institution_id,
        student_id, institution_id,
        student_id, institution_id,
        student_id, institution_id,
        student_id, institution_id
    ))

    module_rows = cur.fetchall()

    module_summary = {}

    for row in module_rows:

        module_summary[row["module"]] = {
            "count": int(
                row["activity_count"] or 0
            ),
            "points": round(
                float(row["points"] or 0),
                2
            )
        }

    total_points = round(
        sum(
            item["points"]
            for item in module_summary.values()
        ),
        2
    )

    total_activities = sum(
        item["count"]
        for item in module_summary.values()
    )

    # =====================================================
    # Exam Performance
    # =====================================================

    cur.execute("""
        SELECT

            COALESCE(
                SUM(em.mark),
                0
            ) AS obtained,

            COALESCE(
                SUM(e.total_mark),
                0
            ) AS possible

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

    exam = cur.fetchone()

    obtained = float(
        exam["obtained"] or 0
    )

    possible = float(
        exam["possible"] or 0
    )

    exam_percentage = (
        round((obtained / possible) * 100, 2)
        if possible > 0
        else 0
    )

    exam_performance = {
        "obtained": round(obtained, 2),
        "possible": round(possible, 2),
        "percentage": exam_percentage
    }

    # =====================================================
    # Achievements
    # =====================================================

    cur.execute("""
        SELECT
            id,
            title,
            achievement_type,
            event_name,
            position,
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

        LIMIT 10
    """, (
        student_id,
        institution_id
    ))

    achievements = cur.fetchall()

    # =====================================================
    # Recent Reading
    # =====================================================

    cur.execute("""
        SELECT
            id,
            book_title,
            reading_type,
            pages,
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
    # Recent Writing
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
    # Recent Speaking
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
    # Language Skills
    # =====================================================

    cur.execute("""
        SELECT
            id,
            language_name,
            skill_type,
            category,
            title,
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
    # Publications
    # =====================================================

    cur.execute("""
        SELECT
            id,
            publication_type,
            title,
            category,
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
    # Paper Presentation
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

    cur.close()
    conn.close()

    return render_template(
        "parent/child_progress.html",

        student=student,

        module_summary=module_summary,

        total_points=total_points,

        total_activities=total_activities,

        attendance=attendance,

        exam_performance=exam_performance,

        achievements=achievements,

        reading_records=reading_records,

        writing_records=writing_records,

        speaking_records=speaking_records,

        language_records=language_records,

        publication_records=publication_records,

        paper_records=paper_records
    )    
    
