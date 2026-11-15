"""Piece library (Jordan, 11-15): ready-made, checked map pieces cut from fan tile sheets, so a house, a stage or a palm
is made once and placed anywhere ("a 4x4 Alola house, N-S, entrance 1 tile wide ... so you don't remake the same houses").

A spec (dev/builders/pieces/<set>.json) says how each piece is cut and how it stands on the map:
    "hut_small": {"sheet": "AlolaMisc", "blocks": [[0, 80, 6, 87]],      tile blocks [col0, row0, col1, row1], side by side
                  "foot": [1, 0, 5, 5], "doors": [2],                        footprint [x, y, w, h] in the piece's tiles
                  "kind": "house", "label": "Thatched hut (small)"}         (its bottom row holds the doors), door columns
A set can also hold single tiles ("tiles": {"lip_C": {"sheet": "outdoor", "id": 969, "code": "b"}}, an RPG Maker tile id:
384 + its place on the sheet, 8 a row), written as they are: the cliff tiles dev/tools/cliff_tiers.py lays (rock_bp).
"touches": ["right"] lets a side touch the sheet's next picture (only after checking the piece by eye).
A piece wider than its sheet (8 tiles) wraps like a strip: the part at the sheet's right edge carries on at its left edge
lower down; list the blocks left to right and they're joined (Hala's house, the festival stage).

    python -I dev/tools/piece_library.py alola            cut, check and write the alola pieces
    python -I dev/tools/piece_library.py alola --check    only check (exit 1 if anything fails)

Writes assets/tiles/<set>/<name>.png and assets/tiles/<set>/index.json ({"ox", "oy"}: where the footprint's top-left corner
is in the picture, 32 px a tile, the way art.py places the real games' models; plus foot, doors, kind, label, credit),
and dev/builders/out/pieces_<set>.png: every piece on its tile grid, footprint in red, doors in blue, its checks.

Checks: the picture's outer edge is clear (nothing cut off: the stage's missing steps, the house's missing wing), every
seam between joined blocks lines up, the footprint lies inside the picture and its doors inside the footprint.
The sheets are downloads: run this with python -I, and it only reads them as pictures.
"""
import json
import os
import sys

GAME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPECS = os.path.join(GAME, "dev", "builders", "pieces")
T = 32
SHADOW = (120, 120, 120)          # (Essentials sheets draw shadows in solid grey: made see-through dark here)


def background(c):
    return c.a < 20 or (c.r > 240 and c.g < 20 and c.b > 240)


def solid(c):
    return not background(c) and (c.r, c.g, c.b) != SHADOW


def cut(sheet, blocks, pygame):
    """The piece's picture: its tile blocks side by side, background clear, shadows see-through. Also the seams' x."""
    w = sum(c1 - c0 for c0, _r0, c1, _r1 in blocks) * T
    h = max(r1 - r0 for _c0, r0, _c1, r1 in blocks) * T
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    x, seams = 0, []
    for c0, r0, c1, r1 in blocks:
        part = sheet.subsurface((c0 * T, r0 * T, (c1 - c0) * T, (r1 - r0) * T))
        for yy in range(part.get_height()):
            for xx in range(part.get_width()):
                c = part.get_at((xx, yy))
                if background(c):
                    continue
                out.set_at((x + xx, yy), (0, 0, 0, 70) if (c.r, c.g, c.b) == SHADOW else c)
        x += (c1 - c0) * T
        seams.append(x)
    return out, seams[:-1]


def check(sheet, spec, pygame):
    """Problems with a piece, in words (none: it's whole)."""
    out = []
    blocks = spec["blocks"]
    # 1. nothing cut off: no solid pixel on the outer edge of the joined picture (the sheet's own pixels, before clearing)
    w = sum(c1 - c0 for c0, _r0, c1, _r1 in blocks) * T
    h = max(r1 - r0 for _c0, r0, _c1, r1 in blocks) * T
    def px(x, y):
        """The sheet pixel at (x, y) of the joined picture, or None past a block."""
        for c0, r0, c1, r1 in blocks:
            bw = (c1 - c0) * T
            if x < bw:
                return sheet.get_at((c0 * T + x, r0 * T + y)) if y < (r1 - r0) * T else None
            x -= bw
        return None
    # an edge pixel is only cut off if the sheet goes on past it with more of a picture (touching the tile line is fine)
    SW, SH = sheet.get_size()
    def outside_solid(sx, sy):
        return 0 <= sx < SW and 0 <= sy < SH and solid(sheet.get_at((sx, sy)))
    cuts = {"top": 0, "bottom": 0, "left": 0, "right": 0}
    for i, (c0, r0, c1, r1) in enumerate(blocks):
        for sx in range(c0 * T, c1 * T):
            if solid(sheet.get_at((sx, r0 * T))) and outside_solid(sx, r0 * T - 1):
                cuts["top"] += 1
            if solid(sheet.get_at((sx, r1 * T - 1))) and outside_solid(sx, r1 * T):
                cuts["bottom"] += 1
        for sy in range(r0 * T, r1 * T):
            if i == 0 and solid(sheet.get_at((c0 * T, sy))) and outside_solid(c0 * T - 1, sy):
                cuts["left"] += 1
            if i == len(blocks) - 1 and solid(sheet.get_at((c1 * T - 1, sy))) and outside_solid(c1 * T, sy):
                cuts["right"] += 1
    allowed = set(spec.get("touches", []))     # (sides where the next picture on the sheet really does touch: checked by eye)
    for side, n in cuts.items():
        if n >= 3 and side not in allowed:
            out.append(f"cut off on its {side} edge ({n} px): its blocks are too small, or a part is stored elsewhere on the sheet")
    # 2. seams line up: across each join, solid pixels meet solid pixels of a similar colour
    x0 = 0
    for c0, r0, c1, r1 in blocks[:-1]:
        x0 += (c1 - c0) * T
        a = [px(x0 - 1, y) for y in range(h)]
        b = [px(x0, y) for y in range(h)]
        both = [(p, q) for p, q in zip(a, b) if p is not None and q is not None and (solid(p) or solid(q))]
        if not both:
            continue
        broken = sum(1 for p, q in both if solid(p) != solid(q))
        far = sum(1 for p, q in both if solid(p) and solid(q) and abs(p.r - q.r) + abs(p.g - q.g) + abs(p.b - q.b) > 150)
        if (broken + far) > max(4, len(both) * 0.35):   # (thin lines and shading change across any column; a real misjoin breaks half or more)
            out.append(f"seam at x={x0} doesn't line up ({broken + far} of {len(both)} px): wrong block, or rows off")
    # 3. footprint inside the picture, doors inside the footprint (on its bottom row)
    fx, fy, fw, fh = spec["foot"]
    if fx < 0 or fy < 0 or (fx + fw) * T > w or (fy + fh) * T > h:
        out.append(f"footprint {spec['foot']} goes outside the picture ({w // T} x {h // T} tiles)")
    for d in spec.get("doors", []):
        if not 0 <= d < fw:
            out.append(f"door at column {d} is outside the footprint ({fw} wide)")
    return out


def preview(pieces, path, pygame):
    """Every piece on its tile grid: footprint red, doors blue, its name and checks."""
    pygame.font.init()
    f = pygame.font.SysFont("arial", 13, bold=True)
    cells = []
    for name, (pic, spec, problems) in pieces.items():
        w, h = pic.get_size()
        c = pygame.Surface((max(w, 220) + 16, h + 64))
        c.fill((120, 196, 110))
        c.blit(pic, (8, 40))
        for x in range(0, w + 1, T):
            pygame.draw.line(c, (40, 70, 40), (8 + x, 40), (8 + x, 40 + h))
        for y in range(0, h + 1, T):
            pygame.draw.line(c, (40, 70, 40), (8, 40 + y), (8 + w, 40 + y))
        fx, fy, fw, fh = spec["foot"]
        pygame.draw.rect(c, (230, 30, 30), (8 + fx * T, 40 + fy * T, fw * T, fh * T), 3)
        for d in spec.get("doors", []):
            pygame.draw.rect(c, (40, 90, 255), (8 + (fx + d) * T + 3, 40 + (fy + fh - 1) * T + 3, T - 6, T - 6), 3)
        c.blit(f.render(f"{name}  {fw}x{fh}  doors {spec.get('doors', [])}", 1, (0, 0, 0)), (8, 4))
        c.blit(f.render("OK" if not problems else "CHECK: " + problems[0][:60], 1, (0, 90, 0) if not problems else (200, 0, 0)), (8, 20))
        cells.append(c)
    W = 1500
    rows, row, x = [], [], 0
    for c in cells:
        if x + c.get_width() > W and row:
            rows.append(row)
            row, x = [], 0
        row.append(c)
        x += c.get_width() + 10
    rows.append(row)
    H = sum(max(c.get_height() for c in r) + 10 for r in rows)
    out = pygame.Surface((W, H))
    out.fill((235, 235, 235))
    y = 0
    for r in rows:
        x = 0
        for c in r:
            out.blit(c, (x, y))
            x += c.get_width() + 10
        y += max(c.get_height() for c in r) + 10
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pygame.image.save(out, path)


def main():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    name = sys.argv[1]
    only_check = "--check" in sys.argv
    with open(os.path.join(SPECS, f"{name}.json"), encoding="utf-8") as f:
        spec = json.load(f)
    sheets = {k: pygame.image.load(os.path.join(spec["sheet_dir"], v)) for k, v in spec["sheets"].items()}
    tiles = {}
    for tname, ts in (spec.get("tiles") or {}).items():
        i = ts["id"] - 384
        pic = pygame.Surface((T, T), pygame.SRCALPHA)
        part = sheets[ts["sheet"]].subsurface(((i % 8) * T, (i // 8) * T, T, T))
        for yy in range(T):
            for xx in range(T):
                c = part.get_at((xx, yy))
                if not background(c):
                    pic.set_at((xx, yy), (0, 0, 0, 70) if (c.r, c.g, c.b) == SHADOW else c)
        tiles[tname] = (pic, ts)
    done, failed = {}, 0
    for pname, ps in spec["pieces"].items():
        sheet = sheets[ps["sheet"]]
        problems = check(sheet, ps, pygame)
        pic, _seams = cut(sheet, ps["blocks"], pygame)
        done[pname] = (pic, ps, problems)
        failed += bool(problems)
        print(f"  {pname}: {'OK' if not problems else '; '.join(problems)}")
    if done:
        preview(done, os.path.join(GAME, "dev", "builders", "out", f"pieces_{name}.png"), pygame)
    if not only_check:
        out = os.path.join(GAME, "assets", "tiles", spec["set"])
        os.makedirs(out, exist_ok=True)
        index = {}
        for tname, (pic, ts) in tiles.items():
            pygame.image.save(pic, os.path.join(out, tname + ".png"))
            index[tname] = {"tile": ts["id"], "code": ts.get("code", ""), "credit": spec.get("credit", "")}
        for pname, (pic, ps, problems) in done.items():
            if problems:
                continue                      # (a piece that fails its checks isn't written)
            pygame.image.save(pic, os.path.join(out, pname + ".png"))
            fx, fy, fw, fh = ps["foot"]
            index[pname] = {"name": ps.get("label", pname), "ox": fx * T, "oy": fy * T, "foot": [fw, fh],
                            "doors": ps.get("doors", []), "kind": ps.get("kind", "house"), "label": ps.get("label", pname),
                            "credit": spec.get("credit", "")}
        with open(os.path.join(out, "index.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(index, f, indent=1)
            f.write("\n")
        print(f"wrote {len(index)} pieces and tiles to assets/tiles/{spec['set']} (checks failed: {failed})")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
