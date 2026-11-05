"""Move animations from the fan game Pokemon Orre 2.1.1 (Jordan, 11-04): its Pokemon Essentials animation
set (Data/PkmnAnimations.rxdata, the Gen 8 animation project's: 934 moves, 343 foe-side versions, 84
common ones such as status and stat changes), the largest of the fan games we have.

Each animation is a list of frames (20 a second); a frame is a list of cels. Cel 0 is the user's sprite and
cel 1 the target's (their pattern is -1 / -2: they move, hide or tint the battlers); the others are 192 x 192
patterns of the animation's graphic sheet (5 a row). A cel's focus says what its x, y are measured from:
0 the screen, 1 the target, 2 the user, 3 the line from user to target (Essentials' editor puts the user at
(128, 224) and the target at (384, 96) on a 512 x 384 screen). Timings play a sound, flash a battler or the
screen, or show / move a background or foreground picture.

Also our own: Found Power, Nown's move (FOUND_POWER): Hidden Power's orbs gather round the user, then, as
they fade, a bigger Hyper Beam washed violet fires, with a white flash. A cel's 17th field, where there is
one, picks its sheet from the animation's "graphics" list (else its "graphic").

Written to assets/move_animations/: animations.json.gz ({name: animation}, name as Essentials has it,
"Move:TACKLE", "OppMove:TACKLE", "Common:Burn"), and the graphics and sounds they use (graphics/, sounds/).
    python dev/builders/import_move_animations.py ["<Pokemon Orre folder>"]
"""
import gzip
import json
import os
import shutil
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rxdata  # noqa: E402

ORRE_GAME = os.path.join(os.path.expanduser("~"), "Downloads", "Pokemon_Orre_2.1.1", "Pokemon_Orre_2.1.1_reupload")
OUT = os.path.join("assets", "move_animations")
KINDS = ("Move:", "OppMove:", "Common:")
# Essentials' cel fields (AnimFrame): kept as [pattern, x, y, zoom x, zoom y, angle, mirror, opacity, blend,
# focus, visible, priority, colour r, g, b, a]
CEL = (7, 0, 1, 2, 11, 3, 4, 8, 5, 26, 6, 25, 12, 13, 14, 15)


def color(v):
    """An RGSS Color or Tone (4 doubles) as [r, g, b, a], or None."""
    if isinstance(v, rxdata.RUser) and len(v.data) >= 32:
        return [round(c) for c in struct.unpack("<4d", v.data[:32])]
    return None


def cel(c):
    if not c:
        return None
    out = [c[i] if i < len(c) else None for i in CEL]
    return [0 if v is None else (round(v) if isinstance(v, float) else v) for v in out]


def timing(t):
    a = t.attrs
    return {k: v for k, v in {
        "frame": a.get("frame", 0), "type": a.get("timingType", 0), "name": rxdata.text(a.get("name")) or None,
        "volume": a.get("volume", 100), "pitch": a.get("pitch", 100),
        "flash_scope": a.get("flashScope", 0), "flash_color": color(a.get("flashColor")),
        "flash_duration": a.get("flashDuration", 5), "duration": a.get("duration", 5),
        "bg_x": a.get("bgX"), "bg_y": a.get("bgY"), "opacity": a.get("opacity"),
        "color": [a.get("colorRed"), a.get("colorGreen"), a.get("colorBlue"), a.get("colorAlpha")]
        if a.get("colorRed") is not None else None,
    }.items() if v is not None}


def found_power(anims):
    """Nown's Found Power (Jordan, 11-04): a mix of Hidden Power and Hyper Beam."""
    orbs, beam = anims["Move:HIDDENPOWER"], anims["Move:HYPERBEAM"]
    start = len(orbs["frames"]) - 5  # the beam fires while the last orbs fade
    frames = []
    for i in range(max(len(orbs["frames"]), start + len(beam["frames"]))):
        a = orbs["frames"][i] if i < len(orbs["frames"]) else []
        b = beam["frames"][i - start] if 0 <= i - start < len(beam["frames"]) else []
        # the battlers (cels 0 and 1) follow the beam once it fires
        frame = [(b[k] if k < len(b) and b[k] else a[k] if k < len(a) else None) for k in range(2)]
        frame += [c + [0] for c in a[2:] if c]
        for c in b[2:]:
            if c:
                c = list(c)
                c[3], c[4] = int(c[3] * 1.25), int(c[4] * 1.25)  # bigger
                if not c[15]:
                    c[12:16] = [170, 110, 255, 110]  # washed violet
                frame.append(c + [1])
        frames.append(frame)
    timings = [dict(t) for t in orbs["timings"]]
    for t in beam["timings"]:
        t = dict(t, frame=t["frame"] + start)
        timings.append(t)
    timings.append({"frame": start, "type": 0, "name": None, "flash_scope": 3,
                    "flash_color": [255, 255, 255, 200], "flash_duration": 6})
    return {"graphic": orbs["graphic"], "graphics": [orbs["graphic"], beam["graphic"]], "hue": 0,
            "frames": frames, "timings": timings}


def find(folder, name, exts):
    """The file `name` names in folder (any case, with or without an extension), or None."""
    if not name or not os.path.isdir(folder):
        return None
    files = {f.lower(): f for f in os.listdir(folder)}
    for cand in [name] + [name + e for e in exts]:
        if cand.lower() in files:
            return os.path.join(folder, files[cand.lower()])
    return None


def main(argv):
    root = argv[0] if argv and os.path.isdir(argv[0]) else ORRE_GAME
    data = rxdata.load(os.path.join(root, "Data", "PkmnAnimations.rxdata"))
    anims, graphics, sounds = {}, set(), set()
    for a in data.attrs.get("array") or data:
        if not isinstance(a, rxdata.RList):
            continue
        name = rxdata.text(a.attrs.get("name"))
        if not name.startswith(KINDS) or name in anims:
            continue
        frames = [[cel(c) for c in f] for f in a.attrs.get("array") or []]
        times = [timing(t) for t in a.attrs.get("timing") or []]
        graphic = rxdata.text(a.attrs.get("graphic"))
        anims[name] = {"graphic": graphic, "hue": a.attrs.get("hue", 0), "frames": frames, "timings": times}
        graphics.add(graphic)
        for t in times:
            (sounds if t["type"] == 0 else graphics).add(t.get("name"))
    anims["Move:FOUNDPOWER"] = found_power(anims)
    os.makedirs(os.path.join(OUT, "graphics"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "sounds"), exist_ok=True)
    copied, missing, size = {}, set(), 0
    for kind, names, folder, exts in (("graphics", graphics, os.path.join(root, "Graphics", "Animations"), (".png",)),
                                      ("sounds", sounds, os.path.join(root, "Audio", "SE", "Anim"),
                                       (".ogg", ".wav", ".mp3", ".WAV")),
                                      ("sounds", sounds, os.path.join(root, "Audio", "SE"),
                                       (".ogg", ".wav", ".mp3", ".WAV"))):
        for n in sorted(x for x in names if x):
            if (kind, n) in copied:
                continue
            src = find(folder, n, exts)
            if src:
                dst = os.path.join(OUT, kind, os.path.basename(src))
                shutil.copyfile(src, dst)
                copied[(kind, n)] = os.path.basename(src)
                size += os.path.getsize(src)
            else:
                missing.add((kind, n))
    missing = {m for m in missing if m not in copied}
    # each animation names its files as copied ("files": graphic / sound name -> file)
    for a in anims.values():
        names = {a["graphic"]} | set(a.get("graphics", [])) | {t.get("name") for t in a["timings"]}
        a["files"] = {n: copied[(k, n)] for k, n in copied if n in names}
    with gzip.open(os.path.join(OUT, "animations.json.gz"), "wt", encoding="utf-8") as f:
        json.dump(anims, f, separators=(",", ":"))
    print(f"{len(anims)} animations, {len(copied)} files ({size / 1e6:.1f} MB), {len(missing)} missing:",
          sorted(n for _, n in missing)[:20])


if __name__ == "__main__":
    main(sys.argv[1:])
