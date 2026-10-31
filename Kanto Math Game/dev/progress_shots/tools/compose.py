"""Build one timeline sheet and one before/after image per menu from shots/<commit>/<menu>.png.

usage: python compose.py <shots_dir> <out_dir> <menu,menu,...> <hash:date:label> ...
"""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

pygame.init()
shots, out = sys.argv[1], sys.argv[2]
menus = sys.argv[3].split(",")
commits = [a.split(":", 2) for a in sys.argv[4:]]
os.makedirs(out, exist_ok=True)

BG, BAR, TXT, SUB = (24, 28, 40), (44, 52, 74), (240, 240, 245), (170, 180, 205)
title_font = pygame.font.SysFont("segoeui", 30, bold=True)
font = pygame.font.SysFont("segoeui", 20, bold=True)
small = pygame.font.SysFont("segoeui", 17)


def tile(path, w, h, h_, d, label):
    surf = pygame.Surface((w, h + 52))
    surf.fill(BAR)
    surf.blit(font.render(f"{d}  ·  {h_}", True, TXT), (10, 4))
    surf.blit(small.render(label, True, SUB), (10, 28))
    if os.path.exists(path):
        img = pygame.image.load(path).convert()
        surf.blit(pygame.transform.smoothscale(img, (w, h)), (0, 52))
    else:
        pygame.draw.rect(surf, (60, 30, 30), (0, 52, w, h))
        surf.blit(font.render("could not render", True, TXT), (20, 52 + h // 2))
    return surf


def title_name(menu):
    return menu.replace("_", " ").title()


pygame.display.set_mode((1, 1))
for menu in menus:
    # Timeline: every commit, 4 per row.
    w, h, gap, cols = 480, 270, 12, 4
    rows = (len(commits) + cols - 1) // cols
    sheet = pygame.Surface((cols * w + (cols + 1) * gap, 60 + rows * (h + 52 + gap) + gap))
    sheet.fill(BG)
    sheet.blit(title_font.render(f"{title_name(menu)}: timeline (oldest → newest)", True, TXT), (gap, 12))
    for i, (h_, d, label) in enumerate(commits):
        x = gap + (i % cols) * (w + gap)
        y = 60 + (i // cols) * (h + 52 + gap)
        sheet.blit(tile(os.path.join(shots, h_, f"{menu}.png"), w, h, h_, d, label), (x, y))
    pygame.image.save(sheet, os.path.join(out, f"{menu}_timeline.png"))

    # Before / after: the oldest and newest commits side by side.
    w, h = 960, 540
    pair = pygame.Surface((2 * w + 3 * gap, 60 + h + 52 + gap))
    pair.fill(BG)
    pair.blit(title_font.render(f"{title_name(menu)}: before → after", True, TXT), (gap, 12))
    for i, (h_, d, label) in enumerate((commits[0], commits[-1])):
        pair.blit(tile(os.path.join(shots, h_, f"{menu}.png"), w, h, h_, d, label), (gap + i * (w + gap), 60))
    pygame.image.save(pair, os.path.join(out, f"{menu}_before_after.png"))
    print("wrote", menu)
