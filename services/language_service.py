from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from database.db import get_connection


def list_language_skills():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            l.*,
            s.full_name,
            s.admission_no
        FROM language_skill_assessments l
        JOIN students s
            ON l.student_id = s.id
        WHERE l.institution_id = %s
        ORDER BY l.id DESC
    """, (
        session["institution_id"],
    ))

    assessments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "language/list.html",
        assessments=assessments
    )


def get_students(cur):

    cur.execute("""
        SELECT
            id,
            admission_no,
            full_name
        FROM students
        WHERE
            institution_id = %s
            AND is_active = TRUE
        ORDER BY full_name
    """, (
        session["institution_id"],
    ))

    return cur.fetchall()


def add_language_skill():

    conn = get_connection()
    cur = conn.cursor()

    students = get_students(cur)

    if request.method == "POST":

        student_id = request.form["student_id"]

        language_name = request.form[
            "language_name"
        ].strip()

        skill_type = request.form[
            "skill_type"
        ]

        category = request.form.get(
            "category"
        ) or None

        title = request.form.get(
            "title",
            ""
        ).strip()

        duration_minutes = request.form.get(
            "duration_minutes"
        )

        pages = request.form.get(
            "pages"
        )

        review = request.form.get(
            "review",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        # Category is required only for
        # Reading and Writing

        if skill_type in (
            "Reading",
            "Writing"
        ) and category not in (
            "Fiction",
            "Non-Fiction"
        ):

            flash(
                "Please select Fiction or Non-Fiction.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "language/add.html",
                students=students
            )

        # Category is not required for
        # Presentation / Hearing

        if skill_type in (
            "Presentation",
            "Hearing"
        ):

            category = None

        if not language_name:

            flash(
                "Language name is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "language/add.html",
                students=students
            )

        # Duration

        if duration_minutes:

            try:

                duration_minutes = int(
                    duration_minutes
                )

            except (TypeError, ValueError):

                flash(
                    "Invalid duration.",
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "language/add.html",
                    students=students
                )

            if duration_minutes <= 0:

                flash(
                    "Duration must be greater than zero.",
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "language/add.html",
                    students=students
                )

        else:

            duration_minutes = None

        # Pages

        if pages:

            try:

                pages = int(pages)

            except (TypeError, ValueError):

                flash(
                    "Invalid page count.",
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "language/add.html",
                    students=students
                )

            if pages <= 0:

                flash(
                    "Pages must be greater than zero.",
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "language/add.html",
                    students=students
                )

        else:

            pages = None

        cur.execute("""
            INSERT INTO language_skill_assessments
            (
                institution_id,
                student_id,
                language_name,
                skill_type,
                category,
                title,
                duration_minutes,
                pages,
                review,
                description,
                points,
                bonus_points,
                status
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
                %s,
                %s,
                %s,
                %s,
                %s,
                'Pending'
            )
        """, (
            session["institution_id"],
            student_id,
            language_name,
            skill_type,
            category,
            title,
            duration_minutes,
            pages,
            review,
            description,
            0,
            0
        ))

        conn.commit()

        cur.close()
        conn.close()

        flash(
            "Language skill assessment added successfully.",
            "success"
        )

        return redirect(
            url_for(
                "language.language_list"
            )
        )

    cur.close()
    conn.close()

    return render_template(
        "language/add.html",
        students=students
    )


def edit_language_skill(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM language_skill_assessments

        WHERE
            id = %s
            AND institution_id = %s
            AND status = 'Pending'
    """, (
        id,
        session["institution_id"]
    ))

    assessment = cur.fetchone()

    if not assessment:

        cur.close()
        conn.close()

        flash(
            "Language assessment not found or cannot be edited.",
            "error"
        )

        return redirect(
            url_for(
                "language.language_list"
            )
        )

    students = get_students(cur)

    if request.method == "POST":

        student_id = request.form["student_id"]

        language_name = request.form[
            "language_name"
        ].strip()

        skill_type = request.form[
            "skill_type"
        ]

        category = request.form.get(
            "category"
        ) or None

        title = request.form.get(
            "title",
            ""
        ).strip()

        duration_minutes = request.form.get(
            "duration_minutes"
        )

        pages = request.form.get(
            "pages"
        )

        review = request.form.get(
            "review",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        if skill_type in (
            "Reading",
            "Writing"
        ) and category not in (
            "Fiction",
            "Non-Fiction"
        ):

            flash(
                "Please select Fiction or Non-Fiction.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "language/edit.html",
                assessment=assessment,
                students=students
            )

        if skill_type in (
            "Presentation",
            "Hearing"
        ):

            category = None

        if not language_name:

            flash(
                "Language name is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "language/edit.html",
                assessment=assessment,
                students=students
            )

        if duration_minutes:

            try:

                duration_minutes = int(
                    duration_minutes
                )

            except (TypeError, ValueError):

                flash(
                    "Invalid duration.",
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "language/edit.html",
                    assessment=assessment,
                    students=students
                )

            if duration_minutes <= 0:

                flash(
                    "Duration must be greater than zero.",
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "language/edit.html",
                    assessment=assessment,
                    students=students
                )

        else:

            duration_minutes = None

        if pages:

            try:

                pages = int(pages)

            except (TypeError, ValueError):

                flash(
                    "Invalid page count.",
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "language/edit.html",
                    assessment=assessment,
                    students=students
                )

            if pages <= 0:

                flash(
                    "Pages must be greater than zero.",
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "language/edit.html",
                    assessment=assessment,
                    students=students
                )

        else:

            pages = None

        cur.execute("""
            UPDATE language_skill_assessments

            SET
                student_id = %s,
                language_name = %s,
                skill_type = %s,
                category = %s,
                title = %s,
                duration_minutes = %s,
                pages = %s,
                review = %s,
                description = %s,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
                AND status = 'Pending'
        """, (
            student_id,
            language_name,
            skill_type,
            category,
            title,
            duration_minutes,
            pages,
            review,
            description,
            id,
            session["institution_id"]
        ))

        conn.commit()

        cur.close()
        conn.close()

        flash(
            "Language skill assessment updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "language.language_list"
            )
        )

    cur.close()
    conn.close()

    return render_template(
        "language/edit.html",
        assessment=assessment,
        students=students
    )


def approve_language_skill(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            skill_type,
            category,
            duration_minutes,
            pages,
            review

        FROM language_skill_assessments

        WHERE
            id = %s
            AND institution_id = %s
            AND status = 'Pending'
    """, (
        id,
        session["institution_id"]
    ))

    assessment = cur.fetchone()

    if not assessment:

        cur.close()
        conn.close()

        flash(
            "Language assessment not found or already reviewed.",
            "error"
        )

        return redirect(
            url_for(
                "language.language_list"
            )
        )

    skill_type = assessment["skill_type"]
    category = assessment["category"]
    duration = assessment["duration_minutes"]
    pages = assessment["pages"]
    review = assessment["review"]

    points = 0
    bonus_points = 0

    # --------------------------------
    # PRESENTATION
    # Minimum 5 minutes = 5 points
    # --------------------------------

    if skill_type == "Presentation":

        if duration and duration >= 5:

            points = 5

    # --------------------------------
    # HEARING
    # Two 5-minute sessions
    # + written review = 3 points
    # --------------------------------

    elif skill_type == "Hearing":

        if (
            duration
            and duration >= 10
            and review
        ):

            points = 3

    # --------------------------------
    # WRITING
    # Same scoring structure
    # as Writing Assessment
    # --------------------------------

    elif skill_type == "Writing":

        if category == "Fiction":

            # Writing fiction base
            points = 3

        elif category == "Non-Fiction":

            if pages and pages >= 4:

                points = 5

                extra_pages = pages - 4

                points += (
                    extra_pages // 2
                )

    # --------------------------------
    # READING
    # Same scoring structure
    # as Reading Assessment
    # --------------------------------

    elif skill_type == "Reading":

        if category == "Fiction":

            if pages and pages >= 50:

                points = 3

        elif category == "Non-Fiction":

            if pages and pages >= 25:

                points = 5

    # Bonus values are intentionally
    # kept at 0 because the proposal
    # does not define their numerical
    # values.

    bonus_points = 0

    cur.execute("""
        UPDATE language_skill_assessments

        SET
            status = 'Approved',
            points = %s,
            bonus_points = %s,
            reviewed_by = %s,
            reviewed_at = NOW(),
            rejection_reason = NULL,
            updated_at = NOW()

        WHERE
            id = %s
            AND institution_id = %s
            AND status = 'Pending'
    """, (
        points,
        bonus_points,
        session.get("user_id"),
        id,
        session["institution_id"]
    ))

    conn.commit()

    cur.close()
    conn.close()

    flash(
        f"Language assessment approved. Points: {points}",
        "success"
    )

    return redirect(
        url_for(
            "language.language_list"
        )
    )


def reject_language_skill(id):

    conn = get_connection()
    cur = conn.cursor()

    reason = request.form.get(
        "rejection_reason",
        ""
    ).strip()

    if not reason:

        flash(
            "Rejection reason is required.",
            "error"
        )

        cur.close()
        conn.close()

        return redirect(
            url_for(
                "language.language_list"
            )
        )

    cur.execute("""
        UPDATE language_skill_assessments

        SET
            status = 'Rejected',
            points = 0,
            bonus_points = 0,
            reviewed_by = %s,
            reviewed_at = NOW(),
            rejection_reason = %s,
            updated_at = NOW()

        WHERE
            id = %s
            AND institution_id = %s
            AND status = 'Pending'
    """, (
        session.get("user_id"),
        reason,
        id,
        session["institution_id"]
    ))

    conn.commit()

    cur.close()
    conn.close()

    flash(
        "Language assessment rejected.",
        "success"
    )

    return redirect(
        url_for(
            "language.language_list"
        )
    )