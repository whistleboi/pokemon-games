# [REF-0001: System Imports]
import pygame
import os
import sys
from src.states.base import GameState
from src.ui.widgets import Button, ItemCard
from src.ui.panels import PartySlotUI, CommandButton
from src.ui import theme
from src.ui.dialogue import ClassicDialogueBox
from src.utils import Utils
from src.config import WHITE, BLACK, GREEN, BLUE, RED, GOLD, GRAY, LIGHT_GRAY, VOLUME, DARK_RED
from src.pokemon.data import Pokemon
from src.pokemon.poffin import BERRY_PRICE
from src.pokemon.contest import (feebas_ready, feed_pokeblock, POKEBLOCKS, POKEBLOCK_PRICE, CATEGORIES,
                                 CATEGORY_COLOR, MAX_CONDITION, FEEBAS_BEAUTY)
from src.states.battle import TrainerBattleState, TrainerIntroState
from src.pokemon import items as itemlib
from src.pokemon import forms
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
    """The Journal (menu redesign, uncluttered): a list of missions at the left, the one picked
    in full at the right (its story, its reward, GUIDE ME), the mission being guided in the text
    box at the bottom."""

    ROWS = 7  # list rows on show

    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.missions = game.story_manager.get_all_journal_entries()
        self.missions.sort(key=lambda x: 0 if x["status"] == "ACTIVE" else 1)
        self.scroll_idx = 0
        self.selected = 0
        from src.world import guide
        tracked = guide.tracked_mission(game)
        if tracked:  # open on the mission being guided
            self.selected = next((i for i, m in enumerate(self.missions) if m["id"] == tracked.get("id")), 0)
            self.scroll_idx = max(0, min(self.selected, len(self.missions) - self.ROWS))

        f = game.assets.fonts
        H = theme.HEADER_H
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.go_back, bg_color=theme.BACK,
                                      autosize=False)
        self.bar_rect = pygame.Rect(16, game.height - 86, game.width - 32, 78)
        top = H + 16
        self.list_rect = pygame.Rect(24, top, 470, self.bar_rect.top - 12 - top)
        self.detail_rect = pygame.Rect(self.list_rect.right + 16, top, game.width - 24 - self.list_rect.right - 16,
                                       self.list_rect.h)
        arrow_y = self.list_rect.bottom - 52
        self.btn_up = CommandButton((self.list_rect.x + 12, arrow_y, 110, 42), "UP", f["label"],
                                    lambda: self.scroll(-1), bg_color=theme.ACCENT["journal"], autosize=False)
        self.btn_down = CommandButton((self.list_rect.right - 12 - 110, arrow_y, 110, 42), "DOWN", f["label"],
                                      lambda: self.scroll(1), bg_color=theme.ACCENT["journal"], autosize=False)
        d = self.detail_rect
        self.btn_guide = CommandButton((d.right - 24 - 240, d.bottom - 24 - 62, 240, 62), "GUIDE ME", f["button"],
                                       self.toggle_guide, bg_color=theme.RUN, autosize=False)
        self.guide_buttons = [self.btn_guide]

    def row_rect(self, k):
        r = self.list_rect
        h = (r.h - 12 - 64 - (self.ROWS - 1) * 8) // self.ROWS
        return pygame.Rect(r.x + 12, r.y + 12 + k * (h + 8), r.w - 24, h)

    def scroll(self, step):
        self.scroll_idx = max(0, min(max(0, len(self.missions) - self.ROWS), self.scroll_idx + step))

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def start(self):
        for btn in (self.btn_back, self.btn_up, self.btn_down, self.btn_guide):
            self.game.ui_manager.add_element(btn)
        for m in self.missions:
            if m["id"] not in self.game.story_manager.notified_missions:
                self.game.story_manager.notified_missions.append(m["id"])
        self._guide_layout()

    def _mission(self):
        return self.missions[self.selected] if 0 <= self.selected < len(self.missions) else None

    def _guide_layout(self):
        """GUIDE ME on the picked mission (when it's active): the route guide and the Town Map
        point to it (src/world/guide.py); GUIDING turns it off."""
        from src.world import guide
        m = self._mission()
        tracked = guide.tracked_mission(self.game)
        on = bool(m and tracked and tracked.get("id") == m["id"])
        self.btn_guide.text = "GUIDING" if on else "GUIDE ME"
        self.btn_guide.bg_color = theme.BAG if on else theme.RUN
        self.btn_guide.set_visibility(bool(m) and m["status"] == "ACTIVE")

    def toggle_guide(self):
        from src.world import guide
        m = self._mission()
        if m:
            tracked = guide.tracked_mission(self.game)
            self.track(m, bool(tracked) and tracked.get("id") == m["id"])

    def track(self, mission, on):
        from src.world import guide
        story = self.game.story_manager
        story.tracked_mission = "off" if on else mission["id"]
        guide._CACHE.clear()
        self._guide_layout()
        if not on:
            goal = guide.mission_target(self.game, mission)
            prog = self.game.loader.area_data.get("STORY_PROGRESSION", {})
            where = prog.get(goal, {}).get("route_name") if goal else None
            self.game.show_dialogue([f"Guiding you to {where}! Follow the gold buttons." if where
                                     else "This mission doesn't point to one place. Explore to find it!"])

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
                self.scroll(-1 if event.button == 4 else 1)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for k in range(self.ROWS):
                    i = self.scroll_idx + k
                    if i < len(self.missions) and self.row_rect(k).collidepoint(event.pos):
                        self.selected = i
                        self._guide_layout()
                        return

    def update(self):
        pass

    def draw(self):
        from src.ui.dialogue import wrap_text
        from src.world import guide
        screen = self.game.screen
        f = self.game.assets.fonts
        accent = theme.ACCENT["journal"]
        theme.menu_background(screen, accent, "JOURNAL", f["button"], title_x=176)
        active = sum(1 for m in self.missions if m["status"] == "ACTIVE")
        Utils.draw_text_outline(screen, f"{active} active   {len(self.missions) - active} done", f["button"], WHITE,
                                self.game.width - 24, theme.HEADER_H // 2 - 4, align="right",
                                outline_color=theme.shade(accent, 0.45), thickness=3)
        tracked = guide.tracked_mission(self.game)
        mouse = pygame.mouse.get_pos()

        # The list: tag, title, a dot for its status.
        theme.draw_panel(screen, self.list_rect)
        if not self.missions:
            theme.shadow_text(screen, "No missions yet.", f["label"], self.list_rect.centerx, self.list_rect.y + 60,
                              color=(220, 226, 244), shadow=theme.MENU_BG, align="center")
        for k in range(self.ROWS):
            i = self.scroll_idx + k
            if i >= len(self.missions):
                break
            m, r = self.missions[i], self.row_rect(k)
            done = m["status"] != "ACTIVE"
            theme.card(screen, r, hover=r.collidepoint(mouse), selected=i == self.selected, accent=accent,
                       fill=(220, 224, 234) if done else theme.TEXTBOX, radius=10)
            story = m["type"] == "MAIN"
            chip = pygame.Rect(r.x + 10, r.centery - 12, 84, 24)
            pygame.draw.rect(screen, theme.FIGHT if story else theme.RUN, chip, border_radius=12)
            Utils.draw_text_outline(screen, "STORY" if story else "SIDE", f["caption"], WHITE,
                                    chip.centerx, chip.centery, outline_color=(30, 30, 40), thickness=1)
            title = m["text"]
            tw = r.right - 40 - chip.right - 12
            from src.ui.slot_list import fit
            theme.shadow_text(screen, fit(f["label"], title, tw), f["label"], chip.right + 12,
                              r.centery - f["label"].get_height() // 2, color=(120, 126, 146) if done else theme.TEXT)
            dot = theme.POKEMON if done else (theme.BAG if tracked and tracked.get("id") == m["id"] else theme.RUN)
            pygame.draw.circle(screen, dot, (r.right - 20, r.centery), 8)
        if len(self.missions) > self.ROWS:
            first, last = self.scroll_idx + 1, min(len(self.missions), self.scroll_idx + self.ROWS)
            Utils.draw_text_outline(screen, f"{first}-{last} of {len(self.missions)}", f["label"], WHITE,
                                    self.list_rect.centerx, self.btn_up.rect.centery)
        self.btn_up.set_visibility(self.scroll_idx > 0)
        self.btn_down.set_visibility(self.scroll_idx + self.ROWS < len(self.missions))

        # The picked mission in full.
        d = self.detail_rect
        m = self._mission()
        theme.card(screen, d, radius=16)
        if m:
            story = m["type"] == "MAIN"
            chip = pygame.Rect(d.x + 24, d.y + 22, 96, 30)
            pygame.draw.rect(screen, theme.FIGHT if story else theme.RUN, chip, border_radius=15)
            Utils.draw_text_outline(screen, "STORY" if story else "SIDE", f["caption"], WHITE, chip.centerx,
                                    chip.centery, outline_color=(30, 30, 40), thickness=1)
            st_color = theme.POKEMON if m["status"] == "COMPLETED" else theme.BAG
            st = pygame.Rect(0, 0, f["caption"].size(m["status"])[0] + 24, 30)
            st.topleft = (chip.right + 10, chip.y)
            pygame.draw.rect(screen, st_color, st, border_radius=15)
            tc, oc = theme.text_on(st_color)
            Utils.draw_text_outline(screen, m["status"], f["caption"], tc, st.centerx, st.centery,
                                    outline_color=oc, thickness=1)
            y = chip.bottom + 18
            for row in wrap_text(m["text"], f["s_med"], d.w - 48)[:2]:
                theme.shadow_text(screen, row, f["s_med"], d.x + 24, y)
                y += 34
            y += 10
            pygame.draw.line(screen, (214, 218, 228), (d.x + 24, y), (d.right - 24, y), 2)
            y += 16
            for row in wrap_text(m.get("desc", ""), f["label"], d.w - 48)[:7]:
                theme.shadow_text(screen, row, f["label"], d.x + 24, y)
                y += 28
            reward = m.get("reward")
            if reward and reward != "None":
                ry = d.bottom - 24 - 62 - 58
                theme.shadow_text(screen, "Reward", f["caption"], d.x + 24, ry, color=(110, 116, 136))
                theme.shadow_text(screen, str(reward), f["label"], d.x + 24, ry + 22, color=(40, 110, 170))
        else:
            theme.shadow_text(screen, "Explore to find missions!", f["s_med"], d.centerx, d.centery, align="center")

        # The bar: who's being guided.
        line = f"Guiding: {tracked['text']}" if tracked else "Pick a mission, then GUIDE ME to follow it."
        from src.ui.slot_list import fit
        bf = f["s_med"]
        theme.draw_textbox(screen, self.bar_rect)
        theme.shadow_text(screen, fit(bf, line, self.bar_rect.w - 64), bf, self.bar_rect.x + 32,
                          self.bar_rect.centery - bf.get_height() // 2 - 2)

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
            self.game.change_state(PokemonDetailState(self.game, pkmn, self))
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
        if self.popup_active:  # the menu over the cards, then its buttons on top
            team = getattr(self.game.story_manager, "player_team", [])
            name = team[self.selected_slot_index].display_name.upper() if 0 <= self.selected_slot_index < len(team) else ""
            theme.popup_panel(screen, self.popup_rect, name, f["label"])
            self.btn_summary.draw(screen)
            self.btn_switch.draw(screen)


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
        self.btn_yes = CommandButton((cx - 150, cy + 50, 140, 60), "BUY", game.assets.fonts["button"], self.confirm_purchase, bg_color=theme.POKEMON, autosize=False, visible=False)
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

        self._build_ui()

    WEATHER_ROCKS = {"RAIN": "DAMP_ROCK", "SUN": "HEAT_ROCK", "SAND": "SMOOTH_ROCK", "SNOW": "ICY_ROCK"}

    # Never on an ordinary shelf. The Up-Grade is sold only at Veilstone (Sinnoh) and the Crystal Stone
    # only at Pummelo (Orange Islands), through those areas' "extra_stock".
    NEVER_SOLD = {"UPGRADE", "UP_GRADE", "CRYSTAL_STONE"}

    def _shop_items(self):
        return [i for i in self._stock_items() if i not in self.NEVER_SOLD] + self._extra_stock()

    def _extra_stock(self):
        """An area's own extra shelf ("extra_stock": [{"item", "condition"}]): Pummelo Island sells the
        Crystal Stone once you're the Orange League Champion."""
        if self.stock is not None:
            return []
        flags = self.game.story_manager.story_flags
        return [e["item"] for e in self.game.story_manager.get_current_area_data().get("extra_stock", [])
                if not e.get("condition") or flags.get(e["condition"])]

    def _stock_items(self):
        if self.stock is not None:
            return list(self.stock)
        area = self.game.story_manager.current_area_key
        items = self._town_stock()
        if self._is_department_store():  # X items, drinks, evolution items, Rare Candy
            evo_items = sorted(i for i in self.game.loader.evolution_map.get("EVOLUTION_ITEMS", {})
                               if self._item_allowed(i))
            items += [i for i in itemlib.DEPARTMENT + ["RARE_CANDY", "EVERSTONE"] + evo_items if i not in items]
        return items + self._regional_weather_rocks() + self._contest_items()

    def _town_stock(self):
        """The games' Poke Mart counter (Gen 4 on), by the region's badges: Poke Balls, Potions and
        the status heals first, then Great Balls / Super Potions (1 badge), Hyper Potions and Revives
        (3), Ultra Balls and Full Heals (5), Max Potions (7), Full Restores (8); the second counter's
        balls (Net, Nest, Quick, Dusk, Heal, Dive, Repeat, Timer, Luxury) by badges too. The
        Everstone from 2 badges and Rare Candy at the League are this game's own."""
        story = self.game.story_manager
        badges = len(story.badges.get(story.get_current_region(), []))
        if story.is_region_champion(story.get_current_region()):
            badges = 8
        items = itemlib.standard_stock(badges)
        if badges >= 2:
            items.append("EVERSTONE")
        from src.states.overworld import is_league
        if is_league(story.get_current_area_data().get("gym")):
            items += [i for i in ("REVIVE", "RARE_CANDY", "FULL_RESTORE", "MAX_POTION") if i not in items]
        return items

    def _item_allowed(self, item):
        """An evolution item is only sold once something it evolves can evolve here
        (Kanto and Johto keep later regions' items until those regions are played)."""
        targets = self.game.loader.evolution_map.get("EVOLUTION_ITEMS", {}).get(item) or {}
        if not isinstance(targets, dict) or not targets:
            return True
        from src.pokemon import evolution
        ids = [self.game.name_to_id.get(str(t).split("_")[0].upper()) for t in targets.values()]
        return any(evolution.evolution_allowed(self.game, i) for i in ids if i)

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

    # ---------------------------------------------------------------- prices
    BASE_PRICES = {"POKE_BALLS": 1000, "RARE_CANDY": 10000, "POTION": 500, "FULL_HEAL": 600,
                   "REVIVE": 1000, "EVERSTONE": 3000}

    def _price(self, item):
        if itemlib.price(item):
            return itemlib.price(item)
        if item in self.BASE_PRICES:
            return self.BASE_PRICES[item]
        return (2000 if item in self.WEATHER_ROCKS.values()
                else 5000 if item.endswith(("ITE", "ITE_X", "ITE_Y"))
                else POKEBLOCK_PRICE if item in POKEBLOCKS
                else BERRY_PRICE if item.endswith("_BERRY") else 10000)

    def _name(self, item, qty=1):
        if item == "POKE_BALLS":
            return "Poké Balls (x5)" if qty == 1 else f"{qty} packs of 5 Poké Balls"
        from src.pokemon import catching
        name = (catching.label(item).title() if item in catching.BALLS
                else item.replace("_", " ").title().replace(" Fossil", "").replace("X Sp ", "X Sp. "))
        return name if qty == 1 else f"{qty} x {name}"

    def _icon(self, item, size=48):
        icon = (self.game.assets.ui_ball if item == "POKE_BALLS"
                else self.game.assets.get_item_image(item) or self.game.assets.get_item_image(item.replace("X_SP_", "X_SP_")
                                                                                              .replace("PARALYZE", "PARLYZ"))
                or (self.game.assets.get_item_image("POTION") if item in itemlib.MEDICINE else None))
        return pygame.transform.scale(icon, (size, size)) if icon else None

    def _sellable(self):
        """Items in the Bag the Mart will buy back (never key items, gifts or Mega Stones)."""
        story = self.game.story_manager
        key_items = set(self.game.loader.area_data.get("GAME_CONFIG", {}).get("KEY_ITEMS", []))
        evo_items = set(self.game.loader.evolution_map.get("EVOLUTION_ITEMS", {}).keys())
        shop_kinds = (set(self.BASE_PRICES) | evo_items | set(self.WEATHER_ROCKS.values())
                      | set(POKEBLOCKS) | set(itemlib.MEDICINE) | set(itemlib.BATTLE) | set(itemlib.FIELD)
                      | set(itemlib.BALL_PRICES)) - {"POKE_BALLS", "PREMIER_BALL"}
        return [k for k, q in sorted(story.inventory.items())
                if q > 0 and k not in key_items and k not in self.NEVER_SOLD
                and (k in shop_kinds or k.endswith("_BERRY"))]

    def _have(self, item):
        story = self.game.story_manager
        return story.balls_left if item == "POKE_BALLS" else story.inventory.get(item, 0)

    # ---------------------------------------------------------------- layout
    def _build_ui(self):
        """The menu frame in the Mart's blue: EXIT, BUY / SELL and the money in the header, the
        shelf as white item cards, the text box below for what the item under the pointer does
        (and the clerk's words); the quantity on a card over the shelf."""
        g = self.game
        w = g.width
        fonts = g.assets.fonts
        H = theme.HEADER_H
        self.mode = "BUY"
        self.qty = 1
        self.panel = pygame.Rect(24, H + 16, w - 48, self.bottom_rect.top - 12 - H - 16)
        self.btn_back = CommandButton((16, 14, 140, 56), "EXIT", fonts["button"], self.exit_shop,
                                      bg_color=theme.BACK, autosize=False)
        self.btn_buy_tab = CommandButton((w // 2 - 170, 14, 160, 56), "BUY", fonts["button"],
                                         lambda: self.set_mode("BUY"), bg_color=theme.TAB_OFF, autosize=False)
        self.btn_sell_tab = CommandButton((w // 2 + 10, 14, 160, 56), "SELL", fonts["button"],
                                          lambda: self.set_mode("SELL"), bg_color=theme.TAB_OFF, autosize=False)
        foot = self.panel.bottom - 50
        self.btn_prev = CommandButton((self.panel.x, foot, 80, 50), "<", fonts["button"], self.prev_page,
                                      bg_color=theme.ACCENT["mart"], autosize=False)
        self.btn_next = CommandButton((self.panel.right - 80, foot, 80, 50), ">", fonts["button"], self.next_page,
                                      bg_color=theme.ACCENT["mart"], autosize=False)
        self.card_h = 70
        rows = max(1, (self.panel.h - 62 + 12) // (self.card_h + 12))
        self.items_per_page = rows * 2
        # the quantity card
        self.qty_rect = pygame.Rect(0, 0, min(760, w - 60), 380)
        self.qty_rect.center = (w // 2, (self.panel.top + self.bottom_rect.top) // 2)
        q = self.qty_rect
        by = q.y + 150
        self.qty_buttons = [
            CommandButton((q.x + 40 + k * 120, by, 110, 56), label, fonts["button"], cb,
                          bg_color=theme.RUN, autosize=False)
            for k, (label, cb) in enumerate((("-1", lambda: self.change_qty(-1)), ("+1", lambda: self.change_qty(1)),
                                             ("+10", lambda: self.change_qty(10)), ("MAX", self.max_qty)))]
        self.btn_yes = CommandButton((q.centerx - 230, q.bottom - 76, 210, 60), "BUY", fonts["button"],
                                     self.confirm_purchase, bg_color=theme.POKEMON, autosize=False)
        self.btn_no = CommandButton((q.centerx + 20, q.bottom - 76, 210, 60), "CANCEL", fonts["button"],
                                    self.cancel_purchase, bg_color=theme.BACK, autosize=False)

    def set_mode(self, mode):
        self.mode = mode
        self.current_page = 0
        self.cancel_purchase()

    def _list(self):
        return self._shop_items() if self.mode == "BUY" else self._sellable()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_buttons()

    def next_page(self):
        if (self.current_page + 1) * self.items_per_page < len(self._list()):
            self.current_page += 1
            self.refresh_buttons()

    def refresh_buttons(self):
        ui = self.game.ui_manager
        ui.elements.clear()
        self.btn_buy_tab.bg_color = theme.BAG if self.mode == "BUY" else theme.TAB_OFF
        self.btn_sell_tab.bg_color = theme.BAG if self.mode == "SELL" else theme.TAB_OFF
        for b in (self.btn_back, self.btn_buy_tab, self.btn_sell_tab):
            ui.add_element(b)
        self.shop_buttons = []
        if self.phase == "QTY":
            self.btn_yes.text = self.mode
            self.btn_prev.set_visibility(False)
            self.btn_next.set_visibility(False)
            for b in self.qty_buttons + [self.btn_yes, self.btn_no]:
                b.set_visibility(True)
                ui.add_element(b)
        else:
            for b in self.qty_buttons + [self.btn_yes, self.btn_no]:
                b.set_visibility(False)
            items = self._list()
            pages = max(1, (len(items) + self.items_per_page - 1) // self.items_per_page)
            self.current_page = min(self.current_page, pages - 1)
            self.btn_prev.set_visibility(self.current_page > 0)
            self.btn_next.set_visibility(self.current_page < pages - 1)
            ui.add_element(self.btn_prev)
            ui.add_element(self.btn_next)
            start = self.current_page * self.items_per_page
            col_w = (self.panel.w - 12) // 2
            for i, item in enumerate(items[start:start + self.items_per_page]):
                r, c = divmod(i, 2)
                rect = (self.panel.x + c * (col_w + 12), self.panel.y + r * (self.card_h + 12), col_w, self.card_h)
                btn = Button(rect, "", self.game.assets.fonts["tiny"],
                             lambda k=item: self.init_purchase(k), bg_color=(52, 98, 190), autosize=False)
                btn.item_key = item
                self.shop_buttons.append(btn)
                ui.add_element(btn)
        ui.add_element(self.dialogue_box)

    # ---------------------------------------------------------------- buying and selling
    def _unit_price(self, item):
        return self._price(item) if self.mode == "BUY" else self._price(item) // 2

    def _max_qty(self):
        item = self.pending_item
        if self.mode == "SELL":
            return max(1, self._have(item))
        price = self._unit_price(item)
        afford = self.game.story_manager.money // price if price else 99
        if item == "POKE_BALLS":
            room = (self.game.story_manager.MAX_ITEMS - self._have(item)) // 5
        else:
            room = self.game.story_manager.MAX_ITEMS - self._have(item)
        return max(1, min(99, afford, room))

    def init_purchase(self, item_key, price=None):
        self.pending_item = item_key
        self.pending_cost = self._unit_price(item_key) if price is None else price
        self.qty = 1
        self.phase = "QTY"
        self.dialogue_box.set_visibility(False)
        self.refresh_buttons()

    def change_qty(self, step):
        self.qty = max(1, min(self._max_qty(), self.qty + step))

    def max_qty(self):
        self.qty = self._max_qty()

    def confirm_purchase(self):
        story = self.game.story_manager
        item, qty = self.pending_item, self.qty
        total = self._unit_price(item) * qty
        if self.mode == "SELL":
            qty = min(qty, self._have(item))
            total = self._unit_price(item) * qty
            story.inventory[item] = story.inventory.get(item, 0) - qty
            story.money += total
            lines = [f"You sold {self._name(item, qty)} for ${total:,}.", f"You now have ${story.money:,}."]
        elif story.money < total:
            lines = ["You don't have enough money!",
                     f"That's ${total:,}, and you have ${story.money:,}. You need ${total - story.money:,} more."]
        else:
            if item == "POKE_BALLS":
                if story.MAX_ITEMS - story.balls_left < 5 * qty:
                    self._show([f"Your Bag can only hold {story.MAX_ITEMS} Poké Balls!"])
                    return
                story.balls_left += 5 * qty
                if qty >= 2:
                    story.add_item("PREMIER_BALL", qty // 2)
            elif story.add_item(item, qty) < qty:
                self._show([f"You can't carry more than {story.MAX_ITEMS} of those!"])
                return
            story.money -= total
            if self.game.assets.heal_sfx:
                self.game.assets.heal_sfx.play()
            lines = [f"You bought {self._name(item, qty)} for ${total:,}!", f"You have ${story.money:,} left."]
            if item == "POKE_BALLS" and qty >= 2:
                lines.insert(1, f"You also got {qty // 2} Premier Ball{'s' if qty >= 4 else ''} as a bonus!")
        self._show(lines)

    def _show(self, lines):
        self.phase = "SHOP"
        self.pending_item = None
        self.refresh_buttons()
        self.dialogue_box.reset(lines)
        self.dialogue_box.callback = self.cancel_purchase
        self.dialogue_box.set_visibility(True)

    def cancel_purchase(self):
        self.phase = "SHOP"
        self.dialogue_box.set_visibility(False)
        self.pending_item = None
        self.refresh_buttons()

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

        img = game.assets.get_generic_background("mart")
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

    def update(self):
        if self.dialogue_box.visible:
            self.dialogue_box.update()

    # ---------------------------------------------------------------- drawing
    def draw(self):
        screen, fonts = self.game.screen, self.game.assets.fonts
        w = self.game.width
        if self.phase == "DIALOGUE":  # the clerk's welcome, in the shop itself
            screen.fill(BLACK)
            screen.blit(self.bg, (0, 0))
            self.game.ui_manager.draw(screen)
            return
        accent = theme.ACCENT["mart"]
        theme.menu_background(screen, accent, "POKé MART", fonts["button"], title_x=176)
        story = self.game.story_manager
        Utils.draw_text_outline(screen, f"${story.money:,}", fonts["button"], WHITE, w - 24, theme.HEADER_H // 2 - 4,
                                align="right", outline_color=theme.shade(accent, 0.45), thickness=3)
        for b in (self.btn_back, self.btn_buy_tab, self.btn_sell_tab):
            b.draw(screen)

        hovered = None
        if self.phase == "QTY":
            self._draw_qty()
        else:
            mouse = pygame.mouse.get_pos()
            for btn in self.shop_buttons:
                self._draw_card(btn)
                if btn.rect.collidepoint(mouse):
                    hovered = btn.item_key
            items = self._list()
            pages = max(1, (len(items) + self.items_per_page - 1) // self.items_per_page)
            if not items:
                msg = "Nothing in your Bag to sell." if self.mode == "SELL" else "Sold out!"
                theme.shadow_text(screen, msg, fonts["s_med"], self.panel.centerx, self.panel.centery,
                                  color=(200, 206, 222), shadow=theme.MENU_BG, align="center")
            elif pages > 1:
                self.btn_prev.draw(screen)
                self.btn_next.draw(screen)
                Utils.draw_text_outline(screen, f"Page {self.current_page + 1}/{pages}", fonts["label"], WHITE,
                                        self.panel.centerx, self.btn_prev.rect.centery)
        if self.dialogue_box.visible:
            self.dialogue_box.draw(screen)
        else:  # the text box: what the item under the pointer does
            if hovered:
                line = f"{self._name(hovered)}: {itemlib.describe(hovered) or 'A useful item.'}"
            elif self.phase == "QTY":
                line = "How many? Then BUY." if self.mode == "BUY" else "How many? Then SELL."
            else:
                line = "What would you like?" if self.mode == "BUY" else "What would you like to sell?"
            from src.ui.dialogue import wrap_text
            rows = wrap_text(line, fonts["dialog"], self.bottom_rect.w - 80)[:2]
            theme.draw_textbox(screen, self.bottom_rect)
            lh = int(fonts["dialog"].get_linesize() * 1.2)
            top = self.bottom_rect.centery - lh * len(rows) // 2
            for k, row in enumerate(rows):
                theme.shadow_text(screen, row, fonts["dialog"], self.bottom_rect.x + 40, top + k * lh)

    def _draw_card(self, btn):
        """An item on the shelf: icon, name, how many you have, the price."""
        screen, fonts = self.game.screen, self.game.assets.fonts
        item, r = btn.item_key, btn.rect
        theme.card(screen, r, hover=r.collidepoint(pygame.mouse.get_pos()), accent=theme.ACCENT["mart"])
        icon = self._icon(item, 44)
        if icon:
            screen.blit(icon, icon.get_rect(center=(r.x + 38, r.centery)))
        name = self._name(item)
        font = fonts["label"] if fonts["label"].size(name)[0] < r.w - 260 else fonts["caption"]
        theme.shadow_text(screen, name, font, r.x + 72, r.y + 10)
        theme.shadow_text(screen, f"In Bag: {self._have(item)}", fonts["caption"], r.x + 72, r.bottom - 26,
                          color=(110, 116, 136))
        price = self._unit_price(item)
        label = f"${price:,}" if self.mode == "BUY" else f"sells ${price:,}"
        theme.shadow_text(screen, label, fonts["button"] if self.mode == "BUY" else fonts["label"], r.right - 18,
                          r.centery - (fonts["button"] if self.mode == "BUY" else fonts["label"]).get_height() // 2,
                          color=(176, 120, 16), align="right")

    def _draw_qty(self):
        """The quantity card: the item, -1 / +1 / +10 / MAX, the sum, BUY / CANCEL."""
        screen, fonts = self.game.screen, self.game.assets.fonts
        q = self.qty_rect
        item = self.pending_item
        theme.card(screen, q, selected=True, accent=theme.ACCENT["mart"], radius=16)
        icon = self._icon(item, 64)
        if icon:
            screen.blit(icon, (q.x + 30, q.y + 26))
        verb = "BUY" if self.mode == "BUY" else "SELL"
        theme.shadow_text(screen, f"{verb} {self._name(item).upper()}", fonts["button"], q.x + 110, q.y + 26)
        price = self._unit_price(item)
        theme.shadow_text(screen, f"${price:,} each   (you have {self._have(item)})", fonts["label"], q.x + 110,
                          q.y + 66, color=(110, 116, 136))
        theme.shadow_text(screen, f"x{self.qty}", fonts["big"], q.right - 40, q.y + 150, align="right")
        for b in self.qty_buttons:
            b.draw(screen)
        total = price * self.qty
        money = self.game.story_manager.money
        after = money - total if self.mode == "BUY" else money + total
        theme.shadow_text(screen, f"{self.qty} x ${price:,} = ${total:,}", fonts["s_med"], q.centerx, q.y + 240,
                          align="center")
        sign = "-" if self.mode == "BUY" else "+"
        theme.shadow_text(screen, f"Money: ${money:,} {sign} ${total:,} = ${after:,}", fonts["label"], q.centerx,
                          q.y + 272, color=theme.HP_RED if after < 0 else (110, 116, 136), align="center")
        self.btn_yes.draw(screen)
        self.btn_no.draw(screen)


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
        f = game.assets.fonts
        H = theme.HEADER_H
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.go_back, bg_color=theme.BACK,
                                      autosize=False)
        # The menu frame: the party at the left, the Box (6 x 5, like the games) at the right, the
        # details bar along the bottom.
        self.party_rect = pygame.Rect(16, H + 16, 330, 0)
        self.box_rect = pygame.Rect(self.party_rect.right + 14, H + 16, 0, 0)
        self.box_rect.width = game.width - 16 - self.box_rect.x
        self.bar_rect = pygame.Rect(16, game.height - 86, game.width - 32, 78)
        self.party_rect.height = self.box_rect.height = self.bar_rect.top - 12 - self.party_rect.top
        top = self.box_rect.y + 12
        self.btn_prev_box = CommandButton((self.box_rect.x + 14, top, 64, 50), "<", f["button"], self.prev_box,
                                          bg_color=theme.ACCENT["pc"], autosize=False)
        self.btn_next_box = CommandButton((self.box_rect.x + 330, top, 64, 50), ">", f["button"], self.next_box,
                                          bg_color=theme.ACCENT["pc"], autosize=False)
        self.btn_sort_id = CommandButton((self.box_rect.right - 14 - 330, top, 150, 50), "SORT #", f["label"],
                                         self.sort_by_id, bg_color=theme.TAB_OFF, autosize=False)
        self.btn_sort_name = CommandButton((self.box_rect.right - 14 - 170, top, 170, 50), "SORT A-Z", f["label"],
                                           self.sort_by_name, bg_color=theme.TAB_OFF, autosize=False)
        self.btn_release = CommandButton((self.bar_rect.right - 18 - 180, self.bar_rect.y + 12, 180,
                                          self.bar_rect.h - 28), "RELEASE", f["label"], self.release_pokemon,
                                         bg_color=theme.FIGHT, visible=False, autosize=False)
        self.cols, self.rows = 6, 5  # a Box holds 30, as in the games
        # Tap a Pokemon: a small menu beside it (MOVE, SUMMARY, and RELEASE in the Box). MOVE picks
        # it up; the next tap puts it down (or swaps), as before. Tapping elsewhere closes it.
        self.popup = None  # ("party" | "pc", index)
        self.popup_rect = pygame.Rect(0, 0, 220, 0)
        self.btn_pop_move = CommandButton((0, 0, 196, 50), "MOVE", f["label"], self.popup_move,
                                          bg_color=theme.POKEMON, visible=False, autosize=False)
        self.btn_pop_summary = CommandButton((0, 0, 196, 50), "SUMMARY", f["label"], self.popup_summary,
                                             bg_color=theme.RUN, visible=False, autosize=False)
        self.btn_pop_release = CommandButton((0, 0, 196, 50), "RELEASE", f["label"], self.popup_release,
                                             bg_color=theme.FIGHT, visible=False, autosize=False)
        self.popup_buttons = [self.btn_pop_move, self.btn_pop_summary, self.btn_pop_release]

    def _popup_mon(self):
        if not self.popup:
            return None
        where, i = self.popup
        group = self.party if where == "party" else self.pc
        return group[i] if i < len(group) else None

    def open_popup(self, where, index):
        """The menu beside the tapped Pokemon, kept on the screen."""
        self.popup = (where, index)
        slot = self.party_slot(index) if where == "party" else self.box_slot(index - self.box_index * self.mons_per_box)
        buttons = self.popup_buttons if where == "pc" else self.popup_buttons[:2]
        pr = self.popup_rect
        pr.h = 44 + len(buttons) * 58 + 4
        pr.x = slot.right + 8 if slot.right + 8 + pr.w <= self.game.width - 8 else slot.left - 8 - pr.w
        pr.y = min(max(theme.HEADER_H + 8, slot.centery - pr.h // 2), self.bar_rect.bottom - pr.h)
        for k, btn in enumerate(self.popup_buttons):
            btn.rect.topleft = (pr.x + 12, pr.y + 44 + k * 58)
            btn.set_visibility(btn in buttons)

    def close_popup(self):
        self.popup = None
        for btn in self.popup_buttons:
            btn.set_visibility(False)

    def popup_move(self):
        where, i = self.popup
        self.close_popup()
        if where == "party":
            self.selected_party_idx = i
        else:
            self.selected_pc_idx = i

    def popup_summary(self):
        mon = self._popup_mon()
        self.close_popup()
        if mon is not None:
            self.game.change_state(PokemonDetailState(self.game, mon, self))

    def popup_release(self):
        _, i = self.popup
        self.close_popup()
        self.selected_pc_idx = i
        self.release_pokemon()

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
        for btn in self.popup_buttons:
            self.game.ui_manager.add_element(btn)

    def party_slot(self, i):
        """Rect of party slot i (0-5)."""
        r = self.party_rect
        h = (r.h - 56 - 5 * 8) // 6
        return pygame.Rect(r.x + 12, r.y + 46 + i * (h + 8), r.w - 24, h)

    def box_slot(self, local_idx):
        """Rect of slot local_idx (0-29) of the Box on show."""
        r = self.box_rect
        gx, gy, gap = r.x + 14, r.y + 76, 10
        w = (r.w - 28 - gap * (self.cols - 1)) // self.cols
        h = (r.bottom - 12 - gy - gap * (self.rows - 1)) // self.rows
        c, row = local_idx % self.cols, local_idx // self.cols
        return pygame.Rect(gx + c * (w + gap), gy + row * (h + gap), w, h)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):  # the wheel flips Boxes
                self.close_popup()
                self.prev_box() if event.button == 4 else self.next_box()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.popup:
                # (the menu's own buttons take their taps first) anywhere else closes it; another
                # Pokemon gets the menu instead
                old = self.popup
                self.close_popup()
                hit = self._slot_at(event.pos)
                if hit and hit != old and self._mon_at(*hit) is not None:
                    self.open_popup(*hit)
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i in range(6):
                    if self.party_slot(i).collidepoint(event.pos):
                        self.handle_click("party", i)
                        return
                box_start = self.box_index * self.mons_per_box
                for local in range(self.mons_per_box):
                    if self.box_slot(local).collidepoint(event.pos):
                        self.handle_click("pc", box_start + local)
                        return

    def _slot_at(self, pos):
        for i in range(6):
            if self.party_slot(i).collidepoint(pos):
                return ("party", i)
        box_start = self.box_index * self.mons_per_box
        for local in range(self.mons_per_box):
            if self.box_slot(local).collidepoint(pos):
                return ("pc", box_start + local)
        return None

    def _mon_at(self, where, i):
        group = self.party if where == "party" else self.pc
        return group[i] if i < len(group) else None

    def _hovered(self):
        """The Pokemon under the pointer (party or Box), else None."""
        mouse = pygame.mouse.get_pos()
        for i, p in enumerate(self.party[:6]):
            if self.party_slot(i).collidepoint(mouse):
                return p
        box_start = self.box_index * self.mons_per_box
        for local in range(self.mons_per_box):
            i = box_start + local
            if i < len(self.pc) and self.pc[i] is not None and self.box_slot(local).collidepoint(mouse):
                return self.pc[i]
        return None

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
                self.pc[self.selected_pc_idx] = self.game.story_manager.heal_for_pc(self.party[index])
                self.party[index] = pc_mon
                self.selected_pc_idx = None
            else:
                self.open_popup("party", index)

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

                self.game.story_manager.heal_for_pc(party_mon)
                if self.pc[index] is None:
                    self.pc[index] = party_mon
                    self.party.pop(old_p_idx)
                else:
                    self.party[old_p_idx] = self.pc[index]
                    self.pc[index] = party_mon

                self.selected_party_idx = None
            elif self.pc[index] is not None:
                self.open_popup("pc", index)

    def update(self):
        self.btn_release.set_visibility(False)  # (RELEASE is in the tap menu now)

    def draw(self):
        """The menu frame (src/ui/theme.py) in the PC's teal: the party, the Box, the details bar."""
        screen = self.game.screen
        f = self.game.assets.fonts
        accent = theme.ACCENT["pc"]
        theme.menu_background(screen, accent, self.game.story_manager.pc_name().upper(), f["button"], title_x=176)
        Utils.draw_text_outline(screen, f"{sum(1 for p in self.pc if p)} stored", f["button"], WHITE,
                                self.game.width - 24, theme.HEADER_H // 2 - 4, align="right",
                                outline_color=theme.shade(accent, 0.45), thickness=3)
        mouse = pygame.mouse.get_pos()

        # The party.
        theme.draw_panel(screen, self.party_rect)
        Utils.draw_text_outline(screen, "PARTY", f["button"], WHITE, self.party_rect.centerx, self.party_rect.y + 24)
        for i in range(6):
            rect = self.party_slot(i)
            if i < len(self.party):
                p = self.party[i]
                theme.card(screen, rect, hover=rect.collidepoint(mouse), selected=self.selected_party_idx == i,
                           accent=theme.POKEMON if self.selected_party_idx == i else accent)
                icon = fit_sprite(p.image or p.sidebar_image, rect.h - 8, rect.h - 8) if (p.image or p.sidebar_image) else None
                if icon:
                    screen.blit(icon, icon.get_rect(center=(rect.x + 8 + (rect.h - 8) // 2, rect.centery)))
                tx = rect.x + rect.h + 8
                theme.shadow_text(screen, p.display_name.title(), f["label"], tx, rect.y + 8)
                lv = theme.shadow_text(screen, f"Lv{p.level}", f["caption"], tx, rect.bottom - 26)
                bar = pygame.Rect(lv.right + 10, rect.bottom - 22, rect.right - 12 - lv.right - 10, 8)
                ratio = max(0.0, min(1.0, p.current_hp / max(1, p.get_max_hp())))
                pygame.draw.rect(screen, (88, 88, 96), bar, border_radius=4)
                color = theme.HP_GREEN if ratio > 0.5 else theme.HP_YELLOW if ratio > 0.2 else theme.HP_RED
                if ratio > 0:
                    pygame.draw.rect(screen, color, (bar.x, bar.y, max(3, int(bar.w * ratio)), bar.h), border_radius=4)
            else:
                pygame.draw.rect(screen, theme.shade(theme.PANEL_INNER, 0.8), rect, border_radius=12)
                pygame.draw.rect(screen, theme.PANEL_EDGE, rect, 2, border_radius=12)

        # The Box.
        theme.draw_panel(screen, self.box_rect)
        mid = (self.btn_prev_box.rect.right + self.btn_next_box.rect.left) // 2
        Utils.draw_text_outline(screen, f"BOX {self.box_index + 1} / {self.get_total_boxes()}", f["button"], WHITE,
                                mid, self.btn_prev_box.rect.centery)
        box_start = self.box_index * self.mons_per_box
        for local in range(self.mons_per_box):
            i = box_start + local
            rect = self.box_slot(local)
            if i < len(self.pc) and self.pc[i] is not None:
                p = self.pc[i]
                theme.card(screen, rect, hover=rect.collidepoint(mouse), selected=self.selected_pc_idx == i,
                           accent=theme.POKEMON if self.selected_pc_idx == i else accent)
                sprite = p.image if p.image else p.sidebar_image
                if sprite:
                    spr = fit_sprite(sprite, rect.w - 20, rect.h - 30)
                    screen.blit(spr, spr.get_rect(center=(rect.centerx, rect.y + 4 + (rect.h - 26) // 2)))
                name = p.display_name.title()
                nf = f["caption"] if f["caption"].size(name)[0] <= rect.w - 8 else f["tiny"]
                theme.shadow_text(screen, name, nf, rect.centerx, rect.bottom - 12, align="center")
            else:
                pygame.draw.rect(screen, theme.shade(theme.PANEL_INNER, 0.8), rect, border_radius=10)
                pygame.draw.rect(screen, theme.PANEL_EDGE, rect, 2, border_radius=10)

        # The details bar: the hovered (or picked) Pokemon, else how moving works.
        show = self._hovered()
        if show is None and self.selected_pc_idx is not None and self.selected_pc_idx < len(self.pc):
            show = self.pc[self.selected_pc_idx]
        if show is None and self.selected_party_idx is not None and self.selected_party_idx < len(self.party):
            show = self.party[self.selected_party_idx]
        if show is not None:
            types = "/".join(t.title() for t in (show.types or []))
            line = (f"{show.display_name.upper()}   Lv{show.level}   {types}   "
                    f"HP {int(show.current_hp)}/{show.get_max_hp()}")
        else:
            line = ("Now tap where it goes (party or Box)." if self.selected_pc_idx is not None
                    or self.selected_party_idx is not None else "Tap a Pokémon to move it or see its summary.")
        bf = f["s_med"]
        theme.draw_textbox(screen, self.bar_rect)
        theme.shadow_text(screen, line, bf, self.bar_rect.x + 32, self.bar_rect.centery - bf.get_height() // 2 - 2)

        self.game.ui_manager.draw(screen)
        mon = self._popup_mon()
        if mon is not None:
            theme.popup_panel(screen, self.popup_rect, mon.display_name.upper(), f["label"])
            for btn in self.popup_buttons:
                btn.draw(screen)


# [REF-0032: Bag System]
def dex_regions(story):
    """Regional Pokedexes the player has: the starting region's, and each region whose starter
    they've received (a new region's dex arrives with its starter, as in the games)."""
    national_dex = story.story_flags.get("unlocked_national_dex", False)
    out = []
    for r, cfg in story.get_region_starts():
        lo, hi = cfg.get("dex_range", [0, -1])
        if hi < lo:
            continue  # travel-only places (Orange Islands, Orre) have no Pokedex of their own
        if (r == story.starting_region or story.story_flags.get(f"received_starter_{r.lower()}")
                or (national_dex and r in ("KANTO", "JOHTO"))):
            out.append(r)
    return out or [story.starting_region]


def region_dex(cfg):
    """A region's Pokedex in its own order: an explicit dex_list (Kalos uses the X/Y Kalos dex), else
    its generation's range plus dex_extra."""
    if cfg.get("dex_list"):
        return list(cfg["dex_list"])
    lo, hi = cfg.get("dex_range", [1, 151])
    return list(dict.fromkeys(list(range(lo, hi + 1)) + cfg.get("dex_extra", [])))


def _dex_ids(story, caught_data, seen_ids, view=None):
    """Pokedex 'normal' tab ids. view = a region: that region's own dex (its generation's range plus
    the later-gen evolutions obtainable there, dex_extra). view = None/"NATIONAL": every regional
    dex in a row; species caught outside them are appended, and merely-seen ones (a trainer's
    Crobat) too once the National Dex is unlocked."""
    national_dex = story.story_flags.get("unlocked_national_dex", False)
    regions = dex_regions(story)
    if view and view != "NATIONAL":
        return region_dex(story.get_region_start(view))
    id_list = []
    for r in regions:
        id_list += region_dex(story.get_region_start(r))
    listed = set(id_list)
    extra = {v['id'] for v in caught_data.values()} | (set(seen_ids) if national_dex else set())
    id_list += sorted(i for i in extra if isinstance(i, int) and i <= 1025 and i not in listed)
    return list(dict.fromkeys(id_list))


class BagState(GameState):
    def __init__(self, game, previous_state, context="normal"):
        super().__init__(game)
        self.previous_state = previous_state
        self.context = context
        self.evo_items_map = self.game.loader.evolution_map.get("EVOLUTION_ITEMS", {})
        self.evo_keys = sorted(list(self.evo_items_map.keys()))

        # Pockets, as in the games (Jordan). In battle only the ones you can use there.
        self.pages = list(self.BATTLE_POCKETS if context == "battle" else self.POCKETS)
        self.current_page = 0
        self.pocket_tabs = []
        f = game.assets.fonts
        H = theme.HEADER_H
        gap = 10
        tab_w = (game.width - 48 - gap * (len(self.pages) - 1)) // len(self.pages)
        for i, name in enumerate(self.pages):
            tf = f["label"] if f["label"].size(name)[0] <= tab_w - 24 else f["caption"]
            self.pocket_tabs.append(CommandButton((24 + i * (tab_w + gap), H + 14, tab_w, 50), name, tf,
                                                  (lambda i=i: self.open_pocket(i)), bg_color=theme.TAB_OFF,
                                                  autosize=False))

        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.go_back, bg_color=theme.BACK,
                                      autosize=False)

        # (The tabs pick the pocket; these stay for anything that turns pockets in order.)
        cy = game.height // 2
        self.btn_prev = Button((20, cy - 30, 60, 60), "<", f["med"], self.prev_page, visible=False)
        self.btn_next = Button((game.width - 80, cy - 30, 60, 60), ">", f["med"], self.next_page, visible=False)
        # The menu frame: the pocket's items as cards, the bar along the bottom (the item under the
        # pointer, the page buttons). A full pocket is split into pages.
        self.list_rect = pygame.Rect(24, H + 14 + 50 + 16, game.width - 48, 0)
        self.bar_rect = pygame.Rect(16, game.height - 86, game.width - 32, 78)
        self.list_rect.height = self.bar_rect.top - 12 - self.list_rect.top
        self.item_page = 0
        self.item_page_count = 1
        bh = self.bar_rect.h - 28
        self.btn_items_up = CommandButton((self.bar_rect.right - 18 - 230, self.bar_rect.y + 12, 110, bh), "UP",
                                          f["label"], lambda: self.turn_item_page(-1),
                                          bg_color=theme.ACCENT["bag"], autosize=False)
        self.btn_items_down = CommandButton((self.bar_rect.right - 18 - 110, self.bar_rect.y + 12, 110, bh), "DOWN",
                                            f["label"], lambda: self.turn_item_page(1),
                                            bg_color=theme.ACCENT["bag"], autosize=False)

        self.item_buttons = []
        self.refresh_buttons()

    POCKETS = ("ITEMS", "MEDICINE", "POKE BALLS", "BERRIES", "TMs & HMs", "KEY ITEMS")
    BATTLE_POCKETS = ("MEDICINE", "POKE BALLS", "BATTLE ITEMS")
    MEDICINE = tuple(itemlib.MEDICINE)
    BATTLE_ITEMS = ("DAMP_ROCK", "HEAT_ROCK", "SMOOTH_ROCK", "ICY_ROCK") + tuple(itemlib.BATTLE)
    # Usable from the Bag (anything else says there's no use for it right now).
    USABLE_KEYS = ("TOWN_MAP", "JOHTO_MAP", "UNOWN_REPORT", "POFFIN_CASE", "BERRY_POUCH", "WEATHER_DIAL")
    USABLE_MEDICINE = ("POTION", "FULL_HEAL", "REVIVE", "RARE_CANDY")
    # Key items the games keep in the Items pocket (held / stones / fossils).
    ITEM_POCKET_KEYS = ("ITE", "_FOSSIL", "OLD_AMBER", "_ORB", "_DRIVE", "ROCKY_HELMET", "SOOTHE_BELL", "AMULET_COIN")

    def pocket_of(self, key):
        from src.pokemon.poffin import BERRIES
        if key in self.MEDICINE:
            return "MEDICINE"
        if key in self.BATTLE_ITEMS:
            return "BATTLE ITEMS" if self.context == "battle" else "ITEMS"
        if key.endswith("_BALL") and key != "GS_BALL":
            return "POKE BALLS"
        if key in BERRIES or key.endswith("_BERRY"):
            return "BERRIES"
        if key.startswith(("HM_", "TM_", "TM")) and key[2:3] in ("_", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"):
            return "TMs & HMs"
        keys = self.game.loader.area_data.get("GAME_CONFIG", {}).get("KEY_ITEMS", [])
        if key in keys and not (key.endswith(self.ITEM_POCKET_KEYS) and key not in self.USABLE_KEYS):
            return "KEY ITEMS"
        return "ITEMS"

    def pocket_items(self, pocket):
        """(item, qty) in a pocket, in a fixed order."""
        inv = self.game.story_manager.inventory
        out = []
        if pocket == "POKE BALLS":
            out.append(("POKE_BALLS", self.game.story_manager.balls_left))
        if pocket == "ITEMS":
            held = any(getattr(p, "everstone", False) for p in self.game.story_manager.player_team)
            if held and not inv.get("EVERSTONE"):
                out.append(("EVERSTONE", 0))  # (to take it back)
        order = list(self.MEDICINE) + self.evo_keys + list(POKEBLOCKS)
        keys = sorted((k for k, q in inv.items() if q and q > 0 and k != "POKE_BALLS"),
                      key=lambda k: (order.index(k) if k in order else len(order), k))
        out += [(k, inv[k]) for k in keys if self.pocket_of(k) == pocket]
        return [(k, q) for k, q in out if q > 0 or k == "EVERSTONE"]

    def usable(self, key):
        from src.pokemon import catching
        if self.context == "battle":
            if key in catching.BALLS:  # throw a ball any time in a wild battle, as in the games
                return getattr(self.previous_state, "trainer_class", "") == "WILD"
            return (key in itemlib.MEDICINE and key != "RARE_CANDY") or key in self.BATTLE_ITEMS
        return (key in itemlib.MEDICINE or key in itemlib.FIELD or key in self.USABLE_KEYS
                or key == "EVERSTONE" or key in self.evo_keys or key in POKEBLOCKS)

    def open_pocket(self, i):
        self.current_page = i
        self.item_page = 0
        self.refresh_buttons()

    def prev_page(self):
        self.current_page = (self.current_page - 1) % len(self.pages)
        self.item_page = 0
        self.refresh_buttons()

    def next_page(self):
        self.current_page = (self.current_page + 1) % len(self.pages)
        self.item_page = 0
        self.refresh_buttons()

    def turn_item_page(self, step):
        self.item_page = max(0, min(self.item_page_count - 1, self.item_page + step))
        self.refresh_buttons()

    def go_back(self):
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.elements.clear()
        self.game.ui_manager.add_element(self.btn_back)
        self.game.ui_manager.add_element(self.btn_prev)
        self.game.ui_manager.add_element(self.btn_next)
        self.game.ui_manager.add_element(self.btn_items_up)
        self.game.ui_manager.add_element(self.btn_items_down)
        for btn in self.pocket_tabs:
            self.game.ui_manager.add_element(btn)
        for btn in self.item_buttons:
            self.game.ui_manager.add_element(btn)

    def refresh_buttons(self):
        for btn in self.item_buttons:
            if btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)

        self.item_buttons = []

        for i, tab in enumerate(self.pocket_tabs):  # the open pocket stands out
            tab.bg_color = theme.ACCENT["bag"] if i == self.current_page else theme.TAB_OFF
        items_to_show = self.pocket_items(self.pages[self.current_page])

        cols, gap, btn_h = 2, 12, 58
        col_w = (self.list_rect.w - gap * (cols - 1)) // cols
        rows = max(1, (self.list_rect.h + gap) // (btn_h + gap))
        per_page = rows * cols
        self.item_page_count = max(1, (len(items_to_show) + per_page - 1) // per_page)
        self.item_page = min(self.item_page, self.item_page_count - 1)
        self.btn_items_up.set_visibility(self.item_page > 0)
        self.btn_items_down.set_visibility(self.item_page < self.item_page_count - 1)
        items_to_show = items_to_show[self.item_page * per_page:(self.item_page + 1) * per_page]

        if not items_to_show:
            return

        from src.world import hms
        for i, (item_key, qty) in enumerate(items_to_show):
            row, col = i // cols, i % cols
            x = self.list_rect.x + col * (col_w + gap)
            y = self.list_rect.y + row * (btn_h + gap)

            can_use = (qty > 0 or item_key == "EVERSTONE") and self.usable(item_key)
            callback = ((lambda k=item_key: self.use_item(k)) if can_use
                        else (lambda k=item_key: self.no_use(k)))

            icon = self.game.assets.get_item_image(item_key)
            if item_key == "MYSTERY_EGG":
                egg_path = os.path.join(self.game.assets.pokemon_sprites_dir, "egg.png")
                if os.path.exists(egg_path):
                    icon = pygame.image.load(egg_path).convert_alpha()

            self.item_buttons.append(ItemCard((x, y, col_w, btn_h), hms.item_name(item_key), qty,
                                              self.game.assets.fonts["label"], callback, icon=icon,
                                              usable=can_use, key=item_key))

        for btn in self.item_buttons:
            self.game.ui_manager.add_element(btn)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):  # the wheel turns the page
                self.turn_item_page(-1 if event.button == 4 else 1)

    def update(self):
        pass

    def no_use(self, item_key):
        from src.world import hms
        name = hms.item_name(item_key)
        if item_key == "POKE_BALLS":
            line = "Poke Balls are thrown in battle: weaken a wild Pokemon, then catch it!"
        elif item_key.startswith("HM_"):
            line = f"{name} works on its own: it opens the way wherever it's needed."
        elif self.pocket_of(item_key) == "KEY ITEMS":
            line = f"The {name} is used automatically when you need it."
        else:
            line = f"There's no use for the {name} right now."
        self.game.show_dialogue([line])

    def use_item(self, item_key):
        self.selected_item = item_key

        from src.pokemon import catching
        if self.context == "battle" and item_key in catching.BALLS:
            battle = self.previous_state
            self.game.story_manager.selected_ball = item_key
            self.game.change_state(battle)
            battle.throw_from_bag()
            return
        if item_key in itemlib.MEDICINE and item_key != "RARE_CANDY":
            self.game.change_state(PokemonPartyMenuState(
                self.game, previous_state=self, context="use_item", on_select=self.on_pokemon_select_medicine))
            return
        if item_key in itemlib.BATTLE and self.context == "battle":
            self._use_battle_item(item_key)
            return
        if item_key in itemlib.FIELD:
            self._use_field_item(item_key)
            return

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

        if item_key == "EVERSTONE":
            self.game.change_state(PokemonPartyMenuState(
                self.game, previous_state=self, context="use_item",
                on_select=self.on_pokemon_select_everstone
            ))
            return

        if item_key == "FULL_HEAL":
            self.game.change_state(PokemonPartyMenuState(
                self.game, previous_state=self, context="use_item",
                on_select=self.on_pokemon_select_full_heal
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
            from src.states.region_map import RegionMapState
            self.game.change_state(RegionMapState(self.game, self))
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
        from src.pokemon import evolution
        hit = evolution.item_evolution(self.game, pokemon, self.selected_item)
        if hit:
            entry, target_id = hit
            target_form = entry.split("_", 1)[1].lower() if "_" in entry else "normal"
            self.game.story_manager.inventory[self.selected_item] = max(
                0, self.game.story_manager.inventory.get(self.selected_item, 0) - 1)
            self.game.change_state(EvolutionState(
                self.game, pokemon, target_id, slot_index, next_form=target_form,
                return_state=self.previous_state))
            return
        timed = [r for _, _, r in evolution.evolution_options(self.game, pokemon)
                 if r.get("item") == self.selected_item and r.get("time")]
        if timed:
            self._back_to_bag([f"Nothing happened... try it during the {timed[0]['time']}."])
            return
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
                self._back_to_bag(["Error: Evolution data missing."])
        else:
            self._back_to_bag(["It won't have any effect."])

    def candy_limit(self, pokemon):
        """(highest level Rare Candies can reach now, the cap message if it's already there)."""
        from src.world import levels
        cap = min(levels.xp_cap(self.game.story_manager), pokemon.MAX_LEVEL)
        if pokemon.level >= pokemon.MAX_LEVEL:
            return cap, f"{pokemon.display_name} is already Lv 100! The Rare Candy had no effect."
        if pokemon.level >= cap:
            return cap, (f"{pokemon.display_name} is at the level cap (Lv {cap})! The Rare Candy had no effect. "
                         "Beat the next Gym Leader to raise the cap.")
        return cap, None

    def on_pokemon_select_rare_candy(self, slot_index):
        """Pick how many Rare Candies to use (up to the level cap), then use them."""
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return
        pokemon = party[slot_index]
        cap, full = self.candy_limit(pokemon)
        if full:
            self._back_to_bag([full])
            return
        most = min(self.game.story_manager.inventory.get("RARE_CANDY", 0), cap - pokemon.level)
        if most <= 1:
            self.use_rare_candies(slot_index, 1)
            return
        self.game.change_state(ItemCountState(
            self.game, self, pokemon, "RARE_CANDY", most,
            lambda n: n and f"Lv {pokemon.level} -> Lv {pokemon.level + n}",
            lambda n: self.use_rare_candies(slot_index, n)))

    def use_rare_candies(self, slot_index, count):
        party = self.game.story_manager.player_team
        pokemon = party[slot_index]
        if count <= 0:
            self._back_to_bag()
            return
        from src.pokemon import evolution
        from src.pokemon import moves as movelib
        cap, _ = self.candy_limit(pokemon)
        inv = self.game.story_manager.inventory
        count = min(count, inv.get("RARE_CANDY", 0), cap - pokemon.level)
        old_level = pokemon.level
        pokemon.level_up(count)
        inv["RARE_CANDY"] -= count
        if inv["RARE_CANDY"] <= 0:
            del inv["RARE_CANDY"]
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.play()
        used = "a Rare Candy" if count == 1 else f"{count} Rare Candies"
        lines = [f"You used {used} on {pokemon.display_name}.",
                 f"{pokemon.display_name} grew to Lv {pokemon.level}!"]
        if pokemon.level >= cap and cap < pokemon.MAX_LEVEL:
            lines.append(f"{pokemon.display_name} reached the level cap (Lv {cap}). Beat the next Gym Leader to go higher!")
        lines += movelib.learn_new_moves(self.game, pokemon, old_level)  # before any evolution
        ready = evolution.ready_evolutions(self.game, pokemon)
        if ready:
            entry = self.game.story_manager.pick_evolution_branch(ready)
            base_name, next_form = (entry.rsplit("_", 1) + ["normal"])[:2] if "_" in entry else (entry, "normal")
            next_id = self.game.name_to_id.get(base_name.upper())
            if next_id:  # the messages first, then it evolves
                self.game.change_state(self)
                self.refresh_buttons()
                self.game.show_dialogue(lines + [f"What? {pokemon.display_name} is evolving!"], callback=(
                    lambda: self.game.change_state(EvolutionState(
                        self.game, pokemon, next_id, slot_index, next_form=next_form.lower(), context="party",
                        return_state=self.previous_state, choices=ready if len(ready) > 1 else None))))
                return
        self._back_to_bag(lines)

    def _take(self, item):
        inv = self.game.story_manager.inventory
        inv[item] = inv.get(item, 0) - 1
        if inv[item] <= 0:
            inv.pop(item, None)

    def on_pokemon_select_medicine(self, slot_index):
        """Potions, status heals, Revives (src/pokemon/items.py), in or out of battle."""
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return
        p, item = party[slot_index], self.selected_item
        used, lines = itemlib.medicine_effect(item, p)
        if not used:
            self._back_to_bag(lines)
            return
        self._take(item)
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.play()
        label = forms.item_label(item).upper()
        if self.context == "battle":
            battle = self.previous_state
            if p is battle.player_pokemon:
                battle.player_hp = p.current_hp
            self.game.change_state(battle)
            battle.show_message([f"{self.game.player_name} used a {label}!"] + lines, callback=battle.on_item_used)
            return
        self._back_to_bag([f"You used a {label}."] + lines)

    def _use_battle_item(self, item):
        """X items, Dire Hit, Guard Spec.: on the Pokemon in battle, then the foe's turn."""
        battle = self.previous_state
        data, mon = itemlib.BATTLE[item], battle.player_pokemon
        label = forms.item_label(item).upper()
        if "stat" in data:
            lines = battle.change_stages(mon, [[data["stat"], 2]])
            if "won't go any higher" in lines[-1]:
                self.game.change_state(battle)
                battle.show_message(lines, callback=battle.return_to_menu)
                return
        elif "focus" in data:
            if battle.vol(mon).get("focus"):
                self.game.change_state(battle)
                battle.show_message([f"{mon.display_name.upper()} is already getting pumped!"],
                                    callback=battle.return_to_menu)
                return
            battle.vol(mon)["focus"] = data["focus"]
            lines = [f"{mon.display_name.upper()} is getting pumped!"]
        else:
            battle.side(mon)["mist"] = data["mist"]
            lines = ["Your team became shrouded in mist!"]
        self._take(item)
        self.game.change_state(battle)
        battle.show_message([f"{self.game.player_name} used the {label}!"] + lines, callback=battle.on_item_used)

    def _use_field_item(self, item):
        """Repels (wild Pokemon stay away: routes can be left without battling) and Escape Rope."""
        story = self.game.story_manager
        data = itemlib.FIELD[item]
        if "repel" in data:
            if getattr(story, "repel_routes", 0) > 0:
                self._back_to_bag([f"A Repel is already working ({story.repel_routes} more routes)."])
                return
            story.repel_routes = data["repel"]
            self._take(item)
            self._back_to_bag([f"You used the {forms.item_label(item).upper()}!",
                               f"Wild Pokemon will stay away for the next {data['repel']} routes:",
                               "you can leave them without battling."])
            return
        area = story.get_current_area_data()
        inside = area.get("area_type") == "dungeon" or area.get("battle_type") in ("cave", "indoor", "mountain")
        if not inside:
            self._back_to_bag(["You can only use an Escape Rope in caves and buildings."])
            return
        self._take(item)
        dest, _ = story.whiteout_destination()
        from src.states.overworld import AreaTransitionState
        self.game.change_state(AreaTransitionState(self.game, dest, initial_message="You used the ESCAPE ROPE!"))

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
            from src.pokemon import evolution
            if p.name.upper() == "FEEBAS" and evolution.ready_evolutions(self.game, p):
                milotic = self.game.name_to_id.get("MILOTIC")
                if milotic:
                    self.game.change_state(EvolutionState(
                        self.game, p, milotic, slot_index, context="party", return_state=self))
                    return
        self._back_to_bag(lines)

    def on_pokemon_select_everstone(self, slot_index):
        """Give the Everstone to a Pokemon (it won't evolve), or take it back."""
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return
        p = party[slot_index]
        inv = self.game.story_manager.inventory
        if getattr(p, "everstone", False):
            p.everstone = False
            self.game.story_manager.add_item("EVERSTONE")
            lines = [f"You took the Everstone back from {p.display_name}.", f"{p.display_name} can evolve again."]
        else:
            p.everstone = True
            inv["EVERSTONE"] = inv.get("EVERSTONE", 0) - 1
            lines = [f"{p.display_name} is now holding the Everstone.", "It won't evolve while it holds it."]
        self.refresh_buttons()
        self._back_to_bag(lines)

    def _back_to_bag(self, lines=None):
        """Return to the Bag, then show the message (showing it first got wiped by the
        screen change, so the player never saw it)."""
        self.game.change_state(self)
        self.refresh_buttons()
        if lines:
            self.game.show_dialogue(lines)

    def on_pokemon_select_potion(self, slot_index):
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return
        p = party[slot_index]

        msg = None
        if p.current_hp <= 0:
            msg = f"Potion has no effect on a fainted {p.display_name}!"
        elif p.current_hp >= p.get_max_hp():
            msg = f"{p.display_name} is already at full health!"
        else:
            heal = p.get_max_hp() // 2
            msg = f"{p.display_name} recovered {min(heal, p.get_max_hp() - p.current_hp)} HP!"
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
                self.previous_state.show_message([f"{self.game.player_name} used a POTION!", msg],
                                                 callback=self.previous_state.on_item_used)
                return

        self._back_to_bag([msg])

    def on_pokemon_select_full_heal(self, slot_index):
        """Full Heal: cures burn, paralysis, poison, sleep and freeze."""
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return
        p = party[slot_index]
        if p.current_hp <= 0:
            msg = f"Full Heal has no effect on a fainted {p.display_name}!"
        elif not getattr(p, "status", None):
            msg = f"{p.display_name} has no status problem!"
        else:
            msg = f"{p.display_name} was cured!"
            p.cure_status()
            inv = self.game.story_manager.inventory
            inv["FULL_HEAL"] -= 1
            if inv["FULL_HEAL"] <= 0:
                del inv["FULL_HEAL"]
            if self.game.assets.heal_sfx:
                self.game.assets.heal_sfx.play()
            if self.context == "battle":
                self.game.change_state(self.previous_state)
                self.previous_state.show_message([f"{self.game.player_name} used a FULL HEAL!", msg],
                                                 callback=self.previous_state.on_item_used)
                return
        self._back_to_bag([msg])

    def on_pokemon_select_revive(self, slot_index):
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return
        p = party[slot_index]

        if p.current_hp > 0:
            msg = f"{p.display_name} is not fainted!"
        else:
            msg = f"{p.display_name} was revived!"
            p.current_hp = max(1, p.get_max_hp() // 2)
            self.game.story_manager.inventory["REVIVE"] -= 1
            if self.game.story_manager.inventory["REVIVE"] <= 0:
                del self.game.story_manager.inventory["REVIVE"]
            if self.game.assets.heal_sfx:
                self.game.assets.heal_sfx.play()

            if self.context == "battle":
                if p == self.previous_state.player_pokemon:
                    self.previous_state.player_hp = p.current_hp
                self.game.change_state(self.previous_state)
                self.previous_state.show_message([f"{self.game.player_name} used a REVIVE!", msg,
                                                  f"{p.display_name} has {p.current_hp} HP."],
                                                 callback=self.previous_state.on_item_used)
                return

        self._back_to_bag([msg])

    def draw(self):
        """The menu frame (src/ui/theme.py) in the Bag's orange: pocket tabs, item cards, and the
        bar with what the item under the pointer does."""
        screen = self.game.screen
        f = self.game.assets.fonts
        accent = theme.ACCENT["bag"]
        theme.menu_background(screen, accent, "BAG", f["button"], title_x=176)
        Utils.draw_text_outline(screen, f"${self.game.story_manager.money}", f["button"], WHITE,
                                self.game.width - 24, theme.HEADER_H // 2 - 4, align="right",
                                outline_color=theme.shade(accent, 0.45), thickness=3)
        if not self.item_buttons:
            theme.shadow_text(screen, "Nothing in this pocket yet.", f["s_med"], self.list_rect.centerx,
                              self.list_rect.centery, color=(200, 206, 222), shadow=theme.MENU_BG, align="center")

        mouse = pygame.mouse.get_pos()
        hovered = next((b for b in self.item_buttons if b.rect.collidepoint(mouse)), None)
        if hovered is not None:
            from src.pokemon import items as itemlib_
            text = itemlib_.describe(hovered.key) or (
                "Tap to use it." if hovered.usable else "Tap to see when it's used.")
            line = f"{hovered.name}: {text}"
        else:
            line = "Tap an item to use it."
        bf = f["label"]
        from src.ui.dialogue import wrap_text
        right = self.btn_items_up.rect.x - 90 if self.item_page_count > 1 else self.bar_rect.right - 32
        rows = wrap_text(line, bf, right - self.bar_rect.x - 32)[:2]
        theme.draw_textbox(screen, self.bar_rect)
        lh = bf.get_linesize() + 4
        top = self.bar_rect.centery - lh * len(rows) // 2 - 1
        for k, row in enumerate(rows):
            theme.shadow_text(screen, row, bf, self.bar_rect.x + 32, top + k * lh)
        if self.item_page_count > 1:
            theme.shadow_text(screen, f"{self.item_page + 1}/{self.item_page_count}", f["s_med"],
                              self.btn_items_up.rect.x - 16, self.bar_rect.centery - 14, align="right")

        self.game.ui_manager.draw(screen)


class ItemCountState(GameState):
    """How many of an item to use at once (Rare Candies): -10 / -1 / +1 / +10 / MAX, then USE."""

    def __init__(self, game, previous_state, pokemon, item, most, preview, on_use):
        super().__init__(game)
        self.previous_state = previous_state
        self.pokemon, self.item, self.most = pokemon, item, most
        self.preview, self.on_use = preview, on_use
        self.count = 1
        fonts = game.assets.fonts
        cx, y = game.width // 2, game.height - 230
        self.buttons = [Button((cx - 330 + i * 135, y, 120, 64), label, fonts["small"],
                               (lambda d=d: self.change(d)), autosize=False)
                        for i, (label, d) in enumerate((("-10", -10), ("-1", -1), ("+1", 1), ("+10", 10),
                                                        ("MAX", most)))]
        self.buttons.append(Button((cx - 270, y + 90, 250, 70), "USE", fonts["small"],
                                   lambda: self.on_use(self.count), bg_color=GREEN, autosize=False))
        self.buttons.append(Button((cx + 20, y + 90, 250, 70), "CANCEL", fonts["small"],
                                   lambda: self.on_use(0), bg_color=RED, autosize=False))
        img = pokemon.image or pokemon.sidebar_image
        self.sprite = pygame.transform.scale(img, (220, 220)) if img else None

    def change(self, d):
        self.count = max(1, min(self.most, self.count + d))

    def start(self):
        for btn in self.buttons:
            self.game.ui_manager.add_element(btn)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_UP, pygame.K_RIGHT):
                self.change(1)
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_DOWN, pygame.K_LEFT):
                self.change(-1)

    def update(self):
        pass

    def draw(self):
        screen = self.game.screen
        fonts = self.game.assets.fonts
        cx = self.game.width // 2
        from src.world import hms
        name = hms.item_name(self.item).upper()
        theme.menu_background(screen, theme.ACCENT["bag"], "USE HOW MANY?", fonts["button"], title_x=24)
        Utils.draw_text_outline(screen, f"{name}: {self.game.story_manager.inventory.get(self.item, 0)} in the Bag",
                                fonts["label"], WHITE, self.game.width - 24, theme.HEADER_H // 2 - 4, align="right",
                                outline_color=theme.shade(theme.ACCENT["bag"], 0.45), thickness=2)
        card = pygame.Rect(cx - 360, theme.HEADER_H + 20, 720, 340)
        theme.card(screen, card, radius=16)
        if self.sprite:
            spr = fit_sprite(self.sprite, 200, 170)
            screen.blit(spr, spr.get_rect(center=(cx, card.y + 100)))
        theme.shadow_text(screen, self.pokemon.display_name.upper(), fonts["s_med"], cx, card.y + 200, align="center")
        theme.shadow_text(screen, f"x{self.count}", fonts["big"], cx, card.y + 252, align="center")
        theme.shadow_text(screen, f"{self.preview(self.count)}   (up to {self.most})", fonts["label"], cx,
                          card.y + 302, color=(110, 116, 136), align="center")
        self.game.ui_manager.draw(screen)


# [REF-0038: Pokedex UI]
class PokedexState(GameState):
    COLS, ROWS = 6, 3
    PER_PAGE = COLS * ROWS

    def normal_dex_ids(self, caught_data, seen_ids):
        return _dex_ids(self.game.story_manager, caught_data, seen_ids, getattr(self, "dex_view", None))

    def dex_views(self):
        """Regional dexes the player has, then the National Dex once it's unlocked."""
        story = self.game.story_manager
        views = dex_regions(story)
        if story.story_flags.get("unlocked_national_dex") or len(views) > 1:
            views = views + ["NATIONAL"]
        return views

    def cycle_dex_view(self):
        views = self.dex_views()
        self.dex_view = views[(views.index(self.dex_view) + 1) % len(views)] if self.dex_view in views else views[0]
        self.btn_dex_view.text = f"{self.dex_view.title()} Dex"
        self.page = 0
        self.refresh_dex()

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

        # Which Pokedex: this region's own (as in the games), another region's, or the National Dex.
        views = self.dex_views()
        here = game.story_manager.get_current_region()
        self.dex_view = here if here in views else views[0]
        f = game.assets.fonts
        H = theme.HEADER_H
        self.btn_dex_view = CommandButton((game.width // 2 - 140, 14, 280, 56), f"{self.dex_view.title()} Dex",
                                          f["button"], self.cycle_dex_view, bg_color=theme.BAG, autosize=False)
        self.refresh_dex()

        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.go_back, bg_color=theme.BACK,
                                      autosize=False)
        # Tapping an entry: its cry, where it lives, its summary (a small panel beside it).
        self.btn_cry = CommandButton((0, 0, 160, 50), "CRY", f["label"], self.play_selected_cry,
                                     bg_color=theme.RUN, visible=False, autosize=False)
        self.btn_area = CommandButton((0, 0, 160, 50), "AREA", f["label"], self.show_selected_area,
                                      bg_color=theme.POKEMON, visible=False, autosize=False)
        self.btn_info = CommandButton((0, 0, 160, 50), "INFO", f["label"], self.show_selected_info,
                                      bg_color=theme.BAG, visible=False, autosize=False)
        self.popup_rect.height = 190

        # The filter row under the header: the tabs at the left, SHINIES and SORT at the right.
        row_y, row_h = H + 14, 50
        self.btn_shiny_toggle = CommandButton((game.width - 24 - 300, row_y, 150, row_h), "SHINIES", f["label"],
                                              self.toggle_shiny_filter, bg_color=theme.TAB_OFF, autosize=False)
        self.btn_sort = CommandButton((game.width - 24 - 140, row_y, 140, row_h), "SORT: #", f["label"],
                                      self.toggle_sort, bg_color=theme.TAB_OFF, autosize=False)
        self.tab_buttons = []
        for k, (label, tab) in enumerate((("NORMAL", "normal"), ("MEGA", "mega"), ("GMAX", "gmax"),
                                          ("ALT", "alt"), ("BOSS", "boss"), ("UNOWN", "unown"))):
            btn = CommandButton((24 + k * 146, row_y, 138, row_h), label, f["label"],
                                (lambda t=tab: self.set_tab(t)), bg_color=theme.TAB_OFF, autosize=False)
            btn.tab = tab
            self.tab_buttons.append(btn)
        (self.btn_tab_normal, self.btn_tab_mega, self.btn_tab_gmax,
         self.btn_tab_alt, self.btn_tab_boss, self.btn_tab_unown) = self.tab_buttons

        # Grid of entries, then the page bar (the battle text box) with its arrows.
        self.grid_rect = pygame.Rect(24, row_y + row_h + 16, game.width - 48, 0)
        self.bar_rect = pygame.Rect(16, game.height - 86, game.width - 32, 78)
        self.grid_rect.height = self.bar_rect.top - 14 - self.grid_rect.top
        self.btn_prev = pygame.Rect(self.bar_rect.x + 18, self.bar_rect.y + 12, 120, self.bar_rect.h - 28)
        self.btn_next = pygame.Rect(self.bar_rect.right - 138, self.bar_rect.y + 12, 120, self.bar_rect.h - 28)
        self.dex_btns = []

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.add_element(self.btn_back)
        self.game.ui_manager.add_element(self.btn_dex_view)
        self.game.ui_manager.add_element(self.btn_shiny_toggle)
        self.game.ui_manager.add_element(self.btn_sort)
        self.game.ui_manager.add_element(self.btn_cry)
        self.game.ui_manager.add_element(self.btn_area)
        self.game.ui_manager.add_element(self.btn_info)
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
        self.btn_info.set_visibility(False)

    def _caught_entry(self, pid):
        return next((v for v in self.game.data.data.get("pokedex", {}).values()
                     if isinstance(v, dict) and int(v.get("id", -1)) == int(pid)), None)

    def show_selected_info(self):
        """The summary page for a caught species (cycle its forms there)."""
        entry = self._caught_entry(self.selected_pkmn_id) if self.selected_pkmn_id else None
        self.hide_popup()
        if not entry:
            return
        mon = Pokemon(self.game.loader.fetch_specific(int(entry["id"]), form=entry.get("form", "normal")),
                      self.game.assets, size_mult=2.5)
        self.game.change_state(PokemonDetailState(self.game, mon, self))

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

            id_list = self.normal_dex_ids(caught_data, seen_ids)

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

                if self.btn_next.collidepoint(event.pos) and (self.page + 1) * self.PER_PAGE < len(self.full_dex):
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
                            self.btn_info.rect.topleft = (self.popup_rect.x + 10, self.popup_rect.y + 130)
                            if self.popup_rect.bottom > self.game.height:
                                self.popup_rect.bottom = self.game.height - 10
                                for k, btn in enumerate((self.btn_cry, self.btn_area, self.btn_info)):
                                    btn.rect.topleft = (self.popup_rect.x + 10, self.popup_rect.y + 10 + 60 * k)
                            self.btn_cry.set_visibility(True)
                            self.btn_area.set_visibility(True)
                            self.btn_info.set_visibility(bool(self._caught_entry(p_id)))
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
        """The menu frame (src/ui/theme.py): red header with the Dex and its count, the filter row,
        a grid of entry cards, the page bar."""
        screen = self.game.screen
        width = self.game.width
        f = self.game.assets.fonts
        accent = theme.ACCENT["dex"]
        theme.menu_background(screen, accent)

        if self.current_tab == "normal" and not self.show_shinies_only:
            in_view = [e for e in self.full_dex if e.get("id") != self.game.loader.get_special_id("NOWN", 3025)]
            caught_text = f"Caught {sum(1 for e in in_view if e['status'] == 2)} / {len(in_view)}"
        else:
            total_caught = len({v['id'] for v in self.game.data.data["pokedex"].values() if isinstance(v, dict) and 'id' in v})
            caught_text = f"Caught {total_caught}"
        Utils.draw_text_outline(screen, caught_text, f["button"], WHITE, width - 24, theme.HEADER_H // 2 - 4,
                                align="right", outline_color=theme.shade(accent, 0.45), thickness=3)
        Utils.draw_text_outline(screen, "POKéDEX", f["button"], WHITE, 176, theme.HEADER_H // 2 - 4,
                                align="left", outline_color=theme.shade(accent, 0.45), thickness=3)

        for btn in self.tab_buttons:
            btn.bg_color = accent if btn.tab == self.current_tab else theme.TAB_OFF
        self.btn_shiny_toggle.bg_color = theme.BAG if self.show_shinies_only else theme.TAB_OFF
        self.btn_sort.bg_color = theme.TAB_OFF

        cols, rows, per_page = self.COLS, self.ROWS, self.PER_PAGE
        start_idx = self.page * per_page
        current_view = self.full_dex[start_idx: start_idx + per_page]
        gap = 14
        cw = (self.grid_rect.w - gap * (cols - 1)) // cols
        ch = (self.grid_rect.h - gap * (rows - 1)) // rows
        mouse = pygame.mouse.get_pos()
        nown_id = self.game.loader.get_special_id("NOWN", 3025)

        self.dex_btns = []
        hovered = None
        for i in range(per_page):
            c, r = i % cols, i // cols
            rect = pygame.Rect(self.grid_rect.x + c * (cw + gap), self.grid_rect.y + r * (ch + gap), cw, ch)
            if i >= len(current_view):
                pygame.draw.rect(screen, theme.shade(theme.MENU_BG, 1.25), rect, border_radius=12)
                continue
            p_entry = current_view[i]
            status = p_entry.get("status", 2)
            hover = status > 0 and rect.collidepoint(mouse) and not self.popup_active
            theme.card(screen, rect, hover=hover, accent=accent,
                       fill=theme.TEXTBOX if status else (214, 218, 228))

            id_num = p_entry['id']
            prefix = ""
            if isinstance(id_num, int) and id_num >= 2000:
                mapping = self.game.loader.area_data.get("FORM_MAP", {}).get(str(id_num))
                if mapping:
                    id_num = mapping.get("id", id_num)
                    prefix = f"{p_entry.get('form', '')} ".title()
            display_id = "???" if p_entry['id'] == nown_id else (
                f"{prefix}No.{id_num:03d}" if isinstance(id_num, int) else f"{prefix}#{id_num}")
            theme.shadow_text(screen, display_id, f["label"], rect.x + 12, rect.y + 8)
            name = p_entry["name"].title() if p_entry["name"] != "???" else "???"
            nf = f["label"] if f["label"].size(name)[0] <= rect.w - 16 else f["caption"]
            theme.shadow_text(screen, name, nf, rect.centerx, rect.bottom - 20, align="center")

            if status > 0:
                icon = fit_sprite(self.game.assets.get_pokemon_image(
                    p_entry["id"], p_entry.get("form", "normal"), p_entry.get("shiny", False)
                ), rect.w - 40, rect.h - 62)
                if status == 1:  # seen, not caught: a silhouette
                    icon.fill((40, 40, 48), special_flags=pygame.BLEND_RGB_MULT)
                screen.blit(icon, icon.get_rect(center=(rect.centerx, rect.centery + 1)))
                if hover:
                    hovered = p_entry
                if status == 2 and self.game.assets.ui_ball:
                    ball = pygame.transform.scale(self.game.assets.ui_ball, (22, 22))
                    screen.blit(ball, (rect.right - 30, rect.y + 8))
                if p_entry.get("shiny"):
                    Utils.draw_star(screen, GOLD, (rect.right - 46, rect.top + 19), 10)
                if p_entry.get("gmax") and status == 2:
                    _draw_gmax_tag(screen, f["tiny"], rect.left + 8, rect.bottom - 46)
                self.dex_btns.append((rect, p_entry["id"]))
            else:
                theme.shadow_text(screen, "?", f["big"], rect.centerx, rect.centery, color=(150, 156, 172),
                                  align="center")

        # The page bar: < Page 2 / 9 >
        pages = max(1, -(-len(self.full_dex) // per_page))
        theme.draw_textbox(screen, self.bar_rect)
        page_text = f"Page {self.page + 1} / {pages}"
        bf = f["s_med"]
        ty = self.bar_rect.centery - bf.get_height() // 2 - 2
        theme.shadow_text(screen, page_text, bf, self.btn_next.x - 24, ty, align="right")
        if hovered:  # the entry under the pointer
            state = "Caught" if hovered.get("status") == 2 else "Seen"
            hint = f"{hovered['name'].title()}  -  {state}" + ("  (shiny)" if hovered.get("shiny") else "")
        else:
            hint = "Tap one: cry, area, info"
        theme.shadow_text(screen, hint, bf, self.btn_prev.right + 24, ty)
        for rect, label, ok in ((self.btn_prev, "<", self.page > 0),
                                (self.btn_next, ">", (self.page + 1) * per_page < len(self.full_dex))):
            theme.command_button(screen, rect, label, f["button"], accent if ok else theme.TAB_OFF,
                                 hover=ok and rect.collidepoint(mouse))

        if self.popup_active:  # the panel behind CRY / AREA / INFO
            theme.draw_panel(screen, self.popup_rect.inflate(8, 8))
        self.game.ui_manager.draw(screen)


def fit_sprite(img, max_w, max_h):
    """A Pokemon sprite without its empty margin, scaled (whole pixels where it can) to fit."""
    ink = img.get_bounding_rect()
    if ink.w and ink.h:
        img = img.subsurface(ink).copy()
    k = min(max_w / img.get_width(), max_h / img.get_height())
    return pygame.transform.scale(img, (max(1, int(img.get_width() * k)), max(1, int(img.get_height() * k))))


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
            r for r, cfg in starts
            if (story.story_flags.get(f"unlocked_{r.lower()}_badges") or story.badges.get(r))
            and not cfg.get("no_badges")  # Orre has no Gyms
        ] or [story.starting_region]

        home = game.story_manager.starting_region
        self.unlocked_regions.sort(key=lambda r: 0 if r == home else 1)

        self.current_page_idx = 0

        f = game.assets.fonts
        # The menu frame in the region's colour: the case (8 pockets) and the bar along the bottom
        # with the count and the region arrows.
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.go_back, bg_color=theme.BACK,
                                      autosize=False)
        self.bar_rect = pygame.Rect(16, game.height - 86, game.width - 32, 78)
        self.case_rect = pygame.Rect(24, theme.HEADER_H + 16, game.width - 48,
                                     self.bar_rect.top - 12 - theme.HEADER_H - 16)
        bh = self.bar_rect.h - 28
        self.btn_prev = CommandButton((self.bar_rect.right - 18 - 230, self.bar_rect.y + 12, 110, bh), "<",
                                      f["button"], self.prev_page, bg_color=theme.TAB_OFF, autosize=False)
        self.btn_next = CommandButton((self.bar_rect.right - 18 - 110, self.bar_rect.y + 12, 110, bh), ">",
                                      f["button"], self.next_page, bg_color=theme.TAB_OFF, autosize=False)

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

    REGION_COLORS = {"KANTO": (196, 58, 52), "JOHTO": (52, 84, 170), "HOENN": (44, 140, 84),
                     "SINNOH": (110, 78, 168), "UNOVA": (70, 74, 86), "KALOS": (40, 112, 178),
                     "ALOLA": (214, 128, 40), "GALAR": (168, 44, 92), "PALDEA": (200, 82, 44),
                     "ORANGE": (226, 132, 30)}

    def _badge_name(self, region, i):
        """The badge in pocket i ("Boulder Badge"), from the region's own list."""
        for name, n in self.region_maps.get(region, {}).items():
            if n == i:
                words = name.replace("_", " ").title().replace("Badge", "").strip()
                return f"{words} Badge"
        return f"Badge {i}"

    def draw(self):
        screen = self.game.screen
        f = self.game.assets.fonts
        region = self.unlocked_regions[self.current_page_idx] if self.unlocked_regions else "KANTO"
        accent = self.REGION_COLORS.get(region, theme.ACCENT["journal"])
        theme.menu_background(screen, accent, f"{region} BADGES", f["button"], title_x=176)

        badge_map = self.region_maps.get(region, {})
        earned_list = self.earned_badges.get(region, [])
        count = max(badge_map.values(), default=8)
        earned_n = sum(1 for i in range(1, count + 1) if any(badge_map.get(b) == i for b in earned_list))
        Utils.draw_text_outline(screen, f"{earned_n} / {count}", f["button"], WHITE, self.game.width - 24,
                                theme.HEADER_H // 2 - 4, align="right", outline_color=theme.shade(accent, 0.45),
                                thickness=3)

        # The case: a panel with a velvet pocket for each badge.
        theme.draw_panel(screen, self.case_rect)
        inner = self.case_rect.inflate(-32, -32)
        cols = 4
        rows = (count + cols - 1) // cols
        gap = 16
        cw = (inner.w - gap * (cols - 1)) // cols
        ch = (inner.h - gap * (rows - 1)) // rows
        mouse = pygame.mouse.get_pos()
        hovered = None
        for i in range(1, count + 1):
            c, r = (i - 1) % cols, (i - 1) // cols
            pocket = pygame.Rect(inner.x + c * (cw + gap), inner.y + r * (ch + gap), cw, ch)
            earned = any(badge_map.get(b) == i for b in earned_list)
            velvet = theme.shade(accent, 0.45)
            pygame.draw.rect(screen, velvet, pocket, border_radius=14)
            pygame.draw.rect(screen, theme.shade(accent, 0.75) if earned else theme.shade(accent, 0.3), pocket, 3,
                             border_radius=14)
            spot = (pocket.centerx, pocket.y + (pocket.h - 34) // 2)
            pygame.draw.circle(screen, theme.shade(velvet, 0.75), spot, min(cw, ch - 34) // 2 - 6)
            sprite = self.badge_sprites.get(region, {}).get(i)
            if sprite:
                img = sprite.copy()
                if not earned:  # a faint outline where it will go
                    img.fill((60, 60, 70), special_flags=pygame.BLEND_RGB_MULT)
                    img.set_alpha(110)
                screen.blit(img, img.get_rect(center=spot))
            name = self._badge_name(region, i) if earned else f"#{i}"
            Utils.draw_text_outline(screen, name, f["label"] if f["label"].size(name)[0] <= cw - 12 else f["caption"],
                                    WHITE if earned else (150, 154, 170), pocket.centerx, pocket.bottom - 20,
                                    outline_color=theme.shade(velvet, 0.6), thickness=2)
            if pocket.collidepoint(mouse):
                hovered = (i, earned)

        # The bar: the badge under the pointer, else how many; the region arrows.
        if hovered:
            i, earned = hovered
            line = f"{self._badge_name(region, i)} - earned!" if earned else f"Badge #{i}: not yet earned."
        else:
            line = f"{earned_n} of {count} {region.title()} badges."
        theme.draw_textbox(screen, self.bar_rect)
        bf = f["s_med"]
        theme.shadow_text(screen, line, bf, self.bar_rect.x + 32, self.bar_rect.centery - bf.get_height() // 2 - 2)
        if len(self.unlocked_regions) > 1:
            theme.shadow_text(screen, "Region", f["label"], self.btn_prev.rect.x - 16, self.bar_rect.centery - 12,
                              align="right")
        self.game.ui_manager.draw(screen)


# [REF-0041: Evolution Logic]
class EvolutionState(GameState):
    def __init__(
        self, game, pokemon_to_evolve, evolution_id, team_index, next_form="normal", context="party", return_state=None, consume_catch_count=False,
        choices=None
    ):
        """choices: evolution entries ("SOLGALEO", "LUNALA") when more than one is ready; the player
        picks one on this screen (Jordan: Cosmoem)."""
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
        btn_w, btn_h = 180, 64  # (the battle's YES / NO)
        self.btn_yes = CommandButton((box.right - 2 * btn_w - 46, box.centery - btn_h // 2, btn_w, btn_h), "YES",
                                     game.assets.fonts["button"], self.evolve_yes, bg_color=theme.POKEMON,
                                     visible=False, autosize=False)
        self.btn_no = CommandButton((box.right - btn_w - 28, box.centery - btn_h // 2, btn_w, btn_h), "NO",
                                    game.assets.fonts["button"], self.evolve_no, bg_color=theme.FIGHT,
                                    visible=False, autosize=False)
        # Branch choice: one button per evolution in place of YES.
        self.choice_buttons = []
        for k, entry in enumerate(choices or []):
            base, form = (entry.rsplit("_", 1) + ["normal"])[:2] if "_" in entry else (entry, "normal")
            pid = game.name_to_id.get(base.upper())
            if not pid:
                continue
            label = base.replace("-", " ").upper() + ("" if form == "normal" else f" ({form.title()})")
            self.choice_buttons.append(Button(
                rect=(box.right - 150 - 230 * (len(choices) - k), box.centery - 30, 220, btn_h), text=label,
                font=game.assets.fonts["tiny"], callback=lambda p=pid, f=form.lower(): self.choose(p, f),
                bg_color=GREEN, visible=False, autosize=False))
        if len(self.choice_buttons) < 2:
            self.choice_buttons = []

    def choose(self, pid, form):
        self.evolution_id, self.next_form = pid, form
        for btn in self.choice_buttons:
            btn.set_visibility(False)
        self.evolve_yes()

    def evolve_yes(self):
        self.phase = "START"
        self.btn_yes.set_visibility(False)
        self.btn_no.set_visibility(False)
        self.timer = 60
        if self.pokemon.cry:
            self.pokemon.cry.play()

    def evolve_no(self):
        # Not again this round, or declining would just bring the same question back.
        self.game.evo_declined = getattr(self.game, "evo_declined", set()) | {id(self.pokemon)}
        self._return()

    def start(self):
        self.game.ui_manager.add_element(self.btn_yes)
        self.game.ui_manager.add_element(self.btn_no)
        for btn in self.choice_buttons:
            self.game.ui_manager.add_element(btn)
        if self.phase == "DECISION":
            self.btn_yes.set_visibility(not self.choice_buttons)
            self.btn_no.set_visibility(True)
            for btn in self.choice_buttons:
                btn.set_visibility(True)

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
                # What the Pokémon has earned stays with it through evolution.
                for attr in ("level", "xp", "friendship", "affection", "everstone", "counters", "condition", "sheen", "ribbons",
                             "gmax_factor", "caught_region", "ivs", "moves", "move_pool", "status"):
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

                    # Damage carries over (a fainted Pokemon stays fainted), like the games.
                    old_max = self.pokemon.get_max_hp()
                    new_max = self.evolved_pokemon_obj.get_max_hp()
                    old_hp = self.pokemon.current_hp
                    self.evolved_pokemon_obj.current_hp = (
                        0 if old_hp <= 0 else max(1, min(new_max, old_hp + new_max - old_max)))
                    self.game.data.add_pokemon(self.evolved_pokemon_obj)
                    self._maybe_shedinja()

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

    def _maybe_shedinja(self):
        """Nincada -> Ninjask also leaves a Shedinja behind (as in the games). It is a new
        Pokemon built from the Nincada (same level, IVs, shininess, home region); it joins the
        party, or goes to the PC when the party is full, and both land in the Pokedex."""
        if self.pokemon.id != 290 or self.evolution_id != 291:
            return
        story = self.game.story_manager
        nincada = self.pokemon
        shiny = bool(getattr(nincada, "is_shiny", False))
        shed = Pokemon(self.game.loader.fetch_specific(292, is_shiny=shiny), self.game.assets, size_mult=2.5)
        shed.is_shiny = shiny
        shed.level = nincada.level
        for attr in ("ivs", "caught_region"):
            if hasattr(nincada, attr):
                setattr(shed, attr, getattr(nincada, attr))
        shed.current_hp = shed.get_max_hp()
        if len(story.player_team) < 6:
            story.player_team.append(shed)
            self.shedinja_where = "party"
        else:
            story.deposit_to_pc(shed)
            self.shedinja_where = "pc"
        self.game.data.add_pokemon(shed)
        self.shedinja_added = True

    def _return(self):
        pygame.event.clear()
        # Several Pokemon can be ready at once (as in the games): evolve the next one first.
        if self.context == "party":
            from src.states.overworld import evolve_ready_party
            back_to = self.return_state or self.game.states.get("play")
            if back_to is not None and evolve_ready_party(self.game, back_to):
                return
        self.game.evo_declined = set()
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
            theme.draw_textbox(self.game.screen, box_rect)
            if self.is_hatching:
                text = f"What? The {self.original_name} is hatching!"
            else:
                text = f"What? {self.original_name} is evolving!"
            from src.ui.dialogue import wrap_text
            f = self.game.assets.fonts["dialog"]
            rows = wrap_text(text, f, box_rect.width * 0.55)
            lh = int(f.get_linesize() * 1.2)
            top = box_rect.centery - lh * len(rows) // 2
            for k, row in enumerate(rows):
                theme.shadow_text(self.game.screen, row, f, box_rect.x + 40, top + k * lh)
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
PURPLE_BTN = (120, 70, 170)


class PokemonDetailState(GameState):
    STAT_ROWS = (("HP", "HP"), ("ATTACK", "Attack"), ("DEFENSE", "Defense"),
                 ("SPATK", "Sp. Atk"), ("SPDEF", "Sp. Def"), ("SPEED", "Speed"))
    STATUS_TEXT = {"burn": "BURNED", "paralysis": "PARALYZED", "poison": "POISONED",
                   "toxic": "BADLY POISONED", "sleep": "ASLEEP", "freeze": "FROZEN"}

    def __init__(self, game, pokemon, previous_state):
        super().__init__(game)
        self.pokemon = pokemon
        self.own = pokemon  # the Pokemon this summary was opened for
        self.previous_state = previous_state
        self.tab = "INFO"
        # Every form of this species the player has obtained (regional, Pinkan, Valencia, Shadow...).
        self.forms = self._obtained_forms(pokemon)
        self.form_idx = 0
        f = game.assets.fonts
        H = theme.HEADER_H
        # The menu frame: the portrait card at the left, the tab's cards at the right, the text box
        # along the bottom; BACK and the INFO / STATS / MOVES tabs in the header.
        self.bar_rect = pygame.Rect(16, game.height - 86, game.width - 32, 78)
        self.portrait = pygame.Rect(24, H + 16, 360, self.bar_rect.top - 12 - H - 16)
        self.content = pygame.Rect(self.portrait.right + 16, self.portrait.y,
                                   game.width - 24 - self.portrait.right - 16, self.portrait.h)
        fy = self.portrait.y + 300
        self.btn_form_prev = CommandButton((self.portrait.x + 16, fy, 60, 48), "<", f["button"],
                                           lambda: self.cycle_form(-1), bg_color=theme.MEGA, autosize=False)
        self.btn_form_next = CommandButton((self.portrait.right - 76, fy, 60, 48), ">", f["button"],
                                           lambda: self.cycle_form(1), bg_color=theme.MEGA, autosize=False)
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.go_back, bg_color=theme.BACK,
                                      autosize=False)
        tab_w, gap = 150, 10
        tabs = [("INFO", "INFO"), ("STATS", "STATS"), ("MOVES", "MOVES")]
        x0 = game.width - 24 - len(tabs) * tab_w - (len(tabs) - 1) * gap
        self.tab_buttons = {
            key: CommandButton((x0 + i * (tab_w + gap), 14, tab_w, 56), label, f["label"],
                               (lambda k=key: self.show_tab(k)), bg_color=theme.TAB_OFF, autosize=False)
            for i, (key, label) in enumerate(tabs)}
        # MOVES tab (Legends: Z-A style): pick the four moves it uses from its move pool.
        self.sel_slot = None
        self.pool_page = 0
        self.move_msg = "Tap one of its moves, then a move from the pool to swap it in."
        self.slot_rects, self.pool_rects = [], []
        self.page_prev = self.page_next = None
        # STATS tab: the bars judge each stat (as the games show it), or show its IVs (the games'
        # judge view); a tap on the card's button switches.
        self.stat_view = "STATS"
        self.view_rect = None
        self._color_tabs()

    def show_tab(self, tab):
        self.tab = tab
        self._color_tabs()

    def _obtained_forms(self, pokemon):
        """[pokemon] + a display Pokemon for each other obtained form of its species (Pokedex data)."""
        form_map = self.game.loader.area_data.get("FORM_MAP", {})

        def species(pid):
            pid = int(pid)
            return int((form_map.get(str(pid)) or {}).get("id", pid)) if pid >= 2000 else pid

        base = species(pokemon.id)
        seen = {pokemon.form}  # one page per form (an evolved Crystal Onix and a caught one are the same form)
        out = [pokemon]
        entries = sorted((v for v in self.game.data.data.get("pokedex", {}).values()
                          if isinstance(v, dict) and "id" in v), key=lambda v: (int(v["id"]) >= 2000, int(v["id"])))
        for v in entries:
            pid, form = int(v["id"]), v.get("form", "normal")
            if species(pid) != base or form in seen or form == "gmax" or str(form).startswith("mega"):
                continue
            seen.add(form)
            try:
                mon = Pokemon(self.game.loader.fetch_specific(pid, form=form), self.game.assets, size_mult=2.5)
            except Exception:
                continue
            mon.level = pokemon.level
            out.append(mon)
        return out

    def cycle_form(self, step):
        if len(self.forms) > 1:
            self.form_idx = (self.form_idx + step) % len(self.forms)
            self.pokemon = self.forms[self.form_idx]

    def _color_tabs(self):
        for name, btn in self.tab_buttons.items():
            btn.bg_color = theme.BAG if name == self.tab else theme.TAB_OFF

    def go_back(self):
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.elements.clear()
        self.game.ui_manager.add_element(self.btn_back)
        for btn in self.tab_buttons.values():
            self.game.ui_manager.add_element(btn)
        if len(self.forms) > 1:
            self.game.ui_manager.add_element(self.btn_form_prev)
            self.game.ui_manager.add_element(self.btn_form_next)

    TAB_ORDER = ("INFO", "STATS", "MOVES")

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                step = -1 if event.key == pygame.K_LEFT else 1
                i = self.TAB_ORDER.index(self.tab) if self.tab in self.TAB_ORDER else 0
                self.show_tab(self.TAB_ORDER[(i + step) % len(self.TAB_ORDER)])
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_UP, pygame.K_DOWN):
                self.cycle_form(-1 if event.key == pygame.K_UP else 1)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.tab == "MOVES":
                self.click_moves(event.pos)
            elif (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.tab == "STATS"
                  and self.view_rect and self.view_rect.collidepoint(event.pos)):
                self.toggle_stat_view()

    def toggle_stat_view(self):
        self.stat_view = "IVS" if self.stat_view == "STATS" else "STATS"

    def stat_rating(self, key, value):
        """How strong a stat is for the Pokemon's level, 0-1: against about what a strong stat of
        that kind is at that level (HP runs higher)."""
        lv = max(1, self.pokemon.level)
        strong = (2.2 * lv + 110) if key == "HP" else (2 * lv + 100)
        return max(0.0, min(1.0, value / strong))

    # --- MOVES tab: the move pool ---
    POOL_PER_PAGE = 5

    def _pool_choices(self):
        from src.pokemon import moves as movelib
        p = self.own
        movelib.ensure_moves(self.game, p)
        return [m for m in movelib.move_pool(self.game, p) if m not in p.moves]

    def click_moves(self, pos):
        from src.pokemon import moves as movelib
        p = self.own
        for i, r in enumerate(self.slot_rects):
            if r.collidepoint(pos):
                self.sel_slot = None if self.sel_slot == i else i
                self.move_msg = ("Now tap a move from the pool to put in this slot." if self.sel_slot is not None
                                 else "Tap one of its moves, then a move from the pool to swap it in.")
                return
        if self.page_prev and self.page_prev.collidepoint(pos):
            self.pool_page = max(0, self.pool_page - 1)
            return
        if self.page_next and self.page_next.collidepoint(pos):
            self.pool_page += 1
            return
        for r, name in self.pool_rects:
            if not r.collidepoint(pos):
                continue
            label = name.replace("-", " ").title()
            if self.sel_slot is None and len(p.moves) >= movelib.MAX_MOVES:
                self.move_msg = f"Tap one of its four moves first, then {label}."
                return
            old = p.moves[self.sel_slot] if self.sel_slot is not None and self.sel_slot < len(p.moves) else None
            if movelib.set_move(p, self.sel_slot, name):
                who = p.display_name.upper()
                self.move_msg = (f"{who} will use {label} instead of {old.replace('-', ' ').title()}."
                                 if old else f"{who} will use {label}.")
                self.sel_slot = None
            return

    def update(self):
        pass

    def _accent(self):
        """The header takes the Pokemon's own (first) type colour."""
        from src.states.battle import TrainerBattleState
        types = self.pokemon.types or []
        return theme.shade(TrainerBattleState.TYPE_COLORS.get(types[0], theme.ACCENT["summary"]), 0.9) \
            if types else theme.ACCENT["summary"]

    def _type_chips(self, x, y):
        from src.states.battle import TrainerBattleState
        f = self.game.assets.fonts
        for t in self.pokemon.types or []:
            color = TrainerBattleState.TYPE_COLORS.get(t, (120, 120, 120))
            chip = pygame.Rect(x, y, f["caption"].size(t.upper())[0] + 22, 28)
            pygame.draw.rect(screen := self.game.screen, color, chip, border_radius=14)
            pygame.draw.rect(screen, theme.shade(color, 0.6), chip, 2, border_radius=14)
            Utils.draw_text_outline(screen, t.upper(), f["caption"], WHITE, chip.centerx, chip.centery,
                                    outline_color=theme.shade(color, 0.5), thickness=2)
            x = chip.right + 8

    def _bar_line(self):
        """What the text box says for the tab on show."""
        p = self.pokemon
        if self.tab == "MOVES":
            own = self.own
            if self.sel_slot is not None and self.sel_slot < len(own.moves):
                from src.pokemon import moves as movelib
                name = own.moves[self.sel_slot]
                effect = movelib.info(self.game, name).get("effect") or ""
                if effect:
                    return f"{name.replace('-', ' ').title()}: {effect}"
            return self.move_msg
        if self.tab == "STATS":
            what = ("the bars show how strong each stat is for its level" if self.stat_view == "STATS"
                    else "the bars show its IVs (0-31), what it was born with")
            return (f"XP {p.xp}/{p.xp_to_next} to Lv {p.level + 1}" if p.xp_to_next else "MAX LEVEL") + \
                f"   -   {what}"
        from src.pokemon import evolution
        options = evolution.evolution_options(self.game, p)
        if options:
            entry, _, rule = options[0]
            name = entry.split("_")[0].replace("-", " ").title()
            more = f" (or {len(options) - 1} more)" if len(options) > 1 else ""
            return f"Evolves into {name}{more}: {evolution.condition_hint(rule)}"
        return "It doesn't evolve any further."

    def draw(self):
        from src.ui.dialogue import wrap_text
        screen, f = self.game.screen, self.game.assets.fonts
        accent = self._accent()
        theme.menu_background(screen, accent, "SUMMARY", f["button"], title_x=176)

        # The portrait card: hearts, the Pokemon, its name, level and types, the form arrows.
        p = self.pokemon
        r = self.portrait
        theme.card(screen, r)
        from src.ui.hearts import draw_hearts
        draw_hearts(screen, p, r.centerx, r.y + 24, size=18)
        if p.image:
            spr = fit_sprite(p.image, r.w - 60, 230)
            screen.blit(spr, spr.get_rect(center=(r.centerx, r.y + 160)))
        if getattr(p, "gmax_factor", False):
            _draw_gmax_tag(screen, f["small"], r.right - 90, r.y + 40)
        if len(self.forms) > 1:
            theme.shadow_text(screen, f"Form {self.form_idx + 1}/{len(self.forms)}", f["label"], r.centerx,
                              self.btn_form_prev.rect.centery, align="center")
        y = r.y + 364
        name = p.display_name.upper()
        theme.shadow_text(screen, name, f["s_med"] if f["s_med"].size(name)[0] <= r.w - 40 else f["label"],
                          r.x + 20, y)
        self._type_chips(r.x + 20, y + 40)
        lv = theme.shadow_text(screen, f"Lv{p.level}", f["label"], r.right - 20, y + 42, align="right")
        if self.pokemon is self.own:
            theme.status_tag(screen, "faint" if p.current_hp <= 0 else getattr(p, "status", None), f["caption"],
                             lv.x - 66, y + 41)
            theme.hp_bar(screen, r.x + 20, r.bottom - 40, r.w - 40, p.current_hp, p.get_max_hp())
            theme.shadow_text(screen, f"HP {int(p.current_hp)}/{p.get_max_hp()}", f["caption"], r.right - 20,
                              r.bottom - 26, align="right")

        if self.tab == "STATS":
            self._draw_stats_and_moves()
        elif self.tab == "MOVES":
            self._draw_move_pool()
        else:
            self._draw_info()

        theme.draw_textbox(screen, self.bar_rect)
        rows = wrap_text(self._bar_line(), f["label"], self.bar_rect.w - 64)[:2]
        lh = f["label"].get_linesize() + 4
        top = self.bar_rect.centery - lh * len(rows) // 2 - 1
        for k, row in enumerate(rows):
            theme.shadow_text(screen, row, f["label"], self.bar_rect.x + 32, top + k * lh)
        self.game.ui_manager.draw(screen)

    def _rows(self, rect, rows, label_w=150):
        """Label / value rows on a card."""
        f = self.game.assets.fonts
        y = rect.y + 18
        for label, value in rows:
            theme.shadow_text(screen := self.game.screen, label, f["label"], rect.x + 20, y, color=(110, 116, 136))
            theme.shadow_text(screen, str(value), f["label"], rect.x + 20 + label_w, y)
            y += 38
        return y

    def _draw_info(self):
        """INFO: who it is (left card), its contest condition (right card)."""
        p, c = self.pokemon, self.content
        left = pygame.Rect(c.x, c.y, c.w // 2 - 8, c.h)
        right = pygame.Rect(left.right + 16, c.y, c.right - left.right - 16, c.h)
        theme.card(self.game.screen, left)
        if p is self.own:
            rows = [("Name", p.display_name), ("Level", p.level),
                    ("XP", f"{p.xp}/{p.xp_to_next}" if p.xp_to_next else "MAX"),
                    ("HP", f"{int(p.current_hp)}/{p.get_max_hp()}"), ("Types", "/".join(t.title() for t in p.types)),
                    ("Status", self.STATUS_TEXT.get(getattr(p, "status", None) or "", "Healthy").title())]
            region = getattr(p, "caught_region", None)
            if region:
                rows.append(("Met in", str(region).title()))
        else:  # another form of this species from the Pokedex
            rows = [("Name", p.display_name), ("Form", str(p.form).title()),
                    ("Types", "/".join(t.title() for t in p.types))]
        if getattr(p, "gmax_factor", False):
            rows.append(("G-Max", "Yes"))
        if getattr(p, "everstone", False):
            rows.append(("Holding", "Everstone"))
        from src.world import seasons
        season_form = seasons.form_name(p.id)
        if season_form:
            rows.append(("Coat", season_form))
        self._rows(left, rows)
        self._draw_condition(right)

    def _draw_stats_and_moves(self):
        """STATS: the stats with IV bars (left card), the four moves (right)."""
        from src.pokemon import moves as movelib
        screen, p, f = self.game.screen, self.pokemon, self.game.assets.fonts
        c = self.content
        left = pygame.Rect(c.x, c.y, c.w // 2 - 8, c.h)
        right = pygame.Rect(left.right + 16, c.y, c.right - left.right - 16, c.h)
        theme.card(screen, left)
        x, y = left.x + 20, left.y + 18
        ivs = self.stat_view == "IVS"
        theme.shadow_text(screen, "IVs" if ivs else "STATS", f["label"], x, y, color=(110, 116, 136))
        self.view_rect = pygame.Rect(left.right - 16 - 186, left.y + 10, 186, 40)
        theme.command_button(screen, self.view_rect, "SHOW STATS" if ivs else "SHOW IVs", f["caption"],
                             theme.MEGA, hover=self.view_rect.collidepoint(pygame.mouse.get_pos()))
        y += 56
        for key, label in self.STAT_ROWS:
            value = p.get_max_hp() if key == "HP" else p.stat_value(key)
            theme.shadow_text(screen, label, f["label"], x, y)
            theme.shadow_text(screen, str(value), f["label"], x + 200, y, align="right")
            bar = pygame.Rect(x + 214, y + 4, left.right - 20 - (40 if ivs else 0) - x - 214, 14)
            pygame.draw.rect(screen, (210, 214, 224), bar, border_radius=7)
            share = p.iv(key) / 31 if ivs else self.stat_rating(key, value)
            fill = bar.copy()
            fill.width = max(4, int(bar.width * share))
            pygame.draw.rect(screen, theme.HP_GREEN if share >= 0.6 else theme.HP_YELLOW if share >= 0.35
                             else (220, 130, 96), fill, border_radius=7)
            if ivs:
                theme.shadow_text(screen, str(p.iv(key)), f["label"], left.right - 20, y, align="right")
            y += 50

        known = movelib.ensure_moves(self.game, p)[:4]
        h = (right.h - 3 * 12) // 4
        for i in range(4):
            r = pygame.Rect(right.x, right.y + i * (h + 12), right.w, h)
            if i < len(known):
                self._move_card(r, known[i])
            else:
                pygame.draw.rect(screen, theme.shade(theme.MENU_BG, 1.3), r, border_radius=12)

    def _move_card(self, rect, name, highlight=False):
        """A move in its type's colour (like the battle's move buttons): name, then type, category,
        power and accuracy."""
        from src.pokemon import moves as movelib
        from src.states.battle import TrainerBattleState
        screen, fonts = self.game.screen, self.game.assets.fonts
        d = movelib.info(self.game, name)
        color = TrainerBattleState.TYPE_COLORS.get(d.get("type"), (120, 120, 120))
        dark = theme.shade(color, 0.6)
        pygame.draw.rect(screen, dark, rect.move(0, 4), border_radius=12)
        pygame.draw.rect(screen, color, rect, border_radius=12)
        pygame.draw.rect(screen, GOLD if highlight else (20, 20, 30), rect, 5 if highlight else 3, border_radius=12)
        Utils.draw_text_outline(screen, name.replace("-", " ").upper(), fonts["label"], WHITE,
                                rect.x + 14, rect.y + 8, align="left", outline_color=dark, thickness=2)
        acc = f"{d['accuracy']}%" if d.get("accuracy") else "-"
        detail = (f"{str(d.get('type', '')).title()}  {str(d.get('category', '')).title()}  "
                  f"Pow {d.get('power') or '-'}  {acc}")
        Utils.draw_text_outline(screen, detail, fonts["caption"], WHITE, rect.x + 14, rect.bottom - 26, align="left",
                                outline_color=dark, thickness=2)

    def _draw_move_pool(self):
        """MOVES: its four moves (left), the rest of its move pool (right); tap a move, then a
        pool move to swap it in."""
        from src.pokemon import moves as movelib
        screen, fonts = self.game.screen, self.game.assets.fonts
        p = self.own
        movelib.ensure_moves(self.game, p)
        c = self.content
        half = c.w // 2 - 8
        left_x, right_x = c.x, c.x + half + 16
        top = c.y + 40
        Utils.draw_text_outline(screen, "ITS MOVES", fonts["label"], WHITE, left_x + 4, c.y + 10, align="left")
        self.slot_rects = []
        h = (c.bottom - top - 3 * 10) // 4
        for i in range(movelib.MAX_MOVES):
            r = pygame.Rect(left_x, top + i * (h + 10), half, h)
            self.slot_rects.append(r)
            if i < len(p.moves):
                self._move_card(r, p.moves[i], highlight=(self.sel_slot == i))
            else:
                pygame.draw.rect(screen, theme.shade(theme.MENU_BG, 1.3), r, border_radius=12)
                pygame.draw.rect(screen, GOLD if self.sel_slot == i else theme.PANEL_EDGE, r, 3, border_radius=12)
                Utils.draw_text_outline(screen, "- empty -", fonts["label"], LIGHT_GRAY, r.centerx, r.centery)
        choices = self._pool_choices()
        pages = max(1, -(-len(choices) // self.POOL_PER_PAGE))
        self.pool_page = min(self.pool_page, pages - 1)
        Utils.draw_text_outline(screen, f"MOVE POOL ({len(choices)})", fonts["label"], WHITE, right_x + 4, c.y + 10,
                                align="left")
        self.pool_rects = []
        foot = 52 if pages > 1 else 0
        ph = (c.bottom - top - foot - (self.POOL_PER_PAGE - 1) * 8) // self.POOL_PER_PAGE
        start = self.pool_page * self.POOL_PER_PAGE
        for i, name in enumerate(choices[start:start + self.POOL_PER_PAGE]):
            r = pygame.Rect(right_x, top + i * (ph + 8), half, ph)
            self.pool_rects.append((r, name))
            self._move_card(r, name)
        if not choices:
            Utils.draw_text_outline(screen, "No other moves learned yet.", fonts["label"], LIGHT_GRAY,
                                    right_x + 4, top + 20, align="left")
        self.page_prev = self.page_next = None
        if pages > 1:
            y = c.bottom - 44
            self.page_prev = pygame.Rect(right_x, y, 70, 44)
            self.page_next = pygame.Rect(right_x + half - 70, y, 70, 44)
            mouse = pygame.mouse.get_pos()
            for rr, label in ((self.page_prev, "<"), (self.page_next, ">")):
                theme.command_button(screen, rr, label, fonts["button"], theme.MEGA, hover=rr.collidepoint(mouse))
            Utils.draw_text_outline(screen, f"Page {self.pool_page + 1}/{pages}", fonts["label"], WHITE,
                                    right_x + half // 2, y + 22)

    def _draw_condition(self, rect):
        """Contest condition bars, Sheen and ribbons, on a card."""
        p = self.pokemon
        screen, f = self.game.screen, self.game.assets.fonts
        theme.card(screen, rect)
        cond = getattr(p, "condition", None) or {}
        x, y = rect.x + 20, rect.y + 18
        theme.shadow_text(screen, "CONDITION", f["label"], x, y, color=(110, 116, 136))
        y += 44
        rows = [(cat.title(), cond.get(cat, 0), CATEGORY_COLOR[cat]) for cat in CATEGORIES]
        rows.append(("Sheen", getattr(p, "sheen", 0), (170, 176, 196)))
        bar_x = x + 126
        for label, value, color in rows:
            theme.shadow_text(screen, label, f["label"], x, y)
            bar = pygame.Rect(bar_x, y + 4, rect.right - 20 - bar_x, 14)
            pygame.draw.rect(screen, (210, 214, 224), bar, border_radius=7)
            fill = bar.copy()
            fill.width = int(bar.w * min(value, MAX_CONDITION) / MAX_CONDITION)
            if fill.width:
                pygame.draw.rect(screen, color, fill, border_radius=7)
            y += 40
        ribbons = getattr(p, "ribbons", [])
        theme.shadow_text(screen, f"Ribbons: {len(ribbons)}", f["label"], x, y + 6, color=(170, 120, 20))
        if p.name.upper() == "FEEBAS" and not feebas_ready(p):
            theme.shadow_text(screen, f"Needs Beauty {FEEBAS_BEAUTY} to evolve", f["caption"], x, y + 40)


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
        elif self.game.story_manager.current_area_key == "GOLDENROD_CITY":
            # HeartGold/SoulSilver: the new Goldenrod shop has no customers yet, so it lends you a
            # bike to ride around and show off (Grok's Johto walk: there was no Bike Shop).
            lines = [
                "Welcome! We just opened, but nobody knows about us yet...",
                "Tell you what: ride one of our bikes around Johto and show it off for us!",
                "You received the BICYCLE!"
            ]
            inv["BICYCLE"] = 1
            if self.game.assets.heal_sfx:
                self.game.assets.heal_sfx.play()
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

    # The Rocket Hideout's boss on B4F (FireRed/LeafGreen): Giovanni, who drops the Silph Scope.
    HIDEOUT_GIOVANNI = ([95, 111, 115], [25, 24, 29])

    def next_rocket_battle(self):
        if self.rocket_progress >= 5:
            self.give_porygon()
            return
        if self.rocket_progress == 4:
            self.giovanni_battle()
            return

        rocket_pool = self.game.loader.area_data.get("TEAM_ROCKET_POOL", [19, 23, 52])
        team_ids = [random.choice(rocket_pool) for _ in range(2 + (self.rocket_progress // 2))]
        opponent_team = [Pokemon(self.game.loader.fetch_specific(pid), self.game.assets, size_mult=3.125) for pid in team_ids]
        # Same curve as other Celadon trainers, each grunt a little tougher than the last.
        from src.world import levels
        team_levels = levels.trainer_team_levels(self.game, "CELADON_CITY", len(opponent_team))
        levels.set_team(opponent_team, [lv + self.rocket_progress for lv in team_levels])

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

    def giovanni_battle(self):
        from src.world import levels
        team_ids, team_levels = self.HIDEOUT_GIOVANNI
        team = [Pokemon(self.game.loader.fetch_specific(pid), self.game.assets, size_mult=3.125) for pid in team_ids]
        levels.set_team(team, levels.follow_team(self.game, team_levels), exact=True)
        sprite = self.game.assets.get_trainer_image("leader_giovanni.png")
        intro = ["B4F: Giovanni: So, you've made it all the way down here.",
                 "I am Giovanni, the leader of Team Rocket. You'll regret getting in my way!"]

        class GiovanniBattle(TrainerBattleState):
            def exit_battle(self):
                story = self.game.story_manager
                if self.player_won:
                    story.story_flags["game_corner_rocket_progress"] = 5
                state = GameCornerState(self.game, self.game.states.get("city"))
                state.rocket_progress = story.story_flags.get("game_corner_rocket_progress", 0)
                state.phase = "VICTORY_SEQ"
                self.game.change_state(state)

        battle = GiovanniBattle(
            self.game, team, trainer_sprite=sprite, trainer_class="ROCKET_LEADER", trainer_name="GIOVANNI",
            battle_type="indoor", area_name="CELADON_CITY", is_boss_battle=True, rewards={"balls": 10},
            custom_dialogue={"player_won": ["Giovanni: ...What! This can't be!",
                                            "I'll leave the hideout. But Team Rocket isn't finished."],
                             "player_lost": ["Giovanni: Leave Team Rocket's business to the adults."]})
        self.game.change_state(TrainerIntroState(self.game, sprite, intro, battle))

    def give_porygon(self):
        story = self.game.story_manager
        story.story_flags["game_corner_cleared"] = True
        self.cleared = True
        porygon = Pokemon(self.game.loader.fetch_specific(137), self.game.assets, size_mult=2.5)
        msg = ["You drove Team Rocket out of their hideout!"]
        if story.inventory.get("SILPH_SCOPE", 0) <= 0:
            story.inventory["SILPH_SCOPE"] = 1
            msg.append("Giovanni dropped the SILPH SCOPE! Now you can see ghosts for what they are.")
        msg += ["In the chaos, you found a PORYGON!", "You rescued PORYGON!"]
        if len(self.game.story_manager.player_team) < 6:
            self.game.story_manager.player_team.append(porygon)
        else:
            self.game.story_manager.deposit_to_pc(porygon)
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
        elif self.phase == "MAIN_MENU":
            self.show_main_menu()  # back from Cash In / Slots: the menu buttons come back too

    def on_rocket_victory(self):
        if self.rocket_progress >= 5:
            self.give_porygon()
        elif self.rocket_progress == 4:  # the last grunt down: B4F and the boss
            self.dialogue_box.reset(["Defeated Rocket Grunt 4!", "A man in a dark suit is waiting at the bottom of the stairs..."])
            self.dialogue_box.callback = self.next_rocket_battle
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

        f = game.assets.fonts
        self.bar_rect = pygame.Rect(16, game.height - 86, game.width - 32, 78)
        by, bh = self.bar_rect.y + 10, self.bar_rect.h - 26
        self.btn_exit = CommandButton((16, 14, 140, 56), "EXIT", f["button"], self.go_back, bg_color=theme.BACK,
                                      autosize=False)
        self.btn_bet_one = CommandButton((self.bar_rect.right - 18 - 3 * 170 - 20, by, 170, bh), "BET 100", f["label"],
                                         self.bet_one, bg_color=theme.RUN, autosize=False)
        self.btn_bet_max = CommandButton((self.bar_rect.right - 18 - 2 * 170 - 10, by, 170, bh), "BET MAX", f["label"],
                                         self.bet_max, bg_color=theme.RUN, autosize=False)
        self.btn_spin = CommandButton((self.bar_rect.right - 18 - 170, by, 170, bh), "SPIN", f["button"],
                                      self.spin_reels, bg_color=theme.POKEMON, autosize=False)

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
        screen, f = self.game.screen, self.game.assets.fonts
        accent = theme.ACCENT["fun"]
        theme.menu_background(screen, accent, "SLOT MACHINE", f["button"], title_x=176)
        Utils.draw_text_outline(screen, f"${self.money:,}   Bet ${self.bet}", f["button"], WHITE, self.game.width - 24,
                                theme.HEADER_H // 2 - 4, align="right", outline_color=theme.shade(accent, 0.45),
                                thickness=3)
        machine = pygame.Rect(0, 0, 3 * 180 + 2 * 40 + 80, 260)
        machine.center = (self.game.width // 2, (theme.HEADER_H + self.bar_rect.top) // 2)
        theme.draw_panel(screen, machine)

        reel_width = 180
        reel_height = 180
        reel_spacing = 40
        start_x = self.game.width // 2 - (reel_width * 3 + reel_spacing * 2) // 2
        start_y = self.game.height // 2 - reel_height // 2

        for i, symbol_data in enumerate(self.reels):
            rect = pygame.Rect(start_x + i * (reel_width + reel_spacing), start_y, reel_width, reel_height)
            rect.centery = machine.centery
            theme.card(self.game.screen, rect, radius=14)

            if symbol_data:
                symbol_key = symbol_data[0]
                img = self.symbol_images.get(symbol_key)
                if img:
                    img_rect = img.get_rect(center=rect.center)
                    self.game.screen.blit(img, img_rect)

        theme.draw_textbox(screen, self.bar_rect)
        line = self.spin_result_message or "Pick a bet, then SPIN!"
        if self.payout > 0:
            line += f"   You won ${self.payout}!"
        bf = f["s_med"]
        theme.shadow_text(screen, line, bf, self.bar_rect.x + 32, self.bar_rect.centery - bf.get_height() // 2 - 2)
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
        return pygame.Rect(self.get_cx(i) - 90, self.game.height * 0.65, 180, 90)

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
        f = self.game.assets.fonts
        Utils.draw_text_outline(screen, f"SCORE: {self.score}", f["button"], theme.BAG, 24, 30, align="left",
                                outline_color=(20, 20, 30), thickness=3)
        Utils.draw_text_outline(screen, f"BALLS: {self.balls}", f["label"], WHITE, 24, 66, align="left",
                                outline_color=(20, 20, 30), thickness=2)
        for i, p in enumerate(self.p_data):
            if p and p.image:
                if not (self.pause_timer > 0 and i == self.caught_idx):
                    screen.blit(p.image, p.image.get_rect(center=(self.get_cx(i), self.sprite_y)))
        if not self.ball_active and self.pause_timer == 0:
            qf = f["big"]
            card = pygame.Rect(0, 0, max(360, qf.size(self.problem_str)[0] + 120), 100)
            card.center = (self.game.width // 2, 100)
            theme.draw_textbox(screen, card)
            theme.shadow_text(screen, self.problem_str, qf, card.centerx, card.centery, align="center")
            mouse = pygame.mouse.get_pos()
            for i in range(3):
                txt = str(self.options[i])
                rect = self.get_btn_rect(i)
                theme.card(screen, rect, hover=rect.collidepoint(mouse), accent=theme.RUN)
                theme.shadow_text(screen, txt, f["num"], rect.centerx, rect.centery, align="center")
        if self.ball_active:
            screen.blit(self.ball_img, (self.ball_pos[0]-42, self.ball_pos[1]-42))


class FlyState(GameState):
    """Fly: every town you've visited, three columns, grouped by region (the
    region you're in first). The list scrolls like the PC: the mouse wheel, plus the arrow
    buttons and Page Up / Page Down."""

    COLS = 3
    ROW_H = 74      # a row of towns (or a region heading)
    CELL_H = 60
    LEFT, RIGHT = 40, 90     # margins (the arrows sit in the right one)
    TOP = 104                # first row of the list (under the menu frame's header)
    BOTTOM_PAD = 20

    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        story = game.story_manager
        fonts = game.assets.fonts
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", fonts["button"], self.go_back,
                                      bg_color=theme.BACK, autosize=False)
        x = game.width - self.RIGHT + 15
        self.btn_up = Button((x, self.TOP, 60, 60), "UP", fonts["tiny"], lambda: self.scroll_by(-1),
                             autosize=False)
        self.btn_down = Button((x, game.height - self.BOTTOM_PAD - 60, 60, 60), "DN", fonts["tiny"],
                               lambda: self.scroll_by(1), autosize=False)

        cities = []
        prog = game.loader.area_data.get("STORY_PROGRESSION", {})
        for key, data in prog.items():
            if data.get("area_type") == "town" and story.story_flags.get(f"visited_{key}"):
                cities.append((key, data.get("route_name", key)))
        if story.inventory.get("MT_SILVER_MAP", 0) > 0:
            silver_key = "SILVER_LEAGUE_PLATEAU"
            silver_name = prog.get(silver_key, {}).get("route_name", "Silver League")
            if not any(c[0] == silver_key for c in cities):
                cities.append((silver_key, silver_name))
        self.cities = cities

        # Rows: a heading for each region, then its towns three to a row.
        here = story.get_current_region()
        order = {r: i for i, (r, _) in enumerate(story.get_region_starts())}
        regions = sorted({story.area_region(k) for k, _ in cities},
                         key=lambda r: (r != here, order.get(r, 99), r))
        self.rows = []
        for region in regions:
            towns = [c for c in cities if story.area_region(c[0]) == region]
            self.rows.append(("heading", region.title()))
            for i in range(0, len(towns), self.COLS):
                self.rows.append(("towns", towns[i:i + self.COLS]))
        self.visible_rows = max(1, (game.height - self.TOP - self.BOTTOM_PAD) // self.ROW_H)
        self.first_row = 0
        self.cell_buttons = []

    @property
    def max_first_row(self):
        return max(0, len(self.rows) - self.visible_rows)

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def fly_to(self, key):
        from src.states.overworld import AreaTransitionState
        self.game.change_state(AreaTransitionState(self.game, key))

    def start(self):
        for btn in (self.btn_back, self.btn_up, self.btn_down):
            self.game.ui_manager.add_element(btn)
        self._layout()

    def scroll_by(self, rows):
        first = min(self.max_first_row, max(0, self.first_row + rows))
        if first != self.first_row:
            self.first_row = first
            self._layout()

    def _layout(self):
        """Buttons for the towns on the rows in view (rebuilt when the list scrolls)."""
        ui = self.game.ui_manager
        for btn in self.cell_buttons:
            if btn in ui.elements:
                ui.elements.remove(btn)
        self.cell_buttons = []
        width = self.game.width - self.LEFT - self.RIGHT
        cell_w = (width - (self.COLS - 1) * 16) // self.COLS
        for n, (kind, data) in enumerate(self.rows[self.first_row:self.first_row + self.visible_rows]):
            if kind != "towns":
                continue
            y = self.TOP + n * self.ROW_H
            for i, (key, name) in enumerate(data):
                rect = (self.LEFT + i * (cell_w + 16), y, cell_w, self.CELL_H)
                btn = Button(rect, name.upper(), self.game.assets.fonts["small"],
                             lambda k=key: self.fly_to(k), autosize=False)
                self.cell_buttons.append(btn)
                ui.add_element(btn)
        self.btn_up.set_visibility(self.first_row > 0)
        self.btn_down.set_visibility(self.first_row < self.max_first_row)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):  # the wheel, as in the PC
                self.scroll_by(-1 if event.button == 4 else 1)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEDOWN:
                self.scroll_by(self.visible_rows - 1)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEUP:
                self.scroll_by(-(self.visible_rows - 1))

    def update(self):
        pass

    def draw(self):
        screen = self.game.screen
        fonts = self.game.assets.fonts
        title = "FLY"
        theme.menu_background(screen, theme.ACCENT["map"], title, fonts["button"], title_x=176)
        if not self.cities:
            theme.shadow_text(screen, "You haven't visited any towns yet.", fonts["s_med"], self.game.width // 2,
                              self.game.height // 2, color=WHITE, shadow=theme.MENU_BG, align="center")
        for n, (kind, data) in enumerate(self.rows[self.first_row:self.first_row + self.visible_rows]):
            if kind == "heading":
                y = self.TOP + n * self.ROW_H + self.CELL_H // 2
                head = Utils.draw_text_outline(screen, data.upper(), fonts["button"], WHITE, self.LEFT, y,
                                               align="left", outline_color=theme.PANEL_BORDER, thickness=3)
                pygame.draw.line(screen, theme.PANEL_EDGE, (self.LEFT + 240, y), (self.game.width - self.RIGHT, y), 3)
        if self.max_first_row:  # where you are in the list
            track = pygame.Rect(self.game.width - self.RIGHT + 40, self.TOP + 75, 10,
                                self.game.height - self.TOP - self.BOTTOM_PAD - 150)
            pygame.draw.rect(screen, (60, 60, 90), track, border_radius=5)
            share = self.visible_rows / len(self.rows)
            h = max(30, int(track.height * share))
            y = track.y + int((track.height - h) * self.first_row / self.max_first_row)
            pygame.draw.rect(screen, GOLD, (track.x, y, track.width, h), border_radius=5)
        self.game.ui_manager.draw(screen)


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
            if self.timer <= 0:  # once, when the reveal ends (these ran every frame before)
                self.phase = "END"
                self.timer = 60
                self._finalize_revival()
        elif self.phase == "END" and self.timer <= 0:
            pygame.event.clear()
            self.game.change_state(self.previous_state)

    def _finalize_revival(self):
        story = self.game.story_manager
        for item in self.consume:
            story.inventory[item] = story.inventory.get(item, 0) - 1
            if story.inventory[item] <= 0:
                story.inventory.pop(item, None)

        revival_flag = f"revived_fossil_{story.current_area_key}"
        story.story_flags[revival_flag] = True

        msg = f"Success! The fossil was revived into {self.evolved_pokemon_obj.display_name}!"
        if len(story.player_team) < 6:
            story.player_team.append(self.evolved_pokemon_obj)
        else:
            pc = story.pc_pokemon
            slot = next((i for i, p in enumerate(pc) if p is None), None)
            if slot is None:
                pc.append(self.evolved_pokemon_obj)
            else:
                pc[slot] = self.evolved_pokemon_obj  # (append would land past the 300 saved slots)
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
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", game.assets.fonts["button"], self.go_back,
                                      bg_color=theme.BACK, autosize=False)

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
        """The menu frame: one card per Unown form (28), caught ones with their sprite."""
        screen = self.game.screen
        f = self.game.assets.fonts
        accent = theme.ACCENT["tool"]
        theme.menu_background(screen, accent, "UNOWN REPORT", f["button"], title_x=176)
        found = sum(1 for x in self.forms if x in (self.caught_forms or ()))
        Utils.draw_text_outline(screen, f"{found} / {len(self.forms)} forms", f["button"], WHITE,
                                self.game.width - 24, theme.HEADER_H // 2 - 4, align="right",
                                outline_color=theme.shade(accent, 0.45), thickness=3)
        cols, gap = 7, 12
        top = theme.HEADER_H + 16
        cw = (self.game.width - 48 - gap * (cols - 1)) // cols
        ch = (self.game.height - 16 - top - gap * 3) // 4
        for i, form in enumerate(self.forms):
            col, row = i % cols, i // cols
            rect = pygame.Rect(24 + col * (cw + gap), top + row * (ch + gap), cw, ch)
            caught = form in (self.caught_forms or ())
            theme.card(screen, rect, fill=theme.TEXTBOX if caught else (214, 218, 228))
            lbl = "A" if form == "normal" else ("?" if form == "question" else "!" if form == "exclamation"
                                                 else form.upper())
            if caught:
                img = self.game.assets.get_pokemon_image(201, form, False)
                if img:
                    spr = fit_sprite(img, cw - 30, ch - 50)
                    screen.blit(spr, spr.get_rect(center=(rect.centerx, rect.centery - 10)))
                theme.shadow_text(screen, lbl, f["s_med"], rect.centerx, rect.bottom - 22, align="center")
            else:
                theme.shadow_text(screen, "?", f["big"], rect.centerx, rect.centery, color=(150, 156, 172),
                                  align="center")
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
        
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", game.assets.fonts["button"], self.go_back,
                                      bg_color=theme.BACK, autosize=False)

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
        """The menu frame: the area's wild Pokemon as white rows (sprite, name, caught ball, how often
        it appears), in two columns. Rare ones (< 5%) stay hidden without the Devon Scope."""
        screen = self.game.screen
        f = self.game.assets.fonts
        accent = theme.ACCENT["tool"]
        route_name = self.area_data.get("route_name", "Unknown Area")
        theme.menu_background(screen, accent, f"POKENAV: {route_name.upper()}", f["button"], title_x=176)
        if not self.pool:
            theme.shadow_text(screen, "No wild Pokemon data for this area.", f["s_med"], self.game.width // 2,
                              self.game.height // 2, color=WHITE, shadow=theme.MENU_BG, align="center")
            self.game.ui_manager.draw(screen)
            return
        has_devon_scope = self.game.story_manager.inventory.get("DEVON_SCOPE", 0) > 0
        caught_data = self.game.data.data.get("pokedex", {})
        caught_ids = {int(v.get("id", -1)) for v in caught_data.values() if isinstance(v, dict)}
        rows = sorted(self.pool.items(), key=lambda x: x[1], reverse=True)
        top, gap, rh = theme.HEADER_H + 16, 10, 64
        per_col = max(1, (self.game.height - 16 - top + gap) // (rh + gap))
        cw = (self.game.width - 48 - 16) // 2
        for i, (p_id_str, chance) in enumerate(rows[:per_col * 2]):
            p_id = int(p_id_str)
            col, row = i // per_col, i % per_col
            rect = pygame.Rect(24 + col * (cw + 16), top + row * (rh + gap), cw, rh)
            rare = chance < 5
            hidden = rare and not has_devon_scope
            theme.card(screen, rect, selected=rare and has_devon_scope, accent=theme.BAG, radius=10)
            if not hidden:
                img = self.game.assets.get_pokemon_image(p_id, "normal", False)
                if img:
                    spr = fit_sprite(img, 52, 52)
                    screen.blit(spr, spr.get_rect(center=(rect.x + 36, rect.centery)))
            name = "???" if hidden else self.game.assets.pokemon_names.get(str(p_id), "???").title()
            theme.shadow_text(screen, name, f["label"], rect.x + 74, rect.y + 10)
            if p_id in caught_ids and self.game.assets.ui_ball:
                screen.blit(pygame.transform.scale(self.game.assets.ui_ball, (20, 20)), (rect.right - 34, rect.y + 10))
            bar = pygame.Rect(rect.x + 74, rect.bottom - 20, rect.w - 74 - 90, 10)
            pygame.draw.rect(screen, (210, 214, 224), bar, border_radius=5)
            pygame.draw.rect(screen, theme.BAG if rare else theme.POKEMON,
                             (bar.x, bar.y, max(4, int(bar.w * min(1.0, chance / 50))), bar.h), border_radius=5)
            theme.shadow_text(screen, f"{chance}%", f["label"], rect.right - 16, rect.bottom - 30, align="right")
        self.game.ui_manager.draw(screen)
