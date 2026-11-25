"""python dev/builders/unova_towers.py : the Black Tower's and White Treehollow's trainers from Black 2's own file (Unova batch
11b, 11-25) -> assets/unova_towers.json, read by src/world/black_tower.py.

Black 2's tower trainers aren't in its main trainer table. They're a/2/6/2 (661 entries: u16 class, u16 count, then that
many Pokemon-set numbers; entry i's name is system text 53 line i - 1) with the sets in a/2/6/1 (16 bytes each: u16
species, 4 u16 moves, u8, u8, u16 held item, u16). Entries 1-600 come in ten blocks of 60, one block an Area (each pair of
blocks shares a set tier, growing stronger), each block holding both towers' classes; 601-660 are the special classes
(Pokemon Breeders, Rich Boys, Ladies, Gentlemen, Socialites, Doctors, Nurses). Bulbapedia's Black Tower page (read 11-25):
the Black Tower's classes, Areas 1-10's levels (47-50, +3 each Area; two Pokemon of one level), Rich Boy / Lady in Areas
1-5, Gentleman / Socialite in 6-10, a Doctor on every floor; the Boss Trainers (main trainer table 183-202, 504, 505).
The White Treehollow takes the other classes, its Breeders and Nurses in the same places (kanto_handoff notes)."""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import unova_trainers as UT   # noqa: E402  (the file reader, class names, battle pictures)
import nds5                   # noqa: E402
import uitems                 # noqa: E402
import utrainers              # noqa: E402

OUT = os.path.join(UT.GAME, "assets", "unova_towers.json")
BLACK_CLASSES = {"Youngster", "Lass", "School Kid", "Scientist", "Psychic", "Backpacker", "Waiter", "Waitress"}
SPECIAL = {"BLACK": {"Rich Boy": (1, 5), "Lady": (1, 5), "Gentleman": (6, 10), "Socialite": (6, 10), "Doctor": (1, 10)},
           "WHITE": {"Pokemon Breeder": (1, 10), "Pokemon Breeder M": (1, 10), "Pokemon Breeder F": (1, 10), "Nurse": (1, 10)}}
HEALERS = {"Doctor", "Nurse"}
BOSSES = {"BLACK": [184, 186, 188, 190, 192, 194, 196, 198, 200, 201],
          "WHITE": [183, 185, 187, 189, 191, 193, 195, 197, 199, 202]}
AREA10_LATER = {"BLACK": 505, "WHITE": 504}   # (Janna / Jariel: Area 10's boss once Benga's been beaten)


def main():
    r = nds5.Rom()
    cls = r.text(nds5.SYSTEXT, uitems.TRAINER_CLASSES)
    names = r.text(nds5.SYSTEXT, 53)
    species = r.text(nds5.SYSTEXT, 90)
    moves = r.text(nds5.SYSTEXT, 403)
    items = r.text(nds5.SYSTEXT, 64)
    T, S = r.narc("a/2/6/2"), r.narc("a/2/6/1")

    def sset(k):
        sp, m1, m2, m3, m4, _a, item, _f = struct.unpack_from("<6H2H", S[k] + b"\0" * 16)[:8]
        out = {"id": sp, "moves": [moves[m].upper().replace(" ", "-") for m in (m1, m2, m3, m4) if m]}
        name = items[item] if 0 < item < len(items) else ""
        if name.endswith("Berry"):
            out["item"] = name.upper().replace(" ", "_")
        return out

    def trainer(i):
        v = struct.unpack_from("<%dH" % (len(T[i]) // 2), T[i])
        c = UT._clean(cls[v[0]])
        slug = UT._slug(c).replace("pokemon_", "")
        pic = UT.BY_CLASS.get(v[0]) or ("b2_%s.png" % slug if os.path.isfile(os.path.join(UT.SPRITES, "b2_%s.png" % slug))
                                        else "%s.png" % slug)
        return c, {"name": "%s %s" % (c, UT._clean(names[i - 1])), "class": slug.upper(), "sprite": pic,
                   "sets": list(v[2:2 + v[1]])}

    out = {}
    for tower in ("BLACK", "WHITE"):
        areas = {}
        for n in range(1, 11):
            block = [trainer(i) for i in range(1 + 60 * (n - 1), 61 + 60 * (n - 1))]
            mine = [t for c, t in block if (c in BLACK_CLASSES) == (tower == "BLACK")]
            pool = {s for t in mine for s in t["sets"]}
            spec, healers = [], []
            for i in range(601, 661):
                c, t = trainer(i)
                lo_hi = SPECIAL[tower].get(c)
                if not lo_hi or not lo_hi[0] <= n <= lo_hi[1]:
                    continue
                inside = [s for s in t["sets"] if s in pool]
                t["sets"] = inside or t["sets"]
                (healers if c in HEALERS else spec).append(t)
            used = {s for t in mine + spec + healers for s in t["sets"]}
            lo = 47 + 3 * (n - 1)
            boss = UT.entry(r, BOSSES[tower][n - 1])
            boss["is_boss_battle"] = True
            area = {"levels": [lo, lo + 3], "trainers": mine + spec, "healers": healers, "boss": boss,
                    "sets": {str(s): sset(s) for s in sorted(used) if s < len(S)}}
            if n == 10:
                later = UT.entry(r, AREA10_LATER[tower])
                later["is_boss_battle"] = True
                area["boss_later"] = later
            areas[str(n)] = area
        out[tower] = areas
    # (each class's walking sheet: where Black 2 already stands a trainer of that class in Unova - its sheet exists)
    import g5map
    Z = g5map.Zones()
    sheets = os.path.join(UT.GAME, "assets", "dungeon", "characters")
    looks = {}
    for z in range(len(Z.heads)):
        try:
            people = Z.events(z)["people"]
        except Exception:
            continue
        for p in people:
            s = p["script"]
            if 3000 <= s < 5000:
                try:
                    t = utrainers.team(r, s - 3000)
                except Exception:
                    continue
                key = UT._slug(UT._clean(t["class"])).replace("pokemon_", "").upper()
                f = "b2_c%d.png" % p.get("sprite", 0)
                if key not in looks and os.path.isfile(os.path.join(sheets, f)):
                    looks[key] = "sheet:" + f
    out["looks"] = looks
    json.dump(out, open(OUT, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    need = {t["class"] for tw in ("BLACK", "WHITE") for a in out[tw].values() for t in a["trainers"] + a["healers"]}
    print("classes without a walking sheet:", sorted(need - set(looks)))
    for tower, areas in ((k, v) for k, v in out.items() if k != "looks"):
        print(tower, [(n, len(a["trainers"]), len(a["healers"]), a["boss"]["name"], len(a["sets"])) for n, a in areas.items()])
    print("wrote", OUT, os.path.getsize(OUT))


if __name__ == "__main__":
    main()
