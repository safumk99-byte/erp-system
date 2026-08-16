from datetime import date

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for
)

from database.db import get_connection


institution_dashboard = Blueprint(
    "institution_dashboard",
    __name__
)


# =========================================================
# Institution Dashboard
# =========================================================

@institution_dashboard.route(
    "/institution/dashboard"
)
def dashboard():

    # =====================================================
    # Authentication
    # =====================================================

    if session.get("role") != "institution_admin":

        return redirect(
            url_for("auth.login")
        )

    institution_id = session.get(
        "institution_id"
    )

    if not institution_id:

        return redirect(
            url_for("auth.login")
        )


    # =====================================================
    # Read Filters
    # =====================================================

    selected_month = request.args.get(
        "month",
        ""
    ).strip()

    selected_academic_year_id = request.args.get(
        "academic_year_id",
        ""
    ).strip()

    selected_course_id = request.args.get(
        "course_id",
        ""
    ).strip()


    # =====================================================
    # Validate Month
    # =====================================================

    month_number = None

    if selected_month:

        try:

            value = int(
                selected_month
            )

            if 1 <= value <= 12:

                month_number = value

        except (
            ValueError,
            TypeError
        ):

            month_number = None


    # =====================================================
    # Validate Academic Year
    # =====================================================

    academic_year_id = None

    if selected_academic_year_id:

        try:

            academic_year_id = int(
                selected_academic_year_id
            )

        except (
            ValueError,
            TypeError
        ):

            academic_year_id = None


    # =====================================================
    # Validate Course
    # =====================================================

    course_id = None

    if selected_course_id:

        try:

            course_id = int(
                selected_course_id
            )

        except (
            ValueError,
            TypeError
        ):

            course_id = None


    # =====================================================
    # Database
    # =====================================================

    conn = get_connection()
    cur = conn.cursor()


    try:

        # =================================================
        # Academic Year Options
        # =================================================

        cur.execute("""
            SELECT
                id,
                year_name,
                start_date,
                end_date,
                is_current

            FROM academic_years

            WHERE
                institution_id = %s
                AND is_active = TRUE

            ORDER BY
                start_date DESC,
                id DESC
        """, (
            institution_id,
        ))

        academic_years = cur.fetchall()


        # =================================================
        # Select Academic Year
        # =================================================

        academic_year = None


        if academic_year_id:

            for item in academic_years:

                if item["id"] == academic_year_id:

                    academic_year = item
                    break


        # -------------------------------------------------
        # Default = Current Academic Year
        # -------------------------------------------------

        if not academic_year:

            for item in academic_years:

                if item["is_current"]:

                    academic_year = item
                    break


        # -------------------------------------------------
        # Fallback = Latest Academic Year
        # -------------------------------------------------

        if not academic_year and academic_years:

            academic_year = academic_years[0]


        if academic_year:

            academic_year_id = academic_year["id"]

        else:

            academic_year_id = None


        # =================================================
        # Academic Year Date Range
        # =================================================

        date_start = None
        date_end = None


        if academic_year:

            date_start = academic_year["start_date"]
            date_end = academic_year["end_date"]


        # =================================================
        # Month Filter
        # =================================================

        if month_number:

            if academic_year:

                academic_start = (
                    academic_year["start_date"]
                )

                academic_end = (
                    academic_year["end_date"]
                )

                start_year = (
                    academic_start.year
                )

                end_year = (
                    academic_end.year
                )

                start_month = (
                    academic_start.month
                )

                # -----------------------------------------
                # Academic Year Month Mapping
                # -----------------------------------------
                #
                # Example:
                #
                # 2026-06 → 2027-05
                #
                # June-December = 2026
                # January-May   = 2027
                #
                # -----------------------------------------

                if month_number >= start_month:

                    target_year = start_year

                else:

                    target_year = end_year

            else:

                target_year = date.today().year


            month_start = date(
                target_year,
                month_number,
                1
            )


            if month_number == 12:

                month_end = date(
                    target_year + 1,
                    1,
                    1
                )

            else:

                month_end = date(
                    target_year,
                    month_number + 1,
                    1
                )


            # -----------------------------------------
            # Keep month inside academic year
            # -----------------------------------------

            if academic_year:

                academic_start = (
                    academic_year["start_date"]
                )

                academic_end = (
                    academic_year["end_date"]
                )


                if month_start < academic_start:

                    month_start = academic_start


                if month_end > academic_end:

                    month_end = academic_end


            date_start = month_start
            date_end = month_end


        # =================================================
        # Course Options
        # =================================================

        cur.execute("""
            SELECT
                id,
                course_name,
                course_code

            FROM courses

            WHERE
                institution_id = %s
                AND is_active = TRUE

            ORDER BY
                course_name ASC
        """, (
            institution_id,
        ))

        courses = cur.fetchall()


        # =================================================
        # Selected Course
        # =================================================

        selected_course = None


        if course_id:

            for course in courses:

                if course["id"] == course_id:

                    selected_course = course
                    break


        if not selected_course:

            course_id = None


        # =================================================
        # COURSE CLASS CONDITION
        # =================================================

        course_class_condition = ""
        course_class_params = []


        if course_id:

            course_class_condition = """
                AND c.course_id = %s
            """

            course_class_params.append(
                course_id
            )


        # =================================================
        # 1. TOTAL STUDENTS
        # =================================================

        student_query = """
            SELECT
                COUNT(*) AS total_students

            FROM students s

            WHERE
                s.institution_id = %s
                AND s.is_active = TRUE
        """

        student_params = [
            institution_id
        ]


        if course_id:

            student_query += """
                AND EXISTS (
                    SELECT 1

                    FROM classes c

                    WHERE
                        c.id = s.class_id
                        AND c.institution_id = s.institution_id
                        AND c.is_active = TRUE
                        AND c.course_id = %s
                )
            """

            student_params.append(
                course_id
            )


        cur.execute(
            student_query,
            tuple(student_params)
        )

        result = cur.fetchone()

        total_students = (
            result["total_students"] or 0
            if result
            else 0
        )


        # =================================================
        # 2. TOTAL STAFF
        # =================================================

        staff_query = """
            SELECT
                COUNT(DISTINCT u.id) AS total_staff

            FROM users u

            JOIN roles r
                ON u.role_id = r.id

            WHERE
                u.institution_id = %s
                AND u.is_active = TRUE
                AND r.name = 'staff'
        """

        staff_params = [
            institution_id
        ]


        if course_id:

            staff_query += """
                AND EXISTS (
                    SELECT 1

                    FROM staff_classes sc

                    JOIN classes c
                        ON c.id = sc.class_id
                        AND c.institution_id = sc.institution_id

                    WHERE
                        sc.staff_id = u.id
                        AND sc.institution_id = u.institution_id
                        AND sc.is_active = TRUE
                        AND c.is_active = TRUE
                        AND c.course_id = %s
                )
            """

            staff_params.append(
                course_id
            )


        cur.execute(
            staff_query,
            tuple(staff_params)
        )

        result = cur.fetchone()

        total_staff = (
            result["total_staff"] or 0
            if result
            else 0
        )


        # =================================================
        # 3. TOTAL CLASSES
        # =================================================

        class_query = """
            SELECT
                COUNT(*) AS total_classes

            FROM classes c

            WHERE
                c.institution_id = %s
                AND c.is_active = TRUE
        """

        class_params = [
            institution_id
        ]


        if course_id:

            class_query += """
                AND c.course_id = %s
            """

            class_params.append(
                course_id
            )


        cur.execute(
            class_query,
            tuple(class_params)
        )

        result = cur.fetchone()

        total_classes = (
            result["total_classes"] or 0
            if result
            else 0
        )


        # =================================================
        # 4. TOTAL SUBJECTS
        # =================================================

        subject_query = """
            SELECT
                COUNT(*) AS total_subjects

            FROM subjects s

            JOIN classes c
                ON c.id = s.class_id
                AND c.institution_id = s.institution_id

            WHERE
                s.institution_id = %s
                AND s.is_active = TRUE
                AND c.is_active = TRUE
        """

        subject_params = [
            institution_id
        ]


        if course_id:

            subject_query += """
                AND c.course_id = %s
            """

            subject_params.append(
                course_id
            )


        cur.execute(
            subject_query,
            tuple(subject_params)
        )

        result = cur.fetchone()

        total_subjects = (
            result["total_subjects"] or 0
            if result
            else 0
        )


        # =================================================
        # 5. ATTENDANCE
        # =================================================

        attendance_query = """
            SELECT

                COUNT(*) AS total,

                COUNT(*) FILTER (
                    WHERE a.status = 'Present'
                ) AS present,

                COUNT(*) FILTER (
                    WHERE a.status = 'Absent'
                ) AS absent,

                COUNT(*) FILTER (
                    WHERE a.status = 'Leave'
                ) AS leave

            FROM attendance a

            JOIN students s
                ON s.id = a.student_id
                AND s.institution_id = a.institution_id

            WHERE
                a.institution_id = %s
                AND s.is_active = TRUE
        """

        attendance_params = [
            institution_id
        ]


        # -------------------------------------------------
        # Course
        # -------------------------------------------------

        if course_id:

            attendance_query += """
                AND EXISTS (
                    SELECT 1

                    FROM classes c

                    WHERE
                        c.id = s.class_id
                        AND c.institution_id = s.institution_id
                        AND c.is_active = TRUE
                        AND c.course_id = %s
                )
            """

            attendance_params.append(
                course_id
            )


        # -------------------------------------------------
        # Date Range
        # -------------------------------------------------

        if date_start:

            attendance_query += """
                AND a.attendance_date >= %s
            """

            attendance_params.append(
                date_start
            )


        if date_end:

            attendance_query += """
                AND a.attendance_date < %s
            """

            attendance_params.append(
                date_end
            )


        cur.execute(
            attendance_query,
            tuple(attendance_params)
        )

        attendance = cur.fetchone()


        attendance_total = (
            attendance["total"] or 0
            if attendance
            else 0
        )

        attendance_present = (
            attendance["present"] or 0
            if attendance
            else 0
        )

        attendance_absent = (
            attendance["absent"] or 0
            if attendance
            else 0
        )

        attendance_leave = (
            attendance["leave"] or 0
            if attendance
            else 0
        )


        if attendance_total:

            attendance_percentage = round(
                (
                    attendance_present
                    / attendance_total
                ) * 100,
                1
            )

        else:

            attendance_percentage = 0


        # =================================================
        # Approval Helper
        # =================================================

        def pending_count(
            table_name
        ):

            query = f"""
                SELECT
                    COUNT(*) AS count

                FROM {table_name}

                WHERE
                    institution_id = %s
                    AND status = 'Pending'
            """

            params = [
                institution_id
            ]


            if date_start:

                query += """
                    AND created_at >= %s
                """

                params.append(
                    date_start
                )


            if date_end:

                query += """
                    AND created_at < %s
                """

                params.append(
                    date_end
                )


            cur.execute(
                query,
                tuple(params)
            )

            result = cur.fetchone()

            return (
                result["count"] or 0
                if result
                else 0
            )


        # =================================================
        # 6. PENDING APPROVALS
        # =================================================

        pending_reading = pending_count(
            "reading_submissions"
        )

        pending_writing = pending_count(
            "writing_submissions"
        )

        pending_speaking = pending_count(
            "speaking_submissions"
        )

        pending_publication = pending_count(
            "publications"
        )

        pending_presentation = pending_count(
            "paper_presentations"
        )

        pending_language = pending_count(
            "language_skill_assessments"
        )

        pending_achievement = pending_count(
            "achievements"
        )


        total_pending_approvals = (
            pending_reading
            + pending_writing
            + pending_speaking
            + pending_publication
            + pending_presentation
            + pending_language
            + pending_achievement
        )


        # =================================================
        # 7. PENDING LEAVES
        # =================================================

        leave_query = """
            SELECT
                COUNT(*) AS count

            FROM student_leave_requests slr

            WHERE
                slr.institution_id = %s
                AND slr.status = 'Pending'
        """

        leave_params = [
            institution_id
        ]


        if date_start:

            leave_query += """
                AND slr.leave_date >= %s
            """

            leave_params.append(
                date_start
            )


        if date_end:

            leave_query += """
                AND slr.leave_date < %s
            """

            leave_params.append(
                date_end
            )


        if course_id:

            leave_query += """
                AND EXISTS (
                    SELECT 1

                    FROM students s

                    JOIN classes c
                        ON c.id = s.class_id
                        AND c.institution_id = s.institution_id

                    WHERE
                        s.id = slr.student_id
                        AND s.institution_id = slr.institution_id
                        AND c.course_id = %s
                )
            """

            leave_params.append(
                course_id
            )


        cur.execute(
            leave_query,
            tuple(leave_params)
        )

        result = cur.fetchone()

        pending_leaves = (
            result["count"] or 0
            if result
            else 0
        )


        # =================================================
        # 8. UNREAD NOTIFICATIONS
        # =================================================

        unread_notifications = 0

        user_id = session.get(
            "user_id"
        )


        if user_id:

            cur.execute("""
                SELECT
                    COUNT(*) AS count

                FROM notifications

                WHERE
                    user_id = %s
                    AND institution_id = %s
                    AND is_read = FALSE
            """, (
                user_id,
                institution_id
            ))

            result = cur.fetchone()

            if result:

                unread_notifications = (
                    result["count"] or 0
                )


        # =================================================
        # 9. RECENT STUDENTS
        # =================================================

        recent_students_query = """
            SELECT
                s.id,
                s.admission_no,
                s.full_name,
                s.created_at

            FROM students s

            WHERE
                s.institution_id = %s
                AND s.is_active = TRUE
        """

        recent_students_params = [
            institution_id
        ]


        if course_id:

            recent_students_query += """
                AND EXISTS (
                    SELECT 1

                    FROM classes c

                    WHERE
                        c.id = s.class_id
                        AND c.institution_id = s.institution_id
                        AND c.is_active = TRUE
                        AND c.course_id = %s
                )
            """

            recent_students_params.append(
                course_id
            )


        recent_students_query += """
            ORDER BY
                s.created_at DESC NULLS LAST,
                s.id DESC

            LIMIT 5
        """


        cur.execute(
            recent_students_query,
            tuple(recent_students_params)
        )

        recent_students = cur.fetchall()


        # =================================================
        # 10. UPCOMING EXAMS
        # =================================================

        upcoming_exams_query = """
            SELECT
                e.id,
                e.exam_name,
                e.exam_type,
                e.exam_date

            FROM exams e

            WHERE
                e.institution_id = %s
        """

        upcoming_exams_params = [
            institution_id
        ]


        # -------------------------------------------------
        # Date
        # -------------------------------------------------

        if date_start:

            upcoming_exams_query += """
                AND e.exam_date >= %s
            """

            upcoming_exams_params.append(
                date_start
            )

        else:

            upcoming_exams_query += """
                AND e.exam_date >= CURRENT_DATE
            """


        if date_end:

            upcoming_exams_query += """
                AND e.exam_date < %s
            """

            upcoming_exams_params.append(
                date_end
            )


        # -------------------------------------------------
        # Course
        # -------------------------------------------------

        if course_id:

            upcoming_exams_query += """
                AND EXISTS (
                    SELECT 1

                    FROM exam_subjects es

                    JOIN subjects s
                        ON s.id = es.subject_id
                        AND s.institution_id = e.institution_id

                    JOIN classes c
                        ON c.id = s.class_id
                        AND c.institution_id = e.institution_id

                    WHERE
                        es.exam_id = e.id
                        AND c.course_id = %s
                        AND c.is_active = TRUE
                )
            """

            upcoming_exams_params.append(
                course_id
            )


        upcoming_exams_query += """
            ORDER BY
                e.exam_date ASC

            LIMIT 5
        """


        cur.execute(
            upcoming_exams_query,
            tuple(upcoming_exams_params)
        )

        upcoming_exams = cur.fetchall()


        # =================================================
        # Render Dashboard
        # =================================================

        return render_template(
            "institution/dashboard.html",

            # -------------------------------------------------
            # Statistics
            # -------------------------------------------------

            total_students=total_students,
            total_staff=total_staff,
            total_classes=total_classes,
            total_subjects=total_subjects,


            # -------------------------------------------------
            # Attendance
            # -------------------------------------------------

            attendance_total=attendance_total,
            attendance_present=attendance_present,
            attendance_absent=attendance_absent,
            attendance_leave=attendance_leave,
            attendance_percentage=attendance_percentage,


            # -------------------------------------------------
            # Pending Approvals
            # -------------------------------------------------

            pending_reading=pending_reading,
            pending_writing=pending_writing,
            pending_speaking=pending_speaking,
            pending_publication=pending_publication,
            pending_presentation=pending_presentation,
            pending_language=pending_language,
            pending_achievement=pending_achievement,

            total_pending_approvals=total_pending_approvals,

            pending_leaves=pending_leaves,


            # -------------------------------------------------
            # Notifications
            # -------------------------------------------------

            unread_notifications=unread_notifications,


            # -------------------------------------------------
            # Lists
            # -------------------------------------------------

            recent_students=recent_students,
            upcoming_exams=upcoming_exams,


            # -------------------------------------------------
            # Filter Options
            # -------------------------------------------------

            academic_years=academic_years,
            courses=courses,


            # -------------------------------------------------
            # Selected Filters
            # -------------------------------------------------

            selected_month=month_number,

            selected_academic_year=academic_year,

            selected_academic_year_id=academic_year_id,

            selected_course=selected_course,

            selected_course_id=course_id
        )


    finally:

        cur.close()
        conn.close()