# [REF-0077: Hoenn version choice]
"""Choose Omega Ruby (Team Magma, Groudon) or Alpha Sapphire (Team Aqua, Kyogre), and Wally's Ralts catch."""
import math

import pygame

from src.states.poffin import _MenuState, _button_row
from src.utils import Utils
from src.config import WHITE, GOLD
from src.world import hoenn


class HoennVersionState(_MenuState):
    def __init__(self, game, next_state_factory):
        super().__init__(game, None)
        self.next_state_factory = next_state_factory
        self.art = {}
        for key, v in hoenn.VERSIONS.items():
            img = game.assets.get_pokemon_image(v["legend_id"], "primal", False, placeholder=False)
            img = img or game.assets.get_pokemon_image(v["legend_id"], "normal", False)
            self.art[key] = pygame.transform.scale(img, (260, 260))

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        self.say(["Welcome to Hoenn!",
                  "Two teams want to reshape the world with the ancient Pokemon Groudon and Kyogre.",
                  "Which story will you play?"], self.show_choices)

    def show_choices(self):
        self.dialogue_box.set_visibility(False)
        specs = [(v["title"], (lambda k=key: self.choose(k)), v["color"], None) for key, v in hoenn.VERSIONS.items()]
        self.set_buttons(_button_row(self.game, specs, self.box_rect.top + 40, width=320, height=70))

    def choose(self, key):
        story = self.game.story_manager
        story.story_flags["hoenn_version"] = key
        hoenn.apply_version(self.game)
        v = hoenn.VERSIONS[key]
        self.say([f"You chose {v['title']}!",
                  f"{v['team']} and its leader {v['leader']} want to awaken {v['legend']} to {v['goal']}.",
                  "Good luck on your journey!"], self.finish)

    def finish(self):
        self.set_buttons([])
        self.game.change_state(self.next_state_factory())

    def draw(self):
        screen = self.game.screen
        w = self.game.width
        screen.fill((20, 20, 35))
        half = w // 2
        pygame.draw.rect(screen, (90, 20, 20), (0, 0, half, self.box_rect.top))
        pygame.draw.rect(screen, (20, 40, 100), (half, 0, w - half, self.box_rect.top))
        Utils.draw_text_outline(screen, "CHOOSE YOUR STORY", self.game.assets.fonts["big"], GOLD, half, 50)
        for i, (key, v) in enumerate(hoenn.VERSIONS.items()):
            cx = half // 2 + i * half
            img = self.art[key]
            screen.blit(img, img.get_rect(center=(cx, 250)))
            Utils.draw_text_outline(screen, v["title"], self.game.assets.fonts["label"], WHITE, cx, 410)
            Utils.draw_text_outline(screen, f"{v['team']}  -  {v['legend']}", self.game.assets.fonts["caption"],
                                    WHITE, cx, 455)
        if not self.dialogue_box.visible:
            Utils.draw_textbox(screen, *self.box_rect)
        self.game.ui_manager.draw(screen)


class WallyCatchState(_MenuState):
    """Wally catches his first Pokemon on Route 102 with Norman's Zigzagoon (a scene that plays
    itself, like the games' catching tutorial): Wally's back sprite stands on the player's side,
    a wild Ralts appears, Zigzagoon tackles it, Wally throws a Poke Ball and it's caught.
    Tapping speeds it up; done() runs at the end."""

    RALTS = 280
    WAIT = 70  # frames each finished line stays up before the scene moves on

    def __init__(self, game, done):
        super().__init__(game, None)
        self.done = done
        top = self.box_rect.top
        bg = game.assets.get_random_battle_background("grass", "HOENN_ROUTE_102")
        self.bg = pygame.transform.scale(bg, (game.width, top)) if bg else None
        wally = game.assets.get_trainer_image("wally_back.png")
        h = int(top * 0.6)
        self.wally = (pygame.transform.scale(wally, (int(wally.get_width() * h / wally.get_height()), h))
                      if wally else None)
        from src.pokemon.data import Pokemon
        self.ralts = Pokemon(game.loader.fetch_specific(self.RALTS), game.assets, size_mult=3.125).image
        self.ball = pygame.transform.scale(game.assets.ball_imgs[0], (40, 40))
        self.ralts_pos = (int(game.width * 0.73), int(game.height * 0.39))  # where battles put a foe
        self.hand_pos = (int(game.width * 0.3), top - h + 40)
        self.hp, self.hp_to = 1.0, 1.0
        self.ralts_shown, self.ball_t = True, None
        self.step, self.wait, self.frame = -1, 0, 0
        self.steps = [
            ("A wild RALTS appeared!", None),
            ("WALLY: I-I'll do my best... Zigzagoon, please help me!", None),
            ("ZIGZAGOON used TACKLE!", self._tackle),
            ("WALLY threw a POKE BALL!", self._throw),
            ("...", None),
            ("Gotcha! RALTS was caught!", None),
            ("WALLY: I did it... I really caught a Pokemon!", None),
        ]

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        self.next_step()

    def next_step(self):
        self.step += 1
        if self.step >= len(self.steps):
            if self.dialogue_box in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(self.dialogue_box)
            self.done()
            return
        text, action = self.steps[self.step]
        if action:
            action()
        self.wait = 0
        self.dialogue_box.reset([text])
        self.dialogue_box.callback = self.next_step
        self.dialogue_box.set_visibility(True)

    def _tackle(self):
        self.hp_to = 0.3

    def _throw(self):
        self.ball_t = 0.0

    def handle_events(self, events):
        pass

    def update(self):
        super().update()
        self.frame += 1
        if self.hp > self.hp_to:
            self.hp = max(self.hp_to, self.hp - 0.02)
        if self.ball_t is not None and self.ball_t < 1.0:
            self.ball_t = min(1.0, self.ball_t + 1 / 40)
            if self.ball_t >= 1.0:
                self.ralts_shown = False
        box = self.dialogue_box
        if box.is_waiting_for_click and not box.is_finished:
            self.wait += 1
            if self.wait >= self.WAIT:
                self.wait = 0
                box.advance()

    def _ball_pos(self):
        (x0, y0), (x1, y1) = self.hand_pos, self.ralts_pos
        t = self.ball_t or 0.0
        return (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t - math.sin(t * math.pi) * 160)

    def draw(self):
        screen = self.game.screen
        top = self.box_rect.top
        if self.bg:
            screen.blit(self.bg, (0, 0))
        else:
            screen.fill((120, 190, 110))
        if self.ralts and self.ralts_shown:
            screen.blit(self.ralts, self.ralts.get_rect(center=self.ralts_pos))
        if self.wally:
            screen.blit(self.wally, self.wally.get_rect(midbottom=(int(self.game.width * 0.25), top)))
        # The wild Ralts's HP bar.
        fonts = self.game.assets.fonts
        from src.ui import theme
        panel = pygame.Rect(26, 26, 420, 96)  # the battle screen's info box
        pygame.draw.rect(screen, theme.INFOBOX, panel, border_radius=10)
        pygame.draw.rect(screen, theme.INFOBOX_FRAME, panel, 4, border_radius=10)
        theme.shadow_text(screen, "RALTS", fonts["s_med"], panel.x + 22, panel.y + 12)
        theme.shadow_text(screen, "Lv5", fonts["label"], panel.right - 22, panel.y + 16, align="right")
        theme.hp_bar(screen, panel.x + 22, panel.y + 60, panel.w - 44, self.hp, 1.0)
        if self.ball_t is not None:
            x, y = self._ball_pos()
            angle = 0
            if self.ball_t >= 1.0 and self.step == 4:  # three wobbles, then still
                angle = math.sin(self.frame * 0.25) * 25
            img = pygame.transform.rotate(self.ball, angle)
            screen.blit(img, img.get_rect(center=(int(x), int(y) + (50 if self.ball_t >= 1.0 else 0))))
        if not self.dialogue_box.visible:
            Utils.draw_textbox(screen, *self.box_rect)
        self.game.ui_manager.draw(screen)
