# Every species in one playthrough: Hoenn's Safari Zone, Togepi Egg, DexNav, Birch's other starters (split from canon_species 11-23).
#   bash dev/checks/run.sh canon_species_hoenn
exec(open("dev/checks/canon_species_lib.py", encoding="utf-8").read())

print("5) Hoenn: the Safari Zone's water and rocks; Lavaridge's Togepi Egg")
sz = _P["HOENN_SAFARI_ZONE"]
check(sz.get("can_fish") and {"194", "195", "183", "54"} <= set(_AD[sz["surf_pool_percentages"]])
      and "213" in _AD[sz["rock_smash_pool_percentages"]] and _AD.get("HOENN_SAFARI_ZONE_SUPER_ROD_PERCENTAGES"),
      "Safari Zone: Emerald's Surf (Wooper, Quagsire, Marill, Psyduck), rods and Rock Smash (Shuckle)")
lady = next(p for p in _TM["LAVARIDGE_TOWN"]["people"] if isinstance(p, dict) and p.get("text") == "Egg lady")
story.enter_region("HOENN")
for f in ("got_lavaridge_egg", "got_lavaridge_togepi_egg", "cave_of_origin_cleared"):
    story.story_flags.pop(f, None)
story.player_team = [mk(25)]
ok = lambda c: (len(story.player_team) < 6) if c == "party_room" else bool(story.story_flags.get(c))
_run_story_event(st, lady["event"], ok, lambda ls: None)
first = [p.id for p in story.player_team][-1] == 360
_run_story_event(st, lady["event"], ok, lambda ls: None)
not_yet = len(story.player_team) == 2
story.story_flags["cave_of_origin_cleared"] = True
_run_story_event(st, lady["event"], ok, lambda ls: None)
check(first and not_yet and len(story.player_team) == 3 and story.player_team[-1].id == 175,
      "Lavaridge's Egg lady: Wynaut's Egg first, Togepi's once Sootopolis's crisis is over (ORAS)")

print("6) Hoenn's DexNav: hidden Pokemon (ORAS's), Gen 1-3 after Groudon/Kyogre, later ones once you're Champion (11-19)")
from src.world import dexnav as _dn
story.enter_region("HOENN")
story.inventory["POKE_NAV"] = 1
for f in ("cave_of_origin_cleared", "beat_hoenn_champion"):
    story.story_flags.pop(f, None)
check(_dn.pool(g, "HOENN_SAFARI_ZONE") == {} and _dn.pool(g, "HOENN_ROUTE_101") == {}, "nothing hidden before Groudon/Kyogre")
story.story_flags["cave_of_origin_cleared"] = True
sz_pool, r101 = _dn.pool(g, "HOENN_SAFARI_ZONE"), _dn.pool(g, "HOENN_ROUTE_101")
check(set(sz_pool) == {"14", "17"} and r101 == {}, f"after it: the Gen 1-3 ones (Safari: Kakuna, Pidgeotto), not yet Buneary or Route 101's Unova Pokemon ({sorted(sz_pool)})")
story.story_flags["beat_hoenn_champion"] = True
check("427" in _dn.pool(g, "HOENN_SAFARI_ZONE") and {"506", "540", "570"} <= set(_dn.pool(g, "HOENN_ROUTE_101"))
      and "594" in _dn.pool(g, "HOENN_ROUTE_124", "surf"), "as Champion: the later ones too (Buneary; Lillipup, Sewaddle, Zorua; Alomomola surfing)")
_all = set()
for _k, _a in _P.items():
    for _f in ("dexnav_pool_percentages", "dexnav_surf_pool_percentages"):
        if isinstance(_a, dict) and _a.get(_f):
            _all |= set(_AD[_a[_f]])
check(len(_all) >= 57 and {"133", "443", "610", "633", "707"} <= _all, f"ORAS's hidden species, all placed ({len(_all)}: Eevee, Gible, Axew, Deino, Klefki...)")
st = open_route("HOENN_ROUTE_101", "LITTLEROOT_TOWN")
grass = [(x, y) for y in range(st.run.floor.h) for x in range(st.run.floor.w) if st.run.floor.tile(x, y) == _core.GRASS and st.run.floor.walkable(x, y)]
st.run.player = grass[len(grass) // 2]
st.run.floor.movers = [m for m in st.run.floor.movers if m.kind != "wild"]


class _Always:
    @staticmethod
    def random():
        return 0.0

    @staticmethod
    def choice(s):
        return s[0]

    @staticmethod
    def choices(a, weights=None):
        return [a[0]]


st._dexnav = None
_dn.on_step(st, _Always)
spot = (st._dexnav or {}).get("spot")
st.run.player = spot if spot else st.run.player
met = _dn.on_step(st) if spot else False
check(spot and met and st.encounter is not None and st.encounter.payload.id in (506, 540, 570),
      f"on Route 101: a tail in the grass nearby {spot}; creep onto it and the hidden Pokemon is there ({getattr(getattr(st.encounter, 'payload', None), 'name', None)})")
st.encounter = None
story.inventory.pop("POKE_NAV", None)
st._dexnav = None
_dn.on_step(st, _Always)
check(not (st._dexnav or {}).get("spot"), "...and nothing without the DexNav")

print("7) Professor Birch's other starters on Route 101 (ORAS), one from each region")
bi = next(p for p in _TM["HOENN_ROUTE_101"]["people"] if isinstance(p, dict) and p.get("text") == "Professor Birch")
for f in [k for k in story.story_flags if k.startswith("hoenn_birch_")] + ["delta_episode_cleared", "hall_of_fame_twice_hoenn"]:
    story.story_flags.pop(f, None)
story.player_team = [mk(25)]
okc = lambda c: (len(story.player_team) < 6) if c == "party_room" else bool(story.story_flags.get(c))


def birch_pick(value):
    _run_story_event(st, bi["event"], okc, lambda ls: None)
    for _ in range(60):
        if type(g.current_state).__name__ == "PickListState":
            break
        cur = g.current_state
        if getattr(cur, "dialogue_box", None) is not None and getattr(cur.dialogue_box, "visible", False):
            cur.dialogue_box.advance()
        frames()
    if type(g.current_state).__name__ == "PickListState":
        g.current_state.pick(value)
        g.change_state(st)
        return True
    g.change_state(st)
    return False


got = [birch_pick(155)]
check(got[0] and story.player_team[-1].id == 155 and bi["condition"] == "beat_hoenn_champion",
      "after the Hall of Fame: one Johto starter of your choice (Cyndaquil)")
check(not birch_pick(498), "...the Unova ones wait for the Delta Episode")
story.story_flags["delta_episode_cleared"] = True
check(birch_pick(501) and story.player_team[-1].id == 501, "after the Delta Episode: one Unova starter (Oshawott)")
check(not birch_pick(387), "...Sinnoh's wait for a second Hall of Fame")
story.story_flags["hall_of_fame_twice_hoenn"] = True
check(birch_pick(387) and story.player_team[-1].id == 387 and not birch_pick(390),
      "after the second: one Sinnoh starter (Turtwig), and that's all - one from each")
story.player_team = [mk(25)]


print(f"##### {fails} failures")
