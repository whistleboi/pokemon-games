"""HMs (Kanto through Kalos): each Gym hands out the HM its badge unlocks in the games, and the
story gates check for the HM (Cut trees, Surf routes, Flash caves, Whirlpool...). Kanto's are all
story gifts, where FireRed hands them out (Cut: the S.S. Anne's captain; Flash: Route 2's aide; Fly:
Route 16's house; Surf: the Safari Zone's Secret House; Strength: the Warden), each used outside
battle only with FireRed's badge (USE_BADGE; Jordan 11-16).

Alola, Galar and Paldea have no HMs; their gates use their own story steps instead."""

# Region -> badge (normalised, see _norm) -> HM item key. Badges without one are left out.
HM_BY_BADGE = {
    "KANTO": {},  # (all story gifts: Cut the S.S. Anne's captain, Fly Route 16's house, Strength the Warden 11-07; Surf the Safari Zone's Secret House 11-16)
    "JOHTO": {
              },   # (Waterfall: an item ball in the Ice Path, HGSS)
    # (Hoenn's Rock Smash, Strength and Fly are story gifts before their badges: Wally's uncle in Mauville,
    # the rival on Route 112 and on Route 119; Jordan, 11-06: one source for each key item in a region)
    "HOENN": {"STONE": "HM_CUT", "KNUCKLE": "HM_FLASH", "BALANCE": "HM_SURF", "MIND": "HM_DIVE",
              "RAIN": "HM_WATERFALL"},
    "SINNOH": {"COAL": "HM_ROCK_SMASH", "FOREST": "HM_CUT", "COBBLE": "HM_FLY", "FEN": "HM_DEFOG",
               "RELIC": "HM_SURF", "MINE": "HM_STRENGTH", "ICICLE": "HM_ROCK_CLIMB", "BEACON": "HM_WATERFALL"},
    # (11-20, Black 2 / White 2: every HM is a story gift - Cut from Roxie at Virbank's docks, Strength from Hugh in the
    #  Castelia Sewers, Fly from Bianca on Route 5, Surf from Cheren on Route 6, Waterfall from N at Victory Road, Dive from
    #  Hugh in Undella after the League. Until each batch builds its gift, the badge just before stands in; Cut is the
    #  docks event (batch 2). BW's table gave Cheren's Basic Badge Strength.)
    "UNOVA": {"INSECT": "HM_STRENGTH", "BOLT": "HM_FLY", "QUAKE": "HM_SURF", "WAVE": "HM_WATERFALL"},
    "KALOS": {"BUG": "HM_CUT", "CLIFF": "HM_STRENGTH", "RUMBLE": "HM_SURF", "PLANT": "HM_FLY",
              "FAIRY": "HM_WATERFALL"},
}

# HMs handed out by the story, used only once a badge allows it (HGSS: Elder Li's Flash works after the Zephyr Badge, the
# charcoal maker's Cut after the Hive Badge; Jordan 11-15: "true to cannon").
USE_BADGE = {"KANTO": {"HM_CUT": "CASCADE", "HM_FLY": "THUNDER", "HM_SURF": "SOUL", "HM_STRENGTH": "RAINBOW", "HM_FLASH": "BOULDER", "HM_ROCK_SMASH": "MARSH", "HM_WATERFALL": "VOLCANO"},   # (FireRed's own; Jordan 11-16)
             "ORRE": {"HM_FLY": "PYRITE"},   # (neither Orre game has Fly; Jordan 11-21: Fly in Orre after the first badge, HM Fly in Pyrite)
             "JOHTO": {"HM_FLASH": "ZEPHYR", "HM_CUT": "HIVE", "HM_ROCK_SMASH": "ZEPHYR", "HM_SURF": "FOG", "HM_STRENGTH": "PLAIN", "HM_FLY": "STORM", "HM_WHIRLPOOL": "GLACIER", "HM_WATERFALL": "RISING"}}   # (Surf: the Dance Theater's gentleman, HGSS)   # (Rock Smash: the man on Route 36, after Sudowoodo)


def usable(story, item):
    """You have it, and (where the games ask for one) the badge that lets you use it outside battle."""
    if story.inventory.get(item, 0) <= 0:
        return False
    need = USE_BADGE.get(str(story.get_current_region()).upper(), {}).get(item)
    return not need or any(_norm(b) == need for b in story.badges.get(str(story.get_current_region()).upper(), []))


# Regions where EVERY map test of an HM asks for its badge too (Kanto, 11-16). Elsewhere the tests that only ever asked
# for the item (Surf on a route, Strength, Rock Smash, Waterfall, Fly) still do, till that region's own pass.
FIELD_STRICT = {"KANTO", "ORRE"}

# Field moves a region's game uses by the move alone, with no HM item (Orange Islands 5.7: Route L's swimmer teaches Waterfall
# and a Pokemon that knows it climbs Butwal's falls; 11-18). {region: {our HM item: the move}}
FIELD_BY_MOVE = {"ORANGE": {"HM_WATERFALL": "WATERFALL"}}


def field(story, item):
    """Can it be used on the map here: usable() in a FIELD_STRICT region, else just carried."""
    if item == "HM_ROCK_SMASH" and story.inventory.get("PICKAXE", 0) > 0:   # (Orange 5.7's Pickaxe breaks the same rocks, 11-17)
        return True
    if item in FIELD_BY_MOVE.get(str(story.get_current_region()).upper(), {}) and any(
            p and FIELD_BY_MOVE[str(story.get_current_region()).upper()][item] in [str(m).upper().replace("-", "_") for m in (getattr(p, "moves", None) or [])]
            for p in (story.player_team or [])):
        return True   # (Orange 5.7 has no HM for it: a Pokemon that knows the move climbs the falls, Route 62's tutor; 11-18)
    if str(story.get_current_region()).upper() in FIELD_STRICT:
        return usable(story, item)
    return story.inventory.get(item, 0) > 0


def badge_wanted(story, item):
    """The badge still missing for an HM you carry (its name, 'Rainbow'), else None."""
    if story.inventory.get(item, 0) <= 0 or usable(story, item):
        return None
    need = USE_BADGE.get(str(story.get_current_region()).upper(), {}).get(item)
    return need.title() if need else None


# A badge that hands out a second HM (not canon). Johto's Rising Badge also gives Rock Climb, so a Johto
# player can climb Mt. Silver (Jordan, 11-09).
EXTRA_HMS = {"JOHTO": {"RISING": ["HM_ROCK_CLIMB"]}}

ALL_HMS = sorted({hm for table in HM_BY_BADGE.values() for hm in table.values()}
                 | {hm for table in EXTRA_HMS.values() for hms in table.values() for hm in hms})


def _norm(badge):
    """'COAL_BADGE', 'Coal', 'STORMBADGE', 'KNuckle' -> 'COAL', 'STORM', 'KNUCKLE'."""
    b = str(badge).upper().replace("_BADGE", "")
    return b[:-5] if b.endswith("BADGE") and len(b) > 5 else b


def hm_for_badge(region, badge):
    return HM_BY_BADGE.get(str(region).upper(), {}).get(_norm(badge))


def hms_for_badge(region, badge):
    """Every HM a badge hands out (its own, then any extra: the Rising Badge's Rock Climb)."""
    main = hm_for_badge(region, badge)
    return ([main] if main else []) + list(EXTRA_HMS.get(str(region).upper(), {}).get(_norm(badge), []))


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
            for hm in hms_for_badge(region, badge):
                if story.inventory.get(hm, 0) <= 0:
                    story.inventory[hm] = 1
                    added.append(hm)
    return added
