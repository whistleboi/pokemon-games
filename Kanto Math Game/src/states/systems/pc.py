"""The PC: boxes, search and filters."""

import pygame
from src.states.base import GameState
from src.ui.panels import CommandButton
from src.ui import theme
from src.utils import Utils
from src.config import WHITE
from src.states.battle import TrainerBattleState
from src.states.systems.summary import PokemonDetailState
from src.ui.mon_tags import draw_shiny_star, fit_sprite


# [REF-0031: PC System]
class PCState(GameState):
    def text_input_rect(self):  # the search box (a phone's keyboard opens on a tap: src/core/android.py)
        return self.search_rect

    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.party = game.story_manager.player_team
        self.pc = game.story_manager.pc_pokemon
        self.selected_party_idx = None
        self.selected_pc_idx = None
        self.scroll_y = 0

        self.box_index = 0
        self.mons_per_box = 30

        self.font = game.assets.fonts["tiny"]
        f = game.assets.fonts
        H = theme.HEADER_H
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.go_back, bg_color=theme.BACK,
                                      autosize=False)
        # The menu frame: the party at the left, the Box (6 x 5, like the games) at the right, the
        # details bar along the bottom.
        self.party_rect = pygame.Rect(16, H + 16, 330, 0)
        self.box_rect = pygame.Rect(self.party_rect.right + 14, H + 16, 0, 0)
        self.box_rect.width = game.width - 16 - self.box_rect.x
        self.bar_rect = pygame.Rect(16, game.height - 86, game.width - 32, 78)
        self.party_rect.height = self.box_rect.height = self.bar_rect.top - 12 - self.party_rect.top
        top = self.box_rect.y + 12
        self.btn_prev_box = CommandButton((self.box_rect.x + 14, top, 64, 50), "<", f["button"], self.prev_box,
                                          bg_color=theme.ACCENT["pc"], autosize=False)
        self.btn_next_box = CommandButton((self.box_rect.x + 330, top, 64, 50), ">", f["button"], self.next_box,
                                          bg_color=theme.ACCENT["pc"], autosize=False)
        self.btn_sort_id = CommandButton((self.box_rect.right - 14 - 330, top, 150, 50), "SORT #", f["label"],
                                         self.sort_by_id, bg_color=theme.TAB_OFF, autosize=False)
        self.btn_sort_name = CommandButton((self.box_rect.right - 14 - 170, top, 170, 50), "SORT A-Z", f["label"],
                                           self.sort_by_name, bg_color=theme.TAB_OFF, autosize=False)
        self.btn_release = CommandButton((self.bar_rect.right - 18 - 180, self.bar_rect.y + 12, 180,
                                          self.bar_rect.h - 28), "RELEASE", f["label"], self.release_pokemon,
                                         bg_color=theme.FIGHT, visible=False, autosize=False)
        self.cols, self.rows = 6, 5  # a Box holds 30, as in the games
        # Tap a Pokemon: a small menu beside it (MOVE, SUMMARY, and RELEASE in the Box). MOVE picks
        # it up; the next tap puts it down (or swaps), as before. Tapping elsewhere closes it.
        self.popup = None  # ("party" | "pc", index)
        self.popup_rect = pygame.Rect(0, 0, 220, 0)
        self.btn_pop_move = CommandButton((0, 0, 196, 50), "MOVE", f["label"], self.popup_move,
                                          bg_color=theme.POKEMON, visible=False, autosize=False)
        self.btn_pop_summary = CommandButton((0, 0, 196, 50), "SUMMARY", f["label"], self.popup_summary,
                                             bg_color=theme.RUN, visible=False, autosize=False)
        self.btn_pop_release = CommandButton((0, 0, 196, 50), "RELEASE", f["label"], self.popup_release,
                                             bg_color=theme.FIGHT, visible=False, autosize=False)
        self.popup_buttons = [self.btn_pop_move, self.btn_pop_summary, self.btn_pop_release]
        # Search and filter (Jordan, 11-02): type a name (or a number, #25), or pick a filter (Shiny,
        # Legendary, a type); the Box then shows every match from all the Boxes, a page at a time.
        self.search = ""
        self.search_active = False
        self.filter = "ALL"
        self.result_page = 0
        self.search_rect = pygame.Rect(452, 16, 330, 52)
        self.btn_filter = CommandButton((self.search_rect.right + 12, 14, 196, 56), "FILTER", f["label"],
                                        self.toggle_filter_menu, bg_color=theme.TAB_OFF, autosize=False)
        self.filter_open = False
        chips = [("ALL", "ALL", theme.BACK), ("SHINY", "SHINY", theme.BAG), ("LEGENDARY", "LEGEND", theme.MEGA)]
        from src.states.battle import TrainerBattleState
        chips += [(t, t, TrainerBattleState.TYPE_COLORS.get(t, theme.TAB_OFF)) for t in self.TYPES]
        cols, cw, ch, gap = 4, 150, 46, 8
        rows = (len(chips) + cols - 1) // cols
        self.filter_rect = pygame.Rect(0, 0, cols * cw + (cols + 1) * gap, 52 + rows * (ch + gap) + gap)
        self.filter_rect.topright = (self.btn_filter.rect.right, self.btn_filter.rect.bottom + 8)
        self.filter_buttons = []
        for k, (key, label, color) in enumerate(chips):
            r, c = divmod(k, cols)
            rect = (self.filter_rect.x + gap + c * (cw + gap), self.filter_rect.y + 52 + r * (ch + gap), cw, ch)
            self.filter_buttons.append(CommandButton(rect, label, f["caption"], (lambda k=key: self.set_filter(k)),
                                                     bg_color=color, visible=False, autosize=False))

    TYPES = ("NORMAL", "FIRE", "WATER", "GRASS", "ELECTRIC", "ICE", "FIGHTING", "POISON", "GROUND", "FLYING",
             "PSYCHIC", "BUG", "ROCK", "GHOST", "DRAGON", "DARK", "STEEL", "FAIRY")

    def toggle_filter_menu(self):
        self.close_popup()
        self.search_active = False
        self.filter_open = not self.filter_open
        for btn in self.filter_buttons:
            btn.set_visibility(self.filter_open)

    def set_filter(self, key):
        self.filter = key
        self.result_page = 0
        self.filter_open = True
        self.toggle_filter_menu()  # (closes it)
        self.btn_filter.text = "FILTER" if key == "ALL" else ("LEGEND" if key == "LEGENDARY" else key)
        self.btn_filter.bg_color = theme.TAB_OFF if key == "ALL" else theme.BAG

    def _base_id(self, p):
        if p.id >= 2000:
            mapping = self.game.loader.area_data.get("FORM_MAP", {}).get(str(p.id))
            if mapping:
                return int(mapping.get("id", p.id))
        return p.id

    def _matches(self, p):
        q = self.search.strip().lower()
        if q:
            if q.lstrip("#").isdigit():
                if self._base_id(p) != int(q.lstrip("#")):
                    return False
            elif q not in p.display_name.lower() and q not in str(p.name).lower():
                return False
        if self.filter == "SHINY":
            return bool(getattr(p, "is_shiny", False))
        if self.filter == "LEGENDARY":
            from src.pokemon.balance import is_legendary
            return is_legendary(self._base_id(p))
        if self.filter in self.TYPES:
            return self.filter in [str(t).upper() for t in (p.types or [])]
        return True

    def filtering(self):
        return bool(self.search.strip()) or self.filter != "ALL"

    def results(self):
        """PC indexes of the matches, in Box order."""
        return [i for i, p in enumerate(self.pc) if p is not None and self._matches(p)]

    def result_pages(self):
        return max(1, (len(self.results()) + self.mons_per_box - 1) // self.mons_per_box)

    def shown_index(self, local):
        """The PC index in Box slot local (0-29) on show: the Box's, or the search's page."""
        if self.filtering():
            found = self.results()
            k = self.result_page * self.mons_per_box + local
            return found[k] if k < len(found) else None
        return self.box_index * self.mons_per_box + local

    def local_of(self, index):
        for local in range(self.mons_per_box):
            if self.shown_index(local) == index:
                return local
        return 0

    def clear_search(self):
        self.search, self.search_active, self.result_page = "", False, 0

    def _popup_mon(self):
        if not self.popup:
            return None
        where, i = self.popup
        group = self.party if where == "party" else self.pc
        return group[i] if i < len(group) else None

    def open_popup(self, where, index):
        """The menu beside the tapped Pokemon, kept on the screen."""
        if where == "pc" and getattr(self.pc[index], "coop_lent", None) is not None:
            from src.coop import roster
            roster.toast(self.game, "A friend is borrowing that one.")
            return
        self.popup = (where, index)
        slot = self.party_slot(index) if where == "party" else self.box_slot(self.local_of(index))
        buttons = self.popup_buttons if where == "pc" else self.popup_buttons[:2]
        pr = self.popup_rect
        pr.h = 44 + len(buttons) * 58 + 4
        pr.x = slot.right + 8 if slot.right + 8 + pr.w <= self.game.width - 8 else slot.left - 8 - pr.w
        pr.y = min(max(theme.HEADER_H + 8, slot.centery - pr.h // 2), self.bar_rect.bottom - pr.h)
        for k, btn in enumerate(self.popup_buttons):
            btn.rect.topleft = (pr.x + 12, pr.y + 44 + k * 58)
            btn.set_visibility(btn in buttons)

    def close_popup(self):
        self.popup = None
        for btn in self.popup_buttons:
            btn.set_visibility(False)

    def popup_move(self):
        where, i = self.popup
        self.close_popup()
        if where == "party":
            self.selected_party_idx = i
        else:
            self.selected_pc_idx = i

    def popup_summary(self):
        where = self.popup[0] if self.popup else None
        mon = self._popup_mon()
        self.close_popup()
        if mon is not None:
            if where == "party":
                roster = list(self.party)
            else:  # the Box (or the search's matches) on show
                shown = (self.shown_index(k) for k in range(self.mons_per_box))
                roster = [self.pc[i] for i in shown if i is not None and i < len(self.pc) and self.pc[i] is not None]
            self.game.change_state(PokemonDetailState(self.game, mon, self, roster=roster))

    def popup_release(self):
        _, i = self.popup
        self.close_popup()
        self.selected_pc_idx = i
        self.release_pokemon()

    def go_back(self):
        if not self.party:
            self.game.show_dialogue(["You must have at least one Pokémon in your party!"])
            return
        self.game.change_state(self.previous_state)

    def prev_box(self):
        if self.filtering():  # the search's pages
            self.result_page = (self.result_page - 1) % self.result_pages()
            return
        self.box_index = (self.box_index - 1) % self.get_total_boxes()
        self.scroll_y = 0

    def next_box(self):
        if self.filtering():
            self.result_page = (self.result_page + 1) % self.result_pages()
            return
        self.box_index = (self.box_index + 1) % self.get_total_boxes()
        self.scroll_y = 0

    def sort_by_id(self):
        start = self.box_index * self.mons_per_box
        end = start + self.mons_per_box
        box_mons = [p for p in self.pc[start:end] if p is not None]

        def get_base_id(p):
            if p.id >= 2000:
                mapping = self.game.loader.area_data.get("FORM_MAP", {}).get(str(p.id))
                if mapping:
                    return mapping.get("id", p.id)
            return p.id

        box_mons.sort(key=get_base_id)
        self.pc[start:end] = box_mons + [None] * (self.mons_per_box - len(box_mons))

    def sort_by_name(self):
        start = self.box_index * self.mons_per_box
        end = start + self.mons_per_box
        box_mons = [p for p in self.pc[start:end] if p is not None]
        box_mons.sort(key=lambda x: x.display_name.upper())
        self.pc[start:end] = box_mons + [None] * (self.mons_per_box - len(box_mons))

    def release_pokemon(self):
        if self.selected_pc_idx is not None:
            p = self.pc[self.selected_pc_idx]
            self.pc[self.selected_pc_idx] = None
            msg = f"Released {p.display_name.upper()} back into the wild!"
            self.selected_pc_idx = None
            self.game.show_dialogue([msg])

    def get_total_boxes(self):
        return max(1, (len(self.pc) + self.mons_per_box - 1) // self.mons_per_box)

    def start(self):
        self.game.ui_manager.add_element(self.btn_back)
        self.game.ui_manager.add_element(self.btn_prev_box)
        self.game.ui_manager.add_element(self.btn_next_box)
        self.game.ui_manager.add_element(self.btn_sort_id)
        self.game.ui_manager.add_element(self.btn_sort_name)
        self.game.ui_manager.add_element(self.btn_release)
        self.game.ui_manager.add_element(self.btn_filter)
        for btn in self.popup_buttons + self.filter_buttons:
            self.game.ui_manager.add_element(btn)

    def party_slot(self, i):
        """Rect of party slot i (0-5)."""
        r = self.party_rect
        h = (r.h - 56 - 5 * 8) // 6
        return pygame.Rect(r.x + 12, r.y + 46 + i * (h + 8), r.w - 24, h)

    def box_slot(self, local_idx):
        """Rect of slot local_idx (0-29) of the Box on show."""
        r = self.box_rect
        gx, gy, gap = r.x + 14, r.y + 76, 10
        w = (r.w - 28 - gap * (self.cols - 1)) // self.cols
        h = (r.bottom - 12 - gy - gap * (self.rows - 1)) // self.rows
        c, row = local_idx % self.cols, local_idx // self.cols
        return pygame.Rect(gx + c * (w + gap), gy + row * (h + gap), w, h)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and self.search_active:  # typing in the search box
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.search_active = False
                elif event.key == pygame.K_ESCAPE:
                    self.clear_search()
                elif event.key == pygame.K_BACKSPACE:
                    self.search, self.result_page = self.search[:-1], 0
                elif event.unicode and event.unicode.isprintable() and len(self.search) < 16:
                    self.search, self.result_page = self.search + event.unicode, 0
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.filter_open:
                self.toggle_filter_menu()  # a tap outside the filter menu closes it
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                was = self.search_active
                self.search_active = self.search_rect.collidepoint(event.pos)
                if self.search_active:
                    self.close_popup()
                    if was and self.search:  # a second tap on the box clears it
                        self.clear_search()
                        self.search_active = True
                    return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):  # the wheel flips Boxes
                self.close_popup()
                self.prev_box() if event.button == 4 else self.next_box()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.popup:
                # (the menu's own buttons take their taps first) anywhere else closes it; another
                # Pokemon gets the menu instead
                old = self.popup
                self.close_popup()
                hit = self._slot_at(event.pos)
                if hit and hit != old and self._mon_at(*hit) is not None:
                    self.open_popup(*hit)
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i in range(6):
                    if self.party_slot(i).collidepoint(event.pos):
                        self.handle_click("party", i)
                        return
                for local in range(self.mons_per_box):
                    if self.box_slot(local).collidepoint(event.pos):
                        if self.shown_index(local) is not None:
                            self.handle_click("pc", self.shown_index(local))
                        return

    def _slot_at(self, pos):
        for i in range(6):
            if self.party_slot(i).collidepoint(pos):
                return ("party", i)
        for local in range(self.mons_per_box):
            if self.box_slot(local).collidepoint(pos):
                i = self.shown_index(local)
                return ("pc", i) if i is not None else None
        return None

    def _mon_at(self, where, i):
        group = self.party if where == "party" else self.pc
        return group[i] if i < len(group) else None

    def _hovered(self):
        """The Pokemon under the pointer (party or Box), else None."""
        mouse = pygame.mouse.get_pos()
        for i, p in enumerate(self.party[:6]):
            if self.party_slot(i).collidepoint(mouse):
                return p
        for local in range(self.mons_per_box):
            i = self.shown_index(local)
            if i is not None and i < len(self.pc) and self.pc[i] is not None and self.box_slot(local).collidepoint(mouse):
                return self.pc[i]
        return None

    def handle_click(self, source, index):
        if source == "pc" and index < len(self.pc) and getattr(self.pc[index], "coop_lent", None) is not None:
            from src.coop import roster
            roster.toast(self.game, "A friend is borrowing that one.")
            return
        if source == "party":
            if index >= len(self.party):
                if self.selected_pc_idx is not None and self.pc[self.selected_pc_idx] is not None:
                    self.party.append(self.pc[self.selected_pc_idx])
                    self.pc[self.selected_pc_idx] = None
                    self.selected_pc_idx = None
                return

            if self.selected_party_idx == index:
                self.selected_party_idx = None
            elif self.selected_party_idx is not None:
                old_idx = self.selected_party_idx
                self.party[index], self.party[old_idx] = self.party[old_idx], self.party[index]
                self.selected_party_idx = None
            elif self.selected_pc_idx is not None:
                pc_mon = self.pc[self.selected_pc_idx]
                self.pc[self.selected_pc_idx] = self.game.story_manager.heal_for_pc(self.party[index])
                self.party[index] = pc_mon
                self.selected_pc_idx = None
            else:
                self.open_popup("party", index)

        elif source == "pc":
            if self.selected_pc_idx == index:
                self.selected_pc_idx = None
            elif self.selected_pc_idx is not None:
                self.pc[index], self.pc[self.selected_pc_idx] = self.pc[self.selected_pc_idx], self.pc[index]
                self.selected_pc_idx = None
            elif self.selected_party_idx is not None:
                if len(self.party) == 1 and self.pc[index] is None:
                    self.game.show_dialogue(["Can't store your last Pokémon!"])
                    return

                old_p_idx = self.selected_party_idx
                party_mon = self.party[old_p_idx]

                self.game.story_manager.heal_for_pc(party_mon)
                if self.pc[index] is None:
                    self.pc[index] = party_mon
                    self.party.pop(old_p_idx)
                else:
                    self.party[old_p_idx] = self.pc[index]
                    self.pc[index] = party_mon

                self.selected_party_idx = None
            elif self.pc[index] is not None:
                self.open_popup("pc", index)

    def update(self):
        self.btn_release.set_visibility(False)  # (RELEASE is in the tap menu now)

    def draw(self):
        """The menu frame (src/ui/theme.py) in the PC's teal: the party, the Box, the details bar."""
        screen = self.game.screen
        f = self.game.assets.fonts
        accent = theme.ACCENT["pc"]
        theme.menu_background(screen, accent, self.game.story_manager.pc_name().upper(), f["button"], title_x=176)
        Utils.draw_text_outline(screen, f"{sum(1 for p in self.pc if p)} stored", f["label"], WHITE,
                                self.game.width - 24, theme.HEADER_H // 2 - 4, align="right",
                                outline_color=theme.shade(accent, 0.45), thickness=3)
        theme.text_field(screen, self.search_rect, self.search, f["label"], "Search name or #",
                         focused=self.search_active)
        mouse = pygame.mouse.get_pos()

        # The party.
        theme.draw_panel(screen, self.party_rect)
        Utils.draw_text_outline(screen, "PARTY", f["button"], WHITE, self.party_rect.centerx, self.party_rect.y + 24)
        for i in range(6):
            rect = self.party_slot(i)
            if i < len(self.party):
                p = self.party[i]
                theme.card(screen, rect, hover=rect.collidepoint(mouse), selected=self.selected_party_idx == i,
                           accent=theme.POKEMON if self.selected_party_idx == i else accent)
                icon = fit_sprite(p.image or p.sidebar_image, rect.h - 8, rect.h - 8) if (p.image or p.sidebar_image) else None
                if icon:
                    screen.blit(icon, icon.get_rect(center=(rect.x + 8 + (rect.h - 8) // 2, rect.centery)))
                tx = rect.x + rect.h + 8
                theme.shadow_text(screen, p.display_name.title(), f["label"], tx, rect.y + 8)
                lv = theme.shadow_text(screen, f"Lv{p.level}", f["caption"], tx, rect.bottom - 26)
                bar = pygame.Rect(lv.right + 10, rect.bottom - 22, rect.right - 12 - lv.right - 10, 8)
                ratio = max(0.0, min(1.0, p.current_hp / max(1, p.get_max_hp())))
                pygame.draw.rect(screen, (88, 88, 96), bar, border_radius=4)
                color = theme.HP_GREEN if ratio > 0.5 else theme.HP_YELLOW if ratio > 0.2 else theme.HP_RED
                if ratio > 0:
                    pygame.draw.rect(screen, color, (bar.x, bar.y, max(3, int(bar.w * ratio)), bar.h), border_radius=4)
            else:
                pygame.draw.rect(screen, theme.shade(theme.PANEL_INNER, 0.8), rect, border_radius=12)
                pygame.draw.rect(screen, theme.PANEL_EDGE, rect, 2, border_radius=12)

        # The Box.
        theme.draw_panel(screen, self.box_rect)
        mid = (self.btn_prev_box.rect.right + self.btn_next_box.rect.left) // 2
        title = (f"FOUND {len(self.results())}  ({self.result_page + 1}/{self.result_pages()})" if self.filtering()
                 else f"BOX {self.box_index + 1} / {self.get_total_boxes()}")
        room = self.btn_next_box.rect.left - self.btn_prev_box.rect.right - 12
        tf = f["button"] if f["button"].size(title)[0] <= room else f["label"]
        Utils.draw_text_outline(screen, title, tf, WHITE, mid, self.btn_prev_box.rect.centery)
        for local in range(self.mons_per_box):
            i = self.shown_index(local)
            rect = self.box_slot(local)
            if i is not None and i < len(self.pc) and self.pc[i] is not None:
                p = self.pc[i]
                theme.card(screen, rect, hover=rect.collidepoint(mouse), selected=self.selected_pc_idx == i,
                           accent=theme.POKEMON if self.selected_pc_idx == i else accent)
                sprite = p.image if p.image else p.sidebar_image
                if sprite:
                    spr = fit_sprite(sprite, rect.w - 20, rect.h - 30)
                    screen.blit(spr, spr.get_rect(center=(rect.centerx, rect.y + 4 + (rect.h - 26) // 2)))
                name = p.display_name.title()
                nf = f["caption"] if f["caption"].size(name)[0] <= rect.w - 8 else f["tiny"]
                theme.shadow_text(screen, name, nf, rect.centerx, rect.bottom - 12, align="center")
                if getattr(p, "is_shiny", False) and not getattr(p, "is_egg", False):
                    draw_shiny_star(screen, rect.right - 14, rect.y + 14, 9)
            else:
                pygame.draw.rect(screen, theme.shade(theme.PANEL_INNER, 0.8), rect, border_radius=10)
                pygame.draw.rect(screen, theme.PANEL_EDGE, rect, 2, border_radius=10)

        # The details bar: the hovered (or picked) Pokemon, else how moving works.
        show = self._hovered()
        if show is None and self.selected_pc_idx is not None and self.selected_pc_idx < len(self.pc):
            show = self.pc[self.selected_pc_idx]
        if show is None and self.selected_party_idx is not None and self.selected_party_idx < len(self.party):
            show = self.party[self.selected_party_idx]
        if show is not None:
            types = "/".join(t.title() for t in (show.types or []))
            line = (f"{show.display_name.upper()}   Lv{show.level}   {types}   "
                    f"HP {int(show.current_hp)}/{show.get_max_hp()}")
        elif self.filtering() and not self.results():
            line = "No Pokémon in the Boxes match. Tap the search box twice to clear it, or pick ALL."
        else:
            line = ("Now tap where it goes (party or Box)." if self.selected_pc_idx is not None
                    or self.selected_party_idx is not None else "Tap a Pokémon to move it or see its summary.")
        bf = f["s_med"]
        theme.draw_textbox(screen, self.bar_rect)
        theme.shadow_text(screen, line, bf, self.bar_rect.x + 32, self.bar_rect.centery - bf.get_height() // 2 - 2)

        self.game.ui_manager.draw(screen)
        mon = self._popup_mon()
        if mon is not None:
            theme.popup_panel(screen, self.popup_rect, mon.display_name.upper(), f["label"])
            for btn in self.popup_buttons:
                btn.draw(screen)
        if self.filter_open:
            theme.popup_panel(screen, self.filter_rect, "SHOW ONLY", f["label"])
            for btn in self.filter_buttons:
                btn.draw(screen)
