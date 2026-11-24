# Sinnoh's played checks (11-24, Dev Map clean-sinnoh-sinnoh-played-suite; Johto's johto_played made Sinnoh's): what the other
# Sinnoh suites win the quick way, played as a player would, battles fought turn by turn (the first move, the right answer to
# each sum: kanto_maps' _fight), on the walked maps.
#   1. Jordan's own old save in slot 1 (a copy, read only: it stands in Ecruteak with every badge of the menu days, Sinnoh's
#      eight among them) loads, and set down in Twinleaf, every Sinnoh place it had been to is still reachable through today's
#      gates (Platinum's HM badges, 11-24, included)
#   2. every Gym: walked into, then its Leader fought turn by turn: the badge and the Leader's own TM
#   3. the Elite Four and Cynthia room by room, and 4. Cynthia's rematch: wait on S6 (the League's walked rooms) - said, not failed
#        bash dev/checks/run.sh sinnoh_played
import json, os, copy
_src = open("dev/checks/sinnoh_playthrough_body.py", encoding="utf-8").read()
_src = _src.replace('OUT = os.path.join(S, "sinnoh_playthrough")', 'OUT = os.path.join(S, "sinnoh_played")')   # (its own folder)
exec(_src[_src.index("import json, time"):_src.index("def play_through():")])   # (a new Sinnoh game, and the playthrough's driver)
_km = open("dev/checks/kanto_maps_body.py", encoding="utf-8").read()
exec(_km[_km.index("def _fight(b, n=8000):"):_km.index("# ---- the Hall of Fame")])   # (a battle fought as a player would)
from src.states.overworld.gym_lobby import GymLobbyState


def frames(n=1):
    for _ in range(n):
        g.current_state.update(); g.current_state.draw()


fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


FOUGHT = []


def _win(b):   # (the driver's battles: fought turn by turn, not counted as won)
    STATE["battles"] += 1
    name = getattr(b, "trainer_name", None) or getattr(b, "trainer_class", "?")
    lv = [getattr(p, "level", None) for p in (getattr(b, "opponent_team", None) or [])]
    ids = [getattr(p, "id", None) for p in (getattr(b, "opponent_team", None) or [])]
    FOUGHT.append((name, lv, ids))
    if g.current_state is not b:
        g.change_state(b)
    for _round in range(8):
        _fight(b)
        st = g.current_state
        if type(st).__name__ == "PokemonPartyMenuState" and getattr(st, "context", None) == "forced_switch":
            nxt = next((i for i, p in enumerate(story.player_team) if p and getattr(p, "current_hp", 0) > 0 and p is not getattr(b, "player_pokemon", None)), None)
            if nxt is None:
                break
            st.on_select(nxt)
            if g.current_state is not b:
                g.change_state(b)
            continue
        break
    if g.current_state is b:   # (the fight didn't finish: say so, then end it so the run goes on)
        FOUGHT[-1] = (name + " (UNFINISHED)", lv, ids)
        b.player_won = True
        b.exit_battle()


def ace():
    a = Pokemon(g.loader.fetch_specific(150), g.assets, size_mult=2.5)
    a.level = 100; a.moves = ["ICE-BEAM", "PSYCHIC", "THUNDERBOLT", "FLAMETHROWER"]
    if hasattr(a, "recalculate_stats"):
        a.recalculate_stats()
    a.heal_full()
    a.max_hp = a.get_max_hp()
    return a


def walk_town(area, came, room=None, at_=None):
    story.current_area_key, story.last_area_key = area, came
    g.walk_town_pos = (area, tuple(at_), (0, -1)) if at_ else None
    g.walk_town_room = (area, room) if room else None
    g.change_state(CityState(g))
    return settle()


def people(st):
    return {o.get("text"): p for p, o in st._people().items()}


def talk_to(st, spot):
    """Stand beside someone (an open tile next to them) facing them, and talk."""
    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        n = (spot[0] + dx, spot[1] + dy)
        if st._open(n):
            st.player = n; st.anim = 0; st.anim_from = n; st.facing = (-dx, -dy)
            st._talk(tuple(spot))
            return settle()
    return None


_TMS = json.load(open("assets/tms.json", encoding="utf-8"))


def tm_moves():
    return {k: (q, (_TMS.get(k) or {}).get("move")) for k, q in story.inventory.items() if str(k).startswith("TM") and q}


# (Platinum's order of the eight)
GYMS = [("OREBURGH_CITY", "OREBURGH_GATE", "COAL"), ("ETERNA_CITY", "ETERNA_FOREST", "FOREST"),
        ("VEILSTONE_CITY", "SINNOH_ROUTE_215", "COBBLE"), ("PASTORIA_CITY", "SINNOH_ROUTE_212", "FEN"),
        ("HEARTHOME_CITY", "SINNOH_ROUTE_209", "RELIC"), ("CANALAVE_CITY", "SINNOH_ROUTE_218", "MINE"),
        ("SNOWPOINT_CITY", "SINNOH_ROUTE_217", "ICICLE"), ("SUNYSHORE_CITY", "SINNOH_ROUTE_222", "BEACON")]


def gym_room(v):
    """The Gym's room with the Leader in it (its "Gym" person): the last gym room of the town that has one."""
    rooms = [r for r in (v.town_map.get("rooms") or {}) if r.startswith("gym")]
    for r in reversed(rooms):
        if any((p if isinstance(p, str) else p.get("text") if isinstance(p, dict) else None) == "Gym"
               for p in v.town_map["rooms"][r].get("people") or []):
            return r
    return rooms[-1] if rooms else None


def lobby_run(limit=4000):
    """A Gym's lobby (or its challenge) driven as a player: CHALLENGE, each battle fought, till it's left."""
    for _ in range(limit):
        st = g.current_state
        if isinstance(st, TrainerBattleState):
            _win(st); continue
        if isinstance(st, _MG) and not getattr(st, "done", False):
            st.on_done(True); continue
        if isinstance(st, GymLobbyState):
            if st.is_cleared or not st.next_opponent and not getattr(st, "challenge", None):
                st.exit_gym(); continue
            st.challenge_gym()
            if g.current_state is st:
                st.exit_gym()
            continue
        if is_map(st) and not getattr(st, "_busy", lambda: False)():
            return st
        if getattr(getattr(st, "dialogue_box", None), "visible", False):
            st.dialogue_box.advance()
        elif hasattr(st, "handle_events") and not is_map(st):
            _click(st)
        st.update(); st.draw()
    return g.current_state


# ================================================================================ 1. Jordan's old save
print("1) Jordan's old save, slot 1 (a copy of the main folder's: Ecruteak, every badge of the menu days), set down in Twinleaf")
_main = (os.path.normpath(os.path.join(os.getcwd(), "..", "..", "..", "..", "Kanto Math Game")) if ".claude" in os.getcwd() else os.getcwd())
_new_game, _story0 = copy.deepcopy(g.data.data), g.story_manager
for _p in [os.path.join(_main, "game_data_1.json.bak"), os.path.join(_main, "game_data_1.json")]:
    if not os.path.exists(_p):
        print(f"   --   not found: {_p}")
        continue
    _d = json.load(open(_p, encoding="utf-8"))
    g.data.data = copy.deepcopy(_d)
    try:
        ok = g.load_game_data()
        story = g.story_manager
        st = settle()
        check(ok and is_map(st) and story.player_team, f"{os.path.basename(_p)}: Continue lands on the walked map ({story.current_area_key}, {type(st).__name__}, {len(story.player_team)} in the party, Sinnoh badges {story.badges.get('SINNOH')})")
        story.current_area_key = "TWINLEAF_TOWN"   # (as if it had travelled home to Sinnoh)
        exec(open("dev/checks/reach_lib.py", encoding="utf-8").read())
        _tmj = json.load(open("assets/town_maps.json", encoding="utf-8"))
        _keys = {k for k, v in AREAS.items() if str(v.get("region", "")).upper() == "SINNOH" and k in _tmj}
        _had = {k[8:] for k, v in story.story_flags.items() if k.startswith("visited_") and v and k[8:] in _keys}
        _seen, _gyms = reach("TWINLEAF_TOWN")
        _lost = sorted(_had - set(_seen))
        check(not _lost, f"...every Sinnoh place it had been to is still reachable from Twinleaf through today's gates ({len(_had)} visited; cut off: {_lost})")
        break
    except Exception as ex:
        import traceback
        check(False, f"{os.path.basename(_p)}: loading it crashed: {type(ex).__name__}: {ex} @ {traceback.extract_tb(ex.__traceback__)[-1].lineno}")
g.data.data = _new_game
g.story_manager = story = _story0
story.starting_region = "SINNOH"
g.change_state(CityState(g)); settle()

# ================================================================================ 2. the Gyms
print("\n2) every Gym: walked in, then its Leader fought turn by turn (the badge and the Leader's own TM)")
_order = [b for _t, _c, b in GYMS]
for _town, _came, _badge in GYMS:
    story.badges["SINNOH"] = _order[:_order.index(_badge)]
    for _k in [k for k in story.story_flags if _town in k and ("gym" in k or "league" in k)]:
        story.story_flags.pop(_k)
    story.player_team = [ace(), ace()]
    _rq = AREAS[_town]["gym"].get("requirements") or {}
    if _rq.get("flag"):   # (the story as it stands by then: Roark met in the mine, Spear Pillar resolved for Volkner)
        story.story_flags[_rq["flag"]] = True
    _ld = AREAS[_town]["gym"]["leader"]
    _tm = next((k for k in (_ld.get("rewards") or {}) if str(k).startswith("TM")), None)
    v = walk_town(_town, _came)
    if not isinstance(v, _WTS):
        check(False, f"{_town}: no walked town ({type(v).__name__})"); continue
    _r = gym_room(v)
    if _r is None:
        print(f"   --   {_town}: no walked Gym yet (S6)"); continue
    v._go(_r, ""); settle(); v = g.current_state
    _gp = people(v).get("Gym")
    _tms0 = tm_moves()
    FOUGHT.clear()
    if _gp is not None:
        talk_to(v, _gp)
        lobby_run()
    _got = {k: mv for k, (q, mv) in tm_moves().items() if q > (_tms0.get(k) or (0, None))[0]}
    _lead = [f for f in FOUGHT if str(f[0]).startswith(_ld["name"])]
    _done = _badge in story.badges.get("SINNOH", [])
    check(bool(_lead) and not any(str(f[0]).endswith("(UNFINISHED)") for f in FOUGHT) and _done and (not _tm or _tm in _got),
          f"{_town}: {_ld['name']} fought turn by turn ({[(f[0], f[1]) for f in FOUGHT][-1:]}): "
          f"{'the ' + _badge.title() + ' Badge' if _done else 'NO badge'} and {_got or 'no TM'} (wants {_tm})")

# ================================================================================ 3-4. the League and Cynthia's rematch
print("\n3) the Elite Four and Cynthia room by room, 4) Cynthia's rematch")
print("   --   wait on S6: the League's walked rooms aren't built yet (ROADMAP_SINNOH); her rematch teams are in the area data")

print(f"##### {len(fails)} failures")
