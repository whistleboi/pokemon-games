"""Hoenn's own TMs (Jordan, 11-14): Omega Ruby / Alpha Sapphire's numbering, TM01-TM100, and Emerald's TMs whose move
ORAS doesn't have numbered on from TM101. Everywhere else keeps Sword/Shield's (assets/tms.json).

Their items are "HTM01".."HTM1xx" (shown as "TM01 Hone Claws"): their own keys, so a Bag shared between regions (linked
saves) can hold Hoenn's TM34 and another region's TM34 side by side. Like build_tms.py: the list from PokeAPI's
machines table (version groups omega-ruby-alpha-sapphire and emerald), tiers by power for Hoenn's Marts, prices by tier;
the ones the Hoenn story only gives (build_tms.GIFT_TMS's moves) stay gifts, Lilycove's TM Corner's stay shop-only.
Learner lists for moves the game had none for are added to assets/tm_learners.json (any game's TM/TR learners).

Writes assets/tms_hoenn.json. Run from the game folder:
    python dev/builders/build_hoenn_tms.py [<PokeAPI CSV folder>]
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_tms  # noqa: E402

CSV = sys.argv[1] if len(sys.argv) > 1 else os.path.join("dev", "builders", "out", "pokeapi_csv")
ORAS, EMERALD = "omega-ruby-alpha-sapphire", "emerald"
MACHINE = 4


def rows(name):
    with open(os.path.join(CSV, name + ".csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def machines(vg_name, vg, item_name, move_name):
    out = {}
    for r in rows("machines"):
        if int(r["version_group_id"]) != vg[vg_name]:
            continue
        item = item_name.get(int(r["item_id"]), "")
        if item.startswith("tm") and item[2:].isdigit():
            out[int(item[2:])] = move_name[int(r["move_id"])]
    return out


def main():
    moves = json.load(open(os.path.join("assets", "moves.json"), encoding="utf-8"))
    vg = {r["identifier"]: int(r["id"]) for r in rows("version_groups")}
    item_name = {int(r["id"]): r["identifier"] for r in rows("items")}
    move_name = {int(r["id"]): r["identifier"].upper() for r in rows("moves")}
    oras = machines(ORAS, vg, item_name, move_name)
    emerald = machines(EMERALD, vg, item_name, move_name)
    numbered = {n: m for n, m in oras.items()}
    extra = [emerald[n] for n in sorted(emerald) if emerald[n] not in set(oras.values())]
    for i, m in enumerate(extra):
        numbered[101 + i] = m
    gift_moves = {m for m, _w in build_tms.GIFT_TMS.values()}
    shop_moves = {m for m, _w in build_tms.SHOP_TMS.values()}

    def strength(move):
        return moves.get(move, {}).get("power") or 55
    sellable = sorted((n for n, m in numbered.items() if m not in gift_moves and m not in shop_moves),
                      key=lambda n: (strength(numbered[n]), n))
    out = {}
    for n, move in sorted(numbered.items()):
        d = {"move": move, "type": moves.get(move, {}).get("type", "NORMAL"), "number": n}
        if move in gift_moves:
            d.update(tier=8, price=3000, gift=True)
        elif move in shop_moves:
            d.update(tier=8, price=5500, shop_only=True)
        else:
            tier = min(8, sellable.index(n) * 9 // len(sellable))
            d.update(tier=tier, price=build_tms.PRICES[tier])
        d["from"] = "ORAS" if n <= 100 else f"Emerald TM{[k for k, v in emerald.items() if v == move][0]:02d}"
        out[f"HTM{n:02d}"] = d
    json.dump(out, open(os.path.join("assets", "tms_hoenn.json"), "w", encoding="utf-8"), indent=1)

    learners_path = os.path.join("assets", "tm_learners.json")
    learners = json.load(open(learners_path, encoding="utf-8"))
    wanted = {mid for mid, n in move_name.items() if n in set(numbered.values()) and n not in learners}
    species_of = {int(r["id"]): int(r["species_id"]) for r in rows("pokemon")}
    new = {}
    for r in rows("pokemon_moves"):
        if int(r["pokemon_move_method_id"]) != MACHINE or int(r["move_id"]) not in wanted:
            continue
        sid = species_of.get(int(r["pokemon_id"]))
        if sid and sid <= 1025:
            new.setdefault(move_name[int(r["move_id"])], set()).add(sid)
    learners.update({m: sorted(s) for m, s in new.items()})
    json.dump(dict(sorted(learners.items())), open(learners_path, "w", encoding="utf-8"), separators=(",", ":"))
    missing = sorted(m for m in numbered.values() if m not in moves)
    print(f"{len(out)} Hoenn TMs ({len(oras)} ORAS, {len(extra)} Emerald-only: {extra}); learner lists added: {sorted(new)}; "
          f"moves not in moves.json: {missing}")


if __name__ == "__main__":
    main()
