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


def list_paper_presentations():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            p.*,
            s.full_name,
            s.admission_no

        FROM paper_presentations p

        JOIN students s
            ON p.student_id = s.id

        WHERE
            p.institution_id = %s

        ORDER BY p.id DESC
    """, (
        session["institution_id"],
    ))

    presentations = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "paper_presentation/list.html",
        presentations=presentations
    )


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

        # Proposal specifically requires
        # recognized university/college affiliation
        # for Others.

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


def edit_paper_presentation(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM paper_presentations

        WHERE
            id = %s
            AND institution_id = %s
            AND status = 'Pending'
    """, (
        id,
        session["institution_id"]
    ))

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

    cur.execute("""
        SELECT
            presentation_level,
            affiliated_institution

        FROM paper_presentations

        WHERE
            id = %s
            AND institution_id = %s
            AND status = 'Pending'
    """, (
        id,
        session["institution_id"]
    ))

    presentation = cur.fetchone()

    if not presentation:

        cur.close()
        conn.close()

        flash(
            "Paper presentation not found or already reviewed.",
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

    points = calculate_paper_points(
        level
    )

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
                "paper_presentation.paper_presentation_list"
            )
        )

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