"""The slide puzzle (Jordan, 11-07): a boulder in the way (Seafoam Islands, later Victory Road) is pushed aside
with Strength by sliding numbered tiles into order, smallest at the top left, the gap at the bottom right.
Tap a tile beside the gap (or use the arrow keys) to slide it.

The numbers follow the math difficulty (Options > MATH), counting up in a different way at each level, so
putting them in order is a counting puzzle too. 3 x 3 until Ultra Ball, then 4 x 4:

  Poke Ball 1 to 8 | Great Ball by 2s | Ultra Ball by 3s | Quick Ball by 5s | Timer Ball by 10s
  Dusk Ball a times table, 3 to 9 | Luxury Ball by 11s or 12s | Master Ball any start, any step

The puzzle is shuffled by real slides from the solved order, so it can always be solved. on_done(solved)."""
import random

import pygame

from src.states.base import GameState
from src.ui import theme


def numbers(level, rng=random):
    """(grid side, the tiles' numbers in order) for a math level (1 Poke Ball ... 8 Master Ball)."""
    level = max(1, min(8, int(level or 1)))
    side = 3 if level < 3 else 4
    count = side * side - 1
    if level == 8:
        start, step = rng.randint(11, 60), rng.randint(6, 15)
    else:
        step = {1: 1, 2: 2, 3: 3, 4: 5, 5: 10, 6: rng.randint(3, 9), 7: rng.choice((11, 12))}[level]
        start = step
    return side, [start + step * i for i in range(count)]


def shuffled(side, rng=random, moves=None):
    """The board (a list, None the gap) after real slides from the solved order."""
    board = list(range(side * side - 1)) + [None]
    gap = len(board) - 1
    last = None
    for _ in range(moves or (36 if side == 3 else 70)):
        gx, gy = gap % side, gap // side
        near = [(gx + dx, gy + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if 0 <= gx + dx < side and 0 <= gy + dy < side and (gx + dx) + (gy + dy) * side != last]
        nx, ny = rng.choice(near)
        k = nx + ny * side
        board[gap], board[k] = board[k], None
        last, gap = gap, k
    if board == list(range(side * side - 1)) + [None]:  # (shuffled back into order: once more)
        return shuffled(side, rng, (moves or 36) + 1)
    return board


class SlidePuzzleState(GameState):
    def __init__(self, game, on_done, level=None, rng=None, title="Push the boulder!"):
        super().__init__(game)
        self.rng = rng or random.Random()
        story = game.story_manager
        self.level = level or (story.get_math_level() if hasattr(story, "get_math_level") else 1)
        self.side, self.values = numbers(self.level, self.rng)
        self.board = shuffled(self.side, self.rng)
        self.on_done = on_done
        self.title = title
        self.moves = 0
        self.solved = False
        self.timer = 0

    def start(self):
        self.game.transitioning = False
        self.game.ui_manager.elements.clear()

    # ---------------------------------------------------------------- the board
    def _rects(self):
        W, H = self.game.width, self.game.height
        size = min(int(H * 0.62), 470)
        cell = size // self.side
        x0, y0 = W // 2 - cell * self.side // 2, int(H * 0.22)
        return [pygame.Rect(x0 + (k % self.side) * cell + 4, y0 + (k // self.side) * cell + 4, cell - 8, cell - 8)
                for k in range(self.side * self.side)]

    def _leave_rect(self):
        return pygame.Rect(self.game.width - 230, self.game.height - 100, 200, 70)

    def slide(self, k):
        """Slide the tile at k into the gap, if it's beside it. True if it moved."""
        if self.solved or self.board[k] is None:
            return False
        gap = self.board.index(None)
        kx, ky, gx, gy = k % self.side, k // self.side, gap % self.side, gap // self.side
        if abs(kx - gx) + abs(ky - gy) != 1:
            return False
        self.board[gap], self.board[k] = self.board[k], None
        self.moves += 1
        if self.board == list(range(self.side * self.side - 1)) + [None]:
            self.solved = True
            self.timer = 75
            sfx = getattr(self.game.assets, "heal_sfx", None)
            if sfx:
                sfx.play()
        return True

    def _key(self, key):
        """Arrow keys move the tile on that side of the gap into it (left: the one right of the gap)."""
        way = {pygame.K_LEFT: (1, 0), pygame.K_RIGHT: (-1, 0), pygame.K_UP: (0, 1), pygame.K_DOWN: (0, -1),
               pygame.K_a: (1, 0), pygame.K_d: (-1, 0), pygame.K_w: (0, 1), pygame.K_s: (0, -1)}.get(key)
        if way is None:
            return
        gap = self.board.index(None)
        x, y = gap % self.side + way[0], gap // self.side + way[1]
        if 0 <= x < self.side and 0 <= y < self.side:
            self.slide(x + y * self.side)

    def _finish(self, solved):
        self.game.ui_manager.elements.clear()
        self.on_done(solved)

    def handle_events(self, events):
        for e in events:
            if self.solved:
                continue
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self._leave_rect().collidepoint(e.pos):
                    return self._finish(False)
                for k, r in enumerate(self._rects()):
                    if r.collidepoint(e.pos):
                        self.slide(k)
                        break
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return self._finish(False)
                self._key(e.key)

    def update(self):
        if self.solved and self.timer > 0:
            self.timer -= 1
            if self.timer == 0:
                self._finish(True)

    def draw(self):
        screen = self.game.screen
        fonts = self.game.assets.fonts
        W, H = self.game.width, self.game.height
        screen.fill((34, 40, 62))
        top = pygame.Rect(40, 18, W - 80, int(H * 0.16))
        theme.draw_textbox(screen, top)
        line = "It moved! The way is clear." if self.solved else \
            f"{self.title} Slide the numbers into order, smallest first."
        theme.shadow_text(screen, line, fonts["label"], top.centerx, top.y + 16, align="center")
        hint = f"Count by {self.values[1] - self.values[0]}s from {self.values[0]}.   Moves: {self.moves}"
        theme.shadow_text(screen, hint, fonts["small"], top.centerx, top.y + 58, align="center")
        rects = self._rects()
        frame = rects[0].union(rects[-1]).inflate(24, 24)
        pygame.draw.rect(screen, (90, 78, 66), frame, border_radius=16)
        pygame.draw.rect(screen, (60, 50, 42), frame, 4, border_radius=16)
        mouse = pygame.mouse.get_pos()
        gap = self.board.index(None)
        big = fonts["button"] if self.side == 3 else fonts["label"]
        for k, r in enumerate(rects):
            v = self.board[k]
            if v is None:
                pygame.draw.rect(screen, (60, 50, 42), r, border_radius=10)
                continue
            beside = abs(k % self.side - gap % self.side) + abs(k // self.side - gap // self.side) == 1
            right = v == k  # (already in its place)
            col = (120, 196, 120) if right or self.solved else (226, 214, 190)
            if beside and r.collidepoint(mouse) and not self.solved:
                col = (250, 236, 170)
            pygame.draw.rect(screen, col, r, border_radius=10)
            pygame.draw.rect(screen, (110, 92, 70), r, 3, border_radius=10)
            t = big.render(str(self.values[v]), True, (50, 40, 34))
            screen.blit(t, t.get_rect(center=r.center))
        if not self.solved:
            lr = self._leave_rect()
            theme.command_button(screen, lr, "LEAVE", fonts["button"], theme.BACK, hover=lr.collidepoint(mouse))
