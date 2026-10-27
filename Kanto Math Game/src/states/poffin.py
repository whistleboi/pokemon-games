# [REF-0073: Poffin House and Poffin Case]
"""
Hearthome's Poffin House: pick up to three different berries, then stir the
batter through three stages by answering math problems before the timer runs
out. Right answers stir, wrong ones spill and slow ones burn; the result sets
the Poffin's level and smoothness. The Poffin Case feeds Poffins to Pokemon.
"""
import math
import pygame

from src.states.base import GameState
from src.ui.dialogue import ClassicDialogueBox
from src.ui.widgets import Button, MathBattleUI
from src.utils import Utils
from src.config import WHITE, BLACK, GOLD, GRAY, RED, GREEN
from src.pokemon.poffin import (
    BERRIES, FLAVORS, FLAVOR_COLOR, COOK_STAGES, STIRS_PER_STAGE, MAX_BERRIES_PER_POFFIN, MAX_POFFINS,
    BASIC_BERRIES, berry_name, berry_label, cook, poffin_label, poffin_color, feed_poffin,
)


def _kitchen(surface, width, height):
    surface.fill((70, 45, 35))
    pygame.draw.rect(surface, (120, 85, 60), (0, int(height * 0.55), width, height))
    for x in range(0, width, 80):
        pygame.draw.line(surface, (95, 65, 45), (x, int(height * 0.55)), (x, height), 2)
    pygame.draw.rect(surface, (230, 210, 170), (0, 0, width, 30))


def _button_row(game, specs, top, width=230, height=60, per_row=4):
    """specs: (text, callback, color, icon). Returns the Buttons laid out centred in rows."""
    buttons = []
    for r in range(0, len(specs), per_row):
        row = specs[r:r + per_row]
        total = len(row) * (width + 14) - 14
        x = game.width // 2 - total // 2
        for i, (text, cb, color, icon) in enumerate(row):
            buttons.append(Button((x + i * (width + 14), top + (r // per_row) * (height + 10), width, height),
                                  text, game.assets.fonts["caption"], cb, autosize=False,
                                  bg_color=color or (60, 90, 200), icon=icon))
    return buttons


class _MenuState(GameState):
    """Shared plumbing: a dialogue box plus a set of menu buttons."""

    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.story = game.story_manager
        self.box_rect = Utils.get_full_dialogue_rect(game)
        self.dialogue_box = ClassicDialogueBox(self.box_rect, [], game.assets.fonts["med"], visible=False)
        self.buttons = []

    def set_buttons(self, buttons):
        for btn in self.buttons:
            if btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)
        self.buttons = buttons
        for btn in buttons:
            self.game.ui_manager.add_element(btn)

    def say(self, lines, then):
        self.set_buttons([])
        self.dialogue_box.reset(lines)
        self.dialogue_box.callback = then

    def icon(self, item):
        img = self.game.assets.get_item_image(item)
        return pygame.transform.scale(img, (32, 32)) if img else None

    def handle_events(self, events):
        pass

    def update(self):
        self.dialogue_box.update()


# ---------------------------------------------------------------------------
class PoffinHouseState(_MenuState):
    def __init__(self, game, previous_state):
        super().__init__(game, previous_state)
        self.npc_sprite = game.assets.get_trainer_image("beauty.png")
        self.pending = self._welcome()

    def _welcome(self):
        flags, inv = self.story.story_flags, self.story.inventory
        if flags.get("poffin_case_received"):
            return ["Welcome back to the Poffin House!", "Shall we cook something tasty?"]
        flags["poffin_case_received"] = True
        inv["POFFIN_CASE"] = 1
        lines = ["Welcome to the Poffin House!",
                 "Poffins are treats cooked from berries. Pokemon adore them!",
                 "Each flavor raises a contest condition: Spicy for Cool, Dry for Beauty,",
                 "Sweet for Cute, Bitter for Smart and Sour for Tough.",
                 "Stir by answering quickly and correctly. Slow stirs burn, wrong ones spill!",
                 "And never use the same berry twice in one batch. It turns out foul!",
                 "Here, take this POFFIN CASE to keep your Poffins in."]
        if not flags.get("has_berry_pouch"):
            flags["has_berry_pouch"] = True
            inv["BERRY_POUCH"] = 1
            for b in BASIC_BERRIES:
                inv[b] = inv.get(b, 0) + 2
            lines.append("You don't have berries? Have a BERRY POUCH and a few to start!")
        lines.append("You received the POFFIN CASE!")
        return lines

    def show_menu(self):
        self.dialogue_box.set_visibility(False)
        self.set_buttons(_button_row(self.game, [
            ("COOK POFFINS", self.cook, (200, 110, 60), self.icon("POFFIN_CASE")),
            ("POFFIN CASE", self.open_case, (170, 120, 200), None),
            ("LEAVE", self.leave, RED, None)], self.box_rect.top + 45))

    def cook(self):
        if not any(self.story.inventory.get(b, 0) for b in BERRIES):
            self.say(["You don't have any berries!",
                      "Pick them from berry trees on Sinnoh's routes, or buy some in Floaroma."],
                     self.show_menu)
            return
        if len(self.story.poffins) >= MAX_POFFINS:
            self.say(["Your Poffin Case is full! Feed some Poffins to your Pokemon first."], self.show_menu)
            return
        self.set_buttons([])
        self.game.change_state(PoffinCookState(self.game, self))

    def open_case(self):
        self.set_buttons([])
        self.game.change_state(PoffinCaseState(self.game, self))

    def leave(self):
        self.set_buttons([])
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        if self.pending:
            lines, self.pending = self.pending, None
            self.say(lines, self.show_menu)
        else:
            self.show_menu()

    def draw(self):
        _kitchen(self.game.screen, self.game.width, self.box_rect.top)
        Utils.draw_text_outline(self.game.screen, "POFFIN HOUSE", self.game.assets.fonts["big"], GOLD,
                                self.game.width // 2, 80)
        if self.npc_sprite:
            img = pygame.transform.smoothscale(self.npc_sprite, (240, 240))
            self.game.screen.blit(img, img.get_rect(midbottom=(self.game.width // 2, self.box_rect.top - 10)))
        if not self.dialogue_box.visible:
            Utils.draw_textbox(self.game.screen, *self.box_rect)
        self.game.ui_manager.draw(self.game.screen)


# ---------------------------------------------------------------------------
class PoffinCookState(_MenuState):
    def __init__(self, game, house):
        super().__init__(game, house)
        self.house = house
        self.phase = "SELECT"
        self.selected = []
        self.page = 0
        self.math_ui = None

    # -- choosing berries -------------------------------------------------
    def owned_berries(self):
        return [b for b in BERRIES if self.story.inventory.get(b, 0) > 0]

    def show_select(self):
        self.phase = "SELECT"
        self.dialogue_box.set_visibility(False)
        owned = self.owned_berries()
        per_page = 8
        self.page = min(self.page, max(0, (len(owned) - 1) // per_page))
        specs = []
        for b in owned[self.page * per_page:(self.page + 1) * per_page]:
            left = self.story.inventory[b] - self.selected.count(b)
            mark = "> " if b in self.selected else ""
            color = FLAVOR_COLOR[max(BERRIES[b], key=BERRIES[b].get)]
            specs.append((f"{mark}{berry_name(b)} x{left}", (lambda b=b: self.toggle(b)), color, self.icon(b)))
        buttons = _button_row(self.game, specs, self.box_rect.top + 14, width=270, height=56)
        y = self.box_rect.top - 76
        controls = [("COOK!", self.begin_cooking, GREEN if self.selected else GRAY, None),
                    ("BACK", self.back, RED, None)]
        if len(owned) > per_page:
            controls.insert(1, ("MORE BERRIES", self.next_page, (90, 90, 140), None))
        buttons += _button_row(self.game, controls, y, width=200, height=56)
        self.set_buttons(buttons)

    def toggle(self, berry):
        if berry in self.selected:
            self.selected.remove(berry)
        elif len(self.selected) < MAX_BERRIES_PER_POFFIN:
            self.selected.append(berry)
        self.show_select()

    def next_page(self):
        self.page = (self.page + 1) % max(1, math.ceil(len(self.owned_berries()) / 8))
        self.show_select()

    def back(self):
        self.set_buttons([])
        self.game.change_state(self.house)

    # -- cooking -----------------------------------------------------------
    def begin_cooking(self):
        if not self.selected:
            return
        inv = self.story.inventory
        for b in self.selected:
            inv[b] -= 1
            if inv[b] <= 0:
                del inv[b]
        self.berries = list(self.selected)
        self.selected = []
        self.stir = 0
        self.good = self.quick = self.mistakes = 0
        self.last_result = ""
        self.phase = "COOK"
        names = ", ".join(berry_name(b) for b in self.berries)
        self.say([f"Into the pot: {names}!", COOK_STAGES[0][0]], self.ask)

    def stage(self):
        return min(self.stir // STIRS_PER_STAGE, len(COOK_STAGES) - 1)

    def ask(self):
        self.dialogue_box.set_visibility(False)
        play = self.game.states["play"]
        self.problem, self.answer, self.options = play.generate_math_set(0, num_options=4)
        if self.math_ui and self.math_ui in self.game.ui_manager.elements:
            self.game.ui_manager.elements.remove(self.math_ui)
        self.math_ui = MathBattleUI(self.game, self.problem, self.options, self.on_answer)
        self.game.ui_manager.add_element(self.math_ui)
        self.limit = COOK_STAGES[self.stage()][1]
        self.asked_at = pygame.time.get_ticks()
        self.phase = "STIR"

    def time_left(self):
        return max(0, self.limit - (pygame.time.get_ticks() - self.asked_at))

    def on_answer(self, index):
        if self.phase != "STIR":
            return
        elapsed = pygame.time.get_ticks() - self.asked_at
        if self.options[index] != self.answer:
            self.mistakes += 1
            msg = "Oops! Some batter spilled out!"
        elif elapsed > self.limit:
            self.mistakes += 1
            msg = "Too slow... the batter burned a little!"
        else:
            self.good += 1
            if elapsed <= self.limit / 2:
                self.quick += 1
                msg = "Perfect stir!"
            else:
                msg = "Nice stir!"
        self._next_stir(msg)

    def _next_stir(self, msg):
        self.math_ui.set_visibility(False)
        self.phase = "COOK"
        self.last_result = msg
        before = self.stage()
        self.stir += 1
        if self.stir >= STIRS_PER_STAGE * len(COOK_STAGES):
            self.say([msg], self.finish)
        elif self.stage() != before:
            self.say([msg, COOK_STAGES[self.stage()][0]], self.ask)
        else:
            self.say([msg], self.ask)

    def finish(self):
        poffin = cook(self.berries, self.good, self.quick, self.mistakes)
        self.story.poffins.append(poffin)
        flav = ", ".join(f"{f.title()} {v}" for f, v in poffin["flavors"].items())
        lines = [f"You made a {poffin['name']}! (Level {poffin['level']})", f"Flavors: {flav}."]
        if poffin["name"] == "Foul Poffin":
            lines.append("Hmm... use different berries and stir carefully next time.")
        elif poffin["name"] == "Mild Poffin":
            lines.append("A Mild Poffin! That's master-chef quality!")
            self.story.story_flags["made_mild_poffin"] = True
        lines.append("It went into your POFFIN CASE.")
        self.game.data.save()
        self.say(lines, self.show_select if self.owned_berries() else self.back)

    def update(self):
        super().update()
        if self.phase == "STIR" and self.time_left() <= 0:
            self.mistakes += 1
            self.phase = "COOK"
            self._next_stir("Too slow... the batter burned a little!")

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        if self.phase == "SELECT":
            self.show_select()

    def draw(self):
        screen = self.game.screen
        top = self.box_rect.top
        _kitchen(screen, self.game.width, top)
        cx, cy = self.game.width // 2, int(top * 0.52)
        # Pot and batter (mixed from the chosen berries' flavors).
        pygame.draw.ellipse(screen, (40, 40, 45), (cx - 230, cy - 120, 460, 260))
        pygame.draw.ellipse(screen, (90, 90, 100), (cx - 210, cy - 105, 420, 220), 6)
        berries = self.berries if self.phase in ("COOK", "STIR") else self.selected
        if berries:
            cols = [FLAVOR_COLOR[max(BERRIES[b], key=BERRIES[b].get)] for b in berries]
            mix = tuple(sum(c[i] for c in cols) // len(cols) for i in range(3))
            pygame.draw.ellipse(screen, mix, (cx - 190, cy - 90, 380, 190))
            # Spoon swirls faster as the batter thickens.
            speed = 1 + self.stage() if self.phase in ("COOK", "STIR") else 0.5
            ang = pygame.time.get_ticks() / 1000 * speed * 2
            sx, sy = cx + int(120 * math.cos(ang)), cy + int(55 * math.sin(ang))
            pygame.draw.line(screen, (200, 170, 120), (sx, sy), (sx + 40, sy - 170), 10)
            pygame.draw.circle(screen, (200, 170, 120), (sx, sy), 14)
        font = self.game.assets.fonts["caption"]
        if self.phase == "SELECT":
            msg = f"Choose up to {MAX_BERRIES_PER_POFFIN} different berries, then COOK!"
            Utils.draw_text_outline(screen, msg, self.game.assets.fonts["label"], WHITE, cx, 60)
            if self.selected:
                text = "In the pot: " + ", ".join(f"{berry_name(b)} ({berry_label(b)})" for b in self.selected)
                Utils.draw_text_outline(screen, text, font, GOLD, cx, 100)
        else:
            stage_no = self.stage() + 1
            Utils.draw_text_outline(screen, f"STAGE {stage_no}/{len(COOK_STAGES)}", self.game.assets.fonts["label"],
                                    WHITE, cx, 60)
            if self.phase == "STIR":
                ratio = self.time_left() / self.limit
                bar = pygame.Rect(cx - 250, 95, 500, 22)
                pygame.draw.rect(screen, BLACK, bar, border_radius=8)
                fill = bar.copy()
                fill.width = int(bar.width * ratio)
                color = GREEN if ratio > 0.5 else GOLD if ratio > 0.25 else RED
                pygame.draw.rect(screen, color, fill, border_radius=8)
            score = f"Stirs {self.good}   Perfect {self.quick}   Spills/Burns {self.mistakes}"
            Utils.draw_text_outline(screen, score, font, WHITE, cx, top - 30)
        if not self.dialogue_box.visible and self.phase != "STIR":
            Utils.draw_textbox(screen, *self.box_rect)
        self.game.ui_manager.draw(screen)


# ---------------------------------------------------------------------------
class PoffinCaseState(_MenuState):
    """List Poffins; pick one, then a party Pokemon to feed it to."""
    PER_PAGE = 8

    def __init__(self, game, previous_state):
        super().__init__(game, previous_state)
        self.page = 0
        self.chosen = None
        self.pending = None

    def show_list(self):
        self.dialogue_box.set_visibility(False)
        poffins = self.story.poffins
        if not poffins:
            self.say(["Your POFFIN CASE is empty.", "Cook some at the Poffin House in Hearthome City!"], self.back)
            return
        pages = max(1, math.ceil(len(poffins) / self.PER_PAGE))
        self.page %= pages
        start = self.page * self.PER_PAGE
        specs = [(poffin_label(p), (lambda i=start + k: self.choose(i)), poffin_color(p), None)
                 for k, p in enumerate(poffins[start:start + self.PER_PAGE])]
        buttons = _button_row(self.game, specs, 140, width=260, height=60)
        controls = [("BACK", self.back, RED, None)]
        if pages > 1:
            controls.insert(0, (f"PAGE {self.page + 1}/{pages}", self.next_page, (90, 90, 140), None))
        buttons += _button_row(self.game, controls, self.box_rect.top + 45, width=220)
        self.set_buttons(buttons)

    def next_page(self):
        self.page += 1
        self.show_list()

    def choose(self, index):
        from src.states.systems import PokemonPartyMenuState
        self.chosen = index
        self.set_buttons([])
        self.game.change_state(PokemonPartyMenuState(self.game, previous_state=self, context="use_item",
                                                     on_select=self.feed))

    def feed(self, slot):
        team = self.story.player_team
        poffin = self.story.poffins[self.chosen]
        lines = ["Nothing happened."]
        if slot < len(team):
            ate, lines = feed_poffin(team[slot], poffin)
            if ate:
                self.story.poffins.pop(self.chosen)
                if self.game.assets.heal_sfx:
                    self.game.assets.heal_sfx.play()
        self.pending = lines
        self.game.change_state(self)

    def back(self):
        self.set_buttons([])
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        if self.pending:
            lines, self.pending = self.pending, None
            self.say(lines, self.show_list)
        else:
            self.show_list()

    def draw(self):
        screen = self.game.screen
        screen.fill((45, 30, 55))
        Utils.draw_text_outline(screen, "POFFIN CASE", self.game.assets.fonts["big"], GOLD, self.game.width // 2, 60)
        font = self.game.assets.fonts["caption"]
        legend_x = self.game.width // 2 - 380
        for i, f in enumerate(FLAVORS):
            pygame.draw.circle(screen, FLAVOR_COLOR[f], (legend_x + i * 160, 108), 9)
            screen.blit(font.render(f.title(), True, WHITE), (legend_x + 16 + i * 160, 100))
        if not self.dialogue_box.visible:
            Utils.draw_textbox(screen, *self.box_rect)
        self.game.ui_manager.draw(screen)
