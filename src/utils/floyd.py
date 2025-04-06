from typing import Any, Dict

from src.models.mk12.profile import Profile

def get_floyd_maps():
    name_maps = {
        "profilestat9001": "ProfileStat9001",
        "profilestat9002": "Total Times Encountered Floyd",
        "profilestat9003": "Floyd Challenges Completed",
        "profilestat9004": "Floyd Last Battle State",
        "profilestat9005": "Total Times Defeated Floyd",
        "profilestat9006": "Total Matches Since Last Seen Floyd",
        "profilestat9100": "Floyd Fatalities Tracker",
        "profilestat9101": "Floyd Animalities Tracker",
        "profilestat9102": "Shaolin Monks Tower Completions",
        "profilestat9103": "Door Buster Completions",
        "profilestat9104": "Chapter 15 Current Location",
        "profilestat9105": "Towers of Time Challenge Points",
        "profilestat9106": "Quests Completed",
    }
    
    return name_maps


def get_floyd_data(user_profile: Profile):
    tracked_stats_ranges = list(range(9001, 9007)) + list(range(9100, 9107))
    platforms = ["ps5", "xsx", ""]


    profile_stats = (
        user_profile.get("data", {}).get("game", {}).get("profile_stats", {})
    )
    bitmask = profile_stats.get("bitmask", {})
    trophies = profile_stats.get("trophy")
    stats_dict = {}

    for stat_id in tracked_stats_ranges:
        key = f"profilestat{stat_id}"
        current_value = bitmask.get(key)  # 0 for allowing comparison
        if current_value is not None:
            for platform in platforms:
                stats_dict.setdefault(platform, {})[key] = current_value
            continue

        for platform in platforms:
            if platform:
                plat_name = f"{platform}_{key}"
            else:
                plat_name = key
            current_value = trophies.get(plat_name, 0)
            stats_dict.setdefault(platform, {})[key] = current_value

    return stats_dict


def parse_floyd_data(floyd_data, hydra_platform):

    tracker_dict = {
        "9001": 0,
        "encounters": 0,
        "challenges_checklist": {i+1: False for i in range(10)},
        "challenges_mask": 0,
        "challenges_remaining": 10,
        "challenges_done": 0,
        "last_battle": "Not yet encountered",
        "victories": 0,
        "losses": 0,
        "next_floyd_clue": "In 100 Matches",
        "fatal_finish": "Incomplete",
        "you_finish_yet": "Incomplete",
        "inner_beast": "Incomplete",
        "shaolin": "Incomplete",
        "door_buster": "Incomplete",
        "chapter_15": "Incomplete",
        "tot_points": "20 Points left",
        "daily": "2 Quests left",
    }

    tracker_dict_raw: Dict[int, Any] = {}

    profile_counter = 0

    for k, value in floyd_data.get(hydra_platform, floyd_data.get("")).items(): # Replaced with hydra_platform cuz the game tracks different stats
        floyd_chal_id = int(k[-4:])
        if floyd_chal_id == 9001:
            tracker_dict["9001"] = value
        elif floyd_chal_id == 9002:
            tracker_dict["encounters"] = value
        elif floyd_chal_id == 9003:
            # challenges_count = 10
            challenges_count = 37
            _value = [bool(int(bit)) for bit in bin(value)[2:].zfill(challenges_count)]
            total = sum(_value)
            l = {i + 1: v for i, v in enumerate(_value[::-1])} # Reverse order!
            # value = f"Done {total} - Remaining {10-total}"
            tracker_dict["challenges_checklist"] = l
            tracker_dict["challenges_remaining"] = 10-total # 37 slots but 10 at most
            tracker_dict["challenges_done"] = total
            tracker_dict['challenges_mask'] = value
            value = bin(value)[2:].zfill(challenges_count)
        elif floyd_chal_id == 9004:
            if value == 0:
                value = "No Fight Information"
            elif value == 9:
                value = "Lost"
            elif value == 12:
                value = "Won"
            elif value == 11:
                value = "Did not finish"
            tracker_dict["last_battle"] = value
        elif floyd_chal_id == 9005:
            tracker_dict["victories"] = value
        elif floyd_chal_id == 9006:
            insert_value = value%501
            if insert_value < 100:
                tracker_dict["next_floyd_clue"] = f"You need at least {100-insert_value} fights before floyd may appear to give you a clue."
            else:
                tracker_dict["next_floyd_clue"] = f"Floyd will pop up within the next {500-insert_value} fights. Even if he appears, that doesn't mean this is the challenge you need to do."
        elif floyd_chal_id == 9100:
            try:
                most_fatalities_done_as, most_fatalities_done = max(value.items(), key=lambda x: x[1])
            except ValueError:
                most_fatalities_done_as, most_fatalities_done = None, 0
            except AttributeError:
                most_fatalities_done_as, most_fatalities_done = "Unknown", 1 # For standarization
                value = {"Unknown": 1}  # For standarization
            if most_fatalities_done >= 5:
                tracker_dict["you_finish_yet"] = "Complete"
                profile_counter += 1
            else:
                tracker_dict["you_finish_yet"] = f"Incomplete"
                if most_fatalities_done > 1:
                    tracker_dict["you_finish_yet"] += f" | Suggested {5-most_fatalities_done} more as {most_fatalities_done_as}"
            count = len(value)
            if count < 5:
                done_chars = value.keys()
                tracker_dict["fatal_finish"] = f"You need fatalities as {5-count} more characters other than: {', '.join(done_chars)}"

            else:
                tracker_dict["fatal_finish"] = "Complete"
                profile_counter += 1
        elif floyd_chal_id == 9101:
            try:
                most_fatalities_done_as, most_fatalities_done = max(value.items(), key=lambda x: x[1])
            except ValueError:
                most_fatalities_done_as, most_fatalities_done = None, 0
            except AttributeError:
                most_fatalities_done_as, most_fatalities_done = "Unknown", 1
                value = {"Unknown": 1} # For standarization
            if most_fatalities_done >= 2:
                tracker_dict["inner_beast"] = "Complete"
                profile_counter += 1
            else:
                tracker_dict["inner_beast"] = "Incomplete"
        elif floyd_chal_id == 9102:
            if value:
                tracker_dict["shaolin"] = "Complete"
                profile_counter += 1
            else:
                tracker_dict["shaolin"] = "Incomplete"
        elif floyd_chal_id == 9103:
            if value:
                tracker_dict["door_buster"] = "Complete"
                profile_counter += 1
            else:
                tracker_dict["door_buster"] = "Incomplete"
        elif floyd_chal_id == 9104:
            if value >= 4095:
                value = "Complete"
                profile_counter += 1
            elif value == 0:
                value = "Not Started"
            else:
                value = "Started But Not Finished"
            tracker_dict["chapter_15"] = value
        elif floyd_chal_id == 9105:
            insert_value = value
            if value >= 20:
                tracker_dict["tot_points"] = "Complete"
                profile_counter += 1
            else:
                tracker_dict["tot_points"] = f"{20-value} Points remaining"
        elif floyd_chal_id == 9106:
            if value >= 2:
                tracker_dict["daily"] = "Complete"
                profile_counter += 1
            else:
                tracker_dict["daily"] = f"{2-value} quests left"

        tracker_dict_raw[floyd_chal_id] = value
        tracker_dict["losses"] = tracker_dict["encounters"] - tracker_dict["victories"]

    hints = []
    if False and tracker_dict["challenges_done"] >= 10: # Disabled due to update
        hints.append("Floyd active! Go to versus to start the battle!")
    else:
        remaining = tracker_dict["challenges_remaining"]
        if profile_counter == 0:
            hints.append(f"You did not yet attempt any challenge between 30 and 37.")
        if profile_counter < 8:
            hints.append(f"You have {8-profile_counter} challenges between 30 and 37 to try!")
        else:
            if remaining > 0:
                hints.append(f"You have {remaining} challenges left between 1 and 29.")
            else:
                hints.append(f"Tracker incorrectly tracking your profile. You either are playing on more than 1 platform at once, or you need to use offline mode.")

    if tracker_dict["encounters"]:
        if tracker_dict["last_battle"] == "Won":
            hints.append(f"I see you're going for another win. You got it!")
        elif tracker_dict["last_battle"] == "Did not finish":
            hints.append(f"Hopefully this time you're able to finish the fight.")
        elif tracker_dict["last_battle"] == "Lost":
            hints.append(f"You're gonna beat him this time. I'm sure of it!")
        else:
            # hints.append(f"I don't know what happened in your last fight but remember to block more than you attack!")
            hints.append(f"If you keep blocking, eventually Floyd will pause and you can hit him!")
    else:
        hints.append("The first time you meet floyd is gonna be epic! Good luck, rooting for you!")

    return {
        "raw": tracker_dict_raw,
        "parsed": tracker_dict,
        "hints": hints,
    }
