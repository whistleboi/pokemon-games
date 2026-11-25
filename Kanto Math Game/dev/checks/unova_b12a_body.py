# Unova batch 12a (11-25): Black 2's west today, after the title - Skyarrow Bridge from Castelia, Pinwheel Forest (Cheren
# walks it with you; two tag pairs battle you both; Rumination Field, two Hidden Grottoes), Nacrene City (Lenora's Cover /
# Plume Fossil, the Museum's restoration desk, Cafe Warehouse's specials and the Grubby Hanky, the gate's Egg), Route 3 (the
# preschool, the Day Care, two Hidden Grottoes) and Wellspring Cave.
#   bash dev/checks/run.sh unova_b12a
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
for k in ("beat_unova_champion", "b2_hall_of_fame", "move_offer_unova", "visited_ASPERTIA_CITY", "visited_CASTELIA_CITY"):
    flags[k] = True
said = []
tmaps = json.load(open("assets/town_maps.json", encoding="utf-8"))
prog = json.load(open("assets/unova_area_data.json", encoding="utf-8"))
SP = prog["STORY_PROGRESSION"]
exec(open("dev/checks/unova_lib.py", encoding="utf-8").read())

print("1) the places and how they join")
sky, pw, pwo = tmaps["SKYARROW_BRIDGE"], tmaps["PINWHEEL_FOREST"], tmaps["PINWHEEL_FOREST_OUTSIDE"]
nac, r3, ws, ws1 = tmaps["NACRENE_CITY"], tmaps["UNOVA_ROUTE_3"], tmaps["WELLSPRING_CAVE"], tmaps["WELLSPRING_CAVE_B1F"]
check(tmaps["CASTELIA_CITY"]["gated_exits"].get("SKYARROW_BRIDGE") == ["beat_unova_champion"],
      "Castelia's Bridge Gate opens onto Skyarrow Bridge after the title")
check(sky["rooms"]["gate"]["exits"].get("<") == "PINWHEEL_FOREST", "the bridge's far gate leads into Pinwheel Forest")
check(set(pw["exits"].values()) == {"SKYARROW_BRIDGE", "PINWHEEL_FOREST_OUTSIDE"} and {"field", "grotto"} <= set(pw["rooms"]),
      "Pinwheel Forest: the bridge, the forest's edge; Rumination Field and a Hidden Grotto")
check(set(pwo["exits"].values()) == {"PINWHEEL_FOREST", "NACRENE_CITY"} and "grotto" in pwo["rooms"],
      "the forest's edge: into the forest, east to Nacrene; the Challenge Rock's Hidden Grotto")
check(nac["exits"].get("<") == "PINWHEEL_FOREST_OUTSIDE" and "UNOVA_ROUTE_3" in nac["exits"].values()
      and {"museum", "library", "office", "center", "cafe", "gate_e", "loblolly"} <= set(nac["rooms"]),
      "Nacrene: west to the forest, its east gate to Route 3; the Museum (library, office), Center, Cafe, Loblolly's")
check(set(r3["exits"].values()) == {"NACRENE_CITY", "STRIATON_CITY", "WELLSPRING_CAVE"}
      and {"preschool", "daycare", "grotto", "grotto2"} <= set(r3["rooms"]),
      "Route 3: Nacrene, Striaton, Wellspring Cave; the preschool, the Day Care, two Hidden Grottoes")
check(set(ws["exits"].values()) == {"UNOVA_ROUTE_3", "WELLSPRING_CAVE_B1F"} and set(ws1["exits"].values()) == {"WELLSPRING_CAVE"},
      "Wellspring Cave and its B1F")
for k in ("PINWHEEL_FOREST", "PINWHEEL_FOREST_OUTSIDE", "UNOVA_ROUTE_3", "WELLSPRING_CAVE", "WELLSPRING_CAVE_B1F"):
    pool = {t["name"] for t in SP[k]["trainer_pool"]}
    m = tmaps[k]
    check(SP[k].get("wild_tables") and set(m.get("trainer_spots", [])) == pool,
          f"{k}: Black 2's wild tables; every trainer stands in the place ({len(pool)})")
pairs = [t for t in SP["PINWHEEL_FOREST"]["trainer_pool"] if (t.get("battle_options") or {}).get("second_trainer")]
check(sorted(t.get("victory_flag") for t in pairs) == ["b2_pw_pair_1", "b2_pw_pair_2"], "Pinwheel's two tag pairs, each a double")

print("2) Cheren walks the forest with you")
ds = walked("PINWHEEL_FOREST", (75, 27))
from src.world import walk_partners as WP
joined = False
for mv in list(ds.run.floor.movers):
    if mv.kind == "figure" and isinstance(mv.payload, dict) and mv.payload.get("text") == "Cheren":
        ds._get_route_callback(mv.payload)(); settle(200)
        joined = True
        break
check(joined and WP.active(story, "PINWHEEL_FOREST") == "cheren_pinwheel", "Cheren joins you inside the forest")
opts = WP.trainer_options(story, dict(pairs[0]["battle_options"]))
check(opts.get("partner") and opts.get("second_trainer") and opts.get("heal_after"),
      "a tag pair battles you and Cheren together; he heals your team after")
flags["b2_pw_pair_2"] = True
check(WP.active(story, "PINWHEEL_FOREST") is None, "he heads off once the second pair is beaten")

print("3) Lenora's Fossil, the restoration desk")
for k in ("COVER_FOSSIL", "PLUME_FOSSIL"):
    story.inventory.pop(k, None)
flags.pop("b2_nacrene_fossil", None)
st = town("NACRENE_CITY", (11, 27), "museum")
ok = talk(st, "Lenora")
cur = until(("PickListState",), 400)
check(ok and type(cur).__name__ == "PickListState" and [v for _l, v in cur.choices] == ["COVER_FOSSIL", "PLUME_FOSSIL"],
      "Lenora asks: the Cover Fossil or the Plume Fossil?")
if type(cur).__name__ == "PickListState":
    cur.pick("PLUME_FOSSIL"); settle(200)
check(story.inventory.get("PLUME_FOSSIL") == 1 and flags.get("b2_nacrene_fossil") == "PLUME_FOSSIL", "you get the one you pick, once")
st = g.current_state if isinstance(g.current_state, CityState) else town("NACRENE_CITY", (11, 27), "museum")
talk(st, "Lenora"); settle(200)
check(story.inventory.get("PLUME_FOSSIL") == 1 and type(g.current_state).__name__ != "PickListState", "asked again: no second Fossil")
desk = [o for p in nac["rooms"]["museum"]["people"] for o in (p if isinstance(p, list) else [p]) if o.get("target") == "nacrene_museum"]
check(len(desk) == 1, "the front desk restores Fossils (town_kanto.visit_stoneman: Cover -> Tirtouga, Plume -> Archen)")

print("4) the gate's Egg")
n = len(story.player_team)
st = town("NACRENE_CITY", (9, 4), "gate_e")
talk(st, "Pokemon Breeder"); settle(200)
egg = story.player_team[-1] if len(story.player_team) > n else None
check(egg is not None and flags.get("b2_nacrene_egg"), f"a Pokemon Breeder gives you an Egg ({getattr(egg, 'id', None)})")

print("5) Cafe Warehouse")
cafe = {o.get("text"): o for p in nac["rooms"]["cafe"]["people"] for o in (p if isinstance(p, list) else [p])}
w = [o for p in nac["rooms"]["cafe"]["people"] for o in (p if isinstance(p, list) else [p]) if o.get("text") == "Waitress"]
gifts = sorted((o["condition"][0], list(o["event"]["gift_item"])[0]) for o in w if "gift_item" in o.get("event", {}))
check(gifts == [("weekday:sat", "LEMONADE"), ("weekday:wed", "SODA_POP")], f"the specials: Wednesday's Soda Pop, Saturday's Lemonade ({gifts})")
hanky = cafe["Waitress downstairs"]["event"]["stages"]
check(hanky[0]["ready"] == ["weekday:sun"] and "GRUBBY_HANKY" in hanky[0]["gift_item"]
      and cafe["Customer with a Watchog"]["event"]["stages"][0]["ready"][0] == "weekday:thu" and "FLUFFY_TAIL" in hanky[1]["gift_item"],
      "the Grubby Hanky on Sunday, back to its owner on Thursday, a Fluffy Tail the Sunday after")

print("6) Route 3's Day Care")
dc = [o for p in r3["rooms"]["daycare"]["people"] + r3["people"] for o in (p if isinstance(p, list) else [p]) if o.get("action") == "DAYCARE"]
check(len(dc) == 2, "the Day-Care Lady inside and the Day-Care Man outside")

for f_ in fails:
    print("  -", f_)
print(f"##### {len(fails)} failures")
