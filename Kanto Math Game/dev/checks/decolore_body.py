import json

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
check(len(DECO) == 17 and len(DECO) <= 35, f"{len(DECO)} Decolore areas (no bigger than Sevii)")
bad = [(k, o.get("target_area")) for k in DECO for o in prog[k].get("travel_options", []) + prog[k].get("route_menu", [])
       if o.get("target_area") and o["target_area"] not in prog]
check(not bad, f"every link leads somewhere {bad}")
check(not prog["DECOLORE_FERRY"].get("wild_pool_percentages"), "no wild Pokemon on the ferry")
check(exits("DECOLORE_FERRY") == ["Honey Island", "Castelia City"], f"ferry at first: {exits('DECOLORE_FERRY')}")

print("2) The islands in the order Ash visits them (Bulbapedia, BW124-BW140)")
ORDER = ["Scalchop Island", "Grand Spectrala Island", "Torom Island", "Pirate Isles", "Wayfarer Island", "Capacia Island",
         "Harvest Island", "Frond Island", "Cave Island", "Paladin Island"]
KEYS = ["SCALCHOP_ISLAND", "GRAND_SPECTRALA_ISLAND", "TOROM_ISLAND", "DECOLORE_PIRATE_ISLES", "WAYFARER_ISLAND", "CAPACIA_ISLAND",
        "HARVEST_ISLAND", "FROND_ISLAND", "CAVE_ISLAND", "PALADIN_ISLAND"]
prev = "HONEY_ISLAND"
for name, key in zip(ORDER, KEYS):
    check(name not in exits("DECOLORE_FERRY"), f"{name} waits for the island before it")
    story.story_flags[f"visited_{prev}"] = True
    check(name in exits("DECOLORE_FERRY"), f"{name} opens")
    prev = key
txt = json.dumps({k: prog[k] for k in DECO})
check("Plasma" not in txt and "Genesect" not in txt, "no villainous team in Decolore (as in the anime)")
from src.pokemon import balance
from src.world import levels
data = g.loader.area_data
pools = [data[prog[k]["wild_pool_percentages"]] for k in DECO if prog[k].get("wild_pool_percentages")]
check(all(int(p) <= 649 for pl in pools for p in pl if p.isdigit()), "wild Pokemon are Gen 5 or earlier")

print("3) Island stories")
for area, text in (("SCALCHOP_ISLAND", "SCALCHOP KING: CADBURY"), ("DECOLORE_PIRATE_ISLES", "BATTLE OFFICER JENNY"),
                   ("WAYFARER_ISLAND", "The Butterfree Migration"), ("CAPACIA_ISLAND", "SEARCHING FOR A WISH: JIRACHI"),
                   ("HARVEST_ISLAND", "BATTLE RODNEY"), ("FROND_ISLAND", "The Deserted Island"), ("CAVE_ISLAND", "BATTLE CLAIR")):
    a = prog[area]
    check(any(o.get("text") == text for o in (a.get("route_menu") or []) + (a.get("explore_options") or [])), f"{area}: {text}")
check("479" in data[prog["TOROM_PEAK"]["wild_pool_percentages"]], "Torom Peak: Rotom")
check(prog["P2_LABORATORY"]["area_boss"]["id"] == 649 and "SHOCK_DRIVE" in prog["P2_LABORATORY"]["area_boss"]["rewards"],
      "Genesect is back at P2 Laboratory, with the four Drives")

print("4) Paladin Tournament")
check("Paladin Island" in exits("DECOLORE_FERRY"), "Paladin Island open after Cave Island")
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
