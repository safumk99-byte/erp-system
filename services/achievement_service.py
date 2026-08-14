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
from services.notification_service import notify_student_and_parent


# =========================================================
# Constants
# =========================================================

ALLOWED_CERTIFICATE_EXTENSIONS = {
    "pdf",
    "jpg",
    "jpeg",
    "png"
}


ACHIEVEMENT_CATEGORIES = {
    "Kithab",
    "Language",
    "Writing",
    "Presentation",
    "Others"
}


POSITIONS = {
    "First",
    "Second",
    "Third"
}


# =========================================================
# Get Allowed Students
# =========================================================

def get_students(cur):

    role = session.get("role")

    # -----------------------------------------------------
    # Institution Admin
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Staff
    # -----------------------------------------------------

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
# Verify Student Access
# =========================================================

def _student_is_allowed(cur, student_id):

    role = session.get("role")

    # -----------------------------------------------------
    # Institution Admin
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Staff
    # -----------------------------------------------------

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
# Calculate Achievement Points
# =========================================================

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
        "certificates"
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
        "certificates",
        unique_name
    ).replace("\\", "/")


# =========================================================
# List Achievements
# =========================================================

def list_achievements():

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    # =====================================================
    # Base Query
    # =====================================================

    query = """
        SELECT
            a.*,
            s.full_name,
            s.admission_no

        FROM achievements a

        JOIN students s
            ON a.student_id = s.id

        WHERE
            a.institution_id = %s
            AND s.institution_id = %s
    """

    params = [
        session["institution_id"],
        session["institution_id"]
    ]


    # =====================================================
    # Staff Access Control
    # =====================================================

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
        ORDER BY a.id DESC
    """


    cur.execute(
        query,
        tuple(params)
    )

    achievements = cur.fetchall()

    cur.close()
    conn.close()


    return render_template(
        "achievement/list.html",
        achievements=achievements
    )


# =========================================================
# Add Achievement
# =========================================================

def add_achievement():

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")

    if role not in (
        "institution_admin",
        "staff"
    ):

        cur.close()
        conn.close()

        return "Unauthorized", 403


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


        # =============================================
        # Student Access
        # =============================================

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
                "achievement/add.html",
                students=students
            )


        # =============================================
        # Basic Validation
        # =============================================

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


        if category not in ACHIEVEMENT_CATEGORIES:

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


        # =============================================
        # Standard Categories
        # =============================================

        if category != "Others":

            if position not in POSITIONS:

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


        # =============================================
        # Others
        # =============================================

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


        # =============================================
        # Certificate
        # =============================================

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


        # =============================================
        # Insert Achievement
        # =============================================

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


    # =========================================================
    # Edit Achievement
    # =========================================================

def edit_achievement(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    if role not in (
        "institution_admin",
        "staff"
    ):

        cur.close()
        conn.close()

        return "Unauthorized", 403


    # =====================================================
    # Get Achievement + Verify Student Access
    # =====================================================

    if role == "institution_admin":

        cur.execute("""
            SELECT
                a.*

            FROM achievements a

            JOIN students s
                ON a.student_id = s.id

            WHERE
                a.id = %s
                AND a.institution_id = %s
                AND s.institution_id = %s
                AND a.status = 'Pending'
        """, (
            id,
            session["institution_id"],
            session["institution_id"]
        ))

    else:

        cur.execute("""
            SELECT
                a.*

            FROM achievements a

            JOIN students s
                ON a.student_id = s.id

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                a.id = %s
                AND a.institution_id = %s
                AND s.institution_id = %s
                AND a.status = 'Pending'

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


    achievement = cur.fetchone()


    if not achievement:

        cur.close()
        conn.close()

        flash(
            "Achievement not found or you do not have permission to edit it.",
            "error"
        )

        return redirect(
            url_for(
                "achievement.achievement_list"
            )
        )


    students = get_students(cur)


    # =====================================================
    # POST
    # =====================================================

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


        # =============================================
        # Verify New Student Access
        # =============================================

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
                "achievement/edit.html",
                achievement=achievement,
                students=students
            )


        # =============================================
        # Validation
        # =============================================

        if category not in ACHIEVEMENT_CATEGORIES:

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

            if position not in POSITIONS:

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


            if assigned_points < 0:

                flash(
                    "Points cannot be negative.",
                    "error"
                )

                cur.close()
                conn.close()

                return render_template(
                    "achievement/edit.html",
                    achievement=achievement,
                    students=students
                )


        # =============================================
        # Certificate
        # =============================================

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


        # =============================================
        # Update
        # =============================================

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


    # =====================================================
    # GET
    # =====================================================

    cur.close()
    conn.close()


    return render_template(
        "achievement/edit.html",
        achievement=achievement,
        students=students
    )


# =========================================================
# Approve Achievement
# =========================================================

def approve_achievement(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")
    institution_id = session.get("institution_id")
    user_id = session.get("user_id")


    if role not in (
        "institution_admin",
        "staff"
    ):

        cur.close()
        conn.close()

        return "Unauthorized", 403


    # =====================================================
    # Verify Achievement Access
    # =====================================================

    if role == "institution_admin":

        cur.execute("""
            SELECT
                a.student_id,
                a.achievement_type,
                a.position,
                a.assigned_points,
                a.certificate_file

            FROM achievements a

            JOIN students s
                ON a.student_id = s.id

            WHERE
                a.id = %s
                AND a.institution_id = %s
                AND s.institution_id = %s
                AND s.is_active = TRUE
                AND a.status = 'Pending'

            FOR UPDATE
        """, (
            id,
            institution_id,
            institution_id
        ))


    else:

        cur.execute("""
            SELECT
                a.student_id,
                a.achievement_type,
                a.position,
                a.assigned_points,
                a.certificate_file

            FROM achievements a

            JOIN students s
                ON a.student_id = s.id

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                a.id = %s
                AND a.institution_id = %s
                AND s.institution_id = %s
                AND s.is_active = TRUE
                AND a.status = 'Pending'

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


    achievement = cur.fetchone()


    if not achievement:

        cur.close()
        conn.close()

        flash(
            "Achievement not found or you do not have permission to approve it.",
            "error"
        )

        return redirect(
            url_for(
                "achievement.achievement_list"
            )
        )


    student_id = achievement[
        "student_id"
    ]


    # =====================================================
    # Calculate Points
    # =====================================================

    points = calculate_achievement_points(
        achievement["achievement_type"],
        achievement["position"],
        achievement["assigned_points"]
    )


    # =====================================================
    # Approve
    # =====================================================

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
        user_id,
        id,
        institution_id
    ))


    # =====================================================
    # Notification
    # =====================================================

    notify_student_and_parent(
        student_id=student_id,
        module_name="Achievement",
        approved=True,
        remarks=None,
        institution_id=institution_id,
        cur=cur
    )


    # =====================================================
    # Commit
    # =====================================================

    conn.commit()


    cur.close()
    conn.close()


    flash(
        f"Achievement approved. "
        f"Points: {points}. "
        f"Notification sent.",
        "success"
    )


    return redirect(
        url_for(
            "achievement.achievement_list"
        )
    )


# =========================================================
# Reject Achievement
# =========================================================

def reject_achievement(id):

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")
    institution_id = session.get("institution_id")
    user_id = session.get("user_id")


    if role not in (
        "institution_admin",
        "staff"
    ):

        cur.close()
        conn.close()

        return "Unauthorized", 403


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


    # =====================================================
    # Verify Achievement Access
    # =====================================================

    if role == "institution_admin":

        cur.execute("""
            SELECT
                a.id,
                a.student_id

            FROM achievements a

            JOIN students s
                ON a.student_id = s.id

            WHERE
                a.id = %s
                AND a.institution_id = %s
                AND s.institution_id = %s
                AND s.is_active = TRUE
                AND a.status = 'Pending'

            FOR UPDATE
        """, (
            id,
            institution_id,
            institution_id
        ))


    else:

        cur.execute("""
            SELECT
                a.id,
                a.student_id

            FROM achievements a

            JOIN students s
                ON a.student_id = s.id

            JOIN staff_classes sc
                ON sc.class_id = s.class_id

            WHERE
                a.id = %s
                AND a.institution_id = %s
                AND s.institution_id = %s
                AND s.is_active = TRUE
                AND a.status = 'Pending'

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


    achievement = cur.fetchone()


    if not achievement:

        cur.close()
        conn.close()

        flash(
            "Achievement not found or you do not have permission to reject it.",
            "error"
        )

        return redirect(
            url_for(
                "achievement.achievement_list"
            )
        )


    student_id = achievement[
        "student_id"
    ]


    # =====================================================
    # Reject
    # =====================================================

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
        user_id,
        reason,
        id,
        institution_id
    ))


    # =====================================================
    # Notification
    # =====================================================

    notify_student_and_parent(
        student_id=student_id,
        module_name="Achievement",
        approved=False,
        remarks=reason,
        institution_id=institution_id,
        cur=cur
    )


    # =====================================================
    # Commit
    # =====================================================

    conn.commit()


    cur.close()
    conn.close()


    flash(
        "Achievement rejected and notification sent.",
        "success"
    )


    return redirect(
        url_for(
            "achievement.achievement_list"
        )
    )