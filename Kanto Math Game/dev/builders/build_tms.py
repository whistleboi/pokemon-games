"""TMs (Jordan, 11-03): Sword/Shield's 100 (TM00-TM99), in every region, reusable (Gen 5 on).

- The list: PokeAPI's machines table (version group sword-shield, the "tmNN" items).
- Who learns each: any Pokemon that can learn the move by TM/TR in any main-series game (PokeAPI's
  pokemon_moves, method "machine"); a regional form uses its species' list.
- Tiers 0-8 by strength (weak first): the Poke Mart sells a TM once the region has that many badges,
  cheaply, so all 100 are on sale by the League; Gym Leaders and route trainers also give them
  (src/pokemon/tms.py).
- Icons: Pokemon Journeys' TM discs, one per type (Graphics/Icons/itemMachine<TYPE>.png), and our grey
  HM disc for every HM.

Writes assets/tms.json {"TM00": {"move", "type", "tier", "price"}} and assets/tm_learners.json
{MOVE: [species ids]}. Run from the game folder:
    python dev/builders/build_tms.py [<PokeAPI CSV folder>] [<Journeys Icons folder>]
"""
import csv
import json
import os
import shutil
import sys

CSV = sys.argv[1] if len(sys.argv) > 1 else os.path.join("dev", "builders", "out", "pokeapi_csv")
ICONS = sys.argv[2] if len(sys.argv) > 2 else os.path.join("..", "..", "Pokemon Journeys V18", "Graphics", "Icons")
ITEMS = os.path.join("assets", "sprites", "items")
SWSH = "sword-shield"
MACHINE = 4
PRICES = [1000, 1000, 1500, 1500, 2000, 2000, 2500, 2500, 3000]  # by tier: cheap (Jordan)
# Story gifts whose move isn't one of Sword/Shield's 100 (Jordan, 11-12): numbered on from TM100, only ever given
# ("gift": never sold or won). Professor Cozmo's thanks after Meteor Falls (ORAS: TM23 Smack Down).
GIFT_TMS = {"TM100": ("SMACK-DOWN", "ORAS TM23: Professor Cozmo, Fallarbor Town"),
            "TM101": ("SWORDS-DANCE", "ORAS TM75: the dancing Black Belt, Lavaridge Town"),
            "TM102": ("FLAME-CHARGE", "ORAS TM43: lying on the Jagged Pass (across the round stones)"),
            "TM103": ("ROCK-POLISH", "ORAS TM69: lying on the Jagged Pass's west hill"),
            "TM104": ("HIDDEN-POWER", "ORAS TM10: Fortree City's old woman and her coin game"),
            "TM105": ("SHADOW-BALL", "ORAS TM30: lying on Mt. Pyre's top floor"),
            "TM106": ("EARTHQUAKE", "ORAS TM26 / Emerald TM26: lying in the Seafloor Cavern"),
            "TM107": ("SCALD", "ORAS TM55: on the island in the Seafloor Cavern's current room"),
            "TM108": ("FROST-BREATH", "ORAS TM79: in Shoal Cave, by the sandy slope")}
# Sold only by the shop that lists them (Jordan, 11-13: match the games): Lilycove Department Store's TM Corner
# (Emerald and ORAS: Fire Blast, Thunder, Blizzard), never on an ordinary Mart's shelf.
SHOP_TMS = {"TM109": ("FIRE-BLAST", "Lilycove Department Store 4F"), "TM110": ("THUNDER", "Lilycove Department Store 4F"),
            "TM111": ("BLIZZARD", "Lilycove Department Store 4F")}


def rows(name):
    with open(os.path.join(CSV, name + ".csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    moves = json.load(open(os.path.join("assets", "moves.json"), encoding="utf-8"))
    vg = {r["identifier"]: int(r["id"]) for r in rows("version_groups")}[SWSH]
    item_name = {int(r["id"]): r["identifier"] for r in rows("items")}
    move_name = {int(r["id"]): r["identifier"].upper() for r in rows("moves")}
    tms = {}
    for r in rows("machines"):
        if int(r["version_group_id"]) != vg:
            continue
        item = item_name.get(int(r["item_id"]), "")
        if not item.startswith("tm"):
            continue  # (the TRs)
        tms[f"TM{int(item[2:]):02d}"] = move_name[int(r["move_id"])]
    missing = [m for m in tms.values() if m not in moves]
    # tiers: by power (status moves count as 55)
    def strength(move):
        d = moves.get(move, {})
        return d.get("power") or 55
    order = sorted(tms, key=lambda k: (strength(tms[k]), k))
    out = {}
    for rank, key in enumerate(order):
        tier = min(8, rank * 9 // len(order))
        move = tms[key]
        out[key] = {"move": move, "type": moves.get(move, {}).get("type", "NORMAL"), "tier": tier,
                    "price": PRICES[tier]}
    for key, (move, where) in GIFT_TMS.items():
        out[key] = {"move": move, "type": moves.get(move, {}).get("type", "NORMAL"), "tier": 8, "price": 3000,
                    "gift": True, "from": where}
        tms[key] = move
    for key, (move, where) in SHOP_TMS.items():
        out[key] = {"move": move, "type": moves.get(move, {}).get("type", "NORMAL"), "tier": 8, "price": 5500,
                    "shop_only": True, "from": where}
        tms[key] = move
    out = dict(sorted(out.items()))

    species_of = {int(r["id"]): int(r["species_id"]) for r in rows("pokemon")}
    wanted = {mid for mid, n in move_name.items() if n in set(tms.values())}
    learners = {}
    for r in rows("pokemon_moves"):
        if int(r["pokemon_move_method_id"]) != MACHINE or int(r["move_id"]) not in wanted:
            continue
        sid = species_of.get(int(r["pokemon_id"]))
        if sid and sid <= 1025:
            learners.setdefault(move_name[int(r["move_id"])], set()).add(sid)
    learners = {m: sorted(s) for m, s in sorted(learners.items())}
    json.dump(out, open(os.path.join("assets", "tms.json"), "w", encoding="utf-8"), indent=1)
    json.dump(learners, open(os.path.join("assets", "tm_learners.json"), "w", encoding="utf-8"),
              separators=(",", ":"))

    for t in {d["type"] for d in out.values()} | {"FAIRY", "NORMAL"}:
        src = os.path.join(ICONS, f"itemMachine{t}.png")
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(ITEMS, f"tm-{t.lower()}.png"))
    shutil.copyfile(os.path.join(ITEMS, "hm-cut.png"), os.path.join(ITEMS, "hm-disc.png"))
    print(f"{len(out)} TMs; moves not in moves.json: {missing}; learner lists: {len(learners)}")
    for tier in range(9):
        print(tier, [f"{k} {v['move']}" for k, v in out.items() if v["tier"] == tier])


if __name__ == "__main__":
    main()
