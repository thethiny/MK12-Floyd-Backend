from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from src.utils.floyd_randomizer import convert_profile_id_to_seed

PCG_MULT = 0x5851F42D4C957F2D
PCG_INC = 0x280AF6FDEECF029F
MASK_64 = 0xFFFFFFFFFFFFFFFF

TICKS_EPOCH = datetime(1, 1, 1, tzinfo=timezone.utc) # FDateTime ticks (100ns) start at year 1

# Baked in MK12.exe @ 0x1478250E0
TOWERS_PER_DAY = 1
MIN_SLOT = 4
DURATION = timedelta(minutes=60)

# Map Mode towers left to right, each slot rotates at minute slot*10
SLOTS = ["C_1", "C_2", "C_4", "C_5", "C_7", "C_8"]


class Pcg32:
    def __init__(self, seed: int):
        self.state = (PCG_MULT * ((seed + PCG_INC) & MASK_64) + PCG_INC) & MASK_64

    def bounded(self, bound: int) -> int:
        if not bound:
            return 0

        threshold = (-bound & 0xFFFFFFFF) % bound # Rejection sampling, same as shuffler
        while True:
            old = self.state
            self.state = (PCG_MULT * old + PCG_INC) & MASK_64
            xorshifted = ((old >> 27) ^ (old >> 45)) & 0xFFFFFFFF
            rot = old >> 59
            value = ((xorshifted >> rot) | (xorshifted << (-rot & 31))) & 0xFFFFFFFF
            if value >= threshold:
                return value % bound


def to_ticks(dt: datetime) -> int:
    return (dt - TICKS_EPOCH) // timedelta(microseconds=1) * 10


def get_day_windows(hydra_id: str, day: datetime) -> List[Dict[str, Any]]:
    day = day.replace(hour=0, minute=0, second=0, microsecond=0)
    rng = Pcg32(to_ticks(day) ^ convert_profile_id_to_seed(hydra_id))

    hours = list(range(24))
    for i in range(len(hours) - 1):
        j = i + rng.bounded(len(hours) - i)
        hours[i], hours[j] = hours[j], hours[i]

    windows = []
    for i in range(TOWERS_PER_DAY):
        slot = MIN_SLOT + rng.bounded(len(SLOTS) - MIN_SLOT)
        start = day + timedelta(hours=hours[i % len(hours)], minutes=slot * 10) # Slot index is also the minute offset
        windows.append({"slot": SLOTS[slot], "slot_index": slot, "start": start, "end": start + DURATION})

    return windows


def get_taco_tower(hydra_id: str, floyd_victories: int, now: Optional[datetime] = None):
    if floyd_victories < 1: # Tower never spawns before beating Floyd once
        return {"unlocked": False}

    now = now or datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Yesterday's window can spill past midnight, tomorrow's is the fallback
    windows = [w for d in (-1, 0, 1) for w in get_day_windows(hydra_id, today + timedelta(days=d))]
    window = min((w for w in windows if w["end"] > now), key=lambda w: w["start"])

    return {
        "unlocked": True,
        "active": window["start"] <= now,
        "slot": window["slot"],
        "slot_index": window["slot_index"],
        "start": window["start"].isoformat(),
        "end": window["end"].isoformat(),
    }
