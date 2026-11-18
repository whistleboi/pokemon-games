"""The Orange Crew's own Gym challenges (Jordan, 11-17: the anime's tests, before 5.7's battle).

CissyChallenge (Mikan Island): the anime's two tests in one game, as Cissy sets them.
  Round 1, the Water Gun target test: targets pop up from the pool and sink again; tap one (or move the sight with the
  arrow keys and press Space) while it's up to hit it with your Water Gun. Hit enough before too many get away.
  Round 2, the Lapras race: Lapras against Cissy's Seadra across the bay. Tap (or press Space) to swim on; switch lane
  (tap above or below Lapras, or the arrow keys) to dodge the rocks, which slow you down. Reach the buoy first.
Both rounds won: the challenge is done and Cissy's battle is next."""
import math

import pygame

from src.minigames.base import Minigame, icon, species_name
from src.config import FPS


class CissyChallenge(Minigame):
    key = "cissy"
    title = "Cissy's Challenge"
    how = ("Round 1: hit the targets with Water Gun as they pop up from the pool. "
           "Round 2: race Lapras against Cissy's Seadra across the bay!")
    controls = (("Tap a target / tap to swim", "Fire / swim on"), ("Arrows + Space", "Aim and fire / switch lane and swim"))
    accent = (40, 150, 230)
    in_pool = False
    win_line = "You passed both of Cissy's tests! Now for the battle."
    HITS = 8           # targets to hit in round 1
    MISSES = 6         # targets you may let sink
    LANES = 3

    def target(self):
        return self.HITS if self.round == 1 else 100

    def goal_text(self):
        return (f"Round 1: hit {self.HITS} targets (missed {self.missed}/{self.MISSES})" if self.round == 1
                else "Round 2: reach the buoy before Seadra")

    def progress(self):
        if self.round == 1:
            return self.hits, self.HITS
        return int(min(100, self.me)), 100

    def setup(self):
        self.round = 1
        self.hits = self.missed = 0
        self.targets = []          # [x, y, frames left]
        self.sight = [self.area.centerx, self.area.centery]
        self.splash = []           # [x, y, frames]
        self.next_pop = FPS // 2
        self.lane, self.me, self.foe, self.boost = 1, 0.0, 0.0, 0.0
        self.rocks = []            # [lane, distance]
        self.slow = 0

    # ---------------------------------------------------------------- round 1
    def _fire(self, pos):
        self.splash.append([pos[0], pos[1], 14])
        for t in list(self.targets):
            if math.hypot(t[0] - pos[0], t[1] - pos[1]) < 46:
                self.targets.remove(t)
                self.hits += 1
                if self.hits >= self.HITS:
                    self._round2()
                return

    def _round2(self):
        self.round = 2
        self.targets = []
        self.rocks = [[self.rng.randrange(self.LANES), 12 + i * 9 + self.rng.randint(0, 4)] for i in range(10)]

    # ---------------------------------------------------------------- round 2
    def _lane_y(self, lane):
        top = self.area.top + 120
        return top + lane * (self.area.h - 200) // (self.LANES - 1)

    def _swim(self):
        self.boost = min(3.0, self.boost + 0.9)

    def on_tap(self, pos):
        if self.round == 1:
            self._fire(pos)
            return
        ly = self._lane_y(self.lane)
        if pos[1] < ly - 60 and self.lane > 0:
            self.lane -= 1
        elif pos[1] > ly + 60 and self.lane < self.LANES - 1:
            self.lane += 1
        else:
            self._swim()

    def on_key(self, key):
        if self.round == 1:
            step = 60
            if key in (pygame.K_LEFT, pygame.K_a): self.sight[0] -= step
            elif key in (pygame.K_RIGHT, pygame.K_d): self.sight[0] += step
            elif key in (pygame.K_UP, pygame.K_w): self.sight[1] -= step
            elif key in (pygame.K_DOWN, pygame.K_s): self.sight[1] += step
            elif key in (pygame.K_SPACE, pygame.K_RETURN): self._fire(tuple(self.sight))
            self.sight[0] = max(self.area.x + 40, min(self.area.right - 40, self.sight[0]))
            self.sight[1] = max(self.area.top + 40, min(self.area.bottom - 40, self.sight[1]))
            return
        if key in (pygame.K_UP, pygame.K_w) and self.lane > 0:
            self.lane -= 1
        elif key in (pygame.K_DOWN, pygame.K_s) and self.lane < self.LANES - 1:
            self.lane += 1
        elif key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_RIGHT, pygame.K_d):
            self._swim()

    def step(self):
        for s in list(self.splash):
            s[2] -= 1
            if s[2] <= 0:
                self.splash.remove(s)
        if self.round == 1:
            self.next_pop -= 1
            if self.next_pop <= 0:
                self.next_pop = max(FPS // 3, FPS - self.level * 3) + self.rng.randint(0, FPS // 2)
                self.targets.append([self.rng.randint(self.area.x + 80, self.area.right - 80),
                                     self.rng.randint(self.area.top + 80, self.area.bottom - 80), int(FPS * (1.8 - self.level * 0.08))])
            for t in list(self.targets):
                t[2] -= 1
                if t[2] <= 0:
                    self.targets.remove(t)
                    self.missed += 1
                    if self.missed >= self.MISSES:
                        self.lose("Too many targets got away. Cissy wants a sharper aim!")
            return
        # round 2: you swim on your taps; Seadra keeps a steady pace
        speed = 0.12 + self.boost * 0.16
        if self.slow:
            self.slow -= 1
            speed *= 0.3
        self.boost = max(0.0, self.boost - 0.035)
        self.me += speed
        self.foe += 0.30 + self.level * 0.012
        for r in self.rocks:
            if r[0] == self.lane and abs(r[1] - self.me) < 0.6 and not self.slow:
                self.slow = FPS
        if self.me >= 100:
            self.score = 1
            self.win()
        elif self.foe >= 100:
            self.lose("Seadra reached the buoy first! Tap faster and dodge the rocks.")

    def render(self, screen):
        pool = pygame.Surface(self.area.size, pygame.SRCALPHA)
        pool.fill((40, 130, 210, 150))
        screen.blit(pool, self.area)
        t = pygame.time.get_ticks()
        for y in range(self.area.top + 30, self.area.bottom, 70):   # ripples
            for x in range(0, self.W, 120):
                dx = int(20 * math.sin(t / 500 + y))
                pygame.draw.arc(screen, (170, 215, 250), (x + dx, y, 60, 18), 0, math.pi, 2)
        if self.round == 1:
            for x, y, left in self.targets:
                r = 34 if left > 10 else 34 * left // 10
                pygame.draw.circle(screen, (240, 240, 240), (x, y), r)
                pygame.draw.circle(screen, (220, 40, 40), (x, y), max(1, r * 2 // 3))
                pygame.draw.circle(screen, (240, 240, 240), (x, y), max(1, r // 3))
            for x, y, k in self.splash:
                pygame.draw.circle(screen, (220, 240, 255), (x, y), 50 - k * 2, 3)
            pygame.draw.circle(screen, (255, 220, 40), self.sight, 30, 3)
            return
        span = self.W - 260
        fx = lambda d: 120 + int(span * d / 100)
        pygame.draw.line(screen, (255, 120, 40), (fx(100), self.area.top + 20), (fx(100), self.area.bottom - 20), 6)
        for lane, d in self.rocks:
            if d < 100:
                pygame.draw.circle(screen, (110, 100, 90), (fx(d), self._lane_y(lane)), 24)
        foe = icon(self.game, 117, 96)
        screen.blit(foe, foe.get_rect(center=(fx(self.foe), self.area.bottom - 40)))
        me = icon(self.game, 131, 112)
        screen.blit(me, me.get_rect(center=(fx(self.me), self._lane_y(self.lane))))
