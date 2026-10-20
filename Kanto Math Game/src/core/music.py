"""Background music by situation: towns, routes, wild/trainer/gym battles, and a victory jingle.

Tracks are found in assets/sounds by name: every file whose name has the kind's word in it
(kanto_wild2.ogg, music_town.wav, kanto_battle1.mp3 for gyms). If the current region has its
own files (johto_town1.ogg) only those are used. New files dropped in are picked up automatically.
"""
import os
import random

import pygame

from src.config import VOLUME

# kind -> file-name keywords, best first
KINDS = {
    "town": ("town",),
    "route": ("route",),
    "wild": ("wild",),
    "trainer": ("trainer",),
    "gym": ("gym", "battle"),
    "victory": ("victory",),
}
EXTS = (".ogg", ".mp3", ".wav")


class MusicManager:
    def __init__(self, game):
        self.game = game
        self.kind = None
        self.pending = None   # what to play once the victory jingle ends

    def tracks(self, kind, region=None):
        files = getattr(self.game.assets, "sound_map", {})
        names = [f for f in files if f.endswith(EXTS)]
        words = KINDS.get(kind, ())
        matches = [f for f in names if any(w in os.path.splitext(f)[0] for w in words)]
        if region:
            own = [f for f in matches if f.startswith(region.lower() + "_")]
            if own:  # this region's tracks (plus the built-in ones), not other regions'
                return [files[f] for f in matches if f in own or f.startswith("music_")]
        return [files[f] for f in matches]

    def play(self, kind, force=False):
        """Switch to this kind of music (no restart if it's already playing)."""
        if not pygame.mixer.get_init():
            return
        if self.kind == "victory" and kind != "victory" and pygame.mixer.music.get_busy():
            self.pending = kind  # let the jingle finish first
            return
        if kind == self.kind and pygame.mixer.music.get_busy() and not force:
            return
        region = None
        try:
            region = self.game.story_manager.get_current_region()
        except Exception:
            pass
        choices = self.tracks(kind, region)
        if not choices:
            return
        path = os.path.join(self.game.assets.sounds_dir, random.choice(choices))
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(VOLUME)
            pygame.mixer.music.play(0 if kind == "victory" else -1)
            pygame.mixer.music.set_endevent(self._end_event())
            self.kind = kind
        except Exception as e:
            print(f"Music: couldn't play {path}: {e}")

    def victory(self):
        self.pending = None
        self.play("victory", force=True)

    def on_track_end(self):
        """MUSIC_ENDED_EVENT: after the jingle, go back to the area's music."""
        if self.kind == "victory":
            self.kind = None
            if self.pending:
                kind, self.pending = self.pending, None
                self.play(kind)

    def for_state(self, state):
        """Pick the music for a screen the game just switched to (menus keep what's playing)."""
        from src.states.battle import TrainerBattleState, WildBattleState
        from src.states.overworld import CityState, PlayState, GymLobbyState
        from src.states.menus import MainMenuState
        if isinstance(state, WildBattleState):
            kind = "gym" if getattr(state, "is_boss_battle", False) else "wild"
        elif isinstance(state, TrainerBattleState):
            big = (state.battle_type == "gym" or getattr(state, "is_boss_battle", False)
                   or state.trainer_class in ("GYM_LEADER", "ELITE_FOUR", "CHAMPION"))
            kind = "gym" if big else "trainer"
        elif isinstance(state, GymLobbyState):
            kind = "gym"
        elif isinstance(state, (CityState, MainMenuState)):
            kind = "town"
        elif isinstance(state, PlayState):
            kind = "route"
        else:
            return
        self.play(kind)

    @staticmethod
    def _end_event():
        from src.config import MUSIC_ENDED_EVENT
        return MUSIC_ENDED_EVENT
