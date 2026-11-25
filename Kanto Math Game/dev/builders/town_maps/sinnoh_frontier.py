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
    j = johto_maps["JOHTO_BATTLE_FRONTIER"]   # (11-22 later: Johto's is the right way round now - Tower north, gate south)
    e = copy.deepcopy(j)
    e["exits"] = {}
    e["buildings"] = {"A": "sgate", "G": "stower", "B": "sfactory", "C": "shall", "E": "scastle", "F": "sarcade"}
    names = dict(ROOMS, jtower="stower", jgate="sgate")
    e["inside"] = {k: names.get(v, v) for k, v in j["inside"].items()}
    rooms = {}
    titles = {"sfactory": "Battle Factory", "shall": "Battle Hall", "scastle": "Battle Castle", "sarcade": "Battle Arcade"}
    for old, new in ROOMS.items():
        r = copy.deepcopy(j["rooms"][old])
        r["title"] = titles[new]
        rooms[new] = r
    # the gate (D32R0101): the plaza up top, the Fight Area down its stairs (Johto's go to Frontier Access)
    g = copy.deepcopy(j["rooms"]["jgate"])
    g["exits"] = {ch: ("FIGHT_AREA" if v == "FRONTIER_ACCESS" else v) for ch, v in g["exits"].items()}
    g["people"] = [{"text": "Gate attendant", "action": "EVENT", "event": {"lines": [
        "Welcome to the Battle Frontier! Five facilities and their Frontier Brains are waiting for you.",
        "The way back to the Fight Area is down the stairs behind me."]}}]
    rooms["sgate"] = g
    rooms["stower"] = copy.deepcopy(j["rooms"]["jtower"])   # (the Battle Tower's lobby, D31R0201)
    e["rooms"] = rooms
    # the Exchange Service Corner's stalls: Platinum's lists (HGSS's without U-turn)
    e["people"] = [dict(p, shop={"hgss_items": "plat_items", "hgss_tms": "plat_tms"}.get(p.get("shop"), p.get("shop")))
                   if isinstance(p, dict) else p for p in (e.get("people") or [])]
    return e


def apply(maps):
    """The Frontier built from Johto's map - keeping, room by room, the people Sinnoh gave its facility rooms (S8 11-25:
    Platinum's townsfolk, kanto_handoff/sinnoh_map_tools/sfolk.py, written by s_folk.py into sinnoh.py's own copy)."""
    from . import johto as _J
    own = maps.get(KEY) or {}
    built = build(_J.MAPS)
    for name, room in (built.get("rooms") or {}).items():
        mine = (own.get("rooms") or {}).get(name) or {}
        if len(mine.get("people") or []) > len(room.get("people") or []) and len(mine.get("art") or []) == len(room.get("art") or []):
            room["art"], room["people"] = list(mine["art"]), list(mine["people"])
    maps[KEY] = built
