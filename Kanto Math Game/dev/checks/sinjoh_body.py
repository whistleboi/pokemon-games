SIN = [k for k, a in prog.items() if a.get("subregion") == "SINJOH"]
ENTRY = "Follow the Unown (Sinjoh Ruins)"


def explore(area):
    c = ow.CityState(g)
    return [o["text"] for o in prog[area]["explore_options"] if c._check_menu_condition(o.get("condition"))
            and not (o.get("flag_condition", "").startswith("not ") and story.story_flags.get(o["flag_condition"][4:]))]


print("1) Getting in (HGSS: Arceus at the Ruins of Alph)")
story.badges = {"JOHTO": ["x"] * 8}
story.story_flags, story.inventory, story.catch_counts = {}, {}, {}
story.player_team = [mk(25)]
check(ENTRY not in travel("RUINS_OF_ALPH"), "no Arceus: no way in")
story.player_team.append(mk(493))
check(ENTRY in travel("RUINS_OF_ALPH"), "Arceus in the party: the Unown take you")
check(SIN == ["SINJOH_CABIN"] and prog["SINJOH_CABIN"]["route_name"] == "Sinjoh Ruins", f"one area, as in the game: {SIN}")
check(not prog["SINJOH_CABIN"].get("trainer_pool") and not prog["SINJOH_CABIN"].get("wild_pool_percentages"),
      "no wild Pokemon or trainers")
check("Abra's Teleport (home)" in travel("SINJOH_CABIN")
      and prog["SINJOH_CABIN"]["travel_options"][0]["target_area"] == "NEW_BARK_TOWN", "the old man's Abra Teleports you home")
from src.states.menus import RegionSelectionState
check("Sinjoh Ruins" not in str(RegionSelectionState.SUB_REGIONS), "not listed as a sub-region on the title screen")
state_for("SINJOH_CABIN")

print("2) The Mystri Stage")
check("THE MYSTRI STAGE" not in explore("SINJOH_CABIN"), "the stage waits for Cynthia")
run("SINJOH_CABIN", "Talk to Cynthia")
check("THE MYSTRI STAGE" in explore("SINJOH_CABIN"), "Cynthia: on to the stage")
run("SINJOH_CABIN", "THE MYSTRI STAGE")
check(not story.story_flags.get("sinjoh_rite_ready"), "other Pokemon in the party: Cynthia turns you back")
story.player_team = [mk(493)]
run("SINJOH_CABIN", "THE MYSTRI STAGE")
m = explore("SINJOH_CABIN")
check({"RECEIVE DIALGA", "RECEIVE PALKIA", "RECEIVE GIRATINA"} <= set(m), f"choose one of three: {m}")
run("SINJOH_CABIN", "RECEIVE GIRATINA")
gira = [p for p in story.player_team if p.id == 487]
check(gira and gira[0].level == 1, f"Giratina joins at Lv 1 {[ (p.id, p.level) for p in story.player_team]}")
check(story.inventory.get("GRISEOUS_ORB") == 1, "with the Griseous Orb")
m = explore("SINJOH_CABIN")
check(not any(t.startswith("RECEIVE") for t in m), f"one dragon for now: {m}")
check(ENTRY not in travel("RUINS_OF_ALPH"), "the Ruins of Alph link closes afterwards")

print("3) The Unown open the ruins again: 14 forms for a second dragon, 28 for the third")
story.player_team = [mk(493)]
for f in story.UNOWN_FORMS[:13]:
    story.catch_counts[f"201_{f}"] = 1
check(ENTRY not in travel("RUINS_OF_ALPH"), "13 Unown forms: still closed")
story.catch_counts[f"201_{story.UNOWN_FORMS[13]}"] = 1
check(ENTRY in travel("RUINS_OF_ALPH"), "14 Unown forms: open again")
m = explore("SINJOH_CABIN")
check({"RECEIVE DIALGA", "RECEIVE PALKIA"} <= set(m) and "RECEIVE GIRATINA" not in m, f"the other two to choose from: {m}")
run("SINJOH_CABIN", "RECEIVE DIALGA")
check(story.sinjoh_dragons_received() == 2 and ENTRY not in travel("RUINS_OF_ALPH"), "second dragon; closed until all 28")
for f in story.UNOWN_FORMS:
    story.catch_counts[f"201_{f}"] = 1
check(ENTRY in travel("RUINS_OF_ALPH"), "all 28 Unown forms: open for the last one")
run("SINJOH_CABIN", "RECEIVE PALKIA")
check(story.sinjoh_dragons_received() == 2, "Dialga still in the party: Cynthia turns you back")
story.player_team = [mk(493)]  # Dialga deposited
run("SINJOH_CABIN", "RECEIVE PALKIA")
check(story.sinjoh_dragons_received() == 3 and story.inventory.get("LUSTROUS_ORB") == 1, "all three dragons")
check(ENTRY not in travel("RUINS_OF_ALPH"), "nothing left: closed for good")

print("4) Old saves inside the removed areas")
story.current_area_key = "SINJOH_PATHWAYS"
story._migrate_sinnoh_start()
check(story.current_area_key == "SINJOH_CABIN", "moved to the ruins")
print("FAILURES:", fails)
