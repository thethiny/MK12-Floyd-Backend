import os
import uuid
import requests

from datetime import datetime, timedelta

from src.models.mk12.access import Access, Profile
from src.models.mk12.account import Account
from src.models.mk12.envelope import ssc_envelope_response_from_dict
from src.models.mk12.responses.error import HydraError
from src.models.mk12.wb.player_modules import PlayerModules
from src.utils import prevent_over_refresh

class MK12API:
    ROOT_URL = "https://k1-api.wbagora.com"
    SSC_URL = ROOT_URL + "/ssc"
    INVOKE_URL = SSC_URL + "/invoke"
    HYDRA_KEY = os.environ.get("MK12_API_KEY", "")
    CURRENT_GAME_VERSION = "0.294"

    def __init__(self, steam_key: str = "", wb_creds: dict = {}):
        self.steam_key = ""
        self.wb_creds = {}
        self.access_token = ""

        if steam_key:
            self.setup_steam(steam_key)
        if wb_creds:
            self.setup_wb(wb_creds)

        self.refresh_required = True
        self.refresh_time = datetime(1970, 1, 1)
        self.lock = None

    def set_mutex_lock(self, lock):
        self.lock = lock

    def setup_steam(self, steam_key: str):
        if not steam_key:
            raise ValueError(f"Missing Steam Key")
        if not steam_key.startswith("080"):
            raise ValueError(f"Invalid Steam Key Version {steam_key[:4]}")

        self.steam_key = steam_key.strip()

    def setup_wb(self, wb_creds: dict):
        raise NotImplementedError(self.setup_wb.__name__)

    def make_url(self, url: str, *resources: str):
        url = self.ROOT_URL.rstrip("/") + "/" + url.lstrip("/")
        resources_string = "/".join(r.lstrip("/") for r in resources).rstrip("/")
        if resources_string:
            url += "/" + resources_string
        return url

    def make_invoke_url(self, url: str, *resources: str):
        url = self.INVOKE_URL.rstrip("/") + "/" + url.lstrip("/")
        resources_string = "/".join(r.lstrip("/") for r in resources).rstrip("/")
        if resources_string:
            url += "/" + resources_string
        return url

    @prevent_over_refresh()
    def login(self):        
        url = self.make_url("access")
        body = {
            "auth": {
                "fail_on_missing": False, "steam": self.steam_key
            },
            "options": [
                "configuration",
                "achievements",
                "account",
                "profile",
                "notifications",
                "maintenance",
                "wb_network",
            ],
        }

        headers = self.make_headers_dict(False, False, False)
        headers.update({
            "X-NRS-Kore-Response": "true",
        })

        print("MK Logging In")
        resp = requests.post(url, json=body, headers=headers)

        if int(resp.status_code)//100 != 2:
            raise ValueError(f"Received Error {resp.status_code}: {resp.json()}")

        resp_data: Access = resp.json()

        self.access_token = resp_data["token"]
        if not self.access_token:
            raise ValueError(f"Response 200 but token empty!")

        self.account = resp_data["account"]
        self.profile = resp_data["profile"]
        self.maintenance = resp_data["maintenance"]
        self.notifications = resp_data["notifications"]
        self.wb_network = resp_data["wb_network"]
        self.wb_authorization_code = self.wb_network["network_token"]
        self.refresh_required = False
        mk_ident = self.account["identity"]["alternate"].get("steam", list(self.account["identity"]["alternate"].keys())[0])[0]
        print("MK Identity:", mk_ident["username"])

    def make_headers_dict(self, envelope: bool = True, game_version: bool = True, auth_required: bool = True):        
        headers = {
            "X-Hydra-Api-Key": self.HYDRA_KEY,
            "Content-Type": "application/json",
        }

        if auth_required and self.access_token:
            headers["X-Hydra-Access-Token"] = self.access_token

        if envelope:
            headers["X-SSC-Envelope-Response"] = "true"
            headers["X-SSC-Transaction"] = str(uuid.uuid4())

        if game_version:
            headers["X-Nrs-Client-Version"] = self.CURRENT_GAME_VERSION

        return headers

    def api_call(self, url, body: dict = {}, headers: dict = {}, method="GET"):
        if method.lower() == "get":
            caller = requests.get
        elif method.lower() == "post":
            caller = requests.post
        elif method.lower() == "put":
            caller = requests.put
        else:
            raise ValueError(f"Unsupported Method {method.upper()}")

        call_dict = {}

        if body:
            call_dict["json"] = body
        if not headers:
            headers = self.make_headers_dict()

        call_dict["headers"] = headers

        resp = caller(url, **call_dict)

        return resp

    def validate_resp_auth(self, resp: requests.Response):
        if resp.status_code // 100 != 2:
            error = HydraError.from_dict(resp.json())
            print(f"Hydra Error {resp.status_code} ({error.hydra_error}): {error.msg}")
            if resp.status_code in [401, 403]:
                self.refresh_required = True
                self.refresh()
                return False
        return True

    def refresh(self, lock = None):
        lock = lock or self.lock
        if not lock:
            return self.login()

        with lock:
            if self.refresh_required:
                return self.login()

    def get_profile(self, profile_id: str):
        url = self.make_url("profiles", profile_id)

        resp = self.api_call(url)
        if not self.validate_resp_auth(resp):
            return self.get_profile(profile_id)

        if resp.status_code // 100 != 2:
            if resp.status_code == 404:
                error = HydraError.from_dict(resp.json())
                raise ValueError(f"Profile {profile_id} not found!")

        profile: Profile = resp.json()

        return profile

    def get_account(self, account_id: str):
        url = self.make_url("accounts", account_id)

        resp = self.api_call(url)
        if not self.validate_resp_auth(resp):
            return self.get_account(account_id)

        if resp.status_code // 100 != 2:
            if resp.status_code == 404:
                error = HydraError.from_dict(resp.json())
                raise ValueError(f"Account {account_id} not found!")

        account: Account = resp.json()

        return account

    def get_mk_id_from_wb(self, user_id: str, platform: str):
        if not user_id or not platform:
            raise ValueError(f"`user_id` and `platform` must be provided")

        url = self.make_invoke_url(f"player_modules_by_auth_id?auth_type={platform}&ids={user_id}")
        headers = self.make_headers_dict(envelope=True, game_version=False, auth_required=False)

        print(f"Fetching wbid for {user_id} on {platform}")
        resp = self.api_call(url, headers=headers)
        if not self.validate_resp_auth(resp):
            return self.get_mk_id_from_wb(user_id, platform)

        envelope, response = ssc_envelope_response_from_dict(resp.json(), PlayerModules)

        return response
