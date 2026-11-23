"""The town screen's Johto townsfolk (Kurt, the Radio Tower, Mr. Pokemon...) and the Ruins of Alph."""

import pygame
import os
from src.utils import Utils
from src.ui.dialogue import ClassicDialogueBox
from src.world import levels
from src.pokemon import forms
from src.pokemon.data import Pokemon
from src.world import story_events


class JohtoTown:
    """Part of CityState (town.py): Johto's townsfolk (Kurt, the Radio Tower, Mr. Pokemon...) and the Ruins of Alph."""

    # The Ruins of Alph's chambers (HeartGold/SoulSilver): each has a stone panel to put back together.
    ALPH_DONE = {"kabuto": "The wall slides away... Unown drift out of the chamber!",
                 "omanyte": "The floor rumbles... the Omanyte panel glows, and Unown pour out!",
                 "aerodactyl": "A hidden door opens behind the Aerodactyl panel. More Unown appear!",
                 "hooh": "The Ho-Oh panel shines like a rainbow... Unown fill the chamber!"}

    def solve_alph_panel(self, panel):
        from src.minigames.tiles import AlphPuzzle, flag

        def done(won):
            self.game.change_state(self)
            if won:
                self.game.story_manager.story_flags[flag(panel)] = True
                rm = ((getattr(self, "town_map", None) or {}).get("rooms") or {}).get(getattr(self, "room", None) or "") or {}
                drop = rm.get("drop")
                if drop and drop.get("room") in (self.town_map.get("rooms") or {}):   # (walked in, 11-22: the floor gives way under
                    self._go(drop["room"], "DROP")                                     #  you, into the chamber's writing room, HGSS)
                    self.player = self.anim_from = self.partner = self.partner_from = tuple(drop["at"])
                    self.facing = (0, 1)
                    self.anim = 0
                    self._remember()
                    said = ["You put the panel back together!"] + list(drop.get("lines") or [])
                    inv = self.game.story_manager.inventory
                    if not inv.get("UNOWN_REPORT"):   # (the first puzzle: a researcher hands you the Unown Report, HGSS)
                        inv["UNOWN_REPORT"] = 1
                        said += ["A researcher hurries over: You solved it! The Unown are coming out!",
                                 "Here, keep a record of every one you find in this Unown Report!", "You got the UNOWN REPORT!"]
                    self.show_message(said)
                    return
                self.show_message(["You put the panel back together!", self.ALPH_DONE.get(panel, "")])

        self.clear_hover_menu()
        self.game.change_state(AlphPuzzle(self.game, done, panel=panel, background=self.load_area_background()))

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
                if self.game.story_manager.sinjoh_dragons_received() < 3:
                    # The Sinjoh Ruins open for Arceus (from Sinnoh's Hall of Origin), as in HGSS; the
                    # Unown open them again for a second and third dragon.
                    msg += ["One more thing... the carvings say the Unown gather around ARCEUS.",
                            "It's said to wait in the Hall of Origin, far away in Sinnoh.",
                            "If you ever bring ARCEUS here, the Unown may show you something amazing!"]
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
            story = self.game.story_manager
            if 0 < story.sinjoh_dragons_received() < 3:  # the Unown re-open the Sinjoh Ruins
                step = next(n for n in story.SINJOH_UNOWN_STEPS if caught_count < n) if caught_count < 28 else 28
                msg.append(f"The Unown want to take ARCEUS back to those ruins... at {step} forms, I think they will!")

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
        from src.states.overworld.route import PlayState
        self.clear_hover_menu()
        from src.states.overworld import PlayState
        ruins_state = PlayState(self.game)
        self.game.change_state(ruins_state)
        ruins_state.action_search_pokemon()

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

        story = self.game.story_manager
        flags = story.story_flags
        if flags.get("kurt_has_gs_ball"):   # (an older save left it with him overnight: he gives it straight back now)
            flags.pop("kurt_has_gs_ball", None); flags.pop("kurt_gs_ball_day", None)
            flags["kurt_examined_gs_ball"] = True
            story.inventory["GS_BALL"] = story.inventory.get("GS_BALL", 0) + 1
            msg = ["Kurt: Ah, there you are. I've studied that GS Ball.",
                   "Kurt: It can't be opened, but it's calling to the shrine in Ilex Forest. Take it there and see what happens.",
                   "You got the GS BALL back!"]
        elif story.inventory.get("GS_BALL", 0) > 0 and not flags.get("kurt_examined_gs_ball"):   # (Crystal keeps it a day; ours gives it back at once)
            flags["kurt_examined_gs_ball"] = True
            msg = ["Kurt: What's that? A GS Ball? I've never seen one like it!",
                   "Kurt: Hmm... It can't be opened, but it's calling to the shrine in Ilex Forest. Take it there and see what happens.",
                   "Kurt handed the GS BALL back."]
        elif not flags.get("slowpoke_well_cleared"):
            flags["kurt_went_to_well"] = True   # (HGSS: Kurt sees off the Grunt guarding the Well: the way in is open; 11-22)
            msg = self.game.assets.get_text("kurt_intro")
        elif not flags.get("got_fast_ball_kurt"):   # (once: his thanks for the Well, and the Fast Ball he made; HGSS)
            flags["got_fast_ball_kurt"] = True
            story.balls_left += 5
            story.inventory["FAST_BALL"] = story.inventory.get("FAST_BALL", 0) + 1
            msg = list(self.game.assets.get_text("kurt_reward")) + [
                "Kurt: And take this. It's a Fast Ball I made from a White Apricorn.",
                "Bring me Apricorns from the trees around Johto, and I'll make you balls from them!"]
        else:   # (Apricorns into his balls, on the spot: Jordan 11-15, simplified)
            from src.pokemon.items import APRICORN_BALL
            made = []
            for apr, ball in APRICORN_BALL.items():
                n = story.inventory.pop(apr, 0)
                if n:
                    story.inventory[ball] = story.inventory.get(ball, 0) + n
                    made.append(f"{n} {ball.replace('_', ' ').title()}{'s' if n > 1 else ''}")
            msg = (["Kurt: Apricorns, eh? Let's see what we've got...", "Kurt: There! " + ", ".join(made) + ". Use them well!"] if made else
                   ["Kurt: Bring me Apricorns and I'll make them into balls.", "Each colour of Apricorn makes a different kind of ball!"])
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
        from src.states.overworld.area_transition import AreaTransitionState
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
                
                # The tower's own levels (Grok's Johto walk: they kept their base levels, L5 / L20 / L5).
                levels.set_team(opponent_team, levels.trainer_team_levels(self.game, "RADIO_TOWER", len(opponent_team), True))

                # Winning takes you into the tower; losing is an ordinary loss (you stay outside).
                class RadioTowerGateBattle(TrainerBattleState):
                    def exit_battle(self):
                        if not self.player_won:
                            return super().exit_battle()
                        from src.states.overworld import AreaTransitionState
                        self.game.story_manager.story_flags["radio_takeover_started"] = True   # (the Rockets inside now stand on their floors)
                        self.game.change_state(AreaTransitionState(self.game, "RADIO_TOWER"))

                battle_state = RadioTowerGateBattle(
                    self.game, opponent_team, trainer_sprite=self.npc_sprite,
                    trainer_class="ROCKET", trainer_name="GRUNT", 
                    battle_type="indoor", area_name=self.area_key, is_boss_battle=True
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
                "Professor Oak: Hm? So you're the trainer Elm sent! I'm Oak. I was visiting my old friend here.",
                "Professor Oak: You and your Pokemon look like a fine team. Here, take this Pokedex: record every Pokemon you meet!",
                "You received the POKEDEX!",
                "Professor Oak: I'll give you my number too. Now I must hurry: I'm on the radio in Goldenrod soon!",
                "It's safe in your BAG. Hurry back to the lab!"
            ]
            flags["met_mr_pokemon"] = True
            flags["received_pokedex_johto"] = True   # (HGSS: Oak is at Mr. Pokemon's, and gives you the Pokedex)
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
        story = self.game.story_manager
        if story.story_flags.get("ampharos_cured") or story.inventory.get("SECRET_POTION", 0) > 0:   # (one potion, for Amphy: not one each visit; 11-22)
            return self.show_message(["Pharmacist: That Secret Potion works wonders. I hope the Lighthouse's Ampharos is well!"])
        self.show_message(self.game.assets.get_text("pharmacist_reward"))
        story.inventory["SECRET_POTION"] = 1

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
