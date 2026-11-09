"""The player's Options (Jordan, 11-08): kept in the save (story.prefs), put into effect by apply()."""
import os

import pygame

DEFAULTS = {"math_timer": "NORMAL", "text_speed": 3, "auto_text": 2, "move_anims": True, "battle_intros": True, "screen_fade": True,
            "music": 5, "sfx": 5}


def get(story, key):
    return getattr(story, "prefs", {}).get(key, DEFAULTS[key])


def put(game, key, value):
    game.story_manager.prefs[key] = value
    apply(game)


def apply(game):
    from src import config
    from src.ui import dialogue
    story = game.story_manager
    dialogue.TEXT_SPEED = get(story, "text_speed")
    config.AUDIO_LEVELS.update(music=get(story, "music"), sfx=get(story, "sfx"))
    game.FADE_FRAMES = 6 if get(story, "screen_fade") else 0
    game.battle_transitions = get(story, "battle_intros") and os.environ.get("SDL_VIDEODRIVER") != "dummy"
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(config.music_volume())
    except pygame.error:
        pass
    assets = game.assets
    sounds = list(getattr(assets, "ui_sfx", {}).values()) if isinstance(getattr(assets, "ui_sfx", None), dict) else []
    sounds += [getattr(assets, "heal_sfx", None)]
    for s in sounds:
        if s is not None and hasattr(s, "set_volume"):
            s.set_volume(config.sfx_volume())
