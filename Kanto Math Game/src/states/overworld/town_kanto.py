"""The town screen's Kanto townsfolk (Mr. Fuji, Silph Co., Bill, the Dojo...) and the fossil labs."""

import pygame
import random
import os
from src.utils import Utils
from src.ui.dialogue import ClassicDialogueBox
from src.pokemon.data import Pokemon


class KantoTown:
    """Part of CityState (town.py): Kanto's townsfolk (Mr. Fuji, Silph Co., Bill, the Dojo...) and the fossil labs."""

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

    def visit_silph_employee(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "silph_employee"
        self.npc_slide_offset = 400
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("supernerd.png")

        story = self.game.story_manager
        # The Up-Grade isn't given in Kanto any more: it's sold only at the Veilstone Department Store
        # in Sinnoh (Jordan, 10-23). The employee points the way.
        if story.story_flags.get("silph_co_cleared") and "JOHTO" in story.visited_regions():
            msg = ["You saved us! Silph's UP-GRADE, a part that makes Porygon even better, is made in Sinnoh now.",
                   "You can buy one at the Veilstone Department Store there."]
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
        porygon = Pokemon(raw, self.game.assets, size_mult=2.5).max_ivs()  # a gift: perfect IVs
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
            pokemon = Pokemon(raw, self.game.assets, size_mult=2.5).max_ivs()  # a gift: perfect IVs
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

        if not self.game.story_manager.has_badge("BOULDER"):
            msgs.append("Welcome! Please return after you have defeated Brock.")
        else:
            msgs.append("Welcome to the Pewter Museum of Science!")
            msgs.append("Fossils of ancient Pokémon are often found in Mt. Moon, east of here.")
            has_amber = flags.get("received_old_amber")
            if not has_amber and self.game.story_manager.has_badge("CASCADE"):
                # FRLG: a scientist behind the museum (past a Cut tree) hands over the Old Amber.
                msgs.append("You Cut through the tree behind the museum and find a scientist at the back door.")
                msgs.append("Scientist: This amber has something inside! Take it to the Pokémon Lab on Cinnabar Island.")
                msgs.append("You received the Old Amber!")
                inv["OLD_AMBER"] = inv.get("OLD_AMBER", 0) + 1
                flags["received_old_amber"] = True
            elif not has_amber:
                msgs.append("A small tree blocks the path behind the museum. Someone with Cut could get past it.")

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

    def _miguels_fossil(self):
        """Cinnabar's lab: the fossil Super Nerd Miguel kept in Mt. Moon, sent on for you, so every
        Kanto fossil can be had (Jordan). Older saves had a museum fossil instead."""
        flags = self.game.story_manager.story_flags
        if self.area_key != "CINNABAR_ISLAND" or flags.get("received_museum_fossil_2"):
            return []
        if flags.get("took_dome_fossil"):
            other = "HELIX_FOSSIL"
        elif flags.get("took_helix_fossil"):
            other = "DOME_FOSSIL"
        elif flags.get("received_museum_fossil"):
            first = flags.get("museum_fossil_choice", "HELIX_FOSSIL")
            other = "DOME_FOSSIL" if first == "HELIX_FOSSIL" else "HELIX_FOSSIL"
        else:
            return []
        inv = self.game.story_manager.inventory
        inv[other] = inv.get(other, 0) + 1
        flags["received_museum_fossil_2"] = True
        name = other.replace("_", " ").title()
        return [f"A Super Nerd from Mt. Moon sent us his {name}. He says you should have it!",
                f"You received the {name}!"]

    def visit_stoneman(self):
        self.clear_hover_menu()
        self.npc_active = True
        self.current_npc = "stoneman"
        self.action_menu.set_visibility(False)
        self.npc_sprite = self.game.assets.get_trainer_image("ruinmaniac.png")

        msgs = ["Welcome to the fossil lab!", "We can bring ancient Pokémon back to life."]
        msgs += self._miguels_fossil()
        items, target_id = self._next_fossil_revival()

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

        # Nugget Bridge is Route 24 (FRLG); older saves that cleared the old bridge on Route 25 count too.
        def cleared(area):
            pool = self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(area, {}).get("trainer_pool", [])
            return len(pool) > 0 and len(story.defeated_trainers.get(area, set())) >= len(pool)
        bridge_clear = cleared("KANTO_ROUTE_24") or flags.get("nugget_bridge_cleared_old") or flags.get("nugget_bridge_cleared")

        msgs = ["Hi! I'm Bill!", "I'm the developer of the PC Storage System."]

        def grant_eevee(flag_name):
            flags[flag_name] = True
            raw = self.game.loader.fetch_specific(133)
            new_eevee = Pokemon(raw, self.game.assets, size_mult=2.5).max_ivs()  # a gift: perfect IVs
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
