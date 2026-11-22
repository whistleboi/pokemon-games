"""Sinnoh's Battle Frontier (Platinum; Jordan 11-22: "Do we have any battle plaza type place in sinnoh yet? If not, that is
the next place to build, using all of the DS camera knowledge learned").

HeartGold / SoulSilver reused Platinum's Frontier: zone D32 and its rooms are the same in both game files, walls tile for
tile (6 of 9,216 plaza tiles differ; the Tower lobby D31R0201, the gate D32R0101 and the four facility rooms D32R0301-0601
not at all: kanto_handoff/sinnoh_map_tools/cache vs johto_map_tools/cache). So Sinnoh's Frontier is built from Johto's
(dev/builders/town_maps/johto.py), with SoulSilver's own pictures and live 3D scenes (the DS camera: ss_ground / ss_3d),
and Platinum's own doors:
  - the north building (48,17) is the Battle Tower: its lobby (D31R0201), the Tower attendant at the counter;
  - the south building (48,52) is the gate (D32R0101): the plaza at its top, the Fight Area down its stairs (C11), as in
    Platinum;
  - the Factory, Hall, Castle and Arcade as Johto's, each with Sinnoh's own attendant (src/world/frontier.py SINNOH_FIVE);
  - the Exchange Service Corner's two stalls with Platinum's lists (battle_points: plat_items, plat_tms).
The facilities are simple streaks (no special rules: Jordan 11-22). Area data: sinnoh_area_data.json SINNOH_BATTLE_FRONTIER."""
import copy

KEY = "SINNOH_BATTLE_FRONTIER"
ROOMS = {"jfactory": "sfactory", "jhall": "shall", "jcastle": "scastle", "jarcade": "sarcade"}


def _set(art, x, y, ch):
    art[y] = art[y][:x] + ch + art[y][x + 1:]


def build(johto_maps):
    j = johto_maps["JOHTO_BATTLE_FRONTIER"]
    e = copy.deepcopy(j)
    art = list(e["art"])
    # the Battle Tower's door at the top of the plaza (Johto's map had a way out there: Platinum's Tower)
    for x, ch in ((47, "G"), (48, "D"), (49, "D"), (50, "G")):
        _set(art, x, 17, ch)
    e["art"] = art
    e["exits"] = {}
    e["buildings"] = {"A": "sgate", "G": "stower", "B": "sfactory", "C": "shall", "E": "scastle", "F": "sarcade"}
    e["inside"] = {k: ROOMS.get(v, "sgate" if v == "jtower" else v) for k, v in j["inside"].items()}
    e["inside"].update({"48,17": "stower", "49,17": "stower"})
    rooms = {}
    titles = {"sfactory": "Battle Factory", "shall": "Battle Hall", "scastle": "Battle Castle", "sarcade": "Battle Arcade"}
    for old, new in ROOMS.items():
        r = copy.deepcopy(j["rooms"][old])
        r["title"] = titles[new]
        rooms[new] = r
    # the gate (D32R0101): the plaza up top, the Fight Area down the stairs at the bottom (the game's warps, zone row 20)
    g = copy.deepcopy(j["rooms"]["jtower"])
    w = len(g["art"][0])
    art_g = list(g["art"])
    last = max(y for y, row in enumerate(art_g) if "." in row)   # (the stairs: in the wall row under the room's last open row)
    art_g[last + 1] = art_g[last + 1][:6] + "nnn" + art_g[last + 1][9:]
    if last + 2 >= len(art_g):
        art_g.append("c" * w)
    g["art"] = art_g
    g["exits"] = dict(g["exits"], n="FIGHT_AREA")
    g["people"] = [{"text": "Gate attendant", "action": "EVENT", "event": {"lines": [
        "Welcome to the Battle Frontier! Five facilities and their Frontier Brains are waiting for you.",
        "The way back to the Fight Area is down the stairs behind me."]}}]
    g["title"] = "Gate"
    g["land"] = {"48,52": [48, 50], "49,52": [49, 50]}   # (its door faces the plaza, north: out onto the tile above it, not below)
    rooms["sgate"] = g
    # the Battle Tower's lobby (D31R0201): Johto's "Frontier Access" map was drawn from it; its lift (^) is behind the counter
    fa = johto_maps["FRONTIER_ACCESS"]
    t = {"theme": "room", "art": [row.replace("^", "c") for row in fa["art"]], "exits": {"v": "OUT:48,17"},
         "buildings": {}, "roofs": copy.deepcopy(fa["roofs"]), "overheads": copy.deepcopy(fa.get("overheads") or []),
         "people": ["Tower attendant"] + copy.deepcopy(fa.get("people") or [])[1:], "title": "Battle Tower"}
    rooms["stower"] = t
    e["rooms"] = rooms
    # the Exchange Service Corner's stalls: Platinum's lists (HGSS's without U-turn)
    e["people"] = [dict(p, shop={"hgss_items": "plat_items", "hgss_tms": "plat_tms"}.get(p.get("shop"), p.get("shop")))
                   if isinstance(p, dict) else p for p in (e.get("people") or [])]
    return e


def apply(maps):
    from . import johto as _J
    maps[KEY] = build(_J.MAPS)
