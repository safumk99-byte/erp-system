import os

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


def calculate_achievement_points(
    category,
    position,
    assigned_points=None
):

    points = 0

    if category == "Kithab":

        if position == "First":
            points = 5

        elif position == "Second":
            points = 4

        elif position == "Third":
            points = 3

    elif category == "Language":

        if position == "First":
            points = 5

        elif position == "Second":
            points = 4

        elif position == "Third":
            points = 3

    elif category == "Writing":

        if position == "First":
            points = 4

        elif position == "Second":
            points = 3

        elif position == "Third":
            points = 2

    elif category == "Presentation":

        if position == "First":
            points = 3

        elif position == "Second":
            points = 2

        elif position == "Third":
            points = 1

    elif category == "Others":

        if assigned_points is not None:

            try:
                points = float(
                    assigned_points
                )

            except (
                TypeError,
                ValueError
            ):

                points = 0

    return points


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
        "certificates"
    )

    os.makedirs(
        certificate_folder,
        exist_ok=True
    )

    import uuid

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
        "certificates",
        unique_name
    ).replace("\\", "/")


def list_achievements():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            a.*,
            s.full_name,
            s.admission_no

        FROM achievements a

        JOIN students s
            ON a.student_id = s.id

        WHERE
            a.institution_id = %s

        ORDER BY a.id DESC
    """, (
        session["institution_id"],
    ))

    achievements = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "achievement/list.html",
        achievements=achievements
    )


def add_achievement():

    conn = get_connection()
    cur = conn.cursor()

    students = get_students(cur)

    if request.method == "POST":

        student_id = request.form[
            "student_id"
        ]

        event_name = request.form.get(
            "event_name",
            ""
        ).strip()

        category = request.form[
            "achievement_type"
        ]

        position = request.form.get(
            "position"
        )

        title = request.form[
            "title"
        ].strip()

        issuing_organization = request.form.get(
            "issuing_organization",
            ""
        ).strip()

        achievement_date = request.form.get(
            "achievement_date"
        )

        certificate_number = request.form.get(
            "certificate_number",
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

        assigned_points = request.form.get(
            "assigned_points"
        )

        certificate_file = request.files.get(
            "certificate_file"
        )

        if not event_name:

            flash(
                "Event name is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "achievement/add.html",
                students=students
            )

        if not title:

            flash(
                "Achievement title is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "achievement/add.html",
                students=students
            )

        if category not in (
            "Kithab",
            "Language",
            "Writing",
            "Presentation",
            "Others"
        ):

            flash(
                "Invalid achievement category.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "achievement/add.html",
                students=students
            )

        if category != "Others":

            if position not in (
                "First",
                "Second",
                "Third"
            ):

                flash(
                    "Please select the achievement position.",
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "achievement/add.html",
                    students=students
                )

            assigned_points = None

        else:

            position = None

            if assigned_points is None or assigned_points == "":

                flash(
                    "Assigned points are required for Others.",
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "achievement/add.html",
                    students=students
                )

            try:

                assigned_points = float(
                    assigned_points
                )

            except (
                TypeError,
                ValueError
            ):

                flash(
                    "Invalid assigned points.",
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "achievement/add.html",
                    students=students
                )

            if assigned_points < 0:

                flash(
                    "Points cannot be negative.",
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "achievement/add.html",
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
                "achievement/add.html",
                students=students
            )

        cur.execute("""
            INSERT INTO achievements
            (
                institution_id,
                student_id,
                achievement_type,
                event_name,
                position,
                assigned_points,
                title,
                issuing_organization,
                achievement_date,
                certificate_number,
                verification_value,
                certificate_file,
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
                %s,
                0,
                0,
                'Pending'
            )
        """, (
            session["institution_id"],
            student_id,
            category,
            event_name,
            position,
            assigned_points,
            title,
            issuing_organization or None,
            achievement_date or None,
            certificate_number or None,
            verification_value or None,
            certificate_path,
            description
        ))

        conn.commit()

        cur.close()
        conn.close()

        flash(
            "Achievement added successfully.",
            "success"
        )

        return redirect(
            url_for(
                "achievement.achievement_list"
            )
        )

    cur.close()
    conn.close()

    return render_template(
        "achievement/add.html",
        students=students
    )


def edit_achievement(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM achievements

        WHERE
            id = %s
            AND institution_id = %s
            AND status = 'Pending'
    """, (
        id,
        session["institution_id"]
    ))

    achievement = cur.fetchone()

    if not achievement:

        cur.close()
        conn.close()

        flash(
            "Achievement not found or cannot be edited.",
            "error"
        )

        return redirect(
            url_for(
                "achievement.achievement_list"
            )
        )

    students = get_students(cur)

    if request.method == "POST":

        student_id = request.form[
            "student_id"
        ]

        event_name = request.form.get(
            "event_name",
            ""
        ).strip()

        category = request.form[
            "achievement_type"
        ]

        position = request.form.get(
            "position"
        )

        title = request.form[
            "title"
        ].strip()

        issuing_organization = request.form.get(
            "issuing_organization",
            ""
        ).strip()

        achievement_date = request.form.get(
            "achievement_date"
        )

        certificate_number = request.form.get(
            "certificate_number",
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

        assigned_points = request.form.get(
            "assigned_points"
        )

        certificate_file = request.files.get(
            "certificate_file"
        )

        if category not in (
            "Kithab",
            "Language",
            "Writing",
            "Presentation",
            "Others"
        ):

            flash(
                "Invalid achievement category.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "achievement/edit.html",
                achievement=achievement,
                students=students
            )

        if not event_name or not title:

            flash(
                "Event name and title are required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "achievement/edit.html",
                achievement=achievement,
                students=students
            )

        if category != "Others":

            if position not in (
                "First",
                "Second",
                "Third"
            ):

                flash(
                    "Please select the achievement position.",
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "achievement/edit.html",
                    achievement=achievement,
                    students=students
                )

            assigned_points = None

        else:

            position = None

            if assigned_points in (
                None,
                ""
            ):

                flash(
                    "Assigned points are required for Others.",
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "achievement/edit.html",
                    achievement=achievement,
                    students=students
                )

            try:

                assigned_points = float(
                    assigned_points
                )

            except (
                TypeError,
                ValueError
            ):

                flash(
                    "Invalid assigned points.",
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "achievement/edit.html",
                    achievement=achievement,
                    students=students
                )

        certificate_path = achievement[
            "certificate_file"
        ]

        if certificate_file and certificate_file.filename:

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
                    "achievement/edit.html",
                    achievement=achievement,
                    students=students
                )

        cur.execute("""
            UPDATE achievements

            SET
                student_id = %s,
                achievement_type = %s,
                event_name = %s,
                position = %s,
                assigned_points = %s,
                title = %s,
                issuing_organization = %s,
                achievement_date = %s,
                certificate_number = %s,
                verification_value = %s,
                certificate_file = %s,
                description = %s,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
                AND status = 'Pending'
        """, (
            student_id,
            category,
            event_name,
            position,
            assigned_points,
            title,
            issuing_organization or None,
            achievement_date or None,
            certificate_number or None,
            verification_value or None,
            certificate_path,
            description,
            id,
            session["institution_id"]
        ))

        conn.commit()

        cur.close()
        conn.close()

        flash(
            "Achievement updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "achievement.achievement_list"
            )
        )

    cur.close()
    conn.close()

    return render_template(
        "achievement/edit.html",
        achievement=achievement,
        students=students
    )


def approve_achievement(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            achievement_type,
            position,
            assigned_points,
            certificate_file

        FROM achievements

        WHERE
            id = %s
            AND institution_id = %s
            AND status = 'Pending'
    """, (
        id,
        session["institution_id"]
    ))

    achievement = cur.fetchone()

    if not achievement:

        cur.close()
        conn.close()

        flash(
            "Achievement not found or already reviewed.",
            "error"
        )

        return redirect(
            url_for(
                "achievement.achievement_list"
            )
        )

    category = achievement[
        "achievement_type"
    ]

    position = achievement[
        "position"
    ]

    assigned_points = achievement[
        "assigned_points"
    ]

    # Proposal-defined automatic scoring

    points = calculate_achievement_points(
        category,
        position,
        assigned_points
    )

    cur.execute("""
        UPDATE achievements

        SET
            status = 'Approved',
            points = %s,
            bonus_points = 0,
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
        f"Achievement approved. Points: {points}",
        "success"
    )

    return redirect(
        url_for(
            "achievement.achievement_list"
        )
    )


def reject_achievement(id):

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
                "achievement.achievement_list"
            )
        )

    cur.execute("""
        UPDATE achievements

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
        "Achievement rejected.",
        "success"
    )

    return redirect(
        url_for(
            "achievement.achievement_list"
        )
    )