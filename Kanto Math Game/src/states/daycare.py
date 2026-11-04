# [REF-0094: The Pokemon Day Care]
"""The Pokemon Day Care screen (Jordan, 11-03): leave two Pokemon, see if they get along, take them
back, collect their Egg. The rules are in src/pokemon/breeding.py.

LEAVE A POKEMON opens the party; once one Pokemon is in the Day Care, each card there says whether
it's COMPATIBLE with it, before you choose."""
import pygame

from src.states.base import GameState
from src.ui import theme
from src.ui.panels import CommandButton
from src.pokemon import breeding, abilities as ablib


class DaycareState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.story = game.story_manager
        f = game.assets.fonts
        w, h = game.width, game.height
        H = theme.HEADER_H
        self.bar_rect = pygame.Rect(16, h - 86, w - 32, 78)
        top = H + 16
        card_h = 250
        self.slot_rects = [pygame.Rect(24, top, (w - 64) // 2, card_h),
                           pygame.Rect(40 + (w - 64) // 2, top, (w - 64) // 2, card_h)]
        self.status_rect = pygame.Rect(24, top + card_h + 14, w - 48, self.bar_rect.top - 14 - (top + card_h + 14))
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.go_back, bg_color=theme.BACK,
                                      autosize=False)
        sr = self.status_rect
        self.btn_leave = CommandButton((sr.right - 20 - 300, sr.centery - 30, 300, 60), "LEAVE A POKéMON",
                                       f["label"], self.choose_to_leave, bg_color=theme.POKEMON, autosize=False)
        self.btn_egg = CommandButton((sr.right - 20 - 300, sr.centery - 30, 300, 60), "COLLECT EGG",
                                     f["label"], self.collect_egg, bg_color=theme.BAG, autosize=False)
        self.btn_take = [CommandButton((r.right - 20 - 200, r.bottom - 70, 200, 52), "TAKE BACK", f["label"],
                                       (lambda i=i: self.take_back(i)), bg_color=theme.RUN, autosize=False)
                         for i, r in enumerate(self.slot_rects)]
        self.message = "Leave two Pokemon here: if they get along, they may find an Egg!"

    # ------------------------------------------------------------------ state
    @property
    def dc(self):
        return breeding.daycare(self.story)

    def go_back(self):
        self.game.change_state(self.previous_state)

    def start(self):
        ui = self.game.ui_manager
        ui.elements.clear()
        ui.add_element(self.btn_back)
        mons = self.dc["mons"]
        self.btn_egg.set_visibility(bool(self.dc["egg"]))
        self.btn_leave.set_visibility(len(mons) < 2 and not self.dc["egg"])
        for b in (self.btn_leave, self.btn_egg):
            ui.add_element(b)
        for i, b in enumerate(self.btn_take):
            b.set_visibility(i < len(mons))
            ui.add_element(b)

    def _say(self, text):
        self.message = text
        self.start()

    # ------------------------------------------------------------------ leaving / taking back
    def party_tag(self, mon):
        """The party menu's tag on each card: COMPATIBLE / NOT COMPATIBLE with the one left here."""
        if getattr(mon, "is_egg", False):
            return ("EGG", False)
        mons = self.dc["mons"]
        if len(mons) != 1:
            return None
        ok, _ = breeding.compatible(self.game, mons[0], mon)
        return ("COMPATIBLE", True) if ok else ("NOT COMPATIBLE", False)

    def choose_to_leave(self):
        from src.states.systems import PokemonPartyMenuState
        menu = PokemonPartyMenuState(self.game, previous_state=self, context="use_item", on_select=self.leave)
        menu.message = "Which Pokémon will you leave?"
        self.game.change_state(menu)

    def leave(self, index):
        team = self.story.player_team
        self.game.change_state(self)
        if index >= len(team):
            return
        mon = team[index]
        if getattr(mon, "is_egg", False):
            self._say("An Egg can't be left at the Day Care.")
            return
        others = [p for p in team if p is not mon and not getattr(p, "is_egg", False)]
        if not others:
            self._say("You can't leave your last Pokémon! Keep at least one with you.")
            return
        self.story.heal_for_pc(mon)
        team.remove(mon)
        self.dc["mons"].append(mon)
        self.dc["steps"] = 0
        if len(self.dc["mons"]) == 2:
            ok, why = breeding.compatible(self.game, *self.dc["mons"])
            self._say(f"We'll look after {mon.display_name}. " + (
                "The two seem to get along very well!" if ok else f"The two prefer to play apart. ({why})"))
        else:
            self._say(f"We'll look after {mon.display_name}. Leave another to keep it company!")

    def take_back(self, i):
        mons = self.dc["mons"]
        if i >= len(mons):
            return
        if len(self.story.player_team) >= 6:
            self._say("Your party is full! Make room first.")
            return
        mon = mons.pop(i)
        self.story.player_team.append(mon)
        self.dc["steps"] = 0
        self._say(f"You took back {mon.display_name}.")

    def collect_egg(self):
        mons = self.dc["mons"]
        if len(self.story.player_team) >= 6:
            self._say("Your party is full! Make room for the Egg first.")
            return
        if len(mons) < 2:
            self.dc["egg"] = False
            self.start()
            return
        egg = breeding.make_egg(self.game, *mons)
        self.story.player_team.append(egg)
        self.dc["egg"] = False
        self._say(f"You received an Egg! It will hatch after about {breeding.HATCH_TRAVELS} trips in your party.")

    # ------------------------------------------------------------------ drawing
    def handle_events(self, events):
        pass

    def update(self):
        pass

    def draw(self):
        from src.states.systems import fit_sprite
        screen, f = self.game.screen, self.game.assets.fonts
        accent = theme.ACCENT["party"]
        theme.menu_background(screen, accent, "POKéMON DAY CARE", f["button"], title_x=176)
        mons = self.dc["mons"]
        for i, r in enumerate(self.slot_rects):
            theme.card(screen, r)
            if i >= len(mons):
                theme.shadow_text(screen, "(empty)", f["s_med"], r.centerx, r.centery, color=(150, 156, 176),
                                  align="center")
                continue
            p = mons[i]
            if p.image:
                spr = fit_sprite(p.image, 170, 170)
                screen.blit(spr, spr.get_rect(center=(r.x + 110, r.centery)))
            x = r.x + 220
            nr = theme.shadow_text(screen, p.display_name.upper(), f["s_med"], x, r.y + 22)
            theme.draw_gender(screen, breeding.gender_of(self.game, p), nr.right + 10, r.y + 26, 22)
            theme.shadow_text(screen, f"Lv{p.level}", f["label"], x, r.y + 70)
            groups = ", ".join(g.title().replace("1", " 1").replace("2", " 2").replace("3", " 3")
                               for g in sorted(breeding.egg_groups(self.game, p)))
            theme.shadow_text(screen, f"Egg Group: {groups}", f["caption"], x, r.y + 108, color=(110, 116, 136))
            theme.shadow_text(screen, ablib.name(self.game, ablib.ability(self.game, p)), f["caption"], x, r.y + 136,
                              color=(110, 116, 136))
        sr = self.status_rect
        theme.card(screen, sr)
        if self.dc["egg"]:
            line = "The couple found an Egg! Collect it below."
        elif len(mons) == 2:
            ok, why = breeding.compatible(self.game, *mons)
            line = (f"The two get along very well! An Egg in about {breeding.EGG_TRAVELS - self.dc['steps']} trips."
                    if ok else f"The two prefer to play apart. {why}")
        else:
            line = "Leave two Pokémon that share an Egg Group (a male and a female), or one with Ditto."
        from src.ui.dialogue import wrap_text
        for k, row in enumerate(wrap_text(line, f["label"], sr.w - 380)[:3]):
            theme.shadow_text(screen, row, f["label"], sr.x + 24, sr.y + 24 + k * 34)
        theme.draw_textbox(screen, self.bar_rect)
        theme.shadow_text(screen, self.message, f["label"], self.bar_rect.x + 32,
                          self.bar_rect.centery - f["label"].get_height() // 2)
        self.game.ui_manager.draw(screen)
