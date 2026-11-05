"""The route screen (PlayState): a route, cave or other wild area. Its parts are mixins:
route_menu (buttons and conditions), route_encounters (wild and trainer battles, bosses, raids),
route_actions (fishing, headbutt, diving, berries and route NPCs) and route_catch (the catch round)."""

import pygame
import random
import math
from src.states.base import GameState
from src.utils import Utils
from src.ui.dialogue import ClassicDialogueBox
from src.ui.widgets import Button
from src.ui.panels import CommandButton
from src.ui import theme
from src.world.boss import BossManager
from src.world import hoenn
from src.world import black_fog
from src.pokemon import catching
from src.world import regional_forms
from src.config import WHITE, BLACK, GREEN, BLUE, GOLD, RED, PURPLE, GRAY, FPS
from src.states.overworld.common import HUD_INFO_Y, _draw_season_hud
from src.states.overworld.route_actions import RouteActions
from src.states.overworld.route_catch import RouteCatch
from src.states.overworld.route_encounters import RouteEncounters
from src.states.overworld.route_menu import RouteMenu


# [REF-0029: Overworld & Play Logic]
class PlayState(RouteMenu, RouteEncounters, RouteActions, RouteCatch, GameState):
    # One Poke Ball count for the whole game: the story's. Routes used to keep their own copy,
    # and an old copy coming back (a revisited route, after a battle) erased balls you'd bought.
    @property
    def balls_left(self):
        return self.game.story_manager.balls_left

    @balls_left.setter
    def balls_left(self, value):
        self.game.story_manager.balls_left = value

    def __new__(cls, game=None, restore_data=None, classic=False):
        # A route dungeon (assets/dungeon_routes.json) is walked on a map instead: PlayState(game)
        # hands back a DungeonState there, or the walk going on when a battle comes back to it
        # (src/states/overworld/dungeon.py). classic=True: always this screen.
        if cls is PlayState and game is not None and not classic:
            from src.states.overworld.dungeon import dungeon_for
            state = dungeon_for(game, restore_data)
            if state is not None:
                return state
        return super().__new__(cls)

    def __init__(self, game, restore_data=None, classic=False):
        from src.states.overworld.area_transition import _collapse_hud
        super().__init__(game)
        if hasattr(game.story_manager, "sync_rival"):
            game.story_manager.sync_rival()  # this region's rival (one per region per save)
        hoenn.apply_version(game)
        self.area_data = game.story_manager.get_current_area_data()
        self._inject_regional_data()
        # A banished Black Fog may gather here again (10%, once a day: src/world/black_fog.py).
        self.fog_returned = black_fog.maybe_return(game.story_manager, game.story_manager.current_area_key,
                                                   self.area_data)

        self.game.story_manager.sync_badges()

        pygame.event.clear()

        main_rect = Utils.get_full_dialogue_rect(self.game)
        self.dialogue_box = ClassicDialogueBox(
            main_rect,
            [self.game.assets.get_text(
                f"welcome_{self.game.story_manager.get_current_region().lower()}",
                default=f"Welcome to {self.game.story_manager.get_current_region().title()}!")],
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
        story = self.game.story_manager
        if restore_data is None and getattr(story, "repel_routes", 0) > 0 and self.min_rounds:
            # A Repel keeps wild Pokemon away: this route can be left without battling.
            self.min_rounds = 0
            story.repel_routes -= 1

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
        self.route_bg = self._load_route_background()

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

        if self.game.story_manager.can_fly():
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

        self.btn_flee = CommandButton(
            rect=(game.width - 200, game.height // 2 - 40, 180, 70),
            text="FLEE",
            font=game.assets.fonts["button"],
            callback=self.action_flee,
            bg_color=theme.RUN,
            visible=False,
            autosize=False,
        )

        self.btn_yes = CommandButton((0, 0, 0, 0), "YES", game.assets.fonts["button"],
                                     self.boss_catch_yes, bg_color=theme.POKEMON,
                                     visible=False, autosize=False)
        self.btn_no = CommandButton((0, 0, 0, 0), "NO", game.assets.fonts["button"],
                                    self.boss_catch_no, bg_color=theme.FIGHT,
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
        from src.states.region_map import RegionMapState
        self.game.change_state(RegionMapState(self.game, self))

    def _open_fly(self):
        from src.states.region_map import RegionMapState
        self.game.change_state(RegionMapState(self.game, self, fly=True))

    def _open_pokenav(self):
        from src.states.systems import PokeNavState
        self.game.change_state(PokeNavState(self.game, self))

    def _load_route_background(self):
        """The route's own picture (Pokemon Journeys' maps, framed on its tall grass), else its
        battle background; None leaves the old starfield."""
        key = self.game.story_manager.current_area_key
        zone = self._zone()
        img = zone and self.game.assets.get_journeys_background("routes", f"{key}_{zone['key']}")
        img = img or self.game.assets.get_journeys_background("routes", key)
        if img is None:
            name = self._get_battle_background_for_area()
            img = self.game.assets.get_background(name) if name else None
        if img is None:
            return None
        box_top = Utils.get_full_dialogue_rect(self.game).top
        return pygame.transform.scale(img, (self.game.width, box_top))

    ROUTE_GROUND = {"cave": (128, 108, 86), "dungeon": (128, 108, 86), "water": (72, 132, 206),
                    "surf": (72, 132, 206), "ocean": (72, 132, 206)}

    def _draw_ground(self, screen, x, y, w):
        """The patch a wild Pokemon stands on: tall grass on a route, rock in a cave, a ripple on
        the water (like the battle screen's bases)."""
        color = self.ROUTE_GROUND.get(self.area_data.get("battle_type", ""), (70, 150, 64))
        patch = pygame.Surface((w, w // 4), pygame.SRCALPHA)
        pygame.draw.ellipse(patch, (*color, 210), patch.get_rect())
        pygame.draw.ellipse(patch, (*[min(255, c + 60) for c in color], 230), patch.get_rect(), 4)
        screen.blit(patch, patch.get_rect(center=(int(x), int(y))))

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
            menu = getattr(self, "route_action_menu", None)
            if menu is not None and menu not in self.game.ui_manager.elements:
                self.game.ui_manager.add_element(menu)
            if getattr(self, "route_popup", None):
                group, self.route_popup = self.route_popup, None
                self.toggle_route_popup(group)

        pygame.event.clear()

        visited_flag = f"visited_{self.game.story_manager.current_area_key}"
        if not self.game.story_manager.story_flags.get(visited_flag, False):
            self.game.story_manager.story_flags[visited_flag] = True

        if self._starter_return():
            return

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

        if self.route_starter_event():
            return

        if self.check_roaming_encounter():
            return

        num_johto = len(self.game.story_manager.badges.get("JOHTO", []))
        if (self.game.story_manager.inventory.get("MYSTERY_EGG", 0) > 0
            and num_johto >= 2
            and not self.game.story_manager.story_flags.get("egg_hatched")):
            self.trigger_egg_hatch()
            return

        gauntlet_areas = ["INDIGO_PLATEAU", "KANTO_ROUTE_24"]  # (Nugget Bridge is Route 24, FRLG)
        current_area = self.game.story_manager.current_area_key
        is_gauntlet_area = current_area in gauntlet_areas
        if is_gauntlet_area and self.rounds_completed == 0 and self.fresh_entry:
            self.create_checkpoint()

        events = self.area_data.get("on_enter_event")
        for on_enter in (events if isinstance(events, list) else [events] if events else []):
            if on_enter.get("type") != "trainer_battle":  # (one list can hold several story battles)
                continue
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

    def _draw_season_hud(self, screen, x, y):
        _draw_season_hud(self.game, screen, self.game.story_manager.current_area_key, x, y)

    def _hud_shade(self, width):
        """A soft dark band along the top so the ball count and goal read on a bright route."""
        if getattr(self, "_shade", None) is None or self._shade.get_width() != width:
            self._shade = pygame.Surface((width, 120), pygame.SRCALPHA)
            for yy in range(120):
                pygame.draw.line(self._shade, (0, 0, 0, int(110 * (1 - yy / 120))), (0, yy), (width, yy))
        return self._shade

    def _bar_text(self, screen, bar, text, color):
        """Feedback ("Gotcha!", the right answer) in the bottom bar, centred: dark text, or a
        light colour (gold, white) with a dark edge so it reads on the white box."""
        from src.ui.dialogue import wrap_text
        font = self.game.assets.fonts["dialog"]
        rows = [r for line in str(text).split("\n") for r in wrap_text(line, font, bar.width - 120)]
        lh = int(font.get_linesize() * 1.15)
        top = bar.centery - lh * len(rows) // 2 + lh // 2
        for k, row in enumerate(rows):
            if sum(color[:3]) > 450:
                Utils.draw_text_outline(screen, row, font, color, bar.centerx, top + k * lh,
                                        outline_color=theme.TEXTBOX_FRAME, thickness=3)
            else:
                theme.shadow_text(screen, row, font, bar.centerx, top + k * lh, color=color, align="center")

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
            if getattr(self, "route_popup", None) and any(
                    e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and not self.route_popup_rect.collidepoint(e.pos)
                    for e in events):
                self.close_route_popup()
            return

        for event in events:
            if self.dialogue_box.visible:
                self.dialogue_box.handle_event(event)
                if not self.catch_selection_active:
                    continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                ball_rect = getattr(self, "ball_hud_rect", None)
                if ball_rect is not None and ball_rect.collidepoint(event.pos):  # tap the ball count: switch ball
                    catching.cycle(self.game.story_manager)
                    continue
                rect = getattr(self, "speak_rect", None)
                if rect is not None and rect.collidepoint(event.pos) and not self.catch_selection_active:
                    from src.core import speech
                    speech.say(speech.math_words(self.problem_str))
                    continue
                if not self.ball_active and self.input_delay == 0 and self.pause_timer == 0 and catching.total_balls(self.game.story_manager) > 0:
                    if self.catch_selection_active:
                        self.check_selection(event.pos)
                    elif not self.dialogue_box.visible:
                        self.check_answer(event.pos)

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

    def _open_pokedex(self):
        from src.states.systems import PokedexState
        self.game.change_state(PokedexState(self.game, self))

    def _open_party(self):
        from src.states.systems import PokemonPartyMenuState
        self.game.change_state(PokemonPartyMenuState(self.game, self, context="normal"))

    def update(self):
        self.boss_manager.update()
        self._sync_route_menu()

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

        if catching.total_balls(self.game.story_manager) <= 0 and not self.ball_active and self.pause_timer == 0:
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

    def draw(self):
        screen = self.game.screen
        width, height = self.game.width, self.game.height
        offset_x, offset_y = 0, 0
        if self.scr_shake_timer > 0:
            offset_x, offset_y = random.randint(-15, 15), random.randint(-15, 15)

        caught_ids = {v['id'] for v in self.game.data.data.get("pokedex", {}).values()}

        if self.boss_manager.draw(screen, width, height, offset_x, offset_y):
            return

        bar = Utils.get_full_dialogue_rect(self.game)
        if not self.boss_manager.in_boss_mode:
            screen.fill(BLACK)
            if self.route_bg:  # the route itself (redesign); the HUD gets a soft shade to read on
                screen.blit(self.route_bg, (offset_x, offset_y))
                screen.blit(self._hud_shade(width), (0, 0))

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
            for s in (self.stars if not self.route_bg else []):
                s[1] += s[2] * spd_base * warp_speed
                if s[1] > height:
                    s[1], s[0] = 0, random.randint(0, width)
                pygame.draw.circle(
                    screen, (150, 150, 150), (s[0] + offset_x, s[1] + offset_y), 1
                )

        if not self.boss_manager.in_boss_mode:
            theme.draw_textbox(screen, bar)  # the bottom bar: answers, feedback, the route menu's words
        story = self.game.story_manager
        ball = catching.selected(story)
        lbl_text = f"{catching.label(ball).title()}: "  # the ball you'll throw; tap to switch
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
        count_x = 20 + lbl_width + 5 + offset_x + self.game.assets.ui_ball.get_width() + 5
        count = f"x{catching.owned(story, ball)}"
        if len(catching.balls_owned(story)) > 1:
            count += "  (tap to switch)"
        Utils.draw_text_outline(screen, count, self.game.assets.fonts["small"], WHITE, count_x, 20 + offset_y,
                                align="left")
        self.ball_hud_rect = pygame.Rect(10, 5, count_x + self.game.assets.fonts["small"].size(count)[0], 40)

        self._draw_season_hud(screen, 20 + offset_x, HUD_INFO_Y + offset_y)

        pool_name = self.area_data.get("wild_pool_percentages")
        if pool_name:
            wild_pool = self.game.loader.area_data.get(pool_name, {})
            if wild_pool:
                all_caught = True
                for pid_str in wild_pool.keys():
                    pid = int(pid_str)
                    if not regional_forms.counts_for_area(self.game, pid):  # (other regions' forms don't count)
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

        if self.is_progression_paused and getattr(self, "route_popup_rect", None):  # the pop-up's card
            theme.card(screen, self.route_popup_rect)
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
                if not should_hide and not self.boss_manager.in_boss_mode and self.runaway_x_offsets[i] == 0:
                    ink = p_info.image.get_bounding_rect()  # the sprite without its empty margin
                    feet = self.sprite_y - p_info.image.get_height() / 2 + ink.bottom
                    self._draw_ground(screen, cx + offset_x, feet - 4, max(120, int(ink.width * 1.3)))
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
                # The answer under each Pokemon, in the bottom bar: the battle's white answer card.
                txt = str(self.options[i])
                font = self.game.assets.fonts["num"]
                if len(txt) > 3:
                    font = self.game.assets.fonts["s_med"]
                btn_w = max(220, font.size(txt)[0] + 60)
                btn_rect = pygame.Rect(0, 0, btn_w, bar.height - 56)
                btn_rect.center = (cx, bar.centery - 2)
                self.answer_btn_rects[i] = btn_rect
                hover = btn_rect.collidepoint(pygame.mouse.get_pos())
                pygame.draw.rect(screen, theme.TEXTBOX_FRAME, btn_rect.move(0, 5), border_radius=14)
                pygame.draw.rect(screen, (236, 244, 255) if hover else WHITE, btn_rect, border_radius=14)
                pygame.draw.rect(screen, theme.TEXTBOX_FRAME, btn_rect, 4, border_radius=14)
                theme.shadow_text(screen, txt, font, btn_rect.centerx, btn_rect.centery, align="center")

        if self.game.debug_mode:
            for r in self.answer_btn_rects:
                pygame.draw.rect(screen, (255, 0, 255), r, 2)

        if self.pause_timer == 0 and not self.is_progression_paused and not self.catch_selection_active:
            # The question on a card at the top (the battle's text box style), the time left
            # as a bar along its bottom.
            qfont = self.game.assets.fonts["big"]
            tw = qfont.size(self.problem_str)[0]
            card = pygame.Rect(0, 0, max(360, tw + 120), 100)
            card.center = (width // 2, 92)
            theme.draw_textbox(screen, card)
            theme.shadow_text(screen, self.problem_str, qfont, card.centerx, card.centery - 4, align="center")
            from src.core import speech
            if speech.available():
                self.speak_rect = pygame.Rect(card.right + 12, card.centery - 26, 52, 52)
                speech.draw_speaker(screen, self.speak_rect)

            if self.question_timer > 0:
                ratio = max(0, min(1, self.question_timer / (30 * FPS)))
                track = pygame.Rect(card.x + 24, card.bottom - 20, card.w - 48, 8)
                pygame.draw.rect(screen, (210, 214, 224), track, border_radius=4)
                color = theme.HP_GREEN if ratio > 0.5 else theme.HP_YELLOW if ratio > 0.2 else theme.HP_RED
                pygame.draw.rect(screen, color, (track.x, track.y, int(track.w * ratio), track.h), border_radius=4)

        if self.flash_timer > 0 and not (self.pause_timer > 0 and self.feedback_text):
            self._bar_text(screen, bar, self.flash_msg, GOLD)
        if self.pause_timer > 0:
            self._bar_text(screen, bar, self.feedback_text, self.feedback_color)

        if self.ball_active:
            screen.blit(
                self.current_ball_img, (self.ball_pos[0] - 42, self.ball_pos[1] - 42)
            )

        if self.is_progression_paused:
            if self.rounds_completed == 0:
                route_name = self.area_data.get(
                    "route_name",
                    self.game.story_manager.current_area_key.replace("_", " ").title(),
                )
                msg = f"Entered {route_name}"
            else:
                msg = self.game.assets.get_text("explored_area")
            if not self.dialogue_box.visible and getattr(self, "route_action_menu", None) is None:
                theme.draw_textbox(screen, bar)
                font = self.game.assets.fonts["dialog"]
                theme.shadow_text(screen, msg, font, bar.x + 40, bar.y + 34)
                theme.shadow_text(screen, self.game.assets.get_text("whats_next"), font, bar.x + 40,
                                  bar.y + 34 + int(font.get_linesize() * 1.25))
