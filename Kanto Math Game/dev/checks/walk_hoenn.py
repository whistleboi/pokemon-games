from src.world.story import StoryManager


# (11-24: the Sailors' and Ferry attendant's sailing - EVENTs with "travel" - is followed by reach_lib.links itself since
#  main 16d55bef; walk_hoenn's own links() wrapper for it is gone)

story.badges = {"HOENN": []}
story.inventory = {}
story.story_flags = {"visited_LITTLEROOT_TOWN": True, "hoenn_version": "OMEGA_RUBY"}
# The ORAS story beats (build_hoenn_story.py) as they happen before each badge.
story.story_flags.update({f: True for f in StoryManager.HOENN_START_FLAGS}, helped_wally=True)
BEATS = {"STONE": ["rusturf_rescued", "met_mr_stone"], "KNUCKLE": ["met_steven", "oceanic_museum_cleared"],
         "DYNAMO": ["defeated_wally_mauville", "got_strength_hoenn", "meteor_falls_cleared", "mt_chimney_boss_defeated"],
         "BALANCE": ["got_mega_bracelet", "weather_institute_cleared", "hoenn_rival_119", "got_starter_mega_stone"],
         "FEATHER": ["got_mt_pyre_orb", "hoenn_rival_lilycove"], "RAIN": ["defeated_wally_victory"]}
HM_GIVERS = {"STONE": ["HM_CUT"], "KNUCKLE": ["HM_FLASH"], "BALANCE": ["HM_SURF"], "MIND": ["HM_DIVE"], "RAIN": ["HM_WATERFALL"]}
story.defeated_trainers = {}
story.starting_region = "HOENN"
R, S = "HOENN", "LITTLEROOT_TOWN"
seen = report("start", S, set())
for b, extra in [("STONE", {}), ("KNUCKLE", {}), ("DYNAMO", {}), ("HEAT", {}), ("BALANCE", {}),
                 ("FEATHER", {"weather_institute_cleared": True}), ("MIND", {"seafloor_cavern_cleared": True}),
                 ("RAIN", {"cave_of_origin_cleared": True})]:
    badge(R, b)
    story.story_flags.update(extra)
    story.story_flags.update({f: True for f in BEATS.get(b, [])})
    if "got_strength_hoenn" in BEATS.get(b, []):
        story.inventory["HM_STRENGTH"] = 1  # the rival's gift on Route 112
    if "defeated_wally_mauville" in BEATS.get(b, []):
        story.inventory["HM_ROCK_SMASH"] = 1  # Wally's uncle, in Mauville (not the Dynamo Badge: 11-06)
    for hm in HM_GIVERS.get(b, []):   # (H5, 11-23: ORAS's givers, not the badges - the Cutter, the hiker, Wally's father, Steven, Wallace)
        story.inventory[hm] = 1
    if "hoenn_rival_119" in BEATS.get(b, []):
        story.inventory["HM_FLY"] = 1  # the rival on Route 119 (not the Feather Badge: 11-06)
    seen = report(f"{b} badge", S, seen)
story.story_flags["beat_hoenn_champion"] = True
seen = report("champion", S, seen)
# (H8, 11-24: every Hoenn SIDE mission's target is reached by the walk after the title - the Soaring legends' own places
#  by a Soaring landing: src/world/soaring.py LEGENDS / KIND_OF)
story.story_flags["wattson_new_mauville_asked"] = True   # (Wattson asks you into New Mauville after the Rain Badge: hoenn_gates)
story.inventory["EON_TICKET"] = 1   # (Wallace's prize here: the boat to Southern Island - hoenn_gates eon_ticket)
seen = report("champion, Wattson's ask, the Eon Ticket", S, seen)
from src.world import soaring as _soar
_fly = set(_soar.LEGENDS) | set(_soar.KIND_OF) | {"HOENN_SOARING_IN_THE_SKY"}
_side = [(m["id"], m.get("target")) for m in g.loader.area_data.get("JOURNAL_MISSIONS", [])
         if str(m.get("id", "")).startswith("hoenn") and str(m.get("type")).upper() == "SIDE" and m.get("target")]
_late = {"HOENN_MAGMA_HIDEOUT"}   # (its door wants the Magma Emblem too: expansion_check walks it below)
_off = [(i, t) for i, t in _side if t not in seen and t not in _fly and t not in _late]
print(("   OK" if not _off else "   FAIL"), f"every Hoenn side mission's place is reached after the title ({len(_side)} with a place; not reached: {_off})")
print("HMs:", sorted(k for k in story.inventory if k.startswith("HM_")))

# ---- areas expansion (areas_06_hoenn.patch): Gen 3 / ORAS side areas
H_STORY = ["HOENN_MAGMA_HIDEOUT", "HOENN_MIRAGE_TOWER", "HOENN_ALTERING_CAVE", "HOENN_SCORCHED_SLAB", "HOENN_SS_TIDAL"]
H_POST = ["HOENN_SEALED_CHAMBER", "HOENN_DESERT_UNDERPASS", "HOENN_BATTLE_FRONTIER", "HOENN_ARTISAN_CAVE"]
# (11-14: the daily Mirage spots are Soaring's, before the Champion as in ORAS: side areas, not post-game ones)
H_STORY += ["HOENN_MIRAGE_CAVE", "HOENN_MIRAGE_FOREST", "HOENN_MIRAGE_MOUNTAIN"]
expansion_check("hoenn side areas", H_STORY, S)
gate_check("hoenn post-game side areas", H_POST, S, "beat_hoenn_champion")
expansion_check("hoenn post-game side areas", H_POST, S)
ev = [m for m in PROG["HOENN_SEALED_CHAMBER"]["route_menu"] if m.get("action") == "EVENT"]
st = _state("HOENN_SEALED_CHAMBER")
st.story_event(ev[0]["event"])
print("   OK" if story.story_flags.get("regi_trio_awakened") else "   FAIL", "Sealed Chamber braille sets regi_trio_awakened (Regi BOSS options)")
