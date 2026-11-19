"""Soaring in the Sky, 3D (Jordan, 11-14: "baked 2.5D, phone-safe"): fly Mega Latios / Latias over Omega Ruby's
own Hoenn, seen from behind as in ORAS. Pygame only: no 3D library, so it runs in Pydroid as the rest does.

How it's drawn: the ground is the game's sky map baked flat from above (assets/soaring3d/ground*.jpg, made from
Jordan's Omega Ruby file by kanto_handoff/oras_rom_tools/bake_soaring3d.py) and laid out in perspective a row at a
time ("Mode 7"): each frame a square of the ground round you is turned so you face up, and every screen row below
the horizon is one strip of it, stretched. Nearer rows read a finer picture, farther rows coarser ones. The Eon is
Jordan's back sprite (the 2D version's), leaning into turns; or, with EON_LOOK = "model", one of the baked
pictures of Omega Ruby's model from behind (5 bank x 3 pitch angles). Spots, the rift, the storm
cloud and wild Pokemon are pictures standing in the world, smaller the farther they are.

Controls: Left / Right turn, Up / Down climb and dive, hold Space (or FAST) to speed up; with a finger or the mouse,
hold where you want to go (left/right turns, high climbs, low dives). LAND (or Esc) sets you down at the nearest town
you've been to. Fly over a Mirage place to land there; into the rift or the storm cloud to meet its legend; into a
flock to battle one of it.

This is the HOENN_SOARING_IN_THE_SKY area's screen (dungeon.dungeon_for hands it out): a route underneath, so
battles are the route's own and come back here, the flight going on where it was. Places: src/world/soaring3d.py.
"""
import json
import math
import os
import random
import time

import pygame

from src.config import FPS
from src.states.overworld.route import PlayState
from src.ui import theme
from src.world import soaring3d as S3

FOV = 70.0                       # degrees across
SPEEDS = (90.0, 150.0, 260.0)    # world units a frame: slow, cruising, fast (25 frames a second)
TURN = 2.6                       # degrees a frame at full turn
CLIMB = 45.0                     # world units a frame at full climb
ALT_MIN, ALT_MAX = 700.0, 4200.0
CROP = 320                       # half-size of the turned square of ground, in that level's pixels
FAR_CROP = 320
REACH = 0.72                     # how much of the square a row may use (the rest: room to move before turning anew)
HAZE = (176, 206, 236)
SEA = (40, 108, 184)
HUD_H = 76
SPRITE_SCALE = 5                 # Jordan's 31 x 30 back sprites, five times (as in the 2D version)
SPRITE_ROLL = 22.0               # degrees the sprite leans at full turn
WILD_EVERY = (FPS * 5, FPS * 9)
WALL_ALTS = (300, 1600, 2900, 4200)  # heights of the cloud bank's rows (it stands from the ground to above ALT_MAX)
WALL_SEEN = 32000                    # how far off the cloud bank is drawn
BANNER_T = FPS * 4                   # how long a region's name shows when you fly into it
_cache = {}


def _load(game, name, alpha=True):
    key = ("img", name)
    if key not in _cache:
        try:
            img = pygame.image.load(os.path.join(game.assets.assets_dir, "soaring3d", name))
            _cache[key] = img.convert_alpha() if alpha else img.convert()
        except (pygame.error, FileNotFoundError):
            _cache[key] = None
    return _cache[key]


def storm_picture(seed=7, w=320, h=180):
    """A black storm cloud of our own: dark round puffs, a lighter top edge, soft at the rim."""
    rng = random.Random(seed)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    puffs = [(rng.randint(w // 6, 5 * w // 6), rng.randint(h // 3, 2 * h // 3), rng.randint(h // 5, h // 3))
             for _ in range(11)]
    for col, dy, grow in (((30, 26, 44, 120), 6, 8), ((58, 52, 78, 235), 0, 0), ((92, 86, 116, 235), -5, -9)):
        for x, y, r in puffs:
            pygame.draw.circle(s, col, (x, y + dy), max(2, r + grow))
    return s


def rift_picture(size=256):
    """The Dimensional Rift, ours: a dark hole with violet arms curling into it."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size / 2
    for i in range(36, 0, -1):            # a soft violet glow, darker inwards
        k = i / 36
        pygame.draw.circle(s, (int(40 + 120 * k), int(10 + 40 * k), int(70 + 150 * k), int(200 * (1 - k) + 30)),
                           (int(c), int(c)), int(c * k * 0.95))
    for arm in range(4):                  # spiral arms
        pts = []
        for j in range(40):
            t = j / 39
            a = arm * math.pi / 2 + t * 4.2
            r = c * 0.92 * (1 - t) + 6
            pts.append((c + math.cos(a) * r, c + math.sin(a) * r))
        pygame.draw.lines(s, (210, 170, 255, 210), False, pts, 5)
        pygame.draw.lines(s, (90, 40, 150, 230), False, pts, 2)
    pygame.draw.circle(s, (6, 0, 14, 255), (int(c), int(c)), int(c * 0.2))
    return s


def fit_text(fonts, texts, room, sizes=("label", "caption")):
    """(font, text) of the first of these texts that fits `room` pixels in the first font size it fits; else the last
    text cut short with "...", in the smallest size."""
    for name in sizes:
        for t in texts:
            if fonts[name].size(t)[0] <= room:
                return fonts[name], t
    font, t = fonts[sizes[-1]], texts[-1]
    while t and font.size(t + "...")[0] > room:
        t = t[:-1]
    return font, t.rstrip() + "..."


def lightning_bolts(game):
    """The forked lightning bolts in Thundercage's frames (assets/move_animations/graphics/GEN8- Thundercage.png, 192-pixel
    cells: the three that strike down out of a glow, and the two thin ones), each cut to its own box."""
    key = ("bolts",)
    if key not in _cache:
        out = []
        try:
            sheet = pygame.image.load(os.path.join(game.assets.assets_dir, "move_animations", "graphics",
                                                   "GEN8- Thundercage.png")).convert_alpha()
            for col, row in ((1, 1), (2, 1), (3, 1), (3, 0), (4, 0)):
                cell = sheet.subsurface((col * 192, row * 192, 192, 192))
                out.append(cell.subsurface(cell.get_bounding_rect()).copy())
        except (pygame.error, FileNotFoundError, ValueError):
            out = []
        _cache[key] = out
    return _cache[key]


def _soft_disc(d):
    """A white disc, opaque in the middle and fading out to its rim (to round off a square of cloud texture)."""
    key = ("disc", d)
    if key not in _cache:
        s = pygame.Surface((d, d), pygame.SRCALPHA)
        for i in range(24, 0, -1):
            k = i / 24
            s_a = int(255 * min(1.0, (1 - k) * 2.2))
            pygame.draw.circle(s, (255, 255, 255, s_a), (d // 2, d // 2), max(1, int(d / 2 * k)))
        _cache[key] = s
    return _cache[key]


def oras_storm_picture(game, seed=7, w=320, h=180):
    """The black storm cloud from Omega Ruby's own thundercloud textures (its cloud masses, darkened as the game tints
    them), in round puffs with a lighter top; None if they're missing."""
    texs = [t for t in (_load(game, "oras_kumo03.png"), _load(game, "oras_kumo01.png")) if t is not None]
    if not texs:
        return None
    rng = random.Random(seed)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    puffs = [(rng.randint(w // 6, 5 * w // 6), rng.randint(h // 3, 2 * h // 3), rng.randint(h // 5, h // 3))
             for _ in range(11)]
    for col, dy, grow in (((34, 30, 48, 170), 8, 10), ((64, 58, 86, 255), 0, 2), ((110, 104, 138, 235), -6, -8)):
        for x, y, r in puffs:
            d = max(4, 2 * (r + grow) + 16)
            p = pygame.transform.smoothscale(rng.choice(texs), (d, d))
            p.blit(_soft_disc(d), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            p.fill(col, special_flags=pygame.BLEND_RGBA_MULT)
            s.blit(p, (x - d // 2, y + dy - d // 2))
    return s


def oras_rift_layers(game):
    """(glow, streaks) for the Dimensional Rift: Essentials' portal glow and Omega Ruby's rift streaks tinted violet;
    None if missing."""
    glow, uv = _load(game, "portal_glow.png", alpha=False), _load(game, "oras_rift_streaks.png")
    if glow is None or uv is None:
        return None
    st = pygame.transform.smoothscale(uv, (256, 256))
    st.fill((200, 130, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
    st2 = pygame.transform.rotate(st, 90)                 # (a second turn of streaks: fuller)
    st.blit(st2, st2.get_rect(center=(128, 128)))
    st.blit(_soft_disc(256), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return glow, st


def mount(game):
    """(species id, name) of the Eon you ride: one in your party first, else your version's, else Latios."""
    story = game.story_manager
    for p in getattr(story, "player_team", []) or []:
        if getattr(p, "id", None) in (380, 381):
            return p.id, ("Latias" if p.id == 380 else "Latios")
    try:
        from src.world import hoenn
        v = hoenn.info(story)
        if v and v.get("eon_id") in (380, 381):
            return v["eon_id"], v["eon"]
    except Exception:
        pass
    return 381, "Latios"


def follower(game, pid, size, row=0, frame=0):
    """A flying Pokemon in the world: its following-Pokemon sheet (assets/dungeon/followers, 4 x 4: rows down, left,
    right, up), cropped to the box all its frames share, at this height; the party icon if it has no sheet."""
    key = ("follower", pid)
    if key not in _cache:
        data = None
        path = os.path.join(game.assets.assets_dir, "dungeon", "followers", f"{int(pid)}.png")
        if os.path.isfile(path):
            img = pygame.image.load(path).convert_alpha()
            cw, ch = img.get_width() // 4, img.get_height() // 4
            box = None
            for c in range(4):
                for r in range(4):
                    bb = img.subsurface((c * cw, r * ch, cw, ch)).get_bounding_rect()
                    if bb.w and bb.h:
                        box = bb if box is None else box.union(bb)
            data = (img, cw, ch, box)
        _cache[key] = data
    data = _cache[key]
    if not data:
        from src.minigames.base import icon
        return icon(game, pid, size)
    img, cw, ch, box = data
    cell = img.subsurface((frame % 4 * cw + box.x, row * ch + box.y, box.w, box.h))
    return pygame.transform.scale(cell, (max(2, int(size * box.w / box.h)), max(2, int(size))))


class Level:
    """One picture of the ground (world rect, units per pixel) and its turned square, kept while it still fits."""

    def __init__(self, img, rect, crop, sea=None):
        self.img = img
        self.sea = sea or SEA
        self.x0, self.z0, x1, z1 = rect
        self.s = (x1 - self.x0) / img.get_width()
        self.crop = crop
        self.surf = None      # the turned square
        self.at = None        # (world x, z, heading) it was turned at

    def turned(self, x, z, heading):
        if self.at is not None:
            ox, oz, oh = self.at
            if abs(oh - heading) < 0.01 and math.hypot(x - ox, z - oz) < self.crop * self.s * (0.95 - REACH):
                return self.surf      # (still turned the right way, and you haven't flown off it)
        c = self.crop
        sq = pygame.Surface((2 * c, 2 * c))
        sq.fill(self.sea)
        px, pz = (x - self.x0) / self.s, (z - self.z0) / self.s
        if isinstance(self.img, Tiled):
            self.img.draw(sq, (c - int(px), c - int(pz)))
        else:
            sq.blit(self.img, (c - int(px), c - int(pz)))
        self.surf = pygame.transform.rotate(sq, heading)
        self.at = (int(px) * self.s + self.x0, int(pz) * self.s + self.z0, heading)  # (the pixel it's centred on)
        return self.surf


class Tiled:
    """A ground picture too big to keep whole on a phone (the world's finest two): 512-pixel tiles
    (assets/soaring3d/world/<name>_<col>_<row>.png), read when the flight first needs them, clouded as they're read,
    and dropped again once far away."""
    KEEP = 20

    def __init__(self, folder, name, size, tile, cover, level):
        self.folder, self.name, self.size, self.tile = folder, name, size, tile
        self.cover, self.level = cover, level
        self.tiles = {}

    def get_width(self):
        return self.size[0]

    def get_height(self):
        return self.size[1]

    def _tile(self, col, row):
        key = (col, row)
        if key not in self.tiles:
            try:
                img = pygame.image.load(os.path.join(self.folder, f"{self.name}_{col}_{row}.png")).convert()
            except (pygame.error, FileNotFoundError):
                img = None
            if img is not None and self.cover is not None:
                self.cover.cover(img, self.level, col * self.tile, row * self.tile)
            if len(self.tiles) >= self.KEEP:            # (the oldest one goes)
                self.tiles.pop(next(iter(self.tiles)))
            self.tiles[key] = img
        return self.tiles[key]

    def draw(self, dest, at):
        """Blit the picture onto dest with its top-left at `at` (as dest.blit would), reading only the tiles that show."""
        ax, ay = at
        t = self.tile
        c0, c1 = max(0, -ax // t), min((self.size[0] - 1) // t, (dest.get_width() - ax) // t)
        r0, r1 = max(0, -ay // t), min((self.size[1] - 1) // t, (dest.get_height() - ay) // t)
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                img = self._tile(col, row)
                if img is not None:
                    dest.blit(img, (ax + col * t, ay + row * t))


class Clouds:
    """Clouds over every part of the world you haven't been to (Jordan, 11-18): each patch of ground belongs to a town
    (world/cells.png, its town's number per pixel; 255 = no town's, open sea far from all); a patch stays under
    clouds until you've been to its town. The ground pictures are clouded once, as they're read (no cost a frame):
    the cloud-tops are Omega Ruby's own (its cloud mass and its cloud-from-above), faded in over the edge."""
    BASE = (206, 218, 238)

    def __init__(self, game, meta, open_ids):
        folder = os.path.join(game.assets.assets_dir, "soaring3d", S3.WORLD)
        self.cells = pygame.image.load(os.path.join(folder, "cells.png"))
        self.cell = meta["cell"]                       # town-map pixels a cell
        self.meta = meta
        self.open = set(open_ids)
        m = self.cells.copy()
        m.set_palette([(0, 0, 0) if i in self.open else (255, 255, 255) for i in range(256)])
        m = m.convert()
        w, h = m.get_size()                            # (blurred a little: a soft edge, not a staircase)
        m = pygame.transform.smoothscale(pygame.transform.smoothscale(m, (max(1, w // 4), max(1, h // 4))), (w, h))
        self.mask = m
        self.top = _load(game, "oras_cloud_top.png")
        self.mass = _load(game, "oras_kumo03.png")
        self.textures = {}

    def region_at(self, mx, my):
        """The region a town-map pixel of the world belongs to (its town's, or its sea's), or None."""
        cx, cy = int(mx // self.cell), int(my // self.cell)
        if not (0 <= cx < self.cells.get_width() and 0 <= cy < self.cells.get_height()):
            return None
        i = self.cells.get_at((cx, cy))[0]
        seeds, regions = self.meta["seeds"], self.meta.get("regions") or []
        if i < len(seeds):
            return seeds[i][1]
        sea = self.meta.get("sea_of", 200)
        if sea <= i < sea + len(regions):
            return regions[i - sea]
        return None

    def open_box(self):
        """(x0, y0, x1, y1) in town-map pixels round every clear cell, or None."""
        w, h = self.cells.get_size()
        xs, ys = [], []
        for cy in range(0, h, 4):
            for cx in range(0, w, 4):
                if self.cells.get_at((cx, cy))[0] in self.open:
                    xs.append(cx)
                    ys.append(cy)
        if not xs:
            return None
        c = self.cell
        return min(xs) * c, min(ys) * c, (max(xs) + 4) * c, (max(ys) + 4) * c

    def locked(self, mx, my):
        """Is this town-map pixel of the world under cloud?"""
        cx, cy = int(mx // self.cell), int(my // self.cell)
        if not (0 <= cx < self.cells.get_width() and 0 <= cy < self.cells.get_height()):
            return True
        return self.cells.get_at((cx, cy))[0] not in self.open

    def texture(self, level, w, h):
        """Cloud-tops as seen from above, w x h, at this level's size (the same clouds the same size on every level)."""
        key = (level, w, h)
        if key not in self.textures:
            s = pygame.Surface((w, h))
            s.fill(self.BASE)
            for img, period in [] if level >= 3 else ((self.mass, 256), (self.top, 512)):    # (periods that fit a tile: no seams)
                if img is None:
                    continue
                p = max(8, period >> level)
                t = pygame.transform.smoothscale(img, (p, p))
                for y in range(0, h, p):
                    for x in range(0, w, p):
                        s.blit(t, (x, y))
            if len(self.textures) > 8:
                self.textures.clear()
            self.textures[key] = s
        return self.textures[key]

    def cover(self, img, level, gx, gy):
        """Cloud this piece of a ground picture in place (level 0 = 4 pixels a town-map pixel, each level half that;
        (gx, gy): where the piece's top-left is in its level's picture)."""
        per = 4 * self.cell / (2 ** level)              # the level's pixels a cell
        w, h = img.get_size()
        r = pygame.Rect(int(gx // per), int(gy // per), max(1, int(math.ceil(w / per))), max(1, int(math.ceil(h / per))))
        r = r.clip(self.mask.get_rect())
        if r.w <= 0 or r.h <= 0:
            img.fill(self.BASE)
            return
        sub = self.mask.subsurface(r)
        avg = pygame.transform.average_color(sub)
        if avg[0] <= 1:
            return                                      # (nothing clouded here)
        m = pygame.transform.smoothscale(sub, (max(1, int(r.w * per)), max(1, int(r.h * per))))
        mask = pygame.Surface((w, h))
        mask.fill((255, 255, 255))
        mask.blit(m, (int(r.x * per - gx), int(r.y * per - gy)))
        cloud = self.texture(level, w, h).copy()
        if avg[0] < 254:
            ground = img.copy()
            ground.blit(mask, (0, 0), special_flags=pygame.BLEND_MULT)
            img.blit(ground, (0, 0), special_flags=pygame.BLEND_SUB)          # the ground, less where it's cloud
            cloud.blit(mask, (0, 0), special_flags=pygame.BLEND_MULT)
            img.blit(cloud, (0, 0), special_flags=pygame.BLEND_ADD)           # ... and the cloud there instead
        else:
            img.blit(cloud, (0, 0))

    def wall(self, meta, rng, step=6):
        """The cloud bank along the edge of where you may fly: billboards standing on the cloud side of every edge,
        (world x, z) each, every `step` cells."""
        out = []
        w, h = self.cells.get_size()
        lock = {}

        def is_locked(cx, cy):
            if (cx, cy) not in lock:
                lock[(cx, cy)] = not (0 <= cx < w and 0 <= cy < h) or self.cells.get_at((cx, cy))[0] not in self.open
            return lock[(cx, cy)]

        for cy in range(0, h, step):
            for cx in range(0, w, step):
                if not is_locked(cx, cy):
                    continue
                if any(not is_locked(cx + dx, cy + dy) for dx, dy in ((step, 0), (-step, 0), (0, step), (0, -step))):
                    mx, my = (cx + rng.uniform(-0.4, 0.4) * step) * self.cell, (cy + rng.uniform(-0.4, 0.4) * step) * self.cell
                    out.append(S3.world_point(meta, mx, my))
        return out


class Soaring3DState(PlayState):

    def __init__(self, game, restore_data=None, classic=False):
        if getattr(self, "_soar_ready", False):   # back from a battle: the flight goes on where it was
            self._back_from_battle()
            return
        super().__init__(game, restore_data=restore_data, classic=True)
        self._soar_ready = True
        game.soaring3d_state = self
        story = game.story_manager
        self.area_key = story.current_area_key
        self.W, self.H = game.width, game.height
        self.RW, self.RH = self.W // 2, self.H // 2        # the view is drawn at half size, then doubled
        self.F = (self.RW / 2) / math.tan(math.radians(FOV / 2))
        self.rng = random.Random()
        self.t = 0
        self._setup_pictures()
        self.eon_id, self.eon_name = self._mount()
        self.eon_imgs = {}
        self.rider = self._rider()
        came = getattr(story, "last_area_key", None) or "MOSSDEEP_CITY"
        start = S3.TOWNS.get(came) or S3.LAND_SPOTS.get(came, (None, None))[1]
        self.far = start is None                 # (the flute played in a region not on the world: off to the skies we know)
        start = start or S3.TOWNS.get("MOSSDEEP_CITY", (0, 0))
        self.x, self.z = float(start[0]), float(start[1]) + 2500   # (a little south, looking north at it)
        if self._locked(self.x, self.z):        # (never start inside the clouds: the nearest town you've been to)
            flags = story.story_flags
            seen = [k for k in S3.TOWNS if flags.get(f"visited_{k}") and not self._locked(*S3.TOWNS[k])]
            if seen:
                k, _d = S3.nearest_town(self.x, self.z, set(seen))
                self.x, self.z = S3.TOWNS[k]
        self.heading = 0.0       # degrees, 0 = north, clockwise
        self.alt = 1800.0
        self.speed = SPEEDS[1]
        self.bank = 0.0          # -1 .. 1 (left .. right)
        self.pitch = 0.0         # -1 .. 1 (dive .. climb)
        self.mode = "FLY"        # FLY, ASK (land / fly in?), PAUSE
        self.ask = None
        self.skip = set()
        self.held = None
        self.fast_held = False
        self.wilds = []
        self.next_wild = FPS * 2
        self.region_now, self.region_seen, self.banner, self.banner_t = None, 0, None, 0
        self.flash_text, self.flash_t = (f"{self.eon_name} flew you far over the sea, to skies you know!" if self.far
                                         else f"You're soaring on {self.eon_name}!"), FPS * 3
        self.pool = self._get_wild_pool(self.area_data) or {"278": 1}
        self._refresh_spots()

    # ---------------------------------------------------------------- set-up
    def _setup_pictures(self):
        meta = {}
        try:
            with open(os.path.join(self.game.assets.assets_dir, "soaring3d", "soaring3d.json"), encoding="utf-8") as f:
                meta = json.load(f)
        except (OSError, ValueError):
            pass
        self.levels = []
        self.sea = SEA
        self.world = S3.world_meta(self.game.assets.assets_dir) if S3.GROUND == "world" else None
        self.clouds, self.wall = None, []
        near = _load(self.game, "map_ground.png", alpha=False) if S3.GROUND in ("map", "world") else None
        self.on_map = near is not None or self.world is not None
        if self.world is not None:
            self._setup_world()
        elif self.on_map:
            S3.use_ground("map", self._map_points())
        else:                     # Omega Ruby's sky map (chosen, or the map picture is missing)
            S3.use_ground("oras")
            near = _load(self.game, "ground.jpg", alpha=False)
        if self.world is not None:
            pass                  # (set up above)
        elif self.on_map:
            # the 2D version's map: crisp pixels, so its halves are picked, not blended; its own sea all round
            rect = S3.map_ground_rect(*near.get_size())
            self.sea = tuple(near.get_at((4, 4)))[:3]
            key = ("mips", "map")
            if key not in _cache:
                l1 = pygame.transform.scale(near, (near.get_width() // 2, near.get_height() // 2))
                l2 = pygame.transform.scale(l1, (l1.get_width() // 2, l1.get_height() // 2))
                l3 = pygame.transform.smoothscale(l2, (l2.get_width() // 2, l2.get_height() // 2))
                _cache[key] = (near, l1, l2, l3)
            for img in _cache[key]:
                self.levels.append(Level(img, rect, CROP, self.sea))
            m = 30000                                   # (open sea round it, then the edge of the sky)
            self.bounds = (rect[0] - m, rect[1] - m, rect[2] + m, rect[3] + m)
            self.mm_src, self.mm_rect = _cache[key][2], rect
        elif near is not None:
            far = _load(self.game, "ground_far.jpg", alpha=False)
            rect = tuple(meta.get("near", (-16000, -19000, 32000, 17000)))
            key = ("mips",)
            if key not in _cache:         # the finer pictures, halved and halved again
                l1 = pygame.transform.smoothscale(near, (near.get_width() // 2, near.get_height() // 2))
                l2 = pygame.transform.smoothscale(l1, (l1.get_width() // 2, l1.get_height() // 2))
                _cache[key] = (near, l1, l2)
            for img in _cache[key]:
                self.levels.append(Level(img, rect, CROP, self.sea))
            if far is not None:
                self.levels.append(Level(far, tuple(meta.get("far", (-56000, -50000, 64000, 40000))), FAR_CROP, self.sea))
            self.bounds = tuple(meta.get("far", (-56000, -50000, 64000, 40000)))
            self.mm_src, self.mm_rect = _cache[key][2], rect
        else:
            self.bounds = (-56000, -50000, 64000, 40000)
            self.mm_src, self.mm_rect = None, self.bounds
        self.minimap = None
        if self.mm_src is not None:               # the mini-map: Hoenn itself, not the open sea round it
            src = self.mm_src
            mw = 300 if self.world is not None else 240
            self.minimap = pygame.transform.smoothscale(src, (mw, int(mw * src.get_height() / src.get_width())))
        self.banks = tuple(meta.get("banks", (-50, -25, 0, 25, 50)))
        self.pitches = tuple(meta.get("pitches", (-25, 0, 25)))
        self.view = pygame.Surface((self.RW, self.RH))
        self.band = 2           # screen rows per strip of ground; 3 if frames come slow (a slower phone)
        self.frame_ms = 0.0
        # the sky: a gradient, the game's own horizon clouds going round as you turn, and haze over the far ground
        self.sky = pygame.Surface((self.RW, self.RH))
        for y in range(self.RH):
            k = min(1.0, y / (self.RH * 0.45))
            self.sky.fill((int(70 + (HAZE[0] - 70) * k), int(120 + (HAZE[1] - 120) * k), int(205 + (HAZE[2] - 205) * k)),
                          (0, y, self.RW, 1))
        pano_w = int(self.RW * 360 / FOV)
        self.pano = pygame.Surface((pano_w, 64), pygame.SRCALPHA)
        for name, y in (("cloud_b.png", 4), ("cloud_a.png", 18)):
            img = _load(self.game, name)
            if img is None:
                continue
            img = pygame.transform.smoothscale(img, (pano_w // 6, 44))
            for i in range(6):
                self.pano.blit(img, (i * pano_w // 6 + (40 if y == 18 else 0), y))
        self.haze = pygame.Surface((self.RW, 90), pygame.SRCALPHA)
        for y in range(90):
            self.haze.fill(HAZE + (int(235 * (1 - y / 90) ** 1.6),), (0, y, self.RW, 1))
        self.rift_img = rift_picture()
        self.storm_img = oras_storm_picture(self.game) or storm_picture()
        self.rift_layers = oras_rift_layers(self.game)     # (Omega Ruby's rift streaks over a glow; None: ours)
        self._wall_cache = {}

    def _setup_world(self):
        """The world ground (Jordan, 11-18): the five regions as his world map has them, clouded where you haven't been.
        Its finest two pictures are tiles read as needed; the coarser two are whole (and the mini-map)."""
        meta = self.world
        S3.use_ground("world", meta=meta)
        # the cloud bank's pictures: Omega Ruby's horizon clouds and its soft puff
        self.wall_pics = []
        for name in ("cloud_a.png", "cloud_b.png", "oras_puff.png"):
            p = _load(self.game, name)
            if p is not None:                    # (rounded off: no square corners or flat edges against the sky)
                p = p.copy()
                p.blit(pygame.transform.smoothscale(_soft_disc(128), p.get_size()), (0, 0),
                       special_flags=pygame.BLEND_RGBA_MULT)
                self.wall_pics.append(p)
        folder = os.path.join(self.game.assets.assets_dir, "soaring3d", S3.WORLD)
        flags = self.game.story_manager.story_flags
        opened = S3.cover_open(meta, flags)
        # (a save that has no town marked as visited would be all cloud: then nothing is hidden)
        self.clouds = Clouds(self.game, meta, opened) if opened else None
        rect = S3.world_rect(meta)
        self.sea = Clouds.BASE if self.clouds is not None else SEA   # (past the farthest picture: more cloud)
        w, h = meta["ground_px"]
        tile = meta["tile"]
        self.levels.append(Level(Tiled(folder, "t0", (w, h), tile, self.clouds, 0), rect, CROP, self.sea))
        self.levels.append(Level(Tiled(folder, "t1", (w // 2, h // 2), tile, self.clouds, 1), rect, CROP, self.sea))
        whole = []
        for name, level in (("w2.png", 2), ("w3.png", 3)):
            try:
                img = pygame.image.load(os.path.join(folder, name)).convert()
            except (pygame.error, FileNotFoundError):
                continue
            if self.clouds is not None:
                self.clouds.cover(img, level, 0, 0)
            whole.append(img)
            self.levels.append(Level(img, rect, CROP, self.sea))
        self.bounds = rect
        self.mm_src, self.mm_rect = None, rect
        if whole:                      # the mini-map: where you may fly and a little round it, not the whole cloud sea
            img = whole[-1]
            k = img.get_width() / (rect[2] - rect[0])
            box = self.clouds.open_box() if self.clouds is not None else None
            if box:
                bx0, bz0, bx1, bz1 = (S3.world_point(meta, box[0], box[1]) + S3.world_point(meta, box[2], box[3]))
                pad = 6000
                cut = pygame.Rect(int((bx0 - pad - rect[0]) * k), int((bz0 - pad - rect[1]) * k),
                                  int((bx1 - bx0 + 2 * pad) * k), int((bz1 - bz0 + 2 * pad) * k)).clip(img.get_rect())
                self.mm_src = img.subsurface(cut)
                self.mm_rect = (rect[0] + cut.x / k, rect[1] + cut.y / k, rect[0] + cut.right / k, rect[1] + cut.bottom / k)
            else:
                self.mm_src = img
        if self.clouds is None:
            return
        self.wall = [(x, z, alt + self.rng.uniform(-250, 250), self.rng.choice(self.wall_pics), self.rng.uniform(4200, 6400))
                     for x, z in self.clouds.wall(meta, self.rng) for alt in WALL_ALTS] if self.wall_pics else []

    def _region_at(self, x, z):
        """The region (world.json's name) under this spot (world units), or None (off the world, or no region's)."""
        if self.clouds is None:
            return None
        ox, oz = self.world["origin"]
        u = self.world["unit_per_map_px"]
        return self.clouds.region_at((x - ox) / u, (z - oz) / u)

    def _watch_region(self):
        """Crossing into another region (Jordan, 11-18: "subtle transparent labeling ... when a player is leaving the
        region"): its name fades in over the view, with where you've left. A region counts once you've been over it a
        moment (no flicker along a border)."""
        if self.t % 6:
            return
        here = self._region_at(self.x, self.z)
        if here is None or here == self.region_now:
            self.region_seen = 0
            return
        self.region_seen += 1
        if self.region_now is not None and self.region_seen < 3:
            return
        self.banner = (S3.REGION_NAMES.get(here, here.title()),
                       f"Leaving {S3.REGION_NAMES.get(self.region_now, self.region_now.title())}" if self.region_now else "")
        self.banner_t = BANNER_T
        self.region_now, self.region_seen = here, 0

    def _draw_banner(self, screen):
        """The region's name, large and see-through, fading in and out (never in the way of the flight)."""
        if self.banner_t <= 0 or not self.banner:
            return
        self.banner_t -= 1
        t = BANNER_T - self.banner_t
        a = min(1.0, t / (FPS * 0.6), self.banner_t / (FPS * 1.2))
        name, left = self.banner
        fonts = self.game.assets.fonts
        y = int(self.H * 0.27)
        big = fonts["big"].render(name, True, (255, 255, 255))
        small = fonts["button"].render(left, True, (235, 240, 255)) if left else None
        h = big.get_height() + (small.get_height() + 4 if small else 0) + 22
        w = max(big.get_width(), small.get_width() if small else 0) + 140
        band = pygame.Surface((w, h), pygame.SRCALPHA)           # (a soft dark band: readable over white cloud too)
        for i in range(h):
            edge = min(i, h - 1 - i) / (h / 2)
            band.fill((16, 24, 52, int(95 * a * min(1.0, edge * 2.2))), (0, i, w, 1))
        sides = pygame.Surface((w, 1), pygame.SRCALPHA)           # (and soft at the ends)
        for i in range(w):
            sides.set_at((i, 0), (255, 255, 255, int(255 * min(1.0, min(i, w - 1 - i) / 70))))
        band.blit(pygame.transform.scale(sides, (w, h)), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        top = y - h // 2
        screen.blit(band, (self.W // 2 - w // 2, top))
        cy = top + 11
        if small:
            for img, dx, k in ((fonts["button"].render(left, True, (10, 14, 30)), 2, 0.55), (small, 0, 0.8)):
                img.set_alpha(int(255 * k * a))
                screen.blit(img, img.get_rect(midtop=(self.W // 2 + dx, cy + dx)))
            cy += small.get_height() + 4
        for img, dx, k in ((fonts["big"].render(name, True, (10, 14, 30)), 3, 0.6), (big, 0, 0.85)):
            img.set_alpha(int(255 * k * a))
            screen.blit(img, img.get_rect(midtop=(self.W // 2 + dx, cy + dx)))

    def _locked(self, x, z):
        """Is this spot (world units) under the clouds of somewhere you haven't been?"""
        if self.clouds is None:
            return False
        ox, oz = self.world["origin"]
        u = self.world["unit_per_map_px"]
        return self.clouds.locked((x - ox) / u, (z - oz) / u)

    def _map_points(self):
        try:
            with open(os.path.join(self.game.assets.assets_dir, "map_points.json"), encoding="utf-8") as f:
                return (json.load(f).get("region_maps", {}).get("HOENN") or {}).get("points") or {}
        except (OSError, ValueError):
            return {}

    def _mount(self):
        return mount(self.game)

    def _eon_sprite(self):
        """Jordan's Mega Latias / Latios from behind, five times (the 2D version's), or None."""
        key = ("sprite",)
        if key not in self.eon_imgs:
            img = _load(self.game, "mega_latias_back.png" if self.eon_id == 380 else "mega_latios_back.png")
            if img is not None:
                img = pygame.transform.scale(img, (img.get_width() * SPRITE_SCALE, img.get_height() * SPRITE_SCALE))
            self.eon_imgs[key] = img
        return self.eon_imgs[key]

    def _eon_img(self, bank_i, pitch_i):
        key = (bank_i, pitch_i)
        if key not in self.eon_imgs:
            img = _load(self.game, "eon_%d_%d_%d.png" % (self.eon_id, self.banks[bank_i], self.pitches[pitch_i]))
            if img is not None:
                w = int(self.W * 0.34)
                img = pygame.transform.smoothscale(img, (w, int(w * img.get_height() / img.get_width())))
            self.eon_imgs[key] = img
        return self.eon_imgs[key]

    def _rider(self):
        """You, from behind (your trainer's facing-up frame), cut off at the waist: sat on its back."""
        try:
            from src.coop import world
            char = str(getattr(self.game, "player_character", "") or "red")
            img = world.person_img(self.game, char, (0, -1), height=70 if S3.EON_LOOK == "sprite" else 60)
        except Exception:
            return None
        if img is None:
            return None
        return img.subsurface((0, 0, img.get_width(), int(img.get_height() * 0.72))).copy()

    def _refresh_spots(self):
        story = self.game.story_manager
        flags = story.story_flags
        progression = self.game.loader.area_data.get("STORY_PROGRESSION", {})
        names = {k: (progression.get(k) or {}).get("route_name") for k in S3.LAND_SPOTS}
        self.land = S3.mark_beacons(S3.land_spots(self.area_data, flags, names), progression, flags)
        self.skyspots = S3.sky_spots(self.area_data, flags)
        if self.clouds is not None:            # (nothing shows through the clouds)
            self.land = [s for s in self.land if not self._locked(*s["at"])]
            self.skyspots = [s for s in self.skyspots if not self._locked(*s["at"])]
        self.visited = {k for k in S3.TOWNS if flags.get(f"visited_{k}")}
        # LAND sets you down where Fly could: a town you've been to with a Center, or a region's home town (any region
        # on the world, Jordan 11-18; landing in another region's town is a trip there, as Fly's is)
        from src.states.systems.fly_map import fly_ok
        self.land_towns = {k for k in self.visited if k in S3.LAND_TOWNS and fly_ok(self.game, k)}

    # ---------------------------------------------------------------- the route underneath
    def _back_from_battle(self):
        self.mode = "FLY"
        self.dialogue_box.visible = False   # (the legend's line from before the battle)
        self.ask = None
        self.held = None
        self.fast_held = False
        self.wilds = []
        self.next_wild = self.rng.randint(*WILD_EVERY)
        self._refresh_spots()          # (a legend caught: the next one comes out, or the rift closes)

    def _play_data(self):
        return {"balls_left": self.balls_left, "current_streak": self.current_streak,
                "rounds_completed": self.rounds_completed, "pending_wild_encounters": 0,
                "initial_round_active": False, "soaring": True}

    def start(self):
        self.game.ui_manager.elements.clear()
        pygame.event.clear()
        self.game.story_manager.story_flags[f"visited_{self.area_key}"] = True

    def show_progression_menu(self):
        """A battle or its catch is over: fly on."""
        self.is_progression_paused = True
        self.p_data = [None] * 3
        self.catch_selection_active = False
        self.dialogue_box.visible = False
        self.mode = "FLY"
        self.ask = None

    # ---------------------------------------------------------------- input
    def handle_events(self, events):
        for e in events:
            if self.dialogue_box.visible:
                if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) or (
                        e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER)):
                    self.dialogue_box.advance()
                continue
            if self.mode == "ASK":
                self._ask_event(e)
                continue
            if self.mode != "FLY":
                continue
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_l, pygame.K_AC_BACK):
                self._ask_land()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self._land_rect().collidepoint(e.pos):
                    self._ask_land()
                elif self._fast_rect().collidepoint(e.pos):
                    self.fast_held = True
                else:
                    self.held = e.pos
            elif e.type == pygame.MOUSEMOTION and self.held is not None:
                self.held = e.pos
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                self.held = None
                self.fast_held = False

    def _ask_event(self, e):
        _spot, buttons = self.ask
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for rect, _label, _c, fn in buttons:
                if rect.collidepoint(e.pos):
                    return fn()
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER, pygame.K_y):
                return buttons[0][3]()
            if e.key in (pygame.K_ESCAPE, pygame.K_n, pygame.K_AC_BACK):
                return buttons[-1][3]()

    def _land_rect(self):
        return pygame.Rect(self.W - 190, 12, 172, HUD_H - 24)

    def _fast_rect(self):
        return pygame.Rect(self.W - 190, self.H - 120, 172, 96)

    # ---------------------------------------------------------------- choices
    def _ask_box(self, spot, line, yes, yes_fn, no="FLY ON"):
        cx, y = self.W // 2, HUD_H + 30
        buttons = [(pygame.Rect(cx - 330, y + 70, 300, 76), yes, theme.POKEMON, yes_fn),
                   (pygame.Rect(cx + 30, y + 70, 300, 76), no, theme.BACK, self._fly_on)]
        self.ask = (spot, buttons)
        self.ask_line = line
        self.mode = "ASK"

    def _fly_on(self):
        spot = self.ask[0] if self.ask else None
        if spot is not None:
            self.skip.add(spot["key"])
        self.ask = None
        self.mode = "FLY"

    def _ask_land(self):
        key, _d = S3.nearest_town(self.x, self.z, self.land_towns or set(S3.LAND_TOWNS))
        name = self._town_name(key)
        self._ask_box(None, f"Land at {name}?", "LAND", lambda: self._land_town(key), no="KEEP FLYING")

    def _town_name(self, key):
        try:
            from src.states.systems.fly_map import fly_name
            return S3.town_name(fly_name(self.game, key))
        except Exception:
            return S3.town_name(key)

    def _land_town(self, key):
        """Down at a town, as Fly lands you (outside its Center where it has one; into its region, as Fly goes)."""
        self.game.soaring3d_state = None
        self.mode = "GONE"
        from src.states.systems.fly_map import fly_land
        fly_land(self.game, key)

    def _land(self, key, line=None):
        self.game.soaring3d_state = None
        self.mode = "GONE"
        from src.states.overworld.area_transition import AreaTransitionState
        self.game.change_state(AreaTransitionState(self.game, key, initial_message=line))

    def _reach(self, spot):
        if spot["look"] in ("rift", "storm"):
            what = "A huge gap has opened in the sky!" if spot["look"] == "rift" else "A black cloud is crackling with power!"
            self._ask_box(spot, what, "FLY IN", lambda: self._legend(spot))
        else:
            self._ask_box(spot, f"{spot['name']} is below you!", "LAND", lambda: self._land_on(spot))

    def _land_on(self, spot):
        """Down onto a Mirage place: which legend is out, which place of its kind, today's hidden item (src/world/soaring.py)."""
        from src.world import soaring as landing
        place = (S3.SPOT_PLACES.get(spot["area"]) or (None, None, None))[2]   # (its point on the map picture)
        extra = landing.on_landing(self.game.story_manager, spot["area"], place, self.rng)
        self._land(spot["area"], f"{self.eon_name} landed on {spot['name']}.{extra}")

    def _legend(self, spot):
        self.ask = None
        self.mode = "PAUSE"
        self.wilds = []
        self.action_challenge_boss(dict(spot["next"]))

    def _wild(self, pid):
        """Into a flock: a battle with one of it (the route's own, back here after)."""
        from src.pokemon.data import Pokemon
        from src.states.battle import WildBattleState
        from src.world import levels
        self.mode = "PAUSE"
        self.rounds_completed += 1
        pokemon = Pokemon(self.game.loader.fetch_specific(int(pid)), self.game.assets, size_mult=3.125)
        levels.set_wild(self.game, pokemon, self.area_key)
        self.game.data.mark_seen(pokemon.id)
        battle = WildBattleState(self.game, pokemon, self.area_key, background_image=self._get_battle_background_for_area())
        battle.play_state_data = self._play_data()
        pygame.event.clear()
        self.game.change_state(battle)

    # ---------------------------------------------------------------- the flight
    def _vectors(self):
        h = math.radians(self.heading)
        return (math.sin(h), -math.cos(h)), (math.cos(h), math.sin(h))   # forward, right (x, z)

    def update(self):
        self.t += 1
        if self.dialogue_box.visible:
            self.dialogue_box.update()
            return
        if self.flash_t > 0:
            self.flash_t -= 1
        if self.mode != "FLY":
            return
        keys = pygame.key.get_pressed()
        steer = climb = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            steer -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            steer += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            climb += 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            climb -= 1
        if self.held is not None:
            if not steer:
                steer = max(-1.0, min(1.0, (self.held[0] - self.W / 2) / (self.W * 0.25)))
            if not climb:
                climb = max(-1.0, min(1.0, (self.H * 0.6 - self.held[1]) / (self.H * 0.25)))
        fast = self.fast_held or keys[pygame.K_SPACE] or keys[pygame.K_LSHIFT]
        want = SPEEDS[2] if fast else SPEEDS[1]
        self.speed += (want - self.speed) * 0.08
        self.bank += (steer - self.bank) * 0.15
        self.pitch += (climb - self.pitch) * 0.15
        self.heading = (self.heading + self.bank * TURN) % 360
        self.alt = max(ALT_MIN, min(ALT_MAX, self.alt + self.pitch * CLIMB))
        f, _r = self._vectors()
        self.x += f[0] * self.speed
        self.z += f[1] * self.speed
        self._edge()
        self._cloud_bank(f)
        self._watch_region()
        self._spawn()
        self._move_wilds()
        self._check_spots()

    def _edge(self):
        """The edge of the sky (ORAS turns you back): a U-turn."""
        x0, z0, x1, z1 = self.bounds
        m = 9000
        if self.x < x0 + m or self.x > x1 - m or self.z < z0 + m or self.z > z1 - m:
            self.x = max(x0 + m, min(x1 - m, self.x))
            self.z = max(z0 + m, min(z1 - m, self.z))
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            self.heading = math.degrees(math.atan2(cx - self.x, -(cz - self.z))) % 360
            self.flash_text, self.flash_t = "You can't fly any farther! Turning back...", FPS * 2

    def _cloud_bank(self, f):
        """The clouds over where you haven't been (Jordan, 11-18): flying into them turns you back, as the edge does."""
        if self.clouds is None or not self._locked(self.x + f[0] * 1500, self.z + f[1] * 1500):
            return
        self.x -= f[0] * self.speed * 2
        self.z -= f[1] * self.speed * 2
        self.heading = (self.heading + 180) % 360
        self.bank = 0.0
        self.flash_text, self.flash_t = "Thick clouds! You haven't been there yet. Turning back...", FPS * 2

    def _spawn(self):
        """Flyers ahead: the birds of the region they're over (S3.SKY_BIRDS, Jordan 11-18), in flocks of three or more,
        now and then one strong flyer alone, higher up."""
        self.next_wild -= 1
        if self.next_wild > 0 or len(self.wilds) >= 3:
            return
        self.next_wild = self.rng.randint(*WILD_EVERY)
        f, r = self._vectors()
        ahead, side = self.rng.uniform(6000, 9000), self.rng.uniform(-2500, 2500)
        wx, wz = self.x + f[0] * ahead + r[0] * side, self.z + f[1] * ahead + r[1] * side
        if self._locked(wx, wz):
            return                              # (none come out of the clouds)
        pool = {int(k): v for k, v in (self.pool or {}).items()}
        pid, n = S3.sky_wild(self._region_at(wx, wz) or "HOENN", self.rng, fallback=pool)
        if not pid:
            return
        lift = self.rng.uniform(400, 900) if n == 1 else self.rng.uniform(-500, 500)
        self.wilds.append({"pid": pid, "x": wx, "z": wz, "alt": max(ALT_MIN, min(ALT_MAX, self.alt + lift)),
                           "dx": self.rng.uniform(-30, 30), "dz": self.rng.uniform(-30, 30), "ph": self.rng.random() * 6,
                           "n": n})

    def _move_wilds(self):
        keep = []
        for w in self.wilds:
            w["x"] += w["dx"]
            w["z"] += w["dz"]
            dx, dz = w["x"] - self.x, w["z"] - self.z
            f, r = self._vectors()
            ahead = dx * f[0] + dz * f[1]
            if math.hypot(dx, dz) < 420 and abs(w["alt"] - self.alt) < 600:
                return self._wild(w["pid"])
            if -2000 < ahead < 14000:
                keep.append(w)
        self.wilds = keep

    def _check_spots(self):
        for spot in self.land + self.skyspots:
            d = math.hypot(spot["at"][0] - self.x, spot["at"][1] - self.z)
            near = d < (900 if spot["look"] in ("rift", "storm") else 1100)
            if spot["look"] in ("rift", "storm"):
                near = near and abs(self.alt - spot["alt"]) < 1200
            if not near:
                self.skip.discard(spot["key"])
            elif spot["key"] not in self.skip:
                return self._reach(spot)

    # ---------------------------------------------------------------- drawing
    def _horizon(self):
        return int(self.RH * 0.30 + self.pitch * self.RH * 0.06)

    def draw(self):
        screen = self.game.screen
        view = self.view
        hy = self._horizon()
        view.blit(self.sky, (0, 0), (0, self.RH * 0.45 - hy if hy < self.RH * 0.45 else 0, self.RW, self.RH))
        # the horizon clouds go round as you turn
        pw = self.pano.get_width()
        off = -int(self.heading / 360 * pw) % pw
        for k in (-1, 0, 1):
            view.blit(self.pano, (off + k * pw, hy - 52))
        t0 = time.perf_counter()
        self._draw_ground(view, hy)
        self.frame_ms += ((time.perf_counter() - t0) * 1000 - self.frame_ms) * 0.05
        self.band = 3 if self.frame_ms > 22 else 2 if self.frame_ms < 12 else self.band
        view.blit(self.haze, (0, hy - 6))
        self._draw_things(view, hy)
        pygame.transform.scale(view, (self.W, self.H), screen)
        self._draw_me(screen)
        self._draw_banner(screen)
        self._draw_hud(screen)
        if self.mode == "ASK" and self.ask:
            self._draw_ask(screen)
        if self.dialogue_box.visible:
            self.dialogue_box.draw(screen)

    def _draw_ground(self, view, hy):
        """Mode 7: every row below the horizon is a strip of ground, from the finest picture that reaches."""
        if not self.levels:
            view.fill(self.sea, (0, hy, self.RW, self.RH - hy))
            return
        turned = [None] * len(self.levels)
        half_w = self.RW / 2
        y = hy + 1
        band = self.band
        while y < self.RH:
            d = self.alt * self.F / (y + band / 2 - hy)            # how far ahead this row is
            lvl = None
            for i, L in enumerate(self.levels):
                # the finest picture whose turned square reaches this row, and not so fine that it shimmers
                if d * 1.25 < L.crop * L.s * REACH and (2 * half_w * d / self.F) / L.s <= self.RW * 2:
                    lvl = i
                    break
            if lvl is None:
                lvl = len(self.levels) - 1
            L = self.levels[lvl]
            if d * 1.25 > L.crop * L.s * REACH:                    # past the farthest picture: open sea
                view.fill(self.sea, (0, y, self.RW, band))
                y += band
                continue
            if turned[lvl] is None:
                turned[lvl] = L.turned(self.x, self.z, self.heading)
            surf = turned[lvl]
            cxs, czs = surf.get_width() / 2, surf.get_height() / 2
            # where you are in the turned square (it was turned a little way back, maybe)
            ox, oz, _h = L.at
            f, r = self._vectors()
            dx, dz = self.x - ox, self.z - oz
            mx = cxs + (dx * r[0] + dz * r[1]) / L.s
            my = czs - (dx * f[0] + dz * f[1]) / L.s
            sw = 2 * half_w * d / self.F / L.s
            sy = my - d / L.s
            src = pygame.Rect(int(mx - sw / 2), int(sy), max(1, int(sw)), 1)
            clip = src.clip(surf.get_rect())
            if clip.w > 0 and clip.h > 0:
                strip = surf.subsurface(clip)
                k = self.RW / src.w
                dx0 = int((clip.x - src.x) * k)
                dw = max(1, int(clip.w * k + 1))
                if clip.w < src.w:
                    view.fill(self.sea, (0, y, self.RW, band))
                view.blit(pygame.transform.scale(strip, (dw, band)), (dx0, y))
            else:
                view.fill(self.sea, (0, y, self.RW, band))
            y += band

    def _project(self, wx, wz, walt):
        """(screen x, y, scale, distance ahead) in the half-size view, or None if behind."""
        f, r = self._vectors()
        dx, dz = wx - self.x, wz - self.z
        ahead = dx * f[0] + dz * f[1]
        if ahead < 150:
            return None
        side = dx * r[0] + dz * r[1]
        k = self.F / ahead
        return self.RW / 2 + side * k, self._horizon() + (self.alt - walt) * k, k, ahead

    def _draw_things(self, view, hy):
        things = []
        for s in self.land:
            p = self._project(s["at"][0], s["at"][1], 0)
            if p:
                things.append((p[3], "land", s, p))
        for s in self.skyspots:
            p = self._project(s["at"][0], s["at"][1], s["alt"])
            if p:
                things.append((p[3], s["look"], s, p))
        for w in self.wilds:
            p = self._project(w["x"], w["z"], w["alt"])
            if p:
                things.append((p[3], "wild", w, p))
        for b in self.wall:
            if abs(b[0] - self.x) < WALL_SEEN and abs(b[1] - self.z) < WALL_SEEN:
                p = self._project(b[0], b[1], b[2])
                if p and p[3] < WALL_SEEN:
                    things.append((p[3], "wall", b, p))
        for _d, kind, s, (sx, sy, k, ahead) in sorted(things, key=lambda t: -t[0]):
            if ahead > 40000 or not (-400 < sx < self.RW + 400):
                continue
            fade = max(0, min(255, int(255 * (1 - (ahead - 22000) / 18000)))) if ahead > 22000 else 255
            if kind == "wall":
                self._draw_wall_cloud(view, s, sx, sy, k, ahead)
            elif kind == "rift" and self.rift_layers:
                self._draw_rift(view, sx, sy, max(8, int(2600 * k)), fade)
            elif kind == "land":
                self._draw_land_spot(view, s, sx, sy, k, fade)
            elif kind in ("rift", "storm"):
                img = self.rift_img if kind == "rift" else self.storm_img
                size = max(8, int((2600 if kind == "rift" else 4800) * k))
                if size < 900:
                    pic = pygame.transform.smoothscale(img, (size, int(size * img.get_height() / img.get_width())))
                    if kind == "rift":
                        pic = pygame.transform.rotate(pic, (self.t * 4) % 360)
                    pic.set_alpha(fade)
                    view.blit(pic, pic.get_rect(center=(int(sx), int(sy))))
                if kind == "storm" and (self.t // 3) % 7 == 0 and size > 20:
                    self._draw_lightning(view, sx, sy, size, fade)
            else:
                size = max(6, min(200, int(380 * k)))
                img = follower(self.game, s["pid"], size, row=0, frame=self.t // 4)   # (flying at you)
                bob = math.sin(self.t / 5 + s["ph"]) * size * 0.08
                for i in range(s["n"]):
                    ox = (i - (s["n"] - 1) / 2) * size * 0.7
                    oy = (abs(i - (s["n"] - 1) / 2)) * size * 0.25
                    view.blit(img, img.get_rect(center=(int(sx + ox), int(sy + oy + bob))))

    def _draw_wall_cloud(self, view, b, sx, sy, k, ahead):
        """One cloud of the bank over where you haven't been: thinner far off, so the bank comes up out of the haze."""
        _x, _z, _alt, img, size = b
        w = int(size * k)
        if w < 4 or w > 2600 or not (-w < sx < self.RW + w):
            return
        w = max(4, w // 6 * 6)
        key = (id(img), w)
        pic = self._wall_cache.get(key)
        if pic is None:
            if len(self._wall_cache) > 400:
                self._wall_cache.clear()
            pic = self._wall_cache[key] = pygame.transform.smoothscale(img, (w, max(2, w * img.get_height() // img.get_width())))
        a = 255 if ahead < WALL_SEEN * 0.6 else max(0, int(255 * (WALL_SEEN - ahead) / (WALL_SEEN * 0.4)))
        pic.set_alpha(a)
        view.blit(pic, pic.get_rect(center=(int(sx), int(sy))))

    def _draw_lightning(self, view, sx, sy, size, fade):
        """A fork of lightning out of the storm cloud: the forked bolts of Thundercage (Pokemon Orre 2.1.1's move
        animations), a different one each flash; the old drawn zigzag if the sheet is missing."""
        bolts = lightning_bolts(self.game)
        if not bolts:
            pts = [(sx - size * 0.05, sy + size * 0.1), (sx + size * 0.04, sy + size * 0.25),
                   (sx - size * 0.03, sy + size * 0.27), (sx + size * 0.06, sy + size * 0.45)]
            pygame.draw.lines(view, (255, 240, 120), False, pts, max(1, size // 60))
            return
        flash = self.t // 21
        bolt = bolts[flash % len(bolts)]
        h = max(8, int(size * 0.55))
        w = max(4, int(h * bolt.get_width() / bolt.get_height()))
        if h > 900:
            return
        pic = pygame.transform.smoothscale(bolt, (w, h))
        if fade < 255:
            pic.set_alpha(fade)
        x = sx + ((flash * 37) % 7 - 3) * size * 0.04           # (striking from a different part of the cloud)
        view.blit(pic, (int(x - w / 2), int(sy + size * 0.08)))   # (its see-through pixels are white: no adding)

    def _draw_rift(self, view, sx, sy, size, fade):
        """The Dimensional Rift: Omega Ruby's own rift streaks (tinted violet, as the game tints them) turning in a glow."""
        if size > 1400:
            return
        glow, streaks = self.rift_layers
        g = pygame.transform.smoothscale(glow, (int(size * 1.4), int(size * 1.4)))
        if fade < 255:
            g.fill((fade, fade, fade), special_flags=pygame.BLEND_MULT)
        view.blit(g, g.get_rect(center=(int(sx), int(sy))), special_flags=pygame.BLEND_ADD)
        st = pygame.transform.smoothscale(streaks, (size, size))
        for turn, a in ((self.t * 4, 1.0), (-self.t * 3 + 45, 0.7)):
            r = pygame.transform.rotate(st, turn % 360)
            r.set_alpha(int(fade * a))
            view.blit(r, r.get_rect(center=(int(sx), int(sy))))
        pygame.draw.circle(view, (8, 0, 18), (int(sx), int(sy)), max(2, int(size * 0.13)))

    def _draw_land_spot(self, view, s, sx, sy, k, fade):
        """A Mirage place: a glowing ring on the ground, a shaft of light, and the red beacon while a legend's there."""
        rw = max(6, int(1500 * k))
        rh = max(3, int(rw * 0.3))
        pulse = 0.5 + 0.5 * math.sin(self.t / 6)
        ring = pygame.Surface((rw + 8, rh + 8), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (255, 236, 150, int((110 + 120 * pulse) * fade / 255)), ring.get_rect(), max(2, rw // 25))
        view.blit(ring, ring.get_rect(center=(int(sx), int(sy))))
        bh = max(10, min(int(sy) + 10, int(2200 * k)))
        bw = max(2, min(26, int(110 * k)))
        beam = pygame.Surface((bw, bh), pygame.SRCALPHA)
        for yy in range(bh):
            beam.fill((255, 244, 200, int(150 * (yy / bh) * fade / 255)), (0, yy, bw, 1))
        view.blit(beam, (int(sx - bw / 2), int(sy - bh)))
        if s.get("beacon"):
            by = sy - bh - max(6, int(300 * k)) - math.sin(self.t / 5) * 4
            r = max(4, int(170 * k))
            pts = [(sx, by - r), (sx + r * 0.66, by), (sx, by + r), (sx - r * 0.66, by)]
            pygame.draw.polygon(view, (230, 40, 50), pts)
            pygame.draw.polygon(view, (90, 10, 20), pts, 1)

    def _draw_me(self, screen):
        cx, cy = self.W // 2, int(self.H * 0.66 + 6 * math.sin(self.t / 6))
        sprite = self._eon_sprite() if S3.EON_LOOK == "sprite" else None
        if sprite is not None:
            # Jordan's back view, as the 2D version draws it: rolled into the turn, nudged up as you climb
            roll = -self.bank * SPRITE_ROLL
            img = pygame.transform.rotate(sprite, roll) if abs(roll) > 0.5 else sprite
            cy -= int(self.pitch * 10)
            screen.blit(img, img.get_rect(center=(cx, cy)))
            if self.rider is not None:
                r = pygame.transform.rotate(self.rider, roll * 0.8) if abs(roll) > 0.5 else self.rider
                a = math.radians(roll)
                up = 4 + r.get_height() / 2                        # (the rider's middle, above the sprite's middle)
                screen.blit(r, r.get_rect(center=(int(cx - math.sin(a) * up), int(cy - math.cos(a) * up))))
            return
        # (the baked models' bank: + is the left wing down, so turning left picks the + end)
        bi = min(len(self.banks) - 1, max(0, int(round((1 - self.bank) / 2 * (len(self.banks) - 1)))))
        pi = min(len(self.pitches) - 1, max(0, int(round((self.pitch + 1) / 2 * (len(self.pitches) - 1)))))
        img = self._eon_img(bi, pi)
        if img is not None:
            screen.blit(img, img.get_rect(center=(cx, cy)))
        else:
            pygame.draw.circle(screen, (150, 110, 210), (cx, cy), 50)
        if self.rider is not None:
            roll = self.banks[bi] * 0.8                      # sat on its back, leaning with it
            r = pygame.transform.rotate(self.rider, roll) if roll else self.rider
            up = self.H * 0.035 + self.pitch * 8 + self.rider.get_height() / 2
            a = math.radians(roll)
            at = (cx - math.sin(a) * up, cy - math.cos(a) * up)
            screen.blit(r, r.get_rect(center=(int(at[0]), int(at[1]))))

    def _draw_hud(self, screen):
        fonts = self.game.assets.fonts
        bar = pygame.Rect(12, 8, self.W - 214, HUD_H - 16)
        theme.draw_textbox(screen, bar)
        title = "Soaring in the Sky"
        theme.shadow_text(screen, title, fonts["button"], bar.x + 20, bar.centery - fonts["button"].get_height() // 2)
        key, _d = S3.nearest_town(self.x, self.z, self.visited)
        room = bar.w - 60 - fonts["button"].size(title)[0]        # (a long town name never runs over the title)
        town, height = self._town_name(key), f"Height {int(self.alt / 10) * 10}"
        font, text = fit_text(fonts, (f"Near {town}   {height}", f"{town}   {height}", town), room)
        theme.shadow_text(screen, text, font, bar.right - 20, bar.centery - font.get_height() // 2, align="right")
        mouse = pygame.mouse.get_pos()
        r = self._land_rect()
        theme.command_button(screen, r, "LAND", fonts["button"], theme.BACK, hover=r.collidepoint(mouse))
        r = self._fast_rect()
        theme.command_button(screen, r, "FAST", fonts["button"], theme.POKEMON, hover=self.fast_held)
        mm = self.minimap
        if mm is not None:
            at = pygame.Rect(16, self.H - mm.get_height() - 16, mm.get_width(), mm.get_height())
            screen.blit(mm, at)
            pygame.draw.rect(screen, theme.TEXTBOX_FRAME, at.inflate(4, 4), 3)
            x0, z0, x1, z1 = self.mm_rect
            kx, kz = mm.get_width() / (x1 - x0), mm.get_height() / (z1 - z0)
            for s in self.land:
                pygame.draw.circle(screen, (230, 40, 50) if s.get("beacon") else (255, 230, 120),
                                   (at.x + int((s["at"][0] - x0) * kx), at.y + int((s["at"][1] - z0) * kz)), 3)
            for s in self.skyspots:
                pygame.draw.circle(screen, (150, 80, 220), (at.x + int((s["at"][0] - x0) * kx), at.y + int((s["at"][1] - z0) * kz)), 4)
            me = (at.x + max(0, min(mm.get_width(), int((self.x - x0) * kx))),
                  at.y + max(0, min(mm.get_height(), int((self.z - z0) * kz))))
            f, _r = self._vectors()
            pygame.draw.line(screen, (20, 20, 30), me, (me[0] + int(f[0] * 10), me[1] + int(f[1] * 10)), 2)
            pygame.draw.circle(screen, (255, 255, 255) if (self.t // 6) % 2 else (20, 20, 30), me, 4)
        if self.flash_t > 0 and self.mode == "FLY":
            t = fonts["button"].render(self.flash_text, True, (255, 255, 255))
            pill = t.get_rect(center=(self.W // 2, HUD_H + 40)).inflate(30, 14)
            pygame.draw.rect(screen, (40, 30, 80), pill, border_radius=12)
            pygame.draw.rect(screen, (190, 150, 255), pill, 2, border_radius=12)
            screen.blit(t, t.get_rect(center=pill.center))

    def _draw_ask(self, screen):
        fonts = self.game.assets.fonts
        _spot, buttons = self.ask
        card = pygame.Rect(0, 0, 760, 200)
        card.center = (self.W // 2, HUD_H + 90)
        theme.draw_textbox(screen, card)
        font, text = fit_text(fonts, (self.ask_line,), card.w - 48, ("button", "label"))
        theme.shadow_text(screen, text, font, card.centerx, card.y + 26 + (fonts["button"].get_height() - font.get_height()) // 2,
                          align="center")
        mouse = pygame.mouse.get_pos()
        for rect, label, colour, _fn in buttons:
            theme.command_button(screen, rect, label, fonts["button"], colour, hover=rect.collidepoint(mouse))
