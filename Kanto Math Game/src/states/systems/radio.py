"""The RADIO screen (the Pokegear's radio, HGSS; Jordan 11-15): the channels you can hear here; tap one to tune in
(src/world/radio.py). The station stays on (the March, the Lullaby, Hoenn / Sinnoh Sound) till you change it."""
import pygame

from src.states.base import GameState
from src.ui import theme
from src.ui.panels import CommandButton
from src.ui.dialogue import ClassicDialogueBox
from src.utils import Utils
from src.config import WHITE

ACCENT = (40, 120, 170)


class RadioState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        from src.world import radio
        self.previous_state = previous_state
        f = game.assets.fonts
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.go_back, bg_color=theme.BACK, autosize=False)
        self.rows = []
        top = theme.HEADER_H + 24
        for i, (key, name) in enumerate(radio.channels(game)):
            col, row = i % 2, i // 2
            r = (40 + col * (game.width - 80) // 2, top + row * 84, (game.width - 80) // 2 - 16, 72)
            self.rows.append(CommandButton(r, name, f["button"], (lambda k=key: self.tune(k)), bg_color=theme.TAB_OFF, autosize=False))
        self.box = None

    def tune(self, key):
        from src.world import radio
        self.box = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), radio.tune(self.game, key), self.game.assets.fonts["med"],
                                      callback=self._done)

    def _done(self):
        self.box = None

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState) or hasattr(self.previous_state, "is_resuming"):
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
        from src.world import radio
        screen = self.game.screen
        f = self.game.assets.fonts
        theme.menu_background(screen, ACCENT, "RADIO", f["button"], title_x=176)
        st = self.game.story_manager.story_flags.get("radio_station")
        on = {"march": "Pokemon March: more wild Pokemon", "lullaby": "Pokemon Lullaby: fewer wild Pokemon",
              "hoenn": "Hoenn Sound playing", "sinnoh": "Sinnoh Sound playing"}.get(st, "")
        if on:
            Utils.draw_text_outline(screen, on, f["med"], WHITE, self.game.width // 2, self.game.height - 40, outline_color=theme.shade(ACCENT, 0.45))
        if self.box is not None:
            self.box.draw(screen)
