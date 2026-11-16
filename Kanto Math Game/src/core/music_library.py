"""The music library (Jordan, 11-15): every track from the fan games and game files on this PC,
in assets/music/library/gen<N>/<source>/<track>.ogg, listed in assets/music/library/manifest.json.

The audio is built on this PC by dev/builders/build_music_library.py (it is too big for git); the
manifest is kept in git. Only tracks whose file is really there are offered.

Wherever the player picks music, tracks come in this order: by generation (Gen 1 first, then
Gen 2 ... Gen 9, then "Other" for tracks that aren't from a Pokemon game), then alphabetically by
name, then by source. ordered() gives that list; a radio or jukebox should cycle through it.
"""
import json
import os

MANIFEST = os.path.join("music", "library", "manifest.json")
OTHER = 0  # generation 0: not from a Pokemon game (RPG Maker defaults, other games' tunes)
# What the jukebox offers: songs only (Jordan, 11-15). The library also keeps fanfares (me: level up,
# healed, item get; any track under 20 seconds), background loops (bgs: wind, engines) and the sounds.
MUSIC_KINDS = ("bgm",)

_cache = {}


def gen_label(gen):
    return "Other" if gen == OTHER else f"Gen {gen}"


def sort_key(entry):
    """Generation (Other last), then name A-Z (ignoring case and a leading 'The'), then source."""
    gen = entry.get("gen", OTHER)
    name = entry.get("name", "").casefold()
    if name.startswith("the "):
        name = name[4:]
    return (gen == OTHER, gen, name, entry.get("source", ""))


def manifest(assets_dir):
    """The library's manifest (empty when it was never built)."""
    path = os.path.join(assets_dir or "", MANIFEST)
    try:
        stamp = os.path.getmtime(path)
    except OSError:
        return {"tracks": [], "sources": {}}
    hit = _cache.get(path)
    if hit and hit[0] == stamp:
        return hit[1]
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {"tracks": [], "sources": {}}
    _cache[path] = (stamp, data)
    return data


def ordered(assets_dir, kinds=MUSIC_KINDS, gen=None):
    """The library's tracks that are on this PC, by generation then name (see sort_key).
    gen: only that generation (OTHER for 'Other')."""
    root = os.path.join(assets_dir or "", "music", "library")
    out = []
    for t in manifest(assets_dir).get("tracks", []):
        if t.get("kind") not in kinds or (gen is not None and t.get("gen", OTHER) != gen):
            continue
        if os.path.isfile(os.path.join(root, t["file"])):
            out.append(dict(t, path=os.path.join(root, t["file"])))
    out.sort(key=sort_key)
    return out


def generations(tracks):
    """The generations these tracks come from, in cycling order (Gen 1 ... Gen 9, Other)."""
    gens = sorted({t.get("gen", OTHER) for t in tracks}, key=lambda g: (g == OTHER, g))
    return gens


def source_title(assets_dir, key):
    return manifest(assets_dir).get("sources", {}).get(key, {}).get("title", key)
