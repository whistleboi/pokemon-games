"""Save slots: game_data_0.json .. game_data_{SAVE_SLOTS-1}.json (each may have a .bak).

SAVE_SLOTS is the one place the slot count lives. Slot screens list which files exist with a
single os.listdir() and only open the files of the page on screen; each file's summary is
cached by (mtime, size), so paging back and forth never re-reads an unchanged save.
"""
import os
import re
import time

SAVE_SLOTS = 100

_NAME_RE = re.compile(r"^game_data_(\d+)\.json(\.bak)?$")
_cache = {}  # path -> ((mtime, size, bak_mtime, bak_size), summary)


def folder(game):
    """Where the slot files live: assets.save_dir when the build has one, else the game folder."""
    return getattr(game.assets, "save_dir", None) or game.assets.base_dir


def slot_path(save_dir, index):
    return os.path.join(save_dir, f"game_data_{index}.json")


def slot_index(path):
    """Slot number of a game_data_N.json path, or None (e.g. plain game_data.json)."""
    m = _NAME_RE.match(os.path.basename(path or ""))
    if m and not m.group(2):
        i = int(m.group(1))
        return i if 0 <= i < SAVE_SLOTS else None
    return None


def used_slots(save_dir):
    """Set of slot numbers that have a file or a .bak, from one directory listing."""
    try:
        names = os.listdir(save_dir)
    except OSError:
        return set()
    used = set()
    for n in names:
        m = _NAME_RE.match(n)
        if m and int(m.group(1)) < SAVE_SLOTS:
            used.add(int(m.group(1)))
    return used


def any_saves(save_dir):
    return bool(used_slots(save_dir))


def first_empty(save_dir):
    used = used_slots(save_dir)
    for i in range(SAVE_SLOTS):
        if i not in used:
            return i
    return None


def _stamp(path):
    try:
        st = os.stat(path)
        return st.st_mtime, st.st_size
    except OSError:
        return 0, -1


def _count_badges(badges):
    if isinstance(badges, dict):
        return sum(len(v) for v in badges.values() if isinstance(v, (list, tuple, set)))
    if isinstance(badges, (list, tuple)):
        return len(badges)
    return 0


def summary(save_dir, index):
    """Small dict describing a slot, or None when empty. Cached until the file changes."""
    from src.core.data import DataManager
    path = slot_path(save_dir, index)
    key = _stamp(path) + _stamp(path + ".bak")
    hit = _cache.get(path)
    if hit and hit[0] == key:
        return hit[1]
    if key[1] < 0 and key[3] < 0:
        result = None
    else:
        data, status = DataManager.read_json(path)
        if data is not None:
            story = data.get("story") or {}
            region = story.get("active_badge_region") or story.get("starting_region") or ""
            when = key[0] or key[2]
            result = {
                "name": data.get("save_name", f"File {index + 1}"),
                "area": data.get("save_area", "Unknown"),
                "region": str(region).replace("_", " ").title(),
                "badges": _count_badges(story.get("badges")),
                "saved": time.strftime("%Y-%m-%d %H:%M", time.localtime(when)) if when else "",
                "file": path,
                "restored": status == "restored",
            }
        elif status == "damaged":
            result = {"damaged": True, "file": path}
        else:
            result = None
    _cache[path] = (key, result)
    return result


def forget(path=None):
    """Drop cached summaries (one path, or all)."""
    if path is None:
        _cache.clear()
    else:
        _cache.pop(path, None)
