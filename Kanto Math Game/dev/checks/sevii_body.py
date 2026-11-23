print("1) Getting there")
story.badges = {"KANTO": ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH"]}
story.story_flags, story.inventory = {"received_starter_kanto": True, "received_pokedex_kanto": True}, {}  # past Oak's Parcel
check("Seagallop to One Island" not in travel("VERMILLION_CITY"), "no Tri-Pass: no ferry")
story.badges["KANTO"].append("VOLCANO")
story.sync_key_items()
# (11-17, FireRed: the Volcano Badge opens Bill's boat from Cinnabar; Celio on One Island gives the Tri-Pass)
check(not story.inventory.get("TRI_PASS") and "Seagallop to One Island" in travel("CINNABAR_ISLAND") and "Seagallop to One Island" not in travel("VERMILLION_CITY"),
      "the Volcano Badge: Bill's boat from Cinnabar to One Island; no Tri-Pass yet, so no ferry from Vermilion")
story.inventory["TRI_PASS"] = 1; story.story_flags["got_tri_pass"] = True   # (Celio's gift: kanto_gates plays it)
t = travel("VERMILLION_CITY")
check("Seagallop to One Island" in t and "Seagallop to Four Island" not in t, "Vermilion: Seagallop to One Island")
t = travel("ONE_ISLAND")
check({"Seagallop to Two Island", "Seagallop to Three Island"} <= set(t) and "Seagallop to Four Island" not in t, f"One Island: {t}")
check(len(SEVII) == 35, f"{len(SEVII)} Sevii areas")  # 24 + 7 (areas_09_sevii.patch) + 3 (Three Isle Port, Navel Rock, Birth Island; the empty Three Isle Path went 11-04) + the Trainer Tower (11-23)
bad = [(k, o.get("target_area")) for k in SEVII for o in prog[k].get("travel_options", []) + prog[k].get("route_menu", [])
       if o.get("target_area") and o["target_area"] not in prog]
check(not bad, f"every link leads somewhere {bad}")

print("2) Johto Pokemon early, only on Sevii")
story.visited_region_set = {"KANTO"}
story.starting_region = "KANTO"
story.current_area_key = "RUIN_VALLEY"  # (FRLG: Cape Brink has no Johto Pokemon; Ruin Valley does)
pool = g.loader.area_data["SEVII_RUIN_VALLEY_PERCENTAGES"]
check("193" in regional_forms.restrict(g, dict(pool)), "Yanma in Ruin Valley before Johto")
story.current_area_key = "VIRIDIAN_FOREST"
print("   (mainland:", story.get_current_region(), story.visited_regions(), prog["VIRIDIAN_FOREST"].get("subregion"), ")")
check("193" not in regional_forms.restrict(g, {"193": 10, "16": 10}), "but not on the Kanto mainland")

print("3) Mt. Ember and Moltres")
run("MT_EMBER", "TALK TO THE RESEARCHERS")
run("MT_EMBER", "CHASE OFF TEAM ROCKET")   # (11-17: FireRed's two diggers first, Grunt 538 and Grunt 537, then the old build's pair)
check(lineup(battle_of(g.current_state)) == [(19, 35), (20, 35), (27, 35), (28, 35)], "Mt. Ember: FireRed's second digger (Rattata, Raticate, Sandshrew, Sandslash 35)")
run("MT_EMBER", "ROCKET GRUNT")
check(lineup(battle_of(g.current_state)) == [(104, 37), (105, 37)], "...FireRed's first digger (Cubone, Marowak 37)")
story.story_flags["ember_grunt_a"] = story.story_flags["ember_grunt_b"] = True
run("MT_EMBER", "JESSIE AND JAMES")
check(lineup(battle_of(g.current_state)) == [(24, 37), (110, 37), (52, 37)], "...then Jessie & James (Jordan 11-17: in place of the old Rocket pair)")
run("MT_EMBER", "RUBY")
check(story.inventory.get("RUBY") == 1, "the Ruby, at the bottom of the Ruby Path (FireRed's first trip)")
run("ONE_ISLAND", "Celio's Ruby")
check(story.story_flags.get("celio_has_ruby") and not story.inventory.get("RUBY"), "Celio takes the Ruby")
st = state_for("MT_EMBER")
mol = opt("MT_EMBER", "CHALLENGE MOLTRES")
check(st._check_route_condition(mol["condition"], False), "Moltres at the summit")
story.story_flags["MT_EMBER_boss_defeated"] = True  # (an old volcano win becomes this when the save loads)
check(not st._check_route_condition(mol["condition"], False), "not once it's beaten")
check(not prog["CINNABAR_VOLCANO"].get("area_boss") and not prog["MT_MOON"].get("area_boss"), "volcano and Mt. Moon bosses moved")

print("4) Two and Three Island: Lostelle, bikers, the tutor")
run("TWO_ISLAND", "Lostelle's Dad")
check(not ow.CityState(g)._check_menu_condition(opt("THREE_ISLAND", "Bond Bridge")["condition"]), "bikers block Bond Bridge")
run("THREE_ISLAND", "Stop the Biker Gang")   # (11-17: FireRed's three Goons one after another, then Cue Ball Paxton)
check(lineup(battle_of(g.current_state)) == [(109, 37), (88, 37)], "the first Biker Goon (Koffing, Grimer 37)")
story.story_flags.update({"three_goon_1": True, "three_goon_2": True, "three_goon_3": True})
run("THREE_ISLAND", "Stop the Biker Gang")
check(lineup(battle_of(g.current_state)) == [(110, 39), (89, 39)], "...their boss, Cue Ball Paxton (Weezing, Muk 39)")
story.story_flags["beat_three_island_bikers"] = True
story.current_area_key = "THREE_ISLAND"
check(ow.CityState(g)._check_menu_condition(opt("THREE_ISLAND", "Bond Bridge")["condition"]), "bridge open")
st = state_for("BERRY_FOREST")
check(st._check_route_condition(opt("BERRY_FOREST", "FIND LOSTELLE")["condition"], False), "Hypno boss in the Berry Forest")
zard = mk(6)
zard.level = 50
story.player_team = [zard]
said = run("CAPE_BRINK", "VISIT THE MOVE TUTOR")
from src.pokemon import moves as _ml
check("BLAST-BURN" in _ml.move_pool(g, zard), f"tutor: {said[-1][-1] if said else said}")

print("5) Islands 4-7 and the gems")
story.story_flags.update({"beat_champion": True, "unlocked_national_dex": True, "met_celio": True})
run("ONE_ISLAND", "Celio's Rainbow Pass")
check(story.inventory.get("RAINBOW_PASS") == 1, "Celio gives the Rainbow Pass")
check("Seagallop to Seven Island" in travel("ONE_ISLAND"), "Rainbow Pass: Islands 4-7")
run("FOUR_ISLAND", "Lorelei's House")
run("ICEFALL_CAVE", "STOP TEAM ROCKET")
check(isinstance(g.current_state, TrainerIntroState) and lineup(battle_of(g.current_state)) == [(110, 38), (24, 38), (52, 38)], "Icefall Cave: Jessie & James (in place of FireRed's Grunt)")
check("Rocket Warehouse" not in travel("FIVE_ISLAND"), "warehouse hidden until the Sapphire is stolen")
import json as _json
_rv = _json.load(open("assets/town_maps.json", encoding="utf-8"))["RUIN_VALLEY"].get("barred", [])
check(any((b.get("open_with") or {}).get("flag") == "dotted_hole_open" and "has_item:HM_CUT" in (b.get("open_with") or {}).get("condition", []) for b in _rv),
      "the Dotted Hole's door: braille outside, opened with Cut (FireRed; Jordan 11-17)")
story.story_flags["dotted_hole_open"] = True   # (the walk itself is in sevii_maps)
run("DOTTED_HOLE", "TAKE THE SAPPHIRE")
check("Rocket Warehouse" in travel("FIVE_ISLAND"), "Gideon steals it: warehouse open")
run("ROCKET_WAREHOUSE", "UNLOCK THE DOORS")
run("ROCKET_WAREHOUSE", "CONFRONT THE ADMIN")
from src.world import levels
_arch = lineup(battle_of(g.current_state))
check(_arch == [(42, 53), (110, 54), (229, 55)], f"the Warehouse's last Admin with FireRed's team and levels (11-17: Golbat, Weezing, Houndoom) {_arch}")
story.story_flags["sevii_warehouse_cleared"] = True
run("ROCKET_WAREHOUSE", "RECOVER THE GEMS")
run("ONE_ISLAND", "Give Celio the Gems")
check(story.story_flags.get("network_machine_fixed") and story.inventory.get("OLD_SEA_MAP") == 1
      and not story.inventory.get("SAPPHIRE"), "the Sapphire from the Warehouse: Network Machine fixed, Old Sea Map")
check("Seagallop to Faraway Island" in travel("ONE_ISLAND"), "ferry to Faraway Island")

print("6) Seven Island and Mew")
run("SEVAULT_CANYON", "OPEN THE CHAMBERS")  # (the Tanoby Key cave is in Sevault Canyon, as in FireRed: the option moved there with the maps, 11-11)
story.balls_left = 10  # (Poke Balls are in the Bag in use now)
st = state_for("TANOBY_RUINS")
check(st._check_route_condition(opt("TANOBY_RUINS", "CATCH WILD PKMN")["condition"], False), "Tanoby chambers: Unown")
_ttd = _json.load(open("assets/trainer_tower.json", encoding="utf-8"))   # (11-23: FireRed's Trainer Tower, walked - sevii_maps plays it)
check(any(o.get("target_area") == "TRAINER_TOWER" for o in g.loader.area_data["STORY_PROGRESSION"]["SEVEN_ISLAND"]["explore_options"]) and len(_ttd["climbs"]) == 4,
      "Trainer Tower: Seven Island's door leads in; FireRed's four climbs")
st = state_for("FARAWAY_ISLAND")
mew = opt("FARAWAY_ISLAND", "CHALLENGE MEW")
dex = g.data.data.setdefault("pokedex", {})
dex.clear()
check(not st._check_route_condition(mew["condition"], False), "Mew hides until all 150")
for pid in range(1, 151):
    dex[f"{pid}-normal"] = {"id": pid}
check(st._check_route_condition(mew["condition"], False), "all 150: Mew appears")

no_traps(SEVII)
print("7) Visiting every Sevii area")
for k in SEVII:
    try:
        state_for(k)
        for _ in range(3):
            g.current_state.update()
        g.current_state.draw()
    except Exception as e:
        check(False, f"{k}: {type(e).__name__} {e}")
missions = [m for m in g.loader.area_data["JOURNAL_MISSIONS"] if m["id"].startswith("sevii")]
check(len(missions) == 15 and all(m["region"] == "KANTO" for m in missions), "15 Sevii journal entries (11-17: + the Ruby, Celio's Ruby, the National Pokedex; Back to Celio, the Unown of Tanoby and the legendaries too)")
# areas_09_sevii.patch: the seven added Sevii areas, linked both ways and opening cleanly
NEW7 = ["CANYON_ENTRANCE", "GREEN_PATH", "OUTCAST_ISLAND", "SEVII_ALTERING_CAVE", "WATER_PATH", "MEMORIAL_PILLAR", "RESORT_GORGEOUS"]
def _tg(k): return {o.get("target_area") for o in prog[k].get("travel_options", []) + prog[k].get("route_menu", []) if o.get("target_area")}
check(all(k in SEVII for k in NEW7), "added areas are tagged SEVII")
oneway = [(k, t) for k in NEW7 for t in _tg(k) if k not in _tg(t)]
check(not oneway, f"added Sevii links go both ways {oneway}")
no_traps(NEW7)
print("FAILURES:", fails)
