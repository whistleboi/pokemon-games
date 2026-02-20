import pygame
import random
import requests
import io
import os
import math

# --- System Initialization ---
pygame.mixer.pre_init(44100, -16, 2, 4096)
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1024, 768
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pokémath Adventures")

# Colors
WHITE, BLACK = (255, 255, 255), (10, 10, 10)
GREEN, RED, YELLOW, GOLD = (50, 255, 50), (255, 50, 50), (255, 255, 0), (255, 215, 0)
DARK_GREEN, GRAY, BLUE = (34, 139, 34), (50, 50, 50), (50, 50, 255)
HP_GREEN, HP_YELLOW, HP_RED = (112, 248, 168), (248, 224, 56), (248, 88, 56)

# Fonts
FONT_BIG = pygame.font.SysFont("impact", 64)
FONT_MED = pygame.font.SysFont("impact", 48)
FONT_SMALL = pygame.font.SysFont("arial", 28, bold=True)
FONT_UI = pygame.font.SysFont("arial", 32, bold=True)
FONT_MSG = pygame.font.SysFont("lucidaconsole", 36)

# --- Data Pools ---
STARTER_POOLS = {
    1: [1, 4, 7, 25],       # Kanto
    2: [152, 155, 158],     # Johto
    3: [252, 255, 258],     # Hoenn
    4: [387, 390, 393],     # Sinnoh
    5: [495, 498, 501],     # Unova
    6: [650, 653, 656],     # Kalos
    7: [722, 725, 728],     # Alola
    8: [810, 813, 816],     # Galar
    9: [906, 909, 912]      # Paldea
}
ACTIVE_POOL = STARTER_POOLS[1]

# --- Asset Loading ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

def load_asset(filename, subfolder, size=None):
    path = os.path.join(ASSETS_DIR, subfolder, filename)
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        if size: img = pygame.transform.scale(img, size)
        return img
    return None

def load_sound(filename):
    path = os.path.join(ASSETS_DIR, "sounds", filename)
    if os.path.exists(path):
        return pygame.mixer.Sound(path)
    return None

def load_bg(filename, subfolder):
    img = load_asset(filename, subfolder)
    if img:
        scale = WIDTH / img.get_width()
        new_h = int(img.get_height() * scale)
        return pygame.transform.scale(img, (WIDTH, new_h))
    return None
# --- Helper Functions ---
def draw_text(text, font, text_col, x, y, center=True):
    img = font.render(text, True, text_col)
    rect = img.get_rect()
    if center: rect.center = (x, y)
    else: rect.topleft = (x, y)
    screen.blit(img, rect)

def fetch_pokemon_data(poke_id, back=False):
    """Fetches sprites. Uses 'back' parameter to decide which sprite to get."""
    try:
        url = f"https://pokeapi.co/api/v2/pokemon/{poke_id}"
        response = requests.get(url).json()
        name = response["name"].upper()
        
        sprite_key = "back_default" if back else "front_default"
        sprite_url = response["sprites"][sprite_key]
        
        img_resp = requests.get(sprite_url).content
        image = pygame.image.load(io.BytesIO(img_resp)).convert_alpha()
        image = pygame.transform.scale(image, (384, 384))
        
        cry_sound = None
        base_xp = response.get("base_experience", 50) # Default to 50 if missing
        try:
            cry_url = response["cries"]["latest"]
            audio_resp = requests.get(cry_url).content
            cry_sound = pygame.mixer.Sound(io.BytesIO(audio_resp))
        except: pass
        return image, name, cry_sound, base_xp
    except:
        # Fallback to prevent crash if offline or API fails
        fallback = pygame.Surface((384, 384))
        fallback.fill(GRAY)
        pygame.draw.rect(fallback, RED, (0, 0, 384, 384), 4)
        return fallback, "?????", None, 0

def generate_math_problem(level):
    """Generates math problems scaled by level."""
    # Determine difficulty based on level
    if level < 5:
        ops = ['+']
        limit = 10
    elif level < 10:
        ops = ['+', '-']
        limit = 20
    else:
        ops = ['+', '-', 'x']
        limit = 12 # Lower limit for multiplication to keep it mental-math friendly

    op = random.choice(ops)
    
    if op == '+':
        a, b = random.randint(1, limit), random.randint(1, limit)
        ans = a + b
        question = f"SOLVE: {a} + {b} = ?"
    elif op == '-':
        a, b = random.randint(1, limit), random.randint(1, limit)
        # Ensure positive result
        high, low = max(a, b), min(a, b)
        ans = high - low
        question = f"SOLVE: {high} - {low} = ?"
    elif op == 'x':
        a, b = random.randint(2, 9), random.randint(2, 9)
        ans = a * b
        question = f"SOLVE: {a} x {b} = ?"

    correct_ans = str(ans)
    options = {correct_ans}
    
    # Generate smart wrong answers (close to the real answer)
    while len(options) < 4:
        offset = random.randint(-5, 5)
        if offset != 0:
            fake = ans + offset
            if fake >= 0:
                options.add(str(fake))
    
    options_list = list(options)
    random.shuffle(options_list)
    return question, options_list, correct_ans

def draw_hp_bar(x, y, current_hp, max_hp, name, level, current_xp=None, max_xp=None):
    """B2W2 Slanted HP bar."""
    points = [(x, y), (x + 350, y), (x + 320, y + 80), (x - 30, y + 80)]
    pygame.draw.polygon(screen, (60, 60, 60), points)
    pygame.draw.polygon(screen, WHITE, points, 3)
    draw_text(name, FONT_UI, WHITE, x + 20, y + 25, center=False)
    draw_text(f"Lv. {level}", FONT_UI, WHITE, x + 240, y + 25, center=False)
    
    # Draw XP Bar (Player Only) - Now above HP bar
    if current_xp is not None and max_xp is not None:
        xp_pct = min(1, current_xp / max_xp)
        pygame.draw.rect(screen, BLUE, (x + 20, y + 55, 250 * xp_pct, 6))

    # HP Bar is now below XP bar
    hp_bar_y = y + 63
    pygame.draw.rect(screen, BLACK, (x + 20, hp_bar_y, 250, 12))
    hp_pct = max(0, current_hp / max_hp)
    bar_col = HP_GREEN if hp_pct > 0.5 else HP_YELLOW if hp_pct > 0.2 else HP_RED
    pygame.draw.rect(screen, bar_col, (x + 20, hp_bar_y, 250 * hp_pct, 12))

def draw_multiline_text(text, font, text_col, x, y, max_width, line_height=None):
    if line_height is None: line_height = font.get_linesize()
    words = text.split(' ')
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        w, h = font.size(test_line)
        if w < max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))
    
    total_height = len(lines) * line_height
    start_y = y - (total_height // 2)
    
    for i, line in enumerate(lines):
        draw_text(line, font, text_col, x, start_y + i * line_height)

# ─────────────────────────────────────────────────────────────
# NEW CLASSIC POKÉMON BATTLE ASSETS (Phase 1)
# ─────────────────────────────────────────────────────────────
BATTLE_SCALE = 192
ENEMY_POS = [WIDTH - 320, 85]
PLAYER_POS = [135, 265]
ENEMY_HP_POS = [45, 48]
PLAYER_HP_POS = [520, 380]

# ─────────────────────────────────────────────────────────────
# MAIN GAME LOOP
# ─────────────────────────────────────────────────────────────
def main():
    STATE_CHAR_SELECT, STATE_LOADING = "CHAR_SELECT", "LOADING"
    STATE_INTRO, STATE_TRANSITION, STATE_ANIM_ENTRY = "INTRO", "TRANSITION", "ANIM_ENTRY"
    STATE_ANIM_GARY = "ANIM_GARY"
    STATE_BATTLE_POOCH, STATE_WIN_POOCH = "BATTLE_POOCH", "WIN_POOCH"
    STATE_POOCH_FLEE = "POOCH_FLEE"
    STATE_FOREST_EXIT = "FOREST_EXIT"
    STATE_RIVAL_INTRO, STATE_RIVAL_NAME_INPUT = "RIVAL_INTRO", "RIVAL_NAME_INPUT"
    STATE_LAB, STATE_BATTLE_GARY = "LAB", "BATTLE_GARY"
    STATE_RIVAL_FAINT, STATE_RIVAL_WIN_TEXT = "RIVAL_FAINT", "RIVAL_WIN_TEXT"
    STATE_GARY_EXIT = "GARY_EXIT"
    STATE_LAB_END, STATE_FINAL_WIN = "LAB_END", "FINAL_WIN"
    STATE_LAB_EXIT_CHOICE = "LAB_EXIT_CHOICE"
    STATE_ROUTE1_HUB = "ROUTE1_HUB"
    STATE_LOADING_WILD = "LOADING_WILD"
    STATE_BATTLE_WILD, STATE_WILD_WIN = "BATTLE_WILD", "WILD_WIN"
    STATE_VIRIDIAN = "VIRIDIAN"
    STATE_XP_GAIN = "XP_GAIN"
    STATE_POKECENTER = "POKECENTER"
    STATE_POKEMART = "POKEMART"
    STATE_VIRIDIAN_GYM = "VIRIDIAN_GYM"
    STATE_MENU = "MENU"
    STATE_ROUTE1_FROM_VIRIDIAN = "ROUTE1_FROM_VIRIDIAN"
    STATE_LEVEL_UP = "LEVEL_UP"
    
    # === BATTLE CONSTANTS (Classic Handheld Feel) ===
    BATTLE_SCALE = 384
    ENEMY_POS = [WIDTH - 420, 100]
    PLAYER_POS = [80, 290]
    ENEMY_HP_POS = [45, 48]
    PLAYER_HP_POS = [520, 380]

    current_state = STATE_CHAR_SELECT
    clock = pygame.time.Clock()
    running = True
    current_music_theme = ""

    def play_battle_music(prefix):
        nonlocal current_music_theme
        if current_music_theme == prefix: # Theme is already playing
            return
        try:
            sound_dir = os.path.join(ASSETS_DIR, "sounds")
            
            # Handle specific named tracks vs. prefixed random tracks
            if prefix in ["viridian", "opening"]:
                song_name = "viridian1.ogg" if prefix == "viridian" else "opening1.ogg"
                song_path = os.path.join(sound_dir, song_name)
            else:
                files = [f for f in os.listdir(sound_dir) if f.startswith(prefix)]
                if not files: return
                song_path = os.path.join(sound_dir, random.choice(files))

            if os.path.exists(song_path):
                pygame.mixer.music.load(song_path)
                pygame.mixer.music.play(-1)
                current_music_theme = prefix # Use the prefix as the theme identifier
            else:
                print(f"Warning: Music file '{song_path}' not found.")
        except Exception as e:
            print(f"Error playing music for prefix '{prefix}': {e}")

    
    music_path = os.path.join(ASSETS_DIR, "sounds", "opening1.ogg")
    play_battle_music("opening")

    # Load Scene Assets (unchanged)
    bg_forest = load_asset("forest1.png", "backgrounds", (WIDTH, HEIGHT))
    bg_route = load_asset("route1.png", "backgrounds", (WIDTH, HEIGHT)) # For non-battle screens
    bg_lab = load_asset("oaklab1.png", "backgrounds")
    if bg_lab:
        scale = WIDTH / bg_lab.get_width()
        new_h = int(bg_lab.get_height() * scale)
        bg_lab = pygame.transform.scale(bg_lab, (WIDTH, new_h))
    bg_viridian = load_asset("viridian1.png", "backgrounds", (WIDTH, HEIGHT))
    spr_oak = load_asset("oak1.png", "pngs", (400, 500))
    spr_gary_overworld = load_asset("gary1.png", "pngs", (400, 400))
    rival_files = ["rival1.png", "rival2.png", "rival3.png"]
    rival_imgs = [load_asset(f, "sprites", (400, 400)) for f in rival_files]
    rival_imgs = [img for img in rival_imgs if img]
    if rival_imgs: spr_gary_battle = random.choice(rival_imgs)
    else: spr_gary_battle = spr_gary_overworld
    bg_mart = load_bg("mart1.png", "backgrounds")
    bg_center = load_bg("center1.png", "backgrounds")
    bg_gym = load_bg("viridian_gym1.png", "backgrounds")
    bg_menu = load_bg("menu.png", "backgrounds")
    spr_joy = load_asset("joy1.png", "pngs", (300, 450))
    spr_grunts = load_asset("grunts_disguise.png", "pngs", (400, 400))
    sfx_blip = load_sound("blip.wav")
    sfx_heal = load_sound("heal.ogg")
    
    # --- Character Selection Data ---
    # Map filenames to Pokemon Showdown IDs for fallback downloading
    trainer_map = {
        "red_back.png": "red",
        "ethan_back.png": "ethan", "lyra_back.png": "lyra",
        "brendan_back.png": "brendan", "may_back.png": "may",
        "lucas_back.png": "lucas", "dawn_back.png": "dawn",
        "hilbert_back.png": "hilbert", "hilda_back.png": "hilda",
        "nate_back.png": "nate", "rosa_back.png": "rosa"
    }
    trainer_filenames = [
        "red_back.png", "ethan_back.png", "lyra_back.png",
        "brendan_back.png", "may_back.png", "lucas_back.png", "dawn_back.png",
        "hilbert_back.png", "hilda_back.png", "nate_back.png", "rosa_back.png"
    ]
    available_trainers = []
    
    for f in trainer_filenames:
        # 1. Load Back Sprite (for Battle)
        back_img = load_asset(f, "sprites", (384, 384))
        
        # 2. Load Front Sprite (for Selector) - Infer filename
        front_f = f.replace("_back.png", ".png")
        front_img = load_asset(front_f, "sprites", (384, 384))
        
        # 3. Web Download Fallback (Showdown)
        showdown_name = trainer_map.get(f, "red")
        if not front_img:
            try:
                url = f"https://play.pokemonshowdown.com/sprites/trainers/{showdown_name}.png"
                raw = requests.get(url).content
                front_img = pygame.image.load(io.BytesIO(raw)).convert_alpha()
                front_img = pygame.transform.scale(front_img, (384, 384))
            except:
                pass
        
        # 4. Final Fallback
        if not back_img: back_img = pygame.Surface((384, 384), pygame.SRCALPHA); pygame.draw.rect(back_img, BLUE, (100, 100, 184, 284))
        if not front_img: front_img = back_img
            
        available_trainers.append({'front': front_img, 'back': back_img})
    
    selected_char_idx = 0
    spr_player = available_trainers[0]['back']
    player_name = ""
    rival_name = ""
    starter_data, enemy_data, rival_starter_data = None, None, None
    starter_id = None
    q_text, options, correct_ans = "", [], ""
    player_hp, enemy_hp = 3, 3
    player_level, enemy_level = 5, 3
    player_xp = 0
    xp_needed = 100
    xp_gain_amount = 0
    visited_center = False
    visited_mart = False
    visited_gym = False
    return_state_from_menu = None
    return_state_after_battle = None
    xp_anim_start_xp = 0
    xp_anim_current_xp = 0
    xp_anim_target_xp = 0
    feedback_text, feedback_color = "", WHITE
    dialogue_index = 0
    loading_phase = 0
    battle_phase = 0
    battle_menu_mode = 0
    chosen_move = None          # ← NEW
    battle_escaped = False
    route1_progress = 0
    next_state = None
    prev_state = None
    transition_bg = None
    transition_type = 0
    battle_bg = None
    transition_data = []
    battle_music_prefix = ""
    char_idx = 0
    text_timer = 0
    current_text = ""
    text_done = False
    anim_phase = 0
    anim_timer = 0
    pos_player = [80, 290]
    pos_starter = [-400, 290]
    pos_enemy = [WIDTH - 420, 100]
    pos_trainer = [WIDTH + 100, HEIGHT - 500]
    oak_script = []
    gary_script = []
    gary_post_script = []
    win_script = []
    oak_dex_script = []
    center_script = []
    center_script_after = []
    mart_script = []
    gym_script = []
    viridian_music_path = os.path.join(ASSETS_DIR, "sounds", "viridian1.ogg")

    menu_btn_rect = pygame.Rect(WIDTH - 120, 20, 100, 50)
    overworld_states = [STATE_VIRIDIAN, STATE_ROUTE1_HUB, STATE_ROUTE1_FROM_VIRIDIAN]

    while running:
        screen.fill(BLACK)

        # --- Music Management ---
        if current_state in [STATE_VIRIDIAN, STATE_POKECENTER, STATE_POKEMART, STATE_VIRIDIAN_GYM]:
            play_battle_music("viridian")
        elif current_state in [STATE_ROUTE1_HUB, STATE_ROUTE1_FROM_VIRIDIAN]:
            play_battle_music("kanto_route")
        elif current_state in [STATE_CHAR_SELECT, STATE_INTRO, STATE_FOREST_EXIT, STATE_RIVAL_INTRO, STATE_RIVAL_NAME_INPUT, STATE_LAB, STATE_LAB_END]:
            play_battle_music("opening")

        mouse_pos = pygame.mouse.get_pos()

        if current_state == STATE_CHAR_SELECT:
            draw_text("CHOOSE YOUR CHARACTER", FONT_MED, WHITE, WIDTH//2, 100)
            
            # Draw current character
            char_img = available_trainers[selected_char_idx]['front']
            char_rect = char_img.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(char_img, char_rect)
            
            # Draw Arrows
            left_arrow_rect = pygame.Rect(WIDTH//2 - 280, HEIGHT//2 - 50, 60, 100)
            right_arrow_rect = pygame.Rect(WIDTH//2 + 220, HEIGHT//2 - 50, 60, 100)
            draw_text("<", FONT_BIG, GOLD, WIDTH//2 - 250, HEIGHT//2)
            draw_text(">", FONT_BIG, GOLD, WIDTH//2 + 250, HEIGHT//2)
            
            # Name Input
            draw_text("ENTER NAME:", FONT_SMALL, WHITE, WIDTH//2, HEIGHT - 210)
            pygame.draw.rect(screen, WHITE, (WIDTH//2 - 150, HEIGHT - 180, 300, 40), 2)
            draw_text(player_name + "_", FONT_UI, GOLD, WIDTH//2, HEIGHT - 160)
            
            start_rect = pygame.Rect(WIDTH//2 - 200, HEIGHT - 130, 400, 60)
            pygame.draw.rect(screen, (20, 20, 20), start_rect, border_radius=10)
            pygame.draw.rect(screen, GREEN, start_rect, 2, border_radius=10)
            draw_text("CLICK HERE TO START", FONT_SMALL, GREEN, WIDTH//2, HEIGHT - 100)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    elif len(player_name) < 10 and event.unicode.isalnum():
                        player_name += event.unicode.upper()

                    if event.key == pygame.K_LEFT:
                        if sfx_blip: sfx_blip.play()
                        selected_char_idx = (selected_char_idx - 1) % len(available_trainers)
                    elif event.key == pygame.K_RIGHT:
                        if sfx_blip: sfx_blip.play()
                        selected_char_idx = (selected_char_idx + 1) % len(available_trainers)
                    elif event.key == pygame.K_RETURN:
                        if sfx_blip: sfx_blip.play()
                        if player_name == "": player_name = "TRAINER"
                        spr_player = available_trainers[selected_char_idx]['back']
                        current_state = STATE_LOADING
                        loading_phase = 0
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if left_arrow_rect.collidepoint(event.pos):
                        if sfx_blip: sfx_blip.play()
                        selected_char_idx = (selected_char_idx - 1) % len(available_trainers)
                    elif right_arrow_rect.collidepoint(event.pos):
                        if sfx_blip: sfx_blip.play()
                        selected_char_idx = (selected_char_idx + 1) % len(available_trainers)
                    elif start_rect.collidepoint(event.pos) or char_rect.collidepoint(event.pos):
                        if sfx_blip: sfx_blip.play()
                        if player_name == "": player_name = "TRAINER"
                        spr_player = available_trainers[selected_char_idx]['back']
                        current_state = STATE_LOADING
                        loading_phase = 0

        elif current_state == STATE_LOADING:
            # Robust Loading System: Retries until data is valid (no squares!)
            if loading_phase == 0:
                draw_text("CATCHING STARTER...", FONT_BIG, WHITE, WIDTH//2, HEIGHT//2)
                pygame.display.flip()
                starter_id = random.choice(ACTIVE_POOL)
                starter_data = fetch_pokemon_data(starter_id, back=True)
                if starter_data[1] != "?????": loading_phase = 1
                else: pygame.time.wait(500) # Wait before retry
            elif loading_phase == 1:
                draw_text("TRACKING POOCHYENA...", FONT_BIG, WHITE, WIDTH//2, HEIGHT//2)
                pygame.display.flip()
                enemy_data = fetch_pokemon_data(261) # Poochyena
                enemy_level = 3
                if enemy_data[1] != "?????": 
                    loading_phase = 2
                else: pygame.time.wait(500)
            elif loading_phase == 2:
                draw_text("SCOUTING RIVAL...", FONT_BIG, WHITE, WIDTH//2, HEIGHT//2)
                pygame.display.flip()
                while True:
                    rid = random.choice(ACTIVE_POOL)
                    if rid != starter_id:
                        rival_starter_data = fetch_pokemon_data(rid)
                        break
                if rival_starter_data[1] != "?????":
                    q_text, options, correct_ans = generate_math_problem(player_level)
                    current_state = STATE_INTRO
                    dialogue_index = 0
                    char_idx = 0; text_timer = 0; current_text = ""; text_done = False

        elif current_state == STATE_INTRO:
            if bg_forest: screen.blit(bg_forest, (0, HEIGHT - bg_forest.get_height()))

            # Text Box
            pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
            pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)

            intro_script = [
                f"One morning, {player_name} was walking alone in the nearby woods.",
                "He was excited to start his Pokémon adventure but had not met with Professor Oak yet.",
                "As he was walking back home, he heard rustling in the bushes."
            ]
            
            target_text = intro_script[dialogue_index]
            if not text_done:
                text_timer += 1
                if text_timer >= 2: # Standard typewriter speed
                    text_timer = 0
                    char_idx += 1
                    if char_idx > len(target_text):
                        char_idx = len(target_text)
                        text_done = True
                    current_text = target_text[:char_idx]
            else:
                current_text = target_text

            draw_multiline_text(current_text, FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100, WIDTH - 100)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                    if text_done:
                        dialogue_index += 1
                        if dialogue_index >= len(intro_script):
                            current_state = STATE_TRANSITION
                            next_state = STATE_ANIM_ENTRY
                            prev_state = STATE_INTRO
                            transition_bg = bg_forest
                            transition_type = random.randint(0, 9)
                            transition_data = []
                            if transition_type == 6: # Grid Dissolve setup
                                transition_data = list(range(32 * 24)) # 32x32px blocks
                                random.shuffle(transition_data)
                            battle_music_prefix = "kanto_wild"
                            battle_bg = load_bg("forest3.png", "backgrounds/battle")
                            anim_timer = 0
                        else:
                            char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                    else:
                        char_idx = len(target_text); text_done = True; current_text = target_text

        elif current_state == STATE_TRANSITION:
            # Draw background based on where we came from or where we are going
            if prev_state == STATE_LAB:
                if bg_lab: screen.blit(bg_lab, (0, (HEIGHT - 200) - bg_lab.get_height()))
            elif transition_bg: 
                screen.blit(transition_bg, (0, HEIGHT - transition_bg.get_height()))
            
            anim_timer += 1
            
            # 1. Play Cry
            if anim_timer == 1:
                play_battle_music(battle_music_prefix)
            
            # 2. Flash Effect (0-60 frames)
            if anim_timer < 20: # Shortened flash for snappiness
                if (anim_timer // 4) % 2 == 0:
                    screen.fill(WHITE, special_flags=pygame.BLEND_ADD)
                else:
                    screen.fill((50, 50, 50), special_flags=pygame.BLEND_SUB)
            
            # 3. Transition Animation (20-80 frames)
            elif anim_timer < 80:
                progress = (anim_timer - 20) / 60
                if progress > 1: progress = 1
                
                if transition_type == 0: # Classic Iris
                    radius = int(1000 * (1 - progress))
                    if radius < 0: radius = 0
                    mask = pygame.Surface((WIDTH, HEIGHT))
                    mask.fill(BLACK)
                    pygame.draw.circle(mask, WHITE, (WIDTH//2, HEIGHT//2), radius)
                    mask.set_colorkey(WHITE)
                    screen.blit(mask, (0, 0))

                elif transition_type == 1: # Horizontal Blinds
                    bars = 10
                    bar_h = HEIGHT / bars
                    fill_h = bar_h * progress
                    for i in range(bars):
                        pygame.draw.rect(screen, BLACK, (0, i * bar_h, WIDTH, fill_h))

                elif transition_type == 2: # Vertical Blinds
                    bars = 16
                    bar_w = WIDTH / bars
                    fill_w = bar_w * progress
                    for i in range(bars):
                        pygame.draw.rect(screen, BLACK, (i * bar_w, 0, fill_w, HEIGHT))

                elif transition_type == 3: # Curtain Close (Horizontal)
                    w = (WIDTH / 2) * progress
                    pygame.draw.rect(screen, BLACK, (0, 0, w, HEIGHT)) # Left
                    pygame.draw.rect(screen, BLACK, (WIDTH - w, 0, w, HEIGHT)) # Right

                elif transition_type == 4: # Barn Door (Vertical)
                    h = (HEIGHT / 2) * progress
                    pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, h)) # Top
                    pygame.draw.rect(screen, BLACK, (0, HEIGHT - h, WIDTH, h)) # Bottom

                elif transition_type == 5: # Wipe Left
                    w = WIDTH * progress
                    pygame.draw.rect(screen, BLACK, (WIDTH - w, 0, w, HEIGHT))

                elif transition_type == 6: # Grid Dissolve
                    # 32x32 pixel blocks. 1024/32 = 32 cols, 768/32 = 24 rows
                    blocks_to_draw = int(len(transition_data) * progress)
                    for i in range(blocks_to_draw):
                        idx = transition_data[i]
                        r, c = divmod(idx, 32)
                        pygame.draw.rect(screen, BLACK, (c * 32, r * 32, 32, 32))

                elif transition_type == 7: # Checkerboard Zoom
                    rows, cols = 12, 16
                    cell_w, cell_h = WIDTH / cols, HEIGHT / rows
                    for r in range(rows):
                        for c in range(cols):
                            if (r + c) % 2 == 0:
                                # Grow black square from center of cell
                                size_w = cell_w * progress
                                size_h = cell_h * progress
                                cx, cy = c * cell_w + cell_w/2, r * cell_h + cell_h/2
                                pygame.draw.rect(screen, BLACK, (cx - size_w/2, cy - size_h/2, size_w, size_h))
                            else:
                                # Grow from outside (inverse)? Or just same. Let's do same but delayed slightly?
                                # Let's just do all cells growing
                                size_w = cell_w * progress
                                size_h = cell_h * progress
                                cx, cy = c * cell_w + cell_w/2, r * cell_h + cell_h/2
                                pygame.draw.rect(screen, BLACK, (cx - size_w/2, cy - size_h/2, size_w, size_h))

                elif transition_type == 8: # Spiral Box In
                    # Draw 4 rects moving in
                    h_margin = (HEIGHT / 2) * progress
                    w_margin = (WIDTH / 2) * progress
                    
                    pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, h_margin)) # Top
                    pygame.draw.rect(screen, BLACK, (0, HEIGHT - h_margin, WIDTH, h_margin)) # Bottom
                    pygame.draw.rect(screen, BLACK, (0, 0, w_margin, HEIGHT)) # Left
                    pygame.draw.rect(screen, BLACK, (WIDTH - w_margin, 0, w_margin, HEIGHT)) # Right

                elif transition_type == 9: # Diamond Close
                    # Draw 4 black triangles in corners growing
                    size = (WIDTH + HEIGHT) * progress # Max size
                    # Top Left
                    pygame.draw.polygon(screen, BLACK, [(0,0), (size, 0), (0, size)])
                    # Top Right
                    pygame.draw.polygon(screen, BLACK, [(WIDTH,0), (WIDTH-size, 0), (WIDTH, size)])
                    # Bottom Left
                    pygame.draw.polygon(screen, BLACK, [(0,HEIGHT), (size, HEIGHT), (0, HEIGHT-size)])
                    # Bottom Right
                    pygame.draw.polygon(screen, BLACK, [(WIDTH,HEIGHT), (WIDTH-size, HEIGHT), (WIDTH, HEIGHT-size)])

            # 4. Start Battle
            else:
                current_state = next_state
                anim_phase = 0
                # Reset positions for slide-in
                if next_state == STATE_ANIM_ENTRY:
                    pos_enemy = [WIDTH + 100, 100]
                    pos_player = [-400, 290]
                    anim_phase = 0
                elif next_state == STATE_ANIM_GARY:
                    pos_enemy = [WIDTH + 100, 100] # Pokemon start pos
                    pos_trainer = [WIDTH + 100, 100] # Rival start pos (Aligned with Pokemon)
                    pos_player = [-400, 290]
                    anim_phase = 0 # 0: Slide In, 1: Wants to battle, 2: Sent out
        
        elif current_state == STATE_ANIM_ENTRY:
            # Draw Background
            if battle_bg:
                screen.blit(battle_bg, (0, (HEIGHT - 200) - battle_bg.get_height()))
            
            # Draw Sprites based on current positions
            screen.blit(enemy_data[0], (pos_enemy[0], pos_enemy[1]))
            screen.blit(spr_player, (pos_player[0], pos_player[1]))
            if anim_phase >= 5:
                screen.blit(starter_data[0], (pos_starter[0], pos_starter[1]))
            
            # Animation Logic
            if anim_phase == 0: # Slide Enemy In
                pos_enemy[0] -= 25
                if pos_enemy[0] <= WIDTH - 420:
                    pos_enemy[0] = WIDTH - 420
                    if enemy_data[2]: enemy_data[2].play()
                    anim_phase = 1
            
            elif anim_phase == 1: # Slide Player In
                pos_player[0] += 25
                if pos_player[0] >= 80:
                    pos_player[0] = 80
                    anim_phase = 2
            
            elif anim_phase == 2: # Enemy Attack (Lunge)
                pos_enemy[0] -= 25
                if pos_enemy[0] <= WIDTH - 600:
                    anim_phase = 3
            
            elif anim_phase == 3: # Enemy Return
                pos_enemy[0] += 25
                if pos_enemy[0] >= WIDTH - 420:
                    pos_enemy[0] = WIDTH - 420
                    anim_phase = 4
                    char_idx = 0; text_timer = 0; current_text = ""; text_done = False
            
            elif anim_phase == 4: # Text Event
                # Draw Text Box
                pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
                pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)
                
                target_text = f"A nearby {starter_data[1]} jumped in to help!"
                if not text_done:
                    text_timer += 1
                    if text_timer >= 2:
                        text_timer = 0
                        char_idx += 1
                        if char_idx > len(target_text): 
                            char_idx = len(target_text); 
                            text_done = True
                        current_text = target_text[:char_idx]
                else: current_text = target_text
                
                draw_multiline_text(current_text, FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100, WIDTH - 100)
            
            elif anim_phase == 5: # Swap Player for Pokemon
                pos_player[0] -= 20 # Player slides out left
                pos_starter[0] += 20 # Pokemon slides in from left
                if pos_starter[0] >= 80:
                    pos_starter[0] = 80
                    current_state = STATE_BATTLE_POOCH
                    battle_escaped = False
                    battle_menu_mode = 0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if anim_phase == 4 and event.type == pygame.MOUSEBUTTONDOWN:
                    if text_done:
                        if sfx_blip: sfx_blip.play()
                        if starter_data[2]: starter_data[2].play()
                        anim_phase = 5
                    else:
                        char_idx = len(target_text); text_done = True; current_text = target_text

        elif current_state == STATE_ANIM_GARY:
            # Shift up to align with top of text box
            if battle_bg: screen.blit(battle_bg, (0, (HEIGHT - 200) - battle_bg.get_height()))
            
            # Draw Sprites
            if anim_phase < 2:
                screen.blit(spr_gary_battle, (pos_trainer[0], pos_trainer[1]))
            else:
                screen.blit(enemy_data[0], (pos_enemy[0], pos_enemy[1]))
            
            # Text Box
            pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
            pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)

            # Animation Logic
            if anim_phase == 0: # Slide Rival In
                pos_trainer[0] -= 25
                if pos_trainer[0] <= WIDTH - 420: # Stop where Pokemon ends up
                    pos_trainer[0] = WIDTH - 420
                    anim_phase = 1
                    char_idx = 0; text_timer = 0; current_text = ""; text_done = False
            
            elif anim_phase == 2: # Slide Rival Out, Pokemon In
                pos_trainer[0] += 25
                pos_enemy[0] -= 25
                if pos_enemy[0] <= WIDTH - 420:
                    pos_enemy[0] = WIDTH - 420
                    if enemy_data[2]: enemy_data[2].play()
                    anim_phase = 3
                    char_idx = 0; text_timer = 0; current_text = ""; text_done = False

            elif anim_phase in [1, 3]: # Text Phases
                if anim_phase == 1: target_text = f"RIVAL {rival_name} wants to battle!"
                else: target_text = f"RIVAL {rival_name} sent out {enemy_data[1]}!"
                
                if not text_done:
                    text_timer += 1
                    if text_timer >= 2:
                        text_timer = 0; 
                        char_idx += 1
                        if char_idx > len(target_text): 
                            char_idx = len(target_text); 
                            text_done = True
                        current_text = target_text[:char_idx]
                else: current_text = target_text
                
                draw_multiline_text(current_text, FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100, WIDTH - 100)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if anim_phase in [1, 3]:
                        if text_done:
                            if sfx_blip: sfx_blip.play()
                            if anim_phase == 1:
                                anim_phase = 2
                            else:
                                # Transition to Battle
                                current_state = STATE_BATTLE_GARY
                                battle_escaped = False
                                battle_menu_mode = 0
                        else:
                            char_idx = len(target_text); text_done = True; current_text = target_text

        elif current_state in [STATE_BATTLE_POOCH, STATE_BATTLE_GARY, STATE_BATTLE_WILD]:
            is_wild = current_state in [STATE_BATTLE_POOCH, STATE_BATTLE_WILD]
            is_trainer = current_state == STATE_BATTLE_GARY

            # Background
            if battle_bg: screen.blit(battle_bg, (0, (HEIGHT - 200) - battle_bg.get_height()))

            # Classic idle bobbing
            bob = int(math.sin(pygame.time.get_ticks() / 150) * 6)

            # Sprites
            enemy_surf = pygame.transform.scale(enemy_data[0], (BATTLE_SCALE, BATTLE_SCALE))
            screen.blit(enemy_surf, (ENEMY_POS[0], ENEMY_POS[1] + bob))

            player_surf = pygame.transform.scale(starter_data[0], (BATTLE_SCALE, BATTLE_SCALE))
            screen.blit(player_surf, (PLAYER_POS[0], PLAYER_POS[1] + bob * 1.2))

            # HP bars (classic positions)
            draw_hp_bar(ENEMY_HP_POS[0], ENEMY_HP_POS[1], enemy_hp, 3, enemy_data[1], enemy_level)
            draw_hp_bar(PLAYER_HP_POS[0], PLAYER_HP_POS[1], player_hp, 3, starter_data[1], player_level, player_xp, xp_needed)

            # Text box
            pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
            pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 6)

            if battle_menu_mode == 0:  # Main battle menu
                draw_text(f"What will {starter_data[1]} do?", FONT_MSG, WHITE, 40, HEIGHT - 150, center=False)

                btn_w, btn_h = 220, 80
                bx, by = WIDTH - 480, HEIGHT - 190
                buttons = [
                    (pygame.Rect(bx, by, btn_w, btn_h), "FIGHT", (200,40,40)),
                    (pygame.Rect(bx + 240, by, btn_w, btn_h), "BAG", (220,160,20)),
                    (pygame.Rect(bx, by + 95, btn_w, btn_h), "POKÉMON", (40,180,60)),
                    (pygame.Rect(bx + 240, by + 95, btn_w, btn_h), "RUN", (60,100,220))
                ]
                for rect, txt, col in buttons:
                    pygame.draw.rect(screen, col, rect, border_radius=12)
                    draw_text(txt, FONT_UI, WHITE, rect.centerx, rect.centery)
                    if rect.collidepoint(mouse_pos):
                        pygame.draw.rect(screen, WHITE, rect, 5, border_radius=12)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT: running = False
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        for rect, txt, _ in buttons:
                            if rect.collidepoint(event.pos):
                                if txt == "FIGHT":
                                    battle_menu_mode = 1
                                elif txt == "RUN":
                                    if is_wild:
                                        if current_state == STATE_BATTLE_POOCH:
                                            current_state = STATE_WIN_POOCH
                                            battle_escaped = True
                                            win_script = ["Got away safely!"]
                                            dialogue_index = 0
                                            char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                                        else:
                                            current_state = STATE_WILD_WIN
                                            win_script = ["Got away safely!"]
                                            dialogue_index = 0
                                            char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                                    else:
                                        feedback_text = "No running from a Trainer battle!"

            elif battle_menu_mode == 1:  # Move selection (feels exactly like real Pokémon)
                moves = [
                    ("ADD TACKLE", "+", "easy"),
                    ("SUB SLASH", "-", "medium"),
                    ("MULTI BLAST", "x", "hard"),
                    ("EQUATION GUARD", "+", "easy")
                ]
                draw_text(f"Choose {starter_data[1]}'s attack!", FONT_MSG, YELLOW, 40, HEIGHT - 160, center=False)

                move_buttons = []
                btn_w, btn_h = 240, 70
                for i, (name, op, diff) in enumerate(moves):
                    x = 80 + (i % 2) * 280
                    y = HEIGHT - 170 + (i // 2) * 85
                    rect = pygame.Rect(x, y, btn_w, btn_h)
                    move_buttons.append((rect, name, op, diff))
                    pygame.draw.rect(screen, (50,50,80), rect, border_radius=12)
                    draw_text(name, FONT_UI, WHITE, rect.centerx, rect.centery)
                    if rect.collidepoint(mouse_pos):
                        pygame.draw.rect(screen, GOLD, rect, 6, border_radius=12)

                # Back Button
                back_arrow_rect = pygame.Rect(WIDTH - 80, HEIGHT - 140, 60, 120)
                draw_text("<", FONT_BIG, WHITE, back_arrow_rect.centerx, back_arrow_rect.centery)
                if back_arrow_rect.collidepoint(mouse_pos):
                    draw_text("<", FONT_BIG, GOLD, back_arrow_rect.centerx, back_arrow_rect.centery)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT: running = False
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if back_arrow_rect.collidepoint(event.pos):
                            battle_menu_mode = 0
                            continue
                        for rect, name, op, diff in move_buttons:
                            if rect.collidepoint(event.pos):
                                chosen_move = (name, op, diff)
                                q_text, options, correct_ans = generate_math_problem(player_level)
                                battle_menu_mode = 2
                                feedback_text = f"{starter_data[1]} used {name}!"

            elif battle_menu_mode == 2:  # Math solving phase
                draw_text(feedback_text, FONT_MSG, YELLOW, 40, HEIGHT - 160, center=False)
                draw_text(q_text, FONT_MSG, WHITE, 40, HEIGHT - 110, center=False)

                answer_buttons = []
                for i, opt in enumerate(options):
                    bx = 620 + (i % 2 * 190)
                    by = HEIGHT - 170 + (i // 2 * 75)
                    rect = pygame.Rect(bx, by, 170, 65)
                    answer_buttons.append((rect, opt))
                    pygame.draw.rect(screen, (40,40,40), rect, border_radius=12)
                    pygame.draw.rect(screen, GOLD if rect.collidepoint(mouse_pos) else WHITE, rect, 4, border_radius=12)
                    draw_text(opt, FONT_UI, WHITE, rect.centerx, rect.centery)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT: running = False
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        for rect, opt in answer_buttons:
                            if rect.collidepoint(event.pos):
                                if opt == correct_ans:
                                    dmg = 2 if "MULTI" in chosen_move[0] else 1
                                    enemy_hp -= dmg
                                    feedback_text = "CRITICAL HIT!!" if random.random() < 0.3 else "Great math!"
                                else:
                                    player_hp -= 1
                                    feedback_text = "The attack missed..."

                                battle_menu_mode = 0
                                q_text, options, correct_ans = generate_math_problem(player_level)

                                if enemy_hp <= 0:
                                    if current_state == STATE_BATTLE_GARY:
                                        current_state = STATE_RIVAL_FAINT
                                        pos_enemy = list(ENEMY_POS)
                                    elif current_state == STATE_BATTLE_POOCH:
                                        current_state = STATE_POOCH_FLEE
                                        pos_enemy = list(ENEMY_POS)
                                        anim_phase = 0
                                    else:  # STATE_BATTLE_WILD
                                        current_state = STATE_WILD_WIN
                                        # XP Gain
                                        xp_gain_amount = (enemy_data[3] * enemy_level) // 7
                                        win_script = [f"Wild {enemy_data[1]} fainted!", f"{starter_data[1]} gained {xp_gain_amount} EXP. Points!"]
                                        xp_anim_start_xp = player_xp
                                        xp_anim_target_xp = player_xp + xp_gain_amount
                                        player_xp = xp_anim_target_xp # Update model
                                        
                                        dialogue_index = 0
                                        char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                                    if enemy_data[2]: enemy_data[2].play()
                                    play_battle_music("kanto_win")

        elif current_state == STATE_POOCH_FLEE:
            if battle_bg: screen.blit(battle_bg, (0, (HEIGHT - 200) - battle_bg.get_height()))

            # Player is always visible
            player_surf = pygame.transform.scale(starter_data[0], (BATTLE_SCALE, BATTLE_SCALE))
            screen.blit(player_surf, (PLAYER_POS[0], PLAYER_POS[1]))

            # Text Box is always visible
            pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
            pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)

            if anim_phase == 0: # Poochyena runs away
                # Draw Enemy Fleeing
                enemy_surf = pygame.transform.scale(enemy_data[0], (BATTLE_SCALE, BATTLE_SCALE))
                screen.blit(enemy_surf, (pos_enemy[0], pos_enemy[1]))
                pos_enemy[0] += 25
                
                draw_text(f"The wild {enemy_data[1]} fled!", FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100)
                
                if pos_enemy[0] > WIDTH:
                    anim_phase = 1
                    # Reset text animation variables for the next phase
                    char_idx = 0; text_timer = 0; current_text = ""; text_done = False
            
            elif anim_phase == 1: # New dialogue
                target_text = f"The {starter_data[1]} looks at you gratefully. It wants to join your team!"
                if not text_done:
                    text_timer += 1
                    if text_timer >= 2:
                        text_timer = 0; char_idx += 1
                        if char_idx > len(target_text): char_idx = len(target_text); text_done = True
                        current_text = target_text[:char_idx]
                else: current_text = target_text
                draw_multiline_text(current_text, FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100, WIDTH - 100)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if anim_phase == 1:
                        if text_done:
                            current_state = STATE_WIN_POOCH
                            player_xp += 50
                            win_script = [f"The {starter_data[1]} has joined your team!", f"{starter_data[1]} gained 50 EXP. Points!"]
                            dialogue_index = 0
                            char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                        else:
                            char_idx = len(target_text); text_done = True; current_text = target_text

        elif current_state == STATE_RIVAL_FAINT:
            if battle_bg: screen.blit(battle_bg, (0, (HEIGHT - 200) - battle_bg.get_height()))
            
            screen.blit(starter_data[0], (PLAYER_POS[0], PLAYER_POS[1]))
            
            # Sink Enemy
            enemy_surf = pygame.transform.scale(enemy_data[0], (BATTLE_SCALE, BATTLE_SCALE))
            screen.blit(enemy_surf, (ENEMY_POS[0], pos_enemy[1]))
            
            pos_enemy[1] += 10
            
            pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
            pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)
            draw_text(f"{enemy_data[1]} fainted!", FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100)
            
            if pos_enemy[1] > HEIGHT - 200:
                current_state = STATE_GARY_EXIT
                pos_enemy = [WIDTH + 100, HEIGHT - 500] # Reset for Gary slide in
                anim_phase = 0
                gary_post_script = [
                    f"{rival_name}: What? Unbelievable!",
                    f"{rival_name}: I picked the wrong Pokemon!",
                    f"{rival_name}: Smell ya later!"
                ]
                dialogue_index = 0
                char_idx = 0; text_timer = 0; current_text = ""; text_done = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False

        elif current_state == STATE_WIN_POOCH:
            if battle_bg: screen.blit(battle_bg, (0, (HEIGHT - 200) - battle_bg.get_height()))
            screen.blit(starter_data[0], (80, 250))
            
            pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
            pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)
            
            target_text = win_script[dialogue_index]
            if not text_done:
                text_timer += 1
                if text_timer >= 2:
                    text_timer = 0
                    char_idx += 1
                    if char_idx > len(target_text): 
                        char_idx = len(target_text); 
                        text_done = True
                    current_text = target_text[:char_idx]
            else: current_text = target_text
            
            draw_multiline_text(current_text, FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100, WIDTH - 100)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if text_done:
                        if sfx_blip: sfx_blip.play()
                        dialogue_index += 1
                        if dialogue_index >= len(win_script):
                            player_hp = 3 # Restore HP
                            current_state = STATE_FOREST_EXIT
                            dialogue_index = 0
                            char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                        else:
                            char_idx = 0; text_timer = 0; current_text = ""; text_done = False

        elif current_state == STATE_FOREST_EXIT:
            if bg_forest: screen.blit(bg_forest, (0, HEIGHT - bg_forest.get_height()))
            
            pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
            pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)
            
            forest_script = [
                f"With the wild POOCHYENA scared off, {player_name} and {starter_data[1]} made their way out of the woods.",
                "They headed towards the town, safe and sound."
            ]
            
            target_text = forest_script[dialogue_index]
            if not text_done:
                text_timer += 1
                if text_timer >= 2:
                    text_timer = 0; char_idx += 1
                    if char_idx > len(target_text): 
                        char_idx = len(target_text); 
                        text_done = True
                    current_text = target_text[:char_idx]
            else: current_text = target_text
            
            draw_multiline_text(current_text, FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100, WIDTH - 100)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if text_done:
                        if sfx_blip: sfx_blip.play()
                        dialogue_index += 1
                        if dialogue_index >= len(forest_script):
                            current_state = STATE_RIVAL_INTRO
                            dialogue_index = 0
                            starter_name = starter_data[1]
                            oak_script = [
                                f"On the way back, {player_name} ran into Professor Oak and explained what happened.",
                                f"OAK: Incredible! You handled that POOCHYENA with ease, {player_name}!",
                                f"OAK: I'm Professor Oak. That {starter_name} seems to really like you!",
                                "OAK: Come with me to my Lab. I have a gift for you.",
                                "OAK: My grandson is waiting there too.",
                                "OAK: ...Erm, what was his name again?"
                            ]
                        char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                    else: char_idx = len(target_text); text_done = True; current_text = target_text

        elif current_state == STATE_GARY_EXIT:
            if bg_lab: screen.blit(bg_lab, (0, (HEIGHT - 200) - bg_lab.get_height()))
            
            # Phase 0: Slide In
            if anim_phase == 0:
                pos_enemy[0] -= 25
                if pos_enemy[0] <= WIDTH - 450:
                    pos_enemy[0] = WIDTH - 450
                    anim_phase = 1
            
            # Phase 2: Slide Out
            elif anim_phase == 2:
                pos_enemy[0] += 25
                if pos_enemy[0] > WIDTH:
                    player_hp = 3 # Restore HP
                    current_state = STATE_LAB_END
                    dialogue_index = 0
                    oak_dex_script = [
                        f"OAK: Ah, {rival_name} left in a huff. But you battled excellently!",
                        "OAK: Take this POKEDEX! It automatically records data on Pokemon you've seen or caught!",
                        "OAK: It's a hi-tech encyclopedia!",
                        "OAK: I've also linked it to your PC. You can swap Pokemon using the Pokedex!",
                        "OAK: Good luck on your journey to become a Pokemon Master!"
                    ]
            
            # Draw Gary
            if spr_gary_overworld: screen.blit(spr_gary_overworld, (pos_enemy[0], pos_enemy[1]))
            
            # Phase 1: Dialogue
            if anim_phase == 1:
                pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
                pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)
                
                target_text = gary_post_script[dialogue_index]
                
                if not text_done:
                    text_timer += 1
                    if text_timer >= 2: # Typing speed
                        text_timer = 0
                        char_idx += 1
                        if char_idx > len(target_text):
                            char_idx = len(target_text)
                            text_done = True
                        current_text = target_text[:char_idx]
                else:
                    current_text = target_text
                
                draw_multiline_text(current_text, FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100, WIDTH - 100)

            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if anim_phase == 1:
                        if text_done:
                            if sfx_blip: sfx_blip.play()
                            dialogue_index += 1
                            if dialogue_index >= len(gary_post_script):
                                anim_phase = 2
                            else:
                                char_idx = 0
                                text_timer = 0
                                current_text = ""
                                text_done = False
                        else:
                            char_idx = len(target_text); text_done = True; current_text = target_text

        elif current_state == STATE_RIVAL_INTRO:
            if bg_route: screen.blit(bg_route, (0, HEIGHT - bg_route.get_height()))
            if spr_oak: screen.blit(spr_oak, (WIDTH//2 - 200, HEIGHT - 500))
            
            pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
            pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)
            
            if dialogue_index < len(oak_script):
                target_text = oak_script[dialogue_index]
                if not text_done:
                    text_timer += 1
                    if text_timer >= 2:
                        text_timer = 0
                        char_idx += 1
                        if char_idx > len(target_text): 
                            char_idx = len(target_text); 
                            text_done = True
                        current_text = target_text[:char_idx]
                else:
                    current_text = target_text
            
            draw_multiline_text(current_text, FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100, WIDTH - 100)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if text_done:
                        if sfx_blip: sfx_blip.play()
                        dialogue_index += 1
                        if dialogue_index >= len(oak_script):
                            current_state = STATE_RIVAL_NAME_INPUT
                        else:
                            char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                    else:
                        char_idx = len(target_text); text_done = True; current_text = target_text

        elif current_state == STATE_RIVAL_NAME_INPUT:
            if bg_route: screen.blit(bg_route, (0, HEIGHT - bg_route.get_height()))
            if spr_oak: screen.blit(spr_oak, (WIDTH//2 - 200, HEIGHT - 500))
            
            # Darken background for input focus
            s = pygame.Surface((WIDTH, HEIGHT))
            s.set_alpha(150); s.fill(BLACK)
            screen.blit(s, (0,0))
            
            draw_text("WHAT IS HIS NAME?", FONT_MED, WHITE, WIDTH//2, HEIGHT//2 - 50)
            pygame.draw.rect(screen, WHITE, (WIDTH//2 - 150, HEIGHT//2, 300, 40), 2)
            draw_text(rival_name + "_", FONT_UI, GOLD, WIDTH//2, HEIGHT//2 + 20)
            draw_text("PRESS ENTER TO CONFIRM", FONT_SMALL, GREEN, WIDTH//2, HEIGHT//2 + 80)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        rival_name = rival_name[:-1]
                    elif len(rival_name) < 10 and event.unicode.isalnum():
                        rival_name += event.unicode.upper()
                    elif event.key == pygame.K_RETURN:
                        if sfx_blip: sfx_blip.play()
                        if rival_name == "": rival_name = "GARY"
                        current_state = STATE_LAB
                        dialogue_index = 0
                        
                        # --- Generate Lab Scripts ---
                        insult_adjs = ["dumb", "goofy", "clumsy", "silly", "weird", "stinky", "boring", "smelly", "sloppy", "slow"]
                        insult_nouns = ["pipsqueak", "clown", "amateur", "noodle-head", "ding-dong", "dork", "nerd", "loser", "trukey-brain", "blockhead"]
                        insult = f"{random.choice(insult_adjs)} {random.choice(insult_nouns)}"
                        
                        oak_script = [
                            f"OAK: Ah, yes! {rival_name}! Let's go inside."
                        ]
                        gary_pre_battle_script = [
                            f"{rival_name}: Gramps! Who's the new kid? {player_name}? They look like a {insult}.",
                            f"{rival_name}: You think you're a trainer? I've been training for hours!",
                            f"{rival_name}: I just got a new Pokemon too. Let's settle this right now!",
                            f"{rival_name}: You'll see how a REAL trainer handles himself in battle! Go, {rival_starter_data[1]}!"
                        ]

        elif current_state == STATE_LAB:
            # Determine Background and Speaker based on script progress
            if dialogue_index < len(oak_script):
                if bg_route: screen.blit(bg_route, (0, HEIGHT - bg_route.get_height()))
                if spr_oak: screen.blit(spr_oak, (WIDTH//2 - 200, HEIGHT - 500))
            else:
                if bg_lab: screen.blit(bg_lab, (0, (HEIGHT - 200) - bg_lab.get_height()))
                if spr_gary_overworld: screen.blit(spr_gary_overworld, (WIDTH//2 - 200, HEIGHT - 500))

            # Dialogue Box
            pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
            pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)
            
            full_script = oak_script + gary_pre_battle_script
            if dialogue_index < len(full_script):
                target_text = full_script[dialogue_index]
                if not text_done:
                    text_timer += 1
                    if text_timer >= 2: # Consistent speed
                        text_timer = 0
                        char_idx += 1
                        if char_idx > len(target_text): 
                            char_idx = len(target_text); 
                            text_done = True
                        current_text = target_text[:char_idx]
                else:
                    current_text = target_text
            
            draw_multiline_text(current_text, FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100, WIDTH - 100)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if text_done:
                        if sfx_blip: sfx_blip.play()
                        dialogue_index += 1
                        if dialogue_index >= len(full_script):
                            enemy_data = rival_starter_data
                            enemy_hp, player_hp = 3, 3
                            enemy_level = 5
                            current_state = STATE_TRANSITION
                            next_state = STATE_ANIM_GARY
                            prev_state = STATE_LAB
                            transition_bg = bg_lab
                            transition_type = random.randint(0, 9)
                            transition_data = []
                            if transition_type == 6:
                                transition_data = list(range(32 * 24))
                                random.shuffle(transition_data)
                            battle_music_prefix = "kanto_trainer"
                            battle_bg = load_bg("oaklab.png", "backgrounds/battle")
                            anim_timer = 0
                            feedback_text = f"{rival_name} sent out {enemy_data[1]}!"
                            char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                        else:
                            char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                    else:
                        char_idx = len(target_text); text_done = True; current_text = target_text

        elif current_state == STATE_LAB_END:
            if bg_lab: screen.blit(bg_lab, (0, (HEIGHT - 200) - bg_lab.get_height()))
            if spr_oak: screen.blit(spr_oak, (WIDTH//2 - 200, HEIGHT - 500))
            
            pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
            pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)
            
            if dialogue_index < len(oak_dex_script):
                target_text = oak_dex_script[dialogue_index]
                if not text_done:
                    text_timer += 1
                    if text_timer >= 2:
                        text_timer = 0
                        char_idx += 1
                        if char_idx > len(target_text): 
                            char_idx = len(target_text); 
                            text_done = True
                        current_text = target_text[:char_idx]
                else:
                    current_text = target_text
            
            draw_multiline_text(current_text, FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100, WIDTH - 100)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if text_done:
                        if sfx_blip: sfx_blip.play()
                        dialogue_index += 1
                        if dialogue_index >= len(oak_dex_script):
                            current_state = STATE_TRANSITION
                            next_state = STATE_ROUTE1_HUB
                            prev_state = STATE_LAB
                            transition_bg = bg_lab
                            transition_type = 4 # Barn Door fade
                            battle_music_prefix = "kanto_route"
                            anim_timer = 0
                            route1_progress = 0
                        else:
                            char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                    else:
                        char_idx = len(target_text); text_done = True; current_text = target_text

        elif current_state == STATE_ROUTE1_HUB:
            if bg_route: screen.blit(bg_route, (0, HEIGHT - bg_route.get_height()))

            # Draw Menu Button
            pygame.draw.rect(screen, WHITE, menu_btn_rect, border_radius=8)
            draw_text("MENU", FONT_UI, BLACK, menu_btn_rect.centerx, menu_btn_rect.centery)
            if menu_btn_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, GOLD, menu_btn_rect, 4, border_radius=8)
            
            if route1_progress < 3:
                # Proceed Button
                btn_rect = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 - 40, 400, 80)
                pygame.draw.rect(screen, GREEN if btn_rect.collidepoint(mouse_pos) else WHITE, btn_rect, border_radius=12) 
                draw_multiline_text("PROCEED THROUGH ROUTE 1", FONT_UI, BLACK, btn_rect.centerx, btn_rect.centery, btn_rect.width - 20)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: running = False
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if menu_btn_rect.collidepoint(event.pos):
                            return_state_from_menu = current_state
                            current_state = STATE_MENU
                            continue
                        if btn_rect.collidepoint(event.pos):
                            if sfx_blip: sfx_blip.play()
                            current_state = STATE_LOADING_WILD
            else:
                # Almost there text
                draw_text("Almost to Viridian City...", FONT_BIG, WHITE, WIDTH//2, HEIGHT//2)
                draw_text("(Click to continue)", FONT_SMALL, WHITE, WIDTH//2, HEIGHT//2 + 50)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: running = False
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        current_state = STATE_TRANSITION
                        next_state = STATE_VIRIDIAN
                        prev_state = STATE_ROUTE1_HUB
                        transition_bg = bg_route
                        transition_type = 0
                        anim_timer = 0

        elif current_state == STATE_LOADING_WILD:
            if bg_route: screen.blit(bg_route, (0, HEIGHT - bg_route.get_height()))
            draw_text("A wild Pokemon appeared!", FONT_BIG, WHITE, WIDTH//2, HEIGHT//2)
            pygame.display.flip()
            
            # Route 1 Pool
            # 016 (33%), 019 (33%), 020 (1%), 043 (8%), 069 (8%), 161 (8%), 162 (1%), 163 (8%)
            pool = [16, 19, 20, 43, 69, 161, 162, 163]
            weights = [33, 33, 1, 8, 8, 8, 1, 8]
            
            # Weighted choice
            wild_id = random.choices(pool, weights=weights, k=1)[0]
            
            enemy_data = fetch_pokemon_data(wild_id)
            enemy_hp = 3
            enemy_level = random.randint(2, 4)
            
            # Setup Battle
            q_text, options, correct_ans = generate_math_problem(player_level)
            battle_menu_mode = 0
            feedback_text = ""
            
            # Transition to Battle
            current_state = STATE_TRANSITION
            next_state = STATE_BATTLE_WILD
            prev_state = STATE_ROUTE1_HUB
            transition_bg = bg_route
            transition_type = random.randint(0, 9)
            battle_bg = load_bg("grass1.png", "backgrounds/battle")
            battle_music_prefix = "kanto_wild"
            anim_timer = 0

        elif current_state == STATE_WILD_WIN:
            if battle_bg: screen.blit(battle_bg, (0, (HEIGHT - 200) - battle_bg.get_height()))
            # Draw the HP bar with the XP value *before* the gain, so it doesn't jump.
            draw_hp_bar(600, 450, player_hp, 3, starter_data[1], player_level, xp_anim_start_xp, xp_needed)
            screen.blit(starter_data[0], (80, 250))
            
            pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
            pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)
            
            target_text = win_script[dialogue_index]
            if not text_done:
                text_timer += 1
                if text_timer >= 2:
                    text_timer = 0; char_idx += 1
                    if char_idx > len(target_text): char_idx = len(target_text); text_done = True
                    current_text = target_text[:char_idx]
            else: current_text = target_text
            
            draw_multiline_text(current_text, FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100, WIDTH - 100)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if text_done:
                        if sfx_blip: sfx_blip.play()
                        dialogue_index += 1
                        if dialogue_index >= len(win_script):
                            current_state = STATE_XP_GAIN
                            xp_anim_current_xp = xp_anim_start_xp
                            next_state = STATE_ROUTE1_HUB
                            prev_state = STATE_BATTLE_WILD
                        else:
                            char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                    else: char_idx = len(target_text); text_done = True; current_text = target_text

        elif current_state == STATE_XP_GAIN:
            # Determine background from previous battle state
            if battle_bg: screen.blit(battle_bg, (0, (HEIGHT - 200) - battle_bg.get_height()))
            
            # Draw player pokemon and animating XP bar
            screen.blit(starter_data[0], (80, 250))
            
            # Animate XP bar
            if xp_anim_current_xp < xp_anim_target_xp:
                # Make animation speed proportional to total gain to keep it reasonably fast
                speed = max(1, xp_gain_amount // 25)
                xp_anim_current_xp += speed
                if xp_anim_current_xp > xp_anim_target_xp:
                    xp_anim_current_xp = xp_anim_target_xp
            
            # Draw HP/XP bar with the animating value. HP is static here.
            draw_hp_bar(600, 450, player_hp, 3, starter_data[1], player_level, xp_anim_current_xp, xp_needed)
            
            # Draw Text Box
            pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
            pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)
            draw_text(f"{starter_data[1]} gained {xp_gain_amount} EXP. Points!", FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if xp_anim_current_xp < xp_anim_target_xp:
                        xp_anim_current_xp = xp_anim_target_xp
                    else:
                        if player_xp >= xp_needed:
                            current_state = STATE_LEVEL_UP
                        else:
                            if return_state_after_battle:
                                current_state = return_state_after_battle
                                return_state_after_battle = None
                            else:
                                if next_state == STATE_ROUTE1_HUB:
                                    route1_progress += 1
                                current_state = next_state

        elif current_state == STATE_LEVEL_UP:
            # Draw BG (same as XP gain)
            if battle_bg: screen.blit(battle_bg, (0, (HEIGHT - 200) - battle_bg.get_height()))
            screen.blit(starter_data[0], (80, 250))
            
            # Draw HP Bar (Full XP)
            draw_hp_bar(600, 450, player_hp, 3, starter_data[1], player_level, xp_needed, xp_needed)
            
            # Text Box
            pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
            pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)
            draw_text(f"{starter_data[1]} grew to Lv. {player_level + 1}!", FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if sfx_blip: sfx_blip.play()
                    player_level += 1
                    player_xp -= xp_needed
                    xp_needed = int(xp_needed * 1.2)
                    
                    # Exit Logic
                    if return_state_after_battle:
                        current_state = return_state_after_battle
                        return_state_after_battle = None
                    else:
                        if next_state == STATE_ROUTE1_HUB:
                            route1_progress += 1
                        current_state = next_state

        elif current_state == STATE_VIRIDIAN:
            if bg_viridian: screen.blit(bg_viridian, (0, HEIGHT - bg_viridian.get_height()))
            draw_text("VIRIDIAN CITY", FONT_BIG, WHITE, WIDTH//2, 100)

            # Draw Menu Button
            pygame.draw.rect(screen, WHITE, menu_btn_rect, border_radius=8)
            draw_text("MENU", FONT_UI, BLACK, menu_btn_rect.centerx, menu_btn_rect.centery)
            if menu_btn_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, GOLD, menu_btn_rect, 4, border_radius=8)

            center_btn = pygame.Rect(WIDTH//2 - 200, HEIGHT//2, 400, 80)
            mart_btn = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 + 100, 400, 80)
            gym_btn = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 + 200, 400, 80)
            forest_btn = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 + 300, 190, 80)
            route1_btn = pygame.Rect(WIDTH//2 + 10, HEIGHT//2 + 300, 190, 80)

            pygame.draw.rect(screen, GREEN if center_btn.collidepoint(mouse_pos) else WHITE, center_btn, border_radius=12)
            draw_multiline_text("POKÉMON CENTER", FONT_UI, BLACK, center_btn.centerx, center_btn.centery, center_btn.width - 20)

            pygame.draw.rect(screen, GREEN if mart_btn.collidepoint(mouse_pos) else WHITE, mart_btn, border_radius=12)
            draw_multiline_text("POKÉMART", FONT_UI, BLACK, mart_btn.centerx, mart_btn.centery, mart_btn.width - 20)

            if visited_center and visited_mart:
                pygame.draw.rect(screen, GREEN if gym_btn.collidepoint(mouse_pos) else WHITE, gym_btn, border_radius=12)
                draw_multiline_text("CHALLENGE GYM LEADER", FONT_UI, BLACK, gym_btn.centerx, gym_btn.centery, gym_btn.width - 20)
            
            if visited_gym:
                pygame.draw.rect(screen, GREEN if forest_btn.collidepoint(mouse_pos) else WHITE, forest_btn, border_radius=12)
                draw_text("VIRIDIAN FOREST", FONT_SMALL, BLACK, forest_btn.centerx, forest_btn.centery)
                pygame.draw.rect(screen, GREEN if route1_btn.collidepoint(mouse_pos) else WHITE, route1_btn, border_radius=12)
                draw_text("ROUTE 1", FONT_SMALL, BLACK, route1_btn.centerx, route1_btn.centery)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if menu_btn_rect.collidepoint(event.pos):
                        return_state_from_menu = current_state
                        current_state = STATE_MENU
                    elif center_btn.collidepoint(event.pos):
                        current_state = STATE_POKECENTER
                        anim_phase = 0
                        pos_trainer = [-400, HEIGHT - 500] # For Joy sprite
                        dialogue_index = 0
                        char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                        center_script = [f"Welcome to the Viridian City Pokémon Center, {player_name}!", "Let me restore your Pokémon to full health."]
                    elif mart_btn.collidepoint(event.pos):
                        current_state = STATE_POKEMART
                        dialogue_index = 0
                        char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                        if not visited_mart:
                            mart_script = ["Welcome to the PokéMart!", "To help you on your new journey, please take these!", "(You received 5 Pokéballs and 5 Potions!)", "Good luck out there!"]
                        else:
                            mart_script = ["Welcome back to the PokéMart!"]
                    elif visited_center and visited_mart and gym_btn.collidepoint(event.pos):
                        current_state = STATE_VIRIDIAN_GYM
                        anim_phase = 0
                        pos_trainer = [-400, HEIGHT - 500] # For Grunts
                        dialogue_index = 0
                        char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                        insult = f"{random.choice(['dumb', 'goofy', 'clumsy'])} {random.choice(['pipsqueak', 'clown', 'amateur'])}"
                        gym_script = [
                            "GRUNTS: Hey! What do you want, kid?",
                            f"GRUNTS: This is the Viridian City Gym! It's closed! Scram, you {insult}!",
                            "GRUNTS: The Gym Leader is away on... very important business!",
                            "GRUNTS: If you're so desperate for a battle, go to the Viridian Forest and find your way to Pewter City.",
                            "GRUNTS: Now get out of our sight!"
                        ]
                    elif visited_gym and route1_btn.collidepoint(event.pos):
                        current_state = STATE_ROUTE1_FROM_VIRIDIAN

        elif current_state == STATE_POKECENTER:
            if bg_center: screen.blit(bg_center, (0,0))

            if anim_phase == 0: # Joy slides in
                visited_center = True
                pos_trainer[0] += 20
                if pos_trainer[0] >= WIDTH//2 - 200:
                    pos_trainer[0] = WIDTH//2 - 200
                    anim_phase = 1
            
            if anim_phase >= 1 and spr_joy:
                screen.blit(spr_joy, pos_trainer)

            if anim_phase == 1: # Dialogue before heal
                pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
                pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)
                target_text = center_script[dialogue_index]
                if not text_done:
                    text_timer += 1
                    if text_timer >= 2:
                        text_timer = 0; char_idx += 1
                        if char_idx > len(target_text): char_idx = len(target_text); text_done = True
                        current_text = target_text[:char_idx]
                else: current_text = target_text
                draw_multiline_text(current_text, FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100, WIDTH - 100)

            elif anim_phase == 2: # Healing
                anim_timer += 1
                pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
                pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)
                draw_text("Healing your Pokémon...", FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100)
                if anim_timer > 180:
                    anim_phase = 3
                    dialogue_index = 0
                    char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                    center_script_after = ["All better! Your Pokémon are happy and healthy.", "You should check out the PokéMart next door if you haven't!"]

            elif anim_phase == 3: # Dialogue after heal
                pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
                pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)
                target_text = center_script_after[dialogue_index]
                if not text_done:
                    text_timer += 1
                    if text_timer >= 2:
                        text_timer = 0; char_idx += 1
                        if char_idx > len(target_text): char_idx = len(target_text); text_done = True
                        current_text = target_text[:char_idx]
                else: current_text = target_text
                draw_multiline_text(current_text, FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100, WIDTH - 100)

            elif anim_phase == 4: # Show button
                mart_btn = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 + 100, 400, 80)
                pygame.draw.rect(screen, GREEN if mart_btn.collidepoint(mouse_pos) else WHITE, mart_btn, border_radius=12)
                draw_multiline_text("GO TO POKÉMART", FONT_UI, BLACK, mart_btn.centerx, mart_btn.centery, mart_btn.width - 20)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if anim_phase == 1:
                        if text_done:
                            dialogue_index += 1
                            if dialogue_index >= len(center_script):
                                anim_phase = 2
                                if sfx_heal: sfx_heal.play()
                                player_hp = 3 # Heal
                                anim_timer = 0
                            else: char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                        else: char_idx = len(target_text); text_done = True; current_text = target_text
                    elif anim_phase == 3:
                        if text_done:
                            dialogue_index += 1
                            if dialogue_index >= len(center_script_after): anim_phase = 4
                            else: char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                        else: char_idx = len(target_text); text_done = True; current_text = target_text
                    elif anim_phase == 4 and mart_btn.collidepoint(event.pos):
                        current_state = STATE_POKEMART
                        dialogue_index = 0
                        char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                        mart_script = ["Welcome to the PokéMart!", "To help you on your new journey, please take these!", "(You received 5 Pokéballs and 5 Potions!)", "Good luck out there!"]

        elif current_state == STATE_POKEMART:
            if bg_mart: screen.blit(bg_mart, (0,0))
            visited_mart = True
            
            pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
            pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)
            
            if dialogue_index < len(mart_script):
                target_text = mart_script[dialogue_index]
                if not text_done:
                    text_timer += 1
                    if text_timer >= 2:
                        text_timer = 0; char_idx += 1
                        if char_idx > len(target_text): char_idx = len(target_text); text_done = True
                        current_text = target_text[:char_idx]
                else: current_text = target_text
                draw_multiline_text(current_text, FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100, WIDTH - 100)
            else:
                # After dialogue, show a leave button
                leave_btn = pygame.Rect(WIDTH//2 - 150, HEIGHT//2, 300, 80)
                pygame.draw.rect(screen, GREEN if leave_btn.collidepoint(mouse_pos) else WHITE, leave_btn, border_radius=12)
                draw_text("LEAVE", FONT_UI, BLACK, leave_btn.centerx, leave_btn.centery)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if dialogue_index < len(mart_script):
                        if text_done:
                            dialogue_index += 1
                            char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                        else:
                            char_idx = len(target_text); text_done = True; current_text = target_text
                    else: # Leave button is showing
                        leave_btn = pygame.Rect(WIDTH//2 - 150, HEIGHT//2, 300, 80)
                        if leave_btn.collidepoint(event.pos):
                            current_state = STATE_VIRIDIAN

        elif current_state == STATE_VIRIDIAN_GYM:
            if bg_gym: screen.blit(bg_gym, (0,0))

            if anim_phase == 0: # Grunts slide in
                pos_trainer[0] += 20
                if pos_trainer[0] >= WIDTH//2 - 200:
                    pos_trainer[0] = WIDTH//2 - 200
                    anim_phase = 1
            
            if anim_phase >= 1 and spr_grunts:
                screen.blit(spr_grunts, pos_trainer)

            if anim_phase == 1: # Dialogue
                pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
                pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)
                target_text = gym_script[dialogue_index]
                if not text_done:
                    text_timer += 1
                    if text_timer >= 2:
                        text_timer = 0; char_idx += 1
                        if char_idx > len(target_text): char_idx = len(target_text); text_done = True
                        current_text = target_text[:char_idx]
                else: current_text = target_text
                draw_multiline_text(current_text, FONT_MSG, WHITE, WIDTH//2, HEIGHT - 100, WIDTH - 100)
            
            elif anim_phase == 2: # Show leave button
                leave_btn = pygame.Rect(WIDTH//2 - 150, HEIGHT//2, 300, 80)
                pygame.draw.rect(screen, GREEN if leave_btn.collidepoint(mouse_pos) else WHITE, leave_btn, border_radius=12)
                draw_text("LEAVE GYM", FONT_UI, BLACK, leave_btn.centerx, leave_btn.centery)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if anim_phase == 1:
                        if text_done:
                            dialogue_index += 1
                            if dialogue_index >= len(gym_script):
                                anim_phase = 2
                                visited_gym = True
                            else: char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                        else: char_idx = len(target_text); text_done = True; current_text = target_text
                    elif anim_phase == 2 and leave_btn.collidepoint(event.pos):
                        current_state = STATE_VIRIDIAN

        elif current_state == STATE_ROUTE1_FROM_VIRIDIAN:
            if bg_route: screen.blit(bg_route, (0, HEIGHT - bg_route.get_height()))

            # Draw Menu Button
            pygame.draw.rect(screen, WHITE, menu_btn_rect, border_radius=8)
            draw_text("MENU", FONT_UI, BLACK, menu_btn_rect.centerx, menu_btn_rect.centery)
            if menu_btn_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, GOLD, menu_btn_rect, 4, border_radius=8)

            look_btn = pygame.Rect(WIDTH//2 - 200, HEIGHT//2, 400, 80)
            city_btn = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 + 100, 400, 80)

            pygame.draw.rect(screen, GREEN if look_btn.collidepoint(mouse_pos) else WHITE, look_btn, border_radius=12)
            draw_multiline_text("LOOK FOR POKÉMON", FONT_UI, BLACK, look_btn.centerx, look_btn.centery, look_btn.width - 20)

            pygame.draw.rect(screen, GREEN if city_btn.collidepoint(mouse_pos) else WHITE, city_btn, border_radius=12)
            draw_multiline_text("RETURN TO VIRIDIAN CITY", FONT_UI, BLACK, city_btn.centerx, city_btn.centery, city_btn.width - 20)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if menu_btn_rect.collidepoint(event.pos):
                        return_state_from_menu = current_state
                        current_state = STATE_MENU
                    elif look_btn.collidepoint(event.pos):
                        current_state = STATE_LOADING_WILD
                        return_state_after_battle = STATE_ROUTE1_FROM_VIRIDIAN
                    elif city_btn.collidepoint(event.pos):
                        current_state = STATE_VIRIDIAN

        elif current_state == STATE_MENU:
            if bg_menu: screen.blit(bg_menu, (0,0))
            else: screen.fill(DARK_GREEN) # Fallback bg

            draw_text("MENU", FONT_BIG, WHITE, WIDTH//2, 80)

            menu_items = ["POKÉMON", "POKÉDEX", "BACKPACK", "SAVE", "OPTIONS", "LEAVE"]
            menu_buttons = []
            btn_w, btn_h = 400, 60
            start_y = HEIGHT // 2 - (len(menu_items) * (btn_h + 15)) // 2 + 50

            for i, item in enumerate(menu_items):
                rect = pygame.Rect(WIDTH//2 - btn_w//2, start_y + i * (btn_h + 15), btn_w, btn_h)
                menu_buttons.append((rect, item))
                
                pygame.draw.rect(screen, (60, 60, 90), rect, border_radius=15)
                if rect.collidepoint(mouse_pos):
                    pygame.draw.rect(screen, GOLD, rect, 5, border_radius=15)
                else:
                    pygame.draw.rect(screen, WHITE, rect, 3, border_radius=15)
                draw_text(item, FONT_UI, WHITE, rect.centerx, rect.centery)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for rect, item in menu_buttons:
                        if rect.collidepoint(event.pos):
                            if item == "LEAVE":
                                current_state = return_state_from_menu

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
    return False # Signal quit

if __name__ == "__main__":
    while main():
        pass