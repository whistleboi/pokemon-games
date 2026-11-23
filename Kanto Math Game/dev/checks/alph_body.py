# The Ruins of Alph walked in (11-22): SoulSilver's own rooms (kanto_handoff/johto_map_tools/j_alph.py) - the Research Center,
# the four puzzle chambers, their hidden rooms and writing rooms, the hallway and the underground hall - and how they play:
# the slab's slide puzzle drops you into the writing room, the far wall opens for its word, each puzzle calls its own Unown.
#   bash dev/checks/run.sh alph
import json
import random
from src.states.overworld import CityState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.world import alph

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "red"
_tm = json.load(open("assets/town_maps.json", encoding="utf-8")); _tm = _tm.get("maps", _tm)
m = _tm["RUINS_OF_ALPH"]
CH = ("kabuto", "aerodactyl", "omanyte", "hooh")
for c in CH:
    story.story_flags.pop(f"alph_{c}_solved", None); story.story_flags.pop(f"alph_{c}_wall", None)
story.inventory.pop("ESCAPE_ROPE", None); story.inventory.pop("UNOWN_REPORT", None)

print("1) the rooms, each from SoulSilver's own zone")
rooms = m.get("rooms") or {}
want = {"lab", "entrance", "hall"} | set(CH) | {f"{c}_room" for c in CH} | {f"{c}_words" for c in CH}
check(want <= set(rooms), f"every room built {sorted(want - set(rooms))}")
check(all(str((rooms[r].get("roofs") or {}).get("_picture", {}).get("f", "")).startswith("ss_ground/D24R") for r in want if r in rooms),
      "each in SoulSilver's own picture")
ins = m.get("inside") or {}
check(ins.get("20,10") == "kabuto" and ins.get("20,53") == "aerodactyl" and ins.get("9,53") == "omanyte" and ins.get("9,33") == "hooh"
      and ins.get("25,29") == "lab" and ins.get("14,28") == "entrance", f"each door its own room ({ins})")
check(all(len(rooms[f"{c}_room"].get("people") or []) == 4 for c in CH), "each hidden room: its four items (HGSS)")

print("2) walking in: a chamber, its wall, its hidden room")
story.current_area_key, story.last_area_key = "RUINS_OF_ALPH", "JOHTO_ROUTE_36"
g.walk_town_pos = g.walk_town_room = None
t = CityState(g); g.change_state(t)
check(isinstance(t, _WTS), f"the Ruins is a walk-in town ({type(t).__name__})")
t._go("kabuto", "OUT:20,10")
check(t.room == "kabuto" and t._open(t.player), f"in the Kabuto chamber, on its floor ({t.player})")
wall = next(iter(t.barred), None)
check(wall is not None, "the far wall is shut")


def bump_wall():
    t.npc_active = False
    t.player = t.anim_from = (wall[0], wall[1] + 1); t.facing = (0, -1); t.anim = 0
    t._step_tile(0, -1)


bump_wall()
check(not story.story_flags.get("alph_kabuto_wall") and tuple(t.player) == (wall[0], wall[1] + 1), "no Escape Rope: the wall stays shut")
story.inventory["ESCAPE_ROPE"] = 1
bump_wall()
check(story.story_flags.get("alph_kabuto_wall"), "with an Escape Rope: it slides open")
check(story.inventory.get("ESCAPE_ROPE") == 1, "and the rope isn't used up (HGSS)")
t.npc_active = False
t.barred = {k: v for k, v in t.barred.items() if not t._bar_met(v)}
t.player = t.anim_from = (wall[0], wall[1] + 1); t.anim = 0
t._step_tile(0, -1)
check(t.room == "kabuto_room", f"through it: the hidden room ({t.room})")
t._go("kabuto", "ROOM:kabuto_room")

print("3) the slab: the slide puzzle, then the floor gives way")
slab = next(iter(rooms["kabuto"].get("sign_events") or {}), None)
ev = (rooms["kabuto"].get("sign_events") or {}).get(slab) or {}
check(ev.get("action") == "TILE_PUZZLE" and ev.get("panel") == "kabuto", f"the slab is the Kabuto puzzle ({ev.get('text')})")
t.npc_active = False
t._get_callback_for_option(ev)()
pz = g.current_state
check(type(pz).__name__ == "AlphPuzzle" and pz.panel == "kabuto", f"the puzzle opens ({type(pz).__name__})")
pz.on_done(True)
check(g.current_state is t and story.story_flags.get("alph_kabuto_solved"), "solved: back in the ruins, the chamber's flag set")
check(t.room == "kabuto_words" and tuple(t.player) == tuple(rooms["kabuto"]["drop"]["at"]), f"dropped into the writing room ({t.room}, {t.player})")
check(t.npc_active, "and told what the floor says")
check(story.inventory.get("UNOWN_REPORT") == 1, "the first puzzle: the Unown Report (HGSS)")
t.npc_active = False
mat = next(k for k, v in t.exits.items() if v == "ROOM:hall")
t.player = t.anim_from = (mat[0], mat[1] - 1); t.anim = 0
t._step_tile(0, 1)
check(t.room == "hall", f"down into the underground hall ({t.room})")
check(any(v == "ROOM:entrance" and abs(k[0] - t.player[0]) + abs(k[1] - t.player[1]) <= 1 for k, v in t.exits.items()),
      f"by its ladder ({t.player})")

print("4) Unown: only the letters the puzzles have called")
rate = rooms["hall"]["wild"]["rate"]
t.town_map["rooms"]["hall"]["wild"]["rate"] = 1.0
seen = set()
for _ in range(40):
    g.change_state(t); t.anim_from = (0, 0)
    if t._room_wild(t.player):
        b = g.current_state
        seen.add(str(getattr(getattr(b, "opponent_pokemon", None), "form", "?")))
seen = {"a" if f == "normal" else f for f in seen}
check(seen and seen <= set("abcdefghij"), f"after the Kabuto puzzle: A to J only ({sorted(seen)})")
story.story_flags["alph_hooh_solved"] = True
seen = set()
for _ in range(80):
    seen.add(alph.pick(story, None) or "-")
check(seen == set("abcdefghij") | set("wxyz"), f"Ho-Oh's too: W to Z join them ({''.join(sorted(seen))})")
for c in CH:
    story.story_flags.pop(f"alph_{c}_solved", None)
g.change_state(t); t.anim_from = (0, 0)
check(not t._room_wild(t.player), "no puzzle solved: no Unown in the hall")
t.town_map["rooms"]["hall"]["wild"]["rate"] = rate
check(alph.open_forms(story) == set(), "and nothing open")

print("5) the other walls' words")
need = {c: rooms[c]["barred"][0]["on_bump"]["need"] for c in CH}
check(need == {"kabuto": "has_escape_rope", "aerodactyl": "has_item:HM_FLASH", "omanyte": "has_water_stone", "hooh": "party_has:250"},
      f"Escape Rope, Flash, a Water Stone, Ho-Oh ({need})")
story.story_flags.pop("alph_kabuto_wall", None)

print(f"##### FAILURES: {len(fails)}")
