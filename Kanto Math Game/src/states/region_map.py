# [REF-0080: Region map and Fly]
"""The Town Map and Fly on the region's map (Jordan): each region is its part of the world map
(assets/world_map 2.png); towns sit where assets/map_points.json puts them
(dev/builders/build_map_points.py).

- TOWN MAP: where you are (a blinking marker), the towns you've visited, and the town your
  active Journal mission points to (a gold marker, see src/world/guide.py).
- FLY: tap a town you've visited, then FLY. LIST opens the town list (FlyState) instead.
Tabs switch between the regions you've been to."""
import json
import os

import pygame

from src.states.base import GameState
from src.ui.widgets import Button
from src.utils import Utils
from src.config import WHITE, BLACK, GOLD, RED, BLUE, GREEN

_DATA = {}


def map_data(game):
    """assets/map_points.json, loaded once."""
    if "d" not in _DATA:
        try:
            with open(os.path.join(game.assets.assets_dir, "map_points.json"), encoding="utf-8") as f:
                _DATA["d"] = json.load(f)
        except OSError:
            _DATA["d"] = {"views": {}, "points": {}, "sub_views": {}}
    return _DATA["d"]


def view_of(game, area_key):
    """The map an area is drawn on: its sub-region's (Sevii, Decolore) or its region's."""
    data = map_data(game)
    for view, keys in data.get("sub_views", {}).items():
        if area_key in keys:
            return view
    region = game.story_manager.area_region(area_key)
    return region if region in data.get("views", {}) else None


class RegionMapState(GameState):
    TOP = 84 + 10   # under the menu frame's header (src/ui/theme.py)
    PAD = 16
    BAR_H = 78

    def __init__(self, game, previous_state, fly=False):
        super().__init__(game)
        self.previous_state = previous_state
        self.fly = fly
        story = game.story_manager
        data = map_data(game)
        prog = game.loader.area_data.get("STORY_PROGRESSION", {})
        self.names = {k: a.get("route_name") or k.replace("_", " ").title() for k, a in prog.items()}
        self.visited = {k for k in data["points"] if story.story_flags.get(f"visited_{k}")}
        here_view = view_of(game, story.current_area_key)
        views = {view_of(game, k) for k in self.visited} | ({here_view} if here_view else set())
        order = list(data.get("views", {}))
        self.views = sorted((v for v in views if v), key=lambda v: (v != here_view, order.index(v)))
        self.view_idx = 0
        self.selected = None
        self.hover = None
        self.frame = 0
        try:
            self.world = pygame.image.load(os.path.join(game.assets.assets_dir, data.get("map", "world_map 2.png"))).convert()
        except (pygame.error, FileNotFoundError):
            self.world = None
        from src.world import guide
        self.goal = guide.goal_area(game)  # the active mission's town (gold marker), or None

        from src.ui.panels import CommandButton
        from src.ui import theme
        fonts = game.assets.fonts
        W, H = game.width, game.height
        self.bar_rect = pygame.Rect(16, H - 86, W - 32, self.BAR_H)
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", fonts["button"], self.go_back, bg_color=theme.BACK,
                                      autosize=False)
        self.btn_fly = CommandButton((self.bar_rect.right - 18 - 200, self.bar_rect.y + 10, 200, self.bar_rect.h - 26),
                                     "FLY", fonts["button"], self.fly_now, bg_color=theme.POKEMON, autosize=False,
                                     visible=False)
        self.btn_list = CommandButton((W - 16 - 130, 14, 130, 56), "LIST", fonts["button"], self.open_list,
                                      bg_color=theme.RUN, autosize=False, visible=fly)
        right = W - 16 - (146 if fly else 0)
        self.btn_next = CommandButton((right - 64, 14, 64, 56), ">", fonts["button"], lambda: self.turn(1),
                                      bg_color=theme.TAB_OFF, autosize=False, visible=len(self.views) > 1)
        self.btn_prev = CommandButton((right - 64 - 10 - 64, 14, 64, 56), "<", fonts["button"], lambda: self.turn(-1),
                                      bg_color=theme.TAB_OFF, autosize=False, visible=len(self.views) > 1)
        self._layout()

    # ---------------------------------------------------------------- layout
    @property
    def view(self):
        return self.views[self.view_idx] if self.views else None

    def _layout(self):
        """Scale this region's part of the world map to fit under the title bar."""
        self.map_img, self.map_rect, self.scale = None, pygame.Rect(0, 0, 0, 0), 1.0
        box = map_data(self.game)["views"].get(self.view) if self.view else None
        if not box or not self.world:
            return
        x0, y0, x1, y1 = box
        area_w = self.game.width - 2 * self.PAD
        area_h = self.game.height - self.TOP - self.BAR_H - 2 * self.PAD
        self.scale = min(area_w / (x1 - x0), area_h / (y1 - y0))
        w, h = int((x1 - x0) * self.scale), int((y1 - y0) * self.scale)
        crop = self.world.subsurface((x0, y0, x1 - x0, y1 - y0))
        self.map_img = pygame.transform.scale(crop, (w, h))  # crisp pixel art, like the games
        self.map_rect = self.map_img.get_rect(center=(self.game.width // 2, self.TOP + area_h // 2))
        self.origin = (x0, y0)

    def towns(self):
        """(area key, screen position) of every town on this map."""
        data = map_data(self.game)
        out = []
        for key, (x, y) in data["points"].items():
            if view_of(self.game, key) != self.view:
                continue
            sx = self.map_rect.x + (x - self.origin[0]) * self.scale
            sy = self.map_rect.y + (y - self.origin[1]) * self.scale
            out.append((key, (int(sx), int(sy))))
        return out

    def _hit(self, pos):
        best, dist = None, 26 ** 2
        for key, (x, y) in self.towns():
            d = (x - pos[0]) ** 2 + (y - pos[1]) ** 2
            if d < dist and (key in self.visited or not self.fly):
                best, dist = key, d
        return best

    # ---------------------------------------------------------------- actions
    def turn(self, step):
        self.view_idx = (self.view_idx + step) % len(self.views)
        self.selected = None
        self.btn_fly.set_visibility(False)
        self._layout()

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def open_list(self):
        from src.states.systems import FlyState
        self.game.change_state(FlyState(self.game, self.previous_state))

    def fly_now(self):
        if not self.selected:
            return
        if self.selected == self.game.story_manager.current_area_key:
            self.go_back()
            return
        from src.states.overworld import AreaTransitionState
        self.game.change_state(AreaTransitionState(self.game, self.selected))

    def start(self):
        for btn in (self.btn_back, self.btn_fly, self.btn_list, self.btn_prev, self.btn_next):
            self.game.ui_manager.add_element(btn)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEMOTION:
                self.hover = self._hit(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                key = self._hit(event.pos)
                if key is None:
                    continue
                if self.fly and key == self.selected:
                    self.fly_now()  # a second tap on the same town flies there
                    return
                self.selected = key
                self.btn_fly.set_visibility(self.fly and key in self.visited)
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_RIGHT) and len(self.views) > 1:
                self.turn(-1 if event.key == pygame.K_LEFT else 1)

    def update(self):
        self.frame += 1

    # ---------------------------------------------------------------- drawing
    def _label(self, screen, text, pos, color=WHITE):
        """A town's name in a small white card above it (its frame in the given colour)."""
        from src.ui import theme
        font = self.game.assets.fonts["label"]
        w, h = font.size(text)
        rect = pygame.Rect(0, 0, w + 28, h + 14)
        rect.midbottom = (pos[0], pos[1] - 18)
        rect.clamp_ip(self.map_rect)
        theme.card(screen, rect, selected=color != WHITE, accent=color, radius=10)
        theme.shadow_text(screen, text, font, rect.centerx, rect.centery, align="center")

    def draw(self):
        screen = self.game.screen
        fonts = self.game.assets.fonts
        from src.ui import theme
        title = "FLY" if self.fly else "TOWN MAP"
        if self.view:
            title += f"  -  {self.view.upper()}"
        theme.menu_background(screen, theme.ACCENT["map"], title, fonts["button"], title_x=176)
        theme.draw_textbox(screen, self.bar_rect)
        if not self.map_img:
            theme.shadow_text(screen, "No map for this place yet.", fonts["s_med"], self.game.width // 2,
                              self.game.height // 2, color=WHITE, shadow=theme.MENU_BG, align="center")
            self.game.ui_manager.draw(screen)
            return
        theme.draw_panel(screen, self.map_rect.inflate(16, 16), radius=10)
        screen.blit(self.map_img, self.map_rect)

        here = self.game.story_manager.current_area_key
        size = max(14, int(self.scale * 5))
        for key, (x, y) in self.towns():
            rect = pygame.Rect(0, 0, size, size)
            rect.center = (x, y)
            if key == self.goal:  # the active mission's town
                pygame.draw.rect(screen, GOLD, rect.inflate(10, 10), 4, border_radius=4)
            if key in self.visited:
                pygame.draw.rect(screen, WHITE, rect, 3, border_radius=3)
            if key == self.selected:
                pygame.draw.rect(screen, GREEN, rect.inflate(16, 16), 4, border_radius=6)
        for key, (x, y) in self.towns():  # you are here (blinks)
            if key == here and (self.frame // 15) % 2 == 0:
                pygame.draw.circle(screen, RED, (x, y), size // 2 + 4)
                pygame.draw.circle(screen, WHITE, (x, y), size // 2 + 4, 3)
        shown = self.selected or self.hover
        if shown:
            pos = dict(self.towns()).get(shown)
            if pos:
                name = self.names.get(shown, shown).upper()
                if self.fly and shown not in self.visited:
                    name += " (not visited)"
                self._label(screen, name, pos, GREEN if shown == self.selected else WHITE)
        if self.goal and view_of(self.game, self.goal) == self.view and not shown:
            pos = dict(self.towns()).get(self.goal)
            if pos:
                self._label(screen, "GOAL: " + self.names.get(self.goal, self.goal).upper(), pos, GOLD)
        if self.selected:
            hint = self.names.get(self.selected, self.selected) + (
                "  -  tap FLY" if self.fly and self.selected in self.visited else
                ("  -  not visited yet" if self.fly else ""))
        else:
            hint = "Tap a town you've visited, then FLY." if self.fly else "Tap a town to see its name."
        f = fonts["s_med"]
        theme.shadow_text(screen, hint, f, self.bar_rect.x + 32, self.bar_rect.centery - f.get_height() // 2 - 2)
        self.game.ui_manager.draw(screen)
