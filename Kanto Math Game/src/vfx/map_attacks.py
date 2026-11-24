"""Attacks on the map (Jordan 11-24, region/systems): how a move looks in an OVERWORLD-style battle and the swarm's
battle on the map.

A physical move is a lunge: the attacker leans back (wind-up), dashes onto the target and back; the target flashes and
is knocked back (recoil). A special move is a beam in the move's type colour from the user to the target, with the
type's own sprites riding it; the target flinches. A status move is a short ring of its colour round whoever it acts on.
The move's power sets how big all of it is (TIERS: up to 40, 75, 100, more): the wind-up, the recoil, the beam's width,
how many sprites; the strongest also shake the screen and flash it white.

The type sprites are cells of the game's own move-animation sheets (assets/move_animations/graphics: Pokemon
Essentials' animations, the ones the classic battle screen plays), from each type's signature moves - Rock Tomb's
boulder for a Rock lunge, Thunderbolt's bolts along an Electric beam (SPRITES; preview approved by Jordan 11-24)."""
import math
import os
import random

import pygame

from src.config import FPS

COLORS = {"NORMAL": (200, 200, 160), "FIRE": (240, 128, 48), "WATER": (104, 144, 240), "ELECTRIC": (248, 208, 48),
          "GRASS": (120, 200, 80), "ICE": (152, 216, 216), "FIGHTING": (208, 64, 48), "POISON": (160, 64, 160),
          "GROUND": (224, 192, 104), "FLYING": (168, 144, 240), "PSYCHIC": (248, 88, 136), "BUG": (168, 184, 32),
          "ROCK": (184, 160, 56), "GHOST": (112, 88, 152), "DRAGON": (112, 56, 248), "DARK": (112, 88, 72),
          "STEEL": (184, 184, 208), "FAIRY": (238, 153, 172)}

# type: (along a beam, the physical hit played on the target, the bits a physical hit throws out): (sheet, [cells])
SPRITES = {
    "NORMAL": (("PRAS- Swift.png", [0]), ("PRAS- Strike.png", [0]), ("PRAS- Swift.png", [0])),
    "FIRE": (("PRAS- Fire.png", [36, 37, 38, 39]), ("PRAS- Fire.png", [36, 37, 38, 39]), ("PRAS- Fire.png", [20, 21, 22])),
    "WATER": (("PRAS- Water.png", [28]), ("PRAS- Water.png", [32, 33, 34, 35]), ("PRAS- Water.png", [28, 29])),
    "ELECTRIC": (("PRAS- Electric.png", [48, 51]), ("PRAS- Electric.png", [50, 49, 50]), ("PRAS- Electric.png", [48, 51])),
    "GRASS": (("PRAS- Grass.png", [8, 9, 10]), ("PRAS- Grass.png", [9, 10, 11, 12]), ("PRAS- Grass.png", [8, 9, 14])),
    "ICE": (("PRAS- Powder Snow.png", [9]), ("PRAS- Ice.png", [12]), ("PRAS- Ice.png", [7])),
    "FIGHTING": (("PRAS- Aura Sphere.png", [0, 1, 2, 3]), ("PRAS- Strike.png", [20, 0]), ("PRAS- Strike.png", [0])),
    "POISON": (("PRAS- Sludge Bomb.png", [4]), ("PRAS- Poison Jab.png", [0, 1, 2]), ("PRAS- Sludge Bomb.png", [4])),
    "GROUND": (("PRAS- Mud Slap.png", [1, 2]), ("PRAS- Mud Slap.png", [4, 5, 6]), ("PRAS- Rock.png", [3, 4, 5])),
    "FLYING": (("PRAS- Air Slash.png", [2, 3]), ("PRAS- Slash.png", [6, 8, 5]), ("PRAS- Air Slash.png", [1])),
    "PSYCHIC": (("PRAS- Psybeam.png", [0, 1, 2, 3]), ("PRAS- Uproar.png", [0, 1, 8, 9, 10, 11]), ("PRAS- Psycho Cut.png", [0])),
    "BUG": (("PRAS- Bug Buzz.png", [0, 2, 1]), ("PRAS- X Scissor.png", [1, 2, 3]), ("PRAS- Bug Bite.png", [4, 5])),
    "ROCK": (("PRAS- Rock.png", [16, 15, 18]), ("PRAS- Rock.png", [0]), ("PRAS- Rock.png", [1, 2, 3])),
    "GHOST": (("PRAS- Will O Wisp.png", [0, 1, 2, 3, 4, 5, 6, 7]), ("PRAS- Shadow Claw.png", [3, 1, 2]), ("PRAS- Grudge.png", [0, 1, 2, 3])),
    "DRAGON": (("PRAS- Dragon Pulse.png", [1, 2, 3, 4]), ("PRAS- Dragon Claw.png", [1, 2, 3, 4]), ("PRAS- Dragonbreath.png", [0, 1])),
    "DARK": (("Shadow2.png", [1, 2, 3]), ("PRAS- Bite.png", [0, 1]), ("Shadow2.png", [4, 5, 6])),
    "STEEL": (("PRAS- Iron Head.png", [1]), ("PRAS- Slash.png", [39, 40, 41, 42]), ("PRAS- Iron Head.png", [0, 1])),
    "FAIRY": (("PRAS- Recovery.png", [0, 1, 2, 3]), ("PRAS- Love.png", [10, 11]), ("PRAS- Love.png", [3, 7, 9])),
}
TIERS = (40, 75, 100)            # power up to each: tiers 0, 1, 2; above: 3
SCALE = (0.55, 0.8, 1.05, 1.4)   # sprite size by tier
WIND = (6, 11, 17, 26)           # px leaned back before a lunge
RECOIL = (8, 17, 30, 42)         # px a physical hit pushes the target back
FLINCH = (4, 8, 12, 18)          # px a special hit pushes it
BEAM_W = (4, 7, 11, 17)
BITS = (4, 7, 11, 16)            # sprites a physical hit throws out (a special one: about two thirds)
LENGTH = {"PHYSICAL": int(FPS * 1.0), "SPECIAL": int(FPS * 1.05), "STATUS": int(FPS * 0.7)}

_cells = {}


def tier(power):
    p = int(power or 0)
    return next((i for i, top in enumerate(TIERS) if p <= top), 3)


def _cell(assets_dir, sheet, i):
    key = (sheet, i)
    if key not in _cells:
        img = None
        try:
            s = pygame.image.load(os.path.join(assets_dir, "move_animations", "graphics", sheet))
            s = s.convert_alpha() if pygame.display.get_surface() else s
            cols = max(1, s.get_width() // 192)
            c = s.subsurface(((i % cols) * 192, (i // cols) * 192, 192, 192))
            b = c.get_bounding_rect()
            img = c.subsurface(b.inflate(4, 4).clip(c.get_rect())).copy() if b.w else None
        except (pygame.error, OSError, ValueError):
            img = None
        _cells[key] = img
    return _cells[key]


def sprites(assets_dir, typ, which):
    """The cells (Surfaces) for a type's beam (0), hit (1) or bits (2); [] if none load."""
    sheet, cells = SPRITES.get(str(typ).upper(), SPRITES["NORMAL"])[which]
    return [img for img in (_cell(assets_dir, sheet, i) for i in cells) if img is not None]


def white(img):
    """img as a white silhouette (a flash as it's hit)."""
    out = img.copy()
    out.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
    return out


class MapAttack:
    """One move played on the map. user / target: callables giving their tile rects on screen now (the camera may
    move). Ask offset(who) each frame for how far to draw the user ("user") or target ("target") from its spot, and
    flashing() for the target's white flash; draw(screen) adds the beam, the sprites and the flash; done when over."""

    def __init__(self, game, move, user, target, self_target=False):
        self.game = game
        d = move if isinstance(move, dict) else {}
        self.type = str(d.get("type") or "NORMAL").upper()
        if self.type not in COLORS:
            self.type = "NORMAL"
        self.power = int(d.get("power") or 0)
        cat = str(d.get("category") or "STATUS").upper()
        self.kind = cat if cat in ("PHYSICAL", "SPECIAL") and self.power > 0 else "STATUS"
        self.tier = tier(self.power)
        self.user, self.target = user, (user if self_target else target)
        self.t, self.length = 0, LENGTH[self.kind]
        self.parts, self.fired = [], False
        self.rng = random.Random()
        adir = game.assets.assets_dir if getattr(game, "assets", None) else ""
        self.beam_imgs, self.hit_imgs, self.bit_imgs = (sprites(adir, self.type, k) for k in range(3))

    # ---------------------------------------------------------------- timing
    @property
    def k(self):
        return self.t / max(1, self.length)

    @property
    def done(self):
        return self.t >= self.length and not self.parts

    def update(self):
        self.t += 1
        if self.hitting() and not self.fired:
            self.fired = True
            self._burst()
        for p in self.parts:
            p[0] += p[2]
            p[1] += p[3]
            p[2] *= 0.93
            p[3] = p[3] * 0.93 + 0.18
            p[4] -= 1
            p[6] += p[7]
        self.parts = [p for p in self.parts if p[4] > 0]

    def hitting(self):
        """The moment it lands (and a little after)."""
        k = self.k
        return {"PHYSICAL": 0.32 <= k < 0.62, "SPECIAL": 0.36 <= k < 0.62, "STATUS": 0.2 <= k < 0.8}[self.kind]

    def _hit_k(self):
        lo = {"PHYSICAL": 0.32, "SPECIAL": 0.36, "STATUS": 0.2}[self.kind]
        return max(0.0, min(1.0, (self.k - lo) / 0.3))

    def flashing(self):
        return self.kind != "STATUS" and self.hitting() and self._hit_k() < 0.25

    def _way(self):
        a, b = self.user().center, self.target().center
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1.0
        return dx / n, dy / n, n

    def offset(self, who):
        """(dx, dy) to draw the user or the target away from its spot now."""
        if self.kind == "STATUS" or self.t >= self.length:
            return 0, 0
        ux, uy, dist = self._way()
        k = self.k
        if who == "user" and self.kind == "PHYSICAL":
            wind, reach = WIND[self.tier], max(0.0, dist - 34)
            if k < 0.2:
                d = -wind * (k / 0.2)
            elif k < 0.32:
                d = -wind + (reach + wind) * ((k - 0.2) / 0.12)
            elif k < 0.55:
                d = reach * (1 - (k - 0.32) / 0.23)
            else:
                d = 0
            return int(ux * d), int(uy * d)
        if who == "target" and self.hitting():
            hk = self._hit_k()
            if self.kind == "PHYSICAL":
                d = RECOIL[self.tier] * math.sin(min(1.0, hk * 2) * math.pi / 2) * (1 - hk) * 1.6
            else:
                d = FLINCH[self.tier] * math.sin(hk * math.pi)
            return int(ux * d), int(uy * d)
        return 0, 0

    def shake(self):
        """Screen shake (px) for the strongest moves as they land."""
        if self.tier < 3 or not self.hitting() or self.kind == "STATUS":
            return 0
        return int((1 - self._hit_k()) * 6)

    # ---------------------------------------------------------------- drawing
    def _burst(self):
        imgs = self.bit_imgs if self.kind == "PHYSICAL" else self.beam_imgs
        if not imgs:
            return
        n = BITS[self.tier] if self.kind == "PHYSICAL" else max(2, BITS[self.tier] * 2 // 3)
        speed = (2.0, 2.8, 3.6, 4.4)[self.tier]
        cx, cy = self.target().center
        for _ in range(n):
            a, v = self.rng.uniform(0, math.tau), self.rng.uniform(0.6, 1.4) * speed
            # [x, y, vx, vy, life, max, angle, spin, image index, scale]
            self.parts.append([cx, cy - 6, math.cos(a) * v, math.sin(a) * v - 1, self.rng.randint(14, 24), 24, 0.0,
                               self.rng.uniform(-8, 8), self.rng.randrange(len(imgs)), self.rng.uniform(0.6, 1.0)])

    @staticmethod
    def _blit(screen, img, at, scale, alpha=255, angle=0.0):
        if img is None or scale <= 0:
            return
        w, h = max(1, int(img.get_width() * scale)), max(1, int(img.get_height() * scale))
        pic = pygame.transform.scale(img, (w, h))
        if angle:
            pic = pygame.transform.rotate(pic, angle)
        if alpha < 255:
            pic.set_alpha(max(0, int(alpha)))
        screen.blit(pic, pic.get_rect(center=(int(at[0]), int(at[1]))))

    def draw(self, screen):
        if self.t >= self.length and not self.parts:
            return
        sc = SCALE[self.tier]
        col = COLORS[self.type]
        k = self.k
        a, b = self.user().center, self.target().center
        if self.kind == "SPECIAL" and self.t < self.length:
            if k < 0.15:   # (charging: a glow on the user)
                glow = pygame.Surface((80, 80), pygame.SRCALPHA)
                pygame.draw.circle(glow, col + (140,), (40, 40), int(4 + k * 160 * sc))
                screen.blit(glow, glow.get_rect(center=a))
            elif k < 0.55:   # (the beam, growing out to the target, the type's sprites riding it)
                bk = min(1.0, (k - 0.15) / 0.4 * 1.6)
                end = (a[0] + (b[0] - a[0]) * bk, a[1] + (b[1] - a[1]) * bk)
                w = BEAM_W[self.tier]
                pygame.draw.line(screen, col, a, end, w)
                pygame.draw.line(screen, (255, 255, 255), a, end, max(1, w // 3))
                if self.beam_imgs:
                    n = 2 + self.tier * 2
                    ux, uy, dist = self._way()
                    span = math.hypot(end[0] - a[0], end[1] - a[1])
                    for j in range(n):
                        d = (self.t * 6 + j * dist / n) % max(1.0, span)
                        wob = math.sin(d / 14 + j) * w * 0.7
                        at = (a[0] + ux * d - uy * wob, a[1] + uy * d + ux * wob)
                        self._blit(screen, self.beam_imgs[(self.t // 3 + j) % len(self.beam_imgs)], at, sc * 0.9)
        if self.kind == "PHYSICAL" and self.hitting() and self.hit_imgs:   # (the hit, played on the target)
            hk = self._hit_k()
            img = self.hit_imgs[min(len(self.hit_imgs) - 1, int(hk * len(self.hit_imgs) * 1.2))]
            self._blit(screen, img, (b[0], b[1] - 6), sc * 1.25 * (0.8 + hk * 0.4), 255 * (1 - max(0.0, hk - 0.7) / 0.3))
        if self.kind == "STATUS" and self.t < self.length:   # (a ring of its colour round whoever it acts on)
            rk = self._hit_k()
            ring = pygame.Surface((120, 120), pygame.SRCALPHA)
            pygame.draw.circle(ring, col + (int(220 * (1 - rk)),), (60, 60), int(14 + rk * 40), 4)
            screen.blit(ring, ring.get_rect(center=b))
        imgs = self.bit_imgs if self.kind == "PHYSICAL" else self.beam_imgs
        for p in self.parts:
            if imgs:
                self._blit(screen, imgs[(p[8] + p[4] // 6) % len(imgs)], (p[0], p[1]), p[9] * sc,
                           255 * min(1.0, p[4] / p[5] * 1.5), p[6])
        if self.tier == 3 and self.kind != "STATUS" and self.hitting() and self._hit_k() < 0.12:   # (the strongest: a white flash)
            flash = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            flash.fill((255, 255, 255, 90))
            screen.blit(flash, (0, 0))


def move_for(game, name):
    """The move's data (type, power, category, target) by its name ("THUNDERBOLT" or "Thunderbolt")."""
    from src.pokemon import moves as movelib
    key = str(name or "").upper().replace(" ", "-")
    return movelib.info(game, key)
