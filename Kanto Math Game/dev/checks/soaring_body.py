# Soaring in the Sky (11-14): the 2D flight on Mega Latios / Latias, played the way a player meets it. Glue after harness_head.py:
#   bash dev/checks/run.sh soaring       (screenshots of the flight go to <scratch folder>/soaring_*.png)
import pygame
import importlib.util as _iu
_sp = _iu.spec_from_file_location("town_maps_soaring", "dev/builders/town_maps/soaring.py")
town_maps_soaring = _iu.module_from_spec(_sp); _sp.loader.exec_module(town_maps_soaring)
sys.modules["town_maps_soaring"] = town_maps_soaring
from src.states.systems import BagState
from src.states.overworld import AreaTransitionState
from src.states.overworld.soaring import SoaringState
from src.world import soaring

fails = []


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


def frames(st, n):
    for _ in range(n):
        st.update()
    st.draw()


def shot(name):
    g.current_state.draw()
    pygame.image.save(g.screen, os.path.join(S, f"soaring_{name}.png"))


def key(st, k, down=True):
    st.handle_events([pygame.event.Event(pygame.KEYDOWN if down else pygame.KEYUP, key=k, mod=0, unicode="")])


def tap(st, pos, up=True):
    st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)])
    if up:
        st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos)])


story.story_flags["hoenn_version"] = "ALPHA_SAPPHIRE"
story.current_area_key = "MOSSDEEP_CITY"
flags = story.story_flags

print("== the Eon Flute")
flags.pop("got_mega_bracelet", None)
story.inventory.pop(soaring.FLUTE, None)
check(not soaring.give_flute(story), "no flute before Southern Island")
flags["got_mega_bracelet"] = True
check(soaring.give_flute(story) and story.inventory.get(soaring.FLUTE) == 1, "a save past Southern Island gets the flute")
bag = BagState(g, g.current_state)
check(bag.usable(soaring.FLUTE), "the flute can be used from the Bag")
check(bag.pocket_of(soaring.FLUTE) == "KEY ITEMS", "the flute is in the Key Items pocket")
flags.pop("beat_hoenn_champion", None)   # (ORAS: the flute works as soon as Steven gives it)
story.current_area_key = "HOENN_GRANITE_CAVE"
check(soaring.flute_block(story) is not None, "no flying from inside a cave")
story.current_area_key = "MOSSDEEP_CITY"
check(soaring.flute_block(story) is None, "before the Champion, it plays in Mossdeep (ORAS)")
g.change_state(bag); bag.use_item(soaring.FLUTE)
check(isinstance(g.current_state, AreaTransitionState), "playing it starts the trip up")
st = run_transition()
check(isinstance(st, SoaringState), f"the trip ends in the flight (got {type(st).__name__})")
check(story.current_area_key == soaring.AREA, "the area is Soaring in the Sky")

print("== the mount and the rider")
check(st.eon_id == 380, "Alpha Sapphire with no Eon in the party: Latias carries you")
check(st.mount_img is not None and st.mount_img.get_width() == 31 * 5, "the Mega Latias back sprite is loaded, 5x")
check(st.rider is not None and st.rider.get_height() < 70, "your trainer's facing-up frame, cut at the waist")
start = soaring.ground_xy((401, 129))
check(abs(st.wx - start[0]) < 2 and abs(st.wy - start[1]) < 2, "you start over Mossdeep City, where you played it")
story.player_team.append(mk(381))
check(soaring.mount(g)[0] == 381, "a Latios in the party carries you instead")
story.player_team.pop()
frames(st, 30)
shot("start")

print("== flying")
st.wilds = []; st.gusts = []; st.next_wild = st.next_gust = 10 ** 6
_spots, st.spots = st.spots, []   # (nothing to land on while the steering is tried)
y0 = st.wy
frames(st, 50)
check(st.wy < y0, "the ground scrolls: you go north")
st.wy = 30.0
frames(st, 40)
check(st.wy > st.GH - 400, "north of the map it loops round (open sea)")
x0 = st.wx


class _Keys(dict):  # (keys held down)
    def __getitem__(self, k):
        return self.get(k, False)


pygame.key.get_pressed = lambda: _Keys({pygame.K_RIGHT: True})
frames(st, 20)
check(st.wx > x0 + 60, "holding Right steers right")
pygame.key.get_pressed = lambda: _Keys()
x0 = st.wx
tap(st, (40, 400), up=False)
frames(st, 20)
check(st.wx < x0 - 60, "a finger held to the left steers left (touch / mouse)")
tap(st, (40, 400))
st.wx = 30.0; frames(st, 2)
check(st.wx >= 60, "you can't fly off the map's side")
st.wx = 900.0
key(st, pygame.K_UP); key(st, pygame.K_UP)
frames(st, 40)
check(st.speed > 5.5, "Up twice: flying fast")
key(st, pygame.K_DOWN); key(st, pygame.K_DOWN)
frames(st, 60)
check(st.speed < 2.6, "Down: slow")
tap(st, st._fast_rect().center, up=False)
frames(st, 40)
check(st.speed > 5.5, "holding FAST speeds up")
tap(st, st._fast_rect().center)
key(st, pygame.K_UP)

print("== gusts")
st.gusts = [{"x": st.wx, "y": st.wy - 10, "push": 12.0, "hit": False}]
x0 = st.wx
frames(st, 6)
check(st.gusts and st.gusts[0]["hit"] and abs(st.wx - x0) > 20, "a gust knocks you aside")
st.gusts = []

# a busy sky, for the screenshot: a Swablu and a Wingull crossing, a gust ahead, clouds, the first black cloud
team0 = list(story.player_team)
story.player_team = [mk(351)] + team0
st.spots = [s for s in soaring.spots(story) if s["key"] == "storm1"]
sx, sy = st.spots[0]["at"]
st.wx, st.wy = float(sx + 40), float(sy + 330)
st.wilds = [{"pid": 333, "x": st.wx - 260, "y": st.wy - 150, "vx": 0.0, "vy": 0.0, "ph": 0},
            {"pid": 278, "x": st.wx + 300, "y": st.wy - 60, "vx": 0.0, "vy": 0.0, "ph": 2}]
st.gusts = [{"x": st.wx + 120, "y": st.wy - 260, "push": 0.0, "hit": True}]
st.clouds = [{"x": st.wx - 560, "y": st.wy - 420, "w": 300, "h": 150, "seed": 4, "alpha": 170, "drift": 0},
             {"x": st.wx + 260, "y": st.wy + 20, "w": 240, "h": 120, "seed": 9, "alpha": 150, "drift": 0}]
st.t = 12
shot("sky")
story.player_team = team0
st.wilds, st.gusts, st.clouds = [], [], []

print("== the spots")
st.spots = _spots
by = {s["key"]: s for s in st.spots}
check("daily" in by and by["daily"]["kind"] == "land", "today's Mirage spot is out")
check("crescent" in by, "Crescent Isle is always out")
check("pathless" in by, "the Pathless Plain is always out (no EV condition)")
for k in ("nameless", "fabled", "gnarled", "trackless", "rift1", "rift2", "storm1", "storm2"):
    check(k not in by, f"{k}: hidden without its party")
kinds = {soaring.daily(story, __import__("datetime").date(2026, 11, d))[0] for d in range(1, 29)}
check(kinds == set(soaring.DAILY_KINDS), "the daily spot is each kind on some day")
check(soaring.daily(story) == soaring.daily(story), "the same spot all day")
team = list(story.player_team)
story.player_team = [mk(480), mk(481), mk(482)]
check(any(s["key"] == "rift1" for s in soaring.spots(story)), "Uxie, Mesprit and Azelf: the first rift opens")
story.player_team = [mk(351)]
check(any(s["key"] == "storm1" for s in soaring.spots(story)), "Castform: the first black cloud")
lv = mk(260); lv.level = 100
story.player_team = [lv]
check(any(s["key"] == "fabled" for s in soaring.spots(story)), "a Lv. 100 Pokemon: the Fabled Cave")
story.player_team = [mk(249)]
check(any(s["key"] == "trackless" for s in soaring.spots(story)), "Ho-Oh: the Trackless Forest")
fr = [mk(260), mk(261), mk(262)]
for p in fr:
    p.friendship = 5
story.player_team = fr
check(any(s["key"] == "nameless" for s in soaring.spots(story)), "three friendly Pokemon: the Nameless Cavern")
story.player_team = team
flags["mirage_cresselia"] = True
check(not next(s for s in soaring.spots(story) if s["key"] == "crescent")["beacon"], "Cresselia caught: no beacon")
flags.pop("mirage_cresselia")

print("== one legend per visit")
import random as _r
path = next(s for s in soaring.FIXED if s["key"] == "pathless")
seen, quiet = set(), 0
for i in range(400):
    pick = soaring.roll_visit(story, path, _r.Random(i))
    out = [f for f in path["legends"] if flags.get(f"mirage_here_{f}")]
    if pick is None:
        quiet += 1
        check(not out, "a quiet visit: no legend out") if not out else check(False, f"quiet visit but {out} out")
    else:
        seen.add(pick)
        if out != [pick]:
            check(False, f"one legend out, not {out}")
check(seen == set(path["legends"]), "over many visits each of the three comes out")
check(40 < quiet < 130, f"about one visit in five is quiet ({quiet} of 400)")
flags["mirage_cobalion"] = flags["mirage_terrakion"] = True
check(all(soaring.roll_visit(story, path, _r.Random(i)) in (None, "mirage_virizion") for i in range(50)),
      "caught ones don't come out again")
flags.pop("mirage_cobalion"); flags.pop("mirage_terrakion")

print("== landing on a spot")
cres = by["crescent"]
st.wx, st.wy = float(cres["at"][0]), float(cres["at"][1] + 90)
st.skip = set(); st.mode = "FLY"
for _ in range(60):
    st.update()
    if st.mode == "ASK":
        break
check(st.mode == "ASK" and st.ask[0]["key"] == "crescent", "over Crescent Isle you're asked to land")
shot("crescent")
key(st, pygame.K_ESCAPE)
check(st.mode == "FLY" and "crescent" in st.skip, "FLY ON: you fly on past it")
frames(st, 3)
check(st.mode == "FLY", "... and it doesn't ask again while you're over it")
st.skip = set(); st.wy = cres["at"][1] + 40; st.mode = "FLY"
for _ in range(30):
    st.update()
    if st.mode == "ASK":
        break
tap(st, st.ask[1][0][0].center)
t = run_transition()
check(story.current_area_key == "HOENN_CRESCENT_ISLE", f"LAND: on Crescent Isle (in {story.current_area_key})")
check(getattr(g, "soaring_state", None) is None, "the flight is over")

print("== soaring away again")
g.change_state(AreaTransitionState(g, soaring.AREA))
st = run_transition()
check(isinstance(st, SoaringState), "SOAR AWAY: the flight again")
check(abs(st.wy - cres["at"][1]) < 4, "you take off over Crescent Isle")

print("== a wild Pokemon")
st.skip = {s["key"] for s in st.spots}; st.next_gust = st.next_wild = 10 ** 6
st.wilds = [{"pid": 278, "x": st.wx, "y": st.wy - 4, "vx": 0.0, "vy": 0.0, "ph": 0}]
st.update()
b = g.current_state
check(type(b).__name__ == "WildBattleState", "flying into Wingull: a battle")
check(getattr(b, "play_state_data", {}).get("soaring"), "the battle knows to come back to the flight")
wy = st.wy
b.on_flee_complete()
check(g.current_state is st and st.mode == "FLY", "run away: back in the sky")
check(abs(st.wy - wy) < 1, "... where you were")

print("== a legend in a rift")
story.player_team = [mk(480), mk(481), mk(482)] + team[:1]
st._back_from_battle()
rift = next(s for s in st.spots if s["key"] == "rift1")
st.skip = set(); st.wx, st.wy = float(rift["at"][0]), float(rift["at"][1] + 60); st.mode = "FLY"
for _ in range(40):
    st.update()
    if st.mode == "ASK":
        break
check(st.mode == "ASK" and st.ask[0]["key"] == "rift1", "into the huge gap: asked to fly in")
shot("rift")
tap(st, st.ask[1][0][0].center)
for _ in range(10):
    if st.dialogue_box.visible:
        st.dialogue_box.is_finished = True
        cb, st.dialogue_box.callback = st.dialogue_box.callback, None
        cb and cb()
    if g.current_state is not st:
        break
b = g.current_state
first = getattr(b, "victory_flag", None)
check(type(b).__name__ == "WildBattleState" and getattr(b, "is_boss_battle", False) and first in ("soaring_dialga", "soaring_palkia"),
      f"FLY IN: Dialga's or Palkia's battle ({type(b).__name__}, {first})")
flags[first] = True
b.on_flee_complete()
check(g.current_state is st, "back in the sky after")
other = ({"soaring_dialga", "soaring_palkia"} - {first}).pop()
check(soaring.next_legend(story, rift, st.area_data)["victory_flag"] == other, "the same rift holds the other one next")
flags[other] = True
st._back_from_battle()
check(not any(s["key"] == "rift1" for s in st.spots), "both caught: the rift is gone")
story.player_team = team

print("== landing at a town")
_visited = {k: v for k, v in flags.items() if k.startswith("visited_")}
for k in _visited:
    flags.pop(k)
flags["visited_MOSSDEEP_CITY"] = True
check(soaring.nearest_town(g, *soaring.ground_xy((315, 110)))[0] == "MOSSDEEP_CITY",
      "over Lilycove before you've been there: you land at the nearest town you HAVE been to (Mossdeep)")
flags["visited_LILYCOVE_CITY"] = True
st.mode = "FLY"; st.wx, st.wy = map(float, soaring.ground_xy((315, 110)))
tap(st, st._land_rect().center)
check(st.mode == "ASK" and "Lilycove" in st.ask_line, "LAND over Lilycove asks to land there")
key(st, pygame.K_RETURN)
run_transition()
check(story.current_area_key == "LILYCOVE_CITY", f"... and sets you down there ({story.current_area_key})")

print("== the landing areas (walked maps)")
import json as _json
from src.states.overworld.dungeon import DungeonState
g.dungeon_routes = True
_tm = _json.load(open("assets/town_maps.json", encoding="utf-8"))


def figures(st):
    return [(m.payload.get("text"), getattr(m, "floor", None)) for m in st.run.floor.movers
            if m.kind == "figure" and isinstance(m.payload, dict)]


def land(area):
    story.current_area_key = soaring.AREA
    g.soaring_state = None
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


LEGENDS = {"HOENN_CRESCENT_ISLE": "crescent", "HOENN_PATHLESS_PLAIN": "pathless", "HOENN_TRACKLESS_FOREST": "trackless",
           "HOENN_GNARLED_DEN": "gnarled", "HOENN_FABLED_CAVE": "fabled", "HOENN_NAMELESS_CAVERN": "nameless"}
for area, key in LEGENDS.items():
    spot = next(x for x in soaring.FIXED if x["key"] == key)
    pick = None
    for i in range(20):
        pick = soaring.roll_visit(story, spot, _r.Random(i))
        if pick:
            break
    st = land(area)
    check(isinstance(st, DungeonState), f"{area}: a walked map ({type(st).__name__})")
    if not isinstance(st, DungeonState):
        continue
    arr = _tm[area]["arrive"][soaring.AREA]
    check(list(st.run.player) == arr and st.run.index == 0, f"{area}: you land beside your Eon ({st.run.player} vs {arr})")
    seeks = {t for t in placed(st) if t.startswith("SEEK ")}
    want = {next(o["text"] for o in g.loader.area_data["STORY_PROGRESSION"][area]["route_menu"]
                 if (o.get("boss") or {}).get("victory_flag") == pick)}
    check(seeks == want, f"{area}: only this visit's legend is out ({seeks})")
    check("SOAR AWAY" in placed(st), f"{area}: your Eon waits")
    snap(st, area.lower().replace("hoenn_", ""))
    if _tm[area].get("floors"):
        snap(st, area.lower().replace("hoenn_", "") + "_in", 1)
        st.run.enter_floor(0)
    for f in spot["legends"]:
        flags.pop(f"mirage_here_{f}", None)
    st = land(area)
    check(not any(t.startswith("SEEK ") for t in placed(st)), f"{area}: a quiet visit, nobody at the back")

print("== the daily Mirage spots")
for kind in ("forest", "cave", "mountain"):
    area = soaring.DAILY[kind][0]
    from town_maps_soaring import MIRAGE_ITEMS, item_text
    for i, it in enumerate(MIRAGE_ITEMS[kind]):
        if not it:
            continue
        soaring.mark_place(story, kind, i)
        st = land(area)
        items = {t for t in placed(st) if t not in ("SOAR AWAY",) and t[-1].isdigit()}
        check(items == {item_text(kind, i)}, f"{area} place {i + 1}: its own item, {it} ({items})")
    snap(st, f"mirage_{kind}")
    if _tm[area].get("floors"):
        snap(st, f"mirage_{kind}_in", 1)
        st.run.enter_floor(0)

print("== the Mirage Islands: Gen 1-3 legends")
isl = {"key": "daily", "legends": soaring.ISLAND_LEGENDS}
out = set()
for i in range(60):
    pick = soaring.roll_visit(story, isl, _r.Random(i))
    out.add(pick)
check(out - {None} == set(soaring.ISLAND_LEGENDS), "over many visits each of Articuno, Zapdos, Moltres, Mewtwo, Celebi comes out")
day = next(d for d in range(1, 60) if soaring.daily(story, __import__("datetime").date(2026, 12, 1) + __import__("datetime").timedelta(d))[0] == "island")
dspot = next(x for x in soaring.spots(story, __import__("datetime").date(2026, 12, 1) + __import__("datetime").timedelta(day)) if x["key"] == "daily")
check(dspot["area"] == "HOENN_MIRAGE_ISLANDS" and dspot["legends"] == soaring.ISLAND_LEGENDS, "the daily island lands on ORAS's Mirage Island, with its legends")
from town_maps_soaring import MIRAGE_ITEMS as _MI, item_text as _it
for i, it in enumerate(_MI["island"]):
    if not it:
        continue
    soaring.mark_place(story, "island", i)
    flags.pop("mirage_here_mirage_zapdos", None)
    for f in soaring.ISLAND_LEGENDS:
        flags.pop(f"mirage_here_{f}", None)
    flags["mirage_here_mirage_zapdos"] = True
    st = land("HOENN_MIRAGE_ISLANDS")
    items = {t for t in placed(st) if t[-1].isdigit()}
    check(items == {_it("island", i)}, f"Mirage Island place {i + 1}: its own item, {it} ({items})")
    check({t for t in placed(st) if t.startswith("SEEK ")} == {"SEEK ZAPDOS"}, "Mirage Island: only this visit's legend (Zapdos)")
snap(st, "mirage_island")
boss = next(o for o in g.loader.area_data["STORY_PROGRESSION"]["HOENN_MIRAGE_ISLANDS"]["route_menu"] if o["text"] == "SEEK MEWTWO")["boss"]
check(boss["id"] == 150 and boss["level"] == 70 and boss["victory_flag"] == "mirage_mewtwo", "Mewtwo at Lv. 70 (FireRed's), its own Hoenn flag")

print("== Hoopa's ring")
def at_ring(area, floor, name, legend_flag):
    spot = next(x for x in soaring.FIXED if x.get("area") == area)
    for f in spot["legends"]:
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
import datetime as _dt
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
    for _ in range(40):
        if st.dialogue_box.visible:
            st.dialogue_box.is_finished = True
            cb, st.dialogue_box.callback = st.dialogue_box.callback, None
            if cb:
                cb()
        st.update()
_got = {k for k, v in story.inventory.items() if v > _before.get(k, 0)}
check(_got and _got <= {i for i, _w in soaring.DAILY_ITEMS["crescent"]}, f"picked up: one of Crescent Isle's ({_got})")
check(not flags.get("mirage_daily_ready"), "taken: none more today")
soaring.new_day_item(story, _d0)
check(not flags.get("mirage_daily_ready"), "landing again the same day: still none")
soaring.new_day_item(story, _d0 + _dt.timedelta(1))
check(flags.get("mirage_daily_ready"), "the next day: a new one")

print("== Rock Smash rocks")
story.inventory["HM_ROCK_SMASH"] = 1
st = land("HOENN_MIRAGE_FOREST")
rocks = [t for t, w in st.run.floor.decor.items() if str(w).startswith("crack:")]
check(len(rocks) == 3, f"the Mirage Forest's three cracked rocks stand, even with Rock Smash ({len(rocks)})")
st.SMASH_WILD = 1.0
t = rocks[0]
st.run.player, st.facing = (t[0], t[1] + 1), (0, -1)
st._read_sign()
check(t not in st.run.floor.decor, "facing one with Rock Smash: it breaks")
wild = [m for m in st.run.floor.movers if m.kind == "wild" and (m.x, m.y) == t]
pool = {int(k) for k in g.loader.area_data[g.loader.area_data["STORY_PROGRESSION"]["HOENN_MIRAGE_FOREST"]["wild_pool_percentages"]]}
check(wild and int(getattr(wild[0].payload, "meta_id", None) or wild[0].payload.id) in pool, "a wild Pokemon from the forest's own pool jumped out")
check(len([x for x, w in st.run.floor.decor.items() if str(w).startswith("crack:")]) == 2, "the other rocks still stand")
story.inventory.pop("HM_ROCK_SMASH", None)

print("== a beaten legend comes back the next day")
from src.states.battle import legend_back
flags["legend_rematch_mirage_kyurem"] = _dt.date.today().toordinal()
check(not legend_back(flags, "mirage_kyurem"), "beaten today, not caught: not back yet")
flags["legend_rematch_mirage_kyurem"] = _dt.date.today().toordinal() - 1
check(legend_back(flags, "mirage_kyurem"), "the next day: back")
flags["legend_rematch_mirage_kyurem"] = True
check(legend_back(flags, "mirage_kyurem"), "an older save's rematch: back now")
flags.pop("legend_rematch_mirage_kyurem")

print("== soaring away from a landing area")
st = land("HOENN_CRESCENT_ISLE")
eon = next(m for m in st.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == "SOAR AWAY")
st._use_figure(eon)
for _ in range(60):
    if g.current_state is not st:
        break
    if st.dialogue_box.visible:
        st.dialogue_box.is_finished = True
        cb, st.dialogue_box.callback = st.dialogue_box.callback, None
        if cb:
            cb()
    st.update()
nxt = run_transition()
check(isinstance(nxt, SoaringState), f"talking to your Eon: off you fly ({type(nxt).__name__})")
cres = soaring.ground_xy(next(x for x in soaring.FIXED if x["key"] == "crescent")["at"])
check(isinstance(nxt, SoaringState) and abs(nxt.wy - cres[1]) < 4, "... from over Crescent Isle")

print("== Hoenn's own TMs (ORAS numbering, Emerald's after 100)")
from src.pokemon import tms as _tms
_ht = {k: v for k, v in _tms.table(g).items() if _tms.is_hoenn(k)}
check(len([k for k in _ht if int(k[3:]) <= 100]) == 100 and len(_ht) == 108, f"ORAS's 100 and Emerald's 8 more ({len(_ht)})")
check(_tms.move_of(g, "HTM24") == "THUNDERBOLT" and _tms.label(g, "HTM24") == "TM24 Thunderbolt", "TM24 is ORAS's Thunderbolt, shown as TM24")
check(_tms.move_of(g, "HTM101") == "FOCUS-PUNCH", "TM101: Emerald's Focus Punch (ORAS has none)")
check(_tms.move_of(g, "TM24") != "THUNDERBOLT" or True, "other regions keep Sword/Shield's")
_reg = story.get_current_region
story.get_current_region = lambda: "HOENN"
_stock_h = _tms.mart_stock(g, 8)
story.get_current_region = lambda: "KANTO"
_stock_k = _tms.mart_stock(g, 8)
story.get_current_region = _reg
check(_stock_h and all(_tms.is_hoenn(k) for k in _stock_h), "Hoenn's Marts sell Hoenn's own TMs")
check(_stock_k and not any(_tms.is_hoenn(k) for k in _stock_k), "Kanto's Marts sell Sword/Shield's")
_sp = g.loader.area_data["STORY_PROGRESSION"]
_gifts = set()
for _a, _d in _sp.items():
    if not isinstance(_d, dict) or _d.get("region") != "HOENN":
        continue
    for _o in _d.get("route_menu", []):
        _ev = _o.get("event") if isinstance(_o, dict) else None
        if isinstance(_ev, dict):
            _gifts |= {it for it in (_ev.get("gift_item") or {}) if _tms.is_tm(it)}
check(_gifts and all(_tms.is_hoenn(k) for k in _gifts), f"every TM Hoenn's places give is Hoenn's own ({sorted(_gifts)[:6]}...)")
check(_tms.move_of(g, "HTM23") == "SMACK-DOWN", "Cozmo's thanks: TM23 Smack Down")
_linked, _area = set(story.linked_regions), story.current_area_key
story.linked_regions = _linked - {"HOENN"}
story.current_area_key = "MOSSDEEP_CITY"
check(story.active_store == "HOENN", "a save with Hoenn's own Bag")
_old = next(k for k in sorted(_tms.table(g)) if not _tms.is_hoenn(k) and _tms.hoenn_key(g, _tms.move_of(g, k)))
_new = _tms.hoenn_key(g, _tms.move_of(g, _old))
story.inventory[_old] = 1     # (a Sword/Shield TM bought in Hoenn before, one Hoenn has too)
story.inventory["TM00"] = 1   # (Mega Punch: Hoenn has no TM for it)
story.sync_key_items()
check(story.inventory.get(_new) and _old not in story.inventory and story.inventory.get("TM00"),
      f"loading it: its {_tms.label(g, _new)} ({_old} before) is Hoenn's own now; Mega Punch stays as it was")
story.linked_regions = _linked
story.current_area_key = _area

print(f"##### {len(fails)} fail")
