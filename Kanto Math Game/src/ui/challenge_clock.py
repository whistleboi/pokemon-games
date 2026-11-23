"""A challenge's clock on screen (11-23, first user: FireRed's Trainer Tower, Kanto K2 - Jordan: "Clock on screen").

A region's facility starts it (start), reads it (elapsed) and stops it (stop): the time runs on through battles, as
FireRed's VBlank counter does, and is kept in the story flags (so a saved game keeps its climb's start). While it runs
and you're on a map (not in a battle or a menu), a small panel shows it at the top of the screen: "<label> 3:21.45".
"""
import time

KEY = "challenge_clock"
MAX = 60 * 60 - 0.01   # (FireRed's TRAINER_TOWER_MAX_TIME: the clock stops at 59:59.99)


def start(story, label):
    story.story_flags[KEY] = {"start": time.time(), "label": str(label)}


def running(story):
    c = (getattr(story, "story_flags", None) or {}).get(KEY)
    return c if isinstance(c, dict) and "start" in c else None


def elapsed(story):
    c = running(story)
    return min(MAX, max(0.0, time.time() - float(c["start"]))) if c else 0.0


def stop(story):
    """Stops the clock: the seconds it showed (0 if it wasn't running)."""
    t = elapsed(story)
    story.story_flags.pop(KEY, None)
    return t


def text(seconds):
    m, s = divmod(max(0.0, float(seconds)), 60)
    return f"{int(m)}:{s:05.2f}"


def draw(game):
    story = getattr(game, "story_manager", None)
    c = running(story) if story else None
    if not c:
        return
    st = getattr(game, "current_state", None)
    name = type(st).__name__
    if name not in ("DungeonState", "PlayState", "WalkTownState", "CityState"):   # (on a map only: not in a battle, a menu, a scene)
        return
    import pygame
    from src.ui import theme
    fonts = game.assets.fonts
    f = fonts.get("caption") or fonts.get("small") or next(iter(fonts.values()))
    words = f.render(f"{c.get('label') or 'TIME'}  {text(elapsed(story))}", True, theme.TEXT)
    w, h = words.get_width() + 28, words.get_height() + 14
    sw = game.screen.get_width()
    box = pygame.Rect((sw - w) // 2, 10, w, h)
    theme.draw_panel(game.screen, box, radius=8, accent=theme.TEXTBOX_ACCENT, tab=False)
    game.screen.blit(words, words.get_rect(center=box.center))
