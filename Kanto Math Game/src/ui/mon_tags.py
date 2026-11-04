"""Small drawing helpers for Pokemon: the shiny and G-Max tags, and fitting a sprite in a box."""

import pygame
from src.config import WHITE


G_MAX_RED = (220, 30, 70)


def _draw_gmax_tag(screen, font, x, y):
    """Small red "G-MAX" badge marking a Pokemon with the Gigantamax Factor."""
    label = font.render("G-MAX", True, WHITE)
    box = label.get_rect(topleft=(x, y)).inflate(10, 6)
    pygame.draw.rect(screen, G_MAX_RED, box, border_radius=6)
    pygame.draw.rect(screen, WHITE, box, 2, border_radius=6)
    screen.blit(label, label.get_rect(center=box.center))


SHINY_GOLD = (255, 204, 40)


def draw_shiny_star(screen, cx, cy, r):
    """The games' shiny mark: a gold five-point star with a dark edge (Summary, PC Box)."""
    import math
    pts = [(cx + (r if k % 2 == 0 else r * 0.45) * math.sin(math.pi * k / 5),
            cy - (r if k % 2 == 0 else r * 0.45) * math.cos(math.pi * k / 5)) for k in range(10)]
    pygame.draw.polygon(screen, SHINY_GOLD, pts)
    pygame.draw.polygon(screen, (120, 72, 0), pts, max(1, r // 6))


def _draw_shiny_tag(screen, font, x, y):
    """A gold "SHINY" badge with the star, for the Summary's portrait."""
    label = font.render("SHINY", True, (90, 54, 0))
    box = pygame.Rect(x, y, label.get_width() + 40, label.get_height() + 8)
    pygame.draw.rect(screen, (255, 236, 150), box, border_radius=8)
    pygame.draw.rect(screen, (196, 140, 20), box, 2, border_radius=8)
    draw_shiny_star(screen, box.x + 16, box.centery, 10)
    screen.blit(label, label.get_rect(midleft=(box.x + 30, box.centery)))
    return box


def fit_sprite(img, max_w, max_h):
    """A Pokemon sprite without its empty margin, scaled (whole pixels where it can) to fit."""
    ink = img.get_bounding_rect()
    if ink.w and ink.h:
        img = img.subsurface(ink).copy()
    k = min(max_w / img.get_width(), max_h / img.get_height())
    return pygame.transform.scale(img, (max(1, int(img.get_width() * k)), max(1, int(img.get_height() * k))))
