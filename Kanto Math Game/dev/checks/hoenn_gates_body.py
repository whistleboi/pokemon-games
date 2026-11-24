# Hoenn's story gates, both sides (Hoenn re-audit H5, 11-23; kanto_handoff/SWEEP_RULES.md Part 3 item 12). The gate list is
# kanto_handoff/hoenn_rom_tools/hoenn_gates.json (62 gates in Omega Ruby / Alpha Sapphire's order, Emerald's own scripts
# beside each); the findings are in kanto_handoff/hoenn_check/GATES.md. Here each gate is met on our walked maps the way a
# player meets it: BEFORE (the story just short of it: you must not get past) and AFTER (what opens it given: you must get
# past). A FAIL is a finding about the game, not something to patch here: GATES.md "Suite run" lists them.
#     bash dev/checks/run_par.sh hoenn_gates
# Jordan's 11-23 decisions (kanto_handoff/hoenn_check/DECISIONS.md #3-#14) are tested as the NEW behaviour: HMs from ORAS's
# givers needing ORAS's badge on the map, the S.S. Tidal after the Champion, New Mauville after Wattson asks, the Devon Scope
# only from Steven, the Eon Flute after the Cave of Origin, the hideout after the sub theft, Briney after the Letter, the Fiery
# Path open, Route 124 -> 126 by Surf, and the Delta Episode as a chain (#13). Gates where ours stays different on purpose
# say "deviation kept".
# Method, printed with each line: "steps" = real steps into the blocker on the walked map; "event" = the story event played
# (its option pressed, its lines tapped through) and the flag it sets read back; "menu" = the game's own test of a map option
# (what the menu or the person shows); "data" = read from the area data.
import json
import os as _os
from collections import deque
from src.states.overworld import PlayState, CityState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.states.overworld.dungeon import DungeonState
from src.states.menus import StarterSelectionState as _SSS
from src.states.battle import TrainerIntroState, TrainerBattleState
from src.dungeon import core as _core
from src.world import hms as _hms

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True
g.rival_character = g.rival_character or "brendan"
story.story_flags["hoenn_version"] = "OMEGA_RUBY"
story.starting_region = "HOENN"
_tm = json.load(open("assets/town_maps.json", encoding="utf-8"))
_area = g.loader.area_data["STORY_PROGRESSION"]
said = []   # (every line the game showed, in order)


def _note(st):
    box = getattr(st, "npc_dialogue", None) if getattr(st, "npc_active", False) else getattr(st, "dialogue_box", None)
    if box is not None and getattr(box, "visible", True):
        for line in getattr(box, "text_lines", []) or []:
            if not said or said[-1] != line:
                said.append(line)


def _toast(st):
    for k in ("toast", "flash_text", "_flash", "message"):
        v = getattr(st, k, None)
        if isinstance(v, str) and v:
            return v
        if isinstance(v, (list, tuple)) and v and isinstance(v[0], str):
            return v[0]
    return ""


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


def play(until, n=1500):
    """Run the game, tapping through whatever is said, till until() (or n frames). True if until() came true."""
    for _ in range(n):
        if until():
            return True
        st = g.current_state
        if getattr(st, "npc_active", False):
            _note(st)
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False) and not _is_battle(st):
            _note(st)
            st.dialogue_box.advance()
        st.update(); st.draw()
    return until()


def _is_battle(st):
    return isinstance(st, (TrainerIntroState, TrainerBattleState, WildBattleState)) or "Battle" in type(st).__name__ or type(st).__name__ in ("BossIntroState", "LegendIntroState")


def _is_map(st):
    return isinstance(st, (_WTS, DungeonState))


def _settled():
    st = g.current_state
    if _is_battle(st):
        return True
    if isinstance(st, _WTS):
        return not st._busy() and st.anim == 0 and not getattr(st, "npc_active", False)
    if isinstance(st, DungeonState):
        return st._ready() and not st.dialogue_box.visible
    return False


def settle(n=700):
    play(_settled, n)
    return g.current_state


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


def _calm(st):
    if isinstance(st, DungeonState):
        st.run.floor.movers = [m for m in st.run.floor.movers if m.kind != "wild"]
        st.encounter_free = 999


def where():
    st = g.current_state
    if isinstance(st, _WTS):
        return (story.current_area_key, st.room, tuple(st.player))
    if isinstance(st, DungeonState):
        return (story.current_area_key, st.run.index, tuple(st.run.player))
    return (story.current_area_key, type(st).__name__, None)


_D = {"u": (0, -1), "d": (0, 1), "l": (-1, 0), "r": (1, 0)}

# ---------------------------------------------------------------------------------------------- the story in order (OUR flags)
BADGES = ["STONE", "KNUCKLE", "DYNAMO", "HEAT", "BALANCE", "FEATHER", "MIND", "RAIN"]
# (name, flags set, items given ("-X" takes one away), Hoenn badges held after it)
STEPS = [
    ("starter", ["received_starter_hoenn", "hoenn_birch_rescued", "hoenn_birch_walked_up", "hoenn_birch_thanked"], [], 0),
    ("rival103", ["hoenn_rival_103", "received_pokedex_hoenn", "hoenn_mom_sendoff", "hoenn_rival_101_tips", "got_dexnav_hoenn",
                  "oldale_free_potions", "hoenn_rival_102_beautifly"], [], 0),
    ("wally", ["helped_wally", "petalburg_center_tour"], [], 0),
    ("woods", ["petalburg_woods_grunt", "woods_boss_defeated", "woods_researcher_left", "route104_grunt_report", "rustboro_rival_mart"], [], 0),
    ("stone", ["badge_stone_earned"], [], 1),
    ("cut", ["got_cut_hoenn"], ["HM_CUT"], 1),
    ("rusturf", ["rusturf_grunt_met", "rusturf_rescued", "rusturf_briney_thanks"], [], 1),
    ("letter", ["met_mr_stone", "rustboro_researcher_thanks"], ["POKE_NAV", "LETTER", "DEVON_PARTS"], 1),
    ("knuckle", ["badge_knuckle_earned", "slateport_grunt_defeated"], [], 2),
    ("steven", ["met_steven"], ["-LETTER"], 2),
    ("dock", ["slateport_saw_dock"], [], 2),
    ("museum", ["oceanic_museum_cleared", "contest_pass_received", "slateport_lisia_met"], ["-DEVON_PARTS"], 2),
    ("rival110", ["defeated_rival_110"], [], 2),
    ("bike", [], ["BICYCLE"], 2),
    ("wallyb", ["defeated_wally_mauville"], ["HM_ROCK_SMASH"], 2),
    ("dynamo", ["badge_dynamo_earned"], [], 3),
    ("strength", ["got_strength_hoenn"], ["HM_STRENGTH"], 3),
    ("cozmo", ["heard_cozmo", "route113_rival_rest"], [], 3),
    ("meteor", ["meteor_falls_cleared"], [], 3),
    ("chimney", ["mt_chimney_boss_defeated"], [], 3),
    ("heat", ["badge_heat_earned"], ["GO_GOGGLES"], 4),
    ("balance", ["badge_balance_earned"], [], 5),
    ("surf", ["got_surf_hoenn"], ["HM_SURF"], 5),
    ("bracelet", ["got_mega_bracelet"], ["MEGA_BRACELET"], 5),
    ("weather", ["weather_institute_cleared"], [], 5),
    ("rival119", ["hoenn_rival_119"], ["HM_FLY"], 5),
    ("scope", ["got_starter_mega_stone"], ["DEVON_SCOPE"], 5),
    ("feather", ["badge_feather_earned"], [], 6),
    ("pyre", ["route121_grunts_ran", "mt_pyre_cleared", "got_mt_pyre_orb"], ["MAGMA_EMBLEM"], 6),
    ("sub", ["slateport_sub_stolen"], [], 6),
    ("lilyrival", ["hoenn_rival_lilycove"], [], 6),
    ("hideout", ["aqua_hideout_cleared"], [], 6),
    ("mind", ["badge_mind_earned"], [], 7),
    ("dive", ["got_dive_hoenn"], ["HM_DIVE"], 7),
    ("seafloor", ["seafloor_cavern_cleared", "seafloor_awakening_seen"], [], 7),
    ("wallace", ["sootopolis_wallace_met"], [], 7),
    ("origin", ["cave_of_origin_cleared"], [], 7),
    ("flute", ["got_eon_flute_hoenn"], ["EON_FLUTE"], 7),
    ("rain", ["badge_rain_earned"], ["HM_WATERFALL"], 8),
    ("wattson", ["wattson_new_mauville_asked"], [], 8),
    ("wallyvr", ["defeated_wally_victory"], [], 8),
    ("league", [f"league_won_EVER_GRANDE_CITY_{i}" for i in range(1, 5)], [], 8),
    ("champion", ["beat_hoenn_champion", "beat_hoenn_elite_four", "league_won_EVER_GRANDE_CITY_5", "move_offer_hoenn"], [], 8),
    ("delta_mom", ["delta_started"], [], 8),
    ("delta_petalburg", ["delta_courtney_petalburg", "delta_matt_petalburg"], [], 8),
    ("delta_zinnia", ["delta_zinnia_granite"], [], 8),
    ("delta_devon", ["h4_rustboro_city_delta_grunt_1", "h4_rustboro_city_delta_grunt_2", "h4_rustboro_city_delta_grunt_3"], [], 8),
    ("delta_mossdeep", ["delta_courtney_mossdeep", "delta_matt_mossdeep"], [], 8),
    ("delta_wallace", ["delta_wallace_131"], [], 8),
]
_NAMES = [s[0] for s in STEPS]
_ALL_FLAGS = {f for s in STEPS for f in s[1]}
_ALL_ITEMS = {i.lstrip("-") for s in STEPS for i in s[2]} | {"EON_TICKET", "HM_FLASH", "SS_TICKET"}
for _f in _ALL_FLAGS:
    story.story_flags.pop(_f, None)
for _i in _ALL_ITEMS:
    story.inventory.pop(_i, None)
story.repel_routes = 0
from src.world import vs_seeker as _vs
story.inventory[_vs.ITEM] = 1   # (the VS Seeker's own arrival gift would otherwise speak first, the first time a check talks to someone)
_BASE = (dict(story.story_flags), dict(story.inventory), {k: set(v) for k, v in story.defeated_trainers.items()},
         list(story.player_team), {r: list(b) for r, b in story.badges.items()})


def beat(area):
    """Every trainer of an area beaten (what winning its battles leaves behind: the boss off its spot)."""
    story.defeated_trainers[area] = set(range(len(_area[area].get("trainer_pool") or [])))


def at(step, also=False, flags=(), items=(), badges=None, drop=()):
    """A clean save at just BEFORE step (also=True: just after it): the opening's state restored, then the story up to there.
    flags / items on top; drop takes flags or items away; badges: how many Hoenn badges (else the story's own count)."""
    story.story_flags.clear(); story.story_flags.update(_BASE[0])
    story.inventory.clear(); story.inventory.update(_BASE[1])
    story.defeated_trainers.clear(); story.defeated_trainers.update({k: set(v) for k, v in _BASE[2].items()})
    story.player_team = list(_BASE[3])
    story.badges.clear(); story.badges.update({r: list(b) for r, b in _BASE[4].items()})
    n = _NAMES.index(step) + (1 if also else 0)
    nb = 0
    for name, fl, it, b in STEPS[:n]:
        for f in fl:
            story.story_flags[f] = True
        for i in it:
            if i.startswith("-"):
                story.inventory.pop(i[1:], None)
            else:
                story.inventory[i] = 1
        nb = b
    story.story_flags["hoenn_version"] = "OMEGA_RUBY"
    for f in flags:
        story.story_flags[f] = True
    for i in items:
        story.inventory[i] = 1
    for d_ in drop:
        story.story_flags.pop(d_, None); story.inventory.pop(d_, None)
    story.badges["HOENN"] = BADGES[:nb if badges is None else badges]
    story.repel_routes = 9999   # (no wild Pokemon in the town grass while stepping about)
    story.current_area_key = "LITTLEROOT_TOWN"
    said.clear()


# ---------------------------------------------------------------------------------------------- walking helpers
def town(key, came, pos=None, room=None):
    v = open_map(key, came)
    v = settle()
    if isinstance(v, _WTS):
        v.scenes.entered = True
        if room:
            _ex = list((_tm[key]["rooms"][room].get("exits") or {}).values())   # (out to the town, or the stairs from the floor below)
            v._go(room, next((x for x in _ex if str(x).startswith("OUT:")), _ex[0] if _ex else "")); frames(2)
        if pos:
            v.player = tuple(pos); v.anim = 0; v.anim_from = v.partner = v.partner_from = tuple(pos)
    return v


def route(key, came, floor=0, pos=None):
    r = open_map(key, came)
    r = settle()
    if isinstance(r, DungeonState):
        if floor and r.run.index != floor:
            r.run.jump_floor(floor, pos or tuple(r.run.player)); frames(2)
        _calm(r)
        if pos:
            r.run.player = tuple(pos); r.anim = 0; r.anim_from = r.partner = r.partner_from = tuple(pos)
    return r


def _town_beside(v, tile, avoid=()):
    for c, (dx, dy) in _D.items():
        n = (tile[0] - dx, tile[1] - dy)
        if n not in avoid and n not in v.exits and n not in v.doors and v._open(n):
            return n, c
    return None, None


def _floor_open(f, q, avoid=()):
    return f.inside(*q) and f.walkable(*q) and q not in f.exits and f.mover_at(*q) is None and q not in avoid


def _floor_beside(r, tile, avoid=()):
    f = r.run.floor
    for c, (dx, dy) in _D.items():
        n = (tile[0] - dx, tile[1] - dy)
        if _floor_open(f, n, avoid):
            return n, c
    return None, None


def stand(st, at_):
    if isinstance(st, _WTS):
        st.player = tuple(at_); st.anim = 0; st.anim_from = st.partner = st.partner_from = tuple(at_)
    else:
        st.run.player = tuple(at_); st.anim = 0; st.anim_from = st.partner = st.partner_from = tuple(at_)


def go(path):
    """Real steps on whatever map is up, each finished (talk tapped through, a change of map waited for) before the next."""
    for c in path:
        st = settle()
        if not _is_map(st):
            break
        frames(2)
        st = settle()
        if not _is_map(st):
            break
        st.step(*_D[c])
        frames(1)
    settle(); frames(4)
    return settle()


def _floors_with(r, target):
    m = _tm[r.area_key] if r.area_key in _tm else {}
    fl = m.get("floors") or [m]
    out = []
    for i, f in enumerate(fl):
        if target in (f.get("exits") or {}).values():
            out.append(i)
    return out or [r.run.index]


def take_exit(key, came, target, floor=None, prefer=None):
    """Open key (in from came), stand beside a way out to target and step on to it, as a player walks out. Returns
    (out?, the tile stepped from, what was said)."""
    st = open_map(key, came)
    st = settle()
    said.clear()
    if isinstance(st, _WTS):
        st.scenes.entered = True
        tiles = sorted(t for t, x in st.exits.items() if x == target)
        if prefer:
            tiles.sort(key=lambda t: abs(t[0] - prefer[0]) + abs(t[1] - prefer[1]))
        for t in tiles:
            n, c = _town_beside(st, t)
            if n:
                stand(st, n)
                go(c)
                out = play(lambda: story.current_area_key == target, 300)
                return out, n, list(said)
        return False, None, [f"(no open tile beside the way out to {target}: {tiles[:3]})"]
    if isinstance(st, DungeonState):
        for i in ([floor] if floor is not None else _floors_with(st, target)):
            if st.run.index != i:
                st.run.jump_floor(i, tuple(st.run.player)); frames(2)
            _calm(st)
            f = st.run.floor
            tiles = sorted(t for t, x in f.exits.items() if x == target)
            if prefer:
                tiles.sort(key=lambda t: abs(t[0] - prefer[0]) + abs(t[1] - prefer[1]))
            for t in tiles:
                n, c = _floor_beside(st, t)
                if n:
                    stand(st, n)
                    go(c)
                    out = play(lambda: story.current_area_key == target, 300)
                    return out, n, list(said)
        return False, None, [f"(no open tile beside the way out to {target})"]
    return False, None, [f"(the map did not open: {type(st).__name__})"]


def bump(st, tile, from_=None):
    """Stand beside tile (or at from_) and step into it. Returns (moved onto it?, from where, said)."""
    said.clear()
    tile = tuple(tile)
    if from_ is None:
        n, c = (_town_beside(st, tile) if isinstance(st, _WTS) else _floor_beside(st, tile))
    else:
        n = tuple(from_); c = next(k for k, d in _D.items() if (n[0] + d[0], n[1] + d[1]) == tile)
    if not n:
        return None, None, ["(nowhere to stand beside it)"]
    stand(st, n)
    _room0 = getattr(st, "room", None)
    st.step(*_D[c]); frames(2)
    now = where()
    moved = now[2] == tile or now[0] != story.current_area_key or (isinstance(st, _WTS) and now[1] != _room0)
    play(lambda: _settled(), 300)
    t_ = _toast(g.current_state)
    return moved, n, list(said) + ([t_] if t_ else [])


def press(st, at_, face):
    """Stand at a spot facing a person or sign and press A (towns)."""
    stand(st, at_); st.facing = face
    said.clear()
    st.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode="", scancode=0)])
    play(lambda: _settled() or not _is_map(g.current_state), 600)
    return list(said)


def find_opt(key, text, lst=None, pred=None):
    a = _area[key]
    for l in ([lst] if lst else ["explore_options", "travel_options", "route_menu"]):
        for o in a.get(l) or []:
            if isinstance(o, dict) and (o.get("text") == text) and (pred is None or pred(o)):
                return o
    return None


def town_shown(v, opt):
    return bool(opt) and v._shown(opt)


def route_ok(r, opt):
    if not opt:
        return False
    if opt.get("flag_condition"):
        p = opt["flag_condition"].split()
        if len(p) == 2 and story.story_flags.get(p[1]):
            return False
        if len(p) == 1 and not story.story_flags.get(p[0]):
            return False
    pool = r.area_data.get("trainer_pool", [])
    left = any(not story.is_trainer_defeated(r.area_key, i) for i in range(len(pool)))   # (as the route's own menu counts them)
    return r._check_route_condition(opt.get("condition"), left, opt)


def press_option(st, opt):
    """Press a map option (the person, or the route's menu button) and play what it does."""
    said.clear()
    if isinstance(st, _WTS):
        cb = st._get_callback_for_option(opt)
    else:
        cb = st._get_route_callback(opt)
    if cb:
        cb()
    play(lambda: _settled() or not _is_map(g.current_state), 900)
    s = g.current_state
    if _is_battle(s):
        _win(s)
    return list(said)


def _win(b, won=True):
    """A battle the check stands in for: past the trainer's opening words, won (its victory flag set, its rewards), then
    back to the map."""
    try:
        for _ in range(3):
            if isinstance(b, TrainerIntroState) and getattr(b, "next_state", None) is not None:
                b = b.next_state
                g.change_state(b); frames(1)
        b = g.current_state if _is_battle(g.current_state) else b
        b.player_won = won
        if hasattr(b, "exit_battle"):
            b.exit_battle()
    except Exception as ex:
        print(f"      (battle end: {type(ex).__name__}: {ex})")
    play(lambda: not _is_battle(g.current_state), 300)
    settle(300)


def unbattle():
    s = g.current_state
    if isinstance(s, WildBattleState) and hasattr(s, "on_flee_complete"):
        s.on_flee_complete(); frames(3); settle()


def trainers_out(key, came, pred, floor=None):
    """The trainers standing on the walked map now (opened as a player arrives), whose name passes pred."""
    st = open_map(key, came); st = settle()
    if not isinstance(st, DungeonState):
        return None
    out = []
    m = _tm.get(key) or {}
    n = len(m.get("floors") or [m])
    for i in ([floor] if floor is not None else range(n)):
        try:
            if st.run.index != i:
                st.run.jump_floor(i, tuple(st.run.player)); frames(1)
        except Exception:
            continue
        for mv in st.run.floor.movers:
            if mv.kind == "trainer":
                p = mv.payload if isinstance(mv.payload, dict) else (mv.payload[1] if isinstance(mv.payload, (tuple, list)) and len(mv.payload) > 1 and isinstance(mv.payload[1], dict) else {})
                nm = str(p.get("spot_name") or p.get("name") or p.get("text") or "")
                if pred(nm, p):
                    out.append((i, nm))
    return out


RESULTS = []   # (gate id, side, ok, method)


def side(gid, which, ok, what, method="steps"):
    RESULTS.append((gid, which, bool(ok), method))
    check(ok, f"[{gid}] {which} ({method}): {what}")


def note(gid, text):
    RESULTS.append((gid, "not verified", None, "none"))
    print(f"   --   [{gid}] not verified: {text}")


def title(gid, text):
    print(f"\n{gid}: {text}")


def guarded(gid, fn):
    try:
        fn()
    except Exception as ex:   # (a gate the check could not even set up: a finding of its own, the rest still run)
        import traceback
        tb = traceback.extract_tb(ex.__traceback__)
        side(gid, "setup", False, f"the check could not run this gate: {type(ex).__name__}: {ex} @ line {tb[-1].lineno} ({tb[-1].name})")
    finally:
        settle(50)


def pick(st, word):
    """A menu of choices is up (a boat's destinations, a person's several things): press the one whose words hold word."""
    for b in list(getattr(st, "hover_buttons", []) or []):
        if word.lower() in str(getattr(b, "text", "")).lower():
            cb = getattr(b, "callback", None)
            st.clear_hover_menu()
            if cb:
                cb()
            return True
    return False


def menu_words(st):
    return [str(getattr(b, "text", "")) for b in (getattr(st, "hover_buttons", []) or [])]


def _texts(o):
    if isinstance(o, dict) and "any" in o:
        return [x.get("text") for x in o["any"] if isinstance(x, dict)]
    return [o.get("text")] if isinstance(o, dict) else [o]


def person(v, text):
    """Where someone stands in the town or room you're in (by the words on them)."""
    for t, o in v.people.items():
        if text in _texts(o):
            mo = getattr(v, "motions", {}).get(t)
            return mo.pos if mo is not None else t
    return None


def talk(v, text, choose=None):
    """Walk up beside them (an open tile next to them) and press A, facing them; choose: then pick that from their menu."""
    t = person(v, text)
    if t is None:
        return None
    getattr(v, "motions", {}).pop(tuple(t), None)
    for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)):
        b = (t[0] + dx, t[1] + dy)
        if v._open(b) and b not in v._people() and b not in v.exits and b not in v.doors:
            out = press(v, b, (-dx, -dy))
            if choose and getattr(g.current_state, "hover_menu_active", False):
                said.clear()
                ok = pick(g.current_state, choose)
                play(lambda: _settled() or not _is_map(g.current_state), 900)
                out = (out or []) + list(said) + ([] if ok else [f"(no '{choose}' in the menu: {menu_words(g.current_state)})"])
            s = g.current_state
            if _is_battle(s):
                _win(s)
            return out
    return ["(nowhere to stand beside them)"]


def figure(r, pred):
    """A person on the route's floor whose words pass pred (each floor looked at in turn)."""
    m = _tm.get(r.area_key) or {}
    for i in range(len(m.get("floors") or [m])):
        if r.run.index != i:
            r.run.jump_floor(i, tuple(r.run.player)); frames(1)
        for mv in r.run.floor.movers:
            if mv.kind == "figure" and isinstance(mv.payload, dict) and pred(str(mv.payload.get("text", ""))):
                return i, mv
    return None, None


def use_figure(r, mv):
    said.clear()
    for c, (dx, dy) in _D.items():
        n = (mv.x - dx, mv.y - dy)
        if _floor_open(r.run.floor, n):
            stand(r, n); r.facing = (dx, dy)
            break
    r._use_figure(mv)
    play(lambda: _settled() or not _is_map(g.current_state), 900)
    s = g.current_state
    if _is_battle(s):
        _win(s)
    return list(said)


def scene_flag(key, came, flag, at_=None, step=None, n=1500):
    """Arrive (or step into a scene's zone) and let the town or route play what it plays; True if flag is now set."""
    st = open_map(key, came)
    if at_ is not None:
        stand(st, at_)
        if isinstance(st, _WTS):
            st.scenes.entered = True
    if step:
        _calm(st)
        st.step(*_D[step])
    for _ in range(n):
        s = g.current_state
        if _is_battle(s):
            _win(s)
            continue
        if story.story_flags.get(flag):
            break
        if getattr(s, "npc_active", False):
            _note(s); s.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(s, "dialogue_box", None) is not None and getattr(s.dialogue_box, "visible", False):
            _note(s); s.dialogue_box.advance()
        s.update(); s.draw()
    return bool(story.story_flags.get(flag))


def gym_door(key, came, room="gym"):
    """Into the Gym (its door walked through) and up to its Leader: what the Gym says."""
    v = town(key, came)
    door = next((t for t, k in v.doors.items() if k == room), None)
    if door is None:
        return None, ["(no Gym door)"], v
    stand(v, (door[0], door[1] + 1)); said.clear()
    v.step(0, -1); frames(3); settle()
    inside = getattr(g.current_state, "room", None)
    v = g.current_state
    said.clear()
    closed = v.gym_closed() if hasattr(v, "gym_closed") else "?"
    return inside, closed, v


# =================================================================================================== the gates, in ORAS order
def g01():
    gid = "littleroot_route101_birch"
    title(gid, "Route 101: Birch chased by a Poochyena; you can't go on till you pick a starter from his bag (Emerald: var 0x4060, flag 0x860)")
    at("starter")
    team = list(story.player_team); story.player_team = []
    story.current_area_key, story.last_area_key = "HOENN_ROUTE_101", "LITTLEROOT_TOWN"
    p = PlayState(g); g.states["play"] = p; g.change_state(p); frames(2)
    bars = {t: b.get("look") for t, b in getattr(p, "_bars", {}).items()}
    shut = [t for t in ((9, 13), (10, 13), (7, 14)) if not p.run.floor.walkable(*t)]
    side(gid, "before", len(shut) == 3 and {(9, 13), (10, 13), (7, 14)} <= set(bars),
         f"no Pokemon yet: Birch, the Poochyena and the bag stand on Emerald's tiles and can't be walked through (shut: {shut})")
    got = False
    for _ in range(600):
        s = g.current_state
        if isinstance(s, _SSS):
            s.load_starters(); s.selected_idx = 0; s.complete_selection(); got = True
            break
        if getattr(s, "dialogue_box", None) is not None and s.dialogue_box.visible:
            s.dialogue_box.advance()
        s.update(); s.draw()
    play(lambda: _is_battle(g.current_state), 600)
    if _is_battle(g.current_state):
        _win(g.current_state)
    play(lambda: story.story_flags.get("hoenn_birch_walked_up") and story.current_area_key == "LITTLEROOT_TOWN", 900)
    side(gid, "event", got and story.story_flags.get("received_starter_hoenn") and story.story_flags.get("hoenn_birch_walked_up"),
         f"the scene plays: pick a starter from the bag, beat the Poochyena, Birch walks up (starter: {got}, flags: received_starter_hoenn "
         f"{story.story_flags.get('received_starter_hoenn')}, hoenn_birch_walked_up {story.story_flags.get('hoenn_birch_walked_up')}; now {where()})", "event")
    story.player_team = team or [mk(258)]
    at("starter", also=True)
    r = route("HOENN_ROUTE_101", "LITTLEROOT_TOWN")
    f = r.run.floor
    free = [t for t in ((9, 13), (10, 13), (7, 14)) if f.walkable(*t) or str(f.decor.get(t, "")).startswith("ledge:")]
    moved, n, s_ = bump(r, (7, 14))
    side(gid, "after", len(free) == 3 and moved, f"with a starter (Birch rescued): the three tiles are clear (9,13 and 10,13 are Emerald's ledges again) ({free}) and you walk on to the bag's spot 7,14 from {n}")


def g02():
    gid = "oldale_sketch_artist"
    title(gid, "Oldale's west road (Route 102): the boy sketching footprints sends you back till Birch gives the Pokedex (Emerald: trigger 0,10, var 0x4051)")
    at("rival103", drop=["received_pokedex_hoenn"])
    v = town("OLDALE_TOWN", "HOENN_ROUTE_101", (2, 10))
    v.step(-1, 0)
    for _ in range(400):
        if v.npc_active:
            break
        frames(1)
    talked = v.npc_active
    tap(v); frames(150); settle()
    side(gid, "before", talked and story.current_area_key == "OLDALE_TOWN" and tuple(v.player) == (2, 10),
         f"no Pokedex: the boy walks up, talks and steps you back to {tuple(v.player)}, still in Oldale {said[:1]}")
    at("rival103", also=True)
    out, n, s_ = take_exit("OLDALE_TOWN", "HOENN_ROUTE_101", "HOENN_ROUTE_102")
    side(gid, "after", out, f"with the Pokedex: west out of Oldale on to Route 102 (from {n}: {where()})")


def g03():
    gid = "route103_rival"
    title(gid, "Route 103: your rival battles you; Birch then hands over the Pokedex")
    at("rival103")
    p = open_map("HOENN_ROUTE_103", "OLDALE_TOWN")
    _calm(p)
    stand(p, (10, 8))
    hit = play(lambda: _is_battle(g.current_state), 400)
    side(gid, "before", hit and isinstance(g.current_state, (TrainerIntroState, TrainerBattleState)),
         f"the rival walks up to battle as you come near ({type(g.current_state).__name__})")
    if _is_battle(g.current_state):
        _win(g.current_state)
    side(gid, "event", story.story_flags.get("hoenn_rival_103"), f"...and winning sets hoenn_rival_103 ({story.story_flags.get('hoenn_rival_103')})", "event")
    at("rival103", also=True)
    p = open_map("HOENN_ROUTE_103", "OLDALE_TOWN")
    _calm(p); stand(p, (10, 8))
    hit = play(lambda: _is_battle(g.current_state), 300)
    side(gid, "after", not hit, f"rival beaten: no battle on Route 103 again ({type(g.current_state).__name__})")


def g04():
    gid = "route103_east_water"
    title(gid, "Route 103's east water (to Route 110): Surf, used with the Balance Badge (ORAS's rule, hms.USE_BADGE)")
    at("dynamo", also=True)
    out, n, s_ = take_exit("HOENN_ROUTE_103", "OLDALE_TOWN", "HOENN_ROUTE_110")
    side(gid, "before", not out, f"no HM Surf: not out east to Route 110 (from {n}: {where()}) {s_[-1:]}")
    at("surf", also=True)
    out, n, s_ = take_exit("HOENN_ROUTE_103", "OLDALE_TOWN", "HOENN_ROUTE_110")
    side(gid, "after", out, f"HM Surf and the Balance Badge: out east to Route 110 (from {n}: {where()})")


def g05():
    gid = "petalburg_gym_four_badges"
    title(gid, "Petalburg Gym: Norman battles you only with four other badges")
    at("heat", badges=3)
    inside, closed, v = gym_door("PETALBURG_CITY", "HOENN_ROUTE_102")
    side(gid, "before", inside == "gym" and bool(closed), f"three badges: you walk into the Gym ({inside}), and Norman's Gym says: {str(closed)[:90]}")
    at("heat", also=True)
    inside, closed, v = gym_door("PETALBURG_CITY", "HOENN_ROUTE_102")
    side(gid, "after", inside == "gym" and not closed, f"four badges: the Gym is open to you ({inside}, closed: {closed})")


def g06():
    gid = "petalburg_woods_trees"
    title(gid, "Petalburg Woods' small trees (19,10 / 19,11): HM Cut from Rustboro's Cutter, used with the Stone Badge")
    for which, setup, want in (("before", lambda: at("stone", also=True), False),
                               ("old save", lambda: at("cut", also=True, badges=0), False),
                               ("after", lambda: at("cut", also=True), True)):
        setup()
        r = route("HOENN_PETALBURG_WOODS", "HOENN_ROUTE_104")
        moved, n, s_ = bump(r, (19, 10), from_=(18, 10))
        what = {"before": "no HM Cut", "old save": "a save holding HM Cut but no Stone Badge (ORAS: Cut can't be used yet)",
                "after": "HM Cut and the Stone Badge"}[which]
        side(gid, which, moved == want, f"{what}: stepping from 18,10 into the tree at 19,10 {'cuts it and walks on' if moved else 'is stopped'} ({where()}) {s_[-1:]}")


def g07():
    gid = "rustboro_devon_chase"
    title(gid, "Rustboro: a Grunt runs off with Devon's parts as you come out with the Stone Badge")
    at("stone")
    ok = scene_flag("RUSTBORO_CITY", "HOENN_ROUTE_104", "rustboro_devon_chase", n=500)
    side(gid, "before", not ok, f"no Stone Badge: the chase doesn't play (rustboro_devon_chase: {ok})", "event")
    at("stone", also=True)
    ok = scene_flag("RUSTBORO_CITY", "HOENN_ROUTE_104", "rustboro_devon_chase")
    side(gid, "after", ok, f"with the Stone Badge: the Grunt and the researcher run past (rustboro_devon_chase: {ok}) {said[:1]}", "event")


def g08():
    gid = "rusturf_thief"
    title(gid, "Rusturf Tunnel: the thief has Peeko; Peeko stands in the way (14,4) till he's beaten")
    at("rusturf", flags=["rusturf_grunt_met"])
    r = route("HOENN_RUSTURF_TUNNEL", "HOENN_ROUTE_116")
    moved, n, s_ = bump(r, (14, 4), from_=(13, 4))
    side(gid, "before", not moved, f"thief not beaten: Peeko blocks 14,4 (from {n}: {where()}) {s_[-1:]}")
    at("rusturf", also=True)
    r = route("HOENN_RUSTURF_TUNNEL", "HOENN_ROUTE_116")
    moved, n, s_ = bump(r, (14, 4), from_=(13, 4))
    side(gid, "after", moved, f"thief beaten (rusturf_rescued): through 14,4 ({where()})")


def g09():
    gid = "devon_letter"
    title(gid, "Devon 3F: Mr. Stone gives the PokeNav, the Letter for Steven and the parts for Stern, once the parts are back")
    at("letter", drop=["rusturf_rescued"])
    v = town("RUSTBORO_CITY", "HOENN_ROUTE_104", room="devon_3")
    s_ = talk(v, "Mr. Stone", choose="Devon")
    side(gid, "before", not story.inventory.get("LETTER"), f"parts not back: no Letter from Mr. Stone (Letter: {story.inventory.get('LETTER', 0)}) {(s_ or [])[:1]}", "event")
    at("letter")
    v = town("RUSTBORO_CITY", "HOENN_ROUTE_104", room="devon_3")
    s_ = talk(v, "Mr. Stone", choose="Devon")
    side(gid, "after", story.inventory.get("LETTER") and story.inventory.get("DEVON_PARTS") and story.story_flags.get("met_mr_stone"),
         f"parts back: Mr. Stone gives the Letter ({story.inventory.get('LETTER', 0)}), the Devon Parts ({story.inventory.get('DEVON_PARTS', 0)}), "
         f"met_mr_stone {story.story_flags.get('met_mr_stone')} {(s_ or [])[-1:]}", "event")


def g10():
    gid = "briney_boat_dewford"
    title(gid, "Route 104: Mr. Briney sails you to Dewford once you have Mr. Stone's Letter")
    at("letter")
    out, n, s_ = take_exit("HOENN_ROUTE_104", "RUSTBORO_CITY", "DEWFORD_TOWN")
    side(gid, "before", not out, f"Stone Badge, no Letter: Briney won't sail (from {n}: {where()}) {s_[-1:]}")
    at("letter", also=True)
    out, n, s_ = take_exit("HOENN_ROUTE_104", "RUSTBORO_CITY", "DEWFORD_TOWN")
    side(gid, "after", out, f"with the Letter: across to Dewford ({where()})")


def g11():
    gid = "granite_cave_dark"
    title(gid, "Granite Cave's dark floors (optional in both games): Flash from the Hiker on 1F only (DECISIONS #7)")
    side(gid, "no badge Flash", _hms.hm_for_badge("HOENN", "KNUCKLE") is None and not _hms.USE_BADGE["HOENN"].get("HM_FLASH"),
         f"the Knuckle Badge hands out no Flash, and Flash needs no badge (ORAS: TM70) ({_hms.hm_for_badge('HOENN', 'KNUCKLE')})", "data")
    at("knuckle", also=True)
    r = route("HOENN_GRANITE_CAVE", "HOENN_ROUTE_106")
    fl, mv = figure(r, lambda t: t == "Hiker")
    s_ = use_figure(r, mv) if mv else ["(no Hiker on the map)"]
    side(gid, "giver", story.inventory.get("HM_FLASH", 0) == 1, f"the Hiker on floor {fl} gives HM Flash ({story.inventory.get('HM_FLASH', 0)}) {s_[-1:]}", "event")


def g12():
    gid = "steven_letter"
    title(gid, "Granite Cave: Steven takes the Letter in the deepest room; the way he stands (12,12 on 1F) is shut till then")
    at("steven")
    r = route("HOENN_GRANITE_CAVE", "HOENN_ROUTE_106", floor=1)
    moved, n, s_ = bump(r, (12, 12))
    side(gid, "before", not moved, f"Letter not delivered: 12,12 on 1F stays shut (from {n}: {where()})")
    r = route("HOENN_GRANITE_CAVE", "HOENN_ROUTE_106")
    fl, mv = figure(r, lambda t: "STEVEN" in t.upper())
    s_ = use_figure(r, mv) if mv else ["(no Steven on the map)"]
    side(gid, "event", story.story_flags.get("met_steven") and not story.inventory.get("LETTER"),
         f"talk to Steven (floor {fl}): he takes the Letter (met_steven {story.story_flags.get('met_steven')}, Letter left {story.inventory.get('LETTER', 0)}) {s_[:1]}", "event")
    at("steven", also=True)
    r = route("HOENN_GRANITE_CAVE", "HOENN_ROUTE_106", floor=1)
    moved, n, s_ = bump(r, (12, 12))
    side(gid, "after", moved, f"Letter delivered: through 12,12 ({where()})")


def _boat(key, came, to, word, pos, room=None):
    """Talk to the one who sails (standing below them), pick where to, and see if you arrive there."""
    v = town(key, came, room=room)
    said.clear()
    stand(v, (pos[0], pos[1] + 1)); v.facing = (0, -1)
    v.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode="", scancode=0)])
    frames(3)
    words = menu_words(g.current_state)
    if getattr(g.current_state, "hover_menu_active", False):
        pick(g.current_state, word)
    out = play(lambda: story.current_area_key == to, 600)
    return out, words, list(said)


def g13():
    gid = "briney_boat_slateport"
    title(gid, "Dewford: Mr. Briney sails on to Slateport once the Letter is delivered (ORAS / Emerald: no Knuckle Badge; DECISIONS #14)")
    at("steven", badges=2)
    out, words, s_ = _boat("DEWFORD_TOWN", "HOENN_ROUTE_106", "SLATEPORT_CITY", "Slateport", (12, 9))
    side(gid, "before", not out, f"Letter not delivered: no sailing to Slateport ({where()}; Briney offers {words}) {s_[-1:]}")
    at("steven", also=True, badges=1)
    out, words, s_ = _boat("DEWFORD_TOWN", "HOENN_ROUTE_106", "SLATEPORT_CITY", "Slateport", (12, 9))
    side(gid, "after", out, f"Letter delivered, no Knuckle Badge yet: Briney sails to Slateport ({where()}; offered {words})")


def flood_town(v, start, goals):
    """Can you walk from start to any goal tile over the town's own open test (people, barred tiles and trees count)?"""
    goals = {tuple(t) for t in goals}
    seen, q = {tuple(start)}, deque([tuple(start)])
    while q:
        x, y = q.popleft()
        if (x, y) in goals:
            return True
        for dx, dy in _D.values():
            n = (x + dx, y + dy)
            if n not in seen and (v._open(n) or n in goals):
                seen.add(n)
                if n in goals:
                    return True
                if n not in v.exits and n not in v.doors:
                    q.append(n)
    return False


def room_step(v, target):
    """In a room: step on to its way out to target (another room, "ROOM:x"); True if you're in that room now."""
    tiles = sorted(t for t, x in v.exits.items() if x == target)
    for t in tiles:
        n, c = _town_beside(v, t)
        if n:
            stand(v, n); said.clear()
            go(c)
            want = target[5:] if target.startswith("ROOM:") else target
            return getattr(g.current_state, "room", None) == want, n, list(said)
    return False, None, [f"(no open tile beside {tiles[:2]})"]


def g14():
    gid = "slateport_museum_line"
    title(gid, "Slateport: Grunts queue outside the Oceanic Museum till you've seen Stern's Shipyard (Dock says Stern is at the Museum)")
    for which, also in (("before", False), ("after", True)):
        at("dock", also=also)
        v = town("SLATEPORT_CITY", "HOENN_ROUTE_109", (16, 28))   # (the square west of the Museum, by the Market)
        door = next((t for t, k in v.doors.items() if k == "museum"), None)
        can = door is not None and flood_town(v, (16, 28), [door])
        went = False
        if door is not None and v._open((door[0], door[1] + 1)):
            stand(v, (door[0], door[1] + 1)); said.clear()
            go("u"); went = play(lambda: story.current_area_key == "HOENN_OCEANIC_MUSEUM" or getattr(g.current_state, "room", None) == "museum", 300)
        side(gid, which, (can and went) == also,
             f"{'saw the Shipyard' if also else 'Shipyard not seen'}: from the square (16,28) the Museum's door {door} {'can' if can else 'cannot'} be walked to past the Grunts' queue; "
             f"stepping in from below it: {'inside' if went else 'not inside'} ({where()}) {said[-1:]}")


def g15():
    gid = "museum_stern"
    title(gid, "Oceanic Museum 2F: two Grunts with Stern; beat them, then Stern takes the Devon Parts")
    at("museum")
    t = trainers_out("HOENN_OCEANIC_MUSEUM", "SLATEPORT_CITY", lambda n, p: True)
    side(gid, "before", t, f"Museum not cleared: the team's Grunts stand in the Museum ({t})")
    vic = [x.get("victory_flag") for x in _area["HOENN_OCEANIC_MUSEUM"].get("trainer_pool", [])]
    side(gid, "opener", "oceanic_museum_cleared" in vic or any("oceanic_museum_cleared" in json.dumps(x) for x in _area["HOENN_OCEANIC_MUSEUM"].get("route_menu", [])),
         f"beating them is what sets oceanic_museum_cleared (the trainers' victory flags: {vic})", "data")


def g16():
    gid = "slateport_north_lisia"
    title(gid, "Slateport's north road (Route 110): open once the Devon Parts are delivered at the Museum (ORAS's order)")
    at("museum")
    out, n, s_ = take_exit("SLATEPORT_CITY", "HOENN_ROUTE_109", "HOENN_ROUTE_110")
    side(gid, "before", not out, f"Museum not cleared: not out north (from {n}: {where()}) {s_[-1:]}")
    at("museum", also=True)
    out, n, s_ = take_exit("SLATEPORT_CITY", "HOENN_ROUTE_109", "HOENN_ROUTE_110")
    side(gid, "after", out, f"Museum cleared: north on to Route 110 ({where()})")


def g17():
    gid = "cycling_road_bike"
    title(gid, "Route 110's Cycling Road gatehouses (15,17 / 16,89): only with a Bike from Rydel in Mauville")
    for which, also in (("before", False), ("after", True)):
        at("bike", also=also)
        for tile in ((15, 17), (16, 89)):
            r = route("HOENN_ROUTE_110", "SLATEPORT_CITY")
            moved, n, s_ = bump(r, tile)
            side(gid, which, moved == also, f"{'with the Bicycle' if also else 'no Bicycle'}: into the gate at {tile} from {n}: {'through' if moved else 'stopped'} {s_[-1:]}")
    at("bike")
    v = town("MAUVILLE_CITY", "HOENN_ROUTE_110", room="bike_shop")
    s_ = talk(v, "Bike Shop", choose="Bike") or []
    if not story.inventory.get("BICYCLE") and getattr(g.current_state, "hover_menu_active", False):
        pick(g.current_state, "Mach") or pick(g.current_state, "Acro") or pick(g.current_state, "Bike"); play(lambda: _settled(), 600)
    side(gid, "giver", story.inventory.get("BICYCLE", 0) >= 1 or story.inventory.get("MACH_BIKE", 0) >= 1 or story.inventory.get("ACRO_BIKE", 0) >= 1,
         f"Rydel's Bike Shop in Mauville hands over a Bike (Bicycle: {story.inventory.get('BICYCLE', 0)}) {s_[-1:]}", "event")


def g18():
    gid = "mauville_wally"
    title(gid, "Mauville: Wally battles you outside the Gym; win and his uncle gives HM Rock Smash; the Gym waits for it")
    at("wallyb")
    open_map("MAUVILLE_CITY", "HOENN_ROUTE_110")
    hit = play(lambda: _is_battle(g.current_state), 600)
    side(gid, "before", hit, f"Wally not beaten: he steps up to battle as you arrive ({type(g.current_state).__name__})", "event")
    if hit:
        _win(g.current_state)
    side(gid, "event", story.story_flags.get("defeated_wally_mauville") and story.inventory.get("HM_ROCK_SMASH", 0) == 1,
         f"...win: defeated_wally_mauville {story.story_flags.get('defeated_wally_mauville')}, HM Rock Smash in the Bag {story.inventory.get('HM_ROCK_SMASH', 0)}", "event")
    req = ((_area["MAUVILLE_CITY"].get("gym") or {}).get("requirements") or {}).get("flags") or []
    side(gid, "gym", "defeated_wally_mauville" in req, f"Wattson's Gym wants Wally beaten ({req})", "data")
    at("wallyb", also=True)
    v = town("MAUVILLE_CITY", "HOENN_ROUTE_110")
    side(gid, "after", (9, 6) not in v.barred and not _is_battle(g.current_state), f"Wally beaten: no battle again, the Gym door clear (barred 9,6: {(9, 6) in v.barred})")


def g19():
    gid = "rock_smash_route111"
    title(gid, "Mauville north to Route 111, and Route 111's cracked rocks: HM Rock Smash used with the Dynamo Badge (ORAS)")
    for which, setup, want, what in (("before", lambda: at("wallyb"), False, "no HM Rock Smash"),
                                     ("old save", lambda: at("wallyb", also=True), False, "HM Rock Smash but no Dynamo Badge"),
                                     ("after", lambda: at("dynamo", also=True), True, "HM Rock Smash and the Dynamo Badge")):
        setup()
        out, n, s_ = take_exit("MAUVILLE_CITY", "HOENN_ROUTE_110", "HOENN_ROUTE_111")
        side(gid, which, out == want, f"{what}: Mauville's north road {'opens' if out else 'stays shut'} (from {n}: {where()}) {s_[-1:]}")
    for which, setup, want, what in (("old save: rock", lambda: at("wallyb", also=True), False, "HM Rock Smash, no Dynamo Badge"),
                                     ("after: rock", lambda: at("dynamo", also=True), True, "HM Rock Smash and the Dynamo Badge")):
        setup()
        r = route("HOENN_ROUTE_111", "MAUVILLE_CITY")
        rocks = sorted(t for t, d in r.run.floor.decor.items() if str(d).startswith("crack:"))
        moved, n, s_ = bump(r, (18, 101))
        side(gid, which, moved == want, f"{what}: into the cracked rock at 18,101 (Emerald's) from {n}: {'broken, walked on' if moved else 'stopped'} (rocks on the floor: {rocks[:4]}) {s_[-1:]}")


def g20():
    gid = "rusturf_rocks"
    title(gid, "Rusturf Tunnel to Verdanturf: the cracked rocks (24,4 / 24,5) need Rock Smash and the Dynamo Badge (ORAS)")
    for which, setup, want, what in (("before", lambda: at("wallyb"), False, "no HM Rock Smash"),
                                     ("old save", lambda: at("wallyb", also=True), False, "HM Rock Smash but no Dynamo Badge"),
                                     ("after", lambda: at("dynamo", also=True), True, "HM Rock Smash and the Dynamo Badge")):
        setup()
        out, n, s_ = take_exit("HOENN_RUSTURF_TUNNEL", "HOENN_ROUTE_116", "VERDANTURF_TOWN")
        side(gid, which, out == want, f"{what}: through to Verdanturf {'yes' if out else 'no'} (from {n}: {where()}) {s_[-1:]}")


def g21():
    gid = "new_mauville_door"
    title(gid, "Mauville's door to New Mauville: locked till Wattson asks you to check it (after the Rain Badge) and scans your eyes (DECISIONS #9)")
    at("rain", also=True)
    out, n, s_ = take_exit("MAUVILLE_CITY", "HOENN_ROUTE_110", "HOENN_NEW_MAUVILLE")
    side(gid, "before", not out, f"Wattson hasn't asked: the door stays locked (from {n}: {where()}) {s_[-1:]}")
    at("rain")
    v = town("MAUVILLE_CITY", "HOENN_ROUTE_110", room="hills")
    s_ = talk(v, "Wattson", choose="Wattson") or []
    side(gid, "before: no Rain Badge", not story.story_flags.get("wattson_new_mauville_asked"), f"before the Rain Badge Wattson doesn't ask ({s_[:1]})", "event")
    at("rain", also=True)
    v = town("MAUVILLE_CITY", "HOENN_ROUTE_110", room="hills")
    s_ = talk(v, "Wattson", choose="Wattson") or []
    side(gid, "event", story.story_flags.get("wattson_new_mauville_asked"), f"with the Rain Badge Wattson asks, and scans your eyes {s_[-2:]}", "event")
    out, n, s_ = take_exit("MAUVILLE_CITY", "HOENN_ROUTE_110", "HOENN_NEW_MAUVILLE")
    side(gid, "after", out, f"...and the door opens: into New Mauville ({where()})")
    side(gid, "deviation kept", out, "ORAS reaches New Mauville by Surf from Route 110; ours keeps Mauville's door (the agreed layout), locked as above", "data")


def g22():
    gid = "route111_desert"
    title(gid, "Route 111's sandstorm (10,62 and 10,37): only with the Go-Goggles (the rival, after the Heat Badge)")
    for which, also in (("before", False), ("after", True)):
        at("heat", also=also)
        r = route("HOENN_ROUTE_111", "MAUVILLE_CITY")
        moved, n, s_ = bump(r, (10, 62))
        side(gid, which, moved == also, f"{'Go-Goggles' if also else 'no Go-Goggles'}: into the sandstorm at 10,62 from {n}: {'walked in' if moved else 'turned back'} {s_[-1:]}")


def g23():
    gid = "route112_strength_rival"
    title(gid, "Route 112: your rival walks up and gives HM Strength (ORAS; Emerald: Rusturf)")
    at("strength")
    ok = scene_flag("HOENN_ROUTE_112", "HOENN_ROUTE_111", "got_strength_hoenn", at_=(37, 50), step="u")
    side(gid, "event", ok and story.inventory.get("HM_STRENGTH", 0) == 1, f"walking up Route 112 the rival gives Strength (got_strength_hoenn {ok}, HM {story.inventory.get('HM_STRENGTH', 0)}) {said[:1]}", "event")


def g24():
    gid = "route112_cable_car"
    title(gid, "Route 112's Cable Car: two Grunts stand in the only way up (26,30 / 27,30) till Meteor Falls")
    for which, also in (("before", False), ("after", True)):
        at("meteor", also=also)
        r = route("HOENN_ROUTE_112", "HOENN_ROUTE_111")
        moved, n, s_ = bump(r, (26, 30))
        opt = find_opt("HOENN_ROUTE_112", "CABLE CAR")
        ok = route_ok(r, opt)
        side(gid, which, moved == also and ok == also, f"{'Meteor Falls done' if also else 'Meteor Falls not done'}: into 26,30 from {n}: {'walked on' if moved else 'a Grunt blocks it'}; the Cable Car {'runs' if ok else 'is shut'} {s_[-1:]}")


def g25():
    gid = "route112_west_ledges"
    title(gid, "Route 112 west to Lavaridge and the Jagged Pass: only coming down from Mt. Chimney")
    for which, also in (("before", False), ("after", True)):
        at("chimney", also=also)
        for tgt in ("LAVARIDGE_TOWN", "HOENN_JAGGED_PASS"):
            out, n, s_ = take_exit("HOENN_ROUTE_112", "HOENN_ROUTE_111", tgt)
            side(gid, which, out == also, f"{'Mt. Chimney done' if also else 'Mt. Chimney not done'}: on to {tgt} {'yes' if out else 'no'} (from {n}: {where()}) {s_[-1:]}")


def g26():
    gid = "fiery_path_boulders"
    title(gid, "The Fiery Path: the main tunnel open (DECISIONS #14); the side boulders need Strength and the Heat Badge")
    at("dynamo", also=True)
    out, n, s_ = take_exit("HOENN_ROUTE_112", "HOENN_ROUTE_111", "HOENN_FIERY_PATH")
    side(gid, "main tunnel", out, f"no Strength: into the Fiery Path's main tunnel all the same ({where()}) {s_[-1:]}")
    from src.states.slide_puzzle import SlidePuzzleState
    for which, setup, want, what in (("before", lambda: at("dynamo", also=True), False, "no HM Strength"),
                                     ("old save", lambda: at("strength", also=True), False, "HM Strength but no Heat Badge"),
                                     ("after", lambda: at("heat", also=True), True, "HM Strength and the Heat Badge")):
        setup()
        r = route("HOENN_FIERY_PATH", "HOENN_ROUTE_112")
        boulders = sorted(t for t, d in r.run.floor.decor.items() if str(d).startswith("boulder:"))
        tile = (8, 11) if (8, 11) in boulders else (boulders[0] if boulders else (8, 11))
        said.clear()
        n, c = _floor_beside(r, tile)
        if n:
            stand(r, n); r.step(*_D[c]); frames(3)
        pushed = isinstance(g.current_state, SlidePuzzleState)
        if not pushed:
            play(lambda: _settled() or isinstance(g.current_state, SlidePuzzleState), 300)
            pushed = isinstance(g.current_state, SlidePuzzleState) or any("push it?" in x for x in said)
        side(gid, which, pushed == want, f"{what}: at the boulder {tile} (from {n}): {'you push it (the puzzle opens)' if pushed else 'it stays'} {said[-1:]}")
        if pushed:
            g.change_state(r); frames(2)


def g27():
    gid = "fallarbor_cozmo"
    title(gid, "Fallarbor: Professor Cozmo has been taken (the rival calls you over as you arrive)")
    at("cozmo")
    ok = scene_flag("FALLARBOR_TOWN", "HOENN_ROUTE_113", "fallarbor_cozmo_taken", at_=(10, 10), step="u")
    side(gid, "event", ok, f"reaching Fallarbor: the scene plays (fallarbor_cozmo_taken {ok}) {said[:1]}", "event")
    at("meteor", also=True)
    ok = scene_flag("FALLARBOR_TOWN", "HOENN_ROUTE_113", "fallarbor_cozmo_taken", at_=(10, 10), step="u", n=400)
    side(gid, "after", not ok, f"once Meteor Falls is done it doesn't play again ({ok})", "event")


def g28():
    gid = "meteor_falls_team"
    title(gid, "Meteor Falls: the team holds Cozmo (13,23 barred) till you beat them with your rival")
    for which, also in (("before", False), ("after", True)):
        at("meteor", also=also, flags=["meteor_falls_rival_joins"])
        r = route("HOENN_METEOR_FALLS", "HOENN_ROUTE_114")
        moved, n, s_ = bump(r, (13, 23))
        side(gid, which, moved == also, f"{'beaten' if also else 'not beaten'}: into 13,23 from {n}: {'through' if moved else 'stopped'} {s_[-1:]}")
    vic = [x.get("victory_flag") for x in _area["HOENN_METEOR_FALLS"].get("trainer_pool", []) if x.get("victory_flag")]
    side(gid, "opener", "meteor_falls_cleared" in vic, f"the team's boss battle sets meteor_falls_cleared ({vic})", "data")


def g29():
    gid = "mt_chimney_summit"
    title(gid, "Mt. Chimney's summit: the team's Admin and leader stand at the machine (13,6) till beaten")
    for which, also in (("before", False), ("after", True)):
        at("chimney", also=also)
        if also:
            beat("HOENN_MT_CHIMNEY")
        r = route("HOENN_MT_CHIMNEY", "HOENN_JAGGED_PASS")
        who = [(m.x, m.y, m.kind) for m in r.run.floor.movers if m.kind in ("trainer", "figure") and abs(m.x - 13) + abs(m.y - 6) <= 3]
        moved, n, s_ = bump(r, (13, 6))
        side(gid, which, (not who and moved) if also else (bool(who) or not moved), f"{'beaten' if also else 'not beaten'}: by the machine {who or 'nobody'}; into 13,6 from {n}: {'walked on' if moved else 'stopped'}")


def g30():
    gid = "magma_emblem_hideout"
    title(gid, "Jagged Pass: the Magma Hideout's hidden door (16,18) opens with the Magma Emblem from Mt. Pyre (Emerald only, kept)")
    for which, also in (("before", False), ("after", True)):
        at("pyre", also=also)
        out, n, s_ = take_exit("HOENN_JAGGED_PASS", "HOENN_ROUTE_112", "HOENN_MAGMA_HIDEOUT")
        side(gid, "deviation kept: " + which, out == also, f"Emerald-only, kept: {'with' if also else 'without'} the Magma Emblem: into the hideout {'yes' if out else 'no'} (from {n}: {where()}) {s_[-1:]}")


def g31():
    gid = "surf_water"
    title(gid, "Water (Route 118 north to Route 119): HM Surf from Wally's father after Norman, used with the Balance Badge")
    at("balance")
    v = town("PETALBURG_CITY", "HOENN_ROUTE_102", room="wally_home")
    s_ = talk(v, "Wally's father") or []
    side(gid, "giver: before", not story.inventory.get("HM_SURF"), f"no Balance Badge: Wally's father has nothing for you yet ({s_[:1]})", "event")
    at("balance", also=True)
    v = town("PETALBURG_CITY", "HOENN_ROUTE_102", room="wally_home")
    s_ = talk(v, "Wally's father") or []
    side(gid, "giver", story.inventory.get("HM_SURF") == 1, f"with the Balance Badge he gives HM Surf ({s_[-1:]})", "event")
    for which, setup, want, what in (("before", lambda: at("balance", also=True), False, "the Balance Badge, no HM Surf"),
                                     ("old save", lambda: at("surf", also=True, badges=4), False, "a save holding HM Surf without the Balance Badge (as ORAS: no surfing)"),
                                     ("after", lambda: at("surf", also=True), True, "HM Surf and the Balance Badge")):
        setup()
        out, n, s_ = take_exit("HOENN_ROUTE_118", "MAUVILLE_CITY", "HOENN_ROUTE_119")
        side(gid, which, out == want, f"{what}: across Route 118's river to Route 119 {'yes' if out else 'no'} (from {n}: {where()}) {s_[-1:]}")
    at("surf", also=True, badges=4)
    r = route("HOENN_ROUTE_118", "MAUVILLE_CITY")
    side(gid, "old save: the Surf test", not r._can_surf() and _hms.badge_wanted(story, "HM_SURF") == "Balance",
         f"...the map's own Surf test with the HM but no badge: can surf {r._can_surf()}, badge still wanted: {_hms.badge_wanted(story, 'HM_SURF')}", "menu")


def g32():
    gid = "route118_steven_southern"
    title(gid, "Route 118: Steven meets you with the Balance Badge and gives the Mega Bracelet; no Eon Flute here now (DECISIONS #11)")
    at("bracelet")
    ok = scene_flag("HOENN_ROUTE_118", "MAUVILLE_CITY", "got_mega_bracelet", at_=(43, 9), step="u")
    side(gid, "event", ok and not story.inventory.get("EON_FLUTE"), f"with the Balance Badge: Steven's meeting gives the Mega Bracelet ({ok}), and no Eon Flute (flute: {story.inventory.get('EON_FLUTE', 0)}) {said[:1]}", "event")
    at("heat", also=True)
    r = route("HOENN_ROUTE_118", "MAUVILLE_CITY")
    opt = find_opt("HOENN_ROUTE_118", "MEET STEVEN")
    side(gid, "before", not route_ok(r, opt), "no Balance Badge: Steven isn't there to meet", "menu")


def g33():
    gid = "weather_institute"
    title(gid, "The Weather Institute: the team's Admin holds it; beating them sets weather_institute_cleared")
    at("weather")
    t = trainers_out("HOENN_WEATHER_INSTITUTE", "HOENN_ROUTE_119", lambda n, p: True)
    side(gid, "before", t, f"not cleared: the team stands inside ({t[:4] if t else t})")
    vic = [x.get("victory_flag") for x in _area["HOENN_WEATHER_INSTITUTE"].get("trainer_pool", []) if x.get("victory_flag")]
    side(gid, "opener", "weather_institute_cleared" in vic, f"the Admin's battle sets it ({vic})", "data")


def g34():
    gid = "route119_rival_fly"
    title(gid, "Route 119: the rival battles you after the Weather Institute and gives HM Fly; Fortree waits for that battle")
    at("weather")
    ok = scene_flag("HOENN_ROUTE_119", "HOENN_ROUTE_118", "hoenn_rival_119", at_=(27, 30), step="u", n=500)
    side(gid, "before: Institute", not ok, f"the Institute not cleared: the rival doesn't come ({ok})", "event")
    at("weather", also=True)
    ok = scene_flag("HOENN_ROUTE_119", "HOENN_ROUTE_118", "hoenn_rival_119", at_=(27, 30), step="u")
    side(gid, "event", ok and story.inventory.get("HM_FLY", 0) == 1, f"Institute cleared: the rival battles you (hoenn_rival_119 {ok}) and HM Fly is in the Bag ({story.inventory.get('HM_FLY', 0)})", "event")
    for which, also in (("before", False), ("after", True)):
        at("rival119", also=also)
        out, n, s_ = take_exit("HOENN_ROUTE_119", "HOENN_ROUTE_118", "FORTREE_CITY")
        side(gid, which, out == also, f"{'rival beaten' if also else 'rival not beaten'}: on to Fortree {'yes' if out else 'no'} (from {n}: {where()}) {s_[-1:]}")


def g35():
    gid = "fly_feather_badge"
    title(gid, "Fly on the map: HM Fly used with the Feather Badge (ORAS)")
    at("rival119", also=True)
    v = town("FORTREE_CITY", "HOENN_ROUTE_119")
    side(gid, "old save", not story.can_fly() if hasattr(story, "can_fly") else False,
         f"HM Fly, no Feather Badge: Fly can't be used ({_hms.badge_wanted(story, 'HM_FLY')} Badge wanted)", "menu")
    at("feather", also=True)
    v = town("FORTREE_CITY", "HOENN_ROUTE_119")
    side(gid, "after", story.can_fly() if hasattr(story, "can_fly") else False, "HM Fly and the Feather Badge: Fly works", "menu")


def g36():
    gid = "route119_kecleon"
    title(gid, "Route 119's unseen Kecleon (31,6 / 25,15): in the way till the Devon Scope shows them")
    for which, also in (("before", False), ("after", True)):
        at("scope", also=also)
        r = route("HOENN_ROUTE_119", "HOENN_ROUTE_118")
        moved, n, s_ = bump(r, (25, 15))
        bat = _is_battle(g.current_state)
        if bat:
            _win(g.current_state)
        side(gid, which, (bat and not moved) if also else (not moved and not bat),
             f"{'Devon Scope' if also else 'no Devon Scope'}: into 25,15 from {n}: {'a Kecleon shows itself and battles' if bat else ('walked on' if moved else 'something unseen is in the way')} {s_[-1:]}")


def g37():
    gid = "fortree_gym_kecleon"
    title(gid, "Fortree: an unseen Kecleon (25,8) blocks the Gym's way; the Gym also wants Steven's flag and five badges")
    at("scope")
    v = town("FORTREE_CITY", "HOENN_ROUTE_119")
    moved, n, s_ = bump(v, (25, 8))
    side(gid, "before", not moved, f"no Devon Scope: 25,8 can't be walked into (from {n}) {s_[-1:]}")
    at("scope", also=True)
    v = town("FORTREE_CITY", "HOENN_ROUTE_119")
    moved, n, s_ = bump(v, (25, 8))
    flag = story.story_flags.get("kecleon_fortree_city_25_8")
    v = settle()
    moved2, n2, s2 = bump(v, (25, 8)) if isinstance(v, _WTS) else (False, None, [])
    side(gid, "after", flag and moved2, f"with the Devon Scope: the Kecleon shows itself and runs ({flag}), then 25,8 is walked on ({moved2}) {s_[-1:]}")
    req = (_area["FORTREE_CITY"].get("gym") or {}).get("requirements") or {}
    at("scope", also=True, drop=["got_starter_mega_stone"])
    inside, closed, v = gym_door("FORTREE_CITY", "HOENN_ROUTE_119")
    side(gid, "gym: before", bool(closed), f"without Steven's meeting on Route 120 the Gym is closed ({str(closed)[:70]}; needs {req.get('flags')}, {req.get('badges')} badges)")
    at("scope", also=True)
    inside, closed, v = gym_door("FORTREE_CITY", "HOENN_ROUTE_119")
    side(gid, "gym: after", not closed, f"with it: open ({closed})")


def g38():
    gid = "route120_steven_scope"
    title(gid, "Route 120: Steven gives the Devon Scope (the only giver; DECISIONS #10)")
    w = (_area["MAUVILLE_CITY"].get("gym") or {}).get("leader") or {}
    side(gid, "Wattson", "DEVON_SCOPE" not in (w.get("rewards") or {}), f"Wattson's prizes have no Devon Scope ({sorted((w.get('rewards') or {}))})", "data")
    at("scope")
    ok = scene_flag("HOENN_ROUTE_120", "FORTREE_CITY", "got_starter_mega_stone", at_=(8, 16), step="u")
    side(gid, "event", ok and story.inventory.get("DEVON_SCOPE", 0) == 1, f"Steven on the bridge: the Devon Scope ({story.inventory.get('DEVON_SCOPE', 0)}) and your starter's Mega Stone ({ok}) {said[:1]}", "event")
    at("scope")
    r = route("HOENN_ROUTE_120", "FORTREE_CITY")
    moved, n, s_ = bump(r, (12, 16))
    side(gid, "before", not moved and not _is_battle(g.current_state), f"before Steven's scope: the bridge's Kecleon (12,16) is an unseen block (from {n})")
    at("scope", also=True)
    r = route("HOENN_ROUTE_120", "FORTREE_CITY")
    moved, n, s_ = bump(r, (12, 16))
    bat = _is_battle(g.current_state)
    if bat:
        _win(g.current_state)
    side(gid, "after", bat, f"with it: the Kecleon on the bridge shows itself and battles ({type(g.current_state).__name__})")


def g39():
    gid = "route121_grunts"
    title(gid, "Route 121: Grunts run past to Mt. Pyre once you hold the Feather Badge")
    for which, also in (("before", False), ("after", True)):
        at("feather", also=also)
        ok = scene_flag("HOENN_ROUTE_121", "HOENN_ROUTE_120", "route121_grunts_ran", at_=(25, 9), step="u", n=900 if also else 400)
        side(gid, which, ok == also, f"{'with' if also else 'without'} the Feather Badge: the Grunts {'run past' if ok else 'are not there'}", "event")


def g40():
    gid = "mt_pyre_orb"
    title(gid, "Mt. Pyre's summit: beat the Admin; the elders give you the other orb (and the Magma Emblem)")
    for which, also in (("before", False), ("after", True)):
        at("pyre", drop=([] if also else ["mt_pyre_cleared"]), flags=(["mt_pyre_cleared", "route121_grunts_ran"] if also else ["route121_grunts_ran"]))
        r = route("HOENN_MT_PYRE", "HOENN_ROUTE_122")
        opt = find_opt("HOENN_MT_PYRE", "TALK TO THE ELDERS")
        ok = route_ok(r, opt)
        if ok:
            fl, mv = figure(r, lambda t: "ELDER" in t.upper())
            s_ = use_figure(r, mv) if mv else press_option(r, opt)
        side(gid, which, ok == also and (not also or story.story_flags.get("got_mt_pyre_orb")),
             f"Admin {'beaten' if also else 'not beaten'}: the elders {'give the orb' if ok else 'wait'} (got_mt_pyre_orb {story.story_flags.get('got_mt_pyre_orb')}, Magma Emblem {story.inventory.get('MAGMA_EMBLEM', 0)})", "event")


def g41():
    gid = "slateport_sub_stolen"
    title(gid, "Slateport: the team steals Stern's submarine once you have the orb from Mt. Pyre")
    for which, also in (("before", False), ("after", True)):
        at("pyre", also=also)
        ok = scene_flag("SLATEPORT_CITY", "HOENN_ROUTE_109", "slateport_sub_stolen", at_=(28, 16), step="u", n=1500 if also else 400)
        side(gid, which, ok == also, f"{'with' if also else 'without'} the orb: the sub theft {'plays' if ok else 'does not play'} (slateport_sub_stolen {ok})", "event")


def g42():
    gid = "lilycove_rival"
    title(gid, "Lilycove: beat your rival; the hideout's lookout (70,5) waits for that battle and for Slateport's sub theft (DECISIONS #12)")
    at("lilyrival")
    v = town("LILYCOVE_CITY", "HOENN_ROUTE_121")
    moved, n, s_ = bump(v, (70, 5))
    side(gid, "before", not moved, f"rival not beaten: the lookout at 70,5 blocks the way (from {n}) {s_[-1:]}")
    ok = scene_flag("LILYCOVE_CITY", "HOENN_ROUTE_121", "hoenn_rival_lilycove", at_=(31, 13), step="u")
    side(gid, "event", ok, f"the rival walks up and battles you (hoenn_rival_lilycove {ok})", "event")
    for which, setup, want, what in (("before: no sub theft", lambda: at("lilyrival", also=True, drop=["slateport_sub_stolen"]), False, "rival beaten, the sub not yet stolen"),
                                     ("after", lambda: at("lilyrival", also=True), True, "rival beaten and the sub stolen")):
        setup()
        out, n, s_ = take_exit("LILYCOVE_CITY", "HOENN_ROUTE_121", "HOENN_TEAM_HIDEOUT")
        side(gid, which, out == want, f"{what}: into the hideout {'yes' if out else 'no'} (from {n}: {where()}) {s_[-1:]}")


def g43():
    gid = "lilycove_wailmer"
    title(gid, "Lilycove's east sea: Wailmer block it (79,10-17) till the team's hideout is cleared")
    for which, also in (("before", False), ("after", True)):
        at("hideout", also=also)
        out, n, s_ = take_exit("LILYCOVE_CITY", "HOENN_ROUTE_121", "HOENN_ROUTE_124")
        v = g.current_state
        side(gid, which, out == also, f"hideout {'cleared' if also else 'not cleared'}: out to sea on to Route 124 {'yes' if out else 'no'} (from {n}: {where()}) {s_[-1:]}")


def g44():
    gid = "team_hideout"
    title(gid, "The team's hideout: its leader's battle sets aqua_hideout_cleared")
    at("hideout")
    t = trainers_out("HOENN_TEAM_HIDEOUT", "LILYCOVE_CITY", lambda n, p: True)
    side(gid, "before", t, f"not cleared: the team stands inside ({t[:3] if t else t})")
    vic = [x.get("victory_flag") for x in _area["HOENN_TEAM_HIDEOUT"].get("trainer_pool", []) if x.get("victory_flag")]
    side(gid, "opener", "aqua_hideout_cleared" in vic, f"the boss battle sets it ({vic})", "data")


def g45():
    gid = "mossdeep_gym"
    title(gid, "Mossdeep Gym: Tate and Liza want six badges")
    at("mind", badges=5)
    inside, closed, v = gym_door("MOSSDEEP_CITY", "HOENN_ROUTE_124")
    side(gid, "before", bool(closed), f"five badges: closed ({str(closed)[:70]})")
    at("mind")
    inside, closed, v = gym_door("MOSSDEEP_CITY", "HOENN_ROUTE_124")
    side(gid, "after", not closed, f"six badges: open ({closed})")


def g46():
    gid = "mossdeep_dive"
    title(gid, "Mossdeep: Steven gives HM Dive in his house after the Mind Badge (ORAS)")
    for which, also in (("before", False), ("after", True)):
        at("mind", also=also)
        v = town("MOSSDEEP_CITY", "HOENN_ROUTE_124", room="steven")
        s_ = talk(v, "Steven") or []
        got = story.inventory.get("HM_DIVE", 0)
        side(gid, which, (got == 1) == also, f"{'with' if also else 'without'} the Mind Badge: HM Dive from Steven {got} {s_[-1:]}", "event")


def g47():
    gid = "dive_spots"
    title(gid, "Dive: HM Dive used with the Mind Badge; Route 124 to Route 126 by Surf (DECISIONS #14)")
    at("mind", also=True)
    out, n, s_ = take_exit("HOENN_ROUTE_124", "MOSSDEEP_CITY", "HOENN_ROUTE_126")
    side(gid, "Route 124 -> 126", out, f"Surf, no Dive: on to Route 126 ({where()}) {s_[-1:]}")
    for which, setup, want, what in (("before", lambda: at("mind", also=True), False, "no HM Dive"),
                                     ("old save", lambda: at("dive", also=True, badges=6), False, "HM Dive but no Mind Badge"),
                                     ("after", lambda: at("dive", also=True), True, "HM Dive and the Mind Badge")):
        setup()
        out, n, s_ = take_exit("HOENN_ROUTE_128", "HOENN_ROUTE_127", "HOENN_SEAFLOOR_CAVERN", floor=1)
        side(gid, which, out == want, f"{what}: from Route 128's seabed into the Seafloor Cavern {'yes' if out else 'no'} (from {n}: {where()}) {s_[-1:]}")
    for which, setup, want in (("old save: diving", lambda: at("dive", also=True, badges=6), False), ("after: diving", lambda: at("dive", also=True), True)):
        setup()
        r = route("HOENN_ROUTE_128", "HOENN_ROUTE_127")
        spots = sorted(tuple(int(v) for v in k.split(",")) for k in ((_tm["HOENN_ROUTE_128"]["floors"][0].get("dive") or {}) if isinstance(_tm["HOENN_ROUTE_128"]["floors"][0].get("dive"), dict) else {}))
        can = _hms.field(story, "HM_DIVE")
        side(gid, which, can == want, f"the map's own Dive test (hms.field): {can}; dive spots on Route 128: {len(spots)}", "menu")


def g48():
    gid = "seafloor_cavern"
    title(gid, "The Seafloor Cavern: the team's leader at the bottom; the battle sets seafloor_cavern_cleared")
    at("seafloor")
    t = trainers_out("HOENN_SEAFLOOR_CAVERN", "HOENN_ROUTE_128", lambda n, p: True)
    side(gid, "before", t, f"not cleared: the team stands in the cavern ({t[:3] if t else t})")
    vic = [x.get("victory_flag") for x in _area["HOENN_SEAFLOOR_CAVERN"].get("trainer_pool", []) if x.get("victory_flag")]
    side(gid, "opener", "seafloor_cavern_cleared" in vic, f"the leader's battle sets it ({vic})", "data")


def g49():
    gid = "sootopolis_cave_of_origin"
    title(gid, "Sootopolis: Wallace stands at the Cave of Origin (31,17) till the crisis brings him to you")
    at("seafloor")
    out, n, s_ = take_exit("SOOTOPOLIS_CITY", "HOENN_ROUTE_126", "HOENN_CAVE_OF_ORIGIN")
    side(gid, "before", not out, f"the Seafloor Cavern not done: no way into the cave (from {n}: {where()}) {s_[-1:]}")
    at("wallace")
    ok = scene_flag("SOOTOPOLIS_CITY", "HOENN_ROUTE_126", "sootopolis_wallace_met", at_=(31, 23), step="u")
    side(gid, "event", ok, f"after the Seafloor Cavern, Wallace and Steven meet you (sootopolis_wallace_met {ok})", "event")
    at("wallace", also=True)
    out, n, s_ = take_exit("SOOTOPOLIS_CITY", "HOENN_ROUTE_126", "HOENN_CAVE_OF_ORIGIN")
    side(gid, "after", out, f"Wallace met: into the Cave of Origin ({where()})")


def g50():
    gid = "cave_of_origin_primal"
    title(gid, "The Cave of Origin: the Primal legend at the bottom (9,9 on the last floor), after the Seafloor Cavern")
    for which, also in (("before", False), ("after", True)):
        at("seafloor", also=also, flags=["sootopolis_wallace_met"] if also else [])
        r = route("HOENN_CAVE_OF_ORIGIN", "SOOTOPOLIS_CITY")
        opt = next((o for o in _area["HOENN_CAVE_OF_ORIGIN"].get("route_menu", []) if str(o.get("text", "")).startswith("CONFRONT PRIMAL")), None)
        ok = route_ok(r, opt)
        side(gid, which, ok == also, f"Seafloor {'done' if also else 'not done'}: the Primal battle {'can' if ok else 'cannot'} start", "menu")
    at("wallace", also=True)
    r = route("HOENN_CAVE_OF_ORIGIN", "SOOTOPOLIS_CITY", floor=5)
    moved, n, s_ = bump(r, (9, 9))
    bat = _is_battle(g.current_state)
    if bat:
        _win(g.current_state)
    side(gid, "after: walked", bat, f"walking up to it on the last floor (from {n}): {'the battle starts' if bat else 'nothing'} ({type(g.current_state).__name__})")


def g51():
    gid = "eon_flute"
    title(gid, "The Eon Flute: Steven gives it in Sootopolis after the Cave of Origin (ORAS; DECISIONS #11); Soaring from Mossdeep needs it")
    for which, also in (("before", False), ("after", True)):
        at("origin", also=also)
        v = town("SOOTOPOLIS_CITY", "HOENN_ROUTE_126")
        s_ = talk(v, "Steven") or ["(Steven not there)"]
        got = story.inventory.get("EON_FLUTE", 0)
        side(gid, which, (got >= 1) == also, f"Cave of Origin {'done' if also else 'not done'}: {'the flute is yours' if got else 'Steven has no flute for you'} ({got}) {s_[-1:]}", "event")
        if also:
            side(gid, "one flute", got == 1, f"...and only one Eon Flute in the Bag ({got}): the flute that arrives by itself once the Cave of Origin is done (soaring3d.give_flute) and Steven's own gift are both given", "event")
    for which, also in (("Soaring: before", False), ("Soaring: after", True)):
        at("flute", also=True) if also else at("origin")
        v = town("MOSSDEEP_CITY", "HOENN_ROUTE_124")
        opt = find_opt("MOSSDEEP_CITY", "Soaring in the Sky", "travel_options")
        ok = town_shown(v, opt)
        side(gid, which, ok == also, f"{'with' if also else 'without'} the Eon Flute: Mossdeep's Soaring {'opens' if ok else 'stays shut'} (the Mega Bracelet alone is not enough)", "menu")


def g52():
    gid = "sootopolis_gym"
    title(gid, "Sootopolis Gym: seven badges and the Cave of Origin done")
    at("origin")
    inside, closed, v = gym_door("SOOTOPOLIS_CITY", "HOENN_ROUTE_126")
    side(gid, "before", bool(closed), f"seven badges, the cave not done: closed ({str(closed)[:70]})")
    at("origin", also=True)
    inside, closed, v = gym_door("SOOTOPOLIS_CITY", "HOENN_ROUTE_126")
    side(gid, "after", not closed, f"cave done: open ({closed})")


def g53():
    gid = "waterfall"
    title(gid, "Route 128 to Ever Grande: HM Waterfall (Wallace's prize) used with the Rain Badge")
    w = (_area["SOOTOPOLIS_CITY"].get("gym") or {}).get("leader") or {}
    side(gid, "giver", (w.get("rewards") or {}).get("HM_WATERFALL") == 1, "HM Waterfall is Wallace's prize", "data")
    for which, setup, want, what in (("before", lambda: at("rain"), False, "no HM Waterfall"),
                                     ("old save", lambda: at("rain", also=True, badges=7), False, "HM Waterfall but no Rain Badge"),
                                     ("after", lambda: at("rain", also=True), True, "HM Waterfall and the Rain Badge")):
        setup()
        out, n, s_ = take_exit("HOENN_ROUTE_128", "HOENN_ROUTE_127", "EVER_GRANDE_CITY")
        side(gid, which, out == want, f"{what}: up to Ever Grande {'yes' if out else 'no'} (from {n}: {where()}) {s_[-1:]}")


def g54():
    gid = "victory_road_moves"
    title(gid, "Victory Road: its cracked rocks need Rock Smash (Dynamo) and its boulders Strength (Heat)")
    m = _tm["HOENN_VICTORY_ROAD"]
    found = []
    for i, f in enumerate(m.get("floors") or [m]):
        for y, row in enumerate(f["art"]):
            for x, c in enumerate(row):
                if c in "0b":
                    found.append((i, x, y, c))
    rocks = [t for t in found if t[3] == "0"]
    if not rocks:
        note(gid, f"no cracked rock on Victory Road's floors (boulders: {len([t for t in found if t[3] == 'b'])}); its puzzles are walked in hoenn_maps")
        return
    i, x, y, _c = rocks[0]
    for which, setup, want in (("before", lambda: at("wallyvr", drop=["HM_ROCK_SMASH"]), False), ("after", lambda: at("wallyvr"), True)):
        setup()
        r = route("HOENN_VICTORY_ROAD", "EVER_GRANDE_CITY", floor=i)
        moved, n, s_ = bump(r, (x, y))
        side(gid, which, moved == want, f"{'with' if want else 'without'} Rock Smash: into the rock at {x},{y} on floor {i} from {n}: {'through' if moved else 'stopped'}")


def g55():
    gid = "victory_road_wally"
    title(gid, "Victory Road: Wally waits; the League wants him beaten")
    at("wallyvr")
    t = trainers_out("HOENN_VICTORY_ROAD", "EVER_GRANDE_CITY", lambda n, p: "WALLY" in (n + str(p.get("name", ""))).upper())
    side(gid, "before", t, f"Wally stands in Victory Road ({t})")
    vic = [x.get("victory_flag") for x in _area["HOENN_VICTORY_ROAD"].get("trainer_pool", []) if x.get("victory_flag")]
    side(gid, "opener", "defeated_wally_victory" in vic, f"beating him sets defeated_wally_victory ({vic})", "data")


def _league_in(gid, which, setup, want, what):
    setup()
    v = town("EVER_GRANDE_CITY", "HOENN_VICTORY_ROAD", room="league")
    closed = v.gym_closed()
    ok, n, s_ = room_step(v, "ROOM:league_way")
    side(gid, which, (ok and not closed) == want, f"{what}: past the League's guards {'yes' if ok else 'no'} (the League says: {str(closed)[:60] if closed else 'open'}) {s_[-1:]}")


def g56():
    gid = "league_badge_check"
    title(gid, "The League's guards: all eight badges (ORAS) and Wally beaten")
    _league_in(gid, "before: seven badges", lambda: at("wallyvr", also=True, badges=7), False, "seven badges, Wally beaten")
    _league_in(gid, "before: Wally", lambda: at("wallyvr"), False, "eight badges, Wally not beaten")
    _league_in(gid, "after", lambda: at("wallyvr", also=True), True, "eight badges and Wally beaten")


def g57():
    gid = "league_rooms"
    title(gid, "The Elite Four's rooms: each room's way on opens once you win there")
    for which, also in (("before", False), ("after", True)):
        at("wallyvr", also=True, flags=(["league_won_EVER_GRANDE_CITY_1"] if also else []))
        v = town("EVER_GRANDE_CITY", "HOENN_VICTORY_ROAD", room="league_sidney")
        moved, n, s_ = bump(v, (6, 2))
        side(gid, which, moved == also, f"Sidney {'beaten' if also else 'not beaten'}: his room's way on (6,2) {'opens' if moved else 'is shut'} (from {n}: {where()})")


def g58():
    gid = "delta_start"
    title(gid, "The Delta Episode begins at home: Mom's news after the Hall of Fame (DECISIONS #13)")
    for which, also in (("before", False), ("after", True)):
        at("champion", also=also)
        v = town("LITTLEROOT_TOWN", "HOENN_ROUTE_101", room="home")
        opt = find_opt("LITTLEROOT_TOWN", "Mom's news")
        ok = town_shown(v, opt)
        if ok:
            s_ = talk(v, "Mom's news", choose="news") or []
        side(gid, which, ok == also and bool(story.story_flags.get("delta_started")) == also,
             f"{'Champion' if also else 'not Champion yet'}: Mom's news {'is told' if ok else 'is not there'} (delta_started {story.story_flags.get('delta_started')})", "event")


def g59():
    gid = "delta_chain"
    title(gid, "The Delta Episode's steps, in ORAS order: each opens only after the one before (DECISIONS #13)")
    chain = [("PETALBURG_CITY", "HOENN_ROUTE_102", "Battle Courtney", "delta_mom", "delta_courtney_petalburg"),
             ("PETALBURG_CITY", "HOENN_ROUTE_102", "Battle Matt", "delta_mom", "delta_matt_petalburg"),
             ("HOENN_GRANITE_CAVE", "HOENN_ROUTE_106", "BATTLE ZINNIA", "delta_petalburg", "delta_zinnia_granite"),
             ("RUSTBORO_CITY", "HOENN_ROUTE_104", "Team Magma Grunt (Devon 1)", "delta_zinnia", "h4_rustboro_city_delta_grunt_1"),
             ("MOSSDEEP_CITY", "HOENN_ROUTE_124", "Battle Courtney", "delta_devon", "delta_courtney_mossdeep"),
             ("MOSSDEEP_CITY", "HOENN_ROUTE_124", "Battle Matt", "delta_devon", "delta_matt_mossdeep"),
             ("HOENN_ROUTE_131", "PACIFIDLOG_TOWN", "BATTLE WALLACE", "delta_mossdeep", "delta_wallace_131")]
    for key, came, text, step, flag in chain:
        for which, also in (("before", False), ("after", True)):
            at(step, also=also)
            st = open_map(key, came); st = settle()
            opt = find_opt(key, text, pred=lambda o: "OMEGA_RUBY" in json.dumps(o.get("condition")) or "ALPHA" not in json.dumps(o.get("condition")))
            if isinstance(st, _WTS):
                st.scenes.entered = True
                ok = town_shown(st, opt)
            else:
                ok = route_ok(st, opt)
            if ok:
                if isinstance(st, _WTS) and person(st, text):
                    talk(st, text)
                else:
                    press_option(st, opt)
            side(gid, f"{text} @ {key.title()}: {which}", ok == also and bool(story.story_flags.get(flag)) == also,
                 f"{'after' if also else 'before'} the step before it ({step}): {text} {'is there' if ok else 'is not'}; played: {flag} {story.story_flags.get(flag)}", "event")
    for key, came, step, what in (("HOENN_SPACE_CENTER", "MOSSDEEP_CITY", "delta_devon", "the Space Center's Delta Grunts (after Devon)"),
                                  ("HOENN_TEAM_HIDEOUT", "LILYCOVE_CITY", "delta_mossdeep", "the hideout's Delta Grunts (after Mossdeep's Admins)")):
        for which, also in (("before", False), ("after", True)):
            at(step, also=also)
            t = trainers_out(key, came, lambda n, p: "DELTA" in n.upper())
            side(gid, f"{key.title()}: {which}", bool(t) == also, f"{what}: {'out on the map' if t else 'not there'} ({t[:3] if t else t})")


def g60():
    gid = "sky_pillar_wallace"
    title(gid, "Sky Pillar's door on Route 131: Wallace battles you there in the Delta Episode, then lets you in (DECISIONS #13)")
    at("champion", also=True)
    out, n, s_ = take_exit("HOENN_ROUTE_131", "PACIFIDLOG_TOWN", "HOENN_SKY_PILLAR")
    side(gid, "before: Champion only", not out, f"Champion, the Delta Episode not reached Wallace: Sky Pillar stays shut (from {n}: {where()}) {s_[-1:]}")
    at("delta_wallace")
    out, n, s_ = take_exit("HOENN_ROUTE_131", "PACIFIDLOG_TOWN", "HOENN_SKY_PILLAR")
    side(gid, "before", not out, f"the Mossdeep Admins beaten, Wallace not: shut (from {n}: {where()})")
    at("delta_wallace", also=True)
    out, n, s_ = take_exit("HOENN_ROUTE_131", "PACIFIDLOG_TOWN", "HOENN_SKY_PILLAR")
    side(gid, "after", out, f"Wallace beaten: into Sky Pillar ({where()})")


def g61():
    gid = "ss_tidal_ticket"
    title(gid, "The S.S. Tidal (Slateport and Lilycove harbours): sails only after the Champion (Emerald; DECISIONS #8)")
    for key, came in (("SLATEPORT_CITY", "HOENN_ROUTE_109"), ("LILYCOVE_CITY", "HOENN_ROUTE_121")):
        for which, setup, want in (("before", lambda: at("league", also=True, badges=8), False), ("after", lambda: at("champion", also=True), True)):
            setup()
            v = town(key, came, room="harbor")
            if person(v, "S.S. Tidal") is None:
                side(gid, f"{key.title()}: {which}", False, "(no harbour sailor with the S.S. Tidal in the harbour room)")
                continue
            said.clear()
            s_ = talk(v, "S.S. Tidal", choose="Tidal") or []
            went = play(lambda: story.current_area_key == "HOENN_SS_TIDAL", 600)
            side(gid, f"{key.title()}: {which}", went == want,
                 f"{'Champion' if want else 'all eight badges and the Elite Four, not yet Champion'}: asking the harbour sailor for the S.S. Tidal: {'aboard' if went else 'not aboard'} ({where()}) {s_[-1:]}")


def g62():
    gid = "eon_ticket"
    title(gid, "The Eon Ticket (ORAS: a StreetPass event): Wallace's prize stands in; Slateport's boat to Southern Island needs it (deviation kept)")
    w = (_area["SOOTOPOLIS_CITY"].get("gym") or {}).get("leader") or {}
    side(gid, "deviation kept: giver", (w.get("rewards") or {}).get("EON_TICKET") == 1, "deviation kept: the Eon Ticket is Wallace's prize (ORAS hands it out by StreetPass)", "data")
    for which, also in (("before", False), ("after", True)):
        at("rain", also=True, items=(["EON_TICKET"] if also else []))
        v = town("SLATEPORT_CITY", "HOENN_ROUTE_109", room="harbor")
        s_ = talk(v, "Southern Island", choose="Southern") or []
        went = play(lambda: story.current_area_key == "HOENN_SOUTHERN_ISLAND", 600)
        side(gid, "deviation kept: " + which, went == also, f"{'with' if also else 'without'} the Eon Ticket: the boat to Southern Island: {'sailed' if went else 'not sailed'} ({where()}) {s_[-1:]}")


if not _os.environ.get("HG_NONE"):
  for _fn in (g01, g02, g03, g04, g05, g06, g07, g08, g09, g10, g11, g12, g13, g14, g15, g16, g17, g18, g19, g20, g21, g22, g23, g24,
            g25, g26, g27, g28, g29, g30, g31, g32, g33, g34, g35, g36, g37, g38, g39, g40, g41, g42, g43, g44, g45, g46, g47, g48,
            g49, g50, g51, g52, g53, g54, g55, g56, g57, g58, g59, g60, g61, g62):
    if _os.environ.get("HG_ONLY") and _fn.__name__ not in _os.environ["HG_ONLY"].split(","):
        continue
    guarded(_fn.__name__, _fn)

at("starter", also=True)
story.current_area_key = "LITTLEROOT_TOWN"

# =================================================================================================== the list itself
_gates_file = _os.path.normpath(_os.path.join(_os.getcwd(), "..", "..", "kanto_handoff", "hoenn_rom_tools", "hoenn_gates.json"))
for _up in range(6):   # (a worktree sits deeper than the main folder: look up the tree for pokemon-games\kanto_handoff)
    _try = _os.path.normpath(_os.path.join(_os.getcwd(), *([".."] * _up), "kanto_handoff", "hoenn_rom_tools", "hoenn_gates.json"))
    if _os.path.exists(_try):
        _gates_file = _try
        break
if _os.path.exists(_gates_file):
    _gl = json.load(open(_gates_file, encoding="utf-8"))
    _ids = [x["id"] for x in _gl.get("gates", [])]
    _done = {r[0] for r in RESULTS if r[2] is not None}
    _not = [i for i in _ids if i not in _done]
    print(f"\nthe gate list: {len(_ids)} gates in hoenn_gates.json; tested here: {len([i for i in _ids if i in _done])}; not stepped: {_not}")
else:
    print(f"\n(the gate list was not found at {_gates_file})")

print("\nsummary by gate (ok / checks):")
_by = {}
for gid, which, ok, method in RESULTS:
    _by.setdefault(gid, []).append(ok)
for gid, oks in _by.items():
    _n = [o for o in oks if o is not None]
    print(f"   {'ok ' if all(_n) else 'XX '} {gid}: {sum(_n)}/{len(_n)}" + (f" (+{len(oks) - len(_n)} not verified)" if len(_n) < len(oks) else ""))
_meth = {}
for gid, which, ok, method in RESULTS:
    _meth.setdefault(method, 0)
    _meth[method] += 1
print("\nchecks by method: " + "; ".join(f"{m}: {v}" for m, v in sorted(_meth.items()) if m != "none") + f"; in all: {len([r for r in RESULTS if r[2] is not None])}")
print(f"\n##### {len(fails)} failures")
