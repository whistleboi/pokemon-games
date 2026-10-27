# [REF-0074: Pokemon-Amie]
"""
Pokemon-Amie (Kalos Pokemon Centers): choose a party Pokemon, then PET it or PLAY a
quick math game with it. Both raise its affection (src/pokemon/affection.py), up to
a daily limit per Pokemon. Affection gives battle perks in every region.
"""
import math
import random
import pygame

from src.states.poffin import _MenuState, _button_row
from src.ui.widgets import MathBattleUI
from src.utils import Utils
from src.config import WHITE, BLACK, GOLD, RED, GREEN
from src.pokemon import affection

PLAY_ROUNDS = 3
PLAY_TIME_MS = 8000
PET_GAIN = 4
PLAY_GAIN, PLAY_QUICK_GAIN = 8, 12

PET_LINES = ("{n} closed its eyes happily.", "{n} nuzzled your hand!", "{n} wiggled with joy!",
             "{n} made a happy little sound.")
from src.ui.hearts import HEART_RED, HEART_EMPTY, draw_heart, draw_hearts  # noqa: F401 (shared)


class AmieState(_MenuState):
    def __init__(self, game, previous_state):
        super().__init__(game, previous_state)
        self.mon = None
        self.phase = "PICK"
        self.math_ui = None
        self.pending = None
        flags = self.story.story_flags
        if not flags.get("amie_explained"):
            flags["amie_explained"] = True
            self.pending = ["Welcome to Pokemon-Amie!",
                            "Pet your Pokemon or play a math game with it to raise its affection.",
                            "Pokemon that love you try harder in battle: they earn more XP, can hang on",
                            "after a big hit, dodge attacks, shake off status and land more critical hits!"]

    # -- choosing a Pokemon ----------------------------------------------
    def show_party(self):
        self.phase = "PICK"
        self.mon = None
        self.dialogue_box.set_visibility(False)
        team = [p for p in self.story.player_team if p]
        specs = [(f"{p.display_name.upper()}  Lv{p.level}", (lambda p=p: self.pick(p)), (200, 90, 140), None)
                 for p in team]
        buttons = _button_row(self.game, specs, 150, width=270, height=60, per_row=3)
        buttons += _button_row(self.game, [("LEAVE", self.leave, RED, None)], self.box_rect.top + 45, width=200)
        self.set_buttons(buttons)

    def pick(self, poke):
        self.mon = poke
        self.show_actions()

    def show_actions(self):
        self.phase = "WITH"
        self.dialogue_box.set_visibility(False)
        self.set_buttons(_button_row(self.game, [
            ("PET", self.pet, (230, 120, 160), None),
            ("PLAY (MATH)", self.play, (90, 150, 230), None),
            ("OTHER POKEMON", self.show_party, (120, 100, 160), None),
            ("LEAVE", self.leave, RED, None)], self.box_rect.top + 45, width=230))

    def _limit_lines(self):
        return [f"{self.mon.display_name.upper()} has had lots of attention today.",
                "Come back tomorrow to bond some more!"]

    # -- pet ---------------------------------------------------------------
    def pet(self):
        name = self.mon.display_name.upper()
        before = affection.hearts(self.mon)
        got = affection.add(self.mon, PET_GAIN)
        if not got:
            self.say(self._limit_lines(), self.show_actions)
            return
        lines = [random.choice(PET_LINES).format(n=name)]
        lines += self._heart_lines(before)
        self.say(lines, self.show_actions)

    def _heart_lines(self, before):
        after = affection.hearts(self.mon)
        if after > before:
            return [f"{self.mon.display_name.upper()}'s affection rose to {after} heart{'s' if after > 1 else ''}!"]
        return []

    # -- play: a short timed math game -------------------------------------
    def play(self):
        if affection.gain_today(self.mon) >= affection.DAILY_CAP:
            self.say(self._limit_lines(), self.show_actions)
            return
        self.round = 0
        self.earned = 0
        self.before = affection.hearts(self.mon)
        self.say([f"{self.mon.display_name.upper()} wants to play!",
                  "Answer quickly. The faster you are, the happier it gets!"], self.ask)

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
        self.phase = "PLAY"

    def time_left(self):
        return max(0, PLAY_TIME_MS - (pygame.time.get_ticks() - self.asked_at))

    def on_answer(self, index):
        if self.phase != "PLAY":
            return
        elapsed = pygame.time.get_ticks() - self.asked_at
        name = self.mon.display_name.upper()
        if self.options[index] != self.answer:
            msg = f"{name} tilted its head, confused."
        elif elapsed > PLAY_TIME_MS:
            msg = f"{name} got a little bored waiting..."
        else:
            gain = PLAY_QUICK_GAIN if elapsed <= PLAY_TIME_MS / 2 else PLAY_GAIN
            got = affection.add(self.mon, gain)
            self.earned += got
            msg = f"{name} jumped for joy!" if gain == PLAY_QUICK_GAIN else f"{name} looks pleased!"
        self._next(msg)

    def _next(self, msg):
        self.math_ui.set_visibility(False)
        self.phase = "WAIT"
        self.round += 1
        if self.round >= PLAY_ROUNDS:
            lines = [msg, f"You played with {self.mon.display_name.upper()}! (+{self.earned} affection)"]
            lines += self._heart_lines(self.before)
            self.say(lines, self.show_actions)
        else:
            self.say([msg], self.ask)

    def leave(self):
        self.set_buttons([])
        if self.math_ui and self.math_ui in self.game.ui_manager.elements:
            self.game.ui_manager.elements.remove(self.math_ui)
        self.game.data.save()
        self.game.change_state(self.previous_state)

    def update(self):
        super().update()
        if self.phase == "PLAY" and self.time_left() <= 0:
            self._next(f"{self.mon.display_name.upper()} got a little bored waiting...")

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        if self.pending:
            lines, self.pending = self.pending, None
            self.say(lines, self.show_party)
        else:
            self.show_party()

    def draw(self):
        screen = self.game.screen
        top = self.box_rect.top
        screen.fill((255, 228, 236))
        pygame.draw.rect(screen, (250, 205, 220), (0, int(top * 0.7), self.game.width, top))
        for i in range(12):  # soft floating hearts
            t = pygame.time.get_ticks() / 1500 + i
            x = int((i * 113) % self.game.width)
            y = int(top * 0.7 - (t % 1) * top * 0.6)
            draw_heart(screen, x, y, 14, (255, 190, 210))
        cx = self.game.width // 2
        Utils.draw_text_outline(screen, "POKEMON-AMIE", self.game.assets.fonts["big"], GOLD, cx, 60)
        font = self.game.assets.fonts["label"]
        if self.mon is None:
            Utils.draw_text_outline(screen, "Who would you like to spend time with?", font, WHITE, cx, 110)
            # Hearts under each party button.
            for btn in self.buttons:
                for p in self.story.player_team:
                    if p and btn.text.startswith(p.display_name.upper() + "  "):
                        draw_hearts(screen, p, btn.rect.centerx, btn.rect.bottom + 16, size=16)
        else:
            img = self.mon.image
            if img:
                h = int(top * 0.5)
                bob = int(6 * math.sin(pygame.time.get_ticks() / 250))
                img = pygame.transform.scale(img, (int(img.get_width() * h / img.get_height()), h))
                screen.blit(img, img.get_rect(midbottom=(cx, int(top * 0.78) + bob)))
            Utils.draw_text_outline(screen, f"{self.mon.display_name.upper()} {affection.mood(self.mon)}",
                                    font, WHITE, cx, 110)
            draw_hearts(screen, self.mon, cx, int(top * 0.86))
            if self.phase == "PLAY":
                ratio = self.time_left() / PLAY_TIME_MS
                bar = pygame.Rect(cx - 250, 150, 500, 20)
                pygame.draw.rect(screen, BLACK, bar, border_radius=8)
                fill = bar.copy()
                fill.width = int(bar.width * ratio)
                pygame.draw.rect(screen, GREEN if ratio > 0.5 else GOLD if ratio > 0.25 else RED, fill,
                                 border_radius=8)
        if not self.dialogue_box.visible and self.phase != "PLAY":
            Utils.draw_textbox(screen, *self.box_rect)
        self.game.ui_manager.draw(screen)
