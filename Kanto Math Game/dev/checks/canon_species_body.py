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

print("2) Johto's swarms (SoulSilver's swarm slots), after the National Pokedex")
from src.world import swarms as _sw, radio as _radio
check(_sw.SWARMS["JOHTO"] == {"DARK_CAVE": 206, "JOHTO_ROUTE_32": ("fish", 211), "JOHTO_ROUTE_34": 280, "JOHTO_ROUTE_35": 193, "JOHTO_ROUTE_38": 209,
                              "JOHTO_ROUTE_44": ("fish", 223), "JOHTO_ROUTE_45": 333, "JOHTO_ROUTE_47": 132, "MT_MORTAR": 183,
                              "KANTO_ROUTE_27": ("surf", 370), "VIOLET_CITY": ("fish", 340)},
      "SoulSilver's whole Johto list (11-22): Dunsparce, Ralts, Yanma, Snubbull, Swablu, Ditto, Marill in the wild; Luvdisc on the water; Qwilfish, Remoraid, Whiscash on any rod")
story.enter_region("JOHTO")
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

print("3) Orre: XD's stones and Colosseum's Plusle")
story.enter_region("ORRE")
_said = []
_show = lambda ls: _said.extend(ls)
gp = next(p for p in _TM["GATEON_PORT"]["rooms"]["house_west"]["people"] if isinstance(p, dict) and p.get("text") == "Eevee expert")
st = _CS(g); g.change_state(st)
for f in [k for k in story.story_flags if k.startswith("xd_eevee_stone")]:
    story.story_flags.pop(f)
_before = {k: story.inventory.get(k, 0) for k in ("WATER_STONE", "THUNDER_STONE", "FIRE_STONE")}
_run_story_event(st, gp["event"], lambda c: True, _show)
for _ in range(60):
    if type(g.current_state).__name__ == "PickListState":
        break
    cur = g.current_state
    if getattr(cur, "dialogue_box", None) is not None and getattr(cur.dialogue_box, "visible", False):
        cur.dialogue_box.advance()
    elif getattr(cur, "npc_active", False):
        cur.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
    frames()
pl = g.current_state
picked = type(pl).__name__ == "PickListState"
if picked:
    pl.pick("WATER_STONE")
again = []
_run_story_event(st, gp["event"], lambda c: True, lambda ls: again.extend(ls))
check(picked and story.inventory.get("WATER_STONE", 0) == _before["WATER_STONE"] + 1 and any("tomorrow" in x for x in again)
      and type(g.current_state).__name__ != "PickListState",
      f"Gateon Port's Eevee expert: pick a stone (Water/Thunder/Fire), then another tomorrow ({again[:1]})")
lab = [o for o in _P["XD_CIPHER_LAB"]["route_menu"] if o.get("text") == "LEAF STONE"]
lib = [o for o in _P["SS_LIBRA"]["route_menu"] if o.get("text") == "FIRE STONE"]
check(lab and lab[0]["event"]["gift_item"] == {"LEAF_STONE": 1} and _TM["XD_CIPHER_LAB"]["figure_floors"].get("LEAF STONE") == 3
      and lib and lib[0]["event"]["gift_item"] == {"FIRE_STONE": 1} and _TM["SS_LIBRA"]["figure_floors"].get("FIRE STONE") == 5,
      "the Cipher Lab's Leaf Stone (B2F) and the S.S. Libra's Fire Stone (Hold 3) lie on their floors")
ch = [o for o in _P["KAMINKO_HOUSE"]["route_menu"] if "CHOBIN" in o["text"]]   # (11-21: XD's third Chobin battle gives it - Orre batch 5b)
check(any(o["event"]["battle"]["rewards"].get("SUN_STONE") == 1 for o in ch), "Chobin hands over his Sun Stone when you beat him")
du = next(p for p in _TM["PYRITE_TOWN"]["rooms"]["duking"]["people"] if isinstance(p, dict) and p.get("text") == "Duking")
story.story_flags.pop("orre_miror_cave", None); story.story_flags.pop("orre_duking_plusle", None)
_said.clear()
_n = len(story.player_team)
_run_story_event(st, du["event"], lambda c: story.story_flags.get(c) if not c.startswith("party") else True, _show)
early = len(story.player_team) == _n
story.story_flags["orre_miror_cave"] = True
_run_story_event(st, du["event"], lambda c: story.story_flags.get(c) if not c.startswith("party") else True, _show)
check(early and len(story.player_team) == _n + 1 and story.player_team[-1].id == 311,
      "Duking gives you Plusle once Miror B. is beaten at Pyrite Cave (not before)")
story.player_team = story.player_team[:_n]

print("4) Orange: the Linking Cord and Tauros")
tro = next(o for o in _P["TROVITOPOLIS"]["explore_options"] if o.get("text") == "Gift clerk")
r60 = _AD[_P["ORANGE_ROUTE_60"]["wild_pool_percentages"]]
check("LINKING_CORD" in tro["stock"] and r60.get("128") and sum(r60.values()) == 100,
      "Trovitopolis's Dept. Store sells the Linking Cord (Alakazam, Machamp, Golem, Gengar); Tauros grazes on Route 60")

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

print("8) Orange: the old pokeorange hack's Gen 2 species back; the dex is only what Orange gives (11-19)")
story.enter_region("ORANGE")
_ost = _AD["REGION_START"]["ORANGE"]
_odex = set(_ost["dex_list"]) | set(_ost["dex_extra"])
check(len(_odex) == 192 and 152 not in _odex and 151 not in _odex and {18, 137, 143, 150, 171, 176, 186, 222, 227, 233, 250, 251} <= _odex,
      f"Orange's dex: everything Orange gives, 192 (Jordan 11-23; no Chikorita or Mew; Pidgeot, Porygon, Snorlax, Mewtwo, Lanturn, Togetic, Politoed, Corsola, Skarmory, Porygon2, Ho-Oh, Celebi in) ({len(_odex)})")
_pm = next(o for o in _P["TROVITOPOLIS"]["explore_options"] if o.get("text") == "Porygon man")
for _f in ("got_porygon_trovitopolis", "got_upgrade_trovitopolis", "beat_orange_champion"):
    story.story_flags.pop(_f, None)
story.inventory.pop("UPGRADE", None)
story.player_team = [mk(25)]
_okp = lambda c: bool(story.story_flags.get(c))
_run_story_event(g.current_state, _pm["event"], _okp, lambda ls: None)
_got_pory = story.player_team[-1].id == 137
_run_story_event(g.current_state, _pm["event"], _okp, lambda ls: None)
_early = story.inventory.get("UPGRADE", 0) == 0
story.story_flags["beat_orange_champion"] = True
_run_story_event(g.current_state, _pm["event"], _okp, lambda ls: None)
check(_got_pory and _early and story.inventory.get("UPGRADE") == 1,
      "Trovitopolis's Porygon man: his Porygon first, then the Up-Grade once you're the Orange Champion (11-19)")
story.player_team = [mk(25)]
_wild_new = {"ORANGE_ROUTE_69": "179", "FIRE_ISLAND": "218", "ORANGE_ROUTE_62": "227", "ORANGE_ROUTE_64": "192"}
check(all(_AD[_P[a]["wild_pool_percentages"]].get(s) and sum(_AD[_P[a]["wild_pool_percentages"]].values()) == 100 for a, s in _wild_new.items())
      and _AD[_P["ORANGE_ROUTE_70"]["surf_pool_percentages"]].get("171"),
      "...wild where the hack had them: Mareep (Route 69), Slugma (Fire Island), Skarmory (Route 62), Sunflora (Route 64), Lanturn (Route 70's water)")
seller = next(p for p in _TM["TROVITOPOLIS"]["rooms"]["roof"]["people"] if isinstance(p, dict) and p.get("text") == "Egg seller")
story.player_team = [mk(25)]
story.money = 1000
story.current_area_key, story.last_area_key = "TROVITOPOLIS", "ORANGE_ROUTE_64"
g.walk_town_pos = None
st = _CS(g); g.change_state(st)


def roof_pick(value):
    said = []
    _run_story_event(st, seller["event"], lambda c: True, lambda ls: said.extend(ls))
    for _ in range(60):
        if type(g.current_state).__name__ == "PickListState":
            break
        cur = g.current_state
        if getattr(cur, "dialogue_box", None) is not None and getattr(cur.dialogue_box, "visible", False):
            cur.dialogue_box.advance()
        elif getattr(cur, "npc_active", False):
            cur.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        frames()
    if type(g.current_state).__name__ == "PickListState":
        g.current_state.pick(value)
    g.change_state(st)
    return said


roof_pick(175)
poor = len(story.player_team) == 1 and story.money == 1000
story.money = 5000
roof_pick(175)
roof_pick(239)
check(poor and [p.id for p in story.player_team][1:] == [175, 239] and story.money == 1000,
      "the Trovitopolis rooftop Egg seller: $2,000 an Egg of your choice, as often as you like (not without the money)")
story.player_team = [mk(25)]
_old = next(p for p in _TM["MIKAN_ISLAND"]["rooms"]["house"]["people"] if isinstance(p, dict) and p.get("text") == "Old man")
story.story_flags.pop("orange_got_tyrogue", None)
_run_story_event(st, _old["event"], lambda c: True, lambda ls: None)
check(story.player_team[-1].id == 236 and getattr(story.player_team[-1], "held_item", None) == "BLACK_BELT",
      "Mikan's old man gives you his Tyrogue (holding a Black Belt), as the hack")
_b = {a: [o for o in _P[a]["route_menu"] if o.get("action") == "BOSS" and o.get("boss", {}).get("id") == s]
      for a, s in (("ORANGE_ROUTE_68", 186), ("ORANGE_ROUTE_50", 250), ("ORANGE_ROUTE_73", 251))}
_on_map = lambda a, txt: any(txt in [p if isinstance(p, str) else p.get("text") for p in (f.get("people") or [])] for f in (_TM[a].get("floors") or [_TM[a]]))
check(all(_b.values()) and _b["ORANGE_ROUTE_50"][0].get("flag_condition") == "beat_orange_champion"
      and _b["ORANGE_ROUTE_73"][0].get("flag_condition") == "beat_orange_champion" and not _b["ORANGE_ROUTE_68"][0].get("flag_condition")
      and _on_map("ORANGE_ROUTE_68", "POLITOED") and _on_map("ORANGE_ROUTE_50", "HO-OH") and _on_map("ORANGE_ROUTE_73", "CELEBI"),
      "Politoed waits on Route 68's shore; Ho-Oh (Routes 50-51) and Celebi (by Tarroco) once you're the Orange Champion")
story.player_team = [mk(25)]

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

print("FAILURES:", fails)
