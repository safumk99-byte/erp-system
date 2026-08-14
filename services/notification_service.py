from flask import session

from database.db import get_connection


# =========================================================
# Create Notification
# =========================================================

def create_notification(
    user_id,
    notification_type,
    title,
    message,
    institution_id=None
):

    if institution_id is None:

        institution_id = session.get(
            "institution_id"
        )


    if not institution_id:

        return False


    conn = get_connection()
    cur = conn.cursor()

    try:

        # -----------------------------------------
        # Verify User Belongs To Institution
        # -----------------------------------------

        cur.execute("""
            SELECT
                id

            FROM users

            WHERE
                id = %s
                AND institution_id = %s
                AND is_active = TRUE

            LIMIT 1
        """, (
            user_id,
            institution_id
        ))

        user = cur.fetchone()


        if not user:

            return False


        # -----------------------------------------
        # Create Notification
        # -----------------------------------------

        cur.execute("""
            INSERT INTO notifications
            (
                institution_id,
                user_id,
                notification_type,
                title,
                message,
                is_read,
                created_at
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                FALSE,
                CURRENT_TIMESTAMP
            )
        """, (
            institution_id,
            user_id,
            notification_type,
            title,
            message
        ))


        conn.commit()

        return True


    except Exception:

        conn.rollback()

        raise


    finally:

        cur.close()
        conn.close()


# =========================================================
# Create Bulk Notification
# =========================================================

def create_bulk_notification(
    notification_type,
    title,
    message,
    recipient_type,
    institution_id=None
):

    if institution_id is None:

        institution_id = session.get(
            "institution_id"
        )


    if not institution_id:

        return 0


    conn = get_connection()
    cur = conn.cursor()


    try:

        # =================================================
        # Get Recipients
        # =================================================

        if recipient_type == "staff":

            cur.execute("""
                SELECT
                    u.id

                FROM users u

                JOIN roles r
                    ON u.role_id = r.id

                WHERE
                    u.institution_id = %s
                    AND r.name = 'staff'
                    AND u.is_active = TRUE

                ORDER BY
                    u.id
            """, (
                institution_id,
            ))


        elif recipient_type == "parent":

            cur.execute("""
                SELECT
                    u.id

                FROM users u

                JOIN roles r
                    ON u.role_id = r.id

                WHERE
                    u.institution_id = %s
                    AND r.name = 'parent'
                    AND u.is_active = TRUE

                ORDER BY
                    u.id
            """, (
                institution_id,
            ))


        elif recipient_type == "student":

            cur.execute("""
                SELECT
                    u.id

                FROM users u

                JOIN roles r
                    ON u.role_id = r.id

                WHERE
                    u.institution_id = %s
                    AND r.name = 'student'
                    AND u.is_active = TRUE

                ORDER BY
                    u.id
            """, (
                institution_id,
            ))


        elif recipient_type == "all":

            cur.execute("""
                SELECT
                    u.id

                FROM users u

                WHERE
                    u.institution_id = %s
                    AND u.is_active = TRUE
                    AND u.id != %s

                ORDER BY
                    u.id
            """, (
                institution_id,
                session.get(
                    "user_id",
                    0
                )
            ))


        else:

            return 0


        recipients = cur.fetchall()


        if not recipients:

            return 0


        # =================================================
        # Create Notifications
        # =================================================

        created_count = 0


        for recipient in recipients:

            cur.execute("""
                INSERT INTO notifications
                (
                    institution_id,
                    user_id,
                    notification_type,
                    title,
                    message,
                    is_read,
                    created_at
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    FALSE,
                    CURRENT_TIMESTAMP
                )
            """, (
                institution_id,
                recipient["id"],
                notification_type,
                title,
                message
            ))


            created_count += 1


        # =================================================
        # Commit
        # =================================================

        conn.commit()


        return created_count


    except Exception:

        conn.rollback()

        raise


    finally:

        cur.close()
        conn.close()


# =========================================================
# Get User Notifications
# =========================================================

def get_user_notifications(
    limit=20
):

    user_id = session.get(
        "user_id"
    )

    institution_id = session.get(
        "institution_id"
    )


    if not user_id or not institution_id:

        return []


    conn = get_connection()
    cur = conn.cursor()


    try:

        cur.execute("""
            SELECT
                id,
                notification_type,
                title,
                message,
                is_read,
                read_at,
                created_at

            FROM notifications

            WHERE
                user_id = %s
                AND institution_id = %s

            ORDER BY
                created_at DESC

            LIMIT %s
        """, (
            user_id,
            institution_id,
            limit
        ))


        return cur.fetchall()


    finally:

        cur.close()
        conn.close()


# =========================================================
# Get Unread Notification Count
# =========================================================

def get_unread_count():

    user_id = session.get(
        "user_id"
    )

    institution_id = session.get(
        "institution_id"
    )


    if not user_id or not institution_id:

        return 0


    conn = get_connection()
    cur = conn.cursor()


    try:

        cur.execute("""
            SELECT
                COUNT(*) AS unread_count

            FROM notifications

            WHERE
                user_id = %s
                AND institution_id = %s
                AND is_read = FALSE
        """, (
            user_id,
            institution_id
        ))


        result = cur.fetchone()


        if not result:

            return 0


        return int(
            result["unread_count"]
        )


    finally:

        cur.close()
        conn.close()


# =========================================================
# Mark Notification As Read
# =========================================================

def mark_notification_read(
    notification_id
):

    user_id = session.get(
        "user_id"
    )

    institution_id = session.get(
        "institution_id"
    )


    if not user_id or not institution_id:

        return False


    conn = get_connection()
    cur = conn.cursor()


    try:

        cur.execute("""
            UPDATE notifications

            SET
                is_read = TRUE,
                read_at = CURRENT_TIMESTAMP

            WHERE
                id = %s
                AND user_id = %s
                AND institution_id = %s
                AND is_read = FALSE
        """, (
            notification_id,
            user_id,
            institution_id
        ))


        updated = (
            cur.rowcount > 0
        )


        conn.commit()


        return updated


    except Exception:

        conn.rollback()

        raise


    finally:

        cur.close()
        conn.close()


# =========================================================
# Mark All Notifications As Read
# =========================================================

def mark_all_notifications_read():

    user_id = session.get(
        "user_id"
    )

    institution_id = session.get(
        "institution_id"
    )


    if not user_id or not institution_id:

        return False


    conn = get_connection()
    cur = conn.cursor()


    try:

        cur.execute("""
            UPDATE notifications

            SET
                is_read = TRUE,
                read_at = CURRENT_TIMESTAMP

            WHERE
                user_id = %s
                AND institution_id = %s
                AND is_read = FALSE
        """, (
            user_id,
            institution_id
        ))


        updated = (
            cur.rowcount > 0
        )


        conn.commit()


        return updated


    except Exception:

        conn.rollback()

        raise


    finally:

        cur.close()
        conn.close()


# =========================================================
# Notify Student + Parent
# =========================================================

def notify_student_and_parent(
    student_id,
    module_name,
    approved,
    remarks=None,
    institution_id=None,
    cur=None
):

    if institution_id is None:

        institution_id = session.get(
            "institution_id"
        )


    if not institution_id:

        return 0


    # -----------------------------------------------------
    # Use Existing Cursor If Provided
    # -----------------------------------------------------

    own_connection = False


    if cur is None:

        conn = get_connection()
        cur = conn.cursor()

        own_connection = True

    else:

        conn = None


    try:

        # =================================================
        # Get Student + Parent
        # =================================================

        cur.execute("""
            SELECT
                user_id,
                parent_user_id

            FROM students

            WHERE
                id = %s
                AND institution_id = %s
                AND is_active = TRUE

            LIMIT 1
        """, (
            student_id,
            institution_id
        ))


        student = cur.fetchone()


        if not student:

            return 0


        # =================================================
        # Recipients
        # =================================================

        recipient_ids = []


        # Student

        if student["user_id"]:

            recipient_ids.append(
                student["user_id"]
            )


        # Parent

        if student["parent_user_id"]:

            recipient_ids.append(
                student["parent_user_id"]
            )


        # Remove duplicate user IDs

        recipient_ids = list(
            dict.fromkeys(
                recipient_ids
            )
        )


        if not recipient_ids:

            return 0


        # =================================================
        # Notification Content
        # =================================================

        if approved:

            title = (
                f"{module_name} Approved"
            )

            message = (
                f"{module_name} has been approved."
            )

            notification_type = (
                "approval"
            )


        else:

            title = (
                f"{module_name} Rejected"
            )

            message = (
                f"{module_name} has been rejected."
            )

            if remarks:

                message += (
                    f" Reason: {remarks}"
                )

            notification_type = (
                "rejection"
            )


        # =================================================
        # Create Notifications
        # =================================================

        created_count = 0


        for recipient_id in recipient_ids:

            # ---------------------------------------------
            # Verify Recipient
            # ---------------------------------------------

            cur.execute("""
                SELECT
                    id

                FROM users

                WHERE
                    id = %s
                    AND institution_id = %s
                    AND is_active = TRUE

                LIMIT 1
            """, (
                recipient_id,
                institution_id
            ))


            recipient = cur.fetchone()


            if not recipient:

                continue


            # ---------------------------------------------
            # Insert Notification
            # ---------------------------------------------

            cur.execute("""
                INSERT INTO notifications
                (
                    institution_id,
                    user_id,
                    notification_type,
                    title,
                    message,
                    is_read,
                    created_at
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    FALSE,
                    CURRENT_TIMESTAMP
                )
            """, (
                institution_id,
                recipient_id,
                notification_type,
                title,
                message
            ))


            created_count += 1


        # =================================================
        # Commit Only If We Created Our Own Connection
        # =================================================

        if own_connection:

            conn.commit()


        return created_count


    except Exception:

        if own_connection:

            conn.rollback()

        raise


    finally:

        if own_connection:

            cur.close()
            conn.close()