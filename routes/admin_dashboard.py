from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for
)

from database.db import get_connection
from middleware.roles import role_required


admin_dashboard = Blueprint(
    "admin_dashboard",
    __name__
)


# =========================================================
# Super Admin Dashboard
# =========================================================

@admin_dashboard.route(
    "/admin/dashboard"
)
@role_required("super_admin")
def dashboard():

    conn = get_connection()
    cur = conn.cursor()

    try:

        # =================================================
        # 1. Institution Statistics
        # =================================================

        cur.execute("""
            SELECT
                COUNT(*) AS total_institutions,

                COUNT(*) FILTER (
                    WHERE status = 'active'
                ) AS active_institutions,

                COUNT(*) FILTER (
                    WHERE status <> 'active'
                        OR status IS NULL
                ) AS inactive_institutions

            FROM institutions

            WHERE
                code <> 'SYSTEM'
        """)

        institution_stats = cur.fetchone()

        total_institutions = (
            institution_stats["total_institutions"] or 0
            if institution_stats
            else 0
        )

        active_institutions = (
            institution_stats["active_institutions"] or 0
            if institution_stats
            else 0
        )

        inactive_institutions = (
            institution_stats["inactive_institutions"] or 0
            if institution_stats
            else 0
        )


        # =================================================
        # 2. Total Students
        # =================================================

        cur.execute("""
            SELECT
                COUNT(*) AS total_students

            FROM students s

            JOIN institutions i
                ON i.id = s.institution_id

            WHERE
                i.code <> 'SYSTEM'
                AND s.is_active = TRUE
        """)

        result = cur.fetchone()

        total_students = (
            result["total_students"] or 0
            if result
            else 0
        )


        # =================================================
        # 3. Total Staff
        # =================================================

        cur.execute("""
            SELECT
                COUNT(*) AS total_staff

            FROM users u

            JOIN roles r
                ON r.id = u.role_id

            JOIN institutions i
                ON i.id = u.institution_id

            WHERE
                i.code <> 'SYSTEM'
                AND u.is_active = TRUE
                AND r.name IN (
                    'staff',
                    'principal'
                )
        """)

        result = cur.fetchone()

        total_staff = (
            result["total_staff"] or 0
            if result
            else 0
        )


        # =================================================
        # 4. Subscription Statistics
        # =================================================

        cur.execute("""
            SELECT
                COUNT(*) FILTER (
                    WHERE subscription_plan = 'free'
                        OR subscription_plan IS NULL
                ) AS free_institutions,

                COUNT(*) FILTER (
                    WHERE subscription_plan = 'premium'
                ) AS premium_institutions

            FROM institutions

            WHERE
                code <> 'SYSTEM'
        """)

        subscription_stats = cur.fetchone()

        free_institutions = (
            subscription_stats["free_institutions"] or 0
            if subscription_stats
            else 0
        )

        premium_institutions = (
            subscription_stats["premium_institutions"] or 0
            if subscription_stats
            else 0
        )


        # =================================================
        # 5. Recent Institutions
        # =================================================

        cur.execute("""
            SELECT
                i.id,
                i.name,
                i.code,
                i.email,
                i.phone,
                i.status,
                i.subscription_plan,
                i.subscription_start,
                i.subscription_end,
                i.created_at,

                (
                    SELECT COUNT(*)

                    FROM students s

                    WHERE
                        s.institution_id = i.id
                        AND s.is_active = TRUE
                ) AS student_count,

                (
                    SELECT COUNT(*)

                    FROM users u

                    JOIN roles r
                        ON r.id = u.role_id

                    WHERE
                        u.institution_id = i.id
                        AND u.is_active = TRUE
                        AND r.name IN (
                            'staff',
                            'principal'
                        )
                ) AS staff_count

            FROM institutions i

            WHERE
                i.code <> 'SYSTEM'

            ORDER BY
                i.created_at DESC NULLS LAST,
                i.id DESC

            LIMIT 6
        """)

        recent_institutions = cur.fetchall()


        # =================================================
        # 6. Subscription Expiring Soon
        # =================================================

        cur.execute("""
            SELECT
                COUNT(*) AS count

            FROM institutions

            WHERE
                code <> 'SYSTEM'
                AND status = 'active'
                AND subscription_end IS NOT NULL
                AND subscription_end >= CURRENT_DATE
                AND subscription_end <= (
                    CURRENT_DATE + INTERVAL '30 days'
                )
        """)

        result = cur.fetchone()

        expiring_soon = (
            result["count"] or 0
            if result
            else 0
        )


        # =================================================
        # 7. Expired Subscriptions
        # =================================================

        cur.execute("""
            SELECT
                COUNT(*) AS count

            FROM institutions

            WHERE
                code <> 'SYSTEM'
                AND subscription_end IS NOT NULL
                AND subscription_end < CURRENT_DATE
        """)

        result = cur.fetchone()

        expired_subscriptions = (
            result["count"] or 0
            if result
            else 0
        )


        # =================================================
        # 8. Dashboard
        # =================================================

        return render_template(
            "admin/dashboard.html",

            # Institution statistics
            total_institutions=total_institutions,
            active_institutions=active_institutions,
            inactive_institutions=inactive_institutions,

            # User statistics
            total_students=total_students,
            total_staff=total_staff,

            # Subscription statistics
            free_institutions=free_institutions,
            premium_institutions=premium_institutions,
            expiring_soon=expiring_soon,
            expired_subscriptions=expired_subscriptions,

            # Recent institutions
            recent_institutions=recent_institutions
        )


    finally:

        cur.close()
        conn.close()