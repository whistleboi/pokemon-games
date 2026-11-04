"""A Pokemon's Summary (info, stats, moves, ribbons)."""

import pygame
from src.states.base import GameState
from src.ui.panels import CommandButton
from src.ui import theme
from src.utils import Utils
from src.config import WHITE, GOLD, LIGHT_GRAY
from src.pokemon.data import Pokemon
from src.pokemon.contest import feebas_ready, CATEGORIES, CATEGORY_COLOR, MAX_CONDITION, FEEBAS_BEAUTY
from src.states.battle import TrainerBattleState
from src.ui.mon_tags import _draw_gmax_tag, _draw_shiny_tag, fit_sprite


# [REF-0022: Pokemon Detail View]
PURPLE_BTN = (120, 70, 170)


class PokemonDetailState(GameState):
    STAT_ROWS = (("HP", "HP"), ("ATTACK", "Attack"), ("DEFENSE", "Defense"),
                 ("SPATK", "Sp. Atk"), ("SPDEF", "Sp. Def"), ("SPEED", "Speed"))
    STATUS_TEXT = {"burn": "BURNED", "paralysis": "PARALYZED", "poison": "POISONED",
                   "toxic": "BADLY POISONED", "sleep": "ASLEEP", "freeze": "FROZEN"}

    def __init__(self, game, pokemon, previous_state, roster=None, dex=False):
        super().__init__(game)
        # Opened from the Pokedex: a species page, not a Pokemon of yours, so no level, HP or STATS
        # tab (Jordan, 11-02); its forms still cycle.
        self.dex = dex
        self.pokemon = pokemon
        self.own = pokemon  # the Pokemon this summary was opened for
        self.previous_state = previous_state
        # The Pokemon either side (the party, or the Box / search on show): LEFT / RIGHT or the
        # header's arrows page through their summaries (Jordan, 11-02).
        roster = [m for m in (roster or []) if m is not None]
        self.roster = roster if any(m is pokemon for m in roster) else [pokemon]
        self.tab = "INFO"
        # Every form of this species the player has obtained (regional, Pinkan, Valencia, Shadow...).
        self.forms = self._obtained_forms(pokemon)
        self.form_idx = 0
        f = game.assets.fonts
        H = theme.HEADER_H
        # The menu frame: the portrait card at the left, the tab's cards at the right, the text box
        # along the bottom; BACK and the INFO / STATS / MOVES tabs in the header.
        self.bar_rect = pygame.Rect(16, game.height - 86, game.width - 32, 78)
        self.portrait = pygame.Rect(24, H + 16, 360, self.bar_rect.top - 12 - H - 16)
        self.content = pygame.Rect(self.portrait.right + 16, self.portrait.y,
                                   game.width - 24 - self.portrait.right - 16, self.portrait.h)
        fy = self.portrait.y + 300
        self.btn_form_prev = CommandButton((self.portrait.x + 16, fy, 60, 48), "<", f["button"],
                                           lambda: self.cycle_form(-1), bg_color=theme.MEGA, autosize=False)
        self.btn_form_next = CommandButton((self.portrait.right - 76, fy, 60, 48), ">", f["button"],
                                           lambda: self.cycle_form(1), bg_color=theme.MEGA, autosize=False)
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.go_back, bg_color=theme.BACK,
                                      autosize=False)
        self.btn_mon_prev = CommandButton((396, 14, 60, 56), "<", f["button"], lambda: self.show_mon(-1),
                                          bg_color=theme.RUN, autosize=False)
        self.btn_mon_next = CommandButton((566, 14, 60, 56), ">", f["button"], lambda: self.show_mon(1),
                                          bg_color=theme.RUN, autosize=False)
        tab_w, gap = 150, 10
        tabs = [("INFO", "INFO")] + ([] if dex else [("STATS", "STATS")]) + [("MOVES", "MOVES")]
        if getattr(pokemon, "is_egg", False):  # an Egg: just its page (how close it is to hatching)
            tabs = [("INFO", "INFO")]
        self.tab_order = tuple(key for key, _ in tabs)
        x0 = game.width - 24 - len(tabs) * tab_w - (len(tabs) - 1) * gap
        self.tab_buttons = {
            key: CommandButton((x0 + i * (tab_w + gap), 14, tab_w, 56), label, f["label"],
                               (lambda k=key: self.show_tab(k)), bg_color=theme.TAB_OFF, autosize=False)
            for i, (key, label) in enumerate(tabs)}
        # MOVES tab (Legends: Z-A style): pick the four moves it uses from its move pool.
        self.sel_slot = None
        self.pool_page = 0
        self.move_msg = "Tap one of its moves, then a move from the pool to swap it in."
        self.slot_rects, self.pool_rects = [], []
        self.page_prev = self.page_next = None
        # STATS tab: the bars judge each stat (as the games show it), or show its IVs (the games'
        # judge view); a tap on the card's button switches.
        self.stat_view = "STATS"
        self.view_rect = None
        self._color_tabs()

    def show_tab(self, tab):
        self.tab = tab
        self._color_tabs()

    def _roster_index(self):
        return next((i for i, m in enumerate(self.roster) if m is self.own), 0)

    def show_mon(self, step):
        """The next (or previous) Pokemon's summary, on the same tab."""
        if len(self.roster) < 2:
            return
        mon = self.roster[(self._roster_index() + step) % len(self.roster)]
        self.pokemon = self.own = mon
        self.forms = self._obtained_forms(mon)
        self.form_idx = 0
        self.sel_slot = None
        self.pool_page = 0
        self.move_msg = "Tap one of its moves, then a move from the pool to swap it in."
        self.start()

    def _obtained_forms(self, pokemon):
        """[pokemon] + a display Pokemon for each other obtained form of its species (Pokedex data)."""
        form_map = self.game.loader.area_data.get("FORM_MAP", {})

        def species(pid):
            pid = int(pid)
            return int((form_map.get(str(pid)) or {}).get("id", pid)) if pid >= 2000 else pid

        base = species(pokemon.id)
        seen = {pokemon.form}  # one page per form (an evolved Crystal Onix and a caught one are the same form)
        out = [pokemon]
        entries = sorted((v for v in self.game.data.data.get("pokedex", {}).values()
                          if isinstance(v, dict) and "id" in v), key=lambda v: (int(v["id"]) >= 2000, int(v["id"])))
        for v in entries:
            pid, form = int(v["id"]), v.get("form", "normal")
            if pid == 201 and form == "a":
                form = "normal"  # (older saves) the A is Unown's plain form
            if species(pid) != base or form in seen or form == "gmax" or str(form).startswith("mega"):
                continue
            seen.add(form)
            try:
                mon = Pokemon(self.game.loader.fetch_specific(pid, form=form), self.game.assets, size_mult=2.5)
            except Exception:
                continue
            mon.level = pokemon.level
            out.append(mon)
        return out

    def cycle_form(self, step):
        if len(self.forms) > 1:
            self.form_idx = (self.form_idx + step) % len(self.forms)
            self.pokemon = self.forms[self.form_idx]

    def _color_tabs(self):
        for name, btn in self.tab_buttons.items():
            btn.bg_color = theme.BAG if name == self.tab else theme.TAB_OFF

    def go_back(self):
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.elements.clear()
        self.game.ui_manager.add_element(self.btn_back)
        for btn in self.tab_buttons.values():
            self.game.ui_manager.add_element(btn)
        if len(self.forms) > 1:
            self.game.ui_manager.add_element(self.btn_form_prev)
            self.game.ui_manager.add_element(self.btn_form_next)
        if len(self.roster) > 1:
            self.game.ui_manager.add_element(self.btn_mon_prev)
            self.game.ui_manager.add_element(self.btn_mon_next)

    TAB_ORDER = ("INFO", "STATS", "MOVES")

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_RIGHT) and len(self.roster) > 1:
                self.show_mon(-1 if event.key == pygame.K_LEFT else 1)  # the Pokemon either side
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB):
                step = -1 if event.key == pygame.K_LEFT or (event.mod & pygame.KMOD_SHIFT) else 1
                i = self.tab_order.index(self.tab) if self.tab in self.tab_order else 0
                self.show_tab(self.tab_order[(i + step) % len(self.tab_order)])
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_UP, pygame.K_DOWN):
                self.cycle_form(-1 if event.key == pygame.K_UP else 1)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.tab == "MOVES":
                self.click_moves(event.pos)
            elif (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.tab == "STATS"
                  and self.view_rect and self.view_rect.collidepoint(event.pos)):
                self.toggle_stat_view()

    def toggle_stat_view(self):
        self.stat_view = "IVS" if self.stat_view == "STATS" else "STATS"

    def stat_rating(self, key, value):
        """How strong a stat is for the Pokemon's level, 0-1: against about what a strong stat of
        that kind is at that level (HP runs higher)."""
        lv = max(1, self.pokemon.level)
        strong = (2.2 * lv + 110) if key == "HP" else (2 * lv + 100)
        return max(0.0, min(1.0, value / strong))

    # --- MOVES tab: the move pool ---
    POOL_PER_PAGE = 5

    def _pool_choices(self):
        from src.pokemon import moves as movelib
        p = self.own
        movelib.ensure_moves(self.game, p)
        return [m for m in movelib.move_pool(self.game, p) if m not in p.moves]

    def click_moves(self, pos):
        from src.pokemon import moves as movelib
        p = self.own
        for i, r in enumerate(self.slot_rects):
            if r.collidepoint(pos):
                self.sel_slot = None if self.sel_slot == i else i
                self.move_msg = ("Now tap a move from the pool to put in this slot." if self.sel_slot is not None
                                 else "Tap one of its moves, then a move from the pool to swap it in.")
                return
        if self.page_prev and self.page_prev.collidepoint(pos):
            self.pool_page = max(0, self.pool_page - 1)
            return
        if self.page_next and self.page_next.collidepoint(pos):
            self.pool_page += 1
            return
        for r, name in self.pool_rects:
            if not r.collidepoint(pos):
                continue
            label = name.replace("-", " ").title()
            if self.sel_slot is None and len(p.moves) >= movelib.MAX_MOVES:
                self.move_msg = f"Tap one of its four moves first, then {label}."
                return
            old = p.moves[self.sel_slot] if self.sel_slot is not None and self.sel_slot < len(p.moves) else None
            if movelib.set_move(p, self.sel_slot, name):
                who = p.display_name.upper()
                self.move_msg = (f"{who} will use {label} instead of {old.replace('-', ' ').title()}."
                                 if old else f"{who} will use {label}.")
                self.sel_slot = None
            return

    def update(self):
        pass

    def _accent(self):
        """The header takes the Pokemon's own (first) type colour."""
        from src.states.battle import TrainerBattleState
        types = self.pokemon.types or []
        return theme.shade(TrainerBattleState.TYPE_COLORS.get(types[0], theme.ACCENT["summary"]), 0.9) \
            if types else theme.ACCENT["summary"]

    def _type_chips(self, x, y):
        from src.states.battle import TrainerBattleState
        f = self.game.assets.fonts
        for t in self.pokemon.types or []:
            color = TrainerBattleState.TYPE_COLORS.get(t, (120, 120, 120))
            chip = pygame.Rect(x, y, f["caption"].size(t.upper())[0] + 22, 28)
            pygame.draw.rect(screen := self.game.screen, color, chip, border_radius=14)
            pygame.draw.rect(screen, theme.shade(color, 0.6), chip, 2, border_radius=14)
            Utils.draw_text_outline(screen, t.upper(), f["caption"], WHITE, chip.centerx, chip.centery,
                                    outline_color=theme.shade(color, 0.5), thickness=2)
            x = chip.right + 8

    def _bar_line(self):
        """What the text box says for the tab on show."""
        p = self.pokemon
        if getattr(p, "is_egg", False):
            from src.pokemon import breeding
            return breeding.hatch_hint(p)
        if self.tab == "MOVES":
            own = self.own
            if self.sel_slot is not None and self.sel_slot < len(own.moves):
                from src.pokemon import moves as movelib
                name = own.moves[self.sel_slot]
                effect = movelib.info(self.game, name).get("effect") or ""
                if effect:
                    return f"{name.replace('-', ' ').title()}: {effect}"
            return self.move_msg
        if self.tab == "STATS":
            what = ("the bars show how strong each stat is for its level" if self.stat_view == "STATS"
                    else "the bars show its IVs (0-31), what it was born with")
            return (f"XP {p.xp}/{p.xp_to_next} to Lv {p.level + 1}" if p.xp_to_next else "MAX LEVEL") + \
                f"   -   {what}"
        from src.pokemon import evolution
        options = evolution.evolution_options(self.game, p)
        if options:
            entry, _, rule = options[0]
            name = entry.split("_")[0].replace("-", " ").title()
            more = f" (or {len(options) - 1} more)" if len(options) > 1 else ""
            return f"Evolves into {name}{more}: {evolution.condition_hint(rule)}"
        return "It doesn't evolve any further."

    def draw(self):
        from src.ui.dialogue import wrap_text
        screen, f = self.game.screen, self.game.assets.fonts
        accent = self._accent()
        theme.menu_background(screen, accent, "SUMMARY", f["button"], title_x=176)

        # The portrait card: hearts, the Pokemon, its name, level and types, the form arrows.
        p = self.pokemon
        r = self.portrait
        theme.card(screen, r)
        from src.ui.hearts import draw_hearts
        if not self.dex:  # (a Pokedex page is the species, not one of yours)
            draw_hearts(screen, p, r.centerx, r.y + 24, size=18)
        if p.image:
            spr = fit_sprite(p.image, r.w - 60, 230)
            screen.blit(spr, spr.get_rect(center=(r.centerx, r.y + 160)))
        if getattr(p, "gmax_factor", False):
            _draw_gmax_tag(screen, f["small"], r.right - 90, r.y + 40)
        if getattr(p, "is_shiny", False) and not getattr(p, "is_egg", False):
            _draw_shiny_tag(screen, f["small"], r.x + 14, r.y + 40)
        if len(self.roster) > 1:  # which of the party / Box this is
            mid = (self.btn_mon_prev.rect.right + self.btn_mon_next.rect.left) // 2
            Utils.draw_text_outline(screen, f"{self._roster_index() + 1}/{len(self.roster)}", f["label"], WHITE,
                                    mid, self.btn_mon_prev.rect.centery, outline_color=theme.shade(accent, 0.45),
                                    thickness=3)
        if len(self.forms) > 1:
            theme.shadow_text(screen, f"Form {self.form_idx + 1}/{len(self.forms)}", f["label"], r.centerx,
                              self.btn_form_prev.rect.centery, align="center")
        y = r.y + 364
        name = p.display_name.upper()
        nr = theme.shadow_text(screen, name, f["s_med"] if f["s_med"].size(name)[0] <= r.w - 40 else f["label"],
                               r.x + 20, y)
        egg = getattr(p, "is_egg", False)
        if not egg and not self.dex:
            from src.pokemon import breeding
            theme.draw_gender(screen, breeding.gender_of(self.game, p), nr.right + 10, y + 4, 22)
        if not egg:
            self._type_chips(r.x + 20, y + 40)
        if self.dex or egg:
            pass  # (a species page: no level or HP)
        elif (lv := theme.shadow_text(screen, f"Lv{p.level}", f["label"], r.right - 20, y + 42, align="right")) \
                and self.pokemon is self.own:
            theme.status_tag(screen, "faint" if p.current_hp <= 0 else getattr(p, "status", None), f["caption"],
                             lv.x - 66, y + 41)
            theme.hp_bar(screen, r.x + 20, r.bottom - 40, r.w - 40, p.current_hp, p.get_max_hp())
            theme.shadow_text(screen, f"HP {int(p.current_hp)}/{p.get_max_hp()}", f["caption"], r.right - 20,
                              r.bottom - 26, align="right")

        if self.tab == "STATS":
            self._draw_stats_and_moves()
        elif self.tab == "MOVES":
            self._draw_move_pool()
        else:
            self._draw_info()

        theme.draw_textbox(screen, self.bar_rect)
        rows = wrap_text(self._bar_line(), f["label"], self.bar_rect.w - 64)[:2]
        lh = f["label"].get_linesize() + 4
        top = self.bar_rect.centery - lh * len(rows) // 2 - 1
        for k, row in enumerate(rows):
            theme.shadow_text(screen, row, f["label"], self.bar_rect.x + 32, top + k * lh)
        self.game.ui_manager.draw(screen)

    def _rows(self, rect, rows, label_w=150):
        """Label / value rows on a card."""
        f = self.game.assets.fonts
        y = rect.y + 18
        for label, value in rows:
            theme.shadow_text(screen := self.game.screen, label, f["label"], rect.x + 20, y, color=(110, 116, 136))
            theme.shadow_text(screen, str(value), f["label"], rect.x + 20 + label_w, y)
            y += 38
        return y

    def _draw_info(self):
        """INFO: who it is (left card), its contest condition (right card)."""
        p, c = self.pokemon, self.content
        left = pygame.Rect(c.x, c.y, c.w // 2 - 8, c.h)
        right = pygame.Rect(left.right + 16, c.y, c.right - left.right - 16, c.h)
        theme.card(self.game.screen, left)
        if getattr(p, "is_egg", False):  # an Egg: the hint about hatching
            from src.pokemon import breeding
            from src.ui.dialogue import wrap_text
            y = self._rows(left, [("Name", "Egg"), ("Found in", str(getattr(p, "caught_region", "") or "?").title())])
            for k, row in enumerate(wrap_text(breeding.hatch_hint(p), self.game.assets.fonts["label"], left.w - 40)):
                theme.shadow_text(self.game.screen, row, self.game.assets.fonts["label"], left.x + 20, y + 10 + k * 34)
            return
        if p is self.own and not self.dex:
            rows = [("Name", p.display_name), ("Level", p.level),
                    ("XP", f"{p.xp}/{p.xp_to_next}" if p.xp_to_next else "MAX"),
                    ("HP", f"{int(p.current_hp)}/{p.get_max_hp()}"), ("Types", "/".join(t.title() for t in p.types)),
                    ("Status", self.STATUS_TEXT.get(getattr(p, "status", None) or "", "Healthy").title())]
            region = getattr(p, "caught_region", None)
            if region:
                rows.append(("Met in", str(region).title()))
            if self.game.story_manager.inventory.get("TERA_ORB"):
                from src.pokemon import zpower
                rows.append(("Tera Type", zpower.tera_type(p).title()))
        else:  # another form of this species from the Pokedex
            rows = [("Name", p.display_name), ("Form", str(p.form).title()),
                    ("Types", "/".join(t.title() for t in p.types))]
        if getattr(p, "gmax_factor", False):
            rows.append(("G-Max", "Yes"))
        if getattr(p, "everstone", False):
            rows.append(("Holding", "Everstone"))
        if getattr(p, "held_item", None):
            from src.world import hms
            rows.append(("Holding", hms.item_name(p.held_item)))
        from src.world import seasons
        season_form = seasons.form_name(p.id)
        if season_form:
            rows.append(("Coat", season_form))
        y = self._rows(left, rows)
        if not self.dex:
            self._draw_ability(left, y + 6)
            self._draw_condition(right)
        else:
            self._draw_species_abilities(right)

    def _draw_ability(self, rect, y):
        """Its ability (Jordan, 11-03): the name, (Hidden) for a hidden one, and what it does."""
        from src.pokemon import abilities as ablib
        from src.ui.dialogue import wrap_text
        f, p = self.game.assets.fonts, self.pokemon
        key = ablib.ability(self.game, p)
        name = ablib.name(self.game, key) + ("  (Hidden)" if ablib.is_hidden(self.game, p) else "")
        theme.shadow_text(self.game.screen, "Ability", f["label"], rect.x + 20, y, color=(110, 116, 136))
        theme.shadow_text(self.game.screen, name, f["label"], rect.x + 170, y)
        for k, row in enumerate(wrap_text(ablib.desc(self.game, key), f["caption"], rect.w - 40)[:3]):
            theme.shadow_text(self.game.screen, row, f["caption"], rect.x + 20, y + 40 + k * 26, color=(84, 90, 110))

    def _draw_species_abilities(self, rect):
        """A Pokedex page: the species' abilities and hidden ability, with what each does."""
        from src.pokemon import abilities as ablib
        from src.ui.dialogue import wrap_text
        f, screen = self.game.assets.fonts, self.game.screen
        theme.card(screen, rect)
        normal, hidden = ablib.choices(self.game, self.pokemon.id)
        theme.shadow_text(screen, "ABILITIES", f["label"], rect.x + 20, rect.y + 18, color=(110, 116, 136))
        y = rect.y + 58
        for key, tag in [(k, "") for k in normal] + ([(hidden, "  (Hidden)")] if hidden else []):
            theme.shadow_text(screen, ablib.name(self.game, key) + tag, f["label"], rect.x + 20, y)
            rows = wrap_text(ablib.desc(self.game, key), f["caption"], rect.w - 40)[:3]
            for k, row in enumerate(rows):
                theme.shadow_text(screen, row, f["caption"], rect.x + 20, y + 34 + k * 24, color=(84, 90, 110))
            y += 44 + len(rows) * 24

    def _draw_stats_and_moves(self):
        """STATS: the stats with IV bars (left card), the four moves (right)."""
        from src.pokemon import moves as movelib
        screen, p, f = self.game.screen, self.pokemon, self.game.assets.fonts
        c = self.content
        left = pygame.Rect(c.x, c.y, c.w // 2 - 8, c.h)
        right = pygame.Rect(left.right + 16, c.y, c.right - left.right - 16, c.h)
        theme.card(screen, left)
        x, y = left.x + 20, left.y + 18
        ivs = self.stat_view == "IVS"
        theme.shadow_text(screen, "IVs" if ivs else "STATS", f["label"], x, y, color=(110, 116, 136))
        self.view_rect = pygame.Rect(left.right - 16 - 186, left.y + 10, 186, 40)
        theme.command_button(screen, self.view_rect, "SHOW STATS" if ivs else "SHOW IVs", f["caption"],
                             theme.MEGA, hover=self.view_rect.collidepoint(pygame.mouse.get_pos()))
        y += 56
        for key, label in self.STAT_ROWS:
            value = p.get_max_hp() if key == "HP" else p.stat_value(key)
            theme.shadow_text(screen, label, f["label"], x, y)
            theme.shadow_text(screen, str(value), f["label"], x + 200, y, align="right")
            bar = pygame.Rect(x + 214, y + 4, left.right - 20 - (40 if ivs else 0) - x - 214, 14)
            pygame.draw.rect(screen, (210, 214, 224), bar, border_radius=7)
            share = p.iv(key) / 31 if ivs else self.stat_rating(key, value)
            fill = bar.copy()
            fill.width = max(4, int(bar.width * share))
            pygame.draw.rect(screen, theme.HP_GREEN if share >= 0.6 else theme.HP_YELLOW if share >= 0.35
                             else (220, 130, 96), fill, border_radius=7)
            if ivs:
                theme.shadow_text(screen, str(p.iv(key)), f["label"], left.right - 20, y, align="right")
            y += 50

        known = movelib.ensure_moves(self.game, p)[:4]
        h = (right.h - 3 * 12) // 4
        for i in range(4):
            r = pygame.Rect(right.x, right.y + i * (h + 12), right.w, h)
            if i < len(known):
                self._move_card(r, known[i])
            else:
                pygame.draw.rect(screen, theme.shade(theme.MENU_BG, 1.3), r, border_radius=12)

    def _move_card(self, rect, name, highlight=False):
        """A move in its type's colour (like the battle's move buttons): name, then type, category,
        power and accuracy."""
        from src.pokemon import moves as movelib
        from src.states.battle import TrainerBattleState
        screen, fonts = self.game.screen, self.game.assets.fonts
        d = movelib.info(self.game, name)
        color = TrainerBattleState.TYPE_COLORS.get(d.get("type"), (120, 120, 120))
        dark = theme.shade(color, 0.6)
        pygame.draw.rect(screen, dark, rect.move(0, 4), border_radius=12)
        pygame.draw.rect(screen, color, rect, border_radius=12)
        pygame.draw.rect(screen, GOLD if highlight else (20, 20, 30), rect, 5 if highlight else 3, border_radius=12)
        Utils.draw_text_outline(screen, name.replace("-", " ").upper(), fonts["label"], WHITE,
                                rect.x + 14, rect.y + 8, align="left", outline_color=dark, thickness=2)
        acc = f"{d['accuracy']}%" if d.get("accuracy") else "-"
        detail = (f"{str(d.get('type', '')).title()}  {str(d.get('category', '')).title()}  "
                  f"Pow {d.get('power') or '-'}  {acc}")
        Utils.draw_text_outline(screen, detail, fonts["caption"], WHITE, rect.x + 14, rect.bottom - 26, align="left",
                                outline_color=dark, thickness=2)

    def _draw_move_pool(self):
        """MOVES: its four moves (left), the rest of its move pool (right); tap a move, then a
        pool move to swap it in."""
        from src.pokemon import moves as movelib
        screen, fonts = self.game.screen, self.game.assets.fonts
        p = self.own
        movelib.ensure_moves(self.game, p)
        c = self.content
        half = c.w // 2 - 8
        left_x, right_x = c.x, c.x + half + 16
        top = c.y + 40
        Utils.draw_text_outline(screen, "ITS MOVES", fonts["label"], WHITE, left_x + 4, c.y + 10, align="left")
        self.slot_rects = []
        h = (c.bottom - top - 3 * 10) // 4
        for i in range(movelib.MAX_MOVES):
            r = pygame.Rect(left_x, top + i * (h + 10), half, h)
            self.slot_rects.append(r)
            if i < len(p.moves):
                self._move_card(r, p.moves[i], highlight=(self.sel_slot == i))
            else:
                pygame.draw.rect(screen, theme.shade(theme.MENU_BG, 1.3), r, border_radius=12)
                pygame.draw.rect(screen, GOLD if self.sel_slot == i else theme.PANEL_EDGE, r, 3, border_radius=12)
                Utils.draw_text_outline(screen, "- empty -", fonts["label"], LIGHT_GRAY, r.centerx, r.centery)
        choices = self._pool_choices()
        pages = max(1, -(-len(choices) // self.POOL_PER_PAGE))
        self.pool_page = min(self.pool_page, pages - 1)
        Utils.draw_text_outline(screen, f"MOVE POOL ({len(choices)})", fonts["label"], WHITE, right_x + 4, c.y + 10,
                                align="left")
        self.pool_rects = []
        foot = 52 if pages > 1 else 0
        ph = (c.bottom - top - foot - (self.POOL_PER_PAGE - 1) * 8) // self.POOL_PER_PAGE
        start = self.pool_page * self.POOL_PER_PAGE
        for i, name in enumerate(choices[start:start + self.POOL_PER_PAGE]):
            r = pygame.Rect(right_x, top + i * (ph + 8), half, ph)
            self.pool_rects.append((r, name))
            self._move_card(r, name)
        if not choices:
            Utils.draw_text_outline(screen, "No other moves learned yet.", fonts["label"], LIGHT_GRAY,
                                    right_x + 4, top + 20, align="left")
        self.page_prev = self.page_next = None
        if pages > 1:
            y = c.bottom - 44
            self.page_prev = pygame.Rect(right_x, y, 70, 44)
            self.page_next = pygame.Rect(right_x + half - 70, y, 70, 44)
            mouse = pygame.mouse.get_pos()
            for rr, label in ((self.page_prev, "<"), (self.page_next, ">")):
                theme.command_button(screen, rr, label, fonts["button"], theme.MEGA, hover=rr.collidepoint(mouse))
            Utils.draw_text_outline(screen, f"Page {self.pool_page + 1}/{pages}", fonts["label"], WHITE,
                                    right_x + half // 2, y + 22)

    def _draw_condition(self, rect):
        """Contest condition bars, Sheen and ribbons, on a card."""
        p = self.pokemon
        screen, f = self.game.screen, self.game.assets.fonts
        theme.card(screen, rect)
        cond = getattr(p, "condition", None) or {}
        x, y = rect.x + 20, rect.y + 18
        theme.shadow_text(screen, "CONDITION", f["label"], x, y, color=(110, 116, 136))
        y += 44
        rows = [(cat.title(), cond.get(cat, 0), CATEGORY_COLOR[cat]) for cat in CATEGORIES]
        rows.append(("Sheen", getattr(p, "sheen", 0), (170, 176, 196)))
        bar_x = x + 126
        for label, value, color in rows:
            theme.shadow_text(screen, label, f["label"], x, y)
            bar = pygame.Rect(bar_x, y + 4, rect.right - 20 - bar_x, 14)
            pygame.draw.rect(screen, (210, 214, 224), bar, border_radius=7)
            fill = bar.copy()
            fill.width = int(bar.w * min(value, MAX_CONDITION) / MAX_CONDITION)
            if fill.width:
                pygame.draw.rect(screen, color, fill, border_radius=7)
            y += 40
        ribbons = getattr(p, "ribbons", [])
        theme.shadow_text(screen, f"Ribbons: {len(ribbons)}", f["label"], x, y + 6, color=(170, 120, 20))
        if p.name.upper() == "FEEBAS" and not feebas_ready(p):
            theme.shadow_text(screen, f"Needs Beauty {FEEBAS_BEAUTY} to evolve", f["caption"], x, y + 40)
