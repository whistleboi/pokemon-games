# Unova batch 7a (11-24): Lentimas Town (Juniper's errand, the Blue Shard tutor, Charge Beam, the plane back), Reversal
# Mountain (the mountainside; the entrance chamber, the main chamber with Bianca walking beside you, its lake / Heatran /
# Undella rooms, the south passage: each version's own layout), the Strange House (its rooms as the furniture moves, the
# ghost girl, the Lunar Wing).
#   bash dev/checks/run.sh unovab7a
import json
from src.states.overworld import CityState, PlayState


fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "nate"
flags = story.story_flags
flags["unova_version"] = "BLACK_2"; story.starting_region = "UNOVA"
NEW = ("LENTIMAS_TOWN", "REVERSAL_MOUNTAIN", "REVERSAL_MOUNTAIN_ENTRY", "REVERSAL_MOUNTAIN_INSIDE", "REVERSAL_MOUNTAIN_SOUTH",
       "STRANGE_HOUSE")
for a in NEW:
    flags["visited_" + a] = True
story.badges["UNOVA"] = ["BASIC", "TOXIC", "INSECT", "BOLT", "QUAKE", "JET"]
for k in ("b2_mom_talk", "b2_jet_badge", "b2_lucky_egg", "b2_lentimas_flight"):
    flags[k] = True
said = []
tmaps = json.load(open("assets/town_maps.json", encoding="utf-8"))
prog = json.load(open("assets/unova_area_data.json", encoding="utf-8"))
SP = prog["STORY_PROGRESSION"]


exec(open("dev/checks/unova_lib.py", encoding="utf-8").read())   # (settle, heard, town, _opts, talk, walked, go: shared, Checks C5)


def where():
    return story.current_area_key, tuple(getattr(getattr(g.current_state, "run", None), "player", None) or getattr(g.current_state, "player", (0, 0)))


print("1) the places: walked; trainers and wild Pokemon from the file; both versions' layouts")
for a in NEW:
    check(a in tmaps, f"{a} is walked")
inside = SP["REVERSAL_MOUNTAIN_INSIDE"]["trainer_pool"]
b2 = [t["name"] for t in inside if t.get("when_flags") == ["unova_version:BLACK_2"]]
w2 = [t["name"] for t in inside if t.get("when_flags") == ["unova_version:WHITE_2"]]
check(len(b2) == 10 and len(w2) == 10, f"the main chamber: Black 2's 10 trainers and White 2's 10 ({len(b2)}, {len(w2)})")
check(len(SP["REVERSAL_MOUNTAIN"]["trainer_pool"]) == 2, "the mountainside's two Cyclists")
for a in ("REVERSAL_MOUNTAIN_ENTRY", "REVERSAL_MOUNTAIN_INSIDE", "REVERSAL_MOUNTAIN_SOUTH"):
    sm = tmaps[a].get("story_maps") or []
    check(SP[a].get("wild_tables") and SP[a].get("phenomena") == "dust" and sm and sm[0]["when"] == ["unova_version:WHITE_2"],
          f"{a}: its wild Pokemon, dust clouds, and White 2's own layout")
check(all(r.get("wild_tables") for r in tmaps["REVERSAL_MOUNTAIN_INSIDE"]["rooms"].values())
      and all(r.get("wild_tables") for r in tmaps["STRANGE_HOUSE"]["rooms"].values()), "the side rooms have their wild Pokemon too")

print("2) Lentimas: Juniper's errand; the Blue Shard tutor; Charge Beam; the plane back")
flags.pop("b2_lentimas_juniper", None)
st = town("LENTIMAS_TOWN", (10, 20)); settle(1500)
check(flags.get("b2_lentimas_juniper") and "Drayden" in heard(), "Juniper: ask Drayden about the legendary dragons")
main = [m["id"] for m in story.get_active_missions() if m["type"] == "MAIN"]
check("b2_m34" in main, f"the Journal: through Reversal Mountain ({main})")
tutor = next(c for o in tmaps["LENTIMAS_TOWN"]["rooms"]["tutor_house"]["people"] for c in _opts(o)
             if isinstance(c, dict) and c.get("text") == "Move Tutor")
check({"ICY-WIND", "DRAGON-PULSE"} <= set(tutor["event"]["tutor"]["choices"]) and len(tutor["event"]["tutor"]["choices"]) == 17,
      "the Blue Shard tutor's 17 moves (Icy Wind, Dragon Pulse for the next Gym)")
st = town("LENTIMAS_TOWN", (6, 5), "tm_house", (0, -1))
talk(st, "Old man by the table")
check(story.inventory.get("TM023", 0) >= 1, "the old man's TM57 Charge Beam (our TM023)")
st = town("LENTIMAS_TOWN", (6, 6), face=(0, -1))
talk(st, "Pilot by the runway"); settle(200)
check(story.current_area_key == "MISTRALTON_CITY", f"the plane back to Mistralton ({story.current_area_key})")

print("3) into Reversal Mountain; Bianca walks with you; out to Undella")
st = town("LENTIMAS_TOWN", (30, 18), face=(1, 0))
st.step(1, 0); settle(150)
if story.current_area_key == "LENTIMAS_TOWN":
    g.current_state.step(1, 0); settle(200)
check(story.current_area_key == "REVERSAL_MOUNTAIN", f"east from Lentimas onto the mountainside ({story.current_area_key})")
ds = walked("REVERSAL_MOUNTAIN", (14, 7))
go(0, -1, 1, 80)
check(where()[0] == "REVERSAL_MOUNTAIN_ENTRY", f"into the entrance chamber ({where()})")
ds = walked("REVERSAL_MOUNTAIN_ENTRY", (20, 4))
go(1, 0, 1, 80)
a, p = where()
check(a == "REVERSAL_MOUNTAIN_INSIDE" and abs(p[0] - 4) + abs(p[1] - 9) <= 2, f"into the main chamber, by its door ({a} {p})")
flags.pop("walk_bianca", None); flags.pop("walk_bianca_met", None); flags.pop("b2_reversal_bianca_met", None)
ds = walked("REVERSAL_MOUNTAIN_INSIDE", (5, 10))
go(1, 0, 1, 900)
check(flags.get("walk_bianca"), "Bianca joins you in the main chamber")
from src.world import walk_partners
check(walk_partners.active(story) == "bianca", "and walks beside you there (she heals you, and battles wild Pokemon with you)")
spots = tmaps["REVERSAL_MOUNTAIN_INSIDE"].get("trainer_spots") or []
check(len(spots) == 10 and "Black Belt Corey" in spots, f"Black 2's chamber: its ten trainers where the file stands them ({len(spots)})")
flags["unova_version"] = "WHITE_2"
from src.states.overworld.walk_town import story_map
w2map = story_map(g, "REVERSAL_MOUNTAIN_INSIDE")
check(w2map is not None and w2map.get("art") == tmaps["REVERSAL_MOUNTAIN_INSIDE"]["story_maps"][0]["map"]["art"]
      and "Battle Girl Chan" in (w2map.get("trainer_spots") or []), "a White 2 player walks White 2's own chamber, its trainers where it stands them")
flags["unova_version"] = "BLACK_2"
flags.pop("b2_reversal_bianca_bye", None)
east = list(tmaps["REVERSAL_MOUNTAIN_INSIDE"]["rooms"]).index("east") + 1
ds = walked("REVERSAL_MOUNTAIN_INSIDE", (2, 4), east); settle(900)
check(flags.get("b2_reversal_bianca_bye") and not walk_partners.walking(story, "bianca"), "the Undella room: Bianca stays to research Heatran")
er = tmaps["REVERSAL_MOUNTAIN_INSIDE"]["rooms"]["east"]
check("UNDELLA_TOWN" in er["exits"].values(), "the Undella room's way out to Undella Town")

print("4) the south passage and the cliffs")
ds = walked("REVERSAL_MOUNTAIN_INSIDE", (8, 56))
go(0, 1, 1, 80)
check(where()[0] == "REVERSAL_MOUNTAIN_SOUTH", f"south from the main chamber into the passage ({where()})")
ds = walked("REVERSAL_MOUNTAIN_SOUTH", (8, 7))
go(1, 0, 1, 80)
a, p = where()
check(a == "REVERSAL_MOUNTAIN" and abs(p[0] - 33) + abs(p[1] - 11) <= 3, f"out onto the east cliff, by the Strange House ({a} {p})")

print("5) the Strange House: the library, the ghost girl, the Lunar Wing")
ds = walked("REVERSAL_MOUNTAIN", (43, 17))
go(0, -1, 1, 80)
check(where()[0] == "STRANGE_HOUSE", f"into the Strange House ({where()})")
rooms = tmaps["STRANGE_HOUSE"]["rooms"]
check({"library", "hall_2", "library_2", "hall_3", "attic", "room_w", "room_e", "room_w2", "room_e2"} <= set(rooms),
      "the house as the furniture moves: two libraries, three halls, the attic, four side rooms")
check(rooms["library"]["exits"].get(">") == "ROOM:hall_2" and rooms["library_2"]["exits"].get(">") == "ROOM:hall_3"
      and rooms["hall_3"]["exits"].get("^") == "ROOM:attic", "library -> the moved hall -> library -> the last hall -> the attic")
flags.pop("b2_sh_ghost_1", None)
names = list(rooms)
ds = walked("STRANGE_HOUSE", (29, 20), names.index("hall_2") + 1); settle(600)
check(flags.get("b2_sh_ghost_1") and "Abra" in heard(), "a ghost girl calls for her family, and fades")
flags.pop("b2_sh_lunar_wing", None)
lw = next(c for o in rooms["attic"]["people"] for c in _opts(o) if isinstance(c, dict) and c.get("text") == "Lunar Wing")
check(lw["event"]["gift_item"] == {"LUNAR_WING": 1}, "the Lunar Wing in the attic")
battles = [c for r in ("room_e", "room_w2") for o in rooms[r]["people"] for c in _opts(o) if isinstance(c, dict) and c.get("event", {}).get("battle")]
check(len(battles) == 2, "Backpacker Boone and Psychic Lynette in the side rooms")

print("6) Heatran, after the Champion")
ht = tmaps["REVERSAL_MOUNTAIN_INSIDE"]["rooms"]["heatran"]
boss = next((c for o in ht["people"] for c in _opts(o) if isinstance(c, dict) and c.get("action") == "BOSS"), None)
check(boss and boss["boss"]["id"] == 485 and "beat_unova_champion" in boss["condition"] and boss["boss"]["victory_flag"] == "reversal_heatran",
      "Heatran in its chamber after the Champion (the side quest's flag)")

for f_ in fails:
    print("  -", f_)
print(f"##### {len(fails)} failures")
