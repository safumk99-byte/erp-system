from flask import (
    request,
    session,
    redirect,
    url_for,
    flash,
    render_template
)

from database.db import get_connection


# =========================================================
# Helper
# =========================================================

def _redirect_to_list():
    return redirect(
        url_for(
            "academic_years.list_academic_years_page"
        )
    )


# =========================================================
# 1. List Academic Years
# =========================================================

def list_academic_years():

    institution_id = session.get("institution_id")

    if not institution_id:
        flash(
            "Institution information is missing.",
            "error"
        )

        return redirect(
            url_for("portal.index")
        )

    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                year_name,
                start_date,
                end_date,
                is_current,
                is_active,
                created_at,
                updated_at

            FROM academic_years

            WHERE
                institution_id = %s

            ORDER BY
                start_date DESC,
                id DESC
        """, (
            institution_id,
        ))

        academic_years = cur.fetchall()

        return render_template(
            "academic_years/list.html",
            academic_years=academic_years
        )

    except Exception:

        if conn:
            conn.rollback()

        flash(
            "Unable to load academic years.",
            "error"
        )

        return _redirect_to_list()

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# 2. Add Academic Year
# =========================================================

def add_academic_year():

    institution_id = session.get("institution_id")

    if not institution_id:
        flash(
            "Institution information is missing.",
            "error"
        )

        return redirect(
            url_for("portal.index")
        )

    if request.method == "POST":

        year_name = request.form.get(
            "year_name",
            ""
        ).strip()

        start_date = request.form.get(
            "start_date",
            ""
        ).strip()

        end_date = request.form.get(
            "end_date",
            ""
        ).strip()

        is_current = (
            request.form.get("is_current") == "on"
        )

        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if not year_name:

            flash(
                "Academic year name is required.",
                "error"
            )

            return redirect(
                url_for(
                    "academic_years.create_academic_year"
                )
            )

        if not start_date or not end_date:

            flash(
                "Start date and end date are required.",
                "error"
            )

            return redirect(
                url_for(
                    "academic_years.create_academic_year"
                )
            )

        if start_date >= end_date:

            flash(
                "End date must be after start date.",
                "error"
            )

            return redirect(
                url_for(
                    "academic_years.create_academic_year"
                )
            )

        conn = None
        cur = None

        try:

            conn = get_connection()
            cur = conn.cursor()

            # -------------------------------------------------
            # Duplicate Check
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    id

                FROM academic_years

                WHERE
                    institution_id = %s
                    AND year_name = %s

                LIMIT 1
            """, (
                institution_id,
                year_name
            ))

            existing = cur.fetchone()

            if existing:

                flash(
                    "This academic year already exists.",
                    "error"
                )

                return redirect(
                    url_for(
                        "academic_years.create_academic_year"
                    )
                )

            # -------------------------------------------------
            # Set Current
            # -------------------------------------------------

            if is_current:

                cur.execute("""
                    UPDATE academic_years

                    SET
                        is_current = FALSE,
                        updated_at = NOW()

                    WHERE
                        institution_id = %s
                        AND is_current = TRUE
                """, (
                    institution_id,
                ))

            # -------------------------------------------------
            # Insert
            # -------------------------------------------------

            cur.execute("""
                INSERT INTO academic_years
                (
                    institution_id,
                    year_name,
                    start_date,
                    end_date,
                    is_current,
                    is_active
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    TRUE
                )
            """, (
                institution_id,
                year_name,
                start_date,
                end_date,
                is_current
            ))

            conn.commit()

            flash(
                "Academic year added successfully.",
                "success"
            )

            return _redirect_to_list()

        except Exception:

            if conn:
                conn.rollback()

            flash(
                "Unable to add academic year.",
                "error"
            )

            return redirect(
                url_for(
                    "academic_years.create_academic_year"
                )
            )

        finally:

            if cur:
                cur.close()

            if conn:
                conn.close()

    return render_template(
        "academic_years/add.html"
    )


# =========================================================
# 3. Edit Academic Year
# =========================================================

def edit_academic_year(id):

    institution_id = session.get(
        "institution_id"
    )

    if not institution_id:
        flash(
            "Institution information is missing.",
            "error"
        )

        return redirect(
            url_for("portal.index")
        )

    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()

        # -------------------------------------------------
        # Get Academic Year
        # -------------------------------------------------

        cur.execute("""
            SELECT
                id,
                year_name,
                start_date,
                end_date,
                is_current,
                is_active

            FROM academic_years

            WHERE
                id = %s
                AND institution_id = %s

            FOR UPDATE
        """, (
            id,
            institution_id
        ))

        academic_year = cur.fetchone()

        if not academic_year:

            flash(
                "Academic year not found.",
                "error"
            )

            return _redirect_to_list()

        # -------------------------------------------------
        # GET
        # -------------------------------------------------

        if request.method == "GET":

            return render_template(
                "academic_years/edit.html",
                academic_year=academic_year
            )

        # -------------------------------------------------
        # POST
        # -------------------------------------------------

        year_name = request.form.get(
            "year_name",
            ""
        ).strip()

        start_date = request.form.get(
            "start_date",
            ""
        ).strip()

        end_date = request.form.get(
            "end_date",
            ""
        ).strip()

        is_current = (
            request.form.get("is_current") == "on"
        )

        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if not year_name:

            flash(
                "Academic year name is required.",
                "error"
            )

            return redirect(
                url_for(
                    "academic_years.edit_academic_year",
                    id=id
                )
            )

        if not start_date or not end_date:

            flash(
                "Start date and end date are required.",
                "error"
            )

            return redirect(
                url_for(
                    "academic_years.edit_academic_year",
                    id=id
                )
            )

        if start_date >= end_date:

            flash(
                "End date must be after start date.",
                "error"
            )

            return redirect(
                url_for(
                    "academic_years.edit_academic_year",
                    id=id
                )
            )

        # -------------------------------------------------
        # IMPORTANT:
        # A current academic year cannot be unchecked.
        # To change current year, use "Set Current".
        # -------------------------------------------------

        if (
            academic_year["is_current"]
            and not is_current
        ):

            flash(
                "The current academic year cannot be unset. "
                "Set another academic year as current instead.",
                "error"
            )

            return redirect(
                url_for(
                    "academic_years.edit_academic_year",
                    id=id
                )
            )

        # -------------------------------------------------
        # Duplicate Check
        # -------------------------------------------------

        cur.execute("""
            SELECT
                id

            FROM academic_years

            WHERE
                institution_id = %s
                AND year_name = %s
                AND id != %s

            LIMIT 1
        """, (
            institution_id,
            year_name,
            id
        ))

        duplicate = cur.fetchone()

        if duplicate:

            flash(
                "This academic year already exists.",
                "error"
            )

            return redirect(
                url_for(
                    "academic_years.edit_academic_year",
                    id=id
                )
            )

        # -------------------------------------------------
        # Set Current
        # -------------------------------------------------

        if is_current:

            cur.execute("""
                UPDATE academic_years

                SET
                    is_current = FALSE,
                    updated_at = NOW()

                WHERE
                    institution_id = %s
                    AND id != %s
                    AND is_current = TRUE
            """, (
                institution_id,
                id
            ))

        # -------------------------------------------------
        # Update
        # -------------------------------------------------

        cur.execute("""
            UPDATE academic_years

            SET
                year_name = %s,
                start_date = %s,
                end_date = %s,
                is_current = %s,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
        """, (
            year_name,
            start_date,
            end_date,
            is_current,
            id,
            institution_id
        ))

        conn.commit()

        flash(
            "Academic year updated successfully.",
            "success"
        )

        return _redirect_to_list()

    except Exception:

        if conn:
            conn.rollback()

        flash(
            "Unable to update academic year.",
            "error"
        )

        return _redirect_to_list()

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# 4. Toggle Academic Year Status
# =========================================================

def toggle_academic_year_status(id):

    institution_id = session.get(
        "institution_id"
    )

    if not institution_id:
        flash(
            "Institution information is missing.",
            "error"
        )

        return redirect(
            url_for("portal.index")
        )

    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()

        # -------------------------------------------------
        # Get Academic Year
        # -------------------------------------------------

        cur.execute("""
            SELECT
                id,
                is_active,
                is_current

            FROM academic_years

            WHERE
                id = %s
                AND institution_id = %s

            FOR UPDATE
        """, (
            id,
            institution_id
        ))

        academic_year = cur.fetchone()

        if not academic_year:

            flash(
                "Academic year not found.",
                "error"
            )

            return _redirect_to_list()

        # -------------------------------------------------
        # Current year cannot be deactivated
        # -------------------------------------------------

        if academic_year["is_current"]:

            flash(
                "The current academic year cannot be deactivated.",
                "error"
            )

            return _redirect_to_list()

        new_status = not academic_year["is_active"]

        # -------------------------------------------------
        # Update
        # -------------------------------------------------

        cur.execute("""
            UPDATE academic_years

            SET
                is_active = %s,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
        """, (
            new_status,
            id,
            institution_id
        ))

        conn.commit()

        if new_status:

            flash(
                "Academic year activated successfully.",
                "success"
            )

        else:

            flash(
                "Academic year deactivated successfully.",
                "success"
            )

        return _redirect_to_list()

    except Exception:

        if conn:
            conn.rollback()

        flash(
            "Unable to change academic year status.",
            "error"
        )

        return _redirect_to_list()

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# 5. Set Current Academic Year
# =========================================================

def set_current_academic_year(id):

    institution_id = session.get(
        "institution_id"
    )

    if not institution_id:
        flash(
            "Institution information is missing.",
            "error"
        )

        return redirect(
            url_for("portal.index")
        )

    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()

        # -------------------------------------------------
        # Verify Selected Year
        # -------------------------------------------------

        cur.execute("""
            SELECT
                id,
                is_active

            FROM academic_years

            WHERE
                id = %s
                AND institution_id = %s

            FOR UPDATE
        """, (
            id,
            institution_id
        ))

        academic_year = cur.fetchone()

        if not academic_year:

            flash(
                "Academic year not found.",
                "error"
            )

            return _redirect_to_list()

        # -------------------------------------------------
        # Inactive year cannot become current
        # -------------------------------------------------

        if not academic_year["is_active"]:

            flash(
                "An inactive academic year cannot be set as current.",
                "error"
            )

            return _redirect_to_list()

        # -------------------------------------------------
        # Reset Current Year
        # -------------------------------------------------

        cur.execute("""
            UPDATE academic_years

            SET
                is_current = FALSE,
                updated_at = NOW()

            WHERE
                institution_id = %s
                AND is_current = TRUE
        """, (
            institution_id,
        ))

        # -------------------------------------------------
        # Set Selected Year
        # -------------------------------------------------

        cur.execute("""
            UPDATE academic_years

            SET
                is_current = TRUE,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
        """, (
            id,
            institution_id
        ))

        conn.commit()

        flash(
            "Current academic year updated successfully.",
            "success"
        )

        return _redirect_to_list()

    except Exception:

        if conn:
            conn.rollback()

        flash(
            "Unable to change the current academic year.",
            "error"
        )

        return _redirect_to_list()

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()