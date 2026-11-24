# Soaring in the Sky's landing places, and the Hoenn work done alongside (11-14): played the way a player meets them.
# The flight itself is the 3D one, with its own suite (soaring3d). Glue after harness_head.py:
#   bash dev/checks/run.sh soaring       (screenshots go to <scratch folder>/soaring_*.png)
import datetime as _dt
import importlib.util as _iu
import json as _json
import random as _r
import pygame
from src.states.overworld import AreaTransitionState
from src.states.overworld.dungeon import DungeonState
from src.states.overworld.soaring3d import Soaring3DState
from src.world import soaring
from src.world import soaring3d as S3

_sp_ = _iu.spec_from_file_location("town_maps_soaring", "dev/builders/town_maps/soaring.py")
town_maps_soaring = _iu.module_from_spec(_sp_); _sp_.loader.exec_module(town_maps_soaring)
MIRAGE_ITEMS, item_text = town_maps_soaring.MIRAGE_ITEMS, town_maps_soaring.item_text

fails = []
AREA = S3.AREA


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


def run_transition(frames=400):
    for _ in range(frames):
        st = g.current_state
        if not isinstance(st, AreaTransitionState):
            return st
        st.dialogue_box.is_finished = True
        st.update()
    return g.current_state


def shot(name):
    g.current_state.draw()
    pygame.image.save(g.screen, os.path.join(S, f"soaring_{name}.png"))


def land(area):
    story.current_area_key = AREA
    g.soaring3d_state = None
    g.change_state(AreaTransitionState(g, area))
    return run_transition()


def placed(st):
    return {i.get("text") for i in st.placed}


def snap(st, name, floor=None):
    if floor is not None:
        st.run.enter_floor(floor)
    st.run.floor.seen = {(x, y) for x in range(st.run.floor.w) for y in range(st.run.floor.h)}
    for _ in range(3):
        st.update()
    shot(name)


def play_out(st, n=60):
    for _ in range(n):
        if g.current_state is not st:
            break
        if st.dialogue_box.visible:
            st.dialogue_box.is_finished = True
            cb, st.dialogue_box.callback = st.dialogue_box.callback, None
            if cb:
                cb()
        st.update()


g.dungeon_routes = True
story.story_flags["hoenn_version"] = "ALPHA_SAPPHIRE"
flags = story.story_flags
_tm = _json.load(open("assets/town_maps.json", encoding="utf-8"))
_sp = g.loader.area_data["STORY_PROGRESSION"]

print("== the 3D flight's landings run the landing rules")
st = object.__new__(Soaring3DState)   # (just its landing: the flight itself is the soaring3d suite's)
st.game, st.rng, st.eon_name, st.mode = g, _r.Random(3), "Latias", "FLY"
story.current_area_key = AREA
for k in [k for k in flags if k.startswith(("mirage_spot_", "mirage_here_"))]:
    flags.pop(k)
st._land_on({"area": "HOENN_MIRAGE_FOREST", "name": "Mirage Forest"})
fi = soaring.DAILY["forest"][2].index(tuple(S3.SPOT_PLACES["HOENN_MIRAGE_FOREST"][2]))
check(flags.get(f"mirage_spot_forest_{fi}") and flags.get("mirage_daily_ready") is not None,
      f"landing on the Mirage Forest: its place ({fi + 1} of 8) and today's hidden item are set")
check(isinstance(g.current_state, AreaTransitionState) and g.current_state.next_area_key == "HOENN_MIRAGE_FOREST", "... and down you go")
run_transition()
check("HOENN_MIRAGE_ISLANDS" in S3.LAND_SPOTS and "HOENN_MIRAGE_ISLAND" not in S3.LAND_SPOTS
      and any((o.get("target_area") or o.get("target")) == "HOENN_MIRAGE_ISLANDS" for o in _sp[AREA]["route_menu"]),
      "the flight's Mirage Island is ORAS's (the Gen 1-3 legends'), not Emerald's on Route 130")
from src.states.battle import legend_back
flags["soaring_dialga"] = True
flags["legend_rematch_soaring_dialga"] = _dt.date.today().toordinal()
check("soaring_dialga" not in S3.bosses(_sp[AREA], flags), "a sky legend beaten today, not caught: not back in the sky yet")
flags["legend_rematch_soaring_dialga"] = _dt.date.today().toordinal() - 1
check("soaring_dialga" in S3.bosses(_sp[AREA], flags), "... the next day: back")
flags.pop("soaring_dialga"); flags.pop("legend_rematch_soaring_dialga")

print("== one legend per visit")
path = soaring.LEGENDS["HOENN_PATHLESS_PLAIN"]
seen, quiet = set(), 0
for i in range(400):
    pick = soaring.roll_visit(story, path, _r.Random(i))
    out = [f for f in path if flags.get(f"mirage_here_{f}")]
    if pick is None:
        quiet += 1
        if out:
            check(False, f"quiet visit but {out} out")
    else:
        seen.add(pick)
        if out != [pick]:
            check(False, f"one legend out, not {out}")
check(seen == set(path), "over many visits each of the three comes out")
check(40 < quiet < 130, f"about one visit in five is quiet ({quiet} of 400)")
flags["mirage_cobalion"] = flags["mirage_terrakion"] = True
check(all(soaring.roll_visit(story, path, _r.Random(i)) in (None, "mirage_virizion") for i in range(50)),
      "caught ones don't come out again")
flags.pop("mirage_cobalion"); flags.pop("mirage_terrakion")

print("== the landing places (walked maps)")
for area, legends in soaring.LEGENDS.items():
    if area == "HOENN_MIRAGE_ISLANDS":
        continue
    pick = next(p for p in (soaring.roll_visit(story, legends, _r.Random(i)) for i in range(20)) if p)
    st = land(area)
    check(isinstance(st, DungeonState), f"{area}: a walked map ({type(st).__name__})")
    if not isinstance(st, DungeonState):
        continue
    arr = _tm[area]["arrive"][AREA]
    check(list(st.run.player) == arr and st.run.index == 0, f"{area}: you land beside your Eon ({st.run.player} vs {arr})")
    seeks = {t for t in placed(st) if t.startswith("SEEK ")}
    want = {next(o["text"] for o in _sp[area]["route_menu"] if (o.get("boss") or {}).get("victory_flag") == pick)}
    check(seeks == want, f"{area}: only this visit's legend is out ({seeks})")
    check("SOAR AWAY" in placed(st), f"{area}: your Eon waits")
    snap(st, area.lower().replace("hoenn_", ""))
    if _tm[area].get("floors"):
        snap(st, area.lower().replace("hoenn_", "") + "_in", 1)
        st.run.enter_floor(0)
    for f in legends:
        flags.pop(f"mirage_here_{f}", None)
    st = land(area)
    check(not any(t.startswith("SEEK ") for t in placed(st)), f"{area}: a quiet visit, nobody at the back")

print("== the Mirage spots' own items")
for kind in ("forest", "cave", "mountain", "island"):
    area = soaring.DAILY[kind][0]
    for i, it in enumerate(MIRAGE_ITEMS[kind]):
        if not it:
            continue
        soaring.mark_place(story, kind, i)
        st = land(area)
        items = {t for t in placed(st) if t[-1].isdigit()}
        check(items == {item_text(kind, i)}, f"{area} place {i + 1}: its own item, {it} ({items})")
    snap(st, f"mirage_{kind}")
    if _tm[area].get("floors"):
        snap(st, f"mirage_{kind}_in", 1)
        st.run.enter_floor(0)

print("== the Mirage Islands: Gen 1-3 legends")
out = {soaring.roll_visit(story, soaring.ISLAND_LEGENDS, _r.Random(i)) for i in range(60)}
check(out - {None} == set(soaring.ISLAND_LEGENDS), "over many visits each of Articuno, Zapdos, Moltres, Mewtwo, Celebi comes out")
for f in soaring.ISLAND_LEGENDS:
    flags.pop(f"mirage_here_{f}", None)
flags["mirage_here_mirage_zapdos"] = True
st = land("HOENN_MIRAGE_ISLANDS")
check({t for t in placed(st) if t.startswith("SEEK ")} == {"SEEK ZAPDOS"}, "Mirage Island: only this visit's legend (Zapdos)")
boss = next(o for o in _sp["HOENN_MIRAGE_ISLANDS"]["route_menu"] if o["text"] == "SEEK MEWTWO")["boss"]
check(boss["id"] == 150 and boss["level"] == 70 and boss["victory_flag"] == "mirage_mewtwo", "Mewtwo at Lv. 70 (FireRed's), its own Hoenn flag")


print("== Hoopa's ring")
def at_ring(area, floor, name, legend_flag):
    for f in soaring.LEGENDS[area]:
        flags.pop(f"mirage_here_{f}", None)
    if legend_flag:
        flags[f"mirage_here_{legend_flag}"] = True
    st = land(area)
    if floor:
        st.run.enter_floor(floor)
    ring = _tm[area]["floors"][floor]["ring"] if _tm[area].get("floors") else _tm[area]["ring"]
    st.run.player = (ring[0], ring[1] + 2)
    st.anim = 0
    for _ in range(200):   # (the place's name fades first)
        st.update()
    st.run.player = (ring[0], ring[1] + 2)
    snap(st, name)
    return st, ring


st, ring = at_ring("HOENN_PATHLESS_PLAIN", 0, "ring_terrakion", "mirage_terrakion")
check(st._ring_spot(st.run.floor) == (), "a legend out: it stands in front of its own ring")
st, ring = at_ring("HOENN_PATHLESS_PLAIN", 0, "ring_quiet", None)
check(st._ring_spot(st.run.floor) == tuple(ring), "a quiet visit: the empty ring floats at the back")
at_ring("HOENN_FABLED_CAVE", 1, "ring_zekrom", "mirage_zekrom")
at_ring("HOENN_CRESCENT_ISLE", 0, "ring_cresselia", "mirage_cresselia")

print("== the daily hidden item")
_d0 = _dt.date(2026, 11, 20)
_seen = {soaring.daily_item(story, "forest", _d0 + _dt.timedelta(d)) for d in range(60)}
check(_seen == {"TINY_MUSHROOM", "BIG_MUSHROOM", "RAZOR_CLAW"}, f"a Mirage Forest's daily item rotates by ORAS's three ({_seen})")
check(soaring.daily_item(story, "cave", _d0) == soaring.daily_item(story, "cave", _d0), "the same item all day")
flags.pop("mirage_daily_day", None)
soaring.new_day_item(story, _d0)
check(flags.get("mirage_daily_ready"), "landing on a new day: the hidden item is there")
st = land("HOENN_CRESCENT_ISLE")
hid = next((m for m in st.run.floor.movers if m.kind == "figure" and m.payload.get("text") == "HIDDEN ITEM"), None)
check(hid is not None, "Crescent Isle: the hidden item lies on the sand")
_before = dict(story.inventory)
if hid is not None:
    st._use_figure(hid)
    play_out(st, 40)
_got = {k for k, v in story.inventory.items() if v > _before.get(k, 0)}
check(_got and _got <= {i for i, _w in soaring.DAILY_ITEMS["crescent"]}, f"picked up: one of Crescent Isle's ({_got})")
check(not flags.get("mirage_daily_ready"), "taken: none more today")
soaring.new_day_item(story, _d0)
check(not flags.get("mirage_daily_ready"), "landing again the same day: still none")
soaring.new_day_item(story, _d0 + _dt.timedelta(1))
check(flags.get("mirage_daily_ready"), "the next day: a new one")

print("== Rock Smash rocks")
story.inventory["HM_ROCK_SMASH"] = 1
story.badges["HOENN"] = list(dict.fromkeys(list(story.badges.get("HOENN", [])) + ["DYNAMO"]))   # (Hoenn H5: Rock Smash needs the Dynamo Badge on the map, ORAS)
st = land("HOENN_MIRAGE_FOREST")
rocks = [t for t, w in st.run.floor.decor.items() if str(w).startswith("crack:")]
check(len(rocks) == 3, f"the Mirage Forest's three cracked rocks stand, even with Rock Smash ({len(rocks)})")
st.SMASH_WILD = 1.0
t = rocks[0]
st.run.player, st.facing = (t[0], t[1] + 1), (0, -1)
st._read_sign()
check(t not in st.run.floor.decor, "facing one with Rock Smash: it breaks")
wild = [m for m in st.run.floor.movers if m.kind == "wild" and (m.x, m.y) == t]
pool = {int(k) for k in g.loader.area_data[_sp["HOENN_MIRAGE_FOREST"]["wild_pool_percentages"]]}
check(wild and int(getattr(wild[0].payload, "meta_id", None) or wild[0].payload.id) in pool, "a wild Pokemon from the forest's own pool jumped out")
check(len([x for x, w in st.run.floor.decor.items() if str(w).startswith("crack:")]) == 2, "the other rocks still stand")
story.inventory.pop("HM_ROCK_SMASH", None)

print("== a beaten legend comes back the next day")
flags["legend_rematch_mirage_kyurem"] = _dt.date.today().toordinal()
check(not legend_back(flags, "mirage_kyurem"), "beaten today, not caught: not back yet")
flags["legend_rematch_mirage_kyurem"] = _dt.date.today().toordinal() - 1
check(legend_back(flags, "mirage_kyurem"), "the next day: back")
flags["legend_rematch_mirage_kyurem"] = True
check(legend_back(flags, "mirage_kyurem"), "an older save's rematch: back now")
flags.pop("legend_rematch_mirage_kyurem")

print("== soaring away from a landing place")
st = land("HOENN_CRESCENT_ISLE")
eon = next(m for m in st.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == "SOAR AWAY")
st._use_figure(eon)
play_out(st)
nxt = run_transition()
check(isinstance(nxt, Soaring3DState), f"talking to your Eon: off you fly ({type(nxt).__name__})")

print("== the wild Pokemon: Bulbapedia's ORAS tables")
_pool = lambda k: g.loader.area_data.get(k) or {}
check({k: v for k, v in _pool("HOENN_ROUTE_101_PERCENTAGES").items() if int(k) < 2000} == {"261": 20, "263": 40, "265": 40},
      "Route 101: Poochyena 20, Zigzagoon 40, Wurmple 40 (ORAS's grass)")
check(_sp["HOENN_ROUTE_119"].get("surf_pool_percentages") and "72" in _pool(_sp["HOENN_ROUTE_119"]["surf_pool_percentages"])
      and "72" not in _pool("HOENN_ROUTE_119_PERCENTAGES"), "Route 119: Tentacool on its water, not in its grass")
check(set(_pool("HOENN_GRANITE_CAVE_ROCK_SMASH_PERCENTAGES")) == {"74", "299"}, "Granite Cave's Rock Smash: Geodude and Nosepass")
check(_pool("HOENN_ROUTE_119_SUPER_ROD_PERCENTAGES"), "Route 119 has its own Super Rod Pokemon")
from src.dungeon import core as _core
st = land("HOENN_ROUTE_119")
_core.CURRENT_TILE = _core.SURF
_m = st._wild_for_pool(_r.Random(2))
_core.CURRENT_TILE = None
check(_m is not None and str(_m.id) in _pool(_sp["HOENN_ROUTE_119"]["surf_pool_percentages"]), f"a wild Pokemon out on Route 119's water is a surfing one ({getattr(_m, 'id', None)})")

print("== Hoenn's TMs: the one list (11-17: Scarlet/Violet's numbers in every region)")
from src.pokemon import tms as _tms
check(_tms.move_of(g, "TM126") == "THUNDERBOLT" and _tms.label(g, "TM126") == "TM126 Thunderbolt", "Thunderbolt is TM126 here too")
_reg = story.get_current_region
story.get_current_region = lambda: "HOENN"
_stock_h = _tms.mart_stock(g, 8)
story.get_current_region = lambda: "KANTO"
_stock_k = _tms.mart_stock(g, 8)
story.get_current_region = _reg
check(_stock_h and _stock_h == _stock_k, "Hoenn's Marts sell the same TMs as Kanto's")
_gifts = set()
for _a, _d in _sp.items():
    if not isinstance(_d, dict) or _d.get("region") != "HOENN":
        continue
    for _o in _d.get("route_menu", []):
        _ev = _o.get("event") if isinstance(_o, dict) else None
        if isinstance(_ev, dict):
            _gifts |= {it for it in (_ev.get("gift_item") or {}) if str(it).startswith(("TM", "HTM"))}
check(_gifts and all(_tms.is_tm(k) for k in _gifts), f"every TM Hoenn's places give is on the one list ({sorted(_gifts)[:6]}...)")
check(_tms.move_of(g, "TM179") == "SMACK-DOWN", "Cozmo's thanks: Smack Down (TM179)")

print("== New Mauville's story (ORAS), in Mauville")
for f in ("wattson_square_talk", "wattson_new_mauville_asked", "new_mauville_checked", "new_mauville_cleared"):
    flags.pop(f, None)
_mv = _tm["MAUVILLE_CITY"]
check(_mv["inside"].get("19,14") == "hills" and _mv["rooms"]["hills"]["title"] == "Mauville Hills", "Mauville Hills: the house by the Mart, its hall inside")
check(any(sc.get("flag") == "wattson_square_talk" and sc.get("condition") == "has_badge:RAIN" for sc in _mv.get("scenes", [])),
      "Wattson walks up in the square once you have the Rain Badge")
from src.states.overworld.town_menu import TownMenu as _TM
_fake = type("F", (), {"game": g})()
_badges = {k: list(v) for k, v in story.badges.items()}
story.badges["HOENN"] = [b for b in story.badges.get("HOENN", []) if "RAIN" not in str(b).upper()]
for k in list(story.badges):
    story.badges[k] = [b for b in story.badges[k] if "RAIN" not in str(b).upper()]
check(not _TM._check_menu_condition(_fake, "has_badge:RAIN"), "no Rain Badge: no Wattson yet")
story.badges["HOENN"].append("RAIN")
check(_TM._check_menu_condition(_fake, "has_badge:RAIN"), "with the Rain Badge: has_badge:RAIN")
story.badges.clear(); story.badges.update(_badges)
st = land("HOENN_NEW_MAUVILLE")
comp = [m for m in st.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == "Security computer"]
check(len(comp) == 1, "New Mauville: the security computer stands where Wattson used to battle")
check(not any(t.get("name") == "Wattson" for t in _sp["HOENN_NEW_MAUVILLE"]["trainer_pool"]), "... and Wattson is at home, not battling there")
if comp:
    st._use_figure(comp[0]); play_out(st, 30)
    check(not flags.get("new_mauville_checked"), "before Wattson's eye scan: access denied")
    flags["wattson_new_mauville_asked"] = True
    st = land("HOENN_NEW_MAUVILLE")
    comp = [m for m in st.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == "Security computer"]
    st._use_figure(comp[0]); play_out(st, 30)
    check(flags.get("new_mauville_checked"), "after it: the security check runs")
    snap(st, "new_mauville")
_hills = _mv["rooms"]["hills"]["people"]
_w = next(p for p in _hills if "any" in p)["any"]
check(_w[1]["event"].get("gift_item") == {"TM126": 1} and _w[1]["event"].get("flag") == "new_mauville_cleared",
      "back in Mauville Hills: Wattson gives TM24 Thunderbolt and the Journal's New Mauville is done")
check(any(p.get("event", {}).get("gift_item") == {"TM060": 1} for p in _hills if isinstance(p, dict) and "event" in p),
      "Mauville Hills' balcony: TM89 U-turn")

from src.states.overworld import CityState
g.walk_towns = True
story.current_area_key, story.last_area_key = "MAUVILLE_CITY", "HOENN_ROUTE_110"
g.walk_town_pos = None
flags["wattson_square_talk"] = True   # (past his walk-up: straight up to the flat)
g.change_state(CityState(g))
for _ in range(3):
    g.current_state.update(); g.current_state.draw()
cs = g.current_state
cs._go("hills", "")
for _ in range(60):
    cs.update()
cs.draw()
check(getattr(cs, "room", None) == "hills", f"through the door by the Mart: into Mauville Hills ({type(cs).__name__}, {getattr(cs, 'room', None)})")
shot("mauville_hills")

print(f"##### {len(fails)} fail")
