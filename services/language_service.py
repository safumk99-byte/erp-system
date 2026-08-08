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


def add_language_skill():

    conn = get_connection()
    cur = conn.cursor()

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

    students = cur.fetchall()

    if request.method == "POST":

        student_id = request.form["student_id"]

        language_name = request.form[
            "language_name"
        ].strip()

        skill_type = request.form[
            "skill_type"
        ]

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

        # Duration validation

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

        # Pages validation

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

        points = 0
        bonus_points = 0

        cur.execute("""
            INSERT INTO language_skill_assessments
            (
                institution_id,
                student_id,
                language_name,
                skill_type,
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
                'Pending'
            )
        """, (
            session["institution_id"],
            student_id,
            language_name,
            skill_type,
            title,
            duration_minutes,
            pages,
            review,
            description,
            points,
            bonus_points
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

    students = cur.fetchall()

    if request.method == "POST":

        student_id = request.form["student_id"]

        language_name = request.form[
            "language_name"
        ].strip()

        skill_type = request.form[
            "skill_type"
        ]

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
    duration = assessment["duration_minutes"]
    pages = assessment["pages"]
    review = assessment["review"]

    points = 0
    bonus_points = 0

    # Presentation
    # Minimum 5 minutes = 5 points

    if skill_type == "Presentation":

        if duration and duration >= 5:
            points = 5

    # Hearing
    # Proposal: two 5-minute sessions
    # + written review = 3 points
    #
    # Since the current table stores one duration,
    # require 10 total minutes and a review.

    elif skill_type == "Hearing":

        if (
            duration
            and duration >= 10
            and review
        ):
            points = 3

    # Writing
    # Same scoring as Writing Section.
    #
    # Fiction = 3
    # Non-Fiction = 5 for 4 pages
    # +1 for every extra 2 pages
    #
    # The current table does not have a
    # Fiction/Non-Fiction field, so Writing
    # cannot yet distinguish those categories.

    elif skill_type == "Writing":

        points = 0

    # Reading
    # Same scoring as Reading Section.
    #
    # Fiction: 50 pages = 3
    # Non-Fiction: 25 pages = 5
    #
    # Category is not currently stored,
    # so calculation is left at 0.

    elif skill_type == "Reading":

        points = 0

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