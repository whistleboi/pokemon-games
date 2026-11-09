"""The MENU (Jordan, 11-08): a trainer's home screen. Your party on the left, your journey in the middle, everything you
can open on the right. Math Stats and Journal progress are here too."""
import math as _math
import types

import pygame

from src.minigames.base import icon
from src.states.base import GameState
from src.states.menu_grid import MenuGridState, _glyph
from src.ui import theme
from src.ui.panels import CommandButton
from src.utils import Utils

COLS = 4


def journal_progress(story, region=None):
    """(missions done, missions in all) for a region (the current one if None)."""
    keep = None
    try:
        if region is not None:
            keep = story.__dict__.get("get_current_region")
            story.get_current_region = lambda *a: region
        total = len(story.region_missions())
        done = sum(1 for m in story.get_all_journal_entries() if m.get("status") == "COMPLETED")
        return min(done, total), total
    except Exception:
        return 0, 0
    finally:
        if region is not None:
            del story.get_current_region
            if keep is not None:
                story.get_current_region = keep


def entries_for(state):
    """What the MENU offers on a town or route: by the order Jordan picked, what's unlocked only."""
    game, by_name = state.game, {b.text: b.callback for b in state.menu_entries}

    def coop():
        from src.states.coop_lobby import CoopState
        game.change_state(CoopState(game, state, "host"))
    out = [("POKEMON", getattr(state, "_open_party", None), theme.POKEMON), ("BAG", by_name.get("BAG"), theme.BAG),
           ("POKEDEX", getattr(state, "_open_pokedex", None), theme.FIGHT), ("MAP", by_name.get("MAP"), theme.RUN),
           ("JOURNAL", by_name.get("JOURNAL"), theme.RUN), ("BADGES", by_name.get("BADGES"), theme.BAG), ("PC", by_name.get("PC"), theme.POKEMON),
           ("FLY", by_name.get("FLY"), theme.RUN), ("NAV", by_name.get("NAV"), theme.POKEMON),
           ("STATS", lambda: game.change_state(StatsState(game, game.current_state)), theme.MEGA),
           ("SAVE", by_name.get("SAVE"), theme.POKEMON), ("LOAD", by_name.get("LOAD"), theme.BAG), ("CO-OP", coop, theme.MEGA),
           ("OPTIONS", by_name.get("OPTIONS"), theme.BACK), ("QUIT", "quit", theme.FIGHT)]
    return [e for e in out if e[1]]


class HomeMenuState(MenuGridState):
    def __init__(self, game, previous_state, entries, mission=None):
        self.mission_fn = mission
        rows = [types.SimpleNamespace(text=t, callback=(self.ask_quit if c == "quit" else self._and_back(c)), bg_color=b) for t, c, b in entries]
        super().__init__(game, previous_state, rows)
        w, h, H = game.width, game.height, theme.HEADER_H
        self.panel = screen_rect = pygame.Rect(0, 0, w, h)
        x0, top, gap = 660, H + 16, 10
        tile_w = (w - 16 - x0 - (COLS - 1) * gap) // COLS
        n_rows = max(1, _math.ceil(len(self.tiles) / COLS))
        tile_h = min(140, (h - top - 16 - (n_rows - 1) * gap) // n_rows)
        for i, b in enumerate(self.tiles):
            r, c = divmod(i, COLS)
            b.rect = pygame.Rect(x0 + c * (tile_w + gap), top + r * (tile_h + gap), tile_w, tile_h)
            icon_img = _glyph(b.label, min(56, tile_h - 44), game)
            ink = icon_img.get_bounding_rect()  # (just the picture, so it's truly centred)
            b.icon_surf = icon_img.subsurface(ink) if ink.w and ink.h else icon_img
        self.btn_close.rect = pygame.Rect(w - 16 - 150, 14, 150, 56)
        self.party_rects = [pygame.Rect(16, top + i * 92, 316, 84) for i in range(6)]
        self.info = pygame.Rect(342, top, 306, h - top - 16)
        self.quitting, self.quit_buttons = False, []
        f = game.assets.fonts
        self.quit_buttons = [
            CommandButton((w // 2 - 200, 270, 400, 62), "SAVE & QUIT TO TITLE", f["label"], lambda: self._quit(True), bg_color=theme.POKEMON, autosize=False),
            CommandButton((w // 2 - 200, 344, 400, 62), "QUIT TO TITLE (NO SAVE)", f["label"], lambda: self._quit(False), bg_color=theme.FIGHT, autosize=False),
            CommandButton((w // 2 - 200, 418, 400, 62), "CANCEL", f["label"], self.cancel_quit, bg_color=theme.BACK, autosize=False)]

    def _and_back(self, callback):
        """Open a screen so that its BACK / CANCEL comes back to this menu, not the map."""
        def run():
            callback()
            screen = self.game.current_state
            if screen is self:
                return
            for attr in ("previous_state", "back", "return_state"):
                if getattr(screen, attr, None) is self.previous_state:
                    setattr(screen, attr, self)
            if type(screen).__name__ == "OptionsState":
                screen.on_close = self._options_closed
        return run

    def _options_closed(self):
        self.game.update_save_data()
        self.game.change_state(self)

    def ask_quit(self):
        self.quitting = True

    def cancel_quit(self):
        self.quitting = False

    def _quit(self, save):
        from src.states.menus import MainMenuState
        if save:
            self.game.update_save_data()
            self.game.data.save()
        self.game.change_state(MainMenuState(self.game))

    def start(self):
        ui = self.game.ui_manager
        ui.elements.clear()
        for b in self.tiles + [self.btn_close]:
            ui.add_element(b)

    def _party_screen(self):
        tile = next((b for b in self.tiles if b.label == "POKEMON"), None)
        if tile is not None:
            tile.callback()

    def handle_events(self, events):
        for e in events:
            if self.quitting:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    self.cancel_quit()
                elif any(b.handle_event(e) for b in self.quit_buttons):
                    return
                continue
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return self.close()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and any(r.collidepoint(e.pos) for r in self.party_rects[:len(self.game.story_manager.player_team)]):
                return self._party_screen()

    def _mission(self):
        if self.mission_fn:
            return self.mission_fn()
        from src.world import guide
        return guide.tracked_mission(self.game)

    def draw(self):
        screen, f, story = self.game.screen, self.game.assets.fonts, self.game.story_manager
        theme.menu_background(screen, theme.ACCENT["options"], "MENU", f["button"], title_x=24)
        self.btn_close.draw(screen)
        for r, p in zip(self.party_rects, story.player_team):
            theme.card(screen, r)
            img = icon(self.game, p.id, 64)
            if img is not None:
                screen.blit(img, img.get_rect(center=(r.x + 44, r.centery)))
            theme.shadow_text(screen, p.display_name.upper()[:14], f["caption"], r.x + 84, r.y + 12)
            theme.shadow_text(screen, f"Lv{p.level}", f["caption"], r.right - 64, r.y + 12)
            if getattr(p, "is_egg", False):
                continue
            theme.hp_bar(screen, r.x + 84, r.y + 44, r.w - 110, p.current_hp, p.get_max_hp())
        self._draw_info(screen, f, story)
        for b in self.tiles:
            b.draw(screen)
            ic = b.icon_surf
            screen.blit(ic, ic.get_rect(center=(b.rect.centerx, b.rect.y + (b.rect.h - 34) // 2 + 4)))
            Utils.draw_text_outline(screen, b.label, f["caption"], (255, 255, 255), b.rect.centerx, b.rect.bottom - 18,
                                    outline_color=theme.shade(theme.theme_color(b.bg_color), 0.55), thickness=2)
        if self.quitting:
            shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 170))
            screen.blit(shade, (0, 0))
            for b in self.quit_buttons:
                b.draw(screen)

    def _draw_info(self, screen, f, story):
        r = self.info
        theme.card(screen, r)
        x, y, area = r.x + 16, r.y + 14, story.get_current_area_data() or {}
        place = theme.pokemon_word(area.get("route_name") or str(story.current_area_key).replace("_", " ").title())
        theme.shadow_text(screen, place[:22], f["label"], x, y)
        region = story.get_current_region()
        badges = len(story.badges.get(region, []))
        hours = int(story.play_seconds) // 3600
        for k, text in enumerate((f"Money  ${story.money:,}", f"Badges  {badges}", f"Played  {hours}h {int(story.play_seconds) // 60 % 60:02d}m")):
            theme.shadow_text(screen, text, f["caption"], x, y + 44 + k * 30)
        done, total = journal_progress(story)
        y2 = y + 150
        theme.shadow_text(screen, f"Journal  {done}/{total}", f["caption"], x, y2)
        bar = pygame.Rect(x, y2 + 32, r.w - 32, 12)
        pygame.draw.rect(screen, (88, 88, 96), bar, border_radius=6)
        if total:
            pygame.draw.rect(screen, theme.ACCENT["journal"], (bar.x, bar.y, int(bar.w * done / total), bar.h), border_radius=6)
        m = self._mission()
        if m:
            from src.ui.dialogue import wrap_text
            y3 = y2 + 66
            theme.shadow_text(screen, "Next:", f["caption"], x, y3, color=theme.shade(theme.ACCENT["journal"], 0.8))
            title = str(m.get("text") or m.get("title") or "")
            for k, row in enumerate(wrap_text(title, f["caption"], r.w - 32)[:2]):
                theme.shadow_text(screen, row, f["caption"], x, y3 + 30 + k * 26)
            desc = str(m.get("desc") or m.get("description") or "")
            for k, row in enumerate(wrap_text(desc, f["small"], r.w - 32)[:7]):
                theme.shadow_text(screen, row, f["small"], x, y3 + 88 + k * 24, color=(96, 102, 122))


OPS = (("add", "Add"), ("sub", "Subtract"), ("mul", "Multiply"), ("div", "Divide"))


class StatsState(GameState):
    """Math Stats and Journal progress, region by region."""

    def __init__(self, game, back):
        super().__init__(game)
        self.back = back
        f = game.assets.fonts
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], lambda: game.change_state(back), bg_color=theme.BACK, autosize=False)

    def handle_events(self, events):
        for e in events:
            if self.btn_back.handle_event(e):
                return
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return self.game.change_state(self.back)

    def update(self):
        pass

    @staticmethod
    def _bar(screen, x, y, w, right, wrong):
        pygame.draw.rect(screen, (88, 88, 96), (x, y, w, 12), border_radius=6)
        total = right + wrong
        if total:
            pygame.draw.rect(screen, theme.POKEMON, (x, y, int(w * right / total), 12), border_radius=6)

    def _regions(self, story):
        seen = [r for r, b in story.badges.items() if b]
        here = story.get_current_region()
        return ([here] if here not in seen else []) + seen

    def draw(self):
        screen, f, story = self.game.screen, self.game.assets.fonts, self.game.story_manager
        theme.menu_background(screen, theme.ACCENT["journal"], "MATH STATS", f["button"], title_x=176)
        self.btn_back.draw(screen)
        H, w, h = theme.HEADER_H, self.game.width, self.game.height
        left, right = pygame.Rect(16, H + 16, 620, h - H - 32), pygame.Rect(648, H + 16, w - 664, h - H - 32)
        theme.card(screen, left)
        theme.card(screen, right)
        s = story.math_stats
        total, x = s["right"] + s["wrong"], left.x + 20
        acc = f"{round(100 * s['right'] / total)}%" if total else "-"
        for k, (label, value) in enumerate((("Answered", f"{total:,}"), ("Accuracy", acc), ("Best streak", str(s["best"])), ("Quick answers", f"{s['quick']:,}"))):
            col, row = k % 2, k // 2
            theme.shadow_text(screen, label, f["caption"], x + col * 300, left.y + 14 + row * 66)
            theme.shadow_text(screen, value, f["label"], x + col * 300, left.y + 40 + row * 66)
        y = left.y + 156
        def line(name, pair, yy):
            r, wr = pair
            theme.shadow_text(screen, name, f["small"], x, yy - 6)
            self._bar(screen, x + 200, yy, 260, r, wr)
            pct = f"{round(100 * r / (r + wr))}%" if r + wr else "-"
            theme.shadow_text(screen, pct, f["small"], x + 480, yy - 6)
        for k, (key, name) in enumerate(OPS):
            line(name, s["ops"].get(key, [0, 0]), y + k * 34)
        y += 4 * 34 + 10
        for k, lv in enumerate(self.game.math.levels[:8]):
            line(lv["name"].title(), s["levels"].get(str(lv["id"]), [0, 0]), y + k * 30) if y + k * 30 < left.bottom - 12 else None
        x2 = right.x + 20
        theme.shadow_text(screen, "Journal progress", f["label"], x2, right.y + 14)
        for k, region in enumerate(self._regions(story)[:9]):
            done, n = journal_progress(story, region)
            yy = right.y + 60 + k * 58
            theme.shadow_text(screen, region.title(), f["caption"], x2, yy)
            theme.shadow_text(screen, f"{done}/{n}", f["caption"], right.right - 90, yy)
            bar = pygame.Rect(x2, yy + 30, right.w - 40, 12)
            pygame.draw.rect(screen, (88, 88, 96), bar, border_radius=6)
            if n:
                pygame.draw.rect(screen, theme.ACCENT["journal"], (bar.x, bar.y, int(bar.w * done / n), 12), border_radius=6)
