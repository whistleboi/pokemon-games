import pygame
import random
import requests
import io
import os
import math
import threading
import queue
import json
import sys

# --- System Initialization ---
pygame.mixer.pre_init(44100, -16, 2, 4096)
pygame.init()
pygame.mixer.init()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h

# --- Caching System ---
CACHE_DIR = os.path.join(BASE_DIR, "cache")
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Platform Detection
IS_PC = sys.platform in ['win32', 'linux', 'darwin']
if IS_PC:
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
else:
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)

PLAY_CRY_EVENT = pygame.USEREVENT + 1
preloaded_queue = queue.Queue(maxsize=2)
last_served_names = set()

# Global State for Threading
shiny_charm_active = False
dev_shiny_mode = False

# Colors
WHITE, BLACK, GREEN, RED, YELLOW, BLUE, GOLD = (
    (255, 255, 255), (0, 0, 0), (0, 255, 0), (255, 50, 50), (255, 215, 0),
    (50, 50, 200), (255, 215, 0)
)
ORANGE, DARK_RED = (255, 165, 0), (139, 0, 0)
PURPLE, NEON_BLUE, AMBER = (128, 0, 128), (0, 255, 255), (255, 191, 0)
GRAY = (128, 128, 128)
FPS = 20
VOLUME = 0.1

# UI Scaling
FONT_SCALE = 0.5 if IS_PC else 1.0

# Fonts
FONT_BIG = pygame.font.SysFont("Arial", int(WIDTH * 0.08 * FONT_SCALE), bold=True)
FONT_MED = pygame.font.SysFont("Arial", int(WIDTH * 0.07 * FONT_SCALE), bold=True)
FONT_S_MED = pygame.font.SysFont("Arial", int(WIDTH * 0.05 * FONT_SCALE), bold=True)
FONT_NUM = pygame.font.SysFont("Arial", int(WIDTH * 0.08 * FONT_SCALE), bold=True)
FONT_SMALL = pygame.font.SysFont("Arial", int(WIDTH * 0.035 * FONT_SCALE), bold=True)
FONT_TINY = pygame.font.SysFont("Arial", int(WIDTH * 0.025 * FONT_SCALE), bold=True)
FONT_TRIVIA = pygame.font.SysFont("Arial", int(WIDTH * 0.040 * FONT_SCALE), bold=True)

# --- Assets ---
collected_team = []
high_score = 0
total_shinies = 0

BALL_IMGS = []
ball_types = [
    "poke-ball", "great-ball", "ultra-ball", "premier-ball", "luxury-ball",
    "timer-ball", "quick-ball", "nest-ball", "net-ball", "dive-ball",
    "repeat-ball"
]
for bt in ball_types:
    try:
        url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/{bt}.png"
        img = pygame.image.load(
            io.BytesIO(requests.get(url).content)
        ).convert_alpha()
        BALL_IMGS.append(pygame.transform.scale(img, (85, 85)))
    except Exception:
        pass
if not BALL_IMGS:
    fallback = pygame.Surface((85, 85), pygame.SRCALPHA)
    pygame.draw.circle(fallback, RED, (42, 42), 35)
    BALL_IMGS = [fallback]

UI_BALL = pygame.transform.scale(BALL_IMGS[0], (int(WIDTH*0.04), int(WIDTH*0.04)))

shiny_charm_img = None
try:
    url = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/shiny-charm.png"
    charm_raw = pygame.image.load(
        io.BytesIO(requests.get(url).content)
    ).convert_alpha()
    shiny_charm_img = pygame.transform.scale(
        charm_raw, (int(WIDTH * 0.08), int(WIDTH * 0.08))
    )
except Exception:
    shiny_charm_img = None

GO_IMG = None
img_path = os.path.join(BASE_DIR, "1.png")
if os.path.exists(img_path):
    try:
        raw_img = pygame.image.load(img_path).convert()
        scale_h = int(HEIGHT * 0.4)
        scale_w = int(raw_img.get_width() * (scale_h / raw_img.get_height()))
        GO_IMG = pygame.transform.scale(raw_img, (scale_w, scale_h))
    except Exception:
        pass

# --- Data Management ---
SAVE_FILE = os.path.join(BASE_DIR, "game_data.json")

def load_data():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"high_score": 0, "total_shinies": 0, "pokedex": {}}

game_data = load_data()
high_score = game_data.get("high_score", 0)
total_shinies = game_data.get("total_shinies", 0)

def save_data():
    game_data["high_score"] = high_score
    game_data["total_shinies"] = total_shinies
    with open(SAVE_FILE, "w") as f:
        json.dump(game_data, f)

# --- Helpers ---
class Starburst:
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
        self.particles = [
            p for p in self.particles if p[2] > 0
        ]
    def draw(self, surface):
        for p in self.particles:
            pygame.draw.circle(
                surface, self.color,
                (int(p[0][0]), int(p[0][1])), random.randint(3, 6)
            )


class ShinyBurst:
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
        self.particles = [
            p for p in self.particles if p[2] > 0
        ]
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


def draw_text_outline(
    text, font, color, x, y, outline_color=BLACK, thickness=3, align="center"
):
    text_surf = font.render(text, True, color)
    if align == "center":
        pos = (x - text_surf.get_width()//2, y - text_surf.get_height()//2)
    elif align == "right":
        pos = (x - text_surf.get_width(), y)
    else:
        pos = (x, y)

    for dx, dy in [(-thickness, 0), (thickness, 0), (0, -thickness), (0, thickness)]:
        outline_surf = font.render(text, True, outline_color)
        screen.blit(outline_surf, (pos[0] + dx, pos[1] + dy))
    screen.blit(text_surf, pos)


# --- ID Pools ---
UB_IDS = [793, 794, 795, 796, 797, 798, 799, 803, 804, 805, 806]
PAST_IDS = [984, 985, 986, 987, 988, 989, 990, 1007, 1009]
FUTURE_IDS = [991, 992, 993, 994, 995, 996, 997, 1008, 1010]
STANDARD_BOSS_IDS = [
    144, 145, 146, 150, 151, 243, 244, 245, 249, 250, 251, 380, 381, 382, 383,
    384, 385, 386, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491,
    492, 493, 494, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 716, 717,
    718, 719, 720, 721, 772, 773, 785, 786, 787, 788, 789, 790, 791, 792, 888,
    889, 890, 891, 892, 893, 894, 895, 896, 897, 898
]

# Master list for strict exclusion from regular rounds
ALL_BOSS_IDS = set(UB_IDS + PAST_IDS + FUTURE_IDS + STANDARD_BOSS_IDS)


def fetch_pokemon_raw(pool_type=None, exclude_names=None):
    global shiny_charm_active, dev_shiny_mode
    if exclude_names is None: exclude_names = set()
    attempts = 0
    if dev_shiny_mode: base_odds = 0.25
    else: base_odds = 0.04 if shiny_charm_active else 0.02
    
    target_pool = None
    if pool_type == "UB":
        target_pool = UB_IDS
    elif pool_type == "PAST":
        target_pool = PAST_IDS
    elif pool_type == "FUTURE":
        target_pool = FUTURE_IDS
    elif pool_type == "STANDARD":
        target_pool = STANDARD_BOSS_IDS
    
    while attempts < 5:
        if target_pool:
            p_id = random.choice(target_pool)
        else:
            p_id = random.randint(1, 1010)
            # EXCLUSION FIX: Strictly avoid any boss ID in regular slots
            if p_id in ALL_BOSS_IDS:
                continue
            
        is_shiny = (random.random() < base_odds)
        try:
            # 1. Fetch/Cache Data JSON
            json_path = os.path.join(CACHE_DIR, f"data_{p_id}.json")
            if os.path.exists(json_path):
                with open(json_path, "r") as f:
                    resp = json.load(f)
            else:
                resp = requests.get(f"https://pokeapi.co/api/v2/pokemon/{p_id}").json()
                with open(json_path, "w") as f:
                    json.dump(resp, f)

            name = resp['name'].upper()
            if name in exclude_names:
                attempts += 1
                continue

            # 2. Fetch/Cache Sprite
            img_url = resp['sprites'][
                'front_shiny' if is_shiny else 'front_default'
            ]
            img_name = f"sprite_{p_id}_{'shiny' if is_shiny else 'normal'}.png"
            img_path = os.path.join(CACHE_DIR, img_name)
            if os.path.exists(img_path):
                with open(img_path, "rb") as f:
                    img_bytes = f.read()
            else:
                img_bytes = requests.get(img_url).content
                with open(img_path, "wb") as f:
                    f.write(img_bytes)

            # 3. Fetch/Cache Cry
            cry_url = resp['cries']['latest']
            cry_name = f"cry_{p_id}.ogg"
            cry_path = os.path.join(CACHE_DIR, cry_name)
            if os.path.exists(cry_path):
                with open(cry_path, "rb") as f:
                    cry_bytes = f.read()
            else:
                cry_bytes = requests.get(cry_url).content
                with open(cry_path, "wb") as f:
                    f.write(cry_bytes)

            return {
                "id": p_id, "name": name, "img": img_bytes, "cry": cry_bytes,
                "is_shiny": is_shiny
            }
        except Exception:
            return None
    return None

def loader_worker():
    global last_served_names
    while True:
        if not preloaded_queue.full():
            p_list = []; current_batch_names = set()
            for _ in range(3):
                p = fetch_pokemon_raw(
                    None, exclude_names=last_served_names | current_batch_names
                )
                if p:
                    p_list.append(p)
                    current_batch_names.add(p['name'])

            # Every batch now contains a randomized Boss encounter (Random Boss Type)
            b_type = random.choice(["STANDARD", "UB", "PAST", "FUTURE"])
            boss_p = fetch_pokemon_raw(b_type)
            
            if len(p_list) == 3 and boss_p:
                preloaded_queue.put({
                    "normal": p_list,
                    "boss": boss_p,
                    "names": current_batch_names,
                    "boss_type": b_type
                })
        pygame.time.wait(200)

threading.Thread(target=loader_worker, daemon=True).start()


def finalize_p_data(raw_item, size_mult=3.5):
    img = pygame.image.load(io.BytesIO(raw_item['img'])).convert_alpha()
    mult = size_mult * 2 if IS_PC else size_mult
    s = int(WIDTH // mult)
    scaled_img = pygame.transform.scale(img, (s, s))
    sb_scale = 0.05 if IS_PC else 0.12
    sidebar_img = pygame.transform.scale(img, (int(WIDTH * sb_scale), int(WIDTH * sb_scale)))
    cry = pygame.mixer.Sound(io.BytesIO(raw_item['cry']))
    cry.set_volume(VOLUME)
    return (
        scaled_img, raw_item['name'], raw_item['is_shiny'], cry, sidebar_img,
        raw_item['id'], raw_item['cry']
    )


def generate_math_set(score=0):
    if score < 10:
        limit = 20
    elif score < 20:
        limit = 30
    elif score < 30:
        limit = 40
    elif score < 40:
        limit = 50
    else:
        limit = 100
    op = random.choice(['+', '-'])
    if op == '+':
        ans = random.randint(2, limit)
        a = random.randint(1, ans - 1)
        b = ans - a
    else:
        a = random.randint(2, limit)
        b = random.randint(1, a - 1)
        ans = a - b
    opts = {ans}
    while len(opts) < 3:
        f = ans + random.randint(-5, 5)
        if f >= 0 and f != ans:
            opts.add(f)
    return (
        f"{a} {op} {b}", ans,
        sorted(list(opts), key=lambda x: random.random())
    )


SHINY_SFX = None
HEAL_SFX = None
music_path = os.path.join(BASE_DIR, 'music.mp3')
shiny_path = os.path.join(BASE_DIR, 'Shiny.mp3')
heal_path = os.path.join(BASE_DIR, 'heal.mp3')
try:
    if os.path.exists(music_path):
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(VOLUME)
        pygame.mixer.music.play(-1)
    if os.path.exists(shiny_path):
        SHINY_SFX = pygame.mixer.Sound(shiny_path)
        SHINY_SFX.set_volume(VOLUME)
    if os.path.exists(heal_path): 
        HEAL_SFX = pygame.mixer.Sound(heal_path)
        HEAL_SFX.set_volume(VOLUME)
except Exception: pass

def show_pokedex():
    global total_shinies, dev_shiny_mode
    page = 0
    show_shinies_only = False
    while True:
        screen.fill(WHITE)
        pygame.draw.circle(screen, RED, (WIDTH//2, HEIGHT//2), WIDTH)
        pygame.draw.rect(screen, WHITE, (0, HEIGHT//2, WIDTH, HEIGHT//2))
        pygame.draw.line(screen, BLACK, (0, HEIGHT//2), (WIDTH, HEIGHT//2), 20)
        pygame.draw.circle(screen, BLACK, (WIDTH//2, HEIGHT//2), 120)
        pygame.draw.circle(screen, WHITE, (WIDTH//2, HEIGHT//2), 90)

        full_dex = list(game_data["pokedex"].values())
        if show_shinies_only:
            full_dex = [p for p in full_dex if p['shiny']]
        full_dex.sort(key=lambda x: x['id'])
        
        draw_text_outline(
            "POKÉDEX", FONT_MED, BLACK, WIDTH // 2, HEIGHT * 0.08,
            outline_color=WHITE
        )
        draw_text_outline(
            f"CAUGHT: {len(game_data['pokedex'])} / 1010", FONT_TINY, BLACK,
            WIDTH // 2, HEIGHT * 0.13, outline_color=WHITE
        )
        
        cols, rows = 4, 3
        per_page = cols * rows
        start_idx = page * per_page
        current_view = full_dex[start_idx : start_idx + per_page]
        
        dex_btns = []
        for i in range(per_page):
            c, r = i % cols, i // cols
            x = WIDTH * 0.15 + (c * (WIDTH * 0.23))
            y = HEIGHT * 0.25 + (r * (HEIGHT * 0.20))
            rect = pygame.Rect(x - 60, y - 60, 120, 120)
            pygame.draw.rect(screen, (220, 220, 220), rect, border_radius=10)
            pygame.draw.rect(screen, BLACK, rect, 3, border_radius=10)
            
            if i < len(current_view):
                p_entry = current_view[i]
                try:
                    raw_img = bytes.fromhex(p_entry['img_hex'])
                    icon = pygame.transform.scale(
                        pygame.image.load(io.BytesIO(raw_img)).convert_alpha(),
                        (100, 100)
                    )
                    screen.blit(icon, icon.get_rect(center=rect.center))
                    draw_text_outline(
                        f"#{p_entry['id']}", FONT_TINY, BLACK, rect.centerx,
                        rect.bottom + 15, outline_color=WHITE
                    )
                    if p_entry['shiny']:
                        draw_star(screen, GOLD, (rect.right - 15, rect.top + 15), 12)
                    dex_btns.append((rect, p_entry['cry_hex']))
                except Exception:
                    pass
            else:
                draw_text_outline("?", FONT_MED, (180, 180, 180), rect.centerx, rect.centery)

        btn_back = pygame.Rect(30, 30, 140, 70)
        pygame.draw.rect(screen, RED, btn_back, border_radius=15)
        draw_text_outline("BACK", FONT_SMALL, WHITE, btn_back.centerx, btn_back.centery)
        
        btn_shiny_toggle = pygame.Rect(WIDTH - 250, 30, 220, 70)
        pygame.draw.rect(
            screen, GOLD if show_shinies_only else BLUE, btn_shiny_toggle,
            border_radius=15
        )
        draw_text_outline(
            "SHINIES", FONT_SMALL, WHITE, btn_shiny_toggle.centerx,
            btn_shiny_toggle.centery
        )

        btn_wipe = pygame.Rect(30, HEIGHT * 0.75, 220, 60)
        pygame.draw.rect(screen, DARK_RED, btn_wipe, border_radius=15)
        draw_text_outline("WIPE DATA", FONT_TINY, WHITE, btn_wipe.centerx, btn_wipe.centery)

        btn_dev = pygame.Rect(WIDTH - 250, HEIGHT * 0.75, 220, 60)
        dev_col = GREEN if dev_shiny_mode else BLACK
        pygame.draw.rect(screen, dev_col, btn_dev, border_radius=15)
        draw_text_outline("DEV MODE", FONT_TINY, WHITE, btn_dev.centerx, btn_dev.centery)
        
        btn_prev = pygame.Rect(WIDTH * 0.3, HEIGHT * 0.85, 150, 70)
        pygame.draw.rect(screen, BLACK, btn_prev, border_radius=15)
        draw_text_outline("<", FONT_S_MED, WHITE, btn_prev.centerx, btn_prev.centery)
        
        btn_next = pygame.Rect(WIDTH * 0.6, HEIGHT * 0.85, 150, 70)
        pygame.draw.rect(screen, BLACK, btn_next, border_radius=15)
        draw_text_outline(">", FONT_S_MED, WHITE, btn_next.centerx, btn_next.centery)

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_back.collidepoint(event.pos):
                    return
                if btn_shiny_toggle.collidepoint(event.pos):
                    show_shinies_only = not show_shinies_only
                    page = 0
                if btn_dev.collidepoint(event.pos):
                    dev_shiny_mode = not dev_shiny_mode
                if btn_wipe.collidepoint(event.pos):
                    confirming = True
                    while confirming:
                        pygame.draw.rect(
                            screen, BLACK,
                            (WIDTH // 4, HEIGHT // 3, WIDTH // 2, HEIGHT // 3)
                        )
                        draw_text_outline(
                            "WIPE ALL DATA?", FONT_SMALL, RED, WIDTH // 2,
                            HEIGHT // 2 - 30
                        )
                        by = pygame.Rect(WIDTH//2 - 110, HEIGHT//2 + 20, 100, 60)
                        pygame.draw.rect(screen, RED, by)
                        bn = pygame.Rect(WIDTH//2 + 10, HEIGHT//2 + 20, 100, 60)
                        pygame.draw.rect(screen, GREEN, bn)
                        draw_text_outline("YES", FONT_TINY, WHITE, by.centerx, by.centery)
                        draw_text_outline("NO", FONT_TINY, WHITE, bn.centerx, bn.centery)
                        pygame.display.flip()
                        for e in pygame.event.get():
                            if e.type == pygame.MOUSEBUTTONDOWN:
                                if by.collidepoint(e.pos):
                                    if HEAL_SFX: HEAL_SFX.play()
                                    game_data["pokedex"] = {}
                                    total_shinies = 0
                                    save_data()
                                    confirming = False
                                if bn.collidepoint(e.pos):
                                    confirming = False
                if btn_next.collidepoint(event.pos) and (page + 1) * per_page < len(full_dex):
                    page += 1
                if btn_prev.collidepoint(event.pos) and page > 0:
                    page -= 1
                for r, cry_hex in dex_btns:
                    if r.collidepoint(event.pos):
                        pygame.mixer.Sound(io.BytesIO(bytes.fromhex(cry_hex))).play()

def show_loading_screen():
    angle = 0
    ball_img = BALL_IMGS[0] if BALL_IMGS else pygame.Surface((85, 85))
    ball_img = pygame.transform.scale(ball_img, (150, 150))

    while not preloaded_queue.full():
        screen.fill(BLACK)
        draw_text_outline(
"LOADING WORLD DATA...", FONT_MED, WHITE, WIDTH // 2, HEIGHT * 0.3
        )

        angle = (angle - 5) % 360
        rot_img = pygame.transform.rotate(ball_img, angle)
        rect = rot_img.get_rect(center=(WIDTH // 2, HEIGHT * 0.6))
        screen.blit(rot_img, rect)

        pygame.display.flip()
        pygame.time.Clock().tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

def show_game_over():
    global high_score, total_shinies
    while True:
        screen.fill(BLACK)
        if GO_IMG:
            screen.blit(GO_IMG, GO_IMG.get_rect(center=(WIDTH // 2, HEIGHT * 0.35)))
        draw_text_outline(
            "GAME OVER", FONT_BIG, RED, WIDTH // 2, HEIGHT * 0.1
        )
        btn_retry = pygame.Rect(WIDTH//2 - 200, HEIGHT * 0.60, 400, 80)
        pygame.draw.rect(screen, GREEN, btn_retry, border_radius=15)
        draw_text_outline("RETRY", FONT_S_MED, WHITE, btn_retry.centerx, btn_retry.centery)
        btn_reset = pygame.Rect(WIDTH//2 - 200, HEIGHT * 0.72, 400, 80)
        pygame.draw.rect(screen, DARK_RED, btn_reset, border_radius=15)
        draw_text_outline(
            "RESET STREAK", FONT_SMALL, WHITE, btn_reset.centerx,
            btn_reset.centery
        )
        btn_exit = pygame.Rect(WIDTH//2 - 200, HEIGHT * 0.84, 400, 80)
        pygame.draw.rect(screen, RED, btn_exit, border_radius=15)
        draw_text_outline("EXIT GAME", FONT_S_MED, WHITE, btn_exit.centerx, btn_exit.centery)

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_retry.collidepoint(event.pos):
                    if HEAL_SFX: HEAL_SFX.play()
                    return
                if btn_reset.collidepoint(event.pos): 
                    if HEAL_SFX: HEAL_SFX.play()
                    high_score = 0
                    save_data()
                    return
                if btn_exit.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

def play():
    global high_score, total_shinies, collected_team, last_served_names, shiny_charm_active, dev_shiny_mode, VOLUME
    total_caught, balls_left, aura_pulse, boss_hp = 0, 5, 0.0, 3
    current_streak = 0
    shiny_charm_active = False
    flash_msg, flash_timer = "", 0
    
    def get_cx(i):
        if IS_PC:
            return WIDTH // 2 + (i - 1) * (WIDTH // 6)
        return (i * WIDTH // 3) + (WIDTH // 6)
    btn_size = 100 if IS_PC else 140

    in_boss_mode, boss_intro_played = False, False
    feedback_text, feedback_color, boss_hits = "", WHITE, 0
    current_boss_type = "STANDARD"
    current_ball_img = BALL_IMGS[0]
    
    show_loading_screen()
    current_raw = preloaded_queue.get()
    last_served_names = current_raw['names']
    problem_str, correct_ans, options = generate_math_set(0)
    p_data = [finalize_p_data(p) for p in current_raw['normal']]
    
    starbursts, idle_sparkles, sprite_y, scr_shake_timer = [], [], HEIGHT * 0.4, 0
    
    for i, p in enumerate(p_data):
        if p[2]:
            idle_sparkles.append((IdleSparkle(0,0), i))
            starbursts.append(
                ShinyBurst(get_cx(i), sprite_y)
            )
            if SHINY_SFX: SHINY_SFX.play()

    ball_active, ball_pos, ball_target, pause_timer = False, [0,0], [0,0], 0
    caught_idx, flee_active, shake_amount, boss_intro, boss_cry_triggered = -1, False, 0, 0, False
    runaway_x_offsets = [0, 0, 0]
    stars = [
        [random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(2, 4)]
        for _ in range(40)
    ]
    clock = pygame.time.Clock()
    
    dragging_vol = False

    while True:
        # ANDROID FOCUS RECOVERY: Fixes lag and audio loss after phone calls
        if not pygame.display.get_active():
            pygame.time.wait(250)
            continue

        if not pygame.mixer.music.get_busy():
            try:
                pygame.mixer.music.play(-1)
            except Exception:
                pass

        screen.fill(BLACK)
        clock.tick(FPS)
        offset_x, offset_y = 0, 0
        if scr_shake_timer > 0:
            scr_shake_timer -= 1
            offset_x, offset_y = random.randint(-15, 15), random.randint(-15, 15)

        if in_boss_mode and not boss_intro_played and pause_timer == 0 and not ball_active:
            boss_intro, shake_amount, boss_intro_played, boss_hits, boss_cry_triggered = 50, 40, True, 0, False
            
            current_boss_type = current_raw.get('boss_type', 'STANDARD')
            caught_idx = -1
            
            if current_boss_type == "UB":
                feedback_text = "A STRANGE WORMHOLE HAS OPENED!"
            elif current_boss_type == "PAST":
                feedback_text = "ANCIENT ROARS ECHO FROM THE ABYSS..."
            elif current_boss_type == "FUTURE":
                feedback_text = "METALLIC WHIRS CRACKLE FROM THE VOID..."
            else:
                feedback_text = "A POWERFUL POKEMON IS APPROACHING!"
                
            boss_p = finalize_p_data(current_raw['boss'], 1.5)
            p_data = [
                (None, "", False, None, None, 0, b""), boss_p,
                (None, "", False, None, None, 0, b"")
            ]
            runaway_x_offsets = [0, 0, 0]
            if boss_p[2]:
                idle_sparkles = [(IdleSparkle(0,0), 1)]
                starbursts.append(ShinyBurst(WIDTH//2, sprite_y))
                if SHINY_SFX: SHINY_SFX.play()

        if boss_intro > 0:
            boss_intro -= 1
            if boss_intro % 12 < 6: 
                if current_boss_type == "UB":
                    screen.fill(PURPLE)
                elif current_boss_type == "PAST":
                    screen.fill(AMBER)
                elif current_boss_type == "FUTURE":
                    screen.fill(NEON_BLUE)
                else:
                    screen.fill((150, 0, 0))
                
            draw_text_outline(feedback_text, FONT_S_MED, YELLOW, WIDTH//2, HEIGHT//2)
            pygame.display.flip()
            continue

        if in_boss_mode and boss_intro == 0 and not boss_cry_triggered:
            if p_data[1][3]: p_data[1][3].play()
            boss_cry_triggered = True

        if in_boss_mode:
            aura_pulse += 0.05
            if current_boss_type == "UB":
                bg_v = int(20 + math.sin(aura_pulse) * 15)
                screen.fill((bg_v, 0, bg_v))
            elif current_boss_type == "PAST":
                bg_v = int(40 + math.sin(aura_pulse) * 20)
                screen.fill((bg_v, bg_v // 2, 0))
            elif current_boss_type == "FUTURE":
                bg_v = int(40 + math.sin(aura_pulse) * 20)
                screen.fill((0, bg_v, bg_v))
            else:
                bg_v = int(30 + math.sin(aura_pulse) * 20)
                screen.fill((bg_v, 0, bg_v // 2))
        else:
            warp_speed = 15 if ball_active else 1
            spd_base = 10 if (
                pause_timer > 0 and (flee_active or caught_idx != -1)
            ) else 1
            for s in stars:
                s[1] += s[2] * spd_base * warp_speed
                if s[1] > HEIGHT:
                    s[1], s[0] = 0, random.randint(0, WIDTH)
                pygame.draw.circle(screen, (150, 150, 150), (s[0] + offset_x, s[1] + offset_y), 1)

        lbl_balls = FONT_SMALL.render("Balls Remaining: ", True, GREEN)
        screen.blit(lbl_balls, (20 + offset_x, 20 + offset_y))
        ball_x = 20 + lbl_balls.get_width() + 5 + offset_x
        screen.blit(UI_BALL, (ball_x, 15 + offset_y))
        count_x = ball_x + UI_BALL.get_width() + 5
        draw_text_outline(
            f": {balls_left}", FONT_SMALL, WHITE, count_x, 20 + offset_y,
            align="left"
        )
        draw_text_outline(
            f"Current Streak: {current_streak}", FONT_SMALL, YELLOW,
            20 + offset_x, 80 + offset_y, align="left"
        )
        draw_text_outline(
            f"Best Streak: {high_score}", FONT_SMALL, GOLD, 20 + offset_x,
            140 + offset_y, align="left"
        )

        lbl_shiny = FONT_SMALL.render("Shinies ", True, GOLD)
        screen.blit(lbl_shiny, (20 + offset_x, 200 + offset_y))
        star_x = 20 + lbl_shiny.get_width() + 15 + offset_x
        draw_star(screen, GOLD, (star_x, 215 + offset_y), 15)
        shiny_count_x = star_x + 20
        draw_text_outline(
            f": {total_shinies}", FONT_SMALL, WHITE, shiny_count_x,
            200 + offset_y, align="left"
        )
        
        # Volume Slider (Bottom Left)
        vol_bar = pygame.Rect(120, HEIGHT - 40, 200, 10)
        vol_knob_x = vol_bar.x + int(VOLUME * vol_bar.width)
        vol_knob = pygame.Rect(vol_knob_x - 10, HEIGHT - 50, 20, 30)
        
        draw_text_outline("VOL", FONT_TINY, WHITE, 110, HEIGHT - 35, align="right")
        pygame.draw.rect(screen, GRAY, vol_bar, border_radius=5)
        pygame.draw.rect(screen, GREEN, (vol_bar.x, vol_bar.y, vol_knob_x - vol_bar.x, vol_bar.height), border_radius=5)
        pygame.draw.rect(screen, WHITE, vol_knob, border_radius=5)

        if shiny_charm_active and shiny_charm_img:
            screen.blit(shiny_charm_img, (20 + offset_x, 260 + offset_y))

        BTN_DEX = pygame.Rect(20, 260 if not shiny_charm_active else 350, 250, 80)
        BTN_END = pygame.Rect(20, BTN_DEX.bottom + 15, 250, 80)
        pygame.draw.rect(screen, BLUE, BTN_DEX, border_radius=15)
        draw_text_outline(
            "POKÉDEX", FONT_SMALL, WHITE, BTN_DEX.centerx, BTN_DEX.centery
        )
        pygame.draw.rect(screen, RED, BTN_END, border_radius=15)
        draw_text_outline(
            "END GAME", FONT_SMALL, WHITE, BTN_END.centerx, BTN_END.centery
        )

        for i, tp in enumerate(collected_team[-6:]):
            col, row = i % 3, i // 3
            if IS_PC:
                unit = int(WIDTH * 0.05)
                spacing = int(unit * 1.1)
                margin_x = int(WIDTH * 0.02)
                margin_y = int(HEIGHT * 0.02)
                sx = WIDTH - margin_x - ((3 - col) * spacing)
                sy = margin_y + (row * spacing)
            else:
                sx = WIDTH - (WIDTH * 0.42) + (col * (WIDTH * 0.13))
                sy = 20 + (row * (WIDTH * 0.14))
            if tp[4]:
                screen.blit(tp[4], (sx + offset_x, sy + offset_y))
        
        if in_boss_mode and boss_intro == 0 and boss_hp > 0:
            bar_color, bar_width = GREEN, 300
            if boss_hp == 2:
                bar_color, bar_width = ORANGE, 150
            elif boss_hp == 1:
                bar_color, bar_width = DARK_RED, 75
            pygame.draw.rect(screen, RED, (WIDTH//2 - 150, 200, 300, 25))
            pygame.draw.rect(screen, bar_color, (WIDTH//2 - 150, 200, bar_width, 25))
        
        if pause_timer == 0 and not ball_active:
            for sparkle, idx in idle_sparkles:
                cx = get_cx(idx)
                sparkle.update(cx + offset_x, sprite_y + offset_y - (WIDTH * 0.15))
                sparkle.draw(screen)

        for sb in starbursts:
            sb.update()
            sb.draw(screen)

        current_btns = []
        for i in range(3):
            cx = get_cx(i)
            p_info = p_data[i]
            if p_info[0]:
                if (ball_active or pause_timer > 0 or flee_active) and caught_idx != -1:
                    if flee_active and not in_boss_mode:
                        if i <= 1:
                            runaway_x_offsets[i] -= 35
                        else:
                            runaway_x_offsets[i] += 35
                    else:
                        if i != caught_idx:
                            if i < caught_idx:
                                runaway_x_offsets[i] -= 30
                            else:
                                runaway_x_offsets[i] += 30
                sk = random.randint(-shake_amount, shake_amount) + (random.randint(-5, 5) if in_boss_mode else 0)
                bounce = abs(math.sin(pygame.time.get_ticks() * 0.02) * 30) if runaway_x_offsets[i] != 0 else 0
                wiggle = math.sin(pygame.time.get_ticks() * 0.12) * 25 if (
                    ball_active and not flee_active and i == caught_idx
                ) else 0
                hover_y = math.sin(pygame.time.get_ticks() * 0.005) * 10
                dx, dy = (
                    (WIDTH // 2 if in_boss_mode else cx) + runaway_x_offsets[i] +
                    sk + offset_x + wiggle, sprite_y + sk + offset_y - bounce + hover_y
                )
                should_hide = (
                    (pause_timer > 0) and i == caught_idx and not flee_active and
                    not (in_boss_mode and boss_hp > 0)
                )
                if not should_hide:
                    screen.blit(p_info[0], p_info[0].get_rect(center=(dx, dy)))
            
            if pause_timer == 0:
                cp = (cx, HEIGHT * 0.75)
                pygame.draw.circle(screen, BLUE, cp, int(WIDTH * 0.07 * FONT_SCALE))
                draw_text_outline(str(options[i]), FONT_NUM, WHITE, cp[0], cp[1])
                current_btns.append((
                    pygame.Rect(cx - btn_size//2, cp[1] - btn_size//2, btn_size, btn_size),
                    options[i],
                    p_data[1] if in_boss_mode else p_data[i],
                    i
                ))

        if pause_timer == 0:
            draw_text_outline(
                problem_str, FONT_BIG, YELLOW, WIDTH // 2, HEIGHT * 0.15
            )
        if flash_timer > 0:
            flash_timer -= 1
            draw_text_outline(flash_msg, FONT_S_MED, GOLD, WIDTH//2, HEIGHT//2)

        if ball_active:
            ball_pos[0] += (ball_target[0] - ball_pos[0]) * 0.25
            ball_pos[1] += (ball_target[1] - ball_pos[1]) * 0.25
            screen.blit(current_ball_img, (ball_pos[0]-42, ball_pos[1]-42))
            if abs(ball_pos[1]-ball_target[1]) < 10:
                ball_active, pause_timer = False, 35
                if not flee_active and not (
                    in_boss_mode and feedback_text.endswith("ATTACKED!")
                ):
                    if 0 <= caught_idx < len(p_data) and p_data[caught_idx][3]:
                        p_data[caught_idx][3].play()
                    if in_boss_mode and (feedback_text == "DIRECT HIT!" or
                                         feedback_text == "CRITICAL HIT!"):
                        boss_hp -= 1
                        if boss_hp <= 0:
                            total_caught += 1
                            current_streak += 1
                            collected_team.append(p_data[caught_idx])
                            if current_streak % 5 == 0:
                                balls_left += 1
                                flash_msg = "+1 BALL!"
                                flash_timer = 60
                            if current_streak == 10:
                                shiny_charm_active = True
                                starbursts.append(ShinyBurst(WIDTH//2, HEIGHT//2))
                                if SHINY_SFX: SHINY_SFX.play()
                            p_id_str = str(p_data[caught_idx][5])
                            game_data["pokedex"][p_id_str] = {
                                "id": p_data[caught_idx][5],
                                "name": p_data[caught_idx][1],
                                "shiny": p_data[caught_idx][2],
                                "cry_hex": p_data[caught_idx][6].hex(),
                                "img_hex": current_raw['boss']['img'].hex()
                            }
                            pause_timer = 90
                            feedback_text = f"YOU CAUGHT {p_data[caught_idx][1]}!"
                            if total_caught > high_score:
                                high_score = total_caught
                            save_data()
                            if p_data[caught_idx][2]:
                                total_shinies += 1
                                starbursts.append(ShinyBurst(ball_target[0], ball_target[1]))
                                if SHINY_SFX: SHINY_SFX.play()
                    elif not in_boss_mode:
                        p_id_str = str(p_data[caught_idx][5])
                        game_data["pokedex"][p_id_str] = {
                            "id": p_data[caught_idx][5],
                            "name": p_data[caught_idx][1],
                            "shiny": p_data[caught_idx][2],
                            "cry_hex": p_data[caught_idx][6].hex(),
                            "img_hex": current_raw['normal'][caught_idx]['img'].hex()
                        }
                        current_streak += 1
                        if current_streak % 5 == 0:
                            balls_left += 1
                            flash_msg = "+1 BALL!"
                            flash_timer = 60
                        if current_streak == 10:
                            shiny_charm_active = True
                            starbursts.append(ShinyBurst(WIDTH//2, HEIGHT//2))
                            if SHINY_SFX: SHINY_SFX.play()
                        save_data()
                        if p_data[caught_idx][2]: 
                            total_shinies += 1
                            starbursts.append(ShinyBurst(ball_target[0], ball_target[1]))
                            if SHINY_SFX: SHINY_SFX.play()
                        else:
                            starbursts.append(Starburst(ball_target[0], ball_target[1], WHITE))

        if pause_timer > 0:
            pause_timer -= 1
            draw_text_outline(
                feedback_text, FONT_S_MED, feedback_color, WIDTH // 2,
                HEIGHT * 0.35
            )
            if pause_timer == 1:
                starbursts, idle_sparkles, scr_shake_timer = [], [], 0
                if not (in_boss_mode and boss_hp > 0):
                    p_data = [(None, "", False, None, None, 0, b"")] * 3
                if in_boss_mode and boss_hp <= 0:
                    in_boss_mode = False
                    boss_p = None
                    pygame.event.clear()
                if not in_boss_mode:
                    if not preloaded_queue.empty():
                        current_raw = preloaded_queue.get()
                        last_served_names = current_raw['names']
                        # BOSS TRIGGER FIX: Catch #5 is now a randomized boss from the queue's preloaded type
                        force_boss = (total_caught == 5)
                        random_boss = (total_caught > 5 and random.random() < 0.25)
                        if force_boss or random_boss:
                            in_boss_mode, boss_intro_played, boss_hp = True, False, 3
                        else:
                            p_data = [finalize_p_data(p) for p in current_raw['normal']]
                        for i, p in enumerate(p_data):
                            if p[2]:
                                idle_sparkles.append((IdleSparkle(0,0), i))
                                starbursts.append(
                                    ShinyBurst((i * WIDTH // 3) + (WIDTH // 6),
                                               sprite_y)
                                )
                                if SHINY_SFX: SHINY_SFX.play()
                problem_str, correct_ans, options = generate_math_set(
                    total_caught
                )
                feedback_text, caught_idx, flee_active, runaway_x_offsets = (
                    "", -1, False, [0, 0, 0]
                )
                if not in_boss_mode: shake_amount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # Volume Control
            if event.type == pygame.MOUSEBUTTONDOWN:
                if vol_knob.collidepoint(event.pos) or vol_bar.collidepoint(event.pos):
                    dragging_vol = True
                    mx = max(vol_bar.left, min(event.pos[0], vol_bar.right))
                    VOLUME = (mx - vol_bar.left) / vol_bar.width
                    pygame.mixer.music.set_volume(VOLUME)
                    if SHINY_SFX: SHINY_SFX.set_volume(VOLUME)
                    if HEAL_SFX: HEAL_SFX.set_volume(VOLUME)
                    for p in p_data:
                        if p[3]: p[3].set_volume(VOLUME)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging_vol = False
                
            elif event.type == pygame.MOUSEMOTION:
                if dragging_vol:
                    mx = max(vol_bar.left, min(event.pos[0], vol_bar.right))
                    VOLUME = (mx - vol_bar.left) / vol_bar.width
                    pygame.mixer.music.set_volume(VOLUME)
                    if SHINY_SFX: SHINY_SFX.set_volume(VOLUME)
                    if HEAL_SFX: HEAL_SFX.set_volume(VOLUME)
                    for p in p_data:
                        if p[3]: p[3].set_volume(VOLUME)

            if event.type == pygame.MOUSEBUTTONDOWN and not ball_active and pause_timer == 0:
                idle_sparkles, ui_clicked = [], False
                if BTN_DEX.collidepoint(event.pos):
                    show_pokedex()
                    ui_clicked = True
                elif BTN_END.collidepoint(event.pos):
                    balls_left = 0
                    ui_clicked = True
                if not ui_clicked:
                    for r, v, pi, idx in current_btns:
                        if r.collidepoint(event.pos):
                            current_ball_img, is_shiny_catch = (
                                random.choice(BALL_IMGS),
                                (not in_boss_mode and pi[2])
                            )
                            if v == correct_ans or is_shiny_catch:
                                if in_boss_mode:
                                    boss_hits += 1
                                    feedback_text = (
                                        "DIRECT HIT!" if boss_hits == 1
                                        else "CRITICAL HIT!"
                                    )
                                    feedback_color = YELLOW if boss_hits == 1 else GOLD
                                    ball_active = True
                                    ball_pos = [WIDTH//2, HEIGHT]
                                    ball_target = [WIDTH//2, sprite_y]
                                    caught_idx = 1
                                else:
                                    total_caught += 1
                                    collected_team.append(pi)
                                    if total_caught > high_score:
                                        high_score = total_caught
                                    save_data()
                                    if is_shiny_catch and v != correct_ans:
                                        feedback_text = "CAN'T PASS UP A SHINY!"
                                    else:
                                        feedback_text = f"YOU CAUGHT {pi[1]}!"
                                    feedback_color = GOLD if pi[2] else GREEN
                                    ball_active = True
                                    ball_pos = [WIDTH//2, HEIGHT]
                                    ball_target = [r.centerx, sprite_y]
                                    caught_idx = idx
                            else:
                                balls_left -= 1
                                current_streak = 0
                                shiny_charm_active = False
                                if in_boss_mode: 
                                    if pi[3]: pi[3].play()
                                    feedback_text = f"{pi[1]} ATTACKED!"
                                    feedback_color = RED
                                    shake_amount = 40
                                    pause_timer = 45
                                    ball_active = True
                                    ball_pos = [WIDTH//2, HEIGHT]
                                    ball_target = [WIDTH//2, sprite_y]
                                    caught_idx = 1
                                    scr_shake_timer = 20
                                else:
                                    feedback_text = "OH NO, THEY FLED!"
                                    feedback_color = RED
                                    pause_timer = 40
                                    flee_active = True
                                    caught_idx = idx
                                    ball_active = True
                                    ball_pos = [WIDTH//2, HEIGHT]
                                    ball_target = [r.centerx, sprite_y]
        if balls_left <= 0:
            show_game_over()
            return play()
        pygame.display.flip()
play()
