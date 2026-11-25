# Unova batch 11a (11-24): the post-game east - Route 14 and its Black Gate, the Abundant Shrine (Landorus, the Reveal
# Glass, its grottoes), Route 15 (the Transfer Lab, the trailer's Rotom trade, its Black Gate), Marvelous Bridge (Cresselia),
# and Undella after the title: Hugh's HM06 Dive and battle, Cynthia.
#   bash dev/checks/run.sh unova_b11a
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
NEW = ("UNOVA_ROUTE_14", "ABUNDANT_SHRINE", "UNOVA_ROUTE_15", "MARVELOUS_BRIDGE", "UNDELLA_TOWN")
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





print("1) the maps")
r14, r15, br, sh = tmaps["UNOVA_ROUTE_14"], tmaps["UNOVA_ROUTE_15"], tmaps["MARVELOUS_BRIDGE"], tmaps["ABUNDANT_SHRINE"]
check(set(r14["exits"].values()) >= {"UNDELLA_TOWN", "ABUNDANT_SHRINE"} and len(r14["trainer_spots"]) == 8, "Route 14: Undella, the Abundant Shrine, its eight trainers")
check("BLACK_CITY" in r14["rooms"]["gate"]["exits"].values()
      and "WHITE_FOREST" in r14["story_maps"][0]["map"]["rooms"]["gate"]["exits"].values(),
      "Route 14's Black Gate: Black City in Black 2, White Forest in White 2")
check({"lab", "trailer", "gate"} <= set(r15["rooms"]) and "MARVELOUS_BRIDGE" in r15["exits"].values()
      and "WHITE_FOREST" in r15["rooms"]["gate"]["exits"].values() and "BLACK_CITY" in r15["story_maps"][0]["map"]["rooms"]["gate"]["exits"].values(),
      "Route 15: the Transfer Lab, the trailer, its Black Gate, the way to Marvelous Bridge")
tr = next(c for c in opts(r15["rooms"]["trailer"]) if (c.get("event") or {}).get("trade"))
check(tr["event"]["trade"]["want"] == 132 and tr["event"]["trade"]["give"] == 479, "the trailer: her Rotom for a Ditto")
check("UNOVA_ROUTE_16" in br["exits"].values() and "UNOVA_ROUTE_15" in br["rooms"]["gate_e"]["exits"].values(),
      "Marvelous Bridge: Route 16 to the west, its Bridge Gate to Route 15")
cr = [c for c in opts(br) if c.get("action") == "BOSS"]
check(cr and cr[0]["boss"]["id"] == 488 and br["scenes"][0]["condition"][0] == "has_item:LUNAR_WING", "Cresselia, with the Lunar Wing")
lan = [c for c in opts(sh) if c.get("action") == "BOSS"]
check(lan and lan[0]["boss"]["id"] == 645 and {"grotto", "grotto2", "house"} <= set(sh["rooms"]),
      "the Abundant Shrine: Landorus after the title, its two Hidden Grottoes, the house")
check(not SP["ABUNDANT_SHRINE"]["route_menu"] and "area_boss" not in SP["ABUNDANT_SHRINE"], "the old menus gone")

print("2) Undella after the title: Hugh, Dive")
flags["beat_unova_champion"] = True; flags["b2_hall_of_fame"] = True; flags["move_offer_unova"] = True
flags["visited_UNDELLA_TOWN"] = True
for k in ("b2_undella_hugh", "b2_undella_hugh_met", "b2_cynthia_beaten"):
    flags.pop(k, None)
story.inventory.pop("HM_DIVE", None)
st = town("UNDELLA_TOWN", (30, 20))
cur = until(BATTLES, 1500)
t = team_of(cur)
check(type(cur).__name__ in BATTLES and any(lv == 62 for _s, lv in t), f"Hugh battles you by the gate, Lv 62 ({t})")
if type(cur).__name__ in BATTLES:
    win(cur)
settle(400)
check(flags.get("b2_undella_hugh") and story.inventory.get("HM_DIVE"), "Hugh gives HM06 Dive")

print("3) Cynthia")
st = town("UNDELLA_TOWN", (6, 6), "villa")
ok = talk(st, "Cynthia ")
cur = until(BATTLES, 800)
t = team_of(cur)
check(ok and type(cur).__name__ in BATTLES and [s for s, _l in t] == _TEAMS["456"]["team"], f"Cynthia battles you ({t})")
if type(cur).__name__ in BATTLES:
    win(cur)
check(flags.get("b2_cynthia_beaten"), "Cynthia beaten")

for f_ in fails:
    print("  -", f_)
print(f"##### {len(fails)} failures")
