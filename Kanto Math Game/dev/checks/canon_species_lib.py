# Shared helpers for the canon_species suites, split by region 11-23 (each suite reads this with exec).
# Every species the source games give in one playthrough (11-19, Jordan: "go through the differences with our game versus canon
# and if we removed or changed sections that affect the player's ability to catch every species or obtain every species in a
# single play through"). What that pass fixed, met the way a player meets it:
#   - fishing on a walked route with the area's own rod table (the old menu's FISH button had been the only way)
#   - Johto's swarms (SoulSilver's, after the National Dex), in the grass, on the water and on the line; Pokemon Talk tells
#   - Orre: XD's stones (Gateon's Eevee expert, a stone a day; Cipher Lab's Leaf Stone; the S.S. Libra's Fire Stone; Chobin's
#     Sun Stone) and Colosseum's Plusle from Duking
#   - Orange: the Linking Cord at Trovitopolis's Dept. Store, Tauros on Route 60
#   - Hoenn: the Safari Zone's water and rocks (Emerald), Lavaridge's second Egg (Togepi, ORAS)
#   bash dev/checks/run_par.sh canon_species
import json as _json
from src.states.overworld import PlayState, CityState as _CS
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.states.overworld.common import _run_story_event
from src.dungeon import core as _core

fails = 0
g.dungeon_routes = True
g.walk_towns = True
_AD = g.loader.area_data
_P = _AD["STORY_PROGRESSION"]
_TM = _json.load(open("assets/town_maps.json", encoding="utf-8"))
_TM = _TM.get("maps", _TM)


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def frames(n=1):
    for _ in range(n):
        g.current_state.update()
        g.current_state.draw()


def open_route(key, came=None):
    story.current_area_key, story.last_area_key = key, came
    g.walk_town_pos = None
    p = PlayState(g)
    g.states["play"] = p
    g.change_state(p)
    frames(3)
    return g.current_state


def shore(st):
    f = st.run.floor
    for y in range(f.h):
        for x in range(f.w):
            if f.walkable(x, y) and f.tile(x, y) not in (_core.WATER, _core.SURF) and \
                    any(f.tile(x + dx, y + dy) in (_core.WATER, _core.SURF) for dx, dy in _core.DIRS):
                return (x, y)
    return None


