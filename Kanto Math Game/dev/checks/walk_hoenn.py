
story.badges = {"HOENN": []}
story.inventory = {}
story.story_flags = {"visited_LITTLEROOT_TOWN": True, "hoenn_version": "OMEGA_RUBY"}
story.defeated_trainers = {}
story.starting_region = "HOENN"
R, S = "HOENN", "LITTLEROOT_TOWN"
seen = report("start", S, set())
for b, extra in [("STONE", {}), ("KNuckle", {}), ("DYNAMO", {}), ("HEAT", {}), ("BALANCE", {}),
                 ("FEATHER", {"weather_institute_cleared": True}), ("MIND", {"seafloor_cavern_cleared": True}),
                 ("RAIN", {"cave_of_origin_cleared": True})]:
    badge(R, b)
    story.story_flags.update(extra)
    seen = report(f"{b} badge", S, seen)
story.story_flags["beat_hoenn_champion"] = True
seen = report("champion", S, seen)
print("HMs:", sorted(k for k in story.inventory if k.startswith("HM_")))

# ---- areas expansion (areas_06_hoenn.patch): Gen 3 / ORAS side areas
H_STORY = ["HOENN_MAGMA_HIDEOUT", "HOENN_MIRAGE_TOWER", "HOENN_ALTERING_CAVE", "HOENN_SEA_MAUVILLE", "HOENN_SCORCHED_SLAB", "HOENN_SS_TIDAL"]
H_POST = ["HOENN_SEALED_CHAMBER", "HOENN_DESERT_UNDERPASS", "HOENN_BATTLE_FRONTIER", "HOENN_ARTISAN_CAVE", "HOENN_BATTLE_RESORT",
          "HOENN_SOARING_IN_THE_SKY", "HOENN_MIRAGE_CAVE", "HOENN_MIRAGE_FOREST", "HOENN_MIRAGE_MOUNTAIN", "HOENN_MIRAGE_ISLAND"]
expansion_check("hoenn side areas", H_STORY, S)
gate_check("hoenn post-game side areas", H_POST, S, "beat_hoenn_champion")
expansion_check("hoenn post-game side areas", H_POST, S)
ev = [m for m in PROG["HOENN_SEALED_CHAMBER"]["route_menu"] if m.get("action") == "EVENT"]
st = _state("HOENN_SEALED_CHAMBER")
st.story_event(ev[0]["event"])
print("   OK" if story.story_flags.get("regi_trio_awakened") else "   FAIL", "Sealed Chamber braille sets regi_trio_awakened (Regi BOSS options)")
