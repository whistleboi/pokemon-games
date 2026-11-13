"""Story-event math puzzles (menu-node style), and the questions behind Kanto's Gym challenges.

make_step(kind, step) makes one screen's question. Kanto's Gym challenges (src/minigames/kanto.py:
Lt. Surge's trash cans, Sabrina's warp tiles, Blaine's quiz machine) draw their questions from the
"surge", "sabrina" and "quiz" kinds. (The Gyms' old menu puzzles, Koga's and the Orange Crew's
included, gave way to the Gym challenge minigames on 11-01.)

Story events run a puzzle with GymPuzzleState ("puzzle": kind, see overworld._start_event_puzzle):
- braille (Sevii, Dotted Hole): count the raised dots in the wall's cells.
- security (Sevii, Rocket Warehouse): a door code is three numbers added up.
- tanoby (Sevii, Tanoby Ruins): what comes next in the pattern (2, 4, 6, ?).
- illusion (Decolore, Grand Spectrala): Zoroark's fake doors. Only one sign tells the truth.
- carvings (Sinjoh Ruins, the frozen spring): which carving shows the bigger number?
- cafe (Lumiose, Rouge District): a cafe job. Find the order whose two prices add up to the bill.
- galette (Lumiose, Magenta District): count the galettes on each tray and hand over the right one.
- coins (Fortree City, the Hidden Power old woman): which hand holds the coin? The one whose sum makes her number.
"""
import random


from src.states.base import GameState
from src.utils import Utils
from src.ui.widgets import Button
from src.config import WHITE, BLACK, GREEN, PURPLE, GOLD


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
    if kind == "sabrina":
        target = rng.randint(2, 10)
        wrong = rng.sample([n for n in range(1, 13) if n != target], 3)
        tiles = [(f"{_diff_pair(target, rng)}", True)] + [(f"{_diff_pair(n, rng)}", False) for n in wrong]
        rng.shuffle(tiles)
        return (f"Room {step + 1}: step on the warp tile whose answer is {target}.", "", tiles)
    if kind == "braille":
        cells = [rng.randint(1, 6) for _ in range(2)]
        target = sum(cells)
        pics = "    ".join("[" + "o" * n + "." * (6 - n) + "]" for n in cells)
        opts = {target}
        while len(opts) < 4:
            opts.add(max(2, target + rng.choice([-3, -2, -1, 1, 2, 3])))
        return ("Count the raised dots (o) in both cells. How many in all?", pics,
                [(str(o), o == target) for o in sorted(opts)])
    if kind == "coins":  # (ORAS: guess which hand, three times running; here, work it out)
        target = rng.randint(6, 14)
        other = rng.choice([n for n in range(4, 17) if n != target])
        hands = [("Left hand: " + _sum_pair(target, rng), True), ("Right hand: " + _sum_pair(other, rng), False)]
        if rng.random() < 0.5:
            hands = [("Left hand: " + _sum_pair(other, rng), False), ("Right hand: " + _sum_pair(target, rng), True)]
        return (f"Round {step + 1}: the coin is in the hand that makes {target}. Which hand?", "", hands)
    if kind == "security":
        nums = [rng.randint(1, 9) for _ in range(3)]
        code = sum(nums)
        opts = {code}
        while len(opts) < 4:
            opts.add(max(3, code + rng.choice([-4, -2, -1, 1, 2, 4])))
        return (f"Door {step + 1}: the code is {nums[0]} + {nums[1]} + {nums[2]}.", "",
                [(str(o), o == code) for o in sorted(opts)])
    if kind == "tanoby":
        stepv = rng.choice([1, 2, 3, 5, 10])
        start = rng.randint(1, 10)
        seq = [start + stepv * i for i in range(4)]
        ans = start + stepv * 4
        opts = {ans}
        while len(opts) < 4:
            opts.add(max(1, ans + rng.choice([-stepv, stepv, -1, 1, 2])))
        return (f"Chamber {step + 1}: the carvings count {', '.join(map(str, seq))}, ... What comes next?", "",
                [(str(o), o == ans) for o in sorted(opts)])
    if kind == "illusion":
        signs = []
        a, b = rng.randint(2, 9), rng.randint(2, 9)
        signs.append((f"{a} + {b} = {a + b}", True))
        while len(signs) < 4:
            x, y = rng.randint(2, 9), rng.randint(2, 9)
            fake = x + y + rng.choice([-2, -1, 1, 2])
            label = f"{x} + {y} = {fake}"
            if all(label != s[0] for s in signs):
                signs.append((label, False))
        rng.shuffle(signs)
        return (f"Door {step + 1}: Zoroark made fake doors! Pick the door whose sign is TRUE.", "", signs)
    if kind == "carvings":
        a, b = rng.randint(2, 9), rng.randint(2, 9)
        left = a + b
        right = left + rng.choice([-3, -2, -1, 1, 2, 3])
        opts = [(f"{a} + {b}", left > right), (str(right), right > left)]
        rng.shuffle(opts)
        return (f"Ice seal {step + 1}: touch the carving with the BIGGER number.", "", opts)
    if kind == "cafe":
        target = rng.randint(6, 15)
        wrong = rng.sample([n for n in range(4, 18) if n != target], 3)
        orders = [(_sum_pair(target, rng), True)] + [(_sum_pair(n, rng), False) for n in wrong]
        rng.shuffle(orders)
        return (f"Table {step + 1}'s bill is ${target}. Which order did they have?", "", orders)
    if kind == "galette":
        target = rng.randint(3, 9)
        counts = [target] + rng.sample([n for n in range(2, 11) if n != target], 2)
        rng.shuffle(counts)
        pics = "    ".join(f"Tray {i + 1}: " + "o" * n for i, n in enumerate(counts))
        return (f"A customer wants {target} Lumiose Galettes. Which tray is it?", pics,
                [(f"TRAY {i + 1}", n == target) for i, n in enumerate(counts)])
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
    return (f"QUIZ! What is {q}?", "", [(str(o), o == ans) for o in opts])


STEPS = {"coins": 3, "braille": 3, "security": 3, "tanoby": 7, "illusion": 3, "carvings": 3, "cafe": 3, "galette": 3}
INTRO = {
    "coins": "The old woman holds out two closed hands. \"Which one has the coin? Get it right three times!\"",
    "braille": "Strange dots are carved into the walls of the Dotted Hole...",
    "security": "The warehouse doors are locked with number pads!",
    "tanoby": "Seven chambers, seven sealed doors, each carved with a number pattern.",
    "illusion": "The woods shimmer. Every path looks the same... it's an illusion!",
    "carvings": "Three ice seals cover the spring, each carved with numbers.",
    "cafe": "Cafe Soleil is busy! Help ring up three tables.",
    "galette": "The galette stall has a line of customers. Hand each the right tray!",
}
WRONG = {
    "coins": ("Empty! Not that hand.", "Empty! Let's start over from the first round."),
    "braille": ("Nothing happens.", "Nothing happens."),
    "security": ("BZZT! Wrong code.", "BZZT! Wrong code. The alarm resets the doors!"),
    "tanoby": ("The door stays shut.", "The door stays shut."),
    "illusion": ("Poof! That door was an illusion.", "Poof! An illusion! You're back at the start."),
    "carvings": ("The ice stays frozen.", "The ice stays frozen."),
    "cafe": ("That's not their order!", "Oops! The orders got mixed up. Start again."),
    "galette": ("That's the wrong tray!", "Oops! Those trays got mixed up. Start again."),
}
DONE = {
    "coins": "Three in a row! The old woman laughs with delight.",
    "braille": "The wall rumbles open! A passage leads deeper underground.",
    "security": "Click! The last door slides open.",
    "tanoby": "All seven chambers are open! Unown pour out of the ruins!",
    "illusion": "The illusion fades. A Zoroark steps out, laughing, and points the way.",
    "carvings": "Crack! The last seal melts away.",
    "cafe": "Every table is paid up. The owner is delighted!",
    "galette": "Every customer leaves happy, munching a galette!",
}


class GymPuzzleState(GameState):
    """kind: one of the story events' puzzles (braille, security...). on_done(solved: bool) when it ends."""

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
        if right:
            self.step += 1
            if self.step >= STEPS[self.kind]:
                self.message = DONE[self.kind]
                return self._finish(True)
            self.message = "That's it! Keep going."
        else:
            first, later = WRONG[self.kind]
            self.message = first if self.step == 0 else later
            if self.kind in ("security", "illusion"):
                self.step = 0  # the alarm resets the doors; Zoroark sends you back
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
        font = self.game.assets.fonts.get("s_med") or self.game.assets.fonts["label"]
        color = PURPLE
        for i, (label, _) in enumerate(self.options):
            r, c = divmod(i, cols)
            self.buttons.append(Button((x0 + c * (bw + gap), y0 + r * (bh + gap), bw, bh), label, font,
                                       (lambda k=i: self.answer(k)), bg_color=color, autosize=False))
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
        f_big = self.game.assets.fonts.get("s_med") or self.game.assets.fonts["label"]
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
