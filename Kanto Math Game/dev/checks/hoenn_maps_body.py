# Hoenn's maps from the Emerald file (11-12): every rebuilt map opened in the game the way a player meets it, its ways
# out and doors, its people, and the story scenes played through. Glue after harness_head.py:
#   cat dev/checks/harness_head.py dev/checks/hoenn_maps_body.py > dev/checks/out/check_hoenn_maps.py
#   python dev/checks/out/check_hoenn_maps.py <scratch folder>
import json
from collections import deque
from src.states.overworld import PlayState, CityState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.states.overworld.dungeon import DungeonState
from src.states.menus import StarterSelectionState as _SSS

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True
story.story_flags["hoenn_version"] = "OMEGA_RUBY"
_tm = json.load(open("assets/town_maps.json", encoding="utf-8"))
_area = g.loader.area_data["STORY_PROGRESSION"]
import importlib.util as _u
_spec = _u.spec_from_file_location("emerald", "dev/builders/town_maps/emerald.py")
_em = _u.module_from_spec(_spec); _spec.loader.exec_module(_em)
BUILT = list(_em.HOENN)


def tap(st, n=600):
    for _ in range(n):
        if getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "dialogue_box", None) is not None and st.dialogue_box.visible:
            st.dialogue_box.advance()
        else:
            return
        st.update(); st.draw()


def frames(n):
    for _ in range(n):
        g.current_state.update(); g.current_state.draw()


def open_map(key, came):
    story.current_area_key, story.last_area_key = key, came
    g.walk_town_pos = None
    st = CityState(g) if _area[key].get("area_type") == "town" else None
    if st is None or not isinstance(st, _WTS):
        st = PlayState(g); g.states["play"] = st
    g.change_state(st)
    frames(2)
    tap(g.current_state)
    return g.current_state


# ---- every rebuilt map: opens on its own map, from each way in, and everything on it can be reached
story.story_flags.update({"received_pokedex_hoenn": True, "helped_wally": True, "hoenn_birch_thanked": True, "hoenn_rival_103": True})
for key in BUILT:
    m = _tm[key]
    a = _area.get(key, {})
    _parts = m["floors"] if m.get("floors") else [m]
    targets = set(v for f in _parts for v in f.get("exits", {}).values())
    known = {o.get("target_area") or o.get("target") for o in a.get("travel_options", []) + a.get("route_menu", []) + a.get("explore_options", [])}
    check(targets <= known, f"{key}: every way out on the map is a way out in the story data {sorted(targets - known)}")
    came = sorted(targets)[0] if targets else key
    st = open_map(key, came)
    is_town = isinstance(st, _WTS)
    w, h = (st.w, st.h) if is_town else (st.run.floor.w, st.run.floor.h)
    _here = _parts[st.run.index] if (not is_town and m.get("floors")) else m
    check((w, h) == (len(_here["art"][0]), len(_here["art"])) and (is_town or isinstance(st, DungeonState)),
          f"{key}: opens on its Emerald map ({w} x {h}, {'town' if is_town else 'route'}), in from {came}")
    grid = _here["art"]
    if m.get("floors"):  # (a place of floors: every passage leads to a tile on a floor that exists)
        _bad = [(i, k, to) for i, f in enumerate(m["floors"]) for k, to in (f.get("links") or {}).items()
                if not (0 <= to[0] < len(m["floors"]) and 0 <= to[2] < len(m["floors"][to[0]]["art"]) and 0 <= to[1] < len(m["floors"][to[0]]["art"][0]))]
        check(not _bad and all(f["art"][int(k.split(",")[1])][int(k.split(",")[0])] == "1" for f in m["floors"] for k in (f.get("links") or {})),
              f"{key}: {len(m['floors'])} floors joined by Emerald's own ladders and passages {_bad[:3]}")
    elif not m.get("parts"):
        walk = set('.="NX!ow$[]{}%_()D<>^vnwu20b:|;,')
        starts = [(x, y) for y, r in enumerate(grid) for x, c in enumerate(r) if c in "<>^vnwu"]
        seen, todo = {starts[0]} if starts else set(), deque(starts[:1])
        while todo:
            x, y = todo.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                t = (x + dx, y + dy)
                if 0 <= t[0] < w and 0 <= t[1] < h and t not in seen and grid[t[1]][t[0]] in walk:
                    seen.add(t); todo.append(t)
        cut = [(x, y, c) for y, r in enumerate(grid) for x, c in enumerate(r) if c in "<>^vnwuDNX" and (x, y) not in seen]
        check(not cut, f"{key}: every way out, door, person and trainer is reachable from the first way out {cut[:4]}")
    texts = [p.get("text") if isinstance(p, dict) else p for f in _parts for p in f.get("people", []) if isinstance(p, (dict, str))]
    check(len(texts) == len(set(texts)), f"{key}: each person has a name of their own")

# ---- story scenes, played as a player meets them
def walk_into(st, way, n=1):
    for _ in range(n):
        st.anim = 0
        st.step(*way)
        frames(STEP_WAIT)


STEP_WAIT = 12
_saved = dict(story.story_flags)

# Route 101: Birch chased by a Poochyena; after the battle he walks up and you go to the lab
for k in ("received_starter_hoenn", "hoenn_birch_rescued", "hoenn_birch_walked_up", "hoenn_birch_thanked"):
    story.story_flags.pop(k, None)
_team = list(story.player_team); story.player_team = []
story.current_area_key, story.last_area_key = "HOENN_ROUTE_101", "LITTLEROOT_TOWN"
p = PlayState(g); g.states["play"] = p; g.change_state(p); frames(2)   # (not tapped through: the opening's lines are still up)
_bars = {t: b.get("look") for t, b in getattr(p, "_bars", {}).items()}
check(_bars.get((9, 13)) == "sheet:em_64.png" and _bars.get((10, 13)) == "mon:261" and _bars.get((7, 14)) == "ow:em:bag",
      f"Route 101: Birch, the Poochyena and his bag stand where Emerald has them {_bars}")


def adv(n, stop):
    for _ in range(n):
        s = g.current_state
        if stop(s):
            return True
        if getattr(s, "dialogue_box", None) is not None and s.dialogue_box.visible:
            s.dialogue_box.advance()
        s.update(); s.draw()
    return False


_s1 = adv(400, lambda s: isinstance(s, _SSS))
if _s1:
    g.current_state.load_starters(); g.current_state.selected_idx = 0; g.current_state.complete_selection()
_s2 = adv(400, lambda s: "Battle" in type(s).__name__)
if _s2:
    g.current_state.player_won = True; g.current_state.exit_battle()
_walk = [False]
def _seen_walker(s):
    _walk[0] = _walk[0] or bool(getattr(s, "_walker", None))
    return story.current_area_key == "LITTLEROOT_TOWN"
_s3 = adv(600, _seen_walker)
check(_s1 and _s2 and _walk[0] and _s3 and story.story_flags.get("hoenn_birch_walked_up"),
      f"Route 101: pick a starter, beat the Poochyena, Birch walks up and you head to Littleroot ({_s1}, {_s2}, {_walk[0]}, {_s3})")
story.story_flags.clear(); story.story_flags.update(_saved); story.player_team = _team or [mk(258)]
story.story_flags["hoenn_version"] = "OMEGA_RUBY"

# Oldale: no Pokedex, west exit: the footprint man walks up, talks, steps you back
story.story_flags.pop("received_pokedex_hoenn", None)
t = open_map("OLDALE_TOWN", "HOENN_ROUTE_101")
home = next(h for h, o in t.people.items() if o.get("text") == "Path to Route 102")
t.player = (2, 10); walk_into(t, (-1, 0))
for _ in range(400):
    if t.npc_active: break
    frames(1)
_talked = t.npc_active
tap(t); frames(150)
check(_talked and t.player == (2, 10) and t.motions[home].pos == home, f"Oldale: the footprint man stops you at the west exit and walks back ({t.player}, {t.motions[home].pos})")
story.story_flags["received_pokedex_hoenn"] = True

# (Oldale's Mart clerk: ORAS's version, below: he runs up as you arrive)

# Route 103: the rival walks up to battle
story.story_flags.pop("hoenn_rival_103", None)
p = open_map("HOENN_ROUTE_103", "OLDALE_TOWN")
rv = next((m for m in p.run.floor.movers if m.kind == "figure" and m.payload.get("action") == "ARRIVAL"), None)
_at = rv and (rv.x, rv.y)
if rv:
    p.run.player = (10, 8)
    adv(300, lambda s: s is not p)
check(_at == (10, 3) and rv and abs(rv.x - 10) + abs(rv.y - 8) == 1 and "Trainer" in type(g.current_state).__name__,
      f"Route 103: the rival waits at Emerald's spot {_at} and walks up to battle")
story.story_flags["hoenn_rival_103"] = True

# Petalburg Woods and Rusturf Tunnel: the Grunt walks up near the Devon researcher / over Peeko
for key, came, near, flag in (("HOENN_PETALBURG_WOODS", "HOENN_ROUTE_104", (23, 18), "petalburg_woods_grunt"),
                             ("HOENN_RUSTURF_TUNNEL", "HOENN_ROUTE_116", (10, 7), "rusturf_grunt_met")):
    story.story_flags.pop(flag, None)
    story.defeated_trainers.pop(key, None)
    p = open_map(key, came)
    p.run.player = near
    _said = []
    for _ in range(600):
        s = g.current_state
        if s is not p: break
        if p.dialogue_box.visible:
            _said.append(" ".join(p.dialogue_box.text_lines)); p.dialogue_box.advance()
        s.update(); s.draw()
    check(any("Grunt" in x for x in _said) and "Trainer" in type(g.current_state).__name__, f"{key}: the Grunt notices you, walks up and battles ({_said[:1]})")

# Petalburg: the guide walks a newcomer to the Pokemon Center
story.story_flags.pop("petalburg_center_tour", None)
t = open_map("PETALBURG_CITY", "HOENN_ROUTE_102")
home = next(h for h, o in t.people.items() if o.get("text") == "Guide")
t.player = (home[0] + 1, home[1]); t.anim = 0; t._talk(home)
_stops = []
for _ in range(1500):
    if t.npc_active:
        _stops.append(t.motions[home].pos)
        t.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
    frames(1)
    if story.story_flags.get("petalburg_center_tour") and not t.scenes.busy(): break
check((20, 17) in _stops, f"Petalburg: the guide takes you to the Pokemon Center ({_stops[:1]})")

# Dewford: Mr. Briney at the pier runs the boats
t = open_map("DEWFORD_TOWN", "HOENN_ROUTE_106")
_br = t._people().get((12, 9))
check(_br is not None and "Boat" in str(_br.get("text")) and (12, 8) in t.barred, f"Dewford: Mr. Briney stands by his boat at the pier and sails you ({_br and _br.get('text')})")

# Granite Cave: Steven in the deepest room where Emerald stands him; down the ladders floor by floor
_gc = _tm["HOENN_GRANITE_CAVE"]["floors"]
check(_gc[0]["art"][8][7] == "N" and "TALK TO STEVEN" in _gc[0]["people"], "Granite Cave: Steven stands in the deepest room at Emerald's spot")
story.current_area_key, story.last_area_key = "HOENN_GRANITE_CAVE", "HOENN_ROUTE_106"
p = PlayState(g); g.states["play"] = p; g.change_state(p); frames(2)
_lad = (35, 3)   # 1F's ladder down (Emerald) -> B1F
p._warp(1, 37, 11); p.run.player = (_lad[0], _lad[1] + 1); p.anim = 0
p.step(0, -1); frames(10); tap(p)
check(p.run.index == 2, f"Granite Cave: 1F's ladder at {_lad} takes you down to B1F (floor {p.run.index})")

# Route 110: through a gatehouse with the Bicycle, up the ramp onto the Cycling Road
_r110 = _tm["HOENN_ROUTE_110"]["floors"]
_gate = {k: v for k, v in _r110[0].get("links", {}).items() if v[0] == 0}
_ramps = {k: v for k, v in _r110[0].get("links", {}).items() if v[0] == 1}
check(len(_gate) == 4 and len(_ramps) >= 2 and any(b.get("item") == "BICYCLE" for b in _r110[0].get("barred", [])),
      f"Route 110: two gatehouses walked through ({len(_gate)} doors), {len(_ramps)} ramps up to the Cycling Road, the Bicycle checked at the gates")

# ---- ORAS story events on the maps (the walkthrough's, 11-12): each played as a player meets it
g.rival_character = g.rival_character or "brendan"


def _play(st, frames=1500):
    said = []
    for i in range(frames):
        s = g.current_state
        if s is not st:
            said.append("<" + type(s).__name__ + ">"); break
        sc = st.scenes if isinstance(st, _WTS) else st._scenes()
        talking = getattr(st, "npc_active", False) or (getattr(st, "dialogue_box", None) is not None and st.dialogue_box.visible)
        if talking:
            box = st.npc_dialogue if getattr(st, "npc_active", False) else st.dialogue_box
            t = " ".join(box.text_lines or [])
            if not said or said[-1] != t:
                said.append(t)
            if getattr(st, "npc_active", False):
                st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            else:
                st.dialogue_box.advance()
        st.update(); st.draw()
        if i > 60 and not sc.busy() and not talking and len(said) > 1:
            break
    return said


def _scene(key, came, flags_on=(), flags_off=(), at=None, step=None):
    for k in flags_on:
        story.story_flags[k] = True
    for k in flags_off:
        story.story_flags.pop(k, None)
    st = open_map(key, came)
    if at is not None:
        if isinstance(st, _WTS):
            st.player = at
            st.scenes.entered = True
        else:
            st.run.player = at
        st.anim = 0
    if step:
        st.step(*step)
    return st, _play(st)


_saved2 = dict(story.story_flags)
st, said = _scene("LITTLEROOT_TOWN", "HOENN_ROUTE_101", ["received_pokedex_hoenn"], ["hoenn_mom_sendoff"], at=(10, 4), step=(0, -1))
check(story.story_flags.get("hoenn_mom_sendoff") and any("Mom:" in x for x in said), f"Littleroot: Mom walks out to see you off once you have the Pokedex ({said[-1:]})")
_nav = story.inventory.pop("POKE_NAV", None)
st, said = _scene("HOENN_ROUTE_101", "LITTLEROOT_TOWN", ["received_pokedex_hoenn", "hoenn_birch_walked_up", "hoenn_birch_rescued", "hoenn_birch_thanked"], ["hoenn_rival_101_tips", "got_dexnav_hoenn"])
check(story.story_flags.get("hoenn_rival_101_tips") and story.inventory.get("POKE_NAV", 0) > 0,
      f"Route 101: your rival catches up with a tip about hidden Pokemon, and hands over the DexNav ({said[:1]})")
_pot = story.inventory.get("POTION", 0)
st, said = _scene("OLDALE_TOWN", "HOENN_ROUTE_101", ["received_pokedex_hoenn"], ["oldale_free_potions"])
check(story.inventory.get("POTION", 0) > _pot, f"Oldale: the Mart clerk runs up as you arrive and hands over Potions ({said[-1:]})")
st, said = _scene("HOENN_ROUTE_102", "OLDALE_TOWN", ["received_pokedex_hoenn"], ["hoenn_rival_102_beautifly"], at=(6, 8))
check(story.story_flags.get("hoenn_rival_102_beautifly"), f"Route 102: your rival catches up to watch the Beautifly")
st, said = _scene("HOENN_PETALBURG_WOODS", "HOENN_ROUTE_104", ["woods_boss_defeated"], ["woods_researcher_left"], at=(24, 18))
check(story.story_flags.get("woods_researcher_left"), "Petalburg Woods: after the battle the researcher heals your team and hurries off")
st, said = _scene("HOENN_ROUTE_104", "HOENN_PETALBURG_WOODS", ["woods_boss_defeated"], ["route104_grunt_report"], at=(10, 28))
check(story.story_flags.get("route104_grunt_report") and any("Grunt" in x for x in said), "Route 104: out of the woods, a Grunt reports to her boss")
st, said = _scene("RUSTBORO_CITY", "HOENN_ROUTE_104", [], ["rustboro_rival_mart", "has_stone_badge"], at=(15, 50))
check(story.story_flags.get("rustboro_rival_mart"), "Rustboro: your rival steps out of the Mart and dashes off to the Gym")
_gb = story.inventory.get("GREAT_BALL", 0)
st, said = _scene("RUSTBORO_CITY", "HOENN_ROUTE_104", ["rusturf_rescued"], ["met_mr_stone", "rustboro_researcher_thanks"], at=(11, 20))
check(story.inventory.get("GREAT_BALL", 0) > _gb, "Rustboro: the researcher waits outside Devon with a Great Ball")
st, said = _scene("HOENN_RUSTURF_TUNNEL", "HOENN_ROUTE_116", ["rusturf_rescued", "rusturf_grunt_met"], ["rusturf_briney_thanks"], at=(13, 5))
check(story.story_flags.get("rusturf_briney_thanks") and any("Peeko" in x for x in said), "Rusturf Tunnel: Mr. Briney runs in to Peeko")
_tm2 = json.load(open("assets/town_maps.json", encoding="utf-8"))
_dew = next(p for p in _tm2["DEWFORD_TOWN"]["people"] if isinstance(p, dict) and p.get("text") == "Fisherman")
_hik = next(p for p in _tm2["HOENN_GRANITE_CAVE"]["floors"][1]["people"] if isinstance(p, dict) and p.get("text") == "Hiker")
check((_dew["event"].get("gift_item") or {}).get("OLD_ROD") and (_hik["event"].get("gift_item") or {}).get("HM_FLASH"),
      "Dewford's fisherman gives the Old Rod; Granite Cave's hiker gives Flash")
_q = [b for b in _tm2["SLATEPORT_CITY"].get("barred", []) if b.get("look") == "sheet:@grunt"]
check(len(_q) == 9, f"Slateport: the villain team's Grunts queue outside the Museum ({len(_q)})")
_inv = {k: story.inventory.pop(k, None) for k in ("CONTEST_PASS", "POKEBLOCK_CASE")}
st, said = _scene("SLATEPORT_CITY", "HOENN_ROUTE_109", ["oceanic_museum_cleared", "slateport_saw_dock"], ["contest_pass_received", "slateport_lisia_met"], at=(17, 6))
check(story.inventory.get("CONTEST_PASS", 0) > 0 and any("Lisia" in x for x in said), f"Slateport: after the Museum, Lisia walks out of the Contest Hall with a Contest Pass ({said[:1]})")
for _k, _v in _inv.items():
    if _v is not None and not story.inventory.get(_k):
        story.inventory[_k] = _v
st, said = _scene("HOENN_ROUTE_110", "SLATEPORT_CITY", ["oceanic_museum_cleared"], ["defeated_rival_110"], at=(34, 58))
check("<TrainerIntroState>" in said, f"Route 110: your rival walks up for a battle ({said[:1]})")
# ---- batch 5: Mauville, Route 117, Verdanturf, Route 111
st, said = _scene("MAUVILLE_CITY", "HOENN_ROUTE_110", ["helped_wally"], ["defeated_wally_mauville"])
check(any("Trainer" in x for x in said if x.startswith("<")),   # (his lines open the battle: the battle's own intro shows them)
      f"Mauville: Wally steps up from the Gym door to battle you, his uncle beside him ({said[:1]})")
story.story_flags["defeated_wally_mauville"] = True
_mv = _tm2["MAUVILLE_CITY"]
check("HOENN_NEW_MAUVILLE" in _mv["exits"].values() and "HOENN_ROUTE_111" in _mv["exits"].values(),
      "Mauville: the east house leads into New Mauville; Route 111 north")
_r111 = _tm2["HOENN_ROUTE_111"]
_dr = [(x, y) for y, r in enumerate(_r111["art"]) for x, c in enumerate(r) if c == "N"]
check((29, 88) in _dr and "HOENN_MIRAGE_TOWER" in _r111["exits"].values() and any(b.get("look") == "storm" for b in _r111.get("barred", [])),
      "Route 111: the Desert Ruins at their door, Mirage Tower in the desert, the sandstorm until the Go-Goggles")
check("daycare" in _tm2["HOENN_ROUTE_117"]["buildings"].values() and len(_tm2["HOENN_ROUTE_117"].get("barred", [])) == 4,
      "Route 117: the Day Care, its Pokemon playing in the yard")
check({"contest", "wally", "center", "mart"} <= set(_tm2["VERDANTURF_TOWN"]["buildings"].values()), "Verdanturf: the Contest Hall, Wally's uncle's house, the Center and Mart")


def _press(st, at, face):
    """Stand at a spot facing a person or sign and press A (towns)."""
    st.player, st.facing, st.anim = at, face, 0
    st.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode="", scancode=0)])
    return _play(st)


# Verdanturf (ORAS): the little girl's lost Shroomish is behind the town sign; she gives the Intriguing Stone, which Mr. Stone trades for the Pidgeotite
for _k in ("verdanturf_shroomish_asked", "verdanturf_shroomish_found", "got_intriguing_stone"):
    story.story_flags.pop(_k, None)
_stone = story.inventory.get("INTRIGUING_STONE", 0)
st = open_map("VERDANTURF_TOWN", "HOENN_ROUTE_117")
st.scenes.entered = True
_press(st, (14, 7), (0, -1))
check(not story.story_flags.get("verdanturf_shroomish_found"), "Verdanturf: the town sign is just a sign until the girl asks for help")
said = _press(st, (14, 16), (0, -1))
check(story.story_flags.get("verdanturf_shroomish_asked") and any("Shroomish" in x for x in said), f"Verdanturf: the little girl has lost her Shroomish near the sign ({said[:1]})")
said = _press(st, (14, 7), (0, -1))
check(story.story_flags.get("verdanturf_shroomish_found") and (13, 15) in st.barred, f"Verdanturf: reading the sign, the Shroomish pops out and hops back beside her ({said[:1]})")
said = _press(st, (14, 16), (0, -1))
check(story.inventory.get("INTRIGUING_STONE", 0) > _stone, f"Verdanturf: she thanks you with the Intriguing Stone ({said[-1:]})")
import json as _json
def _find(d, key):
    if isinstance(d, dict):
        if key in d:
            return d[key]
        for v in d.values():
            r = _find(v, key)
            if r is not None:
                return r
_ms = next(o for o in _find(_json.load(open("assets/hoenn_area_data.json", encoding="utf-8")), "RUSTBORO_CITY")["explore_options"] if o.get("text") == "Mr. Stone")
check(_ms.get("condition") == "has_item:INTRIGUING_STONE" and _ms["event"].get("take_item") == {"INTRIGUING_STONE": 1},
      "Rustboro: Mr. Stone trades the Pidgeotite for the Intriguing Stone")
story.inventory["INTRIGUING_STONE"] = _stone

# Route 111 (ORAS): the Winstrates, four battles in a row out of their door; Victoria gives the Macho Brace
for _k in ("winstrate_asked", "winstrate_victor", "winstrate_victoria", "winstrate_vivi", "winstrate_vicky", "winstrate_brace"):
    story.story_flags.pop(_k, None)
st, said = _scene("HOENN_ROUTE_111", "MAUVILLE_CITY", at=(14, 116), step=(0, -1))
check("<TrainerIntroState>" in said and any("Victor:" in x for x in said), f"Route 111: Victor challenges you to the Winstrate family ({said[:1]})")
for _fl, _who in (("winstrate_victor", "Victoria"), ("winstrate_victoria", "Vivi"), ("winstrate_vivi", "Vicky")):
    st, said = _scene("HOENN_ROUTE_111", "MAUVILLE_CITY", [_fl], at=(13, 116))
    check("<TrainerIntroState>" in said and any(_who + ":" in x for x in said), f"Route 111: {_who} walks out of the house to battle next ({said[:1]})")
_mb = story.inventory.get("MACHO_BRACE", 0)
st, said = _scene("HOENN_ROUTE_111", "MAUVILLE_CITY", ["winstrate_vicky"], at=(13, 116))
check(story.inventory.get("MACHO_BRACE", 0) > _mb, f"Route 111: beat all four and Victoria gives you the Macho Brace ({said[-1:]})")
story.story_flags.clear(); story.story_flags.update(_saved2)

story.story_flags.clear(); story.story_flags.update(_saved)
print(f"##### {len(fails)} failures")
