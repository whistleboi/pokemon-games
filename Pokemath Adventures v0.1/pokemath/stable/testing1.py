import pygame
import random
import os
import math
from dataclasses import dataclass
from typing import List, Callable, Tuple

pygame.mixer.pre_init(44100, -16, 2, 4096)
pygame.init()
pygame.mixer.init()

# ====================== CONSTANTS & ASSETS (unchanged) ======================
WIDTH, HEIGHT = 1024, 768
WHITE, BLACK, GREEN, RED, YELLOW, GOLD = (255,255,255), (10,10,10), (50,255,50), (255,50,50), (255,255,0), (255,215,0)
HP_GREEN, HP_YELLOW, HP_RED = (112,248,168), (248,224,56), (248,88,56)
GB_BORDER, GB_PANEL, GB_PANEL_DARK, GB_TEXT = (0,0,0), (224,192,104), (184,152,64), (0,0,0)
FONT_BIG = pygame.font.SysFont("impact", 64)
FONT_UI = pygame.font.SysFont("arial", 32, bold=True)
FONT_MSG = pygame.font.SysFont("lucidaconsole", 36)

BOTTOM_UI_Y = HEIGHT - 200
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# ====================== DATA CLASSES ======================
@dataclass
class Pokemon:
    id: int
    name: str
    level: int
    hp: int
    max_hp: int
    moves: list
    sprite: pygame.Surface
    front_sprite: pygame.Surface
    types: list
    capture_rate: int

    def heal(self, amount): self.hp = min(self.max_hp, self.hp + amount)
    def is_fainted(self): return self.hp <= 0

class Party:
    def __init__(self, mons: List[Pokemon]):
        self.pokemon = mons
        self.active_idx = 0
    @property
    def active(self): return self.pokemon[self.active_idx]

# ====================== ROUTE EVENT SYSTEM (your CYOA) ======================
class RouteEventSystem:
    def __init__(self, overworld):
        self.ow = overworld
        self.event_pool = {
            "wild": (45, self._trigger_wild),
            "trainer": (25, self._trigger_trainer),
            "item": (15, self._trigger_item),
            "special": (10, self._trigger_special),
            "rival": (5, self._trigger_rival)
        }

    def explore_route(self):
        self.ow.show_text("Exploring the route...")
        for step in range(10):
            pygame.time.wait(300)  # dramatic pause
            weights, funcs = zip(*[(w, f) for w, f in self.event_pool.values()])
            event_func = random.choices(funcs, weights=weights, k=1)[0]
            event_func()
            if not self.ow.battle_running: return  # player lost
        self.ow.show_text("You finished exploring the route!")
        self.ow.explored_routes.add(self.ow.current_area_name)

    def _trigger_wild(self):
        pool = self.ow.area_pools.get(self.ow.current_area_name, [16,19,21])
        enemy_id = random.choice(pool)
        self.ow.start_battle(enemy_id, is_trainer=False)

    def _trigger_trainer(self):
        enemy_id = random.choice(self.ow.area_pools.get(self.ow.current_area_name, [1]))
        trainer_name = random.choice(["Youngster", "Lass", "Bug Catcher"])
        self.ow.start_battle(enemy_id, is_trainer=True, trainer_name=trainer_name)

    def _trigger_item(self):
        self.ow.show_text("You found a Potion!")
        # TODO: add to bag

    def _trigger_special(self):
        self.ow.show_text("A mysterious old man gave you a rare candy!")

    def _trigger_rival(self):
        self.ow.show_text("Your rival wants to battle!")
        self.ow.start_battle(25, is_trainer=True, trainer_name="Rival")

# ====================== OVERWORLD MANAGER (cleaned) ======================
class OverworldManager:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.current_area_name = "PALLET"
        self.explored_routes = set()
        self.player_party = Party([self._make_starter(1), self._make_starter(4), self._make_starter(7)])
        self.text = ""
        self.battle_running = False
        self.route_events = RouteEventSystem(self)

        # Area pools (expand later)
        self.area_pools = {
            "PALLET": [16,19,21],
            "ROUTE1_SOUTH": [16,19,21,10],
            "VIRIDIAN_FOREST1": [10,13,25],
            # ... add the rest as you like
        }

        self.menu_options = []
        self.show_overlay = None
        self.refresh_menu()

    def _make_starter(self, pid):
        # placeholder – replace with your DataManager later
        return Pokemon(pid, f"POKÉ{pid}", 5, 20, 20, [], None, None, ["NORMAL"], 45)

    def refresh_menu(self):
        area = self.current_area_name
        self.menu_options = [("Explore Route", self.explore_route)]
        if area in self.explored_routes:
            self.menu_options.append(("Quick Travel Through", self.quick_travel))
        self.menu_options.append(("Go Back", self.go_back))

    def explore_route(self):
        self.route_events.explore_route()
        self.refresh_menu()

    def quick_travel(self):
        self.show_text("You quickly traveled through the route.")
        self.current_area_name = "VIRIDIAN"  # example next area
        self.refresh_menu()

    def go_back(self):
        self.show_text("Returning...")

    def start_battle(self, enemy_id, is_trainer=False, trainer_name=""):
        self.battle_running = True
        engine = BattleEngine(self.screen, self.clock, self.player_party, enemy_id,
                              is_trainer=is_trainer, trainer_name=trainer_name,
                              use_cache_only=True)
        result = engine.run()
        self.battle_running = False

        # INTEGRATION: battle feeds back to overworld
        if result.get("caught"):
            self.player_party.pokemon.append(result["caught"])
            self.show_text(f"{result['caught'].name} was added to your party!")
        self.refresh_menu()

    def show_text(self, text):
        self.text = text
        print("OVERWORLD:", text)  # replace with real UI later

    def draw(self):
        self.screen.fill((34,139,34))
        # your background logic here
        draw_text(self.screen, self.text or f"In {self.current_area_name}", FONT_UI, WHITE, WIDTH//2, HEIGHT//2)
        # bottom menu (simplified)
        for i, (txt, _) in enumerate(self.menu_options):
            draw_text(self.screen, txt, FONT_UI, YELLOW, 100, 500 + i*50)

    def handle_click(self, mx, my):
        for i, (_, action) in enumerate(self.menu_options):
            if 480 < my < 530 + i*50:
                action()

class BattleEngine:
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

        # Enemy & Trainer (simplified)
        self.is_trainer = is_trainer
        self.trainer_name = trainer_name
        self.trainer_system = None
        if is_trainer:
            self.trainer_system = TrainerSystem(trainer_name, "trainer.png", [{"id": enemy_id, "level": 50}], self.data_manager, self.mechanics)
            self.enemy = self.trainer_system.get_active()
        else:
            self.enemy = Pokemon(enemy_id, self.data_manager, self.mechanics, level=50, back_sprite=False)
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

    # [REF-0024b] Helper Methods (Action Creation, AI)
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
    # ====================== MAIN (Story + Test Buttons) ======================
def draw_text(screen, text, font, col, x, y, center=True):
    img = font.render(text, True, col)
    rect = img.get_rect(center=(x,y) if center else None)
    if not center: rect.topleft = (x,y)
    screen.blit(img, rect)

def standalone_main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pokémath Adventures")
    clock = pygame.time.Clock()

    overworld = OverworldManager(screen, clock)

    running = True
    in_story = False
    in_overworld_test = False
    in_battle_test = False

    while running:
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not in_story and not in_overworld_test and not in_battle_test:
                    if pygame.Rect(200, 250, 600, 80).collidepoint(mx, my):
                        in_story = True
                    elif pygame.Rect(200, 350, 600, 80).collidepoint(mx, my):
                        in_overworld_test = True
                    elif pygame.Rect(200, 450, 600, 80).collidepoint(mx, my):
                        in_battle_test = True
                elif in_story or in_overworld_test:
                    overworld.handle_click(mx, my)

        screen.fill(BLACK)

        if in_story or in_overworld_test:
            overworld.draw()
        else:
            # Splash
            draw_text(screen, "POKÉMATH ADVENTURES", FONT_BIG, GOLD, WIDTH//2, 150)
            draw_text(screen, "Story Mode", FONT_UI, GREEN, WIDTH//2, 280)
            draw_text(screen, "Test Overworld", FONT_UI, YELLOW, WIDTH//2, 380)
            draw_text(screen, "Test Battle", FONT_UI, RED, WIDTH//2, 480)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    standalone_main()