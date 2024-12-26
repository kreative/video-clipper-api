from flask import Blueprint
from src.utils.auth import authorize

videos_blueprint = Blueprint("videos", __name__, url_prefix="/videos")


@videos_blueprint.route("/", methods=["GET"])
@authorize()
