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
            "POKEMATH ADVENTURES",
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
    """Choose a region: where a new game begins, or (mode="move") where Mom buys the next home."""
    COLS = 3

    def __init__(self, game, mode="new", return_state=None):
        super().__init__(game)
        self.mode = mode
        self.return_state = return_state
        story = game.story_manager
        starts = story.get_region_starts()
        if mode == "move":
            here = story.get_current_region()
            starts = [(r, cfg) for r, cfg in starts if r != here]
        self.regions = [r for r, _ in starts] or ["KANTO"]
        self.subtitles = {r: cfg.get("subtitle", "") for r, cfg in starts}
        if mode == "move":
            for r in self.regions:
                if story.is_region_champion(r):
                    self.subtitles[r] = "CHAMPION"
                elif story.story_flags.get(f"unlocked_{r.lower()}_badges"):
                    self.subtitles[r] = "VISITED"
                else:
                    self.subtitles[r] = "NEW - " + self.subtitles[r].split(" / ")[0]
        self.selected_idx = 0
        self.stay_rect = pygame.Rect(game.width // 2 - 120, game.height - 110, 240, 60)

        rows = (len(self.regions) + self.COLS - 1) // self.COLS
        gap = 24
        card_w = min(320, (game.width - 80 - gap * (self.COLS - 1)) // self.COLS)
        card_h = min(130, (game.height - 300 - gap * (rows - 1)) // rows)
        grid_w = self.COLS * card_w + (self.COLS - 1) * gap
        left, top = (game.width - grid_w) // 2, 170
        self.rects = [
            pygame.Rect(left + (i % self.COLS) * (card_w + gap),
                        top + (i // self.COLS) * (card_h + gap), card_w, card_h)
            for i in range(len(self.regions))
        ]

    def handle_events(self, events):
        n = len(self.regions)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.mode == "move" and self.stay_rect.collidepoint(event.pos):
                    self.stay()
                    return
                for i, rect in enumerate(self.rects):
                    if rect.collidepoint(event.pos):
                        self.selected_idx = i
                        self.confirm_selection()
                        return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.selected_idx = (self.selected_idx - 1) % n
                elif event.key == pygame.K_RIGHT:
                    self.selected_idx = (self.selected_idx + 1) % n
                elif event.key == pygame.K_UP:
                    self.selected_idx = (self.selected_idx - self.COLS) % n
                elif event.key == pygame.K_DOWN:
                    self.selected_idx = (self.selected_idx + self.COLS) % n
                elif event.key == pygame.K_RETURN:
                    self.confirm_selection()

    def stay(self):
        if self.return_state:
            self.game.change_state(self.return_state)
            self.return_state.show_message(["Mom: No rush! The house hunt can wait.",
                                            "Visit me at home whenever you're ready to move."])

    def confirm_selection(self):
        region = self.regions[self.selected_idx]
        story = self.game.story_manager
        if self.mode == "move":
            self.game.change_state(story.move_to_region(region))
            return
        cfg = story.get_region_start(region)
        story.starting_region = region
        story.story_flags[f"unlocked_{region.lower()}_badges"] = True
        story.badges.setdefault(region, [])
        story.active_badge_region = region
        story.current_area_key = cfg.get("start_area", "PALLET_TOWN")

        self.game.change_state(RivalSelectionState(self.game))

    def update(self):
        pass

    def draw(self):
        screen = self.game.screen
        screen.fill(BLACK)
        cx = self.game.width // 2

        title = "WHERE SHOULD WE MOVE?" if self.mode == "move" else "WHERE WILL YOUR JOURNEY BEGIN?"
        Utils.draw_text_outline(screen, title, self.game.assets.fonts["med"], WHITE, cx, 100)
        if self.mode == "move":
            pygame.draw.rect(screen, GB_PANEL_DARK, self.stay_rect, border_radius=12)
            pygame.draw.rect(screen, WHITE, self.stay_rect, 2, border_radius=12)
            Utils.draw_text_outline(screen, "STAY HERE", self.game.assets.fonts["small"], WHITE,
                                    self.stay_rect.centerx, self.stay_rect.centery)

        for i, rect in enumerate(self.rects):
            is_selected = (self.selected_idx == i)
            bg_color = GB_PANEL if is_selected else GB_PANEL_DARK
            border_color = GOLD if is_selected else WHITE
            border_thickness = 6 if is_selected else 2

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
                text_color, rect.centerx, rect.centery - 14
            )
            Utils.draw_text_outline(
                screen, self.subtitles.get(region_name, ""),
                self.game.assets.fonts["tiny"],
                GRAY, rect.centerx, rect.centery + 26
            )

        if self.mode != "move":
            Utils.draw_text_outline(
                screen, "SELECT A REGION TO CONTINUE", self.game.assets.fonts["small"],
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
        # [FIX] Set rival name to ??? initially if no name is entered
        rival_name_input = self.input_name.strip()
        self.game.rival_name = rival_name_input if rival_name_input else "???"
        # Store the actual character name for later if needed, but display ???
        self.game.rival_true_name = char_key.upper()

        region = self.game.story_manager.starting_region
        starter_ids = self.game.story_manager.get_region_start(region).get(
            "starters", [1, 4, 7])

        # Pick math difficulty before the starter (the starter pick has math)
        self.game.change_state(
            DifficultySelectionState(
                self.game,
                on_confirm=lambda: self.game.change_state(
                    StarterSelectionState(
                        self.game,
                        starter_ids=starter_ids,
                        region=region
                    )
                ),
                on_back=lambda: self.game.change_state(RivalSelectionState(self.game)),
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

        self.region_cfg = self.game.story_manager.get_region_start(self.region)
        background_raw = None
        for bg_name in (self.region_cfg.get("starter_bg"),
                        f"starter_{self.region.lower()}.png", "starter_bg.png"):
            background_raw = self.game.assets.get_background(bg_name)
            if background_raw:
                break
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
        lines = []
        for key in ("newgame_text", "intro_text"):
            lines += self._region_lines(key)
        lines.append(self.game.assets.get_text("choose_partner"))
        self.dialogue_box.reset(lines)

    def _region_lines(self, cfg_key):
        """Region text from REGION_START, with player/rival names filled in."""
        key = self.region_cfg.get(cfg_key)
        if not key:
            return []
        text = self.game.assets.get_text(
            key, player_name=self.game.player_name,
            rival_name=getattr(self.game, "rival_name", "???"))
        return text if isinstance(text, list) else [text]

    @property
    def uses_town_rival(self):
        """Hoenn onward: the rival battle fires in the starting town, not here."""
        return self.region not in ("KANTO", "JOHTO")

    def generate_math_set(self):
        # Starter pick uses the difficulty chosen on the previous screen
        level = self.game.story_manager.get_math_level()
        return self.game.math.generate(level, num_options=3)

    def update_answer_buttons(self):
        self.math_buttons_ready = True
        box_rect = self.dialogue_box.rect

        for i in range(3):
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

        team = self.game.story_manager.player_team
        pc = self.game.story_manager.pc_pokemon

        if len(team) >= 6:
            moved_pkmn = team.pop(5)
            pc.append(moved_pkmn)
            pc_msg = (
                f"{moved_pkmn.display_name.upper()} was sent to BILL'S PC!"
            )
            msg_text = [msg_text, pc_msg]

        team.insert(0, chosen_pokemon_obj)

        self.game.data.add_pokemon(chosen_pokemon_obj)
        self.game.data.save()

        story = self.game.story_manager
        r = self.region.lower()
        story.story_flags[f"received_starter_{r}"] = True
        story.story_flags[f"has_{r}_starter"] = True
        story.story_flags[f"starter_{r}"] = chosen_pokemon_obj.id

        if self.uses_town_rival:
            msg_text = (msg_text if isinstance(msg_text, list) else [msg_text])
            msg_text += self._region_lines("starter_text")
            story.balls_left = max(story.balls_left, 5)
        elif self.region == "JOHTO":
            rival_map = {0: 1, 1: 2, 2: 0}
            s_idx = self.selected_idx
            rival_idx_in_list = rival_map.get(s_idx, 0)
            rival_starter = self.starters_raw[rival_idx_in_list]
            self.game.story_manager.rival_starter_raw = rival_starter

            all_indices = {0, 1, 2}
            taken = {self.selected_idx, rival_idx_in_list}
            remaining = list(all_indices - taken)[0]
            user_rival_starter = self.starters_raw[remaining]
            self.game.story_manager.user_rival_starter_raw = (
                user_rival_starter
            )
        else:
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

        if not story.game_started:
            story.game_started = True
            story.current_area_key = self.region_cfg.get(
                "start_area", "PALLET_TOWN")

        self.selection_complete = True
        self.dialogue_box.reset(msg_text)
        self.dialogue_box.callback = self.start_rival_battle

    def start_rival_battle(self):
        if self.uses_town_rival:
            from src.states.overworld import AreaTransitionState
            self.game.change_state(AreaTransitionState(
                self.game, self.region_cfg.get("start_area")))
            return

        if self.region == "JOHTO":
            self.game.story_manager.story_flags["johto_rival_met_in_lab"] = True
            from src.states.overworld import AreaTransitionState
            self.game.change_state(AreaTransitionState(self.game, "NEW_BARK_TOWN"))
            return

        from src.states.battle import TrainerBattleState, TrainerIntroState
        rival_pokemon = Pokemon(
            self.game.story_manager.rival_starter_raw,
            self.game.assets,
            size_mult=2
        )

        if self.region == "JOHTO": # This block is now effectively Kanto-only
            rival_name = getattr(self.game, "rival_name", "???") # [FIX] Use game.rival_name
            trainer_class = "RIVAL"
            rival_sprite = self.game.assets.get_trainer_image("silver.png")
            if not rival_sprite:
                rival_sprite = self.game.assets.get_trainer_image("rival.png")
            bg_name = "battle_elmlab.png"
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
            starter_battle=True,
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
        slot_data = self.save_slots[self.selected_slot_index]
        self.game.data.save_file = slot_data["file"]

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

        current_file = os.path.basename(self.game.data.save_file)
        is_data = 'game_data_' in current_file
        self.selected_slot = int(
            current_file.split('_')[-1].split('.')[0]) if is_data else 0

        self.input_text = self.game.data.data.get("save_name", f"File {
            self.selected_slot + 1}")
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


# [REF-0071: Math Difficulty Selection]
class DifficultySelectionState(GameState):
    """
    Lets the player pick how hard the math is. Used in two places:
      * New Game flow (after choosing a rival, before the starter)
      * In-game OPTIONS button (Play/City HUD)

    on_confirm / on_back are callables so the same screen works in both
    places and can never soft-lock: BACK and ESC always leave.
    """

    def __init__(self, game, on_confirm, on_back, title="CHOOSE YOUR MATH LEVEL"):
        super().__init__(game)
        self.on_confirm = on_confirm
        self.on_back = on_back
        self.title = title
        self.story = game.story_manager
        self.input_lock = 6  # frames; stops the click that opened us from landing here

        # Card list: AUTO first, then every level from math_levels.json
        self.entries = [{"key": "AUTO", "name": "AUTO", "desc": ""}]
        for lv in game.math.levels:
            self.entries.append({"key": lv["id"], "name": lv["name"], "desc": lv["desc"]})

        current = self.story.math_difficulty
        self.selected_idx = next(
            (i for i, e in enumerate(self.entries) if e["key"] == current), 0
        )

        self._layout()
        self._refresh_preview()

    # ---------------- layout ----------------
    def _layout(self):
        w, h = self.game.width, self.game.height
        # 3 columns on wide screens, 1 tall column on portrait phones
        self.cols = 3 if w >= h else 1
        rows = (len(self.entries) + self.cols - 1) // self.cols
        margin, gap = int(w * 0.05), int(w * 0.015)
        top, bottom = int(h * 0.20), int(h * 0.78)
        card_w = (w - 2 * margin - gap * (self.cols - 1)) // self.cols
        card_h = min(int(h * 0.16), (bottom - top - gap * (rows - 1)) // rows)
        self.card_rects = []
        for i in range(len(self.entries)):
            r, c = divmod(i, self.cols)
            self.card_rects.append(pygame.Rect(
                margin + c * (card_w + gap), top + r * (card_h + gap), card_w, card_h
            ))

        fonts = self.game.assets.fonts
        self.btn_back = Button((30, 30, 140, 70), "BACK", fonts["small"],
                               self.go_back, bg_color=RED)
        self.btn_confirm = Button((w // 2 - 150, int(h * 0.90) - 40, 300, 80),
                                  "CONFIRM", fonts["s_med"], self.confirm,
                                  bg_color=GREEN)

    def _fit_font(self, text, max_w, keys=("s_med", "small", "tiny")):
        """Dynamic font scaling: biggest game font that fits the space."""
        fonts = self.game.assets.fonts
        for k in keys:
            if fonts[k].size(text)[0] <= max_w:
                return fonts[k]
        return fonts[keys[-1]]

    def _entry_desc(self, entry):
        if entry["key"] == "AUTO":
            return f"Follows your journey (now {self._auto_name()})"
        return entry["desc"]

    def _auto_name(self):
        region = self.story.get_current_region()
        badges = len(self.story.badges.get(region, []))
        return self.game.math.level_by_id[
            self.game.math.auto_level(region, badges)]["name"]

    def _selected_level(self):
        key = self.entries[self.selected_idx]["key"]
        saved = self.story.math_difficulty
        self.story.math_difficulty = key
        level = self.story.get_math_level()
        self.story.math_difficulty = saved
        return level

    def _refresh_preview(self):
        # Prefer a plain "a + b = ?" style example; it explains the level best
        level = self._selected_level()
        for _ in range(20):
            self.preview = self.game.math.generate(level, 3)[0]
            if self.preview.endswith("= ?") and len(self.preview.split()) == 5:
                break

    # ---------------- actions ----------------
    def select(self, idx):
        idx = max(0, min(len(self.entries) - 1, idx))
        if idx != self.selected_idx:
            self.selected_idx = idx
            self._refresh_preview()

    def confirm(self):
        self.story.math_difficulty = self.entries[self.selected_idx]["key"]
        self.on_confirm()

    def go_back(self):
        self.on_back()

    # ---------------- GameState ----------------
    def start(self):
        self.input_lock = 6

    def handle_events(self, events):
        if self.input_lock > 0:
            return
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_back.handle_event(event) or self.btn_confirm.handle_event(event):
                    return  # state changed; ignore the rest of this frame
                for i, rect in enumerate(self.card_rects):
                    if rect.collidepoint(event.pos):
                        if i == self.selected_idx:
                            self.confirm()  # second tap on the same card confirms
                            return
                        self.select(i)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.go_back()
                    return
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self.confirm()
                    return
                step = {pygame.K_LEFT: -1, pygame.K_RIGHT: 1,
                        pygame.K_UP: -self.cols, pygame.K_DOWN: self.cols}.get(event.key)
                if step:
                    self.select(self.selected_idx + step)

    def update(self):
        if self.input_lock > 0:
            self.input_lock -= 1

    def draw(self):
        screen = self.game.screen
        fonts = self.game.assets.fonts
        w, h = self.game.width, self.game.height
        screen.fill(BLACK)

        Utils.draw_text_outline(screen, self.title,
                                self._fit_font(self.title, w - 360, ("med", "s_med", "small")),
                                GOLD, w // 2, int(h * 0.08))
        sub = "Pick what feels right - you can change it any time from OPTIONS."
        Utils.draw_text_outline(screen, sub, self._fit_font(sub, w - 80, ("small", "tiny")),
                                WHITE, w // 2, int(h * 0.145))

        for i, (entry, rect) in enumerate(zip(self.entries, self.card_rects)):
            selected = i == self.selected_idx
            pygame.draw.rect(screen, GB_PANEL if selected else GB_PANEL_DARK, rect, border_radius=15)
            pygame.draw.rect(screen, GOLD if selected else GB_BORDER, rect,
                             6 if selected else 3, border_radius=15)
            inner_w = rect.width - 30
            name = entry["name"] if entry["key"] == "AUTO" else f"{entry['key']}. {entry['name']}"
            Utils.draw_text_outline(screen, name, self._fit_font(name, inner_w),
                                    WHITE, rect.centerx, rect.centery - rect.height // 5)
            desc = self._entry_desc(entry)
            Utils.draw_text_outline(screen, desc, self._fit_font(desc, inner_w, ("small", "tiny")),
                                    WHITE if selected else LIGHT_GRAY,
                                    rect.centerx, rect.centery + rect.height // 5)

        example = f"EXAMPLE:  {self.preview}"
        Utils.draw_text_outline(screen, example, self._fit_font(example, w - 80, ("s_med", "small")),
                                GOLD, w // 2, int(h * 0.82))

        self.btn_back.draw(screen)
        self.btn_confirm.draw(screen)


def open_difficulty_options(game, return_state):
    """
    Opens the difficulty screen from any in-game state (route or town HUD)
    and comes back to return_state afterwards.
    """
    old_level = game.story_manager.get_math_level()

    def back():
        if hasattr(return_state, "is_resuming"):
            return_state.is_resuming = True
        game.change_state(return_state)

    def confirm():
        # If a question is already on screen and the level changed, swap it out
        if (getattr(return_state, "problem_str", "") not in ("", "...")
                and hasattr(return_state, "generate_math_set")
                and game.story_manager.get_math_level() != old_level):
            n = len(getattr(return_state, "options", [])) or 3
            (return_state.problem_str, return_state.correct_ans,
             return_state.options) = return_state.generate_math_set(num_options=n)
        game.update_save_data()
        back()

    game.change_state(DifficultySelectionState(
        game, on_confirm=confirm, on_back=back, title="MATH DIFFICULTY"))
