"""The Bag: pockets, using and giving items, and choosing how many."""

import pygame
import os
from src.states.base import GameState
from src.ui.widgets import Button, ItemCard
from src.ui.panels import CommandButton
from src.ui import theme
from src.utils import Utils
from src.config import WHITE, GREEN, RED
from src.pokemon.contest import feed_pokeblock, POKEBLOCKS, MAX_CONDITION
from src.pokemon import items as itemlib
from src.pokemon import forms
from src.states.systems.evolution_scene import EvolutionState
from src.states.systems.party_menu import PokemonPartyMenuState
from src.states.systems.town_services import UnownReportState
from src.ui.mon_tags import fit_sprite


# [REF-0032: Bag System]
class BagState(GameState):
    def __init__(self, game, previous_state, context="normal"):
        super().__init__(game)
        self.previous_state = previous_state
        self.context = context
        self.evo_items_map = self.game.loader.evolution_map.get("EVOLUTION_ITEMS", {})
        self.evo_keys = sorted(list(self.evo_items_map.keys()))

        # Pockets, as in the games (Jordan). In battle only the ones you can use there.
        self.pages = list(self.BATTLE_POCKETS if context == "battle" else self.POCKETS)
        self.current_page = 0
        self.pocket_tabs = []
        f = game.assets.fonts
        H = theme.HEADER_H
        gap = 10
        tab_w = (game.width - 48 - gap * (len(self.pages) - 1)) // len(self.pages)
        for i, name in enumerate(self.pages):
            tf = f["label"] if f["label"].size(name)[0] <= tab_w - 24 else f["caption"]
            self.pocket_tabs.append(CommandButton((24 + i * (tab_w + gap), H + 14, tab_w, 50), name, tf,
                                                  (lambda i=i: self.open_pocket(i)), bg_color=theme.TAB_OFF,
                                                  autosize=False))

        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.go_back, bg_color=theme.BACK,
                                      autosize=False)

        # (The tabs pick the pocket; these stay for anything that turns pockets in order.)
        cy = game.height // 2
        self.btn_prev = Button((20, cy - 30, 60, 60), "<", f["med"], self.prev_page, visible=False)
        self.btn_next = Button((game.width - 80, cy - 30, 60, 60), ">", f["med"], self.next_page, visible=False)
        # The menu frame: the pocket's items as cards, the bar along the bottom (the item under the
        # pointer, the page buttons). A full pocket is split into pages.
        self.list_rect = pygame.Rect(24, H + 14 + 50 + 16, game.width - 48, 0)
        self.bar_rect = pygame.Rect(16, game.height - 86, game.width - 32, 78)
        self.list_rect.height = self.bar_rect.top - 12 - self.list_rect.top
        self.item_page = 0
        self.item_page_count = 1
        bh = self.bar_rect.h - 28
        self.btn_items_up = CommandButton((self.bar_rect.right - 18 - 230, self.bar_rect.y + 12, 110, bh), "UP",
                                          f["label"], lambda: self.turn_item_page(-1),
                                          bg_color=theme.ACCENT["bag"], autosize=False)
        self.btn_items_down = CommandButton((self.bar_rect.right - 18 - 110, self.bar_rect.y + 12, 110, bh), "DOWN",
                                            f["label"], lambda: self.turn_item_page(1),
                                            bg_color=theme.ACCENT["bag"], autosize=False)

        self.item_buttons = []
        self.refresh_buttons()

    POCKETS = ("ITEMS", "MEDICINE", "POKE BALLS", "BERRIES", "TMs & HMs", "KEY ITEMS")
    BATTLE_POCKETS = ("MEDICINE", "POKE BALLS", "BATTLE ITEMS")
    MEDICINE = tuple(itemlib.MEDICINE)
    BATTLE_ITEMS = ("DAMP_ROCK", "HEAT_ROCK", "SMOOTH_ROCK", "ICY_ROCK") + tuple(itemlib.BATTLE)
    # Usable from the Bag (anything else says there's no use for it right now).
    USABLE_KEYS = ("TOWN_MAP", "JOHTO_MAP", "UNOWN_REPORT", "POFFIN_CASE", "BERRY_POUCH", "WEATHER_DIAL")
    USABLE_MEDICINE = ("POTION", "FULL_HEAL", "REVIVE", "RARE_CANDY")
    # Key items the games keep in the Items pocket (held / stones / fossils).
    ITEM_POCKET_KEYS = ("ITE", "_FOSSIL", "OLD_AMBER", "_ORB", "_DRIVE", "ROCKY_HELMET", "SOOTHE_BELL", "AMULET_COIN")

    def pocket_of(self, key):
        from src.pokemon.poffin import BERRIES
        from src.pokemon import zpower
        if key in zpower.KEY_ITEMS:
            return "KEY ITEMS"
        if key in self.MEDICINE:
            return "MEDICINE"
        if key in self.BATTLE_ITEMS:
            return "BATTLE ITEMS" if self.context == "battle" else "ITEMS"
        if key.endswith("_BALL") and key != "GS_BALL":
            return "POKE BALLS"
        if key in BERRIES or key.endswith("_BERRY"):
            return "BERRIES"
        if key.startswith(("HM_", "TM_", "TM")) and key[2:3] in ("_", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"):
            return "TMs & HMs"
        keys = self.game.loader.area_data.get("GAME_CONFIG", {}).get("KEY_ITEMS", [])
        if key in keys and not (key.endswith(self.ITEM_POCKET_KEYS) and key not in self.USABLE_KEYS):
            return "KEY ITEMS"
        return "ITEMS"

    def pocket_items(self, pocket):
        """(item, qty) in a pocket, in a fixed order."""
        inv = self.game.story_manager.inventory
        out = []
        if pocket == "POKE BALLS":
            out.append(("POKE_BALLS", self.game.story_manager.balls_left))
        if pocket == "ITEMS":
            held = any(getattr(p, "everstone", False) for p in self.game.story_manager.player_team)
            if held and not inv.get("EVERSTONE"):
                out.append(("EVERSTONE", 0))  # (to take it back)
        order = list(self.MEDICINE) + self.evo_keys + list(POKEBLOCKS)
        keys = sorted((k for k, q in inv.items() if q and q > 0 and k != "POKE_BALLS"),
                      key=lambda k: (order.index(k) if k in order else len(order), k))
        out += [(k, inv[k]) for k in keys if self.pocket_of(k) == pocket]
        return [(k, q) for k, q in out if q > 0 or k == "EVERSTONE"]

    def usable(self, key):
        from src.pokemon import catching
        if self.context == "battle":
            if key in catching.BALLS:  # throw a ball any time in a wild battle, as in the games
                return getattr(self.previous_state, "trainer_class", "") == "WILD"
            return (key in itemlib.MEDICINE and key != "RARE_CANDY") or key in self.BATTLE_ITEMS
        from src.pokemon import tms, zpower
        return (key in itemlib.MEDICINE or key in itemlib.FIELD or key in self.USABLE_KEYS
                or key == "EVERSTONE" or key in self.evo_keys or key in POKEBLOCKS or tms.is_tm(key)
                or bool(zpower.shard_type(key)) or key in zpower.CRYSTAL_TYPE)

    def open_pocket(self, i):
        self.current_page = i
        self.item_page = 0
        self.refresh_buttons()

    def prev_page(self):
        self.current_page = (self.current_page - 1) % len(self.pages)
        self.item_page = 0
        self.refresh_buttons()

    def next_page(self):
        self.current_page = (self.current_page + 1) % len(self.pages)
        self.item_page = 0
        self.refresh_buttons()

    def turn_item_page(self, step):
        self.item_page = max(0, min(self.item_page_count - 1, self.item_page + step))
        self.refresh_buttons()

    def go_back(self):
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.elements.clear()
        self.game.ui_manager.add_element(self.btn_back)
        self.game.ui_manager.add_element(self.btn_prev)
        self.game.ui_manager.add_element(self.btn_next)
        self.game.ui_manager.add_element(self.btn_items_up)
        self.game.ui_manager.add_element(self.btn_items_down)
        for btn in self.pocket_tabs:
            self.game.ui_manager.add_element(btn)
        for btn in self.item_buttons:
            self.game.ui_manager.add_element(btn)

    def refresh_buttons(self):
        for btn in self.item_buttons:
            if btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)

        self.item_buttons = []

        for i, tab in enumerate(self.pocket_tabs):  # the open pocket stands out
            tab.bg_color = theme.ACCENT["bag"] if i == self.current_page else theme.TAB_OFF
        items_to_show = self.pocket_items(self.pages[self.current_page])

        cols, gap, btn_h = 2, 12, 58
        col_w = (self.list_rect.w - gap * (cols - 1)) // cols
        rows = max(1, (self.list_rect.h + gap) // (btn_h + gap))
        per_page = rows * cols
        self.item_page_count = max(1, (len(items_to_show) + per_page - 1) // per_page)
        self.item_page = min(self.item_page, self.item_page_count - 1)
        self.btn_items_up.set_visibility(self.item_page > 0)
        self.btn_items_down.set_visibility(self.item_page < self.item_page_count - 1)
        items_to_show = items_to_show[self.item_page * per_page:(self.item_page + 1) * per_page]

        if not items_to_show:
            return

        from src.world import hms
        for i, (item_key, qty) in enumerate(items_to_show):
            row, col = i // cols, i % cols
            x = self.list_rect.x + col * (col_w + gap)
            y = self.list_rect.y + row * (btn_h + gap)

            can_use = (qty > 0 or item_key == "EVERSTONE") and self.usable(item_key)
            callback = ((lambda k=item_key: self.use_item(k)) if can_use
                        else (lambda k=item_key: self.no_use(k)))

            icon = self.game.assets.get_item_image(item_key)
            if item_key == "MYSTERY_EGG":
                egg_path = os.path.join(self.game.assets.pokemon_sprites_dir, "egg.png")
                if os.path.exists(egg_path):
                    icon = pygame.image.load(egg_path).convert_alpha()

            self.item_buttons.append(ItemCard((x, y, col_w, btn_h), hms.item_name(item_key), qty,
                                              self.game.assets.fonts["label"], callback, icon=icon,
                                              usable=can_use, key=item_key))

        for btn in self.item_buttons:
            self.game.ui_manager.add_element(btn)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):  # the wheel turns the page
                self.turn_item_page(-1 if event.button == 4 else 1)

    def update(self):
        pass

    def no_use(self, item_key):
        from src.world import hms
        name = hms.item_name(item_key)
        if item_key == "POKE_BALLS":
            line = "Poke Balls are thrown in battle: weaken a wild Pokemon, then catch it!"
        elif item_key.startswith("HM_"):
            line = f"{name} works on its own: it opens the way wherever it's needed."
        elif self.pocket_of(item_key) == "KEY ITEMS":
            line = f"The {name} is used automatically when you need it."
        else:
            line = f"There's no use for the {name} right now."
        self.game.show_dialogue([line])

    def use_item(self, item_key):
        self.selected_item = item_key

        from src.pokemon import catching
        if self.context == "battle" and item_key in catching.BALLS:
            story = self.game.story_manager
            if not story.catch_unlocked():  # battling is fine before the Pokedex, catching waits (canon)
                prof = story.get_region_start().get("professor") or "The Professor"
                self.game.show_dialogue(["You can't catch Pokemon yet!", f"{prof} will give you a Pokedex first."])
                return
            battle = self.previous_state
            self.game.story_manager.selected_ball = item_key
            self.game.change_state(battle)
            battle.throw_from_bag()
            return
        if item_key in itemlib.MEDICINE and item_key != "RARE_CANDY":
            self.game.change_state(PokemonPartyMenuState(
                self.game, previous_state=self, context="use_item", on_select=self.on_pokemon_select_medicine))
            return
        if item_key in itemlib.BATTLE and self.context == "battle":
            self._use_battle_item(item_key)
            return
        if item_key in itemlib.FIELD:
            self._use_field_item(item_key)
            return

        from src.pokemon import tms, zpower
        if item_key in zpower.CRYSTAL_TYPE:  # a Z-Crystal: give it to a Pokemon to hold (or take it back)
            self.game.change_state(PokemonPartyMenuState(
                self.game, previous_state=self, context="use_item", on_select=self.on_pokemon_select_crystal))
            return
        if zpower.shard_type(item_key):  # Tera Shards: 10 change a Pokemon's Tera Type
            self.game.change_state(PokemonPartyMenuState(
                self.game, previous_state=self, context="use_item", on_select=self.on_pokemon_select_shards))
            return
        if tms.is_tm(item_key):  # teach its move (the TM is kept)
            self.game.change_state(PokemonPartyMenuState(
                self.game, previous_state=self, context="use_item", on_select=self.on_pokemon_select_tm))
            return

        if item_key == "RARE_CANDY":
            self.game.change_state(PokemonPartyMenuState(
                self.game,
                previous_state=self,
                context="use_item",
                on_select=self.on_pokemon_select_rare_candy
            ))
            return

        if item_key == "POTION":
            self.game.change_state(PokemonPartyMenuState(
                self.game, previous_state=self, context="use_item",
                on_select=self.on_pokemon_select_potion
            ))
            return

        if item_key == "EVERSTONE":
            self.game.change_state(PokemonPartyMenuState(
                self.game, previous_state=self, context="use_item",
                on_select=self.on_pokemon_select_everstone
            ))
            return

        if item_key == "FULL_HEAL":
            self.game.change_state(PokemonPartyMenuState(
                self.game, previous_state=self, context="use_item",
                on_select=self.on_pokemon_select_full_heal
            ))
            return

        if item_key == "REVIVE":
            self.game.change_state(PokemonPartyMenuState(
                self.game, previous_state=self, context="use_item",
                on_select=self.on_pokemon_select_revive
            ))
            return

        if item_key.endswith("_ROCK") and self.context == "battle":
            battle = self.previous_state
            self.game.change_state(battle)
            if battle.weather_summoned:
                battle.show_message(["The rock has already been used this battle!"],
                                    callback=battle.return_to_menu)
            else:
                battle.show_message([battle.summon_weather(item_key)], callback=battle.on_item_used)
            return

        if item_key in POKEBLOCKS:
            self.game.change_state(PokemonPartyMenuState(
                self.game, previous_state=self, context="use_item",
                on_select=self.on_pokemon_select_pokeblock
            ))
            return

        if item_key == "POFFIN_CASE":
            from src.states.poffin import PoffinCaseState
            self.game.change_state(PoffinCaseState(self.game, self))
            return

        if item_key == "WEATHER_DIAL":
            from src.states.weather import WeatherDialState
            self.game.change_state(WeatherDialState(self.game, self))
            return

        if item_key == "BERRY_POUCH":
            from src.pokemon.poffin import BERRIES, berry_name, berry_label
            inv = self.game.story_manager.inventory
            lines = [f"{berry_name(b)} x{inv[b]} ({berry_label(b)})" for b in BERRIES if inv.get(b, 0) > 0]
            self.game.change_state(self)
            self.refresh_buttons()
            self.game.show_dialogue(lines or ["Your BERRY POUCH is empty."])
            return

        if item_key == "UNOWN_REPORT":
            self.game.change_state(UnownReportState(self.game, self))
            return

        if item_key in ["TOWN_MAP", "JOHTO_MAP"]:
            from src.states.region_map import RegionMapState
            self.game.change_state(RegionMapState(self.game, self))
            return

        self.game.change_state(PokemonPartyMenuState(
            self.game,
            previous_state=self,
            context="use_item",
            on_select=self.on_pokemon_select
        ))

    def on_pokemon_select(self, slot_index):
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return

        pokemon = party[slot_index]
        from src.pokemon import evolution
        hit = evolution.item_evolution(self.game, pokemon, self.selected_item)
        if hit:
            entry, target_id = hit
            target_form = entry.split("_", 1)[1].lower() if "_" in entry else "normal"
            self.game.story_manager.inventory[self.selected_item] = max(
                0, self.game.story_manager.inventory.get(self.selected_item, 0) - 1)
            self.game.change_state(EvolutionState(
                self.game, pokemon, target_id, slot_index, next_form=target_form,
                return_state=self.previous_state))
            return
        timed = [r for _, _, r in evolution.evolution_options(self.game, pokemon)
                 if r.get("item") == self.selected_item and r.get("time")]
        if timed:
            self._back_to_bag([f"Nothing happened... try it during the {timed[0]['time']}."])
            return
        evolution_data = self.evo_items_map.get(self.selected_item, {})

        p_key = pokemon.name.upper()
        if pokemon.form and pokemon.form != "normal":
            alt_key = f"{p_key}_{pokemon.form.upper()}"
            if alt_key in evolution_data:
                p_key = alt_key

        if p_key in evolution_data:
            target_name = evolution_data[p_key]
            target_id = self.game.name_to_id.get(target_name.split("_")[0])

            target_form = "normal"
            if "_" in target_name:
                target_form = target_name.split("_", 1)[1].lower()

            if target_id:
                self.game.story_manager.inventory[self.selected_item] -= 1
                if self.game.story_manager.inventory[self.selected_item] < 0:
                    self.game.story_manager.inventory[self.selected_item] = 0
                self.game.change_state(EvolutionState(
                    self.game, pokemon, target_id, slot_index, next_form=target_form,
                    return_state=self.previous_state
                ))
            else:
                self._back_to_bag(["Error: Evolution data missing."])
        else:
            self._back_to_bag(["It won't have any effect."])

    def on_pokemon_select_crystal(self, slot_index):
        """A Z-Crystal: the Pokemon holds it (the Bag keeps it, as in Sun / Moon); again takes it back."""
        from src.world import hms
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return
        p, item = party[slot_index], self.selected_item
        name = hms.item_name(item)
        if getattr(p, "held_item", None) == item:
            p.held_item = None
            self._back_to_bag([f"You took the {name} back from {p.display_name}."])
            return
        old = getattr(p, "held_item", None)
        p.held_item = item
        lines = [f"{p.display_name} is now holding the {name}."]
        if old:
            lines.append(f"(It let go of the {hms.item_name(old)}.)")
        lines.append("With the Z-Ring, it can use a Z-Move of that type once a battle.")
        self._back_to_bag(lines)

    def on_pokemon_select_shards(self, slot_index):
        from src.pokemon import zpower
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return
        p, item = party[slot_index], self.selected_item
        t = zpower.shard_type(item)
        inv = self.game.story_manager.inventory
        if zpower.tera_type(p) == t:
            self._back_to_bag([f"{p.display_name}'s Tera Type is already {t.title()}."])
        elif inv.get(item, 0) < zpower.SHARDS_TO_CHANGE:
            self._back_to_bag([f"It takes {zpower.SHARDS_TO_CHANGE} {t.title()} Tera Shards to change a Tera Type. "
                               f"You have {inv.get(item, 0)}."])
        else:
            inv[item] -= zpower.SHARDS_TO_CHANGE
            if inv[item] <= 0:
                inv.pop(item)
            p.tera_type = t
            self._back_to_bag([f"{p.display_name}'s Tera Type became {t.title()}!"])

    def on_pokemon_select_tm(self, slot_index):
        from src.pokemon import tms
        party = self.game.story_manager.player_team
        if slot_index < len(party):
            self._back_to_bag(tms.teach(self.game, party[slot_index], self.selected_item))

    def item_works(self, item, p):
        if getattr(p, "is_egg", False):
            return False  # (an Egg can't use items)
        return self._item_works(item, p)

    def _item_works(self, item, p):
        """Would using `item` on p do something? (the party's ABLE / NO EFFECT tags, Jordan 11-02;
        the same tests the item's own use makes, tried on a copy where it changes the Pokemon)."""
        import copy
        if p is None or not item:
            return False
        from src.pokemon import tms, zpower
        if tms.is_tm(item):
            return tms.works_on(self.game, p, item)
        if item in zpower.CRYSTAL_TYPE:
            return True  # (give it, or take it back)
        if zpower.shard_type(item):
            return (zpower.tera_type(p) != zpower.shard_type(item)
                    and self.game.story_manager.inventory.get(item, 0) >= zpower.SHARDS_TO_CHANGE)
        if item == "RARE_CANDY":
            return self.candy_limit(p)[1] is None
        if item in itemlib.MEDICINE:
            return itemlib.medicine_effect(item, copy.copy(p))[0]
        if item == "POTION":
            return 0 < p.current_hp < p.get_max_hp()
        if item == "FULL_HEAL":
            return p.current_hp > 0 and bool(getattr(p, "status", None))
        if item == "REVIVE":
            return p.current_hp <= 0
        if item == "EVERSTONE":
            return True  # (given, or taken back)
        if item in POKEBLOCKS:
            from src.pokemon.contest import MAX_SHEEN, MAX_CONDITION
            return p.sheen < MAX_SHEEN and p.condition.get(POKEBLOCKS[item], 0) < MAX_CONDITION
        from src.pokemon import evolution
        if evolution.item_evolution(self.game, p, item):
            return True
        key = p.name.upper()
        data = self.evo_items_map.get(item, {})
        return key in data or f"{key}_{str(p.form).upper()}" in data

    def candy_limit(self, pokemon):
        """(highest level Rare Candies can reach now, the cap message if it's already there)."""
        from src.world import levels
        cap = min(levels.xp_cap(self.game.story_manager), pokemon.MAX_LEVEL)
        if pokemon.level >= pokemon.MAX_LEVEL:
            return cap, f"{pokemon.display_name} is already Lv 100! The Rare Candy had no effect."
        if pokemon.level >= cap:
            return cap, (f"{pokemon.display_name} is at the level cap (Lv {cap})! The Rare Candy had no effect. "
                         "Beat the next Gym Leader to raise the cap.")
        return cap, None

    def on_pokemon_select_rare_candy(self, slot_index):
        """Pick how many Rare Candies to use (up to the level cap), then use them."""
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return
        pokemon = party[slot_index]
        cap, full = self.candy_limit(pokemon)
        if full:
            self._back_to_bag([full])
            return
        most = min(self.game.story_manager.inventory.get("RARE_CANDY", 0), cap - pokemon.level)
        if most <= 1:
            self.use_rare_candies(slot_index, 1)
            return
        self.game.change_state(ItemCountState(
            self.game, self, pokemon, "RARE_CANDY", most,
            lambda n: n and f"Lv {pokemon.level} -> Lv {pokemon.level + n}",
            lambda n: self.use_rare_candies(slot_index, n)))

    def use_rare_candies(self, slot_index, count):
        party = self.game.story_manager.player_team
        pokemon = party[slot_index]
        if count <= 0:
            self._back_to_bag()
            return
        from src.pokemon import evolution
        from src.pokemon import moves as movelib
        cap, _ = self.candy_limit(pokemon)
        inv = self.game.story_manager.inventory
        count = min(count, inv.get("RARE_CANDY", 0), cap - pokemon.level)
        old_level = pokemon.level
        pokemon.level_up(count)
        inv["RARE_CANDY"] -= count
        if inv["RARE_CANDY"] <= 0:
            del inv["RARE_CANDY"]
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.play()
        used = "a Rare Candy" if count == 1 else f"{count} Rare Candies"
        lines = [f"You used {used} on {pokemon.display_name}.",
                 f"{pokemon.display_name} grew to Lv {pokemon.level}!"]
        if pokemon.level >= cap and cap < pokemon.MAX_LEVEL:
            lines.append(f"{pokemon.display_name} reached the level cap (Lv {cap}). Beat the next Gym Leader to go higher!")
        lines += movelib.learn_new_moves(self.game, pokemon, old_level)  # before any evolution
        ready = evolution.ready_evolutions(self.game, pokemon)
        if ready:
            entry = self.game.story_manager.pick_evolution_branch(ready)
            base_name, next_form = (entry.rsplit("_", 1) + ["normal"])[:2] if "_" in entry else (entry, "normal")
            next_id = self.game.name_to_id.get(base_name.upper())
            if next_id:  # the messages first, then it evolves
                self.game.change_state(self)
                self.refresh_buttons()
                self.game.show_dialogue(lines + [f"What? {pokemon.display_name} is evolving!"], callback=(
                    lambda: self.game.change_state(EvolutionState(
                        self.game, pokemon, next_id, slot_index, next_form=next_form.lower(), context="party",
                        return_state=self.previous_state, choices=ready if len(ready) > 1 else None))))
                return
        self._back_to_bag(lines)

    def _take(self, item):
        inv = self.game.story_manager.inventory
        inv[item] = inv.get(item, 0) - 1
        if inv[item] <= 0:
            inv.pop(item, None)

    def on_pokemon_select_medicine(self, slot_index):
        """Potions, status heals, Revives (src/pokemon/items.py), in or out of battle."""
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return
        p, item = party[slot_index], self.selected_item
        used, lines = itemlib.medicine_effect(item, p)
        if not used:
            self._back_to_bag(lines)
            return
        self._take(item)
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.play()
        label = forms.item_label(item).upper()
        if self.context == "battle":
            battle = self.previous_state
            if p is battle.player_pokemon:
                battle.player_hp = p.current_hp
            self.game.change_state(battle)
            battle.show_message([f"{self.game.player_name} used a {label}!"] + lines, callback=battle.on_item_used)
            return
        self._back_to_bag([f"You used a {label}."] + lines)

    def _use_battle_item(self, item):
        """X items, Dire Hit, Guard Spec.: on the Pokemon in battle, then the foe's turn."""
        battle = self.previous_state
        data, mon = itemlib.BATTLE[item], battle.player_pokemon
        label = forms.item_label(item).upper()
        if "stat" in data:
            lines = battle.change_stages(mon, [[data["stat"], 2]])
            if "won't go any higher" in lines[-1]:
                self.game.change_state(battle)
                battle.show_message(lines, callback=battle.return_to_menu)
                return
        elif "focus" in data:
            if battle.vol(mon).get("focus"):
                self.game.change_state(battle)
                battle.show_message([f"{mon.display_name.upper()} is already getting pumped!"],
                                    callback=battle.return_to_menu)
                return
            battle.vol(mon)["focus"] = data["focus"]
            lines = [f"{mon.display_name.upper()} is getting pumped!"]
        else:
            battle.side(mon)["mist"] = data["mist"]
            lines = ["Your team became shrouded in mist!"]
        self._take(item)
        self.game.change_state(battle)
        battle.show_message([f"{self.game.player_name} used the {label}!"] + lines, callback=battle.on_item_used)

    def _use_field_item(self, item):
        """Repels (wild Pokemon stay away: routes can be left without battling) and Escape Rope."""
        story = self.game.story_manager
        data = itemlib.FIELD[item]
        if "attract" in data:  # Honey: used from a route dungeon's map (its HONEY button)
            self._back_to_bag(["Use HONEY out on a route: tap HONEY on the map to draw in wild Pokemon."])
            return
        if "repel" in data:
            if getattr(story, "repel_routes", 0) > 0:
                self._back_to_bag([f"A Repel is already working ({story.repel_routes} more routes)."])
                return
            story.repel_routes = data["repel"]
            self._take(item)
            self._back_to_bag([f"You used the {forms.item_label(item).upper()}!",
                               f"Wild Pokemon will stay away for the next {data['repel']} routes:",
                               "you can leave them without battling."])
            return
        area = story.get_current_area_data()
        inside = area.get("area_type") == "dungeon" or area.get("battle_type") in ("cave", "indoor", "mountain")
        if not inside:
            self._back_to_bag(["You can only use an Escape Rope in caves and buildings."])
            return
        self._take(item)
        dest, _ = story.whiteout_destination()
        from src.states.overworld import AreaTransitionState
        self.game.change_state(AreaTransitionState(self.game, dest, initial_message="You used the ESCAPE ROPE!"))

    def on_pokemon_select_pokeblock(self, slot_index):
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return
        p = party[slot_index]
        block = self.selected_item
        ate, lines = feed_pokeblock(p, block)
        if ate:
            inv = self.game.story_manager.inventory
            inv[block] -= 1
            if inv[block] <= 0:
                del inv[block]
            if self.game.assets.heal_sfx:
                self.game.assets.heal_sfx.play()
            # A Feebas that has grown enough only needed Beauty: it evolves right away.
            from src.pokemon import evolution
            if p.name.upper() == "FEEBAS" and evolution.ready_evolutions(self.game, p, any_time=True):
                milotic = self.game.name_to_id.get("MILOTIC")
                if milotic:
                    self.game.change_state(EvolutionState(
                        self.game, p, milotic, slot_index, context="party", return_state=self))
                    return
        self._back_to_bag(lines)

    def on_pokemon_select_everstone(self, slot_index):
        """Give the Everstone to a Pokemon (it won't evolve), or take it back."""
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return
        p = party[slot_index]
        inv = self.game.story_manager.inventory
        if getattr(p, "everstone", False):
            p.everstone = False
            self.game.story_manager.add_item("EVERSTONE")
            lines = [f"You took the Everstone back from {p.display_name}.", f"{p.display_name} can evolve again."]
        else:
            p.everstone = True
            inv["EVERSTONE"] = inv.get("EVERSTONE", 0) - 1
            lines = [f"{p.display_name} is now holding the Everstone.", "It won't evolve while it holds it."]
        self.refresh_buttons()
        self._back_to_bag(lines)

    def _back_to_bag(self, lines=None):
        """Return to the Bag, then show the message (showing it first got wiped by the
        screen change, so the player never saw it)."""
        self.game.change_state(self)
        self.refresh_buttons()
        if lines:
            self.game.show_dialogue(lines)

    def on_pokemon_select_potion(self, slot_index):
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return
        p = party[slot_index]

        msg = None
        if p.current_hp <= 0:
            msg = f"Potion has no effect on a fainted {p.display_name}!"
        elif p.current_hp >= p.get_max_hp():
            msg = f"{p.display_name} is already at full health!"
        else:
            heal = p.get_max_hp() // 2
            msg = f"{p.display_name} recovered {min(heal, p.get_max_hp() - p.current_hp)} HP!"
            p.current_hp = min(p.get_max_hp(), p.current_hp + heal)
            self.game.story_manager.inventory["POTION"] -= 1
            if self.game.story_manager.inventory["POTION"] <= 0:
                del self.game.story_manager.inventory["POTION"]
            if self.game.assets.heal_sfx:
                self.game.assets.heal_sfx.play()

            if self.context == "battle":
                if p == self.previous_state.player_pokemon:
                    self.previous_state.player_hp = p.current_hp
                self.game.change_state(self.previous_state)
                self.previous_state.show_message([f"{self.game.player_name} used a POTION!", msg],
                                                 callback=self.previous_state.on_item_used)
                return

        self._back_to_bag([msg])

    def on_pokemon_select_full_heal(self, slot_index):
        """Full Heal: cures burn, paralysis, poison, sleep and freeze."""
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return
        p = party[slot_index]
        if p.current_hp <= 0:
            msg = f"Full Heal has no effect on a fainted {p.display_name}!"
        elif not getattr(p, "status", None):
            msg = f"{p.display_name} has no status problem!"
        else:
            msg = f"{p.display_name} was cured!"
            p.cure_status()
            inv = self.game.story_manager.inventory
            inv["FULL_HEAL"] -= 1
            if inv["FULL_HEAL"] <= 0:
                del inv["FULL_HEAL"]
            if self.game.assets.heal_sfx:
                self.game.assets.heal_sfx.play()
            if self.context == "battle":
                self.game.change_state(self.previous_state)
                self.previous_state.show_message([f"{self.game.player_name} used a FULL HEAL!", msg],
                                                 callback=self.previous_state.on_item_used)
                return
        self._back_to_bag([msg])

    def on_pokemon_select_revive(self, slot_index):
        party = self.game.story_manager.player_team
        if slot_index >= len(party):
            return
        p = party[slot_index]

        if p.current_hp > 0:
            msg = f"{p.display_name} is not fainted!"
        else:
            msg = f"{p.display_name} was revived!"
            p.current_hp = max(1, p.get_max_hp() // 2)
            self.game.story_manager.inventory["REVIVE"] -= 1
            if self.game.story_manager.inventory["REVIVE"] <= 0:
                del self.game.story_manager.inventory["REVIVE"]
            if self.game.assets.heal_sfx:
                self.game.assets.heal_sfx.play()

            if self.context == "battle":
                if p == self.previous_state.player_pokemon:
                    self.previous_state.player_hp = p.current_hp
                self.game.change_state(self.previous_state)
                self.previous_state.show_message([f"{self.game.player_name} used a REVIVE!", msg,
                                                  f"{p.display_name} has {p.current_hp} HP."],
                                                 callback=self.previous_state.on_item_used)
                return

        self._back_to_bag([msg])

    def draw(self):
        """The menu frame (src/ui/theme.py) in the Bag's orange: pocket tabs, item cards, and the
        bar with what the item under the pointer does."""
        screen = self.game.screen
        f = self.game.assets.fonts
        accent = theme.ACCENT["bag"]
        theme.menu_background(screen, accent, "BAG", f["button"], title_x=176)
        Utils.draw_text_outline(screen, f"${self.game.story_manager.money}", f["button"], WHITE,
                                self.game.width - 24, theme.HEADER_H // 2 - 4, align="right",
                                outline_color=theme.shade(accent, 0.45), thickness=3)
        if not self.item_buttons:
            theme.shadow_text(screen, "Nothing in this pocket yet.", f["s_med"], self.list_rect.centerx,
                              self.list_rect.centery, color=(200, 206, 222), shadow=theme.MENU_BG, align="center")

        mouse = pygame.mouse.get_pos()
        hovered = next((b for b in self.item_buttons if b.rect.collidepoint(mouse)), None)
        if hovered is not None:
            from src.pokemon import items as itemlib_
            text = itemlib_.describe(hovered.key) or (
                "Tap to use it." if hovered.usable else "Tap to see when it's used.")
            line = f"{hovered.name}: {text}"
        else:
            line = "Tap an item to use it."
        bf = f["label"]
        from src.ui.dialogue import wrap_text
        right = self.btn_items_up.rect.x - 90 if self.item_page_count > 1 else self.bar_rect.right - 32
        rows = wrap_text(line, bf, right - self.bar_rect.x - 32)[:2]
        theme.draw_textbox(screen, self.bar_rect)
        lh = bf.get_linesize() + 4
        top = self.bar_rect.centery - lh * len(rows) // 2 - 1
        for k, row in enumerate(rows):
            theme.shadow_text(screen, row, bf, self.bar_rect.x + 32, top + k * lh)
        if self.item_page_count > 1:
            theme.shadow_text(screen, f"{self.item_page + 1}/{self.item_page_count}", f["s_med"],
                              self.btn_items_up.rect.x - 16, self.bar_rect.centery - 14, align="right")

        self.game.ui_manager.draw(screen)


class ItemCountState(GameState):
    """How many of an item to use at once (Rare Candies): -10 / -1 / +1 / +10 / MAX, then USE."""

    def __init__(self, game, previous_state, pokemon, item, most, preview, on_use):
        super().__init__(game)
        self.previous_state = previous_state
        self.pokemon, self.item, self.most = pokemon, item, most
        self.preview, self.on_use = preview, on_use
        self.count = 1
        fonts = game.assets.fonts
        cx, y = game.width // 2, game.height - 230
        self.buttons = [Button((cx - 330 + i * 135, y, 120, 64), label, fonts["small"],
                               (lambda d=d: self.change(d)), autosize=False)
                        for i, (label, d) in enumerate((("-10", -10), ("-1", -1), ("+1", 1), ("+10", 10),
                                                        ("MAX", most)))]
        self.buttons.append(Button((cx - 270, y + 90, 250, 70), "USE", fonts["small"],
                                   lambda: self.on_use(self.count), bg_color=GREEN, autosize=False))
        self.buttons.append(Button((cx + 20, y + 90, 250, 70), "CANCEL", fonts["small"],
                                   lambda: self.on_use(0), bg_color=RED, autosize=False))
        img = pokemon.image or pokemon.sidebar_image
        self.sprite = pygame.transform.scale(img, (220, 220)) if img else None

    def change(self, d):
        self.count = max(1, min(self.most, self.count + d))

    def start(self):
        for btn in self.buttons:
            self.game.ui_manager.add_element(btn)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_UP, pygame.K_RIGHT):
                self.change(1)
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_DOWN, pygame.K_LEFT):
                self.change(-1)

    def update(self):
        pass

    def draw(self):
        screen = self.game.screen
        fonts = self.game.assets.fonts
        cx = self.game.width // 2
        from src.world import hms
        name = hms.item_name(self.item).upper()
        theme.menu_background(screen, theme.ACCENT["bag"], "USE HOW MANY?", fonts["button"], title_x=24)
        Utils.draw_text_outline(screen, f"{name}: {self.game.story_manager.inventory.get(self.item, 0)} in the Bag",
                                fonts["label"], WHITE, self.game.width - 24, theme.HEADER_H // 2 - 4, align="right",
                                outline_color=theme.shade(theme.ACCENT["bag"], 0.45), thickness=2)
        card = pygame.Rect(cx - 360, theme.HEADER_H + 20, 720, 340)
        theme.card(screen, card, radius=16)
        if self.sprite:
            spr = fit_sprite(self.sprite, 200, 170)
            screen.blit(spr, spr.get_rect(center=(cx, card.y + 100)))
        theme.shadow_text(screen, self.pokemon.display_name.upper(), fonts["s_med"], cx, card.y + 200, align="center")
        theme.shadow_text(screen, f"x{self.count}", fonts["big"], cx, card.y + 252, align="center")
        theme.shadow_text(screen, f"{self.preview(self.count)}   (up to {self.most})", fonts["label"], cx,
                          card.y + 302, color=(110, 116, 136), align="center")
        self.game.ui_manager.draw(screen)
