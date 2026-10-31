"""Battle intros (Jordan, 10-30): the screen you were on gives way to the battle, with Pokemon Journeys'
transition art (assets/transitions, from its Graphics/Transitions):

- wild: a wipe to black along one of its patterns (light parts last), or a spinning Poke Ball;
  on the water, bubbles rising;
- trainers: black wedges closing in from the four sides, the hexagon wipe, or a pattern wipe;
- gym leaders, the Elite Four, champions, rivals and bosses: the VS screen (a coloured bar, the foe
  on it, VS, a flash);
- Team Rocket: their R.

Game.change_state puts this in front of a wild battle or a trainer's intro (see wants_transition)."""
import math
import os
import random

import pygame

from src.states.base import GameState

_IMAGES = {}
RULES = ["Battle.png", "Image1.png", "Image2.png", "Image3.png", "Image4.png",
         "battle1.png", "battle2.png", "battle3.png", "battle4.png"]
BIG = ("GYM_LEADER", "ELITE_FOUR", "CHAMPION", "RIVAL")


def image(game, name):
    """A picture from assets/transitions, loaded once (None if missing)."""
    if name not in _IMAGES:
        path = os.path.join(game.assets.assets_dir, "transitions", name)
        try:
            _IMAGES[name] = pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError):
            _IMAGES[name] = None
    return _IMAGES[name]


def wants_transition(game, new_state):
    """A wild battle or a trainer's intro, entered from outside a battle."""
    if not getattr(game, "battle_transitions", True):
        return False
    from src.states.battle import TrainerBattleState, WildBattleState, TrainerIntroState
    cur = getattr(game, "current_state", None)
    if cur is None or getattr(game, "screen", None) is None:
        return False
    if isinstance(cur, (TrainerBattleState, TrainerIntroState, BattleTransitionState)):
        return False
    return isinstance(new_state, (WildBattleState, TrainerIntroState))


def style_for(target):
    """Which intro suits this battle."""
    from src.states.battle import WildBattleState
    battle = getattr(target, "next_state", target)
    cls = str(getattr(battle, "trainer_class", "") or "").upper()
    if "ROCKET" in cls:
        return "rocket"
    if isinstance(target, WildBattleState):
        if getattr(target, "is_boss_battle", False):
            return "vs"
        if str(getattr(target, "battle_type", "")).lower() in ("ocean", "water"):
            return "water"
        return random.choice(["rule", "rule", "ball"])
    if cls in BIG or getattr(battle, "battle_type", "") in ("gym", "rival") or getattr(battle, "is_boss_battle", False):
        return "vs"
    return random.choice(["wedges", "hexa", "rule"])


class BattleTransitionState(GameState):
    LENGTH = {"rule": 22, "ball": 26, "water": 26, "wedges": 20, "hexa": 22, "vs": 46, "rocket": 40}

    def __init__(self, game, target, style=None):
        super().__init__(game)
        self.target = target
        self.style = style or style_for(target)
        self.snapshot = game.screen.copy()
        self.t = 0
        self.length = self.LENGTH.get(self.style, 22)
        w, h = game.width, game.height
        self.masks = []
        if self.style in ("rule", "hexa"):
            name = "hexatr.png" if self.style == "hexa" else random.choice(RULES)
            self.masks = self._rule_masks(image(game, name), (w, h))
        battle = getattr(target, "next_state", target)
        self.foe = getattr(target, "trainer_sprite", None) or getattr(battle, "trainer_sprite", None)
        if self.foe is not None and not isinstance(self.foe, pygame.Surface):
            self.foe = None
        self.bar = image(game, random.choice(["vsBar0.png", "vsBar1.png", "vsBar4.png"]))

    @staticmethod
    def _rule_masks(rule, size, steps=16):
        """Black masks for a pattern wipe: step i covers the pattern's parts darker than i/steps."""
        if rule is None:
            return []
        small = pygame.transform.smoothscale(rule.convert(), (size[0] // 4, size[1] // 4))
        out = []
        for i in range(1, steps + 1):
            v = int(255 * i / steps)
            m = pygame.Surface(small.get_size())
            m.fill((255, 0, 255))
            pygame.transform.threshold(m, small, (0, 0, 0), (v, v, v, 255), (0, 0, 0), 1, None, True)
            m.set_colorkey((255, 0, 255))
            out.append(pygame.transform.scale(m, size))
        return out

    def start(self):
        music = getattr(self.game, "music", None)
        if music:
            music.for_state(self.target)  # the battle music starts with the intro

    def handle_events(self, events):
        pass  # it plays through (about a second)

    def update(self):
        self.t += 1
        if self.t >= self.length:
            self.game.change_state(self.target)

    # ------------------------------------------------------------------ drawing
    def draw(self):
        screen = self.game.screen
        w, h = self.game.width, self.game.height
        k = min(1.0, self.t / self.length)
        screen.blit(self.snapshot, (0, 0))
        if self.t < 4:  # a flash or two first, as in the games
            if self.t % 2 == 0:
                screen.fill((250, 250, 250))
            return
        getattr(self, "_draw_" + self.style, self._draw_rule)(screen, w, h, k)

    def _draw_rule(self, screen, w, h, k):
        if not self.masks:
            screen.fill((0, 0, 0), (0, 0, w, int(h * k)))
            return
        screen.blit(self.masks[min(len(self.masks) - 1, int(k * len(self.masks)))], (0, 0))

    _draw_hexa = _draw_rule

    def _draw_ball(self, screen, w, h, k):
        """A Poke Ball spins in, growing until it fills the screen, then black."""
        ball = image(self.game, "ball_large.png")
        if ball is None or k > 0.85:
            screen.fill((0, 0, 0))
            return
        size = int(max(w, h) * 1.6 * (k / 0.85) ** 2) + 8
        img = pygame.transform.rotozoom(ball, -720 * k, size / ball.get_width())
        dark = pygame.Surface((w, h), pygame.SRCALPHA)
        dark.fill((0, 0, 0, int(200 * k)))
        screen.blit(dark, (0, 0))
        screen.blit(img, img.get_rect(center=(w // 2, h // 2)))

    def _draw_water(self, screen, w, h, k):
        """Bubbles rise over the screen, then the deep water closes over it."""
        bubbles = image(self.game, "water_1.png")
        wave = image(self.game, "water_2.png")
        if bubbles:
            b = pygame.transform.scale(bubbles, (w, h))
            screen.blit(b, (0, int(h * (1 - 2 * k))))
        if wave:
            wv = pygame.transform.scale(wave, (w, h))
            screen.blit(wv, (0, int(h * (1.4 - 1.6 * k))))
        if k > 0.85:
            screen.fill((0, 0, 0))

    def _draw_wedges(self, screen, w, h, k):
        """Four black wedges close in from the edges until they meet in the middle."""
        e = 1 - (1 - k) ** 2
        cx, cy = w / 2, h / 2
        for (ax, ay), (bx, by) in (((0, 0), (w, 0)), ((w, 0), (w, h)), ((w, h), (0, h)), ((0, h), (0, 0))):
            tip = (ax + (bx - ax) / 2 + (cx - (ax + (bx - ax) / 2)) * e, ay + (by - ay) / 2 + (cy - (ay + (by - ay) / 2)) * e)
            pygame.draw.polygon(screen, (0, 0, 0), [(ax, ay), (bx, by), tip])
        if k > 0.95:
            screen.fill((0, 0, 0))

    def _draw_vs(self, screen, w, h, k):
        """The VS screen: the bar sweeps in, the foe slides onto it, VS lands, a flash, black."""
        screen.fill((0, 0, 0))
        bar_h = int(h * 0.42)
        y = (h - bar_h) // 2
        if self.bar:
            bar = pygame.transform.scale(self.bar, (w, bar_h))
            x = int(w * (1 - min(1.0, k / 0.25)))
            shift = int((self.t * 28) % w)  # the streaks rush past
            screen.blit(bar, (x - shift, y))
            screen.blit(bar, (x - shift + w, y))
        if self.foe is not None and k > 0.15:
            f = self.foe.subsurface(self.foe.get_bounding_rect())  # its visible part, filling the bar
            fh = int(bar_h * 1.1)
            fw = int(f.get_width() * fh / max(1, f.get_height()))
            f = pygame.transform.scale(f, (fw, fh))
            slide = min(1.0, (k - 0.15) / 0.25)
            fx = int(w * 1.1 - (w * 1.1 - w * 0.70) * (1 - (1 - slide) ** 3))
            screen.blit(f, f.get_rect(midbottom=(fx, y + bar_h)))
        vs = image(self.game, "vs.png")
        if vs is not None and k > 0.40:
            land = min(1.0, (k - 0.40) / 0.12)
            scale = 3.0 - 1.6 * land
            img = pygame.transform.rotozoom(vs, 0, scale * h / 720 * 1.6)
            screen.blit(img, img.get_rect(center=(int(w * 0.32), h // 2)))
        if 0.55 < k < 0.62:
            screen.fill((255, 255, 255))
        if k > 0.88:
            fade = pygame.Surface((w, h))
            fade.set_alpha(int(255 * (k - 0.88) / 0.12))
            screen.blit(fade, (0, 0))

    def _draw_rocket(self, screen, w, h, k):
        """Team Rocket's ground, then their R between two white stripes, then black."""
        bg = image(self.game, "rocket_bg_2.png" if k > 0.3 else "rocket_bg_1.png")
        if bg:
            pulse = 1 + (0.06 * math.sin(self.t * 0.8) if k > 0.3 else 0)
            img = pygame.transform.scale(bg, (int(w * pulse), int(h * pulse)))
            screen.blit(img, img.get_rect(center=(w // 2, h // 2)))
        else:
            screen.fill((30, 30, 30))
        if k > 0.85:
            fade = pygame.Surface((w, h))
            fade.set_alpha(int(255 * (k - 0.85) / 0.15))
            screen.blit(fade, (0, 0))
