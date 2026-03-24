# [REF-0017: Story Manager]
from src.pokemon.data import Pokemon

class StoryManager:
    """Tracks the player's progress through the story."""

    def __init__(self):
        self.player_team = []
        self.pc_pokemon = []
        self.rival_starter_raw = None
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
        self.initialized = False

    def initialize_new_game(self, config):
        if self.initialized: return
        self.money = config.get("STARTING_MONEY", 3000)
        self.balls_left = config.get("STARTING_BALLS", 5)
        self.current_area_key = config.get("STARTING_AREA", "PALLET_TOWN")
        self.initialized = True

    def get_victory_outcome(self, battle_type="rival"):
        area_data = self.game.loader.area_data
        if battle_type == "rival":
            event_data = area_data.get("AFTER_STARTER_RIVAL", {})
            return {
                "next_area": event_data.get("next_area", "KANTO_ROUTE_1"),
                "rewards": event_data.get("rewards", {"balls": 5}),
                "message": event_data.get("rewards", {}).get("message", ""),
            }

        current = area_data.get("STORY_PROGRESSION", {}).get(self.current_area_key, {})
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
            "player_team": [
                {"id": p.id, "form": p.form, "shiny": p.is_shiny, "wins": p.wins}
                for p in self.player_team
            ],
            "pc_pokemon": [
                {"id": p.id, "form": p.form, "shiny": p.is_shiny, "wins": p.wins}
                for p in self.pc_pokemon
            ],
            "rival_starter_id": (
                self.rival_starter_raw["id"] if self.rival_starter_raw else None
            ),
            "player_name": self.game.player_name,
            "rival_name": getattr(self.game, "rival_name", "BLUE"),
        }

    def deserialize(self, data, loader):
        self.current_area_key = data.get("current_area_key", "PALLET_TOWN")
        self.badges = data.get("badges", [])
        self.defeated_trainers = {
            k: set(v) for k, v in data.get("defeated_trainers", {}).items()
        }
        self.story_flags = data.get("story_flags", {})
        self.balls_left = data.get("balls_left", 5)
        self.current_streak = data.get("current_streak", 0)
        self.money = data.get("money", 3000)
        self.catch_counts = data.get("catch_counts", {})
        self.inventory = data.get("inventory", {})

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

        elif isinstance(gym_bg_config, str):
            return gym_bg_config

        return None
