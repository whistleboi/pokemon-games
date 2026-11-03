"""The Game Corner's games and counters (Jordan, 11-01), drawn with Pokemon Essentials' Slot Machine
and Voltorb Flip pictures (from Pokemon Orre 2.1.1: dev/builders/import_game_corner.py), the
HeartGold/SoulSilver look. Each machine's 512 x 384 picture is scaled up (crisp) to the screen's height,
centred, with our buttons either side.

Coins: kept in story flag "game_corner_coins" (max 9,999). Bought at the counter (50 for $1,000),
won at the Slots and Voltorb Flip, spent at the Prize Counter.

- SlotsState: bet 1-3 coins (1-3 pay lines), START, then STOP each reel (tap its button, or 1 / 2 / 3,
  Space stops the next). The machine's own table pays: 7-7-7 300, mixed 7s 90, Pikachu or Psyduck
  15, Magnemite or Shellder 8, a cherry 2 (two: 4); 3 Replays: a free spin.
- VoltorbFlipState: the HeartGold/SoulSilver game. Each row and column shows its points and how many
  Voltorb hide in it; flip tiles (1, 2, 3 multiply your coins), find every 2 and 3 to clear the
  level; a Voltorb loses the round's coins. Memo marks; levels 1-8.
- PrizeCounterState: each Game Corner's prizes (Pokemon and items) for coins.
- BlackjackState: Blackjack for coins against Meowth (our own code; the classic card game).
"""
import os
import random

import pygame

from src.states.base import GameState
from src.ui import theme
from src.ui.panels import CommandButton
from src.utils import Utils
from src.config import FPS

COINS_FLAG = "game_corner_coins"
MAX_COINS = 9999
COIN_PRICE = 20  # $1,000 for 50 coins, as in the games
COIN_PACKS = (50, 100, 500, 1000)  # the counter's choices (Jordan, 11-02)


def coins(story):
    return int(story.story_flags.get(COINS_FLAG, 0) or 0)


def add_coins(story, n):
    story.story_flags[COINS_FLAG] = max(0, min(MAX_COINS, coins(story) + int(n)))


def coin_cost(n):
    return n * COIN_PRICE


def buy_coins(story, n=50):
    """n coins for $20 each. Returns the line to show."""
    price = coin_cost(n)
    if story.money < price:
        return f"You need ${price:,} for {n:,} coins."
    if coins(story) + n > MAX_COINS:
        return f"Your Coin Case can't hold {n:,} more coins! (It holds {MAX_COINS:,}.)"
    story.money -= price
    add_coins(story, n)
    return f"You bought {n:,} coins for ${price:,}! You have {coins(story):,} coins."


class PriceButton(CommandButton):
    """A command button with a second line under its label (a price, what a game is)."""

    def __init__(self, rect, text, sub, font, small, callback, bg_color):
        super().__init__(rect, text, font, callback, bg_color=bg_color, autosize=False)
        self.sub, self.small = sub, small

    def draw(self, surface):
        if not self.visible:
            return
        hover = self.callback is not None and self.rect.collidepoint(pygame.mouse.get_pos())
        color = self.bg_color if self.callback is not None else (128, 132, 144)
        theme.command_button(surface, self.rect, self.text, self.font, color, hover=hover, small=self.small,
                             sub=self.sub)


_pics = {}


def pic(game, kind, name):
    """A Game Corner picture (assets/sprites/game_corner/<kind>/<name>), or None."""
    key = (kind, name)
    if key not in _pics:
        path = os.path.join(game.assets.assets_dir or "", "sprites", "game_corner", kind, name)
        try:
            _pics[key] = pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError):
            _pics[key] = None
    return _pics[key]


def frames(img, count, vertical=False):
    if img is None:
        return []
    w, h = img.get_size()
    if vertical:
        return [img.subsurface((0, i * h // count, w, h // count)) for i in range(count)]
    return [img.subsurface((i * w // count, 0, w // count, h)) for i in range(count)]


class _Machine(GameState):
    """A machine screen: its 512 x 384 picture scaled to the screen height (crisp), centred; the
    Game Corner's background either side; EXIT and the coin count in the left margin."""
    W0, H0 = 512, 384

    def __init__(self, game, previous_state, background=None):
        super().__init__(game)
        self.previous_state = previous_state
        self.story = game.story_manager
        self.k = game.height / self.H0
        self.ox = (game.width - int(self.W0 * self.k)) // 2
        self.side = None
        if background is not None:
            self.side = pygame.transform.smoothscale(background, (game.width, game.height))
            shade = pygame.Surface(self.side.get_size(), pygame.SRCALPHA)
            shade.fill((10, 10, 20, 170))
            self.side.blit(shade, (0, 0))
        self.buttons = [CommandButton((16, 14, self.ox - 32, 60), "EXIT", game.assets.fonts["button"], self.leave,
                                      bg_color=theme.BACK, autosize=False)]

    def S(self, img):
        """A picture at the machine's scale (crisp)."""
        return pygame.transform.scale(img, (int(img.get_width() * self.k), int(img.get_height() * self.k)))

    def at(self, x, y):
        """A point of the 512 x 384 picture on the screen."""
        return self.ox + int(x * self.k), int(y * self.k)

    def leave(self):
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.transitioning = False
        self.game.ui_manager.elements.clear()
        for b in self.buttons:
            self.game.ui_manager.add_element(b)

    def draw_frame(self, screen):
        if self.side:
            screen.blit(self.side, (0, 0))
        else:
            screen.fill((24, 20, 36))

    def side_text(self, screen, text, cx, y, color=(255, 255, 255)):
        """A few words in a side margin, wrapped to fit it."""
        from src.ui.dialogue import wrap_text
        f = self.game.assets.fonts["caption"]
        for i, row in enumerate(wrap_text(text, f, self.ox - 24)):
            theme.shadow_text(screen, row, f, cx, y + i * (f.get_linesize() + 2), color=color, shadow=(20, 20, 30),
                              align="center")

    def draw_coins(self, screen, extra=None):
        f = self.game.assets.fonts
        box = pygame.Rect(16, 96, self.ox - 32, 110)
        theme.draw_textbox(screen, box)
        theme.shadow_text(screen, "COINS", f["label"], box.centerx, box.y + 22, align="center")
        theme.shadow_text(screen, f"{coins(self.story):,}", f["button"], box.centerx, box.y + 70, align="center")
        if extra:
            self.side_text(screen, extra, box.centerx, box.bottom + 24)


# ------------------------------------------------------------------------------------------- slots
SYMBOLS = ("CHERRY", "MAGNEMITE", "SHELLDER", "PIKACHU", "PSYDUCK", "RED7", "BLUE7", "REPLAY")
# How many of each on a reel (21 stops): the 7s are rare.
STRIP = {"CHERRY": 4, "MAGNEMITE": 4, "SHELLDER": 4, "PIKACHU": 3, "PSYDUCK": 3, "RED7": 1, "BLUE7": 1, "REPLAY": 1}
SEVENS = {"RED7", "BLUE7"}
# (row of the left, middle, right reel) for each pay line, by how many coins are bet
LINES = {1: [(1, 1, 1)], 2: [(1, 1, 1), (0, 0, 0), (2, 2, 2)], 3: [(1, 1, 1), (0, 0, 0), (2, 2, 2), (0, 1, 2), (2, 1, 0)]}


def line_pay(a, b, c):
    """Coins one pay line wins (the machine's table), or "REPLAY"."""
    if a == b == c:
        if a in SEVENS:
            return 300
        return {"PIKACHU": 15, "PSYDUCK": 15, "MAGNEMITE": 8, "SHELLDER": 8, "CHERRY": 4, "REPLAY": "REPLAY"}[a]
    if {a, b, c} <= SEVENS:
        return 90
    if a == b == "CHERRY":
        return 4
    if a == "CHERRY":
        return 2
    return 0


class SlotsState(_Machine):
    REEL_X = (64, 144, 224)
    REEL_Y = 112
    SYM_H = 48

    def __init__(self, game, previous_state, background=None, rng=None):
        super().__init__(game, previous_state, background)
        self.rng = rng or random.Random()
        self.bg = self.S(pic(game, "slots", "bg.png"))
        sheet = pic(game, "slots", "images.png")
        self.sym = {s: self.S(f) for s, f in zip(SYMBOLS, frames(sheet, 8))}
        self.button = self.S(pic(game, "slots", "button.png"))
        self.led = {k: [self.S(f) for f in frames(pic(game, "slots", f"{k}.png"), n)]
                    for k, n in (("insert", 2), ("press", 2), ("stop", 4), ("win", 4), ("lose", 2))}
        self.bonus = [self.S(f) for f in frames(pic(game, "slots", "bonus.png"), 2)]
        self.digits = [self.S(f) for f in frames(pic(game, "slots", "numbers.png"), 10)]
        self.line_pics = {k: self.S(pic(game, "slots", f"{k}.png")) for k in ("line1", "line2", "line3a", "line3b")}
        self.strips = []
        for _ in range(3):
            strip = [s for s, n in STRIP.items() for _ in range(n)]
            self.rng.shuffle(strip)
            self.strips.append(strip)
        self.pos = [float(self.rng.randrange(21)) for _ in range(3)]
        self.spinning = [False, False, False]
        self.bet = 0
        self.payout = 0
        self.paying = 0
        self.led_kind = "insert"
        self.led_time = 0
        self.spin_time = 0
        self.free = False
        self.won_lines = []
        f = game.assets.fonts
        x, w = game.width - self.ox + 16, self.ox - 32
        self.btn_bet = [CommandButton((x, 96 + i * 76, w, 64), f"BET {i + 1}", f["button"], (lambda n=i + 1: self.place_bet(n)),
                                      bg_color=theme.BAG, autosize=False) for i in range(3)]
        self.btn_start = CommandButton((x, 340, w, 90), "START", f["button"], self.spin, bg_color=theme.POKEMON,
                                       autosize=False)
        self.buttons += self.btn_bet + [self.btn_start]

    # ---- play
    def place_bet(self, n):
        if any(self.spinning) or self.paying:
            return
        if self.free:
            return
        if coins(self.story) + self.bet < n:
            self.led_kind = "insert"
            return
        add_coins(self.story, self.bet - n)  # change the bet: the old one comes back first
        self.bet = n
        self.led_kind = "press"

    def spin(self):
        if any(self.spinning) or self.paying:
            return
        if not self.bet and not self.free:
            if coins(self.story) < 1:
                return
            self.place_bet(min(3, coins(self.story)))
        self.spinning = [True, True, True]
        self.spin_time = 0
        self.won_lines = []
        self.payout = 0
        self.led_kind = "stop"

    def stop_reel(self, i):
        if 0 <= i < 3 and self.spinning[i]:
            self.spinning[i] = False
            self.pos[i] = float(int(self.pos[i]) % 21)  # click into place on a symbol
            if not any(self.spinning):
                self._settle()

    def _row(self, reel, row):
        return self.strips[reel][(int(self.pos[reel]) + row) % 21]

    def _settle(self):
        bet = self.bet
        self.free = False
        total = 0
        for idx, (ra, rb, rc) in enumerate(LINES.get(bet, [])):
            pay = line_pay(self._row(0, ra), self._row(1, rb), self._row(2, rc))
            if pay == "REPLAY":
                self.free = True
                self.won_lines.append(idx)
            elif pay:
                total += pay
                self.won_lines.append(idx)
        self.payout = total
        self.paying = total
        if not self.free:
            self.bet = 0
        self.led_kind = "win" if total or self.free else "lose"
        self.led_time = 0

    # ---- frame
    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    n = e.key - pygame.K_1
                    if any(self.spinning):
                        self.stop_reel(n)
                    else:
                        self.place_bet(n + 1)
                elif e.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if any(self.spinning):
                        self.stop_reel(self.spinning.index(True))
                    else:
                        self.spin()
                elif e.key == pygame.K_ESCAPE:
                    self.leave()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for i in range(3):  # the round STOP buttons under the reels
                    cx, cy = self.at(self.REEL_X[i] + 32, 287)
                    if (e.pos[0] - cx) ** 2 + (e.pos[1] - cy) ** 2 < (30 * self.k) ** 2:
                        self.stop_reel(i)
                reels = pygame.Rect(*self.at(64, 112), int(224 * self.k), int(144 * self.k))
                if reels.collidepoint(e.pos) and any(self.spinning):
                    self.stop_reel(self.spinning.index(True))

    def update(self):
        self.led_time += 1
        if any(self.spinning):
            self.spin_time += 1
            for i in range(3):
                if self.spinning[i]:
                    self.pos[i] = (self.pos[i] + 0.55) % 21
            if self.spin_time > FPS * 6:  # nobody pressing: they stop by themselves
                self.stop_reel(self.spinning.index(True))
        elif self.paying:  # count the win into the Coin Case
            step = max(1, self.paying // 20)
            n = min(step, self.paying)
            add_coins(self.story, n)
            self.paying -= n

    def draw(self):
        screen = self.game.screen
        self.draw_frame(screen)
        screen.blit(self.bg, (self.ox, 0))
        k = self.k
        for i in range(3):  # the reels: three symbols showing, scrolling down while they spin
            window = pygame.Rect(*self.at(self.REEL_X[i], self.REEL_Y), int(64 * k), int(144 * k))
            screen.set_clip(window)
            pygame.draw.rect(screen, (250, 250, 250), window)
            frac = self.pos[i] - int(self.pos[i])
            for row in range(-1, 4):
                sym = self.strips[i][(int(self.pos[i]) + row) % 21]
                y = window.y + int((row - frac) * self.SYM_H * k)
                screen.blit(self.sym[sym], (window.x, y))
            screen.set_clip(None)
        for idx in range(len(LINES.get(self.bet or (3 if self.free else 0), []))):  # the lit pay lines
            if idx in self.won_lines and (self.led_time // 6) % 2:
                continue
            name, xy = (("line1", (2, 169)), ("line2", (2, 121)), ("line2", (2, 215)), ("line3a", (2, 82)),
                        ("line3b", (2, 82)))[idx]
            screen.blit(self.line_pics[name], self.at(*xy))
        for i in range(3):
            if self.spinning[i]:
                screen.blit(self.button, self.at(self.REEL_X[i] + 4, 259))
        led = self.led.get(self.led_kind) or []
        if led:
            screen.blit(led[(self.led_time // 6) % len(led)], self.at(359, 96))
        if self.won_lines and self.payout >= 90:
            screen.blit(self.bonus[1 if self.payout >= 300 else 0], self.at(359, 96))
        self._digits(screen, coins(self.story), 362, 66)
        self._digits(screen, self.payout, 438, 66)
        f = self.game.assets.fonts
        hint = "Free spin!" if self.free else ("Bet, then START" if not any(self.spinning) else "STOP each reel!")
        self.side_text(screen, hint, self.game.width - self.ox // 2, 460)
        theme.shadow_text(screen, f"Bet: {self.bet}", f["label"], self.game.width - self.ox // 2, 74,
                          color=(255, 255, 255), shadow=(20, 20, 30), align="center")
        self.draw_coins(screen, "Keys: 1 2 3 bet or stop a reel, Space: start / stop")
        self.game.ui_manager.draw(screen)

    def _digits(self, screen, n, x, y):
        s = str(max(0, min(99999, int(n)))).rjust(5)
        for i, ch in enumerate(s):
            if ch != " " and self.digits:
                screen.blit(self.digits[int(ch)], self.at(x + i * 14, y))


# ---------------------------------------------------------------------------------- Voltorb Flip
# HeartGold/SoulSilver's boards: (2s, 3s, Voltorb) for each level, one picked at random.
LEVELS = {
    1: [(3, 1, 6), (0, 3, 6), (5, 0, 6), (2, 2, 6), (4, 1, 6)],
    2: [(1, 3, 7), (6, 0, 7), (3, 2, 7), (0, 4, 7), (5, 1, 7)],
    3: [(2, 3, 8), (7, 0, 8), (4, 2, 8), (1, 4, 8), (6, 1, 8)],
    4: [(3, 3, 8), (0, 5, 8), (8, 0, 10), (5, 2, 10), (2, 4, 10)],
    5: [(7, 1, 10), (4, 3, 10), (1, 5, 10), (9, 0, 10), (6, 2, 10)],
    6: [(3, 4, 10), (0, 6, 10), (8, 1, 10), (5, 3, 10), (2, 5, 10)],
    7: [(7, 2, 10), (4, 4, 10), (1, 6, 13), (9, 1, 13), (6, 3, 10)],
    8: [(0, 7, 10), (8, 2, 10), (5, 4, 10), (2, 6, 10), (7, 3, 10)],
}
LEVEL_FLAG = "voltorb_flip_level"


def deal(level, rng):
    """A 5 x 5 board: 0 is a Voltorb, else the tile's points."""
    twos, threes, bombs = rng.choice(LEVELS[level])
    tiles = [2] * twos + [3] * threes + [0] * bombs
    tiles += [1] * (25 - len(tiles))
    rng.shuffle(tiles)
    return [tiles[r * 5:(r + 1) * 5] for r in range(5)]


class VoltorbFlipState(_Machine):
    TILE = 64

    def __init__(self, game, previous_state, background=None, rng=None):
        super().__init__(game, previous_state, background)
        self.rng = rng or random.Random()
        self.board_img = self.S(pic(game, "voltorb", "board.png"))
        self.tiles = [self.S(f) for f in frames(pic(game, "voltorb", "tiles.png"), 15)]
        self.small = [self.S(f) for f in frames(pic(game, "voltorb", "numbers_small.png"), 10)]
        self.boom = [self.S(f) for f in frames(pic(game, "voltorb", "explosion.png"), 6)]
        self.cursor = [self.S(f) for f in frames(pic(game, "voltorb", "cursor.png"), 2)]
        self.level = max(1, min(8, int(self.story.story_flags.get(LEVEL_FLAG, 1) or 1)))
        f = game.assets.fonts
        x, w = game.width - self.ox + 16, self.ox - 32
        self.btn_memo = CommandButton((x, 96, w, 70), "MEMO", f["button"], self.toggle_memo, bg_color=theme.BAG,
                                      autosize=False)
        self.btn_quit = CommandButton((x, 186, w, 70), "QUIT", f["button"], self.quit_round, bg_color=theme.FIGHT,
                                      autosize=False)
        self.buttons += [self.btn_memo, self.btn_quit]
        self.memo_mode = False
        self.message = ""
        self.new_round()

    def new_round(self):
        self.board = deal(self.level, self.rng)
        self.shown = [[False] * 5 for _ in range(5)]
        self.memo = [[None] * 5 for _ in range(5)]
        self.round_coins = 0
        self.flipping = {}   # (c, r) -> frames of the flip so far
        self.exploding = None
        self.over = None     # "WIN" / "BOOM" while the round's result shows
        self.over_time = 0
        self.cur = [0, 0]
        self.flips = 0
        self.message = f"Level {self.level}. Flip the tiles!"

    def toggle_memo(self):
        self.memo_mode = not self.memo_mode
        self.btn_memo.text = "FLIP" if self.memo_mode else "MEMO"

    def quit_round(self):
        """Keep the coins found so far and leave the board (it's the next one when you come back)."""
        if self.over:
            return
        if self.round_coins:
            add_coins(self.story, self.round_coins)
        self.leave()

    def tile_rect(self, c, r):
        x, y = self.at(128 + c * self.TILE, r * self.TILE)
        return pygame.Rect(x, y, int(self.TILE * self.k), int(self.TILE * self.k))

    def _sums(self):
        rows = [(sum(v for v in self.board[r]), sum(1 for v in self.board[r] if v == 0)) for r in range(5)]
        cols = [(sum(self.board[r][c] for r in range(5)), sum(1 for r in range(5) if self.board[r][c] == 0))
                for c in range(5)]
        return rows, cols

    def flip(self, c, r):
        if self.over or self.shown[r][c] or (c, r) in self.flipping:
            return
        if self.memo_mode:  # memo: Voltorb, 1, 2, 3, then nothing
            order = [None, 0, 1, 2, 3]
            self.memo[r][c] = order[(order.index(self.memo[r][c]) + 1) % len(order)]
            return
        self.flipping[(c, r)] = 0

    def _revealed(self, c, r):
        self.shown[r][c] = True
        if self.over:  # a tile still turning when the round ended: it just shows
            return
        v = self.board[r][c]
        self.flips += 1
        if v == 0:
            self.exploding = (c, r, 0)
            self.over, self.over_time = "BOOM", 0
            lost = self.round_coins
            self.round_coins = 0
            drop = max(1, min(self.level, self.flips - 1))
            self.message = "Oh no! A Voltorb! " + (f"You lost {lost} coins. " if lost else "") + \
                (f"Down to level {drop}." if drop < self.level else "")
            self.level = drop
        else:
            self.round_coins = v if not self.round_coins else min(MAX_COINS, self.round_coins * v)
            left = sum(1 for rr in range(5) for cc in range(5) if self.board[rr][cc] > 1 and not self.shown[rr][cc])
            if not left:
                add_coins(self.story, self.round_coins)
                self.message = f"Level {self.level} cleared! You got {self.round_coins} coins!"
                self.level = min(8, self.level + 1)
                self.over, self.over_time = "WIN", 0
        self.story.story_flags[LEVEL_FLAG] = self.level

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.over and self.over_time > FPS:
                    self.new_round()
                    continue
                for r in range(5):
                    for c in range(5):
                        if self.tile_rect(c, r).collidepoint(e.pos):
                            self.cur = [c, r]
                            self.flip(c, r)
                memo_box = pygame.Rect(*self.at(8, 210), int(112 * self.k), int(100 * self.k))
                if memo_box.collidepoint(e.pos):
                    self.toggle_memo()
            elif e.type == pygame.KEYDOWN:
                if self.over and self.over_time > FPS and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.new_round()
                    continue
                d = {pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0), pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1)}.get(e.key)
                if d:
                    self.cur = [(self.cur[0] + d[0]) % 5, (self.cur[1] + d[1]) % 5]
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.flip(*self.cur)
                elif e.key == pygame.K_m:
                    self.toggle_memo()
                elif e.key == pygame.K_ESCAPE:
                    self.quit_round()

    def update(self):
        for key in list(self.flipping):
            self.flipping[key] += 1
            if self.flipping[key] >= 8:
                del self.flipping[key]
                self._revealed(*key)
        if self.exploding:
            c, r, t = self.exploding
            self.exploding = (c, r, t + 1) if t < 6 * 3 else None
        if self.over:
            self.over_time += 1
            if self.over == "BOOM" and self.over_time == FPS:  # show the whole board
                self.shown = [[True] * 5 for _ in range(5)]

    def draw(self):
        screen = self.game.screen
        self.draw_frame(screen)
        screen.blit(self.board_img, (self.ox, 0))
        rows, cols = self._sums()
        for r in range(5):  # the hints: points (two digits) and Voltorb (one), on each row's and column's panel
            self._hint(screen, 448, r * 64, *rows[r])
        for c in range(5):
            self._hint(screen, 128 + c * 64, 320, *cols[c])
        for r in range(5):
            for c in range(5):
                rect = self.tile_rect(c, r)
                v = self.board[r][c]
                if (c, r) in self.flipping:  # the flip: face-down, edge-on, then the face
                    t = self.flipping[(c, r)]
                    frame = (14, 5, 6, 7 + v, 7 + v, v, v, v)[min(t, 7)]
                    screen.blit(self.tiles[frame], rect)
                elif self.shown[r][c]:
                    screen.blit(self.tiles[v], rect)
                else:
                    screen.blit(self.tiles[14], rect)
                    m = self.memo[r][c]
                    if m == 0:
                        screen.blit(self.tiles[4], rect)
                    elif m:
                        d = self.small[m]
                        screen.blit(d, d.get_rect(center=rect.center))
        if self.exploding:
            c, r, t = self.exploding
            img = self.boom[min(5, t // 3)]
            screen.blit(img, img.get_rect(center=self.tile_rect(c, r).center))
        if not self.over:
            cur = self.cursor[1 if self.memo_mode else 0]
            screen.blit(cur, self.tile_rect(*self.cur).topleft)
        f = self.game.assets.fonts
        box = pygame.Rect(*self.at(10, 10), int(108 * self.k), int(100 * self.k))
        theme.shadow_text(screen, f"Lv. {self.level}", f["label"], box.centerx, box.y + 20, align="center")
        theme.shadow_text(screen, "This round", f["caption"], box.centerx, box.y + 62, align="center")
        theme.shadow_text(screen, str(self.round_coins), f["button"], box.centerx, box.y + 110, align="center")
        if self.memo_mode:
            theme.shadow_text(screen, "MEMO ON: tap a tile to mark it", f["caption"], self.game.width // 2,
                              self.game.height - 20, color=(255, 230, 120), shadow=(20, 20, 30), align="center")
        if self.message:
            self.side_text(screen, self.message, self.game.width - self.ox // 2, 290)
        if self.over and self.over_time > FPS:
            theme.shadow_text(screen, "Tap for the next board", f["label"], self.game.width // 2,
                              self.game.height // 2, color=(255, 255, 255), shadow=(20, 20, 30), align="center")
        self.draw_coins(screen, "Keys: arrows move, Enter flips, M: memo")
        self.game.ui_manager.draw(screen)

    def _hint(self, screen, x, y, points, bombs):
        tens, ones = divmod(points, 10)
        for i, dgt in enumerate((tens, ones)):
            screen.blit(self.small[dgt], self.at(x + 30 + i * 16, y + 8))
        screen.blit(self.small[bombs], self.at(x + 46, y + 38))


# ------------------------------------------------------------------------------- the Prize Counter
# Each Game Corner's prizes (FireRed/LeafGreen's Celadon; HeartGold/SoulSilver's Goldenrod...):
# ("POKEMON", species id, coins) or ("ITEM", item key, coins).
PRIZES = {
    "CELADON_CITY": [("POKEMON", 63, 180), ("POKEMON", 35, 500), ("POKEMON", 147, 2800), ("POKEMON", 123, 5500),
                     ("ITEM", "RARE_CANDY", 500), ("ITEM", "NUGGET", 1000), ("ITEM", "EXP_SHARE", 2000)],
    "GOLDENROD_CITY": [("POKEMON", 63, 200), ("POKEMON", 23, 700), ("POKEMON", 147, 2100),
                       ("ITEM", "EVERSTONE", 300), ("ITEM", "RARE_CANDY", 500), ("ITEM", "AMULET_COIN", 2000)],
    "MAUVILLE_CITY": [("ITEM", "RARE_CANDY", 500), ("ITEM", "NUGGET", 1000), ("ITEM", "METAL_COAT", 1500),
                      ("ITEM", "KINGS_ROCK", 1500), ("ITEM", "EXP_SHARE", 2000)],
    "VEILSTONE_CITY": [("POKEMON", 133, 1000), ("ITEM", "RARE_CANDY", 500), ("ITEM", "HARD_STONE", 800),
                       ("ITEM", "AMULET_COIN", 2000)],
}
DEFAULT_PRIZES = PRIZES["CELADON_CITY"]


def prizes_here(story):
    return PRIZES.get(story.current_area_key, DEFAULT_PRIZES)


class PrizeCounterState(GameState):
    def __init__(self, game, previous_state, background=None):
        super().__init__(game)
        self.previous_state = previous_state
        self.story = game.story_manager
        self.bg = background
        self.list = prizes_here(self.story)
        self.message = "What prize would you like?"
        f = game.assets.fonts
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.leave, bg_color=theme.BACK,
                                      autosize=False)
        self.cards = []
        cols = 4
        w, h = 280, 200
        x0 = (game.width - (cols * w + (cols - 1) * 20)) // 2
        for i, prize in enumerate(self.list):
            r, c = divmod(i, cols)
            self.cards.append((pygame.Rect(x0 + c * (w + 20), 110 + r * (h + 20), w, h), prize))

    def leave(self):
        self.game.change_state(self.previous_state)

    def _name(self, prize):
        kind, what, _ = prize
        if kind == "POKEMON":
            from src.minigames.base import species_name
            return species_name(self.game, what)
        return str(what).replace("_", " ").title()

    def _image(self, prize):
        kind, what, _ = prize
        if kind == "POKEMON":
            from src.minigames.base import icon
            return icon(self.game, what, 110)
        from src.minigames.base import item
        return item(self.game, str(what).lower().replace("_", "-"), 80)

    def buy(self, prize):
        kind, what, cost = prize
        if coins(self.story) < cost:
            self.message = f"You need {cost:,} coins for {self._name(prize)}."
            return
        add_coins(self.story, -cost)
        if kind == "POKEMON":
            from src.world import story_events
            story_events.gift_pokemon(self.game, what)
            self.message = f"You got {self._name(prize)}!"
        else:
            self.story.add_item(what, 1)
            self.message = f"You got a {self._name(prize)}!"

    def start(self):
        self.game.ui_manager.elements.clear()
        self.game.ui_manager.add_element(self.btn_back)

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for rect, prize in self.cards:
                    if rect.collidepoint(e.pos):
                        self.buy(prize)

    def update(self):
        pass

    def draw(self):
        screen = self.game.screen
        theme.menu_background(screen, (196, 70, 140), "PRIZE COUNTER", self.game.assets.fonts["button"], title_x=176)
        f = self.game.assets.fonts
        Utils.draw_text_outline(screen, f"{coins(self.story):,} coins", f["button"], (255, 255, 255),
                                self.game.width - 24, theme.HEADER_H // 2 - 4, align="right")
        mouse = pygame.mouse.get_pos()
        for rect, prize in self.cards:
            theme.card(screen, rect, hover=rect.collidepoint(mouse), accent=(196, 70, 140))
            img = self._image(prize)
            screen.blit(img, img.get_rect(center=(rect.centerx, rect.y + 70)))
            theme.shadow_text(screen, self._name(prize), f["label"], rect.centerx, rect.y + 140, align="center")
            theme.shadow_text(screen, f"{prize[2]:,} coins", f["caption"], rect.centerx, rect.y + 176,
                              color=(176, 60, 120), align="center")
        bar = pygame.Rect(16, self.game.height - 86, self.game.width - 32, 78)
        theme.draw_textbox(screen, bar)
        theme.shadow_text(screen, self.message, f["s_med"], bar.x + 32, bar.centery - f["s_med"].get_height() // 2)
        self.game.ui_manager.draw(screen)


# ------------------------------------------------------------------------------------------ Blackjack
RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
SUITS = ("spade", "heart", "diamond", "club")


def hand_total(cards):
    """The best total of a hand (an Ace counts 11 unless that goes over 21) and whether it's soft."""
    total = sum(10 if r in ("J", "Q", "K", "10") else 1 if r == "A" else int(r) for r, _ in cards)
    aces = sum(1 for r, _ in cards if r == "A")
    if aces and total + 10 <= 21:
        return total + 10, True
    return total, False


def blackjack(cards):
    return len(cards) == 2 and hand_total(cards)[0] == 21


def _suit(screen, suit, center, size, color):
    """A suit sign drawn from shapes (the pixel font has none)."""
    x, y = center
    s = size
    if suit == "diamond":
        pygame.draw.polygon(screen, color, [(x, y - s), (x + s * 0.7, y), (x, y + s), (x - s * 0.7, y)])
    elif suit == "heart":
        pygame.draw.circle(screen, color, (int(x - s * 0.45), int(y - s * 0.25)), int(s * 0.5))
        pygame.draw.circle(screen, color, (int(x + s * 0.45), int(y - s * 0.25)), int(s * 0.5))
        pygame.draw.polygon(screen, color, [(x - s * 0.92, y - s * 0.05), (x + s * 0.92, y - s * 0.05), (x, y + s)])
    elif suit == "spade":
        pygame.draw.circle(screen, color, (int(x - s * 0.45), int(y + s * 0.15)), int(s * 0.5))
        pygame.draw.circle(screen, color, (int(x + s * 0.45), int(y + s * 0.15)), int(s * 0.5))
        pygame.draw.polygon(screen, color, [(x - s * 0.92, y + s * 0.05), (x + s * 0.92, y + s * 0.05), (x, y - s)])
        pygame.draw.polygon(screen, color, [(x, y + s * 0.2), (x - s * 0.35, y + s), (x + s * 0.35, y + s)])
    else:  # club
        r = int(s * 0.42)
        for dx, dy in ((0, -0.45), (-0.5, 0.15), (0.5, 0.15)):
            pygame.draw.circle(screen, color, (int(x + dx * s), int(y + dy * s)), r)
        pygame.draw.polygon(screen, color, [(x, y), (x - s * 0.35, y + s), (x + s * 0.35, y + s)])


class BlackjackState(GameState):
    """Blackjack for coins: get closer to 21 than the dealer without going over. Blackjack (an Ace and
    a 10 or face card) pays 3 to 2; a win pays 1 to 1; a tie gives the bet back. The dealer draws to
    17. DOUBLE: double the bet for exactly one more card."""
    CARD = (120, 168)
    BETS = (1, 5, 10, 25)
    DEALER = 52  # Meowth (Pay Day!)

    def __init__(self, game, previous_state, background=None, rng=None):
        super().__init__(game)
        self.previous_state = previous_state
        self.story = game.story_manager
        self.rng = rng or random.Random()
        self.bg = None
        if background is not None:
            self.bg = pygame.transform.smoothscale(background, (game.width, game.height))
        self.shoe = []
        self.bet = 0
        self.doubled = False
        self.player, self.dealer = [], []
        self.phase = "BET"   # BET -> DEALING -> PLAY -> DEALER -> DONE
        self.hide = True     # the dealer's second card face down
        self.queue = []      # cards still to deal ("P" / "D"), a few frames apart
        self.wait = 0
        self.message = "Place a bet, then DEAL."
        f = game.assets.fonts
        y = game.height - 96
        self.btn_exit = CommandButton((16, 14, 140, 56), "EXIT", f["button"], self.leave, bg_color=theme.BACK,
                                      autosize=False)
        self.bet_buttons = [CommandButton((24 + i * 150, y, 136, 70), f"+{b}", f["button"],
                                          (lambda b=b: self.add_bet(b)), bg_color=theme.BAG, autosize=False)
                            for i, b in enumerate(self.BETS)]
        self.btn_clear = CommandButton((24 + 4 * 150, y, 150, 70), "CLEAR", f["button"], self.clear_bet,
                                       bg_color=theme.BACK, autosize=False)
        self.btn_deal = CommandButton((game.width - 240, y, 216, 70), "DEAL", f["button"], self.deal,
                                      bg_color=theme.POKEMON, autosize=False)
        self.btn_hit = CommandButton((game.width - 720, y, 216, 70), "HIT", f["button"], self.hit,
                                     bg_color=theme.POKEMON, autosize=False)
        self.btn_stand = CommandButton((game.width - 480, y, 216, 70), "STAND", f["button"], self.stand,
                                       bg_color=theme.FIGHT, autosize=False)
        self.btn_double = CommandButton((game.width - 240, y, 216, 70), "DOUBLE", f["button"], self.double,
                                        bg_color=theme.MEGA, autosize=False)

    # ---- the cards
    def _draw_card(self):
        if len(self.shoe) < 15:  # a fresh shuffled deck when it runs low
            self.shoe = [(r, s) for r in RANKS for s in SUITS]
            self.rng.shuffle(self.shoe)
        return self.shoe.pop()

    def add_bet(self, n):
        if self.phase not in ("BET", "DONE"):
            return
        if self.phase == "DONE":
            self._new_hand()
        n = min(n, coins(self.story))
        if n <= 0:
            self.message = "You're out of coins! Buy more at the counter."
            return
        add_coins(self.story, -n)
        self.bet += n
        self.message = f"Bet: {self.bet} coins. DEAL when you're ready."

    def clear_bet(self):
        if self.phase == "BET" and self.bet:
            add_coins(self.story, self.bet)
            self.bet = 0
            self.message = "Place a bet, then DEAL."

    def _new_hand(self):
        self.player, self.dealer = [], []
        self.bet = 0
        self.doubled = False
        self.phase = "BET"
        self.hide = True

    def deal(self):
        if self.phase == "DONE":
            self._new_hand()
        if self.phase != "BET":
            return
        if not self.bet:
            if not coins(self.story):
                self.message = "You're out of coins! Buy more at the counter."
                return
            self.add_bet(1)
        self.phase = "DEALING"
        self.queue = ["P", "D", "P", "D"]
        self.message = "Dealing..."

    def hit(self):
        if self.phase == "PLAY" and not self.queue:
            self.queue = ["P"]

    def stand(self):
        if self.phase == "PLAY" and not self.queue:
            self.phase = "DEALER"
            self.hide = False

    def double(self):
        if self.phase == "PLAY" and not self.queue and len(self.player) == 2 and coins(self.story) >= self.bet:
            add_coins(self.story, -self.bet)
            self.bet *= 2
            self.doubled = True
            self.queue = ["P"]

    def _after_player_card(self):
        total = hand_total(self.player)[0]
        if total > 21:
            self._finish("BUST")
        elif total == 21 or self.doubled:
            self.stand()

    def _finish(self, how):
        self.hide = False
        p, d = hand_total(self.player)[0], hand_total(self.dealer)[0]
        bet, pay = self.bet, 0
        if how == "BUST":
            self.message = f"Bust! {p} is over 21. You lose {bet} coins."
        elif blackjack(self.player) and not blackjack(self.dealer):
            pay = bet + bet * 3 // 2
            self.message = f"Blackjack! You win {pay - bet} coins!"
        elif blackjack(self.dealer) and not blackjack(self.player):
            self.message = f"The dealer has Blackjack. You lose {bet} coins."
        elif d > 21:
            pay = bet * 2
            self.message = f"The dealer busts with {d}! You win {bet} coins!"
        elif p > d:
            pay = bet * 2
            self.message = f"{p} beats {d}! You win {bet} coins!"
        elif p == d:
            pay = bet
            self.message = f"Both {p}: a tie. Your bet comes back."
        else:
            self.message = f"{d} beats {p}. You lose {bet} coins."
        add_coins(self.story, pay)
        self.bet = 0
        self.doubled = False
        self.phase = "DONE"

    # ---- frame
    def leave(self):
        if self.phase == "BET" and self.bet:
            self.clear_bet()
        if self.phase in ("BET", "DONE"):
            self.game.change_state(self.previous_state)

    def _buttons(self):
        if self.phase in ("BET", "DONE"):
            return [self.btn_exit, *self.bet_buttons, self.btn_clear, self.btn_deal]
        if self.phase == "PLAY":
            return [self.btn_exit, self.btn_hit, self.btn_stand, self.btn_double]
        return [self.btn_exit]

    def start(self):
        self.game.transitioning = False
        self._shown = None
        self._sync_buttons()

    def _sync_buttons(self):
        want = self._buttons()
        if getattr(self, "_shown", None) != want:
            self.game.ui_manager.elements.clear()
            for b in want:
                self.game.ui_manager.add_element(b)
            self._shown = want

    def handle_events(self, events):
        for e in events:
            if e.type != pygame.KEYDOWN:
                continue
            if e.key == pygame.K_h:
                self.hit()
            elif e.key == pygame.K_s:
                self.stand()
            elif e.key == pygame.K_d:
                self.double()
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.deal()
            elif e.key in (pygame.K_UP, pygame.K_EQUALS, pygame.K_PLUS):
                self.add_bet(1)
            elif e.key == pygame.K_ESCAPE:
                self.leave()

    def update(self):
        if self.wait:
            self.wait -= 1
        elif self.queue:
            who = self.queue.pop(0)
            (self.player if who == "P" else self.dealer).append(self._draw_card())
            self.wait = FPS // 3
            if not self.queue:
                if self.phase == "DEALING":
                    if blackjack(self.player) or blackjack(self.dealer):
                        self._finish("NATURAL")
                    else:
                        self.phase = "PLAY"
                        self.message = "HIT for another card, or STAND."
                elif self.phase == "PLAY":
                    self._after_player_card()
        elif self.phase == "DEALER":  # the dealer draws to 17
            if hand_total(self.dealer)[0] < 17:
                self.queue = ["D"]
            else:
                self._finish("STAND")
        self._sync_buttons()

    def _card(self, screen, card, x, y, face=True):
        r = pygame.Rect(x, y, *self.CARD)
        pygame.draw.rect(screen, (20, 30, 20), r.move(4, 6), border_radius=12)
        if not face:
            from src.minigames.board import _ball_back
            _ball_back(screen, r)
            return
        pygame.draw.rect(screen, (250, 250, 246), r, border_radius=12)
        pygame.draw.rect(screen, (60, 60, 70), r, 3, border_radius=12)
        rank, suit = card
        color = (210, 40, 40) if suit in ("heart", "diamond") else (30, 30, 40)
        f = self.game.assets.fonts
        theme.shadow_text(screen, rank, f["button"], r.x + 14, r.y + 8, color=color, shadow=(230, 230, 230))
        _suit(screen, suit, (r.x + 28, r.y + 62), 12, color)
        _suit(screen, suit, (r.centerx + 8, r.centery + 20), 30, color)

    def draw(self):
        screen = self.game.screen
        if self.bg:
            screen.blit(self.bg, (0, 0))
        else:
            screen.fill((24, 20, 36))
        table = pygame.Rect(40, 80, self.game.width - 80, self.game.height - 200)
        pygame.draw.rect(screen, (20, 70, 40), table.move(0, 8), border_radius=40)
        pygame.draw.rect(screen, (32, 120, 66), table, border_radius=40)
        pygame.draw.rect(screen, (196, 150, 60), table, 8, border_radius=40)
        f = self.game.assets.fonts
        from src.minigames.base import icon
        meowth = icon(self.game, self.DEALER, 110)
        screen.blit(meowth, (table.x + 40, table.y + 20))
        theme.shadow_text(screen, "Dealer", f["label"], table.x + 95, table.y + 140, color=(255, 255, 255),
                          shadow=(20, 50, 30), align="center")
        for i, rule in enumerate(("Blackjack pays 3 to 2", "Dealer draws to 17")):
            theme.shadow_text(screen, rule, f["caption"], table.x + 120, table.y + 178 + i * 30, color=(230, 210, 140),
                              shadow=(20, 50, 30), align="center")
        for hand, y, hide in ((self.dealer, table.y + 24, self.hide),
                              (self.player, table.bottom - self.CARD[1] - 24, False)):
            x0 = table.centerx - (len(hand) * 70 + 50) // 2
            for i, card in enumerate(hand):
                self._card(screen, card, x0 + i * 70, y, face=not (hide and i == 1))
        if self.dealer:
            shown = self.dealer[:1] if self.hide else self.dealer
            more = " + ?" if self.hide and len(self.dealer) > 1 else ""
            theme.shadow_text(screen, f"{hand_total(shown)[0]}{more}", f["big"], table.right - 140, table.y + 70,
                              color=(255, 255, 255), shadow=(20, 50, 30), align="center")
        if self.player:
            total, soft = hand_total(self.player)
            theme.shadow_text(screen, str(total), f["big"], table.right - 140, table.bottom - 110,
                              color=(255, 255, 255), shadow=(20, 50, 30), align="center")
            if soft and total < 21:
                theme.shadow_text(screen, "(an Ace as 11)", f["caption"], table.right - 140, table.bottom - 60,
                                  color=(230, 230, 200), shadow=(20, 50, 30), align="center")
        tw = f["dialog"].size(self.message)[0]
        box = pygame.Rect(0, 0, min(table.w - 40, tw + 70), 54)
        box.center = (table.centerx, table.y + 24 + self.CARD[1] + (table.h - 48 - 2 * self.CARD[1]) // 2)
        theme.draw_textbox(screen, box)
        theme.shadow_text(screen, self.message, f["dialog"], box.centerx, box.centery, align="center")
        Utils.draw_text_outline(screen, f"{coins(self.story):,} coins   Bet: {self.bet}", f["button"],
                                (255, 255, 255), self.game.width - 24, 40, align="right")
        self.game.ui_manager.draw(screen)
