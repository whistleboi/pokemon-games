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

# Black City / Black Tower / White Forest (route exit fixes): canon links, the post-game gate and the
# Black Tower unlock for White Forest.
def bc_check(ok, what):
    print(("    ok   " if ok else "   FAIL ") + what)

print("--- Black City / White Forest")
seen, _ = reach(S)
bc_check("BLACK_CITY" in seen and "BLACK_TOWER" in seen and "UNOVA_ROUTE_15" in seen, "Black City, Black Tower and Route 15 open after the champion")
bc_check("WHITE_FOREST" not in seen and "WHITE_TREEHOLLOW" not in seen, "White Forest locked until the Black Tower is cleared")
bc_check("UNOVA_ROUTE_15" not in links("UNOVA_ROUTE_14"), "no Route 14 -> 15 shortcut")
saved = dict(story.story_flags)
story.story_flags.pop("beat_unova_champion", None)
pre, _ = reach("UNOVA_ROUTE_14")
bc_check("BLACK_CITY" not in pre, "Black City shut before the champion (canon: Hall of Fame first)")
story.story_flags.update(saved)
pool = PROG["BLACK_TOWER"]["trainer_pool"]
bc_check(pool[-1].get("is_boss_battle") and pool[-1].get("victory_flag") == "black_tower_cleared", "Black Tower ends on its Area 5 boss, who sets black_tower_cleared")
bc_check(all(bool(t.get("is_boss_battle")) == (i % 2 == 1) for i, t in enumerate(pool)), "gate Trainer then Boss Trainer, area by area")
from src.world import levels as lvmod
st = _state("BLACK_TOWER")
st.show_progression_menu()
texts = [getattr(b, "text", "") for b in st.route_buttons]
bc_check(any("BLACK TOWER" in str(t) for t in texts), "gauntlet button offered in the tower")
team_lv = lvmod.trainer_team_levels(g, "BLACK_TOWER", 3, boss=True)
bc_check(all(lv >= 40 for lv in team_lv), f"boss team scales with the game's levels {team_lv}")
clear_area("BLACK_TOWER")
st = _state("BLACK_TOWER")
st.show_progression_menu()
bc_check(story.story_flags.get("black_tower_cleared"), "clearing every Black Tower trainer sets black_tower_cleared")
seen, _ = reach(S)
bc_check({"WHITE_FOREST", "WHITE_TREEHOLLOW", "BLACK_TOWER_UPPER"} <= seen, "White Forest, the Treehollow and Areas 6-10 open after the Black Tower")
for a, b in (("UNOVA_ROUTE_15", "WHITE_FOREST"), ("UNOVA_ROUTE_14", "BLACK_CITY")):   # (11a: Black 2's Route 14 gate to Black City, Route 15's to White Forest after the Tower; 11b swaps them by League wins)
    bc_check(b in links(a) and a in links(b), f"{a} <-> {b}")

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
           "CHALLENGERS_CAVE", "CLAY_TUNNEL"]
expansion_check("unova b2w2 side areas", B2_EARLY, S)
gate_check("unova post-game side areas", B2_POST, S, "beat_unova_champion")
story.story_flags["beat_unova_champion"] = True
story.story_flags["b2_chasm_done"] = True   # (the League is past the Giant Chasm's end: Route 23 opens then, 9b-2)
expansion_check("unova post-game side areas", B2_POST, S)
