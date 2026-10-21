# [REF-0001: System Imports]
import pygame
from src.ui.manager import UIElement
from src.ui.widgets import Button
from src.utils import Utils
from src.config import WHITE, BLACK, BLUE, RED, GREEN, GOLD


# [REF-0007: Battle Action UI]
class BattleActionMenu(UIElement):

    def __init__(self, game, pokemon_name, on_math, on_pkdex, on_pkmn, on_run, on_mega=None, mega_label="MEGA"):
        rect = Utils.get_full_dialogue_rect(game)
        super().__init__(rect, None, visible=True)
        self.game = game

        self.pokemon_name = pokemon_name.upper()
        self.on_math = on_math
        self.on_pkdex = on_pkdex
        self.on_run = on_run

        self.left_rect = pygame.Rect(
            rect.x, rect.y, int(rect.width * 0.55), rect.height
        )
        self.right_rect = pygame.Rect(
            rect.x + self.left_rect.width,
            rect.y,
            rect.width - self.left_rect.width,
            rect.height
        )

        btn_w = (self.right_rect.width - 50) // 2
        btn_h = (self.right_rect.height - 50) // 2

        self.buttons = []

        r = pygame.Rect(self.right_rect.x + 20, self.right_rect.y + 15, btn_w, btn_h)
        self.buttons.append(
            Button(
                r,
                "MATH",
                game.assets.fonts["s_med"],
                on_math,
                bg_color=WHITE,
                text_color=WHITE,
                outline_color=BLACK,
            )
        )

        r = pygame.Rect(
            self.right_rect.x + btn_w + 30, self.right_rect.y + 15, btn_w, btn_h
        )
        self.buttons.append(
            Button(
                r,
                "BAG",
                game.assets.fonts["s_med"],
                on_pkdex,
                bg_color=WHITE,
                text_color=WHITE,
                outline_color=BLACK,
            )
        )

        r = pygame.Rect(
            self.right_rect.x + 20, self.right_rect.y + btn_h + 25, btn_w, btn_h
        )
        self.buttons.append(
            Button(
                r,
                "PKMN",
                self.game.assets.fonts["s_med"],
                on_pkmn,
                bg_color=WHITE,
                text_color=WHITE,
                outline_color=BLACK,
            )
        )

        r = pygame.Rect(
            self.right_rect.x + btn_w + 30, self.right_rect.y + btn_h + 25, btn_w, btn_h
        )
        self.buttons.append(
            Button(
                r,
                "RUN",
                self.game.assets.fonts["s_med"],
                on_run,
                bg_color=WHITE,
                text_color=WHITE,
                outline_color=BLACK,
            )
        )

        # Mega Evolution / Primal Reversion: beside the four, only while it's available.
        self.mega_button = None
        if on_mega:
            mega_w = 220
            r = pygame.Rect(self.right_rect.x - mega_w - 10, self.right_rect.centery - btn_h // 2, mega_w, btn_h)
            color = (200, 60, 40) if mega_label == "PRIMAL" else (150, 60, 200)
            self.mega_button = Button(r, mega_label, game.assets.fonts["s_med"], on_mega,
                                      bg_color=color, text_color=WHITE, outline_color=BLACK, autosize=False)
            self.buttons.append(self.mega_button)

    def handle_event(self, event):
        if not self.visible:
            return False
        for btn in self.buttons:
            if btn.handle_event(event):
                return True
        return False

    def draw(self, surface):
        if not self.visible:
            return

        Utils.draw_classic_panel(
            surface, self.rect.x, self.rect.y, self.rect.width, self.rect.height
        )

        text = f"What will {self.pokemon_name} do?"
        text_rect = self.left_rect.copy()
        font, line_height = self.game.assets.fonts["med"], 65
        if self.mega_button:
            # Make room for the MEGA / PRIMAL button.
            text_rect.width = self.mega_button.rect.left - self.left_rect.x
            font, line_height = self.game.assets.fonts["s_med"], 50
        Utils.draw_multiline_text(
            surface,
            text,
            font,
            WHITE,
            text_rect.centerx,
            text_rect.centery,
            max_width=text_rect.width - 40,
            line_height=line_height,
            center=True,
            outline_color=BLACK,
        )

        white_panel = self.right_rect.inflate(-18, -18)
        pygame.draw.rect(surface, WHITE, white_panel, border_radius=12)
        pygame.draw.rect(surface, BLACK, white_panel, 6, border_radius=12)

        for btn in self.buttons:
            btn.draw(surface)


# [REF-0008: City Action UI]
class CityActionMenu(UIElement):

    def __init__(self, game, area_name, on_explore, on_pkdex, on_pkmn, on_travel):
        rect = Utils.get_full_dialogue_rect(game)
        super().__init__(rect, None, visible=True)
        self.game = game
        self.area_name = area_name

        self.right_rect = pygame.Rect(
            rect.x + int(rect.width * 0.55),
            rect.y,
            rect.width - int(rect.width * 0.55),
            rect.height
        )

        btn_w = (self.right_rect.width - 50) // 2
        btn_h = (self.right_rect.height - 50) // 2

        self.buttons = []
        font = game.assets.fonts["s_med"]

        button_defs = [
            (pygame.Rect(self.right_rect.x + 20, self.right_rect.y + 15, btn_w, btn_h), "EXPLORE", on_explore, BLUE),
            (pygame.Rect(self.right_rect.x + btn_w + 30, self.right_rect.y + 15, btn_w, btn_h), "PKDEX", on_pkdex, RED),
            (pygame.Rect(self.right_rect.x + 20, self.right_rect.y + btn_h + 25, btn_w, btn_h), "PKMN", on_pkmn, GREEN),
            (pygame.Rect(self.right_rect.x + btn_w + 30, self.right_rect.y + btn_h + 25, btn_w, btn_h), "TRAVEL", on_travel, GOLD),
        ]

        for r, text, callback, color in button_defs:
            self.buttons.append(Button(r, text, font, callback, bg_color=color, text_color=WHITE, outline_color=BLACK))

    def handle_event(self, event):
        if not self.visible:
            return False
        for btn in self.buttons:
            if btn.handle_event(event):
                return True
        return False

    def draw(self, surface):
        if not self.visible:
            return

        Utils.draw_classic_panel(
            surface, self.rect.x, self.rect.y, self.rect.width, self.rect.height
        )

        welcome_text = f"Welcome to\n{self.area_name.replace('_', ' ').title()}!"
        left_rect_w = int(self.rect.width * 0.55)
        font = self.game.assets.fonts["med"]
        if font.size(self.area_name.replace("_", " ").title() + "!")[0] > left_rect_w - 60:
            font = self.game.assets.fonts["s_med"]  # long town names stay on one line
        Utils.draw_multiline_text(
            surface,
            welcome_text,
            font,
            WHITE,
            self.rect.x + left_rect_w // 2,
            self.rect.centery,
            max_width=left_rect_w - 60,
            line_height=font.get_linesize() + 10,
            center=True,
            outline_color=BLACK,
        )

        white_panel = self.right_rect.inflate(-18, -18)
        pygame.draw.rect(surface, WHITE, white_panel, border_radius=12)
        pygame.draw.rect(surface, BLACK, white_panel, 6, border_radius=12)

        for btn in self.buttons:
            btn.draw(surface)


# [REF-0009: Party Slot UI]
class PartySlotUI(UIElement):
    def __init__(self, rect, pokemon, index, callback, game):
        super().__init__(rect, None, True)
        self.pokemon = pokemon
        self.index = index
        self.callback = callback
        self.game = game
        self.hovered = False

    def handle_event(self, event):
        if not self.visible or not self.pokemon:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback(self.index)
                return True
        elif event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        return False

    def draw(self, surface):
        if not self.visible or not self.pokemon:
            return

        base_color = (65, 130, 255) if not self.hovered else (100, 165, 255)
        pygame.draw.rect(surface, base_color, self.rect, border_radius=14)
        pygame.draw.rect(surface, WHITE, self.rect, 5, border_radius=14)

        name_x = self.rect.x + 20
        name_y = self.rect.y + 25
        name = self.pokemon.display_name.upper()

        font = self.game.assets.fonts["s_med"]
        if len(name) > 10:
            font = self.game.assets.fonts["small"]

        Utils.draw_text_outline(surface, name, font, WHITE, name_x, name_y, BLACK, 2, align="left")

        stage_str = f"Lv {self.pokemon.level}" + ("  MAX" if self.pokemon.level >= self.pokemon.MAX_LEVEL else "")
        Utils.draw_text_outline(surface, stage_str, self.game.assets.fonts["tiny"], WHITE, name_x, name_y + 30, BLACK, 2, align="left")
        from src.pokemon import affection
        if affection.hearts(self.pokemon) > 0:  # Pokemon-Amie hearts, once it has any
            from src.ui.hearts import draw_hearts
            lv_w = self.game.assets.fonts["tiny"].size(stage_str)[0]
            draw_hearts(surface, self.pokemon, name_x + lv_w + 60, name_y + 38, size=14)

        sprite = pygame.transform.scale(self.pokemon.sidebar_image, (80, 80))
        sprite_rect = sprite.get_rect(center=(self.rect.right - 60, self.rect.y + 45))
        surface.blit(sprite, sprite_rect)

        bar_h = 14
        bar_margin = 15
        bar_w = self.rect.width - (bar_margin * 2)
        hp_y = self.rect.bottom - bar_h - 10

        bar_bg = pygame.Rect(self.rect.x + bar_margin, hp_y, bar_w, bar_h)
        pygame.draw.rect(surface, BLACK, bar_bg)
        pygame.draw.rect(surface, (50, 50, 50), bar_bg.inflate(-6, -6))

        max_hp = self.pokemon.get_max_hp()
        current_hp = self.pokemon.current_hp
        ratio = current_hp / max_hp if max_hp > 0 else 0
        hp_color = GREEN if ratio > 0.5 else GOLD if ratio > 0.25 else RED
        bar = pygame.Rect(bar_bg.x + 2, bar_bg.y + 2, int((bar_w - 4) * ratio), 8)
        pygame.draw.rect(surface, hp_color, bar, border_radius=4)

        hp_str = f"{int(current_hp)}/{int(max_hp)}"
        Utils.draw_text_outline(surface, "HP: " + hp_str, self.game.assets.fonts["tiny"], WHITE, bar_bg.x, hp_y - 12, BLACK, 1, align="left")
