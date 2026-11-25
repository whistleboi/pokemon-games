# Unova batch 7b (11-24): Undella Town (the gate north, the Center, the bay's edge), Undella Bay (its Swimmers, the weekly
# Jellicent), Route 13 (its trainers, the treasure hunter's daily Flute, the Power Lens / Band house, two Hidden Grottoes),
# Lacunosa Town (Juniper and Bianca, the old woman's tale, the double battle with Hugh against Zinzolin and a Grunt).
#   bash dev/checks/run.sh unovab7b
import json
from src.states.overworld import CityState, PlayState


fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "nate"
flags = story.story_flags
flags["unova_version"] = "BLACK_2"; story.starting_region = "UNOVA"
NEW = ("UNDELLA_TOWN", "UNDELLA_BAY", "UNOVA_ROUTE_13", "LACUNOSA_TOWN")
for a in NEW:
    flags["visited_" + a] = True
story.badges["UNOVA"] = ["BASIC", "TOXIC", "INSECT", "BOLT", "QUAKE", "JET"]
for k in ("b2_mom_talk", "b2_jet_badge", "b2_lucky_egg", "b2_lentimas_flight", "b2_lentimas_juniper"):
    flags[k] = True
said = []
tmaps = json.load(open("assets/town_maps.json", encoding="utf-8"))
prog = json.load(open("assets/unova_area_data.json", encoding="utf-8"))
SP = prog["STORY_PROGRESSION"]


exec(open("dev/checks/unova_lib.py", encoding="utf-8").read())   # (settle, heard, town, until, _opts, talk, walked, team_of, go: shared, Checks C5)


def where():
    return story.current_area_key, tuple(getattr(getattr(g.current_state, "run", None), "player", None) or getattr(g.current_state, "player", (0, 0)))


BATTLES = ("TrainerIntroState", "TrainerBattleState", "DoubleBattleState")


print("1) the places")
for a in NEW:
    check(a in tmaps, f"{a} is walked")
for a, n in (("UNOVA_ROUTE_13", 11), ("UNDELLA_BAY", 6)):
    check(len(SP[a]["trainer_pool"]) == n, f"{a}: Black 2's {n} trainers")
for a in NEW:
    if a != "LACUNOSA_TOWN":
        check(bool(SP[a].get("wild_tables")), f"{a}: its wild Pokemon")
check({"grotto", "grotto2", "house_w", "house_e"} <= set(tmaps["UNOVA_ROUTE_13"]["rooms"]), "Route 13's houses and Hidden Grottoes")
check(not any(o.get("target_area") == "UNOVA_ROUTE_12" for o in SP["UNDELLA_TOWN"].get("travel_options") or []),
      "Undella's old shortcut to Route 12 is gone (no such road)")

print("2) Undella -> the gate -> Route 13 -> Lacunosa")
ds = walked("REVERSAL_MOUNTAIN_INSIDE", (7, 24), list(tmaps["REVERSAL_MOUNTAIN_INSIDE"]["rooms"]).index("east") + 1)
go(1, 0, 1, 80)
if where()[0] != "UNDELLA_TOWN":
    go(0, 1, 1, 80)
check(where()[0] == "UNDELLA_TOWN", f"out of Reversal Mountain into Undella ({where()})")
gate = tmaps["UNDELLA_TOWN"]["rooms"]["gate"]
check("UNOVA_ROUTE_13" in gate["exits"].values(), "the Undella Gate leads north to Route 13")
ds = walked("UNOVA_ROUTE_13", (33, 16))
go(-1, 0, 1, 120)
check(where()[0] == "LACUNOSA_TOWN", f"west from Route 13 into Lacunosa ({where()})")

print("3) Lacunosa: Juniper and Bianca, the old tale, Hugh against Zinzolin")
for k in ("b2_lacunosa_juniper", "b2_lacunosa_tale", "b2_lacunosa_zinzolin", "b2_lacunosa_hugh"):
    flags.pop(k, None)
flags["visited_UNDELLA_TOWN"] = True
main = [m["id"] for m in story.get_active_missions() if m["type"] == "MAIN"]
check("b2_m35" in main, f"the Journal: on to Lacunosa ({main})")
st = town("LACUNOSA_TOWN", (28, 16)); settle(1500)
check(flags.get("b2_lacunosa_juniper") and "Juniper" in heard(), "Juniper and Bianca meet you in Lacunosa")
st = town("LACUNOSA_TOWN", (6, 7), "elder", (0, -1)); settle(1500)
check(flags.get("b2_lacunosa_tale") and "meteorite" in heard(), "the old woman's tale of the Giant Chasm")
st = town("LACUNOSA_TOWN", (5, 26), face=(1, 0))
st.step(1, 0); settle(200)
cur = until(BATTLES, 1500)
t = team_of(cur)
check(type(cur).__name__ in BATTLES and 615 in [s for s, _ in t], f"you and your rival against Zinzolin and a Grunt ({t})")
if type(cur).__name__ in BATTLES:
    from src.states.battle import TrainerIntroState
    b = cur
    for _ in range(3):
        if isinstance(b, TrainerIntroState) and getattr(b, "next_state", None) is not None:
            b = b.next_state; g.change_state(b); settle(1)
    b.player_won = True
    if hasattr(b, "exit_battle"):
        b.exit_battle()
    settle(400)
check(flags.get("b2_lacunosa_zinzolin"), "Zinzolin's beaten")
main = [m["id"] for m in story.get_active_missions() if m["type"] == "MAIN"]
check("b2_m36" in main, f"the Journal: west to Opelucid ({main})")

print("4) Route 13's treasure hunter; the Power item house; the bay's Jellicent")
flags.pop("b2_r13_treasure", None)
flutes = ("BLUE_FLUTE", "RED_FLUTE", "YELLOW_FLUTE", "BLACK_FLUTE", "WHITE_FLUTE")
n0 = sum(story.inventory.get(f, 0) for f in flutes)
ds = walked("UNOVA_ROUTE_13", (43, 78))
st = g.current_state
hunter = next((c for o in tmaps["UNOVA_ROUTE_13"]["people"] for c in _opts(o) if isinstance(c, dict) and c.get("text") == "Treasure hunter"), None)
from src.world import unova_story
said.clear(); unova_story.event(st, hunter["event"], hunter["event"]["lines"], lambda ls: said.extend(ls))
n1 = sum(story.inventory.get(f, 0) for f in flutes)
said.clear(); unova_story.event(st, hunter["event"], hunter["event"]["lines"], lambda ls: said.extend(ls))
check(n1 == n0 + 1 and sum(story.inventory.get(f, 0) for f in flutes) == n1, "the treasure hunter's Flute: one a day")
jel = [c for o in tmaps["UNDELLA_BAY"]["people"] for c in _opts(o) if isinstance(c, dict) and c.get("action") == "BOSS"]
check(len(jel) == 2 and {tuple(c["condition"]) for c in jel} == {("weekday:mon", "unova_version:BLACK_2"), ("weekday:thu", "unova_version:WHITE_2")},
      "the bay's Jellicent: Mondays in Black 2, Thursdays in White 2")

for f_ in fails:
    print("  -", f_)
print(f"##### {len(fails)} failures")
