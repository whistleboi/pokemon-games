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
