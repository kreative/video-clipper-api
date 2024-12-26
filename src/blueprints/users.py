from flask import Blueprint, g, request

from src.constants.status_codes import ACCEPTED, NOT_FOUND, UNAUTHORIZED
from src.services.kreative_id import get_info_for_accounts
from src.services.user import get_user_by_id, update_user
from src.services.videos import add_new_video, delete_video, get_videos_for_user
from src.utils.auth import authorize

users_blueprint = Blueprint("users", __name__, url_prefix="/users")

@users_blueprint.route("/", methods=["GET"])
@authorize(lambda: g.has_base)
def get_user_route(user_id):
    user = get_user_by_id(g.ksn)

    if not user:
        NOT_FOUND

    id_account = get_info_for_accounts([user_id])
    account = id_account[0] if id_account else None

    return {
        "id": user.id,
        "markdown_template": user.markdown_template,
        "prompt": user.prompt,
        "account": account,
        "created_at": user.created_at,
    }


@users_blueprint.route("/", methods=["PUT"])
@authorize(lambda: g.has_base)
def update_user_route():
    markdown_template = request.json.get("markdown_template")
    prompt = request.json.get("prompt")

    updated_user = update_user(g.ksn, markdown_template, prompt)

    return {
        "id": updated_user.id,
        "markdown_template": updated_user.markdown_template,
        "prompt": updated_user.prompt,
        "created_at": updated_user.created_at,
    }


@users_blueprint.route("/videos", methods=["GET"])
def get_videos_for_user_route():
    videos = get_videos_for_user(g.ksn)

    if not videos or len(videos) == 0:
        return { "videos": [] }

    videos_dict = [video.to_dict() for video in videos]

    return { "videos": videos_dict }


@users_blueprint.route("/video", methods=["POST"])
@authorize(lambda: g.has_base)
def add_video_for_user_route():
    user = get_user_by_id(g.ksn)

    if not user:
        NOT_FOUND

    yt_link = request.json.get("yt_link")
    video = add_new_video(user_id, yt_link)

    return { "video": video.to_dict() }


@users_blueprint.route("/video/<int:video_id>", methods=["DELETE"])
@authorize(lambda: g.has_base)
def delete_video_route(video_id):
    video = get_video_by_id(video_id)

    if not video:
        NOT_FOUND

    if video.user_id != user_id:
        return UNAUTHORIZED

    delete_video(video_id)

    return ACCEPTED
