import os
import json


# [REF-0012: Data Manager]
class DataManager:
    def __init__(self, base_dir):
        self.save_file = os.path.join(base_dir, "game_data.json")
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "high_score": 0,
            "total_shinies": 0,
            "pokedex": {},
            "defeated_bosses": {},
            "story": {},
            "seen_pokemon": [],
        }

    def save(self):
        with open(self.save_file, "w") as f:
            json.dump(self.data, f)

    def get_high_score(self):
        return self.data.get("high_score", 0)

    def set_high_score(self, score):
        self.data["high_score"] = score

    def get_total_shinies(self):
        return self.data.get("total_shinies", 0)

    def add_shiny(self):
        self.data["total_shinies"] = self.get_total_shinies() + 1

    def reset_shinies(self):
        self.data["total_shinies"] = 0

    def add_pokemon(self, pokemon):
        p_key = f"{pokemon.id}-{pokemon.form}"
        if (
            p_key in self.data["pokedex"]
            and self.data["pokedex"][p_key].get("shiny", False)
            and not pokemon.is_shiny
        ):
            if getattr(pokemon, "gmax_factor", False):
                self.data["pokedex"][p_key]["gmax"] = True
            return

        had_gmax = self.data["pokedex"].get(p_key, {}).get("gmax", False)
        self.data["pokedex"][p_key] = {
            "id": pokemon.id,
            "name": pokemon.display_name,
            "form": pokemon.form,
            "shiny": pokemon.is_shiny,
            "gmax": had_gmax or getattr(pokemon, "gmax_factor", False),
        }

    def add_defeated_boss(self, pokemon):
        p_key = f"{pokemon.id}-{pokemon.form}"
        if (
            p_key in self.data["defeated_bosses"]
            and self.data["defeated_bosses"][p_key].get("shiny", False)
            and not pokemon.is_shiny
        ):
            return

        self.data["defeated_bosses"][p_key] = {
            "id": pokemon.id,
            "name": pokemon.display_name,
            "form": pokemon.form,
            "shiny": pokemon.is_shiny,
        }

    def mark_seen(self, p_id):
        """Registers a Pokemon ID as seen."""
        if "seen_pokemon" not in self.data:
            self.data["seen_pokemon"] = []
        if p_id not in self.data["seen_pokemon"]:
            self.data["seen_pokemon"].append(int(p_id))
            self.save()

    def wipe_data(self):
        self.data["pokedex"] = {}
        self.data["total_shinies"] = 0
        self.data["defeated_bosses"] = {}
        self.data["story"] = {}
        self.data["seen_pokemon"] = []
        self.save()
