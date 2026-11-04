"""The Journal: story and side missions."""

import pygame
from src.states.base import GameState
from src.ui.panels import CommandButton
from src.ui import theme
from src.utils import Utils
from src.config import WHITE


# [REF-0060: Journal System]
class JournalState(GameState):
    """The Journal (menu redesign, uncluttered): a list of missions at the left, the one picked
    in full at the right (its story, its reward, GUIDE ME), the mission being guided in the text
    box at the bottom."""

    ROWS = 7  # list rows on show

    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.missions = game.story_manager.get_all_journal_entries()
        self.missions.sort(key=lambda x: 0 if x["status"] == "ACTIVE" else 1)
        self.scroll_idx = 0
        self.selected = 0
        from src.world import guide
        tracked = guide.tracked_mission(game)
        if tracked:  # open on the mission being guided
            self.selected = next((i for i, m in enumerate(self.missions) if m["id"] == tracked.get("id")), 0)
            self.scroll_idx = max(0, min(self.selected, len(self.missions) - self.ROWS))

        f = game.assets.fonts
        H = theme.HEADER_H
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.go_back, bg_color=theme.BACK,
                                      autosize=False)
        self.bar_rect = pygame.Rect(16, game.height - 86, game.width - 32, 78)
        top = H + 16
        self.list_rect = pygame.Rect(24, top, 470, self.bar_rect.top - 12 - top)
        self.detail_rect = pygame.Rect(self.list_rect.right + 16, top, game.width - 24 - self.list_rect.right - 16,
                                       self.list_rect.h)
        arrow_y = self.list_rect.bottom - 52
        self.btn_up = CommandButton((self.list_rect.x + 12, arrow_y, 110, 42), "UP", f["label"],
                                    lambda: self.scroll(-1), bg_color=theme.ACCENT["journal"], autosize=False)
        self.btn_down = CommandButton((self.list_rect.right - 12 - 110, arrow_y, 110, 42), "DOWN", f["label"],
                                      lambda: self.scroll(1), bg_color=theme.ACCENT["journal"], autosize=False)
        d = self.detail_rect
        self.btn_guide = CommandButton((d.right - 24 - 240, d.bottom - 24 - 62, 240, 62), "GUIDE ME", f["button"],
                                       self.toggle_guide, bg_color=theme.RUN, autosize=False)
        self.guide_buttons = [self.btn_guide]

    def row_rect(self, k):
        r = self.list_rect
        h = (r.h - 12 - 64 - (self.ROWS - 1) * 8) // self.ROWS
        return pygame.Rect(r.x + 12, r.y + 12 + k * (h + 8), r.w - 24, h)

    def scroll(self, step):
        self.scroll_idx = max(0, min(max(0, len(self.missions) - self.ROWS), self.scroll_idx + step))

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def start(self):
        for btn in (self.btn_back, self.btn_up, self.btn_down, self.btn_guide):
            self.game.ui_manager.add_element(btn)
        for m in self.missions:
            if m["id"] not in self.game.story_manager.notified_missions:
                self.game.story_manager.notified_missions.append(m["id"])
        self._guide_layout()

    def _mission(self):
        return self.missions[self.selected] if 0 <= self.selected < len(self.missions) else None

    def _guide_layout(self):
        """GUIDE ME on the picked mission (when it's active): the route guide and the Town Map
        point to it (src/world/guide.py); GUIDING turns it off."""
        from src.world import guide
        m = self._mission()
        tracked = guide.tracked_mission(self.game)
        on = bool(m and tracked and tracked.get("id") == m["id"])
        self.btn_guide.text = "GUIDING" if on else "GUIDE ME"
        self.btn_guide.bg_color = theme.BAG if on else theme.RUN
        self.btn_guide.set_visibility(bool(m) and m["status"] == "ACTIVE")

    def toggle_guide(self):
        from src.world import guide
        m = self._mission()
        if m:
            tracked = guide.tracked_mission(self.game)
            self.track(m, bool(tracked) and tracked.get("id") == m["id"])

    def track(self, mission, on):
        from src.world import guide
        story = self.game.story_manager
        story.tracked_mission = "off" if on else mission["id"]
        guide._CACHE.clear()
        self._guide_layout()
        if not on:
            goal = guide.mission_target(self.game, mission)
            prog = self.game.loader.area_data.get("STORY_PROGRESSION", {})
            where = prog.get(goal, {}).get("route_name") if goal else None
            self.game.show_dialogue([f"Guiding you to {where}! Follow the gold buttons." if where
                                     else "This mission doesn't point to one place. Explore to find it!"])

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
                self.scroll(-1 if event.button == 4 else 1)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for k in range(self.ROWS):
                    i = self.scroll_idx + k
                    if i < len(self.missions) and self.row_rect(k).collidepoint(event.pos):
                        self.selected = i
                        self._guide_layout()
                        return

    def update(self):
        pass

    def draw(self):
        from src.ui.dialogue import wrap_text
        from src.world import guide
        screen = self.game.screen
        f = self.game.assets.fonts
        accent = theme.ACCENT["journal"]
        theme.menu_background(screen, accent, "JOURNAL", f["button"], title_x=176)
        active = sum(1 for m in self.missions if m["status"] == "ACTIVE")
        Utils.draw_text_outline(screen, f"{active} active   {len(self.missions) - active} done", f["button"], WHITE,
                                self.game.width - 24, theme.HEADER_H // 2 - 4, align="right",
                                outline_color=theme.shade(accent, 0.45), thickness=3)
        tracked = guide.tracked_mission(self.game)
        mouse = pygame.mouse.get_pos()

        # The list: tag, title, a dot for its status.
        theme.draw_panel(screen, self.list_rect)
        if not self.missions:
            theme.shadow_text(screen, "No missions yet.", f["label"], self.list_rect.centerx, self.list_rect.y + 60,
                              color=(220, 226, 244), shadow=theme.MENU_BG, align="center")
        for k in range(self.ROWS):
            i = self.scroll_idx + k
            if i >= len(self.missions):
                break
            m, r = self.missions[i], self.row_rect(k)
            done = m["status"] != "ACTIVE"
            theme.card(screen, r, hover=r.collidepoint(mouse), selected=i == self.selected, accent=accent,
                       fill=(220, 224, 234) if done else theme.TEXTBOX, radius=10)
            story = m["type"] == "MAIN"
            chip = pygame.Rect(r.x + 10, r.centery - 12, 84, 24)
            pygame.draw.rect(screen, theme.FIGHT if story else theme.RUN, chip, border_radius=12)
            Utils.draw_text_outline(screen, "STORY" if story else "SIDE", f["caption"], WHITE,
                                    chip.centerx, chip.centery, outline_color=(30, 30, 40), thickness=1)
            title = m["text"]
            tw = r.right - 40 - chip.right - 12
            from src.ui.slot_list import fit
            theme.shadow_text(screen, fit(f["label"], title, tw), f["label"], chip.right + 12,
                              r.centery - f["label"].get_height() // 2, color=(120, 126, 146) if done else theme.TEXT)
            dot = theme.POKEMON if done else (theme.BAG if tracked and tracked.get("id") == m["id"] else theme.RUN)
            pygame.draw.circle(screen, dot, (r.right - 20, r.centery), 8)
        if len(self.missions) > self.ROWS:
            first, last = self.scroll_idx + 1, min(len(self.missions), self.scroll_idx + self.ROWS)
            Utils.draw_text_outline(screen, f"{first}-{last} of {len(self.missions)}", f["label"], WHITE,
                                    self.list_rect.centerx, self.btn_up.rect.centery)
        self.btn_up.set_visibility(self.scroll_idx > 0)
        self.btn_down.set_visibility(self.scroll_idx + self.ROWS < len(self.missions))

        # The picked mission in full.
        d = self.detail_rect
        m = self._mission()
        theme.card(screen, d, radius=16)
        if m:
            story = m["type"] == "MAIN"
            chip = pygame.Rect(d.x + 24, d.y + 22, 96, 30)
            pygame.draw.rect(screen, theme.FIGHT if story else theme.RUN, chip, border_radius=15)
            Utils.draw_text_outline(screen, "STORY" if story else "SIDE", f["caption"], WHITE, chip.centerx,
                                    chip.centery, outline_color=(30, 30, 40), thickness=1)
            st_color = theme.POKEMON if m["status"] == "COMPLETED" else theme.BAG
            st = pygame.Rect(0, 0, f["caption"].size(m["status"])[0] + 24, 30)
            st.topleft = (chip.right + 10, chip.y)
            pygame.draw.rect(screen, st_color, st, border_radius=15)
            tc, oc = theme.text_on(st_color)
            Utils.draw_text_outline(screen, m["status"], f["caption"], tc, st.centerx, st.centery,
                                    outline_color=oc, thickness=1)
            y = chip.bottom + 18
            for row in wrap_text(m["text"], f["s_med"], d.w - 48)[:2]:
                theme.shadow_text(screen, row, f["s_med"], d.x + 24, y)
                y += 34
            y += 10
            pygame.draw.line(screen, (214, 218, 228), (d.x + 24, y), (d.right - 24, y), 2)
            y += 16
            for row in wrap_text(m.get("desc", ""), f["label"], d.w - 48)[:7]:
                theme.shadow_text(screen, row, f["label"], d.x + 24, y)
                y += 28
            reward = m.get("reward")
            if reward and reward != "None":
                ry = d.bottom - 24 - 62 - 58
                theme.shadow_text(screen, "Reward", f["caption"], d.x + 24, ry, color=(110, 116, 136))
                theme.shadow_text(screen, str(reward), f["label"], d.x + 24, ry + 22, color=(40, 110, 170))
        else:
            theme.shadow_text(screen, "Explore to find missions!", f["s_med"], d.centerx, d.centery, align="center")

        # The bar: who's being guided.
        line = f"Guiding: {tracked['text']}" if tracked else "Pick a mission, then GUIDE ME to follow it."
        from src.ui.slot_list import fit
        bf = f["s_med"]
        theme.draw_textbox(screen, self.bar_rect)
        theme.shadow_text(screen, fit(bf, line, self.bar_rect.w - 64), bf, self.bar_rect.x + 32,
                          self.bar_rect.centery - bf.get_height() // 2 - 2)

        self.game.ui_manager.draw(screen)
