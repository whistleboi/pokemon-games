"""The Name Rater (Jordan, 11-18: the only way to give a nickname; only Pokemon you caught). A town person whose event
has "name_rater": true says its lines, you pick a Pokemon, and type its new name: empty gives it back its species' name.
A Pokemon you got in a trade keeps the name its first owner gave it; an Egg has no name yet. The nickname is kept through
evolution (Pokemon.display_name) and saved (story._pokemon_record)."""
import pygame

from src.states.base import GameState
from src.ui import theme
from src.ui.panels import CommandButton
from src.utils import Utils

MAX_LEN = 12


def start(state, intro_lines, show):
    """From a town's event: its lines, then the party list; a pick opens the name box."""
    game = state.game
    from src.states.systems import PokemonPartyMenuState

    def chosen(idx):
        team = game.story_manager.player_team
        p = team[idx] if 0 <= idx < len(team) else None
        if p is None:
            return
        game.change_state(state)
        if getattr(p, "is_egg", False):
            return show(["Name Rater: An Egg? Let's wait until it hatches before we give it a name!"])
        if getattr(p, "traded", False):
            return show([f"Name Rater: {p.display_name.upper()}... a fine name its first Trainer gave it.",
                         "Name Rater: It came to you in a trade, so I'd better not change it. That's only polite!"])
        game.change_state(NameRaterState(game, state, p, show))

    def cancel():
        game.change_state(state)
        show(["Name Rater: Come back any time. A good name is worth the wait!"])

    def pick():
        menu = PokemonPartyMenuState(game, previous_state=state, context="rename", on_select=chosen, on_cancel=cancel)
        menu.message = "Rename which Pokemon?"
        game.change_state(menu)

    lines = intro_lines or ["Name Rater: Hello, hello! I'm the Name Rater. Shall I rate a Pokemon's nickname?"]
    if hasattr(state, "show_message"):
        state.show_message(lines, callback=pick)
    else:
        show(lines)
        pick()


class NameRaterState(GameState):
    """The name box: the Pokemon, what it's called now, the new name as you type; OK / CANCEL."""
    uses_keyboard = True

    def text_input_rect(self):   # (a phone's keyboard opens on a tap: src/core/android.py)
        return self.box

    def __init__(self, game, previous_state, pokemon, show):
        super().__init__(game)
        self.previous_state, self.pokemon, self.show = previous_state, pokemon, show
        self.text = pokemon.nickname or ""
        w, h = game.width, game.height
        self.box = pygame.Rect(w // 2 - 260, int(h * 0.52), 520, 70)
        fonts = game.assets.fonts
        self.btn_ok = CommandButton((w // 2 - 270, int(h * 0.70), 250, 70), "OK", fonts["button"], self.confirm,
                                    bg_color=theme.ACCENT["party"], autosize=False)
        self.btn_cancel = CommandButton((w // 2 + 20, int(h * 0.70), 250, 70), "CANCEL", fonts["button"], self.cancel,
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
                elif len(self.text) < MAX_LEN and event.unicode and event.unicode.isprintable():
                    self.text = (self.text + Utils.typable(self.game, event.unicode))[:MAX_LEN]

    def confirm(self):
        p = self.pokemon
        name = self.text.strip()
        old = p.display_name
        p.nickname = name if name and name.upper() != p.species_name.upper() else None
        self._close()
        if p.nickname:
            self.show([f"Name Rater: {p.nickname.upper()}! What a name! Far better than {old.upper()}, if you ask me.",
                       f"{p.species_name.upper()} is now called {p.nickname.upper()}."])
        else:
            self.show([f"Name Rater: Back to plain {p.species_name.upper()}? Classic. Nothing wrong with that!"])

    def cancel(self):
        self._close()
        self.show(["Name Rater: Hmm, keeping its name? That's fine too. It suits it!"])

    def _close(self):
        self.stop()
        self.game.change_state(self.previous_state)

    def update(self):
        pass

    def draw(self):
        screen, fonts = self.game.screen, self.game.assets.fonts
        theme.menu_background(screen, theme.ACCENT["party"], "NAME RATER", fonts["button"], title_x=24)
        w, h = self.game.width, self.game.height
        img = getattr(self.pokemon, "image", None)
        if img is not None:
            k = min(1.0, (h * 0.30) / max(1, img.get_height()))
            pic = pygame.transform.smoothscale(img, (int(img.get_width() * k), int(img.get_height() * k)))
            screen.blit(pic, pic.get_rect(midbottom=(w // 2, int(h * 0.44))))
        theme.shadow_text(screen, f"Now: {self.pokemon.display_name.upper()}  ({self.pokemon.species_name.upper()})", fonts["med"],
                          w // 2, int(h * 0.455), align="center")
        theme.draw_textbox(screen, self.box)
        shown = self.text + ("_" if (pygame.time.get_ticks() // 400) % 2 == 0 else " ")
        theme.shadow_text(screen, shown, fonts["button"], self.box.x + 20, self.box.y + 14)
        theme.shadow_text(screen, "Type a new name. Leave it empty for its species' name.", fonts["small"],
                          w // 2, self.box.bottom + 8, align="center")
        self.game.ui_manager.draw(screen)
