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
                 effect=None, stab=False, pp=None):
        self.pp = pp  # (PP left, most PP), or None (Struggle)
        if pp and pp[0] <= 0:  # out of PP: greyed out
            type_color = tuple(int(c * 0.45 + 70) for c in type_color)
        super().__init__(rect, name, font, callback, bg_color=type_color, autosize=False)
        self.small_font = small_font
        self.type_name = type_name
        self.type_color = type_color
        self.detail = detail
        self.effect = effect
        self.stab = stab

    def is_on(self):
        """The pointer or the keyboard highlight is on this move."""
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            return True
        kb = getattr(MoveButton, "keyboard", None)
        return bool(kb and kb.active and kb.focus and kb.focus[0] == id(self))

    def _badge(self, surface, cx, cy, rad):
        """How well it works on the foe, as a badge: green !! super, orange arrow not very, grey X none."""
        color = self.EFFECT[self.effect][0]
        pygame.draw.circle(surface, (16, 16, 20), (cx, cy + 2), rad + 2)
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

    def draw(self, surface):
        """Elite Battle's move buttons (Jordan's pick, 11-21): a charcoal body with cut ends in the
        move type's colour, its type tag, the name and the PP left. The one you're on fills with
        its type colour; a same-type move has a gold line inside the frame. Power, accuracy and how
        well it works are in MoveInfoPanel beside them (when the screen has one); without one, the
        power and accuracy go under the name."""
        if not self.visible:
            return
        from src.ui import theme
        r = self.rect
        on = self.is_on()
        col = tuple(self.type_color)[:3]
        c = max(8, min(18, r.h // 3))
        pts = theme.chamfer(r, c)
        theme.alpha_poly(surface, (0, 0, 0), theme.chamfer(r.move(4, 4), c), 120)
        body = theme.mix((34, 34, 40), col, 0.55 if on else 0.14)
        pygame.draw.polygon(surface, body, pts)
        for k in range(r.x + c, r.right - c, 8):  # the fine lines of Elite Battle's buttons
            pygame.draw.line(surface, theme.mix(body, (255, 255, 255), 0.06), (k, r.y + 6), (k, r.bottom - 7))
        pygame.draw.polygon(surface, (255, 255, 255) if on else col, pts, 3)
        if self.stab:  # same type as the user: a gold line inside the frame
            pygame.draw.polygon(surface, GOLD, theme.chamfer(r.inflate(-10, -10), max(4, c - 4)), 2)
        small = self.small_font
        two_rows = not getattr(self, "info_panel", False) and r.h >= 2 * small.get_height() + 30
        tag_h = small.get_height() + 8
        cy = r.y + 8 + tag_h // 2 if two_rows else r.centery
        x = r.x + c + 2
        x += theme.type_tag(surface, self.type_name.upper(), col, small, x, cy - tag_h // 2, h=tag_h) + 12
        right = r.right - c - 4
        if self.pp:  # PP left / most (red when empty, gold when low)
            have, most = self.pp
            pcol = (255, 110, 100) if have <= 0 else (255, 214, 90) if have * 4 <= most else WHITE
            right -= theme.shadow_text(surface, f"{have}/{most}", small, right, cy - small.get_height() // 2,
                                       color=pcol, align="right").w + 8
            pp = small.render("PP", False, theme.TEXT_DIM)
            surface.blit(pp, (right - pp.get_width(), cy - pp.get_height() // 2))
            right -= pp.get_width() + 12
        if self.effect in self.EFFECT:
            rad = max(10, min(13, r.h // 5))
            self._badge(surface, right - rad, cy, rad)
            right -= 2 * rad + 10
        name = self.text.upper()
        name_font = self.font if self.font.size(name)[0] <= right - x else small
        theme.shadow_text(surface, name, name_font, x, cy - name_font.get_height() // 2)
        if two_rows and self.detail:
            text = self.detail.replace("Sure hit", "--")
            theme.shadow_text(surface, text, small, r.x + c + 2, r.bottom - small.get_height() - 8, color=theme.TEXT_DIM)


class MoveInfoPanel(UIElement):
    """Beside the FIGHT menu's moves (Elite Battle's info box): the move you're on, its type,
    power, accuracy and, in words, how well it works on the foe (for pre-readers too: the badge)."""

    def __init__(self, rect, buttons, font, small_font):
        super().__init__(rect)
        self.buttons = buttons
        self.font, self.small = font, small_font
        self.last = None
        for b in buttons:
            b.info_panel = True

    def handle_event(self, event):
        return False

    def draw(self, surface):
        if not self.visible:
            return
        from src.ui import theme
        r = self.rect
        moves = [b for b in self.buttons if isinstance(b, MoveButton) and b.visible]
        cur = next((b for b in moves if b.is_on()), None) or self.last or (moves[0] if moves else None)
        self.last = cur
        pts = theme.chamfer(r, 12, tl=False, br=True, tr=False, bl=False)
        theme.alpha_poly(surface, (0, 0, 0), [(x + 4, y + 4) for x, y in pts], 110)
        pygame.draw.polygon(surface, (24, 24, 30), pts)
        if cur is None:
            pygame.draw.polygon(surface, theme.PANEL_BORDER, pts, 3)
            return
        col = tuple(cur.type_color)[:3]
        pygame.draw.polygon(surface, col, pts, 3)
        small = self.small
        lh = small.get_height() + 6
        y = r.y + 10
        parts = [p for p in (cur.detail or "").split("  ") if p]
        rows = []
        for p in parts:
            if p.startswith("Pow "):
                rows.append(("Power", p[4:]))
            elif p.startswith("Acc "):
                rows.append(("Accuracy", p[4:]))
            elif p == "Sure hit":
                rows.append(("Accuracy", "Never misses"))
            elif p == "Fixed":
                rows.append(("Power", "Fixed"))
            else:
                rows.append(("Kind", p))
        for label, value in rows[:3]:
            theme.shadow_text(surface, label, small, r.x + 14, y, color=theme.TEXT_LABEL)
            theme.shadow_text(surface, value, small, r.right - 14, y, align="right")
            y += lh
        if cur.effect in cur.EFFECT:
            ecol, word = cur.EFFECT[cur.effect]
            word = {"SUPER!": "SUPER EFFECTIVE", "WEAK": "NOT VERY EFFECTIVE"}.get(word, word)
            f = small if small.size(word)[0] <= r.w - 60 else small
            cur._badge(surface, r.x + 24, r.bottom - 20, 11)
            theme.shadow_text(surface, word, f, r.x + 44, r.bottom - 20 - f.get_height() // 2,
                              color=theme.mix(ecol, (255, 255, 255), 0.35))


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
        if len(self.options) == 3:  # three answers (<, = and >): one row, the full height
            bw3 = (self.rect.width - pad * 2 - gap * 2) // 3
            for i, option in enumerate(self.options):
                self.button_rects.append(pygame.Rect(self.rect.x + pad + i * (bw3 + gap), self.rect.y + pad, bw3,
                                                     self.rect.height - pad * 2 - 4))
                self.button_texts.append(str(option))
            return
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
            # (the 11-21 look: charcoal answer plates with cut corners, big white digits; the right
            # answer fills green, a wrong pick red)
            pts = theme.chamfer(r, 14)
            theme.alpha_poly(surface, (0, 0, 0), theme.chamfer(r.move(4, 5), 14), 120)
            pygame.draw.polygon(surface, fill or ((62, 62, 74) if hover else (44, 44, 52)), pts)
            pygame.draw.line(surface, (255, 255, 255) if fill else (84, 84, 98), (r.x + 14, r.y + 3), (r.right - 15, r.y + 3), 2)
            pygame.draw.polygon(surface, (255, 255, 255) if hover else theme.TEXTBOX_ACCENT if not fill else theme.shade(fill, 0.5),
                                pts, 3)
            color = WHITE if fill else theme.TEXT
            text = self.button_texts[i]
            font = self.font
            if font.size(text)[0] > r.w - 24:
                font = self.small_font
            if text in theme.SYMBOLS:  # <, = and >: drawn big (the number font's are tiny)
                theme.answer_text(surface, text, font, r.centerx, r.centery, color=WHITE if fill else theme.TEXT,
                                  shadow=fill or theme.TEXT_SHADOW)
            elif fill:
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
        pygame.draw.polygon(surface, (22, 22, 28), theme.chamfer(card, 14, tl=False))
        pygame.draw.polygon(surface, theme.TEXTBOX_ACCENT, theme.chamfer(card, 14, tl=False), 3)
        theme.slashes(surface, card.x + 12, card.y + 10, 12, theme.TEXTBOX_ACCENT)
        if self.feedback:
            self._draw_feedback(surface, card)
            return
        font = self.game.assets.fonts["big"]
        if font.size(self.problem_str)[0] > card.width - 90:
            font = self.game.assets.fonts["num"]
        theme.math_text(surface, self.problem_str, font, card.centerx - 20, card.centery)
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
        color = (110, 230, 130) if fb["correct"] else theme.TEXT
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
