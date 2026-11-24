# Rock Smash in a walked town (walk_town._town_smash): on a map with "smash_wild", its cracked rocks stay till you break
# each one by walking into it, and now and then a wild Pokemon from the area's Rock Smash table jumps out (HGSS's Cianwood;
# main cleanup clean-main-johto-town-smash-wild, 11-24).
#   bash dev/checks/run.sh town_smash
from src.states.overworld import CityState
from src.states.overworld import walk_town as _wt

fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.dungeon_routes = True; g.walk_towns = True; g.live3d_headless = True
g.data.save = lambda *a, **k: None
story.enter_region("JOHTO")
story.inventory["HM_ROCK_SMASH"] = 1
story.badges.setdefault("JOHTO", [])
for b in ("Zephyr", "Hive", "Plain", "Fog", "Storm", "Mineral", "Glacier", "Rising"):
    if b not in story.badges["JOHTO"]:
        story.badges["JOHTO"].append(b)
story.current_area_key, story.last_area_key = "CIANWOOD_CITY", None
story.story_flags["visited_CIANWOOD_CITY"] = True
g.walk_town_pos = g.walk_town_room = None
t = CityState(g)
if not hasattr(t, "town_map"):
    print("   (Cianwood isn't walked here)")
else:
    t.town_map["smash_wild"] = True
    t._from_art(t.town_map)
    rocks = [(x, y) for y, row in enumerate(t.grid) for x, c in enumerate(row) if c == "0"]
    check(t._smash_map and len(rocks) >= 2, f"with Rock Smash, Cianwood's cracked rocks stand till broken ({len(rocks)})")

    def beside(r):
        return next(((r[0] - dx, r[1] - dy), (dx, dy)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if 0 <= r[0] - dx < t.w and 0 <= r[1] - dy < t.h and t._open((r[0] - dx, r[1] - dy)))

    was = _wt.WalkTownState.SMASH_WILD
    _wt.WalkTownState.SMASH_WILD = 0.0
    r0 = rocks[0]
    (sx, sy), d = beside(r0)
    t.player, t.anim, t.mode, t.npc_active = (sx, sy), 0, "MAP", False
    t.step(*d)
    check(t.grid[r0[1]][r0[0]] == "." and r0 in t._smashed_here() and t.player == (sx, sy) and g.current_state is not None,
          f"walk into one: it crumbles, and you stay put ({t.grid[r0[1]][r0[0]]})")
    check(t._open(r0), "...where it stood is open ground")

    _wt.WalkTownState.SMASH_WILD = 1.0
    r1 = rocks[1]
    (sx, sy), d = beside(r1)
    t.player, t.anim = (sx, sy), 0
    from src.states.battle import WildBattleState
    t.step(*d)
    b = g.current_state
    check(isinstance(b, WildBattleState) and b.opponent_pokemon.id in (98, 213),
          f"another hides a wild Pokemon from Cianwood's Rock Smash table: Krabby or Shuckle ({type(b).__name__})")
    _wt.WalkTownState.SMASH_WILD = was
    del t.town_map["smash_wild"]
print(f"##### {fails} failures")
