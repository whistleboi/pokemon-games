import pygame
import random
import io
import os
import math
import threading
import queue
import json
import sys
from abc import ABC, abstractmethod
import base64
import io

# === EMBEDDED FONT (copy-paste the huge text here) ===
POKEMON_GSC_BASE64 = "AAAAAAAAAAAAAAICAAAAAAUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAQEBAwMCAgEBAQECAQEBAQAAAAABAQEBAAEAAAABAAEBAQABAgABAQEBAgEBAQEBAQAAAQEAAAIBAgMCAAAAAQICAgAAAAAAAwAAAAEAAQABAQADAQIAAQEBAQEBAAIBAAEBAAIAAAAAAgEBAAEAAAEBAAABAQEAAQEAAAAAAQECAwACAQMBAQEAAAABAAACAQIAAAIAAgIBAAEBAAEAAgEBAAEBAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="

# --- System Initialization ---
pygame.mixer.pre_init(44100, -16, 2, 4096)
pygame.init()
pygame.mixer.init()

# --- Constants ---
FPS = 25
VOLUME = 0.1

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 50, 50)
YELLOW = (255, 215, 0)
BLUE = (50, 50, 200)
GOLD = (255, 215, 0)
ORANGE = (255, 165, 0)
DARK_RED = (139, 0, 0)
PURPLE = (128, 0, 128)
NEON_BLUE = (0, 255, 255)
AMBER = (255, 191, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)

# Events
MUSIC_ENDED_EVENT = pygame.USEREVENT + 2

# ID Pools
UB_IDS = [793, 794, 795, 796, 797, 798, 799, 800, 803, 804, 805, 806,]
PAST_IDS = [984, 985, 986, 987, 988, 989, 990, 999, 1006, 1007, 1009, 1020]
FUTURE_IDS = [991, 992, 993, 994, 995, 998, 1005, 1008, 1010, 1021, 1022, 1023]
MEGA_IDS = [
    3, 6, 9, 15, 18, 26, 65, 71, 80, 94, 115, 127, 130, 142, 150, 181, 208, 212,
    214, 229, 248, 249, 254, 257, 260, 282, 302, 303, 306, 308, 310, 319, 323,
    334, 354, 358, 359, 362, 373, 376, 380, 381, 382, 383, 384, 398, 428, 445,
    448, 460, 475, 485, 491, 530, 531, 545, 560, 604, 623, 646, 647, 648, 652,
    655, 658, 668, 670, 678, 687, 691, 701, 718, 719, 720, 740, 768, 780, 791,
    792, 800, 801, 807, 870, 901, 952, 969, 978, 998, 1024
]
GMAX_IDS = [
    6, 25, 52, 94, 133, 143, 812, 815, 818, 823, 839, 849, 858, 861, 869, 892
]
MYTHICAL_IDS = [
    151, 251, 385, 386, 489, 490, 491, 492, 493, 494, 647, 648, 649, 719, 720,
    721, 801, 802, 807, 808, 809, 893, 1025
]
STANDARD_BOSS_IDS = [
    144, 145, 146, 150, 243, 244, 245, 249, 250, 380, 381, 382, 383,
    384, 480, 481, 482, 483, 484, 485, 486, 487, 488, 638, 639, 640, 641, 642,
    643, 644, 645, 646, 716, 717, 718, 772, 773, 785, 786, 787, 788, 789, 790,
    791, 792, 888, 889, 890, 891, 892, 894, 895, 896, 897, 898, 905, 1001, 1002,
    1003, 1004, 1007, 1008, 1014, 1015, 1016, 1024
]
ALL_BOSS_IDS = set(
    UB_IDS + PAST_IDS + FUTURE_IDS + STANDARD_BOSS_IDS + MYTHICAL_IDS
)

BOSS_WARNINGS = {
    "UB": "An ultra wormhole tears open!",
    "PAST": "Primal roars awaken from the abyss!",
    "FUTURE": "Iron machines whir from the future!",
    "MEGA": "Rogue Mega energy surges wildly!",
    "GMAX": "Gigantamax growth engulfs the arena!",
    "MYTHICAL": "A mythical aura descends upon you!",
    "STANDARD": "A legendary storm brews ahead!"
}

# --- Utilities ---
class Utils:
    @staticmethod
    def get_actual_path(base, name):
        """Finds a folder/file case-insensitively in base directory."""
        if not os.path.exists(base): return os.path.join(base, name)
        target = os.path.join(base, name)
        if os.path.exists(target): return target
        try:
            for item in os.listdir(base):
                if item.lower() == name.lower():
                    return os.path.join(base, item)
        except OSError:
            pass
        return target

    @staticmethod
    def index_files(directory):
        if not os.path.exists(directory): return {}
        return {f.lower(): f for f in os.listdir(directory)}

    @staticmethod
    def draw_text_outline(surface, text, font, color, x, y, outline_color=BLACK, thickness=3, align="center"):
        text_surf = font.render(text, True, color)
        if align == "center":
            pos = (x - text_surf.get_width()//2, y - text_surf.get_height()//2)
        elif align == "right":
            pos = (x - text_surf.get_width(), y)
        else:
            pos = (x, y)

        for dx, dy in [(-thickness, 0), (thickness, 0), (0, -thickness), (0, thickness)]:
            outline_surf = font.render(text, True, outline_color)
            surface.blit(outline_surf, (pos[0] + dx, pos[1] + dy))
        surface.blit(text_surf, pos)

    @staticmethod
    def draw_star(surface, color, center, size):
        points = []
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            radius = size if i % 2 == 0 else size // 2
            points.append((
                center[0] + radius * math.cos(angle),
                center[1] + radius * math.sin(angle)
            ))
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, BLACK, points, 2)

class DummySound:
    def play(self): pass
    def set_volume(self, v): pass

class Pokemon:
    def __init__(self, raw_data, assets, size_mult=3.5, is_boss=False):
        self.id = raw_data['id']
        self.name = raw_data['name']
        self.display_name = raw_data.get('display_name', self.name)
        self.form = raw_data.get('form', 'normal')
        self.is_shiny = raw_data['is_shiny']
        self.raw_cry_bytes = raw_data['cry']

        if raw_data['img']:
            img_surface = pygame.image.load(io.BytesIO(raw_data['img'])).convert_alpha()
        else:
            img_surface = pygame.Surface((100, 100), pygame.SRCALPHA)
            pygame.draw.circle(img_surface, (100, 100, 100), (50, 50), 40)

        mult = (size_mult * 2 if assets.is_pc else size_mult)
        s = int(assets.width // mult)
        self.image = pygame.transform.scale(img_surface, (s, s))
        
        sb_scale = 0.05 if assets.is_pc else 0.12
        self.sidebar_image = pygame.transform.scale(img_surface, 
                                            (int(assets.width * sb_scale), 
                                             int(assets.width * sb_scale)))
        try:
            self.cry = pygame.mixer.Sound(io.BytesIO(self.raw_cry_bytes)) if self.raw_cry_bytes else DummySound()
            self.cry.set_volume(VOLUME)
        except pygame.error:
            self.cry = DummySound()
            
        self.bob_offset = random.uniform(0, 2 * math.pi)
        self.bob_speed = random.uniform(0.004, 0.006)
        self.bob_amount = random.uniform(8, 12)

    def set_volume(self, volume):
        if self.cry:
            self.cry.set_volume(volume)

class MultiFont:
    def __init__(self, primary_font, fallback_font):
        self.primary = primary_font
        self.fallback = fallback_font
        # Characters the user specified are missing from the primary font.
        self.SPECIAL_CHARS = {'#', '<', '>', 'é', 'É'}

    def render(self, text, antialias, color, background=None):
        # This implementation ignores the `background` argument as it's not used in the project.
        segments = []
        current_segment = ""
        
        if not text:
            return self.primary.render("", antialias, color)

        current_is_special = text[0] in self.SPECIAL_CHARS
        for char in text:
            is_special = char in self.SPECIAL_CHARS
            if is_special == current_is_special:
                current_segment += char
            else:
                segments.append((current_segment, current_is_special))
                current_segment = char
                current_is_special = is_special
        segments.append((current_segment, current_is_special))

        rendered_surfaces = []
        total_width = 0
        for segment_text, is_special in segments:
            font_to_use = self.fallback if is_special else self.primary
            surf = font_to_use.render(segment_text, antialias, color)
            rendered_surfaces.append(surf)
            total_width += surf.get_width()
        
        master_height = self.primary.get_height()
        master_surf = pygame.Surface((total_width, master_height), pygame.SRCALPHA)
        current_x = 0
        for surf in rendered_surfaces:
            master_surf.blit(surf, (current_x, master_height - surf.get_height()))
            current_x += surf.get_width()
        return master_surf

    def get_height(self):
        return self.primary.get_height()

# --- UI Elements ---
class UIElement(ABC):
    def __init__(self, rect, callback=None, visible=True):
        self.rect = pygame.Rect(rect)
        self.callback = callback
        self.visible = visible

    def set_visibility(self, visible):
        self.visible = visible

    @abstractmethod
    def handle_event(self, event):
        pass

    @abstractmethod
    def draw(self, surface):
        pass

class Button(UIElement):
    def __init__(self, rect, text, font, callback, text_color=WHITE, bg_color=BLUE, outline_color=BLACK, border_radius=15, visible=True):
        super().__init__(rect, callback, visible)
        self.text = text
        self.font = font
        self.text_color = text_color
        self.bg_color = bg_color
        self.outline_color = outline_color
        self.border_radius = border_radius
        
        # Scale button to fit text
        text_surf = self.font.render(self.text, True, self.text_color)
        padding_x = 40
        padding_y = 20
        original_center = self.rect.center
        self.rect.size = (text_surf.get_width() + padding_x, text_surf.get_height() + padding_y)
        self.rect.center = original_center

    def handle_event(self, event):
        if not self.visible: return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback: self.callback()
                return True
        return False

    def draw(self, surface):
        if not self.visible: return
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=self.border_radius)
        Utils.draw_text_outline(surface, self.text, self.font, self.text_color, self.rect.centerx, self.rect.centery, outline_color=self.outline_color)

class Slider(UIElement):
    def __init__(self, rect, value_range, initial_value, callback, bar_color=GRAY, knob_color=WHITE, fill_color=GREEN, visible=True):
        super().__init__(rect, callback, visible)
        self.value_range = value_range
        self._value = initial_value
        self.bar_color, self.knob_color, self.fill_color = bar_color, knob_color, fill_color
        self.dragging = False

    def handle_event(self, event):
        if not self.visible: return False
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.dragging = True
            self._update_value_from_pos(event.pos[0])
            return True
        elif event.type == pygame.MOUSEBUTTONUP: self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_value_from_pos(event.pos[0])
            return True
        return False

    def _update_value_from_pos(self, mouse_x):
        self._value = max(0.0, min(1.0, (mouse_x - self.rect.left) / self.rect.width))
        if self.callback: self.callback(self._value)

    def draw(self, surface):
        if not self.visible: return
        pygame.draw.rect(surface, self.bar_color, self.rect, border_radius=5)
        fill_width = int(self._value * self.rect.width)
        pygame.draw.rect(surface, self.fill_color, (self.rect.x, self.rect.y, fill_width, self.rect.height), border_radius=5)
        knob_rect = pygame.Rect(self.rect.left + fill_width - 10, self.rect.centery - 15, 20, 30)
        pygame.draw.rect(surface, self.knob_color, knob_rect, border_radius=5)

class UIManager:
    def __init__(self):
        self.elements = []

    def add_element(self, element):
        self.elements.append(element)

    def handle_events(self, events):
        for event in events:
            for element in self.elements:
                if element.handle_event(event):
                    if isinstance(element, Button) or (isinstance(element, Slider) and event.type == pygame.MOUSEBUTTONDOWN):
                        return True
        return False

    def draw(self, surface):
        for element in self.elements:
            element.draw(surface)

    # --- Managers ---#
class AssetManager:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        # Determine base directory for bundled vs. dev environments
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running in a PyInstaller bundle
            self.base_dir = sys._MEIPASS
        else:
            # Running in a normal Python environment
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # Path Resolution
        self.assets_dir = Utils.get_actual_path(self.base_dir, "assets")

        self.sprites_dir = Utils.get_actual_path(self.assets_dir, "sprites")
        self.pokemon_sprites_dir = Utils.get_actual_path(self.sprites_dir, "pokemon")
        self.shiny_sprites_dir = Utils.get_actual_path(self.pokemon_sprites_dir, "shiny")
        self.mega_sprites_dir = Utils.get_actual_path(self.pokemon_sprites_dir, "mega")
        self.gmax_sprites_dir = Utils.get_actual_path(self.pokemon_sprites_dir, "gmax")
        self.alt_sprites_dir = Utils.get_actual_path(self.pokemon_sprites_dir, "altform")
        self.items_sprites_dir = Utils.get_actual_path(self.sprites_dir, "items")
        self.sounds_dir = Utils.get_actual_path(self.assets_dir, "sounds")

        if not os.path.exists(self.sounds_dir):
            self.sounds_dir = Utils.get_actual_path(self.pokemon_sprites_dir, "sounds")
        
        self.cries_dir = Utils.get_actual_path(self.sounds_dir, "cries")

        # File Maps
        self.sprite_map = Utils.index_files(self.pokemon_sprites_dir)
        self.shiny_sprite_map = Utils.index_files(self.shiny_sprites_dir)
        self.mega_sprite_map = Utils.index_files(self.mega_sprites_dir)
        self.gmax_sprite_map = Utils.index_files(self.gmax_sprites_dir)
        self.alt_sprite_map = Utils.index_files(self.alt_sprites_dir)
        self.cry_map = Utils.index_files(self.cries_dir)
        self.item_map = Utils.index_files(self.items_sprites_dir)
        self.sound_map = Utils.index_files(self.sounds_dir)
        mega_path = Utils.get_actual_path(self.items_sprites_dir, "mega-symbol.png")
        if os.path.exists(mega_path):
            self.mega_symbol = pygame.image.load(mega_path).convert_alpha()
        else:
            self.mega_symbol = None
        shiny_charm_path = Utils.get_actual_path(self.items_sprites_dir, "shiny_charm.png")
        if os.path.exists(shiny_charm_path):
            self.shiny_charm = pygame.image.load(shiny_charm_path).convert_alpha()
            # Optional: scale to reasonable size
            self.shiny_charm = pygame.transform.scale(self.shiny_charm, (80, 80))
        else:
            self.shiny_charm = None
        dynamax_band_path = Utils.get_actual_path(self.items_sprites_dir, "dynamax-band.png")
        if os.path.exists(dynamax_band_path):
            self.dynamax_band = pygame.image.load(dynamax_band_path).convert_alpha()
            # Scale similar to shiny charm
            self.dynamax_band = pygame.transform.scale(self.dynamax_band, (80, 80))
        else:
            self.dynamax_band = None

        # Fonts
        self.font_path = Utils.get_actual_path(self.assets_dir, "pokemon_gsc.ttf")
        if not os.path.exists(self.font_path):
            print(f"Warning: Custom font not found at '{self.font_path}'. Using system fallback.", file=sys.stderr)
        self.is_pc = sys.platform in ['win32', 'linux', 'darwin']
        self.font_scale = 0.5 if self.is_pc else 1.0
        self.fonts = {
            "big": self._load_font(int(width * 0.065 * self.font_scale), bold=True),
            "med": self._load_font(int(width * 0.06 * self.font_scale), bold=True),
            "s_med": self._load_font(int(width * 0.04 * self.font_scale), bold=True),
            "num": self._load_font(int(width * 0.06 * self.font_scale), bold=True),
            "small": self._load_font(int(width * 0.02 * self.font_scale), bold=True),
            "tiny": self._load_font(int(width * 0.015 * self.font_scale), bold=True),
        }

        # Images
        self.ball_imgs = self._load_balls()
        self.ui_ball = pygame.transform.scale(self.ball_imgs[0], (int(width*0.04), int(width*0.04)))
        self.shiny_charm_img = self._load_charm()
        self.go_img = self._load_go_img()

        # Sounds
        self.shiny_sfx = self._load_sound('shiny.ogg')
        self.heal_sfx = self._load_sound('heal.ogg')
        self.music_playlist = self._load_music()

        # Data
        self.movesets = {}
        self.pokemon_names = self._load_pokemon_data()

    def _load_font(self, size, bold=False):
        primary_font = None
        # 1. Try file candidates
        candidates = [self.font_path, 
                      Utils.get_actual_path(self.assets_dir, "pokemon_gsc.ttf.ttf"), 
                      Utils.get_actual_path(self.assets_dir, "pokemon-gsc-font.otf")]
        for path in candidates:
            if primary_font: break
            if os.path.exists(path):
                try:
                    font = pygame.font.Font(path, size)
                    font.render("Test", False, WHITE)
                    primary_font = font
                    print(f"✓ Primary font loaded from file: {os.path.basename(path)}")
                except Exception as e:
                    print(f"Failed to load font {path}: {e}")

        # 2. Try embedded base64
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

        # 3. Last resort system font for primary
        if not primary_font:
            print("Using system font as primary backup.")
            primary_font = pygame.font.SysFont("Verdana", size, bold=bold)

        # Set bold property on the chosen primary font
        try: primary_font.set_bold(bold)
        except: pass

        # Create the fallback font for special characters
        try:
            fallback_font = pygame.font.SysFont("Arial", size, bold=bold)
        except Exception:
            fallback_font = pygame.font.Font(None, size)

        return MultiFont(primary_font, fallback_font)

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

    def _load_charm(self):
        try:
            real_name = self.item_map.get("shiny-charm.png")
            if real_name:
                path = os.path.join(self.items_sprites_dir, real_name)
                charm_raw = pygame.image.load(path).convert_alpha()
                return pygame.transform.scale(charm_raw, (int(self.width * 0.08), int(self.width * 0.08)))
        except Exception:
            pass
        return None

    def _load_go_img(self):
        img_path = os.path.join(self.base_dir, "1.png")
        if os.path.exists(img_path):
            try:
                raw_img = pygame.image.load(img_path).convert()
                scale_h = int(self.height * 0.4)
                scale_w = int(raw_img.get_width() * (scale_h / raw_img.get_height()))
                return pygame.transform.scale(raw_img, (scale_w, scale_h))
            except Exception:
                pass
        return None

    def _load_sound(self, name):
        if name in self.sound_map:
            try:
                s = pygame.mixer.Sound(os.path.join(self.sounds_dir, self.sound_map[name]))
                s.set_volume(VOLUME)
                return s
            except: pass
        return None

    def _load_music(self):
        files = [self.sound_map[f] for f in self.sound_map if f.startswith('kanto_') and f.endswith('.ogg')]
        paths = [os.path.join(self.sounds_dir, f) for f in files]
        random.shuffle(paths)
        return paths

    def _load_pokemon_data(self):
        names = {}
        # 1. Try pokemon_names.json (generated by generate_names.py)
        names_path = os.path.join(self.assets_dir, "pokemon_names.json")
        if os.path.exists(names_path):
            try:
                with open(names_path, "r", encoding="utf-8") as f:
                    names = json.load(f)
            except Exception: pass

        # 2. Load movesets (always needed for moves)
        path = os.path.join(self.assets_dir, "pokemon_movesets.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.movesets = data  # Full data for moves/power
                    # If names still empty, fallback to movesets
                    if not names:
                        names = {k: v['name'] for k, v in data.items()}
            except Exception: pass
        
        return names

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
        return {"high_score": 0, "total_shinies": 0, "pokedex": {}}

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

    def add_pokemon(self, pokemon, img_hex):
        p_key = f"{pokemon.id}-{pokemon.form}"
        if p_key in self.data["pokedex"] and self.data["pokedex"][p_key].get('shiny', False) and not pokemon.is_shiny:
            return

        self.data["pokedex"][p_key] = {
            "id": pokemon.id,
            "name": pokemon.display_name,
            "form": pokemon.form,
            "shiny": pokemon.is_shiny,
            "cry_hex": pokemon.raw_cry_bytes.hex(),
            "img_hex": img_hex
        }

    def wipe_data(self):
        self.data["pokedex"] = {}
        self.data["total_shinies"] = 0
        self.save()

class PokemonLoader:
    def __init__(self, game):
        self.game = game
        self.assets = game.assets
        self.queue = queue.Queue(maxsize=2)
        self.last_served_names = set()
        self.shiny_charm_active = False
        self.dev_shiny_mode = False
        self.mega_unlocked = False # Track if Mega forms are unlocked for random boss selection
        self.gmax_unlocked = False # Track if Gmax forms are unlocked for random boss selection
        self.total_caught = 0
        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _fetch_raw(self, pool_type=None, exclude_names=None):
        if exclude_names is None: exclude_names = set()
        if self.dev_shiny_mode: base_odds = 0.25
        else: base_odds = 0.02 if self.shiny_charm_active else 0.01
        
        attempts = 0
        max_attempts = 40 if pool_type else 10 # More attempts for specific boss searches
        caught_pokedex_keys = set(self.game.data.data['pokedex'].keys())
        target_pool = None
        if pool_type == "UB": target_pool = UB_IDS
        elif pool_type == "PAST": target_pool = PAST_IDS
        elif pool_type == "FUTURE": target_pool = FUTURE_IDS
        elif pool_type == "MYTHICAL": target_pool = MYTHICAL_IDS
        elif pool_type == "MEGA": target_pool = MEGA_IDS
        elif pool_type == "GMAX": target_pool = GMAX_IDS
        elif pool_type == "STANDARD": target_pool = STANDARD_BOSS_IDS
        
        form = pool_type.lower() if pool_type in ["MEGA", "GMAX"] else "normal"

        while attempts < max_attempts:
            try:
                if target_pool:
                    p_id = random.choice(target_pool)
                else:
                    p_id = random.randint(1, 1025)
                    if p_id in ALL_BOSS_IDS:
                        attempts += 1
                        continue

                # Determine form before checking for duplicates
                temp_form = form
                if temp_form == "mega":
                    possible_files = [f for f in self.assets.mega_sprite_map if f.startswith(f"{p_id}_mega")]
                    if possible_files:
                        # Temporarily pick a form to check against the dex
                        temp_fname = random.choice(possible_files)
                        form_suffix = temp_fname.replace(f"{p_id}_mega", "").replace(".png", "")
                        temp_form = f"mega{form_suffix}"

                p_key = f"{p_id}-{temp_form}"
                if pool_type is not None and p_key in caught_pokedex_keys:
                    attempts += 1
                    continue
                is_shiny = (random.random() < base_odds)
                name = self.assets.pokemon_names.get(str(p_id), f"POKEMON_{p_id}").upper()
                if name in exclude_names:
                    attempts += 1
                    continue

                # Sprite Selection Logic
                img_bytes = b""
                fname = f"{p_id}.png"
                
                target_dir = self.assets.pokemon_sprites_dir
                target_map = self.assets.sprite_map
                target_fname = fname

                display_name = name
                if form == "mega":
                    possible_files = [f for f in self.assets.mega_sprite_map if f.startswith(f"{p_id}_mega")]
                    if possible_files:
                        target_fname = random.choice(possible_files)
                        target_dir = self.assets.mega_sprites_dir
                        target_map = self.assets.mega_sprite_map
                        
                        form_suffix = target_fname.replace(f"{p_id}_mega", "").replace(".png", "")
                        form = f"mega{form_suffix}"
                        form_suffix = target_fname.replace(f"{p_id}_mega", "").replace(".png", "")
                        if form_suffix:
                            display_name = f"MEGA {name} {form_suffix.replace('_', ' ').upper()}"
                        else:
                            display_name = f"MEGA {name}"
                elif form == "gmax":
                    display_name = f"GMAX {name}"
                    target_dir = self.assets.gmax_sprites_dir
                    target_map = self.assets.gmax_sprite_map
                    
                    possible_files = [f for f in self.assets.gmax_sprite_map if f.startswith(f"{p_id}_gmax")]
                    if possible_files:
                        target_fname = random.choice(possible_files)
                    else:
                        target_fname = f"{p_id}_gmax.png"
                elif form == "normal":
                    # Check for Alt Form
                    p_id_str = str(p_id)
                    possible_alts = [f for f in self.assets.alt_sprite_map if f == f"{p_id_str}.png" or f.startswith(f"{p_id_str}_")]
                    
                    if possible_alts:
                        if random.random() < 0.5: # 50% chance for Alt
                            target_dir = self.assets.alt_sprites_dir
                            target_map = self.assets.alt_sprite_map
                            target_fname = random.choice(possible_alts)
                            
                            # Update display name
                            base_name = target_fname.rsplit('.', 1)[0]
                            if base_name.startswith(p_id_str):
                                suffix = base_name[len(p_id_str):]
                                if suffix.startswith("_"):
                                    suffix = suffix[1:]
                                form = suffix if suffix else "alt"
                                if suffix:
                                    suffix_clean = suffix.replace("_", " ").title()
                                    display_name = f"{name} {suffix_clean.upper()}"

                # Load Image
                if is_shiny:
                    if target_dir == self.assets.pokemon_sprites_dir: # Only check standard shiny folder for standard sprites
                        real_shiny = self.assets.shiny_sprite_map.get(target_fname)
                        if real_shiny:
                            with open(os.path.join(self.assets.shiny_sprites_dir, real_shiny), "rb") as f:
                                img_bytes = f.read()
                
                if not img_bytes:
                    real_normal = target_map.get(target_fname)
                    if real_normal:
                        with open(os.path.join(target_dir, real_normal), "rb") as f:
                            img_bytes = f.read()

                # Cry
                cry_bytes = b""
                cry_fname = f"{p_id}.ogg"
                cry_fname_pad = f"{p_id:04d}.ogg"
                real_cry = self.assets.cry_map.get(cry_fname) or self.assets.cry_map.get(cry_fname_pad)
                if real_cry:
                    with open(os.path.join(self.assets.cries_dir, real_cry), "rb") as f:
                        cry_bytes = f.read()

                return {
                    "id": p_id, "name": name, "display_name": display_name,
                    "img": img_bytes, "cry": cry_bytes, "is_shiny": is_shiny, "form": form
                }
            except Exception as e:
                attempts += 1
        return {"id": 0, "name": "MISSINGNO", "display_name": "MISSINGNO", "img": b"", "cry": b"", "is_shiny": False, "form": "normal"}

    def _worker(self):
        while self.running:
            if not self.queue.full():
                p_list = []; current_batch_names = set()
                for _ in range(3):
                    p = self._fetch_raw(None, exclude_names=self.last_served_names | current_batch_names)
                    if p:
                        p_list.append(p)
                        current_batch_names.add(p['name'])

                b_type = random.choice(
                    ["STANDARD", "UB", "PAST", "FUTURE", "MYTHICAL", "GMAX", "MEGA"]
                )
                boss_p = self._fetch_raw(b_type)
                
                if len(p_list) == 3 and boss_p:
                    self.queue.put({
                        "normal": p_list,
                        "boss": boss_p,
                        "names": current_batch_names,
                        "boss_type": b_type
                    })
            pygame.time.wait(200)

    def get_batch(self):
        if not self.queue.empty():
            batch = self.queue.get()
            self.last_served_names = batch['names']
            return batch
        return None

class BossManager:
    def __init__(self, game):
        self.game = game
        self.in_boss_mode = False
        self.boss_intro_played = False
        self.boss_hp = 3
        self.feedback_text = ""
        self.feedback_color = WHITE
        self.boss_hits = 0
        self.current_boss_type = "STANDARD"
        self.boss_intro_timer = 0 # Renamed from boss_intro to avoid confusion with boss_pokemon_data
        self.boss_cry_triggered = False
        self.boss_pokemon_data = None # Stores the finalized p_data for the boss
        self.aura_pulse = 0.0

    def start_boss_mode(self, raw_boss_data):
        self.in_boss_mode = True
        self.boss_intro_played = False
        self.boss_hp = 3
        self.boss_hits = 0
        self.boss_cry_triggered = False
        self.current_boss_type = raw_boss_data.get('boss_type', 'STANDARD')
        self.boss_intro_timer = 50 # Duration of the intro animation
        self.feedback_text = BOSS_WARNINGS.get(self.current_boss_type, BOSS_WARNINGS["STANDARD"])

        # Finalize boss data here, similar to PlayState's finalize_p_data
        self.boss_pokemon_data = Pokemon(raw_boss_data['boss'], self.game.assets, size_mult=1.5, is_boss=True)

    def update(self):
        if not self.in_boss_mode:
            return

        if self.boss_intro_timer > 0:
            self.boss_intro_timer -= 1
            return

        if not self.boss_cry_triggered and self.boss_pokemon_data and self.boss_pokemon_data.cry:
            self.boss_pokemon_data.cry.play()
            self.boss_cry_triggered = True

        self.aura_pulse += 0.05

    def draw(self, screen, width, height, offset_x, offset_y):
        if not self.in_boss_mode:
            return

        # Boss Intro Animation
        if self.boss_intro_timer > 0:
            # Determine color for the overlay
            if self.current_boss_type == "UB": intro_color = PURPLE
            elif self.current_boss_type == "PAST": intro_color = AMBER
            elif self.current_boss_type == "FUTURE": intro_color = NEON_BLUE
            elif self.current_boss_type == "MEGA": intro_color = (180, 50, 255)
            elif self.current_boss_type == "GMAX": intro_color = (255, 80, 120)
            elif self.current_boss_type == "MYTHICAL": intro_color = (255, 105, 180)
            else: intro_color = (150, 0, 0)

            # Create a pulsing, semi-transparent overlay for a less jarring effect
            pulse_alpha = (math.sin(self.boss_intro_timer * 0.25) + 1) / 2 * 150  # Varies between 0 and 150
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            overlay.fill((intro_color[0], intro_color[1], intro_color[2], int(pulse_alpha)))
            screen.blit(overlay, (0, 0))

            Utils.draw_text_outline(screen, self.feedback_text, self.game.assets.fonts['s_med'], YELLOW, width//2, height//2)
            return True # Still blocks main game draw for a clean warning screen

        # Boss Background Aura
        if self.current_boss_type == "UB": bg_v = int(20 + math.sin(self.aura_pulse) * 15); screen.fill((bg_v, 0, bg_v))
        elif self.current_boss_type == "PAST": bg_v = int(40 + math.sin(self.aura_pulse) * 20); screen.fill((bg_v, bg_v // 2, 0))
        elif self.current_boss_type == "FUTURE": bg_v = int(40 + math.sin(self.aura_pulse) * 20); screen.fill((0, bg_v, bg_v))
        elif self.current_boss_type == "MEGA": bg_v = int(50 + math.sin(self.aura_pulse) * 25); screen.fill((bg_v, 0, bg_v + 20))
        elif self.current_boss_type == "GMAX": bg_v = int(50 + math.sin(self.aura_pulse) * 25); screen.fill((bg_v + 20, 0, bg_v))
        elif self.current_boss_type == "MYTHICAL": bg_v = int(60 + math.sin(self.aura_pulse) * 30); screen.fill((bg_v, 20, 80))
        else: bg_v = int(30 + math.sin(self.aura_pulse) * 20); screen.fill((bg_v, 0, bg_v // 2))

        # Boss HP Bar & Counter — always draw in boss mode after intro
        if self.in_boss_mode and self.boss_intro_timer <= 0:
            bar_center_x = width // 2 + offset_x
            bar_y = height * 0.08           # high position — above equation area
            bar_w = 320
            bar_h = 36
            fill_ratio = self.boss_hp / 3.0
            fill_w = int(bar_w * fill_ratio)
            fill_color = GREEN if fill_ratio > 0.66 else YELLOW if fill_ratio > 0.33 else RED

            # Background (empty bar)
            pygame.draw.rect(screen, DARK_RED, 
                            (bar_center_x - bar_w//2, bar_y + offset_y, bar_w, bar_h),
                            border_radius=10)
            
            # Filled portion
            pygame.draw.rect(screen, fill_color, 
                            (bar_center_x - bar_w//2, bar_y + offset_y, fill_w, bar_h),
                            border_radius=10)
            
            # White border
            pygame.draw.rect(screen, WHITE, 
                            (bar_center_x - bar_w//2, bar_y + offset_y, bar_w, bar_h),
                            width=4, border_radius=10)

            # Counter nicely centered above bar
            counter_y = bar_y - 45 + offset_y
            Utils.draw_text_outline(screen, f"{self.boss_hp}/3", 
                                    self.game.assets.fonts['med'], WHITE,
                                    bar_center_x, counter_y,
                                    outline_color=BLACK, thickness=4)

# --- Particles ---
class Particle(ABC):
    @abstractmethod
    def update(self): pass
    @abstractmethod
    def draw(self, surface): pass

class Starburst(Particle):
    def __init__(self, x, y, color=GOLD):
        self.particles = []
        self.color = color
        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(5, 12)
            self.particles.append([
                [x, y],
                [math.cos(angle) * speed, math.sin(angle) * speed],
                random.randint(20, 40)
            ])
    def update(self):
        for p in self.particles:
            p[0][0] += p[1][0]
            p[0][1] += p[1][1]
            p[2] -= 1
        self.particles = [p for p in self.particles if p[2] > 0]
    def draw(self, surface):
        for p in self.particles:
            pygame.draw.circle(
                surface, self.color,
                (int(p[0][0]), int(p[0][1])), random.randint(3, 6)
            )

class ShinyBurst(Particle):
    def __init__(self, x, y):
        self.particles = []
        self.colors = [GOLD, WHITE, (0, 255, 255), (255, 105, 180)]
        for _ in range(50):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(4, 15)
            color = random.choice(self.colors)
            self.particles.append([
                [x, y],
                [math.cos(angle) * speed, math.sin(angle) * speed],
                random.randint(30, 50),
                color,
                random.randint(4, 8)
            ])
    def update(self):
        for p in self.particles:
            p[0][0] += p[1][0]
            p[0][1] += p[1][1]
            p[2] -= 1
        self.particles = [p for p in self.particles if p[2] > 0]
    def draw(self, surface):
        for p in self.particles:
            pygame.draw.circle(
                surface, p[3], (int(p[0][0]), int(p[0][1])), p[4]
            )

class IdleSparkle:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.particles = []
    def update(self, current_x, current_y):
        self.x, self.y = current_x, current_y
        if len(self.particles) < 12:
            self.particles.append({
                "rel_x": random.randint(-50, 50),
                "rel_y": random.randint(-70, 30),
                "size": random.randint(2, 5),
                "life": random.randint(15, 30),
                "color": random.choice([GOLD, WHITE])
            })
        for p in self.particles:
            p["life"] -= 1
            p["rel_y"] -= 0.5
        self.particles = [p for p in self.particles if p["life"] > 0]
    def draw(self, surface):
        for p in self.particles:
            pygame.draw.circle(
                surface, p["color"],
                (int(self.x + p["rel_x"]), int(self.y + p["rel_y"])), p["size"]
            )

# --- Game States ---

class GameState(ABC):
    def __init__(self, game):
        self.game = game
    def start(self):
        pass
    @abstractmethod
    def handle_events(self, events): pass
    @abstractmethod
    def update(self): pass
    @abstractmethod
    def draw(self): pass

class LoadingState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.angle = 0
        self.ball_img = game.assets.ball_imgs[0]
        self.ball_img = pygame.transform.scale(self.ball_img, (150, 150))

    def handle_events(self, events):
        pass

    def update(self):
        self.angle = (self.angle - 5) % 360
        if not self.game.loader.queue.empty():
            self.game.change_state(PlayState(self.game))

    def draw(self):
        self.game.screen.fill(BLACK)
        Utils.draw_text_outline(self.game.screen, "LOADING WORLD DATA...", self.game.assets.fonts['med'], WHITE, self.game.width // 2, self.game.height * 0.3)
        rot_img = pygame.transform.rotate(self.ball_img, self.angle)
        rect = rot_img.get_rect(center=(self.game.width // 2, self.game.height * 0.6))
        self.game.screen.blit(rot_img, rect)

class PlayState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.total_caught = 0
        self.balls_left = 5 # This remains in PlayState as it's a core game mechanic
        self.current_streak = 0
        self.flash_msg = ""
        self.flash_timer = 0
        self.mega_unlocked = False # Flag for Mega evolution unlocked
        self.gmax_unlocked = False # Flag for Gmax unlocked
        self.p_data = [None] * 3
        self.collected_team = []
        
        self.question_timer = 0
        self.current_ball_img = game.assets.ball_imgs[0]
        
        self.starbursts = []
        self.idle_sparkles = []
        self.sprite_y = game.height * 0.4
        self.scr_shake_timer = 0
        
        self.ball_active = False
        self.ball_pos = [0, 0]
        self.ball_target = [0, 0]
        self.pause_timer = 0
        self.caught_idx = -1
        self.flee_active = False; self.shake_amount = 0
        self.runaway_x_offsets = [0, 0, 0]
        
        self.answer_btn_rects = [pygame.Rect(0,0,0,0) for _ in range(3)]
        self.stars = [[random.randint(0, game.width), random.randint(0, game.height), random.randint(2, 4)] for _ in range(40)]
        self.btn_size = 100 if game.assets.is_pc else 140

        # Initialize UI elements
        self.vol_slider = Slider(
            rect=(120, game.height - 40, 200, 10), value_range=(0.0, 1.0),
            initial_value=VOLUME, callback=self.update_volume_from_slider
        )
        self.btn_dex = Button(
            rect=(20, 260, 250, 80), text="POKEDEX", font=game.assets.fonts['small'],
            callback=lambda: game.change_state(PokedexState(game, self))
        )
        self.btn_end = Button(
            rect=(20, self.btn_dex.rect.bottom + 15, 250, 80), text="END GAME",
            font=game.assets.fonts['small'], callback=self.end_game_action, bg_color=RED
        )
        
        self.boss_manager = BossManager(game)
        self.load_next_batch()

    def start(self):
        self.game.ui_manager.add_element(self.vol_slider)
        self.game.ui_manager.add_element(self.btn_dex)
        self.game.ui_manager.add_element(self.btn_end)

    def load_next_batch(self):
        raw = self.game.loader.get_batch()
        if not raw: return # Should handle waiting state if needed
        
        self.current_raw = raw
        self.question_timer = 15 * FPS

        if not self.boss_manager.in_boss_mode:
            self.problem_str, self.correct_ans, self.options = self.generate_math_set(self.total_caught)

        self.p_data = [Pokemon(p, self.game.assets) if p['id'] != 0 else None for p in raw['normal']]
        
        self.idle_sparkles = []
        for i, p in enumerate(self.p_data):
            if p and p.is_shiny:
                self.idle_sparkles.append((IdleSparkle(0,0), i))
                self.starbursts.append(ShinyBurst(self.get_cx(i), self.sprite_y))
                if self.game.assets.shiny_sfx: self.game.assets.shiny_sfx.play() # cite: 1

    def generate_math_set(self, score=0):
        # New scaling logic based on total catches (score)
        if score <= 5:
            sum_limit = 10
            sub_digit_limit = 15
        elif score <= 15:
            sum_limit = 20
            sub_digit_limit = 20
        elif score <= 25:
            sum_limit = 25
            sub_digit_limit = 25
        else: # score > 25
            sum_limit = score
            sub_digit_limit = score
        
        p_type = random.choice([1, 2, 3])
        op = random.choice(['+', '-'])
        
        if op == '+':
            c = random.randint(2, sum_limit)
            a = random.randint(1, c - 1)
            b = c - a
        else:
            a = random.randint(2, sub_digit_limit)
            b = random.randint(1, a - 1)
            c = a - b
            
        if p_type == 1: # A +/- B = ?
            problem_str = f"{a} {op} {b} = ?"
            ans = c
            opts = {c}
            while len(opts) < 3:
                f = c + random.randint(-5, 5)
                if f >= 0 and f != c: opts.add(f)
            options = sorted(list(opts), key=lambda x: random.random())
            
        elif p_type == 2: # A +/- ? = C
            if random.random() < 0.5:
                problem_str = f"? {op} {b} = {c}"
                ans = a
            else:
                problem_str = f"{a} {op} ? = {c}"
                ans = b
            opts = {ans}
            while len(opts) < 3:
                f = ans + random.randint(-5, 5)
                if f >= 0 and f != ans: opts.add(f)
            options = sorted(list(opts), key=lambda x: random.random())
            
        else: # C = ? (Equation)
            problem_str = f"{c} = ?"
            ans = f"{a} {op} {b}"
            options = [ans]
            while len(options) < 3:
                w_op = random.choice(['+', '-'])
                if w_op == '+':
                    w_c = random.randint(2, sum_limit)
                    while w_c == c: w_c = random.randint(2, sum_limit)
                    w_a = random.randint(1, w_c - 1)
                    w_b = w_c - w_a
                else:
                    w_a = random.randint(2, sub_digit_limit)
                    w_b = random.randint(1, w_a - 1)
                    w_c = w_a - w_b
                    while w_c == c:
                        w_a = random.randint(2, sub_digit_limit)
                        w_b = random.randint(1, w_a - 1)
                        w_c = w_a - w_b
                w_eq = f"{w_a} {w_op} {w_b}"
                if w_eq not in options: options.append(w_eq)
            random.shuffle(options)
            
        return problem_str, ans, options

    def get_cx(self, i):
        if self.game.assets.is_pc:
            return self.game.width // 2 + (i - 1) * (self.game.width // 6)
        return (i * self.game.width // 3) + (self.game.width // 6)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and not self.ball_active and self.pause_timer == 0:
                self.check_answer(event.pos)

    def update_volume_from_slider(self, new_volume):
        global VOLUME
        VOLUME = new_volume
        self._apply_volume_to_mixers()

    def _apply_volume_to_mixers(self):
        global VOLUME
        pygame.mixer.music.set_volume(VOLUME)
        if self.game.assets.shiny_sfx: self.game.assets.shiny_sfx.set_volume(VOLUME)
        if self.game.assets.heal_sfx: self.game.assets.heal_sfx.set_volume(VOLUME)
        for p in self.p_data:
            if p: p.set_volume(VOLUME)

    def end_game_action(self):
        self.balls_left = 0

    def check_answer(self, pos):
        for i, btn_rect in enumerate(self.answer_btn_rects):
            if btn_rect.width > 0 and btn_rect.collidepoint(pos):
                self.current_ball_img = random.choice(self.game.assets.ball_imgs)
                pi = self.boss_manager.boss_pokemon_data if self.boss_manager.in_boss_mode else self.p_data[i]
                is_shiny_catch = (not self.boss_manager.in_boss_mode and pi and pi.is_shiny)
                
                if self.options[i] == self.correct_ans or is_shiny_catch:
                    self.handle_correct(i, pi, is_shiny_catch, btn_rect.centerx)
                else:
                    self.handle_wrong(i, pi)
                return

    def handle_correct(self, idx, pi, is_shiny_catch, target_x):
        if self.boss_manager.in_boss_mode:
            self.boss_manager.boss_hits += 1
            self.feedback_text = "DIRECT HIT!" if self.boss_manager.boss_hits == 1 else "CRITICAL HIT!"
            self.feedback_color = YELLOW if self.boss_manager.boss_hits == 1 else GOLD
            self.ball_active = True
            self.ball_pos = [self.game.width//2, self.game.height]
            self.ball_target = [self.game.width//2, self.sprite_y]
            self.caught_idx = 1
        else:
            # Catch finalization is now handled in complete_catch
            self.feedback_text = "CAN'T PASS UP A SHINY!" if is_shiny_catch and self.options[idx] != self.correct_ans else f"YOU CAUGHT {pi.display_name.upper()}!"
            self.feedback_color = GOLD if pi.is_shiny else GREEN
            self.ball_active = True
            self.ball_pos = [self.game.width//2, self.game.height]
            self.ball_target = [target_x, self.sprite_y]
            self.caught_idx = idx

    def handle_wrong(self, idx, pi):
        self.balls_left -= 1
        self.current_streak = 0
        self.game.loader.shiny_charm_active = False
        if self.boss_manager.in_boss_mode:
            if pi and pi.cry: pi.cry.play()
            
            # Custom move attack text from movesets
            moves_data = self.game.assets.movesets.get(str(pi.id), {})
            moves = moves_data.get('moves', [])
            exclude_names = {"self-destruct", "explosion", "fissure", "guillotine", "horn drill", "sheer cold"}
            valid_moves = []
            for move in moves:
                m_lower = move.get('name', '').lower()
                power = move.get('power', 0)
                if m_lower not in exclude_names and power > 0:
                    valid_moves.append((power, move['name']))
            if valid_moves:
                valid_moves.sort(key=lambda x: x[0], reverse=True)
                top5 = valid_moves[:5]
                _, strong_move = random.choice(top5)
                self.feedback_text = f"{pi.display_name.upper()} USED {strong_move.upper()}!"
            else:
                self.feedback_text = f"{pi.display_name.upper()} ATTACKED!"
            
            self.shake_amount = 40
            self.pause_timer = 45
            self.ball_active = True
            self.ball_pos = [self.game.width//2, self.game.height]
            self.ball_target = [self.game.width//2, self.sprite_y]
            self.caught_idx = 1
            self.scr_shake_timer = 20
        else:
            self.feedback_text = "OH NO, THEY FLED!"
            self.feedback_color = RED
            self.pause_timer = 40
            self.flee_active = True
            self.caught_idx = idx
            self.ball_active = True
            self.ball_pos = [self.game.width//2, self.game.height]
            self.ball_target = [self.get_cx(idx), self.sprite_y]

    def handle_timeout(self):
        self.balls_left -= 1
        self.current_streak = 0
        self.game.loader.shiny_charm_active = False
        
        if self.boss_manager.in_boss_mode:
            pi = self.boss_manager.boss_pokemon_data
            if pi and pi.cry: pi.cry.play()
            
            moves_data = self.game.assets.movesets.get(str(pi.id), {})
            moves = moves_data.get('moves', [])
            exclude_names = {"self-destruct", "explosion", "fissure", "guillotine", "horn drill", "sheer cold"}
            valid_moves = []
            for move in moves:
                m_lower = move.get('name', '').lower()
                power = move.get('power', 0)
                if m_lower not in exclude_names and power > 0:
                    valid_moves.append((power, move['name']))
            if valid_moves:
                valid_moves.sort(key=lambda x: x[0], reverse=True)
                top5 = valid_moves[:5]
                _, strong_move = random.choice(top5)
                self.feedback_text = f"{pi.display_name.upper()} USED {strong_move.upper()}!"
            else:
                self.feedback_text = f"{pi.display_name.upper()} ATTACKED!"
            
            self.shake_amount = 40
            self.pause_timer = 45
            self.ball_active = True
            self.ball_pos = [self.game.width//2, self.game.height]
            self.ball_target = [self.game.width//2, self.sprite_y]
            self.caught_idx = 1
            self.scr_shake_timer = 20
        else:
            self.feedback_text = "THE POKEMON GOT AWAY!"
            self.feedback_color = RED
            self.pause_timer = 40
            self.flee_active = True
            self.caught_idx = 1
            self.ball_active = True
            self.ball_pos = [self.game.width//2, self.game.height]
            self.ball_target = [self.get_cx(1), self.sprite_y]

    def update(self):
        self.boss_manager.update()

        if self.balls_left <= 0:
            self.game.change_state(GameOverState(self.game))
            return

        if self.flash_timer > 0: self.flash_timer -= 1
        
        if self.boss_manager.boss_intro_timer > 0:
            return

        if self.pause_timer == 0 and not self.ball_active:
            self.question_timer -= 1
            if self.question_timer <= 0:
                self.handle_timeout()

        # Ball Animation
        if self.ball_active:
            self.ball_pos[0] += (self.ball_target[0] - self.ball_pos[0]) * 0.25
            self.ball_pos[1] += (self.ball_target[1] - self.ball_pos[1]) * 0.25
            if abs(self.ball_pos[1] - self.ball_target[1]) < 10:
                self.ball_active = False
                self.pause_timer = 35
                self.resolve_catch()

        # Pause Timer
        if self.pause_timer > 0:
            self.pause_timer -= 1
            if self.pause_timer == 1:
                self.reset_round()
        
        # Particles
        for sb in self.starbursts: sb.update()
        if self.pause_timer == 0 and not self.ball_active:
            for sparkle, idx in self.idle_sparkles:
                cx = self.get_cx(idx)
                sparkle.update(cx + (random.randint(-15, 15) if self.scr_shake_timer > 0 else 0), self.sprite_y - (self.game.width * 0.15))

    def resolve_catch(self):
        # Play cry if this wasn't a flee or boss attack
        if not self.flee_active:
            if 0 <= self.caught_idx < len(self.p_data) and self.p_data[self.caught_idx]:
                if self.p_data[self.caught_idx].cry:
                    self.p_data[self.caught_idx].cry.play()

        # ───────────────────────────────────────────────
        # Boss mode handling
        # ───────────────────────────────────────────────
        if self.boss_manager.in_boss_mode:
            # This was a correct answer → we hit the boss
            if self.feedback_text in ("DIRECT HIT!", "CRITICAL HIT!"):
                self.boss_manager.boss_hp -= 1
                
                if self.boss_manager.boss_hp <= 0:
                    # Boss defeated → catch it
                    self.complete_catch(
                        self.caught_idx,
                        self.current_raw['boss']['img'].hex()
                    )
                else:
                    # Boss still alive → new math problem
                    self.problem_str, self.correct_ans, self.options = self.generate_math_set(self.total_caught)
                    self.question_timer = 15 * FPS
            
            # This was a wrong answer → boss attacked us
            else:
                # Regenerate math problem after boss attack
                self.problem_str, self.correct_ans, self.options = self.generate_math_set(self.total_caught)
                self.question_timer = 15 * FPS

        # Normal (non-boss) catch
        elif not self.flee_active:
            # Regular successful catch
            self.complete_catch(
                self.caught_idx,
                self.current_raw['normal'][self.caught_idx]['img'].hex()
            )

    def complete_catch(self, idx, img_hex):
        pokemon_caught = self.p_data[idx]
        self.total_caught += 1
        self.game.loader.total_caught = self.total_caught
        self.current_streak += 1
        self.collected_team.append(pokemon_caught)
        if self.total_caught >= 5:
            self.mega_unlocked = True
        if self.total_caught >= 10:
            self.gmax_unlocked = True
        if self.current_streak % 5 == 0:
            self.balls_left += 1
            self.flash_msg = "+1 BALL!"
            self.flash_timer = 60
        if self.current_streak == 10:
            self.game.loader.shiny_charm_active = True
            self.starbursts.append(ShinyBurst(self.game.width//2, self.game.height//2))
            self.flash_msg = "SHINY CHARM ACTIVATED!"
            self.flash_timer = 80
            if self.game.assets.shiny_sfx: self.game.assets.shiny_sfx.play()

        self.game.data.add_pokemon(pokemon_caught, img_hex)
        if self.total_caught > self.game.data.get_high_score():
            self.game.data.set_high_score(self.total_caught)
        if pokemon_caught.is_shiny:
            self.game.data.add_shiny()
            self.starbursts.append(ShinyBurst(self.ball_target[0], self.ball_target[1]))
            if self.game.assets.shiny_sfx: self.game.assets.shiny_sfx.play() # cite: 1
        else:
            if not self.boss_manager.in_boss_mode: self.starbursts.append(Starburst(self.ball_target[0], self.ball_target[1], WHITE))
        
        self.game.data.save() # cite: 1
        self.pause_timer = 90 if self.boss_manager.in_boss_mode else 40
        self.feedback_text = f"YOU CAUGHT {pokemon_caught.display_name.upper()}!"

    def reset_round(self):
        self.starbursts, self.idle_sparkles, self.scr_shake_timer, self.shake_amount = [], [], 0, 0
        self.feedback_text, self.caught_idx, self.flee_active, self.runaway_x_offsets = "", -1, False, [0, 0, 0]
        
        # If boss was defeated, reset boss manager
        if self.boss_manager.in_boss_mode and self.boss_manager.boss_hp <= 0:
            self.boss_manager.in_boss_mode = False
            self.boss_manager.boss_pokemon_data = None
            pygame.event.clear() # Clear any lingering boss-related events
            # After a boss, always go to a normal round with new pokemon
            self.load_next_batch()
            return

        # If not in boss mode (or boss was just defeated), clear p_data
        if not self.boss_manager.in_boss_mode:
            self.p_data = [None] * 3
        
        # Decide if the next round is a boss round
        trigger_boss_round = False
        desired_boss_type = None

        if not self.boss_manager.in_boss_mode:
            if self.total_caught > 0 and self.total_caught % 5 == 0: # Every 5 catches is a boss round
                trigger_boss_round = True
                if self.total_caught >= 10 and self.total_caught % 10 == 0: # Prioritize GMAX every 10 catches
                    desired_boss_type = "GMAX"
                elif self.total_caught >= 5 and self.total_caught % 5 == 0: # Prioritize MEGA every 5 catches (if not GMAX)
                    desired_boss_type = "MEGA"
                else: # Other bosses for other multiples of 5
                    desired_boss_type = random.choice(["STANDARD", "UB", "PAST", "FUTURE", "MYTHICAL"])
            elif self.total_caught > 5 and random.random() < 0.25: # Random boss chance
                trigger_boss_round = True
                # Include unlocked boss types in random selection
                possible_random_bosses = ["STANDARD", "UB", "PAST", "FUTURE", "MYTHICAL"]
                if self.mega_unlocked: possible_random_bosses.append("MEGA")
                if self.gmax_unlocked: possible_random_bosses.append("GMAX")
                desired_boss_type = random.choice(possible_random_bosses)

            if trigger_boss_round:
                # Fetch the specific boss data
                raw_boss_data = self.game.loader._fetch_raw(desired_boss_type) # cite: 1
                
                # If the desired pool is exhausted, fall back to a standard boss
                if raw_boss_data and raw_boss_data['id'] == 0:
                    print(f"Pool '{desired_boss_type}' exhausted. Falling back to STANDARD.")
                    desired_boss_type = "STANDARD"
                    raw_boss_data = self.game.loader._fetch_raw(desired_boss_type)

                if raw_boss_data and raw_boss_data['id'] != 0:
                    self.boss_manager.start_boss_mode({'boss': raw_boss_data, 'boss_type': desired_boss_type})
                    self.p_data = [None, self.boss_manager.boss_pokemon_data, None]
                    self.runaway_x_offsets = [0, 0, 0]
                    self.problem_str, self.correct_ans, self.options = self.generate_math_set(self.total_caught)
                    self.question_timer = 15 * FPS
                    if self.boss_manager.boss_pokemon_data.is_shiny:
                        self.idle_sparkles = [(IdleSparkle(0,0), 1)]
                        self.starbursts.append(ShinyBurst(self.game.width // 2, self.sprite_y))
                        if self.game.assets.shiny_sfx: self.game.assets.shiny_sfx.play()
                else:
                    # All boss pools might be exhausted, so just do a normal round
                    self.load_next_batch()
            else:
                self.load_next_batch()
    def draw(self):
        screen = self.game.screen
        width, height = self.game.width, self.game.height
        offset_x, offset_y = 0, 0
        if self.scr_shake_timer > 0:
            offset_x, offset_y = random.randint(-15, 15), random.randint(-15, 15)

        # Background
        if self.boss_manager.draw(screen, width, height, offset_x, offset_y):
            return
        
        # If not in boss mode, draw normal starfield background
        if not self.boss_manager.in_boss_mode:
            screen.fill(BLACK)
            warp_speed = 15 if self.ball_active else 1
            spd_base = 10 if (self.pause_timer > 0 and (self.flee_active or self.caught_idx != -1)) else 1
            for s in self.stars:
                s[1] += s[2] * spd_base * warp_speed
                if s[1] > height: s[1], s[0] = 0, random.randint(0, width)
                pygame.draw.circle(screen, (150, 150, 150), (s[0] + offset_x, s[1] + offset_y), 1)
        
        lbl_balls = self.game.assets.fonts['small'].render("Balls Remaining: ", True, GREEN)
        screen.blit(lbl_balls, (20 + offset_x, 20 + offset_y))
        screen.blit(self.game.assets.ui_ball, (20 + lbl_balls.get_width() + 5 + offset_x, 15 + offset_y))
        Utils.draw_text_outline(screen, f": {self.balls_left}", self.game.assets.fonts['small'], WHITE, 20 + lbl_balls.get_width() + 5 + offset_x + self.game.assets.ui_ball.get_width() + 5, 20 + offset_y, align="left")
        Utils.draw_text_outline(screen, f"Current Streak: {self.current_streak}", self.game.assets.fonts['small'], YELLOW, 20 + offset_x, 80 + offset_y, align="left")
        Utils.draw_text_outline(screen, f"Best Streak: {self.game.data.get_high_score()}", self.game.assets.fonts['small'], GOLD, 20 + offset_x, 140 + offset_y, align="left")

        lbl_shiny = self.game.assets.fonts['small'].render("Shinies ", True, GOLD)
        screen.blit(lbl_shiny, (20 + offset_x, 200 + offset_y))
        Utils.draw_star(screen, GOLD, (20 + lbl_shiny.get_width() + 15 + offset_x, 215 + offset_y), 15)
        Utils.draw_text_outline(screen, f": {self.game.data.get_total_shinies()}", self.game.assets.fonts['small'], WHITE, 20 + lbl_shiny.get_width() + 35 + offset_x, 200 + offset_y, align="left")

        # Volume
        Utils.draw_text_outline(screen, "VOL", self.game.assets.fonts['tiny'], WHITE, 110, height - 35, align="right")
        self.vol_slider.draw(screen)
            
        # UI elements
        self.btn_dex.draw(screen)
        self.btn_end.draw(screen)

        # Team
        for i, tp in enumerate(self.collected_team[-6:]):
            col, row = i % 3, i // 3
            if self.game.assets.is_pc:
                unit = int(width * 0.05)
                spacing = int(unit * 1.1)
                sx = width - int(width * 0.02) - ((3 - col) * spacing)
                sy = int(height * 0.02) + (row * spacing)
            else:
                sx = width - (width * 0.42) + (col * (width * 0.13))
                sy = 20 + (row * (width * 0.14))
            if tp and tp.sidebar_image:
                screen.blit(tp.sidebar_image, (sx + offset_x, sy + offset_y))

        # Sprites & Sparkles
        if self.pause_timer == 0 and not self.ball_active:
            for sparkle, idx in self.idle_sparkles:
                sparkle.draw(screen)
        for sb in self.starbursts: sb.draw(screen)

        # Draw Pokemon (or Boss)
        for i in range(3):
            cx = self.get_cx(i)
            p_info = self.boss_manager.boss_pokemon_data if self.boss_manager.in_boss_mode and i == 1 else (self.p_data[i] if i < len(self.p_data) else None)
            if p_info and p_info.image:
                # Animation logic for caught/fleeing/shaking
                if (self.ball_active or self.pause_timer > 0 or self.flee_active) and self.caught_idx != -1:
                    if self.flee_active and not self.boss_manager.in_boss_mode:
                        self.runaway_x_offsets[i] += 35 if i > 1 else -35
                    elif i != self.caught_idx:
                        self.runaway_x_offsets[i] += 30 if i > self.caught_idx else -30
                
                sk = random.randint(-self.shake_amount, self.shake_amount) + (random.randint(-5, 5) if self.boss_manager.in_boss_mode else 0)
                bounce = abs(math.sin(pygame.time.get_ticks() * 0.02) * 30) if self.runaway_x_offsets[i] != 0 else 0 # cite: 1
                wiggle = math.sin(pygame.time.get_ticks() * 0.12) * 25 if (self.ball_active and not self.flee_active and i == self.caught_idx) else 0
                hover_y = math.sin(pygame.time.get_ticks() * p_info.bob_speed + p_info.bob_offset) * p_info.bob_amount # cite: 1
                dx, dy = ((width // 2 if self.boss_manager.in_boss_mode else cx) + self.runaway_x_offsets[i] + sk + offset_x + wiggle, self.sprite_y + sk + offset_y - bounce + hover_y)
                
                should_hide = (self.pause_timer > 0) and i == self.caught_idx and not self.flee_active and not (self.boss_manager.in_boss_mode and self.boss_manager.boss_hp > 0)
                if not should_hide:
                    screen.blit(p_info.image, p_info.image.get_rect(center=(dx, dy)))
            
            # Draw answer buttons
            if self.pause_timer == 0:
                txt = str(self.options[i])
                font = self.game.assets.fonts['num']
                if len(txt) > 3: font = self.game.assets.fonts['s_med']

                text_surf = font.render(txt, True, WHITE)
                padding_x = 30
                padding_y = 20
                btn_w = text_surf.get_width() + padding_x
                btn_h = text_surf.get_height() + padding_y

                cy = height * 0.75
                # Offset the middle button (index 1) downwards if it's an equation question (C = ?)
                # We can detect this by checking if the answer contains an operator
                if i == 1 and any(op in txt for op in ['+', '-']):
                    cy += btn_h + 10
                btn_rect = pygame.Rect(cx - btn_w // 2, cy - btn_h // 2, btn_w, btn_h)
                self.answer_btn_rects[i] = btn_rect

                pygame.draw.rect(screen, BLUE, btn_rect, border_radius=25)
                Utils.draw_text_outline(screen, txt, font, WHITE, btn_rect.centerx, btn_rect.centery)
        # Shiny Charm and Mega Symbol indicators in side UI
        indicator_y = self.btn_end.rect.bottom + 20

        if self.game.loader.shiny_charm_active and self.game.assets.shiny_charm:
            charm_rect = self.game.assets.shiny_charm.get_rect(topleft=(20, indicator_y))
            screen.blit(self.game.assets.shiny_charm, charm_rect)
            indicator_y = charm_rect.bottom + 10
        
        if self.gmax_unlocked and self.game.assets.dynamax_band:
            dynamax_rect = self.game.assets.dynamax_band.get_rect(topleft=(20, indicator_y))
            screen.blit(self.game.assets.dynamax_band, dynamax_rect)
            indicator_y = dynamax_rect.bottom + 10

        if self.game.assets.mega_symbol and self.total_caught >= 10:
            mega_rect = self.game.assets.mega_symbol.get_rect(topleft=(20, indicator_y))
            screen.blit(self.game.assets.mega_symbol, mega_rect)

        # Draw problem string
        if self.pause_timer == 0:
            Utils.draw_text_outline(screen, self.problem_str, self.game.assets.fonts['big'], YELLOW, width // 2, height * 0.15) # cite: 1
        
        # Draw flash messages and feedback text
        if self.flash_timer > 0:
            Utils.draw_text_outline(screen, self.flash_msg, self.game.assets.fonts['s_med'], GOLD, width//2, height//2)
        if self.pause_timer > 0:
            Utils.draw_text_outline(screen, self.feedback_text, self.game.assets.fonts['s_med'], self.feedback_color, width // 2, height * 0.35)

        if self.ball_active:
            screen.blit(self.current_ball_img, (self.ball_pos[0]-42, self.ball_pos[1]-42))

class PokedexState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.current_tab = "normal"
        self.page = 0
        self.show_shinies_only = False
        self.full_dex = []
        self.refresh_dex()
        
        tab_y = game.height * 0.18
        tab_h = 50
        
        # Initialize UI elements
        self.btn_back = Button(
            rect=(30, 30, 140, 70), text="BACK", font=game.assets.fonts['small'],
            callback=lambda: game.change_state(self.previous_state), bg_color=RED
        )
        self.btn_shiny_toggle = Button(
            rect=(game.width - 250, 30, 220, 70), text="SHINIES", font=game.assets.fonts['small'],
            callback=self.toggle_shiny_filter, bg_color=BLUE # Initial color
        )
        btn_y = game.height - 80
        self.btn_wipe = Button(
            rect=(30, btn_y, 220, 60), text="WIPE DATA", font=game.assets.fonts['tiny'],
            callback=self.confirm_wipe_action, bg_color=DARK_RED
        )
        self.btn_dev = Button(
            rect=(game.width - 250, btn_y, 220, 60), text="DEV MODE", font=game.assets.fonts['tiny'],
            callback=self.toggle_dev_mode, bg_color=BLACK # Initial color
        )
        
        self.btn_tab_normal = Button(rect=(game.width*0.1, tab_y, 200, tab_h), text="NORMAL", font=game.assets.fonts['tiny'], callback=lambda: self.set_tab("normal"))
        self.btn_tab_mega = Button(rect=(self.btn_tab_normal.rect.right + 10, tab_y, 200, tab_h), text="MEGA", font=game.assets.fonts['tiny'], callback=lambda: self.set_tab("mega"))
        self.btn_tab_gmax = Button(rect=(self.btn_tab_mega.rect.right + 10, tab_y, 200, tab_h), text="GMAX", font=game.assets.fonts['tiny'], callback=lambda: self.set_tab("gmax"))
        self.btn_tab_alt = Button(rect=(self.btn_tab_gmax.rect.right + 10, tab_y, 200, tab_h), text="ALT", font=game.assets.fonts['tiny'], callback=lambda: self.set_tab("alt"))
        self.tab_buttons = [self.btn_tab_normal, self.btn_tab_mega, self.btn_tab_gmax, self.btn_tab_alt]

        # Center the tab buttons
        total_tab_width = sum(b.rect.width for b in self.tab_buttons) + (len(self.tab_buttons) - 1) * 10
        start_x = (game.width - total_tab_width) / 2
        current_x = start_x
        for btn in self.tab_buttons:
            btn.rect.x = current_x
            current_x += btn.rect.width + 10

        self.btn_prev = pygame.Rect(game.width * 0.3, game.height * 0.85, 150, 70)
        self.btn_next = pygame.Rect(game.width * 0.6, game.height * 0.85, 150, 70)
        self.dex_btns = []

    def start(self):
        self.game.ui_manager.add_element(self.btn_back)
        self.game.ui_manager.add_element(self.btn_shiny_toggle)
        self.game.ui_manager.add_element(self.btn_wipe)
        self.game.ui_manager.add_element(self.btn_dev)
        for btn in self.tab_buttons:
            self.game.ui_manager.add_element(btn)

    def refresh_dex(self):
        self.full_dex = list(self.game.data.data["pokedex"].values())
        self.full_dex = [p for p in self.full_dex if p.get('form', 'normal') == self.current_tab]
        if self.show_shinies_only:
            self.full_dex = [p for p in self.full_dex if p['shiny']]
        self.full_dex.sort(key=lambda x: x['id'])

    def set_tab(self, tab_name):
        self.current_tab = tab_name
        self.page = 0
        self.refresh_dex()

    def toggle_shiny_filter(self):
        self.show_shinies_only = not self.show_shinies_only
        self.page = 0
        self.refresh_dex()
        self.btn_shiny_toggle.bg_color = GOLD if self.show_shinies_only else BLUE

    def toggle_dev_mode(self):
        if not self.game.loader.dev_shiny_mode:
            # Turning ON -> Check
            if self.do_parental_check():
                self.game.loader.dev_shiny_mode = True
                self.btn_dev.bg_color = GREEN
        else:
            # Turning OFF -> No check needed
            self.game.loader.dev_shiny_mode = False
            self.btn_dev.bg_color = BLACK

    def do_parental_check(self):
        a = random.randint(12, 19)
        b = random.randint(3, 9)
        ans = a * b
        options = {ans} # Use a set to ensure unique options
        while len(options) < 10:
            fake = ans + random.randint(-12, 12)
            if fake > 0 and fake != ans:
                options.add(fake)
        
        options_list = list(options)
        random.shuffle(options_list)

        checking = True

        cx, cy = self.game.width // 2, self.game.height // 2

        bw, bh = 500, 350
        box_rect = pygame.Rect(cx - bw//2, cy - bh//2, bw, bh)

        # Button layout (adjusted for better spacing)
        btn_w, btn_h = 70, 45
        gap_x, gap_y = 15, 20
        
        # Calculate start position to center the grid of buttons
        total_grid_w = (5 * btn_w) + (4 * gap_x) # 5 buttons, 4 gaps
        start_x = cx - (total_grid_w // 2)
        start_y = box_rect.top + 160
        
        buttons = []
        for i, val in enumerate(options_list):
            row = i // 5
            col = i % 5
            bx = start_x + col * (btn_w + gap_x)
            by = start_y + row * (btn_h + gap_y)
            buttons.append((pygame.Rect(bx, by, btn_w, btn_h), val))

        while checking:

            # Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if not box_rect.collidepoint(event.pos):
                        return False
                    
                    for rect, val in buttons:
                        if rect.collidepoint(event.pos):
                            return (val == ans)

            # Drawing
            self.draw() # Redraw the Pokedex screen as the background

            # Draw the popup box on top
            pygame.draw.rect(self.game.screen, WHITE, box_rect, border_radius=15)
            pygame.draw.rect(self.game.screen, BLACK, box_rect, 4, border_radius=15)
            

            Utils.draw_text_outline(self.game.screen, "PARENTAL CHECK", self.game.assets.fonts['med'], BLACK, cx, box_rect.top + 40, outline_color=WHITE)
            Utils.draw_text_outline(self.game.screen, f"{a} x {b} = ?", self.game.assets.fonts['big'], BLACK, cx, box_rect.top + 100, outline_color=WHITE)

            # Draw Buttons
            mouse_pos = pygame.mouse.get_pos()
            for rect, val in buttons:
                is_hover = rect.collidepoint(mouse_pos)
                bg = LIGHT_GRAY if is_hover else WHITE
                pygame.draw.rect(self.game.screen, bg, rect, border_radius=8)
                pygame.draw.rect(self.game.screen, BLACK, rect, 2, border_radius=8)
                Utils.draw_text_outline(self.game.screen, str(val), self.game.assets.fonts['s_med'], BLACK, rect.centerx, rect.centery, outline_color=WHITE)

            pygame.display.flip()
            self.game.clock.tick(25)

        return False

    def confirm_wipe_action(self):
        # This method will be called by the button. It then calls the blocking confirm_wipe.
        self.confirm_wipe()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.btn_next.collidepoint(event.pos) and (self.page + 1) * 12 < len(self.full_dex): # cite: 1
                    self.page += 1
                elif self.btn_prev.collidepoint(event.pos) and self.page > 0:
                    self.page -= 1
                else:
                    for r, cry_hex in self.dex_btns:
                        if r.collidepoint(event.pos):
                            try:
                                cry_sound = pygame.mixer.Sound(io.BytesIO(bytes.fromhex(cry_hex)))
                                cry_sound.set_volume(VOLUME)
                                cry_sound.play()
                            except Exception:
                                pass
                            
    def confirm_wipe(self):
        # Simple blocking confirmation loop for safety
        confirming = True
        while confirming:
            pygame.draw.rect(self.game.screen, BLACK, (self.game.width // 4, self.game.height // 3, self.game.width // 2, self.game.height // 3))
            Utils.draw_text_outline(self.game.screen, "WIPE ALL DATA?", self.game.assets.fonts['small'], RED, self.game.width // 2, self.game.height // 2 - 30)
            by = pygame.Rect(self.game.width//2 - 110, self.game.height//2 + 20, 100, 60)
            bn = pygame.Rect(self.game.width//2 + 10, self.game.height//2 + 20, 100, 60) # cite: 1
            pygame.draw.rect(self.game.screen, RED, by)
            pygame.draw.rect(self.game.screen, GREEN, bn)
            Utils.draw_text_outline(self.game.screen, "YES", self.game.assets.fonts['tiny'], WHITE, by.centerx, by.centery)
            Utils.draw_text_outline(self.game.screen, "NO", self.game.assets.fonts['tiny'], WHITE, bn.centerx, bn.centery) # cite: 1
            pygame.display.flip()
            for e in pygame.event.get():
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if by.collidepoint(e.pos):
                        if self.game.assets.heal_sfx: self.game.assets.heal_sfx.play()
                        self.game.data.wipe_data()
                        self.refresh_dex()
                        confirming = False
                    if bn.collidepoint(e.pos):
                        confirming = False

    def update(self): pass

    def draw(self):
        screen = self.game.screen
        width, height = self.game.width, self.game.height
        screen.fill(WHITE)
        pygame.draw.circle(screen, RED, (width//2, height//2), width)
        pygame.draw.rect(screen, WHITE, (0, height//2, width, height//2))
        pygame.draw.line(screen, BLACK, (0, height//2), (width, height//2), 20)
        pygame.draw.circle(screen, BLACK, (width//2, height//2), 120)
        pygame.draw.circle(screen, WHITE, (width//2, height//2), 90)

        Utils.draw_text_outline(screen, "POKEDEX", self.game.assets.fonts['med'], BLACK, width // 2, height * 0.06, outline_color=WHITE)
        total_caught = len(self.game.data.data['pokedex'])
        Utils.draw_text_outline(screen, f"CAUGHT: {total_caught}", self.game.assets.fonts['s_med'], BLACK, width // 2, height * 0.12, outline_color=WHITE)
        
        cols, rows = 4, 3
        per_page = cols * rows
        start_idx = self.page * per_page
        current_view = self.full_dex[start_idx : start_idx + per_page]
        
        for btn in self.tab_buttons:
            btn.bg_color = GREEN if btn.callback.__closure__[0].cell_contents == self.current_tab else BLUE

        self.dex_btns = []
        for i in range(per_page):
            c, r = i % cols, i // cols
            x = width * 0.15 + (c * (width * 0.23)) # cite: 1
            y = height * 0.32 + (r * (height * 0.20))
            rect = pygame.Rect(x - 60, y - 60, 120, 120)
            pygame.draw.rect(screen, (220, 220, 220), rect, border_radius=10)
            pygame.draw.rect(screen, BLACK, rect, 3, border_radius=10)
            
            if i < len(current_view):
                p_entry = current_view[i]
                Utils.draw_text_outline(screen, f"#{p_entry['id']}", self.game.assets.fonts['tiny'], BLACK, rect.centerx, rect.top - 20, outline_color=WHITE)
                Utils.draw_text_outline(screen, p_entry['name'].upper(), self.game.assets.fonts['tiny'], BLACK, rect.centerx, rect.bottom + 15, outline_color=WHITE)
                try:
                    if p_entry.get('img_hex'):
                        raw_img = bytes.fromhex(p_entry['img_hex'])
                        icon = pygame.transform.scale(pygame.image.load(io.BytesIO(raw_img)).convert_alpha(), (100, 100))
                        screen.blit(icon, icon.get_rect(center=rect.center))
                    else:
                        pygame.draw.circle(screen, GRAY, rect.center, 30)
                except Exception:
                    pygame.draw.circle(screen, GRAY, rect.center, 30)

                if p_entry['shiny']:
                    Utils.draw_star(screen, GOLD, (rect.right - 15, rect.top + 15), 12)
                
                if p_entry.get('cry_hex'):
                    self.dex_btns.append((rect, p_entry['cry_hex']))
            else:
                Utils.draw_text_outline(screen, "?", self.game.assets.fonts['med'], LIGHT_GRAY, rect.centerx, rect.centery)

        # Draw UI elements via UIManager
        self.game.ui_manager.draw(screen)
        # Update shiny toggle button color based on state
        self.btn_shiny_toggle.bg_color = GOLD if self.show_shinies_only else BLUE
        # Update dev mode button color based on state
        self.btn_dev.bg_color = GREEN if self.game.loader.dev_shiny_mode else BLACK
        
        pygame.draw.rect(screen, BLACK, self.btn_prev, border_radius=15)
        Utils.draw_text_outline(screen, "<", self.game.assets.fonts['s_med'], WHITE, self.btn_prev.centerx, self.btn_prev.centery)
        
        pygame.draw.rect(screen, BLACK, self.btn_next, border_radius=15)
        Utils.draw_text_outline(screen, ">", self.game.assets.fonts['s_med'], WHITE, self.btn_next.centerx, self.btn_next.centery)

class GameOverState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.btn_retry = Button(
            rect=(game.width//2 - 200, game.height * 0.60, 400, 80), text="RETRY",
            font=game.assets.fonts['s_med'], callback=self.retry_game, bg_color=GREEN
        )
        self.btn_reset = Button(
            rect=(game.width//2 - 200, game.height * 0.72, 400, 80), text="RESET STREAK",
            font=game.assets.fonts['s_med'], callback=self.reset_streak, bg_color=DARK_RED
        )
        self.btn_exit = Button(
            rect=(game.width//2 - 200, game.height * 0.84, 400, 80), text="EXIT GAME",
            font=game.assets.fonts['s_med'], callback=self.exit_game, bg_color=RED
        )

    def start(self):
        self.game.ui_manager.add_element(self.btn_retry)
        self.game.ui_manager.add_element(self.btn_reset)
        self.game.ui_manager.add_element(self.btn_exit)

    def handle_events(self, events):
        pass

    def retry_game(self):
        if self.game.assets.heal_sfx: self.game.assets.heal_sfx.play()
        self.game.change_state(PlayState(self.game))

    def reset_streak(self):
        if self.game.assets.heal_sfx: self.game.assets.heal_sfx.play()
        self.game.data.set_high_score(0)
        self.game.data.save()
        self.game.change_state(PlayState(self.game))

    def exit_game(self):
        pygame.quit()
        sys.exit()

    def update(self): pass

    def draw(self):
        screen = self.game.screen
        screen.fill(BLACK)
        if self.game.assets.go_img:
            screen.blit(self.game.assets.go_img, self.game.assets.go_img.get_rect(center=(self.game.width // 2, self.game.height * 0.35))) # cite: 1
        Utils.draw_text_outline(screen, "GAME OVER", self.game.assets.fonts['big'], RED, self.game.width // 2, self.game.height * 0.1)
        self.game.ui_manager.draw(screen)

# --- Main Game Class ---

class Game:
    def __init__(self):
        info = pygame.display.Info()
        self.width, self.height = info.current_w, info.current_h
        
        # Platform Detection
        self.is_pc = sys.platform in ['win32', 'linux', 'darwin']
        if self.is_pc:
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        else:
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)

        self.assets = AssetManager(self.width, self.height)
        self.data = DataManager(self.assets.base_dir)
        self.loader = PokemonLoader(self)
        
        self.ui_manager = UIManager()
        self.current_state = LoadingState(self)
        self.clock = pygame.time.Clock()
        self.current_song_index = 0
        
        if self.assets.music_playlist:
            self.play_music()

    def play_music(self):
        try:
            pygame.mixer.music.load(self.assets.music_playlist[self.current_song_index])
            pygame.mixer.music.set_volume(VOLUME)
            pygame.mixer.music.play()
            pygame.mixer.music.set_endevent(MUSIC_ENDED_EVENT)
        except Exception: pass

    def change_state(self, new_state):
        self.ui_manager.elements.clear()
        self.current_state = new_state
        self.current_state.start()

    def run(self):
        while True:
            # Android focus check
            if not pygame.display.get_active():
                pygame.time.wait(250)
                continue

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == MUSIC_ENDED_EVENT:
                    if self.assets.music_playlist:
                        self.current_song_index = (self.current_song_index + 1) % len(self.assets.music_playlist)
                        self.play_music()

            if not self.ui_manager.handle_events(events):
                self.current_state.handle_events(events)
            self.current_state.update()
            self.current_state.draw()
            
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    Game().run()
