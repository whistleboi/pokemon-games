# [REF-0001: System Imports]
import pygame
import random
import math
import os
from src.states.base import GameState
from src.utils import Utils
from src.ui.dialogue import ClassicDialogueBox
from src.ui.widgets import Button
from src.ui.panels import CityActionMenu
from src.world.boss import BossManager
from src.pokemon.data import Pokemon
from src.vfx.particles import ShinyBurst, Starburst, IdleSparkle
from src.config import WHITE, BLACK, GREEN, BLUE, GOLD, RED, ORANGE, PURPLE, GRAY, FPS, VOLUME


# [REF-0029: Overworld & Play Logic]
class PlayState(GameState):
    def __init__(self, game, restore_data=None):
        super().__init__(game)
        self.area_data = game.story_manager.get_current_area_data()
        self._inject_regional_data()

        # Hard block ghost clicks from previous screens
        pygame.event.clear()

        main_rect = Utils.get_full_dialogue_rect(self.game)
        self.dialogue_box = ClassicDialogueBox(
            main_rect,
            [self.game.assets.get_text("welcome_kanto")],
            self.game.assets.fonts["med"],
            visible=False,
        )

        self.wild_catches_on_route = 0
        self.is_progression_paused = True
        self.is_resuming = False
        self.fresh_entry = (restore_data is None)

        # Round System State
        self.min_rounds = self.area_data.get("min_rounds", 1)
        self.rounds_completed = 0
        self.pending_wild_encounters = (
            0
        )
        self.initial_round_active = (
            True
        )

        self.total_caught = game.loader.total_caught
        self.balls_left = game.story_manager.balls_left
        self.current_streak = game.story_manager.current_streak

        if restore_data:
            self.balls_left = restore_data.get("balls_left", 0)
            self.current_streak = restore_data.get("current_streak", 0)
            self.rounds_completed = restore_data.get("rounds_completed", 0)
            self.pending_wild_encounters = restore_data.get(
                "pending_wild_encounters", 0
            )
            self.initial_round_active = restore_data.get("initial_round_active", True)

        self.flash_msg = ""
        self.flash_timer = 0
        self.feedback_text = ""
        self.feedback_color = WHITE
        self.boss_catches = 0
        self.since_last_boss = 0
        self.p_data = [None] * 3
        self.collected_team = (
            game.story_manager.player_team
        )
        self.was_shiny_override = False

        self.question_timer = 0
        self.current_ball_img = game.assets.ball_imgs[0]
        self.caught_indicator = pygame.transform.scale(game.assets.ball_imgs[0], (72, 72))

        self.starbursts = []
        self.idle_sparkles = []
        self.sprite_y = game.height * 0.4
        self.scr_shake_timer = 0

        self.ball_active = False
        self.input_delay = 30
        self.ball_pos = [0, 0]
        self.ball_target = [0, 0]
        self.pause_timer = 0
        self.caught_idx = -1
        self.flee_active = False
        self.shake_amount = 0
        self.runaway_x_offsets = [0, 0, 0]
        self.problem_str, self.correct_ans, self.options = (
            "",
            "",
            [],
        )

        self.answer_btn_rects = [pygame.Rect(0, 0, 0, 0) for _ in range(3)]

        self.stars = [
            [
                random.randint(0, game.width),
                random.randint(0, game.height),
                random.randint(2, 4),
            ]
            for _ in range(40)
        ]
        self.btn_size = 100 if game.assets.is_pc else 140

        # Top-Left HUD Buttons (Unified with CityState)
        btn_x, btn_y = 20, 80
        btn_w, btn_h = 120, 40
        spacing = 10
        
        self.hud_buttons = [
            # Local imports inside lambdas to prevent circular dependency
            Button((btn_x, btn_y, btn_w, btn_h), "PC",
                   game.assets.fonts["tiny"],
                   lambda: self._open_pc(),
                   bg_color=GREEN),
            Button((btn_x, btn_y + (btn_h+spacing), btn_w, btn_h), "BAG",
                   game.assets.fonts["tiny"],
                   lambda: self._open_bag(),
                   bg_color=BLUE),
            Button((btn_x, btn_y + (btn_h+spacing)*2, btn_w, btn_h), "BADGES",
                   game.assets.fonts["tiny"],
                   lambda: self._open_badges(),
                   bg_color=GOLD),
            Button((btn_x, btn_y + (btn_h+spacing)*3, btn_w, btn_h), "SAVE",
                   game.assets.fonts["tiny"], self.save_game, bg_color=GREEN),
            Button((btn_x, btn_y + (btn_h+spacing)*4, btn_w, btn_h), "LOAD",
                   game.assets.fonts["tiny"],
                   lambda: self._open_load(),
                   bg_color=RED),
        ]

        self.btn_flee = Button(
            rect=(game.width - 200, game.height // 2, 180, 80),
            text="FLEE",
            font=game.assets.fonts["small"],
            callback=self.action_flee,
            bg_color=ORANGE,
            visible=False,
        )
        
        self.btn_yes = Button((0, 0, 0, 0), "YES", game.assets.fonts["small"],
                              self.boss_catch_yes, bg_color=GREEN,
                              visible=False, autosize=False)
        self.btn_no = Button((0, 0, 0, 0), "NO", game.assets.fonts["small"],
                             self.boss_catch_no, bg_color=RED,
                             visible=False, autosize=False)
        self.boss_prompt_active = False
        
        self.route_buttons = []

        self.boss_manager = BossManager(game)

    # Helper methods for button callbacks to handle imports
    def _open_pc(self):
        from src.states.systems import PCState
        self.game.change_state(PCState(self.game, self))

    def _open_bag(self):
        from src.states.systems import BagState
        self.game.change_state(BagState(self.game, self))
    
    def _open_badges(self):
        from src.states.systems import BadgeCaseState
        self.game.change_state(BadgeCaseState(self.game, self))

    def _open_load(self):
        from src.states.menus import LoadState
        self.game.change_state(LoadState(self.game, self))

    def _inject_regional_data(self):
        """Merges external REGIONAL_CHANCES from JSON into the active area_data for the loader."""
        area_key = self.game.story_manager.current_area_key
        regional_key = f"{area_key}_REGIONAL_CHANCES"
        regional_data = self.game.loader.area_data.get(regional_key)

        if not regional_data:
            return

        # Ensure local area_data has the structure
        if "alt_forms" not in self.area_data:
            self.area_data["alt_forms"] = {"enabled": True, "weights": {}}
        
        target_weights = self.area_data["alt_forms"]["weights"]

        # Smart Form Mapping for Gen 1 IDs
        alolan_ids = {19, 20, 26, 27, 28, 37, 38, 50, 51, 52, 53, 74, 75, 76,
                      88, 89, 103, 105}
        hisuian_ids = {58, 59, 100, 101}
        galarian_ids = {77, 78, 79, 80, 83, 110, 122}
        paldean_ids = {128, 194}

        for pid_str, chance in regional_data.items():
            pid = int(pid_str)
            form = "normal"
            if pid in alolan_ids:
                form = "alolan"
            elif pid in hisuian_ids:
                form = "hisuian"
            elif pid in galarian_ids:
                form = "galarian"
            elif pid in paldean_ids:
                form = "paldean"

            key = f"{pid}_{form}"
            target_weights[key] = chance

    def show_dialogue(self, lines, callback=None):
        """Always uses the ONE persistent full-width box (no more double drawing)"""
        if hasattr(self.game.current_state, "dialogue_box") and isinstance(
            self.game.current_state.dialogue_box, ClassicDialogueBox
        ):
            self.game.current_state.dialogue_box.reset(lines)
            self.game.current_state.dialogue_box.callback = callback
            return self.game.current_state.dialogue_box
        self.dialogue_box.reset(lines)
        self.dialogue_box.callback = callback
        self.dialogue_box.visible = True
        return self.dialogue_box

    def check_roaming_encounter(self):
        """Checks for Entei/Raikou if Burned Tower has been visited."""
        # Only on wild routes
        if self.area_data.get("area_type") != "wild_route":
            return False
            
        # Check flag set by visiting Burned Tower
        if not self.game.story_manager.story_flags.get("visited_BURNED_TOWER"):
            return False
            
        # 5% Chance
        if random.random() < 0.05:
            roamers = [243, 244] # Raikou, Entei
            roamer_id = random.choice(roamers)
            
            # Check if already caught
            caught = self.game.data.data.get("pokedex", {})
            for v in caught.values():
                if v['id'] == roamer_id:
                    return False # Already caught

            raw = self.game.loader.fetch_specific(roamer_id)
            pokemon = Pokemon(raw, self.game.assets, size_mult=2.0)
            
            from src.states.battle import WildBattleState
            battle_state = WildBattleState(self.game, pokemon, self.game.story_manager.current_area_key)
            # Roamers flee quickly? We can handle that in WildBattleState later if desired.
            # For now, treat as standard boss battle event.
            
            self.game.change_state(battle_state)
            return True
        return False

    def check_ninja_ambush(self):
        """Checks for global ambush events defined in data."""
        # Ambush happens ONCE per fresh entry to an area
        if not self.fresh_entry:
            return False
        self.fresh_entry = False

        ambush_config = self.game.loader.area_data.get("AMBUSH_DATA", {})
        if not ambush_config:
            return False

        # Check for local area override first (e.g. "ambush_chance": 1.0 in ROUTE_1), else use global
        chance = self.area_data.get("ambush_chance", ambush_config.get("chance", 0))

        if random.random() < chance:
            trainers = ambush_config.get("trainers", [])
            if not trainers:
                return False
            
            t_data = random.choice(trainers)
            
            team = []
            
            # Check for random pool first
            pool = self.game.loader.area_data.get("NINJA_AMBUSH_POOL")
            if pool:
                # Randomize 2-3 pokemon
                count = random.randint(2, 3)
                team_ids = [random.choice(pool) for _ in range(count)]
            else:
                # Fallback to static team
                team_ids = t_data.get("team", [])
                if team_ids and isinstance(team_ids, list) and len(team_ids) > 0 and isinstance(team_ids[0], list):
                    team_ids = random.choice(team_ids)

            for pid in team_ids:
                raw = self.game.loader.fetch_specific(pid)
                team.append(Pokemon(raw, self.game.assets, size_mult=3.125))
            
            sprite_name = t_data.get("sprite", "youngster.png")
            trainer_sprite = self.game.assets.get_trainer_image(sprite_name)

            self.play_state_data = {
                "balls_left": self.balls_left,
                "current_streak": self.current_streak,
                "rounds_completed": self.rounds_completed,
                "pending_wild_encounters": 0,
                "initial_round_active": True
            }

            from src.states.battle import TrainerBattleState, TrainerIntroState
            battle_state = TrainerBattleState(
                self.game,
                team,
                trainer_sprite=trainer_sprite,
                trainer_class=t_data.get("class", "TRAINER"),
                trainer_name=t_data.get("name"),
                battle_type="field",
                area_name=self.game.story_manager.current_area_key,
                custom_dialogue=t_data.get("dialogue")
            )
            battle_state.play_state_data = self.play_state_data

            intro_text = random.choice(t_data.get("dialogue", {}).get("intro", ["Ambush!"]))
            
            # Ambush Background
            bg_ambush = self.game.assets.get_background("battle_ambush.png")
            if bg_ambush:
                box_top = Utils.get_full_dialogue_rect(self.game).top
                battle_state.background = pygame.transform.scale(bg_ambush, (self.game.width, box_top))
            
            intro = TrainerIntroState(self.game, trainer_sprite, intro_text, battle_state)
            self.game.change_state(intro)
            
            return True
        return False

    def save_game(self):
        from src.states.menus import SaveState
        self.game.change_state(SaveState(self.game, self))

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        for btn in self.hud_buttons:
            self.game.ui_manager.add_element(btn)
        self.game.ui_manager.add_element(self.btn_flee)
        self.game.ui_manager.add_element(self.btn_yes)
        self.game.ui_manager.add_element(self.btn_no)
        pygame.event.clear()

        if self.is_resuming:
            self.is_resuming = False
            return

        if self.check_ninja_ambush():
            return

        if self.check_roaming_encounter():
            return

        # [ELITE FOUR GAUNTLET LOGIC]
        # Force a checkpoint at the START of the Elite Four (Round 0) so retries go here.
        if self.game.story_manager.current_area_key in ["ELITE_FOUR", "KANTO_ROUTE_25"] and self.rounds_completed == 0 and self.fresh_entry:
             self.create_checkpoint()

        on_enter = self.area_data.get("on_enter_event")
        if on_enter and on_enter.get("type") == "trainer_battle":
            trainer_info = on_enter["trainer"]
            team_ids = on_enter["team"]
            
            if team_ids and isinstance(team_ids, list) and len(team_ids) > 0 and isinstance(team_ids[0], list):
                team_ids = random.choice(team_ids)

            opponent_team = []
            for tid in team_ids:
                raw = self.game.loader.fetch_specific(tid)
                opponent_team.append(Pokemon(raw, self.game.assets, size_mult=3.125))

            from src.states.battle import TrainerBattleState, TrainerIntroState
            class ScriptedBattleWrapper(TrainerBattleState):
                def __init__(
                    self, game, opponent_team, trainer_img_name, trainer_class, dialogue, trainer_name=None
                ):
                    super().__init__(
                        game,
                        opponent_team,
                        trainer_img_name=trainer_img_name,
                        trainer_class=trainer_class,
                        trainer_name=trainer_name,
                    )
                    self.dialogue_text = on_enter.get(
                        "dialogue_override", self.dialogue_text
                    )

                def handle_victory(self):
                    next_area_key = self.game.story_manager.get_current_area_data().get(
                        "next_area"
                    )
                    if next_area_key:
                        self.game.change_state(
                            AreaTransitionState(self.game, next_area_key)
                        )

            trainer_sprite = self.game.assets.get_trainer_image(trainer_info["sprite"])
            battle_state = ScriptedBattleWrapper(
                self.game,
                opponent_team,
                trainer_info["sprite"],
                trainer_info["class"],
                on_enter.get("dialogue_override"),
                trainer_name=trainer_info.get("name"),
            )
            intro_dialogue = on_enter.get("dialogue_override", "Prepare to battle!")

            intro_state = TrainerIntroState(
                self.game, trainer_sprite, intro_dialogue, battle_state
            )
            self.game.change_state(intro_state)
            return

        if self.pending_wild_encounters > 0:
            self.trigger_wild_encounter()
        elif self.initial_round_active and self.rounds_completed == 0:
            self.start_initial_round()
        else:
            if self.is_progression_paused:
                self.show_progression_menu()
            else:
                self.show_progression_menu()

    def start_new_round(self):
        self.start_initial_round()

    def start_initial_round(self):
        self.is_progression_paused = False
        self.hide_menu_buttons()
        self.route_buttons.clear()

        if self.balls_left <= 0:
            area_key = self.game.story_manager.current_area_key
            trainer_pool = self.area_data.get("trainer_pool", [])

            available_indices = []
            for i in range(len(trainer_pool)):
                if not self.game.story_manager.is_trainer_defeated(area_key, i):
                    available_indices.append(i)

            if not available_indices:
                self.show_dialogue(
                    [
                        self.game.assets.get_text("no_balls_left"),
                        self.game.assets.get_text("route_safe"),
                    ],
                    callback=self.show_progression_menu,
                )
            else:
                idx = available_indices[0]
                self.trigger_trainer_battle(specific_index=idx)
            return

        trainer_rate = self.area_data.get("trainer_encounter_rate", 0)
        if (
            self.area_data.get("area_type") == "wild_route"
            and random.random() < trainer_rate
        ):
            self.pending_wild_encounters = 0
            self.initial_round_active = False
            self.show_dialogue(
                [self.game.assets.get_text("trainer_spotted")],
                callback=self.trigger_trainer_battle,
            )
        else:
            self.initial_round_active = False
            self.show_progression_menu()

    def trigger_trainer_battle(self, specific_index=None):
        trainer_pool = self.area_data.get("trainer_pool", [])
        if not trainer_pool:
            self.trigger_wild_encounter()
            return

        area_key = self.game.story_manager.current_area_key

        if specific_index is not None:
            trainer_idx = specific_index
        else:
            available = [
                i
                for i in range(len(trainer_pool))
                if not self.game.story_manager.is_trainer_defeated(area_key, i)
            ]
            if not available:
                self.trigger_wild_encounter()
                return
            trainer_idx = available[0]

        trainer_info = trainer_pool[trainer_idx]
        trainer_class = trainer_info.get("class", "YOUNGSTER")
        trainer_name = trainer_info.get("name")
        custom_dialogue = trainer_info.get("dialogue")
        rewards = trainer_info.get("rewards")
        victory_flag = trainer_info.get("victory_flag")

        area_key = self.game.story_manager.current_area_key
        battle_type = self.area_data.get("battle_type", "field")

        self.play_state_data = {}

        opponent_ids = []

        num_pokemon = 2
        if "team_range" in trainer_info:
            rng = trainer_info["team_range"]
            if isinstance(rng, list) and len(rng) >= 2:
                num_pokemon = random.randint(rng[0], rng[1])

        team_override = trainer_info.get("team")
        if team_override and isinstance(team_override, list) and len(team_override) > 0:
            if isinstance(team_override[0], list):
                opponent_ids = random.choice(team_override)
            else:
                opponent_ids = team_override

        elif trainer_class == "ROCKET":
            rocket_pool = self.game.loader.area_data.get("TEAM_ROCKET_POOL", [])
            if rocket_pool:
                for _ in range(num_pokemon):
                    opponent_ids.append(random.choice(rocket_pool))

        if not opponent_ids:
            pool_name = self.area_data.get("wild_pool_percentages")
            wild_pool_pct = (
                self.game.loader.area_data.get(pool_name, {}) if pool_name else {}
            )

            if wild_pool_pct:
                keys = list(wild_pool_pct.keys())
                for _ in range(num_pokemon):
                    opponent_ids.append(int(random.choice(keys)))
            else:
                self.trigger_wild_encounter()
                return

        opponent_team = []
        for opp_id in opponent_ids:
            raw = self.game.loader.fetch_specific(opp_id)
            opponent_team.append(Pokemon(raw, self.game.assets, size_mult=3.125))
            
        from src.states.battle import TrainerBattleState, TrainerIntroState

        trainer_sprite = self.game.assets.get_trainer_image(trainer_info["sprite"])
        battle_state = TrainerBattleState(
            self.game,
            opponent_team,
            trainer_sprite=trainer_sprite,
            trainer_class=trainer_class,
            trainer_index=trainer_idx,
            trainer_name=trainer_name,
            custom_dialogue=custom_dialogue,
            rewards=rewards,
            battle_type=battle_type,
            area_name=area_key,
            victory_flag=victory_flag,
        )

        battle_state.play_state_data = {
            "balls_left": self.balls_left,
            "current_streak": self.current_streak,
            "rounds_completed": self.rounds_completed,
            "pending_wild_encounters": self.pending_wild_encounters,
            "initial_round_active": self.initial_round_active,
        }

        all_dialogue = self.game.loader.area_data.get("TRAINER_CLASS_DIALOGUE", {})
        intro_text_options = all_dialogue.get(trainer_class, {}).get("intro", ["Prepare to battle!"])
        if custom_dialogue and "intro" in custom_dialogue:
            intro_text_options = custom_dialogue["intro"]
        intro_text = random.choice(intro_text_options)

        intro_state = TrainerIntroState(
            self.game, trainer_sprite, intro_text, battle_state
        )
        self.game.change_state(intro_state)

    def trigger_wild_encounter(self):
        pool_name = self.area_data.get("wild_pool_percentages")
        wild_pool_pct = self.game.loader.area_data.get(pool_name, {})
        if not wild_pool_pct:
            print(
                f"Warning: No wild Pokémon defined for area {self.game.story_manager.current_area_key}"
            )
            self.p_data = [None, None, None]
            self.problem_str, self.correct_ans, self.options = (
                "...",
                "...",
                ["...", "...", "..."],
            )
            return
        
        p_list = []
        for _ in range(3):
            p_id_str = Utils.weighted_random_choice(wild_pool_pct)
            p_id = int(p_id_str)
            p_raw = self.game.loader._fetch_raw(
                id_pool=[p_id], area_data=self.area_data
            )
            p_list.append(p_raw)
        
        self.current_raw = {"normal": p_list}
        self.p_data = [
            Pokemon(p, self.game.assets, size_mult=3.125) if p["id"] != 0 else None for p in p_list
        ]
        
        for p in self.p_data:
            if p:
                self.game.data.mark_seen(p.id)

        self.question_timer = 30 * FPS
        self.problem_str, self.correct_ans, self.options = self.generate_math_set(
            self.total_caught, num_options=3
        )

        self.idle_sparkles = []
        for i, p in enumerate(self.p_data):
            if p and p.is_shiny:
                self.idle_sparkles.append((IdleSparkle(0, 0), i))
                self.starbursts.append(ShinyBurst(self.get_cx(i), self.sprite_y))
                if self.game.assets.shiny_sfx:
                    self.game.assets.shiny_sfx.play()

    def create_checkpoint(self):
        self.game.story_manager.set_checkpoint(
            PlayState,
            total_caught=self.total_caught,
            balls_left=self.balls_left,
            current_streak=self.current_streak,
        )
        # Sync back to story manager to be safe
        self.game.story_manager.balls_left = self.balls_left
        self.game.story_manager.current_streak = self.current_streak

    def generate_math_set(self, score_unused=0, num_options=3):
        streak = self.current_streak
        badges = len(self.game.story_manager.badges)
        
        # Default Scaling (0-1 Badges or fallback)
        sum_limit, sub_digit_limit = 12, 15
        min_sum = 4
        use_badge_scaling = False

        # Determine Difficulty Tier based on Badges
        tier = 0
        if badges >= 6: tier = 3
        elif badges >= 4: tier = 2
        elif badges >= 2: tier = 1

        if tier > 0:
            # 2/3 chance for Harder Math, 1/3 for Lower Difficulty (streak-based)
            if random.random() < 0.66:
                use_badge_scaling = True
                if tier == 1: # 2+ Badges: Sums/Diffs 20-30, Digits <= 40
                    sum_limit, sub_digit_limit, min_sum = 30, 40, 20
                elif tier == 2: # 4+ Badges: Sums/Diffs 30-40, Digits <= 50
                    sum_limit, sub_digit_limit, min_sum = 40, 50, 30
                elif tier == 3: # 6+ Badges: Sums/Diffs 40-50, Digits <= 60
                    sum_limit, sub_digit_limit, min_sum = 50, 60, 40

        if not use_badge_scaling:
            # Standard Streak Scaling for lower difficulty / early game
            if streak <= 5: sum_limit, sub_digit_limit = 12, 15
            elif streak <= 15: sum_limit, sub_digit_limit = 20, 20
            elif streak <= 25: sum_limit, sub_digit_limit = 25, 25
            else: sum_limit, sub_digit_limit = streak + 5, streak + 5

        p_type = random.choice([1, 2, 3])
        op = random.choice(["+", "-"])

        if op == "+":
            # Sum Limit logic handling min_sum for Badge Scaling
            effective_min = min_sum if use_badge_scaling else 4
            c = random.randint(effective_min, sum_limit)
            
            # Ensure a and b don't exceed sub_digit_limit
            # If c is 30, and limit is 40, a=29 b=1 is fine.
            # If c is 70 (high streak) and limit 50, we might clamp.
            a = random.randint(2, c - 2)
            b = c - a
        else:
            # For Subtraction: a - b = c
            # Badge Scaling: Result (c) should be between min_sum and sum_limit?
            # Request: "Sums and differences between 20 and 30" -> Result is 20-30.
            if use_badge_scaling:
                c = random.randint(min_sum, sum_limit) # Result
                # "Individual digits no larger than X" (sub_digit_limit)
                # a - b = c  =>  a = c + b
                # We need a <= sub_digit_limit
                # So c + b <= sub_digit_limit  =>  b <= sub_digit_limit - c
                max_b = sub_digit_limit - c
                if max_b < 2: max_b = 2 # Safety
                b = random.randint(2, max_b)
                a = c + b
            else:
                # Old logic
                a = random.randint(4, sub_digit_limit)
                b = random.randint(2, a - 2)
                c = a - b
            c = a - b

        if p_type == 1:
            problem_str = f"{a} {op} {b} = ?"
            ans = c
            opts = {c}
            while len(opts) < num_options:
                offset = random.choice([-3, -2, -1, 1, 2, 3])
                f = c + offset
                if f >= 0 and f not in opts:
                    opts.add(f)
            options = sorted(list(opts), key=lambda x: random.random())

        elif p_type == 2:
            if random.random() < 0.5:
                problem_str = f"? {op} {b} = {c}"
                ans = a
            else:
                problem_str = f"{a} {op} ? = {c}"
                ans = b
            opts = {ans}
            while len(opts) < num_options:
                offset = random.choice([-3, -2, -1, 1, 2, 3])
                f = ans + offset
                if f >= 2 and f not in opts:
                    opts.add(f)
            options = sorted(list(opts), key=lambda x: random.random())

        else:
            problem_str = f"{c} = ?"
            ans = f"{a} {op} {b}"
            options = [ans]
            while len(options) < num_options:
                mod_a, mod_b = a, b
                mod_op = op
                change_type = random.randint(1, 3)
                offset = random.choice([-2, -1, 1, 2])
                if change_type == 1:
                    mod_a += offset
                elif change_type == 2:
                    mod_b += offset
                else:
                    mod_op = "-" if op == "+" else "+"
                if mod_a < 2 or mod_b < 2:
                    continue
                if mod_op == "-" and mod_a <= mod_b:
                    continue
                if change_type == 3:
                    if (mod_op == "+" and (mod_a + mod_b) == c) or (
                        mod_op == "-" and (mod_a - mod_b) == c
                    ):
                        continue
                w_eq = f"{mod_a} {mod_op} {mod_b}"
                if w_eq not in options:
                    options.append(w_eq)
            random.shuffle(options)

        return problem_str, ans, options

    def get_cx(self, i):
        if self.game.assets.is_pc:
            return self.game.width // 2 + (i - 1) * (
                self.game.width // 4
            )
        return (i * self.game.width // 3) + (self.game.width // 6)

    def handle_events(self, events):
        if self.boss_prompt_active:
            return

        if self.is_progression_paused:
            return

        for event in events:
            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and not self.ball_active and self.input_delay == 0
                and self.pause_timer == 0
                and self.balls_left > 0
            ):
                self.check_answer(event.pos)

    def _apply_volume_to_mixers(self):
        pygame.mixer.music.set_volume(VOLUME)
        if self.game.assets.shiny_sfx:
            self.game.assets.shiny_sfx.set_volume(VOLUME)
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.set_volume(VOLUME)
        for p in self.p_data:
            if p:
                p.set_volume(VOLUME)

    def show_progression_menu(self):
        self.is_progression_paused = True
        self.dialogue_box.visible = False

        area_key = self.game.story_manager.current_area_key
        # Pre-calc checks for conditions
        trainer_pool = self.area_data.get("trainer_pool", [])
        trainers_left = any(
            not self.game.story_manager.is_trainer_defeated(area_key, i)
            for i in range(len(trainer_pool))
        )

        # Default menu if not in JSON (backward compatibility)
        default_menu = [
            { "text": "CATCH WILD PKMN", "action": "CATCH", "condition": "has_balls", "color": "BLUE" },
            { "text": "LOOK FOR TRAINER", "action": "TRAINER", "condition": "has_trainers", "color": "BLUE" },
            { "text": "BATTLE WILD PKMN", "action": "BATTLE", "condition": "has_balls", "color": "GREEN" },
            { "text": "EXIT ROUTE", "action": "EXIT", "condition": "can_exit", "color": "RED" }
        ]
        
        menu_config = self.area_data.get("route_menu", default_menu)

        # Clear old buttons from UI
        for btn in self.route_buttons:
            if btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)
        self.route_buttons.clear()

        # Build new buttons
        valid_options = []
        for item in menu_config:
            condition = item.get("condition")
            action = item.get("action")

            # Special exemption: BATTLE is always available (skips catch prompt if 0 balls)
            if action == "BATTLE":
                valid_options.append(item)
                continue

            # If condition is has_balls and fails, show as disabled (Grey)
            if condition in ["has_balls", "has_trainers"] and not self._check_route_condition(condition, trainers_left, item):
                item_copy = item.copy()
                item_copy["disabled"] = True
                item_copy["color"] = "GRAY"
                valid_options.append(item_copy)
            elif self._check_route_condition(condition, trainers_left, item):
                valid_options.append(item)

        if not valid_options:
            # Safety fallback if stuck
            if self.rounds_completed >= self.min_rounds or not trainers_left:
                 valid_options.append({ "text": "EXIT ROUTE", "action": "EXIT", "color": "RED" })

        # --- REBUILT LAYOUT LOGIC (FIXED GRID) ---
        # Using fixed autosize=False buttons to guarantee alignment
        btn_w, btn_h = 280, 80 
        gap_x, gap_y = 60, 40
        cols = 3
        
        count = len(valid_options)
        rows = (count + cols - 1) // cols
        
        # Base layout on the Dialogue Box top to prevent overlap
        box_top = Utils.get_full_dialogue_rect(self.game).top
        
        total_h = rows * btn_h + (rows - 1) * gap_y
        start_y = box_top - total_h - 30
        center_x = self.game.width // 2

        for i, item in enumerate(valid_options):
            row = i // cols
            col = i % cols
            
            # Calculate how many items are in THIS specific row to center it perfectly
            items_in_this_row = min(cols, count - row * cols)
            row_width = items_in_this_row * btn_w + (items_in_this_row - 1) * gap_x
            row_start_x = center_x - row_width // 2
            
            x = row_start_x + col * (btn_w + gap_x)
            y = start_y + row * (btn_h + gap_y)
            
            color_map = {
                "BLUE": BLUE, "GREEN": GREEN, "RED": RED, "ORANGE": ORANGE, 
                "GOLD": GOLD, "PURPLE": PURPLE, "GRAY": GRAY, "CYAN": (0, 255, 255)
            }
            bg_color = color_map.get(item.get("color", "BLUE"), BLUE)

            callback = self._get_route_callback(item)
            if item.get("disabled"):
                callback = None
            
            # [IMPORTANT] autosize=False prevents text length from breaking the grid spacing
            btn = Button(
                pygame.Rect(x, y, btn_w, btn_h), 
                item["text"], 
                self.game.assets.fonts["tiny"], 
                callback, 
                bg_color=bg_color, 
                autosize=False
            )
            self.route_buttons.append(btn)
            self.game.ui_manager.add_element(btn)
            
        self.input_delay = 20

    def _check_route_condition(self, condition, trainers_left, item=None):
        if not condition: return True
        if condition == "has_balls": return self.balls_left > 0
        if condition == "has_trainers": return trainers_left
        if condition == "can_headbutt":
            has_helmet = self.game.story_manager.inventory.get("ROCKY_HELMET", 0) > 0
            return has_helmet and self.area_data.get("has_trees", False)
        if condition == "can_fish":
            has_rod = self.game.story_manager.inventory.get("OLD_ROD", 0) > 0
            return has_rod and self.area_data.get("can_fish", False)
        if condition == "can_exit":
            # Can exit if min rounds met OR no balls left (safety) OR no trainers left
            return self.rounds_completed >= self.min_rounds or self.balls_left <= 0 or not trainers_left
        if condition == "no_trainers":
            return not trainers_left
        if condition == "boss_defeated":
            # Check if specific area boss flag is set
            return self.game.story_manager.story_flags.get(f"{self.game.story_manager.current_area_key}_boss_defeated", False)
        if condition == "boss_available":
            return not self._check_route_condition("boss_defeated", trainers_left) and trainers_left is False
        if condition == "has_silph_scope":
            return self.game.story_manager.inventory.get("SILPH_SCOPE", 0) > 0
        if condition == "has_8_badges":
            return len(self.game.story_manager.badges) >= 8
        if condition == "dungeon_cleared":
            if not item: return False
            areas = item.get("required_areas", [])
            for area in areas:
                # Check if area exists in data
                a_data = self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(area)
                if not a_data: continue
                
                # Check all trainers in that area
                t_pool = a_data.get("trainer_pool", [])
                for i in range(len(t_pool)):
                    if not self.game.story_manager.is_trainer_defeated(area, i):
                        return False
            return True
        if condition == "dungeon_boss_available":
            # Must not have beaten boss yet AND must have cleared specific dungeon areas
            return not self._check_route_condition("boss_defeated", trainers_left) and self._check_route_condition("dungeon_cleared", trainers_left, item)
        return True

    def _get_route_callback(self, item):
        action = item.get("action")
        if action == "CATCH": return self.action_search_pokemon
        if action == "TRAINER": return self.action_search_trainer
        if action == "BATTLE": return self.action_battle_wild
        if action == "BOSS": return self.action_challenge_boss
        if action == "HEADBUTT": return self.action_headbutt
        if action == "FISH": return self.action_fish
        if action == "EXIT": 
            target = item.get("target")
            # Return a lambda that calls exit with the specific target if provided
            return lambda: self.action_exit_route(target)
        return lambda: print(f"Unknown action: {action}")

    def hide_menu_buttons(self):
        for btn in self.route_buttons:
            if btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)
        self.route_buttons.clear()

    def check_for_evolution(self, species_id, force_catch_evo=False):
        # 1. Check Party
        if self._scan_list_for_evolution(self.game.story_manager.player_team, species_id, force_catch_evo, "party", target_form=None):
            return True
        
        # 2. Check PC (only if triggered by catch to avoid weird background evos during battle)
        if force_catch_evo:
            if self._scan_list_for_evolution(self.game.story_manager.pc_pokemon, species_id, force_catch_evo, "pc", target_form=None):
                return True
                
        return False

    def _scan_list_for_evolution(self, pokemon_list, species_id, force_catch_evo, context, target_form=None):
        """Helper to scan a specific list (party or pc) for evolution candidates."""
        for i, poke in enumerate(pokemon_list):
            if poke.id != species_id:
                continue
            
            if target_form and poke.form != target_form:
                continue

            # Track 1: Battle Wins (20 wins)
            # Track 2: Catch Count (5 catches) - passed via force_catch_evo
            # Note: Battle wins reset to 0 after evolution, so >= 20 is the threshold for the NEXT stage.
            
            requirements_met = False
            if force_catch_evo:
                requirements_met = True
            elif poke.wins >= 20:
                requirements_met = True
                
            if not requirements_met:
                continue

            key = poke.name.upper()
            if poke.form and poke.form != "normal":
                key += f"_{poke.form.upper()}"

            # Robust lookup: Try UPPERCASE then Title Case
            next_entries = None
            if key in self.game.loader.evolution_map:
                next_entries = self.game.loader.evolution_map[key]
            elif key.title() in self.game.loader.evolution_map:
                next_entries = self.game.loader.evolution_map[key.title()]

            # Check for Item Locks (Stones, Metal Coat, etc.)
            item_locks = self.game.loader.evolution_map.get("ITEM_LOCKS", [])
            if key in item_locks:
                continue

            if next_entries:
                next_entry = next_entries[0]  # first branch only for now
                
                if "_" in next_entry:
                        base_name, form_part = next_entry.rsplit("_", 1)
                        next_form = form_part.upper()
                else:
                        base_name = next_entry
                        next_form = "normal"

                # Name lookup should also be robust
                next_id = self.game.name_to_id.get(base_name.upper())
                
                if next_id is not None:
                        from src.states.systems import EvolutionState
                        self.game.change_state(
                            EvolutionState(
                                self.game, poke, next_id, i, next_form=next_form, context=context,
                                return_state=self
                            )
                        )
                        return True
        return False

    def action_search_pokemon(self):
        self.is_progression_paused = False
        self.hide_menu_buttons()
        self.input_delay = 30
        self.pending_wild_encounters = 3
        self.trigger_wild_encounter()

    def action_headbutt(self):
        self.is_progression_paused = False
        self.hide_menu_buttons()
        
        pool_name = self.area_data.get("tree_pool")
        tree_pool_pct = self.game.loader.area_data.get(pool_name, {})
        
        if not tree_pool_pct:
            # Fallback if config missing
            tree_pool_pct = self.game.loader.area_data.get("KANTO_ROUTE_TREE_PERCENTAGES", {})

        if not tree_pool_pct:
            self.show_dialogue(["No Pokémon found in this tree."])
            self.show_progression_menu()
            return

        # Pick a tree encounter
        items = []
        for pid, pct in tree_pool_pct.items():
            items.append((int(pid), pct))
        
        # Simple weighted choice
        p_id_str = Utils.weighted_random_choice(tree_pool_pct)
        raw = self.game.loader.fetch_specific(int(p_id_str))
        pokemon = Pokemon(raw, self.game.assets, size_mult=3.125)

        from src.states.battle import WildBattleState
        battle_state = WildBattleState(
            self.game, pokemon, self.game.story_manager.current_area_key 
        )
        battle_state.play_state_data = {
            "balls_left": self.balls_left,
            "current_streak": self.current_streak,
            "rounds_completed": self.rounds_completed,
            "pending_wild_encounters": 0,
            "initial_round_active": False 
        }
        self.game.change_state(battle_state)

    def action_fish(self):
        self.is_progression_paused = False
        self.hide_menu_buttons()

        fishing_pool_pct = self.game.loader.area_data.get("OLD_ROD_POOL_PERCENTAGES", {})
        
        if not fishing_pool_pct:
            self.show_dialogue(["Not even a nibble..."])
            self.show_progression_menu()
            return

        # Hooked a Pokemon!
        p_id_str = Utils.weighted_random_choice(fishing_pool_pct)
        raw = self.game.loader.fetch_specific(int(p_id_str))
        pokemon = Pokemon(raw, self.game.assets, size_mult=3.125)
        
        self.show_dialogue(["Oh! A bite!"], callback=None)

        # [FIX] Use random ocean backgrounds correctly scaled
        bg_file = random.choice(["battle_ocean1.png", "battle_ocean2.png", "battle_ocean3.png"])

        from src.states.battle import WildBattleState
        battle_state = WildBattleState(
            self.game, pokemon, self.game.story_manager.current_area_key,
            background_image=bg_file
        )
        battle_state.play_state_data = {
            "balls_left": self.balls_left,
            "current_streak": self.current_streak,
            "rounds_completed": self.rounds_completed,
            "pending_wild_encounters": 0,
            "initial_round_active": False 
        }
        self.game.change_state(battle_state)

    def action_challenge_boss(self):
        self.is_progression_paused = False
        self.hide_menu_buttons()
        
        boss_data = self.area_data.get("area_boss", {})
        if not boss_data:
            self.show_progression_menu()
            return
            
        pid = boss_data.get("id")
        raw = self.game.loader.fetch_specific(pid)

        # Override name if provided in boss_data (e.g. "Marowak (Ghost)")
        if "name" in boss_data:
            raw["name"] = boss_data["name"]
            raw["display_name"] = boss_data["name"]

        pokemon = Pokemon(raw, self.game.assets, size_mult=2.0)
        
        # Use current area key to generate a unique flag for this boss
        flag_name = f"{self.game.story_manager.current_area_key}_boss_defeated"
        
        from src.states.battle import WildBattleState
        battle_state = WildBattleState(self.game, pokemon, self.game.story_manager.current_area_key)
        battle_state.victory_flag = flag_name
        battle_state.play_state_data = {
            "balls_left": self.balls_left,
            "current_streak": self.current_streak,
            "rounds_completed": self.rounds_completed,
            "pending_wild_encounters": 0,
            "initial_round_active": False 
        }
        self.game.change_state(battle_state)

    def action_flee(self):
        if (
            self.pause_timer > 0
            or self.ball_active
            or self.is_progression_paused
            or self.boss_manager.in_boss_mode
        ):
            return

        self.show_dialogue(["Got away safely!"])
        self.pause_timer = 40
        self.flee_active = True
        self.caught_idx = 1

    def action_search_trainer(self):
        self.is_progression_paused = False
        self.hide_menu_buttons()
        self.input_delay = 20

        self.pending_wild_encounters = 0
        self.trigger_trainer_battle()

        self.rounds_completed += 1

    def action_battle_wild(self):
        self.is_progression_paused = False
        self.hide_menu_buttons()

        pool_name = self.area_data.get("wild_pool_percentages")
        wild_pool_pct = self.game.loader.area_data.get(pool_name, {})
        if not wild_pool_pct:
            self.show_dialogue(["No wild Pokémon here!"])
            self.show_progression_menu()
            return

        items = []
        for pid, pct in wild_pool_pct.items():
            items.append((int(pid), pct))

        items.sort(key=lambda x: x[1])

        candidates = items[:4]

        chosen = random.choice(candidates)
        chosen_id = chosen[0] 

        raw = self.game.loader.fetch_specific(chosen_id)
        pokemon = Pokemon(raw, self.game.assets, size_mult=3.125)

        battle_state = WildBattleState(
            self.game, pokemon, self.game.story_manager.current_area_key 
        )
        battle_state.play_state_data = {
            "balls_left": self.balls_left,
            "current_streak": self.current_streak,
            "rounds_completed": self.rounds_completed,
            "pending_wild_encounters": 0,
            "initial_round_active": False 
        }
        self.game.change_state(battle_state)

    def action_exit_route(self, target_area=None):
        self.wild_catches_on_route = 0
        if target_area:
            next_area_key = target_area
        else:
            next_area_key = self.game.story_manager.get_current_area_data().get("next_area")
            
        if next_area_key:
            self.game.change_state(AreaTransitionState(self.game, next_area_key))

    def check_answer(self, pos):
        for i, btn_rect in enumerate(self.answer_btn_rects):
            if i >= len(self.p_data) or self.p_data[i] is None:
                continue

            if btn_rect.width > 0 and btn_rect.collidepoint(pos):
                self.balls_left -= 1
                self.current_ball_img = random.choice(self.game.assets.ball_imgs)
                pi = (
                    self.boss_manager.boss_pokemon_data
                    if self.boss_manager.in_boss_mode
                    else self.p_data[i]
                )
                if pi is None:
                    return
                is_shiny_catch = (
                    not self.boss_manager.in_boss_mode and pi and pi.is_shiny
                )
                is_correct_answer = self.options[i] == self.correct_ans

                self.was_shiny_override = is_shiny_catch and not is_correct_answer

                if is_correct_answer or is_shiny_catch:
                    self.handle_correct(i, pi, is_shiny_catch, btn_rect.centerx)
                else:
                    self.handle_wrong(i, pi)
                return

    def handle_correct(self, idx, pi, is_shiny_catch, target_x):
        if self.boss_manager.in_boss_mode:
            self.boss_manager.boss_hits += 1
            self.feedback_text = (
                self.game.assets.get_text("direct_hit")
                if self.boss_manager.boss_hits == 1
                else self.game.assets.get_text("critical_hit")
            )
            self.feedback_color = GOLD if self.boss_manager.boss_hits == 1 else GOLD
            self.ball_active = True
            self.ball_pos = [self.game.width // 2, self.game.height]
            self.ball_target = [self.game.width // 2, self.sprite_y]
            self.caught_idx = 1
        else:
            self.feedback_color = GOLD if pi.is_shiny else GREEN
            self.ball_active = True
            self.ball_pos = [self.game.width // 2, self.game.height]
            self.ball_target = [target_x, self.sprite_y]
            self.caught_idx = idx

    def boss_catch_yes(self):
        self.boss_prompt_active = False
        self.btn_yes.set_visibility(False)
        self.btn_no.set_visibility(False)
        self.dialogue_box.visible = False
        self.complete_catch(self.caught_idx)

    def boss_catch_no(self):
        self.boss_prompt_active = False
        self.btn_yes.set_visibility(False)
        self.btn_no.set_visibility(False)
        self.dialogue_box.visible = False
        self.reset_round()

    def show_boss_catch_prompt(self):
        self.boss_prompt_active = True
        boss_name = self.boss_manager.boss_pokemon_data.name
        self.show_dialogue([f"You defeated {boss_name}!", "Catch it?"])
        
        box = self.dialogue_box.rect
        btn_w, btn_h = 120, 60
        self.btn_yes.rect = pygame.Rect(box.right - 280, box.bottom - 80, btn_w, btn_h)
        self.btn_no.rect = pygame.Rect(box.right - 140, box.bottom - 80, btn_w, btn_h)
        self.btn_yes.set_visibility(True)
        self.btn_no.set_visibility(True)

    def handle_wrong(self, idx, pi):
        self.current_streak = 0
        self.game.loader.shiny_charm_active = False
        if self.boss_manager.in_boss_mode:
            if pi and pi.cry:
                pi.cry.play()

            moves_data = self.game.assets.movesets.get(str(pi.id), {})
            moves = moves_data.get("moves", [])
            exclude_names = {
                "self-destruct",
                "explosion",
                "fissure",
                "guillotine",
                "horn drill",
                "sheer cold",
            }
            valid_moves = []
            for move in moves:
                m_lower = move.get("name", "").lower()
                power = move.get("power", 0)
                if m_lower not in exclude_names and power > 0:
                    valid_moves.append((power, move["name"]))
            if valid_moves:
                valid_moves.sort(key=lambda x: x[0], reverse=True)
                top5 = valid_moves[:5]
                _, strong_move = random.choice(top5)
                self.show_dialogue(
                    [
                        self.game.assets.get_text(
                            "used_move",
                            name=pi.display_name.upper(),
                            move=strong_move.upper(),
                        )
                    ]
                )
            else:
                self.feedback_text = self.game.assets.get_text(
                    "attacked", name=pi.display_name.upper()
                )

            self.shake_amount = 40
            self.pause_timer = 45
            self.ball_active = True
            self.ball_pos = [self.game.width // 2, self.game.height]
            self.ball_target = [self.game.width // 2, self.sprite_y]
            self.caught_idx = 1
            self.scr_shake_timer = 20
        else:
            self.show_dialogue([self.game.assets.get_text("fled")])
            self.pause_timer = 40
            self.flee_active = True
            self.caught_idx = idx
            self.ball_active = True
            self.ball_pos = [self.game.width // 2, self.game.height]
            self.ball_target = [self.get_cx(idx), self.sprite_y]

    def handle_timeout(self):
        self.balls_left -= 1
        self.current_streak = 0
        self.game.loader.shiny_charm_active = False

        if self.boss_manager.in_boss_mode:
            pi = (self.boss_manager.boss_pokemon_data if self.boss_manager.boss_pokemon_data else None)
            if pi and pi.cry:
                pi.cry.play()

            moves_data = self.game.assets.movesets.get(str(pi.id), {})
            moves = moves_data.get("moves", [])
            exclude_names = {
                "self-destruct",
                "explosion",
                "fissure",
                "guillotine",
                "horn drill",
                "sheer cold",
            }
            valid_moves = []
            for move in moves:
                m_lower = move.get("name", "").lower()
                power = move.get("power", 0)
                if m_lower not in exclude_names and power > 0:
                    valid_moves.append((power, move["name"]))
            if valid_moves:
                valid_moves.sort(key=lambda x: x[0], reverse=True)
                top5 = valid_moves[:5]
                _, strong_move = random.choice(top5)
                self.show_dialogue(
                    [
                        self.game.assets.get_text(
                            "used_move",
                            name=pi.display_name.upper(),
                            move=strong_move.upper(),
                        )
                    ]
                )
            else:
                self.feedback_text = self.game.assets.get_text(
                    "attacked", name=pi.display_name.upper()
                )

            self.shake_amount = 40
            self.pause_timer = 45
            self.ball_active = True
            self.ball_pos = [self.game.width // 2, self.game.height]
            self.ball_target = [self.game.width // 2, self.sprite_y]
            self.caught_idx = 1
            self.scr_shake_timer = 20
        else:
            self.show_dialogue([self.game.assets.get_text("got_away")])
            self.pause_timer = 40
            self.flee_active = True
            self.caught_idx = 1
            self.ball_active = True
            self.ball_pos = [self.game.width // 2, self.game.height]
            self.ball_target = [self.get_cx(1), self.sprite_y]

    def update(self):
        self.boss_manager.update()

        if self.boss_prompt_active:
            self.dialogue_box.update()
            return

        if self.input_delay > 0:
            self.input_delay -= 1

        if self.dialogue_box.visible:
            self.dialogue_box.update()

        show_flee = (
            not self.is_progression_paused
            and not self.boss_manager.in_boss_mode
            and self.pause_timer == 0
            and not self.ball_active
        )
        self.btn_flee.set_visibility(show_flee)

        if self.is_progression_paused:
            return

        if self.balls_left <= 0 and not self.ball_active and self.pause_timer == 0:
            if self.boss_manager.in_boss_mode:
                self.show_dialogue(
                    [
                        self.game.assets.get_text("no_balls_left"),
                        self.game.assets.get_text("fled"),
                    ],
                    callback=self.show_progression_menu,
                )
                self.boss_manager.in_boss_mode = False

            if self.pending_wild_encounters > 0:
                self.pending_wild_encounters = 0
                self.show_dialogue(
                    [self.game.assets.get_text("no_balls_left")],
                    callback=self.show_progression_menu,
                )
                return

            self.check_team_hp()
            return

        if self.flash_timer > 0:
            self.flash_timer -= 1

        if self.boss_manager.boss_intro_timer > 0:
            return

        if self.pause_timer == 0 and not self.ball_active:
            self.question_timer -= 1
            if self.question_timer <= 0:
                self.handle_timeout()

        if self.ball_active:
            self.ball_pos[0] += (self.ball_target[0] - self.ball_pos[0]) * 0.25
            self.ball_pos[1] += (self.ball_target[1] - self.ball_pos[1]) * 0.25
            if abs(self.ball_pos[1] - self.ball_target[1]) < 10:
                self.ball_active = False
                self.pause_timer = 35
                self.resolve_catch()

        if self.pause_timer > 0:
            self.pause_timer -= 1
            if self.pause_timer == 1:
                self.reset_round()

        for sb in self.starbursts:
            sb.update()
        if self.pause_timer == 0 and not self.ball_active:
            for sparkle, idx in self.idle_sparkles:
                cx = self.get_cx(idx)
                sparkle.update(
                    cx + (random.randint(-15, 15) if self.scr_shake_timer > 0 else 0),
                    self.sprite_y - (self.game.width * 0.15),
                )

    def check_team_hp(self):
        if not any(
            pokemon.get_stat("HP") > 0
            for pokemon in self.game.story_manager.player_team
        ):
            from src.states.systems import GameOverState
            self.game.change_state(GameOverState(self.game))
            return

    def resolve_catch(self):
        if not self.flee_active:
            if 0 <= self.caught_idx < len(self.p_data) and self.p_data[self.caught_idx]:

                if self.p_data[self.caught_idx].cry:
                    self.p_data[self.caught_idx].cry.play()

        # ───────────────────────────────────────────────
        # Boss mode handling
        # ───────────────────────────────────────────────
        if self.boss_manager.in_boss_mode:

            if self.feedback_text in (
                self.game.assets.get_text("direct_hit"),
                self.game.assets.get_text("critical_hit"),
            ):
                self.boss_manager.boss_hp -= 1

                if self.boss_manager.boss_hp <= 0:
                    self.show_boss_catch_prompt()
                else:
                    self.problem_str, self.correct_ans, self.options = (
                        self.generate_math_set(self.total_caught)
                    )
                    self.question_timer = 30 * FPS

            else:
                self.problem_str, self.correct_ans, self.options = (
                    self.generate_math_set(self.total_caught)
                )
                self.question_timer = 30 * FPS

        elif not self.flee_active:
            self.complete_catch(self.caught_idx)

    def complete_catch(self, idx):
        pokemon_caught = self.p_data[idx]
        pokemon_was_kept = False

        all_owned = self.game.story_manager.player_team + self.game.story_manager.pc_pokemon
        is_duplicate_owned = any(p.id == pokemon_caught.id and p.form == pokemon_caught.form for p in all_owned)
        is_party_full = len(self.game.story_manager.player_team) >= 6

        if is_duplicate_owned:
            self.show_dialogue(["Gained evolution XP!"])
            pokemon_was_kept = False
        else:
            pokemon_was_kept = True
            if not is_party_full:
                self.game.story_manager.player_team.append(pokemon_caught)
                if self.was_shiny_override:
                    self.show_dialogue([self.game.assets.get_text("shiny_pass")])
                else:
                    self.show_dialogue([self.game.assets.get_text("caught_pokemon", name=pokemon_caught.display_name.upper())])
            else:
                self.game.story_manager.pc_pokemon.append(pokemon_caught)
                self.show_dialogue(["Party is full.", f"{pokemon_caught.display_name.upper()} was sent to BILL'S PC!"])

        # --- Common logic for any successful catch ---
        
        species_id = pokemon_caught.id
        if is_duplicate_owned:
            species_id = pokemon_caught.id

            self.game.story_manager.catch_counts[species_id] = self.game.story_manager.catch_counts.get(species_id, 0) + 1
            
            threshold = 5

            if self.game.story_manager.catch_counts[species_id] % threshold == 0:
                 self.check_for_evolution(species_id, force_catch_evo=True)
        elif pokemon_was_kept:
            self.game.story_manager.catch_counts[species_id] = self.game.story_manager.catch_counts.get(species_id, 0) + 1

        # ───────────────────────────────────────────────
        # COMMON LOGIC FOR ANY SUCCESSFUL CATCH 
        # ───────────────────────────────────────────────
        self.total_caught += 1
        self.game.loader.total_caught = self.total_caught
        self.current_streak += 1

        if self.boss_manager.in_boss_mode:
            self.boss_catches += 1
            self.game.data.add_defeated_boss(pokemon_caught)
        else:
            self.since_last_boss += 1

        if self.current_streak > 0 and self.current_streak % 5 == 0:
            self.balls_left += 1
            self.flash_msg = self.game.assets.get_text("plus_one_ball")
            self.flash_timer = 60

        if pokemon_was_kept:
            self.game.data.add_pokemon(pokemon_caught)
            self.game.update_save_data()
        if self.total_caught > self.game.data.get_high_score():
            self.game.data.set_high_score(self.total_caught)

        if pokemon_caught.is_shiny:
            self.game.data.add_shiny()
            self.starbursts.append(ShinyBurst(self.ball_target[0], self.ball_target[1]))
            if self.game.assets.shiny_sfx:
                self.game.assets.shiny_sfx.play()
        else:
            if not self.boss_manager.in_boss_mode:
                self.starbursts.append(
                    Starburst(self.ball_target[0], self.ball_target[1], WHITE)
                )

        self.game.data.save()
        self.pause_timer = 90 if self.boss_manager.in_boss_mode else 40

    def reset_round(self):
        self.starbursts, self.idle_sparkles, self.scr_shake_timer, self.shake_amount = (
            [],
            [],
            0,
            0,
        )
        (
            self.feedback_text,
            self.caught_idx,
            self.flee_active,
            self.runaway_x_offsets,
        ) = ("", -1, False, [0, 0, 0])
        self.dialogue_box.visible = (
            False
        )

        if self.boss_manager.in_boss_mode and self.boss_manager.boss_hp <= 0:
            self.boss_manager.in_boss_mode = False
            self.boss_manager.boss_pokemon_data = None
            pygame.event.clear()

        if self.pending_wild_encounters > 0:
            self.pending_wild_encounters -= 1

            if self.pending_wild_encounters <= 0:
                if self.initial_round_active:
                    self.initial_round_active = False

                self.rounds_completed += 1
                self.show_progression_menu()
                return
            else:
                self.trigger_wild_encounter()
                return

        self.show_progression_menu()

    def draw(self):
        screen = self.game.screen
        width, height = self.game.width, self.game.height
        offset_x, offset_y = 0, 0
        if self.scr_shake_timer > 0:
            offset_x, offset_y = random.randint(-15, 15), random.randint(-15, 15)

        # Pre-calculate caught IDs for the frame (Efficient lookup)
        caught_ids = {v['id'] for v in self.game.data.data.get("pokedex", {}).values()}

        if self.boss_manager.draw(screen, width, height, offset_x, offset_y):
            return

        if not self.boss_manager.in_boss_mode:
            screen.fill(BLACK)

            warp_speed = 15 if self.ball_active else 1
            spd_base = (
                10
                if (
                    self.pause_timer > 0 and (self.flee_active or self.caught_idx != -1)
                )
                else 1
            )
            for s in self.stars:
                s[1] += s[2] * spd_base * warp_speed
                if s[1] > height:
                    s[1], s[0] = 0, random.randint(0, width)
                pygame.draw.circle(
                    screen, (150, 150, 150), (s[0] + offset_x, s[1] + offset_y), 1
                )

        lbl_text = "Balls Remaining: "
        lbl_width = self.game.assets.fonts["small"].size(lbl_text)[0]

        Utils.draw_text_outline(
            screen,
            lbl_text,
            self.game.assets.fonts["small"],
            GREEN,
            20 + offset_x,
            20 + offset_y,
            align="left",
            outline_color=BLACK
        )
        
        screen.blit(
            self.game.assets.ui_ball,
            (20 + lbl_width + 5 + offset_x, 15 + offset_y),
        ) 
        Utils.draw_text_outline(
            screen,
            f": {self.balls_left}",
            self.game.assets.fonts["small"],
            WHITE,
            20
            + lbl_width
            + 5
            + offset_x
            + self.game.assets.ui_ball.get_width()
            + 5,
            20 + offset_y,
            align="left", 
        )
        
        # Area Completion Indicator
        pool_name = self.area_data.get("wild_pool_percentages")
        if pool_name:
            wild_pool = self.game.loader.area_data.get(pool_name, {})
            if wild_pool:
                # Check if all IDs in pool are caught
                all_caught = True
                for pid_str in wild_pool.keys():
                    if int(pid_str) not in caught_ids: # Uses the pre-calc set
                        all_caught = False
                        break
                
                if all_caught:
                    Utils.draw_text_outline(
                        screen,
                        "Area Complete!",
                        self.game.assets.fonts["small"],
                        GOLD,
                        20 + offset_x,
                        350 + offset_y,
                        align="left"
                    )
                    Utils.draw_star(screen, GOLD, (20 + offset_x + 360, 350 + offset_y), 15)

        self.game.ui_manager.draw(
            screen
        )

        unique_team_for_display = []
        seen_ids = set()
        for p in reversed(self.collected_team):
            if p.id not in seen_ids:
                unique_team_for_display.append(p)
                seen_ids.add(p.id)
        unique_team_for_display.reverse()

        for i, tp in enumerate(unique_team_for_display[-6:]):
            col, row = i % 3, i // 3
            if self.game.assets.is_pc:
                unit = int(width * 0.05)
                spacing = int(unit * 1.1)
                sx = width - int(width * 0.02) - ((3 - col) * spacing)
                sy = int(height * 0.02) + (row * spacing)
            else:
                sx = width - (width * 0.42) + (col * (width * 0.13))
                sy = 20 + (row * (width * 0.14))
            if tp and tp.sidebar_image:
                screen.blit(tp.sidebar_image, (sx + offset_x, sy + offset_y))

        if self.pause_timer == 0 and not self.ball_active:
            for sparkle, idx in self.idle_sparkles:
                sparkle.draw(screen)
        for sb in self.starbursts:
            sb.draw(screen)

        for i in range(3):
            cx = self.get_cx(i)
            p_info = (
                self.boss_manager.boss_pokemon_data
                if self.boss_manager.in_boss_mode and i == 1
                else (self.p_data[i] if i < len(self.p_data) else None)
            )
            if p_info and p_info.image:
                if (
                    (self.ball_active or self.pause_timer > 0 or self.flee_active)
                    and self.caught_idx != -1
                    and not self.is_progression_paused
                ):
                    if self.flee_active and not self.boss_manager.in_boss_mode:
                        self.runaway_x_offsets[i] += 35 if i > 1 else -35
                    elif i != self.caught_idx:
                        self.runaway_x_offsets[i] += 30 if i > self.caught_idx else -30

                sk = random.randint(-self.shake_amount, self.shake_amount) + (
                    random.randint(-5, 5) if self.boss_manager.in_boss_mode else 0
                )
                bounce = (
                    abs(math.sin(pygame.time.get_ticks() * 0.02) * 30)
                    if self.runaway_x_offsets[i] != 0
                    else 0
                )
                wiggle = (
                    math.sin(pygame.time.get_ticks() * 0.12) * 25
                    if (
                        self.ball_active
                        and not self.flee_active
                        and i == self.caught_idx
                    )
                    else 0
                )
                hover_y = 0
                if self.boss_manager.in_boss_mode:
                    hover_y = (
                        math.sin(
                            pygame.time.get_ticks() * p_info.bob_speed + p_info.bob_offset
                        )
                        * p_info.bob_amount
                    )
                dx, dy = (
                    (width // 2 if self.boss_manager.in_boss_mode else cx)
                    + self.runaway_x_offsets[i]
                    + sk
                    + offset_x
                    + wiggle,
                    self.sprite_y + sk + offset_y - bounce + hover_y,
                )

                should_hide = (
                    (self.pause_timer > 0)
                    and i == self.caught_idx
                    and not self.flee_active
                    and not (
                        self.boss_manager.in_boss_mode and self.boss_manager.boss_hp > 0
                    )
                )
                if not should_hide:
                    screen.blit(p_info.image, p_info.image.get_rect(center=(dx, dy)))
                    
                    # Draw Caught Indicator (Pokeball Icon)
                    if self.caught_idx == -1 and not self.boss_manager.in_boss_mode:
                        if p_info.id in caught_ids:
                            # Draw icon at top-right of sprite
                            r = p_info.image.get_rect(center=(dx, dy))
                            screen.blit(self.caught_indicator, (r.right - 60, r.top))

            if self.pause_timer == 0 and not self.is_progression_paused and not self.dialogue_box.visible:
                txt = str(self.options[i])
                font = self.game.assets.fonts["num"]
                if len(txt) > 3:
                    font = self.game.assets.fonts["s_med"]

                text_surf = font.render(txt, True, WHITE)
                padding_x = 60
                padding_y = 40
                btn_w = text_surf.get_width() + padding_x
                btn_h = text_surf.get_height() + padding_y

                cy = height * 0.60
                if i == 1:
                    cy += btn_h + 10

                btn_rect = pygame.Rect(cx - btn_w // 2, cy - btn_h // 2, btn_w, btn_h)
                self.answer_btn_rects[i] = (
                    btn_rect
                )

                pygame.draw.rect(screen, BLUE, btn_rect, border_radius=25)
                Utils.draw_text_outline(
                    screen, txt, font, WHITE, btn_rect.centerx, btn_rect.centery
                )

        if self.game.debug_mode:
            for r in self.answer_btn_rects:
                pygame.draw.rect(screen, (255, 0, 255), r, 2)

        if self.pause_timer == 0 and not self.is_progression_paused:
            Utils.draw_text_outline(
                screen,
                self.problem_str,
                self.game.assets.fonts["big"],
                GOLD,
                width // 2,
                height * 0.15,
            )

            if self.question_timer > 0:
                bar_w = 200
                bar_h = 10
                ratio = max(0, min(1, self.question_timer / (30 * FPS)))
                bar_x = width // 2 - bar_w // 2
                bar_y = int(height * 0.22)
                pygame.draw.rect(screen, BLACK, (bar_x, bar_y, bar_w, bar_h))
                pygame.draw.rect(screen, GOLD, (bar_x, bar_y, int(bar_w * ratio), bar_h))

        if self.flash_timer > 0:
            Utils.draw_text_outline(
                screen,
                self.flash_msg,
                self.game.assets.fonts["s_med"],
                GOLD,
                width // 2,
                height // 2,
            )
        if self.pause_timer > 0:
            Utils.draw_multiline_text(
                screen,
                self.feedback_text,
                self.game.assets.fonts["s_med"],
                self.feedback_color,
                width // 2,
                height * 0.35,
                max_width=width - 40,
            )

        if self.ball_active:
            screen.blit(
                self.current_ball_img, (self.ball_pos[0] - 42, self.ball_pos[1] - 42)
            )

        if self.is_progression_paused:
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            if self.rounds_completed == 0:
                route_name = self.area_data.get(
                    "route_name",
                    self.game.story_manager.current_area_key.replace("_", " ").title(),
                )
                msg = f"Entered {route_name}"
            else:
                msg = self.game.assets.get_text("explored_area")
            Utils.draw_text_outline(
                screen,
                msg,
                self.game.assets.fonts["med"],
                WHITE,
                width // 2,
                height * 0.3,
            )
            Utils.draw_text_outline(
                screen,
                self.game.assets.get_text("whats_next"),
                self.game.assets.fonts["s_med"],
                WHITE,
                width // 2,
                height * 0.4,
            )
            # Buttons are handled by UI manager, no need to redraw manually


# [REF-0036: City Hub State]
class CityState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.area_key = self.game.story_manager.current_area_key
        self.area_data = self.game.story_manager.get_current_area_data()

        self.background = self.load_area_background()
        if self.background:
            box_top = Utils.get_full_dialogue_rect(self.game).top
            self.background = pygame.transform.scale(self.background, (self.game.width, box_top))
        self.action_menu = CityActionMenu(
            game, self.area_key,
            on_explore=self.open_explore_menu,
            on_pkdex=lambda: self._open_pokedex(),
            on_pkmn=lambda: self._open_party(),
            on_travel=self.open_travel_menu
        )

        self.hover_menu_active = None
        self.hover_buttons = []
        self.hover_bg_rect = None

        self.npc_active = False
        self.npc_sprite = None
        self.npc_dialogue = None
        self.current_npc = None
        self.creepy_timer = 0
        self.choice_active = False
        self.npc_slide_offset = 0

        btn_x, btn_y = 20, 80
        btn_w, btn_h = 120, 40
        spacing = 10
        
        self.hud_buttons = [
            Button((btn_x, btn_y, btn_w, btn_h), "PC", game.assets.fonts["tiny"], lambda: self._open_pc(), bg_color=GREEN),
            Button((btn_x, btn_y + (btn_h+spacing), btn_w, btn_h), "BAG", game.assets.fonts["tiny"], lambda: self._open_bag(), bg_color=BLUE),
            Button((btn_x, btn_y + (btn_h+spacing)*2, btn_w, btn_h), "BADGES", game.assets.fonts["tiny"], lambda: self._open_badges(), bg_color=GOLD),
            Button((btn_x, btn_y + (btn_h+spacing)*3, btn_w, btn_h), "SAVE", game.assets.fonts["tiny"], self.save_game, bg_color=GREEN),
            Button((btn_x, btn_y + (btn_h+spacing)*4, btn_w, btn_h), "LOAD", game.assets.fonts["tiny"], lambda: self._open_load(), bg_color=RED),
        ]
        
        self.yes_btn = Button((0,0,0,0), "YES", game.assets.fonts["small"], None, bg_color=GREEN, visible=False, autosize=False)
        self.no_btn = Button((0,0,0,0), "NO", game.assets.fonts["small"], None, bg_color=RED, visible=False, autosize=False)
        
        for btn in self.hud_buttons:
            self.game.ui_manager.add_element(btn)
        
        self.game.ui_manager.add_element(self.yes_btn)
        self.game.ui_manager.add_element(self.no_btn)

    def _open_pc(self):
        from src.states.systems import PCState
        self.game.change_state(PCState(self.game, self))

    def _open_bag(self):
        from src.states.systems import BagState
        self.game.change_state(BagState(self.game, self))
    
    def _open_badges(self):
        from src.states.systems import BadgeCaseState
        self.game.change_state(BadgeCaseState(self.game, self))

    def _open_load(self):
        from src.states.menus import LoadState
        self.game.change_state(LoadState(self.game, self))

    def _open_pokedex(self):
        from src.states.systems import PokedexState
        self.game.change_state(PokedexState(self.game, self))

    def _open_party(self):
        from src.states.systems import PokemonPartyMenuState
        self.game.change_state(PokemonPartyMenuState(self.game, self, context="normal"))

    def load_area_background(self):
        # 1. Check JSON config first (Data-driven)
        bg_config = self.area_data.get("backgrounds", {}).get("main")
        kanto_bg_dir = self.game.assets.kanto_backgrounds_dir
        
        if bg_config:
            path = os.path.join(kanto_bg_dir, bg_config)
            if os.path.exists(path):
                return pygame.image.load(path).convert()

        # 2. Fallback to constructed name [1st part]_city.png
        first_part = self.area_key.split('_')[0].lower()
        bg_name = f"{first_part}_city.png"
        path = os.path.join(kanto_bg_dir, bg_name)

        if os.path.exists(path):
            try:
                return pygame.image.load(path).convert()
            except pygame.error:
                pass
        
        if os.path.exists(kanto_bg_dir):
            area_name_clean = self.area_key.lower().replace("_", "")
            try:
                candidates = [f for f in os.listdir(kanto_bg_dir) if area_name_clean in f.lower()]
                if candidates:
                    path = os.path.join(kanto_bg_dir, random.choice(candidates))
                    return pygame.image.load(path).convert()
            except (OSError, pygame.error):
                pass

    def start_gym_battle(self): 
        gym_data = self.area_data.get("gym")
        if not gym_data:
            self.show_message("The Gym is locked.")
            return
        
        # 1. Check for Pre-Battle Events (like Team Rocket) FIRST
        pre_event = gym_data.get("pre_battle_event")
        if pre_event:
            flag = pre_event.get("flag_check")
            invert = pre_event.get("invert_flag", False)
            flag_val = self.game.story_manager.story_flags.get(flag, False)
            
            should_trigger = (not flag_val) if invert else flag_val
            
            if should_trigger:
                t_data = pre_event["trainer"]
                self._initiate_gym_battle(t_data, victory_flag=flag)
                return

        # 2. If no event triggers, THEN check Badge Requirements
        reqs = gym_data.get("requirements", {})
        if reqs:
            needed_badges = reqs.get("badges", 0)
            if len(self.game.story_manager.badges) < needed_badges:
                fail_text = reqs.get("fail_text", "The Gym is closed.")
                self.show_message(fail_text)
                return

        # Locks passed, enter Lobby
        self.game.change_state(GymLobbyState(self.game, self))

    # Helper for the PRE-EVENT battle
    def _initiate_gym_battle(self, trainer_data, victory_flag=None):
        from src.states.battle import TrainerBattleState, TrainerIntroState
        team_ids = trainer_data.get("team", [])
        opponent_team = []
        for pid in team_ids:
            raw = self.game.loader.fetch_specific(pid)
            opponent_team.append(Pokemon(raw, self.game.assets, size_mult=3.125))

        sprite_name = trainer_data.get("sprite")
        trainer_sprite = self.game.assets.get_trainer_image(sprite_name)
        
        battle_state = TrainerBattleState(
            self.game,
            opponent_team,
            trainer_sprite=trainer_sprite,
            trainer_class=trainer_data.get("class", "TRAINER"),
            trainer_name=trainer_data.get("name"),
            custom_dialogue=trainer_data.get("dialogue", {}),
            rewards=trainer_data.get("rewards"),
            battle_type="gym_event",
            area_name=self.area_key,
            victory_flag=victory_flag,
            badge_reward=trainer_data.get("badge_reward")
        )

        intro_text = random.choice(trainer_data.get("dialogue", {}).get("intro", ["Prepare to battle!"]))
        self.game.change_state(TrainerIntroState(self.game, trainer_sprite, intro_text, battle_state))

    def show_message(self, text, callback=None):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "system"
        self.action_menu.set_visibility(False)
        self.npc_sprite = None
        self.npc_bg = None

        if not callback:
            callback = self.end_npc_interaction

        self.npc_dialogue = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(self.game),
            text if isinstance(text, list) else [text],
            self.game.assets.fonts["med"],
            callback=callback
        )

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
            valid_options.append(opt_data)

        if not valid_options:
            self.hover_menu_active = False
            return

        font = self.game.assets.fonts["tiny"]
        max_w = 220
        for opt in valid_options:
            w = font.size(opt['text'])[0] + 40
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
        cols = 1
        rows = count

        bg_w = cols * btn_w + (cols - 1) * gap_x + padding * 2
        bg_h = rows * btn_h + (rows - 1) * gap_y + padding * 2
        
        self.hover_bg_rect = pygame.Rect(0, 0, bg_w, bg_h)
        self.hover_bg_rect.bottomright = (anchor_right, anchor_bottom)
        
        start_y = self.hover_bg_rect.top + padding
        
        for i, opt_data in enumerate(valid_options):
            col = 0
            row = i
            
            btn_x = self.hover_bg_rect.left + padding
            btn_y = start_y + row * (btn_h + gap_y)
            
            rect = (btn_x, btn_y, btn_w, btn_h)
            
            callback = self._get_callback_for_option(opt_data)
            if callback:
                btn = Button(rect, opt_data['text'], self.game.assets.fonts["tiny"], callback, autosize=False)
                self.hover_buttons.append(btn)
                self.game.ui_manager.add_element(btn)

    def _get_callback_for_option(self, opt_data):
        action = opt_data.get("action")
        if action == "HEAL": return lambda: self.game.change_state(PokeCenterState(self.game, self))
        if action == "SHOP": return self._open_shop
        if action == "GYM": return self.start_gym_battle
        if action == "NPC":
            target = opt_data.get("target")
            if target == "lunatic": return self.meet_lunatic
            if target == "mom": return self.visit_mom
            if target == "professor_oak": return self.visit_prof_oak
            if target == "oldman": return self.wake_sleeping_man
            if target == "museum": return self.visit_museum
            if target == "bill": return self.visit_bill
            if target == "stoneman": return self.visit_stoneman
            if target == "professor_elm": return self.visit_prof_elm

        if action == "TRAVEL":
            return lambda: self.go_to_area(opt_data.get("target_area"))
        return None

    def _open_shop(self):
        # PokeMartState is in overworld.py, so we can access it directly (defined later in file)
        self.game.change_state(PokeMartState(self.game, self))

    def open_explore_menu(self):
        options = self.area_data.get("explore_options", [])
        self._create_hover_menu(options, self.action_menu.buttons[0].rect)

    def open_travel_menu(self):
        options = self.area_data.get("travel_options", [])
        for opt in options:
            opt['action'] = 'TRAVEL'
        if len(self.action_menu.buttons) > 3:
            self._create_hover_menu(options, self.action_menu.buttons[3].rect)

    def visit_mom(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "mom"
        self.npc_slide_offset = 400
        self.action_menu.set_visibility(False)

        bg_path = os.path.join(self.game.assets.kanto_backgrounds_dir, "pallet_city_mom.png")
        if os.path.exists(bg_path):
            box_top = Utils.get_full_dialogue_rect(self.game).top
            self.npc_bg = pygame.transform.scale(pygame.image.load(bg_path).convert(), (self.game.width, box_top))
        else:
            self.npc_bg = None

        path = os.path.join(self.game.assets.sprites_dir, "png", "mom.png")
        if os.path.exists(path):
             img = pygame.image.load(path).convert_alpha()
             h = int(self.game.height * 0.6)
             w = int(img.get_width() * (h / img.get_height()))
             self.npc_sprite = pygame.transform.scale(img, (w, h))
        else:
             self.npc_sprite = self.game.assets.get_trainer_image("mom.png")

        for p in self.game.story_manager.player_team:
            p.current_hp = p.get_max_hp()
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.play()
            
        dialogue = ["Mom: Oh, you look tired, honey!", "Rest up for a while...", "... ... ...", "Your team is fully healed!", "Good luck on your adventure!"]
        self.npc_dialogue = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(self.game),
            dialogue,
            self.game.assets.fonts["med"],
            callback=self.end_npc_interaction
        )

    def visit_prof_oak(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "professor_oak"
        self.npc_slide_offset = 400
        self.action_menu.set_visibility(False)

        path = os.path.join(self.game.assets.sprites_dir, "png", "oak.png")
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            h = int(self.game.height * 0.6)
            w = int(img.get_width() * (h / img.get_height()))
            self.npc_sprite = pygame.transform.scale(img, (w, h))
        else:
            self.npc_sprite = self.game.assets.get_trainer_image("professor_oak.png")

        self.npc_dialogue = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(self.game),
            [self.game.assets.get_text("professor_oak")],
            self.game.assets.fonts["med"],
            callback=self.end_npc_interaction
        )

    def visit_prof_elm(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "professor_elm"
        self.npc_slide_offset = 400
        self.action_menu.set_visibility(False)

        path = os.path.join(self.game.assets.sprites_dir, "png", "elm.png")
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            h = int(self.game.height * 0.6)
            w = int(img.get_width() * (h / img.get_height()))
            self.npc_sprite = pygame.transform.scale(img, (w, h))
        else:
            self.npc_sprite = self.game.assets.get_trainer_image("scientist.png")

        if not self.game.story_manager.story_flags.get("received_johto_starter"):
            msg = ["Elm: Welcome to Johto!", "I have a special Pokémon for you."]
            from src.states.menus import StarterSelectionState
            callback = lambda: self.game.change_state(StarterSelectionState(self.game, starter_ids=[152, 155, 158], region="JOHTO"))
        else:
            msg = ["Elm: Your journey is just beginning!", "Take care of your Pokémon."]
            callback = self.end_npc_interaction
            
        self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msg, self.game.assets.fonts["med"], callback=callback)

    def wake_sleeping_man(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "oldman"
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("oldman.png")
        if not self.npc_sprite:

            self.npc_sprite = self.game.assets.get_trainer_image("old_man.png")
        
        dialogue_text = ["ZzzZzzz.....", "zzZZZzzzzZzzzzzz.....", "Take the Old Man's helmet?"]
        
        self.npc_dialogue = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(self.game),
            dialogue_text,
            self.game.assets.fonts["med"],
            callback=self.end_npc_interaction
        )
        
    def visit_museum(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "museum"
        self.action_menu.set_visibility(False)

        first_part = self.area_key.split('_')[0].lower()
        bg_name = f"{first_part}_city_museum.png"
        bg_path = os.path.join(self.game.assets.kanto_backgrounds_dir, bg_name)
        
        if os.path.exists(bg_path):
            box_top = Utils.get_full_dialogue_rect(self.game).top
            raw_bg = pygame.image.load(bg_path).convert()
            self.npc_bg = pygame.transform.scale(raw_bg, (self.game.width, box_top))
        else:
            self.npc_bg = None

        self.npc_sprite = self.game.assets.get_trainer_image("scientist.png")
        
        msgs = []
        flags = self.game.story_manager.story_flags
        inv = self.game.story_manager.inventory
        
        has_beat_jessie = flags.get("viridian_rocket_defeated", False)
        has_beat_brock = "BOULDER" in self.game.story_manager.badges
        
        got_helix = inv.get("HELIX_FOSSIL", 0) > 0
        got_dome = inv.get("DOME_FOSSIL", 0) > 0
        
        if has_beat_jessie and not got_helix:
            msgs.append("You chased off those Rockets? Taking this HELIX FOSSIL for safe keeping!")
            msgs.append("You received the HELIX FOSSIL!")
            inv["HELIX_FOSSIL"] = inv.get("HELIX_FOSSIL", 0) + 1
            if not has_beat_brock:
                msgs.append("Please return after you have defeated Brock.")
        elif has_beat_brock and not got_dome:
            msgs.append("You defeated Brock? You are worthy of this DOME FOSSIL.")
            msgs.append("You received the DOME FOSSIL!")
            inv["DOME_FOSSIL"] = inv.get("DOME_FOSSIL", 0) + 1
        else:
            if not has_beat_jessie:
                msgs.append("We are currently closed due to Team Rocket activity.")
            elif not has_beat_brock:
                msgs.append("Please return after you have defeated Brock.")
            else:
                msgs.append("Welcome to the Pewter Museum of Science!")

        self.npc_dialogue = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(self.game),
            msgs,
            self.game.assets.fonts["med"],
            callback=self.end_npc_interaction
        )

    def visit_stoneman(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "stoneman"
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("ruinmaniac.png")

        badges = self.game.story_manager.badges
        flags = self.game.story_manager.story_flags
        inventory = self.game.story_manager.inventory

        # --- CALCULATE REVIVAL CAPACITY ---
        capacity = 0
        if "BOULDER" in badges: capacity += 1
        if "CASCADE" in badges: capacity += 1
        
        # Check Nugget Bridge Clear Status (Route 25)
        r25_data = self.game.loader.area_data.get("STORY_PROGRESSION", {}).get("KANTO_ROUTE_25", {})
        r25_pool = r25_data.get("trainer_pool", [])
        r25_defeated_count = len(self.game.story_manager.defeated_trainers.get("KANTO_ROUTE_25", set()))
        
        if r25_pool and r25_defeated_count >= len(r25_pool):
            capacity += 1

        revived_count = flags.get("fossils_revived_count", 0)
        slots_available = capacity - revived_count

        # --- FOSSIL MAPPING ---
        fossil_map = {
            "HELIX_FOSSIL": 138,    # Omanyte
            "DOME_FOSSIL": 140,     # Kabuto
            "OLD_AMBER": 142,       # Aerodactyl
            "ARMOR_FOSSIL": 410,    # Shieldon
            "SKULL_FOSSIL": 408,    # Cranidos
            "ROOT_FOSSIL": 345,     # Lileep
            "CLAW_FOSSIL": 347      # Anorith
        }

        target_fossil = None
        target_id = None
        if slots_available > 0:
            for f_name, p_id in fossil_map.items():
                if inventory.get(f_name, 0) > 0:
                    target_fossil = f_name
                    target_id = p_id
                    break
        
        msgs = ["I am the Fossil Maniac!", "I can revive fossils into Pokémon."]

        if target_fossil:
            msgs.append(f"Oh! Is that a {target_fossil.replace('_', ' ').title()}?")
            msgs.append("I can revive it for you right now!")
            self.pending_revival = (target_fossil, target_id)
            callback = self.perform_fossil_revival
        elif slots_available > 0:
            msgs.append(f"I have {slots_available} revival slot(s) ready for you.")
            msgs.append("But you don't have any fossils!")
            callback = self.end_npc_interaction
        else:
            msgs.append("I need to study more to revive more fossils.")
            reqs = []
            if "BOULDER" not in badges: reqs.append("defeat Brock")
            if "CASCADE" not in badges: reqs.append("defeat Misty")
            if not (r25_pool and r25_defeated_count >= len(r25_pool)): reqs.append("clear the Nugget Bridge")
            
            if reqs:
                msgs.append(f"To unlock a slot: {reqs[0]}.")
            else:
                msgs.append("You have unlocked all my slots for now!")
            callback = self.end_npc_interaction

        self.npc_dialogue = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(self.game),
            msgs,
            self.game.assets.fonts["med"],
            callback=callback
        )

    def visit_bill(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "bill"
        self.npc_slide_offset = 400
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("bill.png")
        
        bg_path = os.path.join(self.game.assets.kanto_backgrounds_dir, "bill_city.png")
        if os.path.exists(bg_path):
            box_top = Utils.get_full_dialogue_rect(self.game).top
            self.npc_bg = pygame.transform.scale(pygame.image.load(bg_path).convert(), (self.game.width, box_top))
        else:
            self.npc_bg = None
        
        # Check Route 25 (Nugget Bridge) progress
        r25_data = self.game.loader.area_data.get("STORY_PROGRESSION", {}).get("KANTO_ROUTE_25", {})
        r25_pool = r25_data.get("trainer_pool", [])
        r25_defeated = self.game.story_manager.defeated_trainers.get("KANTO_ROUTE_25", set())
        
        all_beaten = len(r25_pool) > 0 and len(r25_defeated) >= len(r25_pool)
        received_eevee = self.game.story_manager.story_flags.get("received_bill_eevee", False)
        
        msgs = ["Hi! I'm Bill!", "I'm the developer of the PC Storage System."]
        
        if received_eevee:
            msgs.append("I hope you and Eevee are getting along well!")
            msgs.append("My collection is full of rare Pokémon data.")
        elif all_beaten:
            msgs.append("Wow! You cleared the Nugget Bridge challenge?")
            msgs.append("That's impressive! Most trainers give up halfway.")
            msgs.append("Here, take this special Pokémon as a reward!")
            
            # Grant Eevee (ID 133)
            self.game.story_manager.story_flags["received_bill_eevee"] = True
            raw = self.game.loader.fetch_specific(133)
            pokemon = Pokemon(raw, self.game.assets, size_mult=2.5)
            
            if len(self.game.story_manager.player_team) < 6:
                self.game.story_manager.player_team.append(pokemon)
                msgs.append("You received Eevee!")
            else:
                self.game.story_manager.pc_pokemon.append(pokemon)
                msgs.append("You received Eevee! Sent to PC.")
            
            self.game.data.add_pokemon(pokemon)
            self.game.data.save()
        else:
            msgs.append("I hear there's a challenge on Nugget Bridge nearby.")
            msgs.append("If you can beat all the trainers there, come show me!")

        self.npc_dialogue = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(self.game),
            msgs,
            self.game.assets.fonts["med"],
            callback=self.end_npc_interaction
        )

    def resolve_oldman_yes(self):
        self.choice_active = False
        self.yes_btn.set_visibility(False)
        self.no_btn.set_visibility(False)
        self.game.story_manager.story_flags['got_rocky_helmet'] = True
        self.game.story_manager.inventory['ROCKY_HELMET'] = self.game.story_manager.inventory.get('ROCKY_HELMET', 0) + 1
        self.npc_dialogue.reset(["You received the Rocky Helmet!", "You can now Headbutt trees."])
        self.npc_dialogue.callback = self.end_npc_interaction

    def perform_fossil_revival(self):
        f_name, p_id = getattr(self, 'pending_revival', (None, None))
        if not f_name: return

        self.game.story_manager.inventory[f_name] -= 1

        self.game.story_manager.story_flags["fossils_revived_count"] = self.game.story_manager.story_flags.get("fossils_revived_count", 0) + 1
        
        raw = self.game.loader.fetch_specific(p_id)
        pokemon = Pokemon(raw, self.game.assets, size_mult=2.5)
        
        if len(self.game.story_manager.player_team) < 6:
            self.game.story_manager.player_team.append(pokemon)
        else:
            self.game.story_manager.pc_pokemon.append(pokemon)
        
        self.game.data.add_pokemon(pokemon)
        self.game.data.save()
        
        self.npc_dialogue.reset([f"Success! The fossil was revived into {pokemon.display_name}!", "Take good care of it!"])
        self.npc_dialogue.callback = self.end_npc_interaction

    def resolve_oldman_no(self):
        self.choice_active = False
        self.yes_btn.set_visibility(False)
        self.no_btn.set_visibility(False)
        self.npc_dialogue.reset("You left the old man to his dreams.")
        self.npc_dialogue.callback = self.end_npc_interaction
    
    def meet_lunatic(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "lunatic"
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("lunatic.png")

        default_key = f"{self.area_key.lower().replace('kanto_', '')}_lunatic_info"
        dialogue_key = self.area_data.get("lunatic_dialogue_key")
        if not dialogue_key:
            dialogue_key = default_key
            
        dialogue_text = self.game.assets.get_text(
            dialogue_key, default="The spirits whisper of a powerful trainer here..."
        )

        self.npc_dialogue = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(self.game),
            dialogue_text,
            self.game.assets.fonts["med"],
            callback=self.end_npc_interaction,
        )

    def end_npc_interaction(self):
        self.npc_active = False
        self.npc_sprite = None
        self.current_npc = None
        self.npc_bg = None
        self.choice_active = False
        self.yes_btn.set_visibility(False)
        self.no_btn.set_visibility(False)
        self.action_menu.set_visibility(True)
        if self.npc_dialogue in self.game.ui_manager.elements:
            self.game.ui_manager.elements.remove(self.npc_dialogue)
        self.npc_dialogue = None

    def go_to_area(self, area_key):
        if area_key:
            self.game.change_state(AreaTransitionState(self.game, area_key))

    def go_to_next_area(self):
        next_area = self.area_data.get("next_area")
        if next_area:
            self.game.change_state(AreaTransitionState(self.game, next_area))

    def save_game(self):
        from src.states.menus import SaveState
        self.game.change_state(SaveState(self.game, self))

    def start(self):
        self.clear_hover_menu()
        self.game.ui_manager.add_element(self.action_menu)

        visited_flag = f"visited_{self.area_key}"
        if not self.game.story_manager.story_flags.get(visited_flag, False):
            self.game.story_manager.story_flags[visited_flag] = True

        pygame.event.clear()
        for btn in self.hud_buttons:
            if btn not in self.game.ui_manager.elements:
                self.game.ui_manager.add_element(btn)
    def clear_hover_menu(self):
        for btn in self.hover_buttons:
            if btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)
        self.hover_menu_active = None
        self.hover_buttons.clear()
        self.hover_bg_rect = None

    def handle_events(self, events):
        if self.npc_active:
            if self.choice_active:
                return
            
            for event in events:
                if self.npc_dialogue:
                    self.npc_dialogue.handle_event(event)
            return

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.hover_menu_active:
                    self.clear_hover_menu()

                for btn in self.hud_buttons:
                    if btn.rect.collidepoint(event.pos):
                        return

    def update(self):
        if self.npc_active and self.npc_dialogue and self.npc_dialogue.visible:
            if self.npc_slide_offset > 0:
                self.npc_slide_offset = max(0, self.npc_slide_offset - 40)

            self.npc_dialogue.update()
            if self.current_npc == "lunatic":
                self.creepy_timer += 1
            
            # Force options for Old Man when text reaches the question
            if self.current_npc == "oldman" and self.npc_dialogue.current_line == 2 and self.npc_dialogue.is_waiting_for_click:
                self.choice_active = True

            if self.choice_active:
                box = self.npc_dialogue.rect
                self.yes_btn.rect = pygame.Rect(box.right - 280, box.bottom - 80, 120, 60)
                self.no_btn.rect = pygame.Rect(box.right - 140, box.bottom - 80, 120, 60)
                self.yes_btn.callback = self.resolve_oldman_yes
                self.no_btn.callback = self.resolve_oldman_no
                
                # Bring buttons to top of UI stack to ensure they aren't covered
                if self.yes_btn in self.game.ui_manager.elements: self.game.ui_manager.elements.remove(self.yes_btn)
                if self.no_btn in self.game.ui_manager.elements: self.game.ui_manager.elements.remove(self.no_btn)
                self.game.ui_manager.add_element(self.yes_btn)
                self.game.ui_manager.add_element(self.no_btn)

                self.yes_btn.set_visibility(True)
                self.no_btn.set_visibility(True)

    def draw(self):
        self.game.screen.fill(BLACK)
        
        if self.npc_active and self.current_npc == "lunatic":
            # Creepy BG effect
            val = int(50 + math.sin(self.creepy_timer * 0.1) * 40)
            self.game.screen.fill((val, 0, val//2))
        elif self.npc_active and hasattr(self, "npc_bg") and self.npc_bg:
            self.game.screen.blit(self.npc_bg, (0, 0))
        else:
            if self.background:
                self.game.screen.blit(self.background, (0, 0))

        if self.hover_menu_active and self.hover_bg_rect:
            # Draw identical white box
            pygame.draw.rect(self.game.screen, WHITE, self.hover_bg_rect, border_radius=12)
            pygame.draw.rect(self.game.screen, BLACK, self.hover_bg_rect, 6, border_radius=12)

        if self.npc_active and self.npc_dialogue:
            if self.npc_sprite:
                rect = self.npc_sprite.get_rect(
                    center=(self.game.width / 2 + self.npc_slide_offset, self.game.height / 2 - 50)
                )
                self.game.screen.blit(self.npc_sprite, rect)
            
            # Draw dialogue manually since we removed it from UI manager
            self.npc_dialogue.draw(self.game.screen)

        self.game.ui_manager.draw(self.game.screen)

        # Draw HUD Balls
        lbl_text = "Balls:"
        lbl_width = self.game.assets.fonts["small"].size(lbl_text)[0]
        
        Utils.draw_text_outline(
            self.game.screen, lbl_text, self.game.assets.fonts["small"], WHITE, 20, 20, align="left", outline_color=BLACK
        )
        
        icon_w = 0
        if self.game.assets.ui_ball:
            self.game.screen.blit(self.game.assets.ui_ball, (20 + lbl_width + 5, 15))
            icon_w = self.game.assets.ui_ball.get_width()
            
        Utils.draw_text_outline(
            self.game.screen,
            f"x{self.game.story_manager.balls_left}",
            self.game.assets.fonts["small"],
            WHITE,
            20 + lbl_width + 5 + icon_w + 5,
            20,
            align="left"
        )


# [REF-0042: Area Transition Logic]
class AreaTransitionState(GameState):
    def __init__(self, game, next_area_key, initial_message=None):
        super().__init__(game)
        self.next_area_key = next_area_key
        self.timer = 75
        self.wait_for_dialogue = bool(initial_message)
        self.bg = None

        if isinstance(self.game.current_state, PlayState):
            self.game.story_manager.balls_left = self.game.current_state.balls_left
            self.game.story_manager.current_streak = self.game.current_state.current_streak
        
        if hasattr(self.game, 'story_manager'):
            pass

        rect = Utils.get_full_dialogue_rect(self.game)
        msg = []
        if initial_message:
            msg.append(initial_message)

        next_area_data = self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(self.next_area_key, {})
        route_name = next_area_data.get("route_name", self.next_area_key.replace("_", " ").title())

        msg.append(
            self.game.assets.get_text("entering_area", area=route_name)
        )

        area_type = next_area_data.get("area_type", "wild_route")
        
        if area_type not in ["town", "city"]:
            warning = next_area_data.get("enter_warning", self.game.assets.get_text("area_warning"))
            msg.append(warning)

        self.dialogue_box = ClassicDialogueBox(rect, msg, self.game.assets.fonts["med"])
        self.oak_sprite = None
        self.oak_pos_x = -300
        
        if initial_message and "Oak" in initial_message:
            # Load Lab Background
            bg_path = os.path.join(self.game.assets.kanto_backgrounds_dir, "pallet_city_lab.png")
            if os.path.exists(bg_path):
                box_top = Utils.get_full_dialogue_rect(self.game).top
                self.bg = pygame.transform.scale(pygame.image.load(bg_path).convert(), (self.game.width, box_top))
            
            # Expand dialogue
            self.dialogue_box.reset(["Oak: Excellent battle!", "You have great potential.", initial_message])
            
            oak_img_path = os.path.join(self.game.assets.sprites_dir, "png", "oak.png")
            if os.path.exists(oak_img_path):
                img = pygame.image.load(oak_img_path).convert_alpha()
                h = int(self.game.height * 0.6)
                w = int(img.get_width() * (h / img.get_height()))
                self.oak_sprite = pygame.transform.scale(img, (w, h))


    def handle_events(self, events):
        for event in events:
            self.dialogue_box.handle_event(event)

    def update(self):
        self.dialogue_box.update()
        if self.oak_sprite:
            target_x = self.game.width // 2
            if self.oak_pos_x < target_x:
                self.oak_pos_x += (target_x - self.oak_pos_x) * 0.05

        if self.wait_for_dialogue:
            if self.dialogue_box.is_finished:
                self.timer -= 1
        else:
            self.timer -= 1

        if self.timer <= 0:
            self.game.story_manager.current_area_key = self.next_area_key
            
            pygame.event.clear()

            new_area_data = self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(
                self.next_area_key, {}
            )
            area_type = new_area_data.get("area_type", "wild_route")

            if area_type == "town":
                self.game.states["city"] = CityState(self.game)
                self.game.change_state(self.game.states["city"])
            else:
                self.game.states["play"] = PlayState(self.game)
                self.game.change_state(self.game.states["play"])

    def draw(self):
        if self.bg:
            self.game.screen.blit(self.bg, (0, 0))
        else:
            self.game.screen.fill(BLACK)
        if self.oak_sprite:
            rect = self.oak_sprite.get_rect(midbottom=(self.oak_pos_x, self.dialogue_box.rect.top))
            self.game.screen.blit(self.oak_sprite, rect)
        self.dialogue_box.draw(self.game.screen)


# [REF-0030: City & Building Logic]
class PokeCenterState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.timer = 0
        self.phase = "HEAL"
        self.bg = self._load_building_bg(game, "center")

        self.nurse_sprite = game.assets.get_trainer_image("nurse.png")
        self.dialogue_box = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(game),
            ["Welcome to the Pokémon Center!", "We've restored your team to full health."],
            game.assets.fonts["med"],
            callback=self.finish_heal
        )
        
        # Heal immediately
        for p in self.game.story_manager.player_team:
            p.current_hp = p.get_max_hp()
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.play()

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)

    def _load_building_bg(self, game, type_suffix):
        # Rule: [1st part]_city_[suffix].png (e.g. lavender_city_center.png)
        area_key = game.story_manager.current_area_key
        first_part = area_key.split('_')[0].lower()
        filename = f"{first_part}_city_{type_suffix}.png"
        
        box_top = Utils.get_full_dialogue_rect(game).top
        kanto_dir = game.assets.kanto_backgrounds_dir
        path = os.path.join(kanto_dir, filename)
        
        if os.path.exists(path):
            return pygame.transform.scale(pygame.image.load(path).convert(), (game.width, box_top))

        bg = pygame.Surface((game.width, box_top))
        bg.fill(WHITE if type_suffix == "center" else BLUE)
        return bg

    def finish_heal(self):
        self.game.change_state(self.previous_state)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                self.finish_heal()

    def update(self):
        self.dialogue_box.update()

    def draw(self):
        self.game.screen.fill(BLACK)
        self.game.screen.blit(self.bg, (0, 0))
        if self.nurse_sprite:
            rect = self.nurse_sprite.get_rect(center=(self.game.width//2, self.game.height*0.5))
            self.game.screen.blit(self.nurse_sprite, rect)
        self.dialogue_box.draw(self.game.screen)


# [REF-0034: PokeMart System]
class PokeMartState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.phase = "DIALOGUE"
        self.shop_buttons = []
        self.current_page = 0
        self.items_per_page = 6

        self.bottom_rect = Utils.get_full_dialogue_rect(game)
        
        mw = int(game.width * 0.18)
        menu_y = int(game.height * 0.15)
        mh = self.bottom_rect.top - menu_y - 20
        self.menu_rect = pygame.Rect((game.width - mw)//4, menu_y, mw, mh)
        
        btn_w, btn_h = 100, 50
        exit_x = self.bottom_rect.right - btn_w - 40
        exit_y = self.bottom_rect.bottom - btn_h - 40
        self.btn_back = Button((exit_x, exit_y, btn_w, btn_h), "EXIT", game.assets.fonts["tiny"], self.exit_shop, bg_color=RED)
        
        self.btn_prev = Button((self.menu_rect.left - 80, self.menu_rect.centery, 60, 60), "<", game.assets.fonts["med"], self.prev_page, visible=False)
        self.btn_next = Button((self.menu_rect.right + 20, self.menu_rect.centery, 60, 60), ">", game.assets.fonts["med"], self.next_page, visible=False)
        
        self.bg = self._load_building_bg(game, "mart")
        
        area_key = game.story_manager.current_area_key
        flag = f"visited_mart_{area_key}"
        
        if not game.story_manager.story_flags.get(flag, False):
            msg = ["Welcome to the Poké Mart!", "We are currently stocking shelves.", "Here, take these 10 Poké Balls!"]
            game.story_manager.balls_left += 10
            game.story_manager.story_flags[flag] = True
            self.dialogue_box = ClassicDialogueBox(
                Utils.get_full_dialogue_rect(game),
                msg,
                game.assets.fonts["med"],
                callback=self.open_shop_ui
            )
        else:
            self.open_shop_ui()

    def open_shop_ui(self):
        self.phase = "SHOP"
        self.refresh_buttons()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_buttons()

    def next_page(self):
        all_items = sorted(list(self.game.loader.evolution_map.get("EVOLUTION_ITEMS", {}).keys()))
        if (self.current_page + 1) * self.items_per_page < len(all_items):
            self.current_page += 1
            self.refresh_buttons()

    def refresh_buttons(self):
        self.game.ui_manager.elements.clear()
        self.game.ui_manager.add_element(self.btn_back)
        self.game.ui_manager.add_element(self.btn_prev)
        self.game.ui_manager.add_element(self.btn_next)
        
        self.shop_buttons = []
        evo_items = sorted(list(self.game.loader.evolution_map.get("EVOLUTION_ITEMS", {}).keys()))
        
        self.btn_prev.set_visibility(self.current_page > 0)
        self.btn_next.set_visibility((self.current_page + 1) * self.items_per_page < len(evo_items))

        start_idx = self.current_page * self.items_per_page
        page_items = evo_items[start_idx : start_idx + self.items_per_page]

        cols = 1
        col_w = (self.menu_rect.width - 40) // cols
        btn_h = 50
        start_y = self.menu_rect.top + 20
        
        for i, item in enumerate(page_items):
            row = i // cols
            col = i % cols
            x = self.menu_rect.left + 20 + col * col_w
            y = start_y + row * (btn_h + 5)
            
            name = item.replace("_", " ").title()
            text = name
            
            icon = self.game.assets.get_item_image(item)
            
            btn = Button(
                rect=(x, y, col_w - 20, btn_h),
                text=text,
                font=self.game.assets.fonts["tiny"],
                callback=lambda k=item: self.buy_item(k),
                bg_color=BLUE,
                icon=icon,
                autosize=False
            )
            self.shop_buttons.append(btn)
            self.game.ui_manager.add_element(btn)

    def buy_item(self, item_key):
        cost = 5
        if self.game.story_manager.balls_left >= cost:
            self.game.story_manager.balls_left -= cost
            self.game.story_manager.inventory[item_key] = self.game.story_manager.inventory.get(item_key, 0) + 1
            if self.game.assets.heal_sfx:
                self.game.assets.heal_sfx.play()
        else:
            self.game.show_dialogue(["Not enough Poké Balls!"])

    def start(self):
        if self.phase == "DIALOGUE":
            self.game.ui_manager.add_element(self.dialogue_box)
        else:
            self.open_shop_ui()

    def _load_building_bg(self, game, type_suffix):
        area_key = game.story_manager.current_area_key
        first_part = area_key.split('_')[0].lower()
        filename = f"{first_part}_city_{type_suffix}.png"
        
        box_top = Utils.get_full_dialogue_rect(game).top
        kanto_dir = game.assets.kanto_backgrounds_dir
        path = os.path.join(kanto_dir, filename)
        
        if os.path.exists(path):
            return pygame.transform.scale(pygame.image.load(path).convert(), (game.width, box_top))

        bg = pygame.Surface((game.width, box_top))
        bg.fill(BLUE)
        return bg

    def exit_shop(self):
        self.game.change_state(self.previous_state)

    def handle_events(self, events):
        if self.phase != "SHOP":
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.dialogue_box.handle_event(event)

    def update(self):
        if self.phase == "DIALOGUE":
            self.dialogue_box.update()

    def draw(self):
        self.game.screen.fill(BLACK)
        self.game.screen.blit(self.bg, (0, 0))
        
        if self.phase == "SHOP":
            Utils.draw_classic_panel(self.game.screen, self.bottom_rect.x, self.bottom_rect.y, self.bottom_rect.width, self.bottom_rect.height)

            Utils.draw_classic_panel(self.game.screen, self.menu_rect.x, self.menu_rect.y, self.menu_rect.width, self.menu_rect.height)
            
            lbl = f"Balls: {self.game.story_manager.balls_left}"
            Utils.draw_text_outline(self.game.screen, lbl, self.game.assets.fonts["small"], WHITE, 20, 20, align="left", outline_color=BLACK)
            if self.game.assets.ui_ball:
                self.game.screen.blit(self.game.assets.ui_ball, (20 + self.game.assets.fonts["small"].size(lbl)[0] + 5, 15))
            
            Utils.draw_text_outline(self.game.screen, "5 balls each", self.game.assets.fonts["tiny"], WHITE, self.menu_rect.centerx, self.menu_rect.bottom - 25)

        self.game.ui_manager.draw(self.game.screen)


# [REF-0035: Gym Lobby State]
class GymLobbyState(GameState):
    def __init__(self, game, previous_state=None):
        super().__init__(game)
        self.area_key = game.story_manager.current_area_key
        self.area_data = game.story_manager.get_current_area_data()
        self.gym_data = self.area_data.get("gym", {})
        
        self.bg = None
        first_part = self.area_key.split('_')[0].lower()
        bg_name = f"{first_part}_city_gym.png"
        path = os.path.join(game.assets.kanto_backgrounds_dir, bg_name)
        
        if os.path.exists(path):
            box_top = Utils.get_full_dialogue_rect(self.game).top
            self.bg = pygame.transform.scale(pygame.image.load(path).convert(), (self.game.width, box_top))
        
        if not self.bg:
             self.bg = pygame.Surface((game.width, int(game.height * 0.75)))
             self.bg.fill((40, 40, 60))

        self.prog_key = f"gym_progress_{self.area_key}"
        self.progress = game.story_manager.story_flags.get(self.prog_key, 0)
        self.trainers = self.gym_data.get("trainers", [])
        self.leader = self.gym_data.get("leader")
        
        self.next_opponent = None
        self.is_cleared = False
        
        if self.progress < len(self.trainers):
            self.next_opponent = self.trainers[self.progress]
            self.status_text = f"Trainer {self.progress + 1}/{len(self.trainers) + 1} is up next!"
        elif self.progress == len(self.trainers) and self.leader:
            self.next_opponent = self.leader
            self.status_text = "The Gym Leader is ready for you."
        else:
            self.is_cleared = True
            self.status_text = "You have defeated this Gym!"

        self.bottom_rect = Utils.get_full_dialogue_rect(game)
        self.right_rect = pygame.Rect(
            self.bottom_rect.x + int(self.bottom_rect.width * 0.55),
            self.bottom_rect.y,
            self.bottom_rect.width - int(self.bottom_rect.width * 0.55),
            self.bottom_rect.height
        )

        self.btn_challenge = Button(
            rect=(self.right_rect.centerx - 100, self.right_rect.y + 25, 200, 60),
            text="CHALLENGE",
            font=game.assets.fonts["s_med"],
            callback=self.challenge_gym,
            bg_color=RED if not self.is_cleared else GRAY
        )
        
        self.btn_exit = Button(
            rect=(self.right_rect.centerx - 100, self.right_rect.y + 100, 200, 60),
            text="EXIT GYM",
            font=game.assets.fonts["s_med"],
            callback=self.exit_gym,
            bg_color=BLUE
        )

    def start(self):
        self.game.ui_manager.elements.clear()
        self.game.ui_manager.add_element(self.btn_challenge)
        self.game.ui_manager.add_element(self.btn_exit)

    def challenge_gym(self):
        if self.is_cleared or not self.next_opponent:
            return

        t_data = self.next_opponent
        from src.states.battle import TrainerBattleState, TrainerIntroState
        
        team_ids = t_data.get("team", [])
        if team_ids and isinstance(team_ids, list) and len(team_ids) > 0 and isinstance(team_ids[0], list):
            team_ids = random.choice(team_ids)

        opponent_team = []
        for pid in team_ids:
            raw = self.game.loader.fetch_specific(pid)
            opponent_team.append(Pokemon(raw, self.game.assets, size_mult=3.125))

        sprite_name = t_data.get("sprite")
        trainer_sprite = self.game.assets.get_trainer_image(sprite_name)
        
        # Determine dynamic background (Handles Elite 4 progression)
        is_leader = (self.next_opponent == self.leader)
        bg_file = self.game.story_manager.get_gym_battle_background(self.area_key, self.progress, is_leader)

        battle_state = TrainerBattleState(
            self.game,
            opponent_team,
            trainer_sprite=trainer_sprite,
            trainer_class=t_data.get("class", "TRAINER"),
            trainer_name=t_data.get("name"),
            custom_dialogue=t_data.get("dialogue", {}),
            rewards=t_data.get("rewards"),
            battle_type="gym",
            area_name=self.area_key,
            badge_reward=t_data.get("badge_reward"),
            background_image=bg_file
        )

        intro_text = random.choice(t_data.get("dialogue", {}).get("intro", ["Prepare to battle!"]))
        self.game.change_state(TrainerIntroState(self.game, trainer_sprite, intro_text, battle_state))

    def exit_gym(self):
        self.game.change_state(CityState(self.game))

    def handle_events(self, events):
        pass

    def update(self):
        pass

    def draw(self):
        self.game.screen.fill(BLACK)
        if self.bg:
            self.game.screen.blit(self.bg, (0, 0))
            
        Utils.draw_classic_panel(
            self.game.screen, self.bottom_rect.x, self.bottom_rect.y, self.bottom_rect.width, self.bottom_rect.height
        )

        left_rect_w = int(self.bottom_rect.width * 0.55)
        Utils.draw_multiline_text(
            self.game.screen,
            self.status_text,
            self.game.assets.fonts["med"],
            WHITE,
            self.bottom_rect.x + left_rect_w // 2,
            self.bottom_rect.centery,
            max_width=left_rect_w - 60,
            line_height=50,
            center=True,
            outline_color=BLACK,
        )

        white_panel = self.right_rect.inflate(-18, -18)
        pygame.draw.rect(self.game.screen, WHITE, white_panel, border_radius=12)
        pygame.draw.rect(self.game.screen, BLACK, white_panel, 6, border_radius=12)

        self.game.ui_manager.draw(self.game.screen)
