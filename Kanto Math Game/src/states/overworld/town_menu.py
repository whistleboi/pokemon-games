"""The town screen's EXPLORE / TRAVEL menus: building the buttons, their conditions, and what they do."""

import pygame
import random
import re
from src.ui.widgets import Button
from src.ui import theme
from src.world import guide
from src.world import story_events
from src.config import BLUE, GOLD
from src.states.overworld.common import _fill_names, travel_label


class TownMenu:
    """Part of CityState (town.py): its explore / travel menus."""

    def _create_hover_menu(self, options, base_button_rect):
        if self.hover_menu_active:
            self.clear_hover_menu()

        self.hover_menu_active = True
        self.hover_buttons.clear()
        self.hover_bg_rect = None

        valid_options = []
        for opt_data in options:
            flag_condition = opt_data.get("flag_condition")
            if flag_condition:
                parts = flag_condition.split()
                should_skip = False
                if len(parts) == 2 and parts[0] == 'not':
                    if self.game.story_manager.story_flags.get(parts[1], False):
                        should_skip = True
                elif len(parts) == 1:
                    if not self.game.story_manager.story_flags.get(parts[0], False):
                        should_skip = True
                if should_skip:
                    continue

            item_condition = opt_data.get("item_condition")
            if item_condition:
                if self.game.story_manager.inventory.get(item_condition, 0) <= 0:
                    continue

            menu_condition = opt_data.get("condition")
            if menu_condition and not self._check_menu_condition(menu_condition):
                continue

            valid_options.append(opt_data)

        if not valid_options:
            self.hover_menu_active = False
            return

        font = self.game.assets.fonts["tiny"]
        max_w = 220
        words = [travel_label(self.game, o) if o.get("action") == "TRAVEL" and o.get("target_area")
                 else _fill_names(self.game, o['text']) for o in valid_options]
        for w_text in words:
            w = font.size(w_text)[0] + 40
            if w > max_w:
                max_w = w

        btn_h = 60
        btn_w = max_w
        gap_y = 10
        gap_x = 10
        padding = 20

        panel_rect = self.action_menu.right_rect
        anchor_right = panel_rect.right - 18
        anchor_bottom = panel_rect.top - 10

        count = len(valid_options)
        # One column while it fits above the panel; long lists (the Orange Islands ships) wrap.
        fit = max(1, (anchor_bottom - 20 - padding * 2 + gap_y) // (btn_h + gap_y))
        cols = -(-count // fit)
        rows = -(-count // cols)

        bg_w = cols * btn_w + (cols - 1) * gap_x + padding * 2
        bg_h = rows * btn_h + (rows - 1) * gap_y + padding * 2

        self.hover_bg_rect = pygame.Rect(0, 0, bg_w, bg_h)
        self.hover_bg_rect.bottomright = (anchor_right, anchor_bottom)

        start_y = self.hover_bg_rect.top + padding

        for i, opt_data in enumerate(valid_options):
            col, row = divmod(i, rows)

            btn_x = self.hover_bg_rect.left + padding + col * (btn_w + gap_x)
            btn_y = start_y + row * (btn_h + gap_y)

            rect = (btn_x, btn_y, btn_w, btn_h)

            callback = self._get_callback_for_option(opt_data)
            if callback:
                toward = (opt_data.get("target_area") and opt_data.get("target_area") == guide.cached(self.game, "hop")) \
                    or guide.advances_goal(self.game, self.area_key, opt_data)  # (the step the Journal needs)
                way = opt_data.get("action") == "TRAVEL" and opt_data.get("target_area")
                btn = Button(rect, ("> " if toward else "") + words[i],
                             self.game.assets.fonts["tiny"], callback, autosize=False,
                             bg_color=GOLD if toward else theme.FIGHT if way else BLUE)  # (gold: the way to the tracked mission)
                self.hover_buttons.append(btn)
                self.game.ui_manager.add_element(btn)

    def _check_menu_condition(self, condition):
        """Condition checker for Town menus, synced with PlayState logic."""
        if not condition:
            return True

        story = self.game.story_manager

        if isinstance(condition, (list, tuple)):
            return all(self._check_menu_condition(c) for c in condition)
        if isinstance(condition, dict) and "any" in condition:  # {"any": [...]}: one is enough
            return any(self._check_menu_condition(c) for c in condition["any"])
        if condition.startswith("not:"):
            return not self._check_menu_condition(condition[4:])

        if condition == "has_8_badges":
            return sum(len(b) for b in story.badges.values()) >= 8

        if condition.startswith("has_item:"):
            return story.inventory.get(condition[9:], 0) > 0
        special = self.game.story_manager.special_condition(condition)
        if special is not None:  # party_has:493, all_unown_registered
            return special
        if isinstance(condition, str) and condition.startswith("caught_range:"):
            lo, hi = (int(x) for x in condition.split(":", 1)[1].split("-"))
            return story.caught_in_range(lo, hi) >= hi - lo + 1  # e.g. all of #1-251
        if condition == "snorlax_defeated":  # canon: Snorlax (Poke Flute) blocks Cycling Road
            return story.snorlax_awake()

        if condition == "has_8_kanto_badges":
            kanto_badges = {"BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH", "VOLCANO", "EARTH"}
            player_badges = set(story.badges.get("KANTO", []))
            return kanto_badges.issubset(player_badges)

        if condition == "has_8_johto_badges":
            johto_badges = {"ZEPHYR", "HIVE", "PLAIN", "FOG", "STORMBADGE",
                            "MINERAL", "GLACIER", "RISING"}
            player_badges = set(story.badges.get("JOHTO", []))
            return johto_badges.issubset(player_badges)

        region_all = re.match(r"has_(?:8|all)_([a-z]+)_(?:badges|z)$", condition)
        if region_all:
            region = region_all.group(1).upper()
            needed = len(story.get_region_gym_badges(region)) or 8
            return len(story.badges.get(region, [])) >= needed

        if condition.startswith("has_") and condition.endswith("_badge"):
            from src.world.hms import _norm
            want = _norm(condition[4:-6])  # case and "_BADGE" don't matter ("KNuckle", "COAL_BADGE")
            # This region's badges: Galar's and Paldea's Grass Badges are different badges.
            return any(_norm(b) == want for b in story.badges.get(story.get_current_region(), []))

        if condition == "has_national_dex":
            return story.story_flags.get("unlocked_national_dex", False)

        if isinstance(condition, str) and condition.startswith("has_")                 and story.inventory.get(condition[4:].upper(), 0) > 0:
            return True  # "has_silver_wing": holding the SILVER_WING
        if isinstance(condition, str):
            return story.story_flags.get(condition, False)

        return True

    def _get_callback_for_option(self, opt_data):
        from src.states.overworld.area_transition import travel_heal
        from src.states.overworld.pokecenter import CenterInsideState, PokeCenterState
        if opt_data.get("move_region"):  # the S.S. Anne to the Orange Islands: a move to a new region
            r = opt_data["move_region"]
            return lambda: self.game.change_state(self.game.story_manager.move_to_region(r))
        if opt_data.get("npc"):  # a way out that someone stops you at (Oak at Route 1, FRLG)
            return self._get_callback_for_option({"action": "NPC", "target": opt_data["npc"]})
        action = opt_data.get("action")
        if action == "CENTER":  # from Unova on: into the Pokemon Center, its shop inside
            return lambda o=opt_data: self.game.change_state(CenterInsideState(self.game, self, o.get("shops", [])))
        if action == "LEAVE_CENTER":
            return self.leave_center
        if action == "HEAL":
            return lambda: self.game.change_state(PokeCenterState
                                                  (self.game, self))
        if action == "SHOP":
            if opt_data.get("stock"):  # a shop with its own shelf (Lumiose's Stone Emporium)
                from src.states.systems import PokeMartState
                return lambda s=list(opt_data["stock"]): self.game.change_state(PokeMartState(self.game, self, stock=s))
            return self._open_shop
        if action == "DAYCARE":
            from src.states.daycare import DaycareState
            return lambda: self.game.change_state(DaycareState(self.game, self))
        if action == "GAMECORNER":
            from src.states.overworld import dungeon
            if dungeon.enabled(self.game, "CELADON_GAME_CORNER"):  # walk in (Jordan, 11-05)
                from src.states.overworld.area_transition import AreaTransitionState
                return lambda: self.game.change_state(AreaTransitionState(self.game, "CELADON_GAME_CORNER"))
            from src.states.systems import GameCornerState
            return lambda: self.game.change_state(GameCornerState
                                                  (self.game, self))
        if action == "BIKESHOP":
            from src.states.systems import BikeShopState
            return lambda: self.game.change_state(BikeShopState
                                                  (self.game, self))
        if action == "GYM":
            return self.start_gym_battle
        if action == "NPC":
            target = opt_data.get("target")
            if target == "giovanni":
                return self.visit_giovanni
            if target in ["mom", "player_mom"]:
                return self.visit_mom
            if target == "silver_mom":
                return self.visit_silver_mom
            if target in ["rival_mom", "blue_mom", "rival_mom_johto"]:
                return self.visit_rival_mom
            if target == "professor_oak":
                return self.visit_prof_oak
            if target == "oldman":
                return self.wake_sleeping_man
            if target == "museum":
                return self.visit_museum
            if target == "fishing_guru":
                return self.visit_fishing_guru
            if target == "alph_scientist":
                return self.visit_alph_scientist
            if target == "bill":
                return self.visit_bill
            if target == "bill_johto":
                return self.visit_bill_johto
            if target == "flower_shop":
                return self.visit_flower_shop
            if target in ("stoneman", "fossil_lab", "nacrene_museum", "ambrette_fossil_lab"):
                return self.visit_stoneman
            if target == "mr_fuji":
                return self.visit_mr_fuji
            if target == "silph_employee":
                return self.visit_silph_employee
            if target == "silph_president":
                return self.visit_silph_president
            if target == "professor_elm":
                return self.visit_prof_elm
            if target == "dojo":
                return self.visit_dojo
            if target == "kurt":
                return self.visit_kurt
            if target == "lance_mahogany":
                return self.visit_lance_johto
            if target == "radio_tower_grunt":
                return self.visit_radio_tower_grunt
            if target == "mr_pokemon":
                return self.visit_mr_pokemon
            if target == "kimono_girl":
                return self.visit_kimono_girls
            if target == "lighthouse_jasmine":
                return self.visit_lighthouse_jasmine
            if target == "ampharos":
                return self.visit_ampharos
            if target == "pharmacist":
                return self.visit_pharmacist
            if target == "euskine":
                return self.visit_euskine
            if target == "dragon_elder":
                return self.visit_dragon_elder
            if target == "contest_hall":
                return self.visit_contest_hall
            if target == "contest_museum":
                return self.visit_contest_museum
            if target == "poffin_house":
                return self.visit_poffin_house
            if target == "berry_shop":
                return self.visit_berry_shop
            if target and "_mom_" in f"_{target}_":
                return self.visit_mom
            if story_events.get(target):
                return lambda t=target: self.story_event(t)
            key = self._npc_text_key(opt_data.get("dialogue") or target)
            if key:
                return lambda k=key, o=opt_data: self.show_npc_text(k, o)

        if action == "RANDOM_NPC":
            targets = opt_data.get("targets", [])
            if any("_mom_" in f"_{t}_" for t in targets):
                return self.visit_mom
            keys = [k for k in (self._npc_text_key(t) for t in targets) if k]
            if keys:
                return lambda: self.show_npc_text(random.choice(keys), opt_data)

        if action == "EVENT":
            return lambda e=opt_data.get("event") or {}: self.story_event(e)
        if action == "DONUT":  # Hyperspace Lumiose's Donut Shop (Jordan, 11-06)
            from src.states.donut import DonutShopState
            return lambda: (self.clear_hover_menu(), self.game.change_state(DonutShopState(self.game, self)))
        if action == "AMIE":
            from src.states.amie import AmieState
            return lambda: (self.clear_hover_menu(), self.game.change_state(AmieState(self.game, self)))
        if action == "ROCKET_GAUNTLET":
            return self.start_rocket_gauntlet
        if action == "RUINS":
            return self.action_explore_ruins
        if action == "TILE_PUZZLE":
            return lambda p=opt_data.get("panel"): self.solve_alph_panel(p)
        if action == "TRAVEL":
            return lambda: self.go_to_area(opt_data.get("target_area"), opt_data.get("message"),
                                           heal=travel_heal(opt_data))
        return None

    def open_explore_menu(self):
        from src.states.overworld.pokecenter import center_entrance, combined_center
        options = self.area_data.get("explore_options", [])
        if combined_center(self.game):
            options = center_entrance(options)
        self._create_hover_menu(options, self.action_menu.buttons[0].rect)

    def open_travel_menu(self):
        options = self.area_data.get("travel_options", [])
        for opt in options:
            opt['action'] = 'TRAVEL'
        if len(self.action_menu.buttons) > 3:
            self._create_hover_menu(options, self.action_menu.buttons[3].rect)

    def go_to_area(self, area_key, message=None, heal=None):
        """Travel; a ship or train ride shows its own message on the way. heal: see travel_heal."""
        from src.states.overworld.area_transition import AreaTransitionState
        if area_key:
            self.game.change_state(AreaTransitionState(self.game, area_key, initial_message=message,
                                                       heal=heal))

    def clear_hover_menu(self):
        for btn in self.hover_buttons:
            if btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)
        self.hover_menu_active = None
        self.hover_buttons.clear()
        self.hover_bg_rect = None
