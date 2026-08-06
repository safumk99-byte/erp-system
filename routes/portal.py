from flask import Blueprint, render_template

portal = Blueprint("portal", __name__)


@portal.route("/")
def index():

    return render_template("portal/index.html")