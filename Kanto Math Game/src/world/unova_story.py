"""Unova's own story conditions (11-23, batch 4a), through main's region hook: "world:unova_story:<arg>".

- "female_player" / "male_player": Black 2 / White 2 change some people by the player's character (Nimbasa's Subway
  partner is Rosa for a boy and Nate for a girl; the Ferris wheel's trainer). Our characters, by look."""

FEMALE = {"rosa", "hilda", "dawn", "leaf", "female", "may", "girls", "lyra", "kris", "serena", "selene", "gloria",
          "juliana", "lillie"}


def female(story):
    game = getattr(story, "game", None)
    return str(getattr(game, "player_character", "") or "").lower() in FEMALE


def condition(story, arg):
    """"female_player" / "male_player"; "not_today:<flag>": the flag is set, and not today (the day it was first seen
    set is kept as <flag>_day: the Ferris wheel's second visit is another day, as Black 2)."""
    if arg.startswith("not_today:"):
        import datetime
        flag = arg[10:]
        if not story.story_flags.get(flag):
            return False
        today = datetime.date.today().isoformat()
        day = story.story_flags.setdefault(flag + "_day", today)
        return day != today
    if arg.startswith("party_level:"):   # (a Pokemon with you at that level or more: Driftveil Market's Expert Belt man, 11-24)
        want = int(arg.split(":", 1)[1])
        return any(p and not getattr(p, "is_egg", False) and int(getattr(p, "level", 0) or 0) >= want for p in story.player_team)
    if arg == "female_player":
        return female(story)
    if arg == "male_player":
        return not female(story)
    return False


def _today_move(story, game):
    """The move the Luxury Suites lady asks to see today: one of your TMs' moves, the same all day (Black 2: she only asks
    for TM or HM moves you own)."""
    import datetime
    import json
    import os
    import random
    base = getattr(getattr(game, "assets", None), "assets_dir", None) or "assets"
    try:
        tms = json.load(open(os.path.join(base, "tms.json"), encoding="utf-8"))
    except Exception:
        return None
    owned = sorted(tms[k]["move"] for k, n in (story.inventory or {}).items() if k in tms and n)
    if not owned:
        return None
    return random.Random("move_lady@" + datetime.date.today().isoformat()).choice(owned)


def event(state, ev, lines, show):
    """{"toggle": flag}: flip a flag (the roller coaster's switches: each press changes a car's route).
    {"move_lady": true}: Driftveil Luxury Suites' lady: show her a Pokemon that knows today's move, a Heart Scale (once a day).
    {"runner": flag}: the thirsty runner on a bridge: a Fresh Water for his thanks (once)."""
    story = state.game.story_manager
    if ev.get("move_lady"):
        import datetime
        today = datetime.date.today().isoformat()
        if story.story_flags.get("b2_move_lady_day") == today:
            show(["I wonder what that move looks like when it's really used. I'm sure you use it beautifully!"])
            return
        mv = _today_move(story, state.game)
        if not mv:
            show(["Oh, a Trainer! Do come back when you've some TMs. I love to see Pokemon use them!"])
            return
        name = mv.replace("-", " ").title()
        knows = next((p for p in story.player_team if p and mv in [str(m).upper() for m in (getattr(p, "moves", None) or [])]), None)
        if knows is None:
            show(["Oh, a Trainer! Would you do me a favour? I'd love to see a Pokemon that knows %s. Today, please!" % name])
            return
        story.story_flags["b2_move_lady_day"] = today
        story.inventory["HEART_SCALE"] = story.inventory.get("HEART_SCALE", 0) + 1
        show(["Oh my! Your %s can use %s! You taught it just for me? How touching!" % (knows.display_name, name),
              "Please accept this small token of my thanks. You received a Heart Scale!"])
        return
    if ev.get("runner"):
        flag = ev["runner"]
        if story.story_flags.get(flag):
            show(["Refreshed! 100% rehydrated! I'll dash to the next bridge!"])
            return
        if not story.inventory.get("FRESH_WATER"):
            show(["*Pant... pant...* So thirsty... We met on Skyarrow Bridge, remember? A Fresh Water...?",
                  "You don't have any? Thanks for the thought anyway..."])
            return
        story.inventory["FRESH_WATER"] -= 1
        story.story_flags[flag] = True
        show(["*Pant... pant...* So thirsty... We met on Skyarrow Bridge, remember? Could you spare a Fresh Water?",
              "You handed over a Fresh Water.", "Refreshed! 100% rehydrated! Thank you! I'll dash to the next bridge!"])
        return
    if ev.get("toggle"):
        flags = state.game.story_manager.story_flags
        flags[ev["toggle"]] = not flags.get(ev["toggle"])
        if lines:
            show(lines)
        return
    show(lines or ["..."])
