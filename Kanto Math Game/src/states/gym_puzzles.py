"""Kanto gym puzzles as K-3 math minigames (menu-node style, like the rest of the game).

- Vermilion (Lt. Surge): trash cans. Each can shows an addition; the switch is in the can whose
  sum is the target. Find two switches in a row; a wrong can on the second resets the locks.
- Fuchsia (Koga): invisible walls. Count the footprints and take the path with the right number.
- Saffron (Sabrina): warp tiles. Step on the tile whose answer matches; a wrong tile warps you back.
- Cinnabar (Blaine): quiz machine before each gym trainer. Right answer = that trainer is skipped,
  wrong answer = battle them (canon FRLG).

Solving Surge/Koga/Sabrina's puzzle sets story flag gym_puzzle_<AREA> and opens the leader.
"""
import random

import pygame

from src.states.base import GameState
from src.utils import Utils
from src.ui.widgets import Button
from src.config import WHITE, BLACK, BLUE, GREEN, RED, ORANGE, PURPLE, GOLD

PUZZLE_GYMS = {"VERMILLION_CITY": "surge", "FUCHSIA_CITY": "koga", "SAFFRON_CITY": "sabrina"}
QUIZ_GYMS = {"CINNABAR_ISLAND"}


def puzzle_flag(area_key):
    return f"gym_puzzle_{area_key}"


def needs_puzzle(story, area_key):
    return area_key in PUZZLE_GYMS and not story.story_flags.get(puzzle_flag(area_key))


def _sum_pair(total, rng):
    a = rng.randint(0, total)
    return f"{a} + {total - a}"


def _diff_pair(answer, rng):
    b = rng.randint(1, 9)
    return f"{answer + b} - {b}"


def make_step(kind, step, rng=random):
    """One puzzle screen: (prompt, picture_text, [(label, is_right), ...])."""
    if kind == "surge":
        target = rng.randint(5, 12)
        wrong = rng.sample([n for n in range(3, 15) if n != target], 5)
        cans = [(f"{_sum_pair(target, rng)}", True)] + [(f"{_sum_pair(n, rng)}", False) for n in wrong]
        rng.shuffle(cans)
        which = "first" if step == 0 else "second"
        return (f"The {which} switch is in the trash can that makes {target}!", "", cans)
    if kind == "koga":
        target = rng.randint(2, 7)
        counts = [target] + rng.sample([n for n in range(1, 9) if n != target], 2)
        rng.shuffle(counts)
        pics = "    ".join(f"Path {i + 1}: " + "o" * n for i, n in enumerate(counts))
        return (f"Koga's walls are invisible! Take the path with {target} footprints.", pics,
                [(f"PATH {i + 1}", n == target) for i, n in enumerate(counts)])
    if kind == "sabrina":
        target = rng.randint(2, 10)
        wrong = rng.sample([n for n in range(1, 13) if n != target], 3)
        tiles = [(f"{_diff_pair(target, rng)}", True)] + [(f"{_diff_pair(n, rng)}", False) for n in wrong]
        rng.shuffle(tiles)
        return (f"Room {step + 1}: step on the warp tile whose answer is {target}.", "", tiles)
    # Blaine's quiz
    a, b = rng.randint(1, 10), rng.randint(1, 10)
    if rng.random() < 0.5 or a < b:
        q, ans = f"{a} + {b}", a + b
    else:
        q, ans = f"{a} - {b}", a - b
    opts = {ans}
    while len(opts) < 4:
        opts.add(max(0, ans + rng.choice([-3, -2, -1, 1, 2, 3])))
    opts = sorted(opts)
    return (f"QUIZ! What is {q}?", "Right answer: skip this trainer. Wrong answer: battle!",
            [(str(o), o == ans) for o in opts])


STEPS = {"surge": 2, "koga": 3, "sabrina": 3, "quiz": 1}
INTRO = {
    "surge": "Lt. Surge locked his door! Two switches are hidden in the trash cans.",
    "koga": "The Fuchsia Gym is full of invisible walls!",
    "sabrina": "The Saffron Gym is a maze of warp tiles!",
    "quiz": "Blaine's quiz machine buzzes to life!",
}
WRONG = {
    "surge": ("Nope! Only trash in there.", "The locks reset! Start over."),
    "koga": ("BONK! An invisible wall!", "BONK! An invisible wall!"),
    "sabrina": ("Whoosh! You warped back to the entrance.", "Whoosh! You warped back to the entrance."),
}
DONE = {
    "surge": "Click! Both switches are on. The door to Lt. Surge opened!",
    "koga": "You found the way through! Koga is waiting.",
    "sabrina": "You warped right in front of Sabrina!",
}


class GymPuzzleState(GameState):
    """kind: surge / koga / sabrina / quiz. on_done(solved: bool) is called when it ends."""

    def __init__(self, game, area_key, kind, on_done, rng=None):
        super().__init__(game)
        self.area_key, self.kind, self.on_done = area_key, kind, on_done
        self.rng = rng or random.Random()
        self.step = 0
        self.message = INTRO[kind]
        self.finished = False
        self.timer = 0
        self.buttons = []
        self._new_step()

    # --- logic (kept UI-free so it can be tested headless) ---
    def _new_step(self):
        self.prompt, self.picture, self.options = make_step(self.kind, self.step, self.rng)
        self._build_buttons()

    def answer(self, index):
        if self.finished:
            return
        right = self.options[index][1]
        if self.kind == "quiz":
            self.message = "Correct! You may pass this trainer." if right else "Wrong! Get ready to battle!"
            return self._finish(right)
        if right:
            self.step += 1
            if self.step >= STEPS[self.kind]:
                self.message = DONE[self.kind]
                self.game.story_manager.story_flags[puzzle_flag(self.area_key)] = True
                return self._finish(True)
            self.message = "That's it! Keep going."
        else:
            first, later = WRONG[self.kind]
            self.message = first if self.step == 0 else later
            if self.kind in ("surge", "sabrina"):
                self.step = 0  # Surge's locks reset; Sabrina's warp sends you back
        self._new_step()

    def _finish(self, solved):
        self.finished = True
        self.solved = solved
        self.timer = 75  # show the result a moment, then leave
        for b in self.buttons:
            b.set_visibility(False)

    def leave(self):
        if not self.finished:
            self.finished, self.solved = True, False
        self.on_done(self.solved)

    # --- UI ---
    def _build_buttons(self):
        ui = getattr(self.game, "ui_manager", None)
        for b in self.buttons:
            if ui and b in ui.elements:
                ui.elements.remove(b)
        self.buttons = []
        w, h = self.game.width, self.game.height
        n = len(self.options)
        cols = 3 if n > 4 else 2 if n > 1 else 1
        bw, bh, gap = min(360, (w - 120) // cols - 20), 80, 20
        x0 = (w - (cols * bw + (cols - 1) * gap)) // 2
        y0 = int(h * 0.45)
        font = self.game.assets.fonts.get("s_med") or self.game.assets.fonts["small"]
        color = {"surge": ORANGE, "koga": PURPLE, "sabrina": BLUE, "quiz": RED}[self.kind]
        for i, (label, _) in enumerate(self.options):
            r, c = divmod(i, cols)
            self.buttons.append(Button((x0 + c * (bw + gap), y0 + r * (bh + gap), bw, bh), label, font,
                                       (lambda k=i: self.answer(k)), bg_color=color, autosize=False))
        if self.kind != "quiz":
            self.buttons.append(Button((w - 240, h - 110, 200, 70), "LEAVE", font, self.leave,
                                       bg_color=GREEN, autosize=False))
        if ui:
            for b in self.buttons:
                ui.add_element(b)

    def start(self):
        self.game.transitioning = False
        self.game.ui_manager.elements.clear()
        for b in self.buttons:
            self.game.ui_manager.add_element(b)

    def handle_events(self, events):
        pass

    def update(self):
        if self.finished and self.timer > 0:
            self.timer -= 1
            if self.timer == 0:
                self.on_done(self.solved)

    def draw(self):
        screen = self.game.screen
        screen.fill((30, 30, 50))
        w, h = self.game.width, self.game.height
        f_big = self.game.assets.fonts.get("s_med") or self.game.assets.fonts["small"]
        f_small = self.game.assets.fonts.get("small") or f_big
        Utils.draw_classic_panel(screen, 40, 30, w - 80, int(h * 0.36))
        Utils.draw_multiline_text(screen, self.message, f_small, GOLD, w // 2, 75, max_width=w - 160,
                                  line_height=36, outline_color=BLACK)
        Utils.draw_multiline_text(screen, self.prompt, f_big, WHITE, w // 2, 160, max_width=w - 160,
                                  line_height=56, outline_color=BLACK)
        if self.picture:
            Utils.draw_multiline_text(screen, self.picture, f_small, WHITE, w // 2, 250, max_width=w - 160,
                                      line_height=36, outline_color=BLACK)
        self.game.ui_manager.draw(screen)
