# Johto's played checks (11-23, Dev Map clean-johto-johto-turn-battles and clean-johto-johto-rematches; Kanto's kanto_played made
# Johto's): what the other Johto suites only read or win the quick way, played as a player would, battles fought turn by turn
# (the first move, the right answer to each sum: kanto_maps' _fight), on the walked maps.
#   1. Jordan's own old save in slot 1 (a copy, read only: it stands in Ecruteak with every Johto badge) loads on the walked map,
#      and every Johto place it had been to is still reachable through today's gates
#   2. every Gym: walked into, its challenge won, then its Leader fought turn by turn: the badge and the Leader's own TM
#   3. the Elite Four and Lance, room by room
#   4. after the title: the League rematch (HGSS's rematch teams, their levels as the games have them) and each Leader's
#      rematch (HGSS's TRAINER_LEADER_*_2 teams, j_leader_rematch.py; the Leader alone, no badge again)
#        bash dev/checks/run.sh johto_played
import json, os, copy
_src = open("dev/checks/johto_playthrough_body.py", encoding="utf-8").read()
_src = _src.replace('OUT = os.path.join(S, "johto_playthrough")', 'OUT = os.path.join(S, "johto_played")')   # (its own folder)
exec(_src[_src.index("import json, time"):_src.index("def play_through():")])   # (a new Johto game, and the playthrough's driver)
_km = open("dev/checks/kanto_maps_body.py", encoding="utf-8").read()
exec(_km[_km.index("def _fight(b, n=8000):"):_km.index("# ---- the Hall of Fame")])   # (a battle fought as a player would)
_jg = open("dev/checks/johto_gates_body.py", encoding="utf-8").read()
exec(_jg[_jg.index("TIMELINE = ["):_jg.index("def _is_map(")])   # (at(step): the story just before / after a step)
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
    a.level = 100; a.moves = ["ICE-BEAM", "PSYCHIC", "THUNDERBOLT", "FLAMETHROWER"]   # (Ice first: nothing is immune to it - Karen's Dark types are to Psychic)
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


BADGES = ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORMBADGE", "MINERAL", "GLACIER", "RISING"]
GYMS = [("VIOLET_CITY", "JOHTO_ROUTE_31", "badge:ZEPHYR"), ("AZALEA_TOWN", "JOHTO_ROUTE_33", "badge:HIVE"),
        ("GOLDENROD_CITY", "JOHTO_ROUTE_34", "badge:PLAIN"), ("ECRUTEAK_CITY", "JOHTO_ROUTE_37", "badge:FOG"),
        ("CIANWOOD_CITY", "JOHTO_ROUTE_41", "badge:STORMBADGE"), ("OLIVINE_CITY", "JOHTO_ROUTE_39", "badge:MINERAL"),
        ("MAHOGANY_TOWN", "JOHTO_ROUTE_42", "badge:GLACIER"), ("BLACKTHORN_CITY", "JOHTO_ROUTE_45", "badge:RISING")]


def gym_room(v):
    """The Gym's room with the Leader in it (its "Gym" person): the last gym room of the town."""
    rooms = [r for r in (v.town_map.get("rooms") or {}) if r.startswith("gym")]
    for r in reversed(rooms):
        if any((p if isinstance(p, str) else (p[-1] if isinstance(p, list) else p).get("text") if not isinstance(p, str) else p) == "Gym"
               or (isinstance(p, list) and any((q.get("text") if isinstance(q, dict) else q) == "Gym" for q in p))
               for p in v.town_map["rooms"][r].get("people") or []):
            return r
    return rooms[-1] if rooms else None


def lobby_run(limit=4000):
    """A Gym's lobby (or its challenge) driven as a player: CHALLENGE, the challenge won, each battle fought, till it's left."""
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
print("1) Jordan's old save, slot 1 (a copy of the main folder's backup: Ecruteak, every Johto badge)")
_main = (os.path.normpath(os.path.join(os.getcwd(), "..", "..", "..", "..", "Kanto Math Game")) if ".claude" in os.getcwd() else os.getcwd())
_new_game, _story0 = copy.deepcopy(g.data.data), g.story_manager
for _p in [os.path.join(_main, "game_data_1.json.bak")]:
    if not os.path.exists(_p):
        print(f"   --   not found: {_p}")
        continue
    _d = json.load(open(_p, encoding="utf-8"))
    g.data.data = copy.deepcopy(_d)
    try:
        ok = g.load_game_data()
        story = g.story_manager
        st = settle()
        check(ok and is_map(st) and story.current_area_key == _d["story"].get("current_area_key") and story.player_team,
              f"{os.path.basename(_p)}: Continue lands on the walked map where it was saved ({story.current_area_key}, {type(st).__name__}, {len(story.player_team)} in the party)")
        exec(open("dev/checks/reach_lib.py", encoding="utf-8").read())
        _jo = {}
        exec(open("dev/builders/town_maps/johto.py", encoding="utf-8").read(), _jo)
        _keys = set(_jo["MAPS"])
        _had = {k[8:] for k, v in story.story_flags.items() if k.startswith("visited_") and v and k[8:] in _keys}
        _seen, _gyms = reach(story.current_area_key)
        _lost = sorted(_had - set(_seen))
        check(not _lost, f"...every Johto place it had been to is still reachable through today's gates ({len(_had)} visited; cut off: {_lost})")
    except Exception as ex:
        import traceback
        check(False, f"{os.path.basename(_p)}: loading it crashed: {type(ex).__name__}: {ex} @ {traceback.extract_tb(ex.__traceback__)[-1].lineno}")
g.data.data = _new_game
g.story_manager = story = _story0
story.starting_region = "JOHTO"
g.change_state(CityState(g)); settle()

# ================================================================================ 2. the Gyms
print("\n2) every Gym: walked in, its challenge won, then its Leader fought turn by turn (the badge and the Leader's own TM)")
for _town, _came, _badge in GYMS:
    at(_badge)
    for _k in [k for k in story.story_flags if _town in k and ("gym" in k or "league" in k)]:
        story.story_flags.pop(_k)
    story.player_team = [ace(), ace()]
    _ld = AREAS[_town]["gym"]["leader"]
    _tm = next((k for k in (_ld.get("rewards") or {}) if str(k).startswith("TM")), None)
    v = walk_town(_town, _came)
    if not isinstance(v, _WTS):
        check(False, f"{_town}: no walked town ({type(v).__name__})"); continue
    _r = gym_room(v)
    v._go(_r, ""); settle(); v = g.current_state
    _gp = people(v).get("Gym")
    _tms0 = tm_moves()
    FOUGHT.clear()
    if _gp is None:   # (Cianwood: Chuck under the waterfall first - the button at the top, then he's the Gym)
        story.story_flags["cianwood_gym_waterfall_off"] = True
        v = walk_town(_town, _came, room=_r); _gp = people(v).get("Gym")
    if _gp is not None:
        talk_to(v, _gp)
        lobby_run()
    _b = _badge.split(":")[1]
    _got = {k: mv for k, (q, mv) in tm_moves().items() if q > (_tms0.get(k) or (0, None))[0]}
    _lead = [f for f in FOUGHT if str(f[0]).startswith(_ld["name"])]
    _done = _b in story.badges.get("JOHTO", []) or (_ld.get("badge_later") and story.story_flags.get(_ld["badge_later"]))
    check(bool(_lead) and not any(str(f[0]).endswith("(UNFINISHED)") for f in FOUGHT) and _done and (not _tm or _tm in _got),
          f"{_town}: {_ld['name']} fought turn by turn ({[(f[0], f[1]) for f in FOUGHT][-2:]}): "
          f"{'the ' + _b.title() + ' Badge' if _b in story.badges.get('JOHTO', []) else ('beaten, the badge after the Dragon Shrine' if _done else 'NO badge')} "
          f"and {_got or 'no TM'} (wants {_tm})")

# ================================================================================ 3. the Elite Four and Lance
print("\n3) the Elite Four and Lance, room by room (battles fought turn by turn)")
at("flag:visited_SILVER_LEAGUE_PLATEAU", also=True)
story.player_team = [ace(), ace()]
for _k in [k for k in story.story_flags if "SILVER_LEAGUE_PLATEAU" in k and k != "visited_SILVER_LEAGUE_PLATEAU"] + ["beat_johto_elite_four", "beat_johto_champion"]:
    story.story_flags.pop(_k, None)
LEAGUE = (("league_will", "Will"), ("league_koga", "Koga"), ("league_bruno", "Bruno"), ("league_karen", "Karen"), ("league_lance", "Lance"))
v = walk_town("SILVER_LEAGUE_PLATEAU", "JOHTO_VICTORY_ROAD")
_first = []
for _i, (_room, _who) in enumerate(LEAGUE, 1):
    v = g.current_state
    if not isinstance(v, _WTS):
        check(False, f"{_who}: not on the Plateau's map ({type(v).__name__})"); break
    v._go(_room, ""); settle(); v = g.current_state
    for _p in story.player_team:
        _p.heal_full()
    FOUGHT.clear()
    if _who not in people(v):
        check(False, f"{_who}: not in the room {_room} ({sorted(people(v))})"); break
    talk_to(v, people(v)[_who]); lobby_run()
    _flag = "beat_johto_champion" if _i == 5 else f"league_won_SILVER_LEAGUE_PLATEAU_{_i}"
    _ok = bool(FOUGHT) and not str(FOUGHT[0][0]).endswith("(UNFINISHED)") and story.story_flags.get(_flag)
    _first.append(FOUGHT[0][1] if FOUGHT else None)
    check(_ok, f"{_who}: fought and beaten ({[(f[0], f[1]) for f in FOUGHT][:1]}; {_flag}: {story.story_flags.get(_flag)})")
    if not _ok:
        break
    if isinstance(g.current_state, _WTS) and g.current_state.room == "hall_of_fame":
        break
check(story.story_flags.get("beat_johto_elite_four") and story.story_flags.get("beat_johto_champion"), "...the title: the Elite Four and Lance beaten")

# ================================================================================ 4. after the title: the rematches
print("\n4) after the title: the League rematch and each Leader's rematch (HGSS's own rematch teams)")
at("flag:beat_johto_champion", also=True, flags=("defeated_red", "move_offer_johto", "move_offer_kanto"))
story.player_team = [ace(), ace(), ace()]
_league = AREAS["SILVER_LEAGUE_PLATEAU"]["gym"]
_want = [t.get("rematch") for t in _league.get("trainers", [])] + [_league["leader"].get("rematch")]
story.story_flags["gym_progress_SILVER_LEAGUE_PLATEAU"] = 5
for _i in range(1, 5):
    story.story_flags[f"league_won_SILVER_LEAGUE_PLATEAU_{_i}"] = True
v = walk_town("SILVER_LEAGUE_PLATEAU", "JOHTO_VICTORY_ROAD")
_rm = []
for _i, (_room, _who) in enumerate(LEAGUE):
    v = g.current_state
    if not isinstance(v, _WTS) or v.area_key != "SILVER_LEAGUE_PLATEAU":   # (sent home after a loss: back to the Plateau)
        v = walk_town("SILVER_LEAGUE_PLATEAU", "JOHTO_VICTORY_ROAD")
    if not isinstance(v, _WTS):
        break
    v._go(_room, ""); settle(); v = g.current_state
    for _p in story.player_team:
        _p.heal_full()
    FOUGHT.clear()
    if _who in people(v):
        talk_to(v, people(v)[_who]); lobby_run()
    _rm.append(FOUGHT[0] if FOUGHT else (_who, None, None))
_match = [bool(w) and f[2] == w.get("team") and f[1] == [max(70, int(x)) for x in w.get("levels")] for f, w in zip(_rm, _want)]
check(len(_rm) == 5 and all(_match) and not any(str(f[0]).endswith("(UNFINISHED)") for f in _rm),
      f"the League rematch: all five fought again with HGSS's rematch teams, every Pokemon at least Lv 70 (Jordan's League rematch rule) "
      f"({[(f[0], f[1]) for f in _rm]}; as the data: {_match})")
for _town, _came, _badge in GYMS:
    _ld = AREAS[_town]["gym"]["leader"]
    _w = _ld.get("rematch") or {}
    story.player_team = [ace(), ace(), ace()]
    for _p in story.player_team:
        _p.heal_full()
    _b0 = list(story.badges.get("JOHTO", []))
    story.story_flags["cianwood_gym_waterfall_off"] = True   # (Chuck stands as the Gym once the waterfall's off)
    v = walk_town(_town, _came)
    _r = gym_room(v)
    v._go(_r, ""); settle(); v = g.current_state
    FOUGHT.clear()
    _gp = people(v).get("Gym")
    if _gp is not None:
        talk_to(v, _gp); lobby_run()
    _f = FOUGHT[0] if FOUGHT else (None, None, None)
    check(len(FOUGHT) == 1 and str(_f[0]).startswith(_ld["name"]) and _f[2] == _w.get("team") and _f[1] == _w.get("levels")
          and story.badges.get("JOHTO", []) == _b0,
          f"{_town}: {_ld['name']} alone, HGSS's rematch team ({_f[1]} {_f[2]}), no badge again ({len(FOUGHT)} battle(s))")

# ================================================================================ 5. the music
print("\n5) SoulSilver's own music (assets/music/johto, johto_map_tools/j_music.py): each place's theme, its rooms', the battles")
_mt = json.load(open("assets/music/johto/music.json", encoding="utf-8"))
_names = {v for v in list(_mt["areas"].values()) + list(_mt["rooms"].values()) + list(_mt["kinds"].values()) if isinstance(v, str)}
_missing = sorted(n for n in _names if not os.path.isfile(os.path.join("assets", "music", "johto", n + ".ogg")))
check(not _missing and len(_mt["areas"]) >= 70, f"every track named is there ({len(_names)} tracks, {len(_mt['areas'])} places; missing {_missing})")
_m = g.music
story.current_area_key = "NEW_BARK_TOWN"; g.walk_town_room = None
_t = _m.region_track("town", "JOHTO")
check(bool(_t) and _t.endswith("t_wakaba.ogg"), f"New Bark Town plays its own SoulSilver theme ({_t and os.path.basename(_t)})")
_k = {k: (_m.region_track(k, "JOHTO") or "") for k in ("wild", "trainer", "gym", "final", "center")}
check(all(_k.values()) and _k["gym"].endswith("vs_gymreader.ogg") and _k["final"].endswith("vs_champ.ogg"),
      f"...and the battles theirs: {[(k, os.path.basename(v)) for k, v in _k.items()]}")

print(f"##### {len(fails)} failures")
for m in fails:
    print("   FAIL " + m)
