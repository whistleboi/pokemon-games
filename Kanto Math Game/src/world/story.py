# [REF-0017: Story Manager]
from src.pokemon.data import Pokemon


class StoryManager:
    """Tracks the player's progress through the story."""

    def __init__(self):
        self.player_team = []
        self.pc_pokemon = []
        self.rival_starter_raw = None
        self.user_rival_starter_raw = None
        self.starting_region = "KANTO"
        self.game_started = False
        self.checkpoint = None
        self.current_area_key = "PALLET_TOWN"
        self.species_evolution_xp = {}
        self.badges = []
        self.defeated_trainers = {}
        self.story_flags = {}
        self.balls_left = 5
        self.current_streak = 0
        self.money = 3000
        self.catch_counts = {}
        self.inventory = {}
        self.notified_missions = []
        self.initialized = False

    def initialize_new_game(self, config):
        if self.initialized:
            return
        self.money = config.get("STARTING_MONEY", 3000)
        self.balls_left = config.get("STARTING_BALLS", 5)
        # RegionSelectionState will override this, but we default to config
        self.current_area_key = config.get("STARTING_AREA", "PALLET_TOWN")
        self.initialized = True

    def get_victory_outcome(self, battle_type="rival"):
        area_data = self.game.loader.area_data
        if battle_type == "rival":
            event_data = area_data.get("AFTER_STARTER_RIVAL", {})
            return {
                "next_area": event_data.get("next_area", "KANTO_ROUTE_1"),
                "rewards": event_data.get("rewards", {"balls": 5}),
                "message": event_data.get("rewards", {}).get("message", "")
            }

        prog = area_data.get("STORY_PROGRESSION", {})
        current = prog.get(self.current_area_key, {})
        return {
            "next_area": current.get("next_area", "KANTO_ROUTE_1"),
            "rewards": current.get("rewards", {"balls": 3}),
            "message": "",
        }

    def set_checkpoint(self, state_class, **kwargs):
        self.checkpoint = {"state_class": state_class, "kwargs": kwargs}

    def get_current_area_data(self):
        if not hasattr(self, "game") or self.game is None:
            return {}
        return self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(
            self.current_area_key, {}
        )

    def get_active_missions(self):
        """Returns a list of missions whose conditions are currently met."""
        all_missions = self.game.loader.area_data.get("JOURNAL_MISSIONS", [])
        active = []

        unique_caught = len(self.game.data.data.get("pokedex", {}))

        for m in all_missions:
            cond = m.get("condition", {})
            met = True

            # Evaluate Conditions
            if "start_region" in cond and self.starting_region != cond["start_region"]:
                met = False

            if "badges_min" in cond and len(self.badges) < cond["badges_min"]:
                met = False
            if "badges_less" in cond and len(self.badges) >= cond["badges_less"]:
                met = False
            
            if "flag" in cond:
                flags = cond["flag"] if isinstance(cond["flag"], list) else [cond["flag"]]
                if not all(self.story_flags.get(f) for f in flags): met = False
            if "flag_not" in cond:
                flags = cond["flag_not"] if isinstance(cond["flag_not"], list) else [cond["flag_not"]]
                if any(self.story_flags.get(f) for f in flags): met = False
                
            if "visited" in cond and not self.story_flags.get(f"visited_{cond['visited']}"):
                met = False
            if "visited_not" in cond and self.story_flags.get(f"visited_{cond['visited_not']}"):
                met = False
                
            if "item" in cond:
                items = cond["item"] if isinstance(cond["item"], list) else [cond["item"]]
                if not any(self.inventory.get(it, 0) > 0 for it in items): met = False
            if "item_not" in cond:
                items = cond["item_not"] if isinstance(cond["item_not"], list) else [cond["item_not"]]
                if any(self.inventory.get(it, 0) > 0 for it in items): met = False
                
            if "has_pokemon" in cond:
                pids = cond["has_pokemon"] if isinstance(cond["has_pokemon"], list) else [cond["has_pokemon"]]
                owned_ids = {p.id for p in self.player_team} | {p.id for p in self.pc_pokemon}
                if not any(pid in owned_ids for pid in pids): met = False
                
            if "defeated_area" in cond:
                area = cond["defeated_area"]
                prog_data = self.game.loader.area_data.get("STORY_PROGRESSION", {})
                a_data = prog_data.get(area, {})
                t_pool = a_data.get("trainer_pool", [])
                defeated = self.defeated_trainers.get(area, set())
                if not t_pool or len(defeated) < len(t_pool): met = False

            if "caught_min" in cond and unique_caught < cond["caught_min"]:
                met = False
            if "caught_less" in cond and unique_caught >= cond["caught_less"]:
                met = False

            if met:
                active.append(m)

        # Sort: Show one MAIN mission (highest badges_min) and all applicable SIDE missions
        main_missions = [m for m in active if m["type"] == "MAIN"]
        side_missions = [m for m in active if m["type"] == "SIDE"]

        # [FIX] Pick the LATEST applicable main mission (the one furthest down the list).
        # This ensures that as you unlock new stages of the journey, the old ones are hidden.
        final_list = []
        if main_missions:
            final_list.append(main_missions[-1]) 

        final_list.extend(side_missions)
        return final_list

    def get_all_journal_entries(self):
        """Returns all missions categorized by Active or Completed status."""
        all_missions = self.game.loader.area_data.get("JOURNAL_MISSIONS", [])
        entries = []
        
        for m in all_missions:
            cond = m.get("condition", {})
            
            # Region filter
            if "start_region" in cond and self.starting_region != cond["start_region"]:
                continue
                
            status = "INACTIVE"
            is_completed = False
            
            # [FIX] Refined completion heuristic. Prerequisite flags should NOT count as completion.
            # Only 'visited' and explicit 'flag' checks that aren't prerequisites count.
            if "visited" in cond and self.story_flags.get(f"visited_{cond['visited']}"): is_completed = True
            if "completed_flag" in m and self.story_flags.get(m["completed_flag"]): is_completed = True

            if is_completed:
                status = "COMPLETED"
            else:
                # Reuse active checking logic
                active_ids = [act["id"] for act in self.get_active_missions()]
                if m["id"] in active_ids:
                    status = "ACTIVE"
            
            if status != "INACTIVE":
                m_copy = m.copy()
                m_copy["status"] = status
                entries.append(m_copy)
                
        return entries

    def has_unread_missions(self):
        """Checks if there are any active missions not yet in the notified list."""
        active = self.get_active_missions()
        for m in active:
            if m["id"] not in self.notified_missions:
                return True
        return False

    def get_current_hint(self):
        """Provides a contextual hint to the player."""
        if "BOULDER" not in self.badges:
            if self.current_area_key != "PEWTER_CITY":
                return "Travel to Pewter City to challenge the first Gym Leader, Brock!"
            else:
                return "Challenge Brock at the Pewter City Gym to earn the Boulder Badge!"

        if "CASCADE" not in self.badges:
            if self.current_area_key != "CERULEAN_CITY":
                return "Make your way through Mt. Moon to get to Cerulean City for your next badge!"
            else:
                return "Challenge Misty at the Cerulean Gym. Her Water-type Pokémon are tough!"

        if not self.story_flags.get("tower_ghost_defeated"):
            if self.current_area_key != "LAVENDER_TOWN":
                return "A sad spirit haunts the Pokémon Tower in Lavender Town. Maybe you can help."
            elif not self.story_flags.get("got_silph_scope"):
                return "You need a Silph Scope to identify the ghost in the Pokémon Tower. Team Rocket might have one..."
            else:
                return "Head to the top of the Pokémon Tower in Lavender Town to confront the ghost."

        if not self.story_flags.get("KANTO_ROUTE_11_boss_defeated"):
            if self.inventory.get("POKE_FLUTE", 0) == 0:
                return "Now that the ghost is at peace, talk to Mr. Fuji in Lavender Town. He might have a reward for you."
            else:
                return "A Snorlax is blocking Route 11, east of Vermillion City. Use the Poké Flute to wake it up!"

        return "Your next challenge awaits! Explore the Kanto region and become a Pokémon Master!"

    def load_last_checkpoint(self, game):
        if not self.checkpoint:
            game.change_state(game.states["play"])
            return

        state_class = self.checkpoint["state_class"]
        kwargs = self.checkpoint["kwargs"]

        if state_class.__name__ == "PlayState":
            new_state = state_class(game)
            for k, v in kwargs.items():
                setattr(new_state, k, v)
            game.states["play"] = new_state
            game.change_state(new_state)
        else:
            game.change_state(state_class(game, **kwargs))

    def is_trainer_defeated(self, area, index):
        return index in self.defeated_trainers.get(area, set())

    def mark_trainer_defeated(self, area, index):
        if area not in self.defeated_trainers:
            self.defeated_trainers[area] = set()
        self.defeated_trainers[area].add(index)

    def sync_badges(self):
        """
        Validates badges against gym progress.
        Ensures players get credit for badges even if a state transition failed.
        """
        if not hasattr(self, "game") or not self.game.loader:
            return

        progression = self.game.loader.area_data.get("STORY_PROGRESSION", {})
        for area_key, area_data in progression.items():
            gym = area_data.get("gym")
            if not gym:
                continue

            # Check progress flag for this gym
            prog_key = f"gym_progress_{area_key}"
            prog_val = self.story_flags.get(prog_key, 0)

            trainers = gym.get("trainers", [])
            leader = gym.get("leader")

            # If progress is higher than trainer count, the leader was beaten
            if leader and prog_val > len(trainers):
                badge = leader.get("badge_reward")
                if badge and badge not in self.badges:
                    print(f"Sync: Awarding missing {badge} Badge for {area_key}!")
                    self.badges.append(badge)
            
            # [FIX] Specific recovery for the League Title
            if area_key == "INDIGO_PLATEAU" and prog_val > len(trainers):
                if not self.story_flags.get("beat_champion"):
                    self.story_flags["beat_champion"] = True

        # Run key item sync as well to catch up legacy saves
        self.sync_key_items()

    def sync_key_items(self):
        """Ensures players have key items associated with badges/flags they have already earned."""
        if not hasattr(self, "inventory") or self.inventory is None:
            self.inventory = {}

        # Mapping: Badge earned -> Item granted by Leader
        badge_to_item = {
            "BOULDER": "OLD_ROD",
            "CASCADE": "BIKE_VOUCHER",
            "THUNDER": "EXP_SHARE",
            "RAINBOW": "COIN_CASE",
            "MARSH": "AIR_BALLOON",
            "SOUL": "SURF_BOARD",
            "VOLCANO": "VOLCANO_PASS",
            "EARTH": "CERULEAN_CAVE_MAP"
        }
        
        # Johto Mapping: ZEPHYR -> EXP_SHARE, etc.
        johto_badge_to_item = {
            "ZEPHYR": "EXP_SHARE",
            "HIVE": "OLD_ROD",
            "PLAIN": "SQUIRT_BOTTLE",
            "FOG": "SUPER_ROD",
            "STORMBADGE": "SURF_BOARD",
            "MINERAL": "AIR_BALLOON",
            "GLACIER": "VOLCANO_PASS",
            "RISING": "MT_SILVER_MAP"
        }

        for badge, item in badge_to_item.items():
            if badge in self.badges and self.inventory.get(item, 0) == 0:
                # Special bypass: if you already have the BICYCLE, you don't need the VOUCHER
                if item == "BIKE_VOUCHER" and self.inventory.get("BICYCLE", 0) > 0:
                    continue
                print(f"Sync: Awarding missing {item} for {badge} Badge!")
                self.inventory[item] = 1
                
        for badge, item in johto_badge_to_item.items():
            if badge in self.badges and self.inventory.get(item, 0) == 0:
                print(f"Sync: Awarding missing {item} for Johto {badge} Badge!")
                self.inventory[item] = 1

        # Flag-based items
        if self.story_flags.get("tower_ghost_defeated"):
            if self.inventory.get("POKE_FLUTE", 0) == 0:
                print("Sync: Awarding missing POKE_FLUTE!")
                self.inventory["POKE_FLUTE"] = 1
            if self.inventory.get("SILPH_SCOPE", 0) == 0:
                print("Sync: Awarding missing SILPH_SCOPE!")
                self.inventory["SILPH_SCOPE"] = 1

    def serialize(self):
        return {
            "current_area_key": self.current_area_key,
            "badges": self.badges,
            "balls_left": self.balls_left,
            "current_streak": self.current_streak,
            "money": self.money,
            "defeated_trainers": {
                k: list(v) for k, v in self.defeated_trainers.items()
            },
            "story_flags": self.story_flags,
            "catch_counts": self.catch_counts,
            "inventory": self.inventory,
            "notified_missions": self.notified_missions,
            "player_team": [
                {"id": p.id, "form": p.form, "shiny": p.is_shiny, "wins": p.wins}
                for p in self.player_team
            ],
            "pc_pokemon": [
                {"id": p.id, "form": p.form, "shiny": p.is_shiny, "wins": p.wins}
                for p in self.pc_pokemon
            ],
            "starting_region": self.starting_region,
            "rival_starter_id": (
                self.rival_starter_raw["id"] if self.rival_starter_raw else None
            ),
            "user_rival_starter_id": (
                self.user_rival_starter_raw["id"] if self.user_rival_starter_raw else None
            ),
            "player_name": self.game.player_name,
            "rival_name": getattr(self.game, "rival_name", "BLUE"),
        }

    def deserialize(self, data, loader):
        self.starting_region = data.get("starting_region", "KANTO")
        self.current_area_key = data.get("current_area_key", "PALLET_TOWN")
        self.badges = data.get("badges", [])
        self.defeated_trainers = {
            k: set(v) for k, v in data.get("defeated_trainers", {}).items()
        }
        self.story_flags = data.get("story_flags", {})
        self.balls_left = data.get("balls_left", 5)
        self.current_streak = data.get("current_streak", 0)
        self.money = data.get("money", 3000)
        
        # [FIX] Ensure catch_counts keys are cast back to integers from JSON string keys
        raw_counts = data.get("catch_counts", {})
        self.catch_counts = {int(k): v for k, v in raw_counts.items()}
        
        self.inventory = data.get("inventory", {})
        self.notified_missions = data.get("notified_missions", [])

        self.player_team = []
        for p_data in data.get("player_team", []):
            raw = loader.fetch_specific(
                p_data["id"],
                form=p_data.get("form", "normal"),
                is_shiny=p_data.get("shiny", False),
            )
            pokemon = Pokemon(raw, loader.game.assets, size_mult=2.5)
            pokemon.wins = p_data.get("wins", 0)
            self.player_team.append(pokemon)

        self.pc_pokemon = []
        for p_data in data.get("pc_pokemon", []):
            raw = loader.fetch_specific(
                p_data["id"],
                form=p_data.get("form", "normal"),
                is_shiny=p_data.get("shiny", False),
            )
            pokemon = Pokemon(raw, loader.game.assets, size_mult=2.5)
            pokemon.wins = p_data.get("wins", 0)
            self.pc_pokemon.append(pokemon)

        rid = data.get("rival_starter_id")
        if rid:
            self.rival_starter_raw = loader.fetch_specific(rid)
            
        urid = data.get("user_rival_starter_id")
        if urid:
            self.user_rival_starter_raw = loader.fetch_specific(urid)

        self.game.player_name = data.get("player_name", "TRAINER")
        self.game.rival_name = data.get("rival_name", "BLUE")

    def get_gym_battle_background(self, area_id, trainer_index=0, is_leader=False):
        """
        Determines the correct battle background for a Gym or League battle.
        Handles both static strings (standard gyms) and lists (Elite 4).
        """
        area_data = self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(area_id, {})
        backgrounds = area_data.get("backgrounds", {})
        gym_bg_config = backgrounds.get("gym")

        if isinstance(gym_bg_config, list):
            if is_leader:
                return gym_bg_config[-1] if gym_bg_config else None
            else:
                if 0 <= trainer_index < len(gym_bg_config):
                    return gym_bg_config[trainer_index]
                else:
                    return gym_bg_config[0]

        # 2. Specific Battle Background (Standard Gyms)
        if "battle" in backgrounds:
            return backgrounds["battle"]

        elif isinstance(gym_bg_config, str):
            return gym_bg_config

        return None
