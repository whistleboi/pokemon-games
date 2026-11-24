# Unova batch 8b (11-24): Route 9 (its gate to Tubeline Bridge, frozen with Opelucid), Shopping Mall Nine (five counters, the
# Waitress and Waiter, the Lady's Hyper Potion errand, the stockroom's appliances for Rotom), the Marine Tube (Undella's
# building, open after Cheren's call; the 3 pm Wailord; the Roxie fan's Black Sludge), Route 11's frozen look.
#   bash dev/checks/run.sh unovab8b
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
NEW = ("UNOVA_ROUTE_9", "MARINE_TUBE", "OPELUCID_CITY", "UNDELLA_TOWN")
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


def where():
    return story.current_area_key, tuple(getattr(getattr(g.current_state, "run", None), "player", None) or getattr(g.current_state, "player", (0, 0)))


def _opts(o):
    return o.get("any") if isinstance(o, dict) and "any" in o else o if isinstance(o, list) else [o]


def talk(st, label):
    spot = next((k for k, o in st.people.items() for c in _opts(o)
                 if isinstance(c, dict) and str(c.get("text", "")).rstrip() == label.rstrip() and st._shown(c)), None)
    if spot is None:
        return False
    said.clear(); st._talk(spot); settle(80)
    return True


BATTLES = ("TrainerIntroState", "TrainerBattleState", "DoubleBattleState", "GymBattleState", "BattleState")


def until(names, n=600):
    for _ in range(n):
        if type(g.current_state).__name__ in names:
            return g.current_state
        settle(1)
    return g.current_state


def team_of(b):
    b = getattr(b, "next_state", None) or b
    return [(int(getattr(p, "id", 0)), int(getattr(p, "level", 0))) for p in (getattr(b, "opponent_team", None) or [])]


def win(cur):
    from src.states.battle import TrainerIntroState
    b = cur
    for _ in range(3):
        if isinstance(b, TrainerIntroState) and getattr(b, "next_state", None) is not None:
            b = b.next_state; g.change_state(b); settle(1)
    b.player_won = True
    if hasattr(b, "exit_battle"):
        b.exit_battle()
    settle(400)


def battle_talk(area, at, room, label, want_id, flag, frozen=None):
    st = town(area, at, room)
    ok = talk(st, label)
    cur = until(BATTLES, 800)
    t = team_of(cur)
    check(ok and type(cur).__name__ in BATTLES and want_id in [s for s, _ in t], f"{label}: Black 2's team ({t})")
    if type(cur).__name__ in BATTLES:
        win(cur)
    if flag:
        check(flags.get(flag), f"{label} beaten ({flag})")


def mains():
    return [m["id"] for m in story.get_active_missions() if m["type"] == "MAIN"]


print("1) the places")
for a in NEW:
    check(a in tmaps, f"{a} is walked")
check(len(SP["UNOVA_ROUTE_9"]["trainer_pool"]) == 5 and SP["UNOVA_ROUTE_9"].get("wild_tables"), "Route 9: Black 2's 5 trainers, its wild Pokemon")
r9 = tmaps["UNOVA_ROUTE_9"]
check({"mall", "stockroom", "gate_w"} <= set(r9["rooms"]), "Route 9: Shopping Mall Nine, its stockroom, the Bridge Gate")
check(r9.get("story_maps") and tmaps["UNOVA_ROUTE_11"].get("story_maps"), "Routes 9 and 11 freeze with Opelucid")
check("tube" in tmaps["UNDELLA_TOWN"]["rooms"] and "gate_n" in tmaps["MARINE_TUBE"]["rooms"], "the Marine Tube's buildings at both ends")
check(not SP["UNOVA_ROUTE_9"].get("route_menu") and not SP["MARINE_TUBE"].get("route_menu"), "old menu buttons gone")

print("2) the road: Opelucid -> Route 9 -> the Mall")
ds = walked("UNOVA_ROUTE_9", (55, 15))
go(1, 0, 2, 120)
check(where()[0] == "OPELUCID_CITY", f"east from Route 9 into Opelucid ({where()})")
mall = r9["rooms"]["mall"]
shops = [c for o in mall["people"] for c in _opts(o) if isinstance(c, dict) and c.get("event", {}).get("stock")]
stock = {i for c in shops for i in c["event"]["stock"]}
check(len(shops) >= 5 and {"TM163", "TM152", "HP_UP", "X_SPEED", "MAX_POTION", "TIMER_BALL"} <= stock,
      f"the Mall's counters: Black 2's stock ({len(shops)} counters)")
from src.world import unova_story as US
_S = type("S", (), {"game": g})()
flags.pop("b2_mall_lady_day", None); flags.pop("b2_mall_lady_done", None)
m0 = story.money
said.clear(); US.event(_S, {"potion_errand": True}, [], lambda ls: said.extend(ls))
check(story.money == m0 + 1200, "the Lady: $1,200 for a Hyper Potion")
story.inventory["HYPER_POTION"] = story.inventory.get("HYPER_POTION", 0) + 1
said.clear(); US.event(_S, {"potion_errand": True}, [], lambda ls: said.extend(ls))
check(story.inventory.get("ENERGY_ROOT", 0) >= 1 and flags.get("b2_mall_lady_done"), "...brought the same day: an Energy Root")

print("3) the stockroom: Rotom's forms")
sr = r9["rooms"]["stockroom"]
forms_here = {e["event"]["rotom_form"] for e in (sr.get("sign_events") or {}).values()}
check(forms_here == {"heat", "wash", "frost", "fan", "mow", "normal"}, f"six appliance boxes ({sorted(forms_here)})")
story.player_team.append(mk(479))
said.clear(); US.event(_S, {"rotom_form": "wash", "lines": []}, [], lambda ls: said.extend(ls))
rot = story.player_team[-1]
check("HYDRO-PUMP" in [str(m).upper() for m in (rot.moves or [])] or "wash" in str(getattr(rot, "form", "")).lower(),
      f"the washing machine: Wash Rotom ({getattr(rot, 'form', None)}, {rot.moves})")

print("4) the Marine Tube")
for k in ("b2_opelucid_cheren",):
    flags.pop(k, None)
tube = tmaps["UNDELLA_TOWN"]["rooms"]["tube"]
check(any(b.get("until", {}).get("flag_condition") == "b2_opelucid_cheren" for b in tube.get("barred") or []),
      "closed for cleaning till Cheren's call from Opelucid")
flags["b2_opelucid_cheren"] = True
ds = walked("MARINE_TUBE", (15, 185))
go(0, 1, 6, 80)
check(where()[0] == "UNDELLA_TOWN", f"south out of the Tube into Undella ({where()})")
mt = tmaps["MARINE_TUBE"]
check(any("hour:15" in str(sc.get("condition")) for sc in mt.get("scenes") or []), "the Wailord swims by at 3 pm")
sl = [c for o in mt["people"] for c in _opts(o) if isinstance(c, dict) and c.get("event", {}).get("gift_item") == {"BLACK_SLUDGE": 1}]
check(sl and "holding:POISON_BARB" in str(sl[0]["condition"]), "the Roxie fan: a Black Sludge for a Poison Barb holder")

print("\n##### %d failures" % len(fails))
for f_ in fails:
    print("  -", f_)
