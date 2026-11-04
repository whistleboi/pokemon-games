"""Pokemon Centers: the inside, healing, and the combined Center and Mart from Unova on."""

import pygame
from src.states.base import GameState
from src.utils import Utils
from src.ui.dialogue import ClassicDialogueBox
from src.config import WHITE, BLACK, BLUE
from src.states.overworld.town import CityState


COMBINED_CENTER_REGIONS = ("UNOVA", "KALOS", "ALOLA", "GALAR", "PALDEA")


def combined_center(game):
    """From Unova on, the Pokemon Center and the shop are one building (Jordan, 10-30)."""
    return game.story_manager.get_current_region() in COMBINED_CENTER_REGIONS


def center_entrance(options):
    """A town's EXPLORE options with its Pokemon Center and plain shop as one way in (the CENTER
    option carries the shop along). Shops with their own stock (Lumiose's Stone Emporium) stay out here."""
    heal = next((o for o in options if o.get("action") == "HEAL"), None)
    if heal is None:
        return options
    shops = [o for o in options if o.get("action") == "SHOP" and not o.get("stock")]
    out = []
    for o in options:
        if o is heal:
            out.append(dict(heal, action="CENTER", shops=shops))
        elif o not in shops:
            out.append(o)
    return out


def center_background(game, state, type_suffix="center"):
    """A Pokemon Center's picture: the region's own Center for all its towns (Kalos), else the town's."""
    shared = game.assets.get_region_building(game.story_manager.get_current_region(), type_suffix)
    if shared:
        state.generic_bg = True  # Nurse Joy is in the picture
        return pygame.transform.scale(shared, (game.width, Utils.get_full_dialogue_rect(game).top))
    return PokeCenterState._load_building_bg_town(state, game, type_suffix)


# [REF-0030: City & Building Logic]
class CenterInsideState(CityState):
    """Inside a Pokemon Center from Unova on, where the shop is part of the Center (Jordan, 10-30):
    the town's menu, with EXPLORE to heal or shop and TRAVEL back out to the town."""

    def __init__(self, game, town, shops=()):
        self.town = town
        super().__init__(game)
        name = self.area_data.get("route_name") or self.area_key.replace("_", " ").title()
        self.area_data = dict(self.area_data)
        self.area_data["explore_options"] = [{"text": "Heal your Pokémon", "action": "HEAL"}] + \
            [dict(o, text="Shop") for o in shops[:1]]
        self.area_data["travel_options"] = [{"text": f"Back to {name}", "action": "LEAVE_CENTER"}]
        self.area_data.pop("on_enter_event", None)
        self.action_menu.prompt_lines = lambda: ["Welcome to", "the Pokémon Center!"]

    def load_area_background(self):
        return center_background(self.game, self)

    def start(self):  # no arrival events in here: just the menu
        self.clear_hover_menu()
        self.game.ui_manager.add_element(self.action_menu)
        pygame.event.clear()
        for btn in self.hud_buttons:
            if btn not in self.game.ui_manager.elements:
                self.game.ui_manager.add_element(btn)

    def open_explore_menu(self):
        self._create_hover_menu(self.area_data["explore_options"], self.action_menu.buttons[0].rect)

    def open_travel_menu(self):
        if len(self.action_menu.buttons) > 3:
            self._create_hover_menu(self.area_data["travel_options"], self.action_menu.buttons[3].rect)

    def leave_center(self):
        self.clear_hover_menu()
        self.game.change_state(self.town)


class PokeCenterState(GameState):
    def __init__(self, game, previous_state, lines=None):
        super().__init__(game)
        self.previous_state = previous_state
        self.timer = 0
        self.phase = "HEAL"
        self.bg = self._load_building_bg(game, "center")
        game.story_manager.last_center = game.story_manager.current_area_key

        self.nurse_sprite = None  # (no nurse drawn in any Pokemon Center, Jordan 11-02)
        self.dialogue_box = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(game),
            lines or ["Welcome to the Pokémon Center!", "We've restored your team to full health."],
            game.assets.fonts["med"],
            callback=self.finish_heal
        )

        for p in self.game.story_manager.player_team:
            p.heal_full()

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        from src.core import music
        if not any(p.search(str(t)) for t in self.dialogue_box.text_lines for p, n in music.JINGLE_CUES
                   if n == "pokemon_healed"):
            self.game.music.jingle("pokemon_healed")  # (a nurse line that doesn't say it)

    def _load_building_bg(self, game, type_suffix):
        return center_background(game, self, type_suffix)

    def _load_building_bg_town(self, game, type_suffix):
        area_data = game.story_manager.get_current_area_data()
        json_key = "pokecenter" if type_suffix == "center" else "pokemart"
        bg_config = area_data.get("backgrounds", {}).get(json_key)

        area_key = game.story_manager.current_area_key
        # ARCHITECT: Fallback naming logic: [area_key]_[suffix] (e.g. azalea_town_center.png)
        fallback_name = f"{area_key.lower()}_{type_suffix}.png"

        # A generic name (pokecenter.png) is only a last resort: this town's own art comes first.
        generic = bg_config in ("pokecenter.png", "pokemart.png")
        filenames = ([fallback_name, bg_config] if generic else [bg_config, fallback_name]) if bg_config             else [fallback_name]
        box_top = Utils.get_full_dialogue_rect(game).top

        for filename in filenames:
            img = game.assets.get_background(filename)
            if img:
                return pygame.transform.scale(img, (game.width, box_top))

        img = game.assets.get_generic_background(type_suffix)
        if img:
            self.generic_bg = True  # the stand-in Center already has Nurse Joy at the counter
            return pygame.transform.scale(img, (game.width, box_top))
        bg = pygame.Surface((game.width, box_top))
        bg.fill(WHITE if type_suffix == "center" else BLUE)
        return bg

    def finish_heal(self):
        self.game.change_state(self.previous_state)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                self.finish_heal()

    def update(self):
        self.dialogue_box.update()

    def draw(self):
        self.game.screen.fill(BLACK)
        self.game.screen.blit(self.bg, (0, 0))
        if self.nurse_sprite:
            rect = self.nurse_sprite.get_rect(center=(self.game.width//2, self.game.height*0.5))
            self.game.screen.blit(self.nurse_sprite, rect)
        self.dialogue_box.draw(self.game.screen)
