"""The Pokedex: regional dexes, the National Dex, and its pages (in Pokemon Journeys' look)."""

import io
import json
import math
import os

import pygame
from src.states.base import GameState
from src.ui.panels import CommandButton
from src.ui import theme
from src.utils import Utils
from src.config import GOLD, VOLUME
from src.pokemon.data import Pokemon
from src.pokemon import forms


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
# Jordan (11-05): the Pokedex in Pokemon Journeys' look (its Pokemon Essentials Pokedex, assets/pokedex,
# dev/builders/import_pokedex.py), laid out as it lays its 512 x 384 screens out, scaled to ours:
# - the LIST: the Pokemon you're on at the left (its name, its picture, Seen / Owned), the dex down the
#   right (owned / seen marks, number, name), a scroll bar. Tap the dex's name to switch dexes, a row to
#   pick it, again (or its picture) for its entry. A small star (bottom left) shows only your shinies.
# - an ENTRY, three pages (INFO, AREA, FORMS) like Journeys': INFO its kind, types, height, weight,
#   footprint and where it lives (in our words); AREA its region's map, a dot where it lives; FORMS its
#   forms you've found (Megas, Gigantamax, regional forms, Unown's letters, its shiny look).
# - SEARCH (Journeys' search screen): order, name, type, height, weight, colour, shape.
# Regional forms go by their species in the Pokedex (number and name).
REGION_FORM_NAMES = ("alolan", "galarian", "hisuian", "paldean", "pinkan", "valencia")
# Journeys' type labels (icon_types.png), a row each, in Essentials' order
TYPE_ROWS = ("NORMAL", "FIGHTING", "FLYING", "POISON", "GROUND", "ROCK", "BUG", "GHOST", "STEEL", "???", "FIRE",
             "WATER", "GRASS", "ELECTRIC", "PSYCHIC", "ICE", "DRAGON", "DARK", "FAIRY")
SEARCH_TYPES = tuple(t for t in TYPE_ROWS if t != "???")
COLORS = ("Red", "Blue", "Yellow", "Green", "Black", "Brown", "Purple", "Gray", "White", "Pink")
SHAPES = 14
ORDERS = ("Numerical", "A to Z", "Heaviest", "Lightest", "Tallest", "Smallest")
NAME_GROUPS = ("ABC", "DEF", "GHI", "JKL", "MNO", "PQR", "STU", "VWX", "YZ")
HEIGHTS = (0, 0.5, 1, 1.5, 2, 3, 5, 10, 20, 100)
WEIGHTS = (0, 5, 10, 25, 50, 100, 200, 500, 1000, 10000)
UNOWN_FORMS = ["normal"] + list("bcdefghijklmnopqrstuvwxyz") + ["exclamation", "question"]
BASE, SHADOW = (88, 88, 80), (168, 184, 184)
WHITE_T, BLACK_T = (248, 248, 248), (0, 0, 0)
ROW_H, ROWS_SHOWN = 32, 10   # the list's rows (Journeys' sizes)

_INFO = {}
# The dexes in generation order (Jordan, 11-05): the Orange Islands after Johto, Orre after Hoenn.
GEN_ORDER = ("KANTO", "JOHTO", "ORANGE", "HOENN", "ORRE", "SINNOH", "UNOVA", "KALOS", "ALOLA", "GALAR", "PALDEA")
TRAVEL_DEXES = ("ORANGE", "ORRE")  # (no Pokedex of their own: what lives there, in National order)
_MAPS = {}  # the AREA page's maps, loaded once


def dex_info(game):
    """assets/dex_info.json: each species' kind, height (m), weight (kg), colour, shape, habitat."""
    if "d" not in _INFO:
        try:
            with open(os.path.join(game.assets.assets_dir, "dex_info.json"), encoding="utf-8") as f:
                _INFO["d"] = json.load(f)
        except (OSError, ValueError):
            _INFO["d"] = {}
    return _INFO["d"]


def travel_dex(game, region):
    """The Orange Islands' / Orre's dex: every Pokemon in its wild areas (grass, zones, day / night,
    fishing) and its starters, in National Dex order."""
    key = "travel_" + region
    if key not in _INFO:
        data = game.loader.area_data
        found = set(game.story_manager.get_region_start(region).get("starters", []) or [])
        for k, a in data.get("STORY_PROGRESSION", {}).items():
            if not isinstance(a, dict) or str(a.get("region") or "").upper() != region:
                continue
            pools = [a.get(n) for n in ("wild_pool_percentages", "day_pool_percentages", "night_pool_percentages")]
            pools += list((a.get("zone_pools") or {}).values())
            pools += [f"{k}_{r}_PERCENTAGES" for r in ("OLD_ROD", "GOOD_ROD", "SUPER_ROD")]
            for pool in pools:
                for pid in (data.get(pool) or {}) if isinstance(pool, str) else ():
                    if str(pid).isdigit():
                        found.add(int(pid))
        _INFO[key] = sorted(i for i in found if isinstance(i, int))
    return list(_INFO[key])


def gen_rank(view):
    return (GEN_ORDER.index(view) if view in GEN_ORDER else len(GEN_ORDER)) if view != "NATIONAL" else 99


class DexFrame:
    """Journeys' 512 x 384 Pokedex screens drawn on ours: scaled by k, centred; a dark grid at the sides."""

    def __init__(self, game):
        self.game = game
        self.k = min(game.width / 512, game.height / 384)
        self.ox = (game.width - 512 * self.k) / 2
        self.oy = (game.height - 384 * self.k) / 2
        self._imgs, self._scaled, self._caps = {}, {}, {}

    def p(self, x, y):
        return int(self.ox + x * self.k), int(self.oy + y * self.k)

    def r(self, x, y, w, h):
        return pygame.Rect(int(self.ox + x * self.k), int(self.oy + y * self.k), int(w * self.k), int(h * self.k))

    def img(self, name):
        if name not in self._imgs:
            try:
                self._imgs[name] = pygame.image.load(os.path.join(self.game.assets.assets_dir, "pokedex",
                                                                  name + ".png")).convert_alpha()
            except (pygame.error, FileNotFoundError):
                self._imgs[name] = None
        return self._imgs[name]

    def part(self, name, rect=None, k=None):
        """A picture (or a part of it), scaled up crisp."""
        k = k or self.k
        key = (name, tuple(rect) if rect else None, k)
        if key not in self._scaled:
            src = self.img(name)
            if src is None:
                self._scaled[key] = None
            else:
                if rect:
                    src = src.subsurface(pygame.Rect(rect).clip(src.get_rect()))
                self._scaled[key] = pygame.transform.scale(src, (max(1, int(src.get_width() * k)),
                                                                 max(1, int(src.get_height() * k))))
        return self._scaled[key]

    def background(self, screen, name):
        pic = self.part(name)
        if pic is None:
            screen.fill((60, 60, 70))
            return
        x0, y0 = self.p(0, 0)
        if x0 > 0:  # the sides: a dark grid
            screen.fill((52, 54, 64))
            cell = int(16 * self.k)
            for x in range(x0 % cell, self.game.width, cell):
                pygame.draw.line(screen, (64, 66, 78), (x, 0), (x, self.game.height))
            for y in range(y0 % cell, self.game.height, cell):
                pygame.draw.line(screen, (64, 66, 78), (0, y), (self.game.width, y))
        screen.blit(pic, (x0, y0))

    def text(self, screen, s, x, y, align=0, color=BASE, shadow=SHADOW, font=None):
        """Essentials' text: at (x, y) of the 512 x 384 screen, the top of its 32-high line (its capitals
        centred in the line, whatever our font's size); 0 left, 1 right, 2 centred."""
        font = font or self.game.assets.fonts["button"]
        s = str(s)
        img = font.render(s, True, color)
        if font not in self._caps:
            cap = font.render("H", True, (0, 0, 0)).get_bounding_rect()
            self._caps[font] = cap.y + cap.h / 2
        px, py = self.p(x, y + 16)
        py = int(py - self._caps[font])
        if align == 1:
            px -= img.get_width()
        elif align == 2:
            px -= img.get_width() // 2
        if shadow:
            screen.blit(font.render(s, True, shadow), (px + 2, py + 2))
        screen.blit(img, (px, py))
        return img.get_width()

    def type_label(self, screen, t, x, y):
        """A type's label (icon_types.png: 96 x 32 a row) at (x, y)."""
        row = TYPE_ROWS.index(t) if t in TYPE_ROWS else 9
        pic = self.part("icon_types", (0, row * 32, 96, 32))
        if pic:
            screen.blit(pic, self.p(x, y))


def fit(img, w, h):
    """A sprite in a w x h space: grown a whole number of times (each pixel a clean square, small
    Pokemon small and big ones big, as in the games), or shrunk smoothly if it's bigger."""
    if img is None:
        return None
    k = min(w / max(1, img.get_width()), h / max(1, img.get_height()))
    if k >= 1:
        k = int(k)
        return pygame.transform.scale(img, (img.get_width() * k, img.get_height() * k)) if k > 1 else img
    return pygame.transform.smoothscale(img, (max(1, int(img.get_width() * k)), max(1, int(img.get_height() * k))))


def arrow(screen, fr, x, y, d, color=WHITE_T):
    """A small arrow at (x, y) of the 512 x 384 screen, pointing left (d -1) or right (1)."""
    pts = [(x + 7 * d, y), (x - 6 * d, y - 9), (x - 6 * d, y + 9)]
    pts = [fr.p(px, py) for px, py in pts]
    pygame.draw.polygon(screen, color, pts)
    pygame.draw.polygon(screen, BLACK_T, pts, max(2, int(fr.k)))


def silhouette(img):
    img = img.copy()
    img.fill((40, 40, 48), special_flags=pygame.BLEND_RGB_MULT)
    return img


def play_cry(game, pid):
    try:
        pygame.mixer.Sound(game.assets.get_cry(pid)).play().set_volume(VOLUME)
    except Exception:
        pass


class PokedexState(GameState):
    """The Pokedex's list (see above)."""

    def normal_dex_ids(self, caught_data, seen_ids):
        if getattr(self, "dex_view", None) in TRAVEL_DEXES:
            return travel_dex(self.game, self.dex_view)
        return _dex_ids(self.game.story_manager, caught_data, seen_ids, getattr(self, "dex_view", None))

    def dex_views(self):
        """Regional dexes the player has (the Orange Islands and Orre once you've been), in generation
        order, then the National Dex once it's unlocked."""
        story = self.game.story_manager
        views = dex_regions(story)
        visited = story.visited_regions()
        views = sorted(views + [r for r in TRAVEL_DEXES if r in visited and r not in views], key=gen_rank)
        if story.story_flags.get("unlocked_national_dex") or len(views) > 1:
            views = views + ["NATIONAL"]
        return views

    def cycle_dex_view(self, step=1):
        views = self.dex_views()
        self.set_dex_view(views[(views.index(self.dex_view) + step) % len(views)] if self.dex_view in views else views[0])

    def set_dex_view(self, view):
        self.dex_view = view
        self.index = self.top = 0
        self.picking = None
        self.refresh_dex()

    def view_title(self, view):
        return (f"{view.title()} Pokédex" if view and view != "NATIONAL" else "National Pokédex")

    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.current_tab = "normal"
        self.show_shinies_only = False
        self.full_dex = []
        self.sort_mode = "NUMBER"
        self.search = None          # the search's settings while its results show
        self.index = self.top = 0   # the row you're on, the first row shown
        self.selected_pkmn_id = None
        self.frame = DexFrame(game)
        self.picking = None         # the dex list (tap the dex's name): the row you're on
        self.title_hits = {}        # "<", ">" and the name: where they are on screen
        views = self.dex_views()
        here = game.story_manager.get_current_region()
        self.dex_view = here if here in views else views[0]
        self.refresh_dex()
        f = game.assets.fonts
        side = max(110, int(self.frame.ox) - 20)  # (in the dark sides, clear of the page)
        self.btn_back = CommandButton((10, 40, side, 56), "BACK", f["button"], self.go_back,
                                      bg_color=theme.BACK, autosize=False)
        self.btn_search = CommandButton((game.width - 10 - side, 40, side, 56), "SEARCH",
                                        f["label"], self.open_search, bg_color=(48, 160, 200), autosize=False)

    # ---------------------------------------------------------------- coming and going
    def go_back(self):
        if self.search is not None:  # (search results: back to the whole dex first)
            self.search = None
            self.index = self.top = 0
            self.refresh_dex()
            return
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def start(self):
        for b in (self.btn_back, self.btn_search):
            if b not in self.game.ui_manager.elements:
                self.game.ui_manager.add_element(b)

    def open_search(self):
        self.game.change_state(DexSearchState(self.game, self))

    def open_entry(self, page=1):
        if 0 <= self.index < len(self.full_dex) and self.full_dex[self.index].get("status", 0) > 0:
            self.game.change_state(DexEntryState(self.game, self, self.index, page))

    # ---------------------------------------------------------------- the data
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
        """The entry of the Pokemon picked (selected_pkmn_id)."""
        if self.selected_pkmn_id is None:
            return
        i = next((k for k, e in enumerate(self.full_dex) if e["id"] == self.selected_pkmn_id), None)
        if i is None:  # (not in this dex: on its own)
            self.full_dex = self.full_dex + [{"id": self.selected_pkmn_id, "status": 2 if self._caught_entry(
                self.selected_pkmn_id) else 1, "shiny": False, "form": "normal",
                "name": self.game.assets.pokemon_names.get(str(self._species(self.selected_pkmn_id)), "???").upper()}]
            i = len(self.full_dex) - 1
        self.index = i
        self.open_entry()

    def toggle_sort(self):
        self.sort_mode = "NAME" if self.sort_mode == "NUMBER" else "NUMBER"
        self.refresh_dex()

    def toggle_shiny_filter(self):
        self.show_shinies_only = not self.show_shinies_only
        self.index = self.top = 0
        self.refresh_dex()

    def refresh_dex(self):
        nown_id = self.game.loader.get_special_id("NOWN", 3025)

        if self.current_tab == "unown":  # (Unown's letters: its FORMS page)
            caught_data = self.game.data.data.get("pokedex", {})
            from src.pokemon.loader import PokemonLoader
            self.full_dex = []
            for f in UNOWN_FORMS:
                keys = ["201-normal", "201-a"] if f == "normal" else [f"201-{f}"]  # (older saves: "201-a")
                found = [caught_data[k] for k in keys if isinstance(caught_data.get(k), dict)]
                self.full_dex.append({"id": 201, "status": 2 if found else 0, "shiny": any(v.get("shiny") for v in found),
                                      "form": f, "name": PokemonLoader.unown_name(f) if found else "???"})
            return
        caught_data = self.game.data.data.get("pokedex", {})
        seen_ids = self.game.data.data.get("seen_pokemon", [])
        id_list = self.normal_dex_ids(caught_data, seen_ids)
        national = self.dex_view in (None, "NATIONAL")
        if national:  # one entry per species
            id_list = list(dict.fromkeys(self._species(i) for i in id_list))
        records = [v for v in caught_data.values() if isinstance(v, dict) and "id" in v]
        seen_set = set(seen_ids)
        out = []
        for p_id in id_list:
            if national:
                mine = [v for v in records if self._species(v["id"]) == p_id]
                is_seen = p_id in seen_set or any(self._species(i) == p_id for i in seen_set if isinstance(i, int))
            else:
                mine = [v for v in records if int(v["id"]) == p_id]
                is_seen = p_id in seen_set
            entry = {"id": p_id, "status": 0, "shiny": False, "form": "normal", "name": "???"}
            name = self.game.assets.pokemon_names.get(str(self._species(p_id)), f"#{p_id}").upper()
            if mine:
                entry.update(status=2, name=name, shiny=any(v.get("shiny") for v in mine),
                             gmax=any(v.get("gmax") for v in mine))
            elif is_seen:
                entry.update(status=1, name=name)
            if self.show_shinies_only and not entry["shiny"]:
                continue
            out.append(entry)
        nown = next((v for v in caught_data.values() if isinstance(v, dict) and v.get("id") == nown_id), None)
        if nown and (not self.show_shinies_only or nown.get("shiny")):
            out.append({"id": nown_id, "status": 2, "shiny": nown.get("shiny", False), "form": "normal", "name": "NOWN"})

        def number(p):
            pid = p.get("id", 0)
            if isinstance(pid, int) and pid >= 2000:
                mapping = self.game.loader.area_data.get("FORM_MAP", {}).get(str(pid))
                if mapping:
                    return mapping.get("id", pid)
            return pid

        if self.sort_mode == "NUMBER":
            out.sort(key=number)
        else:
            out.sort(key=lambda x: (0 if x["status"] == 2 else 1, x.get("name", "ZZZ") if x["status"] == 2 else number(x)))
        # Nown (No. ???, only once caught) sits right after Unown (Jordan, 11-04)
        n = next((p for p in out if p["id"] == nown_id), None)
        if n:
            out.remove(n)
            after = next((k + 1 for k, p in enumerate(out) if self._species(p["id"]) == 201), None)
            if after is not None:  # (a Pokedex without Unown leaves it out too)
                out.insert(after, n)
        if self.search is not None:
            out = self._searched(out, number)
        self.full_dex = out
        self.index = min(self.index, max(0, len(out) - 1))

    def _searched(self, out, number):
        """The search's results (seen ones only: an unseen one is a blank page), in its order."""
        s, info, sets = self.search, dex_info(self.game), self.game.assets.movesets
        found = []
        for e in out:
            if e["status"] == 0:
                continue
            sp = self._species(e["id"])
            d = info.get(str(sp), {})
            types = [t.upper() for t in (sets.get(str(e["id"])) or sets.get(str(sp)) or {}).get("types", [])]
            name = e.get("name", "").upper()
            if s["name"] is not None and not name[:1] in NAME_GROUPS[s["name"]]:
                continue
            if any(t is not None and SEARCH_TYPES[t] not in types for t in (s["type1"], s["type2"])):
                continue
            if s["color"] is not None and d.get("color") != COLORS[s["color"]]:
                continue
            if s["shape"] is not None and d.get("shape") != s["shape"] + 1:
                continue
            h, w = d.get("height", 0), d.get("weight", 0)
            if not HEIGHTS[s["h"][0]] <= h <= HEIGHTS[s["h"][1]] or not WEIGHTS[s["w"][0]] <= w <= WEIGHTS[s["w"][1]]:
                continue
            found.append(e)
        key = {0: number, 1: lambda e: e.get("name", ""),
               2: lambda e: -info.get(str(self._species(e["id"])), {}).get("weight", 0),
               3: lambda e: info.get(str(self._species(e["id"])), {}).get("weight", 0),
               4: lambda e: -info.get(str(self._species(e["id"])), {}).get("height", 0),
               5: lambda e: info.get(str(self._species(e["id"])), {}).get("height", 0)}[s["order"]]
        return sorted(found, key=key)

    # ---------------------------------------------------------------- input
    def _row_rect(self, i):
        return self.frame.r(222, 46 + (i - self.top) * ROW_H, 244, ROW_H)

    def _move(self, step):
        if not self.full_dex:
            return
        self.index = max(0, min(len(self.full_dex) - 1, self.index + step))
        if self.index < self.top:
            self.top = self.index
        elif self.index >= self.top + ROWS_SHOWN:
            self.top = self.index - ROWS_SHOWN + 1

    def _scroll(self, step):
        self.top = max(0, min(max(0, len(self.full_dex) - ROWS_SHOWN), self.top + step))
        self.index = max(self.top, min(self.index, self.top + ROWS_SHOWN - 1))

    def _pick_rects(self):
        """The dex list: (view, rect on screen), one or two columns."""
        views = self.dex_views()
        cols = 1 if len(views) <= 7 else 2
        rows = -(-len(views) // cols)
        w, h = (220 if cols == 1 else 196), 30
        x0, y0 = 256 - (w * cols + 8 * (cols - 1)) / 2, 200 - (rows * (h + 4) + 36) / 2 + 36
        return [(v, self.frame.r(x0 + (i // rows) * (w + 8), y0 + (i % rows) * (h + 4), w, h))
                for i, v in enumerate(views)]

    def _pick_events(self, e):
        views = self.dex_views()
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_LEFT):
                self.picking = (self.picking - 1) % len(views)
            elif e.key in (pygame.K_DOWN, pygame.K_RIGHT):
                self.picking = (self.picking + 1) % len(views)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self.set_dex_view(views[self.picking])
            elif e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.picking = None
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
            self.picking = None
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for v, r in self._pick_rects():
                if r.collidepoint(e.pos):
                    self.set_dex_view(v)
                    return
            self.picking = None  # (a tap outside: closed)

    def open_picker(self):
        views = self.dex_views()
        self.picking = views.index(self.dex_view) if self.dex_view in views else 0

    def handle_events(self, events):
        fr = self.frame
        for e in events:
            if self.picking is not None:
                self._pick_events(e)
                continue
            if e.type == pygame.MOUSEWHEEL:
                self._scroll(-3 * e.y)
            elif e.type == pygame.KEYDOWN:
                keys = {pygame.K_UP: -1, pygame.K_DOWN: 1, pygame.K_PAGEUP: -ROWS_SHOWN, pygame.K_PAGEDOWN: ROWS_SHOWN}
                if e.key in keys:
                    self._move(keys[e.key])
                elif e.key in (pygame.K_LEFT, pygame.K_RIGHT) and self.search is None:
                    self.cycle_dex_view(-1 if e.key == pygame.K_LEFT else 1)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                    self.open_entry()
                elif e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    self.go_back()
                elif e.key == pygame.K_f:
                    self.open_search()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                self.go_back()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                pos = e.pos
                hit = next((k for k, r in self.title_hits.items() if r.collidepoint(pos)), None)
                if hit and self.search is None:  # the arrows: the next dex; its name: the list of them
                    if hit == "name":
                        self.open_picker()
                    else:
                        self.cycle_dex_view(-1 if hit == "<" else 1)
                elif fr.r(468, 48, 40, 30).collidepoint(pos):
                    self._scroll(-ROWS_SHOWN)
                elif fr.r(468, 346, 40, 30).collidepoint(pos):
                    self._scroll(ROWS_SHOWN)
                elif fr.r(468, 78, 40, 268).collidepoint(pos) and len(self.full_dex) > ROWS_SHOWN:
                    k = (pos[1] - fr.p(0, 78)[1]) / max(1, 268 * fr.k)
                    self.top = int(k * (len(self.full_dex) - ROWS_SHOWN))
                    self._scroll(0)
                elif fr.r(4, 290, 28, 26).collidepoint(pos):  # the shiny star
                    self.toggle_shiny_filter()
                elif fr.r(20, 84, 184, 210).collidepoint(pos):  # its picture: its entry
                    self.open_entry()
                else:
                    for i in range(self.top, min(len(self.full_dex), self.top + ROWS_SHOWN)):
                        if self._row_rect(i).collidepoint(pos):
                            if i == self.index:
                                self.open_entry()
                            else:
                                self.index = i
                                if self.full_dex[i].get("status", 0) > 0:
                                    play_cry(self.game, self.full_dex[i]["id"])
                            break

    def update(self):
        pass

    # ---------------------------------------------------------------- drawing
    def _label(self, e):
        nown_id = self.game.loader.get_special_id("NOWN", 3025)
        from src.pokemon.loader import PokemonLoader as _PL
        name = _PL.plain_name(e["name"]).title() if e["name"] != "???" else "???"
        if e["id"] == 201 and e.get("form", "normal") != "normal" and name != "???":
            name = _PL.unown_name(e["form"]).title()
        num = "???" if e["id"] == nown_id else f"{self._species(e['id']):03d}"
        return num, name

    def draw(self):
        screen, fr = self.game.screen, self.frame
        fr.background(screen, "bg_listsearch" if self.search is not None else "bg_list")
        title = self.view_title(self.dex_view)
        if self.show_shinies_only:
            title = "Shiny " + title
        big = self.game.assets.fonts["dialog"]
        w = fr.text(screen, title, 256, -1, 2, WHITE_T, BLACK_T, font=big)
        self.title_hits = {}
        if self.search is None:
            half = w / 2 / fr.k
            left, right = max(10, 256 - half - 22), min(502, 256 + half + 22)
            for key, x, d in (("<", left, -1), (">", right, 1)):
                arrow(screen, fr, x, 15, d)
                self.title_hits[key] = fr.r(x - 22, 0, 44, 34)
            self.title_hits["name"] = fr.r(256 - half - 4, 0, 2 * half + 8, 34)
        cur = self.full_dex[self.index] if 0 <= self.index < len(self.full_dex) else None
        if cur and cur.get("status", 0) > 0:
            self.selected_pkmn_id = cur["id"]
            fr.text(screen, self._label(cur)[1], 112, 50, 2, font=big)
            img = fit(self.game.assets.get_pokemon_image(cur["id"], cur.get("form", "normal"), cur.get("shiny", False)),
                      int(160 * fr.k), int(160 * fr.k))
            if img is not None:
                if cur["status"] == 1:
                    img = silhouette(img)
                screen.blit(img, img.get_rect(center=fr.p(112, 196)))
        else:
            self.selected_pkmn_id = None
        if self.search is not None:
            fr.text(screen, "Search results", 112, 304, 2)
            fr.text(screen, len(self.full_dex), 112, 336, 2)
        else:
            fr.text(screen, "Seen:", 42, 304)
            fr.text(screen, sum(1 for e in self.full_dex if e.get("status", 0) > 0), 182, 304, 1)
            fr.text(screen, "Owned:", 42, 336)
            fr.text(screen, sum(1 for e in self.full_dex if e.get("status", 0) == 2), 182, 336, 1)
        # the shiny star (discreet: bottom left of the counts)
        cx, cy = fr.p(17, 302)
        Utils.draw_star(screen, GOLD if self.show_shinies_only else (200, 204, 210), (cx, cy), int(9 * fr.k))
        # the list
        own, seen = fr.part("icon_own"), fr.part("icon_seen")
        f = self.game.assets.fonts["button"]
        for i in range(self.top, min(len(self.full_dex), self.top + ROWS_SHOWN)):
            e = self.full_dex[i]
            r = self._row_rect(i)
            if i == self.index:
                cur_img = fr.part("cursor_list")
                if cur_img:
                    screen.blit(cur_img, (r.x, r.y - int(6 * fr.k)))
            y = 46 + (i - self.top) * ROW_H
            num, name = self._label(e)
            if e.get("status", 0) > 0:
                mark = own if e["status"] == 2 else seen
                if mark:
                    screen.blit(mark, fr.p(232, y + 8 - 6))
                fr.text(screen, f"{num}  {name}", 268, y, font=f)
                if e.get("shiny"):
                    Utils.draw_star(screen, GOLD, fr.p(452, y + 16), int(5 * fr.k))
            else:
                fr.text(screen, f"{num}  ----------", 268, y, font=f)
        # the scroll bar
        n = len(self.full_dex)
        if n > ROWS_SHOWN:
            slider = fr.img("icon_slider")
            if slider:
                if self.top > 0:
                    screen.blit(fr.part("icon_slider", (0, 0, 40, 30)), fr.p(468, 48))
                if self.top + ROWS_SHOWN < n:
                    screen.blit(fr.part("icon_slider", (0, 30, 40, 30)), fr.p(468, 346))
                box_h = max(40, min(268, int(268 * ROWS_SHOWN / n) + 24))
                y = 78 + int((268 - box_h) * self.top / max(1, n - ROWS_SHOWN))
                screen.blit(fr.part("icon_slider", (40, 0, 40, 8)), fr.p(468, y))
                mid = fr.part("icon_slider", (40, 8, 40, 16))
                for yy in range(y + 8, y + box_h - 16, 16):
                    screen.blit(mid, fr.p(468, yy))
                screen.blit(fr.part("icon_slider", (40, 24, 40, 16)), fr.p(468, y + box_h - 16))
        self.game.ui_manager.draw(screen)
        if self.picking is not None:
            self._draw_picker(screen)

    def _draw_picker(self, screen):
        """The dex list over the page: every dex you have, in generation order."""
        fr = self.frame
        shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 150))
        screen.blit(shade, (0, 0))
        cells = self._pick_rects()
        box = cells[0][1].unionall([r for _v, r in cells]).inflate(int(24 * fr.k), int(24 * fr.k))
        box.y -= int(26 * fr.k)
        box.h += int(26 * fr.k)
        pygame.draw.rect(screen, (232, 56, 56), box, border_radius=int(8 * fr.k))
        pygame.draw.rect(screen, (24, 24, 24), box, max(2, int(2 * fr.k)), border_radius=int(8 * fr.k))
        f = self.game.assets.fonts["button"]
        title = f.render("Choose a Pokédex", True, WHITE_T)
        screen.blit(title, title.get_rect(center=(box.centerx, box.y + int(18 * fr.k))))
        for i, (v, r) in enumerate(cells):
            on = i == self.picking
            pygame.draw.rect(screen, (255, 236, 150) if on else (248, 248, 248), r, border_radius=int(5 * fr.k))
            pygame.draw.rect(screen, (24, 24, 24) if on else (168, 184, 184), r, max(2, int(fr.k)),
                             border_radius=int(5 * fr.k))
            label = f.render(self.view_title(v), True, BASE)
            if label.get_width() > r.w - 12:
                label = pygame.transform.smoothscale(label, (r.w - 12, int(label.get_height() * (r.w - 12) / label.get_width())))
            screen.blit(label, label.get_rect(center=r.center))


class DexEntryState(GameState):
    """A Pokemon's entry: INFO, AREA and FORMS (left / right), the next one up or down; its cry on a tap."""

    PAGES = ("INFO", "AREA", "FORMS")

    def __init__(self, game, dex, index, page=1):
        super().__init__(game)
        self.dex, self.frame = dex, dex.frame
        self.nav = [i for i, e in enumerate(dex.full_dex) if e.get("status", 0) > 0]
        self.index = index
        self.page = page
        f = game.assets.fonts
        side = max(110, int(self.frame.ox) - 20)
        self.btn_back = CommandButton((10, 40, side, 56), "BACK", f["button"], self.go_back,
                                      bg_color=theme.BACK, autosize=False)
        # the next Pokemon up or down the dex (the keys' up / down), in the right-hand side
        rx = game.width - 10 - side
        self.btn_prev = CommandButton((rx, 40, side, 56), "PREV", f["button"], lambda: self._step(-1),
                                      bg_color=(48, 160, 200), autosize=False)
        self.btn_next = CommandButton((rx, 108, side, 56), "NEXT", f["button"], lambda: self._step(1),
                                      bg_color=(48, 160, 200), autosize=False)
        self.area_region = None
        self._load()
        play_cry(game, self.pid)

    def start(self):
        for b in (self.btn_back, self.btn_prev, self.btn_next):
            if b not in self.game.ui_manager.elements:
                self.game.ui_manager.add_element(b)

    def turn_page(self, d):
        """The tab bar's arrows (and left / right): INFO, AREA, FORMS, round and round."""
        self.page = (self.page - 1 + d) % 3 + 1

    def go_back(self):
        self.dex.index = self.index
        if self.dex.index < self.dex.top or self.dex.index >= self.dex.top + ROWS_SHOWN:
            self.dex.top = max(0, self.dex.index - ROWS_SHOWN // 2)
        self.game.change_state(self.dex)

    # ---------------------------------------------------------------- the Pokemon
    def _load(self):
        e = self.dex.full_dex[self.index]
        self.entry, self.pid = e, e["id"]
        self.species = self.dex._species(self.pid)
        self.owned = e.get("status") == 2
        self.num, self.name = self.dex._label(e)
        self.info = dex_info(self.game).get(str(self.species), {})
        sets = self.game.assets.movesets
        self.types = [t.upper() for t in (sets.get(str(self.pid)) or sets.get(str(self.species)) or {}).get("types", [])]
        self.areas = self._areas()
        self.forms = self._forms()
        self.form_idx = 0
        self._form_mon = {}
        regions = list(dict.fromkeys(r for r, _k in self.areas))
        here = self.dex.dex_view if self.dex.dex_view in regions else None
        self.area_region = here or (regions[0] if regions else None)

    def _areas(self):
        """[(map region, area key)] where it lives: a wild pool, a zone's, day or night, fishing."""
        data = self.game.loader.area_data
        prog = data.get("STORY_PROGRESSION", {})
        from src.states.region_map import view_of
        want = {str(self.pid), str(self.species)}
        out = []
        for key, a in prog.items():
            if not isinstance(a, dict) or a.get("area_type") == "town" and not a.get("wild_pool_percentages"):
                continue
            pools = [a.get(k) for k in ("wild_pool_percentages", "day_pool_percentages", "night_pool_percentages")]
            pools += list((a.get("zone_pools") or {}).values())
            pools += [f"{key}_{r}_PERCENTAGES" for r in ("OLD_ROD", "GOOD_ROD", "SUPER_ROD")]
            if any(p and want & set((data.get(p) or {}).keys()) for p in pools):
                view = view_of(self.game, key)
                if view:
                    out.append((view, key))
        return out

    def _forms(self):
        """[(pid, form, shiny, label)]: its look, then each form you've found, and its shiny looks."""
        records = [v for v in self.game.data.data.get("pokedex", {}).values() if isinstance(v, dict) and "id" in v]
        mine = [v for v in records if self.dex._species(v["id"]) == self.species]
        out = [(self.pid, self.entry.get("form", "normal"), False, "Normal")]
        if self.species == 201:  # Unown: its letters you've caught, A to Z, ! and ?
            from src.pokemon.loader import PokemonLoader
            have = {("normal" if v.get("form") in ("a", "normal") else v.get("form")) for v in mine}
            out = [(201, f, False, PokemonLoader.unown_name(f).title()) for f in UNOWN_FORMS if f in have] or out
        for v in mine:
            pid, form = int(v["id"]), v.get("form", "normal")
            if self.species == 201:
                break
            label = forms.item_label(str(form)) if form != "normal" else (
                self.game.assets.pokemon_names.get(str(pid), "").title() if pid != self.species else "Normal")
            if pid >= 2000 and form == "normal":
                mapping = self.game.loader.area_data.get("FORM_MAP", {}).get(str(pid)) or {}
                label = str(mapping.get("form", "form")).title()
            if (pid, form, False, label) not in out:
                out.append((pid, form, False, label))
            if v.get("gmax") and (pid, "gmax", False, "Gigantamax") not in out:
                out.append((pid, "gmax", False, "Gigantamax"))
        for v in mine:
            if v.get("shiny"):
                f = "normal" if v.get("form") == "a" else v.get("form", "normal")
                lab = next((lab for p, ff, _s, lab in out if p == int(v["id"]) and ff == f), "Normal")
                if (int(v["id"]), f, True, f"{lab} (shiny)") not in out:
                    out.append((int(v["id"]), f, True, f"{lab} (shiny)"))
        return out

    def _mon(self, k):
        """Form k's front and back pictures (as drawn, not scaled), loaded once."""
        if k not in self._form_mon:
            pid, form, shiny, _l = self.forms[k]
            pics = [None, None]
            try:
                raw = self.game.loader.fetch_specific(pid, form=form, is_shiny=shiny)
                for i, key in enumerate(("img", "back_img")):
                    if raw.get(key):
                        pics[i] = pygame.image.load(io.BytesIO(raw[key])).convert_alpha()
            except Exception:
                pass
            self._form_mon[k] = pics if pics[0] is not None else None
        return self._form_mon[k]

    def _step(self, d):
        if self.index in self.nav:
            i = self.nav.index(self.index) + d
            if 0 <= i < len(self.nav):
                self.index = self.nav[i]
                self._load()
                play_cry(self.game, self.pid)

    # ---------------------------------------------------------------- input
    def handle_events(self, events):
        fr = self.frame
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    self.turn_page(-1 if e.key == pygame.K_LEFT else 1)
                elif e.key == pygame.K_UP:
                    self._step(-1)
                elif e.key == pygame.K_DOWN:
                    self._step(1)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE) and self.page == 3:
                    self.form_idx = (self.form_idx + 1) % len(self.forms)
                elif e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    self.go_back()
            elif e.type == pygame.MOUSEWHEEL:
                self._step(-e.y)
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                self.go_back()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                pos = e.pos
                # the tab bar (Journeys' picture): its arrows turn the page; a page's name opens it
                for page, (x0, x1) in enumerate(((52, 116), (138, 204), (226, 308)), start=1):
                    if fr.r(x0, 0, x1 - x0, 34).collidepoint(pos):
                        self.page = page
                        break
                else:
                    if fr.r(8, 0, 44, 34).collidepoint(pos):
                        self.turn_page(-1)
                    elif fr.r(308, 0, 44, 34).collidepoint(pos):
                        self.turn_page(1)
                    elif self.page == 1 and fr.r(20, 50, 180, 180).collidepoint(pos):
                        play_cry(self.game, self.pid)
                    elif self.page == 2 and fr.r(316, 40, 196, 38).collidepoint(pos):
                        regions = list(dict.fromkeys(r for r, _k in self.areas))
                        if len(regions) > 1:
                            self.area_region = regions[(regions.index(self.area_region) + 1) % len(regions)]
                    elif self.page == 3 and len(self.forms) > 1:
                        step = -1 if pos[0] < fr.p(256, 0)[0] and fr.r(46, 288, 420, 80).collidepoint(pos) else 1
                        self.form_idx = (self.form_idx + step) % len(self.forms)

    def update(self):
        pass

    # ---------------------------------------------------------------- drawing
    def draw(self):
        screen = self.game.screen
        {1: self._draw_info, 2: self._draw_area, 3: self._draw_forms}[self.page](screen)
        self.game.ui_manager.draw(screen)

    def _draw_info(self, screen):
        fr = self.frame
        fr.background(screen, "bg_info")
        img = fit(self.game.assets.get_pokemon_image(self.pid, self.entry.get("form", "normal"), self.entry.get("shiny", False)),
                  int(160 * fr.k), int(160 * fr.k))
        if img is not None:
            screen.blit(img if self.owned else silhouette(img), img.get_rect(center=fr.p(104, 136)))
        fr.text(screen, f"{self.num}  {self.name}", 246, 36, 0, WHITE_T, BLACK_T, font=self.game.assets.fonts["dialog"])
        fr.text(screen, "Height", 314, 158)
        fr.text(screen, "Weight", 314, 190)
        f = self.game.assets.fonts["button"]
        if self.owned and self.info:
            own = fr.part("icon_own")
            if own:
                screen.blit(own, fr.p(210, 38))
            fr.text(screen, f"{self.info.get('kind', '?')} Pokémon", 480, 66, 1)
            fr.text(screen, f"{self.info.get('height', 0):.1f} m", 470, 158, 1)
            fr.text(screen, f"{self.info.get('weight', 0):.1f} kg", 482, 190, 1)
            for k, t in enumerate(self.types[:2]):
                fr.type_label(screen, t, 296 + 100 * k, 120)
            foot = None
            path = os.path.join(self.game.assets.assets_dir, "pokedex", "footprints", f"footprint{self.species:03d}.png")
            if os.path.isfile(path):
                try:
                    foot = pygame.image.load(path).convert_alpha()
                except pygame.error:
                    foot = None
            if foot is not None:
                screen.blit(pygame.transform.scale(foot, (int(foot.get_width() * fr.k), int(foot.get_height() * fr.k))),
                            fr.p(226, 138))
            # our words, not the games' entry: where it lives, and its habitat
            names = list(dict.fromkeys(
                (self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(k) or {}).get("route_name") or
                k.replace("_", " ").title() for _r, k in self.areas))
            lines = []
            if names:
                lines.append("Lives in: " + ", ".join(names[:4]) + (" and more." if len(names) > 4 else "."))
            else:
                lines.append("Not seen in the wild. Trade, evolve or meet it in the story!")
            extra = [s for s in (self.info.get("habitat") and f"Habitat: {self.info['habitat']}",
                                 self.info.get("color") and f"Colour: {self.info['color']}") if s]
            if extra:
                lines.append(".  ".join(extra) + ".")
            from src.ui.dialogue import wrap_text
            rows = [r for line in lines for r in wrap_text(line, f, int(432 * fr.k))][:4]
            for k, row in enumerate(rows):
                fr.text(screen, row, 40, 242 + 30 * k, font=f)
        else:
            fr.text(screen, "????? Pokémon", 480, 66, 1)
            fr.text(screen, "????.? m", 470, 158, 1)
            fr.text(screen, "????.? kg", 482, 190, 1)
            fr.text(screen, "Catch it to fill in its page!", 256, 288, 2, font=f)

    def _area_map(self, region):
        """(the map picture, {area key: (x, y) on it}) for a region: its town map, else its part of the world's."""
        from src.states.region_map import map_data
        data = map_data(self.game)
        own = data.get("region_maps", {}).get(region)
        cache = _MAPS
        if own:
            if own["file"] not in cache:
                try:
                    cache[own["file"]] = pygame.image.load(os.path.join(self.game.assets.assets_dir, own["file"])).convert()
                except (pygame.error, FileNotFoundError):
                    cache[own["file"]] = None
            return cache[own["file"]], dict(own["points"])
        box = data.get("views", {}).get(region)
        if not box:
            return None, {}
        if "world" not in cache:
            try:
                cache["world"] = pygame.image.load(os.path.join(self.game.assets.assets_dir, data["map"])).convert()
            except (pygame.error, FileNotFoundError):
                cache["world"] = None
        if cache["world"] is None:
            return None, {}
        x0, y0, x1, y1 = box
        crop = cache["world"].subsurface((x0, y0, x1 - x0, y1 - y0))
        return crop, {k: (x - x0, y - y0) for k, (x, y) in data.get("points", {}).items() if x0 <= x <= x1 and y0 <= y <= y1}

    def _spot(self, key, points):
        """Where an area is on the map: its own point, else between the towns its ways out lead to."""
        if key in points:
            return points[key]
        prog = self.game.loader.area_data.get("STORY_PROGRESSION", {})
        seen, frontier = {key}, [key]
        for _depth in range(3):
            near = []
            for k in frontier:
                a = prog.get(k) or {}
                for o in a.get("route_menu", []) + a.get("travel_options", []):
                    t = o.get("target") or o.get("target_area")
                    if t and t not in seen:
                        seen.add(t)
                        near.append(t)
            hits = [points[t] for t in near if t in points]
            if hits:
                return (sum(p[0] for p in hits) / len(hits), sum(p[1] for p in hits) / len(hits))
            frontier = near
        return None

    def _draw_area(self, screen):
        fr = self.frame
        fr.background(screen, "bg_area")
        box = fr.r(18, 50, 476, 316)
        region = self.area_region
        pic, points = self._area_map(region) if region else (None, {})
        spots = []
        if pic is not None:
            k = min(box.w / pic.get_width(), box.h / pic.get_height())
            size = (int(pic.get_width() * k), int(pic.get_height() * k))
            m = pygame.transform.smoothscale(pic, size)
            mr = m.get_rect(center=box.center)
            screen.blit(m, mr)
            for _r, key in [a for a in self.areas if a[0] == region]:
                s = self._spot(key, points)
                if s:
                    spots.append((int(mr.x + s[0] * k), int(mr.y + s[1] * k)))
            pulse = 6 + int(3 * (1 + math.sin(pygame.time.get_ticks() / 200)))
            for s in dict.fromkeys(spots):
                pygame.draw.circle(screen, (248, 64, 64), s, pulse)
                pygame.draw.circle(screen, (255, 255, 255), s, pulse, 2)
        over = fr.part("overlay_area")
        if over:
            screen.blit(over, fr.p(0, 0))
        if not spots:
            none = fr.part("overlay_areanone")
            if none:
                screen.blit(none, fr.p(108, 188))
            fr.text(screen, "Area unknown", 256, 192, 2)
        regions = list(dict.fromkeys(r for r, _k in self.areas))
        fr.text(screen, (region or "").title(), 420, 43, 2)
        if len(regions) > 1:
            arrow(screen, fr, 496, 59, 1, BASE)
        fr.text(screen, f"{self.name}'s area", 256, 350, 2)

    def _draw_forms(self, screen):
        fr = self.frame
        fr.background(screen, "bg_forms")
        mon = self._mon(self.form_idx) if self.owned else None
        if mon is not None:
            for img, (x, y) in ((mon[0], (130, 158)), (mon[1], (382, 158))):
                pic = fit(img, int(180 * fr.k), int(180 * fr.k))
                if pic is not None:
                    screen.blit(pic, pic.get_rect(center=fr.p(x, y)))
        fr.text(screen, self.name, 256, 288, 2)
        label = self.forms[self.form_idx][3] if self.owned else "?????"
        if len(self.forms) > 1 and self.owned:
            label = f"{label}  ({self.form_idx + 1}/{len(self.forms)})"
            arrow(screen, fr, 92, 336, -1, BASE)
            arrow(screen, fr, 420, 336, 1, BASE)
        fr.text(screen, label, 256, 320, 2)


class DexSearchState(GameState):
    """Journeys' search screen: tap a setting to change it; START shows what matches (seen ones)."""

    def __init__(self, game, dex):
        super().__init__(game)
        self.dex, self.frame = dex, dex.frame
        self.s = dict(dex.search) if dex.search else self.blank()

    @staticmethod
    def blank():
        return {"order": 0, "name": None, "type1": None, "type2": None, "color": None, "shape": None,
                "h": [0, len(HEIGHTS) - 1], "w": [0, len(WEIGHTS) - 1]}

    def _cycle(self, key, n):
        v = self.s[key]
        self.s[key] = 0 if v is None else (None if v + 1 >= n else v + 1)

    def fields(self):
        """(rect in 512 x 384, what a tap does)"""
        s = self.s
        return [((258, 54, 172, 26), lambda: s.__setitem__("order", (s["order"] + 1) % len(ORDERS))),
                ((120, 112, 112, 26), lambda: self._cycle("name", len(NAME_GROUPS))),
                ((388, 112, 112, 26), lambda: self._cycle("color", len(COLORS))),
                ((120, 164, 112, 26), lambda: self._cycle("type1", len(SEARCH_TYPES))),
                ((248, 164, 112, 26), lambda: self._cycle("type2", len(SEARCH_TYPES))),
                ((120, 216, 92, 26), lambda: self._step_range("h", 0)),
                ((248, 216, 92, 26), lambda: self._step_range("h", 1)),
                ((120, 268, 92, 26), lambda: self._step_range("w", 0)),
                ((248, 268, 92, 26), lambda: self._step_range("w", 1)),
                ((426, 216, 56, 52), lambda: self._cycle("shape", SHAPES)),
                ((8, 326, 144, 34), self.reset),
                ((176, 326, 160, 34), self.begin),
                ((360, 326, 144, 34), self.cancel)]

    def _step_range(self, key, end):
        """Height or weight: the low end steps up (back to 0 past the top), the high end steps down."""
        lo, hi = self.s[key]
        n = len(HEIGHTS if key == "h" else WEIGHTS)
        if end == 0:
            lo = lo + 1 if lo + 1 < hi else 0
        else:
            hi = hi - 1 if hi - 1 > lo else n - 1
        self.s[key] = [lo, hi]

    def reset(self):
        self.s = self.blank()

    def begin(self):
        self.dex.search = dict(self.s)
        self.dex.index = self.dex.top = 0
        self.dex.refresh_dex()
        self.game.change_state(self.dex)

    def cancel(self):
        self.game.change_state(self.dex)

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for rect, act in self.fields():
                    if self.frame.r(*rect).collidepoint(e.pos):
                        act()
                        break
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                self.cancel()
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    self.cancel()
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.begin()

    def update(self):
        pass

    def draw(self):
        screen, fr, s = self.game.screen, self.frame, self.s
        fr.background(screen, "bg_search")
        fr.text(screen, "Search Mode", 256, -1, 2, WHITE_T, BLACK_T)
        for label, x, y in (("Order", 136, 58), ("Name", 58, 116), ("Type", 58, 168), ("Height", 58, 220),
                            ("Weight", 58, 272), ("Color", 326, 116), ("Shape", 454, 168)):
            fr.text(screen, label, x, y, 2)
        for label, x in (("Reset", 80), ("Start", 256), ("Cancel", 432)):
            fr.text(screen, label, x, 336, 2)
        fr.text(screen, ORDERS[s["order"]], 344, 58, 2)
        fr.text(screen, "----" if s["name"] is None else NAME_GROUPS[s["name"]], 176, 116, 2)
        fr.text(screen, "----" if s["color"] is None else COLORS[s["color"]], 444, 116, 2)
        for key, x in (("type1", 128), ("type2", 256)):
            if s[key] is None:
                fr.text(screen, "----", x + 48, 168, 2)
            else:
                fr.type_label(screen, SEARCH_TYPES[s[key]], x, 166)
        for key, vals, y, col in (("h", HEIGHTS, 220, 0), ("w", WEIGHTS, 272, 32)):
            lo, hi = s[key]
            fr.text(screen, f"{vals[lo]:g}", 166, y, 2)
            fr.text(screen, f"{vals[hi]:g}" if hi < len(vals) - 1 else "any", 294, y, 2)
            unit = fr.part("icon_hw", (col, 0, 32, 44))  # (m, kg: Journeys' pictures)
            if unit:
                screen.blit(unit, fr.p(344, y - 6))
        if s["shape"] is not None:
            pic = fr.part("icon_shapes", (0, s["shape"] * 60, 60, 60))
            if pic:
                screen.blit(pic, fr.p(424, 214))
        else:
            fr.text(screen, "----", 454, 230, 2)
