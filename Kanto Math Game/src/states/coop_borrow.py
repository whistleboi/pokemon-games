"""A guest picks up to 6 of the host's Pokemon to borrow (Jordan, 11-08)."""
import pygame

from src.minigames.base import icon
from src.states.base import GameState
from src.ui import theme
from src.ui.panels import CommandButton

PER_PAGE, COLS = 12, 4
MAX = 6


class CoopBorrowState(GameState):
    uses_keyboard = True

    def __init__(self, game, map_state, rows, swapping=False):
        super().__init__(game)
        self.map_state, self.rows, self.swapping = map_state, rows, swapping
        self.page, self.chosen = 0, [r["uid"] for r in rows if r.get("mine")]
        f = game.assets.fonts
        self.font, self.small = f["label"], f["caption"]
        W, H = game.width, game.height
        self.btn_done = CommandButton((W - 236, H - 76, 220, 62), "DONE", f["label"], self.done, bg_color=theme.POKEMON, autosize=False)
        self.btn_prev = CommandButton((16, H - 76, 160, 62), "PREV", f["label"], lambda: self.turn(-1), bg_color=theme.RUN, autosize=False)
        self.btn_next = CommandButton((190, H - 76, 160, 62), "NEXT", f["label"], lambda: self.turn(1), bg_color=theme.RUN, autosize=False)

    def pages(self):
        return max(1, (len(self.rows) + PER_PAGE - 1) // PER_PAGE)

    def turn(self, by):
        self.page = (self.page + by) % self.pages()

    def done(self):
        if self.swapping:
            self.map_state.swap(self.chosen)
        else:
            self.map_state.borrow(self.chosen)
        self.game.change_state(self.map_state)

    def cards(self):
        W = self.game.width
        w, h, gap = (W - 32 - (COLS - 1) * 10) // COLS, 150, 10
        shown = self.rows[self.page * PER_PAGE:(self.page + 1) * PER_PAGE]
        return [(pygame.Rect(16 + (i % COLS) * (w + gap), 76 + (i // COLS) * (h + gap), w, h), row) for i, row in enumerate(shown)]

    def handle_events(self, events):
        for e in events:
            if self.btn_done.handle_event(e):
                return
            if self.pages() > 1 and (self.btn_prev.handle_event(e) or self.btn_next.handle_event(e)):
                continue
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for r, row in self.cards():
                    if r.collidepoint(e.pos):
                        if row["uid"] in self.chosen:
                            self.chosen.remove(row["uid"])
                        elif len(self.chosen) < MAX:
                            self.chosen.append(row["uid"])

    def update(self):
        self.map_state.pump()

    def draw(self):
        screen = self.game.screen
        screen.fill((28, 36, 62))
        title = f"Borrow up to {MAX} Pokemon: {len(self.chosen)} picked"
        theme.shadow_text(screen, title, self.font, self.game.width // 2, 22, color=(255, 255, 255), shadow=(16, 20, 36), align="center")
        for r, row in self.cards():
            picked = row["uid"] in self.chosen
            pygame.draw.rect(screen, (70, 130, 90) if picked else (46, 56, 90), r, border_radius=10)
            pygame.draw.rect(screen, (255, 230, 120) if picked else (90, 104, 150), r, 4, border_radius=10)
            img = icon(self.game, row["id"], 96)
            if img is not None:
                screen.blit(img, img.get_rect(center=(r.x + 62, r.centery)))
            x = r.x + 124
            theme.shadow_text(screen, str(row["name"]).upper()[:12], self.small, x, r.y + 30, color=(255, 255, 255), shadow=(16, 20, 36))
            theme.shadow_text(screen, f"Lv {row['level']}", self.small, x, r.y + 62, color=(255, 255, 255), shadow=(16, 20, 36))
            theme.shadow_text(screen, f"HP {row['hp']}/{row['max']}", self.small, x, r.y + 94, color=(255, 255, 255), shadow=(16, 20, 36))
        self.btn_done.draw(screen)
        if self.pages() > 1:
            self.btn_prev.draw(screen)
            self.btn_next.draw(screen)
            theme.shadow_text(screen, f"{self.page + 1}/{self.pages()}", self.font, 400, self.game.height - 60, color=(255, 255, 255), shadow=(16, 20, 36))
