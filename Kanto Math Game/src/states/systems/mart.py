"""The Poke Mart."""

import pygame
from src.states.base import GameState
from src.ui.widgets import Button
from src.ui.panels import CommandButton
from src.ui import theme
from src.ui.dialogue import ClassicDialogueBox
from src.utils import Utils
from src.config import WHITE, BLACK, BLUE, RED
from src.pokemon.poffin import BERRY_PRICE
from src.pokemon.contest import POKEBLOCKS, POKEBLOCK_PRICE, CATEGORIES
from src.pokemon import items as itemlib


# [REF-0034: PokeMart System]
class PokeMartState(GameState):
    def __init__(self, game, previous_state, stock=None):
        """stock: sell only these items (e.g. a Contest Hall's Pokéblock stand)."""
        super().__init__(game)
        self.previous_state = previous_state
        self.stock = stock
        self.phase = "SHOP"
        self.shop_buttons = []
        self.current_page = 0
        self.items_per_page = 8
        self.pending_item = None
        self.pending_cost = 0

        self.bottom_rect = Utils.get_full_dialogue_rect(game)

        self.btn_back = Button((20, 20, 100, 50), "EXIT", game.assets.fonts["tiny"], self.exit_shop, bg_color=RED)

        self.btn_prev = Button((self.bottom_rect.left + 10, self.bottom_rect.centery - 25, 50, 50), "<", game.assets.fonts["med"], self.prev_page, visible=False)
        self.btn_next = Button((self.bottom_rect.right - 60, self.bottom_rect.centery - 25, 50, 50), ">", game.assets.fonts["med"], self.next_page, visible=False)

        cx, cy = game.width // 2, game.height // 2
        self.btn_yes = CommandButton((cx - 150, cy + 50, 140, 60), "BUY", game.assets.fonts["button"], self.confirm_purchase, bg_color=theme.POKEMON, autosize=False, visible=False)
        self.btn_no = Button((cx + 30, cy + 50, 120, 60), "CANCEL", game.assets.fonts["small"], self.cancel_purchase, bg_color=RED, autosize=False, visible=False)

        self.dialogue_box = ClassicDialogueBox(self.bottom_rect, [], game.assets.fonts["med"], visible=False)

        self.bg = self._load_building_bg(game, "mart")

        # (no more free Poke Balls on a Mart's first visit: Jordan, 11-07, an old feature)

        self._build_ui()

    WEATHER_ROCKS = {"RAIN": "DAMP_ROCK", "SUN": "HEAT_ROCK", "SAND": "SMOOTH_ROCK", "SNOW": "ICY_ROCK"}

    # Never on an ordinary shelf. The Up-Grade is sold only at Veilstone (Sinnoh) and the Crystal Stone
    # only at Pummelo (Orange Islands), through those areas' "extra_stock".
    NEVER_SOLD = {"UPGRADE", "UP_GRADE", "CRYSTAL_STONE"}

    def _shop_items(self):
        return [i for i in self._stock_items() if i not in self.NEVER_SOLD] + self._extra_stock()

    def _extra_stock(self):
        """An area's own extra shelf ("extra_stock": [{"item", "condition"}]): Pummelo Island sells the
        Crystal Stone once you're the Orange League Champion."""
        if self.stock is not None:
            return []
        flags = self.game.story_manager.story_flags
        return [e["item"] for e in self.game.story_manager.get_current_area_data().get("extra_stock", [])
                if not e.get("condition") or flags.get(e["condition"])]

    def _stock_items(self):
        if self.stock is not None:
            return list(self.stock)
        area = self.game.story_manager.current_area_key
        items = self._town_stock()
        if self._is_department_store():  # X items, drinks, evolution items, Rare Candy
            evo_items = sorted(i for i in self.game.loader.evolution_map.get("EVOLUTION_ITEMS", {})
                               if self._item_allowed(i))
            items += [i for i in itemlib.DEPARTMENT + ["RARE_CANDY", "EVERSTONE"] + evo_items if i not in items]
        return items + self._regional_weather_rocks() + self._contest_items()

    def _town_stock(self):
        """The games' Poke Mart counter (Gen 4 on), by the region's badges: Poke Balls, Potions and
        the status heals first, then Great Balls / Super Potions (1 badge), Hyper Potions and Revives
        (3), Ultra Balls and Full Heals (5), Max Potions (7), Full Restores (8); the second counter's
        balls (Net, Nest, Quick, Dusk, Heal, Dive, Repeat, Timer, Luxury) by badges too. The
        Everstone from 2 badges and Rare Candy at the League are this game's own."""
        story = self.game.story_manager
        badges = len(story.badges.get(story.get_current_region(), []))
        if story.is_region_champion(story.get_current_region()):
            badges = 8
        items = itemlib.standard_stock(badges)
        if badges >= 2:
            items.append("EVERSTONE")
        from src.pokemon import tms, zpower
        items += tms.mart_stock(self.game, badges)  # the TMs for this many badges (Jordan, 11-03)
        items += zpower.mart_stock(story)  # Alola's Z-Crystals, Paldea's Tera Shards
        from src.states.overworld import is_league
        if is_league(story.get_current_area_data().get("gym")):
            items += [i for i in ("REVIVE", "RARE_CANDY", "FULL_RESTORE", "MAX_POTION") if i not in items]
        return items

    def _item_allowed(self, item):
        """An evolution item is only sold once something it evolves can evolve here
        (Kanto and Johto keep later regions' items until those regions are played)."""
        targets = self.game.loader.evolution_map.get("EVOLUTION_ITEMS", {}).get(item) or {}
        if not isinstance(targets, dict) or not targets:
            return True
        from src.pokemon import evolution
        ids = [self.game.name_to_id.get(str(t).split("_")[0].upper()) for t in targets.values()]
        return any(evolution.evolution_allowed(self.game, i) for i in ids if i)

    def _contest_items(self):
        """Towns with a Contest Hall stock Pokéblocks."""
        options = self.game.story_manager.get_current_area_data().get("explore_options", [])
        if any(o.get("target") == "contest_hall" for o in options):
            return list(POKEBLOCKS)
        return []

    def _regional_weather_rocks(self):
        """Rocks for the kinds of weather found in this region this season
        (Galar's Wild Area has them all)."""
        from src.world import seasons
        found = seasons.region_weathers(self.game, self.game.story_manager.get_current_region())
        return [rock for w, rock in self.WEATHER_ROCKS.items() if w in found]

    def _is_department_store(self):
        """Celadon/Goldenrod, or any area flagged "department_store" (sells evolution items)."""
        story = self.game.story_manager
        return (story.current_area_key in ["CELADON_CITY", "GOLDENROD_CITY"]
                or bool(story.get_current_area_data().get("department_store")))

    # ---------------------------------------------------------------- prices
    BASE_PRICES = {"POKE_BALLS": 1000, "RARE_CANDY": 10000, "POTION": 500, "FULL_HEAL": 600,
                   "REVIVE": 1000, "EVERSTONE": 3000}

    def _price(self, item):
        from src.pokemon import tms, zpower
        if tms.is_tm(item):
            return tms.price(self.game, item)
        if zpower.shard_type(item):
            return zpower.SHARD_PRICE
        if item in zpower.CRYSTAL.values():
            return 5000
        if itemlib.price(item):
            return itemlib.price(item)
        if item in self.BASE_PRICES:
            return self.BASE_PRICES[item]
        return (2000 if item in self.WEATHER_ROCKS.values()
                else 5000 if item.endswith(("ITE", "ITE_X", "ITE_Y"))
                else POKEBLOCK_PRICE if item in POKEBLOCKS
                else BERRY_PRICE if item.endswith("_BERRY") else 10000)

    def _name(self, item, qty=1):
        from src.pokemon import tms
        if tms.is_tm(item):
            return tms.label(self.game, item)
        if item == "POKE_BALLS":
            return "Poké Balls (x5)" if qty == 1 else f"{qty} packs of 5 Poké Balls"
        from src.pokemon import catching
        name = (catching.label(item).title() if item in catching.BALLS
                else item.replace("_", " ").title().replace(" Fossil", "").replace("X Sp ", "X Sp. "))
        return name if qty == 1 else f"{qty} x {name}"

    def _icon(self, item, size=48):
        icon = (self.game.assets.ui_ball if item == "POKE_BALLS"
                else self.game.assets.get_item_image(item) or self.game.assets.get_item_image(item.replace("X_SP_", "X_SP_")
                                                                                              .replace("PARALYZE", "PARLYZ"))
                or (self.game.assets.get_item_image("POTION") if item in itemlib.MEDICINE else None))
        return pygame.transform.scale(icon, (size, size)) if icon else None

    def _sellable(self):
        """Items in the Bag the Mart will buy back (never key items, gifts or Mega Stones)."""
        story = self.game.story_manager
        key_items = set(self.game.loader.area_data.get("GAME_CONFIG", {}).get("KEY_ITEMS", []))
        evo_items = set(self.game.loader.evolution_map.get("EVOLUTION_ITEMS", {}).keys())
        shop_kinds = (set(self.BASE_PRICES) | evo_items | set(self.WEATHER_ROCKS.values())
                      | set(POKEBLOCKS) | set(itemlib.MEDICINE) | set(itemlib.BATTLE) | set(itemlib.FIELD)
                      | set(itemlib.BALL_PRICES) | set(itemlib.VITAMINS) | set(itemlib.VALUABLES) | set(itemlib.HELD)) - {"POKE_BALLS", "PREMIER_BALL"}
        return [k for k, q in sorted(story.inventory.items())
                if q > 0 and k not in key_items and k not in self.NEVER_SOLD
                and (k in shop_kinds or k.endswith("_BERRY"))]

    def _have(self, item):
        story = self.game.story_manager
        return story.balls_left if item == "POKE_BALLS" else story.inventory.get(item, 0)

    # ---------------------------------------------------------------- layout
    def _build_ui(self):
        """The menu frame in the Mart's blue: EXIT, BUY / SELL and the money in the header, the
        shelf as white item cards, the text box below for what the item under the pointer does
        (and the clerk's words); the quantity on a card over the shelf."""
        g = self.game
        w = g.width
        fonts = g.assets.fonts
        H = theme.HEADER_H
        self.mode = "BUY"
        self.qty = 1
        self.panel = pygame.Rect(24, H + 16, w - 48, self.bottom_rect.top - 12 - H - 16)
        # Jordan (11-03): the shelf in categories (fewer pages to turn): a row of tabs over it.
        self.category = None
        self.cat_buttons = {}
        tab_w = (self.panel.w - 10 * (len(self.CATEGORIES) - 1)) // len(self.CATEGORIES)
        for k, (cat, color) in enumerate(self.CATEGORIES):
            self.cat_buttons[cat] = CommandButton((self.panel.x + k * (tab_w + 10), self.panel.y, tab_w, 50), cat,
                                                  fonts["label"], (lambda c=cat: self.set_category(c)),
                                                  bg_color=theme.TAB_OFF, autosize=False)
        self.panel = pygame.Rect(self.panel.x, self.panel.y + 62, self.panel.w, self.panel.h - 62)
        self.btn_back = CommandButton((16, 14, 140, 56), "EXIT", fonts["button"], self.exit_shop,
                                      bg_color=theme.BACK, autosize=False)
        self.btn_buy_tab = CommandButton((w // 2 - 170, 14, 160, 56), "BUY", fonts["button"],
                                         lambda: self.set_mode("BUY"), bg_color=theme.TAB_OFF, autosize=False)
        self.btn_sell_tab = CommandButton((w // 2 + 10, 14, 160, 56), "SELL", fonts["button"],
                                          lambda: self.set_mode("SELL"), bg_color=theme.TAB_OFF, autosize=False)
        foot = self.panel.bottom - 50
        self.btn_prev = CommandButton((self.panel.x, foot, 80, 50), "<", fonts["button"], self.prev_page,
                                      bg_color=theme.ACCENT["mart"], autosize=False)
        self.btn_next = CommandButton((self.panel.right - 80, foot, 80, 50), ">", fonts["button"], self.next_page,
                                      bg_color=theme.ACCENT["mart"], autosize=False)
        self.card_h, self.cols = 52, 3  # (three columns of compact cards: fewer pages to turn)
        rows = max(1, (self.panel.h - 62 + 10) // (self.card_h + 10))
        self.items_per_page = rows * self.cols
        # the quantity card
        self.qty_rect = pygame.Rect(0, 0, min(760, w - 60), 380)
        self.qty_rect.center = (w // 2, (self.panel.top + self.bottom_rect.top) // 2)
        q = self.qty_rect
        by = q.y + 150
        self.qty_buttons = [
            CommandButton((q.x + 40 + k * 120, by, 110, 56), label, fonts["button"], cb,
                          bg_color=theme.RUN, autosize=False)
            for k, (label, cb) in enumerate((("-1", lambda: self.change_qty(-1)), ("+1", lambda: self.change_qty(1)),
                                             ("+10", lambda: self.change_qty(10)), ("MAX", self.max_qty)))]
        self.btn_yes = CommandButton((q.centerx - 230, q.bottom - 76, 210, 60), "BUY", fonts["button"],
                                     self.confirm_purchase, bg_color=theme.POKEMON, autosize=False)
        self.btn_no = CommandButton((q.centerx + 20, q.bottom - 76, 210, 60), "CANCEL", fonts["button"],
                                    self.cancel_purchase, bg_color=theme.BACK, autosize=False)

    def set_mode(self, mode):
        self.mode = mode
        self.current_page = 0
        self.category = None
        self.cancel_purchase()

    CATEGORIES = (("BALLS", theme.RUN), ("MEDICINE", theme.POKEMON), ("BATTLE", theme.FIGHT),
                  ("EVOLUTION", theme.MEGA), ("TMs", theme.BAG), ("OTHER", theme.BACK))

    def category_of(self, item):
        from src.pokemon import catching, tms
        if item == "POKE_BALLS" or item in catching.BALLS or item.endswith("_BALL"):
            return "BALLS"
        if tms.is_tm(item):
            return "TMs"
        if item in itemlib.MEDICINE:
            return "MEDICINE"
        if item in itemlib.BATTLE or item in self.WEATHER_ROCKS.values():
            return "BATTLE"
        evo = self.game.loader.evolution_map.get("EVOLUTION_ITEMS", {})
        if item in evo or item == "EVERSTONE" or item.endswith(("ITE", "ITE_X", "ITE_Y", "_STONE")):
            return "EVOLUTION"
        return "OTHER"

    def _categories(self):
        """The tabs with something in them (BUY: on the shelf; SELL: in your Bag)."""
        items = self._shop_items() if self.mode == "BUY" else self._sellable()
        have = {self.category_of(i) for i in items}
        return [c for c, _ in self.CATEGORIES if c in have]

    def set_category(self, cat):
        self.category = cat
        self.current_page = 0
        self.refresh_buttons()

    def _list(self):
        items = self._shop_items() if self.mode == "BUY" else self._sellable()
        cats = self._categories()
        if self.category not in cats:
            self.category = cats[0] if cats else None
        return [i for i in items if self.category_of(i) == self.category]

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_buttons()

    def next_page(self):
        if (self.current_page + 1) * self.items_per_page < len(self._list()):
            self.current_page += 1
            self.refresh_buttons()

    def refresh_buttons(self):
        ui = self.game.ui_manager
        ui.elements.clear()
        self.btn_buy_tab.bg_color = theme.BAG if self.mode == "BUY" else theme.TAB_OFF
        self.btn_sell_tab.bg_color = theme.BAG if self.mode == "SELL" else theme.TAB_OFF
        for b in (self.btn_back, self.btn_buy_tab, self.btn_sell_tab):
            ui.add_element(b)
        self.shop_buttons = []
        self._list()  # (picks a category with items in it)
        cats = self._categories()
        for cat, color in self.CATEGORIES:
            btn = self.cat_buttons[cat]
            btn.set_visibility(self.phase != "QTY" and cat in cats)
            btn.bg_color = color if cat == self.category else theme.TAB_OFF
            if btn.visible:
                ui.add_element(btn)
        if self.phase == "QTY":
            self.btn_yes.text = self.mode
            self.btn_prev.set_visibility(False)
            self.btn_next.set_visibility(False)
            for b in self.qty_buttons + [self.btn_yes, self.btn_no]:
                b.set_visibility(True)
                ui.add_element(b)
        else:
            for b in self.qty_buttons + [self.btn_yes, self.btn_no]:
                b.set_visibility(False)
            items = self._list()
            pages = max(1, (len(items) + self.items_per_page - 1) // self.items_per_page)
            self.current_page = min(self.current_page, pages - 1)
            self.btn_prev.set_visibility(self.current_page > 0)
            self.btn_next.set_visibility(self.current_page < pages - 1)
            ui.add_element(self.btn_prev)
            ui.add_element(self.btn_next)
            start = self.current_page * self.items_per_page
            col_w = (self.panel.w - 12 * (self.cols - 1)) // self.cols
            for i, item in enumerate(items[start:start + self.items_per_page]):
                r, c = divmod(i, self.cols)
                rect = (self.panel.x + c * (col_w + 12), self.panel.y + r * (self.card_h + 10), col_w, self.card_h)
                btn = Button(rect, "", self.game.assets.fonts["tiny"],
                             lambda k=item: self.init_purchase(k), bg_color=(52, 98, 190), autosize=False)
                btn.item_key = item
                self.shop_buttons.append(btn)
                ui.add_element(btn)
        ui.add_element(self.dialogue_box)

    # ---------------------------------------------------------------- buying and selling
    def _unit_price(self, item):
        return self._price(item) if self.mode == "BUY" else self._price(item) // 2

    def _max_qty(self):
        item = self.pending_item
        if self.mode == "SELL":
            return max(1, self._have(item))
        price = self._unit_price(item)
        afford = self.game.story_manager.money // price if price else 99
        from src.pokemon import tms
        if tms.is_tm(item):
            return 1  # (a TM is used again and again)
        if item == "POKE_BALLS":
            room = (self.game.story_manager.MAX_ITEMS - self._have(item)) // 5
        else:
            room = self.game.story_manager.MAX_ITEMS - self._have(item)
        return max(1, min(99, afford, room))

    def init_purchase(self, item_key, price=None):
        self.pending_item = item_key
        self.pending_cost = self._unit_price(item_key) if price is None else price
        self.qty = 1
        self.phase = "QTY"
        self.dialogue_box.set_visibility(False)
        self.refresh_buttons()

    def change_qty(self, step):
        self.qty = max(1, min(self._max_qty(), self.qty + step))

    def max_qty(self):
        self.qty = self._max_qty()

    def confirm_purchase(self):
        story = self.game.story_manager
        item, qty = self.pending_item, self.qty
        total = self._unit_price(item) * qty
        if self.mode == "SELL":
            qty = min(qty, self._have(item))
            total = self._unit_price(item) * qty
            story.inventory[item] = story.inventory.get(item, 0) - qty
            story.money += total
            lines = [f"You sold {self._name(item, qty)} for ${total:,}.", f"You now have ${story.money:,}."]
        elif story.money < total:
            lines = ["You don't have enough money!",
                     f"That's ${total:,}, and you have ${story.money:,}. You need ${total - story.money:,} more."]
        else:
            if item == "POKE_BALLS":
                if story.MAX_ITEMS - story.balls_left < 5 * qty:
                    self._show([f"Your Bag can only hold {story.MAX_ITEMS} Poké Balls!"])
                    return
                story.balls_left += 5 * qty
                if qty >= 2:
                    story.add_item("PREMIER_BALL", qty // 2)
            elif story.add_item(item, qty) < qty:
                self._show([f"You can't carry more than {story.MAX_ITEMS} of those!"])
                return
            story.money -= total
            if self.game.assets.heal_sfx:
                self.game.assets.heal_sfx.play()
            lines = [f"You bought {self._name(item, qty)} for ${total:,}!", f"You have ${story.money:,} left."]
            if item == "POKE_BALLS" and qty >= 2:
                lines.insert(1, f"You also got {qty // 2} Premier Ball{'s' if qty >= 4 else ''} as a bonus!")
        self._show(lines)

    def _show(self, lines):
        self.phase = "SHOP"
        self.pending_item = None
        self.refresh_buttons()
        self.dialogue_box.reset(lines)
        self.dialogue_box.callback = self.cancel_purchase
        self.dialogue_box.set_visibility(True)

    def cancel_purchase(self):
        self.phase = "SHOP"
        self.dialogue_box.set_visibility(False)
        self.pending_item = None
        self.refresh_buttons()

    def start(self):
        self.game.ui_manager.elements.clear()
        if self.phase == "DIALOGUE":
            self.game.ui_manager.add_element(self.dialogue_box)
        else:
            self.refresh_buttons()

    def on_welcome_dialogue_end(self):
        self.phase = "SHOP"
        self.dialogue_box.set_visibility(False)
        self.refresh_buttons()

    def _load_building_bg(self, game, type_suffix):
        box_top = Utils.get_full_dialogue_rect(game).top
        shared = game.assets.get_region_building(game.story_manager.get_current_region(), type_suffix)
        if shared:  # the region's one shop (Kalos's is inside its Pokemon Center)
            return pygame.transform.scale(shared, (game.width, box_top))
        area_data = game.story_manager.get_current_area_data()
        json_key = "pokecenter" if type_suffix == "center" else "pokemart"
        bg_config = area_data.get("backgrounds", {}).get(json_key)

        area_key = game.story_manager.current_area_key
        first_part = area_key.split('_')[0].lower()
        fallback_name = f"{first_part}_city_{type_suffix}.png"
        # The town's own [area_key]_mart.png first (fight_area_mart.png, not fight_city_mart.png).
        own_name = f"{area_key.lower()}_{type_suffix}.png"

        filenames = [n for n in dict.fromkeys([bg_config, own_name, fallback_name]) if n]
        box_top = Utils.get_full_dialogue_rect(game).top

        for filename in filenames:
            img = game.assets.get_background(filename)
            if img:
                return pygame.transform.scale(img, (game.width, box_top))

        img = game.assets.get_region_default_building(area_data, type_suffix)
        if img:
            return pygame.transform.scale(img, (game.width, box_top))

        img = game.assets.get_generic_background("mart")
        if img:
            return pygame.transform.scale(img, (game.width, box_top))
        bg = pygame.Surface((game.width, box_top))
        bg.fill(BLUE)
        return bg

    def exit_shop(self):
        self.game.change_state(self.previous_state)

    def handle_events(self, events):
        if self.phase == "DIALOGUE":
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.dialogue_box.handle_event(event)

    def update(self):
        if self.dialogue_box.visible:
            self.dialogue_box.update()

    # ---------------------------------------------------------------- drawing
    def draw(self):
        screen, fonts = self.game.screen, self.game.assets.fonts
        w = self.game.width
        if self.phase == "DIALOGUE":  # the clerk's welcome, in the shop itself
            screen.fill(BLACK)
            screen.blit(self.bg, (0, 0))
            self.game.ui_manager.draw(screen)
            return
        accent = theme.ACCENT["mart"]
        theme.menu_background(screen, accent, "POKé MART", fonts["button"], title_x=176)
        story = self.game.story_manager
        Utils.draw_text_outline(screen, f"${story.money:,}", fonts["button"], WHITE, w - 24, theme.HEADER_H // 2 - 4,
                                align="right", outline_color=theme.shade(accent, 0.45), thickness=3)
        for b in (self.btn_back, self.btn_buy_tab, self.btn_sell_tab):
            b.draw(screen)
        if self.phase != "QTY":
            for b in self.cat_buttons.values():
                if b.visible:
                    b.draw(screen)

        hovered = None
        if self.phase == "QTY":
            self._draw_qty()
        else:
            mouse = pygame.mouse.get_pos()
            for btn in self.shop_buttons:
                self._draw_card(btn)
                if btn.rect.collidepoint(mouse):
                    hovered = btn.item_key
            items = self._list()
            pages = max(1, (len(items) + self.items_per_page - 1) // self.items_per_page)
            if not items:
                msg = "Nothing in your Bag to sell." if self.mode == "SELL" else "Sold out!"
                theme.shadow_text(screen, msg, fonts["s_med"], self.panel.centerx, self.panel.centery,
                                  color=(200, 206, 222), shadow=theme.MENU_BG, align="center")
            elif pages > 1:
                self.btn_prev.draw(screen)
                self.btn_next.draw(screen)
                Utils.draw_text_outline(screen, f"Page {self.current_page + 1}/{pages}", fonts["label"], WHITE,
                                        self.panel.centerx, self.btn_prev.rect.centery)
        if self.dialogue_box.visible:
            self.dialogue_box.draw(screen)
        else:  # the text box: what the item under the pointer does
            if hovered:
                line = f"{self._name(hovered)}: {itemlib.describe(hovered) or 'A useful item.'}"
            elif self.phase == "QTY":
                line = "How many? Then BUY." if self.mode == "BUY" else "How many? Then SELL."
            else:
                line = "What would you like?" if self.mode == "BUY" else "What would you like to sell?"
            from src.ui.dialogue import wrap_text
            rows = wrap_text(line, fonts["dialog"], self.bottom_rect.w - 80)[:2]
            theme.draw_textbox(screen, self.bottom_rect)
            lh = int(fonts["dialog"].get_linesize() * 1.2)
            top = self.bottom_rect.centery - lh * len(rows) // 2
            for k, row in enumerate(rows):
                theme.shadow_text(screen, row, fonts["dialog"], self.bottom_rect.x + 40, top + k * lh)

    def _draw_card(self, btn):
        """An item on the shelf: icon, name, how many you have, the price."""
        screen, fonts = self.game.screen, self.game.assets.fonts
        item, r = btn.item_key, btn.rect
        theme.card(screen, r, hover=r.collidepoint(pygame.mouse.get_pos()), accent=theme.ACCENT["mart"])
        icon = self._icon(item, 38)
        if icon:
            screen.blit(icon, icon.get_rect(center=(r.x + 30, r.centery)))
        price = self._unit_price(item)
        label = f"${price:,}" if self.mode == "BUY" else f"sells ${price:,}"
        name = self._name(item)  # the name on top, "In Bag" and the price below it
        room = r.w - 56 - 12
        font = fonts["label"] if fonts["label"].size(name)[0] <= room else fonts["caption"]
        theme.shadow_text(screen, name, font, r.x + 56, r.y + 4)
        theme.shadow_text(screen, f"In Bag: {self._have(item)}", fonts["caption"], r.x + 56, r.bottom - 22,
                          color=(110, 116, 136))
        theme.shadow_text(screen, label, fonts["caption"], r.right - 14, r.bottom - 22, color=(176, 120, 16),
                          align="right")

    def _draw_qty(self):
        """The quantity card: the item, -1 / +1 / +10 / MAX, the sum, BUY / CANCEL."""
        screen, fonts = self.game.screen, self.game.assets.fonts
        q = self.qty_rect
        item = self.pending_item
        theme.card(screen, q, selected=True, accent=theme.ACCENT["mart"], radius=16)
        icon = self._icon(item, 64)
        if icon:
            screen.blit(icon, (q.x + 30, q.y + 26))
        verb = "BUY" if self.mode == "BUY" else "SELL"
        theme.shadow_text(screen, f"{verb} {self._name(item).upper()}", fonts["button"], q.x + 110, q.y + 26)
        price = self._unit_price(item)
        theme.shadow_text(screen, f"${price:,} each   (you have {self._have(item)})", fonts["label"], q.x + 110,
                          q.y + 66, color=(110, 116, 136))
        theme.shadow_text(screen, f"x{self.qty}", fonts["big"], q.right - 40, q.y + 150, align="right")
        for b in self.qty_buttons:
            b.draw(screen)
        total = price * self.qty
        money = self.game.story_manager.money
        after = money - total if self.mode == "BUY" else money + total
        theme.shadow_text(screen, f"{self.qty} x ${price:,} = ${total:,}", fonts["s_med"], q.centerx, q.y + 240,
                          align="center")
        sign = "-" if self.mode == "BUY" else "+"
        theme.shadow_text(screen, f"Money: ${money:,} {sign} ${total:,} = ${after:,}", fonts["label"], q.centerx,
                          q.y + 272, color=theme.HP_RED if after < 0 else (110, 116, 136), align="center")
        self.btn_yes.draw(screen)
        self.btn_no.draw(screen)
