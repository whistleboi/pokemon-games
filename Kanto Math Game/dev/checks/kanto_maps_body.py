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
        if type(st).__name__ in ("HallOfFameState", "IntroSpeechState"):   # (11-19: animated scenes - tap on, as a player does)
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "npc_active", False):
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
    targets = targets or set(v for f in (m.get("rooms") or {}).values() for v in f.get("exits", {}).values() if not str(v).startswith(("ROOM:", "OUT:")))   # (no way out but a room's: Birth Island's harbour boat, 11-17)
    known = {o.get("target_area") or o.get("target") for o in a.get("travel_options", []) + a.get("route_menu", []) + a.get("explore_options", [])}
    check(targets <= known, f"{key}: every way out on the map is a way out in the story data {sorted(targets - known)}")
    came = sorted(targets)[0] if targets else key
    st = open_map(key, came)
    is_town = isinstance(st, _WTS)
    w, h = (st.w, st.h) if is_town else (st.run.floor.w, st.run.floor.h)
    _here = _parts[st.run.index] if (not is_town and m.get("floors") and st.run.index < len(_parts)) else None if (not is_town and m.get("floors")) else m   # (None: landed in a room of a map of floors - Navel Rock's harbour, 11-23)
    _sizes = {(len(f["art"][0]), len(f["art"])) for f in ([_here] if _here else []) + ([] if is_town else [r for r in (m.get("rooms") or {}).values() if came in r.get("exits", {}).values()])}   # (you can land in a room: Birth Island's harbour)
    check((w, h) in _sizes and (is_town or isinstance(st, DungeonState)),
          f"{key}: opens on its FireRed map ({w} x {h}, {'town' if is_town else 'route'}), in from {came}")
    check(all("fr_ground/" in json.dumps(f.get("roofs", {})) for f in (_parts[:1] if key == "THREE_ISLE_PORT" else _parts)), f"{key}: drawn from FireRed's own picture (every floor)")   # (Three Isle Path, 11-19: the tunnel is FireRed's dug layout 319; its grass pocket stays the old build's - k_batch36)
    if key == "THREE_ISLE_PORT":   # (11-19: FireRed's dug tunnel, its prospector and hidden Nugget on FireRed's own tiles)
        _t0 = _parts[0]
        check("2_134" in json.dumps(_t0.get("roofs", {})) and _t0["art"][2][23] == "N" and (_t0.get("hidden") or {}).get("21,3") == "NUGGET"
              and (_t0.get("links") or {}).get("25,5") == [1, 12, 2],
              "Three Isle Path: FireRed's dug tunnel (layout 319), the prospector at (23,2), the hidden Nugget at (21,3), the east mouth down to the grass pocket")
    grid = (_here or {}).get("art") or []
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
story.player_team[0].current_hp = 1   # (a hard-won battle: the opening battle heals you after, won or lost; Jordan 11-15)
_pot = story.inventory.get("POTION", 0)
_balls = story.balls_left
b.exit_battle()
check(story.balls_left == _balls, f"...and no Poké Balls from it: you can't catch yet (Jordan 11-15) ({story.balls_left - _balls})")
check(story.player_team[0].current_hp == story.player_team[0].get_max_hp(), "after the rival's first battle your team is healed")
said.clear()
play(lambda: isinstance(g.current_state, _WTS), 600)
t = g.current_state
check(isinstance(t, _WTS) and t.room == "lab" and story.story_flags.get("defeated_rival_kanto"), f"after the battle you're back in the Lab ({getattr(t, 'room', None)})")
_walked = []
def _watch():
    st = g.current_state
    for h, o in (getattr(st, "motions", None) or {}).items():
        if getattr(o, "path", None):
            _walked.append(tuple(o.path[-1]))
    return story.story_flags.get("kanto_rival_left_lab") and not st._busy()
play(_watch, 3000)
t = g.current_state
check((6, 12) in _walked, f"the rival walks out by the Lab's door ({sorted(set(_walked))[:4]})")
check(story.story_flags.get("kanto_rival_left_lab") and any("Smell you later" in s for s in said)
      and not any("{rival_name}" == o.get("text") for o in t._people().values()),
      f"the rival says his piece and leaves ({said[-1:]})")
check(not any("Poke Ball" in str(o.get("text")) for o in t._people().values()), "the Poké Balls are put away")
t.player = (6, 8); t.anim = 0
walk(t, "u"); play(lambda: story.story_flags.get("got_oak_potions") and not g.current_state._busy(), 1500); tap(g.current_state)
t = g.current_state
check(story.inventory.get("POTION", 0) == _pot + 5 and any("Potions" in x for x in said),
      f"...and Oak gives you five Potions for the road to Viridian ({story.inventory.get('POTION', 0) - _pot})")
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
_cm = next(m for m in p.run.floor.movers if m.kind == "figure" and m.payload.get("text") == "POKE MART CLERK")
_pot = story.inventory.get("POTION", 0)
said.clear()
p._use_figure(_cm)
play(lambda: not p.dialogue_box.visible, 300)
p._sync_figures()
check(story.inventory.get("POTION", 0) == _pot + 1 and any(m is _cm for m in p.run.floor.movers),
      "Route 1: the clerk's free Potion, and he's still standing there afterwards (not gone on the spot)")
said.clear()
p._use_figure(_cm)
play(lambda: not p.dialogue_box.visible, 300)
check(story.inventory.get("POTION", 0) == _pot + 1 and any("any time" in s for s in said),
      f"...talked to again: no second Potion, just a word about the Mart ({said[:1]})")
p = open_map("KANTO_ROUTE_1", "PALLET_TOWN")
check(not any(f.get("text") == "POKE MART CLERK" for f in p.placed), "...come back later: he's gone back to his Mart")

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
_who = [k for k, o in v._people().items() if o.get("text") == "Clerk"]
check(v.room == "mart" and _who, "Viridian Mart: the clerk stays behind his counter with the Parcel handed over")
said.clear()
v._talk(_who[0])
play(lambda: any("Professor Oak" in s for s in said) and not g.current_state._busy(), 400)
check(any("parcel to Professor Oak" in s for s in said) and story.inventory.get("OAKS_PARCEL") == 1,
      f"...talked to: take the Parcel to Oak (no second one) ({said[:1]})")
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
# (first, Jordan's own: Jessie & James jump you at the locked doors on your first look; yellow_kanto plays it through)
v = open_map("VIRIDIAN_CITY", "KANTO_ROUTE_1")
v.player = (36, 11); v.anim = 0; v.facing = (0, -1)
walk(v, "u")
check(isinstance(g.current_state, (TrainerIntroState, TrainerBattleState)), f"Viridian Gym: Jessie & James jump you at its locked doors ({type(g.current_state).__name__})")
story.story_flags["viridian_rocket_defeated"] = True
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
check(len(_tr) == 7 and (16, 5) in _tr and (47, 45) in _tr and (29, 23) in _tr and (12, 31) in _tr, f"Viridian Forest: the five Bug Catchers on FireRed's spots, and Yellow's two ({_tr})")
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
check({"MOON STONE", "TM056", "RARE CANDY"} <= _items, f"...FireRed's item balls on 1F ({sorted(_items)[:6]})")
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
check(_figure(r4, "TM172") == (45, 5), f"...FireRed's TM (Roar, our TM120) on the ledge ({_figure(r4, 'TM172')})")
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
story.inventory.pop("TM055", None)
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
check(story.inventory.get("TM055") == 1 and story.story_flags.get("got_tm_dig_cerulean"), "...beaten, he hands back TM28 Dig (our TM15)")
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
_nm = story.story_flags.pop("network_machine_fixed", None); _vc = story.story_flags.pop("visited_CERULEAN_CAVE", None)
check(any(o.get("text") == "Cave guard" for o in ce._people().values()), "...stays for a Champion who hasn't done the Sevii network job (FireRed; Jordan 11-16)")
story.story_flags["network_machine_fixed"] = True
check(not any(o.get("text") == "Cave guard" for o in ce._people().values()), "...and steps aside once you're Champion and Celio's Network Machine works")
for _k, _v in (("network_machine_fixed", _nm), ("visited_CERULEAN_CAVE", _vc)):
    story.story_flags.pop(_k, None)
    if _v:
        story.story_flags[_k] = _v
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
check((dc.run.floor.w, dc.run.floor.h) == (85, 80) and len(_tr) == 0, f"...the cave itself, FireRed's 85 x 80 tunnel; no trainers in it, as FireRed (the data's three were removed 11-17) ({_tr})")
dc2 = open_map("DIGGLETT_CAVE", "KANTO_ROUTE_2")
check(dc2.run.index == 0 and "KANTO_ROUTE_2" in json.dumps(dc2.recipe["art"]["floors"][0].get("exits")), f"...and its Route 2 end ({dc2.run.index})")
# Route 9: FireRed's Cut tree, its TM
story.inventory.pop("HM_CUT", None)
r9 = open_map("KANTO_ROUTE_9", "CERULEAN_CITY")
check(_figure(r9, "TM027") == (12, 17), f"Route 9: FireRed's TM (Aerial Ace, our TM121) at its spot ({_figure(r9, 'TM027')})")
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
check(r7.run.player[0] <= 2 and not _t and not _area["KANTO_ROUTE_7"]["trainer_pool"], f"Route 7: in from Celadon at its west edge; no trainers, as FireRed (Kelly, Nancy and Alpesh removed 11-17, Jordan) ({_t})")
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
check(len(_g) == 4 and (19, 8) in _g.values() and _figure(hq, "GIOVANNI") == (19, 4) and _figure(hq, "LIFT KEY") == (3, 2), f"...B4F: three grunts and Yellow's Jessie & James, Giovanni at FireRed's spot, the Lift Key by the grunt who drops it ({_g})")
_floor(hq, 0)
hq.run.floor.movers = [m for m in hq.run.floor.movers if m.kind not in ("wild", "trainer")]
story.inventory.pop("LIFT_KEY", None)
hq.run.player = (24, 26); hq.anim = 0
said.clear()
hq.step(0, -1); play(lambda: g.current_state._ready(), 300)   # (11-23, K2: FireRed's walk-in lift - into the car, any time)
_car = (hq.run.index, tuple(hq.run.player))
hq.run.player = (0, 3); hq.anim = 0
hq.step(0, -1); play(lambda: g.current_state._ready(), 300)   # (its panel, no Lift Key)
check(_car[0] == 4 and hq.run.index == 4 and type(g.current_state).__name__ != "PickListState" and any("key" in s.lower() for s in said + [hq.toast]),
      f"...into B1F's lift; its panel won't work without the Lift Key ({_car}, {said[-1:]}, {hq.toast!r})")
story.inventory["LIFT_KEY"] = 1
hq.run.player = (0, 3); hq.anim = 0
hq.step(0, -1); play(lambda: type(g.current_state).__name__ == "PickListState", 200)
_pkH = g.current_state if type(g.current_state).__name__ == "PickListState" else None
if _pkH:
    _pkH.done(6)
play(lambda: type(g.current_state).__name__ == "PlayState" and g.current_state._ready(), 600)
hq = g.current_state
_car4 = (hq.run.index, tuple(hq.run.player))
hq.run.floor.movers = [m for m in hq.run.floor.movers if m.kind == "figure"]
hq.anim = 0
hq.step(0, 1); play(lambda: g.current_state._ready(), 300)
check(_pkH is not None and [c[0] for c in _pkH.choices] == ["B1F", "B2F", "B4F"] and _car4 == (6, (2, 4)) and hq.run.index == 3 and tuple(hq.run.player) == (20, 24),
      f"...with it, the panel: B1F, B2F, B4F; down to B4F's far side, Giovanni's, out in front of the lift ({_car4}, {hq.run.index}, {hq.run.player})")
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
_had = story.inventory.get("TM274", 0)
_use(r12, (7, 6), (0, -1))
check(story.inventory.get("TM274", 0) == _had + 1, "...upstairs in the lookout, the girl gives you TM113 Return (FireRed's TM27)")
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
story.inventory.pop("TM274", None) if not _had else None
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

# ---- batch 19: Routes 18, 17 (Cycling Road) and 16
r16 = open_map("KANTO_ROUTE_16", "CELADON_CITY")
_sn16 = story.story_flags.pop("KANTO_ROUTE_16_boss_defeated", None)
r16 = open_map("KANTO_ROUTE_16", "CELADON_CITY")
check(r16.run.floor.exits.get((31, 13)) == "BOSS", "Route 16: Snorlax asleep where FireRed has him")
_rf = r16.recipe["art"]["room_floors"]
_floor(r16, _rf["gate_2"])
check(_figure(r16, "OAK'S AIDE") == (10, 6), "...the Cycling Road gate's upstairs: Oak's aide (FireRed's Amulet Coin for forty kinds)")
if _sn16 is not None:
    story.story_flags["KANTO_ROUTE_16_boss_defeated"] = _sn16
r18 = open_map("KANTO_ROUTE_18", "FUCHSIA_CITY")
_rf = r18.recipe["art"]["room_floors"]
_floor(r18, _rf["gate_2"])
check(_figure(r18, "Trader") == (5, 3), "Route 18: upstairs in the gate, FireRed's trader (his Lickitung for a Golduck)")
r17 = open_map("KANTO_ROUTE_17", "KANTO_ROUTE_16")
check(set(r17.run.floor.exits.values()) <= {"KANTO_ROUTE_16", "KANTO_ROUTE_18"} and r17._here_art().get("downhill") == [0, 158],
      "Cycling Road: FireRed's road, downhill all the way")

# ---- batch 20: Saffron City
_sc = story.story_flags.pop("silph_co_cleared", None)
sa = open_map("SAFFRON_CITY", "KANTO_ROUTE_5")
_pp = {o.get("text"): p for p, o in sa._people().items()}
check((sa.w, sa.h) == (66, 55) and sa.doors.get((20, 7)) == "station" and _pp.get("Grunt  ") == (46, 13),
      f"Saffron: FireRed's city; HeartGold's Magnet Train station in the north-west; a grunt blocks the Gym ({_pp.get('Grunt  ')})")
story.story_flags["silph_co_cleared"] = True
sa = open_map("SAFFRON_CITY", "KANTO_ROUTE_5")
_pp = {o.get("text"): p for p, o in sa._people().items()}
check("Grunt  " not in _pp and _pp.get("Pidgeot") == (45, 22), "...Silph freed: the grunts are gone, the people come back out")
_pp = _room_of(sa, "gym")
_gt = [n for n in _pp if n and n.startswith(("Psychic ", "Channeler "))]
_pads = [k for k in (sa.town_map["rooms"]["gym"].get("links") or {})]
check(_pp.get("Gym") == (14, 11) and len(_gt) == 7 and len(_pads) >= 30, f"...Sabrina's Gym: Sabrina at FireRed's spot, seven trainers, FireRed's warp pads ({len(_gt)}, {len(_pads)} pads)")
_pp = _room_of(sa, "copycat_2")
check(_pp.get("Visit Copycat") == (9, 6), "...the Copycat in her room upstairs")
_pp = _room_of(sa, "psychic")
check(_pp.get("Mr. Psychic") == (7, 4), "...Mr. Psychic (FireRed's TM29 Psychic)")
_pp = _room_of(sa, "dojo")
check((_pp.get("Fighting Dojo") or _pp.get("Karate Master Koichi")) == (6, 5) and sum(1 for n in _pp if n and n.startswith("Black Belt")) == 4, "...the Fighting Dojo: the Karate Master and FireRed's four Black Belts")
_dj = {t["name"]: t for t in _area["SAFFRON_CITY"]["dojo_trainers"]}
_ko = next(o for o in _area["SAFFRON_CITY"]["explore_options"] if o.get("text") == "Karate Master Koichi")["event"]["battle"]
check(_dj["Black Belt Aaron"]["levels"] == [36] and (_ko["team"], _ko["levels"]) == ([106, 107], [37, 37])
      and [t["levels"] for t in _area["SAFFRON_CITY"]["gym"]["trainers"]] == [[34, 34], [38], [33, 33, 33], [31, 31, 31, 31], [38], [33, 33, 33], [34, 34]],
      "...FireRed's levels: the Dojo's Black Belts, the master's Hitmonlee and Hitmonchan (a battle before his prize, 11-17), Sabrina's seven Gym trainers")
story.story_flags.pop("silph_co_cleared", None)
if _sc is not None:
    story.story_flags["silph_co_cleared"] = _sc

# ---- batch 21: Silph Co., FireRed's eleven floors
_sf = ("silph_co_cleared", "got_card_key")
_sfs = {k: story.story_flags.pop(k, None) for k in _sf}
_ck = story.inventory.pop("CARD_KEY", None)
si = open_map("SILPH_CITY", "SAFFRON_CITY")
check(si.run.n_floors == 22 and si.run.index == 0 and (si.run.floor.w, si.run.floor.h) == (36, 22), f"Silph Co.: FireRed's eleven floors (and a lift car for each, 11-23), in at 1F ({si.run.n_floors}, {si.run.player})")
_n, _who = [], {}
for _i in range(11):
    _floor(si, _i)
    _ms = [m for m in si.run.floor.movers if m.kind == "trainer"]
    _n.append(len(_ms))
    for m in _ms:
        _who[m.payload[1].get("spot_name") or m.payload[1]["name"]] = (_i, m.x, m.y)
check(_n == [1, 4, 2, 3, 4, 3, 5, 3, 3, 2, 4], f"...FireRed's trainers floor by floor (Connor on 2F and Taylor on 6F since 11-17), the data's among them, and Yellow's Jessie & James on 11F ({_n})")
check(_who.get("Scientist Connor") == (1, 5, 19) and _who.get("Scientist Taylor") == (5, 9, 11) and _who.get("Scientist Rodney") == (3, 14, 8) and _who.get("Scientist Joshua") == (6, 3, 13),
      f"...FireRed's four Scientists on their own tiles: Connor 2F, Rodney 4F, Taylor 6F, Joshua 7F")
check(_who.get("Grunt 3F") == (2, 25, 9) and _who.get("Admin Proton") == (7, 28, 5) and _who.get("Archer") == (8, 15, 18),
      f"...the data's on the floors their words name: the warp-panel grunt on 3F, Proton on 8F, Archer on 9F ({_who.get('Admin Proton')}, {_who.get('Archer')})")
check(_who.get("{rival_name}") == (6, 2, 6) and _who.get("Giovanni") == (10, 6, 11) and _who.get("Executive Ariana") == (10, 16, 12),
      f"...your rival on 7F; Giovanni and Ariana on 11F, where FireRed has the Boss and his guard ({_who.get('Giovanni')})")
_floor(si, 4)
check(_figure(si, "CARD KEY") == (22, 21) and "1_51_locked" in json.dumps(si.recipe), f"...5F: the Card Key on the floor; the doors drawn locked ({_figure(si, 'CARD KEY')})")
si.run.floor.movers = [m for m in si.run.floor.movers if m.kind not in ("wild", "trainer")]
si.run.player = (6, 9); si.anim = 0; said.clear()
si.step(1, 0); play(lambda: g.current_state._ready(), 300)
check(tuple(si.run.player) == (6, 9) and any("Card Key" in s for s in said + [si.toast]), f"...a locked door won't open without it ({si.run.player}, {said[:1]}, {si.toast!r})")
story.inventory["CARD_KEY"] = 1; story.story_flags["got_card_key"] = True
si.run.player = (6, 9); si.anim = 0
si.step(1, 0); play(lambda: g.current_state._ready(), 300)
check(tuple(si.run.player) == (7, 9), f"...with the Card Key, through it ({si.run.player})")
# (11-23, K2: FireRed's walk-in lift - in at 5F's lift door, press the panel, ride to 3F, step out by 3F's lift door)
si.run.floor.movers = [m for m in si.run.floor.movers if m.kind not in ("wild", "trainer")]
si.run.player = (22, 4); si.anim = 0; said.clear()
si.step(0, -1); play(lambda: g.current_state._ready(), 300)
_in5 = (si.run.index, tuple(si.run.player))
si.run.floor.movers = [m for m in si.run.floor.movers if m.kind == "figure"]
si.run.player = (0, 3); si.anim = 0
si.step(0, -1); play(lambda: type(g.current_state).__name__ == "PickListState", 200)
_pkL = g.current_state if type(g.current_state).__name__ == "PickListState" else None
_rows = [r[0] for r in _pkL.choices] if _pkL else []
if _pkL:
    _pkL.done(13)
play(lambda: type(g.current_state).__name__ == "PlayState" and g.current_state._ready(), 600)
si = g.current_state
_in3 = (getattr(getattr(si, "run", None), "index", None), tuple(getattr(getattr(si, "run", None), "player", ())))
si.run.floor.movers = [m for m in si.run.floor.movers if m.kind == "figure"]
si.anim = 0
si.step(0, 1); play(lambda: g.current_state._ready(), 300)
_nearL = sorted((m.kind, m.x, m.y) for m in si.run.floor.movers if abs(m.x - 22) + abs(m.y - 4) <= 2)
check(_in5 == (15, (2, 4)) and _pkL is not None and _in3 == (13, (2, 4)) and (si.run.index, tuple(si.run.player)) == (2, (22, 4)),
      f"...FireRed's lift: in at 5F's lift door, the panel asks which floor, the car stops at 3F and you step out by 3F's lift door ({_in5}, {_rows[:3]}, {_in3}, {si.run.index}, {si.run.player}, near {_nearL})")
_floor(si, 6)
check(_figure(si, "LAPRAS") == (0, 7), f"...7F: the worker who gives you a Lapras ({_figure(si, 'LAPRAS')})")
_floor(si, 8)
check(_figure(si, "NURSE") == (2, 16), "...9F: the nurse who rests your team")
story.story_flags["silph_co_cleared"] = True
si = open_map("SILPH_CITY", "SAFFRON_CITY"); _floor(si, 10)
check(_figure(si, "VISIT THE PRESIDENT") == (9, 9), f"...Silph freed: the President in his boardroom ({_figure(si, 'VISIT THE PRESIDENT')})")
story.inventory.pop("CARD_KEY", None)
if _ck is not None:
    story.inventory["CARD_KEY"] = _ck
for _k, _v in _sfs.items():
    story.story_flags.pop(_k, None)
    if _v is not None:
        story.story_flags[_k] = _v

# ---- batch 22: Routes 19, 20 and 21, the sea routes
r19 = open_map("KANTO_ROUTE_19", "FUCHSIA_CITY")
_t = _trainers(r19)
check((r19.run.floor.w, r19.run.floor.h) == (24, 60) and len(_t) == 11 and _t.get("Axle") == (11, 47) and _t.get("Lia & Luc") == (8, 41),
      f"Route 19: FireRed's beach and sea, its eleven swimmers on FireRed's spots ({len(_t)})")
check({"FUCHSIA_CITY", "KANTO_ROUTE_20"} <= set(r19.run.floor.exits.values()), "...up to Fuchsia, west on to Route 20")
r20 = open_map("KANTO_ROUTE_20", "KANTO_ROUTE_19")
_t = _trainers(r20)
_ex = r20.run.floor.exits
check((r20.run.floor.w, r20.run.floor.h) == (120, 20) and len(_t) == 10 and _ex.get((60, 8)) == "SEAFOAM_ISLANDS" and _ex.get((72, 14)) == "SEAFOAM_ISLANDS",
      f"Route 20: FireRed's sea, ten trainers, the Seafoam Islands' two mouths ({len(_t)}, {[k for k, v in _ex.items() if v == 'SEAFOAM_ISLANDS']})")
check("CINNABAR_ISLAND" in _ex.values(), "...west to Cinnabar Island")
check(any(h for h in (r20._here_art().get("hidden") or {}).values()) or bool(r20._here_art().get("hidden")), "...FireRed's hidden Stardust")
r21 = open_map("KANTO_ROUTE_21", "PALLET_TOWN")
_t = _trainers(r21)
check((r21.run.floor.w, r21.run.floor.h) == (24, 100) and len(_t) == 9 and _t.get("Wade") == (16, 26) and _t.get("Jerome") == (15, 88),
      f"Route 21: FireRed's two maps as one, Pallet to Cinnabar, nine trainers ({len(_t)})")
check({"PALLET_TOWN", "CINNABAR_ISLAND"} <= set(r21.run.floor.exits.values()), "...Pallet Town at the top, Cinnabar at the bottom")

# ---- batch 23: Cinnabar Island, Blaine's quiz Gym, the Pokémon Mansion's switches
_cf = ("cinnabar_gym_gate_1", "mansion_switch", "got_secret_key", "visited_CINNABAR_ISLAND", "visited_POKEMON_MANSION")
_cfs = {k: story.story_flags.pop(k, None) for k in _cf}
ci = open_map("CINNABAR_ISLAND", "KANTO_ROUTE_21")
_ex = set(_tm["CINNABAR_ISLAND"]["exits"].values())
check((ci.w, ci.h) == (24, 20) and {"POKEMON_MANSION", "CINNABAR_VOLCANO"} <= _ex,
      f"Cinnabar: FireRed's island; the Mansion's door, the data's Volcano by the east shore ({sorted(_ex)})")
_pp = {o.get("text"): p for p, o in ci._people().items()}
check(_pp.get("Seagallop to One Island") in (None, (23, 8)), f"...the Seagallop's sailor on the east shore ({_pp})")
_vp = story.inventory.get("VOLCANO_PASS"); story.inventory["VOLCANO_PASS"] = 1
ci.player = (22, 7); ci.facing = (1, 0); ci.anim = 0
walk(ci, "r"); play(lambda: story.current_area_key == "CINNABAR_VOLCANO" or isinstance(g.current_state, _WTS) and g.current_state.anim == 0, 400)
check(story.current_area_key == "CINNABAR_VOLCANO" or type(g.current_state).__name__ == "AreaTransitionState",
      f"...the Volcano's mouth in the east cliff leads into the data's Volcano ({story.current_area_key}, {type(g.current_state).__name__})")
story.inventory.pop("VOLCANO_PASS", None)
if _vp is not None:
    story.inventory["VOLCANO_PASS"] = _vp
ci = open_map("CINNABAR_ISLAND", "KANTO_ROUTE_21")
_pp = _room_of(ci, "gym")
check(_pp.get("Gym") == (5, 4) and sum(1 for n in _pp if n and n.startswith(("Burglar", "Super Nerd"))) == 7,
      "...Blaine's Gym: Blaine where FireRed has him, his seven trainers")
check(len(ci.sign_events) == 12, f"...six quiz machines, both halves of each readable ({len(ci.sign_events)})")
ci.player = (26, 10); ci.facing = (0, -1); ci.anim = 0
walk(ci, "u")
check(tuple(ci.player) == (26, 10), f"...the first gate is shut ({ci.player})")
ci.player = (22, 11); ci.facing = (0, -1); ci.anim = 0
ci._read((22, 10)); frames(2)
_pz = g.current_state
check(type(_pz).__name__ == "GymPuzzleState", f"...read the machine: a math question ({type(_pz).__name__})")
if type(_pz).__name__ == "GymPuzzleState":
    _pz.answer(next(i for i, o in enumerate(_pz.options) if o[1]))
    play(lambda: isinstance(g.current_state, _WTS), 600)
    tap(g.current_state)
ci = g.current_state
frames(25)
check(story.story_flags.get("cinnabar_gym_gate_1") and getattr(ci, "_pic_now", "").endswith("12_0_q1.png"), f"......answered right: the gate's flag is set, the gate drawn open ({getattr(ci, '_pic_now', None)})")
ci.player = (26, 10); ci.facing = (0, -1); ci.anim = 0
walk(ci, "u")
check(tuple(ci.player) == (26, 9), f"......and the first gate is open ({ci.player})")
ma = open_map("POKEMON_MANSION", "CINNABAR_ISLAND")
check(ma.run.n_floors == 4, f"Pokémon Mansion: FireRed's four floors ({ma.run.n_floors})")
_n = []
for _i in range(4):
    _floor(ma, _i)
    _n.append(sum(1 for m in ma.run.floor.movers if m.kind == "trainer"))
check(_n == [2, 1, 1, 2], f"...FireRed's trainers floor by floor ({_n})")
_floor(ma, 2)
check(_figure(ma, "BURGLAR SIMON") == (7, 13), "...3F: the burglar with the Secret Key")
_floor(ma, 0); _quiet(ma)
ma.run.floor.movers = [m for m in ma.run.floor.movers if m.kind != "trainer"]
ma.run.player = (5, 6); ma.facing = (0, -1); ma.anim = 0
_act = ma._act_here()
check(_act and _act[0] == "CHECK", f"...1F's statue: a secret switch ({_act and _act[0]})")
_shut = (22, 12)   # (below 1F's first switch gate: shut till the switch is pressed)
ma.run.player = _shut; ma.anim = 0
ma.step(0, -1); play(lambda: g.current_state._ready(), 300)
_before = tuple(ma.run.player)
ma.run.player = (5, 6); ma.facing = (0, -1); ma.anim = 0
_act[1](); play(lambda: g.current_state._ready(), 300); tap(g.current_state)
ma = g.current_state
check(story.story_flags.get("mansion_switch"), "......pressed: the switch is on")
ma.run.player = _shut; ma.anim = 0
ma.step(0, -1); play(lambda: g.current_state._ready(), 300)
check(_before == _shut and tuple(ma.run.player) == (22, 11), f"......and the gate it held shut swings open ({_before} -> {ma.run.player})")
for _k, _v in _cfs.items():
    story.story_flags.pop(_k, None)
    if _v is not None:
        story.story_flags[_k] = _v

# ---- batch 24: the Seafoam Islands from the file; batch 25: Route 23, Victory Road, Indigo Plateau, the Elite Four's rooms
sf = open_map("SEAFOAM_ISLANDS", "KANTO_ROUTE_20")
check(sf.run.n_floors == 5 and "fr_ground/1_83" in json.dumps(sf.recipe["art"]["floors"][0]), "Seafoam: FireRed's five floors, drawn from the file")
check(sorted(t for t, v in sf.run.floor.decor.items() if str(v).startswith("boulder")) == [(22, 12), (32, 9)], "...1F's two boulders where FireRed has them")
_floor(sf, 3)
check(sorted(t for t, v in sf.run.floor.decor.items() if str(v).startswith("hole")) == [(6, 18), (9, 18)], "...B3F's two holes take its boulders (ours, kept)")
_floor(sf, 4)
check(_figure(sf, "CHALLENGE ARTICUNO") == (9, 2), "...B4F: Articuno where FireRed has it")
r23 = open_map("KANTO_ROUTE_23", "KANTO_ROUTE_22")
_gd = sorted((m.y, m.payload.get("text")) for m in r23.run.floor.movers if m.kind == "figure" and "GUARD" in str(m.payload.get("text")))
check((r23.run.floor.w, r23.run.floor.h) == (24, 160) and len(_gd) == 8, f"Route 23: FireRed's 24 x 160, the eight badge guards ({len(_gd)})")
vr = open_map("VICTORY_ROAD", "KANTO_ROUTE_23")
_n = []
for _i in range(3):
    _floor(vr, _i)
    _n.append(sum(1 for m in vr.run.floor.movers if m.kind == "trainer"))
check(vr.run.n_floors == 3 and _n == [2, 5, 5], f"Victory Road: FireRed's three floors, its trainers on FireRed's spots ({_n})")
# FireRed's floor switches (11-16): a boulder rolled onto each (Strength's puzzle) drops its rock barrier; till then the way
# on is shut, as FireRed's heights keep it
from collections import deque as _dq
from src.states.slide_puzzle import SlidePuzzleState as _SPS
from src.dungeon import art as _vart
_vrf = ["vr_switch_1f", "vr_switch_2f_w", "vr_switch_2f_e", "vr_switch_3f"]
_vsave = {k: story.story_flags.pop(k, None) for k in _vrf + [k for k in story.story_flags if k.startswith("boulder_VICTORY_ROAD")]}
_vhm = story.inventory.get("HM_STRENGTH", 0)
story.inventory["HM_STRENGTH"] = 1
vr = open_map("VICTORY_ROAD", "KANTO_ROUTE_23")


def _vr_reach(i, frm):
    """The ways out reached on foot from beside the way in at frm (the game's own floor, its walls and barriers)."""
    _floor(vr, i)
    f = vr.run.floor
    start = next((frm[0] + dx, frm[1] + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)) if f.walkable(frm[0] + dx, frm[1] + dy))
    seen, q = {start}, _dq([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in seen and f.inside(*n) and (f.walkable(*n) or n in f.exits) and not vr._height_edge((x, y), n):   # (11-23: FireRed's heights - the plateau only by its stairs)
                seen.add(n)
                if n not in f.exits:
                    q.append(n)
    return {t for t in f.exits if t in seen}, seen


def _vr_push(i, t):
    _floor(vr, i)
    _bk = list(story.badges.get("KANTO", []))
    story.badges["KANTO"] = _bk + [b for b in ("RAINBOW",) if b not in _bk]   # (Kanto, 11-16: Strength works with the Rainbow Badge, FireRed's rule)
    vr._boulder(t)
    play(lambda: isinstance(g.current_state, _SPS), 300)
    if isinstance(g.current_state, _SPS):
        g.current_state._finish(True)
    play(lambda: g.current_state is vr and not vr.dialogue_box.visible, 300)
    story.badges["KANTO"] = _bk


_pic = lambda i: _vart._version_file(vr.recipe["art"]["floors"][i]["roofs"]["_picture"])
# (11-23, K3: Victory Road 2F's cliff tops are a walk level of their own, FireRed's heights: no stepping straight up the
#  cliff, but up its stairs at (9,12) and along the top)
_floor(vr, 1)
vr.run.floor.movers = [m for m in vr.run.floor.movers if m.kind not in ("wild", "trainer")]
vr.run.player, vr.anim = (8, 9), 0
vr.step(0, 1); play(lambda: g.current_state is vr and vr._ready(), 200)
_up_cliff = tuple(vr.run.player)
vr.run.player, vr.anim = (9, 13), 0
vr.step(0, -1); play(lambda: g.current_state is vr and vr._ready(), 200)
vr.step(0, -1); play(lambda: g.current_state is vr and vr._ready(), 200)
vr.step(1, 0); play(lambda: g.current_state is vr and vr._ready(), 200)
_on_top = tuple(vr.run.player)
check(_up_cliff == (8, 9) and _on_top == (10, 11) and vr.recipe["art"]["floors"][1].get("heights"),
      f"Victory Road 2F: the cliff top is a level of its own - no stepping up the cliff from below ({_up_cliff}); up the stairs and along the top ({_on_top})")
_ex, _seen = _vr_reach(0, (11, 20))
check((3, 2) not in _ex and str(vr.run.floor.decor.get((12, 14))).startswith("barrier") and _pic(0).endswith("1_39_bar.png")
      and any((7 + dx, 18 + dy) in _seen for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))),
      f"Victory Road 1F: FireRed's rock barrier stands, the stairs out of reach; the switch's boulder within reach ({_pic(0)})")
_vr_push(0, (7, 18))
_ex, _seen = _vr_reach(0, (11, 20))
check(story.story_flags.get("vr_switch_1f") and str(vr.run.floor.decor.get((20, 16))).startswith("pressed") and (3, 2) in _ex
      and _pic(0).endswith("1_39.png"), f"...Strength rolls it onto the switch: the barrier drops (FireRed's floor drawn), the stairs up open ({sorted(_ex)})")
_ex, _ = _vr_reach(1, (1, 9))
check((3, 3) not in _ex, "2F: up from 1F, the west barrier shuts the stairs to 3F")
_vr_push(1, (8, 7))
_ex, _ = _vr_reach(1, (1, 9))
check(story.story_flags.get("vr_switch_2f_w") and (3, 3) in _ex and _pic(1).endswith("1_40_bar_e.png"),
      f"...a boulder on the west switch: that barrier drops, the east one still up ({_pic(1)})")
_ex, _ = _vr_reach(2, (5, 2))
check((34, 18) not in _ex, "3F: its barrier keeps you from the hole back down")
_vr_push(2, (19, 15))
_ex, _ = _vr_reach(2, (5, 2))
check(story.story_flags.get("vr_switch_3f") and (34, 18) in _ex, "...its switch pressed: through to the hole")
_ex, _ = _vr_reach(1, (34, 19))
check((36, 17) not in _ex, "2F again, dropped by the hole: the east barrier shuts the way on")
_vr_push(1, (33, 19))
_ex, _ = _vr_reach(1, (34, 19))
check(story.story_flags.get("vr_switch_2f_e") and (36, 17) in _ex and _pic(1).endswith("1_40.png"), f"...the east switch: both barriers down ({_pic(1)})")
_ex, _ = _vr_reach(2, (39, 17))
_ex2, _ = _vr_reach(1, (38, 9))
check((37, 10) in _ex and any(vr.run.floor.exits[t] == "KANTO_ROUTE_23" for t in _ex2), "...and on through 3F to the way out by the League")
story.inventory["HM_STRENGTH"] = _vhm
for _k, _v in _vsave.items():
    story.story_flags.pop(_k, None)
    if _v is not None:
        story.story_flags[_k] = _v
_lw = {k: story.story_flags.pop(k, None) for k in [f"league_won_INDIGO_PLATEAU_{i}" for i in range(1, 6)]}
ip = open_map("INDIGO_PLATEAU", "KANTO_ROUTE_23")
_pp = _room_of(ip, "lobby")
check(_pp.get("Heal") == (13, 10) and _pp.get("Shop") == (0, 7), f"Indigo Plateau: the League's lobby, the nurse and the clerk across their counters ({_pp})")
_pp = _room_of(ip, "league_lorelei")
check(_pp.get("Lorelei") == (6, 5), "...Lorelei in her own room")
ip.player = (6, 3); ip.facing = (0, -1); ip.anim = 0
walk(ip, "u")
check(ip.room == "league_lorelei" and tuple(ip.player) == (6, 3), f"...her far door stays shut till you've won ({ip.room}, {ip.player})")
story.story_flags["league_won_INDIGO_PLATEAU_1"] = True
frames(25)
check(getattr(ip, "_pic_now", "").endswith("1_75_won.png"), f"......won: FireRed's open door drawn ({getattr(ip, '_pic_now', None)})")
ip.player = (6, 3); ip.facing = (0, -1); ip.anim = 0
walk(ip, "uu")
check(g.current_state.room == "league_bruno", f"......and through it to Bruno's room ({g.current_state.room})")
for _k, _v in _lw.items():
    story.story_flags.pop(_k, None)
    if _v is not None:
        story.story_flags[_k] = _v

def _fight(b, n=8000):
    """Play a turn-based battle as a player would: each turn the first move and the right answer; tap through
    its text. Returns how many math questions were answered."""
    asked = 0
    for _k in range(n):
        if g.current_state is not b:
            break
        if b.phase == "SWITCH_PROMPT" and b.btn_no.visible and b.btn_no.callback:
            b.btn_no.callback()  # ("Change Pokemon?" NO, as a player would)
        elif b.phase == "MENU" and not b.dialogue_box.visible:
            b.open_move_menu()
            b.choose_move(b.move_buttons[0].text.replace(" ", "-"))
            b.math_ui.on_click(b.options.index(b.correct_ans))
            asked += 1
        elif b.dialogue_box.visible:
            b.dialogue_box.is_finished = True
            if b.phase in ("OUTRO", "VICTORY_TEXT", "REWARD_TEXT"):
                b.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            else:
                _cb = b.dialogue_box.callback
                if _cb:
                    b.dialogue_box.callback = None
                    _cb()
                else:
                    b.dialogue_box.advance()
        b.feedback_timer = 0
        if g.current_state is b:
            b.update()
            b.draw()
    return asked


# ---- the Hall of Fame (FireRed 1.80, 11-16): win the title in the Champion's room; Oak walks in and leads you up; your
# team is recorded; then home
_hsave = {k: story.story_flags.get(k) for k in ("gym_progress_INDIGO_PLATEAU", "hall_of_fame_due_INDIGO_PLATEAU", "beat_elite_four", "move_offer_kanto", "beat_champion")}
_hteam = list(story.player_team)
_ace = mk(150); _ace.level = 100; _ace.moves = ["PSYCHIC", "ICE-BEAM"]; _ace.heal_full()
story.player_team = [_ace]
story.story_flags["gym_progress_INDIGO_PLATEAU"] = 4
for _i in range(1, 5):
    story.story_flags[f"league_won_INDIGO_PLATEAU_{_i}"] = True
ip = open_map("INDIGO_PLATEAU", "KANTO_ROUTE_23")
_pp = _room_of(ip, "league_champion")
_champ = next(p for n, p in _pp.items() if n == "{rival_name}" or (n and story.rival_name in n) or p == (6, 8))
check((6, 2) in getattr(ip, "barred", {}) or not ip._open((6, 2)), "Champion's room: the door up to the Hall of Fame is shut before the title")
ip.player = (_champ[0], _champ[1] + 1); ip.facing = (0, -1); ip.anim = 0
said.clear()
ip._talk(_champ)
play(lambda: type(g.current_state).__name__ in ("TrainerBattleState", "TrainerIntroState"), 600)
if type(g.current_state).__name__ == "TrainerIntroState":
    play(lambda: type(g.current_state).__name__ == "TrainerBattleState", 600)
_b = g.current_state
check(type(_b).__name__ == "TrainerBattleState", f"...talk to the Champion: the battle ({type(_b).__name__})")
_fight(_b)
play(lambda: isinstance(g.current_state, _WTS) and g.current_state.room == "hall_of_fame" and not g.current_state._busy(), 3000)
t = g.current_state
check(story.story_flags.get("beat_elite_four") and isinstance(t, _WTS) and t.room == "hall_of_fame"
      and any("this way" in s for s in said), f"...won: Oak walks in and leads you up into the Hall of Fame ({getattr(t, 'room', None)}, {type(t).__name__})")
play(lambda: story.current_area_key == "PALLET_TOWN" and not getattr(g.current_state, "_busy", lambda: True)(), 3000)
check(story.current_area_key == "PALLET_TOWN" and any("entered in the Hall of Fame" in s for s in said)
      and not story.story_flags.get("hall_of_fame_due_INDIGO_PLATEAU"), f"...your team recorded, then home ({story.current_area_key}, {said[-3:]})")
story.player_team = _hteam
for _k, _v in _hsave.items():
    story.story_flags.pop(_k, None)
    if _v is not None:
        story.story_flags[_k] = _v

# ---- Surf and rods (11-16): every Kanto area with water has FireRed's own Surf table and rod tables (its wild headers);
# 11-17: LeafGreen's species beside FireRed's (kwild.py: Slowpoke for Psyduck, Krabby for Horsea, Staryu for Shellder...)
import random as _wr
import src.dungeon.core as _wc
for _wa, _wwant in (("KANTO_ROUTE_21", {72}), ("SEAFOAM_ISLANDS", {86, 116, 87, 54, 55, 98, 79, 80}), ("SAFARI_ZONE", {54, 79})):
    _wp = open_map(_wa, "PALLET_TOWN" if _wa == "KANTO_ROUTE_21" else "KANTO_ROUTE_20" if _wa == "SEAFOAM_ISLANDS" else "FUCHSIA_CITY")
    _wt0, _wc.CURRENT_TILE = _wc.CURRENT_TILE, _wc.SURF
    _got = set()
    for _k in range(40):
        _m = _wp._wild_for_pool(_wr.Random(_k))
        _got.add(int(getattr(_m, "id", _m)) if _m is not None else None)
    _wc.CURRENT_TILE = _wt0
    check(_got and _got <= _wwant, f"{_wa}: out on the water, only FireRed's and LeafGreen's surfing Pokemon ({sorted(map(str, _got))})")
_wp = open_map("KANTO_ROUTE_10", "CERULEAN_CITY")
check(set(_wp._fishing_pool("SUPER_ROD")) == {"116", "98", "130", "54", "79"} and set(_wp._fishing_pool("OLD_ROD")) == {"129"},
      f"Route 10: FireRed's and LeafGreen's rods (Super Rod: Horsea / Krabby, Gyarados, Psyduck / Slowpoke) ({_wp._fishing_pool('SUPER_ROD')})")

# ---- batch 27: the Sevii Islands begin (One Island, Treasure Beach, Kindle Road, Mt. Ember), from FireRed's pictures
oi = open_map("ONE_ISLAND", "KINDLE_ROAD")
check((oi.w, oi.h) == (24, 20) and "fr_ground/3_12" in json.dumps(oi.town_map), "One Island: FireRed's own picture")
_pp = _room_of(oi, "center")
check(_pp.get("Heal") == (6, 2) and (15, 6) in [p for n, p in _pp.items() if n and n.startswith(("Give Celio", "Celio's"))] and _pp.get("Bill") == (14, 6), f"...the Network Center: the nurse across her counter, Celio by his machine ({_pp})")
_pp = _room_of(oi, "harbor")
check(any(p == (8, 6) for p in _pp.values()), f"...the harbour: the Seagallop's sailor on the pier ({_pp})")
kr = open_map("KINDLE_ROAD", "ONE_ISLAND")
check(len(_trainers(kr)) == 12 and _trainers(kr).get("Mik & Kia") == (8, 68), f"Kindle Road: FireRed's twelve trainers on their spots ({len(_trainers(kr))})")
_floor(kr, kr.recipe["art"]["room_floors"]["spa"])
check(_figure(kr, "EMBER SPA") == (15, 11), "...the Ember Spa: the old man by the pool (HM Rock Smash)")
_mef = {k: story.story_flags.pop(k, None) for k in ("met_ember_researchers", "sevii_ember_rocket")}
me = open_map("MT_EMBER", "KINDLE_ROAD")
_rs = _figure(me, "TALK TO THE RESEARCHERS")
story.story_flags["met_ember_researchers"] = True   # (the Rockets stand at the door once you've heard of them)
me = open_map("MT_EMBER", "KINDLE_ROAD")
check(me.run.n_floors == 13 and _rs == (29, 45) and _figure(me, "CHASE OFF TEAM ROCKET") == (42, 40),
      f"Mt. Ember: thirteen maps; the researchers at the foot, the Rockets at the Ruby Path's door ({[(m.payload.get('text'), m.x, m.y) for m in me.run.floor.movers if m.kind == 'figure']})")
for _k, _v in _mef.items():
    story.story_flags.pop(_k, None)
    if _v is not None:
        story.story_flags[_k] = _v
_floor(me, 4)
check(_figure(me, "CHALLENGE MOLTRES") == (9, 6), "...Moltres on the summit, where FireRed has it")

# ---- batch 28: Two Island, Cape Brink, Three Island with its port, Bond Bridge, Berry Forest
ti = open_map("TWO_ISLAND", "CAPE_BRINK")
_pp = {o.get("text"): p for p, o in ti._people().items()}
check((ti.w, ti.h) == (48, 20) and _pp.get("Shop") == (28, 4), f"Two Island: FireRed's picture; the data's shop at the market stall ({_pp.get('Shop')})")
_pp = _room_of(ti, "gamecorner")
check(_pp.get("Joyful Game Corner") == (4, 2) and (5, 5) in _pp.values(), f"...the Joyful Game Corner: its attendant and Lostelle's dad ({_pp})")
_bk = story.story_flags.pop("beat_three_island_bikers", None)
th = open_map("THREE_ISLAND", "BOND_BRIDGE")
_pp = {o.get("text"): p for p, o in th._people().items()}
check((th.w, th.h) == (48, 60) and _pp.get("Stop the Biker Gang") == (8, 24) and sum(1 for n in _pp if n and n.startswith("Biker")) == 8 and _pp.get("Islander") == (7, 24)
      and "THREE_ISLE_PORT" in set(th.town_map["exits"].values()),
      f"Three Island: the town over its port, as the game joins them; the bikers in the road and on the pier; Three Isle Path's mouth ({sum(1 for n in _pp if n and n.startswith('Biker'))})")
story.story_flags["beat_three_island_bikers"] = True
th = open_map("THREE_ISLAND", "BOND_BRIDGE")
check(not any(n and n.startswith("Biker") for n in {o.get("text") for o in th._people().values()}), "...beaten: the bikers are gone")
story.story_flags.pop("beat_three_island_bikers", None)
if _bk is not None:
    story.story_flags["beat_three_island_bikers"] = _bk
bb = open_map("BOND_BRIDGE", "THREE_ISLAND")
check(len(_trainers(bb)) == 6, f"Bond Bridge: FireRed's six trainers ({len(_trainers(bb))})")
_hl = {k: story.story_flags.pop(k, None) for k in ("heard_lostelle", "rescued_lostelle")}
story.story_flags["heard_lostelle"] = True   # (she's there once her dad has told you she's lost)
bf = open_map("BERRY_FOREST", "BOND_BRIDGE")
for _k, _v in _hl.items():
    story.story_flags.pop(_k, None)
    if _v is not None: story.story_flags[_k] = _v
check((bf.run.floor.w, bf.run.floor.h) == (57, 47) and _figure(bf, "FIND LOSTELLE") == (4, 8), "Berry Forest: FireRed's picture; Lostelle where FireRed has her (talk to her: the Hypno)")

# ---- Silph Co. in the Journal (Jordan, 11-14: "very clearly guided"): three steps, the marker floor by floor
_sf = ("silph_co_cleared", "got_card_key", "received_silph_reward", "tower_ghost_defeated", "fuji_rescued")
_sfs = {k: story.story_flags.pop(k, None) for k in _sf}
_ck = story.inventory.pop("CARD_KEY", None)
_tm0 = story.tracked_mission
story.story_flags["tower_ghost_defeated"] = story.story_flags["fuji_rescued"] = True   # (11-17: Silph opens at Mr. Fuji's rescue, and so does its Journal step)
story.current_area_key = "SAFFRON_CITY"
_sb, _tea = list(story.badges.get("KANTO", [])), story.inventory.get("TEA")
story.badges["KANTO"] = ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL"]; story.inventory["TEA"] = 1
_act = {m["id"]: m for m in story.get_all_journal_entries() if m.get("status") == "ACTIVE"}
check("s_silph" in _act and "s_silph2" not in _act and "Card Key" in _act["s_silph"]["desc"] and "5F" in _act["s_silph"]["desc"],
      f"Journal: Silph Co.'s first step, the Card Key on 5F ({[k for k in _act if 'silph' in k]})")
story.tracked_mission = "s_silph"
si = open_map("SILPH_CITY", "SAFFRON_CITY")
_way = []
_up = {1: (30, 3), 2: (28, 3), 3: (30, 3), 4: (28, 3)}   # (in off the stairs from the floor below)
for _i in range(5):
    _floor(si, _i); si._guide_key = None
    if _i in _up:
        si.run.player = _up[_i]
    _way.append(si._guide_spot())
check([w and w[1] for w in _way] == ["To Lift", "To 3F", "To 4F", "To 5F", "Card Key"] and _way[0][0] == (22, 3) and _way[4][0] == (22, 21),   # (11-23: from 1F the lift is the short way up)
      f"...the marker: into 1F's lift (or up the stairs floor by floor), then the Card Key itself ({_way})")
story.inventory["CARD_KEY"] = 1; story.story_flags["got_card_key"] = True
_act = {m["id"]: m for m in story.get_all_journal_entries() if m.get("status") == "ACTIVE"}
check("s_silph2" in _act and "3F" in _act["s_silph2"]["desc"] and "7F" in _act["s_silph2"]["desc"], "...then the next: 3F's door, the pads to 7F and 11F, Giovanni")
story.tracked_mission = "s_silph2"
_way = {}
for _i, _at in ((0, (8, 19)), (2, (28, 3)), (6, (5, 5)), (10, (2, 6))):   # (1F's door; off 3F's stairs; off the pads)
    _floor(si, _i); si._guide_key = None; si._step_key = None
    si.run.player = _at
    _way[_i] = si._guide_spot()
check(_way[0] == ((22, 3), "To Lift") and _way[2] == ((13, 14), "To 7F") and _way[6] == ((5, 8), "To 11F") and _way[10] == ((6, 11), "Giovanni"),
      f"...the marker: 3F's warp pad to 7F, 7F's to 11F, then Giovanni ({_way})")
story.story_flags["silph_co_cleared"] = True
_act = {m["id"]: m for m in story.get_all_journal_entries() if m.get("status") == "ACTIVE"}
check("s_silph3" in _act and "s_silph2" not in _act and "11F" in _act["s_silph3"]["desc"], "...Silph freed: the last step, the President on 11F")
story.tracked_mission = "s_silph3"
si = open_map("SILPH_CITY", "SAFFRON_CITY"); _floor(si, 10); si._guide_key = None; si._step_key = None
check(si._guide_spot() == ((9, 9), "President"), f"...on 11F the marker is on the President ({si._guide_spot()})")
story.tracked_mission = _tm0
story.badges["KANTO"] = _sb
story.inventory.pop("TEA", None)
if _tea is not None:
    story.inventory["TEA"] = _tea
story.inventory.pop("CARD_KEY", None)
if _ck is not None:
    story.inventory["CARD_KEY"] = _ck
for _k, _v in _sfs.items():
    story.story_flags.pop(_k, None)
    if _v is not None:
        story.story_flags[_k] = _v

# ---- the Journal through Kanto's main story (Jordan, 11-14: "ensure the journal nicely guides the player"): at each
# point of FireRed's story, the mission the guide follows and the place it points to
from src.world import guide as _guide
_jf = ("got_ss_ticket_bill", "got_hm_cut_kanto", "game_corner_poster", "game_corner_cleared", "hideout_giovanni_defeated",
       "tower_ghost_defeated", "fuji_rescued", "got_tea", "got_card_key", "silph_co_cleared", "received_silph_reward",
       "visited_CERULEAN_CITY", "visited_VERMILLION_CITY", "visited_LAVENDER_TOWN", "visited_CELADON_CITY", "visited_FUCHSIA_CITY",
       "visited_PEWTER_CITY", "visited_SAFFRON_CITY", "visited_CINNABAR_ISLAND", "got_secret_key", "received_pokedex_kanto", "received_starter_kanto", "viridian_rocket_defeated")
_jfs = {k: story.story_flags.pop(k, None) for k in _jf}
_jinv = {k: story.inventory.pop(k, None) for k in ("SS_TICKET", "HM_CUT", "SILPH_SCOPE", "LIFT_KEY", "POKE_FLUTE", "TEA", "CARD_KEY")}
_jb, _tm0 = list(story.badges.get("KANTO", [])), story.tracked_mission
story.tracked_mission = None
story.current_area_key = "CERULEAN_CITY"
_BADGES = ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH", "VOLCANO", "EARTH"]


def _no_strength():
    """(11-19, ROADMAP_KANTO: at eight badges, a player who skipped Strength - where does the Journal lead?)"""
    saved = {f: story.story_flags.pop(f, None) for f in ("got_hm_strength_kanto", "got_gold_teeth")}
    inv = {i: story.inventory.pop(i, None) for i in ("HM_STRENGTH", "GOLD_TEETH")}
    got = _journal(8)
    for f, v in saved.items():
        if v is not None:
            story.story_flags[f] = v
    for i, v in inv.items():
        if v is not None:
            story.inventory[i] = v
    return got


def _journal(n, flags=(), items=()):
    story.badges["KANTO"] = _BADGES[:n]
    for f in flags:
        story.story_flags[f] = True
    for it in items:
        story.inventory[it] = 1
    m = _guide.tracked_mission(g)
    return (m or {}).get("id"), _guide.mission_target(g, m) if m else None


for _f in ("received_starter_kanto", "received_pokedex_kanto", "viridian_rocket_defeated", "visited_PEWTER_CITY"):
    story.story_flags[_f] = True
_steps = [
    ("Cerulean: over Nugget Bridge to Bill first, as FireRed leads", _journal(1, ["visited_CERULEAN_CITY"]), ("k_bill", "BILLS_HOUSE")),
    ("the ticket, one badge: Misty", _journal(1, ["got_ss_ticket_bill"], ["SS_TICKET"]), "m4"),
    ("Misty beaten, the ticket: south to Vermilion", _journal(2), "m5"),
    ("Vermilion: aboard the S.S. Anne for Cut", _journal(2, ["visited_VERMILLION_CITY"]), ("k_ssanne", "KANTO_SS_ANNE")),
    ("Cut: Lt. Surge", _journal(2, ["got_hm_cut_kanto"], ["HM_CUT"]), "m6"),
    ("three badges: the Rock Tunnel to Lavender", _journal(3), "m7"),
    ("Lavender: the Silph Scope first, in Celadon's hideout", _journal(3, ["visited_LAVENDER_TOWN"]), ("m8", "ROCKET_HIDEOUT")),
    ("Celadon: the Game Corner's poster", _journal(3, ["visited_CELADON_CITY"]), ("k_hideout1", "CELADON_GAME_CORNER")),
    ("the stairs open: down into the hideout", _journal(3, ["game_corner_poster"]), ("k_hideout2", "ROCKET_HIDEOUT")),
    ("the Silph Scope: Erika, while you're in Celadon", _journal(3, ["hideout_giovanni_defeated", "game_corner_cleared"], ["SILPH_SCOPE"]), "m9"),
    ("four badges: up the Pokémon Tower", _journal(4), ("m8", "KANTO_POKEMON_TOWER")),
    ("Mr. Fuji saved: to his house in Lavender", _journal(4, ["tower_ghost_defeated", "fuji_rescued"]), ("m8", "LAVENDER_TOWN")),
    ("the Poké Flute: south to Fuchsia", _journal(4, [], ["POKE_FLUTE"]), "m10"),
    ("Fuchsia: Koga", _journal(4, ["visited_FUCHSIA_CITY"]), "m11"),
    ("five badges: the Safari Zone's Secret House, for Surf (a MAIN step, 11-17)", _journal(5), ("k_surf", "SAFARI_ZONE")),
    ("Surf: the Warden's Gold Teeth, in the Safari Zone", _journal(5, ["got_hm_surf_kanto"], ["HM_SURF"]), ("k_teeth", "SAFARI_ZONE")),
    ("the Gold Teeth: back to the Warden for Strength", _journal(5, ["got_gold_teeth"], ["GOLD_TEETH"]), ("k_teeth", "FUCHSIA_CITY")),
    ("Surf and Strength, no Tea: Celadon Mansion", _journal(5, ["got_hm_strength_kanto"], ["HM_STRENGTH"]), ("k_tea", "CELADON_CITY")),
    ("the Tea: Silph Co.", _journal(5, ["got_tea"], ["TEA"]), ("s_silph", "SILPH_CITY")),
    ("the Card Key: the boardroom", _journal(5, ["got_card_key"], ["CARD_KEY"]), ("s_silph2", "SILPH_CITY")),
    ("Silph freed: the President", _journal(5, ["silph_co_cleared"]), ("s_silph3", "SILPH_CITY")),
    ("the Master Ball: Sabrina", _journal(5, ["received_silph_reward"]), "m12"),
    ("six badges: by sea to Cinnabar", _journal(6), "m13"),
    ("Cinnabar: the Gym's key is in the Mansion", _journal(6, ["visited_CINNABAR_ISLAND"]), ("k_mansion", "POKEMON_MANSION")),
    ("the Secret Key: Blaine's quiz Gym", _journal(6, ["got_secret_key"]), ("m14", "CINNABAR_ISLAND")),
    ("seven badges: Bill's trip to the Sevii Islands first (Jordan 11-17: Sevii's first trip is MAIN, before Giovanni)", _journal(7), ("sevii_m1", "ONE_ISLAND")),
    ("the first Sevii trip done: Viridian's Gym", _journal(7, ["got_tri_pass", "sevii_ember_rocket", "got_ruby_sevii", "celio_has_ruby", "rescued_lostelle"]), ("m15", "VIRIDIAN_CITY")),
    ("eight badges: the League", _journal(8), "m16"),
    ("eight badges but Strength skipped: the Warden's Teeth before Victory Road's boulders (11-19)", _no_strength(), "k_teeth"),
]
for _what, (_id, _to), _want in _steps:
    _ok = _id == _want if isinstance(_want, str) else (_id, _to) == _want
    check(_ok, f"Journal: {_what} ({_id} -> {_to})")
# ---- the marker inside: the S.S. Anne's Captain, the Hideout's Lift Key, the Tower's ghost
for _f in ("visited_LAVENDER_TOWN", "visited_CELADON_CITY", "visited_FUCHSIA_CITY", "visited_CINNABAR_ISLAND", "got_secret_key",
           "game_corner_poster", "game_corner_cleared", "got_hm_cut_kanto"):
    story.story_flags.pop(_f, None)
story.inventory.pop("HM_CUT", None); story.badges["KANTO"] = _BADGES[:2]
check(_journal(2)[0] == "k_ssanne", "...the S.S. Anne's step is the one the Journal shows")
_cut = None
an = open_map("KANTO_SS_ANNE", "VERMILLION_CITY"); an._guide_key = an._step_key = None
_gs = an._guide_spot()
check(_gs is not None and _gs[1].startswith("To "), f"...aboard the S.S. Anne the marker leads toward the Captain ({_gs})")
_floor(an, an.recipe["art"]["room_floors"]["captain"]); an.run.player = (5, 6); an._guide_key = an._step_key = None
check(an._guide_spot() == ((5, 4), "Captain"), f"......and in his cabin, onto him ({an._guide_spot()})")
if _cut is not None:
    story.story_flags["got_hm_cut_kanto"] = _cut
_hf = {}
story.inventory.pop("SILPH_SCOPE", None); story.inventory.pop("POKE_FLUTE", None)
check(_journal(3, ["got_hm_cut_kanto", "visited_LAVENDER_TOWN", "visited_CELADON_CITY", "game_corner_poster"], ["HM_CUT"])[0] == "k_hideout2", "...the hideout's step is the one the Journal shows")
_lk = story.inventory.pop("LIFT_KEY", None)
hq = open_map("ROCKET_HIDEOUT", "CELADON_GAME_CORNER")
_way = []
for _i in range(4):
    _floor(hq, _i); hq._guide_key = hq._step_key = None
    _way.append(hq._guide_spot())
check(all(_way) and _way[3][1] == "Lift Key", f"...in the Rocket Hideout the marker leads floor by floor to the Lift Key ({_way})")
story.inventory["LIFT_KEY"] = 1
_floor(hq, 0); hq._guide_key = hq._step_key = None
_gs = hq._guide_spot()
hq.run.enter_floor(4); hq.run.player = (2, 4); frames(2); hq._guide_key = hq._step_key = None
_gs2 = hq._guide_spot()
check(_gs and _gs[1] == "To Lift" and _gs2 == ((0, 2), "Lift to B4F"), f"......with the Lift Key, into the lift, its panel: down to Giovanni ({_gs}, {_gs2})")
story.inventory.pop("LIFT_KEY", None)
if _lk is not None:
    story.inventory["LIFT_KEY"] = _lk
_ms = story.story_flags.pop("mansion_switch", None)
check(_journal(6, ["visited_CINNABAR_ISLAND"])[0] == "k_mansion", "...on Cinnabar the Mansion's step is the one the Journal shows")
story.story_flags.pop("got_secret_key", None)
ma = open_map("POKEMON_MANSION", "CINNABAR_ISLAND"); ma._guide_key = ma._step_key = None
_g1 = ma._guide_spot()
_floor(ma, 3); ma.run.player = (4, 9); ma._guide_key = ma._step_key = ma._fig_key = None   # (11-17: the Secret Key is FireRed's item ball in the basement; the marker finds it by the mission's flag, over every floor)
_g3 = ma._guide_spot()
check(_g1 is not None and _g3 == ((5, 7), "SECRET KEY"), f"...in the Mansion the marker leads on (1F: {_g1}), and in the basement onto the Secret Key ({_g3})")
story.story_flags.pop("mansion_switch", None)
if _ms is not None:
    story.story_flags["mansion_switch"] = _ms
for _k, _v in _hf.items():
    story.story_flags.pop(_k, None)
    if _v is not None:
        story.story_flags[_k] = _v
story.tracked_mission = _tm0
story.badges["KANTO"] = _jb
story.tracked_mission = _tm0
for _k, _v in _jfs.items():
    story.story_flags.pop(_k, None)
    if _v is not None:
        story.story_flags[_k] = _v
for _k, _v in _jinv.items():
    story.inventory.pop(_k, None)
    if _v is not None:
        story.inventory[_k] = _v


# ---- FireRed's move tutors (Jordan 11-16: "Put in all Kanto move tutors. Have them cost cannon amount"): free; since 11-22 the first lesson unlocks the move for good (TM-seller rule),
# on FireRed's own spots; Copycat's Mimic for a Poke Doll (Celadon 4F sells it), Silph 2F's Thunder Wave, Mt. Ember's Explosion
from src.states.overworld import _run_story_event as _rseT
from src.pokemon import moves as _mvT
_tmT = json.load(open("assets/town_maps.json", encoding="utf-8"))
_saidT = []
_stT = type("S", (), {"game": g, "show_message": lambda self, l, callback=None: (_saidT.extend(l), callback and callback())})()
def _atT(key, part, name):
    m = _tmT[key]
    m = m["rooms"][part] if isinstance(part, str) else m["floors"][part] if isinstance(part, int) else m
    ns = [(x, y) for y, r in enumerate(m["art"]) for x, c in enumerate(r) if c == "N"]
    for xy, p in zip(ns, m.get("people") or []):
        if isinstance(p, dict) and p.get("text") == name:
            return xy, p
    return None, None
def _pick_teach(st):
    """(11-19) A tutor whose move is a TM too asks first: LEARN IT NOW or BUY THE TM - a player picks LEARN IT NOW."""
    for _ in range(80):
        cs = g.current_state
        if type(cs).__name__ == "PickListState" and getattr(cs, "title", "") == "MOVE TUTOR":
            if hasattr(cs.back, "start"):
                cs.pick("teach")
            else:   # (the test's stand-in state: straight to the choice)
                cs.done("teach")
            return True
        if getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            st.update()
        elif getattr(getattr(st, "dialogue_box", None), "visible", False):
            st.dialogue_box.advance()
            st.update()
        else:
            return False
    return False


def _teachT(ev, team, flags=()):
    said = []
    story.player_team = [mk(i) for i in team]
    for f in flags:
        story.story_flags[f] = True
    _rseT(_stT, ev, lambda c: (story.inventory.get(c[9:], 0) > 0) if c.startswith("has_item:") else
          (not story.story_flags.get(c[4:])) if c.startswith("not:") else bool(story.story_flags.get(c)), lambda l, **k: said.extend(l))
    _pick_teach(_stT)
    return said
_savedT, _invT, _teamT, _moneyT = dict(story.story_flags), dict(story.inventory), list(story.player_team), story.money
for key, part, name, xy, move, can in (("KANTO_ROUTE_4", None, "Punching fan", (25, 3), "MEGA-PUNCH", 66),
                                       ("KANTO_ROUTE_4", None, "Kicking fan", (28, 3), "MEGA-KICK", 66),
                                       ("VIRIDIAN_CITY", None, "Sleepy man", (8, 26), "DREAM-EATER", 63),
                                       ("PEWTER_CITY", "museum_1f", "Wrestling fan", (26, 7), "SEISMIC-TOSS", 66),
                                       ("ROCK_TUNNEL", 1, "Tunnel hiker", (2, 29), "ROCK-SLIDE", 74),
                                       ("CELADON_CITY", "dept_3", "Counter man", (10, 9), "COUNTER", 66),
                                       ("CELADON_CITY", None, "Pond man", (26, 19), "SOFT-BOILED", 113),
                                       ("FUCHSIA_CITY", None, "Kangaskhan fan", (15, 11), "SUBSTITUTE", 25),
                                       ("CINNABAR_ISLAND", "lab_rd", "Metronome scientist", (5, 4), "METRONOME", 35),
                                       ("VICTORY_ROAD", 1, "Ace trainer", (40, 9), "DOUBLE-EDGE", 19)):
    at, who = _atT(key, part, name)
    flag = "frlg_tutor_" + move.lower().replace("-", "_")
    story.story_flags.pop(flag, None)
    no = _teachT(who["event"], [129]) if who else []
    burnt = story.story_flags.get(flag)
    yes = _teachT(who["event"], [can]) if who else []
    got = move in _mvT.move_pool(g, story.player_team[0])
    # (taught once: the move is unlocked for good - Jordan 11-22, tutors are TM sellers - so again, to another Pokemon, free)
    for _tryT in range(6):   # (a fresh Pokemon may know the move already - Clefairy and Metronome: nobody to teach; try another)
        story.money = 10000; _saidT.clear()
        _teachT(who["event"], [can]) if who else []
        if move in _mvT.move_pool(g, story.player_team[0]):
            break
    again = (move in _mvT.move_pool(g, story.player_team[0]) and story.money == 10000
             and any("for good" in s for s in _saidT))
    check(at == xy and not burnt and got and story.story_flags.get(flag) and again,
          f"{key} {part or ''}: {name} at FireRed's spot {xy} teaches {move} free, unlocked for good (again free); a Magikarp can't learn it and that doesn't use it up ({at}, {burnt}, {got}, {story.money}, {_saidT[-1:]})")
# Copycat: the Magnet Train Pass first (HGSS), then Mimic for a Poke Doll (FireRed), bought on Celadon 4F for $1000
_, _clk = _atT("CELADON_CITY", "dept_4", "Clerk")
story.money = 1500; story.inventory.pop("POKE_DOLL", None)
_teachT(_clk["event"], [25])
check(story.inventory.get("POKE_DOLL") == 1 and story.money == 500, f"Celadon Dept. Store 4F: a Poke Doll for $1000 ({story.inventory.get('POKE_DOLL')}, {story.money})")
# (11-23, K2: FireRed's walk-in lift in the Dept. Store - in at 3F's lift door, the panel, ride to 5F, out on 5F by its lift door)
_ce = open_map("CELADON_CITY", "KANTO_ROUTE_7")
_ce._go("dept_3", ""); frames(2)
_ce.player = (6, 2); _ce.anim = 0
walk(_ce, "u")
_ce = g.current_state
_inC = (getattr(_ce, "room", None), tuple(_ce.player))
_ce.player = (0, 3); _ce.anim = 0; _ce.facing = (0, -1)
_ce.step(0, -1); play(lambda: type(g.current_state).__name__ == "PickListState", 200)
_pkC = g.current_state if type(g.current_state).__name__ == "PickListState" else None
_rowsC = [c[0] for c in _pkC.choices] if _pkC else []
if _pkC:
    _pkC.pick("dept_5")
play(lambda: isinstance(g.current_state, _WTS) and not g.current_state._busy(), 300)
_ce = g.current_state
_ce.player = (2, 4); _ce.anim = 0
walk(_ce, "d")
_ce = g.current_state
check(_inC[0] == "lift" and _rowsC == ["1F", "2F", "3F", "4F", "5F"] and _ce.room == "dept_5" and tuple(_ce.player) == (6, 2),
      f"...its lift: in at 3F's lift door, the panel lists 1F-5F, the car stops at 5F and you step out by 5F's lift door ({_inC}, {_rowsC}, {_ce.room}, {_ce.player})")
_cc = next(o for o in _area["SAFFRON_CITY"]["explore_options"] if o.get("text") == "Visit Copycat")
story.story_flags.pop("frlg_tutor_mimic", None)
_w = _teachT(_cc["event"], [129], flags=["got_magnet_pass"])
check(story.inventory.get("POKE_DOLL") == 1 and not story.story_flags.get("frlg_tutor_mimic"), f"...Copycat keeps your doll for later when nobody can learn Mimic ({_w[:1]})")
_w = _teachT(_cc["event"], [35])
check("MIMIC" in _mvT.move_pool(g, story.player_team[0]) and not story.inventory.get("POKE_DOLL") and story.story_flags.get("frlg_tutor_mimic"),
      f"...and teaches a Clefairy Mimic for it ({_w[:2]})")
story.money = 5000; _saidT.clear()
_w = _teachT(_cc["event"], [35])
check("MIMIC" in _mvT.move_pool(g, story.player_team[0]) and story.money == 5000 and any("for good" in s for s in _saidT),
      f"...and again later, no doll needed, free: Mimic is unlocked for good ({story.money}, {_saidT[-1:]})")
# Silph Co. 2F: Thunder Wave (once she's given the Up-Grade hint, when there's one to give)
_se = next(o for o in _area["SILPH_CITY"]["route_menu"] if o.get("text") == "TALK TO EMPLOYEE")
story.story_flags.pop("frlg_tutor_thunder_wave", None)
for _try in range(8):   # (a new Clefairy sometimes already has Thunder Wave in its moves: then there is nobody to teach; try another)
    _w = _teachT(_se["event"], [35], flags=["silph_upgrade_hint"])
    if story.story_flags.get("frlg_tutor_thunder_wave"):
        break
check("THUNDER-WAVE" in _mvT.move_pool(g, story.player_team[0]) and story.story_flags.get("frlg_tutor_thunder_wave"), f"Silph Co. 2F: the employee teaches Thunder Wave ({_w[:1]})")
# Mt. Ember: the researchers, then Explosion
_me = next(o for o in g.loader.area_data["STORY_PROGRESSION"]["MT_EMBER"]["route_menu"] if o.get("text") == "TALK TO THE RESEARCHERS")
story.story_flags.pop("frlg_tutor_explosion", None)
_w = _teachT(_me["event"], [74], flags=["met_ember_researchers"])
check("EXPLOSION" in _mvT.move_pool(g, story.player_team[0]) and story.story_flags.get("frlg_tutor_explosion"), f"Mt. Ember: the researcher teaches Explosion ({_w[:1]})")
story.story_flags.clear(); story.story_flags.update(_savedT)
story.inventory.clear(); story.inventory.update(_invT)
story.player_team, story.money = _teamT, _moneyT

# ---- Kanto check fixes: canon content (11-17): FireRed's Gym trainers, levels, trades, hidden items, wild tables
from src.states.overworld import _run_story_event as _rseC


def _roomC(key, room):
    r = _tm[key]["rooms"][room] if room else _tm[key]
    spots = [(x, y) for y, row in enumerate(r["art"]) for x, c in enumerate(row) if c == "N"]
    out = {}
    for at, p in zip(spots, r.get("people") or []):
        for q in (p if isinstance(p, list) else [p]):
            out[q if isinstance(q, str) else q.get("text")] = (at, q)
    return r, out


_r, _pp = _roomC("VIRIDIAN_CITY", "gym")
_vg = {"Black Belt Takashi": ((10, 2), [38, 38, 38]), "Cooltrainer Yuji": ((12, 10), [38] * 5), "Black Belt Atsushi": ((11, 14), [40, 40]), "Tamer Jason": ((10, 10), [43]),
       "Tamer Cole": ((2, 21), [39, 39]), "Black Belt Kiyo": ((3, 11), [43]), "Cooltrainer Samuel": ((6, 8), [37, 37, 38, 39, 39]), "Cooltrainer Warren": ((13, 7), [37, 37, 38, 39, 39])}
check(all(n in _pp and _pp[n][0] == at and _pp[n][1]["event"]["battle"]["levels"] == lv for n, (at, lv) in _vg.items()),
      f"Viridian Gym: FireRed's eight trainers on FireRed's tiles with FireRed's levels ({sorted(n for n in _vg if n not in _pp)})")
check([t["name"] for t in _area["VIRIDIAN_CITY"]["gym"]["trainers"]] == [_pp[n][1]["event"]["battle"]["name"] for n in sorted(_vg, key=lambda n: int(_pp[n][1]["event"]["flag"].rsplit("_", 1)[1]))],
      "...each one's flag number is his place in the data's gym.trainers")
check(_r.get("hidden") == {"2,2": "MACHO_BRACE"} and _tm["SAFFRON_CITY"]["rooms"]["copycat_2"].get("hidden") == {"2,1": "NUGGET"}
      and _tm["VERMILLION_CITY"]["rooms"]["harbor"].get("hidden") == {"58,28": "LAVA_COOKIE"},
      "FireRed's hidden Macho Brace (Viridian Gym), Nugget (Copycat's room) and Lava Cookie (Vermilion's dock)")
for _k, _room, _want in (("VERMILLION_CITY", "gym", {"Engineer Baily": [21, 21], "Sailor Dwayne": [21, 21], "Gentleman Tucker": [23]}),
                         ("CELADON_CITY", "gym", {"Lass Kay": [23, 23], "Beauty Bridget": [21] * 4, "Picnicker Tina": [24, 24], "Beauty Tamia": [24, 24], "Beauty Lori": [24], "Lass Lisa": [23, 23], "Cooltrainer Mary": [22] * 5}),
                         ("SAFFRON_CITY", "dojo", {"Black Belt Hitoshi": [31] * 3, "Black Belt Hideki": [32, 32], "Black Belt Aaron": [36], "Black Belt Mike": [31] * 3})):
    _r, _pp = _roomC(_k, _room)
    _dt = {t["name"]: t for t in (_area[_k]["gym"]["trainers"] if _room == "gym" else _area[_k]["dojo_trainers"])}
    check(all(n in _pp and _pp[n][1]["event"]["battle"]["levels"] == lv and _dt[n]["levels"] == lv and _dt[n]["team"] == _pp[n][1]["event"]["battle"]["team"] for n, lv in _want.items()),
          f"{_k} {_room}: every trainer standing there has FireRed's team and levels, the same in the data ({len(_want)})")
# the six trades FireRed has that ours lacked: the person stands on FireRed's tile and trades
_savedC, _teamC, _hereC = dict(story.story_flags), list(story.player_team), story.current_area_key
for _k, _room, _who, _at, _want, _give, _where in (("KANTO_ROUTE_2", "house", "TRADER", (7, 2), 63, 122, "route_menu"), ("VERMILLION_CITY", "house_n", "Trader", (4, 4), 21, 83, "explore_options"),
                                                  ("UNDERGROUND_PATH", None, "Trader", (5, 6), 32, 29, "explore_options"), ("CINNABAR_ISLAND", "lab_meet", "Old Trader", (4, 6), 26, 101, "explore_options"),
                                                  ("CINNABAR_ISLAND", "lab_meet", "Lab Trader", (10, 5), 48, 114, "explore_options"), ("CINNABAR_ISLAND", "lab_test", "Young Trader", (11, 8), 77, 86, "explore_options")):
    _r, _pp = _roomC(_k, _room)
    _o = next(o for o in _area[_k][_where] if o.get("text") == _who)
    _said = []
    story.story_flags.pop(_o["event"]["flag"], None)
    story.player_team = [Pokemon(g.loader.fetch_specific(_want), g.assets, size_mult=2.5)]
    story.player_team[0].level = 20
    story.current_area_key = _k
    _rseC(g.current_state, _o["event"], lambda c: story.special_condition(c) if story.special_condition(c) is not None else bool(story.story_flags.get(c)), _said.append)
    _got = story.player_team[0]
    check(_who in _pp and _pp[_who][0] == _at and _got.id == _give and _got.level == 20 and story.story_flags.get(_o["event"]["flag"]),
          f"{_k}: FireRed's trade on FireRed's tile {_at}: a #{_want} for the #{_give} ({_got.id}, {_said[-1][-1:] if _said else None})")
    if _give == 29:
        check(getattr(_got, "held_item", None) == "TINY_MUSHROOM", "...the Nidoran comes holding a TinyMushroom (FireRed)")
    if _give == 83:   # (11-17, Jordan: the Stick is in; the Bag holds its copy, as for every held item)
        check(getattr(_got, "held_item", None) == "STICK" and story.inventory.get("STICK") == 1, f"...the Farfetch'd comes holding the Stick (FireRed) ({getattr(_got, 'held_item', None)}, in the Bag: {story.inventory.get('STICK')})")
        story.inventory.pop("STICK", None)
    _said.clear()
    _rseC(g.current_state, _o["event"], lambda c: True, _said.append)
    check(story.player_team[0].id == _give and len(story.player_team) == 1 and bool(_said), f"...asked again, the trader only asks after it ({_said[-1] if _said else None})")
story.story_flags.clear(); story.story_flags.update(_savedC)
story.player_team, story.current_area_key = _teamC, _hereC
# wild tables: FireRed's and LeafGreen's species together, no others but the dex extras kept (kwild_extra.json)
_wd = g.loader.area_data
check(set(_wd["KANTO_ROUTE_8_PERCENTAGES"]) >= {"16", "52", "23", "27", "58", "37"} and "122" not in _wd["KANTO_ROUTE_2_PERCENTAGES"]
      and set(_wd["VIRIDIAN_FOREST_PERCENTAGES"]) == {"10", "13", "14", "11", "25"} and set(_wd["KANTO_POKEMON_TOWER_PERCENTAGES"]) >= {"92", "93", "104"}
      and "41" not in _wd["KANTO_POKEMON_TOWER_PERCENTAGES"], "wild tables: FireRed's and LeafGreen's species together (Route 8, Viridian Forest, the Tower), none of our old extras")
_off = [k for k in _wd if k.endswith("_PERCENTAGES") and isinstance(_wd[k], dict) and "TREE" not in k and not k.startswith(("KANTO_ROUTE_26", "KANTO_ROUTE_27", "KANTO_ROUTE_28"))
        and k.startswith(("KANTO_ROUTE_", "SAFARI", "SEAFOAM", "MT_MOON", "ROCK_TUNNEL", "VICTORY", "CERULEAN_CAVE", "POKEMON_MANSION", "VIRIDIAN_FOREST", "DIGGLETT", "POWER_PLANT")) and sum(_wd[k].values()) != 100]
check(not _off, f"...every rebuilt table adds up to 100 ({_off})")
_seaC = ("PALLET_TOWN", "VIRIDIAN_CITY", "CERULEAN_CITY", "VERMILLION_CITY", "CELADON_CITY", "FUCHSIA_CITY", "CINNABAR_ISLAND")
check("120" not in _wd["KANTO_ROUTE_19_SUPER_ROD_PERCENTAGES"] and sum(_wd["KANTO_ROUTE_19_SUPER_ROD_PERCENTAGES"].values()) == 100
      and all("120" in _wd[f"{k}_SUPER_ROD_PERCENTAGES"] and _area[k].get("can_fish") for k in ("PALLET_TOWN", "VERMILLION_CITY", "CINNABAR_ISLAND")),
      "no dex extra is left (11-17): Staryu is where LeafGreen has it, on the Super Rod at Pallet, Vermilion and Cinnabar (towns you can fish in), not on Route 19")
check(all(_area[k].get("can_fish") and all(f"{k}_{r}_ROD_PERCENTAGES" in _wd for r in ("OLD", "GOOD", "SUPER")) for k in _seaC),
      "the seven water towns can be fished in (can_fish, with their three rod tables)")
check(all(_area[k].get("can_fish") and any(o.get("action") == "FISH" for o in _area[k]["route_menu"]) for k in ("KANTO_ROUTE_4", "KANTO_ROUTE_6", "KANTO_ROUTE_22", "CERULEAN_CAVE", "SEAFOAM_ISLANDS")),
      "Routes 4, 6 and 22, Cerulean Cave and the Seafoam Islands can be fished in (FireRed has rod tables there)")
check(all(f"{k}_SURF_PERCENTAGES" in _wd for k in ("PALLET_TOWN", "VIRIDIAN_CITY", "CERULEAN_CITY", "VERMILLION_CITY", "CELADON_CITY", "FUCHSIA_CITY", "CINNABAR_ISLAND", "KANTO_ROUTE_4"))
      and _area["KANTO_ROUTE_4"].get("surf_pool_percentages") == "KANTO_ROUTE_4_SURF_PERCENTAGES" and "KANTO_ROUTE_4_SUPER_ROD_PERCENTAGES" in _wd,
      "the seven water towns and Route 4 have a Surf table of their own (and Route 4 its rods)")

# ---- Kanto follow-up decisions (11-17, Jordan; kanto_handoff/kanto_check/DECISIONS.md "Follow-up answers")
_spF = {t["name"]: t for t in _area["SILPH_CITY"]["trainer_pool"]}
_wantF = {"Admin Proton": ([42, 89, 110], [30] * 3), "Archer": ([110, 24, 131], [31] * 3), "Executive Ariana": ([45, 91, 24, 53], [33] * 4)}
check(all(_spF[n]["team"] == tm and _spF[n].get("levels") == lv for n, (tm, lv) in _wantF.items()),
      f"Silph Co.'s story trainers have fixed levels: Proton 3 x 30, Archer 3 x 31, Ariana 4 x 33, their species kept ({ {n: _spF[n].get('levels') for n in _wantF} })")
check(not [k for k, a in _area.items() if isinstance(a, dict) and any(t.get("name") == "Alpesh" for t in a.get("trainer_pool") or [])] and "Alpesh" not in json.dumps(_tm["KANTO_ROUTE_7"]),
      "Alpesh is gone from Route 7 (the data and the map)")
# the Stick: Farfetch'd's own held item, two critical-hit stages (the games' rule); the Lucky Egg: half again the XP
import random as _rndF
from src.pokemon import items as _itF
_bF = battle("VERMILLION_CITY", 83, 19)
_pF, _fF = _bF.player_pokemon, _bF.opponent_pokemon
_realF = _rndF.random


def _critF(mon, item):
    mon.held_item = item
    _rndF.random = lambda: 0.3   # (between a plain hit's 1 in 24 and two stages' 1 in 2)
    try:
        _bF._calculate_damage(mon, _fF, 40, 1.0)
    finally:
        _rndF.random = _realF
    return _bF._last_was_crit


check(_bF.held_crit(_pF) == 0 and not _critF(_pF, None) and _critF(_pF, "STICK") and _bF.held_crit(_pF) == 2,
      "the Stick: Farfetch'd holding it lands critical hits two stages more often (1 in 2, not 1 in 24)")
_rtF = mk(19)
_bF.player_pokemon = _rtF
check(not _critF(_rtF, "STICK") and _bF.held_crit(_rtF) == 0, "...and it does nothing for any other Pokemon (a Rattata)")
_bF.player_pokemon = _pF
check(_itF.holdable("STICK") and _itF.holdable("LUCKY_EGG") and "Farfetch'd" in _itF.describe("STICK") and "XP" in _itF.describe("LUCKY_EGG"),
      "the Stick and the Lucky Egg can be held, and the Bag says what each does")


def _xpF(item):
    b = battle("VERMILLION_CITY", 83, 20)
    b.player_pokemon.level, b.opponent_pokemon.level = 10, 40
    b.player_pokemon.held_item = item
    lines = b._award_battle_xp()
    return next((int(w) for l in lines if " gained " in l and " XP" in l for w in l.replace("!", "").split() if w.isdigit()), 0)


_plainF, _eggF = _xpF(None), _xpF("LUCKY_EGG")
check(_plainF > 20 and abs(_eggF - _plainF * 1.5) <= 1, f"the Lucky Egg: its holder earns half again the XP from a battle ({_plainF} -> {_eggF})")
_o15 = next((o for o in _area["KANTO_ROUTE_15"]["route_menu"] if o.get("text") == "OAK'S AIDE"), {})
check(_o15.get("door") == "gate_2" and _o15.get("event", {}).get("requires") == ["caught_kanto:50"] and _o15["event"].get("gift_item") == {"LUCKY_EGG": 1}
      and _tm["KANTO_ROUTE_15"]["rooms"]["gate_2"]["people"] == ["OAK'S AIDE"],
      "Route 15's aide (the gatehouse's upstairs, FireRed's spot) gives a Lucky Egg for fifty kinds caught (played in kanto_gates)")
check(_tm["VIRIDIAN_CITY"]["rooms"]["gym"].get("hidden_when") == {"2,2": ["has_badge:EARTH"]}, "Viridian Gym's hidden Macho Brace waits for the Earth Badge (played in kanto_gates)")
story.current_area_key = "PALLET_TOWN"


print(f"##### {len(fails)} failures")
for m in fails:
    print("   FAIL " + m)
