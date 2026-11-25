story.badges = {"UNOVA": []}
story.inventory = {}
story.story_flags = {"visited_NUVEMA_TOWN": True}
story.defeated_trainers = {}
story.starting_region = "UNOVA"
R, S = "UNOVA", "NUVEMA_TOWN"
seen = report("start", S, set())
steps = [("TRIO", {}, "TRIO"), ("BASIC", {"b2_pop_roxie_back": True}, "BASIC"),   # (Pop Roxie back at Virbank's terminal: his ship to Castelia)
         ("Castelia sewers", {"plasma_castelia_cleared": True, "b2_castelia_arrived": True}, None),   # (and his ship back)
         ("INSECT", {}, "INSECT"), ("BOLT", {}, "BOLT"), ("Relic Castle", {"plasma_relic_castle_cleared": True}, None),
         ("QUAKE", {}, "QUAKE"), ("JET", {"b2_jet_badge": True, "b2_lucky_egg": True}, "JET"), ("Dragonspiral", {"plasma_dragonspiral_cleared": True}, None),
         ("FREEZE", {}, "FREEZE"), ("LEGEND", {}, "LEGEND"), ("champion", {"beat_unova_champion": True}, None)]
for title, flags, b in steps:
    story.story_flags.update(flags)
    if b:
        badge(R, b)
    seen = report(title, S, seen)
print("HMs:", sorted(k for k in story.inventory if k.startswith("HM_")))

# Black City / White Forest (batch 11b, 11-25): one stands between Route 14's and Route 15's Black Gates, your version's
# first, then they swap after each League win (src/world/unova_city.py); after the Hall of Fame, as Black 2.
def bc_check(ok, what):
    print(("    ok   " if ok else "   FAIL ") + what)

print("--- Black City / White Forest")
saved = dict(story.story_flags)
story.story_flags["hall_of_fame_records"] = [{"region": "UNOVA", "team": []}]
seen, _ = reach(S)
bc_check("BLACK_CITY" in seen and "WHITE_FOREST" not in seen, "after the title, Black 2's Black City stands (White Forest not)")
for a in ("UNOVA_ROUTE_14", "UNOVA_ROUTE_15"):
    bc_check("BLACK_CITY" in links(a) and a in links("BLACK_CITY"), f"{a}'s Black Gate <-> Black City")
bc_check("UNOVA_ROUTE_15" not in links("UNOVA_ROUTE_14"), "no Route 14 -> 15 shortcut")
story.story_flags["hall_of_fame_records"] = [{"region": "UNOVA", "team": []}, {"region": "UNOVA", "team": []}]
seen, _ = reach(S)
bc_check("WHITE_FOREST" in seen and "WHITE_FOREST" in links("UNOVA_ROUTE_14") and "WHITE_FOREST" in links("UNOVA_ROUTE_15")
         and "BLACK_CITY" not in links("UNOVA_ROUTE_14"), "after a second League win, White Forest stands there instead")
story.story_flags.pop("beat_unova_champion", None)
pre, _ = reach("UNOVA_ROUTE_14")
bc_check("BLACK_CITY" not in pre and "WHITE_FOREST" not in pre, "neither before the champion (canon: Hall of Fame first)")
story.story_flags.clear(); story.story_flags.update(saved)

# ---- areas expansion (areas_05_unova.patch): B2W2 side areas, BW1 Challenger's Cave
story.story_flags.update(saved)
story.story_flags["beat_unova_champion"] = False
story.story_flags["b2_opelucid_cheren"] = True   # (the story's own gate before Humilau: the Marine Tube opens after Cheren's call, 9a)
B2_EARLY = ["VIRBANK_CITY", "VIRBANK_COMPLEX", "UNOVA_ROUTE_20", "FLOCCESY_RANCH", "FLOCCESY_TOWN", "UNOVA_ROUTE_19", "ASPERTIA_CITY",
            "RELIC_PASSAGE", "TUBELINE_BRIDGE", "LENTIMAS_TOWN", "REVERSAL_MOUNTAIN", "STRANGE_HOUSE",
            "PWT", "PLASMA_FRIGATE", "RELIC_PASSAGE_MIDDLE", "RELIC_PASSAGE_NORTH", "RELIC_CASTLE_DEPTHS",   # (batch 5b, 11-24)
            "VILLAGE_BRIDGE",   # (11-24: on Black 2's story road, Route 12 to Route 11)
            "UNDELLA_BAY",   # (batch 7b: by Surf from Undella, Cheren's HM on Route 6)
            "HUMILAU_CITY", "SEASIDE_CAVE"]   # (batch 9a: by the Marine Tube; the cave from Route 21)
B2_POST = ["NATURE_PRESERVE", "MARVELOUS_BRIDGE",
           "CHALLENGERS_CAVE", "CLAY_TUNNEL", "N_CASTLE"]
expansion_check("unova b2w2 side areas", B2_EARLY, S)
gate_check("unova post-game side areas", B2_POST, S, "beat_unova_champion")
story.story_flags["beat_unova_champion"] = True
story.story_flags["b2_sister_dream"] = True   # (11c: Hugh's sister's dream opens the Zoroark's cave, and Challenger's Cave inside it)
story.story_flags["b2_chasm_done"] = True   # (the League is past the Giant Chasm's end: Route 23 opens then, 9b-2)
expansion_check("unova post-game side areas", B2_POST, S)
