# [REF-0001: System Imports]
import pygame
import random
import math
from src.utils import Utils
from src.config import WHITE, BLACK, GREEN, GOLD, RED


# [REF-0023: Battle Renderer]
class BattleRenderer:
    def __init__(self, game):
        self.game = game
        self.font_med = game.assets.fonts["med"]
        self.font_small = game.assets.fonts["small"]
        self.font_tiny = game.assets.fonts["tiny"]

        try:
            ball_raw = game.assets.ball_imgs[0] if game.assets.ball_imgs else None
            self.pokeball_icon = (
                pygame.transform.scale(ball_raw, (26, 26)) if ball_raw else None
            )
        except:
            self.pokeball_icon = None

    def _draw_level(self, screen, pokemon, panel):
        """'Lv 23' in the panel's top-right corner, on the name line."""
        Utils.draw_text_outline(screen, f"Lv {getattr(pokemon, 'level', 5)}", self.game.assets.fonts["small"], WHITE,
                                panel.right - 24, panel.y + 40, align="right")

    def _hp_bar(self, screen, key, x, y, w, hp, max_hp, heart=False):
        """HP bar that slides to its new value; the HP just lost shows as a light-red chunk
        that drains away (Showdown-style). Numbers sit above the bar, right-aligned."""
        bars = self.__dict__.setdefault("_hp_bars", {})
        target = max(0.0, min(1.0, hp / max_hp)) if max_hp else 0.0
        shown, ghost = bars.get(key, (target, target))
        shown += (target - shown) * 0.25
        if abs(target - shown) < 0.003:
            shown = target
        ghost = max(shown, ghost - 0.012) if ghost > shown else shown
        bars[key] = (shown, ghost)

        pygame.draw.rect(screen, BLACK, (x - 3, y - 3, w + 6, 20), border_radius=5)
        pygame.draw.rect(screen, (60, 60, 60), (x, y, w, 14), border_radius=4)
        if ghost > shown:
            pygame.draw.rect(screen, (255, 150, 150), (x, y, int(w * ghost), 14), border_radius=4)
        color = GREEN if shown > 0.5 else GOLD if shown > 0.25 else RED
        if shown > 0:
            pygame.draw.rect(screen, color, (x, y, max(2, int(w * shown)), 14), border_radius=4)
            pygame.draw.line(screen, tuple(min(255, c + 70) for c in color[:3]),
                             (x + 3, y + 3), (x + max(3, int(w * shown)) - 4, y + 3), 2)
        if heart:
            hx, hy = x - 22, y + 6
            pygame.draw.circle(screen, (235, 70, 110), (hx - 4, hy - 2), 5)
            pygame.draw.circle(screen, (235, 70, 110), (hx + 4, hy - 2), 5)
            pygame.draw.polygon(screen, (235, 70, 110), [(hx - 9, hy), (hx + 9, hy), (hx, hy + 9)])
        Utils.draw_text_outline(screen, f"HP {int(hp)}/{int(max_hp)}", self.game.assets.fonts["small"], WHITE,
                                x + w, y - 32, align="right")

    def draw(
        self,
        screen,
        opponent_pokemon,
        player_pokemon,
        opp_hp: int,
        player_hp: int,
        opp_max_hp: int,
        player_max_hp: int,
        adv_opp: float = 1.0,
        adv_player: float = 1.0,
        is_trainer_battle: bool = False,
        trainer_img=None,
        background=None,
        anim_ctrl=None,
        fainting_side=None,
        trainer_x_offset=0,
        hide_opponent=False
    ):

        w, h = self.game.width, self.game.height

        screen.fill(BLACK)

        # --- Animation Offsets ---
        shake_offset_x, shake_offset_y = 0, 0
        player_offset_x, player_offset_y = 0, 0
        opp_offset_x, opp_offset_y = 0, 0

        if anim_ctrl:
            if anim_ctrl.impact_shake > 0:
                shake_offset_x = random.randint(-15, 15)
                shake_offset_y = random.randint(-15, 15)

            if anim_ctrl.is_lunging:
                lunge_dist = 120
                progress = anim_ctrl.lunge_timer / 20.0
                lunge_amount = math.sin(progress * math.pi) * lunge_dist
                if anim_ctrl.lunge_side == "player":
                    player_offset_x = lunge_amount
                    player_offset_y = -lunge_amount / 2
                elif anim_ctrl.lunge_side == "opponent":
                    opp_offset_x = -lunge_amount
                    opp_offset_y = lunge_amount / 2

        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill((95, 145, 185))

        # === OPPONENT SPRITE ===
        # Only draw if not fainting, not explicitly hidden (animations), and alive
        # We check > 0 to ensure fainted mons stay gone.
        if fainting_side != "opponent" and not hide_opponent and opponent_pokemon.current_hp > 0:
            draw_img = opponent_pokemon.image
            
            # --- BOSS VISUALS (RPG BATTLE) ---
            if opponent_pokemon.id in self.game.loader.all_boss_ids:
                # Bobbing Animation
                bob_spd = opponent_pokemon.bob_speed
                bob_off = opponent_pokemon.bob_offset
                hover_y = math.sin(pygame.time.get_ticks() * bob_spd + bob_off) * opponent_pokemon.bob_amount
                opp_offset_y += hover_y
                
                # 25% Larger
                w_orig = draw_img.get_width()
                h_orig = draw_img.get_height()
                draw_img = pygame.transform.scale(
                    draw_img, (int(w_orig * 1.25), int(h_orig * 1.25))
                )
            # ---------------------------------

            opp_rect = draw_img.get_rect(
                center=(
                    w * 0.73 + opp_offset_x + shake_offset_x,
                    h * 0.39 + opp_offset_y + shake_offset_y,
                )
            )
            screen.blit(draw_img, opp_rect)

        # === PLAYER SPRITE ===
        p_alive = player_pokemon.current_hp > 0
        if fainting_side not in ["player", "player_switch"] and p_alive:
            p_img = player_pokemon.back_image or player_pokemon.image

            player_rect = p_img.get_rect(
                center=(
                    w * 0.27 + player_offset_x + shake_offset_x,
                    h * 0.69 + player_offset_y + shake_offset_y,
                )
            )
            screen.blit(p_img, player_rect)

        if is_trainer_battle and trainer_img:
            tx = w * 0.78 + shake_offset_x + trainer_x_offset
            ty = h * 0.26 + shake_offset_y
            t_rect = trainer_img.get_rect(center=(tx, ty))
            screen.blit(trainer_img, t_rect)

        # ====================== OPPONENT PANEL ======================
        panel_w = int(w * 0.40)
        panel_h = 150
        opp_panel = pygame.Rect(
            10 + shake_offset_x, 10 + shake_offset_y, panel_w, panel_h
        )
        Utils.draw_classic_panel(
            screen, opp_panel.x, opp_panel.y, opp_panel.width, opp_panel.height
        )

        Utils.draw_text_outline(
            screen,
            opponent_pokemon.display_name.upper(),
            self.game.assets.fonts["s_med"],
            WHITE,
            opp_panel.x + 20,
            opp_panel.y + 35,
            align="left",
        )
        self._draw_level(screen, opponent_pokemon, opp_panel)

        # Poké Ball + HP Bar
        # Check if species is already caught
        has_caught = False
        for p_data in self.game.data.data.get("pokedex", {}).values():
            if p_data["id"] == opponent_pokemon.id:
                has_caught = True
                break

        if has_caught and self.pokeball_icon:
            screen.blit(self.pokeball_icon, (opp_panel.x + 20, opp_panel.y + 100))
        else:
            pass

        # HP Bar
        bar_x = opp_panel.x + 65
        bar_y = opp_panel.y + 103
        bar_w = panel_w - 90
        self._hp_bar(screen, ("opp", id(opponent_pokemon)), bar_x, bar_y, bar_w, opp_hp, opp_max_hp)

        # ====================== PLAYER PANEL ======================
        hud_y_base = h - int(h * 0.25)
        p_panel = pygame.Rect(
            w - panel_w - 10 + shake_offset_x,
            hud_y_base - panel_h - 10 + shake_offset_y,
            panel_w,
            panel_h,
        )
        Utils.draw_classic_panel(
            screen, p_panel.x, p_panel.y, p_panel.width, p_panel.height
        )

        # Name
        Utils.draw_text_outline(
            screen,
            player_pokemon.display_name.upper(),
            self.game.assets.fonts["s_med"],
            WHITE,
            p_panel.x + 30,
            p_panel.y + 35,
            align="left",
        )
        self._draw_level(screen, player_pokemon, p_panel)

        # HP Bar
        bar_x = p_panel.x + 60
        bar_y = p_panel.y + 103
        bar_w = panel_w - 90
        self._hp_bar(screen, ("player", id(player_pokemon)), bar_x, bar_y, bar_w, player_hp, player_max_hp,
                     heart=True)

        # XP Bar (Under HP Bar)
        xp_bar_y = bar_y + 18
        xp_bar_h = 6
        xp_bar_w = bar_w

        # Draw XP Background
        xp_bg_rect = (bar_x - 3, xp_bar_y, xp_bar_w + 6, xp_bar_h)
        pygame.draw.rect(screen, (50, 50, 50), xp_bg_rect, border_radius=3)

        # XP bar: progress to the next level (gold at Lv 100).
        maxed = player_pokemon.level >= player_pokemon.MAX_LEVEL
        target = player_pokemon.level_progress
        key = (id(player_pokemon), player_pokemon.level)
        if getattr(self, "_xp_bar_key", None) != key:
            self._xp_bar_key, self._xp_bar_shown = key, target
        self._xp_bar_shown += (target - self._xp_bar_shown) * 0.08
        if abs(target - self._xp_bar_shown) < 0.002:
            self._xp_bar_shown = target

        if self._xp_bar_shown > 0:
            xp_fill_rect = (
                bar_x, xp_bar_y + 1,
                int(xp_bar_w * self._xp_bar_shown), xp_bar_h - 2
            )
            color = (255, 215, 0) if maxed else (0, 200, 255)
            pygame.draw.rect(screen, color, xp_fill_rect, border_radius=2)
        
        # XP Label (Tiny)
        # Utils.draw_text_outline(screen, "EXP", self.font_tiny, (0, 200, 255), bar_x - 20, xp_bar_y - 2, outline_color=BLACK, thickness=2)
