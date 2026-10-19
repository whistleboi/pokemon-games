# [REF-0001: System Imports]
import pygame
import random
import io
import math
from dataclasses import dataclass
from src.config import DEFAULT_BASE_STATS, VOLUME
from src.utils import DummySound


# [REF-0005: Pokemon Core Class]
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
        self.xp = 0
        self.caught_region = None
        # Caught as a Gigantamax raid boss: shown normally, but keeps the G-Max Factor.
        self.gmax_factor = False

        self.level = 100
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
                self.back_image = pygame.transform.scale(
                    back_img_surface, (s_back, s_back)
                )
            except pygame.error:
                pass

        mult = size_mult * 2 if assets.is_pc else size_mult
        s = int(assets.width // mult)
        self.image = pygame.transform.scale(img_surface, (s, s))

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

    # Wins required to reach each higher stage (stage+1, stage+2).
    STAGE_THRESHOLDS = [15, 30]
    # Progress is tracked in XP; an even-strength win is worth XP_PER_WIN, so a
    # stage still takes 15 nominal wins. Relative-strength modifiers scale it.
    XP_PER_WIN = 10
    TIER_XP = STAGE_THRESHOLDS[0] * XP_PER_WIN
    # Sub-stages inside one tier. Later ones cost more, so the bar slows near evolution.
    SUB_STAGE_COSTS = (20, 30, 40, 60)
    # Share of the gap to the next stage's stats that sub-stages can close (keeps boosts slight).
    SUB_STAGE_GROWTH = 0.4
    HP_BY_STAGE = (20, 20, 60, 90)

    @property
    def wins(self):
        """Nominal wins, derived from XP (evolution checks and saves still use this)."""
        return self.xp // self.XP_PER_WIN

    @wins.setter
    def wins(self, value):
        self.xp = int(value) * self.XP_PER_WIN

    @property
    def effective_stage(self):
        """Stage from base stage + wins crossing each threshold in STAGE_THRESHOLDS."""
        if hasattr(self, "_stage_override"):
            return self._stage_override
        extra = sum(1 for t in self.STAGE_THRESHOLDS if self.wins >= t)
        return min(3, self.stage + extra)

    def _tier_xp(self):
        crossed = sum(1 for t in self.STAGE_THRESHOLDS if self.wins >= t)
        return max(0, min(self.TIER_XP, self.xp - crossed * self.TIER_XP))

    @property
    def sub_stage(self):
        """(completed, total, xp_into_current, current_cost), or None when fully grown."""
        if self.effective_stage >= 3:
            return None
        left = self._tier_xp()
        for i, cost in enumerate(self.SUB_STAGE_COSTS):
            if left < cost:
                return (i, len(self.SUB_STAGE_COSTS), left, cost)
            left -= cost
        n = len(self.SUB_STAGE_COSTS)
        return (n, n, 0, self.SUB_STAGE_COSTS[-1])

    @property
    def sub_stage_fraction(self):
        """How far stats have grown toward the next stage (0 .. <1)."""
        sub = self.sub_stage
        if not sub:
            return 0.0
        return self.SUB_STAGE_GROWTH * min(sub[0], sub[1] - 1) / (sub[1] - 1)

    @property
    def tier_progress(self):
        """0..1 position on the XP bar for the current tier (1.0 when fully grown)."""
        if self.effective_stage >= 3:
            return 1.0
        return self._tier_xp() / self.TIER_XP

    @property
    def evolution_progress(self):
        """(xp_in_current_tier, tier_xp) for a progress bar. None if fully evolved."""
        if self.effective_stage >= 3:
            return None
        return (self._tier_xp(), self.TIER_XP)

    def grows_toward_next_stage(self, stage):
        """Sub-stage boosts only apply when fighting at the Pokémon's true stage."""
        return stage == min(self.effective_stage, 3) and stage < 3

    def get_max_hp(self, stage_override=None):
        """HP per stage: 20 / 60 / 90, plus sub-stage growth toward the next stage."""
        st = min(stage_override if stage_override is not None else self.effective_stage, 3)
        hp = self.HP_BY_STAGE[st]
        if self.grows_toward_next_stage(st):
            hp += (self.HP_BY_STAGE[st + 1] - hp) * self.sub_stage_fraction
        return int(round(hp))

    def battle_xp(self, my_stage, foe_stage, foe_is_weak):
        """XP for beating a foe, in steps of 25%: +1 step per stage the foe is above you,
        -1 per stage below, and -1 if the foe is stat-weak (the side taking the -1 stat
        modifier). So a stage 1 beating a weak stage 2 (e.g. Metapod) nets 0 steps."""
        steps = (foe_stage - my_stage) - (1 if foe_is_weak else 0)
        mult = max(0.5, min(1.75, 1 + 0.25 * steps))
        return max(1, int(self.XP_PER_WIN * mult + 0.5))

    def gain_xp(self, amount):
        """Add XP. Returns how many sub-stages were completed by this gain."""
        stage_before, before = self.effective_stage, self.sub_stage
        self.xp += amount
        if not before:
            return 0
        if self.effective_stage > stage_before or not self.sub_stage:
            return before[1] - before[0]
        return max(0, self.sub_stage[0] - before[0])

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
            "form": self.form
        }

        # Copy target (Takes HP, Stage, Typing, Appearance)
        self.id = target.id
        self.name = target.name
        self.display_name = target.display_name
        self.types = target.types
        self.base_stats = target.base_stats
        self.cry = target.cry
        self.form = target.form

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
        """Reverts a transformed Pokemon back to original state."""
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
