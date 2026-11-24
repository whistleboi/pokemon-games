# [REF-0086: UI theme]
"""One look for every screen.

11-21 restyle (Jordan: "sleek, dynamic, modern", after the fan game Solar Eclipse): dark charcoal
panels with cut corners and a small tab of coloured slashes, a navy grid behind every menu that
drifts slowly, a bold colour band per menu, buttons with a colour wedge, the Power Clear pixel
font (src/ui/fonts.py PixelFont), white text with a dark drop shadow. Everything is drawn in code
(no Solar Eclipse pictures), so it stays sharp at 1280x720 and on phones.

The function names are the ones every screen already calls: draw_panel, draw_textbox,
shadow_text, command_button, menu_background, card, hp_bar, status_tag, popup_panel, text_field."""
import pygame

PANEL = (46, 46, 52)
PANEL_INNER = (38, 38, 44)
PANEL_EDGE = (92, 94, 106)       # the thin light line inside a panel's frame
PANEL_BORDER = (12, 12, 16)
SHADOW = (0, 0, 0, 110)

TEXTBOX = (32, 32, 38)
TEXTBOX_FRAME = (12, 12, 16)
TEXTBOX_ACCENT = (240, 176, 0)   # the message bar's yellow line
TEXT = (248, 248, 248)
TEXT_SHADOW = (20, 20, 26)
TEXT_ARROW = (240, 176, 0)
TEXT_DIM = (176, 182, 200)
TEXT_LABEL = (150, 190, 255)     # field names on panels (Dex No., Ability...)

INFOBOX = (36, 36, 42)
INFOBOX_FRAME = (12, 12, 16)
INFOBOX_ACCENT = (70, 70, 80)

CARD = (54, 54, 62)
CARD_HOVER = (68, 68, 78)
CARD_OFF = (40, 40, 46)

FIGHT = (212, 48, 40)
BAG = (232, 168, 24)
POKEMON = (40, 176, 72)
RUN = (40, 120, 232)
MEGA = (140, 52, 232)

HP_GREEN, HP_YELLOW, HP_RED = (72, 208, 96), (240, 200, 40), (232, 72, 64)
EXP_BLUE = (70, 170, 250)

GRID_BG = (16, 22, 36)
GRID_LINE = (27, 36, 56)
GRID_MAJOR = (38, 52, 78)


def lum(color):
    return 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]


def mix(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def chamfer(rect, c=12, tl=True, tr=True, br=True, bl=True):
    """The corners cut off at 45 degrees (Solar Eclipse's panels), as polygon points."""
    x, y, w, h = pygame.Rect(rect)
    c = max(0, min(c, w // 2, h // 2))
    p = []
    p += [(x, y + c), (x + c, y)] if tl else [(x, y)]
    p += [(x + w - 1 - c, y), (x + w - 1, y + c)] if tr else [(x + w - 1, y)]
    p += [(x + w - 1, y + h - 1 - c), (x + w - 1 - c, y + h - 1)] if br else [(x + w - 1, y + h - 1)]
    p += [(x + c, y + h - 1), (x, y + h - 1 - c)] if bl else [(x, y + h - 1)]
    return p


def alpha_poly(surface, color, pts, alpha):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, y0 = min(xs), min(ys)
    t = pygame.Surface((max(xs) - x0 + 1, max(ys) - y0 + 1), pygame.SRCALPHA)
    pygame.draw.polygon(t, (*color[:3], alpha), [(px - x0, py - y0) for px, py in pts])
    surface.blit(t, (x0, y0))


def _cut(radius):
    """The old rounded corners' radius -> a corner cut (small boxes keep small cuts)."""
    return max(4, min(16, int(radius)))


def _shadow(surface, rect, radius):
    alpha_poly(surface, (0, 0, 0), chamfer(pygame.Rect(rect).move(6, 6), _cut(radius), tl=False, br=True),
               SHADOW[3])


def slashes(surface, x, y, h, color, n=3):
    """The coloured slash marks on a panel's tab (///)."""
    for i in range(n):
        px = x + i * max(6, h // 2 + 2)
        pygame.draw.polygon(surface, color, [(px + h // 2, y), (px + h // 2 + max(3, h // 3), y),
                                             (px + max(3, h // 3), y + h), (px, y + h)])


def draw_panel(surface, rect, radius=14, accent=None, tab=True):
    """The menu panel: dark charcoal, the top-left and bottom-right... corners cut, a thin light
    line inside the dark frame, and (big enough panels) a small tab above it with coloured slashes."""
    rect = pygame.Rect(rect)
    c = _cut(radius)
    _shadow(surface, rect, radius)
    pts = chamfer(rect, c, tl=False)
    pygame.draw.polygon(surface, PANEL, pts)
    if rect.w > 40 and rect.h > 30:
        pygame.draw.polygon(surface, PANEL_INNER, chamfer(rect.inflate(-12, -12), max(3, c - 4), tl=False))
        pygame.draw.polygon(surface, PANEL_EDGE, chamfer(rect.inflate(-8, -8), max(3, c - 3), tl=False), 1)
    pygame.draw.polygon(surface, PANEL_BORDER, pts, 3)
    if tab and rect.w >= 160 and rect.h >= 80 and rect.y >= 12:
        tw = min(96, rect.w // 3)
        tab_r = pygame.Rect(rect.x + 12, rect.y - 11, tw, 12)
        pygame.draw.polygon(surface, PANEL_BORDER, chamfer(tab_r.inflate(0, 2), 6, bl=False, br=False, tl=False))
        slashes(surface, tab_r.x + 10, tab_r.y + 3, 8, accent or ACCENT_TAB)


ACCENT_TAB = (40, 150, 232)


def draw_textbox(surface, rect, radius=14, flush=False):
    """The message box (Solar Eclipse / Elite Battle style): near black, a light inner line, a
    yellow line along the top, two corners cut. flush (a battle's box, Sinnoh 11-24): set right
    against the field above it - no shadow, no dark band over the inner line, which runs along the top."""
    rect = pygame.Rect(rect)
    c = _cut(radius)
    if not flush:
        _shadow(surface, rect, radius)
    pts = chamfer(rect, c, tl=False, br=True, tr=False, bl=False)
    pygame.draw.polygon(surface, TEXTBOX, pts)
    if rect.h > 26 and rect.w > 40:
        inner = rect.inflate(-10, -10) if not flush else pygame.Rect(rect.x + 5, rect.y + 2, rect.w - 10, rect.h - 7)
        pygame.draw.polygon(surface, (62, 62, 72), chamfer(inner, max(3, c - 5), tl=False, tr=False, bl=False), 2)
    pygame.draw.polygon(surface, TEXTBOX_FRAME, pts, 3)
    if rect.w > 120 and rect.h > 40:
        pygame.draw.line(surface, TEXTBOX_ACCENT, (rect.x + 3, rect.y + 2), (rect.x + min(rect.w // 3, 260), rect.y + 2), 3)


def adapt(color, shadow):
    """Colours chosen for the old light boxes (dark text, pale shadow) made readable on the dark
    panels: the pale shadow turns dark, dark text turns white (or a light tint of its colour)."""
    color, shadow = tuple(color)[:3], tuple(shadow)[:3]
    if lum(shadow) > 150 and lum(color) < lum(shadow):
        shadow = TEXT_SHADOW
        if lum(color) < 130:
            grey = max(color) - min(color) < 40
            if grey and lum(color) >= 90:     # the old grey labels ("Name", "Reward"): the label blue
                color = TEXT_LABEL
            else:
                color = TEXT if grey else mix(color, (255, 255, 255), 0.45)
    return color, shadow


def shadow_text(surface, text, font, x, y, color=TEXT, shadow=TEXT_SHADOW, align="left"):
    """White text with a dark drop shadow one font pixel down and right. y is the text's top
    (centre if align=center)."""
    color, shadow = adapt(color, shadow)
    surf = font.render(str(text), False, color)
    sh = font.render(str(text), False, shadow)
    w, h = surf.get_size()
    if align == "center":
        x, y = x - w // 2, y - h // 2
    elif align == "right":
        x -= w
    d = max(1, int(getattr(font, "scale", 0) or font.get_height() // 14))
    surface.blit(sh, (x + d, y + d))
    surface.blit(sh, (x + d, y))
    surface.blit(sh, (x, y + d))
    surface.blit(surf, (x, y))
    return pygame.Rect(x, y, w, h)


SYMBOLS = ("<", "=", ">")


def answer_text(surface, text, font, x, y, color=TEXT, shadow=TEXT_SHADOW):
    """An answer centred at (x, y): <, = and > drawn big and bold (the number font's are tiny),
    anything else as shadow_text."""
    text = str(text)
    if text not in SYMBOLS:
        return shadow_text(surface, text, font, x, y, color=color, shadow=shadow, align="center")
    s = max(10, int(font.get_height() * 0.42))  # half its size
    _symbol(surface, text, x, y, s, color, shadow)
    return pygame.Rect(x - s, y - s, 2 * s, 2 * s)


def _symbol(surface, text, x, y, s, color, shadow):
    """<, = or > as bold strokes, centred at (x, y), s its half-height."""
    w = max(4, s // 2)
    if text == "=":
        lines = [((x - s, y - s // 2), (x + s, y - s // 2)), ((x - s, y + s // 2), (x + s, y + s // 2))]
    else:
        d = -1 if text == "<" else 1
        k = s * 0.7
        lines = [((x - d * k, y - s), (x + d * k, y)), ((x + d * k, y), (x - d * k, y + s))]
    for off, col in ((max(2, w // 3), shadow), (0, color)):
        for p0, p1 in lines:
            p0, p1 = (p0[0] + off, p0[1] + off), (p1[0] + off, p1[1] + off)
            pygame.draw.line(surface, col, p0, p1, w)
            for pt in (p0, p1):
                pygame.draw.circle(surface, col, (int(pt[0]), int(pt[1])), w // 2)


def math_text(surface, text, font, x, y, color=TEXT, shadow=TEXT_SHADOW):
    """A question centred at (x, y), its < and > drawn bold (the number font's are tiny)."""
    text = str(text)
    if "<" not in text and ">" not in text:
        return shadow_text(surface, text, font, x, y, color=color, shadow=shadow, align="center")
    import re as _re
    parts = [t for t in _re.split(r"\s*([<>])\s*", text) if t != ""]
    ink = font.render("8", False, (0, 0, 0)).get_bounding_rect().h or font.get_height() // 2
    s = max(6, int(ink * 0.5))  # as tall as the digits
    gap = max(font.size(" ")[0], s)
    widths = [(2 * s + 2 * gap) if t in "<>" else font.size(t)[0] for t in parts]
    left = x - sum(widths) // 2
    for t, w in zip(parts, widths):
        if t in ("<", ">"):
            _symbol(surface, t, left + w // 2, y, s, color, shadow)
        else:
            shadow_text(surface, t, font, left, y - font.get_height() // 2, color=color, shadow=shadow)
        left += w
    return pygame.Rect(x - sum(widths) // 2, y - font.get_height() // 2, sum(widths), font.get_height())


def command_button(surface, rect, label, font, color, hover=False, small=None, sub=None):
    """A button (battle commands FIGHT / BAG / POKEMON / RUN, and every other button).

    Wide buttons: a dark body with fine lines and a colour wedge on the right (Elite Battle's
    command buttons). Narrow ones (BACK, tabs, YES/NO): the colour itself, both ends cut.
    The frame turns white while the pointer or the keys are on it."""
    rect = pygame.Rect(rect)
    from src.utils import Utils
    color = tuple(color)[:3]
    c = max(4, min(12, rect.h // 4))
    wide = rect.w >= 200 and rect.h >= 44
    pts = chamfer(rect, c)
    alpha_poly(surface, (0, 0, 0), chamfer(rect.move(4, 4), c), 110)
    if wide:
        pygame.draw.polygon(surface, (48, 48, 56) if hover else (38, 38, 44), pts)
        wedge = max(56, rect.w // 4)
        for k in range(rect.x + 12, rect.right - wedge - 16, 8):
            pygame.draw.line(surface, (60, 60, 68) if hover else (50, 50, 58), (k, rect.y + 7), (k, rect.bottom - 8))
        wx = rect.right - wedge
        pygame.draw.polygon(surface, mix(color, (255, 255, 255), 0.15) if hover else color,
                            [(wx, rect.y), (rect.right - 1 - c, rect.y), (rect.right - 1, rect.y + c),
                             (rect.right - 1, rect.bottom - 1 - c), (rect.right - 1 - c, rect.bottom - 1),
                             (wx - rect.h // 3, rect.bottom - 1)])
        pygame.draw.polygon(surface, (255, 255, 255) if hover else color, pts, 3 if hover else 2)
        cx = rect.x + (rect.w - wedge) // 2 + 4
        cy = rect.centery - (8 if sub and small else 0)
        Utils.draw_text_outline(surface, label, font, (255, 255, 255), cx, cy, outline_color=(16, 16, 20), thickness=2)
        if sub and small:
            Utils.draw_text_outline(surface, sub, small, TEXT_DIM, cx, rect.bottom - 16, outline_color=(16, 16, 20),
                                    thickness=1)
        return
    body = mix(color, (255, 255, 255), 0.14) if hover else color
    pygame.draw.polygon(surface, shade(color, 0.55), chamfer(rect.move(0, 3), c))
    pygame.draw.polygon(surface, body, pts)
    pygame.draw.line(surface, mix(body, (255, 255, 255), 0.35), (rect.x + c, rect.y + 2), (rect.right - 1 - c, rect.y + 2), 2)
    pygame.draw.polygon(surface, (255, 255, 255) if hover else shade(color, 0.45), pts, 3 if hover else 2)
    cy = rect.centery - (8 if sub and small else 0)
    if lum(color) > 165:
        Utils.draw_text_outline(surface, label, font, (40, 30, 6), rect.centerx, cy,
                                outline_color=mix(color, (255, 255, 255), 0.3), thickness=1)
    else:
        Utils.draw_text_outline(surface, label, font, (255, 255, 255), rect.centerx, cy,
                                outline_color=shade(color, 0.35), thickness=2)
    if sub and small:
        Utils.draw_text_outline(surface, sub, small, (255, 255, 255), rect.centerx, rect.bottom - 16,
                                outline_color=shade(color, 0.35), thickness=1)


# ---------------------------------------------------------------- menus (Pokedex, PC, Journal, Bag)
# The menu redesign (Jordan: "like the battle screen"): one frame for every menu screen. A slate
# background with faint stripes, a coloured header band (each menu has its own colour) with BACK
# and the title, white cards with dark text for entries, the battle menu's buttons, and the
# battle text box at the bottom for details.
MENU_BG = GRID_BG
MENU_STRIPE = GRID_LINE
HEADER_H = 84
BACK = (64, 70, 92)          # BACK buttons everywhere
TAB_OFF = (70, 76, 100)      # a tab or toggle that is off
ACCENT = {"dex": (204, 40, 36), "pc": (24, 160, 176), "journal": (232, 150, 16), "bag": (240, 112, 16),
          "party": (28, 172, 64), "mart": (40, 120, 232), "options": (140, 52, 232), "summary": (40, 128, 232)}
STATUS_TAGS = {"burn": ("BRN", (232, 104, 40)), "paralysis": ("PAR", (216, 168, 24)),
               "poison": ("PSN", (156, 60, 176)), "toxic": ("TOX", (112, 36, 128)),
               "sleep": ("SLP", (120, 124, 136)), "freeze": ("FRZ", (80, 176, 224)),
               "faint": ("FNT", (204, 48, 40))}

_bg_cache = {}


def shade(color, k):
    return tuple(max(0, min(255, int(c * k))) for c in tuple(color)[:3])


def tap_marker(surface, rect, good=True):
    """The tile you tapped: a pulsing outline on your destination, red if you can't go there."""
    pulse = (pygame.time.get_ticks() // 8) % 100
    k = abs(pulse - 50) / 50
    color = (255, 226, 90) if good else (232, 70, 60)
    r = pygame.Rect(rect).inflate(-4 - int(6 * k), -4 - int(6 * k))
    fill = pygame.Surface(r.size, pygame.SRCALPHA)
    fill.fill((*color, 70))
    surface.blit(fill, r.topleft)
    pygame.draw.polygon(surface, color, chamfer(r, 6), 4)


def _grid(w, h):
    """The navy grid (64 pixels bigger than the screen each way, so it can drift)."""
    key = ("grid", w, h)
    g = _bg_cache.get(key)
    if g is None:
        g = pygame.Surface((w + 64, h + 64))
        g.fill(GRID_BG)
        for x in range(0, w + 64, 16):
            pygame.draw.line(g, GRID_LINE, (x, 0), (x, h + 64))
        for y in range(0, h + 64, 16):
            pygame.draw.line(g, GRID_LINE, (0, y), (w + 64, y))
        for x in range(0, w + 64, 64):
            pygame.draw.line(g, GRID_MAJOR, (x, 0), (x, h + 64))
        for y in range(0, h + 64, 64):
            pygame.draw.line(g, GRID_MAJOR, (0, y), (w + 64, y))
        _bg_cache[key] = g
    return g


def grid_background(surface, rect=None):
    """The navy grid, drifting slowly up and to the left (the menus' moving backdrop)."""
    w, h = surface.get_size()
    off = (pygame.time.get_ticks() // 45) % 64
    if rect is None:
        surface.blit(_grid(w, h), (-off, -off))
    else:
        rect = pygame.Rect(rect)
        surface.blit(_grid(w, h), rect.topleft, pygame.Rect(off + rect.x, off + rect.y, rect.w, rect.h))


def header_band(surface, accent, h=HEADER_H, y=0):
    """A menu's colour band: the colour, a darker line under it, a light line on top, a run of
    darker slashes at the right end, and a soft shadow below."""
    w = surface.get_width()
    accent = tuple(accent)[:3]
    key = ("band", w, h, accent)
    band = _bg_cache.get(key)
    if band is None:
        band = pygame.Surface((w, h + 14), pygame.SRCALPHA)
        pygame.draw.rect(band, accent, (0, 0, w, h))
        for i in range(12):
            x = w - 360 + i * 30
            pygame.draw.polygon(band, shade(accent, 0.86), [(x + 22, 6), (x + 36, 6), (x + 14, h - 10), (x, h - 10)])
        pygame.draw.rect(band, shade(accent, 0.62), (0, h - 8, w, 8))
        pygame.draw.line(band, mix(accent, (255, 255, 255), 0.35), (0, 2), (w, 2), 2)
        for yy in range(14):
            pygame.draw.line(band, (0, 0, 0, int(110 * (1 - yy / 14))), (0, h + yy), (w, h + yy))
        _bg_cache[key] = band
    surface.blit(band, (0, y))


def menu_background(surface, accent, title=None, font=None, title_x=180):
    """Fill the screen with the menu frame: the drifting grid, the colour band, the title."""
    grid_background(surface)
    header_band(surface, accent)
    if title and font:
        from src.utils import Utils
        Utils.draw_text_outline(surface, title, font, (255, 255, 255), title_x, HEADER_H // 2 - 4,
                                align="left", outline_color=shade(accent, 0.4), thickness=3)


def card(surface, rect, hover=False, selected=False, accent=None, fill=TEXTBOX, radius=12):
    """An entry card (Pokedex entry, Box slot, mission, Bag item): a charcoal slot with two cut
    corners; the chosen one takes the menu's colour, a hovered one lightens."""
    rect = pygame.Rect(rect)
    fill = tuple(fill)[:3]
    if fill == TEXTBOX or fill == (250, 250, 250) or fill == (255, 255, 255):
        body = CARD_HOVER if hover else CARD
    elif lum(fill) > 200 and max(fill) - min(fill) < 30:   # the old greyed-out card
        body = CARD_OFF
    elif lum(fill) > 120:                                   # an old pale tint (a done mission...)
        body = mix(CARD, fill, 0.45 if hover else 0.35)
    else:
        body = mix(fill, (255, 255, 255), 0.1) if hover else fill
    accent = tuple(accent or ACCENT_TAB)[:3]
    if selected:
        body = mix(body, accent, 0.28)
    c = _cut(radius)
    pts = chamfer(rect, c, tl=False, br=True)
    alpha_poly(surface, (0, 0, 0), chamfer(rect.move(3, 4), c, tl=False), 100)
    pygame.draw.polygon(surface, body, pts)
    if rect.h > 20:
        pygame.draw.line(surface, mix(body, (255, 255, 255), 0.18), (rect.x + 3, rect.y + 2), (rect.right - c - 2, rect.y + 2), 2)
    edge = accent if (hover or selected) else PANEL_BORDER
    pygame.draw.polygon(surface, edge, pts, 4 if selected else 3 if hover else 2)
    if selected and rect.h >= 30:
        pygame.draw.rect(surface, accent, (rect.x, rect.y, 8, rect.h))


def status_tag(surface, status, font, x, y):
    """The status tag (BRN, PSN...): a slanted colour tag. Returns its width (0 if healthy)."""
    tag = STATUS_TAGS.get(status or "")
    if not tag:
        return 0
    from src.utils import Utils
    text, color = tag
    w, h = font.size(text)[0] + 20, font.get_height() + 6
    pts = [(x, y), (x + w, y), (x + w - 8, y + h), (x, y + h)]
    pygame.draw.polygon(surface, color, pts)
    pygame.draw.polygon(surface, shade(color, 0.45), pts, 2)
    Utils.draw_text_outline(surface, text, font, (255, 255, 255), x + (w - 6) // 2, y + h // 2,
                            outline_color=shade(color, 0.45), thickness=1)
    return w


def type_tag(surface, label, color, font, x, y, h=None):
    """A type's tag (WATER, FIRE...), slanted on the right like Solar Eclipse's. Returns its width."""
    from src.utils import Utils
    color = tuple(color)[:3]
    h = h or font.get_height() + 8
    w = font.size(label)[0] + 26
    pts = [(x, y), (x + w, y), (x + w - h // 3, y + h), (x, y + h)]
    pygame.draw.polygon(surface, color, pts)
    pygame.draw.line(surface, mix(color, (255, 255, 255), 0.35), (x + 2, y + 2), (x + w - 4, y + 2), 2)
    pygame.draw.polygon(surface, shade(color, 0.45), pts, 2)
    Utils.draw_text_outline(surface, label, font, (255, 255, 255), x + (w - h // 3) // 2 + 2, y + h // 2,
                            outline_color=shade(color, 0.4), thickness=1)
    return w


def hp_bar(surface, x, y, w, hp, max_hp, font=None, h=10):
    """An HP bar: a dark track, the colour fill with a light top line; the numbers under it when
    a font is given."""
    ratio = max(0.0, min(1.0, hp / max_hp)) if max_hp else 0.0
    bar = pygame.Rect(x, y, w, h + 6)
    pygame.draw.rect(surface, PANEL_BORDER, bar)
    inner = bar.inflate(-6, -6)
    pygame.draw.rect(surface, (70, 70, 78), inner)
    color = HP_GREEN if ratio > 0.5 else HP_YELLOW if ratio > 0.2 else HP_RED
    if ratio > 0:
        fw = max(2, int(inner.w * ratio))
        pygame.draw.rect(surface, color, (inner.x, inner.y, fw, inner.h))
        pygame.draw.rect(surface, mix(color, (255, 255, 255), 0.4), (inner.x, inner.y, fw, max(1, inner.h // 3)))
    if font:
        shadow_text(surface, f"{int(hp)}/{int(max_hp)}", font, bar.right, bar.bottom + 4, align="right")
    return bar


def hp_label(surface, x, y, h=18):
    """The small yellow "HP" tag in front of a bar. Returns its width."""
    from src.utils import Utils
    f = FONTS.get("caption")
    w = 38
    pts = [(x, y), (x + w, y), (x + w - 6, y + h), (x, y + h)]
    pygame.draw.polygon(surface, (232, 168, 32), pts)
    pygame.draw.polygon(surface, (120, 70, 0), pts, 2)
    if f:
        Utils.draw_text_outline(surface, "HP", f, (255, 255, 255), x + 16, y + h // 2, outline_color=(120, 70, 0),
                                thickness=1)
    return w


def footer_hints(surface, hints, y=None):
    """The black hint bar along the bottom ("C Choose  X Back"), right-aligned."""
    from src.utils import Utils
    w, h = surface.get_size()
    y = h - 40 if y is None else y
    f = FONTS.get("caption")
    if not f:
        return
    pygame.draw.rect(surface, (10, 10, 12), (0, y, w, h - y))
    pygame.draw.line(surface, (60, 60, 68), (0, y), (w, y), 2)
    x = w - 20
    for key, label in reversed(list(hints)):
        x -= f.size(label)[0]
        shadow_text(surface, label, f, x, y + (h - y - f.get_height()) // 2, color=(220, 220, 228))
        kw = f.size(key)[0] + 16
        x -= kw + 8
        r = pygame.Rect(x, y + 7, kw, h - y - 14)
        pygame.draw.polygon(surface, RUN, chamfer(r, 5))
        Utils.draw_text_outline(surface, key, f, (255, 255, 255), r.centerx, r.centery, outline_color=(10, 40, 90),
                                thickness=1)
        x -= 26


def popup_panel(surface, rect, title=None, font=None):
    """A small pop-up menu (tap a Pokemon: SUMMARY, MOVE...): the charcoal panel, its title on a
    dark strip along the top."""
    rect = pygame.Rect(rect)
    draw_panel(surface, rect, radius=12, tab=False)
    if title and font:
        from src.utils import Utils
        strip = pygame.Rect(rect.x + 3, rect.y + 3, rect.w - 6, min(44, font.get_height() + 16))
        pygame.draw.rect(surface, PANEL_BORDER, strip)
        slashes(surface, strip.x + 10, strip.y + 10, max(8, strip.h - 20), ACCENT_TAB)
        Utils.draw_text_outline(surface, title, font, (255, 255, 255), rect.centerx, strip.centery,
                                outline_color=PANEL_BORDER, thickness=2)


GAME = None  # the running game (set by Game), for the region's PC name


def pokemon_word(text):
    """The area data's short "PKMN" written out (Jordan): POKéMON in capitals ("CATCH WILD
    POKéMON"), Pokémon in ordinary text. "BILL'S PC" becomes the region's own PC (Lanette's PC...)."""
    text = str(text)
    if "BILL'S PC" in text.upper() and GAME is not None:
        import re
        name = GAME.story_manager.pc_name()
        text = re.sub(r"BILL'S PC", name.upper(), text)
        text = re.sub(r"Bill's PC", name, text)
    if "PKMN" not in text:
        return text
    letters = [c for c in text.replace("PKMN", "") if c.isalpha()]
    shouting = letters and sum(c.isupper() for c in letters) > len(letters) * 0.7
    return text.replace("PKMN", "POKéMON" if shouting else "Pokémon")


def text_field(surface, rect, text, font, placeholder="", focused=True):
    """A name box: dark, a colour frame while typing, the typed name with a blinking cursor (or
    the placeholder, the name used if nothing is typed, in grey)."""
    rect = pygame.Rect(rect)
    pygame.draw.polygon(surface, (24, 24, 30), chamfer(rect, 8))
    pygame.draw.polygon(surface, ACCENT_TAB if focused else PANEL_EDGE, chamfer(rect, 8), 3)
    y = rect.centery - font.get_height() // 2
    blink = focused and (pygame.time.get_ticks() // 500) % 2
    if text:
        r = shadow_text(surface, text, font, rect.x + 18, y)
        if blink:
            pygame.draw.rect(surface, TEXT_ARROW, (r.right + 4, y + 2, 4, font.get_height() - 6))
    else:
        shadow_text(surface, placeholder, font, rect.x + 18, y, color=(120, 126, 146))
        if blink:
            pygame.draw.rect(surface, TEXT_ARROW, (rect.x + 14, y + 2, 3, font.get_height() - 6))


# ---------------------------------------------------------------- older screens' buttons
FONTS = {}  # the game's fonts (set by Assets), for buttons made with the old tiny fonts


def theme_color(color):
    """An older screen's button colour mapped onto the battle menu's palette: reds to FIGHT,
    greens to POKEMON, blues to RUN, yellows to BAG, purples to MEGA, greys and black to BACK."""
    r, g, b = [int(c) for c in tuple(color)[:3]]
    hi, lo = max(r, g, b), min(r, g, b)
    if hi - lo < 40:
        return BACK
    if r >= g and r >= b:
        if g > 150 and g > b + 60:
            return BAG if g > r * 0.62 else (232, 132, 40)
        return (232, 132, 40) if g > 100 and b < 80 else FIGHT
    if g >= r and g >= b:
        return BAG if r > 180 else POKEMON
    if r > 110 and r > g + 30:
        return MEGA
    return (40, 170, 200) if g > 180 else RUN


def readable_font(font, text, rect):
    """The largest of the redesign's fonts that fits the button (never smaller than it was)."""
    if not FONTS:
        return font
    for key in ("button", "label", "caption"):
        f = FONTS.get(key)
        if f and f.size(str(text))[0] <= rect.w - 24 and f.get_height() <= rect.h - 6:
            return f if f.get_height() >= font.get_height() else font
    return font

ACCENT["map"] = (28, 150, 104)
ACCENT["fun"] = (220, 60, 150)    # Game Corner, Amie, contests, Poffins
ACCENT["tool"] = (60, 84, 168)    # PokeNav, Unown report, Weather Dial


def text_on(color):
    """(text colour, outline colour) for a small label on a coloured tag: dark on light colours
    (yellow, gold), white on the rest."""
    light = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2] > 150
    return ((60, 40, 6), tuple(min(255, int(c * 1.15)) for c in color)) if light else ((255, 255, 255), shade(color, 0.5))


def draw_gender(surface, gender, x, y, size=18):
    """The male / female sign (drawn, so it shows in any font): blue circle and arrow, pink circle and
    cross. x, y is the top-left of a size x size box. Nothing for a genderless Pokemon."""
    if gender not in ("M", "F"):
        return 0
    color = (90, 170, 255) if gender == "M" else (255, 110, 150)
    w = max(2, size // 7)
    r = size * 3 // 10
    if gender == "M":
        cx, cy = x + r + w, y + size - r - w
        pygame.draw.circle(surface, color, (cx, cy), r, w)
        tip = (x + size - w, y + w)
        pygame.draw.line(surface, color, (cx + r * 7 // 10, cy - r * 7 // 10), tip, w)
        pygame.draw.line(surface, color, tip, (tip[0] - size // 3, tip[1]), w)
        pygame.draw.line(surface, color, tip, (tip[0], tip[1] + size // 3), w)
    else:
        cx, cy = x + size // 2, y + r + w
        pygame.draw.circle(surface, color, (cx, cy), r, w)
        pygame.draw.line(surface, color, (cx, cy + r), (cx, y + size - w), w)
        pygame.draw.line(surface, color, (cx - size // 4, y + size * 3 // 4), (cx + size // 4, y + size * 3 // 4), w)
    return size


def menu_tile(surface, rect, color, hover=False):
    """A big menu tile (the MENU grid): a charcoal tile, a colour band slanting across its foot and a
    colour corner (Solar Eclipse's pause menu colours); the tile under the pointer fills with its colour."""
    rect = pygame.Rect(rect)
    color = tuple(color)[:3]
    c = 14
    pts = chamfer(rect, c, tl=False)
    alpha_poly(surface, (0, 0, 0), chamfer(rect.move(5, 6), c, tl=False), 120)
    pygame.draw.polygon(surface, mix((40, 40, 48), color, 0.55) if hover else (40, 40, 48), pts)
    band = rect.h // 4
    pygame.draw.polygon(surface, color, [(rect.x + 2, rect.bottom - band - 10), (rect.right - 2, rect.bottom - band + 4),
                                         (rect.right - 2, rect.bottom - c - 1), (rect.right - c - 1, rect.bottom - 2),
                                         (rect.x + 2, rect.bottom - 2)])
    pygame.draw.polygon(surface, color, [(rect.x + 2, rect.y + 2), (rect.x + 30, rect.y + 2), (rect.x + 2, rect.y + 30)])
    pygame.draw.polygon(surface, (255, 255, 255) if hover else color, pts, 3 if hover else 2)
