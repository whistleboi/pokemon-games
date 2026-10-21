"""The overworld MENU: one big button opens a grid of large icon tiles (Bag, Party, Badges,
Save...) instead of a column of small buttons. Each tile runs the same action its old button did."""
import math

import pygame

from src.states.base import GameState
from src.ui.widgets import Button
from src.utils import Utils
from src.config import WHITE, BLACK, GOLD, RED

INK = (40, 40, 52)


def _glyph(label, size, game):
    """A simple drawn icon for a menu entry (or its item sprite)."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    w = max(3, size // 16)

    def box(rect, fill=WHITE, radius=6):
        pygame.draw.rect(s, fill, rect, border_radius=radius)
        pygame.draw.rect(s, INK, rect, w, border_radius=radius)

    if label == "PC":
        box((6, 8, size - 12, size - 26))
        pygame.draw.rect(s, (110, 190, 240), (12, 14, size - 24, size - 38), border_radius=4)
        pygame.draw.rect(s, INK, (c - 6, size - 18, 12, 8))
        box((c - 18, size - 12, 36, 8), radius=3)
    elif label == "BAG":
        pygame.draw.arc(s, INK, (c - 14, 4, 28, 26), 0, math.pi, w + 1)
        box((8, 18, size - 16, size - 24), fill=(240, 200, 120), radius=12)
        pygame.draw.line(s, INK, (10, 34), (size - 10, 34), w)
        box((c - 7, 28, 14, 12), fill=(250, 230, 160), radius=3)
    elif label == "BADGES":
        pygame.draw.polygon(s, (220, 60, 70), [(c - 14, 4), (c - 2, 4), (c - 8, 26)])
        pygame.draw.polygon(s, (70, 110, 220), [(c + 2, 4), (c + 14, 4), (c + 8, 26)])
        pygame.draw.circle(s, INK, (c, c + 8), size // 3 + w)
        pygame.draw.circle(s, GOLD, (c, c + 8), size // 3)
        pts = [(c + math.cos(a) * (size // 5 if i % 2 else size // 9 + 3) * (1 if i % 2 == 0 else 1),
                c + 8 + math.sin(a) * (size // 5 if i % 2 == 0 else size // 11))
               for i, a in enumerate([-math.pi / 2 + k * math.pi / 5 for k in range(10)])]
        pygame.draw.polygon(s, WHITE, pts)
    elif label == "SAVE":
        box((8, 8, size - 16, size - 16), fill=(70, 120, 220))
        box((16, 10, size - 32, 16), fill=WHITE, radius=2)
        box((16, size - 28, size - 32, 16), fill=(200, 210, 230), radius=2)
    elif label == "LOAD":
        box((6, 14, size - 12, size - 22), fill=(240, 190, 80))
        box((6, 10, 24, 10), fill=(240, 190, 80), radius=3)
        pygame.draw.polygon(s, WHITE, [(c - 10, c + 4), (c + 10, c + 4), (c, c + 16)])
        pygame.draw.rect(s, WHITE, (c - 4, c - 10, 8, 16))
    elif label == "JOURNAL":
        box((10, 6, size - 20, size - 12), fill=(150, 90, 200))
        box((18, 12, size - 32, size - 24), fill=WHITE, radius=3)
        for k in range(4):
            pygame.draw.line(s, INK, (24, 22 + k * 9), (size - 22, 22 + k * 9), 2)
    elif label == "NAV":
        pygame.draw.circle(s, INK, (c, c), c - 4)
        pygame.draw.circle(s, WHITE, (c, c), c - 4 - w)
        pygame.draw.polygon(s, (220, 60, 70), [(c, 10), (c - 7, c), (c + 7, c)])
        pygame.draw.polygon(s, (120, 120, 140), [(c, size - 10), (c - 7, c), (c + 7, c)])
    elif label == "OPTIONS":
        for k in range(8):
            a = k * math.pi / 4
            pygame.draw.circle(s, INK, (c + math.cos(a) * (c - 10), c + math.sin(a) * (c - 10)), 7)
        pygame.draw.circle(s, INK, (c, c), c - 10)
        pygame.draw.circle(s, (190, 190, 205), (c, c), c - 10 - w)
        pygame.draw.circle(s, INK, (c, c), 8)
    else:
        item = {"FLY": "AIR_BALLOON", "MAP": "TOWN_MAP"}.get(label)
        img = game.assets.get_item_image(item) if item else None
        if img:
            return pygame.transform.scale(img, (size, size))
        pygame.draw.circle(s, WHITE, (c, c), c - 6)
        pygame.draw.circle(s, INK, (c, c), c - 6, w)
    return s


class MenuGridState(GameState):
    COLS = 3

    def __init__(self, game, previous_state, entries):
        super().__init__(game)
        self.previous_state = previous_state
        self.entries = [e for e in entries if e.callback]
        self.backdrop = game.screen.copy()
        shade = pygame.Surface(game.screen.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 150))
        self.backdrop.blit(shade, (0, 0))

        w, h = game.width, game.height
        rows = max(1, math.ceil(len(self.entries) / self.COLS))
        gap = 16
        tile_w = 260
        tile_h = min(140, (h - 200 - gap * (rows - 1)) // rows)
        grid_w = self.COLS * tile_w + (self.COLS - 1) * gap
        self.panel = pygame.Rect(0, 0, grid_w + 64, rows * tile_h + (rows - 1) * gap + 130)
        self.panel.center = (w // 2, h // 2)
        top = self.panel.y + 100
        fonts = game.assets.fonts
        self.tiles = []
        for i, entry in enumerate(self.entries):
            r, col = divmod(i, self.COLS)
            rect = (self.panel.x + 32 + col * (tile_w + gap), top + r * (tile_h + gap), tile_w, tile_h)
            btn = Button(rect, "", fonts["s_med"], self._runner(entry.callback),
                         bg_color=entry.bg_color, autosize=False)
            btn.label = entry.text
            btn.icon_surf = _glyph(entry.text, min(72, tile_h - 50), game)
            self.tiles.append(btn)
        self.btn_close = Button((self.panel.right - 170, self.panel.y + 22, 146, 58), "CLOSE", fonts["small"],
                                self.close, bg_color=RED, autosize=False)

    def _runner(self, callback):
        def run():
            callback()
        return run

    def close(self):
        self.game.change_state(self.previous_state)

    def start(self):
        ui = self.game.ui_manager
        ui.elements.clear()
        for b in self.tiles + [self.btn_close]:
            ui.add_element(b)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.panel.collidepoint(event.pos):
                self.close()  # tap outside the panel closes it
                return

    def update(self):
        pass

    def draw(self):
        screen, fonts = self.game.screen, self.game.assets.fonts
        screen.blit(self.backdrop, (0, 0))
        pygame.draw.rect(screen, (28, 36, 72), self.panel, border_radius=22)
        pygame.draw.rect(screen, WHITE, self.panel, 5, border_radius=22)
        Utils.draw_text_outline(screen, "MENU", fonts["med"], GOLD, self.panel.x + 40, self.panel.y + 28, align="left")
        self.btn_close.draw(screen)
        for b in self.tiles:
            b.draw(screen)
            icon = b.icon_surf
            screen.blit(icon, icon.get_rect(center=(b.rect.centerx, b.rect.y + 12 + icon.get_height() // 2)))
            Utils.draw_text_outline(screen, b.label, fonts["small"], WHITE, b.rect.centerx, b.rect.bottom - 22,
                                    outline_color=BLACK)
