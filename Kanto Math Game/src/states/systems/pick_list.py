"""Pick one from a short list (Jordan 11-15: Goldenrod Dept. Store's elevator attendant - "which floor?").
PickListState(game, back, title, [(label, value), ...], done): done(value) runs after back is put back; BACK gives done(None)."""
import pygame

from src.states.base import GameState
from src.ui import theme
from src.ui.panels import CommandButton

ACCENT = (70, 110, 160)


class PickListState(GameState):
    def __init__(self, game, back, title, choices, done):
        super().__init__(game)
        self.back, self.title, self.done = back, title, done
        f = game.assets.fonts
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], lambda: self.pick(None), bg_color=theme.BACK, autosize=False)
        self.rows = []
        top = theme.HEADER_H + 24
        for i, (label, value) in enumerate(choices):
            col, row = i % 2, i // 2
            r = (40 + col * (game.width - 80) // 2, top + row * 84, (game.width - 80) // 2 - 16, 72)
            self.rows.append(CommandButton(r, label, f["button"], (lambda v=value: self.pick(v)), bg_color=theme.TAB_OFF, autosize=False))

    def pick(self, value):
        if hasattr(self.back, "is_resuming"):
            self.back.is_resuming = True
        self.game.change_state(self.back)
        if self.done:
            self.done(value)

    def start(self):
        self.game.ui_manager.add_element(self.btn_back)
        for b in self.rows:
            self.game.ui_manager.add_element(b)

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.pick(None)

    def update(self):
        pass

    def draw(self):
        theme.menu_background(self.game.screen, ACCENT, self.title, self.game.assets.fonts["button"], title_x=176)
