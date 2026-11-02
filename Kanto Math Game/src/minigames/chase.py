"""Gym challenge minigame: the chase (Jordan, 11-01; the idea of python-online.ch's GameGrid
"following" example). You're a small fish Pokemon collecting pearls; a big water Pokemon chases
you, turning toward you and getting faster. The region's own fish (base.local): Magikarp and Gyarados
in Kanto, Feebas and Sharpedo in Hoenn...
"""
import math

import pygame

from src.minigames.base import Minigame, icon, item, local, species_name
from src.config import FPS

PREY = (129, 223, 349, 456, 550, 692, 746, 846, 963)       # Magikarp, Remoraid, Feebas, Finneon, Basculin...
HUNTERS = (130, 230, 319, 457, 593, 693, 779, 847, 977)    # Gyarados, Kingdra, Sharpedo, Lumineon, Jellicent...


class FishEscape(Minigame):
    key = "chase"
    title = "Magikarp Escape"
    how = "Swim around to collect the pearls. A big Pokemon is chasing you, and it gets faster!"
    controls = (("Hold / drag", "Swim toward your finger"), ("Arrow keys / WASD", "Swim"))
    accent = (66, 150, 220)

    @classmethod
    def title_for(cls, game):
        return f"{species_name(game, local(game, PREY)[0])} Escape"

    def target(self):
        return 10 + self.level

    def goal_text(self):
        return f"Collect {self.target()} pearls"

    def setup(self):
        self.prey, self.hunter = local(self.game, PREY)[0], local(self.game, HUNTERS)[0]
        self.px, self.py = float(self.area.x + 200), float(self.area.centery)
        self.hx, self.hy = float(self.area.right - 200), float(self.area.centery)
        self.heading = math.pi
        self.aim = None
        self.facing_left = False
        self.bubbles = [[self.rng.randint(0, self.W), self.rng.randint(self.area.top, self.H), self.rng.randint(3, 9)]
                        for _ in range(26)]
        self._place_pearl()

    def _place_pearl(self):
        while True:
            x = self.rng.randint(self.area.x + 70, self.area.right - 70)
            y = self.rng.randint(self.area.top + 70, self.area.bottom - 60)
            if math.hypot(x - self.hx, y - self.hy) > 220:
                self.pearl = (x, y)
                return

    def on_tap(self, pos):
        self.aim = pos

    def on_motion(self, pos):
        if pygame.mouse.get_pressed()[0]:
            self.aim = pos

    def on_release(self, pos):
        self.aim = None

    def step(self):
        speed = 330 / FPS
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        if not (dx or dy) and self.aim:
            dx, dy = self.aim[0] - self.px, self.aim[1] - self.py
            if math.hypot(dx, dy) < speed:
                dx = dy = 0
        d = math.hypot(dx, dy)
        if d:
            self.px += speed * dx / d
            self.py += speed * dy / d
            self.facing_left = dx < 0
        self.px = max(self.area.x + 40, min(self.area.right - 40, self.px))
        self.py = max(self.area.top + 40, min(self.area.bottom - 40, self.py))
        # the hunter turns toward you a little at a time, and speeds up (never quite as fast as you)
        chase = min(0.92 * 330, 170 + self.level * 14 + self.seconds() * 5) / FPS
        want = math.atan2(self.py - self.hy, self.px - self.hx)
        turn = (want - self.heading + math.pi) % (2 * math.pi) - math.pi
        self.heading += max(-0.09, min(0.09, turn))
        self.hx += chase * math.cos(self.heading)
        self.hy += chase * math.sin(self.heading)
        self.hx = max(self.area.x + 60, min(self.area.right - 60, self.hx))
        self.hy = max(self.area.top + 60, min(self.area.bottom - 60, self.hy))
        if math.hypot(self.px - self.pearl[0], self.py - self.pearl[1]) < 50:
            self.score += 1
            self.check_goal()
            self._place_pearl()
        if math.hypot(self.px - self.hx, self.py - self.hy) < 70:
            self.lose(f"{species_name(self.game, self.hunter)} caught {species_name(self.game, self.prey)}!")
        for b in self.bubbles:
            b[1] -= b[2] * 0.6
            if b[1] < self.area.top:
                b[0], b[1] = self.rng.randint(0, self.W), self.H + 10

    def render(self, screen):
        water = pygame.Surface(self.area.size, pygame.SRCALPHA)
        water.fill((30, 110, 200, 110))
        screen.blit(water, self.area)
        for x, y, r in self.bubbles:
            pygame.draw.circle(screen, (200, 230, 255), (int(x), int(y)), r, 2)
        for x in range(0, self.W, 90):  # seaweed along the bottom
            sway = int(8 * math.sin(pygame.time.get_ticks() / 400 + x))
            pygame.draw.line(screen, (40, 140, 80), (x, self.area.bottom), (x + sway, self.area.bottom - 60), 6)
        glow = 4 * math.sin(pygame.time.get_ticks() / 200)
        pearl = item(self.game, "pearl", int(44 + glow))
        screen.blit(pearl, pearl.get_rect(center=self.pearl))
        hunter = icon(self.game, self.hunter, 180, flip=math.cos(self.heading) > 0)
        screen.blit(hunter, hunter.get_rect(center=(self.hx, self.hy)))
        me = icon(self.game, self.prey, 88, flip=not self.facing_left)
        screen.blit(me, me.get_rect(center=(self.px, self.py)))
