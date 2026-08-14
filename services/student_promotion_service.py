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
# Helpers
# =========================================================

def _get_institution_id():
    return session.get("institution_id")


# =========================================================
# 1. List Promotion History
# =========================================================

def list_promotions():

    institution_id = _get_institution_id()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            sp.id,
            sp.student_id,
            s.admission_no,
            s.full_name,

            sp.academic_year_id,
            ay.year_name,

            sp.from_class_id,
            fc.class_name AS from_class_name,

            sp.to_class_id,
            tc.class_name AS to_class_name,

            sp.promotion_date,
            sp.remarks,

            sp.created_by,
            u.full_name AS created_by_name,

            sp.created_at

        FROM student_promotions sp

        JOIN students s
            ON s.id = sp.student_id

        JOIN academic_years ay
            ON ay.id = sp.academic_year_id

        LEFT JOIN classes fc
            ON fc.id = sp.from_class_id

        JOIN classes tc
            ON tc.id = sp.to_class_id

        LEFT JOIN users u
            ON u.id = sp.created_by

        WHERE
            sp.institution_id = %s

        ORDER BY
            sp.promotion_date DESC,
            sp.id DESC
    """, (
        institution_id,
    ))

    promotions = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "student_promotions/list.html",
        promotions=promotions
    )


# =========================================================
# 2. Promote Student
# =========================================================

def promote_student():

    institution_id = _get_institution_id()

    conn = get_connection()
    cur = conn.cursor()

    # =====================================================
    # Get Students
    # =====================================================

    cur.execute("""
        SELECT
            s.id,
            s.admission_no,
            s.full_name,
            s.class_id,
            c.class_name

        FROM students s

        LEFT JOIN classes c
            ON c.id = s.class_id

        WHERE
            s.institution_id = %s
            AND s.is_active = TRUE

        ORDER BY
            s.full_name
    """, (
        institution_id,
    ))

    students = cur.fetchall()


    # =====================================================
    # Get Active Academic Years
    # =====================================================

    cur.execute("""
        SELECT
            id,
            year_name,
            start_date,
            end_date,
            is_current

        FROM academic_years

        WHERE
            institution_id = %s
            AND is_active = TRUE

        ORDER BY
            start_date DESC,
            id DESC
    """, (
        institution_id,
    ))

    academic_years = cur.fetchall()


    # =====================================================
    # Get Active Classes
    # =====================================================

    cur.execute("""
        SELECT
            id,
            class_name

        FROM classes

        WHERE
            institution_id = %s
            AND is_active = TRUE

        ORDER BY
            class_name
    """, (
        institution_id,
    ))

    classes = cur.fetchall()


    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        student_id = request.form.get(
            "student_id"
        )

        academic_year_id = request.form.get(
            "academic_year_id"
        )

        to_class_id = request.form.get(
            "to_class_id"
        )

        promotion_date = request.form.get(
            "promotion_date"
        )

        remarks = request.form.get(
            "remarks",
            ""
        ).strip()


        # =================================================
        # Required Fields
        # =================================================

        if not student_id:

            flash(
                "Please select a student.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "student_promotions/add.html",
                students=students,
                academic_years=academic_years,
                classes=classes
            )


        if not academic_year_id:

            flash(
                "Please select an academic year.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "student_promotions/add.html",
                students=students,
                academic_years=academic_years,
                classes=classes
            )


        if not to_class_id:

            flash(
                "Please select the new class.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "student_promotions/add.html",
                students=students,
                academic_years=academic_years,
                classes=classes
            )


        if not promotion_date:

            flash(
                "Promotion date is required.",
                "error"
            )

            cur.close()
            conn.close()

            return render_template(
                "student_promotions/add.html",
                students=students,
                academic_years=academic_years,
                classes=classes
            )


        # =================================================
        # Verify Student
        # =================================================

        cur.execute("""
            SELECT
                id,
                class_id,
                is_active

            FROM students

            WHERE
                id = %s
                AND institution_id = %s
        """, (
            student_id,
            institution_id
        ))

        student = cur.fetchone()


        if not student:

            cur.close()
            conn.close()

            flash(
                "Student not found.",
                "error"
            )

            return redirect(
                url_for(
                    "student_promotions.create_promotion"
                )
            )


        if not student["is_active"]:

            cur.close()
            conn.close()

            flash(
                "Inactive students cannot be promoted.",
                "error"
            )

            return redirect(
                url_for(
                    "student_promotions.create_promotion"
                )
            )


        # =================================================
        # Verify Academic Year
        # =================================================

        cur.execute("""
            SELECT
                id,
                is_active

            FROM academic_years

            WHERE
                id = %s
                AND institution_id = %s
        """, (
            academic_year_id,
            institution_id
        ))

        academic_year = cur.fetchone()


        if not academic_year:

            cur.close()
            conn.close()

            flash(
                "Academic year not found.",
                "error"
            )

            return redirect(
                url_for(
                    "student_promotions.create_promotion"
                )
            )


        if not academic_year["is_active"]:

            cur.close()
            conn.close()

            flash(
                "Promotions can only be made under an active academic year.",
                "error"
            )

            return redirect(
                url_for(
                    "student_promotions.create_promotion"
                )
            )


        # =================================================
        # Verify Target Class
        # =================================================

        cur.execute("""
            SELECT
                id,
                class_name

            FROM classes

            WHERE
                id = %s
                AND institution_id = %s
                AND is_active = TRUE
        """, (
            to_class_id,
            institution_id
        ))

        target_class = cur.fetchone()


        if not target_class:

            cur.close()
            conn.close()

            flash(
                "Selected class is not available.",
                "error"
            )

            return redirect(
                url_for(
                    "student_promotions.create_promotion"
                )
            )


        # =================================================
        # Same Class Check
        # =================================================

        if student["class_id"] == target_class["id"]:

            cur.close()
            conn.close()

            flash(
                "The student is already assigned to this class.",
                "error"
            )

            return redirect(
                url_for(
                    "student_promotions.create_promotion"
                )
            )


        # =================================================
        # Duplicate Promotion Check
        # =================================================

        cur.execute("""
            SELECT
                id

            FROM student_promotions

            WHERE
                institution_id = %s
                AND student_id = %s
                AND academic_year_id = %s
        """, (
            institution_id,
            student_id,
            academic_year_id
        ))

        existing_promotion = cur.fetchone()


        if existing_promotion:

            cur.close()
            conn.close()

            flash(
                "This student already has a promotion record for the selected academic year.",
                "error"
            )

            return redirect(
                url_for(
                    "student_promotions.create_promotion"
                )
            )


        # =================================================
        # Create Promotion History
        # =================================================

        cur.execute("""
            INSERT INTO student_promotions
            (
                institution_id,
                student_id,
                academic_year_id,
                from_class_id,
                to_class_id,
                promotion_date,
                remarks,
                created_by
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
                %s
            )
        """, (
            institution_id,
            student_id,
            academic_year_id,
            student["class_id"],
            to_class_id,
            promotion_date,
            remarks,
            session.get("user_id")
        ))


        # =================================================
        # Update Current Student Class
        # =================================================

        cur.execute("""
            UPDATE students

            SET
                class_id = %s,
                updated_at = NOW()

            WHERE
                id = %s
                AND institution_id = %s
        """, (
            to_class_id,
            student_id,
            institution_id
        ))


        conn.commit()

        cur.close()
        conn.close()


        flash(
            "Student promoted successfully.",
            "success"
        )

        return redirect(
            url_for(
                "student_promotions.list_promotions_page"
            )
        )


    # =====================================================
    # GET
    # =====================================================

    cur.close()
    conn.close()

    return render_template(
        "student_promotions/add.html",
        students=students,
        academic_years=academic_years,
        classes=classes
    )