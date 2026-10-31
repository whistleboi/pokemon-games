"""Themed Pokémon Center + Poké Mart backgrounds for every Unova town that has one.

Unova's Centers hold the Mart counter too, so each town gets one picture, saved under both
names the game asks for (<center>.png and <area>_mart.png). It recolors the Gen 5 stand-in
(backgrounds/5gen center-mart.png): floor, walls, the orange counter/booth trim, the Mart
counter and the plant take each town's palette. The Union Room and Global Link staff, the
nurse, the two clerks, the healing machine, globe, PC and shelves are left as drawn.

The art is portrait and the game shows backgrounds wide, so the room is scaled up (crisp,
2x) and centered on a black canvas of the game's shape instead of being stretched.

    python dev/builders/make_unova_buildings.py [town ...]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import pygame  # noqa: E402
from make_sinnoh_buildings import BG, hls, hue, render, theme_for  # noqa: E402

OUT = os.path.join(BG, "unova")
BASE = os.path.join(BG, "5gen center-mart.png")
SCALE = 2
CANVAS_H = 300 * SCALE
CANVAS_W = round(CANVAS_H * 1280 / 540)  # the area above the dialogue box at 1280x720

FLOOR = (hue(22, 42, 0.3, (0.45, 0.8)), "floor", (255, 189, 115))
ACCENT = (hue(5, 16, 0.45, (0.3, 0.75)), "accent", (239, 99, 66))
WALL = (hue(225, 242, 0.3, (0.25, 0.45)), "wall", (58, 66, 148))
MART = (hue(190, 210, 0.4, (0.25, 0.7)), "mart", (58, 173, 214))
PLANT = (hue(70, 170, 0.2), "plant", (60, 160, 70))

# People and fixtures: only the room's own floor and trim colors change inside these boxes,
# so skin, hair, clothes and the machines keep theirs.
KEEP = [(58, 56, 79, 92), (111, 56, 133, 92), (167, 56, 191, 92),  # booth staff
        (112, 159, 134, 187),                                       # nurse
        (185, 216, 208, 276),                                       # Mart clerks
        (203, 50, 248, 106), (53, 158, 84, 206), (3, 205, 26, 248),  # globe, PC, magazine rack
        (209, 226, 248, 280), (98, 118, 150, 165)]                  # Mart shelves, healing machine

REGIONS = [
    ([(0, 0, 248, 300)], [ACCENT, WALL, FLOOR]),
    ([(150, 165, 248, 280)], [MART, ACCENT, FLOOR]),       # Mart corner
    ([(55, 236, 80, 280)], [PLANT, ACCENT, FLOOR]),        # plant
    (KEEP, None),  # filled in below
]


def room_colors_only(base):
    """Rules for the KEEP boxes: floor and trim colors that are common outside them."""
    counts = {}
    w, h = base.get_size()
    for y in range(h):
        for x in range(w):
            if any(x0 <= x < x1 and y0 <= y < y1 for x0, y0, x1, y1 in KEEP):
                continue
            c = tuple(base.get_at((x, y))[:3])
            counts[c] = counts.get(c, 0) + 1
    rules = []
    for test, key, ref in (FLOOR, ACCENT):
        keep = frozenset(hls(c) for c, n in counts.items() if n >= 8 and test(*hls(c)))
        rules.append((lambda hh, l, s, keep=keep: (hh, l, s) in keep, key, ref))
    return rules


THEMES = {
    # Seaside start town: sea breeze and sand.
    "nuvema": dict(wall="#4A8A5A", accent="#E87A5A", floor="#F4E2BE", mart="#5AA8D8", plant="#4FAE60"),
    # Hillside town of street music: dusk violet.
    "accumula": dict(wall="#6A5A8A", accent="#E08A4A", floor="#F2DCB4", mart="#5AA0D0", plant="#4FA860"),
    # Restaurant and Trainers' School: dark wood and wine.
    "striaton": dict(wall="#4A3A2E", accent="#B84A3A", floor="#EAD8BA", mart="#4A8AB0", plant="#4E9E52"),
    # Museum warehouse town: red brick.
    "nacrene": dict(wall="#7A3E2E", accent="#A85A3A", floor="#E6D2B4", mart="#4A86A8", plant="#5A9A50"),
    # Skyscraper city: steel blue and concrete.
    "castelia": dict(wall="#2E4A7A", accent="#3E7FD0", floor="#E2E6EE", mart="#3A9AD8", plant="#4AA060"),
    # Amusement park and stage lights: night sky and Elesa yellow.
    "nimbasa": dict(wall="#2A2A5A", accent="#F2C02A", floor="#FFEBB0", mart="#5AB0E8", plant="#4CB060"),
    # Market port: earth and timber.
    "driftveil": dict(wall="#5A4632", accent="#B86A3A", floor="#E2CFA8", mart="#4A90B0", plant="#5A9A4A"),
    # Cargo airport: open sky.
    "mistralton": dict(wall="#3E78B8", accent="#5AA0E0", floor="#E6EEF4", mart="#3A7AC0", plant="#4AA868"),
    # Snowy wetlands: frost and ice.
    "icirrus": dict(wall="#5A86A8", accent="#8CC4E8", floor="#E8F3FA", mart="#6AAEE0", plant="#3F8270"),
    # Dragon city of old and new: slate and jade.
    "opelucid": dict(wall="#2A2A3A", accent="#3E8A80", floor="#DADDE4", mart="#5A8AA8", plant="#3E8E5A"),
    # Walled town of the cold night: stone and moonlight.
    "lacunosa": dict(wall="#4A4A6A", accent="#7A82A8", floor="#DAD6CE", mart="#6A8AB0", plant="#5A8A6A"),
    # Beach resort: ocean and coral.
    "undella": dict(wall="#2E8AB0", accent="#F28A5A", floor="#F6E6C0", mart="#3AB0D0", plant="#4CB070"),
    # Desert-edge town by the volcano: ash and ember.
    "lentimas": dict(wall="#5A3A2A", accent="#D8502E", floor="#E8C49C", mart="#5A8AA0", plant="#7A9A4A"),
    # Village on the water: deep sea and aqua.
    "humilau": dict(wall="#1E6E9A", accent="#3AB8C8", floor="#D8EEF0", mart="#2E8AC0", plant="#3FA070"),
    # Lookout town by the trees: pine green.
    "aspertia": dict(wall="#3E6E4A", accent="#E06A3C", floor="#F6D8A4", mart="#4AA8D8", plant="#3FA05A"),
    # Ranch town: meadow and barn red.
    "floccesy": dict(wall="#6A8A3A", accent="#C8763A", floor="#EED8A8", mart="#7AB0C8", plant="#5AAE4A"),
    # Industrial port with a rock club: steel and Roxie purple.
    "virbank": dict(wall="#3A3A4A", accent="#9A4AC0", floor="#D4CCDC", mart="#5A9AB8", plant="#5A9A6A"),
    # Railway town: iron and rust.
    "anville": dict(wall="#4A4A4A", accent="#B8603A", floor="#DED2BE", mart="#5A8AA8", plant="#5A9A50"),
    # The dark modern city.
    "black_city": dict(wall="#1E1E26", accent="#5A5A6A", floor="#BCB8C2", mart="#4A5A7A", plant="#4A7A5A"),
    # The bright forest: leaf and white.
    "white_forest": dict(wall="#5A9A5A", accent="#8CC47A", floor="#F6F6EE", mart="#6AB8A8", plant="#4AAE5A"),
    # Pokémon League: night purple and gold.
    "league": dict(wall="#2E2246", accent="#C8A030", floor="#E6DCC8", mart="#6A4AA0", plant="#3E8E5A"),
    # Shopping street: berry and honey.
    "join_avenue": dict(wall="#7A3A5A", accent="#E86A8A", floor="#F6E0D0", mart="#E8A040", plant="#4FAE60"),
    # The dream-like Entralink: indigo and lavender.
    "entralink": dict(wall="#3A4A8A", accent="#8A6AD8", floor="#E4E0F4", mart="#6A8AD8", plant="#5A9A8A"),
}

# Files per town: the Center name sinnoh-style data already uses (or [area]_center.png), and
# [area]_mart.png for the Mart, which shares the room.
OUTPUTS = {
    "nuvema": ("nuvema_town_center", "nuvema_town_mart"),
    "accumula": ("accumula_center", "accumula_town_mart"),
    "striaton": ("striaton_center", "striaton_city_mart"),
    "nacrene": ("nacrene_center", "nacrene_city_mart"),
    "castelia": ("castelia_center", "castelia_city_mart"),
    "nimbasa": ("nimbasa_center", "nimbasa_city_mart"),
    "driftveil": ("driftveil_center", "driftveil_city_mart"),
    "mistralton": ("mistralton_center", "mistralton_city_mart"),
    "icirrus": ("icirrus_center", "icirrus_city_mart"),
    "opelucid": ("opelucid_center", "opelucid_city_mart"),
    "lacunosa": ("lacunosa_center", "lacunosa_town_mart"),
    "undella": ("undella_center", "undella_town_mart"),
    "lentimas": ("lentimas_town_center", "lentimas_town_mart"),
    "humilau": ("humilau_city_center", "humilau_city_mart"),
    "aspertia": ("aspertia_city_center", "aspertia_city_mart"),
    "floccesy": ("floccesy_town_center", "floccesy_town_mart"),
    "virbank": ("virbank_city_center", "virbank_city_mart"),
    "anville": ("anville_town_center", "anville_town_mart"),
    "black_city": ("black_city_center", "black_city_mart"),
    "white_forest": ("white_forest_center", "white_forest_mart"),
    "league": ("league_center", "unova_pokemon_league_mart"),
    "join_avenue": ("join_avenue_center", "join_avenue_mart"),
    "entralink": ("entralink_center", "entralink_mart"),
}


def main(towns, themes=THEMES, outputs=OUTPUTS, out_dir=OUT):
    """Also used for other regions that borrow the Gen 5 room (make_kalos_buildings.py)."""
    pygame.init()
    base = pygame.image.load(BASE)
    regions = [(r, rules if rules is not None else room_colors_only(base)) for r, rules in REGIONS]
    os.makedirs(out_dir, exist_ok=True)
    for town in towns:
        room = render(base, regions, theme_for(town, themes))
        room = pygame.transform.scale_by(room, SCALE)  # nearest-neighbour: pixels stay crisp
        canvas = pygame.Surface((CANVAS_W, CANVAS_H))
        canvas.fill((0, 0, 0))
        canvas.blit(room, ((CANVAS_W - room.get_width()) // 2, 0))
        for name in outputs[town]:
            pygame.image.save(canvas, os.path.join(out_dir, name + ".png"))
            print("wrote", name + ".png")


if __name__ == "__main__":
    main(sys.argv[1:] or list(OUTPUTS))
