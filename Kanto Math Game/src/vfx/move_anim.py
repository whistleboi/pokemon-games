# [REF-0016: Battle Animations]
"""Move animations (Jordan, 11-04): Pokemon Essentials' animations from the fan game Pokemon Orre 2.1.1
(dev/builders/import_move_animations.py; assets/move_animations), played the way Essentials plays them
(its PBAnimationPlayerX), on our battle screen.

An animation is frames shown 20 a second, each a list of cels. Cel 0 is the user's sprite and cel 1 the
target's: they move, hide, fade or tint the battlers (renderer.py asks battler()). The other cels are
192 x 192 patterns of the animation's graphic sheet, placed by their focus: 0 the screen (512 x 384),
1 the target, 2 the user, 3 the line from the user to the target. Essentials' editor has the user at
(128, 224) and the target at (384, 96); here they are our battlers' centres, and everything is scaled by
how much farther apart ours are. Timings play sounds, flash a battler or the screen, and show or move a
picture behind (background) or in front of (foreground) the battlers.

A foe's move uses the move's foe-side version ("OppMove:") where there is one. That is made with the
editor's user spot on your Pokemon, so Essentials plays it with the user and the target swapped (and so do
we); else the move's own version, with the user and target where they are."""
import gzip
import json
import math
import os
import re

import pygame

FPS = 20
CELL = 192
USER0, TARGET0 = complex(128, 224), complex(384, 96)  # Essentials' editor: the user and the target
SCREEN0 = (512, 384)
# cel fields, as the importer keeps them
PATTERN, X, Y, ZOOM_X, ZOOM_Y, ANGLE, MIRROR, OPACITY, BLEND, FOCUS, VISIBLE, PRIORITY, \
    COL_R, COL_G, COL_B, COL_A, SHEET = range(17)

_data = None


def _anims(assets_dir):
    global _data
    if _data is None:
        path = os.path.join(assets_dir or "", "move_animations", "animations.json.gz")
        try:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                _data = json.load(f)
        except (OSError, ValueError):
            _data = {}
    return _data


def move_key(name):
    """Essentials' name for a move: "DOUBLE-EDGE" -> "DOUBLEEDGE"."""
    return re.sub(r"[^A-Z0-9]", "", str(name).upper())


def find(assets_dir, move, user_side):
    """(animation, swapped) for a move used by a side's Pokemon (swapped: a foe-side version, played with
    the user and target swapped), or (None, False)."""
    anims, key = _anims(assets_dir), move_key(move)
    if user_side == "opponent" and f"OppMove:{key}" in anims:
        return anims[f"OppMove:{key}"], True
    return anims.get(f"Move:{key}"), False


def common(assets_dir, name):
    """A common animation ("Burn", "StatUp"...), or None."""
    return _anims(assets_dir).get(f"Common:{name}")


class MoveAnimation:
    """One animation playing: update() each game frame, draw_back() after the background, draw() after the
    battlers; battler(side) says how cel 0 / 1 move the battlers. done when it's over."""

    _images = {}
    _sounds = {}

    def __init__(self, game, anim, user_pos, target_pos, scene_height, swapped=False, user_side="player"):
        self.game, self.anim = game, anim
        if swapped:  # a foe-side version: its "user" is the target (Essentials' pbAnimation)
            user_pos, target_pos = target_pos, user_pos
            user_side = "opponent" if user_side == "player" else "player"
        self.user_side = user_side
        self.target_side = "opponent" if user_side == "player" else "player"
        self.user, self.target = complex(*user_pos), complex(*target_pos)
        span = abs(TARGET0 - USER0)
        self.scale = abs(self.target - self.user) / span
        # the similarity that takes the editor's user-to-target line onto ours
        self.rot = (self.target - self.user) / (TARGET0 - USER0)
        self.screen_k = (game.width / SCREEN0[0], scene_height / SCREEN0[1])
        self.clock = 0.0  # animation frames gone by: the game's update() runs at config.FPS
        self.frame = -1
        self.done = not anim.get("frames")
        self.flashes = []    # [scope, colour, frames left, frames in all]
        self.layers = {"bg": None, "fg": None}  # {image, x, y, opacity, colour, tween}
        self.sheets = [self._image(n) for n in anim.get("graphics") or [anim.get("graphic")]]
        self._scaled = {}

    # ------------------------------------------------------------------ files
    def _file(self, kind, name):
        f = (self.anim.get("files") or {}).get(name)
        return os.path.join(self.game.assets.assets_dir, "move_animations", kind, f) if f else None

    def _image(self, name):
        path = self._file("graphics", name)
        if not path:
            return None
        if path not in self._images:
            try:
                self._images[path] = pygame.image.load(path).convert_alpha()
            except (pygame.error, FileNotFoundError):
                self._images[path] = None
        return self._images[path]

    def _play(self, t):
        path = self._file("sounds", t.get("name"))
        if not path or not pygame.mixer.get_init():
            return
        if path not in self._sounds:
            try:
                self._sounds[path] = pygame.mixer.Sound(path)
            except (pygame.error, FileNotFoundError):
                self._sounds[path] = None
        sound = self._sounds[path]
        if sound:
            from src.core.music import VOLUME
            sound.set_volume(VOLUME * t.get("volume", 100) / 100)
            sound.play()

    # ------------------------------------------------------------------ placing
    def place(self, x, y, focus):
        """Where an editor point lands on our screen."""
        p = complex(x, y)
        if focus == 1:
            q = self.target + (p - TARGET0) * self.scale
        elif focus == 2:
            q = self.user + (p - USER0) * self.scale
        elif focus == 3:
            q = self.user + (p - USER0) * self.rot
        else:
            q = complex(x * self.screen_k[0], y * self.screen_k[1])
        return q.real, q.imag

    def _cels(self):
        frames = self.anim["frames"]
        return frames[min(self.frame, len(frames) - 1)] if self.frame >= 0 else []

    def battler(self, side):
        """(dx, dy, visible, opacity 0..255, tint [r, g, b, a] or None) for a side's battler now."""
        index = 0 if side == self.user_side else 1
        cels = self._cels()
        c = cels[index] if index < len(cels) else None
        tint = self._flash_tint(side)
        if not c:
            return 0, 0, True, 255, tint
        home = USER0 if index == 0 else TARGET0
        bx, by = self.place(home.real, home.imag, c[FOCUS])
        x, y = self.place(c[X], c[Y], c[FOCUS])
        if c[COL_A] and not tint:
            tint = [c[COL_R], c[COL_G], c[COL_B], c[COL_A]]
        return x - bx, y - by, bool(c[VISIBLE]), c[OPACITY], tint

    def _flash_tint(self, side):
        scope = 1 if side == self.target_side else 2
        for s, col, left, total in self.flashes:
            if s == scope and col:
                return [col[0], col[1], col[2], int(col[3] * left / max(1, total))]
        return None

    # ------------------------------------------------------------------ running
    def update(self):
        if self.done:
            return
        from src.config import FPS as GAME_FPS
        self.clock += FPS / GAME_FPS
        while self.frame < int(self.clock):
            self.frame += 1
            if self.frame >= len(self.anim["frames"]):
                self.done = True
                return
            self._tick_frame()

    def _tick_frame(self):
        for f in self.flashes:
            f[2] -= 1
        self.flashes = [f for f in self.flashes if f[2] > 0]
        for layer in self.layers.values():
            tw = layer and layer.get("tween")
            if tw:
                k = 1 / max(1, tw["left"])
                for key, goal in tw["to"].items():
                    cur = layer[key]
                    layer[key] = [a + (b - a) * k for a, b in zip(cur, goal)] if isinstance(goal, list) \
                        else cur + (goal - cur) * k
                tw["left"] -= 1
                if tw["left"] <= 0:
                    layer["tween"] = None
        for t in self.anim.get("timings", []):
            if t.get("frame") != self.frame:
                continue
            kind = t.get("type", 0)
            if kind == 0:
                self._play(t)
                if t.get("flash_scope"):
                    d = t.get("flash_duration", 5)
                    self.flashes.append([t["flash_scope"], t.get("flash_color"), d, d])
            elif kind in (1, 3):  # set the background / foreground picture
                name = "bg" if kind == 1 else "fg"
                img = self._image(t.get("name"))
                self.layers[name] = {"image": img, "x": t.get("bg_x", 0), "y": t.get("bg_y", 0),
                                     "opacity": t.get("opacity", 255), "color": t.get("color") or [0, 0, 0, 0],
                                     "tween": None} if img else None
            elif kind in (2, 4):  # move / fade it over `duration` frames
                layer = self.layers["bg" if kind == 2 else "fg"]
                if layer:
                    to = {k: t[s] for k, s in (("x", "bg_x"), ("y", "bg_y"), ("opacity", "opacity"),
                                               ("color", "color")) if t.get(s) is not None}
                    layer["tween"] = {"to": to, "left": max(1, t.get("duration", 1))}

    # ------------------------------------------------------------------ drawing
    def _layer(self, screen, layer):
        """A background / foreground picture: scaled to our screen's width and tiled (Essentials draws it
        as a plane), at its offset, faded and tinted."""
        if not layer or not layer.get("image") or layer["opacity"] <= 0:
            return
        img = layer["image"]
        k = self.screen_k[0]
        size = (max(1, int(img.get_width() * k)), max(1, int(img.get_height() * k)))
        key = ("layer", id(img), size)
        if key not in self._scaled:
            self._scaled[key] = pygame.transform.smoothscale(img, size)
        pic = self._scaled[key]
        col = layer.get("color") or [0, 0, 0, 0]
        if col[3] > 0:
            pic = tinted(pic, col)
        if layer["opacity"] < 255:
            pic = pic.copy()
            pic.set_alpha(int(layer["opacity"]))
        w, h = pic.get_size()
        x0 = int(layer["x"] * k) % w - w
        y0 = int(layer["y"] * k) % h - h
        for y in range(y0, screen.get_height(), h):
            for x in range(x0, screen.get_width(), w):
                screen.blit(pic, (x, y))

    def draw_back(self, screen):
        """The background picture (behind the battlers)."""
        self._layer(screen, self.layers["bg"])

    def _pattern(self, c):
        index = c[SHEET] if len(c) > SHEET else 0  # (an animation of two sheets: Found Power)
        sheet = self.sheets[index] if index < len(self.sheets) else None
        if sheet is None or c[PATTERN] < 0:
            return None
        zx = abs(c[ZOOM_X]) * self.scale / 100
        zy = abs(c[ZOOM_Y]) * self.scale / 100
        mirror = bool(c[MIRROR])
        angle = c[ANGLE] % 360
        key = (index, c[PATTERN], round(zx, 2), round(zy, 2), angle, mirror)
        if key not in self._scaled:
            cols = max(1, sheet.get_width() // CELL)
            px, py = (c[PATTERN] % cols) * CELL, (c[PATTERN] // cols) * CELL
            cw, ch = min(CELL, sheet.get_width()), min(CELL, sheet.get_height())
            if py + ch > sheet.get_height():
                self._scaled[key] = None
                return None
            img = sheet.subsurface((px, py, cw, ch))
            img = pygame.transform.smoothscale(img, (max(1, int(cw * zx)), max(1, int(ch * zy))))
            if mirror:
                img = pygame.transform.flip(img, True, False)
            if angle:
                img = pygame.transform.rotate(img, angle)
            if len(self._scaled) > 400:
                self._scaled.clear()
            self._scaled[key] = img
        return self._scaled[key]

    def _tinted(self, img, c):
        """A cel's pattern with its colour washed over it (kept: the same tint comes back frame after frame)."""
        if not c[COL_A]:
            return img
        key = ("tint", id(img), c[COL_R], c[COL_G], c[COL_B], c[COL_A])
        if key not in self._scaled:
            self._scaled[key] = tinted(img, [c[COL_R], c[COL_G], c[COL_B], c[COL_A]])
        return self._scaled[key]

    def draw(self, screen):
        """The animation's cels and the foreground picture, over the battlers; then a screen flash."""
        if self.done:
            return
        cels = [c for c in self._cels()[2:] if c and c[VISIBLE] and c[OPACITY] > 0]
        for c in sorted(cels, key=lambda c: c[PRIORITY]):
            img = self._pattern(c)
            if img is None:
                continue
            x, y = self.place(c[X], c[Y], c[FOCUS])
            rect = img.get_rect(center=(int(x), int(y)))
            if c[BLEND] in (1, 2):  # additive / subtractive: the pattern laid on black first (its see-through
                pic = pygame.Surface(img.get_size())  # pixels are often stored white), weighted by the opacity
                pic.blit(self._tinted(img, c), (0, 0))
                o = c[OPACITY]
                if o < 255:
                    pic.fill((o, o, o), special_flags=pygame.BLEND_RGB_MULT)
                screen.blit(pic, rect, special_flags=pygame.BLEND_RGB_ADD if c[BLEND] == 1
                            else pygame.BLEND_RGB_SUB)
            else:  # (a cel's colour washes over its pattern's own pixels, as Essentials' sprite colour does)
                img = self._tinted(img, c)
                if c[OPACITY] < 255:
                    img = img.copy()
                    img.set_alpha(c[OPACITY])
                screen.blit(img, rect)
        self._layer(screen, self.layers["fg"])
        for scope, col, left, total in self.flashes:
            if scope == 3 and col:
                s = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                s.fill((col[0], col[1], col[2], int(col[3] * left / max(1, total))))
                screen.blit(s, (0, 0))


def tinted(img, tint, opacity=255):
    """A battler's sprite with a cel's or flash's colour laid over it (its shape kept), and faded."""
    if not tint and opacity >= 255:
        return img
    out = img.copy()
    if tint and tint[3] > 0:  # colour * a + pixel * (1 - a), the alpha left alone
        a = max(0, min(255, int(tint[3])))
        out.fill((255 - a, 255 - a, 255 - a, 255), special_flags=pygame.BLEND_RGBA_MULT)
        out.fill((int(tint[0]) * a // 255, int(tint[1]) * a // 255, int(tint[2]) * a // 255, 0),
                 special_flags=pygame.BLEND_RGBA_ADD)
    if opacity < 255:
        out.set_alpha(max(0, int(opacity)))
    return out
