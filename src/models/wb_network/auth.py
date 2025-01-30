from datetime import datetime
from typing import List, Any, TypedDict


class Avatar(TypedDict):
    name: str
    image_url: str
    slug: str

class EmailNotificationPreferences(TypedDict):
    friend_request: bool

class AgeData(TypedDict):
    age_type: str
    age_value: None

class LocationData(TypedDict):
    location_type: str
    location_value: str

class AgeInformation(TypedDict):
    age_data: AgeData
    location_data: LocationData
    country: str
    territory: str

class Steam(TypedDict):
    access_time: datetime

class AllPlatforms(TypedDict):
    steam: Steam

class GameLink(TypedDict):
    game: str
    public_id: str
    last_seen_platform: str
    last_game_login: datetime
    last_accessed: datetime
    all_platforms: AllPlatforms
    age_information: AgeInformation
    age_category: str
    child_age_gate: int
    adult_age_gate: int
    age_gate_date: datetime
    is_requesting_game: bool
    created_at: datetime

class SteamLink(TypedDict):
    created_at: datetime
    updated_at: datetime
    auth_id: str
    refresh_required: bool
    unlink_days_left: int
    pending: None
    last_seen_username: str

class Account(TypedDict):
    id: str
    updated_at: datetime
    public_id: str
    email: str
    email_verified: bool
    email_pending: None
    password_set: bool
    mfa_active: bool
    mfa_generated_at: None
    mfa_reminder_sent_at: None
    username: str
    username_updated_at: datetime
    can_change_username: bool
    date_of_birth: datetime
    implied_date_of_birth: None
    age_category: str
    child_age_gate: None
    adult_age_gate: None
    age_gate_date: None
    locale: str
    country: str
    territory: None
    avatar: Avatar
    marketing_opt_in: bool
    marketing_opt_in_updated_at: datetime
    tos_consent: bool
    tos_consented_at: datetime
    tos_revision_consented: int
    tos_consent_required: bool
    privacy_policy_consent: bool
    privacy_policy_consented_at: datetime
    privacy_policy_revision_consented: int
    privacy_policy_consent_required: bool
    twitch_link: None
    discord_link: None
    epic_games_link: None
    google_link: None
    google_pgs_link: None
    steam_link: SteamLink
    psn_link: None
    apple_link: None
    apple_gc_link: None
    nintendo_link: None
    xbox_link: None
    wizarding_world_link: None
    max_link: None
    curse_forge_link: None
    identity_links: List[Any]
    stub: bool
    completed: bool
    presence_state: int
    recaptcha_flagged: bool
    last_login: datetime
    created_at: datetime
    is_soft_locked: bool
    email_notification_preferences: EmailNotificationPreferences
    game_links: List[GameLink]

class WBAuthResult(TypedDict):
    access_token: str
    expires_in: int
    mfa_required: bool
    account: Account
    refresh_token: str
    refresh_expires_in: int
