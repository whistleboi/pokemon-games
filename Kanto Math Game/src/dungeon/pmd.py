"""Pokemon Mystery Dungeon art for the Giant Volcano easter egg (Jordan, 11-16): the dungeon's own tiles and the
Pokemon's own sprites, in assets/dungeon/pmd.

Tiles: assets/dungeon/pmd/<tileset>/chunks_<k>.png (every 24 x 24 chunk of the tileset in one column, one picture for
each step of its palette animation: the lava's glow) and dma.json (which chunk goes where), read out of Explorers of
Sky by kanto_handoff/pmd_rom_tools/export_tileset.py. A tile's chunk depends on its eight neighbours, as in the game:
for a wall or lava tile a neighbour's bit is set when it is the same kind, for a floor tile when it is not a wall
(off the map counts as wall). Bits: S 1, SE 2, E 4, NE 8, N 16, NW 32, W 64, SW 128.

Sprites: assets/dungeon/pmd/<species>/<Anim>-Anim.png + AnimData.xml (and shiny/), from the PMD Sprite Repository
(PMDCollab/SpriteCollab; CREDITS.md). Each sheet is a row of frames for each of eight directions (down, down-right,
right, up-right, up, up-left, left, down-left)."""
import json
import os
import random
import xml.etree.ElementTree as ET

import pygame

from src.dungeon import core

CHUNK = 24
BITS = ((0, 1, 1), (1, 1, 2), (1, 0, 4), (1, -1, 8), (0, -1, 16), (-1, -1, 32), (-1, 0, 64), (-1, 1, 128))
ROW = {(0, 1): 0, (1, 1): 1, (1, 0): 2, (1, -1): 3, (0, -1): 4, (-1, -1): 5, (-1, 0): 6, (-1, 1): 7}
FPS_PMD = 60   # (the durations in AnimData.xml and the lava's are the DS's frames)

_cache = {}


def root(game):
    return os.path.join(game.assets.assets_dir or "assets", "dungeon", "pmd")


# ---------------------------------------------------------------- the tiles
def _kind(t):
    return "wall" if t == core.WALL else "water" if t == core.WATER else "floor"


def neighbours(floor, x, y):
    """The neighbour bits of tile (x, y) (see the top of this file)."""
    me = _kind(floor.tile(x, y))
    ns = 0
    for dx, dy, b in BITS:
        nx, ny = x + dx, y + dy
        n = _kind(floor.tile(nx, ny)) if floor.inside(nx, ny) else "wall"
        if me == "floor":
            ns |= b if n != "wall" else 0
        else:
            ns |= b if n == me else 0
    return ns


class Tileset:
    """One exported tileset: its chunks (for every lava-glow step) scaled to the map's tile."""

    def __init__(self, game, name, tile):
        base = os.path.join(root(game), name)
        with open(os.path.join(base, "dma.json"), encoding="utf-8") as f:
            self.dma = json.load(f)
        self.tile = tile
        n = max(1, int(self.dma.get("anim_frames") or 0))
        self.sheets = [pygame.image.load(os.path.join(base, f"chunks_{k}.png" if self.dma.get("anim_frames") else "chunks.png")).convert()
                       for k in range(n)]
        speed = self.dma.get("anim_speed") or [12]
        self.step_ms = max(40, int(1000 * (speed[0] or 12) / FPS_PMD))
        self._chunks = {}
        self._moving = {}

    def chunk(self, i, frame=0):
        key = (i, frame)
        if key not in self._chunks:
            sheet = self.sheets[frame % len(self.sheets)]
            sub = sheet.subsurface((0, i * CHUNK, CHUNK, CHUNK))
            self._chunks[key] = pygame.transform.scale(sub, (self.tile, self.tile))
        return self._chunks[key]

    def animated(self, i):
        """Does chunk i glow (change between the palette steps)?"""
        if i not in self._moving:
            first = pygame.image.tostring(self.sheets[0].subsurface((0, i * CHUNK, CHUNK, CHUNK)), "RGB")
            self._moving[i] = any(pygame.image.tostring(s.subsurface((0, i * CHUNK, CHUNK, CHUNK)), "RGB") != first
                                  for s in self.sheets[1:])
        return self._moving[i]

    def frame_now(self, ticks=None):
        ticks = pygame.time.get_ticks() if ticks is None else ticks
        return (ticks // self.step_ms) % len(self.sheets)

    def render(self, floor, seed=0):
        """The floor as one picture (the first glow step) and {tile: chunk} of the tiles that glow."""
        rng = random.Random(seed)
        surf = pygame.Surface((floor.w * self.tile, floor.h * self.tile))
        glow = {}
        for y in range(floor.h):
            for x in range(floor.w):
                k = _kind(floor.tile(x, y))
                i = self.dma[k][neighbours(floor, x, y)][rng.randrange(3)]
                surf.blit(self.chunk(i), (x * self.tile, y * self.tile))
                if len(self.sheets) > 1 and self.animated(i):
                    glow[(x, y)] = i
        return surf, glow


def tileset(game, name, tile):
    key = ("tiles", name, tile)
    if key not in _cache:
        try:
            _cache[key] = Tileset(game, name, tile)
        except (OSError, ValueError, KeyError, pygame.error):
            _cache[key] = None
    return _cache[key]


# ---------------------------------------------------------------- the sprites
def anims(game, pid, shiny=False):
    """{anim name: (sheet path, frame w, frame h, [durations])} for a species (its shiny sheets if it has them)."""
    key = ("anims", int(pid), bool(shiny))
    if key in _cache:
        return _cache[key]
    out = {}
    for base in ([os.path.join(root(game), str(int(pid)), "shiny")] if shiny else []) + [os.path.join(root(game), str(int(pid)))]:
        path = os.path.join(base, "AnimData.xml")
        if not os.path.isfile(path):
            continue
        try:
            tree = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        raw = {}
        for a in tree.iter("Anim"):
            name = a.findtext("Name")
            raw[name] = a
        for name, a in raw.items():
            src = a
            if a.find("CopyOf") is not None:
                src = raw.get(a.findtext("CopyOf"), a)
            sheet = os.path.join(base, f"{src.findtext('Name')}-Anim.png")
            fw, fh = src.findtext("FrameWidth"), src.findtext("FrameHeight")
            if not (fw and fh and os.path.isfile(sheet)):
                continue
            durs = [int(d.text) for d in src.iter("Duration")] or [8]
            hit = src.findtext("HitFrame")
            out[name] = (sheet, int(fw), int(fh), durs, int(hit) if hit else None)
        break
    _cache[key] = out
    return out


def has(game, pid):
    return bool(anims(game, pid))


def _sheet(path):
    key = ("sheet", path)
    if key not in _cache:
        _cache[key] = pygame.image.load(path).convert_alpha()
    return _cache[key]


def frame_at(durs, ms, loop=True):
    """Which frame of an animation is showing ms milliseconds in."""
    t = ms * FPS_PMD // 1000
    total = sum(durs)
    if loop:
        t %= max(1, total)
    for i, d in enumerate(durs):
        if t < d:
            return i
        t -= d
    return len(durs) - 1


def image(game, pid, shiny=False, anim="Idle", facing=(0, 1), ms=None, scale=2.0, loop=True):
    """One frame of a species' PMD animation, scaled, cropped to the animation's own box (so its feet stay put:
    drawn by its midbottom). None if the species has no PMD sprite."""
    table = anims(game, pid, shiny)
    if anim not in table:
        anim = "Walk" if "Walk" in table else next(iter(table), None)
        if anim is None:
            return None
    path, fw, fh, durs, _hit = table[anim]
    ms = pygame.time.get_ticks() if ms is None else ms
    col = frame_at(durs, ms, loop)
    row = ROW.get((max(-1, min(1, facing[0])), max(-1, min(1, facing[1]))), 0)
    key = ("img", path, col, row, scale)
    if key not in _cache:
        sheet = _sheet(path)
        rows = max(1, sheet.get_height() // fh)
        row = min(row, rows - 1)
        box = _cache.get(("box", path))
        if box is None:  # (one box for every frame of the sheet: no jitter)
            for c in range(sheet.get_width() // fw):
                for r in range(rows):
                    b = sheet.subsurface((c * fw, r * fh, fw, fh)).get_bounding_rect()
                    if b.w and b.h:
                        box = b if box is None else box.union(b)
            box = box or pygame.Rect(0, 0, fw, fh)
            _cache[("box", path)] = box
        cell = sheet.subsurface((col * fw + box.x, row * fh + box.y, box.w, box.h))
        _cache[key] = pygame.transform.scale(cell, (max(1, round(box.w * scale)), max(1, round(box.h * scale))))
    return _cache[key]


def length_ms(game, pid, anim, shiny=False):
    table = anims(game, pid, shiny)
    if anim not in table:
        return 0
    return sum(table[anim][3]) * 1000 // FPS_PMD
