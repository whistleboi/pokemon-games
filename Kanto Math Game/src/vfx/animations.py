# [REF-0001: System Imports]
import pygame


# [REF-0016: Battle Animations]
class AnimationController:
    """Attack animations, like the games: the attacker lunges toward the foe (eased, out and back),
    and at the peak the foe is hit: it blinks and is knocked back a little. (The old version shook
    the whole screen 15 px on every attack.)"""

    LUNGE_FRAMES = 16
    HIT_AT = 6          # the lunge frame where the blow lands
    HIT_FRAMES = 18     # how long the foe blinks

    def __init__(self):
        self.lunge_timer = 0
        self.is_lunging = False
        self.lunge_side = None
        self.impact_flash = 0
        self.impact_shake = 0   # (kept for older code; the screen no longer shakes)
        self.hit_side = None
        self.hit_timer = 0

    def start_lunge(self, side):
        self.is_lunging = True
        self.lunge_side = side
        self.lunge_timer = 0

    def lunge_amount(self):
        """0..1: how far forward the attacker is (fast out, eased back)."""
        if not self.is_lunging:
            return 0.0
        t = self.lunge_timer
        if t <= self.HIT_AT:
            k = t / self.HIT_AT
            return 1 - (1 - k) ** 2
        k = (t - self.HIT_AT) / (self.LUNGE_FRAMES - self.HIT_AT)
        return max(0.0, 1 - k * k)

    def hit_visible(self, side):
        """False on the blink frames of the Pokemon that was just hit."""
        return not (self.hit_timer > 0 and self.hit_side == side and (self.hit_timer // 3) % 2 == 0)

    def knockback(self, side):
        """A small push away from the attacker while it's hit."""
        if self.hit_timer <= 0 or self.hit_side != side:
            return 0
        return int(10 * self.hit_timer / self.HIT_FRAMES)

    def update(self):
        if self.is_lunging:
            self.lunge_timer += 1
            if self.lunge_timer == self.HIT_AT:
                self.hit_side = "opponent" if self.lunge_side == "player" else "player"
                self.hit_timer = self.HIT_FRAMES
            if self.lunge_timer >= self.LUNGE_FRAMES:
                self.is_lunging = False
                self.lunge_timer = 0
        if self.hit_timer > 0:
            self.hit_timer -= 1
        if self.impact_flash > 0:
            self.impact_flash -= 1
        if self.impact_shake > 0:
            self.impact_shake -= 1


# [REF-0054: Fainting Animation]
class FaintAnimation:
    """Handles Pokémon fainting animation."""

    def __init__(self):
        self.active = False
        self.timer = 0
        self.alpha = 255
        self.y_offset = 0
        self.sprite = None
        self.pos = (0, 0)

    def start(self, sprite, pos):
        self.active = True
        self.sprite = sprite
        self.pos = pos
        self.timer = 0
        self.alpha = 255
        self.y_offset = 0

    def update(self):
        if not self.active:
            return False
        self.timer += 1
        if self.timer > 10:
            self.y_offset += 10
            self.alpha = max(0, self.alpha - 20)
        if self.alpha <= 0:
            self.active = False
            return True
        return False

    def draw(self, surface):
        if not self.active or not self.sprite:
            return
        temp_sprite = self.sprite.copy()
        temp_sprite.set_alpha(self.alpha)
        surface.blit(temp_sprite, (self.pos[0], self.pos[1] + self.y_offset))


# [REF-0055: Pokémon Summoning Animation]
class PokemonSummonAnimation:
    """Classic Gen 1/2 Poké Ball toss + pop-out + cry"""
    def __init__(self, game, pokemon, side="player", use_back_sprite=False):
        self.game = game
        self.pokemon = pokemon
        self.side = side
        self.use_back_sprite = use_back_sprite
        self.phase = 0
        self.ball_x = game.width * (0.25 if side == "player" else 0.75)
        self.ball_y = game.height * 0.55
        self.target_x = game.width * (0.35 if side == "player" else 0.65)
        self.angle = 0
        self.alpha = 255
        self.finished = False

    def update(self):
        if self.phase == 0:
            self.ball_x += (self.target_x - self.ball_x) * 0.18
            self.angle += 25
            if abs(self.ball_x - self.target_x) < 15:
                self.phase = 1
                if self.pokemon and self.pokemon.cry:
                    self.pokemon.cry.play()
        elif self.phase == 1:
            self.alpha = max(0, self.alpha - 15)
            if self.alpha <= 30:
                self.phase = 2
                self.finished = True

    def draw(self, surface):
        if self.phase == 1 or self.phase == 2:
            if self.pokemon:
                sprite = self.pokemon.image
                if self.side == "player" and self.use_back_sprite and self.pokemon.back_image:
                    sprite = self.pokemon.back_image

                p = sprite.copy()
                alpha = 255 - self.alpha if self.phase == 1 else 255
                p.set_alpha(alpha)
                surface.blit(p, p.get_rect(center=(self.target_x, self.ball_y - 20)))

        if self.phase == 0 or self.phase == 1:
            ball = pygame.transform.rotate(self.game.assets.ball_imgs[0], self.angle)
            ball.set_alpha(self.alpha)
            surface.blit(ball, ball.get_rect(center=(self.ball_x, self.ball_y)))
