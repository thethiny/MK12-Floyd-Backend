from datetime import datetime
from typing import List, TypedDict


class Avatar(TypedDict):
    name: str
    image_url: str

class PublicAccount(TypedDict):
    public_id: str
    username: str
    avatar: Avatar
    presence_state: int

class WBProfileCard(TypedDict):
    id: str
    sent_from: str
    sent_to: str
    account: PublicAccount
    state: str
    created_at: datetime
    updated_at: datetime

class WBSearchResult(TypedDict):
    total: int
    page: int
    page_size: int
    results: List[WBProfileCard]