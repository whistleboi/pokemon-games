"""The Gym challenge minigames' shared frame (Jordan, 11-01).

A Gym's challenge comes in place of its trainers: one minigame, picked at random (src/minigames/
__init__.py), with a goal to reach. Every game here is a Minigame: the Gym's own background, a bar
along the top with the game's name, the goal and a progress bar, a card to start, and a card at the
end (WON: on to the Leader; LOST: TRY AGAIN, the same game, or LEAVE). Each game only sets itself up,
steps, draws its play area and takes taps and keys. Touch first: every game plays with taps alone;
keys (arrows, space) work too.

Pictures: the Pokemon are party icons (assets/sprites/icons/<dex>.png, two frames, from Pokemon
Journeys: dev/builders/import_party_icons.py); berries and balls are the Bag's item pictures.
"""
import os
import random

import pygame

from src.states.base import GameState
from src.ui import theme
from src.ui.dialogue import wrap_text
from src.config import FPS

HUD_H = 96
# Each game's pixel-art backdrop (src/minigames/scenes.py), for the ones played over their background
# (Jordan, 11-06: those were a dark screen). The others fill their own play area.
SCENES = {"catch": "meadow", "dash": "plains", "koga": "dojo", "match": "night",
          "pong": "stadium", "quiz": "volcano", "rhythm": "stage", "sabrina": "cosmos", "surge": "power",
          "typeclash": "arena", "voltorb": "power"}
_icons = {}
_items = {}


def icon_frames(game, pid, size=96):
    """The two frames of Pokemon pid's party icon at size x size (crisp), or its front sprite."""
    key = (pid, size)
    if key not in _icons:
        path = os.path.join(game.assets.assets_dir or "", "sprites", "icons", f"{int(pid)}.png")
        frames = []
        try:
            sheet = pygame.image.load(path).convert_alpha()
            h = sheet.get_height()
            raw = [sheet.subsurface((i * h, 0, h, h)) for i in range(max(1, sheet.get_width() // h))]
            # cropped to the Pokemon (the same square for every frame, so it still bobs)
            box = raw[0].get_bounding_rect().unionall([f.get_bounding_rect() for f in raw[1:]])
            side = max(box.w, box.h) + 2
            square = pygame.Rect(0, 0, side, side)
            square.center = box.center
            square = square.clamp(raw[0].get_rect()) if side <= h else raw[0].get_rect()
            for frame in raw:
                frames.append(pygame.transform.scale(frame.subsurface(square), (size, size)))
        except (pygame.error, FileNotFoundError, ValueError):
            img = game.assets.get_pokemon_image(pid, "normal", False)
            frames = [pygame.transform.smoothscale(img, (size, size))] if img else []
        if not frames:
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(surf, (200, 200, 210), (size // 2, size // 2), size // 3)
            frames = [surf]
        _icons[key] = frames
    return _icons[key]


def icon(game, pid, size=96, flip=False):
    """Pokemon pid's party icon, on its current bobbing frame."""
    frames = icon_frames(game, pid, size)
    img = frames[(pygame.time.get_ticks() // 260) % len(frames)]
    return pygame.transform.flip(img, True, False) if flip else img


# Form words at the end of a species' data name ("basculin-red-striped", "wishiwashi-solo"): dropped.
FORM_WORDS = {"red", "blue", "white", "striped", "solo", "school", "two", "three", "segment", "male", "female",
              "midday", "midnight", "dusk", "disguised", "amped", "incarnate", "altered", "land", "normal",
              "ordinary", "aria", "average", "baile", "meteor", "plant", "standard", "shield", "full", "belly",
              "single", "strike", "family", "of", "four", "zero", "curly", "green", "plumage"}


def species_name(game, pid):
    """A species' name for a game's title ("Basculin", "Mr Mime")."""
    words = str((game.assets.movesets or {}).get(str(pid), {}).get("name", "Pokemon")).lower().split("-")
    while len(words) > 1 and words[-1] in FORM_WORDS:
        words.pop()
    name = "-".join(words)
    special = {"mr-mime": "Mr. Mime", "mime-jr": "Mime Jr.", "mr-rime": "Mr. Rime", "type-null": "Type: Null"}
    return special.get(name) or "-".join(w.capitalize() for w in words)  # Ho-Oh, Porygon-Z, Kommo-O


def local(game, candidates, n=1):
    """The region's own Pokemon for a part in a game (Jordan, 11-01: Hoenn's flyer is Taillow, not
    Pidgey): the candidates native to the region first (its own Pokedex numbers), then ones in its
    Pokedex, then any of its generation. candidates: species ids, in order of preference."""
    from src.world.league_redo import GEN_CAP
    story = game.story_manager
    region = str(story.get_current_region() or "KANTO").upper()
    cfg = story.get_region_start(region)
    lo, hi = (cfg.get("dex_range") or [0, -1])[:2]
    extra = set(cfg.get("dex_extra") or [])
    native = [c for c in candidates if lo <= c <= hi]
    inside = [c for c in candidates if c in extra and c not in native]
    rest = [c for c in candidates if c <= GEN_CAP.get(region, 1025) and c not in native and c not in inside]
    return (native + inside + rest)[:n] or list(candidates[:n])


def item(game, name, size=48):
    """An item's Bag picture ("poke-ball", "pecha-berry") at size x size, or a coloured dot."""
    key = (name, size)
    if key not in _items:
        path = os.path.join(game.assets.items_sprites_dir or "", f"{name}.png")
        try:
            img = pygame.image.load(path).convert_alpha()
            img = img.subsurface(img.get_bounding_rect()) if img.get_bounding_rect().w else img
            _items[key] = pygame.transform.scale(img, (size, size))
        except (pygame.error, FileNotFoundError):
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(surf, (220, 60, 60), (size // 2, size // 2), size // 2 - 2)
            _items[key] = surf
    return _items[key]


class Minigame(GameState):
    key = "minigame"
    title = "Gym Challenge"
    how = ""          # how to play, on the start card
    controls = ()     # (what you press, what it does), on the start card: tap first, then keys
    accent = (66, 130, 220)
    in_pool = True    # picked at random for any Gym (False: only where a Gym asks for it by name)
    win_line = "Challenge complete! The Gym Leader is waiting."

    @classmethod
    def title_for(cls, game):
        """The game's name where it's played ("Taillow Flight" in Hoenn)."""
        return cls.title

    def __init__(self, game, on_done, level=0, background=None, leader=None, team=None, partner=None, seed=None):
        """level: 0-7, the region's badges so far (each game gets a little harder).
        leader: the Gym Leader's data; team: species ids to theme the game with (the Leader's);
        partner: the player's lead Pokemon (species id)."""
        super().__init__(game)
        self.on_done = on_done
        self.level = max(0, min(7, int(level or 0)))
        self.leader = leader or {}
        self.team = [int(p) for p in (team or self.leader.get("team") or [25])]
        self.partner = int(partner or 25)
        self.leader_name = str(self.leader.get("name") or "The Leader").split("(")[0].strip()
        self.rng = random.Random(seed)
        self.W, self.H = game.width, game.height
        self.area = pygame.Rect(0, HUD_H, self.W, self.H - HUD_H)
        self.bg = None
        self.backdrop = None        # its pixel-art scene, alive (SCENES)
        self.anim = 0               # frames shown (the scene moves on the cards too)
        self.scene_scroll = 0.0     # how far a runner has run: its scenery scrolls past
        if SCENES.get(self.key):
            from src.minigames.scenes import Scene
            self.backdrop = Scene(SCENES[self.key], self.W, self.H, seed=self.key)
        elif background is not None:
            self.bg = pygame.transform.smoothscale(background, (self.W, self.H))
            shade = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            shade.fill((10, 14, 30, 150))
            self.bg.blit(shade, (0, 0))
        self.fonts = game.assets.fonts
        self.title = self.title_for(game)
        self.phase = "INTRO"
        self.message = ""
        self.frames = 0
        self.buttons = []
        self.reset()
        self._cards()

    # ---- for each game
    def setup(self):
        """Set up a new round (also on TRY AGAIN)."""

    def target(self):
        return 10

    def goal_text(self):
        return f"Reach {self.target()}"

    def step(self):
        """One frame of play (FPS a second)."""

    def render(self, screen):
        """Draw the play area (self.area)."""

    def on_tap(self, pos):
        pass

    def on_release(self, pos):
        pass

    def on_motion(self, pos):
        pass

    def on_key(self, key):
        pass

    def progress(self):
        return self.score, self.target()

    # ---- the frame
    def reset(self):
        self.score = 0
        self.frames = 0
        self.setup()

    def seconds(self):
        return self.frames / FPS

    def win(self):
        if self.phase == "PLAY":
            self.phase = "WON"
            self.message = self.win_line
            self._cards()

    def lose(self, why):
        if self.phase == "PLAY":
            self.phase = "LOST"
            self.message = why
            self._cards()

    def check_goal(self):
        cur, goal = self.progress()
        if cur >= goal:
            self.win()

    def _play(self):
        self.reset()
        self.phase = "PLAY"
        self.buttons = []

    def _cards(self):
        """The buttons on the start / end card."""
        cx, y = self.W // 2, int(self.H * 0.62)
        if self.phase == "INTRO":  # the controls must be read: GOT IT! (or Enter) starts the game
            self.buttons = [(pygame.Rect(cx - 150, int(self.H * 0.78), 300, 76), "GOT IT!", theme.POKEMON, self._play)]
        elif self.phase == "WON":
            self.buttons = [(pygame.Rect(cx - 150, y, 300, 76), "CONTINUE", theme.POKEMON,
                             lambda: self.on_done(True))]
        elif self.phase == "LOST":
            self.buttons = [(pygame.Rect(cx - 320, y, 300, 76), "TRY AGAIN", theme.POKEMON, self._play),
                            (pygame.Rect(cx + 20, y, 300, 76), "LEAVE", theme.BACK, lambda: self.on_done(False))]

    def start(self):
        self.game.transitioning = False
        self.game.ui_manager.elements.clear()

    def _leave_rect(self):
        return pygame.Rect(self.W // 2 - 20, 20, 150, HUD_H - 40)

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and self.phase == "PLAY":
                self.on_done(False)  # leave mid-game: come back to the same one
                return
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.phase == "PLAY"                     and self._leave_rect().collidepoint(e.pos):
                self.on_done(False)
                return
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.phase != "PLAY":
                    for rect, _label, _color, fn in self.buttons:
                        if rect.collidepoint(e.pos):
                            fn()
                            return
                else:
                    self.on_tap(e.pos)
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and self.phase == "PLAY":
                self.on_release(e.pos)
            elif e.type == pygame.MOUSEMOTION and self.phase == "PLAY":
                self.on_motion(e.pos)
            elif e.type == pygame.KEYDOWN:
                if self.phase == "PLAY":
                    self.on_key(e.key)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER) and self.buttons:
                    self.buttons[0][3]()
                    return

    def scene_speed(self):
        """How fast its scenery scrolls (screen pixels a frame): a runner's own speed."""
        if self.key == "dash":
            return self._speed()
        return 0

    def update(self):
        self.anim += 1
        if self.phase == "PLAY":
            self.frames += 1
            self.scene_scroll += self.scene_speed()
            self.step()

    def draw(self):
        screen = self.game.screen
        if self.backdrop:
            self.backdrop.draw(screen, self.anim, self.scene_scroll)
        elif self.bg:
            screen.blit(self.bg, (0, 0))
        else:
            screen.fill(theme.MENU_BG)
        if self.phase == "PLAY" or self.phase in ("WON", "LOST"):
            self.render(screen)
        self._draw_hud(screen)
        if self.phase != "PLAY":
            self._draw_card(screen)

    def _draw_hud(self, screen):
        bar = pygame.Rect(12, 8, self.W - 24, HUD_H - 16)
        theme.draw_textbox(screen, bar)
        f = self.fonts
        theme.shadow_text(screen, self.title, f["button"], bar.x + 24, bar.centery - f["button"].get_height() // 2)
        cur, goal = self.progress()
        goal_line = self.goal_text()
        gx = bar.right - 470
        theme.shadow_text(screen, goal_line, f["label"], gx, bar.y + 10)
        track = pygame.Rect(gx, bar.bottom - 30, 330, 16)
        pygame.draw.rect(screen, (210, 214, 226), track, border_radius=8)
        k = 0 if not goal else max(0.0, min(1.0, cur / goal))
        if k > 0:
            pygame.draw.rect(screen, self.accent, (track.x, track.y, max(16, int(track.w * k)), track.h), border_radius=8)
        pygame.draw.rect(screen, theme.TEXTBOX_FRAME, track, 2, border_radius=8)
        theme.shadow_text(screen, f"{int(cur)} / {goal}", f["label"], bar.right - 24, track.centery - 12, align="right")
        if self.phase == "PLAY":
            r = self._leave_rect()
            theme.command_button(screen, r, "LEAVE", f["label"], theme.BACK, hover=r.collidepoint(pygame.mouse.get_pos()))

    def _draw_controls(self, screen):
        """The start card: the goal, how to play, and the controls (tap, and keys)."""
        f = self.fonts
        card = pygame.Rect(0, 0, min(1060, self.W - 60), int(self.H * 0.74))
        card.center = (self.W // 2, int(self.H * 0.5))
        theme.draw_textbox(screen, card)
        theme.shadow_text(screen, self.title, f["big"], card.centerx, card.y + 50, align="center")
        screen.blit(icon(self.game, self.partner, 84, flip=True), (card.x + 24, card.y + 10))
        screen.blit(icon(self.game, self.team[-1], 84), (card.right - 108, card.y + 10))
        y = card.y + 100
        theme.shadow_text(screen, "GOAL: " + self.goal_text(), f["label"], card.centerx, y, color=(176, 60, 40),
                          align="center")
        y += 40
        for row in wrap_text(self.how, f["dialog"], card.w - 100):
            theme.shadow_text(screen, row, f["dialog"], card.centerx, y, align="center")
            y += f["dialog"].get_linesize()
        y += 12
        theme.shadow_text(screen, "CONTROLS", f["label"], card.x + 60, y)
        y += 38
        for key, does in self.controls:
            chip = pygame.Rect(card.x + 60, y, 300, 40)
            pygame.draw.rect(screen, theme.TEXTBOX_FRAME, chip, border_radius=10)
            theme.shadow_text(screen, key, f["caption"], chip.centerx, chip.centery, color=(255, 255, 255),
                              shadow=theme.shade(theme.TEXTBOX_FRAME, 0.5), align="center")
            theme.shadow_text(screen, does, f["caption"], chip.right + 24, chip.centery - f["caption"].get_height() // 2)
            y += 48
        mouse = pygame.mouse.get_pos()
        for rect, label, color, _fn in self.buttons:
            theme.command_button(screen, rect, label, f["button"], color, hover=rect.collidepoint(mouse))

    def _draw_card(self, screen):
        shade = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 120))
        screen.blit(shade, (0, 0))
        if self.phase == "INTRO":
            self._draw_controls(screen)
            return
        card = pygame.Rect(0, 0, min(1000, self.W - 80), int(self.H * 0.52))
        card.center = (self.W // 2, int(self.H * 0.52))
        theme.draw_textbox(screen, card)
        f = self.fonts
        if self.phase == "INTRO":
            head, lines = self.title, [self.goal_text() + "!", self.how]
        elif self.phase == "WON":
            head, lines = "You did it!", [self.message]
        else:
            head, lines = "Not this time...", [self.message, "Try again: it's the same challenge."]
        theme.shadow_text(screen, head, f["big"], card.centerx, card.y + 54, align="center")
        y = card.y + 108
        for line in lines:
            if not line:
                continue
            for row in wrap_text(line, f["dialog"], card.w - 120):
                theme.shadow_text(screen, row, f["dialog"], card.centerx, y, align="center")
                y += f["dialog"].get_linesize()
        # the Pokemon to play with, in the card's corner
        if self.team:  # the Leader's ace and your partner, either side of the heading
            screen.blit(icon(self.game, self.partner, 84, flip=True), (card.x + 24, card.y + 14))
            screen.blit(icon(self.game, self.team[-1], 84), (card.right - 108, card.y + 14))
        mouse = pygame.mouse.get_pos()
        for rect, label, color, _fn in self.buttons:
            theme.command_button(screen, rect, label, f["button"], color, hover=rect.collidepoint(mouse))
