"""Moving backdrops for the big moments (Jordan, 11-07): evolving, an Egg hatching, a fossil coming back to
life. Each scene picks one at random (an Egg hatches in front of the softer ones). All drawn with pygame
shapes, cheap enough for a phone:

  dome     a glowing dome of light (after the evolution screen in Pokemon Journeys), turning light rays,
           sparkles drifting up
  stars    a deep night sky: twinkling stars and a slowly turning ring of light
  prism    rainbow rays turning around the middle, rings pulsing outward
  bubbles  a soft warm glow with bubbles rising"""
import math
import random

import pygame

KINDS = ("dome", "stars", "prism", "bubbles")
HATCH_KINDS = ("dome", "bubbles", "stars")

RAINBOW = [(255, 120, 120), (255, 190, 100), (255, 240, 120), (130, 230, 140), (120, 200, 255), (190, 150, 255)]


def _vertical(size, top, bottom):
    w, h = size
    surf = pygame.Surface(size)
    for y in range(h):
        k = y / max(1, h - 1)
        surf.fill(tuple(int(a + (b - a) * k) for a, b in zip(top, bottom)), (0, y, w, 1))
    return surf


def _dome(size, sky, glow, floor):
    """A dark sky with a big dome of light rising from below (bands of colour, white at the bottom)."""
    w, h = size
    surf = _vertical(size, sky, tuple(int(c * 0.7) for c in sky))
    cx, cy = w // 2, int(h * 1.05)
    rx, ry = int(w * 0.62), int(h * 0.98)
    for i in range(14, -1, -1):  # (the outside band first)
        k = i / 14
        col = tuple(int(g + (f - g) * (1 - k) ** 2) for g, f in zip(glow, floor))
        pygame.draw.ellipse(surf, col, (cx - rx * (0.55 + 0.45 * k), cy - ry * (0.55 + 0.45 * k),
                                        2 * rx * (0.55 + 0.45 * k), 2 * ry * (0.55 + 0.45 * k)))
    pygame.draw.rect(surf, floor, (0, int(h * 0.72), w, h))
    return surf


class SceneBackdrop:
    def __init__(self, size, kind=None, hatching=False, rng=None):
        self.rng = rng or random.Random()
        self.kind = kind or self.rng.choice(HATCH_KINDS if hatching else KINDS)
        self.size = (w, h) = size
        self.t = 0
        if self.kind == "dome":
            look = self.rng.choice([((60, 64, 64), (64, 190, 160), (248, 248, 248)),     # Journeys' green
                                    ((50, 44, 80), (150, 120, 230), (250, 246, 255)),    # violet
                                    ((70, 50, 40), (240, 160, 80), (255, 250, 236))])   # sunrise
            self.base = _dome(size, *look)
            self.ray = (255, 255, 255)
        elif self.kind == "stars":
            self.base = _vertical(size, (10, 12, 40), (50, 30, 90))
            self.stars = [(self.rng.uniform(0, w), self.rng.uniform(0, h), self.rng.uniform(0, 6.28),
                           self.rng.choice((1, 1, 2, 2, 3))) for _ in range(90)]
        elif self.kind == "prism":
            self.base = _vertical(size, (34, 30, 60), (90, 70, 120))
        else:
            self.base = _vertical(size, (255, 214, 200), (255, 246, 226))
        self.motes = []  # (x, y, speed, size, colour): sparkles or bubbles rising
        for _ in range(40):
            self.motes.append(self._mote(self.rng.uniform(0, h)))

    def _mote(self, y=None):
        w, h = self.size
        col = self.rng.choice(RAINBOW) if self.kind == "prism" else (255, 255, 255)
        r = self.rng.uniform(4, 14) if self.kind == "bubbles" else self.rng.uniform(1.5, 4)
        return [self.rng.uniform(0, w), h + 20 if y is None else y, self.rng.uniform(0.6, 2.2), r, col,
                self.rng.uniform(0, 6.28)]

    def update(self):
        self.t += 1
        for m in self.motes:
            m[1] -= m[2]
            m[0] += math.sin(self.t / 30 + m[5]) * 0.5
            if m[1] < -20:
                m[:] = self._mote()

    def _rays(self, screen, center, count, colours, alpha, spin, length):
        layer = pygame.Surface(self.size, pygame.SRCALPHA)
        for i in range(count):
            a0 = spin + i * 2 * math.pi / count
            a1 = a0 + math.pi / count * 0.55
            pts = [center, (center[0] + math.cos(a0) * length, center[1] + math.sin(a0) * length),
                   (center[0] + math.cos(a1) * length, center[1] + math.sin(a1) * length)]
            col = colours[i % len(colours)]
            pygame.draw.polygon(layer, (*col, alpha), pts)
        screen.blit(layer, (0, 0))

    def draw(self, screen, center=None):
        """The backdrop, its light centred on center (the Pokemon) or the middle of the screen."""
        w, h = self.size
        cx, cy = center or (w // 2, int(h * 0.45))
        screen.blit(self.base, (0, 0))
        spin = self.t / 240
        if self.kind == "dome":
            self._rays(screen, (cx, cy), 12, [self.ray], 38, spin, max(w, h))
        elif self.kind == "stars":
            for x, y, ph, r in self.stars:
                k = 0.5 + 0.5 * math.sin(self.t / 18 + ph)
                pygame.draw.circle(screen, (int(160 + 95 * k),) * 3, (int(x), int(y)), r)
            layer = pygame.Surface(self.size, pygame.SRCALPHA)
            for i in range(3):
                rad = int(min(w, h) * (0.22 + 0.08 * i) + 6 * math.sin(self.t / 25 + i))
                pygame.draw.circle(layer, (180, 200, 255, 70 - 18 * i), (cx, cy), rad, 4)
            screen.blit(layer, (0, 0))
        elif self.kind == "prism":
            self._rays(screen, (cx, cy), 18, RAINBOW, 46, spin, max(w, h))
            layer = pygame.Surface(self.size, pygame.SRCALPHA)
            for i in range(4):
                k = ((self.t / 90) + i / 4) % 1.0
                pygame.draw.circle(layer, (255, 255, 255, int(110 * (1 - k))), (cx, cy), int(40 + k * max(w, h) * 0.6), 3)
            screen.blit(layer, (0, 0))
        else:
            glow = pygame.Surface(self.size, pygame.SRCALPHA)
            pulse = 0.85 + 0.15 * math.sin(self.t / 40)
            for i in range(6, 0, -1):
                pygame.draw.circle(glow, (255, 255, 255, 22), (cx, cy), int(min(w, h) * 0.07 * i * pulse))
            screen.blit(glow, (0, 0))
        layer = pygame.Surface(self.size, pygame.SRCALPHA)
        for x, y, _s, r, col, ph in self.motes:
            if self.kind == "bubbles":
                pygame.draw.circle(layer, (190, 215, 255, 70), (int(x), int(y)), int(r))
                pygame.draw.circle(layer, (120, 160, 230, 190), (int(x), int(y)), int(r), 2)
                pygame.draw.circle(layer, (255, 255, 255, 170), (int(x - r / 3), int(y - r / 3)), max(1, int(r / 4)))
            else:
                k = 0.5 + 0.5 * math.sin(self.t / 10 + ph)
                pygame.draw.circle(layer, (*col, int(120 + 120 * k)), (int(x), int(y)), max(1, int(r)))
        screen.blit(layer, (0, 0))


def text_band(screen, y, height=90):
    """A dark see-through strip, so the scene's white words read over a bright backdrop."""
    band = pygame.Surface((screen.get_width(), height), pygame.SRCALPHA)
    band.fill((10, 14, 24, 150))
    screen.blit(band, (0, int(y - height / 2)))
