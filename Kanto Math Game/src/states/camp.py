# [REF-0075: Galar camping and curry]
"""
Galar camping: SET UP CAMP on a Galar route or in the Wild Area.
  REST        heals the whole party and cures status (once per day at each spot)
  COOK CURRY  up to 3 berries go in the pot, then three timed math stirs. The
              curry's class (Koffing to Charizard) sets the bonus: every class heals
              and cures, better ones also give XP and a little affection.
"""
import datetime
import math
import random
import pygame

from src.states.poffin import _MenuState, _button_row
from src.ui.widgets import MathBattleUI
from src.utils import Utils
from src.config import WHITE, BLACK, GOLD, RED, GREEN, GRAY
from src.pokemon.poffin import BERRIES, berry_name
from src.pokemon import moves as movelib, affection
from src.world import levels

STIRS = 3
STIR_TIME_MS = 7000
MAX_BERRIES = 3
# (name, points needed, share of a level in XP, affection)
CURRY_CLASSES = (("Koffing", 0, 0.0, 0), ("Wobbuffet", 2, 0.25, 2), ("Milcery", 4, 0.5, 4),
                 ("Copperajah", 6, 0.75, 6), ("Charizard", 8, 1.0, 10))


def curry_class(points):
    return [c for c in CURRY_CLASSES if points >= c[1]][-1]


class CampState(_MenuState):
    def __init__(self, game, previous_state):
        super().__init__(game, previous_state)
        self.area = self.story.current_area_key
        self.phase = "MENU"
        self.math_ui = None
        self.berries = []
        self.selected = []

    def _today(self):
        return datetime.date.today().isoformat()

    def _used(self, what):
        return self.story.story_flags.get(f"camp_{what}_{self.area}") == self._today()

    def _mark(self, what):
        self.story.story_flags[f"camp_{what}_{self.area}"] = self._today()

    def show_menu(self):
        self.phase = "MENU"
        self.dialogue_box.set_visibility(False)
        self.set_buttons(_button_row(self.game, [
            ("REST", self.rest, GRAY if self._used("rest") else (70, 150, 90), None),
            ("COOK CURRY", self.show_berries, GRAY if self._used("curry") else (210, 120, 40), None),
            ("PACK UP", self.leave, RED, None)], self.box_rect.top + 45, width=230))

    def _heal_all(self):
        for p in self.story.player_team:
            if p:
                p.heal_full()

    # -- rest ----------------------------------------------------------------
    def rest(self):
        if self._used("rest"):
            self.say(["Your team already rested at this camp today.", "Try cooking some curry!"], self.show_menu)
            return
        self._mark("rest")
        self._heal_all()
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.play()
        self.say(["You rested by the campfire with your Pokemon...",
                  "Your team is fully healed and refreshed!"], self.show_menu)

    # -- curry ---------------------------------------------------------------
    def owned_berries(self):
        return [b for b in BERRIES if self.story.inventory.get(b, 0) > 0]

    def show_berries(self):
        if self._used("curry"):
            self.say(["You already cooked curry at this camp today."], self.show_menu)
            return
        self.phase = "BERRIES"
        self.dialogue_box.set_visibility(False)
        specs = []
        for b in self.owned_berries()[:8]:
            mark = "> " if b in self.selected else ""
            specs.append((f"{mark}{berry_name(b)} x{self.story.inventory[b]}", (lambda b=b: self.toggle(b)),
                          (170, 90, 60), self.icon(b)))
        buttons = _button_row(self.game, specs, self.box_rect.top + 14, width=270, height=56)
        buttons += _button_row(self.game, [("COOK!", self.begin, GREEN, None), ("BACK", self.show_menu, RED, None)],
                               self.box_rect.top - 76, width=200, height=56)
        self.set_buttons(buttons)

    def toggle(self, berry):
        if berry in self.selected:
            self.selected.remove(berry)
        elif len(self.selected) < MAX_BERRIES:
            self.selected.append(berry)
        self.show_berries()

    def begin(self):
        inv = self.story.inventory
        for b in self.selected:
            inv[b] -= 1
            if inv[b] <= 0:
                del inv[b]
        self.berries, self.selected = list(self.selected), []
        self._mark("curry")
        self.stir = self.good = self.quick = 0
        self.phase = "COOK"
        added = (", ".join(berry_name(b) for b in self.berries) + " went into the pot!") if self.berries \
            else "No berries... it'll be a plain curry."
        self.say([added, "Fan the flames and stir! Answer fast for a better curry."], self.ask)

    def ask(self):
        self.dialogue_box.set_visibility(False)
        self.set_buttons([])
        play = self.game.states["play"]
        self.problem, self.answer, self.options = play.generate_math_set(0, num_options=4)
        if self.math_ui and self.math_ui in self.game.ui_manager.elements:
            self.game.ui_manager.elements.remove(self.math_ui)
        self.math_ui = MathBattleUI(self.game, self.problem, self.options, self.on_answer)
        self.game.ui_manager.add_element(self.math_ui)
        self.asked_at = pygame.time.get_ticks()
        self.phase = "STIR"

    def time_left(self):
        return max(0, STIR_TIME_MS - (pygame.time.get_ticks() - self.asked_at))

    def on_answer(self, index):
        if self.phase != "STIR":
            return
        elapsed = pygame.time.get_ticks() - self.asked_at
        if self.options[index] != self.answer:
            msg = "The curry splattered a bit!"
        elif elapsed > STIR_TIME_MS:
            msg = "The bottom scorched a little..."
        else:
            self.good += 1
            if elapsed <= STIR_TIME_MS / 2:
                self.quick += 1
                msg = "Perfect stir! It smells amazing!"
            else:
                msg = "Nice stir!"
        self._next(msg)

    def _next(self, msg):
        self.math_ui.set_visibility(False)
        self.phase = "COOK"
        self.stir += 1
        self.say([msg], self.finish if self.stir >= STIRS else self.ask)

    def finish(self):
        name, _, share, love = curry_class(self.good + self.quick + len(self.berries))
        lines = [f"Your curry is ready... it's {name} Class!"]
        if name == "Koffing":
            lines.append("It's... edible. Your Pokemon ate it anyway. They're healed, at least!")
        else:
            lines.append("Everyone dug in! Your team is fully healed.")
        cap = levels.xp_cap(self.story)
        for p in self.story.player_team:
            if not p:
                continue
            p.friendship += 1
            if love:
                affection.add(p, love, daily=False)
            if share and p.level < cap:
                old = p.level
                if p.gain_xp(math.ceil(p.xp_to_next * share), cap):
                    lines.append(f"{p.display_name.upper()} grew to Lv {p.level}!")
                    lines.extend(movelib.learn_new_moves(self.game, p, old))
        self._heal_all()  # after any level-ups, so the new max HP is full too
        if share:
            lines.append("Your Pokemon gained experience from the hearty meal!")
        if name == "Charizard":
            lines.append("A Charizard Class curry! You're a true curry master!")
            self.story.story_flags["made_charizard_curry"] = True
        self.game.data.save()
        self.say(lines, self.show_menu)

    def leave(self):
        self.set_buttons([])
        if self.math_ui and self.math_ui in self.game.ui_manager.elements:
            self.game.ui_manager.elements.remove(self.math_ui)
        if hasattr(self.previous_state, "is_resuming"):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def update(self):
        super().update()
        if self.phase == "STIR" and self.time_left() <= 0:
            self._next("The bottom scorched a little...")

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        self.say(["You set up camp. Your Pokemon gather around the tent!"], self.show_menu)

    def draw(self):
        screen = self.game.screen
        top = self.box_rect.top
        w = self.game.width
        screen.fill((25, 35, 70))
        rnd = random.Random(7)
        for _ in range(60):
            pygame.draw.circle(screen, (230, 230, 255), (rnd.randrange(w), rnd.randrange(int(top * 0.5))), 1)
        pygame.draw.rect(screen, (50, 95, 55), (0, int(top * 0.55), w, top))
        # Tent
        tx, ty = int(w * 0.25), int(top * 0.75)
        pygame.draw.polygon(screen, (210, 80, 60), [(tx - 150, ty), (tx + 150, ty), (tx, ty - 190)])
        pygame.draw.polygon(screen, (60, 30, 30), [(tx - 35, ty), (tx + 35, ty), (tx, ty - 90)])
        # Campfire with a flickering flame and the pot
        fx, fy = w // 2, int(top * 0.8)
        for i in range(3):
            pygame.draw.line(screen, (110, 70, 40), (fx - 50, fy + 10 - i * 4), (fx + 50, fy - 10 + i * 4), 8)
        flick = 6 * math.sin(pygame.time.get_ticks() / 90)
        pygame.draw.polygon(screen, (255, 140, 30), [(fx - 35, fy), (fx + 35, fy), (fx, fy - 80 - flick)])
        pygame.draw.polygon(screen, (255, 220, 80), [(fx - 18, fy), (fx + 18, fy), (fx, fy - 45 - flick)])
        if self.phase in ("COOK", "STIR"):
            pygame.draw.ellipse(screen, (40, 40, 45), (fx - 90, fy - 150, 180, 90))
            pygame.draw.ellipse(screen, (200, 130, 40), (fx - 75, fy - 140, 150, 50))
        # The party around the fire
        team = [p for p in self.story.player_team if p and p.image]
        for i, p in enumerate(team):
            img = pygame.transform.scale(p.image, (110, 110))
            x = int(w * 0.62) + (i % 3) * 120
            y = int(top * 0.5) + (i // 3) * 110 + int(4 * math.sin(pygame.time.get_ticks() / 300 + i))
            screen.blit(img, (x, y))
        cx = w // 2
        Utils.draw_text_outline(screen, "CAMP", self.game.assets.fonts["big"], GOLD, cx, 50)
        if self.phase == "BERRIES":
            msg = f"Add up to {MAX_BERRIES} berries (or none), then COOK!"
            Utils.draw_text_outline(screen, msg, self.game.assets.fonts["small"], WHITE, cx, 100)
        if self.phase == "STIR":
            ratio = self.time_left() / STIR_TIME_MS
            bar = pygame.Rect(cx - 250, 95, 500, 22)
            pygame.draw.rect(screen, BLACK, bar, border_radius=8)
            fill = bar.copy()
            fill.width = int(bar.width * ratio)
            pygame.draw.rect(screen, GREEN if ratio > 0.5 else GOLD if ratio > 0.25 else RED, fill, border_radius=8)
            Utils.draw_text_outline(screen, f"STIR {self.stir + 1}/{STIRS}", self.game.assets.fonts["small"],
                                    WHITE, cx, 140)
        if not self.dialogue_box.visible and self.phase != "STIR":
            Utils.draw_classic_panel(screen, *self.box_rect)
        self.game.ui_manager.draw(screen)
