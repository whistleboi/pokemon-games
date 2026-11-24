"""Two Island's Joyful Game Corner (11-23, Kanto K4; Jordan: "Single-player versions" of FireRed's two link games, with sums
like Pikachu's Beach). Played from the attendant (src/world/joyful_games.py).

Pokemon Jump (FireRed's: Pokemon jump the vine together; ours, one Pokemon): the vine swings round once a beat. Tap as it
comes under your Pokemon: a jump. Close to the moment the vine is lowest is a PERFECT (more points); too early or too
late and it trips you. Every ten jumps the vine swings a little faster (FireRed's). Three trips and the game is over.
Ours (math): every fifth swing a sum comes up; answer it before the jump and that jump's points are doubled.

Dodrio Berry Picking (FireRed's: each player one of Dodrio's three heads; ours, all three): Berries fall into five
columns; Dodrio stands under three of them at once (its heads), slide it left or right. Each Berry kind is worth more
(FireRed: 1 to 3 points by kind); a golden Berry carries a sum - answer it and it's worth double. Ten Berries dropped
and the game is over. The falls speed up as you go (FireRed's).

Prizes (FireRed gives Berries by score): see PRIZES; the best score of each is kept (story flag)."""
import math

import pygame

from src.config import FPS
from src.minigames.base import Minigame, icon, item

JUMP_BEST, BERRY_BEST = "joyful_jump_best", "joyful_berry_best"
# (score at least, prize) - FireRed's prizes are Berries; ours from the same idea
PRIZES = {"jump": [(1500, "LUM_BERRY"), (800, "SITRUS_BERRY"), (300, "ORAN_BERRY"), (1, "PECHA_BERRY")],
          "berry": [(300, "LUM_BERRY"), (150, "SITRUS_BERRY"), (60, "ORAN_BERRY"), (1, "CHERI_BERRY")]}


def prize(kind, score):
    return next((p for s, p in PRIZES[kind] if score >= s), None)


class _Sums:
    """A sum on screen with three answers (the game's math, as Pikachu's Beach)."""

    def ask(self):
        story = self.game.story_manager
        try:
            text, ans, opts = self.game.math.generate(story.get_math_level(), num_options=3)
        except Exception:
            a, b = self.rng.randint(1, 9), self.rng.randint(1, 9)
            text, ans = f"{a} + {b} = ?", a + b
            opts = sorted({ans, ans + 1, max(0, ans - 2)})
        self.question = [text, ans, list(opts), None]

    def answer_rects(self):
        n = len(self.question[2]) if self.question else 0
        w, gap = 180, 22
        x0 = self.W // 2 - (n * w + (n - 1) * gap) // 2
        return [pygame.Rect(x0 + i * (w + gap), self.area.top + 70, w, 64) for i in range(n)]

    def answer(self, i):
        q = self.question
        if not q or q[3] is not None or i >= len(q[2]):
            return
        q[3] = str(q[2][i]) == str(q[1])

    def tap_answer(self, pos):
        for i, r in enumerate(self.answer_rects()):
            if r.collidepoint(pos):
                self.answer(i)
                return True
        return False

    def key_answer(self, key):
        for i, k in enumerate((pygame.K_1, pygame.K_2, pygame.K_3)):
            if key in (k, getattr(pygame, f"K_KP{i + 1}")):
                self.answer(i)
                return True
        return False

    def draw_sum(self, screen):
        q = self.question
        if not q:
            return
        f = self.fonts.get("medium") or self.fonts.get("small")
        t = f.render(str(q[0]), True, (255, 255, 255))
        screen.blit(t, t.get_rect(midtop=(self.W // 2, self.area.top + 22)))
        for i, r in enumerate(self.answer_rects()):
            col = (70, 90, 150)
            if q[3] is not None and str(q[2][i]) == str(q[1]):
                col = (60, 160, 80)
            pygame.draw.rect(screen, col, r, border_radius=12)
            pygame.draw.rect(screen, (230, 230, 240), r, 3, border_radius=12)
            n = f.render(f"{i + 1}) {q[2][i]}", True, (255, 255, 255))
            screen.blit(n, n.get_rect(center=r.center))


class PokemonJump(_Sums, Minigame):
    key = "pokejump"
    title = "Pokemon Jump"
    how = ("The vine swings round. Tap just as it passes under your Pokemon to jump - right at the bottom is a PERFECT! "
           "Every fifth swing a sum comes up: answer it before you jump to double that jump. Three trips and it's over.")
    controls = (("Tap", "Jump"), ("Tap an answer", "Answer the sum"), ("Space / Up", "Jump"), ("1 / 2 / 3", "Answer"))
    accent = (90, 170, 90)
    in_pool = False
    win_line = "What a run of jumps!"
    HEARTS = 3

    def goal_text(self):
        return f"Jumps: {self.jumps}"

    def progress(self):
        return self.jumps, max(self.jumps, 1)

    def setup(self):
        self.jumps = 0
        self.hearts = self.HEARTS
        self.beat = int(1.6 * FPS)       # frames a swing takes (FireRed: faster every ten jumps)
        self.t = 0                       # frames into this swing; the vine is lowest at the end of it
        self.air = 0                     # frames of this jump left
        self.jumped = False              # jumped this swing
        self.question = None
        self.popups = []
        self.swings = 0

    def check_goal(self):
        pass

    def _jump(self):
        if self.air > 0 or self.jumped:
            return
        left = self.beat - self.t        # frames till the vine is lowest
        self.jumped = True
        self.air = int(0.45 * FPS)
        self.window = left

    def on_tap(self, pos):
        if not self.tap_answer(pos):
            self._jump()

    def on_key(self, key):
        if not self.key_answer(key) and key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
            self._jump()

    def step(self):
        self.t += 1
        if self.air > 0:
            self.air -= 1
        if self.t >= self.beat:   # (the vine's at the bottom: under your Pokemon now)
            ok = self.jumped and getattr(self, "window", 99) <= int(0.30 * FPS)
            if ok:
                perfect = self.window <= int(0.08 * FPS)
                pts = 20 if perfect else 10
                doubled = bool(self.question and self.question[3])
                pts *= 2 if doubled else 1
                self.jumps += 1
                self.score += pts
                self.popups.append([("PERFECT! " if perfect else "") + f"+{pts}" + (" x2!" if doubled else ""), int(1.0 * FPS)])
                if self.jumps % 10 == 0:
                    self.beat = max(int(0.7 * FPS), int(self.beat * 0.9))
            else:
                self.hearts -= 1
                self.popups.append(["Tripped!", int(1.0 * FPS)])
                if self.hearts <= 0:
                    self.score_end()
                    return
            self.t, self.jumped, self.window = 0, False, 99
            self.swings += 1
            self.question = None
            if self.swings % 5 == 4:
                self.ask()
        self.popups = [[t, n - 1] for t, n in self.popups if n > 1]

    def score_end(self):
        best = int(self.game.story_manager.story_flags.get(JUMP_BEST, 0) or 0)
        if self.score > best:
            self.game.story_manager.story_flags[JUMP_BEST] = self.score
        self.win()

    def render(self, screen):
        ground = self.area.bottom - 120
        cx = self.W // 2
        # the vine: a swinging arc, lowest at the end of the beat
        ph = self.t / max(1, self.beat)
        depth = math.cos(ph * math.pi * 2) * -1   # (1 at the bottom, -1 at the top)
        y = ground + 10 - (1 - depth) * 150
        pygame.draw.arc(screen, (60, 150, 60), pygame.Rect(cx - 260, y - 60, 520, 120), math.pi, 2 * math.pi, 8)
        lift = math.sin(min(1.0, (0.45 * FPS - self.air) / (0.45 * FPS)) * math.pi) * 70 if self.air > 0 else 0
        mon = icon(self.game, self.partner, 110)
        screen.blit(mon, mon.get_rect(midbottom=(cx, ground - lift)))
        for i in range(self.HEARTS):
            ball = item(self.game, "poke-ball", 40)
            if i >= self.hearts:
                ball = ball.copy(); ball.set_alpha(60)
            screen.blit(ball, (24 + i * 48, self.area.top + 14))
        f = self.fonts.get("medium") or self.fonts.get("small")
        s = f.render(f"Score {self.score}   Jumps {self.jumps}", True, (255, 255, 255))
        screen.blit(s, (self.W - s.get_width() - 24, self.area.top + 16))
        for k, (t, n) in enumerate(self.popups[-2:]):
            p = f.render(t, True, (255, 230, 90))
            screen.blit(p, p.get_rect(center=(cx, ground - 190 - k * 40)))
        self.draw_sum(screen)


BERRIES = [("CHERI_BERRY", 1), ("ORAN_BERRY", 1), ("PECHA_BERRY", 2), ("SITRUS_BERRY", 3)]


class DodrioBerryPicking(_Sums, Minigame):
    key = "dodrio"
    title = "Dodrio Berry Picking"
    how = ("Berries fall into five columns. Slide Dodrio left and right: its three heads catch the Berries above them. "
           "A golden Berry brings a sum - answer it and the Berry counts double. Ten Berries dropped and it's over.")
    controls = (("Tap left / right side", "Slide Dodrio"), ("Tap an answer", "Answer the sum"), ("Left / Right", "Slide"),
                ("1 / 2 / 3", "Answer"))
    accent = (200, 120, 60)
    in_pool = False
    win_line = "Dodrio's had a feast!"
    MISSES = 10
    COLS = 5

    def goal_text(self):
        return f"Berries: {self.caught}"

    def progress(self):
        return self.caught, max(self.caught, 1)

    def setup(self):
        self.pos = 1               # (Dodrio's heads over columns pos .. pos+2)
        self.caught = 0
        self.missed = 0
        self.falling = []          # [col, y, kind, points, golden]
        self.until = int(0.8 * FPS)
        self.speed = 160 / FPS
        self.question = None
        self.popups = []

    def check_goal(self):
        pass

    def _col_x(self, c):
        w = min(160, (self.W - 160) // self.COLS)
        return self.W // 2 + (c - (self.COLS - 1) / 2) * w

    def on_tap(self, pos):
        if self.tap_answer(pos):
            return
        self.pos = max(0, min(self.COLS - 3, self.pos + (-1 if pos[0] < self.W // 2 else 1)))

    def on_key(self, key):
        if self.key_answer(key):
            return
        if key in (pygame.K_LEFT, pygame.K_a):
            self.pos = max(0, self.pos - 1)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.pos = min(self.COLS - 3, self.pos + 1)

    def step(self):
        self.until -= 1
        if self.until <= 0:
            golden = self.rng.random() < 0.12 and not any(f[4] for f in self.falling)
            kind, pts = ("GOLD", 5) if golden else self.rng.choice(BERRIES)
            self.falling.append([self.rng.randrange(self.COLS), float(self.area.top + 150), kind, pts, golden])
            self.until = max(int(0.35 * FPS), int((0.9 - self.caught * 0.01) * FPS))
            if golden:
                self.ask()
        catch_y = self.area.bottom - 170
        keep = []
        for f in self.falling:
            f[1] += self.speed * (1 + self.caught / 60)
            if f[1] >= catch_y:
                if self.pos <= f[0] <= self.pos + 2:
                    pts = f[3]
                    if f[4]:
                        pts *= 2 if (self.question and self.question[3]) else 1
                        self.question = None
                    self.caught += 1
                    self.score += pts
                    self.popups.append([f"+{pts}", self._col_x(f[0]), int(0.8 * FPS)])
                else:
                    self.missed += 1
                    if f[4]:
                        self.question = None
                    if self.missed >= self.MISSES:
                        self.score_end()
                        return
            else:
                keep.append(f)
        self.falling = keep
        self.popups = [[t, x, n - 1] for t, x, n in self.popups if n > 1]

    def score_end(self):
        best = int(self.game.story_manager.story_flags.get(BERRY_BEST, 0) or 0)
        if self.score > best:
            self.game.story_manager.story_flags[BERRY_BEST] = self.score
        self.win()

    def render(self, screen):
        catch_y = self.area.bottom - 170
        for c in range(self.COLS):
            x = int(self._col_x(c))
            pygame.draw.line(screen, (90, 70, 50), (x, self.area.top + 150), (x, catch_y), 2)
        for col, y, kind, _p, golden in self.falling:
            if golden:
                pygame.draw.circle(screen, (250, 210, 60), (int(self._col_x(col)), int(y)), 22)
                pygame.draw.circle(screen, (255, 250, 200), (int(self._col_x(col)) - 6, int(y) - 6), 6)
            else:
                img = item(self.game, kind.lower().replace("_", "-"), 48)
                screen.blit(img, img.get_rect(center=(self._col_x(col), y)))
        dodrio = icon(self.game, 85, 150)
        screen.blit(dodrio, dodrio.get_rect(midtop=(self._col_x(self.pos + 1), catch_y - 20)))
        for c in range(self.pos, self.pos + 3):   # (its three heads)
            pygame.draw.circle(screen, (255, 255, 255), (int(self._col_x(c)), catch_y), 10, 3)
        f = self.fonts.get("medium") or self.fonts.get("small")
        s = f.render(f"Score {self.score}   Dropped {self.missed}/{self.MISSES}", True, (255, 255, 255))
        screen.blit(s, (24, self.area.top + 16))
        for t, x, n in self.popups:
            p = f.render(t, True, (255, 230, 90))
            screen.blit(p, p.get_rect(center=(x, catch_y - 60)))
        self.draw_sum(screen)
