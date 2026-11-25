# The Journal between regions (Journal branch J9, 11-24; kanto_handoff/ROADMAP_JOURNAL.md).
#   bash dev/checks/run.sh journal_regions
# One save through several regions: each region's Quest Book, marker and Feats are its own; a finished region keeps its
# place; the missions that link two regions (assets/journeys_area_data.json, journey_*) show at the right end.
exec(open("dev/checks/quest_book_lib.py", encoding="utf-8").read())


def side():
    return {m["id"] for m in story.get_active_missions() if str(m.get("type")).upper() != "MAIN"}


def tracked():
    return (guide.tracked_mission(g) or {}).get("id")


print("Journeys: the file")
jm = [m for m in jmissions.values() if str(m["id"]).startswith("journey_")]
check(len(jm) >= 3, f"journeys loaded ({[m['id'] for m in jm]})")
check(all(m.get("region") and str(m.get("type")).upper() == "SIDE" for m in jm), "every journey names its region and is a SIDE mission")
check(all((m.get("condition") or {}).get("required_region") == m["region"] for m in jm), "every journey shows only in its own region")

print("Hoenn's Champion: the Delta Episode, then the far islands")
story.current_area_key = "LITTLEROOT_TOWN"
story.badges["HOENN"] = ["STONE", "KNUCKLE", "DYNAMO", "HEAT", "BALANCE", "FEATHER", "MIND", "RAIN"]
flags["beat_hoenn_champion"] = True
for f in ("got_island_tickets", "navel_rock_lugia", "navel_rock_ho_oh", "birth_island_deoxys", "sinjoh_rite_done"):
    flags.pop(f, None)
hoenn_now = now()
check(hoenn_now[0] is not None, f"Hoenn's book has a chapter after the title ({hoenn_now})")
check("journey_hoenn_tickets" in side(), "SIDE: the Lilycove ferry clerk's tickets")
flags["got_island_tickets"] = True
story.inventory["MYSTIC_TICKET"] = story.inventory["AURORA_TICKET"] = 1
check("journey_far_islands" in side() and "journey_hoenn_tickets" not in side(), "SIDE: then the islands beyond the map")
story.tracked_mission = "journey_far_islands"
check(guide.goal_area(g) == "NAVEL_ROCK", f"the marker points at Navel Rock ({guide.goal_area(g)})")
at("NAVEL_ROCK"); flags["border_region"] = "HOENN"
check(story.get_current_region() == "HOENN" and "journey_far_islands" in side(), "on Navel Rock it's still Hoenn's Journal, the islands mission shown")
check(not ({"sevii_m9", "sevii_m10", "sevii_m11"} & side()), "Kanto's own Navel Rock missions don't show in Hoenn's Journal")
for f in ("navel_rock_lugia", "navel_rock_ho_oh", "birth_island_deoxys"):
    flags[f] = True
check("journey_far_islands" not in side(), "done once Lugia, Ho-Oh and Deoxys are caught")
story.tracked_mission = None
story.current_area_key = "LITTLEROOT_TOWN"
feats.note(story, "trainers", 30)
paid = feats.pay(story)
check(any("Battle Hardened" in l for l in paid), "Hoenn's own Feat paid in Hoenn")

print("Mom's move to Johto: a new region, its own book and Feats")
story.move_to_region("JOHTO")
check(story.get_current_region() == "JOHTO", "in Johto after the move")
check(now() == (book["JOHTO"][0]["title"], book["JOHTO"][0]["chapters"][0]["title"]), f"Johto's book starts at its first chapter ({now()})")
check(tracked() == book["JOHTO"][0]["chapters"][0]["mission"], f"the marker follows Johto's first mission ({tracked()})")
check(not any(i.startswith("hoenn_") or i.startswith("journey_") for i in side()), f"no Hoenn missions in Johto's Journal ({sorted(side())[:6]})")
counts = story.feat_counts
check(counts.get("HOENN", {}).get("trainers") == 30 and not counts.get("JOHTO", {}).get("trainers"), "Hoenn's Feat counts stay Hoenn's")
feats.note(story, "trainers", 3)
check(not any("Battle Hardened" in l for l in feats.pay(story)), "Johto's Feats count only Johto's battles (3, no tier yet)")

print("Johto's Champion: Kanto starts as a region of its own, Hoenn keeps its place")
story.badges["JOHTO"] = ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORM", "MINERAL", "GLACIER", "RISING"]
flags["beat_johto_champion"] = True
at("NEW_BARK_TOWN")
check("johto_kanto_travel" in side(), "SIDE: the way to Kanto after Johto's title")
at("PALLET_TOWN")
check(now() == (book["KANTO"][0]["title"], book["KANTO"][0]["chapters"][0]["title"]), f"Kanto's book starts at its beginning ({now()})")
at("LITTLEROOT_TOWN")
check(now() == hoenn_now, f"back in Hoenn, its book is where it was ({now()})")

print("Sinnoh's Champion: the ruins in Johto")
story.current_area_key = "TWINLEAF_TOWN"
flags["beat_sinnoh_champion"] = True
check(story.get_current_region() == "SINNOH" and "journey_sinnoh_sinjoh" in side(), "SIDE in Sinnoh: where the Unown gather")
at("RUINS_OF_ALPH")
check("sinjoh_m1" in side(), "SIDE in Johto: the Sinjoh Ruins, at the Ruins of Alph")
flags["sinjoh_rite_done"] = True
story.current_area_key = "TWINLEAF_TOWN"
check("journey_sinnoh_sinjoh" not in side(), "done once the rite at the Sinjoh Ruins has happened")

print("The giant of the Regis: Hoenn's Regis, Sinnoh's Snowpoint Temple (Jordan 11-24)")
at("LITTLEROOT_TOWN")
flags.pop("SNOWPOINT_TEMPLE_boss_defeated", None)
flags["regi_trio_awakened"] = True
check("journey_regi_giant" in side(), "SIDE in Hoenn after the Regis wake: the giant in the ice")
flags["SNOWPOINT_TEMPLE_boss_defeated"] = True
check("journey_regi_giant" not in side(), "done once Regigigas is beaten in Sinnoh")

print("The GS Ball errand: Oak in Kanto -> Ivy on Valencia -> Kurt -> Ilex Forest (Jordan 11-24)")
for f in ("oak_gs_errand", "got_gs_ball_ivy", "kurt_examined_gs_ball", "ILEX_FOREST_boss_defeated"):
    flags.pop(f, None)
story.inventory.pop("GS_BALL", None)
flags["beat_champion"] = True
at("PALLET_TOWN")
check("journey_gs_oak" in side(), "SIDE in Kanto after the title: Professor Oak's favour")
story.tracked_mission = "journey_gs_oak"
check(guide.goal_area(g) == "PALLET_TOWN", f"the marker points at Pallet Town ({guide.goal_area(g)})")
flags["oak_gs_errand"] = True
check("journey_gs_oak" not in side(), "Oak's part done once he asks")
flags.pop("visited_VALENCIA_ISLAND", None)
check("journey_gs_to_orange" in side(), "SIDE in Kanto then: south by blimp")
story.tracked_mission = "journey_gs_to_orange"
check(guide.goal_area(g) == "VERMILLION_CITY", f"the marker points at Vermilion's harbour ({guide.goal_area(g)})")
story.tracked_mission = None
at("VALENCIA_ISLAND")
flags.pop("orange_ivy_thanks", None)
check("journey_gs_ivy" not in side(), "not before Orange's 'Get Well Soon' step (Ivy can't hand it over yet)")
flags["orange_ivy_thanks"] = True
check("journey_gs_ivy" in side(), "SIDE on Valencia: Professor Ivy's ball")
flags["got_gs_ball_ivy"] = True; story.inventory["GS_BALL"] = 1
check("journey_gs_ivy" not in side(), "Ivy's part done with the GS Ball in the Bag")
check("journey_gs_to_johto" in side(), "SIDE on Valencia then: a craftsman in Johto")
at("PALLET_TOWN")
check("journey_gs_to_azalea" in side() and "journey_gs_to_orange" not in side(), "back in Kanto with the ball: the road to Azalea")
story.tracked_mission = "journey_gs_to_azalea"
_p = guide.path_to(g, "PALLET_TOWN", "AZALEA_TOWN")
check(_p and _p[-1] == "AZALEA_TOWN", f"and the marker has a way there over Kanto's and Johto's roads ({_p})")
story.tracked_mission = None
at("AZALEA_TOWN")
check("journey_gs_kurt" in side() and "journey_gs_shrine" not in side(), "SIDE in Johto: Kurt first")
flags["kurt_examined_gs_ball"] = True
check("journey_gs_shrine" in side(), "then the shrine in Ilex Forest (8 Johto badges)")
flags["ILEX_FOREST_boss_defeated"] = True
check("journey_gs_shrine" not in side(), "done once Celebi has come")
story.tracked_mission = None

print("The ancient pair: Hoenn's Champion hears of Johto's Embedded Tower (Jordan 11-24)")
flags.pop("embedded_rayquaza_defeated", None)
at("LITTLEROOT_TOWN")
check("journey_ancient_pair" in side(), "SIDE in Hoenn after the title: echoes in Johto")
at("NEW_BARK_TOWN")
check("journey_embedded_tower" in side(), "SIDE in Johto after its title: the tower in the cliffs")
story.tracked_mission = "journey_embedded_tower"
check(guide.goal_area(g) == "JOHTO_EMBEDDED_TOWER", f"the marker points at the Embedded Tower ({guide.goal_area(g)})")
story.tracked_mission = None
flags["embedded_rayquaza_defeated"] = True
check("journey_embedded_tower" not in side(), "done once Rayquaza has come")

print("New Feat counts (J6): swarm catches, rematches")
from src.world import swarms as _sw
from src.pokemon import catching as _catching
_real_today = _sw.today
_sw.today = lambda st, region, day=None: ("JOHTO_ROUTE_35", 193) if region == "JOHTO" else None
at("JOHTO_ROUTE_35")
_before = story.feat_counts.get("JOHTO", {}).get("swarm", 0)
_catching.after_catch(g, mk(193), "POKE_BALL")
_catching.after_catch(g, mk(16), "POKE_BALL")
check(story.feat_counts.get("JOHTO", {}).get("swarm", 0) == _before + 1, "a swarm Pokemon caught where it swarms counts; another doesn't")
_sw.today = _real_today
check(any(f["id"] == "swarm" for f in ft["JOHTO"]) and any(f["id"] == "rematches" for f in ft["ORRE"]),
      "Swarm Chaser where a region has swarms; Old Rivals in every region")
check(all(any(f["id"] == "rematches" for f in ft[r]) for r in ft if not r.startswith("_")), "every region has Old Rivals")

print("Pokedex and Type Feats count only Pokemon caught in that region (Jordan 11-24)")
at("NEW_BARK_TOWN")
_dexf = next(f for f in ft["JOHTO"] if f["id"] == "dex")
_jd = sorted(feats._dex_ids(story, "JOHTO"))
_before = feats.value(story, _dexf, "JOHTO")
_h = mk(_jd[0]); _h.caught_region = "HOENN"
story.player_team.append(_h)
check(feats.value(story, _dexf, "JOHTO") == _before, "a Johto-dex species caught in Hoenn doesn't count for Johto")
_j = mk(_jd[1]); _j.caught_region = None
story.player_team.append(_j)
check(feats.value(story, _dexf, "JOHTO") == _before + (0 if _jd[1] in feats.caught_in(story, "JOHTO") - {_jd[1]} else 1)
      and _j.caught_region == "JOHTO", "one with no 'Met in' (a starter, an old save) counts where it's kept now, and is tagged")
story.player_team.remove(_j); story.player_team.remove(_h)
check(_jd[1] in feats.caught_in(story, "JOHTO"), "released or traded away, it still counts where it was caught")

print(f"##### {fails} failures")
