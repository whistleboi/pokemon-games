# [REF-0001: System Imports]
import pygame
import random
import io
import os
import threading
import queue
from src.config import DEFAULT_BASE_STATS


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

    def _get_target_pool(self, pool_type, id_pool):
        """Determines the list of Pokemon IDs to draw from."""
        if id_pool:
            return id_pool
        
        if not id_pool:
            # Lazy load all boss IDs into a set for wild encounter filtering
            if not self.all_boss_ids:
                for key in ["UB", "PAST", "FUTURE", "MYTHICAL", "MEGA", "GMAX", "STANDARD_BOSS"]:
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
            candidates = [f for f in target_map.keys() if f.startswith(f"{p_id_str}_") or f == f"{p_id_str}.png"]
            
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
            
            candidates = [f for f in target_map.keys() if f == f"{p_id_str}.png" or f == f"{p_id_str}_gmax.png"]
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
                        if k.startswith(f"{p_id_str}_") and random.random() < chance:
                            form = k.split("_", 1)[1]
                            break
            
            if form != "normal":
                target_dir = self.assets.alt_sprites_dir
                target_map = self.assets.alt_sprite_map
                target_fname = f"{p_id}_{form}.png"
                
                suffix = form.replace("_", " ").title()
                display_name = f"{name} {suffix.upper()}"

        return form, display_name, target_dir, target_map, target_fname

    def _read_asset_bytes(self, directory, filename):
        """Helper to safely read bytes from a file if it exists."""
        if not filename: return b""
        path = os.path.join(directory, filename)
        if os.path.exists(path) and not os.path.isdir(path):
            try:
                with open(path, "rb") as f:
                    return f.read()
            except:
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
        
        shiny_odds = dev_odds if self.dev_shiny_mode else (charm_odds if self.shiny_charm_active else base_odds)
        
        target_pool = self._get_target_pool(pool_type, id_pool)
        base_form = pool_type.lower() if pool_type in ["MEGA", "GMAX"] else "normal"
        caught_pokedex_keys = set(self.game.data.data["pokedex"].keys())
        max_attempts = 40 if (pool_type or id_pool) else 10

        for _ in range(max_attempts):
            p_id = self._pick_random_id(target_pool)
            if not p_id:
                continue

            # Basic Name Check
            name = self.assets.pokemon_names.get(str(p_id), f"POKEMON_{p_id}").upper()
            if name in exclude_names:
                continue

            # Resolve Form (Mega X/Y, Regional, etc)
            final_form, display_name, t_dir, t_map, t_fname = self._resolve_form_context(
                p_id, base_form, name, area_data
            )
            
            # --- CALCULATE STAGE ---
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
                img_bytes = self._read_asset_bytes(self.assets.shiny_sprites_dir, shiny_fname)
            
            if not img_bytes:
                # Fallback to normal map
                real_fname = t_map.get(t_fname.lower())
                img_bytes = self._read_asset_bytes(t_dir, real_fname)

            # 2. Back Sprite
            if is_shiny:
                shiny_back = self.assets.shiny_back_sprite_map.get(t_fname.lower())
                back_img_bytes = self._read_asset_bytes(self.assets.shiny_back_sprites_dir, shiny_back)

            if not back_img_bytes:
                real_back = self.assets.back_sprite_map.get(t_fname.lower())
                back_img_bytes = self._read_asset_bytes(self.assets.back_sprites_dir, real_back)

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
            # --- META ALIASING ---
            meta_id = 105 if p_id == 10500 else p_id

            base_name = self.assets.pokemon_names.get(
                str(meta_id), f"POKEMON_{p_id}"
            ).upper()

            if (
                form
                and form != "normal"
                and not form.startswith("mega")
                and form != "gmax"
            ):
                display_name = f"{form} {base_name}"
            else:
                display_name = base_name

            stage = self.get_stage(base_name)
            
            # Try to fetch form-specific moveset data first
            moveset_key = str(meta_id)
            if form and form != "normal":
                form_key = f"{meta_id}_{form.lower()}"
                if form_key in self.assets.movesets:
                    moveset_key = form_key
            
            moveset_data = self.assets.movesets.get(moveset_key, {})
            # Fallback to base ID if form data missing
            if not moveset_data and str(meta_id) in self.assets.movesets:
                moveset_data = self.assets.movesets[str(meta_id)]

            p_types = moveset_data.get("types", [])
            
            # Hardcoded Type Overrides for Kanto Alolan Forms (if JSON missing them)
            if form == "alolan":
                if p_id in [19, 20]: p_types = ["DARK", "NORMAL"] # Rattata/Raticate
                elif p_id == 26: p_types = ["ELECTRIC", "PSYCHIC"] # Raichu
                elif p_id in [27, 28]: p_types = ["ICE", "STEEL"] # Sandshrew/Sandslash
                elif p_id == 37: p_types = ["ICE"] # Vulpix
                elif p_id == 38: p_types = ["ICE", "FAIRY"] # Ninetales
                elif p_id in [50, 51]: p_types = ["GROUND", "STEEL"] # Diglett/Dugtrio
                elif p_id in [52, 53]: p_types = ["DARK"] # Meowth/Persian
                elif p_id in [74, 75, 76]: p_types = ["ROCK", "ELECTRIC"] # Geodude line
                elif p_id in [88, 89]: p_types = ["POISON", "DARK"] # Grimer/Muk
                elif p_id == 103: p_types = ["GRASS", "DRAGON"] # Exeggutor
                elif p_id == 105: p_types = ["FIRE", "GHOST"] # Marowak

            p_stats = moveset_data.get("stats", DEFAULT_BASE_STATS)

            img_bytes = b""
            img_surface = self.assets.get_pokemon_image(p_id, form, is_shiny)
            if img_surface:
                img_buffer = io.BytesIO()
                pygame.image.save(img_surface, img_buffer, "sprite.png")
                img_bytes = img_buffer.getvalue()

            back_img_bytes = b""
            if form and form != "normal":
                form_fname = f"{p_id}_{form.lower()}.png"
                back_path = self.assets.back_sprite_map.get(form_fname.lower())
                if back_path and os.path.exists(
                    os.path.join(self.assets.back_sprites_dir, back_path)
                ):
                    with open(
                        os.path.join(self.assets.back_sprites_dir, back_path), "rb"
                    ) as f:
                        back_img_bytes = f.read()

            if not back_img_bytes:
                standard_fname = f"{p_id}.png"
                back_path = self.assets.back_sprite_map.get(standard_fname.lower())
                if not back_path:
                    padded_fname = f"{int(p_id):03d}.png"
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
                "name": base_name,
                "display_name": display_name,
                "img": img_bytes,
                "back_img": back_img_bytes,
                "cry": cry_bytes,
                "is_shiny": is_shiny,
                "form": form,
                "stage": stage,
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

    def get_stage(self, species_name):
        if not hasattr(self, "reverse_evo_map"):
            self.reverse_evo_map = {}
            for base, evos in self.evolution_map.items():
                if base == "OVERRIDES": continue
                if base == "ITEM_LOCKS": continue
                if base == "EVOLUTION_ITEMS": continue
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

                b_type = random.choice(
                    ["STANDARD", "UB", "PAST", "FUTURE", "MYTHICAL", "GMAX", "MEGA"]
                )
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
