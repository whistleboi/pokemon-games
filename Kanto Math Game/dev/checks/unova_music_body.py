# Unova's soundtrack (11-23): Black 2's own tracks (kanto_handoff/unova_map_tools/music.py -> assets/music/unova),
# picked by src/core/music.py's region_track as a player meets them: a town, its Center and Gym, a route by season,
# the grotto off Floccesy Ranch, the battles.
#   bash dev/checks/run.sh unova_music
import datetime
import json
import os
from src.core import music as _music
from src.states.overworld import CityState, PlayState as _PS
from src.world import seasons

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True
flags = story.story_flags
flags["unova_version"] = "BLACK_2"; story.starting_region = "UNOVA"
for a in ("ASPERTIA_CITY", "UNOVA_ROUTE_19", "FLOCCESY_RANCH", "CASTELIA_CITY"):
    flags["visited_" + a] = True
M = g.music if getattr(g, "music", None) else _music.MusicManager(g)


def track(kind):
    p = M.region_track(kind, "UNOVA")
    return os.path.splitext(os.path.basename(p))[0] if p else None


def settle(n=10):
    for _ in range(n):
        st = g.current_state
        st.update(); st.draw()


print("1) the files")
table = json.load(open("assets/music/unova/music.json", encoding="utf-8"))
names = set()
for v in list(table["areas"].values()) + list(table["rooms"].values()) + list(table["kinds"].values()):
    names.update(v.values() if isinstance(v, dict) else [v])
missing = sorted(n for n in names if not os.path.isfile(f"assets/music/unova/{n}.ogg"))
check(not missing, f"every track music.json names is there ({len(names)} tracks; missing {missing})")

print("2) a town, then its Center and Gym")
story.current_area_key = "ASPERTIA_CITY"
g.walk_town_pos = ("ASPERTIA_CITY", (20, 20), (0, 1)); g.walk_town_room = None
g.change_state(CityState(g)); settle()
check(track("town") == "sw_c_12", f"Aspertia City: its own theme ({track('town')})")
g.walk_town_room = ("ASPERTIA_CITY", "center"); g.walk_town_pos = ("ASPERTIA_CITY", (7, 10), (0, -1))
g.change_state(CityState(g)); settle()
check(track("town") == "pokecen", f"...in the Pokemon Center: the Center's ({track('town')})")
g.walk_town_room = ("ASPERTIA_CITY", "gym"); g.change_state(CityState(g)); settle()
check(track("town") == "gym", f"...in the Gym: the Gym's ({track('town')})")

print("3) a route by the season")
real = seasons._today
try:
    for month, want in ((1, "sw_r_19_sp"), (2, "sw_r_19_su"), (3, "sw_r_19_au"), (4, "sw_r_19_wi")):
        seasons._today = lambda m=month: datetime.date(2026, m, 10)
        story.current_area_key = "UNOVA_ROUTE_19"; g.walk_town_pos = g.walk_town_room = None
        g.arrive_floor = ("UNOVA_ROUTE_19", 0, [10, 20])
        g.change_state(_PS(g)); settle()
        check(track("route") == want, f"Route 19 in {seasons.current_season().title()}: {want} ({track('route')})")
finally:
    seasons._today = real

print("4) the grotto, a route map's room")
story.current_area_key = "FLOCCESY_RANCH"
g.arrive_floor = ("FLOCCESY_RANCH", 0, [52, 21])
g.change_state(_PS(g)); settle()
t = g.current_state
check(track("route") == "sw_d_22", f"Floccesy Ranch: its own theme ({track('route')})")
t.step(0, -1)
for _ in range(60):
    t = g.current_state; t.update()
check(track("route") == "kemonomichi", f"...into the Hidden Grotto: the grotto's ({track('route')})")

print("5) battles")
check(track("wild") == "vs_norapoke" and track("trainer") == "vs_trainer" and track("gym") == "vs_gymleader",
      "wild, trainer and Gym Leader battles: Black 2's own")
check(M.region_track("town", "KANTO") is None, "a region without its own music.json plays as before")

print("6) the themes by who you battle (11-25, ROADMAP_UNOVA 'Music still to wire'; kanto_handoff/unova_map_tools/music.py)")
class _B:   # (a battle as the music sees it)
    def __init__(s, cls="", name="", mons=()):
        s.trainer_class, s.trainer_name, s.opponent_team = cls, name, [type("P", (), {"id": m})() for m in mons]
_own = lambda b, what: (M._region_own(b, what) or "").split("/")[-1]
g.rival_name = "Hugh"
check(_own(_B("CHAMPION", "Champion Iris"), "trainers") == "vs_iris", f"Champion Iris: her own theme ({_own(_B('CHAMPION', 'Champion Iris'), 'trainers')})")
check(_own(_B("RIVAL", "Hugh"), "trainers") == "vs_hue", f"the rival, Hugh: his ({_own(_B('RIVAL', 'Hugh'), 'trainers')})")
check([_own(_B("", n), "trainers") for n in ("N", "Ghetsis", "Colress", "Boss Trainer Benga", "Cynthia")]
      == ["vs_swan_n", "vs_new_g_cis", "vs_achroma", "vs_banjirou", "vs_shirona"], "N, Ghetsis, Colress, Benga, Cynthia: each their own")
check(_own(_B("YOUNGSTER", "Youngster Wes"), "trainers") == "", "an ordinary trainer: the usual trainer battle theme")
check([_own(_B(c), "eyes") for c in ("DANCER", "HARLEQUIN", "PLASMA")] == ["eye_dancer", "eye_clown", "eye_neo_plasma"],
      "eyes meet: the Dancer's, the Harlequin's and Team Plasma's own")
check([_own(_B(mons=[m]), "legends") for m in (646, 638, 641, 377, 485, 25)] == ["vs_kyuramu", "vs_uma", "vs_rai", "vs_regi", "vs_dplegend", ""],
      "legends: Kyurem, the Swords of Justice, the Forces of Nature, the Regi, Sinnoh's; an ordinary Pokemon none")
M.kind = "wild"
_vw = os.path.basename(M.region_track("victory", "UNOVA") or "")
M.kind = "trainer"
_vt = os.path.basename(M.region_track("victory", "UNOVA") or "")
check(_vw == "win2.ogg" and _vt == "win1.ogg", f"after a wild battle its own fanfare, after a trainer the usual ({_vw}, {_vt})")

print(f"##### {len(fails)} failures")
