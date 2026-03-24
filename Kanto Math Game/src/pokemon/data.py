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
        self.wins = 0

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
        self.sidebar_image = pygame.transform.scale(
            img_surface, (int(assets.width * sb_scale), int(assets.width * sb_scale))
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

    @property
    def effective_stage(self):
        """Calculates stage based on base stage + accumulated wins (Pseudo Stages)."""
        bonus = self.wins // 10
        return min(3, self.stage + bonus)

    def get_max_hp(self, stage_override=None):
        """Returns fixed Max HP based on evolution stage."""
        st = stage_override if stage_override is not None else self.effective_stage
        if st >= 3:
            return 16
        elif st == 2: return 12
        return 8

    def get_stat(self, stat_name):
        """Gets a base stat value."""
        return self.base_stats.get(stat_name.upper(), 50)

    def set_volume(self, volume):
        if self.cry:
            self.cry.set_volume(volume)


# [REF-0060: CaughtPokemon Dataclass for Simplified Storage]
@dataclass
class CaughtPokemon:
    id: int
    name: str
    form: str = "normal"
    is_shiny: bool = False
