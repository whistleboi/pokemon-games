"""The town screen (CityState). Its parts are mixins: town_menu (EXPLORE / TRAVEL), town_story
(home, the professors, rivals, NPC talk), town_kanto (Kanto's townsfolk and the fossil labs) and
town_johto (Johto's townsfolk and the Ruins of Alph)."""

import pygame
import random
from src.states.base import GameState
from src.utils import Utils
from src.ui.dialogue import ClassicDialogueBox
from src.ui.widgets import Button
from src.ui.panels import CityActionMenu
from src.world import seasons
from src.world import hoenn
from src.world import league_redo
from src.world import levels
from src.pokemon import forms
from src.pokemon.data import Pokemon
from src.config import WHITE, BLACK, GREEN, BLUE, GOLD, RED, PURPLE, GRAY
from src.states.overworld.common import _draw_season_hud
from src.states.overworld.town_johto import JohtoTown
from src.states.overworld.town_kanto import KantoTown
from src.states.overworld.town_menu import TownMenu
from src.states.overworld.town_story import TownStory


# [REF-0036: City Hub State]
class CityState(TownMenu, TownStory, KantoTown, JohtoTown, GameState):
    def __new__(cls, game, *args, **kwargs):
        """A town with a walkable map (walk_town.py, Jordan 11-06) is walked; the others are this menu."""
        if cls is CityState:
            from src.states.overworld import walk_town
            if walk_town.available(game, game.story_manager.current_area_key):
                return object.__new__(walk_town.WalkTownState)
        return object.__new__(cls)

    def __init__(self, game):
        from src.states.overworld.area_transition import _collapse_hud
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
        from src.states.region_map import RegionMapState
        self.game.change_state(RegionMapState(self.game, self))

    def _open_fly(self):
        from src.states.region_map import RegionMapState
        self.game.change_state(RegionMapState(self.game, self, fly=True))

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
        # One look for a region's towns (Jordan): Pokemon Journeys' maps where it has the town.
        img = self.game.assets.get_journeys_background("towns", self.area_key)
        if img:
            return img
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
        from src.states.overworld.gym_lobby import GymLobbyState
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

    def save_game(self):
        from src.states.menus import SaveState
        self.game.change_state(SaveState(self.game, self))

    def start(self):
        from src.states.overworld.area_transition import autosave
        if hoenn.needs_choice(self.game.story_manager):
            from src.states.hoenn import HoennVersionState
            self.game.change_state(HoennVersionState(self.game, lambda: CityState(self.game)))
            return
        if self.game.story_manager.needs_rival_choice():  # this region's rival, picked and named
            from src.states.menus import RivalSelectionState
            self.game.change_state(RivalSelectionState(
                self.game, region=self.game.story_manager.get_current_region(),
                on_done=lambda: self.game.change_state(CityState(self.game))))
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
        paid = story.catch_milestones()  # a catch milestone reached by battle, evolution or a gift
        from src.pokemon import zpower
        paid += zpower.give_key_items(story)  # the Z-Ring (Alola's first trial), the Tera Orb (Paldea)
        if paid:
            self.show_message(paid)
            return
        call = league_redo.take_call(story, region)  # back in the first region won: the League Redo
        if call:
            self.show_message(call)
            return
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
            # Save the new title now: the move picker comes next, and a child who closes the
            # game there used to lose the Champion win (the newest save was from before the League).
            autosave(self.game)
            if story.get_region_start(region).get("travel_only"):
                self.show_message(link_lines + self.ISLAND_CHAMPION)  # a trip, not a new home: no move offer
                return
            road = self.ROAD_OPEN.get(region)
            if road:  # Kanto <-> Johto: the road is open, go now or later (Mom's offer follows)
                story.inventory["SS_TICKET"] = 1
                road = road + ["You received an S.S. TICKET!",
                               "The S.S. Aqua sails between Vermilion City and Olivine City."]
                if region == "KANTO" and "ORANGE" not in story.visited_regions():
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
        _draw_season_hud(self.game, screen, self.area_key, 20)
