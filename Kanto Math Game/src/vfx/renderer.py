# [REF-0001: System Imports]
import pygame
import math
from src.utils import Utils
from src.config import WHITE, BLACK
from src.ui import theme


# [REF-0023: Battle Renderer]
class BattleRenderer:
    """The battle scene, in the games' layout (redesign, see src/ui/theme.py): the foe's info box
    top left, yours bottom right above the text box; light boxes with dark text, an "HP" label,
    an HP bar that drains at a steady speed (the battle text waits for it), your HP numbers and
    EXP bar. Attacks lunge and the target blinks (src/vfx/animations.py)."""

    FOE_BOX = (470, 104)
    MY_BOX = (500, 134)
    MARGIN = 26
    HP_SPEED = 0.022   # share of the bar per frame (a full bar drains in ~2 s at 25 FPS)

    def __init__(self, game):
        self.game = game
        self.font_med = game.assets.fonts["med"]
        self.font_small = game.assets.fonts["small"]
        self.font_tiny = game.assets.fonts["tiny"]
        self._hp_bars = {}
        try:
            ball_raw = game.assets.ball_imgs[0] if game.assets.ball_imgs else None
            self.pokeball_icon = pygame.transform.scale(ball_raw, (24, 24)) if ball_raw else None
        except Exception:
            self.pokeball_icon = None

    # Status tags, in the games' colours.
    STATUS_TAGS = {"burn": ("BRN", (232, 120, 48)), "paralysis": ("PAR", (216, 176, 32)),
                   "poison": ("PSN", (152, 64, 160)), "toxic": ("TOX", (112, 40, 112)),
                   "sleep": ("SLP", (128, 128, 136)), "freeze": ("FRZ", (96, 176, 216))}

    # ------------------------------------------------------------------ pieces
    def hp_animating(self):
        """True while an HP bar is still sliding (the battle waits before the next message)."""
        return any(abs(shown - target) > 0.002 for shown, _ghost, target in self._hp_bars.values())

    def tick(self):
        """Slide the HP bars one frame toward their values (called from the battle's update, so
        the bars move, and the battle's wait ends, even on frames that aren't drawn)."""
        for key, (shown, ghost, target) in list(self._hp_bars.items()):
            if shown > target:
                shown = max(target, shown - self.HP_SPEED)
            elif shown < target:
                shown = min(target, shown + self.HP_SPEED)
            ghost = max(shown, ghost - self.HP_SPEED * 0.6) if ghost > shown else shown
            self._hp_bars[key] = (shown, ghost, target)

    def _status_tag(self, screen, pokemon, x, y):
        tag = self.STATUS_TAGS.get(getattr(pokemon, "status", None))
        if not tag or pokemon.current_hp <= 0:
            return 0
        text, color = tag
        font = self.game.assets.fonts["label"]
        rect = pygame.Rect(x, y, font.size(text)[0] + 18, 26)
        pygame.draw.rect(screen, color, rect, border_radius=7)
        pygame.draw.rect(screen, theme.INFOBOX_FRAME, rect, 2, border_radius=7)
        Utils.draw_text_outline(screen, text, font, WHITE, rect.centerx, rect.centery, outline_color=color, thickness=1)
        return rect.w + 8

    def _hp_bar(self, screen, key, x, y, w, hp, max_hp):
        """'HP' label, then the bar: green / yellow / red, sliding to its new value."""
        target = max(0.0, min(1.0, hp / max_hp)) if max_hp else 0.0
        shown, ghost, _ = self._hp_bars.get(key, (target, target, target))
        self._hp_bars[key] = (shown, ghost, target)  # tick() slides it
        font = self.game.assets.fonts["label"]
        pill = pygame.Rect(x, y - 3, 42, 22)
        pygame.draw.rect(screen, (232, 152, 40), pill, border_radius=6)
        Utils.draw_text_outline(screen, "HP", font, WHITE, pill.centerx, pill.centery, outline_color=(150, 80, 20),
                                thickness=1)
        bar = pygame.Rect(pill.right + 6, y, w - 48, 16)
        pygame.draw.rect(screen, theme.INFOBOX_FRAME, bar.inflate(6, 6), border_radius=6)
        pygame.draw.rect(screen, (88, 88, 96), bar, border_radius=4)
        if ghost > shown:
            pygame.draw.rect(screen, (248, 168, 160), (bar.x, bar.y, int(bar.w * ghost), bar.h), border_radius=4)
        color = theme.HP_GREEN if shown > 0.5 else theme.HP_YELLOW if shown > 0.2 else theme.HP_RED
        if shown > 0:
            fill = pygame.Rect(bar.x, bar.y, max(3, int(bar.w * shown)), bar.h)
            pygame.draw.rect(screen, color, fill, border_radius=4)
            pygame.draw.rect(screen, tuple(min(255, c + 60) for c in color), (fill.x + 2, fill.y + 2,
                                                                              max(1, fill.w - 4), 4), border_radius=2)
        return bar

    def _box(self, screen, rect, slant):
        """An info box with one slanted side ('right' for the foe's, 'left' for yours)."""
        x, y, w, h = rect
        cut = 34
        if slant == "right":
            pts = [(x, y), (x + w - cut, y), (x + w, y + h // 2), (x + w - cut, y + h), (x, y + h)]
        else:
            pts = [(x + cut, y), (x + w, y), (x + w, y + h), (x + cut, y + h), (x, y + h // 2)]
        shadow = [(px + 6, py + 6) for px, py in pts]
        sh = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(sh, (0, 0, 0, 90), shadow)
        screen.blit(sh, (0, 0))
        pygame.draw.polygon(screen, theme.INFOBOX, pts)
        band = pygame.Rect(x + (cut if slant == "left" else 8), y + h - 14, w - cut - 8, 8)
        pygame.draw.rect(screen, theme.INFOBOX_ACCENT, band, border_radius=4)
        pygame.draw.polygon(screen, theme.INFOBOX_FRAME, pts, 4)

    def _name_line(self, screen, pokemon, x, y, right):
        name_font, label = self.game.assets.fonts["s_med"], self.game.assets.fonts["label"]
        r = theme.shadow_text(screen, pokemon.display_name.upper(), name_font, x, y)
        theme.shadow_text(screen, f"Lv{getattr(pokemon, 'level', 5)}", label, right, y + 4, align="right")
        return r

    # ------------------------------------------------------------------ the scene
    def draw(self, screen, opponent_pokemon, player_pokemon, opp_hp, player_hp, opp_max_hp, player_max_hp,
             adv_opp=1.0, adv_player=1.0, is_trainer_battle=False, trainer_img=None, background=None,
             anim_ctrl=None, fainting_side=None, trainer_x_offset=0, hide_opponent=False):
        w, h = self.game.width, self.game.height
        screen.fill(BLACK)
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill((95, 145, 185))

        reach = anim_ctrl.lunge_amount() if anim_ctrl else 0.0
        lunge_side = anim_ctrl.lunge_side if anim_ctrl and anim_ctrl.is_lunging else None

        # The foe.
        if fainting_side != "opponent" and not hide_opponent and opponent_pokemon.current_hp > 0 \
                and (not anim_ctrl or anim_ctrl.hit_visible("opponent")):
            img = opponent_pokemon.image
            ox, oy = 0, 0
            if opponent_pokemon.id in self.game.loader.all_boss_ids:  # bosses: bigger, hovering
                oy += math.sin(pygame.time.get_ticks() * opponent_pokemon.bob_speed + opponent_pokemon.bob_offset) \
                    * opponent_pokemon.bob_amount
                img = pygame.transform.scale(img, (int(img.get_width() * 1.25), int(img.get_height() * 1.25)))
            if lunge_side == "opponent":
                ox, oy = ox - 70 * reach, oy + 30 * reach
            if anim_ctrl:
                ox += anim_ctrl.knockback("opponent")
            screen.blit(img, img.get_rect(center=(w * 0.73 + ox, h * 0.39 + oy)))

        # Your Pokemon.
        if fainting_side not in ("player", "player_switch") and player_pokemon.current_hp > 0 \
                and (not anim_ctrl or anim_ctrl.hit_visible("player")):
            img = player_pokemon.back_image or player_pokemon.image
            px, py = 0, 0
            if lunge_side == "player":
                px, py = 70 * reach, -30 * reach
            if anim_ctrl:
                px -= anim_ctrl.knockback("player")
            screen.blit(img, img.get_rect(center=(w * 0.27 + px, h * 0.69 + py)))

        if is_trainer_battle and trainer_img:
            screen.blit(trainer_img, trainer_img.get_rect(center=(w * 0.78 + trainer_x_offset, h * 0.26)))

        # The foe's box (top left).
        bw, bh = self.FOE_BOX
        box = pygame.Rect(self.MARGIN, self.MARGIN, bw, bh)
        self._box(screen, box, "right")
        name = self._name_line(screen, opponent_pokemon, box.x + 22, box.y + 12, box.right - 44)
        caught = any(isinstance(v, dict) and v.get("id") == opponent_pokemon.id
                     for v in self.game.data.data.get("pokedex", {}).values())
        if caught and self.pokeball_icon:
            screen.blit(self.pokeball_icon, (name.right + 10, name.y + 2))
        tag_w = self._status_tag(screen, opponent_pokemon, box.x + 22, box.y + 58)
        self._hp_bar(screen, ("opp", id(opponent_pokemon)), box.x + 22 + max(tag_w, 0), box.y + 61,
                     bw - 80 - max(tag_w, 0), opp_hp, opp_max_hp)

        # Your box (bottom right, above the text box).
        bw, bh = self.MY_BOX
        text_top = Utils.get_full_dialogue_rect(self.game).top
        box = pygame.Rect(w - self.MARGIN - bw, text_top - self.MARGIN - bh, bw, bh)
        self._box(screen, box, "left")
        self._name_line(screen, player_pokemon, box.x + 52, box.y + 12, box.right - 22)
        tag_w = self._status_tag(screen, player_pokemon, box.x + 52, box.y + 56)
        bar = self._hp_bar(screen, ("player", id(player_pokemon)), box.x + 52 + tag_w, box.y + 59,
                           bw - 74 - tag_w, player_hp, player_max_hp)
        theme.shadow_text(screen, f"{int(player_hp)}/{int(player_max_hp)}", self.game.assets.fonts["label"],
                          bar.right, bar.bottom + 6, align="right")
        self._exp_bar(screen, player_pokemon, box.x + 52, box.bottom - 24, bw - 74)

    def _exp_bar(self, screen, pokemon, x, y, w):
        """Progress to the next level (gold at Lv 100), sliding like the HP bar."""
        maxed = pokemon.level >= pokemon.MAX_LEVEL
        target = pokemon.level_progress
        key = (id(pokemon), pokemon.level)
        if getattr(self, "_xp_bar_key", None) != key:
            self._xp_bar_key, self._xp_bar_shown = key, target
        self._xp_bar_shown += (target - self._xp_bar_shown) * 0.08
        if abs(target - self._xp_bar_shown) < 0.002:
            self._xp_bar_shown = target
        label = self.game.assets.fonts["tiny"]
        Utils.draw_text_outline(screen, "EXP", label, theme.EXP_BLUE, x, y - 2, align="left",
                                outline_color=theme.INFOBOX_FRAME, thickness=1)
        bar = pygame.Rect(x + 36, y, w - 36, 8)
        pygame.draw.rect(screen, (72, 72, 84), bar, border_radius=3)
        if self._xp_bar_shown > 0:
            pygame.draw.rect(screen, (240, 200, 40) if maxed else theme.EXP_BLUE,
                             (bar.x, bar.y, int(bar.w * self._xp_bar_shown), bar.h), border_radius=3)
