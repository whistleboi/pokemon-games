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
        """In the battle menu's style (src/ui/theme.py) on every screen: the colour mapped onto the
        theme's palette, the label in the largest of the new fonts that fits; a button with no
        action is grey."""
        if not self.visible:
            return
        from src.ui import theme
        r = self.rect
        live = self.callback is not None
        hover = live and r.collidepoint(pygame.mouse.get_pos())
        color = theme.theme_color(self.bg_color) if live else (128, 132, 144)
        font = theme.readable_font(self.font, self.text, r.inflate(-(self.icon.get_width() + 14) if self.icon else 0, 0))
        if self.icon:
            theme.command_button(surface, r, "", font, color, hover=hover)
            icon_rect = self.icon.get_rect(midleft=(r.left + 15, r.centery))
            surface.blit(self.icon, icon_rect)
            Utils.draw_text_outline(surface, self.text, font, WHITE, (icon_rect.right + r.right) // 2, r.centery,
                                    outline_color=theme.shade(color, 0.6), thickness=3)
        else:
            theme.command_button(surface, r, self.text, font, color, hover=hover)


class Backdrop(UIElement):
    """The white text box behind a set of buttons (the battle's move list)."""

    def __init__(self, rect):
        super().__init__(rect, None, visible=True)

    def handle_event(self, event):
        return False

    def draw(self, surface):
        if self.visible:
            from src.ui import theme
            theme.draw_textbox(surface, self.rect)


class ItemCard(Button):
    """A Bag entry (the menu redesign): a white card with the item's icon, name and count; one
    that can't be used right now is greyed (tapping it still says why)."""

    def __init__(self, rect, name, qty, font, callback, icon=None, usable=True, key=None):
        super().__init__(rect, f"{name}  x{qty}", font, callback, icon=icon, autosize=False)
        self.name, self.qty, self.usable, self.key = name, qty, usable, key
        self._icon = pygame.transform.scale(icon, (40, 40)) if icon else None

    def draw(self, surface):
        if not self.visible:
            return
        from src.ui import theme
        r = self.rect
        hover = r.collidepoint(pygame.mouse.get_pos())
        theme.card(surface, r, hover=hover, accent=theme.ACCENT["bag"],
                   fill=theme.TEXTBOX if self.usable else (222, 226, 234))
        x = r.x + 14
        if self._icon:
            surface.blit(self._icon, (x, r.centery - 20))
            x += 52
        color = theme.TEXT if self.usable else (128, 132, 146)
        y = r.centery - self.font.get_height() // 2 - 1
        theme.shadow_text(surface, self.name, self.font, x, y, color=color)
        theme.shadow_text(surface, f"x{self.qty}", self.font, r.right - 16, y, color=color, align="right")


class MoveButton(Button):
    """A move in the FIGHT menu, like the games' move buttons: its type colour, the name, a type
    label and its power, and how well it works on the foe in words and a badge (for pre-readers
    too): green !! = super effective, orange arrow = not very, grey X = no effect. Moves that match
    the user's own type get a gold edge."""
    EFFECT = {"super": ((46, 170, 74), "SUPER!"), "weak": ((222, 128, 40), "WEAK"),
              "none": ((128, 128, 136), "NO EFFECT")}

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
        r = self.rect
        hover = r.collidepoint(pygame.mouse.get_pos())
        dark = self._shade(self.type_color, 0.6)
        pygame.draw.rect(surface, dark, r.move(0, 5), border_radius=14)
        pygame.draw.rect(surface, self._shade(self.type_color, 1.12) if hover else self.type_color, r, border_radius=14)
        pygame.draw.rect(surface, GOLD if self.stab else (255, 255, 255) if hover else (20, 20, 30), r,
                         4 if self.stab else 3, border_radius=14)
        name_font = self.font if self.font.size(self.text.upper())[0] <= r.w - 70 else self.small_font
        Utils.draw_text_outline(surface, self.text.upper(), name_font, WHITE, r.x + 16, r.y + 6, align="left",
                                outline_color=dark, thickness=2)
        pill_txt = self.type_name.upper()
        tw = self.small_font.size(pill_txt)[0]
        pill = pygame.Rect(r.x + 14, r.bottom - 27, tw + 16, 23)
        pygame.draw.rect(surface, dark, pill, border_radius=13)
        pygame.draw.rect(surface, WHITE, pill, 2, border_radius=13)
        Utils.draw_text_outline(surface, pill_txt, self.small_font, WHITE, pill.centerx, pill.centery,
                                outline_color=dark, thickness=1)
        if self.detail:
            Utils.draw_text_outline(surface, self.detail, self.small_font, WHITE, pill.right + 10, pill.y + 1,
                                    align="left", outline_color=dark, thickness=2)
        if self.effect in self.EFFECT:
            color, word = self.EFFECT[self.effect]
            cx, cy, rad = r.right - 24, r.y + 20, 13
            pygame.draw.circle(surface, (20, 20, 30), (cx, cy + 2), rad + 2)
            pygame.draw.circle(surface, color, (cx, cy), rad)
            pygame.draw.circle(surface, WHITE, (cx, cy), rad, 2)
            if self.effect == "super":
                for dx in (-4, 4):
                    pygame.draw.line(surface, WHITE, (cx + dx, cy - 7), (cx + dx, cy + 1), 3)
                    pygame.draw.circle(surface, WHITE, (cx + dx, cy + 6), 2)
            elif self.effect == "weak":
                pygame.draw.polygon(surface, WHITE, [(cx - 6, cy - 4), (cx + 6, cy - 4), (cx, cy + 6)])
            else:
                pygame.draw.line(surface, WHITE, (cx - 5, cy - 5), (cx + 5, cy + 5), 3)
                pygame.draw.line(surface, WHITE, (cx + 5, cy - 5), (cx - 5, cy + 5), 3)
            tag_w = self.small_font.size(word)[0] + 14
            tag = pygame.Rect(r.right - tag_w - 10, r.bottom - 27, tag_w, 23)
            pygame.draw.rect(surface, WHITE, tag, border_radius=13)
            pygame.draw.rect(surface, color, tag, 2, border_radius=13)
            Utils.draw_text_outline(surface, word, self.small_font, color, tag.centerx, tag.centery,
                                    outline_color=WHITE, thickness=1)


# [REF-0010: Math Battle UI]
class MathAnswerGrid(UIElement):
    """The four answers: big white buttons with dark numbers (clear digits come first in a math
    game), 2 x 2 in the right part of the bottom bar."""

    def __init__(self, rect, options, font, callback, small_font=None):
        super().__init__(rect, callback, visible=True)
        self.options = options
        self.font = font
        self.small_font = small_font or font  # for an answer too wide for its button
        self.answer_callback = callback
        self.button_rects = []
        self.button_texts = []
        pad, gap = 20, 14
        bw = (self.rect.width - pad * 2 - gap) // 2
        bh = (self.rect.height - pad * 2 - gap - 4) // 2
        for i, option in enumerate(self.options[:4]):
            r = pygame.Rect(self.rect.x + pad + (i % 2) * (bw + gap), self.rect.y + pad + (i // 2) * (bh + gap), bw, bh)
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

    def draw(self, surface, marks=None):
        """marks: {index: colour} to paint answers (the right one green, a wrong pick red)."""
        if not self.visible:
            return
        from src.ui import theme
        mouse = pygame.mouse.get_pos()
        for i, r in enumerate(self.button_rects):
            fill = (marks or {}).get(i)
            hover = fill is None and r.collidepoint(mouse)
            lip = r.move(0, 5)
            pygame.draw.rect(surface, theme.TEXTBOX_FRAME, lip, border_radius=14)
            pygame.draw.rect(surface, fill or ((236, 244, 255) if hover else WHITE), r, border_radius=14)
            pygame.draw.rect(surface, theme.TEXTBOX_FRAME, r, 4, border_radius=14)
            color = WHITE if fill else theme.TEXT
            text = self.button_texts[i]
            font = self.font
            if font.size(text)[0] > r.w - 24:
                font = self.small_font
            if fill:
                Utils.draw_text_outline(surface, text, font, WHITE, r.centerx, r.centery, outline_color=fill, thickness=2)
            else:
                theme.shadow_text(surface, text, font, r.centerx, r.centery, align="center")


# [REF-0048: Math Battle UI with Integrated Answer Grid and Problem Display]
class MathBattleUI(UIElement):
    """The math question in battle: the question on a white card at the left of the bottom bar,
    the four answers at the right. After an answer: the right one turns green (with a star burst
    when you got it), a wrong pick red and it wobbles, and a short cheer or "It was 19." shows."""

    QUESTION_SHARE = 0.44

    def __init__(self, game, problem_str, options, callback):
        rect = Utils.get_full_dialogue_rect(game)
        super().__init__(rect, None, visible=True)
        self.game = game
        self.problem_str = problem_str
        self.options = options
        self.answer_callback = callback
        q_w = int(rect.width * self.QUESTION_SHARE)
        self.question_rect = pygame.Rect(rect.x, rect.y, q_w, rect.height)
        self.right_rect = pygame.Rect(rect.x + q_w, rect.y, rect.width - q_w, rect.height)  # (older callers)
        self.text_x = self.question_rect.centerx
        self.text_y = rect.centery
        font = game.assets.fonts["num"] if max((len(str(o)) for o in options), default=0) <= 5 else game.assets.fonts["s_med"]
        self.answer_grid = MathAnswerGrid(self.right_rect, options, font, self.on_click,
                                          small_font=game.assets.fonts["s_med"])
        self.feedback = None  # set by the battle while it shows "Great job!" / the right answer
        self.speak_rect = pygame.Rect(self.question_rect.right - 74, self.question_rect.y + 24, 46, 46)

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
        from src.ui import theme
        theme.draw_textbox(surface, self.rect)
        card = self.question_rect.inflate(-28, -36)
        pygame.draw.rect(surface, (236, 242, 252), card, border_radius=14)
        pygame.draw.rect(surface, theme.TEXTBOX_ACCENT, card, 3, border_radius=14)
        if self.feedback:
            self._draw_feedback(surface, card)
            return
        font = self.game.assets.fonts["big"]
        if font.size(self.problem_str)[0] > card.width - 90:
            font = self.game.assets.fonts["num"]
        theme.shadow_text(surface, self.problem_str, font, card.centerx - 20, card.centery, align="center")
        self.answer_grid.draw(surface)
        from src.core import speech
        if speech.available():
            speech.draw_speaker(surface, self.speak_rect)

    def _draw_feedback(self, surface, card):
        import math
        from src.ui import theme
        fb = self.feedback
        grid = self.answer_grid
        t = 1 - fb["frames"] / max(1, fb["total"])  # 0 -> 1 over the beat
        marks = {fb["right"]: (46, 170, 74)}
        if not fb["correct"]:
            marks[fb["index"]] = (214, 72, 64)
        picked = grid.button_rects[fb["index"]] if fb["index"] < len(grid.button_rects) else None
        if picked is not None and not fb["correct"]:  # the wrong pick wobbles
            wobble = int(6 * math.sin(t * 30) * (1 - t))
            grid.button_rects[fb["index"]] = picked.move(wobble, 0)
            grid.draw(surface, marks)
            grid.button_rects[fb["index"]] = picked
        else:
            grid.draw(surface, marks)
        right = grid.button_rects[fb["right"]] if fb["right"] < len(grid.button_rects) else None
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
        font = self.game.assets.fonts["dialog"]
        color = (36, 140, 64) if fb["correct"] else theme.TEXT
        from src.ui.dialogue import wrap_text
        rows = wrap_text(fb["text"], font, card.width - 30)
        lh = font.get_linesize() + 6
        top = card.centery - len(rows) * lh // 2
        for i, row in enumerate(rows):
            theme.shadow_text(surface, row, font, card.centerx, top + i * lh + lh // 2, color=color, align="center")


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
