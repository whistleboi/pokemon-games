# [REF-0001: System Imports]
import pygame
import random
import io
import os
import math
import threading
import queue
import json
import sys
from abc import ABC, abstractmethod
import base64
from dataclasses import dataclass


# [REF-0006: UI Framework]
class UIElement(ABC):
    def __init__(self, rect, callback=None, visible=True):
        self.rect = pygame.Rect(rect)
        self.callback = callback
        self.visible = visible

    def set_visibility(self, visible):
        self.visible = visible

    @abstractmethod
    def handle_event(self, event):
        pass

    @abstractmethod
    def draw(self, surface):
        pass


# [REF-0049: UI Manager to Handle Multiple UI Elements and Event Routing]
class UIManager:
    def __init__(self):
        self.elements = []

    def add_element(self, element):
        self.elements.append(element)

    def handle_events(self, events):
        for event in events:
            for element in reversed(list(self.elements)):
                if element.handle_event(event):
                    return True
        return False

    def unconsumed(self, events, state_changed=lambda: False):
        """Route each event to the UI elements on its own; return the ones nobody used.
        Stops if a click changed the screen (the rest belonged to the old screen)."""
        left = []
        for event in events:
            used = False
            for element in reversed(list(self.elements)):
                if element.handle_event(event):
                    used = True
                    break
            if used and state_changed():
                return []
            if not used:
                left.append(event)
        return left

    def draw(self, surface):
        for element in self.elements:
            element.draw(surface)
