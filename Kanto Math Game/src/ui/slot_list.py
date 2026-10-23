"""Paged list of the save slots, shared by the Load, Save and New Game slot screens.

Touch: tap a row to pick it, tap PREV / NEXT (or swipe up/down) to change page.
Keyboard (desktop, optional): Up/Down, Page Up/Page Down, Home/End, Enter.
Only the rows on screen are summarised (see src.core.save_slots), so 100 slots stay cheap.
"""
import os
import pygame
from src.core import save_slots
from src.ui.widgets import Button
from src.config import WHITE, GOLD, BLACK, LIGHT_GRAY, RED

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
                    font = pygame.font.Font(path, size)
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
    PER_PAGE = 8

    def __init__(self, game, on_pick, top=96, bottom_bar=616, selected=0):
        self.game = game
        self.on_pick = on_pick
        self.count = save_slots.SAVE_SLOTS
        w = min(1120, game.width - 80)
        self.left = (game.width - w) // 2
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
        by = bottom_bar + 16
        self.btn_prev = Button((self.left, by, 200, 60), "< PREV", game.assets.fonts["small"],
                               lambda: self.goto_page(self.page - 1), autosize=False)
        self.btn_next = Button((self.left + w - 200, by, 200, 60), "NEXT >", game.assets.fonts["small"],
                               lambda: self.goto_page(self.page + 1), autosize=False)
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
            btn.bg_color = (70, 100, 240) if on else (60, 60, 70)
            btn.text_color = WHITE if on else DIM

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
        for k, i in enumerate(self.visible_slots()):
            r = self.row_rect(k)
            s = self.summary(i)
            sel = i == self.selected
            bg = ROW_SEL_BG if sel else (ROW_BG if s else ROW_EMPTY_BG)
            pygame.draw.rect(surface, bg, r, border_radius=10)
            pygame.draw.rect(surface, GOLD if sel else ROW_BORDER, r, 3 if sel else 1, border_radius=10)
            num = self.big.render(f"No.{i + 1:03d}", False, GOLD)
            surface.blit(num, (r.x + 16, r.centery - num.get_height() // 2))
            tx = r.x + 16 + self.big.size("No.000")[0] + 28
            tw = r.right - 16 - tx
            if s is None:
                t = self.big.render("- EMPTY -", False, DIM)
                surface.blit(t, (tx, r.centery - t.get_height() // 2))
                continue
            if s.get("damaged"):
                t = self.big.render(fit(self.big, "DAMAGED FILE (can't be loaded)", tw), False, RED)
                surface.blit(t, (tx, r.centery - t.get_height() // 2))
                continue
            name = s["name"] + ("  (from backup)" if s.get("restored") else "")
            badges = s.get("badges", 0)
            bits = [b for b in (s.get("region"), s.get("area"),
                                f"{badges} badge" + ("" if badges == 1 else "s")) if b]
            when = self.small.render(s.get("saved", ""), False, LIGHT_GRAY)
            line1 = self.big.render(fit(self.big, name, tw - when.get_width() - 24), False, WHITE)
            line2 = self.small.render(fit(self.small, " - ".join(bits), tw), False, LIGHT_GRAY)
            gap = 6
            y = r.centery - (line1.get_height() + gap + line2.get_height()) // 2
            surface.blit(line1, (tx, y))
            surface.blit(when, (r.right - 16 - when.get_width(), y + line1.get_height() - when.get_height()))
            surface.blit(line2, (tx, y + line1.get_height() + gap))
        first = self.page * self.PER_PAGE + 1
        last = min(self.count, first + self.PER_PAGE - 1)
        label = self.small.render(f"PAGE {self.page + 1}/{self.page_count}   No.{first:03d}-{last:03d}",
                                  False, WHITE)
        surface.blit(label, label.get_rect(midright=(self.left + self.width, self.top - 22)))
