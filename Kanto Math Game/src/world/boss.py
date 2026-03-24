# [REF-0001: System Imports]
import pygame
import math
from src.config import WHITE, PURPLE, AMBER, NEON_BLUE
from src.ui.widgets import HealthBarUI
from src.pokemon.data import Pokemon


# [REF-0014: Boss System]
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
        self.boss_intro_timer = (
            0
        )
        self.boss_cry_triggered = False
        self.boss_pokemon_data = None
        self.aura_pulse = 0.0

        bar_w, bar_h = 320, 36
        bar_center_x = game.width // 2
        bar_y = game.height * 0.08
        self.health_bar = HealthBarUI(
            pygame.Rect(bar_center_x - bar_w // 2, bar_y, bar_w, bar_h)
        )
        self.health_bar.set_font(game.assets.fonts["med"])

    def start_boss_mode(self, raw_boss_data):
        self.in_boss_mode = True
        self.boss_intro_played = False
        self.boss_hp = 3
        self.health_bar.update_hp(3)
        self.boss_hits = 0
        self.boss_cry_triggered = False
        self.current_boss_type = raw_boss_data.get("boss_type", "STANDARD")
        self.boss_intro_timer = 50
        boss_warnings = self.game.loader.area_data.get("BOSS_WARNINGS", {})
        warning = boss_warnings.get(
            self.current_boss_type, "A powerful Pokémon appeared!"
        )
        self.game.states["play"].show_dialogue([warning])

        self.boss_pokemon_data = Pokemon(
            raw_boss_data["boss"], self.game.assets, size_mult=1.2
        )

    def _get_visual_config(self):
        """Returns visual configuration based on boss type."""
        defaults = {"intro": (150, 0, 0), "base": 30, "amp": 20, "bg_func": lambda v: (v, 0, v // 2)}
        
        configs = {
            "UB":       {"intro": PURPLE,         "base": 20, "amp": 15, "bg_func": lambda v: (v, 0, v)},
            "PAST":     {"intro": AMBER,          "base": 40, "amp": 20, "bg_func": lambda v: (v, v // 2, 0)},
            "FUTURE":   {"intro": NEON_BLUE,      "base": 40, "amp": 20, "bg_func": lambda v: (0, v, v)},
            "MEGA":     {"intro": (180, 50, 255), "base": 50, "amp": 25, "bg_func": lambda v: (v, 0, v + 20)},
            "GMAX":     {"intro": (255, 80, 120), "base": 50, "amp": 25, "bg_func": lambda v: (v + 20, 0, v)},
            "MYTHICAL": {"intro": (255, 105, 180), "base": 60, "amp": 30, "bg_func": lambda v: (v, 20, 80)},
        }
        return configs.get(self.current_boss_type, defaults)

    def update(self):
        if not self.in_boss_mode:
            return

        if self.boss_intro_timer > 0:
            self.boss_intro_timer -= 1
            return

        if (
            not self.boss_cry_triggered
            and self.boss_pokemon_data
            and self.boss_pokemon_data.cry
        ):
            self.boss_pokemon_data.cry.play()
            self.boss_cry_triggered = True

        self.health_bar.update_hp(self.boss_hp)
        self.aura_pulse += 0.05

    def draw(self, screen, width, height, offset_x, offset_y):
        if not self.in_boss_mode:
            return

        style = self._get_visual_config()

        # Boss Intro Animation
        if self.boss_intro_timer > 0:
            intro_color = style["intro"]
            pulse_alpha = ((math.sin(self.boss_intro_timer * 0.25) + 1) / 2 * 150)
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            overlay.fill(
                (*intro_color, int(pulse_alpha))
            )
            screen.blit(overlay, (0, 0))
            return True

        # Boss Background Aura
        bg_v = int(style["base"] + math.sin(self.aura_pulse) * style["amp"])
        bg_v = max(0, min(255, bg_v))
        bg_color = style["bg_func"](bg_v)
        screen.fill(bg_color)

        # Boss HP Bar & Counter
        if self.in_boss_mode and self.boss_intro_timer <= 0:
            self.health_bar.draw(screen, offset_x, offset_y)
