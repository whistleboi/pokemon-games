# Unova's walkable pilot (11-19): Black 2 / White 2's opening in Aspertia City, played the way a new game meets it.
# Wake in your room; Mom stops you at the door; Hugh and his sister outside; Bianca at the Outlook with the starters;
# the Pokedex and Hugh's battle; Bianca's tour of the Pokemon Center; Mom and Hugh's sister at its door; out through the
# gate to Route 19. Screenshots go to dev/checks/out/unova_*.png. Glue after harness_head.py:
#   bash dev/checks/run.sh unova_start
import json
from src.states.overworld import CityState, PlayState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.states.menus import StarterSelectionState as _SSS, region_opening_state
from src.states.battle import TrainerIntroState, TrainerBattleState

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "nate"
g.rival_name = "HUGH"
said = []


def _note(st):
    box = getattr(st, "npc_dialogue", None) if getattr(st, "npc_active", False) else getattr(st, "dialogue_box", None)
    if box is not None and getattr(box, "visible", True):
        for line in getattr(box, "text_lines", []) or []:
            if not said or said[-1] != line:
                said.append(line)


def play(until, n=3000):
    for _ in range(n):
        if until():
            return True
        st = g.current_state
        if type(st).__name__ in ("HallOfFameState", "IntroSpeechState"):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "npc_active", False):
            _note(st)
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif not isinstance(st, _WTS) and getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            _note(st)
            st.dialogue_box.advance()
        st.update(); st.draw()
    return until()


def walk(st, path):
    for c in path:
        d = {"u": (0, -1), "d": (0, 1), "l": (-1, 0), "r": (1, 0)}[c]
        play(lambda: not g.current_state._busy() and g.current_state.anim == 0, 400) if isinstance(g.current_state, _WTS) else None
        g.current_state.step(*d)
        play(lambda: isinstance(g.current_state, _WTS) and g.current_state.anim == 0, 60)


def shot(name):
    g.current_state.draw()
    pygame.image.save(pygame.display.get_surface(), f"{S}/unova_{name}.png")


def idle():
    return isinstance(g.current_state, _WTS) and not g.current_state._busy() and g.current_state.anim == 0


flags = story.story_flags
for f in [k for k in flags if k.startswith("b2_") or k.endswith("_unova")]:
    flags.pop(f, None)
story.player_team = []
story.starting_region = "UNOVA"
story.badges["UNOVA"] = []
story.inventory.pop("TOWN_MAP", None)
_tm = json.load(open("assets/town_maps.json", encoding="utf-8"))

print("1) the map: Aspertia City from Black 2's own layout, through RPG Maker XP")
a = _tm.get("ASPERTIA_CITY") or {}
check(len(a.get("art", [])) == 64 and len(a["art"][0]) == 32, f"Aspertia is Black 2's 32 x 64 tiles ({len(a.get('art', []))} rows)")
check("b2_ground/427.png" in json.dumps(a.get("roofs", {})) and len(a["roofs"].get("_objects", [])) >= 12,
      f"drawn from Black 2's own ground and building models ({len(a.get('roofs', {}).get('_objects', []))} buildings)")
check(set(a.get("rooms", {})) >= {"home", "hugh", "hugh_2f", "center", "school", "gate"}, f"its rooms ({sorted(a.get('rooms', {}))})")
check(g.story_manager.get_region_start("UNOVA").get("start_area") == "ASPERTIA_CITY", "a new Unova game starts in Aspertia City (not Nuvema)")

print("2) the opening, from the title screen's new game")
flags.pop("unova_version", None)
st = region_opening_state(g, "UNOVA")
g.change_state(st)
from src.states.unova import UnovaVersionState
check(isinstance(st, UnovaVersionState), f"first: Black 2 or White 2, like Hoenn's version pick ({type(st).__name__})")
if isinstance(st, UnovaVersionState):
    st.choose("WHITE_2")
from src.world import unova_version as _uv
check(flags.get("unova_version") == "WHITE_2" and _uv.words(story)["legend"] == "Reshiram", "White 2 picked: Reshiram's story")
_cx = g.loader.area_data["STORY_PROGRESSION"]["VIRBANK_COMPLEX"]
from src.world import wild_tables as _wt
check("239" in _wt.pool(_cx, "grass") and "240" in _wt.pool(_cx, "grass"),
      "the version changes the story, not the wild Pokemon: Elekid and Magby both in the Virbank Complex")
_sp = g.loader.area_data["STORY_PROGRESSION"]
check(any((a.get("area_boss") or {}).get("id") == 644 for a in _sp.values() if isinstance(a, dict))
      and any((a.get("area_boss") or {}).get("id") == 643 for a in _sp.values() if isinstance(a, dict)),
      "Zekrom and Reshiram both have a place: every species in one playthrough, whichever version")
from src.states.overworld.common import _fill_names
check("Reshiram" in _fill_names(g, "the legendary Pokemon {legend}") or story.get_current_region() != "UNOVA",
      "the version's words in lines: {legend} is Reshiram")
play(lambda: isinstance(g.current_state, _WTS), 900)
t = g.current_state
check(isinstance(t, _WTS) and t.area_key == "ASPERTIA_CITY" and t.room == "home" and tuple(t.player) == (13, 6),
      f"you start in your room at home ({getattr(t, 'area_key', None)}, {getattr(t, 'room', None)}, {getattr(t, 'player', None)})")
shot("01_home")
said.clear()
t.player = (5, 6); t.anim = 0
walk(t, "d")
play(lambda: flags.get("b2_mom_talk") and idle(), 1500)
check(flags.get("b2_mom_talk") and any("Juniper" in s for s in said) and any("green hat" in s for s in said),
      f"Mom stops you on the way out: Professor Juniper, a Pokemon, Bianca in the green hat ({len(said)} lines)")
t = g.current_state
t.player = (5, 9); t.anim = 0
said.clear()
walk(t, "d")
play(lambda: flags.get("b2_hugh_met") and idle(), 3000)
t = g.current_state
check(t.room is None and flags.get("b2_hugh_met") and any("Bianca" in s for s in said) and any("sister" in s for s in said),
      f"outside: HUGH and his sister come over; he's coming to find Bianca with you ({said[:1]})")
check(any("HUGH" in s for s in said), "Hugh speaks under the name you gave him")
shot("02_town")

print("3) Bianca at the Outlook, the starter, the Pokedex, Hugh's battle")
t.player = (5, 12); t.anim = 0; t.facing = (0, -1)
said.clear()
walk(t, "u")
shot("02b_outlook")
walk(t, "u")
play(lambda: isinstance(g.current_state, _SSS), 3000)
s = g.current_state
check(any("Pokedex" in x for x in said) and any("Bianca" in x for x in said), f"Bianca, at the Outlook, asks you to help with the Pokedex ({said[:2]})")
check(isinstance(s, _SSS) and s.region == "UNOVA", f"her case opens the starter screen ({type(s).__name__})")
if isinstance(s, _SSS):
    s.load_starters(); s.selected_idx = [p.id for p in s.starters].index(495); s.complete_selection()
    check(flags.get("received_starter_unova") and story.player_team and story.player_team[0].id == 495, "you choose Snivy")
    s.dialogue_box.callback()
said.clear()
play(lambda: isinstance(g.current_state, (TrainerIntroState, TrainerBattleState)), 3000)
check(flags.get("received_pokedex_unova") and any("Pokedex" in x for x in said), "Bianca hands you the Pokedex")
b = g.current_state
b = getattr(b, "next_state", None) or b
check(isinstance(b, TrainerBattleState) and [p.id for p in b.opponent_team] == [498] and b.opponent_team[0].level == 5,
      f"Hugh battles you with the starter strong against yours: Tepig, Lv. 5 ({[(p.id, p.level) for p in getattr(b, 'opponent_team', [])]})")
if isinstance(b, TrainerBattleState):
    g.change_state(b)
    b.player_won = True
    b.exit_battle()

print("4) Bianca's tour of the Pokemon Center; Mom and Hugh's sister at its door")
balls0 = story.balls_left
said.clear()
play(lambda: flags.get("b2_center_tour") and idle(), 5000)
t = g.current_state
check(flags.get("b2_led_to_center") and getattr(t, "room", None) == "center", f"Bianca leads you into the Pokemon Center ({getattr(t, 'room', None)})")
check(flags.get("b2_center_tour") and story.balls_left == balls0 + 10, f"...shows you round and gives you 10 Poke Balls ({story.balls_left - balls0})")
shot("03_center")
_door = next(xy for xy, v in t.exits.items() if str(v).startswith("OUT:"))
t.player = (_door[0], _door[1] - 1); t.anim = 0
said.clear()
walk(t, "d")
play(lambda: flags.get("b2_send_off") and idle(), 5000)
t = g.current_state
check(t.room is None and flags.get("b2_send_off") and flags.get("b2_town_map") and any("Running Shoes" in x for x in said),
      f"outside, Mom brings Running Shoes and Hugh's sister a Town Map ({said[:1]})")
shot("04_send_off")

print("5) free in Aspertia: north through the gate to Route 19")
t.player = (20, 7); t.anim = 0; t.facing = (0, -1)
walk(t, "u")
play(idle, 300)
t = g.current_state
check(getattr(t, "room", None) == "gate", f"into Aspertia Gate ({getattr(t, 'room', None)})")
_pot = story.inventory.get("POTION", 0)
_g = next((xy for xy, o in t._people().items() if o.get("text") == "Gate guard"), None)
if _g:
    t._talk(_g); play(idle, 600)
check(story.inventory.get("POTION", 0) == _pot + 1, "the gate guard's going-away Potion")
_up = next(xy for xy, v in t.exits.items() if v == "UNOVA_ROUTE_19")
t.player = (_up[0], _up[1] + 1); t.anim = 0
walk(t, "u")
play(lambda: story.current_area_key == "UNOVA_ROUTE_19", 900)
check(story.current_area_key == "UNOVA_ROUTE_19", f"out the far side onto Route 19 ({story.current_area_key})")

print(f"##### {len(fails)} failures")
