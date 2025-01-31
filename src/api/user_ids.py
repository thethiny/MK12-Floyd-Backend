import requests
from steam.steamid import SteamID, steam64_from_url

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

def get_steam_user_id(user: str) -> str:
    if user.lower().startswith("http"):
        steam_id = str(steam64_from_url(user))
        if not steam_id or steam_id == "None":
            raise ValueError(f"Couldn't find user for {user}")
        return steam_id
    
    steam_id = str(SteamID(user)).strip()

    if steam_id and steam_id != "0":
        return steam_id

    steam_id = str(SteamID.from_url(f"https://steamcommunity.com/id/{user}")) # type: ignore
    if not steam_id or steam_id == "None":
        raise ValueError(f"Couldn't find steam user {user}")

    return steam_id


if __name__ == "__main__":
    print(get_steam_user_id("76561199811000896"))
