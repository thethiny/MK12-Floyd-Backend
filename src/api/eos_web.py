import os
import urllib.parse
import requests


class EpicWebAuth:
    ROOT_URL = "https://api.epicgames.dev/epic/oauth/v2"

    @staticmethod
    def make_auth_url(redirect_uri: str) -> str:
        client_id = os.environ.get("EPIC_CLIENT_ID", "")
        if not client_id:
            raise ValueError("EPIC_CLIENT_ID not set.")

        return (
            "https://www.epicgames.com/id/authorize"
            f"?client_id={client_id}"
            "&response_type=code"
            f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
            "&scope=basic_profile"
        )

    @staticmethod
    def make_url(relative_path: str) -> str:
        return f"{EpicWebAuth.ROOT_URL.rstrip('/')}/{relative_path.lstrip('/')}"

    @staticmethod
    def _exchange_code(code: str) -> dict:
        try:
            client_id = os.environ.get("EPIC_CLIENT_ID", "")
            client_secret = os.environ.get("EPIC_CLIENT_SECRET", "")
            if not client_id or not client_secret:
                raise ValueError("EPIC_CLIENT_ID or EPIC_CLIENT_SECRET not set.")

            data = {
                "grant_type": "authorization_code",
                "code": code,
            }
            auth = (client_id, client_secret)
            url = EpicWebAuth.make_url("token")
            resp = requests.post(url, data=data, auth=auth)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": f"Token exchange failed: {str(e)}"}

    @staticmethod
    def _get_user_info(access_token: str) -> dict:
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            url = EpicWebAuth.make_url("userInfo")
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": f"Fetching user info failed: {str(e)}"}

    @staticmethod
    def revoke_token(access_token: str) -> dict:
        try:
            client_id = os.environ.get("EPIC_CLIENT_ID", "")
            client_secret = os.environ.get("EPIC_CLIENT_SECRET", "")
            if not client_id or not client_secret:
                raise ValueError("EPIC_CLIENT_ID or EPIC_CLIENT_SECRET not set.")

            data = {"token": access_token, "token_type_hint": "access_token"}
            auth = (client_id, client_secret)
            url = EpicWebAuth.make_url("revoke")
            resp = requests.post(url, data=data, auth=auth)
            resp.raise_for_status()
            return {"success": True}
        except Exception as e:
            return {"error": f"Revoke failed: {str(e)}"}

    @staticmethod
    def get_user_id_by_auth(code: str) -> dict:
        token_resp = EpicWebAuth._exchange_code(code)
        if token_resp.get("error"):
            return token_resp

        account_id = token_resp.get("account_id")
        access_token = token_resp.get("access_token")
        if not account_id or not access_token:
            return {"error": "Missing account_id or access_token."}

        return {"account_id": account_id, "access_token": access_token}

    @staticmethod
    def get_user_display(access_token: str, revoke: bool = True) -> dict:
        user_info = EpicWebAuth._get_user_info(access_token)
        if user_info.get("error"):
            return user_info

        if revoke:
            EpicWebAuth.revoke_token(access_token)

        return {
            "account_id": user_info.get("sub"),
            "display_name": user_info.get("preferred_username"),
        }
