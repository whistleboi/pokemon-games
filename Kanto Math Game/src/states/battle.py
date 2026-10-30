# [REF-0001: System Imports]
import pygame
import random
from src.states.base import GameState
from src.utils import Utils
from src.vfx.renderer import BattleRenderer
from src.ui.panels import BattleActionMenu, CommandButton
from src.ui import theme
from src.ui.widgets import MathBattleUI, Button, MoveButton, Backdrop
from src.ui.dialogue import ClassicDialogueBox
from src.pokemon.mechanics import TypeAdvantage
from src.pokemon import forms
from src.pokemon import catching
from src.states.battle_effects import MoveEffects, usable_status
from src.pokemon import balance
from src.pokemon import evolution
from src.pokemon import moves as movelib, affection
from src.world import levels
from src.vfx.animations import (AnimationController, FaintAnimation, PokemonSummonAnimation, battle_sprite,
                                battle_spot, sprite_rect)
from src.config import WHITE, BLACK, GREEN, RED, GOLD, FPS


# [REF-0024: Trainer Battle Core]
class TrainerBattleState(MoveEffects, GameState):
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
        starter_battle=False,
    ):
        super().__init__(game)
        # First rival battle with starters: Normal-type starter moves, and a loss still moves the story on.
        self.starter_battle = starter_battle

        if isinstance(opponent_data, list):
            self.opponent_team = opponent_data
        else:
            self.opponent_team = [opponent_data]

        self.current_opponent_idx = 0
        self.opponent_pokemon = self.opponent_team[0] if self.opponent_team else None

        self.player_pokemon = self.game.story_manager.player_team[0] if self.game.story_manager.player_team else None

        # Regions keep their own party, PC and Bag (StoryManager regional storage), so the party
        # is used as it is: no boxing Pokemon from another region at the start of a battle.
        story = self.game.story_manager
        story.story_flags.pop("forced_white_out", None)  # old saves stored this; it bricked battles
        team = [p for p in story.player_team if p is not None]
        story.player_team = team
        # The lead is the first Pokemon that can still fight. If none can, the battle ends at once
        # in a whiteout (set up below, once the dialogue box exists).
        self.no_usable_party = not any(p.current_hp > 0 for p in team)
        self.player_pokemon = next((p for p in team if p.current_hp > 0), team[0] if team else None)

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
            if not bg_raw and self.game.assets.generic_kind(background_image) == "battle_elite":
                bg_raw = self.game.assets.get_generic_background("battle_elite")

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
        self.weather = None
        self.weather_turns = 0
        self.weather_summoned = False
        self._turn_end_done = True
        # Mega Evolution / Primal Reversion (one per side per battle) and their extreme weather.
        self.mega_used = {"player": False, "opponent": False}
        self.chosen_move = None
        self.move_buttons = []
        # Per-battle feats for special evolutions (Sirfetch'd crits, Runerigus damage).
        self._battle_crits, self._battle_damage = {}, {}
        self._form_msgs = []
        self.weather_primal = None
        self._init_area_weather()
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

        self.btn_yes = CommandButton(
            rect=(0, 0, 180, 62),
            text="YES",
            font=game.assets.fonts["button"],
            callback=None,
            bg_color=theme.POKEMON,
            visible=False,
            autosize=False
        )
        self.btn_no = CommandButton(
            rect=(0, 0, 180, 62),
            text="NO",
            font=game.assets.fonts["button"],
            callback=None,
            bg_color=theme.FIGHT,
            visible=False,
            autosize=False
        )
        # A YES / NO prompt keeps its text clear of the buttons.
        self.dialogue_box.reserve = lambda: self._prompt_reserve() if self.btn_yes.visible else 0
        self.is_shift_switch = False
        self.is_forced_switch = False  # read when a Ditto's Transform finishes
        if self.no_usable_party:
            self.trigger_outro(win=False)  # nobody can fight: straight to the whiteout

    def _level(self, pokemon):
        return int(getattr(pokemon, "level", 5) or 5)

    def _obey_level(self):
        """Pokemon above this level may ignore the player (badges in this region raise it)."""
        return levels.obey_level(self.game.story_manager)

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

    TYPE_COLORS = {"NORMAL": (168, 168, 120), "FIRE": (240, 128, 48), "WATER": (104, 144, 240),
                   "ELECTRIC": (232, 196, 40), "GRASS": (120, 200, 80), "ICE": (120, 200, 200),
                   "FIGHTING": (192, 48, 40), "POISON": (160, 64, 160), "GROUND": (200, 168, 88),
                   "FLYING": (160, 144, 240), "PSYCHIC": (248, 88, 136), "BUG": (168, 184, 32),
                   "ROCK": (184, 160, 56), "GHOST": (112, 88, 152), "DRAGON": (112, 56, 248),
                   "DARK": (112, 88, 72), "STEEL": (160, 160, 192), "FAIRY": (238, 153, 172)}

    def _place_yes_no(self):
        """YES above NO at the right of the text box (the games' choice box), BALL beside them."""
        box = self.dialogue_box.rect
        w, h, pad, gap = 180, 62, 22, 12
        self.btn_yes.rect = pygame.Rect(box.right - pad - w, box.y + pad, w, h)
        self.btn_no.rect = pygame.Rect(box.right - pad - w, box.y + pad + h + gap, w, h)
        if hasattr(self, "btn_ball"):
            self.btn_ball.rect = pygame.Rect(self.btn_yes.rect.x - 16 - 290, box.centery - h // 2 - 2, 290, h)

    def _prompt_reserve(self):
        """Px of the text box the YES / NO (and BALL) buttons take up."""
        ball = getattr(self, "btn_ball", None)
        return self.dialogue_box.rect.right - (ball.rect.x if ball and ball.visible else self.btn_yes.rect.x) + 80  # (text starts 40 px in)

    def open_move_menu(self):
        """FIGHT: pick one of the four moves, then answer the math question to use it."""
        if self.phase != "MENU":
            return
        self.phase = "MOVE_SELECT"
        self.action_menu.set_visibility(False)
        self.dialogue_box.set_visibility(False)
        box = Utils.get_full_dialogue_rect(self.game)
        names = self._battle_moves(self.player_pokemon)
        pad, gap, back_w = 16, 10, 170
        bw = (box.width - pad * 3 - back_w - gap) // 2
        bh = (box.height - pad * 2 - gap - 4) // 2
        font, small = self.game.assets.fonts["button"], self.game.assets.fonts["label"]
        self._clear_move_buttons()
        self._move_backdrop = Backdrop(box)  # the white text box behind the moves
        self.game.ui_manager.add_element(self._move_backdrop)
        chart = TypeAdvantage(self.game.loader.area_data.get("TYPE_CHART", {}))
        own_types = {t.upper() for t in self.player_pokemon.types}
        for i, name in enumerate(names[:4]):
            d = movelib.info(self.game, name)
            power = d.get("power") or 0
            mtype = d.get("type")  # None for Struggle (typeless)
            effect = None
            if mtype and (power or name in movelib.FIXED_DAMAGE):
                eff = chart.get_multiplier(mtype, self.opponent_pokemon.types)
                effect = "super" if eff > 1 else "weak" if 0 < eff < 1 else "none" if eff == 0 else None
                detail = f"Power {power}" if power else "Fixed"
            elif name in movelib.WEATHER_MOVES:
                detail = "Weather"
            else:
                detail = movelib.STATUS_LABEL.get(d.get("ailment"), "STATUS").title()
            x = box.x + pad + (i % 2) * (bw + gap)
            y = box.y + pad + (i // 2) * (bh + gap)
            btn = MoveButton((x, y, bw, bh), name.replace("-", " "), font, small,
                             (lambda n=name: self.choose_move(n)), mtype or "???",
                             self.TYPE_COLORS.get(mtype, (120, 120, 120)), detail, effect,
                             stab=bool(power and mtype) and mtype.upper() in own_types)
            self.move_buttons.append(btn)
        from src.ui.panels import CommandButton
        back = CommandButton((box.right - pad - back_w, box.y + pad, back_w, box.height - pad * 2 - 4), "BACK",
                             self.game.assets.fonts["button"], self.close_move_menu, bg_color=(120, 124, 144),
                             autosize=False)
        self.move_buttons.append(back)
        for btn in self.move_buttons:
            self.game.ui_manager.add_element(btn)

    def _clear_move_buttons(self):
        for btn in self.move_buttons + [getattr(self, "_move_backdrop", None)]:
            if btn is not None and btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)
        self.move_buttons = []
        self._move_backdrop = None

    def close_move_menu(self):
        self._clear_move_buttons()
        self.return_to_menu()

    def choose_move(self, name):
        self._clear_move_buttons()
        self.chosen_move = name
        self.phase = "MENU"
        self.start_math_phase()

    def start_math_phase(self):
        self.phase = "BATTLE"
        self.action_menu.set_visibility(False)
        self.math_ui.set_visibility(True)
        self.dialogue_box.set_visibility(False)
        self._question_at = pygame.time.get_ticks()  # hidden timer for quick-answer bonuses

    def trigger_outro(self, win):
        self.player_won = win
        if win:
            self.game.music.victory()

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

            if self.starter_battle:
                text = lines + ["Your partner is worn out, but that was a great first battle!",
                                "Your team was healed. Time to set off on your journey!"]
            else:
                text = lines + ["Player is out of usable Pokémon!", "Player whited out!"]
            self.phase = "OUTRO"

        self.dialogue_box.reset(text)
        self.dialogue_box.set_visibility(True)
        self.action_menu.set_visibility(False)
        if self.math_ui:
            self.math_ui.set_visibility(False)

    # Each starter's first Normal-type move in its home game.
    STARTER_MOVES = {
        1: "Tackle", 4: "Scratch", 7: "Tackle", 152: "Tackle", 155: "Tackle", 158: "Scratch",
        252: "Pound", 255: "Scratch", 258: "Tackle", 387: "Tackle", 390: "Scratch", 393: "Pound",
        495: "Tackle", 498: "Tackle", 501: "Tackle", 650: "Tackle", 653: "Scratch", 656: "Pound",
        722: "Tackle", 725: "Scratch", 728: "Pound", 810: "Scratch", 813: "Tackle", 816: "Pound",
        906: "Scratch", 909: "Tackle", 912: "Pound",
    }

    def _pick_move(self, attacker, defender):
        """The opponent's choice (and a preview for the player): (name, type, effectiveness,
        category, power) for the move this Pokemon would use against the defender."""
        name = self._ai_choose(attacker, defender)
        d = movelib.info(self.game, name)
        chart = TypeAdvantage(self.game.loader.area_data.get("TYPE_CHART", {}))
        eff = chart.get_multiplier(d["type"], defender.types) if (d.get("power") or 0) else 1.0
        return name, d["type"], eff, d.get("category") or "PHYSICAL", d.get("power") or 0

    def _battle_moves(self, mon):
        """The moves a Pokemon can pick from in this battle."""
        if self.starter_battle:
            return [self.STARTER_MOVES.get(mon.id, "Tackle").upper().replace(" ", "-")]
        moves = movelib.ensure_moves(self.game, mon)
        foe = (self.opponent_pokemon if mon is getattr(self, "player_pokemon", None)
               else getattr(self, "player_pokemon", None))
        if foe is not None and not any(self._move_can_affect(n, foe) for n in moves):
            return [movelib.STRUGGLE]  # nothing it knows can touch the foe: Struggle instead
        return moves

    def _move_can_affect(self, name, defender):
        """False only when a move can never do anything to this defender (type immunity, or
        a status it can't get). Weather moves always do something."""
        if name in movelib.WEATHER_MOVES or name == movelib.STRUGGLE:
            return True
        d = movelib.info(self.game, name)
        chart = TypeAdvantage(self.game.loader.area_data.get("TYPE_CHART", {}))
        if (d.get("power") or 0) or name in movelib.FIXED_DAMAGE:
            return chart.get_multiplier(d["type"], defender.types) != 0
        return self._status_move_works(d, defender, ignore_current=True)

    def _forced_move(self, mon):
        """A two-turn move charged last turn fires now, whatever was picked."""
        return getattr(self, "_charging", {}).get(id(mon))

    @staticmethod
    def _hit_count(d):
        """Hits for a multi-hit move: 2-5 at 35/35/15/15% (Gen 5+), fixed for 2-hit moves."""
        hi = d.get("max_hits")
        if not hi:
            return 1
        lo = d.get("min_hits") or hi
        if (lo, hi) == (2, 5):
            return random.choices((2, 3, 4, 5), weights=(35, 35, 15, 15))[0]
        return random.randint(lo, hi)

    def _adjust_hp(self, mon, delta, floor=0):
        """Change a battler's HP from inside a move (recoil, drain). Like the games, recoil can
        knock the user out; the faint is handled at the end of the action (_start_pending_faint)."""
        if mon is self.player_pokemon:
            self.player_hp = max(min(floor, self.player_hp), min(self.player_max_hp, self.player_hp + delta))
            mon.current_hp = self.player_hp
        elif mon is self.opponent_pokemon:
            self.opponent_hp = max(min(floor, self.opponent_hp), min(self.opp_max_hp, self.opponent_hp + delta))
            mon.current_hp = self.opponent_hp

    def _ai_choose(self, attacker, defender):
        """Opponents pick the move that does the most damage (power x type x STAB x weather x
        accuracy); now and then they use a status or weather move instead, if it would work."""
        chart = TypeAdvantage(self.game.loader.area_data.get("TYPE_CHART", {}))
        scored = []
        for name in self._battle_moves(attacker):
            d = movelib.info(self.game, name)
            acc = (d.get("accuracy") or 100) / 100
            if (d.get("power") or 0) > 0:
                wm = self._weather_type_mult(d["type"])
                stab = 1.5 if d["type"] in (attacker.types or []) else 1.0
                score = d["power"] * chart.get_multiplier(d["type"], defender.types) * stab * wm * acc
            elif name in movelib.FIXED_DAMAGE:
                score = 60 * acc if chart.get_multiplier(d["type"], defender.types) else 0
            elif name in movelib.WEATHER_MOVES:
                w = movelib.WEATHER_MOVES[name]
                helps = {"RAIN": "WATER", "SUN": "FIRE", "SAND": "ROCK", "SNOW": "ICE"}[w] in (attacker.types or [])
                score = 45 if (helps and self.weather != w and not self.weather_primal) else 0
            elif self._can_inflict(d.get("ailment"), defender):
                score = 40 * acc
            else:
                score = self._status_score(name, d, attacker, defender) * acc
            scored.append((score, name))
        scored = [x for x in scored if x[0] > 0] or scored
        scored.sort(reverse=True)
        if len(scored) > 1 and random.random() < 0.2:
            return random.choice(scored)[1]
        return scored[0][1]

    def _status_score(self, name, d, attacker, defender):
        """How much an opponent wants a status move now (0 = useless here)."""
        meta, changes = d.get("category_meta"), d.get("stat_changes") or []
        hp_share = self._hp(attacker) / max(1, self._max_hp(attacker))
        if meta == "heal" or name in ("REST", "MOONLIGHT", "MORNING-SUN", "SYNTHESIS", "ROOST"):
            return 70 if hp_share < 0.4 else 0
        if d.get("ailment") == "confusion" or meta == "swagger":
            return 0 if self.vol(defender).get("confused") else 30
        if d.get("ailment") in ("leech-seed", "trap", "yawn", "infatuation"):
            return 0 if self.vol(defender).get({"leech-seed": "seeded", "trap": "trapped", "yawn": "drowsy",
                                                  "infatuation": "infatuated"}[d["ailment"]]) else 30
        if changes:
            if d.get("target") in ("user", "users-field", "user-and-allies") or all(n > 0 for _, n in changes):
                return 30 if all(self.stages(attacker).get(s, 0) < 2 for s, _ in changes) else 0
            return 25 if all(self.stages(defender).get(s, 0) > -2 for s, _ in changes) else 0
        if name in ("PROTECT", "DETECT"):
            return 10
        return 15 if usable_status(d) else 0

    def _ready_attacks(self):
        """Effectiveness previews for the HUD: the player's chosen (or first) move and the
        opponent's planned move."""
        chart = TypeAdvantage(self.game.loader.area_data.get("TYPE_CHART", {}))
        name = self.chosen_move or self._battle_moves(self.player_pokemon)[0]
        d = movelib.info(self.game, name)
        eff = chart.get_multiplier(d["type"], self.opponent_pokemon.types) if (d.get("power") or 0) else 1.0
        self.adv_opp = eff if eff > 0 else 1.0
        (self.opponent_move, self.opponent_attack_type, eff,
         self.opponent_move_category, self.opponent_move_power) = self._pick_move(self.opponent_pokemon,
                                                                                    self.player_pokemon)
        self.adv_player = eff if eff > 0 else 1.0

    def _check_forms(self):
        """On every switch-in: extreme weather ends if its Pokemon left, then Mega/Primal changes.
        Stat stages and volatile conditions of a Pokemon that left end; entry hazards hit the new one."""
        self.forget_switched_out()
        seen = self.__dict__.setdefault("_on_field", set())
        for mon in (self.player_pokemon, self.opponent_pokemon):
            if mon and id(mon) not in seen:
                seen.add(id(mon))
                self._form_msgs.extend(self.entry_hazards(mon))
        seen.intersection_update({id(self.player_pokemon), id(self.opponent_pokemon)})
        if self.weather_primal and self.weather_primal not in (self.player_pokemon, self.opponent_pokemon):
            self._form_msgs.append(self.WEATHER_TEXT[self.weather][2])
            self.weather, self.weather_primal, self.weather_turns = None, None, 0
        if self.starter_battle:
            return
        # Foes transform as they come out; the player uses the MEGA / PRIMAL button.
        mon = self.opponent_pokemon
        form = forms.opponent_form(self.game.assets, mon, self.mega_used["opponent"]) if mon else None
        if form:
            lines = forms.apply_form(self.game.assets, mon, form)
            self.mega_used["opponent"] = True
            self._form_msgs.extend(["Foe " + lines[0]] + lines[1:] + self._start_form_weather(mon))

    def _start_form_weather(self, mon):
        """Primal Groudon/Kyogre and Mega Rayquaza bring extreme weather. Returns its message."""
        weather = forms.form_weather(mon)
        if not weather:
            return []
        self.weather, self.weather_turns, self.weather_primal = weather, 0, mon
        self._weather_announced = True
        return [self.WEATHER_TEXT[weather][0]]

    def player_form_option(self):
        """The Mega/Primal form the player's active Pokemon can take now, or None."""
        if self.starter_battle or not self.player_pokemon:
            return None
        used = getattr(self, "mega_used", {}).get("player", False)
        return forms.player_form(self.game.assets, self.player_pokemon,
                                 self.game.story_manager.inventory, used)

    def activate_player_form(self):
        """MEGA / PRIMAL button: transform now (doesn't use the turn), once per battle."""
        form = self.player_form_option()
        if not form or self.phase != "MENU":
            return
        mon = self.player_pokemon
        lines = forms.apply_form(self.game.assets, mon, form)
        self.mega_used["player"] = True
        lines += self._start_form_weather(mon)
        self._ready_attacks()
        self.setup_action_menu()
        self.show_message(lines, callback=self.return_to_menu)

    def setup_battle_matchup(self, reset_opponent_hp=True):
        self._check_forms()
        self._ready_attacks()
        # Real HP at each Pokemon's level; Dynamax raid bosses have double HP.
        self.player_max_hp = self.player_pokemon.get_max_hp()
        foe = self.opponent_pokemon
        self.opp_hp_mult = forms.DYNAMAX_HP_MULT if forms.is_dynamax(foe) else 1
        self.opp_max_hp = foe.get_max_hp() * self.opp_hp_mult
        self.player_hp = max(0, self.player_pokemon.current_hp)
        if reset_opponent_hp:
            self.opponent_hp = self.opp_max_hp

    # ---- Weather (modern rules: lasts 5 turns, 8 with the matching rock) ----
    WEATHER_ROCKS = {"RAIN": "DAMP_ROCK", "SUN": "HEAT_ROCK", "SAND": "SMOOTH_ROCK", "SNOW": "ICY_ROCK"}
    WEATHER_TEXT = {
        "RAIN": ("It started to rain!", "Rain continues to fall.", "The rain stopped."),
        "SUN": ("The sunlight turned harsh!", "The sunlight is strong.", "The harsh sunlight faded."),
        "SAND": ("A sandstorm kicked up!", "The sandstorm rages.", "The sandstorm subsided."),
        "SNOW": ("It started to snow!", "Snow continues to fall.", "The snow stopped."),
        # Extreme weather from Primal Groudon, Primal Kyogre and Mega Rayquaza: lasts while they're out.
        "HARSH_SUN": ("The sunlight turned extremely harsh!", "The sunlight is extremely harsh.",
                      "The extremely harsh sunlight faded!"),
        "HEAVY_RAIN": ("A heavy rain began to fall!", "The heavy rain continues.", "The heavy rain has lifted!"),
        "STRONG_WINDS": ("Mysterious strong winds are protecting Flying-type Pokemon!",
                         "The mysterious strong winds blow on.", "The mysterious strong winds have dissipated!"),
    }
    FIZZLE_TEXT = {"HARSH_SUN": "The Water-type attack evaporated in the extremely harsh sunlight!",
                   "HEAVY_RAIN": "The Fire-type attack fizzled out in the heavy rain!"}
    SAND_IMMUNE = {"ROCK", "GROUND", "STEEL"}

    def _init_area_weather(self):
        """Weather from the current area: a short spell at the start of battle, not permanent."""
        if self.starter_battle:
            return
        # Fixed area weather, Galar's daily Wild Area weather, or today's seasonal weather.
        from src.world import seasons
        weather = seasons.area_weather(self.game, self.game.story_manager.current_area_key)
        if weather in self.WEATHER_ROCKS:
            self.set_weather(weather)
        self._weather_announced = False

    def set_weather(self, weather):
        self.weather = weather
        has_rock = self.game.story_manager.inventory.get(self.WEATHER_ROCKS[weather], 0) > 0
        self.weather_turns = 8 if has_rock else 5

    def summon_weather(self, rock_item):
        """Use a weather rock from the Bag: once per battle. Returns the battle message."""
        weather = next(w for w, rock in self.WEATHER_ROCKS.items() if rock == rock_item)
        self.weather_summoned = True
        if self.weather_primal:
            return "The extreme weather can't be changed!"
        self._weather_announced = True
        self.set_weather(weather)
        return self.WEATHER_TEXT[weather][0]

    def _weather_type_mult(self, attack_type):
        """Rain and sun power up or weaken the move itself."""
        if self.weather == "RAIN":
            return {"WATER": 1.5, "FIRE": 0.5}.get(attack_type, 1.0)
        if self.weather == "SUN":
            return {"FIRE": 1.5, "WATER": 0.5}.get(attack_type, 1.0)
        if self.weather == "HARSH_SUN":
            return {"FIRE": 1.5, "WATER": 0.0}.get(attack_type, 1.0)
        if self.weather == "HEAVY_RAIN":
            return {"WATER": 1.5, "FIRE": 0.0}.get(attack_type, 1.0)
        return 1.0

    def _weather_mult(self, attack_type, defender):
        if not self.weather:
            return 1.0
        mult = self._weather_type_mult(attack_type)
        defender_types = defender.types if defender else []
        if (self.weather == "STRONG_WINDS" and "FLYING" in defender_types
                and attack_type in ("ELECTRIC", "ICE", "ROCK")):
            mult *= 0.5  # Delta Stream: Flying's weaknesses are cancelled
        return mult

    def _status_chip(self):
        """Burn takes 1/16, poison 1/8 and Toxic n/16 of max HP at the end of the turn (it can KO)."""
        out = []
        mine = self.player_pokemon
        if getattr(mine, "status", None) and affection.shakes_off_status(mine):
            out.append(affection.CURE_TEXT.format(n=mine.display_name.upper(),
                                                  s=affection.STATUS_NAME.get(mine.status, "status")))
            mine.cure_status()
        for side in ("player", "opponent"):
            mon = self.player_pokemon if side == "player" else self.opponent_pokemon
            st = getattr(mon, "status", None)
            if st not in ("burn", "poison", "toxic"):
                continue
            max_hp = self.player_max_hp if side == "player" else self.opp_max_hp
            hp = self.player_hp if side == "player" else self.opponent_hp
            if st == "toxic":  # badly poisoned: 1/16, 2/16, 3/16... (counter restarts each battle)
                counts = self.__dict__.setdefault("_toxic_counts", {})
                counts[id(mon)] = min(15, counts.get(id(mon), 0) + 1)
                chip = min(max(1, max_hp * counts[id(mon)] // 16), hp)
            else:
                chip = min(max(1, max_hp // (16 if st == "burn" else 8)), hp)
            if chip <= 0:
                continue
            label = mon.display_name.upper() if side == "player" else f"Foe {mon.display_name.upper()}"
            if side == "player":
                self.player_hp -= chip
                mon.current_hp = self.player_hp
            else:
                self.opponent_hp -= chip
                mon.current_hp = self.opponent_hp
            out.append(f"{label} is hurt by its {'burn' if st == 'burn' else 'poison'}! It lost {chip} HP.")
            explained = self.__dict__.setdefault("_status_explained", set())
            if st not in explained:  # the first time in a battle: what the status does
                explained.add(st)
                out.append(self.STATUS_HELP[st])
        return out

    STATUS_HELP = {"burn": "A burn takes 1/16 of its HP at the end of every turn and weakens its physical moves.",
                   "poison": "Poison takes 1/8 of its HP at the end of every turn.",
                   "toxic": "Bad poison takes more HP every turn it stays in battle."}

    def _count_weather_on_faint(self):
        """A knockout still ends the turn: the weather counts down so it can't outlast its
        turns across switch-ins. Returns the 'weather stopped' line if it ran out."""
        if self._turn_end_done:
            return []
        self._turn_end_done = True
        if not self.weather or self.weather_primal:
            return []
        self.weather_turns -= 1
        if self.weather_turns > 0:
            return []
        line = self.WEATHER_TEXT[self.weather][2]
        self.weather = None
        return [line]

    def _weather_end_of_turn(self):
        """Sandstorm chip, then count the weather down, then status damage. Returns messages."""
        if not self.weather:
            return self._status_chip()
        if self.weather_primal:
            return [self.WEATHER_TEXT[self.weather][1]] + self._status_chip()
        messages = []
        self.weather_turns -= 1
        if self.weather_turns <= 0:
            messages.append(self.WEATHER_TEXT[self.weather][2])
            self.weather = None
            return messages + self._status_chip()
        messages.append(self.WEATHER_TEXT[self.weather][1])
        if self.weather == "SAND":
            # Sand chip can knock a Pokemon out; _start_pending_faint handles it.
            for side in ("player", "opponent"):
                mon = self.player_pokemon if side == "player" else self.opponent_pokemon
                if self.SAND_IMMUNE & set(mon.types or []):
                    continue
                max_hp = self.player_max_hp if side == "player" else self.opp_max_hp
                hp = self.player_hp if side == "player" else self.opponent_hp
                chip = min(max(1, max_hp // 16), hp)
                if chip <= 0:
                    continue
                if side == "player":
                    self.player_hp -= chip
                    self.player_pokemon.current_hp = self.player_hp
                    messages.append(f"{mon.display_name.upper()} is buffeted by the sandstorm!")
                else:
                    self.opponent_hp -= chip
                    self.opponent_pokemon.current_hp = self.opponent_hp
                    messages.append(f"Foe {mon.display_name.upper()} is buffeted by the sandstorm!")
        return messages + self._status_chip()

    WEATHER_TINT = {"RAIN": (40, 70, 140, 50), "SUN": (255, 200, 60, 45),
                    "SAND": (190, 150, 80, 70), "SNOW": (220, 235, 255, 60),
                    "HARSH_SUN": (255, 110, 30, 80), "HEAVY_RAIN": (20, 40, 110, 90),
                    "STRONG_WINDS": (120, 200, 150, 50)}

    def _draw_weather(self, screen):
        """Tint the battlefield, drift a few particles, and show the turns left."""
        if not self.weather:
            return
        field_h = Utils.get_full_dialogue_rect(self.game).top
        w = self.game.width
        tint = pygame.Surface((w, field_h), pygame.SRCALPHA)
        tint.fill(self.WEATHER_TINT[self.weather])
        t = pygame.time.get_ticks()
        rng = random.Random(7)
        for _ in range(60):
            x0, y0 = rng.randrange(w), rng.randrange(field_h)
            if self.weather in ("RAIN", "HEAVY_RAIN"):
                x, y = (x0 - t // 6) % w, (y0 + t // 2) % field_h
                pygame.draw.line(tint, (180, 200, 255, 150), (x, y), (x - 4, y + 14), 2)
                if self.weather == "HEAVY_RAIN":
                    x2 = (x + w // 2) % w
                    pygame.draw.line(tint, (200, 215, 255, 150), (x2, y), (x2 - 5, y + 18), 3)
            elif self.weather == "STRONG_WINDS":
                x, y = (x0 + t // 2) % w, y0
                pygame.draw.line(tint, (230, 255, 240, 140), (x, y), (x + 40, y - 3), 2)
            elif self.weather == "SNOW":
                x, y = (x0 + t // 40) % w, (y0 + t // 12) % field_h
                pygame.draw.circle(tint, (255, 255, 255, 200), (x, y), 3)
            elif self.weather == "SAND":
                x, y = (x0 + t // 3) % w, (y0 + t // 20) % field_h
                pygame.draw.circle(tint, (140, 100, 50, 180), (x, y), 2)
        screen.blit(tint, (0, 0))
        label = (self.weather.replace("_", " ") if self.weather_primal
                 else f"{self.weather}  {self.weather_turns}")
        text = self.game.assets.fonts["tiny"].render(label, True, WHITE)
        box = text.get_rect(midtop=(w // 2, 16)).inflate(16, 8)
        pygame.draw.rect(screen, BLACK, box, border_radius=6)
        screen.blit(text, text.get_rect(center=box.center))

    def _calculate_damage(self, attacker, defender, power, effectiveness, weather=1.0, category="PHYSICAL",
                          move_type=None, defender_max_hp=None, crit_stage=0):
        """One hit with the games' damage formula (src/pokemon/balance.py): levels, the
        Attack/Defense (or Sp. Atk/Sp. Def) stats at those levels, move power, weather,
        crits, the 85-100% roll, STAB and type."""
        special = category == "SPECIAL"
        attack = attacker.stat_value("SPATK" if special else "ATTACK")
        defense = defender.stat_value("SPDEF" if special else "DEFENSE")
        types = defender.types or []
        if special and self.weather == "SAND" and "ROCK" in types:
            defense = defense * 3 // 2  # sandstorm: Rock types' Sp. Def x1.5
        if not special and self.weather == "SNOW" and "ICE" in types:
            defense = defense * 3 // 2  # snow: Ice types' Defense x1.5
        crit = None
        roll = None
        mode = getattr(self, "_answer_mode", None) if attacker is self.player_pokemon else None
        if mode == "crit":
            crit_stage = (crit_stage or 0) + 1
        crit_stage = (crit_stage or 0) + self.vol(attacker).get("focus", 0)  # Focus Energy
        base = balance.CRIT_STAGES[max(0, min(int(crit_stage or 0), 3))]
        if attacker is self.player_pokemon:  # 5 hearts of affection: crits twice as often
            crit = random.random() < min(1.0, affection.crit_chance(attacker, base))
        else:
            crit = random.random() < base
        if self.vol(attacker).get("laser_focus"):
            crit = True
        # Stat stages (a critical hit ignores the attacker's drops and the defender's boosts).
        attack = attack * self.stat_mult(attacker, "SPATK" if special else "ATTACK", crit, True)
        defense = defense * self.stat_mult(defender, "SPDEF" if special else "DEFENSE", crit, False)
        if mode == "weak":
            roll = random.randint(*self.WEAK_ROLL)
        elif mode == "max_roll":
            roll = 100
        dmg, self._last_was_crit = balance.damage(
            self._level(attacker), power, attack, defense,
            stab=move_type in (attacker.types or []), effectiveness=effectiveness, weather=weather,
            crit=crit, crit_stage=crit_stage, roll=roll)
        foe_side = self.side(defender)
        if dmg and not self._last_was_crit and (foe_side.get("aurora_veil") or foe_side.get(
                "light_screen" if special else "reflect")):
            dmg = max(1, dmg // 2)  # Reflect / Light Screen / Aurora Veil
        if dmg and ((move_type == "ELECTRIC" and self.field().get("mud_sport"))
                    or (move_type == "FIRE" and self.field().get("water_sport"))):
            dmg = max(1, dmg // 3)
        if mode and weather != 0:
            self._answer_used = mode if mode != "crit" or self._last_was_crit else None
        return dmg

    def setup_math_ui(self):
        if hasattr(self, "math_ui") and self.math_ui in self.game.ui_manager.elements:
            self.game.ui_manager.elements.remove(self.math_ui)

        def callback(index):
            self._answer_feedback(index)

        self.math_ui = MathBattleUI(self.game, self.problem_str, self.options, callback)
        self.game.ui_manager.add_element(self.math_ui)
        self.math_ui.set_visibility(False)

    PRAISE = ("Great job!", "You got it!", "Awesome!", "Correct!", "Super!")
    QUICK_MS = 2000
    QUICK_BONUSES = ("max_roll", "crit", "flinch")
    WEAK_ROLL = (75, 85)       # a wrong answer: below the usual 85-100% damage roll
    WRONG_ANSWER_CAP = 49      # ...and at most 49% of the foe's max HP per move
    QUICK_FLINCH = 30          # % chance the quick-answer flinch bonus works
    FEEDBACK_FRAMES = {True: 16, False: 24}  # ~0.6 s / ~1 s at 25 FPS

    def _answer_feedback(self, index):
        """A short beat before the turn: cheer a right answer, kindly show the right one
        after a wrong answer. Taps are ignored until it's over."""
        if self.phase == "ANSWER_FEEDBACK":
            return
        correct = self.options[index] == self.correct_ans
        right_index = self.options.index(self.correct_ans) if self.correct_ans in self.options else index
        elapsed = pygame.time.get_ticks() - getattr(self, "_question_at", 0)
        # A wrong answer weakens the move; a right one in under 2 s may earn a bonus.
        self._answer_mode = None if correct else "weak"
        if correct and elapsed < self.QUICK_MS:
            self._answer_mode = random.choice(self.QUICK_BONUSES)
        text = random.choice(self.PRAISE) if correct else f"Nice try! It was {self.correct_ans}."
        self.math_ui.feedback = {"index": index, "right": right_index, "correct": correct, "text": text,
                                 "frames": self.FEEDBACK_FRAMES[correct], "total": self.FEEDBACK_FRAMES[correct]}
        self._answer_correct = correct
        self.phase = "ANSWER_FEEDBACK"
        snd = getattr(self.game.assets, "ui_sfx", {}).get("correct" if correct else "wrong")
        if snd:
            snd.play()

    def _tick_answer_feedback(self):
        fb = getattr(self.math_ui, "feedback", None)
        if not fb:
            self.resolve_turn(getattr(self, "_answer_correct", False))
            return
        fb["frames"] -= 1
        if fb["frames"] <= 0:
            self.math_ui.feedback = None
            self.resolve_turn(fb["correct"])

    def setup_action_menu(self):
        form = self.player_form_option()
        self.action_menu = BattleActionMenu(
            self.game,
            self.player_pokemon.display_name,
            on_math=lambda: self.open_move_menu(),
            on_pkdex=lambda: self._open_bag(),
            on_pkmn=lambda: self.open_party_menu(),
            on_run=lambda: self.handle_run(),
            on_mega=self.activate_player_form if form else None,
            mega_label="PRIMAL" if form and form["form"] == "primal" else "MEGA",
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
        self._turn_end_done = False
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
        v = self.vol(self.player_pokemon)
        if self.trainer_class == "WILD" and (v.get("no_escape") or v.get("trapped")):
            self.show_message("You can't escape!", callback=self.return_to_menu)
            return
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

        sprite = battle_sprite(self.old_pkmn, "player")
        rect = sprite_rect(self.game, sprite, "player")
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

        if self._form_msgs and self.phase == "MENU":
            msgs, self._form_msgs = self._form_msgs, []
            if self.weather and not self._weather_announced:
                msgs.append(self.WEATHER_TEXT[self.weather][0])
            self._weather_announced = True
            self.show_message(msgs, callback=self.return_to_menu)
        elif self.weather and not self._weather_announced and self.phase == "MENU":
            self._weather_announced = True
            self.show_message(self.WEATHER_TEXT[self.weather][0], callback=self.return_to_menu)

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
                                elif self.starter_battle:
                                    self.continue_after_starter_loss()
                                else:

                                    self.perform_battle_black_out()
            return

    def continue_after_starter_loss(self):
        """Losing the starter rival battle heals the team and continues the story as if it were won (no prize money)."""
        for p in self.game.story_manager.player_team:
            p.heal_full()
            if hasattr(p, "revert_transform"):
                p.revert_transform()
        self.exit_battle(lost=True)

    def perform_battle_black_out(self):
        """Back to the last Pokemon Center (or home) with a healed team."""
        from src.states.overworld import white_out, reset_league_after_loss
        if self.battle_type == "gym":
            reset_league_after_loss(self.game)  # a League run starts over after a loss
        white_out(self.game)

    def _speed(self, mon):
        speed = mon.stat_value("SPEED") * (0.5 if getattr(mon, "status", None) == "paralysis" else 1)
        speed *= self.speed_mult(mon)  # Speed stages, Tailwind
        return -speed if self.field().get("trick_room") else speed  # Trick Room: slower first

    def resolve_turn(self, player_was_correct):
        """Both Pokemon act in Speed order (move priority first). The answer changes how well
        your move goes (see _answer_feedback): wrong = weaker hit, quick and right = a bonus."""
        self.phase = "RESOLVE_TURN"
        self.turn_actions.clear()
        self.turn_count += 1
        self._turn_end_done = False
        if self.math_ui:
            self.math_ui.set_visibility(False)
        self._flinched = set()
        self._acts_second = None
        if not player_was_correct and getattr(self, "_answer_mode", None) is None:
            self._answer_mode = "weak"
        mine = movelib.info(self.game, self._forced_move(self.player_pokemon)
                            or self.chosen_move or self._battle_moves(self.player_pokemon)[0])
        theirs = movelib.info(self.game, self._forced_move(self.opponent_pokemon)
                              or self._ai_choose(self.opponent_pokemon, self.player_pokemon))
        self._foe_next_move = theirs["name"]
        p_pri, o_pri = mine.get("priority", 0), theirs.get("priority", 0)
        p_spd, o_spd = self._speed(self.player_pokemon), self._speed(self.opponent_pokemon)
        player_first = (p_pri > o_pri) or (p_pri == o_pri and (p_spd > o_spd or (p_spd == o_spd and random.random() < 0.5)))
        self._acts_second = id(self.opponent_pokemon if player_first else self.player_pokemon)
        if player_first:
            self.turn_actions += [self.player_attack, self.opponent_attack]
        else:
            self.turn_actions += [self.opponent_attack, self.player_attack]

    def _note_participant(self):
        """Remember every Pokemon that has been out against the current foe (XP goes to them)."""
        if not hasattr(self, "_xp_participants"):
            self._xp_participants = []
        p = getattr(self, "player_pokemon", None)
        if p is not None and not any(p is q for q in self._xp_participants):
            self._xp_participants.append(p)

    def _xp_shares(self):
        """[(pokemon, share)] for this KO (Jordan, 10-29). The Pokemon that battled this foe and
        haven't fainted share it; with EXP SHARE on (Options, the default; or the Exp. Share item)
        each of them gets it all and the rest of the party (not fainted) half, as in Gen 6+.
        With it off, the battlers split it evenly, as in Gen 1-5."""
        story = self.game.story_manager
        self._note_participant()
        team = [p for p in story.player_team if p]
        fought = [p for p in self._xp_participants if p.current_hp > 0 and any(p is q for q in team)]
        if not fought and self.player_pokemon is not None and self.player_pokemon.current_hp > 0:
            fought = [self.player_pokemon]
        if getattr(story, "exp_share", True) or story.inventory.get("EXP_SHARE", 0) > 0:
            rest = [p for p in team if p.current_hp > 0 and not any(p is q for q in fought)]
            return [(p, 1.0) for p in fought] + [(p, 0.5) for p in rest]
        return [(p, 1.0 / len(fought)) for p in fought]

    def _award_battle_xp(self):
        """XP for the KO, as in the games: the Gen 7 formula with the foe's base XP yield and the
        level gap, 1.5x from trainers, 1.2x with strong affection, then growth.XP_BOOST for fast
        leveling, shared out by _xp_shares. Returns messages."""
        foe = self.opponent_pokemon
        foe_level = self._level(foe)
        trainer = self.trainer_class != "WILD"
        shares = self._xp_shares()
        self._xp_participants = [self.player_pokemon] if self.player_pokemon is not None else []  # next foe
        earners = [p for p, _ in shares]
        share_of = {id(p): k for p, k in shares}
        lead = self.player_pokemon
        lead.counters["wins"] = lead.counters.get("wins", 0) + 1
        if foe.id == 625:  # Bisharp, for Kingambit
            lead.counters["bisharp"] = lead.counters.get("bisharp", 0) + 1

        from src.pokemon import growth
        from src.pokemon.evolution import base_id
        base_yield = (self.game.assets.movesets.get(str(base_id(foe)), {}).get("base_xp") or 100)
        messages = []
        cap = levels.xp_cap(self.game.story_manager)
        for p in earners:
            my_level = self._level(p)
            gained = max(1, int(growth.battle_xp(base_yield, foe_level, my_level, trainer=trainer)
                                * affection.xp_mult(p) * share_of[id(p)]))
            if my_level >= cap:
                if p is lead:
                    messages.append(f"{p.display_name.upper()} can't grow past Lv {cap} until you beat the next Gym!")
                continue
            old_level = p.level
            grew = p.gain_xp(gained, cap)
            if p is not lead:
                if grew:
                    messages.append(f"{p.display_name.upper()} grew to Lv {p.level}!")
                    messages.extend(movelib.learn_new_moves(self.game, p, old_level))
                continue
            messages.append(f"{p.display_name.upper()} gained {gained} XP!")
            if grew:
                messages.append(f"{p.display_name.upper()} grew to Lv {p.level}!")
                messages.extend(movelib.learn_new_moves(self.game, p, old_level))
        if any(k == 0.5 for k in share_of.values()):
            messages.insert(1 if messages else 0, "The rest of your team gained XP too!")
        return messages

    DISOBEY_LINES = ("{n} is loafing around!", "{n} won't obey!", "{n} turned away!",
                     "{n} pretended not to notice!")
    IMMUNE_TO = {"burn": {"FIRE"}, "paralysis": {"ELECTRIC"}, "poison": {"POISON", "STEEL"},
                 "toxic": {"POISON", "STEEL"}, "freeze": {"ICE"}, "sleep": set()}
    STATUS_TEXT = {"burn": "{n} was burned!", "paralysis": "{n} is paralyzed! It may be unable to move!",
                   "poison": "{n} was poisoned!", "sleep": "{n} fell asleep!", "freeze": "{n} was frozen solid!",
                   "toxic": "{n} was badly poisoned!"}

    def _can_inflict(self, ailment, target):
        return (ailment in movelib.STATUSES and not getattr(target, "status", None)
                and not (self.IMMUNE_TO.get(ailment, set()) & set(target.types or [])))

    def _status_move_works(self, d, target, ignore_current=False):
        """Can this status move inflict its ailment on target? (type of the move matters too:
        Thunder Wave can't hit Ground types.)"""
        ailment = "toxic" if d.get("name") == "TOXIC" else d.get("ailment")
        name = d.get("name")
        if name in movelib.POWDER_MOVES and "GRASS" in (target.types or []):
            return False
        if name in movelib.TYPE_CHECKED_STATUS:
            chart = TypeAdvantage(self.game.loader.area_data.get("TYPE_CHART", {}))
            if chart.get_multiplier(d.get("type"), target.types) == 0:
                return False
        if ailment not in movelib.STATUSES or (self.IMMUNE_TO.get(ailment, set()) & set(target.types or [])):
            return False
        if not ignore_current and getattr(target, "status", None):
            return False
        return True

    def _inflict(self, ailment, target, label):
        target.status = ailment
        if ailment == "sleep":
            target.sleep_turns = random.randint(1, 3)
        return self.STATUS_TEXT[ailment].format(n=label)

    def _status_stops(self, mon, label):
        """Sleep, freeze and paralysis can stop a move. Returns (stopped, lines)."""
        recharging = self.__dict__.setdefault("_recharging", set())
        if id(mon) in recharging:
            recharging.discard(id(mon))
            return True, [f"{label} must recharge!"]
        if id(mon) in getattr(self, "_flinched", ()):
            self._flinched.discard(id(mon))
            return True, [f"{label} flinched and couldn't move!"]
        st = getattr(mon, "status", None)
        if st == "sleep":
            if getattr(mon, "sleep_turns", 0) > 0:  # 1-3 turns it can't move, then it wakes and acts
                mon.sleep_turns -= 1
                return True, [f"{label} is fast asleep."]
            mon.status = None
            return False, [f"{label} woke up!"]
        if st == "freeze":
            if random.random() < 0.2:
                mon.status = None
                return False, [f"{label} thawed out!"]
            return True, [f"{label} is frozen solid!"]
        if st == "paralysis" and random.random() < 0.25:
            return True, [f"{label} is paralyzed! It can't move!"]
        return False, []

    def _use_move(self, attacker, defender, name, att_label, def_label, defender_max_hp, defender_hp):
        """Run one move. Returns (damage dealt, message lines, was_effective_hit)."""
        d = movelib.info(self.game, name)
        blocked = self.move_blocked(attacker, name, d)  # Taunt, Disable
        if blocked:
            return 0, [blocked], False
        self.vol(attacker)["last_move"] = name
        lines = [self.game.assets.get_text("used_move", name=att_label, move=name.replace("-", " "))]
        self._last_was_crit = False  # fixed-damage/charge/status turns never crit
        charging = self.__dict__.setdefault("_charging", {})
        if name in movelib.TWO_TURN and charging.get(id(attacker)) != name \
                and not (name in ("SOLAR-BEAM", "SOLAR-BLADE") and self.weather == "SUN"):
            charging[id(attacker)] = name  # turn 1: charge (it uses the move again next turn)
            if name in movelib.SEMI_INVULNERABLE:  # up in the sky / underground until it strikes
                self.__dict__.setdefault("_semi", {})[id(attacker)] = (name, self.turn_count)
            return 0, [movelib.TWO_TURN[name].format(n=att_label)], False
        charging.pop(id(attacker), None)
        self.__dict__.setdefault("_semi", {}).pop(id(attacker), None)
        semi_mult = 1
        semi = self._semi.get(id(defender))
        # Semi-invulnerable through the rest of the charge turn and the next turn (a wrong math answer
        # keeps the charge, but the cover doesn't last forever).
        if semi and self.turn_count - semi[1] <= 1 and name not in movelib.WEATHER_MOVES:
            hits = movelib.SEMI_INVULNERABLE[semi[0]]
            if name not in hits:
                return 0, lines + [f"{def_label} avoided the attack!"], False
            semi_mult = hits[name]
        if self.protected(attacker, defender, d):
            return 0, lines + [f"{def_label} protected itself!"], False
        acc = d.get("accuracy")
        if acc and d.get("target") != "user" and d.get("category_meta") != "ohko" \
                and random.uniform(0, 100) >= acc * self.acc_mult(attacker, defender):
            return 0, lines + [f"{att_label}'s attack missed!"], False
        if (defender is self.player_pokemon and attacker is not defender and name not in movelib.WEATHER_MOVES
                and affection.evades(defender)):
            return 0, lines + [affection.EVADE_TEXT.format(n=def_label)], False
        if name in movelib.WEATHER_MOVES:
            if self.weather_primal:
                return 0, lines + ["But it failed!"], False
            self.set_weather(movelib.WEATHER_MOVES[name])
            self._weather_announced = True
            return 0, lines + [self.WEATHER_TEXT[self.weather][0]], False
        if name in movelib.FIXED_DAMAGE:
            chart = TypeAdvantage(self.game.loader.area_data.get("TYPE_CHART", {}))
            if chart.get_multiplier(d["type"], defender.types) == 0:
                return 0, lines + [f"It doesn't affect {def_label}..."], False
            kind = movelib.FIXED_DAMAGE[name]
            dmg = (self._level(attacker) if kind == "level" else max(1, defender_hp // 2) if kind == "half"
                   else int(kind))
            if attacker is self.player_pokemon and getattr(self, "_answer_mode", None) == "weak":
                dmg = min(dmg, max(1, defender_max_hp * self.WRONG_ANSWER_CAP // 100))  # (see below)
            return min(dmg, defender_hp), lines, False
        if name == movelib.STRUGGLE:
            dmg = self._calculate_damage(attacker, defender, 50, 1.0, 1.0, category="PHYSICAL",
                                         move_type=None, defender_max_hp=defender_max_hp)
            mx = self.player_max_hp if attacker is self.player_pokemon else self.opp_max_hp
            self._adjust_hp(attacker, -max(1, mx // 4))
            return dmg, lines + [f"{att_label} is hit with recoil!"], False
        if d.get("category_meta") == "ohko":  # Fissure, Guillotine, Horn Drill, Sheer Cold
            lv_a, lv_d = self._level(attacker), self._level(defender)
            chart = TypeAdvantage(self.game.loader.area_data.get("TYPE_CHART", {}))
            if chart.get_multiplier(d["type"], defender.types) == 0:
                return 0, lines + [f"It doesn't affect {def_label}..."], False
            if lv_a < lv_d or random.uniform(0, 100) >= 30 + lv_a - lv_d:
                return 0, lines + [f"{att_label}'s attack missed!"], False
            dmg = defender_hp
            if attacker is self.player_pokemon and getattr(self, "_answer_mode", None) == "weak":
                dmg = min(dmg, max(1, defender_max_hp * self.WRONG_ANSWER_CAP // 100))
                return dmg, lines + ["The answer was off, so it wasn't a one-hit KO."], False
            return dmg, lines + ["It's a one-hit KO!"], False
        if not (d.get("power") or 0):
            if attacker is self.player_pokemon and getattr(self, "_answer_mode", None) == "weak" \
                    and random.random() < 0.5:
                return 0, lines + ["The answer was off, so the move didn't work!"], False
            if d.get("ailment") in movelib.STATUSES and d.get("category_meta") == "ailment":
                if self._status_move_works(d, defender) and not self.vol(defender).get("substitute") \
                        and not self.side(defender).get("safeguard"):
                    ailment = "toxic" if name == "TOXIC" else d["ailment"]
                    return 0, lines + [self._inflict(ailment, defender, def_label)], False
                return 0, lines + ["But it failed!"], False
            extra = self.status_effect(name, d, attacker, defender, att_label, def_label)
            pick = getattr(self, "_metronome", None)
            if pick:  # Metronome: the random move runs now
                self._metronome = None
                dmg, more, eff = self._use_move(attacker, defender, pick, att_label, def_label,
                                                defender_max_hp, defender_hp)
                return dmg, lines + (extra or []) + more[1:], eff
            if extra is not None:
                return 0, lines + extra, False
            return 0, lines + ["But it failed!"], False
        chart = TypeAdvantage(self.game.loader.area_data.get("TYPE_CHART", {}))
        eff = chart.get_multiplier(d["type"], defender.types) if d.get("type") else 1.0
        if eff == 0:
            return 0, lines + [f"It doesn't affect {def_label}..."], False
        weather_mult = self._weather_mult(d["type"], defender)
        hits = self._hit_count(d)
        damage, crit_any, landed = 0, False, 0
        for _ in range(hits):  # multi-hit moves (Double Kick, Fury Attack...) roll each hit
            dmg = self._calculate_damage(attacker, defender, d["power"], eff, weather_mult,
                                         category=d.get("category") or "PHYSICAL", move_type=d["type"],
                                         defender_max_hp=defender_max_hp, crit_stage=d.get("crit_rate") or 0)
            if dmg and getattr(attacker, "status", None) == "burn" and d.get("category") == "PHYSICAL":
                dmg = max(1, dmg // 2)  # burns halve physical attacks
            damage += dmg
            crit_any = crit_any or self._last_was_crit
            landed += 1
            if not dmg or damage >= defender_hp:
                break
        self._last_was_crit = crit_any
        if semi_mult != 1 and damage:
            damage *= semi_mult  # Gust vs Fly, Earthquake vs Dig, Surf vs Dive: double damage
        if damage and attacker is self.player_pokemon and getattr(self, "_answer_mode", None) == "weak":
            # Jordan: a wrong answer can never take more than 49% of the foe's HP (all hits
            # together), so tapping answers at random can't knock anything out in one go.
            damage = min(damage, max(1, defender_max_hp * self.WRONG_ANSWER_CAP // 100))
        if damage and attacker is not defender:  # a Substitute takes the hit
            damage, sub_lines = self.absorb_with_substitute(defender, damage, def_label)
            lines += sub_lines
        if damage >= defender_hp > 1 and self.vol(defender).get("endure"):
            damage = defender_hp - 1
            lines.append(f"{def_label} endured the hit!")
        if landed > 1:
            lines.append(f"Hit {landed} times!")
        # Drain (Giga Drain +50) heals the user; negative drain is recoil (Take Down -25).
        drain = d.get("drain") or 0
        if drain and damage:
            amount = max(1, min(damage, defender_hp) * abs(drain) // 100)
            self._adjust_hp(attacker, amount if drain > 0 else -amount)
            lines.append(f"{def_label} had its energy drained!" if drain > 0
                         else f"{att_label} is damaged by recoil!")
        if weather_mult == 0:
            lines.append(self.FIZZLE_TEXT.get(self.weather, "But it failed!"))
        else:
            if self._last_was_crit:
                lines.append("Critical hit!")
            if eff > 1.0:
                lines.append("It's super effective!")
            elif eff < 1.0:
                lines.append("It's not very effective...")
        if damage and name in movelib.RECHARGE:
            self.__dict__.setdefault("_recharging", set()).add(id(attacker))
        if damage and damage < defender_hp and (d.get("flinch") or 0) \
                and getattr(self, "_acts_second", None) == id(defender) and random.uniform(0, 100) < d["flinch"]:
            self.__dict__.setdefault("_flinched", set()).add(id(defender))  # only if it hasn't moved yet
        # Added effects (Ember's burn, Body Slam's paralysis...) on a target that survives.
        chance = d.get("ailment_chance") or 0
        if damage and damage < defender_hp and chance and self._can_inflict(d.get("ailment"), defender) \
                and random.uniform(0, 100) < chance:
            lines.append(self._inflict(d["ailment"], defender, def_label))
        if getattr(defender, "status", None) == "freeze" and d["type"] == "FIRE" and damage:
            defender.status = None
            lines.append(f"{def_label} thawed out!")
        lines += self.after_hit(name, d, attacker, defender, att_label, def_label, damage, damage < defender_hp)
        return damage, lines, eff > 1.0

    def player_attack(self):
        if self.opponent_hp <= 0 or self.player_hp <= 0:
            return

        mon = self.player_pokemon
        label = mon.display_name.upper()
        # Obedience: a Pokemon far above the badge level may ignore you.
        cap = self._obey_level()
        lv = self._level(mon)
        if lv > cap and random.random() < (lv - cap) / (lv + cap):
            self.dialogue_box.reset([random.choice(self.DISOBEY_LINES).format(n=label),
                                     f"(Win more badges here to earn the trust of Pokemon above Lv {cap}.)"])
            self.dialogue_box.set_visibility(True)
            self.feedback_timer = 30
            return
        stopped, pre = self._status_stops(mon, label)
        if not stopped:
            stopped, more = self.before_move(mon)  # confusion, infatuation
            pre = pre + more
        if stopped:
            self.dialogue_box.reset(pre)
            self.dialogue_box.set_visibility(True)
            self.feedback_timer = 30
            return

        name = (self._forced_move(mon) or self.forced_effect_move(mon) or self.chosen_move
                or self._battle_moves(mon)[0])
        self.player_move = name.replace("-", " ")
        self._answer_used = None
        damage, messages, _ = self._use_move(mon, self.opponent_pokemon, name, label,
                                             f"Foe {self.opponent_pokemon.display_name.upper()}",
                                             self.opp_max_hp // getattr(self, "opp_hp_mult", 1), self.opponent_hp)
        messages = pre + messages + self._answer_notes(label, damage) + self.end_rampage_turn(mon)
        self._answer_mode = None
        self.opponent_hp = max(0, self.opponent_hp - damage)
        self.opponent_pokemon.current_hp = self.opponent_hp
        if damage:
            mon.counters["attacks"] = mon.counters.get("attacks", 0) + 1
            if self._last_was_crit:
                self._battle_crits[id(mon)] = self._battle_crits.get(id(mon), 0) + 1
                # Sirfetch'd: critical hits add up over every battle (Jordan), not just one.
                mon.counters["crits"] = mon.counters.get("crits", 0) + 1
            self.anim_ctrl.start_lunge("player")

        xp_messages = self._award_battle_xp() if self.opponent_hp <= 0 else []

        if self.opponent_hp <= 0 and self.try_trigger_wild_catch_prompt():
            return

        if self.opponent_hp <= 0:
            self.turn_actions.clear()  # a fainted Pokemon's queued move never happens
            self.fainting_side = "opponent"
            messages.append(f"Foe {self.opponent_pokemon.display_name.upper()} fainted!")
            messages.extend(xp_messages)
            messages.extend(self._count_weather_on_faint())
            self.dialogue_box.callback = self._start_faint_animation
            self.phase = "MESSAGE"

        self._end_if_fled(messages)
        self.dialogue_box.reset(messages)
        self.dialogue_box.set_visibility(True)
        self.feedback_timer = 30

    def _end_if_fled(self, messages):
        """Teleport, Roar or Whirlwind in a wild battle: the battle ends after the message."""
        if getattr(self, "_flee_by_move", None) is None:
            return
        self._flee_by_move = None
        self.turn_actions.clear()
        self.phase = "MESSAGE"
        self.dialogue_box.callback = self.on_flee_complete

    def _answer_notes(self, label, damage):
        """Explain what the math answer did to this move (only when it made a difference)."""
        used = getattr(self, "_answer_used", None)
        mode = getattr(self, "_answer_mode", None)
        foe = self.opponent_pokemon
        if mode == "flinch" and damage and 0 < self.opponent_hp - damage                 and getattr(self, "_acts_second", None) == id(foe) and random.uniform(0, 100) < self.QUICK_FLINCH:
            self.__dict__.setdefault("_flinched", set()).add(id(foe))
            return ["Your lightning-fast answer startled the foe! It might flinch!"]
        if not damage:
            return []
        if used == "weak":
            return ["The answer was off, so the attack was weaker."]
        if used == "max_roll":
            return [f"Your speedy answer powered up {label}'s attack: max power!"]
        if used == "crit":
            return ["Your speedy answer helped land that critical hit!"]
        return []

    def opponent_attack(self):
        if self.player_hp <= 0 or self.opponent_hp <= 0:
            return
        foe = self.opponent_pokemon
        label = f"Foe {foe.display_name.upper()}"
        stopped, pre = self._status_stops(foe, label)
        if not stopped:
            stopped, more = self.before_move(foe)  # confusion, infatuation
            pre = pre + more
        if stopped:
            self.dialogue_box.reset(pre)
            self.dialogue_box.set_visibility(True)
            self.feedback_timer = 30
            return
        mon = self.player_pokemon
        name = (self._forced_move(foe) or self.forced_effect_move(foe) or getattr(self, "_foe_next_move", None)
                or self._ai_choose(foe, mon))
        self._foe_next_move = None
        self.opponent_move = name.replace("-", " ")
        damage, messages, _ = self._use_move(foe, mon, name, label, mon.display_name.upper(),
                                             self.player_max_hp, self.player_hp)
        messages = pre + messages + self.end_rampage_turn(foe)
        if damage >= self.player_hp > 1 and affection.endures(mon):
            damage = self.player_hp - 1
            messages.append(affection.ENDURE_TEXT.format(n=mon.display_name.upper()))
        self.player_hp = max(0, self.player_hp - damage)
        mon.current_hp = self.player_hp
        if damage:
            # For Runerigus / Basculegion: damage taken in this battle and overall.
            self._battle_damage[id(mon)] = self._battle_damage.get(id(mon), 0) + damage
            mon.counters["damage_total"] = mon.counters.get("damage_total", 0) + damage
            self.anim_ctrl.start_lunge("opponent")

        if self.player_hp <= 0:
            self.turn_actions.clear()  # a fainted Pokemon's queued move never happens
            self.fainting_side = "player"
            messages.append(f"{mon.display_name.upper()} fainted!")
            messages.extend(self._count_weather_on_faint())
            self.dialogue_box.callback = self._start_faint_animation
            self.phase = "MESSAGE"

        self._end_if_fled(messages)
        self.dialogue_box.reset(messages)
        self.dialogue_box.set_visibility(True)
        self.feedback_timer = 30

    def try_trigger_wild_catch_prompt(self):
        return False

    def _start_pending_faint(self):
        """A Pokemon knocked out by recoil, burn, poison or sandstorm (not by an attack, which
        starts its own faint) faints now. Returns True if a faint started."""
        if self.opponent_hp <= 0 and self.opponent_pokemon:
            msgs = [f"Foe {self.opponent_pokemon.display_name.upper()} fainted!"]
            if self.player_hp > 0:
                msgs += self._award_battle_xp()
            side = "opponent"
        elif self.player_hp <= 0 and self.player_pokemon:
            msgs, side = [f"{self.player_pokemon.display_name.upper()} fainted!"], "player"
        else:
            return False
        self.turn_actions.clear()
        self.fainting_side = side
        self.phase = "MESSAGE"
        self.action_menu.set_visibility(False)
        if self.math_ui:
            self.math_ui.set_visibility(False)
        self.dialogue_box.reset(msgs)
        self.dialogue_box.set_visibility(True)
        self.dialogue_box.callback = self._start_faint_animation
        return True

    def _start_faint_animation(self):
        self.phase = "FAINT_ANIM_RUNNING"
        self.dialogue_box.callback = None
        if self.fainting_side == "opponent":
            img = battle_sprite(self.opponent_pokemon, "opponent")
            self.faint_anim.start(img, sprite_rect(self.game, img, "opponent").topleft)
        elif self.fainting_side == "player":
            # Always run the animation (its end moves the battle on): 60 Gen 6-9 species have no
            # back sprite, and skipping it froze the battle for good (Nemona's first battle).
            p_img = battle_sprite(self.player_pokemon, "player")  # (its front, turned, without a back sprite)
            if p_img is None:
                p_img = pygame.Surface((1, 1), pygame.SRCALPHA)
            self.faint_anim.start(p_img, sprite_rect(self.game, p_img, "player").topleft)

    # Prize money as in the games: the opponent's highest level x a rate for its class. (A flat
    # 25,000 per Elite Four win let a lost League run be farmed for 200k+.)
    PRIZE_RATE = {"CHAMPION": 200, "ELITE_FOUR": 100, "GYM_LEADER": 100}

    def _calc_money_reward(self):
        rate = self.PRIZE_RATE.get(self.trainer_class)
        if rate is None:
            return 1000
        top = max((p.level for p in self.opponent_team if p), default=10)
        return rate * top

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
                from src.world import hms
                hm = hms.hm_for_badge(self.game.story_manager.get_current_region(), self.badge_reward)
                if hm and self.game.story_manager.inventory.get(hm, 0) <= 0:
                    msgs.append(f"You received {hms.item_name(hm)}! It opens new paths on your journey.")

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
                if item.startswith("POKEMON_"):
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

    def exit_battle(self, lost=False):
        for p in self.game.story_manager.player_team:
            forms.revert_form(p)
            if not lost and p.current_hp > 0:
                taken = getattr(self, "_battle_damage", {}).get(id(p), 0)
                p.counters["damage_battle"] = max(p.counters.get("damage_battle", 0), taken)
        if self.trainer_index is not None:
            area_key = self.game.story_manager.current_area_key
            self.game.story_manager.mark_trainer_defeated(area_key, self.trainer_index)

        if self.victory_flag and not (self.battle_type == "gym" and not self.player_won):
            # (a lost gym/League match must not count: Lance's beat_elite_four, beat_champion)
            self.game.story_manager.story_flags[self.victory_flag] = True

        if self.badge_reward:
            region = self.game.story_manager.get_current_region()
            earned = self.game.story_manager.badges.setdefault(region, [])
            if self.badge_reward not in earned:
                earned.append(self.badge_reward)
            from src.world import hms
            hms.give_for_badges(self.game.story_manager)  # this badge's HM (Cut, Surf...)

        money_reward = 0 if lost else self._calc_money_reward()
        if self.game.story_manager.inventory.get("AMULET_COIN", 0) > 0:
            money_reward *= 2
        self.game.story_manager.money += money_reward

        candy = 0 if lost else self._calc_candy_reward()
        if candy > 0:
            self.game.story_manager.add_item("RARE_CANDY", candy)

        reward_balls = self.rewards.get("balls", 3)

        key_items = self.game.loader.area_data.get("GAME_CONFIG", {}).get("KEY_ITEMS", [])
        for item, qty in self.rewards.items():
            if item == "balls":
                continue
            if item.startswith("POKEMON_"):
                if not lost:
                    from src.world import story_events
                    story_events.gift_pokemon(self.game, int(item[8:]))
                continue

            if item in key_items and self.game.story_manager.inventory.get(item, 0) > 0:
                self.game.story_manager.add_item("RARE_CANDY", 2)
            else:
                self.game.story_manager.add_item(item, qty)

        vf = str(self.victory_flag or "")
        if self.player_won and (vf == "beat_champion" or (vf.startswith("beat_") and vf.endswith("_champion"))):
            # Any region's title: home to celebrate, where the post-title story runs (Mom's call,
            # linked PCs, the road to the next region). The lobby would already be in rematch mode.
            story = self.game.story_manager
            story.story_flags[f"gym_progress_{story.current_area_key}"] = 0  # next visit: rematch from match 1
            # The title can be won outside the League (Unova: Ghetsis at N's Castle), so reset the
            # region's League too.
            from src.states.overworld import is_league
            region = story.get_current_region()
            for key, area in self.game.loader.area_data.get("STORY_PROGRESSION", {}).items():
                if str(area.get("region") or "").upper() == region and area.get("gym") and is_league(area["gym"]):
                    story.story_flags[f"gym_progress_{key}"] = 0
            if vf == "beat_champion":
                story.story_flags["beat_elite_four"] = True
            home = story.get_region_start(story.get_current_region()).get("start_area") or "PALLET_TOWN"
            try:  # persist the title right away (Mom's call, exit dialogue, region select read it)
                self.game.update_save_data()
                self.game.data.save()
            except Exception as e:  # never block the victory screen on a save error
                print("Champion save failed:", e)
            from src.states.overworld import AreaTransitionState
            self.game.change_state(AreaTransitionState(self.game, home, initial_message="You returned home to share your victory!"))
            return

        if self.battle_type == "gym":
            prog_key = f"gym_progress_{self.game.story_manager.current_area_key}"
            if self.player_won:
                self.game.story_manager.story_flags[prog_key] = self.game.story_manager.story_flags.get(prog_key, 0) + 1
            from src.states.overworld import GymLobbyState, evolve_ready_party
            lobby = GymLobbyState(self.game, None)
            if self.player_won and evolve_ready_party(self.game, lobby):
                return
            self.game.change_state(lobby)
            return

        if self.battle_type == "rival":
            if self.game.story_manager.get_current_region() == "JOHTO":  # Silver (whatever he's called)
                self.game.story_manager.story_flags["defeated_rival_johto"] = True
            else:
                self.game.story_manager.story_flags["defeated_rival_kanto"] = True

        if self.trainer_class == "RIVAL" and self.game.story_manager.current_area_key == "PALLET_TOWN":
            outcome = self.game.story_manager.get_victory_outcome(battle_type="rival")
            play_state_data = getattr(self, 'play_state_data', {})
            self.game.story_manager.balls_left += reward_balls + outcome.get("rewards", {}).get("balls", 5)
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
        self.game.story_manager.balls_left += reward_balls  # the one ball count (see PlayState)

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
        elif next_state is not None and not lost:
            from src.states.overworld import evolve_ready_party
            if evolve_ready_party(self.game, next_state):
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
        self._draw_weather(screen)

        if (self.phase == "FAINT_ANIM_RUNNING" or self.phase == "RETRACT_ANIM") and self.faint_anim.active:
            self.faint_anim.draw(screen)

        if self.phase == "ENEMY_SUMMON" and self.enemy_summon_anim:
            self.enemy_summon_anim.draw(screen)

        if self.phase == "PLAYER_SUMMON" and self.player_summon_anim:
            self.player_summon_anim.draw(screen)

        self.game.ui_manager.draw(screen)

    def update(self):
        self.anim_ctrl.update()
        self.renderer.tick()
        self._note_participant()

        if self.phase == "ANSWER_FEEDBACK":
            self._tick_answer_feedback()
            return

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
                        bench = any(p.current_hp > 0 and p is not self.player_pokemon
                                    for p in self.game.story_manager.player_team)
                        if self.current_opponent_idx + 1 < len(self.opponent_team) and bench:
                            self.phase = "SWITCH_PROMPT"
                            next_poke = self.opponent_team[self.current_opponent_idx + 1]
                            self._place_yes_no()

                            self.btn_yes.text = "YES"
                            self.btn_no.text = "NO"
                            self.btn_yes.callback = self.on_switch_yes
                            self.btn_no.callback = self.on_switch_no
                            self.btn_yes.set_visibility(True)
                            self.btn_no.set_visibility(True)

                            tr_display = (self.trainer_name
                                          or self.trainer_class)
                            msg = f"{tr_display} is about to use {next_poke.display_name}! Change Pokémon?"
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
                if self.player_hp <= 0 and self._start_pending_faint():
                    return  # our Pokemon went down to recoil on the KO turn
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

        if self._form_msgs and self.phase == "MENU" and not self.dialogue_box.visible and self.math_ui:
            msgs, self._form_msgs = self._form_msgs, []
            self.show_message(msgs, callback=self.return_to_menu)

        if self.dialogue_box.visible:
            self.dialogue_box.update()

        if self.phase in ["INTRO", "OUTRO", "VICTORY_TEXT", "REWARD_TEXT"]:
            return

        if self.phase == "RESOLVE_TURN":
            if self.dialogue_box.visible:
                if not self.dialogue_box.is_finished:
                    return
            if self.renderer.hp_animating() or self.anim_ctrl.is_lunging:
                return  # the next message waits for the attack and the HP bar

            if self.feedback_timer == 0:
                self.dialogue_box.visible = False
                if (self.player_hp <= 0 or self.opponent_hp <= 0) and self._start_pending_faint():
                    return
                if self._form_msgs:
                    msgs, self._form_msgs = self._form_msgs, []
                    self.dialogue_box.reset(msgs)
                    self.dialogue_box.set_visibility(True)
                    self.feedback_timer = 30
                elif self.turn_actions:
                    action = self.turn_actions.pop(
                        0
                    )
                    action()
                elif not self._turn_end_done and self.player_hp > 0 and self.opponent_hp > 0:
                    self._turn_end_done = True
                    weather_msgs = self._weather_end_of_turn() + self.effects_end_of_turn()
                    if weather_msgs:
                        self.dialogue_box.reset(weather_msgs)
                        self.dialogue_box.set_visibility(True)
                        self.feedback_timer = 30
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
                self.game.change_state(self)
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
            source_sprite = battle_sprite(self.player_pokemon, "player")
            target_sprite = battle_sprite(self.opponent_pokemon, "opponent")
            pos_rect = sprite_rect(self.game, source_sprite, "player")
        else:
            source_sprite = battle_sprite(self.opponent_pokemon, "opponent")
            target_sprite = battle_sprite(self.player_pokemon, "player")
            pos_rect = sprite_rect(self.game, source_sprite, "opponent")

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
        if self.phase != "DITTO_TRANSFORM":  # a wild Ditto transforms first (was a soft-lock)
            self.phase = "MENU"
        self.catch_phase = "DECISION"
        self.ball_pos = [0, 0]
        self.ball_target = [0, 0]
        self.shake_timer = 0
        self.ball_img = game.assets.ball_imgs[0]
        self.renderer = BattleRenderer(self.game)

        self.btn_yes.callback = self.catch_yes
        self.btn_no.callback = self.catch_no
        self.sos_ally = None  # an ally called by S.O.S., waiting to step in
        self.sos_chain = 0
        if self.no_usable_party:
            self.trigger_outro(win=False)

    # ---- S.O.S. battles (Sun/Moon, Ultra Sun/Ultra Moon) ----
    # A weakened wild Pokemon may call for help instead of attacking. The battle is one on one,
    # so the ally steps in once the caller is caught or knocked out, and it can call in turn.
    SOS_CALL_CHANCE = (0.5, 0.25)  # at half HP or less / at a fifth or less
    SOS_ANSWER_CHANCE = 0.35
    SOS_SAME_SPECIES = 0.5

    def _sos_pool(self):
        """This area's S.O.S. table ("sos_pool" in its area data), or {} where nobody answers."""
        if (self.is_boss_battle or self.victory_flag or getattr(self, "no_catch", False)
                or balance.is_legendary(self.opponent_pokemon.id)
                or getattr(self.opponent_pokemon, "raid_stage", None)):
            return {}
        data = self.game.loader.area_data
        area = data.get("STORY_PROGRESSION", {}).get(self.game.story_manager.current_area_key, {})
        return data.get(area.get("sos_pool") or "", {})

    def _try_sos_call(self):
        """The foe's turn spent calling for help. Returns the lines to show, or None (it attacks)."""
        pool = self._sos_pool()
        if not pool or self.sos_ally is not None or self.opponent_hp <= 0:
            return None
        ratio = self.opponent_hp / max(1, self.opp_max_hp)
        if ratio > 0.5 or random.random() > (self.SOS_CALL_CHANCE[0] if ratio > 0.2 else
                                             self.SOS_CALL_CHANCE[0] + self.SOS_CALL_CHANCE[1]):
            return None
        name = self.opponent_pokemon.display_name.upper()
        lines = [f"Foe {name} called for help!"]
        if random.random() > self.SOS_ANSWER_CHANCE:
            return lines + ["...But no one came."]
        from src.pokemon.data import Pokemon
        pid = (self.opponent_pokemon.id if random.random() < self.SOS_SAME_SPECIES
               else int(str(Utils.weighted_random_choice(pool)).split("_")[0]))
        ally = Pokemon(self.game.loader.fetch_specific(pid), self.game.assets, size_mult=3.125)
        levels.set_wild(self.game, ally, self.game.story_manager.current_area_key)
        self.sos_ally = ally
        return lines + [f"A wild {ally.display_name.upper()} came to help!",
                        f"It's waiting to step in when {name} is done."]

    def opponent_attack(self):
        if self.player_hp > 0 and self.opponent_hp > 0 and not self._status_stops_silently():
            lines = self._try_sos_call()
            if lines:
                self.dialogue_box.reset(lines)
                self.dialogue_box.set_visibility(True)
                self.feedback_timer = 30
                return
        super().opponent_attack()

    def _status_stops_silently(self):
        """A foe that can't act this turn (asleep, frozen, recharging, flinched) can't call for help;
        the attack path says why."""
        foe = self.opponent_pokemon
        return (getattr(foe, "status", None) in ("sleep", "freeze")
                or id(foe) in self.__dict__.get("_recharging", ()) or id(foe) in getattr(self, "_flinched", ()))

    def _sos_continue(self):
        """The waiting S.O.S. ally steps in. Returns False if there's none (or nobody left to fight it)."""
        ally, self.sos_ally = self.sos_ally, None
        if ally is None or not any(p.current_hp > 0 for p in self.game.story_manager.player_team):
            return False
        self.sos_chain += 1
        for b in (self.btn_yes, self.btn_no, getattr(self, "btn_ball", None)):
            if b is not None:
                b.set_visibility(False)
        self.catch_phase = "DECISION"
        self._mid_battle_throw = False
        self.player_won = False
        self.opponent_pokemon = ally
        self.opponent_team = [ally]
        self.current_opponent_idx = 0
        if self.player_pokemon.current_hp <= 0:  # our Pokemon went down too: the next one is sent in first
            self.player_pokemon = next(p for p in self.game.story_manager.player_team if p.current_hp > 0)
        self.game.music.play("wild", force=True)
        self.setup_battle_matchup()
        if self.check_ditto_transform():  # a Ditto ally transforms as it steps in
            return True
        self.enemy_summon_anim = PokemonSummonAnimation(self.game, ally, "opponent")
        self.phase = "ENEMY_SUMMON"
        self.dialogue_box.callback = None
        self.dialogue_box.reset(f"The wild {ally.display_name.upper()} stepped in!")
        self.dialogue_box.set_visibility(True)
        return True

    def try_trigger_wild_catch_prompt(self):
        if getattr(self, "no_catch", False):
            return False  # an uncatchable boss (Paldea titans): the win goes through trigger_outro
        if self.opponent_pokemon.id == 10500:
            return False
        if not self.game.story_manager.catch_unlocked():  # Hoenn: no Pokedex from Birch yet
            return False
        if self.opponent_pokemon.id == 245 and not self.game.story_manager.story_flags.get("suicune_encountered"):
            return False

        story = self.game.story_manager
        if catching.total_balls(story) > 0:
            self.phase = "CATCH_PROMPT"
            self._catch_prompt_text()
            self.catch_timer = 15 * FPS

            # Which ball to throw (only when you have more than one kind).
            if not hasattr(self, "btn_ball"):
                self.btn_ball = CommandButton((0, 0, 240, 62), "", self.game.assets.fonts["label"], self._next_ball,
                                              bg_color=theme.RUN, autosize=False)
                self.game.ui_manager.add_element(self.btn_ball)
            self.btn_ball.set_visibility(len(catching.balls_owned(story)) > 1)
            self._place_yes_no()
            self._catch_prompt_text()

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

        self.game.music.victory()
        form = (self.game.loader.area_data.get("FORM_MAP", {}).get(str(self.opponent_pokemon.id)) or {}).get("form")
        catch_only = balance.is_legendary(self.opponent_pokemon.id) or form in ("crystal", "shadow")
        if not catch_only or balance.is_legendary(self.opponent_pokemon.id):
            self._record_boss_win()

        if getattr(self, "no_catch", False):
            story = self.game.story_manager
            if self.victory_flag:
                story.story_flags[self.victory_flag] = True
            lines = list(getattr(self, "win_lines", None) or
                         [f"{self.opponent_pokemon.display_name.upper()} was defeated!"])
            for item, qty in getattr(self, "boss_rewards", {}).items():
                story.inventory[item] = story.inventory.get(item, 0) + qty
                lines.append(f"You received {forms.item_label(item).upper()}" + (f" x{qty}!" if qty > 1 else "!"))
            self.player_won = True
            self.phase = "OUTRO"
            self.dialogue_box.reset(lines)
            self.dialogue_box.callback = self._on_catch_exit
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

        if self.game.states["play"].balls_left > 0 and self.game.story_manager.catch_unlocked():
            self.phase = "CATCH_PROMPT"
            self.dialogue_box.reset(f"Will you catch {self.opponent_pokemon.name}?")
            self.catch_timer = 15 * FPS

            self._place_yes_no()

            self.btn_yes.set_visibility(True)
            self.btn_no.set_visibility(True)
        else:  # no balls: say so (a legendary can be found again) instead of silently leaving
            self.show_message([f"You have no Poke Balls left!",
                               f"{self.opponent_pokemon.display_name.upper()} got away..."],
                              callback=lambda: self._sos_continue() or self.on_flee_complete())

    def _raid_catch_to_party_pokemon(self, boss):
        """A caught raid boss joins as a normal-size, normal-form Pokemon; G-Max bosses keep the G-Max Factor."""
        from src.pokemon.data import Pokemon
        raw = self.game.loader.fetch_specific(boss.id, form="normal", is_shiny=boss.is_shiny)
        pokemon = Pokemon(raw, self.game.assets, size_mult=2.5)
        pokemon.is_shiny = boss.is_shiny
        pokemon.gmax_factor = boss.form == "gmax"
        return pokemon

    def _catch_prompt_text(self):
        story = self.game.story_manager
        ball = catching.selected(story)
        count = catching.owned(story, ball)
        if getattr(self, "btn_ball", None) is not None:
            self.btn_ball.text = f"{catching.label(ball)} x{count}"
        many = len(catching.balls_owned(story)) > 1  # the BALL button shows the count
        self.dialogue_box.reset(f"{self.opponent_pokemon.name} is weak!\nThrow a {catching.label(ball)}?"
                                + ("" if many else f" ({count} left)"))

    def _next_ball(self):
        story = self.game.story_manager
        catching.cycle(story)
        self._catch_prompt_text()
        self.catch_timer = 15 * FPS

    # The games' lines when a Pokemon breaks free, by how many times the ball shook.
    BREAK_FREE = ("Oh no! The Pokemon broke free!", "Aww! It appeared to be caught!",
                  "Aargh! Almost had it!", "Gah! It was so close, too!")

    def catch_yes(self):
        """Throw the chosen ball: the games' catch formula decides (src/pokemon/catching.py). A
        knocked-out Pokemon counts as having 1 HP left."""
        self.phase = "CATCH_ANIMATION"
        self.catch_phase = "THROWN"
        story = self.game.story_manager
        ball = catching.selected(story)
        catching.use(story, ball)
        self._thrown_ball = ball
        foe = self.opponent_pokemon
        terrain = self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(
            story.current_area_key, {}).get("battle_type", "")
        kw = dict(hp=max(1, self.opponent_hp), max_hp=self.opp_max_hp, turn=max(1, self.turn_count),
                  fishing=getattr(self, "fishing", False), terrain=terrain)
        if getattr(self, "_mid_battle_throw", False):  # from the Bag mid-battle: the plain odds
            self._catch_result = catching.throw(self.game, foe, ball, **kw)
        else:  # the catch window: bosses are a sure catch, other fails are halved
            self._catch_result = catching.window_throw(self.game, foe, ball, guaranteed=self._sure_catch(), **kw)
        img = self.game.assets.get_item_image(ball if ball != catching.POKE else "POKE_BALL")
        self.ball_img = pygame.transform.scale(img, (84, 84)) if img else self.game.assets.ball_imgs[0]

        self.btn_yes.set_visibility(False)
        self.btn_no.set_visibility(False)
        if hasattr(self, "btn_ball"):
            self.btn_ball.set_visibility(False)

        self.anim_ctrl.impact_shake = 0

        # The throw (games-style): an arc from your side up over the foe, which is drawn into the
        # ball; the ball drops to the ground, bounces, and tilts once per shake.
        self.ball_img = pygame.transform.smoothscale(self.ball_img, (56, 56))
        img = battle_sprite(self.opponent_pokemon, "opponent")
        self.foe_spot = battle_spot(self.game, self.opponent_pokemon, "opponent")
        if img is not None:  # the sprite's visible part (sprites have empty margins)
            ink = img.get_bounding_rect()
            top = self.foe_spot[1] - img.get_height() / 2 + ink.top
            feet = self.foe_spot[1] - img.get_height() / 2 + ink.bottom
        else:
            top, feet = self.foe_spot[1] - 60, self.foe_spot[1] + 60
        self.ball_start = (self.game.width * 0.18, self.game.height * 0.82)
        self.ball_target = [self.foe_spot[0], top - 24]
        self.ball_ground = feet - 22
        self.ball_pos = list(self.ball_start)
        self.catch_t = 0
        self.ball_angle = 0

    def _sure_catch(self):
        """Legendaries, mythicals and boss Pokemon are a sure catch at the catch window (Jordan)."""
        foe = self.opponent_pokemon
        return bool(balance.is_legendary(foe.id) or self.victory_flag or self.is_boss_battle
                    or foe.id in self.game.loader.all_boss_ids)

    def _record_boss_win(self):
        """A beaten boss counts for the story whether or not it is caught (Jordan's rule).
        A beaten legendary that was not caught keeps a rematch button (legend_rematch_<flag>)
        until it is caught, so the Pokedex can still be finished. The Crystal Onix and Orre's
        Shadow Pokemon stay catch-only (their flags mean "caught/snagged")."""
        if not self.victory_flag:
            return
        flags = self.game.story_manager.story_flags
        flags[self.victory_flag] = True
        if balance.is_legendary(self.opponent_pokemon.id):
            flags[f"legend_rematch_{self.victory_flag}"] = True

    def catch_no(self):
        self.btn_yes.set_visibility(False)
        self.btn_no.set_visibility(False)
        if hasattr(self, "btn_ball"):
            self.btn_ball.set_visibility(False)
        # Saying NO (or letting the 15 s prompt run out) after a KO still counts as a win.
        form = (self.game.loader.area_data.get("FORM_MAP", {}).get(str(self.opponent_pokemon.id)) or {}).get("form")
        if self.opponent_hp <= 0 and form not in ("crystal", "shadow"):
            self._record_boss_win()
        if self.opponent_hp <= 0 and self.sos_ally is not None:
            self._sos_continue()
            return
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
            from src.vfx.animations import ball_arc
            self.catch_t = getattr(self, "catch_t", 0) + 1
            if self.catch_phase == "THROWN":
                t = min(1.0, self.catch_t / 20)
                start = getattr(self, "ball_start", self.ball_pos)
                self.ball_pos = list(ball_arc(start, self.ball_target, t, 160))
                self.ball_angle = (getattr(self, "ball_angle", 0) + 32) % 360
                if t >= 1.0:
                    self.catch_phase, self.catch_t, self.ball_angle = "ABSORB", 0, 0
            elif self.catch_phase == "ABSORB":  # the foe turns white and is drawn into the ball
                if self.catch_t >= 14:
                    self.catch_phase, self.catch_t = "DROP", 0
            elif self.catch_phase == "DROP":  # down to the ground, one small bounce
                t = min(1.0, self.catch_t / 16)
                ground = getattr(self, "ball_ground", self.ball_target[1])
                top = self.ball_target[1]
                if t < 0.7:
                    k = t / 0.7
                    y = top + (ground - top) * k * k
                else:
                    k = (t - 0.7) / 0.3
                    y = ground - 26 * 4 * k * (1 - k)
                self.ball_pos = [self.ball_target[0], y]
                if t >= 1.0:
                    self.catch_phase = "SHAKE"
                    # one wobble per shake check passed (a critical capture wobbles once)
                    self.shake_timer = 20 + 30 * getattr(self, "_catch_result", (True, 3, False))[1]
            elif self.catch_phase == "SHAKE":
                left = self.shake_timer - 20  # the last 20 frames: a still pause before the result
                self.ball_angle = 0
                if left > 0:
                    k = (left % 30) / 30
                    if k > 0.4:  # a tilt one way and back, then still
                        import math as _m
                        self.ball_angle = 22 * _m.sin((k - 0.4) / 0.6 * 2 * _m.pi) * (1 if (left // 30) % 2 else -1)
                self.shake_timer -= 1
                if self.shake_timer <= 0:
                    success, shakes, critical = getattr(self, "_catch_result", (True, 3, False))
                    if not success:
                        self._broke_free(shakes)
                        return

                    if success:
                        if self.victory_flag:
                            self.game.story_manager.story_flags[self.victory_flag] = True
                            self.game.story_manager.story_flags.pop(f"legend_rematch_{self.victory_flag}", None)
                            if self.opponent_pokemon.name == "SNORLAX":
                                self.game.story_manager.story_flags["caught_snorlax"] = True

                        forms.revert_form(self.opponent_pokemon)  # a Primal boss is caught in its normal form
                        caught = self.opponent_pokemon
                        if getattr(caught, "raid_stage", None):
                            caught = self._raid_catch_to_party_pokemon(caught)

                        self.player_won = True
                        self.catch_phase = "CAUGHT"
                        self.catch_t = 0
                        caught_lines = self.game.assets.get_text("caught_pokemon", name=self.opponent_pokemon.name)
                        caught_lines = caught_lines if isinstance(caught_lines, list) else [caught_lines]
                        if critical:
                            caught_lines = ["A critical capture!"] + caught_lines
                        self.dialogue_box.reset(caught_lines)
                        catching.after_catch(self.game, caught, getattr(self, "_thrown_ball", None))
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

    def throw_from_bag(self):
        """A ball thrown from the Bag during a wild battle (it still has its HP): the foe gets its
        turn if the ball doesn't hold."""
        self._mid_battle_throw = True
        self.action_menu.set_visibility(False)
        if self.math_ui:
            self.math_ui.set_visibility(False)
        self.dialogue_box.reset([f"{self.game.player_name} threw a "
                                 f"{catching.label(catching.selected(self.game.story_manager))}!"])
        self.dialogue_box.set_visibility(True)
        self.catch_yes()

    def _broke_free(self, shakes):
        """The ball didn't hold: say so, then offer another throw (or end it if you're out)."""
        self.catch_phase = "DECISION"
        self.phase = "MESSAGE"
        lines = [self.BREAK_FREE[min(shakes, 3)]]
        story = self.game.story_manager
        if getattr(self, "_mid_battle_throw", False) and self.opponent_hp > 0:
            self._mid_battle_throw = False
            self.show_message(lines, callback=self.on_item_used)  # the foe's turn
            return
        if catching.total_balls(story) > 0:
            self.show_message(lines, callback=self.try_trigger_wild_catch_prompt)
        else:
            self.show_message(lines + ["You're out of Poke Balls!"], callback=self.catch_no)

    def _on_catch_exit(self):
        if self._sos_continue():
            return
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

        catching_now = self.phase == "CATCH_ANIMATION"
        hide_opponent = (catching_now and self.catch_phase in ["ABSORB", "DROP", "SHAKE", "CAUGHT"]) or \
                        (self.phase == "OUTRO" and self.catch_phase == "CAUGHT")
        # A knocked-out wild Pokemon stays in view while you decide to catch it (Jordan).
        show_ko = self.phase in ("CATCH_PROMPT", "CATCH_ANIMATION", "MESSAGE") and not hide_opponent

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
            hide_opponent=hide_opponent,
            show_fainted=show_ko,
        )
        self._draw_weather(screen)

        if (self.phase == "FAINT_ANIM_RUNNING" or self.phase == "RETRACT_ANIM") and self.faint_anim.active:
            self.faint_anim.draw(screen)
        if self.phase == "PLAYER_SUMMON" and getattr(self, "player_summon_anim", None):
            self.player_summon_anim.draw(screen)  # (a Pokemon sent in after a switch)

        self.game.ui_manager.draw(screen)

        if self.phase == "CATCH_PROMPT":  # the time left to decide, under YES / NO
            from src.ui import theme
            ratio = max(0.0, self.catch_timer / (15 * FPS))
            bar = pygame.Rect(self.btn_yes.rect.x, self.btn_no.rect.bottom + 10, self.btn_yes.rect.w, 8)
            pygame.draw.rect(screen, (210, 214, 224), bar, border_radius=4)
            pygame.draw.rect(screen, theme.BAG, (bar.x, bar.y, int(bar.w * ratio), bar.h), border_radius=4)

        if catching_now or (self.phase == "OUTRO" and self.catch_phase == "CAUGHT"):
            self._draw_catch(screen)

    def _draw_catch(self, screen):
        """The ball (and the foe being drawn in, then the stars of a catch)."""
        from src.vfx.animations import white_silhouette
        import math as _m
        foe = self.opponent_pokemon
        if self.catch_phase == "ABSORB" and foe.image is not None:
            k = min(1.0, self.catch_t / 14)
            img = white_silhouette(battle_sprite(foe, "opponent"), min(1.0, k * 2))
            w, h = img.get_size()
            sc = max(0.05, 1 - k)
            img = pygame.transform.smoothscale(img, (max(1, int(w * sc)), max(1, int(h * sc))))
            cx = self.foe_spot[0]
            cy = self.foe_spot[1] + (self.ball_target[1] - self.foe_spot[1]) * k
            img.set_alpha(int(255 * (1 - k * 0.5)))
            screen.blit(img, img.get_rect(center=(int(cx), int(cy))))
        ball = self.ball_img
        if getattr(self, "ball_angle", 0):
            ball = pygame.transform.rotate(ball, self.ball_angle)
        if self.catch_phase in ("SHAKE", "CAUGHT", "DROP"):  # a soft shadow under it
            gy = int(getattr(self, "ball_ground", self.ball_pos[1]) + 24)
            sh = pygame.Surface((60, 14), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (0, 0, 0, 90), sh.get_rect())
            screen.blit(sh, sh.get_rect(center=(int(self.ball_pos[0]), gy)))
        screen.blit(ball, ball.get_rect(center=(int(self.ball_pos[0]), int(self.ball_pos[1]))))
        if self.catch_phase == "CAUGHT":  # stars burst out once it's caught
            self.catch_t = getattr(self, "catch_t", 0) + 1
            k = min(1.0, self.catch_t / 30)
            if k < 1.0:
                for i in range(3):
                    a = -_m.pi / 2 + (i - 1) * 0.7
                    x = self.ball_pos[0] + _m.cos(a) * 70 * k
                    y = self.ball_pos[1] + _m.sin(a) * 70 * k
                    Utils.draw_star(screen, GOLD, (int(x), int(y)), int(12 * (1 - k)) + 3)


# [REF-0026: Battle Intro State]
class TrainerIntroState(GameState):
    """A trainer battle's opening, as in the games (Jordan, 10-30, from a fan game's battle):
    1. SLIDE_IN: over the battle scene, the foe slides in from the left onto its platform and you
       (seen from behind) from the right;
    2. CHALLENGE: each side's party bar slides in; "You are challenged by X!" (and the trainer's
       own words);
    3. FOE_OUT: "X sent out Y!": the trainer runs off to the right, the ball flies, Y appears and
       its box slides in from the left;
    4. PLAYER_OUT: "Go! Z!": you step off to the left, the ball flies, Z appears and your box slides
       in from the right; then the battle's menu. Steps 3 and 4 need no tap."""

    SLIDE_IN = 34      # frames (25 fps)
    BAR_IN = 12
    EXIT = 12
    BOX_IN = 10
    HOLD = 12          # a beat on each send-out line before moving on

    def __init__(self, game, trainer_sprite, dialogue_text, next_state):
        super().__init__(game)
        self.next_state = next_state
        self.input_delay = 20
        self.trainer_sprite = trainer_sprite
        self.phase = "SLIDE_IN"
        self.t = 0
        self.player_summon = None
        self.enemy_summon = None
        self.battle_bg = None
        self.foe_gone = self.me_gone = 0.0      # 0..1: how far each trainer has left
        self.foe_box_in = self.my_box_in = None  # frames since each box started sliding in
        self.hold = 0
        w, h = game.width, game.height
        self.box_rect = Utils.get_full_dialogue_rect(game)
        lines = dialogue_text if isinstance(dialogue_text, list) else [dialogue_text]
        lines = [ln for ln in lines if ln and str(ln).strip(" .") != ""]
        self.dialogue_box = ClassicDialogueBox(
            self.box_rect, [f"You are challenged by {self._foe_name()}!"] + lines,
            self.game.assets.fonts["med"], callback=self.on_dialogue_finish)
        self.dialogue_box.visible = False

        # The foe on its platform; you from behind, cut off by the text box (as in the games).
        self.foe_sprite = self._fit(trainer_sprite, h * 0.40)
        char_key = getattr(game, "player_character", "red")
        back = game.assets.get_player_image(char_key, back=True)
        front = game.assets.get_player_image(char_key, back=False)
        self.player_sprite = self._fit(back or front, h * 0.55)
        self.rival_sprite = self.trainer_sprite  # (older code reads it)

        team = [p for p in game.story_manager.player_team if p]
        self.player_party = [p.current_hp > 0 for p in team][:6]
        foes = [p for p in getattr(next_state, "opponent_team", []) or [] if p]
        self.foe_party = [p.current_hp > 0 for p in foes][:6]
        self.player_team_count = len(self.player_party)
        self.opponent_team_count = len(self.foe_party)
        self.ball_icon = pygame.transform.smoothscale(game.assets.ball_imgs[0], (30, 30))

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _fit(img, height):
        """Scale a trainer sprite so its visible part is `height` px tall (sprites have margins)."""
        if img is None:
            return None
        ink = img.get_bounding_rect()
        k = height / max(1, ink.height)
        return pygame.transform.scale(img, (max(1, int(img.get_width() * k)), max(1, int(img.get_height() * k))))

    def _foe_name(self):
        ns = self.next_state
        name = getattr(ns, "trainer_name", None)
        if not name:
            name = getattr(ns, "trainer_class", "TRAINER")
            if name == "RIVAL":
                name = getattr(self.game, "rival_name", None) or getattr(self.game, "rival_character", "BLUE")
        return str(name).upper()

    @staticmethod
    def _ease(t):
        t = max(0.0, min(1.0, t))
        return 1 - (1 - t) ** 3

    def _foe_pos(self):
        """Feet of the foe trainer: sliding in from the left, running off to the right."""
        from src.vfx.animations import feet_spot
        fx, fy = feet_spot(self.game, "opponent")
        fx += self.game.width * 0.03
        if self.phase == "SLIDE_IN":
            fx = -self.game.width * 0.25 + (fx + self.game.width * 0.25) * self._ease(self.t / self.SLIDE_IN)
        return fx + self.game.width * 0.45 * self.foe_gone, fy

    def _me_pos(self):
        """Bottom of your trainer: sliding in from the right, stepping off to the left."""
        x = self.game.width * 0.30
        if self.phase == "SLIDE_IN":
            x = self.game.width * 1.25 - (self.game.width * 1.25 - x) * self._ease(self.t / self.SLIDE_IN)
        return x - self.game.width * 0.55 * self.me_gone, self.box_rect.top + int(self.game.height * 0.16)

    def _line_shown(self):
        """The send-out line is fully typed (or a tap has finished it)."""
        box = self.dialogue_box
        return box.is_waiting_for_click or box.is_finished

    def on_dialogue_finish(self):
        ns = self.next_state
        if not ns.player_pokemon or not ns.opponent_pokemon:
            self.game.change_state(ns)
            return
        self._start_foe_out()

    def _start_foe_out(self):
        self.phase = "FOE_OUT"
        self.t = 0
        mon = self.next_state.opponent_pokemon
        self.dialogue_box.reset([f"{self._foe_name()} sent out {mon.display_name.upper()}!"])
        self.dialogue_box.callback = None
        self.dialogue_box.visible = True

    def _start_player_out(self):
        self.phase = "PLAYER_OUT"
        self.t = 0
        self.hold = 0
        mon = self.next_state.player_pokemon
        self.dialogue_box.reset([f"Go! {mon.display_name.upper()}!"])
        self.dialogue_box.callback = None
        self.dialogue_box.visible = True

    # ------------------------------------------------------------------ GameState
    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        if self.next_state and getattr(self.next_state, "background", None):
            self.battle_bg = self.next_state.background
        else:
            battle_type = getattr(self.next_state, "battle_type", "field")
            area_name = getattr(self.next_state, "area_name", "")
            bg_raw = self.game.assets.get_random_battle_background(battle_type, area_name)
            self.battle_bg = (pygame.transform.scale(bg_raw, (self.game.width, self.box_rect.top))
                              if bg_raw else None)

    def handle_events(self, events):
        if self.input_delay > 0:
            return
        for event in events:
            if self.phase == "CHALLENGE" and self.dialogue_box.visible and event.type == pygame.MOUSEBUTTONDOWN:
                self.dialogue_box.handle_event(event)

    def update(self):
        if self.input_delay > 0:
            self.input_delay -= 1
        self.t += 1
        if self.dialogue_box.visible:
            self.dialogue_box.update()

        if self.phase == "SLIDE_IN":
            if self.t >= self.SLIDE_IN:
                self.phase, self.t = "CHALLENGE", 0
                self.dialogue_box.visible = True

        elif self.phase == "FOE_OUT":
            self.foe_gone = min(1.0, self.t / self.EXIT)
            if self.foe_gone >= 1.0 and not self.enemy_summon:
                self.enemy_summon = PokemonSummonAnimation(self.game, self.next_state.opponent_pokemon, "opponent")
            if self.enemy_summon:
                self.enemy_summon.update()
                if self.enemy_summon.finished and self.foe_box_in is None:
                    self.foe_box_in = 0
            if self.foe_box_in is not None:
                self.foe_box_in += 1
                if self.foe_box_in >= self.BOX_IN and self._line_shown():
                    self.hold += 1
                    if self.hold >= self.HOLD:
                        self._start_player_out()

        elif self.phase == "PLAYER_OUT":
            self.me_gone = min(1.0, self.t / self.EXIT)
            if self.me_gone >= 0.6 and not self.player_summon:
                self.player_summon = PokemonSummonAnimation(self.game, self.next_state.player_pokemon, "player",
                                                            use_back_sprite=True)
            if self.player_summon:
                self.player_summon.update()
                if self.player_summon.finished and self.my_box_in is None:
                    self.my_box_in = 0
            if self.my_box_in is not None:
                self.my_box_in += 1
                if self.my_box_in >= self.BOX_IN and self._line_shown():
                    self.hold += 1
                    if self.hold >= self.HOLD:
                        self.dialogue_box.visible = False
                        self.game.change_state(self.next_state)

    # ------------------------------------------------------------------ drawing
    def _party_bar(self, screen, party, side, k):
        """A side's party: balls along a line with an arrow (empty slots as rings), sliding in."""
        if k <= 0:
            return
        w, h = self.game.width, self.game.height
        gap, n = 44, 6
        y = int(h * (0.24 if side == "foe" else 0.60))
        line_w = int(w * 0.40)
        if side == "foe":  # under the foe's box, top left; slides in from the left
            x0 = int(-line_w + (line_w + w * 0.04) * k)
            line = pygame.Rect(x0, y + 22, line_w, 5)
            balls_x = [x0 + 40 + i * gap for i in range(n)]
            arrow = [(line.right, line.centery), (line.right - 18, line.y - 7), (line.right - 18, line.bottom + 7)]
        else:  # above your box, bottom right; slides in from the right
            x0 = int(w - (line_w + w * 0.04) * k)
            line = pygame.Rect(x0, y + 22, line_w, 5)
            balls_x = [line.right - 40 - (n - 1 - i) * gap for i in range(n)]
            arrow = [(line.x, line.centery), (line.x + 18, line.y - 7), (line.x + 18, line.bottom + 7)]
        pygame.draw.rect(screen, (60, 70, 60), line)
        pygame.draw.polygon(screen, (60, 70, 60), arrow)
        order = party + [None] * (n - len(party))
        if side == "foe":
            order = list(reversed(order))
        for x, ok in zip(balls_x, order):
            c = (x + 15, y + 2)
            if ok is None:
                pygame.draw.circle(screen, (70, 70, 80), c, 12, 2)
            elif ok:
                screen.blit(self.ball_icon, self.ball_icon.get_rect(center=c))
            else:  # fainted: a greyed ball
                grey = self.ball_icon.copy()
                grey.fill((90, 90, 90, 0), special_flags=pygame.BLEND_RGBA_SUB)
                screen.blit(grey, grey.get_rect(center=c))

    def draw(self):
        screen = self.game.screen
        w = self.game.width
        if self.battle_bg:
            screen.blit(self.battle_bg, (0, 0))
        else:
            screen.fill((20, 40, 80))
        ns = self.next_state

        # The foe: trainer, then its Pokemon once out.
        if self.foe_sprite and self.foe_gone < 1.0:
            fx, fy = self._foe_pos()
            pad = self.foe_sprite.get_height() - self.foe_sprite.get_bounding_rect().bottom
            screen.blit(self.foe_sprite, self.foe_sprite.get_rect(midbottom=(int(fx), int(fy + pad))))
        if self.enemy_summon:
            self.enemy_summon.draw(screen)

        # You: from behind, then your Pokemon.
        if self.player_sprite and self.me_gone < 1.0:
            mx, my = self._me_pos()
            screen.blit(self.player_sprite, self.player_sprite.get_rect(midbottom=(int(mx), int(my))))
        if self.player_summon:
            self.player_summon.draw(screen)

        # The party bars: in during the challenge, out as each side sends its Pokemon.
        if self.phase in ("CHALLENGE", "FOE_OUT", "PLAYER_OUT"):
            k_in = self._ease(self.t / self.BAR_IN) if self.phase == "CHALLENGE" else 1.0
            if self.phase == "CHALLENGE" or self.foe_gone < 1.0:
                self._party_bar(screen, self.foe_party, "foe", k_in * (1 - self.foe_gone))
            if self.phase != "PLAYER_OUT" or self.me_gone < 1.0:
                self._party_bar(screen, self.player_party, "me", k_in * (1 - self.me_gone))

        # The boxes slide in as each Pokemon appears.
        r = getattr(ns, "renderer", None)
        if r is not None and self.foe_box_in is not None:
            k = self._ease(self.foe_box_in / self.BOX_IN)
            r.draw_foe_box(screen, ns.opponent_pokemon, ns.opponent_hp, ns.opp_max_hp, dx=-(1 - k) * w * 0.5)
        if r is not None and self.my_box_in is not None:
            k = self._ease(self.my_box_in / self.BOX_IN)
            r.draw_my_box(screen, ns.player_pokemon, ns.player_hp, ns.player_max_hp, dx=(1 - k) * w * 0.5)

        theme.draw_textbox(screen, self.box_rect)
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
