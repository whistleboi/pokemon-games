
SIN = [k for k, a in prog.items() if a.get("subregion") == "SINJOH"]
ENTRY = "Follow the Unown (Sinjoh Ruins)"


def menu(area):
    st = state_for(area)
    return [o["text"] for o in prog[area]["route_menu"] if st._check_route_condition(o.get("condition"), False)
            and not (o.get("flag_condition", "").startswith("not ") and story.story_flags.get(o["flag_condition"][4:]))]


print("1) Getting in")
story.badges = {"JOHTO": ["x"] * 8}
story.story_flags, story.inventory, story.catch_counts = {}, {}, {}
story.player_team = [mk(25)]
check(ENTRY not in travel("RUINS_OF_ALPH"), "no Arceus, no Unown: no way in")
story.player_team.append(mk(493))
check(ENTRY not in travel("RUINS_OF_ALPH"), "Arceus alone isn't enough")
for f in story.UNOWN_FORMS[:-1]:
    story.catch_counts[f"201_{f}"] = 1
check(story.unown_forms_caught() == 27 and ENTRY not in travel("RUINS_OF_ALPH"), "27 of 28 Unown: not yet")
story.catch_counts["201_question"] = 1
check(ENTRY in travel("RUINS_OF_ALPH"), "Arceus + all 28 Unown: the Unown lead the way")
state_for("SINJOH_CABIN")
story.player_team = [mk(25)]
check(ENTRY in travel("RUINS_OF_ALPH"), "after a visit: back any time, even without Arceus")
check("Abra's Teleport (Ruins of Alph)" in travel("SINJOH_CABIN"), "Abra Teleports you home")
check(len(SIN) == 4, f"{len(SIN)} Sinjoh areas")
bad = [(k, o.get("target_area")) for k in SIN for o in prog[k].get("travel_options", []) + prog[k].get("route_menu", [])
       if o.get("target_area") and o["target_area"] not in prog]
check(not bad, f"every link leads somewhere {bad}")
no_traps(SIN)

print("2) Phione and the frozen spring")
check("Ruined Pathways" not in travel("SINJOH_CABIN"), "pathways wait for Cynthia")
run("SINJOH_CABIN", "Talk to Cynthia")
check("Ruined Pathways" in travel("SINJOH_CABIN"), "Cynthia: on to the pathways")
run("SINJOH_PATHWAYS", "THE FROZEN SPRING", solve=False)
check(not story.story_flags.get("phione_freed"), "ice seals hold on a wrong answer")
run("SINJOH_PATHWAYS", "THE FROZEN SPRING")
check(story.story_flags.get("phione_freed") and "Mystri Stage" in travel("SINJOH_CABIN"), "Phione freed: Mystri Stage open")
check("489" not in g.loader.area_data["SINNOH_ROUTE_223_PERCENTAGES"], "Phione gone from Route 223")

print("3) The rite")
run("MYSTRI_STAGE", "STEP ONTO THE STAGE")
check(not story.story_flags.get("sinjoh_rite_ready"), "no Arceus in the party: the stage stays silent")
story.player_team = [mk(25), mk(493)]
run("MYSTRI_STAGE", "STEP ONTO THE STAGE")
m = menu("MYSTRI_STAGE")
check({"CALL DIALGA (TIME)", "CALL PALKIA (SPACE)", "CALL GIRATINA (ANTIMATTER)"} <= set(m) and "PHIONE'S FAREWELL" not in m,
      f"choose one of three: {m}")
story.story_flags["sinjoh_palkia"] = True
m = menu("MYSTRI_STAGE")
check(not any(t.startswith("CALL") for t in m) and "PHIONE'S FAREWELL" in m, f"after Palkia: only Phione left {m}")
check("Battle Cynthia" in [o["text"] for o in prog["SINJOH_CABIN"]["explore_options"]
                           if ow.CityState(g)._check_menu_condition(o.get("condition"))], "Cynthia wants a battle")

print("4) Visiting every Sinjoh area")
for k in SIN:
    try:
        state_for(k)
        for _ in range(3):
            g.current_state.update()
        g.current_state.draw()
    except Exception as e:
        check(False, f"{k}: {type(e).__name__} {e}")
print("FAILURES:", fails)
