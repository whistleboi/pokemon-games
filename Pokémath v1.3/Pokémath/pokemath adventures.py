import pygame
import random
import requests
import io
import os

# --- System Initialization ---
pygame.mixer.pre_init(44100, -16, 2, 4096)
pygame.init()
pygame.mixer.init()

# Use dynamic display info or fixed window
WIDTH, HEIGHT = 1024, 768
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pokémath Adventures - Kanto Ironmon Engine")

# Colors
WHITE, BLACK = (255, 255, 255), (10, 10, 10)
GREEN, RED, YELLOW, GOLD = (50, 255, 50), (255, 50, 50), (255, 255, 0), (255, 215, 0)
DARK_GREEN, GRAY = (34, 139, 34), (50, 50, 50)

# Fonts
FONT_BIG = pygame.font.SysFont("impact", 64)
FONT_MED = pygame.font.SysFont("impact", 48)
FONT_SMALL = pygame.font.SysFont("arial", 24, bold=True)

# --- Ironmon Map Config (from TSX/CSS) ---
KANTO_WIDTH = 7700
KANTO_HEIGHT = 6400
# Starting translation from React state: { x: -2500, y: -2000 }
START_X, START_Y = 2500, 2000

class IronmonMapEngine:
    def __init__(self):
        self.show_routes = True
        # Emulating .full-map-img and .svg-container absolute positioning
        self.base_map = self.load_asset("FullKanto.png", (KANTO_WIDTH, KANTO_HEIGHT), DARK_GREEN)
        self.path_map = self.load_asset("FullKantoPaths.png", (KANTO_WIDTH, KANTO_HEIGHT), None)
        
    def load_asset(self, filename, size, fallback_color):
        try:
            img = pygame.image.load(filename).convert_alpha()
            return pygame.transform.scale(img, size)
        except:
            surf = pygame.Surface(size, pygame.SRCALPHA)
            if fallback_color: surf.fill(fallback_color)
            return surf

    def render(self, surface, player_world_pos):
        # Camera Calculation (Translation Logic)
        offset_x = WIDTH // 2 - player_world_pos[0]
        offset_y = HEIGHT // 2 - player_world_pos[1]
        
        # Layer 1: Ground (.full-map-img)
        surface.blit(self.base_map, (offset_x, offset_y))
        
        # Layer 2: Paths (Conditional rendering from TSX)
        if self.show_routes and self.path_map:
            surface.blit(self.path_map, (offset_x, offset_y))

def draw_text(text, font, text_col, x, y, center=True):
    img = font.render(text, True, text_col)
    rect = img.get_rect()
    if center: rect.center = (x, y)
    else: rect.topleft = (x, y)
    screen.blit(img, rect)

# --- Main Game Loop ---
def main():
    STATE_LOADING = "LOADING"
    STATE_WORLD = "WORLD"
    STATE_BATTLE = "BATTLE" # Placeholder for future encounters
    
    current_state = STATE_LOADING
    clock = pygame.time.Clock()
    running = True

    # Map Engine and Player State
    map_engine = None
    player_pos = [START_X, START_Y]
    velocity = 8

    while running:
        screen.fill(BLACK)
        
        if current_state == STATE_LOADING:
            draw_text("SYNCING KANTO COORDINATES...", FONT_MED, WHITE, WIDTH//2, HEIGHT//2)
            pygame.display.flip()
            map_engine = IronmonMapEngine()
            current_state = STATE_WORLD

        elif current_state == STATE_WORLD:
            # 1. Input Handling
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:  player_pos[0] -= velocity
            if keys[pygame.K_RIGHT]: player_pos[0] += velocity
            if keys[pygame.K_UP]:    player_pos[1] -= velocity
            if keys[pygame.K_DOWN]:  player_pos[1] += velocity
            
            # Boundary Clamping (Locked to 7700x6400)
            player_pos[0] = max(0, min(player_pos[0], KANTO_WIDTH))
            player_pos[1] = max(0, min(player_pos[1], KANTO_HEIGHT))

            # 2. Rendering Layers (Simulating Z-Index)
            map_engine.render(screen, player_pos)

            # Layer 3: Player Sprite (Centered Viewport)
            pygame.draw.rect(screen, RED, (WIDTH//2 - 15, HEIGHT//2 - 15, 30, 30))
            pygame.draw.rect(screen, WHITE, (WIDTH//2 - 15, HEIGHT//2 - 15, 30, 30), 2)

            # Layer 4: React Portal Container (UI Overlay)
            # This layer never moves with the map
            pygame.draw.rect(screen, (0, 0, 0, 150), (10, 10, 280, 100))
            draw_text(f"X: {int(player_pos[0])} Y: {int(player_pos[1])}", FONT_SMALL, GOLD, 20, 30, False)
            draw_text("IRONMON MAP ACTIVE", FONT_SMALL, WHITE, 20, 60, False)
            draw_text("[R] TOGGLE ROUTES", FONT_SMALL, GREEN, 20, 85, False)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        map_engine.show_routes = not map_engine.show_routes

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()