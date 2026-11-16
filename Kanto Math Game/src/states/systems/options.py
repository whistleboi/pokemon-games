"""OPTIONS (Jordan, 11-08): tabs, one setting to a row, each change at once."""
import pygame

from src.core import settings
from src.states.base import GameState
from src.ui import theme
from src.ui.panels import CommandButton

TABS = ("MATH", "GAMEPLAY", "TEXT & BATTLE", "SOUND")
ROW_H, ROW_GAP = 72, 12


class OptionsState(GameState):
    uses_keyboard = True

    def __init__(self, game, return_state, on_close):
        super().__init__(game)
        self.return_state, self.on_close, self.story = return_state, on_close, game.story_manager
        self.guest = bool(getattr(game.data, "read_only", False))  # (a co-op guest: the journey's settings are the host's)
        self.tabs = [t for t in TABS if not (self.guest and t == "GAMEPLAY")]
        self.tab, self.row, self.note = 0, 0, ""
        f = game.assets.fonts
        self.f = f
        w, h = game.width, game.height
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.close, bg_color=theme.BACK, autosize=False)
        H = theme.HEADER_H
        tab_w = (w - 32 - 10 * (len(self.tabs) - 1)) // len(self.tabs)
        self.tab_rects = [pygame.Rect(16 + i * (tab_w + 10), H + 10, tab_w, 54) for i in range(len(self.tabs))]
        self.bar = pygame.Rect(16, h - 86, w - 32, 78)
        self.levels = [{"key": "AUTO", "name": "AUTO", "desc": ""}] + [{"key": lv["id"], "name": lv["name"], "desc": lv["desc"]} for lv in game.math.levels]
        gap, top = 10, H + 76
        card_w, card_h = (w - 32 - 2 * gap) // 3, 72
        self.level_rects = [pygame.Rect(16 + (i % 3) * (card_w + gap), top + (i // 3) * (card_h + gap), card_w, card_h) for i in range(len(self.levels))]
        self.preview = ""
        self._new_preview()

    # ------------------------------------------------------------------ what's on each tab
    def _pref(self, key):
        return (lambda: settings.get(self.story, key)), (lambda v: settings.put(self.game, key, v))

    def _story(self, attr):
        return (lambda: getattr(self.story, attr)), (lambda v: setattr(self.story, attr, v))

    def rows(self):
        from src.world import levels
        name = self.tabs[self.tab]
        if name == "MATH":
            return [("Answer timer", [("OFF", "Off"), ("NORMAL", "Normal"), ("LONG", "50% more time")], *self._pref("math_timer"),
                     "How long you get to answer when a question is timed.")]
        if name == "GAMEPLAY":
            caps = [(k, v[0].title()) for k, v in levels.LEVEL_CAP_TEXT.items()]
            return [("Battle style", [("TRADITIONAL", "Classic"), ("OVERWORLD", "Overworld")], *self._story("battle_style"), "Battles on their own screen, or right on the map."),
                    ("Game speed", [(1, "1x"), (2, "2x")], *self._story("game_speed"), "Everything moves twice as fast at 2x."),
                    ("Level cap", caps, *self._story("level_cap_mode"), levels.LEVEL_CAP_TEXT[levels.cap_mode(self.story)][1]),
                    ("Exp Share", [(True, "On"), (False, "Off")], *self._story("exp_share"), "The whole party earns XP from a win."),
                    ("Autosave", [(True, "On"), (False, "Off")], *self._story("autosave"), "Save every time you travel to a new area.")]
        if name == "TEXT & BATTLE":
            return [("Text speed", [(2, "Slow"), (3, "Normal"), (6, "Fast")], *self._pref("text_speed"), "How fast words appear in text boxes."),
                    ("Auto-forward text", [(0, "Off"), (1, "Quick"), (2, "Normal"), (3, "Slow")], *self._pref("auto_text"), "In battles, a line that's fully shown moves on by itself."),
                    ("Move animations", [(True, "On"), (False, "Off")], *self._pref("move_anims"), "Each move's full animation in battle."),
                    ("Battle intros", [(True, "On"), (False, "Off")], *self._pref("battle_intros"), "The transition into a battle."),
                    ("Screen fade", [(True, "On"), (False, "Off")], *self._pref("screen_fade"), "The quick fade between screens.")]
        vols = [(n, str(n)) for n in range(11)]
        return [("Music volume", vols, *self._pref("music"), "0 is silent, 5 is the usual level."),
                ("Sound effects", vols, *self._pref("sfx"), "Cries and button sounds. New sounds use this right away.")]

    def _top(self):
        H = theme.HEADER_H
        if self.tabs[self.tab] == "MATH":
            return self.level_rects[-1].bottom + 12
        return H + 76

    def _row_rect(self, i):
        return pygame.Rect(16, self._top() + i * (ROW_H + ROW_GAP), self.game.width - 32, ROW_H)

    def _arrows(self, r):
        size = r.h - 20
        return pygame.Rect(r.right - 450, r.y + 10, size, size), pygame.Rect(r.right - 10 - size, r.y + 10, size, size)

    # ------------------------------------------------------------------ doing things
    def close(self):
        self.on_close()

    def _new_preview(self):
        level = self.story.get_math_level()
        for _ in range(20):
            self.preview = self.game.math.generate(level, 3)[0]
            if self.preview.endswith("= ?"):
                break

    def _step(self, row, by):
        _name, values, get, put, _desc = row
        keys = [v for v, _l in values]
        now = get()
        i = keys.index(now) if now in keys else 0
        put(keys[(i + by) % len(keys)])

    def _pick_level(self, i):
        self.story.math_difficulty = self.levels[i]["key"]
        self._new_preview()

    def _tap(self, pos):
        for i, r in enumerate(self.tab_rects):
            if r.collidepoint(pos):
                self.tab, self.row = i, 0
                return
        if self.tabs[self.tab] == "MATH":
            for i, r in enumerate(self.level_rects):
                if r.collidepoint(pos):
                    return self._pick_level(i)
        for i, row in enumerate(self.rows()):
            r = self._row_rect(i)
            if r.collidepoint(pos):
                self.row = i
                left, right = self._arrows(r)
                if left.collidepoint(pos):
                    self._step(row, -1)
                elif right.collidepoint(pos) or pos[0] > left.right:
                    self._step(row, 1)

    def handle_events(self, events):
        for e in events:
            if self.btn_back.handle_event(e):
                return
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self._tap(e.pos)
            elif e.type == pygame.KEYDOWN:
                rows = self.rows()
                if e.key == pygame.K_ESCAPE:
                    return self.close()
                if e.key == pygame.K_TAB:
                    self.tab, self.row = (self.tab + 1) % len(self.tabs), 0
                elif e.key == pygame.K_UP:
                    self.row = (self.row - 1) % len(rows)
                elif e.key == pygame.K_DOWN:
                    self.row = (self.row + 1) % len(rows)
                elif e.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    self._step(rows[min(self.row, len(rows) - 1)], -1 if e.key == pygame.K_LEFT else 1)

    def update(self):
        pass

    # ------------------------------------------------------------------ drawing
    def _fit(self, text, width, keys=("label", "caption", "tiny")):
        return next((self.f[k] for k in keys if self.f[k].size(text)[0] <= width), self.f[keys[-1]])

    def draw(self):
        screen, f = self.game.screen, self.f
        accent = theme.ACCENT["options"]
        theme.menu_background(screen, accent, "OPTIONS", f["button"], title_x=176)
        self.btn_back.draw(screen)
        for i, (r, t) in enumerate(zip(self.tab_rects, self.tabs)):
            theme.command_button(screen, r, t, self._fit(t, r.w - 16), accent if i == self.tab else theme.TAB_OFF)
        if self.tabs[self.tab] == "MATH":
            self._draw_levels(screen, accent)
        rows = self.rows()
        for i, (name, values, get, _put, _desc) in enumerate(rows):
            r = self._row_rect(i)
            theme.card(screen, r, selected=i == self.row, accent=accent)
            theme.shadow_text(screen, name, f["label"], r.x + 24, r.centery - 12)
            left, right = self._arrows(r)
            now = get()
            label = next((l for v, l in values if v == now), str(now))
            for rect, mark in ((left, "<"), (right, ">")):
                theme.command_button(screen, rect, mark, f["label"], accent)
            mid = (left.right + right.left) // 2
            theme.shadow_text(screen, label, self._fit(label, right.left - left.right - 16), mid, r.centery, align="center")
        theme.draw_textbox(screen, self.bar)
        if self.tabs[self.tab] == "MATH":
            text = f"Example:  {self.preview}"
            theme.math_text(screen, text, f["label"], self.bar.centerx, self.bar.centery)
        elif rows:
            desc = rows[min(self.row, len(rows) - 1)][4]
            theme.shadow_text(screen, desc, self._fit(desc, self.bar.w - 48), self.bar.x + 24, self.bar.centery - 12)

    def _level_note(self, entry):
        if entry["key"] != "AUTO":
            return entry["desc"]
        story, math = self.story, self.game.math
        region = story.get_current_region()
        return f"Grows with you (now {math.level_by_id[math.auto_level(region, len(story.badges.get(region, [])))]['name'].title()})"

    def _draw_levels(self, screen, accent):
        f = self.f
        for entry, r in zip(self.levels, self.level_rects):
            picked = entry["key"] == self.story.math_difficulty
            theme.card(screen, r, selected=picked, accent=accent)
            name = entry["name"] if entry["key"] == "AUTO" else f"{entry['key']}. {entry['name']}"
            theme.shadow_text(screen, name, self._fit(name, r.w - 50), r.x + 14, r.y + 8, color=theme.shade(accent, 0.8) if picked else theme.TEXT)
            note = self._level_note(entry)
            theme.shadow_text(screen, note, self._fit(note, r.w - 28, ("caption", "tiny")), r.x + 14, r.bottom - 30, color=(96, 102, 122))
