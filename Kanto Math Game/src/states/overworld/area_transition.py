"""Moving between areas, and what happens on the way: healing, autosave, the League, whiting out."""

import pygame
import os
from src.states.base import GameState
from src.utils import Utils
from src.ui.dialogue import ClassicDialogueBox
from src.ui.panels import CommandButton
from src.ui import theme
from src.config import BLACK


# Jordan: only LONG rides between two regions/sub-regions heal (ships, the Seagallop to and from
# Kanto, the Magnet Train, the Hoenn-Orre plane, the Decolore ferry): "long_ride": true on the
# travel option. Island hops inside a region or sub-region are plain, decorative trips.
TRAVEL_HEAL_LINES = {
    "long_ride": ["Your Pokemon rested during the long trip.", "Your team is fully healed!"],
    "teleport": ["Your team is fully healed, as if you'd stopped at a Pokemon Center."],
}


CABIN_REST_LINES = ["You rest in the cabin with your Pokemon...", "Your team is fully healed!"]


def travel_heal(opt_data):
    """None, "long_ride" or "teleport" for a travel option (see TRAVEL_HEAL_LINES)."""
    if opt_data.get("long_ride"):
        return "long_ride"
    heal = opt_data.get("heal")
    return str(heal) if heal else None


def heal_team(game):
    """Full HP and no status for the whole party, like a Pokemon Center."""
    for p in game.story_manager.player_team:
        if p:
            p.heal_full()
    if getattr(game.assets, "heal_sfx", None):
        game.assets.heal_sfx.play()


# [REF-0042: Area Transition Logic]
class AreaTransitionState(GameState):
    def __init__(self, game, next_area_key, initial_message=None, heal=None):
        from src.states.overworld.route import PlayState
        super().__init__(game)
        self.next_area_key = next_area_key
        self.timer = 75
        self.wait_for_dialogue = bool(initial_message)
        self.bg = None

        if isinstance(self.game.current_state, PlayState):
            self.game.story_manager.balls_left = self.game.current_state.balls_left
            self.game.story_manager.current_streak = self.game.current_state.current_streak

        rect = Utils.get_full_dialogue_rect(self.game)
        msg = []
        if isinstance(initial_message, list):  # several lines (a new game's opening scene)
            msg += initial_message
        elif initial_message:
            msg.append(initial_message)
        if heal:  # the team that sets off is healed...
            heal_team(self.game)
        # Another region's party, PC and Bag; a first visit goes to that region's professor.
        self.next_area_key, travel_lines = self.game.story_manager.prepare_travel(next_area_key)
        msg += travel_lines
        if travel_lines:
            self.wait_for_dialogue = True
        if heal:  # ...and so is the team you arrive with, if the trip switched to another region's party
            heal_team(self.game)
            msg += TRAVEL_HEAL_LINES.get(heal, TRAVEL_HEAL_LINES["long_ride"])
            self.wait_for_dialogue = True

        next_area_data = self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(self.next_area_key, {})
        route_name = next_area_data.get("route_name", self.next_area_key.replace("_", " ").title())

        msg.append(
            self.game.assets.get_text("entering_area", area=route_name)
        )

        area_type = next_area_data.get("area_type", "wild_route")

        if area_type not in ["town", "city"]:
            warning = next_area_data.get("enter_warning", self.game.assets.get_text("area_warning"))
            msg.append(warning)

        self.dialogue_box = ClassicDialogueBox(rect, msg, self.game.assets.fonts["med"])
        self.npc_sprite = None
        self.npc_pos_x = -300

        if initial_message:
            is_oak = "Oak" in initial_message
            is_elm = "Elm" in initial_message

            if is_oak or is_elm:
                self.game.music.play("lab")
                bg_name = "pallet_city_lab.png" if is_oak else "new_bark_lab.png"
                kanto_dir = self.game.assets.kanto_backgrounds_dir
                johto_dir = os.path.join(os.path.dirname(kanto_dir), "johto")

                for d in [kanto_dir, johto_dir]:
                    path = os.path.join(d, bg_name)
                    if os.path.exists(path):
                        box_top = Utils.get_full_dialogue_rect(self.game).top
                        self.bg = pygame.transform.scale(pygame.image.load(path).convert(), (self.game.width, box_top))
                        break

                prof_name = "Oak" if is_oak else "Elm"
                self.dialogue_box.reset([f"{prof_name}: Excellent battle!", "You have great potential.", initial_message])

                sprite_name = "oak.png" if is_oak else "elm.png"
                sprite_path = os.path.join(self.game.assets.sprites_dir, "png", sprite_name)
                if os.path.exists(sprite_path):
                    img = pygame.image.load(sprite_path).convert_alpha()
                    h = int(self.game.height * 0.6)
                    w = int(img.get_width() * (h / img.get_height()))
                    self.npc_sprite = pygame.transform.scale(img, (w, h))

    def handle_events(self, events):
        for event in events:
            self.dialogue_box.handle_event(event)

    def update(self):
        from src.states.overworld.route import PlayState
        from src.states.overworld.town import CityState
        self.dialogue_box.update()
        if self.npc_sprite:
            target_x = self.game.width // 2
            if not self.dialogue_box.is_finished:
                if self.npc_pos_x < target_x:
                    self.npc_pos_x += (target_x - self.npc_pos_x) * 0.05
            else:
                self.npc_pos_x += 40

        if self.wait_for_dialogue:
            if self.dialogue_box.is_finished:
                self.timer -= 1
        else:
            self.timer -= 1

        if self.timer <= 0:
            self.timer = 10**9  # only once
            self.game.story_manager.current_area_key = self.next_area_key
            self.game.story_manager.enter_region(self.game.story_manager.get_current_region())

            pygame.event.clear()

            new_area_data = self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(
                self.next_area_key, {}
            )
            area_type = new_area_data.get("area_type", "wild_route")

            if area_type == "town":
                self.game.states["city"] = CityState(self.game)
                self.game.change_state(self.game.states["city"])
            else:
                self.game.states["play"] = PlayState(self.game)
                self.game.change_state(self.game.states["play"])
            if self.game.story_manager.autosave:
                autosave(self.game)
            # A trip: the Day Care counts towards an Egg, Eggs in the party towards hatching (11-03).
            from src.pokemon import breeding
            ready, news = breeding.on_travel(self.game)
            if ready is not None:
                from src.states.systems import EvolutionState
                egg = self.game.story_manager.player_team[ready]
                self.game.change_state(EvolutionState(
                    self.game, egg, breeding.species_id(self.game, egg), ready, next_form=egg.form or "normal",
                    context="party", return_state=self.game.current_state))
            elif news:
                self.game.show_dialogue(news)

    def draw(self):
        if self.bg:
            self.game.screen.blit(self.bg, (0, 0))
        else:
            self.game.screen.fill(BLACK)
        if self.npc_sprite:
            rect = self.npc_sprite.get_rect(midbottom=(self.npc_pos_x, self.dialogue_box.rect.top))
            self.game.screen.blit(self.npc_sprite, rect)
        self.dialogue_box.draw(self.game.screen)


def _collapse_hud(state):
    """The side menus (PC, Bag, Badges, Save...) live behind one big MENU button that opens a
    grid of large tiles, instead of a column of small buttons."""
    state.menu_entries = state.hud_buttons
    for btn in state.menu_entries:  # off screen now: the keyboard highlight must skip them
        btn.nav_hidden = True

    def open_menu():
        if hasattr(state, "is_resuming"):
            state.is_resuming = True  # a route comes back to the same encounter
        from src.states.menu_grid import MenuGridState
        state.game.change_state(MenuGridState(state.game, state, state.menu_entries))

    state.hud_buttons = [CommandButton((20, 56, 170, 60), "MENU", state.game.assets.fonts["button"], open_menu,
                                       bg_color=theme.RUN, autosize=False)]


def evolve_ready_party(game, return_state):
    """Evolve a party Pokemon that is ready (e.g. it hit its level in a gym or town battle),
    then go on to return_state. Returns True if an evolution started."""
    from src.states.overworld.route import PlayState
    scan = PlayState.__new__(PlayState)  # only the party scan is needed, not a whole route
    scan.game = game
    scan._evo_return = return_state
    return scan._scan_list_for_evolution(game.story_manager.player_team, False, "party")


def is_league(gym_data):
    """A Pokemon League: Elite Four trainers and/or a Champion (every region's)."""
    gym_data = gym_data or {}
    leader = gym_data.get("leader") or {}
    return (leader.get("class") == "CHAMPION"
            or any(t.get("class") == "ELITE_FOUR" for t in gym_data.get("trainers", [])))


def reset_league_after_loss(game):
    """Losing at a Pokemon League sends you back to the start of the Elite Four, as in the games."""
    story = game.story_manager
    area = story.get_current_area_data()
    if is_league(area.get("gym")):
        story.story_flags[f"gym_progress_{story.current_area_key}"] = 0


def autosave(game):
    """Save quietly (Options > AUTOSAVE); a failed write never stops the game."""
    try:
        game.update_save_data()
        game.data.save()
    except Exception as e:
        print(f"Autosave failed: {e}")


def white_out(game):
    """Whiting out: heal the team and wake up at the last Pokemon Center used in
    this region, or at home if you haven't used one yet."""
    from src.states.overworld.pokecenter import PokeCenterState
    from src.states.overworld.route import PlayState
    from src.states.overworld.town import CityState
    story = game.story_manager
    for p in story.player_team:
        p.heal_full()
        if hasattr(p, "revert_transform"):
            p.revert_transform()
    story.current_area_key, has_center = story.whiteout_destination()
    area = story.get_current_area_data()
    if area.get("area_type") == "town":
        game.skip_arrival_event = True  # no rival ambush the moment you wake up
        town = game.states["city"] = CityState(game)
    else:
        town = game.states["play"] = PlayState(game)
    if has_center:
        game.change_state(PokeCenterState(game, town, lines=[
            "You hurried back to the Pokémon Center, protecting your exhausted Pokémon.",
            "Nurse: We've healed your Pokémon after that tough battle.",
            "Please take care out there!",
        ]))
    else:
        game.change_state(town)
        game.show_dialogue([
            "You hurried home, protecting your exhausted Pokémon.",
            "Mom: Oh, you're back! You must have had a tough battle.",
            "I've looked after your Pokémon. They're full of energy again!",
        ])
