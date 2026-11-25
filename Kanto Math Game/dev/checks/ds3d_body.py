# The DS regions are 3D only (Jordan 11-24: "3d only"): no Options "3D camera: Flat" choice, and every map drawn from a
# DS game's picture (SoulSilver ss_ground, Platinum pt_ground, Black 2 b2_ground) has that game's 3D scene to draw it
# (live3d.scene_of: assets/ss_3d, pt_3d, b2_3d). A region's flat pictures are deleted once all its places have one:
# Johto, Sinnoh and Unova all done 11-24: their flat pictures are gone.
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
check(not _missing["pt"], f"Sinnoh: all {_count['pt']} Platinum pictures have a scene {_missing['pt'][:8]}")
check(not _missing["b2"], f"Unova: all {_count['b2']} Black 2 pictures have a scene {_missing['b2'][:8]}")
check(not _glob.glob("assets/tiles/b2_ground/*.png"), "Unova's too: no assets/tiles/b2_ground pictures left (11-24)")

print("3) Johto's flat pictures are gone (3D only)")
check(not _glob.glob("assets/tiles/ss_ground/*.png") and not _glob.glob("assets/tiles/ss_top/*.png"),
      "no assets/tiles/ss_ground or ss_top pictures left")
check(not _glob.glob("assets/tiles/pt_ground/*.png"), "Sinnoh's too: no assets/tiles/pt_ground pictures left (11-24)")

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

print("5) every Sinnoh and Unova place opens in 3D (its scene found and under every walkable tile)")
from src.dungeon import live3d as _l3
g.live3d_headless = True; g.dungeon_routes = True
_TMS = _json.load(open("assets/town_maps.json", encoding="utf-8"))
_SP = g.loader.area_data["STORY_PROGRESSION"]


def _settle(n=20):
    for _ in range(n):
        st = g.current_state
        if type(st).__name__ == "DungeonState" and hasattr(st, "run"):
            st.run.floor.movers = [m for m in st.run.floor.movers if m.kind != "wild"]
        if type(st).__name__ == "PickListState":
            st.pick(None); continue
        if getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            st.dialogue_box.advance()
        st.update(); st.draw()


def _ds(roofs, kind):
    return str(((roofs or {}).get("_picture") or {}).get("f") or "").startswith(kind + "_ground/")


if not _l3.available(g):
    print("   (no OpenGL 3.3 here: part 5 skipped)")
else:
    story.story_flags.setdefault("unova_version", "BLACK_2")   # (past Unova's version choice: Black 2's maps)
    for _kind, _reg in (("pt", "Sinnoh"), ("b2", "Unova")):
        _bad, _n = [], 0
        for _key, _m in _TMS.items():
            if _kind + "_ground/" not in _json.dumps(_m) or _key not in _SP:
                continue
            try:
                story.enter_region(_SP[_key].get("region") or ("SINNOH" if _kind == "pt" else "UNOVA"))
            except Exception:
                pass
            try:
                if "floors" in _m:
                    _p = kanto(_key); _settle()
                    if not hasattr(_p, "run"):
                        continue
                    for _i, _fl in enumerate(_m["floors"]):
                        if not _ds(((_fl.get("art") or {}) if isinstance(_fl.get("art"), dict) else _fl).get("roofs"), _kind):
                            continue
                        if _i:
                            _p.run.enter_floor(_i); _settle(3)
                        _n += 1
                        if not _p._dl_live():
                            _bad.append(f"{_key}#{_i}")
                else:
                    story.current_area_key = _key; story.story_flags["visited_" + _key] = True
                    g.walk_town_pos = None; g.walk_town_room = None
                    g.change_state(_CS(g)); _settle()
                    _t = g.current_state
                    if _ds(_m.get("roofs"), _kind):
                        _n += 1
                        if not getattr(_t, "_live", lambda: 1)():
                            _bad.append(_key)
                    for _rn, _rm in (_m.get("rooms") or {}).items():
                        if not _ds(_rm.get("roofs"), _kind):
                            continue
                        _t._go(_rn, None); _settle(3)
                        _n += 1
                        if getattr(_t, "room", None) != _rn or not _t._live():
                            _bad.append(f"{_key}/{_rn}")
            except Exception as _e:
                _bad.append(f"{_key} ({type(_e).__name__}: {str(_e)[:60]})")
        print(f"    {_reg}: {_n - len(_bad)} of {_n} maps live")
        check(not _bad, f"{_reg}: every map live in 3D {_bad[:40]}")
print("6) Unova's season colours (11-25): summer and autumn scenes where Black 2 has its own texture set; winter waits")
from src.world import seasons as _seasons
_sf = {s: _l3.season_file(g, 427, s) for s in ("SPRING", "SUMMER", "AUTUMN", "WINTER")}
check(_sf["SPRING"] is None and _sf["SUMMER"] and _sf["AUTUMN"], f"Aspertia: summer and autumn scenes of their own, spring the plain one ({ {k: bool(v) for k, v in _sf.items()} })")
check(_l3.season_file(g, 28, "AUTUMN") is None, "Castelia: no autumn set of its own (Black 2 has one set): the plain scene")
_n = len([f for f in _os.listdir("assets/b2_3d") if f.endswith(("_summer.npz", "_autumn.npz"))])
check(_n >= 150, f"{_n} summer and autumn scenes")
print(f"##### {fails} failures")
