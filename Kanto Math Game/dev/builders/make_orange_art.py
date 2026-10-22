"""Orange Islands art: Pinkan (pink) and Crystal Onix sprites from the base sprites, and the five
Orange League badges. Run from the game folder: python make_orange_art.py <scratchpad>"""
import math
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame  # noqa: E402

sys.path.insert(0, sys.argv[1])
from orange_special import PINKAN, CRYSTAL_ONIX  # noqa: E402

pygame.display.init()
pygame.display.set_mode((1, 1))
SP = "assets/sprites/pokemon"


def recolor(src, dst, fn):
    if not os.path.exists(src):
        return False
    img = pygame.image.load(src).convert_alpha()
    for x in range(img.get_width()):
        for y in range(img.get_height()):
            r, g, b, a = img.get_at((x, y))
            if a:
                img.set_at((x, y), fn(r, g, b, a))
    pygame.image.save(img, dst)
    return True


def pink(r, g, b, a):
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    if lum < 40:  # keep outlines dark
        return (int(lum * 1.1), int(lum * 0.6), int(lum * 0.8), a)
    k = lum / 255
    return (min(255, int(130 + 125 * k)), int(60 + 150 * k * k), int(110 + 120 * k), a)


def crystal(r, g, b, a):
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    if lum < 40:
        return (40, 70, 110, a)
    k = lum / 255
    return (int(150 + 90 * k), int(200 + 50 * k), 255, min(a, 205))


made = 0
for sid, base in list(PINKAN.items()) + [(CRYSTAL_ONIX, 95)]:
    fn = crystal if sid == CRYSTAL_ONIX else pink
    for d in (SP, f"{SP}/back", f"{SP}/shiny"):
        made += recolor(f"{d}/{base}.png", f"{d}/{sid}.png", fn)
print("sprites:", made)

# ---- Badges (128x128): Coral-Eye, Sea Ruby, Spike Shell, Jade Star, Winner's Trophy.
INK = (40, 30, 30)


def star(c, r1, r2, n=5, rot=-math.pi / 2):
    return [(c[0] + math.cos(rot + i * math.pi / n) * (r1 if i % 2 == 0 else r2),
             c[1] + math.sin(rot + i * math.pi / n) * (r1 if i % 2 == 0 else r2)) for i in range(2 * n)]


def badge(i, draw):
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    draw(s)
    pygame.image.save(s, f"assets/badges/orange_{i}.png")


def coral_eye(s):
    for ang in (-2.4, -1.9, -1.2, -0.7):  # coral branches
        x, y = 64 + math.cos(ang) * 50, 70 + math.sin(ang) * 50
        pygame.draw.line(s, INK, (64, 70), (x, y), 14)
        pygame.draw.line(s, (250, 120, 150), (64, 70), (x, y), 9)
    pygame.draw.ellipse(s, INK, (14, 50, 100, 52))
    pygame.draw.ellipse(s, (255, 170, 190), (19, 55, 90, 42))
    pygame.draw.circle(s, INK, (64, 76), 18)
    pygame.draw.circle(s, (60, 150, 220), (64, 76), 14)
    pygame.draw.circle(s, (255, 255, 255), (59, 71), 4)


def sea_ruby(s):
    pts = [(64, 8), (112, 46), (64, 120), (16, 46)]
    pygame.draw.polygon(s, INK, pts)
    pygame.draw.polygon(s, (220, 30, 60), [(64, 16), (104, 47), (64, 110), (24, 47)])
    pygame.draw.polygon(s, (255, 110, 130), [(64, 16), (84, 47), (64, 60), (44, 47)])
    pygame.draw.arc(s, (80, 170, 255), (20, 70, 88, 40), math.pi, 2 * math.pi, 6)


def spike_shell(s):
    pygame.draw.polygon(s, INK, star((64, 66), 60, 40, 8))
    pygame.draw.polygon(s, (240, 170, 80), star((64, 66), 54, 36, 8))
    for r, col in ((30, (255, 220, 150)), (20, (230, 150, 60)), (10, (255, 230, 180))):
        pygame.draw.circle(s, INK, (64, 66), r + 3)
        pygame.draw.circle(s, col, (64, 66), r)


def jade_star(s):
    pygame.draw.polygon(s, INK, star((64, 66), 62, 28))
    pygame.draw.polygon(s, (40, 170, 90), star((64, 66), 55, 24))
    pygame.draw.polygon(s, (130, 230, 160), star((60, 60), 22, 10))


def trophy(s):
    gold, dark = (250, 200, 50), (190, 130, 20)
    pygame.draw.arc(s, INK, (6, 22, 40, 44), math.pi / 2, 3 * math.pi / 2, 9)
    pygame.draw.arc(s, INK, (82, 22, 40, 44), -math.pi / 2, math.pi / 2, 9)
    pygame.draw.polygon(s, INK, [(22, 12), (106, 12), (90, 74), (38, 74)])
    pygame.draw.polygon(s, gold, [(28, 17), (100, 17), (86, 69), (42, 69)])
    pygame.draw.rect(s, INK, (54, 72, 20, 26))
    pygame.draw.rect(s, dark, (58, 72, 12, 24))
    pygame.draw.rect(s, INK, (30, 96, 68, 22), border_radius=4)
    pygame.draw.rect(s, (230, 120, 30), (35, 100, 58, 14), border_radius=3)
    pygame.draw.polygon(s, (255, 250, 200), star((64, 40), 14, 6))


for i, fn in enumerate((coral_eye, sea_ruby, spike_shell, jade_star, trophy), start=1):
    badge(i, fn)
print("badges: 5")
