# [REF-0001: System Imports]
import pygame
from src.ui.manager import UIElement
from src.utils import Utils
from src.config import WHITE, GOLD, BLACK


def wrap_text(text, font, max_width):
    """Split text into lines that fit max_width (long words get a line of their own)."""
    lines = []
    for para in str(text).split("\n"):
        line = ""
        for word in para.split(" "):
            test = f"{line} {word}" if line else word
            if line and font.size(test)[0] > max_width:
                lines.append(line)
                line = word
            else:
                line = test
        lines.append(line)
    return lines or [""]


# [REF-0047: Classic Dialogue Box with Typewriter Effect and Click-to-Advance]
class ClassicDialogueBox(UIElement):
    """Text box: one logical line at a time, typed out, click to advance.

    A long line is split into pages that fit the box (like the games' two-line text
    boxes), so text never spills out. `current_line` still counts logical lines, so
    code that waits for "line 2" keeps working. A finished box no longer swallows
    clicks; with auto_hide it also disappears when done."""

    def __init__(self, rect, text_lines, font, callback=None, visible=True, auto_hide=False):
        super().__init__(rect, callback, visible)
        self.font = font
        self.auto_hide = auto_hide
        self.speed = 3
        self._set_lines(text_lines)

    def _set_lines(self, text_lines):
        self.text_lines = text_lines if isinstance(text_lines, list) else [text_lines]
        self.current_line = 0
        self.page = 0
        self.visible_chars = 0
        self.is_waiting_for_click = False
        self.is_finished = False
        self.on_line_finish = {}
        self.line_finish_triggered = False
        self._page_cache = {}

    # ---- layout ----
    def _line_height(self):
        return int(self.font.get_linesize() * 1.15)

    def _pages(self, index):
        """Pages (lists of wrapped rows) for logical line `index`."""
        key = (index, self.rect.width, self.rect.height)
        if key not in self._page_cache:
            text = str(self.text_lines[index]) if index < len(self.text_lines) else ""
            rows = wrap_text(text, self.font, self.rect.width - 80)
            per_page = max(1, (self.rect.height - 44) // self._line_height())
            self._page_cache[key] = [rows[i:i + per_page] for i in range(0, len(rows), per_page)] or [[""]]
        return self._page_cache[key]

    def _page_rows(self):
        pages = self._pages(self.current_line)
        return pages[min(self.page, len(pages) - 1)]

    def _page_length(self):
        rows = self._page_rows()
        return sum(len(r) for r in rows) + max(0, len(rows) - 1)

    def _last_page(self):
        return self.page >= len(self._pages(self.current_line)) - 1

    def _line_done(self):
        """The current page is fully shown."""
        self.visible_chars = self._page_length()
        self.is_waiting_for_click = True
        if self._last_page() and not self.line_finish_triggered:
            self.line_finish_triggered = True
            if self.current_line in self.on_line_finish:
                self.on_line_finish[self.current_line]()

    # ---- behaviour ----
    def update(self):
        if self.is_finished or self.is_waiting_for_click:
            return
        if self.visible and self.page == 0 and self.current_line < len(self.text_lines):
            key = (id(self.text_lines), self.current_line, self.text_lines[self.current_line])
            if getattr(self, "_spoken", None) != key:  # character lines speak in their own voice
                self._spoken = key
                from src.core import speech
                if speech.available():
                    speech.say_line(self.text_lines[self.current_line], auto=True)
        if self.current_line < len(self.text_lines):
            self.visible_chars += self.speed
            if self.visible_chars >= self._page_length():
                self._line_done()

    def advance(self):
        """If typing, finish the page. If waiting, show the next page or line, or finish."""
        if self.is_finished:
            return

        if not self.is_waiting_for_click:
            if self.current_line < len(self.text_lines):
                self._line_done()
            return

        self.is_waiting_for_click = False
        self.visible_chars = 0
        if not self._last_page():
            self.page += 1
            return
        self.page = 0
        self.current_line += 1
        self.line_finish_triggered = False
        if self.current_line >= len(self.text_lines):
            self.is_finished = True
            if self.auto_hide:
                self.visible = False
            if self.callback:
                # One-shot: a callback belongs to the text it was set for, so it must not
                # fire again when the box is reused (that ended battle turns early).
                callback, self.callback = self.callback, None
                callback()

    def _speak_rect(self):
        return pygame.Rect(self.rect.x + 16, self.rect.bottom - 58, 44, 44)

    def handle_event(self, event):
        # A finished box lets clicks through, so buttons under it still work.
        if not self.visible or self.is_finished:
            return False
        from src.core import speech
        if (speech.available() and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self._speak_rect().collidepoint(event.pos)):
            if self.current_line < len(self.text_lines):
                speech.say_line(self.text_lines[self.current_line])
            return True
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        ):
            self.advance()
            return True
        return False

    def reset(self, new_text):
        self._set_lines([new_text] if isinstance(new_text, str) else new_text)
        self.visible = True

    def draw(self, surface):
        if not self.visible:
            return
        Utils.draw_classic_panel(
            surface, self.rect.x, self.rect.y, self.rect.width, self.rect.height
        )

        more = self.is_waiting_for_click and not (
            self._last_page() and self.current_line >= len(self.text_lines) - 1)
        waiting = self.is_waiting_for_click and not self.is_finished
        if self.current_line < len(self.text_lines):
            rows = self._page_rows()
            lh = self._line_height()
            top = self.rect.centery - (len(rows) * lh) // 2 - (10 if more else 0)
            left = self.visible_chars
            for i, row in enumerate(rows):
                shown = row[:max(0, left)]
                left -= len(row) + 1
                if shown:
                    Utils.draw_text_outline(surface, shown, self.font, WHITE,
                                            self.rect.centerx, top + lh * i + lh // 2)

        from src.core import speech
        if speech.available() and self.current_line < len(self.text_lines):
            speech.draw_speaker(surface, self._speak_rect())
        if waiting:
            # A bobbing arrow: "tap to go on".
            import math
            bob = int(3 * math.sin(pygame.time.get_ticks() / 150))
            x, y = self.rect.right - 40, self.rect.bottom - 34 + bob
            pts = [(x - 12, y - 8), (x + 12, y - 8), (x, y + 8)]
            pygame.draw.polygon(surface, BLACK, [(px, py + 2) for px, py in pts])
            pygame.draw.polygon(surface, WHITE if more else GOLD, pts)
            pygame.draw.polygon(surface, BLACK, pts, 2)
