"""The route screen's battles: wild, trainer, roaming, boss and Max Raid encounters, and evolutions."""

import pygame
import random
import os
import datetime
from src.utils import Utils
from src.world import seasons
from src.world import black_fog
from src.pokemon import catching
from src.world import levels
from src.pokemon import evolution
from src.world import regional_forms
from src.pokemon import forms
from src.pokemon.data import Pokemon
from src.vfx.particles import ShinyBurst, IdleSparkle
from src.config import FPS
from src.states.overworld.common import (
    _cast_trainer, _fill_names, _region_starter_id, _resolve_lines, _story_team, _trainer_sprite
)


class RouteEncounters:
    """Part of PlayState (route.py): its battles."""

    def check_roaming_encounter(self):
        """Checks for Entei/Raikou if Burned Tower has been visited."""
        if self.area_data.get("area_type") != "wild_route":
            return False

        if not self.game.story_manager.story_flags.get("visited_BURNED_TOWER"):
            return False
        # Raikou and Entei roam Johto's own routes only: not a sub-region (the Sinjoh Ruins) or
        # any other region, even though the Burned Tower flag stays set for the whole save.
        if (self.game.story_manager.get_current_region() != "JOHTO"
                or self.area_data.get("subregion")):
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
            pokemon.level = self.ROAMER_MAX_LEVEL  # Raikou and Entei roam at Lv 40, as in HeartGold/SoulSilver
            pokemon.current_hp = pokemon.get_max_hp()

            from src.states.battle import WildBattleState
            # The battle catches into this route (not an older one left in game.states).
            self.game.states["play"] = self
            battle_state = WildBattleState(self.game, pokemon, self.game.story_manager.current_area_key)
            battle_state.play_state_data = {
                "balls_left": self.balls_left, "current_streak": self.current_streak,
                "rounds_completed": self.rounds_completed, "pending_wild_encounters": 0,
                "initial_round_active": False}
            self.game.change_state(battle_state)
            return True
        return False

    ROAMER_CHANCE = 0.10

    ROAMER_MAX_LEVEL = 40

    def _starter_return(self):
        """After the starter battle (Hoenn's Poochyena), straight back to the professor's town,
        where his thanks play on arrival (starter_event "return_to", until "return_until")."""
        from src.states.overworld.area_transition import AreaTransitionState
        ev = self.area_data.get("starter_event") or {}
        story = self.game.story_manager
        boss_flag = (ev.get("boss") or {}).get("victory_flag")
        if (ev.get("return_to") and boss_flag and story.story_flags.get(boss_flag)
                and not story.story_flags.get(ev.get("return_until"))):
            self.game.change_state(AreaTransitionState(self.game, ev["return_to"]))
            return True
        return False

    def route_starter_event(self):
        """A starter chosen on a route (REGION_START "starter_area"; Hoenn's Route 101): the
        professor calls for help, the player picks a partner from his bag, then fights the wild
        Pokemon chasing him ("starter_event": lines, boss). Returns True when it took over."""
        ev = self.area_data.get("starter_event")
        story = self.game.story_manager
        region = story.get_current_region()
        if not ev or story.starter_on_route(region) != story.current_area_key:
            return False
        if not story.story_flags.get(f"received_starter_{region.lower()}"):
            from src.states.menus import StarterSelectionState
            cfg = story.get_region_start(region)
            self.is_progression_paused = True
            self.hide_menu_buttons()
            self.show_dialogue(_resolve_lines(self.game, ev.get("lines") or ["..."]), callback=lambda: (
                self.game.change_state(StarterSelectionState(
                    self.game, starter_ids=cfg.get("starters"), region=region, on_route=True))))
            return True
        boss = ev.get("boss") or {}
        if boss and not story.story_flags.get(boss.get("victory_flag")):
            self.action_challenge_boss(dict(boss))
            return True
        return False

    def trigger_scripted_on_enter_battle(self, on_enter):
        """Helper to handle the complex on_enter battle setup logic. A story battle on arrival
        (Bianca on Unova's Route 2) isn't one of the route's own rounds (Jordan, 10-29: leaving
        before the route is explored brings an ambush or a reason)."""

        trainer_info = _cast_trainer(self.game, dict(on_enter["trainer"]))
        team_ids = trainer_info.get("team", [])
        if team_ids and isinstance(team_ids, list) and len(team_ids) > 0 and isinstance(team_ids[0], list):
            trainer_info["team"] = random.choice(team_ids)
        opponent_team = _story_team(self.game, self.game.story_manager.current_area_key, trainer_info)

        from src.states.battle import TrainerBattleState, TrainerIntroState
        trainer_sprite = _trainer_sprite(self.game, trainer_info.get("sprite"))  # rival art too
        dlg = trainer_info.get("dialogue") or {}
        battle_state = TrainerBattleState(
            self.game, opponent_team, trainer_sprite=trainer_sprite,
            trainer_class=trainer_info["class"], trainer_name=_fill_names(self.game, trainer_info.get("name")),
            victory_flag=on_enter.get("flag_check"),
            is_boss_battle=trainer_info.get("is_boss_battle", False),
            rewards=dict(trainer_info["rewards"]) if trainer_info.get("rewards") else None,
            custom_dialogue={k: _resolve_lines(self.game, v) for k, v in dlg.items() if k != "intro"} or None,
        )
        intro_text = on_enter.get("dialogue_override") or (
            _resolve_lines(self.game, dlg["intro"]) if dlg.get("intro") else "Stop right there!")
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

    def start_initial_round(self):
        self.is_progression_paused = False
        self.hide_menu_buttons()
        self.route_buttons.clear()

        if catching.total_balls(self.game.story_manager) <= 0 and self.game.story_manager.catch_unlocked():
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
                if not self.game.story_manager.is_trainer_defeated(area_key, i) and self._in_zone(trainer_pool[i])
            ]
            if not available:
                self.trigger_wild_encounter()
                return
            trainer_idx = available[0]

        trainer_info = _cast_trainer(self.game, trainer_pool[trainer_idx])
        trainer_class = trainer_info.get("class", "YOUNGSTER")
        # Names like "{rival_name}" and text keys are filled in, as story battles do.
        trainer_name = _fill_names(self.game, trainer_info.get("name"))
        custom_dialogue = trainer_info.get("dialogue")
        if isinstance(custom_dialogue, dict):
            custom_dialogue = {k: (v if k == "intro" else _resolve_lines(self.game, v))
                               for k, v in custom_dialogue.items()}
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
            choice = (trainer_info.get("team_choice") or {}).get(str(_region_starter_id(self.game)))
            if choice:  # a rival's team follows the player's starter
                opponent_ids = list(choice)

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
        if trainer_info.get("levels") and not levels.postgame_trainers(self.game, area_key):
            # a story trainer's levels from the games (a rival), lifted if the team has outgrown them
            levels.set_team(opponent_team, levels.follow_team(self.game, trainer_info["levels"]), exact=True)
        else:
            levels.set_team(opponent_team, levels.trainer_team_levels(self.game, area_key, len(opponent_team), is_boss))

        bg_file = self._get_battle_background_for_area()

        from src.states.battle import TrainerBattleState, TrainerIntroState

        trainer_sprite = _trainer_sprite(self.game, trainer_info.get("sprite"))
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
        intro_text = _resolve_lines(self.game, random.choice(intro_text_options))

        intro_state = TrainerIntroState(
            self.game, trainer_sprite, intro_text, battle_state
        )
        pygame.event.clear()
        self.game.change_state(intro_state)

    def _get_wild_pool(self, area_data):
        """The current area's percentage pool: day/night split, then season and weather."""
        pool = regional_forms.extend_pool(self.game, self._base_wild_pool(area_data))
        return seasons.adjust_pool(self.game, pool, self.game.story_manager.current_area_key)

    def _base_wild_pool(self, area_data):
        """Returns the percentage pool dict for the current area, respecting day/night splits."""
        # A zone with its own Pokemon (the Safari Zones' areas: "zone_pools" {zone key: pool key}).
        zone = self._zone() if area_data is self.area_data else None
        zone_key = zone and (area_data.get("zone_pools") or {}).get(zone.get("key"))
        if zone_key and self.game.loader.area_data.get(zone_key):
            return self.game.loader.area_data[zone_key]
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
        if catching.total_balls(self.game.story_manager) <= 0:  # no catch screen without balls: say so
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
                poke.evo_due = False  # checked after its level-up: it waits for the next one
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
                        consume_catch_count=is_catch_evo,
                        choices=next_entries if len(next_entries) > 1 else None
                        )
                    self.game.change_state(evo_state)
                    return True
        return False

    def _boss_flag_for(self, item):
        """The victory flag a BOSS button's battle will use (same rule as action_challenge_boss)."""
        boss = item.get("boss") or self.area_data.get("area_boss") or {}
        return boss.get("victory_flag", f"{self.game.story_manager.current_area_key}_boss_defeated")

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
        if pid == black_fog.BOSS_ID:  # the Black Fog: as strong as your strongest Pokemon
            pokemon.level = black_fog.level(self.game.story_manager)
        elif boss_data.get("level"):  # the games' level (canon since 10-29, legendaries included)
            pokemon.level = int(boss_data["level"])
        else:
            pokemon.level = levels.boss_level(self.game, self.game.story_manager.current_area_key, pokemon.id)
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

    # Raid teammates (Jordan, 11-06): three trainers of random classes, each with one fully evolved,
    # non-legendary Pokemon from the region's own Pokedex, at the raid's level.
    RAID_TRAINERS = (("Hiker", "hiker.png"), ("Ace Trainer", "acetrainer_m.png"), ("Ace Trainer", "acetrainer_f.png"),
                     ("Lass", "lass.png"), ("Youngster", "youngster.png"), ("Veteran", "veteran.png"),
                     ("Swimmer", "swimmer_f.png"), ("Scientist", "scientist.png"), ("Psychic", "psychic.png"),
                     ("Backpacker", "hiker.png"), ("Ranger", "ranger_m.png"), ("Skier", "skier.png"))
    RAID_NAMES = ("Ava", "Ben", "Cleo", "Dev", "Esme", "Finn", "Gus", "Hana", "Ivo", "Jade", "Kai", "Lia", "Milo",
                  "Nell", "Otto", "Pia", "Quin", "Rae", "Sol", "Tess", "Uma", "Vic", "Wren", "Zed")

    def raid_allies(self, level):
        """[(trainer's name, Pokemon)] for a Max Raid: three teammates."""
        from src.states.systems.pokedex import region_dex
        from src.pokemon import balance
        story = self.game.story_manager
        region = story.get_current_region()
        evo = self.game.loader.evolution_map or {}
        names = self.game.assets.pokemon_names or {}

        def fully_evolved(pid):
            n = str(names.get(str(pid), "")).upper()
            return n and n not in evo and n.split("-")[0] not in evo
        pool = [p for p in region_dex(story.get_region_start(region))
                if p <= 1025 and not balance.is_legendary(p) and fully_evolved(p)]
        pool = pool or [p for p in range(1, 152) if not balance.is_legendary(p) and fully_evolved(p)]
        out = []
        for (cls, sprite), name, pid in zip(random.sample(self.RAID_TRAINERS, 3), random.sample(self.RAID_NAMES, 3),
                                            random.sample(pool, min(3, len(pool)))):
            try:
                mon = Pokemon(self.game.loader.fetch_specific(pid), self.game.assets, size_mult=3.125)
            except Exception:
                continue
            mon.level = max(5, level - random.randint(0, 3))
            mon.current_hp = mon.get_max_hp()
            from src.pokemon import moves as movelib
            movelib.ensure_moves(self.game, mon)
            out.append((f"{cls} {name}", sprite, mon))
        return out

    def roll_raid(self):
        """(star, pick) for this den's next raid ("94-gmax", "130"), or None: rolled once and kept until it's
        fought, so the walked map can show the den's Pokemon before you go in (Jordan, 11-06)."""
        if getattr(self, "_raid_next", None):
            return self._raid_next
        den = self.area_data.get("max_raid_den", {})
        star = self._roll_raid_star()
        while star > 1 and not den.get(str(star)):
            star -= 1
        table = den.get(str(star))
        if not table:
            return None
        self._raid_next = (star, random.choices(list(table), weights=list(table.values()))[0])
        return self._raid_next

    def action_max_raid(self):
        """Max Raid Battle: a Dynamax (or rare Gigantamax) boss drawn from this den's star-rank table."""
        rolled = self.roll_raid()
        if not rolled:
            self.show_progression_menu()
            return
        star, pick = rolled
        self._raid_next = None  # (the next one rolls fresh)

        self.is_progression_paused = True
        self.hide_menu_buttons()
        self.rounds_completed += 1

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
            battle_state.raid_allies = allies  # (they attack the boss after you each turn)
            self.game.change_state(battle_state)

        allies = self.raid_allies(pokemon.level)
        if allies:
            intro = intro + ["Three trainers joined you: " + ", ".join(
                f"{n} with {m.display_name.upper()}" for n, _s, m in allies) + "!"]
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

        # By the pool's own odds (it used to pick evenly among the four rarest, so a 1% Galarian
        # Zigzagoon came up more often than Hoenn's 43% Zigzagoon).
        chosen_id = int(Utils.weighted_random_choice(wild_pool_pct))

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
