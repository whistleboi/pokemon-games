# [REF-0097: Android (Pydroid 3)]
"""Playing on an Android phone or tablet with Pydroid 3 (Jordan, 11-04). See ANDROID.md.

The game already draws at 1280x720 and SDL scales it to the screen, and every button works by tap.
This adds what a phone needs on top:

- Typing: tapping a screen's name or search box opens the on-screen keyboard; tapping elsewhere,
  Enter or leaving the screen closes it. Its letters (SDL text events) reach the screens as the
  key presses they already read. A screen that takes typing has text_input_rect(): its box.
- The Back button works as Esc (BACK / EXIT / NO on the screen, as on a PC keyboard).
- Leaving the app pauses the sound, and saves in a town or on a route when AUTOSAVE is on
  (Android may close an app in the background).
- Landscape only.

POKEMATH_ANDROID=1 turns it on on a PC, for tests.
"""
import os
import sys

import pygame


def is_android():
    return (os.environ.get("POKEMATH_ANDROID") == "1" or hasattr(sys, "getandroidapilevel")
            or "ANDROID_ARGUMENT" in os.environ or "ANDROID_ROOT" in os.environ)


def prepare():
    """Before pygame starts: keep the Back button for the game, and stay in landscape."""
    if is_android():
        os.environ.setdefault("SDL_ANDROID_TRAP_BACK_BUTTON", "1")
        os.environ.setdefault("SDL_HINT_ORIENTATIONS", "LandscapeLeft LandscapeRight")
        os.environ.setdefault("SDL_IOS_ORIENTATIONS", "LandscapeLeft LandscapeRight")


BACK_KEYS = tuple(k for k in (getattr(pygame, "K_AC_BACK", None),) if k is not None)
BACKGROUND = tuple(getattr(pygame, n) for n in ("APP_WILLENTERBACKGROUND", "APP_DIDENTERBACKGROUND")
                   if hasattr(pygame, n))
FOREGROUND = tuple(getattr(pygame, n) for n in ("APP_DIDENTERFOREGROUND",) if hasattr(pygame, n))


class AndroidInput:
    def __init__(self, game):
        self.game = game
        self.typing = False
        self.state = None
        self.away = False
        if is_android():
            self._stop_typing()  # SDL may start with text input on: no keyboard until a box is tapped

    # ------------------------------------------------------------------ the keyboard
    def _box(self):
        get = getattr(self.game.current_state, "text_input_rect", None)
        try:
            return pygame.Rect(get()) if callable(get) and get() else None
        except (TypeError, ValueError):
            return None

    def _start_typing(self, box):
        try:
            pygame.key.set_text_input_rect(box)
            pygame.key.start_text_input()
        except pygame.error:
            pass
        self.typing = True

    def _stop_typing(self):
        try:
            pygame.key.stop_text_input()
        except pygame.error:
            pass
        self.typing = False

    # ------------------------------------------------------------------ each frame
    def filter(self, events):
        """The frame's events, made to work like a PC's (only on Android)."""
        if not is_android():
            return events
        if self.game.current_state is not self.state:  # a new screen: no keyboard
            self.state = self.game.current_state
            if self.typing:
                self._stop_typing()
        out = []
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and getattr(e, "button", 1) == 1:
                box = self._box()
                if box and box.collidepoint(e.pos):
                    self._start_typing(box)
                elif self.typing:
                    self._stop_typing()
                out.append(e)
            elif e.type == pygame.TEXTINPUT:  # the keyboard's letters, as the key presses screens read
                for ch in e.text:
                    out.append(pygame.event.Event(pygame.KEYDOWN, key=0, unicode=ch, mod=0, scancode=0))
            elif e.type in (pygame.KEYDOWN, pygame.KEYUP) and e.key in BACK_KEYS:
                out.append(pygame.event.Event(e.type, key=pygame.K_ESCAPE, unicode="", mod=0, scancode=0))
            elif e.type == pygame.KEYDOWN and getattr(e, "unicode", "") and e.unicode.isprintable():
                # letters come as text events: drop the key's own letter so nothing is typed twice
                out.append(pygame.event.Event(pygame.KEYDOWN, key=e.key, unicode="", mod=e.mod,
                                              scancode=getattr(e, "scancode", 0)))
            elif e.type in BACKGROUND:
                self._go_away()
            elif e.type in FOREGROUND:
                self._come_back()
            else:
                if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.typing:
                    self._stop_typing()
                out.append(e)
        return out

    def _go_away(self):
        if self.away:
            return
        self.away = True
        try:
            pygame.mixer.pause()
            pygame.mixer.music.pause()
        except pygame.error:
            pass
        story = getattr(self.game, "story_manager", None)
        name = type(self.game.current_state).__name__
        if getattr(story, "autosave", False) and name in ("CityState", "PlayState"):
            from src.states.overworld import autosave
            autosave(self.game)

    def _come_back(self):
        if not self.away:
            return
        self.away = False
        try:
            pygame.mixer.unpause()
            pygame.mixer.music.unpause()
        except pygame.error:
            pass
