"""A YES / NO math quiz (Jordan 11-15: Goldenrod Radio Tower's Radio Card quiz, "math related yes or no equation questions"):
an equation is shown, true or not; answer right N times in a row to win. A wrong answer ends the try.
YesNoQuizState(game, back, rounds, done): done(won) runs after (back is put back first)."""
import random

import pygame

from src.states.base import GameState
from src.ui import theme
from src.ui.panels import CommandButton
from src.utils import Utils
from src.config import WHITE

ACCENT = (200, 120, 40)


def make_question(rng, level=1):
    """(text, is_true): "7 x 8 = 56?" - right about half the time; a wrong one is off by a little."""
    kind = rng.choice(["+", "-", "x"] if level >= 2 else ["+", "-"])
    if kind == "+":
        a, b = rng.randint(2, 50), rng.randint(2, 50); right = a + b
    elif kind == "-":
        a = rng.randint(10, 90); b = rng.randint(1, a); right = a - b
    else:
        a, b = rng.randint(2, 12), rng.randint(2, 12); right = a * b
    true = rng.random() < 0.5
    shown = right if true else right + rng.choice([-3, -2, -1, 1, 2, 3, 10, -10])
    return f"{a} {kind} {b} = {shown}", true


class YesNoQuizState(GameState):
    def __init__(self, game, back, rounds=5, done=None, title="RADIO CARD QUIZ", host="Quiz lady"):
        super().__init__(game)
        self.back, self.rounds, self.done, self.title, self.host = back, rounds, done, title, host
        self.rng = random.Random()
        level = 2 if len(game.story_manager.badges.get(game.story_manager.get_current_region(), [])) >= 2 else 1
        self.level = level
        self.n = 0
        self.q, self.truth = make_question(self.rng, level)
        self.note = ""
        f = game.assets.fonts
        w, h = game.width, game.height
        self.btn_yes = CommandButton((w // 2 - 330, int(h * 0.62), 300, 120), "YES", f["button"], lambda: self.answer(True), bg_color=theme.RUN, autosize=False)
        self.btn_no = CommandButton((w // 2 + 30, int(h * 0.62), 300, 120), "NO", f["button"], lambda: self.answer(False), bg_color=theme.FIGHT, autosize=False)
        self.finished = None

    def start(self):
        self.game.ui_manager.add_element(self.btn_yes)
        self.game.ui_manager.add_element(self.btn_no)

    def answer(self, yes):
        if self.finished is not None:
            return
        if yes == self.truth:
            self.n += 1
            if self.n >= self.rounds:
                self.finished = True
                return self._end()
            self.note = f"Correct! {self.rounds - self.n} to go."
            self.q, self.truth = make_question(self.rng, self.level)
        else:
            self.finished = False
            self._end()

    def _end(self):
        if hasattr(self.back, "is_resuming"):
            self.back.is_resuming = True
        self.game.change_state(self.back)
        if self.done:
            self.done(bool(self.finished))

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_y, pygame.K_1, pygame.K_LEFT):
                    self.answer(True)
                elif e.key in (pygame.K_n, pygame.K_2, pygame.K_RIGHT):
                    self.answer(False)

    def update(self):
        pass

    def draw(self):
        screen = self.game.screen
        f = self.game.assets.fonts
        w, h = self.game.width, self.game.height
        theme.menu_background(screen, ACCENT, self.title, f["button"], title_x=40)
        Utils.draw_text_outline(screen, f"{self.host}: Question {self.n + 1} of {self.rounds}. Is this right?", f["med"], WHITE, w // 2,
                                int(h * 0.30), outline_color=theme.shade(ACCENT, 0.45))
        box = pygame.Rect(0, 0, max(420, f["big"].size(self.q)[0] + 120), 100)
        box.center = (w // 2, int(h * 0.45))
        theme.draw_textbox(screen, box)
        theme.math_text(screen, self.q, f["big"], box.centerx, box.centery)
        if self.note:
            Utils.draw_text_outline(screen, self.note, f["med"], WHITE, w // 2, int(h * 0.56), outline_color=theme.shade(ACCENT, 0.45))
