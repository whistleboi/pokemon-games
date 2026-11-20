# [REF-0077b: Unova version choice]
"""Choose Black 2 (Zekrom, Black Kyurem, Black City) or White 2 (Reshiram, White Kyurem, White Forest) when Unova starts:
Jordan 11-20, "like in Hoenn" (src/states/hoenn.py's HoennVersionState). The choice: story flag "unova_version"
(src/world/unova_version.py)."""
import pygame

from src.states.poffin import _MenuState, _button_row
from src.utils import Utils
from src.config import WHITE, GOLD
from src.world import unova_version as uv


class UnovaVersionState(_MenuState):
    def __init__(self, game, next_state_factory):
        super().__init__(game, None)
        self.next_state_factory = next_state_factory
        self.art = {}
        for key, v in uv.VERSIONS.items():
            img = game.assets.get_pokemon_image(v["legend_id"], "normal", False)
            self.art[key] = pygame.transform.scale(img, (260, 260)) if img is not None else None

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        self.say(["Welcome to Unova!",
                  "Two years have passed since Team Plasma's plan. Now the legendary dragons stir again...",
                  "Which story will you play?"], self.show_choices)

    def show_choices(self):
        self.dialogue_box.set_visibility(False)
        specs = [(v["title"], (lambda k=key: self.choose(k)), v["accent"], None) for key, v in uv.VERSIONS.items()]
        self.set_buttons(_button_row(self.game, specs, self.box_rect.top + 40, width=320, height=70))

    def choose(self, key):
        self.game.story_manager.story_flags["unova_version"] = key
        v = uv.VERSIONS[key]
        self.say([f"You chose {v['title']}!",
                  f"{v['legend']} watches over your story, and {v['kyurem']} waits at its end.",
                  "Good luck on your journey!"], self.finish)

    def finish(self):
        self.set_buttons([])
        self.game.change_state(self.next_state_factory())

    def draw(self):
        screen = self.game.screen
        w = self.game.width
        screen.fill((20, 20, 30))
        half = w // 2
        pygame.draw.rect(screen, (34, 34, 42), (0, 0, half, self.box_rect.top))
        pygame.draw.rect(screen, (214, 218, 228), (half, 0, w - half, self.box_rect.top))
        Utils.draw_text_outline(screen, "CHOOSE YOUR STORY", self.game.assets.fonts["big"], GOLD, half, 50)
        for i, (key, v) in enumerate(uv.VERSIONS.items()):
            cx = half // 2 + i * half
            img = self.art.get(key)
            if img is not None:
                screen.blit(img, img.get_rect(center=(cx, 250)))
            Utils.draw_text_outline(screen, v["title"], self.game.assets.fonts["label"], WHITE, cx, 410)
            Utils.draw_text_outline(screen, f"{v['legend']}  -  {v['city']}", self.game.assets.fonts["caption"], WHITE, cx, 455)
        if not self.dialogue_box.visible:
            Utils.draw_textbox(screen, *self.box_rect)
        self.game.ui_manager.draw(screen)
