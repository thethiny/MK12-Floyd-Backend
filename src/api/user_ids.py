import os
import requests
from steam.steamid import SteamID, steam64_from_url

from src.utils import init_secrets

from src.api.xbl import Xbox

init_secrets()
try:
    xbox_client = Xbox(os.environ.get("OPSP_XR_CLIENT_ID", ""), token_cache_folder="db")
except Exception as e:
    xbox_client = None
    print(f"Xbox client failed to instantiate due to: {e}")

def get_xbox_xuid(user: str):
    if not xbox_client or not xbox_client.available:
        print("Xbox client was not active!")
        return -1
    try:
        gamertag = xbox_client.get_xuid_by_gamertag(user)
        if not gamertag:
            raise ValueError(404)
    except ValueError:
        raise ValueError(404)
    return gamertag.strip()

def get_psn_user_id(user: str):
    user = user.strip()
    print(f"Getting PSN Profile for {user}")
    url = "https://psn.flipscreen.games/search.php"
    resp = requests.get(url, params={
        "username": user
    })
    
    if resp.status_code//100 != 2:
        print(resp.json())
        raise ValueError(resp.status_code)
    
    user_id = resp.json().get("user_id", "")
    if not user_id:
        raise ValueError(f"Server returned empty user_id!")
    return user_id

def is_valid_steam_id(steam_id):
    return SteamID(steam_id) != 0

def sanitize_steam_user_id(steam_id: str):
    return SteamID(SteamID(steam_id).as_32)

def get_steam_user_id(user: str) -> str:
    if user.lower().startswith("http"):
        steam_id = str(steam64_from_url(user))
        if not steam_id or steam_id == "None":
            raise ValueError(f"Couldn't find user for {user}")
        return steam_id

    steam_id = str(SteamID(user)).strip()

    if steam_id and steam_id != "0":
        # recreate steam_id for users with old profiles
        steam_id = str(sanitize_steam_user_id(steam_id).as_64)
        return steam_id

    steam_id = str(SteamID.from_url(f"https://steamcommunity.com/id/{user}")) # type: ignore
    if not steam_id or steam_id == "None":
        raise ValueError(f"Couldn't find steam user {user}")

    return steam_id

if __name__ == "__main__":
    print(get_steam_user_id("76561199811000896"))
