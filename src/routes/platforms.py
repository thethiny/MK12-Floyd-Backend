from typing import Callable
from flask import current_app, request, jsonify, Blueprint

from src.api.auth import auth_epic
from src.api.user_ids import get_psn_user_id, get_steam_user_id, get_xbox_xuid

platform_bp = Blueprint("platforms", __name__)


def sanitize_platform(platform: str, wb: bool = False):
    platform = platform.strip().lower()
    if platform in ["psn", "ps4"]:
        platform = "ps5"
    elif platform in ["xb1", "x360", "wingdk", "xbl"]:
        platform = "xsx"
    elif platform in ["eos", "epicgames", "egs"]:
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


def auth_platform(platform_func: Callable,):
    code = request.args.get("code", "").strip()
    if not code:
        return {"error": "Missing `code` in query!"}, 400

    try:
        user_id, username = platform_func(code.strip())
    except ValueError:
        return {"error": f"Server Error Authenticating {code}"}, 400

    if not user_id:
        return {"error": f"Couldn't get user profile from auth"}, 404
    
    if not username:
        print(f"Warning: Missing username from {platform_func}")

    return dict(user_id=user_id, username=username), 200


@platform_bp.get("/ps5")
@platform_bp.get("/ps4")
@platform_bp.get("/psn")
def get_psn():
    return get_platform(get_psn_user_id)


@platform_bp.get("xsx")
@platform_bp.get("xb1")
@platform_bp.get("xbl")
@platform_bp.get("wingdk")
@platform_bp.get("gdk")
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
    
    platform = sanitize_platform(platform, wb=True)

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
        if x_u[0].get_json().get("user_id", -1) == -1:
            return jsonify(error="Gamertag support is inactive. Please lookup your Xbox Live User ID (XUID) and use it instead."), 400
        return x_u
    elif platform.startswith("auth_"):
        provider = platform.split("_", 1)[-1].strip()
        
        args = {
            "code": username,
            "provider": provider,
        }
        
        with current_app.test_request_context("/auth", query_string=args):
            return auth_any()
        # resp, status_code = auth_any()
                
        # return jsonify(resp), status_code

    return jsonify(error=f"Unsupported platform `{platform}`"), 400

@platform_bp.get("/auth/<string:provider>")
@platform_bp.get("/auth")
def auth_any(provider: str = ""):
    provider = provider.strip()
    if not provider:
        provider = request.args.get("provider", "").strip()
    provider = sanitize_platform(provider)
    
    if provider == "epic":
        user_dict, status_code = auth_platform(auth_epic)
    else:
        return jsonify(error=f"Unsupported Auth Provider {provider}"), 400
    
    user_dict["provider"] = provider
    return jsonify(user_dict), status_code
