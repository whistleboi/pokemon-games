"""The Journal as a Quest Book (Jordan, 11-22; kanto_handoff/QUEST_BOOK_DESIGN.md): STORY (arcs and chapters), SIDE
(errands and events), FEATS (tiered achievements)."""

import pygame
from src.states.base import GameState
from src.ui.panels import CommandButton
from src.ui import theme
from src.utils import Utils
from src.config import WHITE

TABS = ("STORY", "SIDE", "FEATS")
GOLD = (232, 176, 40)
MEDALS = ((205, 127, 50), (192, 196, 206), (240, 196, 40), (120, 220, 230), (200, 120, 240))


# [REF-0060: Journal System]
class JournalState(GameState):
    """A list at the left (the tab's arcs and chapters, errands or feats), the row picked in full at the right (its
    page, GUIDE ME), the mission being guided in the bar at the bottom."""

    ROWS = 7  # list rows on show

    def __init__(self, game, previous_state, tab=None):
        super().__init__(game)
        self.previous_state = previous_state
        self.entries = game.story_manager.get_all_journal_entries()
        from src.world import guide
        tracked = guide.tracked_mission(game)
        self.tab = tab or ("SIDE" if tracked and str(tracked.get("type", "")).upper() != "MAIN" else "STORY")

        f = game.assets.fonts
        H = theme.HEADER_H
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.go_back, bg_color=theme.BACK,
                                      autosize=False)
        self.tab_buttons = {}
        # Orre: the book is the P*DA (its look, plus MAIL / SNAG LIST / MONITOR: src/states/systems/pda.py; Orre batch 8d)
        self.pda = str(game.story_manager.get_current_region() or "").upper() == "ORRE"
        self.pda_scroll = 0
        if self.pda:
            from src.states.systems import pda
            tabs = [(t, t) for t in TABS] + [(k, label) for k, label in pda.TABS if k != "journal"]
            x = game.width - 24
            for key, label in reversed(tabs):
                w = max(120, f["label"].size(label)[0] + 30)
                x -= w
                self.tab_buttons[key] = CommandButton((x, 18, w - 8, 48), label, f["label"], (lambda k=key: self.set_tab(k)),
                                                      bg_color=pda.ACCENT, autosize=False)
                x -= 4
            self.tab_buttons = dict(reversed(list(self.tab_buttons.items())))   # (left to right)
        else:
            for i, name in enumerate(TABS):
                x = game.width - 24 - (len(TABS) - i) * 158
                self.tab_buttons[name] = CommandButton((x, 14, 150, 56), name, f["button"], lambda n=name: self.set_tab(n),
                                                       bg_color=theme.TAB_OFF, autosize=False)
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
        self._build_rows()

    # ------------------------------------------------------------------ rows
    def _build_rows(self):
        """self.rows: what the list shows; self.missions: the mission behind each row (None for a feat)."""
        from src.world import guide, quest_book, feats
        story = self.game.story_manager
        tracked = guide.tracked_mission(self.game)
        rows = []
        pick = 0
        if self.tab == "STORY":
            for n, arc in enumerate(quest_book.arcs(self.game), 1):
                if arc["state"] == "later":
                    continue   # (arcs still to come: not in the book yet)
                now = next((c for c in arc["chapters"] if c["state"] == "now"), None)
                rows.append({"kind": "arc", "n": n, "arc": arc, "title": arc["title"], "done": arc["state"] == "done",
                             "mission": (now or {}).get("mission")})
                if arc["state"] == "now":   # the arc being played: its chapters under it
                    pick = len(rows) - 1
                    for k, c in enumerate(arc["chapters"], 1):
                        rows.append({"kind": "chapter", "n": k, "arc_n": n, "mission": c["mission"], "chapter": c,
                                     "title": c["title"] if c["state"] != "later" else "???", "done": c["state"] == "done"})
                        if c["state"] == "now":
                            pick = len(rows) - 1
        elif self.tab == "SIDE":
            side = [m for m in self.entries if str(m.get("type", "")).upper() != "MAIN"]
            side.sort(key=lambda m: 0 if m["status"] == "ACTIVE" else 1)
            for m in side:
                rows.append({"kind": "side", "mission": m, "title": m["text"], "done": m["status"] != "ACTIVE"})
                if tracked and tracked.get("id") == m["id"]:
                    pick = len(rows) - 1
        else:
            for r in feats.rows(story):
                rows.append(dict(r, kind="feat", mission=None, title=r["feat"].get("name", r["feat"]["id"]),
                                 done=r["next"] is None))
        self.rows = rows
        self.missions = [r["mission"] for r in rows]   # (the mission behind each row: GUIDE ME)
        self.selected = pick if rows else 0
        self.scroll_idx = max(0, min(self.selected - 2, len(rows) - self.ROWS))
        self._tab_colours()

    def _pda_tab(self):
        """On one of the P*DA's own tabs (MAIL, SNAG LIST, MONITOR), not the book's."""
        return self.pda and self.tab not in TABS

    def _tab_colours(self):
        if self.pda:
            from src.states.systems import pda
            for name, b in self.tab_buttons.items():
                b.bg_color = theme.BAG if name == self.tab else pda.ACCENT
        else:
            for name, b in self.tab_buttons.items():
                b.bg_color = theme.ACCENT["journal"] if name == self.tab else theme.TAB_OFF

    def set_tab(self, name):
        self.tab = "STORY" if name == "journal" else name   # ("journal": the P*DA's old first tab)
        self.pda_scroll = 0
        if self._pda_tab():
            self._tab_colours()
        else:
            self._build_rows()
        self._guide_layout()

    def row_rect(self, k):
        r = self.list_rect
        h = (r.h - 12 - 64 - (self.ROWS - 1) * 8) // self.ROWS
        return pygame.Rect(r.x + 12, r.y + 12 + k * (h + 8), r.w - 24, h)

    def scroll(self, step):
        if self._pda_tab():
            from src.states.systems import pda
            self.pda_scroll = max(0, min(max(0, len(pda.rows(self.game, self.tab)) - 1), self.pda_scroll + step))
            return
        self.scroll_idx = max(0, min(max(0, len(self.rows) - self.ROWS), self.scroll_idx + step))

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def start(self):
        for btn in [self.btn_back, self.btn_up, self.btn_down, self.btn_guide] + list(self.tab_buttons.values()):
            self.game.ui_manager.add_element(btn)
        for m in self.entries:
            if m["id"] not in self.game.story_manager.notified_missions:
                self.game.story_manager.notified_missions.append(m["id"])
        self._guide_layout()

    def _row(self):
        return self.rows[self.selected] if 0 <= self.selected < len(self.rows) else None

    def _mission(self):
        r = self._row()
        return r and r["mission"]

    def _guide_layout(self):
        """GUIDE ME on the picked row's mission (when it's active): the route guide and the Town Map point to it
        (src/world/guide.py); GUIDING turns it off."""
        from src.world import guide
        if self._pda_tab():
            self.btn_guide.set_visibility(False)
            return
        m = self._mission()
        tracked = guide.tracked_mission(self.game)
        on = bool(m and tracked and tracked.get("id") == m["id"])
        self.btn_guide.text = "GUIDING" if on else "GUIDE ME"
        self.btn_guide.bg_color = theme.BAG if on else theme.RUN
        row = self._row() or {}
        live = not row.get("chapter") or row["chapter"]["state"] == "now"
        self.btn_guide.set_visibility(bool(m) and m["status"] == "ACTIVE" and live)

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
                                     else "This one doesn't point to one place. Explore to find it!"])

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
                self.scroll(-1 if event.button == 4 else 1)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self._pda_tab():
                for k in range(self.ROWS):
                    i = self.scroll_idx + k
                    if i < len(self.rows) and self.row_rect(k).collidepoint(event.pos):
                        self.selected = i
                        self._guide_layout()
                        return

    def update(self):
        pass

    # ------------------------------------------------------------------ drawing
    def _chip(self, screen, rect, text, color, font):
        pygame.draw.rect(screen, color, rect, border_radius=rect.h // 2)
        tc, oc = theme.text_on(color)
        Utils.draw_text_outline(screen, text, font, tc, rect.centerx, rect.centery, outline_color=oc, thickness=1)

    def _where(self, mission, chapter=None):
        from src.world import guide
        prog = self.game.loader.area_data.get("STORY_PROGRESSION", {})
        area = None
        if chapter and chapter.get("state") == "now":
            area = guide.mission_target(self.game, mission)
        elif chapter:
            area = None
        elif mission:
            area = guide.mission_target(self.game, mission) if mission["status"] == "ACTIVE" else None
        return prog.get(area, {}).get("route_name") if area else None

    def draw(self):
        from src.ui.dialogue import wrap_text
        from src.ui.slot_list import fit
        from src.world import guide, feats
        screen = self.game.screen
        f = self.game.assets.fonts
        accent = theme.ACCENT["journal"]
        if self.pda:
            from src.states.systems import pda
            accent = pda.ACCENT
            theme.menu_background(screen, accent, "P  DA", f["button"], title_x=176)
            sx = 176 + f["button"].size("P ")[0] - f["button"].size(" ")[0] // 2   # (the font has no star: drawn between P and DA)
            sy, r = theme.HEADER_H // 2, 9
            import math as _m
            pts = [(sx + (r if k % 2 == 0 else r * 0.45) * _m.cos(_m.pi / 2 + k * _m.pi / 5),
                    sy - (r if k % 2 == 0 else r * 0.45) * _m.sin(_m.pi / 2 + k * _m.pi / 5)) for k in range(10)]
            pygame.draw.polygon(screen, (255, 232, 120), pts)
            if self._pda_tab():
                full = self.list_rect.union(self.detail_rect)
                total, shown = pda.draw(self, screen, full, self.pda_scroll)
                self.btn_up.set_visibility(self.pda_scroll > 0)
                self.btn_down.set_visibility(self.pda_scroll + shown < total)
                self.btn_guide.set_visibility(False)
                bf = f["s_med"]
                theme.draw_textbox(screen, self.bar_rect)
                hint = {"mail": "Your e-mail, newest first.", "snag": "Every Shadow Pokemon in Orre, and where it is.",
                        "monitor": "Snacks on a Poke Spot's tray bring visitors."}[self.tab]
                theme.shadow_text(screen, hint, bf, self.bar_rect.x + 32, self.bar_rect.centery - bf.get_height() // 2 - 2)
                self.game.ui_manager.draw(screen)
                return
        else:
            theme.menu_background(screen, accent, "QUEST BOOK", f["button"], title_x=176)
        tracked = guide.tracked_mission(self.game)
        mouse = pygame.mouse.get_pos()

        # The list.
        theme.draw_panel(screen, self.list_rect)
        if not self.rows:
            empty = {"STORY": "No story yet.", "SIDE": "No errands yet.", "FEATS": "No feats here."}[self.tab]
            theme.shadow_text(screen, empty, f["label"], self.list_rect.centerx, self.list_rect.y + 60,
                              color=(220, 226, 244), shadow=theme.MENU_BG, align="center")
        for k in range(self.ROWS):
            i = self.scroll_idx + k
            if i >= len(self.rows):
                break
            row, r = self.rows[i], self.row_rect(k)
            done = row["done"]
            indent = 28 if row["kind"] == "chapter" else 0
            rr = pygame.Rect(r.x + indent, r.y, r.w - indent, r.h)
            now = row["kind"] == "chapter" and row["chapter"]["state"] == "now"
            theme.card(screen, rr, hover=rr.collidepoint(mouse), selected=i == self.selected, accent=accent,
                       fill=(220, 224, 234) if done and row["kind"] != "chapter" else theme.TEXTBOX, radius=10)
            if row["kind"] == "arc":
                tag, col = f"ARC {row['n']}", theme.FIGHT
            elif row["kind"] == "chapter":
                tag, col = f"CH. {row['n']}", GOLD if now else (theme.POKEMON if done else theme.TAB_OFF)
            elif row["kind"] == "side":
                tag, col = "SIDE", theme.RUN
            else:
                nxt = row["next"]
                tag = "DONE" if nxt is None else feats.TIER_NAMES[min(nxt, 4)].upper()
                col = MEDALS[min((len(row["tiers"]) - 1) if nxt is None else nxt, 4)]
            chip = pygame.Rect(rr.x + 10, rr.centery - 12, 84, 24)
            self._chip(screen, chip, tag, col, f["caption"])
            tw = rr.right - 40 - chip.right - 12
            title = row["title"]
            if row["kind"] == "feat" and row["next"] is not None:
                title = f"{title}  {min(row['value'], row['tiers'][row['next']][0])}/{row['tiers'][row['next']][0]}"
            dim = done and row["kind"] != "chapter"
            theme.shadow_text(screen, fit(f["label"], title, tw), f["label"], chip.right + 12,
                              rr.centery - f["label"].get_height() // 2, color=(120, 126, 146) if dim else theme.TEXT)
            if row["kind"] == "chapter":
                dot = theme.POKEMON if done else (GOLD if now else theme.TAB_OFF)
            elif row["mission"] is not None:
                dot = theme.POKEMON if done else (theme.BAG if tracked and tracked.get("id") == row["mission"]["id"] else theme.RUN)
            else:
                dot = theme.POKEMON if done else theme.TAB_OFF
            pygame.draw.circle(screen, dot, (rr.right - 20, rr.centery), 8)
        if len(self.rows) > self.ROWS:
            first, last = self.scroll_idx + 1, min(len(self.rows), self.scroll_idx + self.ROWS)
            Utils.draw_text_outline(screen, f"{first}-{last} of {len(self.rows)}", f["label"], WHITE,
                                    self.list_rect.centerx, self.btn_up.rect.centery)
        self.btn_up.set_visibility(self.scroll_idx > 0)
        self.btn_down.set_visibility(self.scroll_idx + self.ROWS < len(self.rows))

        # The row picked, in full.
        d = self.detail_rect
        row = self._row()
        theme.card(screen, d, radius=16)
        if row and row["kind"] == "feat":
            self._draw_feat(screen, d, row)
        elif row:
            m, ch = row["mission"], row.get("chapter")
            hidden = ch is not None and ch["state"] == "later"
            if row["kind"] == "chapter":
                top = f"ARC {row['arc_n']}  -  CHAPTER {row['n']}"
                head = "???" if hidden else ch["title"]
                body = "This part of the story hasn't happened yet..." if hidden else ch.get("say") or ""
                status = {"done": "DONE", "now": "NOW", "open": "OPEN"}.get(ch["state"], "LATER")
            elif row["kind"] == "arc":
                top = f"ARC {row['n']}"
                head = row["title"]
                arc = row["arc"]
                if arc["state"] == "done":   # a finished arc: its chapters, as a short "previously..."
                    body = "Previously: " + "  /  ".join(c["title"] for c in arc["chapters"])
                    status = "DONE"
                else:
                    now = next((c for c in arc["chapters"] if c["state"] == "now"), None)
                    body = (now or {}).get("say") or ""
                    status = "NOW"
            else:
                top, head = "SIDE", row["title"]
                body = m.get("desc", "")
                status = "DONE" if m["status"] == "COMPLETED" else "NOW"
            chip = pygame.Rect(d.x + 24, d.y + 22, f["caption"].size(top)[0] + 28, 30)
            self._chip(screen, chip, top, theme.FIGHT if row["kind"] != "side" else theme.RUN, f["caption"])
            st = pygame.Rect(chip.right + 10, chip.y, f["caption"].size(status)[0] + 24, 30)
            self._chip(screen, st, status, theme.POKEMON if status == "DONE" else (GOLD if status == "NOW" else theme.TAB_OFF),
                       f["caption"])
            y = chip.bottom + 18
            for line in wrap_text(head, f["s_med"], d.w - 48)[:2]:
                theme.shadow_text(screen, line, f["s_med"], d.x + 24, y)
                y += 34
            y += 10
            pygame.draw.line(screen, (214, 218, 228), (d.x + 24, y), (d.right - 24, y), 2)
            y += 16
            for line in wrap_text(body, f["label"], d.w - 48)[:7]:
                theme.shadow_text(screen, line, f["label"], d.x + 24, y)
                y += 28
            ry = d.bottom - 24 - 62 - 58
            where = None if hidden or not m else self._where(m, ch)
            if where and status != "DONE":
                theme.shadow_text(screen, "Where", f["caption"], d.x + 24, ry, color=(110, 116, 136))
                theme.shadow_text(screen, where, f["label"], d.x + 24, ry + 22, color=(40, 110, 170))
            elif row["kind"] == "side" and m.get("reward") and m.get("reward") != "None":
                theme.shadow_text(screen, "Reward", f["caption"], d.x + 24, ry, color=(110, 116, 136))
                theme.shadow_text(screen, str(m["reward"]), f["label"], d.x + 24, ry + 22, color=(40, 110, 170))
        else:
            theme.shadow_text(screen, "Explore to find more!", f["s_med"], d.centerx, d.centery, align="center")

        # The bar: who's being guided.
        line = f"Guiding: {tracked['text']}" if tracked else "Pick a chapter or errand, then GUIDE ME to follow it."
        bf = f["s_med"]
        theme.draw_textbox(screen, self.bar_rect)
        theme.shadow_text(screen, fit(bf, line, self.bar_rect.w - 64), bf, self.bar_rect.x + 32,
                          self.bar_rect.centery - bf.get_height() // 2 - 2)
        self.game.ui_manager.draw(screen)

    def _draw_feat(self, screen, d, row):
        from src.ui.dialogue import wrap_text
        from src.world import feats
        f = self.game.assets.fonts
        feat = row["feat"]
        chip = pygame.Rect(d.x + 24, d.y + 22, 96, 30)
        self._chip(screen, chip, "FEAT", theme.MEGA, f["caption"])
        y = chip.bottom + 18
        theme.shadow_text(screen, row["title"], f["s_med"], d.x + 24, y)
        y += 40
        for line in wrap_text(feat.get("desc", ""), f["label"], d.w - 48)[:2]:
            theme.shadow_text(screen, line, f["label"], d.x + 24, y)
            y += 28
        y += 8
        theme.shadow_text(screen, f"So far: {row['value']:,}", f["label"], d.x + 24, y, color=(40, 110, 170))
        y += 40
        for i, (goal, reward, paid) in enumerate(row["tiers"]):
            name = feats.TIER_NAMES[min(i, 4)]
            pygame.draw.circle(screen, MEDALS[min(i, 4)] if paid or row["value"] >= goal else theme.TAB_OFF,
                               (d.x + 40, y + 14), 12)
            theme.shadow_text(screen, f"{name}: {goal:,}", f["label"], d.x + 62, y + 2,
                              color=theme.TEXT if not paid else (120, 126, 146))
            theme.shadow_text(screen, feats.reward_words(self.game, reward) + ("  (received)" if paid else ""),
                              f["caption"], d.x + 260, y + 6, color=(110, 116, 136))
            y += 40
            if y > d.bottom - 40:
                break
