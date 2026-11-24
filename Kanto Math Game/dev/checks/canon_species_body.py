# Every species in one playthrough (11-19): fishing on walked routes, Kanto's Up-Grade and trades, Jessie & James on the map. Region parts: canon_species_<region>.
#   bash dev/checks/run.sh canon_species
exec(open("dev/checks/canon_species_lib.py", encoding="utf-8").read())

print("1) Fishing on walked routes: any area with its own rod Pokemon (11-19)")
story.player_team = [mk(25)]
for key, region in (("SINNOH_ROUTE_210", "SINNOH"), ("HOENN_ROUTE_104", "HOENN"), ("JOHTO_ROUTE_43", "JOHTO")):
    story.enter_region(region)
    story.story_flags["hoenn_version_chosen"] = True
    story.inventory.pop("OLD_ROD", None); story.inventory.pop("GOOD_ROD", None); story.inventory.pop("SUPER_ROD", None)
    st = open_route(key)
    spot = shore(st) if getattr(st, "run", None) else None
    if spot:
        st.run.player = spot
    no_rod = bool(st._menu_item("FISH")) if spot else True
    story.inventory["SUPER_ROD"] = 1
    with_rod = bool(spot) and bool(st._beside("water")) and bool(st._menu_item("FISH"))
    own = _AD.get(f"{key}_SUPER_ROD_PERCENTAGES")
    check(with_rod and not no_rod and own and st._fishing_pool("SUPER_ROD") == own,
          f"{key}: at the water with a Super Rod you can fish, from its own table (no rod: no FISH) {spot}")
story.inventory.pop("SUPER_ROD", None)


print("9) The Up-Grade in Kanto after the Sevii story (11-19, Jordan: \"Upgrade should be available after Kanto sevii\")")
story.enter_region("KANTO")
_sf = _TM["SILPH_CITY"]["floors"][0]
_sci = next(p for p in _sf["people"] if isinstance(p, dict) and p.get("text") == "Silph scientist")
story.story_flags.pop("network_machine_fixed", None); story.story_flags.pop("got_upgrade_silph", None)
story.inventory.pop("UPGRADE", None)
_ok = lambda c: bool(story.story_flags.get(c))
_run_story_event(st, _sci["event"], _ok, lambda ls: None)
_before = story.inventory.get("UPGRADE", 0)
story.story_flags["network_machine_fixed"] = True
_run_story_event(st, _sci["event"], _ok, lambda ls: None)
check(_before == 0 and story.inventory.get("UPGRADE") == 1 and _TM["SILPH_CITY"]["figure_floors"].get("Silph scientist") == 0,
      "Silph Co. 1F: a scientist gives the Up-Grade once the Network Machine on One Island is fixed (not before)")

print("10) Kanto's trades: FireRed's own (its trade table at 0x26CF8C: nicknames and held items, 11-19)")
_kt = {}
for _k, _a in _P.items():
    if isinstance(_a, dict) and str(_a.get("region", "KANTO")).upper() == "KANTO":
        for _o in (_a.get("explore_options") or []) + (_a.get("route_menu") or []):
            _t = (_o.get("event") or {}).get("trade") if isinstance(_o, dict) else None
            if _t:
                _kt[_t["give"]] = (_t.get("nickname"), _t.get("item"))
check(_kt.get(122) == ("MIMIEN", None) and _kt.get(114) == ("TANGENY", "STARDUST") and _kt.get(29) == ("MS. NIDO", "TINY_MUSHROOM")
      and len([v for v in _kt.values() if v[0]]) == 9, f"FireRed's nine trades with their nicknames (MIMIEN, ZYNX, MS. NIDO...) and Tangeny's Stardust ({len(_kt)})")

print("11) Jessie & James on the map: James, with Jessie and their Meowth as characters of their own (src/world/escorts.py, 11-19)")
from src.world import escorts as _esc
story.enter_region("KANTO")
story.player_team = [mk(25)]
_mm = open_route("MT_MOON", "KANTO_ROUTE_3")
_lead = lambda: next((m for m in _mm.run.floor.movers if m.kind == "trainer" and isinstance(m.payload, tuple)
                      and (m.payload[1] or {}).get("sprite") == "jessie_james.png"), None)
while _lead() is None and _mm.run.index < _mm.run.n_floors - 1:
    _mm._descend()
_esc.sync(_mm)
_L = _lead()
_E = [m for m in _mm.run.floor.movers if m.kind == "escort"]
_near = all(abs(e.x - _L.x) + abs(e.y - _L.y) <= 2 and _mm.run.floor.walkable(e.x, e.y) for e in _E)
check(_L is not None and sorted(e.payload["name"] for e in _E) == ["Jessie", "Meowth"] and _near
      and {e.payload["sheet"] for e in _E} == {"oi_75.png", "mon:52"},
      f"Mt. Moon: James (Orange 5.7's sprite) with Jessie and Meowth each on an open tile beside him ({[(e.payload['name'], e.x, e.y) for e in _E]})")
_was = (_L.x, _L.y)
_L.y += 1
_esc.sync(_mm)
check(any((e.x, e.y) == _was for e in _E), "...when he steps, they follow into his place")
_meow = next(e for e in _E if e.payload["name"] == "Meowth")
_got = []
_orig = _mm._meet_trainer
_mm._meet_trainer = lambda m, spotted=False: _got.append(m)
_mm._handle([("bump", _meow)])
_mm._meet_trainer = _orig
_mm.run.remove(_L)
_esc.sync(_mm)
check(_got and _got[0] is _L and not [m for m in _mm.run.floor.movers if m.kind == "escort"],
      "...walking into Meowth is meeting them; beaten, all three are gone")
story.enter_region("ORANGE")
_og = open_route("MANDARIN_UNDERGROUND", "MANDARIN_NORTH")
_esc.sync(_og)
_gr = [m for m in _og.run.floor.movers if m.kind == "trainer" and isinstance(m.payload, tuple) and (m.payload[1] or {}).get("sprite") == "jessie_james.png"]
from src.states.overworld.dungeon import sprite_map as _spm
check(not [m for m in _og.run.floor.movers if m.kind == "escort"] and _spm(g)["trainers_ORANGE"].get("jessie_james.png") == "oi_49.png"
      and _spm(g)["figures"].get("ORANGE_ROUTE_64:Jessie", {}).get("sheet") == "oi_75.png" and _spm(g)["figures"].get("ORANGE_ROUTE_64:James", {}).get("sheet") == "oi_74.png",
      f"Orange: its Grunts (who borrow the pair's battle picture) walk as 5.7's Grunt, no escorts; Jessie and James are 5.7's own, each a figure ({len(_gr)} Grunts here)")


print(f"##### {fails} failures")
