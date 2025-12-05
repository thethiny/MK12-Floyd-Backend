import os
from scripts import load_secrets
from src.api.xbl import Xbox

if __name__ == "__main__":
    load_secrets()
    XBOX_OSRP_TOKEN = os.getenv(
        "OPSP_XR_CLIENT_ID", os.getenv("creds", {}).get("msclientid", "")  # type: ignore
    )
    
    tokens_folder = "db"
    # if there's xbox_tokens.json in the current folder, rename it to the file's creation timestamp
    if os.path.exists("xbox_tokens.json"):
        import time
        creation_time = time.ctime(os.path.getctime("xbox_tokens.json")).replace(" ", "_").replace(":", "-")
        os.rename("xbox_tokens.json", f"db/xbox_tokens.bkp-{creation_time}.json")

    xbox = Xbox(client_id=XBOX_OSRP_TOKEN, interactive_mode=True, token_cache_folder=tokens_folder)
