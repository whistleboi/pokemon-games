# [REF-0074: Weather Dial]
"""
The Weather Dial (from Hoenn's Weather Institute, after Rayquaza calms the skies).
Used from the Bag on an outdoor route: a weather rock is used up to set that route's
weather until midnight, or the skies can be cleared for free. The season can't be changed.
"""
from src.states.poffin import _MenuState, _button_row
from src.utils import Utils
from src.config import WHITE, GOLD, RED
from src.world import seasons

ROCK_COLORS = {"DAMP_ROCK": (50, 90, 200), "HEAT_ROCK": (210, 90, 40),
               "SMOOTH_ROCK": (170, 130, 70), "ICY_ROCK": (90, 170, 220)}
SET_TEXT = {
    "RAIN": "Dark clouds gather and rain begins to fall!",
    "SUN": "The clouds part and the sunlight turns harsh!",
    "SAND": "The wind picks up and a sandstorm sweeps in!",
    "SNOW": "The air turns cold and snow begins to fall!",
    None: "The weather calms and the skies clear.",
}


class WeatherDialState(_MenuState):
    def __init__(self, game, previous_state):
        super().__init__(game, previous_state)
        self.area_key = self.story.current_area_key
        area = self.story.get_current_area_data()
        self.area_name = area.get("route_name") or self.area_key.replace("_", " ").title()

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        if not seasons.can_change_weather(self.game, self.area_key):
            self.say(["The WEATHER DIAL only works outdoors on routes",
                      "in regions that have weather."], self.back)
            return
        now = seasons.weather_name(seasons.area_weather(self.game, self.area_key))
        self.say([f"{seasons.season_name()} on {self.area_name}. Today's weather: {now}.",
                  "Set a weather rock in the dial to change it until midnight.",
                  "The dial can't change the season, though!"], self.show_choices)

    def show_choices(self):
        self.dialogue_box.set_visibility(False)
        inv = self.story.inventory
        specs = []
        for rock, weather in seasons.ROCK_WEATHER.items():
            qty = inv.get(rock, 0)
            if qty > 0:
                specs.append((f"{seasons.weather_name(weather)} x{qty}",
                              (lambda r=rock: self.use_rock(r)), ROCK_COLORS[rock], self.icon(rock)))
        specs.append(("CLEAR SKIES", (lambda: self.apply(None, None)), (90, 160, 90), None))
        buttons = _button_row(self.game, specs, 200, width=280, height=64, per_row=3)
        buttons += _button_row(self.game, [("BACK", self.back, RED, None)], self.box_rect.top + 45, width=220)
        self.set_buttons(buttons)

    def use_rock(self, rock):
        self.story.inventory[rock] -= 1
        self.apply(seasons.ROCK_WEATHER[rock], rock)

    def apply(self, weather, rock):
        seasons.set_weather(self.game, self.area_key, weather)
        lines = []
        if rock:
            lines.append(f"You set the {rock.replace('_', ' ').title()} in the WEATHER DIAL...")
            lines.append("It crumbled to dust!")
        lines += [SET_TEXT[weather], f"It will stay this way on {self.area_name} until midnight."]
        self.say(lines, self.back)

    def back(self):
        self.set_buttons([])
        self.game.change_state(self.previous_state)

    def draw(self):
        screen = self.game.screen
        season = seasons.current_season()
        screen.fill((30, 40, 60))
        Utils.draw_text_outline(screen, "WEATHER DIAL", self.game.assets.fonts["big"], GOLD,
                                self.game.width // 2, 60)
        weather = seasons.weather_name(seasons.area_weather(self.game, self.area_key))
        Utils.draw_text_outline(screen, f"{seasons.season_name(season)}  -  {weather}",
                                self.game.assets.fonts["small"], seasons.SEASON_COLORS[season],
                                self.game.width // 2, 125)
        Utils.draw_text_outline(screen, self.area_name, self.game.assets.fonts["tiny"], WHITE,
                                self.game.width // 2, 160)
        if not self.dialogue_box.visible:
            Utils.draw_classic_panel(screen, *self.box_rect)
        self.game.ui_manager.draw(screen)
