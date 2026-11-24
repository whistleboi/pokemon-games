"""The walkthrough / encyclopedia's facts, read straight from the game's own data (region/encyclopedia, 11-24).

    python dev/encyclopedia/facts.py KANTO OUT_DIR

Writes OUT_DIR/facts.json (every place: wild tables, items, trainers, people, signs, scenes, rooms, Journal missions)
and OUT_DIR/sheets/<AREA>.txt (the same, readable, for writing each place's sections). Nothing here is guessed: the
wild rates and levels follow the game's own code -
- land: the area's pool (Safari Zone / Seafoam / Tower: each zone's own pool), its alt_forms weights (route.py /
  loader.py); levels = levels.wild_level (area level -2..+1, at least 2) or the area's "wild_levels" land band;
- water: surf_pool_percentages / <AREA>_SURF_PERCENTAGES (dungeon.py, walk_town._surf_table);
- fishing: route_actions._fishing_pool's chain, levels max(wild level, rod minimum 5/10/15), and
  evolution.suited_to_level (a hooked Gyarados below Lv 20 comes up as a Magikarp);
- Headbutt: the area's tree_pool (else KANTO_ROUTE_TREE_PERCENTAGES) when it has trees; needs the Rocky Helmet.
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
A = os.path.join(ROOT, "assets")


def load(name):
    with open(os.path.join(A, name), encoding="utf-8") as f:
        return json.load(f)


# Hoenn's two stories (src/world/hoenn.py VERSIONS): Omega Ruby first, then Alpha Sapphire, as the game's own neutral words do.
VERSION_WORDS = {"team": "Team Magma/Aqua", "team_short": "Magma/Aqua", "leader": "Maxie/Archie", "legend": "Groudon/Kyogre",
                 "other_legend": "Kyogre/Groudon", "orb": "Red/Blue Orb", "other_orb": "Blue/Red Orb", "eon": "Latios/Latias",
                 "goal": "expand the land/sea", "admin": "Tabitha/Shelly", "other_team": "Team Aqua/Magma",
                 "other_team_short": "Aqua/Magma", "other_leader": "Archie/Maxie", "other_admin": "Shelly/Tabitha"}
VILLAIN_NAMES = {"grunt": "Team Magma/Aqua Grunt", "admin_a": "Magma/Aqua Admin Tabitha/Shelly",
                 "admin_b": "Magma/Aqua Admin Courtney/Matt", "leader": "Magma/Aqua Leader Maxie/Archie"}
VERSION_SWAP = {318: 322, 319: 323, 322: 318, 323: 319}   # (Carvanha / Sharpedo for Aqua, Numel / Camerupt for Magma)


def fix(s):
    """The data's text, readable: the broken e-acute and the plain 'Pokemon' words with their accent."""
    if not isinstance(s, str):
        return s
    s = s.replace("Ã©", "é").replace("�", "é")
    for t, w in VERSION_WORDS.items():   # (Hoenn's text names both versions: src/world/hoenn.py fills one in when you choose)
        s = s.replace("{" + t + "}", w)
    s = re.sub(r"\bPoke(?=mon|\s?Ball|dex|\s?Mart|\s?Doll|\s?Flute|\s?Center|$|\b)", "Poké", s)
    s = re.sub(r"\bPOKE(?=MON|\s?BALL|DEX|\s?MART)", "POKÉ", s)
    return s


def deep_fix(o):
    if isinstance(o, str):
        return fix(o)
    if isinstance(o, list):
        return [deep_fix(v) for v in o]
    if isinstance(o, dict):
        return {k: deep_fix(v) for k, v in o.items()}
    return o


AREA = load("pokemon_area_data.json")
SEVII = load("sevii_area_data.json")
DATA = dict(AREA)
for k, v in SEVII.items():
    if k == "STORY_PROGRESSION":
        DATA[k] = dict(AREA[k], **v)
    elif k == "JOURNAL_MISSIONS":
        continue
    else:
        DATA[k] = v
JOHTO = load("johto_area_data.json")
for k, v in JOHTO.items():   # (Johto's own file: its places, pools and missions; shared tables merged, Kanto's kept)
    if k == "STORY_PROGRESSION":
        DATA[k] = dict(DATA[k], **v)
    elif k == "JOURNAL_MISSIONS":
        continue
    elif isinstance(v, dict) and isinstance(DATA.get(k), dict):
        DATA[k] = dict(v, **DATA[k])
    elif k not in DATA:
        DATA[k] = v
ORANGE = load("orange_area_data.json")
for k, v in ORANGE.items():   # (the Orange Islands' own file, merged the same way)
    if k == "STORY_PROGRESSION":
        DATA[k] = dict(DATA[k], **v)
    elif k == "JOURNAL_MISSIONS":
        continue
    elif isinstance(v, dict) and isinstance(DATA.get(k), dict):
        DATA[k] = dict(v, **DATA[k])
    elif k not in DATA:
        DATA[k] = v
HOENN = load("hoenn_area_data.json")
for k, v in HOENN.items():   # (Hoenn's own file, merged the same way)
    if k == "STORY_PROGRESSION":
        DATA[k] = dict(DATA[k], **v)
    elif k == "JOURNAL_MISSIONS":
        continue
    elif isinstance(v, dict) and isinstance(DATA.get(k), dict):
        DATA[k] = dict(v, **DATA[k])
    elif k not in DATA:
        DATA[k] = v
# The game's overlays (src/core/game.py _apply_overlays: Hoenn's ORAS trainers, canon teams, items and gifts), applied the
# same way the game does at load: the function and its file list are read from the game's own code.
_G = open(os.path.join(ROOT, "src", "core", "game.py"), encoding="utf-8").read()
_ns = {"os": os, "json": json}
exec(re.search(r"^OVERLAYS = .*$", _G, re.M).group(0), _ns)
exec(re.search(r"^def _apply_overlays\(.*?(?=^\S)", _G, re.M | re.S).group(0), _ns)
_ns["_apply_overlays"](A, DATA)
PLACES = DATA["STORY_PROGRESSION"]
MISSIONS = (AREA["GAME_CONFIG"]["JOURNAL_MISSIONS"] + SEVII.get("JOURNAL_MISSIONS", []) + JOHTO.get("JOURNAL_MISSIONS", [])
            + ORANGE.get("JOURNAL_MISSIONS", []) + HOENN.get("JOURNAL_MISSIONS", []))


def region_of(key):
    if key in SEVII["STORY_PROGRESSION"]:
        return "SEVII"
    if key in JOHTO["STORY_PROGRESSION"]:
        return "JOHTO"
    if key in ORANGE["STORY_PROGRESSION"]:
        return "ORANGE"
    if key in HOENN["STORY_PROGRESSION"]:
        return "HOENN"
    return "KANTO"
MAPS = load("town_maps.json")
LEVELS = load("area_levels.json")
EVO = load("pokemon_levels.json")
NAMES = load("pokemon_names.json")
FORMS = DATA.get("FORM_MAP", {})   # (every region's forms: Kanto's regional ones, Orange's pink Pinkan Pokemon...)
TMS = load("tms.json")

SPECIAL = {"mr-mime": "Mr. Mime", "nidoran-f": "Nidoran♀", "nidoran-m": "Nidoran♂", "farfetchd": "Farfetch'd",
           "ho-oh": "Ho-Oh", "mime-jr": "Mime Jr.", "porygon-z": "Porygon-Z", "porygon2": "Porygon2"}
FORM_WORD = {"alolan": "Alolan", "galarian": "Galarian", "hisuian": "Hisuian", "paldean": "Paldean"}


# The rival's stand-ins (loader.py: 10100-10105), set by your badges: stage +1 from 3 badges, +2 from 6.
PLACEHOLDER = {"10100": ("his starter", 4), "10101": ("Pidgey / Pidgeotto (3 badges) / Pidgeot (6)", 16),
               "10102": ("Rattata / Raticate (3 badges), Rhyhorn from 6", 19), "10103": ("Abra / Kadabra (3 badges) / Alakazam (6)", 63),
               "10104": ("Growlithe / Magikarp / Exeggcute line, by his starter", 58),
               "10105": ("Magikarp / Exeggcute / Growlithe line, by his starter", 129), "10500": ("Ghost (Marowak)", 105)}


def mon_name(pid):
    pid = str(pid)
    if pid in PLACEHOLDER:
        return PLACEHOLDER[pid][0]
    if pid in FORMS:
        nm = FORMS[pid].get("name")
        form = str(FORMS[pid].get("form") or "")
        if form == "pinkan":
            return "Pink " + mon_name(FORMS[pid]["id"])   # (Pinkan Island's pink Pokemon: "Pinkan butterfree" in the data)
        if nm and nm == nm.lower() or (nm and nm.split(" ", 1)[-1].islower()):   # ("Valencia butterfree": the form, then the name)
            return f"{form.title()} {mon_name(FORMS[pid]['id'])}"
        return nm or mon_name(FORMS[pid]["id"])
    n = NAMES.get(pid)
    if not n:
        return f"#{pid}"
    return SPECIAL.get(n, n.replace("-", " ").title())


def base_id(pid):
    pid = str(pid)
    if pid in PLACEHOLDER:
        return PLACEHOLDER[pid][1]
    return int(FORMS[pid]["id"]) if pid in FORMS else int(pid)


def item_name(key):
    key = str(key)
    if key == "balls":
        return "Poké Ball"
    if re.match(r"^TM\d+$", key):
        move = (TMS.get(key) or {}).get("move")
        return f"{key} {move.replace('-', ' ').title()}" if move else key
    if key.startswith("HM_"):
        return "HM " + key[3:].replace("_", " ").title()
    named = {"POKE_BALL": "Poké Ball", "POKE_BALLS": "Poké Ball", "POKE_DOLL": "Poké Doll", "PP_UP": "PP Up",
             "PP_MAX": "PP Max", "HP_UP": "HP Up", "X_SP_ATK": "X Sp. Atk", "OAKS_PARCEL": "Oak's Parcel",
             "KINGS_ROCK": "King's Rock", "UPGRADE": "Up-Grade", "GUARD_SPEC": "Guard Spec.", "TM_CASE": "TM Case"}
    return named.get(key, key.replace("_", " ").title())


def item_sprite(key):
    key = str(key)
    if key in ("balls", "POKE_BALLS"):
        return "poke-ball.png"
    if re.match(r"^TM\d+$", key):
        return f"tm-{(TMS.get(key) or {}).get('type', 'normal').lower()}.png"
    if key.startswith("HM_"):
        f = "hm-" + key[3:].lower().replace("_", "-") + ".png"
        return f if os.path.exists(os.path.join(A, "sprites", "items", f)) else "hm-disc.png"
    f = key.lower().replace("_", "-") + ".png"
    alias = {"kings-rock.png": "kings-rock.png", "upgrade.png": "up-grade.png", "oaks-parcel.png": "oaks-parcel.png"}
    f = alias.get(f, f)
    return f if os.path.exists(os.path.join(A, "sprites", "items", f)) else None


# ---------------------------------------------------------------- levels

def area_level(key):
    p = PLACES.get(key) or {}
    if p.get("level"):
        return int(p["level"])
    return int(LEVELS.get(key, 7))   # (levels.START_LEVEL + 2 when the area has none)


def land_band(key):
    p = PLACES.get(key) or {}
    band = (p.get("wild_levels") or {}).get("land")
    if band:
        return int(band[0]), int(band[1])
    L = area_level(key)
    return max(2, L - 2), max(2, L + 1)


def water_band(key):
    L = area_level(key)
    return max(2, L - 2), max(2, L + 1)


def min_level(pid):
    return max(5, int(EVO.get("min_level", {}).get(str(pid), 5)))


def suited(pid, level):
    pid = int(pid)
    pairs = EVO.get("pairs", {})
    for _ in range(3):
        if pid >= 2000 or min_level(pid) <= level:
            break
        pre = next((int(k.split(">")[0]) for k in pairs if int(k.split(">")[1]) == pid), None)
        if pre is None:
            break
        pid = pre
    return pid


# ---------------------------------------------------------------- wild tables

def pct(pool):
    tot = sum(float(v) for v in pool.values()) or 1
    return {str(k): float(v) * 100.0 / tot for k, v in pool.items()}


def with_forms(rows, place):
    """alt_forms weights ({"19_alolan": 0.01}): that share of the species comes as the form (loader.py)."""
    w = ((place.get("alt_forms") or {}).get("weights") or {}) if (place.get("alt_forms") or {}).get("enabled", True) else {}
    out = []
    for r in rows:
        forms = {k.split("_", 1)[1]: c for k, c in w.items() if k.split("_", 1)[0] == str(r["id"]) and not k.endswith("_a")}
        left = r["rate"] - sum(r["rate"] * float(c) for c in forms.values())
        out.append(dict(r, rate=left))
        for form, c in forms.items():
            sid = next((s for s, m in FORMS.items() if m.get("id") == r["id"] and m.get("form") == form), None)
            share = r["rate"] * float(c)
            if sid:
                out.append(dict(r, id=int(sid), rate=share))   # (the same as the pool's own form entry: merged below)
            else:
                out.append(dict(r, rate=share, form=form))
    merged = {}
    for r in out:
        k = (r["id"], r.get("form"), r["how"])
        if k in merged:
            merged[k]["rate"] += r["rate"]
        else:
            merged[k] = dict(r)
    return sorted(merged.values(), key=lambda r: -r["rate"])


REGION_OF_DEX = [(151, "KANTO"), (251, "JOHTO"), (386, "HOENN"), (493, "SINNOH"), (649, "UNOVA"), (721, "KALOS"),
                 (809, "ALOLA"), (905, "GALAR"), (1025, "PALDEA")]
FORM_HOME = {"alolan": "ALOLA", "galarian": "GALAR", "hisuian": "SINNOH", "paldean": "PALDEA"}


def later(r, region):
    """Kanto keeps later regions' Pokemon and other regions' forms out until you've played there (regional_forms.py:
    species_allowed / form_allowed); the Sevii Islands open Johto's. Returns the region it waits for, or None."""
    pid = str(r["id"])
    if pid in FORMS:
        home = FORM_HOME.get(FORMS[pid].get("form"))
        if home and home != "KANTO":
            return home
        pid = str(FORMS[pid]["id"])
    if r.get("form") in FORM_HOME:
        return FORM_HOME[r["form"]]
    n = int(pid)
    native = next((reg for top, reg in REGION_OF_DEX if n <= top), None)
    if native in (None, "KANTO") or (native == "JOHTO" and region in ("SEVII", "JOHTO", "ORANGE", "HOENN")) or (native == "HOENN" and region == "HOENN"):
        return None
    return native


def rows_of(pool, how, band, note=None):
    return [{"id": int(k), "how": how, "lv": list(band), "rate": v, **({"note": note} if note else {})}
            for k, v in sorted(pct(pool).items(), key=lambda kv: -kv[1])]


def has_grass(key):
    """The walked map has tall grass ('"' in its art or its floors' art): wild Pokemon sit there most of the time."""
    m = MAPS.get(key) or {}
    rows = list(m.get("art") or []) if isinstance(m.get("art"), list) else []
    for fl in m.get("floors") or []:
        if isinstance(fl, dict) and isinstance(fl.get("art"), list):
            rows += fl["art"]
    return any('"' in r for r in rows if isinstance(r, str))


def land_kind(place, key=None):
    if key and has_grass(key):
        return "Grass"
    bt = (place.get("battle_type") or "").lower()
    return "Cave" if bt in ("cave", "mountain", "volcano") else "Walking"


def surf_pool(key, town):
    p = PLACES.get(key) or {}
    names = [p.get("surf_pool_percentages")] + ([f"{key}_SURF_PERCENTAGES"] if town else [])
    for n in names:
        if n and isinstance(DATA.get(n), dict) and DATA[n]:
            return n, DATA[n]
    return None, None


def fish_pool(key, rod):
    rods = ["SUPER_ROD", "GOOD_ROD", "OLD_ROD"]
    tried = rods[rods.index(rod):]
    for n in [f"{key}_{r}_PERCENTAGES" for r in tried] + [f"KANTO_{r}_POOL_PERCENTAGES" for r in tried] + [f"{rod}_POOL_PERCENTAGES"]:
        if DATA.get(n):
            return n, DATA[n]
    return None, {}


def fishable(key):
    p = PLACES.get(key) or {}
    return bool(p.get("can_fish")) or any(f"{key}_{r}_PERCENTAGES" in DATA for r in ("OLD_ROD", "GOOD_ROD", "SUPER_ROD"))


def wild(key):
    p = PLACES.get(key) or {}
    town = p.get("area_type") in ("town", "city") or key.endswith(("_TOWN", "_CITY", "_ISLAND"))
    out = {"land": [], "zones": [], "water": [], "trees": [], "notes": []}
    if p.get("wild_tables"):
        out["notes"].append("has wild_tables (slot data) - not read by this tool yet")
    band = land_band(key)
    if p.get("wild_levels"):
        out["notes"].append(f"land levels fixed by the area's wild_levels {band}")
    zp = p.get("zone_pools") or {}
    zones = p.get("zones") or []
    if zp:
        for z in zones:
            n = zp.get(z["key"])
            if n and DATA.get(n):
                out["zones"].append({"zone": fix(z.get("name", z["key"])), "pool": n,
                                     "rows": with_forms(rows_of(DATA[n], land_kind(p, key), band), p)})
    base = p.get("wild_pool_percentages")
    same_as_sea = base and p.get("surf_pool_percentages") and DATA.get(base) == DATA.get(p["surf_pool_percentages"]) and not has_grass(key)
    if same_as_sea:
        out["notes"].append("land pool is the same as the Surf pool on a map with no grass: shown once, as Surfing")
    times = {t: DATA.get(p.get(f"{t.lower()}_pool_percentages")) for t in ("Morning", "Day", "Night")}
    if any(times.values()) and not zp:
        # HGSS's morning (4:00-9:59), day and night (20:00-5:59) tables (route_encounters._base_wild_pool): one row per
        # Pokemon with its rate at each time; a missing time falls back to the area's usual table
        fallback = DATA.get(base) or {}
        times = {t: (pool or (times["Day"] if t == "Morning" else None) or fallback) for t, pool in times.items()}
        rows = {}
        for t, pool in times.items():
            for r in with_forms(rows_of(pool, land_kind(p, key), band), p):
                e = rows.setdefault((r["id"], r.get("form")), dict(r, times={}))
                e["times"][t] = r["rate"]
        out["land"] = sorted(rows.values(), key=lambda r: -sum(r["times"].values()))
        for r in out["land"]:
            r["rate"] = max(r["times"].values())
        out["land_pool"] = base
    elif base and DATA.get(base) and not zp and not same_as_sea:
        out["land"] = with_forms(rows_of(DATA[base], land_kind(p, key), band), p)
        out["land_pool"] = base
        if zones:
            out["notes"].append("zones (floors) share one pool: " + ", ".join(fix(z.get("name", "")) for z in zones))
    rs = DATA.get(p.get("rock_smash_pool_percentages"))
    if rs:
        out["trees"] += rows_of(rs, "Rock Smash", band)
    gp = p.get("grass_pool_percentages")
    if gp and DATA.get(gp):
        out["land"] += with_forms(rows_of(DATA[gp], "Grass", band), p)
    sn, sp = surf_pool(key, town)
    if sp:
        out["water"] += rows_of(sp, "Surfing", water_band(key))
        out["surf_pool"] = sn
    elif town and (MAPS.get(key) or {}).get("surf"):
        out["notes"].append("town water: no Surf table of its own (walk_town borrows the nearest place's, else Tentacool)")
    if fishable(key):
        lo, hi = water_band(key)
        for rod, need, label in (("OLD_ROD", 5, "Old Rod"), ("GOOD_ROD", 10, "Good Rod"), ("SUPER_ROD", 15, "Super Rod")):
            n, pool = fish_pool(key, rod)
            if not pool:
                continue
            flo, fhi = max(lo, need), max(hi, need)
            merged = {}
            for k, v in pct(pool).items():
                for lv in range(flo, fhi + 1):
                    s = suited(k, lv)
                    e = merged.setdefault(s, {"rate": 0.0, "lv": [lv, lv]})
                    e["rate"] += v / (fhi - flo + 1)
                    e["lv"] = [min(e["lv"][0], lv), max(e["lv"][1], lv)]
            for s, e in sorted(merged.items(), key=lambda kv: -kv[1]["rate"]):
                out["water"].append({"id": s, "how": label, "lv": e["lv"], "rate": e["rate"], "pool": n})
    if p.get("has_trees") and any(isinstance(e, dict) and e.get("action") == "HEADBUTT" for e in p.get("route_menu") or []):
        # (dungeon.py: a tree gives HEADBUTT only when the area has that button; Route 29 has trees but no button)
        tp = p.get("tree_pool") or "KANTO_ROUTE_TREE_PERCENTAGES"
        for n in (tp if isinstance(tp, list) else [tp]):
            pool = DATA.get(n) or DATA.get("KANTO_ROUTE_TREE_PERCENTAGES")
            share = 1.0 / (len(tp) if isinstance(tp, list) else 1)
            for r in rows_of(pool, "Headbutt", band):
                r["rate"] *= share
                r["ours"] = region_of(key) == "SEVII"   # (Orange: unknown whether the fan game has them, so no tag)   # (HGSS has Headbutt trees, in Johto and Kanto; not on the Sevii Islands)
                out["trees"].append(r)
        out["tree_pool"] = tp
    out["hordes"], out["dexnav"] = [], []
    hp, hr = p.get("horde_pool_percentages"), float(p.get("horde_rate") or 0)
    if hp and DATA.get(hp) and hr > 0:
        # (src/world/hordes.py: that share of the wild battles here are five at once; a key "41+41+41+42+42" names a mixed five)
        hlv = p.get("horde_levels") or list(band)
        for k, v in sorted(pct(DATA[hp]).items(), key=lambda kv: -kv[1]):
            ids = [int(x) for x in str(k).split("+") if x]
            out["hordes"].append({"id": ids[0], "ids": ids, "how": "Horde", "lv": list(hlv), "rate": v, "share": hr})
    for kind, pkey in (("land", "dexnav_pool_percentages"), ("surf", "dexnav_surf_pool_percentages")):
        dp = p.get(pkey)
        if dp and DATA.get(dp):
            # (src/world/dexnav.py: with the DexNav, #1-386 after Groudon / Kyogre, later ones after the title)
            for r in rows_of(DATA[dp], "DexNav" + (" (water)" if kind == "surf" else ""), band):
                r["dex_when"] = "title" if r["id"] > 386 else "origin"
                out["dexnav"].append(r)
    region = region_of(key)
    for r in out["land"] + out["water"] + out["trees"] + out["hordes"] + out["dexnav"] + [r for z in out["zones"] for r in z["rows"]]:
        r["name"] = mon_name(r["id"]) if not r.get("form") else f"{FORM_WORD.get(r['form'], r['form'].title())} {mon_name(r['id'])}"
        r["icon"] = f"{base_id(r['id'])}.png"
        w8 = later(r, region)
        if w8:
            r["after"] = w8
    for r in out["dexnav"]:
        r.pop("after", None)   # (the DexNav's own gate is the story, not a region visited: its table says when)
    boss = p.get("area_boss")
    if boss:
        out["boss"] = deep_fix(boss)
    return out


# ---------------------------------------------------------------- people, items, trainers

def menu(key):
    p = PLACES.get(key) or {}
    by = {}
    for e in (p.get("route_menu") or []) + (p.get("explore_options") or []):
        if isinstance(e, dict) and "text" in e:
            by.setdefault(e["text"], e)
    return by


def resolve(entry, by):
    if isinstance(entry, str):
        return by.get(entry, {"text": entry, "_unresolved": True})
    if isinstance(entry, list):
        return {"text": " / ".join(str(resolve(e, by).get("text", "")) for e in entry),
                "alternatives": [resolve(e, by) for e in entry]}
    return entry


def gifts_in(person, where, out):
    ev = person.get("event") or {}
    if not isinstance(ev, dict):
        ev = {}   # (a named event: Hoenn's "world" hooks and the like, run by code)
    gi = ev.get("gift_item") or {}
    for k, q in gi.items():
        out.append({"item": k, "name": item_name(k), "sprite": item_sprite(k), "qty": q, "where": where,
                    "found": bool(person.get("found")), "who": fix(person.get("text")),
                    "needs": deep_fix(ev.get("requires") or person.get("condition") or person.get("flag_condition")),
                    "flag": ev.get("flag")})
    for alt in person.get("alternatives") or []:
        gifts_in(alt, where, out)


def trainers_of(key):
    p = PLACES.get(key) or {}
    m = MAPS.get(key) or {}
    pool = p.get("trainer_pool") or []
    out = []
    spots = [(s_, "on the map") for s_ in m.get("trainer_spots") or []]
    names = m.get("floor_names") or []
    for i, fl in enumerate(m.get("floors") or []):
        if isinstance(fl, dict):
            nm = fix(names[i]) if i < len(names) and names[i] else f"Floor {i + 1}"
            spots += [(s_, nm) for s_ in fl.get("trainer_spots") or []]
    for rk, r in (m.get("rooms") or {}).items():
        spots += [(s_, fix(r.get("title") or rk)) for s_ in r.get("trainer_spots") or []]
    used = set()
    for spot, where in spots:   # (one pool entry per spot: four "Grunt" spots take the four Grunts, in order)
        t = (next((t for t in pool if t.get("spot_name") == spot and id(t) not in used), None)
             or next((t for t in pool if t.get("name") == spot and id(t) not in used), None))
        if t:
            used.add(id(t))
            out.append(dict(team(t, where), spot=True))
    gym = p.get("gym") or {}
    for t in gym.get("trainers") or []:
        out.append(team(t, "Gym"))
    if gym.get("leader"):
        out.append(team(gym["leader"], "Gym Leader"))
    return out


def team(t, where):
    out = _team(t, where)
    if t.get("team_choice"):   # (a rival's team by your starter)
        out["by_starter"] = {mon_name(s): [{"id": pid, "name": mon_name(pid), "icon": f"{base_id(pid)}.png", "lv": lv}
                                           for pid, lv in zip(tm, t.get("levels") or [None] * len(tm))]
                             for s, tm in t["team_choice"].items()}
    return out


def _team(t, where):
    role = t.get("villain") or next(iter((t.get("villain_by_version") or {}).values()), None)
    villain = role in VILLAIN_NAMES   # (Hoenn: the chosen version's team, admins and Pokemon, src/world/hoenn.py _villain)

    def version_team(key, swap):
        """The team as src/world/hoenn.py _villain makes it for one version: the swap, then team_by_version."""
        tm = [swap.get(p, p) for p in (t.get("team") or [])]
        lv = list(t.get("levels") or [None] * len(tm))
        tm = list((t.get("team_by_version") or {}).get(key) or tm)
        lv = list((t.get("levels_by_version") or {}).get(key) or lv)
        return tm, lv + [None] * (len(tm) - len(lv))

    def mon(pid, lv):
        return {"id": pid, "name": mon_name(pid), "icon": f"{base_id(pid)}.png", "lv": lv}
    if villain:
        orr, orl = version_team("OMEGA_RUBY", {322: 322, 323: 323, 318: 322, 319: 323})
        asr, asl = version_team("ALPHA_SAPPHIRE", {322: 318, 323: 319})
        members = []
        for i, (pid, lv) in enumerate(zip(orr, orl)):
            m = mon(pid, lv)
            if i < len(asr) and asr[i] != pid:
                m["alt"] = {"id": asr[i], "name": mon_name(asr[i]), "icon": f"{base_id(asr[i])}.png"}
            members.append(m)
    else:
        members = [mon(pid, lv) for pid, lv in zip(t.get("team") or [], t.get("levels") or [None] * len(t.get("team") or []))]
    return {"name": VILLAIN_NAMES[role] if villain else (fix(t.get("name")) or "").strip(),
            "class": "TEAM_VILLAIN" if villain and role != "leader" else ("ROCKET_LEADER" if villain else t.get("class")),
            "villain": role, "where": where, "sprite": t.get("sprite"),
            "team": members,
            "rewards": {item_name(k): v for k, v in (t.get("rewards") or {}).items()},
            "reward_keys": t.get("rewards") or {}, "badge": t.get("badge_reward"), "boss": bool(t.get("is_boss_battle")),
            "dialogue": deep_fix(t.get("dialogue")), "moves": t.get("movesets")}


def battles_in(person, where, out):
    ev = person.get("event") or {}
    if not isinstance(ev, dict):
        ev = {}
    b = ev.get("battle")
    if b:
        t = team(b, where)
        t["who"] = fix(person.get("text"))
        out.append(t)
    for alt in person.get("alternatives") or []:
        battles_in(alt, where, out)


def scene_battles(o, where, out):
    """Any trainer team inside a scene (a rival's battle: "team", or "team_choice" by your starter)."""
    if isinstance(o, dict):
        if (o.get("team") or o.get("team_choice")) and (o.get("name") or o.get("class")):
            out.append(team(o, where))
            return
        for v in o.values():
            scene_battles(v, where, out)
    elif isinstance(o, list):
        for v in o:
            scene_battles(v, where, out)


GAME_TEXT = AREA.get("GAME_TEXT", {})


def scan_map(m, by, where, facts):
    people = [deep_fix(resolve(e, by)) for e in (m.get("people") or [])]
    for pr in people:
        gifts_in(pr, where, facts["items"])
        battles_in(pr, where, facts["battles"])
        if pr.get("action") == "NPC" and pr.get("target") in GAME_TEXT:
            pr["script_text"] = deep_fix(GAME_TEXT[pr["target"]])
    scene_battles(m.get("scenes") or [], where + " (scene)", facts["battles"])
    for xy, it in (m.get("hidden") or {}).items():
        facts["items"].append({"item": it, "name": item_name(it), "sprite": item_sprite(it), "qty": 1, "where": where,
                               "hidden": True, "at": xy})
    return people


_LV = open(os.path.join(ROOT, "src", "world", "levels.py"), encoding="utf-8").read()


def gym_levels(key, size):
    """levels.gym_team_levels for a Gym trainer: the Gym's ace (GYM_ACE by its place in GYM_ORDER) - 4, then 2 lower for
    each Pokemon before the last. None when the place isn't one of its region's Gyms."""
    region = region_of(key)
    m = re.search(rf'"{region}": \[([^\]]+)\]', _LV[_LV.index("GYM_ORDER"):])
    order = re.findall(r'"([A-Z_]+)"', m.group(1)) if m else []
    a = re.search(rf'"{region}": (\[[\d, ]+\])', _LV[_LV.index("GYM_ACE = {"):])
    if key not in order or not a:
        return None
    ace = eval(a.group(1))[order.index(key)] - 4
    return [max(2, ace - (size - 1 - i) * 2) for i in range(size)]


def place(key):
    p = PLACES.get(key) or {}
    m = MAPS.get(key) or {}
    by = menu(key)
    facts = {"key": key, "name": fix(p.get("route_name") or key.replace("_", " ").title()), "type": p.get("area_type"),
             "level": area_level(key), "exits": m.get("exits"), "items": [], "battles": [], "rooms": {}}
    facts["wild"] = wild(key)
    facts["trainers"] = trainers_of(key)
    facts["people"] = scan_map(m, by, "outside", facts)
    facts["signs"] = deep_fix(m.get("signs") or [])
    facts["scenes"] = deep_fix(m.get("scenes") or [])
    facts["barred"] = deep_fix(m.get("barred") or [])
    facts["floors"] = deep_fix(m.get("floor_names") or m.get("floors") and [f.get("name") for f in m["floors"] if isinstance(f, dict)])
    names = m.get("floor_names") or []
    for i, fl in enumerate(m.get("floors") or []):
        if isinstance(fl, dict):
            title = fix(names[i]) if i < len(names) and names[i] else f"Floor {i + 1}"
            facts["rooms"][f"floor_{i}"] = {"title": title, "floor": True, "people": scan_map(fl, by, title, facts),
                                            "signs": deep_fix(fl.get("signs") or []), "scenes": deep_fix(fl.get("scenes") or []),
                                            "barred": deep_fix(fl.get("barred") or [])}
    for rk, r in (m.get("rooms") or {}).items():
        title = fix(r.get("title") or rk.replace("_", " ").title())
        rf = {"title": title, "people": scan_map(r, by, title, facts), "signs": deep_fix(r.get("signs") or []),
              "scenes": deep_fix(r.get("scenes") or []), "barred": deep_fix(r.get("barred") or [])}
        facts["rooms"][rk] = rf
    # every other team in the place's data (rivals in trainer_pool / on_enter_event, scene battles), once each
    seen = {(t["name"], tuple(m["id"] for m in t["team"])) for t in facts["trainers"] + facts["battles"]}
    # a walked area's other trainer_pool trainers stand on free tiles of its map (dungeon.py: every pool trainer that
    # story.trainer_on_map allows), so they're on the map too - rivals, villains and story battles aside
    if p.get("area_type") != "town":
        for t in p.get("trainer_pool") or []:
            special = (t.get("is_boss_battle") or t.get("victory_flag") or t.get("villain")
                       or any(w in str(t.get("class", "")).upper() for w in ("RIVAL", "LEADER", "ELITE", "CHAMPION")))
            tt = team(t, "on the map")
            k = (tt["name"], tuple(m["id"] for m in tt["team"]))
            if not special and k not in seen and tt["team"]:
                seen.add(k)
                facts["trainers"].append(dict(tt, spot=True))
    extra = []
    scene_battles({k: v for k, v in p.items() if k != "gym"}, "story data", extra)
    scene_battles({k: v for k, v in (p.get("gym") or {}).items() if k not in ("trainers", "leader")}, "story data", extra)
    for t in extra:
        k = (t["name"], tuple(m["id"] for m in t["team"]))
        if k not in seen:
            seen.add(k)
            t["where"] = "story / trainer pool (not on a map spot)"
            facts["battles"].append(t)
    # a team with no levels in the data gets the game's own (levels.trainer_team_levels): the area's level, + 0-1 on the
    # first routes (below Lv 8) or + 1-3, for its last Pokemon, one less for each before it; a boss the area's level + 4
    base = area_level(key)
    for t in facts["trainers"] + facts["battles"]:
        n = len(t["team"])
        if n and t["where"] == "Gym" and all(m.get("lv") is None for m in t["team"]):
            gl = gym_levels(key, n)   # (a Gym's own trainers: gym_lobby -> levels.gym_team_levels, the Gym's ace - 4, 2 apart)
            if gl:
                for m, lv in zip(t["team"], gl):
                    m["lv"] = lv
                continue
        if n and all(m.get("lv") is None for m in t["team"]) and not any(str(m["id"]) in PLACEHOLDER for m in t["team"]):
            boss = (t.get("boss") and t["where"] != "Gym") or t["where"] == "Gym Leader"   # (gym_lobby: Gym trainers at the plain rule)
            tops = [base + 4] if boss else ([base, base + 1] if base < 8 else [base + 1, base + 3])
            for i, m in enumerate(t["team"]):
                lo, hi = (max(2, tp - (n - 1 - i)) for tp in (tops[0], tops[-1]))
                m["lv"] = f"{lo}" if lo == hi else f"{lo}–{hi}"
            t["lv_rule"] = True
    facts["travel"] = deep_fix(p.get("travel_options"))
    facts["on_enter"] = deep_fix(p.get("on_enter_event"))
    facts["missions"] = [deep_fix(x) for x in MISSIONS if x.get("target") == key]
    return facts


def sheet(f):
    """A readable fact sheet for one place."""
    L = [f"# {f['name']} ({f['key']})  type={f['type']}  area level={f['level']}", f"exits: {f['exits']}"]
    w = f["wild"]
    for title, rows in (("LAND", w["land"]), ("WATER", w["water"]), ("HEADBUTT / ROCK SMASH", w["trees"])):
        if rows:
            L.append(f"## {title}")
            L += [f"  {r['name']:<22} {r['how']:<10} Lv {r['lv'][0]}-{r['lv'][1]}  {r['rate']:.1f}%" + (" (ours)" if r.get('ours') else "")
                  + (" [" + ", ".join(f"{t} {v:.0f}%" for t, v in r["times"].items()) + "]" if r.get("times") else "")
                  + (f" (only after you've played {r['after'].title()})" if r.get('after') else "") for r in rows]
    for z in w["zones"]:
        L.append(f"## ZONE {z['zone']}")
        L += [f"  {r['name']:<22} {r['how']:<10} Lv {r['lv'][0]}-{r['lv'][1]}  {r['rate']:.1f}%" for r in z["rows"]]
    if w.get("boss"):
        L.append(f"## AREA BOSS {json.dumps(w['boss'], ensure_ascii=False)}")
    if w["notes"]:
        L.append("## wild notes: " + "; ".join(w["notes"]))
    if f["missions"]:
        L.append("## JOURNAL MISSIONS (target here)")
        for x in f["missions"]:
            L.append(f"  [{x.get('type')}] {x.get('id')} '{x.get('text')}': {x.get('desc')}  cond={json.dumps(x.get('condition'), ensure_ascii=False)}")
    if f["trainers"]:
        L.append("## TRAINERS (map spots / gym)")
        for t in f["trainers"]:
            L.append(f"  {t['where']}: {t['class']} {t['name']}: " + ", ".join(f"{m['name']} Lv{m['lv']}" for m in t["team"])
                     + f"  rewards={t['rewards']}" + (f" badge={t['badge']}" if t['badge'] else ""))
            if t.get("dialogue"):
                L.append(f"     dialogue={json.dumps(t['dialogue'], ensure_ascii=False)}")
    if f["battles"]:
        L.append("## BATTLES IN PEOPLE EVENTS")
        for t in f["battles"]:
            L.append(f"  {t['where']}: {t.get('who') or t['name']} [{t['class']}]: " + ", ".join(f"{m['name']} Lv{m['lv']}" for m in t["team"])
                     + f" rewards={t['rewards']}" + (f" badge={t['badge']}" if t.get('badge') else ""))
            for s_, tm_ in (t.get("by_starter") or {}).items():
                L.append(f"     if your starter is {s_}: " + ", ".join(f"{m['name']} Lv{m['lv']}" for m in tm_))
            if t.get("dialogue"):
                L.append(f"     dialogue={json.dumps(t['dialogue'], ensure_ascii=False)}")
    if f["items"]:
        L.append("## ITEMS")
        for i in f["items"]:
            how = "hidden" if i.get("hidden") else "on the ground" if i.get("found") else f"from {i.get('who')}"
            L.append(f"  {i['name']} x{i['qty']}  [{i['where']}] {how}" + (f" needs={i['needs']}" if i.get('needs') else ""))

    def people_lines(people, ind="  "):
        for pr in people:
            L.append(ind + json.dumps({k: v for k, v in pr.items() if k not in ("color", "action")}, ensure_ascii=False)[:1500])
    L.append("## PEOPLE (outside)")
    people_lines(f["people"])
    if f["signs"]:
        L.append("## SIGNS " + json.dumps(f["signs"], ensure_ascii=False))
    if f["scenes"]:
        L.append("## SCENES")
        for s in f["scenes"]:
            L.append("  " + json.dumps(s, ensure_ascii=False)[:2500])
    if f["barred"]:
        L.append("## BARRED " + json.dumps(f["barred"], ensure_ascii=False)[:1500])
    if f["on_enter"]:
        L.append("## ON ENTER " + json.dumps(f["on_enter"], ensure_ascii=False)[:1500])
    if f["travel"]:
        L.append("## TRAVEL " + json.dumps(f["travel"], ensure_ascii=False)[:1500])
    for rk, r in f["rooms"].items():
        L.append(f"## ROOM {rk}: {r['title']}")
        people_lines(r["people"], "    ")
        if r["signs"]:
            L.append("    signs " + json.dumps(r["signs"], ensure_ascii=False))
        for s in r["scenes"]:
            L.append("    scene " + json.dumps(s, ensure_ascii=False)[:2500])
        if r["barred"]:
            L.append("    barred " + json.dumps(r["barred"], ensure_ascii=False)[:800])
    return "\n".join(L)


def region_keys(region):
    sevii = set(SEVII["STORY_PROGRESSION"])
    if region == "SEVII":
        return [k for k in MAPS if k in sevii]
    if region == "JOHTO":
        return [k for k in MAPS if k in JOHTO["STORY_PROGRESSION"]]
    if region == "ORANGE":
        return [k for k in MAPS if k in ORANGE["STORY_PROGRESSION"]]
    if region == "HOENN":
        return [k for k in MAPS if k in HOENN["STORY_PROGRESSION"]]
    kanto = (set(AREA["STORY_PROGRESSION"]) - sevii - set(JOHTO["STORY_PROGRESSION"]) - set(ORANGE["STORY_PROGRESSION"])
             - set(HOENN["STORY_PROGRESSION"]))
    return [k for k in MAPS if k in kanto and (AREA["STORY_PROGRESSION"][k].get("region") in (None, "KANTO"))]


if __name__ == "__main__":
    region, out = sys.argv[1].upper(), sys.argv[2]
    os.makedirs(os.path.join(out, "sheets"), exist_ok=True)
    keys = [k for r in (["KANTO", "SEVII"] if region == "ALL" else ["KANTO", "SEVII", "JOHTO"] if region == "EVERY" else [region]) for k in region_keys(r)]
    allf = {}
    for k in keys:
        f = place(k)
        allf[k] = f
        with open(os.path.join(out, "sheets", f"{k}.txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(sheet(f) + "\n")
    with open(os.path.join(out, "facts.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(allf, fh, ensure_ascii=False, indent=1)
    print(len(allf), "places:", ", ".join(allf))
