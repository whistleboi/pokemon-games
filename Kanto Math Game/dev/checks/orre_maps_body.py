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
for _name, _want in (("center", ["HEAL"]), ("mart", ["SHOP"]), ("gym", ["HEAL"]), ("mayor", [])):   # (R2: "gym" is the stadium's lobby now)
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
check("PYRITE_TOWN" not in _now and "PYRITE_TOWN" in _later and "OUTSKIRT_STAND" in _now,
      f"  the bike rides back to the Stand any time, to Pyrite once Phenac's guards are beaten ({_now} -> {_later})")
story.story_flags.pop("got_snag_machine", None)

# ---- people: at the fan game's own spots, with the fan game's own sheets
t = town("PHENAC_CITY", "ORRE_DESERT")
_texts = [(o.get("text") if "any" not in o else "/".join(x.get("text") for x in o["any"])) for o in t.people.values()]
_missing = [k for k in _texts if not any((_sp["figures"].get(f"PHENAC_CITY:{k}") or {}).get(w) for w in ("sheet", "pic", "item"))]   # (the sack: a picture; an item ball)
_files = [v["sheet"] for k, v in _sp["figures"].items() if k.startswith("PHENAC_CITY:") and "sheet" in v]   # (the sack is a picture: "pic")
check(not _missing and all(os.path.exists(f"assets/dungeon/characters/{f}") for f in _files),
      f"every person in Phenac and its rooms has the fan game's own sheet ({len(_files)} sheets; without one: {_missing})")
check("Shady Guy Folly" in [o.get("text") for o in t._people().values()] and "A big sack" not in [o.get("text") for o in t._people().values()],
      "Folly stands by the bike with the sack still shut (Colosseum's opening; orre_pilot plays it)")
story.story_flags["orre_phenac_folly"] = True
t = town("PHENAC_CITY", "ORRE_DESERT")
check("A big sack" in [o.get("text") for o in t._people().values()], "after Folly is beaten, the sack (Rui) waits at the town's foot")
_rui = next(s for s, o in t.people.items() if o.get("text") == "A big sack")
check(path(t, tuple(t.player), _rui) is not None, f"  and you can walk up to it at {_rui}")
story.story_flags.pop("orre_phenac_folly", None)

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
story.story_flags["xd_gateon_bridges"] = True   # (Gateon's island doors: over the bridges Makan fixes - shut before, checked below)
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
story.story_flags["met_agate_elder"] = story.story_flags["orre_beat_skrub"] = True   # (both open after Eagun and Skrub: batch 2)
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
_host = lambda st_: any(isinstance(o, dict) and (o.get("event") or {}).get("referee") for o in st_.people.values())   # (R2: the arena's host is the tournament's referee)
_in = walk_to(t, _d) and t.room == "gym" and _host(t)
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
story.story_flags["col_gonzap_realgam"] = True   # (the door up opens after Gonzap: batch 7b)
t = town("REALGAM_TOWER", "PHENAC_CITY")
_d = next(tuple(int(v) for v in d.split(",")) for d, n in _tm["REALGAM_TOWER"]["inside"].items() if n == "realgam")
_in = walk_to(t, _d) and t.room == "realgam"
_ways = set(t.exits.values())
_up = next((k for k, v in t.exits.items() if v == "ROOM:colosseum"), None)
_col = _up is not None and walk_to(t, _up) and t.room == "colosseum" and _host(t)
check(_in and {"CIPHER_COMMAND", "DEEP_COLOSSEUM", "ROOM:colosseum"} <= _ways and _col,
      f"Realgam: the dome door opens the lobby; out to the Tower Dome and the Deep Colosseum, up to Cipher's Colosseum and its host ({sorted(_ways)})")


# ---- the walkthroughs' gates: shut until their key, disk or samples are found, then open
def _bars(area, came, floor):
    r = route(area, came)
    r.run.warp(floor, *r.run.floors[0].start) if floor else None
    r._clear_boulders()
    return {t for t, w in r.run.floor.decor.items() if str(w).startswith("barrier:")}


for _area, _came, _fl, _flags in (("SHADOW_PKMN_LAB", "THE_UNDER", 0, ["orre_maingate_key"]),
                                   ("SHADOW_PKMN_LAB", "THE_UNDER", 1, ["orre_lab_shutter", "orre_card_key"]),   # (batch 4: the Shutter Switch too)
                                   ("SHADOW_PKMN_LAB", "THE_UNDER", 2, ["orre_down_st_key"]),
                                   ("SHADOW_PKMN_LAB", "THE_UNDER", 3, ["orre_dna_1", "orre_dna_2", "orre_dna_3"]),
                                   ("XD_CIPHER_LAB", "GATEON_PORT", 2, ["xd_id_card"]),
                                   ("THE_UNDER", "PYRITE_TOWN", 0, ["orre_f_disk", "orre_r_disk"]),   # (batch 4: F forward, R right)
                                   ("THE_UNDER", "PYRITE_TOWN", 12, ["orre_subway_bomb"])):   # (batch 4: the far station's blown door)
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


# ---- Gateon's islands (11-24): six movable bridges, raised till Makan; Cyle on the north island; up the lighthouse to the
# roof (Kilen); after the title its three guardians hold the stairs, and Jasmine waits on the roof
def _gate_room(t, room):
    _st = next((k for k, v in t.exits.items() if v == "ROOM:" + room), None)
    return _st is not None and walk_to(t, _st) and t.room == room


_isl = {n: tuple(int(v) for v in d.split(",")) for d, n in _tm["GATEON_PORT"]["inside"].items()}
for _f in ("xd_gateon_bridges", "orre_part2"):
    story.story_flags.pop(_f, None)
t = town("GATEON_PORT", "PHENAC_CITY")
check(len(t.barred) == 48 and path(t, tuple(t.player), _isl["lighthouse"]) is None,
      f"Gateon: the six bridges raised before Makan ({len(t.barred)} tiles), no way to the lighthouse")
story.story_flags["xd_gateon_bridges"] = True
t = town("GATEON_PORT", "PHENAC_CITY")
_ok = {n: path(t, tuple(t.player), d) is not None for n, d in _isl.items() if n in ("house_north", "house_island", "lighthouse")}
_cyle = any(isinstance(p, dict) and p.get("text") == "Casual Guy Cyle" for p in t.people.values())
check(not t.barred and all(_ok.values()) and _cyle, f"Gateon: the bridges down after Makan - the islands reached {_ok}; Cyle on the north island {_cyle}")
_up = walk_to(t, _isl["lighthouse"]) and t.room == "lighthouse" and _gate_room(t, "lighthouse_2f") and _gate_room(t, "lighthouse_3f")     and _gate_room(t, "lighthouse_roof")
_who = sorted(p.get("text") for p in t.people.values() if isinstance(p, dict) and t._shown(p)) if _up else []
check(_up and "Bodybuilder Kilen" in _who and "Gym Leader Jasmine" not in _who,
      f"Gateon lighthouse: up all three stairs to the roof (bridges down, no Gym yet), Kilen there, no Jasmine yet ({_who})")
story.story_flags["orre_part2"] = True   # (the lighthouse Gym: Part 2, story rework S1; badge 5 in S3)
t = town("GATEON_PORT", "PHENAC_CITY")
if g.current_state is not t:
    t = town("GATEON_PORT", "PHENAC_CITY")
_in = walk_to(t, _isl["lighthouse"]) and t.room == "lighthouse"
_held = _in and not _gate_room(t, "lighthouse_2f")
story.story_flags.update(gateon_lh_electabuzz=True, gateon_lh_electrode=True, gateon_lh_ampharos=True)
t = town("GATEON_PORT", "PHENAC_CITY")
_top = walk_to(t, _isl["lighthouse"]) and _gate_room(t, "lighthouse_2f") and _gate_room(t, "lighthouse_3f") and _gate_room(t, "lighthouse_roof")
_jas = _top and any(isinstance(p, dict) and p.get("text") == "Gym Leader Jasmine" and t._shown(p) for p in t.people.values())
check(_held and _jas, f"Gateon lighthouse in Part 2: the guardian holds the stairs ({_held}); past all three, Jasmine on the roof ({_jas})")
for _f in ("xd_gateon_bridges", "orre_part2", "gateon_lh_electabuzz", "gateon_lh_electrode", "gateon_lh_ampharos"):
    story.story_flags.pop(_f, None)

# ---- the story rework S1 (11-24): one journey - Colosseum, Evice, "five years later", XD. Gates by part, the time skip
_P1 = ("orre_part2", "orre_data_rom_given", "orre_ein_lab", "orre_evice_beaten")
for _f in _P1:
    story.story_flags.pop(_f, None)
t = town("PHENAC_CITY", "ORRE_DESERT")
_rides = [o.get("target_area") for o in t._door_options("cycle")]
_pre = [o.get("target_area") for o in t._door_options("pregym")]
check("GATEON_PORT" not in _rides and "REALGAM_TOWER" not in _rides and "PRESTIGE_PRECEPT_CENTER" in _pre,
      f"Part 1: no Gateon (XD) by bike, no Realgam before the Data ROM, the Pre Gym open ({_rides}, {_pre})")
story.story_flags["orre_ein_lab"] = True
t = town("PHENAC_CITY", "ORRE_DESERT")
check("GATEON_PORT" not in [o.get("target_area") for o in t._door_options("cycle")], "Part 1: Ein's Lab beaten - still no Gateon (XD waits for the time skip)")
story.story_flags["orre_data_rom_given"] = True
t = town("PHENAC_CITY", "ORRE_DESERT")
check("REALGAM_TOWER" in [o.get("target_area") for o in t._door_options("cycle")], "Part 1: the Data ROM to Nett opens Realgam Tower (Colosseum's order)")
_rg = _json.load(open("assets/orre_area_data.json", encoding="utf-8"))["STORY_PROGRESSION"]["REALGAM_TOWER"]["gym"]
from src.states.overworld.area_transition import is_league as _isl_league
check(_rg["leader"]["victory_flag"] == "orre_evice_beaten" and not _isl_league(_rg) and _rg["leader"].get("music") == "orre/evice_battle",
      "Realgam: Evice is Cipher's boss (no League, no title), his own battle theme")
from src.world import orre_skip as _skip
story.story_flags["orre_evice_beaten"] = True
t = town("REALGAM_TOWER", "PHENAC_CITY")
_said = []
_skip.event(t, {"world": "orre_skip"}, ["The roof of Realgam Tower falls silent."], lambda l: _said.extend(l))
_tap_through(t, 400)
for _ in range(60):
    if g.current_state is not t:
        break
    t.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))]); frames(t)
_st = g.current_state
_tap_through(_st, 800)
check(story.story_flags.get("orre_part2") and story.current_area_key == "POKEMON_HQ_LAB" and isinstance(_st, _WTS),
      f"the time skip: Evice beaten -> five years later, you arrive at the HQ Lab ({story.current_area_key}, {type(_st).__name__})")
t = town("PHENAC_CITY", "POKEMON_HQ_LAB")
check("GATEON_PORT" in [o.get("target_area") for o in t._door_options("cycle")], "Part 2: Gateon Port by bike after the skip")
from src.states.systems import pda as _pda
check(any(sub == "Please come" and "five years" in body for _frm, sub, body in _pda.mail(g)), "Part 2: Krane's e-mail after the skip")
_txt = open("assets/orre_area_data.json", encoding="utf-8").read() + open("assets/town_maps.json", encoding="utf-8").read()
import re as _re
check(not _re.search(r"Wes", _txt) and "beat_orre_champion" not in open("assets/town_maps.json", encoding="utf-8").read(),
      "the player by their own name (no 'Wes' left in Orre's lines); no map waits on the old title")
for _f in _P1:
    story.story_flags.pop(_f, None)

# ---- the story rework S2 (11-24): the four Part 1 Gyms - Misty (Phenac Stadium's final), Duking (Pyrite Colosseum's final),
# Blaine + Erika (the Agate Gym), Pryce (the Snagem Hideout's ruins); the Under and Orre Colosseums story tournaments
_SP = _json.load(open("assets/orre_area_data.json", encoding="utf-8"))["STORY_PROGRESSION"]
_chain = [(k, _SP[k]["gym"]["leader"].get("badge_reward"), _SP[k]["gym"]["requirements"]["badges"], _SP[k]["gym"]["leader"]["name"])
          for k in ("PHENAC_CITY", "PYRITE_TOWN", "AGATE_VILLAGE", "SNAGEM_HIDEOUT")]
check([b for _k, b, _n, _l in _chain] == ["PHENAC", "PYRITE", "AGATE", "SNAGEM"] and [n for _k, _b, n, _l in _chain] == [0, 1, 2, 3]
      and not _SP["UNDER_COLOSSEUM"]["gym"]["leader"].get("badge_reward") and not _SP["ORRE_COLOSSEUM"]["gym"]["leader"].get("badge_reward")
      and _SP["REALGAM_TOWER"]["gym"]["requirements"]["badges"] == 4,
      f"S2: the badges in order {[(b, l) for _k, b, _n, l in _chain]}; Under / Orre Colosseum crowns only; Realgam needs 4")
_mv = _json.load(open("assets/moves.json", encoding="utf-8"))
_bad = [(l, m) for _k, _b, _n, l in _chain for mm in _SP[_k]["gym"]["leader"]["team_moves"] for m in mm if m not in _mv]
_gen = [(l, i) for _k, _b, _n, l in _chain for i in _SP[_k]["gym"]["leader"]["team"] if i > 386]
check(not _bad and not _gen, f"S2: the Leaders' moves are real and their Pokemon Gen 3 or earlier {_bad[:3]} {_gen[:3]}")
# S2b (Jordan 11-24): Kanto's level caps at each badge (FireRed's 14, 21, 24, 29); the Under Colosseum between badges 3 and 4;
# no Pokemon under its species' min level, rounds below their Leader
_minlv = _json.load(open("assets/pokemon_levels.json", encoding="utf-8"))["min_level"]
_aces = [max(_SP[_k]["gym"]["leader"]["levels"]) for _k, _b, _n, _l in _chain]
_tops = {k: (max(max(t["levels"]) for t in _SP[k]["gym"]["trainers"]) if _SP[k]["gym"]["trainers"] else 0,
             max(_SP[k]["gym"]["leader"]["levels"])) for k in ("PHENAC_CITY", "PYRITE_TOWN", "UNDER_COLOSSEUM")}
_young = [(t["name"], p, lv) for k in ("PHENAC_CITY", "PYRITE_TOWN", "AGATE_VILLAGE", "UNDER_COLOSSEUM", "SNAGEM_HIDEOUT")
          for t in _SP[k]["gym"]["trainers"] + [_SP[k]["gym"]["leader"]] for p, lv in zip(t["team"], t["levels"])
          if _minlv.get(str(p), 1) > lv]
check(_aces == [14, 21, 24, 29] and all(a < b for a, b in _tops.values()) and 24 < _tops["UNDER_COLOSSEUM"][1] <= 29 and not _young,
      f"S2b: Part 1 at Kanto's caps - Leaders' best {_aces}, rounds under their final {_tops}, too young {_young[:3]}")
# L1 (Jordan 11-24): all of Orre at Kanto's caps, stage by stage (dev/builders/town_maps/orre_levels.py): each group's best
# under its cap, the story's bosses rising in order, nobody under its form's min level, the partners at Lv 10 / 11
import sys as _sys
_sys.path.insert(0, "dev/builders/town_maps")
import orre_levels as _OL
_TMJ = _json.load(open("assets/town_maps.json", encoding="utf-8"))
_all = []
for _a, _v in _SP.items():
    if isinstance(_v, dict):
        _all += [(_a, b, _OL.group(_a, gg, w)) for b, gg, w in _OL.battles(_v, _a)]
        if _a in _TMJ:
            _all += [(_a, b, _OL.group(_a, gg, w)) for b, gg, w in _OL.battles(_TMJ[_a], _a)]
_CAP = {"p1": 37, "mtb": 50, "p2": 48, "eagun": 50, "ag": 55, "post": 63}
_over = [(a, b.get("name"), max(b.get("levels") or [b.get("level")])) for a, b, gr in _all
         if b.get("name") not in _OL.SKIP_NAMES and max(b.get("levels") or [b.get("level")]) > _CAP[gr]]
_young2 = [(a, b.get("name"), p, lv) for a, b, gr in _all if isinstance(b.get("team"), list)
           for p, lv in zip(b["team"], b.get("levels") or []) if isinstance(p, int) and p < 2000 and _minlv.get(str(p), 1) > lv
           and b.get("name") not in _OL.SKIP_NAMES]


def _ace(area, name):
    return max((max(b["levels"]) for a, b, gr in _all if a == area and b.get("name") == name and b.get("levels")), default=None)


_order = [("Willie", _ace("OUTSKIRT_STAND", "Rider Willie") and min(max(b["levels"]) for a, b, gr in _all if b.get("name") == "Rider Willie")),
          ("Misty", 14), ("Duking", 21), ("Miror B.", _ace("PYRITE_CAVE", "Cipher Admin Miror B.")), ("Skrub", _ace("RELIC_CAVE", "Cipher Peon Skrub")),
          ("Blaine + Erika", 24), ("Dakim", _ace("MT_BATTLE", "Cipher Admin Dakim")), ("Venus", _ace("THE_UNDER", "Cipher Admin Venus")),
          ("Carben", max(_SP["UNDER_COLOSSEUM"]["gym"]["leader"]["levels"])), ("Ein", _ace("SHADOW_PKMN_LAB", "Cipher Admin Ein")),
          ("Pryce", 29), ("Nascour", max(_SP["REALGAM_TOWER"]["gym"]["trainers"][-1]["levels"])),
          ("Evice", max(_SP["REALGAM_TOWER"]["gym"]["leader"]["levels"])), ("Exol", _ace("XD_ONBS", "Cipher Cmdr Exol")),
          ("Gonzap", _ace("SNAGEM_HIDEOUT", "Snagem Head Gonzap") and max(max(b["levels"]) for a, b, gr in _all if b.get("name") == "Snagem Head Gonzap" and gr == "p2")),
          ("Greevil", max(max(b["levels"]) for a, b, gr in _all if b.get("name") == "Grand Master Greevil" and gr == "p2"))]
_lv = [x for _n, x in _order]
_rs = _json.load(open("assets/orre_area_data.json", encoding="utf-8"))["REGION_START"]["ORRE"]["starter_levels"]
check(not _over and not _young2 and None not in _lv and all(a <= b for a, b in zip(_lv, _lv[1:])) and _lv[12] == 37
      and _rs == {"196": 10, "197": 11},
      f"L1: Orre at Kanto's caps - over a cap {_over[:3]}, too young {_young2[:3]}, bosses in order {_order}, partners {_rs}")
# the Agate Gym's number garden (Jordan 11-24): vines on the way in till three gardens bloom; walked as a player would
t = town("AGATE_VILLAGE", "PYRITE_TOWN")
_gd = next(tuple(int(v) for v in d.split(",")) for d, n in _tm["AGATE_VILLAGE"]["inside"].items() if n == "gym")
for _f in [k for k in story.story_flags if k.startswith("agate_garden_done")]:
    story.story_flags.pop(_f)
_in0 = walk_to(t, _gd) and t.room == "gym"
_G = _tm["AGATE_VILLAGE"]["rooms"]["gym"]["gardens"]
_beds = {tuple(int(v) for v in k.split(",")) for gd in _G["gardens"] for k in gd["beds"]}
_shut = (21, 7) in t.barred


def _bed_walk(st, b):
    """Walk to bed b without stepping on any other bed (a player picking their way round the gardens)."""
    prev, q = {tuple(st.player): None}, _dq([tuple(st.player)])
    while q:
        cur = q.popleft()
        if cur == b:
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (cur[0] + dx, cur[1] + dy)
            if nxt in prev or (nxt != b and (nxt in _beds or not st._open(nxt) or nxt in st.exits or nxt in st._people() or nxt in st.barred)):
                continue
            prev[nxt] = cur; q.append(nxt)
    if b not in prev:
        return False
    way, cur = [], b
    while cur is not None:
        way.append(cur); cur = prev[cur]
    for (x0, y0), (x1, y1) in zip(way[::-1], way[::-1][1:]):
        st.anim = 0; st.step(x1 - x0, y1 - y0); st.anim = 0
    return tuple(st.player) == b


_g1 = {v: tuple(int(c) for c in k.split(",")) for k, v in _G["gardens"][0]["beds"].items()}
_over = _bed_walk(t, _g1[7]) and _bed_walk(t, _g1[6]) and not story.story_flags.get("agate_garden_done_0")   # (7 + 6 > 10: the vines grow back)
_sols = [(7, 3), (9, 6, 3), (12, 9, 6)]
_solved = True
for _i, _sol in enumerate(_sols):
    _bd = {v: tuple(int(c) for c in k.split(",")) for k, v in _G["gardens"][_i]["beds"].items()}
    for _n in _sol:
        _solved = _bed_walk(t, _bd[_n]) and _solved
    _solved = _solved and bool(story.story_flags.get(f"agate_garden_done_{_i}"))
    _tap_through(t)
check(_in0 and _shut and _over and _solved and story.story_flags.get("agate_garden_done") and (21, 7) not in t.barred,
      f"the Agate Gym's number garden: vines shut the way in ({_shut}); 7 + 6 overshoots 10 and resets ({_over}); 10, 18 and 27 "
      f"made by walking the beds ({_solved}); then Blaine burns the vines away")
t = town("AGATE_VILLAGE", "PYRITE_TOWN")
_in = walk_to(t, _gd) and t.room == "gym"
_deep = _in and (lambda st: (lambda e: e is not None and walk_to(st, e) and st.room == "gym_2")(next((k for k, v in st.exits.items() if v == "ROOM:gym_2"), None)))(t)
_lead = _deep and any(isinstance(o, dict) and o.get("action") == "GYM" for o in t.people.values())
check(_in and _deep and _lead, f"S2: the Agate Gym walked - through the hall of light to Blaine and Erika, the Gym's Leader there ({_in}, {_deep}, {_lead})")
for _f in ("orre_part2", "xd_hordel", "orre_data_rom_given"):
    story.story_flags.pop(_f, None)
story.story_flags["orre_data_rom_given"] = True
r = route("SNAGEM_HIDEOUT", "ORRE_DESERT")
_p1 = [o.get("text") for o in r._figure_items()]
_tr1 = [i for i, tr in enumerate(_SP["SNAGEM_HIDEOUT"]["trainer_pool"]) if story.trainer_on_map("SNAGEM_HIDEOUT", i, tr)]
story.story_flags.update(orre_part2=True, xd_hordel=True)
r = route("SNAGEM_HIDEOUT", "ORRE_DESERT")
_p2 = [o.get("text") for o in r._figure_items()]
_tr2 = [i for i, tr in enumerate(_SP["SNAGEM_HIDEOUT"]["trainer_pool"]) if story.trainer_on_map("SNAGEM_HIDEOUT", i, tr)]
check("GYM LEADER PRYCE" in _p1 and "SNAGEM HIDEOUT: GONZAP" not in _p1 and not _tr1
      and "GYM LEADER PRYCE" not in _p2 and "SNAGEM HIDEOUT: GONZAP" in _p2 and len(_tr2) == len(_SP["SNAGEM_HIDEOUT"]["trainer_pool"]),
      f"S2: the Snagem ruins - Pryce and no Snagem in Part 1; Gonzap and his gang in Part 2 after Hordel ({len(_tr2)} trainers)")
from src.world import orre_gym as _og
from src import minigames as _mg
for _f in ("orre_part2", "xd_hordel"):
    story.story_flags.pop(_f, None)
_saved_badges = list(story.badges.get("ORRE", []))
story.badges["ORRE"] = ["PHENAC", "PYRITE", "AGATE"]
r = route("SNAGEM_HIDEOUT", "ORRE_DESERT")
story.story_flags[_mg.done_flag("SNAGEM_HIDEOUT")] = True
_og.event(r, {"world": "orre_gym"}, [], lambda l: None)
_bs = getattr(g.current_state, "battle_state", None) or getattr(g.current_state, "next_state", None)
check(type(g.current_state).__name__ == "TrainerIntroState" and getattr(_bs, "badge_reward", None) == "SNAGEM",
      f"S2: Pryce's battle starts from his room (after his game) and gives the Snagem Badge ({type(g.current_state).__name__})")
story.story_flags.pop(_mg.done_flag("SNAGEM_HIDEOUT"), None)
story.story_flags.pop("orre_data_rom_given", None)

# ---- the story rework S3 (11-24): the four Part 2 Gyms - Jasmine (the Gateon lighthouse's roof), Norman (the Key Lair's hall,
# after Gorigan), Drake (Citadark's Dome 2F, before Greevil), Birch (Realgam's Colosseum in the sky, after Greevil)
_SP = _json.load(open("assets/orre_area_data.json", encoding="utf-8"))["STORY_PROGRESSION"]
_TMJ = _json.load(open("assets/town_maps.json", encoding="utf-8"))
_g2 = [(_SP[a][k]["leader"], _SP[a][k]["requirements"]) for a, k in
       (("GATEON_PORT", "gym"), ("XD_CIPHER_KEY_LAIR", "gym"), ("XD_CITADARK_ISLE", "gym"), ("REALGAM_TOWER", "gym_birch"))]
_ok_team = all(_OL.stage(p, lv) == p and p <= 386 for ld, _r in _g2 for p, lv in zip(ld["team"], ld["levels"]))
_ok_mv = all(m in _mv for ld, _r in _g2 for mm in ld["team_moves"] for m in mm)
check([ld["badge_reward"] for ld, _r in _g2] == ["GATEON", "KEY_LAIR", "CITADARK", "REALGAM"]
      and [r["badges"] for _l, r in _g2] == [4, 5, 6, 7] and [max(ld["levels"]) for ld, _r in _g2] == [41, 45, 48, 50]
      and all(len(ld["team"]) == 6 for ld, _r in _g2) and _ok_team and _ok_mv
      and _SP["ORRE_COLOSSEUM"]["gym"]["requirements"]["badges"] == 5,
      f"S3: Part 2's badges in order, six each at Kanto's caps (41/45/48/50), fit species and real moves")
_tr = {o["text"]: o.get("condition") for o in _SP["GATEON_PORT"]["travel_options"]}
check("has_gateon_badge" in (_tr.get("Cipher Lab") or []) and "has_key_lair_badge" in (_tr.get("Citadark Isle") or []),
      f"S3: the Cipher Lab waits for the Gateon Badge, Citadark for the Key Lair Badge ({_tr.get('Cipher Lab')}, {_tr.get('Citadark Isle')})")
_roof = _TMJ["GATEON_PORT"]["rooms"]["lighthouse_roof"]["people"]
_jas = next((p for p in _roof if isinstance(p, dict) and p.get("text") == "Gym Leader Jasmine"), {})
_gl = [p["boss"]["level"] for rn in ("lighthouse", "lighthouse_2f", "lighthouse_3f") for p in _TMJ["GATEON_PORT"]["rooms"][rn]["people"]
       if isinstance(p, dict) and p.get("action") == "BOSS"]
check((_jas.get("event") or {}).get("stages", [{}])[0].get("world") == "orre_gym" and _gl == [36, 37, 38],
      f"S3: Jasmine's roof battle is the Gym's (math game, then badge 5); the guardians Lv {_gl}")
story.story_flags.update(orre_part2=True)
story.badges["ORRE"] = ["PHENAC", "PYRITE", "AGATE", "SNAGEM", "GATEON"]
r = route("XD_CIPHER_KEY_LAIR", "GATEON_PORT")
_k1 = [o.get("text") for o in r._figure_items()]
story.story_flags["xd_gorigan_beaten"] = True
r = route("XD_CIPHER_KEY_LAIR", "GATEON_PORT")
_k2 = [o.get("text") for o in r._figure_items()]
story.story_flags[_mg.done_flag("XD_CIPHER_KEY_LAIR")] = True
_og.event(r, {"world": "orre_gym"}, [], lambda l: None)
_bs = getattr(g.current_state, "battle_state", None) or getattr(g.current_state, "next_state", None)
check("GYM LEADER NORMAN" not in _k1 and "GYM LEADER NORMAN" in _k2   # (Gorigan stands there once the floors' trainers are beaten)
      and "BATTLE CIPHER ADMIN GORIGAN" not in _k2 and type(g.current_state).__name__ == "TrainerIntroState"
      and getattr(_bs, "badge_reward", None) == "KEY_LAIR",
      f"S3: the Key Lair's hall - Gorigan first, then Norman on his spot; Norman's battle gives the Key Lair Badge ({_k1}, {_k2}, {type(g.current_state).__name__}, {getattr(_bs, 'badge_reward', None)})")
story.badges["ORRE"] += ["KEY_LAIR"]
r = route("XD_CITADARK_ISLE", "GATEON_PORT")
_c1 = [o.get("text") for o in r._figure_items()]
story.badges["ORRE"] += ["CITADARK"]
r = route("XD_CITADARK_ISLE", "GATEON_PORT")
_c2 = [o.get("text") for o in r._figure_items()]
check("GYM LEADER DRAKE" in _c1 and "GRAND MASTER GREEVIL" not in _c1 and "GRAND MASTER GREEVIL" in _c2 and "GYM LEADER DRAKE" not in _c2,
      f"S3: Citadark's arena - Drake on the spot first, Greevil once his badge is won")
story.story_flags["xd_greevil_beaten"] = True
t = town("REALGAM_TOWER", "PYRITE_TOWN")
_birch = [p for p in _TMJ["REALGAM_TOWER"]["rooms"]["colosseum"]["people"] if p == "GYM LEADER BIRCH"]
story.story_flags[_mg.done_flag("REALGAM_TOWER")] = True
_og.event(t, {"world": "orre_gym", "gym": "gym_birch"}, [], lambda l: None)
_bs = getattr(g.current_state, "battle_state", None) or getattr(g.current_state, "next_state", None)
check(len(_birch) == 1 and type(g.current_state).__name__ == "TrainerIntroState" and getattr(_bs, "badge_reward", None) == "REALGAM",
      f"S3: Birch in Realgam's Colosseum in the sky after Greevil; his battle gives the Realgam Badge ({len(_birch)})")
for _f in ("orre_part2", "xd_gorigan_beaten", "xd_greevil_beaten", _mg.done_flag("XD_CIPHER_KEY_LAIR"), _mg.done_flag("REALGAM_TOWER")):
    story.story_flags.pop(_f, None)
story.badges["ORRE"] = _saved_badges

g.walk_towns = False
print(f"##### {fails} failures")
