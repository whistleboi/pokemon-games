"""python dev/builders/unova_wild.py : Black 2's own wild Pokemon for Unova's walkable places (11-20).

Reads kanto_handoff/unova_map_tools/uwild.py (a/1/2/7, by each zone header's wild field) and writes each area's
"wild_tables" (src/world/wild_tables.py: per season, per kind: grass, dark grass, rustling grass, surf, rippling water,
fish, rippling fish; each slot with its own levels) into assets/unova_area_data.json, as text (the file's layout kept).
The area's older pools follow from the same tables so the Pokedex's area lists agree: <AREA>_PERCENTAGES = its grass,
"surf_pool_percentages" -> <AREA>_SURF_PERCENTAGES, <AREA>_SUPER_ROD_PERCENTAGES = its fishing (B2W2 has one rod).
Add a place to PLACES as its batch is built."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(os.path.dirname(HERE))
for _up in range(6):   # (the tools folder above the game folder, from the main folder or a worktree: 11-23)
    _cand = os.path.join(os.path.abspath(os.path.join(GAME, *[".."] * _up)), "kanto_handoff", "unova_map_tools")
    if os.path.isdir(_cand):
        sys.path.insert(0, _cand)
        break
sys.path.insert(0, os.path.join(os.path.dirname(GAME), "..", "kanto_handoff", "unova_map_tools"))
sys.path.insert(0, os.path.join(GAME, "..", "..", "kanto_handoff", "unova_map_tools"))

PLACES = {"ASPERTIA_CITY": 427, "UNOVA_ROUTE_19": 437, "UNOVA_ROUTE_20": 446, "FLOCCESY_RANCH_OUTSIDE": 444,
          "FLOCCESY_RANCH": 445, "VIRBANK_CITY": 448, "VIRBANK_COMPLEX_OUTSIDE": 456, "VIRBANK_COMPLEX": 457,
          "CASTELIA_SEWERS": 495, "CASTELIA_EMPTY_LOT": 500,
          "UNOVA_ROUTE_4": 326, "DESERT_RESORT_ENTRANCE": 157, "DESERT_RESORT": 158, "RELIC_CASTLE": 160,   # (batch 3b, 11-21)
          "UNOVA_ROUTE_16": 383, "LOSTLORN_FOREST": 385, "UNOVA_ROUTE_5": 329,   # (batch 4a, 11-23)
          "DRIFTVEIL_DRAWBRIDGE": 253,   # (batch 5a, 11-24: its "rustle" slots are the bridge's bird shadows)
          "RELIC_PASSAGE": 503, "RELIC_PASSAGE_MIDDLE": 504, "RELIC_PASSAGE_NORTH": 505,   # (batch 5b: "rustle" = dust clouds)
          "RELIC_CASTLE_DEPTHS": 175,
          "UNOVA_ROUTE_6": 331, "MISTRALTON_CAVE": 333, "MISTRALTON_CAVE_2F": 334, "GUIDANCE_CHAMBER": 335,   # (batch 6a, 11-24)
          "CHARGESTONE_CAVE": 195, "CHARGESTONE_CAVE_B1F": 196, "CHARGESTONE_CAVE_B2F": 197,
          "UNOVA_ROUTE_7": 337, "CELESTIAL_TOWER_2F": 339, "CELESTIAL_TOWER_3F": 340, "CELESTIAL_TOWER_4F": 341,   # (batch 6b)
          "CELESTIAL_TOWER_ROOF": 342,
          "REVERSAL_MOUNTAIN": 461, "REVERSAL_MOUNTAIN_INSIDE": 533, "STRANGE_HOUSE": 462,
          "REVERSAL_MOUNTAIN_ENTRY": 531, "REVERSAL_MOUNTAIN_SOUTH": 535,
          "UNDELLA_TOWN": 412, "UNDELLA_BAY": 240, "UNOVA_ROUTE_13": 370,   # (batch 7b)
          "UNOVA_ROUTE_12": 368, "VILLAGE_BRIDGE": 255, "UNOVA_ROUTE_11": 365,   # (batch 8a)
          "UNOVA_ROUTE_9": 348,   # (batch 8b)
          "HUMILAU_CITY": 465, "UNOVA_ROUTE_22": 474, "UNOVA_ROUTE_21": 463, "SEASIDE_CAVE": 515, "SEASIDE_CAVE_B1F": 516,   # (batch 9a)
          "GIANT_CHASM": 231, "GIANT_CHASM_FOREST": 232, "GIANT_CHASM_CAVE": 234,   # (batch 9b-2)
          "UNOVA_ROUTE_23": 475, "VICTORY_ROAD_UNOVA": 573, "VICTORY_ROAD_CAVE_1F": 587, "VICTORY_ROAD_GROVE": 588,
          "VICTORY_ROAD_RIVER": 589, "VICTORY_ROAD_CAVE_2F": 590, "VICTORY_ROAD_2F_BACK": 591, "VICTORY_ROAD_MOUNTAINSIDE": 592,
          "VICTORY_ROAD_3F": 593, "VICTORY_ROAD_TUNNEL": 228,   # (batch 10a)
          "N_CASTLE": 596,   # (batch 11c: the Zoroark's cave; the castle has no wild Pokemon)
          "PINWHEEL_FOREST": 155, "PINWHEEL_FOREST_OUTSIDE": 154, "UNOVA_ROUTE_3": 321, "WELLSPRING_CAVE": 324,
          "WELLSPRING_CAVE_B1F": 325, "DREAMYARD": 152, "DREAMYARD_B1F": 153, "UNOVA_ROUTE_2": 319, "UNOVA_ROUTE_1": 317, "STRIATON_CITY": 6, "NUVEMA_TOWN": 389, "UNOVA_ROUTE_8": 345, "MOOR_OF_ICIRRUS": 346, "ICIRRUS_CITY": 113, "DRAGONSPIRAL_TOWER": 205,   # (batch 12a)
          "UNOVA_ROUTE_14": 374, "ABUNDANT_SHRINE": 376, "UNOVA_ROUTE_15": 378, "MARVELOUS_BRIDGE": 263}   # (batch 11a)   # (batch 7a: both versions' chambers share the tables)
# Unova two years ago (batch 12c, 11-25): run with --white to read Pokemon White's own tables into the past's areas.
PLACES_W1 = {"PAST_UNOVA_ROUTE_1": 317, "PAST_UNOVA_ROUTE_2": 319, "PAST_STRIATON_CITY": 6, "PAST_DREAMYARD": 152,
             "PAST_DREAMYARD_B1F": 153, "PAST_NUVEMA_TOWN": 389}
P = os.path.join(GAME, "assets", "unova_area_data.json")
NL = "\r\n"


def _block(text, key, indent):
    pat = NL + " " * indent + json.dumps(key) + ": "
    if pat not in text:   # (a few areas sit deeper in the file: Skyarrow Bridge, the Driftveil Drawbridge)
        import re
        hit = re.search(re.escape(NL) + r"( +)" + re.escape(json.dumps(key) + ": "), text)
        pat = NL + hit.group(1) + json.dumps(key) + ": "
    i = text.index(pat) + len(NL)
    j = i + len(pat) - len(NL)
    opener = text[j]
    close = {"{": "}", "[": "]"}[opener]
    depth, k, ins = 0, j, False
    while True:
        c = text[k]
        if ins:
            if c == "\\":
                k += 2
                continue
            if c == '"':
                ins = False
        elif c == '"':
            ins = True
        elif c == opener:
            depth += 1
        elif c == close:
            depth -= 1
            if depth == 0:
                return i, k + 1
        k += 1


def _dump(key, val, indent):
    return " " * indent + json.dumps(key) + ": " + json.dumps(val, indent=2, ensure_ascii=False).replace("\n", NL + " " * indent)


def _put(raw, key, val, indent, after=None):
    """Replace "key": ... at this indent, or add it after the entry `after` (top level) / at the end of its block."""
    if (NL + " " * indent + json.dumps(key) + ": ") in raw:
        a, b = _block(raw, key, indent)
        return raw[:a] + _dump(key, val, indent) + raw[b:]
    a, b = _block(raw, after, indent)
    return raw[:b] + "," + NL + _dump(key, val, indent) + raw[b:]


def merged(tb, tw):
    """One table for both versions (Jordan 11-20: the version pick changes the story, never the wild Pokemon; every species
    in one playthrough): a slot where White 2 has another species splits in two, Black 2's and White 2's, each at half its
    chance and at its own levels (the Virbank Complex: Magby and Elekid). A form-only difference (Basculin's stripes) keeps
    Black 2's: our data has one Basculin."""
    out = {}
    for season, kinds in tb.items():
        out[season] = {}
        for kind, slots in kinds.items():
            other = (tw.get(season) or tw.get("ALL") or {}).get(kind) or []
            rows = []
            for i, s in enumerate(slots):
                w = other[i] if i < len(other) else None
                if w and w[0] != s[0]:
                    rows.append([s[0], s[1], s[2] / 2, s[3], s[4]])
                    rows.append([w[0], w[1], w[2] / 2, w[3], w[4]])
                else:
                    rows.append(list(s))
            out[season][kind] = rows
    return out


def main():
    import g5map
    import uwild
    import nds5
    Z = g5map.Zones()
    white = nds5.GAME == "W1"
    ZW = None if white else g5map.Zones(nds5.W2)   # (White 2's file: its Pokemon go in the same tables, 11-20; not for the past)
    raw = open(P, encoding="utf-8", newline="").read()
    data = json.loads(raw)
    sp = data["STORY_PROGRESSION"]
    for area, zid in (PLACES_W1 if white else PLACES).items():
        t = uwild.tables(Z, zid)
        a = sp[area]
        if not t:
            continue
        t = merged(t, uwild.tables(ZW, zid)) if ZW else t
        a["wild_tables"] = t
        a.pop("wild_tables_by_version", None)

        def union(kind):
            out = {}
            for season in t.values():
                for s, _f, c, _lo, _hi in season.get(kind) or []:
                    out[str(s)] = out.get(str(s), 0) + c
            total = sum(out.values()) or 1
            return {k: max(1, round(v * 100 / total)) for k, v in sorted(out.items(), key=lambda kv: -kv[1])}
        grass, surf, fish = union("grass"), union("surf"), union("fish")
        if grass:
            key = a.get("wild_pool_percentages") or f"{area}_PERCENTAGES"
            a["wild_pool_percentages"] = key
            raw = _put(raw, key, grass, 2, after="UNOVA_SUPER_ROD_POOL_PERCENTAGES")
            lo = min(s[3] for season in t.values() for s in season.get("grass") or [])
            hi = max(s[4] for season in t.values() for s in season.get("grass") or [])
            a["wild_levels"] = {"land": [lo, hi]}
        if surf:
            a["surf_pool_percentages"] = f"{area}_SURF_PERCENTAGES"
            raw = _put(raw, f"{area}_SURF_PERCENTAGES", surf, 2, after="UNOVA_SUPER_ROD_POOL_PERCENTAGES")
        if fish:
            raw = _put(raw, f"{area}_SUPER_ROD_PERCENTAGES", fish, 2, after="UNOVA_SUPER_ROD_POOL_PERCENTAGES")
        raw = _put(raw, area, a, 4)
        print(area, "seasons" if len(t) > 1 else "all year", {k: len(v) for k, v in next(iter(t.values())).items()})
    json.loads(raw)
    open(P, "w", encoding="utf-8", newline="").write(raw)


if __name__ == "__main__":
    main()
