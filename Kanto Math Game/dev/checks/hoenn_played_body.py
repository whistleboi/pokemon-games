# Hoenn's played checks (11-24, Dev Map clean-hoenn-hoenn-played; Johto's johto_played made Hoenn's): what the other Hoenn
# suites only read or win the quick way, played as a player would, battles fought turn by turn (the first move, the right
# answer to each sum: kanto_maps' _fight), on the walked maps.
#   1. a Hoenn save made by an earlier run of the story (hoenn_playthrough's own save, the game's save data) loads on the
#      walked map where it was saved (Jordan has no Hoenn save of his own yet)
#   2. every Gym: walked into, its Leader's game won, then the Leader fought turn by turn: the badge and the Leader's own TM
#   3. the Elite Four and Steven, room by room
#   4. after the title: the League rematch (ORAS's rematch teams; ORAS has no Gym Leader rematches)
#   5. Emerald's own music (assets/music/hoenn, kanto_handoff/hoenn_rom_tools/hmusic.py; Dev Map clean-hoenn-music):
#      each place's theme, its rooms', the battles
#        bash dev/checks/run.sh hoenn_played
import json, os, copy, glob
_hg = open("dev/checks/hoenn_gates_body.py", encoding="utf-8").read()
exec(_hg[_hg.index("import json"):_hg.index("def g01():")])   # (a Hoenn game, Omega Ruby; at(step): the story just before / after a step)
_km = open("dev/checks/kanto_maps_body.py", encoding="utf-8").read()
exec(_km[_km.index("def _fight(b, n=8000):"):_km.index("# ---- the Hall of Fame")])   # (a battle fought as a player would)
import pygame
from src.states.overworld.gym_lobby import GymLobbyState
from src.minigames.base import Minigame as _MG
from src.pokemon.data import Pokemon

FOUGHT = []


def _fight_out(b):
    """One trainer battle, fought turn by turn (a fainted Pokemon swapped for the next): what was fought, its levels."""
    name = getattr(b, "trainer_name", None) or getattr(b, "trainer_class", "?")
    lv = [getattr(p, "level", None) for p in (getattr(b, "opponent_team", None) or [])]
    ids = [getattr(p, "id", None) for p in (getattr(b, "opponent_team", None) or [])]
    FOUGHT.append((name, lv, ids))
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
    if g.current_state is b:   # (it didn't finish: say so, then end it)
        FOUGHT[-1] = (name + " (UNFINISHED)", lv, ids)
        b.player_won = True
        b.exit_battle()


def drive(limit=6000):
    """Play on as a player would - each battle fought turn by turn, a Leader's game won, every line tapped - till you're
    back on the walked map with nothing happening."""
    quiet = 0
    for _ in range(limit):
        st = g.current_state
        if isinstance(st, TrainerBattleState):
            _fight_out(st)
            continue
        if isinstance(st, _MG) and not getattr(st, "done", False):
            st.on_done(True)
            continue
        if isinstance(st, GymLobbyState):
            if st.is_cleared or not st.next_opponent:
                st.exit_gym()
                continue
            st.challenge_gym()
            if g.current_state is st:
                st.exit_gym()
            continue
        if getattr(st, "npc_active", False):   # (a walked map's own text box: tap it on)
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            st.update(); st.draw()
            quiet = 0
            continue
        if _is_map(st) and _settled():
            quiet += 1
            if quiet > 240:   # (the map's been quiet a while: whatever was coming - a battle after its intro - has been and gone)
                return st
        else:
            quiet = 0
        if getattr(getattr(st, "dialogue_box", None), "visible", False):
            st.dialogue_box.advance()
        elif hasattr(st, "handle_events") and not _is_map(st):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        st.update()
        st.draw()
    return g.current_state


def ace():
    a = Pokemon(g.loader.fetch_specific(150), g.assets, size_mult=2.5)
    a.level = 100
    a.moves = ["ICE-BEAM", "PSYCHIC", "THUNDERBOLT", "FLAMETHROWER"]
    if hasattr(a, "recalculate_stats"):
        a.recalculate_stats()
    a.heal_full()
    return a


def tm_moves():
    return {k: q for k, q in story.inventory.items() if str(k).startswith("TM") and q}


# ================================================================================ 1. a saved game
print("1) a Hoenn save made by an earlier run of the story loads on the walked map where it was saved")
_saves = sorted(glob.glob(os.path.join("dev", "checks", "out", "hoenn_playthrough_saves", "hoenn_m1[0-9].json")))
_new_game, _story0 = copy.deepcopy(g.data.data), g.story_manager
if not _saves:
    print("   --   no saved game yet (bash dev/checks/run.sh hoenn_playthrough makes them)")
for _p in _saves[:1]:
    _sv = json.load(open(_p, encoding="utf-8"))
    g.data.data = copy.deepcopy(_sv["data"])
    try:
        ok = g.load_game_data()
        story = g.story_manager
        st = settle()
        check(ok and _is_map(st) and story.current_area_key == _sv["data"]["story"].get("current_area_key") and story.player_team,
              f"{os.path.basename(_p)} (saved at {_sv.get('commit')}): Continue lands on the walked map where it was saved "
              f"({story.current_area_key}, {type(st).__name__}, {len(story.player_team)} in the party, {len(story.badges.get('HOENN', []))} badges)")
    except Exception as ex:
        import traceback
        check(False, f"{os.path.basename(_p)}: loading it crashed: {type(ex).__name__}: {ex} @ {traceback.extract_tb(ex.__traceback__)[-1].lineno}")
g.data.data = _new_game
g.story_manager = story = _story0
g.dungeon_routes = True
g.walk_towns = True

# ================================================================================ 2. the Gyms
print("\n2) every Gym: walked in, its Leader's game won, then the Leader fought turn by turn (the badge and the Leader's own TM)")
from src import minigames as _mg
GYMS = [("RUSTBORO_CITY", "HOENN_ROUTE_104", "stone", "STONE"), ("DEWFORD_TOWN", "HOENN_ROUTE_106", "knuckle", "KNUCKLE"),
        ("MAUVILLE_CITY", "HOENN_ROUTE_110", "dynamo", "DYNAMO"), ("LAVARIDGE_TOWN", "HOENN_JAGGED_PASS", "heat", "HEAT"),
        ("PETALBURG_CITY", "HOENN_ROUTE_102", "balance", "BALANCE"), ("FORTREE_CITY", "HOENN_ROUTE_119", "feather", "FEATHER"),
        ("MOSSDEEP_CITY", "HOENN_ROUTE_124", "mind", "MIND"), ("SOOTOPOLIS_CITY", "SOOTOPOLIS_CITY", "rain", "RAIN")]
for _town, _came, _step, _b in GYMS:
    at(_step)
    story.story_flags.pop(_mg.done_flag(_town), None)
    story.player_team = [ace(), ace()]
    _ld = _area[_town]["gym"]["leader"]
    _tm = next((k for k in (_ld.get("rewards") or {}) if str(k).startswith("TM")), None)
    _tms0 = tm_moves()
    FOUGHT.clear()
    try:
        st = open_map(_town, _came)
        _rooms = [r for r in (st.town_map.get("rooms") or {}) if r.startswith("gym")]
        st._go(_rooms[-1] if _rooms else "gym", "")
        frames(2)
        g.transitioning = False
        st.start_gym_battle()
        drive()
    except Exception as ex:
        import traceback
        check(False, f"{_town}: crashed: {type(ex).__name__}: {ex} @ {traceback.extract_tb(ex.__traceback__)[-1].lineno}")
        continue
    _got = {k: q for k, q in tm_moves().items() if q > _tms0.get(k, 0)}
    _lead = [f for f in FOUGHT if str(f[0]).startswith(_ld["name"])]
    check(bool(_lead) and not any(str(f[0]).endswith("(UNFINISHED)") for f in FOUGHT) and _b in story.badges.get("HOENN", [])
          and (not _tm or _tm in _got),
          f"{_town}: {_ld['name']} fought turn by turn ({[(f[0], f[1]) for f in FOUGHT][-2:]}): "
          f"{'the ' + _b.title() + ' Badge' if _b in story.badges.get('HOENN', []) else 'NO badge'} and {sorted(_got) or 'no TM'} (wants {_tm})")
    g.gym_room_return = None

# ================================================================================ 3. the Elite Four and Steven
print("\n3) the Elite Four and Steven, room by room (battles fought turn by turn)")
LEAGUE = (("league_sidney", "Sidney"), ("league_phoebe", "Phoebe"), ("league_glacia", "Glacia"), ("league_drake", "Drake"),
          ("league_champion", "Steven"))


def league_round():
    out = []
    for _i, (_room, _who) in enumerate(LEAGUE, 1):
        st = open_map("EVER_GRANDE_CITY", "HOENN_VICTORY_ROAD")
        st._go(_room, "")
        frames(2)
        for _p in story.player_team:
            _p.heal_full()
        FOUGHT.clear()
        _o = next((v for v in st.people.values() if isinstance(v, dict) and v.get("text") == _who), None)
        if _o is None:
            out.append((_who + f" (not in {_room})", None, None, False))
            break
        g.transitioning = False
        st._get_callback_for_option(_o)()
        drive()
        g.gym_room_return = None
        _won = story.story_flags.get("beat_hoenn_champion" if _i == 5 else f"league_won_EVER_GRANDE_CITY_{_i}")
        out.append((FOUGHT[0] if FOUGHT else (_who, None, None)) + (_won,))
    return out


at("league")
story.player_team = [ace(), ace()]
story.story_flags["gym_progress_EVER_GRANDE_CITY"] = 0
for _k in [k for k in story.story_flags if k.startswith("league_won_EVER_GRANDE_CITY")] + ["beat_hoenn_champion", "beat_hoenn_elite_four"]:
    story.story_flags.pop(_k, None)
_l = league_round()
for (_room, _who), _r in zip(LEAGUE, _l):
    check(_r[1] is not None and not str(_r[0]).endswith("(UNFINISHED)") and _r[-1],
          f"{_who}: fought turn by turn and beaten ({_r[0]}, {_r[1]}; won: {_r[-1]})")
check(story.story_flags.get("beat_hoenn_champion") and len(_l) == 5, "...the title: the Elite Four and Steven beaten")

# ================================================================================ 4. the League rematch
print("\n4) after the title: the League rematch (ORAS's rematch teams; ORAS has no Gym Leader rematches)")
at("champion", also=True)
story.player_team = [ace() for _ in range(6)]   # (a full six: three sometimes lost to Glacia's Lv 72-74 rematch team, 11-24)
_league = _area["EVER_GRANDE_CITY"]["gym"]
_want = [t.get("rematch") for t in _league.get("trainers", [])] + [_league["leader"].get("rematch")]
story.story_flags["gym_progress_EVER_GRANDE_CITY"] = 0
for _k in [k for k in story.story_flags if k.startswith("league_won_EVER_GRANDE_CITY")]:
    story.story_flags.pop(_k, None)
_rm = league_round()
_match = [bool(w) and r[2] == w.get("team") and r[1] == [max(70, int(x)) for x in w.get("levels")] for r, w in zip(_rm, _want)]
check(len(_rm) == 5 and all(_match) and not any(str(r[0]).endswith("(UNFINISHED)") for r in _rm),
      f"the League rematch: all five fought again with ORAS's rematch teams, every Pokemon at least Lv 70 (Jordan's League rematch rule) "
      f"({[(r[0], r[1]) for r in _rm]}; as the data: {_match})")

print("\n5) Emerald's own music (assets/music/hoenn, hoenn_rom_tools/hmusic.py): each place's theme, its rooms', the battles")
_mt = json.load(open("assets/music/hoenn/music.json", encoding="utf-8"))
_names = {v for v in list(_mt["areas"].values()) + list(_mt["rooms"].values()) + list(_mt["kinds"].values()) if isinstance(v, str)}
_missing = sorted(n for n in _names if not os.path.isfile(os.path.join("assets", "music", "hoenn", n + ".ogg")))
check(not _missing and len(_mt["areas"]) >= 80, f"every track named is there ({len(_names)} tracks, {len(_mt['areas'])} places; missing {_missing})")
_m = g.music
story.current_area_key = "LITTLEROOT_TOWN"
g.walk_town_room = None
_t = _m.region_track("town", "HOENN")
check(bool(_t) and _t.endswith("em_405.ogg"), f"Littleroot Town plays its own Emerald theme ({_t and os.path.basename(_t)})")
story.current_area_key = "HOENN_ROUTE_101"
_t = _m.region_track("route", "HOENN")
check(bool(_t) and _t.endswith("em_359.ogg"), f"...Route 101 its own ({_t and os.path.basename(_t)})")
_k = {k: (_m.region_track(k, "HOENN") or "") for k in ("wild", "trainer", "gym", "final", "villain", "center", "victory")}
check(all(_k.values()) and _k["wild"].endswith("em_474.ogg") and _k["gym"].endswith("em_477.ogg") and _k["final"].endswith("em_482.ogg"),
      f"...and the battles Emerald's: {[(k, os.path.basename(v)) for k, v in _k.items()]}")

print(f"##### {len(fails)} failures")
for m in fails:
    print("   FAIL " + m)
