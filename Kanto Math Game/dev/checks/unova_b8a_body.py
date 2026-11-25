# Unova batch 8a (11-24): Route 12, Village Bridge (Stonewall's 1,000th battle, the singer, the Hip Waders, the rest house),
# Route 11 (Virizion), Opelucid City in both versions' looks (Iris; Drayden's Gym: the dragon's head lift, level by level;
# Drayden), Drayden's house and the frozen city (the Grunts, Zinzolin, the Shadow Triad, Cheren's call), Mistralton's White 2 look.
#   bash dev/checks/run.sh unova_b8a
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
NEW = ("UNOVA_ROUTE_12", "VILLAGE_BRIDGE", "UNOVA_ROUTE_11", "OPELUCID_CITY")
for a in NEW:
    flags["visited_" + a] = True
story.badges["UNOVA"] = ["BASIC", "TOXIC", "INSECT", "BOLT", "QUAKE", "JET"]
for k in ("b2_mom_talk", "b2_jet_badge", "b2_lucky_egg", "b2_lentimas_flight", "b2_lentimas_juniper", "visited_UNDELLA_TOWN",
          "b2_lacunosa_juniper", "b2_lacunosa_tale", "b2_lacunosa_zinzolin"):
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


print("1) the places")
for a in NEW:
    check(a in tmaps, f"{a} is walked")
for a, n in (("UNOVA_ROUTE_12", 3), ("VILLAGE_BRIDGE", 7), ("UNOVA_ROUTE_11", 3)):
    check(len(SP[a]["trainer_pool"]) == n, f"{a}: Black 2's {n} trainers")
    check(bool(SP[a].get("wild_tables")), f"{a}: its wild Pokemon")
check({"house_1", "bakery", "waders", "house_4", "house_5", "rest", "singer", "gate_e", "gate_w"} <= set(tmaps["VILLAGE_BRIDGE"]["rooms"]),
      "Village Bridge's houses, the singer's room and both Bridge Gates")
ope = tmaps["OPELUCID_CITY"]
check({"gym", "center", "drayden", "drayden_2f", "gate_w", "gate_e"} <= set(ope["rooms"]), "Opelucid's Gym, Center, Drayden's house, gates")
check(len(ope.get("story_maps") or []) == 3 and ope["story_maps"][2]["map"]["art"] != ope["art"],
      "Opelucid: White 2's own look, and both versions frozen")
check(any(sw["when"] == ["unova_version:WHITE_2"] for sw in tmaps["MISTRALTON_CITY"].get("story_maps") or []),
      "Mistralton: White 2's own look (6b's gap)")
check(not SP["OPELUCID_CITY"].get("explore_options"), "Opelucid's old menu buttons are gone")
gym = SP["OPELUCID_CITY"]["gym"]["leader"]
check(gym["team"] == [621, 330, 612] and gym["levels"] == [46, 46, 48] and gym["rewards"].get("TM044"),
      f"Drayden: Druddigon, Flygon, Haxorus 46/46/48 and Dragon Tail ({gym['team']}, {gym['levels']})")

print("2) the road west: Route 12 -> the Bridge Gate -> Village Bridge -> Route 11 -> Opelucid")
ds = walked("UNOVA_ROUTE_12", (9, 15))
go(-1, 0, 2, 120)
check(where()[0] == "VILLAGE_BRIDGE", f"west from Route 12 onto Village Bridge ({where()})")
ds = walked("UNOVA_ROUTE_11", (8, 15))
go(-1, 0, 2, 120)
check(where()[0] == "OPELUCID_CITY", f"west from Route 11 into Opelucid ({where()})")

print("3) Village Bridge: Stonewall, the singer, the rest house, the Hip Waders")
vb = tmaps["VILLAGE_BRIDGE"]
stone = [c for o in vb["people"] for c in _opts(o) if isinstance(c, dict) and c.get("text") == "Gentleman Stonewall"]
check(stone and stone[0]["event"]["battle"]["team"] == json.load(open("dev/builders/town_maps/unova_teams.json"))["177"]["team"],
      "Gentleman Stonewall: his 1,000th battle, Black 2's team")
sing = vb["rooms"]["singer"]["people"]
check(any(isinstance(c, dict) and c.get("event", {}).get("flag") == "b2_vb_singer" for o in sing for c in _opts(o)),
      "the singer under the bridge (sets b2_vb_singer)")
girl = [c for o in vb["people"] for c in _opts(o) if isinstance(c, dict) and c.get("event", {}).get("flag") == "b2_vb_sitrus"]
check(girl and girl[0]["event"]["gift_item"] == {"SITRUS_BERRY": 5} and girl[0]["condition"] == ["b2_vb_singer"],
      "the girl who heard the voice: 5 Sitrus Berries once you've found the singer")
from src.world import unova_story
wad = [c for o in vb["rooms"]["waders"]["people"] for c in _opts(o) if isinstance(c, dict) and c.get("text") == "Hip Waders fisherman"][0]
said.clear()
st = walked("VILLAGE_BRIDGE", (14, 30))
d = wad["event"]["daily_catch"]
import datetime, random as _r
sp = _r.Random(d["key"] + "@" + datetime.date.today().isoformat()).choice(d["species"])
flags.pop(d["key"], None)
unova_story.event(st, wad["event"], [], lambda ls: said.extend(ls))
check("Catch of the Day" in heard(), "the Hip Waders: today's Catch of the Day")
_old = mk(sp); _old.caught_date = "2026-01-01"   # (11-25: Black 2 wants it caught today - the catch date, main 063d99274)
story.player_team.append(_old)
n0 = story.inventory.get("NET_BALL", 0)
said.clear(); unova_story.event(st, wad["event"], [], lambda ls: said.extend(ls))
check(story.inventory.get("NET_BALL", 0) == n0, f"the Hip Waders: one caught another day doesn't count ({heard()[:60]})")
story.player_team.remove(_old)
story.player_team.append(mk(sp))
said.clear(); unova_story.event(st, wad["event"], [], lambda ls: said.extend(ls))
check(story.inventory.get("NET_BALL", 0) == n0 + 3, f"the Hip Waders: show today's {sp} for the gift ({heard()[:80]})")

print("4) Route 11: Virizion")
r11 = tmaps["UNOVA_ROUTE_11"]
vir = [c for o in r11["people"] for c in _opts(o) if isinstance(c, dict) and c.get("action") == "BOSS"]
check(vir and vir[0]["boss"]["id"] == 640 and vir[0]["boss"]["level"] == 45, "Virizion: a Lv 45 boss on Route 11 (Jordan 11-24)")
check(any(sc.get("flag") == "b2_r11_virizion_seen" for sc in r11.get("scenes") or []), "Virizion leaps down from the cliff")

print("5) Opelucid: Iris, the Gym's dragon lift, Drayden")
for k in ("b2_opelucid_iris", "b2_legend_badge", "b2_drayden_lead", "b2_drayden_tale", "b2_opelucid_frozen"):
    flags.pop(k, None)
check("b2_m37" in mains(), f"the Journal: Drayden's Gym ({mains()})")
st = town("OPELUCID_CITY", (60, 47), face=(-1, 0))
go(-1, 0, 4, 60); settle(1200)
check(flags.get("b2_opelucid_iris") and "Iris" in heard(), "Iris meets you at the east gate")
gr = ope["rooms"]["gym"]
check(len(gr.get("links") or {}) == 6 and len(gr.get("barred") or []) == 3, "the Gym: the dragon heads' lift pads, three that wait on a Veteran")
st = town("OPELUCID_CITY", (15, 27), "gym", (0, -1))
for k in range(1, 6):
    flags.pop("gym_trainer_OPELUCID_CITY_%d" % k, None)
pad_up = (15, 26)
check(pad_up in getattr(st, "barred", {}), "the first head's pad stays dark till Lucius is beaten")
battle_talk("OPELUCID_CITY", (15, 27), "gym", "Veteran Lucius", 611, "gym_trainer_OPELUCID_CITY_1")
st = town("OPELUCID_CITY", (15, 27), "gym", (0, -1))
check(pad_up not in getattr(st, "barred", {}), "beaten: the pad lights up")
st.step(0, -1); settle(200)
check(tuple(st.player) == (15, 21), f"the head lifts you to the second level ({tuple(st.player)})")
battle_talk("OPELUCID_CITY", (10, 20), "gym", "Veteran Rhona", 611, "gym_trainer_OPELUCID_CITY_3")
battle_talk("OPELUCID_CITY", (4, 13), "gym", "Veteran Denae", 621, "gym_trainer_OPELUCID_CITY_5")
st = town("OPELUCID_CITY", (15, 27), "gym", (0, -1))   # (ride the heads up: each level's pad, as in play)
for _ in range(4):
    go(0, -1, 1, 60)
check(tuple(g.current_state.player) == (11, 13), f"up again: the third level ({tuple(g.current_state.player)})")
go(0, -1, 2, 60)
check(tuple(g.current_state.player) == (15, 6), f"the top: across to the far dragon's head ({tuple(g.current_state.player)})")

print("6) Drayden's house and the frozen city")
flags["b2_legend_badge"] = True
story.badges["UNOVA"].append("LEGEND")
check("b2_m38" in mains(), f"the Journal: A World of Ice ({mains()})")
flags["b2_drayden_lead"] = True
st = town("OPELUCID_CITY", (5, 11), "drayden", (0, -1)); settle(1500)
check(flags.get("b2_drayden_tale") and flags.get("b2_opelucid_frozen") and "Kyurem" in heard(),
      "Drayden's tale: the dragons, Kyurem, the DNA Splicers; then the boom")
check(WT.story_map(g, "OPELUCID_CITY") is ope["story_maps"][1]["map"] or WT.story_map(g, "OPELUCID_CITY")["art"] == ope["story_maps"][1]["map"]["art"],
      "outside, the city is frozen (Black 2's ice)")
st = town("OPELUCID_CITY", (34, 33)); settle(1500)
check(flags.get("b2_opelucid_ice") and "DNA Splicers" in heard(), "the ice won't break: Zinzolin demands the DNA Splicers")
fz = ope["story_maps"][1]["map"]
grunts = [c for o in fz["people"] for c in _opts(o) if isinstance(c, dict) and str(c.get("event", {}).get("flag", "")).startswith("b2_ope_grunt")]
check(len(grunts) == 3 and all(c.get("condition") == ["b2_opelucid_ice"] for c in grunts), "three Grunts to drive out")
for k in (1, 2, 3):
    flags["b2_ope_grunt_%d" % k] = True
zin = [c for o in fz["people"] for c in _opts(o) if isinstance(c, dict) and c.get("text") == "Zinzolin"]
check(zin and zin[0]["event"]["battle"]["team"] == [615, 615, 461], "Zinzolin at the Gym: Cryogonal, Cryogonal, Weavile")
flags["b2_opelucid_zinzolin"] = True
st = town("OPELUCID_CITY", (21, 18)); settle(1500)
check(flags.get("b2_splicers_stolen") and "Shadow Triad" in heard(), "the DNA Splicers shown, then stolen by the Shadow Triad")
st = town("OPELUCID_CITY", (59, 47), face=(1, 0))
ok = talk(st, "Shadow Triad")
cur = until(BATTLES, 800)
t = team_of(cur)
check(ok and 359 in [s for s, _ in t], f"the Shadow Triad by the Route 11 gate: Pawniard, Pawniard, Absol ({t})")
if type(cur).__name__ in BATTLES:
    win(cur)
check(flags.get("b2_opelucid_shadow"), "the Shadow Triad beaten")
settle(1500)   # (Cheren's call plays as soon as the battle's over: you're by the gate, in its zone)
check(flags.get("b2_opelucid_cheren") and "Humilau" in heard(), f"Cheren's call: Team Plasma is near Humilau ({where()})")
check("b2_m39" in mains(), f"the Journal: to Humilau ({mains()})")

print("7) White 2")
flags["unova_version"] = "WHITE_2"
flags["b2_opelucid_thawed"] = True
check(WT.story_map(g, "OPELUCID_CITY")["art"] == ope["story_maps"][2]["map"]["art"], "White 2: Opelucid's old-town look")
flags.pop("b2_opelucid_thawed", None)
check(WT.story_map(g, "OPELUCID_CITY")["art"] == ope["story_maps"][0]["map"]["art"], "White 2: frozen in its own look")
flags["unova_version"] = "BLACK_2"

print("8) extras: the Mimic game, the Medal Box painter, the HMs")
from src.world import unova_story as US, medals as MD, hms as HMS
_S = type("S", (), {"game": g})()
said.clear(); US.event(_S, {"mimic": "girl"}, [], lambda ls: said.extend(ls))
k = flags.get("b2_mimic_pick")
check(k is not None and "Who mimicked me" in heard(), "the Mimic girl calls out a Pokemon")
said.clear(); US.event(_S, {"mimic": k}, [], lambda ls: said.extend(ls))
check("Correct" in heard() and flags.get("b2_mimic_wins"), "...and the friend of its family is right")
story.inventory["MEDAL_BOX"] = 1
for m in MD.MEDALS[:len(MD.MEDALS) // 2]:
    flags["medal_" + m[0]] = True
said.clear(); US.event(_S, {"medal_paint": True}, [], lambda ls: said.extend(ls))
check(flags.get("b2_medal_box_paint") == "copper", f"the painter: half the Medals, a copper box ({flags.get('b2_medal_box_paint')})")
_pt = sum(1 for v in tmaps.values() if isinstance(v, dict) for r in (v.get("rooms") or {}).values()
          for o in r.get("people", []) if isinstance(o, dict) and o.get("text") == "Medal Box painter")
check(_pt >= 7, f"a Medal Box painter in every walked Center ({_pt})")
check(HMS.HM_BY_BADGE["UNOVA"] == {}, "Strength, Fly, Surf, Waterfall: story gifts only, no badge stand-ins (Waterfall from N, batch 10a)")

for f_ in fails:
    print("  -", f_)
print(f"##### {len(fails)} failures")
