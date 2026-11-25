# Unova batch 5a (11-24): the Driftveil Drawbridge (bird shadows: Ducklett and feathers), Driftveil City (the arrival
# scene, Rood's test and Zorua, the hotels and their lifts, the Market, the Red Shard tutor), Clay's Gym (the conveyor belts
# between 36 platforms that light up as you land, the Workers, Clay), the World Tournament invitation, and Route 5's
# Musician Preston (his Electric Guitar Prop).
#   bash dev/checks/run.sh unova_b5a
import json
import os
from src.states.overworld import CityState


fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "nate"
flags = story.story_flags
flags["unova_version"] = "BLACK_2"; story.starting_region = "UNOVA"
for a in ("DRIFTVEIL_CITY", "DRIFTVEIL_DRAWBRIDGE", "UNOVA_ROUTE_5"):
    flags["visited_" + a] = True
said = []
tmaps = json.load(open("assets/town_maps.json", encoding="utf-8"))
prog = json.load(open("assets/unova_area_data.json", encoding="utf-8"))
SP = prog["STORY_PROGRESSION"]


exec(open("dev/checks/unova_lib.py", encoding="utf-8").read())   # (settle, heard, town, until, _opts, team_of: shared, Checks C5)


def people(st):
    out = {}
    for home, o in (getattr(st, "people", None) or {}).items():
        for c in _opts(o):
            if isinstance(c, dict) and st._shown(c):
                out[str(c.get("text", "")).rstrip()] = home
    return out


def talk(st, label):
    spot = next((k for k, o in st.people.items() for c in _opts(o)
                 if isinstance(c, dict) and str(c.get("text", "")).rstrip() == label and st._shown(c)), None)
    if spot is None:
        return False
    said.clear(); st._talk(spot); settle(40)
    return True


BATTLES = ("TrainerIntroState", "TrainerBattleState", "DoubleBattleState")


def win(b):
    """Stand in for a battle: past the opening words, won, back to the map."""
    from src.states.battle import TrainerIntroState
    for _ in range(3):
        if isinstance(b, TrainerIntroState) and getattr(b, "next_state", None) is not None:
            b = b.next_state
            g.change_state(b); settle(1)
    b.player_won = True
    if hasattr(b, "exit_battle"):
        b.exit_battle()
    for _ in range(400):
        if type(g.current_state).__name__ not in BATTLES + ("EvolutionState",):
            break
        settle(1)
    settle(60)


print("1) the maps: the drawbridge, Driftveil and its rooms")
dv = tmaps.get("DRIFTVEIL_CITY") or {}
rooms = set(dv.get("rooms") or {})
check({"center", "gym", "gym_lobby", "chateau", "chateau_25", "grand", "grand_19", "luxury", "luxury_23", "continental",
       "continental_25", "rood", "market", "pwt_gate"} <= rooms, f"Driftveil's rooms ({len(rooms)})")
check("DRIFTVEIL_DRAWBRIDGE" in tmaps, "the Driftveil Drawbridge is walked")
gym = SP["DRIFTVEIL_CITY"]["gym"]["leader"]
check(gym["team"] == [552, 28, 530] and gym["levels"] == [31, 31, 33] and gym["rewards"].get("TM028") == 1
      and gym["victory_flag"] == "b2_quake_badge" and gym["sprite"] == "b2_clay.png",
      "Clay: Black 2's team (Krokorok, Sandslash, Excadrill Lv 31-33), his own picture, TM78 Bulldoze (our TM028)")
check(os.path.isfile("assets/sprites/trainers/b2_clay.png") and os.path.isfile("assets/sprites/trainers/b2_veteran_f.png"),
      "Clay's battle picture (a/0/7/1 slot 99; the Veterans are 69 / 70 now)")

print("2) the bridge: west from Route 5, over the drawbridge, into Driftveil")
from src.states.overworld import PlayState
story.current_area_key = "UNOVA_ROUTE_5"; g.walk_town_pos = g.walk_town_room = None
g.arrive_floor = ("UNOVA_ROUTE_5", 0, [11, 16])
g.change_state(PlayState(g)); settle(20)
ds = g.current_state
for _ in range(4):
    if story.current_area_key != "UNOVA_ROUTE_5":
        break
    if hasattr(ds, "try_move"):
        ds.try_move(-1, 0)
    elif hasattr(ds, "step"):
        ds.step(-1, 0)
    settle(40); ds = g.current_state
check(story.current_area_key == "DRIFTVEIL_DRAWBRIDGE", f"Route 5's west edge leads onto the drawbridge ({story.current_area_key})")
from src.world import phenomena
if type(g.current_state).__name__ == "DungeonState":
    check(phenomena._kinds(g.current_state) == ["shadow"], f"the bridge's phenomenon: bird shadows ({phenomena._kinds(g.current_state)})")
else:
    check(False, "the bridge is walked on the route map")
check(SP["DRIFTVEIL_DRAWBRIDGE"].get("wild_tables", {}).get("ALL", {}).get("rustle", [[0]])[0][0] == 580,
      "under the shadows: Ducklett (the file's table)")

print("3) arriving: the Grunt, the ex-Plasma member, Hugh")
flags.pop("b2_drift_arrival", None)
st = town("DRIFTVEIL_CITY", (62, 48), face=(-1, 0))
st.step(-1, 0); settle(1000)
check(flags.get("b2_drift_arrival"), "off the bridge: the arrival scene plays")

print("4) Rood: a test battle, then inside with Hugh; Zorua")
st = town("DRIFTVEIL_CITY", (35, 14), face=(-1, 0))
st.step(-1, 0); settle(200)
cur = until(BATTLES, 400)
check(type(cur).__name__ in BATTLES and [t for t, _ in team_of(cur)] == [507, 528],
      f"Rood stops you outside: a battle (Herdier, Swoobat Lv 27) ({team_of(cur)})")
if type(cur).__name__ in BATTLES:
    win(cur)
check(flags.get("b2_rood_battled"), "Rood beaten")
st = town("DRIFTVEIL_CITY", (35, 14), face=(-1, 0))
st.step(-1, 0); settle(1200)
check(flags.get("b2_rood_talk"), "then his talk with Hugh about Purrloin")
st = town("DRIFTVEIL_CITY", (7, 18), "rood", (0, -1))
n0 = len([p for p in story.player_team if p])
talk(st, "Rood"); settle(80)
check(flags.get("b2_drift_zorua") and (len([p for p in story.player_team if p]) > n0 or any(
    int(getattr(p, "id", 0)) == 570 for p in getattr(story, "pc_boxes_flat", lambda: [])() or [])), "Rood's Zorua joins you")
check("Zorua" not in people(town("DRIFTVEIL_CITY", (7, 18), "rood", (0, -1))), "and no longer waits in the base")

print("5) Clay's Gym: the lift, the belts, the lights, the Workers, Clay")
story.badges["UNOVA"] = ["BASIC", "TOXIC", "INSECT", "BOLT"]
st = town("DRIFTVEIL_CITY", (52, 18), face=(0, -1))
check("Worker by the Gym" not in people(st), "after Rood's talk the Gym's door is clear")
st = town("DRIFTVEIL_CITY", (7, 10), "gym_lobby", (0, -1))
check("8,3" in (st.town_map["rooms"]["gym_lobby"].get("sign_events") or {}), "the entrance's lift goes down to the Gym")
check((8, 3) in st.signs and (11, 85) in [tuple(int(v) for v in k.split(",")) for k in st.town_map["rooms"]["gym"].get("sign_events") or {}]
      and st.town_map["rooms"]["gym"]["art"][85][11] == "!",
      "both lift panels are sign tiles, so facing one and pressing the action key reads it (Journal PT_FULL, 11-24)")
import pygame
from src.states.systems.pick_list import PickListState
st = town("DRIFTVEIL_CITY", (8, 4), "gym_lobby", (0, -1))   # (face the panel and press the action key, as a player does)
st.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, unicode=" ", mod=0)])
settle(200)
pl = g.current_state
check(isinstance(pl, PickListState), f"pressing the action key at the lobby's lift asks which floor ({type(pl).__name__})")
if isinstance(pl, PickListState):
    pl.pick(next(v for _l, v in pl.choices if v[1] == "gym"))
settle(300)
check(getattr(g.current_state, "room", None) == "gym" and tuple(getattr(g.current_state, "player", ())) == (10, 86),
      f"down in the Gym, by the lift ({getattr(g.current_state, 'room', None)}, {getattr(g.current_state, 'player', None)})")
for k in list(flags):
    if k.startswith("b2_dgym_lit_"):
        flags.pop(k)
st = town("DRIFTVEIL_CITY", (5, 60), "gym", (0, -1))
st.step(0, -1); settle(200)
cur = g.current_state
check(tuple(getattr(cur, "player", (0, 0))) == (5, 51) and flags.get("b2_dgym_lit_0_4"),
      f"up off the first platform: a belt carries you to the next one, which lights up ({getattr(cur, 'player', None)})")
lit = cur._lit_sections() if hasattr(cur, "_lit_sections") else []
check((1, 47, 9, 53) in lit and (11, 47, 19, 53) not in lit, "only the platforms you've landed on are lit")
st = town("DRIFTVEIL_CITY", (25, 60), "gym", (0, -1))
st.step(0, -1); settle(500)
check(tuple(getattr(g.current_state, "player", (0, 0))) == (25, 40), f"({getattr(g.current_state, 'player', None)}) a pink belt runs under the next platform to the one beyond")
_rides = [x for x in tmaps["DRIFTVEIL_CITY"]["rooms"]["gym"].get("scenes") or [] if x.get("mark", "").startswith("b2_dgym_lit_")]
check(len(_rides) == 82, f"41 belts, as Bulbapedia's map of the Gym shows ({len(_rides) // 2})")
st = town("DRIFTVEIL_CITY", (25, 7), "gym", (0, -1))
ps = people(st)
check(sum(1 for k in ps if k.startswith("Worker ")) == 7, f"seven Workers in the Gym ({sorted(k for k in ps if k.startswith('Worker'))})")
talk(st, "Worker Pasqual")
cur = until(BATTLES, 300)
check([l for _, l in team_of(cur)] == [30, 30], f"Worker Pasqual: Black 2's team (Drilbur, Baltoy Lv 30) ({team_of(cur)})")
if type(cur).__name__ in BATTLES:
    win(cur)
flags["gym_challenge_done_DRIFTVEIL_CITY"] = True   # (his game before the battle: won; the minigame suites play those)
st = town("DRIFTVEIL_CITY", (45, 17), "gym", (0, -1))
talk(st, "Gym")
cur = until(BATTLES, 300)
check(type(cur).__name__ in BATTLES and [t for t, _ in team_of(cur)] == [552, 28, 530], f"Clay battles ({team_of(cur)}; {type(cur).__name__}; {heard()[:200]})")
if type(cur).__name__ in BATTLES:
    win(cur)
settle(200)
check(flags.get("b2_quake_badge") and "QUAKE" in (story.badges.get("UNOVA") or []), "the Quake Badge")
check(story.inventory.get("TM028", 0) >= 1, "and TM78 Bulldoze")
st = town("DRIFTVEIL_CITY", (52, 20), face=(0, -1)); settle(1200)
check(flags.get("b2_drift_clay_out"), "outside, Clay and Hugh: the World Tournament invitation")

print("6) the hotels, their lifts and gifts; the tutor; the move lady")
st = town("DRIFTVEIL_CITY", (7, 4), "grand", (0, -1))
lift = (st.town_map["rooms"]["grand"].get("sign_events") or {})
check(any(e["event"].get("lift") for e in lift.values()), "Grand Hotel's lift (1F, 2F, 19F)")
st = town("DRIFTVEIL_CITY", (6, 10), "grand_19", (0, -1))
talk(st, "Axew")
check(story.inventory.get("HABAN_BERRY", 0) >= 1, "Axew's Haban Berry on 19F")
st = town("DRIFTVEIL_CITY", (7, 11), "continental_25", (0, -1))
talk(st, "Veteran on 25F")
check(story.inventory.get("BIG_ROOT", 0) >= 1, "the Veteran's Big Root on the Continental's 25F")
st = town("DRIFTVEIL_CITY", (7, 9), "luxury_23", (0, -1))
talk(st, "Waiter on 23F")
check(story.inventory.get("EVERSTONE", 0) >= 1, "the Waiter's Everstone on the Luxury Suites' 23F")
st = town("DRIFTVEIL_CITY", (6, 10), "chateau_25", (0, -1))   # (his Air Balloon: a real held item since main a91de160)
talk(st, "Gentleman on 25F")
check(story.inventory.get("AIR_BALLOON", 0) >= 1, "the Gentleman's Air Balloon on the Chateau's 25F")
st = town("DRIFTVEIL_CITY", (6, 10), "chateau", (0, -1))
check("Move Tutor" in people(st), "the Red Shard tutor in the Chateau Hotel")
tu = next(c for o in st.people.values() for c in _opts(o) if isinstance(c, dict) and c.get("text") == "Move Tutor")["event"]["tutor"]
check(len(tu["choices"]) == 15 and tu["costs"]["ICE-PUNCH"] == {"RED_SHARD": 10} and tu["costs"]["COVET"] == {"RED_SHARD": 2},
      "his 15 moves for 2-10 Red Shards (Black 2's)")
story.inventory["TM028"] = 1
from src.world import unova_story as US
mv = US._today_move(story, g)
check(mv is not None, f"the Luxury Suites lady asks for one of your TM moves today ({mv})")

print("7) the Market: herbs, milk, incense; the Expert Belt; TM63")
st = town("DRIFTVEIL_CITY", (8, 16), "market", (0, -1))
ps = people(st)
check({"Herb seller", "Milk seller", "Incense seller", "Man in sunglasses"} <= set(ps), "the Market's sellers")
herb = next(c for o in st.people.values() for c in _opts(o) if isinstance(c, dict) and c.get("text") == "Herb seller")
check(herb["event"]["stock"] == ["HEAL_POWDER", "ENERGY_POWDER", "ENERGY_ROOT", "REVIVAL_HERB"], "herbal medicine, as Black 2")
check(any(k.startswith("Poke Ball") for k in people(town("DRIFTVEIL_CITY", (1, 9), "market", (1, 0)))),
      "TM63 Embargo in the corner reached by the west door")

print("8) Route 5's Musician Preston and his Electric Guitar")
from src.world import musical as M
flags.pop("b2_prop_case", None); flags.pop("b2_preston", None); flags.pop("b2_preston_guitar", None)
st = town("UNOVA_ROUTE_5", (12, 15), face=(0, -1))
ev = next(c for o in (tmaps["UNOVA_ROUTE_5"].get("people") or []) for c in _opts(o) if isinstance(c, dict) and c.get("text") == "Musician Preston")
check(ev["event"]["stages"][1]["battle"]["team"] == [556], "Preston: Black 2's Maractus (trainer 256), on Route 5 at last")
flags["b2_prop_case"] = True; flags["b2_preston"] = True
from src.states.overworld.common import _run_story_event
out = []
_run_story_event(g.current_state, ev["event"], lambda c: (c != "not:b2_prop_case") if c.startswith("not:") else bool(flags.get(c)), out.extend)
check(84 in M.props(g), "after his battle, the Electric Guitar Prop")

print("9) the Journal")
missions = {m["id"]: m for m in prog["JOURNAL_MISSIONS"]}
check(all(k in missions for k in ("b2_m26", "b2_m27", "b2_m28")) and missions["b2_m27"]["completed_badge"] == "QUAKE",
      "the Journal follows Driftveil's story (Team Plasma, the mine, the World Tournament)")
blob = json.dumps(json.load(open("assets/music/unova/music.json", encoding="utf-8")))
check("DRIFTVEIL_CITY" in blob and "DRIFTVEIL_DRAWBRIDGE" in blob, "Driftveil's and the bridge's own music")

for f in fails:
    print("  -", f)
print(f"##### {len(fails)} failures")
