# Unova batch 10b (11-24): the Pokemon League - the forecourt (Black 2's 64 x 64 block), its Center, the plaza, the four
# Elite Four rooms (any order) and their rematches, the statue down to Iris's temple, the Champion, the Hall of Fame.
#   bash dev/checks/run.sh unova_b10b
import json
from src.states.overworld import CityState, PlayState
from src.states.overworld import walk_town as WT


fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "nate"
flags = story.story_flags
flags["unova_version"] = "BLACK_2"; story.starting_region = "UNOVA"
NEW = ("UNOVA_POKEMON_LEAGUE", "VICTORY_ROAD_TUNNEL")
for a in NEW:
    flags["visited_" + a] = True
story.badges["UNOVA"] = ["BASIC", "TOXIC", "INSECT", "BOLT", "QUAKE", "JET", "LEGEND", "WAVE"]
for k in ("b2_mom_talk", "b2_jet_badge", "b2_lucky_egg", "b2_lentimas_flight", "b2_lentimas_juniper", "visited_UNDELLA_TOWN",
          "b2_lacunosa_juniper", "b2_lacunosa_tale", "b2_lacunosa_zinzolin", "b2_legend_badge", "b2_opelucid_cheren",
          "visited_OPELUCID_CITY", "visited_HUMILAU_CITY", "b2_wave_badge", "b2_humilau_after",
          "b2_colress_mchn", "b2_seaside_crustle", "b2_frigate_done", "b2_frigate2_open", "b2_frigate2_done",
          "b2_r21_cheren", "b2_opelucid_frozen", "b2_chasm_done", "b2_opelucid_thawed", "b2_kyurem_fused",
          "b2_ghetsis_beaten", "b2_vr_hugh", "b2_vr_waterfall", "b2_badge_check", "move_offer_unova"):
    flags[k] = True
said = []
tmaps = json.load(open("assets/town_maps.json", encoding="utf-8"))
_TEAMS = json.load(open("dev/builders/town_maps/unova_teams.json", encoding="utf-8"))
prog = json.load(open("assets/unova_area_data.json", encoding="utf-8"))
SP = prog["STORY_PROGRESSION"]


exec(open("dev/checks/unova_lib.py", encoding="utf-8").read())   # (settle, heard, town, until, _opts, talk, walked, team_of, win, battle_talk, go: shared, Checks C5)


def where():
    return story.current_area_key, tuple(getattr(getattr(g.current_state, "run", None), "player", None) or getattr(g.current_state, "player", (0, 0)))


BATTLES = ("TrainerIntroState", "TrainerBattleState", "DoubleBattleState", "GymBattleState", "BattleState")


def mains():
    return [m["id"] for m in story.get_active_missions() if m["type"] == "MAIN"]


def figure(st, text):
    return next((m for m in st.run.floor.movers if isinstance(getattr(m, "payload", None), dict)
                 and str(m.payload.get("text", "")).rstrip() == text.rstrip()), None)


def use(st, text):
    m = figure(st, text)
    if m is None:
        return False
    said.clear(); st._use_figure(m); settle(80)
    return True


def opts(m):
    return [c for o in m.get("people") or [] for c in _opts(o) if isinstance(c, dict)]




print("1) the League's maps")
lg = tmaps["UNOVA_POKEMON_LEAGUE"]
rooms = lg["rooms"]
check({"plaza", "chamber", "temple", "hof", "center", "approach", "shauntal", "grimsley", "caitlin", "marshal"} <= set(rooms),
      "the forecourt, its Center, the plaza, four Elite Four rooms, the chamber, Iris's temple, the Hall of Fame")
check(sum(r.count(".") for r in lg["art"]) > 300, "the forecourt walkable (Black 2's one 64 x 64 block)")
check("VICTORY_ROAD_TUNNEL" in rooms["approach"]["exits"].values() and tmaps["VICTORY_ROAD_TUNNEL"]["exits"].get("^") == "UNOVA_POKEMON_LEAGUE",
      "Victory Road's tunnel to the League and back, by the last stretch")
plaza_to = {v for v in rooms["plaza"]["exits"].values()}
check({"ROOM:shauntal", "ROOM:grimsley", "ROOM:caitlin", "ROOM:marshal"} <= plaza_to, "the plaza's four doors")
st = rooms["plaza"]["sign_events"]["31,44"]["event"]
check(st["requires"] == ["b2_e4_shauntal", "b2_e4_grimsley", "b2_e4_caitlin", "b2_e4_marshal"] and st["lift"][0][1] == "chamber",
      "the statue carries you down once all four are beaten")
want = {"shauntal": (38, 143), "grimsley": (40, 145), "caitlin": (41, 146), "marshal": (39, 144)}
for k, (a, b) in want.items():
    o = opts(rooms[k])
    first = next(c for c in o if (c.get("event") or {}).get("flag") == "b2_e4_" + k)
    again = next(c for c in o if "beat_unova_champion" in (c.get("condition") or []) and (c.get("event") or {}).get("battle"))
    check(first["event"]["battle"]["team"] == _TEAMS[str(a)]["team"] and again["event"]["battle"]["team"] == _TEAMS[str(b)]["team"],
          f"{k}: Black 2's team, then the rematch's")
iris = [c for c in opts(rooms["temple"]) if (c.get("event") or {}).get("battle")]
check(iris[0]["event"]["flag"] == "beat_unova_champion" and iris[0]["event"]["battle"]["team"] == _TEAMS["341"]["team"]
      and iris[1]["event"]["battle"]["team"] == _TEAMS["536"]["team"], f"Iris: Black 2's Champion team, then her rematch's")
hof = rooms["hof"]["scenes"][0]["event"]
check(hof["scene"] == "hall_of_fame" and hof["travel"] == "ASPERTIA_CITY", "the Hall of Fame, then home to Aspertia")

from src.dungeon import art as _ART
from src.states.overworld.walk_town import MORE_EXIT_CHARS as _MORE
_pz = tmaps["UNOVA_POKEMON_LEAGUE"]["rooms"]["plaza"]
check(sorted(v for k, v in _pz["exits"].items() if k in set(_ART.EXIT_CHARS) | _MORE and any(k in r for r in _pz["art"]))
      == ["OUT:31,45", "ROOM:caitlin", "ROOM:grimsley", "ROOM:marshal", "ROOM:shauntal"],
      "every Elite Four door is a way out the walker reads (11-25, the Journal's PT_FULL: three were '2'-'4', a Cut tree's letter)")

print("2) an Elite Four battle: Shauntal")
for k in ("b2_e4_shauntal", "b2_e4_grimsley", "b2_e4_caitlin", "b2_e4_marshal", "beat_unova_champion", "b2_hall_of_fame"):
    flags.pop(k, None)
st = town("UNOVA_POKEMON_LEAGUE", (15, 8), "shauntal")
ok = talk(st, "Shauntal")
cur = until(BATTLES, 800)
t = team_of(cur)
check(ok and type(cur).__name__ in BATTLES and [s for s, _l in t] == _TEAMS["38"]["team"], f"Shauntal battles you ({t})")
if type(cur).__name__ in BATTLES:
    win(cur)
check(flags.get("b2_e4_shauntal"), "Shauntal beaten")

print("3) Iris")
for k in ("b2_e4_grimsley", "b2_e4_caitlin", "b2_e4_marshal"):
    flags[k] = True
from src.states.systems.pick_list import PickListState
st = town("UNOVA_POKEMON_LEAGUE", (31, 45), "plaza")
st.player = st.anim_from = (31, 45); st.facing = (0, -1); settle(2)
st.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, unicode=" ", mod=0)])
settle(60)
pl = g.current_state
check(isinstance(pl, PickListState), f"the statue's plaque, read with the action key, offers the lift ({type(pl).__name__})")
if isinstance(pl, PickListState):
    pl.pick(pl.choices[0][1]); settle(200)
check(getattr(g.current_state, "room", None) == "chamber" and not getattr(g, "transitioning", False) and not getattr(g.current_state, "npc_active", False),
      f"down to the chamber, the game back to you (11-25, the Journal's PT_FULL: it hung) ({getattr(g.current_state, 'room', None)}, "
      f"{getattr(g, 'transitioning', None)})")
st = town("UNOVA_POKEMON_LEAGUE", (16, 40), "temple")
hx = [t_ for t_, o in st.people.items() if "Haxorus" in str(o)]
check((16, 35) not in [tuple(getattr(m, "pos", (0, 0))) for m in getattr(st, "motions", {}).values()] and st._open((16, 35)) if hasattr(st, "_open") else True,
      "nothing stands in the temple's corridor in front of Iris (her Haxorus did: 11-25)")
st = town("UNOVA_POKEMON_LEAGUE", (16, 35), "temple")
ok = talk(st, "Iris")
cur = until(BATTLES, 800)
t = team_of(cur)
check(ok and type(cur).__name__ in BATTLES and [s for s, _l in t] == _TEAMS["341"]["team"], f"Iris battles you ({t})")
if type(cur).__name__ in BATTLES:
    win(cur)
settle(300)
check(flags.get("beat_unova_champion"), "Champion of Unova")
story.current_area_key = "UNOVA_POKEMON_LEAGUE"
check("b2_m46" not in mains(), f"the Journal: the League done ({mains()})")

for f_ in fails:
    print("  -", f_)
print(f"##### {len(fails)} failures")
