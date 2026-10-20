"""Keyboard play: arrow keys move a highlight between the buttons on screen, Enter/Space
presses the highlighted one (or moves the text on), Esc backs out (BACK / EXIT / CANCEL / NO).

It works on any screen without per-screen code: it finds the screen's buttons (in the UI
manager and in the screen's own button lists) and presses them with a simulated tap, so
every button does exactly what a tap would. Screens with their own key handling (name entry,
the region picker...) set `uses_keyboard = True` and are left alone.
"""
import math

import pygame

from src.ui.dialogue import ClassicDialogueBox
from src.ui.widgets import Button, MathAnswerGrid, MathBattleUI
from src.ui.panels import PartySlotUI

ARROWS = {pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0), pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1)}
SELECT = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
BACK_WORDS = ("BACK", "EXIT", "CANCEL", "NO", "CLOSE", "EXIT GYM", "LEAVE", "DONE")
HIGHLIGHT = (255, 214, 64)


class KeyboardNav:
    def __init__(self, game):
        self.game = game
        self.focus = None      # (key, rect) of the highlighted target
        self.active = False    # only show the highlight once the keyboard is being used

    # ---------------------------------------------------------------- finding targets
    def _targets(self):
        """[(key, rect, text)] for everything on screen that can be pressed."""
        state = self.game.current_state
        out, seen = [], set()

        def add_button(b):
            if id(b) in seen or not isinstance(b, Button):
                return
            seen.add(id(b))
            if b.visible and b.callback is not None and b.rect.w > 0:
                out.append((id(b), pygame.Rect(b.rect), str(getattr(b, "text", "")).upper()))

        def add(el):
            if el is None or id(el) in seen:
                return
            if isinstance(el, Button):
                add_button(el)
            elif isinstance(el, MathBattleUI):
                seen.add(id(el))
                if el.visible:
                    add(el.answer_grid)
            elif isinstance(el, MathAnswerGrid):
                seen.add(id(el))
                if el.visible:
                    for i, r in enumerate(el.button_rects):
                        out.append(((id(el), i), pygame.Rect(r), ""))
            elif isinstance(el, PartySlotUI):
                seen.add(id(el))
                if el.visible and el.pokemon:
                    out.append((id(el), pygame.Rect(el.rect), ""))
            elif hasattr(el, "buttons") and isinstance(getattr(el, "buttons"), list):
                seen.add(id(el))
                if getattr(el, "visible", True):
                    for b in el.buttons:
                        add(b)

        for el in list(self.game.ui_manager.elements):
            add(el)
        # The screen's own buttons and button lists (route menus, shop cards, quit prompts...)
        for value in list(vars(state).values()):
            if isinstance(value, (list, tuple)):
                for v in value:
                    if isinstance(v, (Button, PartySlotUI)) or hasattr(v, "buttons"):
                        add(v)
            elif isinstance(value, dict):
                for v in value.values():
                    if isinstance(v, Button):
                        add(v)
            elif isinstance(value, (Button, MathBattleUI, PartySlotUI)) or (
                    hasattr(value, "buttons") and hasattr(value, "rect")):
                add(value)
        extra = getattr(state, "nav_rects", None)
        if callable(extra):
            for i, r in enumerate(extra()):
                out.append((("extra", i), pygame.Rect(r), ""))
        return out

    def _dialogue(self):
        """A text box that is on screen and waiting (tapping it moves the story on)."""
        state = self.game.current_state
        boxes = [e for e in self.game.ui_manager.elements if isinstance(e, ClassicDialogueBox)]
        boxes += [v for v in vars(state).values() if isinstance(v, ClassicDialogueBox)]
        for box in reversed(boxes):
            if box.visible and box.rect.w > 0:
                return box
        return None

    # ---------------------------------------------------------------- input
    def handle(self, event):
        """Returns True when the key was used."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = False  # tapping hides the highlight
            return False
        if event.type != pygame.KEYDOWN:
            return False
        state = self.game.current_state
        if getattr(state, "uses_keyboard", False):
            return False
        if event.key in ARROWS:
            self._move(*ARROWS[event.key])
            return True
        if event.key in SELECT:
            return self._select()
        if event.key == pygame.K_ESCAPE:
            return self._back()
        return False

    def _current(self, targets):
        if self.focus:
            key, rect = self.focus
            for t in targets:
                if t[0] == key:
                    return t
            if targets:  # it went away: the nearest one instead
                cx, cy = rect.center
                return min(targets, key=lambda t: math.hypot(t[1].centerx - cx, t[1].centery - cy))
        return None

    def _move(self, dx, dy):
        targets = self._targets()
        if not targets:
            return
        cur = self._current(targets) if self.active else None
        if cur is None:
            pick = min(targets, key=lambda t: (t[1].top // 20, t[1].left))
        else:
            cx, cy = cur[1].center
            best, best_score = None, None
            for t in targets:
                if t[0] == cur[0]:
                    continue
                tx, ty = t[1].center
                along = (tx - cx) * dx + (ty - cy) * dy
                if along <= 4:
                    continue
                across = abs((tx - cx) * dy) + abs((ty - cy) * dx)
                score = along + 2 * across
                if best_score is None or score < best_score:
                    best, best_score = t, score
            pick = best or cur
        self.focus = (pick[0], pick[1])
        self.active = True

    def _tap(self, pos):
        """Press at pos exactly like a finger would (UI first, then the screen)."""
        game = self.game
        before = game.current_state
        down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)
        up = pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos)
        left = game.ui_manager.unconsumed([down, up], lambda: game.current_state is not before)
        if left and game.current_state is before:
            game.current_state.handle_events(left)
        if game.current_state is not before:
            self.focus = None

    def _select(self):
        targets = self._targets()
        cur = self._current(targets) if self.active else None
        box = self._dialogue()
        if cur is not None and (box is None or box.is_finished):
            self._tap(cur[1].center)
            return True
        if box is not None:
            self._tap(box.rect.center)
            return True
        if targets:  # nothing highlighted yet: highlight the first button
            self._move(0, 1)
            return True
        return False

    def _back(self):
        for key, rect, text in self._targets():
            if text in BACK_WORDS:
                self._tap(rect.center)
                return True
        state = self.game.current_state
        for name in ("go_back", "exit_shop", "on_back", "_cancel", "exit_gym"):
            fn = getattr(state, name, None)
            if callable(fn):
                fn()
                self.focus = None
                return True
        return False

    # ---------------------------------------------------------------- drawing
    def draw(self, surface):
        if not (self.active and self.focus):
            return
        targets = self._targets()
        cur = self._current(targets)
        if cur is None:
            return
        self.focus = (cur[0], cur[1])
        pulse = 2 + int(2 * (1 + math.sin(pygame.time.get_ticks() / 160)))
        pygame.draw.rect(surface, HIGHLIGHT, cur[1].inflate(10 + pulse, 10 + pulse), 5, border_radius=14)
