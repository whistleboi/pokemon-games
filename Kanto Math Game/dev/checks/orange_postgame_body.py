# The Orange Islands after the title, PLAYED (11-23, Jordan: "to make sure everything is good"): every legendary battled on
# its map (Lugia, Moltres, Zapdos, Articuno, Mewtwo, Ho-Oh, Celebi), the Master Ball picked up, and the rematches the
# game offers (Cissy's Gym hall, Drake's Stadium) fought, their levels read off the battle (main's rule: + the canon
# League boost; the League floor 70). Helpers as orange_events_body.py (from kanto_events_body.py).
#   bash dev/checks/run_par.sh orange_postgame
import json, os
from src.states.overworld import PlayState, CityState as _CS
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.dungeon import core
from src.pokemon import moves as _mv

fails = 0
g.dungeon_routes = True
g.walk_towns = True
g.player_character = "red"   # (any look will do)
said = []


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def frames(n=1):
    for _ in range(n):
        g.current_state.update()
        g.current_state.draw()


def _note(st):
    box = getattr(st, "npc_dialogue", None) if getattr(st, "npc_active", False) else getattr(st, "dialogue_box", None)
    if box is not None and getattr(box, "visible", True):
        for line in getattr(box, "text_lines", []) or []:
            if not said or said[-1] != line:
                said.append(line)


def play(picks=(), n=3000, until=None):
    """Run the game as a player: tap through what's said, answer each pick list with the next of picks (by value, or
    True for the first), fight battles with the right answers. Stops when nothing is left to do (or until() is true)."""
    picks = list(picks)
    quiet = 0
    for _ in range(n):
        if until and until():
            return True
        st = g.current_state
        name = type(st).__name__
        if name == "PickListState":
            v = picks.pop(0) if picks else None
            if v is None:
                st.done(None) if hasattr(st, "done") else None
            elif v is True:   # (the first choice on the list)
                c0 = (getattr(st, "choices", None) or [None])[0]
                st.pick(c0[1] if isinstance(c0, (tuple, list)) else c0)
            else:
                st.pick(v) if hasattr(st, "pick") else st.done(v)
            quiet = 0
        elif hasattr(st, "math_ui") and hasattr(st, "phase"):
            _fight(st)
            quiet = 0
        elif getattr(st, "npc_active", False):
            _note(st)
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            quiet = 0
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            _note(st)
            st.dialogue_box.advance()
            quiet = 0
        else:
            quiet += 1
            if quiet > 40 and until is None:
                return True
        st.update(); st.draw()
    return until() if until else True


def _fight(b, n=8000):
    for _k in range(n):
        if g.current_state is not b:
            return
        if b.phase == "SWITCH_PROMPT" and b.btn_no.visible and b.btn_no.callback:
            b.btn_no.callback()
        elif b.phase == "MENU" and not b.dialogue_box.visible:
            b.open_move_menu()
            b.choose_move(b.move_buttons[0].text.replace(" ", "-"))
            b.math_ui.on_click(b.options.index(b.correct_ans))
        elif b.dialogue_box.visible:
            _note(b)
            b.dialogue_box.is_finished = True
            if b.phase in ("OUTRO", "VICTORY_TEXT", "REWARD_TEXT"):
                b.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            elif b.dialogue_box.callback:
                cb = b.dialogue_box.callback; b.dialogue_box.callback = None; cb()
        b.feedback_timer = 0
        b.update(); b.draw()


def town(area, came, room=None):
    g.walk_town_pos = g.walk_town_exit = g.walk_town_room = None
    story.current_area_key, story.last_area_key = area, came
    t = _CS(g); g.change_state(t); frames(2); play()
    if room:
        t._go(room, ""); frames(2)
    return t


def place(area, came):
    """Open an area the way the game does: a town's walking map, or a route's."""
    a = g.loader.area_data["STORY_PROGRESSION"].get(area, {})
    return town(area, came) if a.get("area_type") == "town" else route(area, came)


def route(area, came, floor=0):
    core.ENTRANCE_INDEX, core.ENTRANCE_COUNT = 0, 0
    story.current_area_key, story.last_area_key = area, came
    p = PlayState(g)
    g.states["play"] = p
    g.change_state(p)
    frames(3); play()
    p = g.current_state
    if floor:
        p.run.enter_floor(floor); frames(2)
    return p


def meet(st, text, picks=(), n=3000):
    """Walk into whoever is called text on this map (from an open tile beside them) and play out what follows."""
    said.clear()
    if isinstance(st, _WTS):
        spot = next((s for s, o in st._people().items() if o.get("text") == text), None)
        if spot is None:   # (in one of the town's rooms: go in)
            for room in (st.town_map.get("rooms") or {}):
                st._go(room, ""); frames(2)
                spot = next((s for s, o in st._people().items() if o.get("text") == text), None)
                if spot is not None:
                    break
        if spot is None:
            return None
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            b = (spot[0] + dx, spot[1] + dy)
            if st._open(b) and b not in st.exits:
                st.player = st.anim_from = b; st.anim = 0; st.walk_goal = None
                st.step(-dx, -dy)
                break
        else:
            return None
    else:
        hit = lambda fl: next((m for m in fl.movers if m.kind in ("figure", "trainer") and isinstance(m.payload, dict) and m.payload.get("text") == text), None)
        if hit(st.run.floor) is None:   # (on another floor, or in a room of the route: rooms are floors after the map's own)
            for i in range(st.run.n_floors):
                if hit(st.run.made(i)) is not None:
                    st.run.enter_floor(i); frames(2)
                    break
        f = st.run.floor
        f.movers = [m for m in f.movers if m.kind != "wild"]
        m = hit(f)
        if m is None:
            return None
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            b = (m.x + dx, m.y + dy)
            if f.walkable(*b) and f.mover_at(*b) is None and b not in f.exits:
                st.run.player = b; st.anim = 0
                st.step(-dx, -dy)
                break
        else:
            return None
    play(picks, n)
    return list(said)


def team(*ids, level=50):
    story.player_team = [mk(i) for i in ids]
    for p in story.player_team:
        p.level = level
        p.heal_full()
    return story.player_team


def ace():
    """A team that wins (as kanto_maps' Mewtwo): Lv 100, Psychic and Ice Beam."""
    a = mk(150); a.level = 100; a.moves = ["PSYCHIC", "ICE-BEAM"]; a.heal_full()
    story.player_team = [a]
    return a



# ---------------------------------------------------------------- Orange (11-23, batch O4; AUDIT_GUIDE step 8)
from src.pokemon import tms as _tmsmod
story.enter_region("ORANGE") if hasattr(story, "enter_region") else None
_P = g.loader.area_data["STORY_PROGRESSION"]
_DEX = g.loader.area_data["REGION_START"]["ORANGE"]["dex_list"]
_flags0, _inv0, _team0, _money0 = dict(story.story_flags), dict(story.inventory), list(story.player_team), story.money
story.balls_left = 20


_TM = json.load(open("assets/town_maps.json", encoding="utf-8"))
story.story_flags["received_starter_orange"] = True


def _scenes_seen(area):
    """A player who comes back to a place has seen its story scenes: mark the map's scenes (and its rooms' and floors')
    as played, so none holds you on arrival (the test starts from a fresh Orange save)."""
    m = _TM.get(area) or {}
    parts = [m] + list(m.get("floors") or []) + list((m.get("rooms") or {}).values())
    for part in parts:
        for sc in part.get("scenes") or []:
            if sc.get("flag"):
                story.story_flags[sc["flag"]] = True


_place = place


def place(area, came):
    _scenes_seen(area)
    return _place(area, came)


def _came(area):
    """A neighbour to arrive from: the first area the map's own exits name (else Valencia)."""
    m = json.load(open("assets/town_maps.json", encoding="utf-8")).get(area) or {}
    for f in (m.get("floors") or [m]):
        for v in (f.get("exits") or {}).values():
            v = str(v)
            if v and not v.startswith(("OUT", "ROOM")) and v in _P:
                return v
    return "VALENCIA_ISLAND"


_meet = meet


def meet(st, text, picks=(), n=3000):
    """As kanto_events' meet, tried again when nothing was said (a Feat pop-up on arrival can swallow the first step)."""
    for _ in range(3):
        w = _meet(g.current_state if g.current_state is not st and type(g.current_state) is type(st) else st, text, picks, n)
        if w:
            return w
    return w


def _learner(move):
    """A young Pokemon from Orange's dex that can learn this move and doesn't know it yet."""
    tm = _tmsmod.key_for_move(g, move)
    for pid in _DEX:
        p = mk(pid); p.level = 5
        if tm and _tmsmod.can_learn(g, p, tm) and move not in _mv.move_pool(g, p):
            return pid
    return None



# ---------------------------------------------------------------- after the title
from src.world import levels as _lv
TEAMS = []
_fight0 = _fight


CATCH = {"on": False}


def _fight(b, n=8000):   # (as the helpers' _fight, writing down the foe's team first; with CATCH on, throw at the catch window)
    TEAMS.append([(int(getattr(p, "id", 0)), int(getattr(p, "level", 0))) for p in (getattr(b, "opponent_team", None) or [])])
    if not CATCH["on"]:
        return _fight0(b, n)
    for _k in range(n):
        if g.current_state is not b:
            return
        if b.phase == "CATCH_PROMPT":
            b.catch_yes()
        elif b.phase == "MENU" and not b.dialogue_box.visible:
            b.open_move_menu()
            b.choose_move(b.move_buttons[0].text.replace(" ", "-"))
            b.math_ui.on_click(b.options.index(b.correct_ans))
        elif b.dialogue_box.visible:
            _note(b)
            b.dialogue_box.is_finished = True
            if b.phase in ("OUTRO", "VICTORY_TEXT", "REWARD_TEXT"):
                b.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            elif b.dialogue_box.callback:
                cb = b.dialogue_box.callback; b.dialogue_box.callback = None; cb()
        b.feedback_timer = 0
        b.update(); b.draw()


def lobby_run(n=40):
    """A Gym lobby or the League's hall screen: CHALLENGE, fight it out, then leave."""
    for _ in range(n):
        st = g.current_state
        if type(st).__name__ == "GymLobbyState":
            if TEAMS and getattr(st, "_pt_done", False):
                st.exit_gym(); play(); return
            st._pt_done = True
            st.challenge_gym()
        play(n=4000, until=lambda: type(g.current_state).__name__ == "GymLobbyState")
        if type(g.current_state).__name__ != "GymLobbyState":
            return


story.badges["ORANGE"] = ["CORAL_EYE", "SEA_RUBY", "SPIKE_SHELL", "JADE_STAR", "WINNERS_TROPHY"]
story.story_flags.update({"beat_orange_champion": True, "heard_shamouti_legend": True, "shamouti_fire_sphere": True,
                          "shamouti_palace_taken": True, "shamouti_palace_crash": True, "shamouti_lightning_sphere": True,
                          "shamouti_lightning_done": True, "shamouti_lugia_rose": True, "shamouti_ice_sphere": True,
                          "shamouti_lugia_song": True, "orange_drake_met": True, "move_offer_orange": True})
for _it in ("HM_SURF", "CLIMB_KIT", "WHIRLPULLER", "PICKAXE", "SCUBA_GEAR"):
    story.inventory[_it] = 1

print("1) The legendaries after Lugia's song (and Ho-Oh and Celebi after the title): walk up, battle, win")
LEGENDS = [("FIRE_ISLAND", "SHAMOUTI_ISLAND", "MOLTRES", "shamouti_moltres_caught"),
           ("LIGHTNING_ISLAND", "SHAMOUTI_ISLAND", "ZAPDOS", "shamouti_zapdos_caught"),
           ("ICE_ISLAND", "SHAMOUTI_ISLAND", "ARTICUNO", "shamouti_articuno_caught"),
           ("ICE_ISLAND", "SHAMOUTI_ISLAND", "LUGIA", "shamouti_lugia_caught"),
           ("NEW_ISLAND", "HAMLIN_ISLAND", "MEWTWO", "orange_mewtwo_caught"),
           ("ORANGE_ROUTE_50", "TANGELO_ISLAND", "HO-OH", "orange_hooh_met"),
           ("ORANGE_ROUTE_73", "PUMMELO_ISLAND", "CELEBI", "orange_celebi_met")]
for area, came, who, flag in LEGENDS:
    story.story_flags.pop(flag, None)
    story.story_flags.pop(f"{area}_boss_defeated", None)
    for k in [k for k in story.defeated_trainers if k == area]:
        pass
    ace()
    n0 = len(TEAMS)
    st = place(area, came)
    w = meet(st, who)
    foe = TEAMS[n0] if len(TEAMS) > n0 else None
    check(w is not None and foe is not None and story.story_flags.get(flag),
          f"{area}: {who} - found on the map, battled ({foe}), and done ({flag}: {story.story_flags.get(flag)}) ({(w or [])[:1]})")

print("1b) Catching one: Ho-Oh, knocked down to the catch window, a Master Ball thrown, and it joins you")
story.story_flags.pop("orange_hooh_met", None)
ace()
story.inventory["MASTER_BALL"] = 1
story.selected_ball = "MASTER_BALL"
CATCH["on"] = True
w = meet(place("ORANGE_ROUTE_50", "TANGELO_ISLAND"), "HO-OH")
CATCH["on"] = False
ids = [p.id for p in story.player_team] + [p.id for p in (getattr(story, "pc_storage", None) or []) if hasattr(p, "id")]
check(250 in [p.id for p in story.player_team] or story.story_flags.get("caught_250") or any("caught" in l.lower() and "ho-oh" in l.lower() for l in said),
      f"...Ho-Oh is caught ({[p.id for p in story.player_team]}; {[l for l in said if 'caught' in l.lower()][:2]}) and gone from Route 50 ({story.story_flags.get('orange_hooh_met')})")

print("2) New Island's Master Ball, picked up where it lies")
story.story_flags.pop("got_master_ball_new_island", None)
story.inventory.pop("MASTER_BALL", None)
w = meet(place("NEW_ISLAND", "HAMLIN_ISLAND"), "MASTER BALL")
check(story.inventory.get("MASTER_BALL") == 1, f"...the Master Ball is in the Bag ({(w or [])[:1]})")

print("3) Rematches after the title, at main's rule (the canon League boost, the League's floor of 70)")
boost = _lv.canon_league_boost(g) if hasattr(_lv, "canon_league_boost") else None
ace()
n0 = len(TEAMS)
t = town("MIKAN_ISLAND", "ORANGE_ROUTE_53", "gym")
meet(t, "Gym")
lobby_run()
cissy = next((tm for tm in TEAMS[n0:] if tm and tm[0][0] == 117), None)
check(boost and cissy and cissy[-1][1] == 22 + boost,
      f"Mikan's Gym hall: Cissy again, her Blastoise at 22 + {boost} ({cissy}; all: {TEAMS[n0:]})")
ace()
n0 = len(TEAMS)
t = town("PUMMELO_ISLAND", "ORANGE_ROUTE_72", "league")
meet(t, "Drake")
lobby_run()
drake = next((tm for tm in TEAMS[n0:] if tm and tm[0][0] == 132), None)
check(drake and drake[-1][1] == max(70, 52 + (boost or 0)),
      f"Pummelo Stadium: Drake again, his Dragonite at max(70, 52 + {boost}) ({drake}; all: {TEAMS[n0:]})")

story.story_flags.clear(); story.story_flags.update(_flags0)
story.inventory.clear(); story.inventory.update(_inv0)
story.player_team, story.money = _team0, _money0
print(f"FAILURES: {fails}")
