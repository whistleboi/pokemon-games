# Every species in one playthrough: Johto's swarms (split from canon_species 11-23).
#   bash dev/checks/run.sh canon_species_johto
exec(open("dev/checks/canon_species_lib.py", encoding="utf-8").read())

print("2) Johto's swarms (SoulSilver's swarm slots), after the National Pokedex")
from src.world import swarms as _sw, radio as _radio
check(_sw.SWARMS["JOHTO"] == {"DARK_CAVE": 206, "JOHTO_ROUTE_32": ("fish", 211), "JOHTO_ROUTE_34": 280, "JOHTO_ROUTE_35": 193, "JOHTO_ROUTE_38": 209,
                              "JOHTO_ROUTE_44": ("fish", 223), "JOHTO_ROUTE_45": 333, "JOHTO_ROUTE_47": 132, "MT_MORTAR": 183,
                              "KANTO_ROUTE_27": ("surf", 370), "VIOLET_CITY": ("fish", 340)},
      "SoulSilver's whole Johto list (11-22): Dunsparce, Ralts, Yanma, Snubbull, Swablu, Ditto, Marill in the wild; Luvdisc on the water; Qwilfish, Remoraid, Whiscash on any rod")
story.enter_region("JOHTO")
story.current_area_key, story.last_area_key = "JOHTO_ROUTE_43", None   # (in Johto, as a player listening to its radio would be)
_flags = dict(story.story_flags)
story.story_flags.pop("unlocked_national_dex", None)
check(_sw.today(story, "JOHTO") is None, "...none before the National Pokedex")
story.story_flags["unlocked_national_dex"] = True
_real_today = _sw.today
try:
    _sw.today = lambda s, r, day=None: ("KANTO_ROUTE_27", 370) if str(r).upper() == "JOHTO" else None
    surf = _sw.adjust(g, {"72": 60, "90": 30, "129": 10}, "KANTO_ROUTE_27", "surf")
    grass = _sw.adjust(g, {"84": 50, "20": 50}, "KANTO_ROUTE_27", "grass")
    check(surf.get("370", 0) >= 40 and "370" not in grass, f"Route 27's Luvdisc swarm is on the water, not in the grass ({surf.get('370')})")
    story.inventory["RADIO_CARD"] = 1; story.inventory["POKEGEAR"] = 1
    talk = _radio._talk(g)
    check(any("Luvdisc" in x and "Route 27" in x for x in talk), f"...Pokemon Talk tells you ({talk[1:2]})")
    _sw.today = lambda s, r, day=None: ("VIOLET_CITY", 340) if str(r).upper() == "JOHTO" else None
    story.current_area_key = "VIOLET_CITY"
    from src.states.overworld.route_actions import RouteActions as _RA
    pool = _RA._fishing_pool(type("X", (), {"game": g})(), "SUPER_ROD")
    check(pool.get("340", 0) >= 40, f"Violet City's Whiscash swarm bites on a Super Rod ({pool.get('340')})")
    pool = _RA._fishing_pool(type("X", (), {"game": g})(), "OLD_ROD")
    check(pool.get("340", 0) >= 1, f"...and on an Old Rod too (HGSS: any rod) ({pool.get('340')})")
    talk = _radio._talk(g)
    check(any("Whiscash" in x and "fishing line" in x for x in talk), f"...Pokemon Talk says to fish for it ({talk[1:2]})")
    from src.world import phone as _ph
    import datetime as _dt
    _ph.contacts(story)["JOHTO_ROUTE_32|Fisher Ralph"] = 0
    story.story_flags.pop(f"phone_swarm_{_dt.date.today().isoformat()}", None)
    call = _ph.swarm_call(g, "JOHTO")
    check(any("Whiscash" in x and "Violet City" in x for x in call), f"...and a phone friend rings about it, once a day ({call[1:2]})")
    check(_ph.swarm_call(g, "JOHTO") == [], "...not twice the same day")
finally:
    _sw.today = _real_today
story.story_flags = _flags


print(f"##### {fails} failures")
