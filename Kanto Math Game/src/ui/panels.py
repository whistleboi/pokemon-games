# [REF-0001: System Imports]
import pygame
from src.ui.manager import UIElement
from src.ui.widgets import Button
from src.utils import Utils
from src.ui import theme


class CommandButton(Button):
    """A big coloured command (FIGHT, BAG, POKeMON, RUN; the town menu's too): src/ui/theme.py."""

    def draw(self, surface):
        if not self.visible:
            return
        hover = self.callback is not None and self.rect.collidepoint(pygame.mouse.get_pos())
        color = self.bg_color if self.callback is not None else (128, 132, 144)  # disabled: grey
        theme.command_button(surface, self.rect, self.text, self.font, color, hover=hover)


class CommandMenu(UIElement):
    """The bottom bar shared by battles and towns: the games' white text box with a prompt on the
    left ("What will PIKACHU do?", "Welcome to Viridian City!") and four coloured commands on the
    right. Same size and place on every screen (Utils.get_full_dialogue_rect)."""

    LEFT_SHARE = 0.52

    def __init__(self, game, specs):
        rect = Utils.get_full_dialogue_rect(game)
        super().__init__(rect, None, visible=True)
        self.game = game
        self.left_rect = pygame.Rect(rect.x, rect.y, int(rect.width * self.LEFT_SHARE), rect.height)
        self.right_rect = pygame.Rect(self.left_rect.right, rect.y, rect.width - self.left_rect.width, rect.height)
        pad, gap = 22, 14
        btn_w = (self.right_rect.width - pad * 2 - gap) // 2
        btn_h = (self.right_rect.height - pad * 2 - gap - 4) // 2
        self.buttons = []
        for i, (label, callback, color) in enumerate(specs):
            r = pygame.Rect(self.right_rect.x + pad + (i % 2) * (btn_w + gap),
                            self.right_rect.y + pad + (i // 2) * (btn_h + gap), btn_w, btn_h)
            self.buttons.append(CommandButton(r, label, game.assets.fonts["button"], callback, bg_color=color,
                                              autosize=False))

    def handle_event(self, event):
        if not self.visible:
            return False
        for btn in self.buttons:
            if btn.handle_event(event):
                return True
        return False

    def prompt_lines(self):
        return []

    def prompt_rect(self):
        return self.left_rect

    def draw(self, surface):
        if not self.visible:
            return
        theme.draw_textbox(surface, self.rect)
        area = self.prompt_rect()
        font = self.game.assets.fonts["dialog"]
        lines = []
        for line in self.prompt_lines():
            from src.ui.dialogue import wrap_text
            lines += wrap_text(line, font, area.width - 70)
        lh = int(font.get_linesize() * 1.2)
        top = area.y + (area.h - len(lines) * lh) // 2
        for i, line in enumerate(lines):
            theme.shadow_text(surface, line, font, area.x + 40, top + i * lh)
        for btn in self.buttons:
            btn.draw(surface)


# [REF-0007: Battle Action UI]
class BattleActionMenu(CommandMenu):
    """FIGHT / BAG / POKeMON / RUN (the order the battle's tests and keyboard rely on), and a
    MEGA / PRIMAL button beside them while it's available."""

    def __init__(self, game, pokemon_name, on_math, on_pkdex, on_pkmn, on_run, on_mega=None, mega_label="MEGA",
                 extra=None):
        """extra: more one-a-battle buttons beside MEGA ([(label, callback, colour)]: Z-MOVE, TERA)."""
        super().__init__(game, [("FIGHT", on_math, theme.FIGHT), ("BAG", on_pkdex, theme.BAG),
                                ("POKéMON", on_pkmn, theme.POKEMON), ("RUN", on_run, theme.RUN)])
        self.pokemon_name = pokemon_name.upper()
        self.on_math, self.on_pkdex, self.on_run = on_math, on_pkdex, on_run
        self.mega_button = None
        specials = ([(mega_label, on_mega, (200, 60, 40) if mega_label == "PRIMAL" else theme.MEGA)] if on_mega else [])
        specials += list(extra or [])
        self.special_buttons = []
        h = self.buttons[0].rect.h
        if len(specials) <= 1:  # one: beside the prompt, as MEGA always was
            for label, cb, color in specials:
                btn = CommandButton(pygame.Rect(self.left_rect.right - 200, self.rect.centery - h // 2, 180, h), label,
                                    game.assets.fonts["button"], cb, bg_color=color, autosize=False)
                self.special_buttons.append(btn)
                self.buttons.append(btn)
        else:  # two or three (MEGA, Z-MOVE, TERA): a row just above the text box
            w, x = 170, self.rect.x + 12
            for label, cb, color in specials:
                btn = CommandButton(pygame.Rect(x, self.rect.top - h - 10, w, h), label, game.assets.fonts["label"], cb,
                                    bg_color=color, autosize=False)
                self.special_buttons.append(btn)
                self.buttons.append(btn)
                x += w + 12
        if on_mega:
            self.mega_button = self.special_buttons[0]

    def prompt_lines(self):
        return [f"What will {self.pokemon_name} do?"]

    def prompt_rect(self):
        if len(self.special_buttons) == 1:  # room for MEGA / PRIMAL beside the prompt
            return pygame.Rect(self.left_rect.x, self.left_rect.y, self.special_buttons[0].rect.left - self.left_rect.x,
                               self.left_rect.h)
        return self.left_rect


# [REF-0008: City Action UI]
class CityActionMenu(CommandMenu):
    """A town's EXPLORE / PKDEX / POKéMON / TRAVEL, in the battle menu's style and place."""

    def __init__(self, game, area_name, on_explore, on_pkdex, on_pkmn, on_travel):
        super().__init__(game, [("EXPLORE", on_explore, theme.RUN), ("PKDEX", on_pkdex, theme.FIGHT),
                                ("POKéMON", on_pkmn, theme.POKEMON), ("TRAVEL", on_travel, theme.BAG)])
        self.area_name = area_name

    def prompt_lines(self):
        return ["Welcome to", self.area_name.replace("_", " ").title() + "!"]


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

    PANEL = (112, 102, 86)      # Solar Eclipse's party panels: see-through, warm grey,
    PANEL_SEL = (196, 152, 56)  # gold for the one you're on,
    PANEL_FAINT = (150, 58, 62)  # red when fainted

    def _panel(self, surface, r, selected, fainted):
        """The slanted, see-through party panel: a ring behind the Pokemon, the right part darker."""
        base = self.PANEL_FAINT if fainted else self.PANEL_SEL if selected else self.PANEL
        if self.hovered and not selected:
            base = theme.mix(base, (255, 255, 255), 0.12)
        c = min(20, r.h // 4)
        pts = theme.chamfer(r, c, tl=False)
        theme.alpha_poly(surface, (0, 0, 0), theme.chamfer(r.move(5, 6), c, tl=False), 120)
        theme.alpha_poly(surface, base, pts, 236 if selected else 214)
        split = r.x + r.h + 10
        theme.alpha_poly(surface, (0, 0, 0), [(split + 26, r.y + 4), (r.right - 4, r.y + 4), (r.right - 4, r.bottom - c - 2),
                                              (r.right - c - 2, r.bottom - 4), (split, r.bottom - 4), (split + 26, r.centery)], 52)
        pygame.draw.circle(surface, theme.shade(base, 0.78), (r.x + 12 + (r.h - 20) // 2, r.centery), (r.h - 20) // 2, 7)
        edge = (255, 228, 150) if selected else (255, 200, 200) if fainted else (232, 228, 214)
        pygame.draw.polygon(surface, edge, pts, 4 if selected else 3)

    def draw(self, surface):
        """Solar Eclipse's party panel (the 11-21 restyle): sprite on a ring, name and gender, level,
        status, HP tag and bar and numbers; gold when picked, red when fainted."""
        if not self.visible or not self.pokemon:
            return
        p, r, f = self.pokemon, self.rect, self.game.assets.fonts
        selected = getattr(self, "selected", False)
        from src.states.systems import fit_sprite
        if getattr(p, "is_egg", False):  # an Egg: the egg and its name, nothing else
            self._panel(surface, r, selected, False)
            if p.image:
                spr = fit_sprite(p.image, r.h - 20, r.h - 20)
                surface.blit(spr, spr.get_rect(center=(r.x + 12 + (r.h - 20) // 2, r.centery)))
            theme.shadow_text(surface, "Egg", f["s_med"], r.x + r.h + 24, r.y + 12)
            return
        fainted = p.current_hp <= 0
        self._panel(surface, r, selected, fainted)
        art = p.image or p.sidebar_image
        if art:
            spr = fit_sprite(art, r.h - 20, r.h - 20)
            surface.blit(spr, spr.get_rect(center=(r.x + 12 + (r.h - 20) // 2, r.centery)))
        x = r.x + r.h + 24
        name = p.display_name.title()
        nf = f["s_med"] if f["s_med"].size(name)[0] <= r.right - x - 110 else f["label"]
        nr = theme.shadow_text(surface, name, nf, x, r.y + 10)
        from src.pokemon import breeding
        theme.draw_gender(surface, breeding.gender_of(self.game, p), nr.right + 8, r.y + 14, 18)
        lv = f"Lv{p.level}" + (" MAX" if p.level >= p.MAX_LEVEL else "")
        theme.shadow_text(surface, lv, f["label"], r.right - 22, r.y + 14, align="right")
        tag_w = theme.status_tag(surface, "faint" if fainted else getattr(p, "status", None), f["caption"],
                                 x, r.y + 46)
        from src.pokemon import affection
        if affection.hearts(p) > 0:  # Pokemon-Amie hearts, once it has any
            from src.ui.hearts import draw_hearts
            draw_hearts(surface, p, x + tag_w + (60 if tag_w else 40), r.y + 58, size=13)
        bar_y = r.bottom - 42
        hw = theme.hp_label(surface, x, bar_y - 1, 18)
        theme.hp_bar(surface, x + hw + 2, bar_y, r.right - 24 - x - hw - 2, p.current_hp, p.get_max_hp(), f["caption"],
                     h=10)
