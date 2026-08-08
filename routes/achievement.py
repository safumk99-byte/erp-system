from flask import Blueprint

from middleware.auth import login_required
from middleware.roles import role_required

from services.achievement_service import (
    list_achievements,
    add_achievement,
    edit_achievement,
    approve_achievement,
    reject_achievement
)


achievement = Blueprint(
    "achievement",
    __name__
)


@achievement.route("/achievements")
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def achievement_list():

    return list_achievements()


@achievement.route(
    "/achievements/add",
    methods=["GET", "POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def create_achievement():

    return add_achievement()


@achievement.route(
    "/achievements/<int:id>/edit",
    methods=["GET", "POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def edit_achievement_submission(id):

    return edit_achievement(id)


@achievement.route(
    "/achievements/<int:id>/approve",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def approve_achievement_submission(id):

    return approve_achievement(id)


@achievement.route(
    "/achievements/<int:id>/reject",
    methods=["POST"]
)
@login_required
@role_required(
    "institution_admin",
    "staff"
)
def reject_achievement_submission(id):

    return reject_achievement(id)