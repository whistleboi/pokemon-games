# Unova batch 9b (11-24): the Plasma Frigate off Route 21 (Hugh and Marlon's gangplank, the deck's Grunt, the North Entrance:
# Black 2's switches / White 2's password, the hall's warp rooms, the Command Center: Zinzolin, Kyurem, the Shadow Triad), and
# Cheren on the beach after.
#   bash dev/checks/run.sh unova_b9b
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
NEW = ("UNOVA_ROUTE_21", "PLASMA_FRIGATE", "HUMILAU_CITY", "UNOVA_ROUTE_22", "SEASIDE_CAVE")
for a in NEW:
    flags["visited_" + a] = True
story.badges["UNOVA"] = ["BASIC", "TOXIC", "INSECT", "BOLT", "QUAKE", "JET", "LEGEND", "WAVE"]
for k in ("b2_mom_talk", "b2_jet_badge", "b2_lucky_egg", "b2_lentimas_flight", "b2_lentimas_juniper", "visited_UNDELLA_TOWN",
          "b2_lacunosa_juniper", "b2_lacunosa_tale", "b2_lacunosa_zinzolin", "b2_legend_badge", "b2_opelucid_cheren",
          "visited_OPELUCID_CITY", "visited_HUMILAU_CITY", "b2_wave_badge", "b2_humilau_after",
          "b2_colress_mchn", "b2_seaside_crustle", "b2_frigate_done"):
    flags[k] = True
said = []
tmaps = json.load(open("assets/town_maps.json", encoding="utf-8"))
prog = json.load(open("assets/unova_area_data.json", encoding="utf-8"))
SP = prog["STORY_PROGRESSION"]


exec(open("dev/checks/unova_lib.py", encoding="utf-8").read())   # (settle, heard, town, until, _opts, talk, walked, team_of, win, battle_talk, go: shared, Checks C5)


def where():
    return story.current_area_key, tuple(getattr(getattr(g.current_state, "run", None), "player", None) or getattr(g.current_state, "player", (0, 0)))


BATTLES = ("TrainerIntroState", "TrainerBattleState", "DoubleBattleState", "GymBattleState", "BattleState")


def mains():
    return [m["id"] for m in story.get_active_missions() if m["type"] == "MAIN"]


print("1) the ship's second visit")
fr = tmaps["PLASMA_FRIGATE"]
sms = [sm for sm in fr.get("story_maps") or [] if "b2_frigate2_open" in sm["when"]]
check(len(sms) == 2 and {"unova_version:WHITE_2" in sm["when"] for sm in sms} == {True, False}, "the frigate off Route 21: each version's own")
f2b = next(sm["map"] for sm in sms if "unova_version:WHITE_2" not in sm["when"])
f2w = next(sm["map"] for sm in sms if "unova_version:WHITE_2" in sm["when"])
rooms = f2b["rooms"]
check({"north", "command", "hall", "room_nw", "room_w", "room_sw", "room_ne", "room_e", "room_se", "dining"} <= set(rooms),
      "the North Entrance, the Command Center, the hall and its rooms")
hall_to = {v for k, v in rooms["hall"]["exits"].items() if str(v).startswith("ROOM:")}
check(len(hall_to) >= 9, f"the hall's warp panels lead to the rooms ({len(hall_to)})")
bar = rooms["north"]["barred"][0]["until"]["condition"]
check(bar == ["b2_fs_1", "b2_fs_2", "b2_fs_3", "b2_fs_4"], "Black 2: the barrier waits on four switches")
check(f2w["rooms"]["north"]["barred"][0]["until"]["condition"] == ["b2_fp_password"], "White 2: the barrier waits on the password")
sw = [sc for sc in rooms["north"]["scenes"] if str(sc.get("flag", "")).startswith("b2_fs_")]
check(len(sw) == 4, "four switches beside the warp panels' landings")
clues = [c for r in f2w["rooms"].values() for o in r.get("people") or [] for c in _opts(o)
         if isinstance(c, dict) and str((c.get("event") or {}).get("flag", "")).startswith("b2_fp_clue_")]
card = [c for r in f2w["rooms"].values() for o in r.get("people") or [] for c in _opts(o)
        if isinstance(c, dict) and (c.get("event") or {}).get("flag") == "b2_fp_card"]
check(len(clues) == 5 and len(card) == 1, f"White 2: five password clues and the Plasma Card ({len(clues)}, {len(card)})")
nb = rooms["north"]["scenes"][0]["event"]["battle"]
check(nb["battle_options"]["double"] and nb["battle_options"]["partner"]["name"] == "{rival_name}",
      "the North Entrance: you and Hugh against two Grunts")
cc = rooms["command"]["scenes"]
check(cc[0]["event"]["battle"]["team"] == [615, 615, 461] and cc[0]["event"]["battle"]["battle_options"]["second_trainer"]["team"] == [110, 89],
      "the Command Center: you and Hugh against Zinzolin and a Grunt")
check(cc[1]["event"].get("travel") == "UNOVA_ROUTE_21" and cc[1]["flag"] == "b2_frigate2_done", "the Shadow Triad throws you back onto Route 21")

print("2) Route 21's cove: Hugh, Marlon's gangplank; the deck's Grunt")
for k in ("b2_frigate2_open", "b2_frigate2_deck", "b2_frigate2_done"):
    flags.pop(k, None)
ds = walked("UNOVA_ROUTE_21", (27, 48))
go(1, 0, 1, 60); settle(1500)
check(flags.get("b2_frigate2_open") and "gangplank" in heard(), "Marlon lowers the gangplank")
from src.states.overworld import walk_town as WT
check(WT.story_map(g, "PLASMA_FRIGATE") is not None and WT.story_map(g, "PLASMA_FRIGATE").get("rooms", {}).get("north"),
      "the ship is the second visit's now")
story.current_area_key = "UNOVA_ROUTE_21"
check("b2_m43" in mains(), f"the Journal: the ship ({mains()})")
flags["b2_frigate2_done"] = True
check("b2_m44" in mains(), f"the Journal: on to the Giant Chasm ({mains()})")

for f_ in fails:
    print("  -", f_)
print(f"##### {len(fails)} failures")
