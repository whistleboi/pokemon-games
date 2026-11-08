"""Hyperspace Lumiose (Jordan, 11-06): Legends: Z-A's Hyperspace as our dungeons. You get in with a donut
(src/world/donuts.py, src/states/donut.py); each zone is three big open floors with nothing in the way of the
view, trainers and wild Pokemon of its theme. Each floor has a clock (180 seconds, a Rainbow donut's 30 more):
beat everyone on it before time runs out, then the way down opens. The last floor's clear wins Rare Candy and
star berries (the Mega Stones are where Legends: Z-A puts them, in Lumiose: dev/builders/place_kalos_mega_stones.py).

Battles here are the usual turn-based ones (the clock waits while you battle). Run out of Pokemon, or of
time, and you're back at the Hyperspace hub."""
import pygame

from src.config import FPS
from src.states.overworld.dungeon import DungeonState
from src.world import donuts

HUB = "HYPERSPACE_LUMIOSE"


class HyperspaceState(DungeonState):

    def __init__(self, game, restore_data=None, classic=False):
        if getattr(self, "_hs_ready", False):  # back from a battle's exit: the zone goes on as it was
            super().__init__(game, restore_data=restore_data, classic=classic)
            return
        super().__init__(game, restore_data=restore_data, classic=classic)
        self._hs_ready = True
        self.hs = self.area_data.get("hyperspace") or {}
        story = game.story_manager
        donut = story.story_flags.pop(donuts.FLAG, None) or {}  # (eaten on the way in)
        self.bonus = int(donut.get("bonus_seconds", 0)) if donut.get("taste") == self.hs.get("taste") else 0
        self._reset_clock()
        self.banner = 150

    # ---------------------------------------------------------------- the clock and the floors
    def _reset_clock(self):
        self.clock = (int(self.hs.get("seconds", 180)) + self.bonus) * FPS
        self.cleared_said = False

    def _enemies(self):
        return [m for m in self.run.floor.movers if m.kind in ("wild", "trainer")]

    def _stairs_blocked(self):
        left = len(self._enemies())
        if left:
            self.flash(f"Beat everyone on this floor first! ({left} left)")
            return True
        return False

    def _descend(self):
        super()._descend()
        self._reset_clock()

    def _collapse(self):
        self.mode = "MAP"
        self.say(["The Hyperspace zone is fading away...", "You were pulled back to the Hyperspace hub!"],
                 then=lambda: self._leave(HUB))

    def _floor_check(self):
        if self.cleared_said or self._enemies() or self.dialogue_box.visible:
            return
        self.cleared_said = True
        if self.run.index < self.run.n_floors - 1:
            self.flash("Floor clear! The way down is open!", 150)
            return
        story = self.game.story_manager
        stone = next((s for s in self.hs.get("stones", []) if story.inventory.get(s, 0) <= 0), None)
        lines = [f"You cleared {self.hs.get('theme', 'the zone')}!"]
        if stone:
            story.inventory[stone] = 1
            from src.pokemon import forms
            lines.append(f"You found a {forms.item_label(stone).upper()}! A new Mega Stone!")
        else:
            story.add_item("RARE_CANDY", 3)
            lines.append("You found 3 RARE CANDY!")
        berry = self.hs.get("star_berry")
        if berry:
            story.add_item(berry, 2)
            lines.append(f"You found 2 {berry.replace('_', ' ')} too! Star berries make stronger donuts.")
        self.say(lines, then=lambda: self._leave(HUB))

    # ---------------------------------------------------------------- the loop
    def update(self):
        super().update()
        if self.dialogue_box.visible:
            return
        if self.mode in ("MAP", "SPOTTED"):
            self.clock -= 1
            if self.clock <= 0:
                return self._collapse()
        if self.mode == "MAP":
            self._floor_check()

    def _draw_hud(self, screen):
        super()._draw_hud(screen)
        if not hasattr(self, "clock"):
            return
        fonts = self.game.assets.fonts
        secs = max(0, self.clock // FPS)
        text = f"TIME {secs // 60}:{secs % 60:02d}   LEFT {len(self._enemies())}"
        t = fonts["label"].render(text, True, (255, 255, 255))
        pill = t.get_rect(topleft=(24, self._minimap_rect().bottom + 14)).inflate(26, 10)  # (under the mini-map)
        hurry = secs <= 30 and (pygame.time.get_ticks() // 300) % 2
        pygame.draw.rect(screen, (150, 30, 40) if hurry else (40, 24, 70), pill, border_radius=10)
        pygame.draw.rect(screen, (200, 120, 255), pill, 2, border_radius=10)
        screen.blit(t, t.get_rect(center=pill.center))
