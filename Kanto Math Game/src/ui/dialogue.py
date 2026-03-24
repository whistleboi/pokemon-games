# [REF-0001: System Imports]
import pygame
from src.ui.manager import UIElement
from src.utils import Utils
from src.config import WHITE, GOLD, BLACK


# [REF-0047: Classic Dialogue Box with Typewriter Effect and Click-to-Advance]
class ClassicDialogueBox(UIElement):
    def __init__(self, rect, text_lines, font, callback=None, visible=True):
        super().__init__(rect, callback, visible)
        self.text_lines = text_lines if isinstance(text_lines, list) else [text_lines]
        self.font = font
        self.current_line = 0
        self.visible_chars = 0
        self.speed = 3
        self.is_waiting_for_click = False
        self.is_finished = False
        self.on_line_finish = {}
        self.line_finish_triggered = False

    def update(self):
        if self.is_finished or self.is_waiting_for_click:
            return
        if self.current_line < len(self.text_lines):
            line = self.text_lines[self.current_line]
            if self.visible_chars < len(line):
                self.visible_chars += self.speed
                if self.visible_chars >= len(line):
                    self.visible_chars = len(line)
                    self.is_waiting_for_click = True
                    if not self.line_finish_triggered:
                        self.line_finish_triggered = True
                        if self.current_line in self.on_line_finish:
                            self.on_line_finish[self.current_line]()

    def advance(self):
        """Manually advances the dialogue state. If typing, finishes typing. If waiting, moves to next line or finishes."""
        if self.is_finished:
            return

        if self.is_waiting_for_click:
            self.current_line += 1
            self.visible_chars = 0
            self.line_finish_triggered = False
            self.is_waiting_for_click = False
            if self.current_line >= len(self.text_lines):
                self.is_finished = True
                if self.callback:
                    self.callback()
        else:
            if self.current_line < len(self.text_lines):
                self.visible_chars = len(self.text_lines[self.current_line])
                self.is_waiting_for_click = True
                if not self.line_finish_triggered:
                    self.line_finish_triggered = True
                    if self.current_line in self.on_line_finish:
                        self.on_line_finish[self.current_line]()

    def handle_event(self, event):
        if not self.visible:
            return False
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        ):
            self.advance()
            return True
        return False

    def reset(self, new_text):
        if isinstance(new_text, str):
            self.text_lines = [new_text]
        else:
            self.text_lines = new_text
        self.current_line = 0
        self.visible_chars = 0
        self.is_waiting_for_click = False
        self.is_finished = False
        self.on_line_finish = {}
        self.line_finish_triggered = False
        self.visible = True

    def draw(self, surface):
        if not self.visible:
            return
        Utils.draw_classic_panel(
            surface, self.rect.x, self.rect.y, self.rect.width, self.rect.height
        )

        if self.current_line < len(self.text_lines):
            full_line = self.text_lines[self.current_line]
            visible = full_line[: self.visible_chars]

            Utils.draw_multiline_text(
                surface,
                visible,
                self.font,
                WHITE,
                self.rect.centerx,
                self.rect.centery - 20,
                max_width=self.rect.width - 80,
                line_height=65,
                center=True,
            )

        if self.is_waiting_for_click and self.current_line < len(self.text_lines) - 1:
            arrow_y = self.rect.bottom - 32
            Utils.draw_text_outline(
                surface,
                "▼",
                self.font,
                GOLD,
                self.rect.centerx,
                arrow_y,
                outline_color=BLACK,
            )
