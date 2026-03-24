# [REF-0001: System Imports]
import pygame
import random
import math
from abc import ABC, abstractmethod
from src.config import GOLD, WHITE


# [REF-0015: VFX & Particles]
class Particle(ABC):
    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def draw(self, surface):
        pass


# [REF-0051: Particle Effects]
class Starburst(Particle):
    def __init__(self, x, y, color=GOLD):
        self.particles = []
        self.color = color
        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(5, 12)
            self.particles.append(
                [
                    [x, y],
                    [math.cos(angle) * speed, math.sin(angle) * speed],
                    random.randint(20, 40),
                ]
            )

    def update(self):
        for p in self.particles:
            p[0][0] += p[1][0]
            p[0][1] += p[1][1]
            p[2] -= 1
        self.particles = [p for p in self.particles if p[2] > 0]

    def draw(self, surface):
        for p in self.particles:
            pygame.draw.circle(
                surface, self.color, (int(p[0][0]), int(p[0][1])), random.randint(3, 6)
            )


# [REF-0052: Shiny Burst Effect]
class ShinyBurst(Particle):
    def __init__(self, x, y):
        self.particles = []
        self.colors = [GOLD, WHITE, (0, 255, 255), (255, 105, 180)]
        for _ in range(50):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(4, 15)
            color = random.choice(self.colors)
            self.particles.append(
                [
                    [x, y],
                    [math.cos(angle) * speed, math.sin(angle) * speed],
                    random.randint(30, 50),
                    color,
                    random.randint(4, 8),
                ]
            )

    def update(self):
        for p in self.particles:
            p[0][0] += p[1][0]
            p[0][1] += p[1][1]
            p[2] -= 1
        self.particles = [p for p in self.particles if p[2] > 0]

    def draw(self, surface):
        for p in self.particles:
            pygame.draw.circle(surface, p[3], (int(p[0][0]), int(p[0][1])), p[4])


# [REF-0053: Idle Sparkle Effect]
class IdleSparkle:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.particles = []

    def update(self, current_x, current_y):
        self.x, self.y = current_x, current_y
        if len(self.particles) < 12:
            self.particles.append(
                {
                    "rel_x": random.randint(-50, 50),
                    "rel_y": random.randint(-70, 30),
                    "size": random.randint(2, 5),
                    "life": random.randint(15, 30),
                    "color": random.choice([GOLD, WHITE]),
                }
            )
        for p in self.particles:
            p["life"] -= 1
            p["rel_y"] -= 0.5
        self.particles = [p for p in self.particles if p["life"] > 0]

    def draw(self, surface):
        for p in self.particles:
            pygame.draw.circle(
                surface,
                p["color"],
                (int(self.x + p["rel_x"]), int(self.y + p["rel_y"])),
                p["size"],
            )
