"""ORAS's trainers and items on the Hoenn maps (Jordan, 11-14: "shoring up those things not in yet ... Make cannon teams").
Where each stands: dev/builders/data/oras_fill.json, written with the trainers, teams and item options
(assets/hoenn_oras.json, laid over hoenn_area_data.json as the game loads) by kanto_handoff/hoenn_rom_tools/oras_fill.py,
from Bulbapedia's ORAS walkthrough and Emerald's own item and trainer spots.

Per area, per floor: "trainers" [[x, y, name, (how they move)]] (an X; the name into trainer_spots), "people" [[x, y, text]] (an N: an
item lying there, or someone who gives one; the text is the area's option), "hidden" {"x,y": item} (found by stepping
there). A map's names go to its N / X tiles in reading order, so each list is rebuilt in that order.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data", "oras_fill.json")


def _put(floor, ch, key, adds):
    """Add [x, y, name] entries as ch tiles, the floor's key list (people / trainer_spots) kept in reading order."""
    rows = [list(r) for r in floor["art"]]
    have = [(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == ch]
    names = list(floor.get(key) or [])
    pairs = list(zip(have, names))
    extra = names[len(have):]   # (names past the tiles: left as they were, after)
    from src.dungeon import art
    for x, y, name, *spec in adds:
        if rows[y][x] not in art.OPEN or rows[y][x] in "NX":   # (open ground, a bridge, the sea for a swimmer)
            print(ascii(f"  oras_fill: {name} at {x},{y} is on {rows[y][x]!r}: left out"))
            continue
        if spec:   # (how they move: the Emerald person's whose spot they stand on (Route 119's Mimic Circle copies you))
            floor.setdefault("moves", {})[f"{x},{y}"] = spec[0]
        rows[y][x] = ch
        pairs.append(((x, y), name))
    pairs.sort(key=lambda p: (p[0][1], p[0][0]))
    floor["art"] = ["".join(r) for r in rows]
    floor[key] = [n for _xy, n in pairs] + extra


def apply(maps):
    if not os.path.exists(DATA):
        return
    plan = json.load(open(DATA, encoding="utf-8"))
    for key, p in plan.items():
        m = maps.get(key)
        if not m:
            continue
        for room, f in (p.get("rooms") or {}).items():   # (a room's own: a Gym's ORAS trainers on its Emerald spots)
            r = (m.get("rooms") or {}).get(room)
            for person in (r or {}).get("people") or []:   # (a Gym trainer already there: ORAS's team and levels)
                t = (f.get("set_battles") or {}).get(person.get("text")) if isinstance(person, dict) else None
                if t and isinstance((person.get("event") or {}).get("battle"), dict):
                    person["event"]["battle"].update(team=list(t["team"]), levels=list(t["levels"]))
                    person["event"]["battle"].pop("movesets", None)
            if r and f.get("people"):
                _put(r, "N", "people", f["people"])
            if r and f.get("moves"):
                r["moves"] = dict(r.get("moves") or {}, **f["moves"])
        floors = m["floors"] if m.get("floors") else [m]
        for i, f in (p.get("floors") or {}).items():
            fl = floors[int(i)]
            for who, x, y, *spec in f.get("move_trainers") or []:   # (an Emerald trainer moved off a spot an ORAS one needs)
                rows = [list(r) for r in fl["art"]]
                xs = [(a, b) for b, r in enumerate(rows) for a, c in enumerate(r) if c == "X"]
                names = list(fl.get("trainer_spots") or [])
                at = next((xy for xy, n in zip(xs, names) if n == who), None)
                if at:
                    rows[at[1]][at[0]] = "."
                    (fl.get("moves") or {}).pop(f"{at[0]},{at[1]}", None)
                    fl["art"] = ["".join(r) for r in rows]
                    fl["trainer_spots"] = [n for n in names if n != who]
                    _put(fl, "X", "trainer_spots", [[x, y, who] + spec])
            if f.get("trainers"):
                _put(fl, "X", "trainer_spots", f["trainers"])
            if f.get("people"):
                _put(fl, "N", "people", f["people"])
            if f.get("hidden"):
                fl["hidden"] = dict(fl.get("hidden") or {}, **f["hidden"])
