"""Fly's little scene (Jordan, 11-08): Pikachu on its balloons carries you off, you dangling from a rope, one of three ways,
before the trip. In co-op everyone hangs on, and every device sees it. A tap skips it."""
import math
import os
import random

import pygame

from src.coop import world
from src.minigames.pikafly import frames as pikachu_frames
from src.states.base import GameState

LENGTH = {"takeoff": 62, "sky": 84, "mountains": 84}
ROPE, ROPE_COLOR = 62, (122, 84, 46)


def _players(game):
    """Who's dangling: the host, then whoever's connected."""
    out = [getattr(game, "player_character", "") or "red"]
    host = getattr(game, "coop_host", None)
    if host is not None:
        out += [g.get("char") or "female" for g in host.guests.values() if g["cid"] is not None]
    return out


def carrier(game):
    """Who carries you (Jordan 11-17, game-wide): if you have ever caught a Pikachu (any region, even one in the PC: the
    Pokedex's caught record), Pikachu's balloons (this scene's own: None); else the party Pokemon that knows Fly (else your
    lead) carries you on the rope."""
    story = getattr(game, "story_manager", None)
    if caught_pikachu(game):
        return None
    team = [m for m in (getattr(story, "player_team", None) or []) if getattr(m, "id", 0)]
    if not team:
        return None
    return next((m for m in team if "FLY" in (getattr(m, "moves", None) or [])), None) or team[0]


def caught_pikachu(game):
    """Has a Pikachu (any form: Pinkan, a cap...) ever been caught: the Pokedex's caught record, every region's."""
    try:
        dex = game.data.data.get("pokedex", {}) or {}
    except AttributeError:
        return False
    return any(isinstance(v, dict) and (str(v.get("id")) == "25" or "PIKACHU" in str(v.get("name", "")).upper())
               for v in dex.values())


def carrier_frames(game):
    """The carrier's following-Pokemon sheet (assets/dungeon/followers), its four steps facing right, doubled; None for
    Pikachu's balloons."""
    mon = carrier(game)
    if mon is None:
        return None
    try:
        from src.states.overworld.dungeon import follower_names
        base = os.path.join(game.assets.assets_dir, "dungeon", "followers")
        path = next((p for p in (os.path.join(base, f"{n}.png") for n in follower_names(game, mon)) if os.path.isfile(p)), None)
        if not path:
            return None
        sheet = pygame.image.load(path).convert_alpha()
        s = sheet.get_width() // 4
        return [pygame.transform.scale(sheet.subsurface((i * s, 2 * s, s, s)), (s * 2, s * 2)) for i in range(4)]
    except (pygame.error, OSError, ValueError, TypeError, ImportError):
        return None


class FlyScene(GameState):
    def __init__(self, game, go, style=None, riders=None, pump=None):
        super().__init__(game)
        self.go, self.t, self.done, self.pump = go, 0, False, pump
        self.style = style if style in LENGTH else random.choice(tuple(LENGTH))
        self.riders = riders or _players(game)
        self.snapshot = game.screen.copy()
        self.frames = carrier_frames(game) or pikachu_frames(game, "pikachu")
        self.bg = None
        if self.style != "takeoff":
            name = "background.png" if self.style == "sky" else "mountain_bg.png"
            raw = pygame.image.load(os.path.join(game.assets.assets_dir, "fly", name)).convert()
            k = game.height / raw.get_height()
            self.bg = pygame.transform.scale(raw, (int(raw.get_width() * k), game.height))
        host = getattr(game, "coop_host", None)
        if host is not None:  # (everyone sees it: the same one)
            for pid in list(host.guests):
                host.send(pid, {"t": "event", "fly": {"style": self.style, "riders": self.riders}})

    def finish(self):
        if not self.done:
            self.done = True
            self.go()

    def handle_events(self, events):
        if any(e.type == pygame.MOUSEBUTTONDOWN or e.type == pygame.KEYDOWN for e in events):
            self.finish()

    def update(self):
        if self.pump is not None and not self.pump():
            return
        self.t += 1
        if self.t >= LENGTH[self.style]:
            self.finish()

    def _carry(self, screen, cx, cy):
        """Pikachu up top; a rope down from it; everyone hanging on, swinging."""
        pika = self.frames[(self.t // 3) % 4]
        x, y = cx, cy + 44
        for i, char in enumerate(self.riders):
            swing = math.sin(self.t / 7 + i * 0.8)
            end = (int(x + swing * 26), y + ROPE)
            pygame.draw.line(screen, ROPE_COLOR, (int(x), y), end, 5)
            pygame.draw.line(screen, (182, 136, 84), (int(x) - 1, y), (end[0] - 1, end[1]), 2)
            person = world.person_img(self.game, char, (1, 0))
            if person is not None:
                tilted = pygame.transform.rotate(person, -swing * 16)
                screen.blit(tilted, tilted.get_rect(midtop=(end[0], end[1] - 6)))
                x, y = end[0], end[1] + person.get_height() - 14
            else:
                x, y = end
        screen.blit(pika, pika.get_rect(center=(cx, cy)))

    def _scroll(self, screen, speed):
        x = (self.t * speed) % self.bg.get_width()
        screen.blit(self.bg, (-x, 0))
        if self.bg.get_width() - x < self.game.width:
            screen.blit(self.bg, (self.bg.get_width() - x, 0))

    def draw(self):
        screen, W, H = self.game.screen, self.game.width, self.game.height
        k = self.t / LENGTH[self.style]
        if self.style == "takeoff":  # the place you were drops away as you're hauled up
            screen.fill((88, 152, 240))
            screen.blit(self.snapshot, (0, int(H * k * k * 1.1)))
            self._carry(screen, W // 2, int(H * 0.42 - H * 0.42 * k))
            if k > 0.75:
                veil = pygame.Surface((W, H))
                veil.fill((255, 255, 255))
                veil.set_alpha(int(255 * (k - 0.75) / 0.25))
                screen.blit(veil, (0, 0))
            return
        self._scroll(screen, 18 if self.style == "sky" else 14)
        bob = int(14 * math.sin(self.t / 6))
        across = int(-160 + (W + 320) * k)
        self._carry(screen, across, int(H * (0.2 if self.style == "sky" else 0.3 - 0.14 * k)) + bob)
