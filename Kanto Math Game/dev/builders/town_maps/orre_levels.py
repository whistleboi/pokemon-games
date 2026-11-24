"""Orre's levels at Kanto's level caps, stage by stage (story rework L1, Jordan 11-24: "scale the leveling down to roughly
match Kanto level caps at each stage"; kanto_handoff/ROADMAP_ORRE.md L1, questions/ORRE.md 4-8).

Kanto (FireRed) Leaders' strongest 14, 21, 24, 29, 43, 43, 47, 50, with a small climb for Orre's long Part 2 (Jordan's pick):
Misty 14, Duking 21, Blaine + Erika 24, Pryce 29, Evice 37, Jasmine 41, Norman 45, Drake 48, Birch 50, Elite Four 54-60,
Champion 63. Colosseum's after-game places open in Part 2 at about Lv 45-55; after the League about Lv 58-63.

Each battle is sorted by its gates (the flags of the person, option, stage or trainer it sits in) into Part 1, Part 2, the
Colosseum after-game or after the League, then by its area, and its levels are mapped from that group's band today onto
the group's new band (who is stronger than whom stays). A Pokemon too young for its form goes back down its line (the
game's own pokemon_levels.json min_level), and moves it couldn't know at the new level give way to its level-up moves.
Shadow Pokemon (ids 9000+) keep their species and moves - Jordan's custom Shadows are never changed but for their level.

Used twice, on the same rules: orre_story.apply runs apply_towns(maps) on every build (the town battles come fresh from
the discs each time), and kanto_handoff/orre_rom_tools/obatchL1.py ran map_area_data once on assets/orre_area_data.json."""
import json as _json
import os as _os

_REPO = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))
_LV = _json.load(open(_os.path.join(_REPO, "assets", "pokemon_levels.json"), encoding="utf-8"))
MIN = {int(k): v for k, v in _LV["min_level"].items()}
LEARN = {int(k): v for k, v in _LV["learnsets"].items()}
PREV = {}
for _pair in _LV["pairs"]:
    _a, _b = (int(x) for x in _pair.split(">"))
    PREV.setdefault(_b, _a)
_TM = {}
for _m, _who in _json.load(open(_os.path.join(_REPO, "assets", "tm_learners.json"), encoding="utf-8")).items():
    for _p in _who:
        _TM.setdefault(int(_p), set()).add(_m)

# Gen 3's moves: every move Orre's two discs give a trainer (dev/builders/data/orre_trainers.json); fill-ins come only from these
GEN3 = set()
for _t in _json.load(open(_os.path.join(_REPO, "dev", "builders", "data", "orre_trainers.json"), encoding="utf-8")).values():
    for _ms in _t.get("team_moves") or []:
        GEN3.update(m for m in (_ms or []) if isinstance(m, str))

XD_AREAS = {"POKEMON_HQ_LAB", "GATEON_PORT", "KAMINKO_HOUSE", "XD_CIPHER_LAB", "SS_LIBRA", "XD_ONBS", "ORRE_COLOSSEUM",
            "XD_CIPHER_KEY_LAIR", "XD_CITADARK_ISLE"}
# (group, area) -> (old low, old high, new low, new high); area None = the group's fallback
BANDS = {
    ("p1", "OUTSKIRT_STAND"): (14, 24, 6, 8),
    ("p1", "ORRE_DESERT"): (14, 14, 7, 7),
    ("p1", "ORRE_POKE_SPOTS"): (14, 14, 7, 7),
    ("p1", "PHENAC_CITY"): (15, 30, 8, 12),
    ("p1", "PRESTIGE_PRECEPT_CENTER"): (26, 41, 11, 27),
    ("p1", "PYRITE_TOWN"): (15, 35, 13, 21),
    ("p1", "CONSTRUCTION_LOT"): (30, 30, 19, 19),
    ("p1", "PYRITE_BUILDING"): (15, 38, 13, 26),
    ("p1", "OASIS_POKE_SPOT"): (16, 16, 14, 14),
    ("p1", "PYRITE_CAVE"): (18, 39, 15, 24),
    ("p1", "AGATE_VILLAGE"): (19, 40, 17, 25),
    ("p1", "RELIC_CAVE"): (20, 38, 19, 23),
    ("p1", "RELIC_FOREST"): (21, 21, 20, 20),
    ("p1", "CAVE_POKE_SPOT"): (21, 21, 21, 21),
    ("p1", "MT_BATTLE"): (22, 40, 22, 26),
    ("p1", "THE_UNDER"): (24, 45, 22, 26),
    ("p1", "UNDER_COLOSSEUM"): (25, 25, 25, 25),
    ("p1", "SHADOW_PKMN_LAB"): (28, 48, 24, 28),
    ("p1", "SNAGEM_HIDEOUT"): (39, 39, 29, 29),
    ("p1", "REALGAM_TOWER"): (52, 69, 30, 37),
    ("p1", "CIPHER_COMMAND"): (46, 65, 29, 35),
    ("mtb", "MT_BATTLE"): (34, 70, 25, 50),          # Mt. Battle's later areas, open after Dakim: an optional climb
    ("p2", "POKEMON_HQ_LAB"): (30, 47, 31, 35),
    ("p2", "GATEON_PORT"): (30, 48, 33, 38),
    ("p2", "KAMINKO_HOUSE"): (30, 51, 33, 38),
    ("p2", "XD_CIPHER_LAB"): (31, 48, 37, 41),
    ("p2", "PYRITE_TOWN"): (47, 49, 40, 41),
    ("p2", "XD_ONBS"): (33, 50, 39, 42),
    ("p2", "PHENAC_CITY"): (46, 56, 40, 43),
    ("p2", "PRESTIGE_PRECEPT_CENTER"): (48, 56, 40, 43),
    ("p2", "OUTSKIRT_STAND"): (53, 57, 41, 43),
    ("p2", "PYRITE_CAVE"): (50, 54, 41, 43),
    ("p2", "CAVE_POKE_SPOT"): (45, 50, 40, 42),
    ("p2", "SS_LIBRA"): (32, 52, 37, 41),
    ("p2", "SNAGEM_HIDEOUT"): (49, 56, 41, 44),
    ("p2", "ORRE_COLOSSEUM"): (43, 62, 42, 44),
    ("p2", "XD_CIPHER_KEY_LAIR"): (48, 61, 41, 44),
    ("p2", "XD_CITADARK_ISLE"): (63, 78, 45, 48),
    ("p2", "REALGAM_TOWER"): (40, 40, 47, 47),        # XD's Realgam Colosseum (Birch's, badge 8; S3 sets its gate)
    ("p2", "DEEP_COLOSSEUM"): (68, 68, 50, 50),
    ("p2", None): (30, 78, 33, 48),
    ("eagun", None): (62, 72, 48, 50),               # after Greevil, before the League
    ("ag", None): (60, 85, 45, 55),                  # Colosseum's after-game, open in Part 2 (Jordan: about Lv 45-55)
    ("post", None): (66, 78, 58, 63),                # after the League
}
AG_FLAGS = ("col_fein_due", "col_post_kid", "col_cail_post", "col_gurks_post", "col_post_nett2")
POST_FLAGS = ("beat_orre_champion", "xd_miror_last_due")
SKIP_NAMES = ("Gym Leader Jasmine",)   # (S3 levels her and the lighthouse)


def _flags(gates):
    out = []
    for g in gates:
        for x in (g if isinstance(g, list) else [g]):
            if isinstance(x, str) and not x.startswith("not:"):
                out.append(x)
    return out


def group(area, gates, where=""):
    """Which band a battle belongs to: p1, p2, mtb, eagun, ag (Colosseum's after-game) or post (after the League)."""
    fl = _flags(gates)
    if any(f in POST_FLAGS for f in fl):
        return "post"
    if area == "DEEP_COLOSSEUM" or any(f in AG_FLAGS for f in fl) or (area == "ORRE_COLOSSEUM" and "xd_colosseum" in where):
        return "ag"
    if "xd_greevil_beaten" in fl:
        return "ag" if area == "XD_CITADARK_ISLE" else "eagun"   # (Greevil's rematch on Citadark: after-game strength)
    if area in XD_AREAS or any(f in ("orre_part2", "orre_snattle_phenac") or f.startswith("xd_") or f.startswith("kaminko") or f == "visited_SNAGEM_HIDEOUT"
                               for f in fl):
        return "p2"
    if area == "MT_BATTLE" and "orre_dakim_mt_battle" in fl:
        return "mtb"
    return "p1"


def band(grp, area):
    return BANDS.get((grp, area)) or BANDS.get((grp, None)) or BANDS[("p2", None)]


def new_level(lv, b):
    o_lo, o_hi, n_lo, n_hi = b
    if o_hi == o_lo:
        x = n_hi if lv >= o_hi else n_lo - (o_lo - lv) * 0.4
    else:
        x = n_lo + (lv - o_lo) * (n_hi - n_lo) / (o_hi - o_lo)
    return int(max(2, max(n_lo - 3, min(n_hi, round(x)))))


def stage(pid, level):
    while MIN.get(pid, 1) > level and pid in PREV:
        pid = PREV[pid]
    return pid


def known(pid, level):
    return [m for lv, m in LEARN.get(pid, []) if lv <= level]


def fit_moves(pid, level, moves):
    """A move list fit for this level: level-up moves it knows by now, TMs from Lv 20; the rest its latest level-up moves."""
    if not moves:
        return moves
    by_lv = {m: lv for lv, m in LEARN.get(pid, [])}
    keep = [m for m in moves if by_lv.get(m, 999) <= level or (level >= 20 and m in _TM.get(pid, ()))]
    for m in reversed(known(pid, level)):
        if len(keep) >= len(moves):
            break
        if m not in keep and m in GEN3:
            keep.append(m)
    return keep or moves[:1]


def refit(b, grp, area):
    """One battle re-levelled in place."""
    bd = band(grp, area)
    if "levels" not in b:
        old = [b["level"]]
        b["level"] = new_level(b["level"], bd)
        return old
    old = list(b["levels"])
    b["levels"] = [new_level(x, bd) for x in old]
    team = b.get("team")
    if isinstance(team, list) and all(isinstance(p, int) for p in team):
        moves = b.get("team_moves")
        new_team = []
        for i, (p, lv) in enumerate(zip(team, b["levels"])):
            if p >= 9000:          # (a Shadow Pokemon: species and moves as they are)
                new_team.append(p)
                continue
            q = stage(p, lv) if p < 2000 else p
            new_team.append(q)
            if isinstance(moves, list) and i < len(moves) and isinstance(moves[i], list):
                moves[i] = fit_moves(q, lv, moves[i])
        b["team"] = new_team + team[len(new_team):]
    return old


GATE_KEYS = ("condition", "requires", "when_flags")


def battles(o, area, gates=(), where="", out=None):
    """Every battle (a dict with a team and levels, or a Pokemon's levels) under o, with its gates and path."""
    out = [] if out is None else out
    if isinstance(o, dict):
        g = list(gates) + [o[k] for k in GATE_KEYS if k in o]
        if isinstance(o.get("levels"), list) and o["levels"] and all(isinstance(x, int) for x in o["levels"]):
            if o.get("name") not in SKIP_NAMES:
                out.append((o, g, where))
        elif where.endswith(".gift_shadow") and isinstance(o.get("level"), int):   # (a Shadow given, e.g. Hordel's Togepi)
            out.append((o, g, where))
        for k, v in o.items():
            if k != "levels":
                battles(v, area, g, where + "." + k, out)
    elif isinstance(o, list):
        for x in o:
            battles(x, area, gates, where, out)
    return out


def apply_towns(maps, areas):
    """The town maps' battles (every build); areas = Orre's area keys. Returns [(area, name, old, new)]."""
    done = []
    for area in areas:
        if area not in maps:
            continue
        for b, g, where in battles(maps[area], area):
            grp = group(area, g, where)
            old = refit(b, grp, area)
            done.append((area, b.get("name"), old, b.get("levels", [b.get("level")]), grp))
    return done


S2_DONE = ("PHENAC_CITY", "PYRITE_TOWN", "AGATE_VILLAGE", "UNDER_COLOSSEUM", "SNAGEM_HIDEOUT")   # (their "gym": S2b)


def map_area_data(sp):
    """orre_area_data.json's STORY_PROGRESSION in place (once). Returns [(area, name, old, new, group)]."""
    done = []
    for area, a in sp.items():
        if not isinstance(a, dict):
            continue
        for key, v in a.items():
            if key == "gym" and area in S2_DONE:
                continue
            if key == "level" and isinstance(v, int):
                grp = "p2" if area in XD_AREAS or area == "DEEP_COLOSSEUM" else "p1"
                a[key] = new_level(v, band(grp, area))
                done.append((area, "(area level)", [v], [a[key]], grp))
                continue
            for b, g, where in battles(v, area, where="." + key):
                grp = group(area, g, where)
                old = refit(b, grp, area)
                done.append((area, b.get("name"), old, b.get("levels", [b.get("level")]), grp))
    return done
