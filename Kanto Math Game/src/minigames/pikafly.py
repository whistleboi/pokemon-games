"""Pikafly (Jordan, 11-08): the balloon-riding minigame from Pokemon Orre, rebuilt here as a Gym challenge. Hold to rise, let go
to fall, grab the Rare Candies, keep clear of the birds, and get through a legendary bird's attack halfway."""
import os

import pygame

from src.config import FPS
from src.minigames.base import Minigame

FOLDER = ("minigames", "pikafly")
SCALE = 2
RISE_ACCEL, RISE_MAX = 1400 / FPS / FPS, 520 / FPS
GRAVITY, FALL_MAX = 1100 / FPS / FPS, 560 / FPS
SKY = ("background", "see2mountain", "mountain_bg", "mountain_bg", "mountain_bg", "mountain2see", "background", "trees", "trees", "trees")
BIRDS = {"pidgeotto": (300, "A Pidgeotto knocked Pikachu off course!"), "fearow": (400, "A Fearow swooped in!"),
         "pelipper": (260, "A Pelipper bumped into Pikachu!"), "skarmory": (460, "A Skarmory cut the balloons!")}
LEVEL_BIRDS = (("pidgeotto",), ("pidgeotto", "fearow"), ("pidgeotto", "fearow", "pelipper"), ("pidgeotto", "fearow", "pelipper", "skarmory"))
BOSSES = (("zapdos", "electroball"), ("articuno", "iceshard"), ("moltres", "fireball"))
BOSS_SECONDS = 9
SHOT_EVERY = 2 * FPS
SHOT_SPEED = 420 / FPS
_images = {}


def _load(game, name):
    return pygame.image.load(os.path.join(game.assets.assets_dir, *FOLDER, f"{name}.png")).convert_alpha()


def frames(game, name):
    """A 4-frame strip, doubled."""
    if name not in _images:
        strip = _load(game, name)
        size = strip.get_height()
        _images[name] = [pygame.transform.scale(strip.subsurface((i * size, 0, size, size)), (size * SCALE, size * SCALE)) for i in range(4)]
    return _images[name]


def sky_image(game, name, height):
    key = ("sky", name, height)
    if key not in _images:
        raw = _load(game, name).convert()
        _images[key] = pygame.transform.scale(raw, (raw.get_width() * height // raw.get_height(), height))
    return _images[key]


class PikaFly(Minigame):
    key = "flight"
    title = "Pikafly"
    how = "Pikachu's balloons rise while you hold. Grab the Rare Candies and keep clear of everything else!"
    controls = (("Hold", "Rise"), ("Let go", "Fall"), ("Space / Up / W", "Hold to rise"))
    accent = (232, 182, 40)

    def target(self):
        return 8 + self.level

    def goal_text(self):
        return f"Grab {self.target()} Rare Candies"

    def setup(self):
        self.bg = sky_image(self.game, "background", self.H)
        self.x, self.y, self.vy = 190, float(self.area.centery), 0.0
        self.holding = False
        self.scroll = 0.0
        self.speed = (300 + self.level * 18) / FPS
        self.birds, self.candies, self.shots = [], [], []
        self.next_bird, self.next_candy = FPS, FPS // 2
        self.boss = None
        self.boss_done = False

    def on_tap(self, pos):
        self.holding = True

    def on_release(self, pos):
        self.holding = False

    def _held(self):
        keys = pygame.key.get_pressed()
        return self.holding or keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]

    def _me(self):
        r = pygame.Rect(0, 0, 66, 84)
        r.center = (self.x, self.y)
        return r

    def _bird_kinds(self):
        return LEVEL_BIRDS[min(len(LEVEL_BIRDS) - 1, self.level // 2)]

    def _free_y(self):
        return self.rng.randint(self.area.top + 70, self.area.bottom - 70)

    def _spawn(self):
        self.next_bird -= 1
        if self.next_bird <= 0 and self.boss is None:
            for _ in range(1 + (self.level >= 4)):
                kind = self.rng.choice(self._bird_kinds())
                self.birds.append([float(self.W + 70), self._free_y(), kind])
            self.next_bird = max(int(FPS * 0.9), int(FPS * 1.7) - self.level * 2)
        self.next_candy -= 1
        if self.next_candy <= 0:
            self.candies.append([float(self.W + 40), self._free_y()])
            self.next_candy = int(FPS * 1.5)

    def _boss_turn(self):
        if self.boss is None and not self.boss_done and self.score >= self.target() // 2:
            name, shot = self.rng.choice(BOSSES)
            self.boss = {"name": name, "shot": shot, "x": float(self.W + 100), "y": float(self.area.top + 130), "t": 0}
            self.birds = []
        b = self.boss
        if b is None:
            return
        b["t"] += 1
        if b["t"] > BOSS_SECONDS * FPS:  # (its attack is over: off it goes)
            b["x"] += 500 / FPS
            if b["x"] > self.W + 120:
                self.boss, self.boss_done = None, True
            return
        b["x"] = max(self.W - 220.0, b["x"] - 500 / FPS)
        if b["t"] % SHOT_EVERY == 0:
            dx, dy = self.x - b["x"], self.y - b["y"]
            d = max(1.0, (dx * dx + dy * dy) ** 0.5)
            self.shots.append([b["x"], b["y"], dx / d * SHOT_SPEED, dy / d * SHOT_SPEED, b["shot"]])

    def step(self):
        self.vy = max(self.vy - RISE_ACCEL, -RISE_MAX) if self._held() else min(self.vy + GRAVITY, FALL_MAX)
        self.y = min(max(self.y + self.vy, self.area.top + 56.0), self.area.bottom - 56.0)
        if self.y in (self.area.top + 56.0, self.area.bottom - 56.0):
            self.vy = 0.0
        self.scroll += self.speed
        self._spawn()
        self._boss_turn()
        me = self._me()
        for b in self.birds:
            b[0] -= BIRDS[b[2]][0] / FPS + self.speed * 0.4
            if me.colliderect(pygame.Rect(int(b[0]) - 40, b[1] - 32, 80, 64)):
                return self.lose(BIRDS[b[2]][1])
        self.birds = [b for b in self.birds if b[0] > -100]
        for s in self.shots:
            s[0] += s[2]
            s[1] += s[3]
            if me.colliderect(pygame.Rect(int(s[0]) - 22, int(s[1]) - 22, 44, 44)):
                return self.lose("Hit by the legendary bird's attack!")
        self.shots = [s for s in self.shots if -80 < s[0] < self.W + 80 and self.area.top - 40 < s[1] < self.area.bottom + 40]
        kept = []
        for c in self.candies:
            c[0] -= self.speed
            if me.inflate(16, 16).colliderect(pygame.Rect(int(c[0]) - 24, c[1] - 24, 48, 48)):
                self.score += 1
                self.check_goal()
            elif c[0] > -50:
                kept.append(c)
        self.candies = kept

    def _draw_sky(self, screen):
        names, x = list(SKY), -(self.scroll % sum(sky_image(self.game, n, self.H).get_width() for n in SKY))
        while x < self.W:
            for n in names:
                img = sky_image(self.game, n, self.H)
                if x < self.W and x + img.get_width() > 0:
                    screen.blit(img, (int(x), 0))
                x += img.get_width()

    def render(self, screen):
        self._draw_sky(screen)
        beat = (self.frames // 3) % 4
        candy = _images.get("candy")
        if candy is None:
            candy = _images["candy"] = pygame.transform.scale(_load(self.game, "RARECANDY"), (72, 72))
        for x, y in self.candies:
            screen.blit(candy, candy.get_rect(center=(int(x), y)))
        for x, y, kind in self.birds:
            img = frames(self.game, kind)[beat]
            screen.blit(img, img.get_rect(center=(int(x), y)))
        if self.boss:
            img = frames(self.game, self.boss["name"])[beat]
            screen.blit(img, img.get_rect(center=(int(self.boss["x"]), int(self.boss["y"]))))
        for s in self.shots:
            img = frames(self.game, s[4])[beat]
            screen.blit(img, img.get_rect(center=(int(s[0]), int(s[1]))))
        img = frames(self.game, "pikachu")[beat]
        screen.blit(img, img.get_rect(center=(int(self.x), int(self.y))))
