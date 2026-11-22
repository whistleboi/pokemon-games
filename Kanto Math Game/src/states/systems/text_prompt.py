"""A short text prompt (11-21, Join Avenue's phrases): a title, a question, a box you type in (up to max_len letters);
OK / CANCEL. done(text) gets what was typed, or None. Built like the Name Rater's box (name_rater.py)."""
import pygame

from src.states.base import GameState
from src.ui import theme
from src.ui.panels import CommandButton
from src.utils import Utils


class TextPromptState(GameState):
    uses_keyboard = True

    def text_input_rect(self):   # (a phone's keyboard opens on a tap: src/core/android.py)
        return self.box

    def __init__(self, game, previous_state, title, question, done, max_len=8, start_text=""):
        super().__init__(game)
        self.previous_state, self.title, self.question, self.done, self.max_len = previous_state, title, question, done, max_len
        self.text = start_text[:max_len]
        w, h = game.width, game.height
        self.box = pygame.Rect(w // 2 - 260, int(h * 0.48), 520, 70)
        fonts = game.assets.fonts
        self.btn_ok = CommandButton((w // 2 - 270, int(h * 0.68), 250, 70), "OK", fonts["button"], self.confirm,
                                    bg_color=theme.ACCENT["party"], autosize=False)
        self.btn_cancel = CommandButton((w // 2 + 20, int(h * 0.68), 250, 70), "CANCEL", fonts["button"], self.cancel,
                                        bg_color=theme.BACK, autosize=False)

    def start(self):
        for b in (self.btn_ok, self.btn_cancel):
            self.game.ui_manager.add_element(b)

    def stop(self):
        for b in (self.btn_ok, self.btn_cancel):
            if b in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(b)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.key == pygame.K_RETURN:
                    self.confirm()
                elif event.key == pygame.K_ESCAPE:
                    self.cancel()
                elif len(self.text) < self.max_len and event.unicode and event.unicode.isprintable():
                    self.text = (self.text + Utils.typable(self.game, event.unicode))[:self.max_len]

    def confirm(self):
        text = self.text.strip()
        self._close()
        self.done(text or None)

    def cancel(self):
        self._close()
        self.done(None)

    def _close(self):
        self.stop()
        self.game.change_state(self.previous_state)

    def update(self):
        pass

    def draw(self):
        screen, fonts = self.game.screen, self.game.assets.fonts
        theme.menu_background(screen, theme.ACCENT["party"], self.title, fonts["button"], title_x=24)
        w, h = self.game.width, self.game.height
        theme.shadow_text(screen, self.question, fonts["med"], w // 2, int(h * 0.38), align="center")
        theme.draw_textbox(screen, self.box)
        shown = self.text + ("_" if (pygame.time.get_ticks() // 400) % 2 == 0 else " ")
        theme.shadow_text(screen, shown, fonts["button"], self.box.x + 20, self.box.y + 14)
        theme.shadow_text(screen, f"Up to {self.max_len} letters.", fonts["small"], w // 2, self.box.bottom + 8, align="center")
        self.game.ui_manager.draw(screen)
