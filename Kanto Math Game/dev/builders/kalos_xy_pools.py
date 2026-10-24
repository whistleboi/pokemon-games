"""Kalos wild pools from the real X/Y encounter tables (PokeAPI), so the X/Y Kalos dex (457) can be
completed in Kalos (Jordan, 10-23). Safe to re-run: species already in a pool keep their weight; each
X/Y species found at a location joins that area's pool weighted by its X/Y chance; fishing species go
to the Kalos rod pools. Run from the game folder:
    python dev/builders/kalos_xy_pools.py dev/builders/data/kalos_xy_encounters.json
(fetch_kalos_encounters.py re-downloads that file; data/kalos_xy_dex.json is the X/Y dex from PokeAPI)."""
import json
import re
import sys

ENC = json.load(open(sys.argv[1]))
P = "assets/kalos_area_data.json"
raw = open(P, encoding="utf-8", newline="").read()
d = json.loads(raw)
sp = d["STORY_PROGRESSION"]
XY = set(d["REGION_START"]["KALOS"]["dex_list"])

SKIP = {"friend-safari", "roaming-kalos", "unknown-dungeon", "kalos-berry-fields", "team-flare-secret-hq"}
RENAME = {"kalos-victory-road": "VICTORY_ROAD_KALOS"}
# Towns can't be searched for wild Pokemon here: their X/Y grass/surf species live on the next route.
TOWN_TO_ROUTE = {"AQUACORDE_TOWN": "KALOS_ROUTE_2", "LUMIOSE_CITY": "KALOS_ROUTE_5", "CYLLAGE_CITY": "KALOS_ROUTE_8",
                 "AMBRETTE_TOWN": "KALOS_ROUTE_8", "SHALOUR_CITY": "KALOS_ROUTE_12", "TOWER_OF_MASTERY": "KALOS_ROUTE_12",
                 "LAVERRE_CITY": "KALOS_ROUTE_14", "COURIWAY_TOWN": "KALOS_ROUTE_18", "POKEMON_VILLAGE": "KALOS_ROUTE_20"}
RODS = {"old-rod": "OLD", "good-rod": "GOOD", "super-rod": "SUPER"}
SKIP_METHODS = {"gift", "gift-egg", "only-one", "roaming-grass", "roaming-water", "pokeflute", "squirt-bottle",
                "wailmer-pail", "devon-scope", "island-scan"}


def to_100(w):
    tot = sum(w.values())
    sc = {k: v * 100 / tot for k, v in w.items()}
    out = {k: max(1, int(v)) for k, v in sc.items()}
    diff = 100 - sum(out.values())
    order = sorted(sc, key=lambda k: sc[k] - int(sc[k]), reverse=diff > 0)
    i = 0
    while diff:
        k = order[i % len(order)]
        if diff > 0:
            out[k] += 1; diff -= 1
        elif out[k] > 1:
            out[k] -= 1; diff += 1
        i += 1
    return out


adds = {}   # pool name -> {species: chance}
rods = {r: {} for r in RODS.values()}
for loc, mons in ENC.items():
    if loc in SKIP:
        continue
    area = RENAME.get(loc, loc.upper().replace("-", "_"))
    area = TOWN_TO_ROUTE.get(area, area)
    a = sp.get(area)
    pool = a and a.get("wild_pool_percentages")
    for pid, e in mons.items():
        if int(pid) not in XY:
            continue
        methods = [m for m in e["methods"] if m not in SKIP_METHODS]
        for m in methods:
            if m in RODS:
                rods[RODS[m]][pid] = rods[RODS[m]].get(pid, 0) + max(1, e["chance"])
        if pool and any(m not in RODS for m in methods):
            adds.setdefault(pool, {})
            adds[pool][pid] = max(adds[pool].get(pid, 0), e["chance"])


def replace_pool(key, new):
    global raw
    m = re.search(r'("%s": )(\{[^{}]*\})' % re.escape(key), raw)
    assert m, key
    raw = raw[:m.start(2)] + json.dumps(new).replace('{"', '{ "').replace('}', ' }') + raw[m.end(2):]


changed = 0
for key, new in adds.items():
    pool = dict(d[key])
    fresh = {k: v for k, v in new.items() if k not in pool}
    if not fresh:
        continue
    total = sum(pool.values())
    for k, chance in fresh.items():
        pool[k] = max(1, chance) * total / 100  # X/Y chance as a share of the existing pool
    replace_pool(key, to_100(pool))
    changed += 1
for rod, mons in rods.items():
    key = f"KALOS_{rod}_ROD_POOL_PERCENTAGES"
    if mons:
        pool = dict(d.get(key, {}))
        pool.update({k: v for k, v in mons.items() if k not in pool})
        replace_pool(key, to_100(pool))
json.loads(raw)
open(P, "w", encoding="utf-8", newline="").write(raw)
print("pools changed:", changed, "| rod pools:", {r: len(m) for r, m in rods.items()})
