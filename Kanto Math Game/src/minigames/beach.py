"""Pikachu's Beach (Pokemon Yellow's Summer Beach House on Route 19; Jordan 11-16): surf Pikachu to the shore.

As in Yellow: each wave throws Pikachu into the air; flip left or right while it's up and land upright for "Radness"
(one flip 50, two the same way 150, two mixed 180, three the same way 350, three mixed 500). A flip that isn't
finished when Pikachu lands is a wipeout: no points and the ride slows. The HP counter runs down all the time (6000,
about a hundred seconds); reach the shore before it runs out. Score = Radness + the HP left. Good flips speed the
ride up, as in Yellow.

Our addition (math): a quick sum comes up with every wave. Answer it before Pikachu lands and that landing's points
are doubled. Wrong or no answer costs nothing.

Played from the Surfin' Dude's door (common._run_story_event, event "minigame": "pikachu_beach"), with the rowdy
Pikachu in the party; the best score is kept in story_flags["pikachu_beach_best"]."""
import math
import os

import pygame

from src.config import FPS
from src.minigames.base import Minigame
from src.ui import theme

HP_START = 6000
HP_PER_FRAME = 6000 / (100 * FPS)      # (100 seconds, as Yellow's 6000 frames at 60 a second)
SHORE = 100.0                          # (how far: percent of the way)
BASE_SPEED = 1.25 / FPS                # (percent a frame: about 80 seconds with no flips)
BOOST, BOOST_MAX = 0.10 / FPS, 1.4 / FPS
WAVE_EVERY = int(2.3 * FPS)
AIR = int(1.45 * FPS)                  # (frames up in the air)
FLIP = int(0.4 * FPS)                  # (frames for one full turn)
POINTS = {1: 50, (2, True): 150, (2, False): 180, (3, True): 350, (3, False): 500}
BEST_FLAG = "pikachu_beach_best"


def radness(flips):
    """Yellow's points for the flips landed in one jump ("L"/"R" each)."""
    n = len(flips)
    if n == 0:
        return 0
    if n == 1:
        return POINTS[1]
    same = len(set(flips)) == 1
    return POINTS[(min(n, 3), same)]


class PikachuBeach(Minigame):
    key = "beach"
    title = "Pikachu's Beach"
    how = ("Waves throw Pikachu into the air. Flip left or right while it's up, and land the right way up for Radness! "
           "Answer the sum before Pikachu lands to double the points. Reach the shore before the HP runs out.")
    controls = (("Tap left / right side", "Flip that way"), ("Tap an answer", "Answer the sum"),
                ("Left / Right", "Flip"), ("1 / 2 / 3", "Answer"))
    accent = (60, 150, 230)
    in_pool = False   # (only at the Summer Beach House)
    win_line = "Pikachu rode the waves all the way to the shore!"

    def goal_text(self):
        return "Surf to the shore"

    def progress(self):
        return int(self.dist), int(SHORE)

    # ---- a round
    def setup(self):
        self.dist = 0.0
        self.hp = float(HP_START)
        self.speed = BASE_SPEED
        self.rad = 0
        self.air = 0             # frames left in the air (0: on the water)
        self.angle = 0.0         # Pikachu's turn, degrees
        self.turning = 0         # frames left of the flip under way
        self.turn_dir = 0
        self.flips = []
        self.next_wave = int(1.2 * FPS)
        self.slow = 0            # frames of a wipeout's slowdown
        self.question = None     # (text, answer, options, answered: None/True/False)
        self.popups = []         # [x, y, text, frames]
        self.scroll = 0.0

    # ---- input
    def _answer_rects(self):
        n = len(self.question[2]) if self.question else 0
        w, gap = 200, 24
        x0 = self.W // 2 - (n * w + (n - 1) * gap) // 2
        y = self.area.top + 86
        return [pygame.Rect(x0 + i * (w + gap), y, w, 70) for i in range(n)]

    def _answer(self, i):
        q = self.question
        if not q or q[3] is not None or i >= len(q[2]):
            return
        q[3] = str(q[2][i]) == str(q[1])

    def _flip(self, way):
        if self.air <= 0 or self.turning:
            return
        self.turning, self.turn_dir = FLIP, (-1 if way == "L" else 1)
        self.flips.append(way)

    def on_tap(self, pos):
        for i, r in enumerate(self._answer_rects()):
            if r.collidepoint(pos):
                return self._answer(i)
        self._flip("L" if pos[0] < self.W // 2 else "R")

    def on_key(self, key):
        if key in (pygame.K_LEFT, pygame.K_a):
            self._flip("L")
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self._flip("R")
        elif key in (pygame.K_1, pygame.K_KP1):
            self._answer(0)
        elif key in (pygame.K_2, pygame.K_KP2):
            self._answer(1)
        elif key in (pygame.K_3, pygame.K_KP3):
            self._answer(2)

    # ---- play
    def _ask(self):
        story = self.game.story_manager
        try:
            text, ans, opts = self.game.math.generate(story.get_math_level(), num_options=3)
        except Exception:   # (no math engine: a plain sum)
            a, b = self.rng.randint(1, 9), self.rng.randint(1, 9)
            text, ans = f"{a} + {b} = ?", a + b
            opts = sorted({ans, ans + 1, max(0, ans - 2)})
        self.question = [text, ans, list(opts), None]

    def _land(self):
        clean = self.turning == 0
        if clean and self.flips:
            pts = radness(self.flips)
            doubled = bool(self.question and self.question[3])
            pts *= 2 if doubled else 1
            self.rad += pts
            self.speed = min(BOOST_MAX, self.speed + BOOST * len(self.flips))
            self.popups.append([self._px(), self._py() - 120, f"+{pts}" + (" x2!" if doubled else ""), int(1.2 * FPS)])
        elif not clean:   # (a flip not finished: into the water)
            self.slow = int(2.0 * FPS)
            self.speed = BASE_SPEED
            self.popups.append([self._px(), self._py() - 120, "Wipeout!", int(1.2 * FPS)])
        self.flips, self.turning, self.angle = [], 0, 0.0
        self.question = None

    def step(self):
        self.hp -= HP_PER_FRAME
        if self.hp <= 0:
            self.hp = 0
            return self.lose("Pikachu ran out of HP before reaching the shore!")
        go = self.speed * (0.4 if self.slow else 1.0)
        self.slow = max(0, self.slow - 1)
        self.dist += go
        self.scroll += 6 + go * FPS * 3
        if self.air > 0:
            self.air -= 1
            if self.turning:
                self.turning -= 1
                self.angle += self.turn_dir * 360.0 / FLIP
                if self.turning == 0:
                    self.angle = 0.0
            if self.air == 0:
                self._land()
        else:
            self.next_wave -= 1
            if self.next_wave <= 0 and not self.slow:
                self.air = AIR
                self.next_wave = WAVE_EVERY
                self._ask()
        for p in self.popups:
            p[1] -= 2
            p[3] -= 1
        self.popups = [p for p in self.popups if p[3] > 0]
        if self.dist >= SHORE:
            self.dist = SHORE
            self.final = self.rad + int(self.hp)
            self.message = f"Radness {self.rad} + HP {int(self.hp)} = {self.final} points!"
            best = int(self.game.story_manager.story_flags.get(BEST_FLAG, 0) or 0)
            if self.final > best:
                self.game.story_manager.story_flags[BEST_FLAG] = self.final
                self.message += " A new best!"
            else:
                self.message += f" (Best: {best})"
            self.win()

    def win(self):
        msg = self.message
        super().win()
        self.message = msg or self.win_line

    # ---- drawing
    def _px(self):
        return int(self.W * 0.32)

    def _sea_y(self):
        return self.area.top + int(self.area.h * 0.62)

    def _py(self):
        if self.air > 0:
            t = 1 - self.air / AIR
            return self._sea_y() - 50 - int(math.sin(math.pi * t) * self.area.h * 0.24)
        return self._sea_y() - 50 + int(math.sin(self.frames / 4) * 4)

    def _pikachu(self):
        key = ("beach_pika",)
        img = self.__class__.__dict__.get("_img_cache", {}).get(key)
        if img is None:
            sheet = pygame.image.load(os.path.join(self.game.assets.assets_dir, "dungeon", "followers", "25.png")).convert_alpha()
            fw, fh = sheet.get_width() // 4, sheet.get_height() // 4
            frame = sheet.subsurface((0, 2 * fh, fw, fh)).copy()   # (facing right)
            frame = pygame.transform.scale(frame, (fw * 3, fh * 3))
            board = pygame.Surface((fw * 3 + 40, fh * 3 + 30), pygame.SRCALPHA)
            br = pygame.Rect(0, 0, fw * 3 + 30, 26)
            br.midbottom = (board.get_width() // 2, board.get_height() - 2)
            pygame.draw.ellipse(board, (224, 64, 52), br)
            pygame.draw.ellipse(board, (255, 214, 80), br.inflate(-24, -10))
            pygame.draw.ellipse(board, (90, 30, 30), br, 2)
            board.blit(frame, frame.get_rect(midbottom=(board.get_width() // 2, br.centery + 4)))
            img = board
            PikachuBeach._img_cache = {key: img}
        return img

    def render(self, screen):
        a = self.area
        sea = self._sea_y()
        # sky
        for i in range(0, sea - a.top, 8):
            k = i / max(1, sea - a.top)
            col = (int(120 + 100 * k), int(190 + 50 * k), 255)
            pygame.draw.rect(screen, col, (0, a.top + i, self.W, 8))
        pygame.draw.circle(screen, (255, 236, 140), (self.W - 160, a.top + 90), 46)
        # the shore coming nearer (a strip of sand at the right, near the end)
        if self.dist > SHORE - 12:
            sx = int(self.W - (self.dist - (SHORE - 12)) / 12 * self.W * 0.5)
            pygame.draw.rect(screen, (240, 216, 150), (sx, sea - 30, self.W - sx, a.bottom - sea + 30))
        # the sea and its rolling swell
        pygame.draw.rect(screen, (40, 120, 210), (0, sea, self.W, a.bottom - sea))
        pts = [(x, sea + int(math.sin((x + self.scroll) / 60.0) * 10)) for x in range(0, self.W + 20, 20)]
        pygame.draw.polygon(screen, (40, 120, 210), [(0, a.bottom)] + pts + [(self.W, a.bottom)])
        pygame.draw.lines(screen, (220, 240, 255), False, pts, 4)
        for j in range(3):
            y = sea + 40 + j * 46
            for x in range(-120, self.W + 120, 160):
                xx = int((x - self.scroll * (0.6 + j * 0.2)) % (self.W + 240)) - 120
                pygame.draw.arc(screen, (120, 180, 240), (xx, y, 90, 24), 0.3, 2.8, 3)
        # the wave coming in
        if self.air <= 0:
            k = max(0.0, self.next_wave / WAVE_EVERY)
            wx = self._px() + int(k * (self.W - self._px()))
            crest = []   # (a swell leaning the way it rolls, steep in front)
            for x in range(wx - 120, wx + 241, 8):
                d = (x - wx) / (38.0 if x < wx else 95.0)
                crest.append((x, sea - int(84 * math.exp(-d * d))))
            pygame.draw.polygon(screen, (52, 132, 222), [(wx - 120, sea + 4)] + crest + [(wx + 240, sea + 4)])
            pygame.draw.polygon(screen, (34, 104, 196), [(wx - 30, sea + 4)] + [p for p in crest if p[0] >= wx - 30 and p[0] <= wx + 60] + [(wx + 60, sea + 4)])
            top = [p for p in crest if p[1] < sea - 30]
            if len(top) > 1:
                pygame.draw.lines(screen, (245, 252, 255), False, top, 6)
                for i, (fx, fy) in enumerate(top[:5]):
                    pygame.draw.circle(screen, (245, 252, 255), (fx - 6, fy + 4 + i * 3), 6 - i)
        # Pikachu
        img = self._pikachu()
        if self.angle:
            img = pygame.transform.rotate(img, -self.angle)
        screen.blit(img, img.get_rect(center=(self._px(), self._py())))
        if self.slow and self.air <= 0:
            pygame.draw.circle(screen, (230, 245, 255), (self._px(), sea), 30 + (self.slow % 6), 3)
        # the sum
        f = self.fonts
        if self.question:
            q = self.question
            box = pygame.Rect(0, 0, 560, 64)
            box.midtop = (self.W // 2, a.top + 14)
            theme.draw_textbox(screen, box)
            theme.shadow_text(screen, q[0], f["button"], box.centerx, box.centery - f["button"].get_height() // 2, align="center")
            for i, r in enumerate(self._answer_rects()):
                col = theme.POKEMON
                if q[3] is not None:
                    col = (70, 170, 90) if str(q[2][i]) == str(q[1]) else theme.BACK
                theme.command_button(screen, r, f"{i + 1}:  {q[2][i]}", f["label"], col)
            if q[3] is not None:
                theme.shadow_text(screen, "x2 if you land it!" if q[3] else "Not this time!", f["label"],
                                  self.W // 2, a.top + 168, align="center",
                                  color=(255, 236, 120) if q[3] else (255, 200, 200))
        # HP and Radness
        theme.shadow_text(screen, f"HP {int(self.hp)}", f["button"], self.W - 30, a.bottom - 60, align="right",
                          color=(255, 255, 255))
        theme.shadow_text(screen, f"RADNESS {self.rad}", f["button"], 30, a.bottom - 60, color=(255, 255, 255))
        for x, y, text, _t in self.popups:
            theme.shadow_text(screen, text, f["button"], x, y, align="center", color=(255, 240, 120))
