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
import random


# [REF-0060: Journal System]
class JournalState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        # Fetch all entries (Active and Completed)
        self.missions = game.story_manager.get_all_journal_entries()
        # [FIX] Sort ACTIVE missions to the top (status 'ACTIVE' before 'COMPLETED')
        self.missions.sort(key=lambda x: 0 if x["status"] == "ACTIVE" else 1)

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
        # Mark all current missions as notified/read
        for m in self.missions:
            if m["id"] not in self.game.story_manager.notified_missions:
                self.game.story_manager.notified_missions.append(m["id"])

    def handle_events(self, events):
        pass

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

        # Mission Cards
        start_y = 150
        card_w = self.game.width - 200
        card_h = 180
        spacing = 20

        for i, m in enumerate(self.missions[:3]):
            rect = pygame.Rect(100, start_y + i * (card_h + spacing), card_w, card_h)

            # Background Panel
            bg_col = (40, 45, 70) if m["status"] == "ACTIVE" else (25, 25, 35)
            pygame.draw.rect(screen, bg_col, rect, border_radius=15)
            pygame.draw.rect(screen, WHITE, rect, 3, border_radius=15)

            # Title
            type_lbl = "[STORY]" if m["type"] == "MAIN" else "[SIDE]"
            Utils.draw_text_outline(
                screen, 
                f"{type_lbl} {m['text']}", 
                self.game.assets.fonts["s_med"], 
                GOLD, 
                rect.x + 20, 
                rect.y + 40, 
                align="left")
            
            # Status and Reward
            stat_col = GREEN if m["status"] == "COMPLETED" else GOLD
            Utils.draw_text_outline(screen, f"STATUS: {m['status']}", self.game.assets.fonts["tiny"], stat_col, rect.right - 20, rect.y + 40, align="right")
            reward = m.get("reward", "None")
            Utils.draw_text_outline(screen, f"REWARD: {reward}", self.game.assets.fonts["tiny"], (0, 200, 255), rect.right - 20, rect.bottom - 30, align="right")

            # [UPDATE] Only display description for ACTIVE missions. 
            # Completed missions only show the header and the reward.
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

        # Swap Logic Handling
        if self.move_swap_index is not None:
            # Perform Swap
            if index != self.move_swap_index:
                team[self.move_swap_index], team[index] = team[index], team[self.move_swap_index]
                self.start()
                self.dialogue_box.reset("Moved Pokémon position!")
                self.dialogue_box.callback = self._dismiss_dialogue
                self.dialogue_box.visible = True
            else:
                # Clicked same slot, cancel swap
                pass

            self.move_swap_index = None
            self.message = "Choose a PKMN."
            return

        # Standard Logic
        if self.context == "use_item": # Handle item usage separately
            if self.on_select:
                self.on_select(index)
            return

        self.selected_slot_index = index

        if self.context in ["battle_switch", "normal"]:
            self.popup_active = True
            clicked_slot_rect = self.slots[index].rect

            popup_w = 150

            # Left Column (indices 0, 2, 4) -> Popup on Right
            # Right Column (indices 1, 3, 5) -> Popup on Left
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
            # Start Move Mode
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

            # Center the message in the left 55% of the panel, leaving room for buttons on the right
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
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.phase = "SHOP"
        self.shop_buttons = []
        self.current_page = 0
        self.items_per_page = 8  # 4 columns x 2 rows fit comfortably
        self.pending_item = None
        self.pending_cost = 0

        self.bottom_rect = Utils.get_full_dialogue_rect(game)

        # Move Exit button to HUD area (Top Left) to clear space in the panel
        self.btn_back = Button((20, 20, 100, 50), "EXIT", game.assets.fonts["tiny"], self.exit_shop, bg_color=RED)

        # Arrows for panel scrolling
        self.btn_prev = Button((self.bottom_rect.left + 10, self.bottom_rect.centery - 25, 50, 50), "<", game.assets.fonts["med"], self.prev_page, visible=False)
        self.btn_next = Button((self.bottom_rect.right - 60, self.bottom_rect.centery - 25, 50, 50), ">", game.assets.fonts["med"], self.next_page, visible=False)

        # Confirmation Buttons (Shopping Cart)
        cx, cy = game.width // 2, game.height // 2
        self.btn_yes = Button((cx - 150, cy + 50, 120, 60), "BUY", game.assets.fonts["small"], self.confirm_purchase, bg_color=GREEN, autosize=False, visible=False)
        self.btn_no = Button((cx + 30, cy + 50, 120, 60), "CANCEL", game.assets.fonts["small"], self.cancel_purchase, bg_color=RED, autosize=False, visible=False)

        self.dialogue_box = ClassicDialogueBox(self.bottom_rect, [], game.assets.fonts["med"], visible=False)

        self.bg = self._load_building_bg(game, "mart")

        area_key = game.story_manager.current_area_key
        flag = f"visited_mart_{area_key}"

        if not game.story_manager.story_flags.get(flag, False):
            msg = ["Welcome to the Poké Mart!", "We are currently stocking shelves.", "Here, take these 10 Poké Balls!"]
            game.story_manager.balls_left += 10
            game.story_manager.story_flags[flag] = True
            self.dialogue_box.reset(msg)
            self.dialogue_box.callback = self.on_welcome_dialogue_end
            self.phase = "DIALOGUE"

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_buttons()

    def next_page(self):
        all_items = ["POKE_BALLS"] + sorted(list(self.game.loader.evolution_map.get("EVOLUTION_ITEMS", {}).keys()))
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

        # Construct Item List: Pokeballs + Evo Items
        evo_items = sorted(
            list(self.game.loader.evolution_map.get("EVOLUTION_ITEMS", {}).keys())
        )
        all_items = ["POKE_BALLS", "RARE_CANDY"] + evo_items

        self.btn_prev.set_visibility(self.current_page > 0)
        self.btn_next.set_visibility((self.current_page + 1) * self.items_per_page < len(all_items))

        start_idx = self.current_page * self.items_per_page
        page_items = all_items[start_idx : start_idx + self.items_per_page]

        # Grid Layout within Bottom Panel
        cols = 4
        rows = 2

        # Define grid area inside the panel, respecting arrow buttons
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

            else:
                # Shorten long names for grid
                name = item.replace("_", " ").title().replace(" Fossil", "")
                price = 999999 if item == "UPGRADE" else 10000
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
            self.dialogue_box.callback = self.cancel_purchase # Reset to shop mode
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
        # 1. Check JSON config first (Primary)
        area_data = game.story_manager.get_current_area_data()
        json_key = "pokecenter" if type_suffix == "center" else "pokemart"
        bg_config = area_data.get("backgrounds", {}).get(json_key)

        # 2. Fallback Construction (Legacy naming)
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
             pass # Handled by buttons

    def update(self):
        if self.phase == "DIALOGUE" or self.phase == "CONFIRM":
            self.dialogue_box.update()

    def draw(self):
        self.game.screen.fill(BLACK)
        self.game.screen.blit(self.bg, (0, 0))
        
        if self.phase == "SHOP" or self.phase == "CONFIRM":
            Utils.draw_classic_panel(self.game.screen, self.bottom_rect.x, self.bottom_rect.y, self.bottom_rect.width, self.bottom_rect.height)

            # [UPDATE] Show Money in HUD area (Top Right) to avoid panel clutter
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
            
            # Balls Count
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
        
        self.font = game.assets.fonts["tiny"]
        self.btn_back = Button((20, 20, 100, 50), "BACK", self.font, self.go_back, bg_color=RED)
        
        # Layout Configuration for Large Sprites (4x size)
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

    def start(self):
        self.game.ui_manager.add_element(self.btn_back)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Check Party Slots (Left Side)
                    for i in range(6):
                        rect = pygame.Rect(50, 100 + i * 85, 300, 75)
                        if rect.collidepoint(event.pos):
                            self.handle_click("party", i)
                            return
                    
                    # Check PC Slots (Right Side Grid)
                    available_w = self.game.width - self.grid_start_x - 20
                    cols = max(1, available_w // (self.slot_size + self.slot_gap))
                    
                    # Render enough slots for all PC mons + 1 empty slot (for deposit)
                    total_slots = len(self.pc) + 1
                    for i in range(total_slots):
                        c, r = i % cols, i // cols
                        rx = self.grid_start_x + c * (self.slot_size + self.slot_gap)
                        ry = self.grid_start_y + r * (self.slot_size + self.slot_gap) - self.scroll_y
                        
                        # Only check if visible on screen
                        if 80 < ry < self.game.height - 20:
                            slot_rect = pygame.Rect(rx, ry, self.slot_size, self.slot_size)
                            if slot_rect.collidepoint(event.pos):
                                self.handle_click("pc", i)
                                return

                elif event.button == 4:
                    self.scroll_y = max(0, self.scroll_y - 40)
                elif event.button == 5:
                    available_w = self.game.width - self.grid_start_x - 20
                    cols = max(1, available_w // (self.slot_size + self.slot_gap))
                    row_h = self.slot_size + self.slot_gap
                    rows = (len(self.pc) // cols) + 2
                    max_scroll = max(0, rows * row_h - (self.game.height - 120))
                    self.scroll_y = min(max_scroll, self.scroll_y + 40)

    def handle_click(self, source, index):
        # 1. Handle Selection Logic
        if source == "party":
            if index >= len(self.party):
                # Clicked empty party slot
                if self.selected_pc_idx is not None:
                    # Withdraw
                    self.party.append(self.pc.pop(self.selected_pc_idx))
                    self.selected_pc_idx = None
                return
            
            if self.selected_party_idx == index:
                self.selected_party_idx = None
            elif self.selected_party_idx is not None:
                # Swap Party <-> Party
                old_idx = self.selected_party_idx
                self.party[index], self.party[old_idx] = self.party[old_idx], self.party[index]
                self.selected_party_idx = None
            elif self.selected_pc_idx is not None:
                # Swap PC -> Party
                self.party[index], self.pc[self.selected_pc_idx] = self.pc[self.selected_pc_idx], self.party[index]
                self.selected_pc_idx = None
            else:
                self.selected_party_idx = index

        elif source == "pc":
            if index >= len(self.pc):
                # Clicked empty PC slot (Deposit target)
                if self.selected_party_idx is not None:
                    if len(self.party) > 1:
                        self.pc.append(self.party.pop(self.selected_party_idx))
                        self.selected_party_idx = None
                    else:
                        self.game.show_dialogue(["Can't store your last Pokémon!"])
                return

            if self.selected_pc_idx == index:
                self.selected_pc_idx = None
            elif self.selected_pc_idx is not None:
                # Swap PC <-> PC
                self.pc[index], self.pc[self.selected_pc_idx] = self.pc[self.selected_pc_idx], self.pc[index]
                self.selected_pc_idx = None
            elif self.selected_party_idx is not None:
                # Swap Party -> PC
                if len(self.party) == 1:
                    self.game.show_dialogue(["Can't store your last Pokémon!"])
                    return
                old_p_idx = self.selected_party_idx
                self.party[old_p_idx], self.pc[index] = self.pc[index], self.party[old_p_idx]
                self.selected_party_idx = None
            else:
                self.selected_pc_idx = index

    def update(self):
        pass

    def draw(self):
        self.game.screen.fill((30, 50, 60))
        Utils.draw_text_outline(self.game.screen, "BILL'S PC", self.game.assets.fonts["med"], WHITE, self.game.width//2, 40)
        
        # Draw Party (Left)
        Utils.draw_text_outline(self.game.screen, "PARTY", self.font, GOLD, 200, 85)
        for i in range(6):
            rect = pygame.Rect(50, 100 + i * 85, 300, 75)
            color = (60, 100, 150)
            if i < len(self.party):
                if self.selected_party_idx == i: color = (100, 200, 100)
                pygame.draw.rect(self.game.screen, color, rect, border_radius=10)
                pygame.draw.rect(self.game.screen, WHITE, rect, 2, border_radius=10)
                
                p = self.party[i]
                screen_y = rect.centery
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
                # Empty slot
                pygame.draw.rect(self.game.screen, (40, 60, 80), rect, border_radius=10)
                pygame.draw.rect(self.game.screen, (80, 100, 120), rect, 2, border_radius=10)

        # Draw PC Grid (Right)
        Utils.draw_text_outline(self.game.screen, f"STORAGE ({len(self.pc)})", self.font, GOLD, 600, 85)
        
        # Scissor clip for scrolling area
        clip_rect = pygame.Rect(self.grid_start_x - 10, self.grid_start_y, self.game.width - self.grid_start_x, self.game.height - 120)
        self.game.screen.set_clip(clip_rect)
        
        available_w = self.game.width - self.grid_start_x - 20
        cols = max(1, available_w // (self.slot_size + self.slot_gap))
        
        total_slots = len(self.pc) + 1
        
        for i in range(total_slots):
            c, r = i % cols, i // cols
            rx = self.grid_start_x + c * (self.slot_size + self.slot_gap)
            ry = self.grid_start_y + r * (self.slot_size + self.slot_gap) - self.scroll_y
            
            rect = pygame.Rect(rx, ry, self.slot_size, self.slot_size)
            
            if i < len(self.pc):
                color = (60, 100, 150)
                if self.selected_pc_idx == i: color = (100, 200, 100)
                pygame.draw.rect(self.game.screen, color, rect, border_radius=5)
                pygame.draw.rect(self.game.screen, WHITE, rect, 2, border_radius=5)
                
                p = self.pc[i]
                # Large 4x Sprite
                sprite = p.image if p.image else p.sidebar_image
                if sprite:
                    spr = pygame.transform.scale(sprite, (self.sprite_size, self.sprite_size))
                    # Center the sprite in the slot
                    spr_rect = spr.get_rect(center=rect.center)
                    self.game.screen.blit(spr, spr_rect)
            else:
                # "New/Empty" slot indicator
                pygame.draw.rect(self.game.screen, (40, 60, 80), rect, border_radius=5)
                pygame.draw.rect(self.game.screen, (80, 100, 120), rect, 2, border_radius=5)
                Utils.draw_text_outline(self.game.screen, "+", self.game.assets.fonts["med"], GRAY, rect.centerx, rect.centery)

        self.game.screen.set_clip(None)
        self.game.ui_manager.draw(self.game.screen)


# [REF-0032: Bag System]
class BagState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.evo_items_map = self.game.loader.evolution_map.get("EVOLUTION_ITEMS", {})
        self.evo_keys = sorted(list(self.evo_items_map.keys()))
        
        self.pages = ["EVOLUTION ITEMS", "KEY ITEMS"]
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
        # [FIX] Properly clear old buttons from UI Manager before rebuilding
        for btn in self.item_buttons:
            if btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)
                
        self.item_buttons = []
        
        items_to_show = []
        if self.current_page == 0:
            # Add Rare Candy first if owned
            if self.game.story_manager.inventory.get("RARE_CANDY", 0) > 0:
                items_to_show.append(("RARE_CANDY", self.game.story_manager.inventory["RARE_CANDY"]))

            for key in self.evo_keys:
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
            can_use = (qty > 0 and (self.current_page == 0 or is_rare_candy))
            color = BLUE if can_use else GRAY
            callback = (lambda k=item_key: self.use_item(k)) if can_use else None
            
            icon = self.game.assets.get_item_image(item_key)
            
            # Special handling for the Mystery Egg icon from the pokemon directory
            if item_key == "MYSTERY_EGG":
                egg_path = os.path.join("assets", "sprites", "pokemon", "egg.png")
                if os.path.exists(egg_path):
                    icon = pygame.image.load(egg_path).convert_alpha()
                    icon = pygame.transform.scale(icon, (128,128))
            
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
            
        # [FIX] Add new buttons to UI Manager immediately
        for btn in self.item_buttons:
            self.game.ui_manager.add_element(btn)
    
    def handle_events(self, events):
        # Need to capture mouse wheel for long lists if we added scrolling (not yet needed for just arrow pages)
        pass

    def update(self):
        pass

    def use_item(self, item_key):
        self.selected_item = item_key
        
        # Special case for Rare Candy
        if item_key == "RARE_CANDY":
            self.game.change_state(PokemonPartyMenuState(
                self.game, 
                previous_state=self, 
                context="use_item",
                on_select=self.on_pokemon_select_rare_candy
            ))
            return

        self.game.change_state(PokemonPartyMenuState(
            self.game, 
            previous_state=self, 
            context="use_item",
            on_select=self.on_pokemon_select
        ))
    def on_pokemon_select(self, slot_index):
        party = self.game.story_manager.player_team
        if slot_index >= len(party): return

        pokemon = party[slot_index]
        evolution_data = self.evo_items_map.get(self.selected_item, {})
        
        # Check standard name or form name (e.g. VULPIX_ALOLAN)
        p_key = pokemon.name.upper()
        if pokemon.form and pokemon.form != "normal":
            alt_key = f"{p_key}_{pokemon.form.upper()}"
            if alt_key in evolution_data:
                p_key = alt_key

        if p_key in evolution_data:
            target_name = evolution_data[p_key]
            # Find target ID
            target_id = self.game.name_to_id.get(target_name.split("_")[0])
            
            target_form = "normal"
            if "_" in target_name:
                target_form = target_name.split("_", 1)[1].lower()

            if target_id:
                # CONSUME ITEM
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
        if slot_index >= len(party): return

        pokemon = party[slot_index]
        
        # Find its evolution
        key = pokemon.name.upper()
        if pokemon.form and pokemon.form != "normal":
            key += f"_{pokemon.form.upper()}"

        next_entries = self.game.loader.evolution_map.get(key)
        if not next_entries:
            self.game.show_dialogue([f"{pokemon.display_name} can't evolve further."])
            self.game.change_state(self) # Return to bag
            self.refresh_buttons()
            return

        # Consume item
        self.game.story_manager.inventory["RARE_CANDY"] -= 1
        if self.game.story_manager.inventory["RARE_CANDY"] <= 0:
            del self.game.story_manager.inventory["RARE_CANDY"]

        next_entry = next_entries[0]
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

    def draw(self):
        self.game.screen.fill((40, 40, 60))
        
        page_title = self.pages[self.current_page]
        Utils.draw_text_outline(self.game.screen, page_title, self.game.assets.fonts["med"], WHITE, self.game.width//2, 50)
        
        if not self.item_buttons:
            Utils.draw_text_outline(self.game.screen, "No Items", self.game.assets.fonts["s_med"], GRAY, self.game.width//2, self.game.height//2)
        
        # [UPDATE] Show Money
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
        
        # Pop-up Menu State
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
        
        # Pop-up Buttons
        self.btn_cry = Button((0, 0, 160, 50), "CRY", game.assets.fonts["tiny"], self.play_selected_cry, bg_color=BLUE, visible=False)
        self.btn_area = Button((0, 0, 160, 50), "AREA", game.assets.fonts["tiny"], self.show_selected_area, bg_color=GREEN, visible=False)

        self.btn_shiny_toggle = Button(
            rect=(game.width - 250, 30, 220, 70),
            text="SHINIES",
            font=game.assets.fonts["small"],
            callback=self.toggle_shiny_filter,
            bg_color=BLUE,
        )
        # [UPDATE] Sort Toggle
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
            except: pass
        self.hide_popup()

    def show_selected_area(self):
        if not self.selected_pkmn_id: return
        
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
        self.game.show_dialogue(msg)
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
            
            # Determine Regional vs National ID list
            if national_dex:
                id_list = list(range(1, 252))  # National: 1-251
            elif starting_region == "KANTO":
                id_list = list(range(1, 152))  # Kanto: 1-151
            else:
                # Johto: Show standard 152-251, plus any Kanto (1-151) seen/caught
                kanto_visible = []
                caught_ids = {v['id'] for v in caught_data.values()}
                seen_set = set(seen_ids)
                for p_id in range(1, 152):
                    if p_id in seen_set or p_id in caught_ids:
                        kanto_visible.append(p_id)
                id_list = kanto_visible + list(range(152, 252))

            for p_id in id_list:
                is_caught = False
                caught_entry = None
                
                # Check if caught (any form counts for the base slot)
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
                    entry["shiny"] = caught_entry['shiny']
                elif is_seen:
                    entry["status"] = 1
                    entry["name"] = self.game.assets.pokemon_names.get(str(p_id), f"#{p_id}").upper()
                
                if self.show_shinies_only:
                    if not entry["shiny"]:
                        continue
                        
                self.full_dex.append(entry)
            
            # ARCHITECT: Check for Nown (3022) - Hidden until received
            for k, v in caught_data.items():
                if v.get('id') == 3022:
                    self.full_dex.append({
                        "id": 3022,
                        "status": 2,
                        "shiny": v.get("shiny", False),
                        "form": "normal",
                        "name": "NOWN"
                    })
                    break

            # Apply Sorting
            if self.sort_mode == "NUMBER":
                self.full_dex.sort(key=lambda x: x.get("id", 0))
            else:
                self.full_dex.sort(key=lambda x: x.get("name", "ZZZ").upper())

            # Force Nown to the very top if it has been discovered
            nown = next((p for p in self.full_dex if p['id'] == 3022), None)
            if nown:
                self.full_dex.remove(nown)
                self.full_dex.insert(0, nown)

            return
        else:
            source_data = self.game.data.data.get("pokedex", {})
            self.full_dex = [ 
                p for p in source_data.values() 
                if p.get("form", "normal") == self.current_tab
            ]

        if self.show_shinies_only:
            self.full_dex = [p for p in self.full_dex if p["shiny"]]

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
                            # Keep on screen
                            if self.popup_rect.right > self.game.width: self.popup_rect.right = event.pos[0] - 10
                            
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
        total_caught = len(self.game.data.data["pokedex"])
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
        current_view = self.full_dex[start_idx : start_idx + per_page]

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
                
                # ARCHITECT: Override ID display for Nown
                id_num = "???" if p_entry['id'] == 3022 else p_entry['id']
                Utils.draw_text_outline(
                    screen,
                    f"#{id_num}",
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
                    # Show Sprite (Normal or Grey)
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
                    
                    # Only allow cry playback if seen/caught
                    self.dex_btns.append((rect, p_entry["id"]))
                else:
                    # Unknown '?'
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
        self.earned_badges = game.story_manager.badges # List of badge keys like "BOULDER"
        
        # Page Management
        self.unlocked_regions = []
        if game.story_manager.story_flags.get("unlocked_kanto_badges"):
            self.unlocked_regions.append("KANTO")
        if game.story_manager.story_flags.get("unlocked_johto_badges"):
            self.unlocked_regions.append("JOHTO")
            
        # Default sorting: starting region first
        if len(self.unlocked_regions) > 1 and game.story_manager.starting_region == "JOHTO":
            self.unlocked_regions = ["JOHTO", "KANTO"]

        self.current_page_idx = 0
        
        self.btn_back = Button(
            rect=(30, 30, 140, 70),
            text="BACK",
            font=game.assets.fonts["small"],
            callback=self.go_back,
            bg_color=RED,
        )

        # Navigation Arrows
        cx, cy = game.width // 2, game.height // 2
        self.btn_prev = Button((30, cy - 30, 60, 60), "<", game.assets.fonts["med"], self.prev_page)
        self.btn_next = Button((game.width - 90, cy - 30, 60, 60), ">", game.assets.fonts["med"], self.next_page)

        # Regional Badge Maps (Name -> Sprite Index 1-8)
        self.region_maps = {
            "KANTO": {
                "BOULDER": 1, "CASCADE": 2, "THUNDER": 3, "RAINBOW": 4,
                "SOUL": 5, "MARSH": 6, "VOLCANO": 7, "EARTH": 8
            },
            "JOHTO": {
                "ZEPHYR": 1, "HIVE": 2, "PLAIN": 3, "FOG": 4,
                "STORMBADGE": 5, "MINERAL": 6, "GLACIER": 7, "RISING": 8
            }
        }
        
        self.badge_sprites = {"KANTO": {}, "JOHTO": {}}
        for i in range(1, 9):
            k_img = game.assets.get_badge_image(i, "kanto")
            if k_img: self.badge_sprites["KANTO"][i] = pygame.transform.scale(k_img, (100, 100))
            
            j_img = game.assets.get_badge_image(i, "johto")
            if j_img: self.badge_sprites["JOHTO"][i] = pygame.transform.scale(j_img, (100, 100))

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
        screen.fill(DARK_RED if region == "KANTO" else (15, 35, 85)) # Red for Kanto, Blue for Johto

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

        # 4x2 Grid Calculation
        # Pad inside the grey box
        grid_rect = case_rect.inflate(-40, -60)
        cell_w = grid_rect.width / 4
        cell_h = grid_rect.height / 2

        for i in range(1, 9):
            row = (i - 1) // 4
            col = (i - 1) % 4
            
            cx = grid_rect.x + (col + 0.5) * cell_w
            cy = grid_rect.y + (row + 0.5) * cell_h + 10
            
            sprite = self.badge_sprites.get(region, {}).get(i)
            badge_map = self.region_maps.get(region, {})

            if sprite:
                # Check if earned
                earned = any(badge_map.get(b_name) == i for b_name in self.earned_badges)
                
                draw_sprite = sprite.copy()
                if not earned:
                    # Grayscale
                    draw_sprite.fill((100, 100, 100), special_flags=pygame.BLEND_RGB_MULT)
                    draw_sprite.set_alpha(100)
                
                # Draw centered
                sprite_rect = draw_sprite.get_rect(center=(cx, cy - 20))
                screen.blit(draw_sprite, sprite_rect)
                
                # Label
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
                    # Update the correct list based on context
                    if self.context == "pc":
                        self.game.story_manager.pc_pokemon[self.team_index] = self.evolved_pokemon_obj
                    else:
                        self.game.story_manager.player_team[self.team_index] = self.evolved_pokemon_obj

                    # Add evolved form to the Pokédex
                    self.game.data.add_pokemon(self.evolved_pokemon_obj)
                    
                    # If it was a shiny evolution, also add the non-shiny version to the dex.
                    if self.evolved_pokemon_obj.is_shiny:
                        non_shiny_raw = self.game.loader.fetch_specific(
                            self.evolved_pokemon_obj.id,
                            form=self.evolved_pokemon_obj.form,
                            is_shiny=False
                        )
                        # Create a dummy pokemon just for the dex entry
                        non_shiny_pokemon = Pokemon(non_shiny_raw, self.game.assets, size_mult=0.1)
                        self.game.data.add_pokemon(non_shiny_pokemon)

                    # [UPDATE] Consume global catch count if this was a catch-triggered evolution
                    if self.consume_catch_count:
                        current_count = self.game.story_manager.catch_counts.get(self.pokemon.id, 0)
                        # Safety check to ensure we don't go negative, though logic should prevent it
                        if current_count >= 5:
                            self.game.story_manager.catch_counts[self.pokemon.id] = current_count - 5

        elif self.phase == "END" and self.timer <= 0:
            self._return()

    def _return(self):
        pygame.event.clear()
        if self.return_state:
            self.game.change_state(self.return_state)
        else:
            # Fallback
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
            if isinstance(msg, list): msg = " ".join(msg)

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

        info_x = 50
        y = 400
        font = self.game.assets.fonts["med"]

        texts = [
            f"Name: {self.pokemon.display_name}",
            f"Stage: {self.pokemon.effective_stage}",
            f"HP: {self.pokemon.current_hp}/{self.pokemon.get_max_hp()}",
            f"Types: {'/'.join(self.pokemon.types)}"
        ]

        # [UPDATE] Catches for evolution
        catch_count = self.game.story_manager.catch_counts.get(self.pokemon.id, 0)
        # Show global banked catches
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

        self.game.ui_manager.draw(self.game.screen)


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
            lines = ["Is that a Coin Case? That means you have money!", "Come on in, kid, have fun!", "Would you like to play PokeMath Infinite?"]
        else:
            lines = ["This place is too dangerous for kids.", "Come back when you have a COIN CASE!"]
            self.phase = "DENIED"

        self.dialogue_box = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(game),
            lines,
            game.assets.fonts["med"],
            visible=True,
            callback=self.go_back if not has_case else None
        )

        self.btn_yes = Button((0,0,0,0), "YES", game.assets.fonts["small"], self.start_infinite, bg_color=GREEN, visible=False, autosize=False)
        self.btn_no = Button((0,0,0,0), "NO", game.assets.fonts["small"], self.decline_infinite, bg_color=RED, visible=False, autosize=False)
        self.menu_buttons = []

    def _load_bg(self, game):
        path = os.path.join(game.assets.kanto_backgrounds_dir, "celadon_game_corner.png")
        box_top = Utils.get_full_dialogue_rect(game).top
        if os.path.exists(path):
            return pygame.transform.scale(pygame.image.load(path).convert(), (game.width, box_top))
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
        if not self.cleared:
            options.insert(0, ("STAIRS", self.check_stairs))

        self.clear_menu()
        btn_w, btn_h = 200, 60
        start_x = self.game.width // 2 - (len(options) * (btn_w + 20)) // 2
        for i, (text, cb) in enumerate(options):
            btn = Button((start_x + i * (btn_w + 20), self.game.height - 150, btn_w, btn_h), text, self.game.assets.fonts["tiny"], cb, autosize=False)
            self.menu_buttons.append(btn)
            self.game.ui_manager.add_element(btn)

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

        from src.states.battle import TrainerBattleState, TrainerIntroState
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
        if len(self.game.story_manager.player_team) < 6: self.game.story_manager.player_team.append(porygon)
        else: self.game.story_manager.pc_pokemon.append(porygon); msg.append("PORYGON was sent to BILL'S PC.")
        self.game.data.add_pokemon(porygon); self.game.data.save()
        self.dialogue_box.reset(msg); self.dialogue_box.callback = self.show_main_menu

    def handle_infinite_result(self, score):
        reward = score * 50
        self.game.story_manager.money += reward
        self.phase = "REWARD"
        self.dialogue_box.reset([f"Game Over! Your score: {score}", f"You received a reward of ${reward}!"])
        self.dialogue_box.callback = self.show_main_menu

    def clear_menu(self):
        for btn in self.menu_buttons:
            if btn in self.game.ui_manager.elements: self.game.ui_manager.elements.remove(btn)
        self.menu_buttons = []

    def go_back(self):
        self.clear_menu()
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        self.game.ui_manager.add_element(self.btn_yes)
        self.game.ui_manager.add_element(self.btn_no)
        if self.phase == "START": self.btn_yes.set_visibility(True); self.btn_no.set_visibility(True)
        elif self.phase == "VICTORY_SEQ": self.on_rocket_victory()

    def on_rocket_victory(self):
        if self.rocket_progress >= 4: self.give_porygon()
        else: self.dialogue_box.reset([f"Defeated Rocket Grunt {self.rocket_progress}!", "Another one is approaching!"]); self.dialogue_box.callback = self.next_rocket_battle

    def handle_events(self, events):
        for event in events: self.dialogue_box.handle_event(event)

    def update(self):
        self.dialogue_box.update()
        if self.phase == "START" or self.phase == "STAIRS_PROMPT":
            box = self.dialogue_box.rect
            self.btn_yes.rect = pygame.Rect(box.right - 280, box.bottom - 80, 120, 60)
            self.btn_no.rect = pygame.Rect(box.right - 140, box.bottom - 80, 120, 60)

    def draw(self):
        self.game.screen.fill(BLACK)
        self.game.screen.blit(self.bg, (0, 0))
        if self.npc_sprite: self.game.screen.blit(self.npc_sprite, self.npc_sprite.get_rect(center=(self.game.width//2, self.game.height*0.45)))
        self.dialogue_box.draw(self.game.screen)
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
        self.dialogue_box.reset(["Hah! You can't afford that!", "You're a pretty bad gamer, aren't you?", "Hehehe... stay away from the secret stairs!"])
        self.dialogue_box.callback = self.go_back

    def go_back(self): self.game.change_state(self.previous_state)
    def start(self): self.game.ui_manager.add_element(self.btn_buy); self.game.ui_manager.add_element(self.btn_back)
    def handle_events(self, events):
        for event in events: self.dialogue_box.handle_event(event)
    def update(self): self.dialogue_box.update()
    def draw(self):
        self.game.screen.fill(BLACK); self.game.screen.blit(self.bg, (0, 0))
        if self.clerk_sprite: self.game.screen.blit(self.clerk_sprite, self.clerk_sprite.get_rect(center=(self.game.width*0.3, self.game.height*0.45)))
        if self.porygon_sprite: self.game.screen.blit(self.porygon_sprite, self.porygon_sprite.get_rect(center=(self.game.width*0.7, self.game.height*0.45)))
        self.dialogue_box.draw(self.game.screen); self.game.ui_manager.draw(self.game.screen)


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
        self.generate_round()

    def generate_round(self):
        self.p_data = [Pokemon(self.game.loader.fetch_specific(random.choice(self.pool)), self.game.assets, size_mult=3.125) for _ in range(3)]
        limit = min(100, 20 + (self.score // 5) * 10)
        op = random.choice(["+", "-"])
        if op == "+":
            c = random.randint(4, limit); s = random.randint(2, min(10, c - 2)); a, b = s, c - s
        else:
            b = random.randint(2, 10); c = random.randint(2, max(2, limit - b)); a = b + c
        self.problem_str, self.correct_ans = f"{a} {op} {b} = ?", c
        opts = {c}
        while len(opts) < 3:
            f = c + random.choice([-3, -2, -1, 1, 2, 3])
            if f >= 0: opts.add(f)
        self.options = sorted(list(opts), key=lambda x: random.random())

    def get_cx(self, i): return (i * self.game.width // 3) + (self.game.width // 6)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and not self.ball_active and self.pause_timer == 0:
                for i, r in enumerate(self.answer_btn_rects):
                    if r.collidepoint(event.pos): self.process_answer(i); return

    def process_answer(self, idx):
        self.balls -= 1
        is_correct = self.options[idx] == self.correct_ans
        self.ball_active = True
        self.ball_pos, self.ball_target = [self.game.width // 2, self.game.height], [self.get_cx(idx), self.sprite_y]
        self.caught_idx = idx
        if is_correct:
            self.score += 1
            if self.score % 10 == 0: self.balls += 1

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
                else: self.generate_round()

    def draw(self):
        screen = self.game.screen
        screen.fill(BLACK)
        for s in self.stars:
            s[1] += s[2]
            if s[1] > self.game.height: s[1], s[0] = 0, random.randint(0, self.game.width)
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
                rect = pygame.Rect(self.get_cx(i) - 60, self.game.height * 0.65, 120, 80)
                self.answer_btn_rects[i] = rect
                pygame.draw.rect(screen, BLUE, rect, border_radius=15)
                Utils.draw_text_outline(screen, txt, self.game.assets.fonts["num"], WHITE, rect.centerx, rect.centery)
        if self.ball_active: screen.blit(self.ball_img, (self.ball_pos[0]-42, self.ball_pos[1]-42))


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
    def __init__(self, game, fossil_name, pokemon_id, previous_state):
        super().__init__(game)
        self.fossil_name = fossil_name
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
            self.phase = "GROW"; self.timer = 50
        elif self.phase == "GROW":
            self.scale += 0.06; self.alpha = max(0, self.alpha - 12)
            if self.timer <= 0: self.phase = "FLASH"; self.timer = 20
        elif self.phase == "FLASH":
            if self.timer <= 0:
                self.phase = "REVEAL"; self.timer = 60
                if self.evolved_pokemon_obj.cry: self.evolved_pokemon_obj.cry.play()
                self.scale = 4.0; self.alpha = 0
        elif self.phase == "REVEAL":
            self.scale = max(1.0, self.scale - 0.15); self.alpha = min(255, self.alpha + 20)
            if self.timer <= 0: self.phase = "END"; self.timer = 60; self._finalize_revival()
        elif self.phase == "END" and self.timer <= 0:
            pygame.event.clear()
            self.game.change_state(self.previous_state)

    def _finalize_revival(self):
        story = self.game.story_manager
        story.inventory[self.fossil_name] -= 1

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
                               lambda: game.change_state(previous_state), bg_color=RED)
        
        # Define all 28 official forms
        self.forms = ["normal", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", 
                      "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "question", "exclamation"]
        
        all_owned = self.game.story_manager.player_team + self.game.story_manager.pc_pokemon
        self.caught_forms = {p.form for p in all_owned if p.id == 201}

    def start(self):
        self.game.ui_manager.add_element(self.btn_back)

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
            
            is_caught = f in self.caught_forms
            pygame.draw.rect(screen, (45, 45, 60), (dx-60, dy-60, 120, 120), border_radius=10)
            
            if is_caught:
                img = self.game.assets.get_pokemon_image(201, f, False)
                if img:
                    img = pygame.transform.scale(img, (90, 90))
                    screen.blit(img, img.get_rect(center=(dx, dy)))
                
                lbl = f.upper() if len(f) == 1 else ("?" if f == "question" else "!")
                if f == "normal": lbl = "A"
                Utils.draw_text_outline(screen, lbl, self.game.assets.fonts["tiny"], WHITE, dx, dy + 75)
            else:
                Utils.draw_text_outline(screen, "?", self.game.assets.fonts["med"], (80, 80, 100), dx, dy)

        self.game.ui_manager.draw(screen)
