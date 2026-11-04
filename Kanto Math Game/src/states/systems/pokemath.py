"""Poke-Math Infinite: the endless math mode."""

import pygame
from src.states.base import GameState
from src.ui import theme
from src.utils import Utils
from src.config import WHITE, BLACK
from src.pokemon.data import Pokemon
import random


class PokeMathInfiniteState(GameState):
    def __init__(self, game, previous_state):
        super().__init__(game)
        self.previous_state = previous_state
        self.score, self.balls = 0, 5
        self.pool = [i for i in range(1, 151)]
        self.p_data = [None] * 3
        self.problem_str, self.correct_ans, self.options = "", "", []
        self.answer_btn_rects = [pygame.Rect(0, 0, 0, 0) for _ in range(3)]
        self.ball_active = False
        self.ball_pos, self.ball_target = [0, 0], [0, 0]
        self.pause_timer, self.caught_idx = 0, -1
        self.ball_img = game.assets.ball_imgs[0]
        self.stars = [[random.randint(0, game.width), random.randint(0, game.height), random.randint(2, 4)] for _ in range(40)]
        self.sprite_y = game.height * 0.4
        self.base_level = game.story_manager.get_math_level()
        self.generate_round()

    def generate_round(self):
        self.p_data = [Pokemon(self.game.loader.fetch_specific(random.choice(self.pool)), self.game.assets, size_mult=3.125) for _ in range(3)]
        # Starts at the player's level and climbs one level every 10 points
        engine = self.game.math
        level = engine.clamp_level(min(engine.max_level, self.base_level + self.score // 10))
        self.problem_str, self.correct_ans, self.options = engine.generate(level, num_options=3)

    def get_cx(self, i): return (i * self.game.width // 3) + (self.game.width // 6)

    def get_btn_rect(self, i):
        return pygame.Rect(self.get_cx(i) - 90, self.game.height * 0.65, 180, 90)

    def start(self):
        self.game.ui_manager.elements.clear()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and not self.ball_active and self.pause_timer == 0:
                for i in range(3):
                    if self.get_btn_rect(i).collidepoint(event.pos):
                        self.process_answer(i)
                        return

    def process_answer(self, idx):
        self.balls -= 1
        is_correct = self.options[idx] == self.correct_ans
        self.ball_active = True
        self.ball_pos, self.ball_target = [self.game.width // 2, self.game.height], [self.get_cx(idx), self.sprite_y]
        self.caught_idx = idx
        if is_correct:
            self.score += 1
            if self.score % 10 == 0:
                self.balls += 1

    def update(self):
        if self.ball_active:
            self.ball_pos[0] += (self.ball_target[0] - self.ball_pos[0]) * 0.25
            self.ball_pos[1] += (self.ball_target[1] - self.ball_pos[1]) * 0.25
            if abs(self.ball_pos[1] - self.ball_target[1]) < 10:
                self.ball_active = False
                self.pause_timer = 30
        if self.pause_timer > 0:
            self.pause_timer -= 1
            if self.pause_timer == 0:
                if self.balls <= 0:
                    self.previous_state.handle_infinite_result(self.score)
                    self.game.change_state(self.previous_state)
                else:
                    self.generate_round()

    def draw(self):
        screen = self.game.screen
        screen.fill(BLACK)
        for s in self.stars:
            s[1] += s[2]
            if s[1] > self.game.height:
                s[1], s[0] = 0, random.randint(0, self.game.width)
            pygame.draw.circle(screen, (150, 150, 150), (s[0], s[1]), 1)
        f = self.game.assets.fonts
        Utils.draw_text_outline(screen, f"SCORE: {self.score}", f["button"], theme.BAG, 24, 30, align="left",
                                outline_color=(20, 20, 30), thickness=3)
        Utils.draw_text_outline(screen, f"BALLS: {self.balls}", f["label"], WHITE, 24, 66, align="left",
                                outline_color=(20, 20, 30), thickness=2)
        for i, p in enumerate(self.p_data):
            if p and p.image:
                if not (self.pause_timer > 0 and i == self.caught_idx):
                    screen.blit(p.image, p.image.get_rect(center=(self.get_cx(i), self.sprite_y)))
        if not self.ball_active and self.pause_timer == 0:
            qf = f["big"]
            card = pygame.Rect(0, 0, max(360, qf.size(self.problem_str)[0] + 120), 100)
            card.center = (self.game.width // 2, 100)
            theme.draw_textbox(screen, card)
            theme.shadow_text(screen, self.problem_str, qf, card.centerx, card.centery, align="center")
            mouse = pygame.mouse.get_pos()
            for i in range(3):
                txt = str(self.options[i])
                rect = self.get_btn_rect(i)
                theme.card(screen, rect, hover=rect.collidepoint(mouse), accent=theme.RUN)
                theme.shadow_text(screen, txt, f["num"], rect.centerx, rect.centery, align="center")
        if self.ball_active:
            screen.blit(self.ball_img, (self.ball_pos[0]-42, self.ball_pos[1]-42))
