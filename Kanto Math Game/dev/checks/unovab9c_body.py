# Unova batch 9b-2 (11-24): the Giant Chasm (the outer cave's spy, the crater forest: Rood and the double battle with Hugh,
# the inner cave), the frigate docked in the crater (the stern, Kyurem's room: Black 2's switches / White 2's password,
# Zinzolin; Colress and the Master Ball; Ghetsis's room: the Shadow Triad, Liepard), and the deepest cave (Ghetsis, N, the
# fused Kyurem, Ghetsis's battle, Opelucid's thaw).
#   bash dev/checks/run.sh unovab9c
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
NEW = ("UNOVA_ROUTE_22", "GIANT_CHASM", "GIANT_CHASM_FOREST", "GIANT_CHASM_CAVE", "PLASMA_FRIGATE")
for a in NEW:
    flags["visited_" + a] = True
story.badges["UNOVA"] = ["BASIC", "TOXIC", "INSECT", "BOLT", "QUAKE", "JET", "LEGEND", "WAVE"]
for k in ("b2_mom_talk", "b2_jet_badge", "b2_lucky_egg", "b2_lentimas_flight", "b2_lentimas_juniper", "visited_UNDELLA_TOWN",
          "b2_lacunosa_juniper", "b2_lacunosa_tale", "b2_lacunosa_zinzolin", "b2_legend_badge", "b2_opelucid_cheren",
          "visited_OPELUCID_CITY", "visited_HUMILAU_CITY", "b2_wave_badge", "b2_humilau_after",
          "b2_colress_mchn", "b2_seaside_crustle", "b2_frigate_done", "b2_frigate2_open", "b2_frigate2_done",
          "b2_r21_cheren", "b2_opelucid_frozen"):
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


print("1) the maps")
ch = tmaps["GIANT_CHASM"]
check(set(ch["exits"].values()) >= {"UNOVA_ROUTE_22", "UNOVA_ROUTE_23", "GIANT_CHASM_FOREST", "UNOVA_ROUTE_13"},
      "the outer cave: Routes 22, 13, 23 and the crater forest")
check(ch["gated_exits"].get("UNOVA_ROUTE_23") == ["b2_chasm_done"], "Route 23 waits on the end of Team Plasma")
check(not tmaps["UNOVA_ROUTE_22"].get("gated_exits", {}).get("GIANT_CHASM"), "Route 22's door to the Chasm is open now")
check(sum(r.count("b") for r in ch["art"]) == 4, "the outer cave's four Strength boulders")
fo = tmaps["GIANT_CHASM_FOREST"]
check("grotto" in fo["rooms"] and fo["inside"].get("28,57") == "grotto", "the forest's Hidden Grotto (by the file's 10804)")
dock = fo["story_maps"][0]
check(dock["when"] == ["b2_frigate2_done", "not:b2_chasm_done"] and "PLASMA_FRIGATE" in dock["map"]["exits"].values(),
      "while the frigate's docked, the forest has its gangway")
rb = dock["map"]["scenes"][0]["event"]["battle"]
check(rb["battle_options"]["double"] and rb["battle_options"]["partner"]["name"] == "{rival_name}" and rb["team"] == [510, 505, 545]
      and rb["battle_options"]["second_trainer"]["team"] == [559, 510], f"Rood's clearing: you and Hugh against two Grunts ({rb['team']})")
fr = tmaps["PLASMA_FRIGATE"]
sm3 = [sm for sm in fr["story_maps"] if "b2_frigate2_done" in sm["when"]]
check(len(sm3) == 2, "the docked frigate: each version's own")
f3b = next(sm["map"] for sm in sm3 if "unova_version:WHITE_2" not in sm["when"])
f3w = next(sm["map"] for sm in sm3 if "unova_version:WHITE_2" in sm["when"])
check(set(f3b["rooms"]) == {"stern", "kyurem", "control", "ghetsis"}, "the stern, Kyurem's room, the Control Room, Ghetsis's room")
kb, kw = f3b["rooms"]["kyurem"], f3w["rooms"]["kyurem"]
check(kb["barred"][0]["until"]["condition"] == ["b2_fk_1", "b2_fk_2", "b2_fk_3", "b2_fk_4"]
      and len([s for s in kb["scenes"] if str(s.get("flag", "")).startswith("b2_fk_")]) == 4, "Black 2: four red switches")
check(kw["barred"][0]["until"]["condition"] == ["b2_fk_password"]
      and len([c for c in opts(kw) if str((c.get("event") or {}).get("flag", "")).startswith("b2_fk_clue_")]) == 5
      and any((c.get("event") or {}).get("flag") == "b2_fk_card" for c in opts(kw)), "White 2: the Plasma Card and five clues")
tb = [c for c in opts(kb) if (c.get("event") or {}).get("battle")]
check(len(tb) == 11, f"Black 2's Kyurem room: its eleven trainers ({len(tb)})")
col = next(c for c in opts(f3b["rooms"]["control"]) if c["text"] == "Colress")
check(col["event"]["battle"]["team"][-1] == 601 and col["event"]["battle"]["rewards"].get("MASTER_BALL") == 1,
      "Colress: Klinklang, then the Master Ball")
gh = f3b["rooms"]["ghetsis"]
check(len([c for c in opts(gh) if c["text"].startswith("Shadow Triad")]) == 3 and "GIANT_CHASM_FOREST" in gh["exits"].values()
      and gh.get("edge_to", {}).get("11,16") == [49, 64], "Ghetsis's room: the Shadow Triad, and the hatch out to the forest")
cv = tmaps["GIANT_CHASM_CAVE"]
dp = cv["rooms"]["deep"]
ky = [c for c in opts(dp) if c.get("action") == "BOSS"]
check(len(ky) == 3 and {c["boss"]["name"] for c in ky} == {"Black Kyurem", "White Kyurem", "Kyurem"}
      and all(c["boss"].get("no_catch") for c in ky if c["boss"]["name"] != "Kyurem")
      and {c["boss"].get("form") for c in ky} == {"black", "white", None},
      "the deepest cave: Black / White Kyurem (no catching), and Kyurem after the League")
gb = next(c for c in opts(dp) if c["text"] == "Ghetsis")["event"]["battle"]
check(gb["team"][-1] == 635 and gb["levels"][-1] == 52, "Ghetsis: Hydreigon Lv 52 last")
check(dp["scenes"][1]["flag"] == "b2_chasm_done" and dp["scenes"][1]["event"]["flag"] == "b2_opelucid_thawed",
      "the end: Team Plasma's finished, Opelucid thaws")
check("GIANT_CHASM_FOREST" in SP and "GIANT_CHASM_CAVE" in SP and SP["GIANT_CHASM"]["route_menu"] == []
      and "area_boss" not in SP["GIANT_CHASM"], "the Chasm's places: walked, Kyurem in the deepest room")

print("2) the outer cave: Rood's spy")
ds = walked("GIANT_CHASM", (61, 34))
go(0, 1, 2, 60); settle(1500)
check(flags.get("b2_chasm_spy") and "spy" in heard(), "the spy sends the Grunts back to the ship")

print("3) the forest: Rood, and the double battle")
check(WT.story_map(g, "GIANT_CHASM_FOREST") is not WT.custom(g).get("GIANT_CHASM_FOREST"), "the frigate is docked in the crater")
ds = walked("GIANT_CHASM_FOREST", (26, 73))
before = story.inventory.get("MAX_REVIVE", 0)
go(0, -1, 2, 60)
cur = until(BATTLES, 1500)
check(type(cur).__name__ in BATTLES, f"Rood's clearing: a battle ({type(cur).__name__})")
if type(cur).__name__ in BATTLES:
    win(cur)
settle(800)
check(flags.get("b2_chasm_rood") and story.inventory.get("MAX_REVIVE", 0) == before + 3, "Rood's three Max Revives")

print("4) aboard: Zinzolin, Colress")
for k in ("b2_fk_1", "b2_fk_2", "b2_fk_3", "b2_fk_4"):
    flags[k] = True
ds = walked("PLASMA_FRIGATE", (15, 20), floor=2)
go(0, -1, 2, 60)
cur = until(BATTLES, 1500)
check(type(cur).__name__ in BATTLES and 615 in [s for s, _ in team_of(cur)], f"Zinzolin's Cryogonal ({team_of(cur)})")
if type(cur).__name__ in BATTLES:
    win(cur)
check(flags.get("b2_f3_zinzolin"), "Zinzolin beaten")
ds = walked("PLASMA_FRIGATE", (7, 6), floor=3)
ok = use(ds, "Colress")
cur = until(BATTLES, 800)
check(ok and type(cur).__name__ in BATTLES, "Colress battles you")
if type(cur).__name__ in BATTLES:
    win(cur)
settle(400)
check(flags.get("b2_colress_beaten") and story.inventory.get("MASTER_BALL", 0) >= 1, "Colress gives you the Master Ball")

print("5) the deepest cave: the end")
for k in ("b2_f3_ghetsis", "b2_shadow_1", "b2_shadow_2", "b2_shadow_3", "b2_liepard_back"):
    flags[k] = True
ds = walked("GIANT_CHASM_CAVE", (13, 24), floor=1)
go(0, -1, 2, 60); settle(1500)
check(flags.get("b2_chasm_ghetsis") and "Absofusion" in heard(), "Ghetsis fuses Kyurem with the legend")
flags["b2_kyurem_fused"] = True; flags["b2_ghetsis_beaten"] = True
ds = walked("GIANT_CHASM_CAVE", (13, 24), floor=1)
go(0, -1, 1, 60); settle(1500)
check(flags.get("b2_chasm_done") and flags.get("b2_opelucid_thawed"), "Team Plasma's finished; Opelucid thaws")
check(WT.story_map(g, "OPELUCID_CITY") is WT.custom(g).get("OPELUCID_CITY"), "Opelucid is its own again")
story.current_area_key = "GIANT_CHASM"
check("b2_m45" in mains() and "b2_m44" not in mains(), f"the Journal: on to Victory Road ({mains()})")

print("\n##### %d failures" % len(fails))
for f_ in fails:
    print("  -", f_)
