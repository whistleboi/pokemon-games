# [REF-0011: Asset Manager]
import os
import pygame
import random
import base64
import io
import sys
import json
from src.utils import Utils, MultiFont
from src.config import POKEMON_GSC_BASE64, WHITE, VOLUME, RED


class AssetManager:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        script_dir = os.path.dirname(os.path.abspath(__file__))

        possible_dirs = [
            script_dir,
            os.path.dirname(script_dir),
            os.path.dirname(os.path.dirname(script_dir)),
        ]

        self.assets_dir = None
        for base in possible_dirs:
            candidate = os.path.join(base, "assets")
            if os.path.exists(candidate):
                self.assets_dir = candidate
                self.base_dir = base
                break

        if not self.assets_dir:
            self.assets_dir = os.path.join(script_dir, "assets")
            self.base_dir = script_dir

        print(f"DEBUG: Script running from → {script_dir}")
        print(f"DEBUG: Assets folder found at → {self.assets_dir}")

        if os.path.exists(self.assets_dir):
            visible = os.listdir(self.assets_dir)
            json_files = [f for f in visible if f.endswith(".json")]
            msg = f"✓ Assets folder FOUND! {len(visible)} items "
            print(
                msg +
                f"({len(json_files)} JSON files)"
            )
            print(f"   JSONs: {json_files}")
        else:
            print(f"✗ CRITICAL: Assets folder missing at {self.assets_dir}")

        self.sprites_dir = Utils.get_actual_path(self.assets_dir, "sprites")
        self.pokemon_sprites_dir = Utils.get_actual_path(
            self.sprites_dir, "pokemon"
        )
        self.back_sprites_dir = Utils.get_actual_path(
            self.pokemon_sprites_dir, "back"
        )
        self.shiny_back_sprites_dir = Utils.get_actual_path(
            self.back_sprites_dir, "shiny"
        )
        self.shiny_sprites_dir = Utils.get_actual_path(
            self.pokemon_sprites_dir, "shiny"
        )
        self.mega_sprites_dir = Utils.get_actual_path(
            self.pokemon_sprites_dir, "mega")
        self.gmax_sprites_dir = Utils.get_actual_path(
            self.pokemon_sprites_dir, "gmax")
        self.alt_sprites_dir = Utils.get_actual_path(
            self.pokemon_sprites_dir, "altform"
        )
        self.items_sprites_dir = Utils.get_actual_path(
            self.sprites_dir, "items")
        self.trainers_dir = Utils.get_actual_path(self.assets_dir, "trainers")

        if not os.path.exists(self.trainers_dir):
            check_path = Utils.get_actual_path(self.sprites_dir, "trainers")
            if os.path.exists(check_path):
                self.trainers_dir = check_path
        self.player_trainers_dir = Utils.get_actual_path(
            self.trainers_dir, "player")
        self.backgrounds_dir = Utils.get_actual_path(
            self.assets_dir, "backgrounds")
        self.kanto_backgrounds_dir = Utils.get_actual_path(
            self.backgrounds_dir, "kanto"
        )
        self.johto_backgrounds_dir = Utils.get_actual_path(
            self.backgrounds_dir, "johto"
        )
        self.battle_backgrounds_dir = Utils.get_actual_path(
            self.backgrounds_dir, "battle"
        )
        self.overworld_dir = Utils.get_actual_path(
            self.assets_dir, "overworld")
        self.sounds_dir = Utils.get_actual_path(self.assets_dir, "sounds")
        if not os.path.exists(self.sounds_dir):
            self.sounds_dir = Utils.get_actual_path(
                self.pokemon_sprites_dir, "sounds")
        self.cries_dir = Utils.get_actual_path(self.sounds_dir, "cries")

        self.sprite_map = Utils.index_files(self.pokemon_sprites_dir)
        self.back_sprite_map = Utils.index_files(self.back_sprites_dir)
        self.shiny_back_sprite_map = Utils.index_files(
            self.shiny_back_sprites_dir)
        self.shiny_sprite_map = Utils.index_files(self.shiny_sprites_dir)
        self.mega_sprite_map = Utils.index_files(self.mega_sprites_dir)
        self.gmax_sprite_map = Utils.index_files(self.gmax_sprites_dir)
        self.alt_sprite_map = Utils.index_files(self.alt_sprites_dir)
        self.cry_map = Utils.index_files(self.cries_dir)
        self.item_map = Utils.index_files(self.items_sprites_dir)
        self.trainer_map = Utils.index_files(self.trainers_dir)
        
        # ARCHITECT: Use recursive indexing for battle backgrounds to support nested 
        # regional, gym, and elite folders automatically.
        self.battle_bg_map = {}
        for root, _, files in os.walk(self.battle_backgrounds_dir):
            for f in files:
                if f.lower().endswith(".png"):
                    self.battle_bg_map[f.lower()] = os.path.relpath(os.path.join(root, f), self.battle_backgrounds_dir)

        self.kanto_bg_map = Utils.index_files(self.kanto_backgrounds_dir)
        self.johto_bg_map = Utils.index_files(self.johto_backgrounds_dir)
        self.badges_dir = Utils.get_actual_path(self.assets_dir, "badges")
        self.player_trainer_map = Utils.index_files(self.player_trainers_dir)
        self.sound_map = Utils.index_files(self.sounds_dir)

        self.font_path = Utils.get_actual_path(
            self.assets_dir, "pokemon_gsc.ttf.ttf")
        is_android = ("ANDROID_ARGUMENT" in os.environ or
                      "ANDROID_PRIVATE" in os.environ)
        self.is_pc = (
            sys.platform in ["win32", "linux", "darwin"]) and not is_android
        self.font_scale = 0.5 if self.is_pc else 1.0
        self.fonts = {
            "big": self._load_font(int(
                width * 0.065 * self.font_scale), bold=True),
            "med": self._load_font(int(
                width * 0.06 * self.font_scale), bold=True),
            "s_med": self._load_font(int(
                width * 0.04 * self.font_scale), bold=True),
            "num": self._load_font(int(
                width * 0.06 * self.font_scale), bold=True),
            "small": self._load_font(int(
                width * 0.02 * self.font_scale), bold=True),
            "tiny": self._load_font(int(
                width * 0.015 * self.font_scale), bold=True),
        }

        self.ball_imgs = self._load_balls()
        self.ui_ball = pygame.transform.scale(
            self.ball_imgs[0], (int(width * 0.04), int(width * 0.04))
        )
        self.go_img = self._load_go_img()

        self.shiny_sfx = self._load_sound("shiny.ogg")
        self.heal_sfx = self._load_sound("heal.ogg")
        self.music_playlist = self._load_music()
        self.game_text = {}

        self.movesets = {}
        self.pokemon_names = self._load_pokemon_data()

    def get_pokemon_image(self, p_id, form, is_shiny, placeholder=True):
        """Retreives the correct sprite surface from assets based on
        metadata."""
        target_dir = self.pokemon_sprites_dir
        target_map = self.sprite_map
        fname_lower = f"{p_id}.png"

        if p_id >= 2000 and fname_lower in target_map:
            form = "normal"

        if form == "normal" and fname_lower not in target_map:
            padded_name = f"{int(p_id):03d}.png"
            if padded_name in target_map:
                fname_lower = padded_name

        if form == "normal":
            target_dir = self.pokemon_sprites_dir
            target_map = self.sprite_map

        elif form.startswith("mega") or form == "primal":
            target_dir = self.mega_sprites_dir
            target_map = self.mega_sprite_map

            if form == "mega":
                fname_lower = f"{p_id}_mega.png"
            elif form == "primal":
                fname_lower = f"{p_id}_primal.png"
            else:
                suffix = form[4:].lstrip("_")
                fname_lower = f"{p_id}_mega_{suffix}.png".lower()

        elif form == "gmax":
            target_dir = self.gmax_sprites_dir
            target_map = self.gmax_sprite_map

            if "_" in form and form != "gmax":
                fname_lower = f"{p_id}_{form}.png".lower()
            else:
                fname_lower = f"{p_id}_gmax.png"

        elif form != "normal":
            if p_id != 201:
                target_dir = self.alt_sprites_dir
                target_map = self.alt_sprite_map
            sep = "-" if p_id == 201 else "_"
            fname_lower = f"{p_id}{sep}{form}.png".lower()

        if is_shiny:
            shiny_fname = self.shiny_sprite_map.get(fname_lower)
            if shiny_fname:
                path = os.path.join(self.shiny_sprites_dir, shiny_fname)
                if os.path.exists(path):
                    return pygame.image.load(path).convert_alpha()

        actual_fname = target_map.get(fname_lower)
        if actual_fname:
            path = os.path.join(target_dir, actual_fname)
            if os.path.exists(path) and not os.path.isdir(path):
                return pygame.image.load(path).convert_alpha()

        if not placeholder:
            return None
        s = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.circle(s, (100, 100, 100), (50, 50), 40)
        return s

    def get_item_image(self, item_name):
        """Smart look-up for item sprites using various naming conventions."""
        if not item_name:
            return None

        base = item_name.lower()
        candidates = [
            f"{base}.png",
            f"{base.replace('_', '-')}.png",
            f"{base.replace('_', '')}.png",
            (f"{base}-ball.png" if "ball" in base and "-ball" not in base
             else None)
        ]

        for cand in candidates:
            if cand and cand in self.item_map:
                path = os.path.join(
                    self.items_sprites_dir, self.item_map[cand])
                return pygame.transform.scale(
                    pygame.image.load(path).convert_alpha(), (40, 40))

        return None

    def get_random_battle_background(self, battle_type, area_name=""):
        if not battle_type:
            return None

        candidates = []
        battle_type_lower = battle_type.lower()
        area_name_lower = (
            area_name.lower().replace(" ", "_").replace("_city", "")
            if area_name
            else ""
        )

        override_bg = None
        if "power_plant" in area_name_lower:
            override_bg = "battle_power_plant.png"
        elif "diglett" in area_name_lower:
            override_bg = "battle_diglett_cave.png"
        elif "safari" in area_name_lower:
            override_bg = "battle_safari_zone.png"

        if override_bg and override_bg in self.battle_bg_map:
            path = os.path.join(
                self.battle_backgrounds_dir,
                self.battle_bg_map[override_bg]
            )
            try:
                return pygame.image.load(path).convert()
            except Exception:
                pass

        if "gym" in battle_type_lower and area_name_lower:
            target_fname = f"battle_gym_{area_name_lower}.png"
            if target_fname in self.battle_bg_map:
                path = os.path.join(self.battle_backgrounds_dir, self.battle_bg_map[target_fname])
                try:
                    return pygame.image.load(path).convert()
                except Exception:
                    pass

        prefix = f"battle_{battle_type_lower}"
        for fname_lower, fname_actual in self.battle_bg_map.items():
            if fname_lower.startswith(prefix):
                candidates.append(fname_actual)

        if candidates:
            chosen_bg = random.choice(candidates)
            path = os.path.join(self.battle_backgrounds_dir, chosen_bg)
            try:
                return pygame.image.load(path).convert()
            except Exception:
                return None

        return None

    def get_trainer_image(self, name):
        name_lower = name.lower()
        real_name = self.trainer_map.get(name_lower)

        if not real_name and not name_lower.endswith(".png"):
            real_name = self.trainer_map.get(f"{name_lower}.png")

        if not real_name and "." in name_lower:
            base = name_lower.rsplit(".", 1)[0]
            real_name = self.trainer_map.get(base)
            if not real_name:
                real_name = self.trainer_map.get(f"{base}.png")

        if real_name:
            path = os.path.join(self.trainers_dir, real_name)
            try:
                img = pygame.image.load(path).convert_alpha()
                h = int(self.height * 0.6)
                w = int(img.get_width() * (h / img.get_height()))
                return pygame.transform.scale(img, (w, h))
            except Exception:
                pass
        return None

    def get_player_image(self, name, back=False):
        suffix = "_back.png" if back else ".png"
        fname = f"{name.lower()}{suffix}"
        real_name = self.player_trainer_map.get(fname)
        if real_name:
            path = os.path.join(self.player_trainers_dir, real_name)
            return pygame.image.load(path).convert_alpha()
        return None

    def get_cry(self, p_id):
        cry_fname = f"{p_id}.ogg"
        cry_fname_pad = f"{p_id:04d}.ogg"
        real_cry = self.cry_map.get(cry_fname) or self.cry_map.get(
            cry_fname_pad)
        if real_cry:
            return os.path.join(self.cries_dir, real_cry)
        return None

    def _load_font(self, size, bold=False):
        primary_font = None
        candidates = [
            self.font_path,
            Utils.get_actual_path(self.assets_dir, "pokemon_gsc.ttf"),
            Utils.get_actual_path(self.assets_dir, "pokemon_gsc.ttf.ttf"),
        ]
        for path in candidates:
            if primary_font:
                break
            if os.path.exists(path):
                try:
                    font = pygame.font.Font(path, size)
                    font.render("Test", False, WHITE)
                    primary_font = font
                except Exception as e:
                    print(f"Failed to load font {path}: {e}")

        if not primary_font:
            try:
                font_data = base64.b64decode(POKEMON_GSC_BASE64)
                font_file = io.BytesIO(font_data)
                font = pygame.font.Font(font_file, size)
                font.render("Test", False, WHITE)
                primary_font = font
                print("✓ Primary font loaded from embedded data.")
            except Exception as e:
                print(f"Embedded font failed: {e}")

        if not primary_font:
            print("Using system font as primary backup.")
            primary_font = pygame.font.SysFont("Verdana", size, bold=bold)

        try:
            primary_font.set_bold(bold)
        except (AttributeError, pygame.error):
            pass

        try:
            fallback_font = pygame.font.SysFont("Arial", size, bold=bold)
        except Exception:
            fallback_font = pygame.font.Font(None, size)

        return MultiFont(primary_font, fallback_font)

    def get_text(self, key, default=None, **kwargs):
        """Retrieves text from loaded GAME_TEXT, formatting with kwargs. Falls
        back to 'default' if key is missing, or returns 'key' string if both
        are missing."""
        if key in self.game_text:
            text = self.game_text[key]
        else:
            text = default if default is not None else key

        if isinstance(text, list):
            if kwargs:
                formatted = []
                for line in text:
                    try:
                        formatted.append(line.format(**kwargs))
                    except Exception:
                        formatted.append(line)
                return formatted
            return text

        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    def _region_bg_map(self):
        """Every background in a region folder (backgrounds/hoenn, backgrounds/sinnoh, ...)."""
        if getattr(self, "_region_bgs", None) is None:
            self._region_bgs = {}
            if self.backgrounds_dir and os.path.isdir(self.backgrounds_dir):
                for entry in sorted(os.listdir(self.backgrounds_dir)):
                    folder = os.path.join(self.backgrounds_dir, entry)
                    if entry.lower() in ("battle", "kanto", "johto") or not os.path.isdir(folder):
                        continue
                    for root, _, files in os.walk(folder):
                        for f in files:
                            if f.lower().endswith(".png"):
                                rel = os.path.relpath(os.path.join(root, f), self.backgrounds_dir)
                                self._region_bgs.setdefault(f.lower(), rel)
        return self._region_bgs

    def get_background(self, name, from_overworld=False):
        if not name:
            return None
            
        # ARCHITECT: Support lists of backgrounds (e.g. Ilex Forest or League backgrounds)
        if isinstance(name, list):
            if not name:
                return None
            name = random.choice(name)
            
        name_lower = name.lower()

        search_configs = [
            (self.johto_backgrounds_dir, self.johto_bg_map),
            (self.kanto_backgrounds_dir, self.kanto_bg_map),
            (self.backgrounds_dir, self._region_bg_map()),
            (self.battle_backgrounds_dir, self.battle_bg_map),
            (self.backgrounds_dir, Utils.index_files(
                self.backgrounds_dir) if self.backgrounds_dir else {}),
            (self.overworld_dir, Utils.index_files(
                self.overworld_dir) if self.overworld_dir else {})
        ]

        if from_overworld:
            search_configs.insert(0, search_configs.pop())

        for bg_dir, bg_map in search_configs:
            if bg_dir and bg_map and name_lower in bg_map:
                path = os.path.join(bg_dir, bg_map[name_lower])
                return pygame.image.load(path).convert()

        # Not found: try the other names art may have been saved under
        # (cinnabar_city.png for cinnabar_island.png, rock_city for rock_tunnel_city, ...).
        for alt in self._background_aliases(name_lower):
            for bg_dir, bg_map in search_configs:
                if bg_dir and bg_map and alt in bg_map:
                    return pygame.image.load(os.path.join(bg_dir, bg_map[alt])).convert()
        return None

    BG_SUFFIXES = ("_center", "_mart", "_gym", "_lab", "_mom", "")

    def _background_aliases(self, name):
        """Other file names the same background might use, most likely first."""
        import difflib
        base = name[:-4] if name.endswith(".png") else name
        suffix = next(sfx for sfx in self.BG_SUFFIXES if not sfx or base.endswith(sfx))
        place = base[:len(base) - len(suffix)] if suffix else base
        words = place.split("_")
        places, stems = [], []
        for kind in ("_island", "_town", "_village", "_city"):
            if place.endswith(kind):
                stem = place[:-len(kind)]
                places += [stem + k for k in ("_city", "_town", "_island", "_village") if k != kind]
                stems.append(stem)
        if len(words) > 2 and len(words[0]) > 2:
            places.append(f"{words[0]}_{words[-1]}")      # rock_tunnel_city -> rock_city
            places.append(f"{words[0]}_city")
        places.append(place.replace("_", ""))              # ever_grande -> evergrande
        if len(words) >= 2:
            places.append("".join(words[:-1]) + "_" + words[-1])  # ever_grande_city -> evergrande_city
        places += stems                                    # the bare name last (it may be a dungeon)
        out = [f"{p}{suffix}.png" for p in dict.fromkeys(places) if p and p != place]
        # Close spelling (fallabor_town_center.png for fallarbor_town_center.png): same start only.
        known = set(self.kanto_bg_map) | set(self.johto_bg_map) | set(self._region_bg_map())
        same_kind = [k for k in known if (k[:-4].endswith(suffix) if suffix else
                                          not any(k[:-4].endswith(x) for x in self.BG_SUFFIXES if x))]
        for cand in [f"{p}{suffix}.png" for p in [place] + places]:
            out += [m for m in difflib.get_close_matches(cand, same_kind, n=3, cutoff=0.9) if m[:4] == cand[:4]]
        return list(dict.fromkeys(out))

    def _load_balls(self):
        imgs = []
        for fname_lower, fname_actual in self.item_map.items():
            if fname_lower.endswith("-ball.png"):
                try:
                    path = os.path.join(self.items_sprites_dir, fname_actual)
                    img = pygame.image.load(path).convert_alpha()
                    imgs.append(pygame.transform.scale(img, (85, 85)))
                except Exception as e:
                    print(f"Failed to load ball image {fname_actual}: {e}")

        if not imgs:
            fallback = pygame.Surface((85, 85), pygame.SRCALPHA)
            pygame.draw.circle(fallback, RED, (42, 42), 35)
            imgs = [fallback]
        return imgs

    def _load_go_img(self):
        img_path = os.path.join(self.base_dir, "1.png")
        if os.path.exists(img_path):
            try:
                raw_img = pygame.image.load(img_path).convert()
                scale_h = int(self.height * 0.4)
                scale_w = int(
                    raw_img.get_width() * (scale_h / raw_img.get_height()))
                return pygame.transform.scale(raw_img, (scale_w, scale_h))
            except Exception:
                pass
        return None

    def _load_sound(self, name):
        if name in self.sound_map:
            try:
                s = pygame.mixer.Sound(
                    os.path.join(self.sounds_dir, self.sound_map[name])
                )
                s.set_volume(VOLUME)
                return s
            except Exception:
                pass
        return None

    def _load_music(self):
        files = [
            self.sound_map[f]
            for f in self.sound_map
            if f.startswith("kanto_") and f.endswith(".ogg")
        ]
        paths = [os.path.join(self.sounds_dir, f) for f in files]
        random.shuffle(paths)
        return paths

    def _load_pokemon_data(self):
        names = {}
        names_path = Utils.find_json_file(
            self.assets_dir, "pokemon_names.json")
        if names_path:
            try:
                with open(names_path, "r", encoding="utf-8-sig") as f:
                    names = json.load(f)
            except Exception:
                pass

        path = Utils.find_json_file(self.assets_dir, "pokemon_movesets.json")
        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.movesets = data
                    if not names:
                        names = {k: v["name"] for k, v in data.items()}
            except Exception:
                pass

        return names

    def get_stab_move(self, pokemon):
        """Gets a powerful STAB (Same Type Attack Bonus) move for a Pokemon."""
        if not pokemon or not pokemon.types:
            return "Struggle"

        target_id = getattr(pokemon, "meta_id", pokemon.id)
        moves_data = self.movesets.get(str(target_id), {})
        all_moves = moves_data.get("moves", [])

        stab_moves = []
        for move in all_moves:
            move_type = move.get("type")
            power = move.get("power", 0) or 0
            if move_type in pokemon.types and power > 0:
                stab_moves.append((power, move.get("name", "")))

        if not stab_moves:
            return "Tackle"

        stab_moves.sort(key=lambda x: x[0], reverse=True)
        _, move_name = random.choice(stab_moves[:3])
        return move_name.upper()

    def get_badge_image(self, badge_index, region="kanto"):
        """Loads [region]_X.png for badges 1-8."""
        fname = f"{region.lower()}_{badge_index}.png"
        path = Utils.get_actual_path(self.badges_dir, fname)
        if os.path.exists(path):
            return pygame.image.load(path).convert_alpha()

        path = Utils.get_actual_path(self.items_sprites_dir, fname)
        if os.path.exists(path):
            return pygame.image.load(path).convert_alpha()
        return None
