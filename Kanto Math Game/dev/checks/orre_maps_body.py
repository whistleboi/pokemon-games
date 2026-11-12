# Orre's walkable maps (dev/builders/town_maps/orre.py, from the fan game Pokemon Orre 2.1.1), walked the way a player would.
#   cat dev/checks/harness_head.py dev/checks/orre_maps_body.py > dev/checks/out/check_orre_maps.py
#   python dev/checks/out/check_orre_maps.py <scratch dir>
import json as _json
from collections import deque as _dq
from src.states.overworld import CityState as _CS
from src.states.overworld.walk_town import WalkTownState as _WTS

fails = 0
g.walk_towns = True


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def frames(p, n=1):
    for _ in range(n):
        g.current_state.update()
        g.current_state.draw()


def _tap_through(st, n=400):
    for _ in range(n):
        if not getattr(st, "npc_active", False):
            return
        st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        frames(st)


def town(area, came):
    g.walk_town_pos = None
    story.current_area_key, story.last_area_key = area, came
    st = _CS(g); g.change_state(st); _tap_through(st)
    return st


def path(t, a, b):
    """Steps a player can walk from a to b (b itself may be a door or a person: walked up to)."""
    prev, q = {a: None}, _dq([a])
    while q:
        cur = q.popleft()
        if cur == b:
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (cur[0] + dx, cur[1] + dy)
            if nxt in prev:
                continue
            if nxt == b or (t._open(nxt) and nxt not in t.exits and nxt not in t._people()):
                prev[nxt] = cur; q.append(nxt)
    if b not in prev:
        return None
    out, cur = [], b
    while cur is not None:
        out.append(cur); cur = prev[cur]
    return out[::-1]


def walk_to(t, b):
    """Walk there step by step through the game's own step(): every move must be taken."""
    p = path(t, tuple(t.player), b)
    if not p:
        return False
    for (x0, y0), (x1, y1) in zip(p, p[1:]):
        t.anim = 0
        t.step(x1 - x0, y1 - y0)
        t.anim = 0
        if (x1, y1) != b and tuple(t.player) != (x1, y1):
            return False
    return True


_tm = _json.load(open("assets/town_maps.json", encoding="utf-8"))
_sp = _json.load(open("assets/dungeon_sprites.json", encoding="utf-8-sig"))
_m = _tm["PHENAC_CITY"]

# ---- in from the desert
story.story_flags.pop("phenac_cipher_beaten", None); story.story_flags.pop("got_snag_machine", None)
t = town("PHENAC_CITY", "ORRE_DESERT")
check(isinstance(t, _WTS) and (t.w, t.h) == (52, 70), f"Phenac City: walked, 52 x 70 as the fan game's map ({type(t).__name__})")
check(tuple(t.player) == (43, 31) and t.exits.get((44, 31)) == "ORRE_DESERT", f"in from the Desert Trail at the east gate {t.player}")
check(sorted(set(t.doors.values())) == ["center", "cycle", "gym", "house", "mart", "mayor"] and "PRESTIGE_PRECEPT_CENTER" in t.exits.values(),
      f"its doors: Center, Mart, Stadium, Mayor's house, two houses, the bike; the Pre Gym's door into the Prestige Precept Center {sorted(set(t.doors.values()))}")
_ov = getattr(t, "overheads", [])
check(len(_ov) == 1,
      f"the fan game's top layer (palm tops, roof edges) is laid over the player: {len(_ov)} picture")

# ---- every door, walked to from the gate, in and out
_area = g.loader.area_data["PHENAC_CITY"] if "PHENAC_CITY" in g.loader.area_data else None
for _name, _want in (("center", ["HEAL"]), ("mart", ["SHOP"]), ("gym", ["GYM"]), ("mayor", [])):
    t = town("PHENAC_CITY", "ORRE_DESERT")
    _door = next(tuple(int(v) for v in d.split(",")) for d, n in _m["inside"].items() if n == _name)
    _ok = walk_to(t, _door)
    check(_ok and t.room == _name, f"walk from the east gate to the {_name} door at {_door} and in ({t.room})")
    if t.room != _name:
        continue
    _acts = sorted({str((o if "any" not in o else next((x for x in o["any"] if t._shown(x)), {})).get("action")).upper()
                    for o in t._people().values()} - {"EVENT"})
    check(all(a in _acts for a in _want), f"  {_name}: who stands inside does {_want} ({len(t.people)} people: {_acts})")
    _mat = next(k for k, v in t.exits.items() if v.startswith("OUT:"))
    _ok = walk_to(t, _mat)
    frames(t, 2)
    check(t.room is None and tuple(t.player) == (_door[0], _door[1] + 1), f"  and out by its mat, below the door again {t.player}")

# ---- the Mayor's house upstairs and down
t = town("PHENAC_CITY", "ORRE_DESERT")
_door = next(tuple(int(v) for v in d.split(",")) for d, n in _m["inside"].items() if n == "mayor")
walk_to(t, _door)
_up = next((k for k, v in t.exits.items() if v == "ROOM:mayor_2f"), None)
_ok = _up is not None and walk_to(t, _up)
check(t.room == "mayor_2f", f"the Mayor's house: up the stairs to the second floor ({t.room})")
_down = next((k for k, v in t.exits.items() if v == "ROOM:mayor"), None)
_x = _down is not None and t.player != _down
_ok = _down is not None and (walk_to(t, _down) if t.player != _down else True)
check(t.room == "mayor" and t._open(tuple(t.player)), f"  and back down ({t.room} at {t.player})")

# ---- the bike at the town's foot: the rides out, each as the story opens it
t = town("PHENAC_CITY", "ORRE_DESERT")
_bike = next(k for k, v in t.doors.items() if v == "cycle")
check(walk_to(t, (_bike[0], _bike[1] - 1)), f"walk down the main street to the bike at {_bike}")
_now = [o["target_area"] for o in t._door_options("cycle")]
story.story_flags["got_snag_machine"] = True
_later = [o["target_area"] for o in t._door_options("cycle")]
check(_now == [] and _later == ["PYRITE_TOWN"], f"  the bike rides to Pyrite only once you have the Snag Machine ({_now} -> {_later})")
story.story_flags.pop("got_snag_machine", None)

# ---- people: at the fan game's own spots, with the fan game's own sheets
t = town("PHENAC_CITY", "ORRE_DESERT")
_texts = [(o.get("text") if "any" not in o else "/".join(x.get("text") for x in o["any"])) for o in t.people.values()]
_missing = [k for k in _texts if not (_sp["figures"].get(f"PHENAC_CITY:{k}") or {}).get("sheet")]
_files = [v["sheet"] for k, v in _sp["figures"].items() if k.startswith("PHENAC_CITY:")]
check(not _missing and all(os.path.exists(f"assets/dungeon/characters/{f}") for f in _files),
      f"every person in Phenac and its rooms has the fan game's own sheet ({len(_files)} sheets; without one: {_missing})")
check("Trouble at the Fountain" in [o.get("text") for o in t._people().values()] and "Meet Rui" not in [o.get("text") for o in t._people().values()],
      "the Cipher Peons stand at the fountain; Rui is not there yet")
story.story_flags["phenac_cipher_beaten"] = True
t = town("PHENAC_CITY", "ORRE_DESERT")
check("Meet Rui" in [o.get("text") for o in t._people().values()], "after the Peons are beaten, Rui waits at the town's foot")
story.story_flags.pop("phenac_cipher_beaten", None)
_rui = next(s for s, o in t.people.items() if o.get("text") == "Meet Rui")
check(path(t, tuple(t.player), _rui) is not None, f"  and you can walk up to her at {_rui}")

# ---- out the east gate to the Desert Trail
t = town("PHENAC_CITY", "PYRITE_TOWN")
check(t._open(tuple(t.player)), f"in from Pyrite (by the bike): you stand on open ground {t.player}")
walk_to(t, (43, 31))
t.anim = 0; t.step(1, 0)
for _ in range(240):
    if story.current_area_key == "ORRE_DESERT":
        break
    frames(g.current_state)
check(story.current_area_key == "ORRE_DESERT",
      f"east through the gate: out to the Desert Trail ({story.current_area_key}, {type(g.current_state).__name__})")

# ---- every Orre town: in by its bike, every door walked to, in and out; its people there; the bike's rides
_area = _json.load(open("assets/orre_area_data.json", encoding="utf-8"))["STORY_PROGRESSION"]
_orre = [k for k in _tm if _area.get(k, {}).get("region") == "ORRE" and "__" not in k and _area[k].get("area_type") == "town"
         and any(v == "cycle" for v in _tm[k].get("buildings", {}).values())]
check(len(_orre) >= 8, f"Orre's walked towns with a motorbike: {_orre}")
for _key in _orre:
    _m = _tm[_key]
    _tv = [o for o in _area[_key].get("travel_options", []) if o.get("door") == "cycle"]
    _came = _tv[0]["target_area"] if _tv else _area[_key]["travel_options"][0]["target_area"]
    t = town(_key, _came)
    _bike = next((d for d, k in t.doors.items() if k == "cycle"), None)
    check(isinstance(t, _WTS) and _bike is not None and t._open(tuple(t.player)) and abs(t.player[0] - _bike[0]) + abs(t.player[1] - _bike[1]) <= 3,
          f"{_key}: walked; in from {_came} by the motorbike, beside it {t.player} (bike {_bike})")
    _bad, _n = [], 0
    for _d, _name in _m["inside"].items():
        _door = tuple(int(v) for v in _d.split(","))
        t = town(_key, _came)
        if not walk_to(t, _door) or t.room != _name:
            _bad.append((_name, _door, "in", t.room)); continue
        _want = len(_m["rooms"][_name].get("people", []))
        if len(t.people) != _want or not t._open(tuple(t.player)):
            _bad.append((_name, "people", len(t.people), _want)); continue
        _mat = next((k for k, v in t.exits.items() if v == "OUT:" + _d), None) or next((k for k, v in t.exits.items() if v.startswith("OUT:")), None)
        if _mat is None or not walk_to(t, _mat):
            _bad.append((_name, "no way back out")); continue
        frames(t, 2)
        if t.room is not None:
            _bad.append((_name, "still inside", t.room)); continue
        _n += 1
    check(not _bad, f"  {_key}: {_n} doors walked to from the bike, in, the right number of people, out again {_bad[:3]}")
    for _rn, _r in _m["rooms"].items():   # (rooms reached only from another room: every floor's way on leads somewhere real)
        for _v in _r["exits"].values():
            if _v.startswith("ROOM:") and _v[5:] not in _m["rooms"]:
                check(False, f"  {_key}/{_rn}: a stair to a room that isn't built ({_v})")
    t = town(_key, _came)
    _rides = [o.get("target_area") or o.get("text") for o in t._door_options("cycle")]
    check(set(o["target_area"] for o in _tv if t._shown(o)) <= set(_rides), f"  {_key}: the bike offers the rides open now {_rides}")

# ---- Agate's cave mouth: purify at the Relic Stone, or go into the cave; Gateon's sailor: the boat
t = town("AGATE_VILLAGE", "PYRITE_CAVE")
_rel = [o.get("text") for o in t._door_options("relic")]
check("Purify at the Relic Stone" in _rel and any(o.get("target_area") == "RELIC_CAVE" for o in t._door_options("relic")),
      f"Agate: the Relic Cave's mouth offers the Relic Stone and the cave {_rel}")
t = town("GATEON_PORT", "PHENAC_CITY")
_sail = [o for o in t.people.values() if "any" in o]
check(any(any(x.get("target_area") == "XD_CITADARK_ISLE" for x in o["any"]) for o in _sail), "Gateon: the sailor at the dock runs the boat to Citadark Isle")
check(any(o.get("text") == "Professor Krane's Lab" for o in t._door_options("cycle")), "Gateon: the bike rides out to Professor Krane's lab")

# ---- the ride: off from Phenac by bike, the desert crossing plays, and you arrive
story.story_flags["got_snag_machine"] = True
t = town("PHENAC_CITY", "PYRITE_TOWN")
_opt = next(o for o in t._door_options("cycle") if o.get("target_area") == "PYRITE_TOWN")
t._get_callback_for_option(_opt)()
_st = g.current_state
_ride = getattr(_st, "ride", None)
for _ in range(60):
    _st.update(); _st.draw()
os.makedirs(S, exist_ok=True); pygame.image.save(g.screen, os.path.join(S, "ride.png"))
for _ in range(400):
    if story.current_area_key == "PYRITE_TOWN":
        break
    st = g.current_state
    box = getattr(st, "dialogue_box", None)
    if box is not None and getattr(box, "visible", True) and not box.is_finished:
        box.is_finished = True
    st.update(); st.draw()
check(_ride is not None and story.current_area_key == "PYRITE_TOWN", f"the ride: Phenac to Pyrite by motorbike, the desert crossing shown, arrived ({story.current_area_key})")
story.story_flags.pop("got_snag_machine", None)

# ---- Orre's walked dungeons: each loads as the game's dungeon, starts you by the way you came, and every passage between
# its floors lands you on open floor of the floor it names
from src.states.overworld import PlayState as _PS
from src.states.overworld.dungeon import DungeonState as _DS
g.dungeon_routes = True


def route(area, came):
    story.current_area_key, story.last_area_key = area, came
    p = _PS(g); g.states["play"] = p; g.change_state(p)
    for _ in range(3):
        g.current_state.update(); g.current_state.draw()
    return g.current_state


_dung = [k for k in _tm if _area.get(k, {}).get("region") == "ORRE" and _tm[k].get("floors")]
check(len(_dung) >= 18, f"Orre's walked dungeons: {len(_dung)} {_dung}")
for _key in _dung:
    _m = _tm[_key]
    _came = next((t for f in _m["floors"] for t in f.get("exits", {}).values()), None)
    r = route(_key, _came)
    if not isinstance(r, _DS):
        check(False, f"{_key}: loads as a dungeon ({type(r).__name__})"); continue
    run = r.run
    _ok = run.n_floors == len(_m["floors"]) and run.floor.walkable(*run.player)
    _bad = []
    for i, f in enumerate(_m["floors"]):
        for k, (j, x, y) in (f.get("links") or {}).items():
            run.warp(i, *[int(v) for v in k.split(",")])
            run.warp(j, x, y)
            if run.index != j or not run.floor.walkable(*run.player):
                _bad.append((i, k, j))
    check(_ok and not _bad, f"{_key}: {run.n_floors} floors, in from {_came} on open floor, every passage lands on open floor {_bad[:3]}")
t = town("UNDER_COLOSSEUM", "THE_UNDER")
_d = next(tuple(int(v) for v in d.split(",")) for d in _tm["UNDER_COLOSSEUM"]["inside"])
_in = walk_to(t, _d) and t.room == "gym" and [str(o.get("action")).upper() for o in t.people.values()] == ["GYM"]
_mat = next((k for k, v in t.exits.items() if v.startswith("OUT:")), None)
_out = _mat is not None and walk_to(t, _mat) and t.room is None
check(isinstance(t, _WTS) and t.exits.get(tuple(t.player)) is None and _in and _out,
      f"the Under Colosseum: in from The Under, through the lobby into the arena (its host runs the Colosseum) and back out")
_lib = route("SS_LIBRA", "GATEON_PORT")
_lib.run.warp(1, 4, 3)
_crates = [t for t, w in _lib.run.floor.decor.items() if str(w).startswith("crate:")]
check(len(_crates) >= 3, f"the S.S. Libra's deck has its crates in the way ({len(_crates)}), pushed aside by the slide puzzle")
_kam = _tm["KAMINKO_HOUSE"]["floors"][2]
_same = [k for k, v in _kam["links"].items() if v[0] == 2]
check(len(_same) >= 10, f"Kaminko's crane floor: {len(_same)} hook pads, each carrying you to its colour's twin")

# ---- Realgam: the dome door opens the tower's lobby; its doors lead to the Tower Dome, Cipher's Colosseum and the Deep Colosseum
t = town("REALGAM_TOWER", "PHENAC_CITY")
_d = next(tuple(int(v) for v in d.split(",")) for d, n in _tm["REALGAM_TOWER"]["inside"].items() if n == "realgam")
_in = walk_to(t, _d) and t.room == "realgam"
_ways = set(t.exits.values())
_up = next((k for k, v in t.exits.items() if v == "ROOM:colosseum"), None)
_col = _up is not None and walk_to(t, _up) and t.room == "colosseum" and [str(o.get("action")).upper() for o in t.people.values()] == ["GYM"]
check(_in and {"CIPHER_COMMAND", "DEEP_COLOSSEUM", "ROOM:colosseum"} <= _ways and _col,
      f"Realgam: the dome door opens the lobby; out to the Tower Dome and the Deep Colosseum, up to Cipher's Colosseum and its host ({sorted(_ways)})")


# ---- the walkthroughs' gates: shut until their key, disk or samples are found, then open
def _bars(area, came, floor):
    r = route(area, came)
    r.run.warp(floor, *r.run.floors[0].start) if floor else None
    r._clear_boulders()
    return {t for t, w in r.run.floor.decor.items() if str(w).startswith("barrier:")}


for _area, _came, _fl, _flags in (("SHADOW_PKMN_LAB", "THE_UNDER", 0, ["orre_maingate_key"]),
                                   ("SHADOW_PKMN_LAB", "THE_UNDER", 1, ["orre_card_key"]),
                                   ("SHADOW_PKMN_LAB", "THE_UNDER", 2, ["orre_down_st_key"]),
                                   ("SHADOW_PKMN_LAB", "THE_UNDER", 3, ["orre_dna_1", "orre_dna_2", "orre_dna_3"]),
                                   ("XD_CIPHER_LAB", "GATEON_PORT", 2, ["xd_id_card"]),
                                   ("THE_UNDER", "PYRITE_TOWN", 0, ["orre_f_disk"]),
                                   ("THE_UNDER", "PYRITE_TOWN", 2, ["orre_u_disk"])):
    for _f in _flags:
        story.story_flags.pop(_f, None)
    _shut = _bars(_area, _came, _fl)
    for _f in _flags[:-1]:
        story.story_flags[_f] = True
    _still = _bars(_area, _came, _fl)
    story.story_flags[_flags[-1]] = True
    _open = _bars(_area, _came, _fl)
    for _f in _flags:
        story.story_flags.pop(_f, None)
    check(_shut and _still and not _open, f"{_area} floor {_fl}: shut ({len(_shut)}) until {' + '.join(_flags)}, then open")

_have = {k: [p if isinstance(p, str) else p.get("text") for f in _tm[k]["floors"] for p in f.get("people", [])] for k in ("SS_LIBRA", "XD_ONBS", "MT_BATTLE", "SHADOW_PKMN_LAB")}
check("REST IN THE BED" in _have["SS_LIBRA"] and "BONSLY" in _have["SS_LIBRA"] and "BONSLY'S GIRL" in _have["XD_ONBS"]
      and "F-DISK" in _have["MT_BATTLE"] and sum(1 for p in _have["SHADOW_PKMN_LAB"] if str(p).startswith("DNA SAMPLE")) == 3,
      "the S.S. Libra's bed and Bonsly, Bonsly's girl at ONBS, the F-Disk on Mt. Battle, the lab's three DNA samples stand on the maps")

g.walk_towns = False
print(f"##### {fails} failures")
