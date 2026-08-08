from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from database.db import get_connection


def list_publications():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            p.*,
            s.full_name,
            s.admission_no

        FROM publications p

        JOIN students s
            ON p.student_id = s.id

        WHERE
            p.institution_id = %s

        ORDER BY p.id DESC

    """, (
        session["institution_id"],
    ))

    publications = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "publication/list.html",
        publications=publications
    )


def add_publication():

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

        publication_type = request.form[
            "publication_type"
        ]

        title = request.form[
            "title"
        ].strip()

        category = request.form.get(
            "category"
        )

        pages = request.form.get(
            "pages"
        )

        publication_date = request.form.get(
            "publication_date"
        )

        isbn = request.form.get(
            "isbn",
            ""
        ).strip()

        verification_value = request.form.get(
            "verification_value",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        if not title:

            flash(
                "Publication title is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "publication/add.html",
                students=students
            )

        # Validate pages when provided

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
                    "publication/add.html",
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
                    "publication/add.html",
                    students=students
                )

        else:

            pages = None

        # Points are calculated
        # only after approval.

        points = 0
        bonus_points = 0

        cur.execute("""
            INSERT INTO publications
            (
                institution_id,
                student_id,
                publication_type,
                title,
                category,
                pages,
                publication_date,
                isbn,
                verification_value,
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
            publication_type,
            title,
            category or None,
            pages,
            publication_date or None,
            isbn or None,
            verification_value or None,
            description,
            points,
            bonus_points
        ))

        conn.commit()

        cur.close()
        conn.close()

        flash(
            "Publication added successfully.",
            "success"
        )

        return redirect(
            url_for(
                "publication.publication_list"
            )
        )

    cur.close()
    conn.close()

    return render_template(
        "publication/add.html",
        students=students
    )


def approve_publication(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            publication_type,
            category,
            pages

        FROM publications

        WHERE
            id = %s
            AND institution_id = %s
            AND status = 'Pending'

    """, (
        id,
        session["institution_id"]
    ))

    publication = cur.fetchone()

    if not publication:

        cur.close()
        conn.close()

        flash(
            "Publication not found or already reviewed.",
            "error"
        )

        return redirect(
            url_for(
                "publication.publication_list"
            )
        )

    publication_type = publication[
        "publication_type"
    ]

    category = publication[
        "category"
    ]

    pages = publication[
        "pages"
    ]

    points = 0

    # Article:
    # Proposal says article points are
    # identical to Writing Assessment.
    #
    # Fiction Article = 3
    # Non-Fiction = 5 for 4 pages
    # +1 for every additional 2 pages

    if publication_type == "Article":

        if category == "Fiction":

            if pages and pages >= 1:
                points = 3

        elif category == "Non-Fiction":

            if pages and pages >= 4:

                points = 5

                extra_pages = pages - 4

                points += (
                    extra_pages // 2
                )

    # Book:
    # 50 pages = base points.
    #
    # Non-Fiction = 20
    # Fiction = 15
    #
    # Proposal does not specify
    # extra-page calculation for books,
    # so no extra-page points are added.

    elif publication_type == "Book":

        if pages and pages >= 50:

            if category == "Non-Fiction":

                points = 20

            elif category == "Fiction":

                points = 15

    # ISBN / verification bonus value
    # is not numerically defined in the proposal.
    # Therefore bonus remains 0 for now.

    bonus_points = 0

    total_points = points + bonus_points

    cur.execute("""
        UPDATE publications

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
        f"Publication approved. "
        f"Points: {total_points}",
        "success"
    )

    return redirect(
        url_for(
            "publication.publication_list"
        )
    )


def reject_publication(id):

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
                "publication.publication_list"
            )
        )

    cur.execute("""
        UPDATE publications

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
        "Publication rejected.",
        "success"
    )

    return redirect(
        url_for(
            "publication.publication_list"
        )
    )
    
def edit_publication(id):

    conn = get_connection()
    cur = conn.cursor()

    # Get existing pending publication
    cur.execute("""
        SELECT *
        FROM publications

        WHERE
            id = %s
            AND institution_id = %s
            AND status = 'Pending'

    """, (
        id,
        session["institution_id"]
    ))

    publication = cur.fetchone()

    if not publication:

        cur.close()
        conn.close()

        flash(
            "Publication not found or cannot be edited.",
            "error"
        )

        return redirect(
            url_for(
                "publication.publication_list"
            )
        )

    # Students
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

        publication_type = request.form[
            "publication_type"
        ]

        title = request.form[
            "title"
        ].strip()

        category = request.form.get(
            "category"
        )

        pages = request.form.get(
            "pages"
        )

        publication_date = request.form.get(
            "publication_date"
        )

        isbn = request.form.get(
            "isbn",
            ""
        ).strip()

        verification_value = request.form.get(
            "verification_value",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        if not title:

            flash(
                "Publication title is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "publication/edit.html",
                publication=publication,
                students=students
            )

        # Validate pages

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
                    "publication/edit.html",
                    publication=publication,
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
                    "publication/edit.html",
                    publication=publication,
                    students=students
                )

        else:

            pages = None

        cur.execute("""
            UPDATE publications

            SET
                student_id = %s,
                publication_type = %s,
                title = %s,
                category = %s,
                pages = %s,
                publication_date = %s,
                isbn = %s,
                verification_value = %s,
                description = %s,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
                AND status = 'Pending'

        """, (
            student_id,
            publication_type,
            title,
            category or None,
            pages,
            publication_date or None,
            isbn or None,
            verification_value or None,
            description,
            id,
            session["institution_id"]
        ))

        conn.commit()

        cur.close()
        conn.close()

        flash(
            "Publication updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "publication.publication_list"
            )
        )

    cur.close()
    conn.close()

    return render_template(
        "publication/edit.html",
        publication=publication,
        students=students
    )    