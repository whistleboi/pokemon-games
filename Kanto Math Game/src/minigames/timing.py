"""Gym challenge minigames of timing (Jordan, 11-01). Each plays by taps alone.

- RhythmTiles: notes slide down four lanes; tap a lane as its note crosses the line.
- GymPong: bounce the Poke Ball past the Leader's Pokemon. First to 5 points.
"""
import math

import pygame

from src.minigames.base import Minigame, icon, item
from src.ui import theme
from src.config import FPS

LANE_COLORS = ((226, 84, 56), (66, 130, 220), (82, 178, 86), (236, 178, 44))


class RhythmTiles(Minigame):
    key = "rhythm"
    title = "Rhythm Tiles"
    how = "Notes slide down the four lanes. Hit each lane just as its note reaches the white line!"
    controls = (("Tap a lane", "Hit its note"), ("D F J K", "Lanes 1-4"), ("Arrow keys", "Lanes 1-4"))
    accent = (150, 70, 210)
    MISSES = 3
    KEYS = {pygame.K_d: 0, pygame.K_f: 1, pygame.K_j: 2, pygame.K_k: 3,
            pygame.K_LEFT: 0, pygame.K_DOWN: 1, pygame.K_UP: 2, pygame.K_RIGHT: 3}

    def target(self):
        return 20 + 2 * self.level

    def goal_text(self):
        return f"Hit {self.target()} notes"

    def setup(self):
        self.lane_w = 190
        self.x0 = (self.W - 4 * self.lane_w) // 2
        self.line_y = self.area.bottom - 110
        self.notes = []  # [lane, y, pid]
        self.until_next = FPS
        self.missed = 0
        self.speed = (300 + self.level * 24) / FPS
        self.flash = [0, 0, 0, 0]

    def _lane_rect(self, i):
        return pygame.Rect(self.x0 + i * self.lane_w, self.area.top + 10, self.lane_w - 8, self.area.h - 20)

    def _miss(self):
        self.missed += 1
        if self.missed >= self.MISSES:
            self.lose("Three notes slipped by!")

    def _hit(self, lane):
        near = [n for n in self.notes if n[0] == lane and abs(n[1] - self.line_y) < 70]
        if near:
            self.notes.remove(min(near, key=lambda n: abs(n[1] - self.line_y)))
            self.score += 1
            self.flash[lane] = FPS // 4
            self.check_goal()
        else:
            self._miss()

    def on_tap(self, pos):
        for i in range(4):
            if self._lane_rect(i).collidepoint(pos):
                self._hit(i)

    def on_key(self, key):
        if key in self.KEYS:
            self._hit(self.KEYS[key])

    def step(self):
        self.until_next -= 1
        if self.until_next <= 0:
            self.notes.append([self.rng.randrange(4), float(self.area.top), self.rng.choice(self.team)])
            beat = max(0.32, 0.62 - self.level * 0.03)
            self.until_next = int(FPS * beat * self.rng.choice((1, 1, 1, 2)))
        for n in self.notes:
            n[1] += self.speed
        late = [n for n in self.notes if n[1] > self.line_y + 70]
        for n in late:
            self.notes.remove(n)
            self._miss()
        self.flash = [max(0, f - 1) for f in self.flash]

    def render(self, screen):
        for i in range(4):
            lane = self._lane_rect(i)
            s = pygame.Surface(lane.size, pygame.SRCALPHA)
            s.fill((*LANE_COLORS[i], 70 if not self.flash[i] else 150))
            screen.blit(s, lane)
            pygame.draw.rect(screen, LANE_COLORS[i], lane, 3, border_radius=10)
        pygame.draw.line(screen, (255, 255, 255), (self.x0 - 10, self.line_y), (self.x0 + 4 * self.lane_w, self.line_y), 5)
        for lane, y, pid in self.notes:
            r = pygame.Rect(0, 0, self.lane_w - 40, 76)
            r.center = (self.x0 + lane * self.lane_w + (self.lane_w - 8) // 2, y)
            pygame.draw.rect(screen, (30, 30, 40), r.move(0, 4), border_radius=14)
            pygame.draw.rect(screen, LANE_COLORS[lane], r, border_radius=14)
            pygame.draw.rect(screen, (255, 255, 255), r, 3, border_radius=14)
            img = icon(self.game, pid, 72)
            screen.blit(img, img.get_rect(center=r.center))
        for i in range(self.MISSES):  # misses left, as Poke Balls
            ball = item(self.game, "poke-ball", 40)
            if i < self.missed:
                ball = ball.copy()
                ball.set_alpha(60)
            screen.blit(ball, (24 + i * 48, self.area.top + 14))


class GymPong(Minigame):
    key = "pong"
    title = "Gym Pong"
    how = "Move your paddle up and down to bounce the Poke Ball back. Get it past the other side!"
    controls = (("Drag / tap", "Move your paddle there"), ("Up / Down, W / S", "Move your paddle"))
    accent = (66, 130, 220)
    POINTS = 5

    def target(self):
        return self.POINTS

    def goal_text(self):
        return f"First to {self.POINTS} points"

    def setup(self):
        self.court = self.area.inflate(-240, -40)  # (room either side for the two Pokemon)
        self.pad_h = 150
        self.me = float(self.court.centery)
        self.aim = self.me
        self.them = float(self.court.centery)
        self.theirs = 0
        self.ace = self.team[-1]
        self._serve(1)

    def _serve(self, direction):
        self.bx, self.by = float(self.court.centerx), float(self.court.centery)
        speed = (440 + self.level * 30) / FPS
        angle = self.rng.uniform(-0.6, 0.6)
        self.vx, self.vy = direction * speed * math.cos(angle), speed * math.sin(angle)
        self.pause = FPS // 2

    def on_tap(self, pos):
        self.aim = pos[1]

    def on_motion(self, pos):
        self.aim = pos[1]

    def step(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.aim = self.me - 40
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.aim = self.me + 40
        half = self.pad_h / 2
        self.me += max(-900 / FPS, min(900 / FPS, self.aim - self.me))
        self.me = max(self.court.top + half, min(self.court.bottom - half, self.me))
        if self.vx > 0:  # the Leader's Pokemon follows the ball, not quite as fast as it
            reach = (260 + self.level * 30) / FPS
            self.them += max(-reach, min(reach, self.by - self.them))
        self.them = max(self.court.top + half, min(self.court.bottom - half, self.them))
        if self.pause:
            self.pause -= 1
            return
        self.bx += self.vx
        self.by += self.vy
        r = 22
        if self.by - r < self.court.top or self.by + r > self.court.bottom:
            self.vy = -self.vy
            self.by = max(self.court.top + r, min(self.court.bottom - r, self.by))
        left, right = self.court.left + 40, self.court.right - 40
        if self.vx < 0 and self.bx - r <= left and abs(self.by - self.me) <= half + r:
            self._bounce(self.me, 1)
        elif self.vx > 0 and self.bx + r >= right and abs(self.by - self.them) <= half + r:
            self._bounce(self.them, -1)
        elif self.bx < self.court.left:
            self.theirs += 1
            if self.theirs >= self.POINTS:
                self.lose(f"{self.leader_name}'s Pokemon won the match!")
            else:
                self._serve(1)
        elif self.bx > self.court.right:
            self.score += 1
            self.check_goal()
            if self.phase == "PLAY":
                self._serve(-1)

    def _bounce(self, paddle_y, direction):
        speed = min(1100 / FPS, math.hypot(self.vx, self.vy) * 1.06)
        angle = max(-1.0, min(1.0, (self.by - paddle_y) / (self.pad_h / 2))) * 0.9
        self.vx, self.vy = direction * speed * math.cos(angle), speed * math.sin(angle)

    def render(self, screen):
        s = pygame.Surface(self.court.size, pygame.SRCALPHA)
        s.fill((255, 255, 255, 40))
        screen.blit(s, self.court)
        pygame.draw.rect(screen, (255, 255, 255), self.court, 4, border_radius=12)
        for y in range(self.court.top + 10, self.court.bottom, 40):
            pygame.draw.line(screen, (255, 255, 255), (self.court.centerx, y), (self.court.centerx, y + 20), 3)
        f = self.game.assets.fonts["big"]
        theme.shadow_text(screen, str(self.score), f, self.court.centerx - 90, self.court.top + 50,
                          color=(255, 255, 255), shadow=(20, 20, 30), align="center")
        theme.shadow_text(screen, str(self.theirs), f, self.court.centerx + 90, self.court.top + 50,
                          color=(255, 255, 255), shadow=(20, 20, 30), align="center")
        for x, y, pid, color, flip in ((self.court.left + 40, self.me, self.partner, theme.RUN, True),
                                       (self.court.right - 40, self.them, self.ace, theme.FIGHT, False)):
            pad = pygame.Rect(0, 0, 22, self.pad_h)
            pad.center = (x, y)
            pygame.draw.rect(screen, color, pad, border_radius=10)
            pygame.draw.rect(screen, (255, 255, 255), pad, 3, border_radius=10)
            img = icon(self.game, pid, 96, flip=flip)
            screen.blit(img, img.get_rect(center=(x - 100 if flip else x + 100, y)))
        ball = item(self.game, "poke-ball", 44)
        ball = pygame.transform.rotate(ball, (pygame.time.get_ticks() // 4) % 360)
        screen.blit(ball, ball.get_rect(center=(self.bx, self.by)))
