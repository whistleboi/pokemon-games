# Kanto's story gates, both sides (Jordan 11-16; kanto_handoff/SWEEP_RULES.md Part 3 item 12). The gate list comes from
# FireRed's own event scripts (kanto_handoff/kanto_rom_tools/kanto_gates.json, read by kscript.py); here each gate is met
# on our walkable maps with real steps: BEFORE (the story state just short of it: you must not get past) and AFTER (what
# opens it granted: you must get past). A FAIL is a finding, not something to patch here: see
# kanto_handoff/kanto_check/GATES.md.          bash dev/checks/run.sh kanto_gates        (-v for every line)
# 11-16, after Jordan's decisions (kanto_handoff/kanto_check/DECISIONS.md): the loose gates, travel conditions and key-item
# places were set to FireRed's, and each approved difference from FireRed is tested as OURS ("deviation kept": Cerulean
# Gym waits for Bill, Nugget Bridge's no turning back, Route 22's gate wanting all eight badges, Route 19's beach
# needing Surf). The key-item givers are played as well as read from the data.
# Method per gate is printed with it: "steps" = real steps into the blocker; "flood" = a walk over the map's own
# open/blocked test (WalkTownState._open, the floor's walkable) where the blocker is a wall of tiles; "data" = read from
# the area data (where a key item is handed out).
_src = open("dev/checks/kanto_maps_body.py", encoding="utf-8").read()
exec(_src[:_src.index("# ---- every rebuilt map")])
import os as _os, re as _re
from src.dungeon import core as _core

story.starting_region = "KANTO"
BADGES = ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH", "VOLCANO", "EARTH"]
# The story in order, in OUR flags and items (what a player has after each step). A gate's BEFORE is everything up to its
# step; its AFTER adds the step. ("-X" takes an item away.)
STEPS = [
    ("starter", ["received_starter_kanto", "kanto_mom_morning", "kanto_oak_led", "kanto_lab_intro", "kanto_rival_left_lab", "got_oak_potions"], [], 0),
    ("parcel", ["got_oaks_parcel", "visited_VIRIDIAN_CITY", "viridian_rocket_defeated"], ["OAKS_PARCEL"], 0),
    ("pokedex", ["received_pokedex_kanto", "kanto_rival_pokedex", "visited_PALLET_TOWN"], ["-OAKS_PARCEL"], 0),
    ("boulder", ["visited_PEWTER_CITY"], [], 1),
    ("cerulean", ["visited_CERULEAN_CITY"], [], 1),
    ("bridge", ["nugget_bridge_cleared", "visited_BILLS_HOUSE"], [], 1),
    ("ticket", ["got_ss_ticket_bill"], ["SS_TICKET"], 1),
    ("cascade", ["got_tm_dig_cerulean"], [], 2),
    ("vermilion", ["visited_VERMILLION_CITY"], [], 2),
    ("cut", ["got_hm_cut_kanto"], ["HM_CUT"], 2),
    ("sailed", ["ss_anne_departed"], [], 2),
    ("thunder", ["vermilion_gym_open"], [], 3),
    ("lavender", ["visited_LAVENDER_TOWN", "visited_CELADON_CITY", "defeated_rival_tower"], [], 3),
    ("rainbow", [], [], 4),
    ("tea", [], ["TEA"], 4),
    ("poster", ["game_corner_guard_defeated", "game_corner_poster", "visited_ROCKET_HIDEOUT"], [], 4),
    ("liftkey", ["got_lift_key"], ["LIFT_KEY"], 4),
    ("scope", ["hideout_giovanni_defeated", "game_corner_cleared"], ["SILPH_SCOPE"], 4),
    ("ghost", ["tower_ghost_defeated"], [], 4),
    ("flute", ["fuji_rescued"], ["POKE_FLUTE"], 4),
    ("saffron", ["visited_SAFFRON_CITY"], [], 4),
    ("cardkey", [], ["CARD_KEY"], 4),
    ("silph", ["silph_co_cleared"], [], 4),
    ("snorlax", ["KANTO_ROUTE_12_boss_defeated", "KANTO_ROUTE_16_boss_defeated"], [], 4),
    ("bicycle", [], ["BICYCLE"], 4),
    ("fuchsia", ["visited_FUCHSIA_CITY"], [], 4),
    ("soul", [], [], 5),
    ("surf", [], ["HM_SURF"], 5),
    ("strength", [], ["HM_STRENGTH"], 5),
    ("marsh", [], [], 6),
    ("cinnabar", ["visited_CINNABAR_ISLAND", "visited_POKEMON_MANSION"], [], 6),
    ("secretkey", ["got_secret_key"], ["SECRET_KEY"], 6),
    ("volcano", [], [], 7),
    ("earth", [], [], 8),
]
_NAMES = [s[0] for s in STEPS]
_ALL_FLAGS = {f for s in STEPS for f in s[1]} | {"vr_switch_1f", "vr_switch_2f_w", "vr_switch_2f_e", "vr_switch_3f", "beat_champion", "beat_elite_four",
                                                 "hall_of_fame_due_INDIGO_PLATEAU"} | {f"league_won_INDIGO_PLATEAU_{i}" for i in range(1, 6)} \
    | {"hideout_b4f_door_open", "network_machine_fixed", "move_offer_kanto", "visited_SILPH_CITY", "visited_CERULEAN_CAVE", "mansion_simon_beaten", "got_bike_voucher",
       "got_coin_case", "got_super_rod_kanto", "got_hm_surf_kanto", "got_tri_pass", "visited_ONE_ISLAND", "visited_SAFARI_ZONE", "visited_POKEMON_MANSION"}
_ALL_ITEMS = {i.lstrip("-") for s in STEPS for i in s[2]} | {"HM_FLY", "HM_FLASH", "HM_ROCK_SMASH", "HM_WATERFALL", "GOLD_TEETH", "TRI_PASS", "RAINBOW_PASS",
                                                            "BIKE_VOUCHER", "COIN_CASE", "SUPER_ROD", "EXP_SHARE"}


def at(step, also=False, flags=(), items=(), badges=None, drop=()):
    """Set the story to just BEFORE step (also=True: just after it). Extra flags / items on top; drop takes flags or items away."""
    n = _NAMES.index(step) + (1 if also else 0)
    for f in _ALL_FLAGS:
        story.story_flags.pop(f, None)
    for i in _ALL_ITEMS:
        story.inventory.pop(i, None)
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
    for f in flags:
        story.story_flags[f] = True
    for i in items:
        story.inventory[i] = 1
    for d_ in drop:
        story.story_flags.pop(d_, None); story.inventory.pop(d_, None)
    story.badges["KANTO"] = BADGES[:nb if badges is None else badges]
    story.money = max(getattr(story, "money", 0) or 0, 5000) if hasattr(story, "money") else None
    said.clear()


_D = {"u": (0, -1), "d": (0, 1), "l": (-1, 0), "r": (1, 0)}
_BATTLE = (TrainerIntroState, TrainerBattleState, WildBattleState)


def _is_map(st):
    return isinstance(st, (_WTS, DungeonState))


def _settled():
    st = g.current_state
    if isinstance(st, _BATTLE) or type(st).__name__ in ("WildBattleState", "LegendIntroState", "BossIntroState"):
        return True
    if isinstance(st, _WTS):
        return not st._busy() and st.anim == 0
    if isinstance(st, DungeonState):
        return st._ready()
    return False


def settle(n=700):
    play(_settled, n)
    return g.current_state


def go(path):
    """Real steps on whatever map is up, each finished (talk tapped through, a map change waited for) before the next."""
    for c in path:
        settle(); frames(2)   # (stand a moment, as the game's own frame does before it reads a held key: scenes re-arm and start here)
        st = settle()
        if not _is_map(st):
            break
        st.step(*_D[c])
        frames(1)
    settle(); frames(4)
    return settle()


def arrive(area, n=400):
    """Wait for a change of map to finish (the Cycling Road takes a moment longer)."""
    return play(lambda: story.current_area_key == area, n)   # (true the moment you are there: Route 17's slope may roll you straight back out)


def note(gid, text):
    """Something the check could not settle either way: said, not counted."""
    RESULTS.append((gid, "not verified", None, "none"))
    print(f"   --   [{gid}] not verified: {text}")


def where():
    st = g.current_state
    if isinstance(st, _WTS):
        return (story.current_area_key, st.room, tuple(st.player))
    if isinstance(st, DungeonState):
        return (story.current_area_key, st.run.index, tuple(st.run.player))
    return (story.current_area_key, type(st).__name__, None)


def town(key, came, pos, room=None):
    if room:
        g.walk_town_pos = (key, tuple(pos), (0, -1)); g.walk_town_room = (key, room)
        story.current_area_key, story.last_area_key = key, came
        st = CityState(g); g.change_state(st); frames(2); tap(g.current_state)
        v = settle()
    else:
        v = open_map(key, came); v = settle()
    if isinstance(v, _WTS):
        v.player = tuple(pos); v.anim = 0; v.anim_from = tuple(pos)
    return v


def _quiet(st):
    st.run.floor.movers = [m for m in st.run.floor.movers if m.kind not in ("wild", "trainer")]


def _floor(st, i):
    while len(st.run.floors) <= i:
        st.run.enter_floor(len(st.run.floors))
    st.run.enter_floor(i); frames(2)
    return st


def dun(key, came, pos, floor=0):
    r = open_map(key, came); r = settle()
    if not isinstance(r, DungeonState):
        return r
    if floor:
        _floor(r, floor)
    _quiet(r)
    r.run.player = tuple(pos); r.anim = 0; r.anim_from = r.partner = r.partner_from = tuple(pos)
    r.encounter_free = 999
    return r


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


def flood_floor(f, start, goals):
    goals = {tuple(t) for t in goals}
    seen, q = {tuple(start)}, deque([tuple(start)])
    while q:
        x, y = q.popleft()
        for dx, dy in _D.values():
            n = (x + dx, y + dy)
            if n in seen or not f.inside(*n):
                continue
            if n in goals:
                return True
            if f.walkable(*n) and n not in f.exits and f.mover_at(*n) is None:
                seen.add(n); q.append(n)
    return False


def beside(ok, tile, avoid=()):
    """An open tile next to tile, and the step from it into tile."""
    for c, (dx, dy) in _D.items():
        n = (tile[0] - dx, tile[1] - dy)
        if n not in avoid and ok(n):
            return n, c
    return None, None


RESULTS = []   # (gate id, side, ok, what happened)


def side(gid, which, ok, what, method="steps"):
    RESULTS.append((gid, which, bool(ok), method))
    check(ok, f"[{gid}] {which} ({method}): {what}")


def title(gid, text):
    print(f"\n{gid}: {text}")


def guarded(gid, fn):
    try:
        fn()
    except Exception as ex:   # (a gate the check could not even set up: a finding of its own, the rest still run)
        import traceback
        side(gid, "setup", False, f"the check could not run this gate: {type(ex).__name__}: {ex} @ {traceback.extract_tb(ex.__traceback__)[-1].lineno}")


# =================================================================================================== the gates, in story order
def g_pallet():
    title("pallet_oak_grass", "Pallet's north edge: Oak stops you till you have a Pokémon (FireRed: trigger tiles 12-13,1, var 0x4050)")
    at("starter", flags=["kanto_mom_morning"])
    v = town("PALLET_TOWN", "PALLET_TOWN", (12, 3))
    go("uuuu"); settle(1500)
    side("pallet_oak_grass", "before", story.current_area_key == "PALLET_TOWN", f"no starter: still in Pallet {where()}")
    at("starter", also=True)
    v = town("PALLET_TOWN", "PALLET_TOWN", (12, 3))
    go("uuuu"); settle()
    side("pallet_oak_grass", "after", story.current_area_key == "KANTO_ROUTE_1", f"with a starter: out on to Route 1 {where()}")


def g_viridian():
    title("viridian_old_man", "Viridian's road north: shut till Oak has his Parcel and you the Pokédex (trigger 22,11, var 0x4051)")
    for nm, st_ in (("no Parcel yet", "parcel"), ("carrying the Parcel", "pokedex")):
        at(st_)
        v = town("VIRIDIAN_CITY", "KANTO_ROUTE_1", (21, 13))
        far = []
        for _ in range(4):   # (one step at a time, waiting each time till the granddaughter is back at her post)
            go("u"); settle(1500); frames(120); settle()
            far.append(where()[2])
        side("viridian_old_man", "before", story.current_area_key == "VIRIDIAN_CITY" and all(t and t[1] >= 12 for t in far), f"{nm}: turned back at the old man's road every time {far} {said[:1]}")
    at("pokedex")
    v = town("VIRIDIAN_CITY", "KANTO_ROUTE_1", (21, 13))
    go("uuuuu"); settle(1500)
    w = where()
    side("viridian_old_man", "before: pressing on", w[2] and w[2][1] >= 11, f"carrying the Parcel and walking straight on (stepping forward again at once after she turns you back, as a held key does): {w} (FireRed's trigger tile turns you back on every step; ours: the scene re-arms as it pushes you out, npc.py)")
    v = g.current_state
    ex = sorted(t for t, x in v.exits.items() if x == "KANTO_ROUTE_2")
    n, c = beside(v._open, ex[0], avoid=set(v.exits))
    v.player = n; v.anim = 0; v.anim_from = n
    go(c); settle()
    side("viridian_old_man", "before: the town's edge", story.current_area_key == "VIRIDIAN_CITY", f"...and at the top of the town, no Pokédex: Route 2 itself stays shut {where()} {getattr(g.current_state, 'toast', '')!r}")
    at("pokedex", also=True)
    v = town("VIRIDIAN_CITY", "KANTO_ROUTE_1", (21, 13))
    ok = flood_town(v, (21, 13), [t for t, x in v.exits.items() if x == "KANTO_ROUTE_2"])
    go("uuuuu"); settle()
    w = where()
    side("viridian_old_man", "after", ok and w[2] and w[2][1] <= 9, f"with the Pokédex: past the old man's spot and on to Route 2's edge {w}, road open: {ok}")
    # the Parcel itself: the Mart hands it over (FireRed: var 0x4057)
    at("parcel")
    v = town("VIRIDIAN_CITY", "KANTO_ROUTE_1", (36, 20))
    go("u"); settle(1500)
    side("viridian_old_man", "key item", story.inventory.get("OAKS_PARCEL") == 1, f"Oak's Parcel comes from Viridian's Mart clerk {where()}", "steps")


def g_pewter():
    title("pewter_guide", "Pewter's east road: the guide walks you to the Gym till you hold the Boulder Badge (triggers 42,21-23 and 43,23, var 0x406C)")
    at("boulder")
    v = town("PEWTER_CITY", "KANTO_ROUTE_2", (40, 22))
    go("rrrrrrrr"); settle(2500)
    side("pewter_guide", "before", story.current_area_key == "PEWTER_CITY", f"no badge: not out to Route 3 {where()} {said[:1]}")
    at("boulder", also=True)
    v = town("PEWTER_CITY", "KANTO_ROUTE_2", (40, 22))
    go("rrrrrrrr"); settle()
    side("pewter_guide", "after", story.current_area_key == "KANTO_ROUTE_3", f"with the Boulder Badge: out to Route 3 {where()}")


def _edge_step(r, target):
    """Stand beside one of this floor's ways out to target and step on to it."""
    f = r.run.floor
    for t in sorted(t for t, x in f.exits.items() if x == target):
        n, c = beside(lambda q: f.inside(*q) and f.walkable(*q) and q not in f.exits, t)
        if n:
            r.run.player = n; r.anim_from = r.partner = n
            go(c); settle()
            return n, t
    return None, None


def g_bridge():
    title("route24_nugget_rocket", "Nugget Bridge: the Rocket at its head must be fought (triggers 10-11,15, var 0x406B) before Route 25; ours also locks the way BACK till it's cleared (approved 11-16)")
    at("bridge", drop=["nugget_bridge_cleared"])
    r = dun("KANTO_ROUTE_24", "CERULEAN_CITY", (11, 17))
    n, t = _edge_step(r, "KANTO_ROUTE_25")
    side("route24_nugget_rocket", "before", story.current_area_key == "KANTO_ROUTE_24", f"bridge not cleared: no way on to Route 25 (from {n} on to {t}: {where()}) {said[:1]}")
    at("bridge", drop=["nugget_bridge_cleared"])
    r = dun("KANTO_ROUTE_24", "CERULEAN_CITY", (11, 17))
    n, t = _edge_step(r, "CERULEAN_CITY")
    side("route24_nugget_rocket", "deviation kept: no way back", story.current_area_key == "KANTO_ROUTE_24", f"mid-bridge, no turning back to Cerulean (FireRed lets you; Jordan keeps ours): {where()} {said[:1]}")
    at("bridge", also=True)
    r = dun("KANTO_ROUTE_24", "CERULEAN_CITY", (11, 17))
    n, t = _edge_step(r, "CERULEAN_CITY")
    side("route24_nugget_rocket", "after: way back", arrive("CERULEAN_CITY", 300), f"bridge cleared: back to Cerulean {where()}")
    at("bridge", also=True)
    r = dun("KANTO_ROUTE_24", "CERULEAN_CITY", (11, 17))
    n, t = _edge_step(r, "KANTO_ROUTE_25")
    side("route24_nugget_rocket", "after", story.current_area_key == "KANTO_ROUTE_25", f"bridge cleared: on to Route 25 {where()} {said[:1]}")


def g_burgled():
    title("cerulean_burgled_house", "Cerulean: the policeman stands in the burgled house's doorway (30,12) till Bill's S.S. Ticket (flag 0x234); the house is the only way on to Route 5")
    for which, st_ in (("before", lambda: at("ticket", flags=["got_tm_dig_cerulean"])), ("after", lambda: at("ticket", also=True, flags=["got_tm_dig_cerulean"]))):
        st_()   # (the Rocket in the back yard already beaten: he is a battle, not the gate)
        v = town("CERULEAN_CITY", "KANTO_ROUTE_4", (30, 13))
        r5 = [t for t, x in v.exits.items() if x == "KANTO_ROUTE_5"]
        road = flood_town(v, (22, 20), r5)
        cop = {t: p for p, o in v._people().items() for t in [(o.get("text") or "").strip()] if t in ("Police officer", "Policeman")}
        go("uu"); v = settle()
        w = where()
        through = None
        if w[1] not in (None,) and isinstance(v, _WTS):   # (inside: out by the back door, then round the yard to Route 5)
            back = next((t for t, x in v.exits.items() if str(x).startswith("OUT:") and x != "OUT:30,11"), None)
            if back:
                n, c = beside(v._open, back, avoid=set(v.exits))
                v.player = n; v.anim = 0; v.anim_from = n
                go(c); v = settle(1500)
                w2 = where()
                through = w2[1] is None and isinstance(v, _WTS) and flood_town(v, w2[2], r5)
                w = (w, "then out the back to", w2)
        if which == "before":
            side("cerulean_burgled_house", "before", not through and not road and cop == {"Policeman": (30, 12)}, f"no S.S. Ticket: no way through the burgled house to Route 5 (policeman: {cop}, FireRed 30,12; walked: {w}; reaches Route 5: {through}; a road round the house: {road}) {said[:1]}")
        else:
            side("cerulean_burgled_house", "after", through and cop == {"Police officer": (31, 12)}, f"with the Ticket: in the front, out the back, round to Route 5 (policeman: {cop}, FireRed 31,12; walked: {w}; reaches Route 5: {through})")
    at("ticket", flags=["got_tm_dig_cerulean", "visited_VERMILLION_CITY"])   # (an old save: past Cerulean before the gate existed, no ticket flag)
    v = town("CERULEAN_CITY", "KANTO_ROUTE_4", (30, 13))
    cop = {t: p for p, o in v._people().items() for t in [(o.get("text") or "").strip()] if t in ("Police officer", "Policeman")}
    go("uu"); settle()
    w = where()
    side("cerulean_burgled_house", "old save", cop == {"Police officer": (31, 12)} and w[1] not in (None, "CityState"),
         f"old-save allowance kept (Jordan 11-17): a save that has been to Vermilion finds the policeman beside the door ({cop}) and walks in: {w}")


def g_ssanne():
    title("vermilion_ss_anne_ticket", "Vermilion harbour: no boarding the S.S. Anne without the S.S. Ticket (triggers 22-23,33; flag 0x234)")
    at("ticket", flags=["visited_VERMILLION_CITY"])
    v = town("VERMILLION_CITY", "KANTO_ROUTE_6", (23, 33))
    go("d"); v = settle()
    gang = next((xy for xy, x in getattr(v, "exits", {}).items() if x == "KANTO_SS_ANNE"), None)
    if gang:
        n, c = beside(v._open, gang, avoid=set(v.exits))
        v.player = n; v.anim = 0; v.anim_from = n
        go(c); settle()
    side("vermilion_ss_anne_ticket", "before", story.current_area_key == "VERMILLION_CITY" and gang is not None, f"no Ticket: not aboard {where()} (gangway {gang}) {getattr(g.current_state, 'toast', '')!r}")
    at("ticket", also=True, flags=["visited_VERMILLION_CITY"])
    v = town("VERMILLION_CITY", "KANTO_ROUTE_6", (23, 33))
    go("d"); v = settle()
    gang = next((xy for xy, x in getattr(v, "exits", {}).items() if x == "KANTO_SS_ANNE"), None)
    if gang:
        n, c = beside(v._open, gang, avoid=set(v.exits))
        v.player = n; v.anim = 0; v.anim_from = n
        go(c); settle()
    side("vermilion_ss_anne_ticket", "after", story.current_area_key == "KANTO_SS_ANNE", f"with the Ticket: up the gangway {where()}")
    title("ss_anne_departs", "The S.S. Anne sails once the Captain has given HM01 Cut (var 0x407E 1 -> 3): no going back aboard")
    at("sailed", also=True)
    v = town("VERMILLION_CITY", "KANTO_ROUTE_6", (23, 33))
    go("d"); v = settle()
    gang = next((xy for xy, x in getattr(v, "exits", {}).items() if x == "KANTO_SS_ANNE"), None)
    if gang:
        n, c = beside(v._open, gang, avoid=set(v.exits))
        if n:
            v.player = n; v.anim = 0; v.anim_from = n
            go(c); settle()
    side("ss_anne_departs", "after sailing", story.current_area_key == "VERMILLION_CITY", f"the ship gone: not aboard again {where()} (gangway {gang})")
    at("cut")
    v = town("VERMILLION_CITY", "KANTO_ROUTE_6", (23, 33))
    go("d"); v = settle()
    side("ss_anne_departs", "before sailing", story.story_flags.get("ss_anne_departed") is None, f"Ticket in hand, no HM01 yet: the ship is still at the pier {where()}")


def _tree(gid, key, came, tree, start, goal_fn, what):
    at("cut")
    v = town(key, came, start)
    goals = goal_fn(v)
    n, c = beside(lambda t: v._open(t) and flood_town(v, start, [t]), tree)
    r0 = flood_town(v, start, goals)
    if n:
        v.player = n; v.anim = 0; v.anim_from = n
        go(c); settle()
    w = where()
    side(gid, "before", not r0 and (n is None or w[2] == n), f"no HM01: the tree at {tree} stands ({what} reachable: {r0}; stepped into it from {n}: {w})")
    at("cut", also=True)
    v = town(key, came, start)
    r1 = flood_town(v, start, goal_fn(v))
    if n:
        v.player = n; v.anim = 0; v.anim_from = n
        go(c); settle()
    w = where()
    side(gid, "after", r1 and (n is None or w[2] == tuple(tree)), f"with HM01 (and the Cascade Badge): through the tree ({what} reachable: {r1}; stepped: {w})")
    at("cut", also=True, badges=1)
    v = town(key, came, start)
    r2 = flood_town(v, start, goal_fn(v))
    side(gid, "before: no Cascade Badge", not r2, f"FireRed's tree script wants the Cascade Badge (flag 0x821) before Cut works; ours with HM01 and no Cascade Badge (hms.USE_BADGE): {what} reachable: {r2}", "flood")


def g_cut():
    title("cut_vermilion_gym_tree", "Vermilion: the Cut tree at 19,24 shuts off the Gym (HM01 from the S.S. Anne's Captain + the Cascade Badge)")
    _tree("cut_vermilion_gym_tree", "VERMILLION_CITY", "KANTO_ROUTE_6", (19, 24), (15, 7),
          lambda v: [(t[0], t[1] + 1) for t, r in v.doors.items() if r == "gym"], "the Gym's door")
    title("cut_route9_tree", "Route 9's west end: the Cut tree (FireRed: Cerulean 50,18 = our Route 9 2,8)")
    at("cut", drop=["visited_VERMILLION_CITY"])
    v = town("CERULEAN_CITY", "KANTO_ROUTE_4", (45, 18))
    go("rrr"); st = settle()
    w = where()
    side("cut_route9_tree", "firered: open road", w[0] == "KANTO_ROUTE_9", f"Cerulean's east road needs nothing (no Vermilion visit, no badge: FireRed's only gate is the tree): on Route 9 {w} {said[:1]}")
    if w[0] == "KANTO_ROUTE_9" and isinstance(st, DungeonState):
        _quiet(st); st.run.player = (1, 8); go("rr"); settle(); w = where()
    side("cut_route9_tree", "before", not (w[0] == "KANTO_ROUTE_9" and w[2] and w[2][0] >= 3), f"no HM01: not past the tree {w} {said[:1]}")
    at("cut", also=True, badges=1, drop=["visited_VERMILLION_CITY"])
    v = town("CERULEAN_CITY", "KANTO_ROUTE_4", (45, 18))
    go("rrr"); st = settle()
    w = where()
    if w[0] == "KANTO_ROUTE_9" and isinstance(st, DungeonState):
        _quiet(st); st.run.player = (1, 8); go("rr"); settle(); w = where()
    side("cut_route9_tree", "before: no Cascade Badge", not (w[0] == "KANTO_ROUTE_9" and w[2] and w[2][0] >= 3), f"HM01 but no Cascade Badge: not past the tree {w} {said[:1]}")
    at("cut", also=True, drop=["visited_VERMILLION_CITY"])
    v = town("CERULEAN_CITY", "KANTO_ROUTE_4", (45, 18))
    go("rrr"); st = settle()
    w = where()
    if w[0] == "KANTO_ROUTE_9" and isinstance(st, DungeonState):
        _quiet(st); st.run.player = (1, 8); go("rr"); settle(); w = where()
    side("cut_route9_tree", "after", w[0] == "KANTO_ROUTE_9" and w[2] and w[2][0] >= 3, f"with HM01 and the Cascade Badge (Vermilion never visited): from Cerulean on to Route 9 and through the tree {w}")


def g_gamecorner():
    title("game_corner_poster", "Celadon Game Corner: the stairs to the Rocket Hideout open from the switch behind the poster (sign 11,1 sets flag 0x26D; the grunt at 11,2 guards it)")
    at("poster")
    r = dun("CELADON_GAME_CORNER", "CELADON_CITY", (9, 11))
    hidden = "ROCKET_HIDEOUT" not in r.run.floor.exits.values()
    r.run.player = (15, 4)
    go("uu"); settle()
    side("game_corner_poster", "before", story.current_area_key == "CELADON_GAME_CORNER" and hidden, f"poster not pressed: no stairs, no way down {where()} (stairs hidden: {hidden})")
    at("poster", also=True)
    r = dun("CELADON_GAME_CORNER", "CELADON_CITY", (9, 11))
    n, t = _edge_step(r, "ROCKET_HIDEOUT")
    side("game_corner_poster", "after", story.current_area_key == "ROCKET_HIDEOUT", f"switch pressed: down the stairs into the Hideout (from {n} on to {t}: {where()})")


def _barred_floor(gid, key, came, floor, tiles, before, after, what, passed=None):
    for which, st_ in (("before", before), ("after", after)):
        st_()
        r = dun(key, came, (0, 0), floor)
        f = r.run.floor
        tiles_ = [tuple(t) for t in tiles]
        t = n = c = None
        for t in tiles_:
            n, c = beside(lambda q: f.inside(*q) and f.walkable(*q) and q not in f.exits and q not in tiles_, t)
            if n:
                break
        if not n:
            side(gid, which, False, f"no open tile beside {tiles_[:3]} on floor {floor} to step from")
            continue
        r.run.player = n; r.anim_from = r.partner = n
        go(c); settle()
        w = where()
        moved = (w[2] != n) or w[1] != floor or w[0] != key
        if passed:
            moved = passed(w, n)
        side(gid, which, (not moved) if which == "before" else moved, f"{what}: from {n} into {t} on floor {floor} -> {w} {said[:1]}")


def g_hideout():
    title("hideout_elevator_lift_key", "Rocket Hideout: the elevator runs only with the Lift Key (elevator panel checks flag 0x2A5, set on picking the key up on B4F)")
    _barred_floor("hideout_elevator_lift_key", "ROCKET_HIDEOUT", "CELADON_GAME_CORNER", 0, [(24, 25), (23, 25), (25, 25)],
                  lambda: at("liftkey"), lambda: at("liftkey", also=True), "the elevator door on B1F")
    _barred_floor("hideout_elevator_lift_key", "ROCKET_HIDEOUT", "CELADON_GAME_CORNER", 1, [(28, 16), (29, 16)],
                  lambda: at("liftkey"), lambda: at("liftkey", also=True), "the elevator door on B2F")


def g_hideout_door():
    title("hideout_b4f_door", "Rocket Hideout B4F: Giovanni's door (17-18,12-14) opens only once both guards (trainers 366, 367) are beaten")
    at("scope", flags=["got_lift_key"])
    r = open_map("ROCKET_HIDEOUT", "CELADON_GAME_CORNER"); r = settle()
    _floor(r, 3)
    f = r.run.floor
    guards = sorted((m.x, m.y) for m in f.movers if m.kind == "trainer")
    boss = next(((m.x, m.y) for m in f.movers if m.kind == "figure" and isinstance(m.payload, dict) and "GIOVANNI" in str(m.payload.get("text", "")).upper()), (19, 4))
    start = next((t for t in ((21, 24), (20, 24), (21, 22), (20, 22)) if f.walkable(*t)), None)
    can = flood_floor(f, start, [boss]) if start else None
    side("hideout_b4f_door", "before", can is False, f"both guards unbeaten (trainers on the floor: {guards}): a clear walk from the elevator {start} to Giovanni {boss} without touching them: {can}", "flood")
    _g = [i for i, t in enumerate(_area["ROCKET_HIDEOUT"]["trainer_pool"]) if t.get("spot_name") in ("Grunt B4F 2", "Grunt B4F 3")]

    def _guards(n):
        at("scope", flags=["got_lift_key"])
        story.defeated_trainers.pop("ROCKET_HIDEOUT", None)
        for i in _g[:n]:
            story.mark_trainer_defeated("ROCKET_HIDEOUT", i)
    _barred_floor("hideout_b4f_door", "ROCKET_HIDEOUT", "CELADON_GAME_CORNER", 3, [(17, 13), (18, 13), (17, 12), (18, 12)], lambda: _guards(0), lambda: _guards(2), "Giovanni's door (both guards beaten for the after side)")
    _guards(1)
    side("hideout_b4f_door", "before: one guard", not story.story_flags.get("hideout_b4f_door_open"), f"one guard beaten: the door stays shut (flag {story.story_flags.get('hideout_b4f_door_open')})", "data")
    _guards(2)
    r = open_map("ROCKET_HIDEOUT", "CELADON_GAME_CORNER"); r = settle()
    _floor(r, 3)
    f = r.run.floor
    side("hideout_b4f_door", "after", flood_floor(f, start, [boss]), f"both guards beaten: the door open, a walk from the elevator {start} to Giovanni {boss}", "flood")
    _pic = _tm["ROCKET_HIDEOUT"]["floors"][3]["roofs"]["_picture"]
    side("hideout_b4f_door", "picture", (_pic.get("until") or {}).get("flag") == "hideout_b4f_door_open" and _os.path.exists(_os.path.join("assets", "tiles", _pic["until"]["f"])),
         f"the floor is drawn with FireRed's shut door till then ({_pic.get('until')})", "data")
    story.defeated_trainers.pop("ROCKET_HIDEOUT", None)
    at("scope", flags=["got_lift_key", "hideout_giovanni_defeated"])
    story.sync_story_flags()
    side("hideout_b4f_door", "old save", bool(story.story_flags.get("hideout_b4f_door_open")), "a save that beat Giovanni before the door existed: open", "data")


def g_tower():
    title("tower_ghost", "Pokémon Tower 6F: the ghost (trigger 11,15 / 12,16, var 0x4059) can't be passed or fought without the Silph Scope")
    at("scope")
    r = dun("KANTO_POKEMON_TOWER", "LAVENDER_TOWN", (11, 14), 5)
    go("d"); st = settle()
    w = where()
    side("tower_ghost", "before", w == ("KANTO_POKEMON_TOWER", 5, (11, 14)), f"no Silph Scope: the ghost turns you back {w} {said[:1]}")
    r = dun("KANTO_POKEMON_TOWER", "LAVENDER_TOWN", (12, 14), 5)
    go("d"); settle()
    w = where()
    side("tower_ghost", "before: beside it", not (w[1] == 5 and w[2] and w[2][1] >= 15), f"...nor round its side (12,15) {w}")
    at("scope", also=True)
    r = dun("KANTO_POKEMON_TOWER", "LAVENDER_TOWN", (11, 14), 5)
    go("d"); st = settle(1500)
    side("tower_ghost", "after", not _is_map(st) or any("Marowak" in s or "MAROWAK" in s for s in said), f"with the Scope: the ghost shows itself and the battle starts ({type(st).__name__}) {said[:1]}")
    at("ghost", also=True)
    r = dun("KANTO_POKEMON_TOWER", "LAVENDER_TOWN", (11, 14), 5)
    go("dd"); settle()
    w = where()
    side("tower_ghost", "after: beaten", w[1] == 6 or (w[1] == 5 and w[2] and w[2][1] >= 15), f"the ghost laid to rest: on to 7F's stairs {w}")


def _tea(gid, key, came, floor, start, path):
    at("tea", flags=["visited_SAFFRON_CITY"] if False else [])
    r = dun(key, came, start, floor)
    go(path); settle(1500)
    side("saffron_gate_guards", "before", story.current_area_key == key, f"{gid}: no Tea: the thirsty guard turns you back {where()} {said[:1]}")
    at("tea", also=True)
    r = dun(key, came, start, floor)
    go(path); settle(1500)
    side("saffron_gate_guards", "after", story.current_area_key == "SAFFRON_CITY", f"{gid}: with the Tea: through to Saffron {where()} {said[:1]}")


def g_tea():
    title("saffron_gate_guards", "Saffron's four gatehouses: the guards want the Tea (triggers var 0x4062; checkflag 0x2A6 = Tea from the old lady in Celadon Mansion; one cup opens all four)")
    _tea("Route 5 gate", "KANTO_ROUTE_5", "CERULEAN_CITY", 2, (4, 3), "dddddd")
    _tea("Route 6 gate", "KANTO_ROUTE_6", "VERMILLION_CITY", 1, (4, 7), "uuuuuu")
    _tea("Route 7 gate", "KANTO_ROUTE_7", "CELADON_CITY", 1, (3, 5), "rrrrrrrr")
    _tea("Route 8 gate", "KANTO_ROUTE_8", "LAVENDER_TOWN", 1, (9, 5), "llllllll")


def _snorlax(gid, key, came, spot, frm, c, beyond):
    at("flute", flags=["visited_FUCHSIA_CITY"] if False else [])
    r = dun(key, came, frm)
    go(c); settle()
    w = where()
    side(gid, "before", w[2] == tuple(frm) and _is_map(g.current_state), f"no Poké Flute: Snorlax won't budge {w} {said[:1]}")
    at("flute", also=True)
    r = dun(key, came, frm)
    go(c); st = settle(1500)
    side(gid, "after", not _is_map(st) or any("woke" in s.lower() or "flute" in s.lower() for s in said), f"with the Flute: it wakes and the battle starts ({type(st).__name__}) {said[:2]}")
    at("flute", also=True, flags=[key + "_boss_defeated"])
    r = dun(key, came, frm)
    go(c + c); settle()
    w = where()
    side(gid, "after: beaten", w[2] == tuple(beyond) or (w[2] and w[2] != tuple(frm)), f"Snorlax gone: the way is clear {w}")


def g_snorlax():
    title("snorlax_route12", "Route 12: Snorlax on the pier at 14,70 (person hidden by flag 0x54; wakes only with flag 0x23D, the Poké Flute from Mr. Fuji)")
    _snorlax("snorlax_route12", "KANTO_ROUTE_12", "LAVENDER_TOWN", (14, 70), (14, 69), "d", (14, 71))
    title("snorlax_route16", "Route 16: Snorlax at 31,13 (hidden by flag 0x80; the same Flute)")
    _snorlax("snorlax_route16", "KANTO_ROUTE_16", "CELADON_CITY", (31, 13), (32, 13), "l", (30, 13))


def g_cycling():
    title("cycling_road_bicycle", "Cycling Road's gatehouses (Routes 16 and 18): no one on foot (trigger tiles in each gatehouse)")
    for key, came, tgt in (("KANTO_ROUTE_16", "CELADON_CITY", "KANTO_ROUTE_17"), ("KANTO_ROUTE_18", "FUCHSIA_CITY", "KANTO_ROUTE_17")):
        for which, st_ in (("before", lambda: at("bicycle")), ("after", lambda: at("bicycle", also=True))):
            st_()
            r = dun(key, came, (0, 0))
            f = r.run.floor
            ex = sorted(t for t, x in f.exits.items() if x == tgt)
            t = n = c = None
            for t in ex:
                n, c = beside(lambda q: f.inside(*q) and f.walkable(*q) and q not in f.exits, t)
                if n:
                    break
            r.run.player = n; r.anim_from = r.partner = n
            if which == "after":   # (watch for the moment you are on Route 17: its slope can roll you back out before you stand still)
                settle(); frames(2); r.step(*_D[c]); ok = arrive(tgt)
            else:
                go(c); settle(); ok = story.current_area_key == tgt
            side("cycling_road_bicycle", which, ok if which == "after" else not ok, f"{key} -> Route 17 {'with' if which == 'after' else 'without'} the Bicycle: {where()} {said[:1]}")


def g_silph_door():
    title("saffron_silph_door", "Saffron: the Rocket in Silph Co.'s doorway (person 6, moved on to 33,31 while flag 0x23C is unset) steps aside once Mr. Fuji is rescued")
    rocket = lambda v: {t: (o.get("text") or "").strip() for t, o in v._people().items() if "security for Silph" in json.dumps(o)}   # (11-17, Jordan: he stands IN the doorway, FireRed's 33,31, then is gone)
    at("ghost", flags=["visited_SAFFRON_CITY"], items=["TEA"])
    v = town("SAFFRON_CITY", "KANTO_ROUTE_5", (33, 32))
    who = rocket(v)
    go("uu"); settle()
    side("saffron_silph_door", "before", story.current_area_key == "SAFFRON_CITY" and who == {(33, 31): "Grunt"} and any("security" in s for s in said),
         f"Tower's ghost not yet beaten: the Rocket stands in Silph Co.'s doorway {who} and turns you back {where()} {said[:1]}")
    v = town("SAFFRON_CITY", "KANTO_ROUTE_5", (34, 31))
    go("l"); settle()
    side("saffron_silph_door", "before: no way round him", story.current_area_key == "SAFFRON_CITY" and not flood_town(v, (34, 31), [(33, 30)]),
         f"...and from beside him (34,31) the door can't be reached either: {where()}", "flood")
    at("flute", also=True, flags=["visited_SAFFRON_CITY"])
    v = town("SAFFRON_CITY", "KANTO_ROUTE_5", (33, 32))
    who = rocket(v)
    go("uu"); settle()
    side("saffron_silph_door", "after", story.current_area_key == "SILPH_CITY" and not who, f"Mr. Fuji rescued: the Rocket is gone ({who or 'nobody'}), into Silph Co. {where()} {said[:1]}")
    at("ghost", also=True, flags=["visited_SAFFRON_CITY"])
    v = town("SAFFRON_CITY", "KANTO_ROUTE_5", (33, 32))
    who = rocket(v)
    go("uu"); settle()
    side("saffron_silph_door", "before: Fuji", story.current_area_key == "SAFFRON_CITY" and who == {(33, 31): "Grunt"}, f"ghost beaten but Mr. Fuji not yet reached on 7F (FireRed: still shut): the Rocket {who}; {where()} {said[:1]}")
    at("ghost", also=True, flags=["visited_SAFFRON_CITY", "visited_SILPH_CITY"])
    v = town("SAFFRON_CITY", "KANTO_ROUTE_5", (33, 32))
    who = rocket(v)
    go("uu"); settle()
    side("saffron_silph_door", "old save", story.current_area_key == "SILPH_CITY" and not who, f"old-save allowance kept (Jordan 11-17): a save already inside Silph Co. under the old rule keeps its way in, the Rocket gone ({who or 'nobody'}): {where()}")


def g_cardkey():
    title("silph_card_key", "Silph Co.: the shut doors on every floor open with the Card Key (5F item ball, flag 0x192)")
    _barred_floor("silph_card_key", "SILPH_CITY", "SAFFRON_CITY", 1, [(5, 8), (6, 8), (5, 9), (6, 9)], lambda: at("cardkey"), lambda: at("cardkey", also=True), "a locked door on 2F")
    _barred_floor("silph_card_key", "SILPH_CITY", "SAFFRON_CITY", 10, [(5, 16), (6, 16), (5, 17), (6, 17)], lambda: at("cardkey"), lambda: at("cardkey", also=True), "the locked door on 11F")


def g_saffron_gym():
    title("saffron_gym_rocket", "Saffron Gym: a Rocket stands in the doorway (46,13; hidden by flag 0x3E, set when Giovanni is beaten on Silph's 11F)")
    at("silph")
    v = town("SAFFRON_CITY", "KANTO_ROUTE_5", (46, 14))
    go("uu"); settle()
    w = where()
    side("saffron_gym_rocket", "before", w[1] is None, f"Silph Co. still held: no way into the Gym {w} {said[:1]}")
    at("silph", also=True)
    v = town("SAFFRON_CITY", "KANTO_ROUTE_5", (46, 14))
    go("uu"); settle()
    w = where()
    side("saffron_gym_rocket", "after", w[1] == "gym", f"Silph Co. freed: into the Gym {w}")


def _wade(r):
    """From the shore step on to the sea: True if you end up on the water."""
    f = r.run.floor
    for y in range(1, f.h - 1):
        for x in range(1, f.w - 1):
            if f.tile(x, y) == _core.SURF or not f.walkable(x, y) or (x, y) in f.exits:
                continue
            for c, (dx, dy) in _D.items():
                n = (x + dx, y + dy)
                if f.tile(*n) == _core.SURF and n not in f.exits and str(f.decor.get(n, "")) == "" and str(f.decor.get((x, y), "")) == "":
                    r.run.player = (x, y); r.anim_from = r.partner = (x, y)
                    go(c); settle()
                    w = where()
                    return (w[0] == "KANTO_ROUTE_19" and w[2] == n), (x, y), n
    return None, None, None


def g_surf():
    title("surf_water", "The sea south of Fuchsia (Routes 19-21): Surf (FireRed: HM03 from the Safari Zone's Secret House, usable with the Soul Badge; ours: HM Surf comes with the Soul Badge)")
    for which, st_ in (("before", lambda: at("soul")), ("after", lambda: at("surf", also=True))):
        st_()
        v = town("FUCHSIA_CITY", "KANTO_ROUTE_15", (24, 36))
        ex = sorted(t for t, x in v.exits.items() if x == "KANTO_ROUTE_19")
        n = c = None
        for t in ex:
            n, c = beside(v._open, t, avoid=set(v.exits))
            if n:
                break
        v.player = n; v.anim = 0; v.anim_from = n
        go(c); st = settle()
        w = where()
        wet = _wade(st) if w[0] == "KANTO_ROUTE_19" and isinstance(st, DungeonState) and (_quiet(st) or True) else (None, None, None)
        has = story.inventory.get("HM_SURF", 0)
        if which == "before":
            side("surf_water", "before", not wet[0], f"four badges, no Surf: not out on the water (Fuchsia's south edge -> {w}; from the sand {wet[1]} on to the sea {wet[2]}: {wet[0]}; HM Surf in the Bag: {has}) {said[:1]}")
            side("surf_water", "deviation kept: the beach", w[0] == "FUCHSIA_CITY", f"Route 19's beach is shut without Surf (FireRed lets you walk it; Jordan keeps ours): from Fuchsia's south edge: {w}")
        else:
            side("surf_water", "after", wet[0], f"Soul Badge and Surf: on to Route 19 and out on the water ({w}, on the sea: {wet[0]})")
    at("surf", also=True, badges=4)
    r = dun("KANTO_ROUTE_19", "FUCHSIA_CITY", (0, 0))
    wet = _wade(r) if isinstance(r, DungeonState) else (None, None, None)
    side("surf_water", "before: no Soul Badge", wet[0] is False, f"HM Surf from the Secret House but no Soul Badge (FireRed: Surf won't work): from the sand {wet[1]} on to the sea {wet[2]}: {wet[0]}")


def g_cinnabar():
    title("cinnabar_gym_secret_key", "Cinnabar Gym: locked (trigger 20,5) till the Secret Key is picked up in the Mansion's basement (flag 0x1A8)")
    at("secretkey")
    v = town("CINNABAR_ISLAND", "KANTO_ROUTE_21", (20, 6))
    go("uu"); settle()
    w = where()
    closed = getattr(g.current_state, "gym_closed", lambda: None)()
    side("cinnabar_gym_secret_key", "before", w[1] is None, f"no Secret Key: the Gym's door is locked {w} {said[:1]} (inside, the Gym's own refusal: {closed!r})")
    at("secretkey", also=True)
    v = town("CINNABAR_ISLAND", "KANTO_ROUTE_21", (20, 6))
    go("uu"); settle()
    w = where()
    side("cinnabar_gym_secret_key", "after", w[1] == "gym", f"with the Secret Key: into the Gym {w}")
    at("secretkey", badges=7)   # (an old save: the Volcano Badge won before the door was locked, no key in the Bag)
    v = town("CINNABAR_ISLAND", "KANTO_ROUTE_21", (20, 6))
    go("uu"); settle()
    w = where()
    side("cinnabar_gym_secret_key", "old save", w[1] == "gym" and not story.inventory.get("SECRET_KEY"), f"old-save allowance kept (Jordan 11-17): a save with the Volcano Badge and no key still gets into the Gym {w}")


def g_viridian_gym():
    title("viridian_gym_badges", "Viridian Gym: locked (trigger 36,11, var 0x405A) till badges two to seven are won (Boulder can't be skipped: seven in all)")
    at("volcano")
    v = town("VIRIDIAN_CITY", "KANTO_ROUTE_1", (36, 12))
    go("uu"); settle()
    w = where()
    side("viridian_gym_badges", "before", w[1] is None and _is_map(g.current_state), f"six badges: locked {w} {said[:1]}")
    at("volcano", also=True)
    v = town("VIRIDIAN_CITY", "KANTO_ROUTE_1", (36, 12))
    go("uu"); settle()
    w = where()
    side("viridian_gym_badges", "after", w[1] == "gym", f"seven badges: into Giovanni's Gym {w}")


def g_league_gate():
    title("route22_league_gate", "Route 22's Pokémon League gate: the first guard wants the Boulder Badge (trigger 7,2 in the gatehouse, var 0x405F)")
    for which, nb in (("before", 0), ("after", 8)):
        at("earth", badges=nb)
        r = dun("KANTO_ROUTE_22", "VIRIDIAN_CITY", (7, 4), 1)
        go("uuu"); settle()
        ok = story.current_area_key == "KANTO_ROUTE_23"
        side("route22_league_gate", which, ok if which == "after" else not ok, f"{nb} badges: {where()} {said[:1]}")
    at("earth", badges=1)
    r = dun("KANTO_ROUTE_22", "VIRIDIAN_CITY", (7, 4), 1)
    go("uuu"); settle()
    side("route22_league_gate", "deviation kept: all eight", story.current_area_key == "KANTO_ROUTE_22", f"Route 22's gate wants all eight badges (FireRed: the Boulder Badge, the rest on Route 23; Jordan keeps ours): with one badge: {where()} {said[:1]}")
    title("route23_badge_guards", "Route 23: seven guards, one badge each (Cascade 15,149; Thunder 8,140; Rainbow 14,123; Soul 16,112; Marsh 10,94; Volcano 14,61; Earth 6,35)")
    guards = [("CASCADE", 2, 149), ("THUNDER", 3, 140), ("RAINBOW", 4, 123), ("SOUL", 5, 112), ("MARSH", 6, 94), ("VOLCANO", 7, 61), ("EARTH", 8, 35)]
    let_by = []
    for name, need, row in guards:
        at("earth")
        story.badges["KANTO"] = [b for b in BADGES if b != name]   # (every badge but this guard's)
        r = dun("KANTO_ROUTE_23", "KANTO_ROUTE_22", (0, 0))
        f = r.run.floor
        south = next(((x, row + 4) for x in range(f.w) if f.walkable(x, row + 4)), None)
        if _r23_walk(r, south, row - 3):
            let_by.append(name)
    side("route23_badge_guards", "before", not let_by, f"each guard met without his own badge (FireRed: turned back): guards who let you walk by: {let_by} (ours asks for all eight at Route 22's gatehouse as well)")
    at("earth", also=True)
    r = dun("KANTO_ROUTE_23", "KANTO_ROUTE_22", (0, 0))
    f = r.run.floor
    ex = sorted(t for t, x in f.exits.items() if x == "INDIGO_PLATEAU")
    n, c = beside(lambda q: f.inside(*q) and f.walkable(*q) and q not in f.exits, ex[0])
    r.run.player = n; r.anim_from = r.partner = n
    go(c); settle()
    side("route23_badge_guards", "after", story.current_area_key == "INDIGO_PLATEAU", f"all eight badges: out the top of Route 23 on to the Plateau {where()}")


def _r23_walk(r, start, north_row):
    """Walk north from start by real steps along a path the floor allows (land or water); True when a step lands at or above north_row."""
    f = r.run.floor
    if start is None:
        return None
    ok = lambda n: f.inside(*n) and (f.walkable(*n) or f.tile(*n) == _core.SURF) and n not in f.exits
    prev, q = {start: None}, deque([start])
    goal = None
    while q:
        cur = q.popleft()
        if cur[1] <= north_row:
            goal = cur; break
        for dx, dy in _D.values():
            n = (cur[0] + dx, cur[1] + dy)
            if n not in prev and ok(n):
                prev[n] = cur; q.append(n)
    if goal is None:
        return False   # (no path at all on the floor)
    path = []
    while goal != start:
        p = prev[goal]; path.append((goal[0] - p[0], goal[1] - p[1])); goal = p
    r.run.player = start; r.anim_from = r.partner = start
    for dx, dy in reversed(path):
        st = settle(300)
        if st is not r:
            return False
        before = tuple(r.run.player)
        r.step(dx, dy); frames(1); settle(300)
        if g.current_state is not r or tuple(r.run.player) == before:
            return False
        if tuple(r.run.player) != (before[0] + dx, before[1] + dy):
            return tuple(r.run.player)[1] <= north_row   # (pushed somewhere else)
    return True


def g_victory_road():
    title("victory_road_barriers", "Victory Road: four rock barriers, each lowered by pushing a Strength boulder on to its switch (trigger tiles, vars 0x4064-0x4067)")
    for fl, tiles, flag in ((0, [(12, 14), (12, 15)], "vr_switch_1f"), (1, [(13, 10), (13, 11)], "vr_switch_2f_w"), (1, [(33, 16), (33, 17)], "vr_switch_2f_e"), (2, [(12, 12), (12, 13)], "vr_switch_3f")):
        _barred_floor("victory_road_barriers", "VICTORY_ROAD", "KANTO_ROUTE_23", fl, tiles, lambda: at("earth", also=True), lambda flag=flag: at("earth", also=True, flags=[flag]),
                      f"the barrier ({flag})", passed=lambda w, n: w[2] != n)
    # the boulder itself: no Strength, no push
    at("earth", also=True, drop=["HM_STRENGTH"])
    r = dun("VICTORY_ROAD", "KANTO_ROUTE_23", (0, 0))
    said.clear()
    try:
        r._boulder((7, 18)); frames(3); settle(300)
        moved = type(g.current_state).__name__ != "DungeonState" or story.story_flags.get("vr_switch_1f")
    except Exception as ex:
        moved = f"error {ex}"
    side("victory_road_barriers", "before: Strength", not moved, f"no HM04: the switch's boulder on 1F (7,18) won't move ({moved}) {said[:1]} {getattr(r, 'toast', '')!r}")


def g_league():
    title("league_doors", "The Elite Four: each room's far door stays shut till its battle is won; the Champion's till the title is yours")
    rooms = [("league_lorelei", (6, 2), "league_won_INDIGO_PLATEAU_1"), ("league_bruno", (6, 2), "league_won_INDIGO_PLATEAU_2"),
             ("league_agatha", (6, 2), "league_won_INDIGO_PLATEAU_3"), ("league_lance", (6, 5), "league_won_INDIGO_PLATEAU_4"),
             ("league_champion", (6, 2), "hall_of_fame_due_INDIGO_PLATEAU")]
    won = []
    for room, door, flag in rooms:
        for which in ("before", "after"):
            at("earth", also=True, flags=won + ([flag] if which == "after" else []))
            v = town("INDIGO_PLATEAU", "KANTO_ROUTE_23", (door[0], door[1] + 1), room)
            w0 = where()
            go("u"); settle(1500)
            w = where()
            moved = w[1] != room or (w[2] and w[2] != w0[2])
            side("league_doors", which, moved if which == "after" else (not moved and w0[1] == room), f"{room}: door at {door}: {w0} -> {w} {said[:1]}")
        won.append(flag)


def g_cave():
    title("cerulean_cave_guard", "Cerulean Cave: FireRed's guard (1,13; hidden by flag 0x5C) leaves only after the Hall of Fame and the Sevii network job (ours: beat_champion and network_machine_fixed)")
    at("earth", also=True)
    v = town("CERULEAN_CITY", "KANTO_ROUTE_4", (2, 13))
    ex = next(t for t, x in v.exits.items() if x == "CERULEAN_CAVE")
    can = flood_town(v, (22, 20), [ex])
    side("cerulean_cave_guard", "before", not can, f"eight badges, not yet Champion: the cave mouth {ex} can be reached: {can}", "flood")
    at("earth", also=True, flags=["beat_champion", "move_offer_kanto"], items=["HM_SURF"])   # (move_offer: Mom's call about moving house already taken)
    v = town("CERULEAN_CITY", "KANTO_ROUTE_4", (2, 13))
    if not isinstance(v, _WTS):
        note("cerulean_cave_guard", f"with the Champion's flag set the game opens {type(v).__name__} instead of Cerulean, so the guard's leaving was not walked")
        return
    can = flood_town(v, (22, 20), [ex]) or flood_town(v, (2, 14), [ex]) or flood_town(v, (1, 14), [ex])
    side("cerulean_cave_guard", "before: Champion only", not can, f"Champion, the Sevii network job not done (FireRed: still shut): the cave mouth reachable: {can}", "flood")
    at("earth", also=True, flags=["network_machine_fixed"], items=["HM_SURF"])
    v = town("CERULEAN_CITY", "KANTO_ROUTE_4", (2, 13))
    can = flood_town(v, (22, 20), [ex]) or flood_town(v, (2, 14), [ex]) or flood_town(v, (1, 14), [ex])
    side("cerulean_cave_guard", "before: network only", not can, f"the network job done but not Champion: the cave mouth reachable: {can}", "flood")
    at("earth", also=True, flags=["beat_champion", "move_offer_kanto", "network_machine_fixed"], items=["HM_SURF"])
    v = town("CERULEAN_CITY", "KANTO_ROUTE_4", (2, 13))
    can = flood_town(v, (22, 20), [ex]) or flood_town(v, (2, 14), [ex]) or flood_town(v, (1, 14), [ex])
    v.player = (1, 13); v.anim = 0; v.anim_from = (1, 13)
    go("u"); settle()
    side("cerulean_cave_guard", "after", can and story.current_area_key == "CERULEAN_CAVE", f"Champion and the network job done: the guard gone (mouth reachable: {can}), in through the cave mouth: {where()} {getattr(g.current_state, 'toast', '')!r}")
    at("earth", also=True, flags=["beat_champion", "move_offer_kanto", "visited_CERULEAN_CAVE"], items=["HM_SURF"])   # (an old save: a Champion inside the cave under the old rule, the network job not done)
    v = town("CERULEAN_CITY", "KANTO_ROUTE_4", (2, 13))
    can = flood_town(v, (22, 20), [ex]) or flood_town(v, (2, 14), [ex]) or flood_town(v, (1, 14), [ex])
    v.player = (1, 13); v.anim = 0; v.anim_from = (1, 13)
    go("u"); settle()
    side("cerulean_cave_guard", "old save", can and story.current_area_key == "CERULEAN_CAVE", f"old-save allowance kept (Jordan 11-17): a Champion's save already inside the cave under the old rule keeps its way in without the network job (mouth reachable: {can}): {where()}")


def g_open():
    title("firered_open_ways", "Ways FireRed leaves open at this point of the story (a block here is a gate FireRed doesn't have)")
    at("ticket", also=True)   # (Bill's Ticket in hand, heading south to Vermilion for the first time)
    r = dun("KANTO_ROUTE_5", "CERULEAN_CITY", (0, 0))
    n, t = _edge_step(r, "UNDERGROUND_PATH")
    ok = arrive("UNDERGROUND_PATH", 300)
    side("open:underground_path_5_6", "firered: open", ok, f"Route 5's Underground Path (FireRed's only road to Vermilion before the Tea), first time through: from {n} on to {t}: {where()} {said[:1]}")
    at("cerulean", also=True)   # (just arrived in Cerulean: Misty before Bill, as FireRed allows)
    v = town("CERULEAN_CITY", "KANTO_ROUTE_4", (31, 23))
    go("uu"); v = settle()
    closed = getattr(v, "gym_closed", lambda: None)()
    side("open:cerulean_gym", "deviation kept: waits for Bill", bool(closed), f"Cerulean Gym before visiting Bill: Misty is away (FireRed: in from the start; Jordan keeps ours): {where()}; the Gym's own refusal: {closed!r}")
    at("ticket", also=True)   # (FireRed's Route 7 - Route 8 tunnel is open from the start too)
    for room, tgt in (("west", "KANTO_ROUTE_7"), ("east", "KANTO_ROUTE_8")):
        v = town("UNDERGROUND_PATH", "KANTO_ROUTE_5", (3, 3), room)
        ex = sorted(t for t, x in getattr(v, "exits", {}).items() if x == tgt)
        n, c = beside(v._open, ex[0], avoid=set(v.exits)) if ex else (None, None)
        if n:
            v.player = n; v.anim = 0; v.anim_from = n
            go(c)
        side("open:underground_path_7_8", "firered: open", bool(n) and arrive(tgt, 300), f"the Underground Path's {room} end, Lavender never visited: out to {tgt} (from {n} on to {ex[:1]}: {where()}) {getattr(g.current_state, 'toast', '')!r}")
    at("thunder", also=True, drop=["HM_CUT"], flags=["visited_LAVENDER_TOWN"])
    r = dun("KANTO_ROUTE_2", "VIRIDIAN_CITY", (0, 0))
    f = r.run.floor
    side("open:diglett_cave_route2", "firered: open", any(x == "DIGGLETT_CAVE" for x in f.exits.values()), f"Diglett's Cave's Route 2 mouth is on the map (coming out of it needs no HM in FireRed; Cut is only for crossing to Route 2's west side)", "data")


for _fn in (g_open, g_pallet, g_viridian, g_pewter, g_bridge, g_burgled, g_ssanne, g_cut, g_gamecorner, g_hideout, g_hideout_door, g_tower, g_tea, g_snorlax, g_cycling,
            g_silph_door, g_cardkey, g_saffron_gym, g_surf, g_cinnabar, g_viridian_gym, g_league_gate, g_victory_road, g_league, g_cave):
    guarded(_fn.__name__, _fn)

# =================================================================================================== where key items are handed out (data)
print("\nkey items: handed out where FireRed hands them out (read from the area data and the map data; not played)")
_area_all = g.loader.area_data["STORY_PROGRESSION"]
_txt = {k: json.dumps(v) for k, v in _area_all.items() if isinstance(v, dict)}
for k, v in _tm.items():
    _txt[k] = _txt.get(k, "") + json.dumps(v)
_code = {"SS_TICKET": ("src/states/overworld/town_kanto.py", "BILLS_HOUSE"), "POKE_FLUTE": ("src/states/overworld/town_kanto.py", "LAVENDER_TOWN"), "OLD_ROD": ("src/states/overworld/town_kanto.py", "VERMILLION_CITY"),
         "BICYCLE": ("src/states/systems/town_services.py", "CERULEAN_CITY")}   # (handed out by code, not data: the file that does it, and the town it serves)
_badge_src = open("src/world/story.py", encoding="utf-8").read()
_badge_src = _badge_src[_badge_src.index('"KANTO": [', _badge_src.index("region_badge_items = {")):]
_badge_gifts = {}   # (src/world/story.py, region_badge_items: what a Kanto badge also hands you, read from the code itself)
for _b, _i in _re.findall(r'\("([A-Z_]+)", "([A-Z_]+)"\)', _badge_src[:_badge_src.index("]")]):
    _badge_gifts.setdefault(_b, []).append(_i)


def given_in(item):
    out = []
    for k, s in _txt.items():
        for m in _re.finditer(r'"(gift_item|rewards|gift_items)": \{[^{}]*"%s"' % item, s):
            out.append(k + (" (a battle's prize)" if m.group(1) == "rewards" else "")); break
    if item in _code and _os.path.exists(_code[item][0]) and _re.search(r'(inventory|inv)\["%s"\] = ' % item, open(_code[item][0], encoding="utf-8").read()):
        out.append(_code[item][1] + " (in code)")
    out += [f"with the {b.title()} Badge (story.py)" for b, its in _badge_gifts.items() if item in its]
    from src.world import hms as _hms
    for b, hm in _hms.HM_BY_BADGE.get("KANTO", {}).items():
        if hm == item:
            out.append(f"the {b.title()} Badge (hms.py)")
    return out


GIFTS = [   # (our item, FireRed's place: our area key, FireRed's words for where)
    ("OAKS_PARCEL", "VIRIDIAN_CITY", "Viridian Mart's clerk"), ("OLD_AMBER", "PEWTER_CITY", "the Museum's back room (Cut)"),
    ("SS_TICKET", "BILLS_HOUSE", "Bill, Route 25"), ("BIKE_VOUCHER", "VERMILLION_CITY", "the Fan Club chairman, Vermilion"),
    ("BICYCLE", "CERULEAN_CITY", "Cerulean's Bike Shop, for the voucher"), ("OLD_ROD", "VERMILLION_CITY", "the Fishing Guru, Vermilion"),
    ("HM_CUT", "KANTO_SS_ANNE", "the S.S. Anne's Captain"), ("HM_FLASH", "KANTO_ROUTE_2", "Oak's aide, Route 2 gate (10 kinds)"),
    ("ITEMFINDER", "KANTO_ROUTE_11", "Oak's aide, Route 11 gate (30 kinds)"), ("COIN_CASE", "CELADON_CITY", "the man in Celadon's diner"),
    ("TEA", "CELADON_CITY", "the old lady, Celadon Mansion 1F"), ("LIFT_KEY", "ROCKET_HIDEOUT", "dropped by a grunt, Hideout B4F"),
    ("SILPH_SCOPE", "ROCKET_HIDEOUT", "left by Giovanni, Hideout B4F"), ("POKE_FLUTE", "LAVENDER_TOWN", "Mr. Fuji, at home after the Tower"),
    ("HM_FLY", "KANTO_ROUTE_16", "the girl in Route 16's hidden house"), ("CARD_KEY", "SILPH_CITY", "an item ball, Silph Co. 5F"),
    ("MASTER_BALL", "SILPH_CITY", "Silph's President, 11F"), ("EXP_SHARE", "KANTO_ROUTE_15", "Oak's aide, Route 15 gate (50 kinds)"),
    ("LUCKY_EGG", "KANTO_ROUTE_15", "ours, in the retired Exp. Share's place (Jordan 11-17): Oak's aide, Route 15 gate (50 kinds)"),
    ("SUPER_ROD", "KANTO_ROUTE_12", "the Fishing Guru's brother, Route 12"), ("GOOD_ROD", "FUCHSIA_CITY", "the Fishing Guru's older brother, Fuchsia"),
    ("HM_SURF", "SAFARI_ZONE", "the Secret House, Safari Zone"), ("GOLD_TEETH", "SAFARI_ZONE", "an item ball, Safari Zone west"),
    ("HM_STRENGTH", "FUCHSIA_CITY", "the Warden, for his Gold Teeth"), ("SECRET_KEY", "POKEMON_MANSION", "an item ball, Mansion B1F"),
    ("TRI_PASS", "ONE_ISLAND", "Celio, One Island (Bill takes you from Cinnabar after Blaine)"),
]
for item, place, words in GIFTS:
    got = given_in(item)
    if item in story.RETIRED_ITEMS:   # (the Exp. Share is an Option in this game: handed out nowhere; Route 15's aide gives a Lucky Egg in its place, Jordan 11-17)
        ok = not [x for x in got if (_area.get(x.split(" (")[0]) or {}).get("region", "KANTO") == "KANTO"]
        RESULTS.append(("gift:" + item, "data", ok, "data"))
        check(ok, f"[gift:{item}] (data): retired in this game (story.RETIRED_ITEMS): handed out nowhere in Kanto (FireRed: {words}); ours: {got or 'nowhere'}")
        continue
    ok = any(x == place or x.startswith(place + " (in code)") for x in got) and not any("Badge" in x for x in got) and (place + " (a battle's prize)") not in got
    RESULTS.append(("gift:" + item, "data", ok, "data"))
    check(ok, f"[gift:{item}] (data): FireRed: {words} [{place}]; ours: {got or 'nowhere found in the data'}")

# =================================================================================================== the moved key items, played
print("\nkey items moved to FireRed's places (11-16), played: given once; not to a save that already holds one")


def talk_town(key, came, room, who):
    """In a town's room, walk into who. True if they were there to talk to."""
    v = town(key, came, (1, 1), room)
    if not isinstance(v, _WTS):
        return False
    p = next((t for t, o in v._people().items() if (o.get("text") or "") == who), None)
    if p is None:
        return False
    n, c = beside(v._open, p, avoid=set(v.exits))
    if n is None:   # (across a counter or a table: stand two off)
        for c, (dx, dy) in _D.items():
            n = (p[0] - 2 * dx, p[1] - 2 * dy)
            if v._open(n):
                break
        else:
            return False
    v.player = n; v.anim = 0; v.anim_from = n
    go(c); settle(1500)
    return True


def talk_route(key, came, who, floors=14):
    """On a route or in a cave (its floors and rooms), walk into who."""
    r = open_map(key, came); r = settle()
    if not isinstance(r, DungeonState):
        return False
    for i in range(floors):
        try:
            _floor(r, i)
        except Exception:
            break
        f = r.run.floor
        m = next((m for m in f.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == who), None)
        if m is None:
            continue
        spot = (m.x, m.y)
        _quiet(r)
        n, c = beside(lambda q: f.inside(*q) and f.walkable(*q) and q not in f.exits and f.mover_at(*q) is None, spot)
        if n is None:
            return False
        r.run.player = n; r.anim = 0; r.anim_from = r.partner = r.partner_from = n
        go(c); settle(1500)
        return True
    return False


def gift(item, name, setup, talk, flag=None):
    """New save: the giver hands it over once (twice asked: still one). A save that already holds one: not a second."""
    setup(); story.inventory.pop(item, None)
    met = talk(); one = story.inventory.get(item, 0)
    again = talk(); two = story.inventory.get(item, 0)
    ok = bool(met) and one == 1 and two == 1 and (not flag or story.story_flags.get(flag))
    RESULTS.append(("gift:" + item, "played", ok, "steps"))
    check(ok, f"[gift:{item}] played (steps): {name}: found: {met}; in the Bag after talking: {one}, after talking again: {two}{'; flag ' + flag + ': ' + str(bool(story.story_flags.get(flag))) if flag else ''} {said[:1]}")
    setup(); story.inventory[item] = 1
    if flag:
        story.story_flags.pop(flag, None)
    talk(); kept = story.inventory.get(item, 0)
    RESULTS.append(("gift:" + item, "old save", kept == 1, "steps"))
    check(kept == 1, f"[gift:{item}] old save (steps): a save that already holds it gets no second one from {name}: in the Bag: {kept}")


def _run_gifts():
    gift("HM_SURF", "the Secret House man, Safari Zone", lambda: at("soul"), lambda: talk_route("SAFARI_ZONE", "FUCHSIA_CITY", "SECRET HOUSE MAN"), "got_hm_surf_kanto")
    gift("SUPER_ROD", "the Fishing Guru's brother, Route 12's house", lambda: at("snorlax", also=True), lambda: talk_route("KANTO_ROUTE_12", "LAVENDER_TOWN", "FISHING GURU"), "got_super_rod_kanto")
    gift("COIN_CASE", "the broke man in Celadon's diner", lambda: at("rainbow"), lambda: talk_town("CELADON_CITY", "KANTO_ROUTE_7", "restaurant", "Man"), "got_coin_case")
    gift("BIKE_VOUCHER", "the Fan Club chairman, Vermilion", lambda: at("vermilion", also=True), lambda: talk_town("VERMILLION_CITY", "KANTO_ROUTE_6", "fanclub", "Fan Club Chairman") or talk_town("VERMILLION_CITY", "KANTO_ROUTE_6", "fanclub", "Chairman"), "got_bike_voucher")
    at("vermilion", also=True, items=["BICYCLE"])
    talk_town("VERMILLION_CITY", "KANTO_ROUTE_6", "fanclub", "Fan Club Chairman"); talk_town("VERMILLION_CITY", "KANTO_ROUTE_6", "fanclub", "Chairman")
    ok = story.inventory.get("BIKE_VOUCHER", 0) == 0
    RESULTS.append(("gift:BIKE_VOUCHER", "old save: has the Bicycle", ok, "steps"))
    check(ok, f"[gift:BIKE_VOUCHER] old save (steps): a save that already rides the Bicycle gets no voucher: in the Bag: {story.inventory.get('BIKE_VOUCHER', 0)} {said[:1]}")
    # the Secret Key: an item ball (gone once taken), the Burglar only a battle
    at("secretkey")
    met = talk_route("POKEMON_MANSION", "CINNABAR_ISLAND", "SECRET KEY")
    ok = met and story.inventory.get("SECRET_KEY") == 1 and story.story_flags.get("got_secret_key")
    RESULTS.append(("gift:SECRET_KEY", "played", bool(ok), "steps"))
    check(ok, f"[gift:SECRET_KEY] played (steps): the item ball on the Mansion's basement table: found: {met}; in the Bag: {story.inventory.get('SECRET_KEY', 0)}; got_secret_key: {bool(story.story_flags.get('got_secret_key'))} {said[:1]}")
    again = talk_route("POKEMON_MANSION", "CINNABAR_ISLAND", "SECRET KEY")
    RESULTS.append(("gift:SECRET_KEY", "old save", not again and story.inventory.get("SECRET_KEY") == 1, "steps"))
    check(not again and story.inventory.get("SECRET_KEY") == 1, f"[gift:SECRET_KEY] old save (steps): with the key already taken (or won from the Burglar before) the ball is gone: still there: {again}; in the Bag: {story.inventory.get('SECRET_KEY', 0)}")
    _simon = next(o for o in _area["POKEMON_MANSION"]["route_menu"] if o.get("text") == "BURGLAR SIMON")
    ok = "SECRET_KEY" not in json.dumps(_simon) and _simon["event"]["flag"] != "got_secret_key"
    RESULTS.append(("gift:SECRET_KEY", "data", ok, "data"))
    check(ok, f"[gift:SECRET_KEY] (data): the Burglar on 3F is a battle of his own (flag {_simon['event'].get('flag')}), no key in his prize")
    # the Tri-Pass: Bill's boat from Cinnabar once Blaine is beaten, Celio hands the pass over
    for nm, st_, want in (("six badges", lambda: at("volcano"), False), ("the Volcano Badge", lambda: at("volcano", also=True), True)):
        st_()
        v = town("CINNABAR_ISLAND", "KANTO_ROUTE_21", (14, 6))
        opt = next((o for o in v.area_data.get("travel_options", []) if o.get("target_area") == "ONE_ISLAND"), None)
        ok = opt is not None and bool(v._shown(opt)) == want
        RESULTS.append(("gift:TRI_PASS", "the boat: " + nm, ok, "data"))
        check(ok, f"[gift:TRI_PASS] Bill's boat from Cinnabar to One Island with {nm}, no Tri-Pass: offered: {opt is not None and bool(v._shown(opt))} (FireRed: after Blaine)")
    gift("TRI_PASS", "Celio, One Island's Network Center", lambda: at("volcano", also=True), lambda: talk_town("ONE_ISLAND", "KINDLE_ROAD", "center", "Celio's Tri-Pass"), "got_tri_pass")


guarded("gifts", _run_gifts)
story.current_area_key = "PALLET_TOWN"

# =================================================================================================== follow-up decisions (Jordan 11-17), played
print("\nfollow-up decisions (11-17), played: Route 15's aide, fishing from a town's shore, the Rocket's doorway is above, Viridian Gym's Macho Brace")


def _run_followups():
    from src.dungeon import art as _art
    from src.states.overworld.route_actions import RouteActions as _RA
    # Route 15's aide: a Lucky Egg for fifty kinds caught (FireRed: the Exp. Share, retired here), once
    try:
        for n, want in ((49, 0), (50, 1), (50, 1)):
            if n == 49:
                at("soul"); story.inventory.pop("LUCKY_EGG", None); story.story_flags.pop("got_lucky_egg_kanto", None)
            story.kanto_caught_count = lambda _n=n: _n
            said.clear()
            met = talk_route("KANTO_ROUTE_15", "FUCHSIA_CITY", "OAK'S AIDE")
            have = story.inventory.get("LUCKY_EGG", 0)
            where_ = getattr(g.current_state, "_floor_name", lambda i: "?")(getattr(getattr(g.current_state, "run", None), "index", 0))
            side("gift:LUCKY_EGG", f"played: {n} kinds" + (" again" if (n, want) == (50, 1) and story.story_flags.get("_egg_once") else ""), bool(met) and have == want and bool(story.story_flags.get("got_lucky_egg_kanto")) == bool(want),
                 f"Oak's aide upstairs in Route 15's gatehouse ({where_}) with {n} kinds caught: Lucky Eggs in the Bag: {have} (wanted {want}) {said[-1:]}")
            if want:
                story.story_flags["_egg_once"] = True
    finally:
        story.__dict__.pop("kanto_caught_count", None); story.story_flags.pop("_egg_once", None)
        story.inventory.pop("LUCKY_EGG", None); story.story_flags.pop("got_lucky_egg_kanto", None)
    # fishing from a town's shore: Vermilion, where LeafGreen has Staryu on the Super Rod
    key = "VERMILLION_CITY"
    table = g.loader.area_data[key + "_SUPER_ROD_PERCENTAGES"]
    at("soul", also=True, items=["SUPER_ROD"])
    v = town(key, "KANTO_ROUTE_6", (1, 1))
    shore = next(((x, y) for y in range(v.h) for x in range(v.w) if v.rows[y][x] == "." and v._open((x, y)) and (x, y) not in v.exits
                  and any(0 <= x + a < v.w and 0 <= y + b < v.h and (v.grid[y + b][x + a] == "~" or v.grid[y + b][x + a] in _art.SEA_CHARS) for a, b in _D.values())), None)
    v.player = shore; v.anim = 0; v.anim_from = shore
    spot, button = v._fish_spot(), next((b for b in v._buttons() if b[1] == "FISH"), None)
    if button:
        button[3]()   # (the FISH button, as a player presses it)
    play(lambda: isinstance(g.current_state, WildBattleState), 900)
    b = g.current_state
    foe = getattr(getattr(b, "opponent_pokemon", None), "id", None)
    ok = isinstance(b, WildBattleState) and (str(foe) in table or (foe == 129 and "130" in table)) and any("bite" in s for s in said)
    side("town_fishing", "with a rod", bool(spot and button) and ok, f"Vermilion, on the shore at {shore} beside the water {spot} with the Super Rod: the FISH button {'shows' if button else 'is missing'}; a bite: {type(b).__name__} #{foe} (the town's Super Rod table: {sorted(table)})")
    if isinstance(b, WildBattleState):
        b.on_flee_complete(); frames(3); settle()
    side("town_fishing", "back to the town", where() == (key, None, shore), f"...and after the battle you stand where you fished: {where()}")
    v = settle()
    bites = set()
    if isinstance(v, _WTS):
        for _ in range(80):
            m = _RA._fish_bite(v)
            bites.add(m.id if m is not None else None)
    side("town_fishing", "Staryu", 120 in bites, f"...Staryu bites there (LeafGreen's place for it; 80 casts: {sorted(x for x in bites if x)})")
    story.inventory.pop("SUPER_ROD", None)
    v = town(key, "KANTO_ROUTE_6", shore)
    side("town_fishing", "without a rod", v._fish_spot() is None and not any(b[1] == "FISH" for b in v._buttons()), f"...no rod: no FISH button ({[b[1] for b in v._buttons()]})")
    at("soul", also=True, items=["SUPER_ROD"])
    v = town(key, "KANTO_ROUTE_6", (57, 8), room="harbor")   # (the dock, a room of Vermilion's that is out of doors: LeafGreen's Staryu spot)
    dock = v._fish_spot() if isinstance(v, _WTS) else None
    v = town("CERULEAN_CITY", "KANTO_ROUTE_4", (1, 1), room="gym")
    pool = next(((x, y) for y in range(v.h) for x in range(v.w) if v._open((x, y)) and any(0 <= x + a < v.w and 0 <= y + b < v.h and v.grid[y + b][x + a] in "~o" for a, b in _D.values())), None)
    if pool:
        v.player = pool
    side("town_fishing", "the dock, not indoors", bool(dock) and pool is not None and v._fish_spot() is None,
         f"...on Vermilion's dock (the harbour room) you can cast too (water at {dock}); beside Cerulean Gym's pool at {pool} you can't ({v._fish_spot()})")
    dry = [k for k in ("LAVENDER_TOWN", "SAFFRON_CITY", "PEWTER_CITY") if _area[k].get("can_fish")]
    side("town_fishing", "towns without water", not dry, f"...Lavender, Saffron and Pewter have no rod tables and can't be fished in ({dry})", "data")
    wet_ = (_core.WATER, _core.SURF)
    for rk, came in (("KANTO_ROUTE_6", "VERMILLION_CITY"), ("KANTO_ROUTE_22", "VIRIDIAN_CITY"), ("CERULEAN_CAVE", "CERULEAN_CITY"), ("SEAFOAM_ISLANDS", "KANTO_ROUTE_20")):
        at("soul", also=True, items=["SUPER_ROD"])
        r = dun(rk, came, (0, 0))
        land = act = None
        for i in range(14):   # (the first floor with a bank to stand on)
            try:
                if i:
                    _floor(r, i)
            except Exception:
                break
            f = r.run.floor
            land = next(((x, y) for y in range(f.h) for x in range(f.w) if f.walkable(x, y) and f.tile(x, y) not in wet_ and (x, y) not in f.exits and f.mover_at(x, y) is None
                         and any(f.tile(x + a, y + b_) in wet_ for a, b_ in _D.values())), None)
            if land:
                _quiet(r)
                r.run.player = land; r.anim = 0; r.anim_from = r.partner = r.partner_from = land
                act = r._act_here()
                break
        side("route_fishing", rk, bool(land) and bool(act) and act[0] == "FISH", f"{rk} with a rod, on a bank ({r._floor_name(r.run.index)}, {land}): the map offers {act[0] if act else None} (FireRed has rod Pokemon here; can_fish was missing)")
    r4 = _tm["KANTO_ROUTE_4"]
    side("route_fishing", "KANTO_ROUTE_4: no water on our map", _area["KANTO_ROUTE_4"].get("can_fish") and not any(c in "~o" for row in r4["art"] for c in row),
         "Route 4 has its rod tables and can_fish, but our map has no water tile (FireRed's corner pond, reached by Surf from Cerulean, is walled: nothing is on it), so there is nowhere to cast", "data")
    # Viridian Gym's hidden Macho Brace: on Giovanni's tile, there to find only once he is beaten
    flag = "hidden_VIRIDIAN_CITY_gym_2_2"
    for which, also in (("before", False), ("after", True)):
        at("earth", also=also); story.inventory.pop("MACHO_BRACE", None); story.story_flags.pop(flag, None)
        v = town("VIRIDIAN_CITY", "VIRIDIAN_CITY", (2, 4), room="gym")
        go("u"); said.clear(); go("u")
        have = story.inventory.get("MACHO_BRACE", 0)
        if which == "before":
            side("viridian_gym_macho_brace", "before", have == 0 and not story.story_flags.get(flag), f"Giovanni not beaten: walking into him finds nothing (in the Bag: {have}); the game goes to {type(g.current_state).__name__}")
        else:
            found = any("MACHO BRACE" in s for s in said)
            tap(g.current_state); settle(); go("u")
            side("viridian_gym_macho_brace", "after", have == 1 and found and story.inventory.get("MACHO_BRACE", 0) == 1,
                 f"with the Earth Badge: walking onto his tile finds the Macho Brace once (in the Bag: {have}, then {story.inventory.get('MACHO_BRACE', 0)} after walking in again) {said[:1]}")
    story.inventory.pop("MACHO_BRACE", None); story.story_flags.pop(flag, None)


guarded("followups", _run_followups)
story.current_area_key = "PALLET_TOWN"

# =================================================================================================== the list itself
_gates_file = _os.path.normpath(_os.path.join(_os.getcwd(), "..", "..", "kanto_handoff", "kanto_rom_tools", "kanto_gates.json"))
if _os.path.exists(_gates_file):
    _gl = json.load(open(_gates_file, encoding="utf-8"))
    _ids = [x["id"] for x in _gl.get("gates", [])]
    _done = {r[0] for r in RESULTS if r[2] is not None}
    _not = [i for i in _ids if i not in _done]
    print(f"\nthe gate list: {len(_ids)} main-story gates in kanto_gates.json; tested here: {len([i for i in _ids if i in _done])}; listed but not stepped: {_not}")
    for i in _not:
        _why = next((x.get("check") for x in _gl["gates"] if x["id"] == i), None)
        print(f"   not stepped  [{i}] {_why or ''}")
else:
    print(f"\n(the gate list was not found at {_gates_file}: the gates above are the check's own)")

print("\nsummary by gate (ok / checks):")
_by = {}
for gid, which, ok, method in RESULTS:
    _by.setdefault(gid, []).append(ok)
for gid, oks in _by.items():
    _n = [o for o in oks if o is not None]
    print(f"   {'ok ' if all(_n) else 'XX '} {gid}: {sum(_n)}/{len(_n)}" + (f" (+{len(oks) - len(_n)} not verified)" if len(_n) < len(oks) else ""))
_meth = {}
for gid, which, ok, method in RESULTS:
    _meth.setdefault(method, set()).add(gid)
print("\nmethod used (gates and key items): " +"; ".join(f"{m}: {len(v)}" for m, v in sorted(_meth.items()) if m != "none"))
print(f"\n##### {len(fails)} failures")
