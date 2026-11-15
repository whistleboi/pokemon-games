"""The PHONE screen (the Pokegear's phone, HGSS; Jordan 11-15): everyone who gave you their number. Tap a name to call them:
they tell you whether a rematch is ready and where to find them (src/world/phone.py)."""
import pygame

from src.states.base import GameState
from src.ui import theme
from src.ui.panels import CommandButton
from src.ui.dialogue import ClassicDialogueBox
from src.utils import Utils
from src.config import WHITE

ACCENT = (52, 84, 170)


class PhoneState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        from src.world import phone
        self.previous_state = previous_state
        self.book = phone.book(game)
        f = game.assets.fonts
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.go_back, bg_color=theme.BACK, autosize=False)
        self.rows = []
        top = theme.HEADER_H + 24
        for i, (name, where, line) in enumerate(self.book[:12]):
            col, row = i % 2, i // 2
            r = (40 + col * (game.width - 80) // 2, top + row * 84, (game.width - 80) // 2 - 16, 72)
            self.rows.append(CommandButton(r, f"{name}  -  {where}", f["med"], (lambda ln=line: self.call(ln)), bg_color=theme.TAB_OFF, autosize=False))
        self.box = None

    def call(self, line):
        self.box = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), ["Calling...", line], self.game.assets.fonts["med"],
                                      callback=self._hang_up)

    def _hang_up(self):
        self.box = None

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.add_element(self.btn_back)
        for b in self.rows:
            self.game.ui_manager.add_element(b)

    def handle_events(self, events):
        if self.box is None:
            return
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN or (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z)):
                self.box.advance()

    def update(self):
        if self.box is not None:
            self.box.update()

    def draw(self):
        screen = self.game.screen
        f = self.game.assets.fonts
        theme.menu_background(screen, ACCENT, "PHONE", f["button"], title_x=176)
        if not self.book:
            Utils.draw_text_outline(screen, "Nobody has given you their number yet.", f["med"], WHITE, self.game.width // 2,
                                    self.game.height // 2, outline_color=theme.shade(ACCENT, 0.45))
            Utils.draw_text_outline(screen, "Beat a trainer while you carry your Pokegear, and they may ask for yours!", f["small"] if "small" in f else f["med"],
                                    WHITE, self.game.width // 2, self.game.height // 2 + 44, outline_color=theme.shade(ACCENT, 0.45))
        if self.box is not None:
            self.box.draw(screen)
