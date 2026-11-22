"""A new game's opening talk (11-19, Jordan: "Instead of the professor asking, they know the character's names. this would play
out after the player selects their name but before they enter the overworld for the first time.")

After the name, region, rival and math level are picked, the region's professor (as its game opens: FireRed's Oak,
HeartGold/SoulSilver's Oak, Emerald/ORAS's Birch, Platinum's Rowan, Orange 5.7's Ivy; Orre, whose games have no
professor, a narrator) talks to you by name: a Pokemon of the region, then you, then your rival by the name you gave them,
and you shrink away into the world, as FireRed's opening ends. Every line is ours.
Animated (Jordan 11-19: "animated scenes that can be clicked through, instead of still images"): it fades up, people slide
in and out between lines and breathe, the professor throws a Poke Ball and the Pokemon pops out with its cry, the words type
out (a tap finishes the line, the next moves on).
Pictures: assets/sprites/intro/<name>.png (Essentials fan games' intro art: Journeys' Oak, Banished Platinum's Rowan and
Barry), else a trainer picture; the Pokemon is the game's own front sprite. Tap or Enter: the next line."""
import math
import os

import pygame

from src.states.base import GameState
from src.ui import theme

# region -> (professor picture or None, the region's Pokemon, its colours, [(who, line)]); who: prof / mon / player / rival / out
INTROS = {
    "KANTO": ("oak", 32, ((236, 240, 250), (176, 196, 232)), [
        ("prof", "Ah, {player}! Right on time. I'm Professor Oak. I study Pokémon here in Kanto."),
        ("mon", "Pokémon live all over this region: in the grass, in the sea, in the caves... even in the cities."),
        ("mon", "Some people keep them as pets. Others battle side by side with them. I study them, myself!"),
        ("player", "And today, {player}, you're setting off with a Pokémon of your very own."),
        ("rival", "My grandson {rival} is leaving today too. You two have been rivals for as long as I can remember!"),
        ("player", "A world of Pokémon is waiting out there, {player}. Off you go!"),
        ("out", "")]),
    "JOHTO": ("oak", 183, ((240, 246, 236), (186, 214, 176)), [
        ("prof", "Hello, {player}! I'm Professor Oak. I'm visiting Johto for my radio show!"),
        ("mon", "Johto is full of Pokémon, and full of people who love them. You'll meet plenty of both."),
        ("player", "Professor Elm in New Bark Town has a favour to ask you, {player}. It'll be the start of something big."),
        ("player", "Your own Pokémon story is about to begin. I'll be listening for news of you!"),
        ("out", "")]),
    "HOENN": ("birch", 270, ((236, 248, 240), (168, 214, 186)), [
        ("prof", "Welcome to Hoenn, {player}! I'm Professor Birch. I'll be your new neighbour in Littleroot Town!"),
        ("mon", "I study Pokémon out in the wild, where they really live. That's where the fun is!"),
        ("player", "You must be tired from the long ride in the moving truck, {player}. Hoenn's going to be good for you."),
        ("rival", "My kid {rival} has been dying to meet you. You'll be friends in no time, I just know it."),
        ("player", "Your new home's just ahead. Your adventure starts the moment you step outside!"),
        ("out", "")]),
    "SINNOH": ("rowan", 427, ((240, 244, 250), (190, 204, 226)), [
        ("prof", "So. You are {player}. I am Rowan. I research Pokémon in this region, Sinnoh."),
        ("mon", "People and Pokémon here live together, help each other, and grow stronger together."),
        ("player", "I have heard you love Pokémon, {player}. Good. That is the most important thing."),
        ("rival", "Your friend {rival} is the impatient sort. He will be at your door before you know it. Hmph."),
        ("player", "Now, then. Your own story waits out there in Sinnoh. Go and find it."),
        ("out", "")]),
    "ORANGE": ("ivy", 131, ((236, 246, 252), (170, 214, 236)), [
        ("prof", "Welcome to the Orange Islands, {player}! I'm Professor Ivy. I study Pokémon here on Valencia Island."),
        ("mon", "Pokémon here can look a little different from the ones back on the mainland. Isn't that wonderful?"),
        ("player", "You've come all this way to take the Orange League challenge, {player}. Islands, beaches, four Gyms..."),
        ("rival", "And I hear {rival} is somewhere out here too. Some things never change!"),
        ("player", "Come see me at my lab first. Your island adventure is about to begin!"),
        ("out", "")]),
    "UNOVA": ("juniper", 572, ((240, 246, 252), (160, 196, 230)), [   # (Black 2 / White 2's opening: Juniper, then Aspertia, 11-19)
        ("prof", "Hi there, {player}! I'm Professor Juniper. I study where Pokémon come from, here in the Unova region."),
        ("mon", "Pokémon and people live side by side all over Unova, helping each other out. Some even battle together!"),
        ("player", "You live in Aspertia City, {player}, way out on Unova's south-west corner. And today's a special day."),
        ("rival", "Your neighbour {rival} already has a Pokémon, raised from an Egg. He's been itching for a partner on the road."),
        ("player", "My assistant is on her way to see you right now. Your own story in Unova starts the moment you step outside!"),
        ("out", "")]),
    "ORRE": (None, None, ((246, 236, 220), (214, 176, 132)), [
        ("player", "Orre. A dry land of desert and towns built in the sand, where trainers battle in colosseums."),
        ("player", "Something is wrong here. People say some Pokémon have had their hearts shut tight..."),
        ("player", "{player} rides in on the motorbike with two partners: an Espeon and an Umbreon."),
        ("player", "Whatever is going on in Orre, {player} is about to find out."),
        ("out", "")]),
}
OUT_MS = 1400         # (you shrink away into the world)
FADE_IN_MS = 600      # (the scene comes up out of black)
MOVE_MS = 520         # (someone sliding in or out between lines)
BALL_MS = 420         # (the professor's Poke Ball flying out)
POP_MS = 300          # (the Pokemon popping out of it)
TYPE_MS = 22          # (each letter typing out)

# where each one stands in each kind of line (fractions of the width); who isn't listed is off the screen
LAYOUT = {"prof": {"prof": 0.5}, "mon": {"prof": 0.36, "mon": 0.64}, "player": {"player": 0.5},
          "rival": {"rival": 0.5}, "out": {"player": 0.5}}
ENTER_FROM = {"prof": 1.25, "mon": None, "player": -0.25, "rival": 1.25}   # (None: it comes out of the Poke Ball)


def _ease(k):
    k = max(0.0, min(1.0, k))
    return 1 - (1 - k) ** 3


class IntroSpeechState(GameState):
    def __init__(self, game, region, then):
        super().__init__(game)
        self.region = str(region or "").upper()
        self.then = then
        self.intro = INTROS.get(self.region)
        self.i = 0
        self.t0 = pygame.time.get_ticks()
        self.t_line = self.t0 + FADE_IN_MS
        self.prev_layout = {}
        self.done = False
        self.typed_all = False
        self._cache = {}
        self._cried = False
        if not self.intro:
            self.done = True

    def start(self):
        if self.done:
            self.then()

    # ---- pictures
    def _intro_pic(self, name, h):
        key = ("intro", name, h)
        if key not in self._cache:
            img = None
            p = os.path.join(self.game.assets.assets_dir, "sprites", "intro", f"{name}.png")
            if os.path.isfile(p):
                img = pygame.image.load(p).convert_alpha()
            else:
                img = self.game.assets.get_trainer_image(f"prof_{name}.png") or self.game.assets.get_trainer_image(f"{name}.png")
            self._cache[key] = self._fit(img, h)
        return self._cache[key]

    def _fit(self, img, h):
        if img is None:
            return None
        box = img.get_bounding_rect()
        if box.w and box.h:
            img = img.subsurface(box)
        k = h / max(1, img.get_height())
        return pygame.transform.scale(img, (max(1, int(img.get_width() * k)), max(1, int(h))))

    def _mon_pic(self, h):
        key = ("mon", h)
        if key not in self._cache:
            img = None
            try:
                from src.pokemon.data import Pokemon
                p = Pokemon(self.game.loader.fetch_specific(self.intro[1]), self.game.assets, size_mult=2.5)
                img = p.image
            except Exception:
                img = None
            self._cache[key] = self._fit(img, h)
        return self._cache[key]

    def _player_pic(self, h):
        key = ("player", h)
        if key not in self._cache:
            self._cache[key] = self._fit(self.game.assets.get_player_image(str(getattr(self.game, "player_character", "") or "red")), h)
        return self._cache[key]

    def _rival_pic(self, h):
        key = ("rival", h)
        if key not in self._cache:
            char = str(getattr(self.game, "rival_character", "") or "")
            img = None
            if self.region == "SINNOH":
                p = os.path.join(self.game.assets.assets_dir, "sprites", "intro", "barry.png")
                img = pygame.image.load(p).convert_alpha() if os.path.isfile(p) else None
            if self.region == "UNOVA":   # (B2W2's rival is always Hugh, whatever you named him: Black 2's own picture)
                img = self.game.assets.get_trainer_image("hugh.png")
            img = img or self.game.assets.get_trainer_image(f"{char}.png") or self.game.assets.get_player_image(char)
            self._cache[key] = self._fit(img, h)
        return self._cache[key]

    def _pic(self, who, h):
        if who == "prof":
            return self._intro_pic(self.intro[0], int(h * 0.50)) if self.intro[0] else None
        if who == "mon":
            return self._mon_pic(int(h * 0.26))
        if who == "player":
            return self._player_pic(int(h * 0.42))
        if who == "rival":
            return self._rival_pic(int(h * 0.42))
        return None

    # ---- flow
    def _line(self):
        who, text = self.intro[3][self.i]
        name = str(getattr(self.game, "player_name", "") or "TRAINER")
        rival = str(getattr(self.game, "rival_name", "") or "your rival")
        return who, text.replace("{player}", name).replace("{rival}", rival)

    def _layout(self, i=None):
        who = self.intro[3][self.i if i is None else i][0]
        lay = dict(LAYOUT.get(who, {}))
        if not self.intro[0]:
            lay.pop("prof", None)
        return lay

    def _shown_chars(self):
        _, text = self._line()
        if self.typed_all:
            return len(text)
        el = pygame.time.get_ticks() - self.t_line - (MOVE_MS // 2)
        return max(0, min(len(text), el // TYPE_MS))

    def handle_events(self, events):
        if self.done:
            return
        for e in events:
            tap = (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) or \
                  (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER))
            if not tap or self._line()[0] == "out":
                continue
            if pygame.time.get_ticks() < self.t_line:   # (still fading in: straight to the first line)
                self.t_line = pygame.time.get_ticks()
            if self._shown_chars() < len(self._line()[1]):   # (a tap finishes the line; the next one moves on)
                self.typed_all = True
            else:
                self.next()

    def next(self):
        if self.i < len(self.intro[3]) - 1:
            self.prev_layout = self._layout()
            self.i += 1
            self.t_line = pygame.time.get_ticks()
            self.typed_all = False
            self._cried = False

    def update(self):
        if self.done:
            return
        now = pygame.time.get_ticks()
        if self._line()[0] == "mon" and not self._cried and "mon" not in self.prev_layout \
                and now - self.t_line >= BALL_MS:   # (out of the ball: its cry)
            self._cried = True
            try:
                path = self.game.assets.get_cry(self.intro[1])
                if path and pygame.mixer.get_init():
                    pygame.mixer.Sound(path).play()
            except Exception:
                pass
        if self._line()[0] == "out" and now - self.t_line >= OUT_MS:
            self.done = True
            self.then()

    # ---- drawing
    def draw(self):
        screen = self.game.screen
        w, h = screen.get_size()
        if not self.intro:
            screen.fill((0, 0, 0))
            return
        now = pygame.time.get_ticks()
        top, bottom = self.intro[2]
        for y in range(0, h, 4):
            k = y / h
            pygame.draw.rect(screen, tuple(int(top[c] + (bottom[c] - top[c]) * k) for c in range(3)), (0, y, w, 4))
        for n in range(10):   # (soft lights drifting across: the scene is never quite still)
            sx = (n * 173 + (now // 30) * (1 + n % 3)) % (w + 120) - 60
            sy = 40 + (n * 61) % int(h * 0.5)
            glow = pygame.Surface((90, 90), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 255, 255, 28), (45, 45), 45)
            screen.blit(glow, (sx, sy))
        who, text = self._line()
        ground = int(h * 0.66)
        plat = pygame.Rect(0, 0, int(w * 0.40), 46)
        plat.center = (w // 2, ground)
        pygame.draw.ellipse(screen, tuple(max(0, c - 40) for c in bottom), plat)
        pygame.draw.ellipse(screen, tuple(max(0, c - 18) for c in bottom), plat.inflate(-20, -14))
        el = now - self.t_line
        mk = _ease(el / MOVE_MS)
        lay, old = self._layout(), self.prev_layout
        for actor in ("prof", "player", "rival", "mon"):
            if actor not in lay and actor not in old:
                continue
            if who == "out" and actor == "player":
                continue
            img = self._pic(actor, h)
            if img is None:
                continue
            if actor in lay and actor in old:
                x = old[actor] + (lay[actor] - old[actor]) * mk
            elif actor in lay:   # (coming in)
                if actor == "mon" and ENTER_FROM["mon"] is None:
                    self._draw_ball_and_pop(screen, img, lay, el, w, ground)
                    continue
                start = ENTER_FROM[actor]
                x = start + (lay[actor] - start) * mk
            else:   # (going out the way they came)
                if actor == "mon":
                    if mk < 1:
                        s = 1 - mk
                        small = pygame.transform.scale(img, (max(1, int(img.get_width() * s)), max(1, int(img.get_height() * s))))
                        screen.blit(small, small.get_rect(midbottom=(int(w * old["mon"]), ground + 8)))
                    continue
                end = ENTER_FROM[actor]
                x = old[actor] + (end - old[actor]) * mk
            bob = int(2 * math.sin((now + hash(actor) % 500) / 380))   # (breathing)
            screen.blit(img, img.get_rect(midbottom=(int(w * x), ground + 8 + bob)))
        if who == "out":   # (you shrink away into the world, the screen going white: FireRed's ending)
            k = min(1.0, el / OUT_MS)
            img = self._player_pic(max(8, int(h * 0.42 * (1 - 0.85 * k))))
            if img is not None:
                screen.blit(img, img.get_rect(midbottom=(w // 2, ground + 8 - int(40 * k))))
            veil = pygame.Surface((w, h), pygame.SRCALPHA)
            veil.fill((255, 255, 255, int(255 * max(0.0, k - 0.35) / 0.65)))
            screen.blit(veil, (0, 0))
            return
        if text and el >= MOVE_MS // 2:
            box = pygame.Rect(16, h - 150, w - 32, 134)
            theme.draw_textbox(screen, box)
            font = self.game.assets.fonts["button"]
            shown = text[:self._shown_chars()]
            words, lines, cur = text.split(), [], ""   # (wrapped on the whole line, so words don't jump as they type)
            for wd in words:
                trial = (cur + " " + wd).strip()
                if font.size(trial)[0] > box.w - 56 and cur:
                    lines.append(cur)
                    cur = wd
                else:
                    cur = trial
            lines.append(cur)
            left = len(shown)
            for n, ln in enumerate(lines[:3]):
                part = ln[:max(0, left)]
                left -= len(ln) + 1
                if part:
                    theme.shadow_text(screen, part, font, box.x + 28, box.y + 18 + n * 36)
            if len(shown) >= len(text) and (now // 400) % 2 == 0:
                pygame.draw.polygon(screen, theme.TEXT_ARROW, [(box.right - 40, box.bottom - 30), (box.right - 24, box.bottom - 30),
                                                               (box.right - 32, box.bottom - 20)])
        fade = now - self.t0
        if fade < FADE_IN_MS:   # (up out of black)
            veil = pygame.Surface((w, h), pygame.SRCALPHA)
            veil.fill((0, 0, 0, int(255 * (1 - fade / FADE_IN_MS))))
            screen.blit(veil, (0, 0))

    def _draw_ball_and_pop(self, screen, img, lay, el, w, ground):
        """The professor tosses a Poke Ball: it arcs over, opens in a flash, and out the Pokemon pops with a hop."""
        x0 = w * lay.get("prof", 0.4) + 30
        x1 = w * lay["mon"]
        if el < BALL_MS:
            k = el / BALL_MS
            bx = x0 + (x1 - x0) * k
            by = ground - 150 - 120 * math.sin(math.pi * k) + 110 * k
            r = 10
            pygame.draw.circle(screen, (30, 30, 30), (int(bx), int(by)), r + 2)
            pygame.draw.circle(screen, (230, 60, 50), (int(bx), int(by)), r)
            pygame.draw.rect(screen, (250, 250, 250), (int(bx) - r, int(by), 2 * r, r))
            pygame.draw.line(screen, (30, 30, 30), (int(bx) - r, int(by)), (int(bx) + r, int(by)), 2)
            return
        k = min(1.0, (el - BALL_MS) / POP_MS)
        if k < 1:
            flash = pygame.Surface((160, 160), pygame.SRCALPHA)
            pygame.draw.circle(flash, (255, 255, 255, int(200 * (1 - k))), (80, 80), int(30 + 50 * k))
            screen.blit(flash, (int(x1) - 80, ground - 120))
        s = 0.2 + 0.8 * _ease(k)
        hop = int(22 * math.sin(math.pi * min(1.0, (el - BALL_MS) / (POP_MS * 2))))
        bob = int(2 * math.sin(pygame.time.get_ticks() / 380))
        im = pygame.transform.scale(img, (max(1, int(img.get_width() * s)), max(1, int(img.get_height() * s))))
        screen.blit(im, im.get_rect(midbottom=(int(x1), ground + 8 - hop + bob)))
