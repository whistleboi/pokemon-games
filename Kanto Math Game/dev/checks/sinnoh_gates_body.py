# Sinnoh's story gates, both sides (11-24, Jordan: "Story gate checks now"; Dev Map clean-sinnoh-frontier-sprites-gates-suite;
# Hoenn's hoenn_gates made Sinnoh's). The gate list is Platinum's own: kanto_handoff/sinnoh_map_tools/sgates.py reads the event
# scripts out of the game file into out/gates.json (98 gates). The findings are in kanto_handoff/sinnoh_check/GATES.md.
#   Part 1: every Platinum gate sorted: tested below, kept different on purpose (with why), or waits on a batch not built
#           yet. A gate nobody has sorted is a FAIL (sgates.py found something new: sort it in SORTED).
#   Part 2: each gate on our walked maps met the way a player meets it: BEFORE (the story just short of it: you must not get
#           past) and AFTER (what opens it given: you must get past). "steps" = real steps into it on the walked map;
#           "reach" = reach_lib's walk of every map exit, as the game gates them, from Twinleaf (no way round).
#   A FAIL is a finding about the game, not something to patch here.
#       bash dev/checks/run.sh sinnoh_gates
import json, os, copy
from collections import deque
from src.states.overworld import PlayState, CityState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.states.overworld.dungeon import DungeonState
from src.states.battle import TrainerIntroState, TrainerBattleState
from src.world import guide, hms as _hms
from src.dungeon import core as _core

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


# ---------------------------------------------------------------------------------------------- a new Sinnoh game
g.dungeon_routes = True; g.walk_towns = True
g.start_new_game(); g.player_name, g.player_character = "LUCAS", "lucas"
story = g.story_manager
_rs = RegionSelectionState(g); _rs.selected_idx = _rs.regions.index("SINNOH"); _rs.confirm_selection()
for _i in range(6):
    _c = g.current_state
    if hasattr(_c, "input_name") and hasattr(_c, "confirm_selection"):
        _c.input_name = _c.input_name or "BARRY"
        _c.confirm_selection()
        if hasattr(_c, "on_confirm") and g.current_state is _c:
            _c.on_confirm()
    else:
        break
guide.WALKED_REGIONS.add("SINNOH")
story.starting_region = "SINNOH"
g.data.save = lambda *a, **k: None
_tm = json.load(open("assets/town_maps.json", encoding="utf-8"))
_area = g.loader.area_data["STORY_PROGRESSION"]

# (Hoenn's walking helpers, as they are: settle, open_map, town, route, bump, _win, side ...)
_hg = open("dev/checks/hoenn_gates_body.py", encoding="utf-8").read()
exec(_hg[_hg.index("said = []"):_hg.index("# ------------------------------------------------------------------------------"
                                                "---------------- the story in order")])
exec(_hg[_hg.index("# ---------------------------------------------------------------------------------------------- walking helpers"):
         _hg.index("def pick(st, word):")])
exec(open("dev/checks/reach_lib.py", encoding="utf-8").read())
_ONLY = set(filter(None, os.environ.get("SG_ONLY", "").split(",")))   # (SG_ONLY=V2,L3: just those gates, for a quick look)
_guarded0 = guarded


def guarded(gid, fn):
    if not _ONLY or gid in _ONLY:
        _guarded0(gid, fn)


def ace():
    a = Pokemon(g.loader.fetch_specific(150), g.assets, size_mult=2.5)
    a.level = 100; a.moves = ["ICE-BEAM", "PSYCHIC", "THUNDERBOLT", "FLAMETHROWER"]
    if hasattr(a, "recalculate_stats"):
        a.recalculate_stats()
    a.heal_full()
    return a


_BASE = (copy.deepcopy(dict(story.story_flags)), copy.deepcopy(dict(story.inventory)),
         {k: set(v) for k, v in story.defeated_trainers.items()}, copy.deepcopy({r: list(b) for r, b in story.badges.items()}))
BADGES = ["COAL", "FOREST", "COBBLE", "FEN", "RELIC", "MINE", "ICICLE", "BEACON"]
# (the story to the end of what's walked, S5's Galactic HQ: every flag our Sinnoh gates read, in story order)
STORY = ["sinnoh_visited_rival_home", "received_starter_sinnoh", "received_pokedex_sinnoh", "sinnoh_route202_lesson",
         "rowan_assistant_balls", "got_poketch", "sinnoh_r205_girl", "windworks_cleared", "galactic_eterna_cleared",
         "received_hm_cut", "sinnoh_cynthia_egg", "defeated_rival_pastoria", "sinnoh_pastoria_bomb", "sinnoh_valor_grunt_beaten",
         "defeated_rival_canalave", "canalave_library_meeting", "galactic_lake_valor_cleared", "galactic_lake_verity_cleared",
         "sinnoh_rowan_walked_up", "galactic_lake_acuity_cleared", "sinnoh_warehouse_guards_beaten", "galactic_hq_cleared"]
ITEMS = ["WORKS_KEY", "BICYCLE", "SECRET_POTION", "GALACTIC_KEY", "HM_CUT", "HM_FLY", "HM_SURF", "HM_STRENGTH", "HM_DEFOG",
         "HM_ROCK_SMASH", "HM_ROCK_CLIMB"]


def at(flags=(), items=(), badges=0, late=False, drop=()):
    """A clean save: the new game's state, then (late) the story to the Galactic HQ with its items and the first badges,
    flags/items on top, drop taken away; badges: how many Sinnoh badges, in Platinum's order."""
    story.story_flags.clear(); story.story_flags.update(copy.deepcopy(_BASE[0]))
    story.inventory.clear(); story.inventory.update(copy.deepcopy(_BASE[1]))
    story.defeated_trainers.clear(); story.defeated_trainers.update({k: set(v) for k, v in _BASE[2].items()})
    story.badges.clear(); story.badges.update(copy.deepcopy(_BASE[3]))
    story.player_team = [ace(), ace()]
    for f in (list(STORY) if late else []) + list(flags):
        story.story_flags[f] = True
    for i in (ITEMS if late else []) + list(items):
        story.inventory[i] = 1
    for d_ in drop:
        story.story_flags.pop(d_, None); story.inventory.pop(d_, None)
    story.badges["SINNOH"] = BADGES[:badges]
    story.repel_routes = 9999
    story.current_area_key = "TWINLEAF_TOWN"
    said.clear()


def cross(gid, which, key, tile, frm, expect, floor=None, room=None, method="steps", what=""):
    """Stand at frm on key's map (its floor / room) and take the step into tile. expect True: you must get on to it (or
    through it, off the map); False: you must not (a wall, a scene that walks you back, a battle that stops you)."""
    came = key
    if room is not None:
        st = town(key, came, room=room)
    elif _area[key].get("area_type") == "town" and floor is None:
        st = town(key, came)
    else:
        st = route(key, came, floor=floor or 0)
        if isinstance(st, DungeonState) and floor is not None and st.run.index != floor:   # (route() skips floor 0)
            st.run.jump_floor(floor, tuple(st.run.player)); frames(2); st = settle()
    for _t in range(3):   # (a wild Pokemon or a battle as you arrive: done with first)
        if _is_map(st):
            break
        if isinstance(st, WildBattleState):
            unbattle()
        elif _is_battle(st):
            _win(st)
        st = settle()
    if not _is_map(st):
        return side(gid, which, False, f"{key}: the map did not open ({type(st).__name__})", method)
    _calm(st)
    start = where()
    moved, n, s = bump(st, tile, frm)
    frames(4); settle(); frames(4); settle()   # (a scene that walks you back starts once you stand still)
    s = s + [x for x in said if x not in s]
    stopped_by_battle = _is_battle(g.current_state)
    if stopped_by_battle:
        _win(g.current_state)
    end = where()
    got = (not stopped_by_battle) and (end[2] == tuple(tile) or end[0] != start[0] or end[1] != start[1])
    line = next((x for x in s if x), "")
    side(gid, which, got == expect,
         f"{what} - {'got past' if got else 'stopped'}{' (a battle)' if stopped_by_battle else ''} at {key} {tuple(tile)} from {n}"
         f"{(': ' + repr(line[:70])) if line and not got else ''}", method)


def reaches(gid, which, target, expect, what=""):
    seen, _gy = reach("TWINLEAF_TOWN")
    side(gid, which, (target in seen) == expect,
         f"{what} - {target} {'reachable' if target in seen else 'not reachable'} from Twinleaf", "reach")


# ================================================================================================ 1. Platinum's gates sorted
# key: "<zone>|<source>" (sgates.py's), value: (what ours does, the gate's id below or "kept"/"waits"/"not a gate")
SORTED = {
    # Twinleaf / Route 201 / 202 / Jubilife
    "T01|trigger, script 4": ("T1", "a neighbour walks you back until you've been to Barry's house"),
    "T01R0202": ("not a gate", "Barry's 'There you are!' cutscene in his house"),
    "R201": ("R1", "Route 201 to Sandgem waits on your starter"),
    "R202": ("J0", "Dawn's catching lesson plays across Route 202"),
    "C01|trigger, script 3": ("J1", "Looker stops you at Jubilife's north exit until you have the Pokétch"),
    "C01|trigger, script 19": ("J2", "the Global Terminal guide turns you away with no badge"),
    "C01|trigger, script 28": ("kept", "Looker's Pal Pad talk: no Pal Pad (wireless play) in ours"),
    "C01|person": ("J1", "Looker himself (ours: he walks out at the north exit)"),
    "C01|on-load script 1 moves person 31 (script 5)": ("J1", "Looker's place by the state of the town"),
    # Eterna
    "C04|trigger, script 20": ("kept", "the Explorer Kit hint: the Underground is parked (long-term add-ins)"),
    "C04|trigger, script 23": ("not a gate", "a hint about Cycling Road once you have the Bicycle"),
    "C04|trigger, script 27": ("E1", "Cynthia stops you leaving Eterna east until you take her gift (Cut)"),
    "C04R0201|person, script 2 (sprite 124)": ("kept", "a Galactic Building grunt who only talks; ours puts trainers on its floors"),
    "C04R0201|person, script 6 (sprite 262)": ("waits", "the Secret Key door to Rotom's room: post-game (S8)"),
    "C04R0205": ("waits", "Rotom's room and its appliances: post-game (S8)"),
    "C04R0401": ("C1", "Cycling Road: only on a Bicycle"),
    "R206R0101": ("C1", "Cycling Road's gate"),
    # Floaroma / Route 205 / Windworks
    "T03": ("F1", "the grunts at Floaroma Meadow until you've helped the girl on Route 205"),
    "R205A": ("F2", "Route 205's bridge grunts until the Valley Windworks is cleared"),
    "D02": ("F3", "the Windworks door needs the Works Key"),
    # Route 210 / Pastoria / Veilstone
    "R210A": ("P1", "the Psyduck need the SecretPotion"),
    "C06|trigger, script 22": ("P2", "Barry by the Great Marsh after the Valor bomb"),
    "C06|trigger, script 18": ("P3", "Barry's battle at Pastoria"),
    "C06R0101": ("P2", "the Great Marsh lobby (Barry's stop)"),
    "C07": ("V1", "the grunt at Veilstone's warehouse until its guards are beaten"),
    "C07R0301": ("V2", "the warehouse's rusted door until Lake Acuity"),
    "D26R0101": ("H1", "Galactic HQ doors: the Galactic Key"),
    "D26R0103": ("H1", "Galactic HQ doors: the Galactic Key"),
    "D26R0104": ("H1", "Galactic HQ doors: the Galactic Key"),
    "D26R0106": ("H1", "Galactic HQ doors: the Galactic Key"),
    "D26R0107": ("H2", "the lake trio's machine until the HQ is cleared"),
    # Canalave / lakes
    "C02|on-load": ("waits", "the sailor's son's house (Darkrai, Newmoon): post-game (S8)"),
    "C02|person": ("waits", "the boat to Fullmoon / Newmoon Island (Lunar Wing): S8"),
    "C02GYM0101": ("not a gate", "the Gym guide's advice"),
    "C02R0501": ("waits", "the Lunar Wing house: S8"),
    "D15": ("waits", "Fullmoon Island: S8"),
    "D30": ("waits", "Newmoon Island: S8"),
    "L02|trigger": ("L2", "Valor Lakefront to Route 222 waits on Spear Pillar"),
    "L02|person": ("L1", "the way to Lake Valor until the Canalave Library meeting"),
    "D27R0101": ("kept", "Rowan at low-water Lake Verity; ours: Rowan and Dawn at Lake Verity's Galactic scene (L3)"),
    # Snowpoint / Coronet / League / Sunyshore
    "C09": ("S1", "Snowpoint Temple: after the Champion"),
    "D05R0102": ("M1", "Mt. Coronet to Spear Pillar"),
    "D05R0112": ("M1", "Mt. Coronet to Spear Pillar"),
    "D05R0114": ("M1", "Spear Pillar's stops"),
    "D05R0116": ("M1", "Spear Pillar's scene"),
    "C08": ("not a gate", "Jasmine's talk at Sunyshore"),
    "C10R0101": ("waits", "Barry at the League's door: S6 (the League's walked rooms)"),
    "R224": ("M2", "Victory Road to Route 224: after the Champion"),
    # the rest
    "D01R0102": ("not a gate", "Roark's Rock Smash show in the Oreburgh Mine"),
    "D10R0101": ("waits", "Pal Park: post-game (S8)"),
    "D11R0101": ("waits", "Amity Square's stroll with a Pokémon: not walked yet (S7 extras)"),
    "D16R0102": ("waits", "Stark Mountain with Buck: post-game (S8)"),
    "D31": ("waits", "the Battle Park: S8"),
    "C11": ("waits", "the Fight Area's blockers: post-game (S8)"),
    "W230": ("M3", "Route 230: Surf"),
    "R212AR0103": ("kept", "the Pokémon Mansion's statue: 'please don't touch' only"),
    "R218": ("not a gate", "the Pikachu trainer on Route 218 (a trainer, no stop)"),
    "T06": ("waits", "the Survival Area's house (Charon arrested): post-game (S8)"),
    "T07": ("waits", "the Resort Area's villa: post-game (S8)"),
    "T07R0201": ("waits", "the Villa's furniture and visitors: post-game (S8)"),
    "UG": ("kept", "the Underground: parked (long-term add-ins)"),
}


def sorted_as(gt):
    k = f"{gt['zone']}|{gt.get('source', '')}"
    for key in (k, k.split(",")[0], f"{gt['zone']}|{gt.get('source', '').split(' ')[0]}", gt["zone"]):
        if key in SORTED:
            return SORTED[key]
    return None


print("1) Platinum's gates (kanto_handoff/sinnoh_map_tools/out/gates.json, from sgates.py), each sorted")
_GJ = os.getcwd()
for _up in range(7):   # (kanto_handoff sits beside the game's folder; a worktree is deeper in)
    if os.path.isdir(os.path.join(_GJ, "kanto_handoff")):
        break
    _GJ = os.path.dirname(_GJ)
_GJ = os.path.join(_GJ, "kanto_handoff", "sinnoh_map_tools", "out", "gates.json")
TESTED = set()
if not os.path.exists(_GJ):
    print(f"   --   not found: {_GJ} (run sgates.py)")
else:
    _gates = json.load(open(_GJ, encoding="utf-8"))["gates"]
    tally = {}
    for _i, _gt in enumerate(_gates):
        s_ = sorted_as(_gt)
        if s_ is None:
            check(False, f"#{_i} {_gt['place']} {_gt['kind']} ({_gt['certainty']}, match {_gt['match']}): not sorted - "
                         f"{(_gt.get('hint') or '')[:70]!r}")
            continue
        cls = s_[0] if s_[0] in ("kept", "waits", "not a gate") else "tested"
        tally[cls] = tally.get(cls, 0) + 1
        if cls == "tested":
            TESTED.add(s_[0])
        print(f"   {'  ' if cls != 'tested' else '->'}   #{_i} {_gt['place']} ({_gt['kind']}, {_gt['certainty']}): "
              f"{s_[0] if cls == 'tested' else cls} - {s_[1]}")
    print(f"   == {len(_gates)} gates: {tally}")

# ================================================================================================ 2. met on the walked maps
print("\n2) each gate on our walked maps, BEFORE and AFTER")
title("T1", "Twinleaf: a neighbour walks you back until you've been to Barry's house")
guarded("T1", lambda: (at(), cross("T1", "BEFORE", "TWINLEAF_TOWN", (15, 3), (15, 4), False, what="a new game"),
                       at(flags=["sinnoh_visited_rival_home"]),
                       cross("T1", "AFTER", "TWINLEAF_TOWN", (15, 3), (15, 4), True, what="been to Barry's")))

title("R1", "Route 201 to Sandgem: your starter first")
guarded("R1", lambda: (at(flags=["sinnoh_visited_rival_home"]),
                       reaches("R1", "BEFORE", "SANDGEM_TOWN", False, "no starter"),
                       at(flags=["sinnoh_visited_rival_home", "received_starter_sinnoh"]),
                       reaches("R1", "AFTER", "SANDGEM_TOWN", True, "a starter")))


def _j0():
    at(flags=STORY[:3])
    st = route("SINNOH_ROUTE_202", "SANDGEM_TOWN")
    bump(st, (20, 27), (21, 27))
    play(lambda: story.story_flags.get("sinnoh_route202_lesson"), 1500)
    _b = g.current_state
    if _is_battle(_b):
        _win(_b)
    side("J0", "event", bool(story.story_flags.get("sinnoh_route202_lesson")),
         "walking up Route 202 with the Pokédex plays Dawn's catching lesson (its flag set)", "event")


title("J0", "Route 202: Dawn's catching lesson")
guarded("J0", _j0)

title("J1", "Jubilife: Looker stops you at the north exit until you have the Pokétch")
guarded("J1", lambda: (at(flags=STORY[:5]), cross("J1", "BEFORE", "JUBILIFE_CITY", (60, 22), (59, 22), False, what="no Pokétch"),
                       at(flags=STORY[:6]), cross("J1", "AFTER", "JUBILIFE_CITY", (60, 22), (59, 22), True, what="the Pokétch")))

title("J2", "Jubilife: the Global Terminal guide turns you away with no badge")
guarded("J2", lambda: (at(flags=STORY[:6]), cross("J2", "BEFORE", "JUBILIFE_CITY", (27, 44), (28, 44), False, what="no badge"),
                       at(flags=STORY[:6], badges=1), cross("J2", "AFTER", "JUBILIFE_CITY", (27, 44), (28, 44), True, what="the Coal Badge")))

title("F1", "Floaroma Meadow: the grunts until you've helped the girl on Route 205")
guarded("F1", lambda: (at(flags=STORY[:6], badges=1), cross("F1", "BEFORE", "FLOAROMA_TOWN", (2, 3), None, False, what="not yet"),
                       at(flags=STORY[:7], badges=1), cross("F1", "AFTER", "FLOAROMA_TOWN", (2, 3), None, True, what="helped her")))

title("F2", "Route 205's bridge: the grunts until the Valley Windworks is cleared")
guarded("F2", lambda: (at(flags=STORY[:7], badges=1), cross("F2", "BEFORE", "SINNOH_ROUTE_205", (24, 77), None, False, what="Windworks not cleared"),
                       at(flags=STORY[:8], badges=1), cross("F2", "AFTER", "SINNOH_ROUTE_205", (24, 77), None, True, what="Windworks cleared")))

title("F3", "Valley Windworks: the door needs the Works Key")
guarded("F3", lambda: (at(flags=STORY[:7], badges=1), cross("F3", "BEFORE", "VALLEY_WINDWORKS", (19, 13), None, False, floor=0, what="no Works Key"),
                       at(flags=STORY[:7], items=["WORKS_KEY"], badges=1),
                       cross("F3", "AFTER", "VALLEY_WINDWORKS", (19, 13), None, True, floor=0, what="the Works Key")))

title("E1", "Eterna: Cynthia stops you on the east road until you take her gift")
guarded("E1", lambda: (at(flags=STORY[:10], badges=2), cross("E1", "BEFORE", "ETERNA_CITY", (53, 30), None, False, what="Cut, no egg yet"),
                       at(flags=STORY[:11], badges=2), cross("E1", "AFTER", "ETERNA_CITY", (53, 30), None, True, what="her gift taken")))

title("C1", "Cycling Road: only on a Bicycle")
guarded("C1", lambda: (at(flags=STORY[:11], badges=2), cross("C1", "BEFORE", "SINNOH_ROUTE_206", (11, 18), None, False, what="no Bicycle"),
                       at(flags=STORY[:11], items=["BICYCLE"], badges=2),
                       cross("C1", "AFTER", "SINNOH_ROUTE_206", (11, 18), None, True, what="the Bicycle")))

title("P1", "Route 210: the Psyduck need the SecretPotion")
guarded("P1", lambda: (at(flags=STORY[:11], badges=3), cross("P1", "BEFORE", "SINNOH_ROUTE_210", (80, 74), None, False, what="no SecretPotion"),
                       at(flags=STORY[:11], items=["SECRET_POTION"], badges=3),
                       cross("P1", "AFTER", "SINNOH_ROUTE_210", (80, 74), None, True, what="the SecretPotion")))

title("P3", "Pastoria: Barry's battle on the way in")
guarded("P3", lambda: (at(flags=STORY[:11], badges=3), cross("P3", "BEFORE", "PASTORIA_CITY", (13, 28), None, False, what="not fought"),
                       at(flags=STORY[:12], badges=3), cross("P3", "AFTER", "PASTORIA_CITY", (13, 28), None, True, what="Barry beaten")))

title("P2", "Pastoria: Barry by the Great Marsh after the Valor bomb, until the grunt at Valor is beaten")
guarded("P2", lambda: (at(flags=STORY[:13], badges=4), cross("P2", "BEFORE", "PASTORIA_CITY", (34, 10), None, False, what="after the bomb"),
                       at(flags=STORY[:14], badges=4), cross("P2", "AFTER", "PASTORIA_CITY", (34, 10), None, True, what="the grunt beaten")))

title("B1", "Canalave: Barry on the bridge with the Mine Badge, until Strength (Jordan's Q2)")
guarded("B1", lambda: (at(flags=STORY[:15], badges=6), cross("B1", "BEFORE", "CANALAVE_CITY", (5, 15), None, False, what="Mine Badge, no Strength"),
                       at(flags=STORY[:15], items=["HM_STRENGTH"], badges=6),
                       cross("B1", "AFTER", "CANALAVE_CITY", (5, 15), None, True, what="Strength from Riley")))

title("L1", "Valor Lakefront: the way to the lake until the Canalave Library meeting")
guarded("L1", lambda: (at(flags=STORY[:15], badges=6), cross("L1", "BEFORE", "VALOR_LAKEFRONT", (35, 24), None, False, what="no meeting"),
                       at(flags=STORY[:16], badges=6), cross("L1", "AFTER", "VALOR_LAKEFRONT", (35, 24), (36, 24), True, what="after the meeting (the cameramen gone)"),
                       cross("L1", "AFTER", "VALOR_LAKEFRONT", (34, 24), (35, 24), True, what="on into Lake Valor")))

title("L3", "Lake Verity: Rowan and Dawn hold the Galactic scene until it's cleared")
guarded("L3", lambda: (at(flags=STORY[:17], badges=6), cross("L3", "BEFORE", "LAKE_VERITY", (45, 25), None, False, floor=0, what="Valor cleared"),
                       at(flags=STORY[:18], badges=6), cross("L3", "AFTER", "LAKE_VERITY", (45, 25), None, True, floor=0, what="Verity cleared")))

title("V1", "Veilstone: the warehouse grunt until its guards are beaten")
guarded("V1", lambda: (at(flags=STORY[:20], badges=7), cross("V1", "BEFORE", "VEILSTONE_CITY", (25, 20), None, False, what="guards not beaten"),
                       at(flags=STORY[:21], badges=7), cross("V1", "AFTER", "VEILSTONE_CITY", (25, 20), None, True, what="guards beaten")))

title("V2", "Galactic Warehouse: the rusted door until Lake Acuity")
guarded("V2", lambda: (at(flags=STORY[:19], badges=7), cross("V2", "BEFORE", "GALACTIC_WAREHOUSE", (8, 6), None, False, floor=0, what="Acuity not done"),
                       at(flags=STORY[:20], badges=7), cross("V2", "AFTER", "GALACTIC_WAREHOUSE", (8, 6), None, True, floor=0, what="Acuity done")))


def _h1():
    for key, fl, tile in (("GALACTIC_WAREHOUSE", 1, (14, 7)), ("TEAM_GALACTIC_HQ", 0, (22, 17)),
                          ("TEAM_GALACTIC_HQ", 2, (27, 18)), ("TEAM_GALACTIC_HQ", 3, (8, 13))):
        at(flags=STORY[:21], badges=7, drop=["GALACTIC_KEY"])
        cross("H1", "BEFORE", key, tile, None, False, floor=fl, what=f"floor {fl}, no Galactic Key")
        at(flags=STORY[:21], items=["GALACTIC_KEY"], badges=7)
        cross("H1", "AFTER", key, tile, None, True, floor=fl, what=f"floor {fl}, the Galactic Key")


title("H1", "Galactic Warehouse and HQ: the Galactic Key's doors")
guarded("H1", _h1)

title("H2", "Galactic HQ: the lake trio's machine until the HQ is cleared")
guarded("H2", lambda: (at(late=True, badges=7, drop=["galactic_hq_cleared"]),
                       cross("H2", "BEFORE", "TEAM_GALACTIC_HQ", (8, 9), None, False, floor=5, what="Saturn not beaten"),
                       side("H2", "AFTER", True, "(the trio's tiles stay walls: they're the machine's floor - see V2/H1 for the way on)", "data")))

title("S1", "Snowpoint Temple: after the Champion")
guarded("S1", lambda: (at(late=True, badges=8), cross("S1", "BEFORE", "SNOWPOINT_CITY", (14, 13), None, False, what="no Champion"),
                       at(late=True, badges=8, flags=["beat_sinnoh_champion"]),
                       cross("S1", "AFTER", "SNOWPOINT_CITY", (14, 13), None, True, what="the Champion beaten")))

title("M1", "Mt. Coronet to Spear Pillar: the Galactic HQ first (and Rock Climb)")
guarded("M1", lambda: (at(late=True, badges=7, drop=["galactic_hq_cleared"]),
                       reaches("M1", "BEFORE", "SPEAR_PILLAR", False, "HQ not cleared"),
                       at(late=True, badges=7), reaches("M1", "AFTER", "SPEAR_PILLAR", True, "HQ cleared")))

title("SP1", "Spear Pillar's summit: Mars and Jupiter hold the narrow way in till you and Barry beat them")
guarded("SP1", lambda: (at(late=True, badges=7), cross("SP1", "BEFORE", "SPEAR_PILLAR", (11, 41), (11, 42), False, floor=3, what="not fought"),
                        at(late=True, badges=7, flags=["spear_pillar_commanders"]),
                        cross("SP1", "AFTER", "SPEAR_PILLAR", (11, 41), (11, 42), True, floor=3, what="Mars and Jupiter beaten")))

title("SP2", "Spear Pillar's summit: Cyrus before the altar holds you back till he's beaten")
guarded("SP2", lambda: (at(late=True, badges=7, flags=["spear_pillar_commanders"]),
                        cross("SP2", "BEFORE", "SPEAR_PILLAR", (8, 14), (8, 15), False, floor=3, what="Cyrus not beaten"),
                        at(late=True, badges=7, flags=["spear_pillar_commanders", "spear_pillar_resolved"]),
                        cross("SP2", "AFTER", "SPEAR_PILLAR", (8, 14), (8, 15), True, floor=3, what="Cyrus beaten")))

title("DW1", "Distortion World B7F: the way down to Giratina after Cyrus")
guarded("DW1", lambda: (at(late=True, badges=8, flags=["spear_pillar_commanders", "spear_pillar_resolved", "beat_sinnoh_champion"]),
                        cross("DW1", "BEFORE", "DISTORTION_WORLD", (6, 44), (6, 43), False, floor=8, what="Cyrus not beaten"),
                        at(late=True, badges=8, flags=["spear_pillar_commanders", "spear_pillar_resolved", "beat_sinnoh_champion", "distortion_world_cleared"]),
                        cross("DW1", "AFTER", "DISTORTION_WORLD", (6, 44), (6, 43), True, floor=8, what="Cyrus beaten")))

title("SP3", "Mt. Coronet to the summit: Spear Pillar's floors join up")
guarded("SP3", lambda: (at(late=True, badges=7), reaches("SP3", "AFTER", "SPEAR_PILLAR", True, "HQ cleared"),
                        side("SP3", "data", "+" in "".join(_tm["SPEAR_PILLAR"]["floors"][2]["art"]) and not _tm["SPEAR_PILLAR"]["floors"][2].get("exits"),
                             "the third floor's way up is stairs to the summit (Platinum's D05R0109 -> D05R0114), not a way back to Mt. Coronet", "data")))

title("L2", "Valor Lakefront to Route 222: after Spear Pillar")
guarded("L2", lambda: (at(late=True, badges=7), reaches("L2", "BEFORE", "SINNOH_ROUTE_222", False, "Spear Pillar not resolved"),
                       at(late=True, badges=7, flags=["spear_pillar_resolved"]),
                       reaches("L2", "AFTER", "SINNOH_ROUTE_222", True, "Spear Pillar resolved")))

title("M2", "Victory Road to Route 224: after the Champion")
guarded("M2", lambda: (at(late=True, badges=8, flags=["spear_pillar_resolved"]),
                       reaches("M2", "BEFORE", "SINNOH_ROUTE_224", False, "no Champion"),
                       at(late=True, badges=8, flags=["spear_pillar_resolved", "beat_sinnoh_champion"]),
                       reaches("M2", "AFTER", "SINNOH_ROUTE_224", True, "the Champion beaten")))

def _flood_to(key, came, target):
    """Open key (in from came) as a player arrives, and walk every open tile from where you stand: can you get beside a
    way out to target?"""
    st = route(key, came)
    if not isinstance(st, DungeonState):
        return None
    f = st.run.floor
    surf = _hms.field(story, "HM_SURF")   # (open sea: only with Surf, as the route walker has it)
    goal = {t for t, x in f.exits.items() if x == target}
    seen, todo = {tuple(st.run.player)}, deque([tuple(st.run.player)])
    while todo:
        c = todo.popleft()
        if c in goal:
            return True
        for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)):
            n = (c[0] + dx, c[1] + dy)
            if n not in seen and f.inside(*n) and (n in goal or f.walkable(*n) and (f.tile(*n) != _core.SURF or surf)):
                seen.add(n); todo.append(n)
    return False


def _m3():
    at(late=True, badges=8, flags=["spear_pillar_resolved", "beat_sinnoh_champion"], drop=["HM_SURF"])
    r = _flood_to("SINNOH_ROUTE_230", "FIGHT_AREA", "SINNOH_ROUTE_229")
    side("M3", "BEFORE", r is False, f"no Surf: in from the Fight Area, the way on to Route 229 {'can' if r else 'can not'} be walked to", "steps")
    at(late=True, badges=8, flags=["spear_pillar_resolved", "beat_sinnoh_champion"])
    r = _flood_to("SINNOH_ROUTE_230", "FIGHT_AREA", "SINNOH_ROUTE_229")
    side("M3", "AFTER", r is True, f"Surf: the way on to Route 229 {'can' if r else 'can not'} be reached", "steps")


title("M3", "Route 230: Surf to cross it")
guarded("M3", _m3)

_missing = [] if _ONLY else sorted(TESTED - {r[0] for r in RESULTS})
check(not _missing, f"every gate Part 1 points to is met in Part 2 (missing: {_missing})")
print(f"\n== {sum(1 for r in RESULTS if r[2])} sides ok, {sum(1 for r in RESULTS if r[2] is False)} not, of {len(RESULTS)}")
print(f"##### {len(fails)} failures")
