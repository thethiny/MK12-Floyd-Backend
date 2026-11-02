import base64
import json
import os
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote

import requests
from steam.steamid import SteamID

from src.api.errors import PlatformLookupError
from src.utils import init_secrets

from src.api.xbl import Xbox
from src.api.psn_web import PSNAuth
from src.api.psn_service import PSNService

init_secrets()
try:
    xbox_client = Xbox(os.environ.get("OPSP_XR_CLIENT_ID", ""), token_cache_folder="db")
except Exception as e:
    xbox_client = None
    print(f"Xbox client failed to instantiate due to: {e}")

try:
    psn_service_client = PSNService(token_cache_folder="db")
except Exception as e:
    psn_service_client = None
    print(f"PSN service client failed to instantiate due to: {e}")

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
    return get_psn_user_id_service(user)

def get_psn_user_id_service(user: str):
    user = user.strip()
    print(f"Getting PSN Profile (service) for {user}")
    if not psn_service_client or not psn_service_client.available:
        raise ValueError("PSN auth is offline. Please notify thethiny to fix: npsso expired.")
    return psn_service_client.get_account_id_by_online_id(user)

def get_psn_user_id_flipscreen(user: str):
    user = user.strip()
    print(f"Getting PSN Profile (flipscreen) for {user}")
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

def get_psn_web_user_id(token: str):
    token = token.strip()
    token_data = json.loads(token)
    npsso: str = token_data.get("npsso", "")
    if not npsso:
        raise ValueError("Missing npsso in token!")
    
    tokens = PSNAuth.exchange_npsso(npsso)
    id_token = tokens.to_dict().get("id_token", "")
    if not id_token:
        raise ValueError("Missing id_token in tokens!")
    
    # tokens is a jwt, extract from it the username as online_id and the id as sub
    # extract jwt
    jwt = id_token.split(".")[1]
    if not jwt:
        raise ValueError("Missing jwt in id_token!")
    jwt_payload = json.loads(base64.urlsafe_b64decode(jwt + "=="))
    online_id: str = jwt_payload.get("online_id", "")
    sub: str = jwt_payload.get("sub", "")
    if not online_id or not sub:
        raise ValueError("Missing online_id or sub in jwt payload!")
    
    return {
        "username": online_id,
        "user_id": sub
    }

def is_valid_steam_id(steam_id):
    return SteamID(steam_id) != 0

def sanitize_steam_user_id(steam_id: str):
    return SteamID(SteamID(steam_id).as_32)

STEAM_COMMUNITY_URL = "https://steamcommunity.com"
STEAM_HTTP_TIMEOUT = 15
STEAM_PROFILE_URL_RE = re.compile(r"^https?://steamcommunity\.com/(?P<type>profiles|id)/(?P<value>[^/?#]+)", re.IGNORECASE)
STEAM_CONTACT_ERROR = "Steam lookup failed. Please contact thethiny to fix."


def fetch_steam_vanity_id(vanity: str) -> str:
    """Resolve a Steam vanity name to a steam64 using the profile XML endpoint."""
    url = f"{STEAM_COMMUNITY_URL}/id/{quote(vanity, safe='')}"
    try:
        resp = requests.get(url, params={"xml": 1}, timeout=STEAM_HTTP_TIMEOUT)
    except requests.exceptions.RequestException as e:
        print(f"Steam lookup for {vanity} failed to connect: {e!r}")
        raise PlatformLookupError(500, STEAM_CONTACT_ERROR)

    if resp.status_code == 429:
        print(f"Steam lookup for {vanity} was rate limited (429)")
        raise PlatformLookupError(429, "Try again later")
    if resp.status_code == 404:
        raise PlatformLookupError(404, f"Couldn't find steam user {vanity}")
    if resp.status_code != 200:
        print(f"Steam lookup for {vanity} returned unexpected status {resp.status_code}")
        raise PlatformLookupError(500, STEAM_CONTACT_ERROR)

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        print(f"Steam lookup for {vanity} returned unparsable XML: {e!r}")
        raise PlatformLookupError(500, STEAM_CONTACT_ERROR)

    steam_id = (root.findtext("steamID64") or "").strip()
    if steam_id:
        return steam_id
    if root.findtext("error"):  # Steam answers 200 with <error> when the profile doesn't exist
        raise PlatformLookupError(404, f"Couldn't find steam user {vanity}")

    print(f"Steam lookup for {vanity} returned XML without a steamID64")
    raise PlatformLookupError(500, STEAM_CONTACT_ERROR)


def get_steam_user_id(user: str) -> str:
    user = user.strip()
    url_match = STEAM_PROFILE_URL_RE.match(user)
    if user.lower().startswith("http"):
        if not url_match:
            raise PlatformLookupError(404, f"Couldn't find steam user {user}")
        if url_match["type"].lower() == "id":
            return fetch_steam_vanity_id(url_match["value"])
        user = url_match["value"]  # /profiles/<id> carries the id, no request needed

    steam_id = str(SteamID(user)).strip()

    if steam_id and steam_id != "0":
        # recreate steam_id for users with old profiles
        return str(sanitize_steam_user_id(steam_id).as_64)

    return fetch_steam_vanity_id(user)

if __name__ == "__main__":
    print(get_steam_user_id("76561199811000896"))
