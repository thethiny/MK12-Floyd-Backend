from datetime import datetime
from typing import Optional
from msal import PublicClientApplication, SerializableTokenCache
import os
import requests

from src.utils import prevent_over_refresh

class Xbox:
    TOKEN_CACHE_PATH = "xbox_tokens.json"
    AUTHORITY_URL = "https://login.microsoftonline.com/consumers"
    PEOPLE_HUB_SEARCH_URL = "https://peoplehub.xboxlive.com/users/me/people/search/decoration/detail,preferredColor?q={gamertag}&maxItems=25"
    SCOPES = ["Xboxlive.signin", "Xboxlive.offline_access"]
    XBL_VERSION = "3.0"

    def __init__(self, client_id: str, token_cache_folder: str = ".", interactive_mode: bool = False):
        self.interactive_mode = interactive_mode
        self.cache = SerializableTokenCache()

        self.token_cache_file = os.path.join(token_cache_folder, self.TOKEN_CACHE_PATH)
        self.load_cache()

        self.app = PublicClientApplication(
            client_id, authority=self.AUTHORITY_URL, token_cache=self.cache
        )

        self.refresh_time = datetime(1970, 1, 1)
        self.available = False
        self.relogin()

    def save_cache(self):
        if self.cache.has_state_changed:
            with open(self.token_cache_file, "w") as f:
                f.write(self.cache.serialize())

    def load_cache(self):
        if os.path.exists(self.token_cache_file):
            print("Xbox Tokens exist!")
            with open(self.token_cache_file) as f:
                self.cache.deserialize(f.read())
        else:
            print("Xbox Tokens do not exist!")

    @prevent_over_refresh()
    def get_token(self):
        accounts = self.app.get_accounts()
        if accounts:
            print("Xbox Account logged in")
            resp = self.app.acquire_token_silent(self.SCOPES, accounts[0])
        else:
            self.available = False
            print("Xbox Account login required")
            if not self.interactive_mode:
                raise ValueError("Xbox account requires auth which is not available in non interactive mode!")
            resp =  self.app.acquire_token_interactive(self.SCOPES)

        if not resp or "access_token" not in resp:
            raise ValueError(f"Xbox Failed to authenticate!")

        ticket = self.get_user_token(resp["access_token"])
        if not ticket:
            raise ValueError(f"Xbox Failed to get access token")
        user_token = ticket.get("Token")
        user_hash = ticket.get("DisplayClaims", {}).get("xui", [{}])[0].get("uhs")
        if not user_hash:
            raise ValueError(f"Invalid User Hash returned from server")

        xsts_ticket = self.get_xsts_token(user_token)

        if not xsts_ticket:
            raise ValueError(f"Xbox Failed to get xsts token")

        xsts_token = xsts_ticket.get("Token")
        xbl_token = f"XBL{self.XBL_VERSION} x={user_hash};{xsts_token}"

        self.available = True
        return xbl_token

    def get_headers(self, token: str = ""):
        token = token or self.xbl_token
        headers = {
            "x-xbl-contract-version": str(int(float(self.XBL_VERSION))),
            "Content-Type": "application/json",
            "Authorization": token,
            "Accept-Language": "en-us",
        }

        return headers

    def relogin(self):
        self.xbl_token = self.get_token()
        if self.xbl_token:
            self.save_cache()

    def get_user_token(self, access_token):
        ticket_data = {
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT",
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": f"d={access_token}",
            },
        }

        headers = {"x-xbl-contract-version": "1", "Content-Type": "application/json"}

        resp = requests.post(
            url="https://user.auth.xboxlive.com/user/authenticate",
            json=ticket_data,
            headers=headers,
        )

        if resp.status_code == 200:
            return resp.json()
        else:
            print(resp.json())
            raise ValueError(f"Get User Token Error: {resp.status_code}")

    def get_xsts_token(self, user_token: str):
        ticket_data = {
            "RelyingParty": "http://xboxlive.com",
            "TokenType": "JWT",
            "Properties": {"UserTokens": [user_token], "SandboxId": "RETAIL"},
        }

        headers = {"x-xbl-contract-version": "1", "Content-Type": "application/json"}

        url = "https://xsts.auth.xboxlive.com/xsts/authorize"
        resp = requests.post(url, json=ticket_data, headers=headers)

        if resp.status_code == 200:
            return resp.json()
        else:
            print(resp.json())
            raise ValueError(f"Get XSTS Token Error: {resp.status_code}")

    def search_users(self, gamertag: str):
        headers = self.get_headers()
        resp = requests.get(
            self.PEOPLE_HUB_SEARCH_URL.format(gamertag=gamertag), headers=headers
        )

        if resp.status_code in [400, 401, 403]:
            self.relogin()
            return self.search_users(gamertag)

        if resp.status_code // 100 != 2:
            print(resp.json())
            raise ValueError(f"Search Users Error {resp.status_code}")

        return resp.json()

    def yield_search_xuids(self, results: dict):
        for user in results.get("people", []):
            xuid = user.get("xuid", "")
            gamertag = user.get("gamertag", "")
            modern_gamertag = user.get("modernGamertag", "")
            unique_gamertag = user.get("uniqueGamertag", "")
            yield xuid, gamertag

    def get_xuid_by_gamertag(self, gamertag: str) -> Optional[str]:
        results = self.search_users(gamertag)
        for xuid, gt in self.yield_search_xuids(results):
            if gamertag.lower().strip() == gt.lower().strip():
                return xuid.strip()
