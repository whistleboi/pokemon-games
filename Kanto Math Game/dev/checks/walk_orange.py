# The Orange reach walk (rewritten 11-17 for the walkable Orange, Jordan's batch 14 answers): which areas a player can get to,
# step by step, from a new Orange game on Valencia. Built places (assets/town_maps.json) are joined by their maps' own ways
# out (edges, doors, cave mouths), once Lapras's Surf is had (every Orange island is across the sea); places not rebuilt yet
# by their menu links (reach_lib.links). The gates ON the walked maps (Tangelo's roads, the storm, Mandarin's hold, the
# whirlpools, the Gyms' stories...) are tried both sides by orange_gates and walked by orange_playthrough, not here.
import json as _json

_TM = _json.load(open("assets/town_maps.json", encoding="utf-8"))
_menu_links = links


def links(area):
    """Menu links, plus (with Surf) a walked map's ways out."""
    out = list(_menu_links(area))
    m = _TM.get(area)
    if m and (PROG.get(area) or {}).get("region") == "ORANGE" and story.inventory.get("HM_SURF"):
        for part in (m.get("floors") or [m]) + list((m.get("rooms") or {}).values()):
            out += [t for t in (part.get("exits") or {}).values() if t in PROG and t != area]
    return out


story.badges = {"ORANGE": []}
story.inventory = {}
story.story_flags = {"visited_VALENCIA_ISLAND": True}
story.defeated_trainers = {}
story.starting_region = "ORANGE"
R, S = "ORANGE", "VALENCIA_ISLAND"
seen = report("start (no partner yet)", S, set())
print("   FAIL" if "ORANGE_ROUTE_49" in seen else "   OK", "Route 49 waits for Professor Ivy's partner")
story.story_flags["received_starter_orange"] = True
seen = report("partner", S, seen)
# (5.7: Valencia's sea routes are surfed; Lapras, 5.7's gift on Tangelo after its rescue scene, brings Surf. Before it, the
#  way on is the airport's parachute jump to Pokemon Park: an event, not a menu way out)
print("   FAIL" if "ORANGE_ROUTE_49" in seen else "   OK", "Route 49 (open sea, 5.7's Route A) waits for Surf")
story.inventory["HM_SURF"] = 1
seen = report("Lapras's Surf", S, seen)
WALKED = sorted(k for k in _TM if (PROG.get(k) or {}).get("region") == "ORANGE")
gone = [k for k in WALKED if k not in seen and k not in ("LAWRENCE_SHIP", "NEW_ISLAND")]   # (batch 23: New Island only by the Hamlin ferry, with the ticket)   # (batch 22: Lawrence III's palace is reached only by the story's beam)
print("   OK" if not gone else "   FAIL", f"every walked Orange place is joined to Valencia by the maps ({len(WALKED)} places) {gone}")
for b in ["CORAL_EYE", "SEA_RUBY", "SPIKE_SHELL", "JADE_STAR"]:   # (the walked Gyms: their badges are given on the maps; no menu gate left)
    badge(R, b)
seen = report("the walked Gyms' badges", S, seen)
# (11-18, batch 18: Kumquat is walked; 5.7 sets no badge gate on Route T west of it, so Route 70 is joined by Kumquat's west edge)
print("   OK" if "ORANGE_ROUTE_70" in seen else "   FAIL", "ORANGE_ROUTE_70 is reached from Kumquat's west edge (5.7: no badge gate)")
# (11-18, batch 20: Pummelo walked; 5.7 sets no League gate on Route W north of it: Tarroco and Hamlin are open before the
#  League, as 5.7's Center visitor says. What waits for the title: the Movie 2000 story's places, below)
POST = []
story.story_flags["beat_orange_champion"] = True
seen = report("champion", S, seen)
ALL = [k for k, a in PROG.items() if isinstance(a, dict) and a.get("region") == "ORANGE"]
NOT_WALKED_TO = {"FIRE_ISLAND", "ICE_ISLAND", "LIGHTNING_ISLAND", "LAWRENCE_SHIP", "NEW_ISLAND"}   # (the Movie 2000 story's places: after the League, by Melody's play;
                                                                                  #  batch 22: Lawrence III's palace has no way in but the story's beam)
missing = [k for k in ALL if k not in seen and k not in NOT_WALKED_TO]
print("   OK" if not missing else "   FAIL", f"every Orange area reachable: {missing}")
