from src.api.eos_web import EpicWebAuth

def auth_epic(code: str):
    if not code:
        raise ValueError()
    
    resp = EpicWebAuth.get_user_id_by_auth(code)
    
    error = resp.get("error")
    if error:
        raise ValueError(error)
    
    user_id = resp.get("account_id", "")
    token = resp.get("access_token", "")
    
    if not user_id or not token:
        raise ValueError(f"Failed to fetch account info with code {code}")
    
    user_resp = EpicWebAuth.get_user_display(token)
    
    account_id = user_resp.get("account_id", "")
    username = user_resp.get("display_name", "")
    
    if account_id and account_id != user_id:
        raise ValueError(f"Mismatch between account_id and user_id: {account_id} != {user_id}")
    
    return user_id.strip(), username.strip() # I don't care if it's empty, not my business
    
    