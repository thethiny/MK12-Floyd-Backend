import base64
import json
import os
from datetime import datetime, timedelta
from typing import Optional

import requests

from src.api.psn_web import PSNAuth, PSNTokens
from src.utils import prevent_over_refresh


TOKEN_CACHE_PATH = "psn_tokens.json"
NPSSO_WARN_DAYS = 10  # warn when NPSSO expires within this many days

PSN_USER_PROFILE_URL = "https://us-prof.np.community.playstation.net/userProfile/v1/users/{online_id}/profile2"


class PSNService:
    """
    PSN service account - authenticates as a single PSN account and looks up
    other users by Online ID. Mirrors the Xbox/xbl.py pattern.

    Bootstrap once via reseed(npsso), then tokens are persisted to disk and
    auto-refreshed. Requires manual reseed every ~55 days when refresh token
    expires.
    """

    def __init__(self, token_cache_folder: str = "."):
        self.token_cache_file = os.path.join(token_cache_folder, TOKEN_CACHE_PATH)
        self.available = False
        self.refresh_time = datetime(1970, 1, 1)
        self._tokens: Optional[PSNTokens] = None
        self._npsso: Optional[str] = None
        self._npsso_expiry: Optional[datetime] = None
        self._access_token_expiry: Optional[datetime] = None
        self._refresh_token_expiry: Optional[datetime] = None

        self._load_cache()
        if self._tokens:
            self._check_and_refresh()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reseed(self, npsso: str, npsso_expires_in: Optional[int] = None):
        """Bootstrap fresh tokens from an NPSSO token. Call this once manually."""
        tokens = PSNAuth.exchange_npsso(npsso)
        self._npsso = npsso.strip()
        self._npsso_expiry = datetime.now() + timedelta(seconds=npsso_expires_in) if npsso_expires_in else None
        self._store_tokens(tokens)
        self.available = True
        print("PSN service account seeded successfully.")

    def get_account_id_by_online_id(self, online_id: str) -> str:
        """Look up a PSN account_id (sub) by Online ID using the service account."""
        if not self.available:
            self._reload_from_disk()

        if not self.available:
            raise ValueError("PSN auth is offline. Please notify thethiny to fix: npsso expired.")

        self._check_and_refresh()

        headers = {
            "Authorization": f"Bearer {self._tokens.access_token}",
        }
        url = PSN_USER_PROFILE_URL.format(online_id=online_id)
        resp = requests.get(url, params={"fields": "accountId,onlineId"}, headers=headers)

        if resp.status_code in [401, 403]:
            self._refresh_access_token()
            return self.get_account_id_by_online_id(online_id)

        if resp.status_code == 404:
            raise ValueError(404)

        if resp.status_code // 100 != 2:
            print(f"PSN profile API error {resp.status_code}: {resp.text}")
            raise ValueError(resp.status_code)

        data = resp.json()
        profile = data.get("profile", {})
        account_id = profile.get("accountId", "")
        if not account_id:
            raise ValueError(f"PSN returned no accountId for {online_id}")

        return account_id.strip()

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def _check_and_refresh(self):
        if not self._tokens:
            self.available = False
            return

        now = datetime.now()

        if self._refresh_token_expiry and now >= self._refresh_token_expiry:
            if self._npsso and (not self._npsso_expiry or now < self._npsso_expiry):
                print("PSN refresh token expired. Attempting reseed from stored NPSSO...")
                try:
                    self.reseed(self._npsso)
                    return
                except Exception as e:
                    print(f"PSN NPSSO reseed failed: {e}")
            self.available = False
            print("PSN refresh token has expired. Manual reseed required.")
            return

        if self._npsso_expiry:
            days_left = (self._npsso_expiry - now).days
            if days_left <= NPSSO_WARN_DAYS:
                print(f"WARNING: PSN NPSSO expires in {days_left} day(s). Reseed soon.")

        if self._access_token_expiry and now >= self._access_token_expiry:
            try:
                self._refresh_access_token()
            except ValueError:
                raise
            except Exception as e:
                self.available = False
                raise ValueError("PSN auth is offline. Please notify thethiny to fix: npsso expired.") from e

        self.available = True

    @prevent_over_refresh(minutes=10)
    def _refresh_access_token(self):
        if not self._tokens or not self._tokens.refresh_token:
            self.available = False
            raise ValueError("PSN auth is offline. Please notify thethiny to fix: npsso expired.")

        print("PSN access token expired, refreshing...")
        try:
            new_tokens = PSNAuth.refresh(self._tokens.refresh_token)
            self._store_tokens(new_tokens)
            print("PSN access token refreshed.")
        except Exception as e:
            print(f"PSN refresh token invalid: {e}")
            if self._npsso and (not self._npsso_expiry or datetime.now() < self._npsso_expiry):
                print("Attempting reseed from stored NPSSO...")
                try:
                    self.reseed(self._npsso)
                    print("PSN reseeded from stored NPSSO.")
                    return
                except Exception as e2:
                    print(f"PSN NPSSO reseed failed: {e2}")
            self.available = False
            raise ValueError("PSN auth is offline. Please notify thethiny to fix: npsso expired.")

    def _store_tokens(self, tokens: PSNTokens):
        self._tokens = tokens
        now = datetime.now()
        self._access_token_expiry = now + timedelta(seconds=tokens.expires_in - 60)
        self._refresh_token_expiry = now + timedelta(seconds=tokens.refresh_token_expires_in - 60)
        self._save_cache()

    def _reload_from_disk(self):
        print("PSN unavailable, checking disk for fresh tokens...")
        self._load_cache()
        if self._tokens:
            self._check_and_refresh()

    def _save_cache(self):
        if not self._tokens:
            return
        data = self._tokens.to_dict()
        data["access_token_expiry"] = self._access_token_expiry.isoformat() if self._access_token_expiry else None
        data["refresh_token_expiry"] = self._refresh_token_expiry.isoformat() if self._refresh_token_expiry else None
        data["npsso"] = self._npsso
        data["npsso_expiry"] = self._npsso_expiry.isoformat() if self._npsso_expiry else None
        with open(self.token_cache_file, "w") as f:
            json.dump(data, f)

    def _load_cache(self):
        if not os.path.exists(self.token_cache_file):
            print("PSN token cache not found. Reseed required.")
            return

        print("PSN token cache found, loading...")
        with open(self.token_cache_file) as f:
            data = json.load(f)

        self._tokens = PSNTokens.from_dict(data)
        self._npsso = data.get("npsso")
        self._npsso_expiry = (
            datetime.fromisoformat(data["npsso_expiry"])
            if data.get("npsso_expiry") else None
        )
        self._access_token_expiry = (
            datetime.fromisoformat(data["access_token_expiry"])
            if data.get("access_token_expiry") else None
        )
        self._refresh_token_expiry = (
            datetime.fromisoformat(data["refresh_token_expiry"])
            if data.get("refresh_token_expiry") else None
        )
        print("PSN token cache loaded.")
