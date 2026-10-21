# [REF-0001: System Imports]
import pygame
import random
import io
import os
import threading
import queue
from src.config import DEFAULT_BASE_STATS
from src.world import regional_forms


# [REF-0013: Pokemon Loader]
class PokemonLoader:
    def __init__(self, game):
        self.game = game
        self.assets = game.assets
        self.evolution_map = {}
        self.area_data = {"STORY_PROGRESSION": {}}
        self.queue = queue.Queue(maxsize=2)
        self.last_served_names = set()
        self.shiny_charm_active = False
        self.dev_shiny_mode = False
        self.total_caught = 0
        self.running = True
        self.all_boss_ids = set()
        self.thread = None

    def start(self):
        """Starts the background loading thread. Call this AFTER loading area_data."""
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def get_special_id(self, key, default=None):
        """Retrieves a special species ID from GAME_CONFIG. Prevents hardcoding in states."""
        config = self.area_data.get("GAME_CONFIG", {})
        targets = config.get("SPECIAL_EVOLUTION_TARGETS", {})
        return targets.get(key, default)

    def _get_target_pool(self, pool_type, id_pool):
        """Determines the list of Pokemon IDs to draw from."""
        if id_pool:
            return id_pool

        if not id_pool:
            # Lazy load all boss IDs into a set for wild encounter filtering
            if not self.all_boss_ids:
                boss_keys = ["UB", "PAST", "FUTURE", "MYTHICAL",
                             "MEGA", "GMAX", "STANDARD_BOSS"]
                for key in boss_keys:
                    ids = self.area_data.get(key, [])
                    self.all_boss_ids.update(ids)

        pools = {
            "UB": self.area_data.get("UB", []),
            "PAST": self.area_data.get("PAST", []),
            "FUTURE": self.area_data.get("FUTURE", []),
            "MYTHICAL": self.area_data.get("MYTHICAL", []),
            "MEGA": self.area_data.get("MEGA", []),
            "GMAX": self.area_data.get("GMAX", []),
            "STANDARD": self.area_data.get("STANDARD_BOSS", []),
        }
        return pools.get(pool_type)

    def _pick_random_id(self, target_pool):
        """Selects an ID from the pool or a random wild ID."""
        if target_pool:
            return random.choice(target_pool)

        # Wild encounter logic: exclude boss IDs from random pool
        p_id = random.randint(1, 1025)
        # Ensure set is populated
        if not self.all_boss_ids:
            for key in ["UB", "PAST", "FUTURE", "MYTHICAL", "MEGA", "GMAX", "STANDARD_BOSS"]:
                ids = self.area_data.get(key, [])
                self.all_boss_ids.update(ids)

        if p_id in self.all_boss_ids:
            return None
        return p_id

    def _resolve_form_context(self, p_id, base_form, name, area_data):
        """Resolves specific form details (Mega X/Y, Alt forms) and sprite targets."""
        p_id_str = str(p_id)
        form = base_form
        display_name = name

        target_dir = self.assets.pokemon_sprites_dir
        target_map = self.assets.sprite_map
        target_fname = f"{p_id}.png"

        # ARCHITECT: Priority handling for Numbered/Smart IDs (>= 2000)
        # These use the standard sprite directory and the ID itself as the filename.
        if p_id >= 2000:
            form_map = self.area_data.get("FORM_MAP", {})
            mapping = form_map.get(str(p_id), {})
            form = mapping.get("form", base_form)
            
            suffix = form.replace("_", " ").upper()
            display_name = f"{suffix} {name}" if suffix not in name.upper() else name
            
            return form, display_name, target_dir, target_map, target_fname

        # Auto-detect padded filenames in loader (001.png vs 1.png)
        if base_form == "normal" and target_fname not in target_map:
            padded_name = f"{p_id:03d}.png"
            if padded_name in target_map:
                target_fname = padded_name

        # --- MEGA EVOLUTION ---
        if base_form == "mega":
            target_dir = self.assets.mega_sprites_dir
            target_map = self.assets.mega_sprite_map

            # Find all possible mega files (e.g. 6_x.png, 6_y.png)
            keys = target_map.keys()
            candidates = [f for f in keys if f.startswith(f"{p_id_str}_")
                          or f == f"{p_id_str}.png"]

            if candidates:
                chosen_key = random.choice(candidates)
                target_fname = target_map[chosen_key]

                # Extract specific form (mega_x, mega_y)
                base_file = chosen_key.rsplit(".", 1)[0]
                suffix = base_file[len(p_id_str):]
                form = f"mega{suffix}"

                if suffix:
                    clean_suffix = suffix.replace("_", " ").upper().strip()
                    display_name = f"MEGA {name} {clean_suffix}"
                else:
                    display_name = f"MEGA {name}"
            else:
                # Fallback
                return form, display_name, target_dir, target_map, target_fname

        # --- GIGANTAMAX ---
        elif base_form == "gmax":
            target_dir = self.assets.gmax_sprites_dir
            target_map = self.assets.gmax_sprite_map
            display_name = f"GMAX {name}"

            keys = target_map.keys()
            candidates = [f for f in keys if f == f"{p_id_str}.png"
                          or f == f"{p_id_str}_gmax.png"]
            if candidates:
                target_fname = target_map[random.choice(candidates)]

        # --- NORMAL / REGIONAL / ALT ---
        elif base_form == "normal":
            # Check Area Data for Regional Forms (e.g., Alolan Rattata)
            if area_data:
                alt_config = area_data.get("alt_forms")
                if alt_config and alt_config.get("enabled"):
                    weights = alt_config.get("weights", {})
                    for k, chance in weights.items():
                        if (k.startswith(f"{p_id_str}_") and random.random() < chance
                                and regional_forms.form_allowed(self.game, k.split("_", 1)[1])):
                            form = k.split("_", 1)[1]
                            break

            if form != "normal":
                if p_id == 201:
                    target_fname = f"201-{form}.png"
                else:
                    target_dir = self.assets.alt_sprites_dir
                    target_map = self.assets.alt_sprite_map
                    target_fname = f"{p_id}_{form}.png"

                # ARCHITECT: Prevent double-naming variants (e.g. Alolan Alolan Rattata)
                suffix = form.replace("_", " ").upper()
                display_name = f"{suffix} {name}" if suffix not in name.upper() else name

        return form, display_name, target_dir, target_map, target_fname

    def _read_asset_bytes(self, directory, filename):
        """Helper to safely read bytes from a file if it exists."""
        if not filename:
            return b""
        path = os.path.join(directory, filename)
        if os.path.exists(path) and not os.path.isdir(path):
            try:
                with open(path, "rb") as f:
                    return f.read()
            except (OSError, IOError):
                pass
        return b""

    def _fetch_raw(
        self, pool_type=None, exclude_names=None, id_pool=None, area_data=None
    ):
        """Main fetching logic - Optimized and Refactored."""
        if exclude_names is None:
            exclude_names = set()

        odds_config = self.area_data.get("GAME_CONFIG", {}).get("SHINY_ODDS", {})
        base_odds = odds_config.get("BASE", 0.01)
        charm_odds = odds_config.get("CHARM", 0.02)
        dev_odds = odds_config.get("DEV", 0.25)

        if self.dev_shiny_mode:
            shiny_odds = dev_odds
        else:
            shiny_odds = (charm_odds if self.shiny_charm_active
                          else base_odds)
            if self.game.story_manager.inventory.get("SHINY_CHARM", 0) > 0:
                shiny_odds *= 3  # the Shiny Charm (all of Kanto and Johto caught), as in the games

        target_pool = self._get_target_pool(pool_type, id_pool)
        base_form = pool_type.lower() if pool_type in ["MEGA", "GMAX"] else "normal"
        caught_pokedex_keys = set(self.game.data.data["pokedex"].keys())
        max_attempts = 40 if (pool_type or id_pool) else 10

        for _ in range(max_attempts):
            p_id = self._pick_random_id(target_pool)
            if not p_id:
                continue

            # ARCHITECT: Resolve Smart IDs (>=2000) from FORM_MAP before asset resolution.
            # This ensures regional variants in wild pools use the correct base ID for sprite lookups.
            form_map = self.area_data.get("FORM_MAP", {})
            mapping = form_map.get(str(p_id))

            lookup_id = p_id
            lookup_form = base_form
            name = ""

            if mapping:
                lookup_id = mapping.get("id", p_id)
                lookup_form = mapping.get("form", base_form)
                name = mapping.get("name", "").upper()

            if not name:
                name = self.assets.pokemon_names.get(str(lookup_id), f"POKEMON_{lookup_id}").upper()

            if name in exclude_names:
                continue

            resolved = self._resolve_form_context(lookup_id, lookup_form, name, area_data)
            final_form, display_name, t_dir, t_map, t_fname = resolved

            # --- CALCULATE STAGE ---
            if p_id in self.all_boss_ids:
                stage = 3
            else:
                stage = self.get_stage(name)

            # Check if this specific form is already caught (for Bosses/Legends)
            p_key = f"{p_id}-{final_form}"
            if pool_type is not None and p_key in caught_pokedex_keys:
                continue

            # Determine Assets (Front/Back/Cry)
            is_shiny = random.random() < shiny_odds

            img_bytes = b""
            back_img_bytes = b""

            # 1. Front Sprite
            if is_shiny and t_dir == self.assets.pokemon_sprites_dir:
                # Check standard shiny map
                shiny_fname = self.assets.shiny_sprite_map.get(t_fname.lower())
                s_dir = self.assets.shiny_sprites_dir
                img_bytes = self._read_asset_bytes(s_dir, shiny_fname)

            if not img_bytes:
                # Fallback to normal map
                real_fname = t_map.get(t_fname.lower())
                img_bytes = self._read_asset_bytes(t_dir, real_fname)

            # 2. Back Sprite
            if is_shiny:
                shiny_back = self.assets.shiny_back_sprite_map.get(t_fname.lower())
                sb_dir = self.assets.shiny_back_sprites_dir
                back_img_bytes = self._read_asset_bytes(sb_dir, shiny_back)

            if not back_img_bytes:
                real_back = self.assets.back_sprite_map.get(t_fname.lower())
                b_dir = self.assets.back_sprites_dir
                back_img_bytes = self._read_asset_bytes(b_dir, real_back)

            # 3. Cry
            cry_bytes = b""
            cry_fname_simple = f"{p_id}.ogg"
            cry_fname_pad = f"{p_id:04d}.ogg"
            real_cry = self.assets.cry_map.get(cry_fname_simple.lower()) or \
                self.assets.cry_map.get(cry_fname_pad.lower())
            cry_bytes = self._read_asset_bytes(self.assets.cries_dir, real_cry)

            # 4. Stats & Types
            moveset_data = self.assets.movesets.get(str(p_id), {})

            return {
                "id": p_id,
                "name": name,
                "display_name": display_name,
                "img": img_bytes,
                "back_img": back_img_bytes,
                "cry": cry_bytes,
                "is_shiny": is_shiny,
                "form": final_form,
                "stage": stage,
                "meta_id": lookup_id,
                "level": self.default_level(lookup_id),
                "types": moveset_data.get("types", []),
                "stats": moveset_data.get("stats", DEFAULT_BASE_STATS),
            }

        return {
            "id": 0,
            "name": "MISSINGNO",
            "display_name": "MISSINGNO",
            "img": b"",
            "back_img": b"",
            "cry": b"",
            "is_shiny": False,
            "form": "normal",
            "types": [],
            "stats": {},
        }

    def fetch_specific(self, p_id, form="normal", is_shiny=False):
        """Fetches data for a specific Pokemon ID with proper regional form support."""
        try:
            # --- SMART NUMBERING & META ALIASING ---
            form_map = self.area_data.get("FORM_MAP", {})

            # ARCHITECT: Resolve Smart ID if provided Base ID + Form (handles evolutions like Galarian Ponyta)
            actual_id = p_id
            if p_id < 2000 and form != "normal":
                for sid, m in form_map.items():
                    if m.get("id") == p_id and m.get("form") == form:
                        actual_id = int(sid)
                        break

            meta_id = actual_id
            mapping = form_map.get(str(actual_id))
            name_override = None
            json_types = None

            if mapping:
                meta_id = mapping.get("id", p_id)
                form = mapping.get("form", "normal")
                name_override = mapping.get("name")
                json_types = mapping.get("types")

            elif 10100 <= p_id <= 10105:
                story = self.game.story_manager
                badges = story.get_total_badges()
                stage_offset = 0
                if badges >= 6:
                    stage_offset = 2
                elif badges >= 3:
                    stage_offset = 1

                if p_id == 10100:
                    rid = story.rival_starter_id("KANTO", 4) if hasattr(story, "rival_starter_id") else 4
                    meta_id = rid + stage_offset
                elif p_id == 10101:
                    meta_id = 16 + stage_offset
                elif p_id == 10102:
                    if badges < 6:
                        meta_id = 19 + min(stage_offset, 1)
                    else:
                        meta_id = 111 + (stage_offset - 2)
                elif p_id == 10103:
                    meta_id = 63 + stage_offset
                elif p_id == 10104:
                    rid = story.rival_starter_id("KANTO", 4) if hasattr(story, "rival_starter_id") else 4
                    map_4 = {1: 58, 4: 129, 7: 102}
                    base = map_4.get(rid, 58)
                    meta_id = base + min(stage_offset, 1) if base != 129 else (129 if stage_offset == 0 else 130)
                elif p_id == 10105:
                    rid = story.rival_starter_id("KANTO", 4) if hasattr(story, "rival_starter_id") else 4
                    map_5 = {1: 129, 4: 102, 7: 58}
                    base = map_5.get(rid, 129)
                    meta_id = base + min(stage_offset, 1) if base != 129 else (129 if stage_offset == 0 else 130)
            elif p_id == 3022:
                meta_id = 3022
                base_name = "NOWN"
                form = "normal"
                stage = 3

            else:
                if p_id == 10500:
                    meta_id = 105
                elif 10000 <= p_id <= 10005:
                    meta_id = 151
                elif p_id >= 11000 and p_id % 100 == 0:
                    meta_id = p_id // 100

            if not self.all_boss_ids:
                boss_keys = ["UB", "PAST", "FUTURE", "MYTHICAL", "MEGA", "GMAX", "STANDARD_BOSS"]
                for key in boss_keys:
                    ids = self.area_data.get(key, [])
                    self.all_boss_ids.update(ids)

            overrides = self.area_data.get("POKEMON_NAME_OVERRIDES", {})
            if name_override:
                base_name = name_override.upper()
            elif str(p_id) in overrides:
                base_name = overrides[str(p_id)].upper()
            else:
                pkmn_names = self.assets.pokemon_names
                base_name = pkmn_names.get(str(meta_id), f"POKEMON_{p_id}").upper()

            if (
                form
                and form != "normal"
                and not form.startswith("mega")
                and form != "gmax"
            ):
                form_upper = form.upper()
                display_name = f"{form_upper} {base_name}" if form_upper not in base_name.upper() else base_name
            else:
                display_name = base_name

            if meta_id in self.all_boss_ids or p_id in self.all_boss_ids:
                stage = 3
            else:
                stage = self.get_stage(base_name)

            moveset_key = str(meta_id)
            if form and form != "normal":
                form_key = f"{meta_id}_{form.lower()}"
                if form_key in self.assets.movesets:
                    moveset_key = form_key

            moveset_data = self.assets.movesets.get(moveset_key, {})
            if not moveset_data and str(meta_id) in self.assets.movesets:
                moveset_data = self.assets.movesets[str(meta_id)]

            p_types = moveset_data.get("types", [])

            if json_types:
                p_types = json_types

            if 10000 <= p_id <= 10005:
                types_pool = [
                    "NORMAL", "FIRE", "WATER", "ELECTRIC", "GRASS", "ICE",
                    "FIGHTING", "POISON", "GROUND", "FLYING", "PSYCHIC", "BUG",
                    "ROCK", "GHOST", "STEEL", "DARK", "FAIRY"
                ]
                p_types = ["DRAGON", random.choice(types_pool)]

            p_stats = moveset_data.get("stats", DEFAULT_BASE_STATS)

            img_bytes = b""
            # Form art first, then the base species' form art, then its normal art (forms without sprites).
            img_surface = (self.assets.get_pokemon_image(actual_id, form, is_shiny, placeholder=False)
                           or self.assets.get_pokemon_image(meta_id, form, is_shiny, placeholder=False)
                           or self.assets.get_pokemon_image(meta_id, "normal", is_shiny))

            if img_surface:
                img_buffer = io.BytesIO()
                pygame.image.save(img_surface, img_buffer, "sprite.png")
                img_bytes = img_buffer.getvalue()

            back_img_bytes = b""

            # Priority 1: Smart ID (e.g., 2022.png)
            back_fname = f"{actual_id}.png" 

            if is_shiny:
                shiny_back = self.assets.shiny_back_sprite_map.get(back_fname.lower())
                if not shiny_back:
                    # Fallback for padded IDs in shiny back map
                    shiny_back = self.assets.shiny_back_sprite_map.get(f"{int(actual_id):03d}.png")
                
                if shiny_back:
                    sb_path = os.path.join(self.assets.shiny_back_sprites_dir, shiny_back)
                    if os.path.exists(sb_path):
                        with open(sb_path, "rb") as f:
                            back_img_bytes = f.read()

            if not back_img_bytes:
                back_path = self.assets.back_sprite_map.get(back_fname.lower())
                if not back_path:
                    # Fallback for padded IDs in standard back map
                    back_path = self.assets.back_sprite_map.get(f"{int(actual_id):03d}.png")
                
                if back_path and os.path.exists(os.path.join(self.assets.back_sprites_dir, back_path)):
                    with open(os.path.join(self.assets.back_sprites_dir, back_path), "rb") as f:
                        back_img_bytes = f.read()

            # Priority 2: Legacy Form Suffix (e.g., 79_galarian.png) - Fallback only
            if not back_img_bytes and form and form != "normal" and actual_id < 2000:
                sep = "-" if meta_id == 201 else "_"
                form_fname = f"{meta_id}{sep}{form.lower()}.png"
                back_path = self.assets.back_sprite_map.get(form_fname.lower())
                if back_path and os.path.exists(
                    os.path.join(self.assets.back_sprites_dir, back_path)
                ):
                    with open(
                        os.path.join(self.assets.back_sprites_dir, back_path), "rb"
                    ) as f:
                        back_img_bytes = f.read()

            if not back_img_bytes:
                standard_fname = f"{meta_id}.png"
                back_path = self.assets.back_sprite_map.get(standard_fname.lower())
                if not back_path:
                    padded_fname = f"{int(meta_id):03d}.png"
                    back_path = self.assets.back_sprite_map.get(padded_fname)
                if back_path and os.path.exists(
                    os.path.join(self.assets.back_sprites_dir, back_path)
                ):
                    with open(
                        os.path.join(self.assets.back_sprites_dir, back_path), "rb"
                    ) as f:
                        back_img_bytes = f.read()

            cry_bytes = b""
            cry_path = self.assets.get_cry(meta_id)
            if cry_path and os.path.exists(cry_path):
                with open(cry_path, "rb") as f:
                    cry_bytes = f.read()

            return {
                "id": p_id,
                "meta_id": meta_id,
                "name": base_name,
                "display_name": display_name,
                "img": img_bytes,
                "back_img": back_img_bytes,
                "cry": cry_bytes,
                "is_shiny": is_shiny,
                "form": form,
                "stage": stage,
                "level": self.default_level(meta_id),
                "types": p_types,
                "stats": p_stats,
            }
        except Exception as e:
            print(f"Error in fetch_specific for ID {p_id} (form={form}): {e}")
            return {
                "id": 0,
                "name": "MISSINGNO",
                "display_name": "MISSINGNO",
                "img": b"",
                "back_img": b"",
                "cry": b"",
                "is_shiny": False,
                "form": "normal",
                "types": [],
                "stats": {},
            }

    ITEM_ALIASES = {"UP_GRADE": "UPGRADE"}

    def load_level_data(self, assets_dir):
        """Real levels: evolution rules, minimum levels and learnsets (assets/pokemon_levels.json).
        Item evolutions from it join EVOLUTION_ITEMS (so marts stock the items), without
        replacing the stand-ins the region data already uses."""
        import json
        path = os.path.join(assets_dir, "pokemon_levels.json")
        try:
            with open(path, encoding="utf-8") as f:
                self.level_data = json.load(f)
        except OSError:
            self.level_data = {}
            return
        # One spelling per item: the level data says UP_GRADE, the item tables say UPGRADE.
        for rule in self.level_data.get("pairs", {}).values():
            if rule.get("item") in self.ITEM_ALIASES:
                rule["item"] = self.ITEM_ALIASES[rule["item"]]
        names = self.assets.pokemon_names
        items = self.evolution_map.setdefault("EVOLUTION_ITEMS", {})
        have = {(src.upper(), dst.split("_")[0].upper()) for table in items.values() for src, dst in table.items()}
        for pair, rule in self.level_data.get("pairs", {}).items():
            if "item" not in rule:
                continue
            a, b = pair.split(">")
            src, dst = names.get(a, "").upper(), names.get(b, "").upper()
            if src and dst and (src, dst) not in have:
                items.setdefault(rule["item"], {})[src] = dst

    def default_level(self, p_id):
        """Level for a newly made Pokemon: legendaries at their fixed level, others at the
        lowest level the species shows up (its evolution level, or Lv 5)."""
        from src.pokemon.balance import is_legendary
        from src.world.levels import legendary_level
        if is_legendary(p_id):
            return legendary_level(p_id)
        mins = getattr(self, "level_data", {}).get("min_level", {})
        return max(5, int(mins.get(str(p_id), 5)))

    def get_stage(self, species_name):
        if not hasattr(self, "reverse_evo_map"):
            self.reverse_evo_map = {}
            for base, evos in self.evolution_map.items():
                if base == "OVERRIDES":
                    continue
                if base == "ITEM_LOCKS":
                    continue
                if base == "EVOLUTION_ITEMS":
                    continue
                for evo in evos:
                    self.reverse_evo_map[evo] = base

        name = species_name.upper()
        if name not in self.reverse_evo_map:
            return 1
        parent = self.reverse_evo_map[name]
        if parent not in self.reverse_evo_map:
            return 2
        return 3

    def _worker(self):
        while self.running:
            if not self.queue.full():
                p_list = []
                current_batch_names = set()
                for _ in range(3):
                    p = self._fetch_raw(
                        None, exclude_names=self.last_served_names | current_batch_names
                    )
                    if p:
                        p_list.append(p)
                        current_batch_names.add(p["name"])

                b_type = random.choice(["STANDARD", "MYTHICAL"])
                boss_p = self._fetch_raw(b_type)

                if len(p_list) == 3 and boss_p:
                    self.queue.put(
                        {
                            "normal": p_list,
                            "boss": boss_p,
                            "names": current_batch_names,
                            "boss_type": b_type,
                        }
                    )
            pygame.time.wait(200)
