"""Kanto's own Gym challenges, drawn like the rest (Jordan, 11-01): the old menu puzzles of
src/states/gym_puzzles.py (same questions, make_step) made into games to see and touch. Each is that
Gym's challenge (GYM_GAMES in src/minigames/__init__.py), not in the random pool.

- SurgeCans (Vermilion): tap the trash can whose sum makes the number. Two switches in a row;
  a wrong can on the second resets the locks.
- KogaWalls (Fuchsia): three paths; take the one with the right number of footprints, three times.
- SabrinaWarps (Saffron): step on the warp tile whose answer is the number; a wrong one warps you
  back to the first room.
- BlaineQuiz (Cinnabar): the quiz machine. Five right answers; three wrong and it's over.
"""
import math

import pygame

from src.minigames.base import Minigame, icon
from src.states.gym_puzzles import make_step
from src.ui import theme
from src.utils import Utils
from src.config import FPS

NUMBER_KEYS = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3, pygame.K_5: 4, pygame.K_6: 5,
               pygame.K_KP1: 0, pygame.K_KP2: 1, pygame.K_KP3: 2, pygame.K_KP4: 3, pygame.K_KP5: 4, pygame.K_KP6: 5}


class _Choice(Minigame):
    """A math step with some choices to tap (or 1-6). Right: on to the next; wrong: say so."""
    in_pool = False

    def setup(self):
        self.wait = 0
        self.after = None
        self.picked = None
        self.note = ""
        self._next_step()

    def _next_step(self):
        self.prompt, _pic, self.options = make_step(self.kind, self.score, self.rng)
        self.picked = None
        self.note = ""

    def _choose(self, i):
        if self.wait or not (0 <= i < len(self.options)):
            return
        self.picked = i
        if self.options[i][1]:
            self.right(i)
        else:
            self.wrong(i)

    def right(self, i):
        self.score += 1
        self.note = self.good_line()
        self._later(self._advance)

    def wrong(self, i):
        self.note = self.bad_line()
        self._later(self._next_step)

    def _advance(self):
        self.check_goal()
        if self.phase == "PLAY":
            self._next_step()

    def _later(self, fn, seconds=0.9):
        self.wait, self.after = int(FPS * seconds), fn

    def step(self):
        if self.wait:
            self.wait -= 1
            if self.wait == 0 and self.after:
                fn, self.after = self.after, None
                fn()

    def on_tap(self, pos):
        for i, rect in enumerate(self.choice_rects()):
            if rect.collidepoint(pos):
                self._choose(i)
                return

    def on_key(self, key):
        if key in NUMBER_KEYS:
            self._choose(NUMBER_KEYS[key])

    def _banner(self, screen, text, y=None):
        f = self.fonts["dialog"]
        from src.ui.dialogue import wrap_text
        rows = wrap_text(text, f, self.W - 200)
        box = pygame.Rect(60, y or self.area.top + 12, self.W - 120, 24 + f.get_linesize() * len(rows))
        theme.draw_textbox(screen, box)
        for k, row in enumerate(rows):
            theme.shadow_text(screen, row, f, box.centerx, box.y + 12 + k * f.get_linesize() + f.get_linesize() // 2,
                              align="center")
        return box

    def _note(self, screen):
        if self.note:
            f = self.fonts["button"]
            good = self.picked is not None and self.options[self.picked][1]
            theme.shadow_text(screen, self.note, f, self.W // 2, self.area.bottom - 34,
                              color=(120, 240, 120) if good else (255, 120, 100), shadow=(20, 20, 30), align="center")


class SurgeCans(_Choice):
    key = "surge"
    kind = "surge"
    title = "Lt. Surge's Trash Cans"
    how = "Lt. Surge locked his door! Each can shows a sum. The switch is in the can that makes the number. Find two switches in a row!"
    controls = (("Tap a can", "Look inside"), ("1 - 6", "Cans 1 to 6"))
    accent = (236, 178, 44)

    def target(self):
        return 2

    def goal_text(self):
        return "Find both switches"

    def good_line(self):
        return "Click! A switch!"

    def bad_line(self):
        return "Only trash in there!" + (" The locks reset!" if self.score else "")

    def wrong(self, i):
        self.note = self.bad_line()
        if self.score:  # a wrong can on the second switch resets the locks
            self.score = 0
        self._later(self._next_step, 1.2)

    def choice_rects(self):
        w, h, gap = 200, 190, 40
        x0 = (self.W - (3 * w + 2 * gap)) // 2
        y0 = self.area.top + 150
        return [pygame.Rect(x0 + (i % 3) * (w + gap), y0 + (i // 3) * (h + 30), w, h) for i in range(len(self.options))]

    def render(self, screen):
        self._banner(screen, self.prompt)
        for k in range(2):  # the door's two locks
            on = k < self.score
            pygame.draw.circle(screen, (30, 30, 40), (self.W - 110 + k * 50, self.area.top + 150), 18)
            pygame.draw.circle(screen, (90, 230, 90) if on else (220, 60, 50), (self.W - 110 + k * 50, self.area.top + 150), 13)
        f = self.fonts["s_med"]
        mouse = pygame.mouse.get_pos()
        for i, r in enumerate(self.choice_rects()):
            body = pygame.Rect(r.x + 20, r.y + 40, r.w - 40, r.h - 40)
            opened = self.picked == i
            hover = r.collidepoint(mouse) and not self.wait
            pygame.draw.rect(screen, (70, 76, 90), body.move(0, 6), border_radius=12)
            pygame.draw.rect(screen, (170, 178, 196) if hover else (150, 158, 176), body, border_radius=12)
            for x in range(body.x + 22, body.right - 10, 26):  # the ridges
                pygame.draw.line(screen, (120, 128, 146), (x, body.y + 12), (x, body.bottom - 12), 4)
            lid = pygame.Rect(r.x + 10, r.y + 22, r.w - 20, 24)
            if opened:
                lid = lid.move(46, -34)
            pygame.draw.rect(screen, (110, 118, 136), lid, border_radius=8)
            pygame.draw.rect(screen, (60, 64, 76), lid, 3, border_radius=8)
            plate = pygame.Rect(0, 0, body.w - 24, 52)
            plate.center = (body.centerx, body.centery + 10)
            pygame.draw.rect(screen, (250, 250, 250), plate, border_radius=8)
            pygame.draw.rect(screen, (60, 64, 76), plate, 3, border_radius=8)
            theme.shadow_text(screen, self.options[i][0], f, plate.centerx, plate.centery, align="center")
            if opened:
                if self.options[i][1]:  # the switch, sparking
                    for a in range(0, 360, 45):
                        t = math.radians(a + pygame.time.get_ticks() / 5)
                        pygame.draw.line(screen, (255, 230, 80), (r.centerx, r.y + 30),
                                         (r.centerx + 30 * math.cos(t), r.y + 30 + 30 * math.sin(t)), 3)
                    pygame.draw.rect(screen, (230, 60, 50), (r.centerx - 14, r.y + 18, 28, 24), border_radius=6)
                else:
                    img = icon(self.game, 88, 72)  # a Grimer in the trash
                    screen.blit(img, img.get_rect(center=(r.centerx, r.y + 22)))
        self._note(screen)


class KogaWalls(_Choice):
    key = "koga"
    kind = "koga"
    title = "Koga's Invisible Walls"
    how = "The Fuchsia Gym is full of invisible walls! Count the footprints and take the path with the right number."
    controls = (("Tap a path", "Walk down it"), ("1 / 2 / 3", "Paths 1 to 3"))
    accent = (150, 70, 210)

    def target(self):
        return 3

    def goal_text(self):
        return "Find the way to Koga"

    def _next_step(self):
        n = self.rng.randint(2, 7)
        counts = [n] + self.rng.sample([k for k in range(1, 9) if k != n], 2)
        self.rng.shuffle(counts)
        self.counts = counts
        self.prompt = f"Take the path with {n} footprints."
        self.options = [(f"Path {i + 1}", c == n) for i, c in enumerate(counts)]
        self.picked = None
        self.note = ""
        self.walk = 0.0

    def good_line(self):
        return "You found the way!"

    def bad_line(self):
        return "BONK! An invisible wall!"

    def choice_rects(self):
        w = 240
        x0 = (self.W - (3 * w + 2 * 60)) // 2
        return [pygame.Rect(x0 + i * (w + 60), self.area.top + 120, w, self.area.h - 230) for i in range(3)]

    def step(self):
        super().step()
        if self.picked is not None and self.wait:
            self.walk = min(1.0, self.walk + 0.06)

    def render(self, screen):
        self._banner(screen, self.prompt + f"  (junction {self.score + 1} of 3)")
        rects = self.choice_rects()
        for i, r in enumerate(rects):
            pygame.draw.rect(screen, (62, 44, 86), r, border_radius=14)
            pygame.draw.rect(screen, (120, 90, 160), r, 4, border_radius=14)
            theme.shadow_text(screen, str(i + 1), self.fonts["button"], r.centerx, r.bottom - 28, color=(255, 255, 255),
                              shadow=(30, 20, 40), align="center")
            n = self.counts[i]
            for k in range(n):  # footprints up the path
                y = r.bottom - 80 - k * ((r.h - 110) // max(1, n))
                x = r.centerx + (-22 if k % 2 else 22)
                pygame.draw.ellipse(screen, (230, 220, 240), (x - 12, y - 18, 24, 36))
                for t in (-9, 0, 9):
                    pygame.draw.circle(screen, (230, 220, 240), (x + t, y - 24), 5)
        ace = icon(self.game, self.team[-1], 110)
        screen.blit(ace, ace.get_rect(center=(self.W - 110, self.area.top + 200)))  # waiting past the walls
        x = self.W // 2
        y = self.area.bottom - 60
        if self.picked is not None:
            r = rects[self.picked]
            x = r.centerx
            go = self.walk if self.options[self.picked][1] else min(self.walk, 0.3) * (1 if self.walk < 0.3 else 0.5)
            y = int(self.area.bottom - 60 - go * (r.h - 60))
        me = icon(self.game, self.partner, 96)
        screen.blit(me, me.get_rect(center=(x, y)))
        if self.note and not self.options[self.picked][1]:
            Utils.draw_text_outline(screen, "BONK!", self.fonts["big"], (255, 230, 90), x, y - 80)
        self._note(screen)


class SabrinaWarps(_Choice):
    key = "sabrina"
    kind = "sabrina"
    title = "Sabrina's Warp Tiles"
    how = "The Saffron Gym is a maze of warp tiles! Step on the tile whose answer is the number. A wrong tile warps you back to the start."
    controls = (("Tap a tile", "Step on it"), ("1 - 4", "Tiles 1 to 4"))
    accent = (150, 70, 210)

    def target(self):
        return 3

    def goal_text(self):
        return "Warp through 3 rooms"

    def good_line(self):
        return "Whoosh! On to the next room!"

    def bad_line(self):
        return "Whoosh! Back to the entrance!"

    def wrong(self, i):
        self.note = self.bad_line()
        self.score = 0
        self._later(self._next_step, 1.2)

    def choice_rects(self):
        cx, cy = self.W // 2, self.area.top + 330
        spots = ((-330, -40), (-110, 60), (110, 60), (330, -40))
        return [pygame.Rect(cx + dx - 95, cy + dy - 70, 190, 140) for dx, dy in spots[:len(self.options)]]

    def render(self, screen):
        self._banner(screen, self.prompt)
        floor = pygame.Rect(40, self.area.top + 110, self.W - 80, self.area.h - 160)
        for x in range(floor.x, floor.right, 80):
            for y in range(floor.y, floor.bottom, 80):
                pygame.draw.rect(screen, (70, 56, 110) if (x // 80 + y // 80) % 2 else (82, 66, 126), (x, y, 80, 80))
        t = pygame.time.get_ticks() / 300
        f = self.fonts["s_med"]
        for i, r in enumerate(self.choice_rects()):
            glow = int(30 + 20 * math.sin(t + i))
            pygame.draw.ellipse(screen, (120 + glow, 90, 220), r)
            pygame.draw.ellipse(screen, (230, 210, 255), r.inflate(-30, -30), 4)
            pygame.draw.ellipse(screen, (255, 255, 255), r, 4)
            theme.shadow_text(screen, self.options[i][0], f, r.centerx, r.centery, color=(255, 255, 255),
                              shadow=(50, 30, 80), align="center")
        rooms = self.score
        for k in range(3):
            pygame.draw.circle(screen, (255, 210, 90) if k < rooms else (90, 80, 120), (80 + k * 46, self.area.top + 130), 14)
        me = icon(self.game, self.partner, 96)
        if self.picked is not None and self.wait:  # warping: fade out on the tile
            me = me.copy()
            me.set_alpha(max(0, 255 - int(255 * (1 - self.wait / (FPS * 1.2)) * 1.5)))
            pos = self.choice_rects()[self.picked].center
        else:
            pos = (self.W // 2, self.area.bottom - 70)
        screen.blit(me, me.get_rect(center=pos))
        abra = icon(self.game, 63, 80)
        screen.blit(abra, (self.W - 130, self.area.bottom - 120))
        self._note(screen)


class BlaineQuiz(_Choice):
    key = "quiz"
    kind = "quiz"
    title = "Blaine's Quiz Machine"
    how = "Blaine's quiz machine buzzes to life! Answer 5 questions right. Three wrong answers and the machine shuts down."
    controls = (("Tap an answer", "Choose it"), ("1 - 4", "Answers 1 to 4"))
    accent = (226, 84, 56)
    STRIKES = 3

    def target(self):
        return 5

    def goal_text(self):
        return "Answer 5 questions"

    def setup(self):
        self.strikes = 0
        super().setup()

    def good_line(self):
        return "DING DING! Correct!"

    def bad_line(self):
        return "BZZT! Wrong!"

    def wrong(self, i):
        self.strikes += 1
        self.note = self.bad_line()
        if self.strikes >= self.STRIKES:
            self._later(lambda: self.lose("Three wrong answers: the quiz machine shut down!"), 1.0)
        else:
            self._later(self._next_step)

    def choice_rects(self):
        w = 220
        x0 = (self.W - (4 * w + 3 * 30)) // 2
        return [pygame.Rect(x0 + i * (w + 30), self.area.bottom - 210, w, 120) for i in range(len(self.options))]

    def render(self, screen):
        machine = pygame.Rect(0, 0, 1000, self.area.h - 40)
        machine.midtop = (self.W // 2, self.area.top + 20)
        pygame.draw.rect(screen, (60, 30, 30), machine.move(0, 8), border_radius=24)
        pygame.draw.rect(screen, (190, 70, 50), machine, border_radius=24)
        pygame.draw.rect(screen, (250, 200, 90), machine, 6, border_radius=24)
        scr = pygame.Rect(machine.x + 70, machine.y + 40, machine.w - 140, 200)
        pygame.draw.rect(screen, (20, 30, 24), scr, border_radius=14)
        pygame.draw.rect(screen, (90, 110, 96), scr, 5, border_radius=14)
        q = self.prompt.replace("QUIZ! ", "")
        theme.shadow_text(screen, "QUIZ!", self.fonts["label"], scr.centerx, scr.y + 34, color=(255, 210, 90),
                          shadow=(20, 30, 24), align="center")
        theme.shadow_text(screen, q, self.fonts["big"], scr.centerx, scr.centery + 20, color=(120, 255, 140),
                          shadow=(20, 30, 24), align="center")
        for k in range(self.target()):  # right answers so far
            pygame.draw.circle(screen, (255, 220, 90) if k < self.score else (90, 40, 30),
                               (machine.centerx - 120 + k * 60, scr.bottom + 34), 16)
        for k in range(self.STRIKES):  # strikes
            x = machine.right - 70 - k * 44
            Utils.draw_text_outline(screen, "X", self.fonts["button"], (255, 80, 60) if k < self.strikes else (110, 60, 50),
                                    x, scr.bottom + 34)
        colors = ((226, 84, 56), (66, 130, 220), (82, 178, 86), (236, 178, 44))
        mouse = pygame.mouse.get_pos()
        for i, r in enumerate(self.choice_rects()):
            theme.command_button(screen, r, self.options[i][0], self.fonts["big"], colors[i % 4],
                                 hover=r.collidepoint(mouse) and not self.wait)
        for x, pid in ((machine.x - 10, 126), (machine.right - 90, 77)):  # Magmar and Ponyta keep watch
            img = icon(self.game, pid, 100)
            screen.blit(img, (x, machine.y - 40))
        self._note(screen)
