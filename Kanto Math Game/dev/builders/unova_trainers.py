"""python dev/builders/unova_trainers.py : each walkable Unova place's trainers from Black 2's own trainer table (11-23).

Reads kanto_handoff/unova_map_tools/utrainers.py (a/0/9/1 + a/0/9/2: class, name, battle kind, team with levels, moves and
held items, Normal mode) for the trainers that stand on each place's zones (people with script 3000 + id; a pair's
second person 5000 + id is the same battle) and writes the area's "trainer_pool" into assets/unova_area_data.json (text
edit, the file's layout kept). Double, triple and rotation battles become double battles (Jordan 11-19). The battle
picture is assets/sprites/trainers/b2_<class>.png when there is one. Add a place to PLACES as its batch is built;
EXTRA adds trainers who aren't standing people (story battles, a crowd's roadblock), by trainer id.
The order in the pool is the zone's people order, so unova.py's trainers={n: name} can name them."""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(os.path.dirname(HERE))


def _tools():
    p = GAME
    for _ in range(6):
        cand = os.path.join(p, "kanto_handoff", "unova_map_tools")
        if os.path.isdir(cand):
            return cand
        p = os.path.dirname(p)
    raise SystemExit("kanto_handoff/unova_map_tools not found above the game folder")


sys.path.insert(0, _tools())
import g5map      # noqa: E402
import utrainers  # noqa: E402

P = os.path.join(GAME, "assets", "unova_area_data.json")
SPRITES = os.path.join(GAME, "assets", "sprites", "trainers")
# area -> zones whose standing trainers it holds (batch 4a, 11-23)
PLACES = {"NIMBASA_CITY": [62, 64, 63, 585], "UNOVA_ROUTE_16": [383], "LOSTLORN_FOREST": [385], "UNOVA_ROUTE_5": [329]}
EXTRA = {"UNOVA_ROUTE_5": [(339, "unova_version:BLACK_2"), (340, "unova_version:WHITE_2")]}   # (Charles at the drawbridge)
CLASS_FIX = {"⒆⒇": "Pokemon", "⑮": "F", "⑭": "M"}   # (the file's PKMN glyph, female / male signs)
# Story and Gym battles that aren't standing trainers: written to town_maps/unova_teams.json {id: entry} for unova.py's _b2(id)
TEAMS = [207, 208, 209, 153,                     # Elesa's Beauties, Elesa
         621, 148,                               # the roller coaster: Rich Boy Rolan, Lady Colette
         47, 803, 10, 804, 138, 805, 136, 806,   # the Ferris wheel's trainers (Nate: spring-winter; Rosa: spring-winter)
         732, 733, 360, 361, 362, 363, 364, 365,  # Ingo, Emmet; Nate and Rosa as partners (by your starter)
         359, 751, 588, 589, 590,                # the Plasma Grunts at Big Stadium; Hugh (by your starter)
         339, 340,                               # Charles at the drawbridge (Black 2: Rotation, White 2: Triple)
         256,                                    # (batch 5a, 11-24) Musician Preston on Route 5 (missed in 4a)
         346, 366, 367, 158,                     # Rood; Charles in Driftveil (Black 2: Triple, White 2: Rotation); Clay
         319, 320, 321, 322, 323, 324, 325]      # Clay's Workers
# Battle pictures where the class slug isn't the file's name (a/0/7/1 slots matched by eye, 11-23; a class without its own
# Black 2 picture keeps the same class from Platinum, never another class's look)
BY_CLASS = {0: "b2_nate.png", 1: "b2_rosa.png", 90: "pt_cyclist_m.png", 91: "pt_cyclist_f.png", 33: "pt_artist.png",
            187: "b2_plasma_grunt_m.png", 188: "b2_plasma_grunt_f.png"}
BY_NAME = {"Elesa": "b2_elesa.png", "Clay": "b2_clay.png", "Emmet": "b2_emmet.png", "Ingo": "b2_ingo.png", "Hugh": "hugh.png"}
TEAMS_OUT = os.path.join(HERE, "town_maps", "unova_teams.json")


def _clean(s):
    for a, b in CLASS_FIX.items():
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s.replace("♂", " M").replace("♀", " F")).strip()


def _slug(cls):
    return re.sub(r"[^a-z0-9]+", "_", cls.lower()).strip("_")


def entry(r, tid, when=None):
    t = utrainers.team(r, tid)
    cls = _clean(t["class"])
    name = _clean(t["name"])
    slug = _slug(cls).replace("pokemon_", "")
    pic = "b2_%s.png" % slug
    pic = BY_CLASS.get(t["class_id"]) or BY_NAME.get(name) or (pic if os.path.isfile(os.path.join(SPRITES, pic)) else f"{slug}.png")
    e = {"name": f"{cls} {name}", "class": slug.upper(), "sprite": pic,
         "team": [m["id"] for m in t["mons"]], "levels": [m["level"] for m in t["mons"]],
         "rewards": {"balls": max(1, min(5, len(t["mons"]) + 1))}, "b2_id": tid}
    names = utrainers._text(r, 403)
    if any(m["moves"] for m in t["mons"]):
        e["movesets"] = {str(m["id"]): [names[x].upper().replace(" ", "-") for x in m["moves"]] for m in t["mons"] if m["moves"]}
    items = utrainers._text(r, 64)
    held = {str(m["id"]): items[m["item"]].upper().replace(" ", "_") for m in t["mons"] if m["item"]}
    if held:
        e["held_items"] = held
    if t["kind"] != "single":
        e["battle_options"] = {"double": True}
    if when:
        e["when_flags"] = [when]
    return e


def pools(Z):
    r = Z.r
    out = {}
    for area, zones in PLACES.items():
        pool, seen = [], set()
        for z in zones:
            for p in Z.events(z)["people"]:
                s = p["script"]
                if 3000 <= s < 5000 and s - 3000 not in seen:
                    seen.add(s - 3000)
                    pool.append(entry(r, s - 3000))
        for tid, when in EXTRA.get(area, []):
            if tid not in seen:
                pool.append(entry(r, tid, when))
        out[area] = pool
    return out


def write(out):
    text = open(P, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in text else "\n"
    data = json.loads(text)["STORY_PROGRESSION"]
    for area, pool in out.items():
        a = data[area]
        a["trainer_pool"] = pool
        block = json.dumps(a, indent=2, ensure_ascii=False).replace("\n", nl + "    ")
        start = text.index('%s    "%s": {' % (nl, area))
        i = start + len(nl) + 4 + len('"%s": ' % area)
        depth, k, ins = 0, i, False
        while True:
            c = text[k]
            if ins:
                if c == "\\":
                    k += 2
                    continue
                if c == '"':
                    ins = False
            elif c == '"':
                ins = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        text = text[:i] + block + text[k + 1:]
    json.loads(text)
    open(P, "w", encoding="utf-8", newline="").write(text)


if __name__ == "__main__":
    Z = g5map.Zones()
    out = pools(Z)
    for area, pool in out.items():
        print(area, [(t["name"], t["levels"], "double" if t.get("battle_options") else "") for t in pool])
    if "--write" in sys.argv:
        write(out)
        old = json.load(open(TEAMS_OUT, encoding="utf-8")) if os.path.isfile(TEAMS_OUT) else {}
        old.update({str(t): entry(Z.r, t) for t in TEAMS})
        with open(TEAMS_OUT, "w", encoding="utf-8") as f:
            json.dump(old, f, indent=1, ensure_ascii=False, sort_keys=True)
        print("wrote", len(out), "areas")
