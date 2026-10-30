# [REF-0001: System Imports]
import pygame
import random
import io
import math
from dataclasses import dataclass
from src.config import DEFAULT_BASE_STATS, VOLUME
from src.utils import DummySound
from src.pokemon.contest import new_condition


# [REF-0005: Pokemon Core Class]
def _fit_square(img, size):
    """A sprite in a size x size square: square sprites as before; others (fan-made art like
    Jordan's Shadow Charizard back) keep their proportions, centred, feet on the bottom edge."""
    w, h = img.get_size()
    if w == h:
        return pygame.transform.scale(img, (size, size))
    k = size / max(w, h)
    scaled = pygame.transform.scale(img, (max(1, int(w * k)), max(1, int(h * k))))
    out = pygame.Surface((size, size), pygame.SRCALPHA)
    out.blit(scaled, scaled.get_rect(midbottom=(size // 2, size)))
    return out


class Pokemon:
    def __init__(self, raw_data, assets, size_mult=3.5):
        self.id = raw_data["id"]
        self.meta_id = raw_data.get("meta_id", self.id)
        self.name = raw_data["name"]
        self.display_name = raw_data.get("display_name", self.name)
        self.form = raw_data.get("form", "normal")
        self.stage = raw_data.get("stage", 1)
        self.is_shiny = raw_data["is_shiny"]
        self.raw_cry_bytes = raw_data["cry"]
        self.types = raw_data.get("types", [])
        self.back_image = None
        self.base_stats = raw_data.get(
            "stats",
            {
                "HP": 50,
                "ATTACK": 50,
                "DEFENSE": 50,
                "SPATK": 50,
                "SPDEF": 50,
                "SPEED": 50,
            },
        )
        self.level = int(raw_data.get("level") or 5)
        self.xp = 0  # XP into the current level
        # Friendship grows with catches made while it's in the party (friendship evolutions),
        # and counters track special evolution conditions (wins, attacks, crits, KOs...).
        self.friendship = 0
        self.affection = 0  # Pokemon-Amie (0-255), see src/pokemon/affection.py
        self.counters = {}
        # Individual values (0-31) like the games; they make each Pokemon's stats a little different.
        self.ivs = {k: random.randint(0, 31) for k in self.IV_KEYS}
        self.status = None        # burn, paralysis, poison, sleep or freeze
        self.sleep_turns = 0
        self.moves = []           # up to four move names (filled from its learnset when needed)
        self.move_pool = []       # every move it has learned; the player picks four in the Summary
        self.caught_region = None
        # The level it was caught at: a level evolution waits until it has levelled up once
        # (Jordan), so a Charmander caught at Lv 20 doesn't turn into Charmeleon on the spot.
        self.caught_level = None
        # Caught as a Gigantamax raid boss: shown normally, but keeps the G-Max Factor.
        self.gmax_factor = False
        # Contest condition (raised by Pokéblocks), Sheen and ribbons won.
        self.condition = new_condition()
        self.sheen = 0
        self.ribbons = []

        self.current_hp = self.get_max_hp()
        self.max_hp = self.get_max_hp()

        if raw_data["img"]:
            img_surface = pygame.image.load(io.BytesIO(raw_data["img"])).convert_alpha()
        else:
            img_surface = pygame.Surface((100, 100), pygame.SRCALPHA)
            pygame.draw.circle(img_surface, (100, 100, 100), (50, 50), 40)

        if raw_data.get("back_img"):
            try:
                back_img_surface = pygame.image.load(
                    io.BytesIO(raw_data["back_img"])
                ).convert_alpha()
                mult_back = (size_mult * 2 if assets.is_pc else size_mult) * 0.8
                s_back = int(assets.width // mult_back)
                self.back_image = _fit_square(back_img_surface, s_back)
            except pygame.error:
                pass

        mult = size_mult * 2 if assets.is_pc else size_mult
        s = int(assets.width // mult)
        self.image = _fit_square(img_surface, s)

        sb_scale = 0.05 if assets.is_pc else 0.12
        sb_size = int(assets.width * sb_scale)
        self.sidebar_image = pygame.transform.scale(
            img_surface,
            (sb_size, sb_size)
        )
        try:
            self.cry = (
                pygame.mixer.Sound(io.BytesIO(self.raw_cry_bytes))
                if self.raw_cry_bytes
                else DummySound()
            )
            self.cry.set_volume(VOLUME)
        except pygame.error:
            self.cry = DummySound()

        self.bob_offset = random.uniform(0, 2 * math.pi)
        self.bob_speed = random.uniform(0.004, 0.006)
        self.bob_amount = random.uniform(8, 12)

    # ---- Levels (real 1-100, fast-paced) ----
    # A level costs 10 XP below Lv 20, then 15, 20, 30 and 40 per level in each band of 20.
    # An even-strength wild win is worth 10 XP, so early on that's about a level per win.
    MAX_LEVEL = 100
    XP_PER_WIN = 10
    LEVEL_COSTS = ((20, 10), (40, 15), (60, 20), (80, 30), (100, 40))  # (below level, XP per level)
    # Legacy stage system, only for converting old saves.
    LEGACY_THRESHOLDS = (15, 30)
    LEGACY_BAND_START = {1: 5, 2: 20, 3: 40}

    @classmethod
    def xp_cost(cls, level):
        """XP needed to go from `level` to the next one (0 at Lv 100)."""
        if level >= cls.MAX_LEVEL:
            return 0
        return next(cost for below, cost in cls.LEVEL_COSTS if level < below)

    @property
    def xp_to_next(self):
        """XP to the next level on this species' real growth curve (see src/pokemon/growth.py)."""
        from src.pokemon import growth
        species = int(getattr(self, "meta_id", None) or self.id) if int(self.id) >= 2000 else int(self.id)
        return growth.level_cost(species, self.level) if self.level < self.MAX_LEVEL else 0

    @property
    def level_progress(self):
        """0..1 along the XP bar to the next level (1.0 at Lv 100)."""
        cost = self.xp_to_next
        return 1.0 if not cost else min(1.0, self.xp / cost)

    def gain_xp(self, amount, cap=None):
        """Add XP and level up (never past `cap`). Returns how many levels it gained."""
        cap = self.MAX_LEVEL if cap is None else min(self.MAX_LEVEL, cap)
        if self.level >= cap:
            self.xp = min(self.xp, max(0, self.xp_to_next - 1))
            return 0
        gained = 0
        old_max = self.get_max_hp()
        self.xp += max(0, int(amount))
        while self.level < cap and self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            gained += 1
        if gained and self.current_hp > 0:  # level-ups add the HP gained, like the games
            self.current_hp = min(self.get_max_hp(), self.current_hp + self.get_max_hp() - old_max)
        if self.level >= self.MAX_LEVEL:
            self.xp = 0
        elif self.level >= cap:
            self.xp = min(self.xp, max(0, self.xp_to_next - 1))
        return gained

    def level_up(self, levels=1):
        """Rare Candy style: straight to the next level(s), keeping HP's share."""
        share = self.current_hp / max(1, self.get_max_hp())
        for _ in range(levels):
            if self.level < self.MAX_LEVEL:
                self.level += 1
        self.xp = 0
        self.current_hp = max(1, round(share * self.get_max_hp())) if self.current_hp > 0 else 0

    @classmethod
    def battle_xp(cls, my_level, foe_level, trainer=False):
        """XP for a KO, scaled like the games (Gen 5+): an even match is worth one full level,
        and the reward grows quickly for beating stronger foes and shrinks for weaker ones:
            (foe / me) x ((2 x foe + 10) / (foe + me + 10)) ^ 2.5
        Trainers' Pokemon give 1.5x."""
        ratio = (foe_level / max(1, my_level)) * ((2 * foe_level + 10) / (foe_level + my_level + 10)) ** 2.5
        base = cls.xp_cost(my_level) or cls.XP_PER_WIN
        return max(1, int(base * ratio * (1.5 if trainer else 1.0) + 0.5))

    @property
    def wins(self):
        """Battles won (a stand-in for steps walked by some special evolutions)."""
        return self.counters.get("wins", 0)

    @wins.setter
    def wins(self, value):
        self.counters["wins"] = int(value)

    @property
    def effective_stage(self):
        """Evolution stage (1-3). Battles use levels now; this is only for display and contests."""
        return min(3, self.stage)

    @classmethod
    def legacy_level(cls, stage, xp):
        """Level for a Pokemon from an old save (stage + XP thresholds, 15 wins per stage)."""
        wins = xp // cls.XP_PER_WIN
        crossed = sum(1 for t in cls.LEGACY_THRESHOLDS if wins >= t)
        st = min(3, stage + crossed)
        used = min(crossed, 3 - stage) * 150 if stage < 3 else 0
        into = max(0, xp - used)
        if st < 3:
            return cls.LEGACY_BAND_START[st] + min(14 if st == 1 else 19, into // 10)
        return min(cls.MAX_LEVEL, 40 + into // 10)

    @staticmethod
    def legacy_hp_scale(stage):
        return (20, 20, 60, 90)[max(0, min(3, stage))]

    IV_KEYS = ("HP", "ATTACK", "DEFENSE", "SPATK", "SPDEF", "SPEED")
    IV_ALIASES = {"SPECIAL-ATTACK": "SPATK", "SPECIAL-DEFENSE": "SPDEF"}

    def iv(self, stat_name):
        key = self.IV_ALIASES.get(stat_name.upper(), stat_name.upper())
        return getattr(self, "ivs", {}).get(key, 15)

    def stat_value(self, stat_name, level=None):
        """The actual stat at a level, as in the games: floor((2 x Base + IV) x Lv / 100) + 5."""
        lv = self.level if level is None else level
        return int((2 * self.get_stat(stat_name) + self.iv(stat_name)) * lv / 100) + 5

    def cure_status(self):
        """Clear burn/paralysis/poison/sleep/freeze (Pokemon Center, whiteout, Full Heal)."""
        self.status = None
        self.sleep_turns = 0
        self.toxic_count = 0

    def heal_full(self):
        """Full HP and no status, like a Pokemon Center."""
        self.current_hp = self.get_max_hp()
        self.cure_status()

    def get_max_hp(self, level=None, **_legacy):
        """Real HP: floor((2 x Base + IV) x Lv / 100) + Lv + 10."""
        lv = self.level if level is None else level
        return int((2 * self.get_stat("HP") + self.iv("HP")) * lv / 100) + int(lv) + 10

    def get_stat(self, stat_name):
        """Gets a base stat value."""
        # Stat data uses "SPECIAL-ATTACK"/"SPECIAL-DEFENSE"; the defaults use "SPATK"/"SPDEF".
        aliases = {"SPATK": "SPECIAL-ATTACK", "SPDEF": "SPECIAL-DEFENSE",
                   "SPECIAL-ATTACK": "SPATK", "SPECIAL-DEFENSE": "SPDEF"}
        key = stat_name.upper()
        if key in self.base_stats:
            return self.base_stats[key]
        return self.base_stats.get(aliases.get(key, key), 50)

    def set_volume(self, volume):
        if self.cry:
            self.cry.set_volume(volume)

    def transform_into(self, target):
        """Transforms this Pokemon into the target (Ditto logic)."""
        if self.id != 132:
            return  # Only Ditto
        if hasattr(self, "transformed_state"):
            return  # Already transformed

        # Save state
        ditto_color_tint = (180, 150, 200)  # A tint color for multiplication

        self.transformed_state = {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "types": self.types,
            "base_stats": self.base_stats,
            "image": self.image,
            "back_image": self.back_image,
            "sidebar_image": self.sidebar_image,
            "cry": self.cry,
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "form": self.form,
            "moves": list(getattr(self, "moves", [])),
        }

        # Copy target (Takes HP, Stage, Typing, Appearance)
        self.id = target.id
        self.name = target.name
        self.display_name = target.display_name
        self.types = target.types
        self.base_stats = target.base_stats
        self.cry = target.cry
        self.form = target.form
        self.moves = list(getattr(target, "moves", []) or getattr(self, "moves", []))  # Transform copies moves

        self.max_hp = target.max_hp
        self.current_hp = target.current_hp
        self._stage_override = target.effective_stage

        if target.image:
            self.image = target.image.copy()
            self.image.fill(ditto_color_tint, special_flags=pygame.BLEND_RGB_MULT)
        else:
            self.image = None

        if target.back_image:
            self.back_image = target.back_image.copy()
            self.back_image.fill(ditto_color_tint, special_flags=pygame.BLEND_RGB_MULT)
        else:
            self.back_image = None

        if target.sidebar_image:
            self.sidebar_image = target.sidebar_image.copy()
            self.sidebar_image.fill(ditto_color_tint, special_flags=pygame.BLEND_RGB_MULT)
        else:
            self.sidebar_image = None

    def revert_transform(self):
        """Reverts a transformed Pokemon back to original state (and any Mega/Primal form)."""
        from src.pokemon.forms import revert_form
        revert_form(self)
        if not hasattr(self, "transformed_state"):
            return

        state = self.transformed_state
        for key, value in state.items():
            setattr(self, key, value)

        if hasattr(self, "_stage_override"):
            del self._stage_override

        del self.transformed_state


# [REF-0060: CaughtPokemon Dataclass for Simplified Storage]
@dataclass
class CaughtPokemon:
    id: int
    name: str
    form: str = "normal"
    is_shiny: bool = False
