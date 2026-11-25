# Unova batch 10a (11-24): Route 23 (its houses, the boulders, the fake items), Victory Road's entrance (N's HM05 Waterfall,
# the Badge Check Gate, the Center) and its caves in both versions' people, doors paired as Black 2's warps, Hugh in the
# tunnel (TM126 Thunderbolt).
#   bash dev/checks/run.sh unova_b10a
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
NEW = ("UNOVA_ROUTE_23", "VICTORY_ROAD_UNOVA", "VICTORY_ROAD_TUNNEL", "GIANT_CHASM")
for a in NEW:
    flags["visited_" + a] = True
story.badges["UNOVA"] = ["BASIC", "TOXIC", "INSECT", "BOLT", "QUAKE", "JET", "LEGEND", "WAVE"]
for k in ("b2_mom_talk", "b2_jet_badge", "b2_lucky_egg", "b2_lentimas_flight", "b2_lentimas_juniper", "visited_UNDELLA_TOWN",
          "b2_lacunosa_juniper", "b2_lacunosa_tale", "b2_lacunosa_zinzolin", "b2_legend_badge", "b2_opelucid_cheren",
          "visited_OPELUCID_CITY", "visited_HUMILAU_CITY", "b2_wave_badge", "b2_humilau_after",
          "b2_colress_mchn", "b2_seaside_crustle", "b2_frigate_done", "b2_frigate2_open", "b2_frigate2_done",
          "b2_r21_cheren", "b2_opelucid_frozen", "b2_chasm_done", "b2_opelucid_thawed", "b2_kyurem_fused",
          "b2_ghetsis_beaten"):
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
r23 = tmaps["UNOVA_ROUTE_23"]
check(set(r23["exits"].values()) >= {"VICTORY_ROAD_UNOVA", "GIANT_CHASM"}, "Route 23: from the Giant Chasm to Victory Road")
check(len(r23["trainer_spots"]) == 12 and sum(r.count("b") for r in r23["art"]) == 6, "Route 23: twelve trainers, the six boulders")
check({"healer", "old_man", "grotto"} <= set(r23["rooms"]), "Route 23: the healer's house, the old man's, the Hidden Grotto")
fakes = [c for c in opts(r23) if c.get("action") == "BOSS"]
check(len(fakes) == 3 and all(c["boss"]["id"] == 591 and c["boss"]["level"] == 56 for c in fakes), "three fake items: Amoonguss Lv 56")
vro = tmaps["VICTORY_ROAD_UNOVA"]
check(vro["exits"].get("^") == "VICTORY_ROAD_CAVE_1F" and "center" in vro["rooms"], "Victory Road's entrance: the caves and the Center")
check(not SP["VICTORY_ROAD_UNOVA"]["route_menu"] and "area_boss" not in SP["VICTORY_ROAD_UNOVA"], "the old menu (BW's Terrakion, Cheren) gone")
caves = ("VICTORY_ROAD_CAVE_1F", "VICTORY_ROAD_GROVE", "VICTORY_ROAD_RIVER", "VICTORY_ROAD_CAVE_2F", "VICTORY_ROAD_2F_BACK",
         "VICTORY_ROAD_MOUNTAINSIDE", "VICTORY_ROAD_3F", "VICTORY_ROAD_TUNNEL")
check(all(k in tmaps and k in SP for k in caves), "Victory Road's eight places")
for k in ("VICTORY_ROAD_CAVE_1F", "VICTORY_ROAD_GROVE", "VICTORY_ROAD_RIVER", "VICTORY_ROAD_CAVE_2F"):
    sm = tmaps[k].get("story_maps") or []
    check(len(sm) == 1 and sm[0]["when"] == ["unova_version:WHITE_2"], f"{k}: White 2's own people")
check(tmaps["VICTORY_ROAD_RIVER"]["trainer_spots"] != tmaps["VICTORY_ROAD_RIVER"]["story_maps"][0]["map"]["trainer_spots"],
      "the River Valley: each version's trainers")
check(tmaps["VICTORY_ROAD_CAVE_2F"]["edge_to"].get("57,27") == [57, 8], "doors pair up as Black 2's warps do (Cave 2F -> the River Valley)")
mt = tmaps["VICTORY_ROAD_MOUNTAINSIDE"]
check(mt["gated_exits"].get("CHALLENGERS_CAVE") == ["beat_unova_champion"], "the Zoroark's cave: after the League only")
hb = tmaps["VICTORY_ROAD_TUNNEL"]["scenes"][0]["event"]["battle"]
check(set(hb["team_choice"]) == {"495", "498", "501"} and hb["levels"][0] == 55 and hb["rewards"].get("TM126") == 1,
      "Hugh in the tunnel: his team by your starter, Lv 55; TM126 Thunderbolt")

print("2) N at the entrance: HM05 Waterfall; the Badge Check")
for k in ("b2_vr_waterfall", "b2_badge_check", "b2_vr_hugh"):
    flags.pop(k, None)
story.inventory.pop("HM_WATERFALL", None)
ds = walked("VICTORY_ROAD_UNOVA", (80, 52))
go(0, -1, 2, 60); settle(1500)
check(flags.get("b2_vr_waterfall") and story.inventory.get("HM_WATERFALL"), "N gives HM05 Waterfall")
ds = walked("VICTORY_ROAD_UNOVA", (41, 47))
go(-1, 0, 1, 60); settle(800)
check(flags.get("b2_badge_check") and "eight Badges" in heard(), "the Badge Check Gate scans the eight Badges")

print("3) Route 23's old man: TM125 Flamethrower; the healer")
flags.pop("b2_r23_tm35", None)
ds = walked("UNOVA_ROUTE_23", (5, 7), floor=2)
ok = use(ds, "Old man by the waterfall")
check(ok and flags.get("b2_r23_tm35") and story.inventory.get("TM125"), "the old man gives TM125 Flamethrower")

print("4) the tunnel: Hugh")
ds = walked("VICTORY_ROAD_TUNNEL", (13, 7))
go(-1, 0, 1, 60)
cur = until(BATTLES, 1500)
t = team_of(cur)
check(type(cur).__name__ in BATTLES and any(lv == 55 for _s, lv in t), f"Hugh battles you, Lv 55 ({t})")
if type(cur).__name__ in BATTLES:
    win(cur)
settle(600)
check(flags.get("b2_vr_hugh") and story.inventory.get("TM126"), "Hugh gives TM126 Thunderbolt")
story.current_area_key = "VICTORY_ROAD_TUNNEL"
check("b2_m46" in mains() and "b2_m45" not in mains(), f"the Journal: on to the League ({mains()})")

for f_ in fails:
    print("  -", f_)
print(f"##### {len(fails)} failures")
