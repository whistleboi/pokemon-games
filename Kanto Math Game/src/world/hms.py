"""HMs (Johto through Kalos): each Gym hands out the HM its badge unlocks in the games, and the
story gates check for the HM (Cut trees, Surf routes, Flash caves, Whirlpool...).

Alola, Galar and Paldea have no HMs; their gates use their own story steps instead."""

# Region -> badge (normalised, see _norm) -> HM item key. Badges without one are left out.
HM_BY_BADGE = {
    "JOHTO": {"ZEPHYR": "HM_FLASH", "HIVE": "HM_CUT", "PLAIN": "HM_STRENGTH", "FOG": "HM_SURF",
              "STORM": "HM_FLY", "GLACIER": "HM_WHIRLPOOL", "RISING": "HM_WATERFALL"},
    "HOENN": {"STONE": "HM_CUT", "KNUCKLE": "HM_FLASH", "DYNAMO": "HM_ROCK_SMASH", "HEAT": "HM_STRENGTH",
              "BALANCE": "HM_SURF", "FEATHER": "HM_FLY", "MIND": "HM_DIVE", "RAIN": "HM_WATERFALL"},
    "SINNOH": {"COAL": "HM_ROCK_SMASH", "FOREST": "HM_CUT", "COBBLE": "HM_FLY", "FEN": "HM_DEFOG",
               "RELIC": "HM_SURF", "MINE": "HM_STRENGTH", "ICICLE": "HM_ROCK_CLIMB", "BEACON": "HM_WATERFALL"},
    "UNOVA": {"TRIO": "HM_CUT", "BASIC": "HM_STRENGTH", "BOLT": "HM_SURF", "QUAKE": "HM_FLY",
              "FREEZE": "HM_WATERFALL", "LEGEND": "HM_DIVE"},
    "KALOS": {"BUG": "HM_CUT", "CLIFF": "HM_STRENGTH", "RUMBLE": "HM_SURF", "PLANT": "HM_FLY",
              "FAIRY": "HM_WATERFALL"},
}

ALL_HMS = sorted({hm for table in HM_BY_BADGE.values() for hm in table.values()})


def _norm(badge):
    """'COAL_BADGE', 'Coal', 'STORMBADGE', 'KNuckle' -> 'COAL', 'STORM', 'KNUCKLE'."""
    b = str(badge).upper().replace("_BADGE", "")
    return b[:-5] if b.endswith("BADGE") and len(b) > 5 else b


def hm_for_badge(region, badge):
    return HM_BY_BADGE.get(str(region).upper(), {}).get(_norm(badge))


def item_name(key):
    """Display name: 'HM_ROCK_SMASH' -> 'HM Rock Smash', other items 'Town Map' style."""
    key = str(key)
    if key.startswith("HM_"):
        return "HM " + key[3:].replace("_", " ").title()
    return key.replace("_", " ").title()


def give_for_badges(story):
    """Give any HM the player's badges have earned (old saves, or badges won before HMs).
    Returns the HMs that were added."""
    added = []
    mine = story.store_regions() if hasattr(story, "store_regions") else None
    for region, earned in (story.badges or {}).items():
        if mine is not None and region not in mine:
            continue  # another region's HMs stay in that region's Bag
        for badge in earned or []:
            hm = hm_for_badge(region, badge)
            if hm and story.inventory.get(hm, 0) <= 0:
                story.inventory[hm] = 1
                added.append(hm)
    return added
