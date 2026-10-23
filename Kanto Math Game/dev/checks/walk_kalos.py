
story.badges = {"KALOS": []}
story.inventory = {}
story.story_flags = {"visited_VANIVILLE_TOWN": True}
story.defeated_trainers = {}
story.starting_region = "KALOS"
R, S = "KALOS", "VANIVILLE_TOWN"
seen = report("start", S, set())
steps = [("BUG", {}, "BUG"), ("Parfum Palace", {"visited_PARFUM_PALACE": True}, None), ("CLIFF", {}, "CLIFF"),
         ("RUMBLE", {}, "RUMBLE"), ("PLANT", {}, "PLANT"), ("VOLTAGE", {}, "VOLTAGE"), ("FAIRY", {}, "FAIRY"),
         ("PSYCHIC", {}, "PSYCHIC"), ("Flare stopped", {"geosenge_flare_cleared": True}, None),
         ("ICEBERG", {}, "ICEBERG"), ("champion", {"beat_kalos_champion": True}, None)]
for title, flags, b in steps:
    story.story_flags.update(flags)
    if b:
        badge(R, b)
    seen = report(title, S, seen)
print("HMs:", sorted(k for k in story.inventory if k.startswith("HM_")))

# ---- areas expansion (areas_02_kalos.patch)
KALOS_NEW = ["KALOS_ROUTE_20", "KALOS_ROUTE_21", "KALOS_ROUTE_22", "KILOUDE_CITY", "BATTLE_MAISON_KALOS", "AZURE_BAY",
             "SEA_SPIRITS_DEN", "BATTLE_CHATEAU", "LYSANDRE_LABS", "KALOS_POWER_PLANT"]
expansion_check("kalos expansion", KALOS_NEW, S)
gate_check("kiloude gate", ["KILOUDE_CITY", "BATTLE_MAISON_KALOS", "SEA_SPIRITS_DEN", "POKEMON_VILLAGE"], S, "beat_kalos_champion")
print("    ok   " if "POKEMON_VILLAGE" in links("KALOS_ROUTE_20") else "   FAIL ", "Route 20 leads to Pokemon Village")
_b = story.badges["KALOS"]; story.badges["KALOS"] = []
_early, _ = reach(S)
print("    ok   " if "KALOS_ROUTE_22" in _early and "VICTORY_ROAD_KALOS" not in _early else "   FAIL ", "Route 22 open from the start, Victory Road still needs the Iceberg Badge")
story.badges["KALOS"] = _b
