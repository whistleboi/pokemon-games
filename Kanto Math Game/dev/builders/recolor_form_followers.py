"""Following-Pokemon sheets for the colour-only forms (Jordan, 11-17: "any form variation or regional form
change should have an accompanying overworld sprite"): the Orange Islands' Pinkan and Valencia Pokemon.
No walking art exists for them, and they differ from their species only in colour, so each is its species'
own sheet (assets/dungeon/followers/<dex>.png, shiny/<dex>.png) recoloured.

How the colours are found: the form's battle sprite (assets/sprites/pokemon/9103.png, Pinkan Butterfree) is
its species' battle sprite (12.png) recoloured pixel for pixel, so laying one on the other gives the form's
colour for every colour the species has (shiny: shiny/12.png -> shiny/9103.png). Each colour on the walking
sheet is matched to the nearest battle-sprite colour and moved the way that colour moved (its hue taken,
lightness and saturation shifted by the same amount), so the sheet keeps its own outlines and shading.

    python dev/builders/recolor_form_followers.py [--contact <folder>]
-> assets/dungeon/followers/<dex>_<form>.png and shiny/<dex>_<form>.png (the name DungeonState._follower_img
tries first for a Pokemon of that form); --contact: a contact sheet per form (battle sprites, then the
species' sheet beside the new one), for Jordan to look over.
"""
import colorsys
import json
import os
import sys
from collections import Counter

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

FORMS = ("pinkan", "valencia")
SOURCE = os.path.join("assets", "orange_area_data.json")   # (read only: its FORM_MAP has the Orange forms)
SPRITES = os.path.join("assets", "sprites", "pokemon")
OUT = os.path.join("assets", "dungeon", "followers")
# form sheets with no shiny one in their pack -> (battle sprite, shiny battle sprite) under SPRITES
SHINY_ONLY = {"94_mega": (os.path.join("mega", "94_mega.png"), os.path.join("mega", "shiny", "94_mega.png"))}


def _lab(rgb):
    """sRGB 0-255 -> CIE Lab (D65): distances that match the eye."""
    def lin(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(float(v)) for v in rgb[:3])
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def colour_map(species_png, form_png):
    """{species colour: form colour} from two pixel-aligned battle sprites (the most common pairing per colour)."""
    a = pygame.image.load(species_png).convert_alpha()
    b = pygame.image.load(form_png).convert_alpha()
    if a.get_size() != b.get_size():
        raise ValueError(f"{form_png}: not the same size as {species_png}")
    pairs = {}
    for y in range(a.get_height()):
        for x in range(a.get_width()):
            ca, cb = a.get_at((x, y)), b.get_at((x, y))
            if ca.a < 128 or cb.a < 128:
                continue
            pairs.setdefault((ca.r, ca.g, ca.b), Counter())[(cb.r, cb.g, cb.b)] += 1
    out = {}
    for src, hits in pairs.items():
        n = sum(hits.values())
        out[src] = (hits.most_common(1)[0][0], n)
    return out


def _clamp(v):
    return max(0.0, min(1.0, v))


def recolour(c, src, dst):
    """Colour c moved the way src moved to dst (hue taken from dst; lightness/saturation shifted alike)."""
    hc, lc, sc = colorsys.rgb_to_hls(*(v / 255.0 for v in c))
    hs, ls, ss = colorsys.rgb_to_hls(*(v / 255.0 for v in src))
    hd, ld, sd = colorsys.rgb_to_hls(*(v / 255.0 for v in dst))
    light = _clamp(lc + (ld - ls))
    if sd < 0.06:            # (the form's colour is grey: keep c's grey-ness in step)
        hue, sat = hc, _clamp(sc * sd / max(ss, 0.06))
    elif ss < 0.12:          # (from grey/white to a colour: the form's saturation)
        hue, sat = hd, sd
    else:                    # (colour to colour: the form's hue, c's saturation shifted alike; a grey c too)
        off = ((hc - hs + 0.5) % 1.0) - 0.5 if sc >= 0.12 else 0.0
        hue, sat = (hd + max(-0.04, min(0.04, off))) % 1.0, _clamp(sd + (sc - ss))
    r, g, b = colorsys.hls_to_rgb(hue, light, sat)
    return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))


def recolour_sheet(sheet_png, cmap):
    """The walking sheet with every colour moved by cmap (each sheet colour -> its nearest battle colour)."""
    sheet = pygame.image.load(sheet_png).convert_alpha()
    keys = [(k, _lab(k), n) for k, (_v, n) in cmap.items() if n >= 2] or [(k, _lab(k), n) for k, (_v, n) in cmap.items()]
    memo = {}
    out = sheet.copy()
    for y in range(sheet.get_height()):
        for x in range(sheet.get_width()):
            c = sheet.get_at((x, y))
            if c.a == 0:
                continue
            rgb = (c.r, c.g, c.b)
            if rgb not in memo:
                lc = _lab(rgb)
                src = min(keys, key=lambda k: (k[1][0] - lc[0]) ** 2 + (k[1][1] - lc[1]) ** 2 + (k[1][2] - lc[2]) ** 2)[0]
                memo[rgb] = recolour(rgb, src, cmap[src][0])
            out.set_at((x, y), (*memo[rgb], c.a))
    return out


def form_entries():
    fm = json.load(open(SOURCE, encoding="utf-8")).get("FORM_MAP", {})
    return sorted((int(k), int(v["id"]), v["form"], v.get("name", "")) for k, v in fm.items() if v.get("form") in FORMS)


def _cells(sheet, row=0):
    cw, ch = sheet.get_width() // 4, sheet.get_height() // 4
    return [sheet.subsurface((c * cw, r * ch, cw, ch)) for r, c in ((0, 0), (1, 0), (2, 0), (3, 0))] if row is None else \
        [sheet.subsurface((c * cw, row * ch, cw, ch)) for c in range(4)]


def contact(entries, folder, form):
    """One picture per form: each row = battle sprite (species, form), the species' sheet (a frame per facing),
    then the new sheet; normal on the left, shiny on the right."""
    rows = [e for e in entries if e[2] == form]
    cell = 64
    w = 2 * (2 * cell + 8 * cell + 24) + 20
    pic = pygame.Surface((w, len(rows) * (cell + 6) + 6))
    pic.fill((214, 214, 222))
    for i, (fid, dex, _f, _name) in enumerate(rows):
        y = 6 + i * (cell + 6)
        for half, sub in enumerate(("", "shiny")):
            x = 6 + half * (w // 2)
            for p in (os.path.join(SPRITES, sub, f"{dex}.png"), os.path.join(SPRITES, sub, f"{fid}.png")):
                if os.path.exists(p):
                    pic.blit(pygame.transform.scale(pygame.image.load(p).convert_alpha(), (cell, cell)), (x, y))
                x += cell
            x += 12
            for p in (os.path.join(OUT, sub, f"{dex}.png"), os.path.join(OUT, sub, f"{dex}_{form}.png")):
                if os.path.exists(p):
                    for c in _cells(pygame.image.load(p).convert_alpha(), None):
                        pic.blit(pygame.transform.scale(c, (cell, cell)), (x, y))
                        x += cell
                else:
                    x += 4 * cell
                x += 6
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{form}.png")
    pygame.image.save(pic, path)
    return path


def main():
    pygame.init()
    pygame.display.set_mode((8, 8))
    entries = form_entries()
    made = 0
    for fid, dex, form, _name in entries:
        for sub in ("", "shiny"):
            sheet = os.path.join(OUT, sub, f"{dex}.png")
            a, b = os.path.join(SPRITES, sub, f"{dex}.png"), os.path.join(SPRITES, sub, f"{fid}.png")
            if not (os.path.exists(sheet) and os.path.exists(a) and os.path.exists(b)):
                print("skip", fid, sub or "normal", "(no sheet or battle sprite)")
                continue
            pygame.image.save(recolour_sheet(sheet, colour_map(a, b)), os.path.join(OUT, sub, f"{dex}_{form}.png"))
            made += 1
    # (Jordan 11-23: the Pinkan / Valencia Pokemon with a Mega or G-Max form get that sheet in their own colours:
    # <dex>_<form>_mega / _gmax, the species -> form battle colours laid on the Mega / G-Max walking sheet)
    for fid, dex, form, _name in entries:
        for big in ("mega", "gmax"):
            for sub in ("", "shiny"):
                sheet = os.path.join(OUT, sub, f"{dex}_{big}.png")
                a, b = os.path.join(SPRITES, sub, f"{dex}.png"), os.path.join(SPRITES, sub, f"{fid}.png")
                if os.path.exists(sheet) and os.path.exists(a) and os.path.exists(b):
                    pygame.image.save(recolour_sheet(sheet, colour_map(a, b)),
                                      os.path.join(OUT, sub, f"{dex}_{form}_{big}.png"))
                    made += 1
    for name, (a, b) in SHINY_ONLY.items():   # (a form sheet whose pack had no shiny: its shiny battle colours)
        a, b = os.path.join(SPRITES, a), os.path.join(SPRITES, b)
        if os.path.exists(os.path.join(OUT, name + ".png")) and os.path.exists(a) and os.path.exists(b):
            pygame.image.save(recolour_sheet(os.path.join(OUT, name + ".png"), colour_map(a, b)),
                              os.path.join(OUT, "shiny", name + ".png"))
            made += 1
    print(made, "sheets")
    if "--contact" in sys.argv:
        folder = sys.argv[sys.argv.index("--contact") + 1]
        for form in FORMS:
            print(contact(entries, folder, form))


if __name__ == "__main__":
    main()
