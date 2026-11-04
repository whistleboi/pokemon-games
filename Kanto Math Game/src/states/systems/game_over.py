"""The Game Over screen."""

import pygame
import sys
from src.states.base import GameState
from src.ui.widgets import Button
from src.utils import Utils
from src.config import BLACK, GREEN, RED, DARK_RED


# [REF-0039: Game Over State]
class GameOverState(GameState):
    def __init__(self, game):
        super().__init__(game)
        mid_x = game.width // 2
        self.btn_retry = Button(
            rect=(mid_x - 200, game.height * 0.60, 400, 80),
            text="RETRY",
            font=game.assets.fonts["s_med"],
            callback=self.retry_game,
            bg_color=GREEN,
        )
        mid_x = game.width // 2
        self.btn_reset = Button(
            rect=(mid_x - 200, game.height * 0.72, 400, 80),
            text="RESET STREAK",
            font=game.assets.fonts["s_med"],
            callback=self.reset_streak,
            bg_color=DARK_RED,
        )
        mid_x = game.width // 2
        self.btn_exit = Button(
            rect=(mid_x - 200, game.height * 0.84, 400, 80),
            text="EXIT GAME",
            font=game.assets.fonts["s_med"],
            callback=self.exit_game,
            bg_color=RED,
        )

    def start(self):
        self.game.ui_manager.add_element(self.btn_retry)
        self.game.ui_manager.add_element(self.btn_reset)
        self.game.ui_manager.add_element(self.btn_exit)

    def handle_events(self, events):
        pass

    def retry_game(self):
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.play()
        self.game.story_manager.load_last_checkpoint(self.game)

    def reset_streak(self):
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.play()
        self.game.data.set_high_score(0)
        self.game.data.save()
        from src.states.overworld import PlayState
        self.game.change_state(PlayState(self.game))

    def exit_game(self):
        pygame.quit()
        sys.exit()

    def update(self):
        pass

    def draw(self):
        screen = self.game.screen
        screen.fill(BLACK)
        if self.game.assets.go_img:
            screen.blit(
                self.game.assets.go_img,
                self.game.assets.go_img.get_rect(
                    center=(self.game.width // 2, self.game.height * 0.35)
                ),
            )
        Utils.draw_text_outline(
            screen,
            "GAME OVER",
            self.game.assets.fonts["big"],
            RED,
            self.game.width // 2,
            self.game.height * 0.1,
        )
        self.game.ui_manager.draw(screen)
