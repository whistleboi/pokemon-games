# [REF-0001: System Imports]
import pygame
import random
import io
import os
import math
import threading
import queue
import json
import sys
from abc import ABC, abstractmethod
import base64
from dataclasses import dataclass
from src.states.base import GameState
from src.ui.widgets import Button
from src.ui.panels import PartySlotUI
from src.ui.dialogue import ClassicDialogueBox
from src.ui.manager import UIManager
from src.utils import Utils
from src.config import WHITE, BLACK, GREEN, BLUE, RED, GOLD, GRAY, LIGHT_GRAY, GB_PANEL, GB_BORDER, GB_TEXT, VOLUME, DARK_RED
from src.pokemon.data import Pokemon


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
        if self.context == "battle_switch" and self.previous_state.player_pokemon is team[index]:
            self.game.show_dialogue([f"{team[index].display_name.upper()} is already in battle!"])
            return
        
        if self.context == "use_item":
            if self.on_select:
                self.on_select(index)
            return

        if self.context == "battle_switch" and team[index].current_hp <= 0:
            self.game.show_dialogue([f"{team[index].display_name.upper()} has no energy left!"])
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
            
            Utils.draw_text_outline(
                self.game.screen, self.message,
                self.game.assets.fonts["med"], WHITE,
                self.game.width // 2 - 100, self.bottom_rect.centery, outline_color=BLACK
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
                            if pygame.Rect(rx, ry, self.slot_size, self.slot_size).collidepoint(event.pos):
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
                self.party[index], self.party[self.selected_party_idx] = self.party[self.selected_party_idx], self.party[index]
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
                self.party[self.selected_party_idx], self.pc[index] = self.pc[index], self.party[self.selected_party_idx]
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
                
                Utils.draw_text_outline(self.game.screen, p.display_name, self.font, WHITE, rect.x + 90, rect.y + 25, align="left")
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
            
            can_use = (qty > 0 and self.current_page == 0)
            color = BLUE if can_use else GRAY
            callback = (lambda k=item_key: self.use_item(k)) if can_use else None
            
            icon = self.game.assets.get_item_image(item_key)
            
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

    def draw(self):
        self.game.screen.fill((40, 40, 60))
        
        page_title = self.pages[self.current_page]
        Utils.draw_text_outline(self.game.screen, page_title, self.game.assets.fonts["med"], WHITE, self.game.width//2, 50)
        
        if not self.item_buttons:
            Utils.draw_text_outline(self.game.screen, "No Items", self.game.assets.fonts["s_med"], GRAY, self.game.width//2, self.game.height//2)
            
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
        self.btn_shiny_toggle = Button(
            rect=(game.width - 250, 30, 220, 70),
            text="SHINIES",
            font=game.assets.fonts["small"],
            callback=self.toggle_shiny_filter,
            bg_color=BLUE,
        )
        btn_y = self.btn_shiny_toggle.rect.bottom + 10
        self.btn_dev = Button(
            rect=(game.width - 250, btn_y, 220, 60),
            text="DEV MODE",
            font=game.assets.fonts["tiny"],
            callback=self.toggle_dev_mode,
            bg_color=BLACK,
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
        self.tab_buttons = [
            self.btn_tab_normal,
            self.btn_tab_mega,
            self.btn_tab_gmax,
            self.btn_tab_alt,
            self.btn_tab_boss,
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
        self.game.ui_manager.add_element(self.btn_dev)
        for btn in self.tab_buttons:
            self.game.ui_manager.add_element(btn)

    def refresh_dex(self):
        if self.current_tab == "boss":
            source_data = self.game.data.data.get("defeated_bosses", {})
            self.full_dex = list(source_data.values())
        elif self.current_tab == "normal":
            # Kanto 1-151 Grid
            self.full_dex = []
            caught_data = self.game.data.data.get("pokedex", {})
            seen_ids = self.game.data.data.get("seen_pokemon", [])
            
            # Force 1-151 slots
            for i in range(1, 152):
                p_id = i
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
            
            return
        else:
            source_data = self.game.data.data.get("pokedex", {})
            self.full_dex = [
                p
                for p in source_data.values()
                if p.get("form", "normal") == self.current_tab
            ]

        if self.show_shinies_only:
            self.full_dex = [p for p in self.full_dex if p["shiny"]]

        self.full_dex.sort(key=lambda x: x.get("id", 0))

    def set_tab(self, tab_name):
        self.current_tab = tab_name
        self.page = 0
        self.refresh_dex()

    def toggle_shiny_filter(self):
        self.show_shinies_only = not self.show_shinies_only
        self.page = 0
        self.refresh_dex()
        self.btn_shiny_toggle.bg_color = GOLD if self.show_shinies_only else BLUE

    def toggle_dev_mode(self):
        if not self.game.loader.dev_shiny_mode:
            if self.do_parental_check():
                self.game.loader.dev_shiny_mode = True
                self.btn_dev.bg_color = GREEN
        else:
            self.game.loader.dev_shiny_mode = False
            self.btn_dev.bg_color = BLACK

    def do_parental_check(self):
        a = random.randint(12, 19)
        b = random.randint(3, 9)
        ans = a * b
        options = {ans}
        while len(options) < 10:
            fake = ans + random.randint(-12, 12)
            if fake > 0 and fake != ans:
                options.add(fake)

        options_list = list(options)
        random.shuffle(options_list)

        checking = True

        cx, cy = self.game.width // 2, self.game.height // 2

        bw, bh = 500, 350
        box_rect = pygame.Rect(cx - bw // 2, cy - bh // 2, bw, bh)

        btn_w, btn_h = 70, 45
        gap_x, gap_y = 15, 20

        total_grid_w = (5 * btn_w) + (4 * gap_x)
        start_x = cx - (total_grid_w // 2)
        start_y = box_rect.top + 160

        buttons = []
        for i, val in enumerate(options_list):
            row = i // 5
            col = i % 5
            bx = start_x + col * (btn_w + gap_x)
            by = start_y + row * (btn_h + gap_y)
            buttons.append((pygame.Rect(bx, by, btn_w, btn_h), val))

        while checking:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if not box_rect.collidepoint(event.pos):
                        return False

                    for rect, val in buttons:
                        if rect.collidepoint(event.pos):
                            return val == ans

            self.draw()

            pygame.draw.rect(self.game.screen, WHITE, box_rect, border_radius=15)
            pygame.draw.rect(self.game.screen, BLACK, box_rect, 4, border_radius=15)

            Utils.draw_text_outline(
                self.game.screen,
                self.game.assets.get_text("parental_check"),
                self.game.assets.fonts["med"],
                BLACK,
                cx,
                box_rect.top + 40,
                outline_color=WHITE,
            )
            Utils.draw_text_outline(
                self.game.screen,
                f"{a} x {b} = ?",
                self.game.assets.fonts["big"],
                BLACK,
                cx,
                box_rect.top + 100,
                outline_color=WHITE,
            )

            mouse_pos = pygame.mouse.get_pos()
            for rect, val in buttons:
                is_hover = rect.collidepoint(mouse_pos)
                bg = LIGHT_GRAY if is_hover else WHITE
                pygame.draw.rect(self.game.screen, bg, rect, border_radius=8)
                pygame.draw.rect(self.game.screen, BLACK, rect, 2, border_radius=8)
                Utils.draw_text_outline(
                    self.game.screen,
                    str(val),
                    self.game.assets.fonts["s_med"],
                    BLACK,
                    rect.centerx,
                    rect.centery,
                    outline_color=WHITE,
                )

            pygame.display.flip()
            self.game.clock.tick(25)

        return False

    def confirm_wipe_action(self):
        self.confirm_wipe()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.btn_next.collidepoint(event.pos) and (self.page + 1) * 12 < len(self.full_dex):
                    self.page += 1
                elif self.btn_prev.collidepoint(event.pos) and self.page > 0:
                    self.page -= 1
                else:
                    for r, p_id in self.dex_btns:
                        if r.collidepoint(event.pos):
                            try:
                                cry_path = self.game.assets.get_cry(p_id)
                                cry_sound = pygame.mixer.Sound(cry_path)
                                cry_sound.set_volume(VOLUME)
                                cry_sound.play()
                            except Exception:
                                pass

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
                
                Utils.draw_text_outline(
                    screen,
                    f"#{p_entry['id']}",
                    self.game.assets.fonts["tiny"],
                    BLACK,
                    rect.centerx,
                    rect.top - 20,
                    outline_color=WHITE,
                )
                Utils.draw_text_outline(
                    screen,
                    p_entry["name"].upper(),
                    self.game.assets.fonts["tiny"],
                    BLACK,
                    rect.centerx,
                    rect.bottom + 15,
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
        self.btn_dev.bg_color = GREEN if self.game.loader.dev_shiny_mode else BLACK

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
        self.btn_retry = Button(
            rect=(game.width // 2 - 200, game.height * 0.60, 400, 80),
            text="RETRY",
            font=game.assets.fonts["s_med"],
            callback=self.retry_game,
            bg_color=GREEN,
        )
        self.btn_reset = Button(
            rect=(game.width // 2 - 200, game.height * 0.72, 400, 80),
            text="RESET STREAK",
            font=game.assets.fonts["s_med"],
            callback=self.reset_streak,
            bg_color=DARK_RED,
        )
        self.btn_exit = Button(
            rect=(game.width // 2 - 200, game.height * 0.84, 400, 80),
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
        self.earned_badges = game.story_manager.badges
        self.btn_back = Button(
            rect=(30, 30, 140, 70),
            text="BACK",
            font=game.assets.fonts["small"],
            callback=self.go_back,
            bg_color=RED,
        )
        # Kanto Badge Map (Name -> Index 1-8)
        self.badge_map = {
            "BOULDER": 1, "CASCADE": 2, "THUNDER": 3, "RAINBOW": 4,
            "SOUL": 5, "MARSH": 6, "VOLCANO": 7, "EARTH": 8
        }
        
        self.badge_sprites = {}
        for i in range(1, 9):
            img = game.assets.get_badge_image(i)
            if img:
                self.badge_sprites[i] = pygame.transform.scale(img, (100, 100))

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
        width, height = self.game.width, self.game.height
        screen.fill(DARK_RED)

        case_rect = pygame.Rect(width * 0.1, height * 0.1, width * 0.8, height * 0.8)
        pygame.draw.rect(screen, (50, 50, 50), case_rect, border_radius=20)
        Utils.draw_text_outline(
            screen,
            "BADGE CASE",
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
            
            # Calculate center of cell
            cx = grid_rect.x + (col + 0.5) * cell_w
            cy = grid_rect.y + (row + 0.5) * cell_h + 10
            
            sprite = self.badge_sprites.get(i)
            if sprite:
                # Check if earned
                earned = any(self.badge_map.get(b_name) == i for b_name in self.earned_badges)
                
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
        self, game, pokemon_to_evolve, evolution_id, team_index, next_form="normal", context="party", return_state=None
    ):
        super().__init__(game)
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
            Utils.draw_text_outline(
                self.game.screen,
                self.game.assets.get_text("evolving", name=self.original_name),
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
        
        for t in texts:
            Utils.draw_text_outline(self.game.screen, t, font, WHITE, info_x, y, align="left")
            y += 50
            
        self.game.ui_manager.draw(self.game.screen)
