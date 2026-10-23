print("1) Getting there")
story.badges = {"KANTO": ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH"]}
story.story_flags, story.inventory = {}, {}
check("Seagallop to One Island" not in travel("VERMILLION_CITY"), "no Tri-Pass: no ferry")
story.badges["KANTO"].append("VOLCANO")
story.sync_key_items()
check(story.inventory.get("TRI_PASS") == 1, "the Volcano Badge brings the Tri-Pass (old saves too)")
t = travel("VERMILLION_CITY")
check("Seagallop to One Island" in t and "Seagallop to Four Island" not in t, "Vermilion: Seagallop to One Island")
t = travel("ONE_ISLAND")
check({"Seagallop to Two Island", "Seagallop to Three Island"} <= set(t) and "Seagallop to Four Island" not in t, f"One Island: {t}")
check(len(SEVII) == 31, f"{len(SEVII)} Sevii areas")  # 24 + 7 added by areas_09_sevii.patch
bad = [(k, o.get("target_area")) for k in SEVII for o in prog[k].get("travel_options", []) + prog[k].get("route_menu", [])
       if o.get("target_area") and o["target_area"] not in prog]
check(not bad, f"every link leads somewhere {bad}")

print("2) Johto Pokemon early, only on Sevii")
story.visited_region_set = {"KANTO"}
story.starting_region = "KANTO"
story.current_area_key = "CAPE_BRINK"
pool = g.loader.area_data["SEVII_CAPE_BRINK_PERCENTAGES"]
check("187" in regional_forms.restrict(g, dict(pool)), "Hoppip on Cape Brink before Johto")
story.current_area_key = "VIRIDIAN_FOREST"
print("   (mainland:", story.get_current_region(), story.visited_regions(), prog["VIRIDIAN_FOREST"].get("subregion"), ")")
check("187" not in regional_forms.restrict(g, {"187": 10, "16": 10}), "but not on the Kanto mainland")

print("3) Mt. Ember and Moltres")
run("MT_EMBER", "TALK TO THE RESEARCHERS")
run("MT_EMBER", "CHASE OFF TEAM ROCKET")
check(lineup(battle_of(g.current_state))[0] == (109, 42), "Team Rocket on Mt. Ember")
st = state_for("MT_EMBER")
mol = opt("MT_EMBER", "CHALLENGE MOLTRES")
check(st._check_route_condition(mol["condition"], False), "Moltres at the summit")
story.story_flags["CINNABAR_VOLCANO_boss_defeated"] = True
check(not st._check_route_condition(mol["condition"], False), "not if you already beat it in the volcano")
check(not prog["CINNABAR_VOLCANO"].get("area_boss") and not prog["MT_MOON"].get("area_boss"), "volcano and Mt. Moon bosses moved")

print("4) Two and Three Island: Lostelle, bikers, the tutor")
run("TWO_ISLAND", "Lostelle's Dad")
check(not ow.CityState(g)._check_menu_condition(opt("THREE_ISLAND", "Bond Bridge")["condition"]), "bikers block Bond Bridge")
run("THREE_ISLAND", "Stop the Biker Gang")
check(lineup(battle_of(g.current_state))[-1] == (89, 46), "biker boss Paxton")
story.story_flags["beat_three_island_bikers"] = True
story.current_area_key = "THREE_ISLAND"
check(ow.CityState(g)._check_menu_condition(opt("THREE_ISLAND", "Bond Bridge")["condition"]), "bridge open")
st = state_for("BERRY_FOREST")
check(st._check_route_condition(opt("BERRY_FOREST", "FIND LOSTELLE")["condition"], False), "Hypno boss in the Berry Forest")
zard = mk(6)
zard.level = 50
story.player_team = [zard]
said = run("CAPE_BRINK", "VISIT THE MOVE TUTOR")
check("BLAST-BURN" in zard.moves, f"tutor: {said[-1][-1] if said else said}")

print("5) Islands 4-7 and the gems")
story.story_flags.update({"beat_champion": True, "unlocked_national_dex": True, "met_celio": True})
run("ONE_ISLAND", "Celio's Rainbow Pass")
check(story.inventory.get("RAINBOW_PASS") == 1, "Celio gives the Rainbow Pass")
check("Seagallop to Seven Island" in travel("ONE_ISLAND"), "Rainbow Pass: Islands 4-7")
run("FOUR_ISLAND", "Lorelei's House")
run("ICEFALL_CAVE", "STOP TEAM ROCKET")
check(isinstance(g.current_state, TrainerIntroState), "Icefall Cave Rocket battle")
check("Rocket Warehouse" not in travel("FIVE_ISLAND"), "warehouse hidden until the Sapphire is stolen")
run("DOTTED_HOLE", "READ THE BRAILLE", solve=False)
check(not story.story_flags.get("dotted_hole_open"), "wrong braille: still sealed")
run("DOTTED_HOLE", "READ THE BRAILLE")
check(story.story_flags.get("dotted_hole_open"), "braille solved: open")
run("DOTTED_HOLE", "TAKE THE SAPPHIRE")
check("Rocket Warehouse" in travel("FIVE_ISLAND"), "Gideon steals it: warehouse open")
run("ROCKET_WAREHOUSE", "UNLOCK THE DOORS")
run("ROCKET_WAREHOUSE", "CONFRONT THE ADMIN")
from src.world import levels
check(lineup(battle_of(g.current_state))[-1] == (112, levels.postgame_cap(story, story.area_region(story.current_area_key)) + 1), f"Admin Archer (post-game cap) {lineup(battle_of(g.current_state))}")
story.story_flags["sevii_warehouse_cleared"] = True
run("ROCKET_WAREHOUSE", "RECOVER THE GEMS")
run("ONE_ISLAND", "Give Celio the Gems")
check(story.story_flags.get("network_machine_fixed") and story.inventory.get("OLD_SEA_MAP") == 1
      and not story.inventory.get("RUBY"), "Network Machine fixed, Old Sea Map")
check("Seagallop to Faraway Island" in travel("ONE_ISLAND"), "ferry to Faraway Island")

print("6) Seven Island and Mew")
run("TANOBY_RUINS", "OPEN THE CHAMBERS")
st = state_for("TANOBY_RUINS")
check(st._check_route_condition(opt("TANOBY_RUINS", "CATCH WILD PKMN")["condition"], False), "Tanoby chambers: Unown")
story.current_area_key = "SEVEN_ISLAND"
lobby = ow.GymLobbyState(g, None)
g.change_state(lobby)
lobby.challenge_gym()
check(lineup(battle_of(g.current_state))[0] == (57, 57), "Trainer Tower floor 1")
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
check(len(missions) == 6 and all(m["region"] == "KANTO" for m in missions), "6 Sevii journal entries")
# areas_09_sevii.patch: the seven added Sevii areas, linked both ways and opening cleanly
NEW7 = ["CANYON_ENTRANCE", "GREEN_PATH", "OUTCAST_ISLAND", "SEVII_ALTERING_CAVE", "WATER_PATH", "MEMORIAL_PILLAR", "RESORT_GORGEOUS"]
def _tg(k): return {o.get("target_area") for o in prog[k].get("travel_options", []) + prog[k].get("route_menu", []) if o.get("target_area")}
check(all(k in SEVII for k in NEW7), "added areas are tagged SEVII")
oneway = [(k, t) for k in NEW7 for t in _tg(k) if k not in _tg(t)]
check(not oneway, f"added Sevii links go both ways {oneway}")
no_traps(NEW7)
print("FAILURES:", fails)
