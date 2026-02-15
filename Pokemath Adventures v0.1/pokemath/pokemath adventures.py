import pygame
import random
import requests
import io
import os

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

def generate_math_easy():
    """Simple math for early game (under 10). Includes reverse logic."""
    a, b = random.randint(1, 4), random.randint(1, 5)
    target = a + b
    
    # Randomly choose between solving for sum or finding equation
    if random.random() < 0.5:
        # Normal: 5 + 1 = ?
        question = f"SOLVE: {a} + {b} = ?"
        ans = str(target)
        options = [ans]
        while len(options) < 4:
            wrong = str(random.randint(1, 9))
            if wrong not in options: options.append(wrong)
    else:
        # Reverse: ? = 6
        question = f"WHICH EQUALS {target}?"
        ans = f"{a} + {b}"
        options = [ans]
        while len(options) < 4:
            wa, wb = random.randint(1, 4), random.randint(1, 5)
            if wa + wb != target:
                weq = f"{wa} + {wb}"
                if weq not in options: options.append(weq)
                
    random.shuffle(options)
    return question, options, ans

def draw_hp_bar(x, y, current_hp, max_hp, name, level, current_xp=None, max_xp=None):
    """B2W2 Slanted HP bar."""
    points = [(x, y), (x + 350, y), (x + 320, y + 80), (x - 30, y + 80)]
    pygame.draw.polygon(screen, (60, 60, 60), points)
    pygame.draw.polygon(screen, WHITE, points, 3)
    draw_text(name, FONT_UI, WHITE, x + 20, y + 25, center=False)
    draw_text(f"Lv. {level}", FONT_UI, WHITE, x + 240, y + 25, center=False)
    pygame.draw.rect(screen, BLACK, (x + 20, y + 55, 250, 12))
    hp_pct = max(0, current_hp / max_hp)
    bar_col = HP_GREEN if hp_pct > 0.5 else HP_YELLOW if hp_pct > 0.2 else HP_RED
    pygame.draw.rect(screen, bar_col, (x + 20, y + 55, 250 * hp_pct, 12))
    
    # Draw XP Bar (Player Only)
    if current_xp is not None and max_xp is not None:
        xp_pct = min(1, current_xp / max_xp)
        pygame.draw.rect(screen, BLUE, (x + 20, y + 72, 250 * xp_pct, 6))

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

def play_battle_music(prefix):
    try:
        sound_dir = os.path.join(ASSETS_DIR, "sounds")
        files = [f for f in os.listdir(sound_dir) if f.startswith(prefix)]
        if files:
            pygame.mixer.music.load(os.path.join(sound_dir, random.choice(files)))
            pygame.mixer.music.play(-1)
    except: pass

# --- Main Game Loop ---
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
    
    current_state = STATE_CHAR_SELECT
    clock = pygame.time.Clock()
    running = True
    
    music_path = os.path.join(ASSETS_DIR, "sounds", "opening1.ogg")
    if os.path.exists(music_path):
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.play(-1) # Loop indefinitely
    else:
        print(f"Warning: Music file '{music_path}' not found.")

    # Load Scene Assets
    bg_forest = load_asset("forest1.png", "backgrounds", (WIDTH, HEIGHT))
    
    # Load battle backgrounds proportionally to avoid distortion
    bg_forest_battle = load_asset("forest_battle1.png", "backgrounds")
    if bg_forest_battle:
        scale = WIDTH / bg_forest_battle.get_width()
        new_h = int(bg_forest_battle.get_height() * scale)
        bg_forest_battle = pygame.transform.scale(bg_forest_battle, (WIDTH, new_h))

    bg_route = load_asset("route1.png", "backgrounds", (WIDTH, HEIGHT))
    
    bg_lab = load_asset("oaklab1.png", "backgrounds")
    if bg_lab:
        scale = WIDTH / bg_lab.get_width()
        new_h = int(bg_lab.get_height() * scale)
        bg_lab = pygame.transform.scale(bg_lab, (WIDTH, new_h))

    spr_oak = load_asset("oak1.png", "pngs", (400, 500))
    
    spr_gary_overworld = load_asset("gary1.png", "pngs", (400, 400))
    
    # Randomly select rival sprite for battle
    rival_files = ["rival1.png", "rival2.png", "rival3.png"]
    rival_imgs = [load_asset(f, "sprites", (400, 400)) for f in rival_files]
    rival_imgs = [img for img in rival_imgs if img] # Filter out missing files
    if rival_imgs: spr_gary_battle = random.choice(rival_imgs)
    else: spr_gary_battle = spr_gary_overworld
    
    sfx_blip = load_sound("blip.wav")
    
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
        if not back_img:
            # Note: Showdown mainly has front sprites easily. We might just use front for back if missing, or try to find back.
            # For now, assuming local back sprites exist as per user.
            pass
            
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

    # Interaction variables
    starter_data, enemy_data, rival_starter_data = None, None, None
    starter_id = None
    q_text, options, correct_ans = "", [], ""
    player_hp, enemy_hp = 3, 3
    player_level, enemy_level = 5, 3
    player_xp = 0
    xp_needed = 100 # Placeholder for Level 5 -> 6
    feedback_text, feedback_color = "", WHITE
    dialogue_index = 0
    loading_phase = 0 # 0: Starter, 1: Enemy, 2: Done
    loading_timer = 0
    battle_phase = 0 # 0: Intro, 1: Battle
    battle_menu_mode = 0 # 0: Main Menu, 1: Fight/Math
    
    battle_escaped = False
    # Transition variables
    next_state = None
    prev_state = None # To know which background to draw during transition
    transition_bg = None
    transition_type = 0
    transition_data = [] # For complex transitions like dissolve
    battle_music_prefix = ""
    
    # Typewriter variables
    char_idx = 0
    text_timer = 0
    current_text = ""
    text_done = False
    
    # Animation Variables
    anim_phase = 0
    anim_timer = 0
    # Coordinates: [x, y]
    pos_player = [80, 250]
    pos_starter = [-400, 250] # Starts off-screen left
    pos_enemy = [WIDTH - 420, 20]
    pos_trainer = [WIDTH + 100, HEIGHT - 500]

    # Script placeholders (populated dynamically)
    oak_script = []
    gary_script = []
    gary_post_script = []
    win_script = []

    oak_dex_script = []

    def draw_lab_bg():
        # Light Yellow Walls
        screen.fill((255, 255, 224))
        
        # Scientific Machinery (Background)
        pygame.draw.rect(screen, (180, 180, 180), (100, 100, 120, 300)) # Machine L
        pygame.draw.rect(screen, (50, 50, 50), (110, 120, 100, 80)) # Screen
        pygame.draw.circle(screen, RED, (120, 220), 5)
        pygame.draw.circle(screen, GREEN, (140, 220), 5)
        
        pygame.draw.rect(screen, (180, 180, 180), (800, 100, 120, 300)) # Machine R
        pygame.draw.rect(screen, (100, 200, 255), (820, 150, 80, 200)) # Tank
        
        # Floor (White Tile with Grid)
        pygame.draw.rect(screen, WHITE, (0, 300, WIDTH, HEIGHT-300))
        for x in range(0, WIDTH, 100):
            pygame.draw.line(screen, (220, 220, 220), (x, 300), (x, HEIGHT))
        for y in range(300, HEIGHT, 50):
            pygame.draw.line(screen, (220, 220, 220), (0, y), (WIDTH, y))
            
        # Platforms (Circle with Dark Yellow Border)
        pygame.draw.ellipse(screen, WHITE, (50, 450, 450, 150))
        pygame.draw.ellipse(screen, (204, 204, 0), (50, 450, 450, 150), 5)
        pygame.draw.ellipse(screen, WHITE, (550, 200, 400, 100))
        pygame.draw.ellipse(screen, (204, 204, 0), (550, 200, 400, 100), 5)

    while running:
        screen.fill(BLACK)

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
                    q_text, options, correct_ans = generate_math_easy()
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
                    pos_enemy = [WIDTH + 100, 20]
                    pos_player = [-400, 250]
                    anim_phase = 0
                elif next_state == STATE_ANIM_GARY:
                    pos_enemy = [WIDTH + 100, 20] # Pokemon start pos
                    pos_trainer = [WIDTH + 100, 20] # Rival start pos (Aligned with Pokemon)
                    pos_player = [-400, 250]
                    anim_phase = 0 # 0: Slide In, 1: Wants to battle, 2: Sent out
        
        elif current_state == STATE_ANIM_ENTRY:
            # Draw Background
            # Shift up to align with top of text box (HEIGHT - 200)
            if bg_forest_battle: screen.blit(bg_forest_battle, (0, (HEIGHT - 200) - bg_forest_battle.get_height()))
            
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
            # Draw Procedural Lab Background
            draw_lab_bg()
            
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

        elif current_state in [STATE_BATTLE_POOCH, STATE_BATTLE_GARY]:
            if current_state == STATE_BATTLE_POOCH and bg_forest_battle:
                screen.blit(bg_forest_battle, (0, (HEIGHT - 200) - bg_forest_battle.get_height()))
            elif current_state == STATE_BATTLE_GARY:
                # Draw Procedural Lab Background
                draw_lab_bg()

            screen.blit(enemy_data[0], (WIDTH - 420, 20))
            screen.blit(starter_data[0], (80, 250))
            
            draw_hp_bar(100, 100, enemy_hp, 3, enemy_data[1], enemy_level, None, None)
            draw_hp_bar(600, 450, player_hp, 3, starter_data[1], player_level, player_xp, xp_needed)

            # Draw Bottom UI Box
            pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
            pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)
            
            if battle_menu_mode == 0:
                # --- MAIN BATTLE MENU (Gen 4 Style) ---
                draw_text(f"What will {starter_data[1]} do?", FONT_MSG, WHITE, 50, HEIGHT - 150, center=False)
                if feedback_text:
                    draw_text(feedback_text, FONT_UI, feedback_color, 50, HEIGHT - 100, center=False)
                
                # Buttons: Fight (Red), Bag (Yellow), Pokemon (Green), Run (Blue)
                btn_width, btn_height = 180, 70
                start_x, start_y = WIDTH - 400, HEIGHT - 180
                
                # Define Rects
                btn_fight = pygame.Rect(start_x, start_y, btn_width, btn_height)
                btn_bag = pygame.Rect(start_x + 190, start_y, btn_width, btn_height)
                btn_pkmn = pygame.Rect(start_x, start_y + 80, btn_width, btn_height)
                btn_run = pygame.Rect(start_x + 190, start_y + 80, btn_width, btn_height)
                
                # Draw Buttons
                pygame.draw.rect(screen, (200, 40, 40), btn_fight, border_radius=10) # Red
                draw_text("FIGHT", FONT_UI, WHITE, btn_fight.centerx, btn_fight.centery)
                
                pygame.draw.rect(screen, (220, 160, 20), btn_bag, border_radius=10) # Yellow
                draw_text("BAG", FONT_UI, WHITE, btn_bag.centerx, btn_bag.centery)
                
                pygame.draw.rect(screen, (40, 180, 60), btn_pkmn, border_radius=10) # Green
                draw_text("POKEMON", FONT_UI, WHITE, btn_pkmn.centerx, btn_pkmn.centery)
                
                pygame.draw.rect(screen, (60, 100, 220), btn_run, border_radius=10) # Blue
                draw_text("RUN", FONT_UI, WHITE, btn_run.centerx, btn_run.centery)
                
                # Highlight Hover
                for btn in [btn_fight, btn_bag, btn_pkmn, btn_run]:
                    if btn.collidepoint(mouse_pos):
                        pygame.draw.rect(screen, WHITE, btn, 4, border_radius=10)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT: running = False
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if btn_fight.collidepoint(event.pos):
                            battle_menu_mode = 1
                            feedback_text = ""
                        elif btn_bag.collidepoint(event.pos) or btn_pkmn.collidepoint(event.pos):
                            feedback_text, feedback_color = "You have no items or other Pokemon!", WHITE
                        elif btn_run.collidepoint(event.pos):
                            if current_state == STATE_BATTLE_POOCH:
                                current_state = STATE_WIN_POOCH
                                battle_escaped = True
                                win_script = ["Got away safely!"]
                                dialogue_index = 0
                                char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                            else:
                                feedback_text, feedback_color = "No! There's no running from a Trainer battle!", WHITE

            elif battle_menu_mode == 1:
                # --- MATH BATTLE MODE ---
                draw_text(q_text, FONT_MSG, YELLOW, 50, HEIGHT - 150, center=False)

                button_rects = []
                for i, opt in enumerate(options):
                    bx, by = 650 + (i % 2 * 160), (HEIGHT - 160) + (i // 2 * 60)
                    rect = pygame.Rect(bx, by, 140, 50)
                    button_rects.append((rect, opt))
                    pygame.draw.rect(screen, (60, 60, 60), rect, border_radius=5)
                    pygame.draw.rect(screen, GOLD if rect.collidepoint(mouse_pos) else WHITE, rect, 2, border_radius=5)
                    draw_text(opt, FONT_UI, WHITE, rect.centerx, rect.centery)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT: running = False
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        for rect, opt in button_rects:
                            if rect.collidepoint(event.pos):
                                if opt == correct_ans:
                                    enemy_hp -= 1
                                    feedback_text, feedback_color = "CRITICAL HIT!", GREEN
                                    battle_menu_mode = 0 # Return to menu
                                    if enemy_hp <= 0:
                                        if current_state == STATE_BATTLE_POOCH:
                                            if enemy_data[2]: enemy_data[2].play()
                                            play_battle_music("kanto_win")
                                            current_state = STATE_POOCH_FLEE
                                            pos_enemy = [WIDTH - 420, 20]
                                        else:
                                            if enemy_data[2]: enemy_data[2].play()
                                            play_battle_music("kanto_win")
                                            current_state = STATE_RIVAL_FAINT
                                            pos_enemy = [WIDTH - 420, 20]
                                            win_script = [
                                                f"Rival's {enemy_data[1]} fainted!",
                                                f"You defeated RIVAL {rival_name}!"
                                            ]
                                            dialogue_index = 0
                                            char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                                else:
                                    player_hp -= 1
                                    feedback_text, feedback_color = "IT BIT YOU!", RED
                                    battle_menu_mode = 0 # Return to menu
                                    if player_hp <= 0: return True # Signal restart
                                q_text, options, correct_ans = generate_math_easy()

        elif current_state == STATE_POOCH_FLEE:
            if bg_forest_battle: screen.blit(bg_forest_battle, (0, (HEIGHT - 200) - bg_forest_battle.get_height()))
            screen.blit(starter_data[0], (80, 250))
            screen.blit(enemy_data[0], (pos_enemy[0], pos_enemy[1]))
            
            pos_enemy[0] += 25
            if pos_enemy[0] > WIDTH:
                current_state = STATE_WIN_POOCH
                
                # XP Calculation
                if not battle_escaped:
                    xp_gain = (enemy_data[3] * enemy_level) // 7
                    player_xp += xp_gain
                    # Simple level up check (visual only for now)
                    if player_xp >= xp_needed: player_xp = xp_needed

                win_script = [
                    f"Wild {enemy_data[1]} fainted!",
                    f"{player_name} escaped safely..."
                ]
                dialogue_index = 0
                char_idx = 0; text_timer = 0; current_text = ""; text_done = False

        elif current_state == STATE_RIVAL_FAINT:
            # Draw Procedural Lab Background
            draw_lab_bg()
            
            screen.blit(starter_data[0], (80, 250))
            screen.blit(enemy_data[0], (pos_enemy[0], pos_enemy[1]))
            
            pos_enemy[0] += 25
            if pos_enemy[0] > WIDTH:
                current_state = STATE_RIVAL_WIN_TEXT
                
                # XP Calculation
                if not battle_escaped:
                    xp_gain = (enemy_data[3] * enemy_level) // 7
                    player_xp += xp_gain
                    if player_xp >= xp_needed: player_xp = xp_needed

                char_idx = 0; text_timer = 0; current_text = ""; text_done = False

        elif current_state == STATE_RIVAL_WIN_TEXT:
            # Draw Procedural Lab Background
            draw_lab_bg()
            screen.blit(starter_data[0], (80, 250))

            pygame.draw.rect(screen, BLACK, (0, HEIGHT - 200, WIDTH, 200))
            pygame.draw.rect(screen, WHITE, (0, HEIGHT - 200, WIDTH, 200), 4)
            
            target_text = win_script[dialogue_index]
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
                    if text_done:
                        if sfx_blip: sfx_blip.play()
                        dialogue_index += 1
                        if dialogue_index >= len(win_script):
                            current_state = STATE_GARY_EXIT
                            dialogue_index = 0
                            anim_phase = 0
                            pos_enemy = [WIDTH + 200, HEIGHT - 500] # Reset for slide in (Overworld height)
                            gary_post_script = [
                                f"{rival_name}: WHAT? Unbelievable! My {enemy_data[1]} lost?!",
                                f"{rival_name}: You just got lucky, {player_name}. Don't get used to it!",
                                f"{rival_name}: I'm going to become the world's strongest trainer!",
                                f"{rival_name}: Smell ya later, {player_name}!"
                            ]
                            char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                        else:
                            char_idx = 0; text_timer = 0; current_text = ""; text_done = False

        elif current_state == STATE_WIN_POOCH:
            if bg_forest_battle: screen.blit(bg_forest_battle, (0, (HEIGHT - 200) - bg_forest_battle.get_height()))
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
                            f"{rival_name}: You'll see how a REAL trainer handles himself in battle! Go, {enemy_data[1]}!"
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
                            current_state = STATE_FINAL_WIN
                        else:
                            char_idx = 0; text_timer = 0; current_text = ""; text_done = False
                    else:
                        char_idx = len(target_text); text_done = True; current_text = target_text

        elif current_state == STATE_FINAL_WIN:
            draw_text(f"{rival_name}: NO WAY! I LOST?!", FONT_MED, RED, WIDTH//2, 150)
            draw_text("RIVAL DEFEATED", FONT_BIG, GOLD, WIDTH//2, HEIGHT//2 - 50)
            replay_btn = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 100, 300, 80)
            pygame.draw.rect(screen, GREEN if replay_btn.collidepoint(mouse_pos) else WHITE, replay_btn, border_radius=12)
            draw_text("REPLAY ADVENTURE", FONT_SMALL, BLACK, replay_btn.centerx, replay_btn.centery)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if replay_btn.collidepoint(event.pos): return True # Signal restart

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
    return False # Signal quit

if __name__ == "__main__":
    while main():
        pass