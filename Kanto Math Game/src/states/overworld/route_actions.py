"""The route screen's field actions: fishing, headbutt, diving, berries, Shadow Pokemon, and route NPCs."""

import pygame
import random
import os
import datetime
from src.utils import Utils
from src.world import seasons
from src.world import hoenn
from src.world import levels
from src.pokemon import evolution
from src.world import regional_forms
from src.pokemon import forms
from src.pokemon.data import Pokemon
from src.states.overworld.common import _resolve_lines, _run_story_event


class RouteActions:
    """Part of PlayState (route.py): its field actions."""

    def _next_shadow(self):
        """The next Shadow Pokemon in this area's shadow_pool that hasn't been snagged."""
        flags = self.game.story_manager.story_flags
        return next((s for s in self.area_data.get("shadow_pool", []) if not flags.get(s["flag"])), None)

    def action_snag_shadow(self, repeat=False):
        """Orre: a Cipher trainer sends out the next Shadow Pokemon; weaken it and snag it. With
        repeat (SNAG AGAIN, once an area is cleared; Jordan, 10-27, not in the games), a straggler
        brings back one of the area's Shadow Pokemon, so you can keep one Shadow and purify another."""
        if repeat:
            pool = self.area_data.get("shadow_pool", [])
            if pool:
                s = random.choice(pool)
                self.action_challenge_boss({
                    "id": s["id"], "name": s["name"], "no_catch": False, "victory_flag": f"resnag_{s['flag']}",
                    "lines": [f"A Cipher straggler sends out another {s['name']}! A dark aura surrounds it...",
                              "Weaken it, then throw a ball. The Snag Machine will catch it!"],
                    "won": [f"The {s['name']} ran off... it will be back."], "rewards": {"balls": 3}})
                return
        shadow = self._next_shadow()
        if not shadow:
            self.is_progression_paused = True
            self.hide_menu_buttons()
            self.show_dialogue(["There are no more Shadow Pokemon here."], callback=self.show_progression_menu)
            return
        name = shadow["name"]
        left = sum(1 for s in self.area_data.get("shadow_pool", [])
                   if not self.game.story_manager.story_flags.get(s["flag"])) - 1
        self.action_challenge_boss({
            "id": shadow["id"], "name": name, "no_catch": False, "victory_flag": shadow["flag"],
            "lines": [f"{shadow.get('trainer') or 'A Cipher trainer'} sends out a {name}! A dark aura surrounds it...",
                      "Weaken it, then throw a ball. The Snag Machine will catch it!",
                      f"({left} more Shadow Pokemon here after this one.)" if left else "(It's the last one here!)"],
            "won": [f"The {name} ran off... it will be back."], "rewards": {"balls": 5}})

    PETAL_BERRIES = ("CHERI_BERRY", "CHESTO_BERRY", "PECHA_BERRY", "RAWST_BERRY", "ASPEAR_BERRY", "LEPPA_BERRY",
                     "ORAN_BERRY", "PERSIM_BERRY")

    def visit_pretty_petal(self):
        """Route 104's Pretty Petal flower shop (ORAS): the eldest sister tells you how Berries grow, the middle one
        gives you the Wailmer Pail, the youngest a Berry every day (one of eight)."""
        from src.world import berries
        self.is_progression_paused = True
        self.hide_menu_buttons()
        story = self.game.story_manager
        inv, flags = story.inventory, story.story_flags
        lines = ["Welcome to the Pretty Petal Flower Shop!"]
        if not flags.get("got_wailmer_pail"):
            flags["got_wailmer_pail"] = True
            inv["WAILMER_PAIL"] = 1
            lines += ["Eldest sister: Plant a Berry in soft soil and it grows into a tree, stage by stage.",
                      "Eldest sister: Pick the Berries once they're ripe, then plant another!",
                      "Middle sister: Take this! Water a growing plant once at each stage and it bears more Berries.",
                      f"{self.game.player_name} received the WAILMER PAIL!"]
        today = datetime.date.today().isoformat()
        if flags.get("pretty_petal_berry_day") != today:
            flags["pretty_petal_berry_day"] = today
            b = random.choice(self.PETAL_BERRIES)
            inv[b] = inv.get(b, 0) + 1
            lines += ["Youngest sister: Here's today's Berry for you!", f"{self.game.player_name} received {berries.a(berries.name(b)).upper()}!"]
        else:
            lines.append("Youngest sister: I'll have another Berry for you tomorrow!")
        self.show_dialogue(lines, callback=self.show_progression_menu)

    def visit_berry_boy(self):
        """Route 114's rich boy outside Lanette's house (ORAS "A Berry A Day"): one of five Berries, once a day."""
        from src.world import berries
        self.is_progression_paused = True
        self.hide_menu_buttons()
        story = self.game.story_manager
        today = datetime.date.today().isoformat()
        if story.story_flags.get("route114_berry_day") == today:
            lines = ["Berry boy: That's today's Berry! Come back tomorrow for another."]
        else:
            story.story_flags["route114_berry_day"] = today
            b = random.choice(("RAZZ_BERRY", "BLUK_BERRY", "NANAB_BERRY", "WEPEAR_BERRY", "PINAP_BERRY"))
            story.inventory[b] = story.inventory.get(b, 0) + 1
            lines = ["Berry boy: I love Berries, so I collect them! Here, have one.",
                     f"{self.game.player_name} received {berries.a(berries.name(b)).upper()}!"]
        self.show_dialogue(lines, callback=self.show_progression_menu)

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
        pokemon = Pokemon(self.game.loader.fetch_specific(pid), self.game.assets, size_mult=2.5).max_ivs()
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
            lines.append("Old man: And this emblem fell from one of their uniforms. It may open a way they keep hidden.")
            self._give_item("MAGMA_EMBLEM", lines)
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
            lines += ["Steven: Something invisible is blocking the way on this bridge... and at the Fortree Gym too.",
                      "Steven: This Devon Scope shows hidden Pokemon. Take it!"]
            self._give_item("DEVON_SCOPE", lines)
            lines += ["Steven: You and your partner have come so far together.",
                      "This Mega Stone belongs with your starter."]
            self._give_item(stone, lines)
            flags["got_starter_mega_stone"] = True
        elif event == "stone_shop":
            from src.states.systems import PokeMartState
            self.game.change_state(PokeMartState(self.game, self, stock=hoenn.shop_stones(self.game)))
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

    def action_rest_in_cabin(self):
        """REST IN CABIN on a long ride: the whole team is healed, like a Pokemon Center."""
        from src.states.overworld.area_transition import CABIN_REST_LINES, heal_team
        self.is_progression_paused = True
        self.hide_menu_buttons()
        heal_team(self.game)
        self.show_dialogue(list(CABIN_REST_LINES), callback=self.show_progression_menu)

    def story_event(self, key):
        self.is_progression_paused = True
        self.hide_menu_buttons()
        _run_story_event(self, key, lambda c: self._check_route_condition(c, False),
                         lambda lines: self.show_dialogue(lines, callback=self.show_progression_menu))

    def _route_npc_text(self, key, flag=None):
        """Talk to someone here; the option's victory_flag (if any) is set once they're done."""
        self.is_progression_paused = True
        self.hide_menu_buttons()

        def done():
            if flag:
                self.game.story_manager.story_flags[flag] = True
            self.show_progression_menu()

        self.show_dialogue(_resolve_lines(self.game, key), callback=done)

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

    def _fishing_pool(self, rod):
        """This area's own rod pool where the games have one (e.g. KANTO_ROUTE_21_SUPER_ROD_PERCENTAGES,
        from Serebii PokeEarth), else the region's (UNOVA_SUPER_ROD_POOL_PERCENTAGES), else its weaker
        rods' pools, else the Kanto pools that every region used to share."""
        data = self.game.loader.area_data
        region = self.game.story_manager.get_current_region()
        area = self.game.story_manager.current_area_key
        rods = ["SUPER_ROD", "GOOD_ROD", "OLD_ROD"]
        tried = rods[rods.index(rod):]
        for key in ([f"{area}_{r}_PERCENTAGES" for r in tried] + [f"{region}_{r}_POOL_PERCENTAGES" for r in tried]
                    + [f"{rod}_POOL_PERCENTAGES"]):
            if data.get(key):
                return data[key]
        return {}

    def action_fish(self):
        self.is_progression_paused = False
        self.hide_menu_buttons()

        self.rounds_completed += 1

        inv = self.game.story_manager.inventory
        rod = next((r for r in ("SUPER_ROD", "GOOD_ROD") if inv.get(r, 0) > 0), "OLD_ROD")
        fishing_pool_pct = self._fishing_pool(rod)

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
