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
            st.dialogue_box.is_finished = True
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
    targets = set(v for f in _parts for v in f.get("exits", {}).values())
    known = {o.get("target_area") or o.get("target") for o in a.get("travel_options", []) + a.get("route_menu", []) + a.get("explore_options", [])}
    check(targets <= known, f"{key}: every way out on the map is a way out in the story data {sorted(targets - known)}")
    came = sorted(targets)[0] if targets else key
    st = open_map(key, came)
    is_town = isinstance(st, _WTS)
    w, h = (st.w, st.h) if is_town else (st.run.floor.w, st.run.floor.h)
    check((w, h) == (len(m["art"][0]), len(m["art"])) and (is_town or isinstance(st, DungeonState)),
          f"{key}: opens on its FireRed map ({w} x {h}, {'town' if is_town else 'route'}), in from {came}")
    check("fr_ground/" in json.dumps(m.get("roofs", {})), f"{key}: drawn from FireRed's own picture")
    grid = m["art"]
    if not m.get("parts") and not m.get("floors"):
        walkable = set(".=\"NX!ow$[]{}%_()D<>^vnwu20b:|;,'")
        starts = [(x, y) for y, r in enumerate(grid) for x, c in enumerate(r) if c in "<>^vnwu"]
        seen, todo = set(starts[:1]), deque(starts[:1])
        while todo:
            x, y = todo.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                t = (x + dx, y + dy)
                if 0 <= t[0] < w and 0 <= t[1] < h and t not in seen and grid[t[1]][t[0]] in walkable:
                    seen.add(t); todo.append(t)
        cut = [(x, y, c) for y, r in enumerate(grid) for x, c in enumerate(r) if c in "<>^vnwuDNX" and (x, y) not in seen]
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

print(f"##### {len(fails)} failures")
for m in fails:
    print("   FAIL " + m)
