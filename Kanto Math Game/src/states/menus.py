# [REF-0001: System Imports]
import pygame
import random
import os
import math
import threading
import json
from src.states.base import GameState
from src.ui.widgets import Button
from src.ui.dialogue import ClassicDialogueBox
from src.utils import Utils
from src.config import (WHITE, BLACK, GOLD, GB_PANEL_DARK, GRAY, LIGHT_GRAY,
                        GREEN, RED, GB_PANEL, GB_BORDER, GB_TEXT)
from src.pokemon.data import Pokemon


# [REF-0019: Main Menu System]
class MainMenuState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.btn_new = Button(
            (game.width // 2 - 150, game.height // 2 - 60, 300, 80),
            "NEW GAME",
            game.assets.fonts["med"],
            self.new_game,
        )
        self.btn_load = Button(
            (game.width // 2 - 150, game.height // 2 + 40, 300, 80),
            "LOAD GAME",
            game.assets.fonts["med"],
            self.load_game,
        )

        # Check for ANY save file (main or slots)
        has_saves = False
        if os.path.exists(game.data.save_file) and game.data.data.get("story"):
            has_saves = True
        else:
            for i in range(5):
                fname = os.path.join(
                    game.assets.base_dir, f"game_data_{i}.json")
                if os.path.exists(fname):
                    has_saves = True
                    break

        if not has_saves:
            self.btn_load.bg_color = GRAY
            self.btn_load.text_color = LIGHT_GRAY
            self.btn_load.callback = None

    def new_game(self):
        self.game.start_new_game()

    def load_game(self):
        self.game.change_state(LoadState(self.game, self))

    def handle_events(self, events):
        for event in events:
            self.btn_new.handle_event(event)
            self.btn_load.handle_event(event)

    def update(self):
        pass

    def draw(self):
        self.game.screen.fill(BLACK)
        Utils.draw_text_outline(
            self.game.screen,
            "KANTO MATH",
            self.game.assets.fonts["big"],
            GOLD,
            self.game.width // 2,
            self.game.height * 0.2,
        )
        self.btn_new.draw(self.game.screen)
        self.btn_load.draw(self.game.screen)


# [REF-0056: Character Selection State]
class CharacterSelectionState(GameState):
    def __init__(self, game):
        super().__init__(game)
        config = game.loader.area_data.get("GAME_CONFIG", {})
        self.char_list = config.get("PLAYABLE_CHARACTERS", ["red", "blue"])
        self.starter_ids = config.get("STARTER_IDS", [1, 4, 7])

        self.selected_idx = random.randint(0, len(self.char_list) - 1)
        self.input_name = ""
        self.sprites = []

        for name in self.char_list:
            front = game.assets.get_player_image(name, back=False)
            if not front:
                front = game.assets.get_player_image(name, back=True)

            if not front:
                front = pygame.Surface((200, 200))
                front.fill(GRAY)

            h = int(game.height * 0.5)
            w = int(front.get_width() * (h / front.get_height()))
            self.sprites.append(pygame.transform.scale(front, (w, h)))

        cx, cy = game.width // 2, game.height // 2
        self.rect_left = pygame.Rect(cx - 280, cy - 60, 80, 120)
        self.rect_right = pygame.Rect(cx + 220, cy - 60, 80, 120)
        self.rect_select = pygame.Rect(cx - 200, game.height - 130, 400, 60)

        threading.Thread(target=self.preload_starters, daemon=True).start()

    def preload_starters(self):
        self.game.preloaded_starter_data = [
            self.game.loader.fetch_specific(i) for i in self.starter_ids
        ]
        print("✓ Background loading of starters complete.")

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.rect_left.collidepoint(event.pos):
                    self.selected_idx = (
                        self.selected_idx - 1) % len(self.char_list)
                elif self.rect_right.collidepoint(event.pos):
                    self.selected_idx = (
                        self.selected_idx + 1) % len(self.char_list)
                elif self.rect_select.collidepoint(event.pos):
                    self.confirm_selection()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.input_name = self.input_name[:-1]
                elif event.key == pygame.K_RETURN:
                    self.confirm_selection()
                elif len(self.input_name) < 12 and event.unicode.isprintable():
                    self.input_name += event.unicode.upper()

    def confirm_selection(self):
        name = self.input_name.strip() or "TRAINER"
        char_key = self.char_list[self.selected_idx]

        self.game.player_name = name
        self.game.player_character = char_key

        self.game.change_state(RegionSelectionState(self.game))

    def update(self):
        pass

    def draw(self):
        screen = self.game.screen
        screen.fill(BLACK)
        cx, cy = self.game.width // 2, self.game.height // 2

        Utils.draw_text_outline(
            screen, "CHOOSE YOUR TRAINER",
            self.game.assets.fonts["big"], WHITE, cx, 80
        )

        sprite = self.sprites[self.selected_idx]
        screen.blit(sprite, sprite.get_rect(center=(cx, cy)))

        pygame.draw.rect(
            screen, GB_PANEL_DARK, self.rect_left, border_radius=12)
        pygame.draw.rect(
            screen, GB_PANEL_DARK, self.rect_right, border_radius=12)
        Utils.draw_text_outline(
            screen,
            "<",
            self.game.assets.fonts["big"],
            WHITE,
            self.rect_left.centerx,
            self.rect_left.centery,
        )
        Utils.draw_text_outline(
            screen,
            ">",
            self.game.assets.fonts["big"],
            WHITE,
            self.rect_right.centerx,
            self.rect_right.centery,
        )

        Utils.draw_text_outline(
            screen,
            "ENTER NAME:",
            self.game.assets.fonts["small"],
            WHITE,
            cx,
            self.game.height - 210,
        )
        name_rect = pygame.Rect(cx - 150, self.game.height - 180, 300, 40)
        pygame.draw.rect(screen, WHITE, name_rect, 2)

        display_name = self.input_name + (
            "_" if (pygame.time.get_ticks() // 500) % 2 else ""
        )
        Utils.draw_text_outline(
            screen,
            display_name,
            self.game.assets.fonts["s_med"],
            WHITE,
            cx,
            self.game.height - 160,
        )

        pygame.draw.rect(
            screen, GB_PANEL_DARK, self.rect_select,
            border_radius=10)
        Utils.draw_text_outline(
            screen,
            "SELECT",
            self.game.assets.fonts["s_med"],
            WHITE,
            self.rect_select.centerx,
            self.rect_select.centery,
            outline_color=BLACK,
        )


class RegionSelectionState(GameState):
    """Allows the player to choose their starting region (Kanto or Johto)."""
    def __init__(self, game):
        super().__init__(game)
        self.regions = ["KANTO", "JOHTO"]
        self.selected_idx = 0

        cx, cy = game.width // 2, game.height // 2
        # Using GB UI style boxes for region cards
        self.rect_kanto = pygame.Rect(cx - 320, cy - 80, 300, 160)
        self.rect_johto = pygame.Rect(cx + 20, cy - 80, 300, 160)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.rect_kanto.collidepoint(event.pos):
                    self.selected_idx = 0
                    self.confirm_selection()
                elif self.rect_johto.collidepoint(event.pos):
                    self.selected_idx = 1
                    self.confirm_selection()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.selected_idx = 0
                elif event.key == pygame.K_RIGHT:
                    self.selected_idx = 1
                elif event.key == pygame.K_RETURN:
                    self.confirm_selection()

    def confirm_selection(self):
        region = self.regions[self.selected_idx]
        self.game.story_manager.starting_region = region

        # ARCHITECT SYNC: Unlock starting regional badge page
        if region == "JOHTO":
            self.game.story_manager.story_flags["unlocked_johto_badges"] = True
        else:
            self.game.story_manager.story_flags["unlocked_kanto_badges"] = True

        # Set the starting location based on chosen region
        if region == "JOHTO":
            self.game.story_manager.current_area_key = "NEW_BARK_TOWN"
        else:
            self.game.story_manager.current_area_key = "PALLET_TOWN"

        self.game.change_state(RivalSelectionState(self.game))

    def update(self):
        pass

    def draw(self):
        screen = self.game.screen
        screen.fill(BLACK)
        cx = self.game.width // 2

        Utils.draw_text_outline(screen, "WHERE WILL YOUR JOURNEY BEGIN?",
                                self.game.assets.fonts["med"], WHITE, cx, 100)

        # Draw Region Selection Cards
        for i, rect in enumerate([self.rect_kanto, self.rect_johto]):
            is_selected = (self.selected_idx == i)
            bg_color = GB_PANEL if is_selected else GB_PANEL_DARK
            border_color = GOLD if is_selected else WHITE
            border_thickness = 6 if is_selected else 2

            # Draw the card
            pygame.draw.rect(screen, bg_color, rect, border_radius=15)
            pygame.draw.rect(
                screen, border_color, rect, border_thickness,
                border_radius=15
            )

            region_name = self.regions[i]
            text_color = WHITE if is_selected else GRAY
            Utils.draw_text_outline(
                screen, region_name,
                self.game.assets.fonts["s_med"],
                text_color, rect.centerx, rect.centery
            )

            # Display region context subtext
            sub = "GEN 1 / RED / BLUE" if i == 0 else "GEN 2 / GOLD / SILVER"
            Utils.draw_text_outline(
                screen, sub, self.game.assets.fonts["tiny"],
                GRAY, rect.centerx, rect.centery + 40
            )

        # Footer hint
        msg = "SELECT A REGION TO CONTINUE"
        Utils.draw_text_outline(
            screen, msg, self.game.assets.fonts["small"],
            GOLD, cx, self.game.height - 80
        )


# [REF-0057: Rival Selection State]
class RivalSelectionState(GameState):
    def __init__(self, game):
        super().__init__(game)
        config = game.loader.area_data.get("GAME_CONFIG", {})
        full_list = config.get("PLAYABLE_CHARACTERS", ["red", "blue"])
        p_char = getattr(game, "player_character", "red")
        self.char_list = [c for c in full_list if c != p_char]

        self.selected_idx = 0
        self.input_name = ""
        self.sprites = []

        for name in self.char_list:
            front = game.assets.get_player_image(name, back=False)
            if not front:
                front = game.assets.get_player_image(name, back=True)
            if not front:
                front = pygame.Surface((200, 200))
                front.fill(GRAY)

            h = int(game.height * 0.5)
            w = int(front.get_width() * (h / front.get_height()))
            self.sprites.append(pygame.transform.scale(front, (w, h)))

        cx, cy = game.width // 2, game.height // 2
        self.rect_left = pygame.Rect(cx - 280, cy - 60, 80, 120)
        self.rect_right = pygame.Rect(cx + 220, cy - 60, 80, 120)
        self.rect_select = pygame.Rect(cx - 200, game.height - 130, 400, 60)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.rect_left.collidepoint(event.pos):
                    self.selected_idx = (
                        self.selected_idx - 1) % len(self.char_list)
                elif self.rect_right.collidepoint(event.pos):
                    self.selected_idx = (
                        self.selected_idx + 1) % len(self.char_list)
                elif self.rect_select.collidepoint(event.pos):
                    self.confirm_selection()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.input_name = self.input_name[:-1]
                elif event.key == pygame.K_RETURN:
                    self.confirm_selection()
                elif event.key == pygame.K_LEFT:
                    self.selected_idx = (
                        self.selected_idx - 1) % len(self.char_list)
                elif event.key == pygame.K_RIGHT:
                    self.selected_idx = (
                        self.selected_idx + 1) % len(self.char_list)
                elif len(self.input_name) < 12 and event.unicode.isprintable():
                    self.input_name += event.unicode.upper()

    def confirm_selection(self):
        char_key = self.char_list[self.selected_idx]
        self.game.rival_character = char_key
        rival_name = self.input_name.strip()
        self.game.rival_name = rival_name if rival_name else char_key.upper()

        region = self.game.story_manager.starting_region
        starter_ids = [152, 155, 158] if region == "JOHTO" else [1, 4, 7]

        self.game.change_state(
            StarterSelectionState(
                self.game,
                starter_ids=starter_ids,
                region=region
            )
        )

    def update(self):
        pass

    def draw(self):
        screen = self.game.screen
        screen.fill(BLACK)
        cx, cy = self.game.width // 2, self.game.height // 2

        Utils.draw_text_outline(
            screen,
            "CHOOSE YOUR RIVAL",
            self.game.assets.fonts["big"],
            WHITE,
            cx,
            80,
        )

        if self.sprites:
            sprite = self.sprites[self.selected_idx]
            screen.blit(sprite, sprite.get_rect(center=(cx, cy)))

        pygame.draw.rect(
            screen, GB_PANEL_DARK, self.rect_left, border_radius=12
        )
        pygame.draw.rect(
            screen, GB_PANEL_DARK, self.rect_right, border_radius=12
        )
        Utils.draw_text_outline(
            screen,
            "<",
            self.game.assets.fonts["big"],
            WHITE,
            self.rect_left.centerx,
            self.rect_left.centery,
        )
        Utils.draw_text_outline(
            screen,
            ">",
            self.game.assets.fonts["big"],
            WHITE,
            self.rect_right.centerx,
            self.rect_right.centery,
        )

        Utils.draw_text_outline(
            screen,
            "ENTER NAME:",
            self.game.assets.fonts["small"],
            WHITE,
            cx,
            self.game.height - 210,
        )
        name_rect = pygame.Rect(cx - 150, self.game.height - 180, 300, 40)
        pygame.draw.rect(screen, WHITE, name_rect, 2)

        display_name = self.input_name + (
            "_" if (pygame.time.get_ticks() // 500) % 2 else ""
        )
        if not self.input_name:
            display_name = self.char_list[self.selected_idx].upper()

        Utils.draw_text_outline(
            screen,
            display_name,
            self.game.assets.fonts["s_med"],
            WHITE,
            cx,
            self.game.height - 160,
        )

        pygame.draw.rect(
            screen, GB_PANEL_DARK, self.rect_select, border_radius=10)
        Utils.draw_text_outline(
            screen,
            "SELECT",
            self.game.assets.fonts["s_med"],
            WHITE,
            self.rect_select.centerx,
            self.rect_select.centery,
            outline_color=BLACK,
        )


# [REF-0021: Starter Selection]
class StarterSelectionState(GameState):
    def __init__(self, game, starter_ids=None, region="KANTO"):
        super().__init__(game)
        self.region = region

        config = game.loader.area_data.get("GAME_CONFIG", {})
        default_starters = config.get("STARTER_IDS", [1, 4, 7])
        self.starter_ids = starter_ids if starter_ids else default_starters

        self.starters_raw = []
        self.starters = []
        self.selected_idx = -1
        self.questions_needed = 2
        self.questions_correct = 0
        self.problem_str, self.correct_ans, self.options = "", "", []
        self.answer_btn_rects = [pygame.Rect(0, 0, 0, 0) for _ in range(3)]
        self.feedback_text = ""
        self.feedback_timer = 0
        self.selection_complete = False
        self.math_buttons_ready = False

        bg_name = (
            "starter_johto.png" if self.region == "JOHTO"
            else "starter_bg.png"
        )
        background_raw = self.game.assets.get_background(bg_name)
        if background_raw:
            self.background = pygame.transform.scale(
                background_raw, (self.game.width, self.game.height)
            )
        else:
            self.background = None

        self.player_back_sprite = None
        char_key = getattr(self.game, "player_character", "red")
        img = self.game.assets.get_player_image(char_key, back=True)
        if img:
            h = int(self.game.height * 0.45)
            w = int(img.get_width() * (h / img.get_height()))
            self.player_back_sprite = pygame.transform.scale(img, (w, h))

        box_height = int(self.game.height * 0.25)
        main_rect = pygame.Rect(
            0, self.game.height - box_height, self.game.width, box_height
        )
        self.dialogue_box = ClassicDialogueBox(
            main_rect,
            self.game.assets.get_text("loading_starters"),
            self.game.assets.fonts["med"],
        )

        threading.Thread(target=self.load_starters, daemon=True).start()

    def start(self):
        pass

    def load_starters(self):
        if (
            self.region == "KANTO"
            and hasattr(self.game, "preloaded_starter_data")
            and self.game.preloaded_starter_data
        ):
            self.starters_raw = self.game.preloaded_starter_data
        else:
            self.starters_raw = [
                self.game.loader.fetch_specific(i)
                for i in self.starter_ids
            ]
        self.starters = [
            Pokemon(p, self.game.assets, size_mult=2)
            for p in self.starters_raw
        ]
        self.dialogue_box.reset(self.game.assets.get_text("choose_partner"))

    def generate_math_set(self):
        op = random.choice(["+", "-"])
        if op == "+":
            c = random.randint(3, 10)
            a = random.randint(1, c - 1)
            b = c - a
        else:
            a = random.randint(3, 10)
            b = random.randint(1, a - 1)
            c = a - b

        problem_str = f"{a} {op} {b} = ?"
        ans = c
        opts = {c}
        while len(opts) < 3:
            offset = random.choice([-2, -1, 1, 2])
            f = c + offset
            if f >= 0 and f not in opts:
                opts.add(f)
        return problem_str, ans, sorted(
            list(opts), key=lambda x: random.random()
        )

    def update_answer_buttons(self):
        self.math_buttons_ready = True
        box_rect = self.dialogue_box.rect

        for i in range(3):
            # Position buttons inside the golden dialogue box at the bottom
            btn_w = 120
            btn_h = 50
            spacing = 20
            total_width = (btn_w * 3) + (spacing * 2)
            start_x = box_rect.centerx - (total_width // 2)

            cx = start_x + i * (btn_w + spacing) + (btn_w // 2)
            cy = box_rect.bottom - 40

            self.answer_btn_rects[i] = pygame.Rect(
                cx - btn_w // 2, cy - btn_h // 2, btn_w, btn_h
            )

    def handle_events(self, events):
        if not self.starters:
            return

        for event in events:
            buttons_handled = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.math_buttons_ready and not self.selection_complete:
                    for i, rect in enumerate(self.answer_btn_rects):
                        if rect.width > 0 and rect.collidepoint(event.pos):
                            buttons_handled = True
                            if self.options[i] == self.correct_ans:
                                self.questions_correct += 1
                                self.feedback_text = self.game.assets.get_text(
                                    "correct"
                                )
                                self.feedback_timer = 45
                                if (
                                    self.questions_correct
                                    >= self.questions_needed
                                ):
                                    self.complete_selection()
                                else:
                                    (
                                        self.problem_str,
                                        self.correct_ans,
                                        self.options,
                                    ) = self.generate_math_set()
                                    self.update_answer_buttons()
                            else:
                                self.feedback_text = self.game.assets.get_text(
                                    "try_again"
                                )
                                self.feedback_timer = 45
                                (
                                    self.problem_str,
                                    self.correct_ans,
                                    self.options,
                                ) = self.generate_math_set()
                                self.update_answer_buttons()
                            break

            if buttons_handled:
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.selected_idx == -1:
                    clicked_idx = -1
                    for i, p in enumerate(self.starters):
                        hover_y = (
                            math.sin(
                                pygame.time.get_ticks() * p.bob_speed
                                + p.bob_offset
                            )
                            * p.bob_amount
                        )
                        base_pos = self.get_pos(i)
                        draw_pos = (base_pos[0], base_pos[1] + hover_y)

                        full_rect = p.image.get_rect(center=draw_pos)
                        hitbox = full_rect.inflate(
                            -full_rect.width * 0.4, -full_rect.height * 0.4
                        )

                        if hitbox.collidepoint(event.pos):
                            clicked_idx = i

                    if clicked_idx != -1:
                        self.dialogue_box.reset("")
                        self.selected_idx = clicked_idx
                        self.problem_str, self.correct_ans, self.options = (
                            self.generate_math_set()
                        )
                        self.update_answer_buttons()

            self.dialogue_box.handle_event(event)

    def complete_selection(self):
        chosen_pokemon_obj = self.starters[self.selected_idx]
        if chosen_pokemon_obj.cry:
            chosen_pokemon_obj.cry.play()

        msg_text = self.game.assets.get_text(
            "chosen_starter", name=chosen_pokemon_obj.name
        )

        # Force starter to lead position.
        # Move 6th member to PC if party is full.
        team = self.game.story_manager.player_team
        pc = self.game.story_manager.pc_pokemon

        if len(team) >= 6:
            moved_pkmn = team.pop(5)  # Remove the 6th Pokémon
            pc.append(moved_pkmn)
            pc_msg = (
                f"{moved_pkmn.display_name.upper()} was sent to BILL'S PC!"
            )
            msg_text = [msg_text, pc_msg]

        team.insert(0, chosen_pokemon_obj)

        self.game.data.add_pokemon(chosen_pokemon_obj)
        self.game.data.save()

        # Handle Johto-specific flag
        if self.region == "JOHTO":
            flag_key = "received_starter_johto"
            self.game.story_manager.story_flags[flag_key] = True
        else:
            flag_key = "received_starter_kanto"
            self.game.story_manager.story_flags[flag_key] = True

        # Determine Rival
        if self.region == "JOHTO":
            # Silver takes the advantage (Rival 1)
            rival_map = {0: 1, 1: 2, 2: 0}
            s_idx = self.selected_idx
            rival_idx_in_list = rival_map.get(s_idx, 0)
            rival_starter = self.starters_raw[rival_idx_in_list]
            self.game.story_manager.rival_starter_raw = rival_starter

            # The User Rival (Rival 2) takes the 3rd one
            all_indices = {0, 1, 2}
            taken = {self.selected_idx, rival_idx_in_list}
            remaining = list(all_indices - taken)[0]
            user_rival_starter = self.starters_raw[remaining]
            self.game.story_manager.user_rival_starter_raw = (
                user_rival_starter
            )
        else:
            # Standard Kanto Logic
            player_primary_type = (
                chosen_pokemon_obj.types[0]
                if chosen_pokemon_obj.types
                else "NORMAL"
            )
            advantage_map = {
                "GRASS": "FIRE",
                "FIRE": "WATER",
                "WATER": "GRASS"
            }
            rival_type_advantage = advantage_map.get(player_primary_type)

            rival_choice = None
            remaining_starters = [
                p_raw for i, p_raw in enumerate(self.starters_raw)
                if i != self.selected_idx
            ]
            if rival_type_advantage:
                for starter in remaining_starters:
                    if rival_type_advantage in starter.get("types", []):
                        rival_choice = starter
                        break
            if not rival_choice:
                rival_choice = random.choice(remaining_starters)

            self.game.story_manager.rival_starter_raw = rival_choice

        # Finalize World Entry if this is the game start
        if not self.game.story_manager.game_started:
            self.game.story_manager.game_started = True
            if self.region == "JOHTO":
                self.game.story_manager.current_area_key = "NEW_BARK_TOWN"
            else:
                self.game.story_manager.current_area_key = "PALLET_TOWN"

        self.selection_complete = True
        self.dialogue_box.reset(msg_text)
        self.dialogue_box.callback = self.start_rival_battle

    def start_rival_battle(self):
        from src.states.battle import TrainerBattleState, TrainerIntroState
        rival_pokemon = Pokemon(
            self.game.story_manager.rival_starter_raw,
            self.game.assets,
            size_mult=2
        )

        if self.region == "JOHTO":
            rival_name = "SILVER"
            trainer_class = "RIVAL"
            rival_sprite = self.game.assets.get_trainer_image("silver.png")
            if not rival_sprite:
                # Fallback if silver.png missing
                rival_sprite = self.game.assets.get_trainer_image("rival.png")
            bg_name = "battle_elmlab.png"  # Optional custom BG
        else:
            rival_sprite_key = getattr(self.game, "rival_character", "blue")
            rival_name = getattr(self.game, "rival_name", "BLUE")
            trainer_class = "RIVAL"
            bg_name = "battle_oaklab.png"

            rival_sprite = self.game.assets.get_player_image(
                rival_sprite_key, back=False
            )
            if rival_sprite:
                h = int(self.game.height * 0.6)
                aspect_ratio = h / rival_sprite.get_height()
                w = int(rival_sprite.get_width() * aspect_ratio)
                rival_sprite = pygame.transform.scale(rival_sprite, (w, h))
            else:
                rival_sprite = self.game.assets.get_trainer_image("rival.png")

        area_name = (
            "NEW_BARK_TOWN" if self.region == "JOHTO"
            else "PALLET_TOWN"
        )
        battle_state = TrainerBattleState(
            self.game,
            rival_pokemon,
            trainer_sprite=rival_sprite,
            trainer_class=trainer_class,
            trainer_name=rival_name,
            area_name=area_name,
            battle_type="rival",
        )

        lab_bg = self.game.assets.get_background(bg_name)
        if lab_bg:
            box_top = Utils.get_full_dialogue_rect(self.game).top - 8
            scaled_bg = pygame.transform.scale(
                lab_bg, (self.game.width, box_top)
            )
            battle_state.background = scaled_bg

        all_dialogue = self.game.loader.area_data.get(
            "TRAINER_CLASS_DIALOGUE", {}
        )
        intro_text_options = all_dialogue.get(
            trainer_class, {}
        ).get("intro", ["Let's battle!"])

        if self.region == "JOHTO":
            intro_text_options = ["...You think you're strong?"]

        dialogue = random.choice(intro_text_options)
        intro_state = TrainerIntroState(
            self.game, rival_sprite, dialogue, battle_state
        )

        self.game.change_state(intro_state)

    def update(self):
        self.dialogue_box.update()
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

    def get_pos(self, i):
        return (
            self.game.width * 0.75 + (i - 1) * (self.game.width // 9),
            self.game.height * 0.35,
        )

    def draw(self):
        if self.background:
            self.game.screen.blit(self.background, (0, 0))
        else:
            self.game.screen.fill(BLACK)

        self.dialogue_box.draw(self.game.screen)

        if not self.starters:
            return

        if self.selection_complete:
            return

        if self.player_back_sprite:
            sprite_rect = self.player_back_sprite.get_rect(
                midbottom=(self.game.width * 0.25, self.dialogue_box.rect.top)
            )
            self.game.screen.blit(self.player_back_sprite, sprite_rect)

        for i, p in enumerate(self.starters):
            pos = self.get_pos(i)
            if self.selected_idx != -1 and i != self.selected_idx:
                p.image.set_alpha(100)
            else:
                p.image.set_alpha(255)

            hover_y = (
                math.sin(pygame.time.get_ticks() * p.bob_speed + p.bob_offset)
                * p.bob_amount
            )
            draw_pos = (pos[0], pos[1] + hover_y)
            self.game.screen.blit(p.image, p.image.get_rect(center=draw_pos))

            # Debug: Draw Hitboxes
            if self.game.debug_mode:
                full_rect = p.image.get_rect(center=draw_pos)
                hitbox = full_rect.inflate(
                    -full_rect.width * 0.4, -full_rect.height * 0.4
                )
                pygame.draw.rect(self.game.screen, RED, hitbox, 2)

        if (
            self.selected_idx != -1
            and self.questions_correct < self.questions_needed
        ):
            msg = self.game.assets.get_text(
                "starter_befriend",
                n=self.questions_needed,
                name=self.starters[self.selected_idx].name,
            )
            if "Answer" in msg and len(msg) > 30:
                starter_name = self.starters[self.selected_idx].name
                msg = (
                    f"Answer {self.questions_needed} Qs to "
                    f"befriend {starter_name}!"
                )

            Utils.draw_text_outline(
                self.game.screen,
                msg,
                self.game.assets.fonts["s_med"],
                GB_TEXT,
                self.game.width // 2,
                self.dialogue_box.rect.top + 30,
                outline_color=GB_PANEL,
            )

            Utils.draw_text_outline(
                self.game.screen,
                self.problem_str,
                self.game.assets.fonts["big"],
                GOLD,
                self.game.width // 2,
                self.dialogue_box.rect.top + 80,
            )

            for i in range(3):
                # Rects are updated in update_answer_buttons, just use them
                btn_rect = self.answer_btn_rects[i]
                txt = str(self.options[i])

                self.answer_btn_rects[i] = btn_rect
                pygame.draw.rect(
                    self.game.screen, WHITE, btn_rect,
                    border_radius=10
                )
                pygame.draw.rect(
                    self.game.screen, BLACK, btn_rect, 2,
                    border_radius=10
                )

                Utils.draw_text_outline(
                    self.game.screen,
                    txt,
                    self.game.assets.fonts["num"],
                    BLACK,
                    btn_rect.centerx,
                    btn_rect.centery,
                    outline_color=WHITE
                )

        if self.feedback_timer > 0:
            Utils.draw_text_outline(
                self.game.screen,
                self.feedback_text,
                self.game.assets.fonts["s_med"],
                GOLD,
                self.game.width // 2,
                self.game.height * 0.5,
            )


# [REF-0033: Load Game State]
class LoadState(GameState):
    """Allows loading a game from the pause menu with confirmation."""
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.save_slots = self.load_save_slots()
        self.buttons = []
        self.phase = "SELECT"
        self.selected_slot_index = -1

        for i in range(5):
            y_pos = game.height * 0.2 + i * 100
            rect = (game.width / 2 - 300, y_pos, 600, 80)

            def make_callback(index):
                return lambda: self.confirm_load(index)

            slot_text = self.get_slot_text(i)
            btn = Button(
                rect, slot_text, game.assets.fonts["tiny"], make_callback(i)
            )
            self.buttons.append(btn)

        self.btn_back = Button(
            (game.width / 2 - 100, game.height - 100, 200, 60),
            "BACK",
            game.assets.fonts["small"],
            self.go_back,
            bg_color=RED,
        )

        # Confirmation UI
        self.confirm_dialogue = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(game),
            ["Load this file?", "Unsaved progress will be lost."],
            game.assets.fonts["med"]
        )
        cx, cy = game.width // 2, game.height // 2
        self.btn_yes = Button(
            (cx - 150, cy + 50, 120, 60),
            "YES",
            game.assets.fonts["small"],
            self.do_load,
            bg_color=GREEN,
            autosize=False
        )
        self.btn_no = Button(
            (cx + 30, cy + 50, 120, 60),
            "NO",
            game.assets.fonts["small"],
            self.cancel_load,
            bg_color=RED,
            autosize=False
        )

    def load_save_slots(self):
        # Reuse logic from SaveState or move to DataManager if preferred
        slots = []
        for i in range(5):
            fname = os.path.join(
                self.game.assets.base_dir, f"game_data_{i}.json"
            )
            if os.path.exists(fname):
                try:
                    with open(fname, "r") as f:
                        data = json.load(f)
                        slots.append({
                                "name": data.get("save_name", f"File {i+1}"),
                                "area": data.get("save_area", "Unknown"),
                                "file": fname
                            })
                except (json.JSONDecodeError, IOError):
                    slots.append(None)
            else:
                slots.append(None)
        return slots

    def get_slot_text(self, i):
        return (
            f"{self.save_slots[i]['name']} - {self.save_slots[i]['area']}"
            if self.save_slots[i]
            else "EMPTY"
        )

    def go_back(self):
        self.game.change_state(self.previous_state)

    def confirm_load(self, i):
        if self.save_slots[i]:
            self.selected_slot_index = i
            self.phase = "CONFIRM"
            self.game.ui_manager.elements.clear()
            self.game.ui_manager.add_element(self.confirm_dialogue)
            self.game.ui_manager.add_element(self.btn_yes)
            self.game.ui_manager.add_element(self.btn_no)

    def do_load(self):
        # Load the specific file
        slot_data = self.save_slots[self.selected_slot_index]
        self.game.data.save_file = slot_data["file"]

        # CRITICAL: Force reload data from the new file path
        self.game.data.data = self.game.data._load()

        if self.game.load_game_data():
            pass
        else:
            self.game.show_dialogue(["Error loading save file."])
            self.cancel_load()

    def cancel_load(self):
        self.phase = "SELECT"
        self.start()

    def start(self):
        self.game.ui_manager.elements.clear()
        for btn in self.buttons:
            self.game.ui_manager.add_element(btn)
        self.game.ui_manager.add_element(self.btn_back)

    def handle_events(self, events):
        pass

    def update(self):
        if self.phase == "CONFIRM":
            self.confirm_dialogue.update()

    def draw(self):
        self.game.screen.fill(BLACK)
        if self.phase == "SELECT":
            Utils.draw_text_outline(
                self.game.screen,
                "LOAD GAME",
                self.game.assets.fonts["med"],
                WHITE,
                self.game.width // 2,
                50
            )
            self.game.ui_manager.draw(self.game.screen)
        elif self.phase == "CONFIRM":
            self.confirm_dialogue.draw(self.game.screen)
            self.btn_yes.draw(self.game.screen)
            self.btn_no.draw(self.game.screen)


# [REF-0037: Save Game State]
class SaveState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        
        # ARCHITECT: Directly identify current slot to prevent accidental overwriting of other slots
        current_file = os.path.basename(self.game.data.save_file)
        self.selected_slot = int(current_file.split('_')[-1].split('.')[0]) if 'game_data_' in current_file else 0
        
        self.input_text = self.game.data.data.get("save_name", f"File {self.selected_slot + 1}")
        self.input_active = True
        
        self.bg_panel = pygame.Rect(
            game.width * 0.15, game.height * 0.15,
            game.width * 0.7, game.height * 0.7
        )
        self.btn_cancel_input = Button(
            (game.width / 2 - 60, game.height / 2 + 110, 120, 50),
            "CANCEL",
            game.assets.fonts["tiny"],
            self.cancel_input,
            bg_color=RED,
            visible=True
        )

    def cancel_input(self):
        self.go_back()

    def go_back(self):
        self.game.change_state(self.previous_state)

    def save_to_slot(self, slot_index, save_name):
        self.game.update_save_data()
        self.game.data.data["save_name"] = save_name
        self.game.data.data["save_area"] = (
            self.game.story_manager.current_area_key.replace("_", " ").title()
        )

        original_save_file = self.game.data.save_file
        self.game.data.save_file = os.path.join(
            self.game.assets.base_dir, f"game_data_{slot_index}.json"
        )
        self.game.data.save()
        self.game.data.save_file = original_save_file
        self.go_back()

    def start(self):
        self.game.ui_manager.add_element(self.btn_cancel_input)

    def handle_events(self, events):
        if not self.input_active:
            return
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.save_to_slot(self.selected_slot, self.input_text)
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.cancel_input()
                elif len(self.input_text) < 20:
                    self.input_text += event.unicode

    def update(self):
        pass

    def draw(self):
        self.game.screen.fill(BLACK)

        # Draw a nice panel for the menu
        pygame.draw.rect(
            self.game.screen, (40, 40, 60),
            self.bg_panel, border_radius=20
            )
        pygame.draw.rect(
            self.game.screen, WHITE,
            self.bg_panel, 4, border_radius=20
            )

        Utils.draw_text_outline(
            self.game.screen,
            "SAVE GAME",
            self.game.assets.fonts["med"],
            WHITE,
            self.game.width / 2,
            50,
        )

        self.game.ui_manager.draw(self.game.screen)

        if self.input_active:
            cx, cy = self.game.width / 2, self.game.height / 2
            pygame.draw.rect(
                self.game.screen,
                GB_PANEL,
                (cx - 250, cy - 100, 500, 200),
                border_radius=15,
            )
            pygame.draw.rect(
                self.game.screen,
                GB_BORDER,
                (cx - 250, cy - 100, 500, 200),
                5,
                border_radius=15,
            )
            Utils.draw_text_outline(
                self.game.screen,
                "Enter Save Name:",
                self.game.assets.fonts["s_med"],
                GB_TEXT,
                cx,
                cy - 50,
            )
            input_rect = pygame.Rect(cx - 200, cy, 400, 50)
            pygame.draw.rect(self.game.screen, WHITE, input_rect)
            pygame.draw.rect(self.game.screen, BLACK, input_rect, 2)
            cursor_text = self.input_text + (
                "_" if (pygame.time.get_ticks() // 500) % 2 == 1 else ""
            )
            Utils.draw_text_outline(
                self.game.screen,
                cursor_text,
                self.game.assets.fonts["s_med"],
                BLACK,
                input_rect.left + 10,
                input_rect.centery,
                align="left",
            )
            Utils.draw_text_outline(
                self.game.screen,
                "Press ENTER to save",
                self.game.assets.fonts["tiny"],
                GB_TEXT,
                cx,
                cy + 70,
            )


# [REF-0028: Loading State]
class LoadingState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.angle = 0
        self.ball_img = game.assets.ball_imgs[0]
        self.ball_img = pygame.transform.scale(self.ball_img, (150, 150))

    def handle_events(self, events):
        pass

    def update(self):
        self.angle = (self.angle - 5) % 360
        if not self.game.loader.queue.empty():
            self.game.change_state(self.game.states["play"])

    def draw(self):
        self.game.screen.fill(BLACK)
        Utils.draw_text_outline(
            self.game.screen,
            "LOADING WORLD DATA...",
            self.game.assets.fonts["med"],
            WHITE,
            self.game.width // 2,
            self.game.height * 0.3,
        )
        rot_img = pygame.transform.rotate(self.ball_img, self.angle)
        rect = rot_img.get_rect(center=(self.game.width // 2,
                                        self.game.height * 0.6))
        self.game.screen.blit(rot_img, rect)
