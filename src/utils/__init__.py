import functools
import os

import yaml
from src.api.errors import TokenExpired


def retry_on_failure(before_retry_func=None):
    @functools.wraps
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except TokenExpired:
                if before_retry_func:
                    before_retry_func(self)
                return func(self, *args, **kwargs)

        return wrapper
    return decorator

def init_secrets():
    try:
        with open("secrets.yaml", encoding="utf-8") as f:
            secrets = yaml.safe_load(f)
            steam_key = secrets["creds"]["steam"]
            mk12_key = secrets["keys"]["mk"]
            wb_key = secrets["keys"]["wb"]
            os.environ.update(
                {
                    "STEAM_KEY": steam_key,
                    "MK12_API_KEY": mk12_key,
                    "WB_API_KEY": wb_key,
                }
            )
    except FileNotFoundError:
        steam_key = os.environ.get("STEAM_KEY")
        if not steam_key:
            raise ValueError(f"`steam_key` secret missing!")
        mk12_key = os.environ.get("MK12_API_KEY")
        if not mk12_key:
            raise ValueError(f"`mk12_key` secret missing!")
        wb_key = os.environ.get("WB_API_KEY")
        if not wb_key:
            raise ValueError(f"`wb_key` secret missing!")
    
    return steam_key, mk12_key, wb_key
