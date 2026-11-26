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
PLACES = {"NIMBASA_CITY": [62, 64, 63, 585], "UNOVA_ROUTE_16": [383], "LOSTLORN_FOREST": [385], "UNOVA_ROUTE_5": [329],
          "RELIC_PASSAGE": [503], "RELIC_PASSAGE_MIDDLE": [504], "RELIC_PASSAGE_NORTH": [505],   # (batch 5b, 11-24)
          "UNOVA_ROUTE_6": [331], "MISTRALTON_CAVE": [333], "MISTRALTON_CAVE_2F": [334],   # (batch 6a, 11-24)
          "CHARGESTONE_CAVE": [195], "CHARGESTONE_CAVE_B1F": [196], "CHARGESTONE_CAVE_B2F": [197],
          "UNOVA_ROUTE_7": [337], "CELESTIAL_TOWER_2F": [339], "CELESTIAL_TOWER_3F": [340], "CELESTIAL_TOWER_4F": [341],   # (batch 6b)
          "REVERSAL_MOUNTAIN": [461],   # (batch 7a: the mountainside's Cyclists; inside, each version's own chamber)
          "REVERSAL_MOUNTAIN_INSIDE": [(533, "unova_version:BLACK_2"), (539, "unova_version:WHITE_2")],
          "UNOVA_ROUTE_13": [370], "UNDELLA_BAY": [240],   # (batch 7b)
          "UNOVA_ROUTE_12": [368], "VILLAGE_BRIDGE": [255], "UNOVA_ROUTE_11": [365],   # (batch 8a)
          "UNOVA_ROUTE_9": [348],   # (batch 8b)
          "UNOVA_ROUTE_22": [474], "UNOVA_ROUTE_21": [463], "SEASIDE_CAVE": [515], "SEASIDE_CAVE_B1F": [516],   # (batch 9a)
          "UNOVA_ROUTE_23": [475], "VICTORY_ROAD_CAVE_1F": [587], "VICTORY_ROAD_GROVE": [588], "VICTORY_ROAD_RIVER": [589, 595],
          "VICTORY_ROAD_CAVE_2F": [590], "VICTORY_ROAD_MOUNTAINSIDE": [592], "VICTORY_ROAD_3F": [593],
          "UNOVA_ROUTE_14": [374], "ABUNDANT_SHRINE": [376], "UNOVA_ROUTE_15": [378],
          "PINWHEEL_FOREST": [155], "PINWHEEL_FOREST_OUTSIDE": [154], "UNOVA_ROUTE_3": [321], "WELLSPRING_CAVE": [324],
          "WELLSPRING_CAVE_B1F": [325],
          "DREAMYARD": [152], "DREAMYARD_B1F": [153], "UNOVA_ROUTE_2": [319], "UNOVA_ROUTE_1": [317],
          "UNOVA_ROUTE_8": [345], "MOOR_OF_ICIRRUS": [346], "TUBELINE_BRIDGE": [254]}   # (batch 10a: each version's
          #  people share the zone's trainers; the River Valley's two versions hold different ones)
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
         319, 320, 321, 322, 323, 324, 325,      # Clay's Workers
         368, 369, 370, 371,                     # (batch 5b) the Plasma Frigate: Hugh as your partner (by your starter), Cheren
         372, 373, 374, 375, 376, 377,           # the Frigate's Grunts: two alone, then two pairs (with Cheren, with Hugh)
         149, 150, 151, 152, 332,                # (batch 6b) Skyla's Pilots
         515, 518, 390, 391,                     # (batch 7a) Rangers Lewis / Eliza in the side chambers; the Strange House's Boone, Lynette
         701, 702, 703, 704, 705,                # (batch 7b) Lacunosa: Hugh as your partner (by your starter), Zinzolin, his Grunt
         177, 335,                               # (batch 8a) Village Bridge: Gentleman Stonewall's 1,000th battle; Baker Chris
         381, 382, 383, 384, 385, 159,           # Drayden's Veterans (Lucius; Jerry / Rhona; Ron / Denae) and Drayden
         585, 586, 587, 584, 583,                # Opelucid frozen: three Grunts, Zinzolin, the Shadow Triad
         12, 11,                                 # (batch 8b) Shopping Mall Nine: Waitress Olwen, Waiter Lou
         350, 351, 352, 353, 354, 355, 160, 580,  # (batch 9a) Marlon's Ace Trainers, Marlon; Black Belt Rocky (Seaside Cave)
         794, 795, 796, 500, 798, 799, 347, 724,  # (batch 9b-1) the frigate: Hugh (by starter), the deck's Grunt, the North
         800, 801, 802, 812, 426, 427, 343, 436,  # Entrance's pair, Zinzolin and his Grunt; the hall's and rooms' Grunts
         429, 428, 437,
         797, 440, 807, 809, 497, 344, 348, 498, 499, 345,   # (batch 9b-2) the Chasm: the forest's pair (with Hugh), the stern,
         430, 431, 432, 433, 434, 435, 438, 439, 808, 810, 811,   # Zinzolin, Colress, the Shadow Triad, Ghetsis; Kyurem's room:
         445, 446, 447, 448, 449, 452, 453, 454,
         684, 685, 686,   # (batch 10a) Hugh in Victory Road's tunnel (by your starter)
         38, 40, 41, 39, 341, 143, 145, 146, 144, 536,   # (batch 10b) the Elite Four and Iris; their rematches
         693, 694, 695, 696, 697, 698, 456,   # (batch 11a)
         5, 6, 782, 783, 784, 785, 494, 495, 496, 687, 688, 689]   # (batch 12b) the Shadow Triad in Icirrus: single, triple, rotation (played as doubles);   # (batch 12a) Chili, Cress, Cilan: the Striaton Restaurant's daily Multi Battle;   # (batch 11c) N: Zekrom (Black 2) / Reshiram (White 2); his seasonal rematches. (11a) Hugh in Undella and once a day after; Cynthia   # Black 2's Grunts and Doctor; White 2's password Grunts, the card's
# Battle pictures where the class slug isn't the file's name (a/0/7/1 slots matched by eye, 11-23; a class without its own
# Black 2 picture keeps the same class from Platinum, never another class's look)
BY_CLASS = {0: "b2_nate.png", 1: "b2_rosa.png", 90: "pt_cyclist_m.png", 91: "pt_cyclist_f.png", 33: "pt_artist.png",
            # (11-24: classes the file names without a gender sign; the class number says which: Black 2's own pictures)
            27: "b2_backpacker_m.png", 28: "b2_backpacker_f.png", 52: "b2_scientist_m.png", 46: "b2_scientist_f.png",
            35: "b2_psychic_m.png", 36: "b2_psychic_f.png",
            187: "b2_plasma_grunt_m.png", 188: "b2_plasma_grunt_f.png"}
BY_NAME = {"Elesa": "b2_elesa.png", "Clay": "b2_clay.png", "Skyla": "b2_skyla.png", "Emmet": "b2_emmet.png", "Ingo": "b2_ingo.png", "Hugh": "hugh.png"}
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
    names = utrainers._text(r, __import__("nds5").P["MOVES"])
    if any(m["moves"] for m in t["mons"]):
        e["movesets"] = {str(m["id"]): [names[x].upper().replace(" ", "-") for x in m["moves"]] for m in t["mons"] if m["moves"]}
    items = utrainers._text(r, __import__("nds5").P["ITEMS"])
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
        for z in zones:   # (a zone, or (zone, condition): a version's own layout, its trainers tagged with when_flags, 11-24)
            z, when = z if isinstance(z, tuple) else (z, None)
            for p in Z.events(z)["people"]:
                s = p["script"]
                if 3000 <= s < 5000 and (s - 3000, when) not in seen:
                    seen.add((s - 3000, when))
                    pool.append(entry(r, s - 3000, when))
        for tid, when in EXTRA.get(area, []):
            if (tid, None) not in seen and (tid, when) not in seen:
                pool.append(entry(r, tid, when))
        out[area] = pool
    return out


# Black 2's tag battles (batch 12a, 11-25): two trainers who battle you (and the partner walking with you) together - the
# lead's pool entry carries the second as "second_trainer" and the pair's own flag; the second trainer drops out of the pool.
PAIRS = {"PINWHEEL_FOREST": [(790, 791, "b2_pw_pair_1"), (793, 792, "b2_pw_pair_2")]}


def pair_up(r, out):
    for area, pairs in PAIRS.items():
        pool = out.get(area) or []
        for lead, second, flag in pairs:
            a = next((t for t in pool if t.get("b2_id") == lead), None)
            b = next((t for t in pool if t.get("b2_id") == second), None)
            if a is None or b is None:
                continue
            a["battle_options"] = {"double": True, "second_trainer": {k: v for k, v in b.items() if k != "b2_id"}}
            a["victory_flag"] = flag
            pool.remove(b)
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


# Unova two years ago (batch 12c, 11-25): --white reads Pokemon White's own trainers into the past's areas, and its story /
# Gym battles into town_maps/unova_teams_w1.json (the builder's _w1(id)).
PLACES_W1 = {"PAST_UNOVA_ROUTE_1": [317], "PAST_UNOVA_ROUTE_2": [319], "PAST_DREAMYARD": [152], "PAST_DREAMYARD_B1F": [153],
             "PAST_UNOVA_ROUTE_3": [321], "PAST_WELLSPRING_CAVE_B1F": [325], "PAST_PINWHEEL_FOREST_OUTSIDE": [154],
             "PAST_PINWHEEL_FOREST": [155],
             "PAST_UNOVA_ROUTE_4": [326], "PAST_DESERT_RESORT": [158], "PAST_RELIC_CASTLE": [160]}
TEAMS_W1 = [9, 10, 21, 196, 198, 66, 68]   # (the Striaton Gym's Waiter Maxwell and Waitress Tia)

if __name__ == "__main__":
    import nds5
    Z = g5map.Zones()
    if nds5.GAME == "W1":
        PLACES, TEAMS, PAIRS = PLACES_W1, TEAMS_W1, {}
        TEAMS_OUT = os.path.join(HERE, "town_maps", "unova_teams_w1.json")
    out = pair_up(Z.r, pools(Z))
    for area, pool in out.items():
        print(area, [(t["name"], t["levels"], "double" if t.get("battle_options") else "") for t in pool])
    if "--write" in sys.argv:
        write(out)
        old = json.load(open(TEAMS_OUT, encoding="utf-8")) if os.path.isfile(TEAMS_OUT) else {}
        old.update({str(t): entry(Z.r, t) for t in TEAMS})
        with open(TEAMS_OUT, "w", encoding="utf-8") as f:
            json.dump(old, f, indent=1, ensure_ascii=False, sort_keys=True)
        print("wrote", len(out), "areas")
