# Unova batch 6b (11-24): Mistralton City (Juniper's Master Ball and Skyla, the Gym's five Pilots and Skyla for the Jet
# Badge, the Center, the runway kids' TM40, the Cargo Service's flight to Lentimas, the TM fan's HP Ups), Route 7 (its
# trainers, the Gigalith trade, the farmer's legends, Mom's call, Hidden Grotto 5), Celestial Tower (1F to the roof:
# Juniper's Lucky Egg, the bell, the Black Fog), Twist Mountain's mouth (Marshal).
#   bash dev/checks/run.sh unovab6b
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
NEW = ("MISTRALTON_CITY", "UNOVA_ROUTE_7", "TWIST_MOUNTAIN_ENTRANCE", "CELESTIAL_TOWER", "CELESTIAL_TOWER_2F",
       "CELESTIAL_TOWER_3F", "CELESTIAL_TOWER_4F", "CELESTIAL_TOWER_ROOF")
for a in NEW + ("CHARGESTONE_CAVE",):
    flags["visited_" + a] = True
story.badges["UNOVA"] = ["BASIC", "TOXIC", "INSECT", "BOLT", "QUAKE"]
for k in ("b2_quake_badge", "b2_frigate_done", "b2_mom_talk", "b2_r6_surf"):
    flags[k] = True
said = []
tmaps = json.load(open("assets/town_maps.json", encoding="utf-8"))
prog = json.load(open("assets/unova_area_data.json", encoding="utf-8"))
SP = prog["STORY_PROGRESSION"]


def settle(n=60):
    for _ in range(n):
        st = g.current_state
        box = getattr(st, "npc_dialogue", None) if getattr(st, "npc_active", False) else getattr(st, "dialogue_box", None)
        if box is not None and getattr(box, "visible", True):
            for line in getattr(box, "text_lines", []) or []:
                if not said or said[-1] != line:
                    said.append(line)
        db = getattr(st, "dialogue_box", None)
        if db is not None and getattr(db, "visible", False):
            db.advance()
        elif getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        st.update(); st.draw()


def heard():
    return " ".join(said)


def town(area, at, room=None, face=(0, 1)):
    story.current_area_key = area
    g.walk_town_pos = (area, tuple(at), face)
    g.walk_town_room = (area, room) if room else None
    said.clear()
    g.change_state(CityState(g)); settle(30)
    return g.current_state


def walked(area, at, floor=0):
    story.current_area_key = area; g.walk_town_pos = g.walk_town_room = None
    g.arrive_floor = (area, floor, list(at))
    said.clear()
    g.change_state(PlayState(g)); settle(30)
    return g.current_state


def go(dx, dy, times=1, n=40):
    for _ in range(times):
        g.current_state.step(dx, dy)
        settle(n)
    return g.current_state


def _opts(o):
    return o.get("any") if isinstance(o, dict) and "any" in o else o if isinstance(o, list) else [o]


def talk(st, label):
    spot = next((k for k, o in st.people.items() for c in _opts(o)
                 if isinstance(c, dict) and str(c.get("text", "")).rstrip() == label.rstrip() and st._shown(c)), None)
    if spot is None:
        return False
    said.clear(); st._talk(spot); settle(80)
    return True


BATTLES = ("TrainerIntroState", "TrainerBattleState", "DoubleBattleState")


def until(names, n=600):
    for _ in range(n):
        if type(g.current_state).__name__ in names:
            return g.current_state
        settle(1)
    return g.current_state


def win(b):
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


def team_of(b):
    b = getattr(b, "next_state", None) or b
    return [(int(getattr(p, "id", 0)), int(getattr(p, "level", 0))) for p in (getattr(b, "opponent_team", None) or [])]


print("1) the places")
for a in NEW:
    check(a in tmaps, f"{a} is walked")
for a, n in (("UNOVA_ROUTE_7", 9), ("CELESTIAL_TOWER_2F", 2), ("CELESTIAL_TOWER_3F", 4), ("CELESTIAL_TOWER_4F", 3)):
    check(len(SP[a]["trainer_pool"]) == n, f"{a}: Black 2's {n} trainers")
for a in ("UNOVA_ROUTE_7", "CELESTIAL_TOWER_2F", "CELESTIAL_TOWER_3F", "CELESTIAL_TOWER_4F", "CELESTIAL_TOWER_ROOF"):
    check(bool(SP[a].get("wild_tables")), f"{a}: its own wild Pokemon")
check({"gym", "center", "house_kids", "cargo", "house_tm"} <= set(tmaps["MISTRALTON_CITY"]["rooms"]), "Mistralton's five buildings")
check(not any(o.get("condition") for o in SP["MISTRALTON_CITY"]["travel_options"]) and "explore_options" not in SP["MISTRALTON_CITY"],
      "no menu-era buttons; Route 7 open before the Gym, as in Black 2")

print("2) Chargestone -> Mistralton; Juniper's Master Ball and Skyla")
ds = walked("CHARGESTONE_CAVE", (73, 6))
go(0, -1, 1, 120)
check(story.current_area_key == "MISTRALTON_CITY", f"out of Chargestone Cave into Mistralton ({story.current_area_key})")
flags.pop("b2_mist_juniper", None); story.inventory.pop("MASTER_BALL", None)
st = town("MISTRALTON_CITY", (38, 46), face=(0, -1))
st.step(0, -1); settle(2500)
check(flags.get("b2_mist_juniper") and story.inventory.get("MASTER_BALL", 0) >= 1, "Juniper gives a Master Ball; Skyla turns up")
main = [m["id"] for m in story.get_active_missions() if m["type"] == "MAIN"]
check("b2_m32" in main, f"the Journal: the Jet Badge ({main})")

print("3) Skyla's Gym: five Pilots, Skyla (Black 2's team), the Jet Badge, TM62 Acrobatics")
gym = tmaps["MISTRALTON_CITY"]["rooms"]["gym"]
pilots = [c for o in gym["people"] for c in _opts(o) if isinstance(c, dict) and str(c.get("text", "")).startswith("Pilot")]
check(len(pilots) == 5 and all(c["event"]["flag"].startswith("gym_trainer_MISTRALTON_CITY_") for c in pilots), "five Pilots, each a Gym trainer")
check((gym.get("gusts") or {}).get("from") == "n" and gym["gusts"].get("to") == [11, 47], "the wind tunnel: the turbines blow you back to the door")
st = town("MISTRALTON_CITY", (2, 14), "gym", (0, -1))   # (out in the open: nothing upwind)
for _ in range(900):
    settle(1)
    if tuple(g.current_state.player) == (11, 47):
        break
check(tuple(g.current_state.player) == (11, 47), f"out in the open, a gust blows you back to the door ({g.current_state.player})")
st = town("MISTRALTON_CITY", (15, 14), "gym", (0, -1))   # (a wall straight upwind: sheltered)
settle(700)
check(tuple(g.current_state.player) == (15, 14), f"behind a wall, the wind can't reach you ({g.current_state.player})")
st = town("MISTRALTON_CITY", (11, 4), "gym", (0, -1))
for k in range(1, 6):
    flags["gym_trainer_MISTRALTON_CITY_%d" % k] = True
flags["gym_challenge_done_MISTRALTON_CITY"] = True   # (the Gym's game before the battle: won)
talk(st, "Gym")
cur = until(BATTLES, 400)
t = team_of(cur)
check(type(cur).__name__ in BATTLES and [s for s, _ in t] == [528, 227, 581] and [l for _, l in t] == [37, 37, 39],
      f"Skyla: Swoobat, Skarmory, Swanna at 37 / 37 / 39 ({t})")
if type(cur).__name__ in BATTLES:
    win(cur); settle(400)
check(flags.get("b2_jet_badge") and "JET" in (story.badges.get("UNOVA") or []) and story.inventory.get("TM014", 0) >= 1,
      "the Jet Badge and TM62 Acrobatics (our TM014)")

print("4) the runway kids' treasure; the TM fan; the Cargo worker")
st = town("MISTRALTON_CITY", (6, 6), "house_kids", (0, -1))
talk(st, "Runway kid")
check(flags.get("b2_runway_secret"), "the kids tell you about their treasure")
st = town("MISTRALTON_CITY", (5, 74), face=(0, -1))
talk(st, "The runway kids' treasure")
check(story.inventory.get("TM027", 0) >= 1, "TM40 Aerial Ace at the south end of the runway (our TM027)")
for i in range(1, 11):
    story.inventory["TM%03d" % (100 + i)] = 1
hp = story.inventory.get("HP_UP", 0)
st = town("MISTRALTON_CITY", (5, 7), "house_tm", (0, -1))
talk(st, "TM fan")
check(story.inventory.get("HP_UP", 0) > hp, f"the TM fan's HP Up for 10 TMs ({story.inventory.get('HP_UP', 0) - hp})")
st = town("MISTRALTON_CITY", (20, 22), "cargo", (0, -1))
talk(st, "Worker loading cargo")
check(story.inventory.get("NET_BALL", 0) == 0 or flags.get("b2_cargo_net_balls"), "the worker only helps a Flying- or Psychic-type's Trainer")

print("5) Route 7 and Celestial Tower: Juniper's Lucky Egg; the trainers; the bell; the Black Fog")
st = town("MISTRALTON_CITY", (53, 33), face=(0, -1))
st.step(0, -1); settle(120)
if story.current_area_key == "MISTRALTON_CITY":
    g.current_state.step(0, -1); settle(200)
check(story.current_area_key == "UNOVA_ROUTE_7", f"north from Mistralton onto Route 7 ({story.current_area_key})")
ds = walked("UNOVA_ROUTE_7", (11, 9))
go(0, -1, 1, 80)
check(story.current_area_key == "CELESTIAL_TOWER", f"into Celestial Tower ({story.current_area_key})")
pl = tuple(getattr(getattr(g.current_state, "run", None), "player", (0, 0)))
check(abs(pl[0] - 11) + abs(pl[1] - 22) <= 2, f"in at the tower's door ({pl})")
flags.pop("b2_lucky_egg", None)
ds = walked("CELESTIAL_TOWER", (12, 11))
st = g.current_state
spot = next((k for k, o in (getattr(st, "people", None) or {}).items() for c in _opts(o)
             if isinstance(c, dict) and str(c.get("text", "")).startswith("Professor Juniper") and st._shown(c)), None) \
    if hasattr(st, "people") else None
juniper = [c for o in tmaps["CELESTIAL_TOWER"]["people"] for c in _opts(o) if isinstance(c, dict) and c.get("text", "").startswith("Professor Juniper")]
check(any(c["event"].get("gift_item") == {"LUCKY_EGG": 1} and "b2_jet_badge" in c["condition"] for c in juniper),
      "Juniper's Lucky Egg on 1F (and back to the Cargo Service once you have the Jet Badge)")
for a, up in (("CELESTIAL_TOWER", "CELESTIAL_TOWER_2F"), ("CELESTIAL_TOWER_2F", "CELESTIAL_TOWER_3F"),
              ("CELESTIAL_TOWER_3F", "CELESTIAL_TOWER_4F"), ("CELESTIAL_TOWER_4F", "CELESTIAL_TOWER_ROOF")):
    check(tmaps[a]["exits"].get("^") == up and tmaps[up]["exits"].get("v") == a, f"{a} <-> {up}")
ds = walked("CELESTIAL_TOWER_2F", (13, 2))
go(0, -1, 1, 80)
check(story.current_area_key == "CELESTIAL_TOWER_3F", f"up the 2F ramp to 3F ({story.current_area_key})")
roof = tmaps["CELESTIAL_TOWER_ROOF"]
check("16,10" in (roof.get("sign_events") or {}), "the bell on the roof")
fog = next((o for o in SP["CELESTIAL_TOWER"].get("route_menu") or [] if (o.get("boss") or {}).get("id") == 10501), None)
check(fog and fog["boss"]["name"] == "Black Fog", "the Black Fog haunts the tower (its route_menu, as every haunt's: blackfog walks to it)")
nurse = next(t for t in SP["CELESTIAL_TOWER_3F"]["trainer_pool"] if "Dixie" in t["name"])
check(nurse, "Nurse Dixie on 3F")

print("6) Route 7's houses, Mom's call, Twist Mountain's mouth")
h = tmaps["UNOVA_ROUTE_7"]["rooms"]["house_w"]
tr = next(c for o in h["people"] for c in _opts(o) if isinstance(c, dict) and "Emolga" in c.get("text", ""))
check(tr["event"]["trade"] == {"want": 587, "give": 526, "item": "LEPPA_BERRY"}, "the Hiker's Gigalith (with a Leppa Berry) for your Emolga")
seen0 = set(g.data.data.get("seen_pokemon", []))
st = town("UNOVA_ROUTE_7", (4, 6), "house_e", (0, -1))
talk(st, "Old farmer")
check({641, 642, 645} <= set(int(x) for x in g.data.data.get("seen_pokemon", [])), "the farmer registers Tornadus, Thundurus, Landorus")
flags.pop("b2_r7_mom_call", None)
ds = walked("UNOVA_ROUTE_7", (39, 20))
go(1, 0, 1, 900)
check(flags.get("b2_r7_mom_call") and "Mom" in heard(), "Mom calls on the Xtransceiver east of the house")
ds = walked("UNOVA_ROUTE_7", (47, 1))
go(0, -1, 2)
check(story.current_area_key == "TWIST_MOUNTAIN_ENTRANCE", f"north to Twist Mountain ({story.current_area_key})")
flags.pop("b2_twist_marshal", None); flags.pop("beat_unova_champion", None)
ds = walked("TWIST_MOUNTAIN_ENTRANCE", (22, 13))
go(0, -1, 1, 900)
check(flags.get("b2_twist_marshal") and "Marshal" in heard(), "Marshal blocks the way: the inside collapsed")
check(tmaps["TWIST_MOUNTAIN_ENTRANCE"]["barred"][0]["until"]["flag_condition"] == "beat_unova_champion"
      and tmaps["TWIST_MOUNTAIN_ENTRANCE"]["gated_exits"] == {"TWIST_MOUNTAIN": ["beat_unova_champion"]},
      "the mountain stays shut till the Champion")

print("7) the flight to Lentimas")
flags["b2_lucky_egg"] = True; flags.pop("b2_lentimas_flight", None)
main = [m["id"] for m in story.get_active_missions() if m["type"] == "MAIN"]
check("b2_m33" in main, f"the Journal: Over the Mountain ({main})")
st = town("MISTRALTON_CITY", (24, 21), "cargo", (0, -1))
talk(st, "Skyla")
settle(300)
_sk = next(c for o in tmaps["MISTRALTON_CITY"]["rooms"]["cargo"]["people"] for c in _opts(o) if isinstance(c, dict) and c.get("text") == "Skyla ")
check(flags.get("b2_lentimas_flight") and story.current_area_key == "LENTIMAS_TOWN" and any("Bianca" in x for x in _sk["event"]["lines"]),
      f"Skyla flies you, Juniper and Bianca to Lentimas Town ({story.current_area_key})")

print("\n##### %d failures" % len(fails))
for f_ in fails:
    print("  -", f_)
