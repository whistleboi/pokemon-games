# [REF-0017: Story Manager]
from src.pokemon.data import Pokemon


class StoryManager:
    """Tracks the player's progress through the story."""

    def __init__(self):
        self.player_team = []
        self.pc_pokemon = [None] * 300
        self.rival_starter_raw = None
        self.user_rival_starter_raw = None
        self.starting_region = "KANTO"
        # Regions this save has been to (cross-gen evolution gating, src/pokemon/evolution.py).
        self.visited_region_set = set()
        # One rival per region, never repeated within a save: {region: {name, character, starter_id}}
        self.region_rivals = {}
        self.game_started = False
        self.checkpoint = None
        self.current_area_key = "PALLET_TOWN"
        self.species_evolution_xp = {}
        self.badges = {"KANTO": [], "JOHTO": []}
        self.active_badge_region = "KANTO"
        self.defeated_trainers = {}
        self.story_flags = {}
        self.balls_left = 5
        self.current_streak = 0
        self.money = 3000
        self.catch_counts = {}
        self.inventory = {}
        self.poffins = []  # Poffin Case contents: dicts from src.pokemon.poffin.cook
        self.notified_missions = []
        self.initialized = False
        # "AUTO" follows the story; a number locks a level from math_levels.json
        self.math_difficulty = "AUTO"
        self.level_cap_mode = "STORY"  # STORY, OBEDIENCE or NONE (Options)
        self.last_center = None  # area key of the last Pokemon Center used (whiteouts go there)
        self.autosave = True     # Options: save every time you travel to a new area

    def caught_in_range(self, lo, hi):
        """How many different species #lo-#hi the player has caught (forms count once)."""
        dex = self.game.data.data.get("pokedex", {}) if getattr(self, "game", None) else {}
        return len({int(v.get("id", 0)) for v in dex.values() if lo <= int(v.get("id", 0)) <= hi})

    def kanto_caught_count(self):
        """Different Kanto species caught, #1-150 (Mew waits until all of them are)."""
        dex = self.game.data.data.get("pokedex", {}) if getattr(self, "game", None) else {}
        return len({int(v.get("id", 0)) for v in dex.values() if 1 <= int(v.get("id", 0)) <= 150})

    MAX_ITEMS = 999  # the most of one item the Bag holds, as in the games

    def add_item(self, key, qty=1):
        """Put items in the Bag (never past 999). Returns how many actually went in."""
        have = self.inventory.get(key, 0)
        added = max(0, min(qty, self.MAX_ITEMS - have))
        self.inventory[key] = have + added
        return added

    def initialize_new_game(self, config):
        if self.initialized:
            return
        self.money = config.get("STARTING_MONEY", 3000)
        self.balls_left = config.get("STARTING_BALLS", 5)
        self.pc_pokemon = [None] * 300
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
        all_missions = self.region_missions()
        active = []

        for m in all_missions:
            if self.check_requirements(m.get("condition", {}), region=m.get("region")):
                if m.get("completed_flag") and self.story_flags.get(m["completed_flag"]):
                    continue
                active.append(self._prepare_mission_for_ui(m))

        main_missions = [m for m in active if m["type"] == "MAIN"]
        # Missions tied to the region the player is in come first.
        region = self.get_current_region()
        regional = [m for m in main_missions if m.get("condition", {}).get("required_region") == region]
        main_missions = regional or main_missions
        side_missions = [m for m in active if m["type"] == "SIDE"]
        final_list = []

        if main_missions:
            final_list.append(main_missions[-1])

        final_list.extend(side_missions)
        return final_list

    def region_missions(self):
        """Missions for the region the player is in (Hisui counts as Sinnoh)."""
        region = self.get_current_region()
        return [m for m in self.game.loader.area_data.get("JOURNAL_MISSIONS", [])
                if (m.get("region") or (m.get("condition") or {}).get("required_region") or region) == region]

    def check_requirements(self, cond, region=None):
        """
        Universal requirement checker. Returns True if all conditions in 'cond' are met.
        Supports: flag, flag_not, visited, visited_not, item, item_not,
        has_pokemon, defeated_area, caught_min, and required_region.
        """
        if not cond:
            return True

        if isinstance(cond, str):
            if cond == "has_8_badges":
                return sum(len(b) for b in self.badges.values()) >= 8
            if cond.startswith("has_8_") and cond.endswith("_badges"):
                region = cond[6:-7].upper()
                return len(self.badges.get(region, [])) >= 8
            if cond.startswith("has_") and cond.endswith("_badge"):
                b_name = cond.split("_")[1].upper()
                return any(b_name in blist for blist in self.badges.values())
            return self.story_flags.get(cond, False)

        total_badges = sum(len(b_list) for b_list in self.badges.values())
        if region:  # a region's missions count that region's badges
            total_badges = len(self.badges.get(region, []))
        unique_caught = len({v['id'] for v in self.game.data.data.get("pokedex", {}).values() if isinstance(v, dict) and 'id' in v})

        if "required_region" in cond and self.get_current_region() != cond["required_region"]:
            return False
        if "badges_min" in cond and total_badges < cond["badges_min"]:
            return False
        region_badges = len(self.badges.get(cond.get("required_region") or self.get_current_region(), []))
        if "region_badges_min" in cond and region_badges < cond["region_badges_min"]:
            return False
        if "region_badges_less" in cond and region_badges >= cond["region_badges_less"]:
            return False
        if "badges_less" in cond and total_badges >= cond["badges_less"]:
            return False

        if "badge" in cond and not self.has_badge(cond["badge"]):
            return False

        if "flag" in cond:
            flags = cond["flag"] if isinstance(cond["flag"], list) else [cond["flag"]]
            if not all(self.story_flags.get(f) for f in flags):
                return False
        if "flag_not" in cond:
            flags = cond["flag_not"] if isinstance(cond["flag_not"], list) else [cond["flag_not"]]
            if any(self.story_flags.get(f) for f in flags):
                return False

        if "visited" in cond and not self.story_flags.get(f"visited_{cond['visited']}"):
            return False
        if "visited_not" in cond and self.story_flags.get(f"visited_{cond['visited_not']}"):
            return False

        if "item" in cond:
            items = cond["item"] if isinstance(cond["item"], list) else [cond["item"]]
            if not any(self.inventory.get(it, 0) > 0 for it in items):
                return False

        if "has_pokemon" in cond:
            pids = cond["has_pokemon"] if isinstance(cond["has_pokemon"], list) else [cond["has_pokemon"]]
            owned_ids = {p.id for p in self.player_team if p} | {p.id for p in self.pc_pokemon if p}
            if not any(pid in owned_ids for pid in pids):
                return False

        if "defeated_area" in cond:
            area = cond["defeated_area"]
            a_data = self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(area, {})
            t_pool = a_data.get("trainer_pool", [])
            defeated = self.defeated_trainers.get(area, set())
            if not t_pool or len(defeated) < len(t_pool):
                return False

        if "caught_min" in cond and unique_caught < cond["caught_min"]:
            return False

        if "catch_id" in cond:
            target = str(cond["catch_id"])
            if target == "201":
                actual = sum(1 for k, v in self.catch_counts.items()
                             if (str(k) == "201" or str(k).startswith("201_")) and v > 0)
            else:
                actual = self.catch_counts.get(target, 0)
            if actual < cond.get("catch_count", 1):
                return False

        return True

    def sync_catch_counts(self):
        """
        Scans the player team and PC to ensure all caught species and forms
        are registered in catch_counts and the Pokedex.
        """
        if not hasattr(self, "game") or not self.game.data:
            return

        pokedex = self.game.data.data.get("pokedex", {})

        all_pkmn = self.player_team + [p for p in self.pc_pokemon if p is not None]
        for p in all_pkmn:
            pid_str = str(p.id)

            if pid_str not in pokedex or isinstance(pokedex[pid_str], bool):
                pokedex[pid_str] = {"id": int(p.id), "caught": True}

            if pid_str == "201":
                f_name = "a" if p.form.lower() == "normal" else p.form.lower()
                form_key = f"201_{f_name}"
                if self.catch_counts.get(form_key, 0) == 0:
                    print(f"Sync: Registering Unown form {f_name.upper()} in Report.")
                    self.catch_counts[form_key] = 1
            else:

                if self.catch_counts.get(pid_str, 0) == 0:
                    self.catch_counts[pid_str] = 1

        self.game.data.data["pokedex"] = pokedex

    def is_captured(self, pokemon_id, form="normal"):
        """
        Checks if a specific species (and specific form for Unown) has been caught.
        Used by the UI to display the Pokeball icon in wild encounters.
        """
        pid_str = str(pokemon_id)
        f_lower = form.lower()

        if pid_str == "201":
            search_key = "201_a" if f_lower == "normal" else f"201_{f_lower}"
            return str(search_key) in self.catch_counts

        return pid_str in self.game.data.data.get("pokedex", {})

    @staticmethod
    def champion_flag(region):
        return "beat_champion" if region == "KANTO" else f"beat_{region.lower()}_champion"

    def is_region_champion(self, region):
        return bool(self.story_flags.get(self.champion_flag(region)))

    def enter_region(self, region):
        """Unlock a region's badge case page and Pokédex section the moment the player arrives."""
        if not region:
            return
        self.story_flags[f"unlocked_{region.lower()}_badges"] = True
        self.badges.setdefault(region, [])
        self.visited_region_set.add(region.upper())

    # Canon rival per region (character key = player-trainer sprite), then fallbacks if that one
    # was already used in this save (e.g. the player picked Silver as their Kanto rival).
    REGION_RIVALS = {
        "KANTO": [("BLUE", "blue")], "JOHTO": [("SILVER", "silver"), ("ETHAN", "ethan"), ("LYRA", "lyra")],
        "HOENN": [("MAY", "may"), ("BRENDAN", "brendan"), ("WALLY", "wally")],
        "SINNOH": [("BARRY", "barry"), ("DAWN", "dawn"), ("LUCAS", "lucas")],
        "UNOVA": [("CHEREN", "cheren"), ("BIANCA", "bianca"), ("HUGH", "hugh")],
        "KALOS": [("SERENA", "serena"), ("CALEM", "calem"), ("SHAUNA", "shauna")],
        "ALOLA": [("HAU", "hau"), ("GLADION", "gladion")], "GALAR": [("HOP", "hop"), ("BEDE", "bede")],
        "PALDEA": [("NEMONA", "nemona"), ("ARVEN", "arven")],
    }

    def used_rivals(self):
        """Rival character keys and names already used in this save."""
        keys = {str(r.get("character", "")).lower() for r in self.region_rivals.values()}
        names = {str(r.get("name", "")).upper() for r in self.region_rivals.values()}
        return keys, names

    def record_region_rival(self, region, name, character):
        """The rival for a region, e.g. the one the player picked for their starting region."""
        self.region_rivals[region.upper()] = {"name": name, "character": character,
                                              "starter_id": self.region_rivals.get(region.upper(), {}).get("starter_id")}

    def assign_region_rival(self, region):
        """Give a region its own rival, never one already used in this save (or the player)."""
        region = region.upper()
        if region in self.region_rivals:
            return self.region_rivals[region]
        keys, names = self.used_rivals()
        player = str(getattr(self.game, "player_character", "") or "").lower()
        playable = [c for c in self.game.loader.area_data.get("GAME_CONFIG", {}).get("PLAYABLE_CHARACTERS", [])]
        options = list(self.REGION_RIVALS.get(region, [])) + [(c.upper(), c) for c in playable]
        for name, char in options:
            if char.lower() not in keys and name.upper() not in names and char.lower() != player:
                self.region_rivals[region] = {"name": name, "character": char, "starter_id": None}
                return self.region_rivals[region]
        self.region_rivals[region] = {"name": "RIVAL", "character": "rival", "starter_id": None}
        return self.region_rivals[region]

    def note_rival_starter(self, region=None):
        """Remember the rival's starter for that region (their teams/Champion team use it)."""
        region = (region or self.get_current_region()).upper()
        if self.rival_starter_raw and region in self.region_rivals:
            self.region_rivals[region]["starter_id"] = self.rival_starter_raw.get("id")

    def rival_starter_id(self, region=None, default=4):
        r = self.region_rivals.get((region or self.get_current_region()).upper(), {})
        if r.get("starter_id"):
            return r["starter_id"]
        return self.rival_starter_raw.get("id", default) if self.rival_starter_raw else default

    def sync_rival(self):
        """Point game.rival_name / rival_character at the current region's rival."""
        game = self.game
        start = (self.starting_region or "KANTO").upper()
        if start not in self.region_rivals and getattr(game, "rival_character", None):
            # older saves / the starting region: the rival the player picked at the start
            self.record_region_rival(start, getattr(game, "rival_name", "???"), game.rival_character)
        region = self.get_current_region().upper()
        if region not in self.region_rivals and region in self.REGION_RIVALS:
            self.assign_region_rival(region)
        r = self.region_rivals.get(region)
        if r:
            game.rival_name, game.rival_character = r["name"], r["character"]
            if region != start:
                game.rival_true_name = str(r["name"]).upper()

    def deposit_to_pc(self, pokemon):
        """Put a Pokemon in the first empty PC slot (the PC is 300 slots, None = empty)."""
        slot = next((i for i, p in enumerate(self.pc_pokemon) if p is None), None)
        if slot is None:
            self.pc_pokemon.append(pokemon)
            return len(self.pc_pokemon) - 1
        self.pc_pokemon[slot] = pokemon
        return slot

    def visited_regions(self):
        """Every region this save has been in: the starting region, any recorded visit, and
        (for older saves) any region whose badge page was unlocked on arrival."""
        out = {r.upper() for r in self.visited_region_set}
        if self.starting_region:
            out.add(self.starting_region.upper())
        for flag, on in self.story_flags.items():
            if on and flag.startswith("unlocked_") and flag.endswith("_badges"):
                out.add(flag[len("unlocked_"):-len("_badges")].upper())
        out.discard("NATIONAL_DEX")
        return out

    def move_to_region(self, region):
        """Mom's move after a championship: unlock the region and return the state to switch to."""
        from src.states.overworld import AreaTransitionState
        from src.states.menus import StarterSelectionState
        src = self.get_current_region()
        cfg = self.get_region_start(region)
        self.enter_region(region)
        self.assign_region_rival(region)  # a new rival for the new region (never a repeat)
        self.active_badge_region = region
        self.story_flags[f"moved_to_{region.lower()}"] = True
        self.current_area_key = cfg.get("start_area", self.current_area_key)
        if not self.story_flags.get(f"received_starter_{region.lower()}"):
            return StarterSelectionState(self.game, starter_ids=cfg.get("starters"), region=region)
        text = self.game.assets.game_text
        for key in (f"{region.lower()}_departure_from_{src.lower()}", f"{src.lower()}_departure_to_{region.lower()}"):
            if key in text:
                lines = text[key]
                message = " ".join(lines) if isinstance(lines, list) else lines
                break
        else:
            town = self.game.loader.area_data["STORY_PROGRESSION"].get(cfg.get("start_area"), {}).get("route_name", region.title())
            message = f"Mom found a lovely new home in {town}! Welcome to the {region.title()} region!"
        return AreaTransitionState(self.game, cfg.get("start_area"), initial_message=message.replace("{player_name}", self.game.player_name))

    def has_badge(self, name):
        """True if a badge with this name was earned in any region ("COAL", "Coal_Badge"...)."""
        from src.world.hms import _norm
        want = _norm(name)
        return any(_norm(b) == want for earned in self.badges.values() for b in earned)

    def get_total_badges(self):
        """Total badges earned across all regions."""
        return sum(len(b) for b in self.badges.values())

    def get_math_level(self):
        """Difficulty scales with total badges across all regions."""
        total = self.get_total_badges()
        return self.game.math.resolve_level(self.math_difficulty, "GLOBAL", total)

    def get_math_label(self):
        total = self.get_total_badges()
        return self.game.math.describe(self.math_difficulty, "GLOBAL", total)

    def pick_evolution_branch(self, entries):
        """For branching evolutions, prefer a branch not yet in the Pokédex so every
        branch is reachable (first Kirlia -> Gardevoir, next -> Gallade); random after."""
        if len(entries) <= 1:
            return entries[0]
        caught = {v.get("id") for v in self.game.data.data.get("pokedex", {}).values() if isinstance(v, dict)}
        for entry in entries:
            name = entry.rsplit("_", 1)[0] if "_" in entry else entry
            if self.game.name_to_id.get(name.upper()) not in caught:
                return entry
        import random
        return random.choice(entries)

    def get_region_starts(self):
        """REGION_START configs as (region, cfg) pairs in story order."""
        starts = self.game.loader.area_data.get("REGION_START", {})
        return sorted(starts.items(), key=lambda kv: kv[1].get("order", 99))

    def get_region_start(self, region=None):
        region = (region or self.starting_region).upper()
        return self.game.loader.area_data.get("REGION_START", {}).get(region, {})

    def get_region_gym_badges(self, region):
        """Badge names awarded by a region's gyms, in story order (league excluded)."""
        badges = []
        for area in self.game.loader.area_data.get("STORY_PROGRESSION", {}).values():
            if str(area.get("region") or "").upper() != region:
                continue
            leader = area.get("gym", {}).get("leader")
            if isinstance(leader, dict) and leader.get("badge_reward"):
                badges.append(leader["badge_reward"])
        return badges

    def area_region(self, area_key):
        area = self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(area_key, {})
        return str(area.get("region") or "KANTO").upper()

    def area_has_center(self, area_key):
        area = self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(area_key, {})
        return any(o.get("action") == "HEAL" for o in area.get("explore_options", []) or [])

    def whiteout_destination(self):
        """(area_key, has_center): the last Pokemon Center used in this region,
        otherwise the region's starting town (home)."""
        region = self.get_current_region()
        prog = self.game.loader.area_data.get("STORY_PROGRESSION", {})
        if (self.last_center in prog and self.area_region(self.last_center) == region
                and self.area_has_center(self.last_center)):
            return self.last_center, True
        home = self.get_region_start(region).get("start_area")
        if home not in prog:
            home = self.get_region_start().get("start_area", "PALLET_TOWN")
        return home, self.area_has_center(home)

    def get_current_region(self):
        """
        Determines the region based on the current area key.
        Future-proofed by checking area data first, then prefix.
        """
        area_data = self.get_current_area_data()
        if area_data.get("region"):
            return str(area_data["region"]).upper()

        if "_" in self.current_area_key:
            prefix = self.current_area_key.split("_")[0]
            if prefix in self.badges:
                return prefix

        return "KANTO"

    def mark_area_visited(self, area_key=None):
        """
        Sets the visited flag for the given area.
        Call this in OverworldState's on_enter logic.
        """
        target = area_key if area_key else self.current_area_key
        flag = f"visited_{target}"
        if not self.story_flags.get(flag):
            self.story_flags[flag] = True
            if self.get_current_area_data().get("has_gym"):
                self.sync_badges()

    def _prepare_mission_for_ui(self, mission):
        """Ensures mission data is compatible with UI rendering logic."""
        m_copy = mission.copy()

        m_copy["text"] = m_copy.get("title", m_copy.get("text", "Unknown Mission"))
        m_copy["desc"] = m_copy.get("description", m_copy.get("desc", "No details available."))
        m_copy["details"] = m_copy["desc"]

        cond = mission.get("condition", {})
        if "catch_id" in cond:
            target = str(cond["catch_id"])
            req = cond.get("catch_count", 1)
            if target == "201":
                current = sum(1 for k, v in self.catch_counts.items()
                              if (str(k) == "201" or str(k).startswith("201_")) and v > 0)
            else:
                current = self.catch_counts.get(target, 0)

            prog_text = f"\n(Progress: {current}/{req})"
            m_copy["details"] += prog_text
            m_copy["desc"] += prog_text
            m_copy["text"] += f" ({current}/{req})"

        return m_copy

    def get_unown_report_text(self):
        """Generates a string representation of caught Unown forms for the UI."""
        if self.inventory.get("UNOWN_REPORT", 0) == 0:
            return "You don't have the Unown Report."

        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        caught_forms = []

        for char in alphabet:
            key = f"201_{char.lower()}"
            if self.catch_counts.get(key, 0) > 0:
                caught_forms.append(char)
            elif char == "A" and self.catch_counts.get("201_normal", 0) > 0:
                caught_forms.append(char)
            else:
                caught_forms.append("_")

        if self.catch_counts.get("201_exclamation", 0) > 0:
            caught_forms.append("!")
        if self.catch_counts.get("201_question", 0) > 0:
            caught_forms.append("?")

        formatted_list = " ".join(caught_forms)
        total = sum(1 for c in caught_forms if c != "_")

        return f"UNOWN REPORT - Total Found: {total}/28\n\n{formatted_list}"

    def get_all_journal_entries(self):
        """Returns all missions categorized by Active or Completed status."""
        all_missions = self.region_missions()
        entries = []

        active_missions = self.get_active_missions()
        active_ids = {act["id"] for act in active_missions}

        for m in all_missions:
            cond = m.get("condition", {})
            if "required_region" in cond and self.get_current_region() != cond["required_region"]:
                continue

            status = "INACTIVE"
            is_completed = False

            if m.get("completed_flag"):
                is_completed = self.story_flags.get(m["completed_flag"], False)

            elif "visited" in cond and not m.get("completed_flag"):
                has_visited = self.story_flags.get(f"visited_{cond['visited']}", False)
                is_completed = has_visited and m["type"] == "SIDE"

            if is_completed:
                status = "COMPLETED"
            else:
                if m["id"] in active_ids:
                    status = "ACTIVE"

            if status != "INACTIVE":
                m_copy = self._prepare_mission_for_ui(m)
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

    def cycle_badge_case(self):
        """Cycles the active view for the badge case UI."""
        regions = list(self.badges.keys())
        idx = regions.index(self.active_badge_region)
        self.active_badge_region = regions[(idx + 1) % len(regions)]
        return self.active_badge_region

    def get_current_hint(self):
        """Provides a contextual hint to the player."""
        if self.get_current_region() != "KANTO":
            main = [m for m in self.get_active_missions() if m.get("type") == "MAIN"]
            if main:
                return main[0]["desc"]
            return "Explore the region, earn badges, and become Champion!"
        kanto_badges = self.badges.get("KANTO", [])
        if "BOULDER" not in kanto_badges:
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
        Handles both old format (gym.leader is a dict with badge_reward)
        and new format (gym.leader is a name string, gym.badge is the badge name).
        """
        if not hasattr(self, "game") or not self.game.loader:
            return

        progression = self.game.loader.area_data.get("STORY_PROGRESSION", {})
        for area_key, area_data in progression.items():
            gym = area_data.get("gym")
            if not gym:
                continue
            prog_key = f"gym_progress_{area_key}"
            prog_val = self.story_flags.get(prog_key, 0)
            trainers = gym.get("trainers", [])
            leader = gym.get("leader")

            if leader and prog_val > len(trainers):
                if isinstance(leader, dict):
                    badge = leader.get("badge_reward")
                else:
                    raw = gym.get("badge", "")
                    badge = (raw.upper().replace(" ", "_").replace("'", "")
                             if raw else None)
                region = area_data.get("region", "KANTO")
                if badge and badge not in self.badges.get(region, []):
                    print(f"Sync: Awarding missing {badge} for {area_key}!")
                    self.badges.setdefault(region, []).append(badge)

            if area_key == "INDIGO_PLATEAU" and prog_val > len(trainers):
                if not self.story_flags.get("beat_champion"):
                    self.story_flags["beat_champion"] = True

        self.sync_key_items()
        self.sync_catch_counts()

    def sync_key_items(self):
        """Ensures players have key items unlocked by their earned badges."""
        if not hasattr(self, "inventory") or self.inventory is None:
            self.inventory = {}
        from src.world import hms
        hms.give_for_badges(self)  # HMs from badges already won

        # region_id → list of (badge_name, item) in order earned
        region_badge_items = {
            "KANTO": [
                ("BOULDER", "TOWN_MAP"),
                ("CASCADE", "BIKE_VOUCHER"),
                ("THUNDER", "EXP_SHARE"),
                ("RAINBOW", "COIN_CASE"),
                ("MARSH", "AIR_BALLOON"),
                ("SOUL", "SURF_BOARD"),
                ("VOLCANO", "VOLCANO_PASS"),
                ("EARTH", "CERULEAN_CAVE_MAP"),
            ],
            "JOHTO": [
                ("ZEPHYR", "JOHTO_MAP"),
                ("HIVE", "OLD_ROD"),
                ("PLAIN", "SQUIRT_BOTTLE"),
                ("FOG", "SUPER_ROD"),
                ("STORMBADGE", "AMULET_COIN"),
                ("GLACIER", "ROCK_SMASHER"),
                ("RISING", "MT_SILVER_MAP"),
            ],
            "HOENN": [
                ("STONE_BADGE", "HOENN_MAP"),
                ("KNUCKLE_BADGE", "OLD_ROD"),
                ("DYNAMO_BADGE", "EXP_SHARE"),
                ("HEAT_BADGE", "GO_GOGGLES"),
                ("BALANCE_BADGE", "AMULET_COIN"),
                ("FEATHER_BADGE", "ACRO_BIKE"),
                ("MIND_BADGE", "DIVE_GOGGLES"),
                ("RAIN_BADGE", "HOENN_CAVE_MAP"),
            ],
            "SINNOH": [
                ("COAL_BADGE", "SINNOH_MAP"),
                ("FOREST_BADGE", "OLD_ROD"),
                ("COBBLE_BADGE", "EXP_SHARE"),
                ("FEN_BADGE", "SUPER_ROD"),
                ("RELIC_BADGE", "AMULET_COIN"),
                ("MINE_BADGE", "EXPLORER_KIT"),
                ("ICICLE_BADGE", "MEMBER_CARD"),
                ("BEACON_BADGE", "SINNOH_CAVE_MAP"),
            ],
            "UNOVA": [
                ("TRIO_BADGE", "UNOVA_MAP"),
                ("BASIC_BADGE", "EXP_SHARE"),
                ("INSECT_BADGE", "OLD_ROD"),
                ("BOLT_BADGE", "SUPER_ROD"),
                ("QUAKE_BADGE", "AMULET_COIN"),
                ("JET_BADGE", "DOWSING_MACHINE"),
                ("FREEZE_BADGE", "PERMIT_CARD"),
                ("LEGEND_BADGE", "UNOVA_CAVE_MAP"),
            ],
            "KALOS": [
                ("BUG_BADGE", "KALOS_MAP"),
                ("CLIFF_BADGE", "EXP_SHARE"),
                ("RUMBLE_BADGE", "OLD_ROD"),
                ("PLANT_BADGE", "SUPER_ROD"),
                ("VOLTAGE_BADGE", "AMULET_COIN"),
                ("FAIRY_BADGE", "HOLO_CASTER"),
                ("PSYCHIC_BADGE", "TMV_PASS"),
                ("ICEBERG_BADGE", "MEGA_RING"),
            ],
            "ALOLA": [
                ("MELEMELE_STAMP", "ALOLA_MAP"),
                ("AKALA_STAMP", "EXP_SHARE"),
                ("ULAUA_STAMP", "AMULET_COIN"),
                ("PONI_STAMP", "Z_RING"),
            ],
            "GALAR": [
                ("GRASS_BADGE", "GALAR_MAP"),
                ("WATER_BADGE", "EXP_SHARE"),
                ("FIRE_BADGE", "OLD_ROD"),
                ("FIGHTING_BADGE", "AMULET_COIN"),
                ("FAIRY_BADGE", "ROTOM_BIKE"),
                ("ROCK_BADGE", "SUPER_ROD"),
                ("DARK_BADGE", "CONTRABAND_PASS"),
                ("DRAGON_BADGE", "WYNDON_PASS"),
            ],
            "PALDEA": [
                ("BUG_BADGE", "PALDEA_MAP"),
                ("GRASS_BADGE", "EXP_SHARE"),
                ("ELECTRIC_BADGE", "OLD_ROD"),
                ("WATER_BADGE", "AMULET_COIN"),
                ("NORMAL_BADGE", "SUPER_ROD"),
                ("GHOST_BADGE", "TERA_ORB"),
                ("PSYCHIC_BADGE", "AREA_ZERO_PASS"),
                ("ICE_BADGE", "ACADEMY_ACE_CARD"),
            ],
        }

        def bare(name):
            return name[:-6] if name.endswith("_BADGE") else name

        for region, pairs in region_badge_items.items():
            earned = {bare(b) for b in self.badges.get(region, [])}
            for badge, item in pairs:
                if bare(badge) not in earned:
                    continue
                if self.inventory.get(item, 0) > 0:
                    continue
                if item == "BIKE_VOUCHER" and self.inventory.get("BICYCLE", 0) > 0:
                    continue
                print(f"Sync: Awarding {item} for {badge} ({region})!")
                self.inventory[item] = 1

        if self.story_flags.get("visited_RUINS_OF_ALPH") and self.inventory.get("UNOWN_REPORT", 0) == 0:
            print("Sync: Awarding missing UNOWN_REPORT!")
            self.inventory["UNOWN_REPORT"] = 1

        # The Poke Flute is Mr. Fuji's to give (talk to him in Lavender Town).
        if self.story_flags.get("tower_ghost_defeated"):
            if self.inventory.get("SILPH_SCOPE", 0) == 0:
                print("Sync: Awarding missing SILPH_SCOPE!")
                self.inventory["SILPH_SCOPE"] = 1

    def serialize(self):
        return {
            "current_area_key": self.current_area_key,
            "badges": self.badges,
            "active_badge_region": self.active_badge_region,
            "balls_left": self.balls_left,
            "current_streak": self.current_streak,
            "money": self.money,
            "defeated_trainers": {
                k: list(v) for k, v in self.defeated_trainers.items()
            },
            "story_flags": self.story_flags,
            "catch_counts": self.catch_counts,
            "inventory": self.inventory,
            "poffins": self.poffins,
            "notified_missions": self.notified_missions,
            "player_team": [self._pokemon_record(p) for p in self.player_team if p],
            "pc_pokemon": [self._pokemon_record(p) if p else None for p in self.pc_pokemon],
            "starting_region": self.starting_region,
            "visited_regions": sorted(self.visited_regions()),
            "region_rivals": self.region_rivals,
            "rival_starter_id": (
                self.rival_starter_raw["id"] if self.rival_starter_raw else None
            ),
            "user_rival_starter_id": (
                self.user_rival_starter_raw["id"] if self.user_rival_starter_raw else None
            ),
            "player_name": self.game.player_name,
            "rival_name": getattr(self.game, "rival_name", "BLUE"),
            "rival_true_name": getattr(self.game, "rival_true_name", "BLUE"),
            "math_difficulty": self.math_difficulty,
            "level_cap_mode": self.level_cap_mode,
            "last_center": self.last_center,
            "autosave": self.autosave,
        }

    @staticmethod
    def _migrate_area_keys(obj, renames={"FUSCHIA_CITY": "FUCHSIA_CITY"}):
        """Rewrite renamed area keys anywhere in an older save (keys, values, flag names)."""
        if isinstance(obj, str):
            for old, new in renames.items():
                obj = obj.replace(old, new)
            return obj
        if isinstance(obj, list):
            return [StoryManager._migrate_area_keys(x) for x in obj]
        if isinstance(obj, dict):
            return {StoryManager._migrate_area_keys(k): StoryManager._migrate_area_keys(v)
                    for k, v in obj.items()}
        return obj

    @staticmethod
    def _pokemon_record(p):
        return {
            "id": p.id, "form": p.form, "shiny": p.is_shiny,
            "level": p.level, "xp": p.xp, "friendship": p.friendship, "counters": dict(p.counters),
            "affection": getattr(p, "affection", 0), "everstone": bool(getattr(p, "everstone", False)),
            "ivs": dict(getattr(p, "ivs", {})), "moves": list(getattr(p, "moves", [])),
            "status": getattr(p, "status", None), "sleep_turns": getattr(p, "sleep_turns", 0),
            "hp": p.current_hp, "hp_real": True, "stage": p.stage, "gmax": p.gmax_factor,
            "caught_region": getattr(p, "caught_region", None),
            "condition": p.condition, "sheen": p.sheen, "ribbons": p.ribbons,
        }

    def _apply_record(self, pokemon, p_data, form):
        pokemon.gmax_factor = p_data.get("gmax", form == "gmax")
        pokemon.caught_region = p_data.get("caught_region")
        pokemon.condition.update(p_data.get("condition", {}))
        pokemon.sheen = p_data.get("sheen", 0)
        pokemon.ribbons = list(p_data.get("ribbons", []))
        if "stage" in p_data:
            pokemon.stage = p_data["stage"]
        pokemon.friendship = p_data.get("friendship", 0)
        pokemon.affection = p_data.get("affection", 0)
        pokemon.everstone = bool(p_data.get("everstone", False))
        pokemon.counters = dict(p_data.get("counters", {}))
        if p_data.get("ivs"):
            pokemon.ivs = dict(p_data["ivs"])
        pokemon.moves = list(p_data.get("moves", []))
        pokemon.status = p_data.get("status")
        pokemon.sleep_turns = int(p_data.get("sleep_turns", 2 if pokemon.status == "sleep" else 0))
        old_scale_hp = None
        if "level" in p_data:
            pokemon.level, pokemon.xp = int(p_data["level"]), int(p_data.get("xp", 0))
        else:
            # Saves from before real levels: stage + XP become a matching level.
            xp = p_data.get("xp", p_data.get("wins", 0) * Pokemon.XP_PER_WIN)
            pokemon.level = max(pokemon.level, Pokemon.legacy_level(pokemon.stage, xp))
            pokemon.xp = 0
            old_scale_hp = Pokemon.legacy_hp_scale(pokemon.stage)
        if "hp" in p_data:
            pokemon.current_hp = self._loaded_hp(pokemon, p_data, old_scale_hp)

    @staticmethod
    def _loaded_hp(pokemon, p_data, old_scale_hp=None):
        """Keep the same share of HP across save formats."""
        if p_data.get("hp_real") and old_scale_hp is None:
            return min(p_data["hp"], pokemon.get_max_hp())
        if p_data.get("hp_real"):
            return pokemon.get_max_hp() if p_data["hp"] > 0 else 0
        share = min(1.0, max(0.0, p_data["hp"] / (old_scale_hp or 20)))
        return int(share * pokemon.get_max_hp() + 0.5)

    def deserialize(self, data, loader):
        data = self._migrate_area_keys(data)
        self.starting_region = data.get("starting_region", "KANTO")
        self.visited_region_set = {str(r).upper() for r in data.get("visited_regions", [])}
        self.region_rivals = {str(k).upper(): dict(v) for k, v in (data.get("region_rivals") or {}).items()}
        self.current_area_key = data.get("current_area_key", "PALLET_TOWN")
        raw_badges = data.get("badges", [])
        if isinstance(raw_badges, list):
            self.badges = {"KANTO": raw_badges, "JOHTO": []}
        else:
            self.badges = raw_badges

        self.active_badge_region = data.get("active_badge_region", "KANTO")
        self.defeated_trainers = {
            k: set(v) for k, v in data.get("defeated_trainers", {}).items()
        }
        self.story_flags = data.get("story_flags", {})
        self.story_flags.pop("forced_white_out", None)  # stale flag from old saves
        self.balls_left = data.get("balls_left", 5)
        self.current_streak = data.get("current_streak", 0)
        self.money = data.get("money", 3000)
        self.catch_counts = data.get("catch_counts", {})

        self.inventory = data.get("inventory", {})
        self.poffins = list(data.get("poffins", []))
        self.notified_missions = data.get("notified_missions", [])
        # Older saves have no setting -> AUTO (follows region + badges)
        self.math_difficulty = data.get("math_difficulty", "AUTO")
        self.level_cap_mode = data.get("level_cap_mode", "STORY")
        self.last_center = data.get("last_center")
        self.autosave = data.get("autosave", True)

        self.player_team = []
        for p_data in data.get("player_team", []):
            form = p_data.get("form", "normal")
            raw = loader.fetch_specific(
                p_data["id"],
                form="normal" if form == "gmax" else form,
                is_shiny=p_data.get("shiny", False),
            )
            pokemon = Pokemon(raw, loader.game.assets, size_mult=2.5)
            self._apply_record(pokemon, p_data, form)
            self.player_team.append(pokemon)

        saved_pc = data.get("pc_pokemon", [])
        self.pc_pokemon = [None] * max(300, len(saved_pc))  # keep anything stored past slot 300
        for i, p_data in enumerate(saved_pc):
            if p_data is None:
                continue
            form = p_data.get("form", "normal")
            raw = loader.fetch_specific(
                p_data["id"],
                form="normal" if form == "gmax" else form,
                is_shiny=p_data.get("shiny", False),
            )
            pokemon = Pokemon(raw, loader.game.assets, size_mult=2.5)
            self._apply_record(pokemon, p_data, form)
            self.pc_pokemon[i] = pokemon

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
        
        # ARCHITECT: Check both 'gym' and 'battle' keys for potential lists (used in Leagues)
        for key in ["gym", "battle"]:
            bg_config = backgrounds.get(key)
            if isinstance(bg_config, list):
                if is_leader:
                    return bg_config[-1] if bg_config else None
                else:
                    if 0 <= trainer_index < len(bg_config):
                        return bg_config[trainer_index]
                    else:
                        return bg_config[0]
            elif isinstance(bg_config, str) and key == "gym":
                return bg_config

        if "battle" in backgrounds:
            return backgrounds["battle"]

        return None
