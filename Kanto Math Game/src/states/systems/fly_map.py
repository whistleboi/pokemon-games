"""Fly, the Town Map and the PokeNav."""

import pygame
import os
from src.states.base import GameState
from src.ui.widgets import Button
from src.ui.panels import CommandButton
from src.ui import theme
from src.ui.dialogue import ClassicDialogueBox
from src.utils import Utils
from src.config import WHITE, BLACK, RED, GOLD
from src.ui.mon_tags import fit_sprite


class FlyState(GameState):
    """Fly: every town you've visited, three columns, grouped by region (the
    region you're in first). The list scrolls like the PC: the mouse wheel, plus the arrow
    buttons and Page Up / Page Down."""

    COLS = 3
    ROW_H = 74      # a row of towns (or a region heading)
    CELL_H = 60
    LEFT, RIGHT = 40, 90     # margins (the arrows sit in the right one)
    TOP = 104                # first row of the list (under the menu frame's header)
    BOTTOM_PAD = 20

    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        story = game.story_manager
        fonts = game.assets.fonts
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", fonts["button"], self.go_back,
                                      bg_color=theme.BACK, autosize=False)
        x = game.width - self.RIGHT + 15
        self.btn_up = Button((x, self.TOP, 60, 60), "UP", fonts["tiny"], lambda: self.scroll_by(-1),
                             autosize=False)
        self.btn_down = Button((x, game.height - self.BOTTOM_PAD - 60, 60, 60), "DN", fonts["tiny"],
                               lambda: self.scroll_by(1), autosize=False)

        cities = []
        prog = game.loader.area_data.get("STORY_PROGRESSION", {})
        for key, data in prog.items():
            if data.get("area_type") == "town" and story.story_flags.get(f"visited_{key}"):
                cities.append((key, data.get("route_name", key)))
        if story.inventory.get("MT_SILVER_MAP", 0) > 0:
            silver_key = "SILVER_LEAGUE_PLATEAU"
            silver_name = prog.get(silver_key, {}).get("route_name", "Silver League")
            if not any(c[0] == silver_key for c in cities):
                cities.append((silver_key, silver_name))
        self.cities = cities

        # Rows: a heading for each region, then its towns three to a row.
        here = story.get_current_region()
        order = {r: i for i, (r, _) in enumerate(story.get_region_starts())}
        regions = sorted({story.area_region(k) for k, _ in cities},
                         key=lambda r: (r != here, order.get(r, 99), r))
        self.rows = []
        for region in regions:
            towns = [c for c in cities if story.area_region(c[0]) == region]
            self.rows.append(("heading", region.title()))
            for i in range(0, len(towns), self.COLS):
                self.rows.append(("towns", towns[i:i + self.COLS]))
        self.visible_rows = max(1, (game.height - self.TOP - self.BOTTOM_PAD) // self.ROW_H)
        self.first_row = 0
        self.cell_buttons = []

    @property
    def max_first_row(self):
        return max(0, len(self.rows) - self.visible_rows)

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def fly_to(self, key):
        from src.states.overworld import AreaTransitionState
        self.game.change_state(AreaTransitionState(self.game, key))

    def start(self):
        for btn in (self.btn_back, self.btn_up, self.btn_down):
            self.game.ui_manager.add_element(btn)
        self._layout()

    def scroll_by(self, rows):
        first = min(self.max_first_row, max(0, self.first_row + rows))
        if first != self.first_row:
            self.first_row = first
            self._layout()

    def _layout(self):
        """Buttons for the towns on the rows in view (rebuilt when the list scrolls)."""
        ui = self.game.ui_manager
        for btn in self.cell_buttons:
            if btn in ui.elements:
                ui.elements.remove(btn)
        self.cell_buttons = []
        width = self.game.width - self.LEFT - self.RIGHT
        cell_w = (width - (self.COLS - 1) * 16) // self.COLS
        for n, (kind, data) in enumerate(self.rows[self.first_row:self.first_row + self.visible_rows]):
            if kind != "towns":
                continue
            y = self.TOP + n * self.ROW_H
            for i, (key, name) in enumerate(data):
                rect = (self.LEFT + i * (cell_w + 16), y, cell_w, self.CELL_H)
                btn = Button(rect, name.upper(), self.game.assets.fonts["small"],
                             lambda k=key: self.fly_to(k), autosize=False)
                self.cell_buttons.append(btn)
                ui.add_element(btn)
        self.btn_up.set_visibility(self.first_row > 0)
        self.btn_down.set_visibility(self.first_row < self.max_first_row)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):  # the wheel, as in the PC
                self.scroll_by(-1 if event.button == 4 else 1)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEDOWN:
                self.scroll_by(self.visible_rows - 1)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEUP:
                self.scroll_by(-(self.visible_rows - 1))

    def update(self):
        pass

    def draw(self):
        screen = self.game.screen
        fonts = self.game.assets.fonts
        title = "FLY"
        theme.menu_background(screen, theme.ACCENT["map"], title, fonts["button"], title_x=176)
        if not self.cities:
            theme.shadow_text(screen, "You haven't visited any towns yet.", fonts["s_med"], self.game.width // 2,
                              self.game.height // 2, color=WHITE, shadow=theme.MENU_BG, align="center")
        for n, (kind, data) in enumerate(self.rows[self.first_row:self.first_row + self.visible_rows]):
            if kind == "heading":
                y = self.TOP + n * self.ROW_H + self.CELL_H // 2
                head = Utils.draw_text_outline(screen, data.upper(), fonts["button"], WHITE, self.LEFT, y,
                                               align="left", outline_color=theme.PANEL_BORDER, thickness=3)
                pygame.draw.line(screen, theme.PANEL_EDGE, (self.LEFT + 240, y), (self.game.width - self.RIGHT, y), 3)
        if self.max_first_row:  # where you are in the list
            track = pygame.Rect(self.game.width - self.RIGHT + 40, self.TOP + 75, 10,
                                self.game.height - self.TOP - self.BOTTOM_PAD - 150)
            pygame.draw.rect(screen, (60, 60, 90), track, border_radius=5)
            share = self.visible_rows / len(self.rows)
            h = max(30, int(track.height * share))
            y = track.y + int((track.height - h) * self.first_row / self.max_first_row)
            pygame.draw.rect(screen, GOLD, (track.x, y, track.width, h), border_radius=5)
        self.game.ui_manager.draw(screen)


class MapState(GameState):
    def __init__(self, game, previous_state, initial_message=None):
        super().__init__(game)
        self.previous_state = previous_state

        self.map_list = []
        inv = self.game.story_manager.inventory
        if inv.get("TOWN_MAP", 0) > 0:
            self.map_list.append((os.path.join(self.game.assets.assets_dir, "kanto_map.png"), "Kanto Region"))
        if inv.get("JOHTO_MAP", 0) > 0:
            self.map_list.append((os.path.join(self.game.assets.assets_dir, "johto_map.png"), "Johto Region"))

        if not self.map_list:
            self.map_list.append((os.path.join(self.game.assets.assets_dir, "kanto_map.png"), "World Map"))

        self.current_idx = 0
        self.map_img = None
        self._load_current_map()

        msg = initial_message if initial_message else [f"TOWN MAP: Exploring the {self.map_list[self.current_idx][1]}!"]
        self.dialogue_box = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(game), msg, self.game.assets.fonts["med"]
        )

        self.btn_back = Button(
            (20, 20, 120, 50), "EXIT", game.assets.fonts["tiny"],
            self.go_back, bg_color=RED
        )

        cy = game.height // 2
        show_arrows = len(self.map_list) > 1
        self.btn_prev = Button((20, cy - 30, 60, 60), "<", game.assets.fonts["med"], self.prev_map, visible=show_arrows)
        self.btn_next = Button((game.width - 80, cy - 30, 60, 60), ">", game.assets.fonts["med"], self.next_map, visible=show_arrows)

    def _load_current_map(self):
        path, label = self.map_list[self.current_idx]
        if os.path.exists(path):
            try:
                raw = pygame.image.load(path).convert()
                box_top = Utils.get_full_dialogue_rect(self.game).top
                self.map_img = pygame.transform.scale(raw, (self.game.width, box_top))
            except pygame.error:
                self.map_img = None
        else:
            self.map_img = None

    def prev_map(self):
        self.current_idx = (self.current_idx - 1) % len(self.map_list)
        self._load_current_map()
        self.dialogue_box.reset([f"Now viewing: {self.map_list[self.current_idx][1]}"])

    def next_map(self):
        self.current_idx = (self.current_idx + 1) % len(self.map_list)
        self._load_current_map()
        self.dialogue_box.reset([f"Now viewing: {self.map_list[self.current_idx][1]}"])

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.elements.clear()
        self.game.ui_manager.add_element(self.btn_back)
        self.game.ui_manager.add_element(self.btn_prev)
        self.game.ui_manager.add_element(self.btn_next)
        self.game.ui_manager.add_element(self.dialogue_box)

    def handle_events(self, events):
        for event in events:
            self.dialogue_box.handle_event(event)

    def update(self):
        self.dialogue_box.update()

    def draw(self):
        self.game.screen.fill(BLACK)
        if self.map_img:
            self.game.screen.blit(self.map_img, (0, 0))
        self.dialogue_box.draw(self.game.screen)
        self.game.ui_manager.draw(self.game.screen)


class PokeNavState(GameState):
    """HUD extension that displays exact route encounter rates and completion status."""
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.area_data = game.story_manager.get_current_area_data()
        self.pool_key = self.area_data.get("wild_pool_percentages")
        self.pool = game.loader.area_data.get(self.pool_key, {}) if self.pool_key else {}
        
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", game.assets.fonts["button"], self.go_back,
                                      bg_color=theme.BACK, autosize=False)

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.add_element(self.btn_back)

    def handle_events(self, events):
        pass

    def update(self):
        pass

    def draw(self):
        """The menu frame: the area's wild Pokemon as white rows (sprite, name, caught ball, how often
        it appears), in two columns. Rare ones (< 5%) stay hidden without the Devon Scope."""
        screen = self.game.screen
        f = self.game.assets.fonts
        accent = theme.ACCENT["tool"]
        route_name = self.area_data.get("route_name", "Unknown Area")
        theme.menu_background(screen, accent, f"POKENAV: {route_name.upper()}", f["button"], title_x=176)
        if not self.pool:
            theme.shadow_text(screen, "No wild Pokemon data for this area.", f["s_med"], self.game.width // 2,
                              self.game.height // 2, color=WHITE, shadow=theme.MENU_BG, align="center")
            self.game.ui_manager.draw(screen)
            return
        has_devon_scope = self.game.story_manager.inventory.get("DEVON_SCOPE", 0) > 0
        caught_data = self.game.data.data.get("pokedex", {})
        caught_ids = {int(v.get("id", -1)) for v in caught_data.values() if isinstance(v, dict)}
        rows = sorted(self.pool.items(), key=lambda x: x[1], reverse=True)
        top, gap, rh = theme.HEADER_H + 16, 10, 64
        per_col = max(1, (self.game.height - 16 - top + gap) // (rh + gap))
        cw = (self.game.width - 48 - 16) // 2
        for i, (p_id_str, chance) in enumerate(rows[:per_col * 2]):
            p_id = int(p_id_str)
            col, row = i // per_col, i % per_col
            rect = pygame.Rect(24 + col * (cw + 16), top + row * (rh + gap), cw, rh)
            rare = chance < 5
            hidden = rare and not has_devon_scope
            theme.card(screen, rect, selected=rare and has_devon_scope, accent=theme.BAG, radius=10)
            if not hidden:
                img = self.game.assets.get_pokemon_image(p_id, "normal", False)
                if img:
                    spr = fit_sprite(img, 52, 52)
                    screen.blit(spr, spr.get_rect(center=(rect.x + 36, rect.centery)))
            name = "???" if hidden else self.game.assets.pokemon_names.get(str(p_id), "???").title()
            theme.shadow_text(screen, name, f["label"], rect.x + 74, rect.y + 10)
            if p_id in caught_ids and self.game.assets.ui_ball:
                screen.blit(pygame.transform.scale(self.game.assets.ui_ball, (20, 20)), (rect.right - 34, rect.y + 10))
            bar = pygame.Rect(rect.x + 74, rect.bottom - 20, rect.w - 74 - 90, 10)
            pygame.draw.rect(screen, (210, 214, 224), bar, border_radius=5)
            pygame.draw.rect(screen, theme.BAG if rare else theme.POKEMON,
                             (bar.x, bar.y, max(4, int(bar.w * min(1.0, chance / 50))), bar.h), border_radius=5)
            theme.shadow_text(screen, f"{chance}%", f["label"], rect.right - 16, rect.bottom - 30, align="right")
        self.game.ui_manager.draw(screen)
