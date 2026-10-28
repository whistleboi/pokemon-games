# [REF-0001: System Imports]
import pygame
import random
import os
import math
import threading
import json
import sys
from src.states.base import GameState
from src.ui.widgets import Button
from src.ui.dialogue import ClassicDialogueBox
from src.utils import Utils
from src.config import (WHITE, BLACK, GOLD, GB_PANEL_DARK, GRAY, LIGHT_GRAY,
                        GREEN, RED, GB_PANEL, GB_BORDER, GB_TEXT)
from src.pokemon.data import Pokemon


# [REF-0019: Main Menu System]
class MainMenuState(GameState):
    """The title screen (redesign): a Journeys town or route drifting behind, the logo, a
    Pokemon showcase that changes every few seconds, and NEW GAME / LOAD GAME / QUIT."""

    # Pokemon that take turns on the title screen (one from each generation's box art and more).
    SHOWCASE = (25, 6, 9, 3, 150, 249, 250, 382, 383, 384, 483, 484, 487, 643, 644, 716, 717, 791, 792,
                888, 889, 890, 1007, 1008, 149, 445, 448, 658, 724, 887)
    SHOW_MS = 4500

    def __init__(self, game):
        super().__init__(game)
        from src.ui.panels import CommandButton
        from src.ui import theme
        f = game.assets.fonts
        x, w, h, gap = 72, 380, 76, 18
        top = game.height // 2 + 10
        self.btn_new = CommandButton((x, top, w, h), "NEW GAME", f["button"], self.new_game,
                                     bg_color=theme.POKEMON, autosize=False)
        self.btn_load = CommandButton((x, top + h + gap, w, h), "LOAD GAME", f["button"], self.load_game,
                                      bg_color=theme.RUN, autosize=False)
        self.btn_quit = CommandButton((x, top + 2 * (h + gap), w, h), "QUIT", f["button"], self.quit_game,
                                      bg_color=theme.BACK, autosize=False)

        from src.core import save_slots
        has_saves = bool(os.path.exists(game.data.save_file) and game.data.data.get("story")) \
            or save_slots.any_saves(save_slots.folder(game))
        if not has_saves:  # greyed: nothing to load yet
            self.btn_load.callback = None

        self.logo_font = game.assets._load_font(96, bold=True)
        self.sub_font = game.assets._load_font(40, bold=True)
        self.backdrop = self._pick_backdrop()
        self.started = pygame.time.get_ticks() - 1500  # the first Pokemon is already in place
        self.order = list(self.SHOWCASE)
        random.shuffle(self.order)
        self._sprites = {}

    def _pick_backdrop(self):
        """A random town or route drawn from Pokemon Journeys' maps, a little larger than the
        screen so it can drift."""
        folder = os.path.join(self.game.assets.assets_dir or "", "journeys")
        files = []
        for sub in ("towns", "routes"):
            path = os.path.join(folder, sub)
            if os.path.isdir(path):
                files += [os.path.join(path, n) for n in os.listdir(path) if n.endswith(".png")]
        if not files:
            return None
        try:
            img = pygame.image.load(random.choice(files)).convert()
        except pygame.error:
            return None
        w, h = self.game.width, self.game.height
        k = max((w + 160) / img.get_width(), h / img.get_height())
        return pygame.transform.smoothscale(img, (int(img.get_width() * k), int(img.get_height() * k)))

    def _sprite(self, pid):
        if pid not in self._sprites:
            from src.states.systems import fit_sprite
            try:
                img = self.game.assets.get_pokemon_image(pid, "normal", False)
            except Exception:
                img = None
            self._sprites[pid] = fit_sprite(img, 360, 340) if img else None
        return self._sprites[pid]

    def new_game(self):
        # Pick which of the SAVE_SLOTS files the new game lives in (empty slots start at once).
        self.game.change_state(LoadState(self.game, self, mode="new"))

    def load_game(self):
        self.game.change_state(LoadState(self.game, self))

    def quit_game(self):
        pygame.quit()
        sys.exit()

    def handle_events(self, events):
        for event in events:
            self.btn_new.handle_event(event)
            self.btn_load.handle_event(event)
            self.btn_quit.handle_event(event)

    def update(self):
        pass

    def draw(self):
        import math
        from src.ui import theme
        screen = self.game.screen
        w, h = self.game.width, self.game.height
        t = pygame.time.get_ticks() - self.started

        # The world behind: drifting slowly side to side, darker toward the menu at the left.
        screen.fill((24, 40, 72))
        if self.backdrop:
            span = self.backdrop.get_width() - w
            dx = int(span * (0.5 + 0.5 * math.sin(t / 9000)))
            screen.blit(self.backdrop, (-dx, (h - self.backdrop.get_height()) // 2))
        shade = getattr(self, "_shade", None)
        if shade is None:
            shade = self._shade = pygame.Surface((w, h), pygame.SRCALPHA)
            for x in range(0, w, 4):
                a = int(150 * max(0.0, 1 - x / (w * 0.55))) + 80
                pygame.draw.rect(shade, (12, 18, 40, min(230, a)), (x, 0, 4, h))
        screen.blit(shade, (0, 0))

        # The showcase: one Pokemon at a time on a grassy patch, sliding in.
        slot = t // self.SHOW_MS
        pid = self.order[slot % len(self.order)]
        spr = self._sprite(pid)
        phase = (t % self.SHOW_MS) / self.SHOW_MS
        slide = int(80 * max(0.0, 1 - phase * 6) ** 2)
        base = (int(w * 0.74) + slide, int(h * 0.70))
        patch = pygame.Surface((300, 70), pygame.SRCALPHA)
        pygame.draw.ellipse(patch, (60, 140, 70, 200), patch.get_rect())
        pygame.draw.ellipse(patch, (130, 210, 120, 220), patch.get_rect(), 4)
        screen.blit(patch, patch.get_rect(center=base))
        if spr:
            bob = int(6 * math.sin(t / 380))
            img = spr.copy()
            img.set_alpha(int(255 * min(1.0, phase * 6)))
            screen.blit(img, img.get_rect(midbottom=(base[0], base[1] + 18 + bob)))

        # The logo: yellow letters with a deep blue edge, as on the games' boxes.
        bob = int(4 * math.sin(t / 700))
        lx, ly = 72, 70 + bob
        for dx, dy in ((6, 8),):
            Utils.draw_text_outline(screen, "POKéMATH", self.logo_font, (10, 20, 50), lx + dx, ly + dy, align="left",
                                    outline_color=(10, 20, 50), thickness=7)
        Utils.draw_text_outline(screen, "POKéMATH", self.logo_font, (255, 214, 40), lx, ly, align="left",
                                outline_color=(36, 70, 160), thickness=7)
        Utils.draw_text_outline(screen, "ADVENTURES", self.sub_font, WHITE, lx + 6, ly + 118, align="left",
                                outline_color=(36, 70, 160), thickness=5)

        for btn in (self.btn_new, self.btn_load, self.btn_quit):
            btn.draw(screen)
        hint = "Learn math, catch them all!"
        theme.shadow_text(screen, hint, self.game.assets.fonts["label"], 72, h - 40, color=(220, 226, 244),
                          shadow=(10, 16, 36))


def _pick_screen(game, accent, title, step, sprite, name_text, placeholder, arrows, next_label, hint):
    """Character / rival pick (the menu redesign): a stage card with the sprite and < > at the
    left, the name card at the right, NEXT in the text box. arrows: (left_rect, right_rect) or None;
    returns (stage, name_rect, next_rect)."""
    from src.ui import theme
    screen, f = game.screen, game.assets.fonts
    w, h = game.width, game.height
    theme.menu_background(screen, accent, title, f["button"], title_x=24)
    Utils.draw_text_outline(screen, step, f["label"], WHITE, w - 24, theme.HEADER_H // 2 - 4, align="right",
                            outline_color=theme.shade(accent, 0.45), thickness=2)
    bar = pygame.Rect(16, h - 86, w - 32, 78)
    stage = pygame.Rect(24, theme.HEADER_H + 16, 560, bar.top - 12 - theme.HEADER_H - 16)
    theme.card(screen, stage, radius=16)
    floor = pygame.Rect(0, 0, 380, 70)
    floor.center = (stage.centerx, stage.bottom - 70)
    pygame.draw.ellipse(screen, theme.shade(accent, 1.15), floor)
    pygame.draw.ellipse(screen, theme.shade(accent, 0.7), floor, 4)
    if sprite:
        from src.states.systems import fit_sprite
        img = fit_sprite(sprite, stage.w - 200, stage.h - 70)
        screen.blit(img, img.get_rect(midbottom=(stage.centerx, floor.centery + 10)))
    mouse = pygame.mouse.get_pos()
    if arrows:
        for rect, label in zip(arrows, ("<", ">")):
            theme.command_button(screen, rect, label, f["button"], accent, hover=rect.collidepoint(mouse))

    panel = pygame.Rect(stage.right + 16, stage.y, w - 24 - stage.right - 16, stage.h)
    theme.card(screen, panel, radius=16)
    theme.shadow_text(screen, "Name", f["label"], panel.x + 32, panel.y + 40, color=(110, 116, 136))
    name_rect = pygame.Rect(panel.x + 32, panel.y + 76, panel.w - 64, 70)
    theme.text_field(screen, name_rect, name_text, f["dialog"], placeholder)
    from src.ui.dialogue import wrap_text
    for k, row in enumerate(wrap_text(hint, f["label"], panel.w - 64)):
        theme.shadow_text(screen, row, f["label"], panel.x + 32, name_rect.bottom + 28 + k * 30,
                          color=(96, 102, 122))

    theme.draw_textbox(screen, bar)
    next_rect = pygame.Rect(bar.right - 18 - 240, bar.y + 10, 240, bar.h - 26)
    theme.shadow_text(screen, "Type a name, or keep the one shown.", f["s_med"], bar.x + 32,
                      bar.centery - f["s_med"].get_height() // 2 - 2)
    theme.command_button(screen, next_rect, next_label, f["button"], theme.POKEMON,
                         hover=next_rect.collidepoint(mouse))
    return stage, name_rect, next_rect


# [REF-0056: Character Selection State]
class CharacterSelectionState(GameState):
    uses_keyboard = True  # its own arrow/Enter/typing handling

    def __init__(self, game):
        super().__init__(game)
        config = game.loader.area_data.get("GAME_CONFIG", {})
        self.char_list = config.get("PLAYABLE_CHARACTERS", ["red", "blue"])
        self.starter_ids = config.get("STARTER_IDS", [1, 4, 7])

        self.selected_idx = random.randint(0, len(self.char_list) - 1)
        self.input_name = ""
        self.sprites = []

        for name in self.char_list:
            front = game.assets.get_player_image(name, back=False)
            if not front:
                front = game.assets.get_player_image(name, back=True)

            if not front:
                front = pygame.Surface((200, 200))
                front.fill(GRAY)

            h = int(game.height * 0.5)
            w = int(front.get_width() * (h / front.get_height()))
            self.sprites.append(pygame.transform.scale(front, (w, h)))

        # (the stage card is x 24-584 under the header; NEXT sits in the text box)
        mid = (84 + 16 + game.height - 98) // 2
        self.rect_left = pygame.Rect(44, mid - 40, 70, 80)
        self.rect_right = pygame.Rect(584 - 20 - 70, mid - 40, 70, 80)
        self.rect_select = pygame.Rect(game.width - 16 - 18 - 240, game.height - 86 + 10, 240, 52)

        threading.Thread(target=self.preload_starters, daemon=True).start()

    def preload_starters(self):
        self.game.preloaded_starter_data = [
            self.game.loader.fetch_specific(i) for i in self.starter_ids
        ]
        print("✓ Background loading of starters complete.")

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.rect_left.collidepoint(event.pos):
                    self.selected_idx = (
                        self.selected_idx - 1) % len(self.char_list)
                elif self.rect_right.collidepoint(event.pos):
                    self.selected_idx = (
                        self.selected_idx + 1) % len(self.char_list)
                elif self.rect_select.collidepoint(event.pos):
                    self.confirm_selection()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.input_name = self.input_name[:-1]
                elif event.key == pygame.K_RETURN:
                    self.confirm_selection()
                elif len(self.input_name) < 12 and event.unicode.isprintable():
                    self.input_name += event.unicode.upper()

    def confirm_selection(self):
        name = self.input_name.strip() or "TRAINER"
        char_key = self.char_list[self.selected_idx]

        self.game.player_name = name
        self.game.player_character = char_key

        self.game.change_state(RegionSelectionState(self.game))

    def update(self):
        pass

    def draw(self):
        from src.ui import theme
        _pick_screen(self.game, theme.ACCENT["party"], "CHOOSE YOUR TRAINER", "Step 1 of 4",
                     self.sprites[self.selected_idx], self.input_name, "TRAINER",
                     (self.rect_left, self.rect_right), "NEXT",
                     "Tap < > to pick how you look, then type your name. It's TRAINER if you don't.")


class RegionSelectionState(GameState):
    """Choose a region: where a new game begins, or (mode="move") where Mom buys the next home."""
    uses_keyboard = True  # its own arrow/Enter/typing handling

    COLS = 3
    # The side areas each region opens up later (shown on its card).
    SUB_REGIONS = {"KANTO": ("Sevii Islands",), "HOENN": ("Orre",),
                   "SINNOH": ("Hisui",), "UNOVA": ("Decolore Islands",),
                   "GALAR": ("Isle of Armor", "Crown Tundra"), "PALDEA": ("Kitakami", "Blueberry Academy")}

    def __init__(self, game, mode="new", return_state=None):
        super().__init__(game)
        self.mode = mode
        self.return_state = return_state
        story = game.story_manager
        # Travel-only regions are reached by ship, never a new game or a move.
        starts = [(r, cfg) for r, cfg in story.get_region_starts() if not cfg.get("travel_only")]
        if mode == "move":
            starts = self.new_regions(story)
        self.regions = [r for r, _ in starts] or ["KANTO"]
        self.subtitles = {r: cfg.get("subtitle", "") for r, cfg in starts}
        if mode == "move":
            for r in self.regions:
                if story.is_region_champion(r):
                    self.subtitles[r] = "CHAMPION"
                elif story.story_flags.get(f"unlocked_{r.lower()}_badges"):
                    self.subtitles[r] = "VISITED"
                else:
                    self.subtitles[r] = "NEW - " + self.subtitles[r].split(" / ")[0]
                if self._travel_only(r):
                    self.subtitles[r] = "TRAVEL THERE"
        self.selected_idx = 0
        self.bar_rect = pygame.Rect(16, game.height - 86, game.width - 32, 78)
        self.stay_rect = pygame.Rect(self.bar_rect.right - 18 - 240, self.bar_rect.y + 10, 240, self.bar_rect.h - 26)

        # Picture cards (the region's first town) in the menu frame.
        rows = (len(self.regions) + self.COLS - 1) // self.COLS
        gap = 14
        top = 84 + 16
        card_w = (game.width - 48 - gap * (self.COLS - 1)) // self.COLS
        card_h = (self.bar_rect.top - 12 - top - gap * (rows - 1)) // max(1, rows)
        grid_w = self.COLS * card_w + (self.COLS - 1) * gap
        left = (game.width - grid_w) // 2
        self._pictures = {}
        self.rects = [
            pygame.Rect(left + (i % self.COLS) * (card_w + gap),
                        top + (i // self.COLS) * (card_h + gap), card_w, card_h)
            for i in range(len(self.regions))
        ]

    @staticmethod
    def new_regions(story):
        """Where Mom can move: only regions not played yet. The goal is to work through all nine
        without repeating one (the regions you've finished keep their own save of your progress)."""
        visited = story.visited_regions()
        return [(r, cfg) for r, cfg in story.get_region_starts()
                if not cfg.get("travel_only") and r not in visited]

    def handle_events(self, events):
        n = len(self.regions)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.mode == "move" and self.stay_rect.collidepoint(event.pos):
                    self.stay()
                    return
                for i, rect in enumerate(self.rects):
                    if rect.collidepoint(event.pos):
                        self.selected_idx = i
                        self.confirm_selection()
                        return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.selected_idx = (self.selected_idx - 1) % n
                elif event.key == pygame.K_RIGHT:
                    self.selected_idx = (self.selected_idx + 1) % n
                elif event.key == pygame.K_UP:
                    self.selected_idx = (self.selected_idx - self.COLS) % n
                elif event.key == pygame.K_DOWN:
                    self.selected_idx = (self.selected_idx + self.COLS) % n
                elif event.key == pygame.K_RETURN:
                    self.confirm_selection()

    def stay(self):
        if self.return_state:
            self.game.change_state(self.return_state)
            self.return_state.show_message(["Mom: No rush! The house hunt can wait.",
                                            "Visit me at home whenever you're ready to move."])

    # Kanto and Johto are next door: you travel between them instead of moving house.
    NEIGHBOURS = {"KANTO", "JOHTO"}
    TRAVEL_LINES = {
        "JOHTO": ["Mom: Johto? Oh, that's right next door! No need to move house for that.",
                  "From the Pokemon League's Reception Gate, follow Route 26 and Route 27 east to New Bark Town.",
                  "Or take the S.S. Aqua from Vermilion City to Olivine City with your S.S. Ticket!"],
        "ORANGE": ["Mom: The Orange Islands? Then you'll need a ship!",
                   "The S.S. Anne sails from Vermilion City to Valencia Island. Board it when you're ready.",
                   "Professor Ivy will meet you there with a new partner."],
        "KANTO": ["Mom: Kanto? That's just next door! You can travel there yourself.",
                  "From New Bark Town, take Route 27 west to the Reception Gate, then Route 22 to Viridian City.",
                  "Or take the S.S. Aqua from Olivine City to Vermilion City with your S.S. Ticket!"],
    }

    def _travel_only(self, region):
        here = self.game.story_manager.get_current_region()
        if self.mode == "move" and here == "KANTO" and region == "ORANGE":
            return True  # Kanto's Champion sails there on the S.S. Anne (Jordan, 10-27)
        return self.mode == "move" and region != here and {here, region} <= self.NEIGHBOURS

    def confirm_selection(self):
        region = self.regions[self.selected_idx]
        story = self.game.story_manager
        if self.mode == "move":
            if self._travel_only(region) and self.return_state:
                self.game.change_state(self.return_state)
                self.return_state.show_message(self.TRAVEL_LINES[region])
                return
            self.game.change_state(story.move_to_region(region))
            return
        cfg = story.get_region_start(region)
        story.starting_region = region
        story.visited_region_set = {region.upper()}  # a new run starts with only its own region
        story.region_rivals = {}  # and no rivals used yet
        story.story_flags[f"unlocked_{region.lower()}_badges"] = True
        story.badges.setdefault(region, [])
        story.active_badge_region = region
        story.current_area_key = cfg.get("start_area", "PALLET_TOWN")
        story.region_stores, story.linked_regions = {}, set()  # a new run: one fresh party, PC and Bag
        story.use_region_store(region)

        self.game.change_state(RivalSelectionState(self.game))

    def update(self):
        pass

    def _picture(self, region, size):
        """The region's first town (the town backgrounds), cropped to the card's picture."""
        key = (region, size)
        if key not in self._pictures:
            story = self.game.story_manager
            area = story.get_region_start(region).get("start_area", "")
            img = (self.game.assets.get_journeys_background("towns", area)
                   or self.game.assets.get_background(f"{area.lower()}.png"))
            if img:
                k = max(size[0] / img.get_width(), size[1] / img.get_height())
                img = pygame.transform.smoothscale(img, (int(img.get_width() * k) + 1, int(img.get_height() * k) + 1))
                crop = pygame.Rect(0, 0, *size)
                crop.center = img.get_rect().center
                img = img.subsurface(crop).copy()
            self._pictures[key] = img
        return self._pictures[key]

    def draw(self):
        from src.ui import theme
        screen, f = self.game.screen, self.game.assets.fonts
        title = "WHERE SHOULD WE MOVE?" if self.mode == "move" else "WHERE WILL YOUR JOURNEY BEGIN?"
        theme.menu_background(screen, theme.ACCENT["mart"], title, f["button"], title_x=24)
        if self.mode != "move":
            Utils.draw_text_outline(screen, "Step 2 of 4", f["label"], WHITE, self.game.width - 24,
                                    theme.HEADER_H // 2 - 4, align="right",
                                    outline_color=theme.shade(theme.ACCENT["mart"], 0.45), thickness=2)
        mouse = pygame.mouse.get_pos()
        for i, rect in enumerate(self.rects):
            region = self.regions[i]
            hover = rect.collidepoint(mouse)
            sel = self.selected_idx == i
            theme.card(screen, rect, hover=hover, selected=sel or hover, accent=theme.BAG)
            pic_rect = pygame.Rect(rect.x + 8, rect.y + 8, rect.w - 16, rect.h - 68)
            pic = self._picture(region, pic_rect.size)
            if pic:
                screen.blit(pic, pic_rect)
                pygame.draw.rect(screen, theme.TEXTBOX_FRAME, pic_rect, 2)
            # its sub-regions, as chips along the bottom of the picture
            cx, cy = pic_rect.x + 6, pic_rect.bottom - 30
            for sub in self.SUB_REGIONS.get(region, ()):
                label = "+ " + sub
                chip = pygame.Rect(cx, cy, f["caption"].size(label)[0] + 16, 24)
                if chip.right > pic_rect.right - 6:  # no room: a row above
                    cx, cy = pic_rect.x + 6, cy - 28
                    chip.topleft = (cx, cy)
                back = pygame.Surface(chip.size, pygame.SRCALPHA)
                pygame.draw.rect(back, (16, 22, 44, 200), back.get_rect(), border_radius=12)
                screen.blit(back, chip)
                Utils.draw_text_outline(screen, label, f["caption"], (255, 226, 120), chip.centerx, chip.centery,
                                        outline_color=(16, 22, 44), thickness=1)
                cx = chip.right + 6
            theme.shadow_text(screen, region, f["s_med"], rect.x + 14, rect.bottom - 56)
            sub = self.subtitles.get(region, "")
            theme.shadow_text(screen, sub, f["caption"] if f["caption"].size(sub)[0] < rect.w - 24 else f["tiny"],
                              rect.x + 14, rect.bottom - 26, color=(110, 116, 136))

        theme.draw_textbox(screen, self.bar_rect)
        line = ("Where will Mom's new home be?" if self.mode == "move"
                else "Tap a region to begin your journey there.")
        theme.shadow_text(screen, line, f["s_med"], self.bar_rect.x + 32,
                          self.bar_rect.centery - f["s_med"].get_height() // 2 - 2)
        if self.mode == "move":
            theme.command_button(screen, self.stay_rect, "STAY HERE", f["button"], theme.BACK,
                                 hover=self.stay_rect.collidepoint(mouse))


# [REF-0057: Rival Selection State]
class RivalSelectionState(GameState):
    """Each region's own rival (Jordan): Blue in Kanto, Silver in Johto, May or Brendan, Barry,
    Cheren or Bianca, Serena or Calem, Hau, Hop, Nemona. Pick one where the game had two, then
    name them (the canon name until you type another). Kalos and Alola then name a second friend
    (Shauna, Gladion). A new game continues to the math level; a region you move to runs on_done."""
    uses_keyboard = True  # its own arrow/Enter/typing handling

    def __init__(self, game, region=None, on_done=None):
        super().__init__(game)
        story = game.story_manager
        self.region = (region or story.starting_region or "KANTO").upper()
        self.on_done = on_done
        self.options = story.rival_options(self.region) or [("RIVAL", "rival")]
        self.friend = story.RIVAL_CHOICES.get(self.region, {}).get("friend")
        self.step = "rival"
        self.selected_idx = 0
        self.input_name = ""
        self.rival_name = None
        self.sprites = [self._sprite(key) for _, key in self.options]
        self.friend_sprite = None

        mid = (84 + 16 + game.height - 98) // 2
        self.rect_left = pygame.Rect(44, mid - 40, 70, 80)
        self.rect_right = pygame.Rect(584 - 20 - 70, mid - 40, 70, 80)
        self.rect_select = pygame.Rect(game.width - 16 - 18 - 240, game.height - 86 + 10, 240, 52)

    def _sprite(self, key):
        img = self.game.assets.get_trainer_image(f"{key}.png") or self.game.assets.get_player_image(key)
        if not img:
            img = pygame.Surface((200, 200))
            img.fill(GRAY)
        h = int(self.game.height * 0.42)
        return pygame.transform.scale(img, (int(img.get_width() * h / img.get_height()), h))

    @property
    def char_list(self):  # (older callers)
        return [key for _, key in self.options]

    def default_name(self):
        if self.step == "friend":
            return self._friend()[0]
        return self.options[self.selected_idx][0]

    def _friend(self):
        return self.game.story_manager.default_friend(self.region, self.options[self.selected_idx][1])

    def _move(self, d):
        if self.step == "rival" and len(self.options) > 1:
            self.selected_idx = (self.selected_idx + d) % len(self.options)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.rect_left.collidepoint(event.pos):
                    self._move(-1)
                elif self.rect_right.collidepoint(event.pos):
                    self._move(1)
                elif self.rect_select.collidepoint(event.pos):
                    self.confirm_selection()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.input_name = self.input_name[:-1]
                elif event.key == pygame.K_RETURN:
                    self.confirm_selection()
                elif event.key == pygame.K_LEFT:
                    self._move(-1)
                elif event.key == pygame.K_RIGHT:
                    self._move(1)
                elif len(self.input_name) < 12 and event.unicode.isprintable():
                    self.input_name += event.unicode.upper()

    def confirm_selection(self):
        name = self.input_name.strip() or self.default_name()
        if self.step == "rival" and self.friend:
            self.rival_name = name  # then the second friend (Shauna, Gladion; Unova: the other one)
            self.step = "friend"
            self.input_name = ""
            self.friend_sprite = self._sprite(self._friend()[1])
            return
        if self.step == "rival":
            self.rival_name, friend_name = name, None
        else:
            friend_name = name
        self.finish(self.rival_name, friend_name)

    def finish(self, rival_name, friend_name=None):
        story = self.game.story_manager
        char_key = self.options[self.selected_idx][1]
        story.record_region_rival(self.region, rival_name, char_key, friend_name=friend_name)
        self.game.rival_name, self.game.rival_character = rival_name, char_key
        self.game.rival_true_name = rival_name.upper()
        if story.get_current_region() == self.region:
            story.sync_rival()
        if self.on_done:
            self.on_done()
            return
        region = self.region
        starter_ids = story.get_region_start(region).get("starters", [1, 4, 7])
        # Pick math difficulty before the starter (the starter pick has math)
        self.game.change_state(
            DifficultySelectionState(
                self.game,
                on_confirm=lambda: self.game.change_state(
                    region_opening_state(self.game, region) or StarterSelectionState(
                        self.game,
                        starter_ids=starter_ids,
                        region=region
                    )
                ),
                on_back=lambda: self.game.change_state(RivalSelectionState(self.game)),
            )
        )

    def update(self):
        pass

    def draw(self):
        from src.ui import theme
        friend = self.step == "friend"
        title = "NAME YOUR FRIEND" if friend else ("CHOOSE YOUR RIVAL" if len(self.options) > 1 else "YOUR RIVAL")
        sprite = self.friend_sprite if friend else self.sprites[self.selected_idx]
        arrows = (self.rect_left, self.rect_right) if not friend and len(self.options) > 1 else None
        label = "NEXT" if (not friend and self.friend) else "SELECT"
        who = "your friend" if friend else "your rival"
        hint = (f"{self.region.title()}: " + ("Tap < > to pick " + who + ", then " if arrows else "")
                + f"type a name for {who}, or keep the one shown.")
        _pick_screen(self.game, theme.ACCENT["journal"], title, f"{self.region.title()}  -  Step 3 of 4",
                     sprite, self.input_name, self.default_name(), arrows, label, hint)


def region_opening_state(game, region):
    """A new game in a region whose starter comes from the story (Hoenn's route, Oak in Kanto):
    the story choice, then home, where the opening plays out. None for regions that start at the
    starter screen."""
    story = game.story_manager
    if not story.starter_in_overworld(region):
        return None
    from src.states.overworld import AreaTransitionState
    from src.world import hoenn
    cfg = story.get_region_start(region)
    story.game_started = True
    story.current_area_key = cfg.get("start_area")
    key = cfg.get("opening_text") or cfg.get("newgame_text")
    text = game.assets.get_text(key, player_name=game.player_name,
                                rival_name=getattr(game, "rival_name", "???")) if key else []
    arrive = lambda: AreaTransitionState(game, cfg.get("start_area"),
                                         initial_message=text if isinstance(text, list) else [text])
    if hoenn.needs_choice(story):  # Omega Ruby or Alpha Sapphire comes first
        from src.states.hoenn import HoennVersionState
        return HoennVersionState(game, arrive)
    return arrive()


# [REF-0021: Starter Selection]
class StarterSelectionState(GameState):
    def __init__(self, game, starter_ids=None, region="KANTO", on_route=False):
        super().__init__(game)
        self.region = region
        # Hoenn: picked from Birch's bag on Route 101, then straight into the Poochyena battle.
        self.on_route = on_route

        config = game.loader.area_data.get("GAME_CONFIG", {})
        default_starters = config.get("STARTER_IDS", [1, 4, 7])
        self.starter_ids = starter_ids if starter_ids else default_starters

        self.starters_raw = []
        self.starters = []
        self.selected_idx = -1
        self.questions_needed = 2
        self.questions_correct = 0
        self.problem_str, self.correct_ans, self.options = "", "", []
        self.answer_btn_rects = [pygame.Rect(0, 0, 0, 0) for _ in range(3)]
        self.feedback_text = ""
        self.feedback_timer = 0
        self.selection_complete = False
        self.math_buttons_ready = False

        self.region_cfg = self.game.story_manager.get_region_start(self.region)
        background_raw = None
        for bg_name in (self.region_cfg.get("starter_bg"),
                        f"starter_{self.region.lower()}.png", "starter_bg.png"):
            background_raw = self.game.assets.get_background(bg_name)
            if background_raw:
                break
        if background_raw:
            self.background = pygame.transform.scale(
                background_raw, (self.game.width, self.game.height)
            )
        else:
            self.background = None

        self.player_back_sprite = None
        char_key = getattr(self.game, "player_character", "red")
        img = self.game.assets.get_player_image(char_key, back=True)
        if img:
            h = int(self.game.height * 0.45)
            w = int(img.get_width() * (h / img.get_height()))
            self.player_back_sprite = pygame.transform.scale(img, (w, h))

        box_height = int(self.game.height * 0.25)
        main_rect = pygame.Rect(
            0, self.game.height - box_height, self.game.width, box_height
        )
        self.dialogue_box = ClassicDialogueBox(
            main_rect,
            self.game.assets.get_text("loading_starters"),
            self.game.assets.fonts["med"],
        )

        threading.Thread(target=self.load_starters, daemon=True).start()

    def start(self):
        pass

    def load_starters(self):
        if (
            self.region == "KANTO"
            and hasattr(self.game, "preloaded_starter_data")
            and self.game.preloaded_starter_data
        ):
            self.starters_raw = self.game.preloaded_starter_data
        else:
            self.starters_raw = [
                self.game.loader.fetch_specific(i)
                for i in self.starter_ids
            ]
        self.starters = [
            Pokemon(p, self.game.assets, size_mult=2)
            for p in self.starters_raw
        ]
        lines = self._fresh_start_lines()
        for key in (("intro_text",) if self.on_route else ("newgame_text", "intro_text")):
            lines += self._region_lines(key)
        lines.append(self.game.assets.get_text("choose_partner"))
        self.dialogue_box.reset(lines)

    PROFESSORS = {"KANTO": "Professor Oak", "JOHTO": "Professor Elm"}

    def _fresh_start_lines(self):
        """A new region after another one: the old team waits at home, the challenge starts over."""
        story = self.game.story_manager
        came = story.story_flags.pop("came_from_region", None)
        if not came or came.upper() == self.region:
            return []
        prof = self.region_cfg.get("professor") or self.PROFESSORS.get(self.region, "Professor")
        return [f"{prof}: Welcome to {self.region.title()}! Your Pokemon from {came.title()} are safe at home in its PC.",
                f"{prof}: Your challenge starts over here, with a new partner. Let's pick one!"]

    def _region_lines(self, cfg_key):
        """Region text from REGION_START, with player/rival names filled in."""
        key = self.region_cfg.get(cfg_key)
        if not key:
            return []
        text = self.game.assets.get_text(
            key, player_name=self.game.player_name,
            rival_name=getattr(self.game, "rival_name", "???"),
            friend_name=getattr(self.game, "friend_name", None) or "???")
        return text if isinstance(text, list) else [text]

    @property
    def uses_town_rival(self):
        """Hoenn onward: the rival battle fires in the starting town, not here."""
        return self.region not in ("KANTO", "JOHTO")

    def generate_math_set(self):
        # Starter pick uses the difficulty chosen on the previous screen
        level = self.game.story_manager.get_math_level()
        return self.game.math.generate(level, num_options=3)

    def update_answer_buttons(self):
        self.math_buttons_ready = True
        box_rect = self.dialogue_box.rect
        # The battle's math layout: the question at the left of the text box, the three answers as
        # white cards at the right.
        right = pygame.Rect(box_rect.x + int(box_rect.w * 0.46), box_rect.y, int(box_rect.w * 0.54), box_rect.h)
        pad, gap = 22, 14
        btn_w = (right.w - pad * 2 - gap * 2) // 3
        btn_h = box_rect.h - pad * 2 - 6
        for i in range(3):
            self.answer_btn_rects[i] = pygame.Rect(right.x + pad + i * (btn_w + gap), right.y + pad, btn_w, btn_h)

    def handle_events(self, events):
        if not self.starters:
            return

        for event in events:
            buttons_handled = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.math_buttons_ready and not self.selection_complete:
                    for i, rect in enumerate(self.answer_btn_rects):
                        if rect.width > 0 and rect.collidepoint(event.pos):
                            buttons_handled = True
                            if self.options[i] == self.correct_ans:
                                self.questions_correct += 1
                                self.feedback_text = self.game.assets.get_text(
                                    "correct"
                                )
                                self.feedback_timer = 45
                                if (
                                    self.questions_correct
                                    >= self.questions_needed
                                ):
                                    self.complete_selection()
                                else:
                                    (
                                        self.problem_str,
                                        self.correct_ans,
                                        self.options,
                                    ) = self.generate_math_set()
                                    self.update_answer_buttons()
                            else:
                                self.feedback_text = self.game.assets.get_text(
                                    "try_again"
                                )
                                self.feedback_timer = 45
                                (
                                    self.problem_str,
                                    self.correct_ans,
                                    self.options,
                                ) = self.generate_math_set()
                                self.update_answer_buttons()
                            break

            if buttons_handled:
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.selected_idx == -1:
                    clicked_idx = -1
                    for i, p in enumerate(self.starters):
                        hover_y = (
                            math.sin(
                                pygame.time.get_ticks() * p.bob_speed
                                + p.bob_offset
                            )
                            * p.bob_amount
                        )
                        base_pos = self.get_pos(i)
                        draw_pos = (base_pos[0], base_pos[1] + hover_y)

                        full_rect = p.image.get_rect(center=draw_pos)
                        hitbox = full_rect.inflate(
                            -full_rect.width * 0.4, -full_rect.height * 0.4
                        )

                        if hitbox.collidepoint(event.pos):
                            clicked_idx = i

                    if clicked_idx != -1:
                        self.dialogue_box.reset("")
                        self.selected_idx = clicked_idx
                        self.problem_str, self.correct_ans, self.options = (
                            self.generate_math_set()
                        )
                        self.update_answer_buttons()

            self.dialogue_box.handle_event(event)

    def complete_selection(self):
        chosen_pokemon_obj = self.starters[self.selected_idx]
        if chosen_pokemon_obj.cry:
            chosen_pokemon_obj.cry.play()

        msg_text = self.game.assets.get_text(
            "chosen_starter", name=chosen_pokemon_obj.name
        )

        team = self.game.story_manager.player_team
        pc = self.game.story_manager.pc_pokemon

        if len(team) >= 6:
            moved_pkmn = team.pop(5)
            self.game.story_manager.deposit_to_pc(moved_pkmn)
            pc_msg = (
                f"{moved_pkmn.display_name.upper()} was sent to BILL'S PC!"
            )
            msg_text = [msg_text, pc_msg]

        team.insert(0, chosen_pokemon_obj)

        self.game.data.add_pokemon(chosen_pokemon_obj)
        self.game.data.save()

        story = self.game.story_manager
        r = self.region.lower()
        story.story_flags[f"received_starter_{r}"] = True
        story.story_flags[f"has_{r}_starter"] = True
        story.story_flags[f"starter_{r}"] = chosen_pokemon_obj.id

        if self.on_route:  # the Poke Balls come later, with the Pokedex
            msg_text = (msg_text if isinstance(msg_text, list) else [msg_text])
            msg_text += self._region_lines("starter_text")
            story.story_flags[f"{r}_rescue_started"] = True
        elif self.uses_town_rival:
            msg_text = (msg_text if isinstance(msg_text, list) else [msg_text])
            msg_text += self._region_lines("starter_text")
            story.balls_left = max(story.balls_left, 5)
        elif self.region == "JOHTO":
            rival_map = {0: 1, 1: 2, 2: 0}
            s_idx = self.selected_idx
            rival_idx_in_list = rival_map.get(s_idx, 0)
            rival_starter = self.starters_raw[rival_idx_in_list]
            self.game.story_manager.rival_starter_raw = rival_starter

            all_indices = {0, 1, 2}
            taken = {self.selected_idx, rival_idx_in_list}
            remaining = list(all_indices - taken)[0]
            user_rival_starter = self.starters_raw[remaining]
            self.game.story_manager.user_rival_starter_raw = (
                user_rival_starter
            )
        else:
            player_primary_type = (
                chosen_pokemon_obj.types[0]
                if chosen_pokemon_obj.types
                else "NORMAL"
            )
            advantage_map = {
                "GRASS": "FIRE",
                "FIRE": "WATER",
                "WATER": "GRASS"
            }
            rival_type_advantage = advantage_map.get(player_primary_type)

            rival_choice = None
            remaining_starters = [
                p_raw for i, p_raw in enumerate(self.starters_raw)
                if i != self.selected_idx
            ]
            if rival_type_advantage:
                for starter in remaining_starters:
                    if rival_type_advantage in starter.get("types", []):
                        rival_choice = starter
                        break
            if not rival_choice:
                rival_choice = random.choice(remaining_starters)

            self.game.story_manager.rival_starter_raw = rival_choice

        story.note_rival_starter(self.region)
        if not story.game_started:
            story.game_started = True
            story.current_area_key = self.region_cfg.get(
                "start_area", "PALLET_TOWN")

        self.selection_complete = True
        self.dialogue_box.reset(msg_text)
        self.dialogue_box.callback = self.start_rival_battle

    def start_rival_battle(self):
        if self.on_route:  # back onto the route, where the wild Pokemon is still waiting
            from src.states.overworld import AreaTransitionState
            self.game.change_state(AreaTransitionState(self.game, self.game.story_manager.current_area_key))
            return
        if self.uses_town_rival:
            from src.states.overworld import AreaTransitionState
            self.game.change_state(AreaTransitionState(
                self.game, self.region_cfg.get("start_area")))
            return

        if self.region == "JOHTO":
            self.game.story_manager.story_flags["johto_rival_met_in_lab"] = True
            from src.states.overworld import AreaTransitionState
            self.game.change_state(AreaTransitionState(self.game, "NEW_BARK_TOWN"))
            return

        from src.states.battle import TrainerBattleState, TrainerIntroState
        rival_pokemon = Pokemon(
            self.game.story_manager.rival_starter_raw,
            self.game.assets,
            size_mult=2
        )

        if self.region == "JOHTO": # This block is now effectively Kanto-only
            rival_name = getattr(self.game, "rival_name", "???") # [FIX] Use game.rival_name
            trainer_class = "RIVAL"
            rival_sprite = self.game.assets.get_trainer_image("silver.png")
            if not rival_sprite:
                rival_sprite = self.game.assets.get_trainer_image("rival.png")
            bg_name = "battle_elmlab.png"
        else:
            rival_sprite_key = getattr(self.game, "rival_character", "blue")
            rival_name = getattr(self.game, "rival_name", "BLUE")
            trainer_class = "RIVAL"
            bg_name = "battle_oaklab.png"

            from src.states.overworld import rival_image
            rival_sprite = (rival_image(self.game, rival_sprite_key)
                            or self.game.assets.get_trainer_image("rival.png"))

        area_name = (
            "NEW_BARK_TOWN" if self.region == "JOHTO"
            else "PALLET_TOWN"
        )
        battle_state = TrainerBattleState(
            self.game,
            rival_pokemon,
            trainer_sprite=rival_sprite,
            trainer_class=trainer_class,
            trainer_name=rival_name,
            area_name=area_name,
            battle_type="rival",
            starter_battle=True,
        )

        lab_bg = self.game.assets.get_background(bg_name) or self.game.assets.get_generic_background("lab")
        if lab_bg:
            box_top = Utils.get_full_dialogue_rect(self.game).top - 8
            scaled_bg = pygame.transform.scale(
                lab_bg, (self.game.width, box_top)
            )
            battle_state.background = scaled_bg

        all_dialogue = self.game.loader.area_data.get(
            "TRAINER_CLASS_DIALOGUE", {}
        )
        intro_text_options = all_dialogue.get(
            trainer_class, {}
        ).get("intro", ["Let's battle!"])

        if self.region == "JOHTO":
            intro_text_options = ["...You think you're strong?"]

        dialogue = random.choice(intro_text_options)
        intro_state = TrainerIntroState(
            self.game, rival_sprite, dialogue, battle_state
        )

        self.game.change_state(intro_state)

    def update(self):
        self.dialogue_box.update()
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

    def get_pos(self, i):
        return (
            self.game.width * 0.75 + (i - 1) * (self.game.width // 9),
            self.game.height * 0.35,
        )

    def draw(self):
        if self.background:
            self.game.screen.blit(self.background, (0, 0))
        else:
            self.game.screen.fill(BLACK)

        self.dialogue_box.draw(self.game.screen)

        if not self.starters:
            return

        if self.selection_complete:
            return

        if self.player_back_sprite:
            sprite_rect = self.player_back_sprite.get_rect(
                midbottom=(self.game.width * 0.25, self.dialogue_box.rect.top)
            )
            self.game.screen.blit(self.player_back_sprite, sprite_rect)

        for i, p in enumerate(self.starters):
            pos = self.get_pos(i)
            if self.selected_idx != -1 and i != self.selected_idx:
                p.image.set_alpha(100)
            else:
                p.image.set_alpha(255)

            hover_y = (
                math.sin(pygame.time.get_ticks() * p.bob_speed + p.bob_offset)
                * p.bob_amount
            )
            draw_pos = (pos[0], pos[1] + hover_y)
            self.game.screen.blit(p.image, p.image.get_rect(center=draw_pos))

            if self.game.debug_mode:
                full_rect = p.image.get_rect(center=draw_pos)
                hitbox = full_rect.inflate(
                    -full_rect.width * 0.4, -full_rect.height * 0.4
                )
                pygame.draw.rect(self.game.screen, RED, hitbox, 2)

        if (
            self.selected_idx != -1
            and self.questions_correct < self.questions_needed
        ):
            msg = self.game.assets.get_text(
                "starter_befriend",
                n=self.questions_needed,
                name=self.starters[self.selected_idx].name,
            )
            if "Answer" in msg and len(msg) > 30:
                starter_name = self.starters[self.selected_idx].name
                msg = (
                    f"Answer {self.questions_needed} Qs to "
                    f"befriend {starter_name}!"
                )

            from src.ui import theme
            screen, fonts, box = self.game.screen, self.game.assets.fonts, self.dialogue_box.rect
            theme.draw_textbox(screen, box)
            card = pygame.Rect(box.x + 16, box.y + 16, int(box.w * 0.46) - 16, box.h - 32)
            pygame.draw.rect(screen, (236, 242, 252), card, border_radius=14)
            pygame.draw.rect(screen, theme.TEXTBOX_ACCENT, card, 3, border_radius=14)
            theme.shadow_text(screen, msg, fonts["label"] if fonts["label"].size(msg)[0] < card.w - 30 else fonts["caption"],
                              card.centerx, card.y + 28, color=(96, 102, 122), align="center")
            theme.shadow_text(screen, self.problem_str, fonts["big"], card.centerx, card.centery + 16, align="center")
            if self.answer_btn_rects[0].w == 0:
                self.update_answer_buttons()
            mouse = pygame.mouse.get_pos()
            for i in range(3):
                btn_rect = self.answer_btn_rects[i]
                txt = str(self.options[i])
                theme.card(screen, btn_rect, hover=btn_rect.collidepoint(mouse), accent=theme.RUN, radius=14)
                theme.shadow_text(screen, txt, fonts["num"], btn_rect.centerx, btn_rect.centery, align="center")

        if self.feedback_timer > 0:
            Utils.draw_text_outline(
                self.game.screen,
                self.feedback_text,
                self.game.assets.fonts["s_med"],
                GOLD,
                self.game.width // 2,
                self.game.height * 0.5,
            )


# [REF-0033: Load Game State]
class LoadState(GameState):
    """Slot screen for LOAD GAME (mode="load") and for picking the file of a NEW GAME (mode="new").
    Pages through all SAVE_SLOTS slots (see src.ui.slot_list), with a YES/NO confirmation."""
    uses_keyboard = True  # its own arrow/Page/Enter handling (all of it also works by tap)

    def __init__(self, game, previous_state, mode="load"):
        super().__init__(game)
        from src.ui.slot_list import SlotList
        from src.core import save_slots
        self.previous_state = previous_state
        self.mode = mode
        self.phase = "SELECT"
        self.selected_slot_index = -1
        if mode == "new":  # a new game starts on the first free file
            current = save_slots.first_empty(save_slots.folder(game)) or 0
        else:
            current = save_slots.slot_index(game.data.save_file) or 0
        self.slot_list = SlotList(game, self.pick, selected=current)
        if mode == "load" and current == 0 and save_slots.used_slots(save_slots.folder(game)):
            self.slot_list.select(min(save_slots.used_slots(save_slots.folder(game))))

        from src.ui.panels import CommandButton
        from src.ui import theme
        f = game.assets.fonts
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.go_back, bg_color=theme.BACK,
                                      autosize=False)
        # YES / NO: a card over the list ("Load this file?").
        self.confirm_lines = (["Load this file?", "Unsaved progress will be lost."] if mode == "load"
                              else ["Start a new game here?", "The game in this file will be replaced."])
        self.confirm_dialogue = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(game), self.confirm_lines, game.assets.fonts["med"]
        )
        cx, cy = game.width // 2, game.height // 2
        self.confirm_rect = pygame.Rect(cx - 330, cy - 150, 660, 300)
        self.btn_yes = CommandButton((cx - 230, cy + 50, 210, 64), "YES", f["button"], self._yes,
                                     bg_color=theme.POKEMON, autosize=False)
        self.btn_no = CommandButton((cx + 20, cy + 50, 210, 64), "NO", f["button"], self.cancel_load,
                                    bg_color=theme.BACK, autosize=False)
        # DELETE (Load screen only): the next file picked is deleted, after a YES / NO.
        self.delete_mode = False
        self.btn_delete = CommandButton((game.width - 196, 14, 180, 56), "DELETE", f["button"],
                                        self.toggle_delete, bg_color=theme.FIGHT, autosize=False)

    @property
    def save_slots(self):
        """Summaries of every slot (None = empty). Reads only the slots that have files."""
        return [self.slot_list.summary(i) for i in range(self.slot_list.count)]

    def get_slot_text(self, i):
        slot = self.slot_list.summary(i)
        if not slot:
            return "EMPTY"
        if slot.get("damaged"):
            return "DAMAGED FILE (can't be loaded)"
        text = f"{slot['name']} - {slot['area']}"
        return text + " (from backup)" if slot.get("restored") else text

    def go_back(self):
        self.game.change_state(self.previous_state)

    def toggle_delete(self):
        from src.ui import theme
        self.delete_mode = not self.delete_mode
        self.btn_delete.text = "CANCEL" if self.delete_mode else "DELETE"
        self.btn_delete.bg_color = theme.BACK if self.delete_mode else theme.FIGHT

    def _yes(self):
        if self.delete_mode:
            self.do_delete()
        elif self.mode == "load":
            self.do_load()
        else:
            self.do_new()

    def do_delete(self):
        from src.core import save_slots
        save_slots.delete(save_slots.folder(self.game), self.selected_slot_index)
        self.toggle_delete()  # one file per DELETE press, so a stray tap can't clear several
        self.cancel_load()

    def pick(self, i):
        slot = self.slot_list.summary(i)
        if self.delete_mode:
            if slot is not None:  # damaged files can be deleted too
                self.selected_slot_index = i
                self._ask()
            return
        if self.mode == "new":
            self.selected_slot_index = i
            if slot is None:
                self.do_new()
            else:
                self._ask()
        else:
            self.confirm_load(i)

    def _ask(self):
        self.phase = "CONFIRM"
        self.game.ui_manager.elements.clear()
        self.game.ui_manager.add_element(self.btn_yes)
        self.game.ui_manager.add_element(self.btn_no)

    def confirm_load(self, i):
        slot = self.slot_list.summary(i)
        if slot and not slot.get("damaged"):
            self.selected_slot_index = i
            self._ask()

    def do_load(self):
        slot_data = self.slot_list.summary(self.selected_slot_index)
        self.game.data.save_file = slot_data["file"]

        self.game.data.data = self.game.data._load()

        if self.game.load_game_data():
            pass
        else:
            self.game.show_dialogue(["Error loading save file."])
            self.cancel_load()

    def do_new(self):
        from src.core import save_slots
        path = save_slots.slot_path(save_slots.folder(self.game), self.selected_slot_index)
        self.game.data.save_file = path
        save_slots.forget(path)
        self.game.start_new_game()

    def cancel_load(self):
        self.phase = "SELECT"
        self.start()

    def start(self):
        self.game.ui_manager.elements.clear()
        self.slot_list.refresh()
        for btn in self.slot_list.buttons():
            self.game.ui_manager.add_element(btn)
        self.game.ui_manager.add_element(self.btn_back)
        if self.mode == "load":
            self.game.ui_manager.add_element(self.btn_delete)

    def handle_events(self, events):
        if self.phase != "SELECT":
            return
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.go_back()
                return
            self.slot_list.handle(event)
            if self.phase != "SELECT" or self.game.current_state is not self:
                return

    def update(self):
        if self.phase == "CONFIRM":
            self.confirm_dialogue.update()

    def draw(self):
        """The menu frame: the files as cards, PREV / NEXT in the text box; YES / NO on a card."""
        from src.ui import theme
        screen, f = self.game.screen, self.game.assets.fonts
        title = ("DELETE - PICK A FILE" if self.delete_mode else
                 "LOAD GAME" if self.mode == "load" else "NEW GAME - PICK A FILE")
        theme.menu_background(screen, theme.ACCENT["mart"] if self.mode == "load" else theme.ACCENT["party"],
                              title, f["button"], title_x=176)
        self.slot_list.draw(screen)
        if self.phase == "SELECT":
            self.game.ui_manager.draw(screen)
            return
        # CONFIRM: the file asked about, on a card over the dimmed list.
        dim = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        screen.blit(dim, (0, 0))
        q = self.confirm_rect
        theme.card(screen, q, selected=True, accent=theme.RUN, radius=16)
        slot = self.slot_list.summary(self.selected_slot_index) if self.selected_slot_index >= 0 else None
        head = f"No.{self.selected_slot_index + 1:03d}" + (f"  {slot['name']}" if slot else "")
        theme.shadow_text(screen, head, f["button"], q.centerx, q.y + 44, align="center")
        lines = ["Delete this file?", "This can't be undone."] if self.delete_mode else self.confirm_lines
        for k, line in enumerate(lines):
            theme.shadow_text(screen, line, f["s_med"] if k == 0 else f["label"], q.centerx, q.y + 100 + k * 38,
                              color=theme.TEXT if k == 0 else (110, 116, 136), align="center")
        self.btn_yes.draw(screen)
        self.btn_no.draw(screen)


# [REF-0037: Save Game State]
class SaveState(GameState):
    uses_keyboard = True  # its own arrow/Enter/typing handling

    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state

        from src.core import save_slots
        from src.ui.slot_list import slot_font
        slot = save_slots.slot_index(self.game.data.save_file)
        if slot is None:  # not playing from a numbered file yet: offer the first free one
            slot = save_slots.first_empty(save_slots.folder(game))
        self.selected_slot = slot or 0
        self.slot_list = None  # the paged slot picker, while choosing a different file

        self.input_text = self.game.data.data.get("save_name", f"File {
            self.selected_slot + 1}")
        self.input_active = True

        from src.ui.panels import CommandButton
        from src.ui import theme
        f = game.assets.fonts
        cx = game.width // 2
        # The menu frame: a card with the file and the name box, SAVE / CANCEL under it.
        self.card_rect = pygame.Rect(cx - 380, theme.HEADER_H + 60, 760, 400)
        c = self.card_rect
        self.name_rect = pygame.Rect(c.x + 40, c.y + 200, c.w - 80, 64)
        self.btn_cancel_input = CommandButton((cx - 230, c.bottom - 86, 210, 64), "CANCEL", f["button"],
                                              self.cancel_input, bg_color=theme.BACK, autosize=False)
        self.btn_save = CommandButton((cx + 20, c.bottom - 86, 210, 64), "SAVE", f["button"],
                                      lambda: self.save_to_slot(self.selected_slot, self.input_text),
                                      bg_color=theme.POKEMON, autosize=False)
        self.btn_slot = CommandButton((c.x + 40, c.y + 80, c.w - 80, 60), self.slot_label(), f["label"],
                                      self.open_slots, bg_color=theme.RUN, autosize=False)
        self.btn_slots_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.close_slots,
                                            bg_color=theme.BACK, autosize=False)

    def slot_label(self):
        from src.core import save_slots
        from src.ui.slot_list import slot_font, fit
        info = save_slots.summary(save_slots.folder(self.game), self.selected_slot)
        what = "EMPTY" if info is None else ("DAMAGED" if info.get("damaged") else "REPLACES " + info["name"])
        head = f"No.{self.selected_slot + 1:03d} "
        font = self.game.assets.fonts["label"]
        return head + fit(font, what, 640 - font.size(head + " - CHANGE")[0]) + " - CHANGE"

    def open_slots(self):
        from src.ui.slot_list import SlotList
        self.input_active = False
        self.slot_list = SlotList(self.game, self.pick_slot, selected=self.selected_slot)
        self.game.ui_manager.elements.clear()
        for btn in self.slot_list.buttons() + [self.btn_slots_back]:
            self.game.ui_manager.add_element(btn)

    def pick_slot(self, i):
        if self.input_text == "File " + str(self.selected_slot + 1):  # untouched default name
            self.input_text = "File " + str(i + 1)
        self.selected_slot = i
        self.close_slots()

    def close_slots(self):
        self.slot_list = None
        self.input_active = True
        self.btn_slot.text = self.slot_label()
        self.game.ui_manager.elements.clear()
        self.start()

    def cancel_input(self):
        self.go_back()

    def go_back(self):
        self.game.change_state(self.previous_state)

    def save_to_slot(self, slot_index, save_name):
        self.game.update_save_data()
        self.game.data.data["save_name"] = save_name
        self.game.data.data["save_area"] = (
            self.game.story_manager.current_area_key.replace("_", " ").title()
        )

        original_save_file = self.game.data.save_file
        from src.core import save_slots
        self.game.data.save_file = save_slots.slot_path(save_slots.folder(self.game), slot_index)
        self.game.data.save()
        self.game.data.save_file = original_save_file
        self.go_back()

    def start(self):
        self.game.ui_manager.add_element(self.btn_slot)
        self.game.ui_manager.add_element(self.btn_cancel_input)
        self.game.ui_manager.add_element(self.btn_save)

    def handle_events(self, events):
        if self.slot_list is not None:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.close_slots()
                    return
                self.slot_list.handle(event)
                if self.slot_list is None:
                    return
            return
        if not self.input_active:
            return
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.save_to_slot(self.selected_slot, self.input_text)
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.cancel_input()
                elif len(self.input_text) < 20:
                    self.input_text += event.unicode

    def update(self):
        pass

    def draw(self):
        from src.ui import theme
        screen, f = self.game.screen, self.game.assets.fonts
        accent = theme.ACCENT["party"]
        if self.slot_list is not None:
            theme.menu_background(screen, accent, "SAVE GAME - PICK A FILE", f["button"], title_x=176)
            self.slot_list.draw(screen)
            self.game.ui_manager.draw(screen)
            return
        theme.menu_background(screen, accent, "SAVE GAME", f["button"], title_x=24)
        c = self.card_rect
        theme.card(screen, c, radius=16)
        theme.shadow_text(screen, "File", f["label"], c.x + 40, c.y + 44, color=(110, 116, 136))
        theme.shadow_text(screen, "Save name", f["label"], c.x + 40, self.name_rect.y - 34, color=(110, 116, 136))
        theme.text_field(screen, self.name_rect, self.input_text, f["s_med"], focused=self.input_active)
        self.game.ui_manager.draw(screen)
        theme.shadow_text(screen, "Type a name, then SAVE (or press Enter).", f["label"], c.centerx, c.bottom + 24,
                          color=(220, 226, 244), shadow=theme.MENU_BG, align="center")


# [REF-0028: Loading State]
class LoadingState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.angle = 0
        self.ball_img = game.assets.ball_imgs[0]
        self.ball_img = pygame.transform.scale(self.ball_img, (150, 150))

    def handle_events(self, events):
        pass

    def update(self):
        self.angle = (self.angle - 5) % 360
        if not self.game.loader.queue.empty():
            self.game.change_state(self.game.states["play"])

    def draw(self):
        self.game.screen.fill(BLACK)
        Utils.draw_text_outline(
            self.game.screen,
            "LOADING WORLD DATA...",
            self.game.assets.fonts["med"],
            WHITE,
            self.game.width // 2,
            self.game.height * 0.3,
        )
        rot_img = pygame.transform.rotate(self.ball_img, self.angle)
        rect = rot_img.get_rect(center=(self.game.width // 2,
                                        self.game.height * 0.6))
        self.game.screen.blit(rot_img, rect)


# [REF-0071: Math Difficulty Selection]
class DifficultySelectionState(GameState):
    """
    Lets the player pick how hard the math is. Used in two places:
      * New Game flow (after choosing a rival, before the starter)
      * In-game OPTIONS button (Play/City HUD)

    on_confirm / on_back are callables so the same screen works in both
    places and can never soft-lock: BACK and ESC always leave.
    """
    uses_keyboard = True  # its own arrow/Enter/typing handling


    def __init__(self, game, on_confirm, on_back, title="CHOOSE YOUR MATH LEVEL",
                 return_state=None):
        super().__init__(game)
        self.on_confirm = on_confirm
        self.on_back = on_back
        self.title = title
        # Opened from the in-game OPTIONS button: also offers AUTOSAVE and QUIT.
        self.in_game = return_state is not None
        self.previous_state = return_state  # lets a save pick up the route's ball count
        self.quit_prompt = False
        self.story = game.story_manager
        self.input_lock = 6  # frames; stops the click that opened us from landing here

        # Card list: AUTO first, then every level from math_levels.json
        self.entries = [{"key": "AUTO", "name": "AUTO", "desc": ""}]
        for lv in game.math.levels:
            self.entries.append({"key": lv["id"], "name": lv["name"], "desc": lv["desc"]})

        current = self.story.math_difficulty
        self.selected_idx = next(
            (i for i, e in enumerate(self.entries) if e["key"] == current), 0
        )

        self._layout()
        self._refresh_preview()

    # ---------------- layout ----------------
    def _layout(self):
        """The menu frame (src/ui/theme.py) in purple: BACK, the title and QUIT in the header; the
        math levels as white cards; the level cap and autosave in a row of setting cards; the
        example question and CONFIRM in the text box at the bottom."""
        from src.ui.panels import CommandButton
        from src.ui import theme
        w, h = self.game.width, self.game.height
        fonts = self.game.assets.fonts
        H = theme.HEADER_H
        self.bar_rect = pygame.Rect(16, h - 86, w - 32, 78)
        self.settings_rect = pygame.Rect(24, self.bar_rect.top - 12 - 84, w - 48, 84)
        self.cols = 3 if w >= h else 1
        rows = (len(self.entries) + self.cols - 1) // self.cols
        top = H + 52
        bottom = self.settings_rect.top - 14
        gap = 12
        card_w = (w - 48 - gap * (self.cols - 1)) // self.cols
        card_h = min(110, (bottom - top - gap * (rows - 1)) // rows)
        self.card_rects = []
        for i in range(len(self.entries)):
            r, c = divmod(i, self.cols)
            self.card_rects.append(pygame.Rect(24 + c * (card_w + gap), top + r * (card_h + gap), card_w, card_h))

        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", fonts["button"], self.go_back,
                                      bg_color=theme.BACK, autosize=False)
        self.btn_quit = CommandButton((w - 16 - 140, 14, 140, 56), "QUIT", fonts["button"], self.open_quit_prompt,
                                      bg_color=theme.FIGHT, autosize=False)
        self.btn_confirm = CommandButton((self.bar_rect.right - 18 - 240, self.bar_rect.y + 10, 240,
                                          self.bar_rect.h - 26), "CONFIRM", fonts["button"], self.confirm,
                                         bg_color=theme.POKEMON, autosize=False)
        half = (self.settings_rect.w - 14) // 2
        s = self.settings_rect
        self.btn_cap = CommandButton((s.x + half - 14 - 250, s.y + 14, 250, s.h - 32), self._cap_label(),
                                     fonts["label"], self.cycle_cap, bg_color=theme.MEGA, autosize=False)
        self.btn_autosave = CommandButton((s.right - 14 - 250, s.y + 14, 250, s.h - 32), self._autosave_label(),
                                          fonts["label"], self.toggle_autosave, bg_color=theme.RUN, autosize=False)
        cx, cy = w // 2, h // 2
        self.quit_panel = pygame.Rect(cx - 260, cy - 170, 520, 340)
        self.quit_buttons = [
            CommandButton((cx - 200, cy - 60, 400, 62), "SAVE & QUIT TO TITLE", fonts["label"],
                          lambda: self.quit_game(save=True), bg_color=theme.POKEMON, autosize=False),
            CommandButton((cx - 200, cy + 14, 400, 62), "QUIT TO TITLE (NO SAVE)", fonts["label"],
                          lambda: self.quit_game(save=False), bg_color=theme.FIGHT, autosize=False),
            CommandButton((cx - 200, cy + 88, 400, 62), "CANCEL", fonts["label"],
                          self.close_quit_prompt, bg_color=theme.BACK, autosize=False),
        ]

    def _autosave_label(self):
        return "AUTOSAVE: " + ("ON" if self.story.autosave else "OFF")

    def toggle_autosave(self):
        self.story.autosave = not self.story.autosave
        self.btn_autosave.text = self._autosave_label()

    def open_quit_prompt(self):
        self.quit_prompt = True

    def close_quit_prompt(self):
        self.quit_prompt = False

    def quit_game(self, save):
        if save:
            self.game.update_save_data()
            self.game.data.save()
        self.game.change_state(MainMenuState(self.game))

    def _cap_label(self):
        from src.world import levels
        return "CAP: " + levels.LEVEL_CAP_TEXT[levels.cap_mode(self.story)][0]

    def cycle_cap(self):
        from src.world import levels
        modes = levels.LEVEL_CAP_MODES
        self.story.level_cap_mode = modes[(modes.index(levels.cap_mode(self.story)) + 1) % len(modes)]
        self.btn_cap.text = self._cap_label()

    def _fit_font(self, text, max_w, keys=("s_med", "small", "tiny")):
        """Dynamic font scaling: biggest game font that fits the space."""
        fonts = self.game.assets.fonts
        for k in keys:
            if fonts[k].size(text)[0] <= max_w:
                return fonts[k]
        return fonts[keys[-1]]

    def _entry_desc(self, entry):
        if entry["key"] == "AUTO":
            return f"Grows with you (now {self._auto_name().title()})"
        return entry["desc"]

    def _auto_name(self):
        region = self.story.get_current_region()
        badges = len(self.story.badges.get(region, []))
        return self.game.math.level_by_id[
            self.game.math.auto_level(region, badges)]["name"]

    def _selected_level(self):
        key = self.entries[self.selected_idx]["key"]
        saved = self.story.math_difficulty
        self.story.math_difficulty = key
        level = self.story.get_math_level()
        self.story.math_difficulty = saved
        return level

    def _refresh_preview(self):
        # Prefer a plain "a + b = ?" style example; it explains the level best
        level = self._selected_level()
        for _ in range(20):
            self.preview = self.game.math.generate(level, 3)[0]
            if self.preview.endswith("= ?") and len(self.preview.split()) == 5:
                break

    # ---------------- actions ----------------
    def select(self, idx):
        idx = max(0, min(len(self.entries) - 1, idx))
        if idx != self.selected_idx:
            self.selected_idx = idx
            self._refresh_preview()

    def confirm(self):
        self.story.math_difficulty = self.entries[self.selected_idx]["key"]
        self.on_confirm()

    def go_back(self):
        self.on_back()

    # ---------------- GameState ----------------
    def start(self):
        self.input_lock = 6

    def handle_events(self, events):
        if self.input_lock > 0:
            return
        if self.quit_prompt:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.close_quit_prompt()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for b in self.quit_buttons:
                        if b.handle_event(event):
                            return
            return
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.in_game and (self.btn_quit.handle_event(event)
                                     or self.btn_autosave.handle_event(event)):
                    return
                if self.btn_back.handle_event(event) or self.btn_confirm.handle_event(event):
                    return  # state changed; ignore the rest of this frame
                if self.btn_cap.handle_event(event):
                    return
                for i, rect in enumerate(self.card_rects):
                    if rect.collidepoint(event.pos):
                        if i == self.selected_idx:
                            self.confirm()  # second tap on the same card confirms
                            return
                        self.select(i)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.go_back()
                    return
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self.confirm()
                    return
                step = {pygame.K_LEFT: -1, pygame.K_RIGHT: 1,
                        pygame.K_UP: -self.cols, pygame.K_DOWN: self.cols}.get(event.key)
                if step:
                    self.select(self.selected_idx + step)

    def update(self):
        if self.input_lock > 0:
            self.input_lock -= 1

    def draw(self):
        from src.ui import theme
        from src.world import levels
        screen = self.game.screen
        fonts = self.game.assets.fonts
        w, h = self.game.width, self.game.height
        accent = theme.ACCENT["options"]
        title_font = self._fit_font(self.title, w - 360 - 176, ("button", "label"))
        theme.menu_background(screen, accent, self.title, title_font, title_x=176)
        sub = "Pick what feels right - you can change it any time from OPTIONS."
        theme.shadow_text(screen, sub, fonts["label"], 24, theme.HEADER_H + 16, color=(220, 224, 240),
                          shadow=theme.MENU_BG)

        mouse = pygame.mouse.get_pos()
        for i, (entry, rect) in enumerate(zip(self.entries, self.card_rects)):
            selected = i == self.selected_idx
            theme.card(screen, rect, hover=rect.collidepoint(mouse), selected=selected, accent=accent)
            inner_w = rect.width - 30
            name = entry["name"] if entry["key"] == "AUTO" else f"{entry['key']}. {entry['name']}"
            theme.shadow_text(screen, name, self._fit_font(name, inner_w, ("button", "label")), rect.x + 16,
                              rect.y + 12, color=theme.shade(accent, 0.8) if selected else theme.TEXT)
            desc = self._entry_desc(entry)
            theme.shadow_text(screen, desc, self._fit_font(desc, inner_w, ("caption", "tiny")),
                              rect.x + 16, rect.bottom - 34, color=(96, 102, 122))
            if selected:  # a tick in the corner
                pygame.draw.circle(screen, accent, (rect.right - 22, rect.y + 22), 12)
                pygame.draw.lines(screen, WHITE, False, [(rect.right - 28, rect.y + 22), (rect.right - 23, rect.y + 27),
                                                         (rect.right - 15, rect.y + 16)], 3)

        # Settings: the level cap (and autosave, in a game).
        s = self.settings_rect
        half = (s.w - 14) // 2
        left = pygame.Rect(s.x, s.y, half, s.h)
        theme.card(screen, left)
        mode = levels.cap_mode(self.story)
        note = levels.LEVEL_CAP_TEXT[mode][1]
        if mode == "STORY":
            note += f" (now Lv {levels.story_level_cap(self.story)})"
        from src.ui.dialogue import wrap_text
        rows = wrap_text(note, fonts["caption"], half - 290)[:3]
        for k, row in enumerate(rows):
            theme.shadow_text(screen, row, fonts["caption"], left.x + 16,
                              left.centery - len(rows) * 11 + k * 22)
        self.btn_cap.draw(screen)
        if self.in_game:
            right = pygame.Rect(s.x + half + 14, s.y, half, s.h)
            theme.card(screen, right)
            tip = "Saves each time you travel to a new area."
            rows = wrap_text(tip, fonts["caption"], half - 290)[:3]
            for k, row in enumerate(rows):
                theme.shadow_text(screen, row, fonts["caption"], right.x + 16,
                                  right.centery - len(rows) * 11 + k * 22)
            self.btn_autosave.draw(screen)
            self.btn_quit.draw(screen)

        # The text box: an example question at this level, and CONFIRM.
        theme.draw_textbox(screen, self.bar_rect)
        example = f"Example:  {self.preview}"
        ef = self._fit_font(example, self.btn_confirm.rect.x - self.bar_rect.x - 60, ("dialog", "s_med", "label"))
        theme.shadow_text(screen, example, ef, self.bar_rect.x + 32, self.bar_rect.centery - ef.get_height() // 2 - 2)
        self.btn_confirm.draw(screen)
        self.btn_back.draw(screen)

        if self.in_game and self.quit_prompt:
            shade = pygame.Surface((w, h), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 170))
            screen.blit(shade, (0, 0))
            theme.draw_panel(screen, self.quit_panel)
            ask = "BACK TO THE TITLE SCREEN?"
            Utils.draw_text_outline(screen, ask, self._fit_font(ask, self.quit_panel.w - 40, ("button", "label")),
                                    WHITE, self.quit_panel.centerx, self.quit_panel.top + 50)
            for b in self.quit_buttons:
                b.draw(screen)


def open_difficulty_options(game, return_state):
    """
    Opens the difficulty screen from any in-game state (route or town HUD)
    and comes back to return_state afterwards.
    """
    old_level = game.story_manager.get_math_level()

    def back():
        if hasattr(return_state, "is_resuming"):
            return_state.is_resuming = True
        game.change_state(return_state)

    def confirm():
        # If a question is already on screen and the level changed, swap it out
        if (getattr(return_state, "problem_str", "") not in ("", "...")
                and hasattr(return_state, "generate_math_set")
                and game.story_manager.get_math_level() != old_level):
            n = len(getattr(return_state, "options", [])) or 3
            (return_state.problem_str, return_state.correct_ans,
             return_state.options) = return_state.generate_math_set(num_options=n)
        game.update_save_data()
        back()

    game.change_state(DifficultySelectionState(
        game, on_confirm=confirm, on_back=back, title="OPTIONS",
        return_state=return_state))
