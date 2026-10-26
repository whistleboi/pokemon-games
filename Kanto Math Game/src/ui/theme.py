# [REF-0086: UI theme]
"""One look for every screen (Jordan: the battle screen redesign, in line with the games, carried
across the game so menus line up):

- panels: deep slate blue with a light top edge (white text with a dark outline reads on them,
  as it did on the old gold panels);
- text boxes: the games' white box with a blue double frame and dark text with a soft shadow;
- command colours: FIGHT red, BAG yellow, POKEMON green, RUN blue (Gen 6/7 style);
- battle info boxes: light cream with a dark frame, dark text.

draw_panel / draw_textbox / shadow_text are what Utils.draw_classic_panel, ClassicDialogueBox and
the battle screen use."""
import pygame

PANEL = (42, 54, 88)
PANEL_INNER = (52, 66, 106)
PANEL_EDGE = (124, 152, 214)
PANEL_BORDER = (16, 20, 36)
SHADOW = (0, 0, 0, 90)

TEXTBOX = (250, 250, 250)
TEXTBOX_FRAME = (56, 72, 120)
TEXTBOX_ACCENT = (128, 172, 224)
TEXT = (60, 60, 70)
TEXT_SHADOW = (206, 206, 214)
TEXT_ARROW = (216, 64, 64)

INFOBOX = (248, 248, 236)
INFOBOX_FRAME = (48, 56, 74)
INFOBOX_ACCENT = (220, 220, 200)

FIGHT = (226, 84, 56)
BAG = (236, 178, 44)
POKEMON = (82, 178, 86)
RUN = (66, 130, 220)
MEGA = (150, 70, 210)

HP_GREEN, HP_YELLOW, HP_RED = (88, 208, 96), (240, 200, 40), (232, 72, 64)
EXP_BLUE = (64, 168, 240)


def _shadow(surface, rect, radius):
    sh = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.rect(sh, SHADOW, sh.get_rect(), border_radius=radius)
    surface.blit(sh, rect.move(6, 6))


def draw_panel(surface, rect, radius=14):
    """The menu panel: slate blue, a lighter inset, a light top edge and a dark frame."""
    rect = pygame.Rect(rect)
    _shadow(surface, rect, radius)
    pygame.draw.rect(surface, PANEL, rect, border_radius=radius)
    inner = rect.inflate(-10, -10)
    pygame.draw.rect(surface, PANEL_INNER, inner, border_radius=max(4, radius - 4))
    pygame.draw.line(surface, PANEL_EDGE, (rect.x + radius, rect.y + 5), (rect.right - radius, rect.y + 5), 3)
    pygame.draw.rect(surface, PANEL_BORDER, rect, 4, border_radius=radius)


def draw_textbox(surface, rect, radius=14):
    """The games' text box: white, a blue double frame."""
    rect = pygame.Rect(rect)
    _shadow(surface, rect, radius)
    pygame.draw.rect(surface, TEXTBOX_FRAME, rect, border_radius=radius)
    mid = rect.inflate(-8, -8)
    pygame.draw.rect(surface, TEXTBOX_ACCENT, mid, border_radius=max(4, radius - 3))
    inner = rect.inflate(-16, -16)
    pygame.draw.rect(surface, TEXTBOX, inner, border_radius=max(4, radius - 6))


def shadow_text(surface, text, font, x, y, color=TEXT, shadow=TEXT_SHADOW, align="left"):
    """Dark text with the games' soft drop shadow. y is the text's top (centre if align=center)."""
    surf = font.render(str(text), False, color)
    sh = font.render(str(text), False, shadow)
    w, h = surf.get_size()
    if align == "center":
        x, y = x - w // 2, y - h // 2
    elif align == "right":
        x -= w
    d = max(1, font.get_height() // 14)
    surface.blit(sh, (x + d, y + d))
    surface.blit(sh, (x + d, y))
    surface.blit(sh, (x, y + d))
    surface.blit(surf, (x, y))
    return pygame.Rect(x, y, w, h)


def command_button(surface, rect, label, font, color, hover=False, small=None, sub=None):
    """A battle command (FIGHT / BAG / POKEMON / RUN): a rounded colour block with a darker lip."""
    rect = pygame.Rect(rect)
    lip = rect.move(0, 5)
    dark = tuple(max(0, int(c * 0.6)) for c in color)
    light = tuple(min(255, int(c * 1.18)) for c in color)
    pygame.draw.rect(surface, dark, lip, border_radius=16)
    pygame.draw.rect(surface, light if hover else color, rect, border_radius=16)
    gloss = pygame.Rect(rect.x + 10, rect.y + 6, rect.w - 20, max(6, rect.h // 4))
    g = pygame.Surface(gloss.size, pygame.SRCALPHA)
    pygame.draw.rect(g, (255, 255, 255, 60), g.get_rect(), border_radius=gloss.h // 2)
    surface.blit(g, gloss)
    pygame.draw.rect(surface, (255, 255, 255) if hover else (20, 20, 30), rect, 3, border_radius=16)
    from src.utils import Utils
    cy = rect.centery - (8 if sub and small else 0)
    Utils.draw_text_outline(surface, label, font, (255, 255, 255), rect.centerx, cy, outline_color=dark, thickness=3)
    if sub and small:
        Utils.draw_text_outline(surface, sub, small, (255, 255, 255), rect.centerx, rect.bottom - 18,
                                outline_color=dark, thickness=2)


# ---------------------------------------------------------------- menus (Pokedex, PC, Journal, Bag)
# The menu redesign (Jordan: "like the battle screen"): one frame for every menu screen. A slate
# background with faint stripes, a coloured header band (each menu has its own colour) with BACK
# and the title, white cards with dark text for entries, the battle menu's buttons, and the
# battle text box at the bottom for details.
MENU_BG = (30, 36, 58)
MENU_STRIPE = (35, 42, 67)
HEADER_H = 84
BACK = (120, 124, 144)       # BACK buttons everywhere
TAB_OFF = (88, 98, 132)      # a tab or toggle that is off
ACCENT = {"dex": (214, 62, 58), "pc": (36, 146, 160), "journal": (204, 146, 36), "bag": (226, 118, 44),
          "party": (58, 150, 88), "mart": (52, 112, 196), "options": (110, 92, 168), "summary": (70, 90, 150)}
STATUS_TAGS = {"burn": ("BRN", (232, 120, 48)), "paralysis": ("PAR", (216, 176, 32)),
               "poison": ("PSN", (152, 64, 160)), "toxic": ("TOX", (112, 40, 112)),
               "sleep": ("SLP", (128, 128, 136)), "freeze": ("FRZ", (96, 176, 216)),
               "faint": ("FNT", (214, 64, 58))}

_bg_cache = {}


def shade(color, k):
    return tuple(max(0, min(255, int(c * k))) for c in color)


def menu_background(surface, accent, title=None, font=None, title_x=180):
    """Fill the screen with the menu frame: background, header band in `accent`, the title."""
    w, h = surface.get_size()
    key = (w, h, tuple(accent))
    bg = _bg_cache.get(key)
    if bg is None:
        bg = pygame.Surface((w, h))
        bg.fill(MENU_BG)
        for i in range(-h, w, 44):
            pygame.draw.line(bg, MENU_STRIPE, (i, h), (i + h, 0), 12)
        pygame.draw.rect(bg, accent, (0, 0, w, HEADER_H))
        pygame.draw.rect(bg, shade(accent, 0.62), (0, HEADER_H - 8, w, 8))
        pygame.draw.line(bg, shade(accent, 1.25), (0, 3), (w, 3), 2)
        sh = pygame.Surface((w, 14), pygame.SRCALPHA)
        for yy in range(14):
            pygame.draw.line(sh, (0, 0, 0, int(80 * (1 - yy / 14))), (0, yy), (w, yy))
        bg.blit(sh, (0, HEADER_H))
        _bg_cache[key] = bg
    surface.blit(bg, (0, 0))
    if title and font:
        from src.utils import Utils
        Utils.draw_text_outline(surface, title, font, (255, 255, 255), title_x, HEADER_H // 2 - 4,
                                align="left", outline_color=shade(accent, 0.45), thickness=3)


def card(surface, rect, hover=False, selected=False, accent=None, fill=TEXTBOX, radius=12):
    """A white entry card (Pokedex entry, Box slot, mission, Bag item) with the text box's frame."""
    rect = pygame.Rect(rect)
    frame = (accent or TEXTBOX_FRAME) if (hover or selected) else TEXTBOX_FRAME
    pygame.draw.rect(surface, shade(frame, 0.7), rect.move(0, 4), border_radius=radius)
    pygame.draw.rect(surface, (236, 244, 255) if hover and fill == TEXTBOX else fill, rect, border_radius=radius)
    pygame.draw.rect(surface, frame, rect, 5 if selected else 3, border_radius=radius)


def info_bar(surface, rect, lines, font, color=TEXT):
    """The battle text box with up to a few lines of details (hovered entry, hints)."""
    draw_textbox(surface, rect)
    lh = int(font.get_linesize() * 1.2)
    top = rect.centery - lh * len(lines) // 2
    for k, line in enumerate(lines):
        shadow_text(surface, line, font, rect.x + 32, top + k * lh, color=color)


def status_tag(surface, status, font, x, y):
    """The battle screen's status tag (BRN, PSN...). Returns its width (0 if healthy)."""
    tag = STATUS_TAGS.get(status or "")
    if not tag:
        return 0
    from src.utils import Utils
    text, color = tag
    rect = pygame.Rect(x, y, font.size(text)[0] + 16, font.get_height() + 6)
    pygame.draw.rect(surface, color, rect, border_radius=7)
    pygame.draw.rect(surface, INFOBOX_FRAME, rect, 2, border_radius=7)
    Utils.draw_text_outline(surface, text, font, (255, 255, 255), rect.centerx, rect.centery, outline_color=color,
                            thickness=1)
    return rect.w


def hp_bar(surface, x, y, w, hp, max_hp, font=None):
    """A small HP bar in the battle colours, the numbers after it when a font is given."""
    ratio = max(0.0, min(1.0, hp / max_hp)) if max_hp else 0.0
    bar = pygame.Rect(x, y, w, 10)
    pygame.draw.rect(surface, (88, 88, 96), bar, border_radius=5)
    color = HP_GREEN if ratio > 0.5 else HP_YELLOW if ratio > 0.2 else HP_RED
    if ratio > 0:
        pygame.draw.rect(surface, color, (bar.x, bar.y, max(3, int(bar.w * ratio)), bar.h), border_radius=5)
    if font:
        shadow_text(surface, f"{int(hp)}/{int(max_hp)}", font, bar.right, bar.bottom + 4, align="right")
    return bar


def popup_panel(surface, rect, title=None, font=None):
    """A small pop-up menu (tap a Pokemon: SUMMARY, MOVE...): the slate panel, its title on top."""
    rect = pygame.Rect(rect)
    draw_panel(surface, rect, radius=12)
    if title and font:
        from src.utils import Utils
        Utils.draw_text_outline(surface, title, font, (255, 255, 255), rect.centerx, rect.y + 24,
                                outline_color=PANEL_BORDER, thickness=2)


def pokemon_word(text):
    """The area data's short "PKMN" written out (Jordan): POKéMON in capitals ("CATCH WILD
    POKéMON"), Pokémon in ordinary text."""
    text = str(text)
    if "PKMN" not in text:
        return text
    letters = [c for c in text.replace("PKMN", "") if c.isalpha()]
    shouting = letters and sum(c.isupper() for c in letters) > len(letters) * 0.7
    return text.replace("PKMN", "POKéMON" if shouting else "Pokémon")


def text_field(surface, rect, text, font, placeholder="", focused=True):
    """A name box: white, the text box's frame, the typed name with a blinking cursor (or the
    placeholder, the name used if nothing is typed, in a lighter colour)."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, TEXTBOX, rect, border_radius=10)
    pygame.draw.rect(surface, TEXTBOX_FRAME, rect, 4, border_radius=10)
    y = rect.centery - font.get_height() // 2
    if text:
        r = shadow_text(surface, text, font, rect.x + 18, y)
        if focused and (pygame.time.get_ticks() // 500) % 2:
            pygame.draw.rect(surface, TEXT, (r.right + 4, y + 2, 4, font.get_height() - 6))
    else:
        r = shadow_text(surface, placeholder, font, rect.x + 18, y, color=(150, 156, 176))
        if focused and (pygame.time.get_ticks() // 500) % 2:
            pygame.draw.rect(surface, TEXT, (rect.x + 14, y + 2, 3, font.get_height() - 6))
