from cProfile import Profile
from datetime import datetime
from typing import Any, List, Optional, Dict, TypedDict
from enum import Enum
from uuid import UUID

from src.models.mk12.account import Account
from src.models.mk12.profile import Profile


class WbNetworkElement(TypedDict):
    id: str
    created_at: datetime

class AccountAuth(TypedDict):
    wb_network: List[WbNetworkElement]

class Environment(TypedDict):
    id: str

class Status(TypedDict):
    environment: Environment
    current_environment: bool

class Connection(TypedDict):
    id: str
    start_time: int
    last_used: int
    realtime_start_time: int
    realtime_end_time: int
    status: Status

class AccountData(TypedDict):
    current_platform: None
    is_orphaned: bool
    entitlement_list_steam: List[int]

class EmailVerification(TypedDict):
    state: str

class ExternalAccounts(TypedDict):
    pass

class Steam(TypedDict):
    id: str
    username: str
    avatar: Optional[str]
    email: None

class Alternate(TypedDict):
    wb_network: List[Steam]
    steam: List[Steam]

class Username(TypedDict):
    auth: str
    username: str

class Identity(TypedDict):
    username: str
    avatar: str
    default_username: bool
    personal_data: ExternalAccounts
    alternate: Alternate
    usernames: List[Username]
    platforms: List[str]
    current_platform: str
    is_cross_platform: bool

class OptIns(TypedDict):
    wbplay_optin: bool

class Clan(TypedDict):
    invitation: str

class Relationship(TypedDict):
    follow: str

class PrivacyLevels(TypedDict):
    presence: EmailVerification
    clan: Clan
    match: Clan
    relationship: Relationship

class AccountServerData(TypedDict):
    preorder_reward_granted: bool

class WbAccount(TypedDict):
    completed: bool
    age_category: str
    email_verified: bool

class Apns(TypedDict):
    enabled: None
    environment: None
    sha1: None

class ConfigurationAuth(TypedDict):
    override_client_restrictions: bool

class Gcm(TypedDict):
    enabled: None
    project_number: None

class Gpgs(TypedDict):
    google_play_client_id: None

class UDP(Enum):
    THE_00000 = "0.0.0.0:0"


class Ec2UsEast1K1(TypedDict):
    ws: str
    wss: str
    udp: UDP

class Servers(TypedDict):
    ec2_us_east_1_k1: Dict[str, Ec2UsEast1K1]

class Realtime(TypedDict):
    enabled: bool
    default_cluster: str
    servers: Servers

class ServerSideCodeDeploy(TypedDict):
    sha: str
    instance: UUID

class Configuration(TypedDict):
    gcm: Gcm
    gpgs: Gpgs
    apns: Apns
    server_side_code_deploy: ServerSideCodeDeploy
    realtime: Realtime
    auth: ConfigurationAuth

class Calculations(TypedDict):
    playtime_minutes: int

class Inventory(TypedDict):
    defaults_version: int
    version: int

class Totalcharacterbloodspilt(TypedDict):
    sub_zero: int

class Totalcharacterkameofightswon(TypedDict):
    sektor_kam: int

class AnyClass(TypedDict):
    tutorialbasecompletionpercentage: int
    totalcharacterbloodspilt: Totalcharacterbloodspilt
    totalcharacterfighterfatalities: Totalcharacterbloodspilt
    totalcharacterfighterfightswon: Totalcharacterbloodspilt
    totalcharacterkameofightswon: Totalcharacterkameofightswon
    totalfatalities: int
    totalfighterfatalities: int
    totalplaytime: int
    totalrostercharactersused: Totalcharacterbloodspilt

class Seasonal(TypedDict):
    seasonalbloodspilt: int
    seasonalfighterfatalities: int
    seasonalmostfightersplayed: Totalcharacterbloodspilt
    seasonalmostfighterswon: Totalcharacterbloodspilt
    seasonalmostkameosplayed: Totalcharacterkameofightswon
    seasonalmostkameoswon: Totalcharacterkameofightswon
    seasonaltimeplayed: int

class Totaldifferentfatalities(TypedDict):
    sub_zero_fatality_a: int

class Trophy(TypedDict):
    profilestat9006: int
    fightscompleted: int
    fightswon: int
    profilestat9100: Totalcharacterbloodspilt
    totalbloodspilt: int
    totaldamageperformed: float
    totaldifferentfatalities: Totaldifferentfatalities
    totalkameocharactersused: Totalcharacterkameofightswon

class ProfileStats(TypedDict):
    any: AnyClass
    trophy: Trophy
    seasonal: Seasonal

class DataGame(TypedDict):
    inventory: Inventory
    steam_true_owner: str
    game_edition: str
    region_code: str
    profile_stats: ProfileStats

class ProfileData(TypedDict):
    game: DataGame
    change_count: int

class Stats(TypedDict):
    win: int
    loss: int
    rank: int

class Matches(TypedDict):
    stats_versus_casual: Stats
    stats_koth_casual: Stats
    stats_versus_ranked: Stats
    stats_versus_tournament: Stats

class ServerDataGame(TypedDict):
    last_calendar_entry_viewed_time: datetime
    claimed_wbpn_link_rewards: bool

class ProfileServerData(TypedDict):
    game: ServerDataGame

class AccessWbNetwork(TypedDict):
    network_token: str

class Access(TypedDict):
    token: str
    in_queue: bool
    configuration: Configuration
    achievements: List[Any]
    account: Account
    profile: Profile
    notifications: List[Any]
    maintenance: None
    wb_network: AccessWbNetwork