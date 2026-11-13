"""Berry screens (Jordan, 11-12: the berry patches): choosing a Berry to plant in soft soil (src/world/berries.py), and
the Pokeblock Kit (ORAS: Lisia's gift with the Contest Pass), which turns Berries into Pokeblocks.

The Kit: pick up to four different Berries; each makes a Pokeblock of its strongest flavor's color (Spicy red for
Cool, Dry blue for Beauty, Sweet pink for Cute, Bitter green for Smart, Sour yellow for Tough), two from a Berry with
a strong flavor (20 or more)."""
import pygame

from src.states.poffin import _MenuState, _button_row
from src.pokemon.poffin import BERRIES, FLAVOR_COLOR, berry_name, berry_label
from src.config import WHITE, GOLD, GRAY, RED, GREEN
from src.utils import Utils

BLOCK_OF = {"SPICY": "RED_POKEBLOCK", "DRY": "BLUE_POKEBLOCK", "SWEET": "PINK_POKEBLOCK",
            "BITTER": "GREEN_POKEBLOCK", "SOUR": "YELLOW_POKEBLOCK"}
MAX_KIT_BERRIES = 4
PER_PAGE = 8


def blocks_from(berries):
    """{pokeblock: count} from these Berries."""
    out = {}
    for b in berries:
        fl = BERRIES.get(b) or {}
        if not fl:
            continue
        top = max(fl, key=fl.get)
        out[BLOCK_OF[top]] = out.get(BLOCK_OF[top], 0) + (2 if fl[top] >= 20 else 1)
    return out


class _BerryPick(_MenuState):
    """A page of the Bag's Berries as buttons over the map you came from."""
    title = ""

    def __init__(self, game, previous_state):
        super().__init__(game, previous_state)
        self.page = 0

    def owned(self):
        return [b for b in BERRIES if self.story.inventory.get(b, 0) > 0]

    def berry_buttons(self, marks=()):
        owned = self.owned()
        self.page = min(self.page, max(0, (len(owned) - 1) // PER_PAGE))
        specs = []
        for b in owned[self.page * PER_PAGE:(self.page + 1) * PER_PAGE]:
            left = self.story.inventory[b] - list(marks).count(b)
            color = FLAVOR_COLOR[max(BERRIES[b], key=BERRIES[b].get)]
            specs.append((f"{'> ' if b in marks else ''}{berry_name(b)} x{left}", (lambda b=b: self.chose(b)), color, self.icon(b)))
        return _button_row(self.game, specs, self.box_rect.top + 14, width=270, height=56)

    def next_page(self):
        self.page = (self.page + 1) % max(1, -(-len(self.owned()) // PER_PAGE))
        self.show()

    def back(self):
        self.set_buttons([])
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        self.show()

    def draw(self):
        prev = self.previous_state
        if prev is not None and hasattr(prev, "draw"):
            prev.draw()
        veil = pygame.Surface((self.game.width, self.game.height), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 120))
        self.game.screen.blit(veil, (0, 0))
        Utils.draw_text_outline(self.game.screen, self.title, self.game.assets.fonts["label"], GOLD, self.game.width // 2, 60)
        if not self.dialogue_box.visible:
            Utils.draw_textbox(self.game.screen, *self.box_rect)
        self.game.ui_manager.draw(self.game.screen)


class PlantBerryState(_BerryPick):
    """Pick the Berry to plant; then(lines) runs back on the map."""
    title = "Which Berry will you plant?"

    def __init__(self, game, previous_state, plant):
        super().__init__(game, previous_state)
        self.plant = plant  # (berry -> lines said back on the map)

    def show(self):
        self.dialogue_box.set_visibility(False)
        controls = [("CANCEL", self.back, RED, None)]
        if len(self.owned()) > PER_PAGE:
            controls.insert(0, ("MORE BERRIES", self.next_page, (90, 90, 140), None))
        self.set_buttons(self.berry_buttons() + _button_row(self.game, controls, self.box_rect.top - 76, width=200, height=56))

    def chose(self, berry):
        self.set_buttons([])
        self.game.change_state(self.previous_state)
        self.plant(berry)


class PokeblockKitState(_BerryPick):
    title = "POKEBLOCK KIT: choose up to 4 different Berries"

    def __init__(self, game, previous_state):
        super().__init__(game, previous_state)
        self.selected = []

    def show(self):
        self.dialogue_box.set_visibility(False)
        controls = [("MAKE!", self.make, GREEN if self.selected else GRAY, None), ("BACK", self.back, RED, None)]
        if len(self.owned()) > PER_PAGE:
            controls.insert(1, ("MORE BERRIES", self.next_page, (90, 90, 140), None))
        self.set_buttons(self.berry_buttons(self.selected) + _button_row(self.game, controls, self.box_rect.top - 76, width=200, height=56))

    def chose(self, berry):
        if berry in self.selected:
            self.selected.remove(berry)
        elif len(self.selected) < MAX_KIT_BERRIES:
            self.selected.append(berry)
        self.show()

    def make(self):
        if not self.selected:
            return
        inv = self.story.inventory
        for b in self.selected:
            inv[b] -= 1
            if inv[b] <= 0:
                del inv[b]
        made = blocks_from(self.selected)
        for k, n in made.items():
            inv[k] = inv.get(k, 0) + n
        names = ", ".join(berry_name(b) for b in self.selected)
        self.selected = []
        lines = [f"Into the Kit: {names}."] + [f"You made {n} {k.replace('_', ' ').title().replace('Pokeblock', 'Pokéblock')}{'s' if n > 1 else ''}!"
                                               for k, n in made.items()]
        self.game.data.save()
        self.say(lines, self.show if self.owned() else self.back)

    def draw(self):
        super().draw()
        if self.selected and not self.dialogue_box.visible:
            text = "In the Kit: " + ", ".join(f"{berry_name(b)} ({berry_label(b)})" for b in self.selected)
            Utils.draw_text_outline(self.game.screen, text, self.game.assets.fonts["caption"], WHITE, self.game.width // 2, 100)
