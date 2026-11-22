# [REF-0085: Game font]
"""The game's Pokemon font (pokemon_gsc.ttf), set like the games' text.

The .ttf gives every character the same wide cell ("W h a t  w i l l"), which made long lines
hard to read and wrap early. TightFont lays characters out by their real ink width plus a small
gap, so text reads like the games' (proportional) font while keeping the same letters and the
clear digits math needs. Glyphs and whole lines are cached, since text is redrawn every frame."""
import pygame


class TightFont(pygame.font.Font):
    """pygame Font with proportional spacing: render/size/metrics-compatible.

    The font's own "é" squashes the e to fit its accent, so "Pokémon" looked off (Jordan): it is
    drawn here as the font's plain "e" with a two-pixel accent above, on the font's pixel grid."""

    ACCENTED = {"é": "e"}

    def __init__(self, path, size, gap=None):
        super().__init__(path, size)
        self.px = size
        self.gap = max(1, round(size / 9)) if gap is None else gap
        self.space = max(4, round(size * 0.36))
        self._glyphs = {}
        self._lines = {}

    def _layout(self, text):
        """x of each character's ink (None for spaces) and the line width."""
        xs, x = [], 0
        base = "".join(self.ACCENTED.get(ch, ch) for ch in text)
        mets = self.metrics(base) if text else []
        for ch, m in zip(text, mets):
            if ch == " " or m is None or m[1] <= m[0]:
                xs.append(None)
                x += self.space
                continue
            xs.append(x - m[0])
            x += (m[1] - m[0]) + self.gap
        return xs, max(1, x - self.gap if x else 1)

    def _accented(self, ch, antialias, color):
        """The plain letter with an acute accent: two font pixels rising to the right, one pixel
        row above the letter (the GSC font's 'e' is 5 pixels tall, which gives the pixel size)."""
        glyph = pygame.font.Font.render(self, self.ACCENTED[ch], antialias, color).copy()
        ink = glyph.get_bounding_rect()
        u = max(1, round(ink.h / 5))
        cx = ink.x + ink.w // 2
        for k in range(2):
            pygame.draw.rect(glyph, color, (cx - u // 2 + k * u, ink.y - 2 * u - k * u, u, u))
        return glyph

    def size(self, text):
        return self._layout(str(text))[1], self.get_height()

    def render(self, text, antialias, color, bg=None):
        text = str(text)
        key = (text, bool(antialias), tuple(color), tuple(bg) if bg else None)
        hit = self._lines.get(key)
        if hit is not None:
            return hit
        xs, w = self._layout(text)
        surf = pygame.Surface((w, self.get_height()), pygame.SRCALPHA)
        if bg:
            surf.fill(bg)
        for ch, x in zip(text, xs):
            if x is None:
                continue
            gk = (ch, bool(antialias), tuple(color))
            glyph = self._glyphs.get(gk)
            if glyph is None:
                glyph = self._glyphs[gk] = (self._accented(ch, antialias, color) if ch in self.ACCENTED
                                            else pygame.font.Font.render(self, ch, antialias, color))
            surf.blit(glyph, (x, 0))
        if len(self._lines) > 2000:  # a long session: start the cache over
            self._lines.clear()
        self._lines[key] = surf
        return surf


# [REF-0085b: Pixel font]
class PixelFont:
    """The Solar Eclipse look's font (Power Clear, from Pokemon Essentials' font pack), drawn
    as a true pixel font (Jordan, 11-21: the UI restyle after Solar Eclipse).

    The .ttf is a pixel font whose pixels sit on a grid at size 13 (one font pixel = one screen
    pixel). Its file has two faults: the space glyph carries a stray mark, and get_height() is
    shorter than its letters, so plain rendering left marks after words and cut letters off.
    Here every glyph is drawn once at the grid size, scaled up by `scale` with whole-pixel
    (nearest) scaling, and laid out by the font's own advances; spaces are only a gap.
    Characters the font lacks come from the fallback font, sized to match.

    Works where a pygame Font is expected: render, size, get_height, get_linesize, get_ascent,
    metrics-free. `size` is the requested point size (as the old fonts were asked for)."""

    NATIVE = 13
    # The font's own stand-ins: its "$" is drawn as the Pokedollar sign, and it has no long dash.
    SWAP = {"₽": "$", "—": "-", "–": "-", "−": "-", "’": "'"}
    _base = {}  # path -> (pygame Font at 13, its notdef glyph bytes, line height, top trim)

    def __init__(self, path, size, scale=None, fallback=None):
        self.path, self.px = path, size
        self.scale = scale if scale is not None else self.scale_for(size)
        self.fallback = fallback
        base = PixelFont._base.get(path)
        if base is None:
            f = pygame.font.Font(path, self.NATIVE)
            notdef = pygame.image.tostring(f.render("\U000E0001", False, (255, 255, 255)), "RGBA")
            sample = "".join(chr(c) for c in range(33, 127)) + "éÉ"
            tops, bottoms = [], []
            for ch in sample:
                r = f.render(ch, False, (255, 255, 255)).get_bounding_rect()
                if r.h:
                    tops.append(r.y); bottoms.append(r.bottom)
            top = min(tops)
            base = PixelFont._base[path] = (f, notdef, max(bottoms) - top, top)
        self._f, self._notdef, self._lh, self._top = base
        self.space = max(2, self._f.metrics(" ")[0][4])
        self.gap = 0
        self._glyphs = {}
        self._lines = {}
        self._adv = {}
        self.bold = False
        self._swap = str.maketrans(self.SWAP)

    @staticmethod
    def scale_for(size):
        """The old fonts' point size -> a pixel scale (their capitals were ~0.9x the size, Power
        Clear's 9 font pixels): whole steps, or half steps below 2 so small text stays small."""
        k = size / 10.0
        return max(1.5, round(k * 2) / 2) if k < 2 else float(max(2, round(k)))

    # -- pygame Font look-alikes
    def get_height(self):
        return int(round(self._lh * self.scale)) + max(1, int(self.scale))

    def get_linesize(self):
        return self.get_height() + max(2, int(self.scale * 2))

    def get_ascent(self):
        return int(round((self._lh - 3) * self.scale))

    def get_descent(self):
        return -int(round(3 * self.scale))

    def set_bold(self, value):
        self.bold = bool(value)

    def get_bold(self):
        return self.bold

    def set_italic(self, value):
        pass

    def set_underline(self, value):
        pass

    def can_draw(self, ch):
        """A character this font draws itself (typed names keep only these: Utils.typable)."""
        ch = str(ch).translate(self._swap)
        return ch.isprintable() and all(self._has(c) for c in ch)

    def _has(self, ch):
        if ch in self._adv:
            return self._adv[ch] is not None
        if ch == " ":
            self._adv[ch] = self.space
            return True
        surf = self._f.render(ch, False, (255, 255, 255))
        m = self._f.metrics(ch)
        ok = (pygame.image.tostring(surf, "RGBA") != self._notdef
              and bool(m and m[0] and m[0][4] > 0))  # (missing letters have no advance)
        self._adv[ch] = (m[0][4] if m and m[0] else surf.get_width()) if ok else None
        return ok

    def _glyph(self, ch, color):
        key = (ch, color)
        g = self._glyphs.get(key)
        if g is None:
            if self._has(ch):
                src = self._f.render(ch, False, color)
                h = self._lh
                crop = pygame.Surface((src.get_width(), h), pygame.SRCALPHA)
                crop.blit(src, (0, -self._top))
                g = pygame.transform.scale(crop, (max(1, round(crop.get_width() * self.scale)),
                                                  max(1, round(h * self.scale))))
            elif self.fallback is not None:
                h = int(round(self._lh * self.scale))
                g = self.fallback.render(ch, False, color)
                if g.get_height() and g.get_height() != h:
                    g = pygame.transform.scale(g, (max(1, g.get_width() * h // g.get_height()), h))
            else:
                g = pygame.Surface((max(1, int(4 * self.scale)), 1), pygame.SRCALPHA)
            self._glyphs[key] = g
        return g

    def _advance(self, ch):
        if self._has(ch):
            return int(round(self._adv[ch] * self.scale))
        return self._glyph(ch, (255, 255, 255)).get_width() + int(self.scale)

    def size(self, text):
        text = str(text).translate(self._swap)
        return sum(self._advance(ch) for ch in text), self.get_height()

    def render(self, text, antialias=False, color=(255, 255, 255), background=None):
        text = str(text).translate(self._swap)
        color = tuple(color)[:3]
        key = (text, color, tuple(background) if background else None)
        hit = self._lines.get(key)
        if hit is not None:
            return hit
        w, h = self.size(text)
        surf = pygame.Surface((max(1, w), h), pygame.SRCALPHA)
        if background:
            surf.fill(background)
        x = 0
        for ch in text:
            if ch != " ":
                surf.blit(self._glyph(ch, color), (x, 0))
            x += self._advance(ch)
        if len(self._lines) > 3000:
            self._lines.clear()
        self._lines[key] = surf
        return surf
