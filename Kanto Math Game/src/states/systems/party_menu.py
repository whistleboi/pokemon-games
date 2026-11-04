"""The party screen (choose a Pokemon, for items, moves and switching)."""

import pygame
from src.states.base import GameState
from src.ui.panels import PartySlotUI, CommandButton
from src.ui import theme
from src.ui.dialogue import ClassicDialogueBox
from src.utils import Utils
from src.config import WHITE
from src.states.systems.summary import PokemonDetailState


# [REF-0020: Party Menu System]
class PokemonPartyMenuState(GameState):

    def __init__(self, game, previous_state, context="normal", on_select=None, on_cancel=None):
        super().__init__(game)
        self.previous_state = previous_state
        self.context = context
        self.on_select = on_select
        self.on_cancel = on_cancel
        if context == "forced_switch":
            self.message = "Choose a new Pokémon!"
        elif context == "battle_switch":
            self.message = "Send out which Pokémon?"
        else:
            self.message = "Choose a Pokémon."
        self.slots = []
        self.popup_active = False
        self.selected_slot_index = -1
        self.popup_buttons = []
        self.move_swap_index = None
        self.bottom_rect = Utils.get_full_dialogue_rect(game)
        self.dialogue_box = ClassicDialogueBox(self.bottom_rect, "", self.game.assets.fonts["med"], visible=False)

    def start(self):
        self.game.ui_manager.elements.clear()
        self.slots = []

        # The menu frame: a 2 x 3 grid of cards under the header, the text box at the bottom.
        gap = 14
        start_y = theme.HEADER_H + 16
        slot_w = (self.game.width - 48 - gap) // 2
        slot_h = (self.bottom_rect.top - 12 - start_y - 2 * gap) // 3
        team = getattr(self.game.story_manager, "player_team", [])[:6]

        for i in range(6):
            row = i // 2
            col = i % 2
            x = 24 + col * (slot_w + gap)
            y = start_y + row * (slot_h + gap)
            slot_rect = pygame.Rect(x, y, slot_w, slot_h)
            pokemon = team[i] if i < len(team) else None

            slot = PartySlotUI(slot_rect, pokemon, i, self._slot_clicked, self.game)
            self.slots.append(slot)
            self.game.ui_manager.add_element(slot)

        self.game.ui_manager.add_element(self.dialogue_box)

        f = self.game.assets.fonts
        if self.context != "forced_switch":
            w = 200
            self.cancel_btn = CommandButton((self.bottom_rect.right - w - 28, self.bottom_rect.centery - 36, w, 68),
                                            "CANCEL", f["button"], self._cancel, bg_color=theme.BACK, autosize=False)
            self.game.ui_manager.add_element(self.cancel_btn)

        # Tap a Pokemon: a small menu beside it (SUMMARY, MOVE / SWITCH). Tapping anywhere else
        # closes it; tapping another Pokemon opens it there.
        self.popup_rect = pygame.Rect(0, 0, 220, 176)
        self.btn_summary = CommandButton((0, 0, 196, 54), "SUMMARY", f["label"], self._show_summary,
                                         bg_color=theme.RUN, visible=False, autosize=False)
        self.btn_switch = CommandButton((0, 0, 196, 54), "MOVE" if self.context == "normal" else "SWITCH",
                                        f["label"], self._confirm_switch, bg_color=theme.POKEMON, visible=False,
                                        autosize=False)

        self.popup_buttons = [self.btn_switch, self.btn_summary]
        for btn in self.popup_buttons:
            self.game.ui_manager.add_element(btn)

    def _slot_clicked(self, index):
        team = getattr(self.game.story_manager, "player_team", [])
        if index >= len(team):
            return
        if self.popup_active:  # the same Pokemon closes the menu, another moves it there
            same = index == self.selected_slot_index
            self._hide_popup()
            if not same:
                self._open_popup(index)
            return

        if self.move_swap_index is not None:
            if index != self.move_swap_index:
                team[self.move_swap_index], team[index] = team[index], team[self.move_swap_index]
                self.start()
                self.dialogue_box.reset("Moved Pokémon position!")
                self.dialogue_box.callback = self._dismiss_dialogue
                self.dialogue_box.visible = True
            else:
                pass

            self.move_swap_index = None
            self.message = "Choose a Pokémon."
            return

        if self.context == "use_item":
            team = getattr(self.game.story_manager, "player_team", [])
            if index < len(team) and getattr(team[index], "is_egg", False) and hasattr(self.previous_state, "item_works"):
                self.message = "That's an Egg! It can't use items."
                return
            if self.on_select:
                self.on_select(index)
            return

        self.selected_slot_index = index

        if self.context in ["battle_switch", "normal"]:
            self._open_popup(index)
        elif self.on_select:
            self.on_select(index)
        else:
            pkmn = team[index]
            self.game.show_dialogue([f"Selected {pkmn.display_name.upper()}!"], self._return)

    def _open_popup(self, index):
        """The small menu beside slot `index`, kept on the screen."""
        self.popup_active = True
        self.selected_slot_index = index
        for slot in self.slots:
            slot.selected = slot.index == index
        slot = self.slots[index].rect
        pr = self.popup_rect
        pr.y = min(max(theme.HEADER_H + 8, slot.centery - pr.h // 2), self.bottom_rect.top - 8 - pr.h)
        pr.x = slot.right - pr.w - 12 if index % 2 == 0 else slot.left + 12
        self.btn_summary.rect.topleft = (pr.x + 12, pr.y + 50)
        self.btn_switch.rect.topleft = (pr.x + 12, pr.y + 112)
        self.btn_switch.set_visibility(True)
        self.btn_summary.set_visibility(True)

    def _confirm_switch(self):
        idx = self.selected_slot_index
        team = getattr(self.game.story_manager, "player_team", [])

        if self.context == "battle_switch":
            if idx < len(team) and team[idx].current_hp <= 0:
                self._hide_popup()
                msg = f"{team[idx].display_name.upper()} has no energy left!"
                self.dialogue_box.reset([msg])
                self.dialogue_box.callback = self._dismiss_dialogue
                self.dialogue_box.visible = True
                return

            if idx < len(team) and team[idx] is self.previous_state.player_pokemon:
                self._hide_popup()
                self.dialogue_box.reset([f"{team[idx].display_name.upper()} is already in battle!"])
                self.dialogue_box.callback = self._dismiss_dialogue
                self.dialogue_box.visible = True
                return

        self._hide_popup()
        if self.context == "normal":
            self.move_swap_index = idx
            self.message = "Move to where?"
        else:
            if self.on_select and idx != -1:
                self.on_select(idx)

    def _show_summary(self):
        team = getattr(self.game.story_manager, "player_team", [])
        if self.selected_slot_index < len(team):
            pkmn = team[self.selected_slot_index]
            self.game.change_state(PokemonDetailState(self.game, pkmn, self, roster=list(self.game.story_manager.player_team)))
        self._hide_popup()

    def _hide_popup(self):
        self.popup_active = False
        self.selected_slot_index = -1
        for slot in self.slots:
            slot.selected = False
        self.btn_switch.set_visibility(False)
        self.btn_summary.set_visibility(False)

    def _cancel(self):
        if self.popup_active:
            self._hide_popup()
        elif self.move_swap_index is not None:
            self.move_swap_index = None
            self.message = "Choose a Pokémon."
            self._hide_popup()
        else:
            if self.on_cancel:
                self.on_cancel()
            self._return()

    def _dismiss_dialogue(self):
        self.dialogue_box.visible = False

    def _draw_use_tag(self, screen, rect, ok, text=None):
        """A green ABLE or grey NO EFFECT tag at the card's right, under its level."""
        f = self.game.assets.fonts["caption"]
        text = text or ("ABLE" if ok else "NO EFFECT")
        color = theme.POKEMON if ok else (132, 136, 150)
        tag = pygame.Rect(0, 0, f.size(text)[0] + 24, f.get_height() + 10)
        tag.topright = (rect.right - 14, rect.y + 48)
        pygame.draw.rect(screen, theme.shade(color, 0.6), tag.move(0, 3), border_radius=9)
        pygame.draw.rect(screen, color, tag, border_radius=9)
        pygame.draw.rect(screen, theme.shade(color, 0.55), tag, 2, border_radius=9)
        Utils.draw_text_outline(screen, text, f, WHITE, tag.centerx, tag.centery,
                                outline_color=theme.shade(color, 0.5), thickness=2)

    def _return(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def handle_events(self, events):
        # Taps on the cards and buttons are theirs (the UI takes them first); any other tap
        # closes the menu.
        if self.popup_active and any(e.type == pygame.MOUSEBUTTONDOWN for e in events):
            self._hide_popup()

    def update(self):
        if self.dialogue_box.visible:
            self.dialogue_box.update()

    def draw(self):
        """The menu frame (src/ui/theme.py) in green: six cards, the message in the text box."""
        screen = self.game.screen
        f = self.game.assets.fonts
        theme.menu_background(screen, theme.ACCENT["party"], "POKéMON", f["button"], title_x=24)
        if not self.dialogue_box.visible:
            theme.draw_textbox(screen, self.bottom_rect)
            theme.shadow_text(screen, self.message, f["dialog"], self.bottom_rect.x + 40,
                              self.bottom_rect.centery - f["dialog"].get_height() // 2)

        if self.move_swap_index is not None and self.move_swap_index < len(self.slots):
            for slot in self.slots:
                slot.selected = slot.index == self.move_swap_index

        self.game.ui_manager.draw(screen)
        bag = self.previous_state
        if self.context == "use_item" and hasattr(bag, "item_works") and not getattr(bag, "party_tag", None):  # ABLE / NO EFFECT on each card
            for slot in self.slots:
                if slot.pokemon is not None:
                    ok = bag.item_works(getattr(bag, "selected_item", None), slot.pokemon)
                    self._draw_use_tag(screen, slot.rect, ok)
        elif hasattr(bag, "party_tag"):  # the Day Care: COMPATIBLE / NOT COMPATIBLE
            for slot in self.slots:
                tag = bag.party_tag(slot.pokemon) if slot.pokemon is not None else None
                if tag:
                    self._draw_use_tag(screen, slot.rect, tag[1], tag[0])
        if self.popup_active:  # the menu over the cards, then its buttons on top
            team = getattr(self.game.story_manager, "player_team", [])
            name = team[self.selected_slot_index].display_name.upper() if 0 <= self.selected_slot_index < len(team) else ""
            theme.popup_panel(screen, self.popup_rect, name, f["label"])
            self.btn_summary.draw(screen)
            self.btn_switch.draw(screen)
