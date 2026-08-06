from functools import wraps

from flask import (
    session,
    redirect,
    flash,
    url_for
)


def role_required(*allowed_roles):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            if "user_id" not in session:

                flash(
                    "Please login to continue.",
                    "error"
                )

                return redirect(
                    url_for("portal.index")
                )

            if session.get("role") not in allowed_roles:

                flash(
                    "You don't have permission to access this page.",
                    "error"
                )

                return redirect(
                    url_for("dashboard.dashboard")
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator