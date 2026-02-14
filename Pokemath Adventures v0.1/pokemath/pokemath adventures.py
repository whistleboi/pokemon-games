import pygame
import random
import requests
import io

# --- System Initialization ---
pygame.mixer.pre_init(44100, -16, 2, 4096)
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1024, 768
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pokémath Adventures - B2W2 Edition")

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
STARTER_IDS_BY_GEN = {
    "gen1": [1, 4, 7], "gen2": [152, 155, 158], "gen3": [252, 255, 258],
    "gen4": [387, 390, 393], "gen5": [495, 498, 501], "gen6": [650, 653, 656],
    "gen7": [722, 725, 728], "gen8": [810, 813, 816], "gen9": [906, 909, 912]
}
FULL_STARTER_POOL = [pid for gen in STARTER_IDS_BY_GEN.values() for pid in gen]

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
        try:
            cry_url = response["cries"]["latest"]
            audio_resp = requests.get(cry_url).content
            cry_sound = pygame.mixer.Sound(io.BytesIO(audio_resp))
        except: pass
        return image, name, cry_sound
    except: return None

def generate_math_easy():
    """Simple math for early game (under 10)."""
    a, b = random.randint(1, 5), random.randint(1, 4)
    target = a + b
    question, ans = f"SOLVE: {a} + {b} = ?", str(target)
    options = [ans]
    while len(options) < 4:
        wrong = str(random.randint(1, 10))
        if wrong not in options: options.append(wrong)
    random.shuffle(options)
    return question, options, ans

def draw_hp_bar(x, y, current_hp, max_hp, name):
    """B2W2 Slanted HP bar."""
    points = [(x, y), (x + 350, y), (x + 320, y + 80), (x - 30, y + 80)]
    pygame.draw.polygon(screen, (60, 60, 60), points)
    pygame.draw.polygon(screen, WHITE, points, 3)
    draw_text(name, FONT_UI, WHITE, x + 20, y + 25, center=False)
    pygame.draw.rect(screen, BLACK, (x + 20, y + 55, 250, 12))
    hp_pct = max(0, current_hp / max_hp)
    bar_col = HP_GREEN if hp_pct > 0.5 else HP_YELLOW if hp_pct > 0.2 else HP_RED
    pygame.draw.rect(screen, bar_col, (x + 20, y + 55, 250 * hp_pct, 12))

# --- Main Game Loop ---
def main():
    STATE_LOADING, STATE_INTRO, STATE_BATTLE_POOCH = "LOADING", "INTRO", "BATTLE_POOCH"
    STATE_WIN_POOCH, STATE_LAB, STATE_BATTLE_GARY, STATE_FINAL_WIN = "WIN_POOCH", "LAB", "BATTLE_GARY", "FINAL_WIN"
    
    current_state = STATE_LOADING
    clock = pygame.time.Clock()
    running = True

    # Interaction variables
    starter_data, enemy_data = None, None
    q_text, options, correct_ans = "", [], ""
    player_hp, enemy_hp = 3, 3
    feedback_text, feedback_color = "", WHITE
    dialogue_index = 0

    oak_script = [
        "OAK: Incredible! You handled that wild Pokemon with ease.",
        "OAK: I'm Professor Oak. That Pokemon seems to really like you!",
        "OAK: Come with me to my Lab. I have a gift for you."
    ]
    gary_script = [
        "GARY: Gramps! Who's the new kid? They look like a total amateur.",
        "GARY: You think you're a trainer? I've been training for hours!",
        "GARY: I just got a new Pokemon too. Let's settle this right now!",
        "GARY: Smell ya later! Go, my Pokemon!"
    ]

    while running:
        screen.fill(BLACK)
        mouse_pos = pygame.mouse.get_pos()

        if current_state == STATE_LOADING:
            draw_text("FETCHING DATA...", FONT_BIG, WHITE, WIDTH//2, HEIGHT//2)
            pygame.display.flip()
            starter_data = fetch_pokemon_data(random.choice(FULL_STARTER_POOL), back=True)
            enemy_data = fetch_pokemon_data(261) # Poochyena
            q_text, options, correct_ans = generate_math_easy()
            current_state = STATE_INTRO

        elif current_state == STATE_INTRO:
            draw_text("You are walking alone in the woods...", FONT_MED, WHITE, WIDTH//2, HEIGHT//2 - 50)
            draw_text("Suddenly, a Poochyena lunges at you!", FONT_SMALL, RED, WIDTH//2, HEIGHT//2 + 20)
            draw_text("PRESS SPACE TO CALL FOR HELP", FONT_SMALL, GOLD, WIDTH//2, HEIGHT//2 + 100)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    current_state = STATE_BATTLE_POOCH
                    if enemy_data[2]: enemy_data[2].play()

        elif current_state in [STATE_BATTLE_POOCH, STATE_BATTLE_GARY]:
            pygame.draw.ellipse(screen, (100, 100, 100), (50, 450, 450, 150))
            pygame.draw.ellipse(screen, (100, 100, 100), (550, 200, 400, 100))
            screen.blit(enemy_data[0], (WIDTH - 420, 20))
            screen.blit(starter_data[0], (80, 250))
            
            draw_hp_bar(100, 100, enemy_hp, 3, enemy_data[1])
            draw_hp_bar(600, 450, player_hp, 3, starter_data[1])

            pygame.draw.rect(screen, (30, 30, 30), (0, 600, WIDTH, 168))
            pygame.draw.rect(screen, WHITE, (0, 600, WIDTH, 168), 4)
            draw_text(feedback_text, FONT_MSG, feedback_color, 50, 640, center=False)
            draw_text(q_text, FONT_MSG, YELLOW, 50, 700, center=False)

            button_rects = []
            for i, opt in enumerate(options):
                bx, by = 650 + (i % 2 * 160), 630 + (i // 2 * 60)
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
                                if enemy_hp <= 0:
                                    current_state = STATE_WIN_POOCH if current_state == STATE_BATTLE_POOCH else STATE_FINAL_WIN
                            else:
                                player_hp -= 1
                                feedback_text, feedback_color = "IT BIT YOU!", RED
                                if player_hp <= 0: main()
                            q_text, options, correct_ans = generate_math_easy()

        elif current_state == STATE_WIN_POOCH:
            draw_text("POOCHYENA FLED!", FONT_MED, GREEN, WIDTH//2, HEIGHT//2)
            draw_text("CLICK TO FOLLOW PROFESSOR OAK", FONT_SMALL, WHITE, WIDTH//2, HEIGHT//2 + 80)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    current_state = STATE_LAB
                    dialogue_index = 0

        elif current_state == STATE_LAB:
            pygame.draw.rect(screen, BLUE, (50, HEIGHT - 200, WIDTH - 100, 150), border_radius=15)
            pygame.draw.rect(screen, WHITE, (50, HEIGHT - 200, WIDTH - 100, 150), 3, border_radius=15)
            full_script = oak_script + gary_script
            if dialogue_index < len(full_script):
                draw_text(full_script[dialogue_index], FONT_SMALL, WHITE, WIDTH//2, HEIGHT - 125)
                draw_text("CLICK TO CONTINUE", FONT_SMALL, GOLD, WIDTH - 200, HEIGHT - 80)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    dialogue_index += 1
                    if dialogue_index == len(oak_script): # Transition to Gary's reveal
                        enemy_data = fetch_pokemon_data(random.choice(FULL_STARTER_POOL))
                        enemy_hp, player_hp = 3, 3
                    if dialogue_index >= len(full_script):
                        current_state = STATE_BATTLE_GARY
                        feedback_text = f"Gary sent out {enemy_data[1]}!"

        elif current_state == STATE_FINAL_WIN:
            draw_text("GARY: NO WAY! I LOST?!", FONT_MED, RED, WIDTH//2, 150)
            draw_text("CHAMPION DEFEATED", FONT_BIG, GOLD, WIDTH//2, HEIGHT//2 - 50)
            replay_btn = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 100, 300, 80)
            pygame.draw.rect(screen, GREEN if replay_btn.collidepoint(mouse_pos) else WHITE, replay_btn, border_radius=12)
            draw_text("REPLAY ADVENTURE", FONT_SMALL, BLACK, replay_btn.centerx, replay_btn.centery)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if replay_btn.collidepoint(event.pos): main()

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()

if __name__ == "__main__":
    main()