"""Themed Pokémon Center and Poké Mart backgrounds for every Sinnoh town that has one.

Recolors the stand-in art (backgrounds/pokemoncenter.png, backgrounds/mart1.png) region by
region: walls, floor, counter, cushions, plants and mat take each town's palette, while the
nurse, clerks, healing machine, shelves and fridges are left as drawn. No characters, text
or symbols are added. Output: assets/backgrounds/sinnoh/<name>.png

    python dev/builders/make_sinnoh_buildings.py [town ...]
"""
import colorsys
import os
import sys

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BG = os.path.join(ROOT, "assets", "backgrounds")
OUT = os.path.join(BG, "sinnoh")


def hls(c):
    if isinstance(c, str):
        c = tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(*(v / 255 for v in c))
    return h * 360, l, s


# --- Rules: (test(h, l, s) -> bool, theme key, reference color in the base art) ---
def hue(lo, hi, s=0.0, l=(0.0, 1.0), smax=1.0):
    def test(h, li, si):
        inside = lo <= h <= hi if lo <= hi else (h >= lo or h <= hi)
        return inside and s <= si <= smax and l[0] <= li <= l[1]
    return test


C_WALL = [(hue(0, 48, 0.12, (0.3, 0.96)), "accent", (252, 221, 154)),
          (hue(48, 72, 0.3, (0.5, 0.96)), "wall", (244, 236, 161))]
C_WALL_SAFE = [(hue(15, 48, 0.3, (0.45, 0.96)), "accent", (252, 221, 154))] + C_WALL[1:]  # spares red crosses
C_FLOOR = [(hue(38, 75, 0.15, (0.4, 0.995)), "floor", (246, 247, 207))]
C_COUNTER = [(hue(350, 16, 0.4, (0.3, 0.9)), "counter", (250, 133, 115))]

M_WALL = [(hue(190, 228, 0.4, (0.25, 0.75)), "accent", (72, 144, 216)),
          (hue(45, 75, 0.25, (0.5, 0.96)), "wall", (240, 240, 208))]
M_FLOOR = [(hue(205, 238, 0.08, (0.35, 0.97)), "floor", (208, 216, 232)),
           (hue(178, 204, 0.25, (0.3, 0.8), smax=0.7), "rug", (112, 184, 200)),
           (hue(25, 50, 0.3, (0.45, 0.78)), "trim", (208, 176, 128))]

# Regions are painted in order (later ones win); each is a list of rects and the rules
# that apply inside them. A region with no rules is left exactly as drawn.
CENTER = [
    ([(0, 0, 1248, 832)], C_FLOOR),
    ([(0, 0, 1248, 168), (0, 168, 62, 212), (0, 212, 32, 246),
      (1186, 168, 1248, 212), (1216, 212, 1248, 246)], C_WALL),
    ([(95, 55, 182, 215)], [(hue(80, 175, 0.15), "plant", (108, 204, 117))] + C_WALL),
    ([(180, 58, 342, 215)], [(hue(90, 175, 0.15), "accent", (161, 252, 173))] + C_WALL),
    ([(340, 125, 905, 168)], C_COUNTER + C_WALL),
    ([(340, 168, 905, 335)], C_COUNTER + C_FLOOR),
    ([(345, 190, 420, 282), (825, 190, 902, 282)],
     [(hue(80, 175, 0.15), "plant", (108, 204, 117)),
      (hue(280, 345, 0.1, (0.35, 0.95)), "flower", (193, 164, 182))] + C_COUNTER),
    ([(0, 405, 188, 640)], [(hue(350, 20, 0.15, (0.3, 0.8)), "accent", (171, 112, 104))] + C_FLOOR),
    ([(895, 405, 1240, 680)], [(hue(45, 62, 0.85, (0.5, 0.84)), "cushA", (254, 244, 129)),
                               (hue(185, 220, 0.4), "cushB", (154, 212, 249))] + C_FLOOR),
    ([(545, 678, 702, 778)], [(hue(345, 20, 0.3), "mat", (196, 79, 61))] + C_FLOOR),
    # Healing machine, TV and PC keep their own colors; only the wall showing around them changes.
    ([(415, 82, 588, 240), (588, 48, 722, 132), (898, 42, 988, 215)], C_WALL_SAFE),
    ([(1003, 66, 1122, 128)], []),  # map, left as drawn
    # Nurse Joy: only the plain wall and floor behind her follow the theme.
    ([(592, 112, 712, 136)], C_WALL_SAFE),
    ([(592, 136, 712, 242)], [(hue(45, 72, 0.35, (0.6, 0.97)), "floor", (246, 247, 207)),
                              (hue(15, 30, 0.5, (0.55, 0.75)), "accent", (252, 221, 154))]),
]

MART = [
    ([(0, 0, 727, 615)], M_FLOOR),
    ([(0, 0, 727, 122), (0, 0, 92, 195), (640, 0, 727, 195)], M_WALL + M_FLOOR),
    ([(135, 115, 197, 395)], [(hue(205, 240, 0.3, (0.2, 0.75)), "counter", (88, 120, 192))] + M_FLOOR),
    ([(360, 420, 595, 532)], [(hue(185, 210, 0.75, (0.2, 0.6)), "cushB", (8, 152, 208)),
                              (hue(25, 55, 0.55, (0.2, 0.85)), "cushA", (232, 176, 72))] + M_FLOOR),
    ([(195, 80, 252, 190), (28, 458, 88, 562), (642, 458, 702, 562)],
     [(hue(90, 175, 0.3), "plant", (0, 192, 56)),
      (hue(285, 350, 0.25), "pot", (200, 60, 150))] + M_FLOOR),
    ([(168, 548, 278, 602)], [(hue(345, 15, 0.3), "mat", (208, 56, 56))] + M_FLOOR),
    # Left as drawn: poster, shelves, fridges, box, glass case.
    ([(85, 58, 142, 102), (252, 80, 478, 192), (478, 52, 645, 142), (28, 198, 82, 248),
      (28, 345, 136, 420)], []),
    # The two clerks: only the floor around them follows the theme.
    ([(72, 155, 142, 248), (72, 262, 142, 352)],
     [(hue(208, 232, 0.2, (0.75, 0.95)), "floor", (208, 216, 232)),
      (hue(182, 202, 0.35, (0.3, 0.75)), "rug", (112, 184, 200))]),
]

# --- Town palettes ---
THEMES = {
    # Seaside lab town: sand and sea.
    "sandgem": dict(wall="#F3E6C8", accent="#6FB7D9", floor="#F5ECD4", counter="#E98A70", mat="#D06A4E",
                    cushA="#F4D27C", cushB="#8FD0E8", plant="#5DBF73", flower="#F7A8B8", pot="#D06A4E"),
    # Big modern city, TV station: cool white and broadcast blue.
    "jubilife": dict(wall="#E8EEF6", accent="#4F7FD1", floor="#DFE7F1", counter="#E0605A", mat="#3F6CC0",
                     cushA="#F2C94C", cushB="#6FB1F0", plant="#4CB86A", flower="#F4F4F8", pot="#7F8CA8"),
    # Mining city: warm stone, coal brown, rust.
    "oreburgh": dict(wall="#DCCBAA", accent="#7A6450", floor="#CFC2AC", counter="#B8653F", mat="#7A4A30",
                     cushA="#E0A050", cushB="#8C8C96", plant="#6FA05A", flower="#E8C070", pot="#8A6448"),
    # Flower town: petal pink and honey.
    "floaroma": dict(wall="#FCE6EE", accent="#F29BB8", floor="#FFF3D8", counter="#F2849F", mat="#E86B95",
                     cushA="#FFE07A", cushB="#F7B3D0", plant="#5CC870", flower="#FF6FA8", pot="#E86B95"),
    # Old forest city: leaf green and timber.
    "eterna": dict(wall="#E8F0D6", accent="#4E8A4E", floor="#E2D4AE", counter="#A0703F", mat="#5F8A38",
                   cushA="#D9B26A", cushB="#8DBF7A", plant="#3E9E4E", flower="#F8F4E8", pot="#8A5E34"),
    # Contest city of hearts: rose and blush.
    "hearthome": dict(wall="#FFE6E6", accent="#E05A7A", floor="#FFF0E8", counter="#E86A86", mat="#D04A6A",
                      cushA="#FFC2CF", cushB="#F7E08A", plant="#66C080", flower="#FF6F91", pot="#D04A6A"),
    # Quiet ruins town: sand and ochre.
    "solaceon": dict(wall="#F4E9CA", accent="#C8A060", floor="#ECDDB8", counter="#D08850", mat="#A86A3A",
                     cushA="#F2C870", cushB="#A8C8A0", plant="#7AB060", flower="#F7E7A0", pot="#A86A3A"),
    # Stone city of martial arts: granite and violet.
    "veilstone": dict(wall="#E4E2E8", accent="#7A6E9A", floor="#D8D4DC", counter="#8A78B8", mat="#6A5A98",
                      cushA="#C9B8E8", cushB="#9AA4B8", plant="#5E9E6E", flower="#D8C8F0", pot="#6A5A98"),
    # Marsh city: reed green and swamp teal.
    "pastoria": dict(wall="#E5F0DC", accent="#4F9A86", floor="#DCE8CC", counter="#3E9C8A", mat="#2F7A6A",
                     cushA="#C8D86A", cushB="#7FC4B8", plant="#4FA858", flower="#F0E06A", pot="#5E7A4A"),
    # Ancient mountain village: old stone and mystic purple.
    "celestic": dict(wall="#EEE7DB", accent="#8C6E9E", floor="#DED6C6", counter="#9C7AB0", mat="#6E5084",
                     cushA="#D8C08A", cushB="#B4A0C8", plant="#6A9A6A", flower="#E0D0F0", pot="#7A6A5A"),
    # Port city of canals: navy and deck wood.
    "canalave": dict(wall="#E9EFF5", accent="#2F5E8C", floor="#DCCFB4", counter="#3C6E9E", mat="#2A4E7A",
                     cushA="#E8D08A", cushB="#6A9AC8", plant="#4EA86A", flower="#F4F4F4", pot="#2F5E8C"),
    # Snow city: frost white and ice blue, pine plants.
    "snowpoint": dict(wall="#F3F8FC", accent="#8CC4E8", floor="#E8F3FA", counter="#7AB4E0", mat="#5A8CC0",
                      cushA="#F6FAFF", cushB="#B8DCF4", plant="#3F8270", flower="#FFFFFF", pot="#5A8CC0"),
    # Solar-powered seaside city: sun gold and sky.
    "sunyshore": dict(wall="#FFF6D8", accent="#F2B230", floor="#F7EFD8", counter="#F2A030", mat="#3E86C8",
                      cushA="#FFD84A", cushB="#5AAEE8", plant="#58C070", flower="#FFD040", pot="#3E86C8"),
    # Pokémon League: royal purple and gold.
    "league": dict(wall="#EDE7F3", accent="#5A3E8C", floor="#E2DEEA", counter="#6A4AA0", mat="#B8902A",
                   cushA="#E2C25A", cushB="#8A70C0", plant="#3E8E5A", flower="#F0D070", pot="#5A3E8C"),
    # Battle island: ember orange.
    "fight_area": dict(wall="#F8E7D8", accent="#D8582E", floor="#ECDAC6", counter="#D8503A", mat="#A83A24",
                       cushA="#F2B040", cushB="#7A8A9A", plant="#5E9E4E", flower="#F28A3A", pot="#A83A24"),
    # Rugged mountain camp: earth and moss.
    "survival_area": dict(wall="#E8E2CE", accent="#7A6A48", floor="#D9CFB6", counter="#8C6A42", mat="#5E6E3A",
                          cushA="#C8A66A", cushB="#8EA070", plant="#4E8A46", flower="#E8E0B0", pot="#7A6A48"),
    # Hisui's Jubilife Village: paper walls, tatami, indigo.
    "jubilife_village": dict(wall="#F0E6D2", accent="#3E4A7A", floor="#D6C29C", counter="#9A6A3E", mat="#3E4A7A",
                             cushA="#C9A060", cushB="#5A6A9A", plant="#4E8E4E", flower="#F0E8D8", pot="#9A6A3E"),
}

# Which file each place needs (names match sinnoh_area_data.json, or the [area]_center/_mart
# fallback the game looks for when the town has no entry).
OUTPUTS = {
    "sandgem": ["sandgem_center"],
    "jubilife": ["jubilife_center", "jubilife_mart"],
    "oreburgh": ["oreburgh_center", "oreburgh_mart"],
    "floaroma": ["floaroma_center", "floaroma_town_mart"],
    "eterna": ["eterna_center", "eterna_mart"],
    "hearthome": ["hearthome_center", "hearthome_mart"],
    "solaceon": ["solaceon_center"],
    "veilstone": ["veilstone_center", "veilstone_mart"],
    "pastoria": ["pastoria_center", "pastoria_mart"],
    "celestic": ["celestic_center"],
    "canalave": ["canalave_center", "canalave_mart"],
    "snowpoint": ["snowpoint_center", "snowpoint_mart"],
    "sunyshore": ["sunyshore_center", "sunyshore_mart"],
    "league": ["sinnoh_league_center", "sinnoh_pokemon_league_mart"],
    "fight_area": ["fight_area_center", "fight_area_mart"],
    "survival_area": ["survival_area_center", "survival_area_mart"],
    "jubilife_village": ["jubilife_village_center", "jubilife_village_mart"],
}


def remap(px, ref, target):
    """Move a pixel from the base art's reference color to the theme color, keeping its shading."""
    h, l, s = px
    _, lr, sr = ref
    ht, lt, st = target
    nl = l * lt / lr if l <= lr else lt + (l - lr) * (1 - lt) / max(1e-6, 1 - lr)
    ns = min(1.0, st * s / sr) if sr > 0.05 else st
    r, g, b = colorsys.hls_to_rgb(ht / 360, max(0.0, min(1.0, nl)), ns)
    return bytes((round(r * 255), round(g * 255), round(b * 255)))


def render(base, regions, theme):
    w, h = base.get_size()
    data = pygame.image.tobytes(base, "RGB")
    mask = bytearray(w * h)
    for rid, (rects, _) in enumerate(regions):
        for x0, y0, x1, y1 in rects:
            x0, x1, y0, y1 = max(0, x0), min(w, x1), max(0, y0), min(h, y1)
            row = bytes([rid]) * (x1 - x0)
            for y in range(y0, y1):
                mask[y * w + x0:y * w + x1] = row
    pal = {k: hls(v) for k, v in theme.items()}
    rules = [[(t, k, hls(ref)) for t, k, ref in r] for _, r in regions]
    out = bytearray(data)
    cache = {}
    for i in range(w * h):
        rid = mask[i]
        if not rules[rid]:
            continue
        rgb = data[i * 3:i * 3 + 3]
        key = (rid, rgb)
        new = cache.get(key)
        if new is None:
            new = rgb
            px = hls(tuple(rgb))
            if px[1] > 0.13:
                for test, k, ref in rules[rid]:
                    if test(*px):
                        new = remap(px, ref, pal[k])
                        break
            cache[key] = new
        if new is not rgb:
            out[i * 3:i * 3 + 3] = new
    return pygame.image.frombytes(bytes(out), (w, h), "RGB")


def theme_for(town, themes=THEMES):
    t = dict(themes[town])
    if "rug" not in t:  # mart's middle floor: a soft version of the accent
        h, l, s = hls(t["accent"])
        r, g, b = colorsys.hls_to_rgb(h / 360, 0.64, min(s, 0.38))
        t["rug"] = "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))
    if "trim" not in t:  # floor border strip
        h, l, s = hls(t["floor"])
        r, g, b = colorsys.hls_to_rgb(h / 360, 0.62, min(0.45, s + 0.15))
        t["trim"] = "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))
    return t


def main(towns):
    pygame.init()
    center = pygame.image.load(os.path.join(BG, "pokemoncenter.png"))
    mart = pygame.image.load(os.path.join(BG, "mart1.png"))
    os.makedirs(OUT, exist_ok=True)
    for town in towns:
        theme = theme_for(town)
        for name in OUTPUTS[town]:
            is_center = name.endswith("_center")
            img = render(center if is_center else mart, CENTER if is_center else MART, theme)
            pygame.image.save(img, os.path.join(OUT, name + ".png"))
            print("wrote", name + ".png")


if __name__ == "__main__":
    main(sys.argv[1:] or list(OUTPUTS))
