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


# Where each side's Pokemon stands (the battle renderer's spots), as shares of the screen.
SPOTS = {"player": (0.27, 0.69), "opponent": (0.73, 0.39)}

# Battle sprites (Jordan, 10-30, from a fan game's battle): bigger, standing on their spots. The foe's
# feet are on its platform; your Pokemon's back stands on the text box's top edge (cut a little by it,
# like the games), instead of sinking half behind it.
BATTLE_SCALE = 1.6
FOE_FEET = (0.73, 0.46)
PLAYER_FEET_X = 0.27
PLAYER_FEET_UNDER_BOX = 10  # px of your Pokemon hidden behind the text box
# Big Pokemon (Snorlax, Gyarados) stop growing at these shares of the screen's height (the visible
# part), so they stay on screen and off the foe's box.
MAX_HEIGHT = {"opponent": 0.40, "player": 0.50}


def battle_sprite(pokemon, side):
    """The Pokemon's battle sprite for a side (your side: its back), BATTLE_SCALE bigger; cached."""
    if pokemon is None:
        return None
    if side == "player":
        base = getattr(pokemon, "back_image", None)
        if base is None and getattr(pokemon, "image", None) is not None:
            base = pygame.transform.flip(pokemon.image, True, False)  # no back sprite: its front, turned
    else:
        base = getattr(pokemon, "image", None)
    if base is None:
        return None
    key = (id(base), side)
    cache = getattr(pokemon, "_battle_sprite_cache", None)
    if cache and cache[0] == key:
        return cache[1]
    w, h = base.get_size()
    screen = pygame.display.get_surface()
    room = (screen.get_height() if screen else 720) * MAX_HEIGHT[side]
    k = min(BATTLE_SCALE, room / max(1, base.get_bounding_rect().height))
    img = pygame.transform.scale(base, (max(1, int(w * k)), max(1, int(h * k))))
    try:
        pokemon._battle_sprite_cache = (key, img)
    except AttributeError:
        pass
    return img


def feet_spot(game, side):
    """Where a side's Pokemon's feet are, in pixels."""
    if side == "player":
        from src.utils import Utils
        return game.width * PLAYER_FEET_X, Utils.get_full_dialogue_rect(game).top + PLAYER_FEET_UNDER_BOX
    return game.width * FOE_FEET[0], game.height * FOE_FEET[1]


def sprite_rect(game, img, side):
    """The rect a battle sprite is drawn in: its visible feet (not the image's empty bottom rows)
    on the side's spot."""
    fx, fy = feet_spot(game, side)
    pad = img.get_height() - img.get_bounding_rect().bottom
    return img.get_rect(midbottom=(int(fx), int(fy + pad)))


def battle_spot(game, pokemon, side):
    """Centre of a side's Pokemon as the battle draws it (for balls, flashes and effects)."""
    img = battle_sprite(pokemon, side)
    if img is None:
        x, y = SPOTS[side]
        return game.width * x, game.height * y
    return sprite_rect(game, img, side).center


def white_silhouette(sprite, amount):
    """The sprite washed toward white (amount 0..1), for a ball's flash."""
    img = sprite.copy()
    if amount > 0:
        v = int(255 * amount)
        img.fill((v, v, v, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return img


def ball_arc(start, end, t, height):
    """A thrown ball's point at t (0..1) on an arc `height` px above the straight line."""
    x = start[0] + (end[0] - start[0]) * t
    y = start[1] + (end[1] - start[1]) * t - height * 4 * t * (1 - t)
    return x, y


# [REF-0054: Fainting Animation]
class FaintAnimation:
    """A fainted Pokemon sinks out of sight into the ground (clipped at its feet, as in the
    games), fading at the end. Also used when a Pokemon is called back for a switch."""

    FRAMES = 22

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
        k = min(1.0, self.timer / self.FRAMES)
        h = self.sprite.get_height() if self.sprite else 100
        self.y_offset = int(h * k * k)                 # slow, then faster, like a slump
        self.alpha = 255 if k < 0.6 else int(255 * (1 - (k - 0.6) / 0.4))
        if self.timer >= self.FRAMES:
            self.active = False
            return True
        return False

    def draw(self, surface):
        if not self.active or not self.sprite:
            return
        w, h = self.sprite.get_size()
        visible = h - self.y_offset
        if visible <= 0:
            return
        part = self.sprite.subsurface((0, 0, w, visible)).copy()
        part.set_alpha(self.alpha)
        surface.blit(part, (self.pos[0], self.pos[1] + self.y_offset))


# [REF-0055: Pokémon Summoning Animation]
class PokemonSummonAnimation:
    """Sending a Pokemon out, as in the games: the ball arcs in from the trainer's side to the
    Pokemon's battle spot, bursts open in a white flash, and the Pokemon grows out of it (white,
    then its colours), with its cry. It appears exactly where the battle draws it afterwards."""

    THROW = 18
    OPEN = 14

    def __init__(self, game, pokemon, side="player", use_back_sprite=False):
        self.game = game
        self.pokemon = pokemon
        self.side = side
        self.use_back_sprite = use_back_sprite
        self.side_key = "player" if side == "player" else "opponent"
        self.spot = battle_spot(game, pokemon, self.side_key)
        self.start = ((game.width * 0.06, game.height * 0.95) if side == "player"
                      else (game.width * 0.95, game.height * 0.12))
        self.phase = 0
        self.timer = 0
        self.finished = False
        ball = game.assets.ball_imgs[0]
        self.ball = pygame.transform.smoothscale(ball, (44, 44))
        # (older code reads these)
        self.ball_x, self.ball_y = self.start
        self.target_x = self.spot[0]
        self.angle = 0
        self.alpha = 255

    def _sprite(self):
        return battle_sprite(self.pokemon, self.side_key)

    def update(self):
        self.timer += 1
        if self.phase == 0:
            t = min(1.0, self.timer / self.THROW)
            self.ball_x, self.ball_y = ball_arc(self.start, self.spot, t, 140)
            self.angle = (self.angle + 30) % 360
            if t >= 1.0:
                self.phase, self.timer = 1, 0
                if self.pokemon and getattr(self.pokemon, "cry", None):
                    self.pokemon.cry.play()
        elif self.phase == 1 and self.timer >= self.OPEN:
            self.phase = 2
            self.finished = True

    def draw(self, surface):
        if self.phase == 0:
            ball = pygame.transform.rotate(self.ball, self.angle)
            surface.blit(ball, ball.get_rect(center=(int(self.ball_x), int(self.ball_y))))
            return
        sprite = self._sprite()
        if sprite is None:
            return
        k = min(1.0, self.timer / self.OPEN) if self.phase == 1 else 1.0
        if self.phase == 1:
            # the burst: a white ring, the Pokemon growing out of it
            ring = pygame.Surface((240, 240), pygame.SRCALPHA)
            pygame.draw.circle(ring, (255, 255, 255, int(200 * (1 - k))), (120, 120), int(30 + 90 * k), 6)
            surface.blit(ring, ring.get_rect(center=(int(self.spot[0]), int(self.spot[1]))))
            scale = 0.2 + 0.8 * (1 - (1 - k) ** 2)
            w, h = sprite.get_size()
            img = pygame.transform.smoothscale(white_silhouette(sprite, 1 - k), (max(1, int(w * scale)), max(1, int(h * scale))))
            # grow from the feet, so it stands where the battle draws it
            surface.blit(img, img.get_rect(midbottom=sprite_rect(self.game, sprite, self.side_key).midbottom))
        else:
            surface.blit(sprite, sprite_rect(self.game, sprite, self.side_key))
