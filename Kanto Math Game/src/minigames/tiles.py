"""The Tile Puzzle (Jordan, 11-01): HeartGold/SoulSilver's Ruins of Alph panels, drawn with Pokemon
Essentials' pictures (assets/sprites/game_corner/tiles, dev/builders/import_game_corner.py).

The pieces start in the slots either side of the stone frame; move them onto the board in the middle
until the picture is whole. Tap a piece, then a free spot (or another piece, to swap them). Keys: the
arrows move the cursor, Enter picks up and puts down.

- TilePuzzle: a Gym challenge (in the random pool): the picture is the Gym Leader's ace, in 3 x 3
  (early Gyms) or 4 x 4 pieces.
- AlphPuzzle: the Ruins of Alph's four chambers (Kabuto, Omanyte, Aerodactyl, Ho-Oh), canon in
  Johto; each opens once and stays solved (story flag alph_<panel>_solved).
"""
import os

import pygame

from src.minigames.base import Minigame, species_name
from src.ui import theme

W0, H0 = 512, 384
BOARD = (160, 64, 192)           # the frame's inner square: x, y, side (the picture's 192 x 192)
LEFT, RIGHT = (20, 64), (396, 64)  # the side slots: 2 columns x 4 rows of 48
SLOT = 48
_pics = {}


def _pic(game, name):
    if name not in _pics:
        path = os.path.join(game.assets.assets_dir or "", "sprites", "game_corner", "tiles", name)
        try:
            _pics[name] = pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError):
            _pics[name] = None
    return _pics[name]


class TilePuzzle(Minigame):
    key = "tiles"
    title = "Tile Puzzle"
    how = "Put the picture back together! Move each piece from the sides onto the board in the middle."
    controls = (("Tap a piece", "Pick it up"), ("Tap a spot", "Put it there (or swap)"),
                ("Arrows + Enter", "Move, pick up, put down"))
    accent = (176, 140, 60)
    WALL = "bg.png"

    def picture(self):
        """The finished picture, 192 x 192: the Leader's ace on a stone tablet."""
        ace = self.team[-1]
        self.title = f"{species_name(self.game, ace)} Puzzle"
        surf = pygame.Surface((192, 192))
        surf.fill((206, 188, 140))
        for i in range(0, 192, 24):  # faint stone grain
            pygame.draw.line(surf, (192, 172, 124), (0, i), (192, i), 1)
        img = self.game.assets.get_pokemon_image(ace, "normal", False)
        if img:
            box = img.get_bounding_rect()
            img = img.subsurface(box) if box.w and box.h else img
            k = 176 / max(img.get_width(), img.get_height())
            img = pygame.transform.smoothscale(img, (max(1, int(img.get_width() * k)), max(1, int(img.get_height() * k))))
            surf.blit(img, img.get_rect(center=(96, 96)))
        return surf

    def size(self):
        return 3 if self.level < 3 else 4

    def target(self):
        return self.n * self.n

    def goal_text(self):
        return "Rebuild the picture"

    # ---- layout: the wall picture fits the play area (crisp), centred
    def _layout(self):
        self.k = min(self.W / W0, self.area.h / H0)
        self.ox = (self.W - int(W0 * self.k)) // 2
        self.oy = self.area.top + (self.area.h - int(H0 * self.k)) // 2

    def _at(self, x, y):
        return self.ox + int(x * self.k), self.oy + int(y * self.k)

    def setup(self):
        self._layout()
        self.n = self.size()
        whole = self.picture()
        part = 192 // self.n
        self.cell = int(192 * self.k) // self.n
        self.slot = int(SLOT * self.k)
        self.pieces = {}  # piece -> (image on the board, image in a slot)
        for i in range(self.n * self.n):
            r, c = divmod(i, self.n)
            sub = whole.subsurface((c * part, r * part, part, part))
            self.pieces[i] = (pygame.transform.scale(sub, (self.cell, self.cell)),
                              pygame.transform.scale(sub, (self.slot, self.slot)))
        wall = _pic(self.game, self.WALL) or _pic(self.game, "bg.png")
        self.wall = pygame.transform.scale(wall, (int(W0 * self.k), int(H0 * self.k))) if wall else None
        # spots: ("B", i) board cells, ("S", j) side slots (0-7 left, 8-15 right)
        self.spots = {("B", i): None for i in range(self.n * self.n)}
        self.spots.update({("S", j): None for j in range(16)})
        slots = list(range(16))
        self.rng.shuffle(slots)
        for piece, j in zip(range(self.n * self.n), slots):
            self.spots[("S", j)] = piece
        self.held = None
        self.cursor = ("S", 0)
        self.score = 0

    def spot_rect(self, spot):
        kind, i = spot
        if kind == "B":
            r, c = divmod(i, self.n)
            x, y = self._at(BOARD[0], BOARD[1])
            return pygame.Rect(x + c * self.cell, y + r * self.cell, self.cell, self.cell)
        side = LEFT if i < 8 else RIGHT
        j = i % 8
        x, y = self._at(side[0] + (j % 2) * SLOT, side[1] + (j // 2) * SLOT)
        return pygame.Rect(x, y, self.slot, self.slot)

    def _use(self, spot):
        here = self.spots[spot]
        if self.held is None:
            if here is not None:
                self.held = spot
            return
        if spot == self.held:
            self.held = None
            return
        self.spots[spot], self.spots[self.held] = self.spots[self.held], here  # put down (or swap)
        self.held = None
        self.score = sum(1 for i in range(self.n * self.n) if self.spots[("B", i)] == i)
        self.check_goal()

    def on_tap(self, pos):
        for spot in self.spots:
            if self.spot_rect(spot).collidepoint(pos):
                self.cursor = spot
                self._use(spot)
                return

    def _grid(self):
        """The spots as one grid for the arrow keys: left slots, the board, right slots."""
        rows = max(4, self.n)
        cols = 2 + self.n + 2
        g = {}
        for r in range(rows):
            for c in range(cols):
                if c < 2:
                    spot = ("S", r * 2 + c) if r < 4 else None
                elif c < 2 + self.n:
                    spot = ("B", r * self.n + c - 2) if r < self.n else None
                else:
                    spot = ("S", 8 + r * 2 + c - 2 - self.n) if r < 4 else None
                if spot:
                    g[(c, r)] = spot
        return g

    def on_key(self, key):
        d = {pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0), pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1),
             pygame.K_a: (-1, 0), pygame.K_d: (1, 0), pygame.K_w: (0, -1), pygame.K_s: (0, 1)}.get(key)
        g = self._grid()
        if d:
            pos = next(p for p, s in g.items() if s == self.cursor)
            cols, rows = max(c for c, _ in g) + 1, max(r for _, r in g) + 1
            c, r = pos
            for _ in range(cols * rows):
                c, r = (c + d[0]) % cols, (r + d[1]) % rows
                if (c, r) in g:
                    self.cursor = g[(c, r)]
                    return
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            self._use(self.cursor)

    def render(self, screen):
        if self.wall:
            screen.blit(self.wall, (self.ox, self.oy))
        for spot, piece in self.spots.items():
            r = self.spot_rect(spot)
            if spot[0] == "B" and piece is None:  # the empty board shows faint lines
                pygame.draw.rect(screen, (0, 0, 0), r, 1)
            if piece is None:
                continue
            img = self.pieces[piece][0 if spot[0] == "B" else 1]
            screen.blit(img, r)
            pygame.draw.rect(screen, (60, 46, 30), r, 2)
            if spot == self.held:
                pygame.draw.rect(screen, (255, 230, 90), r.inflate(6, 6), 5, border_radius=6)
        pygame.draw.rect(screen, (230, 60, 50), self.spot_rect(self.cursor).inflate(10, 10), 4, border_radius=6)
        if self.held:
            f = self.game.assets.fonts["caption"]
            theme.shadow_text(screen, "Now tap where it goes", f, self.W // 2, self.area.bottom - 18,
                              color=(255, 255, 255), shadow=(20, 20, 30), align="center")


class AlphPuzzle(TilePuzzle):
    """One of the Ruins of Alph's chambers: its own panel and wall, always 4 x 4."""
    key = "alph"
    in_pool = False
    PANELS = {"kabuto": ("kabuto.png", "bg.png", 140), "omanyte": ("omanyte.png", "bg_omanyte.png", 138),
              "aerodactyl": ("aerodactyl.png", "bg_aerodactyl.png", 142), "hooh": ("hooh.png", "bg_hooh.png", 250)}
    how = "A stone panel in the chamber is broken into pieces. Put the picture back together!"
    win_line = "The panel is whole again!"

    def __init__(self, game, on_done, panel="kabuto", **kw):
        self.panel = panel if panel in self.PANELS else "kabuto"
        self.WALL = self.PANELS[self.panel][1]
        super().__init__(game, on_done, team=[self.PANELS[self.panel][2]], **kw)

    def size(self):
        return 4

    def picture(self):
        self.title = f"{species_name(self.game, self.PANELS[self.panel][2])} Panel"
        img = _pic(self.game, self.PANELS[self.panel][0])
        return img.copy() if img else super().picture()


def flag(panel):
    return f"alph_{panel}_solved"
