import os
import json


# [REF-0012: Data Manager]
class DataManager:
    def __init__(self, base_dir):
        self.save_file = os.path.join(base_dir, "game_data.json")
        self.data = self._load()

    @staticmethod
    def _json_default(obj):
        if isinstance(obj, (set, frozenset, tuple)):
            return sorted(obj, key=str)
        return str(obj)

    @staticmethod
    def read_json(path):
        """Read a save file, falling back to its .bak copy.
        Returns (data or None, status) with status "ok", "restored", "damaged" or "missing"."""
        if not os.path.exists(path) and not os.path.exists(path + ".bak"):
            return None, "missing"
        for candidate, status in ((path, "ok"), (path + ".bak", "restored")):
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    return json.load(f), status
            except (OSError, ValueError):
                continue
        return None, "damaged"

    def _load(self):
        data, status = self.read_json(self.save_file)
        if status == "damaged":
            # Keep the broken file for rescue instead of quietly overwriting it.
            try:
                os.replace(self.save_file, self.save_file + ".corrupt")
            except OSError:
                pass
            print(f"Save file {self.save_file} was damaged; kept it as .corrupt")
        if data is not None:
            return data
        return {
            "high_score": 0,
            "total_shinies": 0,
            "pokedex": {},
            "defeated_bosses": {},
            "story": {},
            "seen_pokemon": [],
        }

    def save(self):
        """Safe save: build the whole text first, write it to a temp file, keep the previous
        save as .bak, then swap the new file in. A crash mid-save can't destroy the save."""
        text = json.dumps(self.data, default=self._json_default)
        tmp = self.save_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, "r", encoding="utf-8") as f:
                    json.load(f)  # only back up a good save
                os.replace(self.save_file, self.save_file + ".bak")
            except (OSError, ValueError):
                pass
        os.replace(tmp, self.save_file)

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

    # Forms that count as their base species in the Pokedex: a Shadow Pokemon is that species
    # (no entry of its own), and Urshifu's styles are both #892 (kept as styles too).
    BASE_ONLY_FORMS = {"shadow"}
    ALSO_BASE_FORMS = {"single", "rapid"}

    def add_pokemon(self, pokemon):
        base = getattr(pokemon, "meta_id", pokemon.id)
        if pokemon.form in self.BASE_ONLY_FORMS | self.ALSO_BASE_FORMS and base != pokemon.id:
            name = str(pokemon.display_name)
            if name.upper().startswith("SHADOW "):
                name = name[7:]
            self._register(f"{base}-normal", base, name.split(" - ")[0], "normal", pokemon)
            if pokemon.form in self.BASE_ONLY_FORMS:
                return
        self._register(f"{pokemon.id}-{pokemon.form}", pokemon.id, pokemon.display_name, pokemon.form, pokemon)

    def _register(self, p_key, pid, name, form, pokemon):
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
            "id": pid,
            "name": name,
            "form": form,
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
