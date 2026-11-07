"""Pixel-art backdrops for the Gym minigames (Jordan, 11-06): in place of the dark screen behind the
ones that play over their background, each gets a scene of its own, painted in code in the style of
assets/backgrounds/starter_bg.png (DS-style pixel art: a few shades a colour, clustered leaves,
light from the top left, a little dithering), and alive: clouds drift, grass sways, leaves fall,
embers rise, lights sweep, stars twinkle, and a runner's scenery scrolls past at its own speed.

A scene is painted once at a quarter of the screen's size (cached), then each frame its moving
parts are added and the whole is grown 4x, so every pixel is a crisp 4 x 4 square.

    scene = Scene("meadow", width, height, seed)
    scene.draw(screen, frame, scroll)     # scroll: how far a runner has run (screen pixels)

Kinds: meadow, plains, sky, dojo, stage, stadium, arena, power, volcano, cosmos, night.
"""
import math
import random

import pygame

P = 4  # one art pixel = P x P screen pixels
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))

# ---------------------------------------------------------------- colours (dark to light)
LEAF = [(22, 52, 50), (32, 78, 58), (48, 110, 62), (78, 148, 68), (124, 186, 84), (176, 214, 108)]
LEAF_NIGHT = [(12, 22, 38), (18, 34, 50), (26, 48, 62), (40, 66, 74), (58, 88, 84)]
GRASS = [(36, 92, 56), (52, 122, 60), (78, 156, 66), (118, 190, 80), (164, 214, 104)]
BARK = [(48, 32, 34), (78, 52, 44), (112, 76, 56), (150, 106, 72)]
ROCK = [(56, 48, 56), (86, 74, 78), (120, 104, 100), (158, 140, 126), (196, 180, 160)]
CLOUD = [(140, 164, 206), (180, 200, 230), (222, 234, 248), (255, 255, 255)]
WOOD = [(52, 30, 24), (84, 50, 34), (120, 76, 46), (160, 108, 62), (196, 144, 86)]
METAL = [(30, 34, 44), (48, 54, 68), (72, 80, 98), (104, 114, 134), (146, 156, 176)]

_CACHE = {}


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def bayer(x, y):
    return (BAYER[y % 4][x % 4] + 0.5) / 16


def gradient(surf, rect, stops, horizontal=False):
    """A dithered gradient through stops (colours) over rect: flat bands, a 4 x 4 dither between."""
    x0, y0, w, h = rect
    length = w if horizontal else h
    # in-between shades, so each band steps only a little (about one every 14 art pixels)
    per = max(1, round(length / 14 / max(1, len(stops) - 1)))
    stops = [mix(stops[k], stops[k + 1], j / per) for k in range(len(stops) - 1) for j in range(per)] + [stops[-1]]
    n = len(stops) - 1
    for i in range(length):
        t = i / max(1, length - 1) * n
        k = min(n - 1, int(t))
        frac = t - k
        a, b = stops[k], stops[k + 1]
        # each band: solid, then a short dithered blend into the next
        blend = (frac - 0.55) / 0.45
        for j in range(h if horizontal else w):
            x, y = (x0 + i, y0 + j) if horizontal else (x0 + j, y0 + i)
            surf.set_at((x, y), b if blend > bayer(x, y) else a)


def wave(width, rng, base, parts):
    """A ridge's height at each x, repeating every width (so it can scroll forever)."""
    phases = [(k, a, rng.uniform(0, math.tau)) for k, a in parts]
    return [base + sum(a * math.sin(math.tau * k * x / width + p) for k, a, p in phases) for x in range(width)]


def blob(surf, cx, cy, r, ramp, rng, rough=0.16, squash=1.0, light=(-0.62, -0.78), wrap=None):
    """A clump of leaves (or a cloud, or a rock): a rough disc shaded from the light's side, a band of
    dither between shades, the darkest shade round its far rim."""
    lx, ly = light
    ph = [rng.uniform(0, math.tau) for _ in range(3)]
    n = len(ramp) - 1
    w, h = surf.get_size()
    for y in range(int(cy - r * squash) - 2, int(cy + r * squash) + 3):
        for x in range(int(cx - r) - 2, int(cx + r) + 3):
            dx, dy = x - cx, (y - cy) / squash
            d = math.hypot(dx, dy)
            ang = math.atan2(dy, dx)
            rr = r * (1 + rough * (math.sin(ang * 5 + ph[0]) * 0.6 + math.sin(ang * 9 + ph[1]) * 0.4))
            if d > rr:
                continue
            lit = (dx * lx + dy * ly) / max(1, r)           # 1: facing the light (top left)
            v = 0.52 + lit * 0.42 - (d / rr) ** 3 * 0.32
            v += (bayer(x, y) - 0.5) * 0.11
            k = max(0, min(n, int(v * (n + 1))))
            px = x % w if wrap else x
            if 0 <= px < w and 0 <= y < h:
                surf.set_at((px, y), ramp[k])


def canopy(surf, cx, cy, size, ramp, rng, wrap=None):
    """A tree's crown: clumps, the back ones first (darker), the front lit."""
    clumps = []
    for _ in range(int(5 + size / 3)):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0, size * 0.62)
        clumps.append((cx + math.cos(a) * d, cy + math.sin(a) * d * 0.62, size * rng.uniform(0.34, 0.52)))
    clumps.sort(key=lambda c: c[1])
    for x, y, r in clumps:
        blob(surf, x, y, r, ramp, rng, wrap=wrap)
    # leaf glints on the lit side
    for _ in range(int(size * 1.4)):
        x = int(cx + rng.uniform(-size, size * 0.3))
        y = int(cy + rng.uniform(-size * 0.7, size * 0.1))
        if 0 <= y < surf.get_height():
            xx = x % surf.get_width() if wrap else x
            if 0 <= xx < surf.get_width() and surf.get_at((xx, y))[:3] in (tuple(ramp[-2]), tuple(ramp[-3])):
                surf.set_at((xx, y), ramp[-1])
                if 0 <= xx + 1 < surf.get_width():
                    surf.set_at((xx + 1, y), ramp[-1])


def trunk(surf, x, top, bottom, w, ramp, rng, wrap=None):
    """A trunk: lit on its left, its bark in streaks, its roots spreading at the foot."""
    W = surf.get_width()
    for y in range(int(top), int(bottom)):
        flare = max(0, (y - (bottom - 6))) * 0.8
        left, right = int(x - w / 2 - flare), int(x + w / 2 + flare)
        for xx in range(left, right + 1):
            t = (xx - left) / max(1, right - left)
            k = 3 if t < 0.22 else 2 if t < 0.55 else 1 if t < 0.85 else 0
            px = xx % W if wrap else xx
            if 0 <= px < W:
                surf.set_at((px, y), ramp[k])
    for _ in range(int((bottom - top) / 3)):  # bark streaks
        xx = int(x + rng.uniform(-w / 2 + 1, w / 2))
        y0 = int(rng.uniform(top, bottom - 3))
        for y in range(y0, min(int(bottom), y0 + rng.randint(2, 6))):
            px = xx % W if wrap else xx
            if 0 <= px < W:
                surf.set_at((px, y), ramp[0])


def tree(surf, x, ground, height, ramp_leaf, rng, wrap=None, bark=BARK, berries=None):
    w = max(3, height / 9)
    trunk(surf, x, ground - height * 0.62, ground, w, bark, rng, wrap)
    canopy(surf, x, ground - height * 0.72, height * 0.36, ramp_leaf, rng, wrap)
    for _ in range(int(height / 6) if berries else 0):  # berries hanging in the leaves
        a, d = rng.uniform(0, math.tau), rng.uniform(0, height * 0.3)
        bx, by = int(x + math.cos(a) * d), int(ground - height * 0.7 + math.sin(a) * d * 0.6)
        col = rng.choice(berries)
        for ox, oy, c in ((0, 0, col[0]), (1, 0, col[0]), (0, 1, col[1]), (1, 1, col[1]), (0, -1, col[2])):
            px = (bx + ox) % surf.get_width() if wrap else bx + ox
            if 0 <= px < surf.get_width() and 0 <= by + oy < surf.get_height():
                surf.set_at((px, by + oy), c)


def ridge_fill(surf, heights, ramp, top_light=2, dither_to=None, depth=None):
    """Land under a ridge: a lit lip along its top, then its own shade darkening downward."""
    h = surf.get_height()
    for x, top in enumerate(heights):
        top = int(top)
        for y in range(max(0, top), h if depth is None else min(h, top + depth)):
            d = y - top
            if d < top_light:
                c = ramp[-1]
            else:
                t = min(1.0, (d - top_light) / 40)
                c = ramp[-2] if t + (bayer(x, y) - 0.5) * 0.5 < 0.35 else ramp[-3] if len(ramp) > 2 else ramp[0]
                if dither_to is not None and t > 0.6 and bayer(x, y) < (t - 0.6) * 1.5:
                    c = dither_to
            surf.set_at((x, y), c)


def cloud(rng, w, h, ramp=CLOUD):
    """A cloud: rounded heaps on a flat base, lit from above."""
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(max(3, w // 10)):
        r = rng.uniform(h * 0.28, h * 0.5)
        cx = rng.uniform(r, w - r)
        cy = h - r * 0.9 - rng.uniform(0, h * 0.18)
        blob(s, cx, cy, r, ramp, rng, rough=0.08, light=(-0.2, -0.98))
    for x in range(w):  # its flat underside
        for y in range(h - 2, h):
            if s.get_at((x, y)).a:
                s.set_at((x, y), ramp[0])
    return s


def grass_tufts(rng, width, y0, y1, n):
    return [(rng.uniform(0, width), rng.uniform(y0, y1), rng.randint(2, 4), rng.uniform(0, math.tau)) for _ in range(n)]


class Layer:
    def __init__(self, img, factor=0.0, drift=0.0, y=0):
        self.img, self.factor, self.drift, self.y = img, factor, drift, y

    def draw(self, canvas, t, scroll):
        w = self.img.get_width()
        off = (scroll * self.factor + t * self.drift) % w
        x = -int(off)
        while x < canvas.get_width():
            canvas.blit(self.img, (x, self.y))
            x += w


class Scene:
    def __init__(self, kind, width, height, seed=0):
        self.kind = kind
        self.w, self.h = -(-width // P), -(-height // P)
        self.W, self.H = width, height
        self.rng = random.Random(f"{kind}:{seed}")
        key = (kind, self.w, self.h, seed)
        if key not in _CACHE:
            self.back, self.layers, self.front, self.data = None, [], [], {}
            getattr(self, "_build_" + kind)()
            _CACHE[key] = (self.back, self.layers, self.front, self.data)
        self.back, self.layers, self.front, self.data = _CACHE[key]
        self.canvas = pygame.Surface((self.w, self.h))
        self.fx = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self.big = pygame.Surface((self.w * P, self.h * P))

    # ---------------------------------------------------------------- each frame
    def draw(self, screen, t, scroll=0.0):
        c = self.canvas
        c.blit(self.back, (0, 0))
        s = scroll / P
        for layer in self.layers:
            layer.draw(c, t, s)
        getattr(self, "_live_" + self.kind, lambda c, t, s: None)(c, t, s)
        for layer in self.front:
            layer.draw(c, t, s)
        pygame.transform.scale(c, self.big.get_size(), self.big)
        screen.blit(self.big, (0, 0))

    def _glow(self, c, color, alpha, points):
        """Soft lights (translucent shapes) over the scene."""
        self.fx.fill((0, 0, 0, 0))
        for kind, args in points:
            if kind == "poly":
                pygame.draw.polygon(self.fx, (*color, alpha), args)
            else:
                x, y, r = args
                pygame.draw.circle(self.fx, (*color, alpha), (int(x), int(y)), int(r))
        c.blit(self.fx, (0, 0))

    # ================================================================ MEADOW: Berry Catch
    def _build_meadow(self):
        w, h, rng = self.w, self.h, self.rng
        sky = pygame.Surface((w, h))
        gradient(sky, (0, 0, w, h), [(78, 140, 214), (120, 178, 230), (176, 214, 240), (214, 234, 244)])
        back = pygame.Surface((w, h), pygame.SRCALPHA)  # the land, in front of the clouds
        far = wave(w, rng, h * 0.56, [(1, 5), (3, 3), (7, 1.2)])
        ridge_fill(back, far, [(84, 132, 150), (104, 156, 160), (128, 178, 170), (156, 198, 176)], 1)
        mid = wave(w, rng, h * 0.64, [(2, 4), (5, 2), (11, 0.8)])
        ridge_fill(back, mid, [(46, 104, 74), (60, 128, 76), (84, 154, 80), (116, 180, 88)], 1)
        for x in range(-10, w + 10, 9):  # a far line of woods along the hills
            blob(back, x + rng.uniform(-3, 3), mid[x % w] - 1, rng.uniform(4, 7),
                 [(36, 86, 70), (46, 104, 74), (62, 126, 78), (88, 152, 84)], rng, squash=0.8)
        for _ in range(30):  # the field between the woods and us: its own lighter and darker patches
            blob(back, rng.uniform(0, w), rng.uniform(mid[0] + 6, h * 0.86), rng.uniform(6, 14),
                 [(46, 110, 66), (60, 128, 76), (74, 146, 78)], rng, rough=0.3, squash=0.3)
        for _ in range(7):  # bushes along it
            x, y = rng.uniform(0, w), rng.uniform(h * 0.72, h * 0.8)
            for k in range(3):
                blob(back, x + k * 4 - 4, y - (k % 2) * 2, rng.uniform(3.5, 5.5), LEAF[1:], rng, squash=0.85)
        berries = [((214, 58, 74), (150, 30, 52), (90, 140, 60)), ((240, 150, 190), (196, 96, 140), (90, 140, 60)),
                   ((90, 96, 210), (54, 58, 150), (90, 140, 60))]
        for x, ht in ((w * 0.07, h * 0.66), (w * 0.93, h * 0.7), (w * 0.24, h * 0.42), (w * 0.79, h * 0.46)):
            tree(back, x, h * 0.86 if ht > h * 0.5 else h * 0.72, ht, LEAF, rng, berries=berries)
        ground = h * 0.84
        g = [ground + 2 * math.sin(x / 9) for x in range(w)]
        ridge_fill(back, g, GRASS, 1)
        for _ in range(26):  # lighter patches in the grass
            blob(back, rng.uniform(0, w), rng.uniform(ground + 4, h), rng.uniform(5, 12),
                 GRASS[1:], rng, rough=0.3, squash=0.35)
        for _ in range(18):  # flowers
            x, y = int(rng.uniform(0, w)), int(rng.uniform(ground + 3, h - 2))
            col = rng.choice([(246, 120, 150), (250, 236, 120), (255, 255, 255)])
            for ox, oy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                back.set_at(((x + ox) % w, min(h - 1, y + oy)), col)
            back.set_at(((x) % w, min(h - 1, y - 1)), (255, 250, 220))
        self.back = sky
        self.layers = [Layer(self._clouds(5, h * 0.04, h * 0.3), 0, 0.03), Layer(back)]
        self.data["tufts"] = grass_tufts(rng, w, ground + 2, h, 70)
        self.data["leaves"] = [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(0.04, 0.09), rng.uniform(0, math.tau),
                                rng.choice(LEAF[3:])) for _ in range(14)]

    def _clouds(self, n, y0, y1, ramp=CLOUD, width=None):
        w = width or self.w * 2
        s = pygame.Surface((w, self.h), pygame.SRCALPHA)
        rng = self.rng
        for i in range(n):
            cw = int(rng.uniform(34, 70))
            img = cloud(rng, cw, int(cw * rng.uniform(0.36, 0.48)), ramp)
            x, y = int(i * w / n + rng.uniform(0, w / n * 0.5)), int(rng.uniform(y0, y1))
            s.blit(img, (x, y))
            if x + cw > w:
                s.blit(img, (x - w, y))
        return s

    def _tufts(self, c, t, color=GRASS[-1], dark=GRASS[1]):
        for x, y, hgt, ph in self.data["tufts"]:
            sway = round(math.sin(t * 0.05 + ph + x * 0.1) * 0.9)
            x, y = int(x), int(y)
            pygame.draw.line(c, dark, (x, y), (x - 1, y - hgt + 1))
            pygame.draw.line(c, color, (x + 1, y), (x + 1 + sway, y - hgt))
            pygame.draw.line(c, color, (x + 2, y), (x + 3 + sway, y - hgt + 1))

    def _leaves(self, c, t):
        for x0, y0, v, ph, col in self.data["leaves"]:
            y = (y0 + t * v * 4) % (self.h + 6) - 3
            x = (x0 + t * v * 2 + math.sin(t * 0.04 + ph) * 5) % self.w
            c.set_at((int(x), int(y)), col)
            c.set_at((int(x) + 1, int(y) + (1 if math.sin(t * 0.08 + ph) > 0 else 0)), col)

    def _live_meadow(self, c, t, s):
        self._tufts(c, t)
        self._leaves(c, t)

    # ================================================================ PLAINS: the runner (Ponyta Dash)
    def _build_plains(self):
        w, h, rng = self.w, self.h, self.rng
        back = pygame.Surface((w, h))
        gradient(back, (0, 0, w, h), [(92, 150, 220), (140, 190, 236), (210, 226, 236), (246, 222, 196)])
        sun = (int(w * 0.78), int(h * 0.3))
        for r, col in ((12, (250, 236, 200)), (9, (255, 246, 214)), (7, (255, 252, 236))):
            pygame.draw.circle(back, col, sun, r)
        self.back = back
        W2 = w * 2
        mts = pygame.Surface((W2, h), pygame.SRCALPHA)
        peaks = wave(W2, rng, h * 0.42, [(3, 9), (7, 5), (13, 2)])
        for x, top in enumerate(peaks):  # mountains: lit west faces, snow on the peaks
            slope = peaks[(x + 1) % W2] - peaks[x - 1]
            for y in range(int(top), int(h * 0.7)):
                d = y - top
                if d < 6 and top < h * 0.4:
                    col = (236, 242, 250) if slope > 0 else (196, 210, 232)
                else:
                    col = (132, 146, 188) if slope > 0 else (104, 118, 164)
                    if d > 20 and bayer(x, y) < (d - 20) / 30:
                        col = (118, 156, 176)
                mts.set_at((x, y), col)
        hills = pygame.Surface((W2, h), pygame.SRCALPHA)
        hh = wave(W2, rng, h * 0.6, [(4, 5), (9, 2), (17, 1)])
        ridge_fill(hills, hh, [(52, 112, 76), (68, 136, 78), (96, 164, 82), (134, 192, 96)], 1)
        for x in range(0, W2, 6):
            if rng.random() < 0.55:
                blob(hills, x, hh[x] + 1, rng.uniform(3, 5), [(40, 92, 70), (52, 112, 76), (70, 138, 80), (98, 166, 86)],
                     rng, squash=0.8, wrap=True)
        woods = pygame.Surface((W2, h), pygame.SRCALPHA)
        for i in range(14):
            x = i * W2 / 14 + rng.uniform(-6, 6)
            tree(woods, x, h * 0.78, rng.uniform(h * 0.26, h * 0.38), LEAF, rng, wrap=True)
        for x in range(0, W2, 5):
            blob(woods, x, h * 0.775, rng.uniform(3, 5.5), GRASS, rng, squash=0.7, wrap=True)
        self.layers = [Layer(self._clouds(6, h * 0.05, h * 0.25), 0.03, 0.02), Layer(mts, 0.06), Layer(hills, 0.16),
                       Layer(woods, 0.38)]

    # ================================================================ SKY: Pidgey Flight
    def _build_sky(self):
        w, h, rng = self.w, self.h, self.rng
        back = pygame.Surface((w, h))
        gradient(back, (0, 0, w, h), [(60, 104, 196), (98, 150, 226), (156, 196, 240), (238, 214, 206), (250, 196, 160)])
        self.back = back
        W2 = w * 2
        isles = pygame.Surface((W2, h), pygame.SRCALPHA)
        for i in range(5):  # far floating islands of rock and grass
            x, y, r = i * W2 / 5 + rng.uniform(0, 20), rng.uniform(h * 0.55, h * 0.75), rng.uniform(8, 14)
            for k in range(int(r * 1.4)):  # its rock underside, tapering
                ww = r * (1 - k / (r * 1.4)) ** 0.8
                pygame.draw.line(isles, ROCK[2] if k % 3 else ROCK[1], (x - ww, y + k), (x + ww * 0.8, y + k))
                pygame.draw.line(isles, ROCK[1], (x + ww * 0.5, y + k), (x + ww * 0.8, y + k))
            blob(isles, x, y - 1, r * 0.9, GRASS, rng, squash=0.35, wrap=True)
            tree(isles, x + r * 0.3, y, r * 1.5, LEAF, rng, wrap=True)
        far = self._clouds(7, h * 0.48, h * 0.85, [(186, 196, 226), (208, 216, 238), (232, 236, 248), (246, 248, 252)])
        near = self._clouds(5, h * 0.1, h * 0.6)
        self.layers = [Layer(far, 0.05, 0.01), Layer(isles, 0.12), Layer(near, 0.3, 0.02)]
        self.data["birds"] = [(rng.uniform(0, w), rng.uniform(h * 0.1, h * 0.4), rng.uniform(0, math.tau)) for _ in range(4)]

    def _live_sky(self, c, t, s):
        for x, y, ph in self.data["birds"]:  # far flocks, wings beating
            xx = int((x - t * 0.06 - s * 0.08) % self.w)
            up = math.sin(t * 0.25 + ph) > 0
            col = (70, 84, 120)
            c.set_at((xx, int(y)), col)
            c.set_at((xx - 1, int(y) - (1 if up else 0)), col)
            c.set_at((xx + 1, int(y) - (1 if up else 0)), col)

    # ================================================================ DOJO: Koga's walls
    def _build_dojo(self):
        w, h, rng = self.w, self.h, self.rng
        back = pygame.Surface((w, h))
        floor_y = int(h * 0.72)
        gradient(back, (0, 0, w, floor_y), [(46, 30, 44), (72, 46, 58), (96, 62, 64)])
        bay = 46
        for i, x0 in enumerate(range(-bay // 2 + 4, w, bay)):  # paper screens between posts
            sx, sy, sw, sh = x0 + 5, int(h * 0.16), bay - 10, int(floor_y - h * 0.2)
            x_in, x_out = max(0, sx), min(w, sx + sw)
            if x_out > x_in:
                gradient(back, (x_in, sy, x_out - x_in, sh), [(236, 206, 150), (226, 186, 128), (204, 156, 104)])
            for gx in range(sx, sx + sw, 7):
                pygame.draw.line(back, WOOD[1], (gx, sy), (gx, sy + sh - 1))
            for gy in range(sy, sy + sh, 9):
                pygame.draw.line(back, WOOD[1], (sx, gy), (sx + sw - 1, gy))
            pygame.draw.rect(back, WOOD[2], (sx - 1, sy - 1, sw + 2, sh + 2), 1)
            for px in (x0, x0 + bay - 5):  # the posts
                pygame.draw.rect(back, WOOD[1], (px, 0, 5, floor_y))
                pygame.draw.line(back, WOOD[3], (px, 0), (px, floor_y))
                pygame.draw.line(back, WOOD[0], (px + 4, 0), (px + 4, floor_y))
        pygame.draw.rect(back, WOOD[1], (0, 0, w, int(h * 0.1)))  # the beam overhead
        pygame.draw.line(back, WOOD[3], (0, int(h * 0.1)), (w, int(h * 0.1)))
        for x in range(0, w, 3):
            if rng.random() < 0.3:
                pygame.draw.line(back, WOOD[0], (x, 2), (x + rng.randint(4, 12), 2))
        for y in range(floor_y, h):  # the floor: boards in perspective light
            t = (y - floor_y) / (h - floor_y)
            row = int(t * 6)
            for x in range(w):
                col = WOOD[3] if (row % 2 == 0) else WOOD[2]
                if (x + row * 17) % 40 == 0:
                    col = WOOD[1]
                if bayer(x, y) < t * 0.5:
                    col = mix(col, WOOD[1], 0.5)
                back.set_at((x, y), col)
        pygame.draw.line(back, WOOD[0], (0, floor_y), (w, floor_y))
        self.back = back
        self.data["lanterns"] = [(x, int(h * 0.22)) for x in range(bay - 2, w, bay * 2)]
        self.data["motes"] = [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(0, math.tau)) for _ in range(20)]

    def _live_dojo(self, c, t, s):
        for x, y in self.data["lanterns"]:
            flick = 0.85 + 0.15 * math.sin(t * 0.3 + x) * math.sin(t * 0.13 + x * 2)
            self._glow(c, (255, 190, 90), int(60 * flick), [("c", (x, y + 6, 16 * flick))])
            pygame.draw.line(c, WOOD[0], (x, int(self.h * 0.1)), (x, y))
            pygame.draw.ellipse(c, (200, 60, 46), (x - 4, y, 9, 12))
            pygame.draw.ellipse(c, (240, 120, 70), (x - 3, y + 1, 5, 9))
            pygame.draw.line(c, (255, 220, 140), (x - 1, y + 3), (x - 1, y + 7))
            pygame.draw.line(c, WOOD[0], (x - 3, y), (x + 4, y))
            pygame.draw.line(c, WOOD[0], (x - 3, y + 11), (x + 4, y + 11))
        for x0, y0, ph in self.data["motes"]:  # dust in the lantern light
            x = (x0 + math.sin(t * 0.01 + ph) * 8) % self.w
            y = (y0 - t * 0.03) % self.h
            if math.sin(t * 0.05 + ph) > 0.2:
                c.set_at((int(x), int(y)), (255, 226, 170))

    # ================================================================ STAGE: Rhythm Tiles
    def _build_stage(self):
        w, h, rng = self.w, self.h, self.rng
        back = pygame.Surface((w, h))
        gradient(back, (0, 0, w, h), [(14, 10, 34), (30, 18, 60), (54, 26, 84), (28, 16, 50)])
        floor_y = int(h * 0.74)
        for x in range(0, w, 2):  # the curtain's folds at the back
            k = (x // 2) % 6
            col = [(70, 20, 50), (96, 28, 64), (124, 38, 76), (96, 28, 64), (70, 20, 50), (52, 14, 40)][k]
            pygame.draw.line(back, col, (x, 0), (x, floor_y - 30))
            pygame.draw.line(back, col, (x + 1, 0), (x + 1, floor_y - 30))
        for y in range(floor_y - 30, floor_y - 26):
            for x in range(w):
                if bayer(x, y) < (y - floor_y + 30) / 4:
                    back.set_at((x, y), (30, 18, 60))
        for side in (0, 1):  # speaker stacks
            x0 = 6 if side == 0 else w - 30
            for j in range(3):
                r = pygame.Rect(x0, floor_y - 22 - j * 22, 24, 21)
                pygame.draw.rect(back, METAL[1], r)
                pygame.draw.rect(back, METAL[3], r, 1)
                for cy, rr in ((r.y + 6, 4), (r.y + 15, 5)):
                    pygame.draw.circle(back, METAL[0], (r.centerx, cy), rr)
                    pygame.draw.circle(back, METAL[2], (r.centerx, cy), rr, 1)
                    back.set_at((r.centerx - 1, cy - 1), METAL[4])
        gradient(back, (0, floor_y, w, h - floor_y), [(70, 46, 90), (46, 30, 64), (24, 16, 40)])
        for x in range(0, w, 12):
            pygame.draw.line(back, (90, 62, 110), (x, floor_y), (x - (x - w // 2) // 3, h))
        pygame.draw.line(back, (150, 110, 170), (0, floor_y), (w, floor_y))
        self.back = back
        self.data["floor"] = floor_y
        self.data["crowd"] = [(x, rng.uniform(0, math.tau), rng.randint(5, 8)) for x in range(-2, w + 4, 5)]

    def _live_stage(self, c, t, s):
        w, h, fy = self.w, self.h, self.data["floor"]
        beams = []
        for i, col in enumerate(((255, 90, 160), (90, 200, 255), (255, 220, 90), (150, 255, 140))):
            ox = w * (0.15 + 0.23 * i)
            ang = math.sin(t * 0.02 + i * 1.7) * 0.5
            tx = ox + math.sin(ang) * h * 1.2
            self._glow(c, col, 44 + int(18 * math.sin(t * 0.1 + i)),
                       [("poly", [(ox - 2, 0), (ox + 2, 0), (tx + 16, fy), (tx - 16, fy)])])
            beams.append((tx, col))
            pygame.draw.rect(c, METAL[2], (ox - 3, 0, 7, 4))
            pygame.draw.rect(c, col, (ox - 2, 3, 5, 2))
        for tx, col in beams:  # where they land on the floor
            pygame.draw.ellipse(c, mix(col, (255, 255, 255), 0.3), (tx - 14, fy - 1, 28, 5))
        for x, ph, hgt in self.data["crowd"]:  # the crowd in front, bobbing to the beat
            bob = 1 if math.sin(t * 0.21 + ph) > 0 else 0
            top = h - hgt - bob
            pygame.draw.rect(c, (10, 6, 22), (x, top + 3, 5, hgt + 2))
            pygame.draw.circle(c, (10, 6, 22), (x + 2, top + 1), 2)
            if math.sin(t * 0.07 + ph * 3) > 0.92:  # a raised glow stick
                pygame.draw.line(c, (140, 255, 200), (x + 4, top - 1), (x + 6, top - 5))

    # ================================================================ STADIUM: Gym Pong; ARENA: Type Clash
    def _stands(self, back, top, bottom, crowd_cols, wall, rng):
        w = self.w
        for y in range(top, bottom):
            row = (y - top) // 5
            for x in range(w):
                col = wall[1] if (y - top) % 5 == 0 else wall[0]
                back.set_at((x, y), col)
        seats = []
        for row in range((bottom - top) // 5):
            for x in range(1 + (row % 2) * 2, w, 4):
                if rng.random() < 0.85:
                    seats.append((x, top + row * 5 + 1, rng.choice(crowd_cols), rng.uniform(0, math.tau)))
        return seats

    def _build_stadium(self, night=False):
        w, h, rng = self.w, self.h, self.rng
        back = pygame.Surface((w, h))
        sky = ([(14, 18, 46), (30, 36, 84), (70, 60, 116), (150, 90, 120)] if night
               else [(86, 146, 220), (130, 184, 236), (190, 220, 240)])
        gradient(back, (0, 0, w, int(h * 0.3)), sky)
        crowd = [(230, 90, 80), (90, 140, 230), (250, 210, 90), (240, 240, 240), (120, 200, 120), (230, 130, 190)]
        wall = [(70, 74, 96), (92, 98, 124)] if not night else [(40, 36, 64), (58, 52, 86)]
        self.data["seats"] = self._stands(back, int(h * 0.3), int(h * 0.62), crowd, wall, rng)
        pygame.draw.rect(back, (200, 60, 60) if not night else (120, 70, 170), (0, int(h * 0.62), w, 4))
        pygame.draw.line(back, (255, 255, 255), (0, int(h * 0.62)), (w, int(h * 0.62)))
        for x in range(8, w, 40):  # sponsor boards along the wall
            pygame.draw.rect(back, (250, 250, 250), (x, int(h * 0.62) + 1, 20, 2))
        fy = int(h * 0.64)
        field = [(70, 150, 72), (86, 170, 78)] if not night else [(150, 116, 86), (166, 132, 96)]
        for y in range(fy, h):
            for x in range(w):
                stripe = (x // 16) % 2 if not night else ((y - fy) // 6) % 2
                col = field[stripe]
                if bayer(x, y) < (y - fy) / (h - fy) * 0.3:
                    col = mix(col, (40, 40, 40), 0.25)
                back.set_at((x, y), col)
        pygame.draw.ellipse(back, (240, 240, 240), (w // 2 - 30, fy + (h - fy) // 2 - 8, 60, 18), 1)
        pygame.draw.line(back, (240, 240, 240), (w // 2, fy), (w // 2, h))
        for x in (int(w * 0.1), int(w * 0.9)):  # floodlight towers
            pygame.draw.line(back, METAL[2], (x, 2), (x, int(h * 0.3)))
            pygame.draw.rect(back, METAL[1], (x - 7, 0, 15, 7))
        if night:
            for _ in range(40):
                back.set_at((rng.randrange(w), rng.randrange(int(h * 0.2))), (230, 230, 255))
        self.back = back
        self.data["lights"] = [(int(w * 0.1), 3), (int(w * 0.9), 3)]
        self.data["night"] = night
        self.layers = [] if night else [Layer(self._clouds(4, 0, h * 0.1), 0, 0.02)]

    def _build_arena(self):
        self._build_stadium(night=True)

    def _live_stadium(self, c, t, s):
        for x, y, col, ph in self.data["seats"]:  # the crowd, standing up and sitting down
            up = 1 if math.sin(t * 0.09 + ph) > 0.6 else 0
            c.set_at((x, y - up), col)
            c.set_at((x + 1, y - up), col)
            c.set_at((x, y + 1 - up), mix(col, (0, 0, 0), 0.35))
            c.set_at((x, y + 2), (30, 30, 40))
        for x, y in self.data["lights"]:
            for k in range(-6, 7, 3):
                on = math.sin(t * 0.05 + k) > -0.8
                c.set_at((x + k, y), (255, 255, 230) if on else (200, 200, 170))
            if self.data["night"]:
                self._glow(c, (255, 250, 210), 34, [("poly", [(x - 7, y), (x + 7, y), (self.w // 2 + 60, self.h),
                                                              (self.w // 2 - 60, self.h)])])
        flash_seed = int(t // 9)
        r = random.Random(flash_seed)
        for _ in range(3):  # camera flashes in the stands
            if r.random() < 0.5:
                x, y = r.randrange(self.w), r.randrange(int(self.h * 0.32), int(self.h * 0.6))
                c.set_at((x, y), (255, 255, 255))
                c.set_at((x + 1, y), (255, 255, 220))

    _live_arena = _live_stadium

    # ================================================================ POWER: Voltorb Field, Surge's cans
    def _build_power(self):
        w, h, rng = self.w, self.h, self.rng
        back = pygame.Surface((w, h))
        panel = 30
        for y in range(h):  # riveted steel plates
            for x in range(w):
                px, py = x % panel, y % 24
                col = METAL[2]
                if px == 0 or py == 0:
                    col = METAL[1]
                elif px == 1 or py == 1:
                    col = METAL[3]
                elif bayer(x, y) < 0.12 + 0.2 * (py / 24):
                    col = mix(METAL[2], METAL[1], 0.5)
                back.set_at((x, y), col)
        for x in range(0, w, panel):
            for y in range(0, h, 24):
                for rx, ry in ((3, 3), (panel - 4, 3), (3, 20), (panel - 4, 20)):
                    back.set_at((x + rx, y + ry), METAL[4])
                    back.set_at((x + rx + 1, y + ry + 1), METAL[0])
        for y in (int(h * 0.22), int(h * 0.3)):  # pipes along the wall
            for k, col in enumerate((METAL[0], (178, 120, 60), (214, 160, 90), (240, 200, 130), (178, 120, 60), METAL[0])):
                pygame.draw.line(back, col, (0, y + k), (w, y + k))
            for x in range(10, w, 52):
                pygame.draw.rect(back, METAL[1], (x, y - 1, 4, 8))
        stripe_y = int(h * 0.86)
        for y in range(stripe_y, h):  # a hazard stripe along the floor
            for x in range(w):
                back.set_at((x, y), (236, 190, 40) if ((x + y) // 5) % 2 else (34, 30, 30))
        pygame.draw.line(back, METAL[0], (0, stripe_y), (w, stripe_y))
        coils = []
        for x in (int(w * 0.06), int(w * 0.94)):  # coils at the sides, sparking between
            for k in range(14):
                y = int(h * 0.38) + k * 2
                pygame.draw.line(back, (200, 120, 60) if k % 2 else (150, 84, 40), (x - 6, y), (x + 6, y))
                pygame.draw.line(back, (230, 170, 100), (x - 6, y), (x - 4, y))
            pygame.draw.rect(back, METAL[1], (x - 8, int(h * 0.38) + 28, 17, 8))
            pygame.draw.circle(back, METAL[3], (x, int(h * 0.36)), 4)
            coils.append((x, int(h * 0.36)))
        self.back = back
        self.data["coils"] = coils
        self.data["leds"] = [(rng.randrange(w), rng.choice((int(h * 0.12), int(h * 0.5), int(h * 0.7))),
                              rng.choice(((255, 60, 60), (60, 255, 120), (255, 220, 60))), rng.uniform(0, math.tau))
                             for _ in range(18)]

    def _live_power(self, c, t, s):
        for x, y, col, ph in self.data["leds"]:
            on = math.sin(t * 0.08 + ph * 4) > 0
            pygame.draw.rect(c, METAL[0], (x - 1, y - 1, 4, 4))
            pygame.draw.rect(c, col if on else mix(col, (0, 0, 0), 0.7), (x, y, 2, 2))
        for x, y in self.data["coils"]:
            r = random.Random(int(t // 3) + x)
            if r.random() < 0.6:  # a crackling arc off the coil
                pts = [(x, y)]
                for k in range(5):
                    pts.append((x + r.randint(-6, 6), y - 3 - k * 3))
                self._glow(c, (120, 200, 255), 70, [("c", (x, y - 6, 9))])
                pygame.draw.lines(c, (255, 255, 160), False, pts)
                pygame.draw.lines(c, (140, 220, 255), False, [(px + 1, py) for px, py in pts])

    # ================================================================ VOLCANO: Blaine's quiz
    def _build_volcano(self):
        w, h, rng = self.w, self.h, self.rng
        back = pygame.Surface((w, h))
        gradient(back, (0, 0, w, h), [(26, 14, 20), (48, 22, 26), (86, 34, 30), (150, 60, 34)])
        cave = [(36, 22, 28), (56, 34, 38), (82, 52, 50), (112, 72, 60)]
        for side in (0, 1):  # rock walls closing in at the sides
            edge = wave(h, rng, w * 0.16, [(2, 8), (5, 3), (11, 1.5)])
            for y in range(h):
                e = int(edge[y])
                for x in range(e):
                    xx = x if side == 0 else w - 1 - x
                    d = e - x
                    col = cave[3] if d < 2 else cave[2] if d < 5 else cave[1] if d < 14 + 3 * bayer(xx, y) else cave[0]
                    back.set_at((xx, y), col)
        top = wave(w, rng, h * 0.08, [(3, 4), (7, 2)])
        for x in range(w):  # the ceiling, with stalactites
            for y in range(int(top[x])):
                back.set_at((x, y), cave[0] if y < top[x] - 2 else cave[2])
        for _ in range(10):
            x, ln = rng.randrange(w), rng.randint(4, 12)
            for k in range(ln):
                ww = max(0, int((ln - k) / 3))
                pygame.draw.line(back, cave[1], (x - ww, int(top[x]) + k), (x + ww, int(top[x]) + k))
        for x in (int(w * 0.3), int(w * 0.72)):  # lava falls
            pygame.draw.rect(back, (200, 70, 30), (x - 3, int(top[x]), 7, int(h * 0.8)))
        lava_y = int(h * 0.8)
        self.data["lava_y"] = lava_y
        self.data["falls"] = (int(w * 0.3), int(w * 0.72))
        self.data["top"] = [int(top[x]) for x in (int(w * 0.3), int(w * 0.72))]
        self.data["embers"] = [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(0.15, 0.35), rng.uniform(0, math.tau))
                               for _ in range(30)]
        lava = pygame.Surface((w * 2, h - lava_y), pygame.SRCALPHA)
        lc = [(176, 40, 24), (226, 84, 30), (252, 150, 40), (255, 214, 90)]
        for y in range(h - lava_y):
            for x in range(w * 2):
                v = 0.5 + 0.25 * math.sin(math.tau * x / w * 3 + y * 0.5) + 0.2 * math.sin(math.tau * x / w * 7 - y)
                v -= y / (h - lava_y) * 0.4
                v += (bayer(x, y) - 0.5) * 0.25
                lava.set_at((x, y), lc[max(0, min(3, int(v * 4)))])
        for x in range(w * 2):
            lava.set_at((x, 0), lc[3])
        self.back = back
        self.front = [Layer(lava, 0, 0.05, lava_y)]

    def _live_volcano(self, c, t, s):
        for x, top in zip(self.data["falls"], self.data["top"]):  # the falls' flowing light
            for y in range(top, self.data["lava_y"]):
                k = (y - int(t * 0.8)) % 8
                col = (255, 200, 80) if k < 2 else (236, 110, 40) if k < 5 else (200, 70, 30)
                pygame.draw.line(c, col, (x - 2, y), (x + 2, y))
            self._glow(c, (255, 120, 40), 40, [("c", (x, self.data["lava_y"], 14))])
        for x0, y0, v, ph in self.data["embers"]:  # embers rising from the lava
            y = (y0 - t * v) % self.h
            x = (x0 + math.sin(t * 0.03 + ph) * 4) % self.w
            col = (255, 200, 90) if math.sin(t * 0.2 + ph) > 0 else (255, 120, 50)
            c.set_at((int(x), int(y)), col)

    # ================================================================ COSMOS: Sabrina's warps
    def _build_cosmos(self):
        w, h, rng = self.w, self.h, self.rng
        back = pygame.Surface((w, h))
        gradient(back, (0, 0, w, h), [(10, 6, 30), (30, 14, 60), (64, 26, 96), (30, 14, 64)])
        for _ in range(7):  # nebulae: soft dithered clouds of colour
            cx, cy, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(18, 40)
            col = rng.choice([(150, 70, 200), (220, 90, 180), (90, 110, 230)])
            for y in range(int(cy - r), int(cy + r)):
                for x in range(int(cx - r), int(cx + r)):
                    d = math.hypot(x - cx, (y - cy) * 1.4) / r
                    if d < 1 and bayer(x, y) < (1 - d) * 0.55 and 0 <= x < w and 0 <= y < h:
                        back.set_at((x, y), mix(back.get_at((x, y))[:3], col, 0.35))
        for _ in range(110):
            back.set_at((rng.randrange(w), rng.randrange(h)), rng.choice([(150, 140, 200), (200, 190, 240)]))
        self.back = back
        self.data["stars"] = [(rng.randrange(w), rng.randrange(h), rng.uniform(0, math.tau)) for _ in range(26)]
        self.data["rings"] = [(rng.uniform(0.15, 0.85) * w, rng.uniform(0.2, 0.85) * h, rng.uniform(0, math.tau))
                              for _ in range(4)]
        self.data["motes"] = [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(0.05, 0.15), rng.uniform(0, math.tau))
                              for _ in range(24)]

    def _star(self, c, x, y, t, ph, col=(255, 255, 255)):
        b = math.sin(t * 0.06 + ph)
        if b > 0.3:
            c.set_at((x, y), col)
            if b > 0.85:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    c.set_at((x + dx, y + dy), mix(col, (120, 110, 190), 0.4))
        else:
            c.set_at((x, y), (150, 140, 200))

    def _live_cosmos(self, c, t, s):
        for x, y, ph in self.data["stars"]:
            self._star(c, x, y, t, ph)
        for x, y, ph in self.data["rings"]:  # psychic rings, slowly pulsing out
            r = (t * 0.12 + ph * 10) % 26
            col = (230, 160, 255) if r < 18 else (140, 90, 200)
            pygame.draw.ellipse(c, col, (x - r, y - r * 0.45, r * 2, r * 0.9), 1)
        for x0, y0, v, ph in self.data["motes"]:
            y = (y0 - t * v) % self.h
            x = (x0 + math.sin(t * 0.02 + ph) * 6) % self.w
            c.set_at((int(x), int(y)), (255, 180, 250) if math.sin(t * 0.1 + ph) > 0 else (180, 130, 240))

    # ================================================================ NIGHT: Pokemon Match
    def _build_night(self):
        w, h, rng = self.w, self.h, self.rng
        back = pygame.Surface((w, h))
        gradient(back, (0, 0, w, h), [(8, 12, 34), (18, 28, 64), (36, 50, 96), (58, 70, 112)])
        mx, my = int(w * 0.82), int(h * 0.2)
        for r, col in ((14, (40, 52, 96)), (11, (60, 70, 116))):
            pygame.draw.circle(back, col, (mx, my), r)
        blob(back, mx, my, 8, [(190, 196, 210), (220, 224, 230), (246, 246, 236)], rng, rough=0.02, light=(-0.7, -0.7))
        for dx, dy in ((2, -1), (-3, 2), (1, 3)):
            back.set_at((mx + dx, my + dy), (190, 196, 210))
        hills = wave(w, rng, h * 0.7, [(2, 4), (5, 2)])
        ridge_fill(back, hills, [(14, 26, 40), (20, 36, 50), (28, 48, 60), (40, 62, 72)], 1)
        for x in range(0, w, 7):
            tree(back, x + rng.uniform(-3, 3), hills[x % w] + 6, rng.uniform(h * 0.18, h * 0.34), LEAF_NIGHT, rng,
                 bark=[(12, 14, 24), (18, 22, 34), (26, 30, 44), (36, 40, 56)])
        ground = int(h * 0.88)
        g = [ground + math.sin(x / 11) for x in range(w)]
        ridge_fill(back, g, [(16, 34, 40), (24, 50, 48), (34, 68, 56), (50, 90, 64)], 1)
        self.back = back
        self.data["stars"] = [(rng.randrange(w), rng.randrange(int(h * 0.55)), rng.uniform(0, math.tau)) for _ in range(40)]
        self.data["flies"] = [(rng.uniform(0, w), rng.uniform(h * 0.5, h * 0.95), rng.uniform(0, math.tau)) for _ in range(16)]
        self.data["tufts"] = grass_tufts(rng, w, ground + 2, h, 40)

    def _live_night(self, c, t, s):
        for x, y, ph in self.data["stars"]:
            self._star(c, x, y, t, ph, (230, 236, 255))
        self._tufts(c, t, (60, 104, 70), (24, 50, 48))
        for x0, y0, ph in self.data["flies"]:  # fireflies
            x = (x0 + math.sin(t * 0.013 + ph) * 14) % self.w
            y = y0 + math.sin(t * 0.021 + ph * 2) * 6
            b = math.sin(t * 0.05 + ph * 3)
            if b > -0.2:
                self._glow(c, (200, 255, 120), int(40 + 50 * b), [("c", (x, y, 3))])
                c.set_at((int(x), int(y)), (240, 255, 170))
