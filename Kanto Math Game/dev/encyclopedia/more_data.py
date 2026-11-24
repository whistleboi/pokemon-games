"""More of the game's own data for the encyclopedia (region/encyclopedia, 11-24): everything the game already knows about
each Pokemon and move, each region's Pokedex, and its town map. Built by build_site.py into data/ files the pages load
when they open:
  data/pokedex.json     per Pokemon: level-up moves (pokemon_levels.json learnsets, the game's own), the TMs it learns
                        (tm_learners.json), abilities (species_data.json + abilities.json), egg groups, growth rate,
                        EV yield, Mega forms (mega_forms.json)
  data/movedex.json     per move (moves.json): type, category, power, accuracy, PP, priority, effect, its TM, and who
                        learns it by level or by TM
  data/regionmaps.json  per region: its town map picture (assets/region_maps) and where each place sits on it
                        (map_points.json region_maps)
Each region's Pokedex list (src/states/systems/pokedex.py region_dex) goes into the region's own data file."""
import base64
import json
import os
from io import BytesIO

import facts as F

STATS = ("HP", "ATTACK", "DEFENSE", "SPECIAL-ATTACK", "SPECIAL-DEFENSE", "SPEED")
EV_WORDS = {"HP": "HP", "ATK": "Attack", "DEF": "Defense", "SPATK": "Sp. Atk", "SPDEF": "Sp. Def", "SPEED": "Speed",
            "SPD": "Speed"}
GROWTH_WORDS = {"slow": "Slow", "medium": "Medium Fast", "medium-fast": "Medium Fast", "fast": "Fast",
                "medium-slow": "Medium Slow", "slow-then-very-fast": "Erratic", "fast-then-very-slow": "Fluctuating",
                "erratic": "Erratic", "fluctuating": "Fluctuating"}


def load(name):
    return F.load(name)


def move_name(key):
    """THUNDER-SHOCK -> Thunder Shock (the game's keys use hyphens)."""
    special = {"U-TURN": "U-turn", "V-CREATE": "V-create", "X-SCISSOR": "X-Scissor", "SOFT-BOILED": "Soft-Boiled",
               "SELF-DESTRUCT": "Self-Destruct", "DOUBLE-EDGE": "Double-Edge", "WILL-O-WISP": "Will-O-Wisp",
               "LOCK-ON": "Lock-On", "MUD-SLAP": "Mud-Slap", "WAKE-UP-SLAP": "Wake-Up Slap", "BABY-DOLL-EYES": "Baby-Doll Eyes",
               "FREEZE-DRY": "Freeze-Dry", "TRICK-OR-TREAT": "Trick-or-Treat", "FORESTS-CURSE": "Forest's Curse",
               "KINGS-SHIELD": "King's Shield", "LANDS-WRATH": "Land's Wrath", "NATURES-MADNESS": "Nature's Madness",
               "MULTI-ATTACK": "Multi-Attack", "POWER-UP-PUNCH": "Power-Up Punch", "ALL-OUT-PUMMELING": "All-Out Pummeling",
               "DOUBLE-SLAP": "Double Slap", "SAND-ATTACK": "Sand Attack", "TAKE-DOWN": "Take Down"}
    k = str(key).upper()
    return special.get(k) or " ".join(w.capitalize() for w in k.split("-"))


def move_slug(key):
    return str(key).lower()


def pokedex():
    ls = load("pokemon_levels.json").get("learnsets", {})
    tml = load("tm_learners.json")
    tms = load("tms.json")
    by_move = {v.get("move"): tm for tm, v in tms.items()}
    sp = load("species_data.json")
    ab = load("abilities.json")
    gr = load("growth_rates.json").get("species", {})
    ev = load("ev_yields.json")
    mega = load("mega_forms.json")
    learns_tm = {}
    for move, pids in tml.items():
        for p in pids:
            learns_tm.setdefault(int(p), []).append(by_move.get(move) or move)
    out = {}
    for pid in range(1, 1026):
        s = sp.get(str(pid)) or {}
        e = {}
        if ls.get(str(pid)):
            e["ls"] = [[int(lv), m] for lv, m in ls[str(pid)]]
        if learns_tm.get(pid):
            e["tm"] = sorted(learns_tm[pid])
        abil = [(ab.get(a) or {}).get("name") or a.title() for a in s.get("abilities") or []]
        if abil:
            e["ab"] = abil
        if s.get("hidden"):
            e["hab"] = (ab.get(s["hidden"]) or {}).get("name") or s["hidden"].title()
        if s.get("egg_groups"):
            e["eg"] = [g.replace("_", " ").title() for g in s["egg_groups"]]
        g = gr.get(str(pid))
        if g:
            e["gr"] = GROWTH_WORDS.get(str(g).lower(), str(g).replace("-", " ").title())
        if ev.get(str(pid)):
            e["ev"] = ", ".join(f"{v} {EV_WORDS.get(k, k.title())}" for k, v in ev[str(pid)].items())
        if mega.get(str(pid)):
            e["mega"] = [{"n": m.get("name", "").title(), "item": F.item_name(m["item"]) if m.get("item") else "",
                          "ik": str(m.get("item") or "").lower().replace("_", "-"),
                          "t": [t.title() for t in m.get("types") or []],
                          "s": [(m.get("stats") or {}).get(x) for x in STATS]} for m in mega[str(pid)]]
        fl = forms_of(pid, sp, ab, ls)
        if fl:
            e["forms"] = fl
        if e:
            out[pid] = e
    return out, ab


REGIONAL = {"alolan": "Alolan form", "galarian": "Galarian form", "hisuian": "Hisuian form", "paldean": "Paldean form",
            "pinkan": "Pinkan form (Orange Islands)", "valencia": "Valencia form (Orange Islands)"}
_MS = None


def forms_of(pid, sp, ab, ls):
    """A species' other forms, as the game builds them (src/pokemon/loader.fetch_specific): FORM_MAP gives the name
    and types; pokemon_movesets.json a form's own stats/types where it has an entry ("<id>_<form>" or the form's id);
    species_data.json its abilities; pokemon_levels.json its own learnset. Shadow and Mega forms have their own pages."""
    global _MS
    if _MS is None:
        _MS = load("pokemon_movesets.json")
    base = _MS.get(str(pid)) or {}
    out = []
    for fid, m in sorted(F.FORMS.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 0):
        if m.get("id") != pid or m.get("form") in ("shadow", "mega", None):
            continue
        form = m["form"]
        ms = _MS.get(f"{pid}_{form.lower()}") or _MS.get(str(fid)) or {}
        types = m.get("types") or ms.get("types") or base.get("types") or []
        nm = F.fix(m.get("name") or form.title())
        nm = " ".join(w if w[:1].isupper() or w in ("-",) else w.capitalize() for w in nm.split(" "))
        f = {"id": int(fid), "n": nm, "k": REGIONAL.get(form, "Other form"), "t": [t.title() for t in types]}
        if ms.get("stats"):
            f["s"] = [ms["stats"].get(x) for x in STATS]
        s = sp.get(str(fid)) or {}
        if s.get("abilities"):
            f["ab"] = [(ab.get(a) or {}).get("name") or a.title() for a in s["abilities"]]
        if s.get("hidden"):
            f["hab"] = (ab.get(s["hidden"]) or {}).get("name") or s["hidden"].title()
        if ls.get(str(fid)):
            f["ls"] = [[int(lv), mv] for lv, mv in ls[str(fid)]]
        pic = os.path.join(F.A, "sprites", "pokemon", f"{fid}.png")
        if os.path.exists(pic):
            from io import BytesIO
            from PIL import Image
            im = Image.open(pic).convert("RGBA")
            box = im.getbbox()
            if box:
                im = im.crop(box)
            buf = BytesIO()
            im.save(buf, "WEBP", lossless=True, method=6)
            f["pic"] = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
        out.append(f)
    return out


def movedex():
    moves = load("moves.json")
    tms = load("tms.json")
    tm_of = {v.get("move"): tm for tm, v in tms.items()}
    ls = load("pokemon_levels.json").get("learnsets", {})
    tml = load("tm_learners.json")
    out = {}
    for key, m in moves.items():
        out[key] = {"n": move_name(key), "t": (m.get("type") or "").title(), "c": (m.get("category") or "").title(),
                    "p": m.get("power"), "a": m.get("accuracy"), "pp": m.get("pp"), "pr": m.get("priority") or 0,
                    "e": m.get("effect") or "", "tm": tm_of.get(key), "lv": [], "tml": []}
    for pid, rows in ls.items():
        if not pid.isdigit() or int(pid) > 1025:
            continue
        for lv, mv in rows:
            if mv in out:
                out[mv]["lv"].append([int(pid), int(lv)])
    for mv, pids in tml.items():
        if mv in out:
            out[mv]["tml"] = sorted(int(p) for p in pids if int(p) <= 1025)
    for m in out.values():
        m["lv"].sort()
    return out


def region_dexes():
    """{region: [national ids]} in the region's own order, as the game's Pokedex lists it (pokedex.region_dex)."""
    starts = {}
    for name in ("pokemon_area_data.json", "johto_area_data.json", "orange_area_data.json", "hoenn_area_data.json",
                 "sinnoh_area_data.json", "unova_area_data.json", "orre_area_data.json"):
        d = load(name)
        rs = d.get("REGION_START") or (d.get("GAME_CONFIG") or {}).get("REGION_START") or {}
        starts.update({k: v for k, v in rs.items() if isinstance(v, dict)})
    out = {}
    for r, cfg in starts.items():
        if cfg.get("dex_list"):
            ids = list(cfg["dex_list"])
        elif cfg.get("dex_range"):
            lo, hi = cfg["dex_range"]
            ids = list(dict.fromkeys(list(range(lo, hi + 1)) + list(cfg.get("dex_extra") or [])))
        else:
            continue
        out[r] = [int(i) for i in ids if int(i) <= 1025]
    return out


def region_maps(slug):
    """{REGION: {"img", "w", "h", "pts": {place slug: [x, y, name]}}} from map_points.json's region_maps."""
    from PIL import Image
    mp = load("map_points.json").get("region_maps") or {}
    out = {}
    for r, v in mp.items():
        p = os.path.join(F.A, v.get("file") or "")
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB")
        buf = BytesIO()
        im.quantize(256).convert("RGB").save(buf, "WEBP", lossless=True, method=6)
        pts = {}
        for k, xy in (v.get("points") or {}).items():
            if k in F.MAPS:
                pts[slug(k)] = [xy[0], xy[1], F.fix((F.PLACES.get(k) or {}).get("route_name") or k.replace("_", " ").title())]
        out[r] = {"img": "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode(), "w": im.width, "h": im.height,
                  "pts": pts}
    return out
