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
BATTLES = ("TrainerIntroState", "TrainerBattleState", "DoubleBattleState", "GymBattleState", "BattleState")

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

print("7) the second half: Striaton, the Dreamyard, Route 2, Accumula, Route 1, Nuvema")
st_, dy, dy1 = tmaps["STRIATON_CITY"], tmaps["DREAMYARD"], tmaps["DREAMYARD_B1F"]
r2, acc, r1, nuv = tmaps["UNOVA_ROUTE_2"], tmaps["ACCUMULA_TOWN"], tmaps["UNOVA_ROUTE_1"], tmaps["NUVEMA_TOWN"]
check(r3["edge_to"].get("79,31") == [15, 1] and st_["edge_to"].get("15,0") == [79, 30], "Route 3 and Striaton's north road meet tile for tile")
check({"UNOVA_ROUTE_3", "UNOVA_ROUTE_2", "DREAMYARD"} <= set(st_["exits"].values())
      and {"restaurant", "center", "school"} <= set(st_["rooms"]), "Striaton: Route 3, Route 2, the Dreamyard; the restaurant, Center, school")
check(set(dy["exits"].values()) == {"STRIATON_CITY", "DREAMYARD_B1F"} and set(dy1["exits"].values()) == {"DREAMYARD"}
      and len([k for k, v in dy["edge_to"].items() if v in ([25, 3], [4, 20], [25, 27])]) == 9,
      "the Dreamyard's three stairways each lead to their own spot in the basement")
check(set(r2["exits"].values()) == {"STRIATON_CITY", "ACCUMULA_TOWN"} and "grotto" in r2["rooms"], "Route 2: Striaton, Accumula's gate; a Hidden Grotto")
check(acc["rooms"]["gate_w"]["exits"].get("<") == "UNOVA_ROUTE_2" and acc["exits"].get("v") == "UNOVA_ROUTE_1",
      "Accumula: its gate west to Route 2, south to Route 1")
check(set(r1["exits"].values()) == {"ACCUMULA_TOWN", "NUVEMA_TOWN"} and r1["rooms"]["gate"]["exits"].get("<") == "UNOVA_ROUTE_17",
      "Route 1: Accumula, Nuvema; its gate to Route 17")
check(nuv["exits"].get("^") == "UNOVA_ROUTE_1" and {"hero", "hero_2f", "bianca", "cheren", "lab"} <= set(nuv["rooms"]),
      "Nuvema: the hero's house, Bianca's and Cheren's, Juniper's lab")
for k in ("DREAMYARD", "DREAMYARD_B1F", "UNOVA_ROUTE_2", "UNOVA_ROUTE_1"):
    pool = {t["name"] for t in SP[k]["trainer_pool"]}
    check(SP[k].get("wild_tables") and set(tmaps[k].get("trainer_spots", [])) == pool, f"{k}: Black 2's wild tables and trainers ({len(pool)})")
lati = [o for p in dy["people"] for o in (p if isinstance(p, list) else [p]) if o.get("action") == "BOSS"]
check(sorted((o["boss"]["id"], o["boss"]["level"]) for o in lati) == [(380, 68), (381, 68)],
      "the Dreamyard's walkway: Latios (Black 2) / Latias (White 2), Lv 68")

print("8) the restaurant's Multi Battle")
flags.pop("b2_striaton_multi", None)
for k in [k for k in flags if k.startswith("b2_striaton_multi@")]:
    flags.pop(k)
st = town("STRIATON_CITY", (10, 17), "restaurant")
talk(st, "Cilan")
cur = until(BATTLES, 800)
t = team_of(cur)
opts = getattr(getattr(cur, "next_state", None) or cur, "battle_options", None) or {}
check(type(cur).__name__ in BATTLES and t[:3] == [(631, 65), (555, 65), (514, 67)], f"Cilan teams up with you against Chili and Cress ({t})")
if type(cur).__name__ in BATTLES:
    win(cur)
settle(300)
check(any(k.startswith("b2_striaton_multi@") for k in flags), "once a day")

print("9) Accumula's people")
from src.pokemon.data import Pokemon as _P
keep = list(story.player_team)
story.player_team = [_P(g.loader.fetch_specific(595), g.assets)] + keep[:1]   # (Joltik: 0.1 m)
dolls = story.inventory.get("POKE_DOLL", 0)
st = town("ACCUMULA_TOWN", (8, 25))
talk(st, "Youngster on the lower level"); settle(200)
check(story.inventory.get("POKE_DOLL", 0) == dolls + 1, "the tiny-Pokemon fan: a Poke Doll for your Joltik")
flags["starter_unova"] = 501
gems = story.inventory.get("WATER_GEM", 0)
flags.pop("b2_acc_quiz", None)
st = town("ACCUMULA_TOWN", (6, 6), "house_nw_2f")
talk(st, "Girl with a Pokedex"); settle(200)
check(story.inventory.get("WATER_GEM", 0) == gems + 1, "the first-partner quiz: Oshawott's height, a Water Gem")
rock = _P(g.loader.fetch_specific(76), g.assets); rock.ability_override = "SOLID-ROCK"
story.player_team = [rock] + keep[:1]
stones = story.inventory.get("DAWN_STONE", 0)
flags.pop("b2_r2_solid_rock", None)
ds = walked("UNOVA_ROUTE_2", (60, 11))
lady = next((m for m in ds.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == "Lady on the hill"), None)
if lady:
    ds._get_route_callback(lady.payload)(); settle(200)
check(lady is not None and story.inventory.get("DAWN_STONE", 0) == stones + 1, "Route 2's Lady: a Pokemon with Solid Rock, a Dawn Stone")
story.player_team = keep

print("10) Nuvema")
juice = story.inventory.get("BERRY_JUICE", 0)
st = town("NUVEMA_TOWN", (5, 9), "cheren")
talk(st, "Cheren's Dad"); settle(200)
check(story.inventory.get("BERRY_JUICE", 0) == juice + 1, "Cheren's father thanks his son's first Gym challenger with a Berry Juice")
lab = {o.get("text") for p in nuv["rooms"]["lab"]["people"] for o in (p if isinstance(p, list) else [p])}
check({"Cedric Juniper", "Professor Juniper"} <= lab, "Juniper's lab: Cedric (the Super Rod) and the Professor")

for f_ in fails:
    print("  -", f_)
print(f"##### {len(fails)} failures")
