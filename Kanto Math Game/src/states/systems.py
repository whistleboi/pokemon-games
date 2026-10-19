# [REF-0001: System Imports]
import pygame
import os
import sys
from src.states.base import GameState
from src.ui.widgets import Button
from src.ui.panels import PartySlotUI
from src.ui.dialogue import ClassicDialogueBox
from src.utils import Utils
from src.config import WHITE, BLACK, GREEN, BLUE, RED, GOLD, GRAY, LIGHT_GRAY, VOLUME, DARK_RED
from src.pokemon.data import Pokemon
from src.pokemon.poffin import BERRY_PRICE
from src.pokemon.contest import (feebas_ready, feed_pokeblock, POKEBLOCKS, POKEBLOCK_PRICE, CATEGORIES,
                                 CATEGORY_COLOR, MAX_CONDITION, FEEBAS_BEAUTY)
from src.states.battle import TrainerBattleState, TrainerIntroState
import random


G_MAX_RED = (220, 30, 70)


def _draw_gmax_tag(screen, font, x, y):
    """Small red "G-MAX" badge marking a Pokemon with the Gigantamax Factor."""
    label = font.render("G-MAX", True, WHITE)
    box = label.get_rect(topleft=(x, y)).inflate(10, 6)
    pygame.draw.rect(screen, G_MAX_RED, box, border_radius=6)
    pygame.draw.rect(screen, WHITE, box, 2, border_radius=6)
    screen.blit(label, label.get_rect(center=box.center))


# [REF-0060: Journal System]
class JournalState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.missions = game.story_manager.get_all_journal_entries()
        self.missions.sort(key=lambda x: 0 if x["status"] == "ACTIVE" else 1)
        self.scroll_idx = 0

        self.btn_back = Button(
            (30, 30, 140, 70), "BACK", game.assets.fonts["small"],
            self.go_back, bg_color=RED
        )

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.add_element(self.btn_back)
        for m in self.missions:
            if m["id"] not in self.game.story_manager.notified_missions:
                self.game.story_manager.notified_missions.append(m["id"])

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    self.scroll_idx = max(0, self.scroll_idx - 1)
                elif event.button == 5:
                    max_scroll = max(0, len(self.missions) - 3)
                    self.scroll_idx = min(max_scroll, self.scroll_idx + 1)

    def update(self):
        pass

    def draw(self):
        screen = self.game.screen
        screen.fill((20, 20, 30))

        # Header
        Utils.draw_text_outline(screen, "ADVENTURE JOURNAL", self.game.assets.fonts["med"], GOLD, self.game.width//2, 60)

        if not self.missions:
            Utils.draw_text_outline(screen, "No active missions. Explore Kanto!", self.game.assets.fonts["s_med"], WHITE, self.game.width//2, self.game.height//2)
            self.game.ui_manager.draw(screen)
            return

        start_y = 150
        card_w = self.game.width - 200
        card_h = 180
        spacing = 20

        for i, m in enumerate(self.missions[self.scroll_idx: self.scroll_idx + 3]):
            rect = pygame.Rect(100, start_y + i * (card_h + spacing), card_w, card_h)

            bg_col = (40, 45, 70) if m["status"] == "ACTIVE" else (25, 25, 35)
            pygame.draw.rect(screen, bg_col, rect, border_radius=15)
            pygame.draw.rect(screen, WHITE, rect, 3, border_radius=15)

            type_lbl = "[STORY]" if m["type"] == "MAIN" else "[SIDE]"
            Utils.draw_text_outline(
                screen,
                f"{type_lbl} {m['text']}",
                self.game.assets.fonts["s_med"],
                GOLD,
                rect.x + 20,
                rect.y + 40,
                align="left")

            stat_col = GREEN if m["status"] == "COMPLETED" else GOLD
            Utils.draw_text_outline(screen, f"STATUS: {m['status']}", self.game.assets.fonts["tiny"], stat_col, rect.right - 20, rect.y + 40, align="right")
            reward = m.get("reward", "None")
            Utils.draw_text_outline(screen, f"REWARD: {reward}", self.game.assets.fonts["tiny"], (0, 200, 255), rect.right - 20, rect.bottom - 30, align="right")

            if m["status"] == "ACTIVE":
                desc_font = self.game.assets.fonts["tiny"]
                Utils.draw_multiline_text(
                    screen, m["desc"], desc_font, WHITE,
                    rect.x + 20, rect.y + 80,
                    max_width=card_w - 40, line_height=30,
                    center=False,
                    align="left"
                )

        self.game.ui_manager.draw(screen)


# [REF-0020: Party Menu System]
class PokemonPartyMenuState(GameState):

    def __init__(self, game, previous_state, context="normal", on_select=None, on_cancel=None):
        super().__init__(game)
        self.previous_state = previous_state
        self.context = context
        self.on_select = on_select
        self.on_cancel = on_cancel
        if context == "forced_switch":
            self.message = "Choose a new PKMN!"
        elif context == "battle_switch":
            self.message = "Send out which PKMN?"
        else:
            self.message = "Choose a PKMN."
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

        start_y = int(self.game.height * 0.10)
        slot_w = int(self.game.width * 0.43)
        slot_h = 118
        gap = 22

        team = getattr(self.game.story_manager, "player_team", [])[:6]

        for i in range(6):
            row = i // 2
            col = i % 2
            x = int(self.game.width * 0.055) + col * (slot_w + gap)
            y = start_y + row * (slot_h + gap)

            slot_rect = pygame.Rect(x, y, slot_w, slot_h)
            pokemon = team[i] if i < len(team) else None

            slot = PartySlotUI(slot_rect, pokemon, i, self._slot_clicked, self.game)
            self.slots.append(slot)
            self.game.ui_manager.add_element(slot)

        self.game.ui_manager.add_element(self.dialogue_box)

        if self.context != "forced_switch":
            self.cancel_btn = Button(
                rect=(self.bottom_rect.right - 180, self.bottom_rect.centery - 30, 140, 60),
                text="CANCEL",
                font=self.game.assets.fonts["med"],
                callback=self._cancel,
                bg_color=(200, 40, 40),
                text_color=WHITE,
                border_radius=12
            )
            self.game.ui_manager.add_element(self.cancel_btn)

        self.btn_switch = Button(
            rect=(0, 0, 150, 50), text="MOVE" if self.context == "normal" else "SWITCH", font=self.game.assets.fonts["s_med"],
            callback=self._confirm_switch, bg_color=GREEN, visible=False
        )
        self.btn_summary = Button(
            rect=(0, 0, 150, 50), text="SUMMARY", font=self.game.assets.fonts["s_med"],
            callback=self._show_summary, bg_color=BLUE, visible=False
        )

        self.popup_buttons = [self.btn_switch, self.btn_summary]
        for btn in self.popup_buttons:
            self.game.ui_manager.add_element(btn)

    def _slot_clicked(self, index):
        team = getattr(self.game.story_manager, "player_team", [])
        if index >= len(team) or self.popup_active:
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
            self.message = "Choose a PKMN."
            return

        if self.context == "use_item":
            if self.on_select:
                self.on_select(index)
            return

        self.selected_slot_index = index

        if self.context in ["battle_switch", "normal"]:
            self.popup_active = True
            clicked_slot_rect = self.slots[index].rect

            popup_w = 150

            if index % 2 == 0:
                base_x = clicked_slot_rect.right + 10
            else:
                base_x = clicked_slot_rect.left - popup_w - 10

            self.btn_switch.rect.topleft = (base_x, clicked_slot_rect.centery - 55)
            self.btn_summary.rect.topleft = (base_x, clicked_slot_rect.centery + 5)

            self.btn_switch.set_visibility(True)
            self.btn_summary.set_visibility(True)
        elif self.on_select:
            self.on_select(index)
        else:
            pkmn = team[index]
            self.game.show_dialogue([f"Selected {pkmn.display_name.upper()}!"], self._return)

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
            self.game.change_state(PokemonDetailState(self.game, pkmn, self))
        self._hide_popup()

    def _hide_popup(self):
        self.popup_active = False
        self.selected_slot_index = -1
        self.btn_switch.set_visibility(False)
        self.btn_summary.set_visibility(False)

    def _cancel(self):
        if self.popup_active:
            self._hide_popup()
        elif self.move_swap_index is not None:
            self.move_swap_index = None
            self.message = "Choose a PKMN."
            self._hide_popup()
        else:
            if self.on_cancel:
                self.on_cancel()
            self._return()

    def _dismiss_dialogue(self):
        self.dialogue_box.visible = False

    def _return(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def handle_events(self, events):
        if self.popup_active:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    is_outside = True
                    if self.btn_switch.rect.collidepoint(event.pos) or self.btn_summary.rect.collidepoint(event.pos):
                        is_outside = False
                    for slot in self.slots:
                        if slot.rect.collidepoint(event.pos):
                            is_outside = False

                    if is_outside:
                        self._hide_popup()

    def update(self):
        if self.dialogue_box.visible:
            self.dialogue_box.update()

    def draw(self):
        self.game.screen.fill((15, 35, 85))

        if not self.dialogue_box.visible:
            Utils.draw_classic_panel(self.game.screen, self.bottom_rect.x, self.bottom_rect.y, self.bottom_rect.width, self.bottom_rect.height)

            left_rect_w = int(self.bottom_rect.width * 0.55)
            Utils.draw_multiline_text(
                self.game.screen, self.message,
                self.game.assets.fonts["med"], WHITE,
                self.bottom_rect.x + left_rect_w // 2,
                self.bottom_rect.centery,
                max_width=left_rect_w - 40,
                outline_color=BLACK
            )

        if self.popup_active:
            popup_w = 150
            popup_h = 120
            popup_rect = pygame.Rect(0, 0, popup_w, popup_h)
            popup_rect.topleft = (self.btn_switch.rect.left - 10, self.btn_switch.rect.top - 10)
            pygame.draw.rect(self.game.screen, (20, 40, 90), popup_rect, border_radius=10)
            pygame.draw.rect(self.game.screen, WHITE, popup_rect, 3, border_radius=10)

        # Highlight swapping source
        if self.move_swap_index is not None and self.move_swap_index < len(self.slots):
            slot = self.slots[self.move_swap_index]
            pygame.draw.rect(self.game.screen, GOLD, slot.rect, 4, border_radius=14)

        self.game.ui_manager.draw(self.game.screen)


# [REF-0034: PokeMart System]
class PokeMartState(GameState):
    def __init__(self, game, previous_state, stock=None):
        """stock: sell only these items (e.g. a Contest Hall's Pokéblock stand)."""
        super().__init__(game)
        self.previous_state = previous_state
        self.stock = stock
        self.phase = "SHOP"
        self.shop_buttons = []
        self.current_page = 0
        self.items_per_page = 8
        self.pending_item = None
        self.pending_cost = 0

        self.bottom_rect = Utils.get_full_dialogue_rect(game)

        self.btn_back = Button((20, 20, 100, 50), "EXIT", game.assets.fonts["tiny"], self.exit_shop, bg_color=RED)

        self.btn_prev = Button((self.bottom_rect.left + 10, self.bottom_rect.centery - 25, 50, 50), "<", game.assets.fonts["med"], self.prev_page, visible=False)
        self.btn_next = Button((self.bottom_rect.right - 60, self.bottom_rect.centery - 25, 50, 50), ">", game.assets.fonts["med"], self.next_page, visible=False)

        cx, cy = game.width // 2, game.height // 2
        self.btn_yes = Button((cx - 150, cy + 50, 120, 60), "BUY", game.assets.fonts["small"], self.confirm_purchase, bg_color=GREEN, autosize=False, visible=False)
        self.btn_no = Button((cx + 30, cy + 50, 120, 60), "CANCEL", game.assets.fonts["small"], self.cancel_purchase, bg_color=RED, autosize=False, visible=False)

        self.dialogue_box = ClassicDialogueBox(self.bottom_rect, [], game.assets.fonts["med"], visible=False)

        self.bg = self._load_building_bg(game, "mart")

        area_key = game.story_manager.current_area_key
        flag = f"visited_mart_{area_key}"

        if stock is None and not game.story_manager.story_flags.get(flag, False):
            msg = ["Welcome to the Poké Mart!", "We are currently stocking shelves.", "Here, take these 10 Poké Balls!"]
            game.story_manager.balls_left += 10
            game.story_manager.story_flags[flag] = True
            self.dialogue_box.reset(msg)
            self.dialogue_box.callback = self.on_welcome_dialogue_end
            self.phase = "DIALOGUE"

    WEATHER_ROCKS = {"RAIN": "DAMP_ROCK", "SUN": "HEAT_ROCK", "SAND": "SMOOTH_ROCK", "SNOW": "ICY_ROCK"}

    def _shop_items(self):
        if self.stock is not None:
            return list(self.stock)
        if self._is_department_store():
            evo_items = sorted(list(self.game.loader.evolution_map.get("EVOLUTION_ITEMS", {}).keys()))
            items = ["POKE_BALLS", "RARE_CANDY"] + evo_items
        else:
            items = ["POKE_BALLS", "RARE_CANDY", "POTION", "REVIVE"]
        return items + self._regional_weather_rocks() + self._contest_items()

    def _contest_items(self):
        """Towns with a Contest Hall stock Pokéblocks."""
        options = self.game.story_manager.get_current_area_data().get("explore_options", [])
        if any(o.get("target") == "contest_hall" for o in options):
            return list(POKEBLOCKS)
        return []

    def _regional_weather_rocks(self):
        """Rocks for the kinds of weather found in this region this season
        (Galar's Wild Area has them all)."""
        from src.world import seasons
        found = seasons.region_weathers(self.game, self.game.story_manager.get_current_region())
        return [rock for w, rock in self.WEATHER_ROCKS.items() if w in found]

    def _is_department_store(self):
        """Celadon/Goldenrod, or any area flagged "department_store" (sells evolution items)."""
        story = self.game.story_manager
        return (story.current_area_key in ["CELADON_CITY", "GOLDENROD_CITY"]
                or bool(story.get_current_area_data().get("department_store")))

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_buttons()

    def next_page(self):
        all_items = self._shop_items()
        if (self.current_page + 1) * self.items_per_page < len(all_items):
            self.current_page += 1
            self.refresh_buttons()

    def refresh_buttons(self):
        self.game.ui_manager.elements.clear()
        self.game.ui_manager.add_element(self.btn_back)
        self.game.ui_manager.add_element(self.btn_prev)
        self.game.ui_manager.add_element(self.btn_next)
        self.game.ui_manager.add_element(self.btn_yes)
        self.game.ui_manager.add_element(self.btn_no)
        self.game.ui_manager.add_element(self.dialogue_box)

        self.shop_buttons = []

        all_items = self._shop_items()

        self.btn_prev.set_visibility(self.current_page > 0)
        self.btn_next.set_visibility((self.current_page + 1) * self.items_per_page < len(all_items))

        start_idx = self.current_page * self.items_per_page
        page_items = all_items[start_idx: start_idx + self.items_per_page]

        cols = 4
        rows = 2

        grid_x = self.bottom_rect.left + 70
        grid_y = self.bottom_rect.top + 20
        grid_w = self.bottom_rect.width - 140
        grid_h = self.bottom_rect.height - 40

        cell_w = grid_w // cols
        cell_h = grid_h // rows
        btn_w = cell_w - 10
        btn_h = cell_h - 10

        for i, item in enumerate(page_items):
            row = i // cols
            col = i % cols
            x = grid_x + col * cell_w + 5
            y = grid_y + row * cell_h + 5

            if item == "POKE_BALLS":
                name = "5 Poké Balls"
                price = 1000
                icon = self.game.assets.ui_ball
            elif item == "RARE_CANDY":
                name = "Rare Candy"
                price = 10000
                icon = self.game.assets.get_item_image("RARE_CANDY")
            elif item == "POTION":
                name = "Potion"
                price = 500
                icon = self.game.assets.get_item_image("POTION")
            elif item == "REVIVE":
                name = "Revive"
                price = 1000
                icon = self.game.assets.get_item_image("REVIVE")

            else:
                name = item.replace("_", " ").title().replace(" Fossil", "")
                price = (999999 if item == "UPGRADE" else 2000 if item in self.WEATHER_ROCKS.values()
                         else 5000 if item.endswith(("ITE", "ITE_X", "ITE_Y"))
                         else POKEBLOCK_PRICE if item in POKEBLOCKS
                         else BERRY_PRICE if item.endswith("_BERRY") else 10000)
                icon = self.game.assets.get_item_image(item)
                if icon:
                    icon = pygame.transform.scale(icon, (32, 32))

            btn = Button(
                rect=(x, y, btn_w, btn_h),
                text=f"{name} ${price}",
                font=self.game.assets.fonts["tiny"],
                callback=lambda k=item, p=price: self.init_purchase(k, p),
                bg_color=BLUE,
                icon=icon,
                autosize=False
            )
            self.shop_buttons.append(btn)
            self.game.ui_manager.add_element(btn)

    def init_purchase(self, item_key, price):
        self.pending_item = item_key
        self.pending_cost = price
        self.phase = "CONFIRM"

        item_name = "5 Poké Balls" if item_key == "POKE_BALLS" else item_key.replace("_", " ").title()
        self.dialogue_box.reset([f"Buy {item_name}?", f"Cost: ${price}"])
        self.dialogue_box.set_visibility(True)
        self.btn_yes.set_visibility(True)
        self.btn_no.set_visibility(True)

    def confirm_purchase(self):
        if self.game.story_manager.money >= self.pending_cost:
            self.game.story_manager.money -= self.pending_cost

            if self.pending_item == "POKE_BALLS":
                self.game.story_manager.balls_left += 5
            else:
                self.game.story_manager.inventory[self.pending_item] = self.game.story_manager.inventory.get(self.pending_item, 0) + 1

            if self.game.assets.heal_sfx:
                self.game.assets.heal_sfx.play()

            self.dialogue_box.reset(["Purchase successful!"])
            self.dialogue_box.callback = self.cancel_purchase
        else:
            self.dialogue_box.reset(["You don't have enough money!"])
            self.dialogue_box.callback = self.cancel_purchase

        self.btn_yes.set_visibility(False)
        self.btn_no.set_visibility(False)

    def cancel_purchase(self):
        self.phase = "SHOP"
        self.dialogue_box.set_visibility(False)
        self.btn_yes.set_visibility(False)
        self.btn_no.set_visibility(False)
        self.pending_item = None

    def start(self):
        self.game.ui_manager.elements.clear()
        if self.phase == "DIALOGUE":
            self.game.ui_manager.add_element(self.dialogue_box)
        else:
            self.refresh_buttons()

    def on_welcome_dialogue_end(self):
        self.phase = "SHOP"
        self.dialogue_box.set_visibility(False)
        self.refresh_buttons()

    def _load_building_bg(self, game, type_suffix):
        area_data = game.story_manager.get_current_area_data()
        json_key = "pokecenter" if type_suffix == "center" else "pokemart"
        bg_config = area_data.get("backgrounds", {}).get(json_key)

        area_key = game.story_manager.current_area_key
        first_part = area_key.split('_')[0].lower()
        fallback_name = f"{first_part}_city_{type_suffix}.png"

        filenames = [bg_config, fallback_name] if bg_config else [fallback_name]
        box_top = Utils.get_full_dialogue_rect(game).top

        for filename in filenames:
            img = game.assets.get_background(filename)
            if img:
                return pygame.transform.scale(img, (game.width, box_top))

        bg = pygame.Surface((game.width, box_top))
        bg.fill(BLUE)
        return bg

    def exit_shop(self):
        self.game.change_state(self.previous_state)

    def handle_events(self, events):
        if self.phase == "DIALOGUE":
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.dialogue_box.handle_event(event)

        elif self.phase == "CONFIRM":
            pass

    def update(self):
        if self.phase == "DIALOGUE" or self.phase == "CONFIRM":
            self.dialogue_box.update()

    def draw(self):
        self.game.screen.fill(BLACK)
        self.game.screen.blit(self.bg, (0, 0))

        if self.phase == "SHOP" or self.phase == "CONFIRM":
            Utils.draw_classic_panel(self.game.screen, self.bottom_rect.x, self.bottom_rect.y, self.bottom_rect.width, self.bottom_rect.height)

            lbl = f"${self.game.story_manager.money}"
            Utils.draw_text_outline(
                self.game.screen,
                lbl,
                self.game.assets.fonts["small"],
                GOLD,
                self.game.width - 20,
                20,
                align="right",
                outline_color=BLACK
            )

            ball_lbl = f"Balls: {self.game.story_manager.balls_left}"
            Utils.draw_text_outline(self.game.screen, ball_lbl, self.game.assets.fonts["small"], WHITE, self.game.width - 20, 50, align="right", outline_color=BLACK)

        self.game.ui_manager.draw(self.game.screen)


# [REF-0031: PC System]
class PCState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.party = game.story_manager.player_team
        self.pc = game.story_manager.pc_pokemon
        self.selected_party_idx = None
        self.selected_pc_idx = None
        self.scroll_y = 0

        self.box_index = 0
        self.mons_per_box = 30

        self.font = game.assets.fonts["tiny"]
        self.btn_back = Button((20, 20, 100, 50), "BACK", self.font, self.go_back, bg_color=RED)

        self.btn_prev_box = Button((420, 75, 40, 40), "<", self.font, self.prev_box, bg_color=BLUE)
        self.btn_next_box = Button((750, 75, 40, 40), ">", self.font, self.next_box, bg_color=BLUE)

        self.btn_sort_id = Button((820, 75, 100, 40), "SORT ID", self.font, self.sort_by_id, bg_color=GOLD)
        self.btn_sort_name = Button((930, 75, 120, 40), "SORT NAME", self.font, self.sort_by_name, bg_color=GOLD)
        self.btn_release = Button((50, 650, 150, 50), "RELEASE", self.font, self.release_pokemon, bg_color=RED, visible=False)

        self.grid_start_x = 400
        self.grid_start_y = 100
        self.slot_size = 270
        self.slot_gap = 15
        self.sprite_size = 240

    def go_back(self):
        if not self.party:
            self.game.show_dialogue(["You must have at least one Pokémon in your party!"])
            return
        self.game.change_state(self.previous_state)

    def prev_box(self):
        self.box_index = (self.box_index - 1) % self.get_total_boxes()
        self.scroll_y = 0

    def next_box(self):
        self.box_index = (self.box_index + 1) % self.get_total_boxes()
        self.scroll_y = 0

    def sort_by_id(self):
        start = self.box_index * self.mons_per_box
        end = start + self.mons_per_box
        box_mons = [p for p in self.pc[start:end] if p is not None]

        def get_base_id(p):
            if p.id >= 2000:
                mapping = self.game.loader.area_data.get("FORM_MAP", {}).get(str(p.id))
                if mapping:
                    return mapping.get("id", p.id)
            return p.id

        box_mons.sort(key=get_base_id)
        self.pc[start:end] = box_mons + [None] * (self.mons_per_box - len(box_mons))

    def sort_by_name(self):
        start = self.box_index * self.mons_per_box
        end = start + self.mons_per_box
        box_mons = [p for p in self.pc[start:end] if p is not None]
        box_mons.sort(key=lambda x: x.display_name.upper())
        self.pc[start:end] = box_mons + [None] * (self.mons_per_box - len(box_mons))

    def release_pokemon(self):
        if self.selected_pc_idx is not None:
            p = self.pc[self.selected_pc_idx]
            self.pc[self.selected_pc_idx] = None
            msg = f"Released {p.display_name.upper()} back into the wild!"
            self.selected_pc_idx = None
            self.game.show_dialogue([msg])

    def get_total_boxes(self):
        return max(1, (len(self.pc) + self.mons_per_box - 1) // self.mons_per_box)

    def start(self):
        self.game.ui_manager.add_element(self.btn_back)
        self.game.ui_manager.add_element(self.btn_prev_box)
        self.game.ui_manager.add_element(self.btn_next_box)
        self.game.ui_manager.add_element(self.btn_sort_id)
        self.game.ui_manager.add_element(self.btn_sort_name)
        self.game.ui_manager.add_element(self.btn_release)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    self.scroll_y = max(0, self.scroll_y - 60)
                elif event.button == 5:
                    available_w = self.game.width - self.grid_start_x - 20
                    cols = max(1, available_w // (self.slot_size + self.slot_gap))
                    rows = (self.mons_per_box + cols - 1) // cols
                    total_h = rows * (self.slot_size + self.slot_gap)
                    max_scroll = max(0, total_h - (self.game.height - self.grid_start_y - 50))
                    self.scroll_y = min(max_scroll, self.scroll_y + 60)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for i in range(6):
                        rect = pygame.Rect(50, 100 + i * 85, 300, 75)
                        if rect.collidepoint(event.pos):
                            self.handle_click("party", i)
                            return

                    available_w = self.game.width - self.grid_start_x - 20
                    cols = max(1, available_w // (self.slot_size + self.slot_gap))

                    box_start = self.box_index * self.mons_per_box
                    box_end = box_start + self.mons_per_box
                    for i in range(box_start, box_end):
                        local_idx = i - box_start
                        c, r = local_idx % cols, local_idx // cols
                        rx = self.grid_start_x + c * (self.slot_size + self.slot_gap)
                        ry = self.grid_start_y + r * (self.slot_size + self.slot_gap) - self.scroll_y

                        slot_rect = pygame.Rect(rx, ry, self.slot_size, self.slot_size)
                        if slot_rect.collidepoint(event.pos):
                            self.handle_click("pc", i)
                            return

    def handle_click(self, source, index):
        if source == "party":
            if index >= len(self.party):
                if self.selected_pc_idx is not None and self.pc[self.selected_pc_idx] is not None:
                    self.party.append(self.pc[self.selected_pc_idx])
                    self.pc[self.selected_pc_idx] = None
                    self.selected_pc_idx = None
                return

            if self.selected_party_idx == index:
                self.selected_party_idx = None
            elif self.selected_party_idx is not None:
                old_idx = self.selected_party_idx
                self.party[index], self.party[old_idx] = self.party[old_idx], self.party[index]
                self.selected_party_idx = None
            elif self.selected_pc_idx is not None:
                pc_mon = self.pc[self.selected_pc_idx]
                self.pc[self.selected_pc_idx] = self.party[index]
                self.party[index] = pc_mon
                self.selected_pc_idx = None
            else:
                self.selected_party_idx = index

        elif source == "pc":
            if self.selected_pc_idx == index:
                self.selected_pc_idx = None
            elif self.selected_pc_idx is not None:
                self.pc[index], self.pc[self.selected_pc_idx] = self.pc[self.selected_pc_idx], self.pc[index]
                self.selected_pc_idx = None
            elif self.selected_party_idx is not None:
                if len(self.party) == 1 and self.pc[index] is None:
                    self.game.show_dialogue(["Can't store your last Pokémon!"])
                    return

                old_p_idx = self.selected_party_idx
                party_mon = self.party[old_p_idx]

                if self.pc[index] is None:
                    self.pc[index] = party_mon
                    self.party.pop(old_p_idx)
                else:
                    self.party[old_p_idx] = self.pc[index]
                    self.pc[index] = party_mon

                self.selected_party_idx = None
            elif self.pc[index] is not None:
                self.selected_pc_idx = index

    def update(self):
        self.btn_release.set_visibility(self.selected_pc_idx is not None)

    def draw(self):
        self.game.screen.fill((30, 50, 60))
        Utils.draw_text_outline(self.game.screen, "BILL'S PC", self.game.assets.fonts["med"], WHITE, self.game.width//2, 40)

        Utils.draw_text_outline(self.game.screen, "PARTY", self.font, GOLD, 200, 85)
        for i in range(6):
            rect = pygame.Rect(50, 100 + i * 85, 300, 75)
            color = (60, 100, 150)
            if i < len(self.party):
                if self.selected_party_idx == i:
                    color = (100, 200, 100)
                pygame.draw.rect(self.game.screen, color, rect, border_radius=10)
                pygame.draw.rect(self.game.screen, WHITE, rect, 2, border_radius=10)

                p = self.party[i]
                if p.sidebar_image:
                    self.game.screen.blit(p.sidebar_image, (rect.x + 10, rect.y + 5))

                Utils.draw_text_outline(
                    self.game.screen,
                    p.display_name,
                    self.font,
                    WHITE,
                    rect.x + 90,
                    rect.y + 25,
                    align="left")
            else:
                pygame.draw.rect(self.game.screen, (40, 60, 80), rect, border_radius=10)
                pygame.draw.rect(self.game.screen, (80, 100, 120), rect, 2, border_radius=10)

        box_label = f"BOX {self.box_index + 1} ({len(self.pc)})"
        Utils.draw_text_outline(self.game.screen, box_label, self.font, GOLD, 600, 85)

        available_w = self.game.width - self.grid_start_x - 20
        cols = max(1, available_w // (self.slot_size + self.slot_gap))

        box_start = self.box_index * self.mons_per_box
        box_end = box_start + self.mons_per_box

        old_clip = self.game.screen.get_clip()
        clip_rect = pygame.Rect(self.grid_start_x - 10, self.grid_start_y, available_w + 30, self.game.height - self.grid_start_y - 20)
        self.game.screen.set_clip(clip_rect)

        for i in range(box_start, box_end):
            local_idx = i - box_start
            c, r = local_idx % cols, local_idx // cols
            rx = self.grid_start_x + c * (self.slot_size + self.slot_gap)
            ry = self.grid_start_y + r * (self.slot_size + self.slot_gap) - self.scroll_y

            rect = pygame.Rect(rx, ry, self.slot_size, self.slot_size)

            if i < len(self.pc) and self.pc[i] is not None:
                color = (60, 100, 150)
                if self.selected_pc_idx == i:
                    color = (100, 200, 100)
                pygame.draw.rect(self.game.screen, color, rect, border_radius=5)
                pygame.draw.rect(self.game.screen, WHITE, rect, 2, border_radius=5)

                p = self.pc[i]
                sprite = p.image if p.image else p.sidebar_image
                if sprite:
                    spr = pygame.transform.scale(sprite, (self.sprite_size, self.sprite_size))
                    spr_rect = spr.get_rect(center=rect.center)
                    self.game.screen.blit(spr, spr_rect)

                base_id = p.id
                prefix = ""
                if p.id >= 2000:
                    mapping = self.game.loader.area_data.get("FORM_MAP", {}).get(str(p.id))
                    if mapping:
                        base_id = mapping.get("id", base_id)
                        prefix = f"{p.form} "

                Utils.draw_text_outline(
                    self.game.screen,
                    f"{prefix}#{base_id}",
                    self.font,
                    WHITE,
                    rect.right - 10,
                    rect.top + 10,
                    align="right"
                )

                Utils.draw_text_outline(
                    self.game.screen,
                    p.display_name.upper(),
                    self.font,
                    WHITE,
                    rect.centerx,
                    rect.bottom - 20
                )
            else:
                pygame.draw.rect(self.game.screen, (40, 60, 80), rect, border_radius=5)
                pygame.draw.rect(self.game.screen, (80, 100, 120), rect, 2, border_radius=5)
                Utils.draw_text_outline(self.game.screen, "+", self.game.assets.fonts["med"], GRAY, rect.centerx, rect.centery)
        self.game.screen.set_clip(old_clip)

        self.game.ui_manager.draw(self.game.screen)


# [REF-0032: Bag System]
class BagState(GameState):
    def __init__(self, game, previous_state, context="normal"):
        super().__init__(game)
        self.previous_state = previous_state
        self.context = context
        self.evo_items_map = self.game.loader.evolution_map.get("EVOLUTION_ITEMS", {})
        self.evo_keys = sorted(list(self.evo_items_map.keys()))

        self.pages = ["USEABLE ITEMS", "KEY ITEMS"] if context != "battle" else ["USEABLE ITEMS"]
        self.current_page = 0

        self.btn_back = Button(
            rect=(30, 30, 140, 70),
            text="BACK",
            font=game.assets.fonts["small"],
            callback=self.go_back,
            bg_color=RED,
        )

        cy = game.height // 2
        self.btn_prev = Button((20, cy - 30, 60, 60), "<", game.assets.fonts["med"], self.prev_page)
        self.btn_next = Button((game.width - 80, cy - 30, 60, 60), ">", game.assets.fonts["med"], self.next_page)

        self.item_buttons = []
        self.refresh_buttons()

    def prev_page(self):
        self.current_page = (self.current_page - 1) % len(self.pages)
        self.refresh_buttons()

    def next_page(self):
        self.current_page = (self.current_page + 1) % len(self.pages)
        self.refresh_buttons()

    def go_back(self):
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.elements.clear()
        self.game.ui_manager.add_element(self.btn_back)
        self.game.ui_manager.add_element(self.btn_prev)
        self.game.ui_manager.add_element(self.btn_next)
        for btn in self.item_buttons:
            self.game.ui_manager.add_element(btn)

    def refresh_buttons(self):
        for btn in self.item_buttons:
            if btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)

        self.item_buttons = []

        items_to_show = []
        if self.context == "battle":
            for key in ["POTION", "REVIVE", "DAMP_ROCK", "HEAT_ROCK", "SMOOTH_ROCK", "ICY_ROCK"]:
                qty = self.game.story_manager.inventory.get(key, 0)
                if qty > 0:
                    items_to_show.append((key, qty))
        elif self.current_page == 0:
            if self.game.story_manager.inventory.get("RARE_CANDY", 0) > 0:
                items_to_show.append(("RARE_CANDY", self.game.story_manager.inventory["RARE_CANDY"]))

            if self.game.story_manager.inventory.get("POTION", 0) > 0:
                items_to_show.append(("POTION", self.game.story_manager.inventory["POTION"]))
            if self.game.story_manager.inventory.get("REVIVE", 0) > 0:
                items_to_show.append(("REVIVE", self.game.story_manager.inventory["REVIVE"]))

            for key in self.evo_keys:
                qty = self.game.story_manager.inventory.get(key, 0)
                if qty > 0:
                    items_to_show.append((key, qty))
            for key in POKEBLOCKS:
                qty = self.game.story_manager.inventory.get(key, 0)
                if qty > 0:
                    items_to_show.append((key, qty))
        elif self.current_page == 1:
            config = self.game.loader.area_data.get("GAME_CONFIG", {})
            key_item_list = config.get("KEY_ITEMS", [])
            for key in key_item_list:
                qty = self.game.story_manager.inventory.get(key, 0)
                if qty > 0:
                    items_to_show.append((key, qty))

        start_y = 120
        btn_h = 60
        cols = 2
        col_w = (self.game.width - 180) // cols

        if not items_to_show:
            return

        for i, (item_key, qty) in enumerate(items_to_show):
            row = i // cols
            col = i % cols

            x = 90 + col * col_w
            y = start_y + row * (btn_h + 10)

            display_name = f"{item_key.replace('_', ' ').title()}  x{qty}"

            is_rare_candy = (item_key == "RARE_CANDY")
            is_usable_key = item_key in ["TOWN_MAP", "JOHTO_MAP", "UNOWN_REPORT", "POFFIN_CASE", "BERRY_POUCH", "WEATHER_DIAL"]

            can_use = (qty > 0 and (self.current_page == 0 or is_rare_candy or is_usable_key))
            color = BLUE if can_use else GRAY
            callback = (lambda k=item_key: self.use_item(k)) if can_use else None

            icon = self.game.assets.get_item_image(item_key)

            if item_key == "MYSTERY_EGG":
                egg_path = os.path.join(self.game.assets.pokemon_sprites_dir, "egg.png")
                if os.path.exists(egg_path):
                    icon = pygame.image.load(egg_path).convert_alpha()
                    icon = pygame.transform.scale(icon, (128, 128))

            btn = Button(
                rect=(x, y, col_w - 20, btn_h),
                text=display_name,
                font=self.game.assets.fonts["tiny"],
                callback=callback,
                bg_color=color,
                icon=icon,
                autosize=False
            )
            self.item_buttons.append(btn)

        for btn in self.item_buttons:
            self.game.ui_manager.add_element(btn)

    def handle_events(self, events):
        pass

    def update(self):
        pass

    def use_item(self, item_key):
        self.selected_item = item_key

        if item_key == "RARE_CANDY":
            self.game.change_state(PokemonPartyMenuState(
                self.game,
                previous_state=self,
                context="use_item",
                on_select=self.on_pokemon_select_rare_candy
            ))
            return

        if item_key == "POTION":
            self.game.change_state(PokemonPartyMenuState(
                self.game, previous_state=self, context="use_item",
                on_select=self.on_pokemon_select_potion
            ))
            return

        if item_key == "REVIVE":
            self.game.change_state(PokemonPartyMenuState(
                self.game, previous_state=self, context="use_item",
                on_select=self.on_pokemon_select_revive
            ))
            return

        if item_key.endswith("_ROCK") and self.context == "battle":
            battle = self.previous_state
            self.game.change_state(battle)
            if battle.weather_summoned:
                battle.show_message(["The rock has already been used this battle!"],
                                    callback=battle.return_to_menu)
            else:
                battle.show_message([battle.summon_weather(item_key)], callback=battle.on_item_used)
            return

        if item_key in POKEBLOCKS:
            self.game.change_state(PokemonPartyMenuState(
                self.game, previous_state=self, context="use_item",
                on_select=self.on_pokemon_select_pokeblock
            ))
            return

        if item_key == "POFFIN_CASE":
            from src.states.poffin import PoffinCaseState
            self.game.change_state(PoffinCaseState(self.game, self))
            return

        if item_key == "WEATHER_DIAL":
            from src.states.weather import WeatherDialState
            self.game.change_state(WeatherDialState(self.game, self))
            return

        if item_key == "BERRY_POUCH":
            from src.pokemon.poffin import BERRIES, berry_name, berry_label
            inv = self.game.story_manager.inventory
            lines = [f"{berry_name(b)} x{inv[b]} ({berry_label(b)})" for b in BERRIES if inv.get(b, 0) > 0]
            self.game.change_state(self)
            self.refresh_buttons()
            self.game.show_dialogue(lines or ["Your BERRY POUCH is empty."])
            return

        if item_key == "UNOWN_REPORT":
            self.game.change_state(UnownReportState(self.game, self))
            return

        if item_key in ["TOWN_MAP", "JOHTO_MAP"]:
            self.game.change_state(MapState(self.game, self))
            return

        self.game.change_state(PokemonPartyMenuState(
            self.game,
            previous_state=self,
            context="use_item",
            on_select=self.on_pokemon_select
        ))

    def on_pokemon_select(self, slot_index):
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return

        pokemon = party[slot_index]
        evolution_data = self.evo_items_map.get(self.selected_item, {})

        p_key = pokemon.name.upper()
        if pokemon.form and pokemon.form != "normal":
            alt_key = f"{p_key}_{pokemon.form.upper()}"
            if alt_key in evolution_data:
                p_key = alt_key

        if p_key in evolution_data:
            target_name = evolution_data[p_key]
            target_id = self.game.name_to_id.get(target_name.split("_")[0])

            target_form = "normal"
            if "_" in target_name:
                target_form = target_name.split("_", 1)[1].lower()

            if target_id:
                self.game.story_manager.inventory[self.selected_item] -= 1
                if self.game.story_manager.inventory[self.selected_item] < 0:
                    self.game.story_manager.inventory[self.selected_item] = 0
                self.game.change_state(EvolutionState(
                    self.game, pokemon, target_id, slot_index, next_form=target_form,
                    return_state=self.previous_state
                ))
            else:
                self.game.show_dialogue(["Error: Evolution data missing."])
        else:
            self.game.show_dialogue(["It won't have any effect."])

    def on_pokemon_select_rare_candy(self, slot_index):
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return

        pokemon = party[slot_index]

        # ARCHITECT: Use standardized key generation to match regional variants in evolution_map
        p_name = pokemon.name.upper()
        key = p_name
        if pokemon.form and pokemon.form != "normal":
            key = f"{p_name}_{pokemon.form.upper()}"

        # ARCHITECT: Check for item locks to prevent Rare Candy from bypassing item requirements
        item_locks = self.game.loader.evolution_map.get("ITEM_LOCKS", [])
        is_item_locked = (key in item_locks) or (p_name in item_locks) or not feebas_ready(pokemon)

        next_entries = self.game.loader.evolution_map.get(key)
        if not next_entries and key != p_name:
            next_entries = self.game.loader.evolution_map.get(p_name)

        if not next_entries or is_item_locked:
            if pokemon.effective_stage < 3:
                pokemon.stage += 1
                self.game.story_manager.inventory["RARE_CANDY"] -= 1
                if self.game.story_manager.inventory["RARE_CANDY"] <= 0:
                    del self.game.story_manager.inventory["RARE_CANDY"]

                if self.game.assets.heal_sfx:
                    self.game.assets.heal_sfx.play()
                self.game.show_dialogue([f"{pokemon.display_name} grew stronger!", f"It is now a Stage {pokemon.effective_stage} Pokémon!"])
            else:
                self.game.show_dialogue([f"{pokemon.display_name} is already at its maximum potential!"])

            self.game.change_state(self)
            self.refresh_buttons()
            return

        self.game.story_manager.inventory["RARE_CANDY"] -= 1
        if self.game.story_manager.inventory["RARE_CANDY"] <= 0:
            del self.game.story_manager.inventory["RARE_CANDY"]

        next_entry = self.game.story_manager.pick_evolution_branch(next_entries)
        if "_" in next_entry:
            base_name, form_part = next_entry.rsplit("_", 1)
            next_form = form_part.lower()
        else:
            base_name = next_entry
            next_form = "normal"

        next_id = self.game.name_to_id.get(base_name.upper())

        if next_id:
            from src.states.systems import EvolutionState
            self.game.change_state(
                EvolutionState(
                    self.game, pokemon, next_id, slot_index, next_form=next_form, context="party",
                    return_state=self.previous_state
                )
            )

    def on_pokemon_select_pokeblock(self, slot_index):
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return
        p = party[slot_index]
        block = self.selected_item
        ate, lines = feed_pokeblock(p, block)
        if ate:
            inv = self.game.story_manager.inventory
            inv[block] -= 1
            if inv[block] <= 0:
                del inv[block]
            if self.game.assets.heal_sfx:
                self.game.assets.heal_sfx.play()
            # A Feebas that has grown enough only needed Beauty: it evolves right away.
            if p.name.upper() == "FEEBAS" and feebas_ready(p) and p.wins >= 15:
                milotic = self.game.name_to_id.get("MILOTIC")
                if milotic:
                    self.game.change_state(EvolutionState(
                        self.game, p, milotic, slot_index, context="party", return_state=self))
                    return
        self.game.change_state(self)
        self.refresh_buttons()
        self.game.show_dialogue(lines)

    def on_pokemon_select_potion(self, slot_index):
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return
        p = party[slot_index]

        if p.current_hp <= 0:
            self.game.show_dialogue([f"Potion has no effect on a fainted {p.display_name}!"])
        elif p.current_hp >= p.get_max_hp():
            self.game.show_dialogue([f"{p.display_name} is already at full health!"])
        else:
            heal = p.get_max_hp() // 2
            p.current_hp = min(p.get_max_hp(), p.current_hp + heal)
            self.game.story_manager.inventory["POTION"] -= 1
            if self.game.story_manager.inventory["POTION"] <= 0:
                del self.game.story_manager.inventory["POTION"]
            if self.game.assets.heal_sfx:
                self.game.assets.heal_sfx.play()

            if self.context == "battle":
                if p == self.previous_state.player_pokemon:
                    self.previous_state.player_hp = p.current_hp
                self.game.change_state(self.previous_state)
                self.previous_state.show_message([f"Healed {p.display_name}!"], callback=self.previous_state.on_item_used)
                return

        self.game.change_state(self)
        self.refresh_buttons()

    def on_pokemon_select_revive(self, slot_index):
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return
        p = party[slot_index]

        if p.current_hp > 0:
            self.game.show_dialogue([f"{p.display_name} is not fainted!"])
        else:
            p.current_hp = p.get_max_hp() // 2
            self.game.story_manager.inventory["REVIVE"] -= 1
            if self.game.story_manager.inventory["REVIVE"] <= 0:
                del self.game.story_manager.inventory["REVIVE"]
            if self.game.assets.heal_sfx:
                self.game.assets.heal_sfx.play()

            if self.context == "battle":
                if p == self.previous_state.player_pokemon:
                    self.previous_state.player_hp = p.current_hp
                self.game.change_state(self.previous_state)
                self.previous_state.show_message([f"{p.display_name} was revived!"], callback=self.previous_state.on_item_used)
                return

        self.game.change_state(self)
        self.refresh_buttons()

    def draw(self):
        self.game.screen.fill((40, 40, 60))

        page_title = self.pages[self.current_page]
        Utils.draw_text_outline(self.game.screen, page_title, self.game.assets.fonts["med"], WHITE, self.game.width//2, 50)

        if not self.item_buttons:
            Utils.draw_text_outline(self.game.screen, "No Items", self.game.assets.fonts["s_med"], GRAY, self.game.width//2, self.game.height//2)

        money_txt = f"${self.game.story_manager.money}"
        Utils.draw_text_outline(self.game.screen, money_txt, self.game.assets.fonts["small"], GOLD, self.game.width - 150, 50, outline_color=BLACK)

        self.game.ui_manager.draw(self.game.screen)


# [REF-0038: Pokedex UI]
class PokedexState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.current_tab = "normal"
        self.page = 0
        self.show_shinies_only = False
        self.full_dex = []
        self.sort_mode = "NUMBER"

        self.popup_active = False
        self.selected_pkmn_id = None
        self.popup_rect = pygame.Rect(0, 0, 180, 130)

        self.refresh_dex()

        tab_y = game.height * 0.18
        tab_h = 50

        self.btn_back = Button(
            rect=(30, 30, 140, 70),
            text="BACK",
            font=game.assets.fonts["small"],
            callback=self.go_back,
            bg_color=RED,
        )

        self.btn_cry = Button((0, 0, 160, 50), "CRY", game.assets.fonts["tiny"], self.play_selected_cry, bg_color=BLUE, visible=False)
        self.btn_area = Button((0, 0, 160, 50), "AREA", game.assets.fonts["tiny"], self.show_selected_area, bg_color=GREEN, visible=False)

        self.btn_shiny_toggle = Button(
            rect=(game.width - 250, 30, 220, 70),
            text="SHINIES",
            font=game.assets.fonts["small"],
            callback=self.toggle_shiny_filter,
            bg_color=BLUE,
        )
        self.btn_sort = Button(
            rect=(game.width - 250, 110, 220, 70),
            text="SORT: #",
            font=game.assets.fonts["small"],
            callback=self.toggle_sort,
            bg_color=GOLD
        )
        self.btn_tab_normal = Button(
            rect=(game.width * 0.1, tab_y, 200, tab_h),
            text="NORMAL",
            font=game.assets.fonts["tiny"],
            callback=lambda: self.set_tab("normal"),
        )
        self.btn_tab_mega = Button(
            rect=(self.btn_tab_normal.rect.right + 10, tab_y, 200, tab_h),
            text="MEGA",
            font=game.assets.fonts["tiny"],
            callback=lambda: self.set_tab("mega"),
        )
        self.btn_tab_gmax = Button(
            rect=(self.btn_tab_mega.rect.right + 10, tab_y, 200, tab_h),
            text="GMAX",
            font=game.assets.fonts["tiny"],
            callback=lambda: self.set_tab("gmax"),
        )
        self.btn_tab_alt = Button(
            rect=(self.btn_tab_gmax.rect.right + 10, tab_y, 200, tab_h),
            text="ALT",
            font=game.assets.fonts["tiny"],
            callback=lambda: self.set_tab("alt"),
        )
        self.btn_tab_boss = Button(
            rect=(self.btn_tab_alt.rect.right + 10, tab_y, 200, tab_h),
            text="BOSS",
            font=game.assets.fonts["tiny"],
            callback=lambda: self.set_tab("boss"),
        )
        self.btn_tab_unown = Button(
            rect=(self.btn_tab_boss.rect.right + 10, tab_y, 180, tab_h),
            text="UNOWN",
            font=game.assets.fonts["tiny"],
            callback=lambda: self.set_tab("unown"),
        )
        self.tab_buttons = [
            self.btn_tab_normal,
            self.btn_tab_mega,
            self.btn_tab_gmax,
            self.btn_tab_alt,
            self.btn_tab_boss,
            self.btn_tab_unown,
        ]

        total_tab_width = (
            sum(b.rect.width for b in self.tab_buttons)
            + (len(self.tab_buttons) - 1) * 10
        )
        start_x = (game.width - total_tab_width) / 2
        current_x = start_x
        for btn in self.tab_buttons:
            btn.rect.x = current_x
            current_x += btn.rect.width + 10

        self.btn_prev = pygame.Rect(game.width * 0.3, game.height * 0.85, 150, 70)
        self.btn_next = pygame.Rect(game.width * 0.6, game.height * 0.85, 150, 70)
        self.dex_btns = []

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.add_element(self.btn_back)
        self.game.ui_manager.add_element(self.btn_shiny_toggle)
        self.game.ui_manager.add_element(self.btn_sort)
        self.game.ui_manager.add_element(self.btn_cry)
        self.game.ui_manager.add_element(self.btn_area)
        for btn in self.tab_buttons:
            self.game.ui_manager.add_element(btn)

    def play_selected_cry(self):
        if self.selected_pkmn_id:
            try:
                cry_path = self.game.assets.get_cry(self.selected_pkmn_id)
                pygame.mixer.Sound(cry_path).play().set_volume(VOLUME)
            except Exception:
                pass
        self.hide_popup()

    def show_selected_area(self):
        if not self.selected_pkmn_id:
            return

        locations = []
        prog = self.game.loader.area_data.get("STORY_PROGRESSION", {})
        for area_key, data in prog.items():
            pool_name = data.get("wild_pool_percentages")
            if pool_name:
                pool = self.game.loader.area_data.get(pool_name, {})
                if str(self.selected_pkmn_id) in pool:
                    name = data.get("route_name", area_key.replace("KANTO_", "").replace("_", " ").title())
                    locations.append(name)

        msg = [f"Found in: {', '.join(locations)}" if locations else "Location unknown."]
        self.game.change_state(MapState(self.game, self, initial_message=msg))
        self.hide_popup()

    def hide_popup(self):
        self.popup_active = False
        self.btn_cry.set_visibility(False)
        self.btn_area.set_visibility(False)

    def toggle_sort(self):
        self.sort_mode = "NAME" if self.sort_mode == "NUMBER" else "NUMBER"
        self.btn_sort.text = f"SORT: {'A-Z' if self.sort_mode == 'NAME' else '#'}"
        self.refresh_dex()

    def refresh_dex(self):
        nown_id = self.game.loader.get_special_id("NOWN", 3025)

        if self.current_tab == "boss":
            source_data = self.game.data.data.get("defeated_bosses", {})
            self.full_dex = list(source_data.values())
        elif self.current_tab == "unown":
            self.full_dex = []
            caught_data = self.game.data.data.get("pokedex", {})
            forms = ["normal", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "question", "exclamation"]
            for f in forms:
                key = "201" if f == "normal" else f"201_{f}"
                is_caught = key in caught_data
                name = f"UNOWN-{f.upper()}" if f not in ["normal", "question", "exclamation"] else ("UNOWN-A" if f == "normal" else f"UNOWN-{'?' if f == 'question' else '!'}")
                self.full_dex.append({
                    "id": 201,
                    "status": 2 if is_caught else 0,
                    "shiny": caught_data.get(key, {}).get("shiny", False) if is_caught else False,
                    "form": f,
                    "name": name if is_caught else "???"
                })
            return
        elif self.current_tab == "normal":
            self.full_dex = []
            caught_data = self.game.data.data.get("pokedex", {})
            seen_ids = self.game.data.data.get("seen_pokemon", [])
            starting_region = self.game.story_manager.starting_region
            national_dex = self.game.story_manager.story_flags.get("unlocked_national_dex", False)

            # Each region the player has reached gets its own block: its generation's range plus
            # the later-gen evolutions obtainable there (dex_extra). Anything else shows once seen/caught.
            story = self.game.story_manager
            regions = [r for r, _ in story.get_region_starts()
                       if r == starting_region or story.story_flags.get(f"unlocked_{r.lower()}_badges")
                       or (national_dex and r in ("KANTO", "JOHTO"))]
            id_list = []
            for r in regions:
                cfg = story.get_region_start(r)
                lo, hi = cfg.get("dex_range", [1, 151])
                id_list += list(range(lo, hi + 1)) + cfg.get("dex_extra", [])
            caught_ids = {v['id'] for v in caught_data.values()}
            listed = set(id_list)
            id_list += sorted(i for i in (caught_ids | set(seen_ids))
                              if isinstance(i, int) and i <= 1025 and i not in listed)
            id_list = list(dict.fromkeys(id_list))

            for p_id in id_list:
                is_caught = False
                caught_entry = None

                for k, v in caught_data.items():
                    if v['id'] == p_id:
                        is_caught = True
                        caught_entry = v
                        break

                is_seen = p_id in seen_ids

                entry = {
                    "id": p_id,
                    "status": 0,
                    "shiny": False,
                    "form": "normal",
                    "name": "???"
                }

                if is_caught:
                    entry["status"] = 2
                    entry["name"] = self.game.assets.pokemon_names.get(str(p_id), f"#{p_id}").upper()
                    entry["shiny"] = any(v.get("shiny") for v in caught_data.values()
                                         if isinstance(v, dict) and v.get("id") == p_id)
                    entry["gmax"] = any(v.get("gmax") for v in caught_data.values()
                                        if isinstance(v, dict) and v.get("id") == p_id)
                elif is_seen:
                    entry["status"] = 1
                    entry["name"] = self.game.assets.pokemon_names.get(str(p_id), f"#{p_id}").upper()

                if self.show_shinies_only:
                    if not entry["shiny"]:
                        continue

                self.full_dex.append(entry)

            for k, v in caught_data.items():
                if v.get('id') == nown_id:
                    self.full_dex.append({
                        "id": nown_id,
                        "status": 2,
                        "shiny": v.get("shiny", False),
                        "form": "normal",
                        "name": "NOWN"
                    })
                    break

            def get_dex_sort_id(p):
                pid = p.get("id", 0)
                if isinstance(pid, int) and pid >= 2000:
                    mapping = self.game.loader.area_data.get("FORM_MAP", {}).get(str(pid))
                    if mapping:
                        return mapping.get("id", pid)
                return pid

            if self.sort_mode == "NUMBER":
                self.full_dex.sort(key=get_dex_sort_id)
            else:
                self.full_dex.sort(key=lambda x: (
                    0 if x['status'] == 2 else 1,
                    x.get("name", "ZZZ").upper() if x['status'] == 2 else get_dex_sort_id(x)
                ))

            nown = next((p for p in self.full_dex if p['id'] == nown_id), None)
            if nown:
                self.full_dex.remove(nown)
                self.full_dex.insert(0, nown)

            return
        else:
            source_data = self.game.data.data.get("pokedex", {})
            self.full_dex = [
                p for p in source_data.values()
                if p.get("form", "normal") == self.current_tab
                or (self.current_tab == "gmax" and p.get("gmax"))
            ]

        if self.show_shinies_only:
            self.full_dex = [p for p in self.full_dex if p.get("shiny")]

        if self.sort_mode == "NUMBER":
            self.full_dex.sort(key=lambda x: x.get("id", 0))
        else:
            self.full_dex.sort(key=lambda x: x.get("name", "ZZZ"))

    def set_tab(self, tab_name):
        self.current_tab = tab_name
        self.page = 0
        self.refresh_dex()

    def toggle_shiny_filter(self):
        self.show_shinies_only = not self.show_shinies_only
        self.page = 0
        self.refresh_dex()
        self.btn_shiny_toggle.bg_color = GOLD if self.show_shinies_only else BLUE

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.popup_active:
                    popup_hit = self.popup_rect.collidepoint(event.pos)
                    if not popup_hit:
                        self.hide_popup()
                    continue

                if self.btn_next.collidepoint(event.pos) and (self.page + 1) * 12 < len(self.full_dex):
                    self.page += 1
                elif self.btn_prev.collidepoint(event.pos) and self.page > 0:
                    self.page -= 1
                else:
                    for r, p_id in self.dex_btns:
                        if r.collidepoint(event.pos):
                            self.popup_active = True
                            self.selected_pkmn_id = p_id
                            self.popup_rect.topleft = (event.pos[0] + 10, event.pos[1] + 10)
                            if self.popup_rect.right > self.game.width:
                                self.popup_rect.right = event.pos[0] - 10

                            self.btn_cry.rect.topleft = (self.popup_rect.x + 10, self.popup_rect.y + 10)
                            self.btn_area.rect.topleft = (self.popup_rect.x + 10, self.popup_rect.y + 70)
                            self.btn_cry.set_visibility(True)
                            self.btn_area.set_visibility(True)
                            return

    def confirm_wipe(self):
        confirming = True
        while confirming:
            pygame.draw.rect(
                self.game.screen,
                BLACK,
                (
                    self.game.width // 4,
                    self.game.height // 3,
                    self.game.width // 2,
                    self.game.height // 3,
                ),
            )
            Utils.draw_text_outline(
                self.game.screen,
                self.game.assets.get_text("wipe_data_q"),
                self.game.assets.fonts["small"],
                RED,
                self.game.width // 2,
                self.game.height // 2 - 30,
            )
            by = pygame.Rect(
                self.game.width // 2 - 110, self.game.height // 2 + 20, 100, 60
            )
            bn = pygame.Rect(
                self.game.width // 2 + 10, self.game.height // 2 + 20, 100, 60
            )
            pygame.draw.rect(self.game.screen, RED, by)
            pygame.draw.rect(self.game.screen, GREEN, bn)
            Utils.draw_text_outline(
                self.game.screen,
                self.game.assets.get_text("yes"),
                self.game.assets.fonts["tiny"],
                WHITE,
                by.centerx,
                by.centery,
            )
            Utils.draw_text_outline(
                self.game.screen,
                self.game.assets.get_text("no"),
                self.game.assets.fonts["tiny"],
                WHITE,
                bn.centerx,
                bn.centery,
            )
            pygame.display.flip()
            for e in pygame.event.get():
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if by.collidepoint(e.pos):
                        if self.game.assets.heal_sfx:
                            self.game.assets.heal_sfx.play()
                        self.game.data.wipe_data()
                        self.refresh_dex()
                        confirming = False
                    if bn.collidepoint(e.pos):
                        confirming = False

    def update(self):
        pass

    def draw(self):
        screen = self.game.screen
        width, height = self.game.width, self.game.height
        screen.fill(WHITE)
        pygame.draw.circle(screen, RED, (width // 2, height // 2), width)
        pygame.draw.rect(screen, WHITE, (0, height // 2, width, height // 2))
        pygame.draw.line(screen, BLACK, (0, height // 2), (width, height // 2), 20)
        pygame.draw.circle(screen, BLACK, (width // 2, height // 2), 120)
        pygame.draw.circle(screen, WHITE, (width // 2, height // 2), 90)

        Utils.draw_text_outline(
            screen,
            "POKEDEX",
            self.game.assets.fonts["med"],
            BLACK,
            width // 2,
            height * 0.06,
            outline_color=WHITE,
        )

        total_caught = len({v['id'] for v in self.game.data.data["pokedex"].values() if isinstance(v, dict) and 'id' in v})
        Utils.draw_text_outline(
            screen,
            f"CAUGHT: {total_caught}",
            self.game.assets.fonts["s_med"],
            BLACK,
            width // 2,
            height * 0.12,
            outline_color=WHITE,
        )

        cols, rows = 4, 3
        per_page = cols * rows
        start_idx = self.page * per_page
        current_view = self.full_dex[start_idx: start_idx + per_page]

        for btn in self.tab_buttons:
            btn.bg_color = (
                GREEN
                if btn.callback.__closure__[0].cell_contents == self.current_tab
                else BLUE
            )

        self.dex_btns = []
        for i in range(per_page):
            c, r = i % cols, i // cols
            x = width * 0.15 + (c * (width * 0.23))
            y = height * 0.32 + (r * (height * 0.20))
            rect = pygame.Rect(x - 60, y - 60, 120, 120)
            pygame.draw.rect(screen, (220, 220, 220), rect, border_radius=10)
            pygame.draw.rect(screen, BLACK, rect, 3, border_radius=10)

            if i < len(current_view):
                p_entry = current_view[i]
                status = p_entry.get("status", 2)
                nown_id = self.game.loader.get_special_id("NOWN", 3025)

                id_num = p_entry['id']
                prefix = ""
                if isinstance(id_num, int) and id_num >= 2000:
                    mapping = self.game.loader.area_data.get("FORM_MAP", {}).get(str(id_num))
                    if mapping:
                        id_num = mapping.get("id", id_num)
                        prefix = f"{p_entry.get('form', '')} "

                display_id = "???" if p_entry['id'] == nown_id else f"{prefix}#{id_num}"

                Utils.draw_text_outline(
                    screen,
                    display_id,
                    self.game.assets.fonts["tiny"],
                    BLACK,
                    rect.right - 20,
                    rect.top + 15,
                    outline_color=WHITE,
                )
                Utils.draw_text_outline(
                    screen,
                    p_entry["name"].upper(),
                    self.game.assets.fonts["tiny"],
                    BLACK,
                    rect.centerx,
                    rect.bottom + 20,
                    outline_color=WHITE,
                )

                if status > 0:
                    icon = self.game.assets.get_pokemon_image(
                        p_entry["id"], p_entry.get("form", "normal"), p_entry.get("shiny", False)
                    )
                    icon = pygame.transform.scale(icon, (100, 100))

                    if status == 1:
                        # Grey out
                        icon.fill((40, 40, 40), special_flags=pygame.BLEND_RGB_MULT)

                    screen.blit(icon, icon.get_rect(center=rect.center))

                    if p_entry.get("shiny"):
                        Utils.draw_star(screen, GOLD, (rect.right - 15, rect.top + 15), 12)
                    if p_entry.get("gmax") and status == 2:
                        _draw_gmax_tag(screen, self.game.assets.fonts["tiny"], rect.left + 6, rect.bottom - 24)

                    self.dex_btns.append((rect, p_entry["id"]))
                else:
                    Utils.draw_text_outline(
                        screen,
                        "?",
                        self.game.assets.fonts["big"],
                        LIGHT_GRAY,
                        rect.centerx,
                        rect.centery,
                    )
            else:
                Utils.draw_text_outline(
                    screen,
                    "?",
                    self.game.assets.fonts["med"],
                    LIGHT_GRAY,
                    rect.centerx,
                    rect.centery,
                )

        self.game.ui_manager.draw(screen)
        self.btn_shiny_toggle.bg_color = GOLD if self.show_shinies_only else BLUE

        pygame.draw.rect(screen, BLACK, self.btn_prev, border_radius=15)
        Utils.draw_text_outline(
            screen,
            "<",
            self.game.assets.fonts["s_med"],
            WHITE,
            self.btn_prev.centerx,
            self.btn_prev.centery,
        )

        pygame.draw.rect(screen, BLACK, self.btn_next, border_radius=15)
        Utils.draw_text_outline(
            screen,
            ">",
            self.game.assets.fonts["s_med"],
            WHITE,
            self.btn_next.centerx,
            self.btn_next.centery,
        )


# [REF-0039: Game Over State]
class GameOverState(GameState):
    def __init__(self, game):
        super().__init__(game)
        mid_x = game.width // 2
        self.btn_retry = Button(
            rect=(mid_x - 200, game.height * 0.60, 400, 80),
            text="RETRY",
            font=game.assets.fonts["s_med"],
            callback=self.retry_game,
            bg_color=GREEN,
        )
        mid_x = game.width // 2
        self.btn_reset = Button(
            rect=(mid_x - 200, game.height * 0.72, 400, 80),
            text="RESET STREAK",
            font=game.assets.fonts["s_med"],
            callback=self.reset_streak,
            bg_color=DARK_RED,
        )
        mid_x = game.width // 2
        self.btn_exit = Button(
            rect=(mid_x - 200, game.height * 0.84, 400, 80),
            text="EXIT GAME",
            font=game.assets.fonts["s_med"],
            callback=self.exit_game,
            bg_color=RED,
        )

    def start(self):
        self.game.ui_manager.add_element(self.btn_retry)
        self.game.ui_manager.add_element(self.btn_reset)
        self.game.ui_manager.add_element(self.btn_exit)

    def handle_events(self, events):
        pass

    def retry_game(self):
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.play()
        self.game.story_manager.load_last_checkpoint(self.game)

    def reset_streak(self):
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.play()
        self.game.data.set_high_score(0)
        self.game.data.save()
        from src.states.overworld import PlayState
        self.game.change_state(PlayState(self.game))

    def exit_game(self):
        pygame.quit()
        sys.exit()

    def update(self):
        pass

    def draw(self):
        screen = self.game.screen
        screen.fill(BLACK)
        if self.game.assets.go_img:
            screen.blit(
                self.game.assets.go_img,
                self.game.assets.go_img.get_rect(
                    center=(self.game.width // 2, self.game.height * 0.35)
                ),
            )
        Utils.draw_text_outline(
            screen,
            "GAME OVER",
            self.game.assets.fonts["big"],
            RED,
            self.game.width // 2,
            self.game.height * 0.1,
        )
        self.game.ui_manager.draw(screen)


# [REF-0040: Badge Case UI]
class BadgeCaseState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.earned_badges = game.story_manager.badges

        story = game.story_manager
        starts = story.get_region_starts()
        self.unlocked_regions = [
            r for r, _ in starts
            if story.story_flags.get(f"unlocked_{r.lower()}_badges") or story.badges.get(r)
        ] or [story.starting_region]

        home = game.story_manager.starting_region
        self.unlocked_regions.sort(key=lambda r: 0 if r == home else 1)

        self.current_page_idx = 0

        self.btn_back = Button(
            rect=(30, 30, 140, 70),
            text="BACK",
            font=game.assets.fonts["small"],
            callback=self.go_back,
            bg_color=RED,
        )

        cy = game.height // 2
        self.btn_prev = Button((30, cy - 30, 60, 60), "<", game.assets.fonts["med"], self.prev_page)
        self.btn_next = Button((game.width - 90, cy - 30, 60, 60), ">", game.assets.fonts["med"], self.next_page)

        self.region_maps = {
            "KANTO": {
                "BOULDER": 1, "CASCADE": 2, "THUNDER": 3, "RAINBOW": 4,
                "SOUL": 5, "MARSH": 6, "VOLCANO": 7, "EARTH": 8
            },
            "JOHTO": {
                "ZEPHYR": 1, "HIVE": 2, "PLAIN": 3, "FOG": 4,
                "STORMBADGE": 5, "MINERAL": 6, "GLACIER": 7, "RISING": 8
            },
            "HOENN": {
                "STONE": 1, "KNUCKLE": 2, "DYNAMO": 3, "HEAT": 4,
                "BALANCE": 5, "FEATHER": 6, "MIND": 7, "RAIN": 8
            }
        }

        self.badge_sprites = {"KANTO": {}, "JOHTO": {}, "HOENN": {}}
        for i in range(1, 9):
            k_img = game.assets.get_badge_image(i, "kanto")
            if k_img:
                self.badge_sprites["KANTO"][i] = pygame.transform.scale(k_img, (100, 100))

            j_img = game.assets.get_badge_image(i, "johto")
            if j_img:
                self.badge_sprites["JOHTO"][i] = pygame.transform.scale(j_img, (100, 100))

            h_img = game.assets.get_badge_image(i, "hoenn")
            if h_img:
                self.badge_sprites["HOENN"][i] = pygame.transform.scale(h_img, (100, 100))

        for region, cfg in starts:
            if region in self.region_maps:
                continue
            badges = story.get_region_gym_badges(region)
            self.region_maps[region] = {b: i + 1 for i, b in enumerate(badges)}
            numbered = cfg.get("badge_images", [])
            sprites = {}
            for i, badge in enumerate(badges, start=1):
                img = None
                if i <= len(numbered):
                    path = Utils.get_actual_path(game.assets.badges_dir, f"{numbered[i - 1]}.png")
                    if os.path.exists(path):
                        img = pygame.image.load(path).convert_alpha()
                sprites[i] = (pygame.transform.scale(img, (100, 100)) if img
                              else self._placeholder_badge(badge))
            self.badge_sprites[region] = sprites

    def _placeholder_badge(self, badge_name):
        surf = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.circle(surf, (200, 170, 60), (50, 50), 46)
        pygame.draw.circle(surf, (120, 90, 20), (50, 50), 46, 4)
        label = badge_name.replace("_", " ")[:8]
        Utils.draw_text_outline(surf, label, self.game.assets.fonts["tiny"], WHITE, 50, 50)
        return surf

    def prev_page(self):
        if len(self.unlocked_regions) > 1:
            self.current_page_idx = (self.current_page_idx - 1) % len(self.unlocked_regions)

    def next_page(self):
        if len(self.unlocked_regions) > 1:
            self.current_page_idx = (self.current_page_idx + 1) % len(self.unlocked_regions)

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.add_element(self.btn_back)
        if len(self.unlocked_regions) > 1:
            self.game.ui_manager.add_element(self.btn_prev)
            self.game.ui_manager.add_element(self.btn_next)

    def handle_events(self, events):
        pass

    def update(self):
        pass

    def draw(self):
        screen = self.game.screen
        width, height = self.game.width, self.game.height

        region = self.unlocked_regions[self.current_page_idx] if self.unlocked_regions else "KANTO"

        bg_colors = {"KANTO": DARK_RED, "JOHTO": (15, 35, 85), "HOENN": (20, 80, 40),
                     "SINNOH": (60, 40, 90), "UNOVA": (30, 30, 30), "KALOS": (20, 60, 100),
                     "ALOLA": (110, 70, 20), "GALAR": (90, 20, 50), "PALDEA": (120, 40, 20)}
        screen.fill(bg_colors.get(region, (40, 40, 40)))

        case_rect = pygame.Rect(width * 0.1, height * 0.1, width * 0.8, height * 0.8)
        pygame.draw.rect(screen, (50, 50, 50), case_rect, border_radius=20)
        Utils.draw_text_outline(
            screen,
            f"{region} BADGE CASE",
            self.game.assets.fonts["med"],
            WHITE,
            width // 2,
            height * 0.05,
        )

        grid_rect = case_rect.inflate(-40, -60)
        cell_w = grid_rect.width / 4
        cell_h = grid_rect.height / 2

        badge_map = self.region_maps.get(region, {})
        for i in range(1, max(badge_map.values(), default=8) + 1):
            row = (i - 1) // 4
            col = (i - 1) % 4

            cx = grid_rect.x + (col + 0.5) * cell_w
            cy = grid_rect.y + (row + 0.5) * cell_h + 10

            sprite = self.badge_sprites.get(region, {}).get(i)

            if sprite:
                regional_badges = self.earned_badges.get(region, [])
                earned = any(badge_map.get(b_name) == i for b_name in regional_badges)

                draw_sprite = sprite.copy()
                if not earned:
                    draw_sprite.fill((100, 100, 100), special_flags=pygame.BLEND_RGB_MULT)
                    draw_sprite.set_alpha(100)

                sprite_rect = draw_sprite.get_rect(center=(cx, cy - 20))
                screen.blit(draw_sprite, sprite_rect)

                color = WHITE if earned else GRAY
                Utils.draw_text_outline(screen, f"#{i}", self.game.assets.fonts["tiny"], color, cx, cy + 40)

        self.game.ui_manager.draw(screen)


# [REF-0041: Evolution Logic]
class EvolutionState(GameState):
    def __init__(
        self, game, pokemon_to_evolve, evolution_id, team_index, next_form="normal", context="party", return_state=None, consume_catch_count=False
    ):
        super().__init__(game)
        self.consume_catch_count = consume_catch_count
        self.pokemon = pokemon_to_evolve
        self.evolution_id = evolution_id
        self.team_index = team_index
        self.return_state = return_state
        self.context = context
        self.next_form = next_form
        self.phase = "DECISION"
        self.on_line_finish = {}
        self.options_buttons = {}

        self.timer = 0
        self.scale = 1.0
        self.alpha = 255
        self.evolved_pokemon_obj = None
        self.original_name = pokemon_to_evolve.name
        self.is_hatching = (self.original_name == "Mystery Egg")

        box = Utils.get_full_dialogue_rect(game)
        btn_w, btn_h = 120, 60
        self.btn_yes = Button(
            rect=(box.right - 280, box.centery - 30, btn_w, btn_h),
            text="YES",
            font=game.assets.fonts["small"],
            callback=self.evolve_yes,
            bg_color=GREEN,
            visible=False,
        )
        self.btn_no = Button(
            rect=(box.right - 140, box.centery - 30, btn_w, btn_h),
            text="NO",
            font=game.assets.fonts["small"],
            callback=self.evolve_no,
            bg_color=RED,
            visible=False,
        )

    def evolve_yes(self):
        self.phase = "START"
        self.btn_yes.set_visibility(False)
        self.btn_no.set_visibility(False)
        self.timer = 60
        if self.pokemon.cry:
            self.pokemon.cry.play()

    def evolve_no(self):
        self._return()

    def start(self):
        self.game.ui_manager.add_element(self.btn_yes)
        self.game.ui_manager.add_element(self.btn_no)
        if self.phase == "DECISION":
            self.btn_yes.set_visibility(True)
            self.btn_no.set_visibility(True)

    def handle_events(self, events):
        pass

    def update(self):
        if self.phase == "DECISION":
            return

        self.timer -= 1

        if self.phase == "START" and self.timer <= 0:
            self.phase = "GROW"
            self.timer = 50

        elif self.phase == "GROW":
            self.scale += 0.05
            self.alpha = max(0, self.alpha - 10)
            if self.timer <= 0:
                self.phase = "FLASH"
                self.timer = 20
                raw_data = self.game.loader.fetch_specific(
                    self.evolution_id, form=self.next_form,
                    is_shiny=self.pokemon.is_shiny
                )
                self.evolved_pokemon_obj = Pokemon(
                    raw_data, self.game.assets, size_mult=1.5
                )
                self.evolved_pokemon_obj.wins = 0
                # What the Pokémon has earned stays with it through evolution.
                for attr in ("condition", "sheen", "ribbons", "gmax_factor", "caught_region"):
                    if hasattr(self.pokemon, attr):
                        setattr(self.evolved_pokemon_obj, attr, getattr(self.pokemon, attr))

        elif self.phase == "FLASH":
            if self.timer <= 0:
                self.phase = "REVEAL"
                self.timer = 60
                if self.evolved_pokemon_obj and self.evolved_pokemon_obj.cry:
                    self.evolved_pokemon_obj.cry.play()
                self.scale = 3.0
                self.alpha = 0

        elif self.phase == "REVEAL":
            self.scale = max(1.0, self.scale - 0.1)
            self.alpha = min(255, self.alpha + 15)
            if self.timer <= 0:
                self.phase = "END"
                self.timer = 50
                if self.evolved_pokemon_obj:
                    if self.context == "pc":
                        self.game.story_manager.pc_pokemon[self.team_index] = self.evolved_pokemon_obj
                    else:
                        self.game.story_manager.player_team[self.team_index] = self.evolved_pokemon_obj

                    self.game.data.add_pokemon(self.evolved_pokemon_obj)

                    if self.evolved_pokemon_obj.is_shiny:
                        non_shiny_raw = self.game.loader.fetch_specific(
                            self.evolved_pokemon_obj.id,
                            form=self.evolved_pokemon_obj.form,
                            is_shiny=False
                        )
                        non_shiny_pokemon = Pokemon(non_shiny_raw, self.game.assets, size_mult=0.1)
                        self.game.data.add_pokemon(non_shiny_pokemon)

                    if self.consume_catch_count:
                        current_count = self.game.story_manager.catch_counts.get(self.pokemon.id, 0)
                        if current_count >= 5:
                            self.game.story_manager.catch_counts[self.pokemon.id] = current_count - 5

        elif self.phase == "END" and self.timer <= 0:
            self._return()

    def _return(self):
        pygame.event.clear()
        if self.return_state:
            if hasattr(self.return_state, "is_resuming"):
                self.return_state.is_resuming = True
            if hasattr(self.return_state, "show_progression_menu"):
                self.return_state.show_progression_menu()
            self.game.change_state(self.return_state)
        else:
            self.game.change_state(self.game.states["play"])

    def draw(self):
        self.game.screen.fill(BLACK)
        center_x, center_y = self.game.width // 2, self.game.height // 2

        if self.phase == "DECISION":
            img = self.pokemon.image
            rect = img.get_rect(center=(center_x, center_y))
            self.game.screen.blit(img, rect)

            box_rect = Utils.get_full_dialogue_rect(self.game)
            Utils.draw_classic_panel(self.game.screen, *box_rect)

            text_rect = pygame.Rect(
                box_rect.left, box_rect.top, box_rect.width / 2, box_rect.height
            )
            if self.is_hatching:
                text = f"What? The {self.original_name} is hatching!"
            else:
                text = f"What? {self.original_name} is evolving!"

            Utils.draw_multiline_text(
                self.game.screen,
                text,
                self.game.assets.fonts["s_med"],
                WHITE,
                text_rect.centerx,
                text_rect.centery,
                max_width=text_rect.width - 40,
                center=True,
                outline_color=BLACK,
            )
            self.game.ui_manager.draw(self.game.screen)
            return

        if self.phase in ["START", "GROW"]:
            img = pygame.transform.rotozoom(self.pokemon.image, 0, self.scale)
            img.set_alpha(self.alpha)
            rect = img.get_rect(center=(center_x, center_y))
            self.game.screen.blit(img, rect)

            msg = "Hatching..." if self.is_hatching else self.game.assets.get_text("evolving", name=self.original_name)
            if isinstance(msg, list):
                msg = " ".join(msg)

            Utils.draw_text_outline(
                self.game.screen,
                msg,
                self.game.assets.fonts["med"],
                WHITE,
                center_x,
                self.game.height * 0.8,
            )

        elif self.phase == "FLASH":
            self.game.screen.fill(WHITE)

        elif self.phase in ["REVEAL", "END"]:
            if self.evolved_pokemon_obj:
                img = pygame.transform.rotozoom(
                    self.evolved_pokemon_obj.image, 0, self.scale
                )
                img.set_alpha(self.alpha)
                rect = img.get_rect(center=(center_x, center_y))
                self.game.screen.blit(img, rect)

                if self.is_hatching:
                    text = f"Congratulations! The Egg hatched into {self.evolved_pokemon_obj.name}!"
                else:
                    text = self.game.assets.get_text(
                        "evolved",
                        old_name=self.original_name,
                        new_name=self.evolved_pokemon_obj.name,
                    )
                if isinstance(text, list):
                    text = " ".join(text)

                Utils.draw_multiline_text(
                    self.game.screen,
                    text,
                    self.game.assets.fonts["s_med"],
                    WHITE,
                    center_x,
                    self.game.height * 0.8,
                    max_width=self.game.width - 40,
                )


# [REF-0022: Pokemon Detail View]
class PokemonDetailState(GameState):
    def __init__(self, game, pokemon, previous_state):
        super().__init__(game)
        self.pokemon = pokemon
        self.previous_state = previous_state
        self.btn_back = Button(
            (game.width - 140, game.height - 80, 120, 60),
            "BACK",
            game.assets.fonts["small"],
            self.go_back,
            bg_color=RED
        )

    def go_back(self):
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.elements.clear()
        self.game.ui_manager.add_element(self.btn_back)

    def handle_events(self, events):
        pass

    def update(self):
        pass

    def draw(self):
        self.game.screen.fill((40, 40, 60))
        Utils.draw_text_outline(self.game.screen, "SUMMARY", self.game.assets.fonts["big"], WHITE, self.game.width//2, 50)

        if self.pokemon.image:
            img = pygame.transform.scale(self.pokemon.image, (250, 250))
            self.game.screen.blit(img, (self.game.width//2 - 125, 120))
        if getattr(self.pokemon, "gmax_factor", False):
            _draw_gmax_tag(self.game.screen, self.game.assets.fonts["small"], self.game.width // 2 + 110, 130)

        info_x = 50
        y = 400
        font = self.game.assets.fonts["med"]

        texts = [
            f"Name: {self.pokemon.display_name}",
            f"Stage: {self.pokemon.effective_stage}" + (
                f"  (growth {self.pokemon.sub_stage[0]}/{self.pokemon.sub_stage[1]})"
                if self.pokemon.sub_stage else "  (fully grown)"),
            f"HP: {self.pokemon.current_hp}/{self.pokemon.get_max_hp()}",
            f"Types: {'/'.join(self.pokemon.types)}"
        ]
        if getattr(self.pokemon, "gmax_factor", False):
            texts.append("Gigantamax Factor: YES")
        from src.world import seasons
        season_form = seasons.form_name(self.pokemon.id)
        if season_form:
            texts.append(f"Coat: {season_form}")

        catch_count = self.game.story_manager.catch_counts.get(self.pokemon.id, 0)
        catch_str = f"Catches Banked: {catch_count}/5"

        texts.append(catch_str)

        for t in texts:
            Utils.draw_multiline_text(
                self.game.screen, t, font, WHITE,
                info_x, y,
                max_width=self.game.width - 100,
                center=False,
                align="left"
            )
            y += 50

        self._draw_condition()
        self.game.ui_manager.draw(self.game.screen)

    def _draw_condition(self):
        """Contest condition bars, Sheen and ribbon count (right side of the summary)."""
        p = self.pokemon
        cond = getattr(p, "condition", None)
        if not cond:
            return
        screen, font = self.game.screen, self.game.assets.fonts["tiny"]
        x, y, bar_w = self.game.width - 430, 130, 260
        Utils.draw_text_outline(screen, "CONDITION", self.game.assets.fonts["small"], WHITE, x + 190, y - 30)
        rows = [(c.title(), cond.get(c, 0), CATEGORY_COLOR[c]) for c in CATEGORIES]
        rows.append(("Sheen", getattr(p, "sheen", 0), (200, 200, 200)))
        for label, value, color in rows:
            screen.blit(font.render(label, True, WHITE), (x, y))
            bar = pygame.Rect(x + 110, y + 2, bar_w, 16)
            pygame.draw.rect(screen, BLACK, bar, border_radius=6)
            fill = bar.copy()
            fill.width = int(bar_w * min(value, MAX_CONDITION) / MAX_CONDITION)
            if fill.width:
                pygame.draw.rect(screen, color, fill, border_radius=6)
            y += 30
        ribbons = getattr(p, "ribbons", [])
        screen.blit(font.render(f"Ribbons: {len(ribbons)}", True, GOLD), (x, y + 6))
        if p.name.upper() == "FEEBAS" and not feebas_ready(p):
            screen.blit(font.render(f"Needs Beauty {FEEBAS_BEAUTY} to evolve", True, WHITE), (x, y + 36))


# [REF-0061: Bike Shop State]
class BikeShopState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.bg = self._load_bg(game)
        self.clerk_sprite = game.assets.get_trainer_image("supernerd.png")

        inv = self.game.story_manager.inventory
        has_voucher = inv.get("BIKE_VOUCHER", 0) > 0
        has_bike = inv.get("BICYCLE", 0) > 0

        if has_bike:
            lines = ["How's that bike treating you?", "Those Miracle Cycles are top of the line!"]
        elif has_voucher:
            lines = [
                "Is that from Misty? Oh wow, she's pretty...",
                "Umm, forget what I said about it being dangerous.",
                "Just wear a helmet or whatever.",
                "Just tell Misty I gave you a bike. And that my arms look bigger. Please.",
                "You received the BICYCLE!"
            ]
            inv["BICYCLE"] = 1
            inv["BIKE_VOUCHER"] -= 1
            if self.game.assets.heal_sfx:
                self.game.assets.heal_sfx.play()
        else:
            lines = [
                "I'm out of normal bikes right now.",
                "I have a dangerous one, but only a strong trainer could handle the speed.",
                "You need a BIKE VOUCHER to get one."
            ]

        self.dialogue_box = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(game),
            lines,
            game.assets.fonts["med"],
            callback=self.go_back
        )

    def _load_bg(self, game):
        path = os.path.join(game.assets.kanto_backgrounds_dir, "cerulean_bike_shop.png")
        box_top = Utils.get_full_dialogue_rect(game).top
        if os.path.exists(path):
            return pygame.transform.scale(pygame.image.load(path).convert(), (game.width, box_top))
        bg = pygame.Surface((game.width, box_top))
        bg.fill((30, 30, 50))
        return bg

    def go_back(self):
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)

    def handle_events(self, events):
        pass

    def update(self):
        self.dialogue_box.update()

    def draw(self):
        self.game.screen.fill(BLACK)
        self.game.screen.blit(self.bg, (0, 0))
        if self.clerk_sprite:
            rect = self.clerk_sprite.get_rect(center=(self.game.width//2, self.game.height*0.45))
            self.game.screen.blit(self.clerk_sprite, rect)
        self.dialogue_box.draw(self.game.screen)


# [REF-0062: Celadon Game Corner System]
class GameCornerState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.bg = self._load_bg(game)
        self.npc_sprite = game.assets.get_trainer_image("gentleman.png")

        self.flags = self.game.story_manager.story_flags
        self.cleared = self.flags.get("game_corner_cleared", False)
        self.rocket_progress = self.game.story_manager.story_flags.get("game_corner_rocket_progress", 0)

        self.phase = "START"

        has_case = self.game.story_manager.inventory.get("COIN_CASE", 0) > 0
        if has_case:
            lines = ["Is that a Coin Case? That means you have money!",
                     "Come on in, kid, have fun!",
                     "Would you like to play PokeMath Infinite?"]
        else:
            lines = ["This place is too dangerous for kids.",
                     "Come back when you have a COIN CASE!"]
            self.phase = "DENIED"

        self.dialogue_box = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(game),
            lines,
            game.assets.fonts["med"],
            visible=True,
            callback=self.go_back if not has_case else None
        )

        self.btn_yes = Button((0, 0, 0, 0), "YES", game.assets.fonts["small"],
                              self.start_infinite, bg_color=GREEN,
                              visible=False, autosize=False)
        self.btn_no = Button((0, 0, 0, 0), "NO", game.assets.fonts["small"],
                             self.decline_infinite, bg_color=RED,
                             visible=False, autosize=False)
        self.menu_buttons = []

    def _load_bg(self, game):
        path = os.path.join(game.assets.kanto_backgrounds_dir,
                            "celadon_game_corner.png")
        box_top = Utils.get_full_dialogue_rect(game).top
        if os.path.exists(path):
            return pygame.transform.scale(pygame.image.load(path).convert(),
                                          (game.width, box_top))
        bg = pygame.Surface((game.width, box_top))
        bg.fill((20, 20, 40))
        return bg

    def start_infinite(self):
        self.game.change_state(PokeMathInfiniteState(self.game, self))

    def decline_infinite(self):
        self.show_main_menu()

    def show_main_menu(self):
        self.phase = "MAIN_MENU"
        self.dialogue_box.reset("What would you like to do?")
        self.btn_yes.set_visibility(False)
        self.btn_no.set_visibility(False)

        options = [
            ("CASH IN", self.open_shop),
            ("PLAY AGAIN", self.start_infinite),
            ("LEAVE", self.go_back)
        ]
        # ARCHITECT: Add Slot Machine option
        options.insert(0, ("PLAY SLOTS", self.start_slot_machine))

        is_celadon = self.game.story_manager.current_area_key == "CELADON_CITY"
        if is_celadon and not self.cleared:
            options.insert(0, ("STAIRS", self.check_stairs))

        self.clear_menu()
        btn_w, btn_h = 200, 60
        start_x = self.game.width // 2 - (len(options) * (btn_w + 20)) // 2
        for i, (text, cb) in enumerate(options):
            btn = Button(
                (start_x + i * (btn_w + 20), self.game.height - 150,
                    btn_w, btn_h), text, self.game.assets.fonts["tiny"],
                cb, autosize=False)
            self.menu_buttons.append(btn)
            self.game.ui_manager.add_element(btn)

    def start_slot_machine(self):
        self.clear_menu()
        self.game.change_state(SlotMachineState(self.game, self))

    def open_shop(self):
        self.clear_menu()
        self.game.change_state(GameCornerShopState(self.game, self))

    def check_stairs(self):
        self.clear_menu()
        self.phase = "STAIRS_PROMPT"
        self.dialogue_box.reset(["There are stairs leading down behind a poster...", "Investigate?"])
        self.btn_yes.callback = self.start_rocket_gauntlet
        self.btn_no.callback = self.show_main_menu
        self.btn_yes.set_visibility(True)
        self.btn_no.set_visibility(True)

    def start_rocket_gauntlet(self):
        self.btn_yes.set_visibility(False)
        self.btn_no.set_visibility(False)
        self.next_rocket_battle()

    def next_rocket_battle(self):
        if self.rocket_progress >= 4:
            self.give_porygon()
            return

        rocket_pool = self.game.loader.area_data.get("TEAM_ROCKET_POOL", [19, 23, 52])
        team_ids = [random.choice(rocket_pool) for _ in range(2 + (self.rocket_progress // 2))]
        opponent_team = [Pokemon(self.game.loader.fetch_specific(pid), self.game.assets, size_mult=3.125) for pid in team_ids]

        sprite_name = "rocket_grunt_m.png" if random.random() < 0.5 else "rocket_grunt_f.png"
        trainer_sprite = self.game.assets.get_trainer_image(sprite_name)

        class RocketGauntletBattle(TrainerBattleState):
            def exit_battle(self):
                self.game.story_manager.story_flags["game_corner_rocket_progress"] = self.game.story_manager.story_flags.get("game_corner_rocket_progress", 0) + 1
                state = GameCornerState(self.game, self.game.states.get("city"))
                state.rocket_progress = self.game.story_manager.story_flags["game_corner_rocket_progress"]
                state.phase = "VICTORY_SEQ"
                self.game.change_state(state)

        self.game.change_state(TrainerIntroState(self.game, trainer_sprite, "You shouldn't be here!",
                                                 RocketGauntletBattle(self.game, opponent_team, trainer_sprite=trainer_sprite, trainer_class="ROCKET", trainer_name="GRUNT", battle_type="indoor", area_name="CELADON_CITY")))

    def give_porygon(self):
        self.game.story_manager.story_flags["game_corner_cleared"] = True
        self.cleared = True
        porygon = Pokemon(self.game.loader.fetch_specific(137), self.game.assets, size_mult=2.5)
        msg = ["You cleared out Team Rocket!", "In the chaos, you found a PORYGON!", "You rescued PORYGON!"]
        if len(self.game.story_manager.player_team) < 6:
            self.game.story_manager.player_team.append(porygon)
        else:
            self.game.story_manager.pc_pokemon.append(porygon)
            msg.append("PORYGON was sent to BILL'S PC.")
        self.game.data.add_pokemon(porygon)
        self.game.data.save()
        self.dialogue_box.reset(msg)
        self.dialogue_box.callback = self.show_main_menu

    def handle_infinite_result(self, score):
        reward = score * 50
        self.game.story_manager.money += reward
        self.phase = "REWARD"
        self.dialogue_box.reset([f"Game Over! Your score: {score}", f"You received a reward of ${reward}!"])
        self.dialogue_box.callback = self.show_main_menu

    def clear_menu(self):
        for btn in self.menu_buttons:
            if btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)
        self.menu_buttons = []

    def go_back(self):
        self.clear_menu()
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        self.game.ui_manager.add_element(self.btn_yes)
        self.game.ui_manager.add_element(self.btn_no)
        if self.phase == "VICTORY_SEQ":
            self.on_rocket_victory()

    def on_rocket_victory(self):
        if self.rocket_progress >= 4:
            self.give_porygon()
        else:
            self.dialogue_box.reset([f"Defeated Rocket Grunt {self.rocket_progress}!", "Another one is approaching!"])
            self.dialogue_box.callback = self.next_rocket_battle

    def handle_events(self, events):
        for event in events:
            self.dialogue_box.handle_event(event)

    def update(self):
        self.dialogue_box.update()

        # ARCHITECT: Only show Yes/No buttons when the question is actually reached in the dialogue
        if self.phase == "START":
            # Start dialogue has 3 lines; the question is the 3rd line (index 2)
            if self.dialogue_box.current_line == 2 and self.dialogue_box.is_waiting_for_click:
                self.btn_yes.set_visibility(True)
                self.btn_no.set_visibility(True)
        elif self.phase == "STAIRS_PROMPT":
            # Stairs prompt has 2 lines; the question is the 2nd line (index 1)
            if self.dialogue_box.current_line == 1 and self.dialogue_box.is_waiting_for_click:
                self.btn_yes.set_visibility(True)
                self.btn_no.set_visibility(True)

        if self.phase == "START" or self.phase == "STAIRS_PROMPT":
            box = self.dialogue_box.rect
            self.btn_yes.rect = pygame.Rect(box.right - 280, box.bottom - 80, 120, 60)
            self.btn_no.rect = pygame.Rect(box.right - 140, box.bottom - 80, 120, 60)

    def draw(self):
        self.game.screen.fill(BLACK)
        self.game.screen.blit(self.bg, (0, 0))
        if self.npc_sprite:
            self.game.screen.blit(self.npc_sprite, self.npc_sprite.get_rect(center=(self.game.width//2, self.game.height*0.45)))
        self.dialogue_box.draw(self.game.screen)
        self.game.ui_manager.draw(self.game.screen)


class SlotMachineState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.money = self.game.story_manager.money
        self.bet = 100
        self.max_bet = 500
        self.reels = ["", "", ""]
        self.spin_result_message = ""
        self.payout = 0
        self.is_spinning = False
        self.spin_timer = 0
        self.spin_duration = 90
        self.result_display_timer = 0
        self.result_display_duration = 120

        self.symbol_pool = [
            (25, "PIKACHU", 3), (4, "CHARMANDER", 2), (7, "SQUIRTLE", 2), (1, "BULBASAUR", 2),
            (155, "CYNDAQUIL", 2), (158, "TOTODILE", 2), (152, "CHIKORITA", 2),
            (19, "RATTATA", 5), (16, "PIDGEY", 5), (41, "ZUBAT", 5),
            ("POKEBALL_SYMBOL", "POKEBALL", 10)
        ]
        self.symbol_images = {}
        self._load_symbol_images()

        self.btn_exit = Button((30, 30, 140, 70), "EXIT", game.assets.fonts["small"], self.go_back, bg_color=RED)
        self.btn_bet_one = Button((self.game.width // 2 - 250, self.game.height - 100, 150, 60), "BET 100", game.assets.fonts["small"], self.bet_one, bg_color=BLUE)
        self.btn_bet_max = Button((self.game.width // 2 - 75, self.game.height - 100, 150, 60), "BET MAX", game.assets.fonts["small"], self.bet_max, bg_color=BLUE)
        self.btn_spin = Button((self.game.width // 2 + 100, self.game.height - 100, 150, 60), "SPIN", game.assets.fonts["small"], self.spin_reels, bg_color=GREEN)

    def _load_symbol_images(self):
        for symbol_data in self.symbol_pool:
            symbol_key = symbol_data[0]
            if symbol_key == "POKEBALL_SYMBOL":
                self.symbol_images[symbol_key] = pygame.transform.scale(self.game.assets.ui_ball, (100, 100))
            else:
                raw_data = self.game.loader.fetch_specific(symbol_key)
                pokemon = Pokemon(raw_data, self.game.assets)
                if pokemon.image:
                    self.symbol_images[symbol_key] = pygame.transform.scale(pokemon.image, (100, 100))
                else:
                    self.symbol_images[symbol_key] = None

    def go_back(self):
        self.game.story_manager.money = self.money
        self.game.change_state(self.previous_state)

    def bet_one(self):
        if not self.is_spinning and self.result_display_timer == 0:
            self.bet = min(self.max_bet, self.bet + 100)
            self.btn_bet_one.text = f"BET {self.bet}"

    def bet_max(self):
        if not self.is_spinning and self.result_display_timer == 0:
            self.bet = self.max_bet
            self.btn_bet_one.text = f"BET {self.bet}"

    def spin_reels(self):
        if self.is_spinning or self.result_display_timer > 0:
            return
        if self.money < self.bet:
            self.spin_result_message = "Not enough money!"
            self.payout = 0
            self.result_display_timer = self.result_display_duration
            return

        self.money -= self.bet
        self.is_spinning = True
        self.spin_timer = self.spin_duration
        self.spin_result_message = "Spinning..."
        self.payout = 0

    def calculate_payout(self):
        s1, s2, s3 = self.reels
        self.spin_result_message = "No win."
        self.payout = 0

        id1 = s1[0] if isinstance(s1, tuple) else s1
        id2 = s2[0] if isinstance(s2, tuple) else s2
        id3 = s3[0] if isinstance(s3, tuple) else s3

        if id1 == id2 == id3:
            if id1 == "POKEBALL_SYMBOL":
                self.spin_result_message = "JACKPOT! 3 POKEBALLS!"
                self.payout = self.bet * 10
            elif id1 in [25, 4, 7, 155, 158, 152]: # Starters/Legendaries
                self.spin_result_message = f"BIG WIN! 3 {s1[1].upper()}!"
                self.payout = self.bet * 5
            else:
                self.spin_result_message = f"WIN! 3 {s1[1].upper()}!"
                self.payout = self.bet * 3

        elif (id1 == id2 and id3 == "POKEBALL_SYMBOL") or \
             (id1 == id3 and id2 == "POKEBALL_SYMBOL") or \
             (id2 == id3 and id1 == "POKEBALL_SYMBOL"):
            self.spin_result_message = "MEDIUM WIN! 2 MATCH + POKEBALL!"
            self.payout = self.bet * 2
        elif id1 == "POKEBALL_SYMBOL" and id2 == "POKEBALL_SYMBOL" and id3 == "POKEBALL_SYMBOL":
            self.spin_result_message = "SMALL WIN! 3 POKEBALLS!"
            self.payout = self.bet * 1

        self.money += self.payout
        self.result_display_timer = self.result_display_duration

    def start(self):
        self.game.ui_manager.add_element(self.btn_exit)
        self.game.ui_manager.add_element(self.btn_bet_one)
        self.game.ui_manager.add_element(self.btn_bet_max)
        self.game.ui_manager.add_element(self.btn_spin)

    def handle_events(self, events):
        pass

    def update(self):
        if self.is_spinning:
            self.spin_timer -= 1
            if self.spin_timer % 5 == 0:
                weights = [s[2] for s in self.symbol_pool]
                self.reels = random.choices(self.symbol_pool, weights=weights, k=3)
            if self.spin_timer <= 0:
                self.is_spinning = False
                self.calculate_payout()
        elif self.result_display_timer > 0:
            self.result_display_timer -= 1
            if self.result_display_timer <= 0:
                self.spin_result_message = ""
                self.payout = 0

        # ARCHITECT: Use set_visibility instead of set_enabled as the core Button class 
        # uses visibility to manage interaction state and prevent multiple spins.
        can_interact = not self.is_spinning and self.result_display_timer == 0
        self.btn_spin.set_visibility(can_interact)
        self.btn_bet_one.set_visibility(can_interact)
        self.btn_bet_max.set_visibility(can_interact)

    def draw(self):
        self.game.screen.fill((20, 20, 40))

        Utils.draw_text_outline(self.game.screen, "SLOT MACHINE", self.game.assets.fonts["med"], GOLD, self.game.width // 2, 50)

        Utils.draw_text_outline(self.game.screen, f"MONEY: ${self.money}", self.game.assets.fonts["small"], WHITE, self.game.width // 2 - 200, 120, align="left")
        Utils.draw_text_outline(self.game.screen, f"BET: ${self.bet}", self.game.assets.fonts["small"], WHITE, self.game.width // 2 + 200, 120, align="right")

        reel_width = 120
        reel_height = 120
        reel_spacing = 50
        start_x = self.game.width // 2 - (reel_width * 3 + reel_spacing * 2) // 2
        start_y = self.game.height // 2 - reel_height // 2

        for i, symbol_data in enumerate(self.reels):
            rect = pygame.Rect(start_x + i * (reel_width + reel_spacing), start_y, reel_width, reel_height)
            pygame.draw.rect(self.game.screen, (50, 50, 70), rect, border_radius=10)
            pygame.draw.rect(self.game.screen, WHITE, rect, 3, border_radius=10)

            if symbol_data:
                symbol_key = symbol_data[0]
                img = self.symbol_images.get(symbol_key)
                if img:
                    img_rect = img.get_rect(center=rect.center)
                    self.game.screen.blit(img, img_rect)

        if self.spin_result_message:
            Utils.draw_text_outline(self.game.screen, self.spin_result_message, self.game.assets.fonts["s_med"], GOLD, self.game.width // 2, self.game.height // 2 + 150)
            if self.payout > 0:
                Utils.draw_text_outline(self.game.screen, f"WON: ${self.payout}!", self.game.assets.fonts["med"], GREEN, self.game.width // 2, self.game.height // 2 + 200)

        self.game.ui_manager.draw(self.game.screen)


class GameCornerShopState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.bg = previous_state.bg
        self.porygon_sprite = game.assets.get_pokemon_image(137, "normal", False)
        self.clerk_sprite = game.assets.get_trainer_image("supernerd.png")
        self.dialogue_box = ClassicDialogueBox(Utils.get_full_dialogue_rect(game), ["PORYGON: $999,999"], game.assets.fonts["med"])
        self.btn_buy = Button((self.game.width // 2 - 100, 450, 200, 60), "BUY", game.assets.fonts["small"], self.try_buy)
        self.btn_back = Button((20, 20, 100, 50), "BACK", game.assets.fonts["tiny"], self.go_back, bg_color=RED)

    def try_buy(self):
        msg = ["Hah! You can't afford that!", "You're a pretty bad gamer, aren't you?"]
        if self.game.story_manager.current_area_key == "CELADON_CITY":
            msg.append("Hehehe... stay away from the secret stairs!")
        self.dialogue_box.reset(msg)
        self.dialogue_box.callback = self.go_back

    def go_back(self): self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.add_element(self.btn_buy)
        self.game.ui_manager.add_element(self.btn_back)

    def handle_events(self, events):
        for event in events:
            self.dialogue_box.handle_event(event)

    def update(self): self.dialogue_box.update()

    def draw(self):
        self.game.screen.fill(BLACK)
        self.game.screen.blit(self.bg, (0, 0))
        if self.clerk_sprite:
            self.game.screen.blit(self.clerk_sprite, self.clerk_sprite.get_rect(center=(self.game.width*0.3, self.game.height*0.45)))
        if self.porygon_sprite:
            self.game.screen.blit(self.porygon_sprite, self.porygon_sprite.get_rect(center=(self.game.width*0.7, self.game.height*0.45)))
        self.dialogue_box.draw(self.game.screen)
        self.game.ui_manager.draw(self.game.screen)


class PokeMathInfiniteState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.score, self.balls = 0, 5
        self.pool = [i for i in range(1, 151)]
        self.p_data = [None] * 3
        self.problem_str, self.correct_ans, self.options = "", "", []
        self.answer_btn_rects = [pygame.Rect(0, 0, 0, 0) for _ in range(3)]
        self.ball_active = False
        self.ball_pos, self.ball_target = [0, 0], [0, 0]
        self.pause_timer, self.caught_idx = 0, -1
        self.ball_img = game.assets.ball_imgs[0]
        self.stars = [[random.randint(0, game.width), random.randint(0, game.height), random.randint(2, 4)] for _ in range(40)]
        self.sprite_y = game.height * 0.4
        self.base_level = game.story_manager.get_math_level()
        self.generate_round()

    def generate_round(self):
        self.p_data = [Pokemon(self.game.loader.fetch_specific(random.choice(self.pool)), self.game.assets, size_mult=3.125) for _ in range(3)]
        # Starts at the player's level and climbs one level every 10 points
        engine = self.game.math
        level = engine.clamp_level(min(engine.max_level, self.base_level + self.score // 10))
        self.problem_str, self.correct_ans, self.options = engine.generate(level, num_options=3)

    def get_cx(self, i): return (i * self.game.width // 3) + (self.game.width // 6)

    def get_btn_rect(self, i):
        return pygame.Rect(self.get_cx(i) - 60, self.game.height * 0.65, 120, 80)

    def start(self):
        self.game.ui_manager.elements.clear()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and not self.ball_active and self.pause_timer == 0:
                for i in range(3):
                    if self.get_btn_rect(i).collidepoint(event.pos):
                        self.process_answer(i)
                        return

    def process_answer(self, idx):
        self.balls -= 1
        is_correct = self.options[idx] == self.correct_ans
        self.ball_active = True
        self.ball_pos, self.ball_target = [self.game.width // 2, self.game.height], [self.get_cx(idx), self.sprite_y]
        self.caught_idx = idx
        if is_correct:
            self.score += 1
            if self.score % 10 == 0:
                self.balls += 1

    def update(self):
        if self.ball_active:
            self.ball_pos[0] += (self.ball_target[0] - self.ball_pos[0]) * 0.25
            self.ball_pos[1] += (self.ball_target[1] - self.ball_pos[1]) * 0.25
            if abs(self.ball_pos[1] - self.ball_target[1]) < 10:
                self.ball_active = False
                self.pause_timer = 30
        if self.pause_timer > 0:
            self.pause_timer -= 1
            if self.pause_timer == 0:
                if self.balls <= 0:
                    self.previous_state.handle_infinite_result(self.score)
                    self.game.change_state(self.previous_state)
                else:
                    self.generate_round()

    def draw(self):
        screen = self.game.screen
        screen.fill(BLACK)
        for s in self.stars:
            s[1] += s[2]
            if s[1] > self.game.height:
                s[1], s[0] = 0, random.randint(0, self.game.width)
            pygame.draw.circle(screen, (150, 150, 150), (s[0], s[1]), 1)
        Utils.draw_text_outline(screen, f"SCORE: {self.score}", self.game.assets.fonts["small"], GOLD, 20, 20, align="left")
        Utils.draw_text_outline(screen, f"BALLS: {self.balls}", self.game.assets.fonts["small"], WHITE, 20, 60, align="left")
        for i, p in enumerate(self.p_data):
            if p and p.image:
                if not (self.pause_timer > 0 and i == self.caught_idx):
                    screen.blit(p.image, p.image.get_rect(center=(self.get_cx(i), self.sprite_y)))
        if not self.ball_active and self.pause_timer == 0:
            Utils.draw_text_outline(screen, self.problem_str, self.game.assets.fonts["big"], GOLD, self.game.width//2, 100)
            for i in range(3):
                txt = str(self.options[i])
                rect = self.get_btn_rect(i)
                pygame.draw.rect(screen, BLUE, rect, border_radius=15)
                Utils.draw_text_outline(screen, txt, self.game.assets.fonts["num"], WHITE, rect.centerx, rect.centery)
        if self.ball_active:
            screen.blit(self.ball_img, (self.ball_pos[0]-42, self.ball_pos[1]-42))


class FlyState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.btn_back = Button((20, 20, 100, 50), "BACK", game.assets.fonts["tiny"], self.go_back, bg_color=RED)

        self.cities = []
        prog = game.loader.area_data.get("STORY_PROGRESSION", {})
        for key, data in prog.items():
            if data.get("area_type") == "town" and game.story_manager.story_flags.get(f"visited_{key}"):
                self.cities.append((key, data.get("route_name", key)))

        if game.story_manager.inventory.get("MT_SILVER_MAP", 0) > 0:
            silver_key = "SILVER_LEAGUE_PLATEAU"
            silver_name = prog.get(silver_key, {}).get("route_name", "Silver League")
            if not any(c[0] == silver_key for c in self.cities):
                self.cities.append((silver_key, silver_name))

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.add_element(self.btn_back)
        from src.states.overworld import AreaTransitionState
        for i, (key, name) in enumerate(self.cities):
            row, col = i // 2, i % 2
            rect = (100 + col * 350, 150 + row * 80, 300, 60)
            btn = Button(rect, name.upper(), self.game.assets.fonts["tiny"],
                         lambda k=key: self.game.change_state(AreaTransitionState(self.game, k)),
                         autosize=False)
            self.game.ui_manager.add_element(btn)

    def handle_events(self, events):
        pass

    def update(self):
        pass

    def draw(self):
        self.game.screen.fill((30, 30, 50))
        Utils.draw_text_outline(self.game.screen, "AIR BALLOON - FLY", self.game.assets.fonts["med"], GOLD, self.game.width//2, 60)
        self.game.ui_manager.draw(self.game.screen)


class FossilRevivalState(GameState):
    def __init__(self, game, fossil_name, pokemon_id, previous_state, consume=None):
        super().__init__(game)
        self.fossil_name = fossil_name
        self.consume = consume or [fossil_name]
        self.pokemon_id = pokemon_id
        self.previous_state = previous_state
        self.phase = "START"
        self.timer = 60
        self.scale = 1.0
        self.alpha = 255

        self.fossil_img = game.assets.get_item_image(fossil_name)
        if self.fossil_img:
            self.fossil_img = pygame.transform.scale(self.fossil_img, (160, 160))

        raw = self.game.loader.fetch_specific(pokemon_id)
        self.evolved_pokemon_obj = Pokemon(raw, self.game.assets, size_mult=3.0)

    def handle_events(self, events):
        pass

    def update(self):
        self.timer -= 1
        if self.phase == "START" and self.timer <= 0:
            self.phase = "GROW"
            self.timer = 50
        elif self.phase == "GROW":
            self.scale += 0.06
            self.alpha = max(0, self.alpha - 12)
            if self.timer <= 0:
                self.phase = "FLASH"
                self.timer = 20
        elif self.phase == "FLASH":
            if self.timer <= 0:
                self.phase = "REVEAL"
                self.timer = 60
                if self.evolved_pokemon_obj.cry:
                    self.evolved_pokemon_obj.cry.play()
                self.scale = 4.0
                self.alpha = 0
        elif self.phase == "REVEAL":
            self.scale = max(1.0, self.scale - 0.15)
            self.alpha = min(255, self.alpha + 20)
            if self.timer <= 0:
                self.phase = "END"
            self.timer = 60
            self._finalize_revival()
        elif self.phase == "END" and self.timer <= 0:
            pygame.event.clear()
            self.game.change_state(self.previous_state)

    def _finalize_revival(self):
        story = self.game.story_manager
        for item in self.consume:
            story.inventory[item] -= 1

        revival_flag = f"revived_fossil_{story.current_area_key}"
        story.story_flags[revival_flag] = True

        msg = f"Success! The fossil was revived into {self.evolved_pokemon_obj.display_name}!"
        if len(story.player_team) < 6:
            story.player_team.append(self.evolved_pokemon_obj)
        else:
            story.pc_pokemon.append(self.evolved_pokemon_obj)
            msg += " Sent to BILL'S PC."

        self.game.data.add_pokemon(self.evolved_pokemon_obj)
        self.game.data.save()

        if hasattr(self.previous_state, 'show_message'):
            self.previous_state.show_message(msg)

    def draw(self):
        screen = self.game.screen
        screen.fill(BLACK)
        cx, cy = self.game.width // 2, self.game.height // 2

        if self.phase in ["START", "GROW"]:
            if self.fossil_img:
                img = pygame.transform.rotozoom(self.fossil_img, 0, self.scale)
                img.set_alpha(self.alpha)
                screen.blit(img, img.get_rect(center=(cx, cy)))
            Utils.draw_text_outline(screen, "REVIVING ANCIENT FOSSIL...", self.game.assets.fonts["med"], WHITE, cx, self.game.height * 0.85)

        elif self.phase == "FLASH":
            screen.fill(WHITE)

        elif self.phase in ["REVEAL", "END"]:
            if self.evolved_pokemon_obj.image:
                img = pygame.transform.rotozoom(self.evolved_pokemon_obj.image, 0, self.scale)
                img.set_alpha(self.alpha)
                screen.blit(img, img.get_rect(center=(cx, cy)))
                Utils.draw_text_outline(screen, f"REVIVED {self.evolved_pokemon_obj.display_name.upper()}!",
                                        self.game.assets.fonts["med"], GOLD, cx, self.game.height * 0.85)

        self.game.ui_manager.draw(screen)


class UnownReportState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.btn_back = Button((30, 30, 140, 70), "BACK", game.assets.fonts["small"],
                               self.go_back, bg_color=RED)

        self.forms = ["normal", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
                      "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "question", "exclamation"]

        all_owned = self.game.story_manager.player_team + self.game.story_manager.pc_pokemon
        self.caught_forms = {p.form for p in all_owned if p and p.id == 201}

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.elements.clear()
        self.game.ui_manager.add_element(self.btn_back)

    def handle_events(self, events):
        pass

    def update(self):
        pass

    def draw(self):
        screen = self.game.screen
        screen.fill((25, 25, 35))
        Utils.draw_text_outline(screen, "UNOWN RESEARCH REPORT", self.game.assets.fonts["med"], GOLD, self.game.width//2, 50)

        cols = 7
        start_x, start_y = 100, 140
        gap_x, gap_y = 150, 130

        for i, f in enumerate(self.forms):
            col, row = i % cols, i // cols
            dx, dy = start_x + col * gap_x, start_y + row * gap_y

            is_caught = f in self.caught_forms if self.caught_forms else False
            pygame.draw.rect(screen, (45, 45, 60), (dx-60, dy-60, 120, 120), border_radius=10)

            if is_caught:
                img = self.game.assets.get_pokemon_image(201, f, False)
                if img:
                    img = pygame.transform.scale(img, (90, 90))
                    screen.blit(img, img.get_rect(center=(dx, dy)))

                lbl = f.upper() if len(f) == 1 else ("?" if f == "question" else "!")
                if f == "normal":
                    lbl = "A"
                Utils.draw_text_outline(screen, lbl, self.game.assets.fonts["tiny"], WHITE, dx, dy + 75)
            else:
                Utils.draw_text_outline(screen, "?", self.game.assets.fonts["med"], (80, 80, 100), dx, dy)

        self.game.ui_manager.draw(screen)


class MapState(GameState):
    def __init__(self, game, previous_state, initial_message=None):
        super().__init__(game)
        self.previous_state = previous_state

        self.map_list = []
        inv = self.game.story_manager.inventory
        if inv.get("TOWN_MAP", 0) > 0:
            self.map_list.append((os.path.join(self.game.assets.assets_dir, "kanto_map.png"), "Kanto Region"))
        if inv.get("JOHTO_MAP", 0) > 0:
            self.map_list.append((os.path.join(self.game.assets.assets_dir, "johto_map.png"), "Johto Region"))

        if not self.map_list:
            self.map_list.append((os.path.join(self.game.assets.assets_dir, "kanto_map.png"), "World Map"))

        self.current_idx = 0
        self.map_img = None
        self._load_current_map()

        msg = initial_message if initial_message else [f"TOWN MAP: Exploring the {self.map_list[self.current_idx][1]}!"]
        self.dialogue_box = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(game), msg, self.game.assets.fonts["med"]
        )

        self.btn_back = Button(
            (20, 20, 120, 50), "EXIT", game.assets.fonts["tiny"],
            self.go_back, bg_color=RED
        )

        cy = game.height // 2
        show_arrows = len(self.map_list) > 1
        self.btn_prev = Button((20, cy - 30, 60, 60), "<", game.assets.fonts["med"], self.prev_map, visible=show_arrows)
        self.btn_next = Button((game.width - 80, cy - 30, 60, 60), ">", game.assets.fonts["med"], self.next_map, visible=show_arrows)

    def _load_current_map(self):
        path, label = self.map_list[self.current_idx]
        if os.path.exists(path):
            try:
                raw = pygame.image.load(path).convert()
                box_top = Utils.get_full_dialogue_rect(self.game).top
                self.map_img = pygame.transform.scale(raw, (self.game.width, box_top))
            except pygame.error:
                self.map_img = None
        else:
            self.map_img = None

    def prev_map(self):
        self.current_idx = (self.current_idx - 1) % len(self.map_list)
        self._load_current_map()
        self.dialogue_box.reset([f"Now viewing: {self.map_list[self.current_idx][1]}"])

    def next_map(self):
        self.current_idx = (self.current_idx + 1) % len(self.map_list)
        self._load_current_map()
        self.dialogue_box.reset([f"Now viewing: {self.map_list[self.current_idx][1]}"])

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.elements.clear()
        self.game.ui_manager.add_element(self.btn_back)
        self.game.ui_manager.add_element(self.btn_prev)
        self.game.ui_manager.add_element(self.btn_next)
        self.game.ui_manager.add_element(self.dialogue_box)

    def handle_events(self, events):
        for event in events:
            self.dialogue_box.handle_event(event)

    def update(self):
        self.dialogue_box.update()

    def draw(self):
        self.game.screen.fill(BLACK)
        if self.map_img:
            self.game.screen.blit(self.map_img, (0, 0))
        self.dialogue_box.draw(self.game.screen)
        self.game.ui_manager.draw(self.game.screen)
class PokeNavState(GameState):
    """HUD extension that displays exact route encounter rates and completion status."""
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.area_data = game.story_manager.get_current_area_data()
        self.pool_key = self.area_data.get("wild_pool_percentages")
        self.pool = game.loader.area_data.get(self.pool_key, {}) if self.pool_key else {}
        
        self.btn_back = Button((30, 30, 140, 70), "BACK", game.assets.fonts["small"], 
                               self.go_back, bg_color=RED)

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.add_element(self.btn_back)

    def handle_events(self, events):
        pass

    def update(self):
        pass

    def draw(self):
        screen = self.game.screen
        screen.fill((10, 40, 30)) # Dark Nav Green
        
        route_name = self.area_data.get("route_name", "Unknown Area")
        Utils.draw_text_outline(screen, f"POKENAV: {route_name.upper()}", 
                                self.game.assets.fonts["med"], GREEN, self.game.width//2, 60)

        if not self.pool:
            Utils.draw_text_outline(screen, "NO WILD DATA FOR THIS AREA", 
                                    self.game.assets.fonts["s_med"], WHITE, self.game.width//2, self.game.height//2)
            self.game.ui_manager.draw(screen)
            return

        start_y = 150
        has_devon_scope = self.game.story_manager.inventory.get("DEVON_SCOPE", 0) > 0
        caught_data = self.game.data.data.get("pokedex", {})
        
        sorted_pool = sorted(self.pool.items(), key=lambda x: x[1], reverse=True)
        
        for i, (p_id_str, chance) in enumerate(sorted_pool):
            p_id = int(p_id_str)
            name = self.game.assets.pokemon_names.get(str(p_id), "???").upper()
            is_caught = str(p_id) in caught_data
            
            # ARCHITECT: Devon Scope highlights "Hidden" Pokémon (<5%) in Gold
            is_rare = chance < 5
            text_color = WHITE
            if is_rare and has_devon_scope:
                text_color = GOLD
            elif is_rare:
                name = "???" # Obscure rare ones without scope
            
            y_pos = start_y + i * 45
            label = f"{name}: {chance}%"
            
            Utils.draw_text_outline(screen, label, self.game.assets.fonts["tiny"], 
                                    text_color, 200, y_pos, align="left")
            
            if is_caught:
                screen.blit(self.game.assets.ui_ball, (160, y_pos - 10))
            else:
                pygame.draw.circle(screen, GRAY, (175, y_pos), 8)

        self.game.ui_manager.draw(screen)
        self.game.ui_manager.draw(self.game.screen)
