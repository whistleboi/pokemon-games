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

    # Soft click sounds, set once the game has loaded its sounds: {"select": Sound, "back": Sound}
    sounds = {}
    BACK_WORDS = ("BACK", "EXIT", "CANCEL", "NO", "CLOSE", "EXIT GYM", "QUIT")

    armed_at = 0  # pygame ticks before which taps are ignored (see arm)

    def arm(self, delay_ms):
        """Ignore taps for a moment after the button appears, so a quick tap meant for what was
        there before (a math answer) can't press it."""
        self.armed_at = pygame.time.get_ticks() + delay_ms
        return self

    def handle_event(self, event):
        if not self.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if pygame.time.get_ticks() < self.armed_at:
                    return True  # just appeared: swallow the stray tap
                if self.callback:
                    kind = "back" if str(self.text).upper() in self.BACK_WORDS else "select"
                    snd = Button.sounds.get(kind)
                    if snd:
                        snd.play()
                    self.callback()
                return True
        return False

    @staticmethod
    def _shade(color, f):
        return tuple(max(0, min(255, int(c * f))) for c in color[:3])

    def draw(self, surface):
        if not self.visible:
            return
        # A raised look: a darker lip under the button, a light top edge, and a glow under the
        # mouse. Buttons with no action stay flat.
        r = self.rect
        live = self.callback is not None
        hover = live and r.collidepoint(pygame.mouse.get_pos())
        color = self._shade(self.bg_color, 1.12) if hover else self.bg_color
        if live:
            lip = r.move(0, 4)
            pygame.draw.rect(surface, self._shade(self.bg_color, 0.55), lip, border_radius=self.border_radius)
            pygame.draw.rect(surface, BLACK, lip, 3, border_radius=self.border_radius)
        pygame.draw.rect(surface, color, r, border_radius=self.border_radius)
        if r.h > 24:
            shine = pygame.Rect(r.x + 8, r.y + 4, r.w - 16, max(3, r.h // 8))
            pygame.draw.rect(surface, self._shade(color, 1.25), shine, border_radius=max(2, shine.h // 2))
        pygame.draw.rect(surface, WHITE if hover else BLACK, r, 3, border_radius=self.border_radius)
        
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


class MoveButton(Button):
    """A move in the FIGHT menu: name on top, a type pill and power below, and a badge that
    shows how well it works on the foe by colour and shape (for pre-readers too):
    green !! = super effective, orange down-arrow = not very, grey X = no effect.
    Moves that match the user's own type get a gold border."""
    EFFECT = {"super": ((46, 184, 74), "SUPER!"), "weak": ((240, 140, 46), "weak"),
              "none": ((138, 138, 138), "NO EFFECT")}

    def __init__(self, rect, name, font, small_font, callback, type_name, type_color, detail,
                 effect=None, stab=False):
        super().__init__(rect, name, font, callback, bg_color=type_color, autosize=False)
        self.small_font = small_font
        self.type_name = type_name
        self.type_color = type_color
        self.detail = detail
        self.effect = effect
        self.stab = stab

    def draw(self, surface):
        if not self.visible:
            return
        label, self.text = self.text, ""
        super().draw(surface)
        self.text = label
        r = self.rect
        if self.stab:
            pygame.draw.rect(surface, GOLD, r.inflate(4, 4), 4, border_radius=self.border_radius + 2)
        Utils.draw_text_outline(surface, label, self.font, WHITE, r.x + 16, r.y + 8, align="left")
        # type pill + power
        pill_txt = self.type_name.title()
        tw = self.small_font.size(pill_txt)[0]
        pill = pygame.Rect(r.x + 14, r.bottom - 30, tw + 20, 22)
        pygame.draw.rect(surface, self._shade(self.type_color, 0.7), pill, border_radius=11)
        pygame.draw.rect(surface, WHITE, pill, 2, border_radius=11)
        Utils.draw_text_outline(surface, pill_txt, self.small_font, WHITE, pill.centerx, pill.centery, thickness=2)
        if self.detail:
            Utils.draw_text_outline(surface, self.detail, self.small_font, WHITE, pill.right + 12,
                                    pill.y + 2, align="left", thickness=2)
        # effectiveness badge
        if self.effect in self.EFFECT:
            color, word = self.EFFECT[self.effect]
            cx, cy, rad = r.right - 30, r.centery, min(18, r.h // 3)
            pygame.draw.circle(surface, BLACK, (cx, cy + 2), rad + 2)
            pygame.draw.circle(surface, color, (cx, cy), rad)
            pygame.draw.circle(surface, WHITE, (cx, cy), rad, 2)
            if self.effect == "super":
                for dx in (-5, 5):
                    pygame.draw.line(surface, WHITE, (cx + dx, cy - 9), (cx + dx, cy + 2), 4)
                    pygame.draw.circle(surface, WHITE, (cx + dx, cy + 8), 2)
            elif self.effect == "weak":
                pygame.draw.polygon(surface, WHITE, [(cx - 8, cy - 5), (cx + 8, cy - 5), (cx, cy + 7)])
            else:
                pygame.draw.line(surface, WHITE, (cx - 7, cy - 7), (cx + 7, cy + 7), 4)
                pygame.draw.line(surface, WHITE, (cx + 7, cy - 7), (cx - 7, cy + 7), 4)
            Utils.draw_text_outline(surface, word, self.small_font, color, cx - rad - 10, pill.y + 2,
                                    align="right", thickness=2)


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
        self.feedback = None  # set by the battle while it shows "Great job!" / the right answer
        card = self.right_rect.inflate(-18, -18)
        self.speak_rect = pygame.Rect(card.right - 58, card.y + 10, 46, 46)

    def on_click(self, idx):
        if self.feedback:
            return  # already answered
        if self.answer_callback:
            self.answer_callback(idx)

    def handle_event(self, event):
        if not self.visible:
            return False
        if self.feedback:
            return event.type == pygame.MOUSEBUTTONDOWN  # swallow taps during the cheer
        from src.core import speech
        if (speech.available() and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.speak_rect.collidepoint(event.pos)):
            speech.say(speech.math_words(self.problem_str))
            return True
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

        if self.feedback:
            self._draw_feedback(surface, white_panel)
            return

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
        from src.core import speech
        if speech.available():
            speech.draw_speaker(surface, self.speak_rect)

    def _draw_feedback(self, surface, card):
        import math
        fb = self.feedback
        grid = self.answer_grid
        t = 1 - fb["frames"] / max(1, fb["total"])  # 0 -> 1 over the beat
        right = grid.button_rects[fb["right"]] if fb["right"] < len(grid.button_rects) else None
        picked = grid.button_rects[fb["index"]] if fb["index"] < len(grid.button_rects) else None
        if right is not None:
            pygame.draw.rect(surface, (46, 184, 74), right.inflate(-6, -6), border_radius=14)
            pygame.draw.rect(surface, WHITE, right.inflate(-6, -6), 4, border_radius=14)
        if picked is not None and not fb["correct"]:
            wobble = int(6 * math.sin(t * 30) * (1 - t))
            pygame.draw.rect(surface, (200, 120, 90), picked.inflate(-6, -6).move(wobble, 0), 4, border_radius=14)
        grid.draw(surface)
        if fb["correct"] and right is not None:  # star burst
            cx, cy = right.center
            for k in range(10):
                ang = k * math.pi / 5
                dist = 20 + 90 * t
                x, y = cx + math.cos(ang) * dist, cy + math.sin(ang) * dist
                size = max(2, int(9 * (1 - t)))
                pts = []
                for j in range(10):
                    rad = size if j % 2 == 0 else size / 2.5
                    a = ang + j * math.pi / 5
                    pts.append((x + math.cos(a) * rad, y + math.sin(a) * rad))
                pygame.draw.polygon(surface, GOLD, pts)
        font = self.game.assets.fonts["s_med"]
        color = (30, 150, 60) if fb["correct"] else (60, 60, 60)
        Utils.draw_multiline_text(surface, fb["text"], font, color, card.centerx, card.centery,
                                  max_width=card.width - 30, line_height=font.get_linesize() + 6,
                                  center=True, outline_color=WHITE)


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
