import pygame
import random
import os
import math
from abc import ABC, abstractmethod
import json

# [REF-0001] Imports & System Initialization
# Sets up Pygame, Mixer, and basic window configuration.
pygame.mixer.pre_init(44100, -16, 2, 4096)
pygame.init()
pygame.mixer.init()

# [NEW REF-0001.5] ROUTE EVENT SYSTEM
class RouteEventSystem:
    def __init__(self, overworld):
        self.ow = overworld

    def walk_grass(self):
        self.ow.show_text("You step into the tall grass...")
        pygame.time.wait(400)
        self._trigger_wild()

    def search_trainers(self):
        self.ow.show_text("You search for trainers...")
        pygame.time.wait(400)
        self._trigger_trainer()

    def get_special_event(self, area_name):
        """Returns (Button Text, Callback) if a special event exists."""
        if "FOREST" in area_name:
            return ("Headbutt Tree", self._trigger_special_tree)
        if "MT MOON" in area_name:
            return ("Examine Rock", self._trigger_special_rock)
        return None

    def _trigger_wild(self):
        pool = self.ow.area_pools.get(self.ow.current_area_name, [(16, 10), (19, 10)])
        if pool and isinstance(pool[0], tuple):
            ids, weights = zip(*pool)
            enemy_id = random.choices(ids, weights=weights, k=1)[0]
        else:
            enemy_id = random.choice(pool)
        self.ow.start_battle(enemy_id, is_trainer=False)

    def _trigger_trainer(self):
        pool = self.ow.trainer_pools.get(self.ow.current_area_name)
        if pool:
            trainer_name, enemy_id = random.choice(pool)
            self.ow.start_battle(enemy_id, is_trainer=True, trainer_name=trainer_name)
        else:
            self.ow.show_text("No trainers found here.")

    def _trigger_special_tree(self):
        self.ow.show_text("A Pokémon fell out of the tree!")
        self.ow.start_battle(10, is_trainer=False) # Caterpie

    def _trigger_special_rock(self):
        self.ow.show_text("A Geodude jumped out!")
        self.ow.start_battle(74, is_trainer=False)

# [REF-0002] Constants & Configuration
WIDTH, HEIGHT = 1024, 768

# [REF-0002.5] Intro sequence + Save system
STATE_SPLASH = "SPLASH"
STATE_CHAR_SELECT = "CHAR_SELECT"
STATE_STARTER_SELECT = "STARTER_SELECT"
STATE_FIRST_BATTLE = "FIRST_BATTLE"

KANTO_STARTERS = [1, 4, 7, 25]   # Bulbasaur, Charmander, Squirtle, Pikachu
POOCHYENA_ID = 261
SAVE_FILE = "pokemath_save.json"
SAVE_ICON_SIZE = (56, 56)

# [REF-0003] Colors & Fonts
WHITE, BLACK = (255, 255, 255), (10, 10, 10)
GREEN, RED, YELLOW, GOLD = (50, 255, 50), (255, 50, 50), (255, 255, 0), (255, 215, 0)
DARK_GREEN, GRAY, BLUE = (34, 139, 34), (50, 50, 50), (50, 50, 255)
PURPLE, CYAN, ORANGE = (128, 0, 128), (0, 255, 255), (255, 165, 0)
HP_GREEN, HP_YELLOW, HP_RED = (112, 248, 168), (248, 224, 56), (248, 88, 56)
HOVER_BLUE = (80, 190, 255)      # Nice Pokémon-blue highlight
HOVER_LIGHT = (100, 180, 240)    # Softer blue for non-hover

GB_BORDER = (0, 0, 0)
GB_PANEL = (224, 192, 104)
GB_PANEL_DARK = (184, 152, 64)
GB_TEXT = (0, 0, 0)
GB_HIGHLIGHT = (255, 255, 200)

FONT_BIG = pygame.font.SysFont("impact", 64)
FONT_MED = pygame.font.SysFont("impact", 48)
FONT_SMALL = pygame.font.SysFont("arial", 28, bold=True)
FONT_UI = pygame.font.SysFont("arial", 32, bold=True)
FONT_MSG = pygame.font.SysFont("lucidaconsole", 36)

#=== OVERWORLD SUBMENUS ===#
BOTTOM_UI_Y = HEIGHT - 200          # ← back to your original 200px height
MAIN_TEXT_BOX_X = 20
MAIN_TEXT_BOX_Y = BOTTOM_UI_Y + 20
MAIN_TEXT_BOX_W = WIDTH - 40
MAIN_TEXT_BOX_H = 160

OVERLAY_X = 40
OVERLAY_Y = 20
OVERLAY_W = WIDTH - 80
OVERLAY_H = HEIGHT - 220

RIGHT_MENU_X = WIDTH - 305
RIGHT_MENU_Y = BOTTOM_UI_Y + 8
RIGHT_MENU_W = 280
RIGHT_MENU_H = 128


# [REF-0004] Asset Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# [REF-0005] Battle Constants & Positions
BATTLE_SCALE = 384
ENEMY_POS = [WIDTH - 420, 60]
PLAYER_POS = [80, 290]
ENEMY_HP_POS = [45, 48]
PLAYER_HP_POS = [520, 380]

BATTLE_MENU_MAIN      = 0
BATTLE_MENU_MATH      = 1
BATTLE_MENU_TURN      = 2
BATTLE_MENU_MOVES     = 3
BATTLE_MENU_BAG       = 4
BATTLE_MENU_PARTY     = 5
BATTLE_MENU_PARTY_SUB = 6
BATTLE_MENU_CATCH = 7
BATTLE_MENU_KO_CATCH  = 8
BATTLE_MENU_LEARN_MOVE = 9
BATTLE_MENU_VICTORY   = 10
BATTLE_MENU_FAINT_MSG = 11
BATTLE_MENU_SUMMARY   = 12
BATTLE_MENU_FAINT_ANIM = 13

POCKET_NAMES = ["ITEMS", "POKÉ BALLS", "KEY ITEMS"]

# [REF-0006] Asset Loading Helpers
def load_asset(filename, subfolder, size=None):
    path = os.path.join(os.path.dirname(__file__), "assets", subfolder, filename)
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
        return img
    return pygame.Surface(size or (100, 100)).convert_alpha()

def load_bg(filename, subfolder):
    """Load background. Falls back to TEST.png if the file is missing."""
    img = load_asset(filename, subfolder)
    if img and img.get_width() > 0:
        scale = WIDTH / img.get_width()
        new_h = int(img.get_height() * scale)
        return pygame.transform.scale(img, (WIDTH, new_h))
    print(f"⚠️  Missing background: {filename} → using TEST.png fallback")
    test_img = load_asset("TEST.png", subfolder)
    if test_img and test_img.get_width() > 0:
        scale = WIDTH / test_img.get_width()
        new_h = int(test_img.get_height() * scale)
        return pygame.transform.scale(test_img, (WIDTH, new_h))
    return None

# [REF-0007] UI Drawing Helpers (Text)
def draw_text(screen, text, font, text_col, x, y, center=True):
    img = font.render(text, True, text_col)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(img, rect)
    return rect

def draw_multiline_text(screen, text, font, text_col, x, y, max_width, line_height=None, center=True):
    if line_height is None:
        line_height = font.get_linesize()
    words = text.split(" ")
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        w, h = font.size(test_line)
        if w < max_width:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    lines.append(" ".join(current_line))
    total_height = len(lines) * line_height
    start_y = y - (total_height // 2)
    for i, line in enumerate(lines):
        draw_text(screen, line, font, text_col, x, start_y + i * line_height, center=center)

# [REF-0008] OVERWORLD MANAGER
# Point-and-Click Maps
class OverworldManager:
        # [REF-0008a] Initialization & Setup
    def __init__(self, screen, clock, player_bag):      
        self.screen = screen        
        self.clock = clock           
        
        self.current_area_name = "PALLET TOWN"
        self.current_screen = "city"
        self.areas: dict[str, Area] = {}
        self.explored_routes = set()
        self.player_bag = player_bag
        self.player_party = None
        self.text = ""
        self.text_done = True
        self.char_idx = 0
        self.text_timer = 0
        self.current_text = ""
        self.debug_mode = False               # Press D to see yellow boxes

        # === Area-specific wild Pokémon pools ===
        # Format: [(pokemon_id, weight), ...]
        self.area_pools = {
            "ROUTE 1 SOUTH": [(16, 40), (19, 20), (20, 3.5), (161, 8), (162, 3.5), (163, 25)],
            "ROUTE 1 NORTH": [(16, 40), (19, 20), (20, 3.5), (161, 8), (162, 3.5), (163, 25)],
            "ROUTE 2": [(10, 4.5), (11, 1.0), (12, 0.5), (13, 4.5), (14, 1.0), (15, 0.5), 
                       (16, 24.5), (17, 0.5), (19, 21.5), (25, 1.0), (29, 2.5), (32, 2.5), 
                       (163, 22.0), (164, 3.5), (165, 3.5), (166, 0.5), (167, 5.0), 
                       (168, 0.5)],
            "VIRIDIAN FOREST SOUTH": [(10, 24.5), (11, 8.5), (12, 1.0), (13, 24.5), (14, 8.5), 
                                 (15, 1.0), (16, 5.0), (17, 2.5), (25, 6.0), (163, 15.0), 
                                 (164, 3.5)],
            "VIRIDIAN FOREST NORTH": [(10, 24.5), (11, 8.5), (12, 1.0), (13, 24.5), (14, 8.5), 
                                 (15, 1.0), (16, 5.0), (17, 2.5), (25, 6.0), (163, 15.0), 
                                 (164, 3.5)],
            "ROUTE 3 WEST": [(16, 28.0), (19, 15.0), (21, 20.0), (27, 5.0), (39, 8.0), 
                            (163, 17.5), (164, 6.5)],
            "ROUTE 3 EAST": [(16, 28.0), (19, 15.0), (21, 20.0), (27, 5.0), (39, 8.0), 
                            (163, 17.5), (164, 6.5)],
            "MT MOON FLOOR 1": [(41, 74.0), (74, 20.0), (46, 5.0), (35, 1.0)],
            "MT MOON FLOOR 2": [(41, 55.0), (74, 35.0), (46, 8.0), (35, 2.0)],
            "MT MOON FLOOR 3": [(41, 45.0), (74, 40.0), (46, 10.0), (35, 5.0)],
            "ROUTE 4 WEST": [(19, 25.0), (21, 25.0), (23, 10.0), (27, 10.0), (163, 20.0), 
                            (164, 10.0)],
            "ROUTE 4 EAST": [(19, 25.0), (21, 25.0), (23, 10.0), (27, 10.0), (163, 20.0), 
                            (164, 10.0)],
            "ROUTE 5": [(16, 25.0), (19, 20.0), (39, 5.0), (43, 10.0), (52, 10.0), (63, 5.0), 
                       (161, 10.0), (163, 15.0)],
            "ROUTE 6": [(16, 25.0), (19, 20.0), (43, 10.0), (52, 10.0), (54, 5.0), (161, 10.0), 
                       (163, 15.0), (187, 5.0)],
            "ROUTE 24": [(10, 5.0), (13, 5.0), (11, 2.0), (14, 2.0), (16, 20.0), (43, 15.0), 
                        (48, 10.0), (63, 10.0), (163, 25.0), (164, 6.0)],
            "ROUTE 25": [(10, 5.0), (13, 5.0), (11, 2.0), (14, 2.0), (16, 15.0), (19, 15.0), 
                        (43, 15.0), (48, 10.0), (63, 10.0), (163, 15.0), (164, 6.0)],
        }

        # === TRAINER POOLS ===
        self.trainer_pools = {
            "ROUTE 1 SOUTH": [("Youngster", 19), ("Lass", 16)],
            "ROUTE 1 NORTH": [("Youngster", 19), ("Lass", 16)],
            "ROUTE 2": [("Bug Catcher", 10), ("Youngster", 21), ("Lass", 29)],
            "VIRIDIAN FOREST SOUTH": [("Bug Catcher", 13), ("Bug Catcher", 10)],
            "VIRIDIAN FOREST NORTH": [("Bug Catcher", 14), ("Lass", 25)],
            "ROUTE 3 WEST": [("Youngster", 21), ("Lass", 39)],
            "ROUTE 3 EAST": [("Youngster", 21), ("Lass", 39)],
            "MT MOON FLOOR 1": [("Hiker", 74), ("Lass", 35)],
            "MT MOON FLOOR 2": [("Rocket Grunt", 41), ("Rocket Grunt", 19)],
            "MT MOON FLOOR 3": [("Rocket Grunt", 23), ("Super Nerd", 88)],
            "ROUTE 4 WEST": [("Lass", 39), ("Youngster", 21)],
            "ROUTE 4 EAST": [("Lass", 39), ("Youngster", 21)],
            "ROUTE 24": [("Camper", 66), ("Lass", 43), ("Rival", 8)],
            "ROUTE 25": [("Hiker", 74), ("Youngster", 17)],
            "ROUTE 6": [("Camper", 7), ("Picnicker", 1)],
        }

        # === CLEAN MENU SYSTEM (ALL navigation now here) ===
        self.menu_active = False
        self.menu_title = ""
        self.menu_options = []
        self.menu_style = "LIST"
        self.menu_rects = []
        # === OVERWORLD SUBMENU SYSTEM === #
        self.show_overlay = None
        self.active_bottom_button = 0
        self.bottom_button_rects = []
        self.ow_ui_mode = "ACTION"
        self.selected_option = -1

        self.route_events = RouteEventSystem(self)
                # === RULEBOOK SAVE ICON (persistent top-left, overworld only) ===
        self.save_icon = load_asset("rulebook.png", "sprites/items", SAVE_ICON_SIZE)
        if not self.save_icon:  # fallback wooden book
            self.save_icon = pygame.Surface(SAVE_ICON_SIZE, pygame.SRCALPHA)
            pygame.draw.rect(self.save_icon, (139, 69, 19), (6, 4, 44, 48))
        self.save_rect = pygame.Rect(24, 18, *SAVE_ICON_SIZE)
        self.save_flash_timer = 0
        self.battle_running = False

        self.area_order = [
            "PALLET TOWN", "ROUTE 1 SOUTH", "ROUTE 1 NORTH", "VIRIDIAN CITY",
            "ROUTE 2", "VIRIDIAN FOREST SOUTH", "VIRIDIAN FOREST NORTH", "PEWTER CITY",
            "ROUTE 3 WEST", "ROUTE 3 EAST", "MT MOON CITY", "MT MOON FLOOR 1", 
            "MT MOON FLOOR 2", "MT MOON FLOOR 3", "ROUTE 4 WEST", "ROUTE 4 EAST", 
            "CERULEAN CITY", "ROUTE 5", "UNDERGROUND PATH", "ROUTE 6", 
            "VERMILION CITY", "ROUTE 24", "ROUTE 25",
        ]

        self.area_types = {
            "PALLET TOWN": "city",
            "VIRIDIAN CITY": "city",
            "PEWTER CITY": "city",
            "CERULEAN CITY": "city",
            "VERMILION CITY": "city",
            "MT MOON CITY": "city",
            "ROUTE 1 SOUTH": "route",
            "ROUTE 1 NORTH": "route",
            "ROUTE 2": "route",
            "ROUTE 3 WEST": "route",
            "ROUTE 3 EAST": "route",
            "ROUTE 4 WEST": "route",
            "ROUTE 4 EAST": "route",
            "ROUTE 5": "route",
            "ROUTE 6": "route",
            "ROUTE 24": "route",
            "ROUTE 25": "route",
            "UNDERGROUND PATH": "route",
            "MT MOON FLOOR 1": "route",
            "MT MOON FLOOR 2": "route",
            "MT MOON FLOOR 3": "route",
            "VIRIDIAN FOREST SOUTH": "forest",
            "VIRIDIAN FOREST NORTH": "forest",
        }

        self.previous_area = "PALLET TOWN"

        self._setup_areas()
        self.refresh_menu_options()
        self.menu_active = True
        self.show_text("Welcome to Pallet Town!")
        self.current_area_name = "PALLET TOWN"
        self.current_screen = "city"
        self.current_area_index = 0

        # === CLASSIC POKÉMON BOTTOM UI (matches your screenshots perfectly) ===
        self.active_bottom_button = 0        
        self.bottom_button_rects = []
        self.selected_option = -1
        self.ow_ui_mode = "ACTION"

        # Action menu now lives here...
        self.menu_title = ""
        self.menu_options = []
        self.menu_rects = []

    # [REF-0008b] Area Setup
    def _setup_areas(self):
        # === PALLET TOWN ===
        pallet = Area("PALLET TOWN")
        pallet.set_background("city", "pallet_city.png")
        pallet.set_background("lab", "pallet_lab.png")
        pallet.add_building(OaksLab("Oak's Lab", pygame.Rect(380, 420, 160, 100)))
        self.areas["PALLET TOWN"] = pallet
        pallet.custom_menu_options = [
            ("Oak's Lab", lambda: self.areas["PALLET TOWN"].buildings["Oak's Lab"].interact(self)),
            ("Go to Route 1 South", lambda: self.go_to_route1_south()),
        ]

        # === ROUTE 1 ===
        route1_south = Area("ROUTE 1 SOUTH")
        route1_south.add_segment("south", "kanto_route1_1.png")
        route1_south.current_bg_key = "south"
        self.areas["ROUTE 1 SOUTH"] = route1_south
        route1_south.custom_menu_options = []

        route1_north = Area("ROUTE 1 NORTH")
        route1_north.add_segment("north", "kanto_route1_2.png")
        route1_north.current_bg_key = "north"
        self.areas["ROUTE 1 NORTH"] = route1_north
        route1_north.custom_menu_options = []

        # === VIRIDIAN CITY ===
        viridian = Area("VIRIDIAN CITY")
        viridian.set_background("city", "viridian_city.png")
        viridian.set_background("center", "viridian_center.png")
        viridian.set_background("mart", "viridian_mart.png")
        viridian.set_background("gym", "viridian_gym.png")
        viridian.add_building(PokemonCenter("Pokémon Center", pygame.Rect(510, 380, 130, 110)))
        viridian.add_building(PokeMart("Poké Mart", pygame.Rect(725, 240, 120, 90)))
        viridian.add_building(Gym("Viridian Gym", pygame.Rect(710, 20, 155, 100)))
        viridian.add_building(InteriorBuilding("Rocky Helmet Guy", pygame.Rect(80, 300, 160, 130), bg_key="city"))
        self.areas["VIRIDIAN CITY"] = viridian
        viridian.custom_menu_options = [
            ("Pokémon Center", lambda: self.areas["VIRIDIAN CITY"].buildings["Pokémon Center"].interact(self)),
            ("Poké Mart",      lambda: self.areas["VIRIDIAN CITY"].buildings["Poké Mart"].interact(self)),
            ("Viridian Gym",   lambda: self.areas["VIRIDIAN CITY"].buildings["Viridian Gym"].interact(self)),
            ("Visit Friend",   lambda: self.areas["VIRIDIAN CITY"].buildings["Rocky Helmet Guy"].interact(self)),
            ("Go to Route 2",  lambda: self.go_to_route2()),
        ]

        # === ROUTE 2 ===
        route2 = Area("ROUTE 2")
        route2.add_segment("part1", "kanto_route2_1.png")
        route2.add_segment("part2", "kanto_route2_2.png")
        route2.current_bg_key = "part1"
        route2.current_segment = 0
        self.areas["ROUTE 2"] = route2
        route2.custom_menu_options = []

        # === VIRIDIAN FOREST ===
        forest1 = Area("VIRIDIAN FOREST SOUTH")
        forest1.add_segment("forest1", "kanto_viridianforest_1.png")
        forest1.current_bg_key = "forest1"
        self.areas["VIRIDIAN FOREST SOUTH"] = forest1
        forest1.custom_menu_options = []

        forest2 = Area("VIRIDIAN FOREST NORTH")
        forest2.add_segment("forest2", "kanto_viridianforest_2.png")
        forest2.current_bg_key = "forest2"
        self.areas["VIRIDIAN FOREST NORTH"] = forest2
        forest2.custom_menu_options = []

        # === PEWTER CITY ===
        pewter = Area("PEWTER CITY")
        pewter.set_background("city", "pewter_city.png")
        pewter.set_background("museum", "pewter_museum.png")
        pewter.set_background("center", "pewter_center.png")
        pewter.set_background("mart", "pewter_mart.png")
        pewter.set_background("gym", "pewter_gym.png")
        pewter.add_building(PewterMuseum("Pewter Museum", pygame.Rect(95, 48, 165, 105)))
        pewter.add_building(Gym("Pewter Gym", pygame.Rect(280, 160, 155, 100)))
        pewter.add_building(PokeMart("Poké Mart", pygame.Rect(620, 180, 130, 90)))
        pewter.add_building(PokemonCenter("Pokémon Center", pygame.Rect(340, 380, 130, 110)))
        self.areas["PEWTER CITY"] = pewter
        pewter.custom_menu_options = [
            ("Pewter Museum", lambda: self.areas["PEWTER CITY"].buildings["Pewter Museum"].interact(self)),
            ("Pewter Gym",    lambda: self.areas["PEWTER CITY"].buildings["Pewter Gym"].interact(self)),
            ("Poké Mart",     lambda: self.areas["PEWTER CITY"].buildings["Poké Mart"].interact(self)),
            ("Pokémon Center", lambda: self.areas["PEWTER CITY"].buildings["Pokémon Center"].interact(self)),
            ("Go to Route 3", lambda: self.go_to_route3_west()),
        ]

        # === ROUTE 3 ===
        route3_west = Area("ROUTE 3 WEST")
        route3_west.add_segment("part1", "kanto_route3_1.png")
        route3_west.current_bg_key = "part1"
        self.areas["ROUTE 3 WEST"] = route3_west
        route3_west.custom_menu_options = []

        route3_east = Area("ROUTE 3 EAST")
        route3_east.add_segment("part2", "kanto_route3_2.png")
        route3_east.current_bg_key = "part2"
        self.areas["ROUTE 3 EAST"] = route3_east
        route3_east.custom_menu_options = []

        # === MT MOON CITY ===
        mt_moon_city = Area("MT MOON CITY")
        mt_moon_city.set_background("city", "mtmoon_city.png")
        mt_moon_city.set_background("center", "mtmoon_center.png")
        mt_moon_city.add_building(PokemonCenter("Pokémon Center", pygame.Rect(510, 380, 130, 110)))
        self.areas["MT MOON CITY"] = mt_moon_city
        mt_moon_city.custom_menu_options = [
            ("Pokémon Center", lambda: self.areas["MT MOON CITY"].buildings["Pokémon Center"].interact(self)),
            ("Enter Mt. Moon", lambda: self.go_to_mtmoon1()),
            ("Return to Route 3", lambda: self.go_to_route3_east()),
        ]

        # === MT. MOON CAVE (3 sections only) ===
        for i in range(1, 4):
            mt = Area(f"MT MOON{i}")
            mt.add_segment(f"part{i}", f"kanto_mtmoon_{i}.png")
            mt.current_bg_key = f"part{i}"
            self.areas[f"MT MOON{i}"] = mt
            if i < 3:
                mt.custom_menu_options = []
            else:
                mt.custom_menu_options = []

        # === ROUTE 4 ===
        route4_west = Area("ROUTE 4 WEST")
        route4_west.add_segment("part1", "kanto_route4_1.png")
        route4_west.current_bg_key = "part1"
        self.areas["ROUTE 4 WEST"] = route4_west
        route4_west.custom_menu_options = []

        route4_east = Area("ROUTE 4 EAST")
        route4_east.add_segment("part2", "kanto_route4_2.png")
        route4_east.current_bg_key = "part2"
        self.areas["ROUTE 4 EAST"] = route4_east
        route4_east.custom_menu_options = []

        # === CERULEAN CITY ===
        cerulean = Area("CERULEAN CITY")
        cerulean.set_background("city", "cerulean_city.png")
        cerulean.set_background("center", "cerulean_center.png")
        cerulean.set_background("mart", "cerulean_mart.png")
        cerulean.set_background("gym", "cerulean_gym.png")
        cerulean.add_building(PokemonCenter("Pokémon Center", pygame.Rect(510, 380, 130, 110)))
        cerulean.add_building(PokeMart("Poké Mart", pygame.Rect(725, 240, 120, 90)))
        cerulean.add_building(Gym("Cerulean Gym", pygame.Rect(710, 20, 155, 100)))
        self.areas["CERULEAN CITY"] = cerulean
        cerulean.custom_menu_options = [
            ("Pokémon Center", lambda: self.areas["CERULEAN CITY"].buildings["Pokémon Center"].interact(self)),
            ("Poké Mart", lambda: self.areas["CERULEAN CITY"].buildings["Poké Mart"].interact(self)),
            ("Cerulean Gym", lambda: self.areas["CERULEAN CITY"].buildings["Cerulean Gym"].interact(self)),
            ("Head north (Route 24)", lambda: self.go_to_route24()),
            ("Head south (Route 5)", lambda: self.go_to_route5()),
        ]

        # === REMAINING AREAS === 
        for name in ["ROUTE 5", "ROUTE 6", "ROUTE 24", "ROUTE 25", "UNDERGROUND PATH"]:
            if name in self.areas:
                self.areas[name].custom_menu_options = []

        # === VERMILION CITY ===
        vermilion = Area("VERMILION CITY")
        vermilion.set_background("city", "vermilion_city.png")
        vermilion.set_background("center", "vermilion_center.png")
        vermilion.set_background("mart", "vermilion_mart.png")
        vermilion.set_background("gym", "vermilion_gym.png")
        vermilion.add_building(PokemonCenter("Pokémon Center", pygame.Rect(510, 380, 130, 110)))
        vermilion.add_building(PokeMart("Poké Mart", pygame.Rect(725, 240, 120, 90)))
        vermilion.add_building(Gym("Vermilion Gym", pygame.Rect(710, 20, 155, 100)))
        self.areas["VERMILION CITY"] = vermilion
        vermilion.custom_menu_options = [
            ("Pokémon Center", lambda: self.areas["VERMILION CITY"].buildings["Pokémon Center"].interact(self)),
            ("Poké Mart", lambda: self.areas["VERMILION CITY"].buildings["Poké Mart"].interact(self)),
            ("Vermilion Gym", lambda: self.areas["VERMILION CITY"].buildings["Vermilion Gym"].interact(self)),
        ]

        # Force clean start
        self.current_area_name = "PALLET TOWN"
        self.current_screen = "city"
        self.current_area_index = 0

        self.refresh_menu_options()
        self.menu_active = True
        self.show_overlay = None

    # [REF-0008c] Navigation & Transitions
    def enter_area(self, area_name: str, previous=None):
        """Universal way to move anywhere. Always sets correct back button."""
        if previous is None:
            previous = self.current_area_name  # fallback

        self.previous_area = previous
        self.current_area_name = area_name
        self.current_screen = self.area_types.get(area_name, "city")

        # Sync index for "Go to next area" system
        if area_name in self.area_order:
            self.current_area_index = self.area_order.index(area_name)

        self.show_overlay = None
        self.menu_active = True
        self.refresh_menu_options()
        self.show_text(f"You arrived in {area_name.replace('_', ' ').title()}!")
        self.show_text(f"You arrived in {area_name.replace('_', ' ').title()}!")
    
    def go_to_next_area(self):
        area = self.areas[self.current_area_name]

        # === ROUTE 3 → MT MOON CITY ===
        if self.current_area_name == "ROUTE 3 EAST":
            self.go_to_mtmoon_city()
            return

        # === MT MOON CITY → CAVE ===
        if self.current_area_name == "MT MOON CITY":
            self.go_to_mtmoon1()
            return

        # === CAVE EXIT (MT MOON FLOOR 3) → ROUTE 4 ===
        if self.current_area_name == "MT MOON FLOOR 3":
            self.go_to_route4_west()
            return

        # === NORMAL SEGMENT ADVANCE ===
        if area.segments and area.current_segment < len(area.segments) - 1:
            area.current_segment += 1
            area.current_bg_key = area.segments[area.current_segment]
            self.show_text(f"{self.current_area_name.replace('_', ' ')} — Part {area.current_segment + 1}")
            return

        # === NORMAL MAIN PATH ===
        self.current_area_index = (self.current_area_index + 1) % len(self.area_order)
        next_name = self.area_order[self.current_area_index]
        self.enter_area(next_name)

    # ====================== STANDARDIZED GO_TO WRAPPERS (from_area pattern for EVERY location) ======================
    def go_to_pallet(self, from_area=None):
        self.enter_area("PALLET TOWN", previous=from_area or self.current_area_name)

    def go_to_route1_south(self, from_area=None):
        self.enter_area("ROUTE 1 SOUTH", previous=from_area or self.current_area_name)

    def go_to_route1_north(self, from_area=None):
        self.enter_area("ROUTE 1 NORTH", previous=from_area or self.current_area_name)

    def go_to_viridian(self, from_area=None):
        self.enter_area("VIRIDIAN CITY", previous=from_area or self.current_area_name)

    def go_to_route2(self, from_area=None):
        self.enter_area("ROUTE 2", previous=from_area or self.current_area_name)

    def go_to_viridian_forest1(self, from_area=None):
        self.enter_area("VIRIDIAN FOREST SOUTH", previous=from_area or self.current_area_name)

    def go_to_viridian_forest2(self, from_area=None):
        self.enter_area("VIRIDIAN FOREST NORTH", previous=from_area or self.current_area_name)

    def go_to_pewter(self, from_area=None):
        self.enter_area("PEWTER CITY", previous=from_area or self.current_area_name)

    def go_to_route3_west(self, from_area=None):
        self.enter_area("ROUTE 3 WEST", previous=from_area or self.current_area_name)

    def go_to_route3_east(self, from_area=None):
        self.enter_area("ROUTE 3 EAST", previous=from_area or self.current_area_name)

    def go_to_mtmoon_city(self, from_area=None):
        self.enter_area("MT MOON CITY", previous=from_area or self.current_area_name)

    def go_to_mtmoon1(self, from_area=None):
        self.enter_area("MT MOON FLOOR 1", previous=from_area or self.current_area_name)

    def go_to_mtmoon2(self, from_area=None):
        self.enter_area("MT MOON FLOOR 2", previous=from_area or self.current_area_name)

    def go_to_mtmoon3(self, from_area=None):
        self.enter_area("MT MOON FLOOR 3", previous=from_area or self.current_area_name)

    def go_to_route4_west(self, from_area=None):
        self.enter_area("ROUTE 4 WEST", previous=from_area or self.current_area_name)

    def go_to_route4_east(self, from_area=None):
        self.enter_area("ROUTE 4 EAST", previous=from_area or self.current_area_name)

    def go_to_cerulean(self, from_area=None):
        self.enter_area("CERULEAN CITY", previous=from_area or self.current_area_name)

    def go_to_route5(self, from_area=None):
        self.enter_area("ROUTE 5", previous=from_area or self.current_area_name)

    def go_to_route24(self, from_area=None):
        self.enter_area("ROUTE 24", previous=from_area or self.current_area_name)

    def go_to_route25(self, from_area=None):
        self.enter_area("ROUTE 25", previous=from_area or self.current_area_name)

    def go_to_underground_path(self, from_area=None):
        self.enter_area("UNDERGROUND PATH", previous=from_area or self.current_area_name)

    def go_to_route6(self, from_area=None):
        self.enter_area("ROUTE 6", previous=from_area or self.current_area_name)

    def go_to_vermilion(self, from_area=None):
        self.enter_area("VERMILION CITY", previous=from_area or self.current_area_name)








    def go_to_prev_area(self):
        """Universal back button - always returns to the area we came from.
           Works perfectly with the new enter_area + previous_area system."""
        if hasattr(self, 'previous_area') and self.previous_area and self.previous_area in self.areas:
            prev = self.previous_area
            self.enter_area(prev)                    # this sets everything correctly
            self.show_text(f"Back in {prev.replace('_', ' ').title()}!")
        else:
            self.show_text("Nowhere to go back to yet!")

    def exit_building(self):
        """Fixed: buildings inside cities always return to the city view"""
        # Inside any building (gym, center, mart, lab, etc.)
        if self.current_screen not in ("city", "route", "forest"):
            self.current_screen = "city"
            area = self.areas[self.current_area_name]
            if "city" in area.backgrounds:
                area.current_bg_key = "city"
            self.show_text(f"Back in {self.current_area_name.replace('_', ' ')} City.")
            return

        # From route/forest → go to the city we came from
        if hasattr(self, 'previous_area') and self.previous_area and self.previous_area in self.areas:
            self.current_area_name = self.previous_area
            self.current_screen = self.area_types.get(self.previous_area, "city")
            self.show_text(f"Back in {self.current_area_name.replace('_', ' ')}...")
        else:
            self.show_text("Nowhere to return to yet.")

    def show_text(self, text: str):
        self.text = text
        self.text_done = False
        self.char_idx = 0
        self.text_timer = 0


    # [REF-0008d] Menu System
    def show_menu(self, title: str, options: list):
        self.menu_active = True
        self.menu_title = title
        self.menu_options = options
        self.menu_rects = []
        self.text = ""  # clear scrolling text while menu is open

    def hide_menu(self):
        self.menu_active = False
        self.menu_options = []
        self.menu_rects = []

    def heal_party(self):
        """Used by Pokémon Centers — heals everything"""
        if hasattr(self, 'player_party') and self.player_party and self.player_party.pokemon:
            for mon in self.player_party.pokemon:
                mon.heal(mon.max_hp)
                mon.status = None
            self.show_text("All your Pokémon were healed at the Pokémon Center!")
        else:
            self.show_text("No Pokémon in party yet!")
        self.hide_menu()

    def show_location_menu(self):
        area = self.areas.get(self.current_area_name)
        if not area:
            self.show_text("Area not found!")
            return

        # === INSIDE A BUILDING? ===
        if self.current_screen not in ("city", "route", "forest"):
            if self.current_screen == "center":
                self.show_menu("Pokémon Center", [
                    ("Heal all Pokémon", self.heal_party),
                    ("Use PC", lambda: self.show_text("PC storage coming soon!")),
                    ("Exit building", self.exit_building)
                ])
            elif self.current_screen == "mart":
                self.show_menu("Poké Mart", [
                    ("Talk to clerk (shop coming soon)", lambda: self.show_text("Poké Mart shop WIP!")),
                    ("Exit building", self.exit_building)
                ])
            else:
                self.show_menu(f"Inside {self.current_area_name}", [("Exit building", self.exit_building)])
            return

        # Fallback (only for brand-new areas you haven't added custom options for yet)
        opts = []
        for b in area.buildings.values():
            opts.append((b.name, lambda b=b: b.interact(self)))

        if self.previous_area and self.previous_area != self.current_area_name:
            prev_name = self.previous_area.replace('_', ' ').title()
            opts.append((f"Return to {prev_name}", self.go_to_prev_area))

        next_name = self.get_next_area_display_name()
        opts.append((f"Go to {next_name}", self.go_to_next_area))

        self.show_menu("Where to?", opts)

    # [REF-0008e] Drawing
    def draw(self, screen):
        screen.fill(BLACK)
        
        # Persistent Rulebook Save Icon
        icon_y = 18 + int(math.sin(pygame.time.get_ticks() / 180) * 2)
        screen.blit(self.save_icon, (24, icon_y))
        if self.save_flash_timer > 0:
            flash = pygame.Surface(SAVE_ICON_SIZE, pygame.SRCALPHA)
            flash.fill((255, 255, 255, 90))
            screen.blit(flash, (24, icon_y))
            self.save_flash_timer -= 1

        # Background
        area = self.areas.get(self.current_area_name)
        if area:
            bg = load_bg(area.get_background_filename(), "pngs/overworld")
            if bg:
                bg = pygame.transform.scale(bg, (WIDTH, HEIGHT - 200))
                screen.blit(bg, (0, 0))
            else:
                pygame.draw.rect(screen, DARK_GREEN, (0, 0, WIDTH, HEIGHT - 200))

        # Big overlays (Bag / Party / Pokédex)
        if self.show_overlay:
            self.draw_overlay(screen)

        # Bottom 200px UI
        self.draw_bottom_ui(screen)

        if self.debug_mode:
            debug_info = f"AREA: {self.current_area_name}  |  MODE: {self.ow_ui_mode}  |  Overlay: {self.show_overlay}"
            draw_text(screen, debug_info, FONT_SMALL, YELLOW, 20, 20, center=False)
    
    # ====================== REPLACE draw_bottom_ui with this segmented version ======================
    def draw_bottom_ui(self, screen):
        """200px bottom UI - fonts match BattleEngine exactly, split layout, depth shading"""
        # Full black bar + white border (identical to battle UI)
        pygame.draw.rect(screen, BLACK, (0, BOTTOM_UI_Y, WIDTH, 200))
        pygame.draw.rect(screen, WHITE, (0, BOTTOM_UI_Y, WIDTH, 200), 4)

        # Vertical black divider
        divider_x = WIDTH - 305
        pygame.draw.line(screen, BLACK, (divider_x, BOTTOM_UI_Y + 8), (divider_x, BOTTOM_UI_Y + 192), 6)

        # ===================== LEFT SEGMENT (text/menu) =====================
        left_w = divider_x - 30
        draw_classic_panel(screen, 20, BOTTOM_UI_Y + 20, left_w, 160)

        if self.ow_ui_mode == "ACTION":
            if self.menu_active and self.menu_options:
                # Title - FONT_UI (same as battle)
                title = self.menu_title or f"What will you do in {self.current_area_name.replace('_', ' ').title()}?"
                draw_text(screen, title, FONT_UI, GB_TEXT, 20 + left_w//2, BOTTOM_UI_Y + 38, center=True)

                # Options - FONT_UI (unified font)
                self.menu_rects = []
                option_y = BOTTOM_UI_Y + 82
                for i, (text, _) in enumerate(self.menu_options):
                    rect = pygame.Rect(40, option_y, left_w - 60, 34)
                    color = HOVER_LIGHT if i == self.selected_option else GB_PANEL
                    pygame.draw.rect(screen, color, rect, border_radius=6)
                    pygame.draw.rect(screen, GB_BORDER, rect, 3, border_radius=6)
                    draw_text(screen, text, FONT_UI, GB_TEXT, rect.centerx, rect.centery)
                    self.menu_rects.append((rect, i))
                    option_y += 38
                
                if self.menu_style == "GRID":
                    # 2x2 Grid for Routes
                    btn_w = (left_w - 60) // 2
                    btn_h = 50
                    start_x = 40
                    start_y = BOTTOM_UI_Y + 65
                    
                    for i, (text, _) in enumerate(self.menu_options):
                        if not text: continue
                        
                        col = i % 2
                        row = i // 2
                        rect = pygame.Rect(start_x + col * (btn_w + 20), 
                                           start_y + row * (btn_h + 10), 
                                           btn_w, btn_h)
                        
                        color = HOVER_LIGHT if i == self.selected_option else GB_PANEL
                        pygame.draw.rect(screen, color, rect, border_radius=6)
                        pygame.draw.rect(screen, GB_BORDER, rect, 3, border_radius=6)
                        draw_text(screen, text, FONT_UI, GB_TEXT, rect.centerx, rect.centery)
                        self.menu_rects.append((rect, i))
                else:
                    # Standard List
                    option_y = BOTTOM_UI_Y + 82
                    for i, (text, _) in enumerate(self.menu_options):
                        rect = pygame.Rect(40, option_y, left_w - 60, 34)
                        color = HOVER_LIGHT if i == self.selected_option else GB_PANEL
                        pygame.draw.rect(screen, color, rect, border_radius=6)
                        pygame.draw.rect(screen, GB_BORDER, rect, 3, border_radius=6)
                        draw_text(screen, text, FONT_UI, GB_TEXT, rect.centerx, rect.centery)
                        self.menu_rects.append((rect, i))
                        option_y += 38
            else:
                # Welcome text - FONT_MSG, perfectly centered
                text_to_show = self.current_text or f"Welcome to {self.current_area_name.replace('_', ' ').title()}!"
                draw_multiline_text(screen, text_to_show, FONT_MSG, GB_TEXT,
                                  20 + left_w//2, BOTTOM_UI_Y + 88,
                                  left_w - 60, line_height=36)

        # ===================== RIGHT SEGMENT (4 buttons with depth) =====================
        right_x = divider_x + 12
        right_w = WIDTH - right_x - 15
        draw_classic_panel(screen, right_x, BOTTOM_UI_Y + 20, right_w, 160)

        buttons = ["Action", "Bag", "Pokémon", "Pokédex"]
        self.bottom_button_rects = []
        for i in range(4):
            col = i % 2
            row = i // 2
            bx = right_x + 14 + col * 132
            by = BOTTOM_UI_Y + 34 + row * 56
            btn_rect = pygame.Rect(bx, by, 116, 46)
            self.bottom_button_rects.append(btn_rect)

            # Depth + highlight (exact BattleEngine button style)
            color = HOVER_LIGHT if i == self.active_bottom_button else GB_PANEL
            thick = 6 if i == self.active_bottom_button else 3
            pygame.draw.rect(screen, color, btn_rect, border_radius=8)
            pygame.draw.rect(screen, GB_BORDER, btn_rect, thick, border_radius=8)
            pygame.draw.rect(screen, GB_HIGHLIGHT, (btn_rect.x + 5, btn_rect.y + 5, btn_rect.w - 10, 3))  # shine line

            # FONT_UI to match BattleEngine buttons exactly
            draw_text(screen, buttons[i], FONT_UI, GB_TEXT, btn_rect.centerx, btn_rect.centery)

    def refresh_menu_options(self):
        """Routes get Walk Grass / Search Trainers / Go Back"""
        area = self.areas.get(self.current_area_name)
        if not area:
            return

        area_type = self.area_types.get(area.name, "city")

        if area_type != "city" and area.name in self.area_pools:
            self.menu_style = "GRID"
            
            def open_explore():
                self.menu_style = "LIST"
                self.menu_title = "Explore Area"
                self.menu_options = [
                    ("Walk through Grass", self.route_events.walk_grass),
                    ("Search for Trainers", self.route_events.search_trainers),
                    ("Cancel", self.refresh_menu_options)
                ]
                self.selected_option = -1

            special = self.route_events.get_special_event(area.name)
            special_btn = special if special else ("", lambda: None)

            self.menu_options = [
                ("Walk through Grass", self.route_events.walk_grass),
                ("Search for Trainers", self.route_events.search_trainers),
                ("Go Back", self.go_to_prev_area),
                ("Go Forward", self.go_to_next_area),
                ("Explore", open_explore),
                ("Go Back", self.go_to_prev_area),
                special_btn
            ]
            special = self.route_events.get_special_event(area.name)
            if special:
                self.menu_options.append(special)
            self.menu_title = f"What will you do on {area.name.replace('_', ' ').title()}?"

# ====================== [REF-0030]: draw_overlay ======================
    def draw_overlay(self, screen):
        """Draws pop-up overlays: BAG, PARTY, POKEDEX"""
        if self.show_overlay is None:
            return

        # Dark background overlay
        overlay_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay_surf.fill((0, 0, 0, 160))
        screen.blit(overlay_surf, (0, 0))

        # Main content panel
        panel_x = 80
        panel_y = 80
        panel_w = WIDTH - 160
        panel_h = HEIGHT - 160
        draw_classic_panel(screen, panel_x, panel_y, panel_w, panel_h, title=self.show_overlay.upper())

        center_x = panel_x + panel_w // 2
        center_y = panel_y + panel_h // 2

        if self.show_overlay == "BAG":
            # Your working bag code goes here
            draw_text(screen, "BAG", FONT_UI, GOLD, center_x, panel_y + 60, center=True)
            draw_text(screen, "BAG WORKS!", FONT_BIG, GREEN, center_x, center_y, center=True)
            # ... rest of your bag drawing ...

        elif self.show_overlay == "PARTY":
            # Clean party display – no "YOUR POKÉMON" title
            if not self.player_party or not self.player_party.pokemon:
                draw_text(screen, "No Pokémon in party yet!", FONT_UI, RED, center_x, center_y, center=True)
            else:
                y = panel_y + 40
                self.party_click_rects = []  # for mouse clicks

                for i, mon in enumerate(self.player_party.pokemon[:6]):
                    row_y = y + i * 100

                    # Sprite (left side)
                    if hasattr(mon, 'front_sprite') and mon.front_sprite:
                        sprite = pygame.transform.scale(mon.front_sprite, (96, 96))
                        screen.blit(sprite, (panel_x + 40, row_y + 10))

                    # Name + Level
                    draw_text(screen, f"{mon.name}", FONT_UI, WHITE, panel_x + 160, row_y + 20)
                    draw_text(screen, f"Lv.{mon.level}", FONT_UI, GOLD, panel_x + 160, row_y + 50)

                    # HP bar + numbers
                    hp_ratio = mon.hp / mon.max_hp if mon.max_hp > 0 else 0
                    bar_w = int(240 * hp_ratio)
                    bar_color = HP_GREEN if hp_ratio > 0.5 else HP_YELLOW if hp_ratio > 0.25 else HP_RED
                    pygame.draw.rect(screen, bar_color, (panel_x + 400, row_y + 30, bar_w, 20))
                    pygame.draw.rect(screen, GB_BORDER, (panel_x + 400, row_y + 30, 240, 20), 3)
                    draw_text(screen, f"{int(mon.hp)} / {int(mon.max_hp)}", FONT_SMALL, WHITE, panel_x + 700, row_y + 35)

                    # Clickable area for submenu/summary
                    click_rect = pygame.Rect(panel_x + 20, row_y, panel_w - 40, 90)
                    if click_rect.collidepoint(pygame.mouse.get_pos()):
                        pygame.draw.rect(screen, HOVER_LIGHT, click_rect, 4, border_radius=8)
                    self.party_click_rects.append((click_rect, i))

            # Hint text
            draw_text(screen, "Click a Pokémon for details • ESC to close", FONT_SMALL, GRAY,
                    center_x, panel_y + panel_h - 40, center=True)

        elif self.show_overlay == "POKEDEX":
            draw_text(screen, "Pokédex (coming soon)", FONT_UI, GOLD, center_x, center_y, center=True)

        # Debug label (top-left corner)
        draw_text(screen, f"Overlay: {self.show_overlay}", FONT_SMALL, (200, 200, 255), 20, 20)
            
    # [REF-0008f] Input Handling
    def handle_bottom_click(self, pos):
        """Second click on ANY button (Action, Bag, Pokémon, or Pokédex) closes it"""
        for i, rect in enumerate(self.bottom_button_rects):
            if rect.collidepoint(pos):
                self.active_bottom_button = i
                
                if i == 0:  # ACTION
                    if self.menu_active:
                        self.menu_active = False
                        self.show_overlay = None
                    else:
                        self.ow_ui_mode = "ACTION"
                        self.show_overlay = None
                        self.menu_active = True
                        self.refresh_menu_options()
                else:  # BAG / POKÉMON / POKEDEX
                    modes = ["BAG", "PARTY", "POKEDEX"]
                    target = modes[i-1]
                    if self.show_overlay == target:
                        self.show_overlay = None
                        self.ow_ui_mode = "ACTION"
                        self.menu_active = True
                        self.refresh_menu_options()
                    else:
                        self.show_overlay = target
                        self.ow_ui_mode = target
                        self.menu_active = False
                return True
        return False

    def handle_click(self, mx, my):
        pos = (mx, my)

        # Save icon
        if self.save_rect.collidepoint(pos):
            self.save_game()
            self.show_text("Game Saved!")
            self.save_flash_timer = 35
            return

        # Bottom buttons – check ALL 4 if list is ready
        if hasattr(self, 'bottom_button_rects') and len(self.bottom_button_rects) >= 4:
            # Action (0), Bag (1), Pokémon (2), Pokédex (3)
            for i, rect in enumerate(self.bottom_button_rects):
                if rect.collidepoint(pos):
                    targets = ["ACTION", "BAG", "PARTY", "POKEDEX"]
                    target = targets[i]
                    
                    if self.show_overlay == target or (target == "ACTION" and self.ow_ui_mode == "ACTION"):
                        # Toggle close
                        self.show_overlay = None
                        self.ow_ui_mode = "NORMAL" if target == "ACTION" else self.ow_ui_mode
                        self.menu_active = False
                    else:
                        # Open
                        if target == "ACTION":
                            self.ow_ui_mode = "ACTION"
                            self.menu_active = True
                            self.refresh_menu_options()
                        else:
                            self.show_overlay = target
                        self.active_bottom_button = i
                    return

        # Action menu options (when menu is open)
        if self.ow_ui_mode == "ACTION" and self.menu_active:
            for rect, idx in self.menu_rects:
                if rect.collidepoint(pos):
                    if idx < len(self.menu_options):
                        _, action = self.menu_options[idx]
                        action()
                    return
        if self.show_overlay == "PARTY" and hasattr(self, 'party_click_rects'):
            for rect, mon_index in self.party_click_rects:
                if rect.collidepoint(mx, my):
                    # Open submenu or summary for this mon
                    self.selected_party_mon = mon_index
                    self.show_overlay = "PARTY_SUBMENU"  # or trigger summary state
                    return
        # Text box → open location menu
        text_box_rect = pygame.Rect(0, HEIGHT - 200, WIDTH, 200)
        if text_box_rect.collidepoint(pos):
            self.show_location_menu()
            return

        # Exit buildings
        if not self.menu_active and self.current_screen not in ("city", "route", "forest"):
            self.exit_building()

    def handle_mouse_motion(self, mx, my):
        """Handles hover effects for clickable elements."""
        self.selected_option = -1 # Reset
        if self.ow_ui_mode == "ACTION" and self.menu_active:
            for rect, idx in self.menu_rects:
                if rect.collidepoint((mx, my)):
                    self.selected_option = idx
                    return

    def get_next_area_display_name(self):
        """Returns clean name like 'Route 1' or 'Pewter City' for the menu"""
        if self.current_area_index + 1 < len(self.area_order):
            next_key = self.area_order[self.current_area_index + 1]
            return next_key.replace('_', ' ').title()
        return "End of Kanto"
    
    def save_game(self):
        data = {
            "player_name": getattr(self, "player_name", "TRAINER"),
            "char_idx": getattr(self, "selected_char_idx", 0),
            "area": self.current_area_name,
            "screen": self.current_screen,
            "area_index": self.current_area_index,
            "explored": list(self.explored_routes),
            "party": [mon.to_dict() for mon in self.player_party.pokemon] if hasattr(self.player_party, "pokemon") else []
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load_game(self):  # optional - call from splash if you want auto-load later
        try:
            with open(SAVE_FILE) as f:
                data = json.load(f)
            self.current_area_name = data.get("area", "PALLET TOWN")
            self.refresh_menu_options()
            return True
        except:
            return False

    def start_battle(self, enemy_id, is_trainer=False, trainer_name=""):
        engine = BattleEngine(
            self.screen,
            self.clock,
            self.player_party, 
            enemy_id,
            player_bag=self.player_bag,
            is_trainer=is_trainer, 
            trainer_name=trainer_name,
            battle_bg_files=getattr(self, 'battle_bg_files', []),
            use_cache_only=True
        )
        result = engine.run()
        
        if isinstance(result, dict) and "caught" in result and result["caught"]:
            self.player_party.pokemon.append(result["caught"])
            self.show_text(f"Gotcha! {result['caught'].name} was added to your party!")
        
        self.refresh_menu_options()

# [REF-0009] BUILDING SYSTEM
class Building(ABC):
    def __init__(self, name: str, rect: pygame.Rect):
        self.name = name
        self.rect = rect

    @abstractmethod
    def interact(self, overworld):
        """Enter building and instantly show its menu"""
        pass


class PokemonCenter(Building):
    def interact(self, overworld):
        area = overworld.areas[overworld.current_area_name]
        area.current_bg_key = "center"
        overworld.current_screen = "center"
        overworld.show_menu("Pokémon Center", [
            ("Talk to Nurse (heal all Pokémon)", lambda: overworld.heal_party()),
            ("Use PC", lambda: overworld.show_text("PC storage coming soon!")),
            ("Exit building", overworld.exit_building)
        ])


class PokeMart(Building):
    def interact(self, overworld):
        area = overworld.areas[overworld.current_area_name]
        area.current_bg_key = "mart"
        overworld.current_screen = "mart"
        overworld.show_menu("Poké Mart", [
            ("Talk to clerk (shop coming soon)", lambda: overworld.show_text("Poké Mart shop WIP!")),
            ("Exit building", overworld.exit_building)
        ])


class Gym(Building):
    def interact(self, overworld):
        area = overworld.areas[overworld.current_area_name]
        area.current_bg_key = "gym"
        overworld.current_screen = "gym"
        overworld.show_menu(f"{self.name}", [
            ("Exit building", overworld.exit_building)
        ])


class InteriorBuilding(Building):
    def __init__(self, name: str, rect: pygame.Rect, bg_key: str):
        super().__init__(name, rect)
        self.bg_key = bg_key

    def interact(self, overworld):
        area = overworld.areas[overworld.current_area_name]
        area.current_bg_key = self.bg_key
        overworld.current_screen = self.bg_key
        overworld.show_menu(f"Inside {self.name}", [
            ("Exit building", overworld.exit_building)
        ])


class OaksLab(InteriorBuilding):
    def __init__(self, name: str, rect: pygame.Rect):
        super().__init__(name, rect, bg_key="lab")

    def interact(self, overworld):
        area = overworld.areas[overworld.current_area_name]
        area.current_bg_key = "lab"
        overworld.current_screen = "lab"
        overworld.show_menu("Oak's Lab", [
            ("Talk to Professor Oak", lambda: overworld.show_text("Professor Oak is busy right now...")),
        ])


class PewterMuseum(InteriorBuilding):
    def __init__(self, name: str, rect: pygame.Rect):
        super().__init__(name, rect, bg_key="museum")

    def interact(self, overworld):
        area = overworld.areas[overworld.current_area_name]
        area.current_bg_key = "museum"
        overworld.current_screen = "museum"
        overworld.show_menu("Pewter Museum", [
            ("Look at fossils", lambda: overworld.show_text("Amazing ancient Pokémon fossils!")),
            ("Exit building", overworld.exit_building)
        ])
# [REF-0010] AREA SYSTEM
class Area:
    def __init__(self, name: str):
        self.name = name
        self.current_bg_key = "city"
        self.buildings: dict[str, Building] = {}
        self.backgrounds = {
            "city": f"{name.lower()}_city.png",
            "center": f"{name.lower()}_center.png",
            "mart": f"{name.lower()}_mart.png",
        }
        # Linear segment system for long routes
        self.segments = []          
        self.current_segment = 0

    def add_building(self, building: Building):
        """Fixed - this was accidentally removed in the last refactor"""
        self.buildings[building.name] = building

    def add_segment(self, key: str, filename: str):
        self.segments.append(key)
        self.backgrounds[key] = filename

    def go_to_next_segment(self):
        if self.current_segment < len(self.segments) - 1:
            self.current_segment += 1
            self.current_bg_key = self.segments[self.current_segment]
            return True
        return False

    def go_to_prev_segment(self):
        if self.current_segment > 0:
            self.current_segment -= 1
            self.current_bg_key = self.segments[self.current_segment]
            return True
        return False

    def set_background(self, key: str, filename: str):
        self.backgrounds[key] = filename

    def get_background_filename(self):
        return self.backgrounds.get(self.current_bg_key, f"{self.name.lower()}_{self.current_bg_key}.png")

# [REF-0011] UI PANELS & BARS
def draw_classic_panel(screen, x, y, w, h, title=None):
    pygame.draw.rect(screen, GB_BORDER, (x - 8, y - 8, w + 16, h + 16))
    pygame.draw.rect(screen, GB_PANEL, (x, y, w, h))
    pygame.draw.rect(screen, GB_PANEL_DARK, (x, y, w, h), 6)
    pygame.draw.rect(screen, GB_HIGHLIGHT, (x + 6, y + 6, w - 12, 3))
    if title:
        draw_text(screen, title, FONT_UI, GB_TEXT, x + w // 2, y + 22)

def draw_hp_bar(screen, x, y, current_hp, max_hp, name, level, current_xp=None, max_xp=None, status=None):
    points = [(x, y), (x + 350, y), (x + 320, y + 80), (x - 30, y + 80)]
    pygame.draw.polygon(screen, (60, 60, 60), points)
    pygame.draw.polygon(screen, WHITE, points, 3)
    draw_text(screen, name[:12] + "…" if len(name) > 12 else name, FONT_UI, WHITE, x + 20, y + 25, center=False)
    draw_text(screen, f"Lv. {level}", FONT_UI, WHITE, x + 240, y + 25, center=False)

    if current_xp is not None and max_xp is not None:
        xp_pct = min(1, current_xp / max_xp)
        pygame.draw.rect(screen, BLUE, (x + 20, y + 55, 250 * xp_pct, 6))

    hp_bar_y = y + 63
    pygame.draw.rect(screen, BLACK, (x + 20, hp_bar_y, 250, 12))
    hp_pct = max(0, current_hp / max_hp)
    bar_col = HP_GREEN if hp_pct > 0.5 else HP_YELLOW if hp_pct > 0.2 else HP_RED
    pygame.draw.rect(screen, bar_col, (x + 20, hp_bar_y, 250 * hp_pct, 12))

    if status and status.get("condition"):
        cond = status["condition"]
        cols = {"BRN": RED, "PSN": PURPLE, "PAR": YELLOW, "SLP": GRAY, "FRZ": CYAN, "CONF": (255, 165, 0), "TOX": PURPLE}
        col = cols.get(cond, BLACK)
        pygame.draw.rect(screen, col, (x - 25, y + 55, 40, 20), border_radius=5)
        pygame.draw.rect(screen, WHITE, (x - 25, y + 55, 40, 20), 2, border_radius=5)
        draw_text(screen, cond, pygame.font.SysFont("arial", 14, bold=True), WHITE, x - 5, y + 65)

    elif hasattr(status.get('mon', None), 'is_confused') and status.get('mon').is_confused():
        col = (255, 165, 0)
        pygame.draw.rect(screen, col, (x - 25, y + 55, 40, 20), border_radius=5)
        pygame.draw.rect(screen, WHITE, (x - 25, y + 55, 40, 20), 2, border_radius=5)
        draw_text(screen, "CONF", pygame.font.SysFont("arial", 14, bold=True), WHITE, x - 5, y + 65)

    if current_xp is not None and max_xp is not None:
        xp_pct = min(1, current_xp / max_xp)
        pygame.draw.rect(screen, BLUE, (x + 20, y + 55, 250 * xp_pct, 6))

    hp_bar_y = y + 63
    pygame.draw.rect(screen, BLACK, (x + 20, hp_bar_y, 250, 12))
    hp_pct = max(0, current_hp / max_hp)
    bar_col = HP_GREEN if hp_pct > 0.5 else HP_YELLOW if hp_pct > 0.2 else HP_RED
    pygame.draw.rect(screen, bar_col, (x + 20, hp_bar_y, 250 * hp_pct, 12))

def smooth_hp(current, target, speed=2):
    if abs(current - target) <= speed:
        return target
    return current + speed if current < target else current - speed

# [REF-0012] MENU DRAWERS (Bag & Party) - FIXED
def draw_bag_menu(screen, bag_pocket, bag_cursor, player_bag_obj, trainer_name):
    """Battle Bag menu - fully fixed indentation, missing loop added, cursor highlight."""
    draw_classic_panel(screen, 20, 80, 300, 520, "BAG")

    # Left side: Pocket tabs
    for i, pocket in enumerate(POCKET_NAMES):
        col = GB_TEXT if i == bag_pocket else GRAY
        draw_text(screen, pocket, FONT_UI, col, 60, 140 + i * 80, center=False)

    # Right side: Items in selected pocket
    pocket_key = ["items", "pokeballs", "key_items"][bag_pocket]
    items = player_bag_obj.get_items_in_pocket(pocket_key)

    panel_x = 340
    panel_y = 130 + bag_pocket * 80
    panel_w = 400
    panel_h = max(100, len(items) * 45 + 40)

    draw_classic_panel(screen, panel_x, panel_y, panel_w, panel_h)

    # === FIXED: Proper loop over items (this was the indentation error) ===
    for i, item in enumerate(items):
        y = panel_y + 30 + i * 45
        text = f"{item.get('name', 'UNKNOWN')}  x{item.get('qty', 0)}"

        # Highlight selected item (cursor support)
        if i == bag_cursor:
            pygame.draw.rect(screen, HOVER_LIGHT, (panel_x + 20, y - 5, panel_w - 40, 38))

        draw_text(screen, text, FONT_UI, GB_TEXT, panel_x + 30, y, center=False)

    # Back button
    draw_classic_panel(screen, WIDTH//2 - 100, HEIGHT - 90, 200, 60)
    draw_text(screen, "BACK", FONT_UI, GB_TEXT, WIDTH//2, HEIGHT - 65)

def draw_party_menu(screen, player_party, party_cursor):
    draw_classic_panel(screen, 40, 60, 940, 580, "POKéMON")
    name_rects = []
    for i in range(6):
        y = 130 + i * 70
        slot = player_party[i] if i < len(player_party) else None
        if slot:
            # Small sprite next to name - Use FRONT sprite for party menu
            if hasattr(slot, 'front_sprite') and slot.front_sprite:
                small_sprite = pygame.transform.scale(slot.front_sprite, (48, 48))
                screen.blit(small_sprite, (72, y - 12))
            elif slot.sprite:
                small_sprite = pygame.transform.scale(slot.sprite, (48, 48))
                screen.blit(small_sprite, (72, y - 12))
            # Name + Level
            name_text = f"{slot.name}  Lv.{slot.level}"
            name_rect = draw_text(screen, name_text, FONT_SMALL, GB_TEXT, 135, y, center=False)
            name_rects.append((name_rect, i))

            # HP Bar
            bar_x = 410
            pygame.draw.rect(screen, BLACK, (bar_x, y + 8, 220, 14))
            pct = max(0, slot.hp / slot.max_hp)
            col = HP_GREEN if pct > 0.5 else HP_YELLOW if pct > 0.2 else HP_RED
            pygame.draw.rect(screen, col, (bar_x, y + 8, 220 * pct, 14))

            # HP numbers
            draw_text(screen, f"{int(slot.hp)}/{int(slot.max_hp)}", FONT_SMALL, GB_TEXT, bar_x + 235, y + 6, center=False)
        else:
            draw_text(screen, "────────────", FONT_SMALL, GRAY, 135, y, center=False)
    
    return name_rects

def draw_party_submenu(screen, submenu_cursor, submenu_mon, player_party):
    mon = player_party[submenu_mon]
    x = 520
    y = 140 + submenu_mon * 70
    draw_classic_panel(screen, x, y, 380, 260)
    
    # FRONT sprite in sub-menu (left side)
    if hasattr(mon, 'front_sprite') and mon.front_sprite:
        screen.blit(mon.front_sprite, (x + 20, y + 30))
    
    # Options on the right
    options = ["SUMMARY", "SWITCH", "ITEM", "CANCEL"]
    for i, opt in enumerate(options):
        col = GB_TEXT if i == submenu_cursor else GRAY
        draw_text(screen, opt, FONT_UI, col, x + 140, y + 30 + i * 55, center=False)

# [REF-0013] BATTLE MECHANICS
class BattleMechanics:
    """Encapsulates damage calculation, stats, type chart, and catch logic."""
    def __init__(self):
        self.stage_multipliers = [2/8, 2/7, 2/6, 2/5, 2/4, 2/3, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
        self.type_chart = {
            "NORMAL": {"ROCK": 0.5, "GHOST": 0, "STEEL": 0.5},
            "FIRE": {"FIRE": 0.5, "WATER": 0.5, "GRASS": 2.0, "ICE": 2.0, "BUG": 2.0, "ROCK": 0.5, "DRAGON": 0.5, "STEEL": 2.0},
            "WATER": {"FIRE": 2.0, "WATER": 0.5, "GRASS": 0.5, "GROUND": 2.0, "ROCK": 2.0, "DRAGON": 0.5},
            "ELECTRIC": {"WATER": 2.0, "ELECTRIC": 0.5, "GRASS": 0.5, "GROUND": 0, "FLYING": 2.0, "DRAGON": 0.5},
            "GRASS": {"FIRE": 0.5, "WATER": 2.0, "GRASS": 0.5, "POISON": 0.5, "GROUND": 2.0, "FLYING": 0.5, "BUG": 0.5, "ROCK": 2.0, "DRAGON": 0.5, "STEEL": 0.5},
            "ICE": {"FIRE": 0.5, "WATER": 0.5, "GRASS": 2.0, "ICE": 0.5, "GROUND": 2.0, "FLYING": 2.0, "DRAGON": 2.0, "STEEL": 0.5},
            "FIGHTING": {"NORMAL": 2.0, "ICE": 2.0, "POISON": 0.5, "FLYING": 0.5, "PSYCHIC": 0.5, "BUG": 0.5, "ROCK": 2.0, "GHOST": 0, "DARK": 2.0, "STEEL": 2.0, "FAIRY": 0.5},
            "POISON": {"GRASS": 2.0, "POISON": 0.5, "GROUND": 0.5, "ROCK": 0.5, "GHOST": 0.5, "STEEL": 0, "FAIRY": 2.0},
            "GROUND": {"FIRE": 2.0, "ELECTRIC": 2.0, "GRASS": 0.5, "POISON": 2.0, "FLYING": 0, "BUG": 0.5, "ROCK": 2.0, "STEEL": 2.0},
            "FLYING": {"ELECTRIC": 0.5, "GRASS": 2.0, "FIGHTING": 2.0, "BUG": 2.0, "ROCK": 0.5, "STEEL": 0.5},
            "PSYCHIC": {"FIGHTING": 2.0, "POISON": 2.0, "PSYCHIC": 0.5, "DARK": 0, "STEEL": 0.5},
            "BUG": {"FIRE": 0.5, "GRASS": 2.0, "FIGHTING": 0.5, "POISON": 0.5, "FLYING": 0.5, "PSYCHIC": 2.0, "GHOST": 0.5, "DARK": 2.0, "STEEL": 0.5, "FAIRY": 0.5},
            "ROCK": {"FIRE": 2.0, "ICE": 2.0, "FIGHTING": 0.5, "GROUND": 0.5, "FLYING": 2.0, "BUG": 2.0, "STEEL": 0.5},
            "GHOST": {"NORMAL": 0, "PSYCHIC": 2.0, "GHOST": 2.0, "DARK": 0.5},
            "DRAGON": {"DRAGON": 2.0, "STEEL": 0.5, "FAIRY": 0},
            "STEEL": {"FIRE": 0.5, "WATER": 0.5, "ELECTRIC": 0.5, "ICE": 2.0, "ROCK": 2.0, "STEEL": 0.5, "FAIRY": 2.0},
            "DARK": {"FIGHTING": 0.5, "PSYCHIC": 2.0, "GHOST": 2.0, "DARK": 0.5, "FAIRY": 0.5},
            "FAIRY": {"FIRE": 0.5, "FIGHTING": 2.0, "POISON": 0.5, "DRAGON": 2.0, "DARK": 2.0, "STEEL": 0.5}
        }

    # [REF-0013a] Stat Calculations
    def calc_hp(self, base_hp: int, level: int) -> int:
        return ((2 * base_hp + 31) * level // 100) + level + 10

    def calc_stat(self, base: int, level: int) -> int:
        return ((2 * base + 31) * level // 100) + 5

    def get_type_multiplier(self, move_type: str, target_types: list) -> float:
        mult = 1.0
        for t in target_types:
            mult *= self.type_chart.get(move_type, {}).get(t, 1.0)
        return mult

    # [REF-0013b] Damage Formula
    def calculate_damage(self, attacker, defender, move, math_boost=1.0):
        is_crit = random.random() < (1 / 24)
        crit_mult = 1.5 if is_crit else 1.0

        atk_stat_name = "ATTACK" if move.category == "physical" else "SPATK"
        atk = attacker.get_stat(atk_stat_name) * self.stage_multipliers[attacker.stage_manager.get_stage(
            "attack" if move.category == "physical" else "sp_atk") + 6]

        def_stat_name = "DEFENSE" if move.category == "physical" else "SPDEF"
        dfn = defender.get_stat(def_stat_name) * self.stage_multipliers[defender.stage_manager.get_stage(
            "defense" if move.category == "physical" else "sp_def") + 6]

        level_calc = (2 * attacker.level / 5) + 2
        base_damage = ((level_calc * move.power * (atk / dfn)) / 50) + 2

        stab = 1.5 if move.type in attacker.types else 1.0
        type_mult = self.get_type_multiplier(move.type, defender.types)
        variance = random.uniform(0.85, 1.0)
        burn_penalty = 0.5 if (attacker.status == "BRN" and move.category == "physical") else 1.0

        final = int(base_damage * stab * type_mult * crit_mult * variance * burn_penalty * math_boost)
        return max(1, final) if type_mult > 0 else 0, is_crit

    # [REF-0013c] Catch Formula
    def catch_attempt(self, max_hp: int, current_hp: int, base_rate: int, ball: str) -> tuple[bool, int]:
        ball = ball.lower().replace(" ", "").replace("é", "e")
        if ball == "masterball": return True, 4
        mult_table = {"pokeball": 4096, "greatball": 6144, "ultraball": 8192}
        mult = mult_table.get(ball, 4096)
        if max_hp <= 0 or current_hp <= 0: return False, 0
        hp_factor = ((3 * max_hp - 2 * current_hp) * 4096) // (3 * max_hp)
        modified = (hp_factor * base_rate * mult) // 4096
        if modified >= 1_044_480: return True, 4
        b = (modified * 65_536) // 1_044_480
        shakes = 0
        for _ in range(4):
            if random.randint(0, 65_535) < b: shakes += 1
            else: return False, shakes
        return True, 4

    def attempt_flee(self, player_speed: int, wild_speed: int, attempts: int = 1) -> bool:
        if player_speed >= wild_speed: return True
        base = (player_speed * 128) // wild_speed
        odds = base + (30 * attempts)
        return random.randrange(256) < odds

# [REF-0014] STAGE & SESSION
class StageManager:
    def __init__(self):
        self.stages = {"attack": 0, "defense": 0, "sp_atk": 0, "sp_def": 0, "speed": 0, "accuracy": 0, "evasion": 0}

    def change_stage(self, stat, amount):
        old_val = self.stages[stat]
        self.stages[stat] = max(-6, min(6, self.stages[stat] + amount))
        return self.stages[stat] != old_val

    def get_stage(self, stat):
        return self.stages.get(stat, 0)

class BattleSession:
    def __init__(self, player_team_stages):
        self.consecutive_correct = 0
        self.team_stages = player_team_stages 

    def register_answer(self, is_correct):
        if is_correct:
            self.consecutive_correct += 1
            if self.consecutive_correct >= 5:
                stat = random.choice(["attack", "defense", "sp_atk", "sp_def", "speed"])
                self.team_stages.change_stage(stat, 1)
                return f"STREAK {self.consecutive_correct}! Team {stat.upper()} rose!"
        else:
            self.consecutive_correct = 0
            return "Streak broken!"
        return None

# [REF-0015] DATA MANAGER
class DataManager:
    def __init__(self):
        self.POKEMON_CACHE = {}
        self.BALL_CACHE = {}
        self.movesets = self._load_movesets()

    def preload_ui(self):
        self.ui_assets = {"hp_bar_bg": pygame.Surface((250, 12))}

    def _load_movesets(self):
        path = os.path.join(ASSETS_DIR, "pokemon_movesets.json")
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Could not load pokemon_movesets.json: {e}")
        print("⚠️ pokemon_movesets.json missing! Run DOWNLOAD ASSETS once.")
        return {}

    def _get_sprite_path(self, poke_id: int, back: bool = False, shiny: bool = False):
        base = os.path.join(ASSETS_DIR, "sprites", "pokemon")
        
        shiny_path = None
        normal_path = None

        if back:
            normal_path = os.path.join(base, "back", f"{poke_id}.png")
            if shiny:
                shiny_path = os.path.join(base, "back", "shiny", f"{poke_id}.png")
        else:
            normal_path = os.path.join(base, f"{poke_id}.png")
            if shiny:
                shiny_path = os.path.join(base, "shiny", f"{poke_id}.png")

        if shiny_path and os.path.exists(shiny_path):
            return shiny_path
        return normal_path


    def _load_sprite(self, poke_id: int, back: bool = False, shiny: bool = False):
        path = self._get_sprite_path(poke_id, back, shiny)
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.scale(img, (BATTLE_SCALE, BATTLE_SCALE))
            except:
                pass
        surf = pygame.Surface((BATTLE_SCALE, BATTLE_SCALE))
        surf.fill(GRAY)
        return surf

    def fetch_pokemon_data(self, poke_id: int, back: bool = False, level: int = 50, shiny: bool = False):
        key = (poke_id, back, level, shiny)
        if key in self.POKEMON_CACHE:
            return self.POKEMON_CACHE[key]

        data = self.movesets.get(str(poke_id), {})
        name = data.get("name", f"POKÉ {poke_id}").upper()
        types = data.get("types", ["NORMAL"])
        stats = data.get("stats", {"HP":50,"ATTACK":50,"DEFENSE":50,"SPATK":50,"SPDEF":50,"SPEED":50})
        base_xp = data.get("base_xp", 64)
        capture_rate = data.get("capture_rate", 45)

        moves_list = data.get("moves", [])[:4]
        if len(moves_list) < 4:
            moves_list += [{"name": "TACKLE", "power": 40, "type": "NORMAL",
                            "accuracy": 100, "category": "physical", "secondary": []}] * (4 - len(moves_list))

        image = self._load_sprite(poke_id, back, shiny)
        cry_sound = self.load_cry(poke_id)

        result = (image, name, moves_list, base_xp, types, stats, cry_sound, capture_rate)
        self.POKEMON_CACHE[key] = result
        return result

    def load_cry(self, poke_id):
        path = os.path.join(ASSETS_DIR, "sounds", "cries", f"{poke_id:04d}.ogg")
        if os.path.exists(path):
            try:
                sound = pygame.mixer.Sound(path)
                sound.set_volume(0.5)
                return sound
            except:
                pass
        return None
    def load_item_sprite(self, item_name: str):
        key = item_name.lower().strip()
        if key in self.BALL_CACHE:
            return self.BALL_CACHE[key]

        filename = key.replace("é", "e").replace(" ", "-") + ".png"
        local_path = os.path.join(ASSETS_DIR, "sprites", "items", filename)

        if os.path.exists(local_path):
            try:
                img = pygame.image.load(local_path).convert_alpha()
                surf = pygame.transform.scale(img, (64, 64))
                self.BALL_CACHE[key] = surf
                return surf
            except:
                pass

        if "ball" in key:
            # Classic Poké Ball look
            surf = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.circle(surf, (230, 40, 40), (32, 32), 28)
            pygame.draw.circle(surf, (255, 255, 255), (32, 32), 28, 6)
            pygame.draw.circle(surf, (0, 0, 0), (32, 32), 12)
        else:
            # Generic item fallback (potion-style)
            surf = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.rect(surf, (255, 100, 100), (16, 16, 32, 40), border_radius=8)
            pygame.draw.rect(surf, (255, 255, 255), (16, 16, 32, 40), 4, border_radius=8)
        
        self.BALL_CACHE[key] = surf
        return surf

    def get_random_pokemon_id(self, exclude_id=None, max_id=151):
        while True:
            pid = random.randint(1, max_id)
            if exclude_id is None or pid != exclude_id:
                return pid

# [REF-0016] CORE DATA CLASSES
# [REF-0016a] Move Class
class Move:
    def __init__(self, data_dict):
        self.name = data_dict["name"]
        self.power = data_dict.get("power", 0)
        self.type = data_dict["type"]
        self.accuracy = data_dict.get("accuracy", 100)
        self.category = data_dict.get("category", "physical")
        self.secondary = data_dict.get("secondary", [])
        self.is_inflicter = data_dict.get("is_inflicter", False)
        self.ailment = data_dict.get("ailment")
        self.priority = data_dict.get("priority", 0)
        self.ohko = data_dict.get("ohko", False)
        self.self_faint = data_dict.get("self_faint", False)

    def execute(self, user, target, battle, math_boost=1.0):
        feedback = f"{user.name} used {self.name}!"
        dmg = 0
        is_crit = False

        if self.power == 0 and self.is_inflicter:
            # === STATUS MOVE (Poison Powder, Thunder Wave, etc.) ===
            if self.ailment and self.ailment.upper() != "CONFUSION":
                target.apply_status(self.ailment.upper())
                feedback += f" The foe was {self.ailment.lower()}ed!"
            elif self.ailment == "confusion":
                target.volatile["confusion"] = random.randint(3, 5)
                feedback += " The foe became confused!"
            return feedback, dmg, is_crit, self.secondary

        # === OHKO MOVES (Guillotine, Sheer Cold, etc.) ===
        if self.ohko:
            # Special OHKO accuracy (30% base + level check) — math override still applies
            if random.random() < 0.30 and user.level >= target.level:
                dmg = target.hp  # instant KO
                feedback += " It's a one-hit KO!"
                target.take_damage(dmg)
                return feedback, dmg, False, self.secondary
            else:
                feedback += " But it failed!"
                return feedback, 0, False, []

        # === SELF-DESTRUCT / EXPLOSION ===
        if self.self_faint:
            # Damage first, THEN user faints (even on miss/immunity)
            dmg, is_crit = battle.mechanics.calculate_damage(user, target, self, math_boost)
            target.take_damage(dmg)
            user.hp = 0
            feedback += " It exploded!"
            if is_crit:
                feedback += " A critical hit!"
            return feedback, dmg, is_crit, self.secondary

        # === DAMAGING MOVE ===
        dmg, is_crit = battle.mechanics.calculate_damage(user, target, self, math_boost)
        target.take_damage(dmg)

        eff_mult = battle.mechanics.get_type_multiplier(self.type, target.types)
        if eff_mult == 0.0:
            feedback += " It had no effect!"
            dmg = 0
        elif eff_mult > 1.0:
            feedback += " It's super effective!"
        elif eff_mult < 1.0:
            feedback += " It's not very effective..."
        if is_crit:
            feedback += " A critical hit!"

        return feedback, dmg, is_crit, self.secondary

# [REF-0016b] Pokemon Class
class Pokemon:
    def __init__(self, poke_id, data_manager, mechanics, level=50, back_sprite=True, is_shiny=False):
        self.mechanics = mechanics
        self.is_shiny = is_shiny

        # FULLY OFFLINE LOADING (single call, no duplicates)
        image, name, moves_list, base_xp, types, stats, cry_sound, capture_rate = \
            data_manager.fetch_pokemon_data(poke_id, back=back_sprite, level=level, shiny=self.is_shiny)

        self.id = poke_id
        self.name = name
        self.sprite = image
        self.moves = [Move(m) for m in moves_list]
        self.base_xp = base_xp
        self.types = types
        self.base_stats = stats
        self.cry = cry_sound
        self.capture_rate = capture_rate
        self.level = level

        self.max_hp = mechanics.calc_hp(stats.get("HP", 50), level)
        self.hp = self.max_hp

        self.xp = 0
        self.xp_needed = max(100, int(100 * (1.25 ** (level - 1))) + 30)
        self.status = None
        self.status_counter = 0
        self.volatile = {}
        self.stage_manager = StageManager()

        # Front sprite for party menu
        front_image, *_ = data_manager.fetch_pokemon_data(poke_id, back=False, level=level, shiny=self.is_shiny)
        self.front_sprite = pygame.transform.scale(front_image, (96, 96))

    def get_stat(self, stat_name: str) -> int:
        base = self.base_stats.get(stat_name.upper(), 50)
        if stat_name.upper() == "HP":
            return self.max_hp

        key = stat_name.lower().replace("spatk", "sp_atk").replace("spdef", "sp_def")
        stage = self.stage_manager.get_stage(key)
        mult = self.mechanics.stage_multipliers[stage + 6]
        stat = int(self.mechanics.calc_stat(base, self.level) * mult)

        if stat_name.upper() == "SPEED" and self.status == "PAR":
            stat = int(stat * 0.5)

        return stat

    def take_damage(self, damage):
        self.hp = max(0, self.hp - damage)

    def apply_status(self, condition):
        if not self.status:
            self.status = condition
            if condition == "SLP":
                self.status_counter = random.randint(1, 3)
            else:
                self.status_counter = 0

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def is_fainted(self):
        return self.hp <= 0

# [REF-0016c] Party Class
class Party:
    """Manages player party + active slot"""
    def __init__(self, pokemon_list):
        self.pokemon = pokemon_list
        self.active_idx = 0

    @property
    def active(self):
        return self.pokemon[self.active_idx]

    def switch_to(self, new_idx):
        if self.pokemon[new_idx].is_fainted():
            return False
        self.active_idx = new_idx
        return True

    def switch_next(self):
        for i, p in enumerate(self.pokemon):
            if not p.is_fainted():
                self.active_idx = i
                return True
        return False

    def is_wiped(self):
        return all(p.is_fainted() for p in self.pokemon)

# [REF-0016d] Bag Class
class Bag:
    def __init__(self):
        self.pockets = {
            "items": [{"name": "POTION", "qty": 10}, {"name": "SUPER POTION", "qty": 5},
                      {"name": "FULL HEAL", "qty": 3}, {"name": "REVIVE", "qty": 2}],
            "pokeballs": [{"name": "POKÉ BALL", "qty": 15}, {"name": "GREAT BALL", "qty": 8},
                          {"name": "ULTRA BALL", "qty": 3}, {"name": "MASTER BALL", "qty": 1}],
            "key_items": []
        }

    def _get_pocket_and_item(self, item_name):
        item_name_upper = item_name.upper()
        if "BALL" in item_name_upper:
            pocket_key = "pokeballs"
        elif item_name_upper in ["OLD ROD", "TOWN MAP", "BICYCLE"]:
            pocket_key = "key_items"
        else:
            pocket_key = "items"
        pocket = self.pockets[pocket_key]
        for item in pocket:
            if item["name"].upper() == item_name_upper:
                return pocket, item
        return pocket, None

    def add_item(self, item_name, quantity=1):
        pocket, item = self._get_pocket_and_item(item_name)
        if item:
            item["qty"] += quantity
        else:
            pocket.append({"name": item_name.upper(), "qty": quantity})

    def get_items_in_pocket(self, pocket_key):
        return [item for item in self.pockets.get(pocket_key, []) if item.get("qty", 0) > 0]

    def remove_item(self, item_name, qty=1):
        pocket, item = self._get_pocket_and_item(item_name)
        if item and item["qty"] >= qty:
            item["qty"] -= qty
            return True
        return False

# [REF-0017] TRAINER SYSTEM
class TrainerSystem:
    """Handles opponent trainer state, party, and rendering."""
    def __init__(self, name, sprite_name, party_data, data_manager, mechanics):
        self.name = name
        # Try to load specific trainer sprite, fallback to red_back (placeholder) or color rect
        self.sprite = load_asset(sprite_name, "sprites", (BATTLE_SCALE, BATTLE_SCALE))
        if not self.sprite:
            self.sprite = pygame.Surface((BATTLE_SCALE, BATTLE_SCALE))
            self.sprite.fill((200, 50, 50))
            pygame.draw.rect(self.sprite, BLACK, (0,0,BATTLE_SCALE,BATTLE_SCALE), 5)
        
        # Build party
        pokemon_list = []
        if isinstance(party_data, list):
            for p in party_data:
                if isinstance(p, Pokemon): pokemon_list.append(p)
                elif isinstance(p, dict): pokemon_list.append(Pokemon(p.get("id", 1), data_manager, mechanics, p.get("level", 50), back_sprite=False, is_shiny=p.get("is_shiny", False)))
        elif isinstance(party_data, Pokemon):
            pokemon_list.append(party_data)
            
        self.party = Party(pokemon_list)

    def get_active(self):
        return self.party.active

    def has_next(self):
        return any(not p.is_fainted() for p in self.party.pokemon)

    def switch_next(self):
        for i, p in enumerate(self.party.pokemon):
            if not p.is_fainted():
                self.party.active_idx = i
                return p
        return None

# [REF-0018] SOUND MANAGER
class SoundManager:
    """Handles background music and sound effects."""
    def play_random_music(self, filenames):
        try:
            if not filenames: return
            filename = random.choice(filenames) if isinstance(filenames, list) else filenames
            path = os.path.join(os.path.dirname(__file__), "assets", "sounds", filename)
            if os.path.exists(path):
                pygame.mixer.music.load(path)
                pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Error playing music: {e}")

# [REF-0019] MATH SYSTEM
class MathBrain:
    def generate_problem(self, bp=40, is_ohko=False):
        """bp = move Base Power. Higher BP = harder math."""
        if is_ohko or bp >= 150:
            a, b, c = random.randint(12, 25), random.randint(11, 20), random.randint(50, 150)
            res = (a * b) - c
            question = f"ULTIMATE: ({a} * {b}) - {c} = ?"
            correct_ans = str(res)
            options = {correct_ans}
            while len(options) < 4:
                offset = random.randint(-10, 10)
                if offset != 0 and (res + offset) >= 0:
                    options.add(str(res + offset))
            options_list = list(options)
            random.shuffle(options_list)
            return question, options_list, correct_ans

        # SOLID BP SCALING
        if bp <= 55:
            max_num = 18
            reverse_chance = 0.25
        elif bp <= 85:
            max_num = 28
            reverse_chance = 0.50
        else:
            max_num = 38
            reverse_chance = 0.75

        ops = ["+", "-"]
        op = random.choice(ops)
        a = random.randint(3, max_num)
        b = random.randint(1, a-1) if op == "-" else random.randint(2, max_num)
        res = a + b if op == "+" else a - b

        q_type = random.choice([0, 1, 2])
        if random.random() < reverse_chance:
            q_type = 2

        options = set()
        if q_type == 0:
            question = f"SOLVE: {a} {op} {b} = ?"
            correct_ans = str(res)
            ans_val = res
        elif q_type == 1:
            question = f"WHICH EQUALS: {res}"
            correct_ans = f"{a} {op} {b}"
            options.add(correct_ans)
            while len(options) < 4:
                fake_op = random.choice(ops)
                fake_res = max(5, res + random.randint(-5, 5))  # GUARANTEED safe
                if fake_op == "+":
                    f_a = random.randint(1, fake_res - 1)
                    options.add(f"{f_a} + {fake_res - f_a}")
                else:
                    f_b = random.randint(1, fake_res + 5)
                    options.add(f"{fake_res + f_b} - {f_b}")
            ans_val = -1
        else:
            if op == "+":
                question = f"{a} + ? = {res}" if random.random() < 0.5 else f"? + {b} = {res}"
                correct_ans = str(b if question.startswith(str(a)) else a)
                ans_val = int(correct_ans)
            else:
                question = f"{a} - ? = {res}" if random.random() < 0.5 else f"? - {b} = {res}"
                correct_ans = str(b if question.startswith(str(a)) else a)
                ans_val = int(correct_ans)

        if q_type != 1:
            options.add(correct_ans)
            while len(options) < 4:
                val = ans_val + random.randint(-6, 6)
                if val >= 0:
                    options.add(str(val))

        options_list = list(options)
        random.shuffle(options_list)
        return question, options_list, correct_ans

# [REF-0020] WILD POKEMON POOL
class WildPokemonPool:
    """Manages pools of wild Pokémon for different environments."""
    def __init__(self):
        self.pools = {
            "GRASSLAND": [16, 19, 21, 10, 13, 29, 32, 69, 43], # Pidgey, Rattata, Spearow, Caterpie, Weedle, Nidoran, Bellsprout, Oddish
            "FOREST": [10, 11, 13, 14, 25, 1, 4, 7, 123, 48],   # Bugs, Pikachu, Starters, Scyther, Venonat
            "CAVE": [41, 27, 50, 74, 95, 35, 66],              # Zubat, Sandshrew, Diglett, Geodude, Onix, Clefairy, Machop
            "WATER": [72, 129, 60, 54, 79, 118],                # Tentacool, Magikarp, Poliwag, Psyduck, Slowpoke, Goldeen
            "POWER PLANT": [25, 81, 100, 125, 135],            # Pikachu, Magnemite, Voltorb, Electabuzz, Jolteon
            "MT MOON": [35, 39, 41, 74, 113],                  # Clefairy, Jigglypuff, Zubat, Geodude, Chansey
            "RARE": [147, 148, 149, 143, 131, 115, 150, 151]   # Dratini line, Snorlax, Lapras, Kangaskhan, Mewtwo, Mew
        }
    
    def get_random_id(self, pool_name=None):
        if pool_name == "RANDOM" or pool_name is None:
             all_ids = [pid for pool in self.pools.values() for pid in pool]
             return random.choice(all_ids)
        if pool_name in self.pools:
            return random.choice(self.pools[pool_name])
        return random.randint(1, 151)

    def get_pools(self):
        return ["RANDOM"] + list(self.pools.keys())

# [REF-0021] LEVEL UP SYSTEM
class LevelUpSystem:
    """Handles XP gain, leveling up, and learning moves."""
    def __init__(self, engine):
        self.engine = engine

    def process_win(self):
        active = self.engine.party.active
        enemy = self.engine.enemy
        
        # XP Formula: (Base * Level) / 7
        xp_gain = int((enemy.base_xp * enemy.level) / 7)
        active.xp += xp_gain
        self.engine.feedback_text = f"{active.name} gained {xp_gain} XP!"
        
        next_state = "VICTORY"
        
        if active.xp >= active.xp_needed:
            active.level += 1
            active.xp_needed = int(active.xp_needed * 1.25) + 100
            active.xp = 0
            
            # Recalculate stats & Heal increase
            old_max = active.max_hp
            active.max_hp = self.engine.mechanics.calc_hp(active.base_stats["HP"], active.level)
            active.hp += (active.max_hp - old_max)
            
            self.engine.feedback_text += f"\n{active.name} grew to Lv. {active.level}!"
            
            # Check for new moves
            new_moves = []
            if new_moves:
                self.engine.moves_to_learn = new_moves
                next_state = "LEARN_MOVE"
                
        return next_state

# [REF-0022] ANIMATION CONTROLLER
class AnimationController:
    """Manages visual states like lunging, shaking, and flashing."""
    def __init__(self):
        self.lunge_timer = 0
        self.is_lunging = False
        self.lunge_side = None
        self.impact_flash = 0
        self.impact_shake = 0
        self.pending_damage = 0
        self.pending_target = None

    def start_lunge(self, side):
        self.is_lunging = True
        self.lunge_side = side
        self.lunge_timer = 0

    def update(self):
        if self.is_lunging:
            self.lunge_timer += 1
            if self.lunge_timer >= 16:
                self.is_lunging = False
                self.lunge_timer = 0
        if self.impact_flash > 0: self.impact_flash -= 1
        if self.impact_shake > 0: self.impact_shake -= 1

# [REF-0023] TURN PROCESSOR
class TurnProcessor:
    def __init__(self, engine):
        self.engine = engine

    def update(self):
        if self.engine.message_queue:
            self.engine.message_queue[0] = (self.engine.message_queue[0][0], self.engine.message_queue[0][1] - 1)
            if self.engine.message_queue[0][1] <= 0:
                self.engine.advance_message()
            return "WAIT"

    # [REF-0023a] Main Update
        if not self.engine.turn_queue:
            return "NEXT_TURN"

        act = self.engine.turn_queue.pop(0)
        mon = self.engine.party.active if act["who"] == "player" else self.engine.enemy

        # ===== 2. PRE-TURN STATUS GATEKEEPER =====
        if self._handle_pre_turn_status(mon, act["who"]):
            return "ACTION"

        # ===== EXECUTE MOVE =====
        move = act["move_obj"]
        math_boost = 1.2 if random.random() < 0.7 else 0.8   # example
        feedback, dmg, crit, secondary = move.execute(mon, self.engine.enemy if act["who"]=="player" else self.engine.party.active, self.engine, math_boost)

        self.engine.add_message(feedback)
        self.engine.anim_ctrl.start_lunge(act["who"])

        # ===== 3. POST-MOVE SECONDARY EFFECTS =====
        self._process_secondary(secondary, mon, self.engine.enemy if act["who"]=="player" else self.engine.party.active, act["who"])

        # Immediate faint check and message processing
        if self._check_and_handle_faints():
            return "FAINT"

        while self.engine.message_queue and self.engine.message_queue[0][1] <= 0:
            self.engine.advance_message()

        return "ACTION"

    def _handle_pre_turn_status(self, mon, side):
        # Sleep - now works reliably for BOTH player and wild/enemy
        if mon.status == "SLP":
            mon.status_counter -= 1
            if mon.status_counter <= 0:
                mon.status = None
                self.engine.add_message(f"{mon.name} woke up!")
            else:
                self.engine.add_message(f"{mon.name} is fast asleep.")
                if self.engine.turn_queue:
                    self.engine.turn_queue.pop(0)
                return True

        # Paralysis
        if mon.status == "PAR" and random.random() < 0.25:
            self.engine.add_message(f"{mon.name} is paralyzed! It can't move!")
            return True

        # Confusion
        if "confusion" in mon.volatile:
            mon.volatile["confusion"] -= 1
            self.engine.add_message(f"{mon.name} is confused!")
            if mon.volatile["confusion"] <= 0:
                del mon.volatile["confusion"]
                self.engine.add_message(f"{mon.name} snapped out of confusion!")
            elif random.random() < 0.33:
                self.engine.add_message(f"{mon.name} hurt itself in its confusion!")
                dmg = mon.get_stat("ATTACK") // 4
                mon.take_damage(dmg)
                return True
        return False

    # [REF-0023b] Secondary Effects
    def _process_secondary(self, effects, user, target, side):
        
        for eff in effects:
            if random.random() * 100 > eff.get("chance", 100):
                continue

            etype = eff.get("type", "").lower()

            # 1. Status Conditions
            if etype == "ailment":
                ailment = eff.get("ailment", "").upper()
                if ailment == "CONFUSION":
                    target.volatile.setdefault("confusion", 0)
                    target.volatile["confusion"] = random.randint(3, 5)
                    self.engine.add_message(f"{target.name} became confused!")
                elif ailment and not target.status:
                    target.apply_status(ailment)
                    self.engine.add_message(f"{target.name} was {ailment.lower()}ed!")

            # 2. Flinch
            elif etype == "flinch":
                # Only flinch if the target hasn't acted yet this turn
                if (side == "player" and self.engine.turn_queue and 
                    any(a.get("who") == "enemy" for a in self.engine.turn_queue)):
                    self.engine.turn_queue.clear()
                    self.engine.add_message(f"{target.name} flinched!")
                elif side == "enemy":
                    self.engine.add_message(f"{target.name} flinched!")

            # 3. Recoil (25% of damage dealt)
            elif etype == "recoil":
                recoil_dmg = int(user.hp * 0.25)
                user.take_damage(recoil_dmg)
                self.engine.add_message(f"{user.name} was hurt by recoil!")

            # 4. HP Drain / Healing
            elif etype in ("healing", "drain"):
                # Simple 50% heal of damage dealt
                heal_amount = max(1, int(target.hp * 0.5)) if target.hp > 0 else 1
                user.heal(heal_amount)
                self.engine.add_message(f"{user.name} had its HP restored!")

            # 5. Stat Stage Changes
            elif etype == "stat_change":
                stat = eff.get("stat", "").lower()
                stages = eff.get("stages", 1)
                if target.stage_manager.change_stage(stat, stages):
                    direction = "rose" if stages > 0 else "fell"
                    self.engine.add_message(f"{target.name}'s {stat.upper()} {direction}!")

            # 6. Self-Faint (Self-Destruct, Explosion)
            elif etype == "self_faint" or getattr(user, 'self_faint', False):
                user.hp = 0
                self.engine.add_message(f"{user.name} fainted from the explosion!")

            else:
                print(f"[DEBUG] Unknown secondary effect type: {etype} on {user.name}")

        self._check_and_handle_faints()

    def _check_and_handle_faints(self):
        if self.engine.party.active.is_fainted():
            self.engine.turn_queue.clear()
            self.engine.add_message(f"{self.engine.party.active.name} fainted!")
            self.engine.state_machine.set_state("FAINT_MSG")
            return True
        if self.engine.enemy.is_fainted():
            self.engine.turn_queue.clear()
            self.engine.add_message(f"Enemy {self.engine.enemy.name} fainted!")
            
            if not self.engine.is_trainer:
                self.engine.ko_catch_offered = True
                self.engine.state_machine.set_state("KO_CATCH")
            else:
                next_state = self.engine.level_up_system.process_win()
                self.engine.state_machine.set_state(next_state)
            return True

    # [REF-0023c] Residuals
    def process_residuals(self):
        for mon in [self.engine.party.active, self.engine.enemy]:
            if mon.status in ("BRN", "PSN", "TOX"):
                dmg = max(1, mon.max_hp // 16)
                if mon.status == "TOX":
                    dmg = min(mon.max_hp // 2, dmg * (mon.status_counter + 1))
                    mon.status_counter += 1
                mon.take_damage(dmg)
                if dmg > 0:
                    self.engine.add_message(f"{mon.name} is hurt by its {mon.status}!")
        self._check_and_handle_faints()

# [REF-0024] BATTLE STATES
class BattleState(ABC):
    # [REF-0024a] Base & Loading
    def __init__(self, engine):
        self.engine = engine
    def update(self): pass
    def draw(self, screen): pass
    def handle_event(self, event): pass

class LoadingState(BattleState):
    def update(self):
        self.engine.state_machine.set_state("INTRO")
    def draw(self, screen):
        screen.fill(BLACK)
        draw_text(screen, "LOADING BATTLE...", FONT_MED, WHITE, WIDTH // 2, HEIGHT // 2)

class IntroState(BattleState):
    def update(self):
        self.engine.intro_system.update()
        
        # Rescue mode handoff (this was missing!)
        if getattr(self.engine.intro_system, 'finished', False) or getattr(self.engine, 'rescue_finished', False):
            self.engine.state_machine.set_state("MAIN")
            return
        
        # Normal intro handoff
        if self.engine.intro_system.finished:
            self.engine.q_text, self.engine.options, self.engine.correct_ans = self.engine.math_system.generate_problem(40)
            self.engine.state_machine.set_state("MAIN")
            
    def draw(self, screen):
        screen.fill((20, 20, 40))
        if self.engine.battle_bg:
            screen.blit(self.engine.battle_bg, (0, 0))
        self.engine.intro_system.draw()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN)):
            self.engine.intro_system.advance()

# [REF-0024b] Main Menus
class MainBattleState(BattleState):
    def draw(self, screen):
        self.engine.draw_battle_scene(screen)
        draw_classic_panel(screen, WIDTH - 300, HEIGHT - 180, 280, 160)
        self.engine.main_menu_rects = []
        menu_options = ["FIGHT", "BAG", "POKéMON", "RUN"]
        for i, opt in enumerate(menu_options):
            x = WIDTH - 280 + (i % 2) * 160
            y = HEIGHT - 140 + (i // 2) * 60
            rect = draw_text(screen, opt, FONT_UI, GB_TEXT, x, y, center=False)
            self.engine.main_menu_rects.append(rect)
        draw_classic_panel(screen, 20, HEIGHT - 180, WIDTH - 340, 160)
        draw_multiline_text(screen, "What will your Pokémon do?", FONT_MSG, GB_TEXT, 40, HEIGHT - 100, WIDTH - 380, center=False)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, rect in enumerate(self.engine.main_menu_rects):
                if rect.collidepoint(event.pos):
                    if i == 0: self.engine.state_machine.set_state("MOVES")
                    elif i == 1:
                        self.engine.bag_return_state = 'MAIN'
                        self.engine.state_machine.set_state("BAG")
                    elif i == 2: self.engine.state_machine.set_state("PARTY")
                    elif i == 3:  # RUN
                        self.engine.flee_attempts += 1
                        if self.engine.mechanics.attempt_flee(self.engine.party.active.get_stat("SPEED"), self.engine.enemy.get_stat("SPEED"), self.engine.flee_attempts):
                            self.engine.add_message("Got away safely!")
                            self.engine.fled = True
                            self.engine.state_machine.set_state("TURN")
                        else:
                            self.engine.add_message("Can't escape!")
                            e_act = self.engine.create_act("enemy", self.engine.choose_enemy_move_idx())
                            self.engine.turn_queue = [e_act]
                            self.engine.state_machine.set_state("TURN")

class MovesState(BattleState):
    def draw(self, screen):
        self.engine.draw_battle_scene(screen)
        draw_classic_panel(screen, 20, HEIGHT - 180, WIDTH - 40, 160)
        draw_text(screen, "Select a move:", FONT_MSG, GB_TEXT, WIDTH // 2, HEIGHT - 140)
        self.engine.move_menu_rects = []
        for i, move in enumerate(self.engine.party.active.moves[:4]):
            row, col = divmod(i, 2)
            x = 60 + col * (WIDTH // 2 - 40)
            y = HEIGHT - 120 + row * 60
            pwr_str = f"({move.power})" if move.power > 0 else "(---)"
            rect = draw_text(screen, f"{move.name} {pwr_str}", FONT_UI, GB_TEXT, x, y, center=False)
            self.engine.move_menu_rects.append(rect)
        back_rect = pygame.Rect(WIDTH - 180, HEIGHT - 90, 140, 50)
        draw_classic_panel(screen, back_rect.x, back_rect.y, back_rect.w, back_rect.h)
        draw_text(screen, "BACK", FONT_UI, GB_TEXT, back_rect.centerx, back_rect.centery)
        self.engine.move_menu_rects.append(back_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i in range(len(self.engine.move_menu_rects)):
                if self.engine.move_menu_rects[i].collidepoint(event.pos):
                    if i == len(self.engine.move_menu_rects) - 1:
                        self.engine.state_machine.set_state("MAIN")
                    else:
                        self.engine.current_player_move_idx = i
                        p_move = self.engine.party.active.moves[i]
                        self.engine.q_text, self.engine.options, self.engine.correct_ans = self.engine.math_system.generate_problem(p_move.power)
                        self.engine.state_machine.set_state("MATH")
                    break

class MathState(BattleState):
    def draw(self, screen):
        self.engine.draw_battle_scene(screen)
        draw_classic_panel(screen, 20, HEIGHT - 180, WIDTH - 40, 160)
        draw_text(screen, self.engine.q_text, FONT_MSG, GB_TEXT, WIDTH // 2, HEIGHT - 140)
        self.engine.math_option_rects = []
        for i, opt in enumerate(self.engine.options):
            x = 40 + (i % 2) * (WIDTH // 2 - 40)
            y = HEIGHT - 100 + (i // 2) * 40
            rect = draw_text(screen, opt, FONT_UI, GB_TEXT, x, y, center=False)
            self.engine.math_option_rects.append(rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, rect in enumerate(self.engine.math_option_rects):
                if rect.collidepoint(event.pos):
                    opt = self.engine.options[i]
                    if opt == self.engine.correct_ans:
                        # Use NEW sorted queue with speed + priority
                        self.engine.turn_queue = self.engine.build_sorted_turn_queue(self.engine.current_player_move_idx)
                    else:
                        # Wrong answer → enemy acts only
                        e_move_idx = self.engine.choose_enemy_move_idx()
                        self.engine.turn_queue = [self.engine.create_act("enemy", e_move_idx)]
                        self.engine.add_message("Missed! Calculation error.")
                    self.engine.state_machine.set_state("TURN")
                    break

# [REF-0024c] Bag & Party
class BagState(BattleState):
    def draw(self, screen):
        self.engine.draw_battle_scene(screen)
        draw_classic_panel(screen, 20, HEIGHT - 180, WIDTH - 40, 160)
        draw_bag_menu(screen, self.engine.bag_pocket, self.engine.bag_cursor, self.engine.bag, self.engine.trainer_name)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i in range(3):
                if 140 + i * 80 <= event.pos[1] <= 140 + i * 80 + 60 and 30 <= event.pos[0] <= 300:
                    self.engine.bag_pocket = i
                    self.engine.bag_cursor = 0
                    return
            pocket_key = ["items", "pokeballs", "key_items"][self.engine.bag_pocket]
            items = self.engine.bag.pockets[pocket_key]
            items = self.engine.bag.get_items_in_pocket(pocket_key)
            panel_x, panel_y = 340, 130 + self.engine.bag_pocket * 80
            for i, item in enumerate(items):
                y = panel_y + 30 + i * 45
                if panel_x <= event.pos[0] <= panel_x + 400 and y <= event.pos[1] <= y + 40:
                    if pocket_key == "pokeballs" and self.engine.is_trainer:
                        self.engine.add_message("Don't be a thief!")
                        self.engine.state_machine.set_state(self.engine.bag_return_state or 'MAIN')
                        return

                    if item['qty'] > 0:
                        if pocket_key == "pokeballs":
                            item["qty"] -= 1
                            ball_name = item["name"]
                            caught, shakes = self.engine.mechanics.catch_attempt(self.engine.enemy.max_hp, self.engine.enemy.hp, self.engine.enemy.capture_rate, ball_name)
                            self.engine.catch_system.start(self.engine.enemy, ball_name, caught, shakes)
                            self.engine.state_machine.set_state("CATCH")
                        elif pocket_key == "items":
                            item_name = item['name'].upper()
                            item["qty"] -= 1
                    if pocket_key == "pokeballs":
                        self.engine.bag.remove_item(item["name"], 1)
                        ball_name = item["name"]
                        caught, shakes = self.engine.mechanics.catch_attempt(self.engine.enemy.max_hp, self.engine.enemy.hp, self.engine.enemy.capture_rate, ball_name)
                        self.engine.catch_system.start(self.engine.enemy, ball_name, caught, shakes)
                        self.engine.state_machine.set_state("CATCH")
                    elif pocket_key == "items":
                        item_name = item['name'].upper()
                        if self.engine.bag.remove_item(item["name"], 1):
                            if "POTION" in item_name:
                                heal_amount = 50 if "SUPER" in item_name else 20
                                self.engine.party.active.heal(heal_amount)
                                self.engine.add_message(f"{self.engine.party.active.name} recovered {heal_amount} HP!")
                                e_act = self.engine.create_act("enemy", self.engine.choose_enemy_move_idx())
                                self.engine.turn_queue = [e_act]
                                self.engine.state_machine.set_state("TURN")
                            elif item_name in ("FULL HEAL", "REVIVE"):
                                # Open party so player chooses target
                                self.engine.pending_item = item_name
                                self.engine.state_machine.set_state("PARTY")
                                return # Don't let enemy act yet
                            else:
                                self.engine.add_message(f"Used {item['name']}!")
                                e_act = self.engine.create_act("enemy", self.engine.choose_enemy_move_idx())
                                self.engine.turn_queue = [e_act]
                                self.engine.state_machine.set_state("TURN")
                            
                            # Enemy gets a free turn after item use
                            e_act = self.engine.create_act("enemy", self.engine.choose_enemy_move_idx())
                            self.engine.turn_queue = [e_act]
                            self.engine.state_machine.set_state("TURN")
                    return
            if HEIGHT - 90 <= event.pos[1] <= HEIGHT - 30 and WIDTH//2 - 100 <= event.pos[0] <= WIDTH//2 + 100:
                self.engine.state_machine.set_state(self.engine.bag_return_state or 'MAIN')

# [REF-0024d] Action & Result
class TurnState(BattleState):
    def update(self):
        self.engine.anim_ctrl.update()
        result = self.engine.turn_processor.update()

        if getattr(self.engine, 'fled', False) and result != "WAIT":
            self.engine.battle_running = False
            return

        if result == "NEXT_TURN":
            self.engine.turn_processor.process_residuals()   # residuals
            self.engine.state_machine.set_state("MAIN")
        elif result == "FAINT_ENEMY":
            if not self.engine.ko_catch_offered:
                self.engine.ko_catch_offered = True
                self.engine.feedback_text = f"Enemy {self.engine.enemy.name} fainted!"
                self.engine.state_machine.set_state("KO_CATCH")
            else:
                # Process XP and check for level up
                next_state = self.engine.level_up_system.process_win()
                self.engine.state_machine.set_state(next_state)

    def draw(self, screen):
        self.engine.draw_battle_scene(screen)
        draw_classic_panel(screen, 20, HEIGHT - 180, WIDTH - 40, 160)
        current_msg = self.engine.message_queue[0][0] if self.engine.message_queue else self.engine.feedback_text
        draw_multiline_text(screen, current_msg, FONT_MSG, GB_TEXT, WIDTH // 2, HEIGHT - 100, WIDTH - 100)

class CatchState(BattleState):
    def update(self):
        self.engine.catch_system.update()
        if self.engine.catch_system.finished:
            if self.engine.catch_system.caught:
                self.engine.battle_won = True
                next_state = self.engine.level_up_system.process_win()
                self.engine.state_machine.set_state(next_state)
            else:
                # KO Catch failure gets the special flavor text
                if self.engine.ko_catch_offered:
                    msg = f"This particular {self.engine.enemy.name} was too determined!"
                else:
                    msg = "Oh no! The Pokémon broke free!"
                self.engine.add_message(msg)
                
                # Always end battle with victory/XP after KO catch attempt
                next_state = self.engine.level_up_system.process_win()
                self.engine.state_machine.set_state(next_state)
        return

    def draw(self, screen):
        self.engine.draw_battle_scene(screen)   # clean background
        self.engine.catch_system.draw()

class VictoryState(BattleState):
    def draw(self, screen):
        self.engine.draw_battle_scene(screen)
        draw_classic_panel(screen, 20, HEIGHT - 180, WIDTH - 40, 160)
        draw_multiline_text(screen, "Victory! You won the battle!", FONT_MSG, GB_TEXT, WIDTH // 2, HEIGHT - 100, WIDTH - 100)
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.engine.battle_running = False

class PartyState(BattleState):
    def draw(self, screen):
        self.engine.draw_battle_scene(screen)
        self.name_rects = draw_party_menu(screen, self.engine.party.pokemon, self.engine.party_cursor)
        
        # Item confirmation popup ("Use / Cancel")
        if self.engine.pending_item and hasattr(self.engine, 'selected_item_mon') and self.engine.selected_item_mon is not None:
            mon = self.engine.party.pokemon[self.engine.selected_item_mon]
            draw_classic_panel(screen, 300, 260, 420, 160, f"Use {self.engine.pending_item} on {mon.name}?")
            use_rect = pygame.Rect(340, 340, 140, 50)
            cancel_rect = pygame.Rect(520, 340, 140, 50)
            draw_classic_panel(screen, use_rect.x, use_rect.y, use_rect.w, use_rect.h)
            draw_text(screen, "USE", FONT_UI, GREEN, use_rect.centerx, use_rect.centery)
            draw_classic_panel(screen, cancel_rect.x, cancel_rect.y, cancel_rect.w, cancel_rect.h)
            draw_text(screen, "CANCEL", FONT_UI, RED, cancel_rect.centerx, cancel_rect.centery)
            self.engine.item_popup_rects = [use_rect, cancel_rect]

        # Normal sub-menu
        elif hasattr(self.engine, 'submenu_mon') and self.engine.submenu_mon is not None:
            draw_party_submenu(screen, self.engine.submenu_cursor, self.engine.submenu_mon, self.engine.party.pokemon)

        if self.engine.party.active.is_fainted():
            draw_classic_panel(screen, 20, HEIGHT - 100, WIDTH - 40, 80)
            draw_text(screen, "Choose a Pokémon to send out!", FONT_UI, GB_TEXT, WIDTH // 2, HEIGHT - 60)

        # BACK button when using item (prevents soft lock)
        if self.engine.pending_item:
            back_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT - 90, 200, 60)
            draw_classic_panel(screen, back_rect.x, back_rect.y, back_rect.w, back_rect.h)
            draw_text(screen, "BACK", FONT_UI, GB_TEXT, back_rect.centerx, back_rect.centery)
            self.engine.item_back_rect = back_rect

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # Back button (when using item)
            if (hasattr(self.engine, 'item_back_rect') and 
                self.engine.item_back_rect is not None and 
                self.engine.item_back_rect.collidepoint(mx, my)):
                self.engine.pending_item = None
                self.engine.selected_item_mon = None
                self.engine.state_machine.set_state("BAG")
                return

            # Item popup (Use / Cancel)
            if self.engine.pending_item and hasattr(self.engine, 'item_popup_rects'):
                for i, rect in enumerate(self.engine.item_popup_rects):
                    if rect.collidepoint(mx, my):
                        if i == 0:  # USE
                            mon = self.engine.party.pokemon[self.engine.selected_item_mon]
                            msg = self.engine.use_item_on_mon(self.engine.pending_item, mon)
                            self.engine.add_message(msg)
                            self.engine.pending_item = None
                            self.engine.selected_item_mon = None
                            self.engine.state_machine.set_state("TURN")
                        else:  # CANCEL
                            self.engine.selected_item_mon = None
                        return

            # Click only name or sprite area
            for name_rect, i in getattr(self, 'name_rects', []):
                sprite_area = (72 <= mx <= 135 and 130 + i * 70 - 12 <= my <= 130 + i * 70 + 48)
                if name_rect.collidepoint(mx, my) or sprite_area:
                    p = self.engine.party.pokemon[i]
                    if self.engine.pending_item:
                        self.engine.selected_item_mon = i
                    else:
                        self.engine.submenu_mon = i
                        self.engine.submenu_cursor = 0
                    return

            # Sub-menu option clicks
            if not self.engine.pending_item and hasattr(self.engine, 'submenu_mon') and self.engine.submenu_mon is not None:
                x = 520
                y_base = 140 + self.engine.submenu_mon * 70 + 30
                for i in range(4):
                    opt_y = y_base + i * 55
                    if x + 140 <= mx <= x + 380 and opt_y <= my <= opt_y + 50:
                        self.engine.handle_submenu_option(i, self.engine.submenu_mon)
                        self.engine.submenu_mon = None
                    elif option_idx == 0:  # SUMMARY
                        self.engine.summary_mon = self.engine.submenu_mon
                        self.engine.state_machine.set_state("SUMMARY")
                        return

class SummaryState(BattleState):
    def update(self):
        if not hasattr(self, 'cry_played'):
            if self.engine.party.pokemon[self.engine.summary_mon].cry:
                try:
                    self.engine.party.pokemon[self.engine.summary_mon].cry.play()
                except:
                    pass
            self.cry_played = True

    def draw(self, screen):
        mon = self.engine.party.pokemon[self.engine.summary_mon]
        screen.blit(self.engine.battle_bg, (0, 0)) if self.engine.battle_bg else screen.fill((25,55,25))
        
        # Big sprite (centered)
        if mon.front_sprite:
            sprite = pygame.transform.scale(mon.front_sprite, (256, 256))
            screen.blit(sprite, (WIDTH//2 - 128, 120))
        
        draw_text(screen, f"#{mon.id:03d} {mon.name}", FONT_BIG, GOLD, WIDTH//2, 420, center=True)
        draw_text(screen, f"Lv.{mon.level}  HP: {int(mon.hp)}/{int(mon.max_hp)}", FONT_UI, WHITE, WIDTH//2, 480, center=True)
        
        # BACK button (GB style)
        back_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT - 100, 200, 50)
        draw_classic_panel(screen, back_rect.x, back_rect.y, back_rect.w, back_rect.h)
        draw_text(screen, "BACK", FONT_UI, GB_TEXT, back_rect.centerx, back_rect.centery)
        self.back_rect = back_rect

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.back_rect.collidepoint(event.pos):
            self.engine.summary_mon = None
            self.engine.state_machine.set_state("PARTY")

# [REF-XXXX] Learn Move State (when a Pokémon levels up and wants to learn a new move)
class LearnMoveState(BattleState):
    def __init__(self, engine):
        super().__init__(engine)
        self.mon = None               # The Pokémon learning the move
        self.new_move = None          # The move to learn
        self.move_options = []        # List of current moves + new one
        self.cursor = 0
        self.confirming = False
        self.selected_to_replace = -1

    def enter(self, mon=None, new_move=None):
        """Called when entering this state"""
        if mon is None or new_move is None:
            print("[WARNING] LearnMoveState entered without mon or move")
            self.engine.state_machine.set_state("MAIN")
            return

        self.mon = mon
        self.new_move = new_move
        self.move_options = mon.moves[:] + [new_move]  # current 4 + new one
        self.cursor = 0
        self.confirming = False
        self.selected_to_replace = -1

        self.engine.add_message(f"{mon.name} wants to learn {new_move.name}!")
        self.engine.add_message("Select a move to forget (or cancel).")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.cursor = (self.cursor - 1) % len(self.move_options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.cursor = (self.cursor + 1) % len(self.move_options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.confirming:
                    if self.selected_to_replace >= 0:
                        # Replace the move
                        old_move = self.mon.moves[self.selected_to_replace]
                        self.mon.moves[self.selected_to_replace] = self.new_move
                        self.engine.add_message(f"{self.mon.name} forgot {old_move.name}...")
                        self.engine.add_message(f"...and learned {self.new_move.name}!")
                    self.engine.state_machine.set_state("MAIN")
                else:
                    if self.cursor < len(self.mon.moves):
                        # Choose which move to replace
                        self.selected_to_replace = self.cursor
                        self.confirming = True
                        self.engine.add_message(f"Really forget {self.mon.moves[self.cursor].name}?")
                    else:
                        # Cancel (don't learn the new move)
                        self.engine.add_message(f"{self.mon.name} did not learn {self.new_move.name}.")
                        self.engine.state_machine.set_state("MAIN")

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Optional: add mouse support later
            pass

    def update(self):
        pass  # no continuous animation needed here

    def draw(self, screen):
        # Dark overlay background
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        draw_classic_panel(screen, 80, 100, WIDTH-160, HEIGHT-200, title="LEARN MOVE")

        y = 180
        draw_text(screen, f"{self.mon.name} wants to learn", FONT_UI, GOLD, WIDTH//2, y, center=True)
        y += 50
        draw_text(screen, self.new_move.name.upper(), FONT_BIG, WHITE, WIDTH//2, y, center=True)
        y += 80

        draw_text(screen, "Which move should be forgotten?", FONT_UI, GB_TEXT, WIDTH//2, y, center=True)
        y += 60

        for i, move in enumerate(self.move_options):
            text = move.name if i < len(self.mon.moves) else f"{move.name} (NEW!)"
            color = HOVER_LIGHT if i == self.cursor else GB_TEXT
            draw_text(screen, text, FONT_UI, color, WIDTH//2, y + i*50, center=True)

        if self.confirming:
            draw_classic_panel(screen, WIDTH//2 - 200, HEIGHT - 180, 400, 120)
            draw_text(screen, "Forget this move?", FONT_UI, RED, WIDTH//2, HEIGHT - 140, center=True)
            draw_text(screen, "YES          NO", FONT_UI, WHITE, WIDTH//2, HEIGHT - 100, center=True)

class KOCatchState(BattleState):
    def draw(self, screen):
        self.engine.draw_battle_scene(screen)
        draw_classic_panel(screen, 20, HEIGHT - 180, WIDTH - 40, 160)
        draw_text(screen, f"Catch the fainted {self.engine.enemy.name}?", 
                  FONT_MSG, GB_TEXT, WIDTH // 2, HEIGHT - 140)
        
        yes_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT - 90, 140, 50)
        no_rect = pygame.Rect(WIDTH // 2 + 10, HEIGHT - 90, 140, 50)
        
        draw_classic_panel(screen, yes_rect.x, yes_rect.y, yes_rect.w, yes_rect.h)
        draw_text(screen, "YES", FONT_UI, GB_TEXT, yes_rect.centerx, yes_rect.centery)
        
        draw_classic_panel(screen, no_rect.x, no_rect.y, no_rect.w, no_rect.h)
        draw_text(screen, "NO", FONT_UI, GB_TEXT, no_rect.centerx, no_rect.centery)
        
        self.engine.ko_catch_rects = [yes_rect, no_rect]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, rect in enumerate(self.engine.ko_catch_rects):
                if not self.engine.can_catch:
                    return
                if rect.collidepoint(event.pos):
                    if i == 0:  # YES → 95% catch rate
                        caught = random.random() < 0.95
                        shakes = 3 if caught else random.randint(1, 2)
                        self.engine.catch_system.start(self.engine.enemy, "POKÉ BALL", caught, shakes)
                        self.engine.state_machine.set_state("CATCH")
                    else:  # NO
                        next_state = self.engine.level_up_system.process_win()
                        self.engine.state_machine.set_state(next_state)
                    return

class FaintMsgState(BattleState):
    def draw(self, screen):
        self.engine.draw_battle_scene(screen)
        draw_classic_panel(screen, 20, HEIGHT - 180, WIDTH - 40, 160)
        current_msg = self.engine.message_queue[0][0] if self.engine.message_queue else self.engine.feedback_text
        draw_multiline_text(screen, current_msg, FONT_MSG, GB_TEXT, WIDTH // 2, HEIGHT - 100, WIDTH - 100)
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.engine.party.active.is_fainted():
                if self.engine.party.is_wiped(): self.engine.battle_running = False
                else: self.engine.state_machine.set_state("PARTY")
            else:
                if not self.engine.is_trainer: self.engine.state_machine.set_state("KO_CATCH")
                else:
                    next_state = self.engine.level_up_system.process_win()
                    self.engine.state_machine.set_state(next_state)

# [REF-0024e] State Machine
class BattleStateMachine:
    def __init__(self, engine):
        self.engine = engine
        self.states = {
            'LOADING': LoadingState(engine),
            'INTRO': IntroState(engine),
            'MAIN': MainBattleState(engine),
            'MOVES': MovesState(engine),
            'MATH': MathState(engine),
            'BAG': BagState(engine),
            'TURN': TurnState(engine),
            'CATCH': CatchState(engine),
            'VICTORY': VictoryState(engine),
            'LEARN_MOVE': LearnMoveState(engine),
            'PARTY': PartyState(engine),
            'SUMMARY': SummaryState(engine),
            'LEARN_MOVE': LearnMoveState(engine),
            'KO_CATCH': KOCatchState(engine),
            'FAINT_MSG': FaintMsgState(engine),
        }
        self.current_state = self.states['LOADING']

    def set_state(self, name):
        if name in self.states:
            self.current_state = self.states[name]
    
    def update(self):
        self.current_state.update()

    def draw(self, screen):
        self.current_state.draw(screen)

    def handle_event(self, event):
        self.current_state.handle_event(event)

# [REF-0025f] REUSABLE STORY BATTLE SYSTEM — base for all cinematic intros
from abc import ABC, abstractmethod

# [REF-0025f] REUSABLE STORY BATTLE SYSTEM — black flush textbox + Gameboy style
from abc import ABC, abstractmethod

class StoryBattle(ABC):
    def __init__(self, screen, clock, overworld, data_manager, 
                 bg_filename=None,           # ← specific file (e.g. "forest1.png")
                 bg_subfolder="overworld/story",  # ← DEFAULT: your exact folder
                 music_file="kanto_route1.ogg",
                 story_lines=None):
        self.screen = screen
        self.clock = clock
        self.overworld = overworld
        self.data_manager = data_manager
        
        # === BACKGROUND LOGIC (your exact folder + fallback) ===
        if bg_filename:
            self.bg = load_bg(bg_filename, f"pngs/{bg_subfolder}")
            if self.bg:
                print(f"📸 Loaded specific story background: {bg_filename}")
            else:
                print(f"⚠️ Could not load {bg_filename} — falling back to random from overworld/story")
                self.bg = self._load_random_from_folder("overworld/story")
        else:
            self.bg = self._load_random_from_folder("overworld/story")
            print(f"🎲 Using random background from pngs/overworld/story/")

        # Story text
        player_name = getattr(overworld, "player_name", "TRAINER")
        self.story_lines = story_lines or [
            "Today was the day.",
            f"{player_name} had an appointment with Professor Oak to get their first Pokémon.",
            f"Too excited to sleep, {player_name} got up early and decided to take a walk through the nearby woods."
        ]
        
        self.phase = 0
        self.current_line = 0
        self.char_idx = 0
        self.text_timer = 0
        self.text_done = False
        self.current_text = ""
        self.click_cooldown = 0
        self.music_started = False
        self.finished = False
        self.music_file = music_file

    def _load_random_from_folder(self, subfolder):
        bg_dir = os.path.join(ASSETS_DIR, "pngs", subfolder)
        bg_files = []
        if os.path.exists(bg_dir):
            bg_files = [f for f in os.listdir(bg_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if bg_files:
            chosen = random.choice(bg_files)
            print(f"   → Chose: {chosen}")
            return load_bg(chosen, f"pngs/{subfolder}")
        print("⚠️ No images found in folder — using black fallback")
        return None

    def _play_music(self):
        path = os.path.join(ASSETS_DIR, "sounds", self.music_file)
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1)

    def _stop_music(self):
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()

    def update_story_text(self):
        if not self.text_done:
            self.text_timer += 1
            if self.text_timer >= 3:
                self.text_timer = 0
                self.char_idx += 1
                target = self.story_lines[self.current_line]
                self.current_text = target[:self.char_idx]
                if self.char_idx >= len(target):
                    self.text_done = True
        if self.click_cooldown > 0:
            self.click_cooldown -= 1

    def handle_input(self, event):
        if self.click_cooldown > 0: return False
        if event.type not in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN): return False
        if event.type == pygame.KEYDOWN and event.key not in (pygame.K_SPACE, pygame.K_RETURN):
            return False

        if self.phase == 0:
            if not self.text_done:
                self.current_text = self.story_lines[self.current_line]
                self.text_done = True
                self.click_cooldown = 8
                return False
            self.current_line += 1
            if self.current_line >= len(self.story_lines):
                self.phase = 1
                self._start_cinematic()
            else:
                self.char_idx = 0
                self.text_timer = 0
                self.text_done = False
                self.current_text = ""
                self.click_cooldown = 8
            return False
        return self.phase >= 99

    @abstractmethod
    def _start_cinematic(self): pass
    @abstractmethod
    def update_cinematic(self): pass
    @abstractmethod
    def draw_cinematic(self): pass

    def run(self):
        if not self.music_started:
            self._play_music()
            self.music_started = True

        while not self.finished:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._stop_music()
                    return
                if self.handle_input(event):
                    break
            
            if self.phase == 0:
                self.update_story_text()
            else:
                self.update_cinematic()
            
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        
        self._stop_music()
        self._launch_battle()

    def draw(self):
        self.screen.fill(BLACK)
        if self.bg:
            scaled_bg = pygame.transform.scale(self.bg, (WIDTH, HEIGHT - 200))
            self.screen.blit(scaled_bg, (0, 0))
        else:
            # Emergency visible fallback (dark green forest color)
            pygame.draw.rect(self.screen, (34, 139, 34), (0, 0, WIDTH, HEIGHT - 200))
        
        if self.phase == 0:
            draw_classic_panel(self.screen, 8, HEIGHT - 196, WIDTH - 16, 188)
            draw_multiline_text(self.screen, self.current_text, FONT_MSG, GB_TEXT,
                                WIDTH//2, HEIGHT - 125, WIDTH - 80, line_height=38, center=True)
        else:
            self.draw_cinematic()

# [REF-0025g] POOCHYENA RESCUE — story text only (rescue lunge now inside battle)
class PoochyenaRescueBattle(StoryBattle):
    def __init__(self, screen, clock, overworld, data_manager):
        super().__init__(screen, clock, overworld, data_manager,
                         bg_filename="forest1.png",          # ← your exact file
                         bg_subfolder="overworld/story",     # ← your exact folder
                         music_file="kanto_route1.ogg")

    def _start_cinematic(self):
        self.finished = True

    def update_cinematic(self):
        pass

    def draw_cinematic(self):
        pass

    def _launch_battle(self):
        print("🚀 Starting Poochyena rescue battle with lunge animation...")
        trainer_idx = getattr(self.overworld, "selected_char_idx", 0)
        trainer_list = getattr(self.overworld, "available_trainers", None)
        chosen_trainer_sprite = trainer_list[trainer_idx]["back"] if trainer_list and 0 <= trainer_idx < len(trainer_list) else None
        
        engine = BattleEngine(
            self.screen, self.clock, self.overworld.player_party,
            POOCHYENA_ID, is_trainer=False,
            battle_bg_files=getattr(self.overworld, 'battle_bg_files', []),
            use_cache_only=True,
            trainer_sprite=chosen_trainer_sprite,
            rescue_mode=True,
            can_catch=False
        )
        engine.run()

class RivalRescueBattle(StoryBattle):
    def __init__(self, screen, clock, overworld, data_manager):
        super().__init__(screen, clock, overworld, data_manager,
                         bg_filename="route1_north.png",   # or whatever
                         music_file="kanto_trainer.ogg")
        # ... your rival sprites, cries, etc.
    
    # Just copy the 4 methods from PoochyenaRescueBattle and change names/sprites

# [REF-0025] VISUAL SYSTEMS
class IntroSystem:
    # [REF-0025a] Intro Animation
    """Handles the battle start animation (Trainer slide, Wild appear, Ball throw)"""
    def __init__(self, screen, data_manager):
        self.screen = screen
        self.data_manager = data_manager
        self.active = False
        self.phase = 0
        self.trainer_x = -420
        self.enemy_x = WIDTH + 420
        self.player_pokemon_x = -420
        self.ball_progress = 0.0
        self.ball_x = 0
        self.ball_y = 0
        self.flash_timer = 0
        self.text_timer = 0
        self.char_idx = 0
        self.current_text = ""
        self.text_done = False
        self.finished = False
        self.anim_timer = 0
        self.trainer_sprite = None
        self.player_mon = None
        self.enemy_mon = None
        self.ball_sprite = None
        self.trainer_system = None
        self.trainer_slide_out = False

    def start(self, trainer_sprite, player_mon, enemy_mon, trainer_system=None):
        self.active = True
        self.trainer_sprite = trainer_sprite
        self.player_mon = player_mon
        self.enemy_mon = enemy_mon
        self.trainer_system = trainer_system
        self.ball_sprite = self.data_manager.load_item_sprite("poké ball")
        self.phase = 0
        self.trainer_x = -420
        self.enemy_x = WIDTH + 420
        self.player_pokemon_x = -420
        self.ball_progress = 0.0
        self.flash_timer = 0
        self.text_timer = 0
        self.char_idx = 0
        self.text_done = False
        self.finished = False
        self.anim_timer = 0
        self.trainer_slide_out = False

    def update(self):
        if not self.active: return
        self.anim_timer += 1
        
        if self.phase == 0:  # Slide in
            self.trainer_x = min(PLAYER_POS[0] - 90, self.trainer_x + 19)
            self.enemy_x = max(ENEMY_POS[0], self.enemy_x - 24)
            if self.trainer_x >= PLAYER_POS[0] - 90 and self.enemy_x <= ENEMY_POS[0] + 15:
                self.phase = 1
                self.flash_timer = 8
                # === ENEMY CRY ON APPEAR ===
                if getattr(self.enemy_mon, 'cry', None):
                    try: self.enemy_mon.cry.play()
                    except: pass

        elif self.phase == 1:  # Text
            if self.trainer_system:
                self._update_text(f"{self.trainer_system.name} wants to battle!")
            else:
                self._update_text(f"A wild {self.enemy_mon.name} appeared!")
            if self.text_done and self.anim_timer > 300:
                self.advance()

        elif self.phase == 1.5:  # Ball throw
            if self.trainer_system and not self.trainer_slide_out:
                self.enemy_x += 24
                if self.enemy_x > WIDTH:
                    self.trainer_slide_out = True
                    self.enemy_x = ENEMY_POS[0]
                return

            self.ball_progress += 0.055
            if self.ball_progress < 1.0:
                start_x = self.trainer_x + 190
                start_y = PLAYER_POS[1] + 55
                self.ball_x = start_x + (ENEMY_POS[0] - start_x + 70) * self.ball_progress
                self.ball_y = start_y - 160 * math.sin(self.ball_progress * math.pi)
            else:
                self.phase = 2
                self.text_timer = 0
                self.char_idx = 0
                self.text_done = False
                self.flash_timer = 6

        elif self.phase == 2:  # Go Pokémon!
            self._update_text(f"Go! {self.player_mon.name}!")
            self.trainer_x -= 26
            self.player_pokemon_x = min(PLAYER_POS[0], self.player_pokemon_x + 28)
            if self.player_pokemon_x >= PLAYER_POS[0] - 15 and self.text_done:
                # === PLAYER CRY ON SEND OUT ===
                if getattr(self.player_mon, 'cry', None):
                    try: self.player_mon.cry.play()
                    except: pass
                self.finished = True
                self.active = False

    def _update_text(self, target_text):
        if not self.text_done:
            self.text_timer += 1
            if self.text_timer >= 2:
                self.text_timer = 0
                self.char_idx += 1
                self.current_text = target_text[:self.char_idx]
                if self.char_idx >= len(target_text): self.text_done = True
        else:
            self.current_text = target_text

    def advance(self):
        if self.phase == 1 and self.text_done:
            self.phase = 1.5
            self.ball_progress = 0.0
        elif self.phase == 2 and self.text_done:
            if self.player_mon.cry:
                try: self.player_mon.cry.play()
                except: pass
            self.finished = True
            self.active = False

    def draw(self):
        if not self.active: return
        bob = int(math.sin(self.anim_timer / 6) * 5)
        # Enemy (Trainer or Pokemon)
        if self.trainer_system and not self.trainer_slide_out:
            self.screen.blit(self.trainer_system.sprite, 
                             (self.enemy_x, ENEMY_POS[1]))
        else:
            # Defensive check
            if getattr(self.enemy_mon, 
                       'sprite', 
                       None) is not None:
                if self.flash_timer > 0:
                    flash_surf = self.enemy_mon.sprite.copy()
                    flash_surf.fill((255, 255, 255), 
                                    special_flags=pygame.BLEND_RGB_ADD)
                    self.screen.blit(flash_surf, 
                                    (self.enemy_x, ENEMY_POS[1] + bob))
                    self.flash_timer -= 1
                else:
                    self.screen.blit(self.enemy_mon.sprite, 
                                    (self.enemy_x, 
                                    ENEMY_POS[1] + bob))
        # Trainer
        if self.phase < 2:
            self.screen.blit(self.trainer_sprite, 
                            (self.trainer_x, 
                            PLAYER_POS[1] - 40))
        # Player Mon
        if self.phase >= 2 and self.player_mon.sprite:
            p_surf = self.player_mon.sprite.copy()
            progress = min(1.0, (self.player_pokemon_x + 420) / 420)
            scale = 0.6 + 0.4 * progress
            p_surf = pygame.transform.rotozoom(p_surf, 0, scale)
            self.screen.blit(p_surf, (self.player_pokemon_x, 
                                      PLAYER_POS[1] + int(15 * math.sin(self.anim_timer / 4))))
        # Ball
        if self.phase == 1.5:
            rot = int(self.ball_progress * -1080)
            ball_surf = pygame.transform.rotate(self.ball_sprite, 
                                                rot)
            self.screen.blit(ball_surf, 
                             (self.ball_x - 18, 
                              self.ball_y - 18))
        # Text Panel
        if self.phase in [1, 2]:
            draw_classic_panel(self.screen, 
                               20, HEIGHT - 180, 
                               WIDTH - 40, 160)
            draw_multiline_text(self.screen, 
                                self.current_text, 
                                FONT_MSG, GB_TEXT, 
                                WIDTH // 2, 
                                HEIGHT - 100, 
                                WIDTH - 100)

# [NEW REF-0025h] RESCUE INTRO — dramatic Poochyena lunge inside the actual battle
class RescueIntroSystem(IntroSystem):
    def __init__(self, screen, data_manager, battle_engine=None):
        super().__init__(screen, data_manager)
        self.engine = battle_engine
        self.rescue_phase = 0
        self.lunge_offset = 0
        self.starter_x = -400
        self.poochyena_x = WIDTH + 100
        self.poochyena_x = ENEMY_POS[0]
        self.player_x = PLAYER_POS[0]
        self.finished = False
        self.poochyena_sprite = None
        self.starter_back = None

    def start_rescue_mode(self, player_mon, enemy_mon):
        self.player_mon = player_mon
        self.enemy_mon = enemy_mon
        self.rescue_phase = 1
        self.anim_timer = 0
        self.finished = False
        self.lunge_offset = 0

        pooch_data = self.data_manager.fetch_pokemon_data(POOCHYENA_ID, back=True)
        self.poochyena_back = pooch_data[0]
        # Load Poochyena FRONT sprite (enemy)
        pooch_data = self.data_manager.fetch_pokemon_data(POOCHYENA_ID, back=False)
        self.poochyena_sprite = pooch_data[0]
        self.poochyena_cry = self.data_manager.load_cry(POOCHYENA_ID)

        starter_data = self.data_manager.fetch_pokemon_data(player_mon.id, back=True)
        self.starter_back = starter_data[0]
        self.starter_cry = self.data_manager.load_cry(player_mon.id)
        
        self.player_x = PLAYER_POS[0]
        self.starter_x = -300

    def update(self):
        self.anim_timer += 1
        if self.rescue_phase == 1:  # LUNGE + CRY
            # Lunge animation (0-10: forward, 10-20: back)
            if self.anim_timer < 10:
                self.lunge_offset = -int(self.anim_timer * 8)
            elif self.anim_timer < 20:
                self.lunge_offset = -80 + int((self.anim_timer - 10) * 8)
            else:
                self.lunge_offset = 0
            
            if self.anim_timer == 10 and self.poochyena_cry:
                self.poochyena_cry.play()
            
            if self.anim_timer > 60:
                self.rescue_phase = 2
                self.anim_timer = 0

        elif self.rescue_phase == 2:  # PLAYER SLIDE OUT
            self.player_x -= 15
            if self.player_x < -300:
                self.rescue_phase = 3
                self.anim_timer = 0
                if self.starter_cry: self.starter_cry.play()
                
        elif self.rescue_phase == 3:  # STARTER SLIDES IN
            self.starter_x += 20
            if self.starter_x >= PLAYER_POS[0]:
                self.starter_x = PLAYER_POS[0]
                self.finished = True
                if self.engine:
                    self.engine.rescue_finished = True   # ← forces transition
                self.rescue_phase = 0

    def draw(self):
        # Draw Player (Trainer)
        if self.rescue_phase < 3:
            if self.engine and self.engine.spr_player:
                self.screen.blit(self.engine.spr_player, (self.player_x, PLAYER_POS[1] - 40))

        # Draw Poochyena (Enemy)
        if self.poochyena_sprite:
            px = self.poochyena_x + (self.lunge_offset if self.rescue_phase == 1 else 0)
            self.screen.blit(self.poochyena_sprite, (px, ENEMY_POS[1]))
            
        # Draw Starter (Player's Pokemon)
        if self.starter_back and self.rescue_phase == 3:
            self.screen.blit(self.starter_back, (self.starter_x, PLAYER_POS[1]))

# [REF-0025b] Catch Animation
class CatchSystem:
    """Handles the entire ball throw, shake, and capture logic"""
    def __init__(self, screen, data_manager):
        self.screen = screen
        self.data_manager = data_manager
        self.active = False
        self.phase = 0
        self.timer = 0
        self.ball_name = ""
        self.ball_sprite = None
        self.ball_x = 0
        self.ball_y = 0
        self.ball_dy = 0
        self.enemy_scale = 1.0
        self.shakes = 0
        self.caught = False
        self.finished = False
        self.message = ""
        self.enemy = None

    def start(self, enemy, ball_name, caught, shakes):
        self.active = True
        self.enemy = enemy
        self.ball_name = ball_name
        self.ball_sprite = self.data_manager.load_item_sprite(ball_name)
        self.caught = caught
        self.shakes = shakes
        self.phase = 0
        self.timer = 0
        self.ball_x = PLAYER_POS[0] + 180
        self.ball_y = PLAYER_POS[1] + 120
        self.ball_dy = -12
        self.enemy_scale = 1.0
        self.finished = False
        self.message = f"Threw a {ball_name}!"

    def update(self):
        if not self.active: return
        self.timer += 1
        
        if self.phase == 0: # Throw Arc
            self.ball_x += (ENEMY_POS[0] + 60 - self.ball_x) * 0.08
            self.ball_y += self.ball_dy
            self.ball_dy += 0.5
            if self.ball_y >= ENEMY_POS[1] + 40:
                self.phase = 1
                self.timer = 0
                self.enemy_scale = 1.0
        elif self.phase == 1: # Suck In
            self.enemy_scale = max(0, 1.0 - self.timer * 0.1)
            if self.timer > 15:
                self.phase = 2
                self.timer = 0
        elif self.phase == 2: # Shake
            if self.timer > 140:
                if self.caught:
                    self.message = f"Gotcha! {self.enemy.name} was caught!"
                    self.finished = True
                else:
                    self.phase = 3
                    self.timer = 0
        elif self.phase == 3: # Break Free
            self.message = "Oh no! The Pokémon broke free!"
            if self.timer > 60:
                self.finished = True
                self.active = False

    def draw(self):
        if not self.active: return
        # Draw Enemy (special scaling/hiding)
        if self.phase == 0 or self.phase == 3:
            if self.enemy.sprite: self.screen.blit(self.enemy.sprite, (ENEMY_POS[0], ENEMY_POS[1]))
        elif self.phase == 1:
            if self.enemy.sprite and self.enemy_scale > 0:
                w = int(BATTLE_SCALE * self.enemy_scale)
                h = int(BATTLE_SCALE * self.enemy_scale)
                s = pygame.transform.scale(self.enemy.sprite, (w, h))
                s.fill((255, 100, 100), special_flags=pygame.BLEND_RGB_MULT)
                self.screen.blit(s, (ENEMY_POS[0] + (BATTLE_SCALE-w)//2, ENEMY_POS[1] + (BATTLE_SCALE-h)//2))
        # Draw Ball
        if self.phase < 3:
            bx, by = int(self.ball_x), int(self.ball_y)
            if self.phase == 2:
                shake = 0
                if self.timer > 20 and self.timer < 140:
                    cycle = (self.timer - 20) // 40
                    if cycle < self.shakes:
                        p = (self.timer - 20) % 40
                        if p < 10: shake = -5
                        elif p < 20: shake = 5
                bx += shake
            if self.ball_sprite: self.screen.blit(self.ball_sprite, (bx, by))

# [REF-0025c] Faint Animation
class FaintAnimation:
    """Handles Pokémon fainting animation"""
    def __init__(self, screen):
        self.screen = screen
        self.active = False
        self.side = "enemy"
        self.timer = 0
        self.drop = 0
        self.shake = 0
        self.alpha = 255
        self.sprite = None
        self.pos = (0,0)

    def start(self, side, sprite, pos):
        self.active = True
        self.side = side
        self.sprite = sprite
        self.pos = pos
        self.timer = 0
        self.drop = 0
        self.shake = 0
        self.alpha = 255

    def update(self):
        if not self.active: return False
        self.timer += 1
        if self.timer < 8:
            self.shake = (-4 if self.timer % 4 < 2 else 4) if self.side == "player" else 0
        else:
            self.drop += 6
            self.alpha = max(0, 255 - (self.timer - 8) * 12)
        if self.timer > 40:
            self.active = False
            return True # Finished
        return False

    def draw(self):
        if not self.active or not self.sprite: return
        surf = self.sprite.copy()
        surf.set_alpha(self.alpha)
        x, y = self.pos
        self.screen.blit(surf, (x + self.shake, y + self.drop))

# [REF-0026] BATTLE ENGINE
class BattleEngine:
    # [REF-0026a] Initialization
    def __init__(self, screen, clock, player_party, enemy_id, player_bag=None, is_trainer=False,
                 trainer_name="", trainer_sprite=None, battle_bg_files=None,
                 wild_music=None, victory_music=None, trainer_music=None, **kwargs):
        self.screen = screen
        self.clock = clock
        self.can_catch = can_catch

        # === CORE SYSTEMS ===
        self.data_manager = DataManager()
        self.mechanics = BattleMechanics()
        self.math_system = MathBrain()
        self.battle_session = BattleSession(StageManager())

        # === PARTY === (now supports BOTH old test list AND new overworld Party object)
        if isinstance(player_party, Party):
            self.party = player_party
        else:
            self.party = Party([
                Pokemon(
                    p.get("id", random.randint(1, 151)),
                    self.data_manager,
                    self.mechanics,
                    p.get("level", 50),
                    back_sprite=True,
                    is_shiny=p.get("is_shiny", False)
                )
                for p in (player_party or [])
            ])

        # === ENEMY LOADING — CACHE-FIRST (Overworld-ready) ===
        self.use_cache_only = kwargs.get('use_cache_only', False)
        self.enemy_loaded = False
        self.enemy = None
        enemy_level = 50
        cache_key = (enemy_id, False, enemy_level)

        self.is_shiny = False
        if not is_trainer:
            # 1 in 4096 chance for a shiny
            self.is_shiny = random.random() < (1/4096)

        # === TRAINER SYSTEM + AUTO LEVEL SCALING FOR WILD POKÉMON ===
        self.trainer_system = None
        if is_trainer:
            self.trainer_system = TrainerSystem(trainer_name, "trainer.png",
                                                [{"id": enemy_id, "level": 50}],
                                                self.data_manager, self.mechanics)
            self.enemy = self.trainer_system.get_active()
            enemy_level = 50
        else:
            # Scale wild Pokémon (Poochyena, etc.) to your strongest Pokémon's level
            max_player_level = max((p.level for p in self.party.pokemon), default=5)
            enemy_level = max_player_level
            print(f"🌲 Wild Pokémon scaled to Lv.{enemy_level} (matches your strongest Pokémon)")

        # Create enemy with correct level
        if not is_trainer:
            self.enemy = Pokemon(enemy_id, self.data_manager, self.mechanics,
                                 level=enemy_level, back_sprite=False, is_shiny=self.is_shiny)

        # === ALL CORE SYSTEMS (must exist before spawning enemy) ===
        self.message_queue = []

        self.enemy_display_hp = 0
        self.player_display_hp = self.party.active.hp if self.party.pokemon else 0

        # Enemy & Trainer (simplified)
        self.is_trainer = is_trainer
        self.trainer_name = trainer_name
        self.battle_bg_files = battle_bg_files or []
        self.wild_music = wild_music or []
        self.victory_music = victory_music or []
        self.trainer_music = trainer_music or []
        self.battle_running = True

        self.volatile = {"player": {}, "enemy": {}}
        self.bag = Bag()
        self.bag = player_bag if player_bag is not None else Bag()
        self.pending_item = None
        self.selected_item_mon = None
        self.item_popup_rects = []
        self.item_back_rect = None
        self.sound_manager = SoundManager()
        self.anim_ctrl = AnimationController()
        self.level_up_system = LevelUpSystem(self)
        self.turn_processor = TurnProcessor(self)
        self.state_machine = BattleStateMachine(self)

        self.catch_system = CatchSystem(self.screen, self.data_manager)
        self.faint_system = FaintAnimation(self.screen)

        # === LOAD TRAINER SPRITE + SET UP INTRO SYSTEM ===
        passed_sprite = kwargs.get('trainer_sprite', None)
        if passed_sprite:
            self.spr_player = passed_sprite
        if trainer_sprite:
            self.spr_player = trainer_sprite
        else:
            self.spr_player = load_asset("red_back.png", "sprites", (BATTLE_SCALE, BATTLE_SCALE))
            self.spr_player = load_asset("red_back.png", "sprites/trainers/back", (BATTLE_SCALE, BATTLE_SCALE))

        self.rescue_mode = kwargs.get('rescue_mode', False)
        self.rescue_finished = False
        self.intro_system = RescueIntroSystem(self.screen, self.data_manager, self) if self.rescue_mode else IntroSystem(self.screen, self.data_manager)
        self.state_machine.set_state("INTRO")
        # === NOW SAFE TO SPAWN ENEMY ===
        if self.use_cache_only or cache_key in self.data_manager.POKEMON_CACHE:
            self.enemy = Pokemon(enemy_id, self.data_manager, self.mechanics,
                                 level=enemy_level, back_sprite=False, is_shiny=self.is_shiny)
            self.enemy.stage_manager = StageManager()
            self.enemy_display_hp = self.enemy.hp
            self.enemy_loaded = True

        if is_trainer:
            self.enemy = self.trainer_system.get_active()
            self.enemy.stage_manager = StageManager()
            self.enemy_loaded = True

        # Battle variables
        self.battle_menu_mode = 0
        self.battle_menu_cursor = 0
        self.bag_pocket = 0
        self.bag_cursor = 0
        self.party_cursor = 0
        self.submenu_cursor = 0
        self.submenu_mon = None
        self.pending_item = None
        self.main_menu_rects = []
        self.math_option_rects = []
        self.move_menu_rects = []
        self.bag_return_state = BATTLE_MENU_MAIN
        self.current_player_move_idx = 0
        self.summary_mon = None
        self.wait_timer = 0
        self.feedback_text = ""
        self.q_text = ""
        self.options = []
        self.correct_ans = ""
        self.turn_queue = []
        self.moves_to_learn = []
        self.flee_attempts = 0
        self.battle_won = False
        self.ko_catch_offered = False
        self.enemy_fainted = False
        self.fled = False
        self.debug_panel_visible = False

        self.battle_bg = None

        self.STATE_WILD_LOADING = "WILD_LOADING"
        self.STATE_WILD_INTRO = "WILD_INTRO"
        self.STATE_WILD_BATTLE = "WILD_BATTLE"
        self.current_state = self.STATE_WILD_LOADING

        # Visual upgrades
        self.player_bob = 0
        self.is_lunging = False
        self.lunge_side = None
        self.lunge_timer = 0
        self.impact_flash = 0
        self.impact_shake = 0
        self.pending_damage = 0
        self.pending_target = None

        if self.party.pokemon:
            self.player_id = self.party.pokemon[0].id
        else:
            self.player_id = random.randint(1, 151)
    
    def on_enemy_loaded(self, result):
        """Called safely from main thread when async enemy fetch finishes"""
        try:
            self.enemy = Pokemon(self.enemy_id, self.data_manager, self.mechanics,
                                 level=50, back_sprite=False)
            self.enemy.stage_manager = StageManager()
            self.enemy_display_hp = self.enemy.hp
            self.enemy_loaded = True
            print(f"✓ Async enemy loaded: {self.enemy.name} (Lv.{self.enemy.level})")

            if not self.is_trainer:
                self.state_machine.set_state("INTRO")
                self.intro_system.start(self.spr_player, self.party.active, self.enemy, self.trainer_system)
        except Exception as e:
            print(f"[ERROR] on_enemy_loaded: {e}")

    # [REF-0026b] AI & Queue Helpers
    def create_act(self, who, move_idx):
        mon = self.party.active if who == "player" else self.enemy
        move = mon.moves[move_idx]
        return {"who": who, "move_obj": move}
    
    def choose_enemy_move_idx(self):
        """Selects a move for the enemy and returns its index."""
        moves_with_indices = list(enumerate(self.enemy.moves))
        status_moves = [(i, m) for i, m in moves_with_indices if m.is_inflicter]
    
        if status_moves and not self.enemy.status and random.random() < 0.40:
            return random.choice(status_moves)[0]
    
        sorted_moves = sorted(moves_with_indices, key=lambda item: item[1].power, reverse=True)
        choices = sorted_moves[:2] if random.random() < 0.5 else sorted_moves
        if not choices: return 0
        
        chosen_index, _ = random.choice(choices)
        return chosen_index

    def build_sorted_turn_queue(self, player_move_idx):
        p_move = self.party.active.moves[player_move_idx]
        e_move_idx = self.choose_enemy_move_idx()
        e_move = self.enemy.moves[e_move_idx]

        p_act = {"who": "player", "move_obj": p_move, "priority": p_move.priority}
        e_act = {"who": "enemy", "move_obj": e_move, "priority": e_move.priority}

        # Priority check
        if p_act["priority"] != e_act["priority"]:
            return [p_act, e_act] if p_act["priority"] > e_act["priority"] else [e_act, p_act]

        # Speed check
        p_speed = self.party.active.get_stat("SPEED")
        e_speed = self.enemy.get_stat("SPEED")
        return [p_act, e_act] if p_speed >= e_speed else [e_act, p_act]

# list of (text, wait_frames)
    def add_message(self, text: str, wait=60):
         self.message_queue.append((text, wait))

    def use_item_on_mon(self, item_name, target):
        item_name = item_name.upper()
        if "REVIVE" in item_name:
            if target.is_fainted():
                target.hp = target.max_hp // 2
                return f"{target.name} was revived!"
        elif "FULL HEAL" in item_name:
            target.status = None
            return f"{target.name} was cured!"
        return f"{target.name} was healed!"
    
    def advance_message(self):
        if self.message_queue:
            self.message_queue.pop(0)

    def handle_submenu_option(self, option_idx, mon_idx):
        mon = self.party.pokemon[mon_idx]
        if option_idx == 0:  # SUMMARY
            self.add_message(f"Summary for {mon.name} (WIP)")
        elif option_idx == 1:  # SWITCH
            if mon.is_fainted():
                self.add_message("Can't switch to a fainted Pokémon!")
            else:
                self.party.active_idx = mon_idx
                self.add_message(f"Go! {mon.name}!")
                self.state_machine.set_state("MAIN")
        elif option_idx == 2:  # ITEM
            self.add_message("Use item on party (WIP)")
        elif option_idx == 3:  # CANCEL
            self.submenu_mon = None

    # [REF-0026c] Debug Tools
    def draw_debug_panel(self):
        panel_rect = pygame.Rect(WIDTH - 420, 20, 400, 280)
        pygame.draw.rect(self.screen, (40, 40, 40), panel_rect)
        pygame.draw.rect(self.screen, WHITE, panel_rect, 4)

        draw_text(self.screen, "DEBUG STATUS TEST (D to toggle)", FONT_UI, YELLOW, WIDTH - 220, 40)

        draw_text(self.screen, "PLAYER LEAD", FONT_UI, GREEN, WIDTH - 340, 80)
        p_name = self.party.active.name
        draw_text(self.screen, p_name, FONT_SMALL, WHITE, WIDTH - 340, 110)

        btns_p = []
        statuses = ["BRN", "PSN", "PAR", "SLP", "FRZ", "CONF", "TOX", "CLEAR"]
        cols = [RED, PURPLE, YELLOW, GRAY, CYAN, (255,165,0), PURPLE, WHITE]
        for i, st in enumerate(statuses):
            rect = pygame.Rect(WIDTH - 380, 140 + i*32, 120, 26)
            pygame.draw.rect(self.screen, cols[i], rect)
            pygame.draw.rect(self.screen, WHITE, rect, 2)
            draw_text(self.screen, st, FONT_SMALL, BLACK, rect.centerx, rect.centery)
            btns_p.append((rect, st))

        draw_text(self.screen, "ENEMY", FONT_UI, RED, WIDTH - 200, 80)
        e_name = self.enemy.name
        draw_text(self.screen, e_name, FONT_SMALL, WHITE, WIDTH - 200, 110)

        btns_e = []
        for i, st in enumerate(statuses):
            rect = pygame.Rect(WIDTH - 240, 140 + i*32, 120, 26)
            pygame.draw.rect(self.screen, cols[i], rect)
            pygame.draw.rect(self.screen, WHITE, rect, 2)
            draw_text(self.screen, st, FONT_SMALL, BLACK, rect.centerx, rect.centery)
            btns_e.append((rect, st))

        self.debug_btns_player = btns_p
        self.debug_btns_enemy = btns_e

    def handle_debug_click(self, pos):
        for rect, st in getattr(self, 'debug_btns_player', []):
            if rect.collidepoint(pos):
                if st == "CLEAR":
                    self.party.active.status = None
                    self.party.active.status_counter = 0
                else:
                    if st == "CONF":
                        self.volatile["player"]["confusion"] = random.randint(3, 5)
                    else:
                        self.party.active.apply_status(st)
                return

        for rect, st in getattr(self, 'debug_btns_enemy', []):
            if rect.collidepoint(pos):
                if st == "CLEAR":
                    self.enemy.status = None
                    self.enemy.status_counter = 0
                else:
                    if st == "CONF":
                        self.volatile["enemy"]["confusion"] = random.randint(3, 5)
                    else:
                        self.enemy.apply_status(st)
                return

    # [REF-0026d] Main Loop (Run)
    def run(self):
        """Fixed single event loop + proper rescue intro + clean exit + ESC to back out"""
        # === SETUP (before the loop) ===
        if not self.wild_music:
            sound_dir = os.path.join(ASSETS_DIR, "sounds")
            if os.path.exists(sound_dir):
                self.wild_music = [f for f in os.listdir(sound_dir) 
                                  if f.startswith("kanto_wild") and f.endswith(".ogg")]
        
        # Load battle background
        self.battle_bg = load_bg(random.choice(self.battle_bg_files), "pngs/battle") if self.battle_bg_files else None

        # === START INTRO ANIMATION ===
        if self.rescue_mode:
            self.intro_system.start_rescue_mode(self.party.active, self.enemy)
        else:
            self.intro_system.start(self.spr_player, self.party.active, self.enemy, self.trainer_system)

        # Music
        music_to_play = self.trainer_music if self.is_trainer else self.wild_music
        self.sound_manager.play_random_music(music_to_play)

        # ====================== MAIN BATTLE LOOP ======================
        while self.battle_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.battle_running = False
                    break
                
                # === ESC KEY TO GO BACK (prevents soft locks) ===
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state_name = self.state_machine.current_state.__class__.__name__
                    if state_name in ("SUMMARY", "PARTY", "BAG", "MOVES"):
                        self.state_machine.set_state("MAIN")
                        continue
                
                # Debug toggle
                if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                    self.debug_panel_visible = not self.debug_panel_visible
                
                if self.debug_panel_visible and event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_debug_click(event.pos)

                # Pass event to current state
                self.state_machine.handle_event(event)
            
            # Update and draw
            self.state_machine.update()
            self.state_machine.draw(self.screen)
            
            if self.debug_panel_visible:
                self.draw_debug_panel()
            
            pygame.display.flip()
            self.clock.tick(60)

        # Cleanup
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        print("♪ Battle music stopped")
        
        return {
            "result": "QUIT",
            "xp_gain": getattr(self.level_up_system, 'xp_gain', 0) if hasattr(self, 'level_up_system') else 0,
            "caught": getattr(self.catch_system, 'caught_mon', None) if hasattr(self, 'catch_system') and self.catch_system.caught else None
        }
    
    # [REF-0026e] Drawing (Scene)
    def draw_battle_scene(self, screen):
        """Always visible background (no more pure blue screen)"""
        if self.battle_bg:
            screen.blit(self.battle_bg, (0, 0))
        else:
            # Nice dark forest fallback so you always see SOMETHING
            screen.fill((25, 55, 25))
            pygame.draw.rect(screen, (139, 90, 43), (0, HEIGHT - 280, WIDTH, 80))

        # Bobbing + lunging animations
        self.anim_ctrl.update()
        bob = int(math.sin(pygame.time.get_ticks() / 200) * 4)

        # Player Pokémon
        if self.party.active.sprite:
            x_off = 30 if self.anim_ctrl.lunge_side == "player" and self.anim_ctrl.is_lunging else 0
            screen.blit(self.party.active.sprite, (PLAYER_POS[0] + x_off, PLAYER_POS[1]))

        # Enemy Pokémon
        if self.enemy.sprite and not self.enemy_fainted:
            x_off = -30 if self.anim_ctrl.lunge_side == "enemy" and self.anim_ctrl.is_lunging else 0
            screen.blit(self.enemy.sprite, (ENEMY_POS[0] + x_off, ENEMY_POS[1] + bob))

        # HP bars
        active = self.party.active
        p_status = {"condition": active.status, "counter": active.status_counter}
        draw_hp_bar(screen, PLAYER_HP_POS[0], PLAYER_HP_POS[1], active.hp, active.max_hp,
                    active.name, active.level, active.xp, active.xp_needed, status=p_status)
        draw_hp_bar(screen, ENEMY_HP_POS[0], ENEMY_HP_POS[1], self.enemy.hp, self.enemy.max_hp,
                    self.enemy.name, self.enemy.level, status={"condition": self.enemy.status})

# [REF-0027] OVERWORLD ENGINE (Movement)
class OverworldEngine:
    def __init__(self, screen, clock, data_manager, start_area="PALLET_TOWN"):
        self.screen = screen
        self.clock = clock
        self.data_manager = data_manager

        self.area = start_area.upper()
        self.player_x = WIDTH // 2
        self.player_y = HEIGHT // 2
        self.speed = 5

        # Load your town background
        bg_file = f"{self.area.lower()}.png"
        self.bg = load_bg(bg_file, "pngs/overworld") or pygame.Surface((WIDTH, HEIGHT))


        # Preload this zone so battles are instant
        self.data_manager.preload_zone(self.area)

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:  self.player_x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.player_x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:    self.player_y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:  self.player_y += self.speed

        self.player_x = max(30, min(WIDTH - 70, self.player_x))
        self.player_y = max(30, min(HEIGHT - 90, self.player_y))

    def draw(self):
        self.screen.blit(self.bg, (0, 0))

        self.screen.blit(self.player, (self.player_x, self.player_y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for rect, name in self.buildings:
                if rect.collidepoint(mx, my):
                    print(f"Clicked {name} — add your menu here later!")

def draw_character_select(screen, idx, name, trainers):
    # Classic Gameboy black text + retro font for name (as requested)
    draw_text(screen, "CHOOSE YOUR TRAINER", FONT_BIG, GB_TEXT, WIDTH//2, 80)
    char_img = trainers[idx]["front"]
    screen.blit(char_img, (WIDTH//2 - 192, HEIGHT//2 - 192))
    
    # Yellow clickable arrows
    left_rect = pygame.Rect(WIDTH//2 - 280, HEIGHT//2 - 60, 80, 120)
    right_rect = pygame.Rect(WIDTH//2 + 220, HEIGHT//2 - 60, 80, 120)
    
    pygame.draw.rect(screen, (255, 215, 0), left_rect, border_radius=12)
    pygame.draw.rect(screen, (255, 215, 0), right_rect, border_radius=12)
    
    draw_text(screen, "<", FONT_BIG, BLACK, left_rect.centerx, left_rect.centery)
    draw_text(screen, ">", FONT_BIG, BLACK, right_rect.centerx, right_rect.centery)
    
    # Name input box — GB black + retro font
    draw_text(screen, "ENTER NAME:", FONT_SMALL, GB_TEXT, WIDTH//2, HEIGHT - 210)
    name_box_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT - 180, 300, 40)
    pygame.draw.rect(screen, WHITE, name_box_rect, 2)
    display_name = (name if name else "") + "_"
    draw_text(screen, display_name, FONT_MSG, GB_TEXT, WIDTH//2, HEIGHT - 160)  # FONT_MSG = lucidaconsole (more GB retro)
    
    # Green SELECT button
    select_rect = pygame.Rect(WIDTH//2 - 200, HEIGHT - 130, 400, 60)
    pygame.draw.rect(screen, GREEN, select_rect, border_radius=10)
    draw_text(screen, "SELECT", FONT_SMALL, GB_TEXT, select_rect.centerx, select_rect.centery)
    
    return left_rect, right_rect, select_rect, name_box_rect

def draw_starter_select(screen, starter_ids, data_manager):
    draw_text(screen, "CHOOSE YOUR STARTER", FONT_BIG, WHITE, WIDTH//2, 80)
    rects = []
    for i, pid in enumerate(starter_ids):
        mon = Pokemon(pid, data_manager, BattleMechanics(), level=5)
        x = 100 + i * 210
        rect = pygame.Rect(x, HEIGHT//2 - 150, 180, 220)
        screen.blit(mon.sprite, (x + 20, HEIGHT//2 - 120))
        draw_text(screen, mon.name, FONT_UI, GOLD, rect.centerx, rect.bottom + 20)
        rects.append(rect)
    return rects

# [REF-0028] MAIN ENTRY
def standalone_main():
    global screen
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pokémath Adventures")
    clock = pygame.time.Clock()

    data_manager = DataManager()
    pool_system = WildPokemonPool()

    player_bag = Bag()

    overworld = OverworldManager(screen, clock, player_bag)

    # === CREATE REAL POKÉMON OBJECTS FOR OVERWORLD ===
    test_team_data = create_test_team(data_manager, 3)
    real_team = []
    mechanics = BattleMechanics()
    for p in test_team_data:
        mon = Pokemon(
            p["id"],
            data_manager,
            mechanics,
            level=p.get("level", 50),
            back_sprite=True
        )
        real_team.append(mon)

    overworld.player_party = Party(real_team)
    print(f"Party size: {len(overworld.player_party.pokemon)}")
    for mon in overworld.player_party.pokemon:
        print(f" - {mon.name} Lv.{mon.level}")

    # Music & backgrounds (shared across modes)
    sound_dir = os.path.join(ASSETS_DIR, "sounds")
    wild_music = [f for f in os.listdir(sound_dir) if f.startswith("kanto_wild") and f.endswith(".ogg")] or ["kanto_wild1.ogg"]
    trainer_music = [f for f in os.listdir(sound_dir) if f.startswith("kanto_trainer") and f.endswith(".ogg")] or ["kanto_trainer1.ogg"]
    battle_bg_files = [
        f for f in os.listdir(os.path.join(ASSETS_DIR, "pngs", "battle"))
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ] or ["TEST.png"]
    overworld.battle_bg_files = battle_bg_files
    print(f"✅ Loaded {len(battle_bg_files)} battle backgrounds for story mode")

    running = True
    current_state = STATE_SPLASH
    selecting_pool = False
    selected_pool = "RANDOM"
    in_overworld = False

    # Define all rects here so they're always available
    wild_rect    = pygame.Rect(WIDTH//2 - 280, 240, 560, 90)
    trainer_rect = pygame.Rect(WIDTH//2 - 280, 350, 560, 80)
    overworld_rect = pygame.Rect(WIDTH//2 - 280, 450, 560, 80)
    story_rect   = pygame.Rect(WIDTH//2 - 280, 550, 560, 80)   # ← added / fixed
    quit_rect    = pygame.Rect(WIDTH//2 - 100, 620, 200, 65)

    while running:
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                overworld.debug_mode = not overworld.debug_mode
                print(f"Debug mode: {'ON' if overworld.debug_mode else 'OFF'} (yellow rects)")
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if overworld.show_overlay:
                        overworld.show_overlay = None
            if event.type == pygame.MOUSEMOTION:
                # Only call if we're actually in overworld
                if in_overworld:
                    overworld.handle_mouse_motion(mx, my)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if not selecting_pool and not in_overworld:
                    # === SPLASH SCREEN clicks ===
                    if wild_rect.collidepoint(mx, my):
                        selecting_pool = True
                    elif trainer_rect.collidepoint(mx, my):
                        print("→ Starting TRAINER BATTLE")
                        player_party = create_test_team(data_manager, 3)
                        enemy_id = pool_system.get_random_id("RANDOM")
                        trainer_name = random.choice(["Youngster", "Lass", "Camper", "Picnicker", "Bug Catcher"])
                        engine = BattleEngine(
                            screen=screen,
                            clock=clock,
                            player_party=player_party,
                            enemy_id=enemy_id,
                            is_trainer=True,
                            trainer_name=trainer_name,
                            player_bag=player_bag,
                            battle_bg_files=battle_bg_files,
                            trainer_music=trainer_music,
                            use_cache_only=True
                        )
                if not selecting_pool and not in_overworld:
                    # === SPLASH SCREEN ===
                    if wild_rect.collidepoint(mx, my):
                        selecting_pool = True
                    elif trainer_rect.collidepoint(mx, my):
                        print("→ Starting TRAINER BATTLE")
                        player_party = create_test_team(data_manager, 3)
                        enemy_id = pool_system.get_random_id("RANDOM")
                        trainer_name = random.choice(["Youngster", "Lass", "Camper", "Picnicker", "Bug Catcher"])
                        engine = BattleEngine(screen, clock, player_party, enemy_id, is_trainer=True,
                                              trainer_name=trainer_name, battle_bg_files=battle_bg_files,
                                              player_bag=player_bag, trainer_music=trainer_music, use_cache_only=True)
                        engine.run()
                    elif overworld_rect.collidepoint(mx, my) or story_rect.collidepoint(mx, my):
                        print("→ Starting STORY MODE (Overworld / CYOA)")
                        in_overworld = True
                        current_state = STATE_CHAR_SELECT
                        if not hasattr(overworld, "selected_char_idx"):
                            overworld.selected_char_idx = 0
                        if not hasattr(overworld, "player_name"):
                            overworld.player_name = ""

                elif selecting_pool:
                    # === POOL SELECTION CLICK HANDLER (hyper-specific fix) ===
                    pools = pool_system.get_pools()
                    pool_buttons = []
                    for i, pool_name in enumerate(pools):
                        rect = pygame.Rect(WIDTH//2 - 250, 180 + i * 80, 500, 70)
                        pool_buttons.append((rect, pool_name))
                        if rect.collidepoint(mx, my):
                            selected_pool = pool_name
                            print(f"→ Starting WILD BATTLE in pool: {selected_pool}")
                            player_party = create_test_team(data_manager, 3)
                            enemy_id = pool_system.get_random_id(selected_pool)
                            engine = BattleEngine(screen, clock, player_party, enemy_id,
                                                  player_bag=player_bag,
                                                  battle_bg_files=battle_bg_files,
                                                  wild_music=wild_music,
                                                  use_cache_only=True)
                            engine.run()
                            selecting_pool = False
                            break

                    # BACK button
                    back_rect = pygame.Rect(50, HEIGHT - 100, 180, 60)
                    if back_rect.collidepoint(mx, my):
                        selecting_pool = False

                elif in_overworld:
                    overworld.handle_click(mx, my)

            # === TYPING + ARROWS + SELECT (correct level - runs every frame when on character screen) ===
            if current_state == STATE_CHAR_SELECT and hasattr(overworld, "char_select_arrow_rects"):
                left_rect, right_rect, select_rect, name_box_rect = overworld.char_select_arrow_rects
                
                # Mouse clicks for arrows and SELECT button
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if left_rect.collidepoint(mx, my):
                        overworld.selected_char_idx = (getattr(overworld, "selected_char_idx", 0) - 1) % len(overworld.available_trainers)
                    elif right_rect.collidepoint(mx, my):
                        overworld.selected_char_idx = (getattr(overworld, "selected_char_idx", 0) + 1) % len(overworld.available_trainers)
                    elif select_rect.collidepoint(mx, my):
                        # Allow clicking SELECT even if no name typed (defaults to TRAINER)
                        if not getattr(overworld, "player_name", "").strip():
                            overworld.player_name = "TRAINER"
                        random_starter_id = random.choice(KANTO_STARTERS)
                        starter_mon = Pokemon(random_starter_id, data_manager, BattleMechanics(), level=5, back_sprite=True)
                        overworld.player_party = Party([starter_mon])
                        print(f"→ Random starter assigned: {starter_mon.name}")
                        current_state = STATE_FIRST_BATTLE

                # KEYBOARD TYPING - runs every frame when on character select
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        overworld.player_name = overworld.player_name[:-1]
                    elif event.key == pygame.K_RETURN:
                        if not getattr(overworld, "player_name", "").strip():
                            overworld.player_name = "TRAINER"
                        random_starter_id = random.choice(KANTO_STARTERS)
                        starter_mon = Pokemon(random_starter_id, data_manager, BattleMechanics(), level=5, back_sprite=True)
                        overworld.player_party = Party([starter_mon])
                        current_state = STATE_FIRST_BATTLE
                    elif len(overworld.player_name) < 12 and event.unicode.isprintable():
                        overworld.player_name += event.unicode.upper()

                elif selecting_pool:
                    # === POOL SELECTOR (for quick wild testing) ===
                    for rect, pool_name in pool_buttons:
                        if rect.collidepoint(mx, my):
                            selected_pool = pool_name
                            print(f"→ Starting WILD BATTLE in {selected_pool}")
                            player_party = create_test_team(data_manager, 3)
                            enemy_id = pool_system.get_random_id(selected_pool)
                            engine = BattleEngine(screen, clock, player_party, enemy_id, player_bag=player_bag,
                                                  battle_bg_files=battle_bg_files,
                                                  wild_music=wild_music, use_cache_only=True)
                            engine.run()
                            selecting_pool = False
                            break
                    if back_rect.collidepoint(mx, my):
                        selecting_pool = False

# === DRAWING ===
        screen.fill(BLACK)

        if selecting_pool:
            # Pool selector screen (unchanged - for quick testing)
            draw_text(screen, "CHOOSE WILD AREA", FONT_BIG, GOLD, WIDTH // 2, 80)
            pools = pool_system.get_pools()
            pool_buttons = []
            for i, pool in enumerate(pools):
                rect = pygame.Rect(WIDTH//2 - 250, 200 + i * 75, 500, 65)
                pool_buttons.append((rect, pool))
                col = GREEN if rect.collidepoint(mx, my) else GB_PANEL
                pygame.draw.rect(screen, col, rect, border_radius=12)
                pygame.draw.rect(screen, WHITE, rect, 4, border_radius=12)
                draw_text(screen, pool, FONT_UI, BLACK, rect.centerx, rect.centery)
            back_rect = pygame.Rect(50, 650, 180, 60)
            pygame.draw.rect(screen, RED, back_rect, border_radius=12)
            draw_text(screen, "BACK", FONT_UI, WHITE, back_rect.centerx, back_rect.centery)

        elif current_state == STATE_CHAR_SELECT:
            # Load trainer assets once — using your exact folders (as you just told me)
            if not hasattr(overworld, "available_trainers"):
                trainer_filenames = [
                    "red_back.png", "ethan_back.png", "lyra_back.png", "brendan_back.png",
                    "may_back.png", "lucas_back.png", "dawn_back.png", "hilbert_back.png",
                    "hilda_back.png", "nate_back.png", "rosa_back.png", "blue_back.png"
                ]
                overworld.available_trainers = []
                for f in trainer_filenames:
                    # Back sprites → assets/sprites/trainers/back/
                    back = load_asset(f, "sprites/trainers/back", (384, 384))
                    front_f = f.replace("_back.png", ".png")
                    # Front sprites (for character selection) → assets/sprites/trainers/player/
                    front = load_asset(front_f, "sprites/trainers/player", (384, 384)) or back
                    overworld.available_trainers.append({"front": front, "back": back})
                if not hasattr(overworld, "selected_char_idx"):
                    overworld.selected_char_idx = 0
            
            # FIXED: now unpacks ALL 4 values returned by the function
            left_rect, right_rect, select_rect, name_box_rect = draw_character_select(screen, 
                overworld.selected_char_idx,
                getattr(overworld, "player_name", ""), 
                overworld.available_trainers)
            overworld.char_select_arrow_rects = (left_rect, right_rect, select_rect, name_box_rect)

            
        elif current_state == STATE_STARTER_SELECT:
            starter_rects = draw_starter_select(screen, KANTO_STARTERS, data_manager)

        elif current_state == STATE_FIRST_BATTLE:
            if not hasattr(overworld, 'poochyena_rescue'):
                overworld.poochyena_rescue = PoochyenaRescueBattle(screen, clock, overworld, data_manager)
            
            overworld.poochyena_rescue.run()
            
            print("✓ Poochyena rescue finished - returning to Pallet")
            in_overworld = True
            current_state = "OVERWORLD"
            overworld.current_area_name = "PALLET TOWN"
            overworld.current_screen = "city"
            overworld.enter_area("PALLET TOWN")
            overworld.refresh_menu_options()
            overworld.menu_active = True
            overworld.show_text("You made it back to Pallet Town safely!")

        elif in_overworld or current_state == "OVERWORLD":
            overworld.draw(screen)

        else:
            # Main splash screen (your original code — untouched)
            draw_text(screen, "POKÉMATH ADVENTURES", FONT_BIG, WHITE, WIDTH // 2, 100)
            draw_text(screen, "Select Battle Mode", FONT_MED, GOLD, WIDTH // 2, 180)

            wild_rect = pygame.Rect(WIDTH//2 - 280, 240, 560, 90)
            trainer_rect = pygame.Rect(WIDTH//2 - 280, 350, 560, 80)
            overworld_rect = pygame.Rect(WIDTH//2 - 280, 450, 560, 80)
            quit_rect = pygame.Rect(WIDTH//2 - 100, 620, 200, 65)
            story_rect = pygame.Rect(WIDTH//2 - 280, 550, 560, 80)

            pygame.draw.rect(screen, GREEN if wild_rect.collidepoint(mx,my) else DARK_GREEN, wild_rect, border_radius=15)
            draw_text(screen, "WILD BATTLE", FONT_UI, WHITE, wild_rect.centerx, wild_rect.centery)

            pygame.draw.rect(screen, BLUE if trainer_rect.collidepoint(mx,my) else (30,30,180), trainer_rect, border_radius=15)
            draw_text(screen, "TRAINER BATTLE", FONT_UI, WHITE, trainer_rect.centerx, trainer_rect.centery)

            pygame.draw.rect(screen, (0,200,100) if overworld_rect.collidepoint(mx,my) else (0,150,80), overworld_rect, border_radius=15)
            draw_text(screen, "OVERWORLD", FONT_UI, WHITE, overworld_rect.centerx, overworld_rect.centery)

            pygame.draw.rect(screen, (255,215,0) if story_rect.collidepoint(mx,my) else (200,150,0), story_rect, border_radius=15)
            draw_text(screen, "STORY MODE", FONT_UI, BLACK, story_rect.centerx, story_rect.centery)

            pygame.draw.rect(screen, RED, quit_rect, border_radius=12)
            draw_text(screen, "QUIT", FONT_UI, WHITE, quit_rect.centerx, quit_rect.centery)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


# Helper to create a team of 3 random Pokémon (unchanged from your original)
def create_test_team(dm, num=3):
    team = []
    used = set()
    for _ in range(num):
        pid = dm.get_random_pokemon_id(exclude_id=list(used) if used else None)
        used.add(pid)
        team.append({"id": pid, "level": 50, "is_shiny": random.random() < 0.1})
    return team

if __name__ == "__main__":
    standalone_main()