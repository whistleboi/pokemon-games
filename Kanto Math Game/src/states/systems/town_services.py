"""Town services: the Bike Shop, the Game Corner's counter, fossil revival and the Unown Report."""

import pygame
import os
from src.states.base import GameState
from src.ui.widgets import Button
from src.ui.panels import CommandButton
from src.ui import theme
from src.ui.dialogue import ClassicDialogueBox
from src.utils import Utils
from src.config import WHITE, BLACK, GREEN, RED, GOLD
from src.pokemon.data import Pokemon
from src.states.battle import TrainerBattleState, TrainerIntroState
import random
from src.states.systems.pokemath import PokeMathInfiniteState
from src.ui.mon_tags import fit_sprite, draw_shiny_star


# [REF-0061: Bike Shop State]
class BikeShopState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.bg = self._load_bg(game)
        self.clerk_sprite = game.assets.get_trainer_image("supernerd.png")

        inv = self.game.story_manager.inventory
        has_voucher = inv.get("BIKE_VOUCHER", 0) > 0
        has_bike = inv.get("BICYCLE", 0) > 0

        if has_bike:
            lines = ["How's that bike treating you?", "Those Miracle Cycles are top of the line!"]
        elif self.game.story_manager.current_area_key == "GOLDENROD_CITY":
            # HeartGold/SoulSilver: the new Goldenrod shop has no customers yet, so it lends you a
            # bike to ride around and show off (Grok's Johto walk: there was no Bike Shop).
            lines = [
                "Welcome! We just opened, but nobody knows about us yet...",
                "Tell you what: ride one of our bikes around Johto and show it off for us!",
                "You received the BICYCLE!"
            ]
            inv["BICYCLE"] = 1
            if self.game.assets.heal_sfx:
                self.game.assets.heal_sfx.play()
        elif has_voucher:
            lines = [
                "Is that from Misty? Oh wow, she's pretty...",
                "Umm, forget what I said about it being dangerous.",
                "Just wear a helmet or whatever.",
                "Just tell Misty I gave you a bike. And that my arms look bigger. Please.",
                "You received the BICYCLE!"
            ]
            inv["BICYCLE"] = 1
            inv["BIKE_VOUCHER"] -= 1
            if self.game.assets.heal_sfx:
                self.game.assets.heal_sfx.play()
        else:
            lines = [
                "I'm out of normal bikes right now.",
                "I have a dangerous one, but only a strong trainer could handle the speed.",
                "You need a BIKE VOUCHER to get one."
            ]

        self.dialogue_box = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(game),
            lines,
            game.assets.fonts["med"],
            callback=self.go_back
        )

    def _load_bg(self, game):
        path = os.path.join(game.assets.kanto_backgrounds_dir, "cerulean_bike_shop.png")
        box_top = Utils.get_full_dialogue_rect(game).top
        if os.path.exists(path):
            return pygame.transform.scale(pygame.image.load(path).convert(), (game.width, box_top))
        bg = pygame.Surface((game.width, box_top))
        bg.fill((30, 30, 50))
        return bg

    def go_back(self):
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)

    def handle_events(self, events):
        pass

    def update(self):
        self.dialogue_box.update()

    def draw(self):
        self.game.screen.fill(BLACK)
        self.game.screen.blit(self.bg, (0, 0))
        if self.clerk_sprite:
            rect = self.clerk_sprite.get_rect(center=(self.game.width//2, self.game.height*0.45))
            self.game.screen.blit(self.clerk_sprite, rect)
        self.dialogue_box.draw(self.game.screen)


# [REF-0062: Celadon Game Corner System]
class GameCornerState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.bg = self._load_bg(game)
        self.npc_sprite = game.assets.get_trainer_image("gentleman.png")

        self.flags = self.game.story_manager.story_flags
        self.cleared = self.flags.get("game_corner_cleared", False)
        self.rocket_progress = self.game.story_manager.story_flags.get("game_corner_rocket_progress", 0)

        self.phase = "START"

        has_case = self.game.story_manager.inventory.get("COIN_CASE", 0) > 0
        if has_case:
            lines = ["Is that a Coin Case? That means you have money!",
                     "Come on in, kid, have fun!",
                     "Would you like to play PokeMath Infinite?"]
        else:
            lines = ["This place is too dangerous for kids.",
                     "Come back when you have a COIN CASE!"]
            self.phase = "DENIED"

        self.dialogue_box = ClassicDialogueBox(
            Utils.get_full_dialogue_rect(game),
            lines,
            game.assets.fonts["med"],
            visible=True,
            callback=self.go_back if not has_case else None
        )

        self.btn_yes = Button((0, 0, 0, 0), "YES", game.assets.fonts["small"],
                              self.start_infinite, bg_color=GREEN,
                              visible=False, autosize=False)
        self.btn_no = Button((0, 0, 0, 0), "NO", game.assets.fonts["small"],
                             self.decline_infinite, bg_color=RED,
                             visible=False, autosize=False)
        self.menu_buttons = []

    def _load_bg(self, game):
        path = os.path.join(game.assets.kanto_backgrounds_dir,
                            "celadon_game_corner.png")
        box_top = Utils.get_full_dialogue_rect(game).top
        if os.path.exists(path):
            return pygame.transform.scale(pygame.image.load(path).convert(),
                                          (game.width, box_top))
        bg = pygame.Surface((game.width, box_top))
        bg.fill((20, 20, 40))
        return bg

    def start_infinite(self):
        self.game.change_state(PokeMathInfiniteState(self.game, self))

    def decline_infinite(self):
        self.show_main_menu()

    def show_main_menu(self, line=None):
        # 11-01 (Jordan): the Slots and Voltorb Flip from the fan games' Essentials set, played with
        # coins (bought here) for the Prize Counter (src/states/game_corner.py).
        # 11-02 (Jordan): a cleaner counter. Your money and coins on top, the GAMES and the COIN COUNTER
        # (50 / 100 / 500 / 1,000 coins, each with its price) side by side, PRIZES and LEAVE below.
        from src.states import game_corner as gc
        from src import minigames
        story = self.game.story_manager
        won = minigames.beaten(self.game)
        self.phase = "MAIN_MENU"
        self.dialogue_box.reset(line or "Buy coins at the counter, then try your luck!")
        self.btn_yes.set_visibility(False)
        self.btn_no.set_visibility(False)
        self.clear_menu()

        f = self.game.assets.fonts
        w, top = self.game.width, Utils.get_full_dialogue_rect(self.game).top
        margin, gap = 40, 20
        self.header_rect = pygame.Rect(margin, 14, w - 2 * margin, 66)
        bottom_y = top - 78
        half = (w - 2 * margin - gap) // 2
        panel_h = 58 + 3 * 72 + 2 * 20 + 52  # title, three rows of buttons (GYM GAMES the last), the note
        room = bottom_y - self.header_rect.bottom
        self.games_rect = pygame.Rect(margin, self.header_rect.bottom + max(0, (room - panel_h) // 2), half, panel_h)
        self.counter_rect = pygame.Rect(self.games_rect.right + gap, self.games_rect.y, half, self.games_rect.h)

        def grid(panel, specs):
            bw, bh = (panel.w - 3 * 18) // 2, 72
            y0 = panel.y + 58
            for i, (text, sub, cb, color) in enumerate(specs):
                r, c = divmod(i, 2)
                rect = (panel.x + 18 + c * (bw + 18), y0 + r * (bh + 20), bw, bh)
                if i == len(specs) - 1 and len(specs) % 2:  # an odd one out: the whole row
                    rect = (panel.x + 18, y0 + r * (bh + 20), 2 * bw + 18, bh)
                self._menu_add(gc.PriceButton(rect, text, sub, f["label"], f["caption"], cb, color))

        grid(self.games_rect, [
            ("SLOTS", "Bet 1-3 coins", self.start_slot_machine, theme.FIGHT),
            ("VOLTORB FLIP", "Flip for coins", self.start_voltorb_flip, theme.POKEMON),
            ("BLACKJACK", "Beat Meowth to 21", self.start_blackjack, theme.MEGA),
            ("POKEMATH", "Math for money", self.start_infinite, theme.RUN),
            # the Gym games you've won (Jordan, 11-06), to play again for coins
            ("GYM GAMES", f"{len(won)} won so far" if won else "Win a Gym's challenge first",
             self.open_gym_games if won else None, theme.POKEMON)])
        full = gc.coins(story) >= gc.MAX_COINS
        grid(self.counter_rect, [
            (f"{n:,} COINS", f"${gc.coin_cost(n):,}",
             (lambda n=n: self.buy_coins(n)) if story.money >= gc.coin_cost(n) and not full else None, theme.BAG)
            for n in gc.COIN_PACKS])

        bottom = [("PRIZES", self.open_shop, theme.BAG)]
        if story.current_area_key == "CELADON_CITY" and not self.cleared:
            bottom.insert(0, ("STAIRS", self.check_stairs, theme.TAB_OFF))
        bottom.append(("LEAVE", self.go_back, theme.BACK))
        bw = 220
        x0 = w // 2 - (len(bottom) * (bw + gap) - gap) // 2
        for i, (text, cb, color) in enumerate(bottom):
            self._menu_add(CommandButton((x0 + i * (bw + gap), bottom_y, bw, 60), text, f["button"], cb,
                                         bg_color=color, autosize=False))

    def _menu_add(self, btn):
        self.menu_buttons.append(btn)
        self.game.ui_manager.add_element(btn)

    def _draw_main_menu(self, screen):
        """The counter's panels behind its buttons: the wallet bar, GAMES and COIN COUNTER."""
        from src.states import game_corner as gc
        f, story = self.game.assets.fonts, self.game.story_manager
        shade = pygame.Surface((self.game.width, Utils.get_full_dialogue_rect(self.game).top), pygame.SRCALPHA)
        shade.fill((10, 10, 24, 120))
        screen.blit(shade, (0, 0))
        bar = self.header_rect
        theme.draw_panel(screen, bar)
        Utils.draw_text_outline(screen, "GAME CORNER", f["button"], WHITE, bar.x + 28 + f["button"].size("GAME CORNER")[0] // 2,
                                bar.centery, outline_color=theme.PANEL_BORDER, thickness=2)
        x = bar.right - 24
        for label, value, color in (("COINS", f"{gc.coins(story):,}", theme.BAG),
                                    ("MONEY", f"${story.money:,}", theme.POKEMON)):
            chip = pygame.Rect(0, 0, max(200, f["label"].size(value)[0] + 120), 44)
            chip.midright = (x, bar.centery)
            pygame.draw.rect(screen, theme.shade(color, 0.55), chip, border_radius=12)
            pygame.draw.rect(screen, color, chip, 3, border_radius=12)
            Utils.draw_text_outline(screen, label, f["caption"], WHITE, chip.x + 44, chip.centery,
                                    outline_color=theme.PANEL_BORDER, thickness=2)
            Utils.draw_text_outline(screen, value, f["label"], WHITE, chip.right - 16 - f["label"].size(value)[0] // 2,
                                    chip.centery, outline_color=theme.PANEL_BORDER, thickness=2)
            x = chip.x - 16
        for rect, title, note in ((self.games_rect, "GAMES", "Win coins to spend on prizes"),
                                  (self.counter_rect, "COIN COUNTER", f"${gc.COIN_PRICE} per coin  |  holds {gc.MAX_COINS:,}")):
            theme.draw_panel(screen, rect)
            Utils.draw_text_outline(screen, title, f["label"], WHITE, rect.centerx, rect.y + 30,
                                    outline_color=theme.PANEL_BORDER, thickness=2)
            Utils.draw_text_outline(screen, note, f["caption"], (214, 222, 246), rect.centerx, rect.bottom - 24,
                                    outline_color=theme.PANEL_BORDER, thickness=2)

    def buy_coins(self, n=50):
        from src.states import game_corner as gc
        self.show_main_menu(gc.buy_coins(self.game.story_manager, n))

    def open_gym_games(self):
        from src.states.game_corner import GymGamesState
        self.clear_menu()
        self.game.change_state(GymGamesState(self.game, self))

    def start_slot_machine(self):
        from src.states.game_corner import SlotsState
        self.clear_menu()
        self.game.change_state(SlotsState(self.game, self, background=self.bg))

    def start_voltorb_flip(self):
        from src.states.game_corner import VoltorbFlipState
        self.clear_menu()
        self.game.change_state(VoltorbFlipState(self.game, self, background=self.bg))

    def start_blackjack(self):
        from src.states.game_corner import BlackjackState
        self.clear_menu()
        self.game.change_state(BlackjackState(self.game, self, background=self.bg))

    def open_shop(self):
        from src.states.game_corner import PrizeCounterState
        self.clear_menu()
        self.game.change_state(PrizeCounterState(self.game, self, background=self.bg))

    def check_stairs(self):
        self.clear_menu()
        self.phase = "STAIRS_PROMPT"
        self.dialogue_box.reset(["There are stairs leading down behind a poster...", "Investigate?"])
        self.btn_yes.callback = self.start_rocket_gauntlet
        self.btn_no.callback = self.show_main_menu
        self.btn_yes.set_visibility(True)
        self.btn_no.set_visibility(True)

    def start_rocket_gauntlet(self):
        """Down the stairs: the Rocket Hideout, B1F to B4F (Jordan, 11-05: an area of its own, walked on a
        map in dungeon mode). Grunts beaten in the old gauntlet stay beaten."""
        from src.states.overworld.area_transition import AreaTransitionState
        self.btn_yes.set_visibility(False)
        self.btn_no.set_visibility(False)
        story = self.game.story_manager
        for i in range(min(4, int(self.rocket_progress or 0))):
            story.mark_trainer_defeated("ROCKET_HIDEOUT", i)
        if self.rocket_progress >= 5:
            story.story_flags["hideout_giovanni_defeated"] = True
        self.game.change_state(AreaTransitionState(self.game, "ROCKET_HIDEOUT"))

    # The Rocket Hideout's boss on B4F (FireRed/LeafGreen): Giovanni, who drops the Silph Scope.
    HIDEOUT_GIOVANNI = ([95, 111, 115], [25, 24, 29])

    def next_rocket_battle(self):
        if self.rocket_progress >= 5:
            self.give_porygon()
            return
        if self.rocket_progress == 4:
            self.giovanni_battle()
            return

        rocket_pool = self.game.loader.area_data.get("TEAM_ROCKET_POOL", [19, 23, 52])
        team_ids = [random.choice(rocket_pool) for _ in range(2 + (self.rocket_progress // 2))]
        opponent_team = [Pokemon(self.game.loader.fetch_specific(pid), self.game.assets, size_mult=3.125) for pid in team_ids]
        # Same curve as other Celadon trainers, each grunt a little tougher than the last.
        from src.world import levels
        team_levels = levels.trainer_team_levels(self.game, "CELADON_CITY", len(opponent_team))
        levels.set_team(opponent_team, [lv + self.rocket_progress for lv in team_levels])

        sprite_name = "rocket_grunt_m.png" if random.random() < 0.5 else "rocket_grunt_f.png"
        trainer_sprite = self.game.assets.get_trainer_image(sprite_name)

        class RocketGauntletBattle(TrainerBattleState):
            def exit_battle(self):
                self.game.story_manager.story_flags["game_corner_rocket_progress"] = self.game.story_manager.story_flags.get("game_corner_rocket_progress", 0) + 1
                state = GameCornerState(self.game, self.game.states.get("city"))
                state.rocket_progress = self.game.story_manager.story_flags["game_corner_rocket_progress"]
                state.phase = "VICTORY_SEQ"
                self.game.change_state(state)

        self.game.change_state(TrainerIntroState(self.game, trainer_sprite, "You shouldn't be here!",
                                                 RocketGauntletBattle(self.game, opponent_team, trainer_sprite=trainer_sprite, trainer_class="ROCKET", trainer_name="GRUNT", battle_type="indoor", area_name="CELADON_CITY")))

    def giovanni_battle(self):
        from src.world import levels
        team_ids, team_levels = self.HIDEOUT_GIOVANNI
        team = [Pokemon(self.game.loader.fetch_specific(pid), self.game.assets, size_mult=3.125) for pid in team_ids]
        levels.set_team(team, levels.follow_team(self.game, team_levels), exact=True)
        sprite = self.game.assets.get_trainer_image("leader_giovanni.png")
        intro = ["B4F: Giovanni: So, you've made it all the way down here.",
                 "I am Giovanni, the leader of Team Rocket. You'll regret getting in my way!"]

        class GiovanniBattle(TrainerBattleState):
            def exit_battle(self):
                story = self.game.story_manager
                if self.player_won:
                    story.story_flags["game_corner_rocket_progress"] = 5
                state = GameCornerState(self.game, self.game.states.get("city"))
                state.rocket_progress = story.story_flags.get("game_corner_rocket_progress", 0)
                state.phase = "VICTORY_SEQ"
                self.game.change_state(state)

        battle = GiovanniBattle(
            self.game, team, trainer_sprite=sprite, trainer_class="ROCKET_LEADER", trainer_name="GIOVANNI",
            battle_type="indoor", area_name="CELADON_CITY", is_boss_battle=True, rewards={"balls": 10},
            custom_dialogue={"player_won": ["Giovanni: ...What! This can't be!",
                                            "I'll leave the hideout. But Team Rocket isn't finished."],
                             "player_lost": ["Giovanni: Leave Team Rocket's business to the adults."]})
        self.game.change_state(TrainerIntroState(self.game, sprite, intro, battle))

    def give_porygon(self):
        story = self.game.story_manager
        story.story_flags["game_corner_cleared"] = True
        self.cleared = True
        porygon = Pokemon(self.game.loader.fetch_specific(137), self.game.assets, size_mult=2.5).max_ivs()  # a gift
        msg = ["You drove Team Rocket out of their hideout!"]
        if story.inventory.get("SILPH_SCOPE", 0) <= 0:
            story.inventory["SILPH_SCOPE"] = 1
            msg.append("Giovanni dropped the SILPH SCOPE! Now you can see ghosts for what they are.")
        msg += ["In the chaos, you found a PORYGON!", "You rescued PORYGON!"]
        if len(self.game.story_manager.player_team) < 6:
            self.game.story_manager.player_team.append(porygon)
        else:
            self.game.story_manager.deposit_to_pc(porygon)
            msg.append("PORYGON was sent to BILL'S PC.")
        self.game.data.add_pokemon(porygon)
        self.game.data.save()
        self.dialogue_box.reset(msg)
        self.dialogue_box.callback = self.show_main_menu

    def handle_infinite_result(self, score):
        reward = score * 50
        self.game.story_manager.money += reward
        self.phase = "REWARD"
        self.dialogue_box.reset([f"Game Over! Your score: {score}", f"You received a reward of ${reward}!"])
        self.dialogue_box.callback = self.show_main_menu

    def clear_menu(self):
        for btn in self.menu_buttons:
            if btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)
        self.menu_buttons = []

    def go_back(self):
        self.clear_menu()
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.add_element(self.dialogue_box)
        self.game.ui_manager.add_element(self.btn_yes)
        self.game.ui_manager.add_element(self.btn_no)
        if self.phase == "VICTORY_SEQ":
            self.on_rocket_victory()
        elif self.phase == "MAIN_MENU":
            self.show_main_menu()  # back from Cash In / Slots: the menu buttons come back too

    def on_rocket_victory(self):
        if self.rocket_progress >= 5:
            self.give_porygon()
        elif self.rocket_progress == 4:  # the last grunt down: B4F and the boss
            self.dialogue_box.reset(["Defeated Rocket Grunt 4!", "A man in a dark suit is waiting at the bottom of the stairs..."])
            self.dialogue_box.callback = self.next_rocket_battle
        else:
            self.dialogue_box.reset([f"Defeated Rocket Grunt {self.rocket_progress}!", "Another one is approaching!"])
            self.dialogue_box.callback = self.next_rocket_battle

    def handle_events(self, events):
        for event in events:
            self.dialogue_box.handle_event(event)

    def update(self):
        self.dialogue_box.update()

        # ARCHITECT: Only show Yes/No buttons when the question is actually reached in the dialogue
        if self.phase == "START":
            # Start dialogue has 3 lines; the question is the 3rd line (index 2)
            if self.dialogue_box.current_line == 2 and self.dialogue_box.is_waiting_for_click:
                self.btn_yes.set_visibility(True)
                self.btn_no.set_visibility(True)
        elif self.phase == "STAIRS_PROMPT":
            # Stairs prompt has 2 lines; the question is the 2nd line (index 1)
            if self.dialogue_box.current_line == 1 and self.dialogue_box.is_waiting_for_click:
                self.btn_yes.set_visibility(True)
                self.btn_no.set_visibility(True)

        if self.phase == "START" or self.phase == "STAIRS_PROMPT":
            box = self.dialogue_box.rect
            self.btn_yes.rect = pygame.Rect(box.right - 280, box.bottom - 80, 120, 60)
            self.btn_no.rect = pygame.Rect(box.right - 140, box.bottom - 80, 120, 60)

    def draw(self):
        self.game.screen.fill(BLACK)
        self.game.screen.blit(self.bg, (0, 0))
        if self.phase == "MAIN_MENU" and self.menu_buttons:
            self._draw_main_menu(self.game.screen)
        elif self.npc_sprite:
            self.game.screen.blit(self.npc_sprite, self.npc_sprite.get_rect(center=(self.game.width//2, self.game.height*0.45)))
        self.dialogue_box.draw(self.game.screen)
        self.game.ui_manager.draw(self.game.screen)


class FossilRevivalState(GameState):
    def __init__(self, game, fossil_name, pokemon_id, previous_state, consume=None):
        super().__init__(game)
        self.fossil_name = fossil_name
        self.consume = consume or [fossil_name]
        self.pokemon_id = pokemon_id
        self.previous_state = previous_state
        self.phase = "START"
        self.timer = 60
        self.scale = 1.0
        self.alpha = 255

        self.fossil_img = game.assets.get_item_image(fossil_name)
        if self.fossil_img:
            self.fossil_img = pygame.transform.scale(self.fossil_img, (160, 160))

        raw = self.game.loader.fetch_specific(pokemon_id)
        self.evolved_pokemon_obj = Pokemon(raw, self.game.assets, size_mult=3.0).max_ivs()  # a revived fossil: a gift
        from src.ui.scene_backdrop import SceneBackdrop
        self.backdrop = SceneBackdrop((game.width, game.height))  # (one of a few, at random)

    def handle_events(self, events):
        pass

    def update(self):
        self.backdrop.update()
        self.timer -= 1
        if self.phase == "START" and self.timer <= 0:
            self.phase = "GROW"
            self.timer = 50
        elif self.phase == "GROW":
            self.scale += 0.06
            self.alpha = max(0, self.alpha - 12)
            if self.timer <= 0:
                self.phase = "FLASH"
                self.timer = 20
        elif self.phase == "FLASH":
            if self.timer <= 0:
                self.phase = "REVEAL"
                self.timer = 60
                if self.evolved_pokemon_obj.cry:
                    self.evolved_pokemon_obj.cry.play()
                self.scale = 4.0
                self.alpha = 0
        elif self.phase == "REVEAL":
            self.scale = max(1.0, self.scale - 0.15)
            self.alpha = min(255, self.alpha + 20)
            if self.timer <= 0:  # once, when the reveal ends (these ran every frame before)
                self.phase = "END"
                self.timer = 60
                self._finalize_revival()
        elif self.phase == "END" and self.timer <= 0:
            pygame.event.clear()
            self.game.change_state(self.previous_state)

    def _finalize_revival(self):
        story = self.game.story_manager
        for item in self.consume:
            story.inventory[item] = story.inventory.get(item, 0) - 1
            if story.inventory[item] <= 0:
                story.inventory.pop(item, None)

        revival_flag = f"revived_fossil_{story.current_area_key}"
        story.story_flags[revival_flag] = True

        msg = f"Success! The fossil was revived into {self.evolved_pokemon_obj.display_name}!"
        if len(story.player_team) < 6:
            story.player_team.append(self.evolved_pokemon_obj)
        else:
            pc = story.pc_pokemon
            slot = next((i for i, p in enumerate(pc) if p is None), None)
            if slot is None:
                pc.append(self.evolved_pokemon_obj)
            else:
                pc[slot] = self.evolved_pokemon_obj  # (append would land past the 300 saved slots)
            msg += " Sent to BILL'S PC."

        self.game.data.add_pokemon(self.evolved_pokemon_obj)
        self.game.data.save()

        if hasattr(self.previous_state, 'show_message'):
            self.previous_state.show_message(msg)

    def draw(self):
        screen = self.game.screen
        cx, cy = self.game.width // 2, self.game.height // 2
        from src.ui.scene_backdrop import text_band
        self.backdrop.draw(screen, (cx, cy))
        text_band(screen, self.game.height * 0.85, 90)

        if self.phase in ["START", "GROW"]:
            if self.fossil_img:
                img = pygame.transform.rotozoom(self.fossil_img, 0, self.scale)
                img.set_alpha(self.alpha)
                screen.blit(img, img.get_rect(center=(cx, cy)))
            Utils.draw_text_outline(screen, "REVIVING ANCIENT FOSSIL...", self.game.assets.fonts["med"], WHITE, cx, self.game.height * 0.85)

        elif self.phase == "FLASH":
            screen.fill(WHITE)

        elif self.phase in ["REVEAL", "END"]:
            if self.evolved_pokemon_obj.image:
                img = pygame.transform.rotozoom(self.evolved_pokemon_obj.image, 0, self.scale)
                img.set_alpha(self.alpha)
                screen.blit(img, img.get_rect(center=(cx, cy)))
                Utils.draw_text_outline(screen, f"REVIVED {self.evolved_pokemon_obj.display_name.upper()}!",
                                        self.game.assets.fonts["med"], GOLD, cx, self.game.height * 0.85)

        self.game.ui_manager.draw(screen)


class UnownReportState(GameState):
    """The Unown Report: the 28 forms with you (team and PC), and the reward for all of them
    (Jordan, 11-04): MERGE THE UNOWN turns one Unown of each form into one Nown."""

    FORMS = ["normal", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n",
             "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "exclamation", "question"]
    MERGE_GOLD = (214, 160, 40)

    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.forms = self.FORMS
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", game.assets.fonts["button"], self.go_back,
                                      bg_color=theme.BACK, autosize=False)
        w, h = game.width, game.height
        self.bar = pygame.Rect(24, h - 92, w - 48, 76)
        merge_rect = pygame.Rect(self.bar.right - 330, self.bar.y + 10, 314, 56)
        fonts = game.assets.fonts
        merge_font = next((fonts[k] for k in ("button", "label") if fonts[k].size("MERGE THE UNOWN")[0] <= 290),
                          fonts["caption"])
        self.btn_merge = CommandButton(merge_rect, "MERGE THE UNOWN", merge_font, None, bg_color=self.MERGE_GOLD,
                                       autosize=False)
        self.confirm_rect = pygame.Rect(w // 2 - 330, h // 2 - 130, 660, 260)
        self.btn_yes = CommandButton((self.confirm_rect.centerx - 230, self.confirm_rect.bottom - 82, 210, 60),
                                     "MERGE", game.assets.fonts["button"], self.merge, bg_color=self.MERGE_GOLD,
                                     autosize=False, visible=False)
        self.btn_no = CommandButton((self.confirm_rect.centerx + 20, self.confirm_rect.bottom - 82, 210, 60),
                                    "NOT YET", game.assets.fonts["button"], self.close_confirm, bg_color=theme.BACK,
                                    autosize=False, visible=False)
        self.confirming = False
        self.refresh()

    def refresh(self):
        """What's with you now: each form's count, and which have a shiny."""
        story = self.game.story_manager
        self.counts, self.shiny = {}, set()
        for p in story.player_team + story.pc_pokemon:
            if p and p.id == 201:
                form = "normal" if str(p.form).lower() in ("normal", "a") else str(p.form).lower()
                self.counts[form] = self.counts.get(form, 0) + 1
                if p.is_shiny:
                    self.shiny.add(form)
        self.caught_forms = set(self.counts)
        self.ready = len(self.caught_forms) >= len(self.forms)
        self.btn_merge.callback = self.ask_merge if self.ready else None
        self.btn_merge.text = "MERGE THE UNOWN" if self.ready else "MERGE (ALL 28)"

    def go_back(self):
        from src.states.overworld import PlayState
        if isinstance(self.previous_state, PlayState):
            self.previous_state.is_resuming = True
        self.game.change_state(self.previous_state)

    def start(self):
        self.game.ui_manager.elements.clear()
        for btn in (self.btn_back, self.btn_merge, self.btn_yes, self.btn_no):
            self.game.ui_manager.add_element(btn)

    def ask_merge(self):
        self.confirming = True
        for btn, on in ((self.btn_yes, True), (self.btn_no, True), (self.btn_merge, False), (self.btn_back, False)):
            btn.set_visibility(on)

    def close_confirm(self):
        self.confirming = False
        for btn, on in ((self.btn_yes, False), (self.btn_no, False), (self.btn_merge, True), (self.btn_back, True)):
            btn.set_visibility(on)

    def merge(self):
        """One of each form merges; the one left evolves into Nown on the evolution screen."""
        kept = self.game.story_manager.merge_unown()
        self.close_confirm()
        if not kept:
            self.refresh()
            return
        unown, idx, context = kept
        from src.states.systems.evolution_scene import EvolutionState
        evo = EvolutionState(self.game, unown, self.game.loader.get_special_id("NOWN", 3025), idx,
                             context=context, return_state=self.previous_state)
        evo.evolve_yes()  # (already asked here)
        self.game.change_state(evo)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                (self.close_confirm if self.confirming else self.go_back)()

    def update(self):
        pass

    @staticmethod
    def _label(form):
        return {"normal": "A", "question": "?", "exclamation": "!"}.get(form, form.upper())

    def draw(self):
        screen = self.game.screen
        f = self.game.assets.fonts
        accent = theme.ACCENT["tool"]
        theme.menu_background(screen, accent, "UNOWN REPORT", f["button"], title_x=176)
        found = len(self.caught_forms)

        # Progress in the header: a bar that fills as the forms come in (gold at all 28).
        bar = pygame.Rect(self.game.width - 404, theme.HEADER_H // 2 - 18, 380, 32)
        pygame.draw.rect(screen, theme.shade(accent, 0.45), bar, border_radius=16)
        if found:
            fill = bar.inflate(-6, -6)
            fill.w = max(fill.h, int(fill.w * found / len(self.forms)))
            pygame.draw.rect(screen, self.MERGE_GOLD if self.ready else (120, 196, 120), fill, border_radius=13)
        Utils.draw_text_outline(screen, f"{found} / {len(self.forms)} forms", f["label"], WHITE, bar.centerx,
                                bar.centery, outline_color=theme.shade(accent, 0.35), thickness=2)

        cols, gap = 7, 10
        top = theme.HEADER_H + 12
        cw = (self.game.width - 48 - gap * (cols - 1)) // cols
        ch = (self.bar.y - 10 - top - gap * 3) // 4
        for i, form in enumerate(self.forms):
            col, row = i % cols, i // cols
            rect = pygame.Rect(24 + col * (cw + gap), top + row * (ch + gap), cw, ch)
            caught = form in self.caught_forms
            theme.card(screen, rect, fill=theme.TEXTBOX if caught else (206, 210, 222))
            img = self.game.assets.get_pokemon_image(201, form, form in self.shiny)
            if img:
                spr = fit_sprite(img, cw - 40, ch - 52).copy()
                if not caught:  # its shape, so you know what to look for
                    spr.fill((70, 74, 92), special_flags=pygame.BLEND_RGB_MULT)
                    spr.set_alpha(140)
                screen.blit(spr, spr.get_rect(center=(rect.centerx, rect.y + (ch - 30) // 2 + 4)))
            theme.shadow_text(screen, self._label(form), f["label"], rect.centerx, rect.bottom - 26,
                              color=theme.TEXT if caught else (120, 126, 146), align="center")
            if form in self.shiny:
                draw_shiny_star(screen, rect.right - 16, rect.y + 16, 9)
            if self.counts.get(form, 0) > 1:
                theme.shadow_text(screen, f"x{self.counts[form]}", f["caption"], rect.x + 10, rect.y + 6)

        # The bottom bar: how many to go and where they live, or the reward.
        theme.draw_textbox(screen, self.bar)
        if self.ready:
            tip = "All 28 forms! Merge your Unown to see what they become."
        elif self.game.story_manager.story_flags.get("unown_merged") and not found:
            tip = "Your Unown became NOWN! The ruins still hold more Unown."
        else:
            tip = f"{len(self.forms) - found} to go! Unown live in the Ruins of Alph and Tanoby Ruins."
        room = self.bar.w - 380
        font = next((f[k] for k in ("button", "label") if f[k].size(tip)[0] <= room), f["caption"])
        theme.shadow_text(screen, tip, font, self.bar.x + 20, self.bar.centery - font.get_height() // 2)

        if self.confirming:
            veil = pygame.Surface((self.game.width, self.game.height), pygame.SRCALPHA)
            veil.fill((10, 12, 24, 160))
            screen.blit(veil, (0, 0))
            theme.popup_panel(screen, self.confirm_rect, "MERGE THE UNOWN?", f["button"])
            room = self.confirm_rect.w - 60
            lines = ("One of each Unown form will join", "together as one new Pokemon.",
                     "They won't come back. Ready?")
            font = next((f[key] for key in ("label", "caption")  # one size, the largest that fits every line
                         if all(f[key].size(line)[0] <= room for line in lines)), f["caption"])
            for k, line in enumerate(lines):
                Utils.draw_text_outline(screen, line, font, WHITE, self.confirm_rect.centerx,
                                        self.confirm_rect.y + 72 + k * 30, outline_color=theme.MENU_BG, thickness=2)
        self.game.ui_manager.draw(screen)
