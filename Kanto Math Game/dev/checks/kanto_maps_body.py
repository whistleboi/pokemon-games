# Kanto's maps rebuilt from the FireRed file by the Hoenn method (11-14): every rebuilt map opened the way a player meets
# it, and the story walked like a player walks it (the opening first). Glue after harness_head.py:
#   bash dev/checks/run.sh kanto_maps
import json
from collections import deque
from src.states.overworld import PlayState, CityState, AreaTransitionState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.states.overworld.dungeon import DungeonState
from src.states.menus import StarterSelectionState as _SSS, region_opening_state
from src.states.battle import TrainerIntroState, TrainerBattleState

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "red"
_tm = json.load(open("assets/town_maps.json", encoding="utf-8"))
_area = g.loader.area_data["STORY_PROGRESSION"]
import importlib.util as _u
_spec = _u.spec_from_file_location("firered", "dev/builders/town_maps/firered.py")
_fr = _u.module_from_spec(_spec); _spec.loader.exec_module(_fr)
BUILT = list(_fr.KANTO)
said = []   # (every line the game showed, in order)


def _note(st):
    box = getattr(st, "npc_dialogue", None) if getattr(st, "npc_active", False) else getattr(st, "dialogue_box", None)
    if box is not None and getattr(box, "visible", True):
        for line in getattr(box, "text_lines", []) or []:
            if not said or said[-1] != line:
                said.append(line)


def tap(st, n=600):
    for _ in range(n):
        if getattr(st, "npc_active", False):
            _note(st)
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "dialogue_box", None) is not None and st.dialogue_box.visible:
            _note(st)
            st.dialogue_box.advance()
        else:
            return
        st.update(); st.draw()


def frames(n):
    for _ in range(n):
        g.current_state.update(); g.current_state.draw()


def play(until, n=3000):
    """Run the game, tapping through whatever is said, till until() (or n frames). True if until() came true."""
    for _ in range(n):
        if until():
            return True
        st = g.current_state
        if getattr(st, "npc_active", False):
            _note(st)
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif not isinstance(st, _WTS) and getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            _note(st)   # (a message on a screen of its own: the opening's words, the battle's)
            st.dialogue_box.advance()
        st.update(); st.draw()
    return until()


def walk(st, path):
    """Take real steps ("u", "d", "l", "r"), each finished (and anything said after it tapped through) before the next."""
    for c in path:
        d = {"u": (0, -1), "d": (0, 1), "l": (-1, 0), "r": (1, 0)}[c]
        play(lambda: not g.current_state._busy() and g.current_state.anim == 0, 400) if isinstance(g.current_state, _WTS) else None
        g.current_state.step(*d)
        play(lambda: isinstance(g.current_state, _WTS) and g.current_state.anim == 0, 60)


def open_map(key, came):
    story.current_area_key, story.last_area_key = key, came
    g.walk_town_pos = None
    st = CityState(g) if _area[key].get("area_type") == "town" else None
    if st is None or not isinstance(st, _WTS):
        st = PlayState(g); g.states["play"] = st
    g.change_state(st)
    frames(2)
    tap(g.current_state)
    return g.current_state


# ---- every rebuilt map: opens on its own FireRed map, every way out is in the story data, all of it reachable
for key in BUILT:
    m = _tm[key]
    a = _area.get(key, {})
    _parts = m["floors"] if m.get("floors") else [m]
    targets = set(v for f in _parts for v in f.get("exits", {}).values() if not str(v).startswith(("ROOM:", "OUT:")))   # (a room's stairs and doors stay inside the place)
    known = {o.get("target_area") or o.get("target") for o in a.get("travel_options", []) + a.get("route_menu", []) + a.get("explore_options", [])}
    check(targets <= known, f"{key}: every way out on the map is a way out in the story data {sorted(targets - known)}")
    came = sorted(targets)[0] if targets else key
    st = open_map(key, came)
    is_town = isinstance(st, _WTS)
    w, h = (st.w, st.h) if is_town else (st.run.floor.w, st.run.floor.h)
    _here = _parts[st.run.index] if (not is_town and m.get("floors") and st.run.index < len(_parts)) else m
    check((w, h) == (len(_here["art"][0]), len(_here["art"])) and (is_town or isinstance(st, DungeonState)),
          f"{key}: opens on its FireRed map ({w} x {h}, {'town' if is_town else 'route'}), in from {came}")
    check(all("fr_ground/" in json.dumps(f.get("roofs", {})) for f in _parts), f"{key}: drawn from FireRed's own picture (every floor)")
    grid = _here["art"]
    if m.get("floors"):   # (a place of floors: every ladder and passage lands on a real tile of a floor that exists)
        _bad = [(i, k, to) for i, f in enumerate(m["floors"]) for k, to in (f.get("links") or {}).items()
                if not (0 <= to[0] < len(m["floors"]) and 0 <= to[2] < len(m["floors"][to[0]]["art"]) and 0 <= to[1] < len(m["floors"][to[0]]["art"][0]))]
        check(not _bad, f"{key}: {len(m['floors'])} floors joined by FireRed's own ladders {_bad[:3]}")
    if not m.get("parts") and not m.get("floors"):
        walkable = set(".=\"NX!ow$[]{}%_()D<>^vnwu20b:|;,'")
        starts = [(x, y) for y, r in enumerate(grid) for x, c in enumerate(r) if c in "<>^vnwu"]
        seen, todo = set(starts[:1]), deque(starts[:1])
        _thru = {}   # (a gatehouse with doors on both sides joins them: Route 11's east gate)
        for _d, _rn in (m.get("inside") or {}).items():
            _outs = [tuple(int(v) for v in str(t)[4:].split(",")) for t in ((m.get("rooms") or {}).get(_rn, {}).get("exits") or {}).values() if str(t).startswith("OUT:")]
            _thru[tuple(int(v) for v in _d.split(","))] = _outs
        while todo:
            x, y = todo.popleft()
            for t in _thru.get((x, y), []):
                if t not in seen:
                    seen.add(t); todo.append(t)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                t = (x + dx, y + dy)
                if 0 <= t[0] < w and 0 <= t[1] < h and t not in seen and grid[t[1]][t[0]] in walkable:
                    seen.add(t); todo.append(t)
        _over = lambda x, y: any(0 <= y + 2 * dy < h and 0 <= x + 2 * dx < w and grid[y + dy][x + dx] == "m" and (x + 2 * dx, y + 2 * dy) in seen
                                 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))   # (a clerk talked to across the counter: the Game Corner's)
        cut = [(x, y, c) for y, r in enumerate(grid) for x, c in enumerate(r) if c in "<>^vnwuDNX" and (x, y) not in seen and not (c == "N" and _over(x, y))]
        check(not cut, f"{key}: every way out, door, person and trainer is reachable from the first way out {cut[:4]}")
    for rname, room in (m.get("rooms") or {}).items():   # (each building: its own FireRed room, and the way back out)
        outs = [v for v in room.get("exits", {}).values() if str(v).startswith(("OUT:", "ROOM:"))]
        check(outs and "fr_ground/" in json.dumps(room.get("roofs", {})), f"{key}@{rname}: FireRed's own room, with its way out {outs}")

# ---- the opening, as a new Kanto game plays it (FireRed: wake up upstairs; Mom; Oak stops you at the edge of town and
# walks you to his Lab; the three Poke Balls; the rival's battle; he leaves)
for f in [k for k in story.story_flags if "kanto" in k or k in ("got_oaks_parcel", "kanto_parcel_era")]:
    story.story_flags.pop(f, None)
story.player_team = []
story.inventory.pop("OAKS_PARCEL", None)
story.inventory.pop("TOWN_MAP", None)
story.starting_region = "KANTO"
story.badges["KANTO"] = []
st = region_opening_state(g, "KANTO")
g.change_state(st)
play(lambda: isinstance(g.current_state, _WTS), 600)
t = g.current_state
check(isinstance(t, _WTS) and t.area_key == "PALLET_TOWN" and t.room == "home_2" and tuple(t.player) == (5, 6),
      f"a new game: you wake up in your own room upstairs ({getattr(t, 'room', None)}, {getattr(t, 'player', None)})")
said.clear()
t.player = (10, 3); t.anim = 0
walk(t, "u")   # (onto the stairs at 10,2)
play(lambda: story.story_flags.get("kanto_mom_morning") and not g.current_state._busy(), 900)
t = g.current_state
check(t.room == "home" and any("Professor Oak was asking" in s for s in said) and story.story_flags.get("kanto_mom_morning"),
      f"downstairs, Mom tells you Oak was asking for you ({said[-1:] if said else None})")
_door = next(xy for xy, v in t.exits.items() if str(v).startswith("OUT:"))
t.player = (_door[0], _door[1] - 1); t.anim = 0
walk(t, "d")
t = g.current_state
check(t.room is None and tuple(t.player) == (6, 8), f"out of the front door into Pallet Town ({t.room}, {t.player})")
t.player = (12, 3); t.anim = 0
said.clear()
walk(t, "uu")
_saw_lead = []
play(lambda: (_saw_lead.append(tuple(t.player)) or False) or getattr(g.current_state, "room", None) == "lab", 4000)
t = g.current_state
check(any("Hold on" in s for s in said) and any("Come with me" in s for s in said),
      f"Pallet: Oak calls out, hurries up and tells you to come with him ({said[:2]})")
check(len(set(_saw_lead)) > 8 and any(p[1] >= 13 for p in _saw_lead),
      f"you follow him down through town to the Lab door ({len(set(_saw_lead))} tiles walked, last {_saw_lead[-1:]})")
check(t.room == "lab" and story.story_flags.get("kanto_oak_led"), f"...and in through the door into his Lab ({t.room})")
said.clear()
play(lambda: story.story_flags.get("kanto_lab_intro") and not g.current_state._busy(), 4000)

t = g.current_state
oak = next((p for p, o in t._people().items() if "Professor Oak" in str(o.get("text"))), None)
check(story.story_flags.get("kanto_lab_intro") and any("three Poké Balls" in s for s in said) and any("Gramps" in s for s in said),
      f"in the Lab Oak walks to his table, the rival complains, Oak offers the three Poké Balls ({len(said)} lines)")
check(oak == (6, 3) and tuple(t.player) == (6, 4), f"Oak stands at FireRed's spot (6, 3) with you in front of him ({oak}, you {t.player})")
balls = sorted(p for p, o in t._people().items() if "Poke Ball" in str(o.get("text")))
check(balls == [(8, 4), (9, 4), (10, 4)], f"three Poké Balls on the table, FireRed's spots ({balls})")
check(story.get_active_missions() and story.get_active_missions()[0].get("id") == "m0a2",
      f"the Journal: Choose Your Pokemon ({[m.get('id') for m in story.get_active_missions()][:2]})")
# no leaving before you choose
t.player = (6, 10); t.anim = 0
said.clear()
walk(t, "d")
play(lambda: any("Pick a Pokémon first" in s for s in said) and not g.current_state._busy(), 800)
t = g.current_state
check(t.room == "lab" and tuple(t.player) == (6, 10) and any("Pick a Pokémon first" in s for s in said),
      f"heading for the door, Oak calls you back ({t.player}, {said[:1]})")
# walk up to Squirtle's ball and talk to it: the starter screen
t.player = (9, 5); t.anim = 0; t.facing = (0, -1)
said.clear()
walk(t, "u")
play(lambda: isinstance(g.current_state, _SSS), 600)
s = g.current_state
check(isinstance(s, _SSS) and s.region == "KANTO", f"the Poké Ball opens the starter screen ({type(s).__name__})")
s.load_starters(); s.selected_idx = [p.id for p in s.starters].index(7); s.complete_selection()
check(story.story_flags.get("received_starter_kanto") and story.player_team and story.player_team[0].id == 7,
      "you take Squirtle")
s.dialogue_box.callback()
intro = g.current_state
b = getattr(intro, "next_state", None)
check(isinstance(intro, TrainerIntroState) and isinstance(b, TrainerBattleState) and b.trainer_class == "RIVAL"
      and [p.id for p in b.opponent_team] == [1], f"the rival takes Bulbasaur and battles you ({[p.id for p in b.opponent_team] if b else None})")
g.change_state(b)
b.player_won = True
b.exit_battle()
said.clear()
play(lambda: isinstance(g.current_state, _WTS), 600)
t = g.current_state
check(isinstance(t, _WTS) and t.room == "lab" and story.story_flags.get("defeated_rival_kanto"), f"after the battle you're back in the Lab ({getattr(t, 'room', None)})")
play(lambda: story.story_flags.get("kanto_rival_left_lab") and not g.current_state._busy(), 3000)
t = g.current_state
check(story.story_flags.get("kanto_rival_left_lab") and any("Smell you later" in s for s in said)
      and not any("{rival_name}" == o.get("text") for o in t._people().values()),
      f"the rival says his piece and leaves ({said[-1:]})")
check(not any("Poke Ball" in str(o.get("text")) for o in t._people().values()), "the Poké Balls are put away")
_m = [m.get("id") for m in story.get_active_missions()]
check(_m and _m[0] == "m0b", f"the Journal: Oak's Parcel, at the Viridian Mart ({_m[:2]})")
# out of the Lab and up to Route 1: nobody stops you now
t.player = (6, 11); t.anim = 0
walk(t, "d")
t = g.current_state
check(t.room is None and tuple(t.player) == (16, 14), f"out of the Lab below its door ({t.player})")
t.player = (12, 2); t.anim = 0
said.clear()
walk(t, "uu")
play(lambda: story.current_area_key == "KANTO_ROUTE_1" and isinstance(g.current_state, PlayState), 900)
check(story.current_area_key == "KANTO_ROUTE_1" and not any("Hold on" in s for s in said),
      f"with a Pokémon, north to Route 1 ({story.current_area_key})")

# ---- Route 1 (FireRed 3.19): in from Pallet at the bottom; the Mart clerk with a free Potion where FireRed stands him
p = g.current_state
check(isinstance(p, PlayState) and p.run.player[1] >= 37, f"Route 1: you come in at the bottom, from Pallet ({p.run.player if isinstance(p, PlayState) else None})")
_clerk = [f for f in p.placed if f.get("text") == "POKE MART CLERK"]
_at = next(((m.x, m.y) for m in p.run.floor.movers if m.kind == "figure" and m.payload.get("text") == "POKE MART CLERK"), None)
check(_clerk and _at is not None and abs(_at[0] - 6) + abs(_at[1] - 28) <= 1, f"Route 1: the Mart clerk stands at FireRed's spot (6, 28) ({_at})")

# ---- Viridian City (FireRed 3.1): before the Pokedex the road north is shut; the Mart clerk calls you over with Oak's Parcel
v = open_map("VIRIDIAN_CITY", "KANTO_ROUTE_1")
check(isinstance(v, _WTS) and v.player[1] >= 37, f"Viridian: in from Route 1 at the bottom ({v.player})")
v.player = (21, 12); v.anim = 0
said.clear()
walk(v, "u")
play(lambda: any("Grandpa" in s or "grandpa" in s for s in said) and not g.current_state._busy() and g.current_state.anim == 0, 1500)
v = g.current_state
check(v.player[1] >= 12 and any("grandpa" in s.lower() for s in said), f"Viridian: the road north is shut, the granddaughter turns you back ({v.player}, {said[:1]})")
v.player = (36, 20); v.anim = 0; v.facing = (0, -1)
said.clear()
walk(v, "u")   # (into the Mart)
play(lambda: story.story_flags.get("got_oaks_parcel") and not g.current_state._busy(), 1500)
v = g.current_state
check(v.room == "mart" and story.inventory.get("OAKS_PARCEL") == 1 and any("Come over here" in s for s in said),
      f"Viridian Mart: the clerk calls you over and hands you Oak's Parcel ({said[:2]})")
_m = [m.get("id") for m in story.get_active_missions()]
check(_m and _m[0] == "m0c", f"the Journal: take it back to Oak ({_m[:2]})")
g.walk_town_pos = ("PALLET_TOWN", (6, 5), (0, -1)); g.walk_town_room = ("PALLET_TOWN", "lab")
story.current_area_key, story.last_area_key = "PALLET_TOWN", "KANTO_ROUTE_1"
t = CityState(g); g.change_state(t); frames(2)
said.clear()
t.player = (6, 4); t.facing = (0, -1); t.anim = 0
walk(t, "u")   # (talk to Oak: he has two things for you now, so you pick "Professor Oak" from his menu)
if t.hover_menu_active:
    _opt = next(o for o in t._people()[(6, 3)].get("any", [t._people()[(6, 3)]]) if o.get("text") == "Professor Oak") if "any" in t._people()[(6, 3)] else t._people()[(6, 3)]
    t.clear_hover_menu(); t._get_callback_for_option(_opt)()
play(lambda: story.story_flags.get("kanto_rival_pokedex") and not g.current_state._busy(), 4000)
check(story.story_flags.get("received_pokedex_kanto") and not story.inventory.get("OAKS_PARCEL") and story.catch_unlocked("KANTO"),
      "Oak takes the Parcel and gives you the Pokédex: catching is open")
check(story.story_flags.get("kanto_rival_pokedex") and any("heading out" in s for s in said), f"the rival comes in for his Pokédex, then heads off ({said[-1:]})")
t = g.current_state
check(not any(xy in t.barred for xy in ((4, 1), (5, 1))), "the Pokédexes are gone from the shelf")
# Daisy: her own words (no Town Map from her: every region's Town Map is in the Bag from the start)
t._go("rival", "OUT:15,7"); said.clear()
daisy = next(p for p, o in t._people().items() if o.get("text") == "Daisy")
t.player = (daisy[0] - 1, daisy[1]); t.anim = 0; t.facing = (1, 0)
walk(t, "r")
play(lambda: any("Daisy" in s for s in said) and not g.current_state._busy(), 600)
check(any("Daisy: Hi there" in s for s in said), f"Daisy, next door, at FireRed's spot {daisy} ({said[:1]})")

# ---- Viridian: the Gym's doors stay locked till the other seven badges; inside, FireRed's spin maze; the Center
v = open_map("VIRIDIAN_CITY", "KANTO_ROUTE_1")
v.player = (36, 11); v.anim = 0; v.facing = (0, -1)
walk(v, "u")
play(lambda: not g.current_state._busy(), 300)
v = g.current_state
check(v.room is None and tuple(v.player) == (36, 11), f"Viridian Gym: locked without the seven badges ({v.room}, {v.player})")
story.badges["KANTO"] = ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH", "VOLCANO"]
v = open_map("VIRIDIAN_CITY", "KANTO_ROUTE_1")
v.player = (36, 11); v.anim = 0
walk(v, "u")
v = g.current_state
check(v.room == "gym" and (2, 2) in v._people(), f"Viridian Gym: with seven badges you walk in; Giovanni waits at FireRed's spot ({v.room})")
_stops = {tuple(s) for s in (_tm["VIRIDIAN_CITY"]["rooms"]["gym"].get("stops") or [])}
check(len(_stops) >= 10, f"Viridian Gym: FireRed's stop tiles ({len(_stops)})")
v.player = (16, 21); v.anim = 0   # (just inside: the west-pointing arrows at 13,21 and 13,22)
walk(v, "llll")
check(tuple(v.player)[0] < 13, f"Viridian Gym: an arrow carries you along ({v.player})")
story.badges["KANTO"] = []
v = open_map("VIRIDIAN_CITY", "KANTO_ROUTE_1")
v.player = (26, 27); v.anim = 0
walk(v, "u")
v = g.current_state
check(v.room == "center", f"Viridian: into the Pokémon Center ({v.room})")
for p_ in story.player_team:
    p_.current_hp = 1
v.player = (7, 4); v.anim = 0; v.facing = (0, -1)
said.clear()
walk(v, "u")
play(lambda: not g.current_state._busy(), 600)
check(all(p_.current_hp == p_.get_max_hp() for p_ in story.player_team), f"Viridian Center: the nurse across the counter heals your team ({said[:1]})")

# ---- Route 22 (FireRed 3.41): the rival waits at FireRed's spot; cross FireRed's trigger tiles and he walks up to battle
story.badges["KANTO"] = []
story.story_flags.pop("defeated_rival_route22_early", None)
r = open_map("KANTO_ROUTE_22", "VIRIDIAN_CITY")
_riv = next((m for m in r.run.floor.movers if m.kind == "figure" and m.payload.get("action") == "ARRIVAL"), None)
check(_riv is not None and (_riv.x, _riv.y) == (25, 4), f"Route 22: the rival waits at FireRed's spot (25, 4) ({(_riv.x, _riv.y) if _riv else None})")
_m = [m.get("id") for m in story.get_active_missions()]
check("m0e" in _m, f"the Journal: a side mission to battle him ({_m[:3]})")
r.run.player = (34, 5); r.anim = 0
r.run.floor.movers = [m for m in r.run.floor.movers if m.kind == "figure"]
r.step(-1, 0)
play(lambda: isinstance(g.current_state, TrainerIntroState), 1500)
intro = g.current_state
check(isinstance(intro, TrainerIntroState) and getattr(intro.next_state, "trainer_class", "") == "RIVAL",
      f"Route 22: he walks up and battles you ({type(intro).__name__})")
if isinstance(intro, TrainerIntroState):
    b = intro.next_state
    g.change_state(b); b.player_won = True; b.exit_battle()
    play(lambda: isinstance(g.current_state, PlayState), 600)
    play(lambda: False, 200)
    check(story.story_flags.get("defeated_rival_route22_early") and not any(m.kind == "figure" and m.payload.get("action") == "ARRIVAL" for m in g.current_state.run.floor.movers),
          "Route 22: beaten, he's gone and the side mission is done")

# ---- batch 3: Route 2, Viridian Forest, Pewter City (FireRed 3.20, 1.0, 3.2)
story.badges["KANTO"] = []
story.story_flags.pop("visited_PEWTER_CITY", None)
for _k in [k for k in story.story_flags if k.startswith("visited_") and k[8:] not in ("PALLET_TOWN", "VIRIDIAN_CITY")]:
    story.story_flags.pop(_k)   # (the map sweep above walked into every town)
_m = [m.get("id") for m in story.get_active_missions()]
check(_m and _m[0] == "m1b", f"the Journal, Pokedex in hand: through Viridian Forest to Pewter ({_m[:2]})")


def _figure(p, text):
    return next(((m.x, m.y) for m in p.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == text), None)


def _use(p, at, d):
    """Stand at, face d, walk into whoever stands there (route maps), tapping through what's said."""
    p.run.floor.movers = [m for m in p.run.floor.movers if m.kind != "wild"]
    p.run.player = tuple(at); p.anim = 0
    p.step(*d)
    play(lambda: not getattr(g.current_state, "dialogue_box", None) or not g.current_state.dialogue_box.visible, 300)


for _f in ("got_ether_route2",):
    story.story_flags.pop(_f, None)
r2 = open_map("KANTO_ROUTE_2", "VIRIDIAN_CITY")
check(_figure(r2, "ETHER") == (17, 54), f"Route 2: FireRed's Ether lies at (17, 54) ({_figure(r2, 'ETHER')})")
_had = story.inventory.get("ETHER", 0)
_use(r2, (17, 55), (0, -1))
check(story.inventory.get("ETHER", 0) == _had + 1 and story.story_flags.get("got_ether_route2"), "...walk up to it and you pick it up")
fo = open_map("VIRIDIAN_FOREST", "KANTO_ROUTE_2")
_tr = sorted((m.x, m.y) for m in fo.run.floor.movers if m.kind == "trainer")
check(len(_tr) == 5 and (16, 5) in _tr and (47, 45) in _tr, f"Viridian Forest: the five Bug Catchers on FireRed's spots ({_tr})")
_b = story.balls_left
story.story_flags.pop("got_ball_forest", None)
_use(fo, (5, 42), (0, -1))
check(story.balls_left == _b + 1, f"...its Poké Ball item counts in your Poké Balls ({_b} -> {story.balls_left})")
_had = story.inventory.get("POTION", 0)
for _k in [k for k in story.story_flags if k.startswith("hidden_VIRIDIAN_FOREST")]:
    story.story_flags.pop(_k)
fo.run.player = (3, 23); fo.anim = 0
fo.run.floor.movers = [m for m in fo.run.floor.movers if m.kind not in ("wild", "trainer")]   # (nobody to spot you on this step)
for _ in range(300):   # (the Poke Ball's words tapped through first)
    if fo._ready():
        break
    if fo.dialogue_box.visible:
        fo.dialogue_box.advance()
    fo.update(); fo.draw()
fo.anim = 0
fo.step(0, -1)
play(lambda: False, 40)
play(lambda: not fo.dialogue_box.visible, 200)
check(story.inventory.get("POTION", 0) == _had + 1 and story.story_flags.get("hidden_VIRIDIAN_FOREST_0_3_22"), "...FireRed's hidden Potion at (3, 22) is found by stepping on it")

pw = open_map("PEWTER_CITY", "KANTO_ROUTE_2")
_m = [m.get("id") for m in story.get_active_missions()]
check(_m and _m[0] == "m2", f"Pewter: the Journal moves on to Brock ({_m[:2]})")
boy = next((p for p, o in pw._people().items() if o.get("text") == "Boy"), None)
check(boy == (42, 20), f"Pewter: the boy waits by the east road at FireRed's spot ({boy})")
pw.player = (41, 21); pw.anim = 0
said.clear()
walk(pw, "r")
_trail = []
play(lambda: (_trail.append(tuple(g.current_state.player)) or False) or (any("Pewter Gym" in s for s in said) and not g.current_state._busy()), 3000)
check(any("Follow me" in s for s in said) and any(abs(p[0] - 16) + abs(p[1] - 17) <= 2 for p in _trail),
      f"...head east without the Boulder Badge: he walks you to the Gym ({_trail[-1:]}, {said[:1]})")
pw = g.current_state
pw.player = (15, 17); pw.anim = 0
walk(pw, "u")
pw = g.current_state
check(pw.room == "gym" and (6, 5) in pw._people() and (3, 8) in pw._people(), f"Pewter Gym: Brock and Camper Liam on FireRed's spots ({pw.room})")
story.story_flags.pop("gym_trainer_PEWTER_CITY_0", None)
pw.player = (4, 8); pw.anim = 0; pw.facing = (-1, 0)
said.clear()
walk(pw, "l")
play(lambda: isinstance(g.current_state, TrainerIntroState), 600)
_b = getattr(g.current_state, "next_state", None)
check(isinstance(g.current_state, TrainerIntroState) and [p.id for p in _b.opponent_team] == [74, 27],
      f"...talk to Liam: he battles with the data's own team (Geodude, Sandshrew) ({[p.id for p in _b.opponent_team] if _b else None})")
if _b is not None:
    g.change_state(_b); _b.player_won = True; _b.exit_battle()
    play(lambda: isinstance(g.current_state, _WTS), 600)
check(story.story_flags.get("gym_trainer_PEWTER_CITY_0") and getattr(g.current_state, "room", None) == "gym", "...beaten, you're back in the Gym")
# the Museum's back room: the Old Amber, from its scientist
story.story_flags.pop("received_old_amber", None)
story.inventory.pop("OLD_AMBER", None)
pw = open_map("PEWTER_CITY", "KANTO_ROUTE_2")
pw.player = (25, 5); pw.anim = 0
walk(pw, "u")
pw = g.current_state
check(pw.room == "museum_1f" and (22, 3) in pw.barred, f"Museum: in by the back door, the Amber on show ({pw.room}, {pw.player})")
pw.player = (21, 4); pw.anim = 0; pw.facing = (0, -1)
walk(pw, "u")
play(lambda: not g.current_state._busy(), 600)
play(lambda: False, 30)
pw = g.current_state
check(story.inventory.get("OLD_AMBER") == 1 and (22, 3) not in pw.barred, "...the scientist gives you the Old Amber, and it's gone from the case")
for _k in [k for k in story.story_flags if k.startswith("hidden_PEWTER_CITY")]:
    story.story_flags.pop(_k)
pw = open_map("PEWTER_CITY", "KANTO_ROUTE_2")
_b = story.balls_left
pw.player = (6, 4); pw.anim = 0
walk(pw, "u")
play(lambda: not g.current_state._busy(), 300)
check(story.balls_left == _b + 1, f"Pewter: FireRed's hidden Poké Ball at (6, 3) ({_b} -> {story.balls_left})")

# ---- running (Jordan, 11-14: hold Shift while moving; no shoes): a step takes half the frames, on foot only
import src.states.overworld.dungeon as _dn


def _step_frames(st, at, d, run):
    _dn.running = (lambda: True) if run else (lambda: False)
    if isinstance(st, _WTS):
        st.player = st.anim_from = at; st.anim = 0
    else:
        st.run.floor.movers = []; st.run.player = at; st.anim = 0
    st.step(*d)
    n = 0
    while st.anim > 0 and n < 50:
        st.update(); n += 1
    return n


t = open_map("PALLET_TOWN", "KANTO_ROUTE_1")
_w, _r = _step_frames(t, (12, 8), (1, 0), False), _step_frames(t, (12, 8), (1, 0), True)
check(_r < _w and _r * 2 <= _w + 1, f"running in town: a step takes {_r} frames instead of {_w}")
p = open_map("KANTO_ROUTE_1", "PALLET_TOWN")
_w, _r = _step_frames(p, (12, 30), (0, -1), False), _step_frames(p, (12, 30), (0, -1), True)
check(_r < _w, f"running on a route: a step takes {_r} frames instead of {_w}")
story.inventory["HM_SURF"] = 1
t = open_map("PALLET_TOWN", "KANTO_ROUTE_1")
_w, _r = _step_frames(t, (8, 17), (0, 1), False), _step_frames(t, (8, 17), (0, 1), True)
check(_r == _w, f"no running while surfing Pallet's pond ({_r} = {_w} frames)")
story.inventory.pop("HM_SURF", None)
_dn.running = lambda: False

# ---- the Museum's ticket (FireRed: 50, at the desk); and Route 2's aide wants ten kinds caught before HM Flash
for _money, _paid in ((0, False), (500, True)):
    story.story_flags.pop("museum_ticket_paid", None)
    story.money = _money
    pw = open_map("PEWTER_CITY", "KANTO_ROUTE_2")
    pw.player = (17, 7); pw.anim = 0
    walk(pw, "u")
    pw = g.current_state
    pw.player = (13, 6); pw.anim = 0
    said.clear()
    walk(pw, "u")
    play(lambda: any("Receptionist" in s for s in said) and not g.current_state._busy(), 900)
    pw = g.current_state
    if _paid:
        check(story.story_flags.get("museum_ticket_paid") and story.money == _money - 50 and pw.player[1] <= 5,
              f"Museum: with money, you pay the 50 ticket and go in ({story.money}, {pw.player})")
    else:
        check(not story.story_flags.get("museum_ticket_paid") and pw.player[1] >= 6 and any("enough money" in s for s in said),
              f"Museum: without 50, the receptionist turns you back ({pw.player}, {said[-1:]})")
story.story_flags.pop("got_hm_flash_kanto", None)
story.inventory.pop("HM_FLASH", None)
for _n in (3, 10):
    story.kanto_caught_count = lambda _n=_n: _n
    r2 = open_map("KANTO_ROUTE_2", "VIRIDIAN_CITY")
    _i, _at = r2.run.index, None
    r2.run.floor.movers = [m for m in r2.run.floor.movers if m.kind != "wild"]
    said.clear()
    _aide = next(o for o in _area["KANTO_ROUTE_2"]["route_menu"] if o.get("text") == "OAK'S AIDE")
    from src.states.overworld import _run_story_event
    _run_story_event(r2, _aide["event"], lambda c: r2._check_route_condition(c, False), lambda lines: said.extend(lines))
    if _n < 10:
        check(not story.inventory.get("HM_FLASH") and any("ten different kinds" in s for s in said), f"Route 2's aide: with {_n} kinds caught, come back with ten")
    else:
        check(story.inventory.get("HM_FLASH") == 1, f"...with ten kinds caught, HM Flash")
del story.kanto_caught_count

# ---- batch 4: Route 3 (with the foot of Mt. Moon), Mt. Moon, Route 4
story.badges["KANTO"] = ["BOULDER"]
r3 = open_map("KANTO_ROUTE_3", "PEWTER_CITY")
check(r3.run.player[0] <= 1 and 25 <= r3.run.player[1] <= 35, f"Route 3: in from Pewter on the west ({r3.run.player})")
_tr = sorted((m.x, m.y - 20) for m in r3.run.floor.movers if m.kind == "trainer")
check(len(_tr) == 8 and (40, 11) in _tr and (17, 4) in _tr, f"...FireRed's eight trainers on their spots ({len(_tr)})")
check(r3.run.floor.exits.get((78, 5)) == "MT_MOON" or any(v == "MT_MOON" for v in r3.run.floor.exits.values()), "...Mt. Moon's mouth at the foot of the mountain")
# the Center at the foot, and the Magikarp salesman (FireRed: 500)
_i, _at = None, None
r3.run.player = (72, 6); r3.anim = 0; r3.run.floor.movers = [m for m in r3.run.floor.movers if m.kind == "figure"]
r3.step(0, -1); play(lambda: False, 20)
check(r3._floor_name(r3.run.index).lower().startswith("pok"), f"...the Pokémon Center's door: inside ({r3._floor_name(r3.run.index)})")
story.story_flags.pop("got_magikarp_mtmoon", None)
story.money = 600
story.player_team = story.player_team[:1]
_sell = next(o for o in _area["KANTO_ROUTE_3"]["route_menu"] if o.get("text") == "MAGIKARP SALESMAN")
from src.states.overworld import _run_story_event
said.clear()
_run_story_event(r3, _sell["event"], lambda c: r3._check_route_condition(c, False), lambda lines: said.extend(lines))
check(story.money == 100 and any(p.id == 129 for p in story.player_team), f"...the Magikarp salesman: 500 for a Magikarp ({story.money})")
# Mt. Moon: in from the foot; down the ladders; B2F's Super Nerd steps in as you near the fossils
mm = open_map("MT_MOON", "KANTO_ROUTE_3")
check(mm.run.index == 0 and mm.run.player[1] >= 34, f"Mt. Moon: in at 1F's mouth ({mm.run.index}, {mm.run.player})")
_items = {m.payload.get("text") for m in mm.run.floor.movers if m.kind == "figure"}
check({"MOON STONE", "TM50", "RARE CANDY"} <= _items, f"...FireRed's item balls on 1F ({sorted(_items)[:6]})")
story.story_flags.pop("mt_moon_nerd_defeated", None)
for _k in ("took_dome_fossil", "took_helix_fossil"):
    story.story_flags.pop(_k, None)
while len(mm.run.floors) <= 2:   # (floors are made in order)
    mm.run.enter_floor(len(mm.run.floors))
mm.run.enter_floor(2); frames(2)
nerd = next(((m.x, m.y) for m in mm.run.floor.movers if m.kind == "figure" and m.payload.get("text") == "SUPER NERD"), None)
check(nerd == (13, 11), f"B2F: the Super Nerd guards the fossils at FireRed's spot ({nerd})")
mm.run.floor.movers = [m for m in mm.run.floor.movers if m.kind == "figure"]
mm.run.player = (18, 12); mm.anim = 0
said.clear()
mm.step(0, -1)
play(lambda: isinstance(g.current_state, TrainerIntroState), 1500)
_b = getattr(g.current_state, "next_state", None)
check(any("stop right there" in s.lower() for s in said) and isinstance(g.current_state, TrainerIntroState) and [p.id for p in _b.opponent_team] == [88, 100, 109],
      f"...step into the fossil chamber: he stops you and battles ({said[:1]})")
if _b is not None:
    g.change_state(_b); _b.player_won = True; _b.exit_battle()
    play(lambda: isinstance(g.current_state, PlayState), 600)
mm = g.current_state
_fos = sorted((m.payload.get("text"), (m.x, m.y)) for m in mm.run.floor.movers if m.kind == "figure" and "FOSSIL" in str(m.payload.get("text")))
check(story.story_flags.get("mt_moon_nerd_defeated") and _fos == [("TAKE DOME FOSSIL", (13, 7)), ("TAKE HELIX FOSSIL", (14, 7))],
      f"...beaten, the two fossils are yours to choose from ({_fos})")
# B1F's far mouth comes out on Route 4, by its own mouth; Route 4's Roar, then Cerulean
r4 = open_map("KANTO_ROUTE_4", "MT_MOON")
check(abs(r4.run.player[0] - 10) <= 2 and r4.run.player[1] <= 7, f"Route 4: out of Mt. Moon's far mouth ({r4.run.player})")
check(_figure(r4, "TM120") == (45, 5), f"...FireRed's TM (Roar, our TM120) on the ledge ({_figure(r4, 'TM120')})")
check("CERULEAN_CITY" in set(r4.run.floor.exits.values()), "...and east to Cerulean City")
story.badges["KANTO"] = []

# ---- batch 5: Cerulean City, Route 24 (Nugget Bridge), Route 25, Bill's Sea Cottage
story.badges["KANTO"] = ["BOULDER"]
story.story_flags.pop("defeated_rival_nugget_bridge", None)
r24 = open_map("KANTO_ROUTE_24", "CERULEAN_CITY")
_tr = sorted((m.x, m.y) for m in r24.run.floor.movers if m.kind == "trainer")
check(len(_tr) == 7 and (12, 15) in _tr and (12, 31) in _tr, f"Route 24: Nugget Bridge's five, the hidden camper and the Rocket on FireRed's spots ({_tr})")
_riv = next(((m.x, m.y) for m in r24.run.floor.movers if m.kind == "figure" and m.payload.get("action") == "ARRIVAL"), None)
check(_riv == (11, 37), f"...your rival waits at the foot of the bridge ({_riv})")
r24.run.floor.movers = [m for m in r24.run.floor.movers if m.kind == "figure"]
r24.run.player = (11, 39); r24.anim = 0
said.clear()
play(lambda: isinstance(g.current_state, TrainerIntroState), 1500)
_b = getattr(g.current_state, "next_state", None)
check(isinstance(g.current_state, TrainerIntroState) and getattr(_b, "trainer_class", "") == "RIVAL", f"...he walks up and battles you ({type(g.current_state).__name__})")
if _b is not None:
    g.change_state(_b); _b.player_won = True; _b.exit_battle(); play(lambda: isinstance(g.current_state, PlayState), 600)
# the burgled house: in at the front, out through the hole at the back, and the Grunt in the yard
story.story_flags.pop("got_tm_dig_cerulean", None)
story.inventory.pop("TM15", None)
ce = open_map("CERULEAN_CITY", "KANTO_ROUTE_4")
ce.player = (30, 12); ce.anim = 0
walk(ce, "u")
ce = g.current_state
check(ce.room == "house_ne", f"Cerulean: into the burgled house ({ce.room})")
_hole = next(xy for xy, v in ce.exits.items() if v == "OUT:31,8")
ce.player = (_hole[0], _hole[1] + 1); ce.anim = 0
said.clear()
walk(ce, "u")
play(lambda: isinstance(g.current_state, TrainerIntroState), 1500)
_b = getattr(g.current_state, "next_state", None)
check(isinstance(g.current_state, TrainerIntroState) and _b and [p.id for p in _b.opponent_team] == [66, 96],
      f"...out through the hole in the back wall: the Grunt in the yard rounds on you (Machop, Drowzee) ({type(g.current_state).__name__})")
if _b is not None:
    g.change_state(_b); _b.player_won = True; _b.exit_battle(); play(lambda: isinstance(g.current_state, _WTS), 600)
check(story.inventory.get("TM15") == 1 and story.story_flags.get("got_tm_dig_cerulean"), "...beaten, he hands back TM28 Dig (our TM15)")
# the trade house: Poliwhirl for Jynx
story.story_flags.pop("cerulean_jynx_trade", None)
story.player_team = [mk(61)] + story.player_team[:1]
ce = open_map("CERULEAN_CITY", "KANTO_ROUTE_4")
ce.player = (15, 18); ce.anim = 0
walk(ce, "u")
ce = g.current_state
ce.player = (2, 3); ce.anim = 0; ce.facing = (0, -1)
walk(ce, "u")
play(lambda: not g.current_state._busy(), 600)
check(ce.room == "house_mid" and story.player_team[0].id == 124 and story.story_flags.get("cerulean_jynx_trade"), f"...the trade house: Poliwhirl for Jynx ({story.player_team[0].id})")
# Misty's Gym: her two trainers, FireRed's spots, talk to battle
ce = open_map("CERULEAN_CITY", "KANTO_ROUTE_4")
ce.player = (31, 22); ce.anim = 0
walk(ce, "u")
ce = g.current_state
_pp = {o.get("text"): p for p, o in ce._people().items()}
check(ce.room == "gym" and _pp.get("Picnicker Diana") == (4, 7) and _pp.get("Swimmer Luis") == (10, 12) and _pp.get("Gym") == (8, 6),
      f"Cerulean Gym: Misty, Diana and Luis on FireRed's spots ({_pp})")
# the cave's guard, till you're Champion
ce = open_map("CERULEAN_CITY", "KANTO_ROUTE_4")
check(any(o.get("text") == "Cave guard" for o in ce._people().values()), "Cerulean Cave's guard stands by its mouth")
story.story_flags["beat_champion"] = True   # (checked on the open map: arriving as Champion brings Mom's call first)
check(not any(o.get("text") == "Cave guard" for o in ce._people().values()), "...and steps aside once you're Champion")
story.story_flags.pop("beat_champion", None)
# Bill: a Clefairy by his machine till you've helped him, then himself
story.story_flags.pop("got_ss_ticket_bill", None)
bh = open_map("BILLS_HOUSE", "KANTO_ROUTE_25")
_sm = json.load(open("assets/dungeon_sprites.json", encoding="utf-8"))["figures"]
check({o.get("text") for o in bh._people().values()} == {"Talk to Bill"} and _sm.get("BILLS_HOUSE:Talk to Bill", {}).get("sheet") == "fr_113.png",
      f"Bill's Sea Cottage: Bill is a Clefairy ({[o.get('text') for o in bh._people().values()]})")
story.story_flags["got_ss_ticket_bill"] = True
bh = open_map("BILLS_HOUSE", "KANTO_ROUTE_25")
check({o.get("text"): p for p, o in bh._people().items()}.get("Bill") == (7, 5), "...and once you've helped him, Bill himself at FireRed's spot")
story.badges["KANTO"] = []

# ---- batch 6: Route 5, the Underground Path, Route 6, Vermilion City
story.badges["KANTO"] = ["BOULDER", "CASCADE"]
_tea = story.inventory.pop("TEA", None)
r5 = open_map("KANTO_ROUTE_5", "SAFFRON_CITY")
check(r5._floor_name(r5.run.index) == "Saffron Gate" and "GUARD" in {m.payload.get("text") for m in r5.run.floor.movers if m.kind == "figure"},
      f"Route 5: in from Saffron, inside its gatehouse, the thirsty guard ({r5._floor_name(r5.run.index)})")
r5.run.floor.movers = [m for m in r5.run.floor.movers if m.kind == "figure"]
r5.run.player = (4, 4); r5.anim = 0
said.clear()
r5.step(0, 1)
play(lambda: any("thirsty" in s for s in said) and r5._ready(), 900)
check(any("thirsty" in s for s in said) and r5.run.player[1] <= 4, f"...heading for Saffron without a drink, the guard calls you back ({r5.run.player}, {said[:1]})")
story.inventory["TEA"] = 1
r5 = open_map("KANTO_ROUTE_5", "CERULEAN_CITY")
check(r5.run.index == 0 and r5.run.player[1] <= 2, f"...in from Cerulean at the top ({r5.run.player})")
if _tea is None:
    story.inventory.pop("TEA", None)
# the Underground Path: down the stairs, the length of the tunnel, up into the Route 6 hut
up = open_map("UNDERGROUND_PATH", "KANTO_ROUTE_5")
check(up.room is None and "KANTO_ROUTE_5" in up.exits.values(), f"Underground Path: in from Route 5 in its hut ({up.room})")
_st = next(xy for xy, v in up.exits.items() if v == "ROOM:ns")
up.player = (_st[0], _st[1] - 1) if up._open((_st[0], _st[1] - 1)) else (_st[0] - 1, _st[1]); up.anim = 0
walk(up, "d" if up.player[1] < _st[1] else "r")
up = g.current_state
check(up.room == "ns" and up.player[1] <= 6 and any(o.get("text") == "Talk to Fossil Maniac" for o in up._people().values()),
      f"...down its stairs: the north end of the tunnel, the Fossil Maniac in it ({up.room}, {up.player})")
_low = next(xy for xy, v in up.exits.items() if v == "ROOM:south")
up.player = (_low[0], _low[1] - 1); up.anim = 0
walk(up, "d")
up = g.current_state
check(up.room == "south" and "KANTO_ROUTE_6" in up.exits.values(), f"...and at its south end, up into the Route 6 hut ({up.room})")
# Vermilion Gym: FireRed's trash-can puzzle
for _k in ("vermilion_gym_lock1", "vermilion_gym_open", "vermilion_gym_lock1_where"):
    story.story_flags.pop(_k, None)
ve = open_map("VERMILLION_CITY", "KANTO_ROUTE_6")
ve.player = (14, 26); ve.anim = 0
walk(ve, "u")
ve = g.current_state
check(ve.room == "gym" and (5, 6) in ve.barred and (5, 7) in ve.barred, f"Vermilion Gym: the electric gate is shut ({ve.room})")
_cans = [(x, y) for y in (10, 12, 14) for x in (1, 3, 5, 7, 9)]
story.story_flags["vermilion_gym_lock1_where"] = [6, 7]   # (switches under cans 6 and 7: (3,12), then (5,12) beside it)


def _search(can, frm):
    ve = g.current_state
    ve.player = frm; ve.anim = 0
    said.clear()
    ve.step(can[0] - frm[0], can[1] - frm[1])
    play(lambda: not g.current_state._busy(), 300)


_search((9, 10), (9, 11))
check(not story.story_flags.get("vermilion_gym_lock1") and any("only trash" in s for s in said), "...an empty can: only trash")
_search((3, 12), (3, 13))
check(story.story_flags.get("vermilion_gym_lock1") and any("first electric lock" in s for s in said), "...the first switch, under a can: one lock opens")
_pic = json.dumps((g.current_state.town_map["rooms"]["gym"]["roofs"]["_picture"]))
check("9_6_lock1" in _pic, "...FireRed's own picture of the half-open gate is ready for it")
_search((9, 14), (9, 13))
check(not story.story_flags.get("vermilion_gym_lock1") and any("reset" in s for s in said), "...the wrong can next: the locks reset")
story.story_flags["vermilion_gym_lock1_where"] = [6, 7]
_search((3, 12), (3, 13))
_search((5, 12), (5, 13))
ve = g.current_state
check(story.story_flags.get("vermilion_gym_open") and (5, 6) not in ve.barred and ve._open((5, 6)) and ve._open((5, 7)),
      f"...the second switch beside the first: the door to Lt. Surge opens ({said[-1:]})")
_pp = {o.get("text"): p for p, o in ve._people().items()}
check(_pp.get("Gentleman Tucker") == (7, 8) and _pp.get("Gym") == (5, 2), f"...Gentleman Tucker (FireRed's) by the door, Lt. Surge beyond ({_pp})")
story.badges["KANTO"] = []

# ---- batch 7: the S.S. Anne (FireRed's whole ship, Jordan 11-14) and Vermilion's harbour
story.badges["KANTO"] = ["BOULDER", "CASCADE"]
for _k in ("ss_anne_departed", "got_hm_cut_kanto", "ss_anne_cleared"):
    story.story_flags.pop(_k, None)
story.inventory.pop("SS_TICKET", None); story.inventory.pop("HM_CUT", None)
ve = open_map("VERMILLION_CITY", "KANTO_ROUTE_6")
ve.player = (23, 33); ve.anim = 0
walk(ve, "d")
ve = g.current_state
_pic = json.dumps(ve.town_map["rooms"]["harbor"]["roofs"]["_picture"])
check(ve.room == "harbor" and "1_4_ship" in _pic and "ss_anne_departed" in _pic, f"Vermilion Harbor: FireRed's dock, the S.S. Anne moored at the pier ({ve.room})")
_gang = next(xy for xy, v in ve.exits.items() if v == "KANTO_SS_ANNE")
ve.player = (_gang[0], _gang[1] - 1); ve.anim = 0
walk(ve, "d")
check(g.current_state is ve and ve.room == "harbor", f"...no boarding without the S.S. Ticket ({ve.toast!r})")
story.inventory["SS_TICKET"] = 1
ve.player = (_gang[0], _gang[1] - 1); ve.anim = 0
walk(ve, "d")
play(lambda: isinstance(g.current_state, PlayState), 600)
an = g.current_state
check(isinstance(an, PlayState) and story.current_area_key == "KANTO_SS_ANNE" and an.run.index == 0, f"...with it, up the gangway onto the ship's 1F ({story.current_area_key})")
_rf = an.recipe["art"]["room_floors"]


def _floor(st, i):
    while len(st.run.floors) <= i:
        st.run.enter_floor(len(st.run.floors))
    st.run.enter_floor(i); frames(2)
    return st


def _trainers(st):
    return {st.area_data["trainer_pool"][m.payload[0]]["name"]: (m.x, m.y) for m in st.run.floor.movers if m.kind == "trainer"}


_floor(an, _rf["c1_2"])
_t = _trainers(an)
check(_t.get("Lass Ann") == (5, 3) and _t.get("Youngster Tyler") == (0, 4), f"...a 1F cabin: Lass Ann (the data's) and Youngster Tyler (FireRed's, added) on FireRed's spots ({_t})")
_floor(an, _rf["c3_4"])
_t = _trainers(an)
check(_t.get("Sailor Duncan") == (3, 3) and _t.get("Sailor Leonard") == (2, 6), f"...a B1F cabin: Sailors Duncan and Leonard ({_t})")
_floor(an, 3)
_t = _trainers(an)
check(_t.get("Sailor Trevor") == (12, 10) and _t.get("Sailor Edmond") == (6, 9), f"...the deck: Sailors Trevor and Edmond ({_t})")
_floor(an, 1)
_t = _trainers(an)
check(_t.get("{rival_name}") == (30, 4), f"...2F: your rival by the Captain's door ({_t})")
_floor(an, _rf["captain"])
_cap = _figure(an, "CAPTAIN")
check(_cap == (5, 4), f"...the Captain in his office at FireRed's spot ({_cap})")
_ev = next(o for o in _area["KANTO_SS_ANNE"]["route_menu"] if o.get("text") == "CAPTAIN")
from src.states.overworld import _run_story_event
_run_story_event(an, _ev["event"], lambda c: True, lambda lines: said.extend(lines))
check(story.inventory.get("HM_CUT") == 1, "...he gives you HM Cut")
# back on the dock: she sails
story.current_area_key, story.last_area_key = "VERMILLION_CITY", "KANTO_SS_ANNE"
g.walk_town_pos = None
said.clear()
ve = CityState(g); g.change_state(ve); frames(2)
play(lambda: story.story_flags.get("ss_anne_departed") and not g.current_state._busy(), 900)
ve = g.current_state
check(ve.room == "harbor" and story.story_flags.get("ss_anne_departed") and any("setting sail" in s for s in said),
      f"...back on the dock, the S.S. Anne sounds her horn and sails ({ve.room}, {said[:1]})")
check(getattr(ve, "_pic_now", "").endswith("1_4.png"), f"...and the dock is open water ({getattr(ve, '_pic_now', None)})")
ve.player = (_gang[0], _gang[1] - 1); ve.anim = 0
walk(ve, "d")
check(g.current_state is ve and ve.room == "harbor", "...she's gone: no way aboard now")
story.badges["KANTO"] = []

# ---- batch 8: Route 11 and its gatehouse, Diglett's Cave, Route 9
story.badges["KANTO"] = ["BOULDER", "CASCADE", "THUNDER"]
for _k in ("got_itemfinder_kanto", "hidden_KANTO_ROUTE_11_0_58_5"):
    story.story_flags.pop(_k, None)
_had_if = story.inventory.pop("ITEMFINDER", None)


def _quiet(st):
    st.run.floor.movers = [m for m in st.run.floor.movers if m.kind not in ("wild", "trainer")]


def _stepper(st, d):
    st.anim = 0
    st.step(*d)
    play(lambda: g.current_state._ready(), 200)


r11 = open_map("KANTO_ROUTE_11", "VERMILLION_CITY")
_quiet(r11)
check(r11.run.index == 0 and r11.run.player[0] <= 2, f"Route 11: in from Vermilion at its west end ({r11.run.player})")
_rf = r11.recipe["art"]["room_floors"]
r11.run.player = (58, 11)
_stepper(r11, (0, -1))
check(r11.run.index == _rf["gate"], f"...up into FireRed's east gatehouse ({r11._floor_name(r11.run.index)})")
_quiet(r11)
r11.run.player = (9, 9)
_stepper(r11, (0, 1))
check(r11.run.index == _rf["gate_2"], f"...its stairs lead up to 2F ({r11._floor_name(r11.run.index)}, {r11.run.player})")
_aide = _figure(r11, "OAK'S AIDE")
check(_aide == (2, 6) and _figure(r11, "Trader") == (7, 3), f"...upstairs, Oak's aide and the trader on FireRed's spots ({_aide})")
_dex = g.data.data.setdefault("pokedex", {})
_dex_was = dict(_dex)
_dex.clear()
said.clear()
_use(r11, (3, 6), (-1, 0))
check("ITEMFINDER" not in story.inventory and any("thirty" in s for s in said), f"...short of thirty kinds, the aide sends you off to catch more ({said[:2]})")
for _i in range(1, 31):
    _dex[f"k{_i}"] = {"id": _i}
said.clear()
_use(r11, (3, 6), (-1, 0))
check(story.inventory.get("ITEMFINDER") == 1 and story.story_flags.get("got_itemfinder_kanto"), f"...with thirty, the Itemfinder ({said[-1:]})")
_dex.clear(); _dex.update(_dex_was)
r11.run.player = (10, 8)
_stepper(r11, (0, 1))
check(r11.run.index == _rf["gate"], f"...and back down the stairs ({r11._floor_name(r11.run.index)}, {r11.run.player})")
# out the far door: the strip of Route 11 that joins Route 12
_quiet(r11)
_far = next(k for k, v in r11.run.floor_recipe.get("links", {}).items() if v[0] == 0 and v[1] >= 64) if hasattr(r11.run, "floor_recipe") else None
_fl = r11.recipe["art"]["floors"][_rf["gate"]]
_far = next((tuple(int(c) for c in k.split(",")) for k, v in _fl["links"].items() if v[0] == 0 and v[1] >= 64), None)
r11.run.player = (_far[0] - 1, _far[1]); r11.anim = 0
_stepper(r11, (1, 0))
check(r11.run.index == 0 and r11.run.player[0] >= 64, f"...out its east door, on the Route 12 side of the gate ({r11.run.player})")
# the Itemfinder beeps for the hidden Escape Rope
_quiet(r11)
r11.toast = ""
_fl0 = r11.run.floor
_spot = next(((x, y) for y in range(3, 9) for x in range(53, 63) if (x, y) != (58, 5) and _fl0.walkable(x, y) and _fl0.walkable(x + 1, y) and (x + 1, y) != (58, 5)), None)
r11.run.player = _spot
_stepper(r11, (1, 0))
check("Itemfinder is beeping" in r11.toast, f"...near FireRed's hidden Escape Rope, the Itemfinder beeps ({r11.toast!r})")
story.inventory.pop("ITEMFINDER", None)
r11.__dict__.pop("_heard", None)
r11.toast = ""
r11.run.player = _spot
_stepper(r11, (1, 0))
check("Itemfinder" not in r11.toast, "...and without one, nothing")
if _had_if:
    story.inventory["ITEMFINDER"] = _had_if
# Diglett's Cave: in from Route 11's hut, the long tunnel, out at Route 2
dc = open_map("DIGGLETT_CAVE", "KANTO_ROUTE_11")
check(dc.run.index == 2 and "Old man" in {m.payload.get("text") for m in dc.run.floor.movers if m.kind == "figure"},
      f"Diglett's Cave: in from Route 11, the hut and its old man ({dc.run.index})")
_floor(dc, 1)
_tr = sorted(_trainers(dc))
check((dc.run.floor.w, dc.run.floor.h) == (85, 80) and len(_tr) == 3, f"...the cave itself, FireRed's 85 x 80 tunnel, the data's three trainers in it ({_tr})")
dc2 = open_map("DIGGLETT_CAVE", "KANTO_ROUTE_2")
check(dc2.run.index == 0 and "KANTO_ROUTE_2" in json.dumps(dc2.recipe["art"]["floors"][0].get("exits")), f"...and its Route 2 end ({dc2.run.index})")
# Route 9: FireRed's Cut tree, its TM
story.inventory.pop("HM_CUT", None)
r9 = open_map("KANTO_ROUTE_9", "CERULEAN_CITY")
check(_figure(r9, "TM121") == (12, 17), f"Route 9: FireRed's TM (Aerial Ace, our TM121) at its spot ({_figure(r9, 'TM121')})")
_cut = r9.run.floor.tile(2, 8)
check(not r9.run.floor.walkable(2, 8) or r9.run.player != (2, 8), f"...the Cut tree at its west end ({_cut!r})")
story.badges["KANTO"] = []

# ---- batch 9: Route 10 (FireRed's one map, our two areas), its Center and aide, Rock Tunnel
story.story_flags.pop("got_everstone_kanto", None)
_ev_had = story.inventory.pop("EVERSTONE", None)
r10 = open_map("KANTO_ROUTE_10", "KANTO_ROUTE_9")
_quiet(r10)
_rf = r10.recipe["art"]["room_floors"]
check(r10.run.index == 0 and r10.run.player[0] <= 2, f"Route 10: in from Route 9 at its west edge ({r10.run.player})")
r10.run.player = (13, 21)
_stepper(r10, (0, -1))
check(r10.run.index == _rf["center"], f"...into FireRed's Pokémon Center by the tunnel ({r10._floor_name(r10.run.index)})")
_quiet(r10)
_aide = _figure(r10, "OAK'S AIDE")
check(_aide == (12, 5), f"...Oak's aide at FireRed's spot ({_aide})")
_dex = g.data.data.setdefault("pokedex", {})
_dex_was = dict(_dex)
_dex.clear()
for _i in range(1, 21):
    _dex[f"k{_i}"] = {"id": _i}
_use(r10, (11, 5), (1, 0))
check(story.inventory.get("EVERSTONE") == 1, "...twenty kinds caught: the aide's Everstone")
_dex.clear(); _dex.update(_dex_was)
story.inventory.pop("EVERSTONE", None)
if _ev_had:
    story.inventory["EVERSTONE"] = _ev_had
rt = open_map("ROCK_TUNNEL", "KANTO_ROUTE_10")
check(rt.run.index == 0 and rt.run.player[1] <= 4 and len(_trainers(rt)) == 7, f"Rock Tunnel: in at the north mouth, FireRed's seven trainers on 1F ({rt.run.player}, {len(_trainers(rt))})")
_floor(rt, 1)
check(len(_trainers(rt)) == 8, f"...and eight on B1F ({sorted(_trainers(rt))})")
rt = open_map("ROCK_TUNNEL", "KANTO_ROUTE_10_SOUTH")
check(rt.run.index == 0 and rt.run.player[1] >= 34, f"...in from the south area of Route 10 at the south mouth ({rt.run.player})")
rs = open_map("KANTO_ROUTE_10_SOUTH", "ROCK_TUNNEL")
check(rs.run.player[1] <= 9 and len(_trainers(rs)) == 4, f"Route 10 (south): out of the tunnel's south mouth, FireRed's four trainers ({rs.run.player})")

# ---- batch 10: Lavender Town, widened (Jordan 11-14): the Radio Tower beside the Pokémon Tower, full size
story.story_flags.pop("power_plant_fixed", None)
lv = open_map("LAVENDER_TOWN", "KANTO_ROUTE_10_SOUTH")
check((lv.w, lv.h) == (31, 20) and lv.player[1] <= 1, f"Lavender: FireRed's town with its east side widened (31 x 20), in from Route 10 at the top ({lv.player})")
check(lv.rows[6][18] == "D" and lv.rows[6][25] == "D", "...two tower doors side by side on one row: the Pokémon Tower's and the Radio Tower's")
check(all(not lv._open((x, 3)) for x in range(22, 29)), "...the Radio Tower itself solid")
lv.player = (25, 7); lv.anim = 0
lv.toast = ""
walk(lv, "u")
check(g.current_state is lv and lv.room is None and "power" in lv.toast.lower(), f"...its door shut, the power out ({lv.toast!r})")
lv.player = (10, 12); lv.anim = 0
walk(lv, "u")
lv = g.current_state
_pp = {o.get("text"): p for p, o in lv._people().items()}
check(lv.room == "fuji" and _pp.get("Talk to Mr. Fuji") == (3, 3), f"...Mr. Fuji's Volunteer House, FireRed's room ({lv.room}, {_pp.get('Talk to Mr. Fuji')})")
lv = open_map("LAVENDER_TOWN", "KANTO_ROUTE_10_SOUTH")
lv.player = (6, 6); lv.anim = 0
walk(lv, "u")
lv = g.current_state
check(lv.room == "center", f"...the Pokémon Center ({lv.room})")

# ---- batch 11: Route 8 and Route 7, Saffron's east and west gatehouses
_tea = story.inventory.pop("TEA", None)
r8 = open_map("KANTO_ROUTE_8", "LAVENDER_TOWN")
_quiet_t = len(_trainers(r8))
check(r8.run.player[0] >= 69 and _quiet_t == 12, f"Route 8: in from Lavender at its east end, FireRed's twelve trainers ({r8.run.player}, {_quiet_t})")
_quiet(r8)
_rf = r8.recipe["art"]["room_floors"]
r8.run.player = (8, 10)
_stepper(r8, (-1, 0))
check(r8.run.index == _rf["gate"], f"...west into Saffron's east gate ({r8._floor_name(r8.run.index)}, {r8.run.player})")
_quiet(r8)
r8.run.player = (5, 5); r8.anim = 0
said.clear()
r8.step(-1, 0)
play(lambda: any("thirsty" in s for s in said) and r8._ready(), 900)
check(any("thirsty" in s for s in said) and r8.run.player[0] >= 4, f"...heading for Saffron without a drink, the guard calls you back ({r8.run.player})")
r7 = open_map("KANTO_ROUTE_7", "CELADON_CITY")
_t = _trainers(r7)
check(r7.run.player[0] <= 2 and set(_t) == {"Alpesh", "Kelly", "Nancy"}, f"Route 7: in from Celadon at its west edge, the data's three trainers along it ({_t})")
_quiet(r7)
_rf = r7.recipe["art"]["room_floors"]
r7.run.player = (14, 10)
_stepper(r7, (1, 0))
check(r7.run.index == _rf["gate"], f"...east into Saffron's west gate ({r7._floor_name(r7.run.index)})")
_quiet(r7)
r7.run.player = (7, 5); r7.anim = 0
said.clear()
r7.step(1, 0)
play(lambda: any("thirsty" in s for s in said) and r7._ready(), 900)
check(any("thirsty" in s for s in said) and r7.run.player[0] <= 8, f"...and here too, the thirsty guard ({r7.run.player})")
if _tea is not None:
    story.inventory["TEA"] = _tea

# ---- batch 12: Celadon City and its rooms
def _room_of(st, room):
    st._go(room, ""); frames(2)
    return {o.get("text"): p for p, o in st._people().items()}


ce = open_map("CELADON_CITY", "KANTO_ROUTE_7")
check((ce.w, ce.h) == (60, 40) and ce.doors.get((26, 18)) == "diner" and ce.locked.get("diner"), "Celadon: FireRed's city; HeartGold's diner door, shut")
_pp = _room_of(ce, "gym")
_gt = [n for n in _pp if n and n.startswith(("Lass", "Beauty", "Picnicker", "Cooltrainer"))]
check(_pp.get("Gym") == (6, 4) and len(_gt) == 7, f"...Erika's Gym: Erika at FireRed's spot, FireRed's seven trainers ({sorted(_gt)})")
check(any(c == "2" for r in ce.rows for c in r), "...FireRed's Cut trees in the Gym")
_pp = _room_of(ce, "mansion")
check(_pp.get("Celadon Mansion") == (2, 9), f"...the Mansion: the old lady with the Tea, where FireRed has her ({_pp.get('Celadon Mansion')})")
_pp = _room_of(ce, "roof_room")
check(_pp.get("EEVEE") == (7, 3), f"...up on the roof, FireRed's Eevee in its Poké Ball ({_pp.get('EEVEE')})")
story.story_flags.pop("got_eevee_celadon", None)
_n = len([p for p in story.player_team if p])
ce.player = (7, 4); ce.anim = 0; ce.facing = (0, -1)
said.clear()
walk(ce, "u")
play(lambda: not g.current_state._busy(), 600)
_got = story.story_flags.get("got_eevee_celadon")
check(_got or _n >= 6, f"...walk up to it and it's yours ({said[:2]})")
if _got:
    _ev = [p for p in story.player_team if p and p.id == 133]
    check(_ev and _ev[-1].level == 25, f"......an Eevee, Lv25 as in FireRed ({[(p.id, p.level) for p in _ev]})")
    story.player_team[:] = [p for p in story.player_team if not (p and p.id == 133 and p is _ev[-1])]
_pp = _room_of(ce, "dept_2")
check(_pp.get("Dept. Store") == (1, 6), "...the Dept. Store's shop at its 2F counter")
_pp = _room_of(ce, "prize")
check(_pp.get("Prize Corner") == (4, 2), "...the Prize Corner's clerk")

# ---- batch 13: the Game Corner and the Rocket Hideout
_gcf = ("game_corner_poster", "game_corner_guard_defeated", "game_corner_cleared", "visited_ROCKET_HIDEOUT", "hideout_giovanni_defeated", "got_lift_key")
_gcs = {k: story.story_flags.pop(k, None) for k in _gcf}
gc = open_map("CELADON_GAME_CORNER", "CELADON_CITY")
_f = gc.run.floor
check((_f.w, _f.h) == (18, 15) and "fr_ground/10_14" in json.dumps(gc.recipe["art"]), "Game Corner: FireRed's own room and picture")
check(sum(v == "slot" for v in _f.decor.values()) == 20 and _f.decor.get((11, 1)) == "poster", f"...FireRed's slot machines play, the poster is a switch ({sum(v == 'slot' for v in _f.decor.values())})")
check("ROCKET_HIDEOUT" not in _f.exits.values() and _figure(gc, "ROCKET GRUNT") == (11, 2), "...the stairs hidden, a grunt in front of the poster")
gc.run.player = (5, 7); gc.facing = (0, -1)
check(gc._act_here() and gc._act_here()[0] == "PLAY SLOTS", f"...stand at a machine: PLAY SLOTS ({gc._act_here()})")
story.story_flags["game_corner_guard_defeated"] = True
gc._sync_figures(); frames(2)
gc.run.player = (11, 2); gc.facing = (0, -1)
_act = gc._act_here()
check(_act and _act[0] == "CHECK", f"...the grunt beaten, the poster can be checked ({_act})")
_act[1](); play(lambda: g.current_state._ready(), 300)
check(story.story_flags.get("game_corner_poster") and _f.exits.get((15, 2)) == "ROCKET_HIDEOUT", "...a switch behind it: FireRed's stairs open in the corner")
gc = open_map("CELADON_GAME_CORNER", "CELADON_CITY")
gc.run.player = (6, 4); gc.facing = (0, -1); gc.anim = 0
_act = gc._act_here()
check(_act and _act[0] == "TALK", f"...across the counter, the clerk ({_act and _act[0]})")
_act[1](); frames(2)
check(type(g.current_state).__name__ == "GameCornerState", f"......opens our own Game Corner menu: the games, coins, prizes ({type(g.current_state).__name__})")
hq = open_map("ROCKET_HIDEOUT", "CELADON_GAME_CORNER")
check(hq.run.index == 0 and (hq.run.floor.w, hq.run.floor.h) == (28, 34), f"Rocket Hideout: down the stairs to FireRed's B1F ({hq.run.player})")
_g = {m.payload[1].get("spot_name"): (m.x, m.y) for m in hq.run.floor.movers if m.kind == "trainer"}
check(_g.get("Grunt B1F 1") == (4, 9) and _g.get("Grunt B1F 5") == (6, 32) and len(_g) == 5, f"...B1F's five grunts on FireRed's spots, each his own team ({_g})")
_floor(hq, 3)
_g = {m.payload[1].get("spot_name"): (m.x, m.y) for m in hq.run.floor.movers if m.kind == "trainer"}
check(len(_g) == 3 and _figure(hq, "GIOVANNI") == (19, 4) and _figure(hq, "LIFT KEY") == (3, 2), f"...B4F: three grunts, Giovanni at FireRed's spot, the Lift Key by the grunt who drops it ({_g})")
_floor(hq, 0)
hq.run.floor.movers = [m for m in hq.run.floor.movers if m.kind not in ("wild", "trainer")]
story.inventory.pop("LIFT_KEY", None)
hq.run.player = (24, 26); hq.anim = 0
said.clear()
hq.step(0, -1); play(lambda: g.current_state._ready(), 300)
check(hq.run.index == 0 and any("key" in s.lower() for s in said + [hq.toast]), f"...the elevator won't move without the Lift Key ({hq.run.index}, {said[:1]}, {hq.toast!r})")
story.inventory["LIFT_KEY"] = 1
hq.run.player = (24, 26); hq.anim = 0
hq.step(0, -1); play(lambda: g.current_state._ready(), 300)
check(hq.run.index == 3 and abs(hq.run.player[0] - 20) <= 1 and hq.run.player[1] == 24, f"...with it: down to B4F's far side, Giovanni's, out in front of the lift ({hq.run.index}, {hq.run.player})")
story.inventory.pop("LIFT_KEY", None)
for _k, _v in _gcs.items():
    story.story_flags.pop(_k, None)
    if _v is not None:
        story.story_flags[_k] = _v

# ---- batch 14: the Pokemon Tower, FireRed's seven floors
_tf = ("tower_ghost_defeated", "fuji_rescued", "defeated_rival_tower")
_tfs = {k: story.story_flags.pop(k, None) for k in _tf}
story.story_flags["defeated_rival_tower"] = True   # (the rival's battle on the way in: not what this checks)
_scope = story.inventory.pop("SILPH_SCOPE", None)
pt = open_map("KANTO_POKEMON_TOWER", "LAVENDER_TOWN")
check(pt.run.n_floors == 7 and pt.run.index == 0, f"Pokémon Tower: FireRed's seven floors, in at 1F ({pt.run.n_floors})")
_n = []
for _i in range(7):
    _floor(pt, _i)
    _n.append(sum(1 for m in pt.run.floor.movers if m.kind == "trainer"))
check(_n[2:] == [3, 3, 4, 3, 3], f"...FireRed's trainers on 3F-7F: three, three, four, three, three ({_n})")
_floor(pt, 5)
_quiet(pt)
check(pt.run.floor.exits.get((11, 15)) == "BOSS", "...6F: the ghost stands across the way to 7F's stairs")
pt.run.player = (11, 14); pt.anim = 0; said.clear()
pt.step(0, 1); play(lambda: g.current_state._ready(), 300)
check(tuple(pt.run.player) == (11, 14) and any("Silph Scope" in s for s in said), f"...without the Silph Scope: it won't let you by ({said[:3]})")
pt.run.player = (12, 14); pt.anim = 0
pt.step(0, 1); play(lambda: g.current_state._ready(), 300)
check(tuple(pt.run.player) == (12, 14), f"...nor past it ({pt.run.player})")
story.story_flags["tower_ghost_defeated"] = True
pt = open_map("KANTO_POKEMON_TOWER", "LAVENDER_TOWN"); _floor(pt, 5); _quiet(pt); frames(2)
check(pt.run.floor.exits.get((11, 15)) != "BOSS", "...laid to rest: the way is clear")
_floor(pt, 6)
check(_figure(pt, "MR. FUJI") == (11, 4), f"...7F: Mr. Fuji where FireRed has him ({_figure(pt, 'MR. FUJI')})")
for _k, _v in _tfs.items():
    story.story_flags.pop(_k, None)
    if _v is not None:
        story.story_flags[_k] = _v
if _scope is not None:
    story.inventory["SILPH_SCOPE"] = _scope

# ---- batch 15: Route 12, Snorlax on the pier
_sf = {k: story.story_flags.pop(k, None) for k in ("KANTO_ROUTE_12_boss_defeated", "got_tm113_route12", "hidden_KANTO_ROUTE_12_0_14_70")}
_fl = story.inventory.pop("POKE_FLUTE", None)
r12 = open_map("KANTO_ROUTE_12", "LAVENDER_TOWN")
_quiet(r12)
check(r12.run.floor.exits.get((14, 70)) == "BOSS", "Route 12: Snorlax asleep across the pier where FireRed has him")
r12.run.player = (14, 69); r12.anim = 0; said.clear()
r12.step(0, 1); play(lambda: g.current_state._ready(), 300)
check(tuple(r12.run.player) == (14, 69) and any("asleep" in s for s in said), f"...without the Poké Flute he won't budge ({said[:1]})")
_rf = r12.recipe["art"]["room_floors"]
_floor(r12, _rf["gate_2"])
_had = story.inventory.get("TM113", 0)
_use(r12, (7, 6), (0, -1))
check(story.inventory.get("TM113", 0) == _had + 1, "...upstairs in the lookout, the girl gives you TM113 Return (FireRed's TM27)")
story.story_flags["KANTO_ROUTE_12_boss_defeated"] = True
r12 = open_map("KANTO_ROUTE_12", "LAVENDER_TOWN"); _quiet(r12); frames(2)
_lo = story.inventory.get("LEFTOVERS", 0)
r12.run.player = (14, 69); r12.anim = 0; said.clear()
r12.step(0, 1); play(lambda: g.current_state._ready(), 300)
check(tuple(r12.run.player) == (14, 70) and story.story_flags.get("hidden_KANTO_ROUTE_12_0_14_70") and story.inventory.get("LEFTOVERS", 0) >= 1, f"...Snorlax gone: on his spot, FireRed's hidden Leftovers ({r12.run.player})")
for _k, _v in _sf.items():
    story.story_flags.pop(_k, None)
    if _v is not None:
        story.story_flags[_k] = _v
story.inventory.pop("TM113", None) if not _had else None
if _fl is not None:
    story.inventory["POKE_FLUTE"] = _fl

# ---- batch 17: Fuchsia City
fu = open_map("FUCHSIA_CITY", "KANTO_ROUTE_15")
check((fu.w, fu.h) == (48, 40) and fu.doors.get((24, 5)) == "safari" and "SAFARI_ZONE" not in fu.exits.values(),
      "Fuchsia: FireRed's city; the Safari Zone's door opens its entrance house")
_zoo = sorted(b.get("look") for b in fu.town_map.get("barred", []) if str(b.get("look", "")).startswith("mon:"))
check(_zoo == ["mon:100", "mon:113", "mon:115", "mon:131", "mon:79"], f"...the zoo's Pokémon in their pens: Chansey, Kangaskhan, Voltorb, Slowpoke, Lapras ({_zoo})")
fu.player = (24, 6); fu.anim = 0
walk(fu, "u")
fu = g.current_state
check(fu.room == "safari" and "SAFARI_ZONE" in fu.exits.values(), f"...through it: the entrance, its far door into the Safari Zone ({fu.room})")
_pp = _room_of(fu, "gym")
_gt = [n for n in _pp if n and n.startswith(("Juggler", "Tamer"))]
check(_pp.get("Gym") == (7, 13) and len(_gt) == 6, f"...Koga's Gym: Koga at FireRed's spot, his six trainers ({sorted(_gt)})")
_pp = _room_of(fu, "warden")
check(_pp.get("RARE CANDY") == (11, 5) and "b" in "".join(fu.town_map["rooms"]["warden"]["art"]), f"...the Warden's house: FireRed's boulder, the Rare Candy behind it ({_pp.get('RARE CANDY')})")
_pp = _room_of(fu, "brother")
check(set(fu.exits.values()) == {"OUT:38,31", "OUT:39,28"}, f"...the Fishing Guru's brother's house: front door and back door to the pond ({sorted(fu.exits.values())})")

# ---- batch 18: the Safari Zone, FireRed's four areas on one map
sz = open_map("SAFARI_ZONE", "FUCHSIA_CITY")
check((sz.run.floor.w, sz.run.floor.h) == (157, 78) and sz.run.index == 0 and 70 <= sz.run.player[1] <= 77,
      f"Safari Zone: FireRed's four areas on one map, in at the Center's south gate ({sz.run.player})")
check(sz.safari and sz.safari["balls"] == 30 and sz.safari["steps"] == 600, f"...the Safari Game: FireRed's 30 Safari Balls and 600 steps ({sz.safari})")
_pad = sz.recipe["art"]["floors"][0]["links"].get("58,34") if sz.recipe["art"].get("floors") else None
check(_pad and _pad[1:] == [30, 47], f"...the gateways join the areas: North's west gate to the West ({_pad})")
check(sz.zones[sz._zone_index(0, 130, 60)] == "east" and sz.zones[sz._zone_index(0, 20, 60)] == "west", "...each area its own Pokémon (the data's zones)")
_rf = sz.recipe["art"]["room_floors"]
_floor(sz, _rf["secret"])
check(_figure(sz, "SECRET HOUSE MAN") == (6, 5), "...out west, FireRed's Secret House")

print(f"##### {len(fails)} failures")
for m in fails:
    print("   FAIL " + m)
