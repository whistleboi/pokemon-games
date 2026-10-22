# [REF-0001: System Imports]
import pygame
import random
import math
import os
import re
import datetime
from src.states.base import GameState
from src.utils import Utils
from src.ui.dialogue import ClassicDialogueBox
from src.ui.widgets import Button
from src.ui.panels import CityActionMenu
from src.world.boss import BossManager
from src.world import seasons
from src.world import hoenn
from src.world import levels
from src.pokemon import evolution
from src.world import regional_forms
from src.pokemon import forms
from src.pokemon.data import Pokemon
from src.pokemon.contest import feebas_ready
from src.vfx.particles import ShinyBurst, Starburst, IdleSparkle
from src.world import story_events
from src.config import WHITE, BLACK, GREEN, BLUE, GOLD, RED, ORANGE, PURPLE, GRAY, FPS, VOLUME


def _fill_names(game, text):
    if not isinstance(text, str):
        return text
    text = (text.replace("{player_name}", getattr(game, "player_name", "TRAINER"))
                .replace("{rival_name}", getattr(game, "rival_name", "???")))
    if "{kanto_" in text:  # Mew's hint: Kanto species #1-150 only (other regions don't count)
        caught = game.story_manager.kanto_caught_count()
        text = text.replace("{kanto_caught}", str(caught)).replace("{kanto_missing}", str(150 - caught))
    return text


def _resolve_lines(game, value):
    """GAME_TEXT key(s) or literal line(s) -> list of lines with names filled in."""
    items = value if isinstance(value, list) else [value]
    lines = []
    for item in items:
        if isinstance(item, str) and item in game.assets.game_text:
            text = game.assets.game_text[item]
            lines.extend(text if isinstance(text, list) else [text])
        elif item:
            lines.append(item)
    return [_fill_names(game, line) for line in lines]


def _scaled_player_image(game, char_key):
    img = game.assets.get_player_image(char_key, back=False) if char_key else None
    if not img:
        return None
    h = int(game.height * 0.6)
    return pygame.transform.scale(img, (int(img.get_width() * (h / img.get_height())), h))


def _trainer_sprite(game, sprite_name):
    """Trainer art, falling back to the player-chosen rival when a region's sprite is missing."""
    if sprite_name != "{rival_character}":
        img = game.assets.get_trainer_image(sprite_name or "rival.png")
        if img:
            return img
    return (_scaled_player_image(game, getattr(game, "rival_character", None))
            or game.assets.get_trainer_image("rival.png"))


def _region_starter_id(game):
    story = game.story_manager
    sid = story.story_flags.get(f"starter_{story.get_current_region().lower()}")
    if sid:
        return sid
    return story.player_team[0].id if story.player_team else None


def _story_team(game, area_key, t_info):
    """A story trainer's team: picked by the player's starter ("team_choice"), at the exact
    levels from the games when given ("levels"), else around the top "level", else the area's."""
    team_ids = list((t_info.get("team_choice") or {}).get(str(_region_starter_id(game))) or t_info.get("team", []))
    team = [Pokemon(game.loader.fetch_specific(tid), game.assets, size_mult=3.125) for tid in team_ids]
    forms.mark_trainer_team(team, t_info)
    top = t_info.get("level")  # story beats set in early areas carry their own level
    if t_info.get("levels"):
        levels.set_team(team, list(t_info["levels"]), exact=True)
    elif top:
        levels.set_team(team, [max(2, top - (len(team) - 1 - i)) for i in range(len(team))])
    else:
        levels.set_team(team, levels.trainer_team_levels(game, area_key, len(team), boss=True))
    return team


def _start_event_battle(game, area_key, t_info, flag):
    """A story NPC's trainer battle (team chosen by the region starter when it has a team_choice)."""
    from src.states.battle import TrainerBattleState, TrainerIntroState
    team = _story_team(game, area_key, t_info)
    sprite = _trainer_sprite(game, t_info.get("sprite"))
    dlg = t_info.get("dialogue") or {}
    battle = TrainerBattleState(
        game, team, trainer_sprite=sprite, trainer_class=t_info.get("class", "TRAINER"),
        trainer_name=_fill_names(game, t_info.get("name")),
        custom_dialogue={k: _resolve_lines(game, v) for k, v in dlg.items() if k != "intro"},
        rewards=dict(t_info.get("rewards") or {"balls": 3}), battle_type="event",
        is_boss_battle=t_info.get("is_boss_battle", False), area_name=area_key, victory_flag=flag)
    return TrainerIntroState(game, sprite, t_info.get("_intro_lines") or ["..."], battle)


def _run_story_event(state, key, check, show):
    """Play a story NPC event (see src/world/story_events.py).
    check(condition) tests a menu condition; show(lines) shows dialogue and returns to the menu."""
    game = state.game
    story = game.story_manager
    ev = key if isinstance(key, dict) else story_events.get(key)
    flag = ev.get("flag")
    if flag and story.story_flags.get(flag):
        show(_resolve_lines(game, ev.get("done") or ev.get("lines") or ["..."]))
        return
    if not all(check(c) for c in ev.get("requires", [])):
        show(_resolve_lines(game, ev.get("fail") or ["You can't do that yet."]))
        return
    lines = _resolve_lines(game, ev.get("lines") or [])
    if ev.get("puzzle"):  # a math minigame (Dotted Hole's braille, a Rocket door code...)
        _start_event_puzzle(state, ev, lines, show)
        return
    if ev.get("battle"):
        t_info = dict(ev["battle"], _intro_lines=lines or None)
        game.change_state(_start_event_battle(game, story.current_area_key, t_info, flag))
        return
    for item, qty in (ev.get("gift_item") or {}).items():
        if item == "balls":
            story.balls_left = getattr(story, "balls_left", 0) + qty  # the one ball count
            lines.append(f"You received {qty} Poke Balls!")
            continue
        story.inventory[item] = story.inventory.get(item, 0) + qty
        lines.append(f"{getattr(game, 'player_name', 'You')} received the {forms.item_label(item).upper()}!")
    for item, qty in (ev.get("take_item") or {}).items():
        story.inventory[item] = max(0, story.inventory.get(item, 0) - qty)
    lines += _teach_move(game, ev.get("teach"))
    lines += story.evolve_party(ev.get("evolve"))  # Kubfu at the Towers of Two Fists
    if ev.get("purify"):  # Orre's Relic Stone
        names = story.purify_shadow()
        lines += ([f"{n}'s heart opened! It's no longer a Shadow Pokemon." for n in names]
                  or ["None of your Pokemon need purifying right now."])
    gift = story_events.gift_for_starter(ev.get("gift_pokemon"), _region_starter_id(game))
    if gift:
        lines.append(story_events.gift_pokemon(game, gift))
    if flag:
        story.story_flags[flag] = True
    show(lines or ["..."])


def _start_event_puzzle(state, ev, lines, show):
    """Run an event's puzzle (src/states/gym_puzzles.py). Solved: the event's flag and gifts,
    then its lines. Left or failed: back to the area with its "fail" lines."""
    from src.states.gym_puzzles import GymPuzzleState
    game = state.game
    story = game.story_manager

    def done(solved):
        if hasattr(state, "is_resuming"):
            state.is_resuming = True
        game.change_state(state)
        if not solved:
            show(_resolve_lines(game, ev.get("puzzle_fail") or ["You'll have to try again."]))
            return
        out = list(lines)
        for item, qty in (ev.get("gift_item") or {}).items():
            story.add_item(item, qty)
            out.append(f"{getattr(game, 'player_name', 'You')} received the {forms.item_label(item).upper()}!")
        if ev.get("flag"):
            story.story_flags[ev["flag"]] = True
        show(out or ["..."])

    game.change_state(GymPuzzleState(game, story.current_area_key, ev["puzzle"], done))


def _teach_move(game, teach):
    """A move tutor: {species id: move} for the first party Pokemon that can learn one."""
    from src.pokemon import moves as movelib
    for p in game.story_manager.player_team if teach else []:
        move = teach.get(str(p.id))
        if not move or move in (movelib.ensure_moves(game, p) or []):
            continue
        label = move.replace("-", " ")
        if len(p.moves) < movelib.MAX_MOVES:
            p.moves.append(move)
            return [f"{p.display_name.upper()} learned {label}!"]
        weakest = min(p.moves, key=lambda m: movelib.move_value(game, p, m))
        p.moves[p.moves.index(weakest)] = move
        return [f"{p.display_name.upper()} forgot {weakest.replace('-', ' ')} and learned {label}!"]
    return []


# [REF-0029: Overworld & Play Logic]

def _draw_season_hud(game, screen, area_key, x, y):
    """Season and today's weather under the ball count (seasonal regions only)."""
    label = seasons.hud_label(game, area_key)
    if label:
        text, color = label
        Utils.draw_text_outline(screen, text, game.assets.fonts["small"], color, x, y,
                                align="left", outline_color=BLACK)

class PlayState(GameState):
    # One Poke Ball count for the whole game: the story's. Routes used to keep their own copy,
    # and an old copy coming back (a revisited route, after a battle) erased balls you'd bought.
    @property
    def balls_left(self):
        return self.game.story_manager.balls_left

    @balls_left.setter
    def balls_left(self, value):
        self.game.story_manager.balls_left = value

    def __init__(self, game, restore_data=None):
        super().__init__(game)
        if hasattr(game.story_manager, "sync_rival"):
            game.story_manager.sync_rival()  # this region's rival (one per region per save)
        hoenn.apply_version(game)
        self.area_data = game.story_manager.get_current_area_data()
        self._inject_regional_data()

        self.game.story_manager.sync_badges()

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

        self.min_rounds = self.area_data.get("min_rounds", 1)

        if self.game.story_manager.inventory.get("BICYCLE", 0) > 0:
            if self.game.story_manager.story_flags.get(f"visited_{self.game.story_manager.current_area_key}"):
                self.min_rounds = 0

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
            # (balls_left is the story's own count; a saved snapshot of it would be stale)
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
        self.npc_sprite = None
        self.catch_selection_active = False
        self.selected_catch_idx = -1
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

        btn_x, btn_y = 20, 80
        btn_w, btn_h = 120, 40
        spacing = 10

        self.hud_buttons = [
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
            Button((btn_x, btn_y + (btn_h+spacing)*5, btn_w, btn_h), "JOURNAL",
                   game.assets.fonts["tiny"],
                   self._open_journal,
                   bg_color=PURPLE),
        ]

        if (self.game.story_manager.inventory.get("AIR_BALLOON", 0) > 0
                or self.game.story_manager.inventory.get("HM_FLY", 0) > 0):
            self.hud_buttons.append(Button((btn_x, btn_y + (btn_h+spacing)*6, btn_w, btn_h), "FLY",
                                           game.assets.fonts["tiny"],
                                           self._open_fly,
                                           bg_color=BLUE))

        if self.game.story_manager.inventory.get("TOWN_MAP", 0) > 0:
            map_idx = len(self.hud_buttons)
            self.hud_buttons.append(Button((btn_x, btn_y + (btn_h+spacing)*map_idx, btn_w, btn_h), "MAP",
                                           game.assets.fonts["tiny"],
                                           self._open_map,
                                           bg_color=GOLD))

        if self.game.story_manager.inventory.get("POKE_NAV", 0) > 0:
            nav_idx = len(self.hud_buttons)
            self.hud_buttons.append(Button((btn_x, btn_y + (btn_h+spacing)*nav_idx, btn_w, btn_h), "NAV",
                                           game.assets.fonts["tiny"],
                                           self._open_pokenav,
                                           bg_color=GREEN))

        opt_idx = len(self.hud_buttons)
        self.hud_buttons.append(Button((btn_x, btn_y + (btn_h+spacing)*opt_idx, btn_w, btn_h), "OPTIONS",
                                       game.assets.fonts["tiny"],
                                       self._open_options,
                                       bg_color=GRAY))

        # Side menus return to this same route: resume where we were (keep the catch choices,
        # don't roll new encounters).
        for btn in self.hud_buttons:
            if btn.text not in ("SAVE", "LOAD") and btn.callback:
                btn.callback = (lambda cb=btn.callback: (setattr(self, "is_resuming", True), cb()))
        _collapse_hud(self)

        self.btn_flee = Button(
            rect=(game.width - 200, game.height // 2 - 40, 180, 80),
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

    def _open_options(self):
        from src.states.menus import open_difficulty_options
        open_difficulty_options(self.game, self)

    def _open_journal(self):
        from src.states.systems import JournalState
        self.game.change_state(JournalState(self.game, self))

    def _open_map(self):
        from src.states.systems import MapState
        self.game.change_state(MapState(self.game, self))

    def _open_fly(self):
        from src.states.systems import FlyState
        self.game.change_state(FlyState(self.game, self))

    def _open_pokenav(self):
        from src.states.systems import PokeNavState
        self.game.change_state(PokeNavState(self.game, self))

    def _get_battle_background_for_area(self):
        """Returns a specific battle background filename based on the current area."""
        area_key = self.game.story_manager.current_area_key

        bg_config = self.area_data.get("backgrounds", {})
        if "battle" in bg_config:
            val = bg_config["battle"]
            if isinstance(val, list):
                # ARCHITECT: For wild routes/dungeons, pick a random variant from the list
                return random.choice(val)
            return val

        background_map = {
            "KANTO_POKEMON_TOWER": "battle_pokemon_tower.png",
            "MT_MOON": "battle_mt_moon.png",
            "ROCK_TUNNEL": "battle_rock_tunnel.png",
            "DIGGLETT_CAVE": "battle_diglett_cave.png",
            "VICTORY_ROAD": "battle_victory_road.png",
            "SEAFOAM_ISLANDS": "battle_seafoam_islands.png",
            "CERULEAN_CAVE": "battle_cerulean_cave.png"
        }
        return background_map.get(area_key)

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

        if "alt_forms" not in self.area_data:
            self.area_data["alt_forms"] = {"enabled": True, "weights": {}}

        target_weights = self.area_data["alt_forms"]["weights"]

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
        if self.area_data.get("area_type") != "wild_route":
            return False

        if not self.game.story_manager.story_flags.get("visited_BURNED_TOWER"):
            return False

        if random.random() < self.ROAMER_CHANCE:
            roamers = [243, 244]
            roamer_id = random.choice(roamers)

            caught = self.game.data.data.get("pokedex", {})
            for v in caught.values():
                if v['id'] == roamer_id:
                    return False

            raw = self.game.loader.fetch_specific(roamer_id)
            pokemon = Pokemon(raw, self.game.assets, size_mult=2.0)
            # Roamers suit the route (Lv 40 at most, as in HeartGold/SoulSilver) instead of an
            # L50 that one-shots a badge-4 team.
            area_key = self.game.story_manager.current_area_key
            pokemon.level = max(10, min(self.ROAMER_MAX_LEVEL, levels.area_level(self.game, area_key) + 5))
            pokemon.current_hp = pokemon.get_max_hp()

            from src.states.battle import WildBattleState
            # The battle catches into this route (not an older one left in game.states).
            self.game.states["play"] = self
            battle_state = WildBattleState(self.game, pokemon, area_key)
            battle_state.play_state_data = {
                "balls_left": self.balls_left, "current_streak": self.current_streak,
                "rounds_completed": self.rounds_completed, "pending_wild_encounters": 0,
                "initial_round_active": False}
            self.game.change_state(battle_state)
            return True
        return False

    ROAMER_CHANCE = 0.10
    ROAMER_MAX_LEVEL = 40

    def save_game(self):
        from src.states.menus import SaveState
        self.game.change_state(SaveState(self.game, self))

    def start(self):
        if self.dialogue_box not in self.game.ui_manager.elements:
            self.game.ui_manager.add_element(self.dialogue_box)
        for btn in self.hud_buttons:
            if btn not in self.game.ui_manager.elements:
                self.game.ui_manager.add_element(btn)
        if self.btn_flee not in self.game.ui_manager.elements:
            self.game.ui_manager.add_element(self.btn_flee)
        if self.btn_yes not in self.game.ui_manager.elements:
            self.game.ui_manager.add_element(self.btn_yes)
        if self.btn_no not in self.game.ui_manager.elements:
            self.game.ui_manager.add_element(self.btn_no)

        if self.is_progression_paused:
            for btn in self.route_buttons:
                if btn not in self.game.ui_manager.elements:
                    self.game.ui_manager.add_element(btn)

        pygame.event.clear()

        visited_flag = f"visited_{self.game.story_manager.current_area_key}"
        if not self.game.story_manager.story_flags.get(visited_flag, False):
            self.game.story_manager.story_flags[visited_flag] = True

        if self.is_resuming:
            self.is_resuming = False
            if self.is_progression_paused:
                self.show_progression_menu()
            else:
                if self.catch_selection_active:
                    self.show_dialogue(["Choose a Pokémon to catch!"])
                elif self.p_data[0] is None and not self.boss_manager.in_boss_mode:
                    self.show_progression_menu()
            return

        if self.check_roaming_encounter():
            return

        num_johto = len(self.game.story_manager.badges.get("JOHTO", []))
        if (self.game.story_manager.inventory.get("MYSTERY_EGG", 0) > 0
            and num_johto >= 2
            and not self.game.story_manager.story_flags.get("egg_hatched")):
            self.trigger_egg_hatch()
            return

        gauntlet_areas = ["INDIGO_PLATEAU", "KANTO_ROUTE_25"]
        current_area = self.game.story_manager.current_area_key
        is_gauntlet_area = current_area in gauntlet_areas
        if is_gauntlet_area and self.rounds_completed == 0 and self.fresh_entry:
            self.create_checkpoint()

        on_enter = self.area_data.get("on_enter_event")
        if on_enter and on_enter.get("type") == "trainer_battle":
            v_flag = on_enter.get("flag_check")
            cond = on_enter.get("condition")
            met = True
            if v_flag and self.game.story_manager.story_flags.get(v_flag):
                met = False
            elif cond and not self._check_route_condition(cond, False):
                met = False

            if met:
                self.trigger_scripted_on_enter_battle(on_enter)
                return

        if self.pending_wild_encounters > 0:
            self.trigger_wild_encounter()
        elif self.initial_round_active and self.rounds_completed == 0:
            self.start_initial_round()
        else:
            self.show_progression_menu()

    def trigger_scripted_on_enter_battle(self, on_enter):
        """Helper to handle the complex on_enter battle setup logic."""
        self.rounds_completed += 1

        trainer_info = dict(on_enter["trainer"])
        team_ids = trainer_info.get("team", [])
        if team_ids and isinstance(team_ids, list) and len(team_ids) > 0 and isinstance(team_ids[0], list):
            trainer_info["team"] = random.choice(team_ids)
        opponent_team = _story_team(self.game, self.game.story_manager.current_area_key, trainer_info)

        from src.states.battle import TrainerBattleState, TrainerIntroState
        trainer_sprite = _trainer_sprite(self.game, trainer_info.get("sprite"))  # rival art too
        battle_state = TrainerBattleState(
            self.game, opponent_team, trainer_sprite=trainer_sprite,
            trainer_class=trainer_info["class"], trainer_name=_fill_names(self.game, trainer_info.get("name")),
            victory_flag=on_enter.get("flag_check"),
            is_boss_battle=trainer_info.get("is_boss_battle", False),
        )
        intro_text = on_enter.get("dialogue_override", "Stop right there!")
        if isinstance(intro_text, str):
            intro_text = [intro_text]
        self.game.change_state(TrainerIntroState(self.game, trainer_sprite, intro_text, battle_state))

    def trigger_egg_hatch(self):
        """Handles the transition into the Mystery Egg hatching sequence."""
        self.game.story_manager.story_flags["egg_hatched"] = True

        togepi_id = 175

        egg_raw = {
            "id": 0, "name": "Mystery Egg", "display_name": "Mystery Egg",
            "img": None, "back_img": None, "cry": None, "is_shiny": False,
            "form": "normal", "stage": 1, "types": [], "stats": {}
        }

        from src.pokemon.data import Pokemon
        egg_poke = Pokemon(egg_raw, self.game.assets)

        egg_path = os.path.join(self.game.assets.pokemon_sprites_dir, "egg.png")
        if os.path.exists(egg_path):
            try:
                surf = pygame.image.load(egg_path).convert_alpha()
                s = int(self.game.assets.width // 3.5)
                egg_poke.image = pygame.transform.scale(surf, (s, s))
            except Exception:
                pass

        if "MYSTERY_EGG" in self.game.story_manager.inventory:
            self.game.story_manager.inventory["MYSTERY_EGG"] = 0

        team = self.game.story_manager.player_team
        if len(team) < 6:
            target_idx = len(team)
            team.append(egg_poke)
            context = "party"
        else:
            target_idx = self.game.story_manager.deposit_to_pc(egg_poke)
            context = "pc"

        from src.states.systems import EvolutionState
        self.game.change_state(EvolutionState(
            self.game, egg_poke, togepi_id, target_idx,
            context=context, return_state=self
        ))

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
            self.rounds_completed += 1
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
            wild_pool_pct = self._get_wild_pool(self.area_data)

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
        forms.mark_trainer_team(opponent_team, trainer_info)
        is_boss = bool(trainer_info.get("is_boss_battle") or trainer_info.get("villain") == "leader"
                       or trainer_class in ("ROCKET_LEADER", "RIVAL"))
        levels.set_team(opponent_team, levels.trainer_team_levels(self.game, area_key, len(opponent_team), is_boss))

        bg_file = self._get_battle_background_for_area()

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
            is_boss_battle=trainer_info.get("is_boss_battle", False),
            area_name=area_key,
            victory_flag=victory_flag,
            background_image=bg_file
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
        pygame.event.clear()
        self.game.change_state(intro_state)

    def _get_wild_pool(self, area_data):
        """The current area's percentage pool: day/night split, then season and weather."""
        pool = regional_forms.extend_pool(self.game, self._base_wild_pool(area_data))
        return seasons.adjust_pool(self.game, pool, self.game.story_manager.current_area_key)

    def _draw_season_hud(self, screen, x, y):
        _draw_season_hud(self.game, screen, self.game.story_manager.current_area_key, x, y)

    def _base_wild_pool(self, area_data):
        """Returns the percentage pool dict for the current area, respecting day/night splits."""
        hour = datetime.datetime.now().hour
        is_night = hour < 6 or hour >= 20
        night_key = area_data.get("night_pool_percentages")
        day_key = area_data.get("day_pool_percentages")
        if is_night and night_key:
            pool = self.game.loader.area_data.get(night_key, {})
            if pool:
                return pool
        if not is_night and day_key:
            pool = self.game.loader.area_data.get(day_key, {})
            if pool:
                return pool
        base_key = area_data.get("wild_pool_percentages")
        return self.game.loader.area_data.get(base_key, {}) if base_key else {}

    def trigger_wild_encounter(self):
        if self.balls_left <= 0:  # no catch screen without balls: say so and go back to the menu
            self.p_data = [None, None, None]
            self.catch_selection_active = False
            self.pending_wild_encounters = 0
            self.show_dialogue([self.game.assets.get_text("no_balls_left")], callback=self.show_progression_menu)
            return
        wild_pool_pct = self._get_wild_pool(self.area_data)
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
            levels.set_wild(self.game, p, self.game.story_manager.current_area_key)

        for p in self.p_data:
            if p:
                self.game.data.mark_seen(p.id)

        self.catch_selection_active = True
        self.selected_catch_idx = -1
        self.show_dialogue(["Choose a Pokémon to catch!"])

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
            rounds_completed=self.rounds_completed
        )
        self.game.story_manager.balls_left = self.balls_left
        self.game.story_manager.current_streak = self.current_streak

    def generate_math_set(self, score_unused=0, num_options=3):
        """Catching + battle questions. Difficulty comes from the player's
        OPTIONS setting (or AUTO = region + badges). See src/core/math_engine.py."""
        level = self.game.story_manager.get_math_level()
        return self.game.math.generate(level, num_options=num_options)

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
            if self.dialogue_box.visible:
                self.dialogue_box.handle_event(event)
                if not self.catch_selection_active:
                    continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                rect = getattr(self, "speak_rect", None)
                if rect is not None and rect.collidepoint(event.pos) and not self.catch_selection_active:
                    from src.core import speech
                    speech.say(speech.math_words(self.problem_str))
                    continue
                if not self.ball_active and self.input_delay == 0 and self.pause_timer == 0 and self.balls_left > 0:
                    if self.catch_selection_active:
                        self.check_selection(event.pos)
                    elif not self.dialogue_box.visible:
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

    def check_selection(self, pos):
        """Allows the player to click a Pokemon sprite to target it for catching."""
        for i, p in enumerate(self.p_data):
            if p is None or p.image is None:
                continue

            cx = self.get_cx(i)
            hover_y = math.sin(pygame.time.get_ticks() * p.bob_speed + p.bob_offset) * p.bob_amount

            rect = p.image.get_rect(center=(cx, self.sprite_y + hover_y))
            hitbox = rect.inflate(20, 20)

            if hitbox.collidepoint(pos):
                self.selected_catch_idx = i
                self.catch_selection_active = False
                self.question_timer = 30 * FPS
                self.dialogue_box.visible = False
                return

    def show_progression_menu(self):
        self.is_progression_paused = True
        self.dialogue_box.visible = False

        area_key = self.game.story_manager.current_area_key
        trainer_pool = self.area_data.get("trainer_pool", [])
        trainers_left = any(
            not self.game.story_manager.is_trainer_defeated(area_key, i)
            for i in range(len(trainer_pool))
        )

        default_menu = [
            {"text": "CATCH WILD PKMN", "action": "CATCH", "condition": "has_balls", "color": "BLUE"},
            {"text": "LOOK FOR TRAINER", "action": "TRAINER", "condition": "has_trainers", "color": "BLUE"},
            {"text": "BATTLE WILD PKMN", "action": "BATTLE", "condition": "has_balls", "color": "GREEN"},
            {"text": "EXIT ROUTE", "action": "EXIT", "condition": "can_exit", "color": "RED"}
        ]

        menu_config = self.area_data.get("route_menu", default_menu)

        for btn in self.route_buttons:
            if btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)
        self.route_buttons.clear()

        valid_options = []
        flags = self.game.story_manager.story_flags
        for item in menu_config:
            condition = item.get("condition")
            action = item.get("action")
            flag_condition = item.get("flag_condition")
            if flag_condition:
                parts = flag_condition.split()
                if action == "GALACTIC_GAUNTLET" and parts[0] == "not" and trainer_pool and not trainers_left:
                    flags[parts[1]] = True
                if parts[0] == "not" and len(parts) == 2:
                    if flags.get(parts[1]):
                        continue
                elif not flags.get(parts[0]):
                    continue

            if action == "BATTLE":
                valid_options.append(item)
                continue

            if condition in ["has_balls", "has_trainers"] and not self._check_route_condition(condition, trainers_left, item):
                item_copy = item.copy()
                item_copy["disabled"] = True
                item_copy["color"] = "GRAY"
                valid_options.append(item_copy)
            elif self._check_route_condition(condition, trainers_left, item):
                valid_options.append(item)

        if not valid_options:
            if self.rounds_completed >= self.min_rounds or not trainers_left:
                valid_options.append({"text": "EXIT ROUTE", "action": "EXIT", "color": "RED"})

        btn_w, btn_h = 280, 80
        gap_x, gap_y = 60, 40
        cols = 3

        count = len(valid_options)
        rows = (count + cols - 1) // cols

        box_top = Utils.get_full_dialogue_rect(self.game).top

        total_h = rows * btn_h + (rows - 1) * gap_y
        start_y = box_top - total_h - 30
        center_x = self.game.width // 2

        for i, item in enumerate(valid_options):
            row = i // cols
            col = i % cols

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

            btn = Button(
                pygame.Rect(x, y, btn_w, btn_h),
                item["text"],
                self.game.assets.fonts["tiny"],
                callback,
                bg_color=bg_color,
                autosize=False
            ).arm(500)  # a quick tap left over from the last round can't press an exit
            self.route_buttons.append(btn)
            self.game.ui_manager.add_element(btn)

        self.input_delay = 20

    def _check_route_condition(self, condition, trainers_left, item=None):
        if not condition:
            return True

        if isinstance(condition, (list, tuple)):
            return all(self._check_route_condition(c, trainers_left, item) for c in condition)
        if isinstance(condition, dict) and "any" in condition:  # {"any": [...]}: one is enough
            return any(self._check_route_condition(c, trainers_left, item) for c in condition["any"])
        if isinstance(condition, str) and condition.startswith("not:"):
            return not self._check_route_condition(condition[4:], trainers_left, item)

        if isinstance(condition, str) and condition.startswith("has_item:"):
            return self.game.story_manager.inventory.get(condition[9:], 0) > 0
        if isinstance(condition, str) and condition.replace(" ", "").startswith("badges_less:"):
            # "badges_less: N": fewer than N badges in this region (Route 22's early rival)
            story = self.game.story_manager
            need = int(condition.split(":", 1)[1])
            return len(story.badges.get(story.get_current_region(), [])) < need
        if condition == "has_balls":
            return self.balls_left > 0
        if condition == "has_SQUIRT_BOTTLE":
            return self.game.story_manager.inventory.get("SQUIRT_BOTTLE", 0) > 0 and not self.game.story_manager.story_flags.get("defeated_sudowoodo")
        if condition == "has_stormbadge":
            return self.game.story_manager.has_badge("STORMBADGE")
        if condition == "has_glacier_badge":
            return self.game.story_manager.has_badge("GLACIER")
        if condition == "has_trainers":
            return trainers_left
        if condition == "no_trainers":
            return not trainers_left
        if condition == "can_headbutt":
            has_helmet = self.game.story_manager.inventory.get("ROCKY_HELMET", 0) > 0
            return has_helmet and self.area_data.get("has_trees", False)
        if condition == "can_fish":
            inv = self.game.story_manager.inventory
            has_rod = any(inv.get(r, 0) > 0 for r in ("OLD_ROD", "GOOD_ROD", "SUPER_ROD"))
            return has_rod and self.area_data.get("can_fish", False)
        if condition == "can_battle":
            return True
        if condition == "has_EON_TICKET":
            return self.game.story_manager.inventory.get("EON_TICKET", 0) > 0
        if condition == "can_dive":
             return self.area_data.get("battle_type") == "ocean" and self.game.story_manager.inventory.get("DIVE_GEAR", 0) > 0

        if condition == "mew_available":
            has_spotted = (self.game.story_manager.story_flags.get("mew_spotted_mt_moon", False)
                           and self.game.story_manager.kanto_caught_count() >= 150)
            has_caught = self.game.story_manager.story_flags.get("caught_mew", False)
            return has_spotted and not has_caught and not trainers_left

        if condition == "can_battle_red_gyarados":
            # As in the games: the Red Gyarados comes first, then Lance and the Rocket Hideout.
            boss_beaten = self.game.story_manager.story_flags.get("defeated_red_gyarados", False)
            return not boss_beaten and not trainers_left

        if condition == "can_exit":
            if self.area_data.get("area_type") == "town":
                return True
            if self.balls_left <= 0:
                return True
            if self.rounds_completed >= self.min_rounds:
                return True
            # Nothing left to play here: no wild battles on the menu and every trainer beaten
            # (the Radio Tower cleared over two visits used to leave no way out).
            wild = any(o.get("action") in ("CATCH", "BATTLE") for o in self.area_data.get("route_menu", []))
            return not wild and not trainers_left

        if condition == "has_silph_scope":
            return self.game.story_manager.inventory.get("SILPH_SCOPE", 0) > 0
        if condition == "has_rainbow_wing":
            return self.game.story_manager.inventory.get("RAINBOW_WING", 0) > 0
        if condition == "has_8_badges":
            return sum(len(b) for b in self.game.story_manager.badges.values()) >= 8
        if condition == "has_8_kanto_badges":
            kanto_badges = {"BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH", "VOLCANO", "EARTH"}
            player_badges = set(self.game.story_manager.badges.get("KANTO", []))
            return kanto_badges.issubset(player_badges)
        if condition == "has_8_johto_badges":
            johto_badges = {"ZEPHYR", "HIVE", "PLAIN", "FOG", "STORMBADGE", "MINERAL", "GLACIER", "RISING"}
            player_badges = set(self.game.story_manager.badges.get("JOHTO", []))
            return johto_badges.issubset(player_badges)

        if condition.startswith("has_") and condition.endswith("_badge"):
            from src.world.hms import _norm
            want = _norm(condition[4:-6])  # case and "_BADGE" don't matter ("KNuckle", "COAL_BADGE")
            story = self.game.story_manager
            # This region's badges: Galar's and Paldea's Grass Badges are different badges.
            return any(_norm(b) == want for b in story.badges.get(story.get_current_region(), []))

        special = self.game.story_manager.special_condition(condition)
        if special is not None:  # party_has:493, all_unown_registered
            return special
        if isinstance(condition, str) and condition.startswith("caught_range:"):
            lo, hi = (int(x) for x in condition.split(":", 1)[1].split("-"))
            return self.game.story_manager.caught_in_range(lo, hi) >= hi - lo + 1  # e.g. all of #1-251
        if condition == "boss_defeated":
            boss_data = self.area_data.get("area_boss", {})
            victory_flag = boss_data.get("victory_flag")

            if victory_flag:
                return self.game.story_manager.story_flags.get(victory_flag, False)
            default_flag = f"{self.game.story_manager.current_area_key}_boss_defeated"
            return self.game.story_manager.story_flags.get(default_flag, False)
        if condition == "boss_available":
            is_defeated = self._check_route_condition("boss_defeated", trainers_left)
            if is_defeated or trainers_left:
                return False

            if item and item.get("has_SILPH_SCOPE"):
                if self.game.story_manager.inventory.get("SILPH_SCOPE", 0) <= 0:
                    return False
            return True

        if condition == "boss_not_defeated":
            return not self._check_route_condition("boss_defeated", trainers_left, item)
        if condition == "boss_available_with_flute":
            return self.game.story_manager.inventory.get("POKE_FLUTE", 0) > 0 and not self.game.story_manager.story_flags.get("KANTO_ROUTE_11_boss_defeated", False)
        if condition == "snorlax_defeated":
            return self.game.story_manager.story_flags.get("KANTO_ROUTE_11_boss_defeated", False) or self.game.story_manager.story_flags.get("caught_snorlax", False)
        if condition == "can_access_route_11":
            has_flute = self.game.story_manager.inventory.get("POKE_FLUTE", 0) > 0
            is_defeated = self.game.story_manager.story_flags.get("KANTO_ROUTE_11_boss_defeated", False)
            return has_flute or is_defeated

        if condition == "dungeon_cleared":
            if not item:
                return False
            areas = item.get("required_areas", [])
            for area in areas:
                a_data = self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(area)
                if not a_data:
                    continue

                t_pool = a_data.get("trainer_pool", [])
                for i in range(len(t_pool)):
                    if not self.game.story_manager.is_trainer_defeated(area, i):
                        return False
            return True
        if condition == "dungeon_boss_available":
            return not self._check_route_condition("boss_defeated", trainers_left) and self._check_route_condition("dungeon_cleared", trainers_left, item)

        if isinstance(condition, str) and condition.startswith("has_")                 and self.game.story_manager.inventory.get(condition[4:].upper(), 0) > 0:
            return True  # "has_silver_wing": holding the SILVER_WING
        if isinstance(condition, str):
            return self.game.story_manager.story_flags.get(condition, False)

        return True

    def _get_route_callback(self, item):
        action = item.get("action")
        if action == "CATCH":
            return self.action_search_pokemon
        if action == "TRAINER":
            return self.action_search_trainer
        if action == "BATTLE":
            return self.action_battle_wild
        if action == "BOSS":
            if item.get("boss"):
                return lambda b=item["boss"]: self.action_challenge_boss(b)
            return self.action_challenge_boss
        if action == "HEADBUTT":
            return self.action_headbutt
        if action == "DIVE":
            return self.action_dive
        if action == "FISH":
            return self.action_fish
        if action in ["EXIT", "TRAVEL"]:
            target = item.get("target") or item.get("target_area")
            return lambda t=target: self.action_exit_route(t)
        if action == "GALACTIC_GAUNTLET":
            return self.action_search_trainer
        if action == "MAX_RAID":
            return self.action_max_raid
        if action == "BERRY":
            return self.action_pick_berries
        if action == "WEATHER_DIRECTOR":
            return self.visit_weather_director
        if action == "EVENT":
            return lambda e=item.get("event") or {}: self.story_event(e)
        if action == "CAMP":
            return self.open_camp
        if action == "HOENN_EVENT":
            return lambda e=item.get("event"): self.hoenn_event(e)
        if action == "NPC":
            key = item.get("dialogue") or item.get("target")
            if key in story_events.ROUTE_METHODS:
                return getattr(self, story_events.ROUTE_METHODS[key])
            if story_events.get(key):
                return lambda k=key: self.story_event(k)
            if key in self.game.assets.game_text:
                return lambda k=key: self._route_npc_text(k)
        return lambda: print(f"Unknown action: {action}")

    def action_pick_berries(self):
        """Berry trees: once a day per route, pick a few of the berries that grow here."""
        from src.pokemon.poffin import berry_name
        self.is_progression_paused = True
        self.hide_menu_buttons()
        story = self.game.story_manager
        trees = self.area_data.get("berry_trees", [])
        flag = f"berries_picked_{story.current_area_key}"
        today = datetime.date.today().isoformat()
        if not trees:
            lines = ["There are no berry trees here."]
        elif story.story_flags.get(flag) == today:
            lines = ["The berry trees have already been picked today.", "Come back tomorrow!"]
        else:
            story.story_flags[flag] = today
            bonus, season_lines = seasons.berry_bonus(self.game, story.current_area_key)
            picked = {}
            for _ in range(max(1, random.randint(2, 4) + bonus)):
                berry = random.choice(trees)
                picked[berry] = picked.get(berry, 0) + 1
            for berry, n in picked.items():
                story.inventory[berry] = story.inventory.get(berry, 0) + n
            lines = ["You checked the berry trees..."] + season_lines + [
                f"You picked {n} {berry_name(b)}{'s' if n > 1 else ''}!" for b, n in picked.items()]
            lines.append("They went into your BERRY POUCH.")
        self.show_dialogue(lines, callback=self.show_progression_menu)

    def _gift_pokemon(self, pid, lines):
        """Add a gift Pokemon to the party (or the PC when the party is full)."""
        story = self.game.story_manager
        pokemon = Pokemon(self.game.loader.fetch_specific(pid), self.game.assets, size_mult=2.5)
        pokemon.caught_region = story.get_current_region()
        if len(story.player_team) < 6:
            story.player_team.append(pokemon)
            lines.append(f"{pokemon.name} joined your team!")
        else:
            slot = next((i for i, p in enumerate(story.pc_pokemon) if p is None), None)
            if slot is None:
                story.pc_pokemon.append(pokemon)
            else:
                story.pc_pokemon[slot] = pokemon
            lines.append(f"{pokemon.name} was sent to the PC.")
        self.game.data.mark_seen(pokemon.id)
        self.game.data.add_pokemon(pokemon)

    def _give_item(self, item, lines, qty=1):
        inv = self.game.story_manager.inventory
        inv[item] = inv.get(item, 0) + qty
        lines.append(f"{self.game.player_name} received the {forms.item_label(item).upper()}!")

    def hoenn_event(self, event):
        """Omega Ruby / Alpha Sapphire story beats that happen on routes."""
        self.is_progression_paused = True
        self.hide_menu_buttons()
        story = self.game.story_manager
        flags = story.story_flags
        v = hoenn.info(story) or hoenn.VERSIONS["OMEGA_RUBY"]
        lines = []
        if event == "elders":
            lines += [f"Old man: {v['team']} took the {v['orb']}! Without it, {v['legend']} could run wild...",
                      f"Old woman: Please, take the {v['other_orb']}. Keep it safe from them.",
                      f"Someday the two orbs must be reunited."]
            self._give_item(v["other_orb_item"], lines)
            flags["got_mt_pyre_orb"] = True
        elif event == "awakening":
            lines += [f"{v['leader']} held up the {v['orb']}. It began to shine...",
                      f"{v['legend']} awoke and underwent Primal Reversion!",
                      f"Primal {v['legend']} burst out of the cavern and flew toward Sootopolis City!",
                      ("The sunlight is extremely harsh all over Hoenn..." if v["crisis_weather"] == "SUN"
                       else "A heavy rain is pouring down all over Hoenn..."),
                      f"Steven: The Cave of Origin! We have to stop {v['legend']}!"]
        elif event == "leader_orb":
            lines += [f"{v['leader']}: I was wrong. Primal {v['legend']}'s power was never ours to control.",
                      f"Take the {v['orb']}. You've earned it far more than I have."]
            self._give_item(v["orb_item"], lines)
            lines.append(f"Hold it while {v['legend']} is in your party and it will Primal Revert in battle!")
            flags["got_stolen_orb"] = True
        elif event == "southern_island":
            lines += ["Steven: There you are! Come with me to Southern Island.",
                      f"On Southern Island, {v['eon']} was waiting for you...",
                      f"{v['eon']} wants to come with you!"]
            self._gift_pokemon(v["eon_id"], lines)
            self._give_item(v["eon_stone"], lines)
            lines.append("Steven: And you'll need this to bring out its true power.")
            self._give_item("MEGA_BRACELET", lines)
            lines += ["Steven: With the Mega Bracelet, a Pokemon holding its Mega Stone can Mega Evolve!",
                      "It happens when that Pokemon enters battle, once per battle."]
            flags["got_mega_bracelet"] = True
        elif event == "starter_stone":
            stone = hoenn.starter_stone(self.game)
            lines += ["Steven: You and your partner have come so far together.",
                      "This Mega Stone belongs with your starter."]
            self._give_item(stone, lines)
            flags["got_starter_mega_stone"] = True
        elif event == "stone_shop":
            from src.states.systems import PokeMartState
            self.game.change_state(PokeMartState(self.game, self, stock=list(hoenn.HOENN_MEGA_STONES)))
            return
        self.show_dialogue(lines or ["..."], callback=self.show_progression_menu)

    def visit_weather_director(self):
        """After Rayquaza calms the skies, the Weather Institute hands over the Weather Dial."""
        self.is_progression_paused = True
        self.hide_menu_buttons()
        story = self.game.story_manager
        if not story.story_flags.get(seasons.DIAL_UNLOCK_FLAG):
            lines = ["DIRECTOR: The skies are still too wild to study.", "Come back once they have been calmed."]
        elif story.inventory.get(seasons.WEATHER_DIAL, 0) <= 0:
            story.inventory[seasons.WEATHER_DIAL] = 1
            for rock in seasons.ROCK_WEATHER:
                story.inventory[rock] = story.inventory.get(rock, 0) + 1
            story.story_flags["got_weather_dial"] = True
            lines = ["DIRECTOR: You calmed the super-ancient Pokemon and saved Hoenn's skies!",
                     "Our research has made this possible: the WEATHER DIAL.",
                     f"{self.game.player_name} received the WEATHER DIAL!",
                     "Set a weather rock in it on any outdoor route in a region with weather.",
                     "The rock is used up, and the weather you choose lasts until midnight.",
                     "Clearing the skies is free. Here's one of each rock to get you started!",
                     "Received a DAMP, HEAT, SMOOTH and ICY ROCK!",
                     "Nobody can change the seasons, though. Not even Groudon or Kyogre!"]
        else:
            lines = ["DIRECTOR: How is the WEATHER DIAL working out?",
                     "Weather rocks are sold in marts wherever that weather happens."]
        self.show_dialogue(lines, callback=self.show_progression_menu)

    def open_camp(self):
        from src.states.camp import CampState
        self.is_progression_paused = True
        self.hide_menu_buttons()
        self.game.change_state(CampState(self.game, self))

    def story_event(self, key):
        self.is_progression_paused = True
        self.hide_menu_buttons()
        _run_story_event(self, key, lambda c: self._check_route_condition(c, False),
                         lambda lines: self.show_dialogue(lines, callback=self.show_progression_menu))

    def _route_npc_text(self, key):
        self.is_progression_paused = True
        self.hide_menu_buttons()
        self.show_dialogue(_resolve_lines(self.game, key), callback=self.show_progression_menu)

    def visit_director_radio(self):
        self.is_progression_paused = True
        self.hide_menu_buttons()
        inv = self.game.story_manager.inventory
        if inv.get("SILVER_WING", 0) > 0:
            lines = self.game.assets.get_text("director_radio_already", default=["Thank you!"])
        else:
            lines = self.game.assets.get_text("director_radio_intro")
            inv["SILVER_WING"] = 1
            if self.game.assets.heal_sfx: self.game.assets.heal_sfx.play()
        path = os.path.join(self.game.assets.sprites_dir, "png", "director.png")
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            h = int(self.game.height * 0.6); w = int(img.get_width() * (h / img.get_height()))
            self.npc_sprite = pygame.transform.scale(img, (w, h))
        self.show_dialogue(lines, callback=self._end_npc_interaction_playstate)

    def visit_sage_li(self):
        self.is_progression_paused = True
        self.hide_menu_buttons()
        inv = self.game.story_manager.inventory
        # Pokedex keys are "243-normal", so compare species ids (str(pid) in keys never matched).
        caught_ids = {v.get("id") for v in self.game.data.data.get("pokedex", {}).values() if isinstance(v, dict)}
        has_trio = {243, 244, 245} <= caught_ids
        
        if inv.get("RAINBOW_WING", 0) > 0:
            lines = ["Sage Li: Seek the summit, chosen one."]
        elif has_trio:
            lines = self.game.assets.get_text("sage_li_intro")
            inv["RAINBOW_WING"] = 1
            if self.game.assets.heal_sfx: self.game.assets.heal_sfx.play()
        else:
            lines = self.game.assets.get_text("sage_li_fail")
            
        path = os.path.join(self.game.assets.sprites_dir, "png", "elder.png")
        if not os.path.exists(path): path = os.path.join(self.game.assets.sprites_dir, "png", "oldman.png")
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            h = int(self.game.height * 0.6); w = int(img.get_width() * (h / img.get_height()))
            self.npc_sprite = pygame.transform.scale(img, (w, h))
        self.show_dialogue(lines, callback=self._end_npc_interaction_playstate)

    def _end_npc_interaction_playstate(self):
        self.npc_sprite = None
        self.dialogue_box.visible = False
        self.show_progression_menu()

    def hide_menu_buttons(self):
        for btn in self.route_buttons:
            if btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)
        self.route_buttons.clear()

    def check_for_evolution(self, force_catch_evo=False):
        team = self.game.story_manager.player_team
        if self._scan_list_for_evolution(team, force_catch_evo, "party", target_form=None):
            return True

        if force_catch_evo:
            if self._scan_list_for_evolution(self.game.story_manager.pc_pokemon, force_catch_evo, "pc", target_form=None):
                return True

        return False

    def _scan_list_for_evolution(self, pokemon_list, force_catch_evo, context, target_form=None):
        """Helper to scan a specific list (party or pc) for evolution candidates."""
        for i, poke in enumerate(pokemon_list):
            if poke is None:
                continue
            if target_form and poke.form != target_form:
                continue
            if id(poke) in getattr(self.game, "evo_declined", ()):
                continue

            is_catch_evo = False
            if context != "party":
                continue  # only party Pokemon grow and evolve
            # Real evolution rules: level, friendship, time of day, moves, battle feats...
            next_entries = evolution.ready_evolutions(self.game, poke, pokemon_list)
            if not next_entries:
                continue

            if poke.id == 201:
                all_owned = self.game.story_manager.player_team + self.game.story_manager.pc_pokemon
                owned_forms = {p.form for p in all_owned if p and p.id == 201}
                if len(owned_forms) < 28:
                    continue

            if next_entries:
                next_entry = self.game.story_manager.pick_evolution_branch(next_entries)

                if "_" in next_entry:
                    base_name, form_part = next_entry.rsplit("_", 1)
                    next_form = form_part.lower()
                else:
                    base_name = next_entry
                    next_form = "normal"

                next_id = self.game.name_to_id.get(base_name.upper())

                if next_id is not None:
                    from src.states.systems import EvolutionState
                    evo_state = EvolutionState(
                        self.game, poke, next_id, i,
                        next_form=next_form, context=context,
                        return_state=getattr(self, "_evo_return", None) or self,
                        consume_catch_count=is_catch_evo
                        )
                    self.game.change_state(evo_state)
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

        self.rounds_completed += 1

        pool_name = self.area_data.get("tree_pool")
        if isinstance(pool_name, list):
            pool_name = random.choice(pool_name)

        tree_pool_pct = self.game.loader.area_data.get(pool_name, {})

        if not tree_pool_pct:
            tree_pool_pct = self.game.loader.area_data.get("KANTO_ROUTE_TREE_PERCENTAGES", {})

        if not tree_pool_pct:
            self.show_dialogue(["No Pokémon found in this tree."])
            self.show_progression_menu()
            return

        tree_pool_pct = seasons.adjust_pool(self.game, regional_forms.extend_pool(self.game, tree_pool_pct),
                                            self.game.story_manager.current_area_key)
        p_id_str = Utils.weighted_random_choice(tree_pool_pct)
        raw = self.game.loader.fetch_specific(int(p_id_str))
        pokemon = Pokemon(raw, self.game.assets, size_mult=3.125)
        levels.set_wild(self.game, pokemon, self.game.story_manager.current_area_key)

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

    def action_dive(self):
        self.is_progression_paused = False
        self.hide_menu_buttons()
        self.rounds_completed += 1

        dive_pool = self.game.loader.area_data.get("HOENN_UNDERWATER_POOL_PERCENTAGES", {})
        if not dive_pool:
            self.show_dialogue(["The water is too shallow to dive here."], callback=self.show_progression_menu)
            return

        dive_pool = seasons.adjust_pool(self.game, regional_forms.extend_pool(self.game, dive_pool),
                                        self.game.story_manager.current_area_key)
        p_id_str = Utils.weighted_random_choice(dive_pool)
        raw = self.game.loader.fetch_specific(int(p_id_str))
        pokemon = Pokemon(raw, self.game.assets, size_mult=3.125)
        levels.set_wild(self.game, pokemon, self.game.story_manager.current_area_key)

        from src.states.battle import WildBattleState
        battle_state = WildBattleState(
            self.game,
            pokemon,
            self.game.story_manager.current_area_key,
            background_image="battle_ocean1.png" # ARCHITECT: Use ocean bg as placeholder for underwater
        )
        battle_state.play_state_data = {
            "balls_left": self.balls_left,
            "current_streak": self.current_streak,
            "rounds_completed": self.rounds_completed,
            "pending_wild_encounters": 0,
            "initial_round_active": False
        }
        self.show_dialogue(["Diving deep into the blue..."], callback=lambda: self.game.change_state(battle_state))

    def action_fish(self):
        self.is_progression_paused = False
        self.hide_menu_buttons()

        self.rounds_completed += 1

        inv = self.game.story_manager.inventory
        prefix = "JOHTO_" if "JOHTO" in self.game.story_manager.current_area_key or "LAKE" in self.game.story_manager.current_area_key else ""

        rod = next((r for r in ("SUPER_ROD", "GOOD_ROD") if inv.get(r, 0) > 0), "OLD_ROD")
        pool_key = f"{prefix}{rod}_POOL_PERCENTAGES"

        fishing_pool_pct = self.game.loader.area_data.get(pool_key, {})
        if not fishing_pool_pct:
            fishing_pool_pct = self.game.loader.area_data.get(pool_key.replace("JOHTO_", ""), {})

        if not fishing_pool_pct:
            self.show_dialogue(["Not even a nibble..."])
            self.show_progression_menu()
            return

        fishing_pool_pct = seasons.adjust_pool(self.game, regional_forms.extend_pool(self.game, fishing_pool_pct),
                                               self.game.story_manager.current_area_key)
        p_id_str = Utils.weighted_random_choice(fishing_pool_pct)
        # Better rods reach bigger fish (Old Lv 5+, Good 10+, Super 15+), and nothing bites
        # below the level it evolves at.
        area_key = self.game.story_manager.current_area_key
        level = max(levels.wild_level(self.game, area_key), {"OLD_ROD": 5, "GOOD_ROD": 10, "SUPER_ROD": 15}[rod])
        pid = evolution.suited_to_level(self.game, int(p_id_str), level)
        raw = self.game.loader.fetch_specific(pid)
        pokemon = Pokemon(raw, self.game.assets, size_mult=3.125)
        levels.set_wild(self.game, pokemon, area_key)
        if not levels.is_legendary(pokemon.id):
            pokemon.level = level
            pokemon.current_hp = pokemon.get_max_hp()

        self.show_dialogue(["Oh! A bite!"], callback=None)

        bg_file = random.choice(["battle_ocean1.png", "battle_ocean2.png", "battle_ocean3.png"])

        from src.states.battle import WildBattleState
        battle_state = WildBattleState(
            self.game,
            pokemon,
            self.game.story_manager.current_area_key,
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

    def action_challenge_boss(self, boss_data=None):
        if self.game.story_manager.current_area_key == "JOHTO_ROUTE_36":
            if self.game.story_manager.inventory.get("SQUIRT_BOTTLE", 0) <= 0:
                self.hide_menu_buttons()
                msg = ["The strange tree is wiggling...", "It looks like it might respond to water.", "Maybe someone in Goldenrod City can help?"]
                self.show_dialogue(msg, callback=self.show_progression_menu)
                return

        boss_data = boss_data or self.area_data.get("area_boss", {})
        if boss_data and boss_data.get("versions"):
            # Version-exclusive bosses (Great Tusk / Iron Treads): each save gets one version.
            story = self.game.story_manager
            versions = boss_data["versions"]
            if story.story_flags.get("paldea_version") not in versions:
                story.story_flags["paldea_version"] = random.choice(sorted(versions))
            boss_data = dict(boss_data, versions=None, **versions[story.story_flags["paldea_version"]])
        if boss_data and boss_data.get("lines"):
            self.is_progression_paused = True
            self.hide_menu_buttons()
            self.show_dialogue(_resolve_lines(self.game, boss_data["lines"]),
                               callback=lambda b=dict(boss_data, lines=None): self.action_challenge_boss(b))
            return

        self.is_progression_paused = False
        self.hide_menu_buttons()

        self.rounds_completed += 1
        if not boss_data:
            self.show_progression_menu()
            return

        pid = boss_data.get("id")
        # A shiny boss (the Red Gyarados) loads its shiny front and back art straight from the loader.
        raw = self.game.loader.fetch_specific(pid, is_shiny=bool(boss_data.get("is_shiny", False)))

        if "name" in boss_data:
            raw["name"] = boss_data["name"]
            raw["display_name"] = boss_data["name"]

        pokemon = Pokemon(raw, self.game.assets, size_mult=2.0)
        # A Primal boss (Groudon/Kyogre in the Cave of Origin) reverts when the battle starts.
        pokemon.primal_ready = bool(boss_data.get("primal"))
        pokemon.level = int(boss_data.get("level") or levels.boss_level(
            self.game, self.game.story_manager.current_area_key, pokemon.id))
        pokemon.current_hp = pokemon.get_max_hp()

        bg_file = boss_data.get("background") if (boss_data.get("background") and self.game.assets.get_background(
            boss_data["background"], from_overworld=False)) else self._get_battle_background_for_area()

        flag_name = boss_data.get("victory_flag", f"{self.game.story_manager.current_area_key}_boss_defeated")

        self.boss_manager.victory_flag = flag_name

        from src.states.battle import WildBattleState
        battle_state = WildBattleState(
            self.game, pokemon, self.game.story_manager.current_area_key,
            background_image=bg_file,
            is_boss_battle=True
        )
        battle_state.victory_flag = flag_name
        # Titans and other story bosses that are beaten, not caught.
        battle_state.no_catch = bool(boss_data.get("no_catch"))
        battle_state.win_lines = _resolve_lines(self.game, boss_data["won"]) if boss_data.get("won") else []
        battle_state.boss_rewards = dict(boss_data.get("rewards") or {})
        battle_state.play_state_data = {
            "balls_left": self.balls_left,
            "current_streak": self.current_streak,
            "rounds_completed": self.rounds_completed,
            "pending_wild_encounters": 0,
            "initial_round_active": False
        }
        self.game.change_state(battle_state)

    # Raid star rank -> battle stage (1★ easy, 4-5★ fully powered).
    RAID_STAR_STAGE = {1: 1, 2: 2, 3: 2, 4: 3, 5: 3}

    def _roll_raid_star(self):
        """Star rank from the region's MAX_RAID star table, keyed by badges earned (champion counts as 9)."""
        story = self.game.story_manager
        region = story.get_current_region()
        cfg = self.game.loader.area_data.get("MAX_RAID", {})
        progress = len(story.badges.get(region, []))
        if story.story_flags.get(f"beat_{region.lower()}_champion"):
            progress = 9
        rows = [r for r in cfg.get("star_odds_by_badges", [[0, [100, 0, 0, 0, 0]]]) if r[0] <= progress]
        odds = rows[-1][1]
        return random.choices(range(1, 6), weights=odds)[0]

    def action_max_raid(self):
        """Max Raid Battle: a Dynamax (or rare Gigantamax) boss drawn from this den's star-rank table."""
        den = self.area_data.get("max_raid_den", {})
        star = self._roll_raid_star()
        while star > 1 and not den.get(str(star)):
            star -= 1
        table = den.get(str(star))
        if not table:
            self.show_progression_menu()
            return

        self.is_progression_paused = True
        self.hide_menu_buttons()
        self.rounds_completed += 1

        pick = random.choices(list(table), weights=list(table.values()))[0]
        gmax = pick.endswith("-gmax")
        pid = int(pick.split("-")[0])
        raw = self.game.loader.fetch_specific(pid, form="gmax" if gmax else "normal")
        base_name = raw.get("display_name") or raw["name"]
        raw["display_name"] = f"{'G-MAX' if gmax else 'DYNAMAX'} {base_name}"
        pokemon = Pokemon(raw, self.game.assets, size_mult=2.0)
        pokemon.raid_stage = self.RAID_STAR_STAGE[star]
        pokemon.raid_star = star
        pokemon.level = levels.RAID_LEVELS[star]
        pokemon.current_hp = pokemon.get_max_hp()
        pokemon.raid_base_name = base_name

        intro = [f"A {star}★ Max Raid Battle!",
                 f"{'A Gigantamax' if gmax else 'A Dynamax'} {base_name} burst out of the den!"]

        def start_battle():
            from src.states.battle import WildBattleState
            battle_state = WildBattleState(
                self.game, pokemon, self.game.story_manager.current_area_key,
                background_image=self._get_battle_background_for_area(),
                is_boss_battle=True
            )
            battle_state.play_state_data = {
                "balls_left": self.balls_left,
                "current_streak": self.current_streak,
                "rounds_completed": self.rounds_completed,
                "pending_wild_encounters": 0,
                "initial_round_active": False
            }
            self.game.change_state(battle_state)

        self.show_dialogue(intro, callback=start_battle)

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
        self.rounds_completed += 1

        self.pending_wild_encounters = 0
        self.trigger_trainer_battle()

    def action_battle_wild(self):
        self.is_progression_paused = False
        self.hide_menu_buttons()

        wild_pool_pct = self._get_wild_pool(self.area_data)
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

        self.rounds_completed += 1

        raw = self.game.loader.fetch_specific(chosen_id)
        pokemon = Pokemon(raw, self.game.assets, size_mult=3.125)
        levels.set_wild(self.game, pokemon, self.game.story_manager.current_area_key)

        bg_file = self._get_battle_background_for_area()

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
        pygame.event.clear()
        self.game.change_state(battle_state)

    def action_exit_route(self, target_area=None):
        self.wild_catches_on_route = 0
        if target_area:
            next_area_key = target_area
        else:
            next_area_key = self.game.story_manager.get_current_area_data().get("next_area")

        if not next_area_key:
            next_area_key = self.game.story_manager.current_area_key

        if next_area_key:
            self.game.change_state(AreaTransitionState(self.game, next_area_key))

    def check_answer(self, pos):
        for i, btn_rect in enumerate(self.answer_btn_rects):
            if i >= len(self.p_data) or self.p_data[i] is None:
                continue

            if btn_rect.width > 0 and btn_rect.collidepoint(pos):
                self.balls_left -= 1
                self.current_ball_img = random.choice(self.game.assets.ball_imgs)

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

                self.was_shiny_override = is_shiny_catch and not is_correct_answer

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

        if self.pause_timer == 0 and not self.ball_active and not self.catch_selection_active:
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
        # Friendship: every catch made with a Pokemon in the party brings it closer to you.
        for member in self.game.story_manager.player_team:
            if member and member is not pokemon_caught:
                member.friendship += 1
                member.counters["catches"] = member.counters.get("catches", 0) + 1

        pokemon_caught.caught_region = self.game.story_manager.get_current_region()
        all_owned = self.game.story_manager.player_team + [p for p in self.game.story_manager.pc_pokemon if p]
        is_duplicate_owned = any(p.id == pokemon_caught.id and p.form == pokemon_caught.form for p in all_owned)
        is_party_full = len(self.game.story_manager.player_team) >= 6

        msgs = []

        if pokemon_caught.id == 201:
            is_duplicate_owned = False

        if is_duplicate_owned:
            upgraded = False
            if pokemon_caught.is_shiny:
                for i, p in enumerate(self.game.story_manager.player_team):
                    if p and p.id == pokemon_caught.id and p.form == pokemon_caught.form and not p.is_shiny:
                        self.game.story_manager.player_team[i] = pokemon_caught
                        upgraded = True
                        break

                if not upgraded:
                    for i, p in enumerate(self.game.story_manager.pc_pokemon):
                        if p and p.id == pokemon_caught.id and p.form == pokemon_caught.form and not p.is_shiny:
                            self.game.story_manager.pc_pokemon[i] = pokemon_caught
                            upgraded = True
                            break

            if upgraded:
                msgs.append(f"Shiny Upgrade! {pokemon_caught.display_name.upper()} is now Shiny!")
                pokemon_was_kept = True
            else:
                msgs.append("Gained evolution XP!")
                pokemon_was_kept = False
        else:
            pokemon_was_kept = True
            if not is_party_full:
                self.game.story_manager.player_team.append(pokemon_caught)
                if self.was_shiny_override:
                    msgs.append(self.game.assets.get_text("shiny_pass"))
                else:
                    msgs.append(self.game.assets.get_text("caught_pokemon", name=pokemon_caught.display_name.upper()))
            else:
                pc = self.game.story_manager.pc_pokemon
                for i in range(len(pc)):
                    if pc[i] is None:
                        pc[i] = pokemon_caught
                        break

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

        unique_count = len({v['id'] for v in self.game.data.data.get("pokedex", {}).values() if isinstance(v, dict) and 'id' in v})
        if pokemon_was_kept and unique_count > 0 and unique_count % 30 == 0:
            self.game.story_manager.money += 50000
            msgs.append(f"Milestone: {unique_count} species caught!")
            msgs.append("You received a $50,000 bonus!")

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

    def draw(self):
        screen = self.game.screen
        width, height = self.game.width, self.game.height
        offset_x, offset_y = 0, 0
        if self.scr_shake_timer > 0:
            offset_x, offset_y = random.randint(-15, 15), random.randint(-15, 15)

        caught_ids = {v['id'] for v in self.game.data.data.get("pokedex", {}).values()}

        if self.boss_manager.draw(screen, width, height, offset_x, offset_y):
            return

        if not self.boss_manager.in_boss_mode:
            screen.fill(BLACK)

            if self.dialogue_box.visible and hasattr(self, "npc_sprite") and self.npc_sprite:
                rect = self.npc_sprite.get_rect(center=(width // 2, height // 2 - 50))
                screen.blit(self.npc_sprite, rect)

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

        self._draw_season_hud(screen, 20 + offset_x, 58 + offset_y)

        pool_name = self.area_data.get("wild_pool_percentages")
        if pool_name:
            wild_pool = self.game.loader.area_data.get(pool_name, {})
            if wild_pool:
                all_caught = True
                for pid_str in wild_pool.keys():
                    pid = int(pid_str)
                    if pid >= 2000:
                        continue
                    if pid not in caught_ids:
                        all_caught = False
                        break

                if all_caught:
                    Utils.draw_text_outline(
                        screen,
                        "Area Complete!",
                        self.game.assets.fonts["small"],
                        GOLD,
                        width // 2 + offset_x,
                        25 + offset_y,
                        align="center"
                    )
                    Utils.draw_star(screen, GOLD, (width // 2 + 160 + offset_x, 25 + offset_y), 12)

        self.game.ui_manager.draw(screen)
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
                hover_y = (
                    math.sin(pygame.time.get_ticks() * p_info.bob_speed + p_info.bob_offset)
                    * p_info.bob_amount
                )

                is_target = (i == self.selected_catch_idx)
                is_other = (self.selected_catch_idx != -1 and i != self.selected_catch_idx)

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
                    draw_img = p_info.image.copy()
                    if is_other and not self.ball_active:
                        draw_img.set_alpha(100)

                    screen.blit(draw_img, draw_img.get_rect(center=(dx, dy)))

                    if is_target and not self.ball_active and self.pause_timer == 0:
                        pygame.draw.circle(screen, GOLD, (dx, dy + 100), 10 + math.sin(pygame.time.get_ticks()*0.1)*5, 3)

                    if self.caught_idx == -1 and not self.boss_manager.in_boss_mode:
                        if p_info.id in caught_ids:
                            r = p_info.image.get_rect(center=(dx, dy))
                            screen.blit(self.caught_indicator, (r.right - 60, r.top))

            if self.pause_timer == 0 and not self.is_progression_paused and not self.dialogue_box.visible and not self.catch_selection_active:
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

        if self.pause_timer == 0 and not self.is_progression_paused and not self.catch_selection_active:
            Utils.draw_text_outline(
                screen,
                self.problem_str,
                self.game.assets.fonts["big"],
                GOLD,
                width // 2,
                height * 0.15,
            )
            from src.core import speech
            if speech.available():
                tw = self.game.assets.fonts["big"].size(self.problem_str)[0]
                self.speak_rect = pygame.Rect(width // 2 + tw // 2 + 24, int(height * 0.15) - 26, 52, 52)
                speech.draw_speaker(screen, self.speak_rect)

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
            Utils.draw_multiline_text(
                screen,
                msg,
                self.game.assets.fonts["med"],
                WHITE,
                width // 2,
                height * 0.3,
                max_width=width - 100
            )
            Utils.draw_multiline_text(
                screen,
                self.game.assets.get_text("whats_next"),
                self.game.assets.fonts["s_med"],
                WHITE,
                width // 2,
                height * 0.4,
                max_width=width - 100
            )


# [REF-0036: City Hub State]
class CityState(GameState):
    def __init__(self, game):
        super().__init__(game)
        if hasattr(game.story_manager, "sync_rival"):
            game.story_manager.sync_rival()  # this region's rival (one per region per save)
        hoenn.apply_version(game)
        self.area_key = self.game.story_manager.current_area_key
        self.area_data = self.game.story_manager.get_current_area_data()

        self.game.story_manager.sync_badges()

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
        self.choice_active = False
        self.npc_slide_offset = 0
        self.is_npc_exiting = False
        self.npc_exit_callback = None

        btn_x, btn_y = 20, 80
        btn_w, btn_h = 120, 40
        spacing = 10

        self.hud_buttons = [
            Button((btn_x, btn_y, btn_w, btn_h), "PC", game.assets.fonts["tiny"], lambda: self._open_pc(), bg_color=GREEN),
            Button((btn_x, btn_y + (btn_h+spacing), btn_w, btn_h), "BAG", game.assets.fonts["tiny"], lambda: self._open_bag(), bg_color=BLUE),
            Button((btn_x, btn_y + (btn_h+spacing)*2, btn_w, btn_h), "BADGES", game.assets.fonts["tiny"], lambda: self._open_badges(), bg_color=GOLD),
            Button((btn_x, btn_y + (btn_h+spacing)*3, btn_w, btn_h), "SAVE", game.assets.fonts["tiny"], self.save_game, bg_color=GREEN),
            Button((btn_x, btn_y + (btn_h+spacing)*4, btn_w, btn_h), "LOAD", game.assets.fonts["tiny"], lambda: self._open_load(), bg_color=RED),
            Button((btn_x, btn_y + (btn_h+spacing)*5, btn_w, btn_h), "JOURNAL",
                   game.assets.fonts["tiny"],
                   self._open_journal,
                   bg_color=PURPLE),
        ]

        if (self.game.story_manager.inventory.get("AIR_BALLOON", 0) > 0
                or self.game.story_manager.inventory.get("HM_FLY", 0) > 0):
            self.hud_buttons.append(Button((btn_x, btn_y + (btn_h+spacing)*6, btn_w, btn_h), "FLY",
                                           game.assets.fonts["tiny"],
                                           self._open_fly,
                                           bg_color=BLUE))

        if self.game.story_manager.inventory.get("TOWN_MAP", 0) > 0:
            map_idx = len(self.hud_buttons)
            self.hud_buttons.append(Button((btn_x, btn_y + (btn_h+spacing)*map_idx, btn_w, btn_h), "MAP",
                                           game.assets.fonts["tiny"],
                                           self._open_map,
                                           bg_color=GOLD))

        opt_idx = len(self.hud_buttons)
        self.hud_buttons.append(Button((btn_x, btn_y + (btn_h+spacing)*opt_idx, btn_w, btn_h), "OPTIONS",
                                       game.assets.fonts["tiny"],
                                       self._open_options,
                                       bg_color=GRAY))

        _collapse_hud(self)

        self.yes_btn = Button((0, 0, 0, 0), "YES", game.assets.fonts["small"], None, bg_color=GREEN, visible=False, autosize=False)
        self.no_btn = Button((0, 0, 0, 0), "NO", game.assets.fonts["small"], None, bg_color=RED, visible=False, autosize=False)

        for btn in self.hud_buttons:
            self.game.ui_manager.add_element(btn)

        self.game.ui_manager.add_element(self.yes_btn)
        self.game.ui_manager.add_element(self.no_btn)

    def _open_options(self):
        from src.states.menus import open_difficulty_options
        open_difficulty_options(self.game, self)

    def _open_journal(self):
        from src.states.systems import JournalState
        self.game.change_state(JournalState(self.game, self))

    def _open_map(self):
        from src.states.systems import MapState
        self.game.change_state(MapState(self.game, self))

    def _open_fly(self):
        from src.states.systems import FlyState
        self.game.change_state(FlyState(self.game, self))

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
        bg_config = self.area_data.get("backgrounds", {}).get("main")
        if bg_config:
            img = self.game.assets.get_background(bg_config)
            if img:
                return img

        # ARCHITECT: Standardized naming logic: use the full area key name (e.g. azalea_town.png)
        bg_name = f"{self.area_key.lower()}.png"

        img = self.game.assets.get_background(bg_name)
        if img is None and self.area_data.get("area_type") == "town":
            img = self.game.assets.get_generic_background("town")
        return img

    def start_gym_battle(self):
        gym_data = self.area_data.get("gym")
        if not gym_data:
            self.show_message("The Gym is locked.")
            return

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

        reqs = gym_data.get("requirements", {})
        if reqs:
            needed_badges = reqs.get("badges", 0)
            story = self.game.story_manager
            if len(story.badges.get(story.get_current_region(), [])) < needed_badges:
                fail_text = reqs.get("fail_text", "The Gym is closed.")
                self.show_message(fail_text)
                return

            missing = [b for b in reqs.get("badge_names", []) if not self.game.story_manager.has_badge(b)]
            if missing:
                self.show_message(reqs.get("fail_text", "The Gym is closed."))
                return

            req_flag = reqs.get("flag")
            if req_flag and not self.game.story_manager.story_flags.get(req_flag, False):
                fail_text = reqs.get("fail_text", "The Gym is closed.")
                self.show_message(fail_text)
                return
            # Several story steps ("flags"), or every trainer in an area beaten ("defeated_area").
            missing_flags = [f for f in reqs.get("flags", []) if not story.story_flags.get(f, False)]
            area_left = reqs.get("defeated_area") and not story.check_requirements(
                {"defeated_area": reqs["defeated_area"]})
            if missing_flags or area_left:
                self.show_message(reqs.get("fail_text", "The Gym is closed."))
                return

        self.game.change_state(GymLobbyState(self.game, self))

    def _initiate_gym_battle(self, trainer_data, victory_flag=None, trainer_index=None):
        from src.states.battle import TrainerBattleState, TrainerIntroState
        team_ids = trainer_data.get("team", [])
        opponent_team = []
        for pid in team_ids:
            raw = self.game.loader.fetch_specific(pid)
            opponent_team.append(Pokemon(raw, self.game.assets, size_mult=3.125))
        forms.mark_trainer_team(opponent_team, trainer_data)
        region = self.game.story_manager.get_current_region()
        role = levels.gym_role(trainer_data.get("class"), bool(trainer_data.get("badge_reward")))
        if victory_flag and not trainer_data.get("badge_reward"):
            # A story fight at the Gym door (Viridian's Team Rocket): area levels, not the
            # 8th Gym's, since it can happen on day one.
            levels.set_team(opponent_team, levels.trainer_team_levels(
                self.game, self.area_key, len(opponent_team), boss=True))
        else:
            levels.set_team(opponent_team, levels.gym_team_levels(region, self.area_key, len(opponent_team), role))

        sprite_name = trainer_data.get("sprite")
        trainer_sprite = self.game.assets.get_trainer_image(sprite_name)

        bg_file = self.game.story_manager.get_gym_battle_background(self.area_key)

        battle_state = TrainerBattleState(
            self.game,
            opponent_team,
            trainer_sprite=trainer_sprite,
            trainer_class=trainer_data.get("class", "TRAINER"),
            trainer_name=trainer_data.get("name"),
            custom_dialogue=trainer_data.get("dialogue", {}),
            rewards=trainer_data.get("rewards"),
            battle_type="gym_event",
            is_boss_battle=trainer_data.get("is_boss_battle", True),
            area_name=self.area_key,
            victory_flag=victory_flag or trainer_data.get("victory_flag"),
            trainer_index=trainer_index,
            badge_reward=trainer_data.get("badge_reward"),
            background_image=bg_file
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
                btn = Button(rect, _fill_names(self.game, opt_data['text']),
                             self.game.assets.fonts["tiny"], callback, autosize=False)
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
            return bool(story.story_flags.get("KANTO_ROUTE_11_boss_defeated") or story.story_flags.get("caught_snorlax"))

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
        action = opt_data.get("action")
        if action == "HEAL":
            return lambda: self.game.change_state(PokeCenterState
                                                  (self.game, self))
        if action == "SHOP":
            return self._open_shop
        if action == "GAMECORNER":
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
        if action == "AMIE":
            from src.states.amie import AmieState
            return lambda: (self.clear_hover_menu(), self.game.change_state(AmieState(self.game, self)))
        if action == "ROCKET_GAUNTLET":
            return self.start_rocket_gauntlet
        if action == "RUINS":
            return self.action_explore_ruins
        if action == "TRAVEL":
            return lambda: self.go_to_area(opt_data.get("target_area"), opt_data.get("message"))
        return None

    def visit_contest_hall(self):
        from src.states.contest import ContestHallState
        self.game.change_state(ContestHallState(self.game, self))

    def visit_poffin_house(self):
        from src.states.poffin import PoffinHouseState
        self.game.change_state(PoffinHouseState(self.game, self))

    def visit_berry_shop(self):
        """Floaroma's flower shop: a Berry Pouch on the first visit, then berries for sale."""
        from src.pokemon.poffin import BASIC_BERRIES, BERRIES
        from src.states.systems import PokeMartState
        story = self.game.story_manager
        stock = BASIC_BERRIES + ([b for b in BERRIES if len(BERRIES[b]) == 2 and max(BERRIES[b].values()) == 10]
                                 if len(story.badges.get("SINNOH", [])) >= 3 else [])

        def open_stand():
            self.end_npc_interaction()
            self.game.change_state(PokeMartState(self.game, self, stock=stock))

        if story.story_flags.get("has_berry_pouch"):
            open_stand()
            return
        story.story_flags["has_berry_pouch"] = True
        story.inventory["BERRY_POUCH"] = 1
        for b in BASIC_BERRIES:
            story.inventory[b] = story.inventory.get(b, 0) + 3
        self.show_message(["Welcome to Pick a Peck of Colors!",
                           "Berries grow on trees along Sinnoh's routes. Pick them once a day!",
                           "Cook them into Poffins at the Poffin House in Hearthome City.",
                           "Here's a BERRY POUCH, with a few berries to get you started!",
                           "You received the BERRY POUCH!"], callback=open_stand)
        self.npc_sprite = self.game.assets.get_trainer_image("beauty.png")
        self.npc_slide_offset = 400

    def visit_contest_museum(self):
        from src.states.contest import museum_lines
        self.show_message(museum_lines(self.game.story_manager), callback=self.end_npc_interaction)
        self.npc_sprite = self.game.assets.get_trainer_image("gentleman.png")
        self.npc_slide_offset = 400

    def _open_shop(self):
        from src.states.systems import PokeMartState
        self.game.change_state(PokeMartState(self.game, self))

    def _npc_text_key(self, key):
        """GAME_TEXT key for a data-driven NPC (as given, or region-prefixed)."""
        if not key:
            return None
        text = self.game.assets.game_text
        if key in text:
            return key
        prefixed = f"{self.game.story_manager.get_current_region().lower()}_{key}"
        return prefixed if prefixed in text else None

    def story_event(self, key):
        _run_story_event(self, key, self._check_menu_condition, self.show_message)

    def show_npc_text(self, key, opt_data=None):
        """Generic talk-to-NPC: show a GAME_TEXT entry, then set the option's flag if it has one."""
        flag = (opt_data or {}).get("victory_flag")

        def finish():
            if flag:
                self.game.story_manager.story_flags[flag] = True
            self.end_npc_interaction()

        self.show_message(_resolve_lines(self.game, key), callback=finish)
        sprite = (opt_data or {}).get("sprite")
        if sprite:
            self.npc_sprite = self.game.assets.get_trainer_image(sprite)
            self.npc_slide_offset = 400

    def visit_mr_fuji(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "mr_fuji"
        self.npc_slide_offset = 400
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("mr_fuji.png")
        if not self.npc_sprite:
            self.npc_sprite = self.game.assets.get_trainer_image("oldman.png")

        msgs = []
        if self.game.story_manager.story_flags.get("tower_ghost_defeated"):
            if self.game.story_manager.inventory.get("POKE_FLUTE", 0) > 0:
                msgs.append(self.game.assets.get_text("fuji_already_helped", default="Thank you again for your help at the tower."))
            else:
                msgs += [
                    "Mr. Fuji: Thank you! With the ghost at peace, Team Rocket has fled the Pokémon Tower.",
                    "The ghost you calmed was the spirit of a Marowak.",
                    "Team Rocket took her life while she was protecting her child, Cubone.",
                    "Thanks to you, her spirit has finally found peace.",
                    "I care for the orphaned Pokémon here, and they're all safe now.",
                    self.game.assets.get_text("fuji_reward", default="Please, take this as a token of my gratitude."),
                    self.game.assets.get_text("received_flute", default="You received the POKé FLUTE!"),
                    "Mr. Fuji: Its soft melody wakes up even the deepest-sleeping Pokémon.",
                    "A Snorlax is said to be dozing on the road east of Vermilion...",
                ]
                self.game.story_manager.inventory["POKE_FLUTE"] = 1
                self.game.story_manager.story_flags["met_mr_fuji"] = True
        else:
            msgs.append(self.game.assets.get_text("fuji_sadness", default="A terrible sadness hangs over the Pokémon Tower..."))

        self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msgs, self.game.assets.fonts["med"], callback=self.end_npc_interaction)

    def visit_alph_scientist(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "alph_scientist"
        self.npc_slide_offset = 400
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("scientist.png")

        bg_name = self.area_data.get("backgrounds", {}).get("lab", "ruins_lab.png")
        bg_img = self.game.assets.get_background(bg_name) or self.game.assets.get_generic_background("lab")
        if bg_img:
            box_top = Utils.get_full_dialogue_rect(self.game).top
            self.npc_bg = pygame.transform.scale(bg_img, (self.game.width, box_top))

        catch_counts = self.game.story_manager.catch_counts
        forms = ["normal", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "question", "exclamation"]
        caught_count = 0
        for f in forms:
            f_key = "a" if f == "normal" else f
            key = f"201_{f_key}"
            if catch_counts.get(key, 0) > 0:
                caught_count += 1

        remaining = 28 - caught_count

        nown_id = self.game.loader.get_special_id("NOWN", 3025)

        callback = self.end_npc_interaction
        if caught_count == 0:
            msg = ["Researcher: Welcome to the Ruins Research Lab!", "These ruins are filled with a mysterious Pokemon called UNOWN.", "They appear in 28 different forms! We are trying to document them all.", "Could you help us? Explore the ruins and catch as many forms as you can!"]
        elif self.game.story_manager.inventory.get("UNOWN_REPORT", 0) == 0:
            msg = ["Researcher: You've started a collection! That's excellent!", "Here, take this UNOWN REPORT.", "It will help you track every form you find.", "Come back when you've documented more!"]
            self.game.story_manager.inventory["UNOWN_REPORT"] = 1
        elif remaining == 0:
            if any(isinstance(v, dict) and v.get("id") == nown_id
                   for v in self.game.data.data.get("pokedex", {}).values()):  # keys are "id-form"
                msg = ["Researcher: Incredible! You've documented all 28 forms of UNOWN!", "Your math skills and dedication are truly legendary.", "You've solved the greatest mystery of the Johto region!"]
            else:
                msg = ["Researcher: Incredible! You've documented all 28 forms of UNOWN!",
                       "The air in the ruins is vibrating...",
                       "One of your UNOWN is responding to the completed report!",
                       "It's happening!"]

                target_data = self._find_unown_for_evolution()
                if target_data:
                    def trigger_secret_evo():
                        from src.states.systems import EvolutionState
                        self.game.change_state(EvolutionState(
                            self.game, target_data['pkmn'], nown_id, target_data['idx'],
                            context=target_data['context'], return_state=self
                        ))
                    callback = trigger_secret_evo
                else:
                    msg.append("Wait... you don't have an UNOWN with you right now?")
                    msg.append("Come back with one in your party or PC so I can show you something amazing!")
        else:
            msg = [f"Researcher: Let's see your progress...", f"You have documented {caught_count} UNOWN forms so far.", f"That means there are {remaining} forms still waiting to be discovered!", "Keep up the good work! The secret of the ruins is close."]

        self.npc_dialogue = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(self.game),
            msg,
            self.game.assets.fonts["med"],
            callback=callback
        )

    def _find_unown_for_evolution(self):
        """Helper to find an Unown (ID 201) in the party or PC for the secret evolution."""
        for i, p in enumerate(self.game.story_manager.player_team):
            if p.id == 201:
                return {'pkmn': p, 'idx': i, 'context': 'party'}
        for i, p in enumerate(self.game.story_manager.pc_pokemon):
            if p.id == 201:
                return {'pkmn': p, 'idx': i, 'context': 'pc'}
        return None

    def action_explore_ruins(self):
        self.clear_hover_menu()
        from src.states.overworld import PlayState
        ruins_state = PlayState(self.game)
        self.game.change_state(ruins_state)
        ruins_state.action_search_pokemon()

    def visit_silph_employee(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "silph_employee"
        self.npc_slide_offset = 400
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("supernerd.png")

        story = self.game.story_manager
        if (story.story_flags.get("silph_co_cleared") and "JOHTO" in story.visited_regions()
                and not story.story_flags.get("got_upgrade")):
            # HeartGold/SoulSilver: a Silph Co. employee hands over the Up-Grade.
            story.story_flags["got_upgrade"] = True
            story.inventory["UPGRADE"] = story.inventory.get("UPGRADE", 0) + 1
            msg = ["You've been to Johto? Then you'll appreciate this!",
                   "It's the UP-GRADE, a Silph Co. invention. Use it on a Porygon to make it even better!",
                   f"{self.game.player_name} received the UP-GRADE!"]
        elif story.story_flags.get("silph_co_cleared"):
            msg = ["You saved us!", "Team Rocket is gone, but I fear they already have what they need for their 'Ultimate' project."]
        else:
            msg = [
                "They're everywhere... the black suits... the red 'R'...",
                "Please, if you're a trainer, stop them before they take the prototype!",
                "They're on the upper floors... it's coming for us all..."
            ]

        self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msg, self.game.assets.fonts["med"], callback=self.end_npc_interaction)

    def visit_silph_president(self):
        story = self.game.story_manager
        if story.story_flags.get("received_silph_reward"):
            self.show_message(["President: Silph Co. is back in business, thanks to you!",
                               "Take good care of that Porygon. It was our proudest invention."])
            return

        raw = self.game.loader.fetch_specific(137)
        porygon = Pokemon(raw, self.game.assets, size_mult=2.5)
        msgs = ["President: You saved Silph Co. from Team Rocket!",
                "Team Rocket wanted our newest inventions. Instead, I want YOU to have them.",
                "Please take our MASTER BALL. It catches any Pokémon without fail!",
                "And this is PORYGON, the world's first digital Pokémon, built right here at Silph!"]
        if len(story.player_team) < 6:
            story.player_team.append(porygon)
            msgs.append("PORYGON joined your team!")
        else:
            slot = next((i for i, p in enumerate(story.pc_pokemon) if p is None), None)
            if slot is None:
                story.pc_pokemon.append(porygon)
            else:
                story.pc_pokemon[slot] = porygon
            msgs.append("PORYGON was sent to BILL'S PC!")
        self.game.data.add_pokemon(porygon)
        story.inventory["MASTER_BALL"] = story.inventory.get("MASTER_BALL", 0) + 1
        msgs.append("You received the MASTER BALL!")
        story.story_flags["received_silph_reward"] = True
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.play()
        self.show_message(msgs)
        self.npc_sprite = self.game.assets.get_trainer_image("gentleman.png")
        self.npc_slide_offset = 400

    def start_rocket_gauntlet(self):
        self.clear_hover_menu()
        area_key = self.game.story_manager.current_area_key
        trainer_pool = self.area_data.get("trainer_pool", [])

        idx = -1
        for i in range(len(trainer_pool)):
            if not self.game.story_manager.is_trainer_defeated(area_key, i):
                idx = i
                break

        if idx == -1:
            self.game.story_manager.story_flags["silph_co_cleared"] = True
            self.show_message("There are no more Team Rocket members here! Silph Co. is safe.")
            return

        t_data = trainer_pool[idx]
        self._initiate_gym_battle(t_data, trainer_index=idx)

    def open_explore_menu(self):
        options = self.area_data.get("explore_options", [])
        self._create_hover_menu(options, self.action_menu.buttons[0].rect)

    def open_travel_menu(self):
        options = self.area_data.get("travel_options", [])
        for opt in options:
            opt['action'] = 'TRAVEL'
        if len(self.action_menu.buttons) > 3:
            self._create_hover_menu(options, self.action_menu.buttons[3].rect)

    def visit_rival_mom(self):
        self.visit_mom(is_neighbor=True)

    def visit_silver_mom(self):
        self.visit_mom(is_neighbor=True, is_silver_mom=True)

    def visit_mom(self, is_neighbor=False, is_silver_mom=False):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "silver_mom" if is_silver_mom else "mom"
        self.npc_slide_offset = 400
        self.action_menu.set_visibility(False)
        story = self.game.story_manager
        start_reg = getattr(story, "starting_region", "KANTO")

        is_home = ((start_reg == "KANTO" and self.area_key == "PALLET_TOWN") or
                   (start_reg == "JOHTO" and self.area_key == "NEW_BARK_TOWN")) and not is_neighbor

        is_reds_mom = (start_reg == "JOHTO" and self.area_key == "PALLET_TOWN" and not is_neighbor)

        # Hoenn onward: Mom owns a home in every region's starting town.
        home_region = next((r for r, cfg in story.get_region_starts()
                            if cfg.get("start_area") == self.area_key and r not in ("KANTO", "JOHTO")
                            and not cfg.get("travel_only")), None)
        if home_region and not is_neighbor:
            is_home = True

        should_heal = is_home or is_reds_mom

        bgs = self.area_data.get("backgrounds", {})
        bg_name = bgs.get("mom") or bgs.get("mom_home")
        if not bg_name:
            bg_name = "pallet_city_mom.png" if "PALLET" in self.area_key else "new_city_mom.png"

        bg_img = self.game.assets.get_background(bg_name) or self.game.assets.get_generic_background("house")
        if bg_img:
            box_top = Utils.get_full_dialogue_rect(self.game).top
            self.npc_bg = pygame.transform.scale(bg_img, (self.game.width, box_top))

        if is_silver_mom:
            sprite_file = "silver_mom.png"
        elif "NEW_BARK" in self.area_key:
            sprite_file = "new_bark_mom.png"
        else:
            sprite_file = "mom.png"

        path = os.path.join(self.game.assets.sprites_dir, "png", sprite_file)
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            h = int(self.game.height * 0.6)
            w = int(img.get_width() * (h / img.get_height()))
            self.npc_sprite = pygame.transform.scale(img, (w, h))
        else:
            self.npc_sprite = self.game.assets.get_trainer_image(sprite_file)

        if should_heal:
            for p in self.game.story_manager.player_team:
                p.heal_full()
            if self.game.assets.heal_sfx:
                self.game.assets.heal_sfx.play()

            if is_reds_mom:
                dialogue = self.game.assets.get_text("red_mom_johto_visitor", default=["Oh! A visitor from Johto?", "Red is out on Mt. Silver right now.", "He's become such a strong trainer!"])
            elif home_region:
                cfg = story.get_region_start(home_region)
                fresh = start_reg == home_region and cfg.get("mom_newstart_text")
                pool = cfg.get("mom_newstart_text") if fresh else cfg.get("mom_home_text")
                dialogue = _resolve_lines(self.game, random.choice(pool or ["mom"]))
            else:
                dialogue = self.game.assets.get_text("johto_mom_home", default=self.game.assets.get_text("mom"))
        elif is_silver_mom:
            dialogue = self.game.assets.get_text("johto_mom_neighbor", default=["Hello! I'm Silver's Mom.", "Silver is out traveling right now."])
        else:
            r_name = getattr(self.game, "rival_name", "SILVER")
            dialogue = self.game.assets.get_text("johto_mom_neighbor", default=[f"I'm {r_name}'s Mom.", "He's always out training!"])

        self.npc_dialogue = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(self.game),
            _resolve_lines(self.game, dialogue),
            self.game.assets.fonts["med"],
            callback=self.end_npc_interaction
        )
        region = story.get_current_region()
        if should_heal and story.is_region_champion(region):
            self.npc_dialogue.callback = lambda: self._offer_move(region, phone=False)

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

        story = self.game.story_manager
        region = getattr(story, "starting_region", "KANTO")

        if story.kanto_caught_count() >= 150 and not story.story_flags.get("mew_spotted_mt_moon"):
            msg = [
                "Professor Oak: Incredible! You've documented 150 species!",
                "You are truly a master researcher.",
                "I just heard from Celio on One Island, in the Sevii Islands...",
                "Sailors keep seeing a pink, floating Pokemon near an uncharted island.",
                "It could be the mythical Pokemon, MEW!",
                "Help Celio fix his Network Machine. He may know how to find that island."
            ]
            story.story_flags["mew_spotted_mt_moon"] = True
            self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msg, self.game.assets.fonts["med"], callback=self.end_npc_interaction)
            return

        if (region == "JOHTO" and story.is_region_champion("JOHTO")
                and not story.story_flags.get("oak_johto_champion_gift")):
            # Mirror of Elm's gift to Kanto Champions: Johto Champions get a Kanto partner from Oak.
            story.story_flags["oak_johto_champion_gift"] = True
            story.story_flags["unlocked_national_dex"] = True
            story.enter_region("KANTO")
            msg = [
                "Professor Oak: So you're the new Johto Champion! Elm told me all about you.",
                "You've proven yourself to be a true Math Master.",
                "Let me upgrade your Pokédex. It can now record every species from Kanto and Johto!",
                "And here is a Kanto Badge Case for your next challenge!",
                "You received the NATIONAL DEX and KANTO BADGE CASE!",
            ]
            if story.story_flags.get("received_starter_kanto"):
                msg.append("I see you already have a Kanto partner. Go show the Kanto Gyms what you can do!")
                callback = self.end_npc_interaction
            else:
                msg.append("To help you on this new journey... please, choose one of these Kanto Pokémon!")

                def kanto_starter_exit():
                    from src.states.menus import StarterSelectionState
                    self.start_npc_exit(lambda: self.game.change_state(
                        StarterSelectionState(self.game, starter_ids=[1, 4, 7], region="KANTO")))
                callback = kanto_starter_exit
        elif story.story_flags.get("beat_champion"):
            if region == "JOHTO" and not story.story_flags.get("unlocked_national_dex"):
                msg = [
                    "Professor Oak: Congratulations on your victory at the League!",
                    "You've proven yourself to be a true Math Master.",
                    "Since you're exploring Kanto now, let me upgrade your Pokedex.",
                    "It can now record data on all 251 species!",
                    "And here is a Kanto Badge Case for your next challenge!",
                    "You received the NATIONAL DEX and KANTO BADGE CASE!"
                ]
                story.story_flags["unlocked_national_dex"] = True
                story.story_flags["unlocked_kanto_badges"] = True
                callback = self.end_npc_interaction
            else:
                dest = "Johto" if region == "KANTO" else "Kanto"
                msg = ["Congratulations on your victory, Champion!", "Your math skills have reached legendary heights.", f"I have news: the path to the {dest} region is now open.", "Head to Route 26 via the Indigo Plateau to begin your next challenge!"]
                callback = self.end_npc_interaction
        elif not story.game_started and not story.player_team and region == "KANTO":
            msg = ["Hello there! You must be the trainer Elm mentioned.", "I have some Kanto Pokémon here looking for partners."]
            from src.states.menus import StarterSelectionState

            def start_kanto_starters():
                def change_to_starters():
                    self.game.change_state(StarterSelectionState(self.game, starter_ids=[1, 4, 7], region="KANTO"))
                self.start_npc_exit(change_to_starters)
            callback = start_kanto_starters
        elif region == "JOHTO" and not story.game_started:
            msg = ["Hello! You must be Professor Elm's new assistant.", "He's waiting for you in New Bark Town!"]
            callback = self.end_npc_interaction
        elif region == "JOHTO" and not story.story_flags.get("received_starter_kanto"):
            msg = ["Professor Oak: Ah, a trainer from Johto! Welcome to Pallet Town.",
                   "Become the Johto Champion, and I'll have a Kanto partner waiting for you."]
            callback = self.end_npc_interaction
        elif not story.story_flags.get("defeated_rival_kanto"):
            msg = [f"Wait, {self.game.player_name}!", f"{self.game.rival_name} is still waiting for a battle!"]

            def rival_exit_kanto():
                def trigger_battle(): self.retrigger_rival_battle("KANTO")
                self.start_npc_exit(trigger_battle)
            callback = rival_exit_kanto
        else:
            msg = _resolve_lines(self.game, "professor_oak")
            callback = self.end_npc_interaction

        self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msg, self.game.assets.fonts["med"], callback=callback)

    def visit_kurt(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "kurt"
        self.npc_slide_offset = 400
        self.action_menu.set_visibility(False)
        path = os.path.join(self.game.assets.sprites_dir, "png", "kurt.png")
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            h = int(self.game.height * 0.6)
            w = int(img.get_width() * (h / img.get_height()))
            self.npc_sprite = pygame.transform.scale(img, (w, h))
        else:
            path = os.path.join(self.game.assets.sprites_dir, "png", "kurt.png")
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            h = int(self.game.height * 0.6)
            w = int(img.get_width() * (h / img.get_height()))
            self.npc_sprite = pygame.transform.scale(img, (w, h))
        else:
            self.npc_sprite = self.game.assets.get_trainer_image("oldman.png")

        flags = self.game.story_manager.story_flags
        if flags.get("slowpoke_well_cleared"):
            msg = self.game.assets.get_text("kurt_reward")
            self.game.story_manager.balls_left += 5
        else:
            msg = self.game.assets.get_text("kurt_intro")
        self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msg, self.game.assets.fonts["med"], callback=self.end_npc_interaction)

    def visit_bill_johto(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "bill"
        self.npc_slide_offset = 400
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("bill.png")

        story = self.game.story_manager
        if (self.area_key == "GOLDENROD_CITY" and story.story_flags.get("met_bill_johto")
                and not story.story_flags.get("got_bill_eevee")):
            # HeartGold/SoulSilver: at home in Goldenrod, Bill gives you an Eevee.
            story.story_flags["got_bill_eevee"] = True
            msg = ["Bill: Hey, you made it to my place! I found this Eevee while I was in Ecruteak.",
                   "It needs a trainer who'll help it evolve. Here, it's yours!",
                   story_events.gift_pokemon(self.game, 133)]
        else:
            msg = self.game.assets.get_text("bill_johto_intro")
            story.story_flags["met_bill_johto"] = True
        self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msg, self.game.assets.fonts["med"], callback=self.end_npc_interaction)

    def visit_lance_johto(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "lance"
        self.npc_slide_offset = 400
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("lance.png")

        flags = self.game.story_manager.story_flags
        if flags.get("rocket_hq_cleared"):
            msg = self.game.assets.get_text("lance_mahogany_cleared")
        else:
            msg = self.game.assets.get_text("lance_mahogany_intro")
        self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msg, self.game.assets.fonts["med"], callback=self.end_npc_interaction)

    def visit_radio_tower_grunt(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "rocket_grunt"
        self.npc_slide_offset = 400
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("rocket_grunt_m.png")

        # ARCHITECT: Use regional badge check for Johto progression (7 badges required)
        badges = len(self.game.story_manager.badges.get("JOHTO", []))
        flags = self.game.story_manager.story_flags

        if badges < 7:
            msg = self.game.assets.get_text("radio_tower_grunt_deny")
            callback = self.end_npc_interaction
        elif not flags.get("radio_tower_cleared"):
            msg = self.game.assets.get_text("radio_tower_grunt_battle")

            # ARCHITECT: Instead of gauntlet (which fails in cities), trigger a gatekeeper battle.
            def trigger_entry_battle():
                from src.states.battle import TrainerBattleState, TrainerIntroState
                team_ids = [19, 20, 41] # Standard Rocket team: Rattata, Raticate, Zubat
                opponent_team = [Pokemon(self.game.loader.fetch_specific(tid), self.game.assets, size_mult=3.125) for tid in team_ids]
                
                # Create a specialized battle that moves the player into the tower on victory
                class RadioTowerGateBattle(TrainerBattleState):
                    def exit_battle(self):
                        from src.states.overworld import AreaTransitionState
                        self.game.change_state(AreaTransitionState(self.game, "RADIO_TOWER"))

                battle_state = RadioTowerGateBattle(
                    self.game, opponent_team, trainer_sprite=self.npc_sprite,
                    trainer_class="ROCKET", trainer_name="GRUNT", 
                    battle_type="indoor", area_name=self.area_key
                )
                self.game.change_state(TrainerIntroState(self.game, self.npc_sprite, msg, battle_state))
            
            callback = trigger_entry_battle
        else:
            # Safety fallback: Tower cleared but NPC still interacted with
            msg = ["The Radio Tower is safe now. Come on in!"]
            def enter_tower():
                from src.states.overworld import AreaTransitionState
                self.game.change_state(AreaTransitionState(self.game, "RADIO_TOWER"))
            callback = enter_tower

        self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msg, self.game.assets.fonts["med"], callback=callback)

    def visit_mr_pokemon(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "mr_pokemon"
        self.npc_slide_offset = 400
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("mr_pokemon.png")
        if not self.npc_sprite:
            self.npc_sprite = self.game.assets.get_trainer_image("oldman.png")

        flags = self.game.story_manager.story_flags
        if not flags.get("met_mr_pokemon"):
            msg = [
                "Mr. Pokémon: Hello! You must be the trainer Prof. Elm mentioned.",
                "I've made a remarkable discovery—this mysterious Pokémon Egg!",
                "It doesn't look like any Egg I've seen in the Kanto or Johto regions.",
                "Prof. Elm is the expert on Pokémon evolution and life cycles.",
                "Could you take this to him in New Bark Town?",
                "You received the MYSTERY EGG!",
                "It's safe in your BAG. Hurry back to the lab!"
            ]
            flags["met_mr_pokemon"] = True
            self.game.story_manager.inventory["MYSTERY_EGG"] = 1
            self.game.data.save()
        else:
            msg = [
                "Mr. Pokémon: That Egg is a fascinating mystery.",
                "Please show it to Professor Elm as soon as possible.",
                "I'll stay here and continue my research on Pokémon origins!"
            ]

        self.npc_dialogue = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(self.game),
            msg,
            self.game.assets.fonts["med"],
            callback=self.end_npc_interaction,
            visible=True
        )
        self.game.ui_manager.add_element(self.npc_dialogue)

    def visit_kimono_girls(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "kimono_girl"
        self.npc_slide_offset = 400
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("kimono_girl.png")
        if not self.npc_sprite: self.npc_sprite = self.game.assets.get_trainer_image("beauty.png")

        msg = self.game.assets.get_text("kimono_girls_intro")
        self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msg, self.game.assets.fonts["med"], callback=self.end_npc_interaction)

    def visit_flower_shop(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "flower_girl"
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("lass.png")

        if self.game.story_manager.has_badge("PLAIN"):
            if self.game.story_manager.inventory.get("SQUIRT_BOTTLE", 0) == 0:
                msg = self.game.assets.get_text("flower_shop_reward")
                self.game.story_manager.inventory["SQUIRT_BOTTLE"] = 1
            else:
                msg = ["The Squirt Bottle should help you clear the path on Route 36!"]
        else:
            msg = self.game.assets.get_text("flower_shop_intro")

        self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msg, self.game.assets.fonts["med"], callback=self.end_npc_interaction)

    def visit_lighthouse_jasmine(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.npc_slide_offset = 400
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("jasmine.png")

        inv = self.game.story_manager.inventory
        flags = self.game.story_manager.story_flags
        if flags.get("ampharos_cured"):
            msg = ["Jasmine: I will return to the Gym now.", "Thank you for the Secret Potion!"]
        elif inv.get("SECRET_POTION", 0) > 0:
            msg = self.game.assets.get_text("jasmine_lighthouse_medicine")
        else:
            msg = self.game.assets.get_text("jasmine_lighthouse_intro")
            if not flags.get("received_surf_jasmine"):
                inv["SURF_BOARD"] = 1
                flags["received_surf_jasmine"] = True

        self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msg, self.game.assets.fonts["med"], callback=self.end_npc_interaction)

    def visit_ampharos(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_pokemon_image(181, "normal", False)

        inv = self.game.story_manager.inventory
        flags = self.game.story_manager.story_flags
        if flags.get("ampharos_cured"):
            msg = ["Amphy: Palu! Palulu!"]
        elif inv.get("SECRET_POTION", 0) > 0:
            msg = self.game.assets.get_text("amphy_cured")
            inv["SECRET_POTION"] -= 1
            flags["ampharos_cured"] = True
        else:
            msg = self.game.assets.get_text("amphy_sick")
        self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msg, self.game.assets.fonts["med"], callback=self.end_npc_interaction)

    def visit_pharmacist(self):
        self.show_message(self.game.assets.get_text("pharmacist_reward"))
        self.game.story_manager.inventory["SECRET_POTION"] = 1

    def visit_euskine(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "eusine"
        self.npc_slide_offset = 400
        self.action_menu.set_visibility(False)

        # ARCHITECT: Attempt to load Eusine's specific sprite, fallback to generic supernerd
        self.npc_sprite = self.game.assets.get_trainer_image("eusine.png")
        if not self.npc_sprite:
            self.npc_sprite = self.game.assets.get_trainer_image("supernerd.png")

        # Check if Suicune was defeated (default boss victory flag for Burned Tower)
        if self.game.story_manager.story_flags.get("BURNED_TOWER_boss_defeated"):
            msg = self.game.assets.get_text("eusine_suicune_defeated")
        else:
            msg = self.game.assets.get_text("euskine_intro")

        self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msg, self.game.assets.fonts["med"], callback=self.end_npc_interaction)

    def visit_dragon_elder(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.npc_slide_offset = 400
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("oldman.png")

        if self.game.story_manager.has_badge("RISING"):
            msg = self.game.assets.get_text("dragon_elder_pass")
        else:
            msg = self.game.assets.get_text("dragon_elder_intro")
        self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msg, self.game.assets.fonts["med"], callback=self.end_npc_interaction)

    def visit_dojo(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "dojo"
        self.npc_slide_offset = 400
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("blackbelt.png")
        if not self.npc_sprite:
            self.npc_sprite = self.game.assets.get_trainer_image("hiker.png")

        story = self.game.story_manager
        flags = story.story_flags
        has_marsh = story.has_badge("MARSH")
        has_soul = story.has_badge("SOUL")

        msgs = ["Welcome to the Fighting Dojo!", "Only the strongest trainers may enter."]

        def give_hitmon(p_id):
            raw = self.game.loader.fetch_specific(p_id)
            pokemon = Pokemon(raw, self.game.assets, size_mult=2.5)
            if len(story.player_team) < 6:
                story.player_team.append(pokemon)
                msgs.append(f"You received {pokemon.name}!")
            else:
                story.deposit_to_pc(pokemon)
                msgs.append(f"You received {pokemon.name}! Sent to BILL'S PC.")
            self.game.data.add_pokemon(pokemon)
            self.game.data.save()

        if not has_marsh:
            msgs.append("You lack the MARSH BADGE. Come back after defeating Sabrina!")
        else:
            if not flags.get("dojo_gift_1"):
                msgs.append("You defeated Sabrina? Exceptional!")
                msgs.append("As a reward, take one of our top students.")
                chosen_id = random.choice([106, 107])
                give_hitmon(chosen_id)
                flags["dojo_gift_1"] = True
                flags["dojo_gift_1_id"] = chosen_id
                msgs.append("I have another gift for you, but you must prove your speed.")
                msgs.append("Go and defeat Koga, the Ninja Master of Fuchsia City!")
            elif not has_soul:
                msgs.append("You have not yet earned the SOUL BADGE.")
                msgs.append("The second gift awaits your victory over Koga!")
            elif not flags.get("dojo_gift_2"):
                msgs.append("You defeated the Ninja Master! Your speed is legendary!")
                msgs.append("Please, take our remaining fighter.")
                first_id = flags.get("dojo_gift_1_id", 106)
                second_id = 107 if first_id == 106 else 106
                give_hitmon(second_id)
                flags["dojo_gift_2"] = True
                msgs.append("Our Dojo is honored to have met you.")
            else:
                msgs.append("Your fighting spirit will take you far, Champion!")

        self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msgs, self.game.assets.fonts["med"], callback=self.end_npc_interaction)

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

        bg_img = self.game.assets.get_background("new_bark_lab.png") or self.game.assets.get_generic_background("lab")
        if bg_img:
            box_top = Utils.get_full_dialogue_rect(self.game).top
            self.npc_bg = pygame.transform.scale(bg_img, (self.game.width, box_top))

        story = self.game.story_manager
        region = getattr(story, "starting_region", "KANTO")

        if story.inventory.get("MYSTERY_EGG", 0) > 0 and not story.story_flags.get("elm_received_egg"):
            msg = [
                "Professor Elm: Oh! This is the Egg Mr. Pokémon found!",
                "It's certainly a mysterious discovery for the Johto region.",
                "I'll need to study this more. Please, keep it with you!",
                "It may reveal its secrets as you grow as a trainer.",
                "Take these Poké Balls for your help with my research.",
                "You received 10 POKé BALLS!",
                "The Gym Leader in Violet City, Falkner, can help you grow further."
            ]
            story.story_flags["elm_received_egg"] = True
            story.balls_left += 10
            callback = self.end_npc_interaction
            self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msg, self.game.assets.fonts["med"], callback=callback)
            return

        if region == "KANTO" and story.story_flags.get("beat_champion") and not story.story_flags.get("unlocked_national_dex"):
            msg = self.game.assets.get_text("johto_elm_congrats")
            if isinstance(msg, list): msg = msg[:]
            else: msg = [msg]

            story.story_flags["unlocked_national_dex"] = True
            story.story_flags["unlocked_johto_badges"] = True
            if story.story_flags.get("received_starter_johto"):
                msg.append("I see you already have a Johto partner. You two make a great team!")
                self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msg, self.game.assets.fonts["med"], callback=self.end_npc_interaction)
                return

            msg.append("To help you on this new leg of your journey...")
            msg.append("Please, choose one of these Johto Pokémon!")

            def johto_starter_exit():
                from src.states.menus import StarterSelectionState
                def change_to_starters(): self.game.change_state(StarterSelectionState(self.game, starter_ids=[152, 155, 158], region="JOHTO"))
                self.start_npc_exit(change_to_starters)
            callback = johto_starter_exit
            self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msg, self.game.assets.fonts["med"], callback=callback)
            return

        if (story.story_flags.get("received_starter_johto")
            and story.story_flags.get("defeated_rival_johto")
            and not story.story_flags.get("elm_silver_report")):

            msg = [
                "Professor Elm: Oh, you're back! Wait... what happened?!",
                "An officer just told me a Pokémon was stolen from the lab!",
                "A red-haired boy was seen lurking around...",
                "You saw him too? And you battled him? Incredible!",
                "Thank you for trying to stop him. He must have been the thief.",
                "While the police handle that, I have a request for you.",
                "My associate, Mr. Pokémon, found something remarkable.",
                "Could you visit him on Route 30? He lives just past Cherrygrove."
            ]
            story.story_flags["elm_silver_report"] = True
            self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msg, self.game.assets.fonts["med"], callback=self.end_npc_interaction)
            return

        if not story.story_flags.get("received_starter_johto") and not story.player_team and region == "JOHTO":
            msg = ["Welcome to Johto!", "I have a special Pokémon for you."]

            def johto_starter_initial_exit():
                from src.states.menus import StarterSelectionState
                def change_to_starters(): self.game.change_state(StarterSelectionState(self.game, starter_ids=[152, 155, 158], region="JOHTO"))
                self.start_npc_exit(change_to_starters)
            callback = johto_starter_initial_exit
        elif region == "KANTO" and not story.game_started:
            msg = ["Professor Oak is looking for you in Pallet Town!", "He has some important research to share."]
            callback = self.end_npc_interaction
        elif region == "JOHTO" and not story.story_flags.get("defeated_rival_johto"):
            msg = ["Wait! You haven't finished your battle with Silver!", "He's still waiting for you outside the lab!"]

            def rival_exit_johto():
                def trigger_battle(): self.retrigger_rival_battle("JOHTO")
                self.start_npc_exit(trigger_battle)
            callback = rival_exit_johto
        else:
            msg = ["Your journey is just beginning!", "Take care of your Pokémon."]
            callback = self.end_npc_interaction

        self.npc_dialogue = ClassicDialogueBox(Utils.get_full_dialogue_rect(self.game), msg, self.game.assets.fonts["med"], callback=callback)

    def retrigger_rival_battle(self, region):
        """Re-triggers a regional rival battle if it was interrupted."""
        from src.states.battle import TrainerBattleState, TrainerIntroState
        from src.pokemon.data import Pokemon

        story = self.game.story_manager
        rival_pkmn = Pokemon(story.rival_starter_raw, self.game.assets, size_mult=2)

        if region == "JOHTO":
            rival_name = "SILVER"
            rival_sprite = self.game.assets.get_trainer_image("silver.png")
            if not rival_sprite:
                rival_sprite = self.game.assets.get_trainer_image("rival.png")
            bg_name = "battle_elmlab.png"
            intro_text = "...You think you're strong?"
        else:
            rival_name = getattr(self.game, "rival_name", "BLUE")
            rival_sprite_key = getattr(self.game, "rival_character", "blue")
            rival_sprite = self.game.assets.get_player_image(rival_sprite_key, back=False)
            if rival_sprite:
                h = int(self.game.height * 0.6)
                w = int(rival_sprite.get_width() * (h / rival_sprite.get_height()))
                rival_sprite = pygame.transform.scale(rival_sprite, (w, h))
            else:
                rival_sprite = self.game.assets.get_trainer_image("rival.png")
            bg_name = "battle_oaklab.png"
            intro_text = "Let's settle this!"

        battle_state = TrainerBattleState(
            self.game, rival_pkmn, trainer_sprite=rival_sprite,
            trainer_class="RIVAL", trainer_name=rival_name, battle_type="rival"
        )

        lab_bg = self.game.assets.get_background(bg_name) or self.game.assets.get_generic_background("battle_indoor")
        if lab_bg:
            box_top = Utils.get_full_dialogue_rect(self.game).top - 8
            battle_state.background = pygame.transform.scale(lab_bg, (self.game.width, box_top))

        self.game.change_state(TrainerIntroState(self.game, rival_sprite, intro_text, battle_state))

    def start_npc_exit(self, callback=None):
        """Initializes the slide-off sequence for an NPC."""
        self.is_npc_exiting = True
        self.npc_exit_callback = callback

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

    def visit_fishing_guru(self):
        """Vermilion's Fishing Guru (canon): a guaranteed Old Rod, so fishing never depends on an
        optional trainer."""
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "fishing_guru"
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("fisherman.png")
        story = self.game.story_manager
        msgs = ["Fishing Guru: I'm the Fishing Guru! Do you like to fish?"]
        if not story.story_flags.get("got_old_rod_guru"):
            story.story_flags["got_old_rod_guru"] = True
            if story.inventory.get("OLD_ROD", 0) > 0:
                story.inventory["RARE_CANDY"] = story.inventory.get("RARE_CANDY", 0) + 1
                msgs += ["You already have a rod? Then have this Rare Candy instead!"]
            else:
                story.inventory["OLD_ROD"] = 1
                msgs += ["Take this Old Rod! Use FISH wherever there is water.", "You received the OLD ROD!"]
        else:
            msgs.append("Fishing is a way of life!")
        self.npc_dialogue = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(self.game), msgs, self.game.assets.fonts["med"],
            callback=self.end_npc_interaction)

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

        has_beat_brock = self.game.story_manager.has_badge("BOULDER")
        has_earth_badge = self.game.story_manager.has_badge("EARTH")
        got_museum_fossil = flags.get("received_museum_fossil", False)
        got_second_fossil = flags.get("received_museum_fossil_2", False)

        if has_beat_brock:
            if not got_museum_fossil:
                fossil = random.choice(["HELIX_FOSSIL", "DOME_FOSSIL"])
                flags["museum_fossil_choice"] = fossil
                msgs.append("You defeated Brock? That's impressive!")
                msgs.append(f"We found this {fossil.replace('_', ' ').title()} in the mountain.")
                msgs.append("You should have it!")
                msgs.append(f"You received the {fossil.replace('_', ' ').title()}!")
                inv[fossil] = inv.get(fossil, 0) + 1
                flags["received_museum_fossil"] = True
                msgs.append("Come back once you've earned the Earth Badge. We may find another!")
            elif has_earth_badge and not got_second_fossil:
                first_fossil = flags.get("museum_fossil_choice", "HELIX_FOSSIL")
                second_fossil = "DOME_FOSSIL" if first_fossil == "HELIX_FOSSIL" else "HELIX_FOSSIL"
                msgs.append("The Earth Badge! You've become a true hero.")
                msgs.append(f"Our team found the other fossil: the {second_fossil.replace('_', ' ').title()}!")
                msgs.append("A Master like you should preserve it.")
                msgs.append(f"You received the {second_fossil.replace('_', ' ').title()}!")
                inv[second_fossil] = inv.get(second_fossil, 0) + 1
                flags["received_museum_fossil_2"] = True
            elif not got_second_fossil:
                msgs.append("Welcome to the Pewter Museum of Science!")
                msgs.append("Come back once you've earned the Earth Badge. We may find another fossil!")
            else:
                msgs.append("Welcome to the Pewter Museum of Science!")
                msgs.append("Both fossils are in good hands. Thank you, Champion!")
            if not flags.get("received_old_amber"):
                # Canon (FRLG): a scientist at the museum's back door hands over the Old Amber.
                msgs.append("Scientist: Psst! Out back, we have a piece of amber with something inside.")
                msgs.append("Take it to the Pokemon Lab on Cinnabar Island. You received the Old Amber!")
                inv["OLD_AMBER"] = inv.get("OLD_AMBER", 0) + 1
                flags["received_old_amber"] = True
        else:
            msgs.append("Welcome! Please return after you have defeated Brock.")

        self.npc_dialogue = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(self.game),
            msgs,
            self.game.assets.fonts["med"],
            callback=self.end_npc_interaction
        )

    FOSSILS = {
        "HELIX_FOSSIL": 138, "DOME_FOSSIL": 140, "OLD_AMBER": 142,      # Kanto
        "ROOT_FOSSIL": 345, "CLAW_FOSSIL": 347,                          # Hoenn
        "SKULL_FOSSIL": 408, "ARMOR_FOSSIL": 410,                        # Sinnoh
        "COVER_FOSSIL": 564, "PLUME_FOSSIL": 566,                        # Unova
        "JAW_FOSSIL": 696, "SAIL_FOSSIL": 698,                           # Kalos
    }
    # Galar fossils are halves: one top (bird/fish) + one bottom (drake/dino).
    FOSSIL_COMBOS = {
        ("FOSSILIZED_BIRD", "FOSSILIZED_DRAKE"): 880, ("FOSSILIZED_BIRD", "FOSSILIZED_DINO"): 881,
        ("FOSSILIZED_FISH", "FOSSILIZED_DRAKE"): 882, ("FOSSILIZED_FISH", "FOSSILIZED_DINO"): 883,
    }

    def _next_fossil_revival(self):
        """(items to use, Pokemon id) for the next revivable fossil, preferring species not yet owned."""
        inv = self.game.story_manager.inventory
        owned = {v.get("id") for v in self.game.data.data.get("pokedex", {}).values() if isinstance(v, dict)}
        options = [((name,), pid) for name, pid in self.FOSSILS.items() if inv.get(name, 0) > 0]
        options += [(pair, pid) for pair, pid in self.FOSSIL_COMBOS.items() if all(inv.get(p, 0) > 0 for p in pair)]
        options.sort(key=lambda o: o[1] in owned)
        return options[0] if options else (None, None)

    def visit_stoneman(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "stoneman"
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("ruinmaniac.png")

        items, target_id = self._next_fossil_revival()

        msgs = ["Welcome to the fossil lab!", "We can bring ancient Pokémon back to life."]

        if items:
            label = " and ".join(i.replace('_', ' ').title() for i in items)
            msgs.append(f"Oh! Is that a {label}?")
            msgs.append("We can revive it for you right now!" if len(items) == 1
                        else "These two pieces fit together. Let's restore them!")
            self.pending_revival = (items, target_id)
            callback = self.perform_fossil_revival
        else:
            msgs.append("I am always looking for ancient fossils.")
            msgs.append("Bring me any you find in your travels!")
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

        story = self.game.story_manager
        flags = story.story_flags
        owned_ids = {p.id for p in story.player_team if p} | {p.id for p in story.pc_pokemon if p}  # PC has empty (None) slots

        r25_data = self.game.loader.area_data.get("STORY_PROGRESSION", {}).get("KANTO_ROUTE_25", {})
        r25_pool = r25_data.get("trainer_pool", [])
        r25_defeated = story.defeated_trainers.get("KANTO_ROUTE_25", set())
        bridge_clear = len(r25_pool) > 0 and len(r25_defeated) >= len(r25_pool)

        msgs = ["Hi! I'm Bill!", "I'm the developer of the PC Storage System."]

        def grant_eevee(flag_name):
            flags[flag_name] = True
            raw = self.game.loader.fetch_specific(133)
            new_eevee = Pokemon(raw, self.game.assets, size_mult=2.5)
            if len(story.player_team) < 6:
                story.player_team.append(new_eevee)
                msgs.append("You received EEVEE!")
            else:
                story.deposit_to_pc(new_eevee)
                msgs.append("You received EEVEE! Sent to BILL'S PC.")
            self.game.data.add_pokemon(new_eevee)
            self.game.data.save()

        if flags.get("received_bill_eevee_snorlax"):
            if flags.get("received_bill_eevee_lickitung"):
                msgs.append("Thanks for helping with my research!")
                msgs.append("I hope those Eevees are finding good homes on your team.")
            elif 108 in owned_ids:
                msgs.append("Incredible! That's a Lickitung!")
                msgs.append("I've heard they are rare and mostly found in the Safari Zone.")
                msgs.append("Fascinating... those tongues are even longer than the reports said!")
                msgs.append("Please, take this last Eevee as thanks for your help.")
                grant_eevee("received_bill_eevee_lickitung")
            else:
                msgs.append("My next project involves Pokémon with extremely long tongues.")
                msgs.append("I hear there's a specialized 'Safari Zone' out in Fuchsia City.")
                msgs.append("If you find one, come show me for a reward!")

        elif flags.get("received_bill_eevee"):
            if 143 in owned_ids:
                msgs.append("Wow! You actually caught a Snorlax!")
                msgs.append("Those things are massive. You must be a very skilled trainer.")
                msgs.append("I knew there was something worth investigating in Lavender Town.")
                msgs.append("Here, take this Eevee as a special reward!")
                grant_eevee("received_bill_eevee_snorlax")
            else:
                msgs.append("I've been hearing rumors about a giant Pokémon blocking paths.")
                msgs.append("They say it's related to some spooky business in Lavender Town.")
                msgs.append("If you can show me a Snorlax, I'll give you another Eevee!")

        elif bridge_clear:
            if not flags.get("received_bill_eevee"):
                msgs.append("Wow! You cleared the Nugget Bridge challenge?")
                msgs.append("That's impressive! Most trainers give up halfway.")
                msgs.append("Here, take this special Pokémon as a reward!")
                grant_eevee("received_bill_eevee")
            else:
                msgs.append("I hope Eevee is doing well!")

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
        items, p_id = getattr(self, 'pending_revival', (None, None))
        if not items:
            return

        from src.states.systems import FossilRevivalState
        self.game.change_state(FossilRevivalState(self.game, items[0], p_id, self, consume=list(items)))

    def resolve_oldman_no(self):
        self.choice_active = False
        self.yes_btn.set_visibility(False)
        self.no_btn.set_visibility(False)
        self.npc_dialogue.reset("You left the old man to his dreams.")
        self.npc_dialogue.callback = self.end_npc_interaction

    def end_npc_interaction(self):
        """Cleans up NPC states. Now triggers slide-out before fully closing."""
        if self.npc_active and not self.is_npc_exiting:
            self.start_npc_exit()
            return

        self.npc_active = False
        self.is_npc_exiting = False
        self.npc_exit_callback = None
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

    def _try_on_enter_event(self, on_enter):
        """Fire one on_enter trainer battle if its condition is met. Returns True if it fired."""
        story = self.game.story_manager
        condition = on_enter.get("condition")
        v_flag = on_enter.get("flag_check")
        met = False

        if v_flag and story.story_flags.get(v_flag):
            met = False
        elif condition == "first_time":
            flag = f"cleared_event_{self.area_key}_{on_enter.get('type')}"
            if not story.story_flags.get(flag):
                met = True
                story.story_flags[flag] = True
        elif condition:
            met = self._check_menu_condition(condition)
        if not (met and on_enter.get("type") == "trainer_battle"):
            return False

        t_info = dict(on_enter["trainer"])
        team_ids = t_info.get("team", [])
        newbark_rival = (self.area_key == "NEW_BARK_TOWN"
                         and story.story_flags.get("johto_rival_met_in_lab")
                         and not story.story_flags.get("defeated_rival_newbark_ambush"))
        choice = (t_info.get("team_choice") or {}).get(str(_region_starter_id(self.game)))
        if choice:
            team_ids = list(choice)
        elif newbark_rival:
            team_ids = [random.choice([152, 155, 158])]

        is_start_town = self.area_key == story.get_region_start(
            story.get_current_region()).get("start_area")
        starter_battle = (newbark_rival or (is_start_town and str(condition).endswith("_starter"))
                          or bool(on_enter.get("starter_battle")))  # e.g. Silver in Cherrygrove
        if len(team_ids) == 1 and (newbark_rival or is_start_town or on_enter.get("starter_battle")):
            story.rival_starter_raw = self.game.loader.fetch_specific(team_ids[0])
            story.note_rival_starter()

        opponent_team = [Pokemon(self.game.loader.fetch_specific(tid), self.game.assets, size_mult=3.125)
                         for tid in team_ids]
        forms.mark_trainer_team(opponent_team, t_info)
        if t_info.get("levels"):
            levels.set_team(opponent_team, list(t_info["levels"]), exact=True)  # exact levels from the games
        elif starter_battle:
            levels.set_team(opponent_team, [5] * len(opponent_team))
        else:
            levels.set_team(opponent_team, levels.trainer_team_levels(
                self.game, self.area_key, len(opponent_team), boss=True))

        from src.states.battle import TrainerBattleState, TrainerIntroState
        sprite = _trainer_sprite(self.game, t_info.get("sprite", "rival.png"))
        dlg = t_info.get("dialogue") or {}
        battle_state = TrainerBattleState(
            self.game,
            opponent_team,
            trainer_sprite=sprite,
            trainer_class=t_info.get("class", "TRAINER"),
            trainer_name=_fill_names(self.game, t_info.get("name")),
            custom_dialogue={k: _resolve_lines(self.game, v) for k, v in dlg.items() if k != "intro"},
            rewards=t_info.get("rewards"),
            battle_type="event",
            area_name=self.area_key,
            victory_flag=v_flag or t_info.get("victory_flag"),
            starter_battle=starter_battle,
        )
        intro_text = _resolve_lines(
            self.game, dlg.get("intro") or t_info.get("intro", "I'm gonna be the world's greatest trainer!"))
        self.game.change_state(TrainerIntroState(self.game, sprite, intro_text, battle_state))
        return True

    def go_to_area(self, area_key, message=None):
        """Travel; a ship or train ride shows its own message on the way."""
        if area_key:
            self.game.change_state(AreaTransitionState(self.game, area_key, initial_message=message))

    def go_to_next_area(self):
        next_area = self.area_data.get("next_area")
        if next_area:
            self.game.change_state(AreaTransitionState(self.game, next_area))

    def save_game(self):
        from src.states.menus import SaveState
        self.game.change_state(SaveState(self.game, self))

    def start(self):
        if hoenn.needs_choice(self.game.story_manager):
            from src.states.hoenn import HoennVersionState
            self.game.change_state(HoennVersionState(self.game, lambda: CityState(self.game)))
            return
        pending = self.game.story_manager.pending_starter()
        if pending:  # first visit to a region: its professor's partner Pokemon, before anything else
            from src.states.menus import StarterSelectionState
            cfg = self.game.story_manager.get_region_start(pending)
            self.game.story_manager.sync_rival()  # this region's rival in the intro text
            self.game.change_state(StarterSelectionState(self.game, starter_ids=cfg.get("starters"), region=pending))
            return
        self.clear_hover_menu()
        self.game.ui_manager.add_element(self.action_menu)

        visited_flag = f"visited_{self.area_key}"
        if not self.game.story_manager.story_flags.get(visited_flag, False):
            self.game.story_manager.story_flags[visited_flag] = True

        events = self.area_data.get("on_enter_event")
        if isinstance(events, dict):
            events = [events]
        if getattr(self.game, "skip_arrival_event", False):
            self.game.skip_arrival_event = False
            events = []
        for on_enter in events or []:
            if self._try_on_enter_event(on_enter):
                return

        if self.area_key == "INDIGO_PLATEAU":
            prog = self.game.story_manager.story_flags.get("gym_progress_INDIGO_PLATEAU", 0)
            if prog >= 4:
                self.game.story_manager.story_flags["beat_elite_four"] = True
            if prog >= 5:
                self.game.story_manager.story_flags["beat_champion"] = True

        pygame.event.clear()
        for btn in self.hud_buttons:
            if btn not in self.game.ui_manager.elements:
                self.game.ui_manager.add_element(btn)

        story = self.game.story_manager
        region = story.get_current_region()
        story.enter_region(region)
        offer_flag = f"move_offer_{region.lower()}"
        if story.is_region_champion(region) and not story.story_flags.get(offer_flag):
            story.story_flags[offer_flag] = True
            link_lines = []
            if story.link_champion_regions():  # a second (or later) title: PCs and Bags join up
                names = [r.title() for r in sorted(story.linked_regions)]
                link_lines = [
                    "*Ring ring!* It's the Pokemon Professor!",
                    f"Professor: Congratulations, Champion of {', '.join(names[:-1])} and {names[-1]}!",
                    "Your regional PCs are now linked. Pokemon from any of those regions can join your team,",
                    "and your Bags have been combined too. Use them freely in every region you've conquered!"]
            if story.get_region_start(region).get("travel_only"):
                self.show_message(link_lines + self.ISLAND_CHAMPION)  # a trip, not a new home: no move offer
                return
            road = self.ROAD_OPEN.get(region)
            if road:  # Kanto <-> Johto: the road is open, go now or later (Mom's offer follows)
                story.inventory["SS_TICKET"] = 1
                road = road + ["You received an S.S. TICKET!",
                               "The S.S. Aqua sails between Vermilion City and Olivine City."]
                if story.is_region_champion("KANTO") and story.is_region_champion("JOHTO"):
                    road += self.ORANGE_INVITE
                self.show_message(link_lines + road, callback=lambda: self._offer_move(region, phone=True))
            elif link_lines:
                self.show_message(link_lines, callback=lambda: self._offer_move(region, phone=True))
            else:
                self._offer_move(region, phone=True)
            return
        notice = seasons.season_change_notice(self.game, story, region)
        if notice:
            self.show_message(notice)

    ROAD_OPEN = {
        "KANTO": ["Professor Oak: Congratulations, Champion!",
                  "The Pokemon League has opened the road to the Johto region for you.",
                  "From the League's Reception Gate, follow Route 26 and Route 27 east to New Bark Town.",
                  "Go now, or whenever you're ready. The road will stay open!"],
        "JOHTO": ["Professor Elm: You did it, Champion!",
                  "With the Johto title, the road to Kanto is open.",
                  "From New Bark Town, take Route 27 west past Tohjo Falls to the Pokemon League's Reception Gate,",
                  "then Route 22 to Viridian City. Go now, or whenever you like!"],
    }
    # Both titles: Professor Ivy invites the Champion of Kanto and Johto to the Orange Islands.
    ORANGE_INVITE = ["...A letter has arrived from Professor Ivy of Valencia Island!",
                     "\"Champion of Kanto AND Johto! The Orange Crew would love to meet you.",
                     "Beat the four Gym Leaders of the Orange Islands and challenge the Orange League!\"",
                     "Ships to the Orange Islands leave from Vermilion City and Olivine City."]
    ISLAND_CHAMPION = ["Drake: The Winner's Trophy is yours. You're the Orange League Champion!",
                       "Your name will be carved into the wall of Pummelo Stadium.",
                       "The ships still sail between the islands. Come back any time for a rematch!"]

    def _offer_move(self, region, phone):
        """Mom uses the championship prize money for a new home and asks where to move."""
        name = self.game.player_name
        if phone:
            lines = ["*Ring ring!* It's Mom calling!",
                     f"Mom: {name}! I just watched the broadcast. You're the {region.title()} Champion!",
                     "Mom: Your prize money arrived, and it's more than enough to buy us a brand-new home.",
                     "Mom: I've been browsing houses all over the world... Where should we move next?"]
        else:
            lines = ["Mom: Still thinking about moving?",
                     "Mom: There's plenty of championship money left for a new house. Where to?"]

        from src.states.menus import RegionSelectionState
        if not RegionSelectionState.new_regions(self.game.story_manager):
            # every region played: nowhere new to move
            self.show_message((lines[:2] if phone else []) + ["Mom: You've been Champion all over the world! I'm so proud of you.",
                                           "Mom: There's nowhere new left to move. Enjoy being a Champion!"])
            return

        def open_picker():
            from src.states.menus import RegionSelectionState
            self.end_npc_interaction()
            self.game.change_state(RegionSelectionState(self.game, mode="move", return_state=CityState(self.game)))

        self.show_message(lines, callback=open_picker)

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
        if self.npc_active:
            if self.is_npc_exiting:
                self.npc_slide_offset += 40
                if self.npc_slide_offset >= 400:
                    cb = self.npc_exit_callback
                    self.end_npc_interaction()
                    if cb:
                        cb()
                return

            if self.npc_dialogue and self.npc_dialogue.visible:
                if self.npc_slide_offset > 0:
                    self.npc_slide_offset = max(0, self.npc_slide_offset - 40)

            self.npc_dialogue.update()

            if self.current_npc == "oldman" and self.npc_dialogue.current_line == 2 and self.npc_dialogue.is_waiting_for_click:
                self.choice_active = True

            if self.choice_active:
                box = self.npc_dialogue.rect
                self.yes_btn.rect = pygame.Rect(box.right - 280, box.bottom - 80, 120, 60)
                self.no_btn.rect = pygame.Rect(box.right - 140, box.bottom - 80, 120, 60)
                self.yes_btn.callback = self.resolve_oldman_yes
                self.no_btn.callback = self.resolve_oldman_no

                if self.yes_btn in self.game.ui_manager.elements:
                    self.game.ui_manager.elements.remove(self.yes_btn)
                if self.no_btn in self.game.ui_manager.elements:
                    self.game.ui_manager.elements.remove(self.no_btn)
                self.game.ui_manager.add_element(self.yes_btn)
                self.game.ui_manager.add_element(self.no_btn)

                self.yes_btn.set_visibility(True)
                self.no_btn.set_visibility(True)

    def draw(self):
        screen = self.game.screen
        screen.fill(BLACK)

        if self.npc_active and hasattr(self, "npc_bg") and self.npc_bg:
            screen.blit(self.npc_bg, (0, 0))
        else:
            if self.background:
                screen.blit(self.background, (0, 0))

        if self.hover_menu_active and self.hover_bg_rect:
            pygame.draw.rect(screen, WHITE, self.hover_bg_rect, border_radius=12)
            pygame.draw.rect(screen, BLACK, self.hover_bg_rect, 6, border_radius=12)

        if self.npc_active and self.npc_dialogue:
            if self.npc_sprite:
                rect = self.npc_sprite.get_rect(
                    center=(self.game.width / 2 + self.npc_slide_offset, self.game.height / 2 - 50)
                )
                screen.blit(self.npc_sprite, rect)

            self.npc_dialogue.draw(screen)

        self.game.ui_manager.draw(screen)

        lbl_text = "Balls:"
        lbl_width = self.game.assets.fonts["small"].size(lbl_text)[0]

        Utils.draw_text_outline(
            screen, lbl_text, self.game.assets.fonts["small"], WHITE, 20, 20, align="left", outline_color=BLACK
        )

        icon_w = 0
        if self.game.assets.ui_ball:
            screen.blit(self.game.assets.ui_ball, (20 + lbl_width + 5, 15))
            icon_w = self.game.assets.ui_ball.get_width()

        Utils.draw_text_outline(
            screen,
            f"x{self.game.story_manager.balls_left}",
            self.game.assets.fonts["small"],
            WHITE,
            20 + lbl_width + 5 + icon_w + 5,
            20,
            align="left"
        )
        _draw_season_hud(self.game, screen, self.area_key, 20, 58)


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

        rect = Utils.get_full_dialogue_rect(self.game)
        msg = []
        if initial_message:
            msg.append(initial_message)
        # Another region's party, PC and Bag; a first visit goes to that region's professor.
        self.next_area_key, travel_lines = self.game.story_manager.prepare_travel(next_area_key)
        msg += travel_lines
        if travel_lines:
            self.wait_for_dialogue = True

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
        self.npc_sprite = None
        self.npc_pos_x = -300

        if initial_message:
            is_oak = "Oak" in initial_message
            is_elm = "Elm" in initial_message

            if is_oak or is_elm:
                bg_name = "pallet_city_lab.png" if is_oak else "new_bark_lab.png"
                kanto_dir = self.game.assets.kanto_backgrounds_dir
                johto_dir = os.path.join(os.path.dirname(kanto_dir), "johto")

                for d in [kanto_dir, johto_dir]:
                    path = os.path.join(d, bg_name)
                    if os.path.exists(path):
                        box_top = Utils.get_full_dialogue_rect(self.game).top
                        self.bg = pygame.transform.scale(pygame.image.load(path).convert(), (self.game.width, box_top))
                        break

                prof_name = "Oak" if is_oak else "Elm"
                self.dialogue_box.reset([f"{prof_name}: Excellent battle!", "You have great potential.", initial_message])

                sprite_name = "oak.png" if is_oak else "elm.png"
                sprite_path = os.path.join(self.game.assets.sprites_dir, "png", sprite_name)
                if os.path.exists(sprite_path):
                    img = pygame.image.load(sprite_path).convert_alpha()
                    h = int(self.game.height * 0.6)
                    w = int(img.get_width() * (h / img.get_height()))
                    self.npc_sprite = pygame.transform.scale(img, (w, h))

    def handle_events(self, events):
        for event in events:
            self.dialogue_box.handle_event(event)

    def update(self):
        self.dialogue_box.update()
        if self.npc_sprite:
            target_x = self.game.width // 2
            if not self.dialogue_box.is_finished:
                if self.npc_pos_x < target_x:
                    self.npc_pos_x += (target_x - self.npc_pos_x) * 0.05
            else:
                self.npc_pos_x += 40

        if self.wait_for_dialogue:
            if self.dialogue_box.is_finished:
                self.timer -= 1
        else:
            self.timer -= 1

        if self.timer <= 0:
            self.timer = 10**9  # only once
            self.game.story_manager.current_area_key = self.next_area_key
            self.game.story_manager.enter_region(self.game.story_manager.get_current_region())

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
            if self.game.story_manager.autosave:
                autosave(self.game)

    def draw(self):
        if self.bg:
            self.game.screen.blit(self.bg, (0, 0))
        else:
            self.game.screen.fill(BLACK)
        if self.npc_sprite:
            rect = self.npc_sprite.get_rect(midbottom=(self.npc_pos_x, self.dialogue_box.rect.top))
            self.game.screen.blit(self.npc_sprite, rect)
        self.dialogue_box.draw(self.game.screen)


def _collapse_hud(state):
    """The side menus (PC, Bag, Badges, Save...) live behind one big MENU button that opens a
    grid of large tiles, instead of a column of small buttons."""
    state.menu_entries = state.hud_buttons

    def open_menu():
        if hasattr(state, "is_resuming"):
            state.is_resuming = True  # a route comes back to the same encounter
        from src.states.menu_grid import MenuGridState
        state.game.change_state(MenuGridState(state.game, state, state.menu_entries))

    state.hud_buttons = [Button((20, 70, 170, 72), "MENU", state.game.assets.fonts["s_med"], open_menu,
                                bg_color=(60, 96, 210), autosize=False)]


def evolve_ready_party(game, return_state):
    """Evolve a party Pokemon that is ready (e.g. it hit its level in a gym or town battle),
    then go on to return_state. Returns True if an evolution started."""
    scan = PlayState.__new__(PlayState)  # only the party scan is needed, not a whole route
    scan.game = game
    scan._evo_return = return_state
    return scan._scan_list_for_evolution(game.story_manager.player_team, False, "party")


def is_league(gym_data):
    """A Pokemon League: Elite Four trainers and/or a Champion (every region's)."""
    gym_data = gym_data or {}
    leader = gym_data.get("leader") or {}
    return (leader.get("class") == "CHAMPION"
            or any(t.get("class") == "ELITE_FOUR" for t in gym_data.get("trainers", [])))


def reset_league_after_loss(game):
    """Losing at a Pokemon League sends you back to the start of the Elite Four, as in the games."""
    story = game.story_manager
    area = story.get_current_area_data()
    if is_league(area.get("gym")):
        story.story_flags[f"gym_progress_{story.current_area_key}"] = 0


def autosave(game):
    """Save quietly (Options > AUTOSAVE); a failed write never stops the game."""
    try:
        game.update_save_data()
        game.data.save()
    except Exception as e:
        print(f"Autosave failed: {e}")


def white_out(game):
    """Whiting out: heal the team and wake up at the last Pokemon Center used in
    this region, or at home if you haven't used one yet."""
    story = game.story_manager
    for p in story.player_team:
        p.heal_full()
        if hasattr(p, "revert_transform"):
            p.revert_transform()
    story.current_area_key, has_center = story.whiteout_destination()
    area = story.get_current_area_data()
    if area.get("area_type") == "town":
        game.skip_arrival_event = True  # no rival ambush the moment you wake up
        town = game.states["city"] = CityState(game)
    else:
        town = game.states["play"] = PlayState(game)
    if has_center:
        game.change_state(PokeCenterState(game, town, lines=[
            "You hurried back to the Pokémon Center, protecting your exhausted Pokémon.",
            "Nurse: We've healed your Pokémon after that tough battle.",
            "Please take care out there!",
        ]))
    else:
        game.change_state(town)
        game.show_dialogue([
            "You hurried home, protecting your exhausted Pokémon.",
            "Mom: Oh, you're back! You must have had a tough battle.",
            "I've looked after your Pokémon. They're full of energy again!",
        ])


# [REF-0030: City & Building Logic]
class PokeCenterState(GameState):
    def __init__(self, game, previous_state, lines=None):
        super().__init__(game)
        self.previous_state = previous_state
        self.timer = 0
        self.phase = "HEAL"
        self.bg = self._load_building_bg(game, "center")
        game.story_manager.last_center = game.story_manager.current_area_key

        self.nurse_sprite = None if getattr(self, "generic_bg", False) else game.assets.get_trainer_image("nurse.png")
        self.dialogue_box = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(game),
            lines or ["Welcome to the Pokémon Center!", "We've restored your team to full health."],
            game.assets.fonts["med"],
            callback=self.finish_heal
        )

        for p in self.game.story_manager.player_team:
            p.heal_full()
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.play()

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)

    def _load_building_bg(self, game, type_suffix):
        area_data = game.story_manager.get_current_area_data()
        json_key = "pokecenter" if type_suffix == "center" else "pokemart"
        bg_config = area_data.get("backgrounds", {}).get(json_key)

        area_key = game.story_manager.current_area_key
        # ARCHITECT: Fallback naming logic: [area_key]_[suffix] (e.g. azalea_town_center.png)
        fallback_name = f"{area_key.lower()}_{type_suffix}.png"

        # A generic name (pokecenter.png) is only a last resort: this town's own art comes first.
        generic = bg_config in ("pokecenter.png", "pokemart.png")
        filenames = ([fallback_name, bg_config] if generic else [bg_config, fallback_name]) if bg_config             else [fallback_name]
        box_top = Utils.get_full_dialogue_rect(game).top

        for filename in filenames:
            img = game.assets.get_background(filename)
            if img:
                return pygame.transform.scale(img, (game.width, box_top))

        img = game.assets.get_generic_background(type_suffix)
        if img:
            self.generic_bg = True  # the stand-in Center already has Nurse Joy at the counter
            return pygame.transform.scale(img, (game.width, box_top))
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


# [REF-0035: Gym Lobby State]
class GymLobbyState(GameState):
    def __init__(self, game, previous_state=None):
        super().__init__(game)
        self.area_key = game.story_manager.current_area_key
        self.area_data = game.story_manager.get_current_area_data()
        self.gym_data = self.area_data.get("gym", {})

        self.bg = None
        bg_config = self.area_data.get("backgrounds", {}).get("gym")
        if isinstance(bg_config, list) and bg_config:
            bg_config = bg_config[0]

        # ARCHITECT: Standardized fallback to [area_key]_gym.png (e.g. azalea_town_gym.png)
        fallback_name = f"{self.area_key.lower()}_gym.png"

        filenames = [bg_config, fallback_name] if bg_config else [fallback_name]
        box_top = Utils.get_full_dialogue_rect(self.game).top

        for filename in filenames:
            img = self.game.assets.get_background(filename)
            if img:
                self.bg = pygame.transform.scale(img, (self.game.width, box_top))
                break

        if not self.bg:
            img = game.assets.get_generic_background("gym")
            if img:
                self.bg = pygame.transform.scale(img, (self.game.width, box_top))
        if not self.bg:
            self.bg = pygame.Surface((game.width, int(game.height * 0.75)))
            self.bg.fill((40, 40, 60))

        self.prog_key = f"gym_progress_{self.area_key}"
        self.progress = game.story_manager.story_flags.get(self.prog_key, 0)
        self.trainers = self.gym_data.get("trainers", [])
        self.leader = self.gym_data.get("leader")

        self.next_opponent = None
        self.is_cleared = False
        self.region = game.story_manager.get_current_region()
        self.is_league = is_league(self.gym_data)

        if self.is_league:
            # Every region's League: the Elite Four and the Champion in a row. A loss starts it
            # over (see reset_league_after_loss), and after the title it's a rematch run.
            if self.progress > len(self.trainers):
                self.progress = 0
                game.story_manager.story_flags[self.prog_key] = 0

            self.gauntlet = self.trainers + [self.leader]
            self.rematch = game.story_manager.is_region_champion(self.region)
            mode_text = "Rematch" if self.rematch else "League Challenge"

            if self.progress < len(self.gauntlet):
                self.next_opponent = self.gauntlet[self.progress]
                if self.progress == len(self.gauntlet) - 1:
                    if self.area_key == "INDIGO_PLATEAU":
                        r_name = ((game.story_manager.region_rivals.get("KANTO") or {}).get("name")
                                  or getattr(self.game, "rival_name", "CHAMPION"))
                    else:
                        r_name = _fill_names(self.game, self.leader.get("name", "the Champion"))
                    self.status_text = f"{mode_text} - Final Match: Champion {r_name}"
                else:
                    self.status_text = f"{mode_text}: Match {self.progress + 1}/{len(self.gauntlet)}"
            else:
                self.is_cleared = True
                self.status_text = "The League has been conquered!"
        else:
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
        self.game.transitioning = False

        self.game.ui_manager.elements.clear()
        self.game.ui_manager.add_element(self.btn_challenge)
        self.game.ui_manager.add_element(self.btn_exit)

    # Kanto Champion (FireRed/LeafGreen): the rival's team by the starter they took.
    FRLG_RIVAL_LINE = {1: 1, 2: 1, 3: 1, 152: 1, 4: 4, 5: 4, 6: 4, 155: 4, 7: 7, 8: 7, 9: 7, 158: 7}
    FRLG_CHAMPION = {
        1: ([18, 65, 112, 130, 59, 3], [59, 57, 59, 59, 61, 63]),    # Venusaur
        4: ([18, 65, 112, 103, 130, 6], [59, 57, 59, 59, 61, 63]),   # Charizard
        7: ([18, 65, 112, 59, 103, 9], [59, 57, 59, 59, 61, 63]),    # Blastoise
    }

    # FireRed/LeafGreen rematch (post-Sevii) teams, used once the Champion has been beaten.
    FRLG_E4_REMATCH = {
        "LORELEI": ([87, 91, 221, 124, 131], [64, 63, 63, 66, 66]),
        "BRUNO": ([208, 107, 106, 208, 68], [65, 65, 65, 66, 66]),
        "AGATHA": ([94, 169, 200, 24, 94], [66, 66, 65, 66, 70]),
        "LANCE": ([130, 149, 230, 142, 149], [68, 66, 66, 70, 72]),
    }
    FRLG_CHAMPION_REMATCH = {
        1: ([214, 65, 248, 59, 130, 3], [72, 73, 72, 73, 73, 75]),   # Venusaur
        4: ([214, 65, 248, 130, 103, 6], [72, 73, 72, 73, 73, 75]),  # Charizard
        7: ([214, 65, 248, 103, 59, 9], [72, 73, 72, 73, 73, 75]),   # Blastoise
    }

    def challenge_gym(self):
        if self.is_cleared or not self.next_opponent or self.game.transitioning:
            return
        if self._start_gym_puzzle():
            return

        self.game.transitioning = True

        t_data = self.next_opponent.copy()
        from src.states.battle import TrainerBattleState, TrainerIntroState

        is_leader = (self.next_opponent == self.leader)
        if self.area_key == "INDIGO_PLATEAU" and is_leader:
            # Champion: your KANTO rival (never the rival of a region you moved to), with their
            # FireRed/LeafGreen team and levels.
            kr = self.game.story_manager.region_rivals.get("KANTO") or {}
            rival_name = kr.get("name") or getattr(self.game, "rival_name", "BLUE")
            rival_char = kr.get("character") or getattr(self.game, "rival_character", "blue")
            img = self.game.assets.get_player_image(rival_char, back=False)
            if img:
                h = int(self.game.height * 0.6)
                w = int(img.get_width() * (h / img.get_height()))
                trainer_sprite = pygame.transform.scale(img, (w, h))
            else:
                trainer_sprite = self.game.assets.get_trainer_image("rival.png")
            starter_id = self.game.story_manager.rival_starter_id("KANTO", 1)
            rematch = bool(self.game.story_manager.story_flags.get("beat_champion"))
            table = self.FRLG_CHAMPION_REMATCH if rematch else self.FRLG_CHAMPION
            team, team_levels = table.get(self.FRLG_RIVAL_LINE.get(starter_id, 4))
            t_data.update({"name": rival_name, "class": "CHAMPION", "team": list(team),
                           "levels": list(team_levels)})
            t_data["dialogue"] = {
                "intro": [f"{rival_name}: Hey, {self.game.player_name}!",
                          "I was looking forward to seeing you here.",
                          "My rival should be strong to keep me sharp. While working on the Pokedex, "
                          "I looked all over for powerful Pokemon. And now... I'm the Pokemon League Champion!",
                          f"{self.game.player_name}! Do you know what that means? I'll tell you. "
                          "I am the most powerful trainer in the world!"],
                "player_won": ["NO! That can't be! You beat my best!",
                               "After all that work to become League Champ? My reign is over already? "
                               "It's not fair!"],
                "player_lost": ["Hahaha! I won, I won! I'm too good for you, "
                                f"{self.game.player_name}!"],
            }
        else:
            trainer_sprite = _trainer_sprite(self.game, t_data.get("sprite"))
            choice = (t_data.get("team_choice") or {}).get(str(_region_starter_id(self.game)))
            if choice:
                t_data["team"] = list(choice)
            t_data["name"] = _fill_names(self.game, t_data.get("name"))
            if t_data.get("dialogue"):
                t_data["dialogue"] = {k: _resolve_lines(self.game, v) for k, v in t_data["dialogue"].items()}
        # Rematches after the title: the games' rematch teams where we have them (FireRed/LeafGreen
        # for Kanto, HeartGold/SoulSilver for Johto: "rematch" in the data), else 10 levels up.
        rematch_boost = 0
        if getattr(self, "rematch", False) and not (self.area_key == "INDIGO_PLATEAU" and is_leader):
            rm = self.next_opponent.get("rematch")
            if not rm and self.area_key == "INDIGO_PLATEAU":
                frlg = self.FRLG_E4_REMATCH.get(str(t_data.get("name", "")).upper())
                rm = {"team": frlg[0], "levels": frlg[1]} if frlg else None
            if rm:
                t_data["team"], t_data["levels"] = list(rm["team"]), list(rm["levels"])
            else:
                rematch_boost = 10

        team_ids = t_data.get("team", [])
        opponent_team = []
        for pid in team_ids:
            raw = self.game.loader.fetch_specific(pid)
            opponent_team.append(Pokemon(raw, self.game.assets, size_mult=3.125))
        forms.mark_trainer_team(opponent_team, t_data)
        region = self.game.story_manager.get_current_region()
        t_class = t_data.get("class", "GYM_LEADER")
        if t_data.get("levels"):
            team_levels = t_data["levels"]  # exact levels from the games (Kanto's Champion)
        elif t_class == "ELITE_FOUR":
            team_levels = levels.elite_levels(region, self.progress, len(opponent_team))
        elif is_leader and (t_class in ("CHAMPION", "CHALLENGER") or self.leader.get("class") == "CHAMPION"):
            team_levels = levels.gym_team_levels(region, self.area_key, len(opponent_team), "champion")
            if t_class == "CHALLENGER":
                team_levels = [lv + 5 for lv in team_levels]  # title defenses after becoming Champion
        else:
            team_levels = levels.gym_team_levels(region, self.area_key, len(opponent_team),
                                                 levels.gym_role(t_class, is_leader))
        if rematch_boost:
            team_levels = [min(100, int(lv) + rematch_boost) for lv in team_levels]
        levels.set_team(opponent_team, team_levels, exact=bool(t_data.get("levels")))

        bg_file = self.game.story_manager.get_gym_battle_background(
            self.area_key, trainer_index=self.progress, is_leader=is_leader
        )

        battle_state = TrainerBattleState(
            self.game, opponent_team, trainer_sprite=trainer_sprite,
            trainer_class=t_data.get("class", "GYM_LEADER"), trainer_name=t_data.get("name"),
            custom_dialogue=t_data.get("dialogue", {}), rewards=t_data.get("rewards"),
            battle_type="gym", is_boss_battle=True, area_name=self.area_key,
            badge_reward=t_data.get("badge_reward"), background_image=bg_file,
            victory_flag=t_data.get("victory_flag")  # Lance: beat_elite_four, Champion: beat_champion
        )

        intro_text = random.choice(t_data.get("dialogue", {}).get("intro", ["Prepare to battle!"]))
        self.game.change_state(TrainerIntroState(self.game, trainer_sprite, intro_text, battle_state))

    def _start_gym_puzzle(self):
        """Kanto gym puzzles (src/states/gym_puzzles.py): Surge/Koga/Sabrina's must be solved before
        the leader; Blaine quizzes you before each trainer. Returns True if a puzzle took over."""
        from src.states import gym_puzzles as gp
        story = self.game.story_manager
        is_leader = (self.next_opponent == self.leader)
        if is_leader and gp.needs_puzzle(story, self.area_key):
            def done(solved):
                self.game.change_state(GymLobbyState(self.game, None))
            self.game.change_state(gp.GymPuzzleState(self.game, self.area_key,
                                                     gp.PUZZLE_GYMS[self.area_key], done))
            return True
        quiz_flag = f"gym_quiz_{self.area_key}_{self.progress}"
        if self.area_key in gp.QUIZ_GYMS and not is_leader and not story.story_flags.get(quiz_flag):
            def answered(right):
                story.story_flags[quiz_flag] = True
                if right:  # canon: a right answer means you skip that trainer
                    story.story_flags[self.prog_key] = story.story_flags.get(self.prog_key, 0) + 1
                lobby = GymLobbyState(self.game, None)
                self.game.change_state(lobby)
                if not right:
                    lobby.challenge_gym()  # wrong: battle the trainer now
            self.game.change_state(gp.GymPuzzleState(self.game, self.area_key, "quiz", answered))
            return True
        return False

    def exit_gym(self):
        from src.states.overworld import CityState
        self.game.change_state(CityState(self.game))

    def handle_events(self, events):
        pass

    def update(self):
        pass

    def draw(self):
        screen = self.game.screen
        screen.fill(BLACK)
        if self.bg:
            screen.blit(self.bg, (0, 0))
        Utils.draw_classic_panel(screen, self.bottom_rect.x, self.bottom_rect.y, self.bottom_rect.width, self.bottom_rect.height)
        left_rect_w = int(self.bottom_rect.width * 0.55)
        Utils.draw_multiline_text(screen, self.status_text, self.game.assets.fonts["s_med"], WHITE,
                                self.bottom_rect.x + left_rect_w // 2, self.bottom_rect.centery,
                                max_width=left_rect_w - 40, outline_color=BLACK)
        self.game.ui_manager.draw(screen)