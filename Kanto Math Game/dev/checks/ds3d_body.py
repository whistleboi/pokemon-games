# The DS regions are 3D only (Jordan 11-24: "3d only"): no Options "3D camera: Flat" choice, and every map drawn from a
# DS game's picture (SoulSilver ss_ground, Platinum pt_ground, Black 2 b2_ground) has that game's 3D scene to draw it
# (live3d.scene_of: assets/ss_3d, pt_3d, b2_3d). A region's flat pictures are deleted once all its places have one:
# Johto done; Sinnoh and Unova list what they still miss (their branches export them).
#   bash dev/checks/run.sh ds3d
exec(open("dev/checks/dungeon_lib.py", encoding="utf-8").read())
import glob as _glob
import json as _json
import os as _os
import re as _re
from src.core import settings as _settings
from src.states.systems.options import OptionsState as _OS

print("1) no Flat choice")
check("live3d" not in _settings.DEFAULTS, "no 3D camera setting")
_o = _OS(g, g.current_state, lambda: None)
_o.tab = _o.tabs.index("SCREEN & SOUND")
check(not any(r[0] == "3D camera" for r in _o.rows()), "Options, SCREEN & SOUND: no 3D camera row")

print("2) every DS map has its 3D scene")
_pics = set()
for _f in ["assets/town_maps.json"] + _glob.glob("assets/*dungeon*.json"):
    with open(_f, encoding="utf-8") as _h:
        _pics |= set(_re.findall(r'"f": *"((?:ss|pt|b2)_ground/[^"\\]+?\.png)"', _h.read()))   # (a map's ground, not B2's _cam helpers)


def _scene_file(pic):
    kind, name = pic[:2], _os.path.splitext(_os.path.basename(pic))[0]
    return _os.path.join("assets", kind + "_3d", name + ".npz")


_missing = {k: sorted(p for p in _pics if p.startswith(k) and not _os.path.exists(_scene_file(p))) for k in ("ss", "pt", "b2")}
_count = {k: sum(1 for p in _pics if p.startswith(k)) for k in ("ss", "pt", "b2")}
check(_count["ss"] > 200 and not _missing["ss"], f"Johto: all {_count['ss']} SoulSilver pictures have a scene {_missing['ss'][:8]}")
for _k, _r in (("pt", "Sinnoh"), ("b2", "Unova")):
    print(f"    {_r}: {_count[_k] - len(_missing[_k])} of {_count[_k]} have a scene; not yet: {len(_missing[_k])} {_missing[_k][:10]}")

print("3) Johto's flat pictures are gone (3D only)")
check(not _glob.glob("assets/tiles/ss_ground/*.png") and not _glob.glob("assets/tiles/ss_top/*.png"),
      "no assets/tiles/ss_ground or ss_top pictures left")

print("4) a Johto town and room still open and draw without them (headless: no scene drawn, plain tiles)")
from src.states.overworld import CityState as _CS
g.walk_towns = True
story.enter_region("JOHTO")
story.current_area_key, story.last_area_key = "CHERRYGROVE_CITY", "JOHTO_ROUTE_30"
g.walk_town_pos = None
g.change_state(_CS(g))
_t = g.current_state
for _ in range(5):
    _t.update(); _t.draw()
check(getattr(_t, "map_img", None) is not None, "Cherrygrove opens and draws")
_t._go("center", None)
for _ in range(3):
    _t.update(); _t.draw()
check(_t.room == "center", "...and its Pokemon Center")
print(f"##### {fails} failures")
