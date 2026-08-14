from flask import (
    Blueprint,
    redirect,
    url_for,
    render_template,
    flash,
    request
)

from middleware.auth import login_required
from middleware.roles import role_required

from services.notification_service import (
    get_user_notifications,
    get_unread_count,
    mark_notification_read,
    mark_all_notifications_read,
    create_bulk_notification
)


notifications = Blueprint(
    "notifications",
    __name__
)



# =========================================================
# Open Notifications
# =========================================================

@notifications.route(
    "/notifications/open",
    methods=["POST"]
)
@login_required
def open_notifications():

    mark_all_notifications_read()

    return redirect(
        url_for(
            "notifications.notification_list"
        )
    )

# =========================================================
# Notifications
# =========================================================

@notifications.route("/notifications")
@login_required
def notification_list():

    notifications_list = get_user_notifications()

    unread_count = get_unread_count()

    return render_template(
        "notifications/list.html",
        notifications=notifications_list,
        unread_count=unread_count
    )


# =========================================================
# Mark One As Read
# =========================================================

@notifications.route(
    "/notifications/read/<int:id>",
    methods=["POST"]
)
@login_required
def read_notification(id):

    mark_notification_read(id)

    return redirect(
        url_for(
            "notifications.notification_list"
        )
    )


# =========================================================
# Mark All As Read
# =========================================================

@notifications.route(
    "/notifications/read-all",
    methods=["POST"]
)
@login_required
def read_all_notifications():

    mark_all_notifications_read()

    flash(
        "All notifications marked as read.",
        "success"
    )

    return redirect(
        url_for(
            "notifications.notification_list"
        )
    )


# =========================================================
# Create Announcement
# =========================================================

@notifications.route(
    "/notifications/announcement",
    methods=["GET", "POST"]
)
@login_required
@role_required(
    "institution_admin",
    "principal"
)
def create_announcement():

    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        message = request.form.get(
            "message",
            ""
        ).strip()

        recipient_type = request.form.get(
            "recipient_type",
            ""
        ).strip()


        # =================================================
        # Validate Title
        # =================================================

        if not title:

            flash(
                "Announcement title is required.",
                "error"
            )

            return render_template(
                "notifications/announcement.html"
            )


        if len(title) > 200:

            flash(
                "Announcement title is too long.",
                "error"
            )

            return render_template(
                "notifications/announcement.html"
            )


        # =================================================
        # Validate Message
        # =================================================

        if not message:

            flash(
                "Announcement message is required.",
                "error"
            )

            return render_template(
                "notifications/announcement.html"
            )


        # =================================================
        # Validate Recipient
        # =================================================

        allowed_recipients = {
            "staff",
            "parent",
            "student",
            "all"
        }


        if recipient_type not in allowed_recipients:

            flash(
                "Please select a valid recipient group.",
                "error"
            )

            return render_template(
                "notifications/announcement.html"
            )


        # =================================================
        # Create Notifications
        # =================================================

        try:

            created_count = create_bulk_notification(
                notification_type="announcement",
                title=title,
                message=message,
                recipient_type=recipient_type
            )


        except Exception:

            flash(
                "Unable to send announcement. No notifications were created.",
                "error"
            )

            return render_template(
                "notifications/announcement.html"
            )


        # =================================================
        # No Recipients
        # =================================================

        if created_count == 0:

            flash(
                "No active users were found in the selected group.",
                "error"
            )

            return render_template(
                "notifications/announcement.html"
            )


        # =================================================
        # Success
        # =================================================

        flash(
            f"Announcement sent successfully to {created_count} user(s).",
            "success"
        )


        return redirect(
            url_for(
                "notifications.notification_list"
            )
        )


    # =====================================================
    # GET
    # =====================================================

    return render_template(
        "notifications/announcement.html"
    )