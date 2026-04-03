# [REF-0001: System Imports]
import pygame
import random
import os
import math
from src.config import GB_PANEL, GB_PANEL_DARK, GB_BORDER, GB_HIGHLIGHT, GB_TEXT, WHITE, BLACK, GOLD


# [REF-0003: Utilities]
class Utils:
    @staticmethod
    def get_actual_path(base, name):
        """Finds a folder/file case-insensitively in base directory."""
        if not os.path.exists(base):
            return os.path.join(base, name)
        target = os.path.join(base, name)
        if os.path.exists(target):
            return target
        try:
            for item in os.listdir(base):
                if item.lower() == name.lower():
                    return os.path.join(base, item)
        except OSError:
            pass
        return target

    @staticmethod
    def weighted_random_choice(choices_weights_dict):
        choices = list(choices_weights_dict.keys())
        weights = list(choices_weights_dict.values())
        total = sum(weights)
        r = random.uniform(0, total)
        upto = 0
        for c, w in zip(choices, weights):
            if upto + w >= r:
                return c
            upto += w
        return choices[-1]

    @staticmethod
    def index_files(directory):
        if not os.path.exists(directory):
            return {}
        return {f.lower(): f for f in os.listdir(directory)}

    @staticmethod
    def draw_text_outline(
        surface,
        text,
        font,
        color,
        x,
        y,
        outline_color=BLACK,
        thickness=3,
        align="center",
    ):
        if isinstance(text, list):
            text = " ".join(str(t) for t in text)
        text_surf = font.render(text, True, color)
        if align == "center":
            pos = (x - text_surf.get_width() // 2, y - text_surf.get_height() // 2)
        elif align == "right":
            pos = (x - text_surf.get_width(), y)
        else:
            pos = (x, y)

        for dx, dy in [
            (-thickness, 0),
            (thickness, 0),
            (0, -thickness),
            (0, thickness),
        ]:
            outline_surf = font.render(text, True, outline_color)
            surface.blit(outline_surf, (pos[0] + dx, pos[1] + dy))
        surface.blit(text_surf, pos)

    @staticmethod
    def draw_star(surface, color, center, size):
        points = []
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            radius = size if i % 2 == 0 else size // 2
            points.append(
                (
                    center[0] + radius * math.cos(angle),
                    center[1] + radius * math.sin(angle),
                )
            )
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, BLACK, points, 2)

    @staticmethod
    def find_json_file(directory, base_name):
        """Handles pokemon_xxx.json OR pokemon_xxx.json.json"""
        base = base_name.replace(".json", "")
        candidates = [base_name, base_name + ".json", base + ".json.json"]
        for cand in candidates:
            path = Utils.get_actual_path(directory, cand)
            if os.path.exists(path) and not os.path.isdir(path):
                return path
        return None

    @staticmethod
    def draw_classic_panel(surface, x, y, w, h, title=None):
        """Clean forest-style textbox — frames battle circles perfectly"""
        rect = pygame.Rect(x, y, w, h)

        shadow = rect.move(8, 8)
        pygame.draw.rect(surface, (60, 45, 30), shadow, border_radius=12)

        pygame.draw.rect(surface, GB_PANEL, rect, border_radius=12)

        inner = rect.inflate(-12, -12)
        pygame.draw.rect(surface, GB_PANEL_DARK, inner, border_radius=8)

        pygame.draw.rect(surface, GB_BORDER, rect, 8, border_radius=12)

        pygame.draw.line(surface, GB_HIGHLIGHT, (x + 8, y + 8), (x + w - 8, y + 8), 4)
        pygame.draw.line(surface, GB_HIGHLIGHT, (x + 8, y + 8), (x + 8, y + h - 8), 4)

        if title:
            Utils.draw_text_outline(
                surface,
                title,
                pygame.font.SysFont("impact", 26, bold=True),
                GB_TEXT,
                rect.centerx,
                rect.centery - h // 2 - 20,
            )

    @staticmethod
    def get_full_dialogue_rect(game):
        """Exact same rect as starter selection — full width, 25% height"""
        box_height = int(game.height * 0.25)
        return pygame.Rect(0, game.height - box_height, game.width, box_height)

    @staticmethod
    def draw_multiline_text(
        surface,
        text,
        font,
        color,
        x,
        y,
        max_width,
        line_height=65,
        center=True,
        outline_color=BLACK,
        align="center"
    ):
        """Exact multi-line wrapping from workingsim.py"""
        if isinstance(text, list):
            text = " ".join(str(t) for t in text)
        words = text.split(" ")
        lines = []
        current = []
        for word in words:
            test = " ".join(current + [word])
            if font.size(test)[0] <= max_width:
                current.append(word)
            else:
                lines.append(" ".join(current))
                current = [word]
        lines.append(" ".join(current))

        total_h = len(lines) * line_height
        start_y = y - total_h // 2 if center else y
        for i, line in enumerate(lines):
            Utils.draw_text_outline(
                surface,
                line,
                font,
                color,
                x,
                start_y + i * line_height,
                outline_color=outline_color,
                thickness=3,
                align=align
            )


# [REF-0044: Dummy Sound Class for Missing Cries]
class DummySound:
    def play(self):
        pass

    def set_volume(self, v):
        pass


# [REF-0045: MultiFont Class for Mixed Character Support]
class MultiFont:
    def __init__(self, primary_font, fallback_font):
        self.primary = primary_font
        self.fallback = fallback_font
        self.SPECIAL_CHARS = {"#", "<", ">", "é", "É"}

    def render(self, text, antialias, color, background=None):
        segments = []
        current_segment = ""

        if not text:
            return self.primary.render("", antialias, color)

        current_is_special = text[0] in self.SPECIAL_CHARS
        for char in text:
            is_special = char in self.SPECIAL_CHARS
            if is_special == current_is_special:
                current_segment += char
            else:
                segments.append((current_segment, current_is_special))
                current_segment = char
                current_is_special = is_special
        segments.append((current_segment, current_is_special))

        rendered_surfaces = []
        total_width = 0
        for segment_text, is_special in segments:
            font_to_use = self.fallback if is_special else self.primary
            surf = font_to_use.render(segment_text, antialias, color)
            rendered_surfaces.append(surf)
            total_width += surf.get_width()

        master_height = self.primary.get_height()
        master_surf = pygame.Surface(
            (total_width, master_height),
            pygame.SRCALPHA)
        current_x = 0
        for surf in rendered_surfaces:
            master_surf.blit(surf, (current_x, master_height - surf.get_height()))
            current_x += surf.get_width()
        return master_surf

    def size(self, text):
        segments = []
        current_segment = ""

        if not text:
            return (0, self.primary.get_height())

        current_is_special = text[0] in self.SPECIAL_CHARS
        for char in text:
            is_special = char in self.SPECIAL_CHARS
            if is_special == current_is_special:
                current_segment += char
            else:
                segments.append((current_segment, current_is_special))
                current_segment = char
                current_is_special = is_special
        segments.append((current_segment, current_is_special))

        total_width = 0
        for segment_text, is_special in segments:
            font_to_use = self.fallback if is_special else self.primary
            total_width += font_to_use.size(segment_text)[0]

        return (total_width, self.primary.get_height())

    def get_height(self):
        return self.primary.get_height()
