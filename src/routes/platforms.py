from typing import Callable
from flask import request, jsonify, Blueprint

from src.api.user_ids import get_psn_user_id, get_steam_user_id

platform_bp = Blueprint("platforms", __name__)


def get_platform(platform_func: Callable):
    username = request.args.get("username", "").strip()
    if not username:
        return jsonify(error="Missing `username` in query!"), 400

    try:
        user = platform_func(username.strip())
    except ValueError:
        return jsonify(error=f"Server Error retreiving username {username}"), 400

    if not user:
        return jsonify(error=f"Couldn't find user {user}"), 404

    return jsonify(user_id=user), 200


@platform_bp.get("/ps5")
@platform_bp.get("/ps4")
@platform_bp.get("/psn")
def get_psn():
    return get_platform(get_psn_user_id)


@platform_bp.get("/steam")
def get_steam():
    return get_platform(get_steam_user_id)


@platform_bp.get("/hydra")
def get_hydra():
    return jsonify(error="Not yet implemented"), 503


@platform_bp.get("/find")
def find_any():
    username = request.args.get("username", "").strip()
    if not username:
        return jsonify(error="Missing `username` in query!"), 400

    platform = request.args.get("platform", "").strip().lower()
    if not platform:
        return jsonify(error="Missing `platform` in query!"), 400

    if platform == "psn":
        return get_psn()
    elif platform == "steam":
        return get_steam()
    elif platform == "hydra":
        return get_hydra()

    return jsonify(error=f"Unsupported platform `{platform}`"), 400
