"""Gym challenge minigames on a board (Jordan, 11-01). Each plays by taps alone.

- EkansTrail: steer Ekans to the berries; it grows with each one. Don't hit the wall or yourself.
- PokemonMatch: flip cards to find the pairs of Pokemon, before the turns run out.
- VoltorbField: uncover the safe tiles; a number tells how many Voltorb hide next to it.
- TypeClash: Fire, Water or Grass against the Leader (Water beats Fire, Fire beats Grass, Grass
  beats Water). First to 3 wins.
"""
import pygame

from src.minigames.base import Minigame, icon, item, local, species_name
from src.minigames.arcade import HAZARDS
from src.ui import theme
from src.config import FPS

GRASS_A, GRASS_B = (104, 176, 88), (96, 166, 80)
SNAKES = (23, 206, 336, 551, 843, 982, 95)  # Ekans, Dunsparce, Seviper, Sandile, Silicobra, Dudunsparce, Onix


def _ball_back(screen, rect):
    """A face-down card: the Poke Ball."""
    pygame.draw.rect(screen, (230, 70, 60), rect, border_radius=12)
    lower = pygame.Rect(rect.x, rect.centery, rect.w, rect.h - rect.h // 2)
    pygame.draw.rect(screen, (244, 244, 248), lower, border_bottom_left_radius=12, border_bottom_right_radius=12)
    pygame.draw.line(screen, (40, 40, 50), (rect.x, rect.centery), (rect.right, rect.centery), 6)
    r = min(rect.w, rect.h) // 6
    pygame.draw.circle(screen, (40, 40, 50), rect.center, r + 5)
    pygame.draw.circle(screen, (250, 250, 250), rect.center, r)
    pygame.draw.rect(screen, (40, 40, 50), rect, 4, border_radius=12)


class EkansTrail(Minigame):
    key = "snake"
    title = "Ekans Trail"
    how = "Steer to the berries. Each one makes you longer. Don't bump into the wall or your own tail!"
    controls = (("Tap", "Turn toward where you tap"), ("Arrow keys / WASD", "Turn"))
    accent = (150, 70, 210)

    @classmethod
    def title_for(cls, game):
        return f"{species_name(game, local(game, SNAKES)[0])} Trail"

    def target(self):
        return 8 + self.level

    def goal_text(self):
        return f"Eat {self.target()} berries"

    def setup(self):
        self.cell = 52
        self.species = local(self.game, SNAKES)[0]
        self.cols = (self.W - 40) // self.cell
        self.rows = (self.area.h - 30) // self.cell
        self.ox = (self.W - self.cols * self.cell) // 2
        self.oy = self.area.top + (self.area.h - self.rows * self.cell) // 2
        mid = (self.cols // 3, self.rows // 2)
        self.body = [mid, (mid[0] - 1, mid[1]), (mid[0] - 2, mid[1])]
        self.dir = (1, 0)
        self.queued = None
        self.tick = 0
        self.every = max(3, 6 - self.level // 3)  # frames a step
        self._place_berry()

    def _place_berry(self):
        free = [(c, r) for c in range(self.cols) for r in range(self.rows) if (c, r) not in self.body]
        self.berry = self.rng.choice(free) if free else None
        self.berry_kind = self.rng.choice(("cheri-berry", "pecha-berry", "razz-berry", "bluk-berry"))

    def _turn(self, d):
        if (d[0] + self.dir[0], d[1] + self.dir[1]) != (0, 0):  # no turning back on itself
            self.queued = d

    def on_tap(self, pos):
        hx, hy = self.body[0]
        cx, cy = self.ox + hx * self.cell + self.cell // 2, self.oy + hy * self.cell + self.cell // 2
        dx, dy = pos[0] - cx, pos[1] - cy
        self._turn((1 if dx > 0 else -1, 0) if abs(dx) > abs(dy) else (0, 1 if dy > 0 else -1))

    def on_key(self, key):
        d = {pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1), pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0),
             pygame.K_w: (0, -1), pygame.K_s: (0, 1), pygame.K_a: (-1, 0), pygame.K_d: (1, 0)}.get(key)
        if d:
            self._turn(d)

    def step(self):
        self.tick += 1
        if self.tick < self.every:
            return
        self.tick = 0
        if self.queued:
            self.dir, self.queued = self.queued, None
        hx, hy = self.body[0]
        head = (hx + self.dir[0], hy + self.dir[1])
        if not (0 <= head[0] < self.cols and 0 <= head[1] < self.rows):
            self.lose(f"{species_name(self.game, self.species)} bumped into the wall!")
            return
        if head in self.body[:-1]:
            self.lose(f"{species_name(self.game, self.species)} got tangled up in its own tail!")
            return
        self.body.insert(0, head)
        if head == self.berry:
            self.score += 1
            self.check_goal()
            self._place_berry()
        else:
            self.body.pop()

    def render(self, screen):
        board = pygame.Rect(self.ox, self.oy, self.cols * self.cell, self.rows * self.cell)
        pygame.draw.rect(screen, (60, 92, 52), board.inflate(12, 12), border_radius=10)
        for c in range(self.cols):
            for r in range(self.rows):
                pygame.draw.rect(screen, GRASS_A if (c + r) % 2 else GRASS_B,
                                 (self.ox + c * self.cell, self.oy + r * self.cell, self.cell, self.cell))
        if self.berry:
            img = item(self.game, self.berry_kind, self.cell - 6)
            screen.blit(img, img.get_rect(center=(self.ox + self.berry[0] * self.cell + self.cell // 2,
                                                   self.oy + self.berry[1] * self.cell + self.cell // 2)))
        for i, (c, r) in enumerate(reversed(self.body[1:])):  # the purple body with its yellow bands
            center = (self.ox + c * self.cell + self.cell // 2, self.oy + r * self.cell + self.cell // 2)
            pygame.draw.circle(screen, (86, 40, 120), center, self.cell // 2 - 2)
            pygame.draw.circle(screen, (150, 90, 196), center, self.cell // 2 - 6)
            if i % 3 == 0:
                pygame.draw.circle(screen, (236, 200, 70), center, self.cell // 5)
        hx, hy = self.body[0]
        img = icon(self.game, self.species, self.cell + 24, flip=self.dir[0] > 0)
        screen.blit(img, img.get_rect(center=(self.ox + hx * self.cell + self.cell // 2,
                                               self.oy + hy * self.cell + self.cell // 2)))


class PokemonMatch(Minigame):
    key = "match"
    title = "Pokemon Match"
    how = "Turn over two cards at a time. Find every pair of matching Pokemon before you run out of turns!"
    controls = (("Tap a card", "Turn it over"),)
    accent = (204, 146, 36)

    def target(self):
        return self.pairs

    def goal_text(self):
        return f"Find all {self.pairs} pairs"

    def setup(self):
        self.pairs = 6 if self.level < 4 else 8
        self.cols = 4
        self.rows = self.pairs * 2 // self.cols
        from src.world import league_redo
        story = self.game.story_manager
        region = story.get_current_region()
        dex = [p for p in league_redo._region_dex(story, region) if p <= league_redo.GEN_CAP.get(region, 1025)]
        pool = list(dict.fromkeys(self.team))  # the Leader's team, then the region's own Pokemon
        while len(pool) < self.pairs:
            pid = self.rng.choice(dex or list(range(1, 152)))
            if pid not in pool:
                pool.append(pid)
        faces = self.rng.sample(pool, self.pairs) * 2
        self.rng.shuffle(faces)
        self.cards = [{"pid": p, "up": False, "done": False} for p in faces]
        self.open = []
        self.wait = 0
        self.turns = self.pairs * 2 + 6 - self.level // 2
        self.used = 0

    def _rect(self, i):
        c, r = i % self.cols, i // self.cols
        h = min(150, (self.area.h - 60) // self.rows - 14)
        w = int(h * 0.82)
        x0 = (self.W - (self.cols * (w + 16) - 16)) // 2
        y0 = self.area.top + 20 + (self.area.h - 40 - self.rows * (h + 14)) // 2
        return pygame.Rect(x0 + c * (w + 16), y0 + r * (h + 14), w, h)

    def on_tap(self, pos):
        if self.wait or len(self.open) >= 2:
            return
        for i, card in enumerate(self.cards):
            if not card["up"] and not card["done"] and self._rect(i).collidepoint(pos):
                card["up"] = True
                self.open.append(i)
                if len(self.open) == 2:
                    self.used += 1
                    a, b = (self.cards[j] for j in self.open)
                    if a["pid"] == b["pid"]:
                        a["done"] = b["done"] = True
                        self.open = []
                        self.score += 1
                        self.check_goal()
                    else:
                        self.wait = int(FPS * 0.8)
                return

    def step(self):
        if self.wait:
            self.wait -= 1
            if self.wait == 0:
                for j in self.open:
                    self.cards[j]["up"] = False
                self.open = []
                if self.used >= self.turns and self.phase == "PLAY":
                    self.lose("Out of turns!")

    def render(self, screen):
        for i, card in enumerate(self.cards):
            r = self._rect(i)
            if card["up"] or card["done"]:
                theme.card(screen, r, selected=card["done"], accent=self.accent)
                img = icon(self.game, card["pid"], min(r.w, r.h) - 20)
                screen.blit(img, img.get_rect(center=r.center))
            else:
                _ball_back(screen, r)
        f = self.game.assets.fonts["label"]
        theme.shadow_text(screen, f"Turns left: {max(0, self.turns - self.used)}", f, 24, self.area.top + 16,
                          color=(255, 255, 255), shadow=(20, 20, 30))


class VoltorbField(Minigame):
    key = "voltorb"
    title = "Voltorb Field"
    how = "Uncover the tiles. A number tells how many hidden Pokemon are next to it. Uncover every safe tile!"
    controls = (("Tap a tile", "Uncover it"), ("First tap", "Always safe"))
    accent = (216, 176, 32)

    @classmethod
    def title_for(cls, game):
        return f"{species_name(game, local(game, HAZARDS)[0])} Field"

    def target(self):
        return self.safe

    def goal_text(self):
        return "Uncover every safe tile"

    def setup(self):
        self.cols, self.rows = 9, 6
        self.hazard = local(self.game, HAZARDS)[0]
        self.mines = 7 + self.level // 2
        self.safe = self.cols * self.rows - self.mines
        self.board = None  # placed on the first tap (it's always safe)
        self.shown = set()
        self.boom = None

    def _cell(self):
        return min((self.W - 80) // self.cols, (self.area.h - 50) // self.rows)

    def _rect(self, c, r):
        s = self._cell()
        x0 = (self.W - self.cols * s) // 2
        y0 = self.area.top + (self.area.h - self.rows * s) // 2
        return pygame.Rect(x0 + c * s + 3, y0 + r * s + 3, s - 6, s - 6)

    def _near(self, c, r):
        return [(c + dc, r + dr) for dc in (-1, 0, 1) for dr in (-1, 0, 1)
                if (dc or dr) and 0 <= c + dc < self.cols and 0 <= r + dr < self.rows]

    def _place(self, c, r):
        keep_clear = {(c, r), *self._near(c, r)}
        spots = [(x, y) for x in range(self.cols) for y in range(self.rows) if (x, y) not in keep_clear]
        self.board = set(self.rng.sample(spots, self.mines))

    def _count(self, c, r):
        return sum(1 for n in self._near(c, r) if n in self.board)

    def _reveal(self, c, r):
        todo = [(c, r)]
        while todo:
            cell = todo.pop()
            if cell in self.shown or cell in self.board:
                continue
            self.shown.add(cell)
            if self._count(*cell) == 0:
                todo.extend(self._near(*cell))

    def on_tap(self, pos):
        for c in range(self.cols):
            for r in range(self.rows):
                if self._rect(c, r).collidepoint(pos):
                    if self.board is None:
                        self._place(c, r)
                    if (c, r) in self.board:
                        self.boom = (c, r)
                        self.lose(f"A {species_name(self.game, self.hazard)} jumped out!")
                        return
                    self._reveal(c, r)
                    self.score = len(self.shown)
                    self.check_goal()
                    return

    COLORS = {1: (52, 96, 200), 2: (40, 140, 60), 3: (200, 60, 50), 4: (110, 50, 160)}

    def render(self, screen):
        f = self.game.assets.fonts["button"]
        for c in range(self.cols):
            for r in range(self.rows):
                rect = self._rect(c, r)
                if (c, r) in self.shown:
                    pygame.draw.rect(screen, (226, 214, 184), rect, border_radius=8)
                    pygame.draw.rect(screen, (170, 150, 116), rect, 2, border_radius=8)
                    n = self._count(c, r)
                    if n:
                        theme.shadow_text(screen, str(n), f, rect.centerx, rect.centery,
                                          color=self.COLORS.get(n, (40, 40, 40)), align="center")
                elif self.phase == "LOST" and self.board and (c, r) in self.board:
                    pygame.draw.rect(screen, (240, 200, 120) if (c, r) == self.boom else (200, 200, 210), rect,
                                     border_radius=8)
                    img = icon(self.game, self.hazard, rect.w)
                    screen.blit(img, img.get_rect(center=rect.center))
                else:
                    pygame.draw.rect(screen, (60, 120, 54), rect.move(0, 4), border_radius=8)
                    pygame.draw.rect(screen, GRASS_A, rect, border_radius=8)
                    for k in range(3):  # tufts of grass
                        x = rect.x + rect.w * (k + 1) // 4
                        pygame.draw.line(screen, (70, 140, 60), (x, rect.centery + 8), (x - 6, rect.centery - 6), 3)
                        pygame.draw.line(screen, (70, 140, 60), (x, rect.centery + 8), (x + 6, rect.centery - 6), 3)


class TypeClash(Minigame):
    key = "typeclash"
    title = "Type Clash"
    how = "Pick Fire, Water or Grass. Water beats Fire, Fire beats Grass, Grass beats Water. First to 3 wins!"
    controls = (("Tap a type", "Choose it"), ("1 / 2 / 3", "Fire / Water / Grass"))
    accent = (226, 84, 56)
    TYPES = ("FIRE", "WATER", "GRASS")
    BEATS = {"WATER": "FIRE", "FIRE": "GRASS", "GRASS": "WATER"}
    COLORS = {"FIRE": (226, 84, 56), "WATER": (66, 130, 220), "GRASS": (82, 178, 86)}
    WINS = 3

    def target(self):
        return self.WINS

    def goal_text(self):
        return f"Win {self.WINS} rounds"

    def setup(self):
        # This region's three first partners, by type (a region without a set: Kanto's).
        story = self.game.story_manager
        starters = story.get_region_start(story.get_current_region()).get("starters") or []
        ms = self.game.assets.movesets or {}
        self.species = {"GRASS": 1, "FIRE": 4, "WATER": 7}
        typed = {t: next((p for p in starters if t in (ms.get(str(p), {}).get("types") or [])), None) for t in self.TYPES}
        if all(typed.values()):
            self.species = typed
        self.theirs = 0
        self.mine = None
        self.leader_pick = None
        self.last_leader = self.rng.choice(self.TYPES)
        self.show = 0
        self.line = "Choose your type!"

    def _buttons(self):
        w, h = 300, 150
        x0 = (self.W - (3 * w + 2 * 30)) // 2
        y = self.area.bottom - h - 30
        return [(pygame.Rect(x0 + i * (w + 30), y, w, h), t) for i, t in enumerate(self.TYPES)]

    def _pick(self, t):
        if self.show:
            return
        # The Leader's habit: often the same type again (watch for it!), else any.
        pick = self.last_leader if self.rng.random() < 0.45 else self.rng.choice(self.TYPES)
        self.mine, self.leader_pick, self.last_leader = t, pick, pick
        if t == pick:
            self.line = f"Both chose {t.title()}! It's a tie."
        elif self.BEATS[t] == pick:
            self.score += 1
            self.line = f"{t.title()} beats {pick.title()}! You win the round!"
        else:
            self.theirs += 1
            self.line = f"{pick.title()} beats {t.title()}! {self.leader_name} wins the round."
        self.show = int(FPS * 1.4)

    def on_tap(self, pos):
        for rect, t in self._buttons():
            if rect.collidepoint(pos):
                self._pick(t)

    def on_key(self, key):
        t = {pygame.K_1: "FIRE", pygame.K_2: "WATER", pygame.K_3: "GRASS"}.get(key)
        if t:
            self._pick(t)

    def step(self):
        if self.show:
            self.show -= 1
            if self.show == 0:
                if self.score >= self.WINS:
                    self.win()
                elif self.theirs >= self.WINS:
                    self.lose(f"{self.leader_name} won the Type Clash!")
                else:
                    self.mine = self.leader_pick = None
                    self.line = "Choose your type!"

    def render(self, screen):
        f = self.game.assets.fonts
        mid = self.area.top + 150
        for x, who, pick, wins in ((self.W * 0.3, "You", self.mine, self.score),
                                   (self.W * 0.7, self.leader_name, self.leader_pick, self.theirs)):
            panel = pygame.Rect(0, 0, 300, 230)
            panel.center = (x, mid)
            theme.draw_textbox(screen, panel)
            theme.shadow_text(screen, f"{who}: {wins}", f["label"], panel.centerx, panel.y + 22, align="center")
            if pick:
                img = icon(self.game, self.species[pick], 150)
                screen.blit(img, img.get_rect(center=(panel.centerx, panel.centery + 12)))
                theme.shadow_text(screen, pick.title(), f["label"], panel.centerx, panel.bottom - 26,
                                  color=self.COLORS[pick], align="center")
            else:
                theme.shadow_text(screen, "?", f["big"], panel.centerx, panel.centery + 10, align="center")
        theme.shadow_text(screen, self.line, f["dialog"], self.W // 2, mid + 150, color=(255, 255, 255),
                          shadow=(20, 20, 30), align="center")
        mouse = pygame.mouse.get_pos()
        for rect, t in self._buttons():
            theme.command_button(screen, rect, "", f["button"], self.COLORS[t], hover=rect.collidepoint(mouse))
            img = icon(self.game, self.species[t], 96)
            screen.blit(img, img.get_rect(midtop=(rect.centerx, rect.y + 6)))
            from src.utils import Utils
            Utils.draw_text_outline(screen, t, f["button"], (255, 255, 255), rect.centerx, rect.bottom - 30,
                                    outline_color=theme.shade(self.COLORS[t], 0.5), thickness=3)
