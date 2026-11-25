# Unova batch 9b-2 (11-24): the Giant Chasm (the outer cave's spy, the crater forest: Rood and the double battle with Hugh,
# the inner cave), the frigate docked in the crater (the stern, Kyurem's room: Black 2's switches / White 2's password,
# Zinzolin; Colress and the Master Ball; Ghetsis's room: the Shadow Triad, Liepard), and the deepest cave (Ghetsis, N, the
# fused Kyurem, Ghetsis's battle, Opelucid's thaw).
#   bash dev/checks/run.sh unova_b9c
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
check(kw["barred"][0]["until"]["condition"] == ["b2_fk_1", "b2_fk_2", "b2_fk_3", "b2_fk_4"]
      and len([s for s in kw["scenes"] if str(s.get("flag", "")).startswith("b2_fk_")]) == 4,
      "White 2: four switches, each dropping a row of the barrier (11-25: the versions' puzzles were the wrong way round)")
check(kb["barred"][0]["until"]["condition"] == ["b2_fk_password"]
      and len([c for c in opts(kb) if str((c.get("event") or {}).get("flag", "")).startswith("b2_fk_clue_")]) == 5
      and any((c.get("event") or {}).get("flag") == "b2_fk_card" and c["event"]["battle"]["team"][:2] for c in opts(kb)),
      "Black 2: the Plasma Card (the Grunt with Trubbish and Zangoose) and five clues")


def _reach(rm, start):   # (walking plus the room's warp panels: "links" to tiles in the same room)
    a = rm["art"]
    links = {tuple(map(int, k.split(","))): tuple(v[1:]) for k, v in (rm.get("links") or {}).items() if v[0] == "kyurem"}
    seen, todo = {start}, [start]
    while todo:
        x, y = todo.pop()
        nxt = [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))] + ([links[(x, y)]] if (x, y) in links else [])
        for t in nxt:
            if t not in seen and 0 <= t[1] < len(a) and 0 <= t[0] < len(a[0]) and a[t[1]][t[0]] not in "c" \
                    and not any(list(t) in b["tiles"] for b in rm.get("barred") or []):
                seen.add(t)
                if a[t[1]][t[0]] != "N":
                    todo.append(t)
    return seen


_rw = _reach(kw, (15, 21))
check(all(xy in _rw for xy in ((9, 16), (9, 21), (21, 16), (21, 21))),
      "White 2: every switch reachable from the stern's panel, by the warp panels (the Journal's PT_FULL found Black 2's sealed)")
_rb = _reach(kb, (15, 21))
_npos = [(x, y) for y, r in enumerate(kb["art"]) for x, c in enumerate(r) if c == "N"]
check(sum(1 for p in _npos if p in _rb) >= 8, f"Black 2: the password Grunts can be walked to ({sum(1 for p in _npos if p in _rb)})")
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
for k in ("b2_fk_1", "b2_fk_2", "b2_fk_3", "b2_fk_4", "b2_fk_password"):
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

print("6) after the title: Juniper's two starters (Jordan 11-24)")
flags["beat_unova_champion"] = True; flags["starter_unova"] = 495; flags["visited_ASPERTIA_CITY"] = True; flags["move_offer_unova"] = True
flags.pop("b2_juniper_starters", None)
story.player_team = story.player_team[:3]
n0 = len(story.player_team)
st = town("ASPERTIA_CITY", (6, 6), "home")
talk(st, "Professor Juniper")
got = [int(p.id) for p in story.player_team[n0:]]
check(flags.get("b2_juniper_starters"), "Juniper gives both at once")
check(sorted(got) == [498, 501], f"Snivy's Trainer gets Tepig and Oshawott ({got})")

for f_ in fails:
    print("  -", f_)
print(f"##### {len(fails)} failures")
