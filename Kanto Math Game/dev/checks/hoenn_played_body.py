# Hoenn's played checks (11-24, Dev Map clean-hoenn-hoenn-played; Johto's johto_played made Hoenn's): what the other Hoenn
# suites only read, heard or played as a player would.
#   5. Emerald's own music (assets/music/hoenn, kanto_handoff/hoenn_rom_tools/hmusic.py; Dev Map clean-hoenn-music):
#      each place's theme, its rooms', the battles
#   (to come, card clean-hoenn-hoenn-played: an old save loaded; every Gym Leader, the Elite Four and Steven fought turn
#    by turn; the League and Leaders' rematches)
#        bash dev/checks/run.sh hoenn_played
import json, os

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


print("\n5) Emerald's own music (assets/music/hoenn, hoenn_rom_tools/hmusic.py): each place's theme, its rooms', the battles")
_mt = json.load(open("assets/music/hoenn/music.json", encoding="utf-8"))
_names = {v for v in list(_mt["areas"].values()) + list(_mt["rooms"].values()) + list(_mt["kinds"].values()) if isinstance(v, str)}
_missing = sorted(n for n in _names if not os.path.isfile(os.path.join("assets", "music", "hoenn", n + ".ogg")))
check(not _missing and len(_mt["areas"]) >= 80, f"every track named is there ({len(_names)} tracks, {len(_mt['areas'])} places; missing {_missing})")
_m = g.music
story.current_area_key = "LITTLEROOT_TOWN"; g.walk_town_room = None
_t = _m.region_track("town", "HOENN")
check(bool(_t) and _t.endswith("em_405.ogg"), f"Littleroot Town plays its own Emerald theme ({_t and os.path.basename(_t)})")
story.current_area_key = "HOENN_ROUTE_101"
_t = _m.region_track("route", "HOENN")
check(bool(_t) and _t.endswith("em_359.ogg"), f"...Route 101 its own ({_t and os.path.basename(_t)})")
_k = {k: (_m.region_track(k, "HOENN") or "") for k in ("wild", "trainer", "gym", "final", "villain", "center", "victory")}
check(all(_k.values()) and _k["wild"].endswith("em_474.ogg") and _k["gym"].endswith("em_477.ogg") and _k["final"].endswith("em_482.ogg"),
      f"...and the battles Emerald's: {[(k, os.path.basename(v)) for k, v in _k.items()]}")

print(f"##### {len(fails)} failures")
for m in fails:
    print("   FAIL " + m)
