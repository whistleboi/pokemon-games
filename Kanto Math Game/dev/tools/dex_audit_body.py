# Dex audit (11-16; Jordan: "In each region, all of that dex's mons must be available in the first playthrough somehow: catching,
# evolution, in-game trading, non-canon placements we agreed on, gifts, shops, events"). Glue after dev/checks/harness_head.py:
#   cat dev/checks/harness_head.py dev/tools/dex_audit_body.py > dev/checks/out/dex_audit.py; python dev/checks/out/dex_audit.py <scratch> [REGION...]
# Counts, for each region's own dex (REGION_START dex_range + dex_extra), every way inside that region's own areas:
# wild pools the areas reference (walk/day/night/surf/rods/trees/rock smash...), the area's own rod pools and the region's rod pools,
# bosses, gifts, Eggs, trades (the Pokemon you GET), Game Corner prizes, fossils, roamers, and then evolution (into this region's dex
# only) and breeding (pre-evolutions, where the region has a Day Care). Prints what is still missing, with how close each one is.
import json, re
from src.states.game_corner import PRIZES

A = g.loader.area_data
P = A["STORY_PROGRESSION"]
T = json.load(open("assets/town_maps.json", encoding="utf-8"))
EV = json.load(open("assets/pokemon_evolutions.json", encoding="utf-8"))
N2I = dict(g.name_to_id) if hasattr(g, "name_to_id") else {}
I2N = {v: k for k, v in N2I.items()}
STARTS = A.get("REGION_START", {})
try:
    from src.states.overworld import town_kanto as _tk
    FOSSILS = next(v for k, v in vars(_tk).items() if isinstance(v, type) and hasattr(v, "FOSSILS")).FOSSILS
except Exception:
    FOSSILS = {}
FOSSIL_REGION = {138: "KANTO", 140: "KANTO", 142: "KANTO", 345: "HOENN", 347: "HOENN"}
ROAMERS = {"JOHTO": [243, 244]}
CODE_GIFTS = {"KANTO": {106: "Dojo (town_kanto.visit_dojo)", 107: "Dojo (town_kanto.visit_dojo)"}, "JOHTO": {133: "Bill's Eevee (town_johto.py)", 152: "Elm, after the title: the two you didn't pick (town_story.visit_prof_elm)", 155: "Elm, after the title (the two you didn't pick)", 158: "Elm, after the title (the two you didn't pick)"}, "HOENN": {380: "Soaring: Latias", 381: "Soaring: Latios"}}   # (gifts written in code)
from src.world import story_events as _se
SE = _se.EVENTS

regions = [a for a in sys.argv[2:]] or ["KANTO", "JOHTO", "HOENN"]


SEEN = set()


def ids_in(o, out, why, where):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("boss", "area_boss") and isinstance(v, dict) and str(v.get("id", "")).isdigit():
                out.setdefault(int(v["id"]), set()).add(f"{why}:{where}")
            elif k == "gift_pokemon":
                if isinstance(v, dict) and any(isinstance(w, list) for w in v.values()):   # ({your starter: the ones you get}: Birch's
                    v = [y for w in v.values() for y in (w if isinstance(w, list) else [w])]   # two you didn't pick, 11-24 - all count;
                                                                                               # one per starter (Unova's monkey) stays as it was)
                for x in (v if isinstance(v, list) else [v]):
                    x = x.get("id") if isinstance(x, dict) else x
                    if str(x).isdigit():
                        out.setdefault(int(x), set()).add(f"gift:{where}")
            elif k == "gift_egg" and str(v).isdigit():
                out.setdefault(int(v), set()).add(f"egg:{where}")
            elif k == "trade" and isinstance(v, dict) and str(v.get("give", "")).isdigit():
                out.setdefault(int(v["give"]), set()).add(f"trade:{where}")
            elif k == "choose" and isinstance(v, dict) and (v.get("pokemon") or v.get("egg")):   # (pick a Pokemon or an Egg: Birch's bag, the rooftop seller)
                for c in v.get("choices") or []:
                    if str(c.get("value")).isdigit():
                        out.setdefault(int(c["value"]), set()).add(f"pick:{where}")
            elif k == "catch_id" and str(v).isdigit():
                out.setdefault(int(v), set()).add(f"catch:{where}")
            elif re.match(r"POKEMON_(\d+)$", str(k)):
                out.setdefault(int(str(k)[8:]), set()).add(f"gift:{where}")
            elif k == "battle" and isinstance(v, dict) and v.get("catchable") and v.get("team"):
                for x in v["team"]:
                    out.setdefault(int(x), set()).add(f"boss:{where}")
            else:
                if isinstance(v, str) and v in SE and (where.split("/")[0], v) not in SEEN:   # (one visit an event an area: events can name each other)
                    SEEN.add((where.split("/")[0], v)); ids_in(SE[v], out, "story", f"{where}/{v}")
                ids_in(v, out, why, where)
    elif isinstance(o, list):
        for x in o:
            ids_in(x, out, why, where)


def pool_ids(name_or_dict):
    d = A.get(name_or_dict) if isinstance(name_or_dict, str) else name_or_dict
    if not isinstance(d, dict):
        return []
    out = []
    for k in d:
        m = re.match(r"^(\d+)", str(k))
        if m:
            out.append(int(m.group(1)))
    return out


def evo_targets(pid):
    n = I2N.get(pid)
    return [N2I[t.upper()] for t in (EV.get(n) or []) if t.upper() in N2I] if n else []


RULES = json.load(open("assets/pokemon_levels.json", encoding="utf-8"))["pairs"]   # ("a>b": {"item": ...}) how each step evolves
ITEM_KEYS = ("gift_item", "stock", "extra_stock", "hidden", "rewards", "gift_cycle", "items")


def items_in(o, out, _seen=None):
    """Every item key this data can hand over: gifts, rewards, shop stock, hidden items, found balls."""
    _seen = set() if _seen is None else _seen
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("gift_item", "rewards") and isinstance(v, dict):
                out.update(str(x) for x in v)
            elif k in ("stock",) and isinstance(v, list):
                out.update(str(x) for x in v if isinstance(x, str))
            elif k == "extra_stock" and isinstance(v, list):
                out.update(str(x.get("item")) for x in v if isinstance(x, dict))
            elif k == "hidden" and isinstance(v, dict):
                out.update(str(x) for x in v.values())
            elif k == "gift_cycle" and isinstance(v, list):
                out.update(str(x) for x in v)
            elif k == "choose" and isinstance(v, dict) and v.get("gift"):   # (pick one item: Gateon's Eevee expert, the Bay Cave fossil)
                out.update(str(c.get("value")) for c in v.get("choices") or [])
            elif isinstance(v, str) and v in SE and v not in _seen:   # (each story event once: they can name each other)
                _seen.add(v)
                items_in(SE[v], out, _seen)
            items_in(v, out, _seen)
    elif isinstance(o, list):
        for x in o:
            items_in(x, out, _seen)


PRE = {}
for n, ts in EV.items():
    if n in N2I and isinstance(ts, list):
        for t in ts:
            if str(t).upper() in N2I:
                PRE.setdefault(N2I[str(t).upper()], set()).add(N2I[n])

for region in regions:
    st = STARTS.get(region, {})
    lo, hi = st.get("dex_range", [0, 0]); extra = set(st.get("dex_extra", []))
    dex = (set(range(lo, hi + 1)) if hi else set()) | extra
    allowed = lambda t: t <= hi or t in extra
    if st.get("dex_list"):   # (a dex that is a list, not a range: the Orange Islands' 120, plus its extras; 11-17, Jordan)
        dex = set(st["dex_list"]) | extra
        allowed = lambda t, _d=frozenset(dex): t in _d
    areas = [k for k in P if story.area_region(k) == region and isinstance(P[k], dict)]
    got = {}
    for k in areas:
        a = P[k]
        for f, v in a.items():
            if "pool" in f and isinstance(v, (str, dict)):
                for pid in pool_ids(v):
                    got.setdefault(pid, set()).add(f"wild:{k}")
        _fishable = a.get("can_fish") or any(f"{k}_{r}_PERCENTAGES" in A for r in ("OLD_ROD", "GOOD_ROD", "SUPER_ROD"))   # (route_actions.fishable, 11-19)
        for rod in ("OLD_ROD", "GOOD_ROD", "SUPER_ROD"):
            if _fishable:
                for nm in (f"{k}_{rod}_PERCENTAGES", f"{region}_{rod}_POOL_PERCENTAGES"):
                    for pid in pool_ids(nm):
                        got.setdefault(pid, set()).add(f"fish:{k}")
        ids_in(a, got, "boss", k)
        if k in T:
            ids_in(T[k], got, "map", k)
            for fl in (T[k].get("floors") or []):
                ids_in(fl, got, "map", k)
        for city, prizes in PRIZES.items():
            if city == k:
                for kind, pid, _c in prizes:
                    if kind == "POKEMON":
                        got.setdefault(int(pid), set()).add(f"prize:{k}")
    for pid, r in FOSSIL_REGION.items():
        if r == region:
            got.setdefault(pid, set()).add("fossil")
    if region == "JOHTO":                       # (src/world/odd_egg.py: Route 34's Day-Care Man, seven Odd Eggs)
        from src.world import odd_egg as _odd
        for pid in _odd.SPECIES:
            got.setdefault(pid, set()).add("odd egg")
        from src.states.overworld.common import PRIMO_EGGS   # (Violet Center's Primo: Mareep, Wooper, Slugma Eggs - 11-19)
        for pid in PRIMO_EGGS:
            got.setdefault(pid, set()).add("Primo's Egg")
    from src.world import swarms as _sw   # (swarms, after the National Dex: src/world/swarms.py - a species, or (kind, species))
    for _a, e in (_sw.SWARMS.get(region) or {}).items():
        got.setdefault(int(_sw._entry(e)[1]), set()).add(f"swarm:{_a}")
    _fm = A.get("FORM_MAP") or {}
    for k in areas:
        for _stn, sps in ((P[k].get("radio_sounds") or {}).items()):   # (HGSS's Hoenn / Sinnoh Sound on the radio: src/world/radio.py)
            for pid in sps or []:
                got.setdefault(int(pid), set()).add(f"radio {_stn}:{k}")
        for sh in P[k].get("shadow_pool") or []:   # (Orre: Shadow Pokemon snagged from trainers, purified to the species)
            sid = str(sh.get("id") if isinstance(sh, dict) else sh)
            pid = (_fm.get(sid) or {}).get("id") if sid in _fm else (int(sid) if sid.isdigit() and int(sid) < 1000 else None)
            if pid:
                got.setdefault(int(pid), set()).add(f"snag:{k}")
    for pid, why in CODE_GIFTS.get(region, {}).items():
        got.setdefault(pid, set()).add(why)
    if region == "HOENN":
        for pid in pool_ids("HOENN_UNDERWATER_POOL_PERCENTAGES"):
            got.setdefault(pid, set()).add("dive")
    for k in areas:   # (a drawn map's floor with its own wild list: dungeon.py "pool"; Shoal Cave's Ice room, 11-23)
        for _f in (T.get(k) or {}).get("floors") or []:
            if _f.get("pool") and _f["pool"] not in ("NO_WILD_INDOORS_PERCENTAGES", "HOENN_UNDERWATER_POOL_PERCENTAGES"):
                for pid in pool_ids(_f["pool"]):
                    got.setdefault(pid, set()).add(f"floor:{k}")
    for pid in ROAMERS.get(region, []):
        got.setdefault(pid, set()).add("roamer")
    starters = [int(x) for x in st.get("starters", [])]   # (one run gets ONE starter: they're added after the closure, one pick only;
                                                          #  Kanto 11-24 - the two you didn't pick need another source)
    daycare = any('"DAYCARE"' in json.dumps(P[k]) for k in areas)
    have_items = set()
    for k in areas:
        items_in(P[k], have_items)
        if k in T:
            items_in(T[k], have_items)
        for kind, it, _c in PRIZES.get(k, []):
            if kind == "ITEM":
                have_items.add(str(it))
        for _src in (P[k], T.get(k) or {}):   # (Battle Points counters: src/world/battle_points.py SHOPS; 11-23, Hoenn's Razor Claw)
            _txt = json.dumps(_src)
            if '"BP_SHOP"' in _txt:
                from src.world import battle_points as _bp
                for _o in re.findall(r'\{[^{}]*"action": "BP_SHOP"[^{}]*\}', _txt):
                    _shop = (re.search(r'"shop": "(\w+)"', _o) or [None, "emerald"])[1]
                    for _it, _bpc in (_bp.SHOPS.get(_shop) or (None, []))[1] or []:
                        if not str(_it).startswith("TM:"):
                            have_items.add(str(_it))
    if any(k in ("CELADON_CITY", "GOLDENROD_CITY") or P[k].get("department_store") for k in areas):   # (mart.py: a department store
        from src.states.systems.mart import PokeMartState as _PM                                             #  sells every evolution item a
        from src.pokemon import items as _it                                                                 #  Pokemon here can use)
        evo_items = set(g.loader.evolution_map.get("EVOLUTION_ITEMS", {})) | set(getattr(_it, "DEPARTMENT", []))
        have_items |= {i for i in evo_items if i not in getattr(_PM, "NEVER_SOLD", ())}
    need_item = {}
    base = set(got)
    # closure: evolution into this region's dex, breeding back down where there's a Day Care
    reach = set(base); changed = True
    while changed:
        changed = False
        for pid in list(reach):
            for t in evo_targets(pid):
                it = (RULES.get(f"{pid}>{t}") or {}).get("item"); it = {"UP_GRADE": "UPGRADE"}.get(it, it)   # (loader.ITEM_ALIASES)
                if it and it not in have_items:
                    need_item[t] = it; continue
                if allowed(t) and t not in reach:
                    reach.add(t); got.setdefault(t, set()).add(f"evolve:{I2N.get(pid, pid)}"); changed = True
            if daycare:
                for p in PRE.get(pid, ()):
                    if allowed(p) and p not in reach:
                        reach.add(p); got.setdefault(p, set()).add(f"breed:{I2N.get(pid, pid)}"); changed = True
    # (the starter you pick: one family, given after everything else - the one a run is likeliest to lack; the others need their own way)
    left = [s for s in starters if s not in reach]
    pick = left[0] if left else None
    unpicked = left[1:]
    if pick is not None:
        reach.add(pick); got.setdefault(pick, set()).add("starter (your pick)")
        changed = True
        while changed:
            changed = False
            for pid in list(reach):
                for t in evo_targets(pid):
                    it = (RULES.get(f"{pid}>{t}") or {}).get("item"); it = {"UP_GRADE": "UPGRADE"}.get(it, it)
                    if (not it or it in have_items) and allowed(t) and t not in reach:
                        reach.add(t); got.setdefault(t, set()).add(f"evolve:{I2N.get(pid, pid)}"); changed = True
    missing = sorted(dex - reach)
    print(f"===== {region}: dex {len(dex)} ({lo}-{hi} + {len(extra)} extra), {len(areas)} areas, Day Care {daycare}: "
          f"obtainable {len(dex & reach)}, MISSING {len(missing)}")
    for pid in missing:
        pre = PRE.get(pid, set())
        hint = ""
        if pre:
            hint = "evolves from " + ", ".join(f"{I2N.get(p, p)}#{p}{'(have)' if p in reach else ''}" for p in sorted(pre))
        print(f"   #{pid:<4} {I2N.get(pid, '?'):14} {hint}{'  NEEDS ' + need_item[pid] + ' (not found in this region)' if pid in need_item else ''}"
              f"{'  (a starter you did not pick: no other source)' if pid in unpicked else ''}")
    if len(left) > 1:
        print(f"   starters: {len(left)} of {len(starters)} families come only as the starter - one run gets one, so {len(left) - 1} stay out")
    print("   only by evolving/breeding (no direct source):", len([p for p in dex & reach if p not in base]))
    # (11-19: everything this region offers, not only its dex - for the canon-vs-ours comparison: <scratch>/obtainable_<REGION>.json)
    every = set(base); changed = True
    while changed:
        changed = False
        for pid in list(every):
            for t in evo_targets(pid):
                it = (RULES.get(f"{pid}>{t}") or {}).get("item"); it = {"UP_GRADE": "UPGRADE"}.get(it, it)
                if (not it or it in have_items) and t not in every:
                    every.add(t); got.setdefault(t, set()).add(f"evolve:{I2N.get(pid, pid)}"); changed = True
            if daycare:
                for p in PRE.get(pid, ()):
                    if p not in every:
                        every.add(p); got.setdefault(p, set()).add(f"breed:{I2N.get(pid, pid)}"); changed = True
    json.dump({str(p): sorted(got.get(p, [])) for p in sorted(every) if 0 < p < 1000},
              open(f"{S}/obtainable_{region}.json", "w", encoding="utf-8"), indent=0)
