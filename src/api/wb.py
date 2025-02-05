import datetime
import os
import re
from typing import Optional, Union
import requests

from src.models.wb_network.auth import WBAuthResult
from src.models.wb_network.invitations import PublicAccount, WBProfileCard, WBSearchResult
from src.utils import prevent_over_refresh

class WBAPI:
    ROOT_URL = "https://prod-network-api.wbagora.com"
    SEARCH_URL = "accounts/lookup"
    INVITE_URL = "friends/me/invitations"
    AUTH_URL = "sessions/auth"

    API_KEY = os.environ.get("WB_API_KEY", "")

    def __init__(self, access_token: str = "", refresh_token: str = "", authorization_code: str = ""): # Can't use api to sign in
        if not access_token and not refresh_token and not authorization_code:
            raise ValueError(f"A type of token must be specified!")

        if sum(bool(a) for a in [access_token, refresh_token, authorization_code]) > 1:
            raise ValueError("More than one auth method specified!")

        self.access_token = self.refresh_token = ""
        self.account = None
        self.refresh_required = True
        self.refresh_time = datetime.datetime(1970, 1, 1)
        self.token = None
        self.lock = None

        if access_token:
            self.access_token = access_token
            self.set_headers()
        elif refresh_token:
            self.refresh_token = refresh_token
            self.login(refresh_token, grant="refresh_token")
        elif authorization_code:
            self.refresh_token = self.login(authorization_code, grant="auth")

    def set_headers(self, access_token: str = ""):
        if not access_token:
            access_token = self.access_token
        self.headers = {
            "Content-Type": "application/json",
            "X-Hydra-API-Key": self.API_KEY,
            "X-Hydra-Access-Token": access_token,
        }

    def set_mutex_lock(self, lock):
        self.lock = lock

    def refresh(self, lock = None):
        lock = lock or self.lock
        if not lock:
            return self.login(self.refresh_token, "refresh_token")

        with lock:
            if self.refresh_required:
                self.login(self.refresh_token, "refresh_token")

    @prevent_over_refresh()
    def login(self, grant_token: str, grant: str = "refresh_token"):
        url = self.make_url(self.AUTH_URL, "token")

        params = {"options": "account"}
        if grant == "auth":
            grant = "authorization_code"
            params = {
                "options[]": ["account", "refresh_token"]
            }

        print(f"WB Login!")
        resp = requests.post(
            url,
            headers={
                "X-Hydra-Api-Key": self.API_KEY,
            },
            params = params,
            json={
                "grant_type": grant,
                "code": grant_token
            },
        )

        if resp.status_code//100 != 2:
            print(resp.json())
            raise ValueError(resp.status_code)

        response: WBAuthResult = resp.json()
        access_token = response.get("access_token")
        if not access_token:
            raise ValueError(f"Empty response while refresh: {response}")

        self.access_token = access_token
        self.account = response["account"]
        self.set_headers()

        print(f"WB Identity: {self.account['username']}")

        new_refresh_token = response.get("refresh_token", "")
        if new_refresh_token:
            self.refresh_token = new_refresh_token

        self.refresh_required = False

        return self.refresh_token

    def make_url(self, url: str, *resources: str):
        url = self.ROOT_URL.rstrip("/") + "/" + url.lstrip("/")
        resources_string = "/".join(r.lstrip("/") for r in resources).rstrip("/")
        if resources_string:
            url += "/" + resources_string
        return url

    def check_refresh_requirement(self, resp: requests.Response):
        if resp.status_code in [400, 401, 403]:
            self.refresh_required = True
            self.refresh()
            return False
        return True

    def search(self, user: str) -> Optional[PublicAccount]:
        url = self.make_url(self.SEARCH_URL)

        is_email = re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", user) is not None
        search_type = "email" if is_email else "username"
        print("Search by", search_type)

        resp = requests.get(
            url.format(user=user),
            headers=self.headers,
            params={"expand_localization": True, "type": search_type, "value": user},
        )

        if not self.check_refresh_requirement(resp):
            return self.search(user)

        if not resp.status_code // 100 == 2:
            print(resp.json())
            if resp.status_code == 404:
                return None
            raise ValueError(resp.status_code)

        return resp.json()

    def search_by(self, user: Union[str, int], where: str, delete_afterwards: bool = False) -> Optional[PublicAccount]:
        if where == "incoming":
            func = self.get_incoming
        elif where == "outgoing":
            func = self.get_outgoing
            delete_afterwards = False # Can't decline, only cancel # TODO: Change later with todo_afterwards
        elif where in ["friends", "friend"]:
            func = self.get_friends
            delete_afterwards = False # Can't decline, only remove
        else:
            raise ValueError(f"What is {where}?")

        try:
            resp = func(state="open")
        except ValueError:
            return None

        try:
            int_name = int(user)
        except ValueError:
            int_name = None

        if int_name is not None:
            return resp["results"][int_name]["account"]

        if isinstance(user, str):
            for friend in resp["results"]:
                if friend["account"]["username"].strip().lower() == user.strip().lower():
                    if delete_afterwards:
                        try:
                            self.decline_request(friend["id"])
                        except ValueError:
                            print(f"Friend found but couldn't decline {friend['id']}")
                    return friend["account"]
        else:
            raise TypeError(f"What did you send? user with type {type(user)}???")

        return None

    def get_incoming(self, state: str = "open", sort: bool = True) -> WBSearchResult:
        """
        state: one of `open` `accepted` `cancelled` `declined`
        """
        # Returned id is the invitation id and has sent_from and sent_to which can be used to identify the user's id instead of public id
        url = self.make_url(self.INVITE_URL, "incoming")
        # state = open
        resp = requests.get(
            url,
            headers=self.headers,
            params={
                "page": 1,
                "page_size": 200,
                "state": state,
                "expand_localization": True
            }
        )

        if not self.check_refresh_requirement(resp):
            return self.get_incoming(state)

        if not resp.status_code // 100 == 2:
            print(resp.json())
            raise ValueError(resp.status_code)

        data: WBSearchResult = resp.json()

        if sort:
            return self._sort_results(data)

        return data

    def get_outgoing(self, state: str = "open", sort: bool = True) -> WBSearchResult:
        # Returned id is the invitation id and has sent_from and sent_to which can be used to identify the user's id instead of public id
        url = self.make_url(self.INVITE_URL, "outgoing")
        resp = requests.get(
            url,
            headers=self.headers,
            params={
                "page": 1,
                "page_size": 200,
                "state": state,
                "expand_localization": True,
            },
        )

        if not self.check_refresh_requirement(resp):
            return self.get_outgoing(state)

        if not resp.status_code // 100 == 2:
            print(resp.json())
            raise ValueError(resp.status_code)

        data: WBSearchResult = resp.json()

        if sort:
            return self._sort_results(data)

        return data

    def get_friends(self, sort: bool = True, **kwargs) -> WBSearchResult:
        url = self.make_url("friends", "me")
        resp = requests.get(
            url,
            headers=self.headers,
            params={
                "page": 1,
                "page_size": 200,
                "expand_localization": True,
            },
        )

        if not self.check_refresh_requirement(resp):
            return self.get_friends()

        if not resp.status_code // 100 == 2:
            print(resp.json())
            raise ValueError(resp.status_code)

        data: WBSearchResult = resp.json()

        if sort:
            return self._sort_results(data)

        return data

    def decline_request(self, invite_id: str):
        invite_id = invite_id.strip().lower()
        url = self.make_url(self.INVITE_URL, invite_id, "decline")

        resp = requests.put(
            url, headers=self.headers, params={"expand_localizations": True}
        )

        if not self.check_refresh_requirement(resp):
            return self.decline_request(invite_id)

        if not resp.status_code // 100 == 2:
            print(resp.json())
            raise ValueError(resp.status_code)

        data: WBProfileCard = resp.json()
        if data["id"] != invite_id or data["state"] != "declined":
            print(f"Failed to decline invitation {id}!")
            raise ValueError(data["id"] + "=" + data["state"])

        return True

    def _sort_results(self, data: WBSearchResult) -> WBSearchResult:
        data["results"] = sorted(
            data["results"], key=lambda x: x["created_at"], reverse=True
        )

        return data


# API Ref from MK12 Bin
# .ecode:000000014622AC38                 text "UTF-16LE", 'avatar',0
# .ecode:000000014622AC48                 text "UTF-16LE", 'game_links',0
# .ecode:000000014622AC60                 text "UTF-16LE", 'owner_id',0
# .ecode:000000014622AC78                 text "UTF-16LE", 'contact_id',0
# .ecode:000000014622AC90                 text "UTF-16LE", '?',0
# .ecode:000000014622AC98                 text "UTF-16LE", '{0}={1}&',0
# .ecode:000000014622ACB0                 text "UTF-16LE", 'page',0
# .ecode:000000014622ACC0                 text "UTF-16LE", 'page_size',0
# .ecode:000000014622ACD8                 text "UTF-16LE", 'authorization_code',0
# .ecode:000000014622AD00                 text "UTF-16LE", 'grant_type',0
# .ecode:000000014622AD18                 text "UTF-16LE", 'code',0
# .ecode:000000014622AD28                 text "UTF-16LE", 'sessions/auth/token',0
# .ecode:000000014622AD50                 text "UTF-16LE", '{0}?user_code={1}&hidden={2}',0
# .ecode:000000014622AD90                 text "UTF-16LE", 'device_name',0
# .ecode:000000014622ADA8                 text "UTF-16LE", 'user_flow',0
# .ecode:000000014622ADC0                 text "UTF-16LE", 'sessions/device',0
# .ecode:000000014622ADE0                 text "UTF-16LE", 'access_token',0
# .ecode:000000014622AE00                 text "UTF-16LE", 'sdk',0
# .ecode:000000014622AE08                 text "UTF-16LE", 'realtime',0
# .ecode:000000014622AE20                 text "UTF-16LE", 'servers',0
# .ecode:000000014622AE30                 text "UTF-16LE", 'accounts/lookup',0
# .ecode:000000014622AE50                 text "UTF-16LE", 'friends/me/unfriend/{0}',0
# .ecode:000000014622AE80                 text "UTF-16LE", 'account_id',0
# .ecode:000000014622AE98                 text "UTF-16LE", 'friends/me/invitations',0
# .ecode:000000014622AED0                 text "UTF-16LE", 'friends/me/invitations/{0}/accept',0
# .ecode:000000014622AF20                 text "UTF-16LE", 'friends/me/invitations/{0}/decline',0
# .ecode:000000014622AF70                 text "UTF-16LE", 'friends/me/invitations/incoming',0
# .ecode:000000014622AFB0                 text "UTF-16LE", 'social/me/block/{0}',0
# .ecode:000000014622AFD8                 text "UTF-16LE", 'social/me/unblock/{0}',0
# .ecode:000000014622B008                 text "UTF-16LE", 'realtime/config',0
# .ecode:000000014622B028                 text "UTF-16LE", 'accounts/me',0
# .ecode:000000014622B040                 text "UTF-16LE", 'image_url',0
