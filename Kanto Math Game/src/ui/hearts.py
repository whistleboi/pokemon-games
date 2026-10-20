"""Affection hearts (Pokemon-Amie), drawn on the Amie, party and summary screens."""
import pygame

from src.pokemon import affection

HEART_RED, HEART_EMPTY = (235, 70, 110), (90, 70, 90)


def draw_heart(surface, cx, cy, size, color):
    r = size // 4
    pygame.draw.circle(surface, color, (cx - r, cy - r // 2), r + 1)
    pygame.draw.circle(surface, color, (cx + r, cy - r // 2), r + 1)
    pygame.draw.polygon(surface, color, [(cx - 2 * r - 1, cy - r // 3), (cx + 2 * r + 1, cy - r // 3),
                                         (cx, cy + int(1.6 * r))])


def draw_hearts(surface, poke, cx, cy, size=34):
    """Five hearts centred on (cx, cy), filled up to the Pokemon's affection."""
    n = affection.hearts(poke)
    for i in range(5):
        x = cx + int((i - 2) * size * 1.25)
        draw_heart(surface, x, cy, size, HEART_RED if i < n else HEART_EMPTY)
