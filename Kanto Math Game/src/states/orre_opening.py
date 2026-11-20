"""Orre's opening (Jordan 11-20, Q2: Colosseum's, animated): Team Snagem's hideout at night; you run out with the Snag
Machine; Gonzap shouts after you; the hideout blows; you ride off across the desert on the motorbike; at dawn the
Outskirt Stand comes into view. Then the walk begins there (src/states/menus.py, StarterSelectionState).

Clicked through like every scene (feedback_animated_scenes): each beat animates while its words type out; a tap finishes
the words, the next tap moves on once the beat's motion is done. The checks fast-forward it (game.quick_scenes).
Pictures: the hideout's outside (Orre 2.1.1's map 131, assets/tiles/orre_ground/131.png + orre_top), your walking
sheet, Gonzap's battle picture, the ride's desert and motorbike (assets/tiles/orre). Music: XD's Snagem Hideout, then
the world map. Words are ours."""
import math
import os
import random

import pygame

from src.states.base import GameState
from src.ui import theme

TYPE_MS = 24
SCALE = 1.5              # the hideout picture (32 px tiles) on the screen
DOOR = (391, 236)        # the hideout's door in its picture
PATH_END = (391, 560)    # where you stop running, by the fence gap
PARK = (352, 360)        # the parked motorbike in the Outskirt Stand's picture (map 32)
BEATS = [   # (what moves, how long it moves (ms), the words)
    ("night", 1800, "Deep in the Orre desert stands the hideout of Team Snagem, a gang that steals other trainers' Pokémon."),
    ("run", 2600, "Tonight one of its own turns on it. {player} runs out into the dark with Snagem's prize: the Snag Machine."),
    ("gonzap", 900, "Gonzap: {player}! Get back here! That machine belongs to Snagem!"),
    ("blast", 2200, "BOOM! The hideout bursts into flames behind {player}."),
    ("ride", 3200, "{player} speeds off on the motorbike, with Espeon and Umbreon close at hand."),
    ("dawn", 2600, "By dawn, a lonely diner rises out of the sand: the Outskirt Stand."),
]


class OrreOpeningState(GameState):
    def __init__(self, game, then):
        super().__init__(game)
        self.then = then
        self.i = 0
        self.t0 = pygame.time.get_ticks()
        self.typed_from = self.t0
        self.done = False
        self.out_t = None
        self.sparks = []
        A = game.assets.assets_dir
        load = lambda *p: pygame.image.load(os.path.join(A, *p)).convert_alpha()
        try:
            ground = load("tiles", "orre_ground", "131.png")
            top = load("tiles", "orre_top", "131.png")
            ground.blit(top, (0, 0))
            self.hideout = pygame.transform.smoothscale(ground, (int(ground.get_width() * SCALE), int(ground.get_height() * SCALE)))
        except Exception:
            self.hideout = None
        try:
            self.gonzap = load("sprites", "trainers", "orre_snagem_gonzap.png")
        except Exception:
            self.gonzap = None
        try:
            self.desert = pygame.image.load(os.path.join(A, "tiles", "orre", "ride_desert.png")).convert()
            bike = load("tiles", "orre", "ride_bike.png")
            fw = bike.get_width() // 4
            self.bike = pygame.transform.scale(bike.subsurface((0, 0, fw, bike.get_height())), (fw * 2, bike.get_height() * 2))
        except Exception:
            self.desert = self.bike = None
        self.sheet = self._player_sheet(load)
        try:   # (the Outskirt Stand: Orre 2.1.1's map 32, its parked motorbike at PARK)
            st = load("tiles", "orre_ground", "32.png")
            st.blit(load("tiles", "orre_top", "32.png"), (0, 0))
            self.stand = st
        except Exception:
            self.stand = None
        self.boom = None
        try:
            self.boom = pygame.mixer.Sound(os.path.join(game.assets.sounds_dir, "orre_explosion.ogg")) if pygame.mixer.get_init() else None
        except Exception:
            self.boom = None
        music = getattr(game, "music", None)
        if music is not None and hasattr(music, "play_file"):
            music.play_file("orre/snagem_hideout")

    def _player_sheet(self, load):
        import json
        try:
            d = json.load(open(os.path.join(self.game.assets.assets_dir, "dungeon_sprites.json"), encoding="utf-8"))
            name = (d.get("players") or {}).get(str(getattr(self.game, "player_character", "") or "").lower()) or "orre_wes.png"
            return load("dungeon", "characters", name)
        except Exception:
            return None

    # ------------------------------------------------------------ timing
    def _speed(self):
        return 40 if getattr(self.game, "quick_scenes", False) else 1

    def _t(self):
        return (pygame.time.get_ticks() - self.t0) * self._speed()

    def _line(self):
        return BEATS[self.i][2].replace("{player}", str(getattr(self.game, "player_name", "") or "You"))

    def _typed(self):
        n = int((pygame.time.get_ticks() - self.typed_from) * self._speed() / TYPE_MS)
        return self._line()[:n]

    def _advance(self):
        if self.out_t is not None:
            return
        if len(self._typed()) < len(self._line()):
            self.typed_from = -10 ** 9   # (the words finish at once)
            return
        if self._t() < BEATS[self.i][1]:
            return   # (the beat's motion is still playing)
        if self.i + 1 >= len(BEATS):
            self.out_t = pygame.time.get_ticks()
            return
        self.i += 1
        self.t0 = self.typed_from = pygame.time.get_ticks()
        kind = BEATS[self.i][0]
        if kind == "blast" and self.boom is not None:
            self.boom.play()
        if kind == "ride":
            music = getattr(self.game, "music", None)
            if music is not None and hasattr(music, "play_file"):
                music.play_file("orre/world_map")

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN or (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z)):
                self._advance()

    def update(self):
        if self.out_t is not None and (pygame.time.get_ticks() - self.out_t) * self._speed() > 700 and not self.done:
            self.done = True
            self.then()

    # ------------------------------------------------------------ drawing
    def _frame(self, row, col):
        if self.sheet is None:
            return None
        fw, fh = self.sheet.get_width() // 4, self.sheet.get_height() // 4
        img = self.sheet.subsurface((col * fw, row * fh, fw, fh))
        return pygame.transform.scale(img, (int(fw * SCALE * 1.4), int(fh * SCALE * 1.4)))

    def _draw_hideout(self, screen, kind, t):
        w, h = screen.get_size()
        if self.hideout is None:
            screen.fill((20, 18, 30))
            return
        # where you are: at the door, running down the path, or stopped at the gap
        k = 0.0 if kind == "night" else min(1.0, t / BEATS[1][1]) if kind == "run" else 1.0
        px = DOOR[0] + (PATH_END[0] - DOOR[0]) * k
        py = DOOR[1] + (PATH_END[1] - DOOR[1]) * k
        cam_y = max(0, min(self.hideout.get_height() - h, int(py * SCALE - h * 0.55)))
        cam_x = (self.hideout.get_width() - w) // 2   # (the hideout's middle: its picture is about the screen's width)
        shake = (random.randint(-9, 9), random.randint(-7, 7)) if kind == "blast" and t < 1400 else (0, 0)
        screen.fill((0, 0, 0))
        screen.blit(self.hideout, (-cam_x + shake[0], -cam_y + shake[1]))
        if kind != "night" or t > 600:
            row, col = (0, (int(t / 110) % 4) if kind == "run" and k < 1 else 0)
            img = self._frame(row, col)
            if img is not None:
                screen.blit(img, img.get_rect(midbottom=(int(px * SCALE - cam_x + shake[0]), int(py * SCALE - cam_y + shake[1] + 18))))
                glow = pygame.Surface((40, 40), pygame.SRCALPHA)   # (the Snag Machine on your arm)
                pygame.draw.circle(glow, (170, 90, 255, 120 + int(80 * math.sin(t / 120))), (20, 20), 10)
                screen.blit(glow, glow.get_rect(center=(int(px * SCALE - cam_x + 18 + shake[0]), int(py * SCALE - cam_y - 30 + shake[1]))))
        night = pygame.Surface((w, h), pygame.SRCALPHA)
        night.fill((10, 16, 60, 150))
        screen.blit(night, (0, 0))
        if kind in ("night", "run", "gonzap"):   # (the alarm)
            a = int(60 + 50 * math.sin(t / 160))
            red = pygame.Surface((w, h), pygame.SRCALPHA)
            red.fill((200, 20, 20, a))
            screen.blit(red, (0, 0))
        if kind == "blast":
            bx, by = DOOR[0] * SCALE - cam_x, (DOOR[1] - 40) * SCALE - cam_y
            if t < 260:
                flash = pygame.Surface((w, h), pygame.SRCALPHA)
                flash.fill((255, 250, 230, int(255 * (1 - t / 260))))
                screen.blit(flash, (0, 0))
            if len(self.sparks) < 90 and t < 1400:
                for _ in range(6):
                    a = random.uniform(math.pi, 2 * math.pi)
                    v = random.uniform(2, 9)
                    self.sparks.append([bx + random.uniform(-80, 80), by + random.uniform(-20, 30), math.cos(a) * v, math.sin(a) * v,
                                        random.choice([(255, 170, 40), (255, 90, 20), (255, 230, 120), (90, 80, 80)]), 1.0])
            for s in self.sparks:
                s[0] += s[2]; s[1] += s[3]; s[3] += 0.18; s[5] -= 0.012
                if s[5] > 0:
                    r = max(2, int(14 * s[5]))
                    dot = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(dot, s[4] + (int(230 * s[5]),), (r, r), r)
                    screen.blit(dot, (int(s[0]) - r, int(s[1]) - r))
            glow = pygame.Surface((w, h), pygame.SRCALPHA)
            glow.fill((255, 120, 30, max(0, int(90 - t / 25))))
            screen.blit(glow, (0, 0))

    def _draw_ride(self, screen, kind, t):
        w, h = screen.get_size()
        if self.desert is None:
            screen.fill((214, 190, 130))
            return
        dh = self.desert.get_height()
        sc = h / dh
        tile = pygame.transform.smoothscale(self.desert, (int(self.desert.get_width() * sc), h))
        off = int(t * 0.9) % tile.get_width()
        for x in range(-off, w + tile.get_width(), tile.get_width()):
            screen.blit(tile, (x, 0))
        if self.bike is not None:
            bob = int(3 * math.sin(t / 60))
            screen.blit(self.bike, self.bike.get_rect(center=(w // 2, int(h * 0.55) + bob)))
            for j in range(5):   # (dust behind the wheels)
                r = 6 + ((t // 40 + j * 7) % 18)
                d = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(d, (230, 214, 170, max(0, 110 - r * 5)), (r, r), r)
                screen.blit(d, (w // 2 - self.bike.get_width() // 2 - j * 20 - 2 * r, int(h * 0.55) + 40 - r))
        if kind == "ride":   # night lifting
            a = max(0, 160 - int(t / 20))
        else:
            a = 0
        sky = pygame.Surface((w, h), pygame.SRCALPHA)
        sky.fill((10, 16, 60, a) if kind == "ride" else (255, 170, 90, max(0, 70 - int(t / 40))))
        screen.blit(sky, (0, 0))

    def _draw_stand(self, screen, t):
        """Dawn at the Outskirt Stand: the map in the morning light, the motorbike riding in to park by the diner."""
        w, h = screen.get_size()
        s = w / self.stand.get_width()
        pic = pygame.transform.smoothscale(self.stand, (w, int(self.stand.get_height() * s)))
        screen.fill((222, 206, 150))
        screen.blit(pic, (0, (h - 140 - pic.get_height()) // 2 + 20))
        top = (h - 140 - pic.get_height()) // 2 + 20
        k = min(1.0, t / (BEATS[-1][1] * 0.8))
        e = 1 - (1 - k) ** 2   # (slowing as it pulls in)
        if self.bike is not None:
            b = pygame.transform.smoothscale(self.bike, (int(self.bike.get_width() * s * 0.32), int(self.bike.get_height() * s * 0.32)))
            x = -b.get_width() + (PARK[0] * s + b.get_width()) * e
            screen.blit(b, b.get_rect(center=(int(x), int(top + PARK[1] * s + (0 if k >= 1 else 2 * math.sin(t / 50))))))
        warm = pygame.Surface((w, h), pygame.SRCALPHA)
        warm.fill((255, 150, 80, max(0, 90 - int(t / 30))))
        screen.blit(warm, (0, 0))

    def draw(self):
        screen = self.game.screen
        kind = BEATS[self.i][0]
        t = self._t()
        if kind == "dawn" and self.stand is not None:
            self._draw_stand(screen, t)
        elif kind in ("ride", "dawn"):
            self._draw_ride(screen, kind, t)
        else:
            self._draw_hideout(screen, kind, t)
        if kind == "gonzap" and self.gonzap is not None:
            k = min(1.0, t / 500)
            img = pygame.transform.smoothscale(self.gonzap, (self.gonzap.get_width() * 2, self.gonzap.get_height() * 2))
            screen.blit(img, img.get_rect(bottomleft=(int(-img.get_width() + (img.get_width() + 40) * k), screen.get_height() - 150)))
        if self.i == 0 and t < 700:   # (fading up out of black)
            f = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            f.fill((0, 0, 0, int(255 * (1 - t / 700))))
            screen.blit(f, (0, 0))
        self._draw_words(screen)
        if self.out_t is not None:
            k = min(1.0, (pygame.time.get_ticks() - self.out_t) * self._speed() / 700)
            f = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            f.fill((0, 0, 0, int(255 * k)))
            screen.blit(f, (0, 0))

    def _draw_words(self, screen):
        w, h = screen.get_size()
        box = pygame.Rect(40, h - 140, w - 80, 116)
        theme.draw_textbox(screen, box)
        font = self.game.assets.fonts["button"]
        words, lines, cur = self._typed().split(" "), [], ""
        for wd in words:
            test = (cur + " " + wd).strip()
            if font.size(test)[0] > box.w - 60 and cur:
                lines.append(cur)
                cur = wd
            else:
                cur = test
        lines.append(cur)
        for n, part in enumerate(lines[:3]):
            theme.shadow_text(screen, part, font, box.x + 28, box.y + 16 + n * 34)
        if len(self._typed()) >= len(self._line()) and self._t() >= BEATS[self.i][1]:
            pygame.draw.polygon(screen, theme.TEXT_ARROW, [(box.right - 40, box.bottom - 28), (box.right - 24, box.bottom - 28),
                                                           (box.right - 32, box.bottom - 18)])
