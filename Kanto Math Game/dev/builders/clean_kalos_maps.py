"""Kalos town backgrounds from the X/Y town maps with their labels taken out (Jordan, 10-30: these look
nicer than tile-built towns). The maps (assets/backgrounds/kalos/<town>.png) carry a guide's labels:
name boxes, number tags, exit arrows and route boxes. Each one is marked by hand (LABELS), and the hole
is filled in from the picture around it, ring by ring. The guide's blank white corners are left
see-through.

Each cleaned map is fitted whole into the town screen (1280 x 540): the full height, centred, with a
blurred, darkened copy of itself filling the sides. Saved where the game looks first for a town's
background (assets/journeys/towns/<key>.png); a check sheet goes to dev/builders/out/kalos_clean/.
Vaniville uses Jordan's own cleaned copy (assets/backgrounds/kalos/town_map_clean.png).

    python dev/builders/clean_kalos_maps.py [town ...]
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

SRC = os.path.join("assets", "backgrounds", "kalos")
OUT = os.path.join("assets", "journeys", "towns")
CHECK = os.path.join("dev", "builders", "out", "kalos_clean")
TOWNS = ["ambrette_town", "aquacorde_town", "camphrier_town", "coumarine_city", "couriway_town",
         "cyllage_city", "dendemille_town", "geosenge_town", "kiloude_city", "laverre_city", "lumiose_city",
         "santalune_city", "shalour_city", "snowbelle_city", "vaniville_town"]
OWN_CLEAN = {"vaniville_town": "town_map_clean.png"}
# every label on each map, marked by hand on a grid: [x, y, w, h] in map pixels (a colour search caught
# roofs and water too, and missed labels)
LABELS = {
    "ambrette_town": [(440, 2, 70, 36), (553, 5, 170, 35), (762, 0, 45, 20), (535, 190, 35, 30), (485, 288, 35, 30),
                      (598, 320, 35, 30), (710, 255, 310, 40), (885, 305, 125, 60), (925, 365, 30, 40),
                      (800, 385, 45, 70), (390, 400, 155, 40), (448, 483, 35, 30), (148, 180, 40, 30)],
    "aquacorde_town": [(565, 0, 50, 25), (572, 130, 40, 35), (885, 758, 210, 45), (925, 812, 40, 35),
                       (572, 836, 40, 35), (205, 977, 125, 45), (245, 1033, 40, 35), (835, 993, 145, 45),
                       (888, 1098, 40, 35), (825, 1147, 165, 48), (270, 1293, 135, 90), (572, 1663, 42, 38),
                       (572, 1777, 42, 38), (560, 1888, 60, 22)],
    "camphrier_town": [(390, 160, 160, 35), (455, 262, 40, 35), (222, 540, 75, 35), (612, 543, 135, 40),
                       (135, 655, 40, 75), (550, 684, 170, 30), (540, 727, 190, 35), (618, 807, 40, 35),
                       (230, 757, 135, 40), (265, 799, 70, 35), (0, 668, 22, 40), (918, 668, 22, 40)],
    "coumarine_city": [(515, 0, 130, 20), (380, 52, 40, 35), (562, 45, 40, 35), (110, 252, 40, 35), (0, 250, 20, 40),
                       (152, 290, 95, 30), (165, 325, 40, 35), (648, 268, 75, 40), (738, 275, 30, 30),
                       (370, 355, 75, 35), (268, 395, 40, 35), (680, 452, 35, 25), (452, 530, 175, 40),
                       (505, 655, 70, 35), (698, 697, 90, 60), (805, 672, 125, 50), (722, 767, 45, 35),
                       (660, 932, 40, 35), (522, 1007, 40, 35), (522, 1109, 40, 35), (488, 1177, 105, 40),
                       (520, 1215, 40, 19)],
    "couriway_town": [(150, 0, 45, 25), (475, 8, 180, 35), (580, 140, 40, 35), (172, 158, 170, 35), (155, 415, 40, 35),
                      (320, 530, 70, 35), (563, 537, 135, 40), (595, 600, 70, 35), (395, 628, 170, 40),
                      (695, 640, 170, 35), (712, 682, 40, 35), (255, 680, 40, 35), (340, 838, 40, 35),
                      (760, 876, 40, 35), (335, 925, 45, 25)],
    "cyllage_city": [(330, 0, 40, 20), (335, 35, 40, 35), (395, 145, 75, 35), (412, 183, 35, 30), (478, 173, 165, 35),
                     (512, 225, 40, 35), (575, 237, 105, 35), (600, 275, 40, 35), (900, 215, 110, 75),
                     (918, 315, 30, 25), (588, 355, 165, 35), (437, 405, 170, 35), (288, 457, 120, 35),
                     (408, 455, 40, 35), (698, 457, 170, 35), (468, 505, 110, 35), (630, 505, 40, 35),
                     (767, 548, 40, 35), (812, 553, 206, 35), (832, 668, 40, 35), (178, 642, 35, 35),
                     (560, 785, 45, 23)],
    "dendemille_town": [(550, 0, 45, 20), (545, 52, 50, 40), (225, 150, 50, 45), (722, 180, 55, 50), (115, 645, 50, 45),
                        (632, 915, 105, 45), (770, 905, 320, 80), (0, 985, 25, 40), (272, 1075, 55, 45),
                        (410, 1078, 100, 45), (45, 1153, 250, 45), (148, 1270, 50, 45), (0, 1488, 285, 40),
                        (1070, 1695, 28, 50), (750, 1775, 100, 45)],
    "geosenge_town": [(20, 35, 280, 30), (135, 62, 45, 28), (298, 0, 16, 470), (290, 468, 40, 35), (293, 548, 40, 35),
                      (548, 860, 180, 32), (722, 903, 70, 35), (915, 912, 21, 40), (553, 985, 195, 32),
                      (538, 1018, 40, 35), (635, 1053, 40, 35), (233, 1053, 180, 32), (530, 1236, 45, 20)],
    "kiloude_city": [(510, 175, 40, 35), (652, 165, 40, 35), (800, 285, 160, 35), (865, 335, 40, 35), (568, 420, 125, 35),
                     (130, 458, 185, 35), (615, 485, 40, 35), (205, 550, 40, 35), (340, 515, 40, 35),
                     (310, 560, 15, 360), (432, 643, 170, 35), (497, 685, 40, 30), (350, 688, 40, 35),
                     (245, 750, 40, 35)],
    "laverre_city": [(395, 78, 40, 40), (140, 225, 170, 55), (188, 320, 80, 35), (155, 452, 40, 35), (528, 393, 185, 35),
                     (602, 455, 40, 40), (742, 480, 215, 35), (832, 535, 40, 40), (852, 280, 40, 35),
                     (830, 225, 80, 22), (948, 430, 40, 35), (602, 628, 40, 35), (358, 795, 120, 35),
                     (400, 865, 40, 35), (655, 760, 190, 35), (710, 832, 85, 35), (875, 925, 40, 35),
                     (885, 980, 75, 35), (1095, 930, 23, 45), (268, 1258, 50, 22)],
    "santalune_city": [(660, 412, 95, 40)],
    "shalour_city": [(310, 8, 215, 35), (35, 522, 175, 30), (100, 560, 40, 35), (510, 555, 190, 30), (102, 690, 40, 30),
                     (402, 715, 40, 35), (440, 777, 165, 30), (405, 815, 40, 35), (533, 817, 40, 35),
                     (662, 821, 40, 35), (630, 850, 40, 35), (788, 868, 40, 105), (908, 868, 20, 40),
                     (500, 1068, 45, 22)],
    "snowbelle_city": [(315, 50, 40, 35), (625, 68, 40, 35), (383, 115, 120, 35), (425, 165, 40, 35), (778, 150, 40, 35),
                       (478, 180, 215, 35), (542, 245, 40, 35), (700, 253, 195, 35), (845, 295, 40, 35),
                       (0, 228, 22, 40), (108, 255, 40, 35), (165, 335, 240, 35), (362, 380, 40, 35),
                       (542, 345, 40, 35), (540, 485, 100, 75), (0, 680, 90, 75), (85, 690, 34, 40),
                       (1095, 370, 15, 45), (208, 748, 40, 35)],
}
SIZE = (1280, 540)


def fill(img, rects):
    """Fill the holes from the picture around them, a ring at a time (each pixel the average of the
    known pixels next to it)."""
    w, h = img.get_size()
    hole = set()
    for r in rects:
        r = r.clip(img.get_rect())
        hole.update((x, y) for x in range(r.left, r.right) for y in range(r.top, r.bottom))
    while hole:
        ring = {}
        for x, y in hole:
            near = [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1))
                    if 0 <= x + dx < w and 0 <= y + dy < h and (x + dx, y + dy) not in hole]
            if near:
                cs = [img.get_at(p) for p in near]
                ring[(x, y)] = tuple(sum(c[i] for c in cs) // len(cs) for i in range(3))
        if not ring:
            break
        for p, c in ring.items():
            img.set_at(p, c)
        hole.difference_update(ring)
    return img


SNOWY = ("snowbelle_city", "dendemille_town")


def blank_mask(img, name=""):
    """The guide's empty corners: big patches of pure white reaching the map's edge (on the snowy maps,
    only flat rectangles, so the snow stays)."""
    white = pygame.mask.from_threshold(img, (255, 255, 255, 255), (6, 6, 6, 255))
    out = pygame.mask.Mask(img.get_size())
    w, h = img.get_size()
    for comp in white.connected_components(minimum=2000):
        r = comp.get_bounding_rects()[0]
        at_edge = r.left == 0 or r.top == 0 or r.right == w or r.bottom == h
        flat = comp.count() / (r.w * r.h) > 0.9
        if at_edge and (flat or name not in SNOWY):
            out.draw(comp, (0, 0))
    return out


def framed(img, name=""):
    """The whole map at the screen's height, centred, a blurred darker copy of it filling the sides;
    the guide's blank corners are see-through."""
    W, H = SIZE
    blank = blank_mask(img, name)
    img = img.convert_alpha()
    img.blit(blank.to_surface(setcolor=(0, 0, 0, 0), unsetcolor=(255, 255, 255, 255)), (0, 0),
             special_flags=pygame.BLEND_RGBA_MIN)
    solid = pygame.Surface(img.get_size())          # for the backdrop: the blanks in the map's own colour
    solid.fill(pygame.transform.average_color(img, img.get_rect(), True)[:3])
    solid.blit(img, (0, 0))
    k = H / img.get_height()
    size = (round(img.get_width() * k), H)
    if size[0] > W:  # a wide map: fit the width instead
        k = W / img.get_width()
        size = (W, round(img.get_height() * k))
    main = pygame.transform.smoothscale(img, size)
    out = pygame.Surface(SIZE)
    blur = pygame.transform.smoothscale(solid, (24, max(1, round(24 * H / W))))
    out.blit(pygame.transform.smoothscale(blur, SIZE), (0, 0))
    dark = pygame.Surface(SIZE, pygame.SRCALPHA)
    dark.fill((0, 0, 0, 110))
    out.blit(dark, (0, 0))
    out.blit(main, main.get_rect(center=(W // 2, H // 2)))
    return out


def main(names):
    pygame.init()
    pygame.display.set_mode((1, 1))
    os.makedirs(CHECK, exist_ok=True)
    for name in names:
        own = OWN_CLEAN.get(name)
        if own and os.path.isfile(os.path.join(SRC, own)):
            img = pygame.image.load(os.path.join(SRC, own)).convert()
            rects = []
        else:
            img = pygame.image.load(os.path.join(SRC, name + ".png")).convert()
            rects = [pygame.Rect(r).inflate(10, 10) for r in LABELS.get(name, [])]  # their edges too
            marked = img.copy()
            for r in rects:
                pygame.draw.rect(marked, (255, 0, 255), r, 3)
            pygame.image.save(marked, os.path.join(CHECK, name + "_marked.png"))
            fill(img, rects)
        pygame.image.save(img, os.path.join(CHECK, name + ".png"))
        pygame.image.save(framed(img, name), os.path.join(OUT, name + ".png"))
        print(f"{name:16} {len(rects):3} labels out")


if __name__ == "__main__":
    main(sys.argv[1:] or TOWNS)
