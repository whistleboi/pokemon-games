"""Cliff tier builder (Jordan, 11-15: "some smart builder for tiering cliffsides"): from a map's height grid, which
cliff part goes on each tile, so cliffs come out with a top lip, faces, end caps and corners, tier on tier.

    import cliff_tiers
    parts = cliff_tiers.parts(levels, rows=3, stairs={(x, y), ...})
    # {(x, y): (row, col)}: row "lip" / "mid" / "face" / "base", col "L" / "C" / "R"; or ("inside", "W" / "E")
    tiles = cliff_tiers.tiles(parts, cliff_tiers.BANISHED_PLATINUM, stairs)   # {(x, y): [layer 1 tile, layer 2 tile]}
    art, cliffs = cliff_tiers.lay(art, levels)     # a map's cliffs as the game keeps them: rock tiles c, and its
                                                   # roofs "_cliffs" {"set", "rock": rows of codes, "steps": rows}
                                                   # (src/dungeon/art.py draws them; the map maker's "Cliffs from levels")

How a cliff is laid (the older games' way, seen from above with north up):
  - a higher level's south edge shows its whole face: its last `rows` rows are cliff. From the bottom up: the base of the
    face, the face, (middle rows when rows > 3), and the lip, the rounded rim where the grass on top stops;
  - its west and east edges show one column of rock side; its north edge only the lip (you see the top of the rim);
  - the ends round off: a cliff run that stops (beside grass of its own level, or a drop) gets an end cap, and where a
    side meets the south face or the north lip the corner joins them;
  - an inside corner (the lower ground's corner poking into the higher level) carries the face on one tile and turns
    its foot into the side running on down (part ("inside", "W" or "E"): which side the lower ground is on);
  - each tier is its own cliff: a level-3 face stands on a level-2 lip, never merged into one tall wall;
  - stairs (path tiles crossing a cliff, a run of 3 wide) are drawn over the rock: their top step on the lip, the
    flight down the face.
Any tile sheet that has a 3 x 4 rock block (lip, middle, face, base rows; left, centre, right columns) and stairs
can be named in a table like BANISHED_PLATINUM below.
"""

import json
import os

ROWS = ("lip", "mid", "face", "base")
GAME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def table(set_name="rock_bp"):
    """A cliff tile set's spec (dev/builders/pieces/<set>.json "tiles"): {part name: {"id", "code", ...}}. Its tiles are
    cut into assets/tiles/<set>/ by dev/tools/piece_library.py; the game draws them from there."""
    with open(os.path.join(GAME, "dev", "builders", "pieces", f"{set_name}.json"), encoding="utf-8") as f:
        return json.load(f)["tiles"]


def set_rows(set_name="rock_bp"):
    """How tall a set's south faces are (lip included): its spec's "rows" (rock_hgss, the thin-rimmed grass plateau:
    1), else 3."""
    try:
        with open(os.path.join(GAME, "dev", "builders", "pieces", f"{set_name}.json"), encoding="utf-8") as f:
            return int(json.load(f).get("rows", 3))
    except (OSError, ValueError):
        return 3


# the cliff styles the map maker offers: (set, label)
STYLES = [("rock_bp", "Platinum rock (tall faces)"), ("rock_hgss", "Johto grass plateau (thin rim)")]


# Banished Platinum's outdoor sheet (Wesley-FG-DPPt.png): the rock block (rows 73-76 of the sheet), its inside corners,
# the stairs (rows 83-84); Route 213, Route 219 and Oreburgh City draw their cliffs with these. {part name: tile id}
BANISHED_PLATINUM = {k: v["id"] for k, v in table("rock_bp").items()}


def parts(levels, rows=3, stairs=()):
    """Which cliff part each tile of a raised level's edge gets: {(x, y): (row, col)}. levels: rows of ints (a tile's
    height; trees, houses, water count at the level they stand on). rows: how tall a south face is (lip included)."""
    H, W = len(levels), len(levels[0])
    lv = lambda x, y: levels[y][x] if 0 <= x < W and 0 <= y < H else None
    lower = lambda x, y, h: lv(x, y) is not None and lv(x, y) < h
    out = {}
    for y in range(H):
        for x in range(W):
            h = lv(x, y)
            # rows down to the drop below (1 = the face's bottom row); the drop must be straight below, in this column
            def drop_below(cx):
                k = next((k for k in range(1, rows + 1) if lower(cx, y + k, h)), None)
                if k is not None and any(lv(cx, y + j) != h for j in range(1, k)):
                    return None                # (another tier's cliff is in between: that one is lower's own)
                return k
            k = drop_below(x)
            if k is None and lv(x, y + 1) == h:
                # an inside corner (the lower ground's corner pokes in diagonally): the face beside it runs on one tile
                # so it meets the side below it, instead of stopping short of it
                ks = [(kk, cx - x) for cx in (x - 1, x + 1) if lv(cx, y) == h for kk in [drop_below(cx)]
                      if kk is not None and lv(x, y + kk) == h]
                k, inside = min(ks) if ks else (None, 0)
            else:
                inside = 0
            drops = {d for d, (dx, dy) in {"N": (0, -1), "W": (-1, 0), "E": (1, 0)}.items() if lower(x + dx, y + dy, h)}
            if k is None and not drops:
                continue
            if k is not None:
                row = "base" if k == 1 else "face" if k == 2 else "lip" if k == rows else "mid"
                if "N" in drops:
                    row = row if k <= 2 else "lip"
            else:
                row = "lip" if "N" in drops else "mid"
            out[(x, y)] = [row, h, k, drops, inside]
    # a face's lip under more of the same cliff (a tier too small for its own lip row, seen from the north): the middle
    for (x, y), o in out.items():
        up = out.get((x, y - 1))
        if o[0] == "lip" and o[2] is not None and up and up[1] == o[1]:
            o[0] = "mid"
    # columns: an end where the run stops (west/east neighbour drops, or isn't cliff of this level)
    res = {}
    for (x, y), (row, h, k, drops, inside) in out.items():
        if inside and row == "base" and (x, y + 1) in out:
            # the face's foot turning into the side that runs on down from it (Oreburgh City draws it so)
            res[(x, y)] = ("inside", "W" if inside < 0 else "E")
            continue
        def stops(dx):
            n = (x + dx, y)
            if lower(n[0], n[1], h):
                return True
            if k is None:                        # (a side column: only its drop side rounds off)
                return False
            o = out.get(n)
            return o is None or o[1] != h or o[2] is None
        left, right = stops(-1), stops(1)
        if "W" in drops:
            left = True
        if "E" in drops:
            right = True
        col = "L" if left and not right else "R" if right and not left else "C"
        res[(x, y)] = (row, col)
    return res


def names(parts_, stairs=()):
    """Each cliff tile's picture names: {(x, y): (rock part, stairs over it or None)}, e.g. ("lip_C", "stairs_top_1")."""
    stairs = set(stairs)
    out = {}
    for (x, y), (row, col) in parts_.items():
        step = None
        if (x, y) in stairs:
            run = [xx for xx in range(x - 8, x + 9) if all((a, y) in stairs for a in range(min(xx, x), max(xx, x) + 1))]
            i, n = x - min(run), len(run)
            step = ("stairs_top_" if row == "lip" else "stairs_") + str(0 if i == 0 else 2 if i == n - 1 else 1)
        out[(x, y)] = (f"{row}_{col}", step)
    return out


def tiles(parts_, table_, stairs=()):
    """The tile ids for each cliff tile: {(x, y): [rock tile, stairs over it or 0]} (table_: {part name: tile id})."""
    return {xy: [table_[r], table_[st] if st else 0] for xy, (r, st) in names(parts_, stairs).items()}


GROUND = '.f"8c'          # (what a cliff is laid over: lawn, flowers, tall grass, snow, an older cliff)
PATHS = "=deap,s"         # (a path crossing a cliff: stairs; it stays open)


def lay(art, levels, set_name="rock_bp", rows=3, built=None):
    """A map's cliffs from its height levels, the way a map keeps them: (new art rows, its roofs "_cliffs" entry or None).
    Rock tiles become c (in the way); a path crossing a cliff (path above its top and below its foot) stays open, stairs
    drawn on it; a path only running along under it is covered by the rock; trees, buildings and water
    keep their own tile (a cliff runs on hidden under the woods). built: the map's last "_cliffs", whose rock is cleared
    first, so a map can be rebuilt after its levels change."""
    art = [list(r) for r in art]
    H, W = len(art), len(art[0])
    if built:
        for y, r in enumerate(built.get("rock") or ()):
            for x, code in enumerate(r):
                if code != "." and y < H and x < W and art[y][x] == "c":
                    art[y][x] = "."
    p = parts(levels, rows)
    keep = {xy: v for xy, v in p.items() if art[xy[1]][xy[0]] in GROUND + PATHS}
    stairs = set()
    walk = PATHS + "<>^v"
    for (x, y) in keep:                  # stairs where a path runs across the cliff: path above its top and below its foot
        if art[y][x] not in PATHS or (x, y) in stairs:
            continue
        top, foot = y, y
        while (x, top - 1) in keep:
            top -= 1
        while (x, foot + 1) in keep:
            foot += 1
        above = art[top - 1][x] if top > 0 else ""
        below = art[foot + 1][x] if foot + 1 < H else ""
        if above and below and above in walk and below in walk and all(art[yy][x] in PATHS for yy in range(top, foot + 1)):
            stairs |= {(x, yy) for yy in range(top, foot + 1)}
    for (x, y) in keep:                  # (a path running along under a cliff, not across it, goes under the rock)
        if art[y][x] in PATHS and (x, y) not in stairs:
            art[y][x] = "."
    codes = {k: v["code"] for k, v in table(set_name).items()}
    rock, steps = [["."] * W for _ in range(H)], [["."] * W for _ in range(H)]
    for (x, y), (r, st) in names(keep, stairs).items():
        rock[y][x] = codes[r]
        if st:
            steps[y][x] = codes[st]
        elif art[y][x] in GROUND:
            art[y][x] = "c"
    if not keep:
        return ["".join(r) for r in art], None
    return ["".join(r) for r in art], {"set": set_name, "rock": ["".join(r) for r in rock], "steps": ["".join(r) for r in steps]}
