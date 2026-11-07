"""The Donut Shop in Hyperspace Lumiose (Jordan, 11-06): pick 3 berries, answer a math question to bake,
and the donut opens a Hyperspace zone (its taste picks which; its stars how deep: src/world/donuts.py).
Plain berries come free from the basket; star berries are the ones you found in Hyperspace."""
import math

import pygame

from src.states.poffin import _MenuState, _button_row
from src.ui.widgets import MathBattleUI
from src.utils import Utils
from src.config import GOLD, GREEN, RED
from src.world import donuts


def draw_donut(screen, center, radius, donut):
    """A donut: its ring in its taste's colour (a rainbow's in bands), glaze on top, a sprinkle star each."""
    cx, cy = center
    t = pygame.time.get_ticks()
    pygame.draw.circle(screen, (176, 120, 70), (cx, cy + 6), radius)  # the dough
    if donut.get("recipe") == "rainbow":
        cols = [donuts.TASTE_COLOR[donuts.taste(b)] for b in donut.get("berries", [])] or [GOLD]
        for i in range(36):
            a0, a1 = i * math.tau / 36, (i + 1) * math.tau / 36
            col = cols[i % len(cols)]
            pts = [(cx, cy)] + [(cx + math.cos(a) * (radius - 4), cy + math.sin(a) * (radius - 4)) for a in (a0, a1)]
            pygame.draw.polygon(screen, col, pts)
    else:
        col = donuts.TASTE_COLOR.get(donut.get("taste"), (240, 200, 160))
        if donut.get("recipe") == "plain" and donut.get("name", "").startswith("Toasty"):
            col = tuple(int(c * 0.7) for c in col)
        pygame.draw.circle(screen, col, (cx, cy), radius - 4)
    pygame.draw.circle(screen, (255, 255, 255), (cx - radius // 3, cy - radius // 3), radius // 6)  # shine
    pygame.draw.circle(screen, (176, 120, 70), (cx, cy + 4), radius // 3)  # the hole
    pygame.draw.circle(screen, (70, 45, 35), (cx, cy + 4), radius // 3 - 6)
    for k in range(donut.get("stars", 0)):  # a gold star sprinkle each
        a = t / 900 + k * math.tau / 3
        sx, sy = cx + math.cos(a) * radius * 0.68, cy + math.sin(a) * radius * 0.68
        Utils.draw_star(screen, GOLD, (int(sx), int(sy)), max(8, radius // 7))


class DonutShopState(_MenuState):
    def __init__(self, game, town):
        super().__init__(game, town)
        self.town = town
        self.selected = []
        self.math_ui = None
        self.phase = "PICK"
        self.donut = self.story.story_flags.get(donuts.FLAG) or None
        first = not self.story.story_flags.get("donut_shop_met")
        self.story.story_flags["donut_shop_met"] = True
        self.pending = ["Baker: Welcome to the Donut Shop!",
                        "Pick 3 berries and bake a donut. Its taste opens a Hyperspace zone!",
                        "Plain berries are free from the basket. Star berries, the shiny ones, you find in Hyperspace.",
                        "Each star berry adds a star, and deeper zones need more stars.",
                        "Secret recipes: 3 of the same taste makes a PERFECT donut (+1 star),",
                        "and 3 different tastes makes a RAINBOW donut (more time on each floor)!"] if first else None

    # -- picking
    def star_berries(self):
        inv = self.story.inventory
        return [b for b in donuts.STAR if inv.get(b, 0) > 0]

    def show_pick(self):
        self.phase = "PICK"
        self.dialogue_box.set_visibility(False)
        specs = [(f"{b.replace('_BERRY', '').title()} ({donuts.PLAIN[b].title()})", (lambda b=b: self.add(b)),
                  donuts.TASTE_COLOR[donuts.PLAIN[b]], self.icon(b.lower().replace("_", "-"))) for b in donuts.PLAIN]
        inv = self.story.inventory
        specs += [(f"* {b.replace('_BERRY', '').title()} x{inv[b] - self.selected.count(b)}", (lambda b=b: self.add(b)),
                   (210, 170, 40), self.icon(b.lower().replace("_", "-"))) for b in self.star_berries()]
        btns = _button_row(self.game, specs, 300, width=230, height=56, per_row=5)
        ctrl = [("BAKE!", self.bake if len(self.selected) == 3 else None, GREEN if len(self.selected) == 3 else (110, 110, 120), None),
                ("CLEAR", self.clear, (90, 90, 140), None),
                ("ZONES", self.show_zones, (60, 120, 200), None),
                ("LEAVE", self.leave, RED, None)]
        if self.donut:
            ctrl.insert(0, ("GO IN!", self.go_in if donuts.zone_for(self.game, self.donut) else None, GOLD, None))
        btns += _button_row(self.game, ctrl, self.box_rect.top - 76, width=180, height=60, per_row=5)
        self.set_buttons(btns)

    def add(self, berry):
        if len(self.selected) >= 3:
            return
        if berry in donuts.STAR and self.selected.count(berry) >= self.story.inventory.get(berry, 0):
            return
        self.selected.append(berry)
        self.show_pick()

    def clear(self):
        self.selected = []
        self.show_pick()

    def show_zones(self):
        lines = []
        for key, area in donuts.zones(self.game):
            hs = area["hyperspace"]
            need = hs.get("stars", 0)
            lines.append(f"{hs['theme']}: a {hs['taste'].lower()} donut" + (f" with {need} star{'s' * (need > 1)}" if need else "") + ".")
        self.say(lines or ["No zones yet."], self.show_pick)

    # -- baking
    def bake(self):
        self.phase = "BAKE"
        self.set_buttons([])
        play = self.game.states["play"]
        self.problem, self.answer, self.options = play.generate_math_set(0, num_options=3)
        if self.math_ui and self.math_ui in self.game.ui_manager.elements:
            self.game.ui_manager.elements.remove(self.math_ui)
        self.math_ui = MathBattleUI(self.game, self.problem, self.options, self.on_answer)
        self.game.ui_manager.add_element(self.math_ui)

    def on_answer(self, index):
        if self.phase != "BAKE":
            return
        right = self.options[index] == self.answer
        self.math_ui.set_visibility(False)
        inv = self.story.inventory
        for b in self.selected:  # (the star berries are used up; the basket's are free)
            if b in donuts.STAR:
                inv[b] -= 1
                if inv[b] <= 0:
                    del inv[b]
        self.donut = donuts.bake(self.selected, burnt=not right)
        self.story.story_flags[donuts.FLAG] = self.donut
        self.selected = []
        self.phase = "DONE"
        zone = donuts.zone_for(self.game, self.donut)
        lines = ["Ding! The donut is ready!" if right else "Oops, it got a little toasty! It still works."]
        lines.append(f"You made a {self.donut['name']}" + (f" with {self.donut['stars']} star{'s' * (self.donut['stars'] != 1)}!" if self.donut["stars"] else "!"))
        if self.donut["recipe"] == "perfect":
            lines.append("A PERFECT donut! It earned an extra star!")
        elif self.donut["recipe"] == "rainbow":
            lines.append(f"A RAINBOW donut! {donuts.RAINBOW_SECONDS} more seconds on every floor!")
        if zone:
            lines.append(f"It opens {self.game.loader.area_data['STORY_PROGRESSION'][zone]['route_name']}! Tap GO IN! when you're ready.")
        else:
            need = next((a["hyperspace"]["stars"] for k, a in donuts.zones(self.game)
                         if a["hyperspace"]["taste"] == self.donut["taste"]), 0)
            lines.append(f"That zone needs {need} stars. Find star berries in Hyperspace, then bake again!")
        self.say(lines, self.show_pick)

    def go_in(self):
        zone = donuts.zone_for(self.game, self.donut or {})
        if not zone:
            return
        self.set_buttons([])
        self.game.change_state(self.town)
        self.town.go_to_area(zone, f"You took a bite of the {self.donut['name']}... Hyperspace opens up around you!")

    def leave(self):
        self.set_buttons([])
        self.game.change_state(self.town)

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        if self.pending:
            lines, self.pending = self.pending, None
            self.say(lines, self.show_pick)
        else:
            self.show_pick()

    def draw(self):
        screen, W = self.game.screen, self.game.width
        top = self.box_rect.top
        screen.fill((44, 26, 60))
        for y in range(0, top, 6):  # a purple Hyperspace shimmer behind the counter
            k = 0.5 + 0.5 * math.sin(y / 30 + pygame.time.get_ticks() / 700)
            pygame.draw.line(screen, (44 + int(30 * k), 26 + int(10 * k), 60 + int(50 * k)), (0, y), (W, y), 6)
        pygame.draw.rect(screen, (150, 100, 70), (0, top - 120, W, 120))
        Utils.draw_text_outline(screen, "DONUT SHOP", self.game.assets.fonts["big"], GOLD, W // 2, 52)
        # the bowl: the 3 berries picked so far
        bowl = pygame.Rect(0, 0, 420, 120)
        bowl.center = (W // 2 - 260, 190)
        pygame.draw.ellipse(screen, (230, 230, 240), bowl)
        pygame.draw.ellipse(screen, (120, 120, 140), bowl, 4)
        for i in range(3):
            slot = (bowl.x + 80 + i * 130, bowl.centery)
            pygame.draw.circle(screen, (200, 200, 214), slot, 34, 3)
            if i < len(self.selected):
                img = self.game.assets.get_item_image(self.selected[i].lower().replace("_", "-"))
                if img:
                    img = pygame.transform.scale(img, (60, 60))
                    screen.blit(img, img.get_rect(center=slot))
        if len(self.selected) == 3 and self.phase == "PICK":  # what it will make
            preview = donuts.bake(self.selected)
            Utils.draw_text_outline(screen, preview["name"] + f"  ({preview['stars']} star{'s' * (preview['stars'] != 1)})",
                                    self.game.assets.fonts["caption"], (255, 255, 255), bowl.centerx, bowl.bottom + 22)
        if self.donut:  # the donut you have
            draw_donut(screen, (W // 2 + 300, 190), 80, self.donut)
            zone = donuts.zone_for(self.game, self.donut)
            where = self.game.loader.area_data["STORY_PROGRESSION"][zone]["route_name"] if zone else "needs more stars"
            Utils.draw_text_outline(screen, f"{self.donut['name']}: {where}", self.game.assets.fonts["caption"],
                                    (255, 255, 255), W // 2 + 300, 292)
        if not self.dialogue_box.visible and self.phase != "BAKE":
            Utils.draw_textbox(screen, *self.box_rect)
        self.game.ui_manager.draw(screen)
