"""Black 2's Battle Subway from the game file (Unova batch 4b, 11-23) -> assets/b2_subway.json.

    python dev/builders/unova_subway.py

What the file holds (read with kanto_handoff/unova_map_tools; the record layouts are the Gen 5 editors' "bsubway" ones):
- a/2/1/2: the Subway's 314 Trainers, each u16 class, u16 count, then that many u16 Pokemon-set ids (their pool).
  Names: system text 15 (Trainer i is name i - 1). 1-300 the line Trainers; 301-306 Nate / Rosa, the Multi Train's partners
  (three pools each); 307-314 the Subway Bosses: Ingo (singles: normal / Super), Emmet (doubles: normal / Super), and both
  for the Multi Trains (two each: normal / Super).
- a/2/1/1: 1,000 Pokemon sets, 16 bytes: u16 species, u16 x4 moves, u8 effort flags, u8 nature, u16 held item, u16 form.
- overlay 12 at 0x216d9a8: 56 (class, overworld sprite) pairs: how each class looks walking into the car.
Battle pictures: a/0/7/1 slots matched by eye 11-23 (school kids 4/5, waiter 8, waitress 9, nursery aide 13, preschoolers
14 F / 15 M, fisherman 29, psychics 35/36, pilot 43, black belt 50, janitor 57, Pokefans 58/59, nurse 61, battle girl 63,
parasol lady 64, biker 71: the animated ones from their parts sheet). Clerk (F) not found yet: the default picture.
Who appears when (the community's tables, altissimo1's Battle Subway pages, 11-23): line Trainers 1-110 ride the normal
trains, 111-300 the Super trains, by the battle's number in the streak (RANGES below). Every Pokemon at Lv 50 (Black 2's
rule; Jordan 11-23: "Lv 50, as Black 2")."""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import unova_trainers as ut   # noqa: E402  (finds and loads the tools; the class names and battle pictures' rules)
import nds5                   # noqa: E402
import overlays               # noqa: E402
import uitems                 # noqa: E402

OUT = os.path.join(ut.GAME, "assets", "b2_subway.json")
CHARS = os.path.join(ut.GAME, "assets", "dungeon", "characters")
OBJ_TABLE = 0x216d9a8, 56   # (overlay 12: class -> overworld sprite)
# battle number in the streak (1-based) -> the Trainer ids who may appear; the 7th of a train is the "boss" of the train
# (normal: 1-110; Super: 111-300). Past the last row the last row holds.
RANGES = {
    "normal": [(1, 6, [(1, 50)]), (7, 7, [(51, 70)]), (8, 13, [(1, 70)]), (14, 14, [(71, 110)]), (15, 20, [(51, 110)]),
               (21, 21, [(71, 110)]), (22, 999, [(71, 110)])],
    "super": [(1, 6, [(111, 160)]), (7, 7, [(161, 180)]), (8, 13, [(111, 180)]), (14, 14, [(181, 200)]), (15, 20, [(161, 200)]),
              (21, 21, [(201, 220)]), (22, 27, [(181, 220)]), (28, 28, [(221, 300)]), (29, 999, [(201, 300)])],
}
BOSSES = {"single": (307, 308), "double": (309, 310), "multi": ((311, 312), (313, 314))}   # (normal, Super)
PARTNERS = {"nate": (301, 302, 303), "rosa": (304, 305, 306)}


def _obj(r):
    for oid, ram, d in overlays.overlays(r):
        if oid == 12:
            a = OBJ_TABLE[0] - ram
            return {c: code for c, code in (struct.unpack_from("<HH", d, a + 4 * i) for i in range(OBJ_TABLE[1]))}
    return {}


def main():
    r = nds5.Rom()
    sets_raw, trainers_raw = r.narc("a/2/1/1"), r.narc("a/2/1/2")
    names = r.text(nds5.SYSTEXT, 15)
    cls_text = r.text(nds5.SYSTEXT, uitems.TRAINER_CLASSES)
    species_text, moves_text, items_text = (r.text(nds5.SYSTEXT, i) for i in (90, 403, 64))
    obj = _obj(r)
    sets = {}
    for i, d in enumerate(sets_raw):
        sp, m1, m2, m3, m4, _ev, nature, item, form = struct.unpack("<HHHHHBBHH", d)
        if not sp:
            continue
        sets[str(i)] = {"species": sp, "moves": [moves_text[m].upper().replace(" ", "-") for m in (m1, m2, m3, m4) if m],
                        "item": items_text[item].upper().replace(" ", "_").replace("É", "E").replace("'", "") if item else None,
                        "nature": nature, "form": form}
    trainers = {}
    for i, d in enumerate(trainers_raw):
        if i == 0 or len(d) < 4:
            continue
        c, n = struct.unpack_from("<HH", d, 0)
        pool = list(struct.unpack_from("<%dH" % n, d, 4))
        cls = ut._clean(cls_text[c])
        name = ut._clean(names[i - 1]) if i - 1 < len(names) else ""
        slug = ut._slug(cls.replace("é", "e")).replace("pokemon_", "")
        code = obj.get(c)
        # (a class name shared by a man's and a woman's class: the lower overworld code is the man's, as every pair shows)
        twin = [k for k, t in enumerate(cls_text) if k != c and ut._clean(t) == cls and obj.get(k)]
        sex = ("_m" if not code or code < obj[twin[0]] else "_f") if twin else ""
        pic = next((f for f in ("b2_%s%s.png" % (slug, sex), "b2_%s.png" % slug) if os.path.isfile(os.path.join(ut.SPRITES, f))), None)
        pic = ut.BY_CLASS.get(c) or ut.BY_NAME.get(name) or pic or f"{slug}.png"
        walk = "b2_c%d.png" % code if code else None
        trainers[str(i)] = {"name": f"{cls} {name}".strip(), "class": slug.upper(), "class_id": c, "sprite": pic,
                            "walk": walk, "pool": [p for p in pool if str(p) in sets]}
    out = {"_about": "Black 2's Battle Subway (a/2/1/1 sets, a/2/1/2 Trainers, overlay 12 looks): dev/builders/unova_subway.py",
           "level": 50, "ranges": RANGES, "bosses": BOSSES, "partners": PARTNERS, "trainers": trainers, "sets": sets}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    need = sorted({t["walk"] for t in trainers.values() if t["walk"] and not os.path.isfile(os.path.join(CHARS, t["walk"]))})
    print(len(trainers), "Trainers,", len(sets), "sets ->", OUT)
    print("walking sheets still to make:", need)
    print("battle pictures missing:", sorted({t["sprite"] for t in trainers.values()
                                               if not os.path.isfile(os.path.join(ut.SPRITES, t["sprite"]))}))
    print("species:", len({s["species"] for s in sets.values()}), "e.g.", species_text[sets["1"]["species"]])


if __name__ == "__main__":
    main()
