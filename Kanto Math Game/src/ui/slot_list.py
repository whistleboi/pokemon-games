"""Paged list of the save slots, shared by the Load, Save and New Game slot screens.

Touch: tap a row to pick it, tap PREV / NEXT (or swipe up/down) to change page.
Keyboard (desktop, optional): Up/Down, Page Up/Page Down, Home/End, Enter.
Only the rows on screen are summarised (see src.core.save_slots), so 100 slots stay cheap.
"""
import os
import pygame
from src.core import save_slots
from src.config import WHITE, GOLD, BLACK, LIGHT_GRAY, RED
from src.ui import theme

ROW_BG = (28, 36, 72)
ROW_EMPTY_BG = (22, 22, 30)
ROW_SEL_BG = (52, 72, 150)
ROW_BORDER = (110, 130, 200)
DIM = (150, 150, 165)
SWIPE_PX = 60

_fonts = {}


def slot_font(assets, size):
    """The GSC pixel font (rebuilt, with a proper accented e), crisp at multiples of 8 px."""
    if size not in _fonts:
        font = None
        for name in ("pokemon_gsc_rebuilt.ttf", "pokemon_gsc.ttf", "pokemon_gsc.ttf.ttf"):
            path = os.path.join(assets.assets_dir or "", name)
            if os.path.exists(path):
                try:
                    from src.ui.fonts import TightFont
                    font = TightFont(path, size)
                    break
                except (OSError, pygame.error):
                    pass
        _fonts[size] = font or pygame.font.Font(None, size + 8)
    return _fonts[size]


def fit(font, text, width):
    """Text cut with '...' so it fits in width pixels."""
    if font.size(text)[0] <= width:
        return text
    while text and font.size(text + "...")[0] > width:
        text = text[:-1]
    return text + "..."


class SlotList:
    """In the menu frame (src/ui/theme.py): the files as white cards under the header, PREV /
    NEXT and the page in the text box along the bottom."""
    PER_PAGE = 8

    def __init__(self, game, on_pick, top=None, bottom_bar=None, selected=0):
        from src.ui.panels import CommandButton
        self.game = game
        self.on_pick = on_pick
        self.count = save_slots.SAVE_SLOTS
        self.bar_rect = pygame.Rect(16, game.height - 86, game.width - 32, 78)
        top = theme.HEADER_H + 14 if top is None else top
        bottom_bar = self.bar_rect.top - 8 if bottom_bar is None else bottom_bar
        w = game.width - 48
        self.left = 24
        self.width = w
        self.top = top
        self.row_h = (bottom_bar - top) // self.PER_PAGE
        self.page_count = (self.count + self.PER_PAGE - 1) // self.PER_PAGE
        self.selected = max(0, min(self.count - 1, selected))
        self.page = self.selected // self.PER_PAGE
        self.used = save_slots.used_slots(save_slots.folder(game))
        self._down = None
        self.big = slot_font(game.assets, 24)
        self.small = slot_font(game.assets, 16)
        b, f = self.bar_rect, game.assets.fonts
        self.btn_prev = CommandButton((b.x + 16, b.y + 12, 170, b.h - 28), "< PREV", f["label"],
                                      lambda: self.goto_page(self.page - 1), bg_color=theme.RUN, autosize=False)
        self.btn_next = CommandButton((b.right - 16 - 170, b.y + 12, 170, b.h - 28), "NEXT >", f["label"],
                                      lambda: self.goto_page(self.page + 1), bg_color=theme.RUN, autosize=False)
        self._sync_buttons()

    # ---- state
    def refresh(self):
        self.used = save_slots.used_slots(save_slots.folder(self.game))

    def summary(self, i):
        if i not in self.used:
            return None  # empty: no file access at all
        return save_slots.summary(save_slots.folder(self.game), i)

    def buttons(self):
        return [self.btn_prev, self.btn_next]

    def goto_page(self, page):
        page = max(0, min(self.page_count - 1, page))
        if page != self.page:
            self.page = page
            self.selected = page * self.PER_PAGE
        self._sync_buttons()

    def select(self, i):
        self.selected = max(0, min(self.count - 1, i))
        self.page = self.selected // self.PER_PAGE
        self._sync_buttons()

    def _sync_buttons(self):
        for btn, on in ((self.btn_prev, self.page > 0), (self.btn_next, self.page < self.page_count - 1)):
            btn.bg_color = theme.RUN if on else theme.TAB_OFF

    def row_rect(self, k):
        return pygame.Rect(self.left, self.top + k * self.row_h, self.width, self.row_h - 6)

    def visible_slots(self):
        start = self.page * self.PER_PAGE
        return range(start, min(self.count, start + self.PER_PAGE))

    def slot_at(self, pos):
        for k, i in enumerate(self.visible_slots()):
            if self.row_rect(k).collidepoint(pos):
                return i
        return None

    # ---- input; returns True when the event was used
    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._down = event.pos
            return self.slot_at(event.pos) is not None
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self._down:
            start, self._down = self._down, None
            dy = event.pos[1] - start[1]
            if abs(dy) >= SWIPE_PX:  # swipe up = next page, swipe down = previous
                self.goto_page(self.page + (1 if dy < 0 else -1))
                return True
            i = self.slot_at(event.pos)
            if i is not None and i == self.slot_at(start):
                self.select(i)
                self.on_pick(i)
                return True
            return False
        if event.type == pygame.MOUSEWHEEL:
            self.goto_page(self.page - event.y)
            return True
        if event.type == pygame.KEYDOWN:
            k = event.key
            moves = {pygame.K_UP: -1, pygame.K_DOWN: 1,
                     pygame.K_PAGEUP: -self.PER_PAGE, pygame.K_PAGEDOWN: self.PER_PAGE,
                     pygame.K_LEFT: -self.PER_PAGE, pygame.K_RIGHT: self.PER_PAGE}
            if k in moves:
                self.select(self.selected + moves[k])
            elif k == pygame.K_HOME:
                self.select(0)
            elif k == pygame.K_END:
                self.select(self.count - 1)
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.on_pick(self.selected)
            else:
                return False
            return True
        return False

    # ---- drawing
    def draw(self, surface):
        """The files on show, then the bottom bar (its PREV / NEXT are the screen's buttons)."""
        mouse = pygame.mouse.get_pos()
        f = self.game.assets.fonts
        for k, i in enumerate(self.visible_slots()):
            r = self.row_rect(k)
            s = self.summary(i)
            sel = i == self.selected
            if s is None:  # an empty file: a dim slot
                pygame.draw.rect(surface, theme.shade(theme.PANEL_INNER, 0.85), r, border_radius=10)
                pygame.draw.rect(surface, theme.RUN if sel else theme.PANEL_EDGE, r, 3 if sel else 2, border_radius=10)
            else:
                theme.card(surface, r, hover=r.collidepoint(mouse), selected=sel, accent=theme.RUN, radius=10)
            chip = pygame.Rect(r.x + 10, r.y + 8, 112, r.h - 16)
            pygame.draw.rect(surface, theme.RUN if s else theme.TAB_OFF, chip, border_radius=8)
            num = f"No.{i + 1:03d}"
            from src.utils import Utils
            Utils.draw_text_outline(surface, num, f["label"], WHITE, chip.centerx, chip.centery,
                                    outline_color=theme.shade(theme.RUN if s else theme.TAB_OFF, 0.5), thickness=2)
            tx = chip.right + 18
            tw = r.right - 16 - tx
            if s is None:
                theme.shadow_text(surface, "- EMPTY -", f["label"], tx, r.centery - 11, color=(170, 178, 204),
                                  shadow=theme.MENU_BG)
                continue
            if s.get("damaged"):
                theme.shadow_text(surface, fit(f["label"], "DAMAGED FILE (can't be loaded)", tw), f["label"], tx,
                                  r.centery - 11, color=theme.HP_RED)
                continue
            name = s["name"] + ("  (from backup)" if s.get("restored") else "")
            badges = s.get("badges", 0)
            bits = [b for b in (s.get("region"), s.get("area"),
                                f"{badges} badge" + ("" if badges == 1 else "s")) if b]
            when = s.get("saved", "")
            ww = f["caption"].size(when)[0]
            theme.shadow_text(surface, fit(f["label"], name, tw - ww - 24), f["label"], tx, r.y + 7)
            theme.shadow_text(surface, fit(f["caption"], " - ".join(bits), tw), f["caption"], tx, r.bottom - 25,
                              color=(110, 116, 136))
            theme.shadow_text(surface, when, f["caption"], r.right - 16, r.y + 10, color=(110, 116, 136),
                              align="right")
        first = self.page * self.PER_PAGE + 1
        last = min(self.count, first + self.PER_PAGE - 1)
        theme.draw_textbox(surface, self.bar_rect)
        theme.shadow_text(surface, f"Page {self.page + 1}/{self.page_count}   No.{first:03d}-{last:03d}",
                          f["s_med"], self.bar_rect.centerx, self.bar_rect.centery - 2, align="center")
