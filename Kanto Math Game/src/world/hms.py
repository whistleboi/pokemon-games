"""HMs (Kanto through Kalos): each Gym hands out the HM its badge unlocks in the games, and the
story gates check for the HM (Cut trees, Surf routes, Flash caves, Whirlpool...). Kanto's follow
when FRLG hands them out: Cut after Cerulean, Fly by Celadon (gym 4), Surf in Fuchsia.

Alola, Galar and Paldea have no HMs; their gates use their own story steps instead."""

# Region -> badge (normalised, see _norm) -> HM item key. Badges without one are left out.
HM_BY_BADGE = {
    "KANTO": {"SOUL": "HM_SURF"},  # (Cut: the S.S. Anne's captain; Fly: Route 16's house; Strength: the Warden. 11-07)
    "JOHTO": {"ZEPHYR": "HM_FLASH", "HIVE": "HM_CUT", "PLAIN": "HM_STRENGTH", "FOG": "HM_SURF",
              "STORM": "HM_FLY", "GLACIER": "HM_WHIRLPOOL", "RISING": "HM_WATERFALL"},
    # (Hoenn's Rock Smash, Strength and Fly are story gifts before their badges: Wally's uncle in Mauville,
    # the rival on Route 112 and on Route 119; Jordan, 11-06: one source for each key item in a region)
    "HOENN": {"STONE": "HM_CUT", "KNUCKLE": "HM_FLASH", "BALANCE": "HM_SURF", "MIND": "HM_DIVE",
              "RAIN": "HM_WATERFALL"},
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
    from src.pokemon import tms
    from src.ui import theme
    if tms.is_tm(key) and theme.GAME is not None:  # 'TM24 Snore'
        return tms.label(theme.GAME, key)
    if key.startswith("HM_"):
        return "HM " + key[3:].replace("_", " ").title()
    if key == "Z_RING":
        return "Z-Ring"
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
