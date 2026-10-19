# [REF-0001: System Imports]
import pygame
import random
from src.states.base import GameState
from src.utils import Utils
from src.vfx.renderer import BattleRenderer
from src.ui.panels import BattleActionMenu
from src.ui.widgets import MathBattleUI, Button
from src.ui.dialogue import ClassicDialogueBox
from src.pokemon.mechanics import TypeAdvantage
from src.vfx.animations import AnimationController, FaintAnimation, PokemonSummonAnimation
from src.config import WHITE, BLACK, GREEN, RED, GOLD, FPS


# [REF-0024: Trainer Battle Core]
class TrainerBattleState(GameState):
    def __init__(
        self,
        game,
        opponent_data,
        trainer_img_name=None,
        trainer_sprite=None,
        trainer_class="RIVAL",
        trainer_index=None,
        trainer_name=None,
        custom_dialogue=None,
        rewards=None,
        is_boss_battle=False,
        battle_type=None,
        area_name=None,
        victory_flag=None,
        badge_reward=None,
        background_image=None,
    ):
        super().__init__(game)

        if isinstance(opponent_data, list):
            self.opponent_team = opponent_data
        else:
            self.opponent_team = [opponent_data]

        self.current_opponent_idx = 0
        self.opponent_pokemon = self.opponent_team[0] if self.opponent_team else None

        self.player_pokemon = self.game.story_manager.player_team[0] if self.game.story_manager.player_team else None

        # [FIX] Implement "disallow previous region's pokemon" logic
        current_region = self.game.story_manager.get_current_region()
        player_team = self.game.story_manager.player_team
        pc_pokemon = self.game.story_manager.pc_pokemon
        
        # Filter out fainted Pokémon and those from previous regions
        valid_party_pokemon = []
        for i, p in enumerate(player_team):
            if p and p.current_hp > 0:
                if p.caught_region is None or p.caught_region == current_region:
                    valid_party_pokemon.append(p)
                else:
                    # Move disallowed Pokémon to PC
                    for j in range(len(pc_pokemon)):
                        if pc_pokemon[j] is None:
                            pc_pokemon[j] = p
                            player_team[i] = None # Remove from party
                            break
                    else: # PC is full, just remove from party
                        player_team[i] = None
                    
                    # Inform player (this will be handled by a dialogue box later)
                    print(f"Moved {p.display_name} (from {p.caught_region}) to PC.")

        # Clean up player_team (remove None entries)
        self.game.story_manager.player_team = [p for p in player_team if p is not None]
        
        # Select the first valid Pokémon for battle
        if self.game.story_manager.player_team:
            self.player_pokemon = self.game.story_manager.player_team[0]
        else:
            # All Pokémon disallowed or fainted, force white-out
            self.player_pokemon = None 
            # This will be caught by the game loop and trigger a white-out
            # For now, set a flag to indicate this state
            self.game.story_manager.story_flags["forced_white_out"] = True
            print("All Pokémon disallowed or fainted, forcing white-out.")

        # End of "disallow previous region's pokemon" logic

        self.renderer = BattleRenderer(game)
        self.trainer_class = trainer_class
        self.trainer_index = trainer_index
        self.trainer_name = trainer_name
        self.custom_dialogue = custom_dialogue
        self.rewards = rewards if rewards else {"balls": 3}
        self.victory_flag = victory_flag
        self.badge_reward = badge_reward
        self.battle_type = battle_type
        self.area_name = area_name
        self.background = None

        bg_raw = None
        if background_image:
            bg_raw = self.game.assets.get_background(background_image, from_overworld=False)

        if not bg_raw:
            bg_raw = self.game.assets.get_random_battle_background(battle_type, area_name)

        if bg_raw:
            box_top = Utils.get_full_dialogue_rect(self.game).top
            self.background = pygame.transform.scale(bg_raw, (self.game.width, box_top))

        self.trainer_sprite = (
            trainer_sprite
            if trainer_sprite
            else (
                self.game.assets.get_trainer_image(trainer_img_name)
                if trainer_img_name
                else None
            )
        )
        self.is_trainer_battle = bool(self.trainer_sprite)
        area_key = self.game.story_manager.current_area_key

        self.turn_count = 0
        self.is_boss_battle = is_boss_battle
        self.boss_attack_timer = 0
        self.hard_mode = False

        boss_classes = ["GYM_LEADER", "ELITE_FOUR", "CHAMPION", "ROCKET_LEADER"]
        is_scripted_boss = (self.trainer_class == "WILD" and getattr(self, "victory_flag", None))

        if self.trainer_class in boss_classes or is_scripted_boss or self.is_boss_battle:
            self.hard_mode = True
        elif self.trainer_class == "RIVAL" and area_key != "PALLET_TOWN":
            self.hard_mode = True

        for p in self.opponent_team:
            self.game.data.mark_seen(p.id)

        self.setup_action_menu()

        self.phase = "MENU"
        self.player_won = False
        self.turn_actions = []
        self.anim_ctrl = AnimationController()
        self.faint_anim = FaintAnimation()
        self.fainting_side = None
        self.setup_battle_matchup()
        self.player_hits = 0
        self.questions_needed = 3
        self.problem_str, self.correct_ans, self.options = "", "", []
        self.math_ui = None
        self.feedback_text = ""
        self.feedback_timer = 0
        self.scr_shake_timer = 0
        self.pokemon_intro_timer = 0
        self.enemy_summon_anim = None
        self.player_summon_anim = None
        self.trainer_slide_offset = 400
        self.show_trainer = False
        self.transforming_side = None
        self.transform_anim_timer = 0
        self.transform_anim_duration = 90
        
        # [FIX] If forced white-out, skip normal battle setup and go straight to outro
        if self.game.story_manager.story_flags.get("forced_white_out", False):
            self.trigger_outro(win=False)

        main_rect = Utils.get_full_dialogue_rect(self.game)
        self.dialogue_box = ClassicDialogueBox(
            main_rect, [""], self.game.assets.fonts["med"]
        )

        if self.check_ditto_transform():
            if self.math_ui:
                self.math_ui.set_visibility(False)
        else:
            self.dialogue_box.visible = False
            self.setup_math_ui()

        self.btn_yes = Button(
            rect=(0, 0, 140, 60),
            text="YES",
            font=game.assets.fonts["small"],
            callback=None,
            bg_color=GREEN,
            visible=False,
            autosize=False
        )
        self.btn_no = Button(
            rect=(0, 0, 140, 60),
            text="NO",
            font=game.assets.fonts["small"],
            callback=None,
            bg_color=RED,
            visible=False,
            autosize=False
        )
        self.is_shift_switch = False

    def _get_capped_stage(self, pokemon):
        if getattr(pokemon, "raid_stage", None):
            return pokemon.raid_stage
        is_opponent_boss = self.is_boss_battle and (self.opponent_team and pokemon in self.opponent_team)
        if is_opponent_boss or pokemon.id in self.game.loader.all_boss_ids:
            return 3

        if hasattr(pokemon, "transformed_state") and hasattr(pokemon, "_stage_override"):
            base_stage = pokemon._stage_override
        else:
            base_stage = pokemon.effective_stage

        is_johto_battle = False

        if self.area_name:
            johto_indicators = ["JOHTO", "NEW_BARK", "CHERRYGROVE", "VIOLET",
                                "ALPH", "AZALEA", "GOLDENROD", "ECRUTEAK",
                                "OLIVINE", "CIANWOOD", "MAHOGANY",
                                "BLACKTHORN", "MT_SILVER", "UNION", "ILEX",
                                "SPROUT", "BURNED", "BELL", "MORTAR", "WHIRL",
                                "ROCKET", "DEN", "LAKE", "TOHJO"]
            if any(k in self.area_name for k in johto_indicators):
                is_johto_battle = True

        all_badges_dict = self.game.story_manager.badges
        if is_johto_battle:
            num_relevant_badges = len(all_badges_dict.get("JOHTO", []))
        else:
            num_relevant_badges = len(all_badges_dict.get("KANTO", []))

        if num_relevant_badges <= 1:
            stage_cap = 1
        elif num_relevant_badges <= 3:
            stage_cap = 2
        else:
            stage_cap = 3
        return min(base_stage, stage_cap)

    def check_ditto_transform(self):
        if self.phase == "DITTO_TRANSFORM":
            return True

        if self.player_pokemon.id == 132 and not hasattr(self.player_pokemon, "transformed_state"):
            self.transforming_side = 'player'
            self.phase = "DITTO_TRANSFORM"
            self.transform_anim_timer = self.transform_anim_duration
            self.dialogue_box.reset(f"{self.player_pokemon.name} transformed into {self.opponent_pokemon.name}!")
            self.dialogue_box.visible = True
            self.action_menu.set_visibility(False)
            return True

        if self.opponent_pokemon.id == 132 and not hasattr(self.opponent_pokemon, "transformed_state"):
            self.transforming_side = 'opponent'
            self.phase = "DITTO_TRANSFORM"
            self.transform_anim_timer = self.transform_anim_duration
            self.dialogue_box.reset(f"Foe {self.opponent_pokemon.name} transformed into {self.player_pokemon.name}!")
            self.dialogue_box.visible = True
            self.action_menu.set_visibility(False)
            return True

        return False

    def start_math_phase(self):
        self.phase = "BATTLE"
        self.action_menu.set_visibility(False)
        self.math_ui.set_visibility(True)
        self.dialogue_box.set_visibility(False)

    def trigger_outro(self, win):
        self.player_won = win
        if win:

            if self.custom_dialogue and "player_won" in self.custom_dialogue:
                text = self.custom_dialogue["player_won"]
            else:
                all_dialogue = self.game.loader.area_data.get("TRAINER_CLASS_DIALOGUE", {})
                lines = all_dialogue.get(self.trainer_class, {}).get("player_won", [])
                default_win_text = f"Player defeated {self.trainer_name or self.trainer_class}!"
                text = random.choice(lines) if lines else default_win_text

            self.phase = "VICTORY_TEXT"
            self.dialogue_box.is_finished = False
        else:
            if self.custom_dialogue and "player_lost" in self.custom_dialogue:
                lost_lines = self.custom_dialogue["player_lost"]
                lines = lost_lines if isinstance(lost_lines, list) else [lost_lines]
            else:
                all_dialogue = self.game.loader.area_data.get("TRAINER_CLASS_DIALOGUE", {})
                generic_lost = all_dialogue.get(self.trainer_class, {}).get("player_lost", ["..."])
                lines = [random.choice(generic_lost)]

            text = lines + ["Player is out of usable PKMN!", "Player whited out!"]
            self.phase = "OUTRO"

        self.dialogue_box.reset(text)
        self.dialogue_box.set_visibility(True)
        self.action_menu.set_visibility(False)
        if self.math_ui:
            self.math_ui.set_visibility(False)

    def setup_battle_matchup(self, reset_opponent_hp=True):
        type_advantage = TypeAdvantage(self.game.loader.area_data.get("TYPE_CHART", {}))
        player_types = self.player_pokemon.types
        opponent_types = self.opponent_pokemon.types

        best_opp_mult = 0.0
        p_types_check = player_types if player_types else ["NORMAL"]
        for p_t in p_types_check:
            best_opp_mult = max(best_opp_mult, type_advantage.get_multiplier(p_t, opponent_types))
        self.adv_opp = best_opp_mult if best_opp_mult > 0 else 1.0

        best_player_mult = 0.0
        o_types_check = opponent_types if opponent_types else ["NORMAL"]
        for o_t in o_types_check:
            best_player_mult = max(best_player_mult, type_advantage.get_multiplier(o_t, player_types))
        self.adv_player = best_player_mult if best_player_mult > 0 else 1.0

        opponent_stage = self._get_capped_stage(self.opponent_pokemon)

        self.player_max_hp = self.player_pokemon.get_max_hp()
        self.opp_max_hp = self.opponent_pokemon.get_max_hp(stage_override=opponent_stage)

        self.player_hp = max(0, self.player_pokemon.current_hp)
        if reset_opponent_hp:
            self.opponent_hp = self.opp_max_hp

    def _calculate_damage(self, stage, multiplier, attacker=None, defender=None):
        """
        Base damage scaled for HP 20/60/90 (decoupled from HP cap).
        Stage 1: Normal=7,  Super=10, NVE=4
        Stage 2: Normal=20, Super=28, NVE=12
        Stage 3: Normal=30, Super=42, NVE=18
        Stat ±1 modifier: attacker's best ATK vs defender's best DEF.
        """
        _NORMAL = (0, 7, 20, 30)
        _SUPER  = (0, 10, 28, 42)
        _NVE    = (0, 4, 12, 18)

        s = min(stage, 3)
        if multiplier > 1.0:
            table = _SUPER
        elif 0.0 < multiplier < 1.0:
            table = _NVE
        else:
            table = _NORMAL
        base = table[s]
        # Sub-stage growth: damage moves part-way toward the next stage's value.
        if attacker is not None and attacker.grows_toward_next_stage(s):
            base += (table[s + 1] - base) * attacker.sub_stage_fraction

        stat_mod = self._stat_mod(attacker, defender) if attacker and defender else 0

        spread = random.randint(-2, 2)
        self._last_was_crit = random.random() < 0.10
        crit_mult = 1.5 if self._last_was_crit else 1.0
        return max(1, int((base + stat_mod + spread) * crit_mult))

    def setup_math_ui(self):
        if hasattr(self, "math_ui") and self.math_ui in self.game.ui_manager.elements:
            self.game.ui_manager.elements.remove(self.math_ui)

        def callback(index):
            self.resolve_turn(self.options[index] == self.correct_ans)

        self.math_ui = MathBattleUI(self.game, self.problem_str, self.options, callback)
        self.game.ui_manager.add_element(self.math_ui)
        self.math_ui.set_visibility(False)

    def setup_action_menu(self):
        self.action_menu = BattleActionMenu(
            self.game,
            self.player_pokemon.display_name,
            on_math=lambda: self.start_math_phase(),
            on_pkdex=lambda: self._open_bag(),
            on_pkmn=lambda: self.open_party_menu(),
            on_run=lambda: self.handle_run(),
        )
        self.action_menu.set_visibility(True)

        if hasattr(self, 'game') and self.game.ui_manager:

            self.game.ui_manager.elements = [e for e in self.game.ui_manager.elements if not isinstance(e, BattleActionMenu)]
            self.game.ui_manager.add_element(self.action_menu)

    def _open_bag(self):
        from src.states.systems import BagState
        self.game.change_state(BagState(self.game, self, context="battle"))

    def on_item_used(self):
        """Called when an item is used from the bag during battle. Triggers opponent turn."""
        self.phase = "RESOLVE_TURN"
        self.turn_actions = [self.opponent_attack]
        self.game.change_state(self)

    def show_message(self, text, callback=None):
        self.phase = "MESSAGE"
        self.dialogue_box.reset(text)
        self.dialogue_box.callback = callback
        self.dialogue_box.set_visibility(True)
        self.action_menu.set_visibility(False)
        self.math_ui.set_visibility(False)

    def _get_play_state_instance(self):
        """Helper to get or create a PlayState instance for returning to overworld."""
        from src.states.overworld import PlayState
        if self.game.states.get("play"):
            return self.game.states["play"]
        else:
            return PlayState(self.game)

    def return_to_menu(self):
        self.phase = "MENU"
        self.action_menu.set_visibility(True)
        self.dialogue_box.set_visibility(False)

    def handle_run(self):
        if self.trainer_class == "WILD":
            self.show_message(
                "Got away safely!", callback=self.on_flee_complete
            )
        else:
            self.show_message(
                "No! You can't run from a trainer battle!",
                callback=self.return_to_menu
            )

    def on_flee_complete(self):
        pygame.event.clear()

        from src.states.overworld import PlayState
        next_state = self._get_play_state_instance()
        if hasattr(self, 'play_state_data') and self.play_state_data:
            next_state = PlayState(self.game, restore_data=self.play_state_data)
            self.game.states["play"] = next_state

        if next_state.check_for_evolution():
            return

        self.game.change_state(next_state)
        if hasattr(next_state, "show_progression_menu"):
            next_state.show_progression_menu()

    def open_party_menu(self):
        def on_switch_selected(slot_index):
            self.game.change_state(self)
            self.perform_switch(slot_index)

        from src.states.systems import PokemonPartyMenuState
        self.game.change_state(PokemonPartyMenuState(
            self.game,
            previous_state=self,
            context="battle_switch",
            on_select=on_switch_selected
        ))

    def perform_switch(self, slot_index, is_forced=False):
        team = self.game.story_manager.player_team
        self.old_pkmn = self.player_pokemon
        self.new_pkmn_switch = team[slot_index]
        self.is_forced_switch = is_forced

        self.phase = "RETRACT_ANIM"

        sprite = self.old_pkmn.back_image if self.old_pkmn.back_image else self.old_pkmn.image
        rect = sprite.get_rect(center=(self.game.width * 0.27, self.game.height * 0.69))
        self.faint_anim.start(sprite, rect.topleft)
        self.fainting_side = "player_switch"

        self.dialogue_box.reset(f"Come back, {self.old_pkmn.display_name}!")
        self.dialogue_box.set_visibility(True)
        self.action_menu.set_visibility(False)
        if self.math_ui:
            self.math_ui.set_visibility(False)

    def opponent_turn_after_switch(self):
        self.turn_actions.clear()
        self.turn_actions.append(self.opponent_attack)
        self.phase = "RESOLVE_TURN"
        self.feedback_timer = 0
        self.action_menu.set_visibility(False)

    def return_to_menu_after_forced_switch(self):
        self.phase = "MENU"
        self.action_menu.set_visibility(True)
        self.dialogue_box.set_visibility(False)
        play_state = self.game.states["play"]

        self.problem_str, self.correct_ans, self.options = play_state.generate_math_set(
             self.game.states["play"].total_caught, num_options=4
        )
        self.setup_math_ui()

        if self.action_menu in self.game.ui_manager.elements:
            self.game.ui_manager.elements.remove(self.action_menu)
        self.game.ui_manager.add_element(self.action_menu)

    def force_switch_menu(self):
        def on_switch_selected(slot_index):
            team = self.game.story_manager.player_team
            if team[slot_index].current_hp <= 0:
                self.game.show_dialogue([f"{team[slot_index].display_name.upper()} has no energy left!"])
                return

            self.game.change_state(self)
            self.perform_switch(slot_index, is_forced=True)

        from src.states.systems import PokemonPartyMenuState
        self.game.change_state(PokemonPartyMenuState(
            self.game,
            previous_state=self,
            context="forced_switch",
            on_select=on_switch_selected
        ))

    def start(self):
        self.problem_str, self.correct_ans, self.options = self.game.states[
            "play"
        ].generate_math_set(self.game.states["play"].total_caught, num_options=4)
        self.setup_math_ui()

        if self.area_name not in ["ELITE_FOUR", "KANTO_ROUTE_25"]:

            self.game.story_manager.set_checkpoint(
                TrainerBattleState,
                opponent_data=self.opponent_team,
                trainer_sprite=self.trainer_sprite,
                trainer_class=self.trainer_class,
                trainer_index=self.trainer_index,
                trainer_name=self.trainer_name,
                custom_dialogue=self.custom_dialogue,
                rewards=self.rewards,
                battle_type=self.battle_type,
                area_name=self.area_name,
                victory_flag=self.victory_flag,
                badge_reward=self.badge_reward
            )
        self.game.ui_manager.add_element(self.dialogue_box)
        self.game.ui_manager.add_element(self.action_menu)
        self.game.ui_manager.add_element(self.btn_yes)
        self.game.ui_manager.add_element(self.btn_no)

    def handle_events(self, events):
        if self.phase in ["OUTRO", "RESOLVE_TURN", "ENEMY_SUMMON", "VICTORY_TEXT", "REWARD_TEXT", "TRAINER_SLIDE_IN", "RETRACT_ANIM", "PLAYER_SUMMON"] or self.faint_anim.active:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                    if self.phase in ["OUTRO", "VICTORY_TEXT", "REWARD_TEXT", "ENEMY_SUMMON", "RESOLVE_TURN"]:
                        self.dialogue_box.handle_event(event)

                        if self.dialogue_box.is_finished:
                            if self.phase == "VICTORY_TEXT":
                                self.advance_victory_sequence()
                            elif self.phase == "REWARD_TEXT":
                                self.exit_battle()
                            elif self.phase == "OUTRO":
                                if self.player_won:

                                    self.exit_battle()
                                else:

                                    self.perform_battle_black_out()
            return

    def perform_battle_black_out(self):
        """Heals team and returns to the start of the current area."""
        for p in self.game.story_manager.player_team:
            p.current_hp = p.get_max_hp()
            if hasattr(p, "revert_transform"):
                p.revert_transform()

        area_key = self.game.story_manager.current_area_key
        prog_data = self.game.loader.area_data.get("STORY_PROGRESSION", {})
        area_info = prog_data.get(area_key, {})

        if area_info.get("area_type") == "town":
            from src.states.overworld import CityState
            self.game.change_state(CityState(self.game))
        else:
            from src.states.overworld import PlayState
            self.game.change_state(PlayState(self.game))

    def resolve_turn(self, player_was_correct):
        self.phase = "RESOLVE_TURN"
        self.turn_actions.clear()

        self.turn_count += 1
        if player_was_correct:
            self.turn_actions.append(self.player_attack)
            self.turn_actions.append(self.opponent_attack)
        else:
            self.turn_actions.append(self.opponent_attack)

        if self.math_ui:
            self.math_ui.set_visibility(False)

    @staticmethod
    def _stat_mod(attacker, defender):
        """+1 / 0 / -1 depending on attacker's best offense vs defender's best defense."""
        atk = max(attacker.get_stat("ATTACK"), attacker.get_stat("SPATK"))
        def_ = max(defender.get_stat("DEFENSE"), defender.get_stat("SPDEF"))
        return (atk > def_) - (atk < def_)

    def _award_battle_xp(self):
        """Give XP for the KO, scaled by relative stage and foe strength. Returns battle messages."""
        foe = self.opponent_pokemon
        foe_stage = self._get_capped_stage(foe)
        if self.game.story_manager.inventory.get("EXP_SHARE", 0) > 0:
            earners = [p for p in self.game.story_manager.player_team if p]
        else:
            earners = [self.player_pokemon]

        messages = []
        for p in earners:
            my_stage = self._get_capped_stage(p)
            foe_is_weak = self._stat_mod(foe, p) < 0
            gained = p.battle_xp(my_stage, foe_stage, foe_is_weak)
            grew = p.gain_xp(gained)
            if p is not self.player_pokemon:
                continue
            note = ""
            if foe_stage > my_stage:
                note = " Tough foe bonus!"
            elif foe_stage < my_stage or foe_is_weak:
                note = " (easy foe)"
            messages.append(f"{p.display_name.upper()} gained {gained} XP!{note}")
            if grew and p.sub_stage:
                messages.append(f"{p.display_name.upper()} grew a little stronger!")
        return messages

    def player_attack(self):
        if self.opponent_hp <= 0:
            return

        player_stage = self._get_capped_stage(self.player_pokemon)
        damage = self._calculate_damage(player_stage, self.adv_opp,
                                        self.player_pokemon, self.opponent_pokemon)
        self.opponent_hp = max(0, self.opponent_hp - damage)

        self.opponent_pokemon.current_hp = self.opponent_hp

        xp_messages = self._award_battle_xp() if self.opponent_hp <= 0 else []

        self.anim_ctrl.start_lunge("player")
        move_name = self.game.assets.get_stab_move(self.player_pokemon)

        if self.opponent_hp <= 0 and self.try_trigger_wild_catch_prompt():
            return

        messages = [self.game.assets.get_text(
            "used_move", name=self.player_pokemon.name, move=move_name
        )]

        if getattr(self, "_last_was_crit", False):
            messages.append("Critical hit!")
        if self.adv_opp > 1.0:
            messages.append("It's super effective!")
        elif self.adv_opp < 1.0 and self.adv_opp > 0.0:
            messages.append("It's not very effective...")

        if self.opponent_hp <= 0:
            self.fainting_side = "opponent"
            messages.append(f"Foe {self.opponent_pokemon.display_name.upper()} fainted!")
            messages.extend(xp_messages)
            self.dialogue_box.callback = self._start_faint_animation
            self.phase = "MESSAGE"

        self.dialogue_box.reset(messages)
        self.dialogue_box.set_visibility(True)
        self.feedback_timer = 30

    def opponent_attack(self):
        if self.player_hp <= 0:
            return

        opponent_stage = self._get_capped_stage(self.opponent_pokemon)
        damage = self._calculate_damage(opponent_stage, self.adv_player,
                                        self.opponent_pokemon, self.player_pokemon)
        self.player_hp = max(0, self.player_hp - damage)

        self.player_pokemon.current_hp = self.player_hp

        self.anim_ctrl.start_lunge("opponent")
        move_name = self.game.assets.get_stab_move(self.opponent_pokemon)

        messages = [self.game.assets.get_text(
            "used_move", name=f"Foe {self.opponent_pokemon.display_name}", move=move_name
        )]

        if getattr(self, "_last_was_crit", False):
            messages.append("Critical hit!")
        if self.adv_player > 1.0:
            messages.append("It's super effective!")
        elif self.adv_player < 1.0 and self.adv_player > 0.0:
            messages.append("It's not very effective...")

        if self.player_hp <= 0:
            self.fainting_side = "player"
            messages.append(f"{self.player_pokemon.display_name.upper()} fainted!")
            self.dialogue_box.callback = self._start_faint_animation
            self.phase = "MESSAGE"

        self.dialogue_box.reset(messages)
        self.dialogue_box.set_visibility(True)
        self.feedback_timer = 30

    def try_trigger_wild_catch_prompt(self):
        return False

    def _start_faint_animation(self):
        self.phase = "FAINT_ANIM_RUNNING"
        self.dialogue_box.callback = None
        if self.fainting_side == "opponent":
            target_pos = (self.game.width * 0.73, self.game.height * 0.39)
            pos = self.opponent_pokemon.image.get_rect(center=target_pos)
            self.faint_anim.start(self.opponent_pokemon.image, pos.topleft)
        elif self.fainting_side == "player":
            if self.player_pokemon and self.player_pokemon.back_image:
                p_img = self.player_pokemon.back_image
                target_p_pos = (self.game.width * 0.27, self.game.height * 0.69)
                player_pos = p_img.get_rect(center=target_p_pos)
                self.faint_anim.start(p_img, player_pos.topleft)

    def _calc_money_reward(self):
        total = sum(len(b) for b in self.game.story_manager.badges.values())
        if self.trainer_class == "CHAMPION":
            return 50000
        if self.trainer_class == "ELITE_FOUR":
            return 25000 + total * 500
        if self.trainer_class == "GYM_LEADER":
            return 5000 + total * 1000
        return 1000

    def _calc_candy_reward(self):
        total = sum(len(b) for b in self.game.story_manager.badges.values())
        if self.trainer_class == "CHAMPION":
            return 10
        if self.trainer_class == "ELITE_FOUR":
            return 4
        if self.trainer_class == "GYM_LEADER":
            return max(1, total // 4 + 1)
        return 0

    def advance_victory_sequence(self):
        if self.phase == "VICTORY_TEXT":
            self.phase = "REWARD_TEXT"
            msgs = []

            if self.badge_reward:
                badge_name = self.badge_reward.replace("_", " ").title()
                msgs.append(f"You received the {badge_name} Badge!")

            money_reward = self._calc_money_reward()
            if self.game.story_manager.inventory.get("AMULET_COIN", 0) > 0:
                money_reward *= 2
            msgs.append(f"You got ${money_reward:,} for winning!")

            candy = self._calc_candy_reward()
            if candy > 0:
                label = "Rare Candy" if candy == 1 else "Rare Candies"
                msgs.append(f"You received {candy} {label}!")

            balls = self.rewards.get("balls", 0)
            if balls > 0:
                msgs.append(f"You got {balls} Poké Balls!")

            key_items = self.game.loader.area_data.get("GAME_CONFIG", {}).get("KEY_ITEMS", [])
            for item, qty in self.rewards.items():
                if item == "balls":
                    continue

                if item in key_items and self.game.story_manager.inventory.get(item, 0) > 0:
                    msgs.append(f"You already have the {item.replace('_', ' ').title()}!")
                    msgs.append("You received 2 RARE CANDYs instead!")
                else:
                    name = item.replace("_", " ").title()
                    if qty == 1:
                        msgs.append(f"You received {name}!")
                    else:
                        msgs.append(f"You received {qty} {name}s!")

            self.dialogue_box.reset(msgs)

    def exit_battle(self):
        if self.trainer_index is not None:
            area_key = self.game.story_manager.current_area_key
            self.game.story_manager.mark_trainer_defeated(area_key, self.trainer_index)

        if self.victory_flag:
            self.game.story_manager.story_flags[self.victory_flag] = True

        if self.badge_reward:
            region = self.game.story_manager.get_current_region()
            if self.badge_reward not in self.game.story_manager.badges[region]:
                self.game.story_manager.badges[region].append(self.badge_reward)

        money_reward = self._calc_money_reward()
        if self.game.story_manager.inventory.get("AMULET_COIN", 0) > 0:
            money_reward *= 2
        self.game.story_manager.money += money_reward

        candy = self._calc_candy_reward()
        if candy > 0:
            inv = self.game.story_manager.inventory
            inv["RARE_CANDY"] = inv.get("RARE_CANDY", 0) + candy

        reward_balls = self.rewards.get("balls", 3)

        key_items = self.game.loader.area_data.get("GAME_CONFIG", {}).get("KEY_ITEMS", [])
        for item, qty in self.rewards.items():
            if item == "balls":
                continue

            if item in key_items and self.game.story_manager.inventory.get(item, 0) > 0:
                self.game.story_manager.inventory["RARE_CANDY"] = self.game.story_manager.inventory.get("RARE_CANDY", 0) + 2
            else:
                self.game.story_manager.inventory[item] = self.game.story_manager.inventory.get(item, 0) + qty

        if self.victory_flag == "beat_champion":
            from src.states.overworld import AreaTransitionState
            self.game.change_state(AreaTransitionState(self.game, "PALLET_TOWN", initial_message="You returned home to share your victory!"))
            return

        if self.battle_type == "gym":
            prog_key = f"gym_progress_{self.game.story_manager.current_area_key}"
            if self.player_won:
                self.game.story_manager.story_flags[prog_key] = self.game.story_manager.story_flags.get(prog_key, 0) + 1
            from src.states.overworld import GymLobbyState
            self.game.change_state(GymLobbyState(self.game, None))
            return

        if self.battle_type == "rival":
            if self.trainer_name == "SILVER":
                self.game.story_manager.story_flags["defeated_rival_johto"] = True
            else:
                self.game.story_manager.story_flags["defeated_rival_kanto"] = True

        if self.trainer_class == "RIVAL" and self.game.story_manager.current_area_key == "PALLET_TOWN":
            outcome = self.game.story_manager.get_victory_outcome(battle_type="rival")
            play_state_data = getattr(self, 'play_state_data', {})
            play_state_data['balls_left'] = play_state_data.get('balls_left', 0) + reward_balls + outcome.get("rewards", {}).get("balls", 5)
            from src.states.overworld import PlayState, AreaTransitionState
            self.game.states["play"] = PlayState(self.game, restore_data=play_state_data)

            next_area = outcome["next_area"]
            message = outcome.get("message")
            transition_state = AreaTransitionState(
                self.game,
                next_area,
                initial_message=message
            )

            self.game.change_state(transition_state)
            return

        play_state_data = getattr(self, 'play_state_data', {}).copy()
        play_state_data['balls_left'] = play_state_data.get('balls_left', 0) + reward_balls

        area_key = self.game.story_manager.current_area_key

        for p in self.game.story_manager.player_team:
            if hasattr(p, "revert_transform"):
                p.revert_transform()

        area_info = self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(area_key, {})

        if area_info.get("area_type") == "town":
            from src.states.overworld import CityState
            pygame.event.clear()
            self.game.states["city"] = CityState(self.game)
            next_state = self.game.states["city"]
        else:
            from src.states.overworld import PlayState
            pygame.event.clear()
            self.game.states["play"] = PlayState(self.game, restore_data=play_state_data)
            next_state = self.game.states["play"]

        if next_state and hasattr(next_state, "check_for_evolution"):
            if next_state.check_for_evolution():
                return

        self.game.change_state(next_state)

    def draw(self):
        screen = self.game.screen

        is_summoning_enemy = (self.phase == "ENEMY_SUMMON" and self.enemy_summon_anim is not None)
        is_summoning_player = (self.phase == "PLAYER_SUMMON")

        self.renderer.draw(
            screen,
            self.opponent_pokemon,
            self.player_pokemon,
            self.opponent_hp,
            self.player_hp,
            self.opp_max_hp,
            self.player_max_hp,
            self.adv_opp,
            self.adv_player,
            self.is_trainer_battle,

            self.trainer_sprite if (self.phase == "INTRO" or self.show_trainer) else None,
            self.background,
            anim_ctrl=self.anim_ctrl,
            fainting_side="player" if is_summoning_player else (self.fainting_side if (self.phase == "FAINT_ANIM_RUNNING" or self.phase == "RETRACT_ANIM") else None),
            trainer_x_offset=self.trainer_slide_offset,
            hide_opponent=is_summoning_enemy
        )

        if (self.phase == "FAINT_ANIM_RUNNING" or self.phase == "RETRACT_ANIM") and self.faint_anim.active:
            self.faint_anim.draw(screen)

        if self.phase == "ENEMY_SUMMON" and self.enemy_summon_anim:
            self.enemy_summon_anim.draw(screen)

        if self.phase == "PLAYER_SUMMON" and self.player_summon_anim:
            self.player_summon_anim.draw(screen)

        self.game.ui_manager.draw(screen)

    def update(self):
        self.anim_ctrl.update()

        if self.faint_anim.active:
            if self.faint_anim.update():
                if self.fainting_side == "player_switch":
                    self.player_pokemon = self.new_pkmn_switch

                    if self.check_ditto_transform():
                        pass
                    else:
                        self.setup_battle_matchup(reset_opponent_hp=False)
                        self.setup_action_menu()
                        self.action_menu.set_visibility(False)
                        self.phase = "PLAYER_SUMMON"
                        self.player_summon_anim = PokemonSummonAnimation(self.game, self.player_pokemon, "player", use_back_sprite=True)
                        self.dialogue_box.reset(f"Go! {self.player_pokemon.display_name}!")

                elif self.fainting_side == "player":
                    self.player_pokemon.current_hp = 0
                    can_continue = any(p.current_hp > 0 for p in self.game.story_manager.player_team)
                    if can_continue:
                        self.force_switch_menu()
                    else:
                        self.trigger_outro(win=False)
                else:
                    self.opponent_pokemon.current_hp = 0
                    if self.trainer_class == "WILD":
                        self.trigger_outro(win=True)
                    else:
                        if self.current_opponent_idx + 1 < len(self.opponent_team):
                            self.phase = "SWITCH_PROMPT"
                            next_poke = self.opponent_team[self.current_opponent_idx + 1]
                            box = self.dialogue_box.rect

                            btn_w, btn_h = 140, 60
                            self.btn_yes.rect = pygame.Rect(
                                box.right - 300,
                                box.bottom - 80,
                                btn_w, btn_h
                            )
                            self.btn_no.rect = pygame.Rect(
                                box.right - 140,
                                box.bottom - 80,
                                btn_w, btn_h
                            )

                            self.btn_yes.text = "YES"
                            self.btn_no.text = "NO"
                            self.btn_yes.callback = self.on_switch_yes
                            self.btn_no.callback = self.on_switch_no
                            self.btn_yes.set_visibility(True)
                            self.btn_no.set_visibility(True)

                            tr_display = (self.trainer_name
                                          or self.trainer_class)
                            msg = f"{tr_display} is about to use {next_poke.display_name}! Change PKMN?"
                            self.dialogue_box.reset(msg)
                            self.dialogue_box.set_visibility(True)
                            self.dialogue_box.callback = None
                        else:
                            self.phase = "TRAINER_SLIDE_IN"
                            self.trainer_slide_offset = 300
                            self.show_trainer = True
                self.fainting_side = None
            return

        if self.phase == "TRAINER_SLIDE_IN":
            self.trainer_slide_offset = max(0, self.trainer_slide_offset - 20)
            if self.trainer_slide_offset <= 0:
                self.current_opponent_idx += 1

                if self.current_opponent_idx < len(self.opponent_team):
                    self.opponent_pokemon = self.opponent_team[self.current_opponent_idx]

                    if not self.check_ditto_transform():
                        self.setup_battle_matchup()

                    self.enemy_summon_anim = PokemonSummonAnimation(self.game, self.opponent_pokemon, "opponent")
                    self.phase = "ENEMY_SUMMON"

                    display_name = self.trainer_name if self.trainer_name else self.trainer_class
                    if self.trainer_class == "RIVAL":
                        display_name = getattr(self.game, "rival_name", "BLUE")

                    msg = f"{display_name} sent out {self.opponent_pokemon.display_name.upper()}!"
                    self.dialogue_box.reset(msg)
                    self.dialogue_box.set_visibility(True)

                    self.show_trainer = False
                else:
                    self.trigger_outro(win=True)
            return

        if self.phase == "SWITCH_PROMPT":
            if self.dialogue_box.visible:
                self.dialogue_box.update()
            return

        if self.phase == "ENEMY_SUMMON":
            if self.dialogue_box.visible:
                self.dialogue_box.update()
            if self.enemy_summon_anim:
                self.enemy_summon_anim.update()
                if self.enemy_summon_anim.finished:
                    self.enemy_summon_anim = None

            if self.enemy_summon_anim is None and self.dialogue_box.is_finished:
                self.phase = "MENU"
                self.action_menu.set_visibility(True)
                self.dialogue_box.set_visibility(False)
                play_state = self.game.states["play"]
                p_set = play_state.generate_math_set(
                     self.game.states["play"].total_caught, num_options=4
                )
                self.problem_str, self.correct_ans, self.options = p_set
                self.setup_math_ui()
            return

        if self.phase == "PLAYER_SUMMON":
            if self.player_summon_anim:
                self.player_summon_anim.update()
                if self.player_summon_anim.finished:
                    self.player_summon_anim = None
                    if self.is_forced_switch:
                        self.return_to_menu_after_forced_switch()
                    elif self.is_shift_switch:
                        self.on_switch_no()
                    else:
                        self.opponent_turn_after_switch()
            return

        if self.phase == "DITTO_TRANSFORM":
            self.dialogue_box.update()
            if self.transform_anim_timer > 0:
                self.transform_anim_timer -= 1

            if self.transform_anim_timer <= 0 and self.dialogue_box.is_finished:
                if self.transforming_side == 'player':
                    self.player_pokemon.transform_into(self.opponent_pokemon)
                elif self.transforming_side == 'opponent':
                    self.opponent_pokemon.transform_into(self.player_pokemon)

                self.transforming_side = None
                self.setup_battle_matchup()

                if self.is_forced_switch:
                    self.return_to_menu_after_forced_switch()
                elif self.is_shift_switch:
                    self.opponent_turn_after_switch()
                else:
                    self.return_to_menu()
                    play_state = self.game.states["play"]
                    self.problem_str, self.correct_ans, self.options = (
                        play_state.generate_math_set(
                            self.game.states["play"].total_caught, num_options=4
                        ))
                    self.setup_math_ui()
            return

        if self.dialogue_box.visible:
            self.dialogue_box.update()

        if self.phase in ["INTRO", "OUTRO", "VICTORY_TEXT", "REWARD_TEXT"]:
            return

        if self.phase == "RESOLVE_TURN":
            if self.dialogue_box.visible:
                if not self.dialogue_box.is_finished:
                    return

            if self.feedback_timer == 0:
                self.dialogue_box.visible = False
                if self.turn_actions:
                    action = self.turn_actions.pop(
                        0
                    )
                    action()
                else:
                    self.phase = "MENU"
                    self.action_menu.set_visibility(True)
                    self.dialogue_box.set_visibility(False)
                    if self.player_hp > 0 and self.opponent_hp > 0:
                        (
                            self.problem_str,
                            self.correct_ans,
                            self.options,
                        ) = self.game.states["play"].generate_math_set(
                            self.game.states["play"].total_caught, num_options=4
                        )
                        self.setup_math_ui()

        if self.feedback_timer > 0:
            self.feedback_timer -= 1
        self.scr_shake_timer = self.anim_ctrl.impact_shake
        if self.pokemon_intro_timer > 0:
            self.pokemon_intro_timer -= 1

    def on_switch_yes(self):
        self.btn_yes.set_visibility(False)
        self.btn_no.set_visibility(False)

        def on_selected(slot_index):
            team = self.game.story_manager.player_team
            if team[slot_index] == self.player_pokemon:
                self.on_switch_no()
                return
            if team[slot_index].current_hp <= 0:
                self.game.show_dialogue([f"{team[slot_index].display_name} has no energy!"])
                return

            self.game.change_state(self)
            self.is_shift_switch = True
            self.perform_switch(slot_index)

        from src.states.systems import PokemonPartyMenuState
        self.game.change_state(
            PokemonPartyMenuState(
                self.game,
                self,
                context="battle_switch",
                on_select=on_selected,
                on_cancel=self.on_switch_no
            )
        )

    def on_switch_no(self):
        self.btn_yes.set_visibility(False)
        self.btn_no.set_visibility(False)
        self.is_shift_switch = False
        self.phase = "TRAINER_SLIDE_IN"
        self.trainer_slide_offset = 300
        self.show_trainer = True

    def _draw_transform_animation(self, surface):
        if not self.transforming_side:
            return

        progress = 1.0 - (self.transform_anim_timer / self.transform_anim_duration)

        if self.transforming_side == 'player':
            source_sprite = self.player_pokemon.back_image if self.player_pokemon.back_image else self.player_pokemon.image
            target_sprite = self.opponent_pokemon.image
            pos_rect = source_sprite.get_rect(center=(self.game.width * 0.27, self.game.height * 0.69))
        else:
            source_sprite = self.opponent_pokemon.image
            target_sprite = self.player_pokemon.back_image if self.player_pokemon.back_image else self.player_pokemon.image
            pos_rect = source_sprite.get_rect(center=(self.game.width * 0.73, self.game.height * 0.39))

        if progress < 0.5:
            sprite_to_pixelate = source_sprite
            pixelation_level = 1 + int(31 * (progress * 2))

        else:
            sprite_to_pixelate = target_sprite
            pixelation_level = 1 + int(31 * (1.0 - (progress - 0.5) * 2))

        if not sprite_to_pixelate:
            return

        pixelation_level = max(1, pixelation_level)
        w, h = sprite_to_pixelate.get_size()

        if w // pixelation_level <= 0 or h // pixelation_level <= 0:
            return

        temp_surf = pygame.transform.scale(sprite_to_pixelate, (w // pixelation_level, h // pixelation_level))
        final_surf = pygame.transform.scale(temp_surf, (w, h))

        surface.blit(final_surf, pos_rect)


# [REF-0025: Wild Battle Core]
class WildBattleState(TrainerBattleState):
    def __init__(self, game, pokemon, area_name, background_image=None, is_boss_battle=False):
        super().__init__(
            game,
            pokemon,
            trainer_img_name=None,
            trainer_class="WILD",
            battle_type="field",
            area_name=area_name,
            background_image=background_image,
            is_boss_battle=is_boss_battle
        )
        self.phase = "MENU"
        self.catch_phase = "DECISION"
        self.ball_pos = [0, 0]
        self.ball_target = [0, 0]
        self.shake_timer = 0
        self.ball_img = game.assets.ball_imgs[0]
        self.renderer = BattleRenderer(self.game)

        self.btn_yes.callback = self.catch_yes
        self.btn_no.callback = self.catch_no

    def try_trigger_wild_catch_prompt(self):
        if self.opponent_pokemon.id == 10500:
            return False
        if self.opponent_pokemon.id == 245 and not self.game.story_manager.story_flags.get("suicune_encountered"):
            return False

        if self.game.states["play"].balls_left > 0:
            self.phase = "CATCH_PROMPT"
            self.dialogue_box.reset(f"{self.opponent_pokemon.name} is weak! Throw ball?")
            self.catch_timer = 15 * FPS

            box = self.dialogue_box.rect
            btn_w, btn_h = 140, 60
            self.btn_yes.rect = pygame.Rect(box.right - 300, box.bottom - 80, btn_w, btn_h)
            self.btn_no.rect = pygame.Rect(box.right - 140, box.bottom - 80, btn_w, btn_h)

            self.btn_yes.set_visibility(True)
            self.btn_no.set_visibility(True)

            self.dialogue_box.set_visibility(True)
            self.action_menu.set_visibility(False)
            return True
        return False

    def attempt_run(self):
        self.dialogue_box.reset("Got away safely!")
        self.phase = "OUTRO"
        self.dialogue_box.callback = (
            lambda: self.game.story_manager.load_last_checkpoint(self.game)
        )

    def trigger_outro(self, win):
        if not win:
            self.player_won = False
            self.phase = "OUTRO"
            self.dialogue_box.reset("You fled or were defeated!")
            self.dialogue_box.set_visibility(True)
            return

        if self.opponent_pokemon.id == 10500:
            if self.victory_flag:
                self.game.story_manager.story_flags[self.victory_flag] = True

            self.player_won = True
            self.phase = "OUTRO"
            self.dialogue_box.reset("The restless spirit was pacified!")
            self.dialogue_box.callback = self._on_catch_exit
            self.dialogue_box.set_visibility(True)
            return

        if self.opponent_pokemon.id == 245 and not self.game.story_manager.story_flags.get("suicune_encountered"):
            self.game.story_manager.story_flags["suicune_encountered"] = True
            self.player_won = True
            self.phase = "OUTRO"
            self.dialogue_box.reset(["SUICUNE stared intensely...", "It scattered before a ball could be thrown!"])
            self.dialogue_box.callback = self._on_catch_exit
            return

        if self.game.states["play"].balls_left > 0:
            self.phase = "CATCH_PROMPT"
            self.dialogue_box.reset(f"Will you catch {self.opponent_pokemon.name}?")
            self.catch_timer = 15 * FPS

            box = self.dialogue_box.rect
            btn_w, btn_h = 140, 60

            self.btn_yes.rect = pygame.Rect(
                box.right - 300, box.bottom - 80, btn_w, btn_h
            )
            self.btn_no.rect = pygame.Rect(
                box.right - 140, box.bottom - 80, btn_w, btn_h
            )

            self.btn_yes.set_visibility(True)
            self.btn_no.set_visibility(True)
        else:
            self.game.change_state(self.game.states["play"])

    def _raid_catch_to_party_pokemon(self, boss):
        """A caught raid boss joins as a normal-size, normal-form Pokemon; G-Max bosses keep the G-Max Factor."""
        from src.pokemon.data import Pokemon
        raw = self.game.loader.fetch_specific(boss.id, form="normal", is_shiny=boss.is_shiny)
        pokemon = Pokemon(raw, self.game.assets, size_mult=2.5)
        pokemon.is_shiny = boss.is_shiny
        pokemon.gmax_factor = boss.form == "gmax"
        return pokemon

    def catch_yes(self):
        self.phase = "CATCH_ANIMATION"
        self.catch_phase = "THROWN"
        self.game.states["play"].balls_left -= 1

        self.btn_yes.set_visibility(False)
        self.btn_no.set_visibility(False)

        self.anim_ctrl.impact_shake = 0

        self.ball_pos = [self.game.width * 0.27, self.game.height * 0.69]
        self.ball_target = [self.game.width * 0.73, self.game.height * 0.39]

    def catch_no(self):
        self.btn_yes.set_visibility(False)
        self.btn_no.set_visibility(False)
        self.show_message("Got away safely!", callback=self.on_flee_complete)

    def update(self):
        if self.phase == "CATCH_PROMPT":
            self.catch_timer -= 1
            if self.catch_timer <= 0:
                self.catch_no()
                return
            self.dialogue_box.update()
            return

        if self.phase == "CATCH_ANIMATION":
            if self.catch_phase == "THROWN":
                self.ball_pos[0] += (self.ball_target[0] - self.ball_pos[0]) * 0.15
                self.ball_pos[1] += (self.ball_target[1] - self.ball_pos[1]) * 0.15

                if abs(self.ball_pos[1] - self.ball_target[1]) < 10:
                    self.catch_phase = "SHAKE"
                    self.shake_timer = 60
            elif self.catch_phase == "SHAKE":
                self.shake_timer -= 1
                if self.shake_timer <= 0:
                    success = True

                    if success:
                        if self.victory_flag:
                            self.game.story_manager.story_flags[self.victory_flag] = True
                            if self.opponent_pokemon.name == "SNORLAX":
                                self.game.story_manager.story_flags["caught_snorlax"] = True

                        caught = self.opponent_pokemon
                        if getattr(caught, "raid_stage", None):
                            caught = self._raid_catch_to_party_pokemon(caught)

                        self.player_won = True
                        self.catch_phase = "CAUGHT"
                        self.dialogue_box.reset(
                            self.game.assets.get_text(
                                "caught_pokemon", name=self.opponent_pokemon.name
                            )
                        )
                        self.game.states["play"].p_data = [
                            None,
                            caught,
                            None,
                        ]
                        self.game.states["play"].complete_catch(1)

                        if hasattr(self.opponent_pokemon, "revert_transform"):
                            self.opponent_pokemon.revert_transform()

                        self.phase = "OUTRO"
                        self.dialogue_box.callback = self._on_catch_exit
                    else:
                        self.resolve_turn(True)
            return

        super().update()

    def _on_catch_exit(self):
        from src.states.overworld import PlayState
        next_state = self._get_play_state_instance()
        if hasattr(self, 'play_state_data') and self.play_state_data:
            next_state = PlayState(self.game, restore_data=self.play_state_data)
            self.game.states["play"] = next_state

        if next_state.check_for_evolution():
            return
        pygame.event.clear()
        self.game.change_state(next_state)
        if hasattr(next_state, "show_progression_menu"):
            next_state.show_progression_menu()

    def handle_events(self, events):
        if self.phase == "CATCH_ANIMATION":
            return

        super().handle_events(events)

    def start(self):
        super().start()

    def draw(self):
        screen = self.game.screen

        hide_opponent = (self.phase == "CATCH_ANIMATION" and self.catch_phase in ["SHAKE", "CAUGHT"]) or \
                        (self.phase == "OUTRO" and self.catch_phase == "CAUGHT")

        self.renderer.draw(
            screen,
            self.opponent_pokemon,
            self.player_pokemon,
            self.opponent_hp,
            self.player_hp,
            self.opp_max_hp,
            self.player_max_hp,
            self.adv_opp,
            self.adv_player,
            self.is_trainer_battle,
            self.trainer_sprite if self.phase == "INTRO" else None,
            self.background,
            anim_ctrl=self.anim_ctrl,
            fainting_side="opponent" if hide_opponent else ("player" if self.phase == "PLAYER_SUMMON" else (self.fainting_side if self.phase == "FAINT_ANIM_RUNNING" else None)),
            hide_opponent=hide_opponent
        )

        if (self.phase == "FAINT_ANIM_RUNNING" or self.phase == "RETRACT_ANIM") and self.faint_anim.active:
            self.faint_anim.draw(screen)

        self.game.ui_manager.draw(screen)

        if self.phase == "CATCH_PROMPT":
            bar_w = 200
            bar_h = 10
            ratio = self.catch_timer / (15 * FPS)
            pygame.draw.rect(screen, BLACK, (self.game.width//2 - bar_w//2, self.game.height - 120, bar_w, bar_h))
            pygame.draw.rect(screen, GOLD, (self.game.width//2 - bar_w//2, self.game.height - 120, int(bar_w * ratio), bar_h))

        if self.phase == "CATCH_ANIMATION":
            if self.catch_phase == "THROWN":
                self.game.screen.blit(
                    self.ball_img, (self.ball_pos[0] - 42, self.ball_pos[1] - 42)
                )
            elif self.catch_phase == "SHAKE":
                shake_offset = 0
                if self.shake_timer > 0 and self.shake_timer % 20 > 10:
                    shake_offset = random.randint(-5, 5)
                self.game.screen.blit(
                    self.ball_img,
                    (self.ball_target[0] - 42 + shake_offset, self.ball_target[1] - 42),
                )


# [REF-0026: Battle Intro State]
class TrainerIntroState(GameState):
    def __init__(self, game, trainer_sprite, dialogue_text, next_state):
        super().__init__(game)
        self.next_state = next_state
        self.input_delay = 20
        self.trainer_sprite = trainer_sprite
        self.vs_alpha = 255
        self.sprites_in_place = False
        self.phase = "VS"
        self.player_summon = None
        self.enemy_summon = None
        self.slide_offset = 0
        self.pokemon_slide_t = 0.0
        self.battle_bg = None
        main_rect = Utils.get_full_dialogue_rect(game)
        self.dialogue_box = ClassicDialogueBox(
            main_rect, dialogue_text, self.game.assets.fonts["med"],
            callback=self.on_dialogue_finish
        )
        self.dialogue_box.visible = False

        self.player_sprite = None
        char_key = getattr(self.game, "player_character", "red")
        img = self.game.assets.get_player_image(char_key, back=False)
        if img:
            h = int(self.game.height * 0.6)
            w = int(img.get_width() * (h / img.get_height()))
            self.player_sprite = pygame.transform.scale(img, (w, h))

        self.rival_sprite = self.trainer_sprite

        self.player_team_count = len(game.story_manager.player_team)
        self.opponent_team_count = len(getattr(next_state, 'opponent_team', []))
        self.ball_icon = pygame.transform.scale(game.assets.ball_imgs[0], (20, 20))

    def on_dialogue_finish(self):
        if not self.next_state.player_pokemon or not self.next_state.opponent_pokemon:
            self.game.change_state(self.next_state)
            return
        self.phase = "SUMMON"
        self.dialogue_box.visible = False

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        if self.next_state and hasattr(self.next_state, 'background') and self.next_state.background:
            self.battle_bg = self.next_state.background
        else:
            battle_type = getattr(self.next_state, "battle_type", "field")
            area_name = getattr(self.next_state, "area_name", "")
            bg_raw = self.game.assets.get_random_battle_background(battle_type, area_name)
            if bg_raw:
                box_top = Utils.get_full_dialogue_rect(self.game).top
                self.battle_bg = pygame.transform.scale(bg_raw, (self.game.width, box_top))
            else:
                self.battle_bg = None

    def handle_events(self, events):
        if self.input_delay > 0:
            return
        for event in events:
            if self.dialogue_box.visible and event.type == pygame.MOUSEBUTTONDOWN:
                self.dialogue_box.handle_event(event)

    def update(self):
        if self.input_delay > 0:
            self.input_delay -= 1

        if self.dialogue_box.visible:
            self.dialogue_box.update()

        if self.phase == "VS":
            self.vs_alpha = max(0, self.vs_alpha - 6)
            if self.vs_alpha <= 0:
                self.phase = "DIALOGUE"
                self.dialogue_box.visible = True

        elif self.phase == "DIALOGUE":
            pass

        elif self.phase == "SUMMON":
            if not self.player_summon:
                player_pkmn = self.next_state.player_pokemon
                enemy_pkmn = self.next_state.opponent_pokemon
                self.player_summon = PokemonSummonAnimation(self.game, player_pkmn, "player", use_back_sprite=False)
                self.enemy_summon = PokemonSummonAnimation(self.game, enemy_pkmn, "opponent")

                player_text = f"Go, {player_pkmn.display_name.upper()}!"

                r_name = getattr(self.next_state, "trainer_name", None)
                if not r_name:
                    r_name = getattr(self.next_state, "trainer_class", "TRAINER")
                    if r_name == "RIVAL":
                        r_name = getattr(
                            self.game,
                            "rival_name",
                            getattr(self.game, "rival_character", "BLUE")
                        )

                rival_name = str(r_name).upper()
                rival_text = f"{rival_name} sent out {enemy_pkmn.display_name.upper()}!"
                self.dialogue_box.reset([player_text, rival_text])
                self.dialogue_box.visible = True
                self.dialogue_box.callback = None

            if self.player_summon:
                self.player_summon.update()
            if self.enemy_summon:
                self.enemy_summon.update()
            if self.dialogue_box.visible:
                self.dialogue_box.update()

            if self.player_summon and self.enemy_summon and self.player_summon.finished and self.enemy_summon.finished and self.dialogue_box.is_finished:
                self.phase = "SLIDE_OUT"
                self.dialogue_box.reset("")
                self.dialogue_box.visible = False

        elif self.phase == "SLIDE_OUT":
            self.slide_offset += 25
            max_slide = (self.game.width // 2 + 100)
            self.pokemon_slide_t = min(1.0, self.slide_offset / max_slide)
            if self.slide_offset >= max_slide:
                self.game.change_state(self.next_state)

    def draw(self):
        screen = self.game.screen

        if self.phase == 'VS':
            screen.fill(BLACK)
        else:
            if self.battle_bg:
                screen.blit(self.battle_bg, (0, 0))
            else:
                screen.fill((20, 40, 80))

            dialogue_rect = Utils.get_full_dialogue_rect(self.game)
            Utils.draw_classic_panel(screen, dialogue_rect.x, dialogue_rect.y, dialogue_rect.width, dialogue_rect.height)

        player_pos = (self.game.width * 0.25 - self.slide_offset, self.game.height * 0.75)
        rival_pos = (self.game.width * 0.75 + self.slide_offset, self.game.height * 0.75)

        if self.player_sprite:
            screen.blit(self.player_sprite, self.player_sprite.get_rect(midbottom=player_pos))
            if self.phase in ['VS', 'DIALOGUE']:
                start_x = player_pos[0] - 60
                y_pos = player_pos[1] - self.player_sprite.get_height() - 40
                for i in range(6):
                    bx = start_x + (i * 22)
                    if i < self.player_team_count:
                        screen.blit(self.ball_icon, (bx, y_pos))
                    else:
                        pygame.draw.circle(screen, (100, 100, 100), (bx + 10, y_pos + 10), 8)

                Utils.draw_text_outline(
                    screen,
                    self.game.player_name.upper(),
                    self.game.assets.fonts["s_med"],
                    WHITE,
                    player_pos[0],
                    player_pos[1] - self.player_sprite.get_height() - 10)

        if self.rival_sprite:
            screen.blit(self.rival_sprite, self.rival_sprite.get_rect(midbottom=rival_pos))
            if self.phase in ['VS', 'DIALOGUE']:
                start_x = rival_pos[0] - 60
                y_pos = rival_pos[1] - self.rival_sprite.get_height() - 40
                for i in range(6):
                    bx = start_x + (i * 22)
                    if i < self.opponent_team_count:
                        screen.blit(self.ball_icon, (bx, y_pos))
                    else:
                        pygame.draw.circle(screen, (100, 100, 100), (bx + 10, y_pos + 10), 8)

                opponent_name = getattr(self.next_state, "trainer_name", None)
                if not opponent_name:
                    opponent_name = getattr(self.next_state, "trainer_class", "TRAINER")

                Utils.draw_text_outline(
                    screen,
                    opponent_name.upper(),
                    self.game.assets.fonts["s_med"],
                    WHITE,
                    rival_pos[0],
                    rival_pos[1] - self.rival_sprite.get_height() - 10)

        if self.phase == "VS" and self.vs_alpha > 0:
            Utils.draw_text_outline(screen, "VS", self.game.assets.fonts["big"], GOLD,
                                    self.game.width//2, self.game.height//2, BLACK, 5)

        if self.phase == "SUMMON":
            if self.player_summon:
                self.player_summon.draw(screen)
            if self.enemy_summon:
                self.enemy_summon.draw(screen)

        if self.phase == "SLIDE_OUT":

            t = self.pokemon_slide_t
            w, h = self.game.width, self.game.height

            start_x, start_y = w * 0.35, h * 0.55 - 20
            end_x, end_y = w * 0.27, h * 0.69

            cur_x = start_x + (end_x - start_x) * t
            cur_y = start_y + (end_y - start_y) * t

            p_pkmn = self.next_state.player_pokemon
            if p_pkmn:
                if t < 0.5:
                    sprite = p_pkmn.image
                    scale_x = max(0.0, 1.0 - (t * 2.0))
                else:
                    sprite = p_pkmn.back_image if p_pkmn.back_image else p_pkmn.image
                    scale_x = max(0.0, (t - 0.5) * 2.0)

                if sprite:
                    sw, sh = sprite.get_size()
                    scaled_w = int(sw * scale_x)
                    if scaled_w > 0:
                        scaled = pygame.transform.scale(sprite, (scaled_w, sh))
                        screen.blit(scaled, scaled.get_rect(center=(cur_x, cur_y)))

            o_pkmn = self.next_state.opponent_pokemon
            if o_pkmn and o_pkmn.image:
                start_ox, start_oy = w * 0.65, h * 0.55 - 20
                end_ox, end_oy = w * 0.73, h * 0.39
                cur_ox = start_ox + (end_ox - start_ox) * t
                cur_oy = start_oy + (end_oy - start_oy) * t
                screen.blit(o_pkmn.image, o_pkmn.image.get_rect(center=(cur_ox, cur_oy)))

        if self.dialogue_box.visible:
            self.dialogue_box.draw(screen)


# [REF-0027: Battle Victory State]
class TrainerVictoryState(GameState):
    def __init__(self, game, trainer_sprite, victory_dialogue, next_state):
        super().__init__(game)
        self.trainer_sprite = trainer_sprite
        self.dialogue_box = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(game),
            victory_dialogue,
            game.assets.fonts["med"],
            callback=lambda: game.change_state(next_state)
        )

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)

    def handle_events(self, events):
        pass

    def update(self):
        self.dialogue_box.update()

    def draw(self):
        self.game.screen.fill(BLACK)
        if self.trainer_sprite:
            self.game.screen.blit(self.trainer_sprite, self.trainer_sprite.get_rect(center=(self.game.width//2, self.game.height*0.4)))
        self.dialogue_box.draw(self.game.screen)
