"""python dev/builders/unova_pwt.py : the Pokemon World Tournament from Black 2's own file (Unova batch 5b, 11-24).

Writes assets/b2_pwt.json, which src/world/pwt.py reads. Found 11-24 (the community's B2W2 file list + reading the files):
- Trainer names: system text 409 (0 Cheren ... 53 Red; then the story's and the regulars' names).
- The Leaders' and Champions' teams: a/2/5/5 (pwttr6: per Trainer u16 placeholder class, u16 count, six set ids; file k is
  name k - 1) with the sets in a/2/5/6 (pwtpoke: 16 bytes each, as the Subway's: species, 4 moves, effort, nature, item,
  form). Six Pokemon each: a Single Battle uses three, a Double four (Bulbapedia: "the first two listed, and one of the
  other four" for Singles; "the first four" for Doubles).
- The Driftveil Tournament's own teams: a/2/5/2 with sets a/2/5/0: file 2-6 Cheren, Roxie, Burgh, Elesa, Clay; files 7,
  8, 9, 11, 12, 13, 14, 21, 22, 23 the ten regulars (X, Makina, Fidel, Theodora, Allan, Jocelyn, Dmitri, Levina, Rylan,
  Destiny: Bulbapedia's order); the first visit's Cheren and Colress are file 1's first and last three, Hugh file 57 (his
  starter's line by yours). The other files are the bracket's filler (never your opponent).
- Who enters which tournament, when each opens, the BP: Bulbapedia's Pokemon World Tournament page (11-24).
Jordan's calls (unova_check/DECISIONS.md "Batch 5 calls"): every tournament, Black 2's levels (Driftveil 25, the rest 50);
facilities have no special rules (11-22): Rental / Mix / Type Expert play as ordinary tournaments with their rosters.
Triple and Rotation Battles are played as Doubles (11-19)."""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import unova_trainers as ut   # noqa: E402  (finds kanto_handoff/unova_map_tools)
import nds5                   # noqa: E402

OUT = os.path.join(ut.GAME, "assets", "b2_pwt.json")
LEADERS = list(range(0, 54))   # (text 409: 0-8 Unova's current Leaders and Bianca, 9-13 the old Leaders, 14-19 Champions, 20-53 the other regions)
DRIFT_FILES = {"Cheren": 2, "Roxie": 3, "Burgh": 4, "Elesa": 5, "Clay": 6, "X": 7, "Makina": 8, "Fidel": 9, "Theodora": 11,
               "Allan": 12, "Jocelyn": 13, "Dmitri": 14, "Levina": 21, "Rylan": 22, "Destiny": 23}
CHAMPIONS = {"Blue", "Lance", "Steven", "Wallace", "Cynthia", "Alder", "Red"}
# Bulbapedia's participants table (11-24): who enters each tournament
UNOVA = ["Cheren", "Roxie", "Burgh", "Elesa", "Clay", "Skyla", "Drayden", "Marlon", "Cilan", "Chili", "Cress", "Lenora", "Brycen"]
KANTO = ["Brock", "Misty", "Lt. Surge", "Erika", "Janine", "Sabrina", "Blaine", "Giovanni"]
JOHTO = ["Falkner", "Bugsy", "Whitney", "Morty", "Chuck", "Jasmine", "Pryce", "Clair"]
HOENN = ["Roxanne", "Brawly", "Wattson", "Flannery", "Norman", "Winona", "Tate", "Liza", "Juan"]
SINNOH = ["Roark", "Gardenia", "Maylene", "Wake", "Fantina", "Byron", "Candice", "Volkner"]
TYPES = {"Brock": "ROCK", "Misty": "WATER", "Lt. Surge": "ELECTRIC", "Erika": "GRASS", "Janine": "POISON", "Sabrina": "PSYCHIC",
         "Blaine": "FIRE", "Giovanni": "GROUND", "Falkner": "FLYING", "Bugsy": "BUG", "Whitney": "NORMAL", "Morty": "GHOST",
         "Chuck": "FIGHTING", "Jasmine": "STEEL", "Pryce": "ICE", "Clair": "DRAGON", "Roxanne": "ROCK", "Brawly": "FIGHTING",
         "Wattson": "ELECTRIC", "Flannery": "FIRE", "Norman": "NORMAL", "Winona": "FLYING", "Tate": "PSYCHIC", "Liza": "PSYCHIC",
         "Juan": "WATER", "Roark": "ROCK", "Gardenia": "GRASS", "Maylene": "FIGHTING", "Wake": "WATER", "Fantina": "GHOST",
         "Byron": "STEEL", "Candice": "ICE", "Volkner": "ELECTRIC", "Cheren": "NORMAL", "Roxie": "POISON", "Burgh": "BUG",
         "Elesa": "ELECTRIC", "Clay": "GROUND", "Skyla": "FLYING", "Drayden": "DRAGON", "Marlon": "WATER", "Cilan": "GRASS",
         "Chili": "FIRE", "Cress": "WATER", "Lenora": "NORMAL", "Brycen": "ICE"}
TOURNAMENTS = [   # key, name, desk (left / right), roster, level, BP (single, double), opens (flags, or "won:<key>"s)
    ("driftveil", "Driftveil Tournament", "left", "driftveil", 25, (1, 1), []),
    ("rental", "Rental Tournament", "left", "driftveil", 50, (1, 1), ["won:driftveil"]),
    ("mix", "Mix Tournament", "left", "driftveil", 50, (1, 1), ["won:driftveil"]),
    ("unova", "Unova Leaders Tournament", "right", UNOVA, 50, (1, 1), ["beat_unova_champion"]),
    ("kanto", "Kanto Leaders Tournament", "right", KANTO, 50, (2, 2), ["won:unova"]),
    ("johto", "Johto Leaders Tournament", "right", JOHTO, 50, (2, 2), ["won:unova"]),
    ("hoenn", "Hoenn Leaders Tournament", "right", HOENN, 50, (2, 2), ["won:unova"]),
    ("sinnoh", "Sinnoh Leaders Tournament", "right", SINNOH, 50, (2, 2), ["won:unova"]),
    ("world", "World Leaders Tournament", "right", UNOVA + KANTO + JOHTO + HOENN + SINNOH, 50, (3, 3),
     ["won:unova", "won:kanto", "won:johto", "won:hoenn", "won:sinnoh"]),
    ("champions", "Champions Tournament", "right", ["Blue", "Lance", "Steven", "Wallace", "Cynthia", "Alder", "Red"], 50, (4, 4),
     ["won10:world"]),
    ("rental_master", "Rental Master Tournament", "right", UNOVA + KANTO + JOHTO + HOENN + SINNOH + ["Bianca"], 50, (2, 2),
     ["won:driftveil", "won:rental", "won:unova", "won:kanto", "won:johto", "won:hoenn", "won:sinnoh"]),
    ("mix_master", "Mix Master Tournament", "right", ["Cheren", "Roxie", "Burgh", "Elesa", "Clay", "Skyla", "Drayden", "Marlon"], 50,
     (2, 2), ["won:driftveil", "won:mix", "won:unova", "won:kanto", "won:johto", "won:hoenn", "won:sinnoh"]),
    ("type", "Type Expert Tournament", "right", "type", 50, (2, 2),
     ["won:driftveil", "won:unova", "won:kanto", "won:johto", "won:hoenn", "won:sinnoh"]),
]


ROTOM_FORMS = {1: "heat", 2: "wash", 3: "frost", 4: "fan", 5: "mow"}   # (11-24: Rotom's appliance by name; the game
FORMED = {479}   #  maps names to its forms. Other species' form values are stray (an Ampharos set's 5): 0)

def _sets(r, narc):
    sp_mv_it = (r.text(nds5.SYSTEXT, 403), r.text(nds5.SYSTEXT, 64))
    mv, it = sp_mv_it
    out = {}
    for i, d in enumerate(r.narc(narc)):
        s, m1, m2, m3, m4, _ev, nature, item, form = struct.unpack("<HHHHHBBHH", d)
        if not s:
            continue
        out[str(i)] = {"species": s, "moves": [mv[m].upper().replace(" ", "-") for m in (m1, m2, m3, m4) if m],
                       "item": it[item].upper().replace(" ", "_").replace("É", "E").replace("'", "") if item else None,
                       "nature": nature, "form": ROTOM_FORMS.get(form, form) if s == 479 else (form if s in FORMED else 0)}
    return out


def _team_file(r, narc, k):
    d = r.narc(narc)[k]
    v = struct.unpack("<%dH" % (len(d) // 2), d)
    return list(v[2:2 + v[1]])


def _pic(name):
    for f in ("b2_%s.png" % name.lower().replace(". ", "_").replace(" ", "_"), "%s.png" % name.lower().replace(". ", "_").replace(" ", "_"),
              {"Lt. Surge": "surge.png", "Wake": "crasher_wake.png", "Giovanni": "fr_leader_giovanni.png",
               "Cilan": "trio_cilan_chili_cress.png", "Chili": "trio_cilan_chili_cress.png",
               "Cress": "trio_cilan_chili_cress.png"}.get(name, "")):
        if f and os.path.isfile(os.path.join(ut.SPRITES, f)):
            return f
    return "leader.png"


def main():
    r = nds5.Rom()
    names = list(r.text(nds5.SYSTEXT, 409))
    trainers = {}
    for i in LEADERS:
        nm = names[i]
        trainers[nm] = {"name": nm, "class": "CHAMPION" if nm in CHAMPIONS else "GYM_LEADER" if nm != "Bianca" else "PKMN_TRAINER",
                        "sprite": _pic(nm), "sets": _team_file(r, "a/2/5/5", i + 1), "pool": "main", "type": TYPES.get(nm)}
    drift = {}
    for nm, k in DRIFT_FILES.items():
        drift[nm] = {"name": nm, "class": "GYM_LEADER" if nm in TYPES else "PKMN_TRAINER", "sprite": _pic(nm) if nm in TYPES else
                     ("b2_ace_trainer_f.png" if nm in ("Makina", "Theodora", "Jocelyn", "Levina", "Destiny") else "b2_ace_trainer_m.png"), "sets": _team_file(r, "a/2/5/2", k), "pool": "drift"}
    first = _team_file(r, "a/2/5/2", 1)
    hugh = _team_file(r, "a/2/5/2", 57)
    story = {"Cheren": {"name": "Cheren", "class": "GYM_LEADER", "sprite": _pic("Cheren"), "sets": first[:3], "pool": "drift"},
             "Colress": {"name": "Colress", "class": "PKMN_TRAINER", "sprite": _pic("Colress"), "sets": first[3:], "pool": "drift"},
             "Hugh": {"name": "{rival_name}", "class": "RIVAL", "sprite": "hugh.png", "sets": hugh, "pool": "drift",
                      "by_starter": {"495": hugh[:2] + [hugh[4]], "498": hugh[:2] + [hugh[5]], "501": hugh[:2] + [hugh[3]]}}}
    tours = []
    for key, name, desk, roster, level, bp, opens in TOURNAMENTS:
        tours.append({"key": key, "name": name, "desk": desk, "roster": roster, "level": level, "bp": list(bp), "opens": opens})
    out = {"_about": "Black 2's Pokemon World Tournament: dev/builders/unova_pwt.py (a/2/5/5 + a/2/5/6 the Leaders and Champions, "
                     "a/2/5/2 + a/2/5/0 the Driftveil Tournament; rosters and BP from Bulbapedia)",
           "trainers": trainers, "drift": drift, "story": story, "tournaments": tours,
           "sets": {"main": _sets(r, "a/2/5/6"), "drift": _sets(r, "a/2/5/0")}}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
    sp = r.text(nds5.SYSTEXT, 90)
    print(len(trainers), "Leaders and Champions,", len(drift), "Driftveil entrants ->", OUT)
    for nm in ("Hugh", "Cheren", "Colress"):
        print(" first visit", nm, [sp[out["sets"]["drift"][str(s)]["species"]] for s in story[nm]["sets"]])
    print(" pictures missing:", sorted({t["sprite"] for t in list(trainers.values()) + list(drift.values()) if t["sprite"] == "leader.png"
                                       or not os.path.isfile(os.path.join(ut.SPRITES, t["sprite"]))}),
          [n for n, t in trainers.items() if t["sprite"] == "leader.png"])


if __name__ == "__main__":
    main()
