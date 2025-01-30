import yaml
import os
from flask import Flask, request, jsonify

from src.utils.floyd import get_floyd_data, get_floyd_maps, parse_floyd_data

try:
    with open("secrets.yaml", encoding="utf-8") as f:
        secrets = yaml.safe_load(f)
        steam_key = secrets["creds"]["steam"]
        mk12_key = secrets["keys"]["mk"]
        wb_key = secrets["keys"]["wb"]
        os.environ.update(
            {
                "MK12_API_KEY": mk12_key,
                "WB_API_KEY": wb_key,
            }
        )
        # wb_refresh = secrets["creds"]["wb"]
except FileNotFoundError:
    steam_key = os.environ.get("STEAM_KEY")
    if not steam_key:
        raise ValueError(f"`steam_key` secret missing!")

from src.api.mk12 import MK12API
from src.api.user_ids import get_psn_user_id, get_steam_user_id
from src.api.wb import WBAPI
from src.routes.platforms import find_any, platform_bp

api = MK12API(steam_key=steam_key)
api.login()
wb_api = WBAPI(authorization_code=api.wb_authorization_code) # Auth code is one time use

app = Flask("Floyd Tracker")
app.register_blueprint(platform_bp, url_prefix="/platforms")

@app.route("/floyd")
def main():
    params = request.args

    platform = params.get("platform")
    username = params.get("username")

    if not username or not platform:
        return jsonify(error="`platform` and `username` are both required!"), 400

    if platform == "wb_network":
        user_id = wb_api.search(username.strip())["public_id"]
    else:
        user_id, status_code = find_any()
        if status_code != 200:
            return user_id, status_code # jsonify
        user_id = (user_id.json or {}).get("user_id")

    if not user_id:
        return jsonify(error=f"Couldn't find user {username}"), 404

    modules = api.get_mk_id_from_wb(user_id, platform)["player_modules"]
    if not len(modules):
        return jsonify(error=f"User {username} was found but no id was returned from mk servers. If you're on Nintendo Switch, sorry."), 404

    player_module = modules[0]
    hydra_id = player_module["hydra_id"]
    hydra_platform = player_module["platform"]
    platform_name = player_module["platform_name"]
    hydra_name = player_module["wbpn_name"]

    profile = api.get_profile(hydra_id)
    floyd_data = get_floyd_data(profile)
    parsed_data = parse_floyd_data(floyd_data, hydra_platform)
    floyd_map = get_floyd_maps()

    user_obj = {
        "username": username,
        "user_id": user_id,
        "user_platform": platform,
        "hydra": {
            "hydra_linked_platform": hydra_platform,
            "hydra_platform_username": platform_name,
            "username": hydra_name,
            "user_id": hydra_id,
        }
    }

    parsed_data = {
        "parsed": parsed_data["parsed"],
        "raw": {floyd_map[f"profilestat{k}"]: v for k, v in parsed_data["raw"].items()},
        "hints": parsed_data["hints"],
    }
    
    return jsonify(user=user_obj, data=parsed_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
