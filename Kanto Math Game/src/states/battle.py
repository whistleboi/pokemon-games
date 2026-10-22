# [REF-0001: System Imports]
import pygame
import random
from src.states.base import GameState
from src.utils import Utils
from src.vfx.renderer import BattleRenderer
from src.ui.panels import BattleActionMenu
from src.ui.widgets import MathBattleUI, Button, MoveButton
from src.ui.dialogue import ClassicDialogueBox
from src.pokemon.mechanics import TypeAdvantage
from src.pokemon import forms
from src.pokemon import balance
from src.pokemon import evolution
from src.pokemon import moves as movelib, affection
from src.world import levels
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

    def open_move_menu(self):
        """FIGHT: pick one of the four moves, then answer the math question to use it."""
        if self.phase != "MENU":
            return
        self.phase = "MOVE_SELECT"
        self.action_menu.set_visibility(False)
        self.dialogue_box.set_visibility(False)
        box = Utils.get_full_dialogue_rect(self.game)
        names = self._battle_moves(self.player_pokemon)
        bw, bh, gap = (box.width - 260) // 2, (box.height - 40) // 2, 12
        font, small = self.game.assets.fonts["small"], self.game.assets.fonts["tiny"]
        self._clear_move_buttons()
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
            x = box.x + 16 + (i % 2) * (bw + gap)
            y = box.y + 14 + (i // 2) * (bh + gap)
            btn = MoveButton((x, y, bw, bh), name.replace("-", " "), font, small,
                             (lambda n=name: self.choose_move(n)), mtype or "???",
                             self.TYPE_COLORS.get(mtype, (120, 120, 120)), detail, effect,
                             stab=bool(power and mtype) and mtype.upper() in own_types)
            self.move_buttons.append(btn)
        back = Button((box.right - 220, box.centery - 35, 200, 70), "BACK", self.game.assets.fonts["s_med"],
                      self.close_move_menu, bg_color=RED, autosize=False)
        self.move_buttons.append(back)
        for btn in self.move_buttons:
            self.game.ui_manager.add_element(btn)

    def _clear_move_buttons(self):
        for btn in self.move_buttons:
            if btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)
        self.move_buttons = []

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
                text = lines + ["Player is out of usable PKMN!", "Player whited out!"]
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
            else:
                score = 40 * acc if self._can_inflict(d.get("ailment"), defender) else 0
            scored.append((score, name))
        scored = [x for x in scored if x[0] > 0] or scored
        scored.sort(reverse=True)
        if len(scored) > 1 and random.random() < 0.2:
            return random.choice(scored)[1]
        return scored[0][1]

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
        """On every switch-in: extreme weather ends if its Pokemon left, then Mega/Primal changes."""
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
            out.append(f"{label} is hurt by its {'burn' if st == 'burn' else 'poison'}!")
        return out

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
        if attacker is self.player_pokemon:  # 5 hearts of affection: crits twice as often
            base = balance.CRIT_STAGES[max(0, min(int(crit_stage or 0), 3))]
            crit = random.random() < min(1.0, affection.crit_chance(attacker, base))
        if mode == "weak":
            roll = random.randint(*self.WEAK_ROLL)
        elif mode == "max_roll":
            roll = 100
        dmg, self._last_was_crit = balance.damage(
            self._level(attacker), power, attack, defense,
            stab=move_type in (attacker.types or []), effectiveness=effectiveness, weather=weather,
            crit=crit, crit_stage=crit_stage, roll=roll)
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
        return mon.stat_value("SPEED") * (0.5 if getattr(mon, "status", None) == "paralysis" else 1)

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

    def _award_battle_xp(self):
        """XP for the KO, as in the games: the Gen 7 formula with the foe's base XP yield and the
        level gap, 1.5x from trainers, 1.2x with strong affection, then growth.XP_BOOST for fast
        leveling. Returns messages."""
        foe = self.opponent_pokemon
        foe_level = self._level(foe)
        trainer = self.trainer_class != "WILD"
        if self.game.story_manager.inventory.get("EXP_SHARE", 0) > 0:
            earners = [p for p in self.game.story_manager.player_team if p]
        else:
            earners = [self.player_pokemon]
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
            gained = int(growth.battle_xp(base_yield, foe_level, my_level, trainer=trainer)
                         * affection.xp_mult(p))
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
        acc = d.get("accuracy")
        if acc and random.uniform(0, 100) >= acc:
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
            return min(dmg, defender_hp), lines, False
        if name == movelib.STRUGGLE:
            dmg = self._calculate_damage(attacker, defender, 50, 1.0, 1.0, category="PHYSICAL",
                                         move_type=None, defender_max_hp=defender_max_hp)
            mx = self.player_max_hp if attacker is self.player_pokemon else self.opp_max_hp
            self._adjust_hp(attacker, -max(1, mx // 4))
            return dmg, lines + [f"{att_label} is hit with recoil!"], False
        if not (d.get("power") or 0):
            if self._status_move_works(d, defender):
                ailment = "toxic" if name == "TOXIC" else d["ailment"]
                return 0, lines + [self._inflict(ailment, defender, def_label)], False
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
        if stopped:
            self.dialogue_box.reset(pre)
            self.dialogue_box.set_visibility(True)
            self.feedback_timer = 30
            return

        name = self._forced_move(mon) or self.chosen_move or self._battle_moves(mon)[0]
        self.player_move = name.replace("-", " ")
        self._answer_used = None
        damage, messages, _ = self._use_move(mon, self.opponent_pokemon, name, label,
                                             f"Foe {self.opponent_pokemon.display_name.upper()}",
                                             self.opp_max_hp // getattr(self, "opp_hp_mult", 1), self.opponent_hp)
        messages = pre + messages + self._answer_notes(label, damage)
        self._answer_mode = None
        self.opponent_hp = max(0, self.opponent_hp - damage)
        self.opponent_pokemon.current_hp = self.opponent_hp
        if damage:
            mon.counters["attacks"] = mon.counters.get("attacks", 0) + 1
            if self._last_was_crit:
                self._battle_crits[id(mon)] = self._battle_crits.get(id(mon), 0) + 1
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

        self.dialogue_box.reset(messages)
        self.dialogue_box.set_visibility(True)
        self.feedback_timer = 30

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
        if stopped:
            self.dialogue_box.reset(pre)
            self.dialogue_box.set_visibility(True)
            self.feedback_timer = 30
            return
        mon = self.player_pokemon
        name = self._forced_move(foe) or getattr(self, "_foe_next_move", None) or self._ai_choose(foe, mon)
        self._foe_next_move = None
        self.opponent_move = name.replace("-", " ")
        damage, messages, _ = self._use_move(foe, mon, name, label, mon.display_name.upper(),
                                             self.player_max_hp, self.player_hp)
        messages = pre + messages
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
            target_pos = (self.game.width * 0.73, self.game.height * 0.39)
            pos = self.opponent_pokemon.image.get_rect(center=target_pos)
            self.faint_anim.start(self.opponent_pokemon.image, pos.topleft)
        elif self.fainting_side == "player":
            # Always run the animation (its end moves the battle on): 60 Gen 6-9 species have no
            # back sprite, and skipping it froze the battle for good (Nemona's first battle).
            mon = self.player_pokemon
            p_img = getattr(mon, "back_image", None)
            if p_img is None and getattr(mon, "image", None) is not None:
                p_img = pygame.transform.flip(mon.image, True, False)
            if p_img is None:
                p_img = pygame.Surface((1, 1), pygame.SRCALPHA)
            target_p_pos = (self.game.width * 0.27, self.game.height * 0.69)
            player_pos = p_img.get_rect(center=target_p_pos)
            self.faint_anim.start(p_img, player_pos.topleft)

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
            crits = getattr(self, "_battle_crits", {}).get(id(p), 0)
            p.counters["crits"] = max(p.counters.get("crits", 0), crits)
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
            if self.trainer_name == "SILVER":
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
                    weather_msgs = self._weather_end_of_turn()
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
        if self.no_usable_party:
            self.trigger_outro(win=False)

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

        self.game.music.victory()
        form = (self.game.loader.area_data.get("FORM_MAP", {}).get(str(self.opponent_pokemon.id)) or {}).get("form")
        catch_only = balance.is_legendary(self.opponent_pokemon.id) or form in ("crystal", "shadow")
        if self.victory_flag and not catch_only:
            # A beaten roadblock boss (Snorlax) is gone whether or not you catch it. Legendaries,
            # the Crystal Onix and Orre's Shadow Pokemon count only when caught, so they can be
            # tried again instead of being lost for good.
            self.game.story_manager.story_flags[self.victory_flag] = True

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
        else:  # no balls: say so (a legendary can be found again) instead of silently leaving
            self.show_message([f"You have no Poke Balls left!",
                               f"{self.opponent_pokemon.display_name.upper()} got away..."],
                              callback=self.on_flee_complete)

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

                        forms.revert_form(self.opponent_pokemon)  # a Primal boss is caught in its normal form
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
        self._draw_weather(screen)

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
