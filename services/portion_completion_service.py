from datetime import date

from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from database.db import get_connection


# =========================================================
# 1. Portion Completion Page
# =========================================================

def portion_completion_page():

    class_id = request.args.get(
        "class_id",
        ""
    )

    subject_id = request.args.get(
        "subject_id",
        ""
    )

    completion_date = request.args.get(
        "date",
        str(date.today())
    )

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")

    # =====================================================
    # Get Allowed Classes
    # =====================================================

    if role == "institution_admin":

        cur.execute("""
            SELECT
                id,
                class_name

            FROM classes

            WHERE
                institution_id = %s
                AND is_active = TRUE

            ORDER BY class_name
        """, (
            session["institution_id"],
        ))

    elif role == "staff":

        cur.execute("""
            SELECT DISTINCT
                c.id,
                c.class_name

            FROM classes c

            JOIN staff_classes sc
                ON sc.class_id = c.id

            WHERE
                c.institution_id = %s

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

                AND c.is_active = TRUE

            ORDER BY c.class_name
        """, (
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    classes = cur.fetchall()

    subjects = []


    # =====================================================
    # Verify Selected Class
    # =====================================================

    if class_id:

        if role == "institution_admin":

            cur.execute("""
                SELECT
                    id

                FROM classes

                WHERE
                    id = %s
                    AND institution_id = %s
                    AND is_active = TRUE
            """, (
                class_id,
                session["institution_id"]
            ))

        elif role == "staff":

            cur.execute("""
                SELECT
                    c.id

                FROM classes c

                JOIN staff_classes sc
                    ON sc.class_id = c.id

                WHERE
                    c.id = %s
                    AND c.institution_id = %s

                    AND sc.institution_id = %s
                    AND sc.staff_id = %s
                    AND sc.is_active = TRUE

                    AND c.is_active = TRUE
            """, (
                class_id,
                session["institution_id"],
                session["institution_id"],
                session["user_id"]
            ))

        else:

            cur.close()
            conn.close()

            return "Unauthorized", 403


        allowed_class = cur.fetchone()


        if not allowed_class:

            cur.close()
            conn.close()

            flash(
                "You do not have access to this class.",
                "error"
            )

            return redirect(
                url_for(
                    "portion_completion.portion_completion_page_route"
                )
            )


        # =================================================
        # Get Allowed Subjects For Selected Class
        # =================================================

        if role == "institution_admin":

            cur.execute("""
                SELECT
                    id,
                    subject_name

                FROM subjects

                WHERE
                    institution_id = %s
                    AND class_id = %s
                    AND is_active = TRUE

                ORDER BY subject_name
            """, (
                session["institution_id"],
                class_id
            ))

        elif role == "staff":

            cur.execute("""
                SELECT DISTINCT
                    s.id,
                    s.subject_name

                FROM subjects s

                JOIN staff_subjects ss
                    ON ss.subject_id = s.id

                WHERE
                    s.institution_id = %s
                    AND s.class_id = %s

                    AND ss.institution_id = %s
                    AND ss.staff_id = %s
                    AND ss.is_active = TRUE

                    AND s.is_active = TRUE

                ORDER BY s.subject_name
            """, (
                session["institution_id"],
                class_id,
                session["institution_id"],
                session["user_id"]
            ))

        subjects = cur.fetchall()


        # =================================================
        # Verify Selected Subject
        # =================================================

        if subject_id:

            if role == "institution_admin":

                cur.execute("""
                    SELECT
                        id

                    FROM subjects

                    WHERE
                        id = %s
                        AND class_id = %s
                        AND institution_id = %s
                        AND is_active = TRUE
                """, (
                    subject_id,
                    class_id,
                    session["institution_id"]
                ))

            elif role == "staff":

                cur.execute("""
                    SELECT
                        s.id

                    FROM subjects s

                    JOIN staff_subjects ss
                        ON ss.subject_id = s.id

                    WHERE
                        s.id = %s
                        AND s.class_id = %s
                        AND s.institution_id = %s

                        AND ss.institution_id = %s
                        AND ss.staff_id = %s
                        AND ss.is_active = TRUE

                        AND s.is_active = TRUE
                """, (
                    subject_id,
                    class_id,
                    session["institution_id"],
                    session["institution_id"],
                    session["user_id"]
                ))

            valid_subject = cur.fetchone()


            if not valid_subject:

                cur.close()
                conn.close()

                flash(
                    "You do not have access to this subject.",
                    "error"
                )

                return redirect(
                    url_for(
                        "portion_completion.portion_completion_page_route",
                        class_id=class_id
                    )
                )


    cur.close()
    conn.close()


    return render_template(
        "portion_completion/form.html",

        classes=classes,

        subjects=subjects,

        class_id=class_id,

        subject_id=subject_id,

        completion_date=completion_date
    )


# =========================================================
# 2. Save Portion Completion
# =========================================================

def save_portion_completion():

    class_id = request.form.get(
        "class_id"
    )

    subject_id = request.form.get(
        "subject_id"
    )

    completion_date = request.form.get(
        "completion_date"
    )

    completed_portion = request.form.get(
        "completed_portion",
        ""
    ).strip()

    remarks = request.form.get(
        "remarks",
        ""
    ).strip()


    # =====================================================
    # Basic Validation
    # =====================================================

    if not class_id:

        flash(
            "Please select a class.",
            "error"
        )

        return redirect(
            url_for(
                "portion_completion.portion_completion_page_route"
            )
        )


    if not subject_id:

        flash(
            "Please select a subject.",
            "error"
        )

        return redirect(
            url_for(
                "portion_completion.portion_completion_page_route",
                class_id=class_id
            )
        )


    if not completion_date:

        flash(
            "Please select a completion date.",
            "error"
        )

        return redirect(
            url_for(
                "portion_completion.portion_completion_page_route",
                class_id=class_id,
                subject_id=subject_id
            )
        )


    if not completed_portion:

        flash(
            "Please enter the completed portion.",
            "error"
        )

        return redirect(
            url_for(
                "portion_completion.portion_completion_page_route",
                class_id=class_id,
                subject_id=subject_id,
                date=completion_date
            )
        )


    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    # =====================================================
    # Verify Class Access
    # =====================================================

    if role == "institution_admin":

        cur.execute("""
            SELECT
                id

            FROM classes

            WHERE
                id = %s
                AND institution_id = %s
                AND is_active = TRUE
        """, (
            class_id,
            session["institution_id"]
        ))

    elif role == "staff":

        cur.execute("""
            SELECT
                c.id

            FROM classes c

            JOIN staff_classes sc
                ON sc.class_id = c.id

            WHERE
                c.id = %s
                AND c.institution_id = %s

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

                AND c.is_active = TRUE
        """, (
            class_id,
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    valid_class = cur.fetchone()


    if not valid_class:

        cur.close()
        conn.close()

        flash(
            "You do not have access to this class.",
            "error"
        )

        return redirect(
            url_for(
                "portion_completion.portion_completion_page_route"
            )
        )


    # =====================================================
    # Verify Subject Access
    # =====================================================

    if role == "institution_admin":

        cur.execute("""
            SELECT
                id

            FROM subjects

            WHERE
                id = %s
                AND class_id = %s
                AND institution_id = %s
                AND is_active = TRUE
        """, (
            subject_id,
            class_id,
            session["institution_id"]
        ))

    elif role == "staff":

        cur.execute("""
            SELECT
                s.id

            FROM subjects s

            JOIN staff_subjects ss
                ON ss.subject_id = s.id

            WHERE
                s.id = %s
                AND s.class_id = %s
                AND s.institution_id = %s

                AND ss.institution_id = %s
                AND ss.staff_id = %s
                AND ss.is_active = TRUE

                AND s.is_active = TRUE
        """, (
            subject_id,
            class_id,
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    valid_subject = cur.fetchone()


    if not valid_subject:

        cur.close()
        conn.close()

        flash(
            "You do not have access to this subject.",
            "error"
        )

        return redirect(
            url_for(
                "portion_completion.portion_completion_page_route",
                class_id=class_id
            )
        )


    # =====================================================
    # Save Portion Completion
    # =====================================================

    cur.execute("""
        INSERT INTO portion_completion
        (
            institution_id,
            class_id,
            subject_id,
            staff_id,
            completion_date,
            completed_portion,
            remarks
        )

        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """, (
        session["institution_id"],
        class_id,
        subject_id,
        session["user_id"],
        completion_date,
        completed_portion,
        remarks or None
    ))


    conn.commit()

    cur.close()
    conn.close()


    flash(
        "Portion completed successfully.",
        "success"
    )


    return redirect(
        url_for(
            "portion_completion.portion_completion_list_route"
        )
    )


# =========================================================
# 3. Portion Completion List
# =========================================================

def portion_completion_list():

    class_id = request.args.get(
        "class_id",
        ""
    )

    subject_id = request.args.get(
        "subject_id",
        ""
    )

    conn = get_connection()
    cur = conn.cursor()

    role = session.get("role")


    # =====================================================
    # Classes
    # =====================================================

    if role == "institution_admin":

        cur.execute("""
            SELECT
                id,
                class_name

            FROM classes

            WHERE
                institution_id = %s
                AND is_active = TRUE

            ORDER BY class_name
        """, (
            session["institution_id"],
        ))

    elif role == "staff":

        cur.execute("""
            SELECT DISTINCT
                c.id,
                c.class_name

            FROM classes c

            JOIN staff_classes sc
                ON sc.class_id = c.id

            WHERE
                c.institution_id = %s

                AND sc.institution_id = %s
                AND sc.staff_id = %s
                AND sc.is_active = TRUE

                AND c.is_active = TRUE

            ORDER BY c.class_name
        """, (
            session["institution_id"],
            session["institution_id"],
            session["user_id"]
        ))

    else:

        cur.close()
        conn.close()

        return "Unauthorized", 403


    classes = cur.fetchall()

    subjects = []


    # =====================================================
    # Verify Selected Class
    # =====================================================

    if class_id:

        if role == "institution_admin":

            cur.execute("""
                SELECT
                    id

                FROM classes

                WHERE
                    id = %s
                    AND institution_id = %s
                    AND is_active = TRUE
            """, (
                class_id,
                session["institution_id"]
            ))

        elif role == "staff":

            cur.execute("""
                SELECT
                    c.id

                FROM classes c

                JOIN staff_classes sc
                    ON sc.class_id = c.id

                WHERE
                    c.id = %s
                    AND c.institution_id = %s

                    AND sc.institution_id = %s
                    AND sc.staff_id = %s
                    AND sc.is_active = TRUE

                    AND c.is_active = TRUE
            """, (
                class_id,
                session["institution_id"],
                session["institution_id"],
                session["user_id"]
            ))

        valid_class = cur.fetchone()


        if not valid_class:

            cur.close()
            conn.close()

            flash(
                "You do not have access to this class.",
                "error"
            )

            return redirect(
                url_for(
                    "portion_completion.portion_completion_list_route"
                )
            )


        # =================================================
        # Subjects
        # =================================================

        if role == "institution_admin":

            cur.execute("""
                SELECT
                    id,
                    subject_name

                FROM subjects

                WHERE
                    institution_id = %s
                    AND class_id = %s
                    AND is_active = TRUE

                ORDER BY subject_name
            """, (
                session["institution_id"],
                class_id
            ))

        elif role == "staff":

            cur.execute("""
                SELECT DISTINCT
                    s.id,
                    s.subject_name

                FROM subjects s

                JOIN staff_subjects ss
                    ON ss.subject_id = s.id

                WHERE
                    s.institution_id = %s
                    AND s.class_id = %s

                    AND ss.institution_id = %s
                    AND ss.staff_id = %s
                    AND ss.is_active = TRUE

                    AND s.is_active = TRUE

                ORDER BY s.subject_name
            """, (
                session["institution_id"],
                class_id,
                session["institution_id"],
                session["user_id"]
            ))

        subjects = cur.fetchall()


        # =================================================
        # Verify Selected Subject
        # =================================================

        if subject_id:

            if role == "institution_admin":

                cur.execute("""
                    SELECT
                        id

                    FROM subjects

                    WHERE
                        id = %s
                        AND class_id = %s
                        AND institution_id = %s
                        AND is_active = TRUE
                """, (
                    subject_id,
                    class_id,
                    session["institution_id"]
                ))

            elif role == "staff":

                cur.execute("""
                    SELECT
                        s.id

                    FROM subjects s

                    JOIN staff_subjects ss
                        ON ss.subject_id = s.id

                    WHERE
                        s.id = %s
                        AND s.class_id = %s
                        AND s.institution_id = %s

                        AND ss.institution_id = %s
                        AND ss.staff_id = %s
                        AND ss.is_active = TRUE

                        AND s.is_active = TRUE
                """, (
                    subject_id,
                    class_id,
                    session["institution_id"],
                    session["institution_id"],
                    session["user_id"]
                ))

            valid_subject = cur.fetchone()


            if not valid_subject:

                cur.close()
                conn.close()
                
                flash(
                    "You do not have access to this subject.",
                    "error"
                )

                return redirect(
                    url_for(
                        "portion_completion.portion_completion_list_route",
                        class_id=class_id
                    )
                )
                
        # =====================================================
        # Completed Portions
        # =====================================================

        query = """
            SELECT
                pc.id,
                pc.completion_date,
                pc.completed_portion,
                pc.remarks,

                c.class_name,

                s.subject_name,

                u.full_name AS staff_name

            FROM portion_completion pc

            JOIN classes c
                ON pc.class_id = c.id

            JOIN subjects s
                ON pc.subject_id = s.id

            JOIN users u
                ON pc.staff_id = u.id

            WHERE
                pc.institution_id = %s

                AND c.institution_id = %s
                AND s.institution_id = %s
        """

        params = [
            session["institution_id"],
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
                        AND sc.class_id = pc.class_id
                        AND sc.is_active = TRUE
                )

                AND EXISTS (
                    SELECT 1

                    FROM staff_subjects ss

                    WHERE
                        ss.institution_id = %s
                        AND ss.staff_id = %s
                        AND ss.subject_id = pc.subject_id
                        AND ss.is_active = TRUE
                )
            """

            params.extend([
                session["institution_id"],
                session["user_id"],
                session["institution_id"],
                session["user_id"]
            ])


        # =====================================================
        # Class Filter
        # =====================================================

        if class_id:

            query += """
                AND pc.class_id = %s
            """

            params.append(class_id)


        # =====================================================
        # Subject Filter
        # =====================================================

        if subject_id:

            query += """
                AND pc.subject_id = %s
            """

            params.append(subject_id)


        # =====================================================
        # Order
        # =====================================================

        query += """
            ORDER BY
                pc.completion_date DESC,
                c.class_name,
                s.subject_name,
                pc.id DESC
        """


        cur.execute(
            query,
            tuple(params)
        )

        completions = cur.fetchall()


        cur.close()
        conn.close()


        return render_template(
            "portion_completion/list.html",

            completions=completions,

            classes=classes,

            subjects=subjects,

            class_id=class_id,

            subject_id=subject_id
        )

