"""The Black Fog (Jordan, 11-02): the giant Haunter that haunts the spooky places (each has its own
"black_fog_banished_<area>" flag: a route menu option, or the Pokemon Tower's stairs ambush).

- Banished, it can come back: entering its area gives a 10% chance, at most once a day there.
- It's as strong as your strongest Pokemon (two levels above it).
"""
import datetime
import random

BOSS_ID = 10501
RETURN_CHANCE = 0.10


def ace_level(story):
    return max((p.level for p in story.player_team if p), default=5)


def level(story):
    return max(5, min(100, ace_level(story) + 2))


def fog_flag(area_data):
    """The area's Black Fog flag (its menu option's, or its stairs ambush's), or None."""
    for item in (area_data or {}).get("route_menu") or []:
        boss = item.get("boss") or {}
        if boss.get("id") == BOSS_ID:
            return boss.get("victory_flag")
    boss = ((area_data or {}).get("zone_ambush") or {}).get("boss") or {}
    return boss.get("victory_flag") if boss.get("id") == BOSS_ID else None


def maybe_return(story, area_key, area_data, rng=random, today=None):
    """On entering an area: a banished Black Fog may gather again (10%, once a day there).
    Returns True when it came back."""
    flag = fog_flag(area_data)
    if not flag or not story.story_flags.get(flag):
        return False
    day = (today or datetime.date.today()).isoformat()
    seen = f"black_fog_back_{area_key}"
    if story.story_flags.get(seen) == day or rng.random() >= RETURN_CHANCE:
        return False
    story.story_flags.pop(flag, None)
    story.story_flags[seen] = day
    return True
