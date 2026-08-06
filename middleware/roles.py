from functools import wraps

from flask import session, redirect


def role_required(*allowed_roles):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            if "role" not in session:
                return redirect("/login")

            if session["role"] not in allowed_roles:
                return "Access Denied", 403

            return func(*args, **kwargs)

        return wrapper

    return decorator