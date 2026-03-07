import pygame
import random
import requests
import io
import os
import math
from abc import ABC, abstractmethod   # for future clean state machine (optional)
import json
import threading

# [REF-0001] Imports & System Initialization
# Sets up Pygame, Mixer, and basic window configuration.
pygame.mixer.pre_init(44100, -16, 2, 4096)
pygame.init()
pygame.mixer.init()

# [REF-0002] Constants & Configuration
WIDTH, HEIGHT = 1024, 768

# [REF-0003] Colors & Fonts
WHITE, BLACK = (255, 255, 255), (10, 10, 10)
GREEN, RED, YELLOW, GOLD = (50, 255, 50), (255, 50, 50), (255, 255, 0), (255, 215, 0)
DARK_GREEN, GRAY, BLUE = (34, 139, 34), (50, 50, 50), (50, 50, 255)
PURPLE, CYAN, ORANGE = (128, 0, 128), (0, 255, 255), (255, 165, 0)
HP_GREEN, HP_YELLOW, HP_RED = (112, 248, 168), (248, 224, 56), (248, 88, 56)

# ── CLASSIC HANDHELD PALETTE (Gen 1–5 Game Boy / GBC / GBA feel) ──
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

# [REF-0004] Asset Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# [REF-0004b] Cache Configuration (Phase 3)
CACHE_DIR = os.path.join(BASE_DIR, "cache")
POKEMON_CACHE_DIR = os.path.join(CACHE_DIR, "pokemon")
os.makedirs(POKEMON_CACHE_DIR, exist_ok=True)

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
    img = load_asset(filename, subfolder)
    if img:
        scale = WIDTH / img.get_width()
        new_h = int(img.get_height() * scale)
        return pygame.transform.scale(img, (WIDTH, new_h))  # keeps aspect ratio
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

# [REF-0008] Classic Menu Panels
def draw_classic_panel(screen, x, y, w, h, title=None):
    pygame.draw.rect(screen, GB_BORDER, (x - 8, y - 8, w + 16, h + 16))
    pygame.draw.rect(screen, GB_PANEL, (x, y, w, h))
    pygame.draw.rect(screen, GB_PANEL_DARK, (x, y, w, h), 6)
    pygame.draw.rect(screen, GB_HIGHLIGHT, (x + 6, y + 6, w - 12, 3))
    if title:
        draw_text(screen, title, FONT_UI, GB_TEXT, x + w // 2, y + 22)

# [REF-0009] HP Bar Drawer
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

# [REF-0010] Bag & Party UI Drawers
def draw_bag_menu(screen, bag_pocket, bag_cursor, player_bag, trainer_name):
    draw_classic_panel(screen, 20, 80, 300, 520, "BAG")
    for i, pocket in enumerate(POCKET_NAMES):
        col = GB_TEXT if i == bag_pocket else GRAY
        draw_text(screen, pocket, FONT_UI, col, 60, 140 + i * 80, center=False)
    pocket_key = ["items", "pokeballs", "key_items"][bag_pocket]
    items = player_bag[pocket_key]
    panel_x = 340
    panel_y = 130 + bag_pocket * 80
    panel_w = 400
    panel_h = max(100, len(items) * 45 + 40)
    draw_classic_panel(screen, panel_x, panel_y, panel_w, panel_h)
    for i, item in enumerate(items):
        y = panel_y + 30 + i * 45
        text = f"{item['name']}  x{item['qty']}"
        draw_text(screen, text, FONT_UI, GB_TEXT, panel_x + 30, y, center=False)
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

# [REF-0011] BATTLE MECHANICS CLASS
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

    def calc_hp(self, base_hp: int, level: int) -> int:
        return ((2 * base_hp + 31) * level // 100) + level + 10

    def calc_stat(self, base: int, level: int) -> int:
        return ((2 * base + 31) * level // 100) + 5

    def get_type_multiplier(self, move_type: str, target_types: list) -> float:
        mult = 1.0
        for t in target_types:
            mult *= self.type_chart.get(move_type, {}).get(t, 1.0)
        return mult

    def calculate_damage(self, attacker, defender, move, math_boost=1.0):

        is_crit = random.random() < (1 / 24)
        crit_mult = 1.5 if is_crit else 1.0

        atk_stat_name = "ATTACK" if move.category == "physical" else "SPATK"
        atk = attacker.get_stat(atk_stat_name)
        atk *= self.stage_multipliers[attacker.stage_manager.get_stage(
            "attack" if move.category == "physical" else "sp_atk") + 6]

        def_stat_name = "DEFENSE" if move.category == "physical" else "SPDEF"
        if is_crit:
            dfn = defender.get_stat(def_stat_name)
        else:
            dfn = defender.get_stat(def_stat_name)
            dfn *= self.stage_multipliers[defender.stage_manager.get_stage(
                "defense" if move.category == "physical" else "sp_def") + 6]

        level_calc = (2 * attacker.level / 5) + 2
        base_damage = ((level_calc * move.power * (atk / dfn)) / 50) + 2

        stab = 1.5 if move.type in attacker.types else 1.0
        type_mult = self.get_type_multiplier(move.type, defender.types)
        variance = random.uniform(0.85, 1.0)
        burn_penalty = 0.5 if (attacker.status == "BRN" and move.category == "physical") else 1.0

        final = int(base_damage * stab * type_mult * crit_mult * variance * burn_penalty * math_boost)
        return max(1, final) if type_mult > 0 else 0, is_crit

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

# [REF-0012] DATA MANAGER CLASS — Phase 3 (Local JSON Caching + Async + Sprite Batching)
class DataManager:
    """Handles API fetching, local JSON caching, async loads, and pre-loaded UI assets."""
    def __init__(self):
        self.POKEMON_CACHE = {}
        self.BALL_CACHE = {}
        self.BALL_SPRITE_URLS = {
            "poké ball":  "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png",
            "great ball": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/great-ball.png",
            "ultra ball": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/ultra-ball.png",
            "master ball": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/master-ball.png",
        }

        # === ROBUST SESSION (fixes SSL / EOF / rate-limit errors) ===
        self.session = requests.Session()
        retry = requests.adapters.Retry(total=6, backoff_factor=1.2, status_forcelist=[429, 500, 502, 503, 504])
        adapter = requests.adapters.HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Phase 3: Sprite Batching - Pre-load common UI elements
        self.preload_ui()

    def preload_ui(self):
        self.ui_assets = {
            "hp_bar_bg": pygame.Surface((250, 12)),
            "panel": pygame.Surface((300, 160)),
        }

    # [REF-0012a] Utility: Random Pokémon ID (used in create_test_team and splash screen)
    def get_random_pokemon_id(self, exclude_id=None, max_id=151):
        while True:
            pid = random.randint(1, max_id)
            if exclude_id is None or pid != exclude_id:
                return pid

    # Cache helpers
    def _cache_path(self, poke_id, back, level):
        return os.path.join(POKEMON_CACHE_DIR, f"{poke_id}_{'back' if back else 'front'}_lv{level}.json")

    def _save_to_cache(self, poke_id, back, level, data):
        path = self._cache_path(poke_id, back, level)
        try:
            with open(path, "w") as f:
                json.dump(data, f)
        except:
            pass

    def _load_from_cache(self, poke_id, back, level):
        path = self._cache_path(poke_id, back, level)
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except:
                pass
        return None
    
    # Async
    def async_fetch_pokemon(self, poke_id, back=False, level=50, callback=None):
        def worker():
            result = self.fetch_pokemon_data(poke_id, back, level)
            if callback:
                pygame.event.post(pygame.event.Event(pygame.USEREVENT, {"result": result, "callback": callback}))
        threading.Thread(target=worker, daemon=False).start()

    def preload_zone(self, pool_name: str, level=50):
        ids = self._get_zone_ids(pool_name)
        print(f"Preloading zone {pool_name} — {len(ids)} Pokémon...")
        for pid in ids:
            self.async_fetch_pokemon(pid, back=False, level=level)
            self.async_fetch_pokemon(pid, back=True, level=level)

    def _get_zone_ids(self, pool_name):
        if pool_name == "RANDOM":
            return list(range(1, 152))
        pool = WildPokemonPool()
        return pool.pools.get(pool_name, list(range(1, 152)))

    # === CLEAN FETCH ===
    def fetch_pokemon_data(self, poke_id, back=False, level=10):
        key = (poke_id, back, level)
        if key in self.POKEMON_CACHE:
            return self.POKEMON_CACHE[key]

        cached = self._load_from_cache(poke_id, back, level)
        if cached:
            return self._rebuild_from_cache(cached, poke_id, back, level)

        try:
            url = f"https://pokeapi.co/api/v2/pokemon/{poke_id}"
            response = self.session.get(url, timeout=12).json()

            name = response["name"].upper()
            types = [t["type"]["name"].upper() for t in response["types"]]
            stats = {}
            for stat in response["stats"]:
                sname = stat["stat"]["name"].upper()
                if sname == "SPECIAL-ATTACK": sname = "SPATK"
                elif sname == "SPECIAL-DEFENSE": sname = "SPDEF"
                stats[sname] = stat["base_stat"]

            # Sprite
            sprite_key = "back_default" if back else "front_default"
            sprite_url = response["sprites"][sprite_key]
            img_resp = self.session.get(sprite_url, timeout=8).content
            image = pygame.image.load(io.BytesIO(img_resp)).convert_alpha()
            image = pygame.transform.scale(image, (BATTLE_SCALE, BATTLE_SCALE))

            base_xp = response.get("base_experience", 64)

            # Moves logic
            versions = ["scarlet-violet", "sword-shield", "ultra-sun-ultra-moon", "sun-moon", 
                        "omega-ruby-alpha-sapphire", "x-y", "black-2-white-2", "black-white", 
                        "heartgold-soulsilver", "platinum", "diamond-pearl", "emerald", 
                        "firered-leafgreen", "ruby-sapphire", "crystal", "gold-silver", "yellow", "red-blue"]
            move_pool = {}
            for version in versions:
                for move_entry in response["moves"]:
                    for vgd in move_entry["version_group_details"]:
                        if (vgd["move_learn_method"]["name"] == "level-up" and
                            vgd["level_learned_at"] <= level and
                            vgd["version_group"]["name"] == version):
                            m_url = move_entry["move"]["url"]
                            if m_url not in move_pool: move_pool[m_url] = None
                            break
                if len(move_pool) >= 15: break

            # (the rest of your move processing code stays exactly the same — I kept it short for clarity) ##GROK PLEASE EXPAND THE MOVE PROCESSING CODE##
            all_moves = []
            for m_url in move_pool:
                try:
                    move_resp = requests.get(m_url).json()
                    power = move_resp["power"] or 0
                    mtype = move_resp["type"]["name"].upper()
                    accuracy = move_resp["accuracy"] or 100
                    category = move_resp["damage_class"]["name"]
                    m_name = move_resp["name"].upper()
                    priority = move_resp.get("priority", 0)
                    effect_chance = move_resp.get("effect_chance") or 0
                    meta = move_resp.get("meta", {})
                    ailment = meta.get("ailment", {}).get("name") if meta.get("ailment") else None
                    is_inflicter = (power == 0 and ailment and ailment != "none" and 
                                    ailment in ["paralysis", "burn", "poison", "toxic", "sleep", "freeze", "confusion"])
                    secondary = []
                    if meta.get("ailment"):
                        secondary.append({"type": "ailment", "ailment": meta["ailment"]["name"].upper(), "chance": meta.get("ailment_chance", 0)})
                    if meta.get("flinch_chance"):
                        secondary.append({"type": "flinch", "chance": meta["flinch_chance"]})
                    for sc in meta.get("stat_changes", []):
                        stat_name = sc.get("stat", {}).get("name", "").lower()
                        stages = sc.get("change", 0)
                        if stat_name and stages != 0:
                            secondary.append({
                                "type": "stat_change",
                                "stat": stat_name,
                                "stages": stages,
                                "chance": meta.get("stat_chance", 100)
                            })
                    all_moves.append({
                        "name": m_name, "power": power, "type": mtype, "accuracy": accuracy,
                        "category": category, "effect_chance": effect_chance, "is_inflicter": is_inflicter,
                        "ailment": ailment, "secondary": secondary, "priority": priority,
                        "ohko": move_resp.get("meta", {}).get("ailment") == "ohko",
                        "self_faint": (m_name in ["SELFDESTRUCT", "EXPLOSION"] or 
                                      move_resp.get("meta", {}).get("drain", 0) < -20)
                    })
                except: continue

            # Your existing move selection logic (stab, coverage, etc.) — keep exactly as you had it
            stab_moves = [m for m in all_moves if m["power"] > 0 and m["type"] in types]
            coverage_moves = [m for m in all_moves if m["power"] > 0 and m["type"] not in types]
            status_inflicters = [m for m in all_moves if m["is_inflicter"]]
            stab_moves.sort(key=lambda m: m["power"], reverse=True)
            coverage_moves.sort(key=lambda m: m["power"], reverse=True)
            status_inflicters.sort(key=lambda m: m["effect_chance"], reverse=True)

            moves_list = []
            if len(types) == 2:
                type1, type2 = types
                stab1 = [m for m in stab_moves if m["type"] == type1]
                stab2 = [m for m in stab_moves if m["type"] == type2]
                if stab1: moves_list.append(stab1[0])
                if stab2 and len(moves_list) < 2: moves_list.append(stab2[0])
            else:
                moves_list.extend(stab_moves[:2])
            while len(moves_list) < 3 and coverage_moves:
                next_cov = next((m for m in coverage_moves if m["name"] not in [mm["name"] for mm in moves_list]), None)
                if next_cov:
                    moves_list.append(next_cov)
                    coverage_moves = [c for c in coverage_moves if c["name"] != next_cov["name"]]
            if status_inflicters and len(moves_list) < 4:
                status_to_add = next((s for s in status_inflicters if s["name"] not in [m["name"] for m in moves_list]), status_inflicters[0])
                moves_list.append(status_to_add)
            while len(moves_list) < 4 and (coverage_moves or stab_moves):
                remaining = coverage_moves + stab_moves
                remaining.sort(key=lambda m: m["power"], reverse=True)
                next_m = next((m for m in remaining if m["name"] not in [mm["name"] for mm in moves_list]), None)
                if next_m: moves_list.append(next_m)
            while len(moves_list) < 4:
                moves_list.append({"name": "TACKLE", "power": 40, "type": "NORMAL", "accuracy": 100, "category": "physical", "secondary": []})
            moves_list = moves_list[:4]

            # Cry
            cry_sound = None
            try:
                cry_url = response["cries"]["latest"]
                cry_sound = pygame.mixer.Sound(io.BytesIO(self.session.get(cry_url, timeout=6).content))
            except:
                pass

            # Capture rate
            species_url = f"https://pokeapi.co/api/v2/pokemon-species/{poke_id}"
            species_resp = self.session.get(f"https://pokeapi.co/api/v2/pokemon-species/{poke_id}", timeout=6).json()
            capture_rate = species_resp.get("capture_rate", 45)
            result = image, name, moves_list, base_xp, types, stats, cry_sound, capture_rate
            cache_data = {"name": name, "types": types, "stats": stats, "base_xp": base_xp,
                          "capture_rate": capture_rate, "moves": moves_list}
            self._save_to_cache(poke_id, back, level, cache_data)

            self.POKEMON_CACHE[key] = result
            return result

        except Exception as e:
            print(f"Network error for Pokémon {poke_id}: {e}")
            fallback_img = pygame.Surface((BATTLE_SCALE, BATTLE_SCALE))
            fallback_img.fill(GRAY)
            fallback_moves = [{"name": "TACKLE", "power": 40, "type": "NORMAL", "accuracy": 100, "category": "physical", "secondary": []}] * 4
            result = fallback_img, f"POKÉ {poke_id}", fallback_moves, 64, ["NORMAL"], {"HP":50,"ATTACK":50,"DEFENSE":50,"SPATK":50,"SPDEF":50,"SPEED":50}, None, 45
            self.POKEMON_CACHE[key] = result
            return result

    def _rebuild_from_cache(self, cached, poke_id, back, level):
        """Safe rebuild from cache"""
        name = cached["name"]
        types = cached["types"]
        stats = cached["stats"]
        base_xp = cached["base_xp"]
        capture_rate = cached["capture_rate"]
        moves_list = cached["moves"]

        image = None
        try:
            url = f"https://pokeapi.co/api/v2/pokemon/{poke_id}"
            resp = self.session.get(url, timeout=8)
            response = resp.json() if resp.status_code == 200 else {}
            sprite_key = "back_default" if back else "front_default"
            sprite_url = response.get("sprites", {}).get(sprite_key)
            if sprite_url:
                img_resp = self.session.get(sprite_url, timeout=8).content
                image = pygame.image.load(io.BytesIO(img_resp)).convert_alpha()
                image = pygame.transform.scale(image, (BATTLE_SCALE, BATTLE_SCALE))
        except Exception as e:
            print(f"Sprite fetch failed for #{poke_id}: {e}")

        if image is None:
            image = pygame.Surface((BATTLE_SCALE, BATTLE_SCALE))
            image.fill(GRAY)

        # === SAFE CRY FETCH ===
        cry_sound = None
        try:
            cry_url = response.get("cries", {}).get("latest")
            if cry_url:
                cry_resp = self.session.get(cry_url, timeout=6).content
                cry_sound = pygame.mixer.Sound(io.BytesIO(cry_resp))
        except:
            pass

        return image, name, moves_list, base_xp, types, stats, cry_sound, capture_rate

    # [REF-0012b] Sprite Loading
    def load_ball_sprite(self, ball_name: str):
        """Load and cache ball sprites (used by IntroSystem and CatchSystem)"""
        key = ball_name.lower().strip()
        if key in self.BALL_CACHE:
            return self.BALL_CACHE[key]

        url = self.BALL_SPRITE_URLS.get(key) or self.BALL_SPRITE_URLS["poké ball"]
        try:
            resp = requests.get(url, timeout=4)
            img = pygame.image.load(io.BytesIO(resp.content)).convert_alpha()
            surf = pygame.transform.scale(img, (64, 64))
            self.BALL_CACHE[key] = surf
            return surf
        except:
            # Fallback ball sprite
            surf = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.circle(surf, (230, 40, 40), (32, 32), 28)
            pygame.draw.circle(surf, (255, 255, 255), (32, 32), 28, 6)
            pygame.draw.circle(surf, (0, 0, 0), (32, 32), 12)
            return surf

    def download_all_sprites(self, progress_callback=None):
        """One-time download of all 151 Gen 1 sprites (front + back)"""
        print("Downloading all Gen 1 Pokémon sprites (one-time)...")
        for pid in range(252, 1027):
            for back in [False, True]:
                key = (pid, back, 50)
                if key in self.POKEMON_CACHE:
                    continue

                try:
                    url = f"https://pokeapi.co/api/v2/pokemon/{pid}"
                    data = self.session.get(url, timeout=10).json()
                    sprite_key = "back_default" if back else "front_default"
                    sprite_url = data["sprites"][sprite_key]
                    if not sprite_url:
                        continue

                    img_data = self.session.get(sprite_url, timeout=10).content
                    folder = "back" if back else "front"
                    path = os.path.join(ASSETS_DIR, "sprites", "pokemon", folder, f"{pid:03d}.png")
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "wb") as f:
                        f.write(img_data)

                    if progress_callback:
                        progress_callback(pid, 1026)
                    print(f"Downloaded #{pid:03d} {'back' if back else 'front'}")
                except:
                    print(f"Skipped #{pid:03d}")
                    continue
        print("All sprites downloaded!")

    # [REF-0012d] Fetch New Moves (Level Up) — NOW CONSISTENT WITH MAIN FETCH
    def fetch_new_moves(self, poke_id, level):
        try:
            url = f"https://pokeapi.co/api/v2/pokemon/{poke_id}"
            response = requests.get(url).json()
            new_moves = []
            for move_entry in response["moves"]:
                for vgd in move_entry["version_group_details"]:
                    if (vgd["move_learn_method"]["name"] == "level-up" and
                        vgd["level_learned_at"] == level and
                        vgd["version_group"]["name"] == "scarlet-violet"):
                        move_url = move_entry["move"]["url"]
                        move_resp = requests.get(move_url).json()

                        power = move_resp["power"] or 0
                        mtype = move_resp["type"]["name"].upper()
                        accuracy = move_resp["accuracy"] or 100
                        category = move_resp["damage_class"]["name"]
                        m_name = move_resp["name"].upper()
                        priority = move_resp.get("priority", 0)
                        meta = move_resp.get("meta", {})
                        ailment = meta.get("ailment", {}).get("name") if meta.get("ailment") else None
                        is_inflicter = (power == 0 and ailment and ailment in ["paralysis", "burn", "poison", "toxic", "sleep", "freeze", "confusion"])

                        secondary = []
                        if meta.get("ailment"):
                            secondary.append({
                                "type": "ailment",
                                "ailment": meta["ailment"]["name"].upper(),
                                "chance": meta.get("ailment_chance", 0)
                            })
                        if meta.get("flinch_chance"):
                            secondary.append({
                                "type": "flinch",
                                "chance": meta["flinch_chance"]
                            })

                        for sc in meta.get("stat_changes", []):
                            stat_name = sc.get("stat", {}).get("name", "").lower()
                            stages = sc.get("change", 0)
                            if stat_name and stages != 0:
                                secondary.append({
                                    "type": "stat_change",
                                    "stat": stat_name,
                                    "stages": stages,
                                    "chance": meta.get("stat_chance", 100)
                                })

                        new_moves.append({
                            "name": m_name,
                            "power": power,
                            "type": mtype,
                            "accuracy": accuracy,
                            "category": category,
                            "is_inflicter": is_inflicter,
                            "ailment": ailment,
                            "secondary": secondary,
                            "priority": priority,
                            "ohko": move_resp.get("meta", {}).get("ailment") == "ohko",
                            "self_faint": (m_name in ["SELFDESTRUCT", "EXPLOSION"] or 
                                          move_resp.get("meta", {}).get("drain", 0) < -20),
                        })
                        break
            return new_moves
        except Exception as e:
            print(f"Error fetching new moves for Pokemon {poke_id}: {e}")
            return []

# [REF-0013] CORE DATA CLASSES (Move, Pokemon, Party, Bag)
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

class Pokemon:
    def __init__(self, poke_id, data_manager, mechanics, level=50, back_sprite=True):
        self.mechanics = mechanics
        image, name, moves_list, base_xp, types, stats, cry_sound, capture_rate = data_manager.fetch_pokemon_data(poke_id, back=back_sprite, level=level)
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

        self.max_hp = mechanics.calc_hp(stats["HP"], level)
        self.hp = self.max_hp

        self.xp = 0
        self.xp_needed = max(100, int(100 * (1.25 ** (level - 1))) + 30)
        self.status = None
        self.status_counter = 0
        self.volatile = {}
        self.stage_manager = StageManager()

    # NEW: Check local sprite first (instant + offline)
        folder = "back" if back_sprite else "front"
        local_path = os.path.join(ASSETS_DIR, "sprites", "pokemon", folder, f"{poke_id:03d}.png")
        
        if os.path.exists(local_path):
            image = pygame.image.load(local_path).convert_alpha()
            image = pygame.transform.scale(image, (BATTLE_SCALE, BATTLE_SCALE))
            # Still get the rest from cache/API (name, moves, stats, etc.)
            _, name, moves_list, base_xp, types, stats, cry_sound, capture_rate = data_manager.fetch_pokemon_data(poke_id, back=back_sprite, level=level)
        else:
            # Fall back to normal fetch (will also download it)
            image, name, moves_list, base_xp, types, stats, cry_sound, capture_rate = data_manager.fetch_pokemon_data(poke_id, back=back_sprite, level=level)

        # === FRONT SPRITE FOR SUB-MENU (always front view) ===
        front_image, _, _, _, _, _, _, _ = data_manager.fetch_pokemon_data(poke_id, back=False, level=level)
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

class Bag:
    """Simple bag wrapper"""
    def __init__(self):
        self.pockets = {
            "items": [{"name": "POTION", "qty": 10},{"name": "SUPER POTION", "qty": 5},{"name": "FULL HEAL", "qty": 3},{"name": "REVIVE", "qty": 2}],
            "pokeballs": [{"name": "POKÉ BALL", "qty": 15},{"name": "GREAT BALL", "qty": 8},{"name": "ULTRA BALL", "qty": 3},{"name": "MASTER BALL", "qty": 1}],
            "key_items": [{"name": "OLD ROD", "qty": 1},{"name": "TOWN MAP", "qty": 1}]
        }

# [REF-0014] TRAINER SYSTEM
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
                elif isinstance(p, dict): pokemon_list.append(Pokemon(p.get("id", 1), data_manager, mechanics, p.get("level", 50), back_sprite=False))
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

# [REF-0015] SOUND MANAGER
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

# [REF-0016] MATH SYSTEM
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

# [REF-0017] WILD POKEMON POOL CLASS
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

# [REF-0018] LEVEL UP SYSTEM
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
            new_moves = self.engine.data_manager.fetch_new_moves(active.id, active.level)
            if new_moves:
                self.engine.moves_to_learn = new_moves
                next_state = "LEARN_MOVE"
                
        return next_state

# [REF-0019] ANIMATION CONTROLLER
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

# [REF-0020] TURN PROCESSOR
class TurnProcessor:
    def __init__(self, engine):
        self.engine = engine

    def update(self):
        if self.engine.message_queue:          # let player read messages
            self.engine.message_queue[0] = (self.engine.message_queue[0][0], self.engine.message_queue[0][1]-1)
            if self.engine.message_queue[0][1] <= 0:
                self.engine.advance_message()
            return "WAIT"

        if not self.engine.turn_queue:
            return "NEXT_TURN"

        act = self.engine.turn_queue[0]
        
        # ===== 2. PRE-TURN STATUS GATEKEEPER =====
        mon = self.engine.party.active if act["who"] == "player" else self.engine.enemy
        if self._handle_pre_turn_status(mon, act["who"]):
            self.engine.turn_queue.pop(0)   # action consumed, no move executed
            return "ACTION"

        # ===== EXECUTE MOVE =====
        move = act["move_obj"]
        math_boost = 1.2 if random.random() < 0.7 else 0.8   # example
        feedback, dmg, crit, secondary = move.execute(mon, self.engine.enemy if act["who"]=="player" else self.engine.party.active, self.engine, math_boost)

        self.engine.add_message(feedback)
        self.engine.anim_ctrl.start_lunge(act["who"])

        # ===== 3. POST-MOVE SECONDARY EFFECTS =====
        self._process_secondary(secondary, mon, self.engine.enemy if act["who"]=="player" else self.engine.party.active, act["who"])

        # SAFE POP + immediate message flush (fixes delayed text, sleep, faint, explosion)
        if self.engine.turn_queue:
            self.engine.turn_queue.pop(0)

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

    # ===== 4. END-OF-TURN RESIDUALS (called after queue empty) =====
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

# [REF-0021] BATTLE STATE MACHINE & STATES
# [REF-0021a] Base State
class BattleState(ABC):
    def __init__(self, engine):
        self.engine = engine
    def update(self): pass
    def draw(self, screen): pass
    def handle_event(self, event): pass

# [REF-0021b] Loading & Intro States
class LoadingState(BattleState):
    def update(self):
        self.engine.state_machine.set_state("INTRO")
    def draw(self, screen):
        screen.fill(BLACK)
        draw_text(screen, "LOADING BATTLE...", FONT_MED, WHITE, WIDTH // 2, HEIGHT // 2)

class IntroState(BattleState):
    def update(self):
        self.engine.intro_system.update()
        if self.engine.intro_system.finished:
            # FIXED: Use a safe default BP instead of level
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

# [REF-0021c] Main Menu State
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
                            self.engine.state_machine.set_state("TURN")
                        else:
                            self.engine.add_message("Can't escape!")
                            e_act = self.engine.create_act("enemy", self.engine.choose_enemy_move_idx())
                            self.engine.turn_queue = [e_act]
                            self.engine.state_machine.set_state("TURN")

# [REF-0021d] Move Selection State
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

# [REF-0021e] Math Problem State
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

# [REF-0021f] Bag State
class BagState(BattleState):
    def draw(self, screen):
        self.engine.draw_battle_scene(screen)
        draw_bag_menu(screen, self.engine.bag_pocket, self.engine.bag_cursor, self.engine.bag.pockets, self.engine.trainer_name)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i in range(3):
                if 140 + i * 80 <= event.pos[1] <= 140 + i * 80 + 60 and 30 <= event.pos[0] <= 300:
                    self.engine.bag_pocket = i
                    self.engine.bag_cursor = 0
                    return
            pocket_key = ["items", "pokeballs", "key_items"][self.engine.bag_pocket]
            items = self.engine.bag.pockets[pocket_key]
            panel_x, panel_y = 340, 130 + self.engine.bag_pocket * 80
            for i, item in enumerate(items):
                y = panel_y + 30 + i * 45
                if panel_x <= event.pos[0] <= panel_x + 400 and y <= event.pos[1] <= y + 40:
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
                            else:
                                self.engine.add_message(f"Used {item['name']}!")
                                e_act = self.engine.create_act("enemy", self.engine.choose_enemy_move_idx())
                                self.engine.turn_queue = [e_act]
                                self.engine.state_machine.set_state("TURN")
                    return
            if HEIGHT - 90 <= event.pos[1] <= HEIGHT - 30 and WIDTH//2 - 100 <= event.pos[0] <= WIDTH//2 + 100:
                self.engine.state_machine.set_state(self.engine.bag_return_state or 'MAIN')

# [REF-0021g] Turn Execution State
class TurnState(BattleState):
    def update(self):
        self.engine.anim_ctrl.update()
        result = self.engine.turn_processor.update()
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

# [REF-0021h] Catch & Victory States
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

# [REF-0021j] Party State (Interactive Switching)
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
                        return

class LearnMoveState(BattleState):
    def draw(self, screen):
        self.engine.draw_battle_scene(screen)
        draw_classic_panel(screen, 20, HEIGHT - 180, WIDTH - 40, 160)
        draw_multiline_text(screen, "Learned new moves! (Feature WIP)", FONT_MSG, GB_TEXT, WIDTH // 2, HEIGHT - 100, WIDTH - 100)
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.engine.state_machine.set_state("VICTORY")

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

# [REF-0021i] State Machine Manager
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

# [REF-0022] VISUAL SYSTEMS (Intro, Catch, Faint)
# [REF-0022a] Intro Animation System
class IntroSystem:
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
        self.ball_sprite = self.data_manager.load_ball_sprite("poké ball")
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
        
        if self.phase == 0: # Slide in
            self.trainer_x = min(PLAYER_POS[0] - 90, self.trainer_x + 19)
            self.enemy_x = max(ENEMY_POS[0], self.enemy_x - 24)
            if self.trainer_x >= PLAYER_POS[0] - 90 and self.enemy_x <= ENEMY_POS[0] + 15:
                self.phase = 1
                self.flash_timer = 8
                if self.enemy_mon.cry:
                    try: self.enemy_mon.cry.play()
                    except: pass
        elif self.phase == 1: # Wild appeared text
            if self.trainer_system:
                self._update_text(f"{self.trainer_system.name} wants to battle!")
            else:
                self._update_text(f"A wild {self.enemy_mon.name} appeared!")
            if self.text_done and self.anim_timer > 300: self.advance() # Auto advance
        elif self.phase == 1.5: # Throw Ball
            if self.trainer_system and not self.trainer_slide_out:
                self.enemy_x += 24
                if self.enemy_x > WIDTH:
                    self.trainer_slide_out = True
                    self.enemy_x = ENEMY_POS[0] # Reset for pokemon
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
        elif self.phase == 2: # Go Pokemon!
            self._update_text(f"Go! {self.player_mon.name}!")
            self.trainer_x -= 26
            self.player_pokemon_x = min(PLAYER_POS[0], self.player_pokemon_x + 28)
            if self.player_pokemon_x >= PLAYER_POS[0] - 15 and self.text_done:
                if self.player_mon.cry:
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

# [REF-0022b] Catch Animation System
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
        self.ball_sprite = self.data_manager.load_ball_sprite(ball_name)
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

# [REF-0022c] Faint Animation System
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

# [REF-0023] BATTLE ENGINE (Main Controller)
class BattleEngine:
    # [REF-0023a] Initialization
    def __init__(self, screen, clock, player_party, enemy_id, is_trainer=False,
                 trainer_name="", trainer_sprite=None, battle_bg_files=None,
                 wild_music=None, victory_music=None, trainer_music=None, **kwargs):
        self.screen = screen
        self.clock = clock

        # === CORE SYSTEMS ===
        self.data_manager = DataManager()
        self.mechanics = BattleMechanics()
        self.math_system = MathBrain()
        self.battle_session = BattleSession(StageManager())

        # === PARTY ===
        self.party = Party([
            Pokemon(
                p.get("id", random.randint(1, 151)),
                self.data_manager,
                self.mechanics,
                p.get("level", 50),
                back_sprite=True
            )
            for p in (player_party or [])
        ])

        # === ENEMY LOADING — CACHE-FIRST (Overworld-ready) ===
        self.use_cache_only = kwargs.get('use_cache_only', False)
        self.enemy_loaded = False
        self.enemy = None
        enemy_level = 50
        cache_key = (enemy_id, False, enemy_level)

        # === TRAINER SYSTEM ===
        self.trainer_system = None
        if is_trainer:
            self.trainer_system = TrainerSystem(trainer_name, "trainer.png",
                                                [{"id": enemy_id, "level": 50}],
                                                self.data_manager, self.mechanics)

        # === ALL CORE SYSTEMS (must exist before spawning enemy) ===
        self.message_queue = []

        self.enemy_display_hp = 0
        self.player_display_hp = self.party.active.hp if self.party.pokemon else 0

        self.is_trainer = is_trainer
        self.trainer_name = trainer_name
        self.trainer_sprite = trainer_sprite
        self.enemy_id = enemy_id
        self.battle_bg_files = battle_bg_files or []
        self.wild_music = wild_music or []
        self.victory_music = victory_music or []
        self.trainer_music = trainer_music or []
        self.battle_running = True

        self.volatile = {"player": {}, "enemy": {}}
        self.bag = Bag()
        self.pending_item = None
        self.selected_item_mon = None
        self.item_popup_rects = []
        self.item_back_rect = None
        self.sound_manager = SoundManager()
        self.anim_ctrl = AnimationController()
        self.level_up_system = LevelUpSystem(self)
        self.turn_processor = TurnProcessor(self)
        self.state_machine = BattleStateMachine(self)

        self.intro_system = IntroSystem(self.screen, self.data_manager)
        self.catch_system = CatchSystem(self.screen, self.data_manager)
        self.faint_system = FaintAnimation(self.screen)

        # === LOAD TRAINER SPRITE EARLY (required for intro animation) ===
        self.spr_player = load_asset("red_back.png", "sprites", (BATTLE_SCALE, BATTLE_SCALE))

        # === NOW SAFE TO SPAWN ENEMY ===
        if self.use_cache_only or cache_key in self.data_manager.POKEMON_CACHE:
            print(f"⚡ CACHE HIT — spawning enemy #{enemy_id} instantly!")
            self.enemy = Pokemon(enemy_id, self.data_manager, self.mechanics,
                                 level=enemy_level, back_sprite=False)
            self.enemy.stage_manager = StageManager()
            self.enemy_display_hp = self.enemy.hp
            self.enemy_loaded = True

            # TEMP FIX: Skip intro so we see the UI immediately ##GROK PLEASE FIX THE ANIMATION TIMING ISSUE IN INTRO SYSTEM##
            self.state_machine.set_state("MAIN")
        else:
            print(f"🌐 First-time load for #{enemy_id} — fetching async...")
            self.data_manager.async_fetch_pokemon(
                enemy_id, back=False, level=enemy_level, callback=self.on_enemy_loaded
            )

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

    # [REF-0023b] Helper Methods (Action Creation, AI)
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

    # [REF-0023d] Debug Tools
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

    # [REF-0023e] Main Loop (Run)
    def run(self):
        if not self.battle_bg_files:
            pass
        if not self.wild_music:
            sound_dir = os.path.join(ASSETS_DIR, "sounds")
            if os.path.exists(sound_dir):
                self.wild_music = [f for f in os.listdir(sound_dir) if f.startswith("kanto_wild") and f.endswith(".ogg")]
        
        self.battle_bg = load_bg(random.choice(self.battle_bg_files), "backgrounds") if self.battle_bg_files else None
        self.spr_player = load_asset("red_back.png", "sprites", (BATTLE_SCALE, BATTLE_SCALE))

        while self.battle_running:
            # Background music and assets (once)
            if not hasattr(self, '_assets_loaded'):
                music_to_play = self.trainer_music if self.is_trainer else self.wild_music
                self.sound_manager.play_random_music(music_to_play)
                self._assets_loaded = True

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.battle_running = False
                    break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                    self.debug_panel_visible = not self.debug_panel_visible
                if self.debug_panel_visible and event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_debug_click(event.pos)
                
                # === CRITICAL: Async callback handler (for first-time loads) ===
                if event.type == pygame.USEREVENT:
                    if hasattr(event, 'dict') and "callback" in event.dict and "result" in event.dict:
                        try:
                            event.dict["callback"](event.dict["result"])
                        except Exception as e:
                            print(f"[ERROR] Callback failed: {e}")

                self.state_machine.handle_event(event)
            
            self.state_machine.update()
            self.state_machine.draw(self.screen)
            
            if self.debug_panel_visible:
                self.draw_debug_panel()
            
            pygame.display.flip()
            self.clock.tick(60)

        return {"result": "QUIT", "xp_gain": 0, "new_level": 0, "new_xp": 0, "new_xp_needed": 0}
    
    # [REF-0023f] Drawing (Scene)
    def draw_battle_scene(self, screen):
        screen.fill((20, 20, 40))

        if self.battle_bg:
            screen.blit(self.battle_bg, (0, 0))

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

# [REF-0025] OVERWORLD ENGINE — Image-based (perfect for your town PNGs)
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
        self.bg = load_bg(bg_file, "overworld") or pygame.Surface((WIDTH, HEIGHT))

        # Player sprite (use your overworld red sprite)
        self.player = load_asset("red_overworld.png", "sprites", (48, 64)) or pygame.Surface((48, 64))

        # === DEFINE GRASS & BUILDINGS FOR EACH AREA ===
        self.grass_patches = []
        self.buildings = []   # (rect, name)

        if self.area == "PALLET_TOWN":
            self.grass_patches = [pygame.Rect(150, 350, 400, 250)]
            self.buildings = [
                (pygame.Rect(300, 100, 100, 100), "Player House"),
                (pygame.Rect(550, 120, 90, 110), "Rival House"),
                (pygame.Rect(800, 400, 80, 90), "Lab"),
            ]
        # Add more areas here...

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

        # Grass encounter
        if random.random() < 0.03:   # ~3% chance per frame when moving
            for rect in self.grass_patches:
                if rect.collidepoint(self.player_x + 24, self.player_y + 50):
                    enemy_id = self.data_manager.get_random_pokemon_id()  # or pool
                    battle = BattleEngine(self.screen, self.clock, [{"id":1,"level":50}], enemy_id, use_cache_only=True)
                    battle.run()
                    return

    def draw(self):
        self.screen.blit(self.bg, (0, 0))

        # Optional: show grass areas (remove later)
        for r in self.grass_patches:
            pygame.draw.rect(self.screen, (0, 255, 0, 60), r, 2)

        # Buildings
        for rect, name in self.buildings:
            pygame.draw.rect(self.screen, (255, 215, 0), rect, 4)
            draw_text(self.screen, name, FONT_SMALL, WHITE, rect.centerx, rect.bottom + 10)

        self.screen.blit(self.player, (self.player_x, self.player_y))

        draw_text(self.screen, f"Area: {self.area}", FONT_UI, WHITE, 20, 20)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for rect, name in self.buildings:
                if rect.collidepoint(mx, my):
                    print(f"Clicked {name} — add your menu here later!")

# [REF-0024] STANDALONE MAIN (Entry Point)
def standalone_main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pokémath Standalone Battle Sim")
    clock = pygame.time.Clock()

    print("\n=== Pokémath Standalone Battle Simulator ===")
    print("W = Wild Battle   |   T = Trainer Battle   |   ESC = Quit")
    print("Random Level 50 team of 3 Pokémon (for switching test)\n")

    # Auto-collect assets - unchanged from your original
    sound_dir = os.path.join(ASSETS_DIR, "sounds")
    bg_dir = os.path.join(ASSETS_DIR, "backgrounds")

    wild_music = [f for f in os.listdir(sound_dir) if f.startswith("kanto_wild") and f.endswith(".ogg")] or ["kanto_wild1.ogg"]
    trainer_music = [f for f in os.listdir(sound_dir) if f.startswith("kanto_trainer") and f.endswith(".ogg")] or ["kanto_trainer1.ogg"]
    victory_music = [f for f in os.listdir(sound_dir) if f.startswith("kanto_win") and f.endswith(".ogg")] or ["kanto_win1.ogg"]
    battle_bg_files = [f for f in os.listdir(bg_dir) if f.startswith("battle_") and f.endswith(".png")] or ["battle_grass1.png"]
    
    dm = DataManager()
    pool_system = WildPokemonPool()

    running = True
    while running:
        # === SPLASH SCREEN LOOP ===
        in_splash = True
        selected_pool = "RANDOM"
        
        while in_splash and running:
            screen.fill(BLACK)
            draw_text(screen, "POKÉMATH ADVENTURES", FONT_BIG, WHITE, WIDTH // 2, 100)
            draw_text(screen, "Select Battle Mode", FONT_MED, GOLD, WIDTH // 2, 180)

            # Buttons
            mx, my = pygame.mouse.get_pos()
            
            # Wild Button
            wild_rect = pygame.Rect(WIDTH//2 - 250, 250, 240, 80)
            col = GREEN if wild_rect.collidepoint((mx, my)) else DARK_GREEN
            pygame.draw.rect(screen, col, wild_rect, border_radius=15)
            pygame.draw.rect(screen, WHITE, wild_rect, 4, border_radius=15)
            draw_text(screen, "WILD BATTLE", FONT_UI, WHITE, wild_rect.centerx, wild_rect.centery)

            # Trainer Button
            trainer_rect = pygame.Rect(WIDTH//2 + 10, 250, 240, 80)
            col = BLUE if trainer_rect.collidepoint((mx, my)) else (30, 30, 180)
            pygame.draw.rect(screen, col, trainer_rect, border_radius=15)
            pygame.draw.rect(screen, WHITE, trainer_rect, 4, border_radius=15)
            draw_text(screen, "TRAINER BATTLE", FONT_UI, WHITE, trainer_rect.centerx, trainer_rect.centery)

            # Overworld Button
            overworld_rect = pygame.Rect(WIDTH//2 - 120, 380, 240, 80)
            col = (0, 200, 100) if overworld_rect.collidepoint((mx, my)) else (0, 150, 80)
            pygame.draw.rect(screen, col, overworld_rect, border_radius=15)
            pygame.draw.rect(screen, WHITE, overworld_rect, 4, border_radius=15)
            draw_text(screen, "OVERWORLD", FONT_UI, WHITE, overworld_rect.centerx, overworld_rect.centery)

            # Download Sprites Button
            download_rect = pygame.Rect(WIDTH//2 - 130, 480, 260, 70)
            col = (255, 140, 0) if download_rect.collidepoint((mx, my)) else (200, 100, 0)
            pygame.draw.rect(screen, col, download_rect, border_radius=15)
            pygame.draw.rect(screen, WHITE, download_rect, 4, border_radius=15)
            draw_text(screen, "DOWNLOAD ALL SPRITES", FONT_UI, WHITE, download_rect.centerx, download_rect.centery)

            # Quit Button
            quit_rect = pygame.Rect(WIDTH//2 - 100, 650, 200, 60)
            col = RED if quit_rect.collidepoint((mx, my)) else (180, 30, 30)
            pygame.draw.rect(screen, col, quit_rect, border_radius=15)
            pygame.draw.rect(screen, WHITE, quit_rect, 4, border_radius=15)
            draw_text(screen, "QUIT", FONT_UI, WHITE, quit_rect.centerx, quit_rect.centery)

            # Pool Selection
            draw_text(screen, f"Current Pool: {selected_pool}", FONT_SMALL, WHITE, WIDTH//2, 400)
            pools = pool_system.get_pools()
            for i, p_name in enumerate(pools):
                r = pygame.Rect(WIDTH//2 - 300 + (i%4)*150, 450 + (i//4)*60, 140, 40)
                c = GOLD if p_name == selected_pool else GRAY
                if r.collidepoint((mx, my)): c = YELLOW
                pygame.draw.rect(screen, c, r, border_radius=8)
                draw_text(screen, p_name, FONT_SMALL, BLACK, r.centerx, r.centery)
                if pygame.mouse.get_pressed()[0] and r.collidepoint((mx, my)):
                    selected_pool = p_name

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    in_splash = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if wild_rect.collidepoint(event.pos):
                        print(f"→ Starting WILD BATTLE ({selected_pool})")
                        screen.fill(BLACK)
                        draw_text(screen, "LOADING POKÉMON DATA...", FONT_MED, WHITE, WIDTH // 2, HEIGHT // 2)
                        pygame.display.flip()   # show loading immediately
                        player_party = create_test_team(dm, 3)
                        enemy_id = pool_system.get_random_id(selected_pool)
                        engine = BattleEngine(screen, clock, player_party, enemy_id,
                                              battle_bg_files=battle_bg_files,
                                              wild_music=wild_music,
                                              trainer_music=trainer_music,
                                              victory_music=victory_music,
                                              use_cache_only=True)
                        engine.run()
                    elif trainer_rect.collidepoint(event.pos):
                        print("→ Starting TRAINER BATTLE")
                        screen.fill(BLACK)
                        draw_text(screen, "LOADING POKÉMON DATA...", FONT_MED, WHITE, WIDTH // 2, HEIGHT // 2)
                        pygame.display.flip()   # show loading immediately
                        player_party = create_test_team(dm, 3)
                        enemy_id = pool_system.get_random_id(selected_pool)
                        trainer_name = random.choice(["Youngster", "Lass", "Camper", "Picnicker", "Bug Catcher"])
                        engine = BattleEngine(screen, clock, player_party, enemy_id, is_trainer=True, trainer_name=trainer_name, battle_bg_files=battle_bg_files, trainer_music=trainer_music, victory_music=victory_music)
                        engine.run()
                    elif quit_rect.collidepoint(event.pos):
                        running = False
                        in_splash = False
                    elif overworld_rect.collidepoint(event.pos):
                        print("→ Starting OVERWORLD")
                        screen.fill(BLACK)
                        draw_text(screen, "Loading Overworld...", FONT_MED, WHITE, WIDTH // 2, HEIGHT // 2)
                        pygame.display.flip()
                        
                        overworld = OverworldEngine(screen, clock, dm, start_area=selected_pool)
                        # Simple overworld loop
                        running_ow = True
                        while running_ow:
                            for e in pygame.event.get():
                                if e.type == pygame.QUIT:
                                    running_ow = False
                                    running = False
                                overworld.handle_event(e)
                            
                            overworld.update()
                            overworld.draw()
                            pygame.display.flip()
                            clock.tick(60)
                    elif download_rect.collidepoint(event.pos):
                        screen.fill(BLACK)
                        draw_text(screen, "Downloading sprites... (this is one-time)", FONT_MED, WHITE, WIDTH//2, HEIGHT//2)
                        pygame.display.flip()
                        dm.download_all_sprites()
                        draw_text(screen, "Download complete! You can now play offline.", FONT_MED, GREEN, WIDTH//2, HEIGHT//2 + 80)
                        pygame.display.flip()
                        pygame.time.wait(2000)

            clock.tick(60)

    pygame.quit()


# Helper to create a team of 3 random Pokémon (unchanged from your original)
def create_test_team(dm, num=3):
    team = []
    used = set()
    for _ in range(num):
        pid = dm.get_random_pokemon_id(exclude_id=list(used) if used else None)
        used.add(pid)
        team.append({"id": pid, "level": 50})
    return team

if __name__ == "__main__":
    standalone_main()