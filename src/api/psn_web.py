import base64
from dataclasses import dataclass
from typing import Optional
from urllib.parse import parse_qs, urlencode

import requests


@dataclass
class PSNTokens:
    """Authenticated PSN session tokens."""
    access_token: str
    refresh_token: str
    id_token: Optional[str]
    expires_in: int
    refresh_token_expires_in: int
    scope: str

    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "id_token": self.id_token,
            "expires_in": self.expires_in,
            "refresh_token_expires_in": self.refresh_token_expires_in,
            "scope": self.scope,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PSNTokens":
        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            id_token=data.get("id_token"),
            expires_in=data.get("expires_in", 3599),
            refresh_token_expires_in=data.get("refresh_token_expires_in", 5184000),
            scope=data.get("scope", ""),
        )


class PSNAuth:
    """
    PlayStation Network authentication - all class methods, no instance state.
    Uses the PS App (Android) OAuth2 credentials.
    """

    # Endpoints
    AUTHORIZE_URL = "https://ca.account.sony.com/api/authz/v3/oauth/authorize"
    TOKEN_URL = "https://ca.account.sony.com/api/authz/v3/oauth/token"
    SSOCOOKIE_URL = "https://ca.account.sony.com/api/v1/ssocookie"
    LOGIN_URL = "https://store.playstation.com"

    # PS App (Android) client credentials
    CLIENT_ID = "09515159-7237-4370-9b40-3806e67c0891"
    CLIENT_SECRET = "ucPjka5tntB2KqsP"
    REDIRECT_URI = "com.scee.psxandroid.scecompcall://redirect"
    SCOPE = "psn:mobile.v2.core psn:clientapp"

    _BASIC_AUTH = base64.b64encode(
        f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
    ).decode()

    # ============================================================
    # Public API
    # ============================================================

    @classmethod
    def get_login_url(cls) -> str:
        """URL where the user logs in to PlayStation Network."""
        return cls.LOGIN_URL

    @classmethod
    def get_npsso_url(cls) -> str:
        """URL where a logged-in user can retrieve their NPSSO token (JSON response)."""
        return cls.SSOCOOKIE_URL

    @classmethod
    def get_authorize_url(cls) -> str:
        """
        Full PSN OAuth authorize URL.
        After login the browser redirects to a custom scheme URL containing ?code=v3.XXX.
        The user can copy this URL and extract the code.
        """
        params = {
            "access_type": "offline",
            "client_id": cls.CLIENT_ID,
            "redirect_uri": cls.REDIRECT_URI,
            "response_type": "code",
            "scope": cls.SCOPE,
        }
        return f"{cls.AUTHORIZE_URL}?{urlencode(params)}"

    @classmethod
    def exchange_npsso(cls, npsso: str) -> PSNTokens:
        """
        Exchange an NPSSO token for PSN access + refresh tokens.

        The NPSSO token is a 64-character hex string obtained from
        https://ca.account.sony.com/api/v1/ssocookie after logging in
        at store.playstation.com.

        Args:
            npsso: The NPSSO cookie value (64-char hex string).

        Returns:
            PSNTokens with access_token (JWT), refresh_token, etc.
        """
        npsso = npsso.strip()
        code = cls._npsso_to_code(npsso)
        return cls._code_to_tokens(code)

    @classmethod
    def exchange_code(cls, code: str) -> PSNTokens:
        """
        Exchange an authorization code for PSN access + refresh tokens.

        The code is extracted from the redirect URL after login:
        com.scee.psxandroid.scecompcall://redirect/?code=v3.XXXXX

        Args:
            code: The authorization code (starts with "v3.").

        Returns:
            PSNTokens with access_token (JWT), refresh_token, etc.
        """
        code = code.strip()
        return cls._code_to_tokens(code)

    @classmethod
    def extract_code_from_url(cls, url: str) -> str:
        """
        Extract the authorization code from a PSN redirect URL.

        Args:
            url: The full redirect URL, e.g.
                 com.scee.psxandroid.scecompcall://redirect/?code=v3.XXX&cid=...

        Returns:
            The authorization code string.
        """
        # Handle the custom scheme URL - urlparse may not handle it well
        # so we split on the redirect path manually
        if "redirect/" in url:
            query_part = url.split("redirect/", 1)[1]
            if query_part.startswith("?"):
                query_part = query_part[1:]
        elif "?" in url:
            query_part = url.split("?", 1)[1]
        else:
            raise ValueError("No query parameters found in URL")

        params = parse_qs(query_part)
        codes = params.get("code")
        if not codes:
            raise ValueError("No 'code' parameter found in URL")
        return codes[0]

    @classmethod
    def refresh(cls, refresh_token: str) -> PSNTokens:
        """
        Refresh the access token using a refresh token.

        Refresh tokens are valid for ~60 days.

        Args:
            refresh_token: A previously obtained refresh token.

        Returns:
            New PSNTokens (save the new refresh_token for next time).
        """
        response = requests.post(
            cls.TOKEN_URL,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {cls._BASIC_AUTH}",
            },
            data={
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "token_format": "jwt",
                "scope": cls.SCOPE,
            },
        )
        return cls._parse_token_response(response)

    # ============================================================
    # Internal helpers
    # ============================================================

    @classmethod
    def _npsso_to_code(cls, npsso: str) -> str:
        """Exchange an NPSSO cookie for an authorization code."""
        response = requests.get(
            cls.AUTHORIZE_URL,
            params={
                "access_type": "offline",
                "client_id": cls.CLIENT_ID,
                "redirect_uri": cls.REDIRECT_URI,
                "response_type": "code",
                "scope": cls.SCOPE,
            },
            headers={
                "Cookie": f"npsso={npsso}",
            },
            allow_redirects=False,
        )

        if response.status_code != 302:
            # Try to extract an error message
            try:
                data = response.json()
                error = data.get("error", "unknown_error")
                error_desc = data.get("error_description", response.text[:200])
                raise Exception(
                    f"PSN authorization failed: {error} - {error_desc}"
                )
            except (ValueError, KeyError):
                raise Exception(
                    f"PSN authorization failed (HTTP {response.status_code}). "
                    "The NPSSO token may be invalid or expired."
                )

        location = response.headers.get("Location", "")
        if not location:
            raise Exception("PSN authorization failed: no redirect location")

        try:
            code = cls.extract_code_from_url(location)
        except ValueError as e:
            raise Exception(f"PSN authorization redirect missing code: {e}")

        return code

    @classmethod
    def _code_to_tokens(cls, code: str) -> PSNTokens:
        """Exchange an authorization code for tokens."""
        response = requests.post(
            cls.TOKEN_URL,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {cls._BASIC_AUTH}",
            },
            data={
                "code": code,
                "redirect_uri": cls.REDIRECT_URI,
                "grant_type": "authorization_code",
                "token_format": "jwt",
            },
        )
        return cls._parse_token_response(response)

    @classmethod
    def _parse_token_response(cls, response: requests.Response) -> PSNTokens:
        """Parse a token endpoint response into PSNTokens."""
        data = response.json()

        error = data.get("error")
        if error:
            error_desc = data.get("error_description", "No description")
            raise Exception(f"PSN token error: {error} - {error_desc}")

        access_token = data.get("access_token")
        if not access_token:
            raise Exception("PSN token response missing access_token")

        return PSNTokens(
            access_token=access_token,
            refresh_token=data.get("refresh_token", ""),
            id_token=data.get("id_token"),
            expires_in=data.get("expires_in", 3599),
            refresh_token_expires_in=data.get("refresh_token_expires_in", 5184000),
            scope=data.get("scope", ""),
        )