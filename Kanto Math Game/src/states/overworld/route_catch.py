"""The route screen's catch round: the math questions, right and wrong answers, and catching."""

import pygame
import random
from src.pokemon import catching
from src.pokemon import balance
from src.world import regional_forms
from src.vfx.particles import ShinyBurst, Starburst
from src.config import WHITE, GREEN, GOLD, RED, FPS


class RouteCatch:
    """Part of PlayState (route.py): its catch round."""

    def create_checkpoint(self):
        from src.states.overworld.route import PlayState
        self.game.story_manager.set_checkpoint(
            PlayState,
            total_caught=self.total_caught,
            balls_left=self.balls_left,
            current_streak=self.current_streak,
            rounds_completed=self.rounds_completed
        )
        self.game.story_manager.balls_left = self.balls_left
        self.game.story_manager.current_streak = self.current_streak

    def generate_math_set(self, score_unused=0, num_options=3):
        """Catching + battle questions. Difficulty comes from the player's
        OPTIONS setting (or AUTO = region + badges). See src/core/math_engine.py."""
        level = self.game.story_manager.get_math_level()
        return self.game.math.generate(level, num_options=num_options)

    def check_answer(self, pos):
        for i, btn_rect in enumerate(self.answer_btn_rects):
            if i >= len(self.p_data) or self.p_data[i] is None:
                continue

            if btn_rect.width > 0 and btn_rect.collidepoint(pos):
                story = self.game.story_manager
                ball = catching.selected(story)  # the ball you picked (BALL button)
                catching.use(story, ball)
                img = self.game.assets.get_item_image("POKE_BALL" if ball == catching.POKE else ball)
                size = self.game.assets.ball_imgs[0].get_size()
                self.current_ball_img = pygame.transform.scale(img, size) if img else self.game.assets.ball_imgs[0]
                self._thrown_ball = ball

                target_p_idx = self.selected_catch_idx if self.selected_catch_idx != -1 else i

                pi = (
                    self.boss_manager.boss_pokemon_data
                    if self.boss_manager.in_boss_mode
                    else self.p_data[target_p_idx]
                )
                if pi is None:
                    return
                is_shiny_catch = (
                    not self.boss_manager.in_boss_mode and pi and pi.is_shiny
                )
                is_correct_answer = self.options[i] == self.correct_ans
                story.note_answer(self.problem_str, is_correct_answer, (story.timer_frames(30) - self.question_timer) < 5 * FPS)

                self.was_shiny_override = is_shiny_catch and not is_correct_answer

                self._catch_roll = None
                if (is_correct_answer or is_shiny_catch) and not self.boss_manager.in_boss_mode:
                    # The games' catch formula: a right answer has weakened it to a quarter of its
                    # HP, a quick one (under 5 s) all the way to 1 HP.
                    quick = (self.game.story_manager.timer_frames(30) - self.question_timer) < 5 * FPS
                    max_hp = pi.get_max_hp()
                    terrain = self.area_data.get("battle_type", "")
                    self._catch_roll = catching.window_throw(
                        self.game, pi, ball, guaranteed=balance.is_legendary(pi.id),
                        hp=1 if quick else max(1, max_hp // 4), max_hp=max_hp, terrain=terrain)
                if is_correct_answer or is_shiny_catch:
                    self.handle_correct(target_p_idx, pi, is_shiny_catch, self.get_cx(target_p_idx))
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

    def check_team_hp(self):
        if not any(  # current HP (get_stat("HP") is the base stat, always > 0)
            pokemon.current_hp > 0
            for pokemon in self.game.story_manager.player_team
        ):
            self.show_dialogue(
                ["Your team is exhausted!", "Player whited out!"],
                callback=self.perform_black_out
            )
            return

    def perform_black_out(self):
        """Back to the last Pokemon Center (or home) with a healed team."""
        from src.states.overworld.area_transition import white_out
        white_out(self.game)

    def resolve_catch(self):
        if not self.flee_active:
            if 0 <= self.caught_idx < len(self.p_data) and self.p_data[self.caught_idx]:

                if self.p_data[self.caught_idx].cry:
                    self.p_data[self.caught_idx].cry.play()

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
                    self.question_timer = self.game.story_manager.timer_frames(30)

            else:
                self.problem_str, self.correct_ans, self.options = (
                    self.generate_math_set(self.total_caught)
                )
                self.question_timer = self.game.story_manager.timer_frames(30)

        elif not self.flee_active:
            roll = getattr(self, "_catch_roll", None)
            if roll and not roll[0]:  # it broke free: same Pokemon, another question
                from src.states.battle import WildBattleState
                self._retry_idx = self.caught_idx
                self.feedback_text = WildBattleState.BREAK_FREE[min(roll[1], 3)]
                self.feedback_color = RED
                return
            self.complete_catch(self.caught_idx)
            caught = self.p_data[self.caught_idx] if 0 <= self.caught_idx < len(self.p_data) else None
            catching.after_catch(self.game, caught, getattr(self, "_thrown_ball", None))

    def complete_catch(self, idx):
        pokemon_caught = self.p_data[idx]
        pokemon_was_kept = False
        # Friendship: every catch made with a Pokemon in the party brings it closer to you.
        for member in self.game.story_manager.player_team:
            if member and member is not pokemon_caught:
                member.friendship += 1
                member.counters["catches"] = member.counters.get("catches", 0) + 1

        pokemon_caught.caught_region = self.game.story_manager.get_current_region()
        pokemon_caught.caught_level = pokemon_caught.level  # no level evolution until its next level
        # Every catch is kept, duplicates too (Jordan's rule): branched lines (Ralts, Wurmple,
        # Snorunt, Clamperl, Applin, Burmy...) need a second copy. Full party -> the PC.
        is_new_species = not any(isinstance(v, dict) and v.get("id") == pokemon_caught.id
                                 for v in self.game.data.data.get("pokedex", {}).values())
        is_party_full = len(self.game.story_manager.player_team) >= 6

        msgs = []
        pokemon_was_kept = True
        if not is_party_full:
            self.game.story_manager.player_team.append(pokemon_caught)
            if self.was_shiny_override:
                msgs.append(self.game.assets.get_text("shiny_pass"))
            else:
                msgs.append(self.game.assets.get_text("caught_pokemon", name=pokemon_caught.display_name.upper()))
        else:
            self.game.story_manager.deposit_to_pc(pokemon_caught)
            msgs.append("Party is full.")
            msgs.append(f"{pokemon_caught.display_name.upper()} was sent to BILL'S PC!")

        self.total_caught += 1
        self.game.loader.total_caught = self.total_caught
        self.current_streak += 1

        pid_str = str(pokemon_caught.id)
        if pid_str == "201":
            f_name = "a" if pokemon_caught.form.lower() == "normal" else pokemon_caught.form.lower()
            catch_key = f"201_{f_name}"
            self.game.story_manager.catch_counts[catch_key] = self.game.story_manager.catch_counts.get(catch_key, 0) + 1
        else:
            self.game.story_manager.catch_counts[pid_str] = self.game.story_manager.catch_counts.get(pid_str, 0) + 1

        msgs += self.game.story_manager.catch_milestones()  # Kanto's catch missions (species owned)

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

        def post_catch_callback():
            self.check_for_evolution(force_catch_evo=True)

        msgs += regional_forms.check_completion(self.game)
        self.show_dialogue(msgs, callback=post_catch_callback)
        self.pause_timer = 90 if self.boss_manager.in_boss_mode else 40

    def _retry_catch(self, idx):
        """After a ball breaks open: the same Pokemon waits, here's another question."""
        self.feedback_text = ""
        self.caught_idx = -1
        self.catch_selection_active = False
        self.selected_catch_idx = idx
        self.problem_str, self.correct_ans, self.options = self.generate_math_set(self.total_caught, num_options=3)
        self.question_timer = self.game.story_manager.timer_frames(30)
        name = self.p_data[idx].display_name.upper() if self.p_data[idx] else "It"
        # Closing the line clears the box (a finished box stays up otherwise, hiding the new answers).
        self.show_dialogue([f"{name} broke free! Answer again to throw another ball."],
                           callback=lambda: setattr(self.dialogue_box, "visible", False))

    def reset_round(self):
        retry = getattr(self, "_retry_idx", None)
        self._retry_idx = None
        if (retry is not None and 0 <= retry < len(self.p_data) and self.p_data[retry]
                and catching.total_balls(self.game.story_manager) > 0):
            self._retry_catch(retry)
            return
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
            self.catch_selection_active,
            self.selected_catch_idx
        ) = ("", -1, False, [0, 0, 0], False, -1)
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
