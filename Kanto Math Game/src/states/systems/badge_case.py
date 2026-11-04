"""The Badge Case."""

import pygame
import os
from src.states.base import GameState
from src.ui.panels import CommandButton
from src.ui import theme
from src.utils import Utils
from src.config import WHITE


# [REF-0040: Badge Case UI]
class BadgeCaseState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.earned_badges = game.story_manager.badges

        story = game.story_manager
        starts = story.get_region_starts()
        self.unlocked_regions = [
            r for r, cfg in starts
            if (story.story_flags.get(f"unlocked_{r.lower()}_badges") or story.badges.get(r))
            and not cfg.get("no_badges")  # Orre has no Gyms
        ] or [story.starting_region]

        home = game.story_manager.starting_region
        self.unlocked_regions.sort(key=lambda r: 0 if r == home else 1)

        self.current_page_idx = 0

        f = game.assets.fonts
        # The menu frame in the region's colour: the case (8 pockets) and the bar along the bottom
        # with the count and the region arrows.
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.go_back, bg_color=theme.BACK,
                                      autosize=False)
        self.bar_rect = pygame.Rect(16, game.height - 86, game.width - 32, 78)
        self.case_rect = pygame.Rect(24, theme.HEADER_H + 16, game.width - 48,
                                     self.bar_rect.top - 12 - theme.HEADER_H - 16)
        bh = self.bar_rect.h - 28
        self.btn_prev = CommandButton((self.bar_rect.right - 18 - 230, self.bar_rect.y + 12, 110, bh), "<",
                                      f["button"], self.prev_page, bg_color=theme.TAB_OFF, autosize=False)
        self.btn_next = CommandButton((self.bar_rect.right - 18 - 110, self.bar_rect.y + 12, 110, bh), ">",
                                      f["button"], self.next_page, bg_color=theme.TAB_OFF, autosize=False)

        self.region_maps = {
            "KANTO": {
                "BOULDER": 1, "CASCADE": 2, "THUNDER": 3, "RAINBOW": 4,
                "SOUL": 5, "MARSH": 6, "VOLCANO": 7, "EARTH": 8
            },
            "JOHTO": {
                "ZEPHYR": 1, "HIVE": 2, "PLAIN": 3, "FOG": 4,
                "STORMBADGE": 5, "MINERAL": 6, "GLACIER": 7, "RISING": 8
            },
            "HOENN": {
                "STONE": 1, "KNUCKLE": 2, "DYNAMO": 3, "HEAT": 4,
                "BALANCE": 5, "FEATHER": 6, "MIND": 7, "RAIN": 8
            }
        }

        self.badge_sprites = {"KANTO": {}, "JOHTO": {}, "HOENN": {}}
        for i in range(1, 9):
            k_img = game.assets.get_badge_image(i, "kanto")
            if k_img:
                self.badge_sprites["KANTO"][i] = pygame.transform.scale(k_img, (100, 100))

            j_img = game.assets.get_badge_image(i, "johto")
            if j_img:
                self.badge_sprites["JOHTO"][i] = pygame.transform.scale(j_img, (100, 100))

            h_img = game.assets.get_badge_image(i, "hoenn")
            if h_img:
                self.badge_sprites["HOENN"][i] = pygame.transform.scale(h_img, (100, 100))

        for region, cfg in starts:
            if region in self.region_maps:
                continue
            badges = story.get_region_gym_badges(region)
            self.region_maps[region] = {b: i + 1 for i, b in enumerate(badges)}
            numbered = cfg.get("badge_images", [])
            sprites = {}
            for i, badge in enumerate(badges, start=1):
                img = None
                if i <= len(numbered):
                    path = Utils.get_actual_path(game.assets.badges_dir, f"{numbered[i - 1]}.png")
                    if os.path.exists(path):
                        img = pygame.image.load(path).convert_alpha()
                sprites[i] = (pygame.transform.scale(img, (100, 100)) if img
                              else self._placeholder_badge(badge))
            self.badge_sprites[region] = sprites

    def _placeholder_badge(self, badge_name):
        surf = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.circle(surf, (200, 170, 60), (50, 50), 46)
        pygame.draw.circle(surf, (120, 90, 20), (50, 50), 46, 4)
        label = badge_name.replace("_", " ")[:8]
        Utils.draw_text_outline(surf, label, self.game.assets.fonts["tiny"], WHITE, 50, 50)
        return surf

    def prev_page(self):
        if len(self.unlocked_regions) > 1:
            self.current_page_idx = (self.current_page_idx - 1) % len(self.unlocked_regions)

    def next_page(self):
        if len(self.unlocked_regions) > 1:
            self.current_page_idx = (self.current_page_idx + 1) % len(self.unlocked_regions)

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.add_element(self.btn_back)
        if len(self.unlocked_regions) > 1:
            self.game.ui_manager.add_element(self.btn_prev)
            self.game.ui_manager.add_element(self.btn_next)

    def handle_events(self, events):
        pass

    def update(self):
        pass

    REGION_COLORS = {"KANTO": (196, 58, 52), "JOHTO": (52, 84, 170), "HOENN": (44, 140, 84),
                     "SINNOH": (110, 78, 168), "UNOVA": (70, 74, 86), "KALOS": (40, 112, 178),
                     "ALOLA": (214, 128, 40), "GALAR": (168, 44, 92), "PALDEA": (200, 82, 44),
                     "ORANGE": (226, 132, 30)}

    def _badge_name(self, region, i):
        """The badge in pocket i ("Boulder Badge"), from the region's own list."""
        for name, n in self.region_maps.get(region, {}).items():
            if n == i:
                words = name.replace("_", " ").title().replace("Badge", "").strip()
                return f"{words} Badge"
        return f"Badge {i}"

    def _starred(self, region, i):
        """Pocket i's badge won again in the League Redo (src/world/league_redo.py)."""
        from src.world import league_redo
        names = [n for n, k in self.region_maps.get(region, {}).items() if k == i]
        return any(league_redo.has_badge(self.game.story_manager, region, n) for n in names)

    @staticmethod
    def _draw_star(screen, center, r):
        import math
        pts = [(center[0] + (r if k % 2 == 0 else r * 0.45) * math.sin(math.pi * k / 5),
                center[1] - (r if k % 2 == 0 else r * 0.45) * math.cos(math.pi * k / 5)) for k in range(10)]
        pygame.draw.polygon(screen, (255, 214, 64), pts)
        pygame.draw.polygon(screen, (150, 100, 10), pts, 3)

    def draw(self):
        screen = self.game.screen
        f = self.game.assets.fonts
        region = self.unlocked_regions[self.current_page_idx] if self.unlocked_regions else "KANTO"
        accent = self.REGION_COLORS.get(region, theme.ACCENT["journal"])
        theme.menu_background(screen, accent, f"{region} BADGES", f["button"], title_x=176)

        badge_map = self.region_maps.get(region, {})
        earned_list = self.earned_badges.get(region, [])
        count = max(badge_map.values(), default=8)
        earned_n = sum(1 for i in range(1, count + 1) if any(badge_map.get(b) == i for b in earned_list))
        Utils.draw_text_outline(screen, f"{earned_n} / {count}", f["button"], WHITE, self.game.width - 24,
                                theme.HEADER_H // 2 - 4, align="right", outline_color=theme.shade(accent, 0.45),
                                thickness=3)

        # The case: a panel with a velvet pocket for each badge.
        theme.draw_panel(screen, self.case_rect)
        inner = self.case_rect.inflate(-32, -32)
        cols = 4
        rows = (count + cols - 1) // cols
        gap = 16
        cw = (inner.w - gap * (cols - 1)) // cols
        ch = (inner.h - gap * (rows - 1)) // rows
        mouse = pygame.mouse.get_pos()
        hovered = None
        stars = 0
        for i in range(1, count + 1):
            c, r = (i - 1) % cols, (i - 1) // cols
            pocket = pygame.Rect(inner.x + c * (cw + gap), inner.y + r * (ch + gap), cw, ch)
            earned = any(badge_map.get(b) == i for b in earned_list)
            velvet = theme.shade(accent, 0.45)
            pygame.draw.rect(screen, velvet, pocket, border_radius=14)
            pygame.draw.rect(screen, theme.shade(accent, 0.75) if earned else theme.shade(accent, 0.3), pocket, 3,
                             border_radius=14)
            spot = (pocket.centerx, pocket.y + (pocket.h - 34) // 2)
            pygame.draw.circle(screen, theme.shade(velvet, 0.75), spot, min(cw, ch - 34) // 2 - 6)
            sprite = self.badge_sprites.get(region, {}).get(i)
            if sprite:
                img = sprite.copy()
                if not earned:  # a faint outline where it will go
                    img.fill((60, 60, 70), special_flags=pygame.BLEND_RGB_MULT)
                    img.set_alpha(110)
                screen.blit(img, img.get_rect(center=spot))
            name = self._badge_name(region, i) if earned else f"#{i}"
            Utils.draw_text_outline(screen, name, f["label"] if f["label"].size(name)[0] <= cw - 12 else f["caption"],
                                    WHITE if earned else (150, 154, 170), pocket.centerx, pocket.bottom - 20,
                                    outline_color=theme.shade(velvet, 0.6), thickness=2)
            starred = earned and self._starred(region, i)
            if starred:  # won again in the League Redo
                self._draw_star(screen, (pocket.right - 30, pocket.y + 30), 20)
                stars += 1
            if pocket.collidepoint(mouse):
                hovered = (i, earned, starred)

        # The bar: the badge under the pointer, else how many; the region arrows.
        if hovered:
            i, earned, starred = hovered
            line = (f"{self._badge_name(region, i)} - won again in the League Redo!" if starred
                    else f"{self._badge_name(region, i)} - earned!" if earned else f"Badge #{i}: not yet earned.")
        else:
            line = f"{earned_n} of {count} {region.title()} badges."
            if stars:
                line += f"  League Redo: {stars} of {count}."
        theme.draw_textbox(screen, self.bar_rect)
        bf = f["s_med"]
        theme.shadow_text(screen, line, bf, self.bar_rect.x + 32, self.bar_rect.centery - bf.get_height() // 2 - 2)
        if len(self.unlocked_regions) > 1:
            theme.shadow_text(screen, "Region", f["label"], self.btn_prev.rect.x - 16, self.bar_rect.centery - 12,
                              align="right")
        self.game.ui_manager.draw(screen)
