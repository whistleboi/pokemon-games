# Layered tracks (11-25, Unova's Village Bridge: Black 2 brings each musician's instruments into the place's music as you meet
# them): src/core/music.py plays a base track and its parts in step (music.json "layers"), each part heard once its flag is set.
# Parts rendered by kanto_handoff/unova_map_tools/music.py LAYERS.
#   bash dev/checks/run.sh music_layers
import json as _json
import os as _os
import pygame as _pg
fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


story = g.story_manager
table = _json.load(open("assets/music/unova/music.json", encoding="utf-8"))
print("1) Village Bridge's base and its four parts")
parts = (table.get("layers") or {}).get("h_04_base") or []
check(table["areas"].get("VILLAGE_BRIDGE") == "h_04_base", "Village Bridge plays the base (the guitar alone)")
check([p["flag"] for p in parts] == ["vb_music_flute", "vb_music_guitar", "vb_music_beatbox", "vb_music_enka"],
      "four parts: grass flute, second guitar, beatboxing, enka singing")
lens = {}
for name in ["h_04_base"] + [p["file"] for p in parts]:
    path = f"assets/music/unova/{name}.ogg"
    lens[name] = round(_pg.mixer.Sound(path).get_length(), 2) if _os.path.isfile(path) and _pg.mixer.get_init() else None
check(len(set(lens.values())) == 1 and None not in lens.values(), f"all the same length, so they stay in step ({lens})")

print("2) in game: the parts start silent, each comes in with its flag")
if not _pg.mixer.get_init():
    print("   (no sound device here: part 2 skipped)")
else:
    story.enter_region("UNOVA")
    story.current_area_key = "VILLAGE_BRIDGE"
    for p in parts:
        story.story_flags.pop(p["flag"], None)
    m = g.music
    m.play("town", force=True)
    check(_os.path.basename(m.path or "") == "h_04_base.ogg" and len(m.layers) == 4, f"the base and four parts playing ({len(m.layers)})")
    check(all(ch.get_volume() == 0 for ch, _s, _f in m.layers), "no musician met: only the base is heard")
    story.story_flags["vb_music_flute"] = True
    for _ in range(12):
        m.update()
    vols = [round(ch.get_volume(), 2) for ch, _s, _f in m.layers]
    check(vols[0] > 0 and vols[1:] == [0, 0, 0], f"the flute player met: the flute comes in ({vols})")
    story.story_flags.update(vb_music_guitar=True, vb_music_beatbox=True, vb_music_enka=True)
    for _ in range(12):
        m.update()
    check(all(ch.get_volume() > 0 for ch, _s, _f in m.layers), "all four met: the whole band")
    story.current_area_key = "ASPERTIA_CITY"
    m.play("town", force=True)
    check(not m.layers, "somewhere else: the parts stop")
print(f"##### {len(fails)} failures")
