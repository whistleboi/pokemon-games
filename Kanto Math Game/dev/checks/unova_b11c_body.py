# Unova batch 11c (11-25): the Zoroark's cave and N's Castle, Black 2's - Hugh's sister's dream, the Zoroark, N on 1F, his
# old room, 2F, the throne room's battle (Zekrom / Reshiram, Lv 70), the Dark Stone / Light Stone; his monthly rematch by the
# season once Kyurem's caught; Challenger's Cave reached from inside the cave (Jordan 11-25).
#   bash dev/checks/run.sh unova_b11c
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
story.badges["UNOVA"] = ["BASIC", "TOXIC", "INSECT", "BOLT", "QUAKE", "JET", "LEGEND", "WAVE"]
for k in ("beat_unova_champion", "b2_hall_of_fame", "move_offer_unova", "visited_N_CASTLE", "visited_ASPERTIA_CITY",
          "b2_vr_hugh", "b2_chasm_done"):
    flags[k] = True
said = []
tmaps = json.load(open("assets/town_maps.json", encoding="utf-8"))
prog = json.load(open("assets/unova_area_data.json", encoding="utf-8"))
SP = prog["STORY_PROGRESSION"]
exec(open("dev/checks/unova_lib.py", encoding="utf-8").read())
BATTLES = ("TrainerIntroState", "TrainerBattleState", "DoubleBattleState", "GymBattleState", "BattleState")
F1, ROOM, F2, THRONE = 1, 2, 3, 4

print("1) the places")
nc, mt = tmaps["N_CASTLE"], tmaps["VICTORY_ROAD_MOUNTAINSIDE"]
check(set(nc["exits"].values()) == {"VICTORY_ROAD_MOUNTAINSIDE", "CHALLENGERS_CAVE"} and set(nc["rooms"]) == {"1f", "nroom", "2f", "throne"},
      "the Zoroark's cave: back to the mountainside, Challenger's Cave inside it; N's Castle's 1F, N's room, 2F, the throne room")
check("N_CASTLE" in mt["exits"].values() and mt["gated_exits"].get("N_CASTLE") == ["beat_unova_champion", "b2_sister_dream"],
      "Victory Road's mountainside leads to the cave once Hugh's sister has dreamed of it")
check(SP["CHALLENGERS_CAVE"]["route_menu"][-1]["target_area"] == "N_CASTLE", "Challenger's Cave's way back: the Zoroark's cave")
check(SP["N_CASTLE"].get("wild_tables"), "the cave's wild Pokemon (Black 2's: Druddigon, Zweilous; Excadrill and Onix in the dust)")

print("2) Hugh's sister's dream")
st = town("ASPERTIA_CITY", (7, 5), "hugh_2f")
ok = talk(st, "{rival_name}'s sister ")
check(ok and flags.get("b2_sister_dream") and "Zoroark" in heard(), f"she dreamed of a Zoroark on Victory Road ({heard()[:60]})")

print("3) the Zoroark")
ds = walked("N_CASTLE", (4, 21))
go(0, -1, 2, 60); settle(400)
check(flags.get("b2_nc_zoroark"), "it runs deeper in, toward the ruins")

print("4) N's Castle")
ds = walked("N_CASTLE", (10, 10), floor=F1)
go(-1, 0, 1, 60); settle(600)
check(flags.get("b2_nc_met") and "deepest chamber" in heard(), f"1F: N asks you to lead him to the deepest chamber ({heard()[:60]})")
ds = walked("N_CASTLE", (9, 17), floor=ROOM); settle(600)
check(flags.get("b2_nc_room") and "Ghetsis" in heard(), "N's room: his story")
ds = walked("N_CASTLE", (31, 13), floor=F2)
go(-1, 0, 1, 60); settle(600)
check(flags.get("b2_nc_2f"), "2F: 'This is our destination... Go inside.'")
stones = story.inventory.get("DARK_STONE", 0)
ds = walked("N_CASTLE", (16, 43), floor=THRONE)
go(0, -1, 2, 60)
cur = until(BATTLES, 1500)
t = team_of(cur)
check(type(cur).__name__ in BATTLES and t == [(644, 70)], f"the throne room: N with Zekrom, Lv 70 ({t})")
if type(cur).__name__ in BATTLES:
    win(cur)
settle(600)
check(flags.get("b2_n_beaten") and story.inventory.get("DARK_STONE", 0) == stones + 1, "N gives you the Dark Stone, for Dragonspiral Tower")

print("5) White 2: Reshiram and the Light Stone")
th = nc["rooms"]["throne"]
w2 = next(s for s in th["scenes"] if "unova_version:WHITE_2" in s["condition"])
check(w2["event"]["battle"]["team"] == [643] and "LIGHT_STONE" in w2["event"]["battle"]["rewards"], "Reshiram Lv 70; the Light Stone")

print("6) his monthly rematch, by the season")
flags["GIANT_CHASM_boss_defeated"] = True
flags.pop("b2_n_month", None)
ds = walked("N_CASTLE", (16, 39), floor=THRONE)
from src.world import seasons as _SE
season = str(_SE.current(story) if hasattr(_SE, "current") else "").upper()
spot = next((t for t, m in ds.run.floor.movers_at().items() if False), None) if hasattr(ds.run.floor, "movers_at") else None
said.clear()
ds.run.player = (16, 38) if ds.run.floor.walkable(16, 38) else ds.run.player
ds.facing = (0, -1)
from src.states.overworld import dungeon as _DG
talked = False
for m in list(ds.run.floor.movers):
    if m.kind == "figure" and isinstance(m.payload, dict) and str(m.payload.get("text", "")).startswith("N") and (m.payload.get("event") or {}).get("monthly"):
        ds._get_route_callback(m.payload)()
        talked = True
        break
cur = until(BATTLES, 800)
t = team_of(cur)
check(talked and type(cur).__name__ in BATTLES and len(t) == 6 and max(lv for _s, lv in t) == 77,
      f"N's seasonal team, Lv 75-77 ({season}: {t})")
if type(cur).__name__ in BATTLES:
    win(cur)
check(flags.get("b2_n_month"), "once a month")

for f_ in fails:
    print("  -", f_)
print(f"##### {len(fails)} failures")
