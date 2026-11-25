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
    art = [list(r) for r in e["art"]]   # (the road south of the gate, SoulSilver's way on to Frontier Access: a dead end here,
    for y in (79, 80, 81):              #  and Platinum's plaza has no ground under it)
        for x in range(44, 54):
            if art[y][x] == "=":
                art[y][x] = "c"
    e["art"] = ["".join(r) for r in art]
    for o in [e] + list(rooms.values()):   # (11-25, Jordan: "Switch to Platinum's" - drawn with Platinum's own models, the same
        _platinum(o)                     #  zones as SoulSilver's; kanto_handoff/sinnoh_map_tools/pexport3d.py -> assets/pt_3d)
    from .sinnoh_frontier_rooms import ROOMS as _PT   # (the gate and the four facilities: Platinum's own rooms - walk grid,
    for name, pr in _PT.items():                    #  doors, attendant, townsfolk; s_s8_frontier_rooms.py. Johto's were
        r = rooms[name]                             #  drawn to SoulSilver's tilted room pictures)
        r["art"], r["people"] = list(pr["art"]), copy.deepcopy(pr["people"])
        r["roofs"] = {"_picture": {"f": f"pt_ground/{pr['zone']}.png", "at": [0, 0]}}
        r.pop("overheads", None)
        r.pop("land", None)
    return e


def _platinum(o):
    """A part's look: Platinum's scene for its zone (pt_ground/<zone>, the same crop), SoulSilver's flat overheads gone, and
    no "_screen" (that marks SoulSilver's room pictures)."""
    rf = o.get("roofs") if isinstance(o.get("roofs"), dict) else None
    pic = (rf or {}).get("_picture")
    if isinstance(pic, dict) and str(pic.get("f", "")).startswith("ss_ground/"):
        pic["f"] = "pt_ground/" + pic["f"].split("/", 1)[1]
        pic.pop("px", None)
        rf.pop("_screen", None)
    if o.get("overheads"):
        o["overheads"] = [h for h in o["overheads"] if not str(h.get("f", "")).startswith("ss_top/")]
        if not o["overheads"]:
            o.pop("overheads")


def apply(maps):
    from . import johto as _J
    maps[KEY] = build(_J.MAPS)
