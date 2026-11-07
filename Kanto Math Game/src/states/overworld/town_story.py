"""The town screen's story people: home and Mom, the professors, rivals, NPC talk and on-enter events."""

import pygame
import random
import os
from src.utils import Utils
from src.ui.dialogue import ClassicDialogueBox
from src.world import levels
from src.pokemon import forms
from src.pokemon.data import Pokemon
from src.states.overworld.common import (
    _cast_trainer, _fill_names, _region_starter_id, _resolve_lines, _run_story_event, _trainer_sprite,
    rival_image
)


class TownStory:
    """Part of CityState (town.py): its story people."""

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

    def visit_rival_mom(self):
        self.visit_mom(is_neighbor=True)

    def visit_silver_mom(self):
        self.visit_mom(is_neighbor=True, is_silver_mom=True)

    def visit_mom(self, is_neighbor=False, is_silver_mom=False):
        self.game.music.play("home")
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
        self.game.music.play("oak")
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
            story.story_flags["received_pokedex_kanto"] = True  # the National Dex covers Kanto
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
        elif (story.get_current_region() == "KANTO" and not story.story_flags.get("received_starter_kanto")
              and (region == "KANTO" or story.story_flags.get("moved_to_kanto"))):
            # FireRed/LeafGreen: Oak stops you at the edge of town and takes you to his lab.
            msg = ["Professor Oak: Hey! Wait! Don't go out there!",
                   "Wild Pokémon live in the tall grass. You need a Pokémon of your own to stay safe.",
                   "Come with me to my lab!",
                   f"Professor Oak: {self.game.rival_name} is already here. There are three Pokémon on the table...",
                   "Go on, choose one!"]
            story.story_flags["kanto_parcel_era"] = True  # (see StoryManager._migrate_kanto_start)
            from src.states.menus import StarterSelectionState

            def oak_lab_starters():
                self.start_npc_exit(lambda: self.game.change_state(
                    StarterSelectionState(self.game, starter_ids=[1, 4, 7], region="KANTO")))
            callback = oak_lab_starters
        elif (story.get_current_region() == "KANTO" and story.story_flags.get("defeated_rival_kanto")
              and not story.story_flags.get("received_pokedex_kanto")):
            if story.inventory.get("OAKS_PARCEL", 0) > 0:  # Oak's Parcel: the Pokedex and Poke Balls
                story.inventory.pop("OAKS_PARCEL", None)
                story.balls_left = getattr(story, "balls_left", 0) + 5
                story.story_flags["received_pokedex_kanto"] = True
                msg = ["Professor Oak: Oh, my order from the Viridian Mart! Thank you!",
                       "Now, I have a favour to ask. This is a Pokédex, a high-tech encyclopedia.",
                       "It records every Pokémon you see and catch. A complete guide to every Pokémon is my dream!",
                       f"{self.game.player_name} received a POKéDEX!",
                       "And take these. You'll need them to catch Pokémon. You received 5 Poké Balls!",
                       "Head north past Viridian City. Your adventure starts now!"]
            else:
                msg = ["Professor Oak: Your Pokémon looks happy with you!",
                       "If you're passing through Viridian City, the Poké Mart there has a parcel for me."]
            callback = self.end_npc_interaction
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
            rival_name = getattr(self.game, "rival_name", "SILVER")
            rival_sprite = self.game.assets.get_trainer_image("silver.png")
            if not rival_sprite:
                rival_sprite = self.game.assets.get_trainer_image("rival.png")
            bg_name = "battle_elmlab.png"
            intro_text = "...You think you're strong?"
        else:
            rival_name = getattr(self.game, "rival_name", "BLUE")
            rival_sprite = (rival_image(self.game, getattr(self.game, "rival_character", "blue"))
                            or self.game.assets.get_trainer_image("rival.png"))
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

    def end_npc_interaction(self):
        """Cleans up NPC states. Now triggers slide-out before fully closing."""
        if self.npc_active and not self.is_npc_exiting:
            self.start_npc_exit()
            return

        self.npc_active = False
        self.is_npc_exiting = False
        self.npc_exit_callback = None
        self.npc_sprite = None
        if self.current_npc in ("mom", "silver_mom", "professor_oak"):
            self.game.music.play("town")  # back to the town's own music
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
        elif on_enter.get("type") == "event":
            met = True
        if met and on_enter.get("type") == "event":  # a story scene on arrival (Norman and Wally)
            self.story_event(on_enter["event"])
            return True
        if not (met and on_enter.get("type") == "trainer_battle"):
            return False

        t_info = _cast_trainer(self.game, dict(on_enter["trainer"]))
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
        if levels.postgame_trainers(self.game, self.area_key) and not starter_battle:
            levels.set_team(opponent_team, levels.trainer_team_levels(
                self.game, self.area_key, len(opponent_team), boss=True))  # post-game cap; legendaries stay 70
        elif t_info.get("levels") and starter_battle:
            levels.set_team(opponent_team, list(t_info["levels"]), exact=True)
        elif t_info.get("levels"):  # exact levels from the games, lifted if the team has outgrown them
            levels.set_team(opponent_team, levels.follow_team(self.game, t_info["levels"]), exact=True)
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
        # Jordan (11-06): an ambush on arrival says so first, here in town, before the battle screen.
        name = _fill_names(self.game, t_info.get("name")) or "A trainer"
        where = self.area_data.get("route_name") or self.area_key.replace("_", " ").title()
        before = _resolve_lines(self.game, on_enter.get("arrival_lines") or [
            f"As you arrive in {where}, someone calls out to you...", f"It's {name}! {name} wants to battle!"])
        self.show_message(before, callback=lambda: self.game.change_state(
            TrainerIntroState(self.game, sprite, intro_text, battle_state)))
        return True

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
                     "\"Kanto's new Champion! The Orange Islands have their own League, the Orange Crew.",
                     "If you'd like to start a new journey, I'll have a partner waiting for you.\"",
                     "The S.S. Anne sails from Vermilion City to the Orange Islands whenever you're ready."]

    ISLAND_CHAMPION = ["Drake: The Winner's Trophy is yours. You're the Orange League Champion!",
                       "Your name will be carved into the wall of Pummelo Stadium.",
                       "The ships still sail between the islands. Come back any time for a rematch!"]

    def _offer_move(self, region, phone):
        """Mom uses the championship prize money for a new home and asks where to move."""
        from src.states.overworld.town import CityState
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
