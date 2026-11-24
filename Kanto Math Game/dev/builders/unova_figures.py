"""python dev/builders/unova_figures.py : give Unova's walkable towns' people their own Black 2 / White 2 walking sheets.

Reads dev/builders/town_maps/unova.py (each person's "_look": "sheet:b2_<who>.png", from the game file's sprite code via
kanto_handoff/unova_map_tools/rmxp_import.py) and writes assets/dungeon_sprites.json "figures" {"AREA:TEXT": {"sheet"}}:
the town screen looks people up there. Only Unova's own entries are added or replaced; the file's layout is kept (text
edit). Run after the importer, whenever people change."""
import importlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))


def looks():
    maps = importlib.import_module("town_maps.unova").MAPS
    out = {}
    for key, m in maps.items():
        places = [m] + list((m.get("rooms") or {}).values())
        for sm in m.get("story_maps") or []:   # (a story map's people and rooms too: the frigate's later visits, 11-24)
            if isinstance(sm.get("map"), dict):
                places += [sm["map"]] + list((sm["map"].get("rooms") or {}).values())
        for place in places:
            for p in place.get("people", []):
                for o in (p if isinstance(p, list) else [p]):
                    if isinstance(o, dict) and str(o.get("_look", "")).startswith("sheet:"):
                        out[f"{key}:{o['text']}"] = {"sheet": o["_look"][6:]}
                    elif isinstance(o, dict) and str(o.get("_look", "")).startswith("pokemon:"):   # (a Pokemon: its follower sheet; the grottoes, 11-23)
                        out[f"{key}:{o['text']}"] = {"pokemon": int(o["_look"][8:])}
    return out


def main():
    want = looks()
    p = os.path.join(HERE, "..", "..", "assets", "dungeon_sprites.json")
    text = open(p, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in text else "\n"
    for k in want:          # (an entry already there: taken out, to be written again)
        text = re.sub(r'%s\s*%s: \{[^{}]*\},' % (re.escape(nl), re.escape(json.dumps(k))), "", text)
    anchor = '"figures": {'
    i = text.index(anchor) + len(anchor)
    text = text[:i] + "".join(f"{nl}    {json.dumps(k)}: {json.dumps(v)}," for k, v in sorted(want.items())) + text[i:]
    json.loads(text)
    open(p, "w", encoding="utf-8", newline="").write(text)
    print(len(want), "Unova people given their own sheets")


if __name__ == "__main__":
    main()
