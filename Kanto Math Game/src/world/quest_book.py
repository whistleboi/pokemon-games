# [REF-0142: Quest Book]
"""The Quest Book (Jordan, 11-22; kanto_handoff/QUEST_BOOK_DESIGN.md): the Journal's story told as arcs and chapters.

The missions stay as they are (same ids, start conditions, done flags: saves and the scripted playthroughs don't
change). assets/quest_book.json, per region, groups them into arcs and gives each chapter its title and page:

    {"KANTO": [{"title": "The Cascade Badge", "chapters": [
        {"mission": "m3", "title": "Into the Mountain", "say": "..."},
        {"mission": "m8", "steps": [0, 1], "title": "...", "say": "..."},   # (part of a mission: those way-points)
        {"mission": "m16", "title": "...", "done": "beat_champion"}]}]}    # ("done"/"when": the chapter's own)

A chapter's state: "now" (the mission the Journal shows, and for a part, its way-point is the next one), "done" (its
mission's flag / badge, its steps, or its "done"), "open" (its mission could be taken now, but another one is shown),
else not known yet. A chapter not known yet but before one that is done or now was passed ("done"); after it, it is
still to come and shows as "???" (Jordan, 11-22). So a scene changes the story by starting a mission: its chapter
turns up in the arc (Mt. Moon's Rockets, once you've heard of them).

A region with no book yet: every MAIN mission is an arc of its own, its chapters its steps with a "chapter" title."""
import json
import os

_DATA = {}


def table(game):
    key = id(game)
    if key not in _DATA:
        try:
            with open(os.path.join(game.assets.assets_dir, "quest_book.json"), encoding="utf-8") as f:
                _DATA[key] = json.load(f)
        except (OSError, ValueError, TypeError, AttributeError):
            _DATA[key] = {}
    return _DATA[key]


def _ok(story, cond):
    """guide's conditions, plus "beat:AREA:n" (that area's trainer n beaten: Mt. Moon's Jessie and James)."""
    if isinstance(cond, (list, tuple)):
        return all(_ok(story, c) for c in cond)
    if isinstance(cond, dict) and "any" in cond:
        return any(_ok(story, c) for c in cond["any"])
    if isinstance(cond, str) and cond.startswith("beat:"):
        area, _, n = cond[5:].rpartition(":")
        return int(n) in story.defeated_trainers.get(area, set())
    from src.world.guide import _ok as ok
    return ok(story, cond)


def _words(story, text):
    game = getattr(story, "game", None)
    for token, value in (("{rival_name}", getattr(game, "rival_name", None) or "your rival"),
                         ("{player_name}", getattr(game, "player_name", None) or "you")):
        text = str(text or "").replace(token, str(value))
    return text


def _mission_states(game):
    """{mission id: (state, entry)} for the region's missions: "now" (the MAIN the Journal shows), "done", "open"
    (its conditions are met), "unknown"."""
    story = game.story_manager
    shown = {m["id"]: m for m in story.get_active_missions()}
    out = {}
    for m in story.region_missions():
        if m["id"] in shown and str(m.get("type", "")).upper() == "MAIN":
            out[m["id"]] = ("now", dict(shown[m["id"]], status="ACTIVE"))
            continue
        if m.get("completed_badge"):
            done = story.has_badge(m["completed_badge"])
        elif m.get("completed_flag"):
            done = story.mission_flag_done(m)
        else:
            done = False
        entry = dict(story._prepare_mission_for_ui(m), status="COMPLETED" if done else "INACTIVE")
        if done:
            out[m["id"]] = ("done", entry)
        elif story.check_requirements(m.get("condition", {}), region=m.get("region")):
            out[m["id"]] = ("open", entry)
        else:
            out[m["id"]] = ("unknown", entry)
    return out


def _fallback(game, states):
    """No book for the region: each MAIN mission an arc, its chapters its titled steps."""
    story = game.story_manager
    arcs = []
    for m in story.region_missions():
        if str(m.get("type", "")).upper() != "MAIN" or m["id"] not in states:
            continue
        chs, start = [], None
        for i, s in enumerate(m.get("steps") or []):
            if s.get("chapter"):
                if start is not None:
                    chs[-1]["steps"] = list(range(start, i))
                chs.append({"mission": m["id"], "title": s["chapter"], "say": s.get("say")})
                start = i
        if chs:
            chs[-1]["steps"] = list(range(start, len(m.get("steps") or [])))
            if chs[0]["steps"] and chs[0]["steps"][0] > 0:
                chs.insert(0, {"mission": m["id"], "steps": list(range(0, chs[0]["steps"][0]))})
            chs.append({"mission": m["id"], "after_steps": True})
        else:
            chs = [{"mission": m["id"]}]
        arcs.append({"title": m.get("text") or m.get("title"), "chapters": chs})
    return arcs


def arcs(game, region=None):
    """The region's story: [{"title", "state", "chapters": [{"title", "say", "state", "mission" (its entry)}]}],
    every arc, in order (the screen shows the finished ones and the one being played)."""
    story = game.story_manager
    region = str(region or story.get_current_region()).upper()
    states = _mission_states(game)
    book = table(game).get(region) or _fallback(game, states)
    flat = []
    out = []
    taken = set()   # (missions whose "now" chapter is found: later chapters of the same mission come after it)
    for arc in book:
        chs = []
        for c in arc.get("chapters") or []:
            st, entry = states.get(c.get("mission"), ("unknown", None))
            if entry is None and not c.get("done"):
                continue   # (a mission of another region's start, or gone)
            steps = (entry or {}).get("steps") or []
            part = c.get("steps")
            if c.get("after_steps"):
                part = []
            if st == "now" and (part is not None):
                from src.world import guide
                cur = guide.current_step(game, entry)
                idx = next((i for i, s in enumerate(steps) if s is cur), None)
                if c.get("after_steps"):
                    st = "now" if cur is None else "unknown"
                elif idx in part:
                    st = "now"
                elif all(steps[i].get("done") and _ok(story, steps[i]["done"]) for i in part if i < len(steps)):
                    st = "done"
                else:
                    st = "unknown"
            if c.get("done") and _ok(story, c["done"]):
                st = "done"
            if c.get("when") and not _ok(story, c["when"]) and st != "done":
                continue   # (a scene that hasn't happened: the chapter isn't in the book at all, not even as "???")
            if st == "now":
                if c.get("mission") in taken:
                    st = "unknown"
                taken.add(c.get("mission"))
            title = c.get("title") or (entry or {}).get("text") or "?"
            ch = {"title": _words(story, title), "say": _words(story, c.get("say") or (entry or {}).get("desc", "")),
                  "state": st, "mission": entry, "arc": len(out)}
            chs.append(ch)
            flat.append(ch)
        out.append({"title": _words(story, arc.get("title")), "chapters": chs})
    # Passed and still-to-come: a chapter not known yet before the last one done or now was passed.
    last = max((i for i, c in enumerate(flat) if c["state"] in ("done", "now")), default=-1)
    for i, c in enumerate(flat):
        if c["state"] == "unknown":
            c["state"] = "done" if i < last else "later"
        elif c["state"] == "open" and i < last and not any(x["state"] == "now" for x in flat[i:last + 1]):
            c["state"] = "done"
    for a in out:
        s = [c["state"] for c in a["chapters"]]
        a["state"] = ("done" if s and all(x == "done" for x in s) else "now" if "now" in s or (
            "done" in s and any(x != "done" for x in s)) else "later")
    return out


def current(game):
    """(arc, chapter) being played, or (None, None)."""
    for a in arcs(game):
        for c in a["chapters"]:
            if c["state"] == "now":
                return a, c
    return None, None
