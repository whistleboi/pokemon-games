# [REF-0077: Hoenn version choice]
"""Choose Omega Ruby (Team Magma, Groudon) or Alpha Sapphire (Team Aqua, Kyogre)."""
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
            Utils.draw_text_outline(screen, v["title"], self.game.assets.fonts["small"], WHITE, cx, 410)
            Utils.draw_text_outline(screen, f"{v['team']}  -  {v['legend']}", self.game.assets.fonts["tiny"],
                                    WHITE, cx, 455)
        if not self.dialogue_box.visible:
            Utils.draw_classic_panel(screen, *self.box_rect)
        self.game.ui_manager.draw(screen)
