"""The Pokedex: regional dexes, the National Dex, and its pages."""

import pygame
from src.states.base import GameState
from src.ui.panels import CommandButton
from src.ui import theme
from src.utils import Utils
from src.config import WHITE, BLUE, GOLD, VOLUME
from src.pokemon.data import Pokemon
from src.pokemon import forms
from src.states.systems.fly_map import MapState
from src.states.systems.summary import PokemonDetailState
from src.ui.mon_tags import _draw_gmax_tag, fit_sprite


def dex_regions(story):
    """Regional Pokedexes the player has: the starting region's, and each region whose starter
    they've received (a new region's dex arrives with its starter, as in the games)."""
    national_dex = story.story_flags.get("unlocked_national_dex", False)
    out = []
    for r, cfg in story.get_region_starts():
        lo, hi = cfg.get("dex_range", [0, -1])
        if hi < lo:
            continue  # travel-only places (Orange Islands, Orre) have no Pokedex of their own
        if (r == story.starting_region or story.story_flags.get(f"received_starter_{r.lower()}")
                or (national_dex and r in ("KANTO", "JOHTO"))):
            out.append(r)
    return out or [story.starting_region]


def has_national_dex(story):
    """The National Dex: Oak's / Elm's gift, or two regional Pokedexes (the Pokedex shows its NATIONAL
    view then too). Sets the flag so story checks agree with the Pokedex (Celio: Jordan, 11-04)."""
    if not story.story_flags.get("unlocked_national_dex") and len(dex_regions(story)) > 1:
        story.story_flags["unlocked_national_dex"] = True
    return bool(story.story_flags.get("unlocked_national_dex"))


def region_dex(cfg):
    """A region's Pokedex in its own order: an explicit dex_list (Kalos uses the X/Y Kalos dex), else
    its generation's range plus dex_extra."""
    if cfg.get("dex_list"):
        return list(cfg["dex_list"])
    lo, hi = cfg.get("dex_range", [1, 151])
    return list(dict.fromkeys(list(range(lo, hi + 1)) + cfg.get("dex_extra", [])))


def _dex_ids(story, caught_data, seen_ids, view=None):
    """Pokedex 'normal' tab ids. view = a region: that region's own dex (its generation's range plus
    the later-gen evolutions obtainable there, dex_extra). view = None/"NATIONAL": every regional
    dex in a row; species caught outside them are appended, and merely-seen ones (a trainer's
    Crobat) too once the National Dex is unlocked."""
    national_dex = story.story_flags.get("unlocked_national_dex", False)
    regions = dex_regions(story)
    if view and view != "NATIONAL":
        return region_dex(story.get_region_start(view))
    id_list = []
    for r in regions:
        id_list += region_dex(story.get_region_start(r))
    listed = set(id_list)
    extra = {v['id'] for v in caught_data.values()} | (set(seen_ids) if national_dex else set())
    id_list += sorted(i for i in extra if isinstance(i, int) and i <= 1025 and i not in listed)
    return list(dict.fromkeys(id_list))


# [REF-0038: Pokedex UI]
# Regional forms go by their species in the Pokedex (number and name).
REGION_FORM_NAMES = ("alolan", "galarian", "hisuian", "paldean", "pinkan", "valencia")


class PokedexState(GameState):
    COLS, ROWS = 6, 3
    PER_PAGE = COLS * ROWS

    def normal_dex_ids(self, caught_data, seen_ids):
        return _dex_ids(self.game.story_manager, caught_data, seen_ids, getattr(self, "dex_view", None))

    def dex_views(self):
        """Regional dexes the player has, then the National Dex once it's unlocked."""
        story = self.game.story_manager
        views = dex_regions(story)
        if story.story_flags.get("unlocked_national_dex") or len(views) > 1:
            views = views + ["NATIONAL"]
        return views

    def cycle_dex_view(self):
        views = self.dex_views()
        self.dex_view = views[(views.index(self.dex_view) + 1) % len(views)] if self.dex_view in views else views[0]
        self.btn_dex_view.text = f"{self.dex_view.title()} Dex"
        self.page = 0
        self.refresh_dex()

    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.current_tab = "normal"
        self.page = 0
        self.show_shinies_only = False
        self.full_dex = []
        self.sort_mode = "NUMBER"

        self.popup_active = False
        self.selected_pkmn_id = None
        self.popup_rect = pygame.Rect(0, 0, 180, 130)

        # Which Pokedex: this region's own (as in the games), another region's, or the National Dex.
        views = self.dex_views()
        here = game.story_manager.get_current_region()
        self.dex_view = here if here in views else views[0]
        f = game.assets.fonts
        H = theme.HEADER_H
        self.btn_dex_view = CommandButton((game.width // 2 - 140, 14, 280, 56), f"{self.dex_view.title()} Dex",
                                          f["button"], self.cycle_dex_view, bg_color=theme.BAG, autosize=False)
        self.refresh_dex()

        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.go_back, bg_color=theme.BACK,
                                      autosize=False)
        # Tapping an entry: its cry, where it lives, its summary (a small panel beside it).
        self.btn_cry = CommandButton((0, 0, 160, 50), "CRY", f["label"], self.play_selected_cry,
                                     bg_color=theme.RUN, visible=False, autosize=False)
        self.btn_area = CommandButton((0, 0, 160, 50), "AREA", f["label"], self.show_selected_area,
                                      bg_color=theme.POKEMON, visible=False, autosize=False)
        self.btn_info = CommandButton((0, 0, 160, 50), "INFO", f["label"], self.show_selected_info,
                                      bg_color=theme.BAG, visible=False, autosize=False)
        self.popup_rect.height = 190

        # The filter row under the header: the tabs at the left, SHINIES and SORT at the right.
        row_y, row_h = H + 14, 50
        self.btn_shiny_toggle = CommandButton((game.width - 24 - 300, row_y, 150, row_h), "SHINIES", f["label"],
                                              self.toggle_shiny_filter, bg_color=theme.TAB_OFF, autosize=False)
        self.btn_sort = CommandButton((game.width - 24 - 140, row_y, 140, row_h), "SORT: #", f["label"],
                                      self.toggle_sort, bg_color=theme.TAB_OFF, autosize=False)
        self.tab_buttons = []
        for k, (label, tab) in enumerate((("NORMAL", "normal"), ("MEGA", "mega"), ("GMAX", "gmax"),
                                          ("ALT", "alt"), ("BOSS", "boss"), ("UNOWN", "unown"))):
            btn = CommandButton((24 + k * 146, row_y, 138, row_h), label, f["label"],
                                (lambda t=tab: self.set_tab(t)), bg_color=theme.TAB_OFF, autosize=False)
            btn.tab = tab
            self.tab_buttons.append(btn)
        (self.btn_tab_normal, self.btn_tab_mega, self.btn_tab_gmax,
         self.btn_tab_alt, self.btn_tab_boss, self.btn_tab_unown) = self.tab_buttons

        # Grid of entries, then the page bar (the battle text box) with its arrows.
        self.grid_rect = pygame.Rect(24, row_y + row_h + 16, game.width - 48, 0)
        self.bar_rect = pygame.Rect(16, game.height - 86, game.width - 32, 78)
        self.grid_rect.height = self.bar_rect.top - 14 - self.grid_rect.top
        self.btn_prev = pygame.Rect(self.bar_rect.x + 18, self.bar_rect.y + 12, 120, self.bar_rect.h - 28)
        self.btn_next = pygame.Rect(self.bar_rect.right - 138, self.bar_rect.y + 12, 120, self.bar_rect.h - 28)
        self.dex_btns = []

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.add_element(self.btn_back)
        self.game.ui_manager.add_element(self.btn_dex_view)
        self.game.ui_manager.add_element(self.btn_shiny_toggle)
        self.game.ui_manager.add_element(self.btn_sort)
        self.game.ui_manager.add_element(self.btn_cry)
        self.game.ui_manager.add_element(self.btn_area)
        self.game.ui_manager.add_element(self.btn_info)
        for btn in self.tab_buttons:
            self.game.ui_manager.add_element(btn)

    def play_selected_cry(self):
        if self.selected_pkmn_id:
            try:
                cry_path = self.game.assets.get_cry(self.selected_pkmn_id)
                pygame.mixer.Sound(cry_path).play().set_volume(VOLUME)
            except Exception:
                pass
        self.hide_popup()

    def show_selected_area(self):
        if not self.selected_pkmn_id:
            return

        locations = []
        prog = self.game.loader.area_data.get("STORY_PROGRESSION", {})
        for area_key, data in prog.items():
            pool_name = data.get("wild_pool_percentages")
            if pool_name:
                pool = self.game.loader.area_data.get(pool_name, {})
                if str(self.selected_pkmn_id) in pool:
                    name = data.get("route_name", area_key.replace("KANTO_", "").replace("_", " ").title())
                    locations.append(name)

        msg = [f"Found in: {', '.join(locations)}" if locations else "Location unknown."]
        self.game.change_state(MapState(self.game, self, initial_message=msg))
        self.hide_popup()

    def hide_popup(self):
        self.popup_active = False
        self.btn_cry.set_visibility(False)
        self.btn_area.set_visibility(False)
        self.btn_info.set_visibility(False)

    def _species(self, pid):
        """A regional form's species number (Alolan Meowth, #2010: 52); others are their own."""
        pid = int(pid)
        if pid >= 2000:
            mapping = self.game.loader.area_data.get("FORM_MAP", {}).get(str(pid))
            if mapping and str(mapping.get("form")) in REGION_FORM_NAMES:
                return int(mapping.get("id", pid))
        return pid

    def _caught_entry(self, pid):
        """Its Pokedex record: that exact entry, or (a National Dex species) any of its forms."""
        dex = [v for v in self.game.data.data.get("pokedex", {}).values() if isinstance(v, dict) and "id" in v]
        return (next((v for v in dex if int(v["id"]) == int(pid)), None)
                or next((v for v in dex if self._species(v["id"]) == int(pid)), None))

    def show_selected_info(self):
        """The summary page for a caught species (cycle its forms there)."""
        entry = self._caught_entry(self.selected_pkmn_id) if self.selected_pkmn_id else None
        self.hide_popup()
        if not entry:
            return
        mon = Pokemon(self.game.loader.fetch_specific(int(self.selected_pkmn_id), form=entry.get("form", "normal")
                                                      if int(entry["id"]) == int(self.selected_pkmn_id) else "normal"),
                      self.game.assets, size_mult=2.5)
        self.game.change_state(PokemonDetailState(self.game, mon, self, dex=True))

    def toggle_sort(self):
        self.sort_mode = "NAME" if self.sort_mode == "NUMBER" else "NUMBER"
        self.btn_sort.text = f"SORT: {'A-Z' if self.sort_mode == 'NAME' else '#'}"
        self.refresh_dex()

    def refresh_dex(self):
        nown_id = self.game.loader.get_special_id("NOWN", 3025)

        if self.current_tab == "boss":
            source_data = self.game.data.data.get("defeated_bosses", {})
            self.full_dex = list(source_data.values())
        elif self.current_tab == "unown":
            self.full_dex = []
            caught_data = self.game.data.data.get("pokedex", {})
            forms = ["normal", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "question", "exclamation"]
            for f in forms:
                key = "201" if f == "normal" else f"201_{f}"
                is_caught = key in caught_data
                name = f"UNOWN-{f.upper()}" if f not in ["normal", "question", "exclamation"] else ("UNOWN-A" if f == "normal" else f"UNOWN-{'?' if f == 'question' else '!'}")
                self.full_dex.append({
                    "id": 201,
                    "status": 2 if is_caught else 0,
                    "shiny": caught_data.get(key, {}).get("shiny", False) if is_caught else False,
                    "form": f,
                    "name": name if is_caught else "???"
                })
            return
        elif self.current_tab == "normal":
            self.full_dex = []
            caught_data = self.game.data.data.get("pokedex", {})
            seen_ids = self.game.data.data.get("seen_pokemon", [])
            starting_region = self.game.story_manager.starting_region
            national_dex = self.game.story_manager.story_flags.get("unlocked_national_dex", False)

            id_list = self.normal_dex_ids(caught_data, seen_ids)
            national = self.dex_view in (None, "NATIONAL")
            if national:  # one entry per species
                id_list = list(dict.fromkeys(self._species(i) for i in id_list))
            records = [v for v in caught_data.values() if isinstance(v, dict) and "id" in v]
            seen_set = set(seen_ids)

            for p_id in id_list:
                if national:
                    mine = [v for v in records if self._species(v["id"]) == p_id]
                    is_seen = p_id in seen_set or any(self._species(i) == p_id for i in seen_set if isinstance(i, int))
                else:
                    mine = [v for v in records if int(v["id"]) == p_id]
                    is_seen = p_id in seen_set
                is_caught = bool(mine)
                species_name = self.game.assets.pokemon_names.get(str(self._species(p_id)), f"#{p_id}").upper()

                entry = {
                    "id": p_id,
                    "status": 0,
                    "shiny": False,
                    "form": "normal",
                    "name": "???"
                }

                if is_caught:
                    entry["status"] = 2
                    entry["name"] = species_name
                    entry["shiny"] = any(v.get("shiny") for v in mine)
                    entry["gmax"] = any(v.get("gmax") for v in mine)
                elif is_seen:
                    entry["status"] = 1
                    entry["name"] = species_name

                if self.show_shinies_only:
                    if not entry["shiny"]:
                        continue

                self.full_dex.append(entry)

            for k, v in caught_data.items():
                if v.get('id') == nown_id:
                    self.full_dex.append({
                        "id": nown_id,
                        "status": 2,
                        "shiny": v.get("shiny", False),
                        "form": "normal",
                        "name": "NOWN"
                    })
                    break

            def get_dex_sort_id(p):
                pid = p.get("id", 0)
                if isinstance(pid, int) and pid >= 2000:
                    mapping = self.game.loader.area_data.get("FORM_MAP", {}).get(str(pid))
                    if mapping:
                        return mapping.get("id", pid)
                return pid

            if self.sort_mode == "NUMBER":
                self.full_dex.sort(key=get_dex_sort_id)
            else:
                self.full_dex.sort(key=lambda x: (
                    0 if x['status'] == 2 else 1,
                    x.get("name", "ZZZ").upper() if x['status'] == 2 else get_dex_sort_id(x)
                ))

            nown = next((p for p in self.full_dex if p['id'] == nown_id), None)
            if nown:
                self.full_dex.remove(nown)
                self.full_dex.insert(0, nown)

            return
        else:
            source_data = self.game.data.data.get("pokedex", {})
            self.full_dex = [
                p for p in source_data.values()
                if p.get("form", "normal") == self.current_tab
                or (self.current_tab == "gmax" and p.get("gmax"))
            ]

        if self.show_shinies_only:
            self.full_dex = [p for p in self.full_dex if p.get("shiny")]

        if self.sort_mode == "NUMBER":
            self.full_dex.sort(key=lambda x: x.get("id", 0))
        else:
            self.full_dex.sort(key=lambda x: x.get("name", "ZZZ"))

    def set_tab(self, tab_name):
        self.current_tab = tab_name
        self.page = 0
        self.refresh_dex()

    def toggle_shiny_filter(self):
        self.show_shinies_only = not self.show_shinies_only
        self.page = 0
        self.refresh_dex()
        self.btn_shiny_toggle.bg_color = GOLD if self.show_shinies_only else BLUE

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.popup_active:
                    popup_hit = self.popup_rect.collidepoint(event.pos)
                    if not popup_hit:
                        self.hide_popup()
                    continue

                if self.btn_next.collidepoint(event.pos) and (self.page + 1) * self.PER_PAGE < len(self.full_dex):
                    self.page += 1
                elif self.btn_prev.collidepoint(event.pos) and self.page > 0:
                    self.page -= 1
                else:
                    for r, p_id in self.dex_btns:
                        if r.collidepoint(event.pos):
                            self.popup_active = True
                            self.selected_pkmn_id = p_id
                            self.popup_rect.topleft = (event.pos[0] + 10, event.pos[1] + 10)
                            if self.popup_rect.right > self.game.width:
                                self.popup_rect.right = event.pos[0] - 10

                            self.btn_cry.rect.topleft = (self.popup_rect.x + 10, self.popup_rect.y + 10)
                            self.btn_area.rect.topleft = (self.popup_rect.x + 10, self.popup_rect.y + 70)
                            self.btn_info.rect.topleft = (self.popup_rect.x + 10, self.popup_rect.y + 130)
                            if self.popup_rect.bottom > self.game.height:
                                self.popup_rect.bottom = self.game.height - 10
                                for k, btn in enumerate((self.btn_cry, self.btn_area, self.btn_info)):
                                    btn.rect.topleft = (self.popup_rect.x + 10, self.popup_rect.y + 10 + 60 * k)
                            self.btn_cry.set_visibility(True)
                            self.btn_area.set_visibility(True)
                            self.btn_info.set_visibility(bool(self._caught_entry(p_id)))
                            return


    def update(self):
        pass

    def draw(self):
        """The menu frame (src/ui/theme.py): red header with the Dex and its count, the filter row,
        a grid of entry cards, the page bar."""
        screen = self.game.screen
        width = self.game.width
        f = self.game.assets.fonts
        accent = theme.ACCENT["dex"]
        theme.menu_background(screen, accent)

        if self.current_tab == "normal" and not self.show_shinies_only:
            in_view = [e for e in self.full_dex if e.get("id") != self.game.loader.get_special_id("NOWN", 3025)]
            caught_text = f"Caught {sum(1 for e in in_view if e['status'] == 2)} / {len(in_view)}"
        else:
            total_caught = len({v['id'] for v in self.game.data.data["pokedex"].values() if isinstance(v, dict) and 'id' in v})
            caught_text = f"Caught {total_caught}"
        Utils.draw_text_outline(screen, caught_text, f["button"], WHITE, width - 24, theme.HEADER_H // 2 - 4,
                                align="right", outline_color=theme.shade(accent, 0.45), thickness=3)
        Utils.draw_text_outline(screen, "POKéDEX", f["button"], WHITE, 176, theme.HEADER_H // 2 - 4,
                                align="left", outline_color=theme.shade(accent, 0.45), thickness=3)

        for btn in self.tab_buttons:
            btn.bg_color = accent if btn.tab == self.current_tab else theme.TAB_OFF
        self.btn_shiny_toggle.bg_color = theme.BAG if self.show_shinies_only else theme.TAB_OFF
        self.btn_sort.bg_color = theme.TAB_OFF

        cols, rows, per_page = self.COLS, self.ROWS, self.PER_PAGE
        start_idx = self.page * per_page
        current_view = self.full_dex[start_idx: start_idx + per_page]
        gap = 14
        cw = (self.grid_rect.w - gap * (cols - 1)) // cols
        ch = (self.grid_rect.h - gap * (rows - 1)) // rows
        mouse = pygame.mouse.get_pos()
        nown_id = self.game.loader.get_special_id("NOWN", 3025)

        self.dex_btns = []
        hovered = None
        for i in range(per_page):
            c, r = i % cols, i // cols
            rect = pygame.Rect(self.grid_rect.x + c * (cw + gap), self.grid_rect.y + r * (ch + gap), cw, ch)
            if i >= len(current_view):
                pygame.draw.rect(screen, theme.shade(theme.MENU_BG, 1.25), rect, border_radius=12)
                continue
            p_entry = current_view[i]
            status = p_entry.get("status", 2)
            hover = status > 0 and rect.collidepoint(mouse) and not self.popup_active
            theme.card(screen, rect, hover=hover, accent=accent,
                       fill=theme.TEXTBOX if status else (214, 218, 228))

            id_num = p_entry['id']
            if isinstance(id_num, int):
                id_num = self._species(id_num)  # (Alolan Meowth is No.052, like Meowth)
            display_id = "???" if p_entry['id'] == nown_id else (
                f"No.{id_num:03d}" if isinstance(id_num, int) else f"#{id_num}")
            theme.shadow_text(screen, display_id, f["label"], rect.x + 12, rect.y + 8)
            from src.pokemon.loader import PokemonLoader as _PL  # (older saves: "ALOLAN RATTATA")
            name = _PL.plain_name(p_entry["name"]).title() if p_entry["name"] != "???" else "???"
            nf = f["label"] if f["label"].size(name)[0] <= rect.w - 16 else f["caption"]
            theme.shadow_text(screen, name, nf, rect.centerx, rect.bottom - 20, align="center")

            if status > 0:
                icon = fit_sprite(self.game.assets.get_pokemon_image(
                    p_entry["id"], p_entry.get("form", "normal"), p_entry.get("shiny", False)
                ), rect.w - 40, rect.h - 62)
                if status == 1:  # seen, not caught: a silhouette
                    icon.fill((40, 40, 48), special_flags=pygame.BLEND_RGB_MULT)
                screen.blit(icon, icon.get_rect(center=(rect.centerx, rect.centery + 1)))
                if hover:
                    hovered = p_entry
                if status == 2 and self.game.assets.ui_ball:
                    ball = pygame.transform.scale(self.game.assets.ui_ball, (22, 22))
                    screen.blit(ball, (rect.right - 30, rect.y + 8))
                if p_entry.get("shiny"):
                    Utils.draw_star(screen, GOLD, (rect.right - 46, rect.top + 19), 10)
                if p_entry.get("gmax") and status == 2:
                    _draw_gmax_tag(screen, f["tiny"], rect.left + 8, rect.bottom - 46)
                self.dex_btns.append((rect, p_entry["id"]))
            else:
                theme.shadow_text(screen, "?", f["big"], rect.centerx, rect.centery, color=(150, 156, 172),
                                  align="center")

        # The page bar: < Page 2 / 9 >
        pages = max(1, -(-len(self.full_dex) // per_page))
        theme.draw_textbox(screen, self.bar_rect)
        page_text = f"Page {self.page + 1} / {pages}"
        bf = f["s_med"]
        ty = self.bar_rect.centery - bf.get_height() // 2 - 2
        theme.shadow_text(screen, page_text, bf, self.btn_next.x - 24, ty, align="right")
        if hovered:  # the entry under the pointer
            state = "Caught" if hovered.get("status") == 2 else "Seen"
            hint = f"{hovered['name'].title()}  -  {state}" + ("  (shiny)" if hovered.get("shiny") else "")
        else:
            hint = "Tap one: cry, area, info"
        theme.shadow_text(screen, hint, bf, self.btn_prev.right + 24, ty)
        for rect, label, ok in ((self.btn_prev, "<", self.page > 0),
                                (self.btn_next, ">", (self.page + 1) * per_page < len(self.full_dex))):
            theme.command_button(screen, rect, label, f["button"], accent if ok else theme.TAB_OFF,
                                 hover=ok and rect.collidepoint(mouse))

        if self.popup_active:  # the panel behind CRY / AREA / INFO
            theme.draw_panel(screen, self.popup_rect.inflate(8, 8))
        self.game.ui_manager.draw(screen)
