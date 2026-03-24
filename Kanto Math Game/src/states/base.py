# [REF-0001: System Imports]
from abc import ABC, abstractmethod


# [REF-0018: Game State Base]
class GameState(ABC):
    def __init__(self, game):
        self.game = game

    def start(self):
        pass

    @abstractmethod
    def handle_events(self, events):
        pass

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def draw(self):
        pass
