from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from database.db import get_connection
from services.notification_service import notify_student_and_parent


# =========================================================
# Student Access Helper
# =========================================================

def _student_is_allowed(cur, student_id):

    role = session.get("role")

    if role == "institution_admin":

        cur.execute("""
            SELECT
                id

            FROM students

            WHERE
                id = %s
                AND institution_id = %s
                AND is_active = TRUE
        """, (
            student_id,
            session["institution_id"]
        ))

    elif role == "staff":

        cur.execute("""
            SELECT
                s.id

            FROM students s

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                s.id = %s
                AND s.institution_id = %s
                AND s.is_active = TRUE

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE
        """, (
            student_id,
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

    else:

        return False

    return cur.fetchone() is not None


# =========================================================
# Get Students
# =========================================================

def get_students(cur):

    role = session.get("role")

    if role == "institution_admin":

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

    elif role == "staff":

        cur.execute("""
            SELECT DISTINCT
                s.id,
                s.admission_no,
                s.full_name

            FROM students s

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                s.institution_id = %s
                AND s.is_active = TRUE

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

            ORDER BY s.full_name
        """, (
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

    else:

        return []

    return cur.fetchall()


# =========================================================
# List Publications
# =========================================================

def list_publications():

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")

    query = """
        SELECT
            p.*,
            s.full_name,
            s.admission_no

        FROM publications p

        JOIN students s
            ON p.student_id = s.id

        WHERE
            p.institution_id = %s
            AND s.institution_id = %s
    """

    params = [
        session["institution_id"],
        session["institution_id"]
    ]


    # -----------------------------------------------------
    # Staff → Assigned Students Only
    # -----------------------------------------------------

    if role == "staff":

        query += """
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

        params.extend([
            session["institution_id"],
            session["user_id"]
        ])


    query += """
        ORDER BY p.id DESC
    """


    cur.execute(
        query,
        tuple(params)
    )

    publications = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "publication/list.html",
        publications=publications
    )


# =========================================================
# Add Publication
# =========================================================

def add_publication():

    conn = get_connection()
    cur = conn.cursor()

    students = get_students(cur)


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


        # -------------------------------------------------
        # Verify Student Access
        # -------------------------------------------------

        if not _student_is_allowed(
            cur,
            student_id
        ):

            flash(
                "You do not have access to this student.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "publication/add.html",
                students=students
            )


        # -------------------------------------------------
        # Title Validation
        # -------------------------------------------------

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


        # -------------------------------------------------
        # Validate Pages
        # -------------------------------------------------

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


        # -------------------------------------------------
        # Points
        # -------------------------------------------------

        points = 0
        bonus_points = 0


        # -------------------------------------------------
        # Insert
        # -------------------------------------------------

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


# =========================================================
# Approve Publication
# =========================================================

def approve_publication(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")
    institution_id = session.get("institution_id")
    user_id = session.get("user_id")


    # -----------------------------------------------------
    # Verify Publication + Student Access
    # -----------------------------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT
                p.student_id,
                p.publication_type,
                p.category,
                p.pages

            FROM publications p

            JOIN students s
                ON p.student_id = s.id

            WHERE
                p.id = %s
                AND p.institution_id = %s
                AND s.institution_id = %s
                AND p.status = 'Pending'

            FOR UPDATE
        """, (
            id,
            institution_id,
            institution_id
        ))


    elif role == "staff":

        cur.execute("""
            SELECT
                p.student_id,
                p.publication_type,
                p.category,
                p.pages

            FROM publications p

            JOIN students s
                ON p.student_id = s.id

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                p.id = %s
                AND p.institution_id = %s
                AND s.institution_id = %s
                AND p.status = 'Pending'

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

            FOR UPDATE
        """, (
            id,
            institution_id,
            institution_id,
            institution_id,
            user_id
        ))


    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    publication = cur.fetchone()


    if not publication:

        cur.close()
        conn.close()

        flash(
            "Publication not found or you do not have permission to approve it.",
            "error"
        )

        return redirect(
            url_for(
                "publication.publication_list"
            )
        )


    student_id = publication[
        "student_id"
    ]

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


    # -----------------------------------------------------
    # Article
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # Book
    # -----------------------------------------------------

    elif publication_type == "Book":

        if pages and pages >= 50:

            if category == "Non-Fiction":

                points = 20

            elif category == "Fiction":

                points = 15


    # -----------------------------------------------------
    # Bonus
    # -----------------------------------------------------

    bonus_points = 0


    total_points = (
        points
        + bonus_points
    )


    # -----------------------------------------------------
    # Update Publication
    # -----------------------------------------------------

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
        user_id,
        id,
        institution_id
    ))


    # -----------------------------------------------------
    # Notification
    # -----------------------------------------------------

    notify_student_and_parent(
        student_id=student_id,
        module_name="Publication",
        approved=True,
        remarks=None,
        institution_id=institution_id,
        cur=cur
    )


    # -----------------------------------------------------
    # Commit
    # -----------------------------------------------------

    conn.commit()


    cur.close()
    conn.close()


    flash(
        f"Publication approved. "
        f"Points: {total_points}. "
        f"Notification sent.",
        "success"
    )


    return redirect(
        url_for(
            "publication.publication_list"
        )
    )


# =========================================================
# Reject Publication
# =========================================================

def reject_publication(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")
    institution_id = session.get("institution_id")
    user_id = session.get("user_id")


    reason = request.form.get(
        "rejection_reason",
        ""
    ).strip()


    # -----------------------------------------------------
    # Validate Reason
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # Verify Publication + Student Access
    # -----------------------------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT
                p.id,
                p.student_id

            FROM publications p

            JOIN students s
                ON p.student_id = s.id

            WHERE
                p.id = %s
                AND p.institution_id = %s
                AND s.institution_id = %s
                AND p.status = 'Pending'

            FOR UPDATE
        """, (
            id,
            institution_id,
            institution_id
        ))


    elif role == "staff":

        cur.execute("""
            SELECT
                p.id,
                p.student_id

            FROM publications p

            JOIN students s
                ON p.student_id = s.id

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                p.id = %s
                AND p.institution_id = %s
                AND s.institution_id = %s
                AND p.status = 'Pending'

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

            FOR UPDATE
        """, (
            id,
            institution_id,
            institution_id,
            institution_id,
            user_id
        ))


    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    publication = cur.fetchone()


    if not publication:

        cur.close()
        conn.close()

        flash(
            "Publication not found or you do not have permission to reject it.",
            "error"
        )

        return redirect(
            url_for(
                "publication.publication_list"
            )
        )


    student_id = publication[
        "student_id"
    ]


    # -----------------------------------------------------
    # Reject Publication
    # -----------------------------------------------------

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
        user_id,
        reason,
        id,
        institution_id
    ))


    # -----------------------------------------------------
    # Notification
    # -----------------------------------------------------

    notify_student_and_parent(
        student_id=student_id,
        module_name="Publication",
        approved=False,
        remarks=reason,
        institution_id=institution_id,
        cur=cur
    )


    # -----------------------------------------------------
    # Commit
    # -----------------------------------------------------

    conn.commit()


    cur.close()
    conn.close()


    flash(
        "Publication rejected and notification sent.",
        "success"
    )


    return redirect(
        url_for(
            "publication.publication_list"
        )
    )


# =========================================================
# Edit Publication
# =========================================================

def edit_publication(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    # -----------------------------------------------------
    # Get Existing Publication
    # -----------------------------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT
                p.*

            FROM publications p

            JOIN students s
                ON p.student_id = s.id

            WHERE
                p.id = %s
                AND p.institution_id = %s
                AND s.institution_id = %s
                AND p.status = 'Pending'
        """, (
            id,
            session["institution_id"],
            session["institution_id"]
        ))

    elif role == "staff":

        cur.execute("""
            SELECT
                p.*

            FROM publications p

            JOIN students s
                ON p.student_id = s.id

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                p.id = %s
                AND p.institution_id = %s
                AND s.institution_id = %s
                AND p.status = 'Pending'

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE
        """, (
            id,
            session["institution_id"],
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


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


    # -----------------------------------------------------
    # Students
    # -----------------------------------------------------

    students = get_students(cur)


    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

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


        # -------------------------------------------------
        # Verify New Student Access
        # -------------------------------------------------

        if not _student_is_allowed(
            cur,
            student_id
        ):

            flash(
                "You do not have access to this student.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "publication/edit.html",
                publication=publication,
                students=students
            )


        # -------------------------------------------------
        # Title Validation
        # -------------------------------------------------

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


        # -------------------------------------------------
        # Validate Pages
        # -------------------------------------------------

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


        # -------------------------------------------------
        # Update
        # -------------------------------------------------

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