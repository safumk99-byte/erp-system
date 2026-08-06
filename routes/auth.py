from flask import Blueprint

from services.auth_service import login_user, logout_user

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    return login_user()

@auth.route("/logout")
def logout():
    return logout_user()