"""Soaring in the Sky (Jordan, 11-14): Omega Ruby / Alpha Sapphire's flight over Hoenn on Mega Latios or Mega Latias,
as a 2D minigame (the screen: src/states/overworld/soaring.py). This file holds what the flight needs to know: which
Eon carries you, the Eon Flute, and the special spots, where they are and when they show.

Where things are: map pixels on the game's Hoenn map picture (assets/region_maps/hoenn.png, 480 x 320, the same
frame as map_points.json's Hoenn towns). The ground you fly over is that picture redrawn four times the size with
open sea above and below (dev/builders/make_soaring_ground.py), so a spot at (x, y) is at (4x, 4y + 160) on it.

Soaring opens when Steven gives you the Eon Flute at Southern Island, as in ORAS (Jordan, 11-14).

The spots follow ORAS (the saved Bulbapedia pages "Mirage spot" and "Soaring in the sky"):
- one daily Mirage spot (an island, forest, cave or mountain at one of the places the games use), the same all day;
- Crescent Isle, south of Ever Grande City, always there;
- the conditional ones, each when your party meets ORAS's condition ("friendly" is a Pokemon with the friendship to
  evolve, src/pokemon/evolution.py); the Pathless Plain has no condition here (ORAS's max EVs: Jordan, 11-14, left out
  till the game has EVs of its own);
- two Dimensional Rifts south of Dewford Town and two Storm Clouds over Fortree City, in the sky itself.
A red beacon floats over each Mirage spot while a legend there is still to catch, as in ORAS.
Every legend of both versions is here (Jordan, 11-13): the first rift holds Dialga and Palkia, the first cloud
Tornadus and Thundurus. One legend per visit (Jordan, 11-14: not by day or time as in ORAS): landing on a Mirage spot
picks one still to catch, and now and then none comes out (NO_SHOW): soar off and find another. A rift or cloud gives
one of its legends each time you fly in.
"""
import random
import datetime

AREA = "HOENN_SOARING_IN_THE_SKY"
FLUTE = "EON_FLUTE"
SCALE, TOP = 4, 160          # map pixel -> ground pixel; the open sea added above the map


def ground_xy(pt):
    return pt[0] * SCALE, pt[1] * SCALE + TOP


# ---------------------------------------------------------------- who carries you
def mount(game):
    """(species id, name) of the Eon you ride: one in your party first, else your version's (Steven's gift),
    else one you've caught, else Latios."""
    story = game.story_manager
    for p in getattr(story, "player_team", []) or []:
        if getattr(p, "id", None) in (380, 381):
            return p.id, ("Latias" if p.id == 380 else "Latios")
    from src.world import hoenn
    v = hoenn.info(story)
    if v:
        return v["eon_id"], v["eon"]
    dex = ((getattr(game, "data", None) and game.data.data) or {}).get("pokedex") or {}
    for entry in dex.values():
        if entry.get("id") in (380, 381):
            return entry["id"], ("Latias" if entry["id"] == 380 else "Latios")
    return 381, "Latios"


def mount_picture(pid):
    """The back view drawn for each (Jordan's picture: the red Mega Latias, the purple Mega Latios)."""
    return "mega_latias_back.png" if pid == 380 else "mega_latios_back.png"


# ---------------------------------------------------------------- the Eon Flute
def give_flute(story):
    """The Eon Flute comes with the Eon at Southern Island (ORAS); a save that got the Eon before the flute existed
    gets it now. True if it was added."""
    if story.inventory.get(FLUTE, 0) > 0 or not story.story_flags.get("got_mega_bracelet"):
        return False
    mine = story.store_regions() if hasattr(story, "store_regions") else None
    if mine is not None and "HOENN" not in mine:
        return False
    story.inventory[FLUTE] = 1
    return True


def flute_block(story):
    """Why the Eon Flute can't be played here (a line to show), or None."""
    if str(story.get_current_region() or "").upper() != "HOENN":
        return "Your Eon friend can't hear the flute this far from Hoenn."
    area = (story.get_current_area_data() or {})
    if area.get("indoors") or area.get("battle_type") in ("indoor", "cave"):
        return "There's no open sky here. Try it outside!"
    if story.current_area_key == AREA:
        return "You're already soaring!"
    return None


# ---------------------------------------------------------------- party checks (ORAS's conditions)
def _party(story):
    return [p for p in (getattr(story, "player_team", []) or []) if p is not None]


def _has(story, *ids):
    have = {getattr(p, "id", None) for p in _party(story)}
    return all(i in have for i in ids)


def _friendly(p):
    from src.pokemon import evolution
    return getattr(p, "friendship", 0) >= evolution.FRIENDSHIP_CATCHES or getattr(p, "affection", 0) >= 150


CONDITIONS = {
    "three_friendly": (lambda s: sum(_friendly(p) for p in _party(s)) >= 3,
                       "three very friendly Pokemon in your party"),
    "level_100": (lambda s: any(getattr(p, "level", 0) >= 100 for p in _party(s)), "a Lv. 100 Pokemon in your party"),
    "reshiram_zekrom": (lambda s: _has(s, 643, 644), "Reshiram and Zekrom in your party"),
    "hooh_or_lugia": (lambda s: _has(s, 249) or _has(s, 250), "Ho-Oh or Lugia in your party"),
    "lake_trio": (lambda s: _has(s, 480, 481, 482), "Uxie, Mesprit and Azelf in your party"),
    "dialga_palkia": (lambda s: _has(s, 483, 484), "Dialga and Palkia in your party"),
    "castform": (lambda s: _has(s, 351), "Castform in your party"),
    "forces": (lambda s: _has(s, 641, 642), "Tornadus and Thundurus in your party"),
}

# ---------------------------------------------------------------- the spots
# kind "land": a place below to land on (its area); kind "sky": a rift or storm cloud to fly into (its legends).
FIXED = [
    {"key": "crescent", "name": "Crescent Isle", "kind": "land", "look": "crescent", "at": (446, 296),
     "area": "HOENN_CRESCENT_ISLE", "legends": ["mirage_cresselia"]},
    {"key": "pathless", "name": "Pathless Plain", "kind": "land", "look": "plain", "at": (306, 266),
     "area": "HOENN_PATHLESS_PLAIN",
     "legends": ["mirage_cobalion", "mirage_terrakion", "mirage_virizion"]},
    {"key": "nameless", "name": "Nameless Cavern", "kind": "land", "look": "cave", "at": (374, 148),
     "area": "HOENN_NAMELESS_CAVERN", "need": "three_friendly",
     "legends": ["mirage_uxie", "mirage_mesprit", "mirage_azelf"]},
    {"key": "fabled", "name": "Fabled Cave", "kind": "land", "look": "cave", "at": (204, 186),
     "area": "HOENN_FABLED_CAVE", "need": "level_100", "legends": ["mirage_reshiram", "mirage_zekrom"]},
    {"key": "gnarled", "name": "Gnarled Den", "kind": "land", "look": "den", "at": (118, 84),
     "area": "HOENN_GNARLED_DEN", "need": "reshiram_zekrom", "legends": ["mirage_kyurem"]},
    {"key": "trackless", "name": "Trackless Forest", "kind": "land", "look": "forest", "at": (70, 166),
     "area": "HOENN_TRACKLESS_FOREST", "need": "hooh_or_lugia",
     "legends": ["mirage_raikou", "mirage_entei", "mirage_suicune"]},
    {"key": "rift1", "name": "a huge gap in the sky", "kind": "sky", "look": "rift", "at": (84, 300),
     "need": "lake_trio", "legends": ["soaring_dialga", "soaring_palkia"]},
    {"key": "rift2", "name": "a huge gap in the sky", "kind": "sky", "look": "rift", "at": (66, 310),
     "need": "dialga_palkia", "legends": ["soaring_giratina"]},
    {"key": "storm1", "name": "a black cloud", "kind": "sky", "look": "storm", "at": (204, 46),
     "need": "castform", "legends": ["soaring_tornadus", "soaring_thundurus"]},
    {"key": "storm2", "name": "a black cloud", "kind": "sky", "look": "storm", "at": (226, 40),
     "need": "forces", "legends": ["soaring_landorus"]},
]

# The daily Mirage spot's places (ORAS's lists, "Mirage spot"), as near as the map picture allows.
DAILY = {
    "island": ("HOENN_MIRAGE_ISLANDS", "Mirage Island", [(30, 178), (52, 276), (118, 26), (336, 84), (382, 98),
                                                       (296, 252), (272, 248), (204, 250)]),
    "forest": ("HOENN_MIRAGE_FOREST", "Mirage Forest", [(36, 222), (172, 266), (160, 34), (58, 62), (318, 78),
                                                       (348, 80), (444, 128), (262, 250)]),
    "cave": ("HOENN_MIRAGE_CAVE", "Mirage Cave", [(112, 292), (92, 26), (26, 92), (214, 26), (340, 86),
                                                 (424, 232), (334, 252), (268, 196)]),
    "mountain": ("HOENN_MIRAGE_MOUNTAIN", "Mirage Mountain", [(28, 150), (322, 80), (386, 94), (412, 100),
                                                             (432, 114), (428, 236), (414, 250), (326, 258)]),
}
DAILY_KINDS = ("island", "forest", "cave", "mountain")
# ORAS's Mirage Islands (not Emerald's on Route 130) are home to Gen 1-3 legends Hoenn has no place for (Jordan, 11-14):
# one may be out each visit, as on the other spots.
ISLAND_LEGENDS = ["mirage_articuno", "mirage_zapdos", "mirage_moltres", "mirage_mewtwo", "mirage_celebi"]


def daily_place(story, day=None):
    """Today's Mirage spot: (kind, which of its kind's places), the same all day, each save its own."""
    day = day or datetime.date.today()
    seed = sum(ord(c) for c in str(getattr(story, "player_name", "") or story.story_flags.get("hoenn_version") or ""))
    n = day.toordinal() * 7 + seed
    kind = DAILY_KINDS[n % len(DAILY_KINDS)]
    return kind, (n // len(DAILY_KINDS)) % len(DAILY[kind][2])


def daily(story, day=None):
    """Today's Mirage spot: (kind, area, name, map point)."""
    kind, i = daily_place(story, day)
    area, name, places = DAILY[kind]
    return kind, area, name, places[i]


def mark_place(story, kind, i):
    """Landing on a daily Mirage spot: which of its kind's places this is (its once-only item's nook shows: the
    item option's condition "mirage_spot_<kind>_<i>", dev/builders/town_maps/soaring.py)."""
    for k in DAILY_KINDS:
        for j in range(len(DAILY[k][2])):
            story.story_flags.pop(f"mirage_spot_{k}_{j}", None)
    story.story_flags[f"mirage_spot_{kind}_{i}"] = True


def caught_all(story, spot):
    return all(story.story_flags.get(f) for f in spot.get("legends") or [])


def spots(story, day=None):
    """The spots out today: each a dict (key, name, kind "land"/"sky", look, at (ground px), area or legends,
    beacon: True while a legend there is still to catch)."""
    flags = story.story_flags
    out = []
    kind, area, name, at = daily(story, day)
    out.append({"key": "daily", "name": name, "kind": "land", "look": kind, "area": area, "at": ground_xy(at),
                "beacon": True, "place": daily_place(story, day), "legends": ISLAND_LEGENDS if kind == "island" else []})
    for s in FIXED:
        need = s.get("need")
        if s["kind"] == "sky" and caught_all(story, s):
            continue                                       # (caught: the rift / the cloud is gone)
        if need and not CONDITIONS[need][0](story):
            continue
        out.append(dict(s, at=ground_xy(s["at"]), beacon=not caught_all(story, s)))
    return out


NO_SHOW = 0.2   # how often a Mirage spot's ring stays quiet (one visit in five)


def next_legend(story, spot, area_data, rng=random):
    """The boss data of a legend at a sky spot still to catch, one of them at random (from the area's SEEK options)."""
    menu = (area_data or {}).get("route_menu") or []
    left = [f for f in spot.get("legends") or [] if not story.story_flags.get(f)]
    rng.shuffle(left)
    for flag in left:
        for item in menu:
            boss = item.get("boss") or {}
            if boss.get("victory_flag") == flag:
                return boss
    return None


def roll_visit(story, spot, rng=random):
    """Landing on a Mirage spot: which of its legends is out this visit (its flag "mirage_here_<victory flag>",
    the condition on its SEEK option), or None: the ring is quiet this time."""
    legends = spot.get("legends") or []
    for f in legends:
        story.story_flags.pop(f"mirage_here_{f}", None)
    left = [f for f in legends if not story.story_flags.get(f)]
    if not left or rng.random() < NO_SHOW:
        return None
    pick = rng.choice(left)
    story.story_flags[f"mirage_here_{pick}"] = True
    return pick


def nearest_town(game, gx, gy):
    """(area key, name) of the Hoenn town nearest a ground point: where you land."""
    pts = ((game.assets.__dict__.get("_soar_pts")) or None)
    if pts is None:
        import json
        import os
        try:
            with open(os.path.join(game.assets.assets_dir, "map_points.json"), encoding="utf-8") as f:
                pts = (json.load(f).get("region_maps", {}).get("HOENN") or {}).get("points") or {}
        except (OSError, ValueError):
            pts = {}
        game.assets.__dict__["_soar_pts"] = pts
    best = None
    for key, pt in pts.items():
        x, y = ground_xy(pt)
        d = (x - gx) ** 2 + (y - gy) ** 2
        if best is None or d < best[0]:
            best = (d, key)
    key = best[1] if best else "MOSSDEEP_CITY"
    return key, key.replace("_", " ").title()
