import os

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from dotenv import load_dotenv

import cloudinary
import cloudinary.uploader

from database.db import get_connection
from middleware.auth import login_required
from middleware.roles import role_required


load_dotenv()


# =========================================================
# Cloudinary
# =========================================================

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


# =========================================================
# Blueprint
# =========================================================

settings = Blueprint(
    "settings",
    __name__
)


# =========================================================
# Helpers
# =========================================================

def _institution_id():

    return session.get("institution_id")


def _user_id():

    return session.get("user_id")


# =========================================================
# Institution Settings
# =========================================================

@settings.route(
    "/settings",
    methods=["GET", "POST"]
)
@login_required
@role_required("institution_admin")
def institution_settings():

    institution_id = _institution_id()

    if not institution_id:

        flash(
            "Institution session not found.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )


    conn = get_connection()
    cur = conn.cursor()

    try:

        # =================================================
        # POST → Institution Profile
        # =================================================

        if request.method == "POST":

            name = request.form.get(
                "name",
                ""
            ).strip()

            admission_prefix = request.form.get(
                "admission_prefix",
                ""
            ).strip()

            email = request.form.get(
                "email",
                ""
            ).strip()

            phone = request.form.get(
                "phone",
                ""
            ).strip()

            address = request.form.get(
                "address",
                ""
            ).strip()

            city = request.form.get(
                "city",
                ""
            ).strip()

            state = request.form.get(
                "state",
                ""
            ).strip()

            country = request.form.get(
                "country",
                "India"
            ).strip()


            # ---------------------------------------------
            # Validation
            # ---------------------------------------------

            if not name:

                flash(
                    "Institution name is required.",
                    "error"
                )

                return redirect(
                    url_for(
                        "settings.institution_settings"
                    )
                )


            if len(name) > 255:

                flash(
                    "Institution name is too long.",
                    "error"
                )

                return redirect(
                    url_for(
                        "settings.institution_settings"
                    )
                )


            if len(admission_prefix) > 50:

                flash(
                    "Admission prefix is too long.",
                    "error"
                )

                return redirect(
                    url_for(
                        "settings.institution_settings"
                    )
                )


            if len(email) > 255:

                flash(
                    "Email address is too long.",
                    "error"
                )

                return redirect(
                    url_for(
                        "settings.institution_settings"
                    )
                )


            if len(phone) > 50:

                flash(
                    "Phone number is too long.",
                    "error"
                )

                return redirect(
                    url_for(
                        "settings.institution_settings"
                    )
                )


            # ---------------------------------------------
            # Update
            # ---------------------------------------------

            cur.execute(
                """
                UPDATE institutions

                SET
                    name = %s,
                    admission_prefix = %s,
                    email = %s,
                    phone = %s,
                    address = %s,
                    city = %s,
                    state = %s,
                    country = %s,
                    updated_at = NOW()

                WHERE
                    id = %s
                """,
                (
                    name,
                    admission_prefix or None,
                    email or None,
                    phone or None,
                    address or None,
                    city or None,
                    state or None,
                    country or None,
                    institution_id
                )
            )


            if cur.rowcount != 1:

                raise RuntimeError(
                    "Institution update failed."
                )


            conn.commit()


            flash(
                "Institution profile updated successfully.",
                "success"
            )


            return redirect(
                url_for(
                    "settings.institution_settings"
                )
            )


        # =================================================
        # GET → Institution
        # =================================================

        cur.execute(
            """
            SELECT
                id,
                name,
                code,
                email,
                phone,
                status,
                created_at,
                updated_at,
                address,
                city,
                state,
                country,
                logo,
                subscription_plan,
                subscription_start,
                subscription_end,
                admission_prefix

            FROM institutions

            WHERE id = %s

            LIMIT 1
            """,
            (institution_id,)
        )


        institution = cur.fetchone()


        if not institution:

            flash(
                "Institution not found.",
                "error"
            )

            return redirect(
                url_for("auth.login")
            )


        # =================================================
        # Current Admin Account
        # =================================================

        admin = None

        user_id = _user_id()


        if user_id:

            cur.execute(
                """
                SELECT
                    id,
                    full_name,
                    username,
                    email,
                    phone,
                    is_active

                FROM users

                WHERE
                    id = %s
                    AND institution_id = %s

                LIMIT 1
                """,
                (
                    user_id,
                    institution_id
                )
            )

            admin = cur.fetchone()


        return render_template(
            "settings/institution.html",
            institution=institution,
            admin=admin
        )


    except Exception as e:

        conn.rollback()

        print(
            "Institution settings error:",
            e
        )

        flash(
            "Unable to update institution settings.",
            "error"
        )

        return redirect(
            url_for(
                "settings.institution_settings"
            )
        )


    finally:

        cur.close()
        conn.close()


# =========================================================
# Logo Upload
# =========================================================

@settings.route(
    "/settings/logo",
    methods=["POST"]
)
@login_required
@role_required("institution_admin")
def update_logo():

    institution_id = _institution_id()

    if not institution_id:

        return "Unauthorized", 403


    logo = request.files.get("logo")


    if not logo or not logo.filename:

        flash(
            "Please select a logo image.",
            "error"
        )

        return redirect(
            url_for(
                "settings.institution_settings"
            )
        )


    allowed_extensions = {
        "jpg",
        "jpeg",
        "png",
        "webp"
    }


    extension = (
        logo.filename
        .rsplit(".", 1)[-1]
        .lower()
        if "." in logo.filename
        else ""
    )


    if extension not in allowed_extensions:

        flash(
            "Only JPG, JPEG, PNG and WEBP images are allowed.",
            "error"
        )

        return redirect(
            url_for(
                "settings.institution_settings"
            )
        )


    conn = None
    cur = None


    try:

        # =================================================
        # Upload to Cloudinary
        # =================================================

        public_id = (
            f"institution_{institution_id}_logo"
        )


        result = cloudinary.uploader.upload(

            logo,

            folder="alif-erp/institutions",

            public_id=public_id,

            resource_type="image",

            overwrite=True,

            invalidate=True,

            unique_filename=False

        )


        logo_url = result.get(
            "secure_url"
        )


        if not logo_url:

            raise RuntimeError(
                "Cloudinary did not return a logo URL."
            )


        # =================================================
        # Save URL to Database
        # =================================================

        conn = get_connection()
        cur = conn.cursor()


        cur.execute(
            """
            UPDATE institutions

            SET
                logo = %s,
                updated_at = NOW()

            WHERE
                id = %s
            """,
            (
                logo_url,
                institution_id
            )
        )


        if cur.rowcount != 1:

            raise RuntimeError(
                "Institution logo update failed."
            )


        conn.commit()


        flash(
            "Institution logo updated successfully.",
            "success"
        )


    except Exception as e:

        if conn:

            conn.rollback()


        print(
            "Logo upload error:",
            e
        )


        flash(
            "Unable to upload institution logo.",
            "error"
        )


    finally:

        if cur:

            cur.close()


        if conn:

            conn.close()


    return redirect(
        url_for(
            "settings.institution_settings"
        )
    )


# =========================================================
# Remove Logo
# =========================================================

@settings.route(
    "/settings/logo/remove",
    methods=["POST"]
)
@login_required
@role_required("institution_admin")
def remove_logo():

    institution_id = _institution_id()

    if not institution_id:

        return "Unauthorized", 403


    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            UPDATE institutions

            SET
                logo = NULL,
                updated_at = NOW()

            WHERE
                id = %s
            """,
            (institution_id,)
        )


        conn.commit()


        flash(
            "Institution logo removed.",
            "success"
        )


    except Exception:

        conn.rollback()

        flash(
            "Unable to remove institution logo.",
            "error"
        )


    finally:

        cur.close()
        conn.close()


    return redirect(
        url_for(
            "settings.institution_settings"
        )
    )


# =========================================================
# Admin Account
# =========================================================

@settings.route(
    "/settings/admin-account",
    methods=["POST"]
)
@login_required
@role_required("institution_admin")
def update_admin_account():

    institution_id = _institution_id()
    user_id = _user_id()


    if not institution_id or not user_id:

        return "Unauthorized", 403


    full_name = request.form.get(
        "full_name",
        ""
    ).strip()

    username = request.form.get(
        "username",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()


    if not full_name:

        flash(
            "Full name is required.",
            "error"
        )

        return redirect(
            url_for(
                "settings.institution_settings"
            )
        )


    if not username:

        flash(
            "Username is required.",
            "error"
        )

        return redirect(
            url_for(
                "settings.institution_settings"
            )
        )


    conn = get_connection()
    cur = conn.cursor()

    try:

        # ---------------------------------------------
        # Username uniqueness
        # ---------------------------------------------

        cur.execute(
            """
            SELECT id

            FROM users

            WHERE
                username = %s
                AND id <> %s

            LIMIT 1
            """,
            (
                username,
                user_id
            )
        )


        existing = cur.fetchone()


        if existing:

            flash(
                "Username is already in use.",
                "error"
            )

            return redirect(
                url_for(
                    "settings.institution_settings"
                )
            )


        # ---------------------------------------------
        # Update
        # ---------------------------------------------

        cur.execute(
            """
            UPDATE users

            SET
                full_name = %s,
                username = %s,
                email = %s,
                phone = %s,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
            """,
            (
                full_name,
                username,
                email or None,
                phone or None,
                user_id,
                institution_id
            )
        )


        if cur.rowcount != 1:

            raise RuntimeError(
                "Admin account update failed."
            )


        conn.commit()


        session["full_name"] = full_name


        flash(
            "Admin account updated successfully.",
            "success"
        )


    except Exception as e:

        conn.rollback()

        print(
            "Admin account error:",
            e
        )

        flash(
            "Unable to update admin account.",
            "error"
        )


    finally:

        cur.close()
        conn.close()


    return redirect(
        url_for(
            "settings.institution_settings"
        )
    )


# =========================================================
# Admin Password
# =========================================================

@settings.route(
    "/settings/change-password",
    methods=["POST"]
)
@login_required
@role_required("institution_admin")
def change_admin_password():

    institution_id = _institution_id()
    user_id = _user_id()


    if not institution_id or not user_id:

        return "Unauthorized", 403


    current_password = request.form.get(
        "current_password",
        ""
    )

    new_password = request.form.get(
        "new_password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )


    if not current_password:

        flash(
            "Current password is required.",
            "error"
        )

        return redirect(
            url_for(
                "settings.institution_settings"
            )
        )


    if len(new_password) < 6:

        flash(
            "New password must be at least 6 characters.",
            "error"
        )

        return redirect(
            url_for(
                "settings.institution_settings"
            )
        )


    if new_password != confirm_password:

        flash(
            "New passwords do not match.",
            "error"
        )

        return redirect(
            url_for(
                "settings.institution_settings"
            )
        )


    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            SELECT password

            FROM users

            WHERE
                id = %s
                AND institution_id = %s
                AND is_active = TRUE

            LIMIT 1
            """,
            (
                user_id,
                institution_id
            )
        )


        user = cur.fetchone()


        if not user:

            flash(
                "Admin account not found.",
                "error"
            )

            return redirect(
                url_for(
                    "settings.institution_settings"
                )
            )


        stored_password = user[0]


        if not check_password_hash(
            stored_password,
            current_password
        ):

            flash(
                "Current password is incorrect.",
                "error"
            )

            return redirect(
                url_for(
                    "settings.institution_settings"
                )
            )


        new_hash = generate_password_hash(
            new_password
        )


        cur.execute(
            """
            UPDATE users

            SET
                password = %s,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
            """,
            (
                new_hash,
                user_id,
                institution_id
            )
        )


        conn.commit()


        flash(
            "Admin password changed successfully.",
            "success"
        )


    except Exception as e:

        conn.rollback()

        print(
            "Password change error:",
            e
        )

        flash(
            "Unable to change password.",
            "error"
        )


    finally:

        cur.close()
        conn.close()


    return redirect(
        url_for(
            "settings.institution_settings"
        )
    )


# =========================================================
# Password Reset — User
# =========================================================

@settings.route(
    "/settings/reset-password/<int:user_id>",
    methods=["POST"]
)
@login_required
@role_required("institution_admin")
def reset_user_password(user_id):

    institution_id = _institution_id()


    if not institution_id:

        return "Unauthorized", 403


    new_password = request.form.get(
        "new_password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )


    if len(new_password) < 6:

        flash(
            "Password must be at least 6 characters.",
            "error"
        )

        return redirect(
            url_for(
                "settings.institution_settings"
            )
        )


    if new_password != confirm_password:

        flash(
            "Passwords do not match.",
            "error"
        )

        return redirect(
            url_for(
                "settings.institution_settings"
            )
        )


    conn = get_connection()
    cur = conn.cursor()

    try:

        # ---------------------------------------------
        # Find user within same institution
        # ---------------------------------------------

        cur.execute(
            """
            SELECT
                u.id,
                u.full_name,
                r.name AS role_name

            FROM users u

            JOIN roles r
                ON r.id = u.role_id

            WHERE
                u.id = %s
                AND u.institution_id = %s

            LIMIT 1
            """,
            (
                user_id,
                institution_id
            )
        )


        user = cur.fetchone()


        if not user:

            flash(
                "User not found.",
                "error"
            )

            return redirect(
                url_for(
                    "settings.institution_settings"
                )
            )


        role_name = user[2]


        # ---------------------------------------------
        # Allowed reset roles
        # ---------------------------------------------

        allowed_roles = {
            "staff",
            "student",
            "parent"
        }


        if role_name not in allowed_roles:

            flash(
                "This account cannot be reset from Institution Settings.",
                "error"
            )

            return redirect(
                url_for(
                    "settings.institution_settings"
                )
            )


        # ---------------------------------------------
        # Reset password
        # ---------------------------------------------

        password_hash = generate_password_hash(
            new_password
        )


        cur.execute(
            """
            UPDATE users

            SET
                password = %s,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
            """,
            (
                password_hash,
                user_id,
                institution_id
            )
        )


        if cur.rowcount != 1:

            raise RuntimeError(
                "Password reset failed."
            )


        conn.commit()


        flash(
            f"Password reset successfully for {user[1]}.",
            "success"
        )


    except Exception as e:

        conn.rollback()

        print(
            "User password reset error:",
            e
        )

        flash(
            "Unable to reset user password.",
            "error"
        )


    finally:

        cur.close()
        conn.close()


    return redirect(
        url_for(
            "settings.institution_settings"
        )
    )


# =========================================================
# Password Management Data
# =========================================================

@settings.route(
    "/settings/password-management",
    methods=["GET"]
)
@login_required
@role_required("institution_admin")
def password_management():

    institution_id = _institution_id()


    if not institution_id:

        return "Unauthorized", 403


    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            SELECT
                u.id,
                u.full_name,
                u.username,
                u.email,
                u.phone,
                u.is_active,
                r.name AS role_name

            FROM users u

            JOIN roles r
                ON r.id = u.role_id

            WHERE
                u.institution_id = %s

                AND r.name IN (
                    'staff',
                    'student',
                    'parent'
                )

            ORDER BY
                r.name,
                u.full_name
            """,
            (institution_id,)
        )


        users = cur.fetchall()


        return render_template(
            "settings/password_management.html",
            users=users
        )


    finally:

        cur.close()
        conn.close()