"""A walked map seen the way the DS games' camera sees it (Black 2 / White 2's towns; Jordan 11-20).

A map's roofs "_cam" {"picture": file under assets/tiles (the ground drawn from the camera, 32 px a tile, heights and all),
"top": px of picture above the map's row 0, "base": the street height, "lift": [[tiles] a row]: how far each tile's ground
is raised up the screen}. Made by kanto_handoff/unova_map_tools/camview.py through rmxp_import.py.

What it gives the town walker (src/states/overworld/walk_town.py):
- the ground picture, drawn `top` px above the map's row 0, so a raised terrace or the Outlook shows its cliffs and stairs;
- lift(x, y): whoever stands there is drawn that many tiles higher, smoothly between tiles, so you climb and go down stairs;
- the map's buildings ("_objects" with "b2:" models), each drawn every frame at the lean for where it is on screen (the DS
  camera's perspective: a building off to the side shows a little of its side wall) and in depth order with the people,
  so you walk behind them;
- shadow(): the small oval under everyone's feet."""
import json
import os

import pygame

LEAN_PER_TILE = 0.012       # a building this many tiles from the middle of the view leans this much more (x per unit of height: ~10 degrees at the edge)
S_LIFT = 0.7                # (camview.py's: height lifts a point this much up the picture)
_CACHE = {}


def _tiles_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "tiles")


def _load(rel):
    key = ("img", rel)
    if key not in _CACHE:
        img = pygame.image.load(os.path.join(_tiles_dir(), rel))
        try:
            img = img.convert_alpha()
        except pygame.error:
            pass
        _CACHE[key] = img
    return _CACHE[key]


def _index():
    if "index" not in _CACHE:
        try:
            with open(os.path.join(_tiles_dir(), "b2", "index.json"), encoding="utf-8") as f:
                _CACHE["index"] = json.load(f)
        except (OSError, ValueError):
            _CACHE["index"] = {}
    return _CACHE["index"]


def shadow(tile):
    """The oval under someone's feet (B2W2's: a soft dark ellipse, about half a tile wide)."""
    key = ("shadow", tile)
    if key not in _CACHE:
        w, h = int(tile * 0.62), max(4, int(tile * 0.22))
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, 72), s.get_rect())
        pygame.draw.ellipse(s, (0, 0, 0, 56), s.get_rect().inflate(-w // 4, -h // 3))
        _CACHE[key] = s
    return _CACHE[key]


def camera_zone(cameras, fx, fy):
    """(zoom, (dx, dy) tiles) for someone at (fx, fy) (fractional, mid-step) from a map's "cameras" zones, else None.
    A zone is {"rect": [x, y, w, h], "zoom": z} (one setting), or a moving strip from the game file (Black 2's a/1/5/6:
    camview.camera_areas) {"rect", "axis": "x"/"y", "zoom": [a, b], "pan": [[dx, dy], [dx, dy]]}: the camera slides from
    the first setting at the strip's north (west) edge to the second at its south (east) edge as you cross it (11-20)."""
    for c in cameras or ():
        r = c.get("rect") or (0, 0, 0, 0)
        if not (r[0] - 0.5 < fx < r[0] + r[2] - 0.5 and r[1] - 0.5 < fy < r[1] + r[3] - 0.5):
            continue
        z, pan = c.get("zoom") or 1.0, c.get("pan") or ((0, 0), (0, 0))
        if not isinstance(z, (list, tuple)):
            return float(z), (0.0, 0.0)
        if c.get("axis") == "x":
            t = (fx + 0.5 - r[0]) / max(1, r[2])
        else:
            t = (fy + 0.5 - r[1]) / max(1, r[3])
        t = max(0.0, min(1.0, t))
        (ax, ay), (bx, by) = pan
        return z[0] + (z[1] - z[0]) * t, (ax + (bx - ax) * t, ay + (by - ay) * t)
    return None


class Building:
    def __init__(self, obj, meta, tile, doors=(), lift_k=S_LIFT):
        self.key = obj["k"][3:]
        self.at = obj["at"]
        self.lift = lift_k * float(obj.get("h") or 0.0)
        self.foot = float(meta.get("foot", 0.0))
        self.n, self.step = int(meta["lean"]), float(meta["step"])
        k = tile / 32
        self.ox, self.oy = meta["lox"] * k, meta["loy"] * k
        self.k = k
        self.imgs = {}
        # where it sits among the people: its front wall. Its door's row when it has one (its steps and awning reach further
        # south, and whoever stands at the door or on the steps is in front of it); else the front of its model
        self.row = self.at[1] + self.foot
        mine = [y for x, y in doors if abs(x + 0.5 - self.at[0]) <= max(1.5, self.ox / tile) and self.at[1] - 1 <= y <= self.row + 1]
        if mine:
            self.row = min(self.row, max(mine) + 0.5)

    def img(self, i):
        if i not in self.imgs:
            im = _load("b2/%s_L%d.png" % (self.key, i))
            self.imgs[i] = pygame.transform.smoothscale(im, (max(1, round(im.get_width() * self.k)), max(1, round(im.get_height() * self.k))))
        return self.imgs[i]


class Cam3D:
    def __init__(self, spec, objects, tile, w, h, doors=()):
        self.tile = tile
        img = _load(spec["picture"])
        k = tile / 32
        key = ("ground", spec["picture"], tile)
        if key not in _CACHE:
            _CACHE[key] = img if k == 1 else pygame.transform.smoothscale(img, (round(img.get_width() * k), round(img.get_height() * k)))
        self.ground = _CACHE[key]
        self.top = spec["top"] * k
        self.lifts = spec.get("lift") or []
        self.w, self.h = w, h
        idx = _index()
        # the place's own camera (11-20, from the game file: a/0/5/9): how steeply height rises, how far buildings lean
        self.lift_k = float(spec.get("lift_k") or S_LIFT)
        self.lean_tile = float(spec.get("lean_tile") or LEAN_PER_TILE)
        self.buildings = [Building(o, idx[o["k"][3:]], tile, doors, self.lift_k) for o in objects
                          if isinstance(o.get("k"), str) and o["k"].startswith("b2:") and "lean" in idx.get(o["k"][3:], {})]
        # what stands up out of the ground (trees, lamp posts, fences, rails), one cut-out a row: drawn in depth order with
        # the people, so whoever stands just north of a tree is behind it ("tops": a folder of <row>.png + index.json)
        self.tops = []
        if spec.get("tops"):
            try:
                with open(os.path.join(_tiles_dir(), spec["tops"], "index.json"), encoding="utf-8") as f:
                    for r, (x, y) in json.load(f).items():
                        key = ("top", spec["tops"], r, tile)
                        if key not in _CACHE:   # (its pixels from the scaled ground itself, its shape from the cut-out: no seams)
                            im = _load("%s/%s.png" % (spec["tops"], r))
                            rect = pygame.Rect(round(x * k), round(y * k), max(1, round(im.get_width() * k)), max(1, round(im.get_height() * k)))
                            mask = pygame.transform.scale(im, rect.size).convert_alpha()
                            mask.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
                            part = pygame.Surface(rect.size, pygame.SRCALPHA)
                            part.blit(self.ground, (0, 0), rect)
                            part.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                            _CACHE[key] = part
                        self.tops.append((int(r), _CACHE[key], x * k, y * k - self.top))
            except (OSError, ValueError, pygame.error):
                self.tops = []

    def lift_tile(self, x, y):
        if 0 <= y < len(self.lifts) and 0 <= x < len(self.lifts[y]):
            return self.lifts[y][x]
        return 0.0

    def lift(self, fx, fy):
        """How far (tiles) someone at (fx, fy) (fractional, mid-step) is raised: between the two tiles they're crossing."""
        x0, y0 = int(fx // 1), int(fy // 1)
        ax, ay = fx - x0, fy - y0
        a = self.lift_tile(x0, y0)
        if ax > 1e-3:
            a = a + (self.lift_tile(x0 + 1, y0) - a) * ax
        if ay > 1e-3:
            a = a + (self.lift_tile(x0, y0 + 1) - a) * ay
        return a

    def span(self):
        """(top, bottom) px of everything drawn, from the map's row 0."""
        return -self.top, self.ground.get_height() - self.top

    def draw_ground(self, screen, ox, oy):
        screen.blit(self.ground, (ox, oy - self.top))

    def buildings_drawn(self, ox, oy, view):
        """[(depth px, image, topleft)] for every building, at the lean for where it stands in the view."""
        T = self.tile
        out = []
        for b in self.buildings:
            ax = ox + b.at[0] * T
            ay = oy + (b.at[1] - b.lift) * T
            off = (ax - view.centerx) / T
            i = b.n + max(-b.n, min(b.n, round(off * self.lean_tile / b.step)))
            img = b.img(i)
            out.append((oy + b.row * T, img, (round(ax - b.ox), round(ay - b.oy))))
        for r, img, x, y in self.tops:   # (just in front of the row it stands on: someone on that row is in front of it)
            py = oy + y
            if py > view.bottom or py + img.get_height() < view.top:
                continue
            out.append((oy + (r + 1) * T - T // 2, img, (round(ox + x), round(py))))
        return out

    def tile_at(self, wx, wy):
        """The tile drawn under a point (map px from the map's row 0, unlifted): the front-most whose lifted square holds it."""
        T = self.tile
        x = int(wx // T)
        best = None
        for y in range(self.h):
            top = (y - self.lift_tile(x, y)) * T
            if top <= wy < top + T:
                best = (x, y)
        return best if best else (x, int(wy // T))
