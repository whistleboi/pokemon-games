"""TMs: one list for every region, on Scarlet/Violet's numbers (Jordan, 11-17: "1 numbering scheme ... in all regions",
"every TM that has ever been available is available", "Do scarlet numbering").

- TM001-TM229: Scarlet/Violet's TMs by their own numbers (its DLC's TM172-TM229 too), from PokeAPI's machines table
  (version groups scarlet-violet, the-teal-mask, the-indigo-disk).
- TM230 on: every other move that has been a TM in a main-series game (never in Scarlet/Violet), newest game first,
  in that game's TM order (Brilliant Diamond/Shining Pearl, Sword/Shield, Let's Go, ... Red/Blue).
- Then the TMs only Legends: Z-A has (its Mega Dimension DLC's too), in Z-A's own TM order (Jordan, 11-17: "Add the
  LZA tms in sequence after the standard ones"). A move Z-A shares with an older game goes by that game.
- Reusable; one of each in a Bag (src/world/story.py Bag); owning one puts its move in the move pool of every Pokemon
  that can learn it (src/pokemon/moves.py).
- Who learns each: any Pokemon that can learn the move by TM/TR in any main-series game (PokeAPI's pokemon_moves,
  method "machine"); a regional form uses its species' list.
- Tiers 0-8 by strength (weak first), over the whole list: the Poke Marts sell a TM once the region has that many
  badges, cheaply, so every one is on sale by the League; Gym Leaders and route trainers also give them, and the
  story's TM spots (the games' item balls and gifts) hand out the same moves under these numbers
  (src/pokemon/tms.py).
- Who learns the Z-A-only TMs: our PokeAPI copy has no Z-A learnsets, so dev/builders/data/za_tm_learners.json
  (Serebii's Legends: Z-A TM pages, 11-17) gives them.
- assets/tm_legacy.json: the old keys (Sword/Shield's TM00-TM99, the story's TM100-TM141, Hoenn's HTM01-HTM1xx) and
  their moves, and "v1:TM230".. the first Scarlet/Violet list's TM230-TM348 (Z-A's first), for converting older
  saves (StoryManager._migrate_tm_numbers). It's history: this doesn't write it.
- Icons: Pokemon Journeys' TM discs, one per type (Graphics/Icons/itemMachine<TYPE>.png), and our grey
  HM disc for every HM.

Writes assets/tms.json {"TM001": {"move", "type", "tier", "price", "from"}} and the TM moves' lists in
assets/tm_learners.json {MOVE: [species ids]}: it only adds to that file (the move tutors' lists there, wider for
some moves, stay), so running it twice changes nothing. Run from the game folder:
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
SV = ("scarlet-violet", "the-teal-mask", "the-indigo-disk")   # (Scarlet/Violet's TM numbers run on through its DLC)
SV_COUNT = 229
MACHINE = 4
PRICES = [1000, 1000, 1500, 1500, 2000, 2000, 2500, 2500, 3000]  # by tier: cheap (Jordan)
# A game's name in a TM's "from" (its newest game with the move as a TM, and its number there).
GAME_NAME = {"scarlet-violet": "Scarlet/Violet", "the-teal-mask": "Scarlet/Violet", "the-indigo-disk": "Scarlet/Violet",
             "legends-za": "Legends: Z-A", "mega-dimension": "Legends: Z-A", "brilliant-diamond-shining-pearl":
             "Brilliant Diamond/Shining Pearl", "sword-shield": "Sword/Shield", "lets-go-pikachu-lets-go-eevee":
             "Let's Go", "ultra-sun-ultra-moon": "Ultra Sun/Ultra Moon", "sun-moon": "Sun/Moon",
             "omega-ruby-alpha-sapphire": "ORAS", "x-y": "X/Y", "black-2-white-2": "Black 2/White 2",
             "black-white": "Black/White", "heartgold-soulsilver": "HeartGold/SoulSilver", "platinum": "Platinum",
             "diamond-pearl": "Diamond/Pearl", "firered-leafgreen": "FireRed/LeafGreen", "emerald": "Emerald",
             "ruby-sapphire": "Ruby/Sapphire", "crystal": "Crystal", "gold-silver": "Gold/Silver", "yellow": "Yellow",
             "red-blue": "Red/Blue", "red-green-japan": "Red/Green", "blue-japan": "Blue (Japan)"}
NOT_MAIN = {"colosseum", "xd", "champions"}   # (side games: their TMs are Ruby/Sapphire's anyway)
SAME_GAME = {"mega-dimension": "legends-za"}   # (a DLC's TMs number on from its game's: one order)
ZA = ("legends-za", "mega-dimension")   # (not a main-series game: its own TMs come last)
ZA_LEARNERS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "za_tm_learners.json")


def rows(name):
    with open(os.path.join(CSV, name + ".csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def tiered(keys, move_of, moves):
    """Tiers 0-8 by power (status moves count as 55), weak first: {key: tier}."""
    def strength(key):
        return moves.get(move_of[key], {}).get("power") or 55
    order = sorted(keys, key=lambda k: (strength(k), k))
    return {k: min(8, rank * 9 // len(order)) for rank, k in enumerate(order)}


def numbered(machines, vg_by_id, item_name, move_name):
    """[(move, game, its number there)]: Scarlet/Violet's by number, then every other main-series TM move, newest game
    first, then Legends: Z-A's own by its number."""
    best = {}
    order = {r["identifier"]: int(r["order"]) for r in vg_by_id.values()}
    for r in machines:
        vg = vg_by_id[int(r["version_group_id"])]
        if vg["identifier"] in NOT_MAIN or not item_name.get(int(r["item_id"]), "").startswith("tm"):
            continue  # (HMs and TRs)
        move = move_name[int(r["move_id"])]
        sv, za = vg["identifier"] in SV, vg["identifier"] in ZA
        key = (0 if sv else 2 if za else 1, 0 if sv or za else -order[SAME_GAME.get(vg["identifier"], vg["identifier"])],
               int(r["machine_number"]))
        if move not in best or key < best[move][0]:
            best[move] = (key, vg["identifier"], int(r["machine_number"]))
    out = [(m, game, n) for m, (_k, game, n) in sorted(best.items(), key=lambda x: (x[1][0], x[0]))]
    sv_numbers = [n for _m, game, n in out if game in SV]
    assert sv_numbers == list(range(1, SV_COUNT + 1)), "Scarlet/Violet's TM001-TM229 aren't all in the CSV"
    return out


def main():
    moves = json.load(open(os.path.join("assets", "moves.json"), encoding="utf-8"))
    vg_by_id = {int(r["id"]): r for r in rows("version_groups")}
    item_name = {int(r["id"]): r["identifier"] for r in rows("items")}
    move_name = {int(r["id"]): r["identifier"].upper() for r in rows("moves")}
    tms = {f"TM{i + 1:03d}": e for i, e in enumerate(numbered(rows("machines"), vg_by_id, item_name, move_name))}
    tier = tiered(list(tms), {k: e[0] for k, e in tms.items()}, moves)
    out = {}
    for key, (move, game, number) in tms.items():
        out[key] = {"move": move, "type": moves.get(move, {}).get("type", "NORMAL"), "tier": tier[key],
                    "price": PRICES[tier[key]], "from": f"{GAME_NAME.get(game, game)} TM{number:02d}"}
    legacy = json.load(open(os.path.join("assets", "tm_legacy.json"), encoding="utf-8"))
    lost = sorted(set(legacy.values()) - {d["move"] for d in out.values()})
    assert not lost, f"old TMs missing from the new list: {lost}"
    missing = [d["move"] for d in out.values() if d["move"] not in moves]

    species_of = {int(r["id"]): int(r["species_id"]) for r in rows("pokemon")}
    wanted = {mid for mid, n in move_name.items() if n in {d["move"] for d in out.values()}}
    found = {}
    for r in rows("pokemon_moves"):
        if int(r["pokemon_move_method_id"]) != MACHINE or int(r["move_id"]) not in wanted:
            continue
        sid = species_of.get(int(r["pokemon_id"]))
        if sid and sid <= 1025:
            found.setdefault(move_name[int(r["move_id"])], set()).add(sid)
    path = os.path.join("assets", "tm_learners.json")
    try:
        learners = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        learners = {}
    # (added to, never cut: a move tutor's list there can be wider than the TM's, FireRed's Mega Kick)
    za = json.load(open(ZA_LEARNERS, encoding="utf-8")) if os.path.isfile(ZA_LEARNERS) else {}
    for d in out.values():  # (the Z-A-only TMs: Serebii's lists)
        if d["from"].startswith(GAME_NAME["legends-za"]) and isinstance(za.get(d["move"]), dict):
            found.setdefault(d["move"], set()).update(za[d["move"]]["species"])
    learners.update({m: sorted(s | set(learners.get(m, ()))) for m, s in found.items()})
    learners = dict(sorted(learners.items()))
    json.dump(out, open(os.path.join("assets", "tms.json"), "w", encoding="utf-8"), indent=1)
    json.dump(learners, open(path, "w", encoding="utf-8"), separators=(",", ":"))

    for t in {d["type"] for d in out.values()} | {"FAIRY", "NORMAL"}:
        src = os.path.join(ICONS, f"itemMachine{t}.png")
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(ITEMS, f"tm-{t.lower()}.png"))
    shutil.copyfile(os.path.join(ITEMS, "hm-cut.png"), os.path.join(ITEMS, "hm-disc.png"))
    nobody = sorted(d["move"] for d in out.values() if not learners.get(d["move"]))
    first_za = next((k for k, d in out.items() if d["from"].startswith(GAME_NAME["legends-za"])), None)
    print(f"{len(out)} TMs (TM001-TM{SV_COUNT:03d} Scarlet/Violet's, TM{SV_COUNT + 1}- older games', {first_za}- Z-A's); "
          f"moves not in moves.json: {missing}; learner lists: {len(learners)}; no learners: {nobody}")
    for t in range(9):
        print(t, sum(1 for d in out.values() if d["tier"] == t), "TMs, $", PRICES[t])


if __name__ == "__main__":
    main()
