
DECO = [k for k, a in prog.items() if a.get("subregion") == "DECOLORE"]


def exits(area):
    st = state_for(area)
    return [o["text"] for o in prog[area]["route_menu"] if o["action"] == "EXIT"
            and st._check_route_condition(o.get("condition"), False)]


print("1) Getting there")
story.badges = {"UNOVA": ["x"] * 8}
story.story_flags, story.inventory = {}, {}
check("Ferry to the Decolore Islands" not in travel("CASTELIA_CITY"), "before the title: no ferry")
story.story_flags["beat_unova_champion"] = True
check("Ferry to the Decolore Islands" in travel("CASTELIA_CITY"), "Unova Champion: ferry from Castelia")
check(len(DECO) == 11, f"{len(DECO)} Decolore areas")
bad = [(k, o.get("target_area")) for k in DECO for o in prog[k].get("travel_options", []) + prog[k].get("route_menu", [])
       if o.get("target_area") and o["target_area"] not in prog]
check(not bad, f"every link leads somewhere {bad}")
check(not prog["DECOLORE_FERRY"].get("wild_pool_percentages"), "no wild Pokemon on the ferry")
check(exits("DECOLORE_FERRY") == ["Honey Island", "Castelia City"], f"ferry at first: {exits('DECOLORE_FERRY')}")

print("2) The Drives")
run("HONEY_ISLAND", "The Beekeepers' Hives")
run("HONEY_ISLAND", "Search the Scorched Hives")
check(story.inventory.get("BURN_DRIVE") == 1 and "Scalchop Island" in exits("DECOLORE_FERRY"), "Burn Drive opens Scalchop")
run("SCALCHOP_ISLAND", "Plasma at the Shrine")
from src.world import levels
check(lineup(battle_of(g.current_state))[-1] == (530, levels.postgame_cap(story, story.area_region(story.current_area_key)) + 1), f"Plasma Grunts at the shrine (post-game cap) {lineup(battle_of(g.current_state))}")
story.story_flags["decolore_shrine_plasma"] = True
run("SCALCHOP_ISLAND", "Search the Crates")
check(story.inventory.get("DOUSE_DRIVE") == 1 and "Grand Spectrala Island" in exits("DECOLORE_FERRY"), "Douse Drive")
run("GRAND_SPECTRALA_ISLAND", "The Illusion Woods", solve=False)
check(not story.inventory.get("CHILL_DRIVE"), "lost in the illusions: try again")
run("GRAND_SPECTRALA_ISLAND", "The Illusion Woods")
check(story.inventory.get("CHILL_DRIVE") == 1 and "Torom Island" in exits("DECOLORE_FERRY"), "Chill Drive opens Torom")

print("3) Torom Island and Genesect")
st = state_for("TOROM_PEAK")
gen = opt("TOROM_PEAK", "CHALLENGE GENESECT")
check(not st._check_route_condition(gen["condition"], False), "no Genesect before the lab")
run("TOROM_ISLAND", "The Plasma Laboratory")
check(lineup(battle_of(g.current_state))[-1] == (462, levels.postgame_cap(story, story.area_region(story.current_area_key)) + 1), f"Plasma Scientist (post-game cap) {lineup(battle_of(g.current_state))}")
story.story_flags["decolore_lab_cleared"] = True
run("TOROM_ISLAND", "Shut Down the Lab")
st = state_for("TOROM_PEAK")
check(story.inventory.get("SHOCK_DRIVE") == 1 and st._check_route_condition(gen["condition"], False),
      "all four Drives: Genesect on Torom Peak")
story.story_flags["P2_LABORATORY_boss_defeated"] = True
check(not st._check_route_condition(gen["condition"], False), "not twice if beaten at P2 Lab in an old save")
check(not prog["P2_LABORATORY"].get("area_boss"), "P2 Lab's Genesect moved")

print("4) Paladin Tournament")
check("Paladin Island" in exits("DECOLORE_FERRY"), "Paladin Island open after the lab")
story.current_area_key = "PALADIN_ISLAND"
lobby = ow.GymLobbyState(g, None)
g.change_state(lobby)
lobby.challenge_gym()
check(lineup(battle_of(g.current_state))[0] == (508, 62), "round one: Lenora")
story.story_flags["gym_progress_PALADIN_ISLAND"] = 3
lobby = ow.GymLobbyState(g, None)
g.change_state(lobby)
lobby.challenge_gym()
check(lineup(battle_of(g.current_state))[-1] == (637, 68), "final: Alder")

no_traps(DECO)
print("5) Visiting every Decolore area")
for k in DECO:
    try:
        state_for(k)
        for _ in range(3):
            g.current_state.update()
        g.current_state.draw()
    except Exception as e:
        check(False, f"{k}: {type(e).__name__} {e}")
print("FAILURES:", fails)
