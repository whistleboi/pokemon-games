"""Gym challenge minigames: the action ones (Jordan, 11-01). Each plays by taps alone.

- PidgeyFlight: tap to flap through the gaps between rock pillars.
- PonytaDash: tap to jump the rocks and logs on the track; keep running.
- BerryCatch: slide the basket to catch falling berries; a falling Voltorb costs a heart.
- RouteCrossing: hop across the lanes where wild Pokemon stampede (like Crossy Road).
"""
import math

import pygame

from src.minigames.base import Minigame, icon, item, local, species_name
from src.config import FPS

ROCK = (124, 98, 72)
ROCK_DARK = (78, 60, 44)
ROCK_LIGHT = (164, 136, 104)
BERRIES = ("cheri-berry", "pecha-berry", "razz-berry", "aspear-berry", "chesto-berry", "bluk-berry")
# Each game's Pokemon, the region's own where it has one (base.local): the first native one wins.
FLYERS = (16, 163, 276, 396, 519, 661, 731, 821, 940)       # Pidgey, Hoothoot, Taillow, Starly, Pidove...
RUNNERS = (77, 234, 309, 403, 522, 672, 749, 835, 921)      # Ponyta, Stantler, Electrike, Shinx, Blitzle...
CATCHERS = (113, 241, 357, 440, 531, 659, 734, 819, 928)    # Chansey, Miltank, Tropius, Happiny, Audino...
HAZARDS = (100, 204, 590, 771, 837)                         # Voltorb, Pineco, Foongus, Pyukumuku, Rolycoly
STAMPEDE = (128, 85, 78, 111, 232, 234, 241, 323, 400, 522, 523, 626, 586, 672, 673, 749, 750, 831, 832,
            915, 916)                                       # Tauros, Dodrio, Rapidash... Wooloo, Lechonk


def _rock_block(screen, rect):
    """A pillar of stacked stone: the Gym's obstacles."""
    if rect.h <= 0:
        return
    pygame.draw.rect(screen, ROCK_DARK, rect.inflate(8, 0))
    pygame.draw.rect(screen, ROCK, rect)
    for y in range(rect.y + 6, rect.bottom, 34):  # the stones' seams
        pygame.draw.line(screen, ROCK_DARK, (rect.x, y), (rect.right, y), 3)
        off = 18 if (y // 34) % 2 else 46
        pygame.draw.line(screen, ROCK_DARK, (rect.x + off, y), (rect.x + off, min(rect.bottom, y + 34)), 3)
    pygame.draw.line(screen, ROCK_LIGHT, (rect.x + 6, rect.y), (rect.x + 6, rect.bottom), 4)


class PidgeyFlight(Minigame):
    key = "flight"
    title = "Pidgey Flight"
    how = "Flap to stay in the air. Fly through the gaps between the rocks!"
    controls = (("Tap", "Flap"), ("Space / Up / W", "Flap"))
    accent = (196, 150, 84)

    @classmethod
    def title_for(cls, game):
        return f"{species_name(game, local(game, FLYERS)[0])} Flight"

    def target(self):
        return 6 + self.level

    def goal_text(self):
        return f"Fly through {self.target()} gaps"

    def setup(self):
        self.x = self.W * 0.24
        self.y = self.area.centery
        self.vy = 0.0
        self.species = local(self.game, FLYERS)[0]
        self.gap = max(200, 280 - self.level * 10)
        self.speed = (240 + self.level * 14) / FPS
        self.pillars = []
        self.next_x = self.W + 80

    def _flap(self):
        self.vy = -560 / FPS

    def on_tap(self, pos):
        self._flap()

    def on_key(self, key):
        if key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
            self._flap()

    def step(self):
        self.vy += 1500 / FPS / FPS
        self.y += self.vy
        if self.next_x - self.speed <= self.W + 80 or not self.pillars:
            lo, hi = self.area.top + self.gap // 2 + 40, self.area.bottom - self.gap // 2 - 40
            self.pillars.append([self.next_x, self.rng.randint(lo, hi), False])
            self.next_x += 400
        self.next_x -= self.speed
        for p in self.pillars:
            p[0] -= self.speed
            if not p[2] and p[0] + 90 < self.x:
                p[2] = True
                self.score += 1
                self.check_goal()
        self.pillars = [p for p in self.pillars if p[0] > -120]
        me = pygame.Rect(0, 0, 54, 44)
        me.center = (self.x, self.y)
        if me.top < self.area.top or me.bottom > self.area.bottom:
            self.lose(f"{species_name(self.game, self.species)} flew too far and had to land!")
        for x, gy, _ in self.pillars:
            top = pygame.Rect(x, self.area.top, 90, gy - self.gap // 2 - self.area.top)
            bottom = pygame.Rect(x, gy + self.gap // 2, 90, self.area.bottom - gy - self.gap // 2)
            if me.colliderect(top) or me.colliderect(bottom):
                self.lose(f"{species_name(self.game, self.species)} bumped into a rock!")

    def render(self, screen):
        for x, gy, _ in self.pillars:
            _rock_block(screen, pygame.Rect(x, self.area.top, 90, gy - self.gap // 2 - self.area.top))
            _rock_block(screen, pygame.Rect(x, gy + self.gap // 2, 90, self.area.bottom - gy - self.gap // 2))
        img = icon(self.game, self.species, 104, flip=True)
        tilt = max(-30, min(40, -self.vy * FPS / 18))
        img = pygame.transform.rotate(img, tilt)
        screen.blit(img, img.get_rect(center=(self.x, self.y)))


class PonytaDash(Minigame):
    key = "dash"
    title = "Ponyta Dash"
    how = "Jump over the rocks and logs on the track. Keep running!"
    controls = (("Tap", "Jump"), ("Space / Up / W", "Jump"))
    accent = (232, 120, 48)

    @classmethod
    def title_for(cls, game):
        return f"{species_name(game, local(game, RUNNERS)[0])} Dash"

    def target(self):
        return 20 + 2 * self.level

    def goal_text(self):
        return f"Run for {self.target()} seconds"

    def progress(self):
        return int(self.seconds()), self.target()

    def setup(self):
        self.ground = self.area.bottom - 90
        self.species = local(self.game, RUNNERS)[0]
        self.x = self.W * 0.2
        self.y = self.ground
        self.vy = 0.0
        self.obstacles = []
        self.until_next = FPS
        self.scroll = 0.0

    def _jump(self):
        if self.y >= self.ground - 1:
            self.vy = -980 / FPS

    def on_tap(self, pos):
        self._jump()

    def on_key(self, key):
        if key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
            self._jump()

    def _speed(self):
        return (420 + self.level * 20 + self.seconds() * 8) / FPS

    def step(self):
        self.vy += 2700 / FPS / FPS
        self.y = min(self.ground, self.y + self.vy)
        if self.y >= self.ground:
            self.vy = 0
        speed = self._speed()
        self.scroll = (self.scroll + speed) % 80
        self.until_next -= 1
        if self.until_next <= 0:
            kind = self.rng.choice(("rock", "rock", "log"))
            w, h = (70, 62) if kind == "rock" else (110, 44)
            self.obstacles.append([float(self.W + 40), kind, w, h])
            self.until_next = int(FPS * self.rng.uniform(0.9, 1.7) * (420 / (speed * FPS)) ** 0.5)
        for o in self.obstacles:
            o[0] -= speed
        self.obstacles = [o for o in self.obstacles if o[0] > -150]
        me = pygame.Rect(0, 0, 60, 56)
        me.midbottom = (self.x, self.y)
        for x, kind, w, h in self.obstacles:
            if me.colliderect(pygame.Rect(x + 8, self.ground - h + 8, w - 16, h - 8)):
                self.lose(f"{species_name(self.game, self.species)} tripped on a {kind}!")
        self.check_goal()

    def render(self, screen):
        pygame.draw.rect(screen, (120, 96, 64), (0, self.ground, self.W, self.area.bottom - self.ground))
        pygame.draw.line(screen, (70, 54, 36), (0, self.ground), (self.W, self.ground), 4)
        for x in range(-80, self.W + 80, 80):  # the track's ruts, scrolling past
            sx = x - self.scroll
            pygame.draw.line(screen, (96, 76, 50), (sx, self.ground + 30), (sx + 40, self.ground + 30), 4)
        for x, kind, w, h in self.obstacles:
            r = pygame.Rect(x, self.ground - h, w, h)
            if kind == "rock":
                pygame.draw.ellipse(screen, ROCK_DARK, r.inflate(6, 6))
                pygame.draw.ellipse(screen, (150, 150, 158), r)
                pygame.draw.ellipse(screen, (196, 196, 204), (r.x + 12, r.y + 8, r.w // 3, r.h // 4))
            else:
                pygame.draw.rect(screen, (92, 58, 30), r, border_radius=18)
                pygame.draw.rect(screen, (140, 92, 50), r.inflate(-8, -12), border_radius=14)
                pygame.draw.circle(screen, (196, 150, 98), (r.right - 18, r.centery), 14)
        img = icon(self.game, self.species, 112, flip=True)
        screen.blit(img, img.get_rect(midbottom=(self.x, self.y + 12)))


class BerryCatch(Minigame):
    key = "catch"
    title = "Berry Catch"
    how = "Slide the basket left and right. Catch the berries, but not the Pokemon that fall too!"
    controls = (("Tap / drag", "Move the basket there"), ("Left / Right, A / D", "Move the basket"))
    accent = (82, 178, 86)
    HEARTS = 3

    def target(self):
        return 15 + self.level

    def goal_text(self):
        return f"Catch {self.target()} berries"

    def setup(self):
        self.bx = self.W / 2
        self.aim = self.bx
        self.catcher, self.hazard = local(self.game, CATCHERS)[0], local(self.game, HAZARDS)[0]
        self.hearts = self.HEARTS
        self.falling = []
        self.until_next = 10
        self.hurt = 0

    def on_tap(self, pos):
        self.aim = pos[0]

    def on_motion(self, pos):
        if pygame.mouse.get_pressed()[0]:
            self.aim = pos[0]

    def step(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.aim = self.bx - 60
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.aim = self.bx + 60
        self.bx += max(-700 / FPS, min(700 / FPS, self.aim - self.bx))
        self.bx = max(80, min(self.W - 80, self.bx))
        self.until_next -= 1
        if self.until_next <= 0:
            bad = self.rng.random() < 0.22 + self.level * 0.02
            self.falling.append([self.rng.randint(80, self.W - 80), float(self.area.top), bad,
                                 self.rng.choice(BERRIES), (200 + self.level * 18 + self.rng.randint(0, 90)) / FPS])
            self.until_next = max(8, int(FPS * (0.9 - self.level * 0.05)))
        basket = pygame.Rect(0, 0, 150, 40)
        basket.midtop = (self.bx, self.area.bottom - 110)
        keep = []
        for f in self.falling:
            f[1] += f[4]
            r = pygame.Rect(0, 0, 50, 50)
            r.center = (f[0], f[1])
            if r.colliderect(basket):
                if f[2]:
                    self.hearts -= 1
                    self.hurt = FPS // 2
                    if self.hearts <= 0:
                        self.lose(f"Too many {species_name(self.game, self.hazard)} landed in the basket!")
                else:
                    self.score += 1
                    self.check_goal()
            elif f[1] < self.area.bottom + 40:
                keep.append(f)
        self.falling = keep
        self.hurt = max(0, self.hurt - 1)

    def render(self, screen):
        for x, y, bad, berry, _v in self.falling:
            img = icon(self.game, self.hazard, 72) if bad else item(self.game, berry, 52)
            screen.blit(img, img.get_rect(center=(x, y)))
        by = self.area.bottom - 110
        chansey = icon(self.game, self.catcher, 96)
        screen.blit(chansey, chansey.get_rect(midbottom=(self.bx, by + 16)))
        basket = pygame.Rect(0, 0, 150, 56)
        basket.midtop = (self.bx, by + 4)
        color = (220, 80, 60) if self.hurt else (176, 120, 60)
        pygame.draw.rect(screen, (96, 60, 28), basket.inflate(6, 6), border_radius=14)
        pygame.draw.rect(screen, color, basket, border_radius=12)
        for x in range(basket.x + 16, basket.right - 8, 22):  # the weave
            pygame.draw.line(screen, (120, 78, 36), (x, basket.y + 6), (x, basket.bottom - 6), 3)
        pygame.draw.line(screen, (120, 78, 36), (basket.x + 6, basket.centery), (basket.right - 6, basket.centery), 3)
        for i in range(self.HEARTS):
            ball = item(self.game, "poke-ball", 40)
            if i >= self.hearts:
                ball = ball.copy()
                ball.set_alpha(60)
            screen.blit(ball, (24 + i * 48, self.area.top + 14))


class RouteCrossing(Minigame):
    key = "crossing"
    title = "Route Crossing"
    how = "Hop across the lanes where wild Pokemon stampede. Reach the GOAL on the other side!"
    controls = (("Tap above / below", "Hop forward / back"), ("Tap left / right", "Hop sideways"),
                ("Arrow keys / WASD", "Hop"))
    accent = (66, 130, 220)
    ROWS = 9

    def target(self):
        return 2 if self.level < 4 else 3

    def goal_text(self):
        return f"Cross the route {self.target()} times"

    def setup(self):
        self.cell = (self.area.h - 20) // (self.ROWS + 2)
        self.cols = self.W // self.cell
        self.top = self.area.top + 10
        self.lanes = []
        herd = local(self.game, STAMPEDE, n=4)
        for row in range(self.ROWS):  # row 0 is just below the goal
            road = row % 3 != 1 or self.level >= 5
            direction = 1 if row % 2 else -1
            speed = self.rng.uniform(110, 190 + self.level * 20) / FPS
            runners = []
            if road:
                gap = self.rng.randint(4, 6) * self.cell
                x = self.rng.uniform(0, gap)
                while x < self.W + gap:
                    runners.append(x)
                    x += gap + self.rng.randint(0, 2) * self.cell
            self.lanes.append({"road": road, "dir": direction, "speed": speed, "runners": runners,
                               "who": self.rng.choice(herd)})
        self._home()

    def _home(self):
        self.col = self.cols // 2
        self.row = self.ROWS + 1  # the start (bottom grass); 0 is the far side

    def _y(self, row):
        return self.top + row * self.cell + self.cell // 2

    def _move(self, dr, dc):
        self.row = max(0, min(self.ROWS + 1, self.row + dr))
        self.col = max(0, min(self.cols - 1, self.col + dc))
        if self.row == 0:
            self.score += 1
            self.check_goal()
            if self.phase == "PLAY":
                self._home()

    def on_tap(self, pos):
        x, y = pos[0], pos[1]
        px, py = self.col * self.cell + self.cell // 2, self._y(self.row)
        if abs(y - py) > self.cell // 2:
            self._move(-1 if y < py else 1, 0)
        else:
            self._move(0, -1 if x < px else 1)

    def on_key(self, key):
        moves = {pygame.K_UP: (-1, 0), pygame.K_w: (-1, 0), pygame.K_DOWN: (1, 0), pygame.K_s: (1, 0),
                 pygame.K_LEFT: (0, -1), pygame.K_a: (0, -1), pygame.K_RIGHT: (0, 1), pygame.K_d: (0, 1)}
        if key in moves:
            self._move(*moves[key])

    def step(self):
        span = self.W + 6 * self.cell
        for lane in self.lanes:
            lane["runners"] = [((x + lane["dir"] * lane["speed"] + 3 * self.cell) % span) - 3 * self.cell
                               for x in lane["runners"]]
        if 1 <= self.row <= self.ROWS:
            lane = self.lanes[self.row - 1]
            me = pygame.Rect(self.col * self.cell + 10, 0, self.cell - 20, 10)
            for x in lane["runners"]:
                if me.colliderect(pygame.Rect(x + 6, 0, self.cell - 12, 10)):
                    self.lose(f"A wild {self.game.assets.movesets.get(str(lane['who']), {}).get('name', 'Pokemon').title()} ran into you!")
                    self._home()

    def render(self, screen):
        for row in range(self.ROWS + 2):
            y = self.top + row * self.cell
            grass = row in (0, self.ROWS + 1) or not self.lanes[row - 1]["road"]
            color = (96, 168, 84) if grass else (148, 130, 104)
            pygame.draw.rect(screen, color, (0, y, self.W, self.cell))
            if not grass:
                for x in range(0, self.W, 60):
                    pygame.draw.line(screen, (128, 112, 88), (x, y + self.cell // 2), (x + 28, y + self.cell // 2), 3)
            pygame.draw.line(screen, (60, 80, 50), (0, y), (self.W, y), 1)
        flag = self.game.assets.fonts["label"]
        from src.ui import theme
        theme.shadow_text(screen, "GOAL", flag, self.W // 2, self.top + self.cell // 2, color=(255, 255, 255),
                          shadow=(40, 80, 40), align="center")
        for i, lane in enumerate(self.lanes):
            y = self._y(i + 1)
            for x in lane["runners"]:
                img = icon(self.game, lane["who"], self.cell + 8, flip=lane["dir"] > 0)
                screen.blit(img, img.get_rect(center=(x + self.cell // 2, y)))
        me = icon(self.game, self.partner, self.cell + 8)
        screen.blit(me, me.get_rect(center=(self.col * self.cell + self.cell // 2, self._y(self.row))))
        bob = int(4 * math.sin(pygame.time.get_ticks() / 150))
        pygame.draw.polygon(screen, (255, 230, 90), [(self.W // 2 - 14, self.top + self.cell - 8 + bob),
                                                      (self.W // 2 + 14, self.top + self.cell - 8 + bob),
                                                      (self.W // 2, self.top + self.cell - 24 + bob)])
