import os
import uuid

from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
    current_app
)

from werkzeug.utils import secure_filename

from database.db import get_connection


ALLOWED_CERTIFICATE_EXTENSIONS = {
    "pdf",
    "jpg",
    "jpeg",
    "png"
}


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
# Calculate Paper Points
# =========================================================

def calculate_paper_points(level):

    if level == "State":
        return 8

    elif level == "National":
        return 10

    elif level == "International":
        return 20

    elif level == "Others":
        return 5

    return 0


# =========================================================
# Save Certificate
# =========================================================

def save_certificate(file):

    if not file:
        return None

    if not file.filename:
        return None

    filename = secure_filename(
        file.filename
    )

    if not filename:
        return None

    extension = (
        filename.rsplit(".", 1)[-1].lower()
        if "." in filename
        else ""
    )

    if extension not in ALLOWED_CERTIFICATE_EXTENSIONS:

        raise ValueError(
            "Invalid certificate file type."
        )

    upload_folder = current_app.config.get(
        "UPLOAD_FOLDER",
        "uploads"
    )

    certificate_folder = os.path.join(
        upload_folder,
        "paper_presentations"
    )

    os.makedirs(
        certificate_folder,
        exist_ok=True
    )

    unique_name = (
        str(uuid.uuid4())
        + "."
        + extension
    )

    file_path = os.path.join(
        certificate_folder,
        unique_name
    )

    file.save(file_path)

    return os.path.join(
        "paper_presentations",
        unique_name
    ).replace("\\", "/")


# =========================================================
# List Paper Presentations
# =========================================================

def list_paper_presentations():

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")

    query = """
        SELECT
            p.*,
            s.full_name,
            s.admission_no

        FROM paper_presentations p

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

    presentations = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "paper_presentation/list.html",
        presentations=presentations
    )


# =========================================================
# Add Paper Presentation
# =========================================================

def add_paper_presentation():

    conn = get_connection()
    cur = conn.cursor()

    students = get_students(cur)


    if request.method == "POST":

        student_id = request.form[
            "student_id"
        ]

        topic = request.form.get(
            "topic",
            ""
        ).strip()

        presentation_level = request.form.get(
            "presentation_level"
        )

        affiliated_institution = request.form.get(
            "affiliated_institution",
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

        certificate_file = request.files.get(
            "certificate_file"
        )


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
                "paper_presentation/add.html",
                students=students
            )


        if not topic:

            flash(
                "Topic is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "paper_presentation/add.html",
                students=students
            )


        if presentation_level not in (
            "State",
            "National",
            "International",
            "Others"
        ):

            flash(
                "Please select a valid presentation level.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "paper_presentation/add.html",
                students=students
            )


        # -------------------------------------------------
        # Others requires affiliation
        # -------------------------------------------------

        if (
            presentation_level == "Others"
            and not affiliated_institution
        ):

            flash(
                "Affiliated university/college is required for Others.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "paper_presentation/add.html",
                students=students
            )


        try:

            certificate_path = save_certificate(
                certificate_file
            )

        except ValueError as error:

            flash(
                str(error),
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "paper_presentation/add.html",
                students=students
            )


        cur.execute("""
            INSERT INTO paper_presentations
            (
                institution_id,
                student_id,
                topic,
                presentation_level,
                affiliated_institution,
                certificate_file,
                verification_value,
                description,
                points,
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
                0,
                'Pending'
            )
        """, (
            session["institution_id"],
            student_id,
            topic,
            presentation_level,
            affiliated_institution or None,
            certificate_path,
            verification_value or None,
            description
        ))


        conn.commit()

        cur.close()
        conn.close()


        flash(
            "Paper presentation added successfully.",
            "success"
        )


        return redirect(
            url_for(
                "paper_presentation.paper_presentation_list"
            )
        )


    cur.close()
    conn.close()


    return render_template(
        "paper_presentation/add.html",
        students=students
    )


# =========================================================
# Edit Paper Presentation
# =========================================================

def edit_paper_presentation(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    # -----------------------------------------------------
    # Get Existing Presentation
    # -----------------------------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT
                p.*

            FROM paper_presentations p

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

            FROM paper_presentations p

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


    presentation = cur.fetchone()


    if not presentation:

        cur.close()
        conn.close()

        flash(
            "Paper presentation not found or cannot be edited.",
            "error"
        )

        return redirect(
            url_for(
                "paper_presentation.paper_presentation_list"
            )
        )


    students = get_students(cur)


    if request.method == "POST":

        student_id = request.form[
            "student_id"
        ]

        topic = request.form.get(
            "topic",
            ""
        ).strip()

        presentation_level = request.form.get(
            "presentation_level"
        )

        affiliated_institution = request.form.get(
            "affiliated_institution",
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

        certificate_file = request.files.get(
            "certificate_file"
        )


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
                "paper_presentation/edit.html",
                presentation=presentation,
                students=students
            )


        if not topic:

            flash(
                "Topic is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "paper_presentation/edit.html",
                presentation=presentation,
                students=students
            )


        if presentation_level not in (
            "State",
            "National",
            "International",
            "Others"
        ):

            flash(
                "Please select a valid presentation level.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "paper_presentation/edit.html",
                presentation=presentation,
                students=students
            )


        if (
            presentation_level == "Others"
            and not affiliated_institution
        ):

            flash(
                "Affiliated university/college is required for Others.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "paper_presentation/edit.html",
                presentation=presentation,
                students=students
            )


        certificate_path = presentation[
            "certificate_file"
        ]


        if (
            certificate_file
            and certificate_file.filename
        ):

            try:

                certificate_path = save_certificate(
                    certificate_file
                )

            except ValueError as error:

                flash(
                    str(error),
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "paper_presentation/edit.html",
                    presentation=presentation,
                    students=students
                )


        cur.execute("""
            UPDATE paper_presentations

            SET
                student_id = %s,
                topic = %s,
                presentation_level = %s,
                affiliated_institution = %s,
                certificate_file = %s,
                verification_value = %s,
                description = %s,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
                AND status = 'Pending'

        """, (
            student_id,
            topic,
            presentation_level,
            affiliated_institution or None,
            certificate_path,
            verification_value or None,
            description,
            id,
            session["institution_id"]
        ))


        conn.commit()

        cur.close()
        conn.close()


        flash(
            "Paper presentation updated successfully.",
            "success"
        )


        return redirect(
            url_for(
                "paper_presentation.paper_presentation_list"
            )
        )


    cur.close()
    conn.close()


    return render_template(
        "paper_presentation/edit.html",
        presentation=presentation,
        students=students
    )
    
def approve_paper_presentation(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")

    # ---------------------------------
    # Verify presentation access
    # ---------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT
                p.presentation_level,
                p.affiliated_institution

            FROM paper_presentations p

            WHERE
                p.id = %s
                AND p.institution_id = %s
                AND p.status = 'Pending'
        """, (
            id,
            session["institution_id"]
        ))

    elif role == "staff":

        cur.execute("""
            SELECT
                p.presentation_level,
                p.affiliated_institution

            FROM paper_presentations p

            JOIN students s
                ON p.student_id = s.id

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                p.id = %s
                AND p.institution_id = %s

                AND s.institution_id = %s
                AND s.is_active = TRUE

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

                AND p.status = 'Pending'
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


    presentation = cur.fetchone()


    if not presentation:

        cur.close()
        conn.close()

        flash(
            "Paper presentation not found or you do not have permission.",
            "error"
        )

        return redirect(
            url_for(
                "paper_presentation.paper_presentation_list"
            )
        )


    level = presentation[
        "presentation_level"
    ]

    affiliated_institution = presentation[
        "affiliated_institution"
    ]


    # ---------------------------------
    # Others requires affiliation
    # ---------------------------------

    if (
        level == "Others"
        and not affiliated_institution
    ):

        flash(
            "Affiliated university/college is required for Others.",
            "error"
        )

        cur.close()
        conn.close()

        return redirect(
            url_for(
                "paper_presentation.paper_presentation_list"
            )
        )


    # ---------------------------------
    # Calculate points
    # ---------------------------------

    points = calculate_paper_points(
        level
    )


    # ---------------------------------
    # Approve
    # ---------------------------------

    cur.execute("""
        UPDATE paper_presentations

        SET
            status = 'Approved',
            points = %s,
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
        session.get("user_id"),
        id,
        session["institution_id"]
    ))


    conn.commit()

    cur.close()
    conn.close()


    flash(
        f"Paper presentation approved. Points: {points}",
        "success"
    )


    return redirect(
        url_for(
            "paper_presentation.paper_presentation_list"
        )
    )
    
def reject_paper_presentation(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")

    reason = request.form.get(
        "rejection_reason",
        ""
    ).strip()


    # ---------------------------------
    # Validate rejection reason
    # ---------------------------------

    if not reason:

        cur.close()
        conn.close()

        flash(
            "Rejection reason is required.",
            "error"
        )

        return redirect(
            url_for(
                "paper_presentation.paper_presentation_list"
            )
        )


    # ---------------------------------
    # Verify presentation access
    # ---------------------------------

    if role == "institution_admin":

        cur.execute("""
            SELECT
                p.id

            FROM paper_presentations p

            WHERE
                p.id = %s
                AND p.institution_id = %s
                AND p.status = 'Pending'
        """, (
            id,
            session["institution_id"]
        ))

    elif role == "staff":

        cur.execute("""
            SELECT
                p.id

            FROM paper_presentations p

            JOIN students s
                ON p.student_id = s.id

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                p.id = %s
                AND p.institution_id = %s

                AND s.institution_id = %s
                AND s.is_active = TRUE

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

                AND p.status = 'Pending'
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


    presentation = cur.fetchone()


    if not presentation:

        cur.close()
        conn.close()

        flash(
            "Paper presentation not found or you do not have permission.",
            "error"
        )

        return redirect(
            url_for(
                "paper_presentation.paper_presentation_list"
            )
        )


    # ---------------------------------
    # Reject
    # ---------------------------------

    cur.execute("""
        UPDATE paper_presentations

        SET
            status = 'Rejected',
            points = 0,
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
        "Paper presentation rejected.",
        "success"
    )


    return redirect(
        url_for(
            "paper_presentation.paper_presentation_list"
        )
    )        