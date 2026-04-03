# [REF-0001: System Imports]
import pygame
from src.ui.manager import UIElement
from src.utils import Utils
from src.config import WHITE, BLUE, BLACK, GREEN, GOLD, RED, DARK_RED


# [REF-0046: Button Class with Auto-Sizing and Icon Support]
class Button(UIElement):
    def __init__(
        self,
        rect,
        text,
        font,
        callback,
        text_color=WHITE,
        bg_color=BLUE,
        outline_color=BLACK,
        border_radius=15,
        visible=True,
        autosize=True,
        icon=None,
    ):
        super().__init__(rect, callback, visible)
        self.text = text
        self.font = font
        self.text_color = text_color
        self.bg_color = bg_color
        self.outline_color = outline_color
        self.border_radius = border_radius
        self.icon = icon

        if autosize:
            text_surf = self.font.render(self.text, True, self.text_color)
            padding_x = 40
            padding_y = 20
            icon_w = self.icon.get_width() + 10 if self.icon else 0
            original_center = self.rect.center
            self.rect.size = (
                text_surf.get_width() + padding_x + icon_w,
                text_surf.get_height() + padding_y,
            )
            self.rect.center = original_center

    def handle_event(self, event):
        if not self.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()
                return True
        return False

    def draw(self, surface):
        if not self.visible:
            return
        pygame.draw.rect(
            surface, self.bg_color, self.rect, border_radius=self.border_radius
        )
        pygame.draw.rect(surface, BLACK, self.rect, 3, border_radius=self.border_radius)
        
        if self.icon:
            icon_rect = self.icon.get_rect(midleft=(self.rect.left + 15, self.rect.centery))
            surface.blit(self.icon, icon_rect)

        Utils.draw_text_outline(
            surface,
            self.text,
            self.font,
            self.text_color,
            self.rect.centerx,
            self.rect.centery,
            outline_color=self.outline_color,
        )


# [REF-0010: Math Battle UI]
class MathAnswerGrid(UIElement):

    def __init__(self, rect, options, font, callback):
        super().__init__(rect, callback, visible=True)
        self.options = options
        self.font = font
        self.answer_callback = callback
        self.button_rects = []
        self.button_texts = []

        grid_w = self.rect.width
        grid_h = self.rect.height
        btn_w = grid_w // 2 - 10
        btn_h = grid_h // 2 - 10

        positions = [
            (self.rect.left + grid_w * 0.25, self.rect.top + grid_h * 0.3),
            (self.rect.left + grid_w * 0.75, self.rect.top + grid_h * 0.3),
            (self.rect.left + grid_w * 0.25, self.rect.top + grid_h * 0.7),
            (self.rect.left + grid_w * 0.75, self.rect.top + grid_h * 0.7),
        ]

        for i, option in enumerate(self.options):
            if i < 4:
                r = pygame.Rect(0, 0, btn_w, btn_h)
                r.center = positions[i]
                self.button_rects.append(r)
                self.button_texts.append(str(option))

    def handle_event(self, event):
        if not self.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self.button_rects):
                if r.collidepoint(event.pos):
                    if self.answer_callback:
                        self.answer_callback(i)
                    return True
        return False

    def draw(self, surface):
        if not self.visible:
            return
        for i, r in enumerate(self.button_rects):
            Utils.draw_text_outline(
                surface,
                str(self.button_texts[i]),
                self.font,
                WHITE,
                r.centerx,
                r.centery,
                outline_color=BLACK
            )


# [REF-0048: Math Battle UI with Integrated Answer Grid and Problem Display]
class MathBattleUI(UIElement):
    def __init__(self, game, problem_str, options, callback):
        rect = Utils.get_full_dialogue_rect(game)
        super().__init__(rect, None, visible=True)
        self.game = game
        self.problem_str = problem_str
        self.options = options
        self.answer_callback = callback

        left_zone_w = int(rect.width * 0.55)
        left_zone = pygame.Rect(rect.x, rect.y, left_zone_w, rect.height)

        self.right_rect = pygame.Rect(rect.x + left_zone_w, rect.y, rect.width - left_zone_w, rect.height)
        self.text_x = self.right_rect.centerx
        self.text_y = rect.centery

        use_small_font = any(len(str(o)) > 4 for o in options)
        font = game.assets.fonts["s_med"] if use_small_font else game.assets.fonts["num"]

        self.answer_grid = MathAnswerGrid(
            left_zone, options, font, self.on_click
        )

    def on_click(self, idx):
        if self.answer_callback:
            self.answer_callback(idx)

    def handle_event(self, event):
        if not self.visible:
            return False
        return self.answer_grid.handle_event(event)

    def draw(self, surface):
        if not self.visible:
            return
        Utils.draw_classic_panel(
            surface, self.rect.x, self.rect.y, self.rect.width, self.rect.height
        )

        white_panel = self.right_rect.inflate(-18, -18)
        pygame.draw.rect(surface, WHITE, white_panel, border_radius=12)
        pygame.draw.rect(surface, BLACK, white_panel, 6, border_radius=12)

        font = self.game.assets.fonts["big"]
        if len(self.problem_str) > 8:
            font = self.game.assets.fonts["num"]

        Utils.draw_text_outline(
            surface,
            self.problem_str,
            font,
            BLACK,
            self.text_x,
            self.text_y,
            outline_color=WHITE,
        )
        self.answer_grid.draw(surface)


# [REF-0050: Health Bar UI]
class HealthBarUI(UIElement):
    def __init__(self, rect, max_hp=3, visible=True):
        super().__init__(rect, None, visible)
        self.max_hp = max_hp
        self.current_hp = max_hp
        self.font = pygame.font.SysFont("Verdana", 24, bold=True)

    def set_font(self, font):
        self.font = font

    def update_hp(self, new_hp):
        self.current_hp = max(0, new_hp)

    def handle_event(self, event):
        pass

    def draw(self, surface, offset_x=0, offset_y=0):
        if not self.visible:
            return

        bar_w, bar_h = self.rect.width, self.rect.height
        bar_x, bar_y = self.rect.x + offset_x, self.rect.y + offset_y

        fill_ratio = self.current_hp / self.max_hp
        fill_w = int(bar_w * fill_ratio)
        fill_color = GREEN if fill_ratio > 0.66 else GOLD if fill_ratio > 0.33 else RED

        pygame.draw.rect(
            surface, DARK_RED, (bar_x, bar_y, bar_w, bar_h), border_radius=10
        )

        if fill_w > 0:
            pygame.draw.rect(
                surface, fill_color, (bar_x, bar_y, fill_w, bar_h), border_radius=10
            )

        pygame.draw.rect(
            surface, WHITE, (bar_x, bar_y, bar_w, bar_h), width=4, border_radius=10
        )

        Utils.draw_text_outline(
            surface,
            f"{self.current_hp}/{self.max_hp}",
            self.font,
            WHITE,
            self.rect.centerx + offset_x,
            self.rect.y - 25 + offset_y,
            outline_color=BLACK,
            thickness=4,
        )
