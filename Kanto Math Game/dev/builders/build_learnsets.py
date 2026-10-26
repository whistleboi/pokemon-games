"""Latest learnsets: every species (#1-1025) gets its level-up moves from the newest main-series game
it appears in: Scarlet/Violet (+ DLC), else Sword/Shield (+ DLC), else BDSP, USUM, SM, ORAS, XY,
B2W2, BW, HGSS, Pt, DP, FRLG, E, RS, Crystal, GS, Yellow, RB. Legends: Arceus/Z-A, Let's Go and
Champions are skipped (different battle systems). Moves missing from assets/moves.json are added in
its format. Custom learnsets (ids above 1025, e.g. Crystal Onix 9201) are kept.

Data: PokeAPI's CSV tables (github.com/PokeAPI/pokeapi, data/v2/csv): pokemon_moves, moves,
move_meta, move_meta_ailments, move_meta_categories, move_damage_classes, types, version_groups.
Run from the game folder:  python dev/builders/build_learnsets.py <folder with the CSVs>
"""
import csv
import json
import os
import sys

D = sys.argv[1]


def rows(name):
    with open(os.path.join(D, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


vg = {r["identifier"]: int(r["id"]) for r in rows("version_groups.csv")}
ORDER = [["scarlet-violet", "the-teal-mask", "the-indigo-disk"], ["sword-shield", "the-isle-of-armor", "the-crown-tundra"],
         ["brilliant-diamond-shining-pearl"], ["ultra-sun-ultra-moon"], ["sun-moon"], ["omega-ruby-alpha-sapphire"],
         ["x-y"], ["black-2-white-2"], ["black-white"], ["heartgold-soulsilver"], ["platinum"], ["diamond-pearl"],
         ["firered-leafgreen"], ["emerald"], ["ruby-sapphire"], ["crystal"], ["gold-silver"], ["yellow"], ["red-blue"]]
ORDER = [[vg[n] for n in fam if n in vg] for fam in ORDER]
LEVEL_UP = 1

move_rows = {int(r["id"]): r for r in rows("moves.csv")}
name_of = {i: r["identifier"].upper() for i, r in move_rows.items()}

by_species = {}  # pid -> vgid -> [(level, move)]
for r in rows("pokemon_moves.csv"):
    if int(r["pokemon_move_method_id"]) != LEVEL_UP:
        continue
    pid = int(r["pokemon_id"])
    if pid > 1025:
        continue
    lvl = max(1, int(r["level"] or 0))  # 0 = learned on evolving: available from the start
    by_species.setdefault(pid, {}).setdefault(int(r["version_group_id"]), []).append((lvl, int(r["move_id"])))

learnsets, source = {}, {}
for pid, groups in by_species.items():
    for fam in ORDER:
        got = [x for g in fam for x in groups.get(g, [])]
        if got:
            seen, out = set(), []
            for lvl, mid in sorted(got):
                if mid not in seen:
                    seen.add(mid)
                    out.append([lvl, name_of[mid]])
            learnsets[str(pid)] = out
            source[pid] = fam[0]
            break

P = "assets/pokemon_levels.json"
data = json.load(open(P, encoding="utf-8"))
old = data.get("learnsets", {})
for k, v in old.items():  # keep custom forms' learnsets and anything PokeAPI lacks
    if k not in learnsets:
        learnsets[k] = v
# Evolutions that need a move ("Dipplin knowing Dragon Cheer"): the game has no TMs or tutors, so the
# move must be in the learnset (its old level if it had one, else level 1).
for pair, rule in data.get("pairs", {}).items():
    need = rule.get("move")
    src = pair.split(">")[0]
    if need and src in learnsets and need not in {m for _, m in learnsets[src]}:
        lvl = next((max(1, int(l)) for l, m in old.get(src, []) if m == need), 1)
        learnsets[src] = sorted(learnsets[src] + [[lvl, need]], key=lambda x: x[0])
        print(f"evolution move kept: #{src} {need} at Lv {lvl}")
data["learnsets"] = {k: learnsets[k] for k in sorted(learnsets, key=int)}
json.dump(data, open(P, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# Moves the new learnsets use that moves.json lacks.
M = "assets/moves.json"
moves = json.load(open(M, encoding="utf-8"))
meta = {int(r["move_id"]): r for r in rows("move_meta.csv")}
ail = {int(r["id"]): r["identifier"] for r in rows("move_meta_ailments.csv")}
cat = {int(r["id"]): r["identifier"] for r in rows("move_meta_categories.csv")}
dcls = {int(r["id"]): r["identifier"].upper() for r in rows("move_damage_classes.csv")}
types = {int(r["id"]): r["identifier"].upper() for r in rows("types.csv")}
by_name = {v: k for k, v in name_of.items()}


def num(x, default=None):
    return int(x) if x not in ("", None) else default


added = []
for name in sorted({m for v in learnsets.values() for _, m in v} - set(moves)):
    mid = by_name.get(name)
    if mid is None:
        continue
    r, mm = move_rows[mid], meta.get(mid, {})
    moves[name] = {"accuracy": num(r["accuracy"]), "ailment": ail.get(num(mm.get("meta_ailment_id"), 0), "none"),
                   "ailment_chance": num(mm.get("ailment_chance"), 0), "category": dcls.get(num(r["damage_class_id"], 1)),
                   "category_meta": cat.get(num(mm.get("meta_category_id"), 0), "damage"),
                   "crit_rate": num(mm.get("crit_rate"), 0), "drain": num(mm.get("drain"), 0),
                   "flinch": num(mm.get("flinch_chance"), 0), "healing": num(mm.get("healing"), 0),
                   "max_hits": num(mm.get("max_hits")), "min_hits": num(mm.get("min_hits")),
                   "power": num(r["power"], 0), "priority": num(r["priority"], 0), "type": types.get(num(r["type_id"], 1))}
    added.append(name)
moves = {k: moves[k] for k in sorted(moves)}
json.dump(moves, open(M, "w", encoding="utf-8"), ensure_ascii=False, separators=(", ", ": "))

from collections import Counter  # noqa: E402
names = {v: k for k, v in vg.items()}
print("species:", len(source), "from:", dict(Counter(names[g] for g in source.values()).most_common()))
print("moves added to moves.json:", len(added), added[:25])
