# Johto's story gates, both sides (SWEEP_RULES Part 3 item 12; ROADMAP_JOHTO batch J2, 11-23). The gate list comes from
# HeartGold/SoulSilver's own event scripts (pret's pokeheartgold decomp), with Crystal's (pret's pokecrystal) where they differ:
# kanto_handoff/johto_check/gates/johto_gates.json (hg_scan.py reads the scripts). Here each gate is met on our walked maps with
# real steps: BEFORE (the story just short of what opens it: you must not get past) and AFTER (it granted: you must get past).
# The story state comes from the Journal playthrough's own record (TIMELINE: what each mission added, in order).
# A FAIL is a finding, not something to patch here: see kanto_handoff/johto_check/GATES.md.
#   bash dev/checks/run.sh johto_gates        (-v for every line)
_src = open("dev/checks/kanto_maps_body.py", encoding="utf-8").read()
exec(_src[:_src.index("# ---- every rebuilt map")])
from src.dungeon import core as _core

story.starting_region = "JOHTO"
_D = {"u": (0, -1), "d": (0, 1), "l": (-1, 0), "r": (1, 0)}
_BATTLE = (TrainerIntroState, TrainerBattleState)

TIMELINE = [  # (from johto_playthrough's result.json, 11-23 run; HM Whirlpool added after the Hideout: Lance gives it in talk)
    ('johto_m1', [('flag', 'purify_chamber'), ('flag', 'has_johto_starter'), ('flag', 'johto_rival_met_in_lab'), ('flag', 'kanto_gifts_v2'), ('flag', 'received_starter_johto'), ('flag', 'starter_johto'), ('flag', 'johto_lyra_after'), ('flag', 'johto_elm_number'), ('flag', 'johto_elm_number_scene'), ('flag', 'johto_lyra_lesson'), ('flag', 'johto_lyra_lesson_scene'), ('flag', 'visited_JOHTO_ROUTE_29'), ('flag', 'got_map_card_johto'), ('flag', 'johto_gent_tour'), ('flag', 'visited_CHERRYGROVE_CITY'), ('item', 'MAP_CARD'), ('flag', 'visited_JOHTO_ROUTE_30'), ('flag', 'visited_MR_POKEMONS_HOUSE'), ('flag', 'met_mr_pokemon'), ('flag', 'received_pokedex_johto'), ('item', 'MYSTERY_EGG')]),
    ('johto_m2', [('flag', 'defeated_rival_cherrygrove'), ('flag', 'johto_police_scene'), ('flag', 'got_potions_elm_aide'), ('flag', 'elm_received_egg'), ('drop', 'MYSTERY_EGG')]),
    ('johto_m3', [('flag', 'visited_JOHTO_ROUTE_31'), ('flag', 'visited_VIOLET_CITY'), ('flag', 'visited_SPROUT_TOWER'), ('flag', 'johto_silver_sprout'), ('flag', 'defeated_elder_li'), ('item', 'HM_FLASH'), ('item', 'LEAF_STONE')]),
    ('johto_m4', [('flag', 'gym_challenge_VIOLET_CITY'), ('flag', 'gym_challenge_done_VIOLET_CITY'), ('flag', 'gym_progress_VIOLET_CITY'), ('flag', 'league_won_VIOLET_CITY_3'), ('item', 'JOHTO_MAP'), ('badge', 'ZEPHYR')]),
    ('johto_m5', [('flag', 'got_togepi_egg'), ('flag', 'visited_JOHTO_ROUTE_32'), ('flag', 'visited_UNION_CAVE'), ('flag', 'visited_JOHTO_ROUTE_33'), ('flag', 'visited_AZALEA_TOWN'), ('flag', 'johto_azalea_rocket'), ('flag', 'visited_ILEX_FOREST'), ('flag', 'kurt_went_to_well'), ('flag', 'visited_SLOWPOKE_WELL'), ('flag', 'slowpoke_well_cleared')]),
    ('johto_m6', [('flag', 'defeated_rival_azalea'), ('flag', 'gym_challenge_AZALEA_TOWN'), ('flag', 'gym_challenge_done_AZALEA_TOWN'), ('flag', 'gym_progress_AZALEA_TOWN'), ('flag', 'league_won_AZALEA_TOWN_5'), ('item', 'OLD_ROD'), ('item', 'VS_SEEKER'), ('badge', 'HIVE')]),
    ('johto_m7a', [('flag', 'ilex_farfetchd_1'), ('flag', 'ilex_farfetchd_2'), ('flag', 'got_hm_cut_johto'), ('item', 'HM_CUT')]),
    ('johto_m7', [('flag', 'visited_JOHTO_ROUTE_34'), ('flag', 'johto_lyra_daycare'), ('flag', 'visited_GOLDENROD_CITY')]),
    ('johto_m8', [('flag', 'visited_JOHTO_ROUTE_35'), ('flag', 'visited_JOHTO_ROUTE_36'), ('flag', 'saw_odd_tree'), ('flag', 'got_kenya'), ('flag', 'feat_johto_trainers_1'), ('flag', 'gym_challenge_GOLDENROD_CITY'), ('flag', 'gym_challenge_done_GOLDENROD_CITY'), ('flag', 'gym_progress_GOLDENROD_CITY'), ('flag', 'league_won_GOLDENROD_CITY_6'), ('item', 'SQUIRT_BOTTLE'), ('badge', 'PLAIN')]),
    ('johto_m9', [('flag', 'defeated_sudowoodo'), ('flag', 'visited_JOHTO_ROUTE_37'), ('flag', 'visited_ECRUTEAK_CITY'), ('flag', 'visited_BURNED_TOWER'), ('flag', 'defeated_rival_burned_tower'), ('flag', 'johto_beasts_fled')]),
    ('johto_m10', [('flag', 'gym_challenge_ECRUTEAK_CITY'), ('flag', 'gym_challenge_done_ECRUTEAK_CITY'), ('flag', 'gym_progress_ECRUTEAK_CITY'), ('flag', 'league_won_ECRUTEAK_CITY_7'), ('item', 'AMULET_COIN'), ('item', 'SUPER_ROD'), ('badge', 'FOG')]),
    ('johto_m11', [('flag', 'visited_ECRUTEAK_DANCE_THEATER'), ('flag', 'beat_theater_grunt'), ('flag', 'got_hm_surf_theater'), ('item', 'HM_SURF'), ('flag', 'visited_JOHTO_ROUTE_38'), ('flag', 'visited_JOHTO_ROUTE_39'), ('flag', 'visited_OLIVINE_CITY'), ('flag', 'visited_OLIVINE_LIGHTHOUSE_FLOORS'), ('flag', 'visited_OLIVINE_LIGHTHOUSE_BALCONY'), ('flag', 'visited_OLIVINE_LIGHTHOUSE'), ('flag', 'jasmine_explained'), ('flag', 'visited_JOHTO_ROUTE_40'), ('flag', 'visited_JOHTO_ROUTE_41'), ('flag', 'visited_CIANWOOD_CITY'), ('item', 'SECRET_POTION')]),
    ('johto_m12', [('flag', 'cianwood_gym_waterfall_off'), ('flag', 'defeated_eusine'), ('flag', 'johto_suicune_cianwood'), ('flag', 'got_shuckie'), ('flag', 'gym_challenge_CIANWOOD_CITY'), ('flag', 'gym_challenge_done_CIANWOOD_CITY'), ('flag', 'gym_progress_CIANWOOD_CITY'), ('flag', 'league_won_CIANWOOD_CITY_5'), ('item', 'ROCK_SMASHER'), ('badge', 'STORMBADGE')]),
    ('johto_m13', [('flag', 'ampharos_cured'), ('drop', 'SECRET_POTION'), ('flag', 'gym_challenge_OLIVINE_CITY'), ('flag', 'gym_challenge_done_OLIVINE_CITY'), ('flag', 'gym_progress_OLIVINE_CITY'), ('flag', 'league_won_OLIVINE_CITY_3'), ('badge', 'MINERAL')]),
    ('johto_m14', [('flag', 'visited_JOHTO_ROUTE_42'), ('flag', 'got_hm_strength_mortar'), ('flag', 'johto_strength_hiker'), ('flag', 'visited_MAHOGANY_TOWN'), ('item', 'HM_STRENGTH'), ('flag', 'visited_JOHTO_ROUTE_43'), ('flag', 'visited_LAKE_OF_RAGE'), ('flag', 'defeated_red_gyarados'), ('flag', 'visited_ROCKET_HQ'), ('item', 'GUARD_SPEC'), ('item', 'ESCAPE_ROPE'), ('flag', 'rocket_hq_cleared'), ('item', 'HM_WHIRLPOOL')]),
    ('johto_m15', [('flag', 'hq_electrode_3'), ('flag', 'hq_electrode_2'), ('flag', 'gym_challenge_MAHOGANY_TOWN'), ('flag', 'gym_challenge_done_MAHOGANY_TOWN'), ('flag', 'gym_progress_MAHOGANY_TOWN'), ('flag', 'league_won_MAHOGANY_TOWN_8'), ('item', 'ICE_MELTER'), ('badge', 'GLACIER')]),
    ('johto_m15b', [('item', 'MAX_REVIVE'), ('flag', 'radio_takeover_started'), ('flag', 'visited_RADIO_TOWER'), ('item', 'BASEMENT_KEY'), ('flag', 'visited_GOLDENROD_UNDERGROUND'), ('flag', 'salon_older'), ('flag', 'salon_younger'), ('flag', 'warehouse_switch_3'), ('flag', 'got_radio_card_key'), ('item', 'CARD_KEY'), ('flag', 'radio_tower_cleared'), ('item', 'ESCAPE_ROPE')]),
    ('johto_m16', [('flag', 'feat_johto_steps_1'), ('flag', 'visited_JOHTO_ROUTE_44'), ('flag', 'visited_ICE_PATH'), ('item', 'HM_WATERFALL'), ('flag', 'visited_BLACKTHORN_CITY'), ('flag', 'gym_challenge_BLACKTHORN_CITY'), ('flag', 'gym_challenge_done_BLACKTHORN_CITY'), ('flag', 'gym_progress_BLACKTHORN_CITY'), ('flag', 'johto_beat_clair'), ('flag', 'league_won_BLACKTHORN_CITY_8'), ('item', 'MT_SILVER_MAP'), ('flag', 'visited_DRAGONS_DEN'), ('flag', 'visited_DRAGON_SHRINE'), ('flag', 'dragon_quiz_done'), ('item', 'HM_ROCK_CLIMB'), ('badge', 'RISING')]),
    ('johto_m17b', [('flag', 'visited_BELLCHIME_TRAIL'), ('flag', 'wise_trio_beaten'), ('flag', 'visited_BELL_TOWER'), ('flag', 'got_rainbow_wing'), ('item', 'RAINBOW_WING')]),
    ('johto_m17', [('flag', 'visited_RUINS_OF_ALPH'), ('item', 'UNOWN_REPORT'), ('flag', 'got_repel_johto_route_32_r32_11_94'), ('flag', 'got_miracle_seed_johto_route_32'), ('item', 'MIRACLE_SEED'), ('flag', 'got_leppa_berry_johto_route_32_r32_8_49'), ('item', 'LEPPA_BERRY'), ('flag', 'visited_KANTO_ROUTE_27'), ('flag', 'visited_TOHJO_FALLS'), ('flag', 'visited_KANTO_ROUTE_26'), ('flag', 'border_region'), ('flag', 'visited_POKEMON_LEAGUE_GATE'), ('flag', 'visited_JOHTO_VICTORY_ROAD'), ('flag', 'defeated_rival_victory_road_johto'), ('flag', 'visited_SILVER_LEAGUE_PLATEAU'), ('item', 'MAX_REVIVE'), ('flag', 'gym_progress_SILVER_LEAGUE_PLATEAU'), ('flag', 'league_won_SILVER_LEAGUE_PLATEAU_1'), ('flag', 'league_won_SILVER_LEAGUE_PLATEAU_2'), ('flag', 'league_won_SILVER_LEAGUE_PLATEAU_3'), ('flag', 'beat_johto_elite_four'), ('flag', 'league_won_SILVER_LEAGUE_PLATEAU_4'), ('flag', 'beat_johto_champion'), ('flag', 'hall_of_fame_count_johto'), ('flag', 'hall_of_fame_records'), ('flag', 'move_offer_johto'), ('item', 'MASTER_BALL'), ('item', 'SS_TICKET')]),
    ('johto_m18', [('flag', 'visited_KANTO_ROUTE_28'), ('flag', 'visited_MT_SILVER_CITY'), ('flag', 'visited_MT_SILVER'), ('flag', 'defeated_red'), ('item', 'MASTER_BALL')]),
]
_EVENTS = [e for _m, ev in TIMELINE for e in ev]
_FLAGS = {e[1] for e in _EVENTS if e[0] == "flag"}
_ITEMS = {e[1] for e in _EVENTS if e[0] in ("item", "drop")}
_BASE_FLAGS = dict(story.story_flags)
_EXTRA = set()   # (flags / items a test laid on top: taken away again before the next state)


def at(opener, also=False, flags=(), items=(), drop=()):
    """The story just BEFORE opener ("flag:x", "item:X", "badge:Z", "mission:johto_mN" = that mission's start), or just after
    it (also=True). Extra flags / items on top; drop takes flags or items away."""
    kind, name = opener.split(":", 1)
    if kind == "mission":
        n = sum(len(ev) for m, ev in TIMELINE[:[m for m, _ in TIMELINE].index(name)])
        n += len(TIMELINE[[m for m, _ in TIMELINE].index(name)][1]) if also else 0
    else:
        n = next(i for i, e in enumerate(_EVENTS) if e[0] == {"drop": "drop"}.get(kind, kind) and e[1] == name) + (1 if also else 0)
    _EXTRA.update(flags); _EXTRA.update(items)
    for f in _FLAGS | _EXTRA:
        story.story_flags.pop(f, None)
    for i in _ITEMS | _EXTRA:
        story.inventory.pop(i, None)
    badges = []
    for e in _EVENTS[:n]:
        if e[0] == "flag":
            story.story_flags[e[1]] = True
        elif e[0] == "item":
            story.inventory[e[1]] = 1
        elif e[0] == "drop":
            story.inventory.pop(e[1], None)
        elif e[0] == "badge":
            badges.append(e[1])
    story.badges["JOHTO"] = badges
    for f in flags:
        story.story_flags[f] = True
    for i in items:
        story.inventory[i] = 1
    for d_ in drop:
        story.story_flags.pop(d_, None); story.inventory.pop(d_, None)
    for f in [f for f in story.story_flags if f.startswith("badge_") or f.startswith("has_")]:
        pass


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
        settle(); frames(2)
        st = settle()
        if not _is_map(st):
            print(f"      (walk stopped by {type(st).__name__} at {where()})")
            break
        st.step(*_D[c])
        frames(1)
    settle(); frames(4)
    return settle()


def walk_path(path):
    """go(), but each step is tried again (a few frames apart) while someone walking about stands in the way, as a player
    waits: a step that never lands is the gate holding (the walk stops there)."""
    for c in path:
        st = g.current_state
        if isinstance(st, DungeonState):   # (wild Pokemon wander back in: bumping one opens the catch menu)
            st.run.floor.movers = [m for m in st.run.floor.movers if m.kind != "wild"]
            st.encounter_free = 999
        before = where()
        for _ in range(12):
            go(c)
            now = where()
            if now != before or not _is_map(g.current_state):
                break
            frames(20)
        if not _is_map(g.current_state) or where() == before:
            return


def where():
    st = g.current_state
    if isinstance(st, _WTS):
        return (story.current_area_key, st.room, tuple(st.player))
    if isinstance(st, DungeonState):
        return (story.current_area_key, st.run.index, tuple(st.run.player))
    return (story.current_area_key, type(st).__name__, None)


def place(key, came, pos, room=None, floor=0):
    """Stand on our map KEY (a town's room, or a route/cave floor) at pos."""
    if _area[key].get("area_type") == "town":
        if room:
            g.walk_town_pos = (key, tuple(pos) if pos else (1, 1), (0, -1)); g.walk_town_room = (key, room)
            story.current_area_key, story.last_area_key = key, came
            g.change_state(CityState(g)); frames(2); tap(g.current_state)
            v = settle()
        else:
            v = open_map(key, came); v = settle()
        if isinstance(v, _WTS) and pos:
            v.player = tuple(pos); v.anim = 0; v.anim_from = tuple(pos)
        return v
    r = open_map(key, came); r = settle()
    if not isinstance(r, DungeonState):
        return r
    if r.run.index != floor:
        while len(r.run.floors) <= floor:
            r.run.enter_floor(len(r.run.floors))
        r.run.enter_floor(floor); frames(2)
    r.run.floor.movers = [m for m in r.run.floor.movers if m.kind not in ("wild", "trainer")]   # (sight trainers would stop the walk: the gates are what's tested)
    if pos:
        r.run.player = tuple(pos); r.anim = 0; r.anim_from = r.partner = r.partner_from = tuple(pos)
    r.encounter_free = 999
    return r


def passed(goal):
    """goal: an area key (you are there), (area, tile) or (area, floor/room, tile)."""
    w = where()
    if isinstance(goal, str):
        return w[0] == goal
    if len(goal) == 2:
        return w[0] == goal[0] and w[2] == tuple(goal[1])
    return w[0] == goal[0] and w[1] == goal[1] and w[2] == tuple(goal[2])


RESULTS = []   # (gate id, side, ok, method)


def side(gid, which, ok, what, method="steps"):
    RESULTS.append((gid, which, bool(ok), method))
    check(ok, f"[{gid}] {which} ({method}): {what}")


def walk_gate(gid, opener, key, came, start, path, goal, room=None, floor=0, closes=False, also_flags=(), also_items=(), drop=(), before_ok=None):
    """BEFORE opener: walking path from start must NOT reach goal; AFTER: it must (closes=True: the other way round)."""
    for after in (False, True):
        at(opener, also=after, flags=also_flags, items=also_items, drop=drop)
        place(key, came, start, room=room, floor=floor)
        go(path)
        got = passed(goal)
        want = after != closes
        if not after and before_ok is not None:
            want = before_ok
        side(gid, "AFTER" if after else "BEFORE", got == want,
             f"{'reached' if got else 'did not reach'} {goal} from {key} {start} by {path!r} (story {'after' if after else 'before'} {opener}); now {where()}")


def guarded(gid, fn):
    try:
        fn()
    except Exception as ex:
        import traceback
        side(gid, "setup", False, f"the check could not run this gate: {type(ex).__name__}: {ex} @ {traceback.extract_tb(ex.__traceback__)[-1].lineno}")


# =================================================================================================== the gates, in story order
GATES = []
def resolve(goals):
    """Goal tiles: a list of (x, y), or "EXIT:<area>" (the map's ways out to it), "DOOR:<room>" (a town's door into it),
    "OUT" (a room's or floor's every way out)."""
    st = g.current_state
    if isinstance(goals, str):
        kind, _, name = goals.partition(":")
        ex = st.exits if isinstance(st, _WTS) else st.run.floor.exits
        if kind == "EXIT":
            return {t for t, a in ex.items() if str(a) == name}
        if kind == "DOOR":
            return {t for t, k in st.doors.items() if str(k) == name}
        if kind == "OUT":
            return set(ex)
    return {tuple(t) for t in goals}


def present(gid, opener, key, room, match, came=None, floor=0, flags=(), note="", closes=False):
    """An away leader / a person who comes later: BEFORE opener nobody whose words or name contain match stands there; AFTER
    they do."""
    for after in (False, True):
        at(opener, also=after, flags=flags)
        st = place(key, came or key, (1, 1), room=room, floor=floor)
        if isinstance(st, _WTS):
            who = [str(o.get("text", "")) + " " + json.dumps(o.get("event", "")) + " " + str(o.get("action", "")) for o in st._people().values()]
        else:
            who = [str(getattr(m, "payload", "")) for m in st.run.floor.movers]
        here = any(match.lower() in w.lower() for w in who)
        side(gid, "AFTER" if after else "BEFORE", here == (after != closes), f"{match!r} {'is' if here else 'is not'} in {key}/{room or floor} ({'after' if after else 'before'} {opener})" + (f" [{note}]" if note else ""), "people")


def plan(start, goals):
    """A path (letters) from start to any goal tile over the map now up, by the game's own open test (people, barred tiles,
    HM tiles); None if there is none. Exits and doors are only stepped into as goals."""
    from collections import deque as _dq
    st = g.current_state
    goals = resolve(goals)
    if isinstance(st, _WTS):
        ok = lambda n: st._open(n) and n not in st.exits and n not in st.doors
    else:
        f = st.run.floor
        ok = lambda n: f.inside(*n) and f.walkable(*n) and n not in f.exits and f.mover_at(*n) is None
    seen = {tuple(start): ""}
    q = _dq([tuple(start)])
    while q:
        x, y = q.popleft()
        for c, (dx, dy) in _D.items():
            n = (x + dx, y + dy)
            if n in seen:
                continue
            if n in goals:
                return seen[(x, y)] + c
            if ok(n):
                seen[n] = seen[(x, y)] + c; q.append(n)
    return None


def gate(gid, opener, key, start, goals, success, room=None, floor=0, came=None, closes=False, flags=(), items=(), drop=(),
         before_flags=(), after_flags=(), note="", either=None, path=None, shut_also=False):
    """AFTER opener: a path from start to goals must exist and walking it must reach success; BEFORE: the same path must not.
    success: an area key, ("room", name), ("floor", i) or a tile (x, y) on the same map. closes=True: the other way round."""
    came = came or key
    def got():
        w = where()
        if isinstance(success, str):
            return w[0] == success
        if success[0] in ("room", "floor"):
            return w[0] == key and w[1] == success[1]
        return w[0] == key and w[2] == tuple(success)
    open_side, shut_side = (False, True) if closes else (True, False)
    at(opener, also=open_side, flags=tuple(flags) + tuple(after_flags), items=items, drop=drop)
    place(key, came, start, room=room, floor=floor)
    st0 = g.current_state
    start = start or (tuple(st0.player) if isinstance(st0, _WTS) else tuple(st0.run.player))
    path = path or plan(start, goals)
    if path is None:
        side(gid, "OPEN", False, f"no way from {start} to {list(goals)[:4]} on {key}{'/' + str(room or floor) if (room or floor) else ''} with the gate open ({'before' if closes else 'after'} {opener})")
        return
    walk_path(path)
    side(gid, "OPEN", got(), f"{'reached' if got() else 'did NOT reach'} {success} by {len(path)} steps ({'before' if closes else 'after'} {opener}); now {where()}")
    at(opener, also=shut_side or shut_also, flags=tuple(flags) + tuple(before_flags), items=items, drop=drop)
    place(key, came, start, room=room, floor=floor)
    walk_path(path)
    if either and got():
        info(gid, f"SHUT side open too ({'after' if closes else 'before'} {opener}): {either}")
        return
    side(gid, "SHUT", not got(), f"{'got through to' if got() else 'stopped before'} {success} ({'after' if closes else 'before'} {opener}); now {where()}" + (f" [{note}]" if note else ""))




def info(gid, text):
    """Not counted: a gate the walk can't settle, or where ours follows Crystal / an agreed difference (said, with why)."""
    RESULTS.append((gid, "note", None, "note"))
    print(f"   --   [{gid}] {text}")


def gym_needs(gid, area, want, note="", also_ok=()):
    """Data: the Gym's leader battle waits on want (a flag), as the game's away leader does."""
    req = (_area[area].get("gym") or {}).get("requirements") or {}
    have = req.get("flag") or req.get("condition") or req.get("flags")
    side(gid, "GYM", have == want or have in also_ok or (isinstance(have, list) and want in have), f"{area}'s Gym waits on {have!r}; the game's opener is {want!r}" + (f" [{note}]" if note else ""), "data")


def has_people(gid, key, room, match, need_items=(), need_flags=(), base="mission:johto_m18", floor=0):
    """Someone (a ticket gate, a ferryman) is there with need_items/need_flags, and not without them."""
    for after in (False, True):
        at(base, also=True, items=need_items if after else (), flags=need_flags if after else (), drop=() if after else tuple(need_items) + tuple(need_flags))
        st = place(key, key, (1, 1), room=room, floor=floor)
        who = [str(o.get("text", "")) for o in st._people().values()] if isinstance(st, _WTS) else [str(m.payload) for m in st.run.floor.movers]
        here = any(match.lower() in w.lower() for w in who)
        side(gid, "AFTER" if after else "BEFORE", here == after, f"{match!r} {'is' if here else 'is not'} in {key}/{room or floor} ({'with' if after else 'without'} {list(need_items) + list(need_flags)})", "people")


def pharmacist(gid):
    """Cianwood's pharmacist hands over the SecretPotion only once Jasmine has told you about Amphy (HGSS + Crystal; 11-23)."""
    for seen in (False, True):
        at("mission:johto_m11", also=False, flags=("visited_CIANWOOD_CITY",) + (("jasmine_explained",) if seen else ()), drop=("SECRET_POTION",))
        st = place("CIANWOOD_CITY", "CIANWOOD_CITY", (5, 8), room="pharmacy")
        st.visit_pharmacist(); tap(g.current_state)
        got = story.inventory.get("SECRET_POTION", 0) > 0
        side(gid, "AFTER" if seen else "BEFORE", got == seen, f"{'given' if got else 'no'} SecretPotion {'after' if seen else 'before'} Jasmine explains", "talk")


def order(gid, first, then, note="", slack=0):
    """Data: in the playthrough's story, first comes before then (each "flag:x" / "item:X" / "badge:Z")."""
    def idx(spec):
        k, n = spec.split(":", 1)
        return next((i for i, e in enumerate(_EVENTS) if e[0] == k and e[1] == n), None)
    a, b = idx(first), idx(then)
    side(gid, "ORDER", a is not None and b is not None and a < b + slack, f"{first} (#{a}) before {then} (#{b})" + (f" [{note}]" if note else ""), "data")


# =================================================================================================== the gates, in story order
# (ids as kanto_handoff/johto_check/gates/johto_gates.json; each line says what SoulSilver/HeartGold does, and Crystal where it differs)
G = [
    # Elm stops you leaving his Lab before you pick a Pokemon (HGSS + Crystal)
    ("elm_lab_no_escape", lambda: gate("elm_lab_no_escape", "flag:received_starter_johto", "NEW_BARK_TOWN", (5, 8), "OUT", ("room", None), room="lab")),
    # HGSS: the west edge wants the Pokegear (Mom gives it after the starter); Crystal: only a Pokemon
    ("new_bark_west_exit", lambda: gate("new_bark_west_exit", "flag:received_starter_johto", "NEW_BARK_TOWN", (3, 13), "EXIT:JOHTO_ROUTE_29", "JOHTO_ROUTE_29")),
    # HGSS: a Gym guy stands on Violet Gym's lift till Sage Li is beaten; Crystal: no block
    ("violet_gym_sprout_tower", lambda: gym_needs("violet_gym_sprout_tower", "VIOLET_CITY", "defeated_elder_li", "the walk inside is open, as in Crystal")),
    # HGSS + Crystal: a man on north Route 32 walks you back till Elm's aide has given you the Egg (Violet Mart, after the Zephyr Badge)
    ("route32_aide_egg", lambda: gate("route32_aide_egg", "flag:got_togepi_egg", "JOHTO_ROUTE_32", (28, 13), [(28, 21)], (28, 21), came="VIOLET_CITY")),
    ("route32_old_save", lambda: gate("route32_old_save", "flag:got_togepi_egg", "JOHTO_ROUTE_32", (28, 13), [(28, 21)], (28, 21), came="VIOLET_CITY",
                                      before_flags=("visited_AZALEA_TOWN",), either="old save (been to Azalea, no Egg): let through, as meant",
                                      note="old saves past Azalea are let through")),
    # HGSS + Crystal: a Rocket guards the Slowpoke Well till Kurt runs down
    ("azalea_well_guard", lambda: gate("azalea_well_guard", "flag:kurt_went_to_well", "AZALEA_TOWN", (50, 16), "EXIT:SLOWPOKE_WELL", "SLOWPOKE_WELL")),
    # HGSS + Crystal: a Rocket stands at the Gym door till Proton is beaten in the Well
    ("azalea_gym_rocket", lambda: gate("azalea_gym_rocket", "flag:slowpoke_well_cleared", "AZALEA_TOWN", (19, 28), "DOOR:gym", ("room", "gym"))),
    # HGSS: the Cut tree in Ilex Forest (HM01 from the charcoal master after both Farfetch'd; Crystal: inside the kiln)
    ("ilex_cut_tree", lambda: gate("ilex_cut_tree", "item:HM_CUT", "ILEX_FOREST", (17, 65), [(16, 60)], (16, 60))),
    # HGSS + Crystal: Sudowoodo blocks Route 36 till you water it (SquirtBottle: Flower Shop, with the Plain Badge)
    ("route36_sudowoodo", lambda: gate("route36_sudowoodo", "flag:defeated_sudowoodo", "JOHTO_ROUTE_36", (66, 22), "EXIT:JOHTO_ROUTE_37", "JOHTO_ROUTE_37")),
    ("route36_squirtbottle", lambda: order("route36_squirtbottle", "badge:PLAIN", "item:SQUIRT_BOTTLE", "ours: given with the Plain Badge itself (story.py), HGSS: the Flower Shop after it", slack=2)),
    # HGSS: Morty is away (warped out) till the Burned Tower B1F scene; Crystal: an old man stands in the way
    ("ecruteak_gym_morty_away", lambda: gate("ecruteak_gym_morty_away", "flag:johto_beasts_fled", "ECRUTEAK_CITY", (26, 58), "DOOR:gym", ("room", "gym"))),
    # HGSS: a sage blocks the way to Bellchime Trail without the Fog Badge (Crystal: the Wise Trio and the Clear Bell)
    ("bell_tower_barrier_sage", lambda: gate("bell_tower_barrier_sage", "badge:FOG", "ECRUTEAK_CITY", (40, 28), "DOOR:bellchime", "BELLCHIME_TRAIL")),
    # HGSS: HM03 from the Dance Theater gentleman after its Rocket grunt (Crystal: after the five Kimono Girls)
    ("dance_theater_surf", lambda: order("dance_theater_surf", "flag:beat_theater_grunt", "item:HM_SURF")),
    # HGSS: the Olivine beach man turns you back without Surf (Crystal: nothing; the sea needs Surf anyway)
    ("route40_surf_man", lambda: gate("route40_surf_man", "item:HM_SURF", "JOHTO_ROUTE_40", None, "EXIT:JOHTO_ROUTE_41", "JOHTO_ROUTE_41", came="OLIVINE_CITY")),
    # HGSS + Crystal: the pharmacist makes the SecretPotion only after Jasmine explains at the Lighthouse top
    ("cianwood_secretpotion", lambda: pharmacist("cianwood_secretpotion")),
    # HGSS + Crystal: Jasmine is not in her Gym till Amphy is cured
    ("olivine_gym_jasmine_away", lambda: gym_needs("olivine_gym_jasmine_away", "OLIVINE_CITY", "ampharos_cured")),
    ("ecruteak_gym_morty_battle", lambda: gym_needs("ecruteak_gym_morty_battle", "ECRUTEAK_CITY", "johto_beasts_fled", "ours: the rival's Burned Tower battle, in the same scene; the door man waits on the beasts", also_ok=("defeated_rival_burned_tower",))),
    # HGSS: two workmen block the Cliff Edge Gate toward Route 47 till Amphy is cured (Baoba's call); no Crystal equivalent
    ("cliff_edge_gate_workmen", lambda: gate("cliff_edge_gate_workmen", "flag:ampharos_cured", "CLIFF_EDGE_GATE", None, "EXIT:JOHTO_ROUTE_47", "JOHTO_ROUTE_47", came="CIANWOOD_CITY")),
    # HGSS + Crystal: the souvenir shop's hidden stairs open once Lance has met you at the Lake of Rage
    ("souvenir_shop_stairs", lambda: gate("souvenir_shop_stairs", "flag:defeated_red_gyarados", "MAHOGANY_TOWN", (5, 11), "EXIT:ROCKET_HQ", "ROCKET_HQ", room="souvenir")),
    # HGSS + Crystal: Rockets in the Route 43 gate charge a toll till the Hideout is cleared (the west path goes round)
    ("route43_toll", lambda: present("route43_toll", "flag:rocket_hq_cleared", "JOHTO_ROUTE_43", None, "Rocket Grunt", closes=True)),
    # HGSS + Crystal: someone stands at Mahogany Gym's door till the Hideout is cleared
    ("mahogany_gym_blocker", lambda: gate("mahogany_gym_blocker", "flag:rocket_hq_cleared", "MAHOGANY_TOWN", (13, 26), "DOOR:gym", ("room", "gym"))),
    # HGSS + Crystal: Rocket Hideout B3F's door needs the two passwords (two grunts)
    ("rocket_hq_b3f_door", lambda: gate("rocket_hq_b3f_door", "flag:visited_ROCKET_HQ", "ROCKET_HQ", (15, 16), [(15, 11)], (15, 11), floor=2, came="MAHOGANY_TOWN",
                                        after_flags=("hq_password_1", "hq_password_2"), before_flags=("hq_password_1",))),
    # HGSS: B2F's voice-locked door opens when the Murkrow says the password (Crystal: no Murkrow)
    ("rocket_hq_murkrow_door", lambda: gate("rocket_hq_murkrow_door", "flag:visited_ROCKET_HQ", "ROCKET_HQ", (22, 23), [(22, 18)], (22, 18), floor=1, came="MAHOGANY_TOWN",
                                            after_flags=("hq_murkrow_password",))),
    # HGSS: the 1F stair grunt wants the Rocket uniform; Crystal: no stair guard
    ("radio_tower_1f_stairs", lambda: info("radio_tower_1f_stairs", "no uniform in ours (Crystal has none either); our 2F officer holds the upper floors till the takeover starts")),
    ("goldenrod_exits_closed", lambda: info("goldenrod_exits_closed", "HGSS-only (while you wear the uniform); ours has grunts at the north gate during the takeover")),
    # HGSS + Crystal: the Goldenrod Tunnel's locked door needs the Basement Key (from the fake Director)
    ("underground_basement_door", lambda: gate("underground_basement_door", "item:BASEMENT_KEY", "GOLDENROD_UNDERGROUND", (22, 5), "EXIT:WARP:2:27:2", ("floor", 2), came="GOLDENROD_CITY")),
    # HGSS + Crystal: Radio Tower 3F's shutter needs the Card Key (the real Director, in the Underground warehouse)
    ("radio_tower_3f_shutter", lambda: gate("radio_tower_3f_shutter", "item:CARD_KEY", "RADIO_TOWER", (20, 10), [(23, 6)], (23, 6), floor=2, came="GOLDENROD_CITY")),
    # HGSS: Mahogany's east edge (Route 44) opens when the Radio Tower is freed; Crystal: when the takeover starts
    ("mahogany_east_exit", lambda: gate("mahogany_east_exit", "flag:radio_tower_cleared", "MAHOGANY_TOWN", (25, 16), "EXIT:JOHTO_ROUTE_44", "JOHTO_ROUTE_44",
                                        )),
    ("mahogany_east_exit_crystal", lambda: info("mahogany_east_exit_crystal", "Crystal opens it when the takeover starts; ours follows SoulSilver (the Radio Tower freed)")),
    # HGSS + Crystal: a man stands at Blackthorn Gym's door till the Radio Tower is freed
    ("blackthorn_gym_guard", lambda: gate("blackthorn_gym_guard", "flag:radio_tower_cleared", "BLACKTHORN_CITY", (28, 26), "DOOR:gym", ("room", "gym"),
                                          either="no guard in ours; Blackthorn can't be reached before the Radio Tower is freed, so it never matters")),
    # HGSS + Crystal: the old man at the Dragon's Den door till Clair is beaten
    ("dragons_den_guard", lambda: gate("dragons_den_guard", "flag:johto_beat_clair", "BLACKTHORN_CITY", (32, 7), "EXIT:DRAGONS_DEN", "DRAGONS_DEN")),
    ("dragons_den_whirlpool", lambda: info("dragons_den_whirlpool", "whirlpools calmed by walking into them with HM Whirlpool: played by johto_playthrough")),
    # HGSS + Crystal: Clair gives the Rising Badge only after the Elder's test
    ("clair_rising_badge", lambda: order("clair_rising_badge", "flag:dragon_quiz_done", "badge:RISING")),
    ("ice_path_boulders", lambda: info("ice_path_boulders", "B1F's four boulder holes (Strength): played by johto_playthrough")),
    # HGSS + Crystal: Waterfall needs the Rising Badge as well as the HM
    ("tohjo_falls_waterfall", lambda: (info("tohjo_falls_waterfall", "waits on main: clean-main-johto-hm-badges (hms.FIELD_STRICT gets JOHTO)")
                                       if "JOHTO" not in __import__("src.world.hms", fromlist=["FIELD_STRICT"]).FIELD_STRICT else gate("tohjo_falls_waterfall", "badge:RISING", "TOHJO_FALLS", None, "EXIT:WARP:1:5:9", ("floor", 1), came="KANTO_ROUTE_27",
                                           items=("HM_WATERFALL", "HM_SURF")))),
    # HGSS: no badge check at the Reception Gate; Crystal: 8 badges
    ("route26_reception_gate", lambda: gate("route26_reception_gate", "badge:RISING", "POKEMON_LEAGUE_GATE", (7, 9), "DOOR:leaguegate", "JOHTO_VICTORY_ROAD", came="KANTO_ROUTE_26",
                                            either="no badge check here, as in SoulSilver", note="ours checks the 8 Johto badges at the great door, as Crystal does")),
    # HGSS + Crystal: Bell Tower 1F lets you up only with the Rainbow Wing
    ("bell_tower_1f_sage", lambda: gate("bell_tower_1f_sage", "item:RAINBOW_WING", "BELL_TOWER", (9, 5), "EXIT:WARP:1:3:4", ("floor", 1), came="BELLCHIME_TRAIL")),
    ("new_bark_east_exit_mom", lambda: info("new_bark_east_exit_mom", "HGSS-only (Mom, then Lyra, after the Rising Badge till the version legend); Crystal has none, nor do we")),
    ("ecruteak_rival_kimono", lambda: info("ecruteak_rival_kimono", "HGSS-only (Tidal Bell / Kimono Girls before Lugia); ours: Lugia needs the Silver Wing AND Tidal Bell (agreed 11-15)")),
    ("whirl_islands_sage", lambda: info("whirl_islands_sage", "HGSS's Silver Wing sage: ours asks for the Silver Wing and Tidal Bell at Lugia itself (agreed 11-15)")),
    # HGSS + Crystal: the S.S. Aqua wants the S.S. Ticket (Elm, after the Hall of Fame)
    ("ss_aqua_ticket", lambda: has_people("ss_aqua_ticket", "OLIVINE_CITY", "harbor", "S.S. Aqua", need_items=("SS_TICKET",))),
    # HGSS: the Magnet Train wants the Pass; Crystal: the Pass and the Power Plant fixed
    ("magnet_train_pass", lambda: has_people("magnet_train_pass", "GOLDENROD_CITY", "station", "Magnet Train", need_items=("PASS",), need_flags=("power_plant_fixed",))),
    # HGSS: Route 28 / Mt. Silver after 16 badges and Oak's OK; ours: the Johto title (Jordan 10-21, kept 11-23 Q8)
    ("mt_silver_gate", lambda: gate("mt_silver_gate", "flag:beat_johto_champion", "POKEMON_LEAGUE_GATE", (3, 6), "EXIT:KANTO_ROUTE_28", "KANTO_ROUTE_28", came="KANTO_ROUTE_26",
                                    note="agreed difference: the Johto title, not 16 badges")),
    ("route22_west_kanto", lambda: info("route22_west_kanto", "the Reception Gate's Kanto side is Kanto's (FireRed's gate): left to the Kanto check")),
    ("forced_battles", lambda: info("forced_battles", "Cherrygrove / Azalea / Burned Tower / Underground / Victory Road rivals, Eusine, Petrel, Ariana, Archer, Lance: played by johto_playthrough")),
]
_ONLY = [a for a in sys.argv[2:] if not a.startswith("-")]
for gid, fn in G:
    if _ONLY and gid not in _ONLY:
        continue
    print("")
    print(gid)
    guarded(gid, fn)
print("")
print(f"##### {len(fails)} fails")
