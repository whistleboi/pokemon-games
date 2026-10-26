"""Every main-series move with its secondary effects (Jordan; effects as pokemondb.net/move/all
lists them), from PokeAPI's CSV tables (github.com/PokeAPI/pokeapi, data/v2/csv): moves, move_meta,
move_meta_stat_changes, move_meta_ailments, move_meta_categories, move_damage_classes, types,
move_targets, move_effect_prose.

assets/moves.json gets, for every move (not Z-Moves, Max Moves or Shadow moves):
  power, accuracy, pp, priority, type, category (PHYSICAL/SPECIAL/STATUS), target,
  category_meta, ailment + ailment_chance, flinch, drain, healing, crit_rate, min/max_hits,
  min/max_turns, stat_changes [[STAT, +/-n]] + stat_chance, effect (the short description).
Moves not in PokeAPI (this game's own) are kept. Run from the game folder:
  python dev/builders/build_move_effects.py <folder with the CSVs>
"""
import csv
import json
import os
import sys

D = sys.argv[1]


def rows(name):
    with open(os.path.join(D, name + ".csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x, default=None):
    return int(x) if x not in ("", None) else default


ail = {int(r["id"]): r["identifier"] for r in rows("move_meta_ailments")}
cat = {int(r["id"]): r["identifier"] for r in rows("move_meta_categories")}
dcls = {int(r["id"]): r["identifier"].upper() for r in rows("move_damage_classes")}
types = {int(r["id"]): r["identifier"].upper() for r in rows("types")}
targets = {int(r["id"]): r["identifier"] for r in rows("move_targets")}
STAT = {2: "ATTACK", 3: "DEFENSE", 4: "SPATK", 5: "SPDEF", 6: "SPEED", 7: "ACCURACY", 8: "EVASION"}
meta = {int(r["move_id"]): r for r in rows("move_meta")}
stat_changes = {}
for r in rows("move_meta_stat_changes"):
    stat_changes.setdefault(int(r["move_id"]), []).append([STAT[int(r["stat_id"])], int(r["change"])])
prose = {int(r["move_effect_id"]): r["short_effect"] for r in rows("move_effect_prose") if r["local_language_id"] == "9"}

# Z-Moves (622-658, 695-703, 719, 723-728) and Max Moves (757-774) only exist with those gimmicks.
Z_OR_MAX = set(range(622, 659)) | set(range(695, 704)) | {719} | set(range(723, 729)) | set(range(757, 775))

M = "assets/moves.json"
moves = json.load(open(M, encoding="utf-8"))
added = updated = 0
for r in rows("moves"):
    mid = int(r["id"])
    if mid >= 10000 or mid in Z_OR_MAX or r["identifier"].startswith(("max-", "g-max-")):
        continue
    name = r["identifier"].upper()
    mm = meta.get(mid, {})
    chance = num(r["effect_chance"])
    effect = prose.get(num(r["effect_id"], 0), "")
    effect = effect.replace("$effect_chance", str(chance or "")).replace("[", "").replace("]{mechanic:", " ")
    effect = " ".join(w.split("}")[-1] if "}" in w else w for w in effect.split())  # "{move:...}" tags
    entry = {
        "accuracy": num(r["accuracy"]), "power": num(r["power"], 0), "pp": num(r["pp"]),
        "priority": num(r["priority"], 0), "type": types.get(num(r["type_id"], 1)),
        "category": dcls.get(num(r["damage_class_id"], 1)), "target": targets.get(num(r["target_id"], 10)),
        "category_meta": cat.get(num(mm.get("meta_category_id"), 0), "damage") if mm else "unique",
        "ailment": ail.get(num(mm.get("meta_ailment_id"), 0), "none"),
        "ailment_chance": num(mm.get("ailment_chance"), 0), "flinch": num(mm.get("flinch_chance"), 0),
        "drain": num(mm.get("drain"), 0), "healing": num(mm.get("healing"), 0),
        "crit_rate": num(mm.get("crit_rate"), 0), "min_hits": num(mm.get("min_hits")),
        "max_hits": num(mm.get("max_hits")), "min_turns": num(mm.get("min_turns")),
        "max_turns": num(mm.get("max_turns")), "stat_changes": stat_changes.get(mid, []),
        "stat_chance": num(mm.get("stat_chance"), 0), "effect": effect.strip().replace("’", "'"),
    }
    if name in moves:
        updated += 1
    else:
        added += 1
    moves[name] = dict(moves.get(name, {}), **entry)
moves = {k: moves[k] for k in sorted(moves)}
json.dump(moves, open(M, "w", encoding="utf-8"), ensure_ascii=False, separators=(", ", ": "))
print(f"{len(moves)} moves: {added} added, {updated} updated")
