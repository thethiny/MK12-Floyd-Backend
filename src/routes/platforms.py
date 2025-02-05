from typing import Callable
from flask import request, jsonify, Blueprint

from src.api.user_ids import get_psn_user_id, get_steam_user_id, get_xbox_xuid

platform_bp = Blueprint("platforms", __name__)


def sanitize_platform(platform: str, wb: bool = False):
    platform = platform.strip().lower()
    if platform in ["psn", "ps4"]:
        platform = "ps5"
    elif platform in ["xb1", "x360", "wingdk", "xbl"]:
        platform = "xsx"
    elif platform in ["eos", "epicgames"]:
        platform = "epic"
    elif wb and platform.startswith("wb_"):
        platform = "wb_network"
    return platform


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


@platform_bp.get("xsx")
@platform_bp.get("xb1")
@platform_bp.get("xbl")
@platform_bp.get("wingdk")
def get_xbox():
    return get_platform(get_xbox_xuid)

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
    
    platform = sanitize_platform(platform)

    if platform in ["psn", "ps4", "ps5"]:
        return get_psn()
    elif platform == "steam":
        return get_steam()
    elif platform == "hydra":
        return get_hydra()
    elif platform == "epic":
        return jsonify(user_id=username), 200
    elif platform == "xsx":
        if username.isdigit():
            return jsonify(user_id=username), 200
        x_u = get_xbox()
        if x_u == -1:
            return jsonify(error="Gamertag support is inactive. Please lookup your Xbox Live User ID (XUID) and use it instead."), 400
        return x_u

    return jsonify(error=f"Unsupported platform `{platform}`"), 400
