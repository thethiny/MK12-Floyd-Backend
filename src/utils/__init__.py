import functools
import os

import yaml
from src.api.errors import TokenExpired
import datetime


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
            mk12_key = secrets["keys"]["mk"]
            wb_key = secrets["keys"].get("wb")
            steam_key = secrets["creds"]["steam"]
            msclientid = secrets["creds"].get("msclientid")
            epic = secrets["creds"].get("epic", {})
            epic_client = epic.get("client")
            epic_secret = epic.get("secret")
            os.environ.update(
                {
                    "STEAM_KEY": steam_key,
                    "MK12_API_KEY": mk12_key,
                    "WB_API_KEY": wb_key,
                    "OPSP_XR_CLIENT_ID": msclientid,
                    "EPIC_CLIENT_ID": epic_client,
                    "EPIC_CLIENT_SECRET": epic_secret,
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


import time
import logging
from functools import wraps

# Initialize the log
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


class ReloginLimiter:
    def __init__(self):
        self.calls = {}  # To track calls by methods
        self.total_calls = []  # To track total calls across methods
        self.max_calls = 3
        self.max_per_method = 2
        self.time_window = 600  # 10 minutes in seconds

    def __call__(self, func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            current_time = time.time()
            method_name = func.__name__

            # Log the caller function name
            logging.info(f"{method_name} called at {current_time}")

            # Track the method-specific calls
            if method_name not in self.calls:
                self.calls[method_name] = []

            # Remove old calls outside the time window
            self.calls[method_name] = [
                timestamp
                for timestamp in self.calls[method_name]
                if current_time - timestamp < self.time_window
            ]

            # Track total calls
            self.total_calls = [
                timestamp
                for timestamp in self.total_calls
                if current_time - timestamp < self.time_window
            ]

            if len(self.total_calls) >= self.max_calls:
                raise Exception(
                    f"Exceeded maximum total calls of {self.max_calls} in the time window."
                )

            if len(self.calls[method_name]) >= self.max_per_method:
                raise Exception(
                    f"{method_name} can only call relogin {self.max_per_method} times in the 10-minute window."
                )

            # Register the call
            self.calls[method_name].append(current_time)
            self.total_calls.append(current_time)

            return func(self, *args, **kwargs)

        return wrapper



def prevent_over_refresh(minutes=10):
    def timed_refreshed(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            time_now = datetime.datetime.now()
            if time_now - self.refresh_time < datetime.timedelta(minutes=minutes):
                raise ValueError("Refresh too soon. Please try again in 10 minutes.")
            self.refresh_time = time_now
            return func(self, *args, **kwargs)
        return wrapper
    return timed_refreshed